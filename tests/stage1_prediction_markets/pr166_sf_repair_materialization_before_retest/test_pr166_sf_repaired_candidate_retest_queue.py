from .conftest import assert_rows


def test_pr166_sf_repaired_candidate_queue_has_pr166_s2_handoff(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairedCandidateRetestQueue.report.json")
    ready = [row for row in rows if row["ready_for_replay_paper_retest_flag"]]
    assert len(ready) == pr166_sf_records["PR166_SF_FinalSummary.report.json"][0]["repaired_retest_ready_rows"]
    assert ready
    assert all("PR166-S2" in row["downstream_pr_refs"] for row in ready[:50])
