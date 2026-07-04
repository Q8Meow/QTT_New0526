from tests.pr169_dash1_ui1.r2_contract_assertions import assert_education, assert_renderer_controls


def test_ui1r2_chart_explainers_present() -> None:
    assert_education()
    assert_renderer_controls()
