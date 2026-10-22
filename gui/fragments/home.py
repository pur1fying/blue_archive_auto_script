import html
import json
import sys
import time
import traceback
from datetime import datetime
from hashlib import md5
from json import JSONDecodeError
from random import random
from typing import Callable, Dict, List

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QMimeData, QPoint, QEvent, QRect, QSize
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QApplication,
    QLayout,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    TextEdit,
    SwitchButton,
    IndicatorPosition,
    PushButton,
    PrimaryPushButton,
    PrimaryPushSettingCard,
    SubtitleLabel,
)

from core.notification import notify
from gui.util.customized_ui import FuncLabel, ViewportCappedFragment, ViewportCappedVBoxLayout
from gui.util.translator import baasTranslator as bt
from window import Window

try:
    from gui.components.expand.tool_style import (
        apply_theme_to_labels,
        connect_theme_refresh,
        is_dark,
        safe_connect_theme,
        themed_card_bg,
        themed_input_border,
        themed_note_bg,
        themed_text,
    )
except Exception:  # pragma: no cover
    apply_theme_to_labels = connect_theme_refresh = None
    safe_connect_theme = None
    is_dark = lambda: False
    themed_card_bg = lambda: "#34373d"
    themed_input_border = lambda: "rgba(80,120,170,70)"
    themed_note_bg = lambda: "#FFFFFF"
    themed_text = lambda: "#333333"

if sys.platform == "win32":
    from gui.util.hotkey_manager import GlobalHotkeyManager, HotkeyInputDialog

    _Callback = Callable[[], None]

MAIN_BANNER = 'gui/assets/banner_home_bg.png'
HUMAN_TAKE_OVER_MESSAGE = "BAAS Exited, Reason : Human Take Over"

DEFAULT_HOME_ORDER = [
    "banner",
    "title",
    "below_title",
    "startup",
    "below_startup",
    "log",
]

HOME_BLOCK_MIME = "application/x-baas-home-block"


class HomeFlowLayout(QLayout):
    """主页插件槽位容器：卡片从左到右排，一行放不下自动换行。

    审计修复：原实现是纵向堆叠，与设计意图「从左到右，空间不足换行」不符。
    """

    def __init__(self, parent=None, hspacing=6, vspacing=6):
        super().__init__(parent)
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._items = []
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        # 先按行分组（遇换行断行），再每行内按行高垂直居中，
        # 否则高低不一的卡片（囤体含开关格 vs 单按钮）顶端对齐显得靠上。
        x, y = eff.x(), eff.y()
        line = []  # [(item, hint, expand), ...]
        line_h = 0
        rows = []  # [(y, line_h, [(item, hint, expand)])]
        for item in self._items:
            w = item.widget()
            if w is None or w.isHidden():
                continue
            hint = item.sizeHint()
            # 水平铺满的子项（如资产条 AssetsWidget 用 FlowLayout，
            # expandingDirections=0 且 sizeHint=单格宽）：给它整行宽度，
            # 否则 HomeFlowLayout 只给单格宽 → 内部 FlowLayout 把货币格换行成纵向。
            expand = False
            try:
                if w.sizePolicy().horizontalPolicy() == QSizePolicy.Expanding:
                    expand = True
                    # 高度用该宽度下的真实高度（FlowLayout.heightForWidth），
                    # 而非 sizeHint（= minimumSize = 单格高，偏小）；
                    # 这样资产条横向排开后高度紧凑，不撑出多余空白。
                    row_h = hint.height()
                    try:
                        wlay = w.layout()
                        if wlay is not None and getattr(wlay, "hasHeightForWidth", None):
                            if wlay.hasHeightForWidth():
                                _h = wlay.heightForWidth(eff.width())
                                if _h and _h > 0:
                                    row_h = _h
                    except Exception:
                        pass
                    hint = QSize(eff.width(), row_h)
            except Exception:
                pass
            if x + hint.width() > eff.right() and line_h > 0:
                rows.append((y, line_h, line))
                x = eff.x()
                y += line_h + self._vspacing
                line_h = 0
                line = []
            # 水平铺满项独占一行（放不下就单独换行占满）
            if expand and line:
                rows.append((y, line_h, line))
                x = eff.x()
                y += line_h + self._vspacing
                line_h = 0
                line = []
            line.append((item, hint, expand))
            x += hint.width() + self._hspacing
            line_h = max(line_h, hint.height())
        if line:
            rows.append((y, line_h, line))
        for (ry, rline_h, ritems) in rows:
            cx = eff.x()
            for item, hint, expand in ritems:
                if not test_only:
                    # 垂直居中：矮卡片在行高内向下偏移
                    off = (rline_h - hint.height()) // 2 if rline_h > hint.height() else 0
                    item.setGeometry(QRect(QPoint(cx, ry + off), hint))
                cx += hint.width() + self._hspacing
        if rows:
            last_y, last_h, _ = rows[-1]
            return last_y + last_h - rect.y() + m.bottom()
        return y - rect.y() + m.bottom()


class _HomeBlockWrap(QFrame):
    """可视化编辑壳：保留原控件外观，标题条可拖拽到目标位置。"""

    moveRequested = pyqtSignal(str, int)  # key, delta（上/下备用）
    dragStarted = pyqtSignal(str)

    def __init__(self, key: str, title: str, inner: QWidget, home: "HomeFragment"):
        super().__init__(home)
        self._is_home_block_wrap = True
        self._key = key
        self._home = home
        self._inner = inner
        self.setObjectName("homeBlockWrap")
        self.setProperty("homeBlockKey", key)
        self.setAcceptDrops(True)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(4, 4, 4, 4)
        vl.setSpacing(4)

        bar = QFrame(self)
        bar.setObjectName("homeEditBar")
        bar.setCursor(Qt.OpenHandCursor)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(8, 4, 8, 4)
        hl.setSpacing(6)
        grip = QLabel("⋮⋮", bar)
        grip.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:14px;font-weight:700;'
        )
        hl.addWidget(grip, 0)
        lab = QLabel(title, bar)
        lab.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:600;'
        )
        hl.addWidget(lab, 0)
        hl.addStretch(1)
        tip = QLabel("拖到目标板块上松开", bar)
        tip.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:11px;'
        )
        hl.addWidget(tip, 0)
        btn_up = PushButton("上移", bar)
        btn_dn = PushButton("下移", bar)
        try:
            # 高度 26 会吞掉文字下缘：放宽到 30 并收紧内边距
            btn_up.setFixedHeight(30)
            btn_dn.setFixedHeight(30)
            btn_up.setMaximumWidth(60)
            btn_dn.setMaximumWidth(60)
            btn_up.setStyleSheet("PushButton{padding:2px 6px;}")
            btn_dn.setStyleSheet("PushButton{padding:2px 6px;}")
        except Exception:
            pass
        btn_up.clicked.connect(lambda *_: self.moveRequested.emit(self._key, -1))
        btn_dn.clicked.connect(lambda *_: self.moveRequested.emit(self._key, 1))
        hl.addWidget(btn_up, 0)
        hl.addWidget(btn_dn, 0)
        vl.addWidget(bar, 0)

        try:
            inner.setParent(self)
        except Exception:
            pass
        vl.addWidget(inner, 1 if key == "log" else 0)

        self._edit_bar = bar
        self._grip = grip
        self._lab = lab
        self._tip = tip
        self._drag_start = None
        bar.installEventFilter(self)
        self.installEventFilter(self)
        self._refresh()
        # 中心引擎统一重刷（切主题时板块名/提示/描边条全现算）
        try:
            from gui.components.expand.tool_style import register_theme_managed

            register_theme_managed(self, self._refresh)
        except Exception:
            pass

    def _refresh(self):
        """主题感知刷新：编辑壳描边/标题条/板块名/提示文字随深浅色。"""
        try:
            dark = bool(is_dark())
            dashed = "rgba(120,170,230,150)" if dark else "rgba(50,110,200,110)"
            bg = "rgba(255,255,255,12)" if dark else "rgba(255,255,255,18)"
            self.setStyleSheet(
                "QFrame#homeBlockWrap{"
                f"border:1px dashed {dashed};border-radius:8px;"
                f"background:{bg};}}"
                "QFrame#homeBlockWrap[dropHover='true']{"
                "border:2px solid #1F9D55;background:rgba(31,157,85,28);}"
            )
            self._edit_bar.setStyleSheet(
                f"QFrame#homeEditBar{{background:{themed_note_bg()};"
                f"border:1px solid {themed_input_border()};border-radius:6px;}}"
            )
            txt = themed_text()
            muted = "rgba(216,220,228,172)" if dark else "#456789"
            self._grip.setStyleSheet(
                'font-family:"Microsoft YaHei";font-size:14px;font-weight:700;'
                f"color:{txt};"
            )
            self._lab.setStyleSheet(
                'font-family:"Microsoft YaHei";font-size:12px;font-weight:600;'
                f"color:{txt};"
            )
            self._tip.setStyleSheet(
                'font-family:"Microsoft YaHei";font-size:11px;'
                f"color:{muted};"
            )
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            et = event.type()
            if obj is self._edit_bar:
                if et == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self._drag_start = event.pos()
                    self._edit_bar.setCursor(Qt.ClosedHandCursor)
                elif et == QEvent.MouseMove and self._drag_start is not None:
                    if (event.pos() - self._drag_start).manhattanLength() >= QApplication.startDragDistance():
                        self._start_drag()
                        self._drag_start = None
                elif et == QEvent.MouseButtonRelease:
                    self._drag_start = None
                    self._edit_bar.setCursor(Qt.OpenHandCursor)
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _start_drag(self):
        try:
            self.dragStarted.emit(self._key)
            drag = QDrag(self)
            md = QMimeData()
            md.setData(HOME_BLOCK_MIME, self._key.encode("utf-8"))
            md.setText(self._key)
            drag.setMimeData(md)
            # 预览：原板块缩略
            pix = self.grab()
            if not pix.isNull():
                if pix.width() > 360:
                    pix = pix.scaledToWidth(360, Qt.SmoothTransformation)
                drag.setPixmap(pix)
                drag.setHotSpot(QPoint(min(40, pix.width() // 4), 12))
            drag.exec_(Qt.MoveAction)
        except Exception as e:
            print("[home] drag failed:", e)

    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md is not None and (md.hasFormat(HOME_BLOCK_MIME) or md.hasText()):
            event.acceptProposedAction()
            self.setProperty("dropHover", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dropHover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.setProperty("dropHover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        md = event.mimeData()
        src = ""
        try:
            if md.hasFormat(HOME_BLOCK_MIME):
                src = bytes(md.data(HOME_BLOCK_MIME)).decode("utf-8")
            elif md.hasText():
                src = md.text().strip()
        except Exception:
            src = ""
        if src and self._home is not None:
            try:
                self._home._drag_key = src
                self._home._drop_block_at(self._key)
            except Exception as e:
                print("[home] drop failed:", e)
        event.acceptProposedAction()


class HomeFragment(ViewportCappedFragment, QFrame):
    """主页：固定骨架 + 插件槽位宿主。"""

    updateButtonState = pyqtSignal(bool)
    thenSignal = pyqtSignal(str)
    exitSignal = pyqtSignal(int)

    def __init__(self, parent: Window = None, config=None):
        super().__init__(parent=parent)
        self.once = True
        self.event_map = {}
        self.config = config
        self.log_entries = None
        self.crt_line_index = -1
        # 页面顶层布局必须钳制 totalSizeHint（见 ViewportCappedVBoxLayout 文档），
        # 否则主页插件槽位内容变高后，首次移动窗口会被原生层一次性拉高
        self.expandLayout = ViewportCappedVBoxLayout(self)
        self._slot_hosts = {}
        self._home_plugin_widgets = []
        # 栏1/栏2：用户在工具页设置栏选择的主页位置变化时，即时重挂插件条
        try:
            from gui.components.expand.tool_style import on_home_bar_slot_change
            on_home_bar_slot_change(lambda *_a, **_k: self.refresh_home_plugins())
        except Exception:
            pass

        self.info_box = QFrame(self)
        self.info_box.setFixedHeight(45)
        self.infoLayout = QHBoxLayout(self.info_box)

        title = self.tr("蔚蓝档案自动脚本") + ' {name}'
        self.banner_visible = self.config.get('bannerVisibility')
        self.label = SubtitleLabel(self)
        config.inject(self.label, title)
        self.info = SubtitleLabel(self.tr('无任务'), self)

        self.infoLayout.addWidget(self.label, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        self.infoLayout.addWidget(self.info, 0, Qt.AlignRight)

        self.banner = FuncLabel(self)
        self.banner.setFixedHeight(200)
        self.banner.setMaximumHeight(200)
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)
        self.banner.setVisible(self.banner_visible)

        self.startup_card = PrimaryPushSettingCard(
            self.tr('启动'),
            FIF.CARE_RIGHT_SOLID,
            self.tr('档案，启动'),
            self.tr('开始你的档案之旅') + ' - ' + self.tr("完成后") + f' {self.config.get("then")}',
            self
        )
        self.startup_card.setContentsMargins(0, 0, 0, 0)

        self.logger_box = TextEdit(self)
        self.logger_box.setReadOnly(True)

        for slot in ("below_title", "below_startup"):
            host = QFrame(self)
            host.setObjectName("homeSlot_%s" % slot)
            # 横向流式：卡片从左到右，空间不足换行（不再是纵向堆叠）
            HomeFlowLayout(host, hspacing=6, vspacing=6)
            self._slot_hosts[slot] = host

        self.__initLayout()
        self._mount_home_plugins()
        self.__connectSignalToSlot()

        self.main_thread_attach = MainThread(self.config)
        self.config.set_main_thread(self.main_thread_attach)
        self.main_thread_attach.button_signal.connect(self.set_button_state)
        self.main_thread_attach.logger_signal.connect(self.on_log_received)
        self.main_thread_attach.update_signal.connect(self.call_update)
        self.main_thread_attach.exit_signal.connect(lambda x: sys.exit(x))

        config.add_signal('update_signal', self.main_thread_attach.update_signal)
        self._hotkey_container = None
        if sys.platform == "win32":
            self.hk_callbacks = {}
            self.hk_mgr = GlobalHotkeyManager(self)
            self.hotkey_widgets = {}
            self._init_hotkey(
                key="hotkey_run",
                default="Ctrl+Shift+R",
                callback=self.startup_card.button.click
            )

            ht_k = "hotkey_run"
            self.hotkey_desc_label = QLabel(self.tr("启停快捷键"))
            self.hotkey_push_button = PushButton(text=self.config.get(ht_k, 'Ctrl+Shift+R'))
            font = self.hotkey_push_button.font()
            font.setBold(True)
            self.hotkey_push_button.setFont(font)

            hotkey_layout = QHBoxLayout()
            hotkey_layout.setContentsMargins(0, 0, 0, 0)
            hotkey_layout.setSpacing(6)
            hotkey_layout.addWidget(self.hotkey_desc_label)
            hotkey_layout.addWidget(self.hotkey_push_button)

            container = QWidget()
            container.setObjectName("homeHotkeyContainer")
            container.setLayout(hotkey_layout)
            self._hotkey_container = container

            # 先挂快捷键，再挂左侧控件（顺序：显示资产 | 顺序调换 | 启停快捷键 | 启动）
            self.startup_card.hBoxLayout.insertWidget(5, container, 0, Qt.AlignRight)
            self.hotkey_widgets[ht_k] = {
                "hotkey_push_button": self.hotkey_push_button,
                "callback": self.hk_callbacks.get(ht_k, lambda: None)
            }
            self.hotkey_push_button.clicked.connect(lambda _: self._change_hotkey(ht_k))

        # 必须在快捷键创建之后挂载，才能插到「启停快捷键」左边
        try:
            self._mount_startup_home_controls()
        except Exception as e:
            print("[home] mount startup controls failed:", e)

        self.startup_card.clicked.connect(self._start_clicked)
        self.object_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self.setObjectName(f"{self.object_name}.HomeFragment")
        if self.config.get('autostart'):
            self.startup_card.button.click()

        # 深色模式适配
        if apply_theme_to_labels is not None:
            apply_theme_to_labels(self)
            connect_theme_refresh(self)
        if safe_connect_theme is not None:
            safe_connect_theme(self, self._refresh_home_theme)

    def _refresh_home_theme(self):
        """切主题后刷新主页编辑栏/应用栏/编辑壳/栏位单选。"""
        try:
            from PyQt5.QtWidgets import QFrame as _QF
            for w in self.findChildren(_QF):
                try:
                    name = w.objectName()
                    if name == "homeEditBar":
                        w.setStyleSheet(
                            f"QFrame#homeEditBar{{background:{themed_note_bg()};"
                            f"border:1px solid {themed_input_border()};border-radius:6px;}}"
                        )
                    elif name == "homeEditApplyBar":
                        w.setStyleSheet(
                            f"QFrame#homeEditApplyBar{{background:{themed_card_bg()};"
                            f"border-radius:8px;border:1px solid {themed_input_border()};}}"
                        )
                    elif name in ("homeBarSlotCell", "preferClearCell"):
                        # 栏位单选/主页拦截格：统一走现算 _refresh
                        fn = getattr(w, "_refresh", None)
                        if callable(fn):
                            fn()
                except Exception:
                    pass
        except Exception:
            pass
        # 编辑壳（板块名/提示文字/虚线框）也统一重刷
        try:
            for w in self.findChildren(_HomeBlockWrap):
                fn = getattr(w, "_refresh", None)
                if callable(fn):
                    fn()
        except Exception:
            pass

    def _layout_order(self):
        # 编辑态优先用现场顺序（未点应用前不写配置）
        live = getattr(self, "_edit_order_live", None)
        if getattr(self, "_home_edit_mode", False) and isinstance(live, list) and live:
            return list(live)
        try:
            raw = self._cfg_raw("home_layout_order", None)
            if raw is None or str(raw).strip() == "":
                if hasattr(self.config, "get"):
                    raw = self.config.get("home_layout_order", "")
            raw = str(raw or "").strip()
        except Exception:
            raw = ""
        if not raw:
            return list(DEFAULT_HOME_ORDER)
        # 旧配置里的独立 assets 槽已并入 below_startup，丢弃
        parts = [p.strip() for p in raw.split(",") if p.strip() and p.strip() != "assets"]
        for k in DEFAULT_HOME_ORDER:
            if k not in parts:
                parts.append(k)
        # 去掉未知键
        known = set(DEFAULT_HOME_ORDER)
        parts = [p for p in parts if p in known]
        return parts

    def __initLayout(self):
        self.expandLayout.setSpacing(10)
        self._block_wraps = {}
        self._home_edit_mode = False
        self._edit_apply_bar = None
        self._drag_key = None
        self._edit_order_backup = None
        self._edit_order_live = None
        try:
            if hasattr(self.config, "get"):
                self._home_edit_mode = bool(self.config.get("tool_assets_home_edit", False))
        except Exception:
            self._home_edit_mode = False
        if self._home_edit_mode:
            # 残留编辑态：按当前配置作备份，避免空白
            try:
                self._edit_order_backup = list(self._layout_order())
                self._edit_order_live = list(self._edit_order_backup)
            except Exception:
                self._edit_order_backup = list(DEFAULT_HOME_ORDER)
                self._edit_order_live = list(DEFAULT_HOME_ORDER)
        self._rebuild_home_layout()
        self.setLayout(self.expandLayout)
        # 启停栏控件在快捷键创建之后挂载（见 __init__ 尾部），这里不提前挂
        # 若配置残留编辑态，进入时补一圈工具条
        if self._home_edit_mode:
            try:
                self._show_edit_apply_bar(True)
            except Exception:
                pass

    def _block_map(self):
        # banner 始终参与排序；不可见时在编辑态也保留占位便于拖
        # 资产条不再单独占一块，归「启停下插件」槽（由插件 manifest.home.slot 注册）
        return {
            "banner": self.banner,
            "title": self.info_box,
            "below_title": self._slot_hosts.get("below_title"),
            "startup": self.startup_card,
            "below_startup": self._slot_hosts.get("below_startup"),
            "log": self.logger_box,
        }

    def _block_title(self, key: str) -> str:
        return {
            "banner": "横幅",
            "title": "标题",
            "below_title": "标题下插件",
            "startup": "启停栏",
            "below_startup": "启停下插件",
            "log": "运行日志",
        }.get(key, key)

    def _cfg_raw(self, key, default=None):
        """读配置原值：优先 dataclass/挂载字段，避开翻译层干扰。"""
        try:
            c = self.config
            if c is None:
                return default
            # ConfigSet.config 上的真实字段（含插件 setattr 的 extras）
            inner = getattr(c, "config", None)
            if inner is not None:
                try:
                    if hasattr(inner, key):
                        return getattr(inner, key)
                    # dataclass 可能没声明，但 __dict__ 里有
                    d = getattr(inner, "__dict__", None)
                    if isinstance(d, dict) and key in d:
                        return d[key]
                except Exception:
                    pass
            if hasattr(c, key) and key not in ("config", "get", "set", "save"):
                try:
                    return getattr(c, key)
                except Exception:
                    pass
            # 最后才走 get；bool 已被 ConfigSet.get 原样返回
            if hasattr(c, "get"):
                return c.get(key, default)
        except Exception:
            pass
        return default

    def _cfg_bool(self, key, default=False):
        try:
            v = self._cfg_raw(key, default)
            if isinstance(v, bool):
                return v
            if v is None:
                return default
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return bool(v)
            s = str(v).strip().lower()
            if s in ("1", "true", "yes", "on", "是"):
                return True
            if s in ("0", "false", "no", "off", "否", ""):
                return False
            return bool(v)
        except Exception:
            pass
        return default

    def _cfg_set(self, key, value):
        """强制写入底层字段并 save；插件键 / dataclass 键都能落盘。"""
        c = self.config
        if c is None:
            return
        try:
            if hasattr(c, "set"):
                c.set(key, value)
        except Exception as e:
            print("[home] cfg set failed:", key, e)
        # 再保险：直接挂到底层 + save（防止 set 路径异常）
        try:
            inner = getattr(c, "config", None)
            if inner is not None:
                try:
                    setattr(inner, key, value)
                except Exception:
                    try:
                        object.__setattr__(inner, key, value)
                    except Exception:
                        pass
            if hasattr(c, "save"):
                c.save()
        except Exception as e:
            print("[home] cfg set fallback failed:", key, e)

    def _assets_visible_from_config(self) -> bool:
        """显示资产：优先 assetsVisibility 原值；没有再看 tool_assets_enabled。"""
        raw = self._cfg_raw("assetsVisibility", None)
        if raw is not None and str(raw).strip() != "":
            return self._cfg_bool("assetsVisibility", True)
        return self._cfg_bool("tool_assets_enabled", True)

    def _mount_startup_home_controls(self):
        """启停栏：显示资产 + 顺序调换 固定在「启停快捷键」左边。"""
        # —— 显示资产：上文字下开关 ——
        host = QWidget(self.startup_card)
        vl = QVBoxLayout(host)
        vl.setContentsMargins(4, 0, 4, 0)
        vl.setSpacing(2)
        vl.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lab_a = QLabel("显示资产", host)
        lab_a.setAlignment(Qt.AlignHCenter)
        lab_a.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:700;color:#234;'
        )
        vl.addWidget(lab_a, 0, Qt.AlignHCenter)
        try:
            self.sw_assets_home = SwitchButton(host, IndicatorPosition.RIGHT)
        except Exception:
            self.sw_assets_home = SwitchButton(host)
        try:
            self.sw_assets_home.setOnText("开")
            self.sw_assets_home.setOffText("关")
        except Exception:
            pass
        on = self._assets_visible_from_config()
        try:
            self.sw_assets_home.blockSignals(True)
            self.sw_assets_home.setChecked(bool(on))
        finally:
            try:
                self.sw_assets_home.blockSignals(False)
            except Exception:
                pass
        self.sw_assets_home.checkedChanged.connect(self._on_assets_home_toggle)
        vl.addWidget(self.sw_assets_home, 0, Qt.AlignHCenter)
        # 入口显隐：由「主页编辑」工具顶栏「资产主页显示」控制
        switch_entry = self._cfg_bool("tool_assets_home_switch_entry", True)
        host.setVisible(bool(switch_entry))

        # —— 顺序调换：仅当「编辑主页显示」入口开时出现 ——
        self.btn_home_edit = PushButton("顺序调换", self.startup_card)
        try:
            self.btn_home_edit.setFixedHeight(28)
            self.btn_home_edit.setToolTip("进入主页可视化编辑：拖拽板块到目标位置，点应用结束；离开未应用则取消")
        except Exception:
            pass
        self.btn_home_edit.clicked.connect(lambda *_: self.enter_home_edit_mode())
        edit_on = self._cfg_bool("tool_assets_home_edit_entry", False)
        self.btn_home_edit.setVisible(bool(edit_on))

        # 组合：显示资产 | 顺序调换 —— 整组插到启停快捷键左边
        group = QWidget(self.startup_card)
        group.setObjectName("homeStartupLeftControls")
        gl = QHBoxLayout(group)
        gl.setContentsMargins(0, 0, 8, 0)
        gl.setSpacing(8)
        gl.setAlignment(Qt.AlignVCenter)
        gl.addWidget(host, 0, Qt.AlignVCenter)
        gl.addWidget(self.btn_home_edit, 0, Qt.AlignVCenter)

        try:
            lay = self.startup_card.hBoxLayout
            insert_at = None
            hot = getattr(self, "_hotkey_container", None)
            if hot is not None:
                for i in range(lay.count()):
                    it = lay.itemAt(i)
                    if it is not None and it.widget() is hot:
                        insert_at = i
                        break
            if insert_at is None:
                # 无快捷键（非 win）：插到启动按钮前
                insert_at = max(0, lay.count() - 1)
            lay.insertWidget(insert_at, group, 0, Qt.AlignRight | Qt.AlignVCenter)
        except Exception:
            try:
                self.startup_card.hBoxLayout.addWidget(group, 0, Qt.AlignRight)
            except Exception:
                pass
        self._startup_home_host = host
        self._startup_left_group = group
        self._sync_home_edit_entry_btn()
        self._sync_home_assets_switch_entry()

    def _assets_plugin_enabled(self) -> bool:
        """资产与主页编辑插件是否可用（非启用或删除=启停栏两控件都不出现）。

        统一走 registry.tool_available——删除的插件与 UI 皮肤无关，
        主页贡献整个消失，不存在"还在但没反应"的半死态。
        """
        try:
            from module.tools.registry import tool_available

            return bool(tool_available("assets_display"))
        except Exception:
            return True

    def _sync_home_edit_entry_btn(self):
        """主页编辑按钮入口 → 启停栏是否出现「顺序调换」。"""
        try:
            on = self._cfg_bool("tool_assets_home_edit_entry", False) and self._assets_plugin_enabled()
            if getattr(self, "btn_home_edit", None) is not None:
                self.btn_home_edit.setVisible(bool(on))
        except Exception:
            pass

    def _sync_home_assets_switch_entry(self):
        """显示资产开关入口 → 启停栏是否出现「显示资产」。"""
        try:
            on = self._cfg_bool("tool_assets_home_switch_entry", True) and self._assets_plugin_enabled()
            host = getattr(self, "_startup_home_host", None)
            if host is not None:
                host.setVisible(bool(on))
        except Exception:
            pass

    def set_home_edit_entry_visible(self, on: bool):
        """只同步 UI 显隐；配置由工具页开关写入，这里不再二次 set。"""
        try:
            show = bool(on) and self._assets_plugin_enabled()
            if getattr(self, "btn_home_edit", None) is not None:
                self.btn_home_edit.setVisible(bool(show))
        except Exception:
            pass

    def set_home_assets_switch_entry_visible(self, on: bool):
        """只同步 UI 显隐；配置由工具页开关写入，这里不再二次 set。"""
        try:
            host = getattr(self, "_startup_home_host", None)
            if host is not None:
                host.setVisible(bool(on))
        except Exception:
            pass

    def _on_assets_home_toggle(self, checked: bool):
        checked = bool(checked)
        # 两键同步，保证重开后读到的仍是用户选择
        self._cfg_set("assetsVisibility", checked)
        self._cfg_set("tool_assets_enabled", checked)
        # 再保险写一次底层字段
        try:
            c = self.config
            inner = getattr(c, "config", None) if c is not None else None
            if inner is not None:
                setattr(inner, "assetsVisibility", checked)
                setattr(inner, "tool_assets_enabled", checked)
            if c is not None and hasattr(c, "save"):
                c.save()
        except Exception as e:
            print("[home] assets persist failed:", e)
        try:
            if getattr(self, "sw_assets_home", None) is not None:
                if bool(self.sw_assets_home.isChecked()) != checked:
                    self.sw_assets_home.blockSignals(True)
                    self.sw_assets_home.setChecked(checked)
                    self.sw_assets_home.blockSignals(False)
        except Exception:
            pass
        try:
            self.refresh_home_plugins()
        except Exception as e:
            print("[home] refresh home plugins failed:", e)

    def _make_block_wrap(self, key: str, inner) -> QFrame:
        wrap = _HomeBlockWrap(key, self._block_title(key), inner, self)
        wrap.moveRequested.connect(lambda k, d: self._move_home_block(k, delta=d))
        wrap.dragStarted.connect(self._on_block_drag_started)
        return wrap

    def _detach_layout_keep_widgets(self):
        """清空 expandLayout，但绝不 deleteLater 业务控件。"""
        lay = self.expandLayout
        kept = []
        while lay.count():
            it = lay.takeAt(0)
            w = it.widget()
            if w is None:
                continue
            inner = getattr(w, "_inner", None)
            is_wrap = bool(getattr(w, "_is_home_block_wrap", False)) or inner is not None
            if is_wrap and inner is not None:
                try:
                    # 先从 wrap 布局摘掉 inner，再挂回 HomeFragment
                    wlay = w.layout()
                    if wlay is not None:
                        wlay.removeWidget(inner)
                    inner.setParent(self)
                    inner.show()
                except Exception:
                    try:
                        inner.setParent(self)
                    except Exception:
                        pass
                try:
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
                except Exception:
                    pass
            else:
                # 业务块本身：只脱离布局，保留实例
                try:
                    w.setParent(self)
                except Exception:
                    pass
                kept.append(w)
        return kept

    def _rebuild_home_layout(self):
        self._detach_layout_keep_widgets()
        self._block_wraps = {}
        lay = self.expandLayout
        order = self._layout_order()
        bmap = self._block_map()
        edit = bool(getattr(self, "_home_edit_mode", False))
        for key in order:
            inner = bmap.get(key)
            if inner is None:
                continue
            # banner 在非编辑且关闭显示时隐藏
            if key == "banner":
                try:
                    if not edit:
                        inner.setVisible(bool(getattr(self, "banner_visible", False)))
                    else:
                        # 编辑态始终可见，便于拖拽看到原样
                        inner.setVisible(True)
                except Exception:
                    pass
            if edit:
                wrap = self._make_block_wrap(key, inner)
                self._block_wraps[key] = wrap
                if key == "log":
                    lay.addWidget(wrap, 1)
                else:
                    lay.addWidget(wrap, 0)
            else:
                try:
                    inner.setParent(self)
                except Exception:
                    pass
                if key == "log":
                    lay.addWidget(inner, 1)
                else:
                    lay.addWidget(inner, 0)
        # hide empty plugin hosts（编辑态仍显示空槽便于占位感知）
        for slot, host in self._slot_hosts.items():
            try:
                l2 = host.layout()
                empty = l2 is None or l2.count() == 0
                if edit:
                    host.setVisible(True)
                    if empty:
                        host.setMinimumHeight(36)
                else:
                    host.setMinimumHeight(0)
                    host.setVisible(not empty)
            except Exception:
                pass
        self._show_edit_apply_bar(edit)

    def _show_edit_apply_bar(self, on: bool):
        bar = getattr(self, "_edit_apply_bar", None)
        if not on:
            if bar is not None:
                try:
                    bar.hide()
                    bar.setParent(None)
                    bar.deleteLater()
                except Exception:
                    pass
                self._edit_apply_bar = None
            return
        if bar is None:
            bar = QFrame(self)
            bar.setObjectName("homeEditApplyBar")
            bar.setStyleSheet(
                f"QFrame#homeEditApplyBar{{background:{themed_card_bg()};"
                f"border-radius:8px;border:1px solid {themed_input_border()};}}"
            )
            hl = QHBoxLayout(bar)
            hl.setContentsMargins(10, 6, 10, 6)
            hl.setSpacing(10)
            tip = QLabel("主页编辑中：按住板块标题条拖到目标位置", bar)
            tip.setStyleSheet(
                f'font-family:"Microsoft YaHei";font-size:12px;color:{themed_text()};'
            )
            hl.addWidget(tip, 1)
            btn = PrimaryPushButton("应用", bar)
            try:
                btn.setFixedHeight(30)
                btn.setMinimumWidth(72)
            except Exception:
                pass
            btn.clicked.connect(self.apply_home_edit_mode)
            hl.addWidget(btn, 0)
            self._edit_apply_bar = bar
        try:
            self._edit_apply_bar.setParent(self)
            self._edit_apply_bar.adjustSize()
            self._edit_apply_bar.raise_()
            self._edit_apply_bar.show()
            self._place_edit_apply_bar()
        except Exception:
            pass

    def _place_edit_apply_bar(self):
        bar = getattr(self, "_edit_apply_bar", None)
        if bar is None or not bar.isVisible():
            return
        try:
            bar.adjustSize()
            m = 12
            x = max(m, self.width() - bar.width() - m)
            y = m
            bar.move(x, y)
            bar.raise_()
        except Exception:
            pass

    def resizeEvent(self, event):
        # 高度基准取窗口宽度而非横幅当前宽度：后者是布局反馈量，
        # 显示前的瞬时宽度会把主窗口最小高度钉高，首次移动窗口时
        # 原生 WM_WINDOWPOSCHANGING 钳到过期最小值，窗口下扩一截。
        _s = self.width() / 1920.0
        h = min(int(_s * 450), 200)
        if self.banner.height() != h:
            self.banner.setFixedHeight(h)
        pixmap = QPixmap(MAIN_BANNER).scaled(
            self.banner.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.banner.setPixmap(pixmap)
        self.banner.setScaledContents(True)
        try:
            self._place_edit_apply_bar()
        except Exception:
            pass

    def _save_home_order(self, order):
        try:
            val = ",".join([str(x) for x in order if x])
            # 走统一落盘：插件键 home_layout_order 必须进 config.json
            self._cfg_set("home_layout_order", val)
        except Exception as e:
            print("[home] save order failed:", e)

    def _move_home_block(self, key: str, delta: int = 0, to_index: int = None):
        order = self._layout_order()
        if key not in order:
            return
        i = order.index(key)
        if to_index is not None:
            j = max(0, min(int(to_index), len(order) - 1))
            if j == i:
                return
            item = order.pop(i)
            order.insert(j, item)
        else:
            j = i + int(delta)
            if j < 0 or j >= len(order):
                return
            order[i], order[j] = order[j], order[i]
        if getattr(self, "_home_edit_mode", False):
            # 编辑中只改现场顺序，点「应用」才落盘；离开未应用则还原
            self._edit_order_live = list(order)
        else:
            self._save_home_order(order)
        self._rebuild_home_layout()

    def _on_block_drag_started(self, key: str):
        self._drag_key = key

    def _drop_block_at(self, target_key: str):
        src = getattr(self, "_drag_key", None)
        if not src or not target_key or src == target_key:
            return
        order = self._layout_order()
        if src not in order or target_key not in order:
            return
        to_index = order.index(target_key)
        self._move_home_block(src, to_index=to_index)
        self._drag_key = None

    def enter_home_edit_mode(self):
        """进入可视化编辑：备份当前顺序，现场拖拽，点应用才保存。"""
        # 插件级守卫：主页编辑属于 assets_display，非启用/删除 → 整个入口无效
        if not self._assets_plugin_enabled():
            try:
                from gui.util.notification import notification

                notification.saved(self.config, "主页编辑", "主页编辑插件已停用或删除。")
            except Exception:
                pass
            return
        try:
            # 从配置读真实顺序作备份（不要用 live）
            self._home_edit_mode = False
            self._edit_order_live = None
            bak = list(self._layout_order())
        except Exception:
            bak = list(DEFAULT_HOME_ORDER)
        self._edit_order_backup = list(bak)
        self._edit_order_live = list(bak)
        self._cfg_set("tool_assets_home_edit", True)
        self.set_home_edit_mode(True)

    def apply_home_edit_mode(self):
        """应用：把现场顺序写入配置，退出编辑，停留主页。"""
        # 插件级守卫：主页编辑插件非启用/删除 → 不落盘，按取消收场
        if not self._assets_plugin_enabled():
            self.cancel_home_edit_mode()
            return
        live = getattr(self, "_edit_order_live", None)
        if isinstance(live, list) and live:
            self._save_home_order(list(live))
        self._edit_order_backup = None
        self._edit_order_live = None
        self._cfg_set("tool_assets_home_edit", False)
        self.set_home_edit_mode(False)

    def cancel_home_edit_mode(self):
        """取消：还原进入编辑前的顺序，退出编辑。"""
        bak = getattr(self, "_edit_order_backup", None)
        if isinstance(bak, list) and bak:
            try:
                self._save_home_order(list(bak))
            except Exception:
                pass
        self._edit_order_backup = None
        self._edit_order_live = None
        self._cfg_set("tool_assets_home_edit", False)
        try:
            self.set_home_edit_mode(False)
        except Exception:
            self._home_edit_mode = False
            try:
                self._rebuild_home_layout()
            except Exception:
                pass

    def hideEvent(self, event):
        # 离开主页且仍在编辑、未点应用 → 取消本次编辑
        try:
            if getattr(self, "_home_edit_mode", False):
                self.cancel_home_edit_mode()
        except Exception as e:
            print("[home] cancel on hide failed:", e)
        try:
            super().hideEvent(event)
        except Exception:
            pass

    def set_home_edit_mode(self, on: bool):
        on = bool(on)
        prev = bool(getattr(self, "_home_edit_mode", False))
        self._home_edit_mode = on
        if on and not isinstance(getattr(self, "_edit_order_live", None), list):
            try:
                self._edit_order_live = list(self._layout_order())
            except Exception:
                self._edit_order_live = list(DEFAULT_HOME_ORDER)
            if not isinstance(getattr(self, "_edit_order_backup", None), list):
                self._edit_order_backup = list(self._edit_order_live)
        if not on:
            self._edit_order_live = None
            # backup 在 apply/cancel 里清；这里不强制清，避免 hide 链路丢还原数据
        if prev == on:
            # 同态也强制重建一次，避免残留 wrap / 空白
            pass
        try:
            self._rebuild_home_layout()
        except Exception as e:
            print("[home] set_home_edit_mode rebuild failed:", e)
            # 兜底：强制非编辑重建
            self._home_edit_mode = False
            self._edit_order_live = None
            try:
                self._rebuild_home_layout()
            except Exception:
                pass

    def _mount_home_plugins(self):
        reg = None
        try:
            from module.tools.registry import get_registry
            reg = get_registry()
            items = reg.list_home_contributions(self.config)
        except Exception:
            items = []
        for host in self._slot_hosts.values():
            lay = host.layout()
            if lay is None:
                continue
            while lay.count():
                it = lay.takeAt(0)
                w = it.widget()
                if w is not None:
                    w.setParent(None)
        self._home_plugin_widgets = []
        for tool, contrib in items:
            slot = contrib.slot or "below_title"
            # 栏1/栏2 用户选择优先于 manifest 声明（栏1=标题下，栏2=启停下）
            try:
                from gui.components.expand.tool_style import get_home_bar_slot
                _choice = get_home_bar_slot(tool.id)
                if _choice == "1":
                    slot = "below_title"
                elif _choice == "2":
                    slot = "below_startup"
            except Exception:
                pass
            host = self._slot_hosts.get(slot)
            if host is None:
                # 未知槽位：明确告警并回退默认区，绝不静默塞入
                print(
                    "[home] plugin %s declares unknown slot %r, "
                    "falling back to below_title" % (tool.id, slot)
                )
                host = self._slot_hosts.get("below_title")
                if host is not None:
                    warn = QLabel(
                        "⚠ %s：主页位置 %r 未实现，已放到「标题下」" % (tool.name, slot),
                        host,
                    )
                    warn.setStyleSheet("color:#b26b00;font-size:12px;")
                    host.layout().addWidget(warn)
                    self._home_plugin_widgets.append(warn)
                if host is None:
                    continue
            try:
                w = tool.build_home_widget(parent=host, config=self.config)
            except Exception as e:
                print("[home] plugin %s build failed: %s" % (tool.id, e))
                w = None
            if w is None:
                continue
            host.layout().addWidget(w)
            self._home_plugin_widgets.append(w)
        # 加载失败可见提示：挂在标题下栏尾（深浅色各一档红），不遮正常入口
        try:
            errs = reg.errors if reg is not None else {}  # errors 是 property
        except Exception:
            errs = {}
        if errs:
            try:
                from gui.components.expand.tool_style import is_dark

                color = "#e06c75" if is_dark() else "#c0392b"
                from PyQt5.QtWidgets import QLabel

                host = self._slot_hosts.get("below_title")
                note = QLabel(
                    "⚠ 插件加载失败已禁用：" + "、".join(sorted(errs)) + "（详情见工具大厅）",
                    host,
                )
                note.setStyleSheet(f"color:{color};background:transparent;")
                host.layout().addWidget(note)
            except Exception as e:
                print("[home] plugin error notice failed:", e)
        for slot, host in self._slot_hosts.items():
            lay = host.layout()
            empty = lay is None or lay.count() == 0
            try:
                host.setVisible(not empty)
            except Exception:
                pass

    def refresh_home_plugins(self):
        """配置开关即时刷新主页插件区（入口/拦截/资产条）。"""
        try:
            self._mount_home_plugins()
            # 插件显隐后，编辑态下重排一次，避免空槽占位
            if getattr(self, "_home_edit_mode", False):
                self._rebuild_home_layout()
            else:
                for slot, host in self._slot_hosts.items():
                    lay = host.layout()
                    empty = lay is None or lay.count() == 0
                    try:
                        host.setVisible(not empty)
                    except Exception:
                        pass
        except Exception as e:
            print("[home] refresh_home_plugins failed:", e)

    def open_tool(self, tool_id: str):
        """主页入口：跳到左侧工具里的指定页。"""
        try:
            win = self.parent()
            # 向上找 Window
            w = win
            while w is not None and not hasattr(w, "open_tool_page"):
                try:
                    w = w.parent()
                except Exception:
                    w = None
            if w is not None and hasattr(w, "open_tool_page"):
                w.open_tool_page(tool_id, config=self.config)
                return
            # 兜底：config 上挂的 window
            cfg_win = None
            if hasattr(self.config, "get_window"):
                cfg_win = self.config.get_window()
            if cfg_win is not None and hasattr(cfg_win, "open_tool_page"):
                cfg_win.open_tool_page(tool_id, config=self.config)
        except Exception as e:
            print("[home] open_tool failed:", e)

    @pyqtSlot(int, str)
    def on_log_received(self, level: int, message: str) -> None:
        try:
            levels_str = ['&nbsp;&nbsp;&nbsp;&nbsp;INFO', '&nbsp;WARNING', '&nbsp;&nbsp;&nbsp;ERROR', 'CRITICAL']
            levels_color = ['#2d8cf0', '#ff9900', '#ed3f14', '#3e0480']
            status_html = [
                '<b style="color:%s;">%s</b>' % (_color, status)
                for _color, status in zip(levels_color, levels_str)]
            message = html.escape(message)
            message = message.replace('\n', '<br>').replace(' ', '&nbsp;')
            adding = (
                '<div style="font-family: Consolas, monospace;color:%s;">'
                '%s | %s | %s</div>'
            ) % (
                levels_color[level - 1],
                status_html[level - 1],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                message,
            )
            self.logger_box.append(adding)
        except Exception as e:
            print("Error when printing to log box: %s" % e)
            traceback.print_exc()

    def _change_hotkey(self, key: str):
        widgets = self.hotkey_widgets[key]
        current_hotkey_str = widgets["hotkey_push_button"].text().replace("<b>", "").replace("</b>", "")
        new_hotkey, ok = HotkeyInputDialog.get_hotkey(
            self.config.get_window(),
            current_hotkey_str,
            self.hk_mgr
        )
        if ok and new_hotkey != current_hotkey_str:
            widgets["hotkey_push_button"].setText(new_hotkey)
            self.config.set(key, new_hotkey)

    def call_update(self, data=None):
        try:
            if self.event_map == {}:
                with open(self.config.config_dir + '/event.json', 'r', encoding='utf-8') as f:
                    event_config = json.load(f)
                    for item in event_config:
                        self.event_map[item['func_name']] = item['event_name']

            if data:
                if type(data[0]) is dict:
                    self.info.setText(
                        self.tr("正在运行：") + bt.tr('ConfigTranslation', self.event_map[data[0]["func_name"]]))
                else:
                    self.info.setText(self.tr("正在运行：") + bt.tr('ConfigTranslation', data[0]))
                    _main_thread_ = self.config.get_main_thread()
                    _baas_thread_ = _main_thread_.get_baas_thread()
                    if _baas_thread_ is not None:
                        pass
                    else:
                        _main_thread_._init_script()
                        _baas_thread_ = _main_thread_.get_baas_thread()
        except JSONDecodeError:
            print("Empty JSON data")

    def set_button_state(self, state):
        state = bt.tr('MainThread', state)
        self.startup_card.button.setText(state)
        self.main_thread_attach.running = True if state == bt.tr("MainThread", "停止") else False

    def __connectSignalToSlot(self):
        self.thenSignal.connect(self.update_content_then)
        self.exitSignal.connect(lambda x: sys.exit(x))
        self.config.add_signal('then', self.thenSignal)

    def _start_clicked(self):
        self.call_update()
        if self.main_thread_attach.running:
            self.main_thread_attach.stop_play()
        else:
            self.main_thread_attach.start()

    def get_main_thread(self):
        return self.main_thread_attach

    def update_content_then(self, option: str):
        self.startup_card.setContent(self.tr('开始你的档案之旅') + ' - ' + self.tr("完成后") + f' {option}')

    def _init_hotkey(self, key: str, default: str, callback):
        self.hk_callbacks[key] = callback
        if not self.config.has(key):
            self.config.set(key, default)
        bind_key = self.config.get(key, default)
        self.hk_mgr.register(bind_key, callback)
        self.hk_mgr.start()



class MainThread(QThread):
    button_signal = pyqtSignal(str)
    logger_signal = pyqtSignal(int, str)
    update_signal = pyqtSignal(list)
    exit_signal = pyqtSignal(int)

    def __init__(self, config):
        super(MainThread, self).__init__()
        self.config = config
        self.hash_name = md5(f'{time.time()}%{random()}'.encode('utf-8')).hexdigest()
        self._main_thread = None
        self.Main = None
        self.running = False

    def run(self):
        self.display(self.tr("停止"))
        if not self._init_script():
            self.display(self.tr("启动"))
            return
        self.running = True
        self.display(self.tr("停止"))
        self._main_thread.logger.info("Starting Blue Archive Auto Script...")
        self._main_thread.send('start')

    def stop_play(self):
        self.running = False
        if self._main_thread is None:
            return
        self.display(self.tr("启动"))
        self._main_thread.send('stop')
        self.exit(0)

    def _init_script(self):
        while self.Main is None:
            time.sleep(0.01)
        if self._main_thread is None:
            assert self.Main is not None
            self._main_thread = self.Main.get_thread(self.config, name=self.hash_name, logger_signal=self.logger_signal,
                                                     button_signal=self.button_signal, update_signal=self.update_signal,
                                                     exit_signal=self.exit_signal)
            self.config.add_signal('update_signal', self.update_signal)
        return self._main_thread.init_all_data()

    def display(self, text):
        self.button_signal.emit(text)

    def start_hard_task(self):
        self._init_script()
        self.update_signal.emit(['困难关推图'])
        self.display(self.tr("停止"))
        if self._main_thread.send('solve', 'explore_hard_task'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('困难图推图已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.update_signal.emit([self.tr('无任务')])
        self.display(self.tr("启动"))

    def start_normal_task(self):
        self._init_script()
        self.update_signal.emit([self.tr('普通关推图')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'explore_normal_task'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('普通图推图已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.update_signal.emit([self.tr('无任务')])
        self.display(self.tr("启动"))

    def start_fhx(self):
        self._init_script()
        if self._main_thread.send('solve', 'de_clothes'):
            notify(title='BAAS', body=self.tr('反和谐成功，请重启BA下载资源'))

    def start_main_story(self):
        self._init_script()
        self.update_signal.emit([self.tr('自动主线剧情')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'main_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('主线剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.update_signal.emit([self.tr('无任务')])
        self.display(self.tr('启动'))

    def start_group_story(self):
        self._init_script()
        self.update_signal.emit([self.tr('自动小组剧情')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'group_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('小组剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display('启动')
        self.update_signal.emit([self.tr('无任务')])

    def start_mini_story(self):
        self._init_script()
        self.display(self.tr('停止'))
        self.update_signal.emit([self.tr('自动支线剧情')])
        if self._main_thread.send('solve', 'mini_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('支线剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def start_explore_activity_story(self):
        self._init_script()
        self.display(self.tr('停止'))
        self.update_signal.emit([self.tr('自动活动剧情')])
        if self._main_thread.send('solve', 'explore_activity_story'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('活动剧情已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def start_explore_activity_mission(self):
        self._init_script()
        self.display(self.tr('停止'))
        self.update_signal.emit([self.tr('自动活动任务')])
        if self._main_thread.send('solve', 'explore_activity_mission'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('活动任务已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def start_explore_activity_challenge(self):
        self._init_script()
        self.update_signal.emit([self.tr('自动活动挑战')])
        self.display(self.tr('停止'))
        if self._main_thread.send('solve', 'explore_activity_challenge'):
            if self._main_thread.flag_run:
                notify(title='BAAS', body=self.tr('活动挑战推图已完成'))
            else:
                self._main_thread.logger.info(HUMAN_TAKE_OVER_MESSAGE)
        self.display(self.tr('启动'))
        self.update_signal.emit([self.tr('无任务')])

    def get_baas_thread(self):
        return self._main_thread
