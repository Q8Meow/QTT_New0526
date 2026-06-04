"""Fail-closed validator for PR162D-R2A real formulations."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any, Callable

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    CANDIDATE_TRUTH_STATUSES,
    NO_AUTHORITY_FLAGS,
    SOURCE_TRUTH_STATUSES,
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
    formulations = records_from_payload(reports["PR162D_R2A_FormulationRecordRegistry.report.json"])
    test_vectors = records_from_payload(reports["PR162D_R2A_TestVectorRegistry.report.json"])
    packets = records_from_payload(reports["PR162D_R2A_CandidatePacketV1Registry.report.json"])
    family = records_from_payload(reports["PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json"])
    coverage = records_from_payload(reports["PR162D_R2A_FormulationCoverageAudit.report.json"])[0]
    summary = reports["PR162D_R2A_FinalSummary.report.json"]
    _validate_formulation_records(formulations, test_vectors, failures)
    _validate_candidate_packets(packets, {row["formulation_id"] for row in formulations}, failures)
    _validate_family_hierarchy(family, failures)
    _validate_formulation_coverage(coverage, packets, failures)
    _validate_quantum(records_from_payload(reports["PR162D_R2A_QuantumObjectiveRegistry.report.json"]), failures)
    _validate_comparators(records_from_payload(reports["PR162D_R2A_ClassicalComparatorRegistry.report.json"]), failures)
    _validate_human_review(repo_root, reports["PR162D_R2A_HumanReviewTopFormulations.report.json"], failures)
    _validate_summary(summary, failures)
    _validate_no_authority(summary, reports, failures)
    _validate_generated_file_set(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162D-R2A report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162D-R2A report is not an object: {path}")
            continue
        reports[filename] = payload
    md_path = repo_root / p.GENERATED_DIR / p.HUMAN_REVIEW_MD
    if not md_path.exists():
        failures.append(f"missing PR162D-R2A human review markdown: {md_path}")
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in (p.FORMULATION_RECORD_SCHEMA, p.CANDIDATE_PACKET_SCHEMA):
        if not (repo_root / p.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR162D-R2A schema: {filename}")
    for report in p.REPORT_FILENAMES:
        schema = report.replace(".report.json", ".schema.json")
        if not (repo_root / p.SCHEMA_DIR / schema).exists():
            failures.append(f"missing PR162D-R2A report schema: {schema}")


def _validate_common_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR162D_R2A", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(isinstance(payload.get("records"), list), failures, f"{filename} missing records list")
        _expect(payload.get("record_count") == len(payload.get("records", [])), failures, f"{filename} record_count mismatch")
        for flag, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} authority flag drift: {flag}")


def _validate_formulation_records(
    formulations: list[dict[str, Any]],
    test_vectors: list[dict[str, Any]],
    failures: list[str],
) -> None:
    _expect(formulations, failures, "formulation records missing")
    tv_by_id = {row["test_vector_id"]: row for row in test_vectors}
    for row in formulations:
        _expect(row.get("source_truth_status") in SOURCE_TRUTH_STATUSES, failures, f"invalid source truth status: {row.get('formulation_id')}")
        _expect(row.get("candidate_truth_status") in CANDIDATE_TRUTH_STATUSES, failures, f"invalid candidate truth status: {row.get('formulation_id')}")
        failures.extend(validate_record_authority(row).failures)
        if row.get("validator_materiality_status") == "FORMULATION_FULLY_MATERIALIZED":
            _expect(row.get("expression") or row.get("algorithm_procedure") or row.get("objective"), failures, f"fully materialized missing expression/procedure/objective: {row.get('formulation_id')}")
            _expect(row.get("callable_ref"), failures, f"fully materialized missing callable: {row.get('formulation_id')}")
            _expect(row.get("inputs") or row.get("variables"), failures, f"fully materialized missing inputs/variables: {row.get('formulation_id')}")
            _expect(row.get("outputs") or row.get("objective_output_meaning"), failures, f"fully materialized missing outputs/objective meaning: {row.get('formulation_id')}")
            _expect(row.get("units_or_type_hints") or row.get("unit_unknown_but_type_known_flag") is True, failures, f"fully materialized missing units/type hints: {row.get('formulation_id')}")
            _expect(row.get("test_vector_refs"), failures, f"fully materialized missing test vector: {row.get('formulation_id')}")
            for tv_ref in row.get("test_vector_refs", []):
                _expect(tv_ref in tv_by_id, failures, f"missing referenced test vector {tv_ref}")
            if row.get("formulation_type") == "QUANTUM_FORMULATION":
                _validate_quantum_formulation_record(row, tv_by_id, failures)
            else:
                _validate_callable_test_vector(row, tv_by_id, failures)


def _validate_callable_test_vector(
    row: dict[str, Any],
    tv_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    callable_obj = _import_callable(str(row["callable_ref"]), failures)
    if callable_obj is None:
        return
    for tv_ref in row["test_vector_refs"]:
        tv = tv_by_id[tv_ref]
        actual = callable_obj(dict(tv["inputs"]))
        _expect(_matches_expected(actual, tv["expected_outputs"], float(tv.get("tolerance", 0.0))), failures, f"test vector mismatch: {tv_ref}")


def _validate_quantum_formulation_record(
    row: dict[str, Any],
    tv_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    _expect(row.get("objective"), failures, f"quantum objective missing: {row.get('formulation_id')}")
    _expect(row.get("variables"), failures, f"quantum variables missing: {row.get('formulation_id')}")
    _expect(row.get("domains"), failures, f"quantum domains missing: {row.get('formulation_id')}")
    _expect(row.get("constraints") or row.get("penalties"), failures, f"quantum constraints/penalties missing: {row.get('formulation_id')}")
    _expect(row.get("classical_comparator_ref"), failures, f"quantum comparator missing: {row.get('formulation_id')}")
    callable_obj = _import_callable(str(row["callable_ref"]), failures)
    if callable_obj is None:
        return
    for tv_ref in row["test_vector_refs"]:
        shape = callable_obj(dict(tv_by_id[tv_ref]["inputs"]))
        _expect(shape.get("objective"), failures, f"quantum shape objective missing: {row.get('formulation_id')}")
        _expect(shape.get("variables"), failures, f"quantum shape variables missing: {row.get('formulation_id')}")
        _expect(shape.get("domains"), failures, f"quantum shape domains missing: {row.get('formulation_id')}")
        _expect(shape.get("classical_comparator_ref"), failures, f"quantum shape comparator missing: {row.get('formulation_id')}")
        _expect(shape.get("backend_execution") is False, failures, f"quantum backend execution drift: {row.get('formulation_id')}")
        _expect(shape.get("quantum_advantage_claim") is False, failures, f"quantum advantage claim drift: {row.get('formulation_id')}")


def _validate_candidate_packets(
    packets: list[dict[str, Any]],
    formulation_ids: set[str],
    failures: list[str],
) -> None:
    _expect(packets, failures, "CandidatePacketV1 registry missing")
    for packet in packets:
        _expect(packet.get("formulation_ref") or packet.get("exact_fill_action_ref"), failures, f"packet lacks formulation or fill action ref: {packet.get('candidate_packet_id')}")
        if packet.get("formulation_ref"):
            _expect(packet["formulation_ref"] in formulation_ids, failures, f"packet references unknown formulation: {packet['candidate_packet_id']}")
        _expect(packet.get("packet_only_flag") is False, failures, "packet-only QKU detected")
        _expect(packet.get("route_only_flag") is False, failures, "route-only QKU detected")
        _expect(packet.get("metadata_only_flag") is False, failures, "metadata-only QKU detected")
        _expect(packet.get("quantum_label_only_flag") is False, failures, "quantum-label-only QKU detected")
        failures.extend(validate_record_authority(packet).failures)


def _validate_family_hierarchy(rows: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(rows, failures, "family hierarchy missing")
    families = {row.get("domain_family_key") for row in rows}
    _expect(len(families) >= 9, failures, "normalized family keys collapsed too far")
    for row in rows:
        _expect(row.get("subfamily_key"), failures, f"family row missing subfamily: {row.get('hierarchy_id')}")
        _expect(row.get("variant_key"), failures, f"family row missing variant: {row.get('hierarchy_id')}")
        _expect(row.get("formulation_refs"), failures, f"family row lacks formulation refs: {row.get('hierarchy_id')}")


def _validate_formulation_coverage(
    coverage: dict[str, Any],
    packets: list[dict[str, Any]],
    failures: list[str],
) -> None:
    _expect(coverage.get("validation_status") == "PASS", failures, "formulation coverage audit must pass")
    _expect(coverage.get("formulation_backed_qku_count", 0) > coverage.get("field_fill_qku_count", 0), failures, "formulation-backed QKU count must exceed field-fill QKU count")
    _expect(coverage.get("field_fill_qku_percentage", 100.0) <= 25.0, failures, "too many PR162D QKUs are field-fill actions")
    _expect(coverage.get("normalized_family_unmapped_percentage", 100.0) <= 25.0, failures, "too many normalized families unmapped")
    _expect(coverage.get("field_fill_without_mapping_attempt_count") == 0, failures, "field fill exists without mapping-attempt evidence")
    _expect(coverage.get("packet_only_qku_count") == 0, failures, "packet-only QKU coverage drift")
    _expect(coverage.get("route_only_qku_count") == 0, failures, "route-only QKU coverage drift")
    _expect(coverage.get("metadata_only_qku_count") == 0, failures, "metadata-only QKU coverage drift")
    _expect(coverage.get("quantum_label_only_qku_count") == 0, failures, "quantum-label-only QKU coverage drift")
    _expect(len(packets) == coverage.get("formulation_backed_qku_count"), failures, "packet count must match formulation-backed QKUs")


def _validate_quantum(rows: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(rows, failures, "quantum objective registry missing")
    for row in rows:
        _expect(row.get("objective"), failures, f"quantum objective null: {row.get('quantum_formulation_id')}")
        _expect(row.get("variables"), failures, f"quantum variables empty: {row.get('quantum_formulation_id')}")
        _expect(row.get("domains"), failures, f"quantum domains empty: {row.get('quantum_formulation_id')}")
        _expect(row.get("classical_comparator_ref"), failures, f"quantum comparator missing: {row.get('quantum_formulation_id')}")
        _expect(row.get("quantum_backend_execution_flag") is False, failures, "quantum backend execution drift")
        _expect(row.get("quantum_advantage_claim_flag") is False, failures, "quantum advantage claim drift")


def _validate_comparators(rows: list[dict[str, Any]], failures: list[str]) -> None:
    _expect(len(rows) >= 25, failures, "classical comparator registry must contain at least 25 mappings")
    for row in rows:
        _expect(_import_callable(str(row["callable_ref"]), failures) is not None, failures, f"comparator callable not importable: {row.get('classical_comparator_id')}")
        _expect(row.get("procedure"), failures, f"comparator procedure missing: {row.get('classical_comparator_id')}")


def _validate_human_review(repo_root: Path, payload: dict[str, Any], failures: list[str]) -> None:
    rows = records_from_payload(payload)
    _expect(rows, failures, "human review JSON missing")
    record = rows[0]
    _expect(record.get("formula_count", 0) >= 50, failures, "human review formula count below 50")
    _expect(record.get("algorithm_count", 0) >= 25, failures, "human review algorithm count below 25")
    _expect(record.get("quantum_count", 0) >= 25, failures, "human review quantum count below 25")
    _expect(record.get("comparator_count", 0) >= 25, failures, "human review comparator count below 25")
    md = (repo_root / p.GENERATED_DIR / p.HUMAN_REVIEW_MD).read_text(encoding="utf-8")
    for token in ("YES_EV", "NO_EV", "IMPLIED_PROBABILITY", "KELLY", "BRIER", "RSI", "MACD", "VWAP", "QUBO", "CQM"):
        _expect(token in md, failures, f"human review markdown missing visible token: {token}")


def _validate_summary(summary: dict[str, Any], failures: list[str]) -> None:
    _expect(summary.get("real_formula_function_count", 0) >= 24, failures, "real formula count below threshold")
    _expect(summary.get("real_algorithm_callable_count", 0) >= 4, failures, "real algorithm count below threshold")
    _expect(summary.get("real_quantum_shape_builder_count", 0) >= 4, failures, "real quantum shape builder count below threshold")
    _expect(summary.get("real_classical_comparator_count", 0) >= 4, failures, "real comparator count below threshold")
    _expect(summary.get("test_vector_count", 0) >= summary.get("real_formula_function_count", 0) + summary.get("real_algorithm_callable_count", 0) + summary.get("real_quantum_shape_builder_count", 0), failures, "test vector count below callable count")
    _expect(summary.get("candidate_packet_v1_schema_created") is True, failures, "CandidatePacketV1 schema missing")
    _expect(summary.get("candidate_packet_v1_registry_created") is True, failures, "CandidatePacketV1 registry missing")
    _expect(summary.get("formulation_fully_materialized_count", 0) > 0, failures, "no fully materialized formulations")
    _expect(summary.get("quantum_mapping_records_created_count", 0) > 0, failures, "no quantum mapping records")
    _expect(summary.get("formula_latency_class_records_created_count", 0) > 0, failures, "no latency class records")
    _expect(summary.get("qku_agent_workflow_traceability_records_created_count", 0) > 0, failures, "no QKU traceability records")
    _expect(summary.get("orphan_qku_count") == 0, failures, "orphan QKUs detected")
    _expect(summary.get("orphan_generated_file_count") == 0, failures, "orphan generated files detected")


def _validate_no_authority(
    summary: dict[str, Any],
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for field, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(field) == expected, failures, f"boundary count drift: {field}={summary.get(field)}")
    for filename, report in reports.items():
        for row in records_from_payload(report):
            failures.extend(validate_record_authority(row).failures)
            _expect(row.get("live_order_authority") is not True, failures, f"{filename} row creates live order authority")


def _validate_generated_file_set(repo_root: Path, failures: list[str]) -> None:
    existing = {path.name for path in (repo_root / p.GENERATED_DIR).glob("PR162D_R2A_*.report.json")}
    expected = set(p.REPORT_FILENAMES)
    _expect(not (existing - expected), failures, f"orphan PR162D-R2A generated files: {sorted(existing - expected)}")
    _expect(expected.issubset(existing), failures, f"missing PR162D-R2A generated files: {sorted(expected - existing)}")


def _import_callable(callable_ref: str, failures: list[str]) -> Callable[[dict[str, Any]], dict[str, Any]] | None:
    try:
        module_name, attr_name = callable_ref.split(":", 1)
        module = importlib.import_module(module_name)
        obj = getattr(module, attr_name)
    except Exception as exc:  # pragma: no cover - failure path reported to validator output
        failures.append(f"cannot import callable {callable_ref}: {exc}")
        return None
    if not callable(obj):
        failures.append(f"callable_ref is not callable: {callable_ref}")
        return None
    return obj


def _matches_expected(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(key in actual and _matches_expected(actual[key], value, tolerance) for key, value in expected.items())
    if isinstance(expected, list) and isinstance(actual, list):
        return len(actual) == len(expected) and all(_matches_expected(a, e, tolerance) for a, e in zip(actual, expected, strict=True))
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(actual) - float(expected)) <= tolerance
    return actual == expected


def _expect(condition: Any, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
