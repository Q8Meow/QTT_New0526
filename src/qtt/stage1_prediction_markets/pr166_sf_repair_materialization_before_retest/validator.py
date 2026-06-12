"""Fail-closed validator for PR166-SF generated artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import (
    ALLOWED_CONNECTOR_DEPENDENCY_CLASSES,
    ALLOWED_NO_ORPHAN_STATUSES,
    ALLOWED_PRIMARY_REPAIR_CLASSES,
    ALLOWED_REPAIRED_COMPUTABILITY_STATUSES,
    ALLOWED_REPAIR_TARGET_CLASSES,
    ALLOWED_RETEST_QUEUE_STATES,
    ALLOWED_RETEST_READINESS_STATUSES,
    ALLOWED_SOURCE_AUTHORITY_CLASSES,
    ALLOWED_TARGET_PRIORITY_TIERS,
    ALLOWED_VENUE_SEMANTIC_DEPENDENCY_CLASSES,
    FORBIDDEN_STATUS_VALUES,
    RetestQueueState,
)
from .io import read_json, records_from_report_payload, resolve_repo_relative
from .report_writer import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, round6


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


ROW_REQUIRED_FIELDS = (
    "artifact_id",
    "row_id",
    "created_by_pr",
    "roadmap_pr_id",
    "candidate_packet_id",
    "qku_id",
    "formula_id",
    "algorithm_id",
    "parameter_stack_id",
    "condition_fingerprint_id",
    "scenario_group_id",
    "combination_id",
    "upstream_pr_refs",
    "upstream_artifact_refs",
    "upstream_row_refs",
    "upstream_value_refs",
    "source_roadmap_pr_refs",
    "source_artifact_refs",
    "source_row_refs",
    "repair_target_class",
    "primary_repair_class",
    "secondary_repair_classes",
    "pre_repair_selection_state",
    "pre_repair_net_edge_after_costs",
    "pre_repair_edge_lcb",
    "pre_repair_cost_drag_ratio",
    "dominant_negative_edge_root_cause",
    "dominant_missing_field",
    "exact_missing_fields",
    "candidate_fill_values",
    "candidate_fill_value_units",
    "candidate_fill_value_source_authority_class",
    "candidate_fill_value_confidence",
    "formula_repair_action_ref",
    "algorithm_repair_action_ref",
    "parameter_repair_action_ref",
    "tca_repair_action_ref",
    "microstructure_repair_action_ref",
    "probability_edge_repair_action_ref",
    "quantum_repair_action_ref",
    "post_repair_preview_net_edge_after_costs",
    "post_repair_preview_edge_lcb",
    "repair_delta_net_edge",
    "repair_delta_confidence",
    "repair_uncertainty_penalty",
    "repair_confidence_score",
    "repair_evidence_depth_score",
    "repair_verification_test_vector_ref",
    "repair_smoke_test_result_ref",
    "executable_materialization_ref",
    "qku_tradability_readiness_score",
    "point_in_time_no_leakage_status",
    "source_candidate_dedupe_key",
    "source_disagreement_status",
    "repair_threshold_policy_ref",
    "counterfactual_sensitivity_ref",
    "parameter_robustness_ref",
    "dag_node_ref",
    "dag_edge_refs",
    "false_discovery_risk_adjustment",
    "overfit_risk_adjustment",
    "rank_instability_adjustment",
    "capacity_score_after_repair",
    "crowding_penalty_after_repair",
    "correlation_cluster_penalty_after_repair",
    "quantum_mapping_readiness_after_repair",
    "repaired_computability_status",
    "retest_readiness_after_repair",
    "downstream_pr_refs",
    "downstream_artifact_refs",
    "downstream_agent_consumers",
    "owning_agent",
    "reviewer_or_challenger_agent",
    "validator_ref",
    "manifest_ref",
    "schema_ref",
    "authority_boundary_ref",
    "no_orphan_status",
    "terminal_status_flag",
    "terminal_status_reason",
    "deterministic_sort_key",
    "connector_dependency_class",
    "venue_semantic_dependency_class",
    "future_connector_pr_refs",
    "future_venue_readiness_route",
    "connector_binding_allowed_in_this_pr",
    "private_state_fetch_allowed_in_this_pr",
    "runtime_cash_receipt_allowed_in_this_pr",
    "source_truth_acceptance_allowed_in_this_pr",
)


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {
        filename: records_from_report_payload(repo_root, payload)
        for filename, payload in reports.items()
    }
    _validate_payload_contracts(repo_root, reports, records, failures)
    _validate_row_contracts(records, failures)
    _validate_manifest(reports, records, failures)
    _validate_summary(records, failures)
    _validate_input_consumption(records, failures)
    _validate_target_universe(records, failures)
    _validate_repair_preview(records, failures)
    _validate_retest_queue(records, failures)
    _validate_quantum(records, failures)
    _validate_external_receipts(records, failures)
    _validate_connector_routing(records, failures)
    _validate_no_orphans(records, failures)
    _validate_status_drift(repo_root, reports, records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SF report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-SF report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR166-SF schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.REQUIRED_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR166-SF upstream input: {filename}")


def _validate_payload_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("roadmap_pr_id") == c.PR_ID, failures, f"{filename} roadmap_pr_id mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == c.VALIDATION_STATUS, failures, f"{filename} validation_status mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} record_count mismatch")
        path = repo_root / c.GENERATED_DIR / filename
        _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds root report size limit")
        if filename in c.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root duplicates sharded rows")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("shard_files"), failures, f"{filename} missing shard files")
        for shard_ref in payload.get("shard_files") or []:
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"{filename} missing shard {shard_ref}")
            if shard_path.exists():
                _expect(shard_path.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_ref} exceeds shard size limit")
                shard_payload = read_json(shard_path)
                _expect(shard_payload.get("parent_report_filename") == filename, failures, f"{shard_ref} parent mismatch")
                _expect(shard_payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{shard_ref} schema mismatch")


def _validate_row_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for field in ROW_REQUIRED_FIELDS:
                if field in {"secondary_repair_classes", "candidate_fill_values"}:
                    _expect(field in row, failures, f"{filename} row {row.get('row_id')} missing {field}")
                    continue
                value = row.get(field)
                _expect(value not in ("", None), failures, f"{filename} row {row.get('row_id')} missing {field}")
                if field in {
                    "upstream_pr_refs",
                    "upstream_artifact_refs",
                    "upstream_row_refs",
                    "upstream_value_refs",
                    "source_roadmap_pr_refs",
                    "source_artifact_refs",
                    "source_row_refs",
                    "exact_missing_fields",
                    "candidate_fill_value_units",
                    "dag_edge_refs",
                    "downstream_pr_refs",
                    "downstream_artifact_refs",
                    "downstream_agent_consumers",
                    "future_connector_pr_refs",
                }:
                    _expect(value != [], failures, f"{filename} row {row.get('row_id')} empty {field}")
            _expect(row.get("repair_target_class") in ALLOWED_REPAIR_TARGET_CLASSES, failures, f"{filename} row invalid repair target")
            _expect(row.get("primary_repair_class") in ALLOWED_PRIMARY_REPAIR_CLASSES, failures, f"{filename} row invalid primary repair class")
            _expect(row.get("priority_tier") in ALLOWED_TARGET_PRIORITY_TIERS, failures, f"{filename} row invalid priority tier")
            _expect(row.get("no_orphan_status") in ALLOWED_NO_ORPHAN_STATUSES, failures, f"{filename} row invalid no_orphan_status")
            _expect(row.get("connector_dependency_class") in ALLOWED_CONNECTOR_DEPENDENCY_CLASSES, failures, f"{filename} row invalid connector dependency")
            _expect(row.get("venue_semantic_dependency_class") in ALLOWED_VENUE_SEMANTIC_DEPENDENCY_CLASSES, failures, f"{filename} row invalid venue dependency")
            _expect(row.get("source_authority_class") in ALLOWED_SOURCE_AUTHORITY_CLASSES, failures, f"{filename} row invalid source authority")
            _expect(row.get("repaired_computability_status") in ALLOWED_REPAIRED_COMPUTABILITY_STATUSES, failures, f"{filename} row invalid computability")
            _expect(row.get("retest_readiness_after_repair") in ALLOWED_RETEST_READINESS_STATUSES, failures, f"{filename} row invalid retest readiness")
            _expect(row.get("validator_ref") == c.VALIDATOR_REF, failures, f"{filename} row validator mismatch")
            _expect(row.get("manifest_ref") == c.MANIFEST_REF, failures, f"{filename} row manifest mismatch")
            _expect(row.get("created_by_pr") == c.PR_ID, failures, f"{filename} row created_by_pr mismatch")
            _expect(row.get("roadmap_pr_id") == c.PR_ID, failures, f"{filename} row roadmap_pr_id mismatch")
            _expect(row.get("connector_binding_allowed_in_this_pr") is False, failures, f"{filename} connector binding flag invalid")
            _expect(row.get("private_state_fetch_allowed_in_this_pr") is False, failures, f"{filename} private state flag invalid")
            _expect(row.get("runtime_cash_receipt_allowed_in_this_pr") is False, failures, f"{filename} runtime cash flag invalid")
            _expect(row.get("source_truth_acceptance_allowed_in_this_pr") is False, failures, f"{filename} source truth flag invalid")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in c.DOWNSTREAM_PR_REFS, failures, f"{filename} row invalid downstream route {route}")
            for route in row.get("future_connector_pr_refs") or []:
                _expect(
                    route in {*c.FUTURE_CONNECTOR_PR_REFS, "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW", "TERMINAL_BY_NATURE_WITH_REASON"},
                    failures,
                    f"{filename} row invalid future connector route {route}",
                )
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR166_SF_ReportManifest.report.json"]
    root_rows = [row for row in manifest if row.get("manifest_entry_class") == "ROOT_REPORT"]
    shard_rows = [row for row in manifest if row.get("manifest_entry_class") == "SHARD_REPORT"]
    listed = {row["report_name"] + ".report.json" for row in root_rows}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "PR166-SF manifest does not list exactly required root reports")
    expected_shards: dict[str, tuple[str, int]] = {}
    for filename, payload in reports.items():
        for shard in payload.get("shard_manifest_refs") or []:
            expected_shards[shard["shard_path"]] = (filename, int(shard["row_count"]))
    listed_shards = {row["report_path"] for row in shard_rows}
    _expect(listed_shards == set(expected_shards), failures, "PR166-SF manifest does not list exactly required shard reports")
    for row in root_rows:
        filename = row["report_name"] + ".report.json"
        _expect(row["row_count"] == reports[filename]["record_count"], failures, f"manifest row count mismatch {filename}")
        _expect(row["schema_path"].endswith(c.REPORT_SCHEMA_REFS[filename]), failures, f"manifest schema mismatch {filename}")
    for row in shard_rows:
        parent, count = expected_shards.get(row["report_path"], ("", -1))
        _expect(row["parent_report_name"] + ".report.json" == parent, failures, f"manifest shard parent mismatch {row['report_path']}")
        _expect(row["row_count"] == count, failures, f"manifest shard row count mismatch {row['report_path']}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_SF_FinalSummary.report.json"][0]
    equality = {
        "repair_target_rows": len(records["PR166_SF_TargetUniverseRegistry.report.json"]),
        "negative_net_edge_root_cause_rows": len(records["PR166_SF_NegativeEdgeRootCauseLedger.report.json"]),
        "repaired_candidate_rows": len(records["PR166_SF_RepairedPayloadRegistry.report.json"]),
        "external_repair_signal_candidate_rows": len(records["PR166_SF_ExternalRepairSignalRegistry.report.json"]),
        "candidate_values_filled": len(records["PR166_SF_MissingValueFillLedger.report.json"]),
        "formula_repair_actions": len(records["PR166_SF_FormulaQKURepairRegistry.report.json"]),
        "algorithm_repair_actions": len(records["PR166_SF_FormulaQKURepairRegistry.report.json"]),
        "parameter_repair_actions": len(records["PR166_SF_ParameterRobustnessLedger.report.json"]),
        "tca_repair_actions": len(records["PR166_SF_TCATermLedger.report.json"]),
        "probability_edge_repair_actions": len(records["PR166_SF_ProbabilityEdgeRepairLedger.report.json"]),
        "microstructure_repair_actions": len(records["PR166_SF_MicrostructureRepairLedger.report.json"]),
        "quantum_structural_repair_actions": len(records["PR166_SF_QuantumStructureLedger.report.json"]),
        "repaired_test_vector_rows": len(records["PR166_SF_TestVectorRegistry.report.json"]),
        "repaired_smoke_test_rows": len(records["PR166_SF_SmokeTestLedger.report.json"]),
        "agent_repair_task_rows": len(records["PR166_SF_AgentRepairTaskQueue.report.json"]),
        "repair_threshold_materiality_policy_rows": len(records["PR166_SF_RepairThresholdPolicy.report.json"]),
        "source_candidate_dedupe_disagreement_rows": len(records["PR166_SF_SourceDedupeLedger.report.json"]),
        "qku_tradability_readiness_rows": len(records["PR166_SF_QKUTradabilityLedger.report.json"]),
        "executable_formula_algorithm_materialization_rows": len(records["PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json"]),
        "repair_counterfactual_sensitivity_rows": len(records["PR166_SF_RepairSensitivityLedger.report.json"]),
        "parameter_robustness_perturbation_rows": len(records["PR166_SF_ParameterRobustnessLedger.report.json"]),
        "point_in_time_no_leakage_repair_audit_rows": len(records["PR166_SF_NoLeakageRepairAudit.report.json"]),
        "dag_repair_orchestration_rows": len(records["PR166_SF_RepairDAGLedger.report.json"]),
        "retest_readiness_score_rows": len(records["PR166_SF_RetestReadinessRegistry.report.json"]),
        "materialization_actuality_audit_rows": len(records["PR166_SF_MaterializationAudit.report.json"]),
        "agent_duty_application_rows": len(records["PR166_SF_AgentDutyLedger.report.json"]),
        "external_search_coverage_receipt_rows": len(records["PR166_SF_ExternalSearchReceipt.report.json"]),
        "connector_reference_routing_rows": len(records["PR166_SF_ConnectorRefRouting.report.json"]),
    }
    for field, expected in equality.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} mismatch")
    _expect(summary.get("roadmap_pr_id") == c.PR_ID, failures, "summary roadmap_pr_id mismatch")
    _expect(summary.get("pr165_d2_repair_queue_rows_consumed") == 3985, failures, "repair queue consumption must be 3985")
    _expect(summary.get("pr165_d2_negative_net_edge_rows_consumed") == 3150, failures, "negative net edge consumption must be 3150")
    _expect(summary.get("pr165_d2_selected_retest_rows_consumed") == 298, failures, "selected retest consumption must be 298")
    _expect(summary.get("pr165_d2_quantum_priority_rows_consumed") == 6502, failures, "quantum priority consumption must be 6502")
    _expect(summary.get("pr165_d2_agent_roster_rows_consumed") == 8, failures, "agent roster consumption must be 8")
    _expect(summary.get("repair_target_rows") == 6502, failures, "target universe must be 6502")
    _expect(summary.get("repaired_retest_ready_rows", 0) > 0, failures, "PR166-SF must produce retest-ready rows")
    for field in (
        "metadata_only_rows",
        "placeholder_rows",
        "unknown_status_rows",
        "generic_blocker_rows",
        "orphan_rows",
        "authority_violation_count",
        *ZERO_AUTHORITY_KEYS,
    ):
        _expect(summary.get(field) == 0, failures, f"summary {field} must be zero")
    _expect(summary.get("next_recommended_pr") == "PR166-S2", failures, "summary next PR should be PR166-S2 when rows are ready")


def _validate_input_consumption(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    input_rows = records["PR166_SF_InputConsumptionAudit.report.json"]
    by_report = {row["expected_input_report"]: row for row in input_rows}
    for report, expected in c.EXPECTED_ROW_COUNTS.items():
        row = by_report.get(report)
        _expect(row is not None, failures, f"input consumption missing {report}")
        if row:
            _expect(row["expected_row_count"] == expected, failures, f"input expected count mismatch {report}")
            _expect(row["observed_row_count"] == expected, failures, f"input observed count mismatch {report}")
            _expect(row["row_count_reconciled_flag"] is True, failures, f"input row count not reconciled {report}")
    sharded = [row for row in input_rows if row["shard_count"] > 0]
    _expect(sharded, failures, "input audit must include sharded inputs")
    _expect(all(row["input_consumption_mode"] == "ROOT_REPORT_PLUS_ALL_SHARDS" for row in sharded), failures, "sharded input mode invalid")


def _validate_target_universe(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    targets = records["PR166_SF_TargetUniverseRegistry.report.json"]
    _expect(len(targets) == 6502, failures, "target universe must cover QKU/formula/algorithm universe")
    states = Counter(row["pre_repair_selection_state"] for row in targets)
    _expect(states["ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST"] == 537, failures, "explicit repair-before-retest count mismatch")
    _expect(states["EXCLUDED_BY_NEGATIVE_NET_EDGE_WITH_REASON"] == 3150, failures, "negative-net-edge count mismatch")
    _expect(states["SELECTED_AS_CHAMPION"] + states["SELECTED_AS_DIVERSIFYING_CANDIDATE"] == 298, failures, "selected retest count mismatch")
    for row in targets:
        _expect(row["test_vector_materialized_flag"] is True, failures, f"target missing test vector {row['candidate_packet_id']}")
        _expect(row["repair_smoke_test_passed_flag"] is True, failures, f"target smoke failed {row['candidate_packet_id']}")
        _expect(row["profit_evidence_created_flag"] is False, failures, f"target profit flag invalid {row['candidate_packet_id']}")


def _validate_repair_preview(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_SF_RepairPreviewScoreRegistry.report.json"]:
        expected = round6(
            row["pre_repair_gross_edge"]
            - row["repaired_fee_cost_component"]
            - row["repaired_spread_cost_component"]
            - row["repaired_slippage_cost_component"]
            - row["repaired_market_impact_cost_component"]
            - row["repaired_latency_cost_component"]
            - row["repaired_liquidity_cost_component"]
            - row["repaired_settlement_cost_component"]
        )
        _expect(abs(expected - row["post_repair_preview_net_edge_after_costs"]) <= 0.00001, failures, f"repair preview formula mismatch {row['candidate_packet_id']}")
        _expect(row["positive_repair_preview_class"] != "LIVE_PROFIT_EVIDENCE", failures, f"profit evidence class invalid {row['candidate_packet_id']}")


def _validate_retest_queue(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    allowed = ALLOWED_RETEST_QUEUE_STATES
    queue = records["PR166_SF_RepairedCandidateRetestQueue.report.json"]
    ready_states = {
        RetestQueueState.READY_FOR_PR166_S2_RETEST_AFTER_REPAIR.value,
        RetestQueueState.READY_FOR_PR166_S2_RETEST_AS_NEAR_BREAK_EVEN_LEARNING.value,
    }
    _expect(all(row["retest_queue_state"] in allowed for row in queue), failures, "invalid retest queue state")
    ready = [row for row in queue if row["retest_queue_state"] in ready_states]
    _expect(ready, failures, "no repaired retest-ready rows")
    for row in ready:
        _expect(row["repair_verification_test_vector_ref"], failures, f"ready row missing test vector {row['candidate_packet_id']}")
        _expect(row["repair_smoke_test_result_ref"], failures, f"ready row missing smoke test {row['candidate_packet_id']}")
        _expect(row["point_in_time_no_leakage_status"].startswith("POINT_IN_TIME"), failures, f"ready row leakage status invalid {row['candidate_packet_id']}")
        _expect(row["positive_repair_preview_is_profit_evidence_flag"] is False, failures, f"ready row profit evidence flag invalid {row['candidate_packet_id']}")


def _validate_quantum(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    structure = records["PR166_SF_QuantumStructureLedger.report.json"]
    router = records["PR166_SF_QuantumRepairRouter.report.json"]
    _expect(len(structure) == 6502, failures, "quantum structure rows must cover quantum universe")
    _expect(len(router) == 6502, failures, "quantum router rows must cover quantum universe")
    for row in structure:
        _expect(row["objective_direction"], failures, f"quantum objective missing {row['candidate_packet_id']}")
        _expect(row["variables"], failures, f"quantum variables missing {row['candidate_packet_id']}")
        _expect(row["constraints"], failures, f"quantum constraints missing {row['candidate_packet_id']}")
        _expect(row["linear_coefficients"], failures, f"quantum linear coefficients missing {row['candidate_packet_id']}")
        _expect("comparator_baseline" in row, failures, f"quantum comparator missing {row['candidate_packet_id']}")
        _expect(row["quantum_backend_execution_count"] == 0, failures, f"quantum backend count invalid {row['candidate_packet_id']}")
        _expect(row["quantum_advantage_claim_count"] == 0, failures, f"quantum advantage count invalid {row['candidate_packet_id']}")
    for row in router:
        _expect(row["backend_quantum_execution_created"] is False, failures, f"quantum backend flag invalid {row['candidate_packet_id']}")
        _expect(row["quantum_advantage_claim_created"] is False, failures, f"quantum advantage flag invalid {row['candidate_packet_id']}")


def _validate_external_receipts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    receipt = records["PR166_SF_ExternalSearchReceipt.report.json"]
    _expect(receipt, failures, "external search receipt missing")
    _expect(all(row["retrieval_attempted_flag"] is True for row in receipt), failures, "external retrieval attempts not recorded")
    _expect(all(row["source_truth_acceptance_count"] == 0 for row in receipt), failures, "external receipt accepted source truth")
    signals = records["PR166_SF_ExternalRepairSignalRegistry.report.json"]
    _expect(len(signals) == len(c.EXTERNAL_REFERENCE_ROWS), failures, "external signal count mismatch")
    _expect(all(row["value_source_authority_class"] == "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH" for row in signals), failures, "external signals must remain candidate provisional")


def _validate_connector_routing(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_SF_ConnectorRefRouting.report.json"]
    _expect(len(rows) == 6502, failures, "connector routing must cover target universe")
    for row in rows:
        _expect(row["connector_binding_allowed_in_this_pr"] is False, failures, f"connector binding flag invalid {row['candidate_packet_id']}")
        _expect(row["private_state_fetch_allowed_in_this_pr"] is False, failures, f"private state flag invalid {row['candidate_packet_id']}")
        _expect(row["runtime_cash_receipt_allowed_in_this_pr"] is False, failures, f"runtime cash flag invalid {row['candidate_packet_id']}")
        _expect(row["source_truth_acceptance_allowed_in_this_pr"] is False, failures, f"source truth flag invalid {row['candidate_packet_id']}")
        _expect(row["future_connector_pr_refs"], failures, f"future connector refs missing {row['candidate_packet_id']}")


def _validate_no_orphans(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            _expect(row["no_orphan_status"] in ALLOWED_NO_ORPHAN_STATUSES, failures, f"{filename} orphan status invalid")
            _expect(row["upstream_artifact_refs"], failures, f"{filename} upstream refs missing")
            _expect(row["downstream_pr_refs"], failures, f"{filename} downstream refs missing")
            _expect(row["owning_agent"], failures, f"{filename} owning agent missing")


def _validate_status_drift(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        for value in _flatten_values(payload):
            if "\\" in value:
                failures.append(f"{filename} contains backslash path/value: {value}")
            if value in FORBIDDEN_STATUS_VALUES:
                failures.append(f"{filename} contains forbidden status value: {value}")
    for filename, rows in records.items():
        for row in rows:
            for value in _flatten_values(row):
                if value in FORBIDDEN_STATUS_VALUES:
                    failures.append(f"{filename} row {row.get('row_id')} contains forbidden status value: {value}")
    for schema_name in c.SCHEMA_FILENAMES:
        schema_text = (repo_root / c.SCHEMA_DIR / schema_name).read_text(encoding="utf-8")
        for token in FORBIDDEN_STATUS_VALUES:
            if f'"{token}"' in schema_text:
                failures.append(f"{schema_name} embeds forbidden status token {token}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    sha_paths = sorted((repo_root / c.GENERATED_DIR).glob("*.sha256"))
    _expect(not sha_paths, failures, f"generated sha256 artifacts found: {[str(path) for path in sha_paths[:5]]}")
    atomic_sha = repo_root / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
    _expect(not atomic_sha.exists(), failures, "AtomicRows.bundle.sha256 must not exist")


def _flatten_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_flatten_values(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_flatten_values(item))
        return out
    return []


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
