from functools import partial

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QLabel, QHBoxLayout
from qfluentwidgets import LineEdit, PushButton, ComboBox

from .expandTemplate import TemplateLayout
from gui.util import notification
from gui.util.translator import baasTranslator as bt


class Layout(TemplateLayout):
    def __init__(self, parent=None, config=None):
        EmulatorConfig = QObject()
        configItems = [
            {
                'label': EmulatorConfig.tr('在启动Baas时打开模拟器'),
                'key': 'open_emulator_stat',
                'type': 'switch'
            },
            {
                'label': EmulatorConfig.tr('等待模拟器启动时间(秒)'),
                'type': 'text',
                'key': 'emulator_wait_time'
            },
            {
                'label': EmulatorConfig.tr('是否多开'),
                'type': 'switch',
                'key': 'emulatorIsMultiInstance'
            }
        ]

        super().__init__(parent=parent, configItems=configItems, config=config, context='EmulatorConfig')
        if not self.config.get('emulatorIsMultiInstance'):
            self._createNotMultiComponent()
        else:
            self._createMultiComponent()
        self.vBoxLayout.children()[2].itemAt(2).widget().checkedChanged.connect(self._soltForEmulatorIsMultiInstanced)

    def _choose_file(self, line_edit):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Executable files (*.exe);;Link files (*.lnk)")
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        if file_dialog.exec_():
            file_names = file_dialog.selectedFiles()
            if file_names:
                file_path = file_names[0]
                line_edit.setText(file_path)
                self.config.set('program_address', file_path)

    def _createNotMultiComponent(self):
        labelComponent = QLabel(self.tr('选择模拟器地址'), self)
        addressKey = 'program_address'
        inputComponent = LineEdit(self)
        inputComponent.setFixedWidth(500)  # 设置文本框的固定宽度
        inputComponent.setText(str(self.config.get(addressKey)))
        confirmButton = PushButton(self.tr('确定'), self)
        confirmButton.setFixedWidth(80)  # 设置确定按钮的固定宽度
        confirmButton.clicked.connect(partial(self._commit, addressKey, inputComponent, labelComponent))
        selectButton = PushButton(self.tr('选择'), self)
        selectButton.setFixedWidth(80)  # 设置选择按钮的固定宽度
        selectButton.clicked.connect(partial(self._choose_file, inputComponent))
        self.emulatorNotMultiAddressHLayout = QHBoxLayout()
        self.emulatorNotMultiAddressHLayout.addWidget(labelComponent)
        self.emulatorNotMultiAddressHLayout.addWidget(inputComponent)
        self.emulatorNotMultiAddressHLayout.addWidget(selectButton)
        self.emulatorNotMultiAddressHLayout.addWidget(confirmButton)
        self.vBoxLayout.addLayout(self.emulatorNotMultiAddressHLayout)

    def _createMultiComponent(self):
        self.multiMap = {
            'mumu': 'MuMu模拟器',
            'mumu_global': 'MuMu模拟器全球版',
            'bluestacks_nxt_cn': '蓝叠模拟器',
            'bluestacks_nxt': '蓝叠国际版'
        }
        emulatorLabelComponent = QLabel(self.tr('选择模拟器类型'), self)
        multiInstanceNumber = QLabel(self.tr('多开号'), self)
        currentInstanceNumber = self.config.get('emulatorMultiInstanceNumber')
        multiInstanceNumberInputComponent = LineEdit(self)
        multiInstanceNumberInputComponent.setText(str(currentInstanceNumber))
        multiInstanceNumberInputComponent.textChanged.connect(self._slotForMultiInstanceNumberChanged)
        currentMultiEmulatorName = self.config.get('multiEmulatorName')
        chooseMultiEmulatorCombobox = ComboBox(self)
        values = self.multiMap.keys()
        chooseMultiEmulatorCombobox.addItems([bt.tr('ConfigTranslation', self.multiMap[key]) for key in values])
        chooseMultiEmulatorCombobox.setCurrentIndex(list(values).index(currentMultiEmulatorName))
        chooseMultiEmulatorCombobox.currentIndexChanged.connect(self._slotForMultiInstanceComboBoxIndexChanged)
        multiInstanceNumberInputComponent.setFixedWidth(80)
        self.emulatorMultiHLayout = QHBoxLayout(self)
        self.emulatorMultiHLayout.addWidget(emulatorLabelComponent)
        self.emulatorMultiHLayout.addWidget(chooseMultiEmulatorCombobox)
        self.emulatorMultiHLayout.addWidget(multiInstanceNumber)
        self.emulatorMultiHLayout.addWidget(multiInstanceNumberInputComponent)
        self.vBoxLayout.addLayout(self.emulatorMultiHLayout)

    def _slotForMultiInstanceNumberChanged(self):
        self.config.set('emulatorMultiInstanceNumber', self.sender().text())


    def _soltForEmulatorIsMultiInstanced(self, state):
        sub_layout = self.vBoxLayout.children()[3]
        while sub_layout.count():
            item = sub_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout.removeItem(item)
        self.vBoxLayout.removeItem(sub_layout)
        if state:
            self._createMultiComponent()
        else:
            self._createNotMultiComponent()

    def _slotForMultiInstanceComboBoxIndexChanged(self):
        self.config.set('multiEmulatorName', list(self.multiMap.keys())[self.sender().currentIndex()])
