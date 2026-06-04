from __future__ import annotations


def test_pr162r_a_partial_executable_candidates_are_replay_paper_eligible(summary, records):
    partial = records("PR162R_A_PartialReplayPaperCandidateQueue.report.json")
    adapter = {row["candidate_id"]: row for row in records("PR162R_A_PR162RAdapterRerunInputPack.report.json")}
    assert len(partial) == summary["partial_executable_replay_and_paper_ready_count"]
    assert partial
    assert all(adapter[row["candidate_id"]]["replay_input_eligible_flag"] for row in partial)
    assert all(adapter[row["candidate_id"]]["paper_input_eligible_flag"] for row in partial)
    assert all(row["live_ready_flag"] is False for row in partial)
