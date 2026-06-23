from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_challenger_seeds_are_repair_review_only() -> None:
    assert_rank3_valid()
    seeds = rows("challenger_seed")
    assert seeds
    assert all(row["top_challenger_seed_flag"] is False for row in seeds)
