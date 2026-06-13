from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_external_signals_are_candidate_provisional():
    rows = assert_report_rows("PR166_S2_ExternalSignalRegistry.report.json", 10)
    assert all(row["source_acceptance_lane"] == "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH" for row in rows)
    assert all(row["source_truth_acceptance_allowed_in_this_pr"] is False for row in rows)
