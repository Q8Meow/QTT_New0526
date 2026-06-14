from __future__ import annotations

from .helpers import report_rows


def test_pr166_sf_r2_positive_conversions_have_retest_proof_not_profit():
    rows = report_rows("PR166_SF_R2_PosConversion.report.json")
    assert rows
    assert all(row["conversion_status"] == "REPAIRED_AND_RETESTED_POSITIVE" for row in rows)
    assert all(row["retested_net_edge_after_costs"] > 0 for row in rows)
    assert all(row["converted_positive_label"] == "REPAIRED_REPLAY_PAPER_POSITIVE_EDGE_NOT_PROFIT_EVIDENCE" for row in rows)
    assert all(row["preview_only_conversion"] is False for row in rows)
    assert all(row["profit_evidence_count"] == 0 for row in rows)
