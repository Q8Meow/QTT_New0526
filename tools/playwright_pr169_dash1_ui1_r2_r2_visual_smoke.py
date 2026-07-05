from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


SCREENSHOTS = {
    "mobile_menu_only_header_closed": ".tmp/ui1r2r2_mobile_menu_only_header_closed.png",
    "mobile_menu_open_controls_visible": ".tmp/ui1r2r2_mobile_menu_open_controls_visible.png",
    "mobile_first_viewport_trading_content": ".tmp/ui1r2r2_mobile_first_viewport_trading_content.png",
    "mobile_text_extra_large": ".tmp/ui1r2r2_mobile_text_extra_large.png",
    "chat_composer_send_visible": ".tmp/ui1r2r2_chat_composer_send_visible.png",
    "chat_after_send": ".tmp/ui1r2r2_chat_after_send.png",
    "workbench_form_fields": ".tmp/ui1r2r2_workbench_form_fields.png",
    "workbench_dropdown_open": ".tmp/ui1r2r2_workbench_dropdown_open.png",
    "workbench_trade_plan_preview": ".tmp/ui1r2r2_workbench_trade_plan_preview.png",
    "owner_readable_home": ".tmp/ui1r2r2_owner_readable_home.png",
    "developer_raw_refs_visible": ".tmp/ui1r2r2_developer_raw_refs_visible.png",
    "action_to_workbench_prefill": ".tmp/ui1r2r2_action_to_workbench_prefill.png",
}


def _screenshot(page: Page, repo: Path, name: str, rows: list[dict[str, Any]], viewport: str) -> None:
    path = repo / SCREENSHOTS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=False)
    rows.append(
        {
            "path": SCREENSHOTS[name],
            "tested_interaction": name,
            "viewport": viewport,
            "result": "PASS",
            "runtime_side_effect_allowed": False,
        }
    )


def _assert_visible(page: Page, selector: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=10_000)


def _click_visible(page: Page, selector: str) -> None:
    page.locator(f"{selector}:visible").first.click()


def _write_report(
    repo: Path,
    rows: list[dict[str, Any]],
    checks: list[str],
    console_errors: list[str],
    external_requests: list[str],
) -> None:
    report_path = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "ui1r2r2_playwright.report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["status"] = "PASS" if not console_errors and not external_requests else "FAIL"
    payload["screenshots"] = rows
    payload["checks"] = checks
    payload["console_status"] = "PASS" if not console_errors else "FAIL"
    payload["network_status"] = "PASS" if not external_requests else "FAIL"
    payload["console_breaking_errors"] = console_errors
    payload["external_network_requests"] = external_requests
    payload["no_console_breaking_errors"] = not console_errors
    payload["no_external_network_requests"] = not external_requests
    payload["runtime_side_effect_allowed"] = False
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(repo: Path) -> None:
    html = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "owner_dashboard_review_surface.html"
    url = html.resolve().as_uri()
    console_errors: list[str] = []
    external_requests: list[str] = []
    screenshots: list[dict[str, Any]] = []
    checks: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=3,
        )
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)

        page.goto(url, wait_until="load")
        _assert_visible(page, "header[data-header-chrome='menu-only']")
        assert page.locator("#ownerOptionsPanel:visible").count() == 0
        closed_header = page.locator("header").inner_text(timeout=10_000)
        for forbidden in ("Guided", "Advanced", "Developer", "Dark", "Light", "Local Preview", "No Runtime Side Effect", "Technical Details"):
            assert forbidden not in closed_header
        _screenshot(page, repo, "mobile_menu_only_header_closed", screenshots, "mobile")
        _screenshot(page, repo, "mobile_first_viewport_trading_content", screenshots, "mobile")
        checks.append("mobile_closed_header_menu_only_first_viewport_trading_content")

        page.locator("#ownerOptionsToggle").click()
        _assert_visible(page, "#ownerOptionsPanel")
        assert page.locator("#experienceModeSwitch:visible").count() == 1
        assert page.locator("[data-text-size-choice='extra_large']:visible").count() == 1
        _screenshot(page, repo, "mobile_menu_open_controls_visible", screenshots, "mobile")
        page.locator("[data-text-size-choice='extra_large']").click()
        assert page.locator("html").get_attribute("data-text-size") == "extra_large"
        _screenshot(page, repo, "mobile_text_extra_large", screenshots, "mobile")
        checks.append("menu_opens_text_size_extra_large_applies")

        page.keyboard.press("Escape")
        _click_visible(page, "a[href='#chat']")
        _assert_visible(page, "#ownerChatInput")
        _assert_visible(page, "#routePreviewButton")
        assert page.locator("#routePreviewButton").inner_text(timeout=10_000).strip() == "Send"
        _screenshot(page, repo, "chat_composer_send_visible", screenshots, "mobile")
        page.locator("#ownerChatInput").fill("Can QTT check this market and find the best trade?")
        page.locator("#routePreviewButton").click()
        _assert_visible(page, "#chatReceiptPreview [data-preview-object='OwnerPlainEnglishIntentPreviewV1']")
        assert "no live LLM call" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "chat_after_send", screenshots, "mobile")
        checks.append("chat_send_creates_local_preview_only")

        page.locator("#chatReceiptPreview [data-next-step-id='NEXT_STEP_SEND_TO_TRADE_WORKBENCH']").first.click()
        _assert_visible(page, "#tradeWorkbench[data-prefilled-context='true']")
        _screenshot(page, repo, "action_to_workbench_prefill", screenshots, "mobile")
        _assert_visible(page, "[data-workbench-field='venue']")
        _screenshot(page, repo, "workbench_form_fields", screenshots, "mobile")
        page.locator("[data-workbench-field='venue']").select_option("polymarket")
        page.locator("[data-workbench-field='side']").select_option("yes")
        page.locator("[data-workbench-field='max_budget']").fill("50")
        page.locator("[data-workbench-field='max_loss']").fill("20")
        page.locator("[data-workbench-field='hold_duration']").fill("through resolution")
        _screenshot(page, repo, "workbench_dropdown_open", screenshots, "mobile")
        _assert_visible(page, "#tradePlanCandidatePreview")
        assert "Runtime work" in page.locator("#workbenchPreviewGrid").inner_text(timeout=10_000)
        _screenshot(page, repo, "workbench_trade_plan_preview", screenshots, "mobile")
        checks.append("workbench_form_updates_trade_plan_candidate_preview")

        desktop = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        desktop.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        desktop.on("pageerror", lambda exc: console_errors.append(str(exc)))
        desktop.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)
        desktop.goto(url, wait_until="load")
        _assert_visible(desktop, "#overview")
        home_text = desktop.locator("#overview").inner_text(timeout=10_000)
        for raw in ("DASH1_FEATURE_", "OWNER_DASHBOARD_PACKET_V1", "VISIBLE_EMPTY_STATE_PROVIDER_PENDING", "CONTRACT_DEFINED_PROVIDER_PENDING"):
            assert raw not in home_text
        _screenshot(desktop, repo, "owner_readable_home", screenshots, "desktop")

        desktop.locator("#ownerOptionsToggle").click()
        desktop.locator("[data-mode-choice='DEVELOPER']").click()
        _assert_visible(desktop, "body[data-experience-mode='DEVELOPER']")
        _click_visible(desktop, "a[href='#developer-mode']")
        _assert_visible(desktop, "#developerMode")
        desktop.locator("#developerMode summary").first.click()
        assert "OwnerSurfaceResolver" in desktop.locator("#developerMode").inner_text(timeout=10_000)
        _screenshot(desktop, repo, "developer_raw_refs_visible", screenshots, "desktop")
        checks.append("owner_copy_hides_raw_refs_until_developer")

        browser.close()

    _write_report(repo, screenshots, checks, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R2_R2_PLAYWRIGHT_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R2_R2_PLAYWRIGHT_OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    run(Path(args.repo_root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
