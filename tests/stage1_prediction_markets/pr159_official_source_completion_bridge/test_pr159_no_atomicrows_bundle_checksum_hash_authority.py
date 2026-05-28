from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_no_atomicrows_bundle_checksum_hash_authority():
    assert master_report()["atomicrows_bundle_checksum_hash_authority_count"] == 0
    assert master_report()["no_authority_confirmation"]["atomicrows_bundle_checksum_hash_authority_created"] is False

