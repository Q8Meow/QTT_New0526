from ._helpers import read_jsonl


def test_required_inputs_are_read_and_consumed() -> None:
    reads = read_jsonl("read_rec.jsonl")
    consumed = read_jsonl("in_cons.jsonl")
    assert reads
    assert all(row["exists_flag"] for row in reads)
    assert any("pr168_rp5e/unlock_pri.jsonl" in row["file_ref"] for row in reads)
    assert all(row["consumed_flag"] for row in consumed)
