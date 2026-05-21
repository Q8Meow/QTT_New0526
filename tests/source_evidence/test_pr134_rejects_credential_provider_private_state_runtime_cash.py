from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_credential_provider_private_state_runtime_cash():
    assert_malformed("malformed_private_state_fetch.v1.fixture.json", "PRIVATE_STATE_FETCH_CREATED")
    for field_name, expected_code in (
        ("credential_provider_called", "CREDENTIAL_PROVIDER_CALLED"),
        ("live_credential_resolution_performed", "LIVE_CREDENTIAL_RESOLUTION_PERFORMED"),
        ("runtime_cash_authority_created", "RUNTIME_CASH_AUTHORITY_CREATED"),
    ):
        payload = mutable_artifacts()
        payload["runtime_resolver_input_locks"][0][field_name] = True
        assert expected_code in failure_codes(payload)
