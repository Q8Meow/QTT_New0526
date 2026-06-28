from ._helpers import all_jsonl_rows, read_json


def test_no_metadata_only_row_or_source_fact_can_pass() -> None:
    for row in all_jsonl_rows():
        assert row.get("metadata_is_proof_flag") is False
        assert row.get("accepted_source_fact_flag") is False

    receipt = read_json("run_receipt.report.json")
    assert receipt["metadata_only_proof_count"] == 0
    assert receipt["source_fact_acceptance_count"] == 0
