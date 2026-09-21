import re
from functools import partial
import threading
import time
from datetime import datetime, timedelta

from typing import Union

from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal, QRect, QRectF, QPropertyAnimation
from PyQt5.QtGui import QFont, QPainter, QColor, QIcon, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QFrame, QHeaderView, QHBoxLayout, QWidget, QScrollArea,
    QApplication, QSizePolicy,
)
from qfluentwidgets import (MessageBoxBase, TableWidget, CheckBox, LineEdit, SubtitleLabel, ImageLabel, FlowLayout,
                            ComboBox, PushButton, ExpandSettingCard, FluentIcon as FIF, ScrollArea)
from qfluentwidgets.window.fluent_window import FluentWindowBase, FluentTitleBar

from gui.util.config_gui import configGui, COLOR_THEME


class ViewportCappedFragment:
    """页级容器约束：sizeHint 高度永不超过当前视口高度。

    背景：qframelesswindow 在 Windows 高 DPI（如 200% 缩放）下，窗口
    首次移动会做一次性原生几何重对齐，目标高度取自当前页内容的
    sizeHint——若任何一页的内容期望高度大于窗口，首次拖动标题栏时
    窗口就会被一次性加高（如 900x700 -> 900x747），此后不再复现。
    上游各页均为固定骨架，sizeHint 天然不超视口，不会触发；工具大厅
    的插件槽位内容高度动态，属于风险面。混入此约束后，sizeHint 始终
    被钳制在当前可视高度内，原生重对齐的目标与现状一致，从结构上
    使该 bug 无法被后续插件开发触发。

    用法：页类定义处同时继承 QWidget 系基类与本类，如
        class HomeFragment(ViewportCappedFragment, QFrame):
    注意本类须放在基类之前，且页面用布局管理器正常布局即可，无
    额外调用。
    """

    def sizeHint(self):
        hint = super().sizeHint()
        try:
            h = self.height()
            if h > 0 and hint.height() > h:
                hint = hint.__class__(hint.width(), h)
        except Exception:
            pass
        return hint

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        try:
            h = self.height()
            if h > 0 and hint.height() > h:
                hint = hint.__class__(hint.width(), h)
        except Exception:
            pass
        return hint


class ViewportCappedVBoxLayout(QVBoxLayout):
    """布局级视口高度约束（与 ViewportCappedFragment 配套，二者缺一不可）。

    诊断结论：QStackedLayout 等布局链路会绕过 QWidget.sizeHint()，直接
    读取页面顶层布局的 totalSizeHint()/sizeHint()——实测页 widget 的
    sizeHint 已钳制到视口高 651 时，QStackedWidget.sizeHint 仍取布局
    totalSizeHint=698，窗口布局合计 747，正是 frameless 窗口首次移动
    被原生层一次性拉高的目标值。页面顶层布局必须同样钳制。
    """

    def _capped(self, hint):
        try:
            w = self.widget()
            if w is None:
                w = self.parentWidget()
            if w is not None:
                h = w.height()
                if h > 0 and hint.height() > h:
                    hint.setHeight(h)
        except Exception:
            pass
        return hint

    def hasHeightForWidth(self):
        # 关键：不向父级布局链传播 hfw。QStackedLayout::heightForWidth 会
        # 直接问每页 widget->heightForWidth()（穿透到页内流式布局的自然
        # 高度），QLayout::totalSizeHint 又在 hasHeightForWidth() 为真时用
        # 该值顶掉 sizeHint 高度——这正是插件槽位内容把窗口"期望高度"
        # 撑到视口之上的通道。对父级声明 False 后，页面外的 hint 链条
        # 全部走 sizeHint()（已被本类钳制）；页内部子项的行高排布仍按
        # 子项各自的 hfw 正常工作，不受影响。
        return False

    def totalSizeHint(self):
        return self._capped(super().totalSizeHint())

    def sizeHint(self):
        return self._capped(super().sizeHint())


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
        font_family = kwargs.get('font_family', "Microsoft YaHei")  # Retrieve font family from kwargs
        font_weight = kwargs.get('font_weight', QFont.Bold)  # Retrieve font weight from kwargs
        self.outline_color = kwargs.get('outline_color', QColor("white"))  # Retrieve outline color from kwargs
        self.text_color = kwargs.get('text_color', QColor("black"))  # Retrieve text color from kwargs

        font_weight = {
            QFont.Bold: 'bold',
            QFont.Normal: 'normal',
            QFont.Light: 'light',
            QFont.Thin: 'thin',
            QFont.Medium: 'medium',
            QFont.DemiBold: 'demibold',
            QFont.Black: 'black',
        }[font_weight]

        self.setStyleSheet("""
            font-family: %(font_family)s;
            font-size: %(font_size)dpx;
            font-weight: %(font_weight)s;
        """ % {
            'font_family': font_family,
            'font_size': font_size,
            'font_weight': font_weight
        })
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
    """Settings dialog with target-only shop and cafe sizing."""

    _TARGET_SHOPS = {"shoppriority", "arenashoppriority"}
    _TARGET_CAFE = "cafeinvite"
    _HORIZONTAL_CHROME = 48
    _VERTICAL_CHROME = 129
    _SCREEN_MARGIN = 64
    # 咖啡厅内容的真实最小宽度。低于 Layout 的 640 竖排断点，
    # 窄窗口下弹窗才能真正进入竖排而不是溢出屏幕。
    _CAFE_MIN_WIDTH = 360
    # 商店弹窗内容区的最小可视高度：保住一行商品可见。
    _SHOP_MIN_HEIGHT = 160

    def __init__(self, parent=None, config=None, layout=None, *_, **kwargs):
        super().__init__(parent)

        setting_name = str(kwargs.get("setting_name") or "").lower()
        self.config = config
        self._content_layout = layout

        self.yesButton.setText(self.tr("确定"))
        self.cancelButton.setText(self.tr("取消"))

        # Create a frame to wrap the provided layout
        frame = QFrame(self)
        layout_wrapper = QVBoxLayout(frame)
        layout_wrapper.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout_wrapper.setSpacing(0)  # Set spacing to zero
        layout_wrapper.addWidget(layout)  # Add the provided layout to the wrapper

        # Apply a global style sheet to the layout
        layout.setStyleSheet(
            '* {\n'
            '    font-family: "Microsoft YaHei";\n'
            '    font-size: 14px;\n'
            '}\n'
        )

        if setting_name in self._TARGET_SHOPS:
            self._init_shop(frame, layout, parent)
        elif setting_name == self._TARGET_CAFE:
            self._init_cafe(frame, layout, parent)
        else:
            self._init_upstream(frame, layout)

    def _init_upstream(self, frame, layout):
        """Preserve the original geometry for every non-target page."""
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        if layout is not None and hasattr(layout, "setSizePolicy"):
            layout.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        scroll_area = ScrollArea()
        scroll_area.setStyleSheet(
            "background-color: transparent;\nborder: none;\n"
        )
        scroll_area.setWidget(frame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # hoard_ap_cafe_viewport_v2
        try:
            _sn = str(setting_name or '')
            _is_hoard = ('hoard' in _sn.lower()) or ('Hoard' in _sn)
            if _is_hoard:
                scroll_area.setFixedWidth(min(max(self.width() - 80, 860), 960))
                scroll_area.setFixedHeight(480)
                try:
                    content_h = int(layout.minimumSizeHint().height())
                except Exception:
                    content_h = 420
                try:
                    frame.setMinimumWidth(860)
                    frame.setMinimumHeight(max(content_h, 420))
                except Exception:
                    pass
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        except Exception:
            pass
        # hoard_ap_single_scroll_v3
        try:
            _sn = str(setting_name or '')
            _inner = layout
            _prop = False
            try:
                _prop = bool(_inner.property('hoardSingleScroll')) or bool(_inner.property('hoardFreezeTop'))
            except Exception:
                _prop = False
            _name = ''
            try:
                _name = str(_inner.objectName() or '')
            except Exception:
                pass
            if _prop or _name == 'hoardApLayout' or ('hoard' in _sn.lower()):
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except Exception:
            pass
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFixedWidth(self.width() - 100)
        self.viewLayout.addWidget(scroll_area)

    def _init_shop(self, frame, layout, parent):
        # 保存引用供 _refit_shop_height 在 show 后字体就绪时重算：
        # 构造期量高用的字体可能尚未应用样式表，长名换行按更小字体
        # 量矮，竞技场商品因此一页放不下出滚动条；show 时再量一次。
        self._shop_frame = frame
        self._shop_layout = layout
        self._shop_parent = parent
        content_width, content_height = self._compute_shop_size(layout, parent)
        self._shop_content_width = content_width
        self._shop_content_height = content_height

        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if layout is not None:
            layout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setFixedSize(content_width, content_height)
        self.viewLayout.addWidget(frame)
        self.widget.setFixedSize(
            content_width + self._HORIZONTAL_CHROME,
            content_height + self._VERTICAL_CHROME,
        )

    def _init_cafe(self, frame, layout, parent):
        available = self._available_geometry(parent)
        parent_width = self._parent_extent(parent, "width", available.width())
        parent_height = self._parent_extent(parent, "height", available.height())
        width_limit = min(parent_width, available.width()) - self._HORIZONTAL_CHROME - self._SCREEN_MARGIN
        height_limit = min(parent_height, available.height()) - self._VERTICAL_CHROME - self._SCREEN_MARGIN
        # 下限取咖啡厅内容的真实最小宽度（低于 640 竖排断点），
        # 窄窗口下内容宽度能真正跌破断点改走竖排，而不是溢出屏幕。
        content_width = max(self._CAFE_MIN_WIDTH, min(820, width_limit))
        content_height = max(360, min(480, height_limit))

        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if layout is not None:
            layout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 竖排堆叠时内容会高于弹窗可视高度，用内部滚动承接，
        # 避免通用设置或咖啡厅卡片被裁掉、控件不可点。
        scroll_area = ScrollArea()
        scroll_area.setStyleSheet(
            "background-color: transparent;\nborder: none;\n"
        )
        scroll_area.setWidget(frame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFixedSize(content_width, content_height)
        self.viewLayout.addWidget(scroll_area)
        self.widget.setFixedSize(
            content_width + self._HORIZONTAL_CHROME,
            content_height + self._VERTICAL_CHROME,
        )

    def _accelerate_fade_in(self):
        """把配置弹窗的整体弹出动画压到 0.1s 即加载完毕。

        弹窗淡入动画由基类 showEvent 创建（默认约 200ms），
        这里在动画启动后立刻把时长改为 100ms，并在淡入结束后
        清理整窗与内容容器上的图形特效（见 _finish_fade_in），
        避免弹窗持续离屏渲染，拖慢内部控件与下拉菜单。
        """
        try:
            animations = self.findChildren(QPropertyAnimation)
        except Exception:
            return
        for animation in animations:
            try:
                property_name = bytes(animation.propertyName()).decode("ascii", "ignore").lower()
            except Exception:
                property_name = ""
            if "opacity" not in property_name:
                continue
            try:
                animation.setDuration(100)
                animation.finished.connect(self._finish_fade_in)
            except Exception:
                pass

    def _finish_fade_in(self):
        """淡入结束后移除弹窗上的图形特效，恢复正常渲染。

        基类在构造时给内容容器挂了一个大模糊半径的投影特效，
        且不会移除：挂了特效的容器会持续离屏渲染，弹窗内任何
        重绘（悬停、下拉展开收起）都要重画整棵内容树并重算模糊，
        内部控件和下拉菜单因此明显滞涩。淡入用的透明度特效也一并
        兜底清理（部分版本组件库不会自动移除）。
        """
        try:
            if self.graphicsEffect() is not None:
                self.setGraphicsEffect(None)
        except Exception:
            pass
        try:
            widget = getattr(self, "widget", None)
            if widget is not None and widget.graphicsEffect() is not None:
                widget.setGraphicsEffect(None)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        # 先按就绪字体重量高、把弹窗尺寸修正到真实内容高度，再启动
        # 淡入动画：构造期量矮的弹窗会在 show 瞬间长到内容高度。
        self._refit_shop_height()
        self._accelerate_fade_in()

    @staticmethod
    def _fit_shop_height(layout, width, cap):
        """按当前宽度下的实际内容高度收窄商店视口高度。

        内容比上限矮时贴着内容收口（避免弹窗底部空白），
        比上限高时维持上限交给面板内部滚动。
        """
        if layout is None:
            return cap
        try:
            if hasattr(layout, "hasHeightForWidth") and layout.hasHeightForWidth():
                desired = int(layout.heightForWidth(int(width)))
            else:
                desired = int(layout.sizeHint().height())
        except Exception:
            return cap
        if desired <= 0:
            return cap
        return max(DialogSettingBox._SHOP_MIN_HEIGHT, min(cap, desired))

    @staticmethod
    def _compute_shop_size(layout, parent):
        """商店弹窗的内容宽高：宽度取父窗口/屏幕较小值，高度先取上限
        再按当前宽度下的内容高度收窄。

        构造期与 show 后都调它。构造期样式表字体可能尚未应用到商品
        名标签，长名换行按更小字体量矮；show 后字体就绪，_refit_shop_height
        据此重量一次，弹窗随真实内容高度增长。
        """
        from gui.components.shop_goods import (
            GRID_COLUMNS,
            GRID_H_SPACING,
            MIN_COL_W,
            SHOP_MAX_WIDTH,
        )

        available = DialogSettingBox._available_geometry(parent)
        parent_width = DialogSettingBox._parent_extent(parent, "width", available.width())
        parent_height = DialogSettingBox._parent_extent(parent, "height", available.height())
        minimum_width = GRID_COLUMNS * MIN_COL_W + GRID_H_SPACING * (GRID_COLUMNS - 1)
        width_limit = min(parent_width, available.width()) - DialogSettingBox._HORIZONTAL_CHROME - DialogSettingBox._SCREEN_MARGIN
        content_width = max(minimum_width, min(SHOP_MAX_WIDTH, width_limit))
        # 高度与宽度一样取父窗口与屏幕的较小值：矮窗口里弹窗不能超过
        # 宿主；下限 160 保住一行商品可见，内容高于上限时交给面板内部
        # 滚动承接。不再施加固定视口上限，宿主足够高时随内容增长。
        cap = max(
            DialogSettingBox._SHOP_MIN_HEIGHT,
            min(parent_height, available.height())
            - DialogSettingBox._VERTICAL_CHROME
            - DialogSettingBox._SCREEN_MARGIN,
        )
        try:
            layout.ensurePolished()
        except Exception:
            pass
        content_height = DialogSettingBox._fit_shop_height(layout, content_width, cap)
        return content_width, content_height

    def _refit_shop_height(self):
        """show 后字体就绪，按真实字体重量高并重设弹窗尺寸。

        构造期 ensurePolished 不保证样式表字体已落到商品名标签，
        长名换行按更小的默认字体量高，弹窗被量矮、竞技场商品一页
        放不下出滚动条。show 时字体就绪，这里按真实字体重量一次，
        弹窗随真实内容高度增长，商品一页放完。尺寸未变则跳过，
        避免重复 showEvent 时无谓重排。
        """
        frame = getattr(self, "_shop_frame", None)
        layout = getattr(self, "_shop_layout", None)
        parent = getattr(self, "_shop_parent", None)
        if frame is None or layout is None:
            return
        content_width, content_height = self._compute_shop_size(layout, parent)
        if (
            content_height == getattr(self, "_shop_content_height", -1)
            and content_width == getattr(self, "_shop_content_width", -1)
        ):
            return
        self._shop_content_width = content_width
        self._shop_content_height = content_height
        frame.setFixedSize(content_width, content_height)
        self.widget.setFixedSize(
            content_width + self._HORIZONTAL_CHROME,
            content_height + self._VERTICAL_CHROME,
        )

    @staticmethod
    def _parent_extent(parent, method_name, fallback):
        if parent is None:
            return fallback
        method = getattr(parent, method_name, None)
        if not callable(method):
            return fallback
        try:
            value = int(method())
        except Exception:
            return fallback
        return value if value > 0 else fallback

    @staticmethod
    def _available_geometry(parent):
        screen = (
            parent.screen()
            if parent is not None and hasattr(parent, "screen")
            else None
        )
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is not None:
            return screen.availableGeometry()
        return QRect(0, 0, 1024, 768)

    def _is_draft(self) -> bool:
        return bool(getattr(self.config, "is_draft", False))

    def accept(self):
        from gui.util import notification
        from gui.util.config_draft import as_live

        if self._is_draft():
            self.config.flush_pending_editors(self)
            changed = self.config.commit()
            if changed:
                live = as_live(self.config)
                notification.saved(live, label=self.tr('已保存'))
        super().accept()

    def reject(self):
        if self._is_draft():
            self.config.rollback()
        super().reject()

class FuncLabel(QLabel):
    button_clicked_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(FuncLabel, self).__init__(parent)

    def mouseReleaseEvent(self, QMouseEvent):
        self.button_clicked_signal.emit()

    def connect_customized_slot(self, func):
        self.button_clicked_signal.connect(func)


class AssetsWidget(QFrame):
    signal_update = pyqtSignal()

    def __init__(self, config, parent, **kwargs):
        super().__init__(parent)
        self.config = config
        self.item_height = kwargs.get('item_height', 30)
        self.layout = FlowLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(4, 2, 4, 2)
        self.patch_v_dict = {}
        self.patch_t_dict = {}
        self.disp_config = {
            "ap": {
                "name": self.tr("体力"),
                'icon': 'gui/assets/icons/currency_icon_ap.webp',
                'value': 'Unknown',
                "time": '-'
            },
            "creditpoints": {
                "name": self.tr("信用点"),
                'icon': 'gui/assets/icons/currency_icon_gold.webp',
                'value': 'Unknown',
                "time": '-'
            },
            "pyroxene": {
                "name": self.tr("青辉石"),
                'icon': 'gui/assets/icons/currency_icon_gem.webp',
                'value': 'Unknown',
                "time": '-'
            },
            "tactical_challenge_coin": {
                "name": self.tr("竞技币"),
                'icon': 'gui/assets/icons/item_icon_arenacoin.webp',
                'value': 'Unknown',
                "time": '-'
            },
            "bounty_coin": {
                "name": self.tr("悬赏委托币"),
                'icon': 'gui/assets/icons/item_icon_chasercoin.webp',
                'value': 'Unknown',
                "time": '-'
            },
            "Keystone-Piece": {
                "name": self.tr("拱心石碎片"),
                'icon': 'gui/assets/icons/item_icon_craftitem_0.webp',
                'value': 'Unknown',
                "time": '-'
            },
            "Keystone": {
                "name": self.tr("拱心石"),
                'icon': 'gui/assets/icons/item_icon_craftitem_1.webp',
                'value': 'Unknown',
                "time": 'Unknown'
            }
        }
        self._specialize_config()
        self._parse_config()
        self._apply_config_to_layout(self.disp_config)
        self.signal_update.connect(self._apply_config)
        configGui.themeChanged.connect(self.repaint_color)
        self.repaint_color()

    def _specialize_config(self):
        if self.config.server_mode in ['JP']:
            self.disp_config = {
                **self.disp_config,
                "_pass": {
                    "name": self.tr("通行证"),
                    'icon': 'gui/assets/icons/item_icon_pass.webp',
                    'value': 'Unknown',
                    "time": '-'
                }
            }

    def repaint_color(self):
        self.setStyleSheet("""
            AssetsWidget {
                background-color: %(background_color)s;
                border-radius: 10px;
                border: 1px solid %(border_color)s;
            }

            QLabel {
                font-size: %(line_height)dpx;
                line-height: %(item_height)dpx;
                border: none;
                color: %(text_color)s;
            }

            QToolTip {
                 background-color: rgba(80, 80, 80, 0.9);  /* 深灰色背景 */
                 color: white;  /* 文字白色 */
                 border-radius: 5px;
                 padding: 5px;
                 font-size: 14px;
                 height: 20px;
             }
        """ % {
            'background_color': COLOR_THEME[configGui.theme.value]['background'],
            'border_color': COLOR_THEME[configGui.theme.value]['border'],
            'text_color': COLOR_THEME[configGui.theme.value]['text'],
            'line_height': (self.item_height - 10) // 2,
            'item_height': self.item_height
        })

    def get_unit_layout(self, item_key, item_icon_path, item_name, item_value, item_time, parent=None):

        unit_widget = QWidget(parent)

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

        unit_widget.setLayout(unit_layout)
        return unit_widget

    def _apply_config_to_layout(self, disp_config):

        for ind, (item_key, v) in enumerate(self.disp_config.items()):
            self.layout.addWidget(self.get_unit_layout(
                item_key, v['icon'], v['name'], v['value'], v['time'], self))

        # for key, value in disp_config.items():
        #     line_widget = QWidget()
        #     line_layout = QHBoxLayout()
        #     line_layout.setSpacing(0)
        #     line_layout.setContentsMargins(4, 4, 4, 4)
        #
        #     line_widget.setMinimumSize(0, 0)  # ✅ Avoid 22px height
        #     line_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # ✅ Horizontal expanding
        #
        #     line_widget.setLayout(line_layout)
        #
        #     for ind, (item_key, v) in enumerate(value.items()):
        #         if ind != 0: line_layout.addSpacing(10)
        #         line_layout.addLayout(self.get_unit_layout(
        #             item_key, v['icon'], v['name'], v['value'], v['time'], line_widget))
        #     line_widget.setContentsMargins(0, 0, 0, 0)
        #     line_layout.setSpacing(0)
        #     self.layout.addWidget(line_widget, 0, Qt.AlignRight)

    def _parse_config(self):
        # AP
        try:
            original_ap = self.config.get('ap', 'Unknown')
            if type(original_ap) == dict:
                ap_value = original_ap.get('count', 'Unknown')
                max_value = original_ap.get('max', 'Unknown')
                ap_time = original_ap.get('time', '-')
                ap_value = ap_value if ap_value != -1 else 'Unknown'
                max_value = max_value if max_value != -1 else 'Unknown'
                self.disp_config.get('ap')['value'] = f"{ap_value}/{max_value}"
                self.disp_config.get('ap')['time'] = self._parse_time(ap_time)

            original_creditpoints = self.config.get('creditpoints', 'Unknown')
            if type(original_creditpoints) == dict:
                creditpoints_value = original_creditpoints.get('count', 'Unknown')
                creditpoints_time = original_creditpoints.get('time', '-')
                creditpoints_value = creditpoints_value if creditpoints_value != -1 else 'Unknown'
                self.disp_config.get('creditpoints')['value'] = creditpoints_value
                self.disp_config.get('creditpoints')['time'] = self._parse_time(creditpoints_time)

            original_pyroxene = self.config.get('pyroxene', 'Unknown')
            if type(original_pyroxene) == dict:
                pyroxene_value = original_pyroxene.get('count', 'Unknown')
                pyroxene_time = original_pyroxene.get('time', '-')
                pyroxene_value = pyroxene_value if pyroxene_value != -1 else 'Unknown'
                self.disp_config.get('pyroxene')['value'] = pyroxene_value
                self.disp_config.get('pyroxene')['time'] = self._parse_time(pyroxene_time)

            original_tactical_challenge_coin = self.config.get('tactical_challenge_coin', 'Unknown')
            if type(original_tactical_challenge_coin) == dict:
                tactical_challenge_coin_value = original_tactical_challenge_coin.get('count', 'Unknown')
                tactical_challenge_coin_time = original_tactical_challenge_coin.get('time', '-')
                tactical_challenge_coin_value = tactical_challenge_coin_value if tactical_challenge_coin_value != -1 else 'Unknown'
                self.disp_config.get('tactical_challenge_coin')['value'] = tactical_challenge_coin_value
                self.disp_config.get('tactical_challenge_coin')['time'] = self._parse_time(
                    tactical_challenge_coin_time)

            original_bounty_coin = self.config.get('bounty_coin', 'Unknown')
            if type(original_bounty_coin) == dict:
                bounty_coin_value = original_bounty_coin.get('count', 'Unknown')
                bounty_coin_time = original_bounty_coin.get('time', '-')
                bounty_coin_value = bounty_coin_value if bounty_coin_value != -1 else 'Unknown'
                self.disp_config.get('bounty_coin')['value'] = bounty_coin_value
                self.disp_config.get('bounty_coin')['time'] = self._parse_time(bounty_coin_time)

            original_keystone_piece = self.config.get('create_item_holding_quantity').get('Keystone-Piece', 'Unknown')
            original_keystone_piece = original_keystone_piece if original_keystone_piece != -1 else 'Unknown'
            original_keystone = self.config.get('create_item_holding_quantity').get('Keystone', 'Unknown')
            original_keystone = original_keystone if original_keystone != -1 else 'Unknown'

            self.disp_config.get('Keystone-Piece')['value'] = original_keystone_piece
            self.disp_config.get('Keystone-Piece')['time'] = "/"
            self.disp_config.get('Keystone')['value'] = original_keystone
            self.disp_config.get('Keystone')['time'] = "/"
            if self.config.server_mode in ['JP']:
                original_pass = self.config.get('_pass', 'Unknown')
                if type(original_pass) == dict:
                    pass_level = original_pass.get('level', '-')
                    max_pass_level = original_pass.get('max_level', '-')
                    pass_next_level_point = original_pass.get('next_level_point', '-')
                    pass_next_level_point_required = original_pass.get('next_level_point_required', '-')
                    pass_weekly_point = original_pass.get('weekly_point', '-')
                    max_pass_weekly_point = original_pass.get('max_weekly_point', '-')

                    pass_time = original_pass.get('time', '-')
                    self.disp_config.get('_pass')['value'] = \
                        (f"{pass_level}/{max_pass_level};"
                         f"{pass_next_level_point}/{pass_next_level_point_required};"
                         f"{pass_weekly_point}/{max_pass_weekly_point}")
                    self.disp_config.get('_pass')['time'] = self._parse_time(pass_time)

        except:
            return

    def _apply_config(self):
        self.patch_v_dict['ap'].setText(
            f"{self.disp_config.get('ap')['name']}: {self.disp_config.get('ap')['value']}")
        self.patch_t_dict['ap'].setText(self.disp_config.get('ap')['time'])
        self.patch_v_dict['creditpoints'].setText(
            f"{self.disp_config.get('creditpoints')['name']}: {self.disp_config.get('creditpoints')['value']}")
        self.patch_t_dict['creditpoints'].setText(self.disp_config.get('creditpoints')['time'])
        self.patch_v_dict['pyroxene'].setText(
            f"{self.disp_config.get('pyroxene')['name']}: {self.disp_config.get('pyroxene')['value']}")
        self.patch_t_dict['pyroxene'].setText(self.disp_config.get('pyroxene')['time'])
        self.patch_v_dict['tactical_challenge_coin'].setText(
            f"{self.disp_config.get('tactical_challenge_coin')['name']}: {self.disp_config.get('tactical_challenge_coin')['value']}")
        self.patch_t_dict['tactical_challenge_coin'].setText(
            self.disp_config.get('tactical_challenge_coin')['time'])

        self.patch_v_dict['bounty_coin'].setText(
            f"{self.disp_config.get('bounty_coin')['name']}: {self.disp_config.get('bounty_coin')['value']}")
        self.patch_t_dict['bounty_coin'].setText(self.disp_config.get('bounty_coin')['time'])
        self.patch_v_dict['Keystone-Piece'].setText(
            f"{self.disp_config.get('Keystone-Piece')['name']}: {self.disp_config.get('Keystone-Piece')['value']}")
        self.patch_v_dict['Keystone'].setText(
            f"{self.disp_config.get('Keystone')['name']}: {self.disp_config.get('Keystone')['value']}")

        if self.config.server_mode in ['JP']:
            self.patch_t_dict['_pass'].setText(self.disp_config.get('_pass')['time'])
            self.patch_v_dict['_pass'].setText(
                f"{self.disp_config.get('_pass')['name']}: {self.disp_config.get('_pass')['value']}")

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
            return "-"
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
                self.signal_update.emit()
                time.sleep(interval)

        threading.Thread(target=__interval__, daemon=True).start()


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
        self.transpose = False

        # Reverse lookup dictionary for value conversion
        self.revert_dict = {v: k for k, v in self.convert_dict.items()} if self.convert_dict else None

        # Initialize the table with given settings
        self.reset_table(data_key, unit_config, update_callback, col_headers,
                         row_headers, col_length, transpose, **kwargs)

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
        # self.setFixedHeight(kwargs.get('height', 200))
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
        self.transpose = transpose

        disp_data = self.__transpose__(self.data) if transpose else self.data

        self.setRowCount(len(disp_data))
        self.setColumnCount(len(disp_data[0]))

        # Iterate through the data and create UI components
        for _row, _row_data in enumerate(disp_data):
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
        _row = row if not self.transpose else col
        _col = col if not self.transpose else row
        self.data[_row][_col] = self.revert_dict.get(value, value)
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


class ClickFocusLineEdit(LineEdit):
    """
    Custom LineEdit that does not focus unless clicked
    This is to prevent the LineEdit from stealing focus
    from the parent widget when the user strike a hover
    on the LineEdit. This is useful when the LineEdit is
    used in a TableWidget, and the user wants to click on
    the parent widget to select a row.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.installEventFilter(self)

    def eventFilter(self, a0, a1):
        if a1.type() == QEvent.MouseButtonPress:
            self.setFocus()
        return super().eventFilter(a0, a1)


class BAASSettingCard(ExpandSettingCard):
    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None, parent=None):
        super().__init__(icon, title, content, parent)
        self._adjustViewSize()
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key in [Qt.Key_Up, Qt.Key_Down]:
                return True
        return super().eventFilter(obj, event)


class ColorSvgWidget(QLabel):
    def __init__(self, svg_path, color="#000000", parent=None):
        super().__init__(parent)
        self._svg_path = svg_path
        self._color = QColor(color)
        self._renderer = QSvgRenderer(self._svg_path)
        self.setScaledContents(True)  # 让 pixmap 随 QLabel 尺寸缩放
        self._update_pixmap()

    def setColor(self, color):
        """动态设置颜色"""
        self._color = QColor(color)
        self._update_pixmap()

    def _update_pixmap(self):
        size = self._renderer.defaultSize()
        if not size.isValid():
            size = self.size() if self.size().isValid() else Qt.QSize(100, 100)

        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        self._renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), self._color)
        painter.end()

        self.setPixmap(pixmap)

    def resizeEvent(self, event):
        """在 QLabel 缩放时重新生成图像"""
        self._update_pixmap()
        super().resizeEvent(event)
