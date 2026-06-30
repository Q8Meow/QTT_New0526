from ._helpers import rows


def test_memory_is_prior_only_and_mem1_storage_future_only() -> None:
    for row in rows("memory_prior_batch.jsonl"):
        assert row["current_profit_proof_flag"] is False
        assert row["durable_MEM1_storage_created_flag"] is False
    handoff = rows("mem1_handoff.jsonl")[0]
    assert handoff["future_MEM1_storage_required_flag"] is True
    assert handoff["durable_MEM1_storage_created_flag"] is False
