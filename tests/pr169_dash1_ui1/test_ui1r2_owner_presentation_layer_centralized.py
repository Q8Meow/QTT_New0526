from tests.pr169_dash1_ui1.r2_contract_assertions import assert_r2_artifacts_present, assert_renderer_controls


def test_ui1r2_owner_presentation_layer_centralized() -> None:
    assert_r2_artifacts_present()
    assert_renderer_controls()
