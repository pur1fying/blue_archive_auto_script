from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QHeaderView
from qfluentwidgets import LineEdit, TableWidget, PushButton

from gui.util import notification


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.vBoxLayout = QVBoxLayout(self)
        self.to_add_lay = QHBoxLayout()
        self.to_add_label = QLabel(self.tr('输入你需要添加进白名单的好友码:'), self)
        self.to_add_input = LineEdit(self)
        self.add_accept = PushButton(self.tr('确定'), self)
        self.table_view = None

        self.to_add = ""
        self.white_list = self.config.get("clear_friend_white_list")

        self.vBoxLayout.setContentsMargins(24, 0, 24, 0)

        self.add_accept.clicked.connect(self.__accept_add)

        self.to_add_lay.addWidget(self.to_add_label, 20, Qt.AlignLeft)
        self.to_add_lay.addWidget(self.to_add_input, 0, Qt.AlignRight)
        self.to_add_lay.addWidget(self.add_accept, 0, Qt.AlignCenter)

        self.vBoxLayout.setContentsMargins(24, 0, 24, 0)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)

        self.vBoxLayout.addLayout(self.to_add_lay)

        self._init_table()

    def __accept_add(self):
        self.to_add = self.to_add_input.text()
        # Check the user code is valid
        # User code length is 7 in CN server, 8 in JP and Global server
        # The user code is a string, which only contains numbers and lower case letters
        if self.config.server_mode == "CN":
            expected_len = 7
        elif self.config.server_mode == "JP":
            expected_len = 8
        elif self.config.server_mode == "Global":
            expected_len = 8
        else:
            raise ValueError("Invalid server mode [ " + self.config.server_mode + " ]")
        if len(self.to_add) != expected_len:
            notification.error(self.tr('添加失败'), self.tr('用户码长度不符合要求'), self.config)
            return
        if self.config.server_mode == "CN":
            for i in self.to_add:
                if not i.isdigit() and not i.islower():
                    notification.error(self.tr('添加失败'), self.tr('用户码格式不符合要求'), self.config)
                    return
        elif self.config.server_mode == "Global":
            for i in self.to_add:
                if not i.isupper():
                    notification.error(self.tr('添加失败'), self.tr('用户码格式不符合要求'), self.config)
                    return
        # Check the user code is in the white list
        if self.to_add in self.white_list:
            notification.error(self.tr('添加失败'), self.tr('用户码已在白名单中'), self.config)
            return
        self.white_list.append(self.to_add)
        self.config.set('clear_friend_white_list', self.white_list)
        self._init_table()
        notification.success(self.tr('添加成功'), f'{self.tr("您添加的用户为：")}{self.to_add}', self.config)

    def _init_table(self):
        # If the old table exists, delete the old table

        if self.table_view is not None:
            self.table_view.deleteLater()
            self.vBoxLayout.removeItem(self.vBoxLayout.itemAt(3))

        tableView = TableWidget(self)
        tableView.setColumnCount(2)
        tableView.setRowCount(len(self.white_list))
        tableView.setHorizontalHeaderLabels([self.tr('用户码'), self.tr('操作')])
        tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tableView.setEditTriggers(tableView.NoEditTriggers)
        for i in range(len(self.white_list)):
            user_code = QLabel(self.white_list[i], self)
            del_button = PushButton(self.tr('删除'), self)
            del_button.clicked.connect(partial(self.__accept_delete, (i,)))
            tableView.setCellWidget(i, 0, user_code)
            tableView.setCellWidget(i, 1, del_button)

        tableView.setFixedHeight(200)

        self.vBoxLayout.addWidget(tableView)
        self.vBoxLayout.setContentsMargins(24, 0, 24, 0)
        self.vBoxLayout.addSpacing(16)

        self.table_view = tableView

    def __accept_delete(self, item_index):
        for i in range(len(self.white_list)):
            if i == item_index[0]:
                self.white_list.pop(i)
                break
        self.config.set('clear_friend_white_list', self.white_list)
        self._init_table()
