from __future__ import annotations


def test_retest_budget_policy_tiers_exist(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_RetestBudgetAllocationPolicy.report.json"]
    tiers = {row["budget_tier"] for row in rows}
    assert "TIER_1_HIGH_CONFIDENCE_CHAMPIONS" in tiers
    assert "TIER_4_QUANTUM_PRIORITY_CANDIDATES" in tiers
    assert all(row["budget_scope"] == "REPLAY_PAPER_RETEST_ONLY_NO_LIVE_CAPITAL_ALLOCATION" for row in rows)
