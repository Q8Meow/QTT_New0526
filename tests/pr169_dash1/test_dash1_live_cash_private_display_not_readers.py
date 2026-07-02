from tests.pr169_dash1.conftest import jsonl


def test_live_cash_private_rows_are_display_contracts_not_readers() -> None:
    rows = jsonl("owner_live_cash_private_display_contract.generated.jsonl")
    assert rows
    for row in rows:
        assert row["snapshot_ref_type"] == "provider_receipt_ref"
        assert row["direct_reader_created"] is False
