from ._helpers import assert_rows_have_contract


def test_learning_hooks_and_context_similarity_are_future_consumed() -> None:
    hooks = assert_rows_have_contract("learning_hooks.jsonl")
    keys = assert_rows_have_contract("context_similarity_keys.jsonl")

    assert all("MEM1" in row["future_outcome_consumer_refs"] for row in hooks)
    assert all("AGENT-ORCH1" in row["future_outcome_consumer_refs"] for row in hooks)
    assert all(row["similarity_key"] for row in keys)
    assert all("MEM1" in row["consumer_agents"] for row in keys)
