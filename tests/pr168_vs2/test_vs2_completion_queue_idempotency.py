from .test_support import read_jsonl


def test_deferred_packets_have_precise_completion_rows() -> None:
    deferred = {
        row["paper_intent_candidate_id"]
        for row in read_jsonl("paper_readiness.jsonl")
        if row["paper_readiness_state"].startswith("PAPER_INTENT_DEFERRED_")
    }
    completion = read_jsonl("packet_completion_queue.jsonl")
    assert deferred
    assert deferred.issubset({row["paper_intent_candidate_id"] for row in completion})
    assert all(row["profit_forcing_flag"] is False for row in completion)
    assert all(row["qku_mutation_flag"] is False for row in completion)


def test_idempotency_keys_are_non_sha_tuples() -> None:
    for row in read_jsonl("packet_idempotency_key.jsonl"):
        assert row["sha_or_hash_authority_flag"] is False
        assert row["deterministic_non_sha_tuple"]
        assert "sha" not in row["packet_idempotency_key"].lower()
