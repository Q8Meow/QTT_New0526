from ._helpers import assert_rows_have_contract


def test_regime_memory_keys_are_condition_scoped_not_global_bans() -> None:
    rows = assert_rows_have_contract("regime_keys.jsonl")

    assert all(row["future_mem1_key"] for row in rows)
    assert all(row["market_snapshot_fingerprint"] for row in rows)
    assert all(row["formula_stack_fingerprint"] for row in rows)
    assert all(row["global_ban_flag"] is False for row in rows)

