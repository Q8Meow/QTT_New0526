from __future__ import annotations


def test_pr162r_a_rolls_up_pr162d_6502_candidate_universe(summary, records):
    rollup = records("PR162R_A_PR162D6502CoverageRollup.report.json")[0]
    assert rollup["pr162d_consumed_not_rebuilt_flag"] is True
    assert rollup["candidate_universe_expected_count"] == 6502
    assert rollup["candidate_universe_observed_count"] == 6502
    assert summary["pr162d_6502_coverage_rollup_status"] == "ROLLED_UP_FROM_PR162D_NO_REBUILD"
