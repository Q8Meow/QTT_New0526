from __future__ import annotations

from ._helpers import report, rows


def test_quantum_compatibility_is_structural_with_classical_fallback() -> None:
    qobj = rows("rp5d_qobj_constraint_ledger.jsonl")
    compat = rows("rp5d_quantum_compat.jsonl")
    run = report("rp5d_run_receipt.report.json")

    assert len(qobj) == run["quantum_materialization_row_count"]
    assert len(compat) == run["quantum_compatibility_row_count"]
    assert all(row["backend_execution_flag"] is False for row in qobj)
    assert all(row["quantum_advantage_claim_flag"] is False for row in qobj)
    assert all(row["classical_fallback_required_flag"] is True for row in compat)
