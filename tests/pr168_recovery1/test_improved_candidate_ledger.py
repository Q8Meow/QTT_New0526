from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_improved_candidate_ledger_contains_artifact_derived_deltas_only():
    assert_recovery1_valid()
    improved = rows("improved_candidate")

    assert improved
    assert all(row["delta_net_expected_pnl_candidate"] > 0 for row in improved)
    assert all(row["not_real_profit_proof_flag"] is True for row in improved)
    assert all(row["real_positive_flag"] is False for row in improved)
    assert all(row["champion_allowed_flag"] is False for row in improved)
    assert all(row["live_candidate_allowed_flag"] is False for row in improved)
    assert all(row["changed_input_refs"] for row in improved)
    assert all(row["unchanged_input_refs"] for row in improved)
