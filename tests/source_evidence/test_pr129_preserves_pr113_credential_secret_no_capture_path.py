from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_pr113_credential_secret_no_capture_path():
    handoff = support.handoff_report()["runtime_cash_downstream_handoff"]

    assert handoff["future_credential_alias_secret_no_capture_pr"] == "PR113"
    assert support.main_report()["future_credential_alias_secret_no_capture_path_preserved"] is True
