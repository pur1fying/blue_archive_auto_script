from __future__ import annotations

import sys
import types


def pytest_configure():
    if "gui.util.translator" not in sys.modules:
        translator = types.ModuleType("gui.util.translator")

        class _Translator:
            @staticmethod
            def tr(_domain, value):
                return value

            @staticmethod
            def undo(value):
                return value

        translator.baasTranslator = _Translator()
        sys.modules["gui.util.translator"] = translator

    if "gui.util.customized_ui" not in sys.modules:
        customized_ui = types.ModuleType("gui.util.customized_ui")

        class BoundComponent:
            def __init__(self, component, string_rule, config_set, attribute="setText"):
                self.component = component
                self.string_rule = string_rule
                self.config_set = config_set
                self.attribute = attribute

            def config_updated(self, _key):
                return None

        customized_ui.BoundComponent = BoundComponent
        sys.modules["gui.util.customized_ui"] = customized_ui
