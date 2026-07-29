from tests.gui.helpers import FakeConfig


LEVEL = "clear_friend_level_limit"
LOGIN_DAYS = "clear_friend_last_login_time_days"
RANK = "clear_friend_last_total_assault_rank_limit"


def make_widget():
    from gui.components.expand.friendClearConfig import Layout

    config = FakeConfig({LEVEL: -1, LOGIN_DAYS: -1, RANK: -1})
    return Layout(config=config), config


def test_friend_thresholds_start_disabled_and_allow_int32_values(qapp):
    widget, _ = make_widget()

    for spin in (
        widget.level_limit_spin,
        widget.last_login_days_spin,
        widget.total_assault_rank_spin,
    ):
        assert spin.value() == -1
        assert spin.minimum() == -1
        assert spin.maximum() == 2_147_483_647
    assert "-1" in widget.disabled_tip_label.text()


def test_friend_thresholds_write_python_integers(qapp):
    widget, config = make_widget()

    widget.level_limit_spin.setValue(85)
    widget.last_login_days_spin.setValue(30)
    widget.total_assault_rank_spin.setValue(50_000)

    assert config.writes == [
        (LEVEL, 85),
        (LOGIN_DAYS, 30),
        (RANK, 50_000),
    ]
