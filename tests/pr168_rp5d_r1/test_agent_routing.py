from ._helpers import read_jsonl


def test_agent_routing_uses_pr165d2_refs() -> None:
    rows = read_jsonl("agent_route.jsonl")
    assert rows
    assert all(row["route_complete_flag"] for row in rows)
    assert any("PR165_D2" in ref for row in rows for ref in row["agent_duty_source_refs"])
