from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_report


def test_pr157_no_qtt_checksum_freeze_global_digest_authority():
    assert atomic_report()["no_authority_confirmation"]["qtt_checksum_freeze_global_digest_authority_created"] is False
