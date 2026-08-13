from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (
    QGridLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import CheckBox


SHOP_PREFERRED_WIDTH = 800
SHOP_MAX_WIDTH = 1000
SHOP_VIEWPORT_HEIGHT = 400
SHOP_DIALOG_HORIZONTAL_RESERVE = 96
SHOP_DIALOG_VERTICAL_RESERVE = 180

GRID_MIN_COLUMN_WIDTH = 220
GRID_HORIZONTAL_SPACING = 8
GRID_VERTICAL_SPACING = 8


class ShopGoodCard(QFrame):
    """One shop entry whose labels can grow vertically for translations."""

    def __init__(self, name, price, checked=False, price_first=True, parent=None):
        super().__init__(parent)
        self.setObjectName('shopGoodCard')
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            'QFrame#shopGoodCard {'
            '  border: 1px solid rgba(127, 127, 127, 70);'
            '  border-radius: 6px;'
            '  background-color: rgba(127, 127, 127, 10);'
            '}'
        )
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.check_box = CheckBox(self)
        self.check_box.setChecked(checked)
        self.check_box.setLayoutDirection(Qt.RightToLeft)

        self.name_label = QLabel(name, self)
        self.name_label.setWordWrap(True)
        self.name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.price_label = QLabel(price, self)
        self.price_label.setWordWrap(True)
        self.price_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.price_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        copy_layout = QVBoxLayout()
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(2)
        labels = (
            (self.price_label, self.name_label)
            if price_first
            else (self.name_label, self.price_label)
        )
        for label in labels:
            copy_layout.addWidget(label)

        item_layout = QHBoxLayout(self)
        item_layout.setContentsMargins(8, 6, 8, 6)
        item_layout.setSpacing(8)
        item_layout.addLayout(copy_layout, 1)
        item_layout.addWidget(self.check_box, 0, Qt.AlignVCenter)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.check_box.toggle()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ShopGoodsGrid(QWidget):
    """Equal-width grid that reflows from the actual available width."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._items = []
        self._column_count = 0
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)
        self._grid.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self._grid.setAlignment(Qt.AlignTop)

    def addWidget(self, widget):
        self._items.append(widget)
        self._reflow(max(1, self.width()))

    def _columns_for_width(self, width):
        return max(
            1,
            (max(1, width) + GRID_HORIZONTAL_SPACING)
            // (GRID_MIN_COLUMN_WIDTH + GRID_HORIZONTAL_SPACING),
        )

    def _reflow(self, width):
        columns = min(max(1, len(self._items)), self._columns_for_width(width))
        if columns == self._column_count and self._grid.count() == len(self._items):
            return

        previous_columns = self._column_count
        for widget in self._items:
            self._grid.removeWidget(widget)
        for column in range(max(previous_columns, columns)):
            self._grid.setColumnStretch(column, 0)
        for index, widget in enumerate(self._items):
            self._grid.addWidget(widget, index // columns, index % columns)
        for column in range(columns):
            self._grid.setColumnStretch(column, 1)
        self._column_count = columns
        self._sync_minimum_height(width)

    def _sync_minimum_height(self, width):
        self._grid.activate()
        if self._grid.hasHeightForWidth():
            height = self._grid.heightForWidth(max(1, width))
        else:
            height = self._grid.sizeHint().height()
        if height >= 0 and height != self.minimumHeight():
            self.setMinimumHeight(height)
            self.updateGeometry()

    def resizeEvent(self, event):
        self._reflow(event.size().width())
        self._sync_minimum_height(event.size().width())
        super().resizeEvent(event)

    def sizeHint(self):
        width = max(GRID_MIN_COLUMN_WIDTH, self.width())
        height = self._grid.heightForWidth(width) if self._grid.hasHeightForWidth() else self._grid.sizeHint().height()
        return QSize(SHOP_PREFERRED_WIDTH, max(0, height))
