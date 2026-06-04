from __future__ import annotations


def test_pr162r_a_no_live_order_authority(summary, payloads):
    assert summary["live_order_authority_count"] == 0
    for payload in payloads.values():
        for row in payload["records"]:
            assert row.get("live_order_authority") is False
