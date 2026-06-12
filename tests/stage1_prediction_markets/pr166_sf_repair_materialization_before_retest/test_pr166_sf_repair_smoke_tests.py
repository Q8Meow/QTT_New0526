from .conftest import assert_rows


def test_pr166_sf_smoke_tests_pass(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_SmokeTestLedger.report.json")
    assert len(rows) == 6502
    assert all(row["smoke_test_result"] == "PASS" for row in rows[:200])
    assert all(row["absolute_error"] <= 0.00001 for row in rows[:200])
