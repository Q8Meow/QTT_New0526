from ._helpers import assert_rows_have_contract


def test_agent_routes_non_orphan() -> None:
    rows = assert_rows_have_contract("agent_route.jsonl")
    assert all(row["orphan_flag"] is False for row in rows)

