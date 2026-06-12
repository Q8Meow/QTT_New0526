from .conftest import assert_rows


def test_pr166_sf_probability_edge_fields_are_materialized(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_ProbabilityEdgeRepairLedger.report.json")
    for row in rows[:100]:
        assert 0 <= row["market_implied_probability"] <= 1
        assert 0 <= row["model_probability_estimate"] <= 1
        assert 0 <= row["break_even_probability_after_costs"] <= 1
        assert row["yes_no_symmetry_check_passed_flag"] is True
