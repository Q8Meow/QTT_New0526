from __future__ import annotations


def test_authority_boundaries_remain_zero(records, summary):
    for field in (
        "live_order_authority_count",
        "profit_evidence_count",
        "private_state_fetch_count",
        "replay_execution_count",
        "paper_execution_count",
        "result_packet_created_count",
        "qtt_sha_freeze_checksum_authority_count",
        "qtt_generated_sha_count",
        "atomicrows_bundle_mutation_count",
        "protected_atomicrows_hash_sha_artifact_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
    ):
        assert summary[field] == 0
    audit = records("PR162D_R2A_NoLiveOrderProfitReplayExecutionAudit.report.json")[0]
    assert audit["replay_execution_count"] == 0
    assert audit["paper_execution_count"] == 0
    assert audit["result_packet_created_count"] == 0
    assert audit["live_order_authority"] is False
