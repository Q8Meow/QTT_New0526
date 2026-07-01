from .test_support import read_json, read_jsonl


def test_mem1_consumes_required_upstream_families() -> None:
    assert read_json("input_consumption.report.json")["missing_required_input_count"] == 0
    assert read_jsonl("vs2_input_refs.jsonl")
    assert read_jsonl("rank4_input_refs.jsonl")
    assert read_jsonl("qopt1_input_refs.jsonl")
    assert read_jsonl("rp5g_input_refs.jsonl")
    assert all(row["read_status"] == "READ_UTF8" for row in read_jsonl("read_rec.jsonl"))
