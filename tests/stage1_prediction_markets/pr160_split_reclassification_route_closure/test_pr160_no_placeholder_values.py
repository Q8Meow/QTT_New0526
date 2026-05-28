from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import all_generated_payloads


def test_pr160_no_placeholder_values():
    text = repr(all_generated_payloads())
    assert "PLACEHOLDER" not in text
    assert "TODO" not in text
    assert "TBD" not in text
