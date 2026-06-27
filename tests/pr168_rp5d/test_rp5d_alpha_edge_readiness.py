from __future__ import annotations

from ._helpers import rows


def test_alpha_readiness_routes_future_edge_capture_without_pnl_forcing() -> None:
    alpha = rows("rp5d_alpha_readiness.jsonl")

    assert alpha
    assert all(row["readiness_family"] == "alpha_edge" for row in alpha)
    assert all("RP5G" in row["future_consumer_pr_refs"] for row in alpha)
    assert any(row["adapter_queue_refs"] for row in alpha)
