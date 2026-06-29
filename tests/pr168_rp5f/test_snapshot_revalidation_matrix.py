from ._helpers import assert_rows_have_contract


def test_snapshot_revalidation_matrix_covers_snapshot_source_truth_venue_and_risk() -> None:
    rows = assert_rows_have_contract("snapshot_reval.jsonl")

    assert all(row["pre_submit_revalidation_required_flag"] for row in rows)
    assert all(row["snapshot_change_checks"] for row in rows)
    assert all(row["source_change_checks"] for row in rows)
    assert all(row["market_data_truth_checks"] for row in rows)
    assert all(row["venue_state_checks"] for row in rows)
    assert all(row["risk_portfolio_checks"] for row in rows)
    assert all(row["kill_switch_owner_gate_checks"] for row in rows)

