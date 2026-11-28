from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from qfluentwidgets import CheckBox, FluentIcon, MessageBoxBase, PushSettingCard, SubtitleLabel

from gui.util.legacy_migration import suppress_legacy_notice


_SITE = QUrl("https://baas.kiramei.moe")
_TEXT = {
    "zh": ("🎉 现已推出新版 UI，邀您测试使用！ ✨", "前往了解", "我已了解", "下次不再展示"),
    "en": ("🎉 The new BAAS UI is here. Give it a try! ✨", "Learn more", "Got it", "Don't show again"),
    "ja": ("🎉 新しい BAAS UI が登場しました。ぜひお試しください！ ✨", "詳しく見る", "了解しました", "次回から表示しない"),
    "ko": ("🎉 새로운 BAAS UI가 출시되었어요. 사용해 보세요! ✨", "자세히 보기", "확인", "다시 표시하지 않기"),
}


def show_legacy_ui_notice(parent, language):
    title, learn, acknowledge, hide = _TEXT.get(language, _TEXT["en"])
    dialog = MessageBoxBase(parent)
    dialog.viewLayout.addWidget(SubtitleLabel(title, dialog))
    checkbox = CheckBox(hide, dialog)
    dialog.viewLayout.addWidget(checkbox)
    dialog.yesButton.setText(acknowledge)
    dialog.cancelButton.setText(learn)
    dialog.buttonLayout.removeWidget(dialog.cancelButton)
    dialog.buttonLayout.insertWidget(0, dialog.cancelButton, 1)
    dialog.cancelButton.clicked.disconnect()
    dialog.cancelButton.clicked.connect(lambda: QDesktopServices.openUrl(_SITE))
    dialog.exec_()
    if checkbox.isChecked():
        suppress_legacy_notice()


def legacy_ui_notice_card(parent, language):
    title, learn, _, _ = _TEXT.get(language, _TEXT["en"])
    card = PushSettingCard(f"{learn}  →", FluentIcon.INFO, title, parent=parent)
    card.clicked.connect(lambda: QDesktopServices.openUrl(_SITE))
    return card
