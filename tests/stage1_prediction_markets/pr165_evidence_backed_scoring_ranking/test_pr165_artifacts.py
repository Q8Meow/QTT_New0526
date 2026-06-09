from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr165_evidence_backed_scoring_ranking import paths
from src.qtt.stage1_prediction_markets.pr165_evidence_backed_scoring_ranking.json_io import (
    read_json,
)
from src.qtt.stage1_prediction_markets.pr165_evidence_backed_scoring_ranking.report_sharding import (
    load_report_records,
)
from src.qtt.stage1_prediction_markets.pr165_evidence_backed_scoring_ranking.validators import (
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _records(filename: str) -> list[dict[str, object]]:
    payload = read_json(REPO_ROOT / paths.GENERATED_DIR / filename)
    return load_report_records(REPO_ROOT, payload)


def test_pr165_validator_accepts_generated_artifacts() -> None:
    result = validate_artifacts(REPO_ROOT)

    assert result.ok, result.failures[:10]


def test_pr165_final_summary_counts_and_boundaries() -> None:
    summary = _records("PR165_FinalSummary.report.json")[0]

    assert summary["scored_candidate_rows"] == 6502
    assert summary["remaining_materialization_plan_rows"] == 2858
    assert summary["global_ranking_rows"] == 6502
    assert summary["regime_sliced_ranking_rows"] > 6502
    assert summary["score_component_rows"] == 6502
    assert summary["candidate_value_materialization_rows"] == 6502
    assert summary["external_search_queries_executed"] == 20
    assert summary["external_candidate_records_created"] == 50
    assert summary["external_formula_or_parameter_records_created"] == 20
    assert summary["external_quantum_mapping_template_records_created"] == 10
    assert summary["metadata_only_rows"] == 0
    assert summary["placeholder_only_rows"] == 0
    assert summary["future_consumer_only_rows"] == 0
    assert summary["unknown_status_rows"] == 0
    assert summary["orphan_counts_all_0"] is True
    assert summary["authority_counts_all_0"] is True
    assert summary["quantum_backend_execution_count"] == 0
    assert summary["quantum_advantage_claim_count"] == 0
    assert summary["source_acceptance_count"] == 0
    assert summary["connector_binding_count"] == 0
    assert summary["live_order_authority_count"] == 0


def test_pr165_global_ranking_rows_are_component_backed() -> None:
    rows = _records("PR165_GlobalCandidateRanking.report.json")

    assert len(rows) == 6502
    assert [row["global_rank"] for row in rows[:5]] == [1, 2, 3, 4, 5]
    for row in (rows[0], rows[len(rows) // 2], rows[-1]):
        assert row["candidate_packet_id"]
        assert row["qku_id"]
        assert row["score_formula_ref"]
        assert row["score_test_vector_ref"]
        assert row["deterministic_score_component_record"]
        assert row["score_decomposition"]
        assert row["lineage_graph_ref"]
        assert row["repair_routing_ref"]
        assert row["authority_boundary_record"]["live_order_authority_allowed"] is False
        assert row["authority_boundary_record"]["source_truth_conversion_allowed"] is False
        assert "risk_agent" in row["downstream_agent_routes"]
        assert "dashboard_future_consumer" in row["downstream_agent_routes"]
        assert 0 <= row["composite_score"] <= 100
        assert row["score_lower_bound"] <= row["composite_score"] <= row["score_upper_bound"]


def test_pr165_remaining_rows_have_materialization_recipes() -> None:
    rows = _records("PR165_Remaining2858ComputabilityMaterializationPlan.report.json")

    assert len(rows) == 2858
    for row in (rows[0], rows[len(rows) // 2], rows[-1]):
        assert row["computability_status"] in {
            "NEXT_PR_COMPUTABILITY_MATERIALIZATION_REQUIRED",
            "OUT_OF_PR165_SCORING_SCOPE_WITH_MATERIALIZATION_RECIPE",
        }
        assert row["missing_variable_families"]
        assert row["missing_value_families"]
        assert row["candidate_source_search_plan"]
        assert row["candidate_formula_algorithm_plan"]
        assert row["likely_responsible_agent"]
        assert row["likely_downstream_pr"] == "PR162D-R3"
        assert row["replay_paper_route_after_materialization"]
        assert row["repair_retest_route"]
        assert row["authority_boundary_record"]["live_order_authority_allowed"] is False


def test_pr165_model_risk_and_external_scouting_are_routed_not_promoted() -> None:
    model_risk = _records("PR165_ModelRiskPenaltyRegistry.report.json")
    external_rows = _records("PR165_ExternalCandidateScoutingLedger.report.json")

    assert len(model_risk) == 6502
    for row in (model_risk[0], model_risk[-1]):
        route = set(row["model_risk_route"])
        assert {"risk_agent", "governance_agent", "dashboard_future_consumer"} <= route
        assert isinstance(row["model_risk_penalty"], (int, float))
        if row["model_materiality_tier"] == "HIGH_AGENT_SELECTION_IMPACT":
            assert row["independent_review_required_flag"] is True

    assert len(external_rows) == 50
    for row in external_rows[:10]:
        assert row["source_url"].startswith("https://")
        assert row["source_authority_label"] == "CANDIDATE_PROVISIONAL_DESIGN_REFERENCE"
        assert row["converted_to_source_truth"] is False
        assert row["replay_paper_route"] == "PR165_REPLAY_PAPER_DESIGN_REFERENCE_ONLY"
