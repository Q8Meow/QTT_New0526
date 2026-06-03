from __future__ import annotations


def test_pr162d_r1_accepts_non_official_candidates_to_replay_paper(records):
    sources = records("PR162D_R1_ExternalSourceAcquisitionLedger.report.json")
    non_official = [source for source in sources if not source["official_truth_flag"]]
    assert len(non_official) >= 30
    assert all("NON_OFFICIAL_REPLAY_PAPER_CANDIDATE" in source["candidate_labels"] for source in non_official)
    assert all("NOT_OFFICIAL_EXTERNAL_FACT" in source["candidate_labels"] for source in non_official)
