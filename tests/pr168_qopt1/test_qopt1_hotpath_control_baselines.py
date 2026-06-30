from ._helpers import rows


def test_hotpath_coldpath_and_controls_are_non_authority() -> None:
    assert rows("hotpath_batch.jsonl")[0]["hotpath_classification"] == "HOT_PATH_CANDIDATE"
    assert rows("coldpath_route.jsonl")[0]["current_order_authority_flag"] is False
    assert rows("random_base.jsonl")[0]["deterministic_seed_or_no_random_flag"] == "NO_RANDOMNESS_STABLE_LEXICAL_CONTROL"
