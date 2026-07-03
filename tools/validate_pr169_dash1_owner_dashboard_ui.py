from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_pr169_dash1_owner_dashboard_ui import (
    AUTHORITY_BOUNDARY,
    BOOT_JS,
    BOOT_JSON,
    MOBILE_TABS,
    REQUIRED_TOP_LEVEL_KEYS,
    SEMANTIC_COLORS,
    THEME_STORAGE_KEY,
    UI_ARTIFACT_FILES,
)


SUCCESS_MARKER = "PR169_DASH1_UI1_OWNER_DASHBOARD_UI_VALIDATION_OK"
FORBIDDEN_TEXT = (
    "https://",
    "http://",
    "cdn.",
    "POST /orders",
    "submit live order directly",
    "guaranteed positive profit",
)
GENERIC_PLACEHOLDER_PATTERNS = (
    r"\bTODO\b",
    r"\bdummy\b",
    r"\bplaceholder\b",
    r"\bcoming soon\b",
    r"\bnot implemented\b(?! with no provider stage)",
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for key, child in value.items():
            values.append(key)
            values.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk(child))
    return values


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _contains_second_state_model(payload: dict[str, Any]) -> bool:
    state_model = payload.get("meta", {}).get("artifact_id") == "UI1_OWNER_DASHBOARD_REVIEW_DATA"
    renderer = payload.get("authority_boundary", {}).get("UI1_authority_boundary_ref") == AUTHORITY_BOUNDARY
    return not (state_model and renderer)


def validate(base: Path) -> tuple[str, ...]:
    failures: list[str] = []
    ui_dir = base / "ui"
    boot_json = ui_dir / BOOT_JSON
    boot_js = ui_dir / BOOT_JS
    html = ui_dir / "owner_dashboard_review_surface.html"
    css = ui_dir / "owner_dashboard_review_surface.css"
    js = ui_dir / "owner_dashboard_review_surface.js"

    for path in (boot_json, boot_js, html, css, js):
        if not path.exists():
            failures.append(f"missing_ui_file:{path}")
    for file_name in UI_ARTIFACT_FILES:
        if not (ui_dir / file_name).exists():
            failures.append(f"missing_generated_ui_artifact:{file_name}")
    if not boot_json.exists():
        return tuple(failures)

    data = _read_json(boot_json)
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            failures.append(f"boot_data_missing_top_level_key:{key}")
    if data.get("meta", {}).get("data_source") != "GENERATED_ARTIFACTS":
        failures.append("boot_data_not_generated_artifacts_primary")
    if data.get("fixture_fallback", {}).get("active") is not False:
        failures.append("fixture_fallback_active_when_generated_artifacts_exist")
    if data.get("fixture_fallback", {}).get("fixture_primary_when_generated_artifacts_exist") is not False:
        failures.append("fixture_primary_when_generated_artifacts_exist")
    if not data.get("owner_packet", {}).get("packet_id"):
        failures.append("owner_packet_not_loaded")
    if not data.get("decision_queue"):
        failures.append("decision_queue_not_loaded")
    if not data.get("actionable_cards"):
        failures.append("actionable_cards_not_loaded")
    if not data.get("action_registry"):
        failures.append("action_registry_not_loaded")

    renderer_boundary = _read_json(ui_dir / "owner_dashboard_dash1_ui1_renderer_boundary.generated.json")
    for key in (
        "DASH1_is_canonical_backend_control_plane",
        "UI1_is_renderer_enhancement_responsive_layer",
        "renders_existing_dash1_artifacts",
    ):
        if renderer_boundary.get(key) is not True:
            failures.append(f"renderer_boundary_not_true:{key}")
    for key in (
        "replacement_dashboard",
        "parallel_dashboard",
        "second_registry",
        "new_governance_plane",
        "new_action_semantics",
        "second_mobile_state_model",
        "second_chat_state_model",
        "manual_projection_truth",
    ):
        if renderer_boundary.get(key) is not False:
            failures.append(f"renderer_boundary_not_false:{key}")

    state_model = _read_json(ui_dir / "owner_dashboard_state_model.generated.json")
    for key in (
        "one_dashboard_state_model",
        "one_owner_action_grammar",
        "one_owner_agent_conversation_model",
        "one_trade_workbench_model",
        "no_duplicate_mobile_only_data_layer",
        "no_duplicate_chat_system",
        "no_duplicate_telegram_governance_plane",
    ):
        if state_model.get(key) is not True:
            failures.append(f"state_model_contract_missing:{key}")

    theme = _read_json(ui_dir / "owner_dashboard_theme_contract.generated.json")
    if set(theme.get("supported_modes", [])) != {"DARK", "LIGHT"}:
        failures.append("theme_modes_not_dark_light")
    if theme.get("localStorage_key") != THEME_STORAGE_KEY:
        failures.append("theme_storage_key_bad")
    if set(theme.get("semantic_colors", {}).values()) != set(SEMANTIC_COLORS.values()):
        failures.append("semantic_colors_not_stable")
    if theme.get("light_mode_not_separate_dashboard_state") is not True:
        failures.append("light_mode_creates_separate_state")

    mobile = _read_json(ui_dir / "owner_dashboard_mobile_navigation.generated.json")
    labels = [tab["label"] for tab in mobile.get("tabs", [])]
    for tab in MOBILE_TABS:
        if tab not in labels:
            failures.append(f"mobile_tab_missing:{tab}")
    if mobile.get("touch_targets_minimum_px", 0) < 44:
        failures.append("mobile_touch_targets_too_small")

    provider = _read_json(ui_dir / "owner_dashboard_provider_stage_route_map.generated.json")
    stages = {row.get("stage_id") for row in provider.get("routes", [])}
    for stage in {
        "DASH1",
        "UI1",
        "UI2",
        "SVC1",
        "MOBILE1",
        "MOBILE2",
        "TG1",
        "READINESS1",
        "PRETRADE1",
        "LLM1",
        "LLM2",
        "AGENT_ORCH1",
        "PAPER_LOOP",
        "HOTPATH1",
        "LIVE_DRYRUN1",
        "LIVE_PILOT",
        "LAUNCH",
        "POSTLAUNCH",
        "RI1",
        "PLUGIN1",
        "QMAP1",
        "ALLOW1",
    }:
        if stage not in stages:
            failures.append(f"provider_stage_missing:{stage}")

    qku = _read_json(ui_dir / "owner_dashboard_qku_formula_computability_matrix.generated.json")
    allowed_qku_states = {
        "COMPUTABLE_WITH_CURRENT_CONTRACT",
        "COMPUTABLE_AFTER_PROVIDER_ROUTE",
        "SCHEDULABLE_AFTER_ADAPTER",
        "REPLAY_PAPER_READY_PROVIDER_PENDING",
        "QMAP_REQUIRED",
        "PLUGIN_INTAKE_REQUIRED",
        "ALLOWLIST_PROVIDER_PENDING",
        "BLOCKED_BY_AUTHORITY_BOUNDARY",
        "ACTIONABLE_GAP_ROUTE",
    }
    if not qku.get("rows"):
        failures.append("qku_computability_matrix_empty")
    for row in qku.get("rows", []):
        if row.get("computability_state") not in allowed_qku_states:
            failures.append(f"bad_qku_computability_state:{row.get('computability_state')}")
        if not row.get("activation_route"):
            failures.append("qku_matrix_row_missing_activation_route")

    five = _read_json(ui_dir / "owner_dashboard_ui1_five_question_acceptance.report.json")
    if len(five.get("questions", [])) != 5:
        failures.append("five_question_report_wrong_count")
    for row in five.get("questions", []):
        if row.get("answer_status") != "PASS":
            failures.append(f"five_question_not_pass:{row.get('question_id')}")
        if not row.get("visible_widget_refs") or not row.get("generated_artifact_refs"):
            failures.append(f"five_question_missing_refs:{row.get('question_id')}")

    html_text = _text(html)
    css_text = _text(css)
    js_text = _text(js)
    combined = "\n".join([html_text, css_text, js_text])
    for marker in FORBIDDEN_TEXT:
        if marker in combined:
            failures.append(f"forbidden_ui_text:{marker}")
    if f'<script src="{BOOT_JS}">' not in html_text:
        failures.append("bootstrap_script_missing_from_html")
    if "<script src=\"owner_dashboard_review_surface.js\">" not in html_text:
        failures.append("app_script_missing_from_html")
    if 'data-theme="dark"' not in html_text:
        failures.append("html_default_dark_theme_missing")
    for snippet in (
        "OwnerDashboardPacket",
        "OwnerDecisionQueue",
        "OwnerActionableCards",
        "Trade Workbench",
        "Owner-Agent Chat Workspace",
        "Provider Stage Route Map",
        "CENTRALIZED_AGENT_QKU_ACCESS_RESOLVER_PANEL",
        "DARK",
        "LIGHT",
        "mobile-bottom-nav",
        "drilldownDrawer",
    ):
        if snippet not in combined:
            failures.append(f"required_ui_snippet_missing:{snippet}")
    for variable in (
        "--qtt-bg",
        "--qtt-bg-panel",
        "--qtt-bg-card",
        "--qtt-border",
        "--qtt-text",
        "--qtt-muted",
        "--qtt-green",
        "--qtt-red",
        "--qtt-blue",
        "--qtt-purple",
        "--qtt-orange",
        "--qtt-yellow",
        "--qtt-gray",
    ):
        if variable not in css_text:
            failures.append(f"css_variable_missing:{variable}")
    if THEME_STORAGE_KEY not in js_text:
        failures.append("theme_storage_key_missing_from_js")
    if "window.QTT_OWNER_DASHBOARD_DATA" not in _text(boot_js):
        failures.append("bootstrap_global_missing")
    if "fetch(" in js_text:
        failures.append("app_js_uses_fetch")
    if "OwnerActionRegistry" not in combined:
        failures.append("owner_action_registry_ref_missing")
    if "OwnerSurfaceResolver" not in combined:
        failures.append("owner_surface_resolver_ref_missing")

    all_values = "\n".join(str(value) for value in _walk(data))
    if "guaranteed positive profit" in all_values:
        failures.append("profit_guarantee_wording_present")
    if "validated positive net-cash evidence" not in all_values and "validated_positive_net_cash_evidence" not in all_values:
        failures.append("validated_positive_net_cash_wording_missing")
    if _contains_second_state_model(data):
        failures.append("state_model_or_renderer_boundary_bad")
    for pattern in GENERIC_PLACEHOLDER_PATTERNS:
        if re.search(pattern, all_values, flags=re.IGNORECASE):
            failures.append(f"generic_placeholder_pattern_present:{pattern}")

    for file_name in UI_ARTIFACT_FILES:
        payload = _read_json(ui_dir / file_name)
        meta = payload.get("meta", {})
        if meta.get("manual_edit_allowed") is not False:
            failures.append(f"manual_edit_not_false:{file_name}")
        if meta.get("runtime_side_effect_allowed") is not False:
            failures.append(f"runtime_side_effect_not_false:{file_name}")
        if meta.get("credential_access_allowed") is not False:
            failures.append(f"credential_access_not_false:{file_name}")
        if meta.get("connector_access_allowed") is not False:
            failures.append(f"connector_access_not_false:{file_name}")
        if meta.get("order_execution_allowed") is not False:
            failures.append(f"order_execution_not_false:{file_name}")

    return tuple(failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="docs/master_plan/generated/pr169_dash1")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    base = (Path(args.repo_root) / args.base).resolve()
    failures = validate(base)
    if failures:
        print("PR169_DASH1_UI1_OWNER_DASHBOARD_UI_VALIDATION_FAILED")
        for failure in failures[:200]:
            print(failure)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
