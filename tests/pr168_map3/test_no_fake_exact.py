from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_null_or_placeholder_ids_are_rejected_not_promoted() -> None:
    rows = records("PR168_MAP3_BindReject.report.json")
    assert any(row["rejection_state"] == "PLACEHOLDER_OR_NULL_ID_REJECTED" for row in rows)
    proof = records("PR168_MAP3_BindProof.report.json")
    assert all(row["exact_repaired_existing_binding_created_flag"] is False for row in proof)
