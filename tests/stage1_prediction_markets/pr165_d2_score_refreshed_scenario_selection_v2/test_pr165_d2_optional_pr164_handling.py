from __future__ import annotations


def test_optional_pr164_is_recorded_as_strengthening_input(pr165_d2_records, pr165_d2_summary):
    assert pr165_d2_summary["optional_pr164_present"] is True
    assert pr165_d2_summary["optional_pr164_rows_consumed"] > 0
    rows = pr165_d2_records["PR165_D2_OptionalInputResolutionLedger.report.json"]
    assert any(row["optional_input_pr"] == "PR164" and row["present_flag"] for row in rows)
