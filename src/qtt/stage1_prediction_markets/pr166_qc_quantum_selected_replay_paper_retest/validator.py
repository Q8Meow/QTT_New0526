"""Validate PR166-QC generated artifacts."""

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
    _validate_evidence_rows(records, failures)
    _validate_retest_budget(records, failures)
    _validate_evidence_quality(records, failures)
    _validate_replay_paper_and_execution(records, failures)
    _validate_repair_lab(records, failures)
    _validate_dashboard_market_connector(records, failures)
    _validate_crosswalk_and_artifacts(records, failures)
    _validate_agents_and_no_orphans(records, failures)
    _validate_summary(records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(ok=not failures, failures=tuple(failures))


def _validate_schemas(
    repo_root: Path,
    payloads: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
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


def _validate_inputs(
    repo_root: Path,
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"MISSING_INPUT_REPORT::{filename}")
            continue
        payload = read_json(path)
        expanded = records_from_report_payload(repo_root, payload)
        if filename in c.EXPECTED_559_INPUTS and len(expanded) != 559:
            failures.append(f"INPUT_COUNT_DRIFT::{filename}::{len(expanded)}")
    input_rows = records["PR166_QC_InputConsumption.report.json"]
    if len(input_rows) != len(c.STRICT_INPUT_REPORTS):
        failures.append("INPUT_CONSUMPTION_ROW_COUNT_MISMATCH")
    for row in input_rows:
        if not row.get("record_count_matches_expected_flag"):
            failures.append(f"INPUT_EXPECTED_COUNT_FAIL::{row.get('source_report_ref')}")
        if row.get("no_source_truth_acceptance_flag") is not True:
            failures.append(f"INPUT_SOURCE_TRUTH_ACCEPTED::{row.get('row_id')}")


def _validate_evidence_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    required = {
        "row_id",
        "source_pr",
        "upstream_pr166_qb_row_ref",
        "upstream_pr166_qc_handoff_ref",
        "upstream_pr166_q_row_ref",
        "qku_id",
        "qku_family",
        "formula_id",
        "algorithm_id",
        "parameter_stack_id",
        "execution_route_id",
        "model_family",
        "market_scope",
        "stage1_prediction_market_flag",
        "future_market_portability_flag",
        "evidence_disposition",
        "evidence_quality_grade",
        "evidence_quality_score",
        "replay_evidence_flag",
        "paper_evidence_flag",
        "actual_retest_subset_flag",
        "structural_only_flag",
        "retest_budget_ref",
        "retest_subset_reason",
        "primary_evidence_lane",
        "evidence_lanes",
        "expected_net_profit_per_order_candidate",
        "expected_value_delta_candidate",
        "execution_adjusted_score",
        "tca_adjusted_score",
        "fill_probability_score",
        "no_fill_risk_score",
        "queue_risk_adjusted_score",
        "latency_adjusted_score",
        "capacity_adjusted_score",
        "crowding_adjusted_score",
        "risk_adjusted_score",
        "overfit_adjusted_score",
        "false_discovery_penalty",
        "report_consumer_crosswalk_ref",
        "connector_route_readiness_ref",
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
            disposition = row.get("evidence_disposition")
            if disposition not in c.EVIDENCE_DISPOSITIONS:
                failures.append(f"BAD_EVIDENCE_DISPOSITION::{filename}::{row_id}::{disposition}")
            if disposition in c.FORBIDDEN_EVIDENCE_DISPOSITIONS:
                failures.append(f"FORBIDDEN_EVIDENCE_DISPOSITION::{filename}::{row_id}::{disposition}")
            grade = row.get("evidence_quality_grade")
            if grade not in c.EVIDENCE_QUALITY_GRADES:
                failures.append(f"BAD_EVIDENCE_QUALITY_GRADE::{filename}::{row_id}::{grade}")
            primary = row.get("primary_evidence_lane")
            lanes = row.get("evidence_lanes") or []
            if primary not in c.EVIDENCE_LANES:
                failures.append(f"BAD_PRIMARY_EVIDENCE_LANE::{filename}::{row_id}::{primary}")
            if primary not in lanes:
                failures.append(f"PRIMARY_LANE_NOT_IN_LANES::{filename}::{row_id}")
            for lane in lanes:
                if lane not in c.EVIDENCE_LANES:
                    failures.append(f"BAD_EVIDENCE_LANE::{filename}::{row_id}::{lane}")
            _validate_authority(row, failures, filename, row_id)
            if row.get("hot_path_allowed_flag") is not False:
                failures.append(f"HOT_PATH_ALLOWED::{filename}::{row_id}")
            if row.get("classical_fallback_flag") is not True:
                failures.append(f"CLASSICAL_FALLBACK_MISSING::{filename}::{row_id}")
            if row.get("future_live_candidate_flag") is not False:
                failures.append(f"FUTURE_LIVE_CANDIDATE_TRUE::{filename}::{row_id}")


def _validate_authority(
    row: dict[str, Any],
    failures: list[str],
    filename: str,
    row_id: str,
) -> None:
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


def _validate_retest_budget(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    budget = records["PR166_QC_RetestBudget.report.json"][0]
    subset_rows = [
        row
        for row in records["PR166_QC_SubsetSelection.report.json"]
        if row.get("actual_retest_subset_flag")
    ]
    if len(subset_rows) != budget.get("actual_replay_paper_subset_size"):
        failures.append("RETEST_SUBSET_SIZE_MISMATCH")
    if len(subset_rows) > c.RETEST_CAPS["max_actual_replay_paper_rows_default_ci"]:
        failures.append("RETEST_SUBSET_CAP_EXCEEDED")
    for key, cap in c.RETEST_CAPS.items():
        if budget.get(key) != cap:
            failures.append(f"RETEST_CAP_VALUE_MISMATCH::{key}")
    role_counts: dict[str, int] = {}
    for row in subset_rows:
        reason = str(row.get("retest_subset_reason") or "")
        parts = reason.split("::")
        role = parts[1] if len(parts) > 1 else str(row.get("champion_challenger_role"))
        role_counts[role] = role_counts.get(role, 0) + 1
    for role, count in role_counts.items():
        if count > c.RETEST_CAPS["max_rows_per_role_default_ci"]:
            failures.append(f"ROLE_CAP_EXCEEDED::{role}::{count}")
    if [row["deterministic_sort_key"] for row in subset_rows] != sorted(row["deterministic_sort_key"] for row in subset_rows):
        failures.append("RETEST_SUBSET_SORT_NOT_DETERMINISTIC")


def _validate_evidence_quality(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_QC_EvidenceQuality.report.json"]
    if not rows:
        failures.append("EVIDENCE_QUALITY_EMPTY")
    for row in rows:
        score = row.get("evidence_quality_score")
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            failures.append(f"EVIDENCE_QUALITY_SCORE_BAD::{row.get('row_id')}")
        if row.get("paper_champion_flag") and row.get("evidence_quality_grade") not in {
            "A_REPLAY_AND_PAPER_STRONG_NONLIVE",
            "B_REPLAY_STRONG_PAPER_PENDING",
        }:
            failures.append(f"WEAK_EVIDENCE_PAPER_CHAMPION::{row.get('row_id')}")
        if min(row.get("sample_sufficiency_score", 0), row.get("scenario_coverage_score", 0)) < 0.5:
            lanes = set(row.get("evidence_lanes") or [])
            if not lanes.intersection(
                {
                    "REPLAY_RETEST_REQUIRED",
                    "PAPER_RETEST_REQUIRED",
                    "DATA_GAP_REPAIR_NEEDED",
                    "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING",
                    "BENCHMARK_ONLY_RESIDUAL",
                    "STILL_NEGATIVE_AFTER_TCA_LATENCY_FILL_RISK",
                    "REPLAY_PAPER_REPAIR_PROPOSAL",
                    "AUTOMAPPER_NEEDED",
                }
            ):
                failures.append(f"WEAK_SAMPLE_NOT_ROUTED::{row.get('row_id')}")


def _validate_replay_paper_and_execution(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename in (
        "PR166_QC_ReplayEvidence.report.json",
        "PR166_QC_PaperEvidence.report.json",
        "PR166_QC_TCAEvidence.report.json",
        "PR166_QC_OverfitFDRRetest.report.json",
        "PR166_QC_PortfolioUtility.report.json",
        "PR166_QC_RegimeEvidence.report.json",
    ):
        for row in records[filename]:
            row_id = row.get("row_id")
            for key in (
                "replay_evidence_score",
                "paper_evidence_score",
                "calibration_score",
                "brier_score_proxy",
                "sample_sufficiency_score",
                "scenario_coverage_score",
                "replay_paper_confidence_score",
            ):
                if not isinstance(row.get(key), (int, float)):
                    failures.append(f"SCORE_FIELD_MISSING::{filename}::{row_id}::{key}")
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
                "benchmark_to_replay_translation_penalty",
                "replay_to_paper_translation_penalty",
                "total_tca_estimate",
            ):
                if not isinstance(row.get(key), (int, float)):
                    failures.append(f"TCA_COMPONENT_MISSING::{filename}::{row_id}::{key}")
            if not row.get("tca_reason_codes"):
                failures.append(f"TCA_REASON_CODES_MISSING::{filename}::{row_id}")
            for key in (
                "trial_family_id",
                "near_duplicate_cluster_id",
                "effective_independent_trial_count",
                "family_wise_selection_pressure",
                "false_discovery_penalty",
                "deflated_score_proxy",
                "probability_of_backtest_overfitting_proxy",
                "replay_instability_penalty",
                "paper_instability_penalty",
                "replay_paper_divergence_penalty",
                "seed_instability_penalty",
                "rank_stability_score",
                "repeated_test_inflation_penalty",
            ):
                if row.get(key) in {None, ""}:
                    failures.append(f"OVERFIT_FIELD_MISSING::{filename}::{row_id}::{key}")
            for key in (
                "event_cluster",
                "question_market_cluster",
                "formula_family_cluster",
                "qku_family_cluster",
                "algorithm_family_cluster",
                "quantum_model_family_cluster",
                "regime_cluster",
                "time_to_resolution_bucket",
                "liquidity_bucket",
                "correlation_proxy_bucket",
                "diversification_contribution",
                "concentration_penalty",
                "final_marginal_utility_evidence_score",
            ):
                if row.get(key) in {None, ""}:
                    failures.append(f"PORTFOLIO_FIELD_MISSING::{filename}::{row_id}::{key}")
            if row.get("quantum_backend_execution_flag") is not False:
                failures.append(f"QUANTUM_BACKEND_EXECUTED::{filename}::{row_id}")


def _validate_repair_lab(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_QC_ReplayPaperRepairLab.report.json"]
    if len(rows) != 559:
        failures.append("REPAIR_LAB_ROW_COUNT_NOT_559")
    for row in rows:
        for key in (
            "repair_row_id",
            "upstream_pr166_qc_row_ref",
            "evidence_negative_reason",
            "repair_family",
            "proposed_formula_delta",
            "proposed_parameter_delta",
            "proposed_execution_route_delta",
            "proposed_retest_delta",
            "proposed_threshold_delta",
            "expected_edge_delta_candidate",
            "expected_tca_delta_candidate",
            "expected_latency_delta_candidate",
            "expected_fill_delta_candidate",
            "expected_calibration_delta_candidate",
            "expected_net_profit_delta_candidate",
            "replay_retest_route_ref",
            "paper_retest_route_ref",
            "downstream_pr162e_q_route_ref",
            "downstream_pr167_route_ref",
            "owning_agent_id",
            "reviewer_agent_id",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"REPAIR_FIELD_MISSING::{row.get('row_id')}::{key}")
        if row.get("not_profit_evidence_flag") is not True:
            failures.append(f"REPAIR_PROFIT_EVIDENCE::{row.get('row_id')}")
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"REPAIR_LIVE_AUTHORITY::{row.get('row_id')}")


def _validate_dashboard_market_connector(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QC_OwnerDashboardReview.report.json"]:
        if not row.get("dashboard_review_id"):
            failures.append(f"DASHBOARD_REVIEW_ID_MISSING::{row.get('row_id')}")
        if row.get("dashboard_ui_implemented_flag") not in {None, False}:
            failures.append(f"DASHBOARD_UI_CLAIMED::{row.get('row_id')}")
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"DASHBOARD_LIVE_AUTHORITY::{row.get('row_id')}")
        if not row.get("future_dashboard_pr_ref"):
            failures.append(f"DASHBOARD_FUTURE_PR_REF_MISSING::{row.get('row_id')}")
    for row in records["PR166_QC_MarketPortability.report.json"]:
        if row.get("stage1_prediction_market_flag") is not True:
            failures.append(f"MARKET_STAGE1_MISSING::{row.get('row_id')}")
        if row.get("future_market_portability_flag") is not True:
            failures.append(f"MARKET_PORTABILITY_MISSING::{row.get('row_id')}")
        if row.get("no_current_connector_binding_flag") is not True:
            failures.append(f"MARKET_CONNECTOR_BOUND::{row.get('row_id')}")
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"MARKET_LIVE_AUTHORITY::{row.get('row_id')}")
        if not row.get("compatible_future_market_families"):
            failures.append(f"MARKET_FAMILIES_MISSING::{row.get('row_id')}")
    for row in records["PR166_QC_ConnectorRouteReadiness.report.json"]:
        if not row.get("connector_route_id"):
            failures.append(f"CONNECTOR_ROUTE_ID_MISSING::{row.get('row_id')}")
        for flag in (
            "no_current_connector_binding_flag",
            "no_source_truth_acceptance_flag",
            "no_private_state_fetch_flag",
        ):
            if row.get(flag) is not True:
                failures.append(f"CONNECTOR_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")
        if not row.get("downstream_connector_pr_ref"):
            failures.append(f"CONNECTOR_DOWNSTREAM_PR_MISSING::{row.get('row_id')}")


def _validate_crosswalk_and_artifacts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    crosswalk = records["PR166_QC_ReportConsumerCrosswalk.report.json"]
    mapped_paths = {row.get("report_path") for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        path = f"docs/master_plan/generated/{filename}"
        if path not in mapped_paths:
            failures.append(f"CROSSWALK_REPORT_NOT_MAPPED::{filename}")
    for row in crosswalk:
        if not row.get("owning_agent_id"):
            failures.append(f"CROSSWALK_OWNER_MISSING::{row.get('row_id')}")
        if not row.get("consuming_agent_ids") and not row.get("terminal_flag"):
            failures.append(f"CROSSWALK_CONSUMER_MISSING::{row.get('row_id')}")
        if row.get("terminal_flag") and not row.get("terminal_reason"):
            failures.append(f"CROSSWALK_TERMINAL_REASON_MISSING::{row.get('row_id')}")
    artifacts = records["PR166_QC_ArtifactMap.report.json"]
    if not artifacts:
        failures.append("ARTIFACT_MAP_EMPTY")
    for row in artifacts:
        if not row.get("artifact_path"):
            failures.append(f"ARTIFACT_PATH_MISSING::{row.get('row_id')}")
        if not row.get("consumed_by_module"):
            failures.append(f"ARTIFACT_CONSUMER_MISSING::{row.get('row_id')}")
        if row.get("terminal_flag") and not row.get("terminal_reason"):
            failures.append(f"ARTIFACT_TERMINAL_REASON_MISSING::{row.get('row_id')}")


def _validate_agents_and_no_orphans(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_QC_AgentWorkOrders.report.json"]:
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
        if row.get("no_live_authority_flag") is not True:
            failures.append(f"AGENT_WORK_ORDER_LIVE_AUTHORITY::{row.get('row_id')}")
    for row in records["PR166_QC_AgentDAG.report.json"]:
        for key in (
            "dag_node_id",
            "upstream_pr_refs",
            "upstream_row_refs",
            "replay_route",
            "paper_route",
            "automapper_route",
            "open_trade_simulator_route",
            "connector_readiness_route",
            "no_orphan_proof",
        ):
            if not row.get(key):
                failures.append(f"AGENT_DAG_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR166_QC_NoOrphanProof.report.json"]:
        if row.get("no_orphan_status") != "NO_ORPHAN":
            failures.append(f"NO_ORPHAN_STATUS_FAIL::{row.get('row_id')}")
        if not row.get("artifact_refs_checked"):
            failures.append(f"NO_ORPHAN_REFS_MISSING::{row.get('row_id')}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_QC_FinalSummary.report.json"][0]
    if summary.get("consumed_pr166_qc_handoff_rows") != 559:
        failures.append("SUMMARY_HANDOFF_COUNT_NOT_559")
    if summary.get("replay_paper_retest_subset_count", 0) > c.RETEST_CAPS["max_actual_replay_paper_rows_default_ci"]:
        failures.append("SUMMARY_SUBSET_CAP_EXCEEDED")
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
    for path in (repo_root / c.GENERATED_DIR).glob("PR166_QC_*"):
        name = path.name.lower()
        if any(token in name for token in ("sha256", "checksum", "freeze", "global_digest")):
            failures.append(f"FORBIDDEN_DIGEST_ARTIFACT::{path.name}")
