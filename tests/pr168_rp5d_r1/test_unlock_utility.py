from ._helpers import read_jsonl


def test_unlock_utility_rows_drive_selection_without_profit_proof() -> None:
    rows = read_jsonl("unlock_util.jsonl")
    selected = [row for row in rows if row["used_for_selection_flag"]]
    assert len(rows) == 52
    assert len(selected) == 20
    assert all(row["profit_proof_flag"] is False for row in rows)
