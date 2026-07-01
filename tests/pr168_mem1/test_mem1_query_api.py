from src.qtt.memory.pr168_mem1.query_api import (
    get_failure_memories_for_context,
    get_recipe_prior,
    get_top_recipes_for_context,
    record_paper_outcome,
)

from .test_support import ARTIFACT_DIR, read_jsonl


def test_query_api_returns_non_authority_memory_priors() -> None:
    top = get_top_recipes_for_context("sample", 5, ARTIFACT_DIR)
    assert top
    assert top[0]["current_profit_proof_flag"] is False
    assert top[0]["replay_paper_revalidation_required"] is True
    prior = get_recipe_prior(read_jsonl("winning_recipe.jsonl")[0]["recipe_id"], "sample", ARTIFACT_DIR)
    assert prior["state"] == "PENDING_REPLAY_PAPER_REVALIDATION"
    assert get_failure_memories_for_context("sample", 5, ARTIFACT_DIR)
    assert record_paper_outcome("MEM1_RECIPE_0001")["state"] == "PENDING_RECEIPT_FAIL_CLOSED"
