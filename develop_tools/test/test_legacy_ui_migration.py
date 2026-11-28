import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gui.util import legacy_migration


class LegacyUiMigrationTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "linux", "checks Linux's XDG data directory")
    def test_uses_the_platform_user_data_location(self):
        with tempfile.TemporaryDirectory() as data:
            with patch.dict("os.environ", XDG_DATA_HOME=data):
                self.assertEqual(
                    legacy_migration._handoff_directory(),
                    Path(data) / "BAAS" / "legacy-ui-migration",
                )

    def test_keeps_existing_backup_when_a_new_snapshot_cannot_be_opened(self):
        with tempfile.TemporaryDirectory() as workspace:
            directory = Path(workspace) / "user-data" / "BAAS" / "legacy-ui-migration"
            root = Path(workspace) / "old-install"
            profile = root / "config" / "配置"
            profile.mkdir(parents=True)
            config = profile / "config.json"
            config.write_text("saved", encoding="utf-8")
            with patch.object(legacy_migration, "_handoff_directory", return_value=directory):
                self.assertTrue(legacy_migration.sync_legacy_config(root, "zh", "dark"))
                legacy_migration.suppress_legacy_notice()
                self.assertFalse(legacy_migration.sync_legacy_config(root, "zh", "dark"))
                bundle = directory / ".baas.legacy"
                preferences = json.loads((bundle / "baas.preference.json").read_text(encoding="utf-8"))
                self.assertEqual(preferences["installPath"], str(root.resolve()))
                with patch.object(legacy_migration.shutil, "copytree", side_effect=PermissionError):
                    with self.assertRaises(PermissionError):
                        legacy_migration.sync_legacy_config(root, "zh", "dark")
                self.assertEqual((bundle / "config" / "配置" / "config.json").read_text(), "saved")
                self.assertTrue((bundle / "no_notification").is_file())
                self.assertEqual(config.read_text(), "saved")
