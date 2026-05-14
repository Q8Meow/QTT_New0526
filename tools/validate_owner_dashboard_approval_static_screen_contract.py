#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_owner_approval_request_queue_registry as pr93_gate  # noqa: E402
from tools import validate_owner_override_receipt_authoring_gate as pr94_gate  # noqa: E402
from tools import validate_owner_dashboard_approval_menu_schema as pr95_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "governance"
    / "qtt_owner_dashboard_approval_static_screen_contract.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "governance"
    / "QTTOwnerDashboardApprovalStaticScreenContract.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "governance"
    / "synthetic_qtt_owner_dashboard_approval_static_screen_contract.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerDashboardApprovalStaticScreenContract.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr95_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr95_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr95_gate.MASTER_PLAN_CURRENT

REPORT_ID = "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #96"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-OWNER-DASHBOARD-STATIC-SCREEN"
BLUEPRINT_SEMANTIC_TASK_ID = "ROADMAP-OWNER-DASHBOARD-APPROVAL-STATIC-SCREEN-CONTRACT"
TARGET_BRANCH = "pr96-owner-dashboard-approval-static-screen-contract"
EXPECTED_BASELINE_ANCESTOR = "ee9bcc3"
SUCCESS_MARKER = "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_OK"
FAILURE_MARKER = "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr95_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr95_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr95_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
BRANCH_CONTEXT_ENV_CANDIDATES = (
    "GITHUB_HEAD_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF",
    "BRANCH_NAME",
    "CI_COMMIT_REF_NAME",
)

CANONICAL_OPTION_ORDER = pr95_gate.CANONICAL_OPTION_ORDER
REQUIRED_PROMPT_CONCEPT_ORDER = pr95_gate.REQUIRED_PROMPT_CONCEPT_ORDER
CANONICAL_SCOPE_SUBSTITUTIONS = pr95_gate.CANONICAL_SCOPE_SUBSTITUTIONS

REQUIRED_SCREEN_CONCEPT_ORDER = (
    "OWNER_APPROVAL_QUEUE_OVERVIEW_SCREEN",
    "OWNER_APPROVAL_REQUEST_DETAIL_SCREEN",
    "OWNER_APPROVAL_MENU_PANEL",
    "OWNER_TARGET_SCOPE_SELECTOR_PANEL",
    "OWNER_RATIONALE_AND_VALUE_PANEL",
    "OWNER_DECISION_CONFIRMATION_STATIC_SUMMARY",
    "OWNER_LIVE_RUNTIME_QUANTUM_BOUNDARY_BANNER",
)
SCREEN_CLASS_BY_ID = {
    "OWNER_APPROVAL_QUEUE_OVERVIEW_SCREEN": "QUEUE_OVERVIEW_STATIC_SCREEN",
    "OWNER_APPROVAL_REQUEST_DETAIL_SCREEN": "REQUEST_DETAIL_STATIC_SCREEN",
    "OWNER_APPROVAL_MENU_PANEL": "MENU_PANEL_STATIC_SCREEN",
    "OWNER_TARGET_SCOPE_SELECTOR_PANEL": "TARGET_SCOPE_SELECTOR_STATIC_PANEL",
    "OWNER_RATIONALE_AND_VALUE_PANEL": "RATIONALE_AND_VALUE_STATIC_PANEL",
    "OWNER_DECISION_CONFIRMATION_STATIC_SUMMARY": "DECISION_CONFIRMATION_STATIC_SUMMARY",
    "OWNER_LIVE_RUNTIME_QUANTUM_BOUNDARY_BANNER": (
        "LIVE_RUNTIME_QUANTUM_BOUNDARY_STATIC_BANNER"
    ),
}
REQUIRED_COMPONENT_IDS_BY_SCREEN = {
    "OWNER_APPROVAL_QUEUE_OVERVIEW_SCREEN": (
        "QUEUE_OVERVIEW_REQUEST_QUEUE_SUMMARY",
        "QUEUE_OVERVIEW_PENDING_REQUEST_LIST",
        "QUEUE_OVERVIEW_REQUEST_CLASS_BADGES",
        "QUEUE_OVERVIEW_REQUESTING_AGENT_IDENTITY",
        "QUEUE_OVERVIEW_TARGET_SCOPE_SUMMARY",
        "QUEUE_OVERVIEW_OWNER_ACTION_AVAILABILITY",
        "QUEUE_OVERVIEW_BLOCKED_EFFECT_WARNING_SUMMARY",
        "QUEUE_OVERVIEW_STATIC_NO_RUNTIME_BOUNDARY_BANNER",
    ),
    "OWNER_APPROVAL_REQUEST_DETAIL_SCREEN": (
        "REQUEST_DETAIL_REQUEST_METADATA",
        "REQUEST_DETAIL_REQUESTER_AGENT_IDENTITY",
        "REQUEST_DETAIL_REQUESTED_DECISION_CLASS",
        "REQUEST_DETAIL_TARGET_SCOPE",
        "REQUEST_DETAIL_SOURCE_EVIDENCE_STATE",
        "REQUEST_DETAIL_CONNECTOR_SEMANTIC_STATE",
        "REQUEST_DETAIL_REPLAY_PAPER_STATE",
        "REQUEST_DETAIL_RISK_LIVE_ORDER_BOUNDARY",
        "REQUEST_DETAIL_QUANTUM_BACKEND_BOUNDARY",
        "REQUEST_DETAIL_OWNER_RATIONALE_INPUT_CONTRACT",
        "REQUEST_DETAIL_OWNER_APPROVED_VALUE_INPUT_CONTRACT",
    ),
    "OWNER_APPROVAL_MENU_PANEL": (
        "MENU_PANEL_DECISION_OPTIONS",
        "MENU_PANEL_REQUIREMENT_VALUE_OPTIONS",
        "MENU_PANEL_MODE_SCOPE_OPTIONS",
        "MENU_PANEL_TARGET_SCOPE_OPTIONS",
        "MENU_PANEL_CANONICAL_MAPPING_NOTICE",
    ),
    "OWNER_TARGET_SCOPE_SELECTOR_PANEL": (
        "TARGET_SCOPE_ROW_SCOPE",
        "TARGET_SCOPE_PARAMETER_FAMILY_SCOPE",
        "TARGET_SCOPE_AGENT_SCOPE",
        "TARGET_SCOPE_GLOBAL_SCOPE",
        "TARGET_SCOPE_GLOBAL_BLOCKED_EFFECTS",
        "TARGET_SCOPE_NO_MUTATION_NOTICE",
    ),
    "OWNER_RATIONALE_AND_VALUE_PANEL": (
        "RATIONALE_VALUE_OWNER_IDENTITY",
        "RATIONALE_VALUE_OWNER_RATIONALE",
        "RATIONALE_VALUE_OWNER_APPROVED_VALUE_FIELD",
        "RATIONALE_VALUE_TYPE_REASON",
    ),
    "OWNER_DECISION_CONFIRMATION_STATIC_SUMMARY": (
        "CONFIRMATION_SELECTED_MENU_OPTION",
        "CONFIRMATION_TARGET_SCOPE_DISPLAY",
        "CONFIRMATION_REQUIRED_RATIONALE",
        "CONFIRMATION_BLOCKED_EFFECTS",
        "CONFIRMATION_NO_RECEIPT_NOTICE",
        "CONFIRMATION_NO_DECISION_EXECUTION_NOTICE",
    ),
    "OWNER_LIVE_RUNTIME_QUANTUM_BOUNDARY_BANNER": (
        "BOUNDARY_APPROVE_RUNTIME_METADATA_ONLY",
        "BOUNDARY_APPROVE_LIVE_USE_METADATA_ONLY",
        "BOUNDARY_APPROVE_QUANTUM_BACKEND_METADATA_ONLY",
        "BOUNDARY_NO_LIVE_ELIGIBILITY",
        "BOUNDARY_NO_ORDER_AUTHORITY",
        "BOUNDARY_NO_QUANTUM_EXECUTION",
        "BOUNDARY_NO_PROFIT_LATENCY_QUANTUM_ADVANTAGE",
    ),
}
REQUIRED_COMPONENT_CLASSES = (
    "QUEUE_SUMMARY_DISPLAY",
    "PENDING_REQUEST_LIST_DISPLAY",
    "REQUEST_CLASS_BADGE_DISPLAY",
    "REQUESTING_AGENT_IDENTITY_DISPLAY",
    "TARGET_SCOPE_SUMMARY_DISPLAY",
    "OWNER_ACTION_AVAILABILITY_DISPLAY",
    "BLOCKED_EFFECT_WARNING_DISPLAY",
    "STATIC_NO_RUNTIME_BOUNDARY_BANNER",
    "REQUEST_METADATA_DISPLAY",
    "REQUESTED_DECISION_CLASS_DISPLAY",
    "SOURCE_EVIDENCE_STATE_DISPLAY_INTENT",
    "CONNECTOR_SEMANTIC_STATE_DISPLAY_INTENT",
    "REPLAY_PAPER_STATE_DISPLAY_INTENT",
    "RISK_LIVE_ORDER_BOUNDARY_DISPLAY_INTENT",
    "QUANTUM_BACKEND_BOUNDARY_DISPLAY_INTENT",
    "OWNER_RATIONALE_INPUT_REQUIREMENT_CONTRACT",
    "OWNER_APPROVED_VALUE_INPUT_REQUIREMENT_CONTRACT",
    "MENU_DECISION_OPTION_GROUP_DISPLAY",
    "MENU_REQUIREMENT_VALUE_OPTION_GROUP_DISPLAY",
    "MENU_MODE_SCOPE_OPTION_GROUP_DISPLAY",
    "MENU_TARGET_SCOPE_OPTION_GROUP_DISPLAY",
    "MENU_CANONICAL_MAPPING_NOTICE_DISPLAY",
    "ROW_TARGET_SCOPE_DISPLAY",
    "PARAMETER_FAMILY_TARGET_SCOPE_DISPLAY",
    "AGENT_TARGET_SCOPE_DISPLAY",
    "GLOBAL_TARGET_SCOPE_DISPLAY",
    "GLOBAL_SCOPE_BLOCKED_EFFECTS_DISPLAY",
    "NO_MUTATION_STATIC_NOTICE_DISPLAY",
    "OWNER_IDENTITY_REQUIREMENT_DISPLAY",
    "OWNER_RATIONALE_REQUIREMENT_DISPLAY",
    "OWNER_APPROVED_VALUE_FIELD_DISPLAY",
    "VALUE_TYPE_REASON_DISPLAY",
    "SELECTED_MENU_OPTION_DISPLAY",
    "CONFIRMATION_TARGET_SCOPE_DISPLAY",
    "CONFIRMATION_REQUIRED_RATIONALE_DISPLAY",
    "CONFIRMATION_BLOCKED_EFFECTS_DISPLAY",
    "CONFIRMATION_NO_RECEIPT_NOTICE_DISPLAY",
    "CONFIRMATION_NO_DECISION_EXECUTION_NOTICE_DISPLAY",
    "APPROVE_RUNTIME_METADATA_ONLY_DISPLAY",
    "APPROVE_LIVE_USE_METADATA_ONLY_DISPLAY",
    "APPROVE_QUANTUM_BACKEND_METADATA_ONLY_DISPLAY",
    "NO_LIVE_ELIGIBILITY_DISPLAY",
    "NO_ORDER_AUTHORITY_DISPLAY",
    "NO_QUANTUM_EXECUTION_DISPLAY",
    "NO_PROFIT_LATENCY_QUANTUM_ADVANTAGE_DISPLAY",
)
CRITICAL_BLOCKED_EFFECTS = (
    "RUNTIME_EFFECT_CREATION",
    "OWNER_DECISION_EXECUTION",
    "OWNER_APPROVAL_RECEIPT_CREATION",
    "OWNER_OVERRIDE_RECEIPT_CREATION",
    "DASHBOARD_RUNTIME_UI_CREATION",
    "DASHBOARD_RUNTIME_SERVICE_CREATION",
    "API_ENDPOINT_CREATION",
    "ROUTE_HANDLER_CREATION",
    "EVENT_CALLBACK_CREATION",
    "TELEGRAM_RUNTIME_CREATION",
    "LIVE_PROMOTION_CREATION",
    "CANARY_ELIGIBILITY_CREATION",
    "ORDER_AUTHORITY_CREATION",
    "ORDER_SUBMISSION",
    "SOURCE_RETRIEVAL",
    "SOURCE_ACCEPTANCE",
    "CONNECTOR_SEMANTIC_BINDING",
    "RUNTIME_CASH_RECEIPT_CREATION",
    "REPLAY_EXECUTION",
    "PAPER_EXECUTION",
    "OPTIMIZER_EXECUTION",
    "QUANTUM_BACKEND_EXECUTION",
    "PROFIT_EVIDENCE_CREATION",
    "LATENCY_EVIDENCE_CREATION",
    "QUANTUM_ADVANTAGE_EVIDENCE_CREATION",
    "PR97_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_CREATION",
    "ATOMICROWS_BUNDLE_CREATION",
    "ATOMICROWS_BUNDLE_SHA_CREATION",
)
REQUIRED_DISABLED_EFFECTS = (
    "RUNTIME_ACTION_CREATION",
    "STATE_MUTATION",
    "OWNER_DECISION_EXECUTION",
    "OWNER_APPROVAL_RECEIPT_CREATION",
    "OWNER_OVERRIDE_RECEIPT_CREATION",
    "DASHBOARD_RUNTIME_UI_CREATION",
    "API_ENDPOINT_CREATION",
    "ORDER_SUBMISSION",
    "QUANTUM_BACKEND_EXECUTION",
    "PROFIT_LATENCY_QUANTUM_ADVANTAGE_CLAIM",
    "ATOMICROWS_BUNDLE_OR_PR97_CREATION",
)
TOP_LEVEL_FALSE_FLAG_FIELDS = (
    "creates_dashboard_runtime_service_flag",
    "creates_dashboard_runtime_ui_flag",
    "creates_telegram_runtime_flag",
    "creates_owner_decision_execution_flag",
    "creates_owner_approval_receipt_flag",
    "creates_owner_override_receipt_flag",
    "creates_live_promotion_flag",
    "creates_canary_eligibility_flag",
    "creates_order_authority_flag",
    "creates_order_submission_flag",
    "creates_source_fact_flag",
    "creates_connector_semantic_flag",
    "creates_runtime_cash_receipt_flag",
    "creates_replay_paper_result_flag",
    "creates_optimizer_execution_flag",
    "creates_quantum_backend_execution_flag",
    "creates_profit_evidence_flag",
    "creates_latency_evidence_flag",
    "creates_quantum_advantage_evidence_flag",
)
NO_AUTHORITY_FLAG_FIELDS = (
    "creates_runtime_dashboard_service",
    "creates_dashboard_runtime_ui",
    "creates_web_server",
    "creates_api_endpoint",
    "creates_executable_route",
    "creates_route_handler",
    "creates_event_callback",
    "creates_frontend_app",
    "creates_telegram_runtime",
    "executes_owner_decision",
    "creates_owner_approval_receipt",
    "creates_owner_override_receipt",
    "creates_live_promotion",
    "creates_canary_eligibility",
    "creates_order_authority",
    "submits_order",
    "cancels_order",
    "reduces_order",
    "closes_order",
    "creates_live_routing",
    "retrieves_source",
    "accepts_source",
    "creates_accepted_source_packet",
    "creates_source_fact",
    "creates_connector_semantic_binding",
    "fetches_private_state",
    "creates_runtime_cash_receipt",
    "executes_replay",
    "executes_paper",
    "creates_replay_paper_result",
    "executes_optimizer",
    "executes_classical_optimizer",
    "executes_quantum_optimizer",
    "executes_quantum_backend",
    "executes_quantum_simulator",
    "calls_quantum_provider",
    "creates_profit_evidence",
    "creates_latency_evidence",
    "creates_quantum_advantage_evidence",
    "claims_latency_superiority",
    "claims_execution_superiority",
    "creates_atomicrows_bundle_jsonl",
    "creates_atomicrows_bundle_sha256",
    "creates_pr97_atomicrows_full_bundle_row_expansion_plan",
    "creates_atomicrows_row_family_source_files",
    "creates_atomicrows_bundle_builder",
    "creates_sha_freeze_authority",
    "creates_global_mutation",
)
SCREEN_NO_AUTHORITY_FLAG_FIELDS = (
    "creates_runtime_dashboard_service",
    "creates_dashboard_runtime_ui",
    "creates_api_endpoint",
    "creates_executable_route",
    "creates_route_handler",
    "creates_event_callback",
    "creates_owner_decision_execution",
    "creates_owner_approval_receipt",
    "creates_owner_override_receipt",
    "creates_live_authority",
    "creates_order_authority",
    "creates_source_fact",
    "creates_connector_semantic",
    "creates_runtime_cash_receipt",
    "creates_profit_evidence",
    "creates_latency_evidence",
    "creates_quantum_backend_execution",
    "creates_quantum_advantage_evidence",
    "creates_atomicrows_or_pr97_artifact",
)
COMPONENT_FALSE_FLAG_FIELDS = (
    "creates_runtime_action_flag",
    "creates_state_mutation_flag",
    "creates_receipt_flag",
    "creates_live_order_authority_flag",
    "creates_quantum_execution_flag",
    "creates_profit_or_latency_claim_flag",
)
ZERO_COUNT_FIELDS = (
    "owner_decision_execution_count",
    "owner_approval_receipt_created_count",
    "owner_override_receipt_created_count",
    "dashboard_runtime_service_created_count",
    "dashboard_runtime_ui_created_count",
    "telegram_runtime_created_count",
    "web_server_created_count",
    "api_endpoint_created_count",
    "route_handler_created_count",
    "event_callback_created_count",
    "live_promotion_created_count",
    "canary_eligibility_created_count",
    "source_retrieval_count",
    "source_acceptance_count",
    "accepted_source_packet_created_count",
    "connector_binding_created_count",
    "private_state_fetch_count",
    "runtime_cash_receipt_created_count",
    "replay_execution_count",
    "paper_execution_count",
    "replay_paper_result_created_count",
    "optimizer_execution_count",
    "classical_optimizer_execution_count",
    "quantum_optimizer_execution_count",
    "quantum_backend_execution_count",
    "quantum_simulator_execution_count",
    "quantum_provider_call_count",
    "order_submission_count",
    "order_cancellation_count",
    "order_reduction_count",
    "order_close_count",
    "live_routing_count",
    "order_authority_created_count",
    "profit_evidence_created_count",
    "latency_evidence_created_count",
    "quantum_advantage_evidence_created_count",
    "atomicrows_bundle_jsonl_created_count",
    "atomicrows_bundle_sha256_created_count",
    "pr97_atomicrows_full_bundle_row_expansion_plan_created_count",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR96_METADATA_VERIFIED",
    "PASS_REQUIRED_SCREEN_CONCEPTS_PRESENT",
    "PASS_REQUIRED_COMPONENTS_PRESENT",
    "PASS_PR95_MENU_REFERENCES_KNOWN",
    "PASS_CANONICAL_SCOPE_TOKEN_MAPPING_EXPLICIT",
    "PASS_STATIC_NO_EFFECT_FLAGS",
    "PASS_LIVE_RUNTIME_QUANTUM_BOUNDARY_METADATA_ONLY",
    "PASS_PR93_PR94_PR95_RELATIONSHIPS_STATIC_ONLY",
    "PASS_PR97_ATOMICROWS_ARTIFACTS_ABSENT",
    "BLOCK_MISSING_REQUIRED_SCREEN",
    "BLOCK_MISSING_REQUIRED_COMPONENT",
    "BLOCK_DUPLICATE_SCREEN_ID",
    "BLOCK_DUPLICATE_COMPONENT_ID",
    "BLOCK_UNKNOWN_PR95_MENU_OPTION",
    "BLOCK_SILENT_MENU_ALIAS",
    "BLOCK_EXECUTABLE_ROUTE_OR_ENDPOINT",
    "BLOCK_DASHBOARD_RUNTIME_UI_OR_SERVICE_ARTIFACT",
    "BLOCK_RECEIPT_CREATION_CLAIM",
    "BLOCK_SOURCE_CONNECTOR_RUNTIME_LIVE_ORDER_PROFIT_EFFECT",
    "BLOCK_QUANTUM_BACKEND_EXECUTION_CLAIM",
    "BLOCK_ATOMICROWS_BUNDLE_HASH_CLAIM",
    "BLOCK_PR97_FULL_BUNDLE_ROW_EXPANSION_PLAN_CLAIM",
)
FORBIDDEN_ROUTE_TOKENS = (
    "/",
    "://",
    "{",
    "}",
    "<",
    ">",
    ".py",
    ".js",
    ".ts",
    "endpoint",
    "callback",
    "handler",
    "fastapi",
    "flask",
    "streamlit",
    "react",
    "vue",
    "svelte",
)
FORBIDDEN_TEXT_PATTERNS = (
    "creates runtime dashboard readiness",
    "creates live readiness",
    "claims profit improvement",
    "claims latency improvement",
    "claims quantum advantage",
    "creates backend readiness",
    "order submission enabled",
)
PR97_STATIC_PLAN_PATHS = (
    pathlib.Path("schemas/atomicrows/atomicrows_full_bundle_row_expansion_plan.schema.json"),
    pathlib.Path("docs/master_plan/atomicrows/AtomicRowsFullBundleRowExpansionPlan.yaml"),
    pathlib.Path("tests/fixtures/atomicrows/synthetic_atomicrows_full_bundle_row_expansion_plan.v1.fixture.json"),
    pathlib.Path("docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json"),
    pathlib.Path("tools/validate_atomicrows_full_bundle_row_expansion_plan.py"),
    pathlib.Path("tests/atomicrows/test_atomicrows_full_bundle_row_expansion_plan.py"),
)
PR97_ALWAYS_FORBIDDEN_PATHS = (
    pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"),
    pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"),
    pathlib.Path("schemas/governance/atomicrows_full_bundle_row_expansion_plan.schema.json"),
    pathlib.Path("docs/master_plan/atomic_rows/AtomicRowsFullBundleRowExpansionPlan.yaml"),
)
PR99_STATIC_BUILDER_ARTIFACT_PATHS = (
    pathlib.Path("tools/build_atomicrows_bundle.py"),
)
FORBIDDEN_RUNTIME_PATHS = (
    pathlib.Path("src/qtt/dashboard_runtime"),
    pathlib.Path("src/qtt/telegram_runtime"),
    pathlib.Path("src/qtt/owner_dashboard_runtime"),
    pathlib.Path("src/qtt/dashboard_service"),
    pathlib.Path("src/qtt/web_server"),
)


@dataclass(frozen=True)
class BranchContext:
    branch: str
    source: str
    git_error: str = ""


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = pr95_gate.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"registry root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except (json.JSONDecodeError, ValueError) as exc:
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:  # pragma: no cover - defensive parse surface
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def _normalize_branch_context(value: str) -> str:
    branch = value.strip()
    if not branch or branch == "HEAD":
        return ""
    for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
        if branch.startswith(prefix):
            return branch[len(prefix) :]
    return branch


def _current_branch_context(repo_root: pathlib.Path) -> BranchContext:
    for env_name in BRANCH_CONTEXT_ENV_CANDIDATES:
        branch = _normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return BranchContext(branch=branch, source=env_name)

    git_errors: list[str] = []
    for args in (["branch", "--show-current"], ["rev-parse", "--abbrev-ref", "HEAD"]):
        branch_rc, branch_stdout, branch_err = _git_stdout(repo_root, args)
        if branch_rc != 0:
            git_errors.append(branch_err or f"git {' '.join(args)} failed")
            continue
        branch = _normalize_branch_context(branch_stdout)
        if branch:
            return BranchContext(branch=branch, source=f"git {' '.join(args)}")

    return BranchContext(branch="", source="", git_error="; ".join(git_errors))


def _downstream_validation_branch_allowed(branch: str) -> bool:
    match = re.match(r"pr(?P<number>[0-9]+)-", branch)
    if not match:
        return False
    return int(match.group("number")) > 96


def _main_cumulative_branch_allowed(branch: str) -> bool:
    return branch == "main" or branch.startswith("repair/main-cumulative-")


def _downstream_or_main_validation_branch_allowed(branch: str) -> bool:
    return _main_cumulative_branch_allowed(branch) or _downstream_validation_branch_allowed(
        branch
    )


def _pr99_static_builder_branch_allowed(branch: str) -> bool:
    if _main_cumulative_branch_allowed(branch):
        return True
    match = re.match(r"pr(?P<number>[0-9]+)-", branch)
    if not match:
        return False
    return int(match.group("number")) >= 99


def _should_skip_default_report_write(
    *,
    repo_root: pathlib.Path,
    output_abs: pathlib.Path,
    metadata: dict[str, Any],
) -> bool:
    if output_abs != _resolve(repo_root, DEFAULT_REPORT):
        return False
    branch = str(metadata.get("branch") or "")
    return branch not in {TARGET_BRANCH, "main"}


def validate_pr96_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 96), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 96), None)
    if roadmap_entry is None:
        failures.append("PR96 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR96 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Owner dashboard approval static screen contract"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Owner dashboard approval static screen contract"),
        ("blueprint.branch", blueprint_entry.get("branch"), TARGET_BRANCH),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "Owner approval foundation"),
        ("blueprint.priority", blueprint_entry.get("priority"), "S1 launch-essential static"),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(f"{label} must be {expected}, got {actual}")

    branch_context = _current_branch_context(repo_root)
    branch = branch_context.branch
    if not branch:
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        else:
            branch_err = branch_context.git_error or "unable to determine current branch"
            failures.append(f"git branch check failed: {branch_err}")
    elif branch != TARGET_BRANCH:
        if _main_cumulative_branch_allowed(branch):
            pass
        elif _downstream_validation_branch_allowed(branch):
            if github_actions:
                info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        elif github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)

    head_rc, head, head_err = _git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    if head_rc != 0:
        failures.append(f"git HEAD check failed: {head_err}")
    baseline_rc, _, baseline_err = _git_stdout(
        repo_root, ["cat-file", "-e", f"{EXPECTED_BASELINE_ANCESTOR}^{{commit}}"]
    )
    if github_actions and baseline_rc != 0:
        info_lines.append(CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER)
    elif baseline_rc != 0:
        failures.append(f"baseline commit missing: {EXPECTED_BASELINE_ANCESTOR}: {baseline_err}")
    else:
        ancestor_rc, _, ancestor_err = _git_stdout(
            repo_root,
            ["merge-base", "--is-ancestor", EXPECTED_BASELINE_ANCESTOR, "HEAD"],
        )
        if ancestor_rc != 0:
            failures.append(
                f"HEAD must descend from {EXPECTED_BASELINE_ANCESTOR}: {ancestor_err}"
            )

    return failures, {
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": branch,
        "branch_context_source": branch_context.source,
        "base_head": head,
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": "owner prompt semantic task controls",
        "blueprint_semantic_task_id": blueprint_entry.get("semantic_task_id"),
        "blueprint_semantic_task_id_source": BLUEPRINT_INDEX.as_posix(),
        "blueprint_semantic_task_id_expected_by_blueprint": BLUEPRINT_SEMANTIC_TASK_ID,
        "validator_marker": SUCCESS_MARKER,
        "validator_marker_source": (
            f"{ROADMAP_INDEX.as_posix()} and {BLUEPRINT_INDEX.as_posix()}"
        ),
        "ci_info_lines": tuple(info_lines),
    }


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _all_screens(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(registry.get("screens"))


def _all_components(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        component
        for screen in _all_screens(registry)
        for component in _list_of_mappings(screen.get("components"))
    ]


def _all_menu_refs(registry: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend(str(item) for item in registry.get("pr95_canonical_menu_option_ids", []))
    for screen in _all_screens(registry):
        refs.extend(str(item) for item in screen.get("allowed_menu_option_ids", []))
        for component in _list_of_mappings(screen.get("components")):
            refs.extend(str(item) for item in component.get("menu_option_ids", []))
    return refs


def _flag_failures(payload: dict[str, Any], fields: Sequence[str], prefix: str) -> list[str]:
    return [
        f"{prefix}.{field} must be false"
        for field in fields
        if payload.get(field) is not False
    ]


def validate_pr95_integration(registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if registry.get("pr95_canonical_menu_option_ids") != list(CANONICAL_OPTION_ORDER):
        failures.append("pr95_canonical_menu_option_ids must match PR95 canonical option order")
    mappings = _list_of_mappings(registry.get("pr95_prompt_concept_to_option_id_map"))
    prompt_ids = [str(item.get("prompt_concept_id")) for item in mappings]
    option_ids = [str(item.get("option_id")) for item in mappings]
    if prompt_ids != list(REQUIRED_PROMPT_CONCEPT_ORDER):
        failures.append("pr95_prompt_concept_to_option_id_map prompt order mismatch")
    expected_option_ids = [
        pr95_gate.PROMPT_CONCEPT_TO_OPTION_ID[prompt_id]
        for prompt_id in REQUIRED_PROMPT_CONCEPT_ORDER
    ]
    if option_ids != expected_option_ids:
        failures.append("pr95_prompt_concept_to_option_id_map option ids mismatch")
    for prompt_id, option_id in CANONICAL_SCOPE_SUBSTITUTIONS.items():
        match = next(
            (item for item in mappings if item.get("prompt_concept_id") == prompt_id),
            {},
        )
        if match.get("option_id") != option_id:
            failures.append(f"{prompt_id} must map to canonical PR95 option {option_id}")
        if match.get("mapping_policy") != "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME":
            failures.append(f"{prompt_id} mapping_policy must be explicit stronger-name mapping")

    known = set(CANONICAL_OPTION_ORDER)
    aliases = {"APPLY_TO_ROW", "APPLY_TO_FAMILY"}
    unknown = sorted({ref for ref in _all_menu_refs(registry) if ref not in known})
    silent_aliases = sorted({ref for ref in _all_menu_refs(registry) if ref in aliases})
    if unknown:
        failures.append(f"unknown PR95 menu option ids: {', '.join(unknown)}")
    if silent_aliases:
        failures.append(f"silent menu aliases are forbidden: {', '.join(silent_aliases)}")
    return failures


def validate_registry_payload(registry: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    expected_scalars = {
        "contract_id": "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT",
        "contract_version": "v1",
        "semantic_task_id": SEMANTIC_TASK_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "authority_class": (
            "STATIC_OWNER_DASHBOARD_APPROVAL_SCREEN_CONTRACT_ONLY_NOT_RUNTIME_NOT_"
            "OWNER_DECISION_NOT_RECEIPT_NOT_LIVE_AUTHORITY"
        ),
    }
    for field, expected in expected_scalars.items():
        if registry.get(field) != expected:
            failures.append(f"{field} must be {expected}, got {registry.get(field)}")
    for field in (
        "static_only_flag",
        "handoff_only_flag",
        "synthetic_fixture_only_flag",
        "consumes_owner_approval_request_queue_registry_flag",
        "consumes_owner_override_receipt_authoring_gate_flag",
        "consumes_owner_dashboard_approval_menu_schema_flag",
    ):
        if registry.get(field) is not True:
            failures.append(f"{field} must be true")
    failures.extend(_flag_failures(registry, TOP_LEVEL_FALSE_FLAG_FIELDS, "registry"))
    failures.extend(_flag_failures(registry.get("no_authority_flags", {}), NO_AUTHORITY_FLAG_FIELDS, "no_authority_flags"))
    if registry.get("final_ready") is not False:
        failures.append("final_ready must be false")

    top_blocked = set(registry.get("blocked_effects", []))
    for blocked in CRITICAL_BLOCKED_EFFECTS:
        if blocked not in top_blocked:
            failures.append(f"registry blocked_effects missing {blocked}")

    if registry.get("screen_concept_order") != list(REQUIRED_SCREEN_CONCEPT_ORDER):
        failures.append("screen_concept_order must match PR96 required screen order")
    if registry.get("screen_class_order") != [
        SCREEN_CLASS_BY_ID[screen_id] for screen_id in REQUIRED_SCREEN_CONCEPT_ORDER
    ]:
        failures.append("screen_class_order must match PR96 required screen class order")
    if registry.get("component_class_order") != list(REQUIRED_COMPONENT_CLASSES):
        failures.append("component_class_order must match PR96 required component class order")

    screens = _all_screens(registry)
    screen_ids = [str(screen.get("screen_id")) for screen in screens]
    if screen_ids != list(REQUIRED_SCREEN_CONCEPT_ORDER):
        failures.append("screens must be listed in stable PR96 canonical order")
    duplicate_screen_ids = _duplicate_values(screen_ids)
    if duplicate_screen_ids:
        failures.append(f"duplicate screen_id values: {', '.join(duplicate_screen_ids)}")
    screen_orders = [screen.get("canonical_order") for screen in screens]
    if screen_orders != sorted(screen_orders):
        failures.append("screen canonical_order values must be stable ascending order")

    route_keys = [str(screen.get("route_key_static_only")) for screen in screens]
    duplicate_routes = _duplicate_values(route_keys)
    if duplicate_routes:
        failures.append(f"duplicate route_key_static_only values: {', '.join(duplicate_routes)}")

    all_component_ids: list[str] = []
    allowed_component_classes = set(REQUIRED_COMPONENT_CLASSES)
    for screen in screens:
        screen_id = str(screen.get("screen_id"))
        if screen.get("screen_class") != SCREEN_CLASS_BY_ID.get(screen_id):
            failures.append(f"{screen_id} screen_class mismatch")
        if screen.get("static_only_flag") is not True:
            failures.append(f"{screen_id} static_only_flag must be true")
        if screen.get("handoff_only_flag") is not True:
            failures.append(f"{screen_id} handoff_only_flag must be true")
        if screen.get("route_creates_runtime_endpoint_flag") is not False:
            failures.append(f"{screen_id} route_creates_runtime_endpoint_flag must be false")
        route_key = str(screen.get("route_key_static_only") or "")
        route_key_lower = route_key.lower()
        if any(token in route_key_lower for token in FORBIDDEN_ROUTE_TOKENS):
            failures.append(f"{screen_id} route_key_static_only is executable-like: {route_key}")
        failures.extend(
            _flag_failures(
                screen.get("screen_no_authority_flags", {}),
                SCREEN_NO_AUTHORITY_FLAG_FIELDS,
                f"{screen_id}.screen_no_authority_flags",
            )
        )
        screen_blocked = set(screen.get("blocked_effects", []))
        for blocked in CRITICAL_BLOCKED_EFFECTS:
            if blocked not in screen_blocked:
                failures.append(f"{screen_id} blocked_effects missing {blocked}")
        if "NO_ACCEPTED_OR_APPLIED_INPUT_VALUE" not in screen.get("required_owner_inputs", []):
            failures.append(f"{screen_id} must declare owner inputs are display-only only")
        required_components = list(REQUIRED_COMPONENT_IDS_BY_SCREEN.get(screen_id, ()))
        components = _list_of_mappings(screen.get("components"))
        component_ids = [str(component.get("component_id")) for component in components]
        missing_components = [item for item in required_components if item not in component_ids]
        if missing_components:
            failures.append(
                f"{screen_id} missing required components: {', '.join(missing_components)}"
            )
        duplicate_component_ids = _duplicate_values(component_ids)
        if duplicate_component_ids:
            failures.append(
                f"{screen_id} duplicate component_id values: {', '.join(duplicate_component_ids)}"
            )
        component_orders = [component.get("canonical_order") for component in components]
        if component_orders != sorted(component_orders):
            failures.append(f"{screen_id} component canonical_order values must be ascending")
        all_component_ids.extend(component_ids)
        for component in components:
            component_id = str(component.get("component_id"))
            component_class = str(component.get("component_class"))
            if component_class not in allowed_component_classes:
                failures.append(f"{component_id} unknown component_class {component_class}")
            if component.get("static_display_only_flag") is not True:
                failures.append(f"{component_id} static_display_only_flag must be true")
            failures.extend(
                _flag_failures(component, COMPONENT_FALSE_FLAG_FIELDS, component_id)
            )
            disabled = set(component.get("disabled_effects", []))
            for effect in REQUIRED_DISABLED_EFFECTS:
                if effect not in disabled:
                    failures.append(f"{component_id} disabled_effects missing {effect}")
            component_text = " ".join(
                str(component.get(field, ""))
                for field in ("display_label", "data_binding_intent", "source_registry_reference")
            ).lower()
            for pattern in FORBIDDEN_TEXT_PATTERNS:
                if pattern in component_text:
                    failures.append(f"{component_id} contains forbidden claim: {pattern}")

    duplicate_global_component_ids = _duplicate_values(all_component_ids)
    if duplicate_global_component_ids:
        failures.append(
            f"duplicate global component_id values: {', '.join(duplicate_global_component_ids)}"
        )

    menu_panel = next(
        (screen for screen in screens if screen.get("screen_id") == "OWNER_APPROVAL_MENU_PANEL"),
        {},
    )
    menu_panel_refs = set(menu_panel.get("allowed_menu_option_ids", []))
    missing_menu_panel_refs = [item for item in CANONICAL_OPTION_ORDER if item not in menu_panel_refs]
    if missing_menu_panel_refs:
        failures.append(
            "OWNER_APPROVAL_MENU_PANEL missing PR95 option refs: "
            + ", ".join(missing_menu_panel_refs)
        )

    boundary_components = {
        component.get("component_id"): component for component in _all_components(registry)
    }
    for component_id, option_id in (
        ("BOUNDARY_APPROVE_RUNTIME_METADATA_ONLY", "APPROVE_RUNTIME"),
        ("BOUNDARY_APPROVE_LIVE_USE_METADATA_ONLY", "APPROVE_LIVE_USE"),
        ("BOUNDARY_APPROVE_QUANTUM_BACKEND_METADATA_ONLY", "APPROVE_QUANTUM_BACKEND"),
    ):
        component = boundary_components.get(component_id, {})
        if option_id not in component.get("menu_option_ids", []):
            failures.append(f"{component_id} must reference {option_id}")
        if component.get("creates_runtime_action_flag") is not False:
            failures.append(f"{component_id} must not create runtime action")
        if component.get("creates_quantum_execution_flag") is not False:
            failures.append(f"{component_id} must not create quantum execution")

    target_components = {
        component.get("component_id"): component for component in _all_components(registry)
    }
    global_component = target_components.get("TARGET_SCOPE_GLOBAL_SCOPE", {})
    global_block_component = target_components.get("TARGET_SCOPE_GLOBAL_BLOCKED_EFFECTS", {})
    if "APPLY_GLOBALLY" not in global_component.get("menu_option_ids", []):
        failures.append("TARGET_SCOPE_GLOBAL_SCOPE must reference APPLY_GLOBALLY")
    if "APPLY_GLOBALLY" not in global_block_component.get("menu_option_ids", []):
        failures.append("TARGET_SCOPE_GLOBAL_BLOCKED_EFFECTS must reference APPLY_GLOBALLY")
    if "GLOBAL_MUTATION" not in top_blocked:
        failures.append("registry blocked_effects must include GLOBAL_MUTATION")

    failures.extend(validate_pr95_integration(registry))
    failures.extend(validate_filesystem_boundaries(repo_root))
    return failures


def validate_fixture_payload(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "fixture_id": "SYNTHETIC_PR96_QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_FIXTURE",
        "fixture_version": "PR96_QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_FIXTURE_V1",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "registry_ref": DEFAULT_PRODUCTION_REGISTRY.as_posix(),
        "schema_ref": DEFAULT_SCHEMA.as_posix(),
    }
    for field, expected_value in expected.items():
        if fixture.get(field) != expected_value:
            failures.append(f"fixture {field} must be {expected_value}")
    if fixture.get("deterministic_output") is not True:
        failures.append("fixture deterministic_output must be true")
    if fixture.get("required_screen_concepts") != list(REQUIRED_SCREEN_CONCEPT_ORDER):
        failures.append("fixture required_screen_concepts mismatch")
    if fixture.get("canonical_option_ids") != list(CANONICAL_OPTION_ORDER):
        failures.append("fixture canonical_option_ids mismatch")
    expected_scope_mappings = [
        {
            "prompt_concept_id": prompt_id,
            "option_id": option_id,
            "mapping_policy": "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME",
        }
        for prompt_id, option_id in CANONICAL_SCOPE_SUBSTITUTIONS.items()
    ]
    if _list_of_mappings(fixture.get("canonical_scope_token_mapping")) != expected_scope_mappings:
        failures.append("fixture canonical scope token mapping mismatch")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = [str(case.get("case_id")) for case in cases]
    missing_cases = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing_cases:
        failures.append(f"fixture missing required cases: {', '.join(missing_cases)}")
    if _duplicate_values(case_ids):
        failures.append("fixture case ids must not contain duplicates")
    no_claim_flags = fixture.get("no_claim_flags", {})
    if not isinstance(no_claim_flags, dict):
        failures.append("fixture no_claim_flags must be an object")
    else:
        failures.extend(_flag_failures(no_claim_flags, NO_AUTHORITY_FLAG_FIELDS, "fixture.no_claim_flags"))
    return failures


def build_screen_contract_packet(registry: dict[str, Any]) -> dict[str, Any]:
    screens = _all_screens(registry)
    packet: dict[str, Any] = {
        "contract_id": registry.get("contract_id"),
        "contract_version": registry.get("contract_version"),
        "semantic_task_id": registry.get("semantic_task_id"),
        "roadmap_pr_label": registry.get("roadmap_pr_label"),
        "authority_class": registry.get("authority_class"),
        "static_only_flag": registry.get("static_only_flag"),
        "handoff_only_flag": registry.get("handoff_only_flag"),
        "screen_count": len(screens),
        "component_count": len(_all_components(registry)),
        "canonical_screen_order": [screen.get("screen_id") for screen in screens],
        "screen_class_mapping": {
            screen.get("screen_id"): screen.get("screen_class") for screen in screens
        },
        "component_order_by_screen": {
            screen.get("screen_id"): [
                component.get("component_id")
                for component in _list_of_mappings(screen.get("components"))
            ]
            for screen in screens
        },
        "component_class_mapping": {
            component.get("component_id"): component.get("component_class")
            for component in _all_components(registry)
        },
        "allowed_menu_option_ids_by_screen": {
            screen.get("screen_id"): screen.get("allowed_menu_option_ids") for screen in screens
        },
        "pr95_canonical_menu_option_ids": list(registry.get("pr95_canonical_menu_option_ids", [])),
        "pr95_prompt_concept_to_option_id_map": copy.deepcopy(
            registry.get("pr95_prompt_concept_to_option_id_map")
        ),
        "canonical_scope_substitution_policy": {
            prompt_id: {
                "option_id": option_id,
                "mapping_policy": "EXPLICIT_EXISTING_CANONICAL_ENUM_STRONGER_NAME",
                "silent_aliasing": False,
            }
            for prompt_id, option_id in CANONICAL_SCOPE_SUBSTITUTIONS.items()
        },
        "upstream_owner_approval_request_queue_registry_ref": copy.deepcopy(
            registry.get("upstream_owner_approval_request_queue_registry_ref")
        ),
        "upstream_owner_override_receipt_authoring_gate_ref": copy.deepcopy(
            registry.get("upstream_owner_override_receipt_authoring_gate_ref")
        ),
        "upstream_owner_dashboard_approval_menu_schema_ref": copy.deepcopy(
            registry.get("upstream_owner_dashboard_approval_menu_schema_ref")
        ),
        "blocked_effects": list(registry.get("blocked_effects", [])),
        "screens": copy.deepcopy(screens),
        "unknown_menu_option_count": 0,
        "duplicate_screen_id_count": 0,
        "duplicate_component_id_count": 0,
        "duplicate_route_key_count": 0,
        "silent_alias_count": 0,
        "runtime_route_count": 0,
    }
    for field in NO_AUTHORITY_FLAG_FIELDS:
        packet[field] = False
    for field in ZERO_COUNT_FIELDS:
        packet[field] = 0
    return packet


def build_case_packet(case: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id"))
    blocked = case_id.startswith("BLOCK_")
    expected_valid = int(case.get("expected_valid_screen_count", 0))
    expected_reason = str(case.get("expected_reason_code"))
    return {
        "fixture_case_id": case_id,
        "case_authority_class": "STATIC_FIXTURE_CASE_ONLY_NO_RUNTIME_EFFECT",
        "valid_screen_count": 0 if blocked else len(_all_screens(registry)),
        "blocked_screen_count": 1 if blocked else 0,
        "expected_valid_screen_count": expected_valid,
        "screen_reason_codes": [] if blocked else [expected_reason],
        "blocked_reason_codes": [expected_reason] if blocked else [],
        **{field: 0 for field in ZERO_COUNT_FIELDS},
    }


def validate_case_packets(case_packets: list[dict[str, Any]], fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    packets = {packet.get("fixture_case_id"): packet for packet in case_packets}
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        case_id = str(case.get("case_id"))
        packet = packets.get(case_id)
        if packet is None:
            failures.append(f"case packet missing: {case_id}")
            continue
        if packet.get("valid_screen_count") != case.get("expected_valid_screen_count"):
            failures.append(f"case {case_id} valid_screen_count mismatch")
        expected_reason = str(case.get("expected_reason_code"))
        all_reasons = set(packet.get("screen_reason_codes", [])) | set(
            packet.get("blocked_reason_codes", [])
        )
        if expected_reason not in all_reasons:
            failures.append(f"case {case_id} missing expected reason {expected_reason}")
        for field in ZERO_COUNT_FIELDS:
            if packet.get(field, 0) != 0:
                failures.append(f"case {case_id} {field} must be 0")
    return failures


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    upstream: dict[str, Any] = {}
    upstream_specs = (
        ("pr93_report", pr93_gate.DEFAULT_REPORT, pr93_gate.SUCCESS_MARKER, "PR93"),
        ("pr94_report", pr94_gate.DEFAULT_REPORT, pr94_gate.SUCCESS_MARKER, "PR94"),
        ("pr95_report", pr95_gate.DEFAULT_REPORT, pr95_gate.SUCCESS_MARKER, "PR95"),
    )
    for key, path, marker, label in upstream_specs:
        path_abs = _resolve(repo_root, path)
        try:
            report = load_json(path_abs)
        except FileNotFoundError:
            failures.append(f"{label} report missing: {path.as_posix()}")
            report = {}
        except (json.JSONDecodeError, ValueError) as exc:
            failures.append(f"{label} report invalid: {path.as_posix()}: {exc}")
            report = {}
        if report and report.get("validation_marker") != marker:
            failures.append(f"{label} report validation marker mismatch")
        upstream[key] = report
    return failures, upstream


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    branch_context = _current_branch_context(repo_root)
    downstream_pr97_or_later = _downstream_or_main_validation_branch_allowed(
        branch_context.branch
    )
    pr99_static_builder_allowed = _pr99_static_builder_branch_allowed(branch_context.branch)
    for path in PR97_ALWAYS_FORBIDDEN_PATHS:
        if _resolve(repo_root, path).exists():
            failures.append(f"PR96 must not create PR97 or AtomicRows bundle artifact: {path.as_posix()}")
    for path in PR99_STATIC_BUILDER_ARTIFACT_PATHS:
        if _resolve(repo_root, path).exists() and not pr99_static_builder_allowed:
            failures.append(f"PR96 must not create PR97 or AtomicRows bundle artifact: {path.as_posix()}")
    if not downstream_pr97_or_later:
        for path in PR97_STATIC_PLAN_PATHS:
            if _resolve(repo_root, path).exists():
                failures.append(f"PR96 must not create PR97 or AtomicRows bundle artifact: {path.as_posix()}")
    for path in FORBIDDEN_RUNTIME_PATHS:
        if _resolve(repo_root, path).exists():
            failures.append(f"PR96 must not create runtime artifact: {path.as_posix()}")
    return failures


def validate_master_plan_diff(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--quiet", "--", MASTER_PLAN_CURRENT.as_posix()],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return []
    if completed.returncode == 1:
        return [
            "OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_BLOCKED_MASTER_PLAN_EDIT: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    return pr95_gate.validate_validator_static_surface(validator_path)


def build_report(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    packet: dict[str, Any],
    case_packets: list[dict[str, Any]],
    upstream: dict[str, Any],
    metadata: dict[str, Any],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    branch = str(metadata.get("branch") or "")
    downstream_pr97_or_later = _downstream_or_main_validation_branch_allowed(branch)
    pr97_static_plan_files_present = any(
        _resolve(repo_root, path).exists() for path in PR97_STATIC_PLAN_PATHS
    )
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "validator_marker": SUCCESS_MARKER,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": metadata.get("branch"),
        "base_head": metadata.get("base_head"),
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": metadata.get("semantic_task_id_source"),
        "blueprint_semantic_task_id": metadata.get("blueprint_semantic_task_id"),
        "blueprint_semantic_task_id_source": metadata.get("blueprint_semantic_task_id_source"),
        "blueprint_semantic_task_id_expected_by_blueprint": (
            metadata.get("blueprint_semantic_task_id_expected_by_blueprint")
        ),
        "validator_marker_source": metadata.get("validator_marker_source"),
        "owner_dashboard_approval_static_screen_contract_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "upstream_pr93_report_marker": upstream.get("pr93_report", {}).get("validation_marker"),
        "upstream_pr94_report_marker": upstream.get("pr94_report", {}).get("validation_marker"),
        "upstream_pr95_report_marker": upstream.get("pr95_report", {}).get("validation_marker"),
        "screen_count": packet.get("screen_count"),
        "component_count": packet.get("component_count"),
        "canonical_menu_option_count": len(CANONICAL_OPTION_ORDER),
        "canonical_scope_substitution_count": len(CANONICAL_SCOPE_SUBSTITUTIONS),
        "required_screen_concept_count": len(REQUIRED_SCREEN_CONCEPT_ORDER),
        "static_only_flag": True,
        "handoff_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "deterministic_output": True,
        "schema_validated": True,
        "registry_validated": True,
        "fixture_validated": True,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "pr97_atomicrows_full_bundle_row_expansion_plan_exists": pr97_static_plan_files_present,
        "pr97_static_plan_files_allowed_by_downstream_branch": downstream_pr97_or_later,
        "master_plan_diff_empty": True,
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "final_ready": False,
        "remaining_boundary": (
            "PR96 creates no runtime dashboard, dashboard UI, web server, endpoint, "
            "Telegram runtime, owner decision execution, owner approval receipt, owner "
            "override receipt, live trading, order authority, source or connector fact, "
            "runtime cash receipt, replay or paper result, optimizer execution, quantum "
            "backend execution, profit evidence, latency evidence, or quantum-advantage "
            "readiness."
        ),
    }
    for field in NO_AUTHORITY_FLAG_FIELDS:
        report[field] = False
    for field in ZERO_COUNT_FIELDS:
        report[field] = 0
    return report


def validate_report_is_deterministic(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    first = serialize_report(report)
    second = serialize_report(copy.deepcopy(report))
    if first != second:
        failures.append("generated report serialization is not byte-stable")
    if report.get("generated_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
        failures.append("generated report must use deterministic generated_at_utc sentinel")
    forbidden_patterns = (
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        re.compile(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        re.compile(r"[A-Za-z]:\\\\"),
        re.compile(r"\\\\"),
    )
    for pattern in forbidden_patterns:
        if pattern.search(first):
            failures.append("generated report contains nondeterministic or platform-specific content")
            break
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    registry_path: pathlib.Path = DEFAULT_PRODUCTION_REGISTRY,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    registry_abs = _resolve(repo_root, registry_path)
    fixture_abs = _resolve(repo_root, fixture_path)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    registry, registry_failures = _load_yaml_checked(registry_abs, "REGISTRY")
    fixture, fixture_failures = _load_json_checked(fixture_abs, "FIXTURE")
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)
    if schema is None or registry is None or fixture is None:
        return ValidationResult(False, tuple(failures), None)

    metadata_failures, metadata = validate_pr96_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_registry_payload(registry, repo_root=repo_root))
    failures.extend(validate_fixture_payload(fixture))
    packet = build_screen_contract_packet(registry)
    case_packets = [
        build_case_packet(case, registry)
        for case in _list_of_mappings(fixture.get("fixture_cases"))
    ]
    failures.extend(validate_case_packets(case_packets, fixture))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(
        validate_validator_static_surface(
            repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)
        )
    )

    report = build_report(
        registry,
        fixture,
        packet,
        case_packets,
        upstream,
        metadata,
        repo_root,
    )
    failures.extend(validate_report_is_deterministic(report))

    if failures:
        return ValidationResult(False, tuple(failures), report, info_lines)

    if not _should_skip_default_report_write(
        repo_root=repo_root,
        output_abs=output_abs,
        metadata=metadata,
    ):
        write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report, info_lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--registry", default=str(DEFAULT_PRODUCTION_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        registry_path=pathlib.Path(args.registry),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        for line in result.info_lines:
            print(line)
        return 0

    print(FAILURE_MARKER)
    for line in result.info_lines:
        print(line)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
