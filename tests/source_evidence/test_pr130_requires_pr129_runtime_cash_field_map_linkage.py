from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_requires_pr129_runtime_cash_field_map_linkage():
    artifacts = support.artifacts()
    field_map_ids = {
        record["runtime_cash_component_field_map_id"]
        for records in artifacts["field_maps_by_venue"].values()
        for record in records
    }

    assert all(
        receipt["runtime_cash_component_field_map_id"] in field_map_ids
        for receipt in support.read_receipts()
    )
    assert all(
        linkage["runtime_available_after_commitments_receipt_ref"].startswith("PR129_")
        for linkage in support.linkage_receipts()
    )
    assert support.main_report()["pr129_runtime_cash_artifacts_consumed"] is True
