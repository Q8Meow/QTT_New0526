from __future__ import annotations


def test_pr162d_r1_source_quality_priority_not_gate(records):
    sources = records("PR162D_R1_ExternalSourceAcquisitionLedger.report.json")
    non_official = [source for source in sources if not source["official_truth_flag"]]
    assert non_official
    assert all(source["candidate_or_provisional_flag"] for source in non_official)
    assert all(source["replay_paper_route_refs"] for source in non_official)
