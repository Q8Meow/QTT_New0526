from __future__ import annotations

from ._helpers import report


def test_vs1_run_receipt_proves_no_scope_drift_or_execution_runtime():
    run = report("vs1_run_receipt.report.json")

    assert run["paper_submit_count"] == 0
    assert run["live_submit_count"] == 0
    assert run["connector_runtime_count"] == 0
    assert run["private_state_fetch_count"] == 0
    assert run["cash_runtime_count"] == 0
    assert run["venue_api_call_count"] == 0
    assert run["source_fact_acceptance_count"] == 0
    assert run["quantum_backend_execution_count"] == 0
    assert run["quantum_advantage_claim_count"] == 0
    assert run["qtt_sha_authority_count"] == 0
    assert run["atomicrows_bundle_sha_reference_count"] == 0
