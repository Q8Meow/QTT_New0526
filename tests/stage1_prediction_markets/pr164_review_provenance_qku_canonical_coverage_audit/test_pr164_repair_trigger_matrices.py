from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_repair_trigger_matrices():
    record = summary()
    assert len(load_records("PR164_PR162BRepairTriggerMatrix.report.json")) == record["pr162b_r_repair_trigger_rows"]
    assert len(load_records("PR164_PR162D_R3RepairTriggerMatrix.report.json")) == record["pr162d_r3_repair_trigger_rows"]
    assert len(load_records("PR164_PR163CRepairTriggerMatrix.report.json")) == record["pr163c_repair_trigger_rows"]
    assert record["pr162d_r3_repair_trigger_rows"] == record["missing_value_fill_tasks_created"]
