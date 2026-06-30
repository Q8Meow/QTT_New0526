from ._helpers import rows


def test_decision_intelligence_is_optimization_driven() -> None:
    for row in rows("rank_decision_intel_map.jsonl"):
        assert row["optimization_driven_flag"] is True
        assert row["LLM_may_create_rank_proof_flag"] is False

