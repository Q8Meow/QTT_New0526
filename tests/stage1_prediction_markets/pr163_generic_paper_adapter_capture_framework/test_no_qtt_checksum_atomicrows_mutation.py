def test_no_qtt_checksum_atomicrows_mutation(summary, records):
    rows = records("PR163_NoQTTChecksumFreezeAuthorityAudit.report.json")
    assert rows[0]["qtt_freeze_checksum_global_digest_authority_count"] == 0
    assert rows[0]["qtt_generated_sha_authority_count"] == 0
    assert rows[0]["protected_atomicrows_bundle_checksum_mutation_count"] == 0
    assert summary["protected_atomicrows_bundle_checksum_mutation_count"] == 0
