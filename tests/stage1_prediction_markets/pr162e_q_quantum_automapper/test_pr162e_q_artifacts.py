from __future__ import annotations

from collections import Counter

from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper import constants as c
from src.qtt.stage1_prediction_markets.pr162e_q_quantum_automapper.validator import (
    validate_artifacts,
)

from .helpers import REPO_ROOT, assert_report_contract, payload, records, summary


def test_pr162e_q_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def test_pr162e_q_input_counts_and_final_summary():
    final = summary()
    assert final["consumed_pr162e_q_handoff_rows"] == 559
    assert final["input_record_counts"]["PR166_QC_To_PR162E_Q.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_AutomapperNeeds.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_ReplayPaperRepairLab.report.json"] == 559
    assert final["input_record_counts"]["PR166_QC_StillNegativeAfterCosts.report.json"] == 559
    assert final["deep_mapping_subset_count"] == c.MAP_CAPS["max_deep_mapping_rows_default_ci"]
    assert final["forbidden_authority_counts_all_zero_flag"] is True
    assert final["dashboard_ui_implemented_flag"] is False


def test_pr162e_q_required_reports_have_contracts_and_rows():
    for filename in c.REPORT_FILENAMES:
        expected = 559 if filename in c.ROW_REPORTS else None
        assert_report_contract(filename, expected)

    manifest = assert_report_contract("PR162E_Q_ReportManifest.report.json")
    assert len(manifest) == len(c.REPORT_FILENAMES)
    assert {row["report_path"].split("/")[-1] for row in manifest} == set(c.REPORT_FILENAMES)


def test_pr162e_q_source_and_upstream_consumption_ledgers():
    sources = assert_report_contract("PR162E_Q_SourceMapParams.report.json")
    assert len(sources) >= 8
    assert any(row["official_flag"] is True for row in sources)
    assert any(row["non_official_flag"] is True for row in sources)
    assert any(row["source_type"].startswith("official_") for row in sources)
    assert any(row["source_type"].startswith("research_") for row in sources)
    assert all(row["no_backend_execution_flag"] is True for row in sources)
    assert all(row["no_source_truth_acceptance_flag"] is True for row in sources)

    upstream = assert_report_contract("PR162E_Q_UpstreamReportUse.report.json")
    assert len(upstream) == len(c.STRICT_INPUT_REPORTS)
    assert all(row["consumed_by_pr162e_q_flag"] is True for row in upstream)
    assert all(row["terminal_flag"] is False for row in upstream)
    assert {row["source_pr"] for row in upstream} >= {"PR166-QC", "PR166-QB", "PR166-Q", "PR165-D2"}


def test_pr162e_q_budget_subset_and_dispositions_are_bounded():
    budget = records("PR162E_Q_MapBudget.report.json")[0]
    assert budget["max_deep_mapping_rows_default_ci"] == 64
    assert budget["max_penalty_variants_per_row_default_ci"] == 8
    assert budget["no_unbounded_mapping_execution_flag"] is True

    rows = assert_report_contract("PR162E_Q_MapEligibility.report.json", 559)
    deep = [row for row in rows if row["actual_deep_mapping_subset_flag"]]
    assert len(deep) == 64
    assert max(Counter(row["model_family_selected"] for row in deep).values()) <= 16
    assert all(row["automapper_disposition"] in c.AUTOMAPPER_DISPOSITIONS for row in rows)
    assert not (set(row["automapper_disposition"] for row in rows) & set(c.FORBIDDEN_AUTOMAPPER_DISPOSITIONS))
    assert all(row["mapping_quality_grade"] in c.MAPPING_QUALITY_GRADES for row in rows)
    assert all(row["classical_fallback_available"] is True for row in rows)
    assert all(row["hot_path_allowed_flag"] is False for row in rows)


def test_pr162e_q_unit_objective_variable_interpret_and_proof_contracts():
    unit_rows = assert_report_contract("PR162E_Q_UnitNorm.report.json", 559)
    assert all(row["YES_NO_side"] in {"YES", "NO"} for row in unit_rows)
    assert all(row["probability_unit"] == "PROBABILITY_0_TO_1" for row in unit_rows)
    assert all(
        row["expected_value_unit"]
        == "NORMALIZED_EXPECTED_NET_PROFIT_PER_ORDER_CANDIDATE_NOT_EVIDENCE"
        for row in unit_rows
    )

    objective_rows = assert_report_contract("PR162E_Q_ObjectiveMap.report.json", 559)
    assert all(row["objective_terms"] for row in objective_rows)
    assert all(row["objective_linear_terms"] for row in objective_rows)
    assert all("MAXIMIZE" in row["objective_direction"] for row in objective_rows)

    encoding_rows = assert_report_contract("PR162E_Q_VariableEncoding.report.json", 559)
    assert all(row["decision_variables"] for row in encoding_rows)
    assert any("bounded_integer_to_binary" in row["integer_encoding"] for row in encoding_rows)
    assert any(row["spin_encoding"].get("binary_to_spin") == "x=(s+1)/2" for row in encoding_rows)
    assert any("route_case" in row["one_hot_encoding"] for row in encoding_rows)

    interpret_rows = assert_report_contract("PR162E_Q_SolutionInterpretBack.report.json", 559)
    assert all(row["interpret_back_entries"] for row in interpret_rows)
    assert all(row["reverse_transform_rule"] for row in interpret_rows)
    assert all(row["lost_information_flag"] is False for row in interpret_rows)

    proof_rows = assert_report_contract("PR162E_Q_MapProof.report.json", 559)
    assert all(
        row["proof_status"]
        in {
            "PROOF_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER",
            "STRUCTURAL_PROOF_VECTOR_COMPUTED_NO_SOLVER",
        }
        for row in proof_rows
    )
    assert all(abs(row["objective_delta"]) <= 1e-9 for row in proof_rows)
    assert all(row["interpret_back_match_flag"] is True for row in proof_rows)


def test_pr162e_q_recipe_reports_are_computable_not_label_only():
    for filename in (
        "PR162E_Q_QUBORecipe.report.json",
        "PR162E_Q_BQMRecipe.report.json",
        "PR162E_Q_IsingRecipe.report.json",
        "PR162E_Q_CQMRecipe.report.json",
        "PR162E_Q_DQMRecipe.report.json",
        "PR162E_Q_QuadProgramRecipe.report.json",
        "PR162E_Q_HybridRecipe.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["recipe_payload"] for row in rows)
        assert all(row["objective_terms"] for row in rows)
        assert all(row["decision_variables"] for row in rows)
        assert all(row["solution_interpret_back_ref"] for row in rows)
        assert all(row["proof_vector_ref"] for row in rows)


def test_pr162e_q_tca_overfit_portfolio_regime_and_edge_are_materialized():
    for filename in (
        "PR162E_Q_TCAMapImpact.report.json",
        "PR162E_Q_OverfitFDRMapRisk.report.json",
        "PR162E_Q_PortfolioUtilityMap.report.json",
        "PR162E_Q_RegimeMapMemory.report.json",
        "PR162E_Q_EdgeAttribution.report.json",
        "PR162E_Q_MapSensitivityStress.report.json",
        "PR162E_Q_ExecutionAdjustedMapRank.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["total_tca_estimate"] >= 0 for row in rows)
        assert all(row["tca_reason_codes"] for row in rows)
        assert all("FEE" in row["tca_reason_codes"][0] for row in rows)
        assert all(row["false_discovery_penalty"] >= 0 for row in rows)
        assert all(row["final_marginal_utility_mapping_score"] >= 0 for row in rows)
        assert all(row["scenario_similarity_key"] for row in rows)
        assert all(row["not_profit_evidence_flag"] is True for row in rows)


def test_pr162e_q_repairs_handoffs_dashboard_connector_and_portability():
    repairs = assert_report_contract("PR162E_Q_StillNegativeMapRepair.report.json", 559)
    still_negative = [row for row in repairs if row["still_negative_after_costs_flag"]]
    assert len(still_negative) == summary()["still_negative_map_repair_count"] == 385
    assert all(row["repair_mapping_flag"] is True for row in still_negative)
    assert all(row["not_profit_evidence_flag"] is True for row in repairs)

    assert len([row for row in records("PR162E_Q_OpenTradeSimMap.report.json") if row["open_trade_sim_route_flag"]]) == 61
    assert len([row for row in records("PR162E_Q_OwnerDashboardMapReview.report.json") if row["owner_dashboard_review_flag"]]) == 438

    for filename in (
        "PR162E_Q_To_PR166_QC_Retest.report.json",
        "PR162E_Q_To_PR167.report.json",
        "PR162E_Q_To_PR162E.report.json",
        "PR162E_Q_To_PR162F.report.json",
        "PR162E_Q_To_OwnerDashboard.report.json",
        "PR162E_Q_To_CloudSwitchboard.report.json",
        "PR162E_Q_To_FutureConnectors.report.json",
        "PR162E_Q_ConnectorRouteReady.report.json",
        "PR162E_Q_MarketPortability.report.json",
    ):
        rows = assert_report_contract(filename, 559)
        assert all(row["no_live_authority_flag"] is True for row in rows)
        assert all(row["connector_semantic_binding_flag"] is False for row in rows)
        assert all(row["source_truth_acceptance_flag"] is False for row in rows)

    portability = records("PR162E_Q_MarketPortability.report.json")
    assert all(row["stage1_prediction_market_flag"] is True for row in portability)
    assert all(row["future_market_portability_flag"] is True for row in portability)
    assert all(row["no_current_connector_binding_flag"] is True for row in portability)


def test_pr162e_q_crosswalk_artifact_agent_and_no_orphan_maps():
    crosswalk = assert_report_contract("PR162E_Q_ReportConsumerCrosswalk.report.json")
    assert len(crosswalk) >= len(c.REPORT_FILENAMES) + len(c.STRICT_INPUT_REPORTS)
    assert all(
        row["consuming_agent_ids"] or row["consuming_downstream_reports"] or row["terminal_flag"]
        for row in crosswalk
    )

    artifact_rows = assert_report_contract("PR162E_Q_ArtifactMap.report.json")
    assert all(
        row["consumed_by_agent"] or row["consumed_by_report"] or row["terminal_flag"]
        for row in artifact_rows
    )
    assert any(row["artifact_type"] == "generated_schema" for row in artifact_rows)
    assert any(row["artifact_type"] == "generated_shard_report" for row in artifact_rows)

    assert_report_contract("PR162E_Q_AgentWorkOrders.report.json", 559)
    dag = assert_report_contract("PR162E_Q_AgentDAG.report.json", 559)
    assert all(row["downstream_agent_refs"] for row in dag)
    no_orphan = assert_report_contract("PR162E_Q_NoOrphanProof.report.json", 559)
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in no_orphan)
    assert all(row["orphan_count"] == 0 for row in no_orphan)


def test_pr162e_q_summary_counts_match_ledgers():
    final = summary()
    eligibility = records("PR162E_Q_MapEligibility.report.json")
    assert final["automapper_disposition_counts"] == dict(
        sorted(Counter(row["automapper_disposition"] for row in eligibility).items())
    )
    assert final["mapping_quality_grade_counts"] == dict(
        sorted(Counter(row["mapping_quality_grade"] for row in eligibility).items())
    )
    assert final["model_family_selected_counts"] == dict(
        sorted(Counter(row["model_family_selected"] for row in eligibility).items())
    )
    assert payload("PR162E_Q_FinalSummary.report.json")["record_count"] == 1
