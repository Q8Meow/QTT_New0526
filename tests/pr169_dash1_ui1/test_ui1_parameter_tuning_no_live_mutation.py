from tests.pr169_dash1_ui1.r1_contract_assertions import assert_parameter_tuning


def test_ui1_parameter_tuning_no_live_mutation() -> None:
    assert_parameter_tuning()
