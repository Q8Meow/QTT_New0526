from __future__ import annotations

from ._helpers import rows


def test_latency_hot_path_readiness_is_future_only() -> None:
    hot_path = rows("rp5d_hot_path_readiness.jsonl")

    assert hot_path
    assert all(row["readiness_family"] == "hot_path" for row in hot_path)
    assert all(row["no_live_authority_created_flag"] is True for row in hot_path)
    assert any(row["adapter_queue_refs"] for row in hot_path)
