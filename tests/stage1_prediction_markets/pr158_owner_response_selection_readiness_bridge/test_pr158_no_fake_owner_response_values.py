from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import owner_response


def test_pr158_no_fake_owner_response_values():
    for item in owner_response()["response_items"]:
        assert item["claims_external_fact"] is False
        if isinstance(item["value"], str):
            assert item["value"] not in {"TBD", "TODO", "PLACEHOLDER"}
        assert "PRIVATE_DOC_ATTESTATION" not in item["request_id"]
