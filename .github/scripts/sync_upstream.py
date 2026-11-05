#!/usr/bin/env python3
"""Merge original upstream commits without rewriting either repository's history.

An upstream fast-forward keeps its exact commit ID. Diverged branches receive an
ordinary merge commit whose second parent is the original upstream commit.
Conflicts are aborted for manual resolution; this helper never pushes anything.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


class SyncError(Exception):
    """A synchronization that cannot be completed without manual intervention."""


def git(root, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode:
        details = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"git {' '.join(args)} failed: {details}")
    return result


def resolve_commit(root, ref):
    return git(root, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").stdout.strip()


def git_path(root, name):
    path = Path(git(root, "rev-parse", "--git-path", name).stdout.strip())
    return path if path.is_absolute() else Path(root) / path


def require_idle_checkout(root):
    # An existing conflict must never cause us to abort somebody else's merge.
    for marker in (
        "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge",
        "rebase-apply", "sequencer", "BISECT_START",
    ):
        if git_path(root, marker).exists():
            raise SyncError(f"Refusing to sync while a Git operation is in progress ({marker})")
    if git(root, "status", "--porcelain", "--untracked-files=all").stdout:
        raise SyncError("Refusing to sync a dirty working tree (including untracked files)")


def import_upstream(root, target_ref):
    require_idle_checkout(root)
    target = resolve_commit(root, target_ref)
    original_head = resolve_commit(root, "HEAD")
    ancestry = git(root, "merge-base", "--is-ancestor", target, original_head, check=False)
    if ancestry.returncode == 0:
        print(f"Already synchronized with upstream {target}")
        return 0
    if ancestry.returncode != 1:
        raise SyncError(f"Cannot validate upstream ancestry: {ancestry.stderr.strip()}")

    # Resolve once so a moving ref cannot change what gets merged. --ff overrides
    # merge.ff=only/false, while --commit also overrides configured --no-commit.
    merged = git(
        root,
        "-c", "merge.autoStash=false",
        "merge", "--ff", "--commit", "--no-edit",
        "-m", f"Merge upstream master ({target[:12]})", target,
        check=False,
    )
    if merged.returncode:
        conflicts = git(root, "diff", "--name-only", "--diff-filter=U", check=False).stdout.strip()
        diagnostics = "\n".join(
            part.strip() for part in (merged.stdout, merged.stderr) if part.strip()
        )
        if conflicts:
            diagnostics += f"\nConflicting paths:\n{conflicts}"
        # The idle check guarantees this is our merge. Never reset HEAD or abort
        # an unrelated operation to hide a failure.
        if git_path(root, "MERGE_HEAD").exists():
            aborted = git(root, "merge", "--abort", check=False)
            if aborted.returncode:
                raise SyncError(
                    f"Upstream merge of {target} failed:\n{diagnostics}\n"
                    f"Automatic abort failed: {aborted.stderr.strip()}"
                )
        if resolve_commit(root, "HEAD") != original_head:
            raise SyncError(
                f"Upstream merge of {target} failed:\n{diagnostics}\n"
                "HEAD changed; inspect the repository before retrying."
            )
        raise SyncError(
            f"Upstream merge of {target} failed:\n{diagnostics}\n"
            "HEAD and the working tree have not been changed."
        )
    print(f"Merged original upstream commit {target}; history and commit IDs are preserved")
    return 1


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
