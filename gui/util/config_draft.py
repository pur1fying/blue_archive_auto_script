"""Dialog-scoped config draft.

Card-mode setting dialogs edit a draft first:
  - set/update only mutate memory
  - commit() writes dirty keys to the live ConfigSet
  - rollback() drops dirty keys (live was never touched)

Layout code can keep calling config.get/set as usual when the injected
object is a ConfigDraft.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from gui.util.translator import baasTranslator as bt


class ConfigDraft:
    """Proxy around ConfigSet that buffers writes until commit()."""

    __slots__ = ("_live", "_dirty")

    def __init__(self, live_config):
        if isinstance(live_config, ConfigDraft):
            live_config = live_config.live
        self._live = live_config
        self._dirty = {}

    # --- identity ---------------------------------------------------------

    @property
    def live(self):
        return self._live

    @property
    def is_draft(self) -> bool:
        return True

    def dirty_keys(self):
        return tuple(self._dirty.keys())

    def is_dirty(self) -> bool:
        return bool(self._dirty)

    # --- ConfigSet-compatible API ----------------------------------------

    def get(self, key=None, default=None, **kwargs):
        if key is None and "key" in kwargs:
            key = kwargs["key"]
        if key in self._dirty:
            value = self._dirty[key]
            # Only translate strings; lists/bools/ints must pass through untouched.
            if isinstance(value, str):
                return bt.tr("ConfigTranslation", value)
            return value
        # ConfigSet.get supports keyword form used across layouts.
        return self._live.get(key=key, default=default)

    def has(self, key) -> bool:
        if key in self._dirty:
            return True
        return self._live.has(key)

    def set(self, key, value=None, **kwargs):
        # support set(key=..., value=...) used by shop layouts
        if value is None and "value" in kwargs:
            value = kwargs["value"]
        if key is None and "key" in kwargs:
            key = kwargs["key"]
        # Store as-is. UI already bt.undo()s ComboBox display text before set
        # (see expandTemplate._commit). Calling undo here would break list values
        # like CommonShopList (TypeError: unhashable type: 'list').
        self._dirty[key] = value

    def update(self, key, value):
        self.set(key, value)

    def save(self):
        # no-op while drafting; real save happens in commit()
        return

    def __getitem__(self, item: str):
        return self.get(item)

    def __setitem__(self, key: str, value):
        self.set(key, value)

    # --- transaction ------------------------------------------------------

    def commit(self) -> int:
        """Flush dirty keys to the live ConfigSet. Returns number of keys written."""
        if not self._dirty:
            return 0
        count = 0
        # copy items so we can clear safely even if set raises mid-way
        items = list(self._dirty.items())
        self._dirty.clear()
        for key, value in items:
            self._live.set(key, value)
            count += 1
        return count

    def rollback(self) -> None:
        self._dirty.clear()

    def flush_pending_editors(self, root_widget) -> None:
        """Clear focus so LineEdit editingFinished handlers can run before commit."""
        if root_widget is None:
            return
        try:
            from PyQt5.QtWidgets import QApplication

            fw = root_widget.focusWidget() if hasattr(root_widget, "focusWidget") else None
            if fw is None:
                app = QApplication.instance()
                fw = app.focusWidget() if app else None
            if fw is not None:
                fw.clearFocus()
            app = QApplication.instance()
            if app is not None:
                app.processEvents()
        except Exception:
            pass

    # --- attribute passthrough -------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # Called only when normal attribute lookup fails.
        return getattr(self._live, name)


def as_live(config):
    """Return the underlying ConfigSet if config is a draft, else config."""
    if isinstance(config, ConfigDraft):
        return config.live
    return config


def ensure_draft(config) -> ConfigDraft:
    if isinstance(config, ConfigDraft):
        return config
    return ConfigDraft(config)
