from __future__ import annotations

from .helpers import payload
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.enums import FORBIDDEN_STATUS_VALUES


def test_pr166_sm2_no_bad_status_tokens_outside_explicit_audit_field():
    audit = payload("PR166_SM2_StatusDriftAudit.report.json")
    assert audit["records"][0]["unauthorized_token_occurrence_count"] == 0
    checked = set(audit["records"][0]["forbidden_scope_audit_tokens_checked"])
    assert checked == FORBIDDEN_STATUS_VALUES
