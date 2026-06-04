from __future__ import annotations


def test_pr162r_a_consumes_pr162d_r1_outputs_not_rebuild(summary, records):
    consumption = records("PR162R_A_PR162DR1ConsumptionAudit.report.json")
    r1_rows = [row for row in consumption if row["input_ref"].startswith("docs/master_plan/generated/PR162D_R1")]
    assert summary["pr162d_r1_consumed_not_rebuilt_flag"] is True
    assert r1_rows
    assert all(row["present_flag"] for row in r1_rows)
    assert all(row["consumption_mode"] == "CONSUME_PR162D_R1_OUTPUT_NO_REBUILD" for row in r1_rows)
