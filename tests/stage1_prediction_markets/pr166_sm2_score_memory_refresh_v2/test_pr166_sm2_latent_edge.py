from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_latent_edge_requires_retest_for_negatives():
    rows = assert_report_rows("PR166_SM2_LatentEdgeLedger.report.json", 3215)
    assert any(row["latent_edge_requires_retest"] for row in rows)
