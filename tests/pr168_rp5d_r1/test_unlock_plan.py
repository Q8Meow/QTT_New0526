from ._helpers import read_jsonl


def test_unlock_plans_do_not_mutate_qkus_or_formulas() -> None:
    rows = read_jsonl("unlock_plan.jsonl")
    assert len(rows) == len(read_jsonl("unlock_select.jsonl"))
    assert all(row["formula_mutation_flag"] is False and row["qku_mutation_flag"] is False for row in rows)
