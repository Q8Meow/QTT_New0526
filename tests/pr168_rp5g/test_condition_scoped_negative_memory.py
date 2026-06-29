from ._helpers import assert_rows_have_contract


def test_negative_memory_is_condition_scoped() -> None:
    rows = assert_rows_have_contract("negative_memory_hint.jsonl")
    assert all(row["condition_scoped_only_flag"] is True for row in rows)
    assert all(row["global_formula_ban_flag"] is False for row in rows)

