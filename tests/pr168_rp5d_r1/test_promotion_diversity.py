from ._helpers import read_jsonl


def test_promotion_diversity_is_not_a_hard_blocker() -> None:
    row = read_jsonl("promo_diverse.jsonl")[0]
    assert row["hard_blocker_flag"] is False
    assert row["diversity_available_flag"] is True
