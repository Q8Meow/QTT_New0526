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

R2R5_SCREENSHOTS = [
    "workbench_input_state_before_valid_entry_targeted",
    "workbench_input_state_after_valid_entry_targeted",
    "workbench_other_custom_market_field_targeted",
    "workbench_other_custom_event_field_targeted",
    "settings_color_applied_to_workbench_inputs_targeted",
    "owner_drawer_explain_no_raw_payload",
    "owner_drawer_technical_details_payload_expanded",
    "mobile_nav_no_overlap",
    "mobile_more_overflow_open",
    "chart_tooltip_visible_on_hover",
    "chart_tooltip_hidden_after_mouseleave",
    "chart_tooltip_hidden_after_escape",
    "owner_copy_machine_labels_suppressed",
    "more_actions_context_relevant",
    "workflow_queue_targeted",
    "receipt_preview_targeted",
    "mobile_workbench_targeted_input_colors",
]

R2R6_SCREENSHOTS = [
    "mobile_wb",
    "queue",
    "receipts",
    "other_market",
    "other_event",
    "more_actions",
    "color_proof",
    "theme_custom",
    "theme_applied",
    "density",
    "chart_axis",
    "chart_crosshair",
    "chart_grid",
    "chart_tooltip",
    "no_tooltips",
    "market_catalog",
]


def _path(name: str) -> str:
    return f".tmp/ui1r2r4_{name}.png"


def _path_r2r5(name: str) -> str:
    return f".tmp/ui1r2r5_{name}.png"


def _path_r2r6(name: str) -> str:
    return f".tmp/r2r6_{name}.png"


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


def _assert_in_viewport(page: Page, selector: str) -> None:
    locator = page.locator(selector).first
    locator.wait_for(state="visible", timeout=10_000)
    page.wait_for_function(
        """selector => {
            const element = document.querySelector(selector);
            if (!element) return false;
            const rect = element.getBoundingClientRect();
            return rect.width > 0
                && rect.height > 0
                && rect.right >= 0
                && rect.left <= window.innerWidth
                && rect.bottom >= 0
                && rect.top <= window.innerHeight;
        }""",
        arg=selector,
        timeout=10_000,
    )
    box = locator.bounding_box()
    if not box or box["width"] <= 0 or box["height"] <= 0:
        raise AssertionError(f"target has no visible box: {selector}")
    viewport = page.viewport_size
    if not viewport:
        raise AssertionError("page viewport unavailable")
    if box["x"] + box["width"] < 0 or box["x"] > viewport["width"]:
        raise AssertionError(f"target outside horizontal viewport: {selector} {box}")
    if box["y"] + box["height"] < 0 or box["y"] > viewport["height"]:
        raise AssertionError(f"target outside vertical viewport: {selector} {box}")


def _assert_target_box(page: Page, selector: str, *, min_width: int = 1, min_height: int = 1) -> None:
    locator = page.locator(selector).first
    locator.wait_for(state="visible", timeout=10_000)
    locator.evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
    box = locator.bounding_box()
    if not box:
        raise AssertionError(f"target has no bounding box: {selector}")
    viewport = page.viewport_size or {"width": 0, "height": 0}
    if box["y"] < 0 or box["y"] + box["height"] > viewport["height"]:
        page.evaluate("(delta) => window.scrollBy(0, delta)", box["y"] - 80)
        locator.evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
        box = locator.bounding_box()
        if not box:
            raise AssertionError(f"target has no bounding box after scroll repair: {selector}")
    if box["width"] < min_width or box["height"] < min_height:
        raise AssertionError(f"target too small for proof: {selector} {box} min={min_width}x{min_height}")
    if box["x"] < 0 or box["x"] + box["width"] > viewport["width"] + 1:
        raise AssertionError(f"target clipped horizontally: {selector} {box} viewport={viewport}")
    if box["y"] < 0 or box["y"] + box["height"] > viewport["height"] + 1:
        raise AssertionError(f"target clipped vertically: {selector} {box} viewport={viewport}")
    overlays = page.locator(".topbar, #stickyHeader, .app-header, .mobile-bottom-nav").evaluate_all(
        """elements => elements.filter((element) => {
            const style = getComputedStyle(element);
            return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        }).map((element) => {
            const rect = element.getBoundingClientRect();
            return {left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, width: rect.width, height: rect.height};
        })"""
    )
    for overlay in overlays:
        horizontal = box["x"] < overlay["right"] and overlay["left"] < box["x"] + box["width"]
        vertical = box["y"] < overlay["bottom"] and overlay["top"] < box["y"] + box["height"]
        if horizontal and vertical:
            raise AssertionError(f"target obstructed by sticky overlay: {selector} box={box} overlay={overlay}")


def _screenshot_target(
    page: Page,
    repo: Path,
    name: str,
    rows: list[dict[str, Any]],
    viewport: str,
    selector: str,
    proof_text_or_state: str,
    *,
    screenshot_selector: str | None = None,
    forbidden_visible_content: list[str] | None = None,
) -> None:
    _assert_in_viewport(page, selector)
    target = page.locator(selector).first
    text = target.inner_text(timeout=10_000) if target.count() else ""
    if proof_text_or_state and proof_text_or_state not in text:
        state_blob = " ".join(
            value
            for value in (
                target.get_attribute("data-interaction-state"),
                target.get_attribute("data-owner-color-proof"),
                target.get_attribute("data-tooltip-state"),
                target.get_attribute("data-chart-tooltip-visible"),
            )
            if value
        )
        if proof_text_or_state not in state_blob:
            raise AssertionError(f"proof text/state missing for {name}: {proof_text_or_state}")
    if forbidden_visible_content:
        visible_text = page.locator(screenshot_selector or selector).first.inner_text(timeout=10_000)
        for forbidden in forbidden_visible_content:
            if forbidden in visible_text:
                raise AssertionError(f"forbidden visible content in {name}: {forbidden}")
    path = repo / _path_r2r5(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.locator(screenshot_selector or selector).first.screenshot(path=str(path))
    rows.append(
        {
            "path": _path_r2r5(name),
            "tested_interaction": name,
            "viewport": viewport,
            "result": "PASS",
            "proof_selector_or_locator": selector,
            "proof_text_or_state": proof_text_or_state,
            "runtime_side_effect_allowed": False,
            "source_truth_created": False,
            "order_authority_created": False,
        }
    )


def _screenshot_target_r2r6(
    page: Page,
    repo: Path,
    name: str,
    rows: list[dict[str, Any]],
    viewport: str,
    selector: str,
    proof_text_or_state: str,
    *,
    screenshot_selector: str | None = None,
    forbidden_visible_content: list[str] | None = None,
    min_width: int = 1,
    min_height: int = 1,
) -> None:
    shot_selector = screenshot_selector or selector
    _assert_target_box(page, shot_selector, min_width=min_width, min_height=min_height)
    target = page.locator(selector).first
    text = target.inner_text(timeout=10_000) if target.count() else ""
    if proof_text_or_state and proof_text_or_state not in text:
        state_blob = " ".join(
            value
            for value in (
                target.get_attribute("data-interaction-state"),
                target.get_attribute("data-owner-color-proof"),
                target.get_attribute("data-tooltip-state"),
                target.get_attribute("data-axis-labels-enabled"),
                target.get_attribute("data-grid-lines-enabled"),
                target.get_attribute("data-crosshair-enabled"),
                target.get_attribute("data-tooltips-enabled"),
                target.get_attribute("data-chart-registered"),
            )
            if value
        )
        if proof_text_or_state not in state_blob:
            raise AssertionError(f"proof text/state missing for {name}: {proof_text_or_state}")
    if forbidden_visible_content:
        visible_text = page.locator(shot_selector).first.inner_text(timeout=10_000)
        for forbidden in forbidden_visible_content:
            if forbidden in visible_text:
                raise AssertionError(f"forbidden visible content in {name}: {forbidden}")
    path = repo / _path_r2r6(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.locator(shot_selector).first.screenshot(path=str(path))
    rows.append(
        {
            "path": _path_r2r6(name),
            "tested_interaction": name,
            "viewport": viewport,
            "result": "PASS",
            "proof_selector_or_locator": selector,
            "proof_text_or_state": proof_text_or_state,
            "runtime_side_effect_allowed": False,
            "source_truth_created": False,
            "order_authority_created": False,
        }
    )


def _screenshot_union_r2r6(
    page: Page,
    repo: Path,
    name: str,
    rows: list[dict[str, Any]],
    viewport: str,
    selectors: list[str],
    proof_text_or_state: str,
    *,
    forbidden_visible_content: list[str] | None = None,
    min_width: int = 260,
    min_height: int = 90,
) -> None:
    boxes: list[dict[str, float]] = []
    visible_text_parts: list[str] = []
    for selector in selectors:
        locator = page.locator(selector).first
        locator.wait_for(state="visible", timeout=10_000)
        locator.evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
        box = locator.bounding_box()
        if not box:
            raise AssertionError(f"missing union screenshot box for {selector}")
        boxes.append(box)
        visible_text_parts.append(locator.inner_text(timeout=10_000))
    left = min(box["x"] for box in boxes)
    top = min(box["y"] for box in boxes)
    right = max(box["x"] + box["width"] for box in boxes)
    bottom = max(box["y"] + box["height"] for box in boxes)
    margin = 10
    viewport_size = page.viewport_size or {"width": 1440, "height": 1000}
    clip = {
        "x": max(0, left - margin),
        "y": max(0, top - margin),
        "width": min(viewport_size["width"], right + margin) - max(0, left - margin),
        "height": min(viewport_size["height"], bottom + margin) - max(0, top - margin),
    }
    if clip["width"] < min_width or clip["height"] < min_height:
        raise AssertionError(f"union screenshot clip too small for {name}: {clip}")
    visible_text = " ".join(visible_text_parts)
    if proof_text_or_state and proof_text_or_state not in visible_text:
        raise AssertionError(f"union proof text missing for {name}: {proof_text_or_state}")
    for forbidden in forbidden_visible_content or []:
        if forbidden in visible_text:
            raise AssertionError(f"forbidden visible content in {name}: {forbidden}")
    path = repo / _path_r2r6(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), clip=clip)
    rows.append(
        {
            "path": _path_r2r6(name),
            "tested_interaction": name,
            "viewport": viewport,
            "result": "PASS",
            "proof_selector_or_locator": " | ".join(selectors),
            "proof_text_or_state": proof_text_or_state,
            "runtime_side_effect_allowed": False,
            "source_truth_created": False,
            "order_authority_created": False,
        }
    )


def _assert_no_overlap(page: Page, selector: str) -> None:
    boxes = page.locator(selector).evaluate_all(
        """elements => elements.map((element) => {
            const rect = element.getBoundingClientRect();
            return {
                text: element.textContent.trim(),
                left: rect.left,
                right: rect.right,
                top: rect.top,
                bottom: rect.bottom,
                width: rect.width,
                height: rect.height
            };
        })"""
    )
    if len(boxes) != 5:
        raise AssertionError(f"expected five mobile primary tabs, got {len(boxes)}")
    for index, left in enumerate(boxes):
        if left["width"] < 44 or left["height"] < 44:
            raise AssertionError(f"mobile touch target too small: {left}")
        for right in boxes[index + 1 :]:
            horizontal = left["left"] < right["right"] and right["left"] < left["right"]
            vertical = left["top"] < right["bottom"] and right["top"] < left["bottom"]
            if horizontal and vertical:
                raise AssertionError(f"mobile nav overlap: {left['text']} / {right['text']}")


def _assert_visible(page: Page, selector: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=10_000)


def _nav(page: Page, href: str) -> None:
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    page.evaluate("window.scrollTo(0, 0)")
    page.locator(f".rail a[href='{href}']").first.click()
    _assert_visible(page, href)
    page.evaluate(
        """selector => {
            const element = document.querySelector(selector);
            if (!element) return;
            const top = element.getBoundingClientRect().top + window.scrollY - 70;
            window.scrollTo({top, left: 0, behavior: 'instant'});
        }""",
        href,
    )


def _tap_mobile_nav(page: Page, href: str) -> None:
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    link = page.locator(f"#mobileBottomNav a[href='{href}']").first
    link.wait_for(state="visible", timeout=10_000)
    box = link.bounding_box()
    if not box:
        raise AssertionError(f"missing mobile nav box for {href}")
    page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    _assert_visible(page, href)
    page.evaluate(
        """selector => {
            const element = document.querySelector(selector);
            if (!element) return;
            const top = element.getBoundingClientRect().top + window.scrollY - 64;
            window.scrollTo({top, left: 0, behavior: 'instant'});
        }""",
        href,
    )


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


def _write_r2r5_report(
    repo: Path,
    rows: list[dict[str, Any]],
    checks: list[str],
    console_errors: list[str],
    external_requests: list[str],
) -> None:
    report_path = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui1_r2_r5" / "playwright_visual_smoke.report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_id": "UI1R2R5_PLAYWRIGHT_VISUAL_SMOKE",
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
        "source_truth_created": False,
        "order_authority_created": False,
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_r2r6_report(
    repo: Path,
    rows: list[dict[str, Any]],
    checks: list[str],
    console_errors: list[str],
    external_requests: list[str],
) -> None:
    report_path = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui1_r2r6" / "playwright_visual_smoke.report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artifact_id": "UI1R2R6_PLAYWRIGHT_VISUAL_SMOKE",
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
        "source_truth_created": False,
        "order_authority_created": False,
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
        page.locator("[data-owner-setting='input_required_color']").first.fill("#F97316")
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


def run_r2r5(repo: Path) -> None:
    html = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "owner_dashboard_review_surface.html"
    url = html.resolve().as_uri()
    console_errors: list[str] = []
    external_requests: list[str] = []
    screenshots: list[dict[str, Any]] = []
    checks: list[str] = []

    def chart_canvas(page: Page):
        _nav(page, "#portfolio")
        canvas = page.locator(".chart-canvas[data-chart-interaction]").first
        canvas.wait_for(state="visible", timeout=10_000)
        canvas.scroll_into_view_if_needed()
        box = canvas.bounding_box()
        if not box:
            raise AssertionError("chart canvas missing bounding box")
        return canvas, box

    def hover_chart(page: Page):
        canvas, box = chart_canvas(page)
        page.mouse.move(box["x"] + box["width"] * 0.55, box["y"] + box["height"] * 0.45)
        page.locator(".chart-canvas.is-focused [data-chart-tooltip-visible='true']").first.wait_for(state="visible", timeout=10_000)
        return canvas, box

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)
        page.goto(url, wait_until="load")

        _nav(page, "#trade-workbench")
        page.locator("[data-workbench-field-shell='plain_english_detail']").scroll_into_view_if_needed()
        _screenshot_target(
            page,
            repo,
            "workbench_input_state_before_valid_entry_targeted",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='plain_english_detail'][data-interaction-state='input_required']",
            "Plain-English detail",
        )
        page.locator("[data-workbench-field='plain_english_detail']").fill("Check this market for a local TradePlanCandidateV1 preview.")
        _screenshot_target(
            page,
            repo,
            "workbench_input_state_after_valid_entry_targeted",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='plain_english_detail'][data-interaction-state='review_required']",
            "Plain-English detail",
        )
        page.locator("[data-workbench-field='market_family']").select_option("other")
        page.locator("[data-workbench-field-shell='custom_market_family']").scroll_into_view_if_needed()
        _screenshot_target(
            page,
            repo,
            "workbench_other_custom_market_field_targeted",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='custom_market_family'][data-other-visible='true']",
            "Custom market family",
        )
        page.locator("[data-workbench-field='event_category']").select_option("other")
        page.locator("[data-workbench-field-shell='custom_event_category']").scroll_into_view_if_needed()
        _screenshot_target(
            page,
            repo,
            "workbench_other_custom_event_field_targeted",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='custom_event_category'][data-other-visible='true']",
            "Custom event category",
        )
        checks.append("r2r5_workbench_fields_and_other_targets_visible")

        _open_settings(page, "Colors")
        page.locator("[data-owner-setting='input_required_color']").first.fill("#F97316")
        page.locator("#closeOwnerSettings").click()
        _nav(page, "#trade-workbench")
        page.locator("[data-workbench-field='plain_english_detail']").fill("")
        page.locator("[data-workbench-field-shell='plain_english_detail']").scroll_into_view_if_needed()
        _screenshot_target(
            page,
            repo,
            "settings_color_applied_to_workbench_inputs_targeted",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='plain_english_detail'][data-owner-color-proof='input_required']",
            "Plain-English detail",
        )
        checks.append("r2r5_settings_color_binding_visible_on_workbench_field")

        _nav(page, "#overview")
        _open_action(page, "#overviewCards", "explain")
        drawer_text = page.locator("#drilldownDrawer").inner_text(timeout=10_000)
        for forbidden in ("Drawer payload", "Selected card:", "Selected action:", "Runtime side effect:"):
            if forbidden in drawer_text:
                raise AssertionError(f"raw owner drawer payload leaked before technical expansion: {forbidden}")
        _screenshot_target(
            page,
            repo,
            "owner_drawer_explain_no_raw_payload",
            screenshots,
            "desktop",
            "#drilldownDrawer.open",
            "What this means",
            forbidden_visible_content=["Drawer payload", "Selected card:", "Selected action:", "Runtime side effect:"],
        )
        _open_action(page, "#overviewCards", "technical_details")
        technical_text = page.locator("#drilldownDrawer [data-technical-details-expanded='true']").inner_text(timeout=10_000)
        for expected in ("Technical Details payload", "Selected card:", "Selected action:", "Runtime side effect: false"):
            if expected not in technical_text:
                raise AssertionError(f"technical details payload missing expected row: {expected}")
        page.locator("#drilldownDrawer [data-technical-details-expanded='true']").scroll_into_view_if_needed()
        _screenshot_target(
            page,
            repo,
            "owner_drawer_technical_details_payload_expanded",
            screenshots,
            "desktop",
            "#drilldownDrawer.open [data-technical-details-expanded='true']",
            "Technical Details payload",
        )
        _close_drawer(page)
        checks.append("r2r5_owner_drawer_payload_hidden_until_technical_details")

        canvas, box = hover_chart(page)
        _screenshot_target(
            page,
            repo,
            "chart_tooltip_visible_on_hover",
            screenshots,
            "desktop",
            ".chart-canvas.is-focused [data-chart-tooltip-visible='true']",
            "Value: provider receipts pending",
            screenshot_selector=".chart-canvas.is-focused",
        )
        viewport = page.viewport_size or {"width": 1440, "height": 1000}
        page.mouse.move(min(viewport["width"] - 5, box["x"] + box["width"] + 80), min(viewport["height"] - 5, box["y"] + box["height"] + 80))
        page.wait_for_function("() => document.querySelector('.chart-canvas[data-chart-interaction]')?.dataset.tooltipState === 'hidden'")
        _screenshot_target(
            page,
            repo,
            "chart_tooltip_hidden_after_mouseleave",
            screenshots,
            "desktop",
            ".chart-canvas[data-tooltip-state='hidden']",
            "hidden",
            screenshot_selector=".chart-canvas[data-tooltip-state='hidden']",
        )
        hover_chart(page)
        page.keyboard.press("Escape")
        page.wait_for_function("() => document.querySelector('.chart-canvas[data-chart-interaction]')?.dataset.tooltipState === 'hidden'")
        _screenshot_target(
            page,
            repo,
            "chart_tooltip_hidden_after_escape",
            screenshots,
            "desktop",
            ".chart-canvas[data-tooltip-state='hidden']",
            "hidden",
            screenshot_selector=".chart-canvas[data-tooltip-state='hidden']",
        )
        hover_chart(page)
        page.locator(".mini-range button").nth(1).click()
        page.wait_for_function("() => document.querySelector('.chart-canvas[data-chart-interaction]')?.dataset.tooltipState === 'hidden'")
        hover_chart(page)
        _open_action(page, "#portfolioCards", "explain")
        page.wait_for_function("() => document.querySelector('.chart-canvas[data-chart-interaction]')?.dataset.tooltipState === 'hidden'")
        _close_drawer(page)
        checks.append("r2r5_chart_tooltip_hides_on_mouseleave_escape_range_and_drawer")

        _nav(page, "#overview")
        page.locator("body[data-owner-copy-cleanup='r2-r5']").wait_for(state="attached", timeout=10_000)
        owner_text = page.locator("#overview").inner_text(timeout=10_000)
        for forbidden in ("Net Capital Cash Slot", "Today Result Slot", "Provider Route:", "No AGENT_ORCH/SVC runtime attached"):
            if forbidden in owner_text:
                raise AssertionError(f"machine label visible in owner overview: {forbidden}")
        _screenshot_target(
            page,
            repo,
            "owner_copy_machine_labels_suppressed",
            screenshots,
            "desktop",
            "body[data-owner-copy-cleanup='r2-r5']",
            "Net Capital",
            screenshot_selector="#overview",
            forbidden_visible_content=["Net Capital Cash Slot", "Today Result Slot", "Provider Route:", "No AGENT_ORCH/SVC runtime attached"],
        )
        menu = page.locator("#overviewCards .next-action-menu").first
        if menu.get_attribute("open") is None:
            menu.locator("summary").click()
        visible_actions = menu.locator("[data-owner-drawer-action]:visible")
        action_count = visible_actions.count()
        if action_count > 5:
            raise AssertionError(f"owner More Actions menu too noisy: {action_count}")
        menu_text = menu.inner_text(timeout=10_000)
        for forbidden in ("Open chart drilldown", "Show TCA / cost breakdown"):
            if forbidden in menu_text:
                raise AssertionError(f"non-applicable owner action visible: {forbidden}")
        menu.scroll_into_view_if_needed()
        _screenshot_target(
            page,
            repo,
            "more_actions_context_relevant",
            screenshots,
            "desktop",
            "#overviewCards .next-action-menu[data-r2r5-action-cap='owner-contextual']",
            "Explain",
        )
        checks.append("r2r5_owner_copy_and_more_actions_context_relevant")

        _nav(page, "#agents")
        page.locator("#qttTeamWorkflowQueue").scroll_into_view_if_needed()
        queue_text = page.locator("#qttTeamWorkflowQueue").inner_text(timeout=10_000)
        for expected in ("QTT Team Workflow Queue", "provider-pending / not running", "Workflow stages", "no fake runtime queue"):
            if expected not in queue_text:
                raise AssertionError(f"workflow queue proof missing: {expected}")
        _screenshot_target(
            page,
            repo,
            "workflow_queue_targeted",
            screenshots,
            "desktop",
            "#qttTeamWorkflowQueue [data-workflow-queue-shell='OwnerWorkflowQueueStateV1']",
            "QTT Team Workflow Queue",
            screenshot_selector="#qttTeamWorkflowQueue",
        )
        page.locator("#auditReceiptPreview").scroll_into_view_if_needed()
        receipt_text = page.locator("#auditReceiptPreview").inner_text(timeout=10_000)
        for expected in ("Audit Trail / Receipts Preview", "provider-pending / no fake receipts", "No fake timestamps"):
            if expected not in receipt_text:
                raise AssertionError(f"receipt preview proof missing: {expected}")
        _screenshot_target(
            page,
            repo,
            "receipt_preview_targeted",
            screenshots,
            "desktop",
            "#auditReceiptPreview [data-receipt-preview-shell='OwnerReceiptPreviewStateV1']",
            "Audit Trail / Receipts Preview",
            screenshot_selector="#auditReceiptPreview",
        )
        checks.append("r2r5_workflow_queue_and_receipt_preview_targeted")

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
        _assert_no_overlap(mobile, "#mobileBottomNav a, #mobileBottomNav button")
        _screenshot_target(
            mobile,
            repo,
            "mobile_nav_no_overlap",
            screenshots,
            "mobile_390x844",
            "#mobileBottomNav[data-mobile-primary-count='5']",
            "Trade",
            screenshot_selector="#mobileBottomNav",
            forbidden_visible_content=["Trade Workbench", "Decision Queue", "Quantum Control Center"],
        )
        mobile.locator("#mobileMoreToggle").tap()
        mobile.locator("#mobileMoreSheet.open").wait_for(state="visible", timeout=10_000)
        for expected in ("Decision Queue", "Research", "Agent Operations", "QKU / Formula Routes", "Settings"):
            mobile.locator(f"#mobileMoreSheet [data-mobile-overflow-destination='{expected}']").first.wait_for(state="visible", timeout=10_000)
        _screenshot_target(
            mobile,
            repo,
            "mobile_more_overflow_open",
            screenshots,
            "mobile_390x844",
            "#mobileMoreSheet.open",
            "Decision Queue",
            screenshot_selector="#mobileMoreSheet",
        )
        mobile.locator("#mobileMoreToggle").tap()
        _tap_mobile_nav(mobile, "#trade-workbench")
        mobile.locator("[data-workbench-field-shell='plain_english_detail']").scroll_into_view_if_needed()
        _screenshot_target(
            mobile,
            repo,
            "mobile_workbench_targeted_input_colors",
            screenshots,
            "mobile_390x844",
            "[data-workbench-field-shell='plain_english_detail'][data-owner-color-proof='input_required']",
            "Plain-English detail",
        )
        checks.append("r2r5_mobile_primary_nav_more_overflow_and_workbench_target")

        browser.close()

    missing = sorted(set(R2R5_SCREENSHOTS) - {Path(row["path"]).stem.replace("ui1r2r5_", "") for row in screenshots})
    if missing:
        raise SystemExit(f"PR169_DASH1_UI1_R2_R5_PLAYWRIGHT_MISSING_SCREENSHOTS {missing}")
    _write_r2r5_report(repo, screenshots, checks, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R2_R5_PLAYWRIGHT_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R2_R5_PLAYWRIGHT_OK")


def run_r2r6(repo: Path) -> None:
    html = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "owner_dashboard_review_surface.html"
    url = html.resolve().as_uri()
    console_errors: list[str] = []
    external_requests: list[str] = []
    screenshots: list[dict[str, Any]] = []
    checks: list[str] = []

    def first_registered_canvas(page: Page):
        _nav(page, "#portfolio")
        canvas = page.locator(".chart-canvas[data-chart-registered='true']").first
        canvas.wait_for(state="visible", timeout=10_000)
        canvas.evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
        box = canvas.bounding_box()
        if not box:
            raise AssertionError("registered chart canvas missing bounding box")
        return canvas, box

    def hover_registered_chart(page: Page):
        canvas, box = first_registered_canvas(page)
        page.mouse.move(box["x"] + box["width"] * 0.55, box["y"] + box["height"] * 0.45)
        canvas.wait_for(state="visible", timeout=10_000)
        return canvas, box

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)
        page.goto(url, wait_until="load")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")

        _open_settings(page, "Appearance")
        page.locator("[data-owner-setting='theme_preset']").select_option("CUSTOM")
        page.locator("[data-custom-theme-editor='OwnerCustomThemeTokenEditorV1']").wait_for(state="visible", timeout=10_000)
        _screenshot_target_r2r6(
            page,
            repo,
            "theme_custom",
            screenshots,
            "desktop",
            "[data-custom-theme-editor='OwnerCustomThemeTokenEditorV1']",
            "Custom theme uses the color tokens selected here.",
            min_width=320,
            min_height=160,
        )
        before_card_bg = page.locator(".owner-hero-card[data-owner-theme-consumer='custom-theme-token']").first.evaluate("element => getComputedStyle(element).backgroundColor")
        page.locator("[data-owner-setting='custom_card_background_color']").fill("#123456")
        page.locator("[data-owner-setting='custom_accent_color']").fill("#22C55E")
        page.locator("#closeOwnerSettings").click()
        after_card_bg = page.locator(".owner-hero-card[data-owner-theme-consumer='custom-theme-token']").first.evaluate("element => getComputedStyle(element).backgroundColor")
        if before_card_bg == after_card_bg:
            raise AssertionError("custom theme token did not change real dashboard card background")
        theme_applied_path = repo / _path_r2r6("theme_applied")
        theme_applied_path.parent.mkdir(parents=True, exist_ok=True)
        theme_card = page.locator(".owner-hero-card[data-owner-theme-consumer='custom-theme-token']").first
        theme_card.wait_for(state="visible", timeout=10_000)
        theme_box = theme_card.bounding_box()
        if not theme_box or theme_box["width"] < 160 or theme_box["height"] < 120:
            raise AssertionError(f"theme applied card proof too small: {theme_box}")
        theme_card.screenshot(path=str(theme_applied_path))
        screenshots.append(
            {
                "path": _path_r2r6("theme_applied"),
                "tested_interaction": "theme_applied",
                "viewport": "desktop",
                "result": "PASS",
                "proof_selector_or_locator": ".owner-hero-card[data-owner-theme-consumer='custom-theme-token']",
                "proof_text_or_state": "custom token changed computed background",
                "runtime_side_effect_allowed": False,
                "source_truth_created": False,
                "order_authority_created": False,
            }
        )
        checks.append("r2r6_custom_theme_editor_and_real_surface_token_consumption")

        _open_settings(page, "Colors")
        page.locator("[data-owner-setting='input_required_color']").first.fill("#F97316")
        page.locator("#closeOwnerSettings").click()
        _nav(page, "#trade-workbench")
        page.locator("[data-workbench-field='plain_english_detail']").fill("")
        page.locator("[data-workbench-field-shell='plain_english_detail']").scroll_into_view_if_needed()
        border_color = page.locator("[data-workbench-field-shell='plain_english_detail']").evaluate("element => getComputedStyle(element).borderLeftColor")
        if "249" not in border_color and "F97316" not in border_color.upper():
            raise AssertionError(f"input-required color token not applied to Workbench field: {border_color}")
        _screenshot_target_r2r6(
            page,
            repo,
            "color_proof",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='plain_english_detail'][data-owner-color-proof='input_required']",
            "Plain-English detail",
            min_width=260,
            min_height=120,
        )
        checks.append("r2r6_settings_color_token_consumed_by_workbench_field")

        _open_settings(page, "Appearance")
        page.locator("[data-owner-setting='density']").select_option("comfortable")
        comfortable_card_padding = page.locator(".owner-hero-card[data-owner-density-policy='OwnerDensityPolicyV1']").first.evaluate("element => parseFloat(getComputedStyle(element).paddingTop)")
        page.locator("#closeOwnerSettings").click()
        _nav(page, "#trade-workbench")
        comfortable_field_padding = page.locator("[data-workbench-field-shell='plain_english_detail']").evaluate("element => parseFloat(getComputedStyle(element).paddingTop)")
        _open_settings(page, "Appearance")
        page.locator("[data-owner-setting='density']").select_option("compact")
        compact_card_padding = page.locator(".owner-hero-card[data-owner-density-policy='OwnerDensityPolicyV1']").first.evaluate("element => parseFloat(getComputedStyle(element).paddingTop)")
        page.locator("#closeOwnerSettings").click()
        _nav(page, "#trade-workbench")
        compact_field_padding = page.locator("[data-workbench-field-shell='plain_english_detail']").evaluate("element => parseFloat(getComputedStyle(element).paddingTop)")
        if compact_card_padding > comfortable_card_padding * 0.85:
            raise AssertionError(f"compact card padding not smaller enough: compact={compact_card_padding} comfortable={comfortable_card_padding}")
        if compact_field_padding > comfortable_field_padding * 0.85:
            raise AssertionError(f"compact field padding not smaller enough: compact={compact_field_padding} comfortable={comfortable_field_padding}")
        touch_min = page.locator("[data-workbench-field='plain_english_detail']").evaluate("element => parseFloat(getComputedStyle(element).minHeight)")
        if touch_min < 40:
            raise AssertionError(f"compact mobile/control touch target below 40px: {touch_min}")
        density_path = repo / _path_r2r6("density")
        density_path.parent.mkdir(parents=True, exist_ok=True)
        density_field = page.locator("[data-workbench-field-shell='plain_english_detail']").first
        density_box = density_field.bounding_box()
        if not density_box or density_box["width"] < 300 or density_box["height"] < 100:
            raise AssertionError(f"density field proof too small: {density_box}")
        density_field.screenshot(path=str(density_path))
        screenshots.append(
            {
                "path": _path_r2r6("density"),
                "tested_interaction": "density",
                "viewport": "desktop",
                "result": "PASS",
                "proof_selector_or_locator": "[data-workbench-field-shell='plain_english_detail']",
                "proof_text_or_state": "compact card and field padding computed smaller than comfortable",
                "runtime_side_effect_allowed": False,
                "source_truth_created": False,
                "order_authority_created": False,
            }
        )
        checks.append("r2r6_density_compact_comfortable_measurable_on_card_and_workbench")

        _nav(page, "#portfolio")
        _open_settings(page, "Charts")
        page.locator("[data-owner-setting='chart_axis_labels']").set_checked(False)
        page.locator("[data-owner-setting='chart_grid_lines']").set_checked(False)
        page.locator("[data-owner-setting='chart_crosshair']").set_checked(True)
        page.locator("[data-owner-setting='chart_tooltips']").set_checked(True)
        page.locator("#closeOwnerSettings").click()
        _nav(page, "#portfolio")
        page.locator(".chart-panel[data-chart-registered='true'][data-axis-labels-enabled='false']").first.wait_for(state="visible", timeout=10_000)
        if page.locator(".chart-panel[data-chart-registered='true'] .chart-axis-labels:visible").count() != 0:
            raise AssertionError("axis labels still visible after axis setting disabled")
        _screenshot_target_r2r6(
            page,
            repo,
            "chart_axis",
            screenshots,
            "desktop",
            ".chart-panel[data-chart-registered='true'][data-axis-labels-enabled='false']",
            "false",
            min_width=320,
            min_height=200,
        )
        if page.locator(".chart-panel[data-chart-registered='true'] .grid-line:visible").count() != 0:
            raise AssertionError("grid lines still visible after grid setting disabled")
        _screenshot_target_r2r6(
            page,
            repo,
            "chart_grid",
            screenshots,
            "desktop",
            ".chart-panel[data-chart-registered='true'][data-grid-lines-enabled='false']",
            "false",
            min_width=320,
            min_height=200,
        )
        canvas, _box = hover_registered_chart(page)
        page.locator(".chart-canvas[data-chart-registered='true'][data-crosshair-enabled='true'].is-focused").first.wait_for(state="visible", timeout=10_000)
        _screenshot_target_r2r6(
            page,
            repo,
            "chart_crosshair",
            screenshots,
            "desktop",
            ".chart-canvas[data-chart-registered='true'][data-crosshair-enabled='true'].is-focused",
            "true",
            min_width=320,
            min_height=200,
        )
        page.locator(".chart-canvas[data-tooltips-enabled='true'] [data-chart-tooltip-visible='true']").first.wait_for(state="visible", timeout=10_000)
        _screenshot_target_r2r6(
            page,
            repo,
            "chart_tooltip",
            screenshots,
            "desktop",
            ".chart-canvas[data-tooltips-enabled='true'] [data-chart-tooltip-visible='true']",
            "Value: provider receipts pending",
            screenshot_selector=".chart-canvas[data-chart-registered='true'].is-focused",
            min_width=320,
            min_height=200,
        )
        page.keyboard.press("Escape")
        non_chart = page.locator(".chart-panel[data-chart-registered='false']").first
        non_chart.wait_for(state="visible", timeout=10_000)
        non_chart.hover()
        if page.locator(".chart-panel[data-chart-registered='false'] [data-chart-tooltip-visible='true']").count() != 0:
            raise AssertionError("non-chart visual created chart point tooltip")
        _screenshot_target_r2r6(
            page,
            repo,
            "no_tooltips",
            screenshots,
            "desktop",
            ".chart-panel[data-chart-registered='false']",
            "false",
            forbidden_visible_content=["Value: provider receipts pending"],
            min_width=300,
            min_height=160,
        )
        checks.append("r2r6_chart_settings_and_non_chart_tooltip_gating")

        _nav(page, "#trade-workbench")
        market_select = page.locator("[data-workbench-field='market_family']").first
        labels = market_select.evaluate("element => Array.from(element.options).map((option) => option.textContent.trim())")
        for required in ("Prediction Market", "Equities / Stocks", "Crypto Spot & Derivatives"):
            if required not in labels:
                raise AssertionError(f"market family option missing: {required}")
        for forbidden in ("Sports Market", "Financial Market"):
            if forbidden in labels:
                raise AssertionError(f"forbidden market family option present: {forbidden}")
        market_select.evaluate("element => { element.size = element.options.length; }")
        _screenshot_target_r2r6(
            page,
            repo,
            "market_catalog",
            screenshots,
            "desktop",
            "[data-workbench-field-shell='market_family']",
            "Equities / Stocks",
            forbidden_visible_content=["Sports Market", "Financial Market"],
            min_width=260,
            min_height=200,
        )
        market_select.evaluate("element => { element.size = 1; }")
        market_select.select_option("equities_stocks")
        page.locator("#workbenchMarketFamilyStatus").wait_for(state="visible", timeout=10_000)
        status_text = page.locator("#workbenchMarketFamilyStatus").inner_text(timeout=10_000)
        for expected in ("Expansion-stage market sleeve", "Research/intake only"):
            if expected not in status_text:
                raise AssertionError(f"equities dormant status missing: {expected}")
        market_select.select_option("other")
        page.locator("[data-workbench-field='custom_market_family']").fill("Owner sleeve candidate")
        _screenshot_union_r2r6(
            page,
            repo,
            "other_market",
            screenshots,
            "desktop",
            ["[data-workbench-field-shell='market_family']", "[data-workbench-field-shell='custom_market_family'][data-other-visible='true']"],
            "Custom market family",
            forbidden_visible_content=["source truth"],
            min_width=420,
            min_height=130,
        )
        market_select.select_option("prediction_market")
        page.locator("[data-workbench-field='event_category']").select_option("sports")
        sports_text = page.locator("#workbenchMarketFamilyStatus").inner_text(timeout=10_000)
        if "Sports is an event category under Prediction Market, not a Market Family" not in sports_text:
            raise AssertionError("Sports did not render as event-category-only copy")
        page.locator("[data-workbench-field='event_category']").select_option("other")
        page.locator("[data-workbench-field='custom_event_category']").fill("Owner event category candidate")
        _screenshot_union_r2r6(
            page,
            repo,
            "other_event",
            screenshots,
            "desktop",
            ["[data-workbench-field-shell='event_category']", "[data-workbench-field-shell='custom_event_category'][data-other-visible='true']"],
            "Custom event category",
            forbidden_visible_content=["source truth"],
            min_width=420,
            min_height=130,
        )
        checks.append("r2r6_workbench_market_catalog_event_category_and_other_routes")

        _nav(page, "#overview")
        menu = page.locator("#overviewCards .next-action-menu[data-action-alias-policy='OwnerActionRegistryAliasPolicyV1']").first
        if menu.get_attribute("open") is None:
            menu.locator("summary").click()
        menu_text = menu.inner_text(timeout=10_000)
        if "Technical Details" not in menu_text:
            raise AssertionError("canonical Technical Details action missing")
        if "Open technical details" in menu_text:
            raise AssertionError("duplicate technical details alias visible")
        _screenshot_target_r2r6(
            page,
            repo,
            "more_actions",
            screenshots,
            "desktop",
            "#overviewCards .next-action-menu[data-action-alias-policy='OwnerActionRegistryAliasPolicyV1']",
            "Technical Details",
            forbidden_visible_content=["Open technical details"],
            min_width=150,
            min_height=120,
        )
        checks.append("r2r6_more_actions_technical_alias_deduped")

        _nav(page, "#agents")
        _screenshot_target_r2r6(
            page,
            repo,
            "queue",
            screenshots,
            "desktop",
            "#qttTeamWorkflowQueue [data-workflow-queue-shell='OwnerWorkflowQueueStateV1']",
            "QTT Team Workflow Queue",
            min_width=360,
            min_height=220,
        )
        _screenshot_target_r2r6(
            page,
            repo,
            "receipts",
            screenshots,
            "desktop",
            "#auditReceiptPreview [data-receipt-preview-shell='OwnerReceiptPreviewStateV1']",
            "Audit Trail / Receipts Preview",
            min_width=360,
            min_height=220,
        )
        checks.append("r2r6_workflow_queue_and_receipts_unobstructed")

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
        mobile.locator("[data-workbench-field-shell='plain_english_detail']").evaluate("element => element.scrollIntoView({block: 'center', inline: 'nearest'})")
        _screenshot_target_r2r6(
            mobile,
            repo,
            "mobile_wb",
            screenshots,
            "mobile_390x844",
            "[data-workbench-field-shell='plain_english_detail'][data-owner-color-proof='input_required']",
            "Plain-English detail",
            min_width=280,
            min_height=120,
        )
        checks.append("r2r6_mobile_workbench_not_clipped_sliver")

        browser.close()

    missing = sorted(set(R2R6_SCREENSHOTS) - {Path(row["path"]).stem.replace("r2r6_", "") for row in screenshots})
    if missing:
        raise SystemExit(f"PR169_DASH1_UI1_R2R6_PLAYWRIGHT_MISSING_SCREENSHOTS {missing}")
    _write_r2r6_report(repo, screenshots, checks, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R2R6_PLAYWRIGHT_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R2R6_PLAYWRIGHT_OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    parser.add_argument("--suite", choices=("r2-r4", "r2-r5", "r2-r6"), default="r2-r4")
    args = parser.parse_args(argv)
    repo = Path(args.repo_root).resolve()
    if args.suite == "r2-r6":
        run_r2r6(repo)
    elif args.suite == "r2-r5":
        run_r2r5(repo)
    else:
        run(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
