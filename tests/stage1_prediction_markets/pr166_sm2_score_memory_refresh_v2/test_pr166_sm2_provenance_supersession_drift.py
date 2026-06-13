from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_provenance_supersession_and_drift_are_connected():
    assert_report_rows("PR166_SM2_ProvenanceLedger.report.json", 3215)
    supersession = assert_report_rows("PR166_SM2_MemorySupersession.report.json", 3215)
    drift = assert_report_rows("PR166_SM2_ModelDriftLedger.report.json", 3215)
    assert all(row["stale_memory_downweighted"] for row in drift[:100])
    assert all(not row["regime_incompatible_memory_globalized"] for row in supersession[:100])
