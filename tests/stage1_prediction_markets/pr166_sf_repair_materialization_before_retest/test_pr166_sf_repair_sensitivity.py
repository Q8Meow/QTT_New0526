from .conftest import assert_rows


def test_pr166_sf_repair_sensitivity_has_stress_grid(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairSensitivityLedger.report.json")
    for row in rows[:100]:
        scenarios = {item["scenario"] for item in row["sensitivity_grid"]}
        assert "WIDER_SPREAD_STRESS" in scenarios
        assert "LIQUIDITY_COLLAPSE_STRESS" in scenarios
