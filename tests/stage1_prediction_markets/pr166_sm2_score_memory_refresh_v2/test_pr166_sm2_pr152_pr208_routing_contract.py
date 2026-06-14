from __future__ import annotations

from .helpers import summary


def test_pr166_sm2_pr152_pr208_summary_contract():
    data = summary()
    assert data["pr152_currentization_required"] is True
    assert data["pr208_routing_mode"] == "FULL_VALIDATION_REQUIRED_DUE_VALIDATION_INFRASTRUCTURE_AND_GENERATED_REPORT_CHANGES"
