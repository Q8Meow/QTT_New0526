from __future__ import annotations

from pathlib import Path

from tests.source_evidence.pr125_revalidation_scheduler_support import report_and_failures, result


def test_pr125_scheduler_has_no_source_retrieval_or_network_io():
    report, failures = report_and_failures()
    source_text = Path("src/qtt/source_evidence/revalidation/scheduler.py").read_text(
        encoding="utf-8"
    )

    assert failures == []
    assert "requests" not in source_text
    assert "urllib" not in source_text
    assert "socket" not in source_text
    assert report["network_io_violation_count"] == 0
    assert report["source_retrieval_violation_count"] == 0
    assert report["source_acceptance_violation_count"] == 0
    assert all(
        record["network_io_allowed_flag"] is False
        and record["source_retrieval_allowed_flag"] is False
        and record["source_acceptance_allowed_flag"] is False
        for record in result()["source_revalidation_schedule_records"]
    )
