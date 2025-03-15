import re
from functools import partial

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QFrame, QHeaderView, QHBoxLayout
from qfluentwidgets import MessageBoxBase, TableWidget, CheckBox, LineEdit, ComboBox, PushButton
from qfluentwidgets.window.fluent_window import FluentWindowBase, FluentTitleBar


class BoundComponent(QObject):
    """
    BoundComponent is a class that binds a component to a string rule. The string rule is a string that contains
    placeholders that are keys in the config. When the config is updated, the component will be updated with the new
    value. The rule string is a definition of how the component should be updated. For example, if the rule is
    "Title: {title} - Subtitle: {subtitle}", the component will be updated with the new value of the title and subtitle
    keys in the config.

    :param component: Component to bind
    :param string_rule: String rule to bind
    :param config_manager: Config manager
    :param attribute: Attribute to bind (default is setText)
    """

    def __init__(self, component, string_rule, config_manager, attribute="setText"):
        super().__init__()
        self.component = component
        self.attribute = attribute
        self.string_rule = string_rule
        self.config_manager = config_manager
        self.update_component()  # 初始化时更新组件

    def update_component(self):
        """ Update the component with the new value """
        # Replace the keys in the rule with the values in the config
        new_value = self.string_rule
        keys_in_rule = re.findall(r'{(.*?)}', self.string_rule)
        for key in keys_in_rule:
            new_value = new_value.replace(f'{{{key}}}', self.config_manager.get(key, ''))

        # Dynamic call the attribute function of the component
        getattr(self.component, self.attribute)(new_value)

    def config_updated(self, key):
        if f'{{{key}}}' in self.string_rule:
            self.update_component()


class PureWindow(FluentWindowBase):
    """
    A custom window class inheriting from FluentWindowBase.

    This class provides a simplified structure with a title bar and
    a widget layout. It is designed to manage and organize UI elements
    efficiently, with a resizable title bar and support for dynamic widget
    integration.
    """

    def __init__(self):
        """
        Initializes the PureWindow instance.

        Sets up the title bar, layout structure, and ensures the stacked widget
        is removed for a cleaner layout. Also establishes initial layout margins
        and raises the title bar to the forefront.
        """
        super().__init__()
        self.setTitleBar(FluentTitleBar(self))
        self.widgetLayout = QVBoxLayout()
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)
        self.hBoxLayout.addLayout(self.widgetLayout)
        self.hBoxLayout.setStretchFactor(self.widgetLayout, 1)
        self.stackedWidget.deleteLater()
        self.titleBar.raise_()

    def resizeEvent(self, _):
        """
        Handles the resize event for the window.

        Adjusts the title bar's position and width dynamically based
        on the window's current size.
        """
        self.titleBar.move(20, 0)
        self.titleBar.resize(self.width() - 20, self.titleBar.height())

    def setWidget(self, widget):
        """
        Adds a widget to the layout.

        Args:
            widget: The QWidget instance to be added to the layout.
        """
        self.widgetLayout.addWidget(widget)


class OutlineLabel(QLabel):
    """
    A custom QLabel that displays text with an outline effect.
    """

    def __init__(self, text, parent=None, *args, **kwargs):
        """
        Initializes the OutlineLabel.

        Args:
            text (str): The text to display in the label.
            parent (QWidget, optional): The parent widget. Defaults to None.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments. Includes:
                font_size (int): The font size for the text. Defaults to 20.
                font_family (str): The font family for the text. Defaults to "Arial".
                font_weight (QFont.Weight): The font weight for the text. Defaults to QFont.Bold.
                outline_color (QColor): The color for the text outline. Defaults to white.
                text_color (QColor): The color for the main text. Defaults to black.
        """
        super().__init__(text, parent)
        if args: self.init_args = args
        font_size = kwargs.get('font_size', 20)  # Retrieve font size from kwargs
        font_family = kwargs.get('font_family', "Arial")  # Retrieve font family from kwargs
        font_weight = kwargs.get('font_weight', QFont.Bold)  # Retrieve font weight from kwargs

        self.outline_color = kwargs.get('outline_color', QColor("white"))  # Retrieve outline color from kwargs
        self.text_color = kwargs.get('text_color', QColor("black"))  # Retrieve text color from kwargs

        self.setFont(QFont(font_family, font_size, font_weight))
        self.setAlignment(Qt.AlignCenter)  # Align text to the center

    def paintEvent(self, event):
        """
        Reimplements the paintEvent to add an outline effect to the text.

        Args:
            event (QPaintEvent): The paint event object.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smooth edges

        outline_color = self.outline_color  # Color for the text outline
        text_color = self.text_color  # Color for the main text

        # Draw text outline
        painter.setPen(outline_color)
        x_offset = y_offset = 1  # Offset for the outline
        for dx in (-x_offset, 0, x_offset):
            for dy in (-y_offset, 0, y_offset):
                if dx != 0 or dy != 0:  # Skip the center to avoid overlapping
                    painter.drawText(self.rect().translated(dx, dy), Qt.AlignCenter, self.text())

        # Draw main text
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


class DialogSettingBox(MessageBoxBase):
    """
    A custom message box with a settings layout.

    This dialog box supports dynamic layouts and can adjust its size
    based on specific settings.
    """

    def __init__(self, parent=None, config=None, layout=None, *_, **kwargs):
        """
        Initializes the DialogSettingBox.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            config (Config, optional): Configuration object for settings injection. Defaults to None.
            layout (QLayout, optional): The layout to display inside the dialog. Defaults to None.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent)

        setting_name = kwargs.get('setting_name')  # Retrieve the setting name from kwargs
        self.config = config  # Store the configuration object

        # Create a frame to wrap the provided layout
        frame = QFrame(self)
        layout_wrapper = QVBoxLayout(frame)
        layout_wrapper.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout_wrapper.setSpacing(0)  # Set spacing to zero
        layout_wrapper.addWidget(layout)  # Add the provided layout to the wrapper

        # Apply a global style sheet to the layout
        layout.setStyleSheet("""
            * {
                font-family: "Microsoft YaHei";
                font-size: 14px;
            }
        """)

        # Adjust the frame's minimum width if the setting name indicates a shop layout
        if 'shop' in setting_name or 'Shop' in setting_name:
            frame.setMinimumWidth(800)

        # Set the wrapper layout for the frame
        frame.setLayout(layout_wrapper)

        # Add the frame to the dialog's main layout
        self.viewLayout.addWidget(frame)


class TableManager(TableWidget):
    """
    A class that manages a table widget with configurable data, headers, and unit components.
    Supports various input types such as labels, combo boxes, line edits, and checkboxes.
    """

    def __init__(self, parent,
                 config,
                 data_key: str,
                 unit_config: dict,
                 update_callback=None,
                 col_headers: list = None,
                 row_headers=None,
                 col_length=1,
                 convert_dict=None,
                 convert_method=None,
                 transpose=False,
                 **kwargs):
        """
        Initializes the TableManager.

        :param parent: The parent widget.
        :param config: Configuration object storing table data.
        :param data_key: The key to access data from config.
        :param unit_config: Configuration dictionary defining the type of UI component.
        :param update_callback: Callback function triggered on value updates.
        :param col_headers: List of column headers.
        :param row_headers: List of row headers.
        :param col_length: Number of columns in the table.
        :param convert_dict: Dictionary for value conversions.
        :param convert_method: Function for data conversion.
        :param transpose: Flag to transpose the data.
        """
        super().__init__(parent)
        self.config = config
        self.data = None
        self.parent = parent
        self.data_key = data_key
        self.update_callback = update_callback
        self.unit_config = unit_config
        self.convert_dict = convert_dict
        self.convert_method = convert_method
        self.col_length = col_length
        self.col_headers = col_headers
        self.row_headers = row_headers

        # Reverse lookup dictionary for value conversion
        self.revert_dict = {v: k for k, v in self.convert_dict.items()} if self.convert_dict else None

        # Initialize the table with given settings
        self.reset_table(data_key, unit_config, update_callback, col_headers, row_headers, col_length, transpose, **kwargs)

        # Disable direct editing in the table
        self.setEditTriggers(self.NoEditTriggers)

    @staticmethod
    def __transpose__(data):
        return [[data[j][i] for j in range(len(data))] for i in range(len(data[0]))]

    def reset_table(self, data_key, unit_config: dict, update_callback=None,
                    col_headers: list = None, row_headers=None, col_length=None, transpose=False, **kwargs):
        """
        Resets the table with new configuration settings.

        :param data_key: The key to access data from config.
        :param unit_config: Dictionary defining UI components.
        :param update_callback: Function triggered when values change.
        :param col_headers: Optional list of column headers.
        :param row_headers: Optional list of row headers.
        :param col_length: Number of columns.
        :param transpose: Flag to transpose the data.
        """
        self.setFixedHeight(kwargs.get('height', 200))
        self.data_key = data_key if data_key else self.data_key
        self.update_callback = update_callback if update_callback else self.update_callback
        self.unit_config = unit_config if unit_config else self.unit_config
        self.setColumnCount(col_length if col_length else self.col_length)

        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        # 设置列头
        if col_headers is not None or (self.col_headers and row_headers is None):
            self.setVerticalHeaderLabels(col_headers or self.col_headers)
            self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.verticalHeader().show()

        # 设置行头
        if row_headers is not None or (self.row_headers and col_headers is None):
            self.setHorizontalHeaderLabels(row_headers or self.row_headers)
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.horizontalHeader().show()

        self.create_table(transpose)

    def create_table(self, transpose=False):
        """
        Populates the table with data and initializes UI components.
        """
        self.data = self.config.get(self.data_key, None)
        assert self.data is not None, f"Invalid data key: {self.data_key}"

        if transpose:
            self.data = self.__transpose__(self.data)

        self.setRowCount(len(self.data))
        self.setColumnCount(len(self.data[0]))

        # Iterate through the data and create UI components
        for _row, _row_data in enumerate(self.data):
            for _col, unit_data in enumerate(_row_data):
                unit_component = None
                if self.unit_config["type"] == "label":
                    unit_component = QLabel(unit_data, self.parent)
                if self.unit_config["type"] == "comboBox":
                    unit_component = ComboBox(self.parent)
                    unit_component.addItems(self.unit_config["items"])
                    unit_component.setCurrentText(self.convert_dict.get(unit_data, unit_data))
                    unit_component.currentTextChanged.connect(
                        partial(self._parse_update, _row, _col))
                if self.unit_config["type"] == "lineEdit":
                    unit_component = LineEdit(self.parent)
                    unit_component.setText(unit_data)
                    unit_component.textChanged.connect(partial(self._parse_update, _row, _col))
                if self.unit_config["type"] == "switch":
                    unit_component = CheckBox(self.parent)
                    unit_component.setChecked(unit_data)
                    unit_component.stateChanged.connect(
                        partial(self._parse_update, _row, _col))

                self.setCellWidget(_row, _col, unit_component)

    def _parse_update(self, row, col, *args):
        """
        Handles updates to table cell values.

        :param row: Row index of the updated cell.
        :param col: Column index of the updated cell.
        :param args: Updated value.
        """
        value = args[0]
        self.data[row][col] = self.revert_dict.get(value, value)
        self.config.set(self.data_key, self.data)
        if self.update_callback:
            self.update_callback(row, col, value)


class LineWidget:
    """
    A utility class for creating different types of interactive widgets within a horizontal layout.
    """

    @staticmethod
    def get_btn(label, text, callback, tips=None, parent=None):
        """Creates a button with a label."""
        layout = QHBoxLayout()
        label = QLabel(label, parent)
        btn = PushButton(parent)
        btn.setText(text)
        btn.clicked.connect(callback)
        if tips:
            label.setToolTip(tips)
        layout.addWidget(label, 1, Qt.AlignLeft)
        layout.addWidget(btn, 1, Qt.AlignRight)
        return layout

    @staticmethod
    def get_text_edit(label, text, callback, tips=None, parent=None):
        """Creates a text edit field with a label."""
        layout = QHBoxLayout()
        label = QLabel(label, parent)
        edit = LineEdit(parent)
        edit.setText(text)
        edit.textChanged.connect(callback)
        if tips:
            label.setToolTip(tips)
        layout.addWidget(label, 1, Qt.AlignLeft)
        layout.addWidget(edit, 1, Qt.AlignRight)
        return layout

    @staticmethod
    def get_combo_box(label, items, current_index, callback, tips=None, parent=None):
        """Creates a combo box with a label."""
        layout = QHBoxLayout()
        label = QLabel(label, parent)
        combo = ComboBox(parent)
        combo.addItems(items)
        combo.setCurrentIndex(current_index)
        combo.currentIndexChanged.connect(callback)
        if tips:
            label.setToolTip(tips)
        layout.addWidget(label, 1, Qt.AlignLeft)
        layout.addWidget(combo, 1, Qt.AlignRight)
        return layout

    @staticmethod
    def get_check_box(label, checked, callback, tips=None, parent=None):
        """Creates a checkbox with a label."""
        layout = QHBoxLayout()
        label = QLabel(label, parent)
        check = CheckBox(parent)
        check.setChecked(checked)
        check.stateChanged.connect(callback)
        if tips:
            label.setToolTip(tips)
        layout.addWidget(label, 1, Qt.AlignLeft)
        layout.addWidget(check, 1, Qt.AlignRight)
        return layout
