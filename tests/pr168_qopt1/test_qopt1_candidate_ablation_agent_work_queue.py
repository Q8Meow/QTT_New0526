from ._helpers import rows


def test_candidate_ablation_and_agent_work_queue_are_actionable() -> None:
    ablation = rows("cand_ablation.jsonl")
    assert ablation
    assert all(row["candidate_marginal_contribution_class"] in {"ESSENTIAL", "HELPFUL", "DIVERSIFYING", "REDUNDANT", "RISKY", "REPAIR_ONLY", "REJECTED"} for row in ablation)
    work = rows("agent_work_queue.jsonl")
    assert work
    assert all(row["orphan_flag"] is False for row in work)
