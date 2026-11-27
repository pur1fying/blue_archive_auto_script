import asyncio
import json
import os
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from watchfiles import Change

from service.conf.manager import ConfigManager
from core.config.config_set import ConfigSet
from core.scheduler import Scheduler


class ConfigSyncTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.profile = root / "config" / "demo"
        self.profile.mkdir(parents=True)
        self.config = self.profile / "config.json"
        self.event = self.profile / "event.json"
        self.config.write_text('{"ap": {"count": 12}}', encoding="utf-8")
        self.event.write_text('[{"next_tick": 10}]', encoding="utf-8")
        self.manager = ConfigManager(root, asyncio.get_running_loop())
        await self.manager.scan_once()
        for resource in ("config", "event"):
            await self.manager.get_snapshot(resource, "demo")
        self.updates = await self.manager.subscribe_updates()

    async def test_watcher_survives_partial_document_and_resumes_pushes(self):
        other_profile = self.profile.with_name("other")
        other_profile.mkdir()
        other_config = other_profile / "config.json"
        other_config.write_text('{"ap": {"count": 5}}', encoding="utf-8")
        (other_profile / "event.json").write_text("[]", encoding="utf-8")
        await self.manager.get_snapshot("config", "other")

        async def batches(*args, **kwargs):
            self.assertEqual(self.updates.get_nowait()["resource_id"], "other")  # Initial discovery.
            self.config.write_bytes(b'{"ap":')
            self.event.write_text('[{"next_tick": 20}]', encoding="utf-8")
            other_config.write_text('{"ap": {"count": 6}}', encoding="utf-8")
            yield {(Change.modified, str(path)) for path in (self.config, self.event, other_config)}
            pushes = [self.updates.get_nowait(), self.updates.get_nowait()]
            ops = {(msg["resource"], msg["resource_id"]): msg["ops"] for msg in pushes}
            self.assertEqual(ops["event", "demo"], [{"op": "replace", "path": "", "value": [{"next_tick": 20}]}])
            self.assertEqual(ops["config", "other"], [{"op": "replace", "path": "/ap/count", "value": 6}])
            last_good = await self.manager.get_snapshot("config", "demo")
            self.assertEqual(last_good.data["ap"]["count"], 12)
            self.assertTrue(self.updates.empty())

            self.config.write_text('{"ap": {"count": 34}}', encoding="utf-8")
            yield {(Change.modified, str(self.config))}

        with patch("service.conf.manager.awatch", batches), self.assertLogs(level="WARNING"):
            await self.manager.watch_filesystem()
        update = self.updates.get_nowait()
        self.assertEqual(update["resource"], "config")
        self.assertEqual(update["ops"], [{"op": "replace", "path": "/ap/count", "value": 34}])
        self.assertEqual((await self.manager.get_snapshot("config", "demo")).data["ap"]["count"], 34)

    async def test_pull_recovers_missed_event_and_notifies_subscribers_once(self):
        old_mtime = self.event.stat().st_mtime
        self.event.write_text('[{"next_tick": 30}]', encoding="utf-8")
        os.utime(self.event, (old_mtime + 1, old_mtime + 1))
        snapshot = await self.manager.get_snapshot("event", "demo")
        self.assertEqual(snapshot.data, [{"next_tick": 30}])
        self.assertEqual(self.updates.get_nowait()["ops"][0]["value"], snapshot.data)
        await self.manager._handle_watch_batch({(Change.modified, str(self.event))})
        self.assertTrue(self.updates.empty())

    async def test_transient_read_error_retries_without_a_second_notification(self):
        self.config.write_text('{"ap": {"count": 45}}', encoding="utf-8")
        load = self.manager._load_from_disk
        attempts = 0

        def read(*args):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise PermissionError("file temporarily busy")
            return load(*args)

        with patch.object(self.manager, "_load_from_disk", side_effect=read):
            await self.manager._handle_watch_batch({(Change.modified, str(self.config))})
        self.assertEqual(attempts, 2)
        self.assertEqual(self.updates.get_nowait()["ops"][0]["value"], 45)

    def test_failed_saves_leave_complete_files_in_place(self):
        @dataclass
        class Config:
            value: object

        config = ConfigSet.__new__(ConfigSet)
        config.config_dir = self.profile
        config.config = Config(object())
        scheduler = Scheduler.__new__(Scheduler)
        scheduler.event_config_path = self.event
        scheduler._event_config = [object()]
        for path, save in (
            (self.config, config.save),
            (self.event, scheduler._commit_change),
            (self.config, lambda: self.manager._write_json(self.config, {"bad": object()}, "config")),
        ):
            with self.subTest(save=save):
                previous = path.read_bytes()
                with self.assertRaises(TypeError):
                    save()
                self.assertEqual(path.read_bytes(), previous)
                self.assertEqual(set(self.profile.iterdir()), {self.config, self.event})

        mode = self.config.stat().st_mode
        config.config.value = "信用点"
        config.save()
        self.assertEqual(self.config.read_text(encoding="utf-8"), json.dumps(
            {"value": "信用点"}, indent=4, ensure_ascii=False,
        ))
        self.assertEqual(self.config.stat().st_mode, mode)
