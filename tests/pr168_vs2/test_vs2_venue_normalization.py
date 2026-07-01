from .test_support import packet_ids, read_jsonl


def test_venue_normalization_is_candidate_only_not_connector_binding() -> None:
    assert {row["paper_intent_candidate_id"] for row in read_jsonl("venue_norm_intent.jsonl")} == packet_ids()
    for row in read_jsonl("venue_norm_intent.jsonl"):
        assert row["accepted_source_fact_flag"] is False
        assert row["connector_semantic_binding_flag"] is False
        assert row["price_scale"] in {"DOLLARS_0_1", "CENTS", "UNKNOWN_COMPLETION_REQUIRED"}


def test_research_rows_are_candidate_only() -> None:
    for name in ("research_rec.jsonl", "source_coverage.jsonl", "source_intake.jsonl", "source_value_cand.jsonl", "venue_order_semantic_cand.jsonl", "paper_default_cand.jsonl"):
        for row in read_jsonl(name):
            assert row["candidate_only_flag"] is True
            assert row["accepted_source_fact_flag"] is False
            assert row["replay_paper_verification_required"] is True
