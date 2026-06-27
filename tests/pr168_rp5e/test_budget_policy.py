from ._helpers import read_jsonl


def test_budget_policy_prevents_full_cartesian_generation() -> None:
    rows = read_jsonl("budget.jsonl")
    assert rows
    for row in rows:
        assert row["full_cartesian_generation_allowed_flag"] is False
        assert row["persistent_full_stack_universe_allowed_flag"] is False
        assert row["candidate_count_target"] <= 1000
