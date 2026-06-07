"""Fail-closed validator for PR164 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    validate_record_authority,
)
from .central_reason_codes import PROHIBITED_DISPOSITIONS
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
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    summary = records["PR164_FinalSummary.report.json"][0]
    _validate_counts(records, summary, failures)
    _validate_computability(records, failures)
    _validate_missing_tasks(records, failures)
    _validate_source_policy(records, summary, failures)
    _validate_agent_routes(records, failures)
    _validate_quantum(records, failures)
    _validate_authority(summary, records, failures)
    _validate_manifest(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR164 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR164 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR164 schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in (
        "PR162D_R2A_CandidatePacketV1Registry.report.json",
        "PR163_B_FinalSummary.report.json",
        "PR163_B_PR164ReviewProvenanceHandoff.report.json",
    ):
        if not (repo_root / p.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR164 upstream artifact: {filename}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR164", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        if filename in p.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root must not duplicate row records")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("record_count") == payload.get("total_row_count"), failures, f"{filename} root row count mismatch")
        else:
            _expect(payload.get("record_count") == len(records_from_payload(payload)), failures, f"{filename} record_count mismatch")
        for key, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(key) is expected, failures, f"{filename} top-level authority flag drift: {key}")
        path = repo_root / p.GENERATED_DIR / filename
        if path.exists():
            _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds 10 MiB root report limit")
        for shard_path in payload.get("shard_files") or []:
            resolved = p.resolve_repo_relative(repo_root, shard_path)
            _expect(resolved.exists(), failures, f"{filename} missing shard: {shard_path}")
            if resolved.exists():
                _expect(resolved.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_path} exceeds 25 MiB shard limit")
        for record in records[filename]:
            failures.extend(validate_record_authority(record).failures)


def _validate_counts(records: dict[str, list[dict[str, Any]]], summary: dict[str, Any], failures: list[str]) -> None:
    expectations = {
        "qku_canonical_identity_rows": ("PR164_MasterQKUInventoryReconciliation.report.json", 9360),
        "qku_market_scope_rows": ("PR164_QKUMarketScopeCoverageAudit.report.json", 9360),
        "formula_objective_solver_coverage_rows": ("PR164_QKUFormulaObjectiveSolverCoverageAudit.report.json", 9360),
        "execution_cost_component_rows": ("PR164_ExecutionCostComponentCoverage.report.json", 9360),
        "latency_hot_path_rows": ("PR164_LatencyHotPathClassifier.report.json", 9360),
        "pr163_b_evidence_rows_reviewed": ("PR164_PR163BEvidenceReviewProvenanceRegistry.report.json", 6502),
        "pr163_b_divergence_rows_reviewed": ("PR164_PR163BDivergenceMaterialityReview.report.json", 6502),
        "pr163_b_rejection_rows_reviewed": ("PR164_PR163BInfrastructureRejectionReview.report.json", 6502),
        "pr165b_negative_memory_preparation_rows": ("PR164_PR165BNegativeMemoryPreparation.report.json", 6502),
    }
    for field, (filename, minimum) in expectations.items():
        _expect(summary.get(field, 0) == len(records[filename]), failures, f"{field} count mismatch")
        _expect(summary.get(field, 0) >= minimum, failures, f"{field} below expected minimum")
    _expect(summary.get("pr163_b_tca_rows_reviewed") == 6502, failures, "TCA reviewed count mismatch")
    _expect(summary.get("metadata_only_rows_remaining") == 0, failures, "metadata-only rows remain")
    _expect(summary.get("placeholder_only_rows_remaining") == 0, failures, "placeholder-only rows remain")
    _expect(summary.get("future_consumer_only_rows_remaining") == 0, failures, "future-consumer-only rows remain")
    _expect(summary.get("all_orphan_counts_zero") is True, failures, "orphan counts not zero")


def _validate_computability(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR164_QKUComputabilityMaterializationRegistry.report.json"]:
        disposition = row.get("computability_disposition")
        _expect(disposition not in PROHIBITED_DISPOSITIONS, failures, f"prohibited computability disposition: {disposition}")
        _expect(row.get("qku_formula_id"), failures, "computability row missing formula ref")
        _expect(row.get("replay_paper_materialization_route"), failures, "computability row missing replay/paper route")
        if disposition in {"COMPUTABLE_NOW", "COMPUTABLE_WITH_CANDIDATE_VALUES_FOR_REPLAY_PAPER"}:
            for field in (
                "formula_expression",
                "objective_expression",
                "input_fields",
                "output_fields",
                "parameter_fields",
                "parameter_domain",
                "test_vector_ref",
                "expected_test_vector_output",
                "replay_adapter_consumer",
                "paper_adapter_consumer",
                "pr165_scoring_consumer",
                "downstream_agent_consumers",
            ):
                _expect(bool(row.get(field)), failures, f"computable row missing {field}")


def _validate_missing_tasks(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR164_QKUMissingValueFillRouter.report.json"]:
        for field in (
            "exact_missing_field",
            "expected_type",
            "valid_range_or_domain",
            "candidate_source_targets",
            "candidate_estimation_policy_for_replay_paper",
            "confidence_hint",
            "route_to_pr162d_r3_or_pr162b_r_or_pr163c",
        ):
            _expect(bool(row.get(field)), failures, f"missing fill task lacks {field}")
        _expect(row.get("no_live_use_until_downstream_verified_flag") is True, failures, "missing fill task live flag drift")


def _validate_source_policy(records: dict[str, list[dict[str, Any]]], summary: dict[str, Any], failures: list[str]) -> None:
    source_rows = records["PR164_CandidateSourceAcquisitionLedger.report.json"]
    _expect(source_rows, failures, "candidate source acquisition ledger missing")
    _expect(summary.get("nonofficial_candidate_source_rows", 0) > 0, failures, "nonofficial candidate source rows missing")
    _expect(
        records["PR164_CandidateSourcePolicyAudit.report.json"][0]["nonofficial_rejected_merely_because_nonofficial_count"] == 0,
        failures,
        "nonofficial sources rejected merely because nonofficial",
    )
    _expect(any(row["source_policy_disposition"].startswith("REJECT_") for row in source_rows), failures, "explicit rejected source rows missing")


def _validate_agent_routes(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR164_AgentOrchestrationRouter.report.json"]:
        for field in ("upstream_agent", "downstream_agent", "downstream_pr_route", "report_consumer"):
            _expect(bool(row.get(field)), failures, f"agent route missing {field}")
        if row.get("candidate_id"):
            _expect(bool(row.get("replay_paper_consumer")), failures, "agent route missing replay/paper consumer")


def _validate_quantum(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR164_QuantumCompatibilityRouter.report.json"]:
        _expect(row.get("quantum_backend_execution_allowed_flag") is False, failures, "quantum backend allowed")
        _expect(row.get("quantum_advantage_claim_allowed_flag") is False, failures, "quantum advantage claim allowed")
        _expect(row.get("classical_comparator_required_flag") is True, failures, "quantum row lacks classical comparator")
        _expect(bool(row.get("classical_comparator_formula_ref")), failures, "quantum comparator formula missing")


def _validate_authority(summary: dict[str, Any], records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(key) == expected, failures, f"summary authority count drift: {key}")
    _expect(summary.get("all_prohibited_authority_counts_zero") is True, failures, "authority count summary not zero")


def _validate_manifest(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    manifest = records["PR164_ReportManifest.report.json"]
    filenames = {row["report_filename"] for row in manifest}
    _expect(filenames == set(p.REPORT_FILENAMES), failures, "manifest does not cover every PR164 report")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
