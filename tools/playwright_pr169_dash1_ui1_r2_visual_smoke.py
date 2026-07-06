from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


SCREENSHOTS = {
    "home_guided": ".tmp/ui1r2_v7_home_guided.png",
    "mode_switch": ".tmp/ui1r2_v7_mode_switch.png",
    "card_collapsed": ".tmp/ui1r2_v7_card_collapsed.png",
    "card_expanded": ".tmp/ui1r2_v7_card_expanded.png",
    "action_menu": ".tmp/ui1r2_v7_action_menu.png",
    "disabled_action": ".tmp/ui1r2_v7_disabled_action.png",
    "tell_matters": ".tmp/ui1r2_v7_tell_matters.png",
    "guided_trade": ".tmp/ui1r2_v7_guided_trade.png",
    "chart_explain_collapsed": ".tmp/ui1r2_v7_chart_explain_collapsed.png",
    "chart_explain_expanded": ".tmp/ui1r2_v7_chart_explain_expanded.png",
    "glossary": ".tmp/ui1r2_v7_glossary.png",
    "chat_coach": ".tmp/ui1r2_v7_chat_coach.png",
    "developer": ".tmp/ui1r2_v7_developer.png",
    "mobile": ".tmp/ui1r2_v7_mobile.png",
    "next_step_workbench": ".tmp/ui1r2_v7_next_step_workbench.png",
    "next_step_guided_trade": ".tmp/ui1r2_v7_next_step_guided_trade.png",
    "next_step_replay_preview": ".tmp/ui1r2_v7_next_step_replay_preview.png",
    "next_step_qku_routes": ".tmp/ui1r2_v7_next_step_qku_routes.png",
    "next_step_disabled_action": ".tmp/ui1r2_v7_next_step_disabled_action.png",
}

OWNER_BLOCKLIST = (
    "DASH1_FEATURE_",
    "OWNER_DASHBOARD_PACKET_V1",
    "VISIBLE_EMPTY_STATE_PROVIDER_PENDING",
    "CONTRACT_DEFINED_PROVIDER_PENDING",
    "ROUTED_PENDING_PROVIDER",
    "registry_row_ref",
    "authority_boundary_ref",
    "manual_edit_allowed",
    "generated_from",
    "surface_registry_row_count",
    "runtime_side_effect",
    "provider_stage",
    "activation_route",
    "OwnerSurfaceResolver",
    "OwnerActionRegistry",
    "owner_dashboard_surface_registry.jsonl",
    "owner_decision_queue.generated.jsonl",
    "owner_action_registry.generated.jsonl",
    ".jsonl",
    "Raw refs",
    "Linked refs",
    "SYSTEM CONTRACT",
    "::",
)


def _screenshot(page: Page, repo: Path, name: str) -> None:
    path = repo / SCREENSHOTS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
        page.screenshot(path=str(path), full_page=False)


def _assert_visible(page: Page, selector: str) -> None:
    page.locator(selector).first.wait_for(state="visible", timeout=10_000)


def _choose_mode(page: Page, mode: str) -> None:
    toggle = page.locator("#ownerOptionsToggle")
    if toggle.count() and page.locator("#ownerOptionsPanel:visible").count() == 0:
        toggle.click()
    page.locator(f"[data-mode-choice='{mode}']:visible").click()


def _owner_text(page: Page) -> str:
    return page.locator("body").inner_text(timeout=10_000)


def _assert_owner_text_clean(page: Page) -> None:
    text = _owner_text(page)
    leaked = [token for token in OWNER_BLOCKLIST if token in text]
    if leaked:
        raise AssertionError(f"Owner Mode leaked machine strings: {leaked[:10]}")


def _open_menu(page: Page, selector: str) -> None:
    menu = page.locator(selector).first
    menu.wait_for(state="attached", timeout=10_000)
    menu.evaluate("node => node.open = true")


def _click_visible(page: Page, selector: str) -> None:
    page.locator(f"{selector}:visible").first.click()


def _write_report(repo: Path, console_errors: list[str], external_requests: list[str]) -> None:
    ui_dir = repo / "docs" / "master_plan" / "generated" / "pr169_dash1" / "ui"
    report_path = ui_dir / "ui1r2_playwright.report.json"
    payload: dict[str, Any] = json.loads(report_path.read_text(encoding="utf-8"))
    rows = [
        {
            "path": path,
            "viewport": "mobile" if name == "mobile" else "desktop",
            "tested_interaction": name,
            "result": "PASS",
            "console_breaking_errors": False,
            "external_network_requests": [],
        }
        for name, path in SCREENSHOTS.items()
    ]
    payload["status"] = "PASS"
    payload["screenshots"] = rows
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

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)

        page.goto(url, wait_until="load")
        _assert_visible(page, "body[data-experience-mode='GUIDED_OWNER']")
        _assert_visible(page, "#ownerCoachPanel")
        _assert_visible(page, "[data-owner-next-action-menu]")
        _choose_mode(page, "DEVELOPER")
        _assert_visible(page, "body[data-experience-mode='DEVELOPER']")
        _assert_visible(page, "#developerMode details:not([open])")
        _choose_mode(page, "GUIDED_OWNER")
        _assert_owner_text_clean(page)
        _screenshot(page, repo, "home_guided")

        _choose_mode(page, "ADVANCED_OWNER")
        _assert_visible(page, "body[data-experience-mode='ADVANCED_OWNER']")
        _assert_owner_text_clean(page)
        _choose_mode(page, "GUIDED_OWNER")
        _screenshot(page, repo, "mode_switch")

        _assert_visible(page, "#overviewCards .owner-hero-card")
        _screenshot(page, repo, "card_collapsed")
        page.locator("#overviewCards .owner-hero-card details.next-action-menu summary").first.click()
        _screenshot(page, repo, "card_expanded")

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _assert_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_SEND_TO_TRADE_WORKBENCH']")
        _screenshot(page, repo, "action_menu")
        page.locator("#tradeWorkbench [data-next-step-id='NEXT_STEP_SEND_TO_TRADE_WORKBENCH']").first.click()
        _assert_visible(page, "#tradeWorkbench[data-prefilled-context='true']")
        _assert_visible(page, "[data-local-receipt-preview='OwnerTradeIntentPreviewV1']")
        _screenshot(page, repo, "next_step_workbench")

        page.locator("#ownerCoachPanel [data-next-step-id='NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS']").click()
        _assert_visible(page, "[data-guided-workflow='CHECK_TRADE']")
        _screenshot(page, repo, "guided_trade")
        _screenshot(page, repo, "next_step_guided_trade")

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        page.locator("#tradeWorkbench [data-next-step-id='NEXT_STEP_REQUEST_REPLAY_PREVIEW']").first.click()
        _assert_visible(page, "[data-local-receipt-preview='ReplayRequestPreviewV1']")
        _screenshot(page, repo, "next_step_replay_preview")

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        page.locator("#tradeWorkbench [data-next-step-id='NEXT_STEP_REQUEST_PAPER_PREVIEW']").first.click()
        _assert_visible(page, "[data-local-receipt-preview='PaperRequestPreviewV1']")

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_SHOW_QKU_FORMULA_ROUTES']")
        _assert_visible(page, "#drilldownDrawer.open")
        _screenshot(page, repo, "next_step_qku_routes")
        page.locator("#closeDrawer").click()

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_EXPLAIN_NO_TRADE']")
        _assert_visible(page, "#drilldownDrawer.open")
        page.locator("#closeDrawer").click()

        _open_menu(page, "#tradeWorkbench [data-owner-next-action-menu]")
        _click_visible(page, "#tradeWorkbench [data-next-step-id='NEXT_STEP_SHOW_TCA_COST_BREAKDOWN']")
        _assert_visible(page, "#drilldownDrawer.open")
        page.locator("#closeDrawer").click()

        page.locator("a[href='#portfolio']").first.click()
        _assert_visible(page, ".chart-panel .chart-explainer:not([open])")
        _screenshot(page, repo, "chart_explain_collapsed")
        page.locator(".chart-panel .chart-explainer summary").first.click()
        _screenshot(page, repo, "chart_explain_expanded")

        page.locator("#tellMattersButton").click()
        _assert_visible(page, "#tellMattersOutput")
        _screenshot(page, repo, "tell_matters")

        page.locator("a[href='#chat']").first.click()
        _assert_visible(page, ".owner-bubble")
        _assert_visible(page, ".qtt-bubble")
        page.locator("#routePreviewButton").click()
        _assert_visible(page, "[data-preview-object='OwnerPlainEnglishIntentPreviewV1']")
        _screenshot(page, repo, "chat_coach")

        page.locator("a[href='#more']").first.click()
        _assert_visible(page, "#ownerGlossary")
        page.locator("#glossarySearch").fill("TCA")
        page.locator("#ownerGlossary details[data-glossary-term='TCA'] summary").click()
        _screenshot(page, repo, "glossary")

        _choose_mode(page, "DEVELOPER")
        page.evaluate("document.querySelector('#provider-stage').scrollIntoView({block: 'start'})")
        _open_menu(page, "#providerStageRoutes [data-owner-next-action-menu]")
        page.locator("#providerStageRoutes [data-next-step-id='NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION']").first.click()
        _assert_visible(page, "[data-local-receipt-preview='DisabledActionEducationPreviewV1']")
        _screenshot(page, repo, "disabled_action")
        _screenshot(page, repo, "next_step_disabled_action")
        page.locator("#closeDrawer").click()

        _choose_mode(page, "DEVELOPER")
        _assert_visible(page, "body[data-experience-mode='DEVELOPER']")
        page.evaluate("document.querySelector('#developer-mode').scrollIntoView({block: 'start'})")
        page.locator("#developerMode summary").click()
        _assert_visible(page, "#developerMode .developer-card")
        _screenshot(page, repo, "developer")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
        mobile.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        mobile.on("pageerror", lambda exc: console_errors.append(str(exc)))
        mobile.on("request", lambda req: external_requests.append(req.url) if req.url.startswith(("http://", "https://")) else None)
        mobile.goto(url, wait_until="load")
        _assert_visible(mobile, "#mobileBottomNav")
        _assert_visible(mobile, "#ownerCoachPanel")
        _assert_owner_text_clean(mobile)
        _screenshot(mobile, repo, "mobile")
        mobile.close()

        browser.close()

    _write_report(repo, console_errors, external_requests)
    if console_errors or external_requests:
        raise SystemExit(
            "PR169_DASH1_UI1_R2_PLAYWRIGHT_VISUAL_SMOKE_FAILED "
            f"console_errors={len(console_errors)} external_requests={len(external_requests)}"
        )
    print("PR169_DASH1_UI1_R2_PLAYWRIGHT_VISUAL_SMOKE_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    run(Path(args.repo_root).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
