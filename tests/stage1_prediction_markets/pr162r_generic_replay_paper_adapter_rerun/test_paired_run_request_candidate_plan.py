def test_paired_run_request_candidate_plan(summary, records):
    rows = records("PR162R_PairedReplayPaperRunRequestCandidatePlan.report.json")
    replay = {row["replay_run_request_candidate_id"] for row in records("PR162R_ReplayRunRequestCandidateQueue.report.json")}
    paper = {row["paper_run_request_candidate_id"] for row in records("PR162R_PaperRunRequestCandidateQueue.report.json")}
    assert len(rows) == summary["paired_replay_paper_run_request_candidate_count"]
    assert rows
    for row in rows[:25]:
        assert row["replay_run_request_candidate_ref"] in replay
        assert row["paper_run_request_candidate_ref"] in paper
        assert row["paired_status"] == "PAIRED_FILL_REQUIRED"
