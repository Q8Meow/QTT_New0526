from ._helpers import read_jsonl


def test_tier_overlay_does_not_mutate_upstream() -> None:
    rows = read_jsonl("tier_overlay.jsonl")
    assert rows
    assert all(row["overlay_executability_state"] == "REPLAY_PAPER_EXECUTABLE_NOW" for row in rows)
    assert all(row["upstream_mutation_flag"] is False for row in rows)
