from ._helpers import read_jsonl


def test_edge_alpha_feature_surfaces_are_future_numeric_handoffs_not_profit_proof() -> None:
    rows = read_jsonl("edge_feats.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["future_rp5g_numeric_consumer_flag"] is True
        assert row["future_rank4_consumer_flag"] is True
        assert row["future_qopt1_consumer_flag"] is True
        assert row["profit_proof_flag"] is False
        assert row["live_authority_flag"] is False
