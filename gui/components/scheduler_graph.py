"""Editable, fixed-node scheduler dependency graph widgets."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Callable, Iterator

from NodeGraphQt import BaseNode, NodeGraph, Port
from NodeGraphQt.constants import PortTypeEnum
from NodeGraphQt.qgraphics.node_base import NodeItem
from NodeGraphQt.qgraphics.node_text_item import NodeTextItem
from PyQt5.QtCore import QSignalBlocker, QTimer, pyqtSignal
from PyQt5.QtGui import QHideEvent
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from gui.util.scheduler_graph_store import (
    SchedulerEvent,
    SchedulerGraphStore,
    SchedulerRelationship,
)
from gui.util.translator import baasTranslator as bt


PRE_INPUT = "前置任务"
PRE_OUTPUT = "作为前置任务"
POST_INPUT = "作为后置任务"
POST_OUTPUT = "后置任务"

PRE_COLOR = (70, 155, 255)
POST_COLOR = (255, 160, 70)


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

        pre_input = self.add_input(
            PRE_INPUT, multi_input=True, color=PRE_COLOR
        )
        post_input = self.add_input(
            POST_INPUT, multi_input=True, color=POST_COLOR
        )
        pre_output = self.add_output(
            PRE_OUTPUT, multi_output=True, color=PRE_COLOR
        )
        post_output = self.add_output(
            POST_OUTPUT, multi_output=True, color=POST_COLOR
        )

        pre_input.add_accept_port_type(
            PRE_OUTPUT, PortTypeEnum.OUT.value, self.type_
        )
        pre_output.add_accept_port_type(
            PRE_INPUT, PortTypeEnum.IN.value, self.type_
        )
        post_input.add_accept_port_type(
            POST_OUTPUT, PortTypeEnum.OUT.value, self.type_
        )
        post_output.add_accept_port_type(
            POST_INPUT, PortTypeEnum.IN.value, self.type_
        )

        self.add_checkbox("enabled", text="enabled", state=False)
        self.add_text_input("next_tick", text="")

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

    @property
    def func_name(self) -> str:
        return self.get_property("func_name")


class FixedNodeGraph(NodeGraph):
    def __init__(self, parent=None, **kwargs):
        self._construction_depth = 0
        self._construction_scope_used = False
        super().__init__(parent=parent, **kwargs)

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
        self._last_layout_error: str | None = None
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
            events = self._store.load_events()
            relationships, warnings = self._store.load_relationships()
        except Exception as exc:
            self._show_error(exc)
            return

        old_graph = self.graph
        old_widget = old_graph.widget if old_graph is not None else None

        graph = FixedNodeGraph()
        graph.set_acyclic(False)
        graph.register_node(SchedulerTaskNode)
        graph.disable_context_menu(True)
        graph.viewer().setAcceptDrops(False)
        graph.port_connected.connect(self._on_port_connected)
        graph.port_disconnected.connect(self._on_port_disconnected)

        self.graph = graph
        self._nodes_by_func = {}
        self._ports_by_func_role = {}
        self._port_identities = {}
        self._persisted_enabled = {}
        self._persisted_times = {}
        self._layout.addWidget(graph.widget)

        with self._suppress_graph_events():
            with graph._controlled_node_construction():
                self._create_nodes(events)
            self._restore_or_arrange_positions()
            self._draw_relationships(relationships)
        graph.undo_stack().clear()

        if old_graph is not None and old_widget is not None:
            self._layout.removeWidget(old_widget)
            old_widget.close()
            old_widget.setParent(None)
            old_widget.deleteLater()
            old_graph.deleteLater()

        if layout_error is not None:
            warning_text = "\n".join(warnings)
            message = (
                f"{layout_error}\n{warning_text}"
                if warning_text
                else layout_error
            )
            self._message_label.setStyleSheet("color: #d13438;")
            self._message_label.setText(message)
            self._message_label.show()
            if warning_text:
                self.warning_occurred.emit(warning_text)
        elif warnings:
            self._show_warning("\n".join(warnings))
        else:
            self._clear_message()

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
            self._last_layout_error = str(exc) or exc.__class__.__name__
            self._show_error(exc)

    def hideEvent(self, event: QHideEvent) -> None:
        self.save_layout()
        super().hideEvent(event)

    def _create_nodes(self, events: list[SchedulerEvent]) -> None:
        assert self.graph is not None
        for event in events:
            title = bt.tr("ConfigTranslation", event.event_name)
            node = self.graph.create_node(
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

            self._nodes_by_func[event.func_name] = node
            self._persisted_enabled[event.func_name] = event.enabled
            self._persisted_times[event.func_name] = time_text
            self._register_ports(event.func_name, node)
            self._wire_embedded_widgets(event.func_name, node)

    def _register_ports(
        self, func_name: str, node: SchedulerTaskNode
    ) -> None:
        ports = {
            "pre_input": node.inputs()[PRE_INPUT],
            "post_input": node.inputs()[POST_INPUT],
            "pre_output": node.outputs()[PRE_OUTPUT],
            "post_output": node.outputs()[POST_OUTPUT],
        }
        for role, port in ports.items():
            self._ports_by_func_role[(func_name, role)] = port
            self._port_identities[port] = (func_name, role)

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

    def _restore_or_arrange_positions(self) -> None:
        assert self.graph is not None
        positions = self._store.load_positions()
        has_complete_layout = bool(positions) and all(
            func_name in positions for func_name in self._nodes_by_func
        )
        if has_complete_layout:
            for func_name, node in self._nodes_by_func.items():
                node.set_pos(*positions[func_name])
            return
        self.graph.auto_layout_nodes()

    def _draw_relationships(
        self, relationships: list[SchedulerRelationship]
    ) -> None:
        for relationship in relationships:
            output_role = f"{relationship.kind}_output"
            input_role = f"{relationship.kind}_input"
            output_port = self._ports_by_func_role[
                (relationship.source_func, output_role)
            ]
            input_port = self._ports_by_func_role[
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
                ValueError("Only matching scheduler relationship ports can connect.")
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
                ValueError(
                    "Only matching scheduler relationship ports can disconnect."
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

    def _show_error(self, error: Exception) -> None:
        message = str(error) or error.__class__.__name__
        self._message_label.setStyleSheet("color: #d13438;")
        self._message_label.setText(message)
        self._message_label.show()
        self.error_occurred.emit(message)

    def _show_warning(self, message: str) -> None:
        self._message_label.setStyleSheet("color: #d99b00;")
        self._message_label.setText(message)
        self._message_label.show()
        self.warning_occurred.emit(message)

    def _clear_message(self) -> None:
        self._message_label.clear()
        self._message_label.hide()
