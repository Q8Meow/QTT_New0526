from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import summary


def test_pr164_no_qtt_sha_freeze_checksum_atomicrows_hash_authority():
    record = summary()
    assert record["qtt_freeze_checksum_global_digest_authority_count"] == 0
    assert record["qtt_generated_sha_authority_count"] == 0
    assert record["protected_atomicrows_bundle_checksum_mutation_count"] == 0
    assert record["pr164_created_ref_integrity_authority_violation_count"] == 0
