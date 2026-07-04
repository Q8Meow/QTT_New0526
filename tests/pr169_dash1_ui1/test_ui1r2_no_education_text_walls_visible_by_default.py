from tests.pr169_dash1_ui1.r2_contract_assertions import assert_disclosure_defaults, assert_education


def test_ui1r2_no_education_text_walls_visible_by_default() -> None:
    assert_disclosure_defaults()
    assert_education()
