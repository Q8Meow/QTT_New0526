from ._helpers import all_jsonl_rows, read_json


def test_no_mutation_no_sha_no_live_private_cash_or_connector_runtime() -> None:
    for name, row in all_jsonl_rows():
        assert row.get("formula_mutation_flag") is False, (name, row.get("row_id"))
        assert row.get("qku_mutation_flag") is False, (name, row.get("row_id"))
        assert row.get("qtt_sha_authority_flag") is False, (name, row.get("row_id"))
        assert row.get("atomicrows_sha_ref_flag") is False, (name, row.get("row_id"))
        assert row.get("live_authority_flag") is False, (name, row.get("row_id"))
        assert row.get("connector_write_flag") is False, (name, row.get("row_id"))
        assert row.get("private_state_fetch_flag") is False, (name, row.get("row_id"))
        assert row.get("cash_account_read_flag") is False, (name, row.get("row_id"))

    receipt = read_json("run_receipt.report.json")
    assert receipt["formula_mutation_count"] == 0
    assert receipt["qku_mutation_count"] == 0
    assert receipt["qtt_sha_authority_count"] == 0
    assert receipt["connector_write_count"] == 0
    assert receipt["private_state_fetch_count"] == 0
    assert receipt["cash_account_read_count"] == 0

