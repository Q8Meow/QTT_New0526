from ._helpers import read_jsonl


def test_promotion_audit_covers_attempted_rows() -> None:
    assert len(read_jsonl("promote_audit.jsonl")) == len(read_jsonl("unlock_select.jsonl"))
    assert sum(1 for row in read_jsonl("promote_audit.jsonl") if row["promotion_approved_flag"]) == len(read_jsonl("promote.jsonl"))
