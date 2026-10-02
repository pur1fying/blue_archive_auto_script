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
    QSizePolicy,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)


from gui.components.expand.tool_style import (
    TipLabel,
    apply_full_theme_refresh,
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
        # 标题 + 说明同一行（与其他插件一致）；间距由主题引擎 TipLabel 自身留白统一管
        hl = QHBoxLayout(head)
        hl.setContentsMargins(14, 8, 14, 8)
        hl.setSpacing(6)
        # 标题文字：近黑粗体 + 白描边（与说明文字同款画法，大一号）
        lab = _TipLabel(title, head, pixel_size=16, word_wrap=False)
        hl.addWidget(lab, 0)
        if tip:
            t = _TipLabel(tip, head)
            hl.addWidget(t, 1)
        else:
            hl.addStretch(1)
        root.addWidget(head)

        body = QFrame(self)
        body.setObjectName("autoPushBody")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(10, 6, 10, 10)
        self.body.setSpacing(6)
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
            "QFrame{background:rgba(255,240,240,180);border:1px dashed #c66;"
            "border-radius:6px;}"
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 10, 12, 10)
        msg = QLabel(
            "未能载入「%s」面板：%s\n请确认安装完整后重开本工具。" % (module_name, e),
            box,
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:700;color:#622;'
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
            "QFrame{background:rgba(255,240,240,180);border:1px dashed #c66;"
            "border-radius:6px;}"
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 10, 12, 10)
        msg = QLabel("未能载入编队表格：%s" % e, box)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            'font-family:"Microsoft YaHei";font-size:12px;font-weight:700;color:#622;'
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

        scroll = QScrollArea(self)
        scroll.setObjectName("autoPushScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        from gui.components.expand.tool_style import (
            themed_page_transparent_qss,
            themed_scrollbar_qss,
        )

        scroll.setStyleSheet(
            themed_page_transparent_qss("autoPushScroll") + themed_scrollbar_qss()
        )
        try:
            scroll.viewport().setStyleSheet("background:transparent;")
        except Exception:
            pass

        body = QWidget()
        body.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(0, 4, 4, 12)
        bl.setSpacing(12)
        bl.setAlignment(Qt.AlignTop)

        # 四个设置块（编队 / 推未通关图 / 推剧情 / 活动图）
        self._build_sections(bl)

        bl.addStretch(1)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

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

    def _build_sections(self, lay):
        """四个设置块（编队 / 推未通关图 / 推剧情 / 活动图）。"""
        config = self.config

        # 1) 编队（插件私有表格：一张表完成一切：侧栏 / 预设1-4）
        sec_form = _Sec(
            "编队",
            "可设置对应队伍里的属性。侧栏为战斗界面左边的从上到下的1234队。"
            "预设为游戏内的预设队伍。队伍均单独可选。"
            "不选择则使用当前战斗界面设置的队伍战斗。",
            self,
        )
        self.w_form = _embed_formation(config, sec_form)
        sec_form.add_inner(self.w_form)
        lay.addWidget(sec_form)

        # 2) 推未通关图（内嵌 exploreConfig 面板 + 大厅引擎的「推当前页面」按钮行）
        sec_explore = _Sec(
            "推未通关图",
            "填要推的普通图 / 困难图，再点执行。简易模式适合人少；手动 BOSS 会进关后停等你手操。",
            self,
        )
        self.w_explore = _embed("exploreConfig", config, sec_explore)
        sec_explore.add_inner(self.w_explore)
        sec_explore.body.addWidget(self._build_current_push_row(sec_explore))
        lay.addWidget(sec_explore)

        # 3) 推剧情
        sec_plot = _Sec(
            "推剧情",
            "主线章节数 + 主线 / 小组 / 支线一键开推。",
            self,
        )
        self.w_plot = _embed("proceedPlot", config, sec_plot)
        sec_plot.add_inner(self.w_plot)
        lay.addWidget(sec_plot)

        # 4) 活动图
        sec_event = _Sec(
            "活动图",
            "当期活动故事 / 任务 / 挑战；下方属性表帮助你对照带队。",
            self,
        )
        self.w_event = _embed("eventMapConfig", config, sec_event)
        sec_event.add_inner(self.w_event)
        lay.addWidget(sec_event)

    def _build_current_push_row(self, parent):
        """「推当前页面剧情 / 推当前页面关卡」按钮行（挂在「推未通关图」分组内）。

        逻辑全部在插件 push_current.py（工具大厅自包含，上游保持干净）：
        先手动停在剧情选章/选话页或选关页再点执行，不回主页。
        """
        row = QFrame(parent)
        row.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)
        try:
            # 蓝色功能按钮（与「执行」同款 Primary）
            from qfluentwidgets import PrimaryPushButton as PushButton
        except Exception:
            from PyQt5.QtWidgets import QPushButton as PushButton
        btn_story = PushButton("推当前页面剧情", row)
        btn_stage = PushButton("推当前页面关卡", row)
        btn_story.setToolTip("先手动停在剧情选章/选话页（含当期活动故事页）再点；不回主页，自动在右半屏找可开始的按钮逐个推完")
        btn_stage.setToolTip("把游戏停在选关页/活动图/困难页再点即可，无需任何前置：自动扫描右半屏所有蓝色入场按钮逐个战斗（已通关的自动跳过，剧情页自动跳过）")
        for b in (btn_story, btn_stage):
            try:
                b.setMinimumHeight(30)
            except Exception:
                pass
            rl.addWidget(b, 0)
        rl.addStretch(1)
        try:
            btn_story.clicked.connect(self._action_push_current_story)
            btn_stage.clicked.connect(self._action_push_current_stage)
        except Exception as e:
            print("[auto_push] 当前页面推图按钮接线失败:", e)
        return row

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
