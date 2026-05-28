from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT, report


def test_pr160_online_context_non_authoritative_for_values_if_present():
    path = ROOT / c.ONLINE_CONTEXT_RECEIPTS_PATH
    if not path.exists():
        assert report(c.MASTER_REPORT_PATH)["online_classification_context_used"] is False
        return
    records = report(c.ONLINE_CONTEXT_RECEIPTS_PATH)["records"]
    assert all(item["accepted_value_authority_flag"] is False for item in records)
