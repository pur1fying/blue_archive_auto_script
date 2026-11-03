# -*- coding: utf-8 -*-
"""工具注册表：扫 module/tools/*/manifest.json 并实例化插件。"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from module.tools.base import HomeContribution, ToolManifest, ToolPlugin, resolve_dotted, _cfg_bool

logger = logging.getLogger("baas.tools")

_REGISTRY: Optional["ToolRegistry"] = None

# ── 插件启用状态 / 标签覆盖（工具大厅「工具启用与修改」持久化） ──
_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "tool_plugin_state.json"


def load_tool_state() -> dict:
    """读取插件启用状态与标签覆盖（disabled: [id], labels: {id: 名}）。"""
    try:
        if _STATE_FILE.is_file():
            data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_tool_state(state: dict) -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def disabled_tool_ids() -> set:
    st = load_tool_state()
    d = st.get("disabled")
    return {str(x) for x in d} if isinstance(d, list) else set()


def is_tool_enabled(tool_id: str) -> bool:
    return str(tool_id) not in disabled_tool_ids()


def deleted_tool_ids() -> set:
    st = load_tool_state()
    d = st.get("deleted")
    return {str(x) for x in d} if isinstance(d, list) else set()


def is_tool_deleted(tool_id: str) -> bool:
    return str(tool_id) in deleted_tool_ids()


def tool_available(tool_id: str) -> bool:
    """插件整体可用（非启用且未删除）。

    所有"插件接入点"统一查这里：调度函数注册（core.func_dict）、调度事件
    显示（featureSwitch）、执行体入口（executor.implement）、未来任何
    注册型接入（如商店份额注册）。插件只要非启用/删除，接入点即视为
    不存在——与 UI 皮肤无关，整插件从软件行为中消失。
    """
    tid = str(tool_id)
    return tid not in disabled_tool_ids() and tid not in deleted_tool_ids()


def get_tool_label_override(tool_id: str) -> str:
    st = load_tool_state()
    labels = st.get("labels")
    if isinstance(labels, dict):
        v = labels.get(tool_id)
        return str(v).strip() if v else ""
    return ""


def get_tool_tags_override(tool_id: str) -> str:
    """标签（徽章）覆盖，逗号分隔串；""=用清单默认。"""
    st = load_tool_state()
    tags = st.get("tags")
    if isinstance(tags, dict):
        v = tags.get(tool_id)
        return str(v).strip() if v else ""
    return ""


def set_tool_state(
    tool_id: str,
    enabled: Optional[bool] = None,
    label: Optional[str] = None,
    deleted: Optional[bool] = None,
    tags: Optional[str] = None,
) -> None:
    """写单个插件状态。

    enabled=False 非启用：插件保留、卡片灰显、主页贡献隐藏，但不参与执行；
    deleted=True 删除：从注册表屏蔽（大厅/主页/入口全部不再出现），可恢复；
    label/tags 传 "" 清除覆盖（回清单默认）。
    """
    st = load_tool_state()
    dis = {str(x) for x in (st.get("disabled") or [])}
    dels = {str(x) for x in (st.get("deleted") or [])}
    labels = {str(k): str(v) for k, v in (st.get("labels") or {}).items()}
    tagmap = {str(k): str(v) for k, v in (st.get("tags") or {}).items()}
    if enabled is True:
        dis.discard(str(tool_id))
    elif enabled is False:
        dis.add(str(tool_id))
    if deleted is True:
        dels.add(str(tool_id))
    elif deleted is False:
        dels.discard(str(tool_id))
    if label is not None:
        label = str(label).strip()
        if label:
            labels[str(tool_id)] = label
        else:
            labels.pop(str(tool_id), None)
    if tags is not None:
        tags = str(tags).strip()
        if tags:
            tagmap[str(tool_id)] = tags
        else:
            tagmap.pop(str(tool_id), None)
    st["disabled"] = sorted(dis)
    st["deleted"] = sorted(dels)
    st["labels"] = labels
    st["tags"] = tagmap
    save_tool_state(st)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolPlugin] = {}
        self._errors: Dict[str, str] = {}

    @property
    def errors(self) -> Dict[str, str]:
        return dict(self._errors)

    def register(self, tool: ToolPlugin) -> None:
        self._tools[tool.id] = tool
        # 标签覆盖（用户在工具大厅改的名字）持久生效
        try:
            ov = get_tool_label_override(tool.id)
            if ov:
                tool._label_override = ov
        except Exception:
            pass

    def get(self, tool_id: str) -> Optional[ToolPlugin]:
        return self._tools.get(tool_id)

    def _sorted_all(self) -> List[ToolPlugin]:
        def _safe_key(t):
            try:
                return (getattr(t, "order", 0), getattr(t, "name", getattr(t, "id", "")))
            except Exception:
                return (0, "")
        return sorted(self._tools.values(), key=_safe_key)

    def list_all_tools(self) -> List[ToolPlugin]:
        """全部插件（含未启用）——工具大厅编辑模式用。"""
        return self._sorted_all()

    def list_tools(self) -> List[ToolPlugin]:
        """在册插件（含非启用，不含已删除）。

        非启用 = 仍在大厅/仍可打开（灰显、不参与执行）；已删除 = 大厅/
        主页/入口全部不再出现，可经「恢复已删除插件」找回。
        """
        dels = deleted_tool_ids()
        return [t for t in self._sorted_all() if t.id not in dels]

    def list_lobby_tools(self) -> List[ToolPlugin]:
        return [t for t in self.list_tools() if t.show_in_lobby]

    def list_home_contributions(
        self, config=None
    ) -> List[Tuple[ToolPlugin, HomeContribution]]:
        items: List[Tuple[ToolPlugin, HomeContribution]] = []
        dis = disabled_tool_ids()
        for t in self.list_tools():
            # 非启用插件的主页贡献（板块/入口）不再出现
            if t.id in dis:
                continue
            c = t.get_home_contribution()
            if c is None:
                # 未声明 home 的插件：框架自动发一个主页入口（零插件代码）。
                # 声明了 home 的插件用自家板块，不重复发。
                c = HomeContribution(
                    slot="below_title", order=100, widget="__auto_entry__"
                )
            try:
                if not t.home_visible(config):
                    continue
            except Exception:
                continue
            # 框架级「主页显示」总开关（tool_<id>_home_visible，默认开）：
            # 所有插件统一拥有，与插件自身的 home_visible 逻辑取与；
            # 关闭后主页板块即时摘除（设置栏开关 → _refresh_home_live）。
            if not _cfg_bool(config, f"{t.config_prefix}home_visible", True):
                continue
            items.append((t, c))
        items.sort(key=lambda x: (x[1].slot, x[1].order, x[0].name))
        return items

    def load_all(self, root: Optional[Path] = None) -> "ToolRegistry":
        base = root or Path(__file__).resolve().parent
        if not base.is_dir():
            return self
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("_") or child.name.startswith("."):
                continue
            manifest_path = child / "manifest.json"
            if not manifest_path.is_file():
                continue
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest = ToolManifest.from_dict(data)
                if not manifest.id:
                    raise ValueError("manifest.id required")
                # kind=local 禁止 intercept
                if manifest.kind == "local" and manifest.intercept:
                    logger.warning("tool %s is local but declares intercept; ignored", manifest.id)
                    manifest.intercept = None
                # kind=scheduler 必须带 scheduler 节，否则挂不上调度=静默失效，
                # 直接判为加载失败（大厅出现禁用卡，作者可见）
                if manifest.kind == "scheduler" and not manifest.scheduler:
                    raise ValueError("kind=scheduler 需要声明 scheduler 节（event_name/func_name），见 docs/PLUGIN_GUIDE.md")
                if manifest.scheduler and manifest.kind != "scheduler":
                    logger.warning("tool %s declares scheduler but kind=%s; ignored", manifest.id, manifest.kind)
                    manifest.scheduler = None
                entry = manifest.entry or f"module.tools.{child.name}.tool:Tool"
                cls_or_factory = resolve_dotted(entry)
                if isinstance(cls_or_factory, type):
                    tool = cls_or_factory(manifest)
                else:
                    tool = cls_or_factory(manifest)
                if not isinstance(tool, ToolPlugin):
                    raise TypeError(f"{entry} is not a ToolPlugin")
                self.register(tool)
            except Exception as e:
                tid = child.name
                self._errors[tid] = str(e)
                logger.warning("tool load failed %s: %s", tid, e)
        return self


def get_registry(reload: bool = False) -> ToolRegistry:
    global _REGISTRY
    if _REGISTRY is None or reload:
        _REGISTRY = ToolRegistry().load_all()
    return _REGISTRY
