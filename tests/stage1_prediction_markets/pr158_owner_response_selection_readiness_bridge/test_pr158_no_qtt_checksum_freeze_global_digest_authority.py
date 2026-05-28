from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report, owner_response


def test_pr158_no_qtt_checksum_freeze_global_digest_authority():
    assert master_report()["no_authority_confirmation"]["qtt_checksum_freeze_global_digest_authority_created"] is False
    assert all(item["creates_qtt_checksum_freeze_global_digest_authority"] is False for item in owner_response()["response_items"])

