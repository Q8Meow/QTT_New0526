from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_source_evidence_packet_consumed():
    receipts = {item["path"]: item for item in master_report()["input_consumption_receipt"]}
    assert receipts[c.SOURCE_EVIDENCE_PACKET_PATH.as_posix()]["consumed"] is True
    assert master_report()["source_evidence_packet_consumed_confirmation"] is True
