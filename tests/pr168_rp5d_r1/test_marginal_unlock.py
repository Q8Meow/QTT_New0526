from ._helpers import read_jsonl


def test_marginal_unlock_is_preference_only() -> None:
    rows = read_jsonl("marg_unlock.jsonl")
    assert len(rows) == 52
    assert all(row["selection_preference_only_flag"] is True for row in rows)
    assert all(row["promotion_blocker_flag"] is False for row in rows)
