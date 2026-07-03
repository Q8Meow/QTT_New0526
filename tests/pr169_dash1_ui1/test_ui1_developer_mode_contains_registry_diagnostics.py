from tests.pr169_dash1_ui1.r1_contract_assertions import assert_developer_mode_diagnostics


def test_ui1_developer_mode_contains_registry_diagnostics() -> None:
    assert_developer_mode_diagnostics()
