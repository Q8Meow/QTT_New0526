from tests.pr169_dash1_ui1.r2_contract_assertions import assert_education


def test_ui1r2_page_education_controls_collapsed_by_default() -> None:
    assert_education()
