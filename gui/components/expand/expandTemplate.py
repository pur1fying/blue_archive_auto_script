from typing import Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QGridLayout
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
            selectButton = None
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
            elif cfg.type == 'text_and_file_button':  # 新添加的配置类型
                # currentKey = cfg.key
                # inputComponentLayout = QHBoxLayout()
                # inputComponent = LineEdit(self)
                # inputComponent.setText(str(self.config[currentKey]))
                # inputComponentLayout.addWidget(inputComponent)
                # self.patch_signal.connect(inputComponent.setText)
                # fileButton = PushButton('选择', self)
                # fileButton.clicked.connect(partial(self._choose_file, inputComponent))
                # inputComponentLayout.addWidget(fileButton)
                # confirmButton = PushButton('确定', self)
                # confirmButton.clicked.connect(partial(self._commit, currentKey, inputComponent, labelComponent))
                # inputComponentLayout.addWidget(confirmButton)
                # self.vBoxLayout.addLayout(inputComponentLayout)
                currentKey = cfg.key
                inputComponent = LineEdit(self)
                inputComponent.setFixedWidth(500)  # 设置文本框的固定宽度
                inputComponent.setText(str(self.config.get(currentKey)))
                confirmButton = PushButton('确定', self)
                confirmButton.setFixedWidth(80)  # 设置确定按钮的固定宽度
                confirmButton.clicked.connect(partial(self._commit, currentKey, inputComponent, labelComponent))
                selectButton = PushButton('选择', self)
                selectButton.setFixedWidth(80)  # 设置选择按钮的固定宽度
                selectButton.clicked.connect(partial(self._choose_file, inputComponent))
                h_layout = QHBoxLayout()
                self.setLayout(h_layout)
                h_layout.addWidget(inputComponent)
                h_layout.addWidget(confirmButton)
                # 将选择按钮插入到确定按钮之前
                h_layout.insertWidget(3, selectButton)
            else:
                raise ValueError(f'Unknown config type: {cfg.type}')
            optionPanel.addWidget(inputComponent, 0, Qt.AlignRight)
            if selectButton is not None:
                optionPanel.addWidget(selectButton, 0, Qt.AlignRight)
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
