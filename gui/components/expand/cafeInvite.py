from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from qfluentwidgets import ComboBox

from gui.util.config_set import ConfigSet


class Layout(QWidget, ConfigSet):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.student_name = ["日富美(泳装)", "真白(泳装)", "鹤城(泳装)","白子(骑行)","梓(泳装)", "爱丽丝", "切里诺", "志美子", "日富美", "佳代子",
                            "明日奈", "菲娜", "艾米", "真纪",
                            "泉奈", "明里", "芹香", "优香", "小春",
                            "花江", "纯子", "千世", "干世", "莲见", "爱理", "睦月", "野宫", "绫音", "歌原",
                            "芹娜", "小玉", "铃美", "朱莉", "好美", "千夏", "琴里",
                            "春香", "真白", "鹤城", "爱露", "晴奈", "日奈", "伊织", "星野",
                            "白子", "柚子", "花凛", "妮露", "纱绫", "静子", "花子", "风香",
                            "和香", "茜", "泉", "梓", "绿", "堇", "瞬", "桃", "椿", "晴", "响"]

        self.label = QLabel('选择你要邀请的学生：', self)
        self.input = ComboBox(self)
        self.favor_student = self.get('favorStudent')
        self.input.addItems(self.student_name)

        self.input.setText(self.favor_student)
        self.setFixedHeight(53)

        self.hBoxLayout.setContentsMargins(48, 0, 0, 0)

        self.input.currentTextChanged.connect(self.__accept)

        self.hBoxLayout.addWidget(self.label, 20, Qt.AlignLeft)
        self.hBoxLayout.addWidget(self.input, 0, Qt.AlignRight)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.setAlignment(Qt.AlignCenter)

    def __accept(self):
        self.favor_student = self.input.text()
        self.set('favorStudent', self.favor_student)
        print(self.favor_student)
