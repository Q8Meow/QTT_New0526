from .conftest import assert_rows


def test_pr166_sf_missing_values_are_candidate_filled(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_MissingValueFillLedger.report.json")
    assert len(rows) == 6502
    for row in rows[:100]:
        assert row["missing_value_fill_status"].startswith("CANDIDATE_PROVISIONAL_VALUE_FILLED")
        assert row["candidate_provisional_flag"] is True
        assert row["replay_paper_required_before_promotion"] is True
