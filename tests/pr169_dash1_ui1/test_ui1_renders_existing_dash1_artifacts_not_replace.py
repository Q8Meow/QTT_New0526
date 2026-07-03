from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc


def test_ui1_renders_existing_dash1_artifacts_not_replace() -> None:
    data = boot_data()
    boundary = ui_doc("owner_dashboard_dash1_ui1_renderer_boundary.generated.json")
    assert boundary["DASH1_is_canonical_backend_control_plane"] is True
    assert boundary["UI1_is_renderer_enhancement_responsive_layer"] is True
    assert boundary["renders_existing_dash1_artifacts"] is True
    assert data["meta"]["generated_from"].startswith("owner_dashboard_surface_registry.jsonl")
