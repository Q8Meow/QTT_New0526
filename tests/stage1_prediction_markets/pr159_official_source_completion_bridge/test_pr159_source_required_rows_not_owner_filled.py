from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import atomicrows_records


def test_pr159_source_required_rows_not_owner_filled():
    assert all(record["accepted_value_or_null"] is None for record in atomicrows_records())
    assert all(record["canonical_value_or_null"] is None for record in atomicrows_records())

