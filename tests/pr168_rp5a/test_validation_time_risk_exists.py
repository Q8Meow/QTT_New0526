from tests.pr168_rp5a._helpers import load_rows


def test_validation_time_risk_exists() -> None:
    rows = load_rows("validation_time_risk_rows")
    assert rows
    assert any(row["repo_wide_scan_flag"] for row in rows)
