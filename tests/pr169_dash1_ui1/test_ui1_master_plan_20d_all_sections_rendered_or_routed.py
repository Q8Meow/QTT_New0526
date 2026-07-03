from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_master_plan_20d_all_sections_rendered_or_routed() -> None:
    coverage = ui_doc("owner_dashboard_master_plan_20d_exact_surface_coverage.generated.json")
    rows = coverage["rows"]
    assert rows
    assert all(row["render_status"] != "MISSING" for row in rows)
    assert all(row["validation_ref"] for row in rows)
