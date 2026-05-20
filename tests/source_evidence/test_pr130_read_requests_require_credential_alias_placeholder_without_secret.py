from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_read_requests_require_credential_alias_placeholder_without_secret():
    for request in support.read_requests():
        assert request["credential_alias_placeholder_ref"].startswith("PR130_")
        assert request["credential_alias_required_future_pr"] == "PR113"
        assert request["credential_alias_authority_created"] is False
        assert request["raw_secret_capture_allowed_flag"] is False
