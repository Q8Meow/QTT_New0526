"""Validate PR162E-Q generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import FORBIDDEN_AUTHORITY_FLAGS, ZERO_AUTHORITY_KEYS
from .io import read_json, records_from_report_payload


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_REPORT::{filename}")
            continue
        payload = read_json(path)
        payloads[filename] = payload
        records[filename] = records_from_report_payload(repo_root, payload)
    if failures:
        return ValidationResult(ok=False, failures=tuple(failures))
    _validate_schemas(repo_root, payloads, failures)
    _validate_payload_contracts(payloads, records, failures)
    _validate_inputs(repo_root, records, failures)
    _validate_mapping_rows(records, failures)
    _validate_budget(records, failures)
    _validate_source_and_upstream(records, failures)
    _validate_recipe_contracts(records, failures)
    _validate_interpret_back_and_proofs(records, failures)
    _validate_risk_execution_and_units(records, failures)
    _validate_routes_and_agents(records, failures)
    _validate_crosswalk_and_artifacts(records, failures)
    _validate_summary(records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(ok=not failures, failures=tuple(failures))


def _validate_schemas(repo_root: Path, payloads: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in payloads.items():
        schema_ref = payload.get("schema_ref")
        if not schema_ref:
            failures.append(f"MISSING_SCHEMA_REF::{filename}")
            continue
        if not (repo_root / c.SCHEMA_DIR / str(schema_ref)).exists():
            failures.append(f"MISSING_SCHEMA_FILE::{filename}::{schema_ref}")


def _validate_payload_contracts(
    payloads: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in payloads.items():
        if payload.get("roadmap_pr_id") != c.PR_ID:
            failures.append(f"BAD_ROADMAP_PR::{filename}")
        if payload.get("created_by_pr") != c.PR_ID:
            failures.append(f"BAD_CREATED_BY_PR::{filename}")
        if payload.get("record_count") != len(records[filename]):
            failures.append(f"BAD_RECORD_COUNT::{filename}")
        for key in ZERO_AUTHORITY_KEYS:
            if payload.get(key, 0) != 0:
                failures.append(f"PAYLOAD_FORBIDDEN_AUTHORITY_COUNT::{filename}::{key}")
        if filename in c.ROW_REPORTS and not payload.get("sharded_flag"):
            failures.append(f"ROW_REPORT_NOT_SHARDED::{filename}")


def _validate_inputs(repo_root: Path, records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_INPUT_REPORT::{filename}")
            continue
        payload = read_json(path)
        expanded = records_from_report_payload(repo_root, payload)
        if filename in c.EXPECTED_559_INPUTS and len(expanded) != 559:
            failures.append(f"INPUT_COUNT_DRIFT::{filename}::{len(expanded)}")
    input_rows = records["PR162E_Q_InputConsumption.report.json"]
    if len(input_rows) != len(c.STRICT_INPUT_REPORTS):
        failures.append("INPUT_CONSUMPTION_ROW_COUNT_MISMATCH")
    for row in input_rows:
        if not row.get("record_count_matches_expected_flag"):
            failures.append(f"INPUT_EXPECTED_COUNT_FAIL::{row.get('source_report_ref')}")
        for flag in ("no_source_truth_acceptance_flag", "no_connector_binding_flag", "no_profit_evidence_flag", "no_backend_execution_flag"):
            if row.get(flag) is not True:
                failures.append(f"INPUT_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")


def _validate_mapping_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    required = {
        "row_id",
        "source_pr",
        "upstream_pr166_qc_row_ref",
        "upstream_pr166_qb_row_ref",
        "upstream_pr166_q_row_ref",
        "qku_id",
        "qku_family",
        "formula_id",
        "algorithm_id",
        "parameter_stack_id",
        "execution_route_id",
        "market_scope",
        "stage1_prediction_market_flag",
        "future_market_portability_flag",
        "automapper_disposition",
        "mapping_quality_grade",
        "model_family_selected",
        "secondary_model_families",
        "formula_family_id",
        "objective_family_id",
        "canonical_objective_signature",
        "qubo_mappable_flag",
        "bqm_mappable_flag",
        "ising_mappable_flag",
        "cqm_mappable_flag",
        "dqm_mappable_flag",
        "quadratic_program_mappable_flag",
        "hybrid_mapping_flag",
        "objective_direction",
        "objective_terms",
        "objective_linear_terms",
        "objective_quadratic_terms",
        "decision_variables",
        "variable_domains",
        "constraints",
        "penalty_terms",
        "coefficient_scaling_status",
        "coefficient_dynamic_range",
        "unit_normalization_ref",
        "solution_interpret_back_ref",
        "test_vector_ref",
        "proof_vector_ref",
        "mapping_quality_score",
        "mapping_confidence_score",
        "edge_attribution_ref",
        "report_consumer_crosswalk_ref",
        "upstream_report_use_ref",
        "downstream_pr166_qc_retest_route_ref",
        "downstream_pr167_route_ref",
        "downstream_pr162e_route_ref",
        "downstream_pr162f_route_ref",
        "downstream_owner_dashboard_route_ref",
        "downstream_cloud_switchboard_route_ref",
        "downstream_future_connector_route_ref",
        "owning_agent_id",
        "reviewer_agent_id",
        "challenger_agent_id",
        "upstream_refs",
        "downstream_refs",
        "validation_refs",
        "no_orphan_proof_ref",
        "deterministic_sort_key",
    }
    for filename in c.ROW_REPORTS:
        rows = records[filename]
        if len(rows) != 559:
            failures.append(f"ROW_REPORT_COUNT_NOT_559::{filename}::{len(rows)}")
            continue
        seen: set[str] = set()
        for row in rows:
            row_id = str(row.get("row_id"))
            if row_id in seen:
                failures.append(f"DUPLICATE_ROW_ID::{filename}::{row_id}")
            seen.add(row_id)
            for key in required:
                if key not in row:
                    failures.append(f"REQUIRED_FIELD_MISSING::{filename}::{row_id}::{key}")
            disposition = row.get("automapper_disposition")
            if disposition not in c.AUTOMAPPER_DISPOSITIONS:
                failures.append(f"BAD_AUTOMAPPER_DISPOSITION::{filename}::{row_id}::{disposition}")
            if disposition in c.FORBIDDEN_AUTOMAPPER_DISPOSITIONS:
                failures.append(f"FORBIDDEN_AUTOMAPPER_DISPOSITION::{filename}::{row_id}::{disposition}")
            grade = row.get("mapping_quality_grade")
            if grade not in c.MAPPING_QUALITY_GRADES:
                failures.append(f"BAD_MAPPING_QUALITY_GRADE::{filename}::{row_id}::{grade}")
            if row.get("classical_fallback_available") is not True:
                failures.append(f"CLASSICAL_FALLBACK_MISSING::{filename}::{row_id}")
            if row.get("hot_path_allowed_flag") is not False:
                failures.append(f"HOT_PATH_ALLOWED::{filename}::{row_id}")
            if row.get("future_live_candidate_flag") is not False:
                failures.append(f"FUTURE_LIVE_CANDIDATE_TRUE::{filename}::{row_id}")
            _validate_authority(row, failures, filename, row_id)


def _validate_authority(row: dict[str, Any], failures: list[str], filename: str, row_id: str) -> None:
    for key in ZERO_AUTHORITY_KEYS:
        if row.get(key, 0) != 0:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_COUNT::{filename}::{row_id}::{key}")
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if row.get(flag) is not False:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_FLAG::{filename}::{row_id}::{flag}")
    if row.get("no_live_authority_flag") is not True:
        failures.append(f"NO_LIVE_AUTHORITY_FLAG_MISSING::{filename}::{row_id}")
    if row.get("profit_evidence_flag") is not False:
        failures.append(f"PROFIT_EVIDENCE_FLAG_TRUE::{filename}::{row_id}")


def _validate_budget(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    budget = records["PR162E_Q_MapBudget.report.json"][0]
    subset = [row for row in records["PR162E_Q_MapEligibility.report.json"] if row.get("actual_deep_mapping_subset_flag")]
    if len(subset) != budget.get("actual_deep_mapping_subset_size"):
        failures.append("DEEP_MAPPING_SUBSET_SIZE_MISMATCH")
    if len(subset) > c.MAP_CAPS["max_deep_mapping_rows_default_ci"]:
        failures.append("DEEP_MAPPING_SUBSET_CAP_EXCEEDED")
    for key, cap in c.MAP_CAPS.items():
        if budget.get(key) != cap:
            failures.append(f"MAP_CAP_VALUE_MISMATCH::{key}")
    per_family: dict[str, int] = {}
    for row in subset:
        family = str(row.get("model_family_selected"))
        per_family[family] = per_family.get(family, 0) + 1
    for family, count in per_family.items():
        if count > c.MAP_CAPS["max_rows_per_model_family_default_ci"]:
            failures.append(f"DEEP_MAPPING_FAMILY_CAP_EXCEEDED::{family}::{count}")
    if [row["deterministic_sort_key"] for row in subset] != sorted(row["deterministic_sort_key"] for row in subset):
        failures.append("DEEP_MAPPING_SUBSET_SORT_NOT_DETERMINISTIC")
    if budget.get("no_unbounded_mapping_execution_flag") is not True:
        failures.append("MAP_BUDGET_UNBOUNDED_FLAG_MISSING")


def _validate_source_and_upstream(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    sources = records["PR162E_Q_SourceMapParams.report.json"]
    if not any(row.get("official_flag") for row in sources):
        failures.append("SOURCE_MAP_OFFICIAL_SOURCE_MISSING")
    if not any(row.get("non_official_flag") for row in sources):
        failures.append("SOURCE_MAP_NON_OFFICIAL_SOURCE_MISSING")
    for row in sources:
        for key in (
            "mapping_parameters_extracted_count",
            "model_family_patterns_extracted_count",
            "penalty_patterns_extracted_count",
            "encoding_patterns_extracted_count",
            "coefficient_scaling_patterns_extracted_count",
            "interpret_back_patterns_extracted_count",
            "proof_vector_patterns_extracted_count",
            "repair_strategy_parameters_extracted_count",
            "benchmark_retest_parameters_extracted_count",
            "future_market_portability_notes_count",
            "candidate_values_extracted_count",
        ):
            if not isinstance(row.get(key), int) or row[key] < 0:
                failures.append(f"SOURCE_COUNT_BAD::{row.get('row_id')}::{key}")
        if int(row.get("candidate_values_extracted_count", 0)) <= 0 and not row.get("rejected_reason"):
            failures.append(f"SOURCE_CANDIDATE_VALUES_MISSING::{row.get('row_id')}")
        for flag in ("no_source_truth_acceptance_flag", "no_connector_binding_flag", "no_profit_evidence_flag", "no_backend_execution_flag"):
            if row.get(flag) is not True:
                failures.append(f"SOURCE_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")
    upstream = records["PR162E_Q_UpstreamReportUse.report.json"]
    if len(upstream) != len(c.STRICT_INPUT_REPORTS):
        failures.append("UPSTREAM_REPORT_USE_COUNT_MISMATCH")
    for row in upstream:
        if row.get("consumed_by_pr162e_q_flag") is not True and not row.get("terminal_reason"):
            failures.append(f"UPSTREAM_NOT_CONSUMED_OR_TERMINAL::{row.get('row_id')}")
        if not row.get("fields_used"):
            failures.append(f"UPSTREAM_FIELDS_USED_MISSING::{row.get('row_id')}")


def _validate_recipe_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    recipe_reports = (
        "PR162E_Q_QUBORecipe.report.json",
        "PR162E_Q_BQMRecipe.report.json",
        "PR162E_Q_IsingRecipe.report.json",
        "PR162E_Q_CQMRecipe.report.json",
        "PR162E_Q_DQMRecipe.report.json",
        "PR162E_Q_QuadProgramRecipe.report.json",
        "PR162E_Q_HybridRecipe.report.json",
    )
    for filename in recipe_reports:
        for row in records[filename]:
            payload = row.get("recipe_payload") or {}
            if not payload:
                failures.append(f"RECIPE_PAYLOAD_MISSING::{filename}::{row.get('row_id')}")
            if not row.get("objective_terms") or not row.get("decision_variables"):
                failures.append(f"RECIPE_LABEL_ONLY::{filename}::{row.get('row_id')}")
            if row.get("automapper_disposition") in c.FORBIDDEN_AUTOMAPPER_DISPOSITIONS:
                failures.append(f"RECIPE_FORBIDDEN_DISPOSITION::{filename}::{row.get('row_id')}")
            if not row.get("solution_interpret_back_ref") or not row.get("proof_vector_ref"):
                failures.append(f"RECIPE_INTERPRET_OR_PROOF_MISSING::{filename}::{row.get('row_id')}")
    for row in records["PR162E_Q_HybridRecipe.report.json"]:
        if row.get("classical_fallback_available") is not True:
            failures.append(f"HYBRID_CLASSICAL_FALLBACK_MISSING::{row.get('row_id')}")
        if row.get("quantum_backend_execution_flag") is not False:
            failures.append(f"HYBRID_BACKEND_EXECUTED::{row.get('row_id')}")


def _validate_interpret_back_and_proofs(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR162E_Q_SolutionInterpretBack.report.json"]:
        for key in (
            "encoded_variable_name",
            "original_variable_name",
            "original_qku_field",
            "original_formula_field",
            "original_parameter_field",
            "original_execution_route_field",
            "encoded_domain",
            "original_domain",
            "transform_type",
            "reverse_transform_rule",
            "feasibility_check_rule",
            "downstream_agent_consumer",
            "test_vector_ref",
            "proof_vector_ref",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"INTERPRET_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("lost_information_flag") is not False and not row.get("lost_information_reason"):
            failures.append(f"INTERPRET_LOST_INFO_REASON_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_MapProof.report.json"]:
        if row.get("proof_status") not in {
            "PROOF_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER",
            "STRUCTURAL_PROOF_VECTOR_COMPUTED_NO_SOLVER",
        }:
            failures.append(f"PROOF_STATUS_BAD::{row.get('row_id')}::{row.get('proof_status')}")
        if abs(float(row.get("objective_delta", 1.0))) > 1e-9:
            failures.append(f"PROOF_OBJECTIVE_DELTA_NONZERO::{row.get('row_id')}")
        if row.get("interpret_back_match_flag") is not True:
            failures.append(f"PROOF_INTERPRET_BACK_FAIL::{row.get('row_id')}")
    for row in records["PR162E_Q_TestVectors.report.json"]:
        if row.get("test_status") != "PASS_DETERMINISTIC_NO_SOLVER":
            failures.append(f"TEST_VECTOR_STATUS_BAD::{row.get('row_id')}")


def _validate_risk_execution_and_units(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR162E_Q_UnitNorm.report.json"]:
        for key in (
            "probability_unit",
            "YES_NO_side",
            "price_unit",
            "edge_unit",
            "TCA_unit",
            "latency_unit",
            "fill_probability_unit",
            "order_size_unit",
            "expected_value_unit",
            "normalized_expected_net_profit_per_order_candidate",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"UNIT_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("YES_NO_side") not in {"YES", "NO"}:
            failures.append(f"UNIT_YES_NO_SIDE_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_TCAMapImpact.report.json"]:
        for key in (
            "explicit_fee_component",
            "bid_ask_spread_component",
            "slippage_component",
            "impact_component",
            "latency_component",
            "no_fill_opportunity_cost_component",
            "settlement_finality_component",
            "market_state_mismatch_component",
            "model_vs_execution_gap_component",
            "mapping_to_replay_translation_penalty",
            "mapping_to_paper_translation_penalty",
            "mapping_to_simulator_translation_penalty",
            "total_tca_estimate",
        ):
            if not isinstance(row.get(key), (int, float)):
                failures.append(f"TCA_FIELD_MISSING::{row.get('row_id')}::{key}")
        if not row.get("tca_reason_codes"):
            failures.append(f"TCA_REASON_CODES_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_OverfitFDRMapRisk.report.json"]:
        for key in (
            "trial_family_id",
            "near_duplicate_mapping_cluster_id",
            "effective_independent_trial_count",
            "family_wise_selection_pressure",
            "false_discovery_penalty",
            "deflated_score_proxy",
            "probability_of_backtest_overfitting_proxy",
            "mapping_instability_penalty",
            "replay_instability_penalty",
            "paper_instability_penalty",
            "replay_paper_divergence_penalty",
            "rank_stability_score",
            "repeated_test_inflation_penalty",
            "holdout_walk_forward_eligibility_flag",
            "cpcv_purged_walk_forward_route_flag",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"OVERFIT_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR162E_Q_MapSensitivityStress.report.json"]:
        if not row.get("stress_test_result"):
            failures.append(f"STRESS_RESULT_MISSING::{row.get('row_id')}")
        if row.get("paper_champion_flag") or row.get("paper_challenger_flag"):
            if row.get("mapping_robustness_score") in {None, ""}:
                failures.append(f"CHAMPION_CHALLENGER_STRESS_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_EdgeAttribution.report.json"]:
        for key in (
            "baseline_expected_net_profit_per_order_candidate",
            "mapped_expected_net_profit_per_order_candidate",
            "expected_value_delta_candidate",
            "TCA_delta_candidate",
            "latency_delta_candidate",
            "fill_probability_delta_candidate",
            "queue_risk_delta_candidate",
            "capacity_delta_candidate",
            "crowding_delta_candidate",
            "overfit_delta_candidate",
            "marginal_utility_delta_candidate",
            "quantum_precompute_delta_candidate",
            "classical_fallback_delta_candidate",
        ):
            if not isinstance(row.get(key), (int, float)):
                failures.append(f"EDGE_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("not_profit_evidence_flag") is not True:
            failures.append(f"EDGE_PROFIT_EVIDENCE_FLAG_BAD::{row.get('row_id')}")


def _validate_routes_and_agents(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR162E_Q_StillNegativeMapRepair.report.json"]:
        if row.get("still_negative_after_costs_flag") and not row.get("repair_family"):
            failures.append(f"REPAIR_FAMILY_MISSING::{row.get('row_id')}")
        if row.get("not_profit_evidence_flag") is not True or row.get("no_live_authority_flag") is not True:
            failures.append(f"REPAIR_AUTHORITY_FLAG_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_OpenTradeSimMap.report.json"]:
        if row.get("hot_path_allowed_flag") is not False or row.get("no_live_authority_flag") is not True:
            failures.append(f"OPEN_TRADE_AUTHORITY_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_OwnerDashboardMapReview.report.json"]:
        if row.get("dashboard_ui_implemented_flag") not in {None, False}:
            failures.append(f"DASHBOARD_UI_CLAIMED::{row.get('row_id')}")
        if not row.get("future_dashboard_pr_ref"):
            failures.append(f"DASHBOARD_FUTURE_PR_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_ConnectorRouteReady.report.json"]:
        for flag in ("no_current_connector_binding_flag", "no_source_truth_acceptance_flag", "no_private_state_fetch_flag"):
            if row.get(flag) is not True:
                failures.append(f"CONNECTOR_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")
        if not row.get("downstream_connector_pr_ref"):
            failures.append(f"CONNECTOR_DOWNSTREAM_PR_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_MarketPortability.report.json"]:
        if row.get("stage1_prediction_market_flag") is not True or row.get("future_market_portability_flag") is not True:
            failures.append(f"MARKET_PORTABILITY_FLAG_BAD::{row.get('row_id')}")
        if row.get("no_current_connector_binding_flag") is not True or row.get("no_live_authority_flag") is not True:
            failures.append(f"MARKET_AUTHORITY_BAD::{row.get('row_id')}")
    for row in records["PR162E_Q_AgentWorkOrders.report.json"]:
        for key in (
            "work_order_id",
            "owning_agent_id",
            "agent_duty_ref",
            "source_artifact_ref",
            "source_row_ref",
            "task_type",
            "task_priority",
            "expected_input_refs",
            "expected_output_refs",
            "downstream_agent_refs",
            "downstream_pr_refs",
            "expected_agent_output_artifact",
        ):
            if not row.get(key):
                failures.append(f"AGENT_WORK_ORDER_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR162E_Q_AgentDAG.report.json"]:
        for key in ("dag_node_id", "upstream_pr_refs", "upstream_row_refs", "mapping_recipe_route", "replay_route", "open_trade_simulator_route", "connector_readiness_route", "no_orphan_proof"):
            if not row.get(key):
                failures.append(f"AGENT_DAG_FIELD_MISSING::{row.get('row_id')}::{key}")
    for filename in (
        "PR162E_Q_To_PR166_QC_Retest.report.json",
        "PR162E_Q_To_PR167.report.json",
        "PR162E_Q_To_PR162E.report.json",
        "PR162E_Q_To_PR162F.report.json",
        "PR162E_Q_To_OwnerDashboard.report.json",
        "PR162E_Q_To_CloudSwitchboard.report.json",
        "PR162E_Q_To_FutureConnectors.report.json",
    ):
        for row in records[filename]:
            for key in ("handoff_id", "source_mapping_row_ref", "model_family_selected", "objective_map_ref", "variable_encoding_ref", "solution_interpret_back_ref", "proof_vector_ref"):
                if not row.get(key):
                    failures.append(f"HANDOFF_FIELD_MISSING::{filename}::{row.get('row_id')}::{key}")
            if row.get("no_live_authority_flag") is not True:
                failures.append(f"HANDOFF_LIVE_AUTHORITY::{filename}::{row.get('row_id')}")


def _validate_crosswalk_and_artifacts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    crosswalk = records["PR162E_Q_ReportConsumerCrosswalk.report.json"]
    mapped = {row.get("report_path") for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        if f"docs/master_plan/generated/{filename}" not in mapped:
            failures.append(f"CROSSWALK_REPORT_NOT_MAPPED::{filename}")
    for filename in c.STRICT_INPUT_REPORTS:
        if f"docs/master_plan/generated/{filename}" not in mapped:
            failures.append(f"CROSSWALK_INPUT_NOT_MAPPED::{filename}")
    for row in crosswalk:
        if not row.get("owning_agent_id"):
            failures.append(f"CROSSWALK_OWNER_MISSING::{row.get('row_id')}")
        if not row.get("consuming_agent_ids") and not row.get("terminal_flag"):
            failures.append(f"CROSSWALK_CONSUMER_MISSING::{row.get('row_id')}")
    artifacts = records["PR162E_Q_ArtifactMap.report.json"]
    if not artifacts:
        failures.append("ARTIFACT_MAP_EMPTY")
    for row in artifacts:
        if not row.get("artifact_path"):
            failures.append(f"ARTIFACT_PATH_MISSING::{row.get('row_id')}")
        if not row.get("consumed_by_module"):
            failures.append(f"ARTIFACT_CONSUMER_MISSING::{row.get('row_id')}")
    for row in records["PR162E_Q_NoOrphanProof.report.json"]:
        if row.get("no_orphan_status") != "NO_ORPHAN":
            failures.append(f"NO_ORPHAN_STATUS_FAIL::{row.get('row_id')}")
        if not row.get("artifact_refs_checked"):
            failures.append(f"NO_ORPHAN_REFS_MISSING::{row.get('row_id')}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR162E_Q_FinalSummary.report.json"][0]
    if summary.get("consumed_pr162e_q_handoff_rows") != 559:
        failures.append("SUMMARY_HANDOFF_COUNT_NOT_559")
    if summary.get("deep_mapping_subset_count", 0) > c.MAP_CAPS["max_deep_mapping_rows_default_ci"]:
        failures.append("SUMMARY_DEEP_SUBSET_CAP_EXCEEDED")
    if summary.get("forbidden_authority_counts_all_zero_flag") is not True:
        failures.append("SUMMARY_AUTHORITY_NOT_ZERO")
    if summary.get("dashboard_ui_implemented_flag") is not False:
        failures.append("SUMMARY_DASHBOARD_UI_CLAIMED")
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
        if summary.get(key, 0) != 0:
            failures.append(f"SUMMARY_FORBIDDEN_COUNT_NONZERO::{key}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    for path in (repo_root / c.GENERATED_DIR).glob("PR162E_Q_*"):
        name = path.name.lower()
        if any(token in name for token in ("sha256", "checksum", "freeze", "global_digest")):
            failures.append(f"FORBIDDEN_DIGEST_ARTIFACT::{path.name}")
