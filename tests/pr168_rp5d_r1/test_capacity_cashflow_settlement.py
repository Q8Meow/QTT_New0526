from ._helpers import read_jsonl


def test_capacity_cashflow_settlement_ledgers_exist() -> None:
    assert read_jsonl("capacity_ready.jsonl")
    assert read_jsonl("cash_settle.jsonl")
