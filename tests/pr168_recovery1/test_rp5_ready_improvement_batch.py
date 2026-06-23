from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_rp5_ready_improvement_batch_carries_stronger_evidence_refs():
    assert_recovery1_valid()
    batch = rows("rp5_ready_improvement_batch")
    handoff = next(row for row in rows("downstream_handoff") if row["handoff_family"] == "RP5_RANK4_QOPT1")

    assert batch
    assert batch[0]["batch_strengthened_flag"] is True
    assert batch[0]["improved_candidate_refs"]
    assert batch[0]["stronger_before_after_evidence_refs"]
    assert batch[0]["rp5_rank4_qopt1_handoff_improved_count"] > 0
    assert handoff["ready_batch_state"] == "IMPROVED_EVIDENCE_BATCH_READY_NON_PROOF"
    assert handoff["improved_candidate_refs"] == batch[0]["improved_candidate_refs"]
    assert handoff["stronger_before_after_evidence_refs"] == batch[0]["stronger_before_after_evidence_refs"]
