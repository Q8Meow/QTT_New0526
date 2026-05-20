from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_pr112_private_state_read_receipt_path():
    handoff = support.handoff_report()["runtime_cash_downstream_handoff"]

    assert handoff["future_private_state_read_receipt_pr"] == "PR112"
    assert support.main_report()["future_private_state_read_receipt_path_preserved"] is True
    assert all(
        receipt["future_private_state_read_receipt_path_preserved"] is True
        for receipt in support.available_receipts()
    )
