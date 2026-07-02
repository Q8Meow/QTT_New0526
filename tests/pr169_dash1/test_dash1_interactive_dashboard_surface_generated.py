from tests.pr169_dash1.conftest import BASE, json_doc, jsonl


def test_static_interactive_dashboard_surface_files_exist_and_are_manifested() -> None:
    manifest = json_doc("owner_dashboard_ui_manifest.json")
    surface = jsonl("owner_interactive_dashboard_surface.generated.jsonl")[0]
    for ref_key in ("html_ref", "script_ref", "style_ref", "fixture_ref"):
        assert (BASE / manifest[ref_key]).exists()
        assert (BASE / surface[ref_key]).exists()
    assert surface["hover_tooltips"] is True
    assert surface["click_to_drilldown"] is True
    assert surface["sortable_tables"] is True
