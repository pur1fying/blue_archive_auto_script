"""Editable, fixed-node scheduler dependency graph widgets."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Callable, Iterator, Sequence

from NodeGraphQt import BaseNode, NodeGraph, Port
from NodeGraphQt.constants import PortTypeEnum
from NodeGraphQt.qgraphics.node_base import NodeItem
from NodeGraphQt.qgraphics.node_text_item import NodeTextItem
from PyQt5.QtCore import QCoreApplication, QSignalBlocker, QTimer, pyqtSignal
from PyQt5.QtGui import QHideEvent
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from gui.util.scheduler_graph_store import (
    InvalidRelationship,
    SchedulerErrorCode,
    SchedulerEvent,
    SchedulerGraphError,
    SchedulerGraphStore,
    SchedulerRelationship,
    SchedulerWarning,
    SchedulerWarningCode,
)
from gui.util.translator import baasTranslator as bt


PRE_COLOR = (70, 155, 255)
POST_COLOR = (255, 160, 70)

_ERROR_TEMPLATES = {
    SchedulerErrorCode.EVENT_CONFIG_READ_FAILED: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "无法读取调度事件配置。"
    ),
    SchedulerErrorCode.EVENT_CONFIG_INVALID_ROOT: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度事件配置的格式无效。"
    ),
    SchedulerErrorCode.EVENT_CONFIG_MISSING_FIELDS: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度事件配置缺少必需字段。"
    ),
    SchedulerErrorCode.EVENT_CONFIG_INVALID_FIELDS: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度事件配置包含无效字段值。"
    ),
    SchedulerErrorCode.EVENT_CONFIG_DUPLICATE_TASK: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度事件配置包含重复的任务标识“{func_name}”。"
    ),
    SchedulerErrorCode.INVALID_POSITIONS: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度图布局包含无效的节点坐标。"
    ),
    SchedulerErrorCode.UNKNOWN_TASK: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度任务“{func_name}”不存在于事件配置中。"
    ),
    SchedulerErrorCode.RELATIONSHIP_KIND_INVALID: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度关系类型“{kind}”无效。"
    ),
    SchedulerErrorCode.RELATIONSHIP_TASK_MISSING: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度关系引用了不存在的任务“{func_name}”。"
    ),
    SchedulerErrorCode.RELATIONSHIP_SELF_LINK: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度任务“{func_name}”不能依赖自身。"
    ),
    SchedulerErrorCode.RELATIONSHIP_DUPLICATE: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "任务“{owner_func}”与“{related_func}”之间已存在相同的调度关系。"
    ),
    SchedulerErrorCode.RELATIONSHIP_CYCLE: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "连接任务“{owner_func}”与“{related_func}”会形成循环依赖。"
    ),
    SchedulerErrorCode.PORT_TYPE_MISMATCH: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "只能连接或断开类型匹配的调度关系端口。"
    ),
    SchedulerErrorCode.INVALID_TIME: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "时间格式无效，请使用 YYYY-MM-DD HH:MM:SS。"
    ),
    SchedulerErrorCode.SAVE_FAILED: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度配置保存失败。"
    ),
    SchedulerErrorCode.GRAPH_LOAD_FAILED: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度图加载失败。"
    ),
}

_WARNING_TEMPLATES = {
    SchedulerWarningCode.UNKNOWN_DEPENDENCY: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "任务“{owner_func}”引用了未知的调度依赖“{related_func}”，该关系无法显示。"
    ),
    SchedulerWarningCode.EXISTING_CYCLE: lambda: QCoreApplication.translate(
        "SchedulerGraphView", "调度配置中已存在循环依赖。"
    ),
}


class _ImmutableNodeTextItem(NodeTextItem):
    """Node title item that permits text changes only until it is sealed."""

    def __init__(self, text, parent=None):
        self._sealed_text: str | None = None
        self._restoring_text = False
        self._observed_document = None
        super().__init__(text, parent)

    def _seal_text(self, text: str) -> None:
        if self._sealed_text is not None:
            self._reconcile_sealed_document()
            return
        self._sealed_text = text
        self._reconcile_sealed_document()

    def setPlainText(self, text: str) -> None:
        if self._sealed_text is not None:
            self._reconcile_sealed_document()
            return
        super().setPlainText(text)

    def setHtml(self, html: str) -> None:
        if self._sealed_text is not None:
            self._reconcile_sealed_document()
            return
        super().setHtml(html)

    def setDocument(self, document) -> None:
        if self._sealed_text is not None:
            self._reconcile_sealed_document()
            return
        super().setDocument(document)

    def setTextCursor(self, cursor) -> None:
        if self._sealed_text is not None:
            self._reconcile_sealed_document()
            return
        super().setTextCursor(cursor)

    def document(self):
        self._reconcile_sealed_document()
        return super().document()

    def toPlainText(self) -> str:
        self._reconcile_sealed_document()
        return super().toPlainText()

    def toHtml(self) -> str:
        self._reconcile_sealed_document()
        return super().toHtml()

    def textCursor(self):
        self._reconcile_sealed_document()
        return super().textCursor()

    def boundingRect(self):
        self._reconcile_sealed_document()
        return super().boundingRect()

    def shape(self):
        self._reconcile_sealed_document()
        return super().shape()

    def contains(self, point):
        self._reconcile_sealed_document()
        return super().contains(point)

    def paint(self, painter, option, widget=None) -> None:
        self._reconcile_sealed_document()
        super().paint(painter, option, widget)

    def _reconcile_sealed_document(self) -> None:
        if self._sealed_text is None or self._restoring_text:
            return

        current_document = super().document()
        if current_document is not self._observed_document:
            if self._observed_document is not None:
                try:
                    self._observed_document.contentsChanged.disconnect(
                        self._reconcile_sealed_document
                    )
                except (RuntimeError, TypeError):
                    pass
            current_document.contentsChanged.connect(
                self._reconcile_sealed_document
            )
            self._observed_document = current_document

        if super().toPlainText() == self._sealed_text:
            return

        self._restoring_text = True
        try:
            super().setPlainText(self._sealed_text)
        finally:
            self._restoring_text = False


class _SchedulerTaskNodeItem(NodeItem):
    """Node graphics item whose installed display title cannot be replaced."""

    def __init__(self, name="node", parent=None):
        self._immutable_display_title: str | None = None
        super().__init__(name=name, parent=parent)
        original_text_item = self._text_item
        self._text_item = _ImmutableNodeTextItem(self.name, self)
        original_text_item.setParentItem(None)

    @property
    def name(self):
        return NodeItem.name.fget(self)

    @name.setter
    def name(self, name=""):
        title = self._immutable_display_title
        NodeItem.name.fset(self, title if title is not None else name)

    def _set_immutable_display_title(self, title: str) -> None:
        if self._immutable_display_title is not None:
            self.name = self._immutable_display_title
            return
        self.name = title
        self._immutable_display_title = title
        self._text_item._seal_text(title)


class SchedulerTaskNode(BaseNode):
    __identifier__ = "baas.scheduler"
    NODE_NAME = "Scheduler Task"

    def __init__(self):
        super().__init__(qgraphics_item=_SchedulerTaskNodeItem)
        self._display_title: str | None = None
        self.create_property("func_name", "")
        self._port_labels = {
            "pre_input": QCoreApplication.translate(
                "SchedulerGraphView", "前置任务"
            ),
            "pre_output": QCoreApplication.translate(
                "SchedulerGraphView", "作为前置任务"
            ),
            "post_input": QCoreApplication.translate(
                "SchedulerGraphView", "作为后置任务"
            ),
            "post_output": QCoreApplication.translate(
                "SchedulerGraphView", "后置任务"
            ),
        }

        pre_input = self.add_input(
            self._port_labels["pre_input"], multi_input=True, color=PRE_COLOR
        )
        post_input = self.add_input(
            self._port_labels["post_input"], multi_input=True, color=POST_COLOR
        )
        pre_output = self.add_output(
            self._port_labels["pre_output"], multi_output=True, color=PRE_COLOR
        )
        post_output = self.add_output(
            self._port_labels["post_output"], multi_output=True, color=POST_COLOR
        )

        pre_input.add_accept_port_type(
            self._port_labels["pre_output"], PortTypeEnum.OUT.value, self.type_
        )
        pre_output.add_accept_port_type(
            self._port_labels["pre_input"], PortTypeEnum.IN.value, self.type_
        )
        post_input.add_accept_port_type(
            self._port_labels["post_output"], PortTypeEnum.OUT.value, self.type_
        )
        post_output.add_accept_port_type(
            self._port_labels["post_input"], PortTypeEnum.IN.value, self.type_
        )

        enabled_label = QCoreApplication.translate(
            "SchedulerGraphView", "启用"
        )
        self.add_checkbox(
            "enabled", label=enabled_label, text=enabled_label, state=False
        )
        self.add_text_input(
            "next_tick",
            label=QCoreApplication.translate(
                "SchedulerGraphView", "下次执行时间"
            ),
            text="",
        )

    def set_property(self, name, value, push_undo=True):
        if name == "name" and self._display_title is not None:
            self.view.name = self._display_title
            return None
        return super().set_property(name, value, push_undo=push_undo)

    def _set_display_title(self, title: str) -> None:
        """Install an exact, immutable title independent of the model name."""
        if self._display_title is not None:
            self.view.name = self._display_title
            return
        self._display_title = title
        self.view._set_immutable_display_title(title)
        self.view.text_item.set_editable(False)
        self.view.text_item.set_locked(True)

    def port_label(self, role: str) -> str:
        return self._port_labels[role]

    @property
    def func_name(self) -> str:
        return self.get_property("func_name")


class FixedNodeGraph(NodeGraph):
    def __init__(self, parent=None, **kwargs):
        self._construction_depth = 0
        self._construction_scope_used = False
        super().__init__(parent=parent, **kwargs)
        # NodeGraphQt 0.6.44 leaves this popup unparented, so each graph
        # generation otherwise leaks its search menu after teardown.
        search_widget = self.viewer()._search_widget
        if search_widget.parent() is None:
            search_widget.setParent(
                self.viewer(), search_widget.windowFlags()
            )

    @contextmanager
    def _controlled_node_construction(self) -> Iterator[None]:
        """Allow the owning view to build the fixed node set."""
        if self._construction_scope_used:
            raise RuntimeError("fixed-node construction scope has already been used")
        self._construction_scope_used = True
        self._construction_depth += 1
        try:
            yield
        finally:
            self._construction_depth -= 1

    @property
    def _node_construction_allowed(self) -> bool:
        return self._construction_depth > 0

    def create_node(
        self,
        node_type,
        name=None,
        selected=True,
        color=None,
        text_color=None,
        pos=None,
        push_undo=True,
    ):
        if not self._node_construction_allowed:
            return None
        return super().create_node(
            node_type,
            name=name,
            selected=selected,
            color=color,
            text_color=text_color,
            pos=pos,
            push_undo=push_undo,
        )

    def add_node(
        self,
        node,
        pos=None,
        selected=True,
        push_undo=True,
        inherite_graph_style=True,
    ):
        if not self._node_construction_allowed:
            return None
        return super().add_node(
            node,
            pos=pos,
            selected=selected,
            push_undo=push_undo,
            inherite_graph_style=inherite_graph_style,
        )

    def delete_node(self, node, push_undo=True):
        return None

    def remove_node(self, node, push_undo=True):
        return None

    def delete_nodes(self, nodes, push_undo=True):
        return None

    def cut_nodes(self, nodes=None):
        return None

    def paste_nodes(self, adjust_graph_style=True):
        return []

    def duplicate_nodes(self, nodes):
        return []

    def clear_session(self):
        return None

    def deserialize_session(
        self,
        layout_data,
        clear_session=True,
        clear_undo_stack=True,
    ):
        return None

    def load_session(self, file_path):
        return None

    def import_session(self, file_path, clear_undo_stack=True):
        return None

    def toggle_node_search(self):
        """Keep the tab-search node creation UI unavailable."""
        return None


@dataclass
class _SchedulerGraphState:
    graph: FixedNodeGraph
    nodes_by_func: dict[str, SchedulerTaskNode]
    ports_by_func_role: dict[tuple[str, str], Port]
    port_identities: dict[Port, tuple[str, str]]
    persisted_enabled: dict[str, bool]
    persisted_times: dict[str, str]


class SchedulerGraphView(QWidget):
    data_changed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    warning_occurred = pyqtSignal(str)

    def __init__(
        self,
        config_dir: str | Path,
        parent: QWidget | None = None,
        store_factory: Callable[[str | Path], SchedulerGraphStore] = SchedulerGraphStore,
    ):
        super().__init__(parent)
        self._store = store_factory(config_dir)
        self._nodes_by_func: dict[str, SchedulerTaskNode] = {}
        self._ports_by_func_role: dict[tuple[str, str], Port] = {}
        self._port_identities: dict[Port, tuple[str, str]] = {}
        self._persisted_enabled: dict[str, bool] = {}
        self._persisted_times: dict[str, str] = {}
        self._suppression_depth = 0
        self._last_layout_error: SchedulerGraphError | None = None
        self.graph: FixedNodeGraph | None = None

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._message_label = QLabel(self)
        self._message_label.setObjectName("schedulerGraphMessage")
        self._message_label.setWordWrap(True)
        self._message_label.hide()
        self._layout.addWidget(self._message_label)

        self.reload_from_disk()

    def node_for_func(self, func_name: str) -> SchedulerTaskNode | None:
        return self._nodes_by_func.get(func_name)

    def port_for(self, func_name: str, role: str) -> Port | None:
        return self._ports_by_func_role.get((func_name, role))

    def reload_from_disk(self) -> None:
        layout_error = None
        if self.graph is not None:
            self.save_layout()
            layout_error = self._last_layout_error

        try:
            snapshot = self._store.load_snapshot()
        except Exception as exc:
            self._show_error(
                exc, fallback_code=SchedulerErrorCode.GRAPH_LOAD_FAILED
            )
            return

        try:
            replacement = self._build_graph_state(
                snapshot.events,
                snapshot.relationships,
            )
        except Exception as exc:
            self._show_error(
                exc, fallback_code=SchedulerErrorCode.GRAPH_LOAD_FAILED
            )
            return

        old_graph = self.graph
        self.graph = replacement.graph
        self._nodes_by_func = replacement.nodes_by_func
        self._ports_by_func_role = replacement.ports_by_func_role
        self._port_identities = replacement.port_identities
        self._persisted_enabled = replacement.persisted_enabled
        self._persisted_times = replacement.persisted_times
        self._layout.addWidget(replacement.graph.widget)
        if old_graph is not None:
            self._dispose_graph(old_graph)

        if layout_error is not None:
            warning_text = "\n".join(
                self._translated_warning(warning)
                for warning in snapshot.warnings
            )
            layout_error_text = self._translated_error(layout_error)
            message = (
                f"{layout_error_text}\n{warning_text}"
                if warning_text
                else layout_error_text
            )
            self._message_label.setStyleSheet("color: #d13438;")
            self._message_label.setText(message)
            self._message_label.show()
            if warning_text:
                self.warning_occurred.emit(warning_text)
        elif snapshot.warnings:
            self._show_warning(
                "\n".join(
                    self._translated_warning(warning)
                    for warning in snapshot.warnings
                )
            )
        else:
            self._clear_message()

    def _build_graph_state(
        self,
        events: Sequence[SchedulerEvent],
        relationships: Sequence[SchedulerRelationship],
    ) -> _SchedulerGraphState:
        graph = FixedNodeGraph(parent=self)
        state = _SchedulerGraphState(
            graph=graph,
            nodes_by_func={},
            ports_by_func_role={},
            port_identities={},
            persisted_enabled={},
            persisted_times={},
        )
        try:
            graph.set_acyclic(False)
            graph.register_node(SchedulerTaskNode)
            graph.disable_context_menu(True)
            graph.viewer().setAcceptDrops(False)
            graph.port_connected.connect(self._on_port_connected)
            graph.port_disconnected.connect(self._on_port_disconnected)

            with self._suppress_graph_events():
                with graph._controlled_node_construction():
                    self._create_nodes(events, state)
                self._restore_or_arrange_positions(state)
                self._draw_relationships(
                    relationships, state.ports_by_func_role
                )
            graph.undo_stack().clear()
        except BaseException:
            self._dispose_graph(graph)
            raise
        return state

    def _dispose_graph(self, graph: FixedNodeGraph) -> None:
        widget = graph.widget
        if self._layout.indexOf(widget) >= 0:
            self._layout.removeWidget(widget)
        widget.close()
        widget.setParent(None)
        widget.deleteLater()
        graph.deleteLater()

    def save_layout(self) -> None:
        self._last_layout_error = None
        if self.graph is None:
            return
        positions = {
            func_name: (float(node.pos()[0]), float(node.pos()[1]))
            for func_name, node in self._nodes_by_func.items()
        }
        try:
            self._store.save_positions(positions)
        except Exception as exc:
            self._last_layout_error = self._structured_error(
                exc, fallback_code=SchedulerErrorCode.SAVE_FAILED
            )
            self._show_error(self._last_layout_error)

    def hideEvent(self, event: QHideEvent) -> None:
        self.save_layout()
        super().hideEvent(event)

    def _create_nodes(
        self,
        events: Sequence[SchedulerEvent],
        state: _SchedulerGraphState,
    ) -> None:
        for event in events:
            title = bt.tr("ConfigTranslation", event.event_name)
            node = state.graph.create_node(
                SchedulerTaskNode.type_,
                name=title,
                selected=False,
                push_undo=False,
            )
            node._set_display_title(title)
            node.set_property("func_name", event.func_name, push_undo=False)
            time_text = datetime.fromtimestamp(event.next_tick).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            node.set_property("enabled", event.enabled, push_undo=False)
            node.set_property("next_tick", time_text, push_undo=False)

            state.nodes_by_func[event.func_name] = node
            state.persisted_enabled[event.func_name] = event.enabled
            state.persisted_times[event.func_name] = time_text
            self._register_ports(event.func_name, node, state)
            self._wire_embedded_widgets(event.func_name, node)

    def _register_ports(
        self,
        func_name: str,
        node: SchedulerTaskNode,
        state: _SchedulerGraphState,
    ) -> None:
        ports = {
            "pre_input": node.inputs()[node.port_label("pre_input")],
            "post_input": node.inputs()[node.port_label("post_input")],
            "pre_output": node.outputs()[node.port_label("pre_output")],
            "post_output": node.outputs()[node.port_label("post_output")],
        }
        for role, port in ports.items():
            state.ports_by_func_role[(func_name, role)] = port
            state.port_identities[port] = (func_name, role)

    def _wire_embedded_widgets(
        self, func_name: str, node: SchedulerTaskNode
    ) -> None:
        checkbox = node.get_widget("enabled").get_custom_widget()
        line_edit = node.get_widget("next_tick").get_custom_widget()
        checkbox.stateChanged.connect(
            partial(self._on_enabled_changed, func_name, node, checkbox)
        )
        line_edit.editingFinished.connect(
            partial(self._on_next_tick_finished, func_name, node, line_edit)
        )

    def _restore_or_arrange_positions(
        self, state: _SchedulerGraphState
    ) -> None:
        positions = self._store.load_positions()
        has_complete_layout = bool(positions) and all(
            func_name in positions for func_name in state.nodes_by_func
        )
        if has_complete_layout:
            for func_name, node in state.nodes_by_func.items():
                node.set_pos(*positions[func_name])
            return
        state.graph.auto_layout_nodes()

    def _draw_relationships(
        self,
        relationships: Sequence[SchedulerRelationship],
        ports_by_func_role: dict[tuple[str, str], Port],
    ) -> None:
        for relationship in relationships:
            output_role = f"{relationship.kind}_output"
            input_role = f"{relationship.kind}_input"
            output_port = ports_by_func_role[
                (relationship.source_func, output_role)
            ]
            input_port = ports_by_func_role[
                (relationship.target_func, input_role)
            ]
            output_port.connect_to(
                input_port, push_undo=False, emit_signal=False
            )

    def _on_port_connected(
        self, input_port: Port, output_port: Port
    ) -> None:
        if self._events_suppressed:
            return
        relationship = self._relationship_for_ports(input_port, output_port)
        if relationship is None:
            self._rollback_connection(input_port, output_port, connected=False)
            self._show_error(
                InvalidRelationship(
                    SchedulerErrorCode.PORT_TYPE_MISMATCH
                )
            )
            return
        kind, owner_func, related_func = relationship
        try:
            self._store.add_relationship(kind, owner_func, related_func)
        except Exception as exc:
            self._rollback_connection(input_port, output_port, connected=False)
            self._show_error(exc)
            return
        self.data_changed.emit()

    def _on_port_disconnected(
        self, input_port: Port, output_port: Port
    ) -> None:
        if self._events_suppressed:
            return
        relationship = self._relationship_for_ports(input_port, output_port)
        if relationship is None:
            self._rollback_connection(input_port, output_port, connected=True)
            self._show_error(
                InvalidRelationship(
                    SchedulerErrorCode.PORT_TYPE_MISMATCH
                )
            )
            return
        kind, owner_func, related_func = relationship
        try:
            self._store.remove_relationship(kind, owner_func, related_func)
        except Exception as exc:
            self._rollback_connection(input_port, output_port, connected=True)
            self._show_error(exc)
            return
        self.data_changed.emit()

    def _relationship_for_ports(
        self, input_port: Port, output_port: Port
    ) -> tuple[str, str, str] | None:
        input_identity = self._port_identities.get(input_port)
        output_identity = self._port_identities.get(output_port)
        if input_identity is None or output_identity is None:
            return None

        target_func, input_role = input_identity
        source_func, output_role = output_identity
        if (input_role, output_role) == ("pre_input", "pre_output"):
            return "pre", target_func, source_func
        if (input_role, output_role) == ("post_input", "post_output"):
            return "post", source_func, target_func
        return None

    def _rollback_connection(
        self, input_port: Port, output_port: Port, *, connected: bool
    ) -> None:
        with self._suppress_graph_events():
            if connected:
                output_port.connect_to(
                    input_port, push_undo=False, emit_signal=False
                )
            else:
                output_port.disconnect_from(
                    input_port, push_undo=False, emit_signal=False
                )
        self._clear_undo_stack_later()

    def _on_enabled_changed(
        self,
        func_name: str,
        node: SchedulerTaskNode,
        checkbox,
        _state: int,
    ) -> None:
        if self._events_suppressed:
            return
        enabled = checkbox.isChecked()
        previous = self._persisted_enabled[func_name]
        if enabled == previous:
            return
        try:
            self._store.update_enabled(func_name, enabled)
        except Exception as exc:
            self._restore_node_property(node, "enabled", previous, checkbox)
            self._show_error(exc)
            return
        self._persisted_enabled[func_name] = enabled
        self.data_changed.emit()

    def _on_next_tick_finished(
        self, func_name: str, node: SchedulerTaskNode, line_edit
    ) -> None:
        if self._events_suppressed:
            return
        time_text = line_edit.text()
        previous = self._persisted_times[func_name]
        if time_text == previous:
            return
        try:
            self._store.update_next_tick(func_name, time_text)
        except Exception as exc:
            self._restore_node_property(
                node, "next_tick", previous, line_edit
            )
            self._show_error(exc)
            return
        self._persisted_times[func_name] = time_text
        self.data_changed.emit()

    def _restore_node_property(
        self,
        node: SchedulerTaskNode,
        property_name: str,
        value: object,
        custom_widget,
    ) -> None:
        node_widget = node.get_widget(property_name)
        with self._suppress_graph_events():
            blockers = [
                QSignalBlocker(custom_widget),
                QSignalBlocker(node_widget),
            ]
            node.set_property(property_name, value, push_undo=False)
            del blockers
        self._clear_undo_stack_later()

    def _clear_undo_stack_later(self) -> None:
        if self.graph is None:
            return
        # NodeGraphQt signals can arrive while a port/property undo operation
        # is still unwinding. Remove the rejected command on the next event.
        QTimer.singleShot(0, self.graph.undo_stack().clear)

    @property
    def _events_suppressed(self) -> bool:
        return self._suppression_depth > 0

    @contextmanager
    def _suppress_graph_events(self) -> Iterator[None]:
        self._suppression_depth += 1
        try:
            yield
        finally:
            self._suppression_depth -= 1

    @staticmethod
    def _structured_error(
        error: Exception,
        *,
        fallback_code: SchedulerErrorCode | None = None,
    ) -> SchedulerGraphError:
        if isinstance(error, SchedulerGraphError):
            return error
        if fallback_code is None:
            fallback_code = (
                SchedulerErrorCode.SAVE_FAILED
                if isinstance(error, OSError)
                else SchedulerErrorCode.GRAPH_LOAD_FAILED
            )
        return SchedulerGraphError(fallback_code)

    @staticmethod
    def _translated_error(error: SchedulerGraphError) -> str:
        template = _ERROR_TEMPLATES[error.code]()
        return template.format(**error.parameters)

    def _show_error(
        self,
        error: Exception,
        *,
        fallback_code: SchedulerErrorCode | None = None,
    ) -> None:
        structured_error = self._structured_error(
            error, fallback_code=fallback_code
        )
        message = self._translated_error(structured_error)
        self._message_label.setStyleSheet("color: #d13438;")
        self._message_label.setText(message)
        self._message_label.show()
        self.error_occurred.emit(message)

    @staticmethod
    def _translated_warning(warning: SchedulerWarning) -> str:
        template = _WARNING_TEMPLATES[warning.code]()
        return template.format(**warning.parameters)

    def _show_warning(self, message: str) -> None:
        self._message_label.setStyleSheet("color: #d99b00;")
        self._message_label.setText(message)
        self._message_label.show()
        self.warning_occurred.emit(message)

    def _clear_message(self) -> None:
        self._message_label.clear()
        self._message_label.hide()
