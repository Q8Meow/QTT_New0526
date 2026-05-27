from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_report


def test_pr157_no_atomicrows_bundle_checksum_hash_authority():
    assert atomic_report()["no_authority_confirmation"]["atomicrows_bundle_checksum_hash_authority_created"] is False
