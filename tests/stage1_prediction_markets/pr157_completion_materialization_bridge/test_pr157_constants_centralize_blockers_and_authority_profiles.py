from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_constants_centralize_blockers_and_authority_profiles():
    blockers = c.CENTRAL_ENUM_VALUE_SETS["blocker_class"]
    profiles = c.CENTRAL_ENUM_VALUE_SETS["authority_profile_ids"]
    for record in atomic_records()[:100]:
        assert record["blocker_class"] in blockers
        assert set(record["authority_profile_ids"]).issubset(profiles)
