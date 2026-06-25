from tests.pr168_rp5b._helpers import final_summary, load_rows


def test_legacy_keep_reason_ledger_exists() -> None:
    rows = load_rows("legacy_keep_reason_rows")
    assert len(rows) == final_summary()["files_kept_count"]
    assert any(row["future_pr_route"] == "PR168_RP5C" for row in rows)
    assert any(row["keep_reason"] == "UNCLEAR_DO_NOT_DELETE" for row in rows)
