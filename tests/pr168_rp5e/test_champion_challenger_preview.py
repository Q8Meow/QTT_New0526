from ._helpers import read_jsonl


def test_champion_challenger_preview_retains_challengers_without_selecting_champions() -> None:
    rows = read_jsonl("champ_prev.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["challenger_preview_ids"]
        assert row["retain_for_future_rank4_flag"] is True
        assert row["final_champion_selected_flag"] is False
        assert row["champion_selection_authority"] == "NONE_IN_RP5E"
