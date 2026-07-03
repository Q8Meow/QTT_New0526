from tests.pr169_dash1_ui1.r1_contract_assertions import assert_trade_workbench


def test_ui1_trade_workbench_best_challenger_no_trade_cards() -> None:
    assert_trade_workbench()
