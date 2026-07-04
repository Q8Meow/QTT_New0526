from tests.pr169_dash1_ui1.r2_contract_assertions import assert_modes, assert_owner_mode_text_safety


def test_ui1r2_advanced_owner_mode_no_raw_machine_refs() -> None:
    assert_modes()
    assert_owner_mode_text_safety()
