from ._helpers import read_jsonl


def test_context_universe_is_prediction_market_stage1_and_not_global_scan() -> None:
    rows = read_jsonl("ctx_univ.jsonl")
    assert rows
    for row in rows:
        assert row["market_family"] == "PREDICTION_MARKETS"
        assert row["eligible_qku_ids"]
        assert row["eligible_formula_ids"]
        assert row["full_jsonl_scan_allowed_flag"] is False
        assert row["centralized_resolver_required_flag"] is True
