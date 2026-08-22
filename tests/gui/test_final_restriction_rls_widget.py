from tests.gui.helpers import FakeConfig


METHOD = "final_restriction_rls_employ_formation_method"
UNAVAILABLE = (
    "final_restriction_rls_employ_formation_"
    "copy_clear_unit_max_unavailable_student_count"
)
REFRESH = (
    "final_restriction_rls_employ_formation_"
    "copy_clear_unit_max_refresh_count"
)


def make_widget(method="default"):
    from gui.components.expand.finalRestrictionRls import Layout

    config = FakeConfig({METHOD: method, UNAVAILABLE: 2, REFRESH: 10})
    return Layout(config=config), config


def test_default_method_disables_copy_clear_controls(qapp):
    widget, _ = make_widget()

    assert widget.formation_method_combo.currentIndex() == 0
    assert not widget.max_unavailable_spin.isEnabled()
    assert not widget.max_refresh_spin.isEnabled()
    assert widget.max_unavailable_spin.minimum() == 0
    assert widget.max_unavailable_spin.maximum() == 10
    assert widget.max_refresh_spin.minimum() == 0
    assert widget.max_refresh_spin.maximum() == 2_147_483_647


def test_combo_writes_raw_method_and_enables_dependent_controls(qapp):
    widget, config = make_widget()

    widget.formation_method_combo._onItemClicked(1)

    assert config.writes[-1] == (METHOD, "copy_clear_unit")
    assert widget.max_unavailable_spin.isEnabled()
    assert widget.max_refresh_spin.isEnabled()


def test_spin_boxes_write_python_integers(qapp):
    widget, config = make_widget("copy_clear_unit")

    widget.max_unavailable_spin.setValue(7)
    widget.max_refresh_spin.setValue(42)

    assert (UNAVAILABLE, 7) in config.writes
    assert (REFRESH, 42) in config.writes
