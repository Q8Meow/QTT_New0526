from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_atomicrows_compatibility_metadata_only():
    evidence = support.main_report()["PR132_ATOMICROWS_METADATA_ONLY_EVIDENCE"]

    assert evidence["atomicrows_bundle_consumed"] is False
    assert evidence["atomicrows_bundle_created"] is False
    assert evidence["atomicrows_bundle_edited_count"] == 0
    assert evidence["atomicrows_sha_created"] is False
    assert evidence["atomicrows_sha_created_count"] == 0
    assert evidence["atomicrows_row_records_created_count"] == 0
    assert evidence["atomicrows_authority_created"] is False
