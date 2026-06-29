from ._helpers import assert_rows_have_contract


def test_champion_preview_has_no_final_authority() -> None:
    rows = assert_rows_have_contract("champ_chall_preview.jsonl")
    assert all(row["champion_selection_authority"] == "NONE_IN_RP5G" for row in rows)
    assert all(row["final_champion_selected_flag"] is False for row in rows)

