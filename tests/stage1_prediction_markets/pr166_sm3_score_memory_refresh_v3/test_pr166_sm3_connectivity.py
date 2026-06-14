from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_connectivity_reports_cover_files_values_and_provenance():
    assert_report_contract("PR166_SM3_FileConnAudit.report.json", 109)
    assert_report_contract("PR166_SM3_ValueConnAudit.report.json", 109)
    assert_report_contract("PR166_SM3_ProvenanceLedger.report.json", 96)
