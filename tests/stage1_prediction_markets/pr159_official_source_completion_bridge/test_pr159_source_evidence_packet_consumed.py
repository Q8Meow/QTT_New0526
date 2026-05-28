from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_source_evidence_packet_consumed():
    receipts = {item["path"]: item for item in master_report()["input_consumption_receipt"]}
    assert receipts[c.SOURCE_EVIDENCE_PACKET_PATH.as_posix()]["consumed"] is True
    assert master_report()["source_evidence_packet_consumed_confirmation"] is True

