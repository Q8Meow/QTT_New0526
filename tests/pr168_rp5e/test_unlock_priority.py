from ._helpers import read_json, read_jsonl


def test_unlock_priority_consumes_52_schedulable_rows_without_promotion() -> None:
    unlock = read_jsonl("unlock_pri.jsonl")
    triage = read_jsonl("triage52.jsonl")
    report = read_json("to_unlock.report.json")

    assert len(unlock) == 52
    assert len(triage) == 52
    assert report["replay_paper_executable_now_promotion_count"] == 0
    assert all(row["recommended_unlock_pr"] == "PR168-RP5D-R1" for row in unlock)
    assert all(row["promotion_in_rp5e_flag"] is False for row in unlock)
