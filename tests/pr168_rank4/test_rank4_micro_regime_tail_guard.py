from ._helpers import rows


def test_micro_regime_and_tail_guard_are_non_authority() -> None:
    for row in rows("rank_micro_regime.jsonl"):
        assert row["microstructure_regime_key"]
    for row in rows("rank_tail_guard.jsonl"):
        assert row["realized_pnl_claim_flag"] is False
        assert row["live_stage_revalidation_required_flag"] is True

