def test_walk_forward_holdout_readiness(records, summary):
    rows = records("PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["readiness_status"] == "WALK_FORWARD_READY_FOR_LATER_PR" for row in rows)
    assert all(row["no_ranking_created"] and row["no_profit_evidence"] for row in rows)
