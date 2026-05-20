from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_no_account_wallet_balance_private_state_fetch():
    assert support.main_report()["private_state_fetch_created_count"] == 0
    assert all(
        receipt["account_wallet_balance_private_state_fetch_allowed_flag"] is False
        for receipt in support.available_receipts()
    )
    assert all(
        record["account_wallet_balance_private_state_fetch_allowed_flag"] is False
        for record in support.field_maps()
    )
