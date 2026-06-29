from ._helpers import assert_rows_have_contract, read_json


def test_champion_challenger_preview_does_not_select_champion() -> None:
    rows = assert_rows_have_contract("champ_prev.jsonl")

    assert all(row["retain_for_future_rank4_flag"] for row in rows)
    assert all(row["final_champion_selected_flag"] is False for row in rows)
    assert all(row["champion_selection_authority"] == "NONE_IN_RP5F" for row in rows)
    assert read_json("run_receipt.report.json")["champion_selection_count"] == 0

