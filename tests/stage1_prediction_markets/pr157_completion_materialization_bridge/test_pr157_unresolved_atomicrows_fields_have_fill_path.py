from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_unresolved_atomicrows_fields_have_fill_path():
    unresolved = [record for record in atomic_records() if record["blocker_class"] != c.BlockerClass.NONE.value]
    assert unresolved
    assert all(record["unresolved_field_fill_plans"] for record in unresolved)
