from ._helpers import all_jsonl_rows


def test_no_metadata_only_flags() -> None:
    for filename, row in all_jsonl_rows():
        if "metadata_is_proof_flag" in row:
            assert row["metadata_is_proof_flag"] is False, (filename, row["row_id"])
        if "metadata_only_flag" in row:
            assert row["metadata_only_flag"] is False, (filename, row["row_id"])

