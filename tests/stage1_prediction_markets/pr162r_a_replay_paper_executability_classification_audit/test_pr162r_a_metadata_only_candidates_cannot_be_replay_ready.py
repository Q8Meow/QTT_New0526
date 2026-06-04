from __future__ import annotations


def test_pr162r_a_metadata_only_candidates_cannot_be_replay_ready(summary, records):
    audit = records("PR162R_A_NoMetadataOnlyReplayReadyAudit.report.json")[0]
    assert summary["metadata_only_replay_ready_count"] == 0
    assert audit["metadata_only_replay_ready_count"] == 0
