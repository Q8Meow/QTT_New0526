from ._helpers import read_json, read_jsonl


def test_rp5e_unlock_handoff_is_consumed() -> None:
    run = read_json("run_receipt.report.json")
    rows = read_jsonl("rp5e_unlock_in.jsonl")
    assert len(rows) == 52
    assert "unlock_pri.jsonl" in run["rp5e_unlock_inputs_consumed"]
    assert all(row["consumed_from_rp5e_unlock_pri_flag"] for row in rows)
