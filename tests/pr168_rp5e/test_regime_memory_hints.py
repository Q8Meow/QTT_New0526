from ._helpers import read_jsonl


def test_regime_memory_hints_are_condition_scoped_and_never_global_bans() -> None:
    rows = read_jsonl("regime_mem.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["future_mem1_key"]
        assert row["formula_stack_fingerprint"]
        assert row["condition_scoped_cooldown_hint"]
        assert row["global_ban_flag"] is False
