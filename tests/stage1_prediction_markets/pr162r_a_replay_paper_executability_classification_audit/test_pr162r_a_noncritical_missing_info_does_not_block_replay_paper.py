from __future__ import annotations


def test_pr162r_a_noncritical_missing_info_does_not_block_replay_paper(records):
    noncritical = records("PR162R_A_NonCriticalMissingInfoMatrix.report.json")
    classification_by_id = {
        row["candidate_id"]: row
        for row in records("PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json")
    }
    assert noncritical
    for row in noncritical:
        state = classification_by_id[row["candidate_id"]]["primary_executability_state"]
        assert row["does_not_block_replay_paper_flag"] is True
        assert state.startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE"))
