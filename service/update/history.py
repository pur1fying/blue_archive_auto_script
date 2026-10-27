"""Bounded commit metadata, without fetching or storing Git objects or patches.

Both caches and release manifests contain only a commit's hash, author name and
subject. Reading history never invokes an update, fetch, checkout or deepening.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

REPOSITORIES = {
    "stable": "pur1fying/blue_archive_auto_script",
    "dev": "Kiramei/baas-dev",
}
REFERENCE = "master"
MAX_ENTRIES = 500
MAX_BYTES = 2 * 1024 * 1024
CACHE_TTL = 600
MANIFEST_NAME = ".baas-commit-history.json"
_SHA = re.compile(r"^[0-9a-f]{40}$")
_LOCK = threading.RLock()


class HistoryUnavailable(Exception):
    def __init__(self, issue: str):
        self.issue = issue
        super().__init__(issue)


def _sha(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and _SHA.fullmatch(value) else None


def _text(value: Any, maximum: int) -> Optional[str]:
    if not isinstance(value, str):
        return None
    # The table presents subjects, never multiline commit bodies or email data.
    value = value.splitlines()[0] if value.splitlines() else ""
    return "".join(char for char in value if char.isprintable())[:maximum].strip()


def _entries(value: Any) -> Optional[list]:
    if not isinstance(value, list) or len(value) > MAX_ENTRIES:
        return None
    entries, seen = [], set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {"hash", "author", "message"}:
            return None
        commit_hash = _sha(item.get("hash"))
        author = _text(item.get("author"), 256)
        message = _text(item.get("message"), 4096)
        if not commit_hash or author is None or message is None:
            return None
        if commit_hash not in seen:
            seen.add(commit_hash)
            entries.append({"hash": commit_hash, "author": author or "Unknown", "message": message})
    return entries


def _read_metadata(path: Path, repository: str, reference: str, cache: bool = False) -> Optional[dict]:
    try:
        with path.open("rb") as file:
            raw = file.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return None
        document = json.loads(raw)
        if (not isinstance(document, dict) or type(document.get("schema")) is not int
                or document.get("schema") != 1
                or document.get("repository", "").lower() != repository.lower()
                or document.get("reference") != reference):
            return None
        entries = _entries(document.get("entries"))
        if entries is None:
            return None
        if cache:
            fetched = document.get("fetched_at")
            if (isinstance(fetched, bool) or not isinstance(fetched, (int, float))
                    or not 0 < fetched <= time.time() + 60
                    or not isinstance(document.get("has_more"), bool)
                    or not isinstance(document.get("partial", False), bool)):
                return None
        return {**document, "entries": entries}
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def _write_json(path: Path, document: dict) -> None:
    data = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("Commit metadata exceeds the size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".commit-history-", dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(data)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def _github_page(repository: str, reference: str, page: int, timeout: float, token: Optional[str] = None) -> list:
    # Repository/ref are fixed by the channel, never accepted as URLs from clients.
    url = f"https://api.github.com/repos/{repository}/commits?sha={reference}&per_page=100&page={page}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "BAAS-Commit-History",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise HistoryUnavailable("unavailable")
            value = json.loads(raw)
        if not isinstance(value, list) or len(value) > 100:
            raise HistoryUnavailable("unavailable")
        return value
    except HTTPError as exc:
        issue = "rate_limited" if exc.code == 429 or (exc.code == 403 and (
            exc.headers.get("X-RateLimit-Remaining") == "0" or exc.headers.get("Retry-After")
        )) else "unavailable"
        raise HistoryUnavailable(issue) from None
    except (URLError, TimeoutError, OSError):
        raise HistoryUnavailable("offline") from None
    except (ValueError, TypeError):
        raise HistoryUnavailable("unavailable") from None


def _fetch_github(repository: str, reference: str, limit: int, token: Optional[str] = None) -> tuple:
    entries, seen = [], set()
    deadline = time.monotonic() + 20
    has_more = False
    for page in range(1, (limit + 99) // 100 + 1):
        remaining = deadline - time.monotonic()
        try:
            if remaining <= 0:
                raise HistoryUnavailable("offline")
            # Subsequent pages use the first page's commit so a moving branch
            # cannot mix snapshots while paginating.
            anchor = entries[0]["hash"] if entries else reference
            values = _github_page(repository, anchor, page, min(5.0, remaining), token)
        except HistoryUnavailable as exc:
            if entries:
                return entries[:limit], True, True, exc.issue
            raise
        parsed = []
        for item in values:
            commit = item.get("commit") if isinstance(item, dict) else None
            if not isinstance(commit, dict) or not isinstance(commit.get("author"), dict):
                if entries:
                    return entries[:limit], True, True, "unavailable"
                raise HistoryUnavailable("unavailable")
            parsed.append({"hash": item.get("sha"), "author": commit["author"].get("name"),
                           "message": commit.get("message")})
        normalized = _entries(parsed)
        if normalized is None:
            if entries:
                return entries[:limit], True, True, "unavailable"
            raise HistoryUnavailable("unavailable")
        for entry in normalized:
            if entry["hash"] not in seen:
                seen.add(entry["hash"])
                entries.append(entry)
        has_more = len(values) == 100
        if not has_more:
            break
    return entries[:limit], has_more or len(entries) > limit, False, None


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"},
    )
    if len(result.stdout) > MAX_BYTES:
        raise ValueError("Local commit metadata exceeds the size limit")
    return result.stdout.decode("utf-8", errors="replace")


def _origin_matches(origin: str, repository: str) -> bool:
    # Recognize GitHub SSH/HTTPS and the configured GitHub proxy URLs only.
    if origin.startswith("git@github.com:"):
        path = origin[len("git@github.com:"):]
    else:
        parsed = urlparse(origin)
        if parsed.scheme not in {"https", "http", "ssh"}:
            return False
        host = parsed.hostname
        if host in {"github.com", "githubfast.com"}:
            path = parsed.path.lstrip("/")
        elif host in {"v4.gh-proxy.org", "v6.gh-proxy.org", "cdn.gh-proxy.org", "gh-proxy.org",
                      "gh.sevencdn.com", "baas-cdn.kiramei.workers.dev"}:
            prefix = "/https://github.com/"
            if not parsed.path.startswith(prefix):
                return False
            path = parsed.path[len(prefix):]
        else:
            return False
        if parsed.query or parsed.fragment:
            return False
    return path.rstrip("/").removesuffix(".git").lower() == repository.lower()


def _local_history(root: Path, repository: str, limit: int, *, validate_reference: bool = True) -> Optional[dict]:
    try:
        if not (root / ".git").exists():
            return None
        if Path(_git(root, "rev-parse", "--show-toplevel").strip()).resolve() != root.resolve():
            return None
        if not _origin_matches(_git(root, "remote", "get-url", "origin").strip(), repository):
            return None
        if validate_reference and _git(root, "symbolic-ref", "--short", "HEAD").strip() != REFERENCE:
            return None
        raw = _git(root, "log", "--no-show-signature", "-z", "--format=%H%x00%an%x00%s",
                   f"-n{min(limit + 1, MAX_ENTRIES + 1)}", "HEAD", "--")
        fields = raw.split("\0")[:-1] if raw else []
        if len(fields) % 3:
            return None
        values = [{"hash": fields[i], "author": fields[i + 1], "message": fields[i + 2]}
                  for i in range(0, len(fields), 3)]
        entries = _entries(values[:MAX_ENTRIES])
        if not entries:
            return None
        shallow = _git(root, "rev-parse", "--is-shallow-repository").strip() == "true"
        return {"entries": entries[:limit], "current": entries[0]["hash"],
                "has_more": len(values) > limit or shallow, "partial": shallow}
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _response(entries: list, repository: str, current: Optional[str], source: str,
              stale: bool, partial: bool, has_more: bool, issue: Optional[str]) -> dict:
    return {"entries": entries, "repository": repository, "reference": REFERENCE,
            "current": current, "source": source, "stale": stale, "partial": partial,
            "hasMore": has_more, "issue": issue}


def get_commit_history(channel: Optional[str] = None, limit: int = 100, refresh: bool = False,
                       *, root: Optional[Path] = None, setup: Optional[Dict[str, Any]] = None) -> dict:
    """Return channel history, keeping installation files and Git object storage untouched."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_ENTRIES:
        raise ValueError("History limit must be an integer between 1 and 500")
    if not isinstance(refresh, bool):
        raise ValueError("History refresh must be a boolean")
    if channel is not None and (not isinstance(channel, str) or channel not in REPOSITORIES):
        raise ValueError("Unknown history channel")
    root = (root or Path.cwd()).resolve()
    if setup is None:
        from .setup_io import read_setup_toml
        setup, _ = read_setup_toml(root / "setup.toml")
    from .setup_schema import setup_channel
    configured_channel = setup_channel(setup)
    channel = channel or configured_channel
    repository = REPOSITORIES[channel]
    configured_sha = setup.get("general", {}).get("current_baas_sha")
    current = _sha(configured_sha) if channel == configured_channel else None
    cache_path = root / "config" / "commit-history" / f"{channel}.json"
    with _LOCK:
        cached = _read_metadata(cache_path, repository, REFERENCE, cache=True)
        if (cached and not cached.get("partial", False) and not refresh
                and time.time() - cached["fetched_at"] < CACHE_TTL
                and (len(cached["entries"]) >= limit or not cached["has_more"])):
            return _response(cached["entries"][:limit], repository, current, "cache", False, False,
                             cached["has_more"] or len(cached["entries"]) > limit, None)
        try:
            entries, has_more, partial, issue = _fetch_github(repository, REFERENCE, limit)
            document = {"schema": 1, "repository": repository, "reference": REFERENCE,
                        "fetched_at": time.time(), "has_more": has_more, "entries": entries,
                        "partial": partial}
            if partial and cached and len(cached["entries"]) > len(entries):
                # Keep the larger offline snapshot. A failed refresh may have
                # discovered a newer tip, so it must no longer pass the fresh
                # cache shortcut, even if its original TTL has not expired.
                document = {"schema": 1, "repository": repository, "reference": REFERENCE,
                            "fetched_at": cached["fetched_at"], "has_more": cached["has_more"],
                            "entries": cached["entries"], "partial": True}
            try:
                _write_json(cache_path, document)
            except (OSError, ValueError):
                pass  # Read-only deployments may still show the fetched metadata.
            return _response(entries, repository, current, "github", False, partial, has_more, issue)
        except HistoryUnavailable as exc:
            issue = exc.issue
        if cached:
            return _response(cached["entries"][:limit], repository, current, "cache", True,
                             cached.get("partial", False) or (len(cached["entries"]) < limit and cached["has_more"]),
                             cached["has_more"] or len(cached["entries"]) > limit, issue)
        local = _local_history(root, repository, limit)
        if local:
            return _response(local["entries"], repository, current or local["current"], "local", True,
                             local["partial"], local["has_more"], issue)
        bundle = _read_metadata(root / MANIFEST_NAME, repository, REFERENCE)
        if bundle:
            values = bundle["entries"]
            return _response(values[:limit], repository, current, "bundle", True, True,
                             len(values) >= limit, issue)
        return _response([], repository, current, "cache", True, True, False, issue)
