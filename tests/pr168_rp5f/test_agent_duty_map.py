from ._helpers import assert_rows_have_contract


def test_agent_duty_map_contains_owner_and_consumer_agents() -> None:
    rows = assert_rows_have_contract("agent_duty_map.jsonl")
    names = {row["agent_name"] for row in rows}

    assert "TradeTargetScoutAgent" in names
    assert "OrderVariableAgent" in names
    assert "RiskAgent" in names
    assert "QOPTAgent" in names
    assert any(row["owner_agent_flag"] for row in rows)
    assert any(row["consumer_agent_flag"] for row in rows)
    assert all(row["forbidden_authority_flags"] for row in rows)

