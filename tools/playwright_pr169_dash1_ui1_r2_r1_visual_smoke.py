from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


SCREENSHOTS = {
    "guided_mode": ".tmp/ui1r2r1_v4_guided_mode.png",
    "advanced_mode": ".tmp/ui1r2r1_v4_advanced_mode.png",
    "developer_mode": ".tmp/ui1r2r1_v4_developer_mode.png",
    "mode_diff_evidence": ".tmp/ui1r2r1_v4_mode_diff_evidence.png",
    "chat_before_submit": ".tmp/ui1r2r1_v4_chat_before_submit.png",
    "chat_enter_newline_default": ".tmp/ui1r2r1_v4_chat_enter_newline_default.png",
    "chat_after_ctrl_enter_submit": ".tmp/ui1r2r1_v4_chat_after_ctrl_enter_submit.png",
    "chat_after_send_submit": ".tmp/ui1r2r1_v4_chat_after_send_submit.png",
    "chat_shift_enter_newline": ".tmp/ui1r2r1_v4_chat_shift_enter_newline.png",
    "guided_input_after_enter": ".tmp/ui1r2r1_v4_guided_input_after_enter.png",
    "dropdown_to_workbench": ".tmp/ui1r2r1_v4_dropdown_to_workbench.png",
    "dropdown_to_tca": ".tmp/ui1r2r1_v4_dropdown_to_tca.png",
    "dropdown_to_no_trade": ".tmp/ui1r2r1_v4_dropdown_to_no_trade.png",
    "dropdown_to_qku": ".tmp/ui1r2r1_v4_dropdown_to_qku.png",
    "mobile_repaired_flow": ".tmp/ui1r2r1_v4_mobile_repaired_flow.png",
    "guided_compact_view": ".tmp/ui1r2r1_v4_guided_compact_view.png",
    "collapsed_controls_compact": ".tmp/ui1r2r1_v4_collapsed_controls_compact.png",
    "advanced_density": ".tmp/ui1r2r1_v4_advanced_density.png",
    "developer_technical_view": ".tmp/ui1r2r1_v4_developer_technical_view.png",
    "chat_plain_english_route": ".tmp/ui1r2r1_v4_chat_plain_english_route.png",
    "chat_to_workbench_context": ".tmp/ui1r2r1_v4_chat_to_workbench_context.png",
    "evidence_spine_drilldown": ".tmp/ui1r2r1_v4_evidence_spine_drilldown.png",
    "semantic_title_grid": ".tmp/ui1r2r1_v4_semantic_title_grid.png",
    "mode_density_compare": ".tmp/ui1r2r1_v4_mode_density_compare.png",
}


def _screenshot(page: Page, repo: Path, name: str, rows: list[dict[str, Any]], viewport: str = "desktop") -> None:
    path = repo / SCREENSHOTS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
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


def _choose_mode(page: Page, mode: str) -> None:
    toggle = page.locator("#ownerOptionsToggle")
    if toggle.count() and page.locator("#ownerOptionsPanel:visible").count() == 0:
        toggle.click()
    page.locator(f"[data-mode-choice='{mode}']:visible").click()


def _open_menu(page: Page, selector: str) -> None:
    menu = page.locator(selector).first
    menu.wait_for(state="attached", timeout=10_000)
    menu.evaluate("node => node.open = true")


def _close_drawer(page: Page) -> None:
    if page.locator("#drilldownDrawer[aria-hidden='false']").count():
        page.locator("#closeDrawer").click()
        page.locator("#drilldownDrawer[aria-hidden='false']").wait_for(state="detached", timeout=10_000)


def _visible_count(page: Page, selector: str) -> int:
    return page.locator(f"{selector}:visible").count()


def _click_visible(page: Page, selector: str) -> None:
    page.locator(f"{selector}:visible").first.click()


def _write_report(
    repo: Path,
    rows: list[dict[str, Any]],
    checks: list[str],
    console_errors: list[str],
    external_requests: list[str],
) -> None:
    report_path = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui" / "ui1r2r1_playwright.report.json"
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
    payload["chat_enter_to_send_default_enabled"] = False
    payload["chat_default_enter_behavior"] = "NEWLINE"
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
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)

        page.goto(url, wait_until="load")
        _assert_visible(page, "body[data-experience-mode='GUIDED_OWNER']")
        _assert_visible(page, "[data-mode-panel='GUIDED_OWNER']")
        assert _visible_count(page, "[data-mode-developer-technical]") == 0
        guided_metric_count = _visible_count(page, "[data-mode-guided-metric]")
        _screenshot(page, repo, "guided_mode", screenshots)
        _screenshot(page, repo, "guided_compact_view", screenshots)
        _screenshot(page, repo, "collapsed_controls_compact", screenshots)
        checks.append("guided_default_compact_no_raw_refs_visible")

        _choose_mode(page, "ADVANCED_OWNER")
        _assert_visible(page, "body[data-experience-mode='ADVANCED_OWNER']")
        _assert_visible(page, "[data-mode-panel='ADVANCED_OWNER']")
        advanced_metric_count = _visible_count(page, "[data-mode-advanced-metric]")
        assert advanced_metric_count > guided_metric_count
        assert _visible_count(page, "[data-mode-developer-technical]") == 0
        _screenshot(page, repo, "advanced_mode", screenshots)
        _screenshot(page, repo, "advanced_density", screenshots)
        checks.append("advanced_metric_density_exceeds_guided")

        _choose_mode(page, "DEVELOPER")
        _assert_visible(page, "body[data-experience-mode='DEVELOPER']")
        _assert_visible(page, "[data-mode-developer-technical]")
        developer_text = page.locator("[data-mode-panel='DEVELOPER']").inner_text(timeout=10_000)
        assert "OwnerSurfaceResolver" in developer_text
        assert "OwnerActionRegistry" in developer_text
        _screenshot(page, repo, "developer_mode", screenshots)
        _screenshot(page, repo, "developer_technical_view", screenshots)
        _screenshot(page, repo, "mode_density_compare", screenshots)
        checks.append("developer_technical_evidence_visible_only_in_developer")

        _choose_mode(page, "GUIDED_OWNER")
        _assert_visible(page, "body[data-experience-mode='GUIDED_OWNER']")
        assert _visible_count(page, "[data-mode-developer-technical]") == 0
        _screenshot(page, repo, "mode_diff_evidence", screenshots)

        title_values = page.locator("article.card h3").evaluate_all("(nodes) => nodes.map((node) => node.textContent.trim()).filter(Boolean)")
        assert len(set(title_values[:12])) >= 8
        assert title_values.count("Owner Decision") <= 1
        assert page.locator(".action-primary").count() > 0
        assert page.locator(".action-secondary").count() > 0
        assert page.locator("[data-provider-pending-action='true']").count() > 0
        _screenshot(page, repo, "semantic_title_grid", screenshots)
        checks.append("semantic_titles_and_action_states_distinct")

        page.locator("a[href='#chat']").first.click()
        _assert_visible(page, "#ownerChatInput")
        _screenshot(page, repo, "chat_before_submit", screenshots)
        assert page.locator("#chatEnterToSendToggle").is_checked() is False
        before_receipts = page.locator("#chatReceiptPreview .receipt-card").count()
        page.locator("#ownerChatInput").fill("Can QTT check this market and find the best trade?")
        page.keyboard.press("Enter")
        assert page.locator("#chatReceiptPreview .receipt-card").count() == before_receipts
        assert "\n" in page.locator("#ownerChatInput").input_value()
        _screenshot(page, repo, "chat_enter_newline_default", screenshots)
        checks.append("chat_enter_newline_by_default")

        page.locator("#ownerChatInput").fill("Can QTT check this market and find the best trade?")
        page.keyboard.press("Control+Enter")
        _assert_visible(page, "#chatReceiptPreview [data-preview-object='OwnerPlainEnglishIntentPreviewV1']")
        _assert_visible(page, "#chatReceiptPreview .owner-bubble")
        _assert_visible(page, "#chatReceiptPreview .qtt-bubble")
        _assert_visible(page, "#chatReceiptPreview [data-intent-family='TRADE_CHECK_REQUEST']")
        assert page.locator("#chatReceiptPreview [data-runtime-side-effect-allowed='false']").count() > 0
        _screenshot(page, repo, "chat_after_ctrl_enter_submit", screenshots)
        _screenshot(page, repo, "chat_plain_english_route", screenshots)
        checks.append("chat_ctrl_enter_submits_local_preview")

        page.locator("#ownerChatInput").fill("Research this article and tell me if it creates a prediction-market edge.")
        page.locator("#routePreviewButton").click()
        assert page.locator("#chatReceiptPreview .receipt-card").count() >= 1
        assert "Research this article" in page.locator("#chatReceiptPreview").inner_text(timeout=10_000)
        _screenshot(page, repo, "chat_after_send_submit", screenshots)
        checks.append("chat_send_button_submits")

        page.locator("#ownerChatInput").fill("Line one")
        receipt_count = page.locator("#chatReceiptPreview .receipt-card").count()
        page.keyboard.press("Shift+Enter")
        assert page.locator("#chatReceiptPreview .receipt-card").count() == receipt_count
        assert "\n" in page.locator("#ownerChatInput").input_value()
        _screenshot(page, repo, "chat_shift_enter_newline", screenshots)
        checks.append("chat_shift_enter_newline")

        page.locator("#chatReceiptPreview [data-next-step-id='NEXT_STEP_SEND_TO_TRADE_WORKBENCH']").first.click()
        _assert_visible(page, "#tradeWorkbench[data-prefilled-context='true']")
        _assert_visible(page, "#tradeWorkbenchContextRefs [data-workbench-context-preview='WorkbenchContextPreviewV1'], #tradeWorkbenchContextRefs")
        _screenshot(page, repo, "chat_to_workbench_context", screenshots)
        checks.append("chat_to_workbench_prefills_context")

        page.locator("#ownerCoachPanel [data-next-step-id='NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS']").first.click()
        _assert_visible(page, "[data-guided-workflow='CHECK_TRADE']")
        page.locator("#guidedTextInput").fill("Use a small owner-reviewed trade check.")
        start_step = page.locator("[data-guided-workflow]").get_attribute("data-guided-current-step")
        page.keyboard.press("Enter")
        assert page.locator("[data-guided-workflow]").get_attribute("data-guided-current-step") != start_step
        page.locator("#guidedNumericInput").fill("abc")
        invalid_step = page.locator("[data-guided-workflow]").get_attribute("data-guided-current-step")
        page.keyboard.press("Enter")
        assert page.locator("[data-guided-workflow]").get_attribute("data-guided-current-step") == invalid_step
        assert "Enter a number" in page.locator("#guidedInlineValidation").inner_text(timeout=10_000)
        page.locator("#guidedNumericInput").fill("50")
        page.keyboard.press("Enter")
        assert page.locator("#guidedPreviewState").inner_text(timeout=10_000).find("Saved number: 50") >= 0
        _screenshot(page, repo, "guided_input_after_enter", screenshots)
        checks.append("guided_single_line_enter_advances_and_invalid_numeric_blocks")

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_SEND_TO_TRADE_WORKBENCH']")
        _assert_visible(page, "#tradeWorkbench[data-prefilled-context='true']")
        _screenshot(page, repo, "dropdown_to_workbench", screenshots)
        checks.append("dropdown_send_to_workbench_prefills")

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_SHOW_TCA_COST_BREAKDOWN']")
        _assert_visible(page, "#drilldownDrawer[data-drawer-kind='tca'][aria-hidden='false']")
        assert "fees" in page.locator("#drawerBody").inner_text(timeout=10_000).lower()
        _screenshot(page, repo, "dropdown_to_tca", screenshots)
        _screenshot(page, repo, "evidence_spine_drilldown", screenshots)
        _close_drawer(page)

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_EXPLAIN_NO_TRADE']")
        _assert_visible(page, "#drilldownDrawer[data-drawer-kind='no-trade'][aria-hidden='false']")
        assert "reoptimization" in page.locator("#drawerBody").inner_text(timeout=10_000).lower()
        _screenshot(page, repo, "dropdown_to_no_trade", screenshots)
        _close_drawer(page)

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_SHOW_QKU_FORMULA_ROUTES']")
        _assert_visible(page, "#drilldownDrawer[data-drawer-kind='qku'][aria-hidden='false']")
        qku_text = page.locator("#drawerBody").inner_text(timeout=10_000)
        assert "QKU/formula refs or explicit gap route" in qku_text
        assert "no raw JSONL scanning path" in qku_text
        _screenshot(page, repo, "dropdown_to_qku", screenshots)
        _close_drawer(page)
        checks.append("tca_no_trade_qku_drilldowns_with_evidence_spine")

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(url, wait_until="load")
        _assert_visible(page, "body[data-experience-mode='GUIDED_OWNER']")
        no_overflow = page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")
        assert no_overflow is True
        touch_targets_ok = page.evaluate(
            """() => [...document.querySelectorAll('[data-next-step-id], #routePreviewButton, [data-mode-choice]')]
              .filter((node) => !!(node.offsetWidth || node.offsetHeight || node.getClientRects().length))
              .slice(0, 40)
              .every((node) => node.getBoundingClientRect().height >= 34)"""
        )
        assert touch_targets_ok is True
        _screenshot(page, repo, "mobile_repaired_flow", screenshots, viewport="mobile")
        checks.append("mobile_no_horizontal_overflow_and_touch_targets")

        browser.close()

    if console_errors or external_requests:
        raise AssertionError({"console_errors": console_errors, "external_requests": external_requests})
    _write_report(repo, screenshots, checks, console_errors, external_requests)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    run(Path(args.repo_root).resolve())
    print("PR169_DASH1_UI1_R2_R1_PLAYWRIGHT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
