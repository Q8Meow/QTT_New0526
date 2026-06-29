from ._helpers import assert_rows_have_contract


def test_agent_routing_and_consumption_include_downstream_future_consumers() -> None:
    route = assert_rows_have_contract("agent_route.jsonl")
    consume = assert_rows_have_contract("agent_consume.jsonl")

    route_consumers = {consumer for row in route for consumer in row["consumer_refs"]}
    assert {"RP5G", "RANK4", "QOPT1", "VS2", "MEM1", "PAPER-LOOP"} <= route_consumers
    assert any("trade_seed.jsonl" in " ".join(row["consumed_artifact_refs"]) for row in consume)
    assert all(row["orphan_flag"] is False for row in consume)
