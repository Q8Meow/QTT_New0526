"""Validate PR167 generated artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import FORBIDDEN_AUTHORITY_FLAGS, ZERO_AUTHORITY_KEYS
from .io import read_json, records_from_report_payload
from .report_writer import schema_filenames


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
    _validate_sources(records, failures)
    _validate_simulator_rows(records, failures)
    _validate_budget(records, failures)
    _validate_shadow_orders(records, failures)
    _validate_price_book_lifecycle_route_models(records, failures)
    _validate_survivor_failure_firewall(records, failures)
    _validate_downstream_routes(records, failures)
    _validate_crosswalk_and_artifacts(records, failures)
    _validate_agents_and_no_orphans(records, failures)
    _validate_summary(records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(ok=not failures, failures=tuple(failures))


def _validate_schemas(repo_root: Path, payloads: dict[str, dict[str, Any]], failures: list[str]) -> None:
    schema_names = set(schema_filenames())
    for filename, payload in payloads.items():
        schema_ref = str(payload.get("schema_ref") or "")
        if not schema_ref:
            failures.append(f"MISSING_SCHEMA_REF::{filename}")
            continue
        if schema_ref not in schema_names:
            failures.append(f"UNKNOWN_SCHEMA_REF::{filename}::{schema_ref}")
        if not (repo_root / c.SCHEMA_DIR / schema_ref).exists():
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
        expanded = records_from_report_payload(repo_root, read_json(path))
        if filename in c.EXPECTED_559_INPUTS and len(expanded) != 559:
            failures.append(f"INPUT_COUNT_DRIFT::{filename}::{len(expanded)}")
    input_rows = records["PR167_InputConsumption.report.json"]
    if len(input_rows) != len(c.STRICT_INPUT_REPORTS):
        failures.append("INPUT_CONSUMPTION_ROW_COUNT_MISMATCH")
    for row in input_rows:
        if not row.get("record_count_matches_expected_flag"):
            failures.append(f"INPUT_EXPECTED_COUNT_FAIL::{row.get('source_report_ref')}")
        for flag in (
            "no_source_truth_acceptance_flag",
            "no_connector_binding_flag",
            "no_profit_evidence_flag",
            "no_backend_execution_flag",
            "no_live_order_execution_flag",
        ):
            if row.get(flag) is not True:
                failures.append(f"INPUT_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")
    upstream = records["PR167_UpstreamReportUse.report.json"]
    if len(upstream) != len(c.STRICT_INPUT_REPORTS):
        failures.append("UPSTREAM_REPORT_USE_ROW_COUNT_MISMATCH")
    for row in upstream:
        if row.get("consumed_by_pr167_flag") is not True and not row.get("terminal_flag"):
            failures.append(f"UPSTREAM_NOT_CONSUMED_OR_TERMINAL::{row.get('row_id')}")
        if not row.get("fields_used"):
            failures.append(f"UPSTREAM_FIELDS_USED_MISSING::{row.get('row_id')}")


def _validate_sources(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    sources = records["PR167_SourceSimParams.report.json"]
    if len(sources) < 8:
        failures.append("SOURCE_SIM_PARAMS_TOO_FEW")
    if not any(row.get("official_flag") for row in sources):
        failures.append("SOURCE_SIM_OFFICIAL_SOURCE_MISSING")
    if not any(row.get("non_official_flag") for row in sources):
        failures.append("SOURCE_SIM_NON_OFFICIAL_SOURCE_MISSING")
    count_fields = (
        "simulator_parameters_extracted_count",
        "order_book_parameters_extracted_count",
        "fill_model_parameters_extracted_count",
        "queue_risk_parameters_extracted_count",
        "queue_survival_parameters_extracted_count",
        "latency_parameters_extracted_count",
        "TCA_parameters_extracted_count",
        "implementation_shortfall_parameters_extracted_count",
        "capacity_parameters_extracted_count",
        "circuit_breaker_patterns_extracted_count",
        "shadow_order_patterns_extracted_count",
        "route_ladder_patterns_extracted_count",
        "repair_strategy_parameters_extracted_count",
        "future_market_portability_notes_count",
        "candidate_values_extracted_count",
    )
    for row in sources:
        for key in count_fields:
            if not isinstance(row.get(key), int) or row[key] < 0:
                failures.append(f"SOURCE_COUNT_BAD::{row.get('row_id')}::{key}")
        if row.get("candidate_values_extracted_count", 0) <= 0 and not row.get("rejected_reason"):
            failures.append(f"SOURCE_CANDIDATE_VALUES_MISSING::{row.get('row_id')}")
        for flag in (
            "no_source_truth_acceptance_flag",
            "no_connector_binding_flag",
            "no_profit_evidence_flag",
            "no_backend_execution_flag",
            "no_live_order_execution_flag",
        ):
            if row.get(flag) is not True:
                failures.append(f"SOURCE_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")


def _validate_simulator_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
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
            for key in c.REQUIRED_SIM_FIELDS:
                if key not in row:
                    failures.append(f"REQUIRED_FIELD_MISSING::{filename}::{row_id}::{key}")
            disposition = row.get("simulator_disposition")
            if disposition not in c.SIMULATOR_DISPOSITIONS:
                failures.append(f"BAD_SIMULATOR_DISPOSITION::{filename}::{row_id}::{disposition}")
            if disposition in c.FORBIDDEN_SIMULATOR_DISPOSITIONS:
                failures.append(f"FORBIDDEN_SIMULATOR_DISPOSITION::{filename}::{row_id}::{disposition}")
            grade = row.get("simulator_quality_grade")
            if grade not in c.SIMULATOR_QUALITY_GRADES:
                failures.append(f"BAD_SIMULATOR_QUALITY_GRADE::{filename}::{row_id}::{grade}")
            _validate_authority(row, failures, filename, row_id)
            if row.get("classical_fallback_ref") in {"", None, c.NOT_APPLICABLE}:
                failures.append(f"CLASSICAL_FALLBACK_REF_MISSING::{filename}::{row_id}")
            if row.get("hot_path_allowed_flag") is not False:
                failures.append(f"HOT_PATH_ALLOWED::{filename}::{row_id}")
            if row.get("simulator_champion_flag") or row.get("simulator_challenger_flag"):
                if not row.get("counterfactual_route_ref") or not row.get("downstream_pr166_qc_retest_route_ref"):
                    failures.append(f"CHAMPION_CHALLENGER_ROUTE_MISSING::{filename}::{row_id}")


def _validate_authority(row: dict[str, Any], failures: list[str], filename: str, row_id: str) -> None:
    for key in ZERO_AUTHORITY_KEYS:
        if row.get(key, 0) != 0:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_COUNT::{filename}::{row_id}::{key}")
    for flag in FORBIDDEN_AUTHORITY_FLAGS:
        if row.get(flag) is not False:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_FLAG::{filename}::{row_id}::{flag}")
    for flag in ("simulated_order_flag", "shadow_order_flag", "no_live_authority_flag"):
        if row.get(flag) is not True:
            failures.append(f"ROW_REQUIRED_TRUE_FLAG::{filename}::{row_id}::{flag}")


def _validate_budget(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    budget = records["PR167_SimBudget.report.json"][0]
    subset = [row for row in records["PR167_SimEligibility.report.json"] if row.get("actual_sim_subset_flag")]
    if len(subset) != budget.get("actual_sim_subset_size"):
        failures.append("SIM_SUBSET_SIZE_MISMATCH")
    if len(subset) > c.SIM_CAPS["max_actual_sim_rows_default_ci"]:
        failures.append("SIM_SUBSET_CAP_EXCEEDED")
    for key, cap in c.SIM_CAPS.items():
        if budget.get(key) != cap:
            failures.append(f"SIM_CAP_VALUE_MISMATCH::{key}")
    open_trade = [row for row in records["PR167_SimEligibility.report.json"] if row.get("open_trade_sim_route_flag")]
    if len(open_trade) <= c.SIM_CAPS["max_actual_sim_rows_default_ci"]:
        missing = [row["row_id"] for row in open_trade if not row.get("actual_sim_subset_flag")]
        if missing:
            failures.append(f"OPEN_TRADE_ROUTE_NOT_ACTUAL_SUBSET::{missing[:3]}")
    if [row["deterministic_sort_key"] for row in subset] != sorted(row["deterministic_sort_key"] for row in subset):
        failures.append("SIM_SUBSET_SORT_NOT_DETERMINISTIC")
    if budget.get("no_unbounded_simulation_execution_flag") is not True:
        failures.append("SIM_BUDGET_UNBOUNDED_FLAG_MISSING")


def _validate_shadow_orders(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR167_ShadowOrderAudit.report.json"]
    actual = [row for row in records["PR167_SimEligibility.report.json"] if row["actual_sim_subset_flag"]]
    actual_refs = {row["shadow_order_audit_ref"] for row in actual}
    shadow_refs = {row["shadow_order_id"] for row in rows}
    missing = sorted(actual_refs - shadow_refs)
    if missing:
        failures.append(f"SHADOW_AUDIT_MISSING_FOR_ACTUAL::{missing[:3]}")
    for row in rows:
        if row.get("simulator_only_flag") is not True:
            failures.append(f"SHADOW_NOT_SIMULATOR_ONLY::{row.get('row_id')}")
        if row.get("real_order_id") is not None:
            failures.append(f"SHADOW_REAL_ORDER_ID_PRESENT::{row.get('row_id')}")
        for flag in (
            "live_order_authority_flag",
            "live_order_execution_flag",
            "real_fill_flag",
            "real_pnl_flag",
            "profit_evidence_flag",
        ):
            if row.get(flag) is not False:
                failures.append(f"SHADOW_FORBIDDEN_FLAG::{row.get('row_id')}::{flag}")


def _validate_price_book_lifecycle_route_models(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR167_OrderIntent.report.json"]:
        for key in (
            "order_intent_id",
            "side",
            "YES_NO_side",
            "price_candidate",
            "quantity_candidate",
            "time_in_force_candidate",
            "passive_aggressive_route_candidate",
        ):
            if row.get(key) in {None, ""}:
                failures.append(f"ORDER_INTENT_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR167_OrderBookState.report.json"]:
        if row.get("book_state_provenance") not in {"generated_structural", "structural_unavailable"}:
            failures.append(f"BAD_BOOK_PROVENANCE::{row.get('row_id')}")
        if row.get("no_live_market_call_flag") is not True:
            failures.append(f"BOOK_LIVE_MARKET_CALL_FLAG_MISSING::{row.get('row_id')}")
    for row in records["PR167_PriceSideNorm.report.json"]:
        if row.get("probability_unit") != "PROBABILITY_0_TO_1":
            failures.append(f"BAD_PROBABILITY_UNIT::{row.get('row_id')}")
        if row.get("latency_unit") != "MILLISECONDS":
            failures.append(f"BAD_LATENCY_UNIT::{row.get('row_id')}")
    for row in records["PR167_OrderLifecycle.report.json"]:
        states = row.get("lifecycle_states") or []
        if not states:
            failures.append(f"LIFECYCLE_TRACE_MISSING::{row.get('row_id')}")
        for state in states:
            if state.get("simulated_not_real_flag") is not True or state.get("no_live_authority_flag") is not True:
                failures.append(f"LIFECYCLE_AUTHORITY_BAD::{row.get('row_id')}")
    for row in records["PR167_CounterfactualRouteSim.report.json"]:
        for key in (
            "classical_fallback_route_score",
            "quantum_precompute_route_score",
            "hybrid_selects_classical_executes_route_score",
            "passive_limit_route_score",
            "near_touch_limit_route_score",
            "aggressive_limit_route_score",
            "no_trade_route_score",
            "selected_counterfactual_winner",
        ):
            if key not in row:
                failures.append(f"COUNTERFACTUAL_FIELD_MISSING::{row.get('row_id')}::{key}")
    for filename in (
        "PR167_FillNoFillSim.report.json",
        "PR167_PartialFillSim.report.json",
        "PR167_QueuePositionSim.report.json",
        "PR167_QueueSurvivalSim.report.json",
        "PR167_LatencySim.report.json",
        "PR167_TCASim.report.json",
        "PR167_ImplementationShortfallSim.report.json",
        "PR167_CapacityCrowdingSim.report.json",
        "PR167_CancelReplaceSim.report.json",
    ):
        for row in records[filename]:
            if row.get("actual_sim_subset_flag") and row.get("structural_only_flag"):
                failures.append(f"ACTUAL_ROW_STRUCTURAL_ONLY::{filename}::{row.get('row_id')}")


def _validate_survivor_failure_firewall(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    survivors = [row for row in records["PR167_SimSurvivorRegistry.report.json"] if row["simulator_survival_flag"]]
    failures_rows = [row for row in records["PR167_SimFailureRegistry.report.json"] if row["simulator_failure_reason"]]
    if not survivors:
        failures.append("SIM_SURVIVOR_REGISTRY_EMPTY")
    if not failures_rows:
        failures.append("SIM_FAILURE_REGISTRY_EMPTY")
    for row in survivors:
        if not row.get("survival_reason") or "SURVIVED" not in row["survival_reason"]:
            failures.append(f"SURVIVOR_REASON_BAD::{row.get('row_id')}")
        if not row.get("downstream_retest_route_ref"):
            failures.append(f"SURVIVOR_RETEST_ROUTE_MISSING::{row.get('row_id')}")
    for row in failures_rows:
        if row.get("primary_failure_reason") in {"", "NOT_FAILED_SIMULATOR_ROUTE", None}:
            failures.append(f"FAILURE_PRIMARY_REASON_MISSING::{row.get('row_id')}")
        if not row.get("repair_route_ref"):
            failures.append(f"FAILURE_REPAIR_ROUTE_MISSING::{row.get('row_id')}")
    for row in records["PR167_SimPromotionFirewall.report.json"]:
        if row.get("live_ready_flag") is not False:
            failures.append(f"FIREWALL_LIVE_READY_TRUE::{row.get('row_id')}")
        if row.get("future_live_authority_pr_required_flag") is not True:
            failures.append(f"FIREWALL_FUTURE_AUTHORITY_FLAG_MISSING::{row.get('row_id')}")
        if row.get("live_promotion_claim_flag") is not False:
            failures.append(f"FIREWALL_LIVE_PROMOTION_TRUE::{row.get('row_id')}")
    coverage = records["PR167_SimCalibrationCoverage.report.json"]
    coverage_refs = {row["simulator_row_ref"] for row in coverage}
    for row in records["PR167_SimChampChallenger.report.json"]:
        if row.get("simulator_champion") or row.get("simulator_challenger"):
            if row.get("source_sim_row_ref") not in coverage_refs:
                failures.append(f"CHAMPION_COVERAGE_MISSING::{row.get('row_id')}")
            if not row.get("downstream_pr166_qc_retest_route_ref"):
                failures.append(f"CHAMPION_RETEST_ROUTE_MISSING::{row.get('row_id')}")


def _validate_downstream_routes(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename in (
        "PR167_To_PR166_QC_Retest.report.json",
        "PR167_To_PR162E.report.json",
        "PR167_To_PR162F.report.json",
        "PR167_To_OwnerDashboard.report.json",
        "PR167_To_CloudSwitchboard.report.json",
        "PR167_To_FutureConnectors.report.json",
        "PR167_ConnectorRouteReady.report.json",
        "PR167_MarketPortability.report.json",
        "PR167_OwnerDashboardReview.report.json",
    ):
        for row in records[filename]:
            if row.get("no_live_authority_flag") is not True:
                failures.append(f"ROUTE_NO_LIVE_FLAG_MISSING::{filename}::{row.get('row_id')}")
            if row.get("connector_semantic_binding_flag") is not False:
                failures.append(f"ROUTE_CONNECTOR_BOUND::{filename}::{row.get('row_id')}")
            if row.get("source_truth_acceptance_flag") is not False:
                failures.append(f"ROUTE_SOURCE_TRUTH_ACCEPTED::{filename}::{row.get('row_id')}")
    for row in records["PR167_ConnectorRouteReady.report.json"]:
        if row.get("no_current_connector_binding_flag") is not True:
            failures.append(f"CONNECTOR_CURRENT_BINDING_TRUE::{row.get('row_id')}")
        if row.get("no_private_state_fetch_flag") is not True:
            failures.append(f"CONNECTOR_PRIVATE_FETCH_TRUE::{row.get('row_id')}")
    for row in records["PR167_OwnerDashboardReview.report.json"]:
        if row.get("dashboard_ui_implemented_flag") not in {None, False}:
            failures.append(f"DASHBOARD_UI_IMPLEMENTED::{row.get('row_id')}")


def _validate_crosswalk_and_artifacts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    crosswalk = records["PR167_ReportConsumerCrosswalk.report.json"]
    mapped = {row["report_path"] for row in crosswalk}
    for filename in c.REPORT_FILENAMES:
        if f"docs/master_plan/generated/{filename}" not in mapped:
            failures.append(f"CROSSWALK_REPORT_MISSING::{filename}")
    for row in crosswalk:
        if not (row.get("consuming_agent_ids") or row.get("consuming_downstream_reports") or row.get("terminal_flag")):
            failures.append(f"CROSSWALK_ORPHAN::{row.get('row_id')}")
    artifacts = records["PR167_ArtifactMap.report.json"]
    if not artifacts:
        failures.append("ARTIFACT_MAP_EMPTY")
    if not any(row.get("artifact_type") == "generated_schema" for row in artifacts):
        failures.append("ARTIFACT_MAP_SCHEMA_ROWS_MISSING")
    if not any(row.get("artifact_type") == "generated_shard_report" for row in artifacts):
        failures.append("ARTIFACT_MAP_SHARD_ROWS_MISSING")
    for row in artifacts:
        if not (row.get("consumed_by_agent") or row.get("consumed_by_report") or row.get("terminal_flag")):
            failures.append(f"ARTIFACT_ORPHAN::{row.get('row_id')}")


def _validate_agents_and_no_orphans(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR167_AgentWorkOrders.report.json"]:
        for key in (
            "work_order_id",
            "owning_agent_id",
            "agent_duty_ref",
            "source_artifact_ref",
            "source_row_ref",
            "task_type",
            "expected_input_refs",
            "expected_output_refs",
            "downstream_agent_refs",
        ):
            value = row.get(key)
            if value is None or value == "" or value == []:
                failures.append(f"AGENT_WORK_ORDER_FIELD_MISSING::{row.get('row_id')}::{key}")
    for row in records["PR167_AgentDAG.report.json"]:
        if not row.get("downstream_agent_refs"):
            failures.append(f"AGENT_DAG_DOWNSTREAM_MISSING::{row.get('row_id')}")
        if row.get("governance_visibility_flag") is not True or row.get("commander_visibility_flag") is not True:
            failures.append(f"AGENT_DAG_VISIBILITY_BAD::{row.get('row_id')}")
    for row in records["PR167_NoOrphanProof.report.json"]:
        if row.get("no_orphan_status") != "NO_ORPHAN" or row.get("orphan_count") != 0:
            failures.append(f"NO_ORPHAN_FAIL::{row.get('row_id')}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR167_FinalSummary.report.json"][0]
    rows = records["PR167_SimEligibility.report.json"]
    if summary.get("consumed_pr167_handoff_rows") != len(rows):
        failures.append("SUMMARY_CONSUMED_ROW_COUNT_MISMATCH")
    if summary.get("actual_sim_subset_count") != sum(1 for row in rows if row["actual_sim_subset_flag"]):
        failures.append("SUMMARY_ACTUAL_SUBSET_MISMATCH")
    if summary.get("simulator_disposition_counts") != dict(sorted(Counter(row["simulator_disposition"] for row in rows).items())):
        failures.append("SUMMARY_DISPOSITION_COUNTS_MISMATCH")
    if summary.get("simulator_quality_grade_counts") != dict(sorted(Counter(row["simulator_quality_grade"] for row in rows).items())):
        failures.append("SUMMARY_GRADE_COUNTS_MISMATCH")
    if summary.get("forbidden_authority_counts_all_zero_flag") is not True:
        failures.append("SUMMARY_FORBIDDEN_AUTHORITY_NOT_ZERO")
    for key in ZERO_AUTHORITY_KEYS:
        if summary.get(key, 0) != 0:
            failures.append(f"SUMMARY_FORBIDDEN_AUTHORITY_COUNT::{key}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    for path in (repo_root / c.GENERATED_DIR).glob("PR167_*"):
        name = path.name.lower()
        if any(token in name for token in ("sha256", "checksum", "freeze", "digest")):
            failures.append(f"FORBIDDEN_HASH_AUTHORITY_ARTIFACT::{path.relative_to(repo_root).as_posix()}")
