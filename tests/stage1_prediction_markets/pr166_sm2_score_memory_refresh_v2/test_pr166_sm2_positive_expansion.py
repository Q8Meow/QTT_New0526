from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_positive_expansions_are_candidates_only():
    rows = assert_report_rows("PR166_SM2_PosExpansion.report.json", 32)
    assert all(row["positive_expansion_label"] == "POSITIVE_FAMILY_EXPANSION_CANDIDATE_FOR_REPLAY_PAPER" for row in rows)
    assert all(not row["counts_as_positive_replay_paper_result"] for row in rows)
