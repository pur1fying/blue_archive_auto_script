import threading
import time
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import LineEdit, SwitchButton, ComboBox, TextEdit

from core.utils import delay
from gui.components.template_card import TemplateSettingCard

stored_height_local = 0
stored_height_local_ = -1


class Layout(QWidget):
    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.config = config
        self.initiated = False
        self._init_layout()

    def _init_layout(self):
        self.viewLayout = QVBoxLayout(self)
        layout_for_line_one = QHBoxLayout()
        layout_for_acc_ticket = QHBoxLayout()
        label_for_use_acc_ticket_check_box = QLabel(self.tr('是否使用加速券'), self)
        use_acc_ticket_switch = SwitchButton(self)
        use_acc_ticket_switch.setChecked(self.config.get('use_acceleration_ticket'))
        use_acc_ticket_switch.checkedChanged.connect(
            lambda checked: self.config.set('use_acceleration_ticket', checked))
        layout_for_acc_ticket.addWidget(label_for_use_acc_ticket_check_box, 1, Qt.AlignLeft)
        layout_for_acc_ticket.addWidget(use_acc_ticket_switch, 0, Qt.AlignRight)
        layout_for_line_one.addLayout(layout_for_acc_ticket)
        layout_for_line_one.addSpacing(30)
        layout_for_count = QHBoxLayout()
        label_for_count = QLabel(self.tr('制造次数'), self)
        input_for_count = LineEdit(self)
        input_for_count.setFixedWidth(50)
        time = self.config.get('createTime')
        input_for_count.setText(time)
        input_for_count.editingFinished.connect(
            lambda: self.config.set('createTime', input_for_count.text()))
        layout_for_count.addWidget(label_for_count, 1, Qt.AlignLeft)
        layout_for_count.addWidget(input_for_count, 0, Qt.AlignRight)
        layout_for_line_one.addLayout(layout_for_count)
        layout_for_line_one.addSpacing(30)
        layout_for_layer_count = QHBoxLayout()
        label_for_layer_count = QLabel(self.tr('制造级数'), self)
        input_for_layer_count = ComboBox(self)
        input_for_layer_count.addItems(['1', '2', '3'])
        self.phases = self.config.get('create_phase')
        input_for_layer_count.setCurrentText(str(self.phases))
        input_for_layer_count.currentTextChanged.connect(self.__change_create_phase)
        layout_for_layer_count.addWidget(label_for_layer_count, 1, Qt.AlignLeft)
        layout_for_layer_count.addWidget(input_for_layer_count, 0, Qt.AlignRight)
        layout_for_line_one.addLayout(layout_for_layer_count)
        self.viewLayout.addLayout(layout_for_line_one)
        self.layout_for_line_two = QVBoxLayout()
        self.detailed_widgets = self._init_detailed_config()
        global stored_height_local_
        stored_height_local_ = self.layout_for_line_two.sizeHint().height()
        self.viewLayout.addLayout(self.layout_for_line_two)
        self.viewLayout.setAlignment(Qt.AlignCenter)
        self.viewLayout.setContentsMargins(20, 10, 20, 10)
        self.__async_post_init_process()

    def _init_detailed_config(self):
        detailed_widgets = []

        __dict_for_phase = {
            1: self.tr('一级制造配置'),
            2: self.tr('二级制造配置'),
            3: self.tr('三级制造配置')
        }
        self.box_changed = False

        def __adjust_card_height(ref_widget):
            top_card_widget = self.__adjust_raw(ref_widget)
            if top_card_widget: top_card_widget.adjustSize()

        for _phase in range(1, self.phases + 1):
            card_for_create = TemplateSettingCard(
                title=f"{_phase}. {__dict_for_phase[_phase]}",
                content=self.tr("显示并配置") + __dict_for_phase[_phase],
                parent=self,
                sub_view=self,
                config=self.config
            )
            self.layout_for_line_two.addWidget(card_for_create)
            card_for_create.onToggleChangeSignal.connect(partial(__adjust_card_height, self))
            detailed_widgets.append(card_for_create)

        self.__test__(self)
        return detailed_widgets

    @delay(0.05)
    def __test__(self, ref_widget):
        if not self.initiated: return
        self.__adjust_raw(ref_widget)

    def __adjust_raw(self, ref_widget):
        while not isinstance(ref_widget, TemplateSettingCard):
            if ref_widget is None: return
            ref_widget = ref_widget.parent()
        top_card_widget = ref_widget
        global stored_height_local
        delta = self.height() - stored_height_local
        stored_height_local = self.height()
        assert isinstance(top_card_widget, TemplateSettingCard)
        top_card_widget.setFixedHeight(top_card_widget.height() + delta)
        return top_card_widget

    @delay(0.3)
    def __async_adjust(self, widget):
        widget.adjustSize()

    @delay(0.01)
    def __async_post_init_process(self):
        global stored_height_local
        stored_height_local = self.height()

    def __change_create_phase(self, text):
        self.config.set('create_phase', int(text))
        self.phases = int(text)
        for widget in self.detailed_widgets:
            self.layout_for_line_two.removeWidget(widget)
            widget.deleteLater()
            del widget
        self.detailed_widgets = self._init_detailed_config()
        # self.__async_post_init_process()
        self.initiated = True

    class Layout(QWidget):
        def __init__(self, parent=None, config=None, phase=1):
            super().__init__(parent=parent)
            self.viewLayout = QVBoxLayout(self)
            self.config = config

            __dict_for_method = {
                'default': self.tr('默认')
            }
            __rev_dict_for_method = {v: k for k, v in __dict_for_method.items()}

            layout_for_line_one = QHBoxLayout()

            layout_for_create_method = QHBoxLayout()
            label_for_create_method = QLabel(self.tr('制造方式'), self)
            input_for_create_method = ComboBox(self)
            input_for_create_method.addItems([self.tr('默认')])
            self.create_method = self.config.get(f'create_phase_{phase}_select_item_rule')
            input_for_create_method.setCurrentText(__dict_for_method[self.create_method])
            input_for_create_method.currentTextChanged.connect(
                lambda text: self.config.set('create_method', __rev_dict_for_method[text]))
            layout_for_create_method.addWidget(label_for_create_method, 1, Qt.AlignLeft)
            layout_for_create_method.addWidget(input_for_create_method, 0, Qt.AlignRight)

            layout_for_line_one.addLayout(layout_for_create_method)

            self.viewLayout.addLayout(layout_for_line_one)

            layout_for_line_two = QHBoxLayout()

            layout_for_create_priority = QHBoxLayout()
            label_for_create_priority = QLabel(self.tr('制造优先级'), self)
            layout_for_create_priority.addWidget(label_for_create_priority, 1, Qt.AlignLeft)

            layout_for_line_two.addLayout(layout_for_create_priority)

            self.viewLayout.addLayout(layout_for_line_two)

            layout_for_line_three = QHBoxLayout()

            layout_for_create_priority_list = QVBoxLayout()
            self.create_priority = self.get_create_priority(phase)
            input_for_create_priority = TextEdit(self)
            input_for_create_priority.setFixedHeight(125)
            input_for_create_priority.setText(' > '.join(self.create_priority))
            input_for_create_priority.textChanged.connect(self.__change_create_priority)
            layout_for_create_priority_list.addWidget(input_for_create_priority)

            layout_for_line_three.addLayout(layout_for_create_priority_list)

            self.viewLayout.addLayout(layout_for_line_three)

            self.setLayout(self.viewLayout)

        def __change_create_priority(self, text):
            self.create_priority = text.split('>')
            self.create_priority = [i.strip() for i in self.create_priority]
            self.config.set(f'createPriority_phase{self.phase}', self.create_priority)

        def get_create_priority(self, phase):
            cfg_key_name = 'createPriority_phase' + str(phase)
            default_priority = self.config.static_config['create_default_priority'][self.config.server_mode][
                "phase" + str(phase)]
            current_priority = self.config.get(cfg_key_name)
            res = []
            for i in range(0, len(current_priority)):
                if current_priority[i] in default_priority:
                    res.append(current_priority[i])
            for j in range(0, len(default_priority)):
                if default_priority[j] not in res:
                    res.append(default_priority[j])
            self.config.set(cfg_key_name, res)
            return res

