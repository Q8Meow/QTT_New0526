from .conftest import assert_rows


def test_pr166_sf_formula_qku_repair_actions_are_exact(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_FormulaQKURepairRegistry.report.json")
    for row in rows[:100]:
        assert row["formula_repair_action"]
        assert row["qku_repair_action"] == "MATERIALIZE_QKU_REPAIR_PACKET_WITH_TEST_VECTOR"
        assert row["algorithm_repair_action"]
