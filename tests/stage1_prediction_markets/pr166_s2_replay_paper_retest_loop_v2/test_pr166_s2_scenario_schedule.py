from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_scenario_schedule_has_stress_buckets():
    rows = assert_report_rows("PR166_S2_ScenarioSchedule.report.json", 10)
    labels = {row["scenario_slice_name"] for row in rows}
    assert {"BASE_REPLAY_PAPER_RETEST", "SPREAD_WIDENING", "LATENCY_SPIKE"}.issubset(labels)
