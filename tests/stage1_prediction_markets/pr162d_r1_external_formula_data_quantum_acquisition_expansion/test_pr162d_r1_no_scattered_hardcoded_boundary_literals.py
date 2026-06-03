from __future__ import annotations


def test_pr162d_r1_no_scattered_hardcoded_boundary_literals(records):
    audit = records("PR162D_R1_NoScatteredHardcodedBoundaryLiteralAudit.report.json")[0]
    assert audit["scattered_hardcoded_boundary_literal_count"] == 0
