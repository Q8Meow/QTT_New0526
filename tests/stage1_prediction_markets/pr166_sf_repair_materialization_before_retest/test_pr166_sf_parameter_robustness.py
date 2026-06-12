from .conftest import assert_rows


def test_pr166_sf_parameter_robustness_has_perturbations(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_ParameterRobustnessLedger.report.json")
    assert len(rows) == 6502
    assert all(len(row["parameter_perturbation_values"]) == 3 for row in rows[:100])
