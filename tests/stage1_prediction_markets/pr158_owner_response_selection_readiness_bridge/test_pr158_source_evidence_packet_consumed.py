from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report


def test_pr158_source_evidence_packet_consumed():
    receipts = {item["path"]: item for item in master_report()["input_consumption_receipt"]}
    assert receipts[c.SOURCE_EVIDENCE_PACKET_PATH.as_posix()]["consumed"] is True

