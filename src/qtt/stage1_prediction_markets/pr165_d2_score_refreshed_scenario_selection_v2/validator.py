"""Fail-closed validator for PR165-D2 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import (
    ALLOWED_COMPUTABILITY_STATUSES,
    ALLOWED_CONNECTOR_DEPENDENCY_CLASSES,
    ALLOWED_DOWNSTREAM_ROUTES,
    ALLOWED_NO_ORPHAN_STATUSES,
    ALLOWED_SELECTION_STATES,
    ALLOWED_SOURCE_AUTHORITY_CLASSES,
    ALLOWED_VALUE_AUTHORITY_LANES,
    ALLOWED_VENUE_SEMANTIC_DEPENDENCY_CLASSES,
    FORBIDDEN_STATUS_VALUES,
    SelectionState,
)
from .io import read_json, records_from_report_payload, resolve_repo_relative
from .report_writer import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, candidate_selection_score, numeric, round6


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


ROW_REQUIRED_FIELDS = (
    "artifact_id",
    "row_id",
    "created_by_pr",
    "qku_id",
    "formula_id",
    "algorithm_id",
    "candidate_packet_id",
    "condition_fingerprint_id",
    "scenario_group_id",
    "combination_id",
    "upstream_pr_refs",
    "upstream_artifact_refs",
    "upstream_row_refs",
    "upstream_value_refs",
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
    "value_authority_lane",
    "source_authority_class",
    "computability_status",
    "selection_state",
    "materialization_action_ref",
    "repair_route_ref",
    "score_policy_ref",
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
    records = {filename: records_from_report_payload(repo_root, payload) for filename, payload in reports.items()}
    _validate_payload_contracts(repo_root, reports, records, failures)
    _validate_row_contracts(records, failures)
    _validate_manifest(reports, records, failures)
    _validate_summary(records, failures)
    _validate_ranking(records, failures)
    _validate_tca(records, failures)
    _validate_repair(records, failures)
    _validate_quantum(records, failures)
    _validate_connector_boundaries(records, failures)
    _validate_agent_handoffs(records, failures)
    _validate_optional_inputs(records, failures)
    _validate_status_drift(repo_root, reports, records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR165-D2 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR165-D2 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR165-D2 schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.REQUIRED_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR165-D2 upstream input: {filename}")


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
            if payload.get("record_count", 0) > 0:
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
                if row.get(field) in ("", None):
                    failures.append(f"{filename} row {row.get('row_id')} missing {field}")
                if field in {"upstream_pr_refs", "upstream_artifact_refs", "downstream_pr_refs", "downstream_artifact_refs", "future_connector_pr_refs"} and row.get(field) == []:
                    failures.append(f"{filename} row {row.get('row_id')} empty {field}")
            _expect(row.get("no_orphan_status") in ALLOWED_NO_ORPHAN_STATUSES, failures, f"{filename} row invalid no_orphan_status")
            _expect(row.get("value_authority_lane") in ALLOWED_VALUE_AUTHORITY_LANES, failures, f"{filename} row invalid value_authority_lane")
            _expect(row.get("source_authority_class") in ALLOWED_SOURCE_AUTHORITY_CLASSES, failures, f"{filename} row invalid source_authority_class")
            _expect(row.get("computability_status") in ALLOWED_COMPUTABILITY_STATUSES, failures, f"{filename} row invalid computability_status")
            _expect(row.get("selection_state") in ALLOWED_SELECTION_STATES, failures, f"{filename} row invalid selection_state")
            _expect(row.get("connector_dependency_class") in ALLOWED_CONNECTOR_DEPENDENCY_CLASSES, failures, f"{filename} row invalid connector_dependency_class")
            _expect(row.get("venue_semantic_dependency_class") in ALLOWED_VENUE_SEMANTIC_DEPENDENCY_CLASSES, failures, f"{filename} row invalid venue_semantic_dependency_class")
            _expect(row.get("validator_ref") == c.VALIDATOR_REF, failures, f"{filename} row validator mismatch")
            _expect(row.get("manifest_ref") == c.MANIFEST_REF, failures, f"{filename} row manifest mismatch")
            _expect(row.get("created_by_pr") == c.PR_ID, failures, f"{filename} row created_by_pr mismatch")
            _expect(row.get("connector_binding_allowed_in_this_pr") is False, failures, f"{filename} row connector binding flag invalid")
            _expect(row.get("private_state_fetch_allowed_in_this_pr") is False, failures, f"{filename} row private state flag invalid")
            _expect(row.get("runtime_cash_receipt_allowed_in_this_pr") is False, failures, f"{filename} row runtime cash flag invalid")
            _expect(row.get("source_truth_acceptance_allowed_in_this_pr") is False, failures, f"{filename} row source truth flag invalid")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in ALLOWED_DOWNSTREAM_ROUTES, failures, f"{filename} row invalid downstream route {route}")
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    listed = {row["report_name"] + ".report.json" for row in records["PR165_D2_ReportManifest.report.json"]}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "PR165-D2 manifest does not list exactly required reports")
    for row in records["PR165_D2_ReportManifest.report.json"]:
        filename = row["report_name"] + ".report.json"
        _expect(row["row_count"] == reports[filename]["record_count"], failures, f"manifest row count mismatch {filename}")
        _expect(row["schema_path"].endswith(c.REPORT_SCHEMA_REFS[filename]), failures, f"manifest schema mismatch {filename}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR165_D2_FinalSummary.report.json"][0]
    equality = {
        "net_edge_adjusted_candidate_ranking_rows": len(records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"]),
        "replay_paper_retest_batch_v2_rows": len(records["PR165_D2_ReplayPaperRetestBatchV2.report.json"]),
        "repair_aware_selection_queue_rows": len(records["PR165_D2_RepairAwareSelectionQueue.report.json"]),
        "quantum_candidate_priority_v2_rows": len(records["PR165_D2_QuantumCandidatePriorityV2.report.json"]),
        "agent_roster_discovery_rows": len(records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]),
        "agent_duty_source_crosswalk_rows": len(records["PR165_D2_AgentDutySourceCrosswalk.report.json"]),
        "score_component_provenance_rows": len(records["PR165_D2_ScoreComponentProvenanceLedger.report.json"]),
        "prediction_market_probability_edge_rows": len(records["PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json"]),
        "microstructure_feature_rows": len(records["PR165_D2_MicrostructureFeatureLedger.report.json"]),
        "qku_formula_algorithm_computability_rows": len(records["PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json"]),
    }
    for field, expected in equality.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} mismatch")
    _expect(summary.get("refreshed_score_rows_consumed") == 3985, failures, "refreshed score rows must be 3985")
    _expect(summary.get("refreshed_memory_rows_consumed") == 3985, failures, "refreshed memory rows must be 3985")
    _expect(summary.get("qku_formula_algorithm_computability_rows") == 6502, failures, "computability rows must be 6502")
    _expect(summary.get("optional_pr166_sf_present") is False, failures, "PR166-SF should be optional absent in current baseline")
    _expect(summary.get("optional_pr166_sf_missing_handled_by_pr166_sm_repair_handoff") is True, failures, "PR166-SF optional fallback not recorded")
    _expect(summary.get("optional_pr164_present") is True, failures, "optional PR164 presence not recorded")
    for field in (
        "metadata_only_rows",
        "placeholder_rows",
        "unknown_status_rows",
        "generic_blocker_rows",
        "orphan_rows",
        "authority_violation_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "connector_truth_count",
        "venue_account_truth_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "live_order_authority_count",
        "profit_evidence_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_authority_count",
        "atomicrows_bundle_sha_reference_count",
        "new_sha256_artifact_count",
    ):
        _expect(summary.get(field) == 0, failures, f"summary {field} must be zero")


def _validate_ranking(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"]
    _expect(len(rows) == 3985, failures, "ranking rows must cover PR166-SM refreshed score rows")
    ranks = sorted(int(row["pr165_d2_rank"]) for row in rows)
    _expect(ranks == list(range(1, len(rows) + 1)), failures, "PR165-D2 ranks are not contiguous")
    for row in rows:
        expected_score = candidate_selection_score({field: numeric(row, field) for field in c.SCORE_WEIGHTS})
        _expect(abs(expected_score - numeric(row, "candidate_selection_score_v2")) <= 0.00001, failures, f"score formula mismatch {row['candidate_packet_id']}")
        if row["selected_for_retest_v2_flag"]:
            _expect(row["net_edge_after_costs"] >= c.MATERIAL_NEGATIVE_NET_EDGE_THRESHOLD, failures, f"selected materially negative net edge {row['candidate_packet_id']}")
            _expect(row["selection_state"] != SelectionState.ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST.value, failures, f"repair-needed row selected for retest {row['candidate_packet_id']}")
        for penalty in c.NEGATIVE_SCORE_COMPONENTS:
            _expect(numeric(row, penalty) >= 0, failures, f"negative penalty {penalty} {row['candidate_packet_id']}")


def _validate_tca(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR165_D2_TCADecompositionSelectionLedger.report.json"]:
        expected_net = round6(
            row["gross_edge"]
            - row["fee_cost_component"]
            - row["spread_cost_component"]
            - row["slippage_cost_component"]
            - row["market_impact_cost_component"]
            - row["latency_cost_component"]
            - row["liquidity_cost_component"]
            - row["settlement_cost_component"]
        )
        _expect(abs(expected_net - row["net_edge_after_costs"]) <= 0.00001, failures, f"TCA net edge mismatch {row['candidate_packet_id']}")


def _validate_repair(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR165_D2_RepairAwareSelectionQueue.report.json"]:
        if row["repair_needed_flag"]:
            _expect(row["route_to_pr166_sf_flag"] is True, failures, f"repair route missing {row['candidate_packet_id']}")
            _expect(row["route_to_pr165_d2_retest_flag"] is False, failures, f"repair-needed row routed to retest {row['candidate_packet_id']}")
            _expect(row["optional_pr166_sf_queue_status"] == "OPTIONAL_NOT_PRESENT_CONSUMED_PR166_SM_REPAIR_HANDOFF", failures, "PR166-SF optional handling mismatch")


def _validate_quantum(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR165_D2_QuantumCandidatePriorityV2.report.json"]
    _expect(len(rows) == 6502, failures, "quantum priority rows must cover PR166-SM quantum universe")
    for row in rows:
        _expect(row["backend_quantum_execution_created"] is False, failures, f"quantum backend flag invalid {row['candidate_packet_id']}")
        _expect(row["quantum_advantage_claim_created"] is False, failures, f"quantum advantage flag invalid {row['candidate_packet_id']}")
        _expect(row["objective_terms"], failures, f"quantum objective terms missing {row['candidate_packet_id']}")
        _expect(row["variable_domains"], failures, f"quantum variable domains missing {row['candidate_packet_id']}")
        _expect(row["classical_comparator_refs"], failures, f"quantum comparator missing {row['candidate_packet_id']}")


def _validate_connector_boundaries(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            _expect(row.get("connector_binding_allowed_in_this_pr") is False, failures, f"{filename} connector binding allowed")
            _expect(row.get("private_state_fetch_allowed_in_this_pr") is False, failures, f"{filename} private state allowed")
            _expect(row.get("runtime_cash_receipt_allowed_in_this_pr") is False, failures, f"{filename} runtime cash allowed")
            _expect(row.get("source_truth_acceptance_allowed_in_this_pr") is False, failures, f"{filename} source truth allowed")
    connector_rows = records["PR165_D2_ConnectorVenueReadinessReferenceRouting.report.json"]
    _expect(len(connector_rows) == len(records["PR165_D2_NetEdgeAdjustedCandidateRanking.report.json"]), failures, "connector readiness rows must cover ranking rows")


def _validate_agent_handoffs(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    roster = records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]
    crosswalk = records["PR165_D2_AgentDutySourceCrosswalk.report.json"]
    _expect(len(roster) >= 8, failures, "agent roster discovery must include expected agents")
    _expect(len(crosswalk) == len(roster), failures, "agent duty crosswalk must cover roster rows")
    roster_ids = {row["agent_id"] for row in roster}
    _expect(
        {"research_agent", "parameter_selector_agent", "risk_manager_agent", "quantum_optimizer_agent", "commander_agent", "governance_agent", "dashboard_agent"}.issubset(roster_ids),
        failures,
        "agent roster missing required duty agents",
    )
    for row in records["PR165_D2_AgentSelectionHandoff.report.json"]:
        _expect(row["handoff_generated_after_roster_audit_flag"] is True, failures, "agent handoff generated before roster audit flag invalid")
        _expect(row["agent_roster_audit_passed_flag"] is True, failures, "agent roster audit passed flag invalid")


def _validate_optional_inputs(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    optional = records["PR165_D2_OptionalInputResolutionLedger.report.json"]
    by_ref = {row["optional_artifact_ref"]: row for row in optional}
    _expect(
        by_ref["PR166_SF_RepairedCandidateRetestQueue.report.json"]["absence_handling"] == "OPTIONAL_NOT_PRESENT_CONSUMED_PR166_SM_REPAIR_HANDOFF",
        failures,
        "optional PR166-SF repaired queue fallback missing",
    )
    _expect(any(row["optional_input_pr"] == "PR164" and row["present_flag"] for row in optional), failures, "optional PR164 present row missing")
    for row in records["PR165_D2_RowCountReconciliationLedger.report.json"]:
        _expect(row["rows_not_invented_flag"] is True, failures, f"row count reconciliation invented rows for {row['artifact_ref']}")


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
        out = []
        for item in value:
            out.extend(_flatten_values(item))
        return out
    return []


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
