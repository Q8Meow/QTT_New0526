from ._helpers import report, rows


def test_input_consumption_reads_rank4_and_rp5g() -> None:
    assert report("input_consumption.report.json")["missing_required_count"] == 0
    consumed = rows("in_cons.jsonl")
    assert any("pr168_rank4" in row["input_surface_ref"] and row["consumed_flag"] for row in consumed)
    assert any("pr168_rp5g" in row["input_surface_ref"] and row["consumed_flag"] for row in consumed)
    assert rows("rank4_input_refs.jsonl")[0]["rank4_outputs_consumed"] is True
