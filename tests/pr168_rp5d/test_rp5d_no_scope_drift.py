from __future__ import annotations

from ._helpers import report, rows


def test_no_scope_drift_hard_zero_counts_and_proof_rows() -> None:
    run = report("rp5d_run_receipt.report.json")
    proof = rows("rp5d_no_mutation_proof.jsonl")
    hard_zero = [
        "formula_mutation_count",
        "formula_deletion_count",
        "qku_deletion_count",
        "global_formula_ban_count",
        "global_qku_ban_count",
        "stack_generation_count",
        "trade_simulation_count",
        "ranking_count",
        "champion_selection_count",
        "order_variable_optimization_count",
        "paper_submit_count",
        "live_submit_count",
        "connector_runtime_count",
        "source_fact_acceptance_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "qtt_sha_authority_count",
        "qtt_generated_sha_file_count",
        "atomicrows_bundle_sha_reference_count",
    ]

    assert proof
    for field in hard_zero:
        assert run[field] == 0, field
    assert all(row["formula_mutation_flag"] is False for row in proof)
