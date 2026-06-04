"""Fail-closed PR162R-A artifact validator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_common_contracts(reports, failures)
    summary = reports["PR162R_A_FinalSummary.report.json"]
    classifications = records_from_payload(reports["PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json"])
    computability = records_from_payload(reports["PR162R_A_ComputabilityClassMatrix.report.json"])
    _validate_summary(summary, failures)
    _validate_classifications(summary, classifications, failures)
    _validate_computability(summary, computability, failures)
    _validate_ready_contracts(reports, failures)
    _validate_micro_materialization(records_from_payload(reports["PR162R_A_TargetedMicroMaterializationLedger.report.json"]), failures)
    _validate_quantum(reports, failures)
    _validate_no_authority(summary, reports, failures)
    _validate_future_bridges(summary, failures)
    _validate_generated_file_set(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162R-A report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162R-A report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162R-A schema: {filename}")


def _validate_common_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(isinstance(payload.get("records"), list), failures, f"{filename} missing records list")
        _expect(payload.get("record_count") == len(payload.get("records", [])), failures, f"{filename} record_count mismatch")
        _expect(payload.get("source_inputs"), failures, f"{filename} missing source_inputs")
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")


def _validate_summary(summary: dict[str, Any], failures: list[str]) -> None:
    required_zero_fields = (
        "primary_classification_missing_count",
        "duplicate_primary_classification_count",
        "computability_class_missing_count",
        "qku_ref_missing_count",
        "agent_route_missing_count",
        "replay_paper_route_missing_count",
        "source_locator_missing_count",
        "metadata_only_replay_ready_count",
        "orphan_candidate_count",
        "orphan_generated_file_count",
        "replay_execution_count",
        "paper_execution_count",
        "result_packet_created_count",
        "live_order_authority_count",
        "order_ready_count",
        "live_promotion_ready_count",
        "profit_evidence_count",
        "private_state_fetch_count",
        "qtt_sha_freeze_checksum_authority_count",
        "atomicrows_bundle_mutation_count",
        "remote_quantum_hot_path_count",
        "post_launch_formula_plugin_future_bridge_missing_count",
        "post_launch_formula_plugin_requirement_backlog_missing_count",
        "owner_formula_intake_future_bridge_missing_count",
        "agent_formula_scout_future_bridge_missing_count",
        "runtime_formula_allowlist_future_bridge_missing_count",
        "formula_version_rollback_future_bridge_missing_count",
        "hot_path_formula_latency_future_bridge_missing_count",
    )
    for field in required_zero_fields:
        _expect(summary.get(field) == 0, failures, f"{field} must be zero, got {summary.get(field)}")
    _expect(summary.get("pr162d_r1_consumed_not_rebuilt_flag") is True, failures, "PR162D-R1 must be consumed, not rebuilt")
    _expect(summary.get("candidate_source_count") == 548, failures, "candidate_source_count must match PR162D-R1 qku mapped count")
    _expect(summary.get("candidates_classified_count") == summary.get("candidate_source_count"), failures, "classified count mismatch")
    _expect(summary.get("pr162d_6502_candidate_universe_observed_count") == 6502, failures, "PR162D 6502 universe rollup mismatch")
    _expect(summary.get("targeted_micro_materialization_count", 0) > 0, failures, "micro-materialization ledger must not be empty")
    _expect(summary.get("pr162e_pr162f_runtime_allowlist_follow_up_captured_flag") is True, failures, "future bridge capture missing")


def _validate_classifications(summary: dict[str, Any], rows: list[dict[str, Any]], failures: list[str]) -> None:
    ids = [row.get("candidate_id") for row in rows]
    _expect(len(rows) == summary.get("candidate_source_count"), failures, "classification matrix size mismatch")
    _expect(len(ids) == len(set(ids)), failures, "duplicate primary classifications")
    for row in rows:
        state = row.get("primary_executability_state")
        _expect(state in c.PRIMARY_STATES, failures, f"invalid primary state: {state}")
        _expect(row.get("qku_refs"), failures, f"classification missing qku refs: {row.get('candidate_id')}")
        _expect(row.get("agent_refs"), failures, f"classification missing agent refs: {row.get('candidate_id')}")
        _expect(row.get("replay_paper_route_refs"), failures, f"classification missing replay/paper refs: {row.get('candidate_id')}")
        _expect(row.get("source_locator"), failures, f"classification missing source locator: {row.get('candidate_id')}")
        if "NON_OFFICIAL_SOURCE" in row.get("secondary_tags", []):
            _expect(state.startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE")), failures, "non-official source blocked replay/paper eligibility")


def _validate_computability(summary: dict[str, Any], rows: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(len(rows) == summary.get("candidate_source_count"), failures, "computability matrix size mismatch")
    ids = [row.get("candidate_id") for row in rows]
    _expect(len(ids) == len(set(ids)), failures, "duplicate computability classifications")
    for row in rows:
        _expect(row.get("computability_class") in c.COMPUTABILITY_CLASSES, failures, f"invalid computability class: {row.get('computability_class')}")


def _validate_ready_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    input_unit = {
        row["candidate_id"]: row
        for row in records_from_payload(reports["PR162R_A_InputOutputUnitCompatibilityMatrix.report.json"])
    }
    replay_ready = records_from_payload(reports["PR162R_A_ReplayReadyCandidateQueue.report.json"])
    paper_ready = records_from_payload(reports["PR162R_A_PaperReadyCandidateQueue.report.json"])
    for row in [*replay_ready, *paper_ready]:
        details = input_unit.get(row["candidate_id"], {})
        _expect(details.get("input_fields_present_flag"), failures, f"ready candidate missing inputs: {row['candidate_id']}")
        _expect(details.get("output_fields_present_flag"), failures, f"ready candidate missing outputs: {row['candidate_id']}")
        _expect(details.get("units_present_flag"), failures, f"ready candidate missing units: {row['candidate_id']}")


def _validate_micro_materialization(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        _expect(row.get("source_locator"), failures, f"micro materialization missing source locator: {row.get('materialization_id')}")
        _expect(row.get("candidate_or_provisional_flag") is True, failures, "micro materialization must be candidate/provisional")
        _expect(row.get("no_live_order_authority") is True, failures, "micro materialization authority drift")


def _validate_quantum(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    quantum = records_from_payload(reports["PR162R_A_QuantumReplayPaperEligibilityMatrix.report.json"])
    comparator = records_from_payload(reports["PR162R_A_QuantumComparatorCompatibilityMatrix.report.json"])
    _expect(quantum, failures, "quantum eligibility records missing")
    _expect(all(row.get("quantum_specific_mapping_ready_flag") for row in quantum), failures, "quantum mapping missing")
    _expect(all(row.get("quantum_comparator_ready_flag") for row in comparator), failures, "quantum comparator missing")
    latency = records_from_payload(reports["PR162R_A_LatencyClassCompatibilityMatrix.report.json"])
    _expect(not any(row.get("remote_quantum_hot_path_flag") for row in latency), failures, "remote quantum hot path detected")


def _validate_no_authority(summary: dict[str, Any], reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for field, expected in c.BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}={summary.get(field)}")
    for filename, report in reports.items():
        for record in records_from_payload(report):
            _expect(record.get("live_order_authority") is False, failures, f"{filename} live authority drift")
            _expect(not record.get("result_packet_created_flag"), failures, f"{filename} result packet drift")
            _expect(not record.get("profit_evidence_claim_flag"), failures, f"{filename} profit claim drift")


def _validate_future_bridges(summary: dict[str, Any], failures: list[str]) -> None:
    for field in (
        "post_launch_formula_plugin_future_bridge_count",
        "post_launch_formula_plugin_requirement_backlog_count",
        "formula_plugin_candidate_readiness_count",
        "quantum_plugin_candidate_readiness_count",
        "owner_formula_intake_future_bridge_count",
        "agent_formula_scout_future_bridge_count",
        "runtime_formula_allowlist_future_bridge_count",
        "formula_version_rollback_future_bridge_count",
        "hot_path_formula_latency_future_bridge_count",
    ):
        _expect(summary.get(field, 0) > 0, failures, f"{field} must be captured")


def _validate_generated_file_set(repo_root: Path, failures: list[str]) -> None:
    existing = {path.name for path in (repo_root / c.GENERATED_DIR).glob("PR162R_A_*.report.json")}
    expected = set(c.REPORT_FILENAMES)
    _expect(not (existing - expected), failures, f"orphan PR162R-A generated files: {sorted(existing - expected)}")
    _expect(expected.issubset(existing), failures, f"missing PR162R-A generated files: {sorted(expected - existing)}")


def _expect(condition: Any, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
