from __future__ import annotations

from ._helpers import rows


def test_vs1_quantum_encoding_has_no_backend_execution_or_backend_specific_values():
    encodings = rows("trade_plan_quantum_encoding_receipts.jsonl")

    assert encodings
    assert all(row["quantum_backend_execution_flag"] is False for row in encodings)
    assert all(row["quantum_advantage_claim_flag"] is False for row in encodings)
    assert all(row["anneal_time_policy"] == "NOT_SET_IN_VS1" for row in encodings)
    assert all(row["num_reads_policy"] == "NOT_SET_IN_VS1" for row in encodings)
    assert all(row["shots_policy"] == "NOT_SET_IN_VS1" for row in encodings)
    assert all(row["classical_fallback_optimizer_refs"] for row in encodings)
