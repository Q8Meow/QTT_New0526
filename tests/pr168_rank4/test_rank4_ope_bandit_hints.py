from ._helpers import rows


def test_ope_bandit_are_hints_only() -> None:
    for row in rows("rank_bandit_alloc_hint.jsonl"):
        assert row["bandit_runtime_policy_created_flag"] is False
        assert row["live_policy_control_created_flag"] is False
    for row in rows("rank_ope_hint.jsonl"):
        assert row["off_policy_evaluation_as_profit_proof_flag"] is False

