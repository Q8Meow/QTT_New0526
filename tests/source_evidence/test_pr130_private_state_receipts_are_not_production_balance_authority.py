from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_private_state_receipts_are_not_production_balance_authority():
    assert support.main_report()["production_account_balance_authority_count"] == 0
    assert support.main_report()["production_wallet_balance_authority_count"] == 0
    assert all(
        receipt["production_account_balance_authority"] is False
        and receipt["production_wallet_balance_authority"] is False
        for receipt in support.account_receipts()
    )
