"""Fail-closed validator for PR165-D generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import authority_zero_counts, validate_record_authority
from .central_vocab import AUTHORITY_CLASS, NO_ORPHAN_STATUS
from .input_consumption import load_report_records as load_input_report_records
from .json_io import read_json, records_from_payload
from .report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, load_report_records


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    _validate_serialized_repo_refs(reports, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    _validate_manifest(reports, records, failures)
    _validate_counts(repo_root, records, failures)
    _validate_candidate_rows(records, failures)
    _validate_retest_repair_separation(records, failures)
    _validate_quantum_routes(records, failures)
    _validate_authority(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR165-D report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR165-D report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR165-D schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for rel_path in p.REQUIRED_INPUTS:
        normalized = p.normalize_repo_ref(rel_path)
        if not p.resolve_repo_relative(repo_root, normalized).exists():
            failures.append(f"missing required PR165-D upstream artifact: {normalized}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR165-D", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(payload.get("vocab_refs"), failures, f"{filename} missing vocab refs")
        if filename in p.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root must not duplicate row records")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} sharded row count mismatch")
        else:
            _expect(payload.get("record_count") == len(records_from_payload(payload)), failures, f"{filename} record_count mismatch")
        path = repo_root / p.GENERATED_DIR / filename
        _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds root report limit")
        for shard_path in payload.get("shard_files") or []:
            resolved = p.resolve_repo_relative(repo_root, shard_path)
            _expect(resolved.exists(), failures, f"{filename} missing shard: {shard_path}")
            if resolved.exists():
                _expect(resolved.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_path} exceeds shard limit")
        for record in records[filename]:
            for field in ("upstream_source_pr_refs", "downstream_consumer_pr_refs", "owning_agent", "validator", "manifest_entry_ref", "no_orphan_status", "authority_boundary_ref"):
                _expect(record.get(field) not in (None, "", []), failures, f"{filename} row missing {field}")
            _expect(record.get("no_orphan_status") == NO_ORPHAN_STATUS, failures, f"{filename} orphan status drift")
            failures.extend(validate_record_authority(record).failures)


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR165_D_ReportManifest.report.json"]
    listed = {row.get("report_filename") for row in manifest}
    _expect(listed == set(p.REPORT_FILENAMES), failures, "manifest does not list exactly the PR165-D reports")
    for row in manifest:
        filename = row["report_filename"]
        _expect(row.get("row_count") == reports[filename].get("record_count"), failures, f"manifest row count mismatch: {filename}")
        for shard_path in row.get("shard_paths") or []:
            _expect(shard_path in reports[filename].get("shard_files", []), failures, f"manifest shard mismatch: {shard_path}")


def _validate_counts(repo_root: Path, records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR165_D_FinalSummary.report.json"][0]
    memory_count = _root_count(repo_root, "PR165_C_MemoryConsumerRouter.report.json")
    pending_count = _root_count(repo_root, "PR165_C_PendingRetestQueue.report.json")
    repair_count = _root_count(repo_root, "PR165_C_RepairToRetestHandoff.report.json")
    coverage = len(records["PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"])
    equality = {
        "selection_coverage_rows": coverage,
        "candidate_feature_vector_rows": len(records["PR165_D_CandidateFeatureVectorRegistry.report.json"]),
        "selected_excluded_reason_rows": len(records["PR165_D_SelectedExcludedReasonLedger.report.json"]),
        "false_discovery_control_rows": len(records["PR165_D_SelectionFalseDiscoveryControl.report.json"]),
        "point_in_time_selection_audit_rows": len(records["PR165_D_PointInTimeSelectionAudit.report.json"]),
        "quantum_selection_route_rows": len(records["PR165_D_QuantumSelectionRouter.report.json"]),
        "agent_selection_contract_rows": len(records["PR165_D_AgentSelectionContract.report.json"]),
        "agent_selection_handoff_rows": len(records["PR165_D_AgentSelectionHandoff.report.json"]),
        "dashboard_selection_handoff_rows": len(records["PR165_D_DashboardSelectionHandoff.report.json"]),
        "governance_selection_handoff_rows": len(records["PR165_D_GovernanceSelectionHandoff.report.json"]),
        "lineage_graph_rows": len(records["PR165_D_LineageGraph.report.json"]),
    }
    _expect(coverage == memory_count, failures, f"selection coverage does not conserve PR165-C memory rows: {coverage} != {memory_count}")
    _expect(len(records["PR165_D_RetestBatchSelectionQueue.report.json"]) >= pending_count, failures, "retest batch rows do not cover pending retests")
    _expect(len(records["PR165_D_RepairBeforeRetestSelectionQueue.report.json"]) == repair_count, failures, "repair selection rows do not match PR165-C repair handoff")
    _expect(len(records["PR165_D_CommanderSelectionHandoff.report.json"]) >= pending_count + repair_count, failures, "commander rows do not cover retest plus repair routes")
    for field, actual in equality.items():
        _expect(summary.get(field) == actual, failures, f"summary {field} mismatch")
        _expect(actual == memory_count, failures, f"{field} must match memory coverage")
    summary_checks = {
        "metadata_only_rows": 0,
        "placeholder_rows": 0,
        "unknown_status_rows": 0,
        "generic_blocked_rows": 0,
        "fake_retest_result_rows": 0,
        "live_authority_rows": 0,
        "profit_evidence_rows": 0,
        "quantum_backend_execution_rows": 0,
        "quantum_advantage_claim_rows": 0,
    }
    for field, expected in summary_checks.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} must be {expected}")
    _expect(summary.get("orphan_counts_all_zero") is True, failures, "orphan counts not all zero")
    _expect(summary.get("authority_counts_all_zero") is True, failures, "authority counts not all zero")


def _validate_candidate_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    score_ids = {row["candidate_packet_id"] for row in records["PR165_D_SelectionScoreRegistry.report.json"]}
    reason_ids = {row["candidate_packet_id"] for row in records["PR165_D_SelectedExcludedReasonLedger.report.json"]}
    for row in records["PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json"]:
        for field in (
            "candidate_packet_id",
            "qku_id",
            "condition_fingerprint_id",
            "combination_fingerprint_id",
            "computability_action_status",
            "scenario_selection_bucket",
            "target_future_pr",
            "primary_agent_owner",
            "downstream_agent_consumer",
            "lineage_graph_ref",
            "authority_boundary_ref",
            "no_orphan_status",
        ):
            _expect(row.get(field) not in (None, "", []), failures, f"candidate row missing {field}")
        _expect(row["candidate_packet_id"] in score_ids, failures, "candidate lacks selection score")
        _expect(row["candidate_packet_id"] in reason_ids, failures, "candidate lacks selected/excluded reason")


def _validate_retest_repair_separation(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    repair_ids = {row["candidate_packet_id"] for row in records["PR165_D_RepairBeforeRetestSelectionQueue.report.json"]}
    for row in records["PR165_D_RetestBatchSelectionQueue.report.json"]:
        if row["candidate_packet_id"] in repair_ids:
            _expect(row.get("ready_execution_batch_flag") is False, failures, "repair candidate appears in ready execution batch")
            _expect(row.get("batch_stream") == "REPAIR_BEFORE_RETEST", failures, "repair candidate not in repair stream")
        if row.get("batch_stream") == "QUANTUM_FORMULATION_REPAIR":
            _expect(row.get("ready_execution_batch_flag") is False, failures, "quantum repair row appears in ready execution batch")
        _expect(row.get("no_replay_execution_in_pr165_d") is True, failures, "retest row claims replay execution")
        _expect(row.get("no_paper_execution_in_pr165_d") is True, failures, "retest row claims paper execution")


def _validate_quantum_routes(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR165_D_QuantumSelectionRouter.report.json"]:
        _expect(row.get("no_backend_execution") is True, failures, "quantum route allows backend execution")
        _expect(row.get("no_quantum_advantage_claim") is True, failures, "quantum route claims advantage")
        _expect(row.get("quantum_backend_execution_count", 0) == 0, failures, "quantum backend execution count nonzero")
        _expect(row.get("quantum_advantage_claim_count", 0) == 0, failures, "quantum advantage count nonzero")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key in authority_zero_counts():
                if int(row.get(key, 0) or 0) != 0:
                    failures.append(f"{filename} row has nonzero authority count {key}")


def _validate_serialized_repo_refs(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        for value in _flatten_values(payload):
            if "\\" in value:
                failures.append(f"{filename} serialized repo ref contains backslash: {value}")


def _flatten_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return []


def _root_count(repo_root: Path, filename: str) -> int:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    return int(payload.get("record_count", 0) or 0)


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
