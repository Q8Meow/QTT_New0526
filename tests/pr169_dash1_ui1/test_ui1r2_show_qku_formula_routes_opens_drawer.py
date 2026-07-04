from tests.pr169_dash1_ui1.r2_contract_assertions import assert_next_step_route


def test_ui1r2_show_qku_formula_routes_opens_drawer() -> None:
    assert_next_step_route("NEXT_STEP_SHOW_QKU_FORMULA_ROUTES", "qku-formula", "QKUFormulaRoutePreviewV1")
