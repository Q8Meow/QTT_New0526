from __future__ import annotations

from ._helpers import rows


def test_vs1_quantum_structural_readiness_is_metadata_only_with_classical_fallbacks():
    readiness = rows("quantum_structural_readiness_receipts.jsonl")

    assert readiness
    assert all(row["quantum_backend_execution_flag"] is False for row in readiness)
    assert all(row["quantum_advantage_claim_flag"] is False for row in readiness)
    assert all(row["classical_fallback_optimizer_refs"] for row in readiness)
    assert any(row["cqm_eligible_flag"] is True for row in readiness)
