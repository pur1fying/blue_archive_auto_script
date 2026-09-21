# -*- coding: utf-8 -*-
from __future__ import annotations

from module.tools.base import ToolPlugin, resolve_dotted, _cfg_bool


class AssetsDisplayTool(ToolPlugin):
    def build_widget(self, parent=None, config=None):
        ui = self.manifest.ui or "module.tools.assets_display.ui:Layout"
        Layout = resolve_dotted(ui)
        try:
            return Layout(parent, config)
        except TypeError:
            return Layout(config=config)

    def build_home_widget(self, parent=None, config=None):
        if not self.home_visible(config):
            return None
        # 复用已建实例:上游 start_patch 有防重复 flag,二次重建会跳过补丁
        # → 资产条从横向变纵向。复用已打补丁的实例,保留横向布局。
        w = getattr(self, "_assets_widget", None)
        if w is None:
            try:
                from gui.util.customized_ui import AssetsWidget
            except Exception:
                return None
            w = AssetsWidget(config, parent)
            try:
                w.start_patch()
            except Exception as e:
                print("[assets_display] start_patch 失败，资产条按未打补丁显示:", e)
            self._assets_widget = w
        # 上游同款结构：AssetsWidget 外包一层普通布局容器再交给主页槽位
        # （上游 handler_for_logger 即 QHBoxLayout 直挂）。主页整行槽计算行高
        # 时会调 widget.layout().heightForWidth()——AssetsWidget 用
        # self.layout = FlowLayout(...) 属性遮蔽了 QWidget.layout() 方法，
        # 直接挂会让行高计算抛异常走兜底，出现裁第二行或撑出大片空白。
        try:
            w.setParent(None)
        except Exception:
            pass
        try:
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
            host = QWidget(parent)
            hl = QVBoxLayout(host)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(0)
            hl.addWidget(w)
            # 水平 Expanding：槽给满宽，货币格从左到右排；垂直 Maximum：
            # 高度交给 hfw 精确计算，不多占
            host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            host.setMinimumWidth(0)
            old = getattr(self, "_assets_host", None)
            self._assets_host = host
            if old is not None:
                try:
                    old.deleteLater()
                except Exception:
                    pass
            try:
                w.show()
            except Exception:
                pass
            return host
        except Exception:
            return w

    def home_visible(self, config) -> bool:
        # 以 assetsVisibility 为主（主页开关记忆键）；兼容 tool_assets_enabled
        try:
            inner = getattr(config, "config", None) if config is not None else None
            if inner is not None and hasattr(inner, "assetsVisibility"):
                return _cfg_bool(config, "assetsVisibility", True)
        except Exception:
            pass
        if not _cfg_bool(config, "tool_assets_enabled", True):
            return False
        return _cfg_bool(config, "assetsVisibility", True)

    def is_enabled(self, config) -> bool:
        # 工具本身始终可用；显示与否看 home_visible / assetsVisibility
        return True
