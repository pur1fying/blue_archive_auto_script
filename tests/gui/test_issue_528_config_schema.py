import json

from core.config.default_config import DEFAULT_CONFIG
from core.config.generated_user_config import Config


EXPECTED = {
    "final_restriction_rls_employ_formation_method": "default",
    "final_restriction_rls_employ_formation_copy_clear_unit_max_unavailable_student_count": 0,
    "final_restriction_rls_employ_formation_copy_clear_unit_max_refresh_count": 10,
    "clear_friend_level_limit": -1,
    "clear_friend_last_login_time_days": -1,
    "clear_friend_last_total_assault_rank_limit": -1,
}


def test_issue_528_defaults_and_generated_types_match():
    defaults = json.loads(DEFAULT_CONFIG)
    for key, expected in EXPECTED.items():
        assert defaults[key] == expected

    annotations = Config.__annotations__
    for key, expected in EXPECTED.items():
        assert annotations[key] is type(expected)
