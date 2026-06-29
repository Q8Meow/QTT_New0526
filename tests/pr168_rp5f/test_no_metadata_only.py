from ._helpers import all_jsonl_rows, assert_rows_have_contract, read_json


def test_no_metadata_only_rows_or_metadata_proof_exist() -> None:
    rows = assert_rows_have_contract("no_meta.jsonl")

    assert all(row["metadata_only_proof_count"] == 0 for row in rows)
    for name, row in all_jsonl_rows():
        assert row.get("metadata_is_proof_flag") is False, (name, row.get("row_id"))
    assert read_json("run_receipt.report.json")["metadata_only_proof_count"] == 0

