from tests.pr168_gfp2r._helpers import all_generated_payloads, assert_no_forbidden_authority


def test_pr168_gfp2r_no_live_source_connector_cash_order_quantum_backend_or_hash_authority() -> None:
    for payload in all_generated_payloads():
        assert_no_forbidden_authority(payload)
