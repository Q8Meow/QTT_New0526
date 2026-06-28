from ._helpers import read_json, read_jsonl


def test_reading_receipts_cover_required_baseline_inputs() -> None:
    read_rows = read_jsonl("read_rec.jsonl")
    surfaces = {row["surface_family"] for row in read_rows}

    assert "RP5C_IMMUTABLE_LIBRARY" in surfaces
    assert "VS1_VERTICAL_SLICE" in surfaces
    assert "RP5D_EXECUTABILITY_OVERLAY" in surfaces
    assert "PR165_D2_AGENT_DUTY" in surfaces
    assert all(row["exists_flag"] is True for row in read_rows)

    receipt = read_json("run_receipt.report.json")
    assert receipt["universal_coverage_row_count"] == 10189
    assert receipt["schedulable_after_adapter_count"] == 52
    assert receipt["adapter_queue_row_count"] == 35877
