from tests.pr169_dash1_ui1.r2_contract_assertions import assert_renderer_controls, assert_no_runtime_authority


def test_ui1r2_autonomy_education_no_runtime_claim() -> None:
    assert_renderer_controls()
    assert_no_runtime_authority()
