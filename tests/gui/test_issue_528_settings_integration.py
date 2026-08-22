import json

from core.config.default_config import DEFAULT_CONFIG, STATIC_DEFAULT_CONFIG, SWITCH_DEFAULT_CONFIG
from gui.components import expand
from gui.fragments.settings import SettingsFragment
from tests.gui.helpers import SettingsConfig


def test_issue_528_entries_belong_to_dailies():
    entries = json.loads(SWITCH_DEFAULT_CONFIG)
    by_config = {entry["config"]: entry for entry in entries}

    friend = by_config["friendWhiteList"]
    assert friend["sort"] == 15
    assert friend["name"] == "好友清理设置"
    assert friend["tip"] == "设置好友清理条件及需要保留的好友码"

    final = by_config["finalRestrictionRls"]
    assert final["sort"] == 17
    assert final["name"] == "无限制决战"
    assert final["tip"] == "设置编队方式及复制通关队伍限制"

    assert by_config["drillConfig"]["sort"] == 16


def test_issue_528_cards_are_not_built_by_settings(qapp):
    fragment = SettingsFragment(config=SettingsConfig({"name": "Test"}))

    assert not hasattr(fragment, "finalRestrictionRlsCard")
    assert all(
        getattr(card, "sub_view", None)
        is not expand.finalRestrictionRls
        for card in fragment.exploreGroupItems
    )
    assert fragment.minimizeToTrayCard in fragment.guiGroupItems


def test_widgets_round_trip_values_through_real_config_set(
    qapp, tmp_path, monkeypatch
):
    from core.config.config_set import ConfigSet
    from gui.components.expand.finalRestrictionRls import Layout as FinalLayout
    from gui.components.expand.friendWhiteList import Layout as FriendLayout

    config_root = tmp_path / "config"
    account_root = config_root / "test"
    account_root.mkdir(parents=True)
    (config_root / "static.json").write_text(
        STATIC_DEFAULT_CONFIG, encoding="utf-8"
    )
    (account_root / "config.json").write_text(
        DEFAULT_CONFIG, encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    ConfigSet.static_config = None
    config = ConfigSet("test")

    final_widget = FinalLayout(config=config)
    friend_widget = FriendLayout(config=config)
    final_widget.formation_method_combo._onItemClicked(1)
    final_widget.max_unavailable_spin.setValue(4)
    final_widget.max_refresh_spin.setValue(25)
    friend_widget.level_limit_spin.setValue(80)
    friend_widget.last_login_days_spin.setValue(14)
    friend_widget.total_assault_rank_spin.setValue(100_000)
    friend_widget.white_list.append("ABC1234")
    config.set("clear_friend_white_list", friend_widget.white_list)

    saved = json.loads(
        (account_root / "config.json").read_text(encoding="utf-8")
    )
    assert (
        saved["final_restriction_rls_employ_formation_method"]
        == "copy_clear_unit"
    )
    assert (
        saved[
            "final_restriction_rls_employ_formation_"
            "copy_clear_unit_max_unavailable_student_count"
        ]
        == 4
    )
    assert (
        saved[
            "final_restriction_rls_employ_formation_"
            "copy_clear_unit_max_refresh_count"
        ]
        == 25
    )
    assert saved["clear_friend_level_limit"] == 80
    assert saved["clear_friend_last_login_time_days"] == 14
    assert saved["clear_friend_last_total_assault_rank_limit"] == 100_000
    assert saved["clear_friend_white_list"] == ["ABC1234"]
