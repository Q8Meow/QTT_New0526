from __future__ import annotations


def test_pr162d_r1_no_private_state_secret_order_execution(records, summary):
    audit = records("PR162D_R1_NoPrivateStateSecretAudit.report.json")[0]
    assert summary["private_state_fetch_count"] == 0
    assert summary["order_execution_count"] == 0
    assert audit["private_state_or_secret_materialized_flag"] is False
    assert audit["submit_cancel_reduce_close_order_allowed_flag"] is False
