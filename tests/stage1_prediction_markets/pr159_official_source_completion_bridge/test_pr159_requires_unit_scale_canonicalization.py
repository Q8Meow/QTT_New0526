from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import candidate_records


def test_pr159_requires_unit_scale_canonicalization():
    assert all(record["extracted_unit_or_basis_or_null"] for record in candidate_records())
    assert all(record["extracted_scale_or_null"] for record in candidate_records())

