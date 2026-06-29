from ._helpers import rows


def test_similarity_keys_exist_for_contexts() -> None:
    assert rows("rank_context_signature.jsonl")
    for row in rows("rank_similarity_key.jsonl"):
        assert row["formula_stack_fingerprint"]
        assert row["spread_depth_liquidity_key"]

