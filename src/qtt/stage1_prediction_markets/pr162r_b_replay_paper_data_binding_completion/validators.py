"""Fail-closed validator for PR162R-B generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    PAIRED_BINDING_STATUSES,
    validate_dedup_group_label,
    validate_record_authority,
)
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_fixtures(repo_root, failures)
    _validate_required_upstream_inputs(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_common_contracts(reports, failures)
    summary = reports["PR162R_B_FinalSummary.report.json"]
    _validate_summary(summary, failures)
    _validate_missing_action_collapse(reports, failures)
    _validate_tasks(reports, summary, failures)
    _validate_bindings(reports, failures)
    _validate_row_resolution(reports, summary, failures)
    _validate_readiness(reports, summary, failures)
    _validate_orchestration(reports, summary, failures)
    _validate_authority_reports(summary, reports, failures)
    _validate_manifest(reports, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162R-B report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162R-B report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR162R-B schema: {filename}")


def _validate_fixtures(repo_root: Path, failures: list[str]) -> None:
    for filename in p.FIXTURE_FILENAMES:
        path = p.fixture_path(repo_root, filename)
        if not path.exists():
            failures.append(f"missing PR162R-B fixture: {filename}")
            continue
        if filename.endswith(".jsonl"):
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not rows:
                failures.append(f"fixture has no rows: {filename}")
            for row in rows:
                _expect(row.get("fixture_truth_status") == "SYNTHETIC_TEST_FIXTURE", failures, f"fixture truth missing: {filename}")
                _expect(row.get("live_authority") is False, failures, f"fixture live authority drift: {filename}")
                _expect(row.get("profit_evidence") is False, failures, f"fixture profit drift: {filename}")
        else:
            payload = read_json(path)
            _expect(payload.get("fixture_truth_status") == "SYNTHETIC_TEST_FIXTURE", failures, f"fixture truth missing: {filename}")
            _expect(payload.get("live_authority") is False, failures, f"fixture live authority drift: {filename}")
            _expect(payload.get("profit_evidence") is False, failures, f"fixture profit drift: {filename}")


def _validate_required_upstream_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in (
        "PR162R_MissingDataBindingActionQueue.report.json",
        "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
        "PR162R_ReplayAdapterInputPacketRegistry.report.json",
        "PR162R_PaperAdapterInputPacketRegistry.report.json",
        "PR162R_QKUComputabilityClassificationMatrix.report.json",
        "PR162D_R2A_CandidatePacketV1Registry.report.json",
    ):
        if not (repo_root / p.GENERATED_DIR / filename).exists():
            failures.append(f"missing required upstream input: {filename}")


def _validate_common_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR162R-B", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(isinstance(payload.get("records"), list), failures, f"{filename} missing records")
        _expect(payload.get("record_count") == len(payload.get("records", [])), failures, f"{filename} record_count mismatch")
        for flag, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} authority flag drift: {flag}")
        for row in records_from_payload(payload):
            failures.extend(validate_record_authority(row).failures)


def _validate_summary(summary: dict[str, Any], failures: list[str]) -> None:
    minimums = {
        "raw_missing_actions_consumed": 1,
        "candidate_packet_universe_count": 1,
        "unique_binding_tasks_count": 1,
        "dataset_binding_packets_created": 1,
        "replay_dataset_binding_packets_created": 1,
        "paper_dataset_binding_packets_created": 1,
        "fixture_datasets_created": 10,
        "source_candidate_to_binding_rows": 1,
        "normalization_receipt_rows": 1,
        "row_binding_resolution_matrix_rows": 1,
        "rows_with_any_binding_improvement": 1,
        "missing_action_reduction_count": 1,
        "paper_binding_fixture_rows": 1,
        "classical_comparator_input_binding_count": 1,
    }
    for field, minimum in minimums.items():
        _expect(summary.get(field, 0) >= minimum, failures, f"{field} below minimum {minimum}: {summary.get(field)}")
    _expect(summary.get("raw_missing_actions_consumed") == 19506, failures, "raw missing action count drift")
    _expect(summary.get("candidate_packet_universe_count") == 6502, failures, "candidate universe count drift")
    _expect(summary.get("row_binding_resolution_matrix_rows") == summary.get("candidate_packet_universe_count"), failures, "row matrix must cover candidate universe")
    _expect(summary.get("rows_with_any_binding_improvement", 0) >= 3000, failures, "material readiness improvement below 3000 rows")
    _expect(summary.get("paper_binding_fixture_rows") == summary.get("candidate_packet_universe_count"), failures, "paper fixture fanout must cover universe")
    _expect(summary.get("collapsed_binding_family_count", 0) >= 12, failures, "canonical binding family coverage below 12")
    _expect(summary.get("unique_binding_tasks_count", 0) < summary.get("raw_missing_actions_consumed", 0), failures, "dedup did not reduce task count")
    _expect(summary.get("deduplication_ratio", 0) >= 10, failures, "deduplication ratio below 10")
    _expect(summary.get("average_rows_resolved_per_binding_packet", 0) >= 10, failures, "average rows per binding packet below 10")
    for field in (
        "unresolved_raw_row_level_missing_actions_after_collapse",
        "rows_remaining_fill_required",
        "orphan_binding_packet_count",
        "orphan_qku_row_count",
        "orphan_generated_report_count",
        "orphan_fixture_count",
        "orphan_source_candidate_count",
        "orphan_normalization_receipt_count",
    ):
        _expect(summary.get(field) == 0, failures, f"{field} must be zero")
    for field, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}={summary.get(field)}")


def _validate_missing_action_collapse(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    ingestion = records_from_payload(reports["PR162R_B_PR162RMissingActionIngestionLedger.report.json"])
    collapse = records_from_payload(reports["PR162R_B_BindingActionFamilyCollapse.report.json"])
    _expect(len(ingestion) == 19506, failures, "missing action ingestion count mismatch")
    _expect(len(collapse) == len(ingestion), failures, "collapse row count mismatch")
    for row in collapse:
        _expect(row.get("binding_family"), failures, "collapse row lacks binding family")
        _expect(row.get("binding_task_ref"), failures, "collapse row lacks BindingTaskV1 ref")
        _expect(row.get("raw_missing_action_uncollapsed_flag") is False, failures, "raw action left uncollapsed")


def _validate_tasks(reports: dict[str, dict[str, Any]], summary: dict[str, Any], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR162R_B_BindingTaskDeduplicationAudit.report.json"])
    tasks = [row for row in rows if row.get("binding_task_id")]
    _expect(len(tasks) == summary.get("unique_binding_tasks_count"), failures, "unique task summary mismatch")
    for task in tasks:
        _expect(task.get("impacted_missing_action_refs"), failures, "BindingTaskV1 has zero impacted actions")
        _expect(task.get("impacted_candidate_packet_ids"), failures, "BindingTaskV1 has zero impacted candidates")
        _expect(task.get("downstream_refs"), failures, "BindingTaskV1 has no downstream route")
        _expect(task.get("materialized_binding_refs"), failures, "BindingTaskV1 lacks materialized binding refs")
        failures.extend(validate_dedup_group_label(str(task.get("dedup_group_label"))).failures)


def _validate_bindings(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    dataset = records_from_payload(reports["PR162R_B_ReplayPaperDatasetBindingRegistry.report.json"])
    _expect(dataset, failures, "dataset binding packets created count = 0")
    for binding in dataset:
        for field in ("binding_id", "binding_task_id", "binding_family", "binding_status", "data_quality_tier", "unit_map", "timestamp_policy", "normalization_policy"):
            _expect(binding.get(field), failures, f"binding lacks {field}")
        _expect(binding.get("live_allowed") is False, failures, "binding live_allowed true")
        _expect(binding.get("consumer_qku_ids"), failures, "binding lacks consumer QKU")
        _expect(binding.get("consumer_candidate_packet_ids"), failures, "binding lacks consumer CandidatePacketV1 rows")
        _expect(binding.get("normalization_receipt_refs"), failures, "binding lacks normalization receipts")
        _expect(binding.get("source_candidate_refs"), failures, "binding lacks source candidate refs")
    required_reports = (
        "PR162R_B_ReplayHistoricalPriceSeriesBindingRegistry.report.json",
        "PR162R_B_ReplayOrderbookSnapshotBindingRegistry.report.json",
        "PR162R_B_ReplayTradePrintBindingRegistry.report.json",
        "PR162R_B_ReplayEventStateTimelineBindingRegistry.report.json",
        "PR162R_B_ReplaySettlementOutcomeBindingRegistry.report.json",
        "PR162R_B_PaperMarketStateBindingRegistry.report.json",
        "PR162R_B_PaperSyntheticFillModelRegistry.report.json",
        "PR162R_B_PaperPortfolioStateFixtureRegistry.report.json",
        "PR162R_B_QuantumObjectiveInputBindingRegistry.report.json",
        "PR162R_B_QuantumConstraintInputBindingRegistry.report.json",
        "PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json",
        "PR162R_B_ClassicalComparatorInputBindingRegistry.report.json",
        "PR162R_B_FeeSlippageLatencyBindingRegistry.report.json",
    )
    for filename in required_reports:
        _expect(records_from_payload(reports[filename]), failures, f"{filename} has no binding packets")


def _validate_row_resolution(reports: dict[str, dict[str, Any]], summary: dict[str, Any], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR162R_B_RowBindingResolutionMatrix.report.json"])
    _expect(len(rows) == summary.get("candidate_packet_universe_count"), failures, "row binding matrix count mismatch")
    for row in rows:
        _expect(row.get("missing_action_refs_consumed"), failures, "row consumed no missing actions")
        _expect(row.get("binding_task_refs"), failures, "row lacks binding tasks")
        _expect(row.get("replay_binding_refs"), failures, "replay-bound row lacks replay refs")
        _expect(row.get("paper_binding_refs"), failures, "paper-bound row lacks paper refs")
        _expect(row.get("classical_comparator_binding_refs"), failures, "row lacks classical comparator refs")
        _expect(row.get("paired_binding_status") in PAIRED_BINDING_STATUSES, failures, "invalid paired binding status")
        _expect(row.get("no_replay_result_packet") is True, failures, "row created replay result")
        _expect(row.get("no_paper_result_packet") is True, failures, "row created paper result")
        _expect(row.get("no_profit_evidence") is True, failures, "row created profit evidence")
        _expect(row.get("no_live_order_authority") is True, failures, "row created live authority")
    quantum_rows = [row for row in rows if row.get("quantum_binding_refs")]
    _expect(len(quantum_rows) >= 500, failures, "quantum binding improvement rows below target")


def _validate_readiness(reports: dict[str, dict[str, Any]], summary: dict[str, Any], failures: list[str]) -> None:
    readiness = records_from_payload(reports["PR162R_B_ReadinessDeltaVsPR162R.report.json"])
    reduction = records_from_payload(reports["PR162R_B_MissingActionReductionAudit.report.json"])
    _expect(readiness, failures, "readiness delta missing")
    _expect(reduction, failures, "missing action reduction audit missing")
    row = readiness[0]
    _expect(row.get("rows_with_any_binding_improvement") == summary.get("rows_with_any_binding_improvement"), failures, "readiness rows mismatch")
    _expect(row.get("missing_action_reduction_count") == summary.get("missing_action_reduction_count"), failures, "reduction mismatch")
    _expect(row.get("rows_remaining_fill_required") == 0, failures, "fill required rows remain")


def _validate_orchestration(reports: dict[str, dict[str, Any]], summary: dict[str, Any], failures: list[str]) -> None:
    for filename, summary_field in (
        ("PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json", "qku_formula_algorithm_agent_routing_rows"),
        ("PR162R_B_PR163PaperAdapterHandoffUpdate.report.json", "pr163_handoff_update_rows"),
        ("PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json", "pr164_handoff_update_rows"),
        ("PR162R_B_PR165ScoringRankingHandoffUpdate.report.json", "pr165_handoff_update_rows"),
        ("PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json", "pr162e_compatibility_update_rows"),
    ):
        rows = records_from_payload(reports[filename])
        _expect(len(rows) == summary.get(summary_field), failures, f"{filename} summary count mismatch")
        _expect(len(rows) == summary.get("candidate_packet_universe_count"), failures, f"{filename} does not cover universe")
    for row in records_from_payload(reports["PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json"]):
        _expect(row.get("upstream_refs"), failures, "routing row lacks upstream")
        _expect(row.get("downstream_refs"), failures, "routing row lacks downstream")
        _expect(row.get("orphan_flag") is False, failures, "routing orphan flag true")


def _validate_authority_reports(summary: dict[str, Any], reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for field, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"summary authority count drift {field}")
    for filename in (
        "PR162R_B_NoReplayPaperResultPacketAudit.report.json",
        "PR162R_B_NoLiveOrderProfitAuthorityAudit.report.json",
        "PR162R_B_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
        "PR162R_B_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR162R_B_NoQTTChecksumFreezeAuthorityAudit.report.json",
    ):
        row = records_from_payload(reports[filename])[0]
        for field, expected in BOUNDARY_COUNT_FIELDS.items():
            _expect(row.get(field) == expected, failures, f"{filename} authority count drift {field}")


def _validate_manifest(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    manifest = records_from_payload(reports["PR162R_B_ReportManifest.report.json"])
    filenames = {row.get("report_filename") for row in manifest}
    _expect(filenames == set(p.REPORT_FILENAMES), failures, "manifest does not list every report")
    for row in manifest:
        filename = row["report_filename"]
        _expect(row.get("row_count") == reports[filename].get("record_count"), failures, f"manifest row_count mismatch for {filename}")


def _expect(condition: Any, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
