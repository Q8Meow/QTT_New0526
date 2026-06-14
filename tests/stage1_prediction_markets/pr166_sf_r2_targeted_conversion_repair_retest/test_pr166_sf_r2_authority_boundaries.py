from __future__ import annotations

from .helpers import report_rows
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest.authority import ZERO_AUTHORITY_KEYS


def test_pr166_sf_r2_authority_counts_are_zero():
    rows = report_rows("PR166_SF_R2_AuthorityAudit.report.json")
    assert rows[0]["authority_audit_status"] == "PASS"
    for key in ZERO_AUTHORITY_KEYS:
        assert rows[0][key] == 0
