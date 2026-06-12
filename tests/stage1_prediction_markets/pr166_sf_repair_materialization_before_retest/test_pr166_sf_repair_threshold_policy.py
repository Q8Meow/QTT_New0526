from .conftest import assert_rows


def test_pr166_sf_threshold_policy_records_derivations(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairThresholdPolicy.report.json")
    assert rows
    assert all(row["derivation"] for row in rows)
    assert any(row["heuristic_used_flag"] is True for row in rows)
