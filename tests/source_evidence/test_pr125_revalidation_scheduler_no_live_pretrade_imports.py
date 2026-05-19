from __future__ import annotations

from pathlib import Path

from tests.source_evidence.pr125_revalidation_scheduler_support import report_and_failures, result


def test_pr125_scheduler_does_not_import_live_pretrade_path_or_allow_hot_path_use():
    report, failures = report_and_failures()
    source_text = Path("src/qtt/source_evidence/revalidation/scheduler.py").read_text(
        encoding="utf-8"
    )

    assert failures == []
    assert "stage1_prediction_markets.live" not in source_text
    assert "import live" not in source_text
    assert report["source_revalidation_runs_in_live_pretrade_path"] is False
    assert all(
        record["live_pretrade_use_allowed_flag"] is False
        for record in result()["source_revalidation_schedule_records"]
    )
