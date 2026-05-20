from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_no_order_execution_or_order_authority():
    assert support.main_report()["order_authority_created"] is False
    assert support.main_report()["production_order_authority_count"] == 0
    assert all(receipt["order_execution_allowed_flag"] is False for receipt in support.read_receipts())
    assert all(linkage["order_authority_allowed_flag"] is False for linkage in support.linkage_receipts())
