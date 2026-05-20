from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_atomicrows_compatibility_metadata_only():
    evidence = support.main_report()["PR131_ATOMICROWS_METADATA_ONLY_EVIDENCE"]

    assert evidence["atomicrows_bundle_consumed_count"] == 0
    assert evidence["atomicrows_bundle_created_count"] == 0
    assert evidence["atomicrows_bundle_edited_count"] == 0
    assert evidence["atomicrows_sha_created_count"] == 0
    assert evidence["atomicrows_authority_created"] is False
