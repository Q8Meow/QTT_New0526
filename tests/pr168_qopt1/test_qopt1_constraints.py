from ._helpers import rows


def test_hard_constraints_and_checks_exist() -> None:
    constraints = rows("constraints.jsonl")
    assert any(row["constraint_family"] == "min_LCB_constraint" for row in constraints)
    assert any(row["constraint_family"] == "no_live_no_paper_order_authority_constraint" for row in constraints)
    assert any(row["hard_constraint_pass_flag"] is True for row in rows("constraint_check.jsonl"))
