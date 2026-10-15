#!/usr/bin/env python3
"""Import upstream changes as ordinary, single-parent commits.

The state records the upstream tree already reconciled with this fork.  Each
subsequent upstream first-parent commit supplies one three-way delta.  Git only
updates HEAD and the checkout after the complete import has succeeded.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


STATE_PATH = ".github/upstream-sync.json"
REPOSITORY = "pur1fying/blue_archive_auto_script"
BRANCH = "master"


class SyncError(Exception):
    """A synchronization that cannot be completed without manual intervention."""


def git(root, *args, input=None, env=None, check=True):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if check and result.returncode:
        details = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"git {' '.join(args)} failed: {details}")
    return result


def resolve_commit(root, ref):
    return git(root, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").stdout.strip()


def read_state(root, head):
    result = git(root, "show", f"{head}:{STATE_PATH}", check=False)
    if result.returncode:
        raise SyncError(f"Missing committed sync state: {STATE_PATH}")
    try:
        state = json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise SyncError(f"Invalid sync state in {STATE_PATH}: {error}") from error
    if (
        not isinstance(state, dict)
        or type(state.get("schema_version")) is not int
        or state.get("schema_version") != 1
        or state.get("repository") != REPOSITORY
        or state.get("branch") != BRANCH
    ):
        raise SyncError(f"Unsupported sync state in {STATE_PATH}")
    last = state.get("last_synced_commit")
    if not isinstance(last, str) or not last or resolve_commit(root, last) != last:
        raise SyncError("last_synced_commit must be a full upstream commit ID")
    return last


def check_state_path_available(root, commit):
    """The metadata belongs to the fork; never overwrite an upstream path."""
    if git(root, "ls-tree", commit, "--", STATE_PATH).stdout.strip():
        raise SyncError(f"Upstream commit {commit} uses reserved sync state path {STATE_PATH}")
    parent = git(root, "ls-tree", commit, "--", ".github").stdout.strip()
    if parent and parent.split()[1] != "tree":
        raise SyncError(f"Upstream commit {commit} prevents use of {STATE_PATH}")


def state_contents(upstream):
    return json.dumps(
        {
            "schema_version": 1,
            "repository": REPOSITORY,
            "branch": BRANCH,
            "last_synced_commit": upstream,
        },
        indent=2,
    ) + "\n"


def import_upstream(root, target_ref):
    if git(root, "status", "--porcelain", "--untracked-files=all").stdout:
        raise SyncError("Refusing to sync a dirty working tree (including untracked files)")
    original_head = resolve_commit(root, "HEAD")
    original_ref = git(root, "symbolic-ref", "--quiet", "HEAD", check=False).stdout.strip()
    target = resolve_commit(root, target_ref)
    last = read_state(root, original_head)
    ancestry = git(root, "merge-base", "--is-ancestor", last, target, check=False)
    if ancestry.returncode == 1:
        raise SyncError("Upstream history was rewritten or moved behind last_synced_commit")
    if ancestry.returncode:
        raise SyncError(f"Cannot validate upstream ancestry: {ancestry.stderr.strip()}")

    first_parents = git(root, "rev-list", "--first-parent", target).stdout.splitlines()
    if last not in first_parents:
        raise SyncError("last_synced_commit is not on the upstream first-parent chain")
    pending = list(reversed(first_parents[:first_parents.index(last)]))
    for commit in [last, *pending]:
        check_state_path_available(root, commit)
    if not pending:
        print(f"Already synchronized with upstream {target}")
        return 0

    candidate = original_head
    with tempfile.TemporaryDirectory(prefix="baas-upstream-sync-") as temporary:
        index_env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "index"))
        for upstream in pending:
            subject = git(root, "show", "-s", "--format=%s", upstream).stdout.strip()
            merged = git(
                root,
                "merge-tree",
                "--write-tree",
                f"--merge-base={last}",
                candidate,
                upstream,
                check=False,
            )
            if merged.returncode:
                diagnostics = "\n".join(
                    part.strip() for part in (merged.stdout, merged.stderr) if part.strip()
                )
                kind = "conflicts" if merged.returncode == 1 else "failed"
                raise SyncError(
                    f"Upstream commit {upstream} ({subject}) {kind}:\n{diagnostics}\n"
                    "HEAD and the working tree have not been changed."
                )
            merged_tree = merged.stdout.splitlines()[0]
            # A separate index builds trees without touching the checkout or its index.
            git(root, "read-tree", merged_tree, env=index_env)
            blob = git(root, "hash-object", "-w", "--stdin", input=state_contents(upstream)).stdout.strip()
            git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},{STATE_PATH}", env=index_env)
            tree = git(root, "write-tree", env=index_env).stdout.strip()
            message = (
                f"sync(upstream): {subject}\n\n"
                f"Upstream-Commit: {upstream}\n"
                f"Upstream-Repository: https://github.com/{REPOSITORY}\n"
            )
            candidate = git(root, "commit-tree", tree, "-p", candidate, input=message).stdout.strip()
            print(f"Prepared {upstream[:12]} as {candidate[:12]}: {subject}")
            last = upstream

    current_ref = git(root, "symbolic-ref", "--quiet", "HEAD", check=False).stdout.strip()
    if resolve_commit(root, "HEAD") != original_head or current_ref != original_ref:
        raise SyncError("HEAD changed during synchronization; refusing to update it")
    if git(root, "status", "--porcelain", "--untracked-files=all").stdout:
        raise SyncError("Working tree changed during synchronization; refusing to update it")
    git(root, "-c", "merge.autoStash=false", "merge", "--ff-only", candidate)
    print(f"Imported {len(pending)} upstream commits without rewriting history")
    return len(pending)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default="refs/remotes/upstream/master")
    args = parser.parse_args(argv)
    try:
        root = git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip()
        import_upstream(root, args.target)
    except SyncError as error:
        print(f"Upstream sync stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
