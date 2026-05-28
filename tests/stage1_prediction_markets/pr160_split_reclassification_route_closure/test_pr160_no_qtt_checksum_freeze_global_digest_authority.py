from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_no_qtt_checksum_freeze_global_digest_authority():
    assert master_report()["qtt_checksum_freeze_global_digest_authority_count"] == 0
