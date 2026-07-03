from tests.pr169_dash1_ui1.conftest import UI, boot_data, ui_text


def test_ui1_fixture_not_primary_when_dash1_artifacts_exist() -> None:
    data = boot_data()
    assert data["meta"]["fixture_fallback_active"] is False
    assert data["fixture_fallback"]["fixture_primary_when_generated_artifacts_exist"] is False
    surface_text = "\n".join(
        (UI / name).read_text(encoding="utf-8")
        for name in (
            "owner_dashboard_review_surface.html",
            "owner_dashboard_review_surface.css",
            "owner_dashboard_review_surface.js",
        )
    )
    assert "fixtures/owner_dashboard_demo_data.json" not in surface_text
    assert "fetch(" not in ui_text()
