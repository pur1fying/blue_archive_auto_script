from functools import partial

from PyQt5.QtWidgets import QHBoxLayout, QLabel
from qfluentwidgets import ComboBox

from .expandTemplate import TemplateLayout
from PyQt5.QtCore import QObject


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        DrillConfig = QObject()
        # TODO: Add Descriptions
        configItems = [
            {
                'label': DrillConfig.tr('是否扫荡'),
                'type': 'switch',
                'key': 'drill_enable_sweep'
            }
        ]
        super().__init__(parent=parent, configItems=configItems, config=config, context="DrillConfig")
        self.config = config
        self.vBoxLayout.addSpacing(10)

        drill_detail_config = [
            {
                'label': DrillConfig.tr('出击队伍'),
                'key': 'drill_fight_formation_list',
                'selection': ['1', '2', '3', '4'],
            },
            {
                'label': DrillConfig.tr('出击关卡'),
                'key': 'drill_difficulty_list',
                'selection': ['1', '2', '3', '4']
            }
        ]
        for item in drill_detail_config:
            self.vBoxLayout.addLayout(self.create_split_selection(**item))

    def create_split_selection(self, **kwargs):
        description = kwargs['label']
        key = kwargs['key']
        selections = kwargs['selection']
        current_value = self.config.get(key)

        _layout = QHBoxLayout()
        _layout.addWidget(QLabel(description))
        _layout.addStretch(1)
        _combo_list = [ComboBox() for _ in range(len(current_value))]
        for i, combo in enumerate(_combo_list):
            combo.addItems(selections)
            combo.setCurrentText(str(current_value[i]))
            combo.currentTextChanged.connect(partial(self.on_combo_list_changed, key, _combo_list))
            _layout.addWidget(combo)
            if i != len(_combo_list) - 1:
                _layout.addWidget(QLabel('/'))
        return _layout

    def on_combo_list_changed(self, key, value):
        self.config.set(key, [int(combo.currentText()) for combo in value])
