import json

from core.config.default_config import DEFAULT_CONFIG, STATIC_DEFAULT_CONFIG
from tests.gui.helpers import SettingsConfig


def test_settings_page_exposes_both_issue_528_cards(qapp):
    from gui.components import expand
    from gui.fragments.settings import SettingsFragment

    fragment = SettingsFragment(config=SettingsConfig({"name": "Test"}))

    assert fragment.finalRestrictionRlsCard in fragment.exploreGroupItems
    assert fragment.friendClearConfigCard in fragment.exploreGroupItems
    assert fragment.finalRestrictionRlsCard.sub_view is expand.finalRestrictionRls
    assert fragment.friendClearConfigCard.sub_view is expand.friendClearConfig


def test_widgets_round_trip_values_through_real_config_set(
    qapp, tmp_path, monkeypatch
):
    from core.config.config_set import ConfigSet
    from gui.components.expand.finalRestrictionRls import Layout as FinalLayout
    from gui.components.expand.friendClearConfig import Layout as FriendLayout

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
