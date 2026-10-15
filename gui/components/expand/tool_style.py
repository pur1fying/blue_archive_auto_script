# -*- coding: utf-8 -*-
"""工具工作台的主题、表单和排版。

使用中性背景承载内容；主题色只表示选中、焦点与主要操作。
所有颜色在刷新时读取，保证浅色、深色和自定义主题色保持一致。
"""

REM = 8  # 0.5rem（1rem≈16px）

try:
    from gui.util.config_gui import configGui
except Exception:  # pragma: no cover
    configGui = None

# PyQt5 控件导入（TipLabel 等用）；缺库时退化为 None，不阻断样式函数
try:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QColor, QFont
    from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
except Exception:  # pragma: no cover
    Qt = QColor = QFont = pyqtSignal = None  # type: ignore
    QFrame = QHBoxLayout = QLabel = QSizePolicy = None  # type: ignore


def is_dark() -> bool:
    """当前是否为深色主题。

    必须用 qfw 的 isDarkTheme()（读 qconfig.theme，setTheme 实时更新）。
    不能读 configGui.theme：qconfig.load 后全局 qconfig 与 configGui
    共享 _cfg，setTheme 只更新 configGui 实例上的 _theme，而
    configGui.theme 属性读 configGui._cfg._theme——永远停在启动值，
    切主题后得到冻结结果（浅色模式下按深色配色刷字）。
    """
    try:
        from qfluentwidgets import isDarkTheme

        return bool(isDarkTheme())
    except Exception:
        return False


# ── 主题感知颜色函数（深色主题下返回深色版本） ──

def themed_section_header_bg() -> str:
    return themed_section_body_bg()


def themed_section_body_bg() -> str:
    return "#26292F" if is_dark() else "#FFFFFF"


def themed_note_bg() -> str:
    return "#2D3138" if is_dark() else "#F5F7FA"


def themed_switch_note_bg() -> str:
    return themed_section_body_bg()


def themed_input_bg() -> str:
    return "#22252B" if is_dark() else "#FFFFFF"


def themed_input_text() -> str:
    return themed_text()


def themed_accent() -> str:
    """主题强调色：跟随 应用设置 → 主题颜色（configGui.themeColor）。

    选中开关边框、输入框聚焦边框等
    "随用户主题"的颜色都从这里取。
    """
    try:
        from gui.util.config_gui import configGui
        val = QColor(configGui.themeColor.value)
        return val.name() if val.isValid() else "#0078d4"
    except Exception:
        return "#0078d4"


def themed_input_border() -> str:
    """表单和卡片的低对比度细边框。"""
    return "#414650" if is_dark() else "#DDE2E9"


def themed_input_border_focus() -> str:
    """聚焦边框：跟随应用设置的主题颜色（实色，随主题）。"""
    return themed_accent()


def themed_page_bg() -> str:
    return "#202329" if is_dark() else "#F5F7FA"


def themed_card_bg() -> str:
    """卡片与工作台内容使用同一层表面色。"""
    return themed_section_body_bg()


def themed_text() -> str:
    return "#E6E9EF" if is_dark() else "#273142"


def themed_secondary_text() -> str:
    """辅助说明与元数据，避免和标题争抢层次。"""
    return "#A6AFBD" if is_dark() else "#687588"


def themed_selected_bg() -> str:
    """选中项的淡主题色背景。"""
    accent = QColor(themed_accent())
    surface = QColor(themed_section_body_bg())
    alpha = 0.18 if is_dark() else 0.07
    return QColor(*(round(surface.getRgb()[i] * (1 - alpha) + accent.getRgb()[i] * alpha)
                    for i in range(3))).name()


def themed_card_border() -> str:
    """插件卡常态边框：与全局 1px 统一边框同源（实色，深浅自适应）。

    插件卡不是开关格，无 2px 资格；也禁止 COLOR_THEME 里的半透明 border
    （#ee.../rgba(...)），半透明+圆角=抗锯齿灰点（粗糙边框）。
    """
    return themed_input_border()


def themed_card_hover_border() -> str:
    return themed_accent()


def themed_accent_text() -> str:
    return "#8BC4FF" if is_dark() else "#0067B8"


def themed_title_text() -> str:
    """标题文字色（比正文略深/亮）。"""
    return "#F3F5F8" if is_dark() else "#192536"


# ── 颜色收敛：曾经散落在各插件页的字面量，统一在此取值（单一来源） ──

# apply_full_theme_refresh 做「白底跟随主题」时按这些浅色快照识别可替换底色。
# FFFFFF=themed_input_bg 浅值；F7FAFD=themed_top_bg 浅值；FAFAFA=历史默认底。
_LEGACY_LIGHT_BG_HEX = ("FFFFFF", "F7FAFD", "FAFAFA")


def themed_top_bg() -> str:
    return themed_section_body_bg()


def themed_tool_card_bg() -> str:
    return themed_card_bg()


def themed_soft_border_rgba(alpha) -> str:
    """蓝灰边框/分隔线（原各页散落的 rgba(80,120,170,a) 家族）。

    半透明色+圆角会被抗锯齿渲染成粗糙灰点（深浅皆然），故两个主题都
    按 content/input 底色（浅 #FFFFFF、深 #3a3f47）预混为实色，
    观感与半透明一致、描边干净。
    """
    a = max(0, min(255, int(alpha))) / 255.0
    base = (38, 41, 47) if is_dark() else (255, 255, 255)
    fg = (137, 148, 163) if is_dark() else (117, 131, 151)
    return "rgb(%d,%d,%d)" % tuple(round(b + (f - b) * a) for b, f in zip(base, fg))


def themed_accent_fill_rgba(alpha) -> str:
    """主题强调色的淡染底（rgba）。

    用户裁定用途：浅色模式下小按钮选中覆盖层的淡强调底（深色已有底色
    变化，不加）。仅此一处使用，勿再散落。
    """
    hexv = themed_accent()
    r, g, b = (int(hexv[i:i + 2], 16) for i in (1, 3, 5))
    return "rgba(%d,%d,%d,%d)" % (r, g, b, alpha)


def themed_note_border() -> str:
    """小框（Note 类内容框）唯一边线。

    equipNote / homeEditNote / hoardNote / 悬浮选择列表同一条线：
    曾经各写各的（themed_input_border / soft_border 55 / 70 / 80），现统一。
    深浅行为继承 themed_soft_border_rgba（浅半透明原值、深色预混实色防粗糙）。
    """
    return themed_soft_border_rgba(55)


def themed_page_transparent_qss(*objs) -> str:
    """页底透明骨架唯一工厂：传入各容器/滚动区的 objectName 即可。

    每个 obj 生成 QWidget/QFrame 透明底 + QScrollArea 透明（含子代理），
    不匹配的选择器无害。
    """
    parts = []
    for o in objs:
        parts.append("QWidget#%s{background:transparent;}" % o)
        parts.append("QFrame#%s{background:transparent;border:none;}" % o)
        parts.append("QScrollArea#%s{background:transparent;border:none;}" % o)
        parts.append("QScrollArea#%s > QWidget > QWidget{background:transparent;}" % o)
    return "".join(parts)


def themed_small_checkbox_css() -> str:
    """小号勾选框：qfw 原版 check_box qss + 13px 指示器（绿框边体系）。

    unchecked 指示器边框用 note_border（小框统一边线），其余沿用 qfw
    原值；结果按主题缓存，不重复拼串。
    """
    cache = getattr(themed_small_checkbox_css, "_cache", None)
    if cache is None:
        cache = themed_small_checkbox_css._cache = {}
    try:
        from qfluentwidgets.common.style_sheet import (
            FluentStyleSheet, getStyleSheet, applyThemeColor,
        )
        from qfluentwidgets.common.config import Theme

        theme = Theme.DARK if is_dark() else Theme.LIGHT
        css = cache.get(theme)
        if css is None:
            css = applyThemeColor(getStyleSheet(FluentStyleSheet.CHECK_BOX, theme)) + (
                "\nCheckBox::indicator { width: 13px; height: 13px; }"
                "\nCheckBox::indicator:unchecked { border: 1px solid %s; border-radius: 3px; }"
                "\nCheckBox { spacing: 1px; min-width: 0px; min-height: 0px; margin-left: 0px; }"
            ) % themed_note_border()
            cache[theme] = css
        return css
    except Exception as e:
        print("[tool_style] small checkbox css failed:", e)
        return ""


def themed_inner_select_qss(obj, on) -> str:
    """「程序内在选」的 1px 蓝框（库存备品框、编队表格格子/列头共用）。

    主题引擎的三种选中样式家族：
      - GreenFrameOption         功能性的绿框（含第一栏/第二栏单选）
      - header_switch_css        重要开关的 2px 蓝框
      - themed_inner_select_qss  程序内在选的 1px 蓝框（本函数）
    """
    bd = themed_accent() if on else themed_input_border()
    return "QFrame#%s{border:1px solid %s;border-radius:6px;background:transparent;}" % (obj, bd)


class GreenFrameOption(QFrame):
    """可点选的选项按钮；保留旧类名以兼容插件。"""

    toggled = pyqtSignal(str, bool)

    def __init__(self, key="", text="", parent=None, *, checked=False,
                 fixed_h=36, font_px=13, font_weight=500, min_w=0, pad=(10, 6)):
        super().__init__(parent)
        self.key = str(key)
        self._checked = bool(checked)
        self.setObjectName("greenFrameOption")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(text)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFixedHeight(fixed_h)
        if min_w:
            self.setMinimumWidth(int(min_w))
        self._font_px = int(font_px)
        self._font_weight = min(600, int(font_weight))
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(pad[0], pad[1], pad[0], pad[1])
        self._lay.setSpacing(8)
        self.lab = QLabel(text, self)
        self._lay.addWidget(self.lab)
        self._apply()
        try:
            if configGui is not None:
                safe_connect_theme(self, self._apply)
        except Exception:
            pass

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked, *, emit=True):
        checked = bool(checked)
        if self._checked == checked:
            self._apply()
            return
        self._checked = checked
        self._apply()
        if emit:
            self.toggled.emit(self.key, self._checked)

    # 装备侧历史别名（set_on 不发信号，模式互斥由调用方管理）
    def is_on(self) -> bool:
        return self._checked

    def set_on(self, on, emit=False):
        self.set_checked(on, emit=emit)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.set_checked(not self._checked)
            e.accept()
            return
        super().mousePressEvent(e)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.set_checked(not self._checked)
            event.accept()
            return
        super().keyPressEvent(event)

    def _apply(self):
        bg = themed_selected_bg() if self._checked else themed_section_body_bg()
        border = themed_accent() if self._checked else themed_input_border()
        set_style_dedup(
            self,
            "QFrame#greenFrameOption{background:%s;"
            "border:1px solid %s;border-radius:6px;}"
            "QFrame#greenFrameOption:hover,QFrame#greenFrameOption:focus{border-color:%s;}"
            % (bg, border, themed_accent())
        )
        self.setAccessibleDescription("已选择" if self._checked else "未选择")
        if getattr(self, "lab", None) is not None:
            self.lab.setStyleSheet(
                f"font-size:{self._font_px}px;font-weight:{self._font_weight};"
                f"color:{themed_text()};background:transparent;"
            )
        self.update()


def themed_title_bar_qss(obj) -> str:
    """标题栏（顶栏横幅）唯一工厂：边线与小框同一条（note_border）+ top_bg。"""
    return ("QFrame#%s{border:1px solid %s;border-radius:8px;background:%s;}"
            % (obj, themed_note_border(), themed_top_bg()))


def themed_separator() -> str:
    """分隔线唯一取值（原装备 80 / 囤体 70 两个值统一）。"""
    return themed_soft_border_rgba(70)


def themed_success_border() -> str:
    """成功/推荐态边框绿（原 #6FBF63）。"""
    return "#5aa951" if is_dark() else "#6FBF63"


def themed_success_soft() -> str:
    """成功/推荐态浅绿（原 #8FCF84）。"""
    return "#79ab70" if is_dark() else "#8FCF84"


def themed_success_fill_rgba(alpha) -> str:
    """成功态半透明底（原 rgba(111,191,99,a)）。"""
    return "rgba(111,191,99,%d)" % alpha


def themed_badge_bg() -> str:
    return "#333943" if is_dark() else "#EFF2F6"


def themed_disabled_text() -> str:
    """停用态文字灰（原 #8a8a8a）。"""
    return "#929BA8" if is_dark() else "#798596"


def themed_disabled_strip() -> str:
    """停用横条底（原 rgba(140,140,140,36)）。"""
    return "rgba(130,130,130,46)" if is_dark() else "rgba(140,140,140,36)"


def themed_scrollbar_qss(handle_w=10) -> str:
    """竖向滚动条 QSS 工厂（原各页散落的 rgba(100,140,180,*) 写法）。

    只含 QScrollBar 段；调用方把它与其容器（如 QScrollArea）的样式拼接。
    """
    handle = "#505966" if is_dark() else "#C3CAD4"
    hover = "#788393" if is_dark() else "#98A4B4"
    return (
        "QScrollBar:vertical{width:%dpx;background:transparent;margin:2px;}"
        "QScrollBar::handle:vertical{"
        "background:%s;border-radius:%dpx;min-height:28px;}"
        "QScrollBar::handle:vertical:hover{background:%s;}"
        "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:transparent;}"
        "QScrollBar:horizontal{height:%dpx;background:transparent;margin:2px;}"
        "QScrollBar::handle:horizontal{"
        "background:%s;border-radius:%dpx;min-width:28px;}"
        "QScrollBar::handle:horizontal:hover{background:%s;}"
        "QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{width:0;}"
        "QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{background:transparent;}"
        % (handle_w, handle, handle_w // 2, hover, handle_w, handle, handle_w // 2, hover)
    )


def themed_section_css(sec: str, head: str, body: str) -> str:
    """主题引擎统一大框（标题栏+内容）QSS 工厂。

    所有插件页的大框都从这里取样式，禁止各页自造：边框=统一 1px
    （themed_input_border），标题栏/内容底色走 themed_section_*()。
    参数为三个 objectName（外框/标题栏/内容区）。
    """
    body_bg = themed_section_body_bg()
    return (
        "QFrame#%s{border:1px solid %s;border-radius:10px;background:%s;}"
        "QFrame#%s{background:%s;border:none;"
        "border-top-left-radius:9px;border-top-right-radius:9px;}"
        "QFrame#%s{background:%s;border:none;"
        "border-bottom-left-radius:9px;border-bottom-right-radius:9px;}"
        % (sec, themed_input_border(), body_bg, head, themed_section_header_bg(), body, body_bg)
    )


def themed_table_css(table: str) -> str:
    """主题引擎统一小框表格 QSS：整个表格 1px 统一描边 + 输入框底。"""
    return (
        "QFrame#%s{border:1px solid %s;border-radius:8px;background:%s;}"
        % (table, themed_input_border(), themed_input_bg())
    )


def themed_workspace_tabs_css(name: str) -> str:
    """工作台内的轻量页签，共用尺寸和主题色下划线。"""
    return (
        f"QTabWidget#{name}::pane{{border:0;background:transparent;}}"
        f"QTabWidget#{name} QTabBar{{background:transparent;}}"
        f"QTabWidget#{name} QTabBar::tab{{background:transparent;"
        f"color:{themed_secondary_text()};font-size:13px;padding:10px 16px;"
        "border:0;border-bottom:2px solid transparent;margin-right:8px;}"
        f"QTabWidget#{name} QTabBar::tab:selected{{color:{themed_title_text()};"
        f"border-bottom-color:{themed_accent()};}}"
        f"QTabWidget#{name} QTabBar::tab:hover{{background:{themed_note_bg()};}}"
    )


def make_icon_button(icon, tooltip, parent=None, *, primary=False, size=34):
    """统一的图标操作：悬停提示、原生反馈和无障碍名称。"""
    from qfluentwidgets import PrimaryToolButton, ToolButton, ToolTipFilter, ToolTipPosition

    button = (PrimaryToolButton if primary else ToolButton)(icon, parent)
    button.setFixedSize(size, size)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip.split("\n", 1)[0])
    button.setCursor(Qt.PointingHandCursor)
    button._action_tooltip = ToolTipFilter(button, showDelay=250, position=ToolTipPosition.BOTTOM)
    button.installEventFilter(button._action_tooltip)
    return button


# ── 默认常量（浅色，兼容旧引用；动态面板请用 themed_*() 函数） ──

SECTION_HEADER_BG = "#FFFFFF"
SECTION_BODY_BG = "#FFFFFF"

NOTE_BG = "#F5F7FA"
SWITCH_NOTE_BG = "#FFFFFF"

# 顶栏开关格统一尺寸（顶栏设置 = 标题栏快捷 = 同一套）
SWITCH_CELL_H = 56
SWITCH_CELL_PAD_X = 10
SWITCH_CELL_PAD_Y = 8
SWITCH_BORDER_PX = 1
# 选中/未选边框色不再放模块级快照：themed_switch_border(on) 运行时现算
# （历史遗留的 SWITCH_ON_BORDER/SWITCH_OFF_BORDER 浅色快照已删）。
SWITCH_BORDER_RADIUS = 8


def themed_switch_border(on: bool) -> str:
    """开关格通过主题色边框表示已启用。"""
    if on:
        return themed_accent()
    return themed_input_border()


def themed_spinbox_css() -> str:
    """统一 qfluent SpinBox 外壳、编辑区和按钮区主题。

    padding-right 必须为右侧竖排按钮（24px）预留空间；qfw 默认样式预留
    ~80px，窄控件下编辑区会被压成 0 宽导致数字不可见、不可编辑。
    """
    return (
        "QSpinBox{"
        f"background:{themed_input_bg()};color:{themed_input_text()};"
        f"border:1px solid {themed_input_border()};border-radius:6px;"
        "padding:0px 25px 0px 6px;}"
        "QLineEdit{background:transparent;border:0px;padding:0px;margin:0px;"
        f"color:{themed_input_text()};}}"
        "QToolButton{background:transparent;border:0px;padding:0px;margin:0px;}"
    )


def themed_input_css() -> str:
    """输入框统一样式（主题感知）。"""
    return (
        "LineEdit,QLineEdit,QTextEdit{"
        f"background:{themed_input_bg()};color:{themed_input_text()};"
        f"border:1px solid {themed_input_border()};border-radius:6px;padding:4px 8px;"
        'font-size:13px;}'
        "LineEdit:focus,QLineEdit:focus,QTextEdit:focus{"
        f"border:1px solid {themed_input_border_focus()};"
        "}"
    )


# 深灰文字色正则：匹配所有需要在深色主题下变亮的文字色
_DARK_TEXT_RE = None


def _dark_text_re():
    global _DARK_TEXT_RE
    if _DARK_TEXT_RE is None:
        import re
        # 含 themed 文字值(e0e0e0/e8e8e8/333333/111111)：切回浅色时
        # 正则能匹配上一次替换进 styleSheet 的 themed 值 → 双向可逆
        _DARK_TEXT_RE = re.compile(
            r'color:#(222|223|234|334|345|456|622|678|789|'
            r'142433|2A3A4A|1a3a7a|'
            r'e0e0e0|e8e8e8|333333|111111|E6E9EF|273142);',
            re.IGNORECASE,
        )
    return _DARK_TEXT_RE


def apply_theme_to_labels(widget):
    """遍历 widget 下所有 QLabel，把深灰文字色替换为主题感知色。

    保留蓝色强调色（#1a5fb4 等）不动。在初始化和 themeChanged 时调用。
    无显式 color 的裸 QLabel(上游 _embed 页常见)补 themed_text,
    否则深色下沿用 QApplication 默认黑字。
    """
    try:
        from PyQt5.QtWidgets import QLabel
        txt = themed_text()
        pat = _dark_text_re()
        for w in widget.findChildren(QLabel):
            try:
                if w.property("themeSemanticColor"):
                    continue
                old = w.styleSheet() or ""
                if pat.search(old):
                    _set_style_if_changed(w, pat.sub(f'color:{txt};', old))
                elif "color:" not in old.replace(" ", "").lower():
                    _set_style_if_changed(w, (old + " " if old else "") + f"color:{txt};")
            except Exception:
                pass
    except Exception:
        pass


# ── 中心化主题引擎：控件声明式接入，主题切换统一重刷 ──
# 控件不再各自连 themeChanged（此前每格一连接、各自存 CSS 快照，
# 状态与样式两套真源必然错位）。任何控件调 register_theme_managed
# 注册一个"重刷闭包"，闭包内现算 themed_*() 并用活状态（如真实
# SwitchButton.isChecked()），引擎保证切主题时全部按序重刷。
_THEME_MANAGED = []  # [(widget, apply)]
_theme_engine_connected = False


def register_theme_managed(widget, apply):
    """注册一个主题受管控件：apply() 在每次主题切换后调用（现算样式）。

    widget 删除后自动摘除；重复注册同一 (widget, apply) 去重。
    """
    try:
        for w, a in _THEME_MANAGED:
            if w is widget and a is apply:
                return
        _THEME_MANAGED.append((widget, apply))
    except Exception:
        return
    _ensure_theme_engine()


def _ensure_theme_engine():
    global _theme_engine_connected
    if _theme_engine_connected or configGui is None:
        return
    try:
        configGui.themeChanged.connect(_on_theme_changed_global)
        _theme_engine_connected = True
    except Exception:
        pass


def _on_theme_changed_global(*_args):
    """切主题：统一延迟重刷全部受管控件（0ms + 150ms 双刷，防 qfw 异步覆盖）。"""
    try:
        from PyQt5.QtCore import QTimer

        QTimer.singleShot(0, _refresh_managed_now)
        QTimer.singleShot(150, _refresh_managed_now)
    except Exception:
        pass


def _refresh_managed_now():
    from PyQt5 import sip

    alive = []
    for item in list(_THEME_MANAGED):
        ref = item[0]
        w = ref() if callable(ref) else ref  # 兼容弱引用/旧强引用条目
        if w is None:
            continue  # widget 已回收：摘除
        try:
            if sip.isdeleted(w):
                continue  # 已删：摘除
        except Exception:
            continue
        alive.append(item)
        apply = item[1]
        try:
            apply()
        except Exception:
            pass
    _THEME_MANAGED[:] = alive


def safe_connect_theme(widget, callback, light_callback=None):
    """连 themeChanged，切主题后延迟刷新（widget 已删则跳过）。

    双轮：0ms 跑完整 callback；150ms 补刷轮默认只跑 light_callback
    （重型全量刷新每主题切换只跑一遍，dedup 后 150ms 轮本就多为空转，
    轻量化直接砍掉一半感知耗时）。light_callback 缺省时两轮同 callback。

    历史注记：之前同步连回调会崩——themeChanged 信号在 setTheme 过程中
    同步触发，widget 半重建，回调访问易段错误；故用 QTimer.singleShot(0)
    延迟到事件循环空闲（setTheme 已完成、widget 稳定）再刷。
    """
    try:
        if configGui is None or widget is None:
            return
        from PyQt5.QtCore import QTimer
        from PyQt5 import sip

        def _do():
            try:
                if sip.isdeleted(widget):
                    return
                callback()
            except Exception:
                pass

        def _do_light():
            try:
                if sip.isdeleted(widget):
                    return
                (light_callback if light_callback is not None else callback)()
            except Exception:
                pass

        # 去重：同一 widget 上重复连接同一 callback 直接跳过（页面反复
        # open_tool 重建顶栏时，防止 themeChanged 连接数随使用线性累积）
        slots = getattr(widget, "_theme_changed_slots", None)
        if slots is None:
            slots = []
            widget._theme_changed_slots = slots
        if callback in slots:
            return
        slots.append(callback)

        # 绑定成 widget 的成员方法再连接：receiver=widget，widget 被销毁时
        # Qt 自动断开这条连接（旧实现连裸闭包，receiver 永久存活 → 旧控件
        # 的回调永不回收，切主题随使用越来越慢）。槽内保留双 QTimer 语义。
        import types

        def _slot(_self, *_args):
            QTimer.singleShot(0, _do)
            QTimer.singleShot(150, _do_light)

        bound = types.MethodType(_slot, widget)
        widget._theme_changed_slot_ref = bound  # 持引用防 GC
        configGui.themeChanged.connect(bound)
    except Exception:
        pass


def connect_theme_refresh(widget):
    """连 themeChanged，切主题完成后延迟安全刷文字色（widget 删了跳过）。"""
    safe_connect_theme(widget, lambda: apply_theme_to_labels(widget))


def _switch_qss(object_name, on):
    """单个开关格现算 QSS：背景随主题 + 边框按 on/off 着色。

    框用 QSS border 画（不用 paintEvent monkey-patch——PyQt5 虚函数走 C++
    vtable，实例属性覆盖 paintEvent 不会被 Qt 调用，框画不出来）。
    on/off 用同厚 border，开关切换时格子尺寸不抖。
    """
    bg = themed_selected_bg() if on else themed_switch_note_bg()
    bd = themed_switch_border(on)
    return (
        "QFrame#%s{border:%dpx solid %s;border-radius:%dpx;background:%s;}"
        % (object_name, SWITCH_BORDER_PX, bd, SWITCH_BORDER_RADIUS, bg)
    ) + _inline_setting_css(object_name)


def _inline_setting_css(object_name):
    return (
        f'QFrame#{object_name}[inlineHeaderSetting="true"]'
        '{background:transparent;border:0;border-radius:0;}'
    )


def header_switch_css(*object_names, border_px=SWITCH_BORDER_PX):
    """按 QFrame objectName 生成开关格 关/开 两态 QSS（主题感知）。

    off 用淡灰边框、on 用蓝边框，同厚 border_px（切换不挤位）。
    框由 QSS border 画（可靠），所有开关格共用这套 → 厚薄/颜色/圆角一致。
    """
    bg = themed_switch_note_bg()
    bd_off = themed_switch_border(False)
    bd_on = themed_switch_border(True)
    off_parts = []
    on_parts = []
    for n in object_names:
        off_parts.append(
            "QFrame#%s{border:%dpx solid %s;border-radius:%dpx;background:%s;}"
            % (n, border_px, bd_off, SWITCH_BORDER_RADIUS, bg) + _inline_setting_css(n)
        )
        on_parts.append(
            "QFrame#%s{border:%dpx solid %s;border-radius:%dpx;background:%s;}"
            % (n, border_px, bd_on, SWITCH_BORDER_RADIUS, bg) + _inline_setting_css(n)
        )
    return "".join(off_parts), "".join(on_parts)


def _switch_label_css():
    """开关格内 QLabel 文字色 QSS（主题感知）。"""
    return "color:%s;background:transparent;" % themed_text()


def _apply_switch_labels(cell):
    """刷开关格内所有 QLabel 文字色（主题感知）。"""
    try:
        from PyQt5.QtWidgets import QLabel
        css = _switch_label_css()
        import re as _re
        for w in cell.findChildren(QLabel):
            try:
                old = w.styleSheet() or ""
                old = _re.sub(r'color:[^;]+;', '', old)
                old = _re.sub(r'background:[^;]+;', 'background:transparent;', old)
                w.setStyleSheet(old + css)
            except Exception:
                pass
    except Exception:
        pass


def _live_switch_on(cell):
    """从格内真实 SwitchButton 读当前 on 态；无开关子件则回退 _switch_on 属性。

    部分路径（如 _load 里 blockSignals + setChecked）不触发 checkedChanged，
    _switch_on 属性会停在旧值，切主题后 _refresh 按旧值画出灰框（蓝框丢失）。
    以真实 isChecked() 为准可彻底消除态错位；preferClearCell 无开关子件不受影响。
    """
    try:
        from qfluentwidgets import SwitchButton
        for sw in cell.findChildren(SwitchButton):
            return bool(sw.isChecked())
    except Exception:
        pass
    return bool(getattr(cell, "_switch_on", False))


def make_header_setting_cell(title, widget, *, obj_name, min_w=0, parent=None):
    """显示设置栏中的标签与开关，开关本身表达状态。"""
    try:
        off_css, on_css = header_switch_css(obj_name)
    except Exception:
        off_css = on_css = ""
    try:
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QSizePolicy
    except Exception:
        return None
    cell = QFrame(parent)
    cell.setObjectName(obj_name)
    cell.setProperty("inlineHeaderSetting", True)
    cell.setAttribute(Qt.WA_StyledBackground, True)
    cell.setStyleSheet(off_css)
    attach_header_switch_refresh(cell)
    cl = QHBoxLayout(cell)
    cl.setContentsMargins(0, 0, 0, 0)
    cl.setSpacing(10)
    cl.setAlignment(Qt.AlignVCenter)
    lab = QLabel(title, cell)
    lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    lab.setStyleSheet(
        'font-size:13px;font-weight:400;'
        f"color:{themed_text()};background:transparent;"
    )
    cl.addWidget(lab, 0, Qt.AlignVCenter)
    if widget is not None:
        widget.setAccessibleName(title)
        if hasattr(widget, "setOnText") and hasattr(widget, "setOffText"):
            widget.setOnText("")
            widget.setOffText("")
            widget.setSpacing(0)
            widget.label.hide()
            widget.setFixedWidth(44)
            if hasattr(widget, "indicator"):
                widget.indicator.setAccessibleName(title)
        cl.addWidget(widget, 0, Qt.AlignVCenter)
    if min_w:
        cell.setMinimumWidth(min_w)
    cell.setFixedHeight(36)
    cell.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

    def _apply_on(on):
        on = bool(on)
        try:
            cell._header_on = on  # 主题刷新链按此重画选中态
        except Exception:
            pass
        try:
            fn = getattr(cell, "_apply_switch_state", None)
            if callable(fn):
                fn(on)
            else:
                cell.setStyleSheet(on_css if on else off_css)
            cell.update()
        except Exception:
            pass

    def _refresh_all():
        # 用活状态（真实开关 isChecked）重画 + 标题文字主题色跟随；
        # blockSignals+setChecked 不发信号也不会再造成态错位
        try:
            live = _live_switch_on(cell)
            fn = getattr(cell, "_apply_switch_state", None)
            if callable(fn):
                fn(live)
            cell._header_on = live
        except Exception:
            pass
        try:
            lab.setStyleSheet(
                'font-size:13px;font-weight:400;'
                f"color:{themed_text()};background:transparent;"
            )
        except Exception:
            pass

    try:
        cell._header_on = False
        cell._apply_header_on = _apply_on
        cell._header_label = lab  # 引擎统一刷标题文字色
    except Exception:
        pass
    try:
        if widget is not None and hasattr(widget, "checkedChanged"):
            widget.checkedChanged.connect(_apply_on)
            _apply_on(bool(widget.isChecked()))
    except Exception:
        pass
    return cell


def attach_header_switch_refresh(cell):
    """给开关格挂主题感知 _refresh + _apply_switch_state（现算 on/off QSS）。

    开关格 reparent 到工具大厅顶栏容器后，脱离各工具页 QObject 树，
    各页 _apply_theme 的 findChildren 刷不到；改由格子自己监听 themeChanged
    现算刷新。现算 _switch_qss(name, on) 保证深/浅双向正确，不依赖模块
    加载时的浅色常量快照。

    _apply_switch_state(on)：开关拨动时调它设现算 QSS，避免各页 _sync 闭包
    用浅色常量覆盖 → 切主题后再拨开关又变回浅色。
    """
    try:
        name = cell.objectName() if cell is not None else ""
        if not name:
            return cell

        def _refresh():
            try:
                from PyQt5 import sip
                if sip.isdeleted(cell):
                    return
                _on = _live_switch_on(cell)
                cell._switch_on = _on  # type: ignore[attr-defined]
                set_style_dedup(cell, _switch_qss(name, _on))
                _apply_switch_labels(cell)
                # 统一格的标题 label 也跟随主题（_header_on 由引擎外层同步）
                try:
                    _hdr_lab = getattr(cell, "_header_label", None)
                    if _hdr_lab is not None:
                        set_style_dedup(
                            _hdr_lab,
                            'font-size:13px;'
                            f"font-weight:400;color:{themed_text()};"
                            "background:transparent;"
                        )
                except Exception:
                    pass
            except Exception:
                pass

        def _apply_switch_state(on):
            try:
                from PyQt5 import sip
                if sip.isdeleted(cell):
                    return
                cell._switch_on = bool(on)  # type: ignore[attr-defined]
                set_style_dedup(cell, _switch_qss(name, bool(on)))
            except Exception:
                pass

        cell._refresh = _refresh  # type: ignore[attr-defined]
        cell._apply_switch_state = _apply_switch_state  # type: ignore[attr-defined]
        # 中心引擎统一重刷（控件零接线、零快照，态永远读活开关）
        try:
            register_theme_managed(cell, _refresh)
        except Exception:
            pass
        # 首次应用一次（从真实开关态出发，避免初始态错位）
        try:
            _on = _live_switch_on(cell)
            cell._switch_on = _on  # type: ignore[attr-defined]
            cell.setStyleSheet(_switch_qss(name, _on))
        except Exception:
            pass
    except Exception:
        pass
    return cell


def prefer_cell_qss(on):
    """主页拦截格和顶栏开关格使用一致的选中态。"""
    return _switch_qss("preferClearCell", on)


def attach_prefer_cell_refresh(cell):
    """给主页拦截格挂主题感知 _refresh（现算 on/off QSS + 刷文字色）。

    与 attach_header_switch_refresh 同一套边框逻辑，只是态属性叫 _prefer_on
    （拦截格不靠开关拨动，靠 _style(mode) 选中）。切主题时格子自己现算刷新。
    """
    try:
        name = "preferClearCell"

        def _refresh():
            try:
                from PyQt5 import sip
                if sip.isdeleted(cell):
                    return
                _on = bool(getattr(cell, "_prefer_on", False))
                set_style_dedup(cell, _switch_qss(name, _on))
                _apply_switch_labels(cell)
            except Exception:
                pass

        cell._refresh = _refresh  # type: ignore[attr-defined]
        try:
            register_theme_managed(cell, _refresh)
        except Exception:
            pass
    except Exception:
        pass
    return cell


# 标题与说明沿用 QLabel 的原生文字渲染，支持换行、缩放和系统字体。
def themed_tip_fg():
    return QColor(themed_text())


def themed_tip_outline():
    # 兼容旧插件的导入；文字不再绘制描边。
    return QColor(Qt.transparent)


if QLabel is not None:
    class TipLabel(QLabel):
        """工作台分区标题或辅助说明。"""

        def __init__(self, text: str = "", parent=None, *, pixel_size: int = 12, word_wrap: bool = True):
            super().__init__(text or "", parent)
            self._pixel_size = pixel_size
            self.setWordWrap(word_wrap)
            self.setProperty("themeSemanticColor", True)
            if word_wrap:
                self.setMinimumWidth(80)
            font = self.font()
            font.setPixelSize(pixel_size)
            font.setWeight(QFont.DemiBold if pixel_size >= 14 else QFont.Normal)
            self.setFont(font)
            self.setSizePolicy(
                QSizePolicy.Expanding if word_wrap else QSizePolicy.Maximum,
                QSizePolicy.Preferred,
            )
            self._refresh_theme()

        def _refresh_theme(self):
            color = themed_title_text() if self._pixel_size >= 14 else themed_secondary_text()
            set_style_dedup(self, f"background:transparent;border:none;color:{color};")
else:
    TipLabel = None  # type: ignore


def _set_style_if_changed(w, css: str) -> None:
    """仅当样式串真的变化才 setStyleSheet（避免无谓 re-polish 造成切主题卡顿）。"""
    try:
        if (w.styleSheet() or "") != css:
            w.setStyleSheet(css)
    except Exception:
        pass


def set_style_dedup(w, css: str) -> None:
    """公开别名：各控件 _refresh 内部统一用它写样式，主题引擎遍历即零成本。"""
    _set_style_if_changed(w, css)


def apply_full_theme_refresh(widget):
    """统一主题刷新（单遍 findChildren 分桶处理，遍历成本约 1/4）。

    ① QLabel 深灰文字色正则 → ② 输入框/SpinBox/文本域 css →
    ③ QFrame/QListWidget 白底跟随 → ④ 调 _refresh/_refresh_theme/_apply
    （_Section/_NoteCell/绿框选项等统一刷，各页面不用单独补）。
    隐藏的堆叠页（工具大厅里未打开的缓存页）整页跳过，切回当前页时由
    容器补一次全量刷新。init 末尾调一次；
    connect_theme_refresh_full(widget) 接 themeChanged 延迟安全刷。
    """
    try:
        from PyQt5.QtWidgets import (
            QWidget as _QW, QStackedWidget as _QSW, QLabel as _QL,
            QLineEdit as _QLE, QTextEdit as _QTE, QFrame as _QF,
            QListWidget as _QLW,
        )
    except Exception:
        return

    # 隐藏堆叠页跳过集（整页缓存，切回当前页时由容器补刷），4 个桶共用
    _skip = set()
    try:
        for _sw in widget.findChildren(_QSW):
            _cur = _sw.currentWidget()
            for _pg in (_sw.widget(i) for i in range(_sw.count())):
                if _pg is not _cur and _pg is not None:
                    _skip.update(_pg.findChildren(_QW))
                    _skip.add(_pg)
    except Exception:
        _skip = set()

    # 单遍遍历分桶（QLabel/QLineEdit/QTextEdit/QFrame/QListWidget/其余）
    labels, lineeds, texteds, frames, plain = [], [], [], [], []
    for w in widget.findChildren(_QW):
        if w in _skip:
            continue
        if isinstance(w, _QL):
            labels.append(w)
        elif isinstance(w, _QLE):
            lineeds.append(w)
        elif isinstance(w, _QTE):
            texteds.append(w)
        elif isinstance(w, (_QF, _QLW)):
            frames.append(w)
        else:
            plain.append(w)

    txt = themed_text()
    pat = _dark_text_re()
    css = themed_input_css()
    spin_css = themed_spinbox_css()
    _body = themed_section_body_bg()
    import re as _re
    _bg_pat = _re.compile(r"background:#(%s)" % "|".join(_LEGACY_LIGHT_BG_HEX))
    spin_parents = ("SpinBox", "DoubleSpinBox")

    # ① QLabel：深灰文字色正则替换 / 无 color 裸标签补 themed_text
    for w in labels:
        try:
            if w.property("themeSemanticColor"):
                continue
            old = w.styleSheet() or ""
            if pat.search(old):
                _set_style_if_changed(w, pat.sub(f'color:{txt};', old))
            elif "color:" not in old.replace(" ", "").lower():
                _set_style_if_changed(w, (old + " " if old else "") + f"color:{txt};")
        except Exception:
            pass

    # ② 输入框（SpinBox 内的走 spin 外壳）/ 文本域
    for w in lineeds:
        try:
            parent = w.parent()
            if parent is not None and parent.__class__.__name__ in spin_parents:
                _set_style_if_changed(parent, spin_css)
                continue
            _set_style_if_changed(w, css)
        except Exception:
            pass
    for w in texteds:
        try:
            _set_style_if_changed(w, css)
        except Exception:
            pass

    # ③ QFrame/QListWidget 白底跟随（正则替换背景，保留 border/hover/item 态）
    for w in frames:
        try:
            old = w.styleSheet() or ""
            if _bg_pat.search(old):
                w.setStyleSheet(_bg_pat.sub("background:%s" % _body, old))
        except Exception:
            pass

    # ④ 全部 widget：有 _refresh/_refresh_theme/_apply 的统一调
    #    （各 _refresh 内部用 set_style_dedup，内容相同不重设）
    for w in labels + lineeds + texteds + frames + plain:
        fn = None
        for _m in ("_refresh", "_refresh_theme"):
            fn = getattr(w, _m, None)
            if callable(fn):
                break
        if not callable(fn):
            fn = getattr(w, "_apply", None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass


def connect_theme_refresh_full(widget):
    """连 themeChanged，切主题完成后延迟安全刷文字+输入框（widget 删了跳过）。"""
    safe_connect_theme(widget, lambda: apply_full_theme_refresh(widget))


# ── 主页栏位（栏1=标题下 / 栏2=启停下）：所有工具页通用的小单选 ──

def _home_slots_store_path() -> str:
    try:
        import os
        return os.path.join(os.getcwd(), "config", "home_bar_slots.json")
    except Exception:
        return "config/home_bar_slots.json"


def get_home_bar_slot(plugin_id, default=None):
    """读插件主页栏位选择；None=未选过（沿用插件 manifest 声明）。返回 "1"/"2"/default。"""
    try:
        import json, os
        p = _home_slots_store_path()
        if not os.path.isfile(p):
            return default
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        v = str((data or {}).get(str(plugin_id), "") or "")
        return v if v in ("1", "2") else default
    except Exception:
        return default


_home_slot_listeners = []


def on_home_bar_slot_change(fn):
    """订阅栏位变化：fn(plugin_id, "1"|"2")。主页用它即时重挂插件条。"""
    try:
        if fn not in _home_slot_listeners:
            _home_slot_listeners.append(fn)
    except Exception:
        pass


def set_home_bar_slot(plugin_id, slot):
    """写插件主页栏位选择（"1"=标题下 / "2"=启停下）并广播给主页。"""
    try:
        import json, os
        p = _home_slots_store_path()
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
        data = {}
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        if str(slot) in ("1", "2"):
            data[str(plugin_id)] = str(slot)
        else:
            data.pop(str(plugin_id), None)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[tool_style] save home slot failed:", e)
    for fn in list(_home_slot_listeners):
        try:
            fn(str(plugin_id), str(slot))
        except Exception:
            pass


def make_home_bar_slot_cell(plugin_id, parent=None):
    """主页入口的显示位置；选择持久化并即时刷新主页。"""
    if QLabel is None or Qt is None:
        return None
    try:
        from PyQt5.QtWidgets import QFrame, QHBoxLayout
    except Exception:
        return None

    pid = str(plugin_id)

    def _effective_default_slot(p):
        """默认高亮跟随插件 manifest 实际声明（below_startup=第二栏），
        不写死"第一栏"——写死会让用户点已亮的第一栏时早退、永远写不进。"""
        try:
            from module.tools.registry import get_registry

            t = get_registry().get(p)
            c = t.get_home_contribution() if t is not None else None
            if c is not None and str(getattr(c, "slot", "")) == "below_startup":
                return "2"
        except Exception:
            pass
        return "1"

    state = {"slot": get_home_bar_slot(pid) or _effective_default_slot(pid)}

    try:
        from qfluentwidgets import ComboBox
    except ImportError:
        from PyQt5.QtWidgets import QComboBox as ComboBox

    cell = QFrame(parent)
    cell.setObjectName("homeBarSlotCell")
    cell.setFixedHeight(36)
    row = QHBoxLayout(cell)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(10)
    caption = QLabel("显示位置", cell)
    caption.setProperty("themeSemanticColor", True)
    row.addWidget(caption)

    def _refresh_caption():
        caption.setStyleSheet(f"font-size:13px;color:{themed_text()};background:transparent;")

    _refresh_caption()
    safe_connect_theme(caption, _refresh_caption)
    position = ComboBox(cell)
    position.setObjectName("homeBarPosition")
    position.addItems(["标题下方", "启动栏下方"])
    position.setFixedSize(140, 34)
    position.setAccessibleName("主页入口显示位置")
    position.setToolTip("选择工具快捷入口在主页中的显示位置")
    position.setCurrentIndex(0 if state["slot"] == "1" else 1)
    row.addWidget(position)

    def _pick(index):
        slot = "1" if index == 0 else "2"
        if slot != state["slot"]:
            state["slot"] = slot
            set_home_bar_slot(pid, slot)

    position.currentIndexChanged.connect(_pick)
    return cell
