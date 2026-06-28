from ._helpers import read_jsonl


def test_formula_to_pnl_rows_exist() -> None:
    assert read_jsonl("pnl_map.jsonl")
