from ._helpers import rows


def test_champion_preview_is_advisory_only() -> None:
    previews = rows("champ_prev.jsonl")
    assert any(row["advisory_champion_preview_flag"] for row in previews)
    assert all(row["final_champion_selected_flag"] is False for row in previews)
    assert all(row["champion_selection_authority"] == "NONE_IN_RANK4" for row in previews)

