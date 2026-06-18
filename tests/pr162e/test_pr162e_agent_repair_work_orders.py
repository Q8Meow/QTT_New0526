from tests.pr162e.helpers import records


def test_agent_repair_work_orders_cover_negative_candidates():
    repair_orders = records("PR162E_AgentRepairWorkOrders.report.json")
    inventory = records("PR162E_NegativeReplayPaperCandidateInventory.report.json")
    assert len(repair_orders) == len(inventory)
    assert all(row["owning_agent"] == "Negative Candidate Repair Agent" for row in repair_orders)
