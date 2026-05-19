from __future__ import annotations

from tests.source_evidence.pr124_connector_semantic_binding_support import report_and_failures


def test_pr124_quantum_pathways_remain_metadata_only():
    report, failures = report_and_failures()

    assert failures == []
    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["latency_superiority_claim_created"] is False
    assert report["execution_superiority_claim_created"] is False
