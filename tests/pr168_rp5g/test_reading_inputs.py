from ._helpers import assert_rows_have_contract


def test_reading_receipts_consume_required_inputs() -> None:
    rows = assert_rows_have_contract("read_rec.jsonl")
    assert any(row["resolved_path"].endswith("trade_seed.jsonl") for row in rows)
    assert all(row["read_status"] == "READ_UTF8" for row in rows)

