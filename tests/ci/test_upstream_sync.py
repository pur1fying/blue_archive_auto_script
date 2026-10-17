"""Exercise real Git histories; no network or application dependencies required."""

from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / ".github/scripts/sync_upstream.py"


def git(root, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=check
    )
    return result.stdout.strip()


def commit(root, message, files):
    for name, contents in files.items():
        path = root / name
        if contents is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "upstream")
    git(tmp_path, "config", "user.name", "Sync test")
    git(tmp_path, "config", "user.email", "sync@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    base = commit(tmp_path, "initial upstream", {"shared.txt": "first\n" + "middle\n" * 8 + "last\n"})
    git(tmp_path, "checkout", "-b", "fork")
    commit(tmp_path, "fork feature", {"fork.txt": "fork feature\n"})
    return tmp_path, base


def run_sync(root, target="upstream"):
    return subprocess.run(
        [sys.executable, str(SCRIPT), target], cwd=root, capture_output=True, text=True
    )


def assert_success(result):
    assert result.returncode == 0, result.stdout + result.stderr


def assert_ancestor(root, ancestor, descendant="HEAD"):
    git(root, "merge-base", "--is-ancestor", ancestor, descendant)


def assert_unchanged(root, head, index_tree):
    assert git(root, "rev-parse", "HEAD") == head
    assert git(root, "write-tree") == index_tree
    assert git(root, "status", "--porcelain") == ""


def test_diverged_sync_preserves_original_upstream_commits_and_fork_edits(repo):
    root, base = repo
    initial = (root / "shared.txt").read_text()
    before = commit(root, "fork edits", {"shared.txt": initial.replace("first", "fork first")})
    git(root, "checkout", "upstream")
    first = commit(root, "one upstream feature", {"shared.txt": initial.replace("last", "upstream last")})
    second = commit(root, "another upstream feature", {"new.txt": "upstream addition\n"})
    original_objects = [git(root, "cat-file", "commit", sha) for sha in (base, first, second)]
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    assert git(root, "show", "-s", "--format=%P", "HEAD") == f"{before} {second}"
    assert git(root, "rev-list", "--count", "--first-parent", f"{before}..HEAD") == "1"
    for sha, contents in zip((base, first, second), original_objects):
        assert_ancestor(root, sha)
        assert git(root, "cat-file", "commit", sha) == contents
    assert (root / "fork.txt").read_text() == "fork feature\n"
    assert (root / "new.txt").read_text() == "upstream addition\n"
    assert (root / "shared.txt").read_text() == initial.replace("first", "fork first").replace("last", "upstream last")
    assert git(root, "status", "--porcelain") == ""


def test_repeated_sync_keeps_original_hashes_and_uses_current_fork_parent(repo):
    root, _ = repo
    git(root, "checkout", "upstream")
    first = commit(root, "first upstream", {"one.txt": "one\n"})
    git(root, "checkout", "fork")
    assert_success(run_sync(root))
    assert_ancestor(root, first)
    before = commit(root, "later fork work", {"fork.txt": "more fork work\n"})
    git(root, "checkout", "upstream")
    second = commit(root, "second upstream", {"two.txt": "two\n"})
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    assert git(root, "show", "-s", "--format=%P", "HEAD") == f"{before} {second}"
    assert_ancestor(root, first)
    assert_ancestor(root, second)
    assert (root / "fork.txt").read_text() == "more fork work\n"
    synced = git(root, "rev-parse", "HEAD")
    assert_success(run_sync(root))
    assert git(root, "rev-parse", "HEAD") == synced


def test_conflict_aborts_and_preserves_refs_index_and_checkout(repo):
    root, _ = repo
    original = (root / "shared.txt").read_text()
    before = commit(root, "fork modification", {"shared.txt": original.replace("first", "fork")})
    git(root, "checkout", "upstream")
    commit(root, "non conflicting upstream", {"new.txt": "not applied\n"})
    conflicting = commit(root, "conflicting upstream", {"shared.txt": original.replace("first", "upstream")})
    git(root, "checkout", "fork")
    refs = git(root, "show-ref")
    index = git(root, "write-tree")
    checkout = (root / "shared.txt").read_bytes()

    result = run_sync(root)

    assert result.returncode == 1
    assert conflicting in result.stderr
    assert "CONFLICT" in result.stderr
    assert "Conflicting paths:\nshared.txt" in result.stderr
    assert git(root, "show-ref") == refs
    assert_unchanged(root, before, index)
    assert (root / "shared.txt").read_bytes() == checkout
    assert not (root / "new.txt").exists()
    assert not (root / ".git/MERGE_HEAD").exists()


def test_copied_content_still_creates_real_merge_with_unchanged_tree(repo):
    root, _ = repo
    before = commit(root, "equivalent fork fix", {"applied.txt": "same\n"})
    git(root, "checkout", "upstream")
    upstream = commit(root, "upstream fix", {"applied.txt": "same\n"})
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    assert git(root, "show", "-s", "--format=%P", "HEAD") == f"{before} {upstream}"
    assert git(root, "diff", "--name-only", before, "HEAD") == ""
    assert_ancestor(root, upstream)


def test_upstream_merge_and_all_its_original_parents_are_preserved(repo):
    root, base = repo
    before = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "upstream")
    git(root, "checkout", "-b", "upstream-feature")
    first = commit(root, "feature first", {"feature.txt": "first\n"})
    second = commit(root, "feature second", {"feature.txt": "second\n"})
    git(root, "checkout", "upstream")
    git(root, "merge", "--no-ff", "upstream-feature", "-m", "Merge feature PR")
    upstream_merge = git(root, "rev-parse", "HEAD")
    upstream_parents = git(root, "show", "-s", "--format=%P", upstream_merge)
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    assert git(root, "show", "-s", "--format=%P", "HEAD") == f"{before} {upstream_merge}"
    assert git(root, "show", "-s", "--format=%P", upstream_merge) == upstream_parents == f"{base} {second}"
    for sha in (base, first, second, upstream_merge):
        assert_ancestor(root, sha)
    assert (root / "feature.txt").read_text() == "second\n"


@pytest.mark.parametrize("ff_config", ["false", "only"])
def test_explicit_ff_allows_diverged_merge_despite_git_config(repo, ff_config):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    git(root, "config", "merge.ff", ff_config)
    git(root, "checkout", "upstream")
    upstream = commit(root, "new upstream", {"new.txt": "upstream\n"})
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    assert git(root, "show", "-s", "--format=%P", "HEAD") == f"{before} {upstream}"


def test_fast_forward_preserves_exact_upstream_head_even_with_no_ff_config(repo):
    root, base = repo
    git(root, "checkout", "upstream")
    upstream = commit(root, "new upstream", {"new.txt": "new\n"})
    git(root, "checkout", "-b", "mirror", base)
    git(root, "config", "merge.ff", "false")

    assert_success(run_sync(root))

    assert git(root, "rev-parse", "HEAD") == upstream
    assert git(root, "rev-list", "--count", f"{base}..HEAD") == "1"


def test_noop_for_already_contained_target_even_if_upstream_ref_moves_back(repo):
    root, base = repo
    before = git(root, "rev-parse", "HEAD")
    index = git(root, "write-tree")

    result = run_sync(root, base)

    assert_success(result)
    assert "Already synchronized" in result.stdout
    assert_unchanged(root, before, index)


def test_unrelated_history_is_rejected_without_changing_checkout(repo):
    root, _ = repo
    git(root, "checkout", "--orphan", "rewritten")
    git(root, "rm", "-rf", ".")
    commit(root, "new upstream history", {"different.txt": "different\n"})
    git(root, "checkout", "fork")
    before = git(root, "rev-parse", "HEAD")
    index = git(root, "write-tree")

    result = run_sync(root, "rewritten")

    assert result.returncode == 1
    assert "unrelated histories" in result.stderr
    assert_unchanged(root, before, index)


@pytest.mark.parametrize("dirty", ["tracked", "untracked", "staged"])
def test_dirty_checkout_is_rejected_without_changing_local_work(repo, dirty):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    if dirty == "untracked":
        (root / "untracked.txt").write_text("local\n")
    else:
        (root / "fork.txt").write_text("local\n")
        if dirty == "staged":
            git(root, "add", "fork.txt")
    status = git(root, "status", "--porcelain")

    result = run_sync(root)

    assert result.returncode == 1
    assert "dirty" in result.stderr
    assert git(root, "rev-parse", "HEAD") == before
    assert git(root, "status", "--porcelain") == status


def test_existing_conflicted_merge_is_not_aborted(repo):
    root, _ = repo
    original = (root / "shared.txt").read_text()
    before = commit(root, "fork modification", {"shared.txt": original.replace("first", "fork")})
    git(root, "checkout", "upstream")
    upstream = commit(root, "conflicting upstream", {"shared.txt": original.replace("first", "upstream")})
    git(root, "checkout", "fork")
    git(root, "merge", upstream, check=False)
    merge_head = (root / ".git/MERGE_HEAD").read_bytes()
    checkout = (root / "shared.txt").read_bytes()
    status = git(root, "status", "--porcelain")

    result = run_sync(root)

    assert result.returncode == 1
    assert "operation is in progress (MERGE_HEAD)" in result.stderr
    assert git(root, "rev-parse", "HEAD") == before
    assert (root / ".git/MERGE_HEAD").read_bytes() == merge_head
    assert (root / "shared.txt").read_bytes() == checkout
    assert git(root, "status", "--porcelain") == status


@pytest.mark.parametrize("marker", [
    "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer", "BISECT_START",
])
def test_existing_git_operations_are_refused_even_when_checkout_is_clean(repo, marker):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    index = git(root, "write-tree")
    path = root / ".git" / marker
    if marker in {"rebase-merge", "rebase-apply", "sequencer"}:
        path.mkdir()
    else:
        path.write_text(before + "\n")

    result = run_sync(root)

    assert result.returncode == 1
    assert f"operation is in progress ({marker})" in result.stderr
    assert path.exists()
    assert_unchanged(root, before, index)


def test_detached_head_is_supported_without_moving_fork_branch(repo):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "upstream")
    upstream = commit(root, "new upstream", {"new.txt": "new\n"})
    git(root, "checkout", "--detach", before)

    assert_success(run_sync(root))

    assert git(root, "rev-parse", "fork") == before
    assert git(root, "show", "-s", "--format=%P", "HEAD") == f"{before} {upstream}"
    assert_ancestor(root, upstream)


def test_default_remote_tracking_target(repo):
    root, _ = repo
    git(root, "checkout", "upstream")
    upstream = commit(root, "new upstream", {"new.txt": "new\n"})
    git(root, "update-ref", "refs/remotes/upstream/master", upstream)
    git(root, "checkout", "fork")

    result = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=root, capture_output=True, text=True
    )

    assert_success(result)
    assert_ancestor(root, upstream)
