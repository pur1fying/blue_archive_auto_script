# coding:utf-8
import os

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtCore import pyqtProperty, QPropertyAnimation, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from qfluentwidgets import FluentIcon as FIF

from core.utils import delay
from gui.util.config_gui import configGui
from gui.util.customed_ui import OutlineLabel, DialogSettingBox, BAASSettingCard
from gui.util.translator import baasTranslator as bt

BANNER_IMAGE_DIR = 'gui/assets/banners'




class TemplateSettingCardForClick(QFrame):
    COLOR_THEME = {
        'Light': {
            'background': '#ffffff',
            'background_hover': '#e0f7fa',
            'text': '#333333',
            'outline': '#fff'
        },
        'Dark': {
            'background': '#333333',
            'background_hover': '#555555',
            'text': '#fff',
            'outline': '#333333'
        }
    }

    def __init__(self, title: str = '', content: str = '', parent=None,
                 sub_view=None, config=None, context=None, setting_name=''):
        assert config is not None, 'config is required'
        assert sub_view is not None, 'sub_view is required'
        assert context is not None, 'context is required'
        super().__init__(parent=parent)
        self.image_path = f'{BANNER_IMAGE_DIR}/{setting_name}.png'
        self.setting_name = setting_name
        self.title = title
        self.content = content
        self.sub_view = sub_view
        self.config = config
        self.card_display_type = configGui.cardDisplayType.value
        self.card_width = 250
        self.card_height = 150 if self.card_display_type == 'withImage' else 90

        self.setFixedWidth(self.card_width)
        self.setFixedHeight(self.card_height)
        self.setCursor(Qt.PointingHandCursor)

        # 设置整体布局
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.viewLayout.setSpacing(0)  # 移除布局间距
        self.__initWidget()
        self.set_shadow_effect()

        configGui.themeChanged.connect(self._onThemeChange)

    def __initWidget(self):
        # 设置图片
        if self.card_display_type == 'withImage':
            self.image_label = QLabel(self)
            rounded_pixmap = self._create_image()
            self.image_label.setPixmap(rounded_pixmap)

            self.image_label.setFixedSize(self.card_width, int(self.card_height * 0.8))
            self.image_label.setAlignment(Qt.AlignTop)
            self.viewLayout.addWidget(self.image_label)

        # 设置标题
        self.title_label = OutlineLabel(self.title, parent=self,
                                        font_size=15,
                                        font_family='Microsoft YaHei',
                                        font_weight=QFont.Bold)

        self.title_label.setAlignment(Qt.AlignCenter)

        # self.title_label.setContentsMargins(0, 0, 0, 0)

        # 设置简介
        self.content_label = OutlineLabel(self.content, parent=self,
                                          font_size=10,
                                          font_family='Microsoft YaHei',
                                          font_weight=QFont.Normal)

        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setWordWrap(True)

        if self.card_display_type != 'withImage':
            self.title_label.setContentsMargins(0, 20, 0, 0)

        # 添加组件到布局
        self.viewLayout.addWidget(self.title_label)
        self.viewLayout.addWidget(self.content_label)
        self.viewLayout.setAlignment(Qt.AlignTop)

        self.set_default_style()
        # 设置动画
        self.animation = QPropertyAnimation(self, b"back_color")
        self.animation.setDuration(300)  # 动画持续时间 300ms

    def _create_image(self):
        if not os.path.exists(self.image_path):
            self.image_path = f'{BANNER_IMAGE_DIR}/default.png'
        pixmap = QPixmap(self.image_path).scaled(self.card_width, int(self.card_height * 0.8),
                                                 Qt.KeepAspectRatioByExpanding)
        rounded_pixmap = self._add_top_rounded_corners(pixmap, 20)
        return rounded_pixmap

    def set_default_style(self):
        # 设置卡片的样式
        self.setStyleSheet("""
            QFrame {
                border-radius: 20px;
                background-color: %s;
            }
            QLabel {
                background-color: transparent;
            }
        """ % self.COLOR_THEME[configGui.theme.value]['background'])

        if self.card_display_type == 'withImage':
            self.content_label.setStyleSheet("""
                QLabel {
                    margin-bottom: 15px;
                }
            """)

        # 设置标题的样式
        self.title_label.outline_color = QColor(self.COLOR_THEME[configGui.theme.value]['outline'])
        self.title_label.text_color = QColor(self.COLOR_THEME[configGui.theme.value]['text'])
        self.title_label.update()

        # 设置简介的样式
        self.content_label.outline_color = QColor(self.COLOR_THEME[configGui.theme.value]['outline'])
        self.content_label.text_color = QColor(self.COLOR_THEME[configGui.theme.value]['text'])
        self.content_label.update()

    def _onThemeChange(self):
        self.set_default_style()

    def set_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def enterEvent(self, event):
        # 进入时使用动画渐变至 hover 背景色
        self.start_background_animation(
            QColor(self.COLOR_THEME[configGui.theme.value]['background']),
            QColor(self.COLOR_THEME[configGui.theme.value]['background_hover'])
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 离开时使用动画渐变回默认背景色
        self.start_background_animation(
            QColor(self.COLOR_THEME[configGui.theme.value]['background_hover']),
            QColor(self.COLOR_THEME[configGui.theme.value]['background'])
        )
        super().leaveEvent(event)

    def start_background_animation(self, start_color, end_color):
        # 开始背景色动画
        self.animation.stop()  # 停止之前的动画（如有）
        self.animation.setStartValue(start_color)
        self.animation.setEndValue(end_color)
        self.animation.start()

    def _set_back_color(self, col):
        # 获取当前的调色板
        palette = self.palette()
        # 设置前景色（即文本颜色）
        self.setStyleSheet("""
            QFrame {
                border-radius: 20px;
                background-color: %s;
            }
            QLabel {
                background-color: transparent;
            }
        """ % col.name())
        # 应用新的调色板
        self.setPalette(palette)

    back_color = pyqtProperty(QColor, fset=_set_back_color)

    @staticmethod
    def _add_top_rounded_corners(pixmap, radius):
        # 创建一个与pixmap相同大小的QPixmap作为目标图像
        rounded_pixmap = QPixmap(pixmap.size())
        rounded_pixmap.fill(Qt.transparent)

        # 使用QPainter和QPainterPath绘制圆角效果
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()

        # 定义圆角矩形的路径，只在顶部两个角有圆角
        rect = QRectF(0, 0, pixmap.width(), pixmap.height())
        path.moveTo(radius, 0)
        path.arcTo(QRectF(0, 0, 2 * radius, 2 * radius), 90, 90)
        path.lineTo(0, rect.height())
        path.lineTo(rect.width(), rect.height())
        path.lineTo(rect.width(), radius)
        path.arcTo(QRectF(rect.width() - 2 * radius, 0, 2 * radius, 2 * radius), 0, 90)
        path.lineTo(radius, 0)

        # 填充路径并将图像绘制到目标pixmap上
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return rounded_pixmap

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._trigger_expand()

    def _trigger_expand(self):
        # 展开子视图
        pop_layout = self.sub_view.Layout(self, self.config)
        rename_dialog = DialogSettingBox(self.config.get_window(), self.config, pop_layout,
                                         setting_name=self.setting_name)
        if not rename_dialog.exec_(): return


class TemplateSettingCard(BAASSettingCard):
    onToggleChangeSignal = pyqtSignal()

    def __init__(self, title: str = '', content: str = None, parent=None, sub_view=None, config=None, context=None,
                 **kwargs):
        if context is not None:
            title, content = bt.tr(context, title), bt.tr(context, content)
        super().__init__(FIF.CHECKBOX, title, content, parent)
        assert sub_view is not None, 'Sub_view is required'
        self.initiated = False
        self.expand_view = None
        self.sub_view = sub_view
        self.config = config
        self.kwargs = kwargs
        self._adjustViewSize()

    def toggleExpand(self):
        self.__async_emit_toggle_change_signal()
        if self.initiated:
            super().toggleExpand()
            return
        if list(self.kwargs.keys())[0] == 'phase':
            self.expand_view = self.sub_view.Layout(self, self.config, **self.kwargs)
        else:
            self.expand_view = self.sub_view.Layout(self, self.config)
        self.__initWidget()
        self.initiated = True
        super().toggleExpand()

    @delay(0.2)
    def __async_emit_toggle_change_signal(self):
        self.onToggleChangeSignal.emit()

    def __initWidget(self):
        # Add widgets to layout
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        # Initialize layout
        if self.expand_view is not None:
            self.viewLayout.addWidget(self.expand_view)
            self.expand_view.show()
        else:
            self.setExpand(False)
            self.card.expandButton.hide()
            self.card.setContentsMargins(0, 0, 30, 0)
        self._adjustViewSize()


class SimpleSettingCard(BAASSettingCard):
    """ Folder list setting card """

    def __init__(self, sub_view, title: str = '', content: str = None, parent=None, config=None, context=None,
                 **kwargs):
        if context is not None:
            title, content = bt.tr(context, title), bt.tr(context, content)
        super().__init__(FIF.CHECKBOX, title, content, parent)
        self._adjustViewSize()
        self.initiated = False
        self.expand_view = None
        self.sub_view = sub_view
        self.config = config
        self.kwargs = kwargs

    def toggleExpand(self):
        if self.initiated:
            super().toggleExpand()
            return
        if self.kwargs and list(self.kwargs.keys())[0] == 'phase':
            self.expand_view = self.sub_view.Layout(self, self.config, **self.kwargs)
        else:
            self.expand_view = self.sub_view.Layout(self, self.config)
        self.__initWidget()
        self.initiated = True
        super().toggleExpand()

    def __initWidget(self):
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        # Initialize layout
        self.viewLayout.addWidget(self.expand_view)
        self.expand_view.show()
        self._adjustViewSize()
