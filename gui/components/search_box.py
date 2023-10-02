# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCompleter

from qfluentwidgets import SearchLineEdit


class SearchBox:

    def __init__(self, parent, container):
        super().__init__()
        # self.setStyleSheet("Demo {background: rgb(32, 32, 32)}")
        # setTheme(Theme.DARK)
        self.lineEdit = SearchLineEdit(parent)

        # add completer
        stands = [
            "Star Platinum", "Hierophant Green",
            "Made in Haven", "King Crimson",
            "Silver Chariot", "Crazy diamond",
            "Metallica", "Another One Bites The Dust",
            "Heaven's Door", "Killer Queen",
            "The Grateful Dead", "Stone Free",
            "The World", "Sticky Fingers",
            "Ozone Baby", "Love Love Deluxe",
            "Hermit Purple", "Gold Experience",
            "King Nothing", "Paper Moon King",
            "Scary Monster", "Mandom",
            "20th Century Boy", "Tusk Act 4",
            "Ball Breaker", "Sex Pistols",
            "D4C • Love Train", "Born This Way",
            "SOFT & WET", "Paisley Park",
            "Wonder of U", "Walking Heart",
            "Cream Starter", "November Rain",
            "Smooth Operators", "The Matte Kudasai"
        ]
        self.completer = QCompleter(stands, self.lineEdit)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setMaxVisibleItems(10)
        self.lineEdit.setCompleter(self.completer)

        container.addWidget(self.lineEdit)

        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setPlaceholderText('Settings...')
