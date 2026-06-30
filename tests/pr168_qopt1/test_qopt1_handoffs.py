from ._helpers import rows


def test_downstream_handoffs_are_non_authority() -> None:
    vs2 = rows("vs2_handoff.jsonl")[0]
    assert vs2["eligibility_for_future_paper_intent"] == "CANDIDATE_ONLY"
    for filename in ("vs2_handoff.jsonl", "paper_handoff.jsonl", "live_dry_handoff.jsonl", "shadow_handoff.jsonl"):
        for row in rows(filename):
            assert row["paper_order_intent_created_flag"] is False
            assert row["live_authority_created_flag"] is False
            assert row["buy_sell_open_close_logic_created_flag"] is False
