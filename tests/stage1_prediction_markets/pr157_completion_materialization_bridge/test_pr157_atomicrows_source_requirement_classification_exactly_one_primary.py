from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_atomicrows_source_requirement_classification_exactly_one_primary():
    allowed = c.CENTRAL_ENUM_VALUE_SETS["source_requirement_class"]
    for record in atomic_records():
        assert isinstance(record["source_requirement_class"], str)
        assert record["source_requirement_class"] in allowed
