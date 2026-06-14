from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_external_dedupe_preserves_candidate_boundary():
    rows = assert_report_rows("PR166_SM2_ExternalDedupe.report.json", 10)
    assert all(row["candidate_provisional_only"] for row in rows)
    assert all(not row["source_truth_accepted"] for row in rows)
