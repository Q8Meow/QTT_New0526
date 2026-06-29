from ._helpers import assert_rows_have_contract


def test_qku_formula_compute_receipts_exist() -> None:
    assert_rows_have_contract("qku_comp.jsonl")
    formula = assert_rows_have_contract("formula_comp.jsonl")
    assert all(row["compute_status"] == "COMPUTED" for row in formula)

