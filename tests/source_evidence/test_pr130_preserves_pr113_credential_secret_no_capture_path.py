from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_preserves_pr113_credential_secret_no_capture_path():
    assert support.main_report()["future_credential_alias_secret_no_capture_path_preserved"] is True
    assert all(
        attestation["future_credential_alias_secret_no_capture_path_preserved"] is True
        for attestation in support.no_secret_attestations()
    )
    assert support.handoff_report()["private_state_downstream_handoff"][
        "future_credential_alias_secret_no_capture_pr"
    ] == "PR113"
