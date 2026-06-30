from .test_support import packet_ids, read_jsonl


def test_paper_loop_packets_cover_all_candidates_without_submit() -> None:
    for row in read_jsonl("paper_loop_packet.jsonl"):
        assert row["paper_intent_candidate_id"] in packet_ids()
        assert row["paper_loop_required_before_any_paper_execution_flag"] is True
        assert row["paper_submit_created_flag"] is False
        assert row["qopt1_batch_ref"]
        assert row["rank4_ref"]
        assert row["rp5g_ref"]


def test_revalidation_requirements_are_explicit() -> None:
    for row in read_jsonl("paper_loop_revalidation_req.jsonl"):
        assert row["revalidate_market_snapshot_before_paper_run"] is True
        assert row["revalidate_no_trade_margin_before_paper_run"] is True
        assert row["revalidate_stale_TTL_before_paper_run"] is True
