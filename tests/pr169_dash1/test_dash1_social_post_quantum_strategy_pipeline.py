from tests.pr169_dash1.conftest import jsonl


def test_social_post_quantum_strategy_routes_through_no_orphan_pipeline() -> None:
    intake = jsonl("owner_research_candidate_intake_contract.generated.jsonl")
    source_families = {row["source_family"] for row in intake}
    assert "social_post_url" in source_families
    assert "quantum_strategy_text" in source_families

    formula_route = jsonl("owner_research_candidate_formula_extraction_route.generated.jsonl")[0]
    qku_route = jsonl("owner_research_candidate_qku_materialization_route.generated.jsonl")[0]
    replay_route = jsonl("owner_research_candidate_replay_paper_route.generated.jsonl")[0]
    promotion_route = jsonl("owner_research_candidate_promotion_route.generated.jsonl")[0]
    assert formula_route["accepted_formula_truth_created"] is False
    assert qku_route["computability_review_required"] is True
    assert replay_route["paper_submit_authority_created"] is False
    assert "execution_router_gate" in promotion_route["required_before_live_canary"]
