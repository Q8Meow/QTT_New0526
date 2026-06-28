from ._helpers import read_jsonl


def test_gap_family_rows_have_precise_blockers() -> None:
    rows = read_jsonl("gap_family.jsonl")
    assert rows
    assert all(row["r1_blocker_code"].startswith("MISSING_") for row in rows)
