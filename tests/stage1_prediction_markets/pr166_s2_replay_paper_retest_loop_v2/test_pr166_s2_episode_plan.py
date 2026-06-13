from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_episode_plan_covers_primary_universe():
    rows = assert_report_rows("PR166_S2_EpisodePlan.report.json", 3215)
    assert all(row["episode_id"].startswith("PR166_S2_EPISODE::") for row in rows[:50])
    assert all(row["nonlive_order_intent_ref"].startswith("PR166_S2_ORDER_INTENT::") for row in rows[:50])
