from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc


def test_ui1_one_place_modification_manifest() -> None:
    policy = ui_doc("owner_dashboard_generated_projection_policy.report.json")
    assert policy["status"] == "PASS"
    assert policy["generated_UI_projection_files_derived_from_DASH1"] is True
    assert policy["post_launch_one_place_modification_workflow_preserved"] is True
    assert boot_data()["widget_manifest"]["meta"]["generated_from"].startswith("owner_dashboard_surface_registry.jsonl")
