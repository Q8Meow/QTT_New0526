from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report


def test_pr158_lane_count_invariants():
    receipt = master_report()["count_invariant_receipt"]
    assert receipt["count_invariants_passed_flag"] is True
    assert receipt["agent_assignment_count"] + receipt["owner_policy_default_count"] + receipt["parameter_range_owner_policy_count"] == 1405
    assert receipt["pr154_owner_route_count"] + receipt["pr154_split_reclassification_count"] + receipt["pr154_private_doc_attestation_count"] == 78
    assert receipt["owner_request_packet_count"] == 1483

