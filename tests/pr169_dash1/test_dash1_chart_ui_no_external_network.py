from tests.pr169_dash1.conftest import BASE


def test_static_chart_ui_uses_local_files_only() -> None:
    text = "\n".join(
        (BASE / path).read_text(encoding="utf-8").lower()
        for path in (
            "ui/owner_dashboard_review_surface.html",
            "ui/owner_dashboard_review_surface.css",
            "ui/owner_dashboard_review_surface.js",
        )
    ).replace("http://www.w3.org/2000/svg", "")
    assert "https://" not in text
    assert "http://" not in text
    assert "cdn." not in text
    assert '<script src="owner_dashboard_review_surface.js"' in text
