from ._helpers import read_jsonl


def test_agent_consumption_registry_has_future_consumer_refs_without_authority() -> None:
    rows = read_jsonl("agent_consume.jsonl")
    assert rows
    consumers = {row["consumer_agent"] for row in rows}
    assert {"RankerAgent", "TradePlanSimulationAgent", "QOPTAgent", "MemoryAgent"} <= consumers
    assert all(row["paper_authority_flag"] is False for row in rows)
    assert all(row["live_authority_flag"] is False for row in rows)
