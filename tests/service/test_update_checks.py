from __future__ import annotations

from deploy.installer.const import GetShaMethod
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


def test_android_repo_sha_uses_archive_probe_for_baas_cdn(monkeypatch):
    requested_urls = []

    class FakeResponse:
        def __init__(self, url):
            self.url = url

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1):
            yield b"x"

        def json(self):
            return {"commit": {"sha": "455caf" + "0" * 34}}

    def fake_get(url, **kwargs):
        requested_urls.append((url, kwargs))
        return FakeResponse(url)

    def fail_git_wrapper(_config, _timeout):
        raise AssertionError("Android GitHub proxy checks must not use pygit2/git")

    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setattr(checks.requests, "get", fake_get)
    monkeypatch.setattr(checks, "_git_wrapper_get_latest_sha", fail_git_wrapper)

    result = checks.test_repo_sha(
        {
            "name": "baas_cdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://baas-cdn.kiramei.workers.dev/https://github.com/Kiramei/baas-dev.git",
            "branch": "master",
        },
        timeout=3.0,
    )

    assert result["success"] is True
    assert result["value"] == "455caf" + "0" * 34
    assert requested_urls[0][0] == (
        "https://baas-cdn.kiramei.workers.dev/"
        "https://github.com/Kiramei/baas-dev/archive/refs/heads/master.zip"
    )
    assert requested_urls[0][1]["stream"] is True
    assert requested_urls[1][0] == "https://api.github.com/repos/Kiramei/baas-dev/branches/master"


def test_githubfast_archive_url_is_generated_from_accelerated_repo_url():
    archive_url = checks._github_archive_url_for_config(
        {
            "name": "githubfast",
            "url": "https://githubfast.com/Kiramei/baas-dev.git",
            "branch": "master",
        }
    )

    assert archive_url == "https://githubfast.com/Kiramei/baas-dev/archive/refs/heads/master.zip"


def test_non_github_android_sha_keeps_git_wrapper(monkeypatch):
    monkeypatch.setenv("BAAS_ANDROID", "1")
    monkeypatch.setattr(checks, "_git_wrapper_get_latest_sha", lambda _config, _timeout: (False, "git failed"))

    result = checks.test_repo_sha(
        {
            "name": "gitee",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gitee.com/kiramei/baas-dev.git",
            "branch": "master",
        },
        timeout=3.0,
    )

    assert result["success"] is False
    assert result["error"] == "git failed"
