"""Exercise the CNB action against local Git repositories without network access.

Run with ``python .github/scripts/test_sync_cnb.py`` from the repository root.
"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "actions" / "sync-to-cnb" / "sync.sh"
TARGET_URL = "https://cnb.cool/example/test-mirror.git"


def bash_path():
    if os.name == "nt":
        bundled_bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/usr/bin/bash.exe"
        if bundled_bash.is_file():
            return str(bundled_bash)
    return shutil.which("bash")


@unittest.skipUnless(shutil.which("git") and bash_path(), "Git and Bash are required")
class CnbSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-cnb-sync-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / "origin.git"
        self.target = self.root / "target.git"
        self.writer = self.root / "writer"
        self.checkout = self.root / "checkout"
        self.config = self.root / "gitconfig"
        self.env = os.environ.copy()
        self.env.update({
            "GIT_CONFIG_GLOBAL": self.config.as_posix(),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "CNB_REPO_URL": TARGET_URL,
            "CNB_SYNC_TOKEN": "local-test-token",
        })
        self.config.write_text("", encoding="utf-8")
        self.git(self.root, "config", "--file", str(self.config), "user.name", "CNB sync test")
        self.git(self.root, "config", "--file", str(self.config), "user.email", "cnb-test@example.invalid")
        # Keep the production HTTPS input while routing Git to a disposable bare repository.
        self.git(self.root, "config", "--file", str(self.config),
                 "url." + self.target.as_uri() + ".insteadOf", TARGET_URL)
        self.git(self.root, "init", "--bare", str(self.origin))
        self.git(self.root, "init", "--bare", str(self.target))
        self.git(self.root, "init", "-b", "master", str(self.writer))
        self.commit(self.writer, "initial")
        self.git(self.writer, "branch", "feature/original")
        self.git(self.writer, "tag", "v1")
        self.git(self.writer, "remote", "add", "origin", str(self.origin))
        self.publish()
        self.git(self.root, "clone", "--no-local", "--branch", "master", str(self.origin), str(self.checkout))

    def git(self, cwd, *args, check=True):
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=self.env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if check and result.returncode:
            self.fail(f"git {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
        return result.stdout.strip()

    def commit(self, cwd, name):
        (cwd / "content.txt").write_text(name, encoding="utf-8")
        self.git(cwd, "add", "content.txt")
        self.git(cwd, "commit", "-m", name)
        return self.git(cwd, "rev-parse", "HEAD")

    def publish(self):
        self.git(self.writer, "push", "origin", "--all")
        self.git(self.writer, "push", "origin", "--tags")

    def refs(self, repository, prefix="refs/"):
        output = self.git(repository, "for-each-ref", "--format=%(refname) %(objectname)", prefix)
        return dict(line.split(" ", 1) for line in output.splitlines())

    def sync(self, success=True):
        result = subprocess.run(
            [bash_path(), "--noprofile", "--norc", SCRIPT.as_posix()],
            cwd=self.checkout, env=self.env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        return result

    def test_syncs_current_origin_branches_and_tags_but_not_pull_request_refs(self):
        old_checkout = self.git(self.checkout, "rev-parse", "HEAD")
        latest = self.commit(self.writer, "new master after checkout")
        self.git(self.writer, "branch", "feature/new")
        self.git(self.writer, "tag", "v2")
        self.publish()
        self.git(self.origin, "update-ref", "refs/pull/612/head", latest)
        self.git(self.checkout, "update-ref", "refs/pull/613/head", old_checkout)

        self.sync()

        self.assertEqual(self.refs(self.target, "refs/heads/"), self.refs(self.origin, "refs/heads/"))
        self.assertEqual(self.refs(self.target, "refs/tags/"), self.refs(self.origin, "refs/tags/"))
        self.assertFalse(self.refs(self.target, "refs/pull/"))
        self.assertFalse(self.refs(self.target, "refs/remotes/"))
        self.assertEqual(self.git(self.target, "rev-parse", "master"), latest)
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), old_checkout)

    def test_preserves_remote_only_refs_and_prunes_only_the_local_fetch_namespace(self):
        self.sync()
        initial = self.git(self.target, "rev-parse", "master")
        self.git(self.target, "update-ref", "refs/heads/target-only", initial)
        self.git(self.target, "update-ref", "refs/tags/target-only", initial)
        self.git(self.writer, "push", "origin", "--delete", "feature/original")
        self.git(self.writer, "push", "origin", ":refs/tags/v1")

        self.sync()

        self.assertFalse(self.refs(self.checkout, "refs/cnb-sync/heads/feature/original"))
        self.assertFalse(self.refs(self.checkout, "refs/cnb-sync/tags/v1"))
        self.assertEqual(self.refs(self.target, "refs/heads/").get("refs/heads/feature/original"), initial)
        self.assertEqual(self.refs(self.target, "refs/tags/").get("refs/tags/v1"), initial)
        self.assertEqual(self.refs(self.target, "refs/heads/").get("refs/heads/target-only"), initial)
        self.assertEqual(self.refs(self.target, "refs/tags/").get("refs/tags/target-only"), initial)

    def test_divergent_target_branch_is_rejected_without_rewriting_history(self):
        self.sync()
        target_writer = self.root / "target-writer"
        self.git(self.root, "clone", "--no-local", "--branch", "master", str(self.target), str(target_writer))
        target_commit = self.commit(target_writer, "target-only commit")
        self.git(target_writer, "push", "origin", "master")
        source_commit = self.commit(self.writer, "source-only commit")
        self.publish()

        self.sync(success=False)

        self.assertEqual(self.git(self.target, "rev-parse", "master"), target_commit)
        self.assertEqual(self.git(self.origin, "rev-parse", "master"), source_commit)


if __name__ == "__main__":
    unittest.main()
