from ._helpers import read_jsonl


def test_diversity_ledger_tracks_near_clone_and_duplicate_suppression() -> None:
    rows = read_jsonl("diverse.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["near_clone_cluster_id"]
        assert row["duplicate_suppression_rule_ref"]
        assert float(row["duplicate_penalty"]) >= 0.0
        assert row["global_ban_flag"] is False
