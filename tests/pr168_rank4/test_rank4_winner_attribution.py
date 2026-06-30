from ._helpers import rows


def test_winner_attribution_is_proxy_when_causality_absent() -> None:
    for row in rows("rank_winner_attribution.jsonl"):
        assert row["causal_attribution_claim_flag"] is False
        assert row["attribution_provenance"] == "PROXY_FROM_RANK_COMPONENTS"

