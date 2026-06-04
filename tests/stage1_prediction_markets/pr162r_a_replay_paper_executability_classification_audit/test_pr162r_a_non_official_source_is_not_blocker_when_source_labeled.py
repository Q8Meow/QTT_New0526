from __future__ import annotations


def test_pr162r_a_non_official_source_is_not_blocker_when_source_labeled(records):
    rows = records("PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json")
    nonofficial = [row for row in rows if "NON_OFFICIAL_SOURCE" in row["secondary_tags"]]
    assert nonofficial
    assert all(row["primary_executability_state"].startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE")) for row in nonofficial)
