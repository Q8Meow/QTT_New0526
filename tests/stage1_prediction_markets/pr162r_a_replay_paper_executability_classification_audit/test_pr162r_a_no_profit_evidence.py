from __future__ import annotations


def test_pr162r_a_no_profit_evidence(summary, payloads):
    assert summary["profit_evidence_count"] == 0
    for payload in payloads.values():
        for row in payload["records"]:
            assert row.get("profit_evidence_claim_flag") is not True
