from ._helpers import read_jsonl


def test_route_crosswalk_inputs_are_consumed_or_receipted() -> None:
    rows = read_jsonl("xwalk_cons.jsonl")
    assert rows
    assert all(row["consumed_flag"] is True for row in rows)
    assert all(row["downstream_refs"] for row in rows)
    assert any("CommandActionMatrix" in row["optional_crosswalk_ref"] for row in rows)
