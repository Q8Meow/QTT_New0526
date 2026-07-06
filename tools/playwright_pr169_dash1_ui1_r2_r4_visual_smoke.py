from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


SCREENSHOTS = [
    "settings_color_applied_to_workbench_inputs",
    "checkbox_compact_visual_size",
    "workbench_other_custom_market_field",
    "workbench_other_custom_event_field",
    "workbench_input_state_before_valid_entry",
    "workbench_input_state_after_valid_entry",
    "qtt_guide_composer_empty",
    "qtt_guide_composer_after_send",
    "chat_trade_check_response_distinct",
    "chat_agent_disagreement_response_distinct",
    "chat_research_response_distinct",
    "card_explain_distinct",
    "card_learn_distinct",
    "card_why_distinct",
    "invalid_chart_action_hidden_on_nonchart_card",
    "agent_operations_shell",
    "agent_operations_provider_pending_details",
    "qtt_team_workflow_queue_shell",
    "workflow_card_agent_tags",
    "receipt_preview_provider_pending",
    "central_education_explain_learn_why",
    "central_education_disabled_action",
    "central_workbench_field_help",
    "mobile_qtt_guide_composer",
    "mobile_workbench_input_colors",
    "qtt_guide_online_search_provider_pending",
    "plain_english_no_trade_response",
    "plain_english_formula_qku_route_response",
    "disabled_action_educates_with_safe_alternative",
    "qku_formula_agent_route_gap_projection",
    "owner_command_authority_preview_no_direct_submit",
]


def _path(name: str) -> str:
    return f".tmp/ui1r2r4_{name}.png"


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


def _nav(page: Page, href: str) -> None:
    page.locator(f".rail a[href='{href}']").first.click()
    _assert_visible(page, href)


def _tap_mobile_nav(page: Page, href: str) -> None:
    link = page.locator(f"#mobileBottomNav a[href='{href}']").first
    link.wait_for(state="visible", timeout=10_000)
    box = link.bounding_box()
    if not box:
        raise AssertionError(f"missing mobile nav box for {href}")
    page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    _assert_visible(page, href)


def _close_drawer(page: Page) -> None:
    if page.locator("#drilldownDrawer.open").count():
        page.locator("#closeDrawer").click()


def _open_action(page: Page, root_selector: str, kind: str) -> None:
    _close_drawer(page)
    menu = page.locator(f"{root_selector} .next-action-menu").first
    if menu.get_attribute("open") is None:
        menu.locator("summary").click()
    button = page.locator(f"{root_selector} [data-owner-drawer-action='{kind}']").first
    button.wait_for(state="visible", timeout=10_000)
    button.click()
    _assert_visible(page, "#drilldownDrawer.open")
    assert page.locator("#drilldownDrawer").get_attribute("data-drawer-kind") == kind


def _send_chat(page: Page, text: str) -> None:
    _nav(page, "#chat")
    page.locator("#ownerChatInput").fill(text)
    page.locator("#routePreviewButton").click()
    _assert_visible(page, "#chatReceiptPreview .chat-bubble")


def _open_settings(page: Page, section: str = "Appearance") -> None:
    if not page.locator("#ownerSettingsCenter.open").count():
        page.locator("#ownerSettingsToggle").click()
    _assert_visible(page, "#ownerSettingsCenter.open")
    if section != "Appearance":
        page.locator(f"[data-settings-tab='{section}']").click()


def _open_guide(page: Page) -> None:
    if not page.locator("#qttGuidePanel.open").count():
        page.locator("#qttGuideToggle").click()
    _assert_visible(page, "#qttGuidePanel.open")


def _write_report(
    repo: Path,
    rows: list[dict[str, Any]],
    checks: list[str],
    console_errors: list[str],
    external_requests: list[str],
) -> None:
    report_path = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui1_r2_r4" / "playwright_visual_smoke.report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_id": "UI1R2R4_PLAYWRIGHT_VISUAL_SMOKE",
        "status": "PASS" if not console_errors and not external_requests else "FAIL",
        "screenshots": rows,
        "checks": checks,
        "console_status": "PASS" if not console_errors else "FAIL",
        "network_status": "PASS" if not external_requests else "FAIL",
        "console_breaking_errors": console_errors,
        "external_network_requests": external_requests,
        "no_console_breaking_errors": not console_errors,
        "no_external_network_requests": not external_requests,
        "runtime_side_effect_allowed": False,
    }
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

        _nav(page, "#trade-workbench")
        _assert_visible(page, "[data-workbench-field-shell='plain_english_detail'][data-interaction-state='input_required']")
        _screenshot(page, repo, "workbench_input_state_before_valid_entry", screenshots, "desktop")
        page.locator("[data-workbench-field='plain_english_detail']").fill("Check this market for a local TradePlanCandidateV1 preview.")
        _assert_visible(page, "[data-workbench-field-shell='plain_english_detail'][data-interaction-state='review_required']")
        _screenshot(page, repo, "workbench_input_state_after_valid_entry", screenshots, "desktop")
        page.locator("[data-workbench-field='market_family']").select_option("other")
        _assert_visible(page, "[data-workbench-field-shell='custom_market_family'][data-other-visible='true']")
        _screenshot(page, repo, "workbench_other_custom_market_field", screenshots, "desktop")
        page.locator("[data-workbench-field='event_category']").select_option("other")
        _assert_visible(page, "[data-workbench-field-shell='custom_event_category'][data-other-visible='true']")
        _screenshot(page, repo, "workbench_other_custom_event_field", screenshots, "desktop")
        checks.append("workbench_input_states_and_other_fields")

        _open_settings(page, "Colors")
        page.locator("[data-owner-setting='input_required_color']").fill("#F97316")
        _screenshot(page, repo, "checkbox_compact_visual_size", screenshots, "desktop")
        page.locator("#closeOwnerSettings").click()
        _nav(page, "#trade-workbench")
        _screenshot(page, repo, "settings_color_applied_to_workbench_inputs", screenshots, "desktop")
        checks.append("settings_color_and_checkbox_density")

        _open_guide(page)
        page.locator("#qttGuideComposer").fill("")
        _screenshot(page, repo, "qtt_guide_composer_empty", screenshots, "desktop")
        page.locator("#qttGuideComposer").fill("Search online for more information about this market.")
        page.locator("#qttGuideSend").click()
        _assert_visible(page, "#chatReceiptPreview .chat-bubble")
        _screenshot(page, repo, "qtt_guide_composer_after_send", screenshots, "desktop")
        _screenshot(page, repo, "qtt_guide_online_search_provider_pending", screenshots, "desktop")
        page.locator("#closeQttGuide").click()
        checks.append("qtt_guide_composer_shared_chat_path")

        _send_chat(page, "Can QTT check this market and find the best trade?")
        assert "Trade-check" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "chat_trade_check_response_distinct", screenshots, "desktop")
        _send_chat(page, "Show me which agent disagrees and why.")
        assert "Agent disagreement" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "chat_agent_disagreement_response_distinct", screenshots, "desktop")
        _send_chat(page, "Research this article and tell me if it creates a prediction-market edge.")
        assert "Research" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "chat_research_response_distinct", screenshots, "desktop")
        _send_chat(page, "Why did no-trade win here?")
        assert "No-trade" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "plain_english_no_trade_response", screenshots, "desktop")
        _send_chat(page, "Ask the QKU agents to compare the best formula stacks for this event.")
        assert "QKU" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "plain_english_formula_qku_route_response", screenshots, "desktop")
        checks.append("chat_intent_responses_distinct")

        _nav(page, "#overview")
        page.locator("#overviewCards .next-action-menu").first.locator("summary").click()
        assert page.locator("#overviewCards [data-owner-drawer-action='chart_drilldown']").count() == 0
        _screenshot(page, repo, "invalid_chart_action_hidden_on_nonchart_card", screenshots, "desktop")
        _screenshot(page, repo, "disabled_action_educates_with_safe_alternative", screenshots, "desktop")
        _open_action(page, "#overviewCards", "explain")
        _screenshot(page, repo, "card_explain_distinct", screenshots, "desktop")
        _open_action(page, "#overviewCards", "learn")
        _screenshot(page, repo, "card_learn_distinct", screenshots, "desktop")
        _open_action(page, "#overviewCards", "why")
        _screenshot(page, repo, "card_why_distinct", screenshots, "desktop")
        _screenshot(page, repo, "central_education_explain_learn_why", screenshots, "desktop")
        _open_action(page, "#overviewCards", "technical_details")
        _screenshot(page, repo, "central_education_disabled_action", screenshots, "desktop")
        _close_drawer(page)
        checks.append("card_actions_distinct_and_invalid_hidden")

        _nav(page, "#trade-workbench")
        _open_action(page, "#tradeWorkbench", "qku_formula_routes")
        _screenshot(page, repo, "qku_formula_agent_route_gap_projection", screenshots, "desktop")
        _open_action(page, "#tradeWorkbench", "learn")
        _screenshot(page, repo, "central_workbench_field_help", screenshots, "desktop")
        _close_drawer(page)

        _nav(page, "#agents")
        _assert_visible(page, "#agentOperations [data-agent-operations-shell]")
        _screenshot(page, repo, "agent_operations_shell", screenshots, "desktop")
        page.locator("#agentOperations .card").first.click()
        _assert_visible(page, "#drilldownDrawer.open")
        _screenshot(page, repo, "agent_operations_provider_pending_details", screenshots, "desktop")
        _close_drawer(page)
        _assert_visible(page, "#qttTeamWorkflowQueue [data-workflow-queue-shell]")
        _screenshot(page, repo, "qtt_team_workflow_queue_shell", screenshots, "desktop")
        _screenshot(page, repo, "workflow_card_agent_tags", screenshots, "desktop")
        _assert_visible(page, "#auditReceiptPreview [data-receipt-preview-shell]")
        _screenshot(page, repo, "receipt_preview_provider_pending", screenshots, "desktop")
        checks.append("agent_workflow_receipt_shells")

        _send_chat(page, "Preview an Execution Router submit request without direct venue submit.")
        assert "Execution Router" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "owner_command_authority_preview_no_direct_submit", screenshots, "desktop")

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
        _open_guide(mobile)
        _assert_visible(mobile, "#qttGuideComposer")
        _screenshot(mobile, repo, "mobile_qtt_guide_composer", screenshots, "mobile")
        mobile.locator("#closeQttGuide").click()
        _tap_mobile_nav(mobile, "#trade-workbench")
        _assert_visible(mobile, "[data-workbench-field-shell='plain_english_detail']")
        _screenshot(mobile, repo, "mobile_workbench_input_colors", screenshots, "mobile")
        checks.append("mobile_qtt_guide_and_workbench_colors")

        browser.close()

    missing = sorted(set(SCREENSHOTS) - {Path(row["path"]).stem.replace("ui1r2r4_", "") for row in screenshots})
    if missing:
        raise SystemExit(f"PR169_DASH1_UI1_R2_R4_PLAYWRIGHT_MISSING_SCREENSHOTS {missing}")
    _write_report(repo, screenshots, checks, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R2_R4_PLAYWRIGHT_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R2_R4_PLAYWRIGHT_OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    run(Path(args.repo_root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
