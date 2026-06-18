from tests.pr162e.helpers import records


def test_negative_repair_factory_covers_inventory():
    inventory = records("PR162E_NegativeReplayPaperCandidateInventory.report.json")
    plans = records("PR162E_NegativeCandidateRepairPlan.report.json")
    assert inventory
    assert len(plans) == len(inventory)
    assert all(row["repair_actions_applied"] for row in plans)
