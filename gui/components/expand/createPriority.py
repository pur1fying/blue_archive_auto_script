from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QTextEdit
from qfluentwidgets import LineEdit, SwitchButton, ComboBox, TextEdit

from core.utils import delay
from gui.components.template_card import TemplateSettingCard
from gui.util import notification


class WordWrapTextEdit(TextEdit):
    """
    A QTextEdit that wraps text to fit the available width.

    The text is split into words separated by spaces. The words are then joined into lines
    until the line width exceeds the available width. The lines are then joined with '\\n'.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_text = ""
        self.word_split = ">"
        self.setLineWrapMode(QTextEdit.NoWrap)  # 禁用内置换行
        self.document().setDocumentMargin(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.font_metrics = QFontMetrics(self.font())

    def setText(self, text):
        """
        Set the text and rewrap it.
        """
        self.original_text = text
        self.rewrap_text()

    def resizeEvent(self, event):
        """
        If the component is resized, rewrap the text as well.
        """
        super().resizeEvent(event)
        self.rewrap_text()

    def rewrap_text(self):
        """
        Wrap the text to fit the available.
        """
        available_width = self.viewport().width() - 10
        if available_width <= 0:
            return
        # Split the text into a list of words separated by spaces
        words = self.original_text.split(self.word_split)
        lines = []
        current_line = ''
        for word in words:
            if current_line:
                test_line = current_line + self.word_split + word
            else:
                test_line = word
            line_width = self.font_metrics.horizontalAdvance(test_line)
            if line_width <= available_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line + '>')
                current_line = word
                # If a single word exceeds the available width, force a line break
                word_width = self.font_metrics.horizontalAdvance(word)
                if word_width > available_width:
                    lines.append(word)
                    current_line = ''
        if current_line:
            lines.append(current_line)
        # Use '\n' to join the lines
        wrapped_text = '\n'.join(lines)
        # Prevent infinite recursion
        self.blockSignals(True)
        # Keep the cursor position and scroll bar position
        cursor = self.textCursor()
        position = cursor.position()
        scroll_pos = self.verticalScrollBar().value()
        self.setPlainText(wrapped_text)
        # Restore the cursor position and scroll bar position
        cursor.setPosition(position)
        self.setTextCursor(cursor)
        self.verticalScrollBar().setValue(scroll_pos)
        self.blockSignals(False)


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
                config=self.config,
                phase=_phase
            )
            self.layout_for_line_two.addWidget(card_for_create)
            card_for_create.onToggleChangeSignal.connect(partial(__adjust_card_height, self))
            detailed_widgets.append(card_for_create)

        self.__test__(self)
        return detailed_widgets

    @delay(0.1)
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

    @delay(0.5)
    def __async_adjust(self, widget):
        widget.adjustSize()

    @delay(0.2)
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
            self.phase = phase
            self.__dict_for_phase = {
                1: self.tr('一级制造配置'),
                2: self.tr('二级制造配置'),
                3: self.tr('三级制造配置')
            }
            __dict_for_create_method = [
                {
                    'default': self.tr('默认')
                },
                {
                    'primary': self.tr('白色材料'),
                    'normal': self.tr('蓝色材料'),
                    'primary_normal': self.tr('白色+蓝色材料'),
                    'advanced': self.tr('金色材料'),
                    'superior': self.tr('紫色材料'),
                    'advanced_superior': self.tr('金色+紫色材料'),
                    'primary_normal_advanced_superior': self.tr('白色+蓝色+金色+紫色材料'),
                },
                {
                    'advanced': self.tr('金色材料'),
                    'superior': self.tr('紫色材料'),
                    'advanced_superior': self.tr('金色+紫色材料'),
                }
            ]
            __dict_for_create_method = __dict_for_create_method[phase - 1]
            __rev_dict_for_method = {v: k for k, v in __dict_for_create_method.items()}

            layout_for_line_one = QHBoxLayout()

            layout_for_create_method = QHBoxLayout()
            label_for_create_method = QLabel(self.tr('材料选择'), self)
            input_for_create_method = ComboBox(self)
            for key in __dict_for_create_method:
                input_for_create_method.addItems([__dict_for_create_method[key]])
            self.create_method = self.config.get(f'create_phase_{phase}_select_item_rule')
            input_for_create_method.setCurrentText(__dict_for_create_method[self.create_method])
            input_for_create_method.currentTextChanged.connect(
                lambda text: self.config.set(f'create_phase_{phase}_select_item_rule', __rev_dict_for_method[text]))
            layout_for_create_method.addWidget(label_for_create_method, 1, Qt.AlignLeft)
            layout_for_create_method.addWidget(input_for_create_method, 0, Qt.AlignRight)

            layout_for_line_one.addLayout(layout_for_create_method)

            self.viewLayout.addLayout(layout_for_line_one)

            if phase == 2:
                layout_for_line_extra = QHBoxLayout()

                layout_for_rc_create_priority = QHBoxLayout()
                label_for_rc_create_priority = QLabel(self.tr('一键设置推荐优先级'), self)
                input_for_rc_create_priority = ComboBox(self)
                _list = self.get_phase2_recommended_name_list()
                _list.insert(0, self.tr('选择学生'))
                input_for_rc_create_priority.addItems(_list)
                input_for_rc_create_priority.currentIndexChanged.connect(self.__change_rc_create_priority)
                layout_for_rc_create_priority.addWidget(label_for_rc_create_priority, 1, Qt.AlignLeft)
                layout_for_rc_create_priority.addWidget(input_for_rc_create_priority, 0, Qt.AlignRight)

                layout_for_line_extra.addLayout(layout_for_rc_create_priority)

                self.viewLayout.addLayout(layout_for_line_extra)

            layout_for_line_two = QHBoxLayout()

            layout_for_create_priority = QHBoxLayout()
            label_for_create_priority = QLabel(self.tr('制造优先级'), self)
            layout_for_create_priority.addWidget(label_for_create_priority, 1, Qt.AlignLeft)

            layout_for_line_two.addLayout(layout_for_create_priority)

            self.viewLayout.addLayout(layout_for_line_two)

            layout_for_line_three = QHBoxLayout()

            layout_for_create_priority_list = QVBoxLayout()
            self.create_priority = self.get_create_priority(phase)
            self.input_for_create_priority = WordWrapTextEdit(self)
            self.input_for_create_priority.setFixedHeight(125)
            _content = ' > '.join(self.create_priority)
            self.input_for_create_priority.setText(_content)
            self.input_for_create_priority.textChanged.connect(
                partial(self.__change_create_priority, self.input_for_create_priority.toPlainText))
            layout_for_create_priority_list.addWidget(self.input_for_create_priority)

            layout_for_line_three.addLayout(layout_for_create_priority_list)

            self.viewLayout.addLayout(layout_for_line_three)

            self.setLayout(self.viewLayout)

        @delay(1)
        def __change_create_priority(self, text):
            self.create_priority = text().split('>')
            self.create_priority = [i.strip() for i in self.create_priority]
            self.config.set(f'createPriority_phase{self.phase}', self.create_priority)
            notification.success(self.tr('制造优先级'),
                                 self.__dict_for_phase[self.phase] + self.tr("修改成功"),
                                 self.config)

        def get_create_priority(self, phase):
            cfg_key_name = 'createPriority_phase' + str(phase)
            return self.config.get(cfg_key_name)

        def __change_rc_create_priority(self, idx):
            if idx == 0:
                return
            _priority = self.get_phase2_recommended_priority(idx-1)
            self.config.set('createPriority_phase2', _priority)
            self.input_for_create_priority.setText(' > '.join(_priority))
            notification.success(self.tr('推荐制造优先级'),
                                 self.tr('修改成功'),
                                 self.config)

        def get_phase2_recommended_name_list(self):
            return list(self.config.static_config.create_phase2_recommended_priority.keys())

        def get_phase2_recommended_priority(self, idx):
            name = self.get_phase2_recommended_name_list()[idx]
            indexes = self.config.static_config.create_phase2_recommended_priority[name]
            origin_priority = self.config.static_config.create_default_priority[self.config.server_mode]["phase2"]
            res_priority = indexes.copy()
            for i in range(0, len(res_priority)):
                res_priority[i] = origin_priority[res_priority[i]]
            for i in range(0, len(origin_priority)):
                if i not in indexes:
                    res_priority.append(origin_priority[i])
            return res_priority
