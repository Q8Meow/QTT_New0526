"""Fail-closed PR162D-R1 artifact validator."""

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
    summary = reports["PR162D_R1_FinalSummary.report.json"]
    _validate_summary_thresholds(summary, failures)
    _validate_source_records(records_from_payload(reports["PR162D_R1_ExternalSourceAcquisitionLedger.report.json"]), failures)
    _validate_formula_records(records_from_payload(reports["PR162D_R1_FormulaAcquisitionLedger.report.json"]), failures)
    _validate_algorithm_records(records_from_payload(reports["PR162D_R1_AlgorithmAcquisitionLedger.report.json"]), failures)
    _validate_quantum_records(records_from_payload(reports["PR162D_R1_QuantumFormulaAcquisitionLedger.report.json"]), failures)
    _validate_candidate_routes(records_from_payload(reports["PR162D_R1_ComputableCandidateRegistry.report.json"]), failures)
    _validate_no_authority(summary, reports, failures)
    _validate_consumption(records_from_payload(reports["PR162D_R1_PR162DConsumptionAudit.report.json"]), failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162D-R1 report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162D-R1 report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162D-R1 schema: {filename}")


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


def _validate_summary_thresholds(summary: dict[str, Any], failures: list[str]) -> None:
    for field, minimum in c.THRESHOLDS.items():
        _expect(summary.get(field, 0) >= minimum, failures, f"{field} below minimum: {summary.get(field)} < {minimum}")
    zero_fields = (
        "metadata_only_candidate_count",
        "quantum_metadata_only_count",
        "unrouted_external_candidate_count",
        "live_promotion_ready_count",
        "order_ready_count",
        "profit_evidence_count",
        "private_state_fetch_count",
        "order_execution_count",
        "qtt_sha_freeze_checksum_authority_count",
        "atomicrows_bundle_hash_sha_authority_count",
        "atomicrows_bundle_mutation_count",
        "source_locator_missing_count",
        "formula_expression_missing_count",
        "quantum_objective_missing_count",
        "qku_ref_missing_count",
        "agent_route_missing_count",
        "replay_paper_route_missing_count",
        "hallucinated_source_record_count",
    )
    for field in zero_fields:
        _expect(summary.get(field) == 0, failures, f"{field} must be zero, got {summary.get(field)}")
    _expect(summary.get("pr162d_consumed_not_rebuilt_flag") is True, failures, "PR162D outputs must be consumed, not rebuilt")
    _expect(summary.get("active_branch") == c.EXPECTED_BRANCH, failures, "branch context mismatch")


def _validate_source_records(sources: list[dict[str, Any]], failures: list[str]) -> None:
    required = {
        "source_locator",
        "source_tier",
        "source_class",
        "authority_class",
        "confidence_class",
        "candidate_or_provisional_flag",
        "official_truth_flag",
        "qku_refs",
        "agent_route_refs",
        "replay_paper_route_refs",
    }
    _expect(len(sources) >= c.THRESHOLDS["external_source_candidates_created"], failures, "external source candidates missing")
    for source in sources:
        missing = sorted(required - set(source))
        _expect(not missing, failures, f"source record missing fields {missing}: {source.get('source_id')}")
        _expect(source.get("source_locator"), failures, f"source missing locator: {source.get('source_id')}")
        _expect(source.get("candidate_or_provisional_flag") is True, failures, f"source not candidate/provisional: {source.get('source_id')}")
        _expect(source.get("replay_paper_route_refs"), failures, f"source lacks replay/paper route: {source.get('source_id')}")
        if not source.get("official_truth_flag"):
            labels = set(source.get("candidate_labels", []))
            _expect("NON_OFFICIAL_REPLAY_PAPER_CANDIDATE" in labels, failures, f"non-official source not replay/paper labeled: {source.get('source_id')}")
            _expect("NOT_OFFICIAL_EXTERNAL_FACT" in labels, failures, f"non-official source fact authority drift: {source.get('source_id')}")


def _validate_formula_records(formulas: list[dict[str, Any]], failures: list[str]) -> None:
    required = {
        "formula_id",
        "source_locator",
        "source_tier",
        "source_class",
        "authority_class",
        "confidence_class",
        "candidate_or_provisional_flag",
        "official_truth_flag",
        "expression",
        "variables",
        "input_fields",
        "output_fields",
        "units",
        "valid_range",
        "default_parameter_candidates",
        "formula_family",
        "qku_refs",
        "agent_refs",
        "replay_paper_route_refs",
        "test_vector",
        "deterministic_implementation_function_reference",
        "missing_input_behavior",
        "formula_equivalence_family_id",
        "dedupe_key",
        "live_order_authority",
    }
    _expect(len(formulas) >= c.THRESHOLDS["external_formula_candidates_created"], failures, "formula candidates missing")
    dedupe: set[str] = set()
    for formula in formulas:
        missing = sorted(required - set(formula))
        _expect(not missing, failures, f"formula record missing fields {missing}: {formula.get('formula_id')}")
        _expect(formula.get("expression"), failures, f"formula expression missing: {formula.get('formula_id')}")
        _expect(formula.get("input_fields"), failures, f"formula inputs missing: {formula.get('formula_id')}")
        _expect(formula.get("output_fields"), failures, f"formula outputs missing: {formula.get('formula_id')}")
        _expect(formula.get("units"), failures, f"formula units missing: {formula.get('formula_id')}")
        _expect(formula.get("live_order_authority") is False, failures, f"formula live authority drift: {formula.get('formula_id')}")
        key = str(formula.get("dedupe_key"))
        _expect(key not in dedupe, failures, f"formula dedupe duplicate count inflation: {key}")
        dedupe.add(key)


def _validate_algorithm_records(algorithms: list[dict[str, Any]], failures: list[str]) -> None:
    required = {
        "algorithm_id",
        "source_locator",
        "algorithm_family",
        "objective",
        "inputs",
        "outputs",
        "deterministic_steps",
        "parameters",
        "parameter_ranges",
        "complexity_class_candidate",
        "qku_refs",
        "agent_refs",
        "replay_paper_route_refs",
        "test_vector",
        "dedupe_key",
        "live_order_authority",
    }
    _expect(len(algorithms) >= c.THRESHOLDS["external_algorithm_candidates_created"], failures, "algorithm candidates missing")
    for algorithm in algorithms:
        missing = sorted(required - set(algorithm))
        _expect(not missing, failures, f"algorithm record missing fields {missing}: {algorithm.get('algorithm_id')}")
        _expect(algorithm.get("deterministic_steps"), failures, f"algorithm steps missing: {algorithm.get('algorithm_id')}")
        _expect(algorithm.get("parameters"), failures, f"algorithm parameters missing: {algorithm.get('algorithm_id')}")
        _expect(algorithm.get("test_vector"), failures, f"algorithm test vector missing: {algorithm.get('algorithm_id')}")
        _expect(algorithm.get("live_order_authority") is False, failures, f"algorithm live authority drift: {algorithm.get('algorithm_id')}")


def _validate_quantum_records(quantum: list[dict[str, Any]], failures: list[str]) -> None:
    required = {
        "quantum_candidate_id",
        "source_locator",
        "quantum_family",
        "mathematical_objective",
        "variable_definitions",
        "constraint_definitions",
        "parameter_definitions",
        "coefficient_definitions",
        "qubo_mapping",
        "ising_mapping",
        "bqm_cqm_mapping",
        "qaoa_vqe_samplingvqe_annealing_mapping",
        "penalty_terms",
        "parameter_ranges_defaults",
        "local_exact_smoke_test_representation",
        "provider_dry_run_payload_compatibility",
        "strongest_classical_comparator_mapping",
        "qku_refs",
        "agent_refs",
        "replay_paper_route_refs",
        "no_quantum_advantage_claim",
        "no_profit_evidence_claim",
        "live_order_authority",
    }
    _expect(len(quantum) >= c.THRESHOLDS["quantum_formula_candidates_created"], failures, "quantum candidates missing")
    for record in quantum:
        missing = sorted(required - set(record))
        _expect(not missing, failures, f"quantum record missing fields {missing}: {record.get('quantum_candidate_id')}")
        _expect(record.get("mathematical_objective"), failures, f"quantum objective missing: {record.get('quantum_candidate_id')}")
        _expect(record.get("variable_definitions"), failures, f"quantum variables missing: {record.get('quantum_candidate_id')}")
        _expect(record.get("constraint_definitions"), failures, f"quantum constraints missing: {record.get('quantum_candidate_id')}")
        _expect(record.get("coefficient_definitions"), failures, f"quantum coefficients missing: {record.get('quantum_candidate_id')}")
        _expect(record.get("quantum_metadata_only_flag") is False, failures, f"quantum metadata-only record: {record.get('quantum_candidate_id')}")
        _expect(record.get("no_quantum_advantage_claim") is True, failures, f"quantum advantage claim drift: {record.get('quantum_candidate_id')}")
        _expect(record.get("no_profit_evidence_claim") is True, failures, f"quantum profit claim drift: {record.get('quantum_candidate_id')}")
        _expect(record.get("live_order_authority") is False, failures, f"quantum live authority drift: {record.get('quantum_candidate_id')}")


def _validate_candidate_routes(candidates: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(len(candidates) >= c.THRESHOLDS["qku_mapped_external_candidate_count"], failures, "candidate registry too small for mapping threshold")
    for record in candidates:
        cid = record.get("candidate_id")
        _expect(record.get("qku_refs"), failures, f"candidate missing qku route: {cid}")
        _expect(record.get("agent_refs") or record.get("agent_route_refs"), failures, f"candidate missing agent route: {cid}")
        _expect(record.get("replay_paper_route_refs"), failures, f"candidate missing replay/paper route: {cid}")
        _expect(record.get("live_order_authority") is False, failures, f"candidate live authority drift: {cid}")
        _expect(record.get("metadata_only_flag") is False, failures, f"metadata-only candidate: {cid}")


def _validate_no_authority(summary: dict[str, Any], reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for field, expected in c.BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}={summary.get(field)}")
    for filename, report in reports.items():
        for record in records_from_payload(report):
            if "live_order_authority" in record:
                _expect(record["live_order_authority"] is False, failures, f"{filename} live authority record drift: {record.get('candidate_id') or record.get('audit_id')}")
            _expect(not record.get("order_execution_count"), failures, f"{filename} order execution drift")
            _expect(not record.get("private_state_fetch_count"), failures, f"{filename} private state drift")


def _validate_consumption(consumption: list[dict[str, Any]], failures: list[str]) -> None:
    pr162d_rows = [record for record in consumption if str(record.get("input_ref", "")).startswith("docs/master_plan/generated/PR162D")]
    _expect(pr162d_rows, failures, "PR162D consumption rows missing")
    _expect(all(record.get("present_flag") for record in pr162d_rows), failures, "required PR162D input missing")
    _expect(all(record.get("consumption_mode") == "CONSUME_EXISTING_OUTPUT_NO_REBUILD" for record in pr162d_rows), failures, "PR162D consumption mode must not rebuild")


def _expect(condition: Any, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
