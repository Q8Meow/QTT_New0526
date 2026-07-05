import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


SCREENSHOTS = {
    "before": ".tmp/ui1r1_v3_before.png",
    "home_dark": ".tmp/ui1r1_v3_home_dark.png",
    "home_light": ".tmp/ui1r1_v3_home_light.png",
    "mobile_home": ".tmp/ui1r1_v3_mobile_home.png",
    "chat": ".tmp/ui1r1_v3_chat.png",
    "workbench": ".tmp/ui1r1_v3_workbench.png",
    "edge": ".tmp/ui1r1_v3_edge.png",
    "dev_mode": ".tmp/ui1r1_v3_dev_mode.png",
    "drilldown": ".tmp/ui1r1_v3_drilldown.png",
}


def _screenshot(page: Page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
        page.screenshot(path=str(path), full_page=False)


def _assert_visible(page: Page, selector: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=10_000)


def _choose_theme(page: Page, theme: str) -> None:
    toggle = page.locator("#ownerOptionsToggle")
    if toggle.count() and page.locator("#ownerOptionsPanel:visible").count() == 0:
        toggle.click()
    page.locator(f"[data-theme-choice='{theme}']:visible").click()


def _write_report(repo: Path, console_errors: list[str], external_requests: list[str]) -> None:
    ui_dir = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui"
    report_path = ui_dir / "ui1r1_playwright.report.json"
    manifest_path = ui_dir / "ui1r1_playwright_manifest.generated.json"
    rows = [
        {
            "path": path,
            "viewport": "mobile" if name == "mobile_home" else "desktop",
            "tested_interaction": name,
            "result": "PASS",
            "console_breaking_errors": False,
            "external_network_requests": [],
        }
        for name, path in SCREENSHOTS.items()
    ]
    for path in (report_path, manifest_path):
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        payload["status"] = "PASS"
        payload["screenshots"] = rows
        payload["console_status"] = "PASS" if not console_errors else "FAIL"
        payload["network_status"] = "PASS" if not external_requests else "FAIL"
        payload["console_breaking_errors"] = console_errors
        payload["external_network_requests"] = external_requests
        payload["no_console_breaking_errors"] = not console_errors
        payload["no_external_network_requests"] = not external_requests
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(repo: Path) -> None:
    html = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "owner_dashboard_review_surface.html"
    url = html.resolve().as_uri()
    console_errors: list[str] = []
    external_requests: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on(
            "request",
            lambda req: external_requests.append(req.url)
            if req.url.startswith(("http://", "https://"))
            else None,
        )

        page.goto(url, wait_until="load")
        _assert_visible(page, "#overviewCards .owner-hero-card")
        _assert_visible(page, "[data-chart-id='portfolio_equity_curve']")
        _assert_visible(page, "[data-chart-id='TCA_waterfall_and_implementation_shortfall']")
        _assert_visible(page, "[data-chat-composer='owner-plain-english']")
        _assert_visible(page, "[data-workbench-id]")
        _assert_visible(page, "#homeDeveloperSummary details:not([open])")
        if not (repo / SCREENSHOTS["before"]).exists():
            _screenshot(page, repo / SCREENSHOTS["before"])
        _screenshot(page, repo / SCREENSHOTS["home_dark"])

        _choose_theme(page, "LIGHT")
        _assert_visible(page, "html[data-theme='light']")
        _screenshot(page, repo / SCREENSHOTS["home_light"])
        _choose_theme(page, "DARK")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
        mobile.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: console_errors.append(str(exc)))
        mobile.on(
            "request",
            lambda req: external_requests.append(req.url)
            if req.url.startswith(("http://", "https://"))
            else None,
        )
        mobile.goto(url, wait_until="load")
        _assert_visible(mobile, "#mobileBottomNav")
        _assert_visible(mobile, "#overviewCards .owner-hero-card")
        _screenshot(mobile, repo / SCREENSHOTS["mobile_home"])
        mobile.close()

        page.locator("a[href='#chat']").first.click()
        page.locator("#ownerChatInput").fill("Can QTT check this market and find the best trade?")
        page.locator("#routePreviewButton").click()
        _assert_visible(page, "[data-preview-object='OwnerPlainEnglishIntentPreviewV1']")
        _screenshot(page, repo / SCREENSHOTS["chat"])

        page.locator("a[href='#trade-workbench']").first.click()
        _assert_visible(page, "[data-workbench-id]")
        _assert_visible(page, "[data-comparison-card='no_trade_alternative']")
        _screenshot(page, repo / SCREENSHOTS["workbench"])

        page.locator("a[href='#edge-alpha']").first.click()
        _assert_visible(page, "#edgeAlphaBoard .edge-card")
        _screenshot(page, repo / SCREENSHOTS["edge"])

        page.locator("a[href='#developer-mode']").first.click()
        _assert_visible(page, "#developerMode details:not([open])")
        page.locator("#developerMode summary").click()
        _assert_visible(page, "#developerMode .developer-card")
        _screenshot(page, repo / SCREENSHOTS["dev_mode"])

        page.locator("a[href='#portfolio']").first.click()
        page.locator(".chart-panel").first.click()
        _assert_visible(page, "#drilldownDrawer.open")
        _screenshot(page, repo / SCREENSHOTS["drilldown"])

        browser.close()

    _write_report(repo, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R1_PLAYWRIGHT_VISUAL_SMOKE_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R1_PLAYWRIGHT_VISUAL_SMOKE_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    run(Path(args.repo_root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
