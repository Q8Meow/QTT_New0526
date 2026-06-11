"""Fail-closed validator for PR166-SM generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .cost_model import COST_FIELDS, numeric
from .enums import (
    ALLOWED_COMPUTABILITY_STATUSES,
    ALLOWED_DOWNSTREAM_ROUTES,
    ALLOWED_MEMORY_OUTCOMES,
    ALLOWED_NO_ORPHAN_STATUSES,
    ALLOWED_PRIMARY_CLASSIFICATIONS,
    ALLOWED_SOURCE_AUTHORITY_CLASSES,
    ALLOWED_VALUE_AUTHORITY_LANES,
    FORBIDDEN_STATUS_VALUES,
)
from .io import read_json, records_from_report_payload, resolve_repo_relative
from .normalization import round6
from .report_writer import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES
from .scoring import refreshed_net_edge_score


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
    "scenario_id",
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
    "computable_formula_ref",
    "materialization_action_ref",
    "repair_route_ref",
    "score_policy_ref",
    "normalization_policy_ref",
    "condition_similarity_policy_ref",
    "created_at_utc",
    "deterministic_sort_key",
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
    _validate_summary_counts(records, failures)
    _validate_economic_scores(records, failures)
    _validate_rank_and_memory(records, failures)
    _validate_quantum_authority(records, failures)
    _validate_input_consumption(records, failures)
    _validate_status_drift(repo_root, reports, records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SM report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-SM report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        path = repo_root / c.SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SM schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.REQUIRED_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR166-SM upstream input: {filename}")


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
            if int(payload.get("record_count", 0) or 0) > 0:
                _expect(payload.get("shard_files"), failures, f"{filename} missing shard files")
        for shard_ref in payload.get("shard_files") or []:
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"{filename} missing shard {shard_ref}")
            if shard_path.exists():
                _expect(shard_path.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_ref} exceeds shard size limit")
                shard_payload = read_json(shard_path)
                _expect(shard_payload.get("parent_report_filename") == filename, failures, f"{shard_ref} parent mismatch")


def _validate_row_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for field in ROW_REQUIRED_FIELDS:
                if field == "upstream_value_refs" and row.get(field) == []:
                    continue
                _expect(row.get(field) not in ("", [], None), failures, f"{filename} row {row.get('row_id')} missing {field}")
            _expect(row.get("no_orphan_status") in ALLOWED_NO_ORPHAN_STATUSES, failures, f"{filename} row invalid no_orphan_status")
            _expect(row.get("value_authority_lane") in ALLOWED_VALUE_AUTHORITY_LANES, failures, f"{filename} row invalid value_authority_lane")
            _expect(row.get("source_authority_class") in ALLOWED_SOURCE_AUTHORITY_CLASSES, failures, f"{filename} row invalid source_authority_class")
            _expect(row.get("computability_status") in ALLOWED_COMPUTABILITY_STATUSES, failures, f"{filename} row invalid computability_status")
            _expect(row.get("validator_ref") == c.VALIDATOR_REF, failures, f"{filename} row validator mismatch")
            _expect(row.get("manifest_ref") == c.MANIFEST_REF, failures, f"{filename} row manifest mismatch")
            _expect(row.get("created_by_pr") == c.PR_ID, failures, f"{filename} row created_by_pr mismatch")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in ALLOWED_DOWNSTREAM_ROUTES, failures, f"{filename} row invalid downstream route {route}")
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")
            if "primary_classification" in row:
                _expect(row["primary_classification"] in ALLOWED_PRIMARY_CLASSIFICATIONS, failures, f"{filename} row invalid classification")
            if "memory_outcome" in row:
                _expect(row["memory_outcome"] in ALLOWED_MEMORY_OUTCOMES, failures, f"{filename} row invalid memory outcome")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR166_SM_ReportManifest.report.json"]
    listed = {row.get("report_name") + ".report.json" for row in manifest}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "PR166-SM manifest does not list exactly required reports")
    for row in manifest:
        filename = row["report_name"] + ".report.json"
        _expect(row["row_count"] == reports[filename]["record_count"], failures, f"manifest row count mismatch {filename}")
        _expect(row["schema_path"].endswith(c.REPORT_SCHEMA_REFS[filename]), failures, f"manifest schema mismatch {filename}")


def _validate_summary_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_SM_FinalSummary.report.json"][0]
    equality = {
        "score_refresh_row_count": len(records["PR166_SM_RefreshedScoreRegistry.report.json"]),
        "memory_refresh_row_count": len(records["PR166_SM_RefreshedMemoryLedger.report.json"]),
        "rank_delta_row_count": len(records["PR166_SM_NetEdgeRankDeltaRegistry.report.json"]),
        "condition_winner_count": len(records["PR166_SM_ConditionScopedWinnerRegistry.report.json"]),
        "condition_loser_count": len(records["PR166_SM_ConditionScopedLoserRegistry.report.json"]),
        "cost_dominated_count": len(records["PR166_SM_CostDominatedDowngradeRegistry.report.json"]),
        "latency_dominated_count": len(records["PR166_SM_LatencyDominatedDowngradeRegistry.report.json"]),
        "liquidity_dominated_count": len(records["PR166_SM_LiquidityDominatedDowngradeRegistry.report.json"]),
        "adverse_selection_dominated_count": len(records["PR166_SM_AdverseSelectionDowngradeRegistry.report.json"]),
        "settlement_sensitive_count": len(records["PR166_SM_SettlementSensitivityRegistry.report.json"]),
        "repair_priority_count": len(records["PR166_SM_RepairPriorityRegistry.report.json"]),
        "external_candidate_value_count": len(records["PR166_SM_ExternalCandidateValueIntakeRegistry.report.json"]),
        "qku_computability_rows": len(records["PR166_SM_QKUComputabilityClosureAudit.report.json"]),
        "field_materialization_action_count": len(records["PR166_SM_FieldMaterializationCandidateRegistry.report.json"]),
        "agent_task_queue_rows": len(records["PR166_SM_AgentTaskQueue.report.json"]),
    }
    for field, expected in equality.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} mismatch")
    for field in (
        "metadata_only_rows",
        "placeholder_rows",
        "unknown_status_rows",
        "generic_blocker_rows",
        "orphan_rows",
        "authority_violation_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
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
    _expect(summary.get("score_refresh_row_count") == 3985, failures, "score row count must reconcile to PR166-S executed candidates")
    _expect(summary.get("memory_refresh_row_count") == 3985, failures, "memory row count must reconcile to PR166-S executed candidates")


def _validate_economic_scores(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    score_rows = records["PR166_SM_RefreshedScoreRegistry.report.json"]
    for row in score_rows:
        expected_net = round6(numeric(row, "gross_edge") - sum(numeric(row, field) for field in COST_FIELDS))
        _expect(abs(expected_net - numeric(row, "net_edge_after_costs")) <= 0.00001, failures, f"net edge formula mismatch {row['candidate_packet_id']}")
        components = row.get("score_formula_component_values")
        _expect(isinstance(components, dict), failures, f"score formula components missing {row['candidate_packet_id']}")
        if not isinstance(components, dict):
            continue
        expected_score = refreshed_net_edge_score(components)
        _expect(abs(expected_score - numeric(row, "refreshed_net_edge_score")) <= 0.00001, failures, f"score formula mismatch {row['candidate_packet_id']}")
        _expect(row.get("gross_edge_only_score_flag") is False, failures, f"gross-only score flag invalid {row['candidate_packet_id']}")
        for penalty in ("cost_drag_ratio", "latency_drag_ratio", "liquidity_drag_ratio", "adverse_selection_ratio", "crowding_penalty", "correlation_cluster_penalty", "false_discovery_risk_adjustment", "overfit_risk_adjustment"):
            _expect(numeric(row, penalty) >= 0, failures, f"negative penalty {penalty} {row['candidate_packet_id']}")


def _validate_rank_and_memory(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    score_rows = records["PR166_SM_RefreshedScoreRegistry.report.json"]
    ranks = sorted(int(row["refreshed_rank"]) for row in score_rows)
    _expect(ranks == list(range(1, len(score_rows) + 1)), failures, "refreshed ranks are not contiguous")
    memory_rows = records["PR166_SM_RefreshedMemoryLedger.report.json"]
    _expect({row["candidate_packet_id"] for row in memory_rows} == {row["candidate_packet_id"] for row in score_rows}, failures, "memory rows do not cover score rows")
    _expect(all(row.get("condition_scoped_memory_only") is True for row in memory_rows), failures, "memory row escaped condition scope")
    _expect(all(row.get("global_permanent_ban_created") is False for row in memory_rows), failures, "memory row created global permanent ban")


def _validate_quantum_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    quantum_rows = records["PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json"]
    _expect(len(quantum_rows) == 6502, failures, "quantum priority rows must cover PR166-S quantum passthrough universe")
    for row in quantum_rows:
        _expect(row.get("backend_quantum_execution_created") is False, failures, f"quantum backend execution flag invalid {row['candidate_packet_id']}")
        _expect(row.get("quantum_advantage_claim_created") is False, failures, f"quantum advantage flag invalid {row['candidate_packet_id']}")
        _expect(row.get("classical_comparator"), failures, f"quantum row missing classical comparator {row['candidate_packet_id']}")
        _expect(row.get("objective_terms"), failures, f"quantum row missing objective terms {row['candidate_packet_id']}")


def _validate_input_consumption(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    input_rows = records["PR166_SM_InputConsumptionAudit.report.json"]
    by_report = {row["expected_input_report"]: row for row in input_rows}
    for report, expected in c.EXPECTED_ROW_COUNTS.items():
        row = by_report.get(report)
        _expect(row is not None, failures, f"input consumption missing {report}")
        if row:
            _expect(row["expected_row_count"] == expected, failures, f"input expected count mismatch {report}")
            _expect(row["observed_row_count"] == expected, failures, f"input observed count mismatch {report}")
            _expect(row["missing_row_count"] == 0, failures, f"input missing rows {report}")
    _expect(all(row["fail_if_required_missing"] is True for row in input_rows if row["expected_input_report"] in c.REQUIRED_INPUT_REPORTS), failures, "required input missing flag invalid")


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
