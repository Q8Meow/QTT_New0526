from ._helpers import read_json, read_jsonl


def test_no_persistent_full_stack_universe_or_cartesian_grid() -> None:
    receipt = read_json("run_receipt.report.json")
    assert receipt["persistent_full_cartesian_grid_count"] == 0
    assert receipt["full_stack_universe_count"] == 0

    for row in read_jsonl("search_trace.jsonl"):
        assert row["full_cartesian_generation_flag"] is False
        assert row["candidate_count_generated"] <= row["candidate_count_target"]
