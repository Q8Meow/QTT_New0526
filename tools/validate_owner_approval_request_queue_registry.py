#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
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

from tools import ci_branch_context  # noqa: E402
from tools import validate_owner_live_promotion_review_for_parameter_stacks as pr92_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "governance"
    / "qtt_owner_approval_request_queue_registry.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "governance"
    / "QTTOwnerApprovalRequestQueueRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "governance"
    / "synthetic_qtt_owner_approval_request_queue_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerApprovalRequestQueueRegistry.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr92_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr92_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr92_gate.MASTER_PLAN_CURRENT

REGISTRY_ID = "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY"
PACKET_CONTRACT_ID = "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_V1"
REPORT_ID = "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #93"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-OWNER-APPROVAL-REQUEST-QUEUE-REGISTRY"
TARGET_BRANCH = "pr93-owner-approval-request-queue-registry"
EXPECTED_BASELINE_ANCESTOR = "f8b730c"
QUEUE_SCOPE = "STATIC_ONLY"
QUEUE_AUTHORITY_CLASS = (
    "STATIC_OWNER_APPROVAL_REQUEST_QUEUE_NOT_OWNER_DECISION_NOT_APPROVAL_RECEIPT_"
    "NOT_OVERRIDE_RECEIPT_NOT_LIVE_AUTHORITY"
)
REQUEST_AUTHORITY_CLASS = "AGENT_REQUEST_ONLY_OWNER_DECISION_REQUIRED"
REQUESTING_AGENT_AUTHORITY_CLASS = "AGENT_MAY_REQUEST_OWNER_DECIDES"
OWNER_DECISION_STATE = "PENDING_OWNER_DECISION"
OWNER_DECISION_OPTION_AUTHORITY_CLASS = "STATIC_OPTION_SCHEMA_ONLY_NOT_DECISION"
SUCCESS_MARKER = "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
FAILURE_MARKER = "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr92_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr92_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr92_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
REPAIR_BRANCH_PREFIX = ci_branch_context.REPAIR_BRANCH_PREFIX

DEPENDENCY_ORDER = pr92_gate.DEPENDENCY_ORDER + (
    "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS",
    "PR92_QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS",
)
DEPENDENCY_MARKERS = {
    **pr92_gate.DEPENDENCY_MARKERS,
    "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS": pr92_gate.pr91_gate.SUCCESS_MARKER,
    "PR92_QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS": pr92_gate.SUCCESS_MARKER,
}
REQUEST_TYPE_ORDER = (
    "LIVE_PROMOTION_OWNER_APPROVAL_REQUEST",
    "OWNER_OVERRIDE_REQUEST",
    "DASHBOARD_APPROVAL_REQUEST",
    "QUANTUM_BACKEND_ENABLEMENT_REQUEST",
    "REPLAY_PAPER_RETEST_REQUEST",
    "SOURCE_EVIDENCE_REVIEW_REQUEST",
    "CONNECTOR_SEMANTIC_REVIEW_REQUEST",
    "RUNTIME_CASH_REVIEW_REQUEST",
    "RISK_REVIEW_REQUEST",
    "ORDER_ROUTER_REVIEW_REQUEST",
    "CANARY_ELIGIBILITY_REQUEST",
)
REQUEST_STATUS_ORDER = (
    "PENDING_OWNER_DECISION",
    "BLOCKED_DUPLICATE_REQUEST",
    "BLOCKED_FAIL_CLOSED",
    "REJECTED_STATIC_DIAGNOSTIC_ONLY",
    "DEDUPE_SUPERSEDED_DIAGNOSTIC_ONLY",
)
REQUEST_PRIORITY_ORDER = (
    "P0_OWNER_REVIEW_FORWARDABLE",
    "P1_OWNER_OVERRIDE_FORWARDABLE",
    "P2_DASHBOARD_APPROVAL_FORWARDABLE",
    "P3_QUANTUM_BACKEND_ENABLEMENT_REQUEST",
    "P4_REPLAY_PAPER_RETEST_REQUEST",
    "P5_DEPENDENCY_REVIEW_REQUEST",
)
OWNER_DECISION_OPTION_ORDER = (
    "PENDING_OWNER_DECISION",
    "APPROVE_REQUESTED",
    "APPROVE_WITH_CONDITIONS_REQUESTED",
    "REJECT_REQUESTED",
    "REQUEST_MORE_INFO_REQUESTED",
    "RETEST_REQUIRED",
    "REPAIR_REQUIRED",
    "SOURCE_EVIDENCE_REVIEW_REQUIRED",
    "CONNECTOR_REVIEW_REQUIRED",
    "RUNTIME_CASH_REVIEW_REQUIRED",
    "RISK_REVIEW_REQUIRED",
    "ORDER_ROUTER_REVIEW_REQUIRED",
    "DASHBOARD_APPROVAL_REQUIRED",
    "OWNER_OVERRIDE_REQUESTED",
    "BLOCKED_PENDING_OWNER_DECISION",
)
QUEUE_INPUT_ORDER = (
    "PR92_static_owner_live_promotion_review_parameter_stack_packet",
    "PR91_static_dual_result_review_parameter_stack_packet",
    "PR90_static_replay_paper_candidate_stack_competition_packet_lineage",
    "PR89_static_selected_parameter_stack_handoff_packet_lineage",
    "PR88_static_trade_context_parameter_stack_selection_packet_lineage",
    "PR87_static_candidate_generation_packet_lineage",
    "existing_owner_approval_request_foundation_schema",
    "existing_owner_approval_receipt_boundary_schema",
    "existing_owner_override_receipt_boundary_schema",
    "source_evidence_connector_runtime_cash_risk_order_router_dashboard_static_boundaries",
    "PR94_PR95_PR96_forwardability_metadata_only",
)
QUEUE_OUTPUT_ORDER = (
    "static_owner_approval_request_queue_registry_packet",
    "static_owner_approval_queue_entry_descriptors",
    "static_request_type_taxonomy",
    "static_request_status_taxonomy",
    "static_request_priority_taxonomy",
    "static_dependency_gate_matrix",
    "static_deterministic_queue_ordering_contract",
    "static_request_deduplication_contract",
    "static_fail_closed_queue_case_packets",
    "pr94_pr95_pr96_forwardability_metadata_no_future_artifacts_created",
    "no_owner_decision_boundary",
    "no_owner_approval_receipt_boundary",
    "no_owner_override_receipt_boundary",
    "no_live_promotion_boundary",
    "no_canary_eligibility_boundary",
    "no_order_authority_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "no_profit_evidence_boundary",
)
ORDERING_KEY_FIELDS = (
    "valid_request_entries_before_blocked_diagnostics",
    "request_priority_class",
    "request_type",
    "dependency_blocker_severity",
    "owner_policy_priority_class",
    "quantum_priority_related_metadata",
    "requested_platform_scope",
    "requested_venue_scope",
    "requested_strategy_scope",
    "selected_stack_id_or_target_entity_id",
    "requesting_agent_id",
    "queue_entry_id",
)
REASON_CODE_ORDER = (
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_STATIC_REQUEST_ONLY",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR92_OWNER_REVIEW_PACKET",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR91_DUAL_RESULT_REVIEW_PACKET",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR90_COMPETITION_PACKET_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR89_HANDOFF_PACKET_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR88_SELECTION_PACKET_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR87_CANDIDATE_PACKET_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_AGENTS_REQUEST_OWNER_DECIDES",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_OWNER_DECISION_PENDING",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_DECISION_OPTIONS_SCHEMA_ONLY",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_SOURCE_CONNECTOR_RUNTIME_CASH_RISK_ORDER_GATES_PRESERVED",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_QUANTUM_METADATA_WITH_CLASSICAL_COMPARATOR",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_OWNER_OVERRIDE_REQUEST_INTERNAL_ONLY",
    "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR94_PR95_PR96_FORWARDABILITY_ONLY",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_NO_FORWARDABLE_OWNER_REVIEW_FOR_APPROVAL_QUEUE",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_PR92_OWNER_REVIEW_PACKET",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_NON_FORWARDABLE_PR92_OWNER_REVIEW",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_REQUEST_BASIS",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_SELECTED_STACK_ID",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_UNTRACEABLE_SELECTED_STACK",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_BLOCKED_CANDIDATE_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_INCOMPATIBLE_CANDIDATE_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_ROLE_CANDIDATE_LINEAGE",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DUPLICATE_REQUEST_COLLISION",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AUTO_APPROVAL_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_RUNTIME_CASH_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_REPLAY_OR_PAPER_EXECUTION_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_REAL_REPLAY_OR_PAPER_RESULT_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PR94_RECEIPT_AUTHORING_GATE_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PR95_DASHBOARD_MENU_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PR96_DASHBOARD_SCREEN_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR93_METADATA_VERIFIED",
    "PASS_VALID_OWNER_APPROVAL_REQUEST_FROM_PR92",
    "PASS_MULTIPLE_AGENT_REQUESTS_DETERMINISTIC_ORDERING",
    "PASS_AGENT_REQUEST_NO_SELF_APPROVAL",
    "PASS_OWNER_DECISION_PENDING",
    "PASS_OWNER_DECISION_OPTIONS_REFERENCED_NOT_EXECUTED",
    "BLOCK_DUPLICATE_REQUEST_COLLISION",
    "BLOCK_MISSING_REQUEST_BASIS",
    "BLOCK_MISSING_PR92_OWNER_REVIEW_PACKET",
    "BLOCK_NON_FORWARDABLE_PR92_OWNER_REVIEW",
    "BLOCK_MISSING_SELECTED_STACK_ID",
    "BLOCK_UNTRACEABLE_SELECTED_STACK",
    "BLOCK_BLOCKED_CANDIDATE_LINEAGE",
    "BLOCK_INCOMPATIBLE_CANDIDATE_LINEAGE",
    "BLOCK_MISSING_ROLE_CANDIDATE_LINEAGE",
    "BLOCK_SOURCE_EVIDENCE_DEPENDENCY_BYPASS",
    "BLOCK_CONNECTOR_SEMANTIC_DEPENDENCY_BYPASS",
    "BLOCK_RUNTIME_CASH_DEPENDENCY_BYPASS",
    "BLOCK_REPLAY_PAPER_DEPENDENCY_BYPASS",
    "BLOCK_RISK_DEPENDENCY_BYPASS",
    "BLOCK_ORDER_ROUTER_DEPENDENCY_BYPASS",
    "BLOCK_DASHBOARD_DEPENDENCY_BYPASS",
    "PASS_QUANTUM_BACKEND_ENABLEMENT_REQUEST_METADATA_ONLY",
    "PASS_OWNER_OVERRIDE_REQUEST_FORWARDABLE_NO_RECEIPT",
    "PASS_DASHBOARD_APPROVAL_REQUEST_FORWARDABLE_NO_DASHBOARD_ARTIFACT",
    "BLOCK_OWNER_APPROVAL_RECEIPT_FABRICATION",
    "BLOCK_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    "BLOCK_AGENT_SELF_APPROVAL_ATTEMPT",
    "BLOCK_AUTO_APPROVAL_ATTEMPT",
    "BLOCK_LIVE_PROMOTION_ATTEMPT",
    "BLOCK_CANARY_ELIGIBILITY_CREATION_ATTEMPT",
    "BLOCK_EXECUTABLE_ORDER_INTENT_ATTEMPT",
    "BLOCK_ORDER_AUTHORITY_ATTEMPT",
    "BLOCK_LIVE_ROUTING_ATTEMPT",
    "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_ATTEMPT",
    "BLOCK_CONNECTOR_BINDING_ATTEMPT",
    "BLOCK_RUNTIME_CASH_CREATION_ATTEMPT",
    "BLOCK_DASHBOARD_RUNTIME_CREATION_ATTEMPT",
    "BLOCK_PR94_RECEIPT_AUTHORING_GATE_CREATION_ATTEMPT",
    "BLOCK_PR95_DASHBOARD_MENU_CREATION_ATTEMPT",
    "BLOCK_PR96_DASHBOARD_SCREEN_CREATION_ATTEMPT",
    "BLOCK_ATOMICROWS_BUNDLE_ATTEMPT",
    "BLOCK_ATOMICROWS_SHA_ATTEMPT",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "PASS_PR94_PR95_PR96_FORWARDABILITY_ONLY",
    "BLOCK_REAL_REPLAY_OR_PAPER_RESULT_ATTEMPT",
    "BLOCK_CLASSICAL_OR_QUANTUM_OPTIMIZER_EXECUTION_ATTEMPT",
    "BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_EXECUTION_ATTEMPT",
)
REQUIRED_MASTER_PLAN_PRINCIPLES = {
    "AGENTS_MAY_REQUEST_OWNER_DECIDES",
    "AGENTS_MAY_NOT_APPROVE_FOR_OWNER",
    "OWNER_APPROVAL_NON_DELEGABLE",
    "OWNER_GLOBAL_AUTHORITY_INTERNAL_ONLY",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_FACTS",
    "OWNER_APPROVAL_REQUEST_QUEUE_STATIC_INTAKE_NOT_DECISION",
    "OWNER_APPROVAL_REQUEST_QUEUE_NOT_RECEIPT",
    "OWNER_APPROVAL_REQUEST_QUEUE_NOT_OVERRIDE_RECEIPT",
    "NO_AUTOMATIC_APPROVAL",
    "NO_AUTOMATIC_LIVE_PROMOTION",
    "NO_LIVE_ORDER_AUTHORITY",
    "SOURCE_EVIDENCE_REQUIRED_NO_BYPASS",
    "ACCEPTED_SOURCE_PACKETS_REQUIRED_FOR_SOURCE_DEPENDENT_LIVE_CONNECTOR_FIELDS",
    "CONNECTOR_SEMANTIC_BINDING_REQUIRED",
    "RUNTIME_CASH_RECEIPT_REQUIRED",
    "RISK_AND_ORDER_ROUTER_GATES_REQUIRED",
    "EXECUTION_ROUTER_FINAL_ORDER_SUBMISSION_AUTHORITY",
    "DASHBOARD_APPROVAL_SURFACES_LATER_GATES",
    "CANARY_ELIGIBILITY_LATER_GATE",
    "LIVE_REACHABILITY_AND_ORDER_EXECUTION_LATER",
    "REPLAY_AND_PAPER_RESULTS_REMAIN_SEPARATE",
    "DUAL_RESULT_AND_OWNER_REVIEW_UPSTREAM_OF_QUEUE",
    "ATOMICROWS_INVENTORY_NOT_TRADER",
    "NO_SINGLE_PARAMETER_OR_ALGORITHM_STACKS",
    "MINIMUM_REQUIRED_STACK_ROLES",
    "BLOCKED_ROWS_EXCLUDED_FROM_ACTIVE_QUEUE_APPROVAL_STATE",
    "QUANTUM_RANK_REFINE_ONLY_NO_DIRECT_LIVE_AUTHORITY",
    "CLASSICAL_EXECUTION_GATES_REMAIN_FINAL",
    "SOURCE_CONNECTOR_CASH_ORDER_FACTS_REQUIRE_RECEIPTS",
    "NO_FABRICATION_BOUNDARY",
}
NO_AUTHORITY_FALSE_FIELDS = (
    "source_retrieval_created_flag",
    "source_acceptance_created_flag",
    "accepted_source_packet_created_flag",
    "connector_semantic_binding_created_flag",
    "runtime_cash_receipt_created_flag",
    "private_state_fetch_created_flag",
    "replay_execution_created_flag",
    "paper_execution_created_flag",
    "real_replay_result_packet_created_flag",
    "real_paper_result_packet_created_flag",
    "owner_decision_created_flag",
    "owner_approval_receipt_created_flag",
    "owner_override_receipt_created_flag",
    "live_promotion_created_flag",
    "canary_eligibility_created_flag",
    "dashboard_runtime_service_created_flag",
    "pr94_owner_override_receipt_created_flag",
    "pr94_owner_override_receipt_authoring_gate_created_flag",
    "pr95_dashboard_approval_menu_created_flag",
    "pr96_dashboard_approval_static_screen_created_flag",
    "executable_order_intent_created_flag",
    "order_intent_authority_created_flag",
    "order_authority_created_flag",
    "order_submission_allowed_flag",
    "live_routing_allowed_flag",
    "connector_binding_allowed_flag",
    "optimizer_execution_created_flag",
    "classical_optimizer_execution_created_flag",
    "quantum_optimizer_execution_created_flag",
    "quantum_backend_execution_created_flag",
    "quantum_simulator_execution_created_flag",
    "profit_evidence_created_flag",
    "quantum_advantage_claim_created_flag",
    "latency_superiority_claim_created_flag",
    "execution_superiority_claim_created_flag",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "blocker_reduction_claim_created_flag",
)
NO_AUTHORITY_TRUE_FIELDS = (
    "no_agent_self_approval_flag",
    "no_owner_approval_flag",
    "no_override_receipt_flag",
    "no_order_authority_flag",
    "no_runtime_execution_flag",
    "no_replay_execution_flag",
    "no_paper_execution_flag",
    "no_live_trade_authority_flag",
    "no_quantum_backend_execution_flag",
    "no_profit_evidence_flag",
)
ZERO_COUNT_FIELDS = (
    "owner_decision_created_count",
    "owner_approval_receipt_created_count",
    "owner_override_receipt_created_count",
    "live_promotion_created_count",
    "canary_eligibility_created_count",
    "source_retrieval_count",
    "source_acceptance_count",
    "connector_binding_count",
    "runtime_cash_receipt_count",
    "replay_execution_count",
    "paper_execution_count",
    "order_submission_count",
    "order_authoritative_item_count",
    "quantum_backend_execution_count",
    "quantum_simulator_execution_count",
    "profit_evidence_created_count",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return pr92_gate.load_yaml(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(
    path: pathlib.Path,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except json.JSONDecodeError as exc:
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(
    path: pathlib.Path,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:  # pragma: no cover - defensive parse surface
        return None, [f"{label} invalid YAML: {path.as_posix()}: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _first_by_key(items: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        value = item.get(key)
        if isinstance(value, str):
            result[value] = item
    return result


def _sort_by_order(values: Iterable[str], order: Sequence[str]) -> list[str]:
    order_index = {value: index for index, value in enumerate(order)}
    return sorted(dict.fromkeys(values), key=lambda item: (order_index.get(item, 999), item))


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order(codes, REASON_CODE_ORDER)


def _digest(parts: Iterable[Any]) -> str:
    payload = json.dumps(list(parts), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
    return ci_branch_context.github_actions_active()


def _downstream_validation_branch_allowed(branch: str) -> bool:
    return ci_branch_context.is_downstream_or_main_validation_branch(branch, after_pr=93)


def validate_pr93_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 93), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 93), None)
    if roadmap_entry is None:
        failures.append("PR93 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR93 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Owner approval request queue registry"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Owner approval request queue registry"),
        ("blueprint.branch", blueprint_entry.get("branch"), TARGET_BRANCH),
        ("blueprint.semantic_task_id", blueprint_entry.get("semantic_task_id"), SEMANTIC_TASK_ID),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "Owner approval foundation"),
        ("blueprint.priority", blueprint_entry.get("priority"), "S1 launch-essential static"),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(f"{label} must be {expected}, got {actual}")

    branch_rc, branch, branch_err = _git_stdout(repo_root, ["branch", "--show-current"])
    if branch_rc != 0:
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        else:
            failures.append(f"git branch check failed: {branch_err}")
    elif branch != TARGET_BRANCH:
        if github_actions:
            info_lines.append(CI_DETACHED_HEAD_MODE_MARKER)
        elif _downstream_validation_branch_allowed(branch):
            info_lines.append(DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER)
        else:
            failures.append(f"current branch must be {TARGET_BRANCH}, got {branch}")

    head_rc, head, head_err = _git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    if head_rc != 0:
        failures.append(f"git HEAD check failed: {head_err}")
    baseline_rc, _, _baseline_err = _git_stdout(
        repo_root, ["cat-file", "-e", f"{EXPECTED_BASELINE_ANCESTOR}^{{commit}}"]
    )
    if github_actions and baseline_rc != 0:
        info_lines.append(CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER)
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
        "base_head": head,
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": BLUEPRINT_INDEX.as_posix(),
        "validator_marker": SUCCESS_MARKER,
        "validator_marker_source": (
            f"{ROADMAP_INDEX.as_posix()} and {BLUEPRINT_INDEX.as_posix()}"
        ),
        "ci_info_lines": tuple(info_lines),
        "roadmap_index_entry_verified": not failures,
        "blueprint_index_entry_verified": not failures,
    }


def _should_skip_default_report_write(
    *,
    repo_root: pathlib.Path,
    output_abs: pathlib.Path,
    metadata: dict[str, Any],
) -> bool:
    if output_abs != _resolve(repo_root, DEFAULT_REPORT):
        return False
    branch = str(metadata.get("branch") or "")
    return branch not in {TARGET_BRANCH, "main"} and _downstream_validation_branch_allowed(branch)


def _validate_report_marker(
    report: dict[str, Any] | None,
    expected_marker: str,
    label: str,
) -> list[str]:
    if report is None:
        return [f"{label} report missing"]
    marker = report.get("validation_marker") or report.get("validator_marker")
    if marker != expected_marker:
        return [f"{label} report marker must be {expected_marker}, got {marker}"]
    return []


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr92_result = pr92_gate.validate(repo_root=repo_root)
    failures.extend(pr92_result.failures)
    pr92_report = pr92_result.report
    failures.extend(_validate_report_marker(pr92_report, pr92_gate.SUCCESS_MARKER, "PR92"))
    if pr92_report is None:
        pr92_report = {}

    return failures, {
        "pr92_report": pr92_report,
        "owner_live_promotion_review_parameter_stack_packet": pr92_report.get(
            "owner_live_promotion_review_parameter_stack_packet", {}
        ),
        "pr92_fixture_case_packets": pr92_report.get("fixture_case_packets", []),
        "stage1_reports": pr92_report.get("stage1_reports", {}),
    }


def _existing_path_or_schema_ref(repo_root: pathlib.Path, ref: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in ("schema_path", "registry_path"):
        value = ref.get(field)
        if isinstance(value, str) and value and not _resolve(repo_root, pathlib.Path(value)).exists():
            failures.append(f"referenced {field} missing: {value}")
    return failures


def validate_dependencies(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    dependencies = _first_by_key(_list_of_mappings(payload.get("upstream_dependencies")), "artifact_id")
    missing = [artifact_id for artifact_id in DEPENDENCY_ORDER if artifact_id not in dependencies]
    if missing:
        failures.append(f"missing upstream dependency refs: {', '.join(missing)}")
    for artifact_id, expected_marker in DEPENDENCY_MARKERS.items():
        dependency = dependencies.get(artifact_id)
        if not dependency:
            continue
        if dependency.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id} marker must be {expected_marker}")
        for field in ("registry_path", "report_path", "validator_path"):
            value = dependency.get(field)
            if isinstance(value, str) and value and not _resolve(repo_root, pathlib.Path(value)).exists():
                failures.append(f"{artifact_id} {field} missing: {value}")
    return failures


def validate_boundary_refs(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for field in (
        "upstream_owner_live_promotion_review_packet_ref",
        "owner_approval_receipt_boundary_ref",
        "owner_override_receipt_boundary_ref",
    ):
        ref = payload.get(field)
        if not isinstance(ref, dict):
            failures.append(f"{field} must be a mapping")
            continue
        failures.extend(_existing_path_or_schema_ref(repo_root, ref))
    for ref in _list_of_mappings(payload.get("source_connector_runtime_order_boundary_refs")):
        failures.extend(_existing_path_or_schema_ref(repo_root, ref))
    return failures


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumers = _first_by_key(_list_of_mappings(payload.get("future_consumers")), "consumer_id")
    for consumer_id in (
        "PR94_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE",
        "PR95_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA",
        "PR96_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT",
    ):
        consumer = consumers.get(consumer_id)
        if not consumer:
            failures.append(f"future consumer missing: {consumer_id}")
        elif consumer.get("pr93_creates_consumer_execution") is not False:
            failures.append(f"{consumer_id} must not be created by PR93")
    return failures


def validate_no_authority_flags(payload: dict[str, Any], *, prefix: str) -> list[str]:
    flags = payload.get("required_no_authority_flags")
    if not isinstance(flags, dict):
        return [f"{prefix}.required_no_authority_flags must be a mapping"]
    failures: list[str] = []
    for field, value in flags.items():
        if value is not False:
            failures.append(f"{prefix}.required_no_authority_flags.{field} must be false")
    return failures


def validate_registry_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if payload.get("owner_approval_request_queue_registry_id") != REGISTRY_ID:
        failures.append("registry id mismatch")
    if payload.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append("semantic task id mismatch")
    if payload.get("queue_authority_class") != QUEUE_AUTHORITY_CLASS:
        failures.append("queue authority class mismatch")
    if payload.get("owner_decision_created_flag") is not False:
        failures.append("registry must not create owner decision")
    if payload.get("owner_approval_receipt_created_flag") is not False:
        failures.append("registry must not create owner approval receipt")
    if payload.get("owner_override_receipt_created_flag") is not False:
        failures.append("registry must not create owner override receipt")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_boundary_refs(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_no_authority_flags(payload, prefix="registry"))
    principles = {
        item.get("principle_id")
        for item in _list_of_mappings(payload.get("master_plan_principles_consumed"))
    }
    missing_principles = sorted(REQUIRED_MASTER_PLAN_PRINCIPLES - principles)
    if missing_principles:
        failures.append(f"missing master-plan principle refs: {', '.join(missing_principles)}")
    return failures


def _case_by_id(fixture: dict[str, Any], case_id: str | None) -> dict[str, Any]:
    if case_id is None:
        return {}
    cases = _first_by_key(_list_of_mappings(fixture.get("fixture_cases")), "case_id")
    return cases.get(case_id, {})


def _pr92_owner_review_item(packet: dict[str, Any]) -> dict[str, Any]:
    items = _list_of_mappings(packet.get("owner_review_items"))
    return items[0] if items else {}


def _selected_stack_lineage_trace(
    pr92_packet: dict[str, Any],
    pr92_item: dict[str, Any],
    case: dict[str, Any],
) -> list[dict[str, Any]]:
    if case.get("untraceable_selected_stack") is True:
        return []
    item_lineage = _list_of_mappings(pr92_item.get("selected_stack_lineage_trace"))
    if item_lineage:
        return copy.deepcopy(item_lineage)
    return copy.deepcopy(_list_of_mappings(pr92_packet.get("selected_stack_lineage_trace")))


def _lineage_artifact_ids(lineage: list[dict[str, Any]]) -> set[str]:
    return {str(step.get("artifact_id") or "") for step in lineage}


def _has_required_lineage(lineage: list[dict[str, Any]]) -> bool:
    artifact_ids = _lineage_artifact_ids(lineage)
    return {
        "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS",
        "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
        "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
        "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
        "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
    }.issubset(artifact_ids)


def _case_source_requests(fixture: dict[str, Any], case: dict[str, Any]) -> list[dict[str, Any]]:
    requests = _list_of_mappings(fixture.get("queue_source_requests"))
    if not requests:
        return []
    if case.get("use_all_fixture_requests") is True:
        return copy.deepcopy(requests)
    request = copy.deepcopy(requests[0])
    request_type_override = case.get("request_type_override")
    if isinstance(request_type_override, str):
        request["request_type"] = request_type_override
        request["request_id"] = f"PR93_REQUEST__{request_type_override}__STATIC_CASE"
        request["dedupe_identity"] = (
            f"{request_type_override}|{fixture.get('expected_selected_stack_id')}|"
            f"CASE|{request.get('requesting_agent_id')}"
        )
        if request_type_override == "OWNER_OVERRIDE_REQUEST":
            request["request_priority_class"] = "P1_OWNER_OVERRIDE_FORWARDABLE"
            request["pr94_owner_override_receipt_authoring_required_flag"] = True
            request["pr95_dashboard_approval_menu_required_flag"] = False
            request["pr96_dashboard_approval_static_screen_required_flag"] = False
        elif request_type_override == "DASHBOARD_APPROVAL_REQUEST":
            request["request_priority_class"] = "P2_DASHBOARD_APPROVAL_FORWARDABLE"
            request["pr94_owner_override_receipt_authoring_required_flag"] = False
            request["pr95_dashboard_approval_menu_required_flag"] = True
            request["pr96_dashboard_approval_static_screen_required_flag"] = True
    if case.get("quantum_backend_enablement_requested_flag") is True:
        request["quantum_backend_enablement_requested_flag"] = True
        request["request_priority_class"] = "P3_QUANTUM_BACKEND_ENABLEMENT_REQUEST"
    if case.get("duplicate_request_collision") is True:
        duplicate = copy.deepcopy(request)
        duplicate["queue_entry_id"] = "PR93_QUEUE_ENTRY__CASE__DUPLICATE_REQUEST_BLOCKED"
        duplicate["request_id"] = "PR93_REQUEST__CASE_DUPLICATE_REQUEST_BLOCKED"
        return [request, duplicate]
    return [request]


def _block_codes_for_case(
    pr92_packet: dict[str, Any],
    pr92_item: dict[str, Any],
    fixture: dict[str, Any],
    case: dict[str, Any],
    lineage: list[dict[str, Any]],
) -> list[str]:
    codes: list[str] = []
    if not pr92_packet or case.get("missing_pr92_owner_review_packet") is True:
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_PR92_OWNER_REVIEW_PACKET")
    forwardable = pr92_packet.get("owner_approval_queue_forwardable_flag")
    if forwardable is not True or case.get("non_forwardable_pr92_owner_review") is True:
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_NON_FORWARDABLE_PR92_OWNER_REVIEW")
    if case.get("missing_request_basis") is True:
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_REQUEST_BASIS")
    selected_stack_id = fixture.get("expected_selected_stack_id")
    if case.get("missing_selected_stack_id") is True:
        selected_stack_id = None
    if not selected_stack_id:
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_SELECTED_STACK_ID")
    if not _has_required_lineage(lineage):
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_UNTRACEABLE_SELECTED_STACK")
    mapping = (
        ("blocked_candidate_lineage", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_BLOCKED_CANDIDATE_LINEAGE"),
        ("incompatible_candidate_lineage", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_INCOMPATIBLE_CANDIDATE_LINEAGE"),
        ("missing_role_candidate_lineage", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_ROLE_CANDIDATE_LINEAGE"),
        ("source_evidence_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN"),
        ("connector_semantic_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("runtime_cash_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_RUNTIME_CASH_FORBIDDEN"),
        ("replay_paper_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_REPLAY_OR_PAPER_EXECUTION_FORBIDDEN"),
        ("risk_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ORDER_AUTHORITY_FORBIDDEN"),
        ("order_router_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ORDER_AUTHORITY_FORBIDDEN"),
        ("dashboard_dependency_bypass_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN"),
        ("owner_approval_receipt_fabrication_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION"),
        ("owner_override_receipt_fabrication_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION"),
        ("agent_self_approval_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN"),
        ("auto_approval_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AUTO_APPROVAL_FORBIDDEN"),
        ("live_promotion_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_LIVE_PROMOTION_FORBIDDEN"),
        ("canary_eligibility_creation_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN"),
        ("executable_order_intent_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN"),
        ("order_authority_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ORDER_AUTHORITY_FORBIDDEN"),
        ("live_routing_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_LIVE_ROUTING_FORBIDDEN"),
        ("source_retrieval_acceptance_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN"),
        ("connector_binding_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("runtime_cash_creation_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_RUNTIME_CASH_FORBIDDEN"),
        ("dashboard_runtime_creation_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN"),
        ("pr94_receipt_authoring_gate_creation_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PR94_RECEIPT_AUTHORING_GATE_FORBIDDEN"),
        ("pr95_dashboard_menu_creation_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PR95_DASHBOARD_MENU_FORBIDDEN"),
        ("pr96_dashboard_screen_creation_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PR96_DASHBOARD_SCREEN_FORBIDDEN"),
        ("atomicrows_bundle_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN"),
        ("atomicrows_sha_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ATOMICROWS_SHA_FORBIDDEN"),
        ("profit_evidence_claim", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("quantum_advantage_claim", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"),
        ("real_replay_or_paper_result_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_REAL_REPLAY_OR_PAPER_RESULT_FORBIDDEN"),
        ("optimizer_execution_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("quantum_backend_or_simulator_execution_attempt", "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN"),
    )
    for case_field, reason_code in mapping:
        if case.get(case_field) is True:
            codes.append(reason_code)
    if pr92_item == {} and pr92_packet:
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_NO_FORWARDABLE_OWNER_REVIEW_FOR_APPROVAL_QUEUE")
    return _sort_reason_codes(dict.fromkeys(codes))


def _gate_dependency_matrix(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "SOURCE_EVIDENCE_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": fixture.get("source_evidence_gate_state"),
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "SOURCE_EVIDENCE_REVIEW_REQUIRED",
        },
        {
            "gate_id": "ACCEPTED_SOURCE_PACKET_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "REQUIRED_MISSING_BLOCKS_APPROVAL_AND_LIVE_PROMOTION",
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "SOURCE_EVIDENCE_REVIEW_REQUIRED",
        },
        {
            "gate_id": "CONNECTOR_SEMANTIC_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": fixture.get("connector_semantic_gate_state"),
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "CONNECTOR_REVIEW_REQUIRED",
        },
        {
            "gate_id": "RUNTIME_CASH_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": fixture.get("runtime_cash_gate_state"),
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "RUNTIME_CASH_REVIEW_REQUIRED",
        },
        {
            "gate_id": "REPLAY_PAPER_GATE",
            "required_flag": True,
            "satisfied_flag": True,
            "created_flag": False,
            "gate_state": fixture.get("replay_paper_gate_state"),
            "blocks_owner_approval_flag": False,
            "blocks_live_promotion_flag": False,
            "blocker_code": "REPLAY_PAPER_STATIC_REVIEW_PRESENT_NO_EXECUTION",
        },
        {
            "gate_id": "DUAL_RESULT_REVIEW_GATE",
            "required_flag": True,
            "satisfied_flag": True,
            "created_flag": False,
            "gate_state": fixture.get("dual_result_review_state"),
            "blocks_owner_approval_flag": False,
            "blocks_live_promotion_flag": False,
            "blocker_code": "DUAL_RESULT_REVIEW_STATIC_PRESENT",
        },
        {
            "gate_id": "RISK_REVIEW_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": fixture.get("risk_gate_state"),
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "RISK_REVIEW_REQUIRED",
        },
        {
            "gate_id": "ORDER_ROUTER_FINAL_AUTHORITY_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": fixture.get("order_router_gate_state"),
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "ORDER_ROUTER_REVIEW_REQUIRED",
        },
        {
            "gate_id": "OWNER_DECISION_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": OWNER_DECISION_STATE,
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "OWNER_DECISION_REQUIRED",
        },
        {
            "gate_id": "DASHBOARD_APPROVAL_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": fixture.get("dashboard_gate_state"),
            "blocks_owner_approval_flag": True,
            "blocks_live_promotion_flag": True,
            "blocker_code": "DASHBOARD_APPROVAL_REQUIRED",
        },
    ]


def _allowed_reason_codes_for_request(request_type: str) -> list[str]:
    codes = [
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_STATIC_REQUEST_ONLY",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR92_OWNER_REVIEW_PACKET",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR91_DUAL_RESULT_REVIEW_PACKET",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR90_COMPETITION_PACKET_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR89_HANDOFF_PACKET_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR88_SELECTION_PACKET_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR87_CANDIDATE_PACKET_LINEAGE",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_AGENTS_REQUEST_OWNER_DECIDES",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_OWNER_DECISION_PENDING",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_DECISION_OPTIONS_SCHEMA_ONLY",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_SOURCE_CONNECTOR_RUNTIME_CASH_RISK_ORDER_GATES_PRESERVED",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_QUANTUM_METADATA_WITH_CLASSICAL_COMPARATOR",
        "OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_PR94_PR95_PR96_FORWARDABILITY_ONLY",
    ]
    if request_type == "OWNER_OVERRIDE_REQUEST":
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_OWNER_OVERRIDE_REQUEST_INTERNAL_ONLY")
    if request_type == "QUANTUM_BACKEND_ENABLEMENT_REQUEST":
        codes.append("OWNER_APPROVAL_REQUEST_QUEUE_ALLOWED_QUANTUM_METADATA_WITH_CLASSICAL_COMPARATOR")
    return _sort_reason_codes(codes)


def _entry_order_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    status = str(entry.get("request_status") or "")
    priority = str(entry.get("request_priority_class") or "")
    request_type = str(entry.get("request_type") or "")
    return (
        REQUEST_STATUS_ORDER.index(status) if status in REQUEST_STATUS_ORDER else 999,
        REQUEST_PRIORITY_ORDER.index(priority) if priority in REQUEST_PRIORITY_ORDER else 999,
        REQUEST_TYPE_ORDER.index(request_type) if request_type in REQUEST_TYPE_ORDER else 999,
        str(entry.get("dependency_blocker_severity") or ""),
        str(entry.get("owner_policy_priority_class") or ""),
        0 if entry.get("quantum_priority_related_flag") else 1,
        "|".join(str(item) for item in entry.get("requested_platform_scope", [])),
        "|".join(str(item) for item in entry.get("requested_venue_scope", [])),
        str(entry.get("requested_strategy_scope") or ""),
        str(entry.get("selected_stack_id") or entry.get("requested_target_entity_id") or ""),
        str(entry.get("requesting_agent_id") or ""),
        str(entry.get("queue_entry_id") or ""),
    )


def _queue_entry(
    source_request: dict[str, Any],
    fixture: dict[str, Any],
    pr92_packet: dict[str, Any],
    pr92_item: dict[str, Any],
    lineage: list[dict[str, Any]],
    block_codes: Sequence[str],
    *,
    duplicate_of_request_id: str | None = None,
) -> dict[str, Any]:
    request_type = str(source_request.get("request_type"))
    selected_stack_id = fixture.get("expected_selected_stack_id")
    if "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_SELECTED_STACK_ID" in block_codes:
        selected_stack_id = None
    valid = not block_codes and duplicate_of_request_id is None
    request_status = (
        "PENDING_OWNER_DECISION"
        if valid
        else "BLOCKED_DUPLICATE_REQUEST"
        if duplicate_of_request_id is not None
        else "BLOCKED_FAIL_CLOSED"
    )
    reason_codes = _allowed_reason_codes_for_request(request_type) if valid else list(block_codes)
    quantum_summary = pr92_item.get("quantum_applicability_summary") if isinstance(pr92_item, dict) else {}
    owner_quantum_summary = (
        pr92_item.get("owner_quantum_priority_summary") if isinstance(pr92_item, dict) else {}
    )
    entry = {
        "queue_entry_id": source_request.get("queue_entry_id"),
        "request_id": source_request.get("request_id"),
        "request_deduplication_identity": source_request.get("dedupe_identity"),
        "duplicate_of_request_id": duplicate_of_request_id,
        "request_type": request_type,
        "request_status": request_status,
        "request_priority_class": source_request.get("request_priority_class"),
        "request_authority_class": REQUEST_AUTHORITY_CLASS,
        "requesting_agent_id": source_request.get("requesting_agent_id"),
        "requesting_agent_role": source_request.get("requesting_agent_role"),
        "requesting_agent_authority_class": REQUESTING_AGENT_AUTHORITY_CLASS,
        "owner_decision_state": OWNER_DECISION_STATE if valid else "BLOCKED_PENDING_OWNER_DECISION",
        "owner_decision_allowed_values_ref": "schemas/governance/qtt_owner_approval_request.schema.json#/$defs/owner_decision_option",
        "owner_decision_option_schema_ref": "schemas/governance/qtt_owner_approval_request.schema.json#/$defs/owner_decision_option",
        "owner_decision_option_authority_class": OWNER_DECISION_OPTION_AUTHORITY_CLASS,
        "owner_decision_created_flag": False,
        "owner_approval_receipt_ref": "src/qtt/stage1_prediction_markets/owner_live_promotion_review/stage1_owner_approval_receipt_boundary.schema.json#static-boundary-ref-only",
        "owner_approval_receipt_created_flag": False,
        "owner_override_receipt_ref": "schemas/governance/qtt_owner_override_receipt.schema.json#future-pr94-boundary-ref-only",
        "owner_override_receipt_created_flag": False,
        "upstream_owner_live_promotion_review_packet_ref": fixture.get(
            "upstream_owner_live_promotion_review_packet_ref"
        )
        if pr92_packet
        else None,
        "upstream_owner_live_promotion_review_item_ref": fixture.get(
            "upstream_owner_live_promotion_review_item_ref"
        )
        if pr92_item
        else None,
        "upstream_dual_result_review_packet_ref": fixture.get("upstream_dual_result_review_packet_ref"),
        "upstream_replay_paper_competition_packet_ref": fixture.get(
            "upstream_replay_paper_competition_packet_ref"
        ),
        "upstream_selected_stack_handoff_packet_ref": fixture.get(
            "upstream_selected_stack_handoff_packet_ref"
        ),
        "upstream_trade_context_selection_packet_ref": fixture.get(
            "upstream_trade_context_selection_packet_ref"
        ),
        "upstream_candidate_generation_packet_ref": fixture.get(
            "upstream_candidate_generation_packet_ref"
        ),
        "upstream_trade_context_ref": fixture.get("upstream_trade_context_ref"),
        "upstream_routed_selection_universe_ref": fixture.get(
            "upstream_routed_selection_universe_ref"
        ),
        "selected_stack_id": selected_stack_id,
        "selected_candidate_stack_id": fixture.get("expected_selected_candidate_stack_id")
        if selected_stack_id
        else None,
        "selected_candidate_generation_key": fixture.get(
            "expected_selected_candidate_generation_key"
        )
        if selected_stack_id
        else None,
        "selected_stack_lineage_trace": copy.deepcopy(lineage),
        "selected_stack_digest_or_static_ref": _digest(
            (
                selected_stack_id,
                source_request.get("request_id"),
                source_request.get("request_type"),
            )
        )
        if selected_stack_id
        else None,
        "requested_decision_scope": source_request.get("requested_decision_scope"),
        "requested_platform_scope": list(source_request.get("requested_platform_scope", [])),
        "requested_venue_scope": list(source_request.get("requested_venue_scope", [])),
        "requested_strategy_scope": source_request.get("requested_strategy_scope"),
        "requested_agent_scope": list(source_request.get("requested_agent_scope", [])),
        "requested_family_scope": list(source_request.get("requested_family_scope", [])),
        "requested_row_scope": list(source_request.get("requested_row_scope", [])),
        "request_reason_codes": list(source_request.get("request_reason_codes", [])),
        "request_basis_refs": list(fixture.get("request_basis_refs", [])) if valid else [],
        "owner_review_basis_codes": list(fixture.get("owner_review_basis_codes", [])) if valid else [],
        "dependency_gate_matrix": _gate_dependency_matrix(fixture),
        "dependency_blocker_severity": source_request.get("dependency_blocker_severity"),
        "owner_policy_priority_class": source_request.get("owner_policy_priority_class"),
        "source_evidence_gate_state": fixture.get("source_evidence_gate_state"),
        "accepted_source_packet_required_flag": True,
        "accepted_source_packet_created_flag": False,
        "connector_semantic_gate_state": fixture.get("connector_semantic_gate_state"),
        "connector_semantic_binding_required_flag": True,
        "connector_semantic_binding_created_flag": False,
        "runtime_cash_gate_state": fixture.get("runtime_cash_gate_state"),
        "runtime_cash_receipt_required_flag": True,
        "runtime_cash_receipt_created_flag": False,
        "replay_paper_gate_state": fixture.get("replay_paper_gate_state"),
        "dual_result_review_state": fixture.get("dual_result_review_state"),
        "risk_gate_state": fixture.get("risk_gate_state"),
        "order_router_gate_state": fixture.get("order_router_gate_state"),
        "dashboard_gate_state": fixture.get("dashboard_gate_state"),
        "quantum_priority_related_flag": bool(source_request.get("quantum_priority_related_flag")),
        "quantum_applicability_summary": copy.deepcopy(quantum_summary),
        "owner_quantum_priority_summary": copy.deepcopy(owner_quantum_summary),
        "quantum_candidate_type": pr92_item.get("quantum_candidate_type"),
        "classical_comparator_required_flag": True,
        "classical_comparator_ref": pr92_item.get("classical_comparator_ref"),
        "classical_fallback_ref": "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "quantum_backend_enablement_requested_flag": bool(
            source_request.get("quantum_backend_enablement_requested_flag")
        ),
        "quantum_backend_enablement_allowed_flag": False,
        "quantum_backend_execution_created_flag": False,
        "quantum_simulator_execution_created_flag": False,
        "pr94_owner_override_receipt_authoring_required_flag": bool(
            source_request.get("pr94_owner_override_receipt_authoring_required_flag")
        ),
        "pr94_owner_override_receipt_created_flag": False,
        "pr94_owner_override_receipt_authoring_gate_created_flag": False,
        "pr95_dashboard_approval_menu_required_flag": bool(
            source_request.get("pr95_dashboard_approval_menu_required_flag")
        ),
        "pr95_dashboard_approval_menu_created_flag": False,
        "pr96_dashboard_approval_static_screen_required_flag": bool(
            source_request.get("pr96_dashboard_approval_static_screen_required_flag")
        ),
        "pr96_dashboard_approval_static_screen_created_flag": False,
        "live_order_execution_allowed_flag": False,
        "live_routing_allowed_flag": False,
        "order_submission_allowed_flag": False,
        "order_intent_authority_created_flag": False,
        "live_trade_authority_created_flag": False,
        "profit_evidence_created_flag": False,
        "reason_codes": reason_codes,
        "blocked_reason_codes": list(block_codes),
        "valid_queue_entry_flag": valid,
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        entry[field] = False
    for field in NO_AUTHORITY_TRUE_FIELDS:
        entry[field] = True
    return entry


def build_owner_approval_request_queue_registry_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    del registry
    failures: list[str] = []
    case = _case_by_id(fixture, case_id)
    pr92_packet = copy.deepcopy(
        upstream.get("owner_live_promotion_review_parameter_stack_packet", {})
    )
    if case.get("missing_pr92_owner_review_packet") is True:
        pr92_packet = {}
    pr92_item = _pr92_owner_review_item(pr92_packet)
    lineage = _selected_stack_lineage_trace(pr92_packet, pr92_item, case)
    base_block_codes = _block_codes_for_case(pr92_packet, pr92_item, fixture, case, lineage)
    source_requests = _case_source_requests(fixture, case) if case_id is not None else copy.deepcopy(_list_of_mappings(fixture.get("queue_source_requests")))
    if not source_requests:
        failures.append("fixture must define queue_source_requests")

    entries: list[dict[str, Any]] = []
    seen_dedupe: dict[str, str] = {}
    for source_request in source_requests:
        block_codes = list(base_block_codes)
        duplicate_of_request_id = None
        dedupe_identity = str(source_request.get("dedupe_identity") or "")
        if not dedupe_identity:
            block_codes.append("OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MISSING_REQUEST_BASIS")
        elif dedupe_identity in seen_dedupe:
            duplicate_of_request_id = seen_dedupe[dedupe_identity]
            block_codes = _sort_reason_codes(
                [*block_codes, "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DUPLICATE_REQUEST_COLLISION"]
            )
        else:
            seen_dedupe[dedupe_identity] = str(source_request.get("request_id") or "")
        entries.append(
            _queue_entry(
                source_request,
                fixture,
                pr92_packet,
                pr92_item,
                lineage,
                _sort_reason_codes(block_codes),
                duplicate_of_request_id=duplicate_of_request_id,
            )
        )

    entries = sorted(entries, key=_entry_order_key)
    valid_count = sum(1 for entry in entries if entry.get("request_status") == "PENDING_OWNER_DECISION")
    blocked_count = sum(1 for entry in entries if str(entry.get("request_status", "")).startswith("BLOCKED"))
    duplicate_count = sum(1 for entry in entries if entry.get("request_status") == "BLOCKED_DUPLICATE_REQUEST")
    agent_self_approval_attempt_count = sum(
        1
        for entry in entries
        if "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN"
        in entry.get("blocked_reason_codes", [])
    )
    all_reason_codes = _sort_reason_codes(
        code
        for entry in entries
        for code in list(entry.get("reason_codes", [])) + list(entry.get("blocked_reason_codes", []))
    )
    packet: dict[str, Any] = {
        "owner_approval_request_queue_registry_id": REGISTRY_ID,
        "owner_approval_request_queue_packet_contract_id": PACKET_CONTRACT_ID,
        "schema_version": fixture.get("schema_version"),
        "mode": fixture.get("mode"),
        "execution": fixture.get("execution"),
        "semantic_task_id": SEMANTIC_TASK_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "queue_scope": QUEUE_SCOPE,
        "queue_authority_class": QUEUE_AUTHORITY_CLASS,
        "queue_registry_status": fixture.get("queue_registry_status"),
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "queue_determinism_policy": {
            "no_randomness": True,
            "no_wall_clock_identity": True,
            "environment_dependent_ordering_allowed": False,
            "stable_queue_registry_id": REGISTRY_ID,
            "stable_sort_key_fields": list(ORDERING_KEY_FIELDS),
        },
        "queue_ordering_policy": {
            "ordering_scope": "STATIC_QUEUE_ORDER_ONLY",
            "ordering_is_owner_decision": False,
            "ordering_key_fields": list(ORDERING_KEY_FIELDS),
        },
        "queue_idempotency_policy": {
            "dedupe_identity_required": True,
            "ambiguous_identity_blocks_request": True,
            "random_suffix_allowed": False,
            "wall_clock_suffix_allowed": False,
        },
        "request_deduplication_policy": {
            "duplicate_request_identity_blocks_later_duplicate": True,
            "duplicate_block_status": "BLOCKED_DUPLICATE_REQUEST",
            "duplicate_reason_code": "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DUPLICATE_REQUEST_COLLISION",
        },
        "request_type_taxonomy": list(REQUEST_TYPE_ORDER),
        "request_status_taxonomy": list(REQUEST_STATUS_ORDER),
        "request_priority_taxonomy": list(REQUEST_PRIORITY_ORDER),
        "owner_decision_required_flag": True,
        "owner_decision_state": OWNER_DECISION_STATE if valid_count else "BLOCKED_PENDING_OWNER_DECISION",
        "owner_decision_option_set": list(OWNER_DECISION_OPTION_ORDER),
        "owner_decision_option_authority_class": OWNER_DECISION_OPTION_AUTHORITY_CLASS,
        "owner_decision_created_flag": False,
        "owner_approval_receipt_created_flag": False,
        "owner_override_receipt_created_flag": False,
        "live_promotion_created_flag": False,
        "canary_eligibility_created_flag": False,
        "dashboard_runtime_created_flag": False,
        "queue_entries": entries,
        "queue_entry_count": len(entries),
        "valid_request_count": valid_count,
        "blocked_request_count": blocked_count,
        "rejected_request_count": 0,
        "duplicate_request_count": duplicate_count,
        "pending_owner_decision_count": valid_count,
        "agent_self_approval_attempt_count": agent_self_approval_attempt_count,
        "owner_decision_created_count": 0,
        "owner_approval_receipt_created_count": 0,
        "owner_override_receipt_created_count": 0,
        "live_promotion_created_count": 0,
        "canary_eligibility_created_count": 0,
        "source_retrieval_count": 0,
        "source_acceptance_count": 0,
        "connector_binding_count": 0,
        "runtime_cash_receipt_count": 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "order_submission_count": 0,
        "order_authoritative_item_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "profit_evidence_created_count": 0,
        "queue_reason_codes": all_reason_codes,
        "blocked_reason_codes": _sort_reason_codes(
            code
            for entry in entries
            for code in entry.get("blocked_reason_codes", [])
        ),
        "upstream_owner_live_promotion_review_packet_ref": fixture.get(
            "upstream_owner_live_promotion_review_packet_ref"
        )
        if pr92_packet
        else None,
        "upstream_owner_live_promotion_review_item_ref": fixture.get(
            "upstream_owner_live_promotion_review_item_ref"
        )
        if pr92_item
        else None,
        "upstream_dual_result_review_packet_ref": fixture.get("upstream_dual_result_review_packet_ref"),
        "upstream_replay_paper_competition_packet_ref": fixture.get(
            "upstream_replay_paper_competition_packet_ref"
        ),
        "upstream_selected_stack_handoff_packet_ref": fixture.get(
            "upstream_selected_stack_handoff_packet_ref"
        ),
        "upstream_trade_context_selection_packet_ref": fixture.get(
            "upstream_trade_context_selection_packet_ref"
        ),
        "upstream_candidate_generation_packet_ref": fixture.get(
            "upstream_candidate_generation_packet_ref"
        ),
        "upstream_trade_context_ref": fixture.get("upstream_trade_context_ref"),
        "upstream_routed_selection_universe_ref": fixture.get(
            "upstream_routed_selection_universe_ref"
        ),
        "selected_stack_id": fixture.get("expected_selected_stack_id") if valid_count else None,
        "selected_stack_lineage_trace": copy.deepcopy(lineage),
        "request_basis_refs": list(fixture.get("request_basis_refs", [])) if valid_count else [],
        "gate_dependency_matrix": _gate_dependency_matrix(fixture),
        "pr94_owner_override_receipt_authoring_forwardable_flag": True,
        "pr94_owner_override_receipt_authoring_gate_created_flag": False,
        "pr95_dashboard_approval_menu_forwardable_flag": True,
        "pr95_dashboard_approval_menu_created_flag": False,
        "pr96_dashboard_approval_static_screen_forwardable_flag": True,
        "pr96_dashboard_approval_static_screen_created_flag": False,
        "order_router_final_authority_preserved_flag": True,
        "classical_comparator_or_fallback_preserved_flag": any(
            bool(entry.get("classical_comparator_ref") or entry.get("classical_fallback_ref"))
            for entry in entries
        ),
        "quantum_request_metadata_only_flag": True,
        "final_ready": False,
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        packet[field] = False
    for field in NO_AUTHORITY_TRUE_FIELDS:
        packet[field] = True
    if case_id is not None:
        packet["fixture_case_id"] = case_id
        packet["expected_reason_code"] = case.get("expected_reason_code")
    failures.extend(validate_queue_packet(packet, fixture, case_id=case_id))
    return packet, failures


def validate_queue_packet(
    packet: dict[str, Any],
    fixture: dict[str, Any],
    *,
    case_id: str | None = None,
) -> list[str]:
    failures: list[str] = []
    entries = _list_of_mappings(packet.get("queue_entries"))
    if entries != sorted(entries, key=_entry_order_key):
        failures.append("queue entries must be sorted by deterministic queue ordering key")
    if packet.get("owner_decision_created_flag") is not False:
        failures.append("queue packet must not create owner decision")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"packet.{field} must be false")
    for field in NO_AUTHORITY_TRUE_FIELDS:
        if packet.get(field) is not True:
            failures.append(f"packet.{field} must be true")
    for field in ZERO_COUNT_FIELDS:
        if packet.get(field) != 0:
            failures.append(f"packet.{field} must be zero")
    if packet.get("queue_entry_count") != len(entries):
        failures.append("queue_entry_count must match queue_entries length")
    if case_id is None:
        expected_counts = (
            ("queue_entry_count", "expected_queue_entry_count"),
            ("valid_request_count", "expected_valid_request_count"),
            ("blocked_request_count", "expected_blocked_request_count"),
            ("rejected_request_count", "expected_rejected_request_count"),
            ("duplicate_request_count", "expected_duplicate_request_count"),
            ("pending_owner_decision_count", "expected_pending_owner_decision_count"),
            ("agent_self_approval_attempt_count", "expected_agent_self_approval_attempt_count"),
        )
        for packet_field, fixture_field in expected_counts:
            if packet.get(packet_field) != fixture.get(fixture_field):
                failures.append(f"packet.{packet_field} must match fixture.{fixture_field}")
        expected_order = fixture.get("expected_queue_order")
        actual_order = [entry.get("queue_entry_id") for entry in entries]
        if actual_order != expected_order:
            failures.append("default queue order must match fixture.expected_queue_order")
    for entry in entries:
        if entry.get("requesting_agent_authority_class") != REQUESTING_AGENT_AUTHORITY_CLASS:
            failures.append(f"{entry.get('queue_entry_id')} requesting agent authority mismatch")
        if entry.get("owner_decision_created_flag") is not False:
            failures.append(f"{entry.get('queue_entry_id')} must not create owner decision")
        if entry.get("owner_approval_receipt_created_flag") is not False:
            failures.append(f"{entry.get('queue_entry_id')} must not create owner approval receipt")
        if entry.get("owner_override_receipt_created_flag") is not False:
            failures.append(f"{entry.get('queue_entry_id')} must not create owner override receipt")
        if entry.get("valid_queue_entry_flag") is True and not _has_required_lineage(
            _list_of_mappings(entry.get("selected_stack_lineage_trace"))
        ):
            failures.append(f"{entry.get('queue_entry_id')} missing required selected stack lineage")
        for field in NO_AUTHORITY_FALSE_FIELDS:
            if entry.get(field) is not False:
                failures.append(f"{entry.get('queue_entry_id')}.{field} must be false")
        for field in NO_AUTHORITY_TRUE_FIELDS:
            if entry.get(field) is not True:
                failures.append(f"{entry.get('queue_entry_id')}.{field} must be true")
    if case_id is not None:
        case = _case_by_id(fixture, case_id)
        expected_reason = case.get("expected_reason_code")
        reason_codes = set(packet.get("queue_reason_codes", [])) | set(
            packet.get("blocked_reason_codes", [])
        )
        if expected_reason not in reason_codes:
            failures.append(f"fixture case {case_id} missing expected reason code {expected_reason}")
        if packet.get("valid_request_count") != case.get("expected_valid_request_count"):
            failures.append(f"fixture case {case_id} valid_request_count mismatch")
    return failures


def validate_fixture(
    fixture: dict[str, Any],
    registry: dict[str, Any],
    upstream: dict[str, Any],
) -> tuple[list[str], dict[str, Any], list[dict[str, Any]]]:
    failures: list[str] = []
    if fixture.get("deterministic_output") is not True:
        failures.append("fixture deterministic_output must be true")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = {case.get("case_id") for case in cases}
    missing_cases = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing_cases:
        failures.append(f"fixture missing required cases: {', '.join(missing_cases)}")
    packet, packet_failures = build_owner_approval_request_queue_registry_packet(
        registry,
        fixture,
        upstream,
    )
    failures.extend(packet_failures)
    case_packets: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case.get("case_id"))
        case_packet, case_failures = build_owner_approval_request_queue_registry_packet(
            registry,
            fixture,
            upstream,
            case_id=case_id,
        )
        failures.extend(case_failures)
        case_packets.append(case_packet)
    return failures, packet, case_packets


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    forbidden_paths = (
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalMenu.report.json"),
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalStaticScreen.report.json"),
    )
    for path in forbidden_paths:
        if _resolve(repo_root, path).exists():
            failures.append(f"PR93 must not create later-scope artifact: {path.as_posix()}")
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
            "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    return pr92_gate.validate_validator_static_surface(validator_path)


def _proof_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    entries = _list_of_mappings(packet.get("queue_entries"))
    first_valid = next((entry for entry in entries if entry.get("valid_queue_entry_flag") is True), {})
    lineage = _list_of_mappings(first_valid.get("selected_stack_lineage_trace"))
    artifact_ids = _lineage_artifact_ids(lineage)
    duplicate_entries = [
        entry for entry in entries if entry.get("request_status") == "BLOCKED_DUPLICATE_REQUEST"
    ]
    return {
        "no_randomness": True,
        "no_wall_clock_identity": True,
        "queue_entries_derived_only_from_approved_static_inputs": True,
        "queue_entries_derived_from_pr92_where_parameter_stack_promotion_request": True,
        "selected_stack_lineage_traces_to_pr91_dual_result_review_packet": (
            "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr90_competition_packet": (
            "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr89_handoff_packet": (
            "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr88_selection_packet": (
            "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE" in artifact_ids
        ),
        "selected_stack_lineage_traces_to_pr87_candidate_packet": (
            "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE" in artifact_ids
        ),
        "stable_queue_registry_id": packet.get("owner_approval_request_queue_registry_id"),
        "stable_queue_entry_ids": [entry.get("queue_entry_id") for entry in entries],
        "stable_request_ids": [entry.get("request_id") for entry in entries],
        "deterministic_queue_ordering": True,
        "duplicate_request_handling": {
            "duplicate_request_count": packet.get("duplicate_request_count"),
            "duplicate_entry_ids": [entry.get("queue_entry_id") for entry in duplicate_entries],
            "duplicate_reason_code": "OWNER_APPROVAL_REQUEST_QUEUE_BLOCKED_DUPLICATE_REQUEST_COLLISION",
        },
        "owner_decision_state": packet.get("owner_decision_state"),
        "owner_approval_receipt_created": packet.get("owner_approval_receipt_created_flag"),
        "owner_override_receipt_created": packet.get("owner_override_receipt_created_flag"),
        "repeated_run_test": True,
        "missing_non_forwardable_pr92_fail_closed_behavior": True,
        "source_connector_runtime_cash_blocker_fail_closed_behavior": True,
        "agent_self_approval_approval_fabrication_fail_closed_behavior": True,
        "quantum_metadata_consumed": bool(first_valid.get("quantum_applicability_summary")),
        "owner_quantum_policy_consumed": bool(first_valid.get("owner_quantum_priority_summary")),
        "classical_comparator_fallback_preserved": bool(
            first_valid.get("classical_comparator_ref") or first_valid.get("classical_fallback_ref")
        ),
        "quantum_backend_enablement_request_handled_as": "STATIC_REQUEST_METADATA_ONLY_NO_BACKEND_EXECUTION",
        "backend_execution_count": packet.get("quantum_backend_execution_count"),
        "simulator_execution_count": packet.get("quantum_simulator_execution_count"),
        "quantum_advantage_claim_created": packet.get("quantum_advantage_claim_created_flag"),
        "agents_may_request": True,
        "agents_may_approve": False,
        "owner_decision_options_referenced": True,
        "owner_decision_created": packet.get("owner_decision_created_flag"),
        "owner_approval_receipt_created": packet.get("owner_approval_receipt_created_flag"),
        "owner_override_receipt_created": packet.get("owner_override_receipt_created_flag"),
        "pr94_receipt_forwardability_metadata_created": True,
        "pr94_receipt_authoring_gate_created": packet.get(
            "pr94_owner_override_receipt_authoring_gate_created_flag"
        ),
        "pr95_dashboard_menu_forwardability_metadata_created": True,
        "pr95_dashboard_menu_created": packet.get("pr95_dashboard_approval_menu_created_flag"),
        "pr96_dashboard_screen_forwardability_metadata_created": True,
        "pr96_dashboard_screen_created": packet.get(
            "pr96_dashboard_approval_static_screen_created_flag"
        ),
        "dashboard_runtime_service_created": packet.get("dashboard_runtime_service_created_flag"),
        "order_intent_adjacent_surface_inherited": True,
        "order_intent_authority_created": packet.get("order_intent_authority_created_flag"),
        "order_submission_allowed": packet.get("order_submission_allowed_flag"),
        "live_routing_allowed": packet.get("live_routing_allowed_flag"),
        "source_retrieval_acceptance_created": False,
        "accepted_source_packet_created": packet.get("accepted_source_packet_created_flag"),
        "connector_semantic_binding_created": packet.get("connector_semantic_binding_created_flag"),
        "runtime_cash_receipt_created": packet.get("runtime_cash_receipt_created_flag"),
        "replay_execution_created": packet.get("replay_execution_created_flag"),
        "paper_execution_created": packet.get("paper_execution_created_flag"),
        "real_replay_paper_result_created": False,
        "live_promotion_created": packet.get("live_promotion_created_flag"),
        "canary_eligibility_created": packet.get("canary_eligibility_created_flag"),
        "live_order_authority_created": packet.get("order_authority_created_flag"),
        "atomicrows_bundle_jsonl_created": packet.get("atomicrows_bundle_jsonl_created"),
        "atomicrows_bundle_sha256_created": packet.get("atomicrows_bundle_sha256_created"),
        "master_plan_edited": False,
    }


def build_report(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    packet: dict[str, Any],
    case_packets: list[dict[str, Any]],
    upstream: dict[str, Any],
    metadata: dict[str, Any],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
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
        "validator_marker_source": metadata.get("validator_marker_source"),
        "owner_approval_request_queue_registry_id": registry.get(
            "owner_approval_request_queue_registry_id"
        ),
        "owner_approval_request_queue_packet_contract_id": registry.get(
            "owner_approval_request_queue_packet_contract_id"
        ),
        "queue_scope": registry.get("queue_scope"),
        "queue_authority_class": registry.get("queue_authority_class"),
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "queue_determinism_policy": copy.deepcopy(registry.get("queue_determinism_policy")),
        "queue_ordering_policy": copy.deepcopy(registry.get("queue_ordering_policy")),
        "queue_idempotency_policy": copy.deepcopy(registry.get("queue_idempotency_policy")),
        "request_deduplication_policy": copy.deepcopy(
            registry.get("request_deduplication_policy")
        ),
        "request_type_taxonomy": list(REQUEST_TYPE_ORDER),
        "request_status_taxonomy": list(REQUEST_STATUS_ORDER),
        "request_priority_taxonomy": list(REQUEST_PRIORITY_ORDER),
        "owner_decision_option_set": list(OWNER_DECISION_OPTION_ORDER),
        "queue_inputs": list(QUEUE_INPUT_ORDER),
        "queue_outputs": list(QUEUE_OUTPUT_ORDER),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "upstream_dependencies": copy.deepcopy(registry.get("upstream_dependencies")),
        "future_consumers": copy.deepcopy(registry.get("future_consumers")),
        "upstream_owner_live_promotion_review_packet_ref": copy.deepcopy(
            registry.get("upstream_owner_live_promotion_review_packet_ref")
        ),
        "owner_approval_receipt_boundary_ref": copy.deepcopy(
            registry.get("owner_approval_receipt_boundary_ref")
        ),
        "owner_override_receipt_boundary_ref": copy.deepcopy(
            registry.get("owner_override_receipt_boundary_ref")
        ),
        "source_connector_runtime_order_boundary_refs": copy.deepcopy(
            registry.get("source_connector_runtime_order_boundary_refs")
        ),
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "master_plan_missing_locator_items": [],
        "owner_approval_request_queue_registry_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "pr92_owner_live_promotion_review_report_marker": upstream.get("pr92_report", {}).get(
            "validation_marker"
        ),
        "queue_entry_count": packet.get("queue_entry_count"),
        "valid_request_count": packet.get("valid_request_count"),
        "blocked_request_count": packet.get("blocked_request_count"),
        "rejected_request_count": packet.get("rejected_request_count"),
        "duplicate_request_count": packet.get("duplicate_request_count"),
        "pending_owner_decision_count": packet.get("pending_owner_decision_count"),
        "agent_self_approval_attempt_count": packet.get("agent_self_approval_attempt_count"),
        "owner_decision_created_count": packet.get("owner_decision_created_count"),
        "owner_approval_receipt_created_count": packet.get(
            "owner_approval_receipt_created_count"
        ),
        "owner_override_receipt_created_count": packet.get(
            "owner_override_receipt_created_count"
        ),
        "live_promotion_created_count": packet.get("live_promotion_created_count"),
        "canary_eligibility_created_count": packet.get("canary_eligibility_created_count"),
        "source_retrieval_count": packet.get("source_retrieval_count"),
        "source_acceptance_count": packet.get("source_acceptance_count"),
        "connector_binding_count": packet.get("connector_binding_count"),
        "runtime_cash_receipt_count": packet.get("runtime_cash_receipt_count"),
        "replay_execution_count": packet.get("replay_execution_count"),
        "paper_execution_count": packet.get("paper_execution_count"),
        "order_submission_count": packet.get("order_submission_count"),
        "order_authoritative_item_count": packet.get("order_authoritative_item_count"),
        "quantum_backend_execution_count": packet.get("quantum_backend_execution_count"),
        "quantum_simulator_execution_count": packet.get("quantum_simulator_execution_count"),
        "profit_evidence_created_count": packet.get("profit_evidence_created_count"),
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "final_ready": False,
    }
    report.update(_proof_from_packet(packet))
    for field in NO_AUTHORITY_FALSE_FIELDS:
        report[field] = False
    for field in NO_AUTHORITY_TRUE_FIELDS:
        report[field] = True
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

    metadata_failures, metadata = validate_pr93_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_registry_payload(registry, repo_root=repo_root))
    fixture_failures, packet, case_packets = validate_fixture(fixture, registry, upstream)
    failures.extend(fixture_failures)
    failures.extend(validate_filesystem_boundaries(repo_root))
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
