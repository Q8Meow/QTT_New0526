from ._helpers import assert_rows_have_contract


def test_source_coverage_has_official_and_nonofficial_candidate_receipts() -> None:
    rows = assert_rows_have_contract("source_coverage.jsonl")
    source_types = {row["source_type"] for row in rows}

    assert "OFFICIAL" in source_types
    assert source_types & {"RESEARCH", "WEB", "INSTITUTIONAL"}
    assert all(row["candidate_only_flag"] is True for row in rows)
    assert all(row["accepted_source_fact_flag"] is False for row in rows)
    assert all(row["connector_semantic_binding_flag"] is False for row in rows)
    assert all(row["live_default_flag"] is False for row in rows)

