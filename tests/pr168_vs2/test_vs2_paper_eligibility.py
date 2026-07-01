from .test_support import read_jsonl


def test_no_deferred_state_is_ready_now() -> None:
    for row in read_jsonl("paper_readiness.jsonl"):
        if row["paper_readiness_state"].startswith("PAPER_INTENT_DEFERRED_"):
            assert row["paper_loop_candidate_ready_now_flag"] is False
            assert row["paper_submit_authority_created_flag"] is False


def test_no_ready_after_wording_is_generated() -> None:
    for name in ("vs2_candidate_paper_elig.jsonl", "packet_decision_trace.jsonl", "paper_readiness.jsonl"):
        text = "\n".join(str(row) for row in read_jsonl(name))
        assert "READY_AFTER_" not in text
