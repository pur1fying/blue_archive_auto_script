from __future__ import annotations

from service.conf.initializer import ConfigInitializer


def check_switch_config(dir_path="./default_config"):
    ConfigInitializer().check_switch_config(_normalize_config_id(dir_path))


def check_single_event(new_event, old_event):
    return ConfigInitializer.check_single_event(new_event, old_event)


def check_event_config(dir_path="./default_config", user_config=None):
    ConfigInitializer().check_event_config(_normalize_config_id(dir_path), user_config)


def delete_deprecated_config(file_name, config_name=None):
    ConfigInitializer().delete_deprecated_config(file_name, config_name)


def check_static_config():
    ConfigInitializer().check_static_config()


def update_config_reserve_old(config_old, config_new):
    return ConfigInitializer.update_config_reserve_old(config_old, config_new)


def check_and_update_user_config(dir_path="./default_config", server=None, name=None):
    ConfigInitializer().check_and_update_user_config(_normalize_config_id(dir_path), server=server, name=name)


def check_config(dir_path, server=None, name=None):
    ConfigInitializer().check_config(_normalize_config_ids(dir_path), server=server, name=name)


def _normalize_config_id(config_id: str) -> str:
    return str(config_id).replace("./", "", 1)


def _normalize_config_ids(config_ids):
    if isinstance(config_ids, list):
        return [_normalize_config_id(item) for item in config_ids]
    return _normalize_config_id(config_ids)
