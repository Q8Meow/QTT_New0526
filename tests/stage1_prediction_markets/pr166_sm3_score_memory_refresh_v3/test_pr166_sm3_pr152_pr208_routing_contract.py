from __future__ import annotations

from .helpers import summary


def test_pr166_sm3_pr152_pr208_routing_contract_is_recorded():
    s = summary()
    assert s["PR152 currentization status"] == "REQUIRED_FOR_GENERATED_REPORTS_AND_VALIDATION_WIRING"
    assert s["PR208 routing status"] == "FULL_VALIDATION_REQUIRED_FOR_VALIDATION_WIRING_AND_GENERATED_REPORTS"
    assert s["timeout_ms"] == 3600000
    assert s["runtime_split_preservation_status"] == "PRESERVED_PR166_FAMILY_SUBGROUP_SPLIT"
