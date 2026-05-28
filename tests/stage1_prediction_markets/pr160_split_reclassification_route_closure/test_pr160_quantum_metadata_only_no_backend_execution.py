from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_quantum_metadata_only_no_backend_execution():
    records = report(c.QUANTUM_COMPAT_UPDATE_PATH)["records"]
    assert len(records) == 33
    assert all(item["quantum_metadata_only_no_backend_execution"] is True for item in records)
    assert all(item["quantum_advantage_claim_created_flag"] is False for item in records)
