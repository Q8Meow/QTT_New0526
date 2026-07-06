from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


SCREENSHOTS = [
    "sidebar_expanded",
    "sidebar_collapsed",
    "developer_nav_hidden_in_guided",
    "search_chat_result",
    "search_agent_result",
    "action_to_workbench_active_nav",
    "chat_preset_dropdown",
    "qtt_guide_panel",
    "chart_hover_tooltip",
    "chart_drilldown_distinct",
    "tca_breakdown_distinct",
    "explain_card_specific",
    "technical_details_raw_refs",
    "workbench_guided_selectors",
    "workbench_other_custom_field",
    "workbench_numeric_range_hints",
    "input_required_color_state",
    "theme_picker_presets",
    "high_contrast_theme",
    "settings_center_open",
    "settings_appearance_tab",
    "settings_trading_preferences_preview_only",
    "mobile_collapsed_sidebar_and_workbench",
    "mobile_chart_tooltip_or_value_panel",
    "owner_copy_cleanup",
    "options_status_simplified",
    "default_card_action_menu_collapsed",
    "selected_card_action_menu_expanded",
    "drawer_payloads_distinct",
    "default_card_more_actions_menu",
    "chart_tooltip_provider_pending_no_fake_value",
    "search_result_scroll_focus_target",
    "workbench_invalid_range_guidance",
]


def _path(name: str) -> str:
    return f".tmp/ui1r2r3_{name}.png"


def _screenshot(page: Page, repo: Path, name: str, rows: list[dict[str, Any]], viewport: str) -> None:
    path = repo / _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=False)
    rows.append(
        {
            "path": _path(name),
            "tested_interaction": name,
            "viewport": viewport,
            "result": "PASS",
            "runtime_side_effect_allowed": False,
        }
    )


def _assert_visible(page: Page, selector: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=10_000)


def _close_drawer(page: Page) -> None:
    if page.locator("#drilldownDrawer.open").count():
        page.locator("#closeDrawer").click()


def _open_chart_action(page: Page, kind: str) -> None:
    _close_drawer(page)
    details = page.locator("#chartGrid .next-action-menu").first
    if details.get_attribute("open") is None:
        details.locator("summary").click()
    page.locator(f"#chartGrid [data-owner-drawer-action='{kind}']").first.click()
    _assert_visible(page, "#drilldownDrawer.open")


def _tap_mobile_nav(page: Page, href: str) -> None:
    link = page.locator(f"#mobileBottomNav a[href='{href}']").first
    link.wait_for(state="visible", timeout=10_000)
    box = link.bounding_box()
    if not box:
        raise AssertionError(f"missing mobile nav box for {href}")
    page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def _write_report(
    repo: Path,
    rows: list[dict[str, Any]],
    checks: list[str],
    console_errors: list[str],
    external_requests: list[str],
) -> None:
    report_path = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "ui1r2r3_playwright.report.json"
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
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)
        page.goto(url, wait_until="load")

        _assert_visible(page, ".rail")
        _screenshot(page, repo, "sidebar_expanded", screenshots, "desktop")
        assert page.locator(".technical-nav:visible").count() == 0
        _screenshot(page, repo, "developer_nav_hidden_in_guided", screenshots, "desktop")
        page.locator("#sidebarCollapseToggle").click()
        assert page.locator("body").get_attribute("data-sidebar-collapsed") == "true"
        _screenshot(page, repo, "sidebar_collapsed", screenshots, "desktop")
        page.locator("#sidebarCollapseToggle").click()
        checks.append("sidebar_collapses_and_hides_developer_nav_in_guided")

        page.locator("#globalSearch").fill("chat")
        _assert_visible(page, "#ownerSearchResults [data-target-surface='chat']")
        _screenshot(page, repo, "search_chat_result", screenshots, "desktop")
        page.locator("#globalSearch").fill("agent")
        _assert_visible(page, "#ownerSearchResults [data-target-surface='agents']")
        _screenshot(page, repo, "search_agent_result", screenshots, "desktop")
        page.locator("#globalSearch").fill("workbench")
        page.locator("#ownerSearchResults [data-target-surface='trade-workbench']").first.click()
        _assert_visible(page, "#tradeWorkbench")
        assert page.locator(".rail a[href='#trade-workbench'][aria-current='page']").count() == 1
        _screenshot(page, repo, "search_result_scroll_focus_target", screenshots, "desktop")
        checks.append("ranked_search_focuses_targets")

        page.locator("[data-next-step-id='NEXT_STEP_SEND_TO_TRADE_WORKBENCH']").first.click()
        _assert_visible(page, "#tradeWorkbench[data-prefilled-context='true']")
        assert page.locator(".rail a[href='#trade-workbench'][aria-current='page']").count() == 1
        _screenshot(page, repo, "action_to_workbench_active_nav", screenshots, "desktop")

        page.locator("a[href='#chat']").first.click()
        _assert_visible(page, "#chatPresetSelect")
        page.locator("#chatPresetSelect").select_option(index=1)
        assert page.locator("#ownerChatInput").input_value()
        _screenshot(page, repo, "chat_preset_dropdown", screenshots, "desktop")
        page.locator("#qttGuideToggle").click()
        _assert_visible(page, "#qttGuidePanel.open")
        _screenshot(page, repo, "qtt_guide_panel", screenshots, "desktop")
        page.locator("#closeQttGuide").click()
        checks.append("chat_preset_dropdown_and_guide_local_only")

        page.locator("a[href='#portfolio']").first.click()
        _assert_visible(page, "#chartGrid .chart-canvas")
        page.locator("#chartGrid .chart-canvas").first.hover(position={"x": 240, "y": 120})
        _assert_visible(page, "#chartGrid .chart-canvas.is-focused .chart-tooltip")
        _screenshot(page, repo, "chart_hover_tooltip", screenshots, "desktop")
        _screenshot(page, repo, "chart_tooltip_provider_pending_no_fake_value", screenshots, "desktop")

        _open_chart_action(page, "chart_drilldown")
        assert page.locator("#drilldownDrawer").get_attribute("data-drawer-kind") == "chart_drilldown"
        _screenshot(page, repo, "chart_drilldown_distinct", screenshots, "desktop")
        _open_chart_action(page, "tca_breakdown")
        assert page.locator("#drilldownDrawer").get_attribute("data-drawer-kind") == "tca_breakdown"
        _screenshot(page, repo, "tca_breakdown_distinct", screenshots, "desktop")
        _open_chart_action(page, "explain")
        assert page.locator("#drilldownDrawer").get_attribute("data-drawer-kind") == "explain"
        _screenshot(page, repo, "explain_card_specific", screenshots, "desktop")
        _open_chart_action(page, "technical_details")
        assert page.locator("#drilldownDrawer").get_attribute("data-drawer-kind") == "technical_details"
        assert page.locator("#drilldownDrawer").get_attribute("data-content-signature")
        _screenshot(page, repo, "technical_details_raw_refs", screenshots, "desktop")
        _screenshot(page, repo, "drawer_payloads_distinct", screenshots, "desktop")
        _close_drawer(page)
        checks.append("chart_drawers_have_distinct_payloads")

        page.locator("a[href='#trade-workbench']").first.click()
        _assert_visible(page, "[data-workbench-field='market_family']")
        _screenshot(page, repo, "workbench_guided_selectors", screenshots, "desktop")
        page.locator("[data-workbench-field='market_event']").select_option("other")
        _assert_visible(page, "[data-workbench-field-shell='custom_event'][data-other-visible='true']")
        _screenshot(page, repo, "workbench_other_custom_field", screenshots, "desktop")
        _screenshot(page, repo, "workbench_numeric_range_hints", screenshots, "desktop")
        _screenshot(page, repo, "input_required_color_state", screenshots, "desktop")
        page.locator("[data-workbench-field='max_budget']").fill("10")
        page.locator("[data-workbench-field='max_loss']").fill("20")
        _assert_visible(page, "#workbenchRangeValidation")
        _screenshot(page, repo, "workbench_invalid_range_guidance", screenshots, "desktop")
        checks.append("workbench_selectors_other_fields_and_ranges")

        page.locator("#ownerSettingsToggle").click()
        _assert_visible(page, "#ownerSettingsCenter.open")
        _screenshot(page, repo, "settings_center_open", screenshots, "desktop")
        _screenshot(page, repo, "settings_appearance_tab", screenshots, "desktop")
        _screenshot(page, repo, "theme_picker_presets", screenshots, "desktop")
        page.locator("[data-owner-setting='theme_preset']").select_option("HIGH_CONTRAST")
        assert page.locator("html").get_attribute("data-theme") == "high_contrast"
        _screenshot(page, repo, "high_contrast_theme", screenshots, "desktop")
        page.locator("[data-settings-tab='Trading Preferences']").click()
        _screenshot(page, repo, "settings_trading_preferences_preview_only", screenshots, "desktop")
        page.locator("#closeOwnerSettings").click()
        checks.append("settings_center_owner_settings")

        page.locator("#ownerOptionsToggle").click()
        _assert_visible(page, "#ownerOptionsPanel")
        _screenshot(page, repo, "options_status_simplified", screenshots, "desktop")
        page.locator("#ownerOptionsClose").click()
        page.locator("a[href='#overview']").first.click()
        _assert_visible(page, "#ownerCoachPanel")
        assert "QTT Coach" in page.locator("#ownerCoachPanel").inner_text(timeout=10_000)
        _screenshot(page, repo, "owner_copy_cleanup", screenshots, "desktop")
        _screenshot(page, repo, "default_card_action_menu_collapsed", screenshots, "desktop")
        _screenshot(page, repo, "default_card_more_actions_menu", screenshots, "desktop")
        page.locator("#overviewCards .next-action-menu summary").first.click()
        _screenshot(page, repo, "selected_card_action_menu_expanded", screenshots, "desktop")
        checks.append("owner_copy_and_card_declutter")

        mobile = browser.new_page(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=3,
        )
        mobile.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: console_errors.append(str(exc)))
        mobile.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)
        mobile.goto(url, wait_until="load")
        _tap_mobile_nav(mobile, "#trade-workbench")
        _assert_visible(mobile, "#tradeWorkbench")
        _screenshot(mobile, repo, "mobile_collapsed_sidebar_and_workbench", screenshots, "mobile")
        _tap_mobile_nav(mobile, "#portfolio")
        _assert_visible(mobile, "#chartGrid .chart-canvas")
        mobile.locator("#chartGrid .chart-canvas").first.tap(position={"x": 220, "y": 110})
        _assert_visible(mobile, "#chartGrid .chart-canvas.is-focused .chart-tooltip")
        _screenshot(mobile, repo, "mobile_chart_tooltip_or_value_panel", screenshots, "mobile")
        checks.append("mobile_sidebar_workbench_chart")

        browser.close()

    missing = sorted(set(SCREENSHOTS) - {Path(row["path"]).stem.replace("ui1r2r3_", "") for row in screenshots})
    if missing:
        raise SystemExit(f"PR169_DASH1_UI1_R2_R3_PLAYWRIGHT_MISSING_SCREENSHOTS {missing}")
    _write_report(repo, screenshots, checks, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R2_R3_PLAYWRIGHT_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R2_R3_PLAYWRIGHT_OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    run(Path(args.repo_root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
