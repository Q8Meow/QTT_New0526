from tests.pr169_dash1_ui1.r2_contract_assertions import assert_modes
from tests.pr169_dash1_ui1.r1_contract_assertions import assert_developer_mode_diagnostics


def test_ui1r2_developer_mode_preserves_technical_refs() -> None:
    assert_modes()
    assert_developer_mode_diagnostics()
