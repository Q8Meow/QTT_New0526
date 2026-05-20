from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_rejects_missing_runtime_cash_field_map_reference():
    artifacts = support.cloned_artifacts()
    artifacts["gate_report"]["private_state_read_requests"][0][
        "runtime_cash_component_field_map_id"
    ] = "PR129_MISSING_FIELD_MAP"

    assert any(
        "runtime cash field-map reference" in failure
        for failure in support.validation_failures(artifacts)
    )
