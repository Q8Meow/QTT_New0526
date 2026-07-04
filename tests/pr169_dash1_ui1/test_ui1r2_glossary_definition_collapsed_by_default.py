from tests.pr169_dash1_ui1.r2_contract_assertions import assert_glossary, assert_renderer_controls


def test_ui1r2_glossary_definition_collapsed_by_default() -> None:
    assert_glossary()
    assert_renderer_controls()
