from functools import partial
from typing import Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import ComboBox, SwitchButton, PushButton, LineEdit

from gui.util import notification


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
        self.config.update(key, value)
        notification.success('设置成功', f'{labelTarget.text()}已经被设置为：{value}', self.config)


class ConfigItemV2(ConfigItem):
    label: str
    key: str
    dataType: str

    def __init__(self, **kwargs):
        self.label = kwargs.get('label')
        self.key = kwargs.get('key')
        self.dataType = kwargs.get('dataType', 'str')


class ComboBoxCustom(ComboBox):
    def __init__(self, parent=None, inputComponent: LineEdit = None, key: str = None, config=None):
        super().__init__(parent=parent)
        self.inputComponent = inputComponent
        self.config = config
        self.key = key
        self.items = []

    def _onItemClicked(self, index):
        print(self.items[index].text)
        if self.inputComponent:
            value = eval(self.inputComponent.text())
            value.append(self.items[index].text)
            self.inputComponent.setText(str(value))
            self.config[self.key] = value


class TemplateLayoutV2(QWidget):
    def __init__(self, configItems: list[dict], parent=None, config=None, all_label_list: list = None):
        super().__init__(parent=parent)

        _all_label_list = []
        for label in all_label_list:
            if config['event_name'] == label[0]:
                continue
            _all_label_list.append(label)
        all_label_list = _all_label_list
        del _all_label_list

        self.config = config
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(400)
        self.setStyleSheet('''
            QLabel {
                font-size: 16px;
                font-family: "Microsoft YaHei";
            }
        ''')

        self.cfs = []

        for ind, cfg in enumerate(configItems):
            optionPanel = QHBoxLayout(self)
            cfg = ConfigItemV2(**cfg)
            self.cfs.append(cfg)
            labelComponent = QLabel(cfg.label, self)
            optionPanel.addWidget(labelComponent, 0, Qt.AlignLeft)
            optionPanel.addStretch(1)
            currentKey = cfg.key
            inputComponent = LineEdit(self)
            inputComponent.setMinimumWidth(200)
            inputComponent.setText(str(self.config.get(currentKey)))
            inputComponent.textChanged.connect(partial(self._commit, currentKey, inputComponent))
            optionPanel.addWidget(inputComponent, 0, Qt.AlignRight)
            if currentKey == 'pre_task' or currentKey == 'post_task':
                comboTip = ComboBoxCustom(self, inputComponent, currentKey, self.config)
                comboTip.addItems([x[0] for x in all_label_list])
                optionPanel.addWidget(comboTip, 0, Qt.AlignRight)
            self.vBoxLayout.addLayout(optionPanel)
            self.vBoxLayout.addSpacing(8)
            self.vBoxLayout.setContentsMargins(20, 0, 20, 20)

    def _commit(self, key, target):
        value = target.text()
        for cf in self.cfs:
            if cf.key == key:
                if cf.dataType == 'int' or cf.dataType == 'list':
                    value = eval(value)
                else:
                    value = value
        self.config[key] = value
