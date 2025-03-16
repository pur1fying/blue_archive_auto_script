from PyQt5.QtWidgets import QVBoxLayout, QWidget

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
        self.config = config
        self.table = None
        self._init_ui()

    def _init_ui(self):
        self.choose_team_method = self.config.get('choose_team_method')
        self.vBoxLayout = QVBoxLayout(self)

        mode_changer = LineWidget.get_combo_box(
            label=self.tr('编队选择方式'),
            items=[self.tr('预设编队'), self.tr('按序编队')],
            current_index=0 if self.choose_team_method == "preset" else 1,
            callback=self._change_choose_team_method,
            parent=self
        )

        assert self.choose_team_method in ["preset", "order"], "Invalid choose_team_method"
        key = "preset_team_attribute" if self.choose_team_method == "preset" else "side_team_attribute"
        self._recreate_table(key)
        self.vBoxLayout.addLayout(mode_changer)
        self.vBoxLayout.addWidget(self.table)
        self.setLayout(self.vBoxLayout)

        # Though it's meaningless, the visual effect is better
        if self.choose_team_method == "order":
            self._recreate_table("preset_team_attribute")
            self._recreate_table("side_team_attribute")

    def _change_choose_team_method(self, index):
        self.choose_team_method = "preset" if index == 0 else "order"
        self.config.set('choose_team_method', self.choose_team_method)
        key = "preset_team_attribute" if self.choose_team_method == "preset" else "side_team_attribute"
        self._recreate_table(key)

    def _recreate_table(self, key):
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
