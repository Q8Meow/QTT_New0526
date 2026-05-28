from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import lane_f_records


def test_pr158_lane_f_private_doc_requires_owner_attestation():
    records = lane_f_records()
    assert len(records) == 6
    assert all(record["private_doc_access_rights_attestation_required_flag"] is True for record in records)
    assert all(record["response_value_or_null"] is None for record in records)

