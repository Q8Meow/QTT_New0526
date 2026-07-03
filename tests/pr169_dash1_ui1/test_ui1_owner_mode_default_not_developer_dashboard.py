from tests.pr169_dash1_ui1.r1_contract_assertions import assert_owner_mode_migrated


def test_ui1_owner_mode_default_not_developer_dashboard() -> None:
    assert_owner_mode_migrated()
