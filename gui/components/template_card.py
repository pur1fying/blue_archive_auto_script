# coding:utf-8

from PyQt5.QtCore import pyqtProperty, QPropertyAnimation
from PyQt5.QtGui import QColor
from qfluentwidgets import ExpandSettingCard, MessageBoxBase
from qfluentwidgets import FluentIcon as FIF

from gui.util.translator import baasTranslator as bt

BANNER_IMAGE_DIR = 'gui/assets/banners'

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QRectF


class OutlineLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 20, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        outline_color = QColor("white")
        text_color = QColor("black")

        # 设置文字边框（描边）
        painter.setPen(outline_color)
        x_offset = y_offset = 1  # 边框偏移量
        for dx in (-x_offset, 0, x_offset):
            for dy in (-y_offset, 0, y_offset):
                if dx != 0 or dy != 0:
                    painter.drawText(self.rect().translated(dx, dy), Qt.AlignCenter, self.text())

        # 绘制原文字
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


class DialogSettingBox(MessageBoxBase):
    def __init__(self, parent=None, config=None, layout=None, *_, **kwargs):
        super().__init__(parent)
        setting_name = kwargs.get('setting_name')
        self.config = config
        # self.layout = layout
        frame = QFrame(self)
        layout_wrapper = QVBoxLayout(frame)
        layout_wrapper.setContentsMargins(0, 0, 0, 0)
        layout_wrapper.setSpacing(0)
        layout_wrapper.addWidget(layout)
        layout.setStyleSheet("""
            * {
                font-family: "Microsoft YaHei";
                font-size: 14px;
            }
        """)
        # Check if the layout name contains "shop"
        if 'shop' in setting_name or 'Shop' in setting_name:
            frame.setMinimumWidth(800)
        frame.setLayout(layout_wrapper)
        self.viewLayout.addWidget(frame)


class TemplateSettingCardForClick(QFrame):

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
        self.card_width = 250
        self.card_height = 150

        self.setFixedWidth(self.card_width)
        self.setFixedHeight(self.card_height)
        self.setCursor(Qt.PointingHandCursor)

        # 设置整体布局
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.viewLayout.setSpacing(0)  # 移除布局间距
        self.__initWidget()
        self.set_shadow_effect()

    def __initWidget(self):
        # 设置图片
        self.image_label = QLabel(self)
        pixmap = QPixmap(self.image_path).scaled(self.card_width, int(self.card_height * 0.8),
                                                 Qt.KeepAspectRatioByExpanding)
        rounded_pixmap = self._add_top_rounded_corners(pixmap, 20)
        self.image_label.setPixmap(rounded_pixmap)
        self.image_label.setFixedSize(self.card_width, int(self.card_height * 0.8))
        self.image_label.setAlignment(Qt.AlignTop)

        # 设置标题
        self.title_label = OutlineLabel(self.title, self)
        self.title_label.setFont(QFont("Microsoft YaHei", 15, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)

        # 设置简介
        self.content_label = QLabel(self.content, self)
        self.content_label.setFont(QFont("Microsoft YaHei", 10))
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setWordWrap(True)

        # 添加组件到布局
        self.viewLayout.addWidget(self.image_label)
        self.viewLayout.addWidget(self.title_label)
        self.viewLayout.addWidget(self.content_label)
        self.viewLayout.setAlignment(Qt.AlignTop)

        self.set_default_style()
        # 设置动画
        self.animation = QPropertyAnimation(self, b"back_color")
        self.animation.setDuration(300)  # 动画持续时间 300ms

    def set_default_style(self):
        # 设置卡片的样式
        self.setStyleSheet("""
            QFrame {
                border-radius: 20px;
                background-color: #fff;
            }
            QLabel {
                margin-bottom: 10px;
                color: #333;
                background-color: transparent;
            }
        """)

    def set_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def enterEvent(self, event):
        # 进入时使用动画渐变至 hover 背景色
        self.start_background_animation(QColor("#fff"), QColor("#e0f7fa"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 离开时使用动画渐变回默认背景色
        self.start_background_animation(QColor("#e0f7fa"), QColor("#fff"))
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
                margin-bottom: 10px;
                color: #333;
                background-color: transparent;
            }
        """ % col.name())
        # 应用新的调色板
        self.setPalette(palette)

    back_color = pyqtProperty(QColor, fset=_set_back_color)

    def _add_top_rounded_corners(self, pixmap, radius):
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


class TemplateSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    def __init__(self, title: str = '', content: str = None, parent=None, sub_view=None, config=None, context=None,
                 **_):
        if context is not None:
            title, content = bt.tr(context, title), bt.tr(context, content)
        super().__init__(FIF.CHECKBOX, title, content, parent)
        assert sub_view is not None, 'Sub_view is required'
        self.initiated = False
        self.expand_view = None
        self.sub_view = sub_view
        self.config = config
        self._adjustViewSize()

    def toggleExpand(self):
        if self.initiated:
            super().toggleExpand()
            return
        self.expand_view = self.sub_view.Layout(self, self.config)
        self.__initWidget()
        self.initiated = True
        super().toggleExpand()

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


class SimpleSettingCard(ExpandSettingCard):
    """ Folder list setting card """

    def __init__(self, sub_view, title: str = '', content: str = None, parent=None, config=None, context=None, **_):
        if context is not None:
            title, content = bt.tr(context, title), bt.tr(context, content)
        super().__init__(FIF.CHECKBOX, title, content, parent)
        self._adjustViewSize()
        self.initiated = False
        self.expand_view = None
        self.sub_view = sub_view
        self.config = config

    def toggleExpand(self):
        if self.initiated:
            super().toggleExpand()
            return
        print('expand')
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

