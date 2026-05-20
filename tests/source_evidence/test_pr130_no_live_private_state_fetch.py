from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_no_live_private_state_fetch():
    assert support.main_report()["private_state_fetch_created_count"] == 0
    assert all(
        receipt["account_wallet_balance_private_state_fetch_allowed_flag"] is False
        for receipt in support.read_receipts()
    )
    assert support.main_report()["production_private_state_fetch_attempt_rejection_count"] == 1
