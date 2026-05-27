from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import assert_owner_response_rejected, owner_packet


def test_pr157_owner_response_validator_rejects_ambiguous_or_external_fact_values():
    request_id = owner_packet()["requests"][0]["request_id"]
    payload = {
        "response_id": "bad",
        "owner_attestation_timestamp_or_declared_date": "2026-05-27",
        "owner_identity_or_alias": "owner",
        "schema_version": "pr157.owner_response.v1",
        "response_items": [
            {"request_id": request_id, "authority_class": "OWNER_INTERNAL_POLICY", "claims_external_fact": True}
        ],
    }
    assert_owner_response_rejected(payload, "EXTERNAL_FACT_CLAIM_FORBIDDEN")
