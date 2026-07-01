from .test_support import read_jsonl


def test_drift_cooldown_retest_are_context_scoped() -> None:
    assert read_jsonl("drift_monitor.jsonl")
    assert read_jsonl("cooldown_policy.jsonl")
    assert read_jsonl("retest_queue.jsonl")
    for row in read_jsonl("cooldown_policy.jsonl") + read_jsonl("cooldown_state.jsonl"):
        assert row["cooldown_scope_key"]
        assert row["global_formula_ban_flag"] is False
        assert row["global_qku_ban_flag"] is False
        assert row["retest_required"] is True
