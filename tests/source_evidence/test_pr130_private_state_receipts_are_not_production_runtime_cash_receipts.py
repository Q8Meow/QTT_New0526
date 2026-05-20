from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_private_state_receipts_are_not_production_runtime_cash_receipts():
    assert support.main_report()["production_runtime_cash_receipt_authority_count"] == 0
    assert support.main_report()["runtime_cash_receipts_created_count"] == 0
    assert all(
        linkage["production_runtime_cash_receipt_authority"] is False
        for linkage in support.linkage_receipts()
    )
