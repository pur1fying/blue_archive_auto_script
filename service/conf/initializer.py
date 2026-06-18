from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Iterable, Union

from core.config import default_config
from core.config.config_set import ConfigSet
from .paths import ensure_safe_config_id, resolve_config_dir


class ConfigInitializer:
    """Create and migrate BAAS config files under one project root."""

    def __init__(self, project_root: Union[Path, str] = ".") -> None:
        self.project_root = Path(project_root)
        self.config_root = self.project_root / "config"
        self.error_log = self.project_root / "error.log"

    def check_config(self, config_ids: Union[str, Iterable[str]], server=None, name=None) -> None:
        self.config_root.mkdir(exist_ok=True)
        self.check_static_config()
        ids = [config_ids] if isinstance(config_ids, str) else list(config_ids)
        for raw_id in ids:
            config_id = ensure_safe_config_id(raw_id)
            config_dir = resolve_config_dir(self.config_root, config_id)
            config_dir.mkdir(exist_ok=True)
            self.delete_deprecated_config("display.json", config_id)
            self.check_and_update_user_config(config_id, server=server, name=name)
            config = ConfigSet(config_dir=config_id)
            config.update_create_quantity_entry()
            self.check_event_config(config_id, config)
            self.check_switch_config(config_id)

    def check_switch_config(self, config_id: str = "default_config") -> None:
        path = resolve_config_dir(self.config_root, config_id) / "switch.json"
        path.write_text(default_config.SWITCH_DEFAULT_CONFIG, encoding="utf-8")

    def check_event_config(self, config_id: str = "default_config", user_config=None) -> None:
        path = resolve_config_dir(self.config_root, config_id) / "event.json"
        default_event_config = json.loads(default_config.EVENT_DEFAULT_CONFIG)
        server = user_config.server_mode
        enable_state = user_config.config.new_event_enable_state
        if server != "CN":
            for item in default_event_config:
                for reset in item["daily_reset"]:
                    reset[0] = reset[0] - 1
        if not path.exists():
            self._write_error(f"path not exist\n{config_id}")
            self._write_json(path, default_event_config, indent=2)
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for index, default_item in enumerate(default_event_config):
                existing = next((item for item in data if item["func_name"] == default_item["func_name"]), None)
                if existing is None:
                    temp = default_item
                    if enable_state == "on":
                        temp["enabled"] = True
                    elif enable_state == "off":
                        temp["enabled"] = False
                    data.insert(index, temp)
                    continue
                if not isinstance(existing, dict):
                    raise TypeError("expected dict but found {} for existing".format(type(existing)))
                for reset_index, reset in enumerate(existing["daily_reset"]):
                    if len(reset) != 3:
                        existing["daily_reset"][reset_index] = [0, 0, 0]
                self._merge_missing_keys(default_item, existing)
            self._write_json(path, data, indent=2)
        except Exception as exc:  # noqa: BLE001 - preserve recovery behavior
            self._write_error(f"{exc}\n{config_id}")
            self._write_json(path, default_event_config, indent=2)

    def delete_deprecated_config(self, file_name, config_id: Union[str, None] = None) -> None:
        names = [file_name] if isinstance(file_name, str) else list(file_name)
        base = self.config_root if config_id is None else resolve_config_dir(self.config_root, config_id)
        for name in names:
            target = (base / name).resolve()
            if target.exists() and target.parent == base.resolve():
                target.unlink()

    def check_static_config(self) -> None:
        path = self.config_root / "static.json"
        try:
            path.write_text(default_config.STATIC_DEFAULT_CONFIG, encoding="utf-8")
        except Exception:  # noqa: BLE001 - preserve recovery behavior
            if path.exists():
                path.unlink()
            path.write_text(default_config.STATIC_DEFAULT_CONFIG, encoding="utf-8")

    def check_and_update_user_config(self, config_id: str = "default_config", server=None, name=None) -> None:
        path = resolve_config_dir(self.config_root, config_id) / "config.json"
        if not path.exists():
            path.write_text(default_config.DEFAULT_CONFIG, encoding="utf-8")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data = self.update_config_reserve_old(data, json.loads(default_config.DEFAULT_CONFIG))
            if name is not None:
                data["name"] = name
            if server is not None:
                data["server"] = server
            self._write_json(path, data, indent=2)
        except Exception:  # noqa: BLE001 - preserve recovery behavior
            if path.exists():
                path.unlink()
            path.write_text(default_config.DEFAULT_CONFIG, encoding="utf-8")

    @staticmethod
    def update_config_reserve_old(config_old: dict, config_new: dict) -> dict:
        for key in config_new:
            if key not in config_old:
                config_old[key] = config_new[key]
        for key in list(config_old):
            if key not in config_new:
                del config_old[key]
        return config_old

    @staticmethod
    def check_single_event(new_event: dict, old_event: dict) -> dict:
        return ConfigInitializer._merge_missing_keys(new_event, old_event)

    @staticmethod
    def _merge_missing_keys(new_data: dict, old_data: dict) -> dict:
        for key in new_data:
            if key not in old_data:
                old_data[key] = new_data[key]
        return old_data

    def _write_error(self, message: str) -> None:
        self.error_log.write_text(
            f"{message}\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_json(path: Path, data, *, indent: int) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")
