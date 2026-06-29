from ._helpers import assert_valid


def test_rp5g_validator_passes() -> None:
    assert assert_valid()["validation"] == "PR168_RP5G_TRADE_PLAN_SIM_OK"

