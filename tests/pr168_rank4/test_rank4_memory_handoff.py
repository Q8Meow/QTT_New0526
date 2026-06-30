from ._helpers import rows


def test_memory_handoff_is_prior_only() -> None:
    for row in rows("rank_memory_recipe_handoff.jsonl"):
        assert row["memory_prior_only_flag"] is True
        assert row["current_profit_proof_flag"] is False
        assert row["durable_MEM1_storage_created_flag"] is False

