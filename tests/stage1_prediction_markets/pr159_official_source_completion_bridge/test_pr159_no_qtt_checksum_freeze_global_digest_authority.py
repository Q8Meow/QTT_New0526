from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_qtt_checksum_freeze_global_digest_authority():
    assert master_report()["qtt_checksum_freeze_global_digest_authority_count"] == 0
    assert master_report()["no_authority_confirmation"]["qtt_checksum_freeze_global_digest_authority_created"] is False

