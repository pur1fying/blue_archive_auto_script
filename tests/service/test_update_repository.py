from pathlib import Path

import pygit2

from service.update import GitOperationHandler
from service.update import checks, repository


def _commit(repo, root: Path, content: str):
    (root / "tracked.txt").write_text(content, encoding="utf-8")
    repo.index.add("tracked.txt")
    repo.index.write()
    tree = repo.index.write_tree()
    signature = pygit2.Signature("BAAS compatibility test", "test@example.invalid")
    parents = [] if repo.head_is_unborn else [repo.head.target]
    return repo.create_commit("HEAD", signature, signature, content, tree, parents)


def test_service_update_handler_keeps_existing_import_paths():
    assert GitOperationHandler is checks.GitOperationHandler is repository.GitOperationHandler


def test_shared_service_handler_preserves_user_files_and_other_branch_on_switch(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    repo = pygit2.init_repository(source, initial_head="master")
    try:
        stable_sha = _commit(repo, source, "stable")
        repo.references.create("refs/heads/dev", stable_sha)
        repo.set_head("refs/heads/dev")
        dev_sha = _commit(repo, source, "development")
        repo.set_head("refs/heads/master")
        repo.reset(stable_sha, pygit2.GIT_RESET_HARD)
    finally:
        repo.free()

    target = tmp_path / "install"
    (target / "config").mkdir(parents=True)
    user_config = target / "config" / "user.json"
    user_config.write_text('{"keep": true}', encoding="utf-8")
    handler = GitOperationHandler(target)
    handler.clone(str(source))
    assert handler.get_local_head_info() == (str(stable_sha), "master")
    assert handler.get_remote_latest_sha(str(source), "dev") == str(dev_sha)

    handler.fetch_and_reset("dev")
    assert handler.get_local_head_info() == (str(dev_sha), "dev")
    assert handler.get_local_head_sha() == str(dev_sha)
    assert (target / "tracked.txt").read_text(encoding="utf-8") == "development"
    assert user_config.read_text(encoding="utf-8") == '{"keep": true}'

    repo = pygit2.Repository(target)
    try:
        assert repo.references["refs/heads/master"].target == stable_sha
    finally:
        repo.free()

    handler.rollback(str(stable_sha))
    assert handler.get_local_head_sha() == str(stable_sha)
    assert (target / "tracked.txt").read_text(encoding="utf-8") == "stable"
    assert user_config.exists()
