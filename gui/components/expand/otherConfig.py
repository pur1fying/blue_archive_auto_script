from typing import Callable

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import PushButton

from .expandTemplate import TemplateLayout
from ...util.hotkey_manager import HotkeyInputDialog, GlobalHotkeyManager

_Callback = Callable[[], None]

class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        OtherConfig = QObject()
        configItems = [
            {
                'label': OtherConfig.tr('一键反和谐'),
                'type': 'button',
                'selection': self.fhx,
                'key': None
            },
            {
                'label': OtherConfig.tr('显示首页头图（下次启动时生效）'),
                'type': 'switch',
                'key': 'bannerVisibility'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config, context="OtherConfig")
        self.config = config
        # HOTKEY SECTION
        self.hotkey_widgets = {}
        self.manager = config.get_hotkey_manager()

        ht_k ="hotkey_run"
        self._add_setting_row(
            key=ht_k,
            description=OtherConfig.tr("启停快捷键"),
            default_hotkey=config.get(ht_k, "Ctrl+Shift+R"),
            callback=config.callbacks.get(ht_k, lambda : None)
        )

    def fhx(self):
        self.config.get_main_thread().start_fhx()

    def _add_setting_row(self, key: str, description: str, default_hotkey: str, callback: _Callback):
        """Helper function to create and register a hotkey setting row."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        desc_label = QLabel(description)
        hotkey_label = QLabel(f"<b>{default_hotkey}</b>")
        change_button = PushButton(text="Change")

        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(hotkey_label)
        layout.addWidget(change_button)

        self.vBoxLayout.addWidget(container)

        # Store widgets for later access
        self.hotkey_widgets[key] = {
            "hotkey_label": hotkey_label,
            "callback": callback
        }

        # Connect the button's click signal to the generic change handler
        change_button.clicked.connect(lambda _, k=key: self._change_hotkey(k))

        # Register the default hotkey with the manager
        # self.manager.register(default_hotkey, callback)
        #
        # self.manager.start()

    def _change_hotkey(self, key: str):
        """Handles the logic for changing a hotkey via the dialog."""
        widgets = self.hotkey_widgets[key]
        current_hotkey_str = widgets["hotkey_label"].text().replace("<b>", "").replace("</b>", "")

        new_hotkey, ok = HotkeyInputDialog.get_hotkey(self.config.get_window(),
                                                      current_hotkey_str, self.manager)

        if ok and new_hotkey != current_hotkey_str:
            widgets["hotkey_label"].setText(f"<b>{new_hotkey}</b>")
            self.config.set(key, new_hotkey)
