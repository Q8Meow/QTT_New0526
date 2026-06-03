from __future__ import annotations


def test_pr162d_r1_consumes_pr162d_outputs_not_rebuild(summary, records):
    consumption = records("PR162D_R1_PR162DConsumptionAudit.report.json")
    pr162d_rows = [row for row in consumption if row["input_ref"].startswith("docs/master_plan/generated/PR162D")]
    assert summary["pr162d_consumed_not_rebuilt_flag"] is True
    assert pr162d_rows
    assert all(row["present_flag"] for row in pr162d_rows)
    assert all(row["consumption_mode"] == "CONSUME_EXISTING_OUTPUT_NO_REBUILD" for row in pr162d_rows)
