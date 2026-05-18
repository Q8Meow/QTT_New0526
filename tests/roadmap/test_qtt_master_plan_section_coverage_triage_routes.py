from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools import validate_qtt_master_plan_section_coverage_triage_routes as routes_gate


REPORT = Path("docs/master_plan/generated/MasterPlanSectionCoverageReport.json")


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_triage_routes_validator_accepts_existing_section_coverage_family():
    result = routes_gate.validate()

    assert result.ok, result.failures
    assert result.report is not None
    route_map = result.report["route_map"]
    assert route_map["route_map_id"] == "QTT_MASTER_PLAN_SECTION_COVERAGE_TRIAGE_ROUTES_V1_0"
    assert route_map["authority_class"] == (
        "STATIC_CONTROL_PLANE_ROUTE_MAP_NOT_MASTER_PLAN_AUTHORITY"
    )
    assert route_map["repo_canonical_pr_label"] == "PR119"
    assert route_map["roadmap_pr_label"] == "PR #102"
    assert route_map["controller_decision_reference"].endswith(
        "#/roadmap_range_currentization/1"
    )


def test_triage_route_counts_and_no_authority_flags_are_reported():
    summary = _report()["route_map_summary"]

    assert summary["route_entry_count"] == 13
    assert summary["count_by_route_class"]["UNRESOLVED_DEFAULT_ROUTE"] == 1
    assert summary["quantum_forward_route_count"] == 1
    assert summary["optimizer_arbitration_route_count"] == 1
    assert summary["latency_cost_route_count"] == 1
    assert summary["master_plan_mutation_count"] == 0
    assert summary["runtime_authority_created"] is False
    assert summary["live_authority_created"] is False
    assert summary["source_fact_acceptance_created"] is False
    assert summary["connector_semantic_binding_created"] is False
    assert summary["replay_paper_result_created"] is False
    assert summary["order_authority_created"] is False
    assert summary["profit_evidence_created"] is False
    assert summary["latency_superiority_evidence_created"] is False
    assert summary["quantum_backend_simulator_optimizer_execution_created"] is False


def test_quantum_optimizer_latency_routes_are_static_metadata_only():
    entries = {
        entry["current_route_class"]: entry
        for entry in _report()["route_map"]["route_entries"]
    }
    for route_class in (
        "QUANTUM_FORWARD_OPTIMIZATION_ROUTE",
        "OPTIMIZER_ARBITRATION_ROUTE",
        "LATENCY_COST_ROUTE",
    ):
        metadata = entries[route_class]["quantum_forward_metadata"]
        assert metadata["quantum_relevance_class"] != "NONE"
        assert metadata["no_backend_execution_flag"] is True
        assert metadata["no_simulator_execution_flag"] is True
        assert metadata["no_optimizer_runtime_execution_flag"] is True
        assert metadata["no_quantum_advantage_claim_flag"] is True
        assert metadata["no_profit_or_latency_superiority_claim_flag"] is True


def test_triage_routes_validator_prints_success_marker():
    completed = subprocess.run(
        [sys.executable, "tools/validate_qtt_master_plan_section_coverage_triage_routes.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "QTT_MASTER_PLAN_SECTION_COVERAGE_TRIAGE_ROUTES_OK"
