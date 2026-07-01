from .test_support import read_jsonl


def test_winning_recipe_is_trade_plan_prior_not_profit_proof() -> None:
    for row in read_jsonl("winning_recipe.jsonl"):
        assert row["source_trade_plan_candidate_id"]
        assert row["qku_refs"]
        assert row["formula_refs"]
        assert row["numeric_evidence_refs"]
        assert row["memory_prior_only_flag"] is True
        assert row["current_profit_proof_flag"] is False
        assert row["replay_paper_revalidation_required"] is True
