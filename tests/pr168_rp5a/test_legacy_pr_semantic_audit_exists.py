from tests.pr168_rp5a._helpers import load_rows


def test_legacy_pr_semantic_audit_exists() -> None:
    rows = load_rows("legacy_pr_semantic_rows")
    assert rows
    pr240 = [row for row in rows if row["pr_number"] == 240][0]
    assert pr240["state"] == "CLOSED"
    assert pr240["merged_at"] is None
    assert pr240["next_action"] == "HISTORICAL_ONLY"
