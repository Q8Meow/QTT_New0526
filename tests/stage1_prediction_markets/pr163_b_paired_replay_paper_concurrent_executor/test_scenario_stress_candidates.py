from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor.scenario_stress import STRESS_DIMENSIONS


def test_scenario_stress_candidates_cover_all_dimensions(records, summary):
    rows = records("PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"] * len(STRESS_DIMENSIONS)
    assert set(summary["stress_coverage_counts"]) == set(STRESS_DIMENSIONS)
    assert all(summary["stress_coverage_counts"][dimension] == summary["candidate_packet_universe_count"] for dimension in STRESS_DIMENSIONS)
