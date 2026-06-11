from __future__ import annotations


def test_pr152_and_pr208_decisions_are_recorded(pr165_d2_summary):
    assert pr165_d2_summary["pr152_currentization_required"] is True
    assert pr165_d2_summary["pr152_currentization_reason"] == "GENERATED_REPORTS_AND_VALIDATION_ROUTING_CHANGED"
    assert pr165_d2_summary["full_validation_required"] is True
    assert pr165_d2_summary["pr208_reduced_mode_used"] is False
