from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_preserves_future_production_launch_path():
    assert support.main_report()["future_production_launch_path_preserved"] is True
    assert support.main_report()["future_official_source_private_state_production_path_recorded"] is True
    assert all(
        receipt["future_production_launch_path_preserved"] is True
        for receipt in support.read_receipts()
    )
