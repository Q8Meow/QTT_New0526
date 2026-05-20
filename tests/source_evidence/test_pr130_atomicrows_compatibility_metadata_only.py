from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_atomicrows_compatibility_metadata_only():
    report = support.main_report()

    assert report["future_atomicrows_bridge_path_preserved"] is True
    assert report["future_atomicrows_bridge_materialization_recommended_after_repo_pr"] == "PR135"
    assert report["atomicrows_bundle_consumed"] is False
    assert report["atomicrows_bundle_created"] is False
    assert report["atomicrows_sha_created"] is False
    assert report["atomicrows_row_records_created_count"] == 0
    assert report["atomicrows_authority_created"] is False
