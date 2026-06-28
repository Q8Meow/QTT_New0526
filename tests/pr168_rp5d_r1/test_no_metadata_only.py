from ._helpers import all_rows, read_jsonl


def test_no_metadata_only_rows_pass() -> None:
    assert read_jsonl("no_meta.jsonl")[0]["metadata_only_proof_count"] == 0
    assert all(row.get("metadata_is_proof_flag") is False for row in all_rows())
