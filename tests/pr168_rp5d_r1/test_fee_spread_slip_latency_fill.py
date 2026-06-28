from ._helpers import read_jsonl


def test_execution_cost_component_ledgers_exist() -> None:
    for name in ("fee_ready.jsonl", "spread_ready.jsonl", "slip_ready.jsonl", "lat_ready.jsonl", "fill_ready.jsonl"):
        assert read_jsonl(name), name
