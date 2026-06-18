from tests.pr162e.helpers import records


def test_agent_work_orders_cover_plugins():
    rows = records("PR162E_AgentWorkOrders.report.json")
    assert len(rows) == 559
    assert all(row["owning_agent"] for row in rows)
