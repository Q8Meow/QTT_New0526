def test_no_qtt_checksum_atomicrows_mutation(summary):
    assert summary["qtt_freeze_checksum_global_digest_authority_count"] == 0
    assert summary["qtt_generated_sha_authority_count"] == 0
    assert summary["protected_atomicrows_bundle_checksum_mutation_count"] == 0
