from ._helpers import read_jsonl


def test_count_integrity_uses_overlay_formula() -> None:
    row = read_jsonl("count_integrity.jsonl")[0]
    assert row["prior_executable_now_count"] == 0
    assert row["new_overlay_count"] == row["prior_executable_now_count"] + row["promoted_count"]
    assert row["target_met_flag"] is True
    assert row["upstream_files_mutated_flag"] is False
