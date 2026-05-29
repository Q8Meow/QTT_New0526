from src.qtt.stage1_prediction_markets.master_plan_residual_candidate_coverage import constants as c

from .pr161b_test_support import report


def test_pr161b_no_scattered_hardcoded_strings_uses_central_enums():
    enums = report("candidate_inventory")["central_enum_value_sets"]
    assert set(enums["coverage_states"]) == {item.value for item in c.CoverageState}
    assert set(enums["residual_gap_types"]) == {item.value for item in c.ResidualGapType}
    assert "MISSING_OWNER_DECISION_REQUIRED" not in str(enums)
