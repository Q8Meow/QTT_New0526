from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_atomicrows_compatibility_metadata_only():
    main = support.main_report()

    assert main["atomicrows_bundle_consumed"] is False
    assert main["atomicrows_bundle_created"] is False
    assert main["atomicrows_sha_created"] is False
    assert main["atomicrows_row_records_created_count"] == 0
    assert main["atomicrows_authority_created"] is False
    assert main["future_atomicrows_bridge_materialization_recommended_after_repo_pr"] == "PR135"
    assert all(record["future_atomicrows_runtime_cash_component_family_ref"] for record in support.field_maps())
