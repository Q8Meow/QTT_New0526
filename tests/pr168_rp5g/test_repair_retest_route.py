from ._helpers import assert_rows_have_contract


def test_repair_retest_never_mutates_formulas() -> None:
    rows = assert_rows_have_contract("repair_retest_route.jsonl")
    assert all(row["formula_mutation_allowed_flag"] is False for row in rows)
    assert all(row["qku_mutation_allowed_flag"] is False for row in rows)

