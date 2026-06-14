from __future__ import annotations

from .helpers import report_rows


def test_pr166_sf_r2_repair_universe_covers_all_3213_negatives():
    rows = report_rows("PR166_SF_R2_RepairUniverse.report.json")
    assert len(rows) == 3213
    assert len({row["candidate_packet_id"] for row in rows}) == 3213
    assert all(row["conversion_tier"].startswith("TIER_") for row in rows)
