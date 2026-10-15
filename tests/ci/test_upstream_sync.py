"""Exercise real Git histories; no network or application dependencies required."""

import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / ".github/scripts/sync_upstream.py"
STATE_PATH = ".github/upstream-sync.json"


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


def state(last):
    return json.dumps({
        "schema_version": 1,
        "repository": "pur1fying/blue_archive_auto_script",
        "branch": "master",
        "last_synced_commit": last,
    }) + "\n"


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "upstream")
    git(tmp_path, "config", "user.name", "Sync test")
    git(tmp_path, "config", "user.email", "sync@example.com")
    git(tmp_path, "config", "commit.gpgsign", "false")
    base = commit(tmp_path, "initial upstream", {"shared.txt": "first\n" + "middle\n" * 8 + "last\n"})
    git(tmp_path, "checkout", "-b", "fork")
    commit(tmp_path, "fork state", {STATE_PATH: state(base), "fork.txt": "fork feature\n"})
    return tmp_path, base


def run_sync(root, target="upstream"):
    return subprocess.run(
        [sys.executable, str(SCRIPT), target], cwd=root, capture_output=True, text=True
    )


def assert_success(result):
    assert result.returncode == 0, result.stdout + result.stderr


def assert_unchanged(root, head, index_tree):
    assert git(root, "rev-parse", "HEAD") == head
    assert git(root, "write-tree") == index_tree
    assert git(root, "status", "--porcelain") == ""


def test_multiple_commits_preserve_fork_and_separate_same_file_edits(repo):
    root, base = repo
    initial = (root / "shared.txt").read_text()
    before = commit(root, "fork edits", {"shared.txt": initial.replace("first", "fork first")})
    git(root, "checkout", "upstream")
    first = commit(root, "one upstream feature", {"shared.txt": initial.replace("last", "upstream last")})
    second = commit(root, "another upstream feature", {"new.txt": "upstream addition\n"})
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    imports = git(root, "rev-list", "--reverse", f"{before}..HEAD").splitlines()
    assert len(imports) == 2
    assert git(root, "show", "-s", "--format=%P", imports[0]) == before
    assert git(root, "show", "-s", "--format=%P", imports[1]) == imports[0]
    assert json.loads(git(root, "show", f"{imports[0]}:{STATE_PATH}"))["last_synced_commit"] == first
    assert json.loads((root / STATE_PATH).read_text())["last_synced_commit"] == second
    assert (root / "fork.txt").read_text() == "fork feature\n"
    assert (root / "new.txt").read_text() == "upstream addition\n"
    assert (root / "shared.txt").read_text() == initial.replace("first", "fork first").replace("last", "upstream last")
    assert git(root, "status", "--porcelain") == ""
    synced_head = git(root, "rev-parse", "HEAD")
    assert_success(run_sync(root))
    assert git(root, "rev-parse", "HEAD") == synced_head


def test_later_sync_uses_recorded_upstream_even_when_not_head_ancestor(repo):
    root, _ = repo
    git(root, "checkout", "upstream")
    first = commit(root, "first upstream", {"one.txt": "one\n"})
    git(root, "checkout", "fork")
    assert_success(run_sync(root))
    assert subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", first, "HEAD"]).returncode == 1
    before = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "upstream")
    second = commit(root, "second upstream", {"two.txt": "two\n"})
    git(root, "checkout", "fork")
    assert_success(run_sync(root))
    assert git(root, "show", "-s", "--format=%P", "HEAD") == before
    assert json.loads((root / STATE_PATH).read_text())["last_synced_commit"] == second


def test_conflict_after_prepared_commit_leaves_refs_index_and_checkout_untouched(repo):
    root, _ = repo
    original = (root / "shared.txt").read_text()
    before = commit(root, "fork modification", {"shared.txt": original.replace("first", "fork")})
    git(root, "checkout", "upstream")
    commit(root, "non conflicting upstream", {"new.txt": "not applied\n"})
    conflicting = commit(root, "conflicting upstream", {"shared.txt": original.replace("first", "upstream")})
    git(root, "checkout", "fork")
    refs = git(root, "show-ref")
    index = git(root, "write-tree")

    result = run_sync(root)

    assert result.returncode == 1
    assert conflicting in result.stderr
    assert "CONFLICT" in result.stderr
    assert "shared.txt" in result.stderr
    assert git(root, "show-ref") == refs
    assert_unchanged(root, before, index)
    assert not (root / "new.txt").exists()


def test_already_applied_change_still_advances_metadata(repo):
    root, _ = repo
    before = commit(root, "equivalent fork fix", {"applied.txt": "same\n"})
    git(root, "checkout", "upstream")
    upstream = commit(root, "upstream fix", {"applied.txt": "same\n"})
    git(root, "checkout", "fork")
    assert_success(run_sync(root))
    assert git(root, "diff", "--name-only", before, "HEAD") == STATE_PATH
    assert json.loads((root / STATE_PATH).read_text())["last_synced_commit"] == upstream


def test_already_removed_files_are_not_replayed_from_old_fork_commits(repo):
    root, _ = repo
    git(root, "checkout", "upstream")
    old = commit(root, "old installer", {"marker.txt": "original\n"})
    git(root, "checkout", "fork")
    commit(root, "previous installer baseline", {STATE_PATH: state(old), "marker.txt": "original\n"})
    commit(root, "fork extends installer", {"marker.txt": "fork integration\n"})
    before = commit(root, "fork removes installer", {"marker.txt": None})
    git(root, "checkout", "upstream")
    removed = commit(root, "remove installer", {"marker.txt": None})
    git(root, "checkout", "fork")

    assert_success(run_sync(root))

    assert not (root / "marker.txt").exists()
    assert git(root, "diff", "--name-only", before, "HEAD") == STATE_PATH
    assert json.loads((root / STATE_PATH).read_text())["last_synced_commit"] == removed


def test_noop_does_not_create_commit(repo):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    index = git(root, "write-tree")
    result = run_sync(root)
    assert_success(result)
    assert "Already synchronized" in result.stdout
    assert_unchanged(root, before, index)


def test_upstream_merge_imports_pr_delta_as_one_single_parent_commit(repo):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "upstream")
    git(root, "checkout", "-b", "upstream-feature")
    commit(root, "feature first", {"feature.txt": "first\n"})
    commit(root, "feature second", {"feature.txt": "second\n"})
    git(root, "checkout", "upstream")
    git(root, "merge", "--no-ff", "upstream-feature", "-m", "Merge feature PR")
    merged = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "fork")
    assert_success(run_sync(root))
    assert git(root, "rev-list", "--count", f"{before}..HEAD") == "1"
    assert git(root, "show", "-s", "--format=%P", "HEAD") == before
    assert (root / "feature.txt").read_text() == "second\n"
    assert json.loads((root / STATE_PATH).read_text())["last_synced_commit"] == merged


def test_upstream_rewrite_is_rejected(repo):
    root, _ = repo
    git(root, "checkout", "--orphan", "rewritten")
    git(root, "rm", "-rf", ".")
    commit(root, "new upstream history", {"different.txt": "different\n"})
    git(root, "checkout", "fork")
    before = git(root, "rev-parse", "HEAD")
    index = git(root, "write-tree")
    result = run_sync(root, "rewritten")
    assert result.returncode == 1
    assert "rewritten" in result.stderr
    assert_unchanged(root, before, index)


def test_state_must_lie_on_first_parent_chain(repo):
    root, base = repo
    git(root, "checkout", "upstream")
    git(root, "checkout", "-b", "side")
    side = commit(root, "side commit", {"side.txt": "side\n"})
    git(root, "checkout", "upstream")
    git(root, "merge", "--no-ff", "side", "-m", "merge side")
    git(root, "checkout", "fork")
    before = commit(root, "invalid state", {STATE_PATH: state(side)})
    index = git(root, "write-tree")
    result = run_sync(root)
    assert result.returncode == 1
    assert "first-parent" in result.stderr
    assert_unchanged(root, before, index)


@pytest.mark.parametrize("dirty", ["tracked", "untracked", "staged"])
def test_dirty_checkout_is_rejected(repo, dirty):
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


@pytest.mark.parametrize("collision", [STATE_PATH, ".github"])
def test_upstream_cannot_take_sync_metadata_path(repo, collision):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "upstream")
    commit(root, "metadata collision", {collision: "upstream owns this\n"})
    git(root, "checkout", "fork")
    index = git(root, "write-tree")
    result = run_sync(root)
    assert result.returncode == 1
    assert STATE_PATH in result.stderr
    assert_unchanged(root, before, index)


def test_detached_head_is_supported(repo):
    root, _ = repo
    before = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "upstream")
    commit(root, "new upstream", {"new.txt": "new\n"})
    git(root, "checkout", "--detach", before)
    assert_success(run_sync(root))
    assert git(root, "rev-parse", "fork") == before
    assert git(root, "show", "-s", "--format=%P", "HEAD") == before
