from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_no_qtt_sha_freeze_checksum_atomicrows_hash_authority():
    audit = load_records("PR163_C_NoQTTChecksumFreezeAuthorityAudit.report.json")[0]
    assert audit["qtt_freeze_checksum_global_digest_authority_count"] == 0
    assert audit["qtt_generated_sha_authority_count"] == 0
    assert summary()["qtt_sha_freeze_checksum_count"] == 0
    assert summary()["atomicrows_sha_hash_mutation_count"] == 0
