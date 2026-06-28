from ._helpers import assert_rows_have_contract


def test_grid_fdr_surfaces_track_multiple_testing_without_performance_claims() -> None:
    rows = assert_rows_have_contract("grid_fdr.jsonl")

    assert all(row["fdr_control_ready_flag"] is True for row in rows)
    assert all(row["candidate_grid_size"] <= 500 for row in rows)
    assert all(row["bounded_grid_count"] >= 1 for row in rows)
    assert all(row["future_rank4_consumer_refs"] for row in rows)
    assert all(row["profit_proof_flag"] is False for row in rows)

