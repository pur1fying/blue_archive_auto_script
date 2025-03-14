from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from gui.util.customed_ui import LineWidget, TableManager


class Layout(QWidget):
    PROPERTY: dict[str, str]
    NAME: dict[str, str]

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        ExploreConfig = QObject()
        self.PROPERTY = {
            "burst": ExploreConfig.tr('爆发'),
            "pierce": ExploreConfig.tr('贯穿'),
            "mystic": ExploreConfig.tr('神秘'),
            "shock": ExploreConfig.tr('振动'),
            "Unused": ExploreConfig.tr('未使用')
        }
        # Reverse the dictionary
        self.NAME = {v: k for k, v in self.PROPERTY.items()}
        self.COL_NUM_DICT = {
            "preset_team_attribute": 5,
            "side_team_attribute": 4
        }
        self.config = config
        self._init_ui()

    def _init_ui(self):
        self.choose_team_method = self.config.get('choose_team_method')

        self.vBoxLayout = QVBoxLayout()

        mode_changer = LineWidget.get_combo_box(
            label=self.tr('编队选择方式'),
            items=[self.tr('预设编队'), self.tr('按序编队')],
            current_index=0 if self.choose_team_method == "preset" else 1,
            callback=self._change_choose_team_method,
            parent=self
        )

        assert self.choose_team_method in ["preset", "order"], "Invalid choose_team_method"
        key = "preset_team_attribute" if self.choose_team_method == "preset" else "side_team_attribute"

        self.table = TableManager(parent=self,
                                  config=self.config,
                                  data_key=key,
                                  row_headers=[str(x + 1) for x in range(4)],
                                  col_length=self.COL_NUM_DICT[key],
                                  unit_config={
                                      "type": "comboBox",
                                      "items": [self.PROPERTY[x] for x in self.PROPERTY],
                                  },
                                  convert_dict=self.PROPERTY,
                                  )

        self.vBoxLayout.addLayout(mode_changer)
        self.vBoxLayout.addWidget(self.table)
        self.setLayout(self.vBoxLayout)

    def _change_choose_team_method(self, index):
        self.choose_team_method = "preset" if index == 0 else "order"
        self.config.set('choose_team_method', self.choose_team_method)
        key = "preset_team_attribute" if self.choose_team_method == "preset" else "side_team_attribute"
        self.table.reset_table(data_key=key, unit_config={
            "type": "comboBox",
            "items": [self.PROPERTY[x] for x in self.PROPERTY],
        }, col_length=self.COL_NUM_DICT[key])
