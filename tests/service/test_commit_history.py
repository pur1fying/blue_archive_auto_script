from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient

from service.api import commands, ws_trigger
from service.auth import AuthenticationError
from service.types import CommandMessage
from service.update import history

DEV = "Kiramei/baas-dev"
STABLE = "pur1fying/blue_archive_auto_script"


def entry(number=1):
    return {"hash": f"{number:040x}", "author": "Kiramei", "message": f"Change {number}"}


def setup(channel="dev"):
    return {"general": {"channel": channel, "current_baas_sha": f"{9:040x}"}}


def offline(*_args):
    raise history.HistoryUnavailable("offline")


def cache(root, values=None, *, repository=DEV, reference="master", age=0, has_more=False):
    document = {"schema": 1, "repository": repository, "reference": reference,
                "entries": values if values is not None else [entry()],
                "fetched_at": time.time() - age, "has_more": has_more}
    history._write_json(root / "config/commit-history/dev.json", document)


def bundle(root, values=None, *, repository=DEV, reference="master"):
    document = {"schema": 1, "repository": repository, "reference": reference,
                "entries": values if values is not None else [entry()]}
    history._write_json(root / history.MANIFEST_NAME, document)


def call(root, **kwargs):
    return history.get_commit_history(root=root, setup=setup(), **kwargs)


def test_online_keeps_only_the_three_requested_fields_and_subject(monkeypatch, tmp_path):
    calls = []

    def page(repository, reference, page, timeout, token=None):
        calls.append((repository, reference, page, timeout, token))
        return [{"sha": entry()["hash"], "commit": {
            "author": {"name": "A\x00uthor", "email": "do-not-cache@example.invalid"},
            "message": "Subject\n\nPrivate body", "tree": {"sha": "not stored"}},
            "files": [{"patch": "must not persist"}]}]

    monkeypatch.setattr(history, "_github_page", page)
    result = call(tmp_path)
    assert result["entries"] == [{"hash": entry()["hash"], "author": "Author", "message": "Subject"}]
    assert result["repository"] == DEV
    assert result["current"] == f"{9:040x}"
    assert result["source"] == "github" and result["issue"] is None
    stored = json.loads((tmp_path / "config/commit-history/dev.json").read_text())
    assert stored["entries"] == result["entries"]
    assert "Private body" not in json.dumps(stored)
    assert "example.invalid" not in json.dumps(stored)
    assert len(calls) == 1 and calls[0][0:3] == (DEV, "master", 1)


def test_fresh_cache_avoids_network_and_refresh_uses_network(monkeypatch, tmp_path):
    cache(tmp_path)
    monkeypatch.setattr(history, "_fetch_github", lambda *_: pytest.fail("Unexpected network"))
    assert call(tmp_path)["source"] == "cache"
    monkeypatch.setattr(history, "_fetch_github", lambda *_: ([entry(2)], False, False, None))
    assert call(tmp_path, refresh=True)["entries"] == [entry(2)]


def test_stale_cache_survives_offline_refresh(monkeypatch, tmp_path):
    cache(tmp_path, age=history.CACHE_TTL + 1)
    monkeypatch.setattr(history, "_fetch_github", offline)
    result = call(tmp_path)
    assert result["entries"] == [entry()]
    assert result["source"] == "cache" and result["stale"] is True
    assert result["issue"] == "offline"


def test_pagination_requests_more_than_incomplete_cache(monkeypatch, tmp_path):
    cache(tmp_path, has_more=True)
    monkeypatch.setattr(history, "_fetch_github", lambda _r, _b, limit: ([entry(i) for i in range(limit)], True, False, None))
    result = call(tmp_path, limit=200)
    assert len(result["entries"]) == 200 and result["source"] == "github"
    assert result["hasMore"] is True


@pytest.mark.parametrize("kwargs", [{"limit": 0}, {"limit": 501}, {"limit": True}, {"limit": "100"},
                                    {"refresh": "true"}, {"channel": "https://evil.invalid/"},
                                    {"channel": {}}, {"channel": ""}])
def test_client_cannot_supply_unbounded_or_arbitrary_sources(tmp_path, kwargs):
    with pytest.raises(ValueError):
        call(tmp_path, **kwargs)


@pytest.mark.parametrize("document", [
    {"repository": STABLE}, {"reference": "other"}, {"schema": True},
    {"entries": [{**entry(), "diff": "not accepted"}]},
    {"entries": [{**entry(), "hash": "abcdef"}]},
    {"entries": [{**entry(), "author": 1}]},
    {"entries": [entry()] * 501},
])
def test_gitless_bundle_rejects_wrong_scope_and_bad_metadata(monkeypatch, tmp_path, document):
    bundle(tmp_path)
    path = tmp_path / history.MANIFEST_NAME
    value = json.loads(path.read_text())
    value.update(document)
    path.write_text(json.dumps(value))
    monkeypatch.setattr(history, "_fetch_github", offline)
    assert call(tmp_path)["entries"] == []


def test_gitless_mirror_can_show_bundled_metadata_without_cdk_or_network(monkeypatch, tmp_path):
    bundle(tmp_path)
    monkeypatch.setattr(history, "_fetch_github", offline)
    result = call(tmp_path)
    assert result["entries"] == [entry()]
    assert result["source"] == "bundle" and result["stale"] and result["partial"]
    assert not (tmp_path / ".git").exists()


def test_channels_never_share_cache_or_mislabel_installed_sha(monkeypatch, tmp_path):
    cache(tmp_path)
    monkeypatch.setattr(history, "_fetch_github", offline)
    result = call(tmp_path, channel="stable")
    assert result["repository"] == STABLE and result["entries"] == []
    assert result["current"] is None


@pytest.mark.parametrize("content", [b"not JSON", b"x" * (history.MAX_BYTES + 1)], ids=["invalid-json", "oversized"])
def test_corrupt_or_oversized_cache_falls_back_safely(monkeypatch, tmp_path, content):
    path = tmp_path / "config/commit-history/dev.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    bundle(tmp_path)
    monkeypatch.setattr(history, "_fetch_github", offline)
    assert call(tmp_path)["source"] == "bundle"


def test_rate_limit_is_a_safe_status_and_not_raw_exception(monkeypatch, tmp_path):
    def rate_limited(*_args):
        raise history.HistoryUnavailable("rate_limited")
    cache(tmp_path, age=history.CACHE_TTL + 1)
    monkeypatch.setattr(history, "_fetch_github", rate_limited)
    result = call(tmp_path)
    assert result["issue"] == "rate_limited"
    assert result["entries"] == [entry()]


@pytest.mark.parametrize("error,issue", [
    (HTTPError("https://api.github.com/", 429, "sensitive response", {}, None), "rate_limited"),
    (HTTPError("https://api.github.com/", 403, "sensitive response", {"X-RateLimit-Remaining": "0"}, None), "rate_limited"),
    (HTTPError("https://api.github.com/", 404, "sensitive response", {}, None), "unavailable"),
    (URLError("sensitive connection details"), "offline"),
], ids=["too-many-requests", "rate-limit-exhausted", "not-found", "offline"])
def test_http_failures_expose_only_safe_reason_codes(monkeypatch, error, issue):
    def fail(*_args, **_kwargs):
        raise error
    monkeypatch.setattr(history, "urlopen", fail)
    with pytest.raises(history.HistoryUnavailable) as result:
        history._github_page(DEV, "master", 1, 1)
    assert result.value.issue == issue
    assert str(result.value) == issue


def test_oversized_remote_metadata_is_bounded_and_rejected(monkeypatch):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            pass
        def read(self, maximum):
            assert maximum == history.MAX_BYTES + 1
            return b"x" * maximum
    monkeypatch.setattr(history, "urlopen", lambda *_args, **_kwargs: Response())
    with pytest.raises(history.HistoryUnavailable, match="unavailable"):
        history._github_page(DEV, "master", 1, 1)


def test_later_page_failure_preserves_rows_and_does_not_cache_them_as_complete(monkeypatch, tmp_path):
    requests = []
    def page(repository, reference, number, timeout, token=None):
        requests.append(reference)
        if number > 1:
            raise history.HistoryUnavailable("rate_limited")
        return [{"sha": entry(i)["hash"], "commit": {"author": {"name": "Author"}, "message": "Subject"}}
                for i in range(100)]
    monkeypatch.setattr(history, "_github_page", page)
    result = call(tmp_path, limit=200)
    assert len(result["entries"]) == 100
    assert result["partial"] is True and result["hasMore"] is True
    assert result["issue"] == "rate_limited"
    assert requests == ["master", entry(0)["hash"]]
    stored = json.loads((tmp_path / "config/commit-history/dev.json").read_text())
    assert stored["partial"] is True
    monkeypatch.setattr(history, "_fetch_github", lambda *_: ([entry(5)], False, False, None))
    assert call(tmp_path)["source"] == "github"


def test_empty_author_is_normalized_without_adding_email_or_body(monkeypatch, tmp_path):
    monkeypatch.setattr(history, "_github_page", lambda *_: [{
        "sha": entry()["hash"], "commit": {"author": {"name": "  "}, "message": "Subject"}}])
    assert call(tmp_path)["entries"][0]["author"] == "Unknown"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def repository(tmp_path):
    if not shutil.which("git"):
        pytest.skip("Git is unavailable")
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-b", "master")
    git(root, "config", "user.name", "History Author")
    git(root, "config", "user.email", "unused@example.invalid")
    git(root, "remote", "add", "origin", "https://github.com/Kiramei/baas-dev.git")
    for i in range(3):
        (root / "example.txt").write_text(str(i))
        git(root, "add", "example.txt")
        git(root, "commit", "-m", f"Subject {i}\n\nBody excluded")
    return root


def fingerprint(root):
    return {str(path.relative_to(root)): (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in (root / ".git").rglob("*") if path.is_file()}


def test_full_local_git_fallback_reads_metadata_without_touching_git(monkeypatch, repository):
    before = fingerprint(repository)
    monkeypatch.setattr(history, "_fetch_github", offline)
    result = call(repository)
    assert len(result["entries"]) == 3 and result["source"] == "local"
    assert result["entries"][0]["message"] == "Subject 2"
    assert result["entries"][0]["author"] == "History Author"
    assert result["partial"] is False
    assert before == fingerprint(repository)


def test_shallow_clone_is_not_deepened_or_given_old_git_objects(monkeypatch, repository, tmp_path):
    clone = tmp_path / "shallow"
    subprocess.run(["git", "clone", "--depth=1", repository.as_uri(), str(clone)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    git(clone, "remote", "set-url", "origin", "https://github.com/Kiramei/baas-dev.git")
    before = fingerprint(clone)
    monkeypatch.setattr(history, "_fetch_github", offline)
    result = call(clone)
    assert len(result["entries"]) == 1 and result["partial"] is True
    assert result["hasMore"] is True and before == fingerprint(clone)
    assert git(clone, "rev-parse", "--is-shallow-repository") == "true"


def test_local_repository_with_wrong_origin_is_not_presented_as_channel_history(monkeypatch, repository):
    git(repository, "remote", "set-url", "origin", "https://evil.invalid/github.com/Kiramei/baas-dev.git")
    monkeypatch.setattr(history, "_fetch_github", offline)
    assert call(repository)["entries"] == []


def test_local_feature_branch_is_not_presented_as_master_history(monkeypatch, repository):
    git(repository, "checkout", "-b", "feature")
    monkeypatch.setattr(history, "_fetch_github", offline)
    assert call(repository)["entries"] == []


@pytest.mark.parametrize("origin", ["git@github.com:Kiramei/baas-dev.git", "ssh://git@github.com/Kiramei/baas-dev",
                                     "https://githubfast.com/Kiramei/baas-dev.git",
                                     "https://gh-proxy.org/https://github.com/Kiramei/baas-dev.git"])
def test_canonical_and_known_proxy_origins(origin):
    assert history._origin_matches(origin, DEV)


def test_packager_writes_only_metadata_without_changing_git(repository):
    before = fingerprint(repository)
    script = Path(__file__).resolve().parents[2] / "develop_tools/package_commit_history.py"
    subprocess.run([sys.executable, str(script), "--root", str(repository), "--repository", DEV], check=True,
                   stdout=subprocess.DEVNULL)
    document = json.loads((repository / history.MANIFEST_NAME).read_text())
    assert set(document) == {"schema", "repository", "reference", "entries"}
    assert len(document["entries"]) == 3
    assert all(set(value) == {"hash", "author", "message"} for value in document["entries"])
    assert before == fingerprint(repository)


def test_command_dispatch_returns_the_standard_authenticated_trigger_envelope(monkeypatch):
    calls = []
    async def get_history(channel, limit, refresh):
        calls.append((channel, limit, refresh))
        return {"entries": [entry()]}
    monkeypatch.setattr(commands, "context", SimpleNamespace(runtime=SimpleNamespace(get_commit_history=get_history)))
    command = CommandMessage(type="command", command="get_commit_history", timestamp=1,
                             payload={"channel": "dev", "limit": 200, "refresh": True})
    result = asyncio.run(commands.execute_command(command))
    assert result == {"status": "ok", "data": {"entries": [entry()]}}
    assert calls == [("dev", 200, True)]


def test_history_trigger_is_unreachable_before_authentication(monkeypatch):
    async def reject(websocket, **_kwargs):
        await websocket.accept()
        raise AuthenticationError("Authentication required")
    class NoCommands:
        def __init__(self, *_args):
            pytest.fail("Unauthenticated connection reached business commands")
    monkeypatch.setattr(ws_trigger, "perform_business_resume", reject)
    monkeypatch.setattr(ws_trigger, "TriggerChannelHandler", NoCommands)
    app = FastAPI()
    app.include_router(ws_trigger.router)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/trigger") as websocket:
            with pytest.raises(WebSocketDisconnect) as error:
                websocket.receive_json()
            assert error.value.code == 4401
