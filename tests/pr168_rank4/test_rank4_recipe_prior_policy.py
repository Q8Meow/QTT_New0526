from ._helpers import rows


def test_recipe_prior_requires_mem1_for_final_prior() -> None:
    for row in rows("rank_recipe_prior_score.jsonl"):
        assert row["historical_memory_available_flag"] is False
        assert row["MEM1_required_for_final_prior_flag"] is True

