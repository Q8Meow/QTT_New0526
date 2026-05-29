from .pr161a_test_support import report


def test_pr161a_downstream_agent_consumption_counts_by_lane():
    counts = report("agent_readiness")["agent_consumption_counts_by_lane"]
    assert counts["AGENT_CONSUMABLE_REPLAY_PAPER_NOW"] > 0
    assert counts["AGENT_CONSUMABLE_OPTIMIZER_PREP_NOW"] > 0
    assert counts["AGENT_CONSUMABLE_QUANTUM_ADVISORY_NOW"] > 0

