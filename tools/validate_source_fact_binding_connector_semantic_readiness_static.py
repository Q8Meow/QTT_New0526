#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

SUCCESS_MARKER = "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_STATIC_VALIDATION_OK"
FAILURE_MARKER = "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_STATIC_VALIDATION_FAILED"

VALIDATION_HOOK = "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_STATIC_AUDIT"

SOURCE_MATRIX_TYPE = "STAGE1_SOURCE_TO_CONNECTOR_FIELD_BINDING_MATRIX"
CONNECTOR_MATRIX_TYPE = "STAGE1_CONNECTOR_SEMANTIC_TARGET_FIELD_MATRIX"
GATE_REPORT_TYPE = "STAGE1_CONNECTOR_SEMANTIC_READINESS_GATE_REPORT"

SOURCE_REQUIRED = "SOURCE_REQUIRED"
ACCEPTED_PACKET_REQUIRED = "ACCEPTED_PACKET_REQUIRED"
BLOCKED_PENDING_PACKET = "BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET"

CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

VENUE_IDS = ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]

TARGET_FIELDS = [
    "connector.semantic.connector_semantic_values",
    "connector.venue_api.venue_api_facts",
    "connector.fundamentals.fundamental_facts",
    "connector.fees.fee_semantics",
    "connector.market.tick_semantics",
    "connector.api.rate_limit_semantics",
    "connector.settlement.settlement_rules",
    "connector.order_entry.order_entry_fields",
    "connector.order_status.status_lifecycle",
    "connector.private_state.private_state_fields",
    "connector.private_state.account_fields",
    "connector.private_state.balance_fields",
    "connector.selection.market_selection",
    "connector.selection.contract_selection",
    "connector.selection.event_selection",
    "connector.selection.symbol_selection",
    "connector.selection.live_venue_selection",
    "connector.runtime.runtime_resolver_snapshot",
    "connector.execution.replay_paper_execution",
    "connector.cash.runtime_cash_value",
    "connector.order_authority.order_authority_fields",
]

REQUIRED_TYPED_ARTIFACTS = [
    "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_TASK_PACKET",
    "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_RECEIPT",
    "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_BLOCK_RECEIPT",
    "STAGE1_SOURCE_FACT_BINDING_READINESS_RECEIPT",
    "STAGE1_CONNECTOR_SEMANTIC_READINESS_GATE_RECEIPT",
    "STAGE1_SOURCE_TO_CONNECTOR_FIELD_BINDING_MATRIX",
    "STAGE1_CONNECTOR_SEMANTIC_TARGET_FIELD_MATRIX",
    "STAGE1_CONNECTOR_SEMANTIC_READINESS_GATE_REPORT",
    "SOURCE_FACT_BINDING_NO_FACT_ACCEPTANCE_RECEIPT",
    "CONNECTOR_SEMANTIC_READINESS_NO_VALUE_POPULATION_RECEIPT",
    "CONNECTOR_SEMANTIC_ACCEPTED_PACKET_REQUIRED_RECEIPT",
]

REQUIRED_RECEIPTS = [
    "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_RECEIPT",
    "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_BLOCK_RECEIPT",
    "STAGE1_SOURCE_FACT_BINDING_READINESS_RECEIPT",
    "STAGE1_CONNECTOR_SEMANTIC_READINESS_GATE_RECEIPT",
    "SOURCE_FACT_BINDING_NO_FACT_ACCEPTANCE_RECEIPT",
    "CONNECTOR_SEMANTIC_READINESS_NO_VALUE_POPULATION_RECEIPT",
    "CONNECTOR_SEMANTIC_ACCEPTED_PACKET_REQUIRED_RECEIPT",
]

NO_CLAIM_FLAGS = {
    "accepts_source_facts": False,
    "creates_accepted_source_packets": False,
    "populates_connector_semantic_values": False,
    "creates_runtime_resolver_snapshot": False,
    "executes_replay_or_paper": False,
    "creates_live_reachability": False,
    "creates_order_authority": False,
    "creates_atomicrows_bundle_or_hash": False,
    "reduces_blockers": False,
    "creates_profit_evidence": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled": False,
    "source_acceptance_enabled": False,
    "accepted_source_packet_creation_enabled": False,
    "connector_semantic_value_population_enabled": False,
    "live_client_import_enabled": False,
    "network_io_enabled": False,
    "runtime_resolver_snapshot_creation_enabled": False,
    "replay_paper_live_result_packet_creation_enabled": False,
    "order_authority_enabled": False,
    "atomicrows_bundle_or_hash_creation_enabled": False,
    "blocker_reduction_enabled": False,
    "profit_evidence_creation_enabled": False,
}

FORBIDDEN_TRUE_FIELDS = set(NO_CLAIM_FLAGS) | set(FORBIDDEN_ACTION_FLAGS) | {
    "accepted_source_fact_created",
    "accepted_source_packet_created",
    "accepted_source_evidence_packet_created",
    "connector_semantic_value_populated",
    "venue_api_value_populated",
    "fee_tick_rate_limit_settlement_order_private_state_values_populated",
    "runtime_resolver_snapshot_created",
    "replay_paper_result_packet_created",
    "live_reachability_created",
    "order_authority_created",
    "canonical_bundle_present",
    "canonical_bundle_sha_present",
    "atomicrows_bundle_creation_claimed",
    "atomicrows_hash_creation_claimed",
    "atomicrows_sha_authority_claimed",
    "atomicrows_row_creation_claimed",
    "freeze_authority_claimed",
}

FORBIDDEN_COUNT_FIELDS = {
    "accepted_source_fact_created_count",
    "connector_semantic_value_populated_count",
    "runtime_resolver_snapshot_violation_count",
    "replay_paper_execution_violation_count",
    "live_reachability_violation_count",
    "atomicrows_mutation_violation_count",
    "blocker_reduction_or_profit_claim_violation_count",
    "target_field_matrix_missing_count",
}

FORBIDDEN_STRING_MARKERS = {
    "OFFICIAL_SOURCE_FACT_ACCEPTED",
    "ACCEPTED_SOURCE_FACT_CREATED",
    "ACCEPTED_SOURCE_PACKET_CREATED_BY_PR38",
    "CONNECTOR_SEMANTIC_VALUE_POPULATED",
    "CONNECTOR_SEMANTIC_BOUND",
    "VENUE_API_VALUE_POPULATED",
    "FEE_SEMANTIC_VALUE_POPULATED",
    "TICK_SEMANTIC_VALUE_POPULATED",
    "RATE_LIMIT_VALUE_POPULATED",
    "SETTLEMENT_VALUE_POPULATED",
    "ORDER_ENTRY_VALUE_POPULATED",
    "PRIVATE_STATE_VALUE_POPULATED",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "REPLAY_RESULT_PACKET_CREATED",
    "PAPER_RESULT_PACKET_CREATED",
    "LIVE_RESULT_PACKET_CREATED",
    "LIVE_REACHABILITY_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_BUNDLE_HASH_CREATED",
    "BLOCKER_REDUCED",
    "PROFIT_EVIDENCE_CREATED",
}

FORBIDDEN_PYTHON_MODULE_ROOTS = {
    "aiohttp",
    "httpx",
    "requests",
    "selenium",
    "socket",
    "urllib3",
    "websocket",
    "websockets",
}

FORBIDDEN_PYTHON_MODULES = {
    "http.client",
    "urllib.request",
    "playwright.sync_api",
    "playwright.async_api",
}

LOCAL_VISUAL_QA_BROWSER_AUTOMATION_ALLOWED_PATHS = {
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r1_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r1_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r2_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r3_visual_smoke.py"),
}


def _is_allowed_local_visual_qa_browser_module(
    rel: pathlib.PurePosixPath,
    module: str,
) -> bool:
    return (
        rel in LOCAL_VISUAL_QA_BROWSER_AUTOMATION_ALLOWED_PATHS
        and module in {"playwright.sync_api", "playwright.async_api"}
    )

SKIP_DIR_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".tox",
    ".uv-cache",
    ".venv",
    "__pycache__",
    "env",
    "node_modules",
    "venv",
}


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is not valid JSON: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _properties(definition: dict[str, Any]) -> dict[str, Any]:
    properties = definition.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _required(definition: dict[str, Any]) -> set[str]:
    required = definition.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _const_value(definition: dict[str, Any], property_name: str) -> Any:
    prop = _properties(definition).get(property_name, {})
    return prop.get("const") if isinstance(prop, dict) else None


def _require_exact_fields(
    value: dict[str, Any],
    fields: Iterable[str],
    label: str,
) -> list[str]:
    expected = set(fields)
    failures: list[str] = []
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _walk(value: Any, path: str = "value"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _validate_bool_map(value: Any, expected: dict[str, bool], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    failures = _require_exact_fields(value, expected, label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) is not expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def _validate_schema(
    schema: dict[str, Any],
    *,
    expected_type_field: str,
    expected_type: str,
    expected_hook: str,
    schema_path: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    if schema.get("type") != "object":
        failures.append(f"{schema_path}.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path}.additionalProperties must be false")
    if _const_value(schema, expected_type_field) != expected_type:
        failures.append(f"{schema_path}.{expected_type_field} must be {expected_type}")
    if _const_value(schema, "mode") != SOURCE_REQUIRED:
        failures.append(f"{schema_path}.mode must be {SOURCE_REQUIRED}")
    if _const_value(schema, "execution") != "DISABLED":
        failures.append(f"{schema_path}.execution must be DISABLED")
    hooks = _properties(schema).get("validation_hook_ids", {})
    if not isinstance(hooks, dict) or hooks.get("items", {}).get("const") != expected_hook:
        failures.append(f"{schema_path}.validation_hook_ids must require {expected_hook}")
    if not isinstance(schema.get("$defs"), dict):
        failures.append(f"{schema_path} missing $defs")
    return failures


def _canonical_path(root: pathlib.Path, rel_path: pathlib.PurePosixPath) -> pathlib.Path:
    return root.resolve() / pathlib.Path(*rel_path.parts)


def _atomicrows_absence_failures(repo_root: pathlib.Path, label: str) -> list[str]:
    return validate_current_atomicrows_bundle_state(repo_root, label=label)


def _validate_no_forbidden_claims(value: Any, label: str) -> list[str]:
    failures: list[str] = []
    for path, key, item in _walk(value, label):
        if key in FORBIDDEN_TRUE_FIELDS and item is not False:
            failures.append(f"{path} must be false")
        if key in FORBIDDEN_COUNT_FIELDS and item != 0:
            failures.append(f"{path} must be 0")
        if key in {"connector_semantic_value_state", "target_field_state"}:
            if item != SOURCE_REQUIRED:
                failures.append(f"{path} must remain {SOURCE_REQUIRED}")
        if key == "accepted_packet_requirement_state" and item != ACCEPTED_PACKET_REQUIRED:
            failures.append(f"{path} must remain {ACCEPTED_PACKET_REQUIRED}")
        if key == "readiness_state" and item != BLOCKED_PENDING_PACKET:
            failures.append(f"{path} must remain {BLOCKED_PENDING_PACKET}")
        if key in {"accepted_packet_id", "connector_binding_receipt_id"}:
            if item != ACCEPTED_PACKET_REQUIRED:
                failures.append(f"{path} must remain {ACCEPTED_PACKET_REQUIRED}")
        if isinstance(item, str):
            upper = item.upper()
            for marker in sorted(FORBIDDEN_STRING_MARKERS):
                if marker in upper:
                    failures.append(f"{path} contains forbidden claim marker {marker}")
    return failures


def _validate_venue_rows(
    fixture: dict[str, Any],
    *,
    label: str,
    row_type: str,
) -> list[str]:
    rows = fixture.get("venue_rows")
    if not isinstance(rows, list):
        return [f"{label}.venue_rows must be a list"]
    failures: list[str] = []
    actual_venues = [row.get("venue_id") for row in rows if isinstance(row, dict)]
    if actual_venues != VENUE_IDS:
        failures.append(f"{label}.venue_rows must preserve canonical venue order")
    for index, row in enumerate(rows):
        row_label = f"{label}.venue_rows[{index}]"
        if not isinstance(row, dict):
            failures.append(f"{row_label} must be an object")
            continue
        if row.get("record_type") != row_type:
            failures.append(f"{row_label}.record_type must be {row_type}")
        if row.get("target_field_paths") != TARGET_FIELDS:
            failures.append(f"{row_label}.target_field_paths must preserve all Stage-1 target fields")
        if row.get("source_dependency_state", SOURCE_REQUIRED) != SOURCE_REQUIRED:
            failures.append(f"{row_label}.source_dependency_state must be {SOURCE_REQUIRED}")
        if row.get("accepted_packet_requirement_state") != ACCEPTED_PACKET_REQUIRED:
            failures.append(
                f"{row_label}.accepted_packet_requirement_state must be "
                f"{ACCEPTED_PACKET_REQUIRED}"
            )
        if row.get("readiness_state") != BLOCKED_PENDING_PACKET:
            failures.append(f"{row_label}.readiness_state must be {BLOCKED_PENDING_PACKET}")
        failures.extend(_validate_no_forbidden_claims(row, row_label))
    return failures


def validate_source_to_connector_matrix_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("matrix_type") != SOURCE_MATRIX_TYPE:
        failures.append(f"matrix_type must be {SOURCE_MATRIX_TYPE}")
    if fixture.get("mode") != SOURCE_REQUIRED:
        failures.append(f"mode must be {SOURCE_REQUIRED}")
    if fixture.get("execution") != "DISABLED":
        failures.append("execution must be DISABLED")
    policy = fixture.get("target_field_binding_policy")
    if not isinstance(policy, dict):
        failures.append("target_field_binding_policy must be an object")
    else:
        expected_policy = {
            "all_source_dependent_fields_state": SOURCE_REQUIRED,
            "accepted_packet_requirement_state": ACCEPTED_PACKET_REQUIRED,
            "future_binding_state": BLOCKED_PENDING_PACKET,
            "future_accepted_source_evidence_packet_required": True,
            "target_field_specific_packet_required": True,
            "connector_semantic_value_population_allowed": False,
            "connector_semantic_binding_allowed": False,
        }
        failures.extend(_require_exact_fields(policy, expected_policy, "target_field_binding_policy"))
        for field, expected in sorted(expected_policy.items()):
            if policy.get(field) != expected:
                failures.append(f"target_field_binding_policy.{field} must be {expected}")
    failures.extend(
        _validate_venue_rows(
            fixture,
            label="source_to_connector_matrix",
            row_type="STAGE1_SOURCE_TO_CONNECTOR_FIELD_BINDING_MATRIX_VENUE_ROW",
        )
    )
    failures.extend(_validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "no_claim_flags"))
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(_validate_no_forbidden_claims(fixture, "source_to_connector_matrix"))
    return failures


def validate_connector_semantic_target_field_matrix_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("matrix_type") != CONNECTOR_MATRIX_TYPE:
        failures.append(f"matrix_type must be {CONNECTOR_MATRIX_TYPE}")
    if fixture.get("mode") != SOURCE_REQUIRED:
        failures.append(f"mode must be {SOURCE_REQUIRED}")
    if fixture.get("execution") != "DISABLED":
        failures.append("execution must be DISABLED")
    policy = fixture.get("no_value_population_policy")
    if not isinstance(policy, dict):
        failures.append("no_value_population_policy must be an object")
    else:
        expected_policy = {
            "every_connector_semantic_field_unpopulated": True,
            "source_required_state_required": True,
            "accepted_packet_required_state_required": True,
            "blocked_pending_accepted_source_packet_state_required": True,
            "connector_semantic_value_population_allowed": False,
            "venue_api_fee_tick_rate_limit_settlement_order_private_values_allowed": False,
        }
        failures.extend(_require_exact_fields(policy, expected_policy, "no_value_population_policy"))
        for field, expected in sorted(expected_policy.items()):
            if policy.get(field) != expected:
                failures.append(f"no_value_population_policy.{field} must be {expected}")
    failures.extend(
        _validate_venue_rows(
            fixture,
            label="connector_semantic_target_field_matrix",
            row_type="STAGE1_CONNECTOR_SEMANTIC_TARGET_FIELD_MATRIX_VENUE_ROW",
        )
    )
    failures.extend(_validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "no_claim_flags"))
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(
        _validate_no_forbidden_claims(fixture, "connector_semantic_target_field_matrix")
    )
    return failures


def validate_readiness_gate_report_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    if fixture.get("report_type") != GATE_REPORT_TYPE:
        failures.append(f"report_type must be {GATE_REPORT_TYPE}")
    if fixture.get("task_packet_type") != REQUIRED_TYPED_ARTIFACTS[0]:
        failures.append("task_packet_type must represent the PR38 readiness task packet")
    if fixture.get("mode") != SOURCE_REQUIRED:
        failures.append(f"mode must be {SOURCE_REQUIRED}")
    if fixture.get("execution") != "DISABLED":
        failures.append("execution must be DISABLED")
    if fixture.get("status") != "BLOCKED":
        failures.append("status must remain BLOCKED")
    if fixture.get("gate_state") != BLOCKED_PENDING_PACKET:
        failures.append(f"gate_state must be {BLOCKED_PENDING_PACKET}")
    if fixture.get("required_typed_artifacts_represented") != REQUIRED_TYPED_ARTIFACTS:
        failures.append("required_typed_artifacts_represented must preserve the PR38 artifact list")
    if fixture.get("receipt_ids_emitted") != REQUIRED_RECEIPTS:
        failures.append("receipt_ids_emitted must preserve the PR38 receipt list")
    statement = fixture.get("authority_boundary_statement", "")
    for fragment in [
        "no official source fact",
        "no connector semantic value",
        "no runtime resolver snapshot",
        "no live reachability",
        "no order authority",
        "no AtomicRows authority",
        "no blocker reduction",
        "no profit evidence",
    ]:
        if fragment not in statement:
            failures.append(f"authority_boundary_statement missing {fragment}")
    source_report = fixture.get("source_fact_binding_readiness_report")
    if not isinstance(source_report, dict):
        failures.append("source_fact_binding_readiness_report must be an object")
    else:
        if source_report.get("report_type") != "STAGE1_SOURCE_FACT_BINDING_READINESS_REPORT":
            failures.append("source_fact_binding_readiness_report.report_type is invalid")
        if source_report.get("target_field_matrix_present_count") != len(TARGET_FIELDS) * len(VENUE_IDS):
            failures.append("source readiness present count must cover every venue target field")
        failures.extend(_validate_no_forbidden_claims(source_report, "source_fact_binding_readiness_report"))
    summary = fixture.get("connector_semantic_readiness_summary")
    if not isinstance(summary, dict):
        failures.append("connector_semantic_readiness_summary must be an object")
    else:
        if summary.get("venue_ids_checked") != VENUE_IDS:
            failures.append("connector_semantic_readiness_summary.venue_ids_checked is invalid")
        if summary.get("semantic_surface_count") != len(TARGET_FIELDS) * len(VENUE_IDS):
            failures.append("semantic_surface_count must cover every venue target field")
        failures.extend(_validate_no_forbidden_claims(summary, "connector_semantic_readiness_summary"))
    atomicrows = fixture.get("atomicrows_authority_state")
    if not isinstance(atomicrows, dict):
        failures.append("atomicrows_authority_state must be an object")
    else:
        failures.extend(_validate_no_forbidden_claims(atomicrows, "atomicrows_authority_state"))
    failures.extend(_validate_bool_map(fixture.get("forbidden_action_flags"), FORBIDDEN_ACTION_FLAGS, "forbidden_action_flags"))
    failures.extend(_validate_bool_map(fixture.get("no_claim_flags"), NO_CLAIM_FLAGS, "no_claim_flags"))
    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")
    failures.extend(_atomicrows_absence_failures(repo_root, "readiness gate report"))
    failures.extend(_validate_no_forbidden_claims(fixture, "readiness_gate_report"))
    return failures


def _python_paths(root: pathlib.Path) -> list[pathlib.Path]:
    roots = [root / "tools", root / "tests", root / "src"]
    paths: list[pathlib.Path] = []
    for scan_root in roots:
        if not scan_root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(scan_root):
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_PARTS]
            current = pathlib.Path(dirpath)
            paths.extend(current / name for name in filenames if name.endswith(".py"))
    return sorted(paths, key=lambda item: item.as_posix().lower())


def _imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module]
    return []


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _scan_forbidden_python_usage(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    root = repo_root.resolve()
    for path in _python_paths(root):
        rel = pathlib.PurePosixPath(path.relative_to(root).as_posix())
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel} must parse for readiness usage scan: {exc}")
            continue
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                root_name = module.split(".", 1)[0]
                if (
                    module in FORBIDDEN_PYTHON_MODULES
                    and not _is_allowed_local_visual_qa_browser_module(rel, module)
                ) or root_name in FORBIDDEN_PYTHON_MODULE_ROOTS:
                    failures.append(f"{rel} imports forbidden network/client module {module}")
            if isinstance(node, ast.Call):
                name = _dotted_name(node.func)
                if name in {
                    "accept_source_fact",
                    "accept_source_evidence",
                    "accept_source_packet",
                    "create_accepted_source_evidence",
                    "bind_connector_semantic",
                    "bind_connector_semantics",
                    "fetch_private_state",
                    "get_account_balance",
                    "place_order",
                    "submit_order",
                    "send_order",
                    "cancel_order",
                    "reduce_order",
                    "close_order",
                }:
                    failures.append(f"{rel} calls forbidden authority function {name}")
                if name in {
                    "requests.get",
                    "requests.post",
                    "requests.request",
                    "httpx.get",
                    "httpx.post",
                    "httpx.request",
                    "urllib.request.urlopen",
                    "socket.socket",
                    "aiohttp.ClientSession",
                }:
                    failures.append(f"{rel} calls forbidden network/client function {name}")
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    source_to_connector_schema_path: pathlib.Path,
    source_to_connector_fixture_path: pathlib.Path,
    connector_target_schema_path: pathlib.Path,
    connector_target_fixture_path: pathlib.Path,
    gate_report_schema_path: pathlib.Path,
    gate_report_fixture_path: pathlib.Path,
    scan_python_usage: bool = True,
) -> list[str]:
    failures: list[str] = []
    source_schema, source_schema_failures = _load_json(source_to_connector_schema_path)
    source_fixture, source_fixture_failures = _load_json(source_to_connector_fixture_path)
    target_schema, target_schema_failures = _load_json(connector_target_schema_path)
    target_fixture, target_fixture_failures = _load_json(connector_target_fixture_path)
    report_schema, report_schema_failures = _load_json(gate_report_schema_path)
    report_fixture, report_fixture_failures = _load_json(gate_report_fixture_path)

    failures.extend(source_schema_failures)
    failures.extend(source_fixture_failures)
    failures.extend(target_schema_failures)
    failures.extend(target_fixture_failures)
    failures.extend(report_schema_failures)
    failures.extend(report_fixture_failures)

    if source_schema is not None:
        failures.extend(
            _validate_schema(
                source_schema,
                expected_type_field="matrix_type",
                expected_type=SOURCE_MATRIX_TYPE,
                expected_hook=VALIDATION_HOOK,
                schema_path=source_to_connector_schema_path,
            )
        )
    if target_schema is not None:
        failures.extend(
            _validate_schema(
                target_schema,
                expected_type_field="matrix_type",
                expected_type=CONNECTOR_MATRIX_TYPE,
                expected_hook=VALIDATION_HOOK,
                schema_path=connector_target_schema_path,
            )
        )
    if report_schema is not None:
        failures.extend(
            _validate_schema(
                report_schema,
                expected_type_field="report_type",
                expected_type=GATE_REPORT_TYPE,
                expected_hook=VALIDATION_HOOK,
                schema_path=gate_report_schema_path,
            )
        )

    if source_fixture is not None:
        failures.extend(validate_source_to_connector_matrix_fixture(source_fixture))
    if target_fixture is not None:
        failures.extend(validate_connector_semantic_target_field_matrix_fixture(target_fixture))
    if report_fixture is not None:
        failures.extend(validate_readiness_gate_report_fixture(report_fixture, repo_root=repo_root))

    failures.extend(_atomicrows_absence_failures(repo_root, "PR38 readiness validator"))
    if scan_python_usage:
        failures.extend(_scan_forbidden_python_usage(repo_root))
    return failures


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--source-to-connector-schema", required=True)
    parser.add_argument("--source-to-connector-fixture", required=True)
    parser.add_argument("--connector-target-schema", required=True)
    parser.add_argument("--connector-target-fixture", required=True)
    parser.add_argument("--gate-report-schema", required=True)
    parser.add_argument("--gate-report-fixture", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    failures = validate_static_surface(
        repo_root=pathlib.Path(args.repo_root),
        source_to_connector_schema_path=pathlib.Path(args.source_to_connector_schema),
        source_to_connector_fixture_path=pathlib.Path(args.source_to_connector_fixture),
        connector_target_schema_path=pathlib.Path(args.connector_target_schema),
        connector_target_fixture_path=pathlib.Path(args.connector_target_fixture),
        gate_report_schema_path=pathlib.Path(args.gate_report_schema),
        gate_report_fixture_path=pathlib.Path(args.gate_report_fixture),
    )
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
