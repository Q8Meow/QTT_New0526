from ._helpers import read_jsonl


def test_promote_and_nonpromote_cover_unlock_universe() -> None:
    assert len(read_jsonl("promote.jsonl")) + len(read_jsonl("nonpromote.jsonl")) == 52
    assert all(row["exact_blocker_codes"] for row in read_jsonl("nonpromote.jsonl"))
