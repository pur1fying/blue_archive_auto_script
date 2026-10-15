# -*- coding: utf-8 -*-
"""自动推图：把「推未通关新图」相关设置整块收一页。

对应设置里四块（读写同一套配置键）：
  - 编队配置 formationConfig（一张表完成一切：侧栏 / 预设1-4，checkbox 点亮）
  - 推图设置 exploreConfig（未通关推图，不是日常扫荡）+「推当前页面剧情/
    推当前页面关卡」按钮行（功能已从设置页整体插件化，逻辑在 push_current.py，
    上游保持干净）
  - 推剧情 proceedPlot
  - 活动图设置 eventMapConfig

不包含 mainlinePriority / hardPriority 日常扫荡串。
"""
from __future__ import annotations

from core.utils import detach
from module.tools.base import _cfg_bool, _cfg_set
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QSizePolicy,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)


from gui.components.expand.tool_style import (
    TipLabel,
    apply_full_theme_refresh,
    make_icon_button,
    themed_note_bg,
    themed_note_border,
    themed_text,
    themed_workspace_tabs_css,
)


_TipLabel = TipLabel  # 从 tool_style 统一提取,主题感知(深色白字黑描边)


class _Sec(QFrame):
    """蓝标题栏 + 清新内容区，与囤体/装备一致。"""

    def _refresh(self):
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, self._sec_css())
        except Exception:
            pass

    def __init__(self, title: str, tip: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("autoPushSec")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(self._sec_css())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        head = QFrame(self)
        head.setObjectName("autoPushHead")
        hl = QVBoxLayout(head)
        hl.setContentsMargins(16, 12, 16, 12)
        hl.setSpacing(6)
        # 标题文字：近黑粗体 + 白描边（与说明文字同款画法，大一号）
        lab = _TipLabel(title, head, pixel_size=14, word_wrap=False)
        lab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lab.setAlignment(Qt.AlignCenter)
        hl.addWidget(lab)
        if tip:
            t = _TipLabel(tip, head)
            t.setAlignment(Qt.AlignCenter)
            hl.addWidget(t)
        root.addWidget(head)

        body = QFrame(self)
        body.setObjectName("autoPushBody")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(16, 12, 16, 16)
        self.body.setSpacing(10)
        root.addWidget(body)

    @staticmethod
    def _sec_css() -> str:
        """大框(标题栏+内容)：主题引擎统一工厂，不再自造。"""
        from gui.components.expand.tool_style import themed_section_css

        return themed_section_css("autoPushSec", "autoPushHead", "autoPushBody")

    def _refresh(self):
        try:
            from gui.components.expand.tool_style import set_style_dedup

            set_style_dedup(self, self._sec_css())
        except Exception:
            pass

    def add_inner(self, widget: QWidget):
        try:
            widget.setMinimumHeight(0)
            sp = widget.sizePolicy()
            sp.setVerticalPolicy(QSizePolicy.Maximum)
            widget.setSizePolicy(sp)
        except Exception:
            pass
        try:
            widget.setStyleSheet((widget.styleSheet() or "") + "background:transparent;")
        except Exception:
            pass
        self.body.addWidget(widget)
        return widget


def _embed(module_name: str, config, parent) -> QWidget:
    """按模块名加载设置页 Layout；失败时给可读占位。"""
    try:
        import importlib

        mod = importlib.import_module("gui.components.expand.%s" % module_name)
        Layout = getattr(mod, "Layout")
        w = Layout(parent=parent, config=config)
        return w
    except Exception as e:
        box = QFrame(parent)
        box.setStyleSheet(
            f"QFrame{{background:{themed_note_bg()};border:1px solid {themed_note_border()};"
            "border-radius:8px;}"
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 10, 12, 10)
        msg = QLabel(
            "未能载入「%s」面板：%s\n请确认安装完整后重开本工具。" % (module_name, e),
            box,
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f'font-size:13px;color:{themed_text()};'
        )
        lay.addWidget(msg)
        return box


def _drop_stale_adb(serial):
    """init 失败重试前，用 BAAS 自己的 adbutils 封装断开该 serial 的僵尸连接。

    针对 WinError 10054（连接重置）：模拟器重启后 adb 服务器里的旧条目
    显示 connected 但 shell 即断。只对已有 server 发 disconnect 命令，
    不杀 server、不开新进程（BAAS 的 adb 操作同走这一个 server）。
    """
    try:
        from adbutils import adb

        if not serial:
            return
        adb.disconnect(serial)  # raise_error=False：条目不存在时静默
    except Exception:
        pass


def _migrate_legacy_formation_mode(config):
    """一次性迁移：表格旧版写进上游键的 "default" 回到上游合法值。

    上游编队面板（设置页）只认 preset/side/order；"default"（表格全空=
    用当前队伍）的语义已改经 team_config["keep_current"] 标记传递。
    """
    try:
        if config is not None and hasattr(config, "get") and config.get("choose_team_method") == "default":
            _cfg_set(config, "choose_team_method", "preset")
    except Exception:
        pass


def _embed_formation(config, parent) -> QWidget:
    """插件私有编队表格（一张表完成一切：侧栏 / 预设1-4）。

    表格版已从共享 formationConfig 搬进插件（formation_table.py）；
    设置页的上游三模式面板保持干净。失败时给可读占位。
    """
    _migrate_legacy_formation_mode(config)
    try:
        from module.tools.auto_push.formation_table import Layout as _FormationTable

        return _FormationTable(parent=parent, config=config)
    except Exception as e:
        box = QFrame(parent)
        box.setStyleSheet(
            f"QFrame{{background:{themed_note_bg()};border:1px solid {themed_note_border()};"
            "border-radius:8px;}"
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 10, 12, 10)
        msg = QLabel("未能载入编队表格：%s" % e, box)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f'font-size:13px;color:{themed_text()};'
        )
        lay.addWidget(msg)
        return box


def _run_current_push(main, kind):
    """在 detach 线程里驱动推当前页面（逻辑全部在插件 push_current.py，上游零改动）。

    main: gui.fragments.home.MainThread（经 config.get_main_thread() 取得）；
    kind: 'story'（剧情引擎）| 'stage'（关卡引擎，复刻上游任务循环）。
    """
    import time as _time

    from core.notification import notify
    baas = None
    label = '当前页面剧情' if kind == 'story' else '当前页面关卡'
    try:
        ok = main._init_script()
        if not ok:
            # adb 偶发连接重置（WinError 10054，list_packages 不重试该类错误）：
            # 断开僵尸连接后隔 2 秒重试一次
            try:
                cfg = main.config
                serial = cfg.get("serial") if hasattr(cfg, "get") else getattr(cfg, "serial", None)
                _drop_stale_adb(serial)
            except Exception:
                pass
            _time.sleep(2)
            ok = main._init_script()
        if not ok:
            notify(title='BAAS', body=label + '：设备初始化失败，请检查模拟器与 adb 连接')
            return
        baas = main._main_thread
        main.update_signal.emit([label])
        main.display('停止')
        from module.tools.auto_push import push_current
        if kind == 'story':
            done = push_current.push_current_story(baas)
        else:
            done = push_current.push_current_stage(baas)
        if done and baas.flag_run:
            notify(title='BAAS', body=label + '推图已完成')
        elif baas.flag_run:
            # 静默失败不再是"没反应"：给出可行动的提示
            if kind == 'stage':
                notify(title='BAAS',
                       body=label + '：未推任何关卡——当前页面没有可识别的蓝色入场按钮，'
                                    '请把游戏停在选关页/活动图等有入场按钮的页面后重试'
                                    '（详见日志与 log/ 调试截图）')
            else:
                notify(title='BAAS',
                       body=label + '：未识别剧情画面——请把游戏停在剧情选章/选话页后重试'
                                    '（详见日志与 log/ 下调试截图）')
    except Exception as e:
        try:
            from core.exception import RequestHumanTakeOver
            stopped = isinstance(e, RequestHumanTakeOver)
        except Exception:
            stopped = False
        if stopped:
            try:
                if baas is not None:
                    baas.logger.info("Human take over.")
            except Exception:
                pass
        else:
            try:
                if baas is not None:
                    baas.logger.error("当前页面推图异常: %s" % e)
            except Exception:
                pass
            print("[auto_push] 当前页面推图异常:", e)
            notify(title='BAAS', body=label + '推图异常: %s' % e)
    finally:
        try:
            main.update_signal.emit(['无任务'])
            main.display('启动')
        except Exception:
            pass


class Layout(QWidget):
    def __init__(self, parent=None, config=None, **kwargs):
        super().__init__(parent)
        self.config = config
        self.setObjectName("autoPushLayout")
        from gui.components.expand.tool_style import themed_page_transparent_qss

        self.setStyleSheet(themed_page_transparent_qss("autoPushLayout"))
        self._header_settings_cells = []

        # 顶栏：主页显示
        cell = self._build_home_entry_cell()
        if cell is not None:
            self._header_settings_cells.append(cell)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(0)

        self.workspace = QTabWidget(self)
        self.workspace.setObjectName("autoPushWorkspace")
        self.workspace.setDocumentMode(True)
        self._build_sections(self.workspace)
        def _refresh_tabs():
            self.workspace.setStyleSheet(themed_workspace_tabs_css("autoPushWorkspace"))
        self.workspace._refresh = _refresh_tabs
        self.workspace.currentChanged.connect(
            lambda _index: apply_full_theme_refresh(self.workspace.currentWidget()))
        _refresh_tabs()
        root.addWidget(self.workspace, 1)

        # 深色模式适配（统一刷：labels/输入框/QFrame白底/_Sec._refresh 等）
        if apply_full_theme_refresh is not None:
            apply_full_theme_refresh(self)
            # 主题统一由工具页容器（ToolsFragment connect_theme_refresh_full）遍历刷新；
            # 页面根不再重复注册/连接，避免一次切换多重遍历造成卡顿。


    def _build_home_entry_cell(self):
        """顶栏「主页显示」开关格子；无 SwitchButton 时返回 None。"""
        try:
            from qfluentwidgets import SwitchButton
        except Exception:
            SwitchButton = None  # type: ignore
        self.sw_home_entry = SwitchButton(self) if SwitchButton else None
        if self.sw_home_entry is None:
            return None
        try:
            self.sw_home_entry.setOnText("开")
            self.sw_home_entry.setOffText("关")
        except Exception:
            pass
        try:
            self.sw_home_entry.setMinimumWidth(56)
        except Exception:
            pass
        on = _cfg_bool(self.config, "tool_auto_push_home_entry", False)
        try:
            self.sw_home_entry.blockSignals(True)
            self.sw_home_entry.setChecked(bool(on))
            self.sw_home_entry.blockSignals(False)
        except Exception:
            pass
        self.sw_home_entry.setToolTip("主页显示：在主页放「进入自动推图」入口")
        self.sw_home_entry.checkedChanged.connect(self._on_home_entry_changed)
        # 四页统一实现（tool_style.make_header_setting_cell）
        from gui.components.expand.tool_style import make_header_setting_cell

        cell = make_header_setting_cell(
            "主页显示", self.sw_home_entry,
            obj_name="autoPushHeaderSetting", min_w=78,
        )
        return cell

    def _build_sections(self, tabs):
        """按执行场景分开工作区，每页只保留当前任务需要的控件。"""
        from gui.components.expand.tool_style import themed_scrollbar_qss
        def page(title):
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}" + themed_scrollbar_qss())
            scroll.viewport().setStyleSheet("background:transparent;")
            body = QWidget()
            body.setStyleSheet("background:transparent;")
            layout = QVBoxLayout(body)
            layout.setContentsMargins(0, 12, 4, 12)
            layout.setSpacing(12)
            layout.setAlignment(Qt.AlignTop)
            scroll.setWidget(body)
            tabs.addTab(scroll, title)
            return body, layout

        main, layout = page("主线任务")
        section = _Sec("推未通关关卡", "填写目标关卡后执行；队伍可在「编队设置」调整。", main)
        self.w_explore = _embed("exploreConfig", self.config, section)
        self._compact_template(self.w_explore)
        section.add_inner(self.w_explore)
        layout.addWidget(section)
        layout.addStretch(1)

        team, layout = page("编队设置")
        section = _Sec("选择战斗队伍", "勾选队伍并设置属性；全部不选时沿用当前队伍。", team)
        self.w_form = _embed_formation(self.config, section)
        section.add_inner(self.w_form)
        layout.addWidget(section)
        layout.addStretch(1)

        current, layout = page("当前页面")
        section = _Sec("从当前游戏页面继续", "先打开游戏内的选章页或选关页，再启动对应任务。", current)
        section.body.addWidget(self._build_current_push_row(section))
        layout.addWidget(section)
        layout.addStretch(1)

        plot, layout = page("剧情任务")
        section = _Sec("推进剧情", "选择要推进的剧情类型。", plot)
        self.w_plot = _embed("proceedPlot", self.config, section)
        self._compact_template(self.w_plot)
        section.add_inner(self.w_plot)
        layout.addWidget(section)
        layout.addStretch(1)

        event, layout = page("活动任务")
        section = _Sec("当期活动", "活动故事、任务与挑战。", event)
        self.w_event = _embed("eventMapConfig", self.config, section)
        self._compact_template(self.w_event)
        section.add_inner(self.w_event)
        layout.addWidget(section)
        layout.addStretch(1)

    @staticmethod
    def _compact_template(widget):
        """复用原表单与接线，移除通用设置页为独立大页面保留的空白。"""
        from qfluentwidgets import LineEdit, SwitchButton
        names = {
            "是否手动boss战": "手动完成 BOSS 战",
            "使用简易模式推图": "简易模式",
            "普通图推图设置": "普通关卡",
            "困难图推图设置": "困难关卡",
        }
        for label in widget.findChildren(QLabel):
            if label.text() in names:
                label.setText(names[label.text()])
        for switch in widget.findChildren(SwitchButton):
            switch.setOnText("开")
            switch.setOffText("关")
        layout = getattr(widget, "vBoxLayout", None)
        if layout is not None:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(14)
            layout.setAlignment(Qt.AlignTop)
            if layout.count() and layout.itemAt(0).spacerItem() is not None:
                layout.takeAt(0)
        for edit in widget.findChildren(LineEdit):
            edit.setMinimumWidth(100)
            edit.setMaximumWidth(16777215)
            edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if layout is not None:
            for index in range(layout.count()):
                row = layout.itemAt(index).layout()
                if row is None:
                    continue
                for item_index in range(row.count()):
                    item = row.itemAt(item_index)
                    if item.widget() is not None and isinstance(item.widget(), LineEdit):
                        row.setAlignment(item.widget(), Qt.AlignVCenter)
                        row.setStretch(item_index, 1)

    def _build_current_push_row(self, parent):
        """保留原任务入口与信号，用独立设置行说明两个执行目标。"""
        from qfluentwidgets import FluentIcon
        host = QWidget(parent)
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        for title, hint, button_text, action in (
            ("剧情页面", "自动识别可开始的剧情，逐个推进。", "开始推剧情", self._action_push_current_story),
            ("关卡页面", "自动识别入场按钮，跳过已通关关卡。", "开始推关卡", self._action_push_current_stage),
        ):
            row = QHBoxLayout()
            text = QVBoxLayout()
            text.setSpacing(4)
            label = QLabel(title, host)
            label.setStyleSheet("font-size:14px;font-weight:600;")
            description = _TipLabel(hint, host)
            text.addWidget(label)
            text.addWidget(description)
            row.addLayout(text, 1)
            button = make_icon_button(
                FluentIcon.PLAY, button_text + "\n" + hint + "先手动停在对应游戏页面；执行时不返回主页。",
                host, primary=True)
            button.clicked.connect(action)
            row.addWidget(button)
            layout.addLayout(row)
        return host

    def _publish_live_config(self):
        """执行前把卡片对话框注入的 ConfigDraft 落盘并切回 live ConfigSet。"""
        cfg = self.config
        try:
            from gui.util.config_draft import ConfigDraft, as_live
            if isinstance(cfg, ConfigDraft):
                cfg.flush_and_commit(self)
                return as_live(cfg)
        except Exception:
            pass
        return cfg

    @detach
    def _action_push_current_story(self):
        self._start_current_push("story")

    @detach
    def _action_push_current_stage(self):
        self._start_current_push("stage")

    def _start_current_push(self, kind):
        live = self._publish_live_config()
        try:
            main = live.get_main_thread()
        except Exception:
            main = None
        from gui.util import notification
        if main is None:
            notification.error(self.tr('推当前页面剧情'),
                               self.tr('请先在主页完成一次启动以连接设备'), live)
            return
        _run_current_push(main, kind)

    def header_settings_widgets(self):
        cells = list(getattr(self, "_header_settings_cells", []) or [])
        # 主页栏位单选（第一栏=标题下 / 第二栏=启停下），绿框样式，全页通用
        try:
            from gui.components.expand.tool_style import make_home_bar_slot_cell
            _slot = make_home_bar_slot_cell("auto_push")
            if _slot is not None:
                cells.append(_slot)
        except Exception as e:
            print("[auto_push] home slot cell failed:", e)
        return cells

    def _on_home_entry_changed(self, checked: bool = False):
        try:
            on = (
                bool(self.sw_home_entry.isChecked())
                if self.sw_home_entry is not None
                else bool(checked)
            )
        except Exception:
            on = bool(checked)
        _cfg_set(self.config, "tool_auto_push_home_entry", on)
        # 即时刷新主页入口
        try:
            win = (
                self.config.get_window()
                if self.config is not None and hasattr(self.config, "get_window")
                else None
            )
            if win is None:
                return
            for h in getattr(win, "_sub_list", [[]])[0]:
                if getattr(h, "config", None) is not self.config:
                    continue
                if hasattr(h, "refresh_home_plugins"):
                    h.refresh_home_plugins()
        except Exception as e:
            print("[auto_push] refresh home failed:", e)
