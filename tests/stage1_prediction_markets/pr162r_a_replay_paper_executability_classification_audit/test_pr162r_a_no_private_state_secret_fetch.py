from __future__ import annotations


def test_pr162r_a_no_private_state_secret_fetch(summary, records):
    audit = records("PR162R_A_NoPrivateStateSecretAudit.report.json")[0]
    assert summary["private_state_fetch_count"] == 0
    assert audit["private_state_fetch_count"] == 0
