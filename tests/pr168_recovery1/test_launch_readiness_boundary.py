from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_launch_readiness_boundary_marks_recovered_candidates_replay_paper_only():
    assert_recovery1_valid()
    records = report("PR168_RECOVERY1_LaunchReadinessBoundary.report.json")["records"]

    assert records["launch_readiness_state"] == "NOT_LIVE_READY_REPLAY_PAPER_ONLY"
    assert records["still_no_trade_dominated_improved_row_count"] == 32
    assert records["recovered_candidate_count"] == 3
    assert records["paper_or_replay_ready_non_proof_count"] == 3
    assert records["live_ready_count"] == 0
    assert records["live_trading_ready_row_count"] == 0
    assert records["order_authority_created_count"] == 0
    assert records["champion_allowed_count"] == 0
    assert records["live_candidate_allowed_count"] == 0
    assert records["source_truth_acceptance_created_count"] == 0
    assert records["future_live_gate_required_flag"] is True
