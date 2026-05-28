from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_formula_derived_routes_require_accepted_inputs():
    records = report(c.FORMULA_DERIVED_ROUTE_PATH)["records"]
    assert len(records) == 15
    assert all(item["accepted_upstream_inputs_required_flag"] is True for item in records)
    assert all(item["formula_execution_created_by_PR160_flag"] is False for item in records)
