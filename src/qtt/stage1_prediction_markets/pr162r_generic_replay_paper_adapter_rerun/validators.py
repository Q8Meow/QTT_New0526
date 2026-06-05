"""Fail-closed validator for PR162R generic adapter rerun artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    COMPUTABILITY_ROUTES,
    DATA_BINDING_STATUSES,
    DISALLOWED_GENERATED_STATUSES,
    NO_AUTHORITY_FLAGS,
    PAIRED_STATUSES,
    PAPER_STATUSES,
    REPLAY_STATUSES,
    SMOKE_STATUSES,
    TRUTH_STATUSES,
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
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_common_contracts(reports, failures)
    summary = reports["PR162R_FinalSummary.report.json"]
    _validate_summary(summary, failures)
    _validate_ingestion(reports, failures)
    _validate_computability(records_from_payload(reports["PR162R_QKUComputabilityClassificationMatrix.report.json"]), failures)
    _validate_smoke(records_from_payload(reports["PR162R_FormulationSmokeExecutionLedger.report.json"]), summary, failures)
    _validate_source_materialization(records_from_payload(reports["PR162R_SourceCandidateMaterializationQueue.report.json"]), failures)
    _validate_online_scout(records_from_payload(reports["PR162R_OnlineSourceScoutQueue.report.json"]), failures)
    _validate_data_binding(reports, failures)
    _validate_adapter_packets(reports, failures)
    _validate_run_requests(reports, failures)
    _validate_quantum(records_from_payload(reports["PR162R_QuantumBatchPrecomputeRoutingPlan.report.json"]), failures)
    _validate_orchestration(reports, failures)
    _validate_authority(summary, reports, failures)
    _validate_generated_file_set(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162R report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162R report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not (repo_root / p.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162R schema: {filename}")


def _validate_common_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR162R", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(isinstance(payload.get("records"), list), failures, f"{filename} missing records list")
        _expect(payload.get("record_count") == len(payload.get("records", [])), failures, f"{filename} record_count mismatch")
        _expect(payload.get("source_inputs"), failures, f"{filename} missing source_inputs")
        for flag, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")
        for row in records_from_payload(payload):
            failures.extend(validate_record_authority(row).failures)
            _scan_disallowed(row, failures, filename)


def _validate_summary(summary: dict[str, Any], failures: list[str]) -> None:
    required_minimums = {
        "candidate_packet_v1_ingested_count": 6502,
        "pr162d_r2a_candidate_packet_ingested_count": 6502,
        "pr162d_r2a_generic_candidate_extension_count": 1,
        "qku_computability_classification_rows_count": 6502,
        "formulation_callable_registry_refs_loaded_count": 1,
        "formula_callable_smoke_checked_count": 1,
        "algorithm_callable_smoke_checked_count": 1,
        "quantum_shape_builder_smoke_checked_count": 1,
        "classical_comparator_smoke_checked_count": 1,
        "replay_adapter_input_packet_count": 1,
        "paper_adapter_input_packet_count": 1,
        "paired_replay_paper_run_request_candidate_count": 1,
        "data_binding_requirement_rows_count": 1,
        "missing_data_binding_action_count": 1,
        "source_candidate_materialization_row_count": 1,
        "online_source_scout_queue_row_count": 1,
        "quantum_batch_precompute_rows_count": 1,
        "latency_precompute_rows_count": 1,
        "qku_agent_replay_paper_handoff_rows_count": 1,
        "pr163_handoff_seed_count": 1,
        "pr164_handoff_seed_count": 1,
        "pr165_handoff_seed_count": 1,
        "pr162e_compatibility_seed_count": 1,
    }
    for field, minimum in required_minimums.items():
        _expect(summary.get(field, 0) >= minimum, failures, f"{field} below minimum {minimum}: {summary.get(field)}")
    for field in (
        "metadata_only_ready_count",
        "orphan_candidate_count",
        "orphan_generated_report_count",
        "orphan_qku_count",
        "orphan_handoff_count",
    ):
        _expect(summary.get(field) == 0, failures, f"{field} must be zero")
    _expect(summary.get("old_548_backward_compatibility_preserved") is True, failures, "old 548 compatibility not preserved")
    _expect(summary.get("old_548_compatibility_trace_count") == 548, failures, "old 548 trace count mismatch")
    for field, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}={summary.get(field)}")


def _validate_ingestion(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    ingestion = records_from_payload(reports["PR162R_CandidatePacketV1IngestionLedger.report.json"])
    schema = records_from_payload(reports["PR162R_CandidatePacketSchemaCompatibilityAudit.report.json"])
    old = records_from_payload(reports["PR162R_Old548CompatibilityTrace.report.json"])
    _expect(len(ingestion) >= 6502, failures, "CandidatePacketV1 ingestion ignored 6502 universe")
    _expect(all(row.get("generic_extension_present_flag") for row in ingestion), failures, "generic extension not traced for every packet")
    _expect(all(row.get("schema_compatible_flag") for row in schema), failures, "schema compatibility failure")
    _expect(len(old) == 548, failures, "old 548 compatibility trace missing")
    _expect(not any(row.get("overwrites_pr162d_r2a_universe_flag") for row in old), failures, "old 548 overwrote R2A universe")
    route_inputs = records_from_payload(reports["PR162R_RouteTriageCrosswalkConsumptionAudit.report.json"])
    _expect(route_inputs, failures, "route/crosswalk/market/command files ignored")


def _validate_computability(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        _expect(row.get("qku_id"), failures, "QKU row missing qku_id")
        _expect(row.get("candidate_packet_ref"), failures, "QKU row missing candidate_packet_ref")
        _expect(row.get("computability_route") in COMPUTABILITY_ROUTES, failures, f"invalid computability route: {row.get('computability_route')}")
        _expect(row.get("upstream_route_refs"), failures, "QKU row has no upstream route")
        _expect(row.get("downstream_route_refs"), failures, "QKU row has no downstream route")
        _expect(row.get("metadata_only_ready_flag") is False, failures, "metadata-only ready state exists")
        if row.get("candidate_type") in {"FORMULA", "FEATURE", "ALGORITHM", "PARAMETER_PACK"}:
            _expect(row.get("callable_ref") or row.get("exact_fill_action_ref"), failures, "executable QKU lacks callable and fill action")
        if row.get("candidate_type") == "QUANTUM_FORMULATION":
            _expect(row.get("quantum_shape_payload_present_flag") is True or row.get("exact_fill_action_ref"), failures, "quantum QKU lacks shape payload/fill action")


def _validate_smoke(rows: list[dict[str, Any]], summary: dict[str, Any], failures: list[str]) -> None:
    _expect(summary["formula_callable_smoke_checked_count"] > 0, failures, "formula smoke checks missing")
    _expect(summary["algorithm_callable_smoke_checked_count"] > 0, failures, "algorithm smoke checks missing")
    _expect(summary["quantum_shape_builder_smoke_checked_count"] > 0, failures, "quantum shape smoke checks missing")
    _expect(summary["classical_comparator_smoke_checked_count"] > 0, failures, "comparator smoke checks missing")
    for row in rows:
        _expect(row.get("smoke_execution_status") in SMOKE_STATUSES, failures, f"invalid smoke status: {row.get('smoke_execution_status')}")
        if row.get("smoke_execution_status") == "SMOKE_EXECUTION_PASSED":
            proof = row.get("proof", {})
            _expect(proof.get("callable_imported") is True, failures, "smoke passed without callable import proof")
            _expect(row.get("test_vector_ref") or row.get("callable_family") == "CLASSICAL_COMPARATOR", failures, "smoke passed without test vector/comparator proof")
        if row.get("callable_family") == "QUANTUM_SHAPE_BUILDER" and row.get("smoke_execution_status") == "SMOKE_EXECUTION_PASSED":
            _expect(row.get("backend_execution_flag") is False, failures, "quantum backend execution drift")
            _expect(row.get("simulator_execution_flag") is False, failures, "quantum simulator execution drift")
            _expect(row.get("quantum_advantage_claim_flag") is False, failures, "quantum advantage claim drift")


def _validate_source_materialization(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        _expect(row.get("source_class"), failures, "source candidate lacks source_class")
        _expect(row.get("source_locator"), failures, "source candidate lacks locator")
        _expect(row.get("candidate_truth_status") in TRUTH_STATUSES, failures, "source candidate truth status invalid")
        _expect(row.get("no_accepted_source_truth_claim") is True, failures, "source candidate promoted to accepted truth")


def _validate_online_scout(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        for field in ("target_field", "expected_unit", "expected_scale", "responsible_agent", "replay_impact", "paper_impact"):
            _expect(row.get(field), failures, f"online-source queue row lacks {field}")
        _expect(row.get("ci_network_required_flag") is False, failures, "CI must not require network")


def _validate_data_binding(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    binding = records_from_payload(reports["PR162R_ReplayPaperDataBindingRequirementMatrix.report.json"])
    actions = records_from_payload(reports["PR162R_MissingDataBindingActionQueue.report.json"])
    action_ids = {row.get("action_id") for row in actions}
    for row in binding:
        _expect(row.get("data_binding_status") in DATA_BINDING_STATUSES, failures, "invalid data binding status")
        _expect(row.get("route_ready_treated_as_data_ready_flag") is False, failures, "route-ready treated as data-ready")
        _expect(row.get("fill_action_refs"), failures, "missing binding row lacks fill actions")
        _expect(all(ref in action_ids for ref in row.get("fill_action_refs", [])), failures, "binding references unknown fill action")
    for row in actions:
        for field in ("missing_field", "responsible_agent", "suggested_source_classes", "downstream_consumer", "priority_score"):
            _expect(row.get(field), failures, f"missing data action lacks {field}")


def _validate_adapter_packets(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, status_key, allowed in (
        ("PR162R_ReplayAdapterInputPacketRegistry.report.json", "replay_adapter_status", REPLAY_STATUSES),
        ("PR162R_PaperAdapterInputPacketRegistry.report.json", "paper_adapter_status", PAPER_STATUSES),
    ):
        for row in records_from_payload(reports[filename]):
            _expect(row.get("candidate_packet_ref"), failures, f"{filename} row lacks candidate_packet_ref")
            _expect(row.get("formulation_ref") or row.get("fill_action_refs"), failures, f"{filename} row lacks formulation/fill")
            _expect(row.get("computability_route"), failures, f"{filename} row lacks QKU route")
            _expect(row.get("agent_refs"), failures, f"{filename} row lacks agent route")
            _expect(row.get(status_key) in allowed, failures, f"{filename} invalid status")
            _expect(row.get("paired_status") in PAIRED_STATUSES, failures, f"{filename} invalid paired status")
            if row.get(status_key, "").endswith("READY"):
                _expect(not row.get("missing_inputs"), failures, f"{filename} ready row has missing inputs")
            _expect(row.get("live_order_authority") is False, failures, f"{filename} live authority drift")


def _validate_run_requests(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    replay = {row["replay_run_request_candidate_id"] for row in records_from_payload(reports["PR162R_ReplayRunRequestCandidateQueue.report.json"])}
    paper = {row["paper_run_request_candidate_id"] for row in records_from_payload(reports["PR162R_PaperRunRequestCandidateQueue.report.json"])}
    for row in records_from_payload(reports["PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json"]):
        _expect(row.get("replay_run_request_candidate_ref") in replay, failures, "paired plan references nonexistent replay request")
        _expect(row.get("paper_run_request_candidate_ref") in paper, failures, "paired plan references nonexistent paper request")


def _validate_quantum(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        _expect(row.get("objective_present_flag") is True, failures, "quantum objective missing")
        _expect(row.get("variables_present_flag") is True, failures, "quantum variables missing")
        _expect(row.get("domains_present_flag") is True, failures, "quantum domains missing")
        _expect(row.get("classical_comparator_refs") or row.get("comparator_fill_action_ref"), failures, "quantum comparator missing")
        _expect("Quantum Advisory / Quantum Mapping Agent" in row.get("downstream_agent_routes", []), failures, "quantum route missing advisory agent")
        _expect(row.get("quantum_backend_execution_count") == 0, failures, "quantum backend execution drift")
        _expect(row.get("quantum_simulator_execution_count") == 0, failures, "quantum simulator execution drift")
        _expect(row.get("quantum_advantage_claim_count") == 0, failures, "quantum advantage claim drift")


def _validate_orchestration(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    handoff = records_from_payload(reports["PR162R_QKUAgentReplayPaperHandoffMatrix.report.json"])
    _expect(handoff, failures, "handoff rows missing")
    _expect(not any(row.get("orphan_flag") for row in handoff), failures, "orphan handoff row detected")
    for filename in (
        "PR162R_PR163PaperAdapterHandoffSeed.report.json",
        "PR162R_PR164ReviewProvenanceHandoffSeed.report.json",
        "PR162R_PR165ScoringRankingHandoffSeed.report.json",
    ):
        for row in records_from_payload(reports[filename]):
            _expect(row.get("downstream_compatibility_refs"), failures, f"{filename} missing downstream compatibility refs")
    _expect(records_from_payload(reports["PR162R_PR162EPluginReplayPaperCompatibilitySeed.report.json"]), failures, "PR162E compatibility seed missing")


def _validate_authority(summary: dict[str, Any], reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for field, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}={summary.get(field)}")
    for report in reports.values():
        for row in records_from_payload(report):
            for field, expected in BOUNDARY_COUNT_FIELDS.items():
                if field in row:
                    _expect(row.get(field) == expected, failures, f"row boundary count drift: {field}")


def _validate_generated_file_set(repo_root: Path, failures: list[str]) -> None:
    existing = {
        path.name
        for path in (repo_root / p.GENERATED_DIR).glob("PR162R_*.report.json")
        if not path.name.startswith(("PR162R_A_", "PR162R_B_"))
    }
    expected = set(p.REPORT_FILENAMES)
    _expect(not (existing - expected), failures, f"orphan PR162R generated files: {sorted(existing - expected)}")
    _expect(expected.issubset(existing), failures, f"missing PR162R generated files: {sorted(expected - existing)}")


def _scan_disallowed(row: dict[str, Any], failures: list[str], filename: str) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, str) and value in DISALLOWED_GENERATED_STATUSES:
            failures.append(f"{filename} contains disallowed generated status: {value}")
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(row)


def _expect(condition: Any, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
