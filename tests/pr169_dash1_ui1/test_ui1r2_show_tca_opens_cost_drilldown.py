from tests.pr169_dash1_ui1.r2_contract_assertions import assert_next_step_route


def test_ui1r2_show_tca_opens_cost_drilldown() -> None:
    assert_next_step_route("NEXT_STEP_SHOW_TCA_COST_BREAKDOWN", "tca-cost-drilldown", "TCADrilldownPreviewV1")
