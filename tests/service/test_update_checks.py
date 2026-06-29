from __future__ import annotations

from service.update import checks


def test_remote_sha_uses_temporary_bare_repo_without_git(monkeypatch, tmp_path):
    created = {}

    class FakeRemote:
        def ls_remotes(self):
            return [
                {"name": "refs/heads/other", "oid": "0" * 40},
                {"name": "refs/heads/master", "oid": "1" * 40},
            ]

    class FakeRemotes:
        def create_anonymous(self, url):
            created["url"] = url
            return FakeRemote()

    class FakeRepo:
        remotes = FakeRemotes()

    def fake_repository(_path):
        raise AssertionError("remote SHA probing must not require cwd to be a git repository")

    def fake_init_repository(path, bare):
        created["path"] = path
        created["bare"] = bare
        return FakeRepo()

    monkeypatch.setattr(checks.shutil, "which", lambda _name: None)
    monkeypatch.setattr(checks.pygit2, "Repository", fake_repository)
    monkeypatch.setattr(checks.pygit2, "init_repository", fake_init_repository)

    handler = checks.GitOperationHandler(tmp_path / "not-a-repo")
    sha = handler.get_remote_latest_sha("https://example.invalid/repo.git", "master")

    assert sha == "1" * 40
    assert created["url"] == "https://example.invalid/repo.git"
    assert created["bare"] is True

