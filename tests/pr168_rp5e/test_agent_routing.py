from ._helpers import read_jsonl


def test_agent_routing_maps_required_agents_to_owned_artifacts() -> None:
    rows = read_jsonl("agent_route.jsonl")
    agents = {row["agent_name"] for row in rows}
    assert {
        "CommanderAgent",
        "StackGeneratorAgent",
        "RiskAgent",
        "QOPTAgent",
        "PaperExecutionAgent",
        "ShadowObservationAgent",
        "LiveDryRunAgent",
    } <= agents
    assert all(row["owned_artifact_refs"] for row in rows)
    assert all(row["no_independent_all_jsonl_scan_flag"] is True for row in rows)
