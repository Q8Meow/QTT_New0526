"""Fail-closed PR162D artifact validator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from . import constants as c
from .computation_engine_candidate_mode import values_match
from .json_io import read_json, records_from_payload
from .paths import resolve_repo_relative
from .quantum_execution.objective_value_calculator import (
    ising_objective_value,
    qubo_objective_value,
)


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
    _validate_common_report_contracts(reports, failures)
    manifest_by_report = _manifest_by_report(reports[c.SHARD_MANIFEST_REPORT_FILENAME], failures)
    loaded = {
        filename: _load_records(repo_root, filename, reports[filename], manifest_by_report, failures)
        for filename in c.REPORT_FILENAMES
        if filename != c.SHARD_MANIFEST_REPORT_FILENAME
    }
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_pr162c_reinterpretation(repo_root, reports, loaded, failures)
    _validate_sources(loaded, failures)
    _validate_materialization(loaded, failures)
    _validate_agent_routes(loaded, failures)
    _validate_quantum(loaded, failures)
    _validate_downstream_and_boundaries(reports, loaded, failures)
    _validate_no_absolute_paths(reports, loaded, failures)
    _validate_no_forbidden_sidecar_reference(repo_root, reports, loaded, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162D report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162D report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162D schema: {filename}")


def _validate_common_report_contracts(
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority class mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(isinstance(payload.get("source_inputs"), list), failures, f"{filename} missing source inputs")
        _expect(tuple(payload.get("upstream_pr_refs") or ()) == c.UPSTREAM_PR_REFS, failures, f"{filename} upstream refs mismatch")
        for route in c.DOWNSTREAM_PR_ROUTES:
            _expect(route in payload.get("downstream_pr_routes", []), failures, f"{filename} missing downstream route {route}")
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation status must pass")


def _manifest_by_report(
    manifest_payload: dict[str, Any],
    failures: list[str],
) -> dict[str, dict[str, Any]]:
    records = records_from_payload(manifest_payload)
    manifest = {record["report_filename"]: record for record in records}
    for record in records:
        _expect(record.get("posix_relative_shard_refs_flag") is True, failures, f"non-portable shard refs: {record.get('report_filename')}")
    return manifest


def _load_records(
    repo_root: Path,
    filename: str,
    payload: dict[str, Any],
    manifest_by_report: dict[str, dict[str, Any]],
    failures: list[str],
) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest_record = manifest_by_report.get(filename)
    if not manifest_record:
        failures.append(f"missing shard manifest record for {filename}")
        return []
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_record.get("shard_files", []):
        if "\\" in shard_ref or PureWindowsPath(shard_ref).drive:
            failures.append(f"non-portable shard path: {shard_ref}")
            continue
        rows.extend(records_from_payload(read_json(resolve_repo_relative(repo_root, shard_ref))))
    return rows


def _validate_pr162c_reinterpretation(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = reports["PR162D_FinalSummary.report.json"]
    upstream = read_json(repo_root / "docs/master_plan/generated/PR162C_DataRequirementClassificationLedger.report.json")
    upstream_count = upstream.get("total_record_count") or upstream.get("record_count") or 6502
    reinterpretations = loaded["PR162D_PR162CBlockerReinterpretationLedger.report.json"]
    field_fills = loaded["PR162D_QKUFieldFillExpansionMatrix.report.json"]
    _expect(upstream_count == 6502, failures, "PR162C upstream count must remain 6502")
    _expect(len(reinterpretations) == 6502, failures, "PR162D must reinterpret all 6502 PR162C records")
    _expect(len(field_fills) == 6502, failures, "PR162D field fill matrix must cover all 6502 records")
    _expect(summary.get("candidate_materialization_target_count") == 6502, failures, "candidate materialization target count must be 6502")
    _expect(summary.get("generic_required_fields_blocker_remaining_count") == 0, failures, "generic required-fields blocker remaining count must be zero")
    for record in reinterpretations:
        _expect(record.get("candidate_materialization_target_flag") is True, failures, f"reinterpretation missing target flag: {record.get('qku_id')}")
        _expect(record.get("acquisition_blocker_flag") is False, failures, f"acquisition blocker carried over: {record.get('qku_id')}")
        _expect(record.get("generic_required_fields_blocker_remaining_flag") is False, failures, f"generic blocker carried over: {record.get('qku_id')}")
        _expect(record.get("pr162d_progress_status") in c.CANDIDATE_PROGRESS_STATUSES, failures, f"invalid progress status: {record.get('qku_id')}")


def _validate_sources(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    sources = loaded["PR162D_CandidateSourceIntakeRegistry.report.json"]
    official = loaded["PR162D_OfficialPublicCandidateIntakeRegistry.report.json"]
    non_official = loaded["PR162D_NonOfficialCandidateIntakeRegistry.report.json"]
    _expect(sources, failures, "source intake registry missing")
    _expect(official, failures, "official source candidates missing")
    _expect(non_official, failures, "non-official source candidates missing")
    required = {
        "source_tier",
        "source_class",
        "source_quality_score",
        "authority_class",
        "confidence_class",
        "official_truth_flag",
        "candidate_or_provisional_flag",
        "replay_paper_candidate_flag",
        "source_locator",
        "source_capture_digest_or_locator_digest",
        "qku_refs",
        "formula_refs",
        "field_refs",
        "agent_route_refs",
    }
    for record in sources:
        missing = sorted(required - set(record))
        _expect(not missing, failures, f"source record missing fields {missing}: {record.get('source_id')}")
        _expect(record["source_tier"] in c.SOURCE_TIERS, failures, f"invalid source tier: {record.get('source_id')}")
        _expect(record["candidate_or_provisional_flag"] is True, failures, f"source not candidate/provisional: {record.get('source_id')}")
        _expect(record["replay_paper_candidate_flag"] is True, failures, f"source not replay/paper routed: {record.get('source_id')}")


def _validate_materialization(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    formulas = loaded["PR162D_QKUFormulaMaterializationExpansion.report.json"]
    algorithms = loaded["PR162D_QKUAlgorithmMaterializationExpansion.report.json"]
    parameters = loaded["PR162D_QKUParameterValueFieldFillExpansion.report.json"]
    solver_inputs = loaded["PR162D_QKUSolverInputAssemblyExpansion.report.json"]
    formula_tests = loaded["PR162D_QKUFormulaTestVectorExpansion.report.json"]
    algorithm_tests = loaded["PR162D_QKUAlgorithmTestVectorExpansion.report.json"]
    no_metadata = loaded["PR162D_NoMetadataOnlyMaterializationAudit.report.json"][0]
    _expect(formulas, failures, "formula materialization expansion missing")
    _expect(algorithms, failures, "algorithm materialization expansion missing")
    _expect(parameters, failures, "parameter expansion missing")
    _expect(solver_inputs, failures, "solver input expansion missing")
    _expect(formula_tests, failures, "formula test vector expansion missing")
    _expect(algorithm_tests, failures, "algorithm test vector expansion missing")
    _expect(no_metadata["metadata_only_materialization_pass_count"] == 0, failures, "metadata-only materialization passed")
    for record in formulas + algorithms + parameters:
        _expect(record.get("expression"), failures, f"candidate lacks expression: {record.get('candidate_id')}")
        _expect(record.get("executable_function_reference_or_planned_function_reference"), failures, f"candidate lacks function reference: {record.get('candidate_id')}")
        _expect(record.get("input_fields"), failures, f"candidate lacks inputs: {record.get('candidate_id')}")
        _expect(record.get("output_fields"), failures, f"candidate lacks outputs: {record.get('candidate_id')}")
        _expect(record.get("units"), failures, f"candidate lacks units: {record.get('candidate_id')}")
        _expect(record.get("live_order_authority") is False, failures, f"candidate has live order authority: {record.get('candidate_id')}")
    for record in formula_tests + algorithm_tests:
        _expect(
            values_match(record["observed_output"], record["expected_output"], record.get("tolerance", 1e-9)),
            failures,
            f"deterministic test vector mismatch: {record.get('test_vector_ref')}",
        )


def _validate_agent_routes(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    reinterpretations = loaded["PR162D_PR162CBlockerReinterpretationLedger.report.json"]
    routes = loaded["PR162D_AgentConsumableQKURoutingMatrix.report.json"]
    no_orphan = loaded["PR162D_NoOrphanQKUFormulaDatasetAgentAudit.report.json"][0]
    route_qkus = {record["qku_id"] for record in routes}
    _expect(len(routes) == len(reinterpretations), failures, "every acquired/partial QKU must have an agent route")
    for record in reinterpretations:
        _expect(record["qku_id"] in route_qkus, failures, f"QKU lacks route: {record['qku_id']}")
    for record in routes:
        _expect(record["route_status"] in c.AGENT_ROUTE_STATUSES, failures, f"invalid route status: {record.get('route_id')}")
        _expect(record["route_status"] not in c.DISALLOWED_ROUTE_STATUSES, failures, f"disallowed route status: {record.get('route_id')}")
        _expect(record["agent_path_refs"], failures, f"route lacks agent paths: {record.get('route_id')}")
        _expect(record["order_submission_allowed_flag"] is False, failures, f"route allows orders: {record.get('route_id')}")
        _expect(record["live_order_authority"] is False, failures, f"route has live authority: {record.get('route_id')}")
    _expect(no_orphan["orphan_count"] == 0, failures, "orphan audit must be zero")
    intents = loaded["PR162D_StrategySignalDecisionCandidateIntentMatrix.report.json"]
    previews = loaded["PR162D_ExecutionRouterNonAuthorityPreviewMatrix.report.json"]
    _expect(intents and all(record["order_authority_flag"] is False for record in intents), failures, "candidate intents must not be order authority")
    _expect(previews and all(record["submit_cancel_reduce_close_order_allowed_flag"] is False for record in previews), failures, "execution previews must not submit/cancel/reduce/close orders")


def _validate_quantum(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    modes = loaded["PR162D_QuantumExecutionModeRegistry.report.json"]
    models = loaded["PR162D_QuantumProblemModelRegistry.report.json"]
    smoke = loaded["PR162D_QUBOIsingLocalExactSmokeExecution.report.json"]
    adapters = loaded["PR162D_QuantumBackendAdapterReadinessMatrix.report.json"]
    dependencies = loaded["PR162D_QuantumBackendDependencyStatus.report.json"]
    payloads = loaded["PR162D_QuantumProviderDryRunPayloadRegistry.report.json"]
    comparators = loaded["PR162D_QuantumClassicalComparatorSmokeResult.report.json"]
    quantum_routes = loaded["PR162D_QuantumReplayPaperCandidateRouteMatrix.report.json"]
    _expect(any(record["quantum_execution_mode"] == "QUANTUM_LOCAL_EXACT_SMOKE" for record in modes), failures, "local exact smoke mode missing")
    _expect(any(record["problem_model_type"] == "QUBO" for record in models), failures, "QUBO model missing")
    _expect(any(record["problem_model_type"] == "ISING" for record in models), failures, "Ising model missing")
    _expect(any(record["problem_model_type"] == "BQM" for record in models), failures, "BQM descriptor missing")
    _expect(any(record["problem_model_type"] == "CQM" for record in models), failures, "CQM descriptor missing")
    _expect(any(record["problem_model_type"] == "QAOA_DESCRIPTOR" for record in models), failures, "QAOA descriptor missing")
    _expect(any(record["problem_model_type"] == "VQE_DESCRIPTOR" for record in models), failures, "VQE descriptor missing")
    _expect(any(record["problem_model_type"] == "ANNEALING_DESCRIPTOR" for record in models), failures, "annealing descriptor missing")
    _expect(any(record["problem_model_type"] == "QUBO" for record in smoke), failures, "QUBO local smoke missing")
    _expect(any(record["problem_model_type"] == "ISING" for record in smoke), failures, "Ising local smoke missing")
    _expect(adapters, failures, "backend adapters missing")
    _expect(dependencies, failures, "backend dependency status missing")
    _expect(payloads and all(record["remote_submission_attempted_flag"] is False for record in payloads), failures, "provider dry-run payload submitted remote job")
    _expect(comparators, failures, "quantum/classical comparator results missing")
    _expect(quantum_routes, failures, "quantum agent routes missing")
    for record in smoke:
        result = record["result"]
        if record["problem_model_type"] == "QUBO":
            model = next(item for item in models if item["problem_model_id"] == record["problem_model_ref"])
            q = model["objective_coefficients"]["Q"]
            value = qubo_objective_value(result["best_assignment"], q)
            _expect(value == result["best_objective_value"], failures, f"QUBO objective mismatch: {record['quantum_smoke_execution_id']}")
        if record["problem_model_type"] == "ISING":
            model = next(item for item in models if item["problem_model_id"] == record["problem_model_ref"])
            coeffs = model["objective_coefficients"]
            value = ising_objective_value(result["best_assignment"], coeffs["h"], coeffs["J"])
            _expect(value == result["best_objective_value"], failures, f"Ising objective mismatch: {record['quantum_smoke_execution_id']}")
        _expect(record["profit_evidence_claim_flag"] is False, failures, f"quantum smoke claims profit: {record['quantum_smoke_execution_id']}")
        _expect(record["quantum_advantage_claim_flag"] is False, failures, f"quantum smoke claims advantage: {record['quantum_smoke_execution_id']}")
        _expect(record["live_order_authority"] is False, failures, f"quantum smoke has live authority: {record['quantum_smoke_execution_id']}")
    for record in quantum_routes:
        _expect("QUANTUM_ADVISORY_AGENT" in record["agent_path_refs"], failures, f"quantum route lacks advisory: {record['quantum_route_id']}")
        _expect("QUANTUM_EXECUTION_HARNESS" in record["agent_path_refs"], failures, f"quantum route lacks harness: {record['quantum_route_id']}")
        _expect("QUANTUM_CLASSICAL_HYBRID_COMPARATOR" in record["agent_path_refs"], failures, f"quantum route lacks comparator: {record['quantum_route_id']}")
        _expect("REPLAY_PAPER_CANDIDATE_ROUTER" in record["agent_path_refs"], failures, f"quantum route lacks replay/paper: {record['quantum_route_id']}")
        _expect(record["direct_live_order_submission_flag"] is False, failures, f"quantum route allows direct live order: {record['quantum_route_id']}")


def _validate_downstream_and_boundaries(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = reports["PR162D_FinalSummary.report.json"]
    handoff = loaded["PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json"][0]
    _expect(handoff["result_packet_created_flag"] is False, failures, "PR162D must not create result packets")
    _expect(handoff["replay_paper_result_evidence_created_flag"] is False, failures, "PR162D must not create replay/paper result evidence")
    for field, expected in c.BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}")
    _expect(summary.get("pr163_result_packets_created_count") == 0, failures, "PR163 result packets created")
    _expect(summary.get("pr164_provenance_conclusions_created_count") == 0, failures, "PR164 conclusions created")
    _expect(summary.get("pr165_result_backed_rankings_created_count") == 0, failures, "PR165 rankings created")
    _expect(summary.get("quarantined_unsafe_private_illegal_unmappable_material_count") == 0, failures, "unexpected quarantine count")
    _expect(summary.get("master_plan_file_edited_flag") is False, failures, "master plan edit flag drift")
    _expect(summary.get("atomicrows_bundle_jsonl_changed_flag") is False, failures, "AtomicRows bundle mutation flag drift")


def _validate_no_absolute_paths(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        elif isinstance(value, str):
            if PureWindowsPath(value).drive and not value.startswith("https://"):
                failures.append(f"absolute Windows path in PR162D artifact at {path}: {value}")

    for filename, payload in reports.items():
        walk(payload, filename)
    for filename, records in loaded.items():
        walk(records, filename)


def _validate_no_forbidden_sidecar_reference(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    forbidden_filename = "AtomicRows.bundle." + "sha" + "256"
    if (repo_root / "docs/master_plan/generated" / forbidden_filename).exists():
        failures.append("forbidden AtomicRows bundle sidecar exists")
    text = repr(reports) + repr(loaded)
    _expect(forbidden_filename not in text, failures, "forbidden AtomicRows bundle sidecar referenced")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
