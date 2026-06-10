"""Fail-closed validator for PR165-C generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    FORBIDDEN_ACTION_LITERALS,
    FORBIDDEN_COMPUTABILITY_LITERALS,
    SCATTERED_LITERAL_EXCLUDED_FILES,
    authority_zero_counts,
    validate_record_authority,
)
from .central_vocab import AGENT_IDS, AUTHORITY_CLASS, NO_ORPHAN_STATUS
from .computability_action_vocab import COMPUTABILITY_ACTIONS
from .json_io import read_json, records_from_payload
from .memory_consumer_action_vocab import MEMORY_CONSUMER_ACTIONS
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
    _validate_no_scattered_literals(repo_root, failures)
    _validate_serialized_repo_refs(reports, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    _validate_manifest(reports, records, failures)
    _validate_counts(records, failures)
    _validate_memory_rows(records, failures)
    _validate_agent_rows(records, failures)
    _validate_retest_and_repair(records, failures)
    _validate_pr_file_connectivity(records, failures)
    _validate_authority(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR165-C report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR165-C report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR165-C schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for rel_path in p.REQUIRED_INPUTS:
        normalized = p.normalize_repo_ref(rel_path)
        if not p.resolve_repo_relative(repo_root, normalized).exists():
            failures.append(f"missing required PR165-C upstream artifact: {normalized}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR165-C", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(payload.get("vocab_refs"), failures, f"{filename} missing central vocab refs")
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
            failures.extend(validate_record_authority(record).failures)


def _validate_manifest(reports: dict[str, dict[str, Any]], records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    manifest = records["PR165_C_ReportManifest.report.json"]
    listed = {row.get("report_filename") for row in manifest}
    _expect(listed == set(p.REPORT_FILENAMES), failures, "manifest does not list exactly the PR165-C reports")
    for row in manifest:
        filename = row["report_filename"]
        _expect(row.get("row_count") == reports[filename].get("record_count"), failures, f"manifest row count mismatch: {filename}")
        for field in ("upstream_source_pr_refs", "downstream_consumer_pr_refs", "owning_agent", "validator", "manifest_entry_ref", "no_orphan_status"):
            _expect(row.get(field) not in (None, "", []), failures, f"manifest row missing {field}: {filename}")
        for shard_path in row.get("shard_paths") or []:
            _expect(shard_path in reports[filename].get("shard_files", []), failures, f"manifest shard mismatch: {shard_path}")


def _validate_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR165_C_FinalSummary.report.json"][0]
    memory_rows = records["PR165_C_MemoryConsumerRouter.report.json"]
    memory_count = len(memory_rows)
    _expect(memory_count == 6502, failures, f"memory consumer row count mismatch: {memory_count}")
    equality_expectations = {
        "computable_artifact_payload_rows": "PR165_C_ComputableArtifactPayloadRegistry.report.json",
        "computable_qku_action_rows": "PR165_C_ComputableQKUFormulaActionRegistry.report.json",
        "formula_test_vector_rows": "PR165_C_FormulaTestVectorRegistry.report.json",
        "replay_paper_consumer_action_rows": "PR165_C_ReplayPaperConsumerActionRegistry.report.json",
        "scenario_memory_route_rows": "PR165_C_ScenarioMemoryRouter.report.json",
        "condition_regime_feature_rows": "PR165_C_ConditionRegimeFeatureMatrix.report.json",
        "dashboard_handoff_rows": "PR165_C_DashboardConsumerHandoff.report.json",
        "governance_handoff_rows": "PR165_C_GovernanceConsumerHandoff.report.json",
        "lineage_graph_rows": "PR165_C_LineageGraph.report.json",
        "quantum_consumer_route_rows": "PR165_C_QuantumConsumerRouter.report.json",
    }
    for field, filename in equality_expectations.items():
        actual = len(records[filename])
        _expect(actual == memory_count, failures, f"{filename} must match memory rows")
        _expect(summary.get(field) == actual, failures, f"summary {field} mismatch")
    pending = len(records["PR165_C_PendingRetestQueue.report.json"])
    _expect(pending == 6497, failures, f"pending retest row count mismatch: {pending}")
    _expect(len(records["PR165_C_RetestPriorityRanking.report.json"]) == pending, failures, "retest priority rows must match pending rows")
    _expect(len(records["PR165_C_ScoreMemoryRefreshTriggerRegistry.report.json"]) >= pending, failures, "refresh trigger rows must cover pending rows")
    _expect(len(records["PR165_C_RepairToRetestHandoff.report.json"]) == 2512, failures, "repair handoff row count mismatch")
    _expect(summary.get("metadata_only_rows") == 0, failures, "metadata-only rows must be zero")
    _expect(summary.get("placeholder_only_rows") == 0, failures, "placeholder-only rows must be zero")
    _expect(summary.get("unknown_status_rows") == 0, failures, "unresolved status rows must be zero")
    _expect(summary.get("generic_blocked_rows") == 0, failures, "generic blocked rows must be zero")
    _expect(summary.get("orphan_counts_all_0") is True, failures, "orphan counts not all zero")
    _expect(summary.get("authority_boundary_violation_counts_all_0") is True, failures, "authority boundary violations not all zero")


def _validate_memory_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    payload_ids = {row["computable_artifact_payload_id"] for row in records["PR165_C_ComputableArtifactPayloadRegistry.report.json"]}
    route_ids = {row["scenario_memory_route_id"] for row in records["PR165_C_ScenarioMemoryRouter.report.json"]}
    task_ids = {row["task_id"] for row in records["PR165_C_AgentTaskQueue.report.json"]}
    lineage_ids = {row["lineage_graph_id"] for row in records["PR165_C_LineageGraph.report.json"]}
    for row in records["PR165_C_MemoryConsumerRouter.report.json"]:
        for field in (
            "candidate_packet_id",
            "qku_id",
            "primary_agent_owner",
            "computability_action_status",
            "computable_artifact_payload_ref",
            "scenario_memory_route_ref",
            "agent_task_queue_ref",
            "lineage_graph_ref",
            "authority_boundary_ref",
            "no_orphan_status",
        ):
            _expect(row.get(field) not in (None, "", []), failures, f"memory row missing {field}")
        _expect(row["computability_action_status"] in COMPUTABILITY_ACTIONS, failures, "invalid computability action")
        _expect(row["computable_artifact_payload_ref"] in payload_ids, failures, "memory row payload ref missing")
        _expect(row["scenario_memory_route_ref"] in route_ids, failures, "memory row route ref missing")
        _expect(row["agent_task_queue_ref"] in task_ids, failures, "memory row task ref missing")
        _expect(row["lineage_graph_ref"] in lineage_ids, failures, "memory row lineage ref missing")
        _expect(row["primary_agent_owner"] in AGENT_IDS, failures, "memory row invalid primary agent")
        _expect(row["no_orphan_status"] == NO_ORPHAN_STATUS, failures, "memory row orphan status drift")
        _expect(row["replay_consumer_action"] in MEMORY_CONSUMER_ACTIONS, failures, "invalid replay action")
        _expect(row["paper_consumer_action"] in MEMORY_CONSUMER_ACTIONS, failures, "invalid paper action")


def _validate_agent_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    duties = records["PR165_C_AgentDutyDistinctnessMatrix.report.json"]
    ownership = records["PR165_C_AgentFieldOwnershipMatrix.report.json"]
    overlaps = records["PR165_C_AgentOverlapConflictAudit.report.json"]
    _expect(len(duties) >= 13, failures, "agent duty rows missing")
    _expect(len(ownership) >= 13, failures, "agent field ownership rows missing")
    _expect(len(overlaps) >= 13, failures, "agent overlap rows missing")
    for row in duties:
        _expect(row.get("agent_id") in AGENT_IDS, failures, "invalid agent duty id")
        _expect(row.get("forbidden_duties"), failures, "agent contract lacks forbidden duties")
        _expect(row.get("upstream_agent_pr_refs"), failures, "agent duty lacks upstream PR refs")
        _expect(row.get("downstream_consumer_pr_refs"), failures, "agent duty lacks downstream PR refs")
        _expect(row.get("no_orphan_agent_duty_status") == NO_ORPHAN_STATUS, failures, "agent duty orphan status drift")
    for row in overlaps:
        _expect(row.get("overlap_status") == "TYPED_USEFUL_OVERLAP", failures, "agent has untyped overlap")
        _expect(row.get("same_write_duty") is False, failures, "same write duty overlap present")


def _validate_retest_and_repair(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    pending_ids = {row["candidate_packet_id"] for row in records["PR165_C_PendingRetestQueue.report.json"]}
    repair_ids = {row["candidate_packet_id"] for row in records["PR165_C_RepairToRetestHandoff.report.json"]}
    for row in records["PR165_C_MemoryConsumerRouter.report.json"]:
        if row.get("retest_required"):
            _expect(row["candidate_packet_id"] in pending_ids, failures, "retest-required row lacks pending retest")
        if row.get("repair_consumer_action") != "NO_ACTION_WITH_REASON":
            _expect(row["candidate_packet_id"] in repair_ids, failures, "repair-required row lacks repair handoff")
    ranks = [row["retest_priority_rank"] for row in records["PR165_C_RetestPriorityRanking.report.json"]]
    _expect(ranks == list(range(1, len(ranks) + 1)), failures, "retest priority ranks are not contiguous")


def _validate_pr_file_connectivity(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR165_C_PRFileConnectivityAudit.report.json"]
    _expect(rows, failures, "PR file connectivity rows missing")
    for row in rows:
        for field in (
            "upstream_source_pr_refs",
            "downstream_consumer_pr_refs",
            "owning_agent",
            "owning_builder_or_tool",
            "validator",
            "tests_covering_file",
            "manifest_entry_ref",
            "no_orphan_status",
            "authority_boundary_ref",
        ):
            _expect(row.get(field) not in (None, "", []), failures, f"PR file connectivity missing {field}")


def _validate_serialized_repo_refs(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        for value in _flatten_values(payload):
            if "\\" in value:
                failures.append(f"{filename} serialized repo ref contains backslash: {value}")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key in authority_zero_counts():
                if int(row.get(key, 0) or 0) != 0:
                    failures.append(f"{filename} row has nonzero authority count {key}")
            text_values = _flatten_values(row)
            for literal in FORBIDDEN_ACTION_LITERALS:
                _expect(literal not in text_values, failures, f"forbidden action literal emitted: {literal}")
            for literal in FORBIDDEN_COMPUTABILITY_LITERALS:
                _expect(literal not in text_values, failures, f"forbidden computability literal emitted: {literal}")


def _validate_no_scattered_literals(repo_root: Path, failures: list[str]) -> None:
    scan_paths = [
        *sorted((repo_root / p.PACKAGE_DIR).glob("*.py")),
        repo_root / "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
        repo_root / "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
        *sorted((repo_root / p.TEST_DIR).glob("*.py")),
    ]
    for path in scan_paths:
        if not path.exists() or path.name in SCATTERED_LITERAL_EXCLUDED_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        for literal in (*FORBIDDEN_ACTION_LITERALS, *FORBIDDEN_COMPUTABILITY_LITERALS):
            if literal in text:
                failures.append(f"scattered PR165-C literal outside central vocabulary: {p.to_repo_posix(path, repo_root)}::{literal}")


def _flatten_values(value: Any) -> set[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for nested in value.values():
            values.update(_flatten_values(nested))
    elif isinstance(value, list):
        for nested in value:
            values.update(_flatten_values(nested))
    else:
        values.add(str(value))
    return values


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
