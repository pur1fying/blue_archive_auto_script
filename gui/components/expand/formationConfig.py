from PyQt5.QtWidgets import QVBoxLayout, QWidget

from gui.components.template_card import BAASSettingCard
from gui.util.customed_ui import LineWidget, TableManager


class Layout(QWidget):
    PROPERTY: dict[str, str]
    NAME: dict[str, str]

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.PROPERTY = {
            "burst": self.tr('爆发'),
            "pierce": self.tr('贯穿'),
            "mystic": self.tr('神秘'),
            "shock": self.tr('振动'),
            "Unused": self.tr('未使用')
        }
        # Reverse the dictionary
        self.NAME = {v: k for k, v in self.PROPERTY.items()}
        self.COL_NUM_DICT = {
            "preset_team_attribute": 4,
            "side_team_attribute": 4
        }
        # Mode
        self.MODE_DICT = {
            "preset": self.tr('按预设编队'),
            "side": self.tr('按侧栏属性编队'),
            "order": self.tr('按侧栏顺序编队'),
        }

        self.items_k = [x for x in self.MODE_DICT.keys()]
        self.items_v = [x for x in self.MODE_DICT.values()]

        self.config = config
        self.table = None
        self._init_ui()

    def _init_ui(self):
        self.__async_post_init_process()
        self.choose_team_method = self.config.get('choose_team_method')
        assert self.choose_team_method in self.items_k, "Invalid choose_team_method"
        self.vBoxLayout = QVBoxLayout(self)

        mode_changer = LineWidget.get_combo_box(
            label=self.tr('编队选择方式'),
            items=self.items_v,
            current_index=self.items_k.index(self.choose_team_method),
            callback=self._change_choose_team_method,
            parent=self
        )
        self.vBoxLayout.addLayout(mode_changer)

        self._recreate_table(self.choose_team_method + "_team_attribute")
        if not self.choose_team_method == "order":
            self.vBoxLayout.addWidget(self.table)

        self.setLayout(self.vBoxLayout)

        # Though it's meaningless, the visual effect is better
        if self.choose_team_method == "side":
            self._recreate_table("preset_team_attribute")
            self._recreate_table("side_team_attribute")

    def _change_choose_team_method(self, index):
        self.choose_team_method = self.items_k[index]
        self.config.set('choose_team_method', self.choose_team_method)
        self._recreate_table(self.choose_team_method + "_team_attribute")

    def _recreate_table(self, key):

        if key == "order_team_attribute":
            if self.table:
                self.setFixedHeight(60)
                self.table.hide()
                self.__adjust_raw(self)
            return

        self.setFixedHeight(300)

        unit_config = {
            "type": "comboBox",
            "items": list(self.PROPERTY.values()),
        }
        col_length = self.COL_NUM_DICT[key]

        headers: dict = {"row_headers": [str(x + 1) for x in range(4)]} \
            if key == "preset_team_attribute" else \
            {"col_headers": [str(x + 1) for x in range(4)]}
        headers["height"] = 230
        transpose = True

        if not self.table:
            self.table = TableManager(
                parent=self,
                config=self.config,
                data_key=key,
                col_length=col_length,
                unit_config=unit_config,
                convert_dict=self.PROPERTY,
                transpose=transpose,
                **headers
            )
        else:
            self.table.reset_table(
                data_key=key,
                col_length=col_length,
                unit_config=unit_config,
                transpose=transpose,
                **headers
            )

        if self.vBoxLayout.count() == 1:
            self.vBoxLayout.addWidget(self.table)
        self.table.show()
        self.__adjust_raw(self)

    def __async_post_init_process(self):
        global stored_height_local
        stored_height_local = self.height()

    def __adjust_raw(self, ref_widget):
        while not isinstance(ref_widget, BAASSettingCard):
            if ref_widget is None: return
            ref_widget = ref_widget.parent()
        top_card_widget = ref_widget
        global stored_height_local
        delta = self.height() - stored_height_local
        stored_height_local = self.height()
        assert isinstance(top_card_widget, BAASSettingCard)
        top_card_widget.setFixedHeight(top_card_widget.height() + delta)
        return top_card_widget
