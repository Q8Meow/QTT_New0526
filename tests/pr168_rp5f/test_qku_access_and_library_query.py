from ._helpers import assert_rows_have_contract


def test_qku_access_uses_centralized_resolver_receipts() -> None:
    qku_rows = assert_rows_have_contract("qku_access.jsonl")
    receipts = assert_rows_have_contract("library_query.jsonl")

    assert qku_rows
    assert receipts
    assert all(row["full_library_scan_allowed_flag"] is False for row in qku_rows)
    assert all(row["agent_direct_jsonl_scan_allowed_flag"] is False for row in qku_rows)
    assert all(row["full_library_scan_flag"] is False for row in receipts)
    assert all(row["centralized_resolver_ref"] for row in receipts)

