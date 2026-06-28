from ._helpers import read_jsonl


def test_selector_attempts_bounded_top_slice() -> None:
    rows = read_jsonl("unlock_select.jsonl")
    assert len(rows) == 20
    assert all(row["selected_for_contract_completion_flag"] for row in rows)
