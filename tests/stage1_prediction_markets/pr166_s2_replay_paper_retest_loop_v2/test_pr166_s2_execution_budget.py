from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_execution_budget_is_replay_paper_only():
    row = assert_report_rows("PR166_S2_ExecBudgetLedger.report.json", 3215)[0]
    assert row["execution_budget_authority"] == "REPLAY_PAPER_NOTIONAL_AND_CONTRACT_COUNT_ONLY_NO_RUNTIME_CASH"
    assert row["maximum_simulated_size_before_edge_decay"] >= row["base_candidate_size"]
