from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_agent_dag_rows_have_owners_and_consumers() -> None:
    rows = records("PR168_MAP3_AgentDAG.report.json")
    assert rows
    assert all(row["owning_agent"] for row in rows)
    assert all(row["consumer_agents"] for row in rows)
