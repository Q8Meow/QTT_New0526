from __future__ import annotations

from .helpers import summary


def test_pr166_s2_pr152_pr208_summary_contract_present():
    s = summary()
    assert s["pr152_currentization_required"] is True
    assert s["pr208_routing_mode"] in {"FULL_VALIDATION_REQUIRED", "PENDING_FINAL_VALIDATION"}
    assert s["timeout_ms_3600000_usage"] is True
