from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_residual_candidate_assimilation import constants as c
from src.qtt.stage1_prediction_markets.qku_residual_candidate_assimilation.validator import (
    _load_report_records,
    validate_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SUMMARY_PATH = REPO_ROOT / "docs/master_plan/generated/PR161C_QKUFinalAssimilationSummary.report.json"
SCHEMA_DIR = REPO_ROOT / c.SCHEMA_DIR


@pytest.fixture(scope="module")
def summary() -> dict[str, object]:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def qku_records() -> list[dict[str, object]]:
    return _load_report_records(
        REPO_ROOT,
        "PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    )


@pytest.fixture(scope="module")
def field_facets() -> list[dict[str, object]]:
    return _load_report_records(
        REPO_ROOT,
        "PR161C_QKU22625FieldValueFacetLinkage.report.json",
    )


@pytest.fixture(scope="module")
def graph_edges() -> list[dict[str, object]]:
    return _load_report_records(
        REPO_ROOT,
        "PR161C_QKUOrchestrationGraphEdges.report.json",
    )


@pytest.fixture(scope="module")
def quantum_trace() -> list[dict[str, object]]:
    return _load_report_records(
        REPO_ROOT,
        "PR161C_QKUQuantumResidualTrace.report.json",
    )


def test_pr161c_observed_counts_match_owner_approved_targets(summary, qku_records, field_facets):
    assert summary["pr161a_entity_qku_count"] == 4525
    assert summary["pr161a_atomicrow_qku_count"] == 4183
    assert summary["pr161a_pr154_qku_count"] == 342
    assert summary["pr161b_residual_qku_count"] == 4835
    assert summary["primary_qku_source_membership_record_count"] == 9360
    assert summary["pr161a_field_value_facet_count"] == 22625
    assert summary["expanded_qku_and_field_facet_record_count_if_emitted"] == 31985
    assert len(qku_records) == 9360
    assert len(field_facets) == 22625
    assert summary["qku_type_count_sum"] == 9360
    assert summary["qku_type_count_reconciled_flag"] is True


def test_pr161c_full_materialization_and_non_breaking_overlay(qku_records):
    assert all(record["qku_materialized_flag"] for record in qku_records)
    assert all(record["legacy_term_preserved_flag"] for record in qku_records)
    assert all(record["rename_existing_term_flag"] is False for record in qku_records)
    assert all(record["qku_live_use_allowed_flag"] is False for record in qku_records)
    assert all(record["qku_no_profit_evidence_created_flag"] for record in qku_records)
    assert all(record["qku_no_optimizer_execution_flag"] for record in qku_records)
    assert all(record["qku_no_quantum_backend_execution_flag"] for record in qku_records)


def test_pr161c_graph_connects_every_non_rejected_qku(qku_records, graph_edges, summary):
    edges_by_qku: dict[str, list[dict[str, object]]] = {}
    for edge in graph_edges:
        edges_by_qku.setdefault(str(edge["source_qku_id"]), []).append(edge)
        assert edge["edge_type"] in c.QKU_GRAPH_EDGE_TYPES
        assert not any(
            forbidden in str(edge)
            for forbidden in (
                "SOURCE_ACCEPTED_AS_LIVE_ORDER_AUTHORITY",
                "SOURCE_ACCEPTED_AS_PROFIT_EVIDENCE",
                "SOURCE_ACCEPTED_AS_REPLAY_RESULT",
                "SOURCE_ACCEPTED_AS_PAPER_RESULT",
                "SOURCE_ACCEPTED_AS_OPTIMIZER_EXECUTION_RESULT",
                "SOURCE_ACCEPTED_AS_QUANTUM_BACKEND_EXECUTION_RESULT",
            )
        )
    assert summary["qku_orchestration_graph_node_count"] == 9360
    assert summary["qku_orchestration_graph_edge_count"] == len(graph_edges)
    assert summary["natural_upstream_edges"] + summary["fallback_upstream_edges"] == summary["qku_orchestration_graph_upstream_edge_count"]
    assert summary["natural_downstream_edges"] + summary["fallback_downstream_edges"] == summary["qku_orchestration_graph_downstream_edge_count"]
    assert summary["linked_real_validator_count"] == 9360
    assert summary["qku_non_rejected_isolated_node_count"] == 0
    for record in qku_records:
        qku_edges = edges_by_qku[str(record["qku_id"])]
        assert any(edge["edge_direction"] == "UPSTREAM" for edge in qku_edges)
        assert any(edge["edge_direction"] == "DOWNSTREAM" for edge in qku_edges)
        assert record["qku_graph_isolated_flag"] is False


def test_pr161c_ids_are_deterministic_labels_not_hash_authority(qku_records, graph_edges):
    hex_digest = re.compile(r"\\b[0-9a-f]{40,64}\\b", re.IGNORECASE)
    assert all(record["qku_id"].startswith("QKU-") for record in qku_records)
    assert all(edge["edge_id"].startswith("QKUEDGE-") for edge in graph_edges)
    assert not any(hex_digest.search(str(record["qku_id"])) for record in qku_records)
    assert not any(hex_digest.search(str(edge["edge_id"])) for edge in graph_edges)


def test_pr161c_schema_enum_parity_with_constants():
    qku_schema = json.loads((SCHEMA_DIR / "pr161c_qku_record.schema.json").read_text(encoding="utf-8"))
    edge_schema = json.loads((SCHEMA_DIR / "pr161c_qku_orchestration_graph_edge.schema.json").read_text(encoding="utf-8"))
    assert qku_schema["properties"]["qku_type"]["enum"] == list(c.QKU_TYPES)
    assert qku_schema["properties"]["qku_source_class"]["enum"] == list(c.QKU_SOURCE_CLASSES)
    assert qku_schema["properties"]["qku_source_acceptance_state"]["enum"] == list(c.QKU_SOURCE_ACCEPTANCE_STATES)
    assert edge_schema["properties"]["edge_type"]["enum"] == list(c.QKU_GRAPH_EDGE_TYPES)


def test_pr161c_semantic_repair_quantum_residual_trace_and_diagnostics(summary, qku_records, quantum_trace):
    assert len(quantum_trace) == c.EXPECTED_PR161B_QUANTUM_RESIDUALS
    assert summary["pr161b_quantum_residual_trace_count"] == c.EXPECTED_PR161B_QUANTUM_RESIDUALS
    assert summary["pr161b_quantum_residual_trace_gap_count"] == 0
    counts = summary["pr161b_quantum_residual_trace_counts_by_family"]
    assert counts["QUBO"] == c.EXPECTED_PR161B_QUBO_RESIDUALS
    assert counts["ISING"] == c.EXPECTED_PR161B_ISING_RESIDUALS
    assert counts["QAOA"] == c.EXPECTED_PR161B_QAOA_RESIDUALS
    assert counts["VQE"] == c.EXPECTED_PR161B_VQE_RESIDUALS
    assert counts["ANNEALING"] == c.EXPECTED_PR161B_ANNEALING_RESIDUALS
    assert counts["HYBRID"] == c.EXPECTED_PR161B_HYBRID_QUANTUM_CLASSICAL_RESIDUALS
    residual_diagnostics = [
        record["qku_residual_diagnostic_class"]
        for record in qku_records
        if record["qku_master_inventory_membership"] == "PR161B_RESIDUAL_QKU"
    ]
    assert len(set(residual_diagnostics)) > 1


def test_pr161c_semantic_repair_market_online_range_optimizer_and_supplemental(summary, qku_records):
    assert summary["prediction_market_qku_count"] < summary["primary_qku_source_membership_record_count"]
    assert summary["market_agnostic_qku_count"] > 0
    assert summary["stage1_directly_applicable_qku_count"] > 0
    assert summary["stage1_indirectly_applicable_qku_count"] > 0
    assert summary["online_retrieval_attempted_count"] > 0
    assert summary["online_retrieval_succeeded_count"] > 0
    assert summary["online_scout_queue_count"] >= 0
    assert summary["supplemental_category_count_sum"] == summary["supplemental_qku_candidates_discovered_count"]
    range_records = [record for record in qku_records if record["qku_type"] == "RANGE_QKU"]
    optimizer_records = [record for record in qku_records if record["qku_type"] == "OPTIMIZER_SETTING_QKU"]
    assert range_records
    assert optimizer_records
    assert all(record["qku_materialization_state"] == "MATERIALIZED_RANGE_DEFAULT" for record in range_records)
    assert all(record["qku_materialization_state"] == "MATERIALIZED_OPTIMIZER_CONFIG" for record in optimizer_records)
    assert all(record["qku_owner_fallback_reason"] for record in qku_records if record["qku_owner_fallback_default_used_flag"])


def test_pr161c_validation_api_and_sharding_status(summary):
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures
    assert summary["remaining_unassimilated_residual_count"] == 0
    assert summary["remaining_unmaterialized_primary_qku_count"] == 0
    assert summary["remaining_unlinked_qku_count"] == 0
    assert summary["remaining_isolated_non_rejected_qku_count"] == 0
    assert summary["forbidden_authority_scan_status"] == "PASS"
    assert summary["no_scattered_hardcoded_authority_audit_status"] == "PASS"
    assert summary["report_sharding_status"] == "SHARDED_LARGE_REPORTS_UNDER_50_MB"
    assert summary["largest_generated_pr161c_report_size_bytes"] < c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES
