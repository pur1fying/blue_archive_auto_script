from typing import Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import ComboBox, SwitchButton, PushButton, LineEdit, InfoBar, InfoBarIcon, InfoBarPosition

from functools import partial


class ConfigItem:
    label: str
    key: Union[str, None]
    selection: Union[list[str], bool, str, list[int], callable, None]
    type: str

    def __init__(self, **kwargs):
        self.label = kwargs.get('label')
        self.key = kwargs.get('key')
        self.selection = kwargs.get('selection')
        self.type = kwargs.get('type')


class TemplateLayout(QWidget):
    patch_signal = pyqtSignal(str)

    def __init__(self, configItems: Union[list[ConfigItem], list[dict]], parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        if isinstance(configItems[0], dict):
            _configItems = []
            for item in configItems:
                assert isinstance(item, dict)
                _configItems.append(ConfigItem(**item))
            configItems = _configItems

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)

        for ind, cfg in enumerate(configItems):
            confirmButton = None
            optionPanel = QHBoxLayout(self)
            labelComponent = QLabel(cfg.label, self)
            optionPanel.addWidget(labelComponent, 0, Qt.AlignLeft)
            optionPanel.addStretch(1)
            if cfg.type == 'switch':
                currentKey = cfg.key
                inputComponent = SwitchButton(self)
                inputComponent.setChecked(self.config.get(currentKey))
                inputComponent.checkedChanged.connect(partial(self._commit, currentKey, inputComponent, labelComponent))
            elif cfg.type == 'combo':
                currentKey = cfg.key
                inputComponent = ComboBox(self)
                inputComponent.addItems(cfg.selection)
                inputComponent.setCurrentIndex(cfg.selection.index(self.config.get(currentKey)))
                inputComponent.currentIndexChanged.connect(
                    partial(self._commit, currentKey, inputComponent, labelComponent))
            elif cfg.type == 'button':
                inputComponent = PushButton('执行', self)
                inputComponent.clicked.connect(cfg.selection)
            elif cfg.type == 'text':
                currentKey = cfg.key
                inputComponent = LineEdit(self)
                inputComponent.setText(str(self.config.get(currentKey)))
                self.patch_signal.connect(inputComponent.setText)
                confirmButton = PushButton('确定', self)
                confirmButton.clicked.connect(partial(self._commit, currentKey, inputComponent, labelComponent))
            elif cfg.type == 'label':
                inputComponent = QLabel(cfg.selection, self)
            else:
                raise ValueError(f'Unknown config type: {cfg.type}')
            optionPanel.addWidget(inputComponent, 0, Qt.AlignRight)
            if confirmButton is not None:
                optionPanel.addWidget(confirmButton, 0, Qt.AlignRight)
            self.vBoxLayout.addLayout(optionPanel)
            self.vBoxLayout.setContentsMargins(20, 0, 20, 20)

    def _commit(self, key, target, labelTarget):
        value = None
        if isinstance(target, ComboBox):
            value = target.currentText()
        elif isinstance(target, SwitchButton):
            value = target.isChecked()
        elif isinstance(target, LineEdit):
            value = target.text()
        assert value is not None
        self.config.set(key, value)
        infoChanged = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title='设置成功',
            content=f'{labelTarget.text()}已经被设置为：{value}',
            orient=Qt.Vertical,
            position=InfoBarPosition.TOP_RIGHT,
            duration=800,
            parent=self.parent().parent().parent().parent().parent()
            .parent().parent().parent().parent().parent()
        )
        infoChanged.show()
