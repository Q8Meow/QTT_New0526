from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_no_atomicrows_bundle_checksum_hash_authority():
    assert master_report()["atomicrows_bundle_checksum_hash_authority_count"] == 0
