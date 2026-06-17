from __future__ import annotations

from copy import deepcopy

from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.validator import validate_artifacts

from .helpers import REPO_ROOT, assert_report_contract, records, summary


def test_pr166_qc_validator_passes_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr166_qc_consumes_pr166_qb_handoffs_and_counts():
    final = summary()
    assert final["consumed_pr166_qc_handoff_rows"] == 559
    assert final["input_record_counts"]["PR166_QB_To_PR166_QC.report.json"] == 559
    assert final["input_record_counts"]["PR166_QB_ClassicalReceipt.report.json"] == 559
    assert final["input_record_counts"]["PR166_QB_QuantumRepairLab.report.json"] == 559
    assert final["input_record_counts"]["PR166_QB_ArtifactMap.report.json"] == 157
    assert_report_contract("PR166_QC_RetestEligibility.report.json", 559)
    assert_report_contract("PR166_QC_ReplayEvidence.report.json", 559)


def test_pr166_qc_source_replay_params_are_route_only_no_truth():
    rows = assert_report_contract("PR166_QC_SourceReplayParams.report.json", 12)
    assert any(row["official_flag"] for row in rows)
    assert any(row["non_official_flag"] for row in rows)
    assert all(row["source_locator_or_query"] for row in rows)
    assert all(row["candidate_values_extracted_count"] > 0 for row in rows)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in rows)
    assert all(row["no_connector_binding_flag"] is True for row in rows)
    assert all(row["no_profit_evidence_flag"] is True for row in rows)


def test_pr166_qc_retest_budget_subset_is_capped_and_deterministic():
    final = summary()
    budget = records("PR166_QC_RetestBudget.report.json")[0]
    subset = [row for row in records("PR166_QC_SubsetSelection.report.json") if row["actual_retest_subset_flag"]]
    assert len(subset) == 64
    assert final["replay_paper_retest_subset_count"] == 64
    assert budget["max_actual_replay_paper_rows_default_ci"] == 64
    assert budget["max_walk_forward_slices_default_ci"] == 4
    assert budget["max_scenario_states_default_ci"] == 16
    assert budget["max_market_book_states_default_ci"] == 16
    assert budget["max_random_seeds_default_ci"] == 3
    assert [row["deterministic_sort_key"] for row in subset] == sorted(row["deterministic_sort_key"] for row in subset)


def test_pr166_qc_dispositions_and_lanes_are_complete_and_fail_closed():
    rows = assert_report_contract("PR166_QC_RetestEligibility.report.json", 559)
    assert all(row["evidence_disposition"] in c.EVIDENCE_DISPOSITIONS for row in rows)
    assert all(row["evidence_disposition"] not in c.FORBIDDEN_EVIDENCE_DISPOSITIONS for row in rows)
    assert all(row["primary_evidence_lane"] in c.EVIDENCE_LANES for row in rows)
    assert all(row["primary_evidence_lane"] in row["evidence_lanes"] for row in rows)
    bad = deepcopy(rows[0])
    bad["evidence_disposition"] = "METADATA_ONLY_EVIDENCED"
    assert bad["evidence_disposition"] in c.FORBIDDEN_EVIDENCE_DISPOSITIONS
    bad["evidence_disposition"] = "UNBOUNDED_REPLAY_EXECUTED"
    assert bad["evidence_disposition"] in c.FORBIDDEN_EVIDENCE_DISPOSITIONS
    bad["evidence_disposition"] = "LIVE_ORDER_EXECUTED"
    assert bad["evidence_disposition"] in c.FORBIDDEN_EVIDENCE_DISPOSITIONS


def test_pr166_qc_evidence_quality_replay_paper_scores_are_present():
    rows = assert_report_contract("PR166_QC_EvidenceQuality.report.json", 559)
    assert all(row["evidence_quality_grade"] in c.EVIDENCE_QUALITY_GRADES for row in rows)
    assert all(0 <= row["evidence_quality_score"] <= 1 for row in rows)
    assert all(0 <= row["replay_evidence_score"] <= 1 for row in rows)
    assert all(0 <= row["paper_evidence_score"] <= 1 for row in rows)
    assert all(0 <= row["calibration_score"] <= 1 for row in rows)
    assert all(row["probability_reliability_bucket"] for row in rows)
    assert any(row["paper_promotion_candidate_flag"] for row in rows)
    assert all(not row["live_promotion_claim_flag"] for row in rows)


def test_pr166_qc_tca_fill_latency_queue_components_exist():
    rows = assert_report_contract("PR166_QC_TCAEvidence.report.json", 559)
    component_keys = (
        "explicit_fee_component",
        "bid_ask_spread_component",
        "slippage_component",
        "impact_component",
        "latency_component",
        "no_fill_opportunity_cost_component",
        "settlement_finality_component",
        "market_state_mismatch_component",
        "model_vs_execution_gap_component",
        "benchmark_to_replay_translation_penalty",
        "replay_to_paper_translation_penalty",
        "total_tca_estimate",
    )
    assert all(all(isinstance(row[key], (int, float)) for key in component_keys) for row in rows)
    assert all(row["tca_reason_codes"] for row in rows)
    assert all(row["profit_evidence_flag"] is False for row in rows)


def test_pr166_qc_overfit_portfolio_regime_and_race_fields_exist():
    rows = assert_report_contract("PR166_QC_OverfitFDRRetest.report.json", 559)
    assert all(row["trial_family_id"] for row in rows)
    assert all(row["near_duplicate_cluster_id"] for row in rows)
    assert all(row["effective_independent_trial_count"] > 0 for row in rows)
    assert all(row["probability_of_backtest_overfitting_proxy"] >= 0 for row in rows)
    assert all(row["classical_fallback_available"] is True for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)
    portfolio_rows = assert_report_contract("PR166_QC_PortfolioUtility.report.json", 559)
    assert all(row["event_cluster"] for row in portfolio_rows)
    assert all(row["final_marginal_utility_evidence_score"] >= 0 for row in portfolio_rows)
    regime_rows = assert_report_contract("PR166_QC_RegimeEvidence.report.json", 559)
    assert all(row["scenario_similarity_key"] for row in regime_rows)


def test_pr166_qc_repair_dashboard_market_connector_routes_are_safe():
    repair_rows = assert_report_contract("PR166_QC_ReplayPaperRepairLab.report.json", 559)
    assert all(row["repair_row_id"] for row in repair_rows)
    assert all(row["not_profit_evidence_flag"] is True for row in repair_rows)
    assert all(row["no_live_authority_flag"] is True for row in repair_rows)
    dashboard_rows = assert_report_contract("PR166_QC_OwnerDashboardReview.report.json", 559)
    assert all(row["dashboard_review_id"] for row in dashboard_rows)
    assert all(row.get("dashboard_ui_implemented_flag") in {None, False} for row in dashboard_rows)
    market_rows = assert_report_contract("PR166_QC_MarketPortability.report.json", 559)
    assert all(row["stage1_prediction_market_flag"] is True for row in market_rows)
    assert all(row["no_current_connector_binding_flag"] is True for row in market_rows)
    connector_rows = assert_report_contract("PR166_QC_ConnectorRouteReadiness.report.json", 559)
    assert all(row["no_current_connector_binding_flag"] is True for row in connector_rows)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in connector_rows)
    assert all(row["no_private_state_fetch_flag"] is True for row in connector_rows)


def test_pr166_qc_crosswalk_artifact_map_agents_and_handoffs_have_no_orphans():
    crosswalk = assert_report_contract("PR166_QC_ReportConsumerCrosswalk.report.json")
    mapped = {row["report_path"] for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        assert f"docs/master_plan/generated/{filename}" in mapped
    artifact_rows = assert_report_contract("PR166_QC_ArtifactMap.report.json")
    assert artifact_rows
    assert all(row["artifact_path"] for row in artifact_rows)
    assert all(row["consumed_by_module"] for row in artifact_rows)
    assert_report_contract("PR166_QC_AgentWorkOrders.report.json", 559)
    assert_report_contract("PR166_QC_AgentDAG.report.json", 559)
    no_orphan = assert_report_contract("PR166_QC_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in no_orphan)
    for filename in (
        "PR166_QC_To_PR162E_Q.report.json",
        "PR166_QC_To_PR167.report.json",
        "PR166_QC_To_PR162E.report.json",
        "PR166_QC_To_PR162F.report.json",
        "PR166_QC_To_OwnerDashboard.report.json",
        "PR166_QC_To_CloudSwitchboard.report.json",
        "PR166_QC_To_FutureConnectors.report.json",
    ):
        assert_report_contract(filename, 559)


def test_pr166_qc_authority_boundary_forbidden_counts_are_zero():
    final = summary()
    assert final["forbidden_authority_counts_all_zero_flag"] is True
    for key in (
        "cloud_backend_execution_count",
        "credential_access_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "profit_evidence_count",
        "live_order_authority_count",
        "live_promotion_claim_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "qtt_sha_authority_count",
        "atomicrows_bundle_hash_authority_count",
    ):
        assert final[key] == 0
