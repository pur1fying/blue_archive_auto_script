from PyQt5.QtCore import QUrl
from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit


class CreateSettingMessageBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr('新建配置'), self)
        self.pathLineEdit = LineEdit(self)

        self.pathLineEdit.setPlaceholderText(self.tr('输入新建的配置名：'))
        self.pathLineEdit.setClearButtonEnabled(True)

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.pathLineEdit)

        # change the text of button
        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.pathLineEdit.textChanged.connect(self._validateUrl)

        # self.hideYesButton()

    def _validateUrl(self, text):
        self.yesButton.setEnabled(QUrl(text).isValid())
