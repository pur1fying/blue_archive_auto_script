import re
import threading
import time
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, QSizePolicy, QGraphicsBlurEffect
from qfluentwidgets import MessageBoxBase, SubtitleLabel, ImageLabel
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


class FuncLabel(QLabel):
    button_clicked_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(FuncLabel, self).__init__(parent)

    def mouseReleaseEvent(self, QMouseEvent):
        self.button_clicked_signal.emit()

    def connect_customized_slot(self, func):
        self.button_clicked_signal.connect(func)


class AssetsWidget(QFrame):
    def __init__(self, config, parent, **kwargs):
        super().__init__(parent)
        self.config = config
        self.item_height = kwargs.get('item_height', 30)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.patch_v_dict = {}
        self.patch_t_dict = {}
        self.disp_config = {
            "First": {
                "ap": {
                    "name": self.tr("体力"),
                    'icon': 'gui/assets/icons/currency_icon_ap.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                },
                "creditpoints": {
                    "name": self.tr("信用点"),
                    'icon': 'gui/assets/icons/currency_icon_gold.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                },
                "pyroxene": {
                    "name": self.tr("青辉石"),
                    'icon': 'gui/assets/icons/currency_icon_gem.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                },
                "tactical_challenge_coin": {
                    "name": self.tr("竞技币"),
                    'icon': 'gui/assets/icons/item_icon_arenacoin.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                }
            },
            "Second": {

                "bounty_coin": {
                    "name": self.tr("悬赏令"),
                    'icon': 'gui/assets/icons/item_icon_chasercoin.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                },
                "Keystone-Piece": {
                    "name": self.tr("拱心片"),
                    'icon': 'gui/assets/icons/item_icon_craftitem_0.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                },
                "Keystone": {
                    "name": self.tr("拱心石"),
                    'icon': 'gui/assets/icons/item_icon_craftitem_1.webp',
                    'value': 'UNK',
                    "time": 'UNK'
                }
            }
        }
        self._parse_config()
        self._apply_config_to_layout(self.disp_config)
        # self.setStyleSheet('background-color: #53ffffff; border-radius: 10px; border: 2px dashed #66000000;')
        self.setStyleSheet("""
            AssetsWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 10px;
                border: 2px dashed rgba(0, 0, 0, 0.4);
            }

            QLabel {
                font-size: %dpx;
                line-height: %dpx;
                border: none;
            }

            QToolTip {
                 background-color: rgba(80, 80, 80, 0.9);  /* 深灰色背景 */
                 color: white;  /* 文字白色 */
                 border-radius: 5px;
                 padding: 5px;
                 font-size: 14px;
                 height: 20px;
             }
        """ % ((self.item_height - 10) // 2, self.item_height))

    def get_unit_layout(self, item_key, item_icon_path, item_name, item_value, item_time, parent=None):
        item_value = str(item_value)
        unit_layout = QHBoxLayout(parent)
        unit_layout.setSpacing(0)
        unit_layout.setContentsMargins(0, 0, 0, 0)

        item_icon_widget = ImageLabel(item_icon_path, parent)
        item_icon_widget.setFixedSize(self.item_height + 5, self.item_height)
        item_icon_widget.setToolTip(item_name)
        unit_layout.addWidget(item_icon_widget, 0, Qt.AlignLeft)

        text_layout = QVBoxLayout()

        item_value_label = SubtitleLabel(f"{item_name}: {item_value}", parent)
        item_value_label.setFixedHeight(self.item_height // 2)
        item_value_label.setAlignment(Qt.AlignLeft)
        self.patch_v_dict[item_key] = item_value_label
        text_layout.addWidget(item_value_label, 1, Qt.AlignLeft)

        item_time_label = SubtitleLabel(item_time, parent)
        item_time_label.setFixedHeight(self.item_height // 2)
        item_time_label.setAlignment(Qt.AlignLeft)
        self.patch_t_dict[item_key] = item_time_label
        text_layout.addWidget(item_time_label, 1, Qt.AlignLeft)

        unit_layout.addLayout(text_layout, 1)

        unit_layout.setSpacing(0)
        unit_layout.setContentsMargins(0, 0, 0, 0)
        return unit_layout

    def _apply_config_to_layout(self, disp_config):
        for key, value in disp_config.items():
            line_widget = QWidget()
            line_layout = QHBoxLayout()
            line_layout.setSpacing(0)
            line_layout.setContentsMargins(4, 4, 4, 4)

            line_widget.setMinimumSize(0, 0)  # ✅ Avoid 22px height
            line_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # ✅ Horizontal expanding

            line_widget.setLayout(line_layout)

            for ind, (item_key, v) in enumerate(value.items()):
                if ind != 0: line_layout.addSpacing(10)
                line_layout.addLayout(self.get_unit_layout(
                    item_key, v['icon'], v['name'], v['value'], v['time'], line_widget))
            line_widget.setContentsMargins(0, 0, 0, 0)
            line_layout.setSpacing(0)
            self.layout.addWidget(line_widget, 0, Qt.AlignRight)

    def _parse_config(self):
        # AP
        original_ap = self.config.get('ap', 'UNK')
        if type(original_ap) == dict:
            ap_value = original_ap.get('count', 'UNK')
            max_value = original_ap.get('max', 'UNK')
            ap_time = original_ap.get('time', 'UNK')
            ap_value = ap_value if ap_value != -1 else 'UNK'
            max_value = max_value if max_value != -1 else 'UNK'
            self.disp_config.get('First').get('ap')['value'] = f"{ap_value}/{max_value}"
            self.disp_config.get('First').get('ap')['time'] = self._parse_time(ap_time)

        original_creditpoints = self.config.get('creditpoints', 'UNK')
        if type(original_creditpoints) == dict:
            creditpoints_value = original_creditpoints.get('count', 'UNK')
            creditpoints_time = original_creditpoints.get('time', 'UNK')
            creditpoints_value = creditpoints_value if creditpoints_value != -1 else 'UNK'
            self.disp_config.get('First').get('creditpoints')['value'] = creditpoints_value
            self.disp_config.get('First').get('creditpoints')['time'] = self._parse_time(creditpoints_time)

        original_pyroxene = self.config.get('pyroxene', 'UNK')
        if type(original_pyroxene) == dict:
            pyroxene_value = original_pyroxene.get('count', 'UNK')
            pyroxene_time = original_pyroxene.get('time', 'UNK')
            pyroxene_value = pyroxene_value if pyroxene_value != -1 else 'UNK'
            self.disp_config.get('First').get('pyroxene')['value'] = pyroxene_value
            self.disp_config.get('First').get('pyroxene')['time'] = self._parse_time(pyroxene_time)

        original_tactical_challenge_coin = self.config.get('tactical_challenge_coin', 'UNK')
        if type(original_tactical_challenge_coin) == dict:
            tactical_challenge_coin_value = original_tactical_challenge_coin.get('count', 'UNK')
            tactical_challenge_coin_time = original_tactical_challenge_coin.get('time', 'UNK')
            tactical_challenge_coin_value = tactical_challenge_coin_value if tactical_challenge_coin_value != -1 else 'UNK'
            self.disp_config.get('First').get('tactical_challenge_coin')['value'] = tactical_challenge_coin_value
            self.disp_config.get('First').get('tactical_challenge_coin')['time'] = self._parse_time(
                tactical_challenge_coin_time)

        original_bounty_coin = self.config.get('bounty_coin', 'UNK')
        if type(original_bounty_coin) == dict:
            bounty_coin_value = original_bounty_coin.get('count', 'UNK')
            bounty_coin_time = original_bounty_coin.get('time', 'UNK')
            bounty_coin_value = bounty_coin_value if bounty_coin_value != -1 else 'UNK'
            self.disp_config.get('Second').get('bounty_coin')['value'] = bounty_coin_value
            self.disp_config.get('Second').get('bounty_coin')['time'] = self._parse_time(bounty_coin_time)

        original_keystone_piece = self.config.get('create_item_holding_quantity').get('Keystone-Piece', 'UNK')
        original_keystone_piece = original_keystone_piece if original_keystone_piece != -1 else 'UNK'
        original_keystone = self.config.get('create_item_holding_quantity').get('Keystone', 'UNK')
        original_keystone = original_keystone if original_keystone != -1 else 'UNK'
        self.disp_config.get('Second').get('Keystone-Piece')['value'] = original_keystone_piece
        self.disp_config.get('Second').get('Keystone-Piece')['time'] = "/"
        self.disp_config.get('Second').get('Keystone')['value'] = original_keystone
        self.disp_config.get('Second').get('Keystone')['time'] = "/"

    def _apply_config(self):
        self.patch_v_dict['ap'].setText(
            f"{self.disp_config.get('First').get('ap')['name']}: {self.disp_config.get('First').get('ap')['value']}")
        self.patch_t_dict['ap'].setText(self.disp_config.get('First').get('ap')['time'])
        self.patch_v_dict['creditpoints'].setText(
            f"{self.disp_config.get('First').get('creditpoints')['name']}: {self.disp_config.get('First').get('creditpoints')['value']}")
        self.patch_t_dict['creditpoints'].setText(self.disp_config.get('First').get('creditpoints')['time'])
        self.patch_v_dict['pyroxene'].setText(
            f"{self.disp_config.get('First').get('pyroxene')['name']}: {self.disp_config.get('First').get('pyroxene')['value']}")
        self.patch_t_dict['pyroxene'].setText(self.disp_config.get('First').get('pyroxene')['time'])
        self.patch_v_dict['tactical_challenge_coin'].setText(
            f"{self.disp_config.get('First').get('tactical_challenge_coin')['name']}: {self.disp_config.get('First').get('tactical_challenge_coin')['value']}")
        self.patch_t_dict['tactical_challenge_coin'].setText(
            self.disp_config.get('First').get('tactical_challenge_coin')['time'])

        self.patch_v_dict['bounty_coin'].setText(
            f"{self.disp_config.get('Second').get('bounty_coin')['name']}: {self.disp_config.get('Second').get('bounty_coin')['value']}")
        self.patch_t_dict['bounty_coin'].setText(self.disp_config.get('Second').get('bounty_coin')['time'])
        self.patch_v_dict['Keystone-Piece'].setText(
            f"{self.disp_config.get('Second').get('Keystone-Piece')['name']}: {self.disp_config.get('Second').get('Keystone-Piece')['value']}")
        self.patch_v_dict['Keystone'].setText(
            f"{self.disp_config.get('Second').get('Keystone')['name']}: {self.disp_config.get('Second').get('Keystone')['value']}")

    def _parse_time(self, timestamp: float) -> str:
        """
        Converts a timestamp into a human-readable format such as
        "5 minutes ago", "1 second ago", "3 hours ago", or "1 day ago",
        with support for internationalization.

        :param timestamp: Unix timestamp (seconds)
        :param parent: Pass a QObject to support .tr()
        :return: A localized, human-readable time string
        """
        assert type(timestamp) in [int, float], "Timestamp must be an integer or float"
        timestamp = int(timestamp)
        if timestamp == 0:
            return "UNK"
        now = datetime.now()
        past = datetime.fromtimestamp(timestamp)
        diff = now - past  # Calculate time difference

        if diff < timedelta(seconds=60):
            return self.tr("{0}秒前").format(diff.seconds)
        elif diff < timedelta(hours=1):
            return self.tr("{0}分钟前").format(diff.seconds // 60)
        elif diff < timedelta(days=1):
            return self.tr("{0}小时前").format(diff.seconds // 3600)
        elif diff < timedelta(days=30):
            return self.tr("{0}天前").format(diff.days)
        elif diff < timedelta(days=365):
            return self.tr("{0}个月前").format(diff.days // 30)
        else:
            return self.tr("{0}年前").format(diff.days // 365)

    def start_patch(self):
        def __interval__(interval=1):
            while True:
                self._parse_config()
                self._apply_config()
                time.sleep(interval)

        threading.Thread(target=__interval__, daemon=True).start()
