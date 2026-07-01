from .test_support import read_json, read_jsonl


def test_required_inputs_are_read_and_consumed() -> None:
    rows = read_jsonl("read_rec.jsonl")
    assert rows
    assert all(row["read_status"] == "READ_UTF8" for row in rows)
    report = read_json("input_consumption.report.json")
    assert report["qopt1_consumed_file_count"] > 0
    assert report["rank4_consumed_file_count"] > 0
    assert report["rp5g_consumed_file_count"] > 0


def test_qopt1_rank4_rp5g_ref_ledgers_exist() -> None:
    assert read_jsonl("qopt1_input_refs.jsonl")
    assert read_jsonl("rank4_input_refs.jsonl")
    assert read_jsonl("rp5g_input_refs.jsonl")
