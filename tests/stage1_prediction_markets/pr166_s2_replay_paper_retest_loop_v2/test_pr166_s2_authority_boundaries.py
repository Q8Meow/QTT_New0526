from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_authority_boundary_zero_counts():
    row = assert_report_rows("PR166_S2_AuthorityBoundaryAudit.report.json", 1)[0]
    assert summary()["authority_violation_count"] == 0
    for key, value in row.items():
        if key.endswith("_count"):
            assert value == 0
