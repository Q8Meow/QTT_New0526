"""PR161C validation API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json
from .models import ValidationResult
from .report_builder import build_artifacts


def validate_artifacts(repo_root: Path | str) -> ValidationResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    for filename in c.PR161C_REPORT_FILENAMES:
        if not (root / c.GENERATED_DIR / filename).exists():
            failures.append(f"PR161C_REPORT_MISSING: {filename}")
    if failures:
        return ValidationResult(tuple(sorted(failures)), ())

    summary = read_json(root / c.GENERATED_DIR / "PR161C_QKUFinalAssimilationSummary.report.json")
    failures.extend(_validate_summary(summary))
    qku_records = _load_report_records(root, "PR161C_QKU9360PrimaryMaterializationRegistry.report.json")
    facet_records = _load_report_records(root, "PR161C_QKU22625FieldValueFacetLinkage.report.json")
    edge_records = _load_report_records(root, "PR161C_QKUOrchestrationGraphEdges.report.json")
    quantum_trace_records = _load_report_records(root, "PR161C_QKUQuantumResidualTrace.report.json")
    supplemental_records = _load_report_records(root, "PR161C_QKUSupplementalArtifactScout.report.json")
    residual_justification_records = _load_report_records(root, "PR161C_QKUResidualDiagnosticJustification.report.json")
    graph_quality = read_json(root / c.GENERATED_DIR / "PR161C_QKUGraphQualityMetrics.report.json")
    failures.extend(_validate_records(qku_records, facet_records, edge_records))
    failures.extend(
        _validate_semantic_integrity(
            summary,
            qku_records,
            quantum_trace_records,
            supplemental_records,
            residual_justification_records,
            graph_quality,
        )
    )

    rebuilt = build_artifacts(root)
    rebuilt_summary = rebuilt.summary
    deterministic_fields = (
        "primary_qku_source_membership_record_count",
        "pr161a_field_value_facet_count",
        "expanded_qku_and_field_facet_record_count_if_emitted",
        "qku_orchestration_graph_node_count",
        "qku_orchestration_graph_edge_count",
    )
    for field in deterministic_fields:
        if summary.get(field) != rebuilt_summary.get(field):
            failures.append(f"PR161C_REPORT_STALE_OR_NONDETERMINISTIC: {field}")
    return ValidationResult(tuple(sorted(set(failures))), (c.SUCCESS_MARKER,) if not failures else ())


def _load_report_records(root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(root / c.GENERATED_DIR / filename)
    if isinstance(payload, dict) and payload.get("sharded_flag"):
        records: list[dict[str, Any]] = []
        for shard_file in payload.get("shard_files", []):
            shard_payload = read_json(root / str(shard_file))
            records.extend(shard_payload.get("records", []))
        return records
    return payload.get("records", []) if isinstance(payload, dict) else []


def _validate_summary(summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "pr161a_entity_qku_count": c.EXPECTED_PR161A_ENTITY_QKUS,
        "pr161a_atomicrow_qku_count": c.EXPECTED_PR161A_ATOMICROW_QKUS,
        "pr161a_pr154_qku_count": c.EXPECTED_PR161A_PR154_QKUS,
        "pr161b_residual_qku_count": c.EXPECTED_PR161B_RESIDUAL_QKUS,
        "primary_qku_source_membership_record_count": c.EXPECTED_PRIMARY_QKU_SOURCE_MEMBERSHIP_RECORDS,
        "pr161a_field_value_facet_count": c.EXPECTED_PR161A_FIELD_VALUE_FACETS,
        "expanded_qku_and_field_facet_record_count_if_emitted": c.EXPECTED_EXPANDED_QKU_AND_FIELD_FACET_RECORDS,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            failures.append(f"PR161C_COUNT_MISMATCH: {field} expected={expected_value} observed={summary.get(field)}")
    if summary.get("remaining_unassimilated_residual_count") != 0:
        failures.append("PR161C_REMAINING_UNASSIMILATED_RESIDUALS")
    if summary.get("remaining_unmaterialized_primary_qku_count") != 0:
        failures.append("PR161C_REMAINING_UNMATERIALIZED_QKUS")
    if summary.get("remaining_unlinked_qku_count") != 0:
        failures.append("PR161C_REMAINING_UNLINKED_QKUS")
    if summary.get("remaining_isolated_non_rejected_qku_count") != 0:
        failures.append("PR161C_REMAINING_ISOLATED_NON_REJECTED_QKUS")
    if summary.get("forbidden_authority_scan_status") != "PASS":
        failures.append("PR161C_FORBIDDEN_AUTHORITY_SCAN_NOT_PASS")
    if summary.get("no_scattered_hardcoded_authority_audit_status") != "PASS":
        failures.append("PR161C_NO_SCATTERED_AUTHORITY_AUDIT_NOT_PASS")
    if summary.get("qku_type_count_sum") != summary.get("primary_qku_source_membership_record_count"):
        failures.append("PR161C_QKU_TYPE_COUNT_SUM_DOES_NOT_MATCH_PRIMARY_QKU_COUNT")
    if not summary.get("qku_type_count_reconciled_flag"):
        failures.append("PR161C_QKU_TYPE_COUNT_NOT_RECONCILED")
    if summary.get("pr161b_quantum_residual_trace_count") != c.EXPECTED_PR161B_QUANTUM_RESIDUALS:
        failures.append("PR161C_PR161B_QUANTUM_RESIDUAL_TRACE_COUNT_INVALID")
    expected_quantum_families = {
        "QUBO": c.EXPECTED_PR161B_QUBO_RESIDUALS,
        "ISING": c.EXPECTED_PR161B_ISING_RESIDUALS,
        "QAOA": c.EXPECTED_PR161B_QAOA_RESIDUALS,
        "VQE": c.EXPECTED_PR161B_VQE_RESIDUALS,
        "ANNEALING": c.EXPECTED_PR161B_ANNEALING_RESIDUALS,
        "HYBRID": c.EXPECTED_PR161B_HYBRID_QUANTUM_CLASSICAL_RESIDUALS,
    }
    trace_counts = summary.get("pr161b_quantum_residual_trace_counts_by_family") or {}
    for family, expected_count in expected_quantum_families.items():
        if trace_counts.get(family) != expected_count:
            failures.append(f"PR161C_PR161B_QUANTUM_FAMILY_TRACE_COUNT_INVALID: {family}")
    if not summary.get("supplemental_category_reconciled_flag"):
        failures.append("PR161C_SUPPLEMENTAL_CATEGORY_COUNTS_NOT_RECONCILED")
    return failures


def _validate_semantic_integrity(
    summary: dict[str, Any],
    qku_records: list[dict[str, Any]],
    quantum_trace_records: list[dict[str, Any]],
    supplemental_records: list[dict[str, Any]],
    residual_justification_records: list[dict[str, Any]],
    graph_quality: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    type_count_sum = sum(1 for record in qku_records if record.get("qku_type") in c.QKU_TYPES)
    if type_count_sum != c.EXPECTED_PRIMARY_QKU_SOURCE_MEMBERSHIP_RECORDS:
        failures.append("PR161C_QKU_RECORD_TYPE_ENUM_COVERAGE_INVALID")
    if len(quantum_trace_records) != c.EXPECTED_PR161B_QUANTUM_RESIDUALS:
        failures.append("PR161C_QUANTUM_TRACE_RECORDS_MISSING")
    if summary.get("pr161b_quantum_residual_trace_gap_count") != 0:
        failures.append("PR161C_QUANTUM_TRACE_GAP_NOT_ZERO")
    residual_records = [record for record in qku_records if record.get("qku_master_inventory_membership") == "PR161B_RESIDUAL_QKU"]
    if residual_records and all(record.get("qku_residual_diagnostic_class") == "TRUE_NEW_QKU_REQUIRED" for record in residual_records):
        if not residual_justification_records:
            failures.append("PR161C_ALL_TRUE_NEW_RESIDUAL_DIAGNOSTIC_WITHOUT_JUSTIFICATION")
    if len(residual_justification_records) != c.EXPECTED_PR161B_RESIDUAL_QKUS:
        failures.append("PR161C_RESIDUAL_DIAGNOSTIC_JUSTIFICATION_COUNT_INVALID")
    supplemental_counts: dict[str, int] = {}
    for record in supplemental_records:
        key = str(record.get("scout_classification"))
        supplemental_counts[key] = supplemental_counts.get(key, 0) + 1
    if sum(supplemental_counts.values()) != summary.get("supplemental_qku_candidates_discovered_count"):
        failures.append("PR161C_SUPPLEMENTAL_SCOUT_CATEGORY_SUM_INVALID")
    range_records = [record for record in qku_records if record.get("qku_type") == "RANGE_QKU"]
    if any(record.get("qku_materialization_state") != "MATERIALIZED_RANGE_DEFAULT" for record in range_records):
        failures.append("PR161C_RANGE_QKU_MATERIALIZATION_INCOMPLETE")
    optimizer_records = [record for record in qku_records if record.get("qku_type") == "OPTIMIZER_SETTING_QKU"]
    if any(record.get("qku_materialization_state") != "MATERIALIZED_OPTIMIZER_CONFIG" for record in optimizer_records):
        failures.append("PR161C_OPTIMIZER_QKU_MATERIALIZATION_INCOMPLETE")
    if graph_quality.get("fallback_upstream_edges") is None or graph_quality.get("fallback_downstream_edges") is None:
        failures.append("PR161C_GRAPH_FALLBACK_EDGE_METRICS_MISSING")
    if graph_quality.get("natural_upstream_edges", 0) + graph_quality.get("fallback_upstream_edges", 0) != summary.get("qku_orchestration_graph_upstream_edge_count"):
        failures.append("PR161C_GRAPH_UPSTREAM_QUALITY_COUNT_MISMATCH")
    if graph_quality.get("natural_downstream_edges", 0) + graph_quality.get("fallback_downstream_edges", 0) != summary.get("qku_orchestration_graph_downstream_edge_count"):
        failures.append("PR161C_GRAPH_DOWNSTREAM_QUALITY_COUNT_MISMATCH")
    if summary.get("online_retrieval_attempted_count", 0) <= 0:
        failures.append("PR161C_ONLINE_RETRIEVAL_NOT_ATTEMPTED")
    if summary.get("online_retrieval_succeeded_count", 0) <= 0 and summary.get("online_retrieval_unavailable_count", 0) <= 0:
        failures.append("PR161C_ONLINE_RETRIEVAL_STATUS_NOT_RECORDED")
    return failures


def _validate_records(
    qku_records: list[dict[str, Any]],
    facet_records: list[dict[str, Any]],
    edge_records: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    if len(qku_records) != c.EXPECTED_PRIMARY_QKU_SOURCE_MEMBERSHIP_RECORDS:
        failures.append("PR161C_PRIMARY_QKU_RECORD_COUNT_INVALID")
    if len(facet_records) != c.EXPECTED_PR161A_FIELD_VALUE_FACETS:
        failures.append("PR161C_FIELD_VALUE_FACET_RECORD_COUNT_INVALID")
    by_qku: dict[str, list[dict[str, Any]]] = {}
    for edge in edge_records:
        by_qku.setdefault(str(edge.get("source_qku_id")), []).append(edge)
        if edge.get("edge_type") not in c.QKU_GRAPH_EDGE_TYPES:
            failures.append(f"PR161C_UNKNOWN_GRAPH_EDGE_TYPE: {edge.get('edge_type')}")
        if any(token in str(edge).upper() for token in ("PROFIT_EVIDENCE_ACCEPTED", "LIVE_ORDER_AUTHORITY", "REPLAY_RESULT_ACCEPTED", "PAPER_RESULT_ACCEPTED", "OPTIMIZER_EXECUTION_RESULT", "QUANTUM_BACKEND_EXECUTION_RESULT")):
            failures.append(f"PR161C_FORBIDDEN_EVIDENCE_EDGE: {edge.get('edge_id')}")
    edge_ids = [str(edge.get("edge_id")) for edge in edge_records]
    if len(edge_ids) != len(set(edge_ids)):
        failures.append("PR161C_DUPLICATE_GRAPH_EDGE_ID")
    for record in qku_records:
        qku_id = str(record.get("qku_id"))
        if record.get("rename_existing_term_flag") is not False:
            failures.append(f"PR161C_GLOBAL_RENAME_FLAG_INVALID: {qku_id}")
        if record.get("legacy_term_preserved_flag") is not True:
            failures.append(f"PR161C_LEGACY_TERM_NOT_PRESERVED: {qku_id}")
        if not record.get("qku_materialized_flag"):
            failures.append(f"PR161C_QKU_NOT_MATERIALIZED: {qku_id}")
        if record.get("qku_graph_isolated_flag"):
            failures.append(f"PR161C_NON_REJECTED_QKU_ISOLATED: {qku_id}")
        edges = by_qku.get(qku_id, [])
        if not any(edge.get("edge_direction") == "UPSTREAM" for edge in edges):
            failures.append(f"PR161C_UPSTREAM_EDGE_MISSING: {qku_id}")
        if not any(edge.get("edge_direction") == "DOWNSTREAM" for edge in edges):
            failures.append(f"PR161C_DOWNSTREAM_EDGE_MISSING: {qku_id}")
    return failures
