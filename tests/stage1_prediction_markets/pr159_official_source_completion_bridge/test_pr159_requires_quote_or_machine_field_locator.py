from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import candidate_records


def test_pr159_requires_quote_or_machine_field_locator():
    assert all(record["quote_span_or_machine_field_locator"]["quote_span"] for record in candidate_records())

