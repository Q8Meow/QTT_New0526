from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_q_comparator_rows_exist_for_all_quantum_candidates():
    classical = assert_report_contract("PR166_Q_ClassicalBaselineComparator.report.json", 559)
    inspired = assert_report_contract("PR166_Q_QuantumInspiredComparator.report.json", 559)
    hybrid = assert_report_contract("PR166_Q_HybridComparator.report.json", 559)
    race = assert_report_contract("PR166_Q_QuantumClassicalHybridRaceLedger.report.json", 559)
    assert all(row["classical_baseline_exists_flag"] for row in classical)
    assert all(row["quantum_inspired_structurally_valid_flag"] for row in inspired)
    assert all(row["true_quantum_readiness_structural_only_flag"] for row in hybrid)
    assert sorted(row["final_non_live_comparator_rank"] for row in race) == list(range(1, 560))


def test_pr166_q_tca_components_sum_and_expected_net_is_deterministic():
    rows = assert_report_contract("PR166_Q_TCADecomposition.report.json", 559)
    for row in rows[:25]:
        total = round(
            row["explicit_fee_component"]
            + row["bid_ask_spread_component"]
            + row["slippage_component"]
            + row["impact_component"]
            + row["latency_component"]
            + row["no_fill_opportunity_cost_component"]
            + row["settlement_finality_component"]
            + row["market_state_mismatch_component"]
            + row["model_vs_execution_gap_component"]
            + row["adverse_selection_cost_component"],
            6,
        )
        assert total == row["total_transaction_cost_estimate"]
        assert row["expected_net_profit_per_order_candidate"] == row["execution_adjusted_edge"]


def test_pr166_q_overfit_false_discovery_fields_penalize_rank():
    rows = assert_report_contract("PR166_Q_OverfitFalseDiscoveryControl.report.json", 559)
    assert all(row["effective_independent_trial_count"] > 0 for row in rows)
    assert all(row["false_discovery_penalty"] >= 0 for row in rows)
    assert all(row["probability_of_backtest_overfitting_proxy"] >= 0 for row in rows)
    assert all(row["purged_walk_forward_cpcv_eligibility_flag"] is True for row in rows)
