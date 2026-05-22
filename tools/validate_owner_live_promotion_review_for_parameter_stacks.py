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
from tools import validate_dual_result_review_for_parameter_stacks as pr91_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "owner_live_promotion_review_for_parameter_stacks.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "OwnerLivePromotionReviewForParameterStacks.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_owner_live_promotion_review_for_parameter_stacks.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerLivePromotionReviewForParameterStacks.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr91_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr91_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr91_gate.MASTER_PLAN_CURRENT

GATE_REGISTRY_ID = "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_GATE"
PACKET_CONTRACT_ID = "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_V1"
REPORT_ID = "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #92"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-OWNER-LIVE-PROMOTION-REVIEW-FOR-PARAMETER-STACKS"
TARGET_BRANCH = "pr92-owner-live-promotion-review-parameter-stack-gate"
EXPECTED_BASELINE_ANCESTOR = "8939da6"
GATE_SCOPE = "STATIC_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_ONLY"
REVIEW_SCOPE = "STATIC_ONLY"
REVIEW_AUTHORITY_CLASS = (
    "STATIC_OWNER_LIVE_PROMOTION_REVIEW_NOT_OWNER_APPROVAL_NOT_LIVE_EXECUTION_"
    "NOT_ORDER_AUTHORITY"
)
OWNER_REVIEW_REQUEST_AUTHORITY_CLASS = "STATIC_AGENT_REQUEST_ONLY_OWNER_DECISION_REQUIRED"
REQUESTING_AGENT_AUTHORITY_CLASS = "AGENT_MAY_REQUEST_OWNER_DECIDES"
OWNER_DECISION_OPTION_AUTHORITY_CLASS = "STATIC_OPTION_SCHEMA_ONLY_NOT_DECISION"
ORDER_INTENT_PREVIEW_AUTHORITY = pr91_gate.ORDER_INTENT_PREVIEW_AUTHORITY
SUCCESS_MARKER = "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK"
FAILURE_MARKER = "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr91_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr91_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr91_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
REPAIR_BRANCH_PREFIX = "repair/"

ROLE_ORDER = pr91_gate.ROLE_ORDER
DEPENDENCY_ORDER = pr91_gate.DEPENDENCY_ORDER + (
    "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS",
)
DEPENDENCY_MARKERS = {
    **pr91_gate.DEPENDENCY_MARKERS,
    "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS": pr91_gate.SUCCESS_MARKER,
}
FUTURE_CONSUMER_ORDER = (
    "PR93_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY",
    "PR94_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE",
    "PR95_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA",
    "PR96_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT",
    "LATER_THREE_VENUE_CANARY_ELIGIBILITY_GATE",
)
OWNER_DECISION_OPTION_ORDER = (
    "PENDING_OWNER_REVIEW",
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
    "BLOCKED_PENDING_OWNER_DECISION",
)
REVIEW_INPUT_ORDER = (
    "PR91_static_dual_result_review_parameter_stack_packet",
    "PR90_static_replay_paper_candidate_stack_competition_packet_lineage",
    "PR89_static_selected_parameter_stack_handoff_packet_lineage",
    "PR88_static_trade_context_parameter_stack_selection_packet_lineage",
    "PR87_static_candidate_generation_packet_lineage",
    "PR78_static_trade_context_packet_metadata",
    "PR81_routed_selection_universe_metadata",
    "PR82_quantum_applicability_metadata",
    "PR83_owner_quantum_priority_policy_metadata",
    "PR84_scoring_policy_registry",
    "PR85_static_scoring_ranking_metadata",
    "PR86_static_optimizer_arbitration_metadata",
    "Stage1_owner_live_promotion_review_static_contract",
    "Stage1_owner_approval_receipt_boundary_static_contract",
    "Stage1_three_venue_canary_eligibility_static_contract",
    "Source_evidence_connector_runtime_cash_order_router_boundary_static_contracts",
)
REVIEW_OUTPUT_ORDER = (
    "static_owner_live_promotion_review_parameter_stack_packet",
    "static_owner_review_item_descriptors",
    "static_owner_review_request_descriptor",
    "static_owner_decision_option_schema_only",
    "static_gate_dependency_matrix",
    "static_fail_closed_owner_review_case_packets",
    "pr93_pr96_forwardability_metadata_no_future_artifacts_created",
    "no_owner_approval_receipt_boundary",
    "no_owner_override_receipt_boundary",
    "no_live_promotion_boundary",
    "no_canary_eligibility_boundary",
    "no_order_authority_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "no_profit_evidence_boundary",
)
DETERMINISTIC_REVIEW_CHAIN = (
    "PR91_dual_result_review_packet_required",
    "PR91_dual_result_review_item_required",
    "PR91_review_item_static_forwardability_required",
    "selected_stack_lineage_to_PR91_PR90_PR89_PR88_PR87_required",
    "trade_context_and_routed_selection_universe_lineage_required",
    "role_completion_and_compatibility_required",
    "blocked_rows_absent",
    "source_connector_runtime_cash_risk_order_router_gate_requirements_preserved",
    "requesting_agents_request_only_owner_decides",
    "owner_decision_pending_no_receipt_created",
    "pr93_pr96_forwardability_metadata_only",
    "quantum_policy_lineage_with_classical_comparator_or_fallback",
    "owner_override_internal_basis_only_when_recorded",
    "replay_paper_result_separation_preserved",
    "no_live_promotion_no_canary_no_order_authority",
    "lexicographic_owner_review_packet_and_item_ids",
)
REASON_CODE_ORDER = (
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_STATIC_OWNER_REQUEST_ONLY",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR91_DUAL_RESULT_REVIEW_PACKET",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR90_COMPETITION_PACKET_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR89_HANDOFF_PACKET_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR88_SELECTION_PACKET_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR87_CANDIDATE_PACKET_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_TRADE_CONTEXT_ROUTE_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_QUANTUM_POLICY_LINEAGE",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_AGENTS_REQUEST_OWNER_DECIDES",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_OWNER_DECISION_PENDING",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_DECISION_OPTIONS_SCHEMA_ONLY",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_SOURCE_CONNECTOR_RUNTIME_CASH_RISK_ORDER_ROUTER_GATES_REQUIRED",
    "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR93_PR96_FORWARDABILITY_ONLY",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_NO_FORWARDABLE_DUAL_RESULT_REVIEW_FOR_OWNER_PROMOTION",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_PR91_DUAL_RESULT_REVIEW_PACKET",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_NON_FORWARDABLE_PR91_REVIEW",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_OWNER_REQUEST_BASIS",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR91_PR90_PR89_PR88_PR87",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_SELECTED_STACK_ID",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_BLOCKED_CANDIDATE",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_INCOMPATIBLE_CANDIDATE",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_REQUIRED_ROLE_CANDIDATE",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_REPLAY_PAPER_IDENTITY_MISMATCH",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_MERGE_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_OVERWRITE_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_COLLAPSE_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_AUTO_PROMOTION_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR93_QUEUE_CREATION_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR94_RECEIPT_AUTHORING_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR95_DASHBOARD_MENU_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR96_DASHBOARD_SCREEN_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR92_METADATA_VERIFIED",
    "PASS_VALID_STATIC_OWNER_REVIEW_REQUEST_FROM_PR91",
    "PASS_SELECTED_STACK_LINEAGE_TO_PR91_PR90_PR89_PR88_PR87",
    "PASS_PENDING_OWNER_DECISION_STATE",
    "PASS_OWNER_DECISION_OPTIONS_SCHEMA_ONLY",
    "PASS_AGENT_REQUEST_NO_SELF_APPROVAL",
    "PASS_OWNER_AUTHORITY_NO_EXTERNAL_FACT_FABRICATION",
    "PASS_OWNER_OVERRIDE_BASIS_NO_RECEIPT_CREATED",
    "PASS_QUANTUM_AWARE_CLASSICAL_COMPARATOR_PRESERVED",
    "PASS_STATIC_QUANTUM_METADATA_NO_BACKEND_EXECUTION",
    "PASS_SOURCE_CONNECTOR_RUNTIME_CASH_ORDER_GATES_REQUIRED",
    "PASS_PR93_PR96_BOUNDARY_FORWARDABILITY_ONLY",
    "BLOCK_MISSING_PR91_DUAL_RESULT_REVIEW_PACKET",
    "BLOCK_NON_FORWARDABLE_PR91_REVIEW",
    "BLOCK_MISSING_OWNER_REQUEST_BASIS",
    "BLOCK_MISSING_SELECTED_STACK_ID",
    "BLOCK_BLOCKED_CANDIDATE",
    "BLOCK_INCOMPATIBLE_CANDIDATE",
    "BLOCK_MISSING_ROLE_CANDIDATE",
    "BLOCK_REPLAY_PAPER_IDENTITY_MISMATCH",
    "BLOCK_RESULT_MERGE",
    "BLOCK_RESULT_OVERWRITE",
    "BLOCK_RESULT_COLLAPSE",
    "BLOCK_AGENT_SELF_APPROVAL_ATTEMPT",
    "BLOCK_OWNER_APPROVAL_RECEIPT_FABRICATION",
    "BLOCK_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    "BLOCK_AUTO_PROMOTION_ATTEMPT",
    "BLOCK_LIVE_PROMOTION_ATTEMPT",
    "BLOCK_CANARY_ELIGIBILITY_CREATION_ATTEMPT",
    "BLOCK_EXECUTABLE_ORDER_INTENT_ATTEMPT",
    "BLOCK_ORDER_AUTHORITY_ATTEMPT",
    "BLOCK_LIVE_ROUTING_ATTEMPT",
    "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_ATTEMPT",
    "BLOCK_CONNECTOR_BINDING_ATTEMPT",
    "BLOCK_RUNTIME_CASH_CREATION_ATTEMPT",
    "BLOCK_DASHBOARD_RUNTIME_CREATION_ATTEMPT",
    "BLOCK_PR93_QUEUE_CREATION_ATTEMPT",
    "BLOCK_PR94_RECEIPT_AUTHORING_ATTEMPT",
    "BLOCK_PR95_DASHBOARD_MENU_CREATION_ATTEMPT",
    "BLOCK_PR96_DASHBOARD_SCREEN_CREATION_ATTEMPT",
    "BLOCK_ATOMICROWS_BUNDLE_ATTEMPT",
    "BLOCK_ATOMICROWS_SHA_ATTEMPT",
    "BLOCK_OPTIMIZER_EXECUTION_ATTEMPT",
    "BLOCK_QUANTUM_BACKEND_EXECUTION_ATTEMPT",
    "BLOCK_QUANTUM_SIMULATOR_EXECUTION_ATTEMPT",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
)
REQUIRED_MASTER_PLAN_PRINCIPLES = {
    "AGENTS_MAY_REQUEST_OWNER_DECIDES",
    "OWNER_APPROVAL_NON_DELEGABLE",
    "OWNER_GLOBAL_AUTHORITY_INTERNAL_ONLY",
    "OWNER_OVERRIDE_CANNOT_FABRICATE_FACTS",
    "NO_AUTOMATIC_LIVE_PROMOTION",
    "OWNER_REVIEW_NOT_LIVE_ORDER_EXECUTION",
    "SOURCE_EVIDENCE_REQUIRED_NO_BYPASS",
    "CONNECTOR_SEMANTIC_BINDING_REQUIRED",
    "RUNTIME_CASH_RECEIPT_REQUIRED",
    "RISK_AND_ORDER_ROUTER_GATES_REQUIRED",
    "CANARY_ELIGIBILITY_LATER_GATE",
    "REPLAY_AND_PAPER_RESULTS_REMAIN_SEPARATE",
    "DUAL_RESULT_REVIEW_UPSTREAM_OF_OWNER_REVIEW",
    "OWNER_REVIEW_STATE_CLASSIFICATIONS",
    "ATOMICROWS_INVENTORY_NOT_TRADER",
    "NO_SINGLE_PARAMETER_OR_ALGORITHM_STACKS",
    "MINIMUM_REQUIRED_STACK_ROLES",
    "BLOCKED_ROWS_EXCLUDED_FROM_ACTIVE_REVIEW",
    "QUANTUM_RANK_REFINE_ONLY_NO_DIRECT_LIVE_AUTHORITY",
    "CLASSICAL_EXECUTION_GATES_REMAIN_FINAL",
    "NO_FABRICATION_BOUNDARY",
}
NO_AUTHORITY_FALSE_FIELDS = (
    "source_retrieval_created_flag",
    "source_acceptance_created_flag",
    "accepted_source_packet_created_flag",
    "connector_semantic_binding_created_flag",
    "runtime_cash_receipt_created_flag",
    "live_trade_authority_created_flag",
    "owner_decision_created_flag",
    "owner_approval_receipt_created_flag",
    "owner_override_receipt_created_flag",
    "executable_order_intent_created_flag",
    "order_authority_created_flag",
    "order_submission_allowed_flag",
    "live_routing_allowed_flag",
    "connector_binding_allowed_flag",
    "replay_execution_created_flag",
    "paper_execution_created_flag",
    "real_replay_result_packet_created_flag",
    "real_paper_result_packet_created_flag",
    "result_values_created_from_execution_flag",
    "optimizer_execution_created_flag",
    "classical_optimizer_execution_created_flag",
    "quantum_optimizer_execution_created_flag",
    "quantum_backend_execution_created_flag",
    "quantum_simulator_execution_created_flag",
    "profit_evidence_created_flag",
    "quantum_advantage_claim_created_flag",
    "latency_superiority_claim_created_flag",
    "execution_superiority_claim_created_flag",
    "pr93_owner_approval_request_queue_created_flag",
    "pr94_owner_override_receipt_created_flag",
    "pr95_dashboard_approval_menu_created_flag",
    "pr96_dashboard_approval_static_screen_created_flag",
    "dashboard_runtime_service_created_flag",
    "canary_eligibility_created_flag",
    "live_promotion_created_flag",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "blocker_reduction_claim_created_flag",
)
NO_AUTHORITY_TRUE_FIELDS = (
    "no_order_authority_flag",
    "no_runtime_execution_flag",
    "no_replay_execution_flag",
    "no_paper_execution_flag",
    "no_owner_approval_flag",
    "no_live_promotion_flag",
    "no_quantum_backend_execution_flag",
    "no_profit_evidence_flag",
    "no_live_trade_authority_flag",
)
ZERO_COUNT_FIELDS = (
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
    "real_optimizer_execution_count",
    "quantum_backend_execution_count",
    "quantum_simulator_execution_count",
)
FIELD_REASON_CODES = {
    "source_retrieval_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    "source_acceptance_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    "accepted_source_packet_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    "connector_semantic_binding_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN",
    "live_trade_authority_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "owner_decision_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
    "owner_approval_receipt_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
    "owner_override_receipt_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION",
    "executable_order_intent_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
    "order_authority_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "order_submission_allowed_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "live_routing_allowed_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "connector_binding_allowed_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "replay_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "paper_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "real_replay_result_packet_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "real_paper_result_packet_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "result_values_created_from_execution_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "classical_optimizer_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_backend_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "profit_evidence_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "execution_superiority_claim_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "pr93_owner_approval_request_queue_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR93_QUEUE_CREATION_FORBIDDEN",
    "pr94_owner_override_receipt_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR94_RECEIPT_AUTHORING_FORBIDDEN",
    "pr95_dashboard_approval_menu_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR95_DASHBOARD_MENU_FORBIDDEN",
    "pr96_dashboard_approval_static_screen_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR96_DASHBOARD_SCREEN_FORBIDDEN",
    "dashboard_runtime_service_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN",
    "canary_eligibility_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    "live_promotion_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "atomicrows_bundle_jsonl_created": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "blocker_reduction_claim_created_flag": "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION",
}


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
    return pr91_gate.load_yaml(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_json(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:  # pragma: no cover - defensive CLI detail
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:  # pragma: no cover - defensive CLI detail
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def schema_subset_failures(
    payload: dict[str, Any], schema: dict[str, Any], label: str
) -> list[str]:
    return [f"{label}{failure}" for failure in validate_json_schema_subset(payload, schema)]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _first_by_key(items: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        value = item.get(key)
        if isinstance(value, str) and value not in result:
            result[value] = item
    return result


def _sort_by_order(values: Iterable[str], order: Sequence[str]) -> list[str]:
    order_index = {value: index for index, value in enumerate(order)}
    return sorted(
        (str(value) for value in values),
        key=lambda item: (order_index.get(item, 999), item),
    )


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order(codes, REASON_CODE_ORDER)


def _digest(parts: Iterable[Any]) -> str:
    normalized = "|".join(json.dumps(part, sort_keys=True) for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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
    return ci_branch_context.is_downstream_or_main_validation_branch(branch, after_pr=92)


def validate_pr92_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 92), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 92), None)
    if roadmap_entry is None:
        failures.append("PR92 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR92 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Owner live-promotion review for parameter stacks"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Owner live-promotion review for parameter stacks"),
        ("blueprint.branch", blueprint_entry.get("branch"), TARGET_BRANCH),
        ("blueprint.semantic_task_id", blueprint_entry.get("semantic_task_id"), SEMANTIC_TASK_ID),
        ("blueprint.validator_marker", blueprint_entry.get("validator_marker"), SUCCESS_MARKER),
        ("blueprint.category", blueprint_entry.get("category"), "STATIC"),
        ("blueprint.stage", blueprint_entry.get("stage"), "Stage 1 prediction-market foundation"),
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
    default_abs = _resolve(repo_root, DEFAULT_REPORT)
    if output_abs != default_abs:
        return False
    if metadata.get("branch") == TARGET_BRANCH:
        return False
    if not output_abs.exists():
        return False
    try:
        existing = load_json(output_abs)
    except Exception:
        return False
    return existing.get("validation_marker") == SUCCESS_MARKER


def validate_dependencies(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    dependency_ids = [
        item.get("artifact_id") for item in _list_of_mappings(payload.get("upstream_dependencies"))
    ]
    if dependency_ids != list(DEPENDENCY_ORDER):
        failures.append("upstream_dependencies must preserve PR77-PR91 dependency order")
    for item in _list_of_mappings(payload.get("upstream_dependencies")):
        artifact_id = str(item.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker is None:
            failures.append(f"unexpected upstream dependency {artifact_id}")
            continue
        if item.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id}.validation_marker must be {expected_marker}")
        for path_field in ("registry_path", "report_path", "validator_path"):
            path_value = item.get(path_field)
            if isinstance(path_value, str) and not _resolve(repo_root, pathlib.Path(path_value)).exists():
                failures.append(f"{artifact_id}.{path_field} missing: {path_value}")
    return failures


def validate_source_connector_runtime_order_refs(
    payload: dict[str, Any], repo_root: pathlib.Path
) -> list[str]:
    failures: list[str] = []
    refs = _list_of_mappings(payload.get("source_connector_runtime_order_boundary_refs"))
    expected_ids = (
        "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER_CONTRACT_STATIC_VALIDATION",
        "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK",
        "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK",
        "RUNTIME_CASH_FIELD_MAP_STATIC_BOUNDARY",
        "ORDER_INTENT_EXECUTION_ROUTER_STATIC_VALIDATION",
    )
    actual_ids = tuple(str(item.get("artifact_id") or "") for item in refs)
    if actual_ids != expected_ids:
        failures.append("source_connector_runtime_order_boundary_refs order mismatch")
    for item in refs:
        for path_field in ("schema_path", "report_path", "validator_path"):
            path_value = item.get(path_field)
            if isinstance(path_value, str) and not _resolve(repo_root, pathlib.Path(path_value)).exists():
                failures.append(f"{item.get('artifact_id')}.{path_field} missing: {path_value}")
        if not item.get("validation_marker"):
            failures.append(f"{item.get('artifact_id')}.validation_marker required")
    return failures


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumer_ids = [
        item.get("consumer_id") for item in _list_of_mappings(payload.get("future_consumers"))
    ]
    if consumer_ids != list(FUTURE_CONSUMER_ORDER):
        failures.append("future_consumers must preserve PR93-PR96 and later canary order")
    for item in _list_of_mappings(payload.get("future_consumers")):
        if item.get("pr92_creates_consumer_execution") is not False:
            failures.append(f"{item.get('consumer_id')} must not create consumer execution")
    return failures


def validate_stage1_contract_refs(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    refs = (
        payload.get("stage1_owner_live_promotion_review_contract_ref"),
        payload.get("stage1_owner_approval_receipt_boundary_ref"),
        payload.get("stage1_three_venue_canary_eligibility_contract_ref"),
    )
    for ref in refs:
        if not isinstance(ref, dict):
            failures.append("stage1 contract ref must be object")
            continue
        for path_field in ("schema_path", "report_path", "validator_path"):
            path_value = ref.get(path_field)
            if isinstance(path_value, str) and not _resolve(repo_root, pathlib.Path(path_value)).exists():
                failures.append(f"{ref.get('artifact_id')}.{path_field} missing: {path_value}")
        marker = str(ref.get("validation_marker") or "")
        if not marker.endswith("_OK"):
            failures.append(f"{ref.get('artifact_id')}.validation_marker must end with _OK")
    return failures


def validate_review_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = payload.get("review_policy")
    if not isinstance(policy, dict):
        return ["review_policy must be an object"]
    true_fields = (
        "stable_sort_required",
        "owner_review_items_derive_only_from_pr91_dual_result_review_packet",
        "selected_stack_lineage_to_pr91_pr90_pr89_pr88_pr87_required",
        "requesting_agents_may_request_only",
        "owner_decision_required",
        "pr93_pr96_forwardability_metadata_only",
        "source_connector_runtime_cash_risk_order_router_gates_required",
        "accepted_source_packet_absence_blocks_live_promotion",
        "connector_semantic_binding_absence_blocks_live_promotion",
        "runtime_cash_receipt_absence_blocks_live_promotion",
        "order_router_final_authority_preserved",
        "quantum_candidates_require_classical_comparator_or_fallback",
    )
    false_fields = (
        "random_identity_allowed",
        "wall_clock_identity_allowed",
        "owner_decision_created",
        "owner_approval_receipt_created",
        "owner_override_receipt_created",
        "live_promotion_created",
        "canary_eligibility_created",
        "order_submission_allowed",
        "live_routing_allowed",
    )
    for field in true_fields:
        if policy.get(field) is not True:
            failures.append(f"review_policy.{field} must be true")
    for field in false_fields:
        if policy.get(field) is not False:
            failures.append(f"review_policy.{field} must be false")
    if policy.get("deterministic_review_chain") != list(DETERMINISTIC_REVIEW_CHAIN):
        failures.append("review_policy.deterministic_review_chain mismatch")
    return failures


def validate_blocked_review_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = payload.get("blocked_review_policy")
    if not isinstance(policy, dict):
        return ["blocked_review_policy must be an object"]
    for field in (
        "blocked_or_rejected_items_remain_traceable",
        "blocked_items_retain_reason_codes",
    ):
        if policy.get(field) is not True:
            failures.append(f"blocked_review_policy.{field} must be true")
    if policy.get("blocked_items_enter_active_owner_review_status") is not False:
        failures.append("blocked_review_policy.blocked_items_enter_active_owner_review_status must be false")
    if policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
        failures.append("blocked_review_policy.blocked_reason_code_order mismatch")
    return failures


def validate_no_authority_flags(payload: dict[str, Any], *, prefix: str) -> list[str]:
    flags = payload.get("required_no_authority_flags")
    if not isinstance(flags, dict):
        return [f"{prefix}.required_no_authority_flags must be an object"]
    return [
        f"{prefix}.required_no_authority_flags.{field} must be false"
        for field, value in flags.items()
        if value is not False
    ]


def validate_gate_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for field, expected in (
        ("owner_live_promotion_review_gate_registry_id", GATE_REGISTRY_ID),
        ("owner_live_promotion_review_parameter_stack_packet_contract_id", PACKET_CONTRACT_ID),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("roadmap_pr_label", ROADMAP_PR_LABEL),
        ("github_pr_number_policy", GITHUB_PR_NUMBER_POLICY),
        ("gate_scope", GATE_SCOPE),
        ("policy_version", POLICY_VERSION),
        ("review_scope", REVIEW_SCOPE),
        ("review_authority_class", REVIEW_AUTHORITY_CLASS),
    ):
        if payload.get(field) != expected:
            failures.append(f"{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "review_contract_only_flag",
    ):
        if payload.get(field) is not True:
            failures.append(f"{field} must be true")
    if payload.get("final_ready") is not False:
        failures.append("final_ready must be false")
    if payload.get("required_stack_roles") != list(ROLE_ORDER):
        failures.append("required_stack_roles must match repo role order")
    if payload.get("owner_decision_option_set") != list(OWNER_DECISION_OPTION_ORDER):
        failures.append("owner_decision_option_set order mismatch")
    if payload.get("review_inputs") != list(REVIEW_INPUT_ORDER):
        failures.append("review_inputs order mismatch")
    if payload.get("review_outputs") != list(REVIEW_OUTPUT_ORDER):
        failures.append("review_outputs order mismatch")
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("reason_codes order mismatch")
    principles = _list_of_mappings(payload.get("master_plan_principles_consumed"))
    principle_ids = {str(item.get("principle_id") or "") for item in principles}
    missing = sorted(REQUIRED_MASTER_PLAN_PRINCIPLES - principle_ids)
    if missing:
        failures.append(f"missing master_plan_principles_consumed: {', '.join(missing)}")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_source_connector_runtime_order_refs(payload, repo_root))
    failures.extend(validate_stage1_contract_refs(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_review_policy(payload))
    failures.extend(validate_blocked_review_policy(payload))
    failures.extend(validate_no_authority_flags(payload, prefix="REGISTRY"))
    return failures


def _validate_report_marker(
    report: dict[str, Any] | None, expected_marker: str, label: str
) -> list[str]:
    if report is None:
        return []
    marker = report.get("validation_marker") or report.get("validator_marker")
    if marker != expected_marker:
        return [f"{label} report marker must be {expected_marker}"]
    return []


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr91_result = pr91_gate.validate(repo_root=repo_root)
    failures.extend(pr91_result.failures)
    pr91_report = pr91_result.report
    failures.extend(_validate_report_marker(pr91_report, pr91_gate.SUCCESS_MARKER, "PR91"))
    if pr91_report is None:
        pr91_report = {}

    stage1_reports: dict[str, dict[str, Any]] = {}
    for label, path in (
        (
            "stage1_owner_live_promotion_review_contract_report",
            pathlib.Path("docs/master_plan/generated/Stage1OwnerLivePromotionReviewContractCheck.report.json"),
        ),
        (
            "stage1_three_venue_canary_eligibility_contract_report",
            pathlib.Path("docs/master_plan/generated/Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"),
        ),
        (
            "stage1_connector_semantic_binding_ledger_report",
            pathlib.Path("docs/master_plan/generated/Stage1ConnectorSemanticBindingLedgerCheck.report.json"),
        ),
        (
            "stage1_runtime_resolver_snapshot_contract_report",
            pathlib.Path("docs/master_plan/generated/Stage1RuntimeResolverSnapshotContractCheck.report.json"),
        ),
    ):
        report, report_failures = _load_json_checked(_resolve(repo_root, path), label)
        failures.extend(report_failures)
        if report is not None:
            marker = report.get("validation_marker") or report.get("validator_marker")
            if marker is not None and not str(marker).endswith("_OK"):
                failures.append(f"{label} marker must end with _OK")
            created_at = report.get("created_at_utc") or report.get("generated_at_utc")
            if created_at not in (None, "STATIC_DETERMINISTIC_NO_WALL_CLOCK"):
                failures.append(f"{label} must use deterministic timestamp sentinel")
            stage1_reports[label] = report

    return failures, {
        "pr91_report": pr91_report,
        "dual_result_review_parameter_stack_packet": pr91_report.get(
            "dual_result_review_parameter_stack_packet", {}
        ),
        "stage1_reports": stage1_reports,
    }


def _case_by_id(fixture: dict[str, Any], case_id: str | None) -> dict[str, Any]:
    if case_id is None:
        return {}
    cases = _first_by_key(_list_of_mappings(fixture.get("fixture_cases")), "case_id")
    return cases.get(case_id, {})


def _pr91_review_item_for_fixture(
    upstream: dict[str, Any], fixture: dict[str, Any]
) -> dict[str, Any]:
    packet = upstream.get("dual_result_review_parameter_stack_packet")
    if not isinstance(packet, dict):
        return {}
    review_items = _list_of_mappings(packet.get("review_items"))
    expected_item_id = fixture.get("expected_dual_result_review_item_id")
    expected_stack_id = fixture.get("expected_selected_stack_id")
    for item in review_items:
        if item.get("review_item_id") == expected_item_id:
            return item
    for item in review_items:
        if item.get("selected_stack_id") == expected_stack_id:
            return item
    return review_items[0] if review_items else {}


def _selected_stack_lineage_trace(
    item: dict[str, Any], fixture: dict[str, Any]
) -> list[dict[str, Any]]:
    lineage = [
        {
            "artifact_id": "PR91_QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS",
            "artifact_ref": fixture.get("upstream_dual_result_review_packet_ref"),
            "review_item_id": fixture.get("expected_dual_result_review_item_id"),
            "validation_marker": pr91_gate.SUCCESS_MARKER,
        }
    ]
    for step in _list_of_mappings(item.get("selected_stack_lineage_trace")):
        lineage.append(copy.deepcopy(step))
    return lineage


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


def _block_codes_for_case(
    item: dict[str, Any] | None,
    fixture: dict[str, Any],
    case: dict[str, Any],
    lineage: list[dict[str, Any]],
) -> list[str]:
    codes: list[str] = []
    if not item:
        codes.append("OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_PR91_DUAL_RESULT_REVIEW_PACKET")
    if case.get("missing_pr91_dual_result_review_packet") is True:
        codes.append("OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_PR91_DUAL_RESULT_REVIEW_PACKET")
    if case.get("non_forwardable_pr91_dual_result_review") is True:
        codes.append("OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_NON_FORWARDABLE_PR91_REVIEW")
    if case.get("missing_owner_request_basis") is True:
        codes.append("OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_OWNER_REQUEST_BASIS")
    selected_stack_id = fixture.get("expected_selected_stack_id")
    if case.get("missing_selected_stack_id") is True:
        selected_stack_id = None
    if not selected_stack_id:
        codes.append("OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_SELECTED_STACK_ID")
    if not _has_required_lineage(lineage):
        codes.append(
            "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR91_PR90_PR89_PR88_PR87"
        )
    mapping = (
        ("blocked_candidate", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_BLOCKED_CANDIDATE"),
        ("incompatible_candidate", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_INCOMPATIBLE_CANDIDATE"),
        ("missing_role_candidate", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_REQUIRED_ROLE_CANDIDATE"),
        ("replay_paper_identity_mismatch", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_REPLAY_PAPER_IDENTITY_MISMATCH"),
        ("result_merge_detected", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_MERGE_FORBIDDEN"),
        ("result_overwrite_detected", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_OVERWRITE_FORBIDDEN"),
        ("result_collapse_detected", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RESULT_COLLAPSE_FORBIDDEN"),
        ("agent_self_approval_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_AGENT_SELF_APPROVAL_FORBIDDEN"),
        ("owner_approval_receipt_fabrication_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_APPROVAL_RECEIPT_FABRICATION"),
        ("owner_override_receipt_fabrication_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OWNER_OVERRIDE_RECEIPT_FABRICATION"),
        ("auto_promotion_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_AUTO_PROMOTION_FORBIDDEN"),
        ("live_promotion_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN"),
        ("canary_eligibility_creation_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN"),
        ("executable_order_intent_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN"),
        ("order_authority_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN"),
        ("live_routing_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_LIVE_ROUTING_FORBIDDEN"),
        ("source_retrieval_acceptance_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN"),
        ("connector_binding_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("runtime_cash_creation_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN"),
        ("dashboard_runtime_creation_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_DASHBOARD_RUNTIME_FORBIDDEN"),
        ("pr93_queue_creation_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR93_QUEUE_CREATION_FORBIDDEN"),
        ("pr94_receipt_authoring_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR94_RECEIPT_AUTHORING_FORBIDDEN"),
        ("pr95_dashboard_menu_creation_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR95_DASHBOARD_MENU_FORBIDDEN"),
        ("pr96_dashboard_screen_creation_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PR96_DASHBOARD_SCREEN_FORBIDDEN"),
        ("atomicrows_bundle_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN"),
        ("atomicrows_sha_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN"),
        ("optimizer_execution_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("quantum_backend_execution_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_simulator_execution_attempt", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN"),
        ("profit_evidence_claim", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("quantum_advantage_claim", "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"),
    )
    for case_field, reason_code in mapping:
        if case.get(case_field) is True:
            codes.append(reason_code)
    return _sort_reason_codes(dict.fromkeys(codes))


def _gate_dependency_matrix() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "SOURCE_EVIDENCE_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "REQUIRED_NOT_SATISFIED_BLOCKS_LIVE_PROMOTION",
            "blocker_code": "SOURCE_EVIDENCE_REVIEW_REQUIRED",
        },
        {
            "gate_id": "ACCEPTED_SOURCE_PACKET_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "REQUIRED_MISSING_BLOCKS_LIVE_PROMOTION",
            "blocker_code": "SOURCE_EVIDENCE_REVIEW_REQUIRED",
        },
        {
            "gate_id": "CONNECTOR_SEMANTIC_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "REQUIRED_NOT_BOUND_BLOCKS_LIVE_PROMOTION",
            "blocker_code": "CONNECTOR_REVIEW_REQUIRED",
        },
        {
            "gate_id": "RUNTIME_CASH_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "REQUIRED_NO_RECEIPT_BLOCKS_LIVE_PROMOTION",
            "blocker_code": "RUNTIME_CASH_REVIEW_REQUIRED",
        },
        {
            "gate_id": "RISK_REVIEW_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "REVIEW_REQUIRED_BLOCKS_LIVE_PROMOTION",
            "blocker_code": "RISK_REVIEW_REQUIRED",
        },
        {
            "gate_id": "ORDER_ROUTER_FINAL_AUTHORITY_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "FINAL_AUTHORITY_PRESERVED_BLOCKS_DIRECT_ORDER",
            "blocker_code": "ORDER_ROUTER_REVIEW_REQUIRED",
        },
        {
            "gate_id": "OWNER_DECISION_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "PENDING_OWNER_DECISION",
            "blocker_code": "OWNER_DECISION_REQUIRED",
        },
        {
            "gate_id": "DASHBOARD_APPROVAL_GATE",
            "required_flag": True,
            "satisfied_flag": False,
            "created_flag": False,
            "gate_state": "DASHBOARD_APPROVAL_REQUIRED_FUTURE_GATE",
            "blocker_code": "DASHBOARD_APPROVAL_REQUIRED",
        },
    ]


def _owner_review_item(
    item: dict[str, Any],
    fixture: dict[str, Any],
    lineage: list[dict[str, Any]],
    *,
    block_codes: Sequence[str],
) -> dict[str, Any]:
    valid = len(block_codes) == 0
    selected_stack_id = None if not valid and "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MISSING_SELECTED_STACK_ID" in block_codes else fixture.get("expected_selected_stack_id")
    owner_review_state = (
        fixture.get("expected_owner_review_state") if valid else block_codes[0]
    )
    owner_decision_state = (
        fixture.get("owner_decision_state") if valid else "BLOCKED_PENDING_OWNER_DECISION"
    )
    selected_stack_digest = _digest(
        (
            selected_stack_id,
            fixture.get("expected_dual_result_review_item_id"),
            fixture.get("expected_competition_entry_id"),
            fixture.get("owner_review_request_id"),
        )
    )
    review_item = {
        "owner_review_item_id": (
            f"PR92_OWNER_REVIEW_ITEM__{selected_stack_id}"
            if selected_stack_id
            else "PR92_OWNER_REVIEW_ITEM__BLOCKED_MISSING_SELECTED_STACK_ID"
        ),
        "owner_live_promotion_review_parameter_stack_packet_id": fixture.get(
            "owner_live_promotion_review_parameter_stack_packet_id"
        ),
        "selected_stack_id": selected_stack_id,
        "selected_candidate_stack_id": item.get(
            "selected_candidate_stack_id", fixture.get("expected_selected_candidate_stack_id")
        ),
        "selected_candidate_generation_key": item.get(
            "selected_candidate_generation_key",
            fixture.get("expected_selected_candidate_generation_key"),
        ),
        "selected_stack_lineage_trace": copy.deepcopy(lineage),
        "selected_stack_digest_or_static_ref": selected_stack_digest,
        "dual_result_review_item_id": fixture.get("expected_dual_result_review_item_id"),
        "competition_entry_id": fixture.get("expected_competition_entry_id"),
        "selected_by_pr88_packet_ref": item.get(
            "selected_by_pr88_packet_ref", fixture.get("upstream_trade_context_selection_packet_ref")
        ),
        "handoff_by_pr89_packet_ref": item.get(
            "handoff_by_pr89_packet_ref", fixture.get("upstream_selected_stack_handoff_packet_ref")
        ),
        "competition_by_pr90_packet_ref": item.get(
            "competition_by_pr90_packet_ref", fixture.get("upstream_replay_paper_competition_packet_ref")
        ),
        "dual_review_by_pr91_packet_ref": fixture.get("upstream_dual_result_review_packet_ref"),
        "candidate_from_pr87_packet_ref": item.get(
            "candidate_from_pr87_packet_ref", fixture.get("upstream_candidate_generation_packet_ref")
        ),
        "trade_context_ref": item.get("trade_context_ref", fixture.get("upstream_trade_context_ref")),
        "routed_selection_universe_ref": item.get(
            "routed_selection_universe_ref", fixture.get("upstream_routed_selection_universe_ref")
        ),
        "venue_scope": item.get("venue_scope", ["KALSHI"]),
        "platform_scope": fixture.get("requested_platform_scope"),
        "market_type": item.get("market_type", "BINARY_OUTCOME"),
        "strategy_class": item.get("strategy_class", "OWNER_SUBMITTED_PARAMETER_STACK_STATIC_ONLY"),
        "edge_type": item.get("edge_type", "OWNER_SUBMITTED_EDGE_STATIC_ONLY"),
        "latency_sensitivity_class": item.get("latency_sensitivity_class", "LATENCY_SENSITIVE_STATIC_ONLY"),
        "capital_intensity_class": item.get("capital_intensity_class", "CAPITAL_STATIC_ONLY"),
        "source_dependency_state": fixture.get("source_dependency_state"),
        "required_role_completion_state": item.get("required_role_completion_state", "ROLE_COMPLETE"),
        "compatibility_state": item.get("compatibility_state", "COMPATIBLE_ROLE_TUPLE"),
        "blocker_state": "NONE" if valid else "BLOCKED",
        "blocked_row_ids_and_reasons": [] if valid else [
            {"row_id": selected_stack_id or "UNKNOWN_SELECTED_STACK", "reason_codes": list(block_codes)}
        ],
        "signal_family_ids": copy.deepcopy(item.get("signal_family_ids", [])),
        "scoring_family_ids": copy.deepcopy(item.get("scoring_family_ids", [])),
        "normalization_family_ids": copy.deepcopy(item.get("normalization_family_ids", [])),
        "risk_family_ids": copy.deepcopy(item.get("risk_family_ids", [])),
        "execution_family_ids": copy.deepcopy(item.get("execution_family_ids", [])),
        "capital_family_ids": copy.deepcopy(item.get("capital_family_ids", [])),
        "latency_family_ids": copy.deepcopy(item.get("latency_family_ids", [])),
        "error_guard_family_ids": copy.deepcopy(item.get("error_guard_family_ids", [])),
        "quantum_advisory_family_ids": copy.deepcopy(item.get("quantum_advisory_family_ids", [])),
        "scoring_policy_refs": copy.deepcopy(item.get("scoring_policy_refs", [])),
        "ranking_contract_ref": item.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": item.get("optimizer_arbitration_policy_ref"),
        "quantum_applicability_summary": copy.deepcopy(item.get("quantum_applicability_summary", {})),
        "owner_quantum_priority_summary": copy.deepcopy(item.get("owner_quantum_priority_summary", {})),
        "classical_comparator_required_flag": item.get("classical_comparator_required_flag", True),
        "classical_comparator_ref": item.get("classical_comparator_ref"),
        "quantum_candidate_type": item.get("quantum_candidate_type"),
        "replay_result_packet_ref": fixture.get("replay_result_packet_ref"),
        "paper_result_packet_ref": fixture.get("paper_result_packet_ref"),
        "dual_result_review_state": item.get("review_state"),
        "owner_review_state": owner_review_state,
        "owner_decision_state": owner_decision_state,
        "owner_decision_required_flag": True,
        "owner_decision_created_flag": False,
        "requested_promotion_scope": fixture.get("requested_promotion_scope"),
        "requested_live_scope": fixture.get("requested_live_scope"),
        "requested_canary_scope": fixture.get("requested_canary_scope"),
        "requested_platform_scope": fixture.get("requested_platform_scope"),
        "request_reason_codes": list(fixture.get("request_reason_codes", [])),
        "owner_review_request_id": fixture.get("owner_review_request_id"),
        "owner_review_request_authority_class": OWNER_REVIEW_REQUEST_AUTHORITY_CLASS,
        "requesting_agent_ids": list(fixture.get("requesting_agent_ids", [])),
        "requesting_agent_authority_class": REQUESTING_AGENT_AUTHORITY_CLASS,
        "owner_decision_option_set": list(OWNER_DECISION_OPTION_ORDER),
        "owner_decision_option_authority_class": OWNER_DECISION_OPTION_AUTHORITY_CLASS,
        "owner_review_basis_codes": list(fixture.get("owner_review_basis_codes", [])),
        "owner_review_required_reason_codes": list(
            fixture.get("owner_review_required_reason_codes", [])
        ),
        "blocking_gate_states": [
            gate["gate_state"] for gate in _gate_dependency_matrix() if gate["satisfied_flag"] is False
        ],
        "gate_dependency_matrix": _gate_dependency_matrix(),
        "pr93_queue_forwardable_flag": valid,
        "pr94_receipt_authoring_forwardable_flag": valid,
        "pr95_dashboard_menu_forwardable_flag": valid,
        "pr96_dashboard_screen_forwardable_flag": valid,
        "canary_eligibility_forwardable_flag": False,
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
        "blocked_reason_codes": list(block_codes),
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        review_item[field] = False
    for field in NO_AUTHORITY_TRUE_FIELDS:
        review_item[field] = True
    return review_item


def build_owner_live_promotion_review_parameter_stack_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    del registry
    failures: list[str] = []
    case = _case_by_id(fixture, case_id)
    pr91_packet = copy.deepcopy(upstream.get("dual_result_review_parameter_stack_packet", {}))
    item = _pr91_review_item_for_fixture(upstream, fixture)
    if case.get("missing_pr91_dual_result_review_packet") is True:
        pr91_packet = {}
        item = {}
    lineage = _selected_stack_lineage_trace(item, fixture) if item else []
    block_codes = _block_codes_for_case(item if item else None, fixture, case, lineage)
    valid = len(block_codes) == 0
    owner_item = _owner_review_item(item, fixture, lineage, block_codes=block_codes)
    review_items = [owner_item] if valid else []
    blocked_items = [] if valid else [owner_item]
    allowed_reason_codes = _sort_reason_codes(
        [
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_STATIC_OWNER_REQUEST_ONLY",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR91_DUAL_RESULT_REVIEW_PACKET",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR90_COMPETITION_PACKET_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR89_HANDOFF_PACKET_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR88_SELECTION_PACKET_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR87_CANDIDATE_PACKET_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_TRADE_CONTEXT_ROUTE_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_QUANTUM_POLICY_LINEAGE",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_AGENTS_REQUEST_OWNER_DECIDES",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_OWNER_DECISION_PENDING",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_DECISION_OPTIONS_SCHEMA_ONLY",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_SOURCE_CONNECTOR_RUNTIME_CASH_RISK_ORDER_ROUTER_GATES_REQUIRED",
            "OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PR93_PR96_FORWARDABILITY_ONLY",
        ]
    )
    packet = {
        "owner_live_promotion_review_parameter_stack_packet_id": fixture.get(
            "owner_live_promotion_review_parameter_stack_packet_id"
        ),
        "schema_version": fixture.get("schema_version"),
        "mode": fixture.get("mode"),
        "execution": fixture.get("execution"),
        "semantic_task_id": SEMANTIC_TASK_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "gate_scope": GATE_SCOPE,
        "review_scope": REVIEW_SCOPE,
        "review_authority_class": REVIEW_AUTHORITY_CLASS,
        "owner_review_request_authority_class": OWNER_REVIEW_REQUEST_AUTHORITY_CLASS,
        "requesting_agent_authority_class": REQUESTING_AGENT_AUTHORITY_CLASS,
        "owner_decision_state": (
            fixture.get("owner_decision_state") if valid else "BLOCKED_PENDING_OWNER_DECISION"
        ),
        "owner_decision_option_authority_class": OWNER_DECISION_OPTION_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "review_contract_only_flag": True,
        "source_dependency_state": fixture.get("source_dependency_state"),
        "upstream_dual_result_review_packet_ref": fixture.get("upstream_dual_result_review_packet_ref") if pr91_packet else None,
        "upstream_dual_result_review_packet_digest_or_static_ref": fixture.get(
            "upstream_dual_result_review_packet_digest_or_static_ref"
        ),
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
        "selected_stack_id": owner_item.get("selected_stack_id"),
        "selected_candidate_stack_id": owner_item.get("selected_candidate_stack_id"),
        "selected_candidate_generation_key": owner_item.get("selected_candidate_generation_key"),
        "selected_stack_lineage_trace": copy.deepcopy(lineage),
        "selected_stack_digest_or_static_ref": owner_item.get("selected_stack_digest_or_static_ref"),
        "dual_result_review_item_id": fixture.get("expected_dual_result_review_item_id"),
        "dual_result_comparison_matrix_ref": fixture.get("dual_result_comparison_matrix_ref"),
        "replay_result_packet_ref": fixture.get("replay_result_packet_ref"),
        "paper_result_packet_ref": fixture.get("paper_result_packet_ref"),
        "replay_result_packet_authority_class": fixture.get("replay_result_packet_authority_class"),
        "paper_result_packet_authority_class": fixture.get("paper_result_packet_authority_class"),
        "replay_paper_shared_input_identity_ref": fixture.get("replay_paper_shared_input_identity_ref"),
        "replay_paper_result_separation_preserved_flag": True,
        "upstream_pr91_owner_review_forwardable_flag": item.get("pr92_owner_review_forwardable_flag"),
        "dual_result_review_forwardable_flag": valid,
        "owner_review_request_id": fixture.get("owner_review_request_id"),
        "requesting_agent_ids": list(fixture.get("requesting_agent_ids", [])),
        "owner_decision_created_flag": False,
        "owner_approval_receipt_ref": "STAGE1_OWNER_APPROVAL_RECEIPT_BOUNDARY_STATIC_REF_ONLY",
        "owner_approval_receipt_created_flag": False,
        "owner_override_receipt_ref": "PR94_OWNER_OVERRIDE_RECEIPT_AUTHORING_FUTURE_BOUNDARY_REF_ONLY",
        "owner_override_receipt_created_flag": False,
        "owner_review_basis_codes": list(fixture.get("owner_review_basis_codes", [])),
        "owner_review_required_reason_codes": list(fixture.get("owner_review_required_reason_codes", [])),
        "owner_decision_option_set": list(OWNER_DECISION_OPTION_ORDER),
        "owner_approval_queue_forwardable_flag": valid,
        "pr93_owner_approval_request_queue_required_flag": True,
        "pr93_owner_approval_request_queue_created_flag": False,
        "pr94_owner_override_receipt_authoring_required_flag": True,
        "pr94_owner_override_receipt_created_flag": False,
        "pr95_dashboard_approval_menu_required_flag": True,
        "pr95_dashboard_approval_menu_created_flag": False,
        "pr96_dashboard_approval_static_screen_required_flag": True,
        "pr96_dashboard_approval_static_screen_created_flag": False,
        "source_evidence_gate_state": fixture.get("source_evidence_gate_state"),
        "source_evidence_gate_required_flag": True,
        "source_evidence_gate_satisfied_flag": False,
        "accepted_source_packet_required_flag": True,
        "accepted_source_packet_created_flag": False,
        "connector_semantic_gate_state": fixture.get("connector_semantic_gate_state"),
        "connector_semantic_gate_required_flag": True,
        "connector_semantic_binding_created_flag": False,
        "runtime_cash_gate_state": fixture.get("runtime_cash_gate_state"),
        "runtime_cash_receipt_required_flag": True,
        "runtime_cash_receipt_created_flag": False,
        "risk_gate_state": fixture.get("risk_gate_state"),
        "risk_review_required_flag": True,
        "order_router_gate_state": fixture.get("order_router_gate_state"),
        "order_router_final_authority_preserved_flag": True,
        "live_order_execution_allowed_flag": False,
        "live_routing_allowed_flag": False,
        "canary_eligibility_required_flag": True,
        "canary_eligibility_created_flag": False,
        "live_promotion_created_flag": False,
        "live_trade_authority_created_flag": False,
        "owner_review_items": review_items,
        "blocked_owner_review_items": blocked_items,
        "rejected_owner_review_items": [],
        "review_reason_codes": allowed_reason_codes if valid else list(block_codes),
        "blocked_reason_codes": list(block_codes),
        "gate_dependency_matrix": _gate_dependency_matrix(),
        "dual_result_review_item_count": 1 if pr91_packet and item else 0,
        "owner_review_request_count": 1 if item and not case.get("missing_owner_request_basis") else 0,
        "valid_owner_review_item_count": 1 if valid else 0,
        "blocked_owner_review_item_count": 0 if valid else 1,
        "rejected_owner_review_item_count": 0,
        "pending_owner_decision_count": 1 if valid else 0,
        "source_retrieval_count": 0,
        "source_acceptance_count": 0,
        "connector_binding_count": 0,
        "runtime_cash_receipt_count": 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "order_submission_count": 0,
        "order_authoritative_item_count": 0,
        "owner_approval_receipt_created_count": 0,
        "owner_override_receipt_created_count": 0,
        "live_promotion_created_count": 0,
        "canary_eligibility_created_count": 0,
        "real_optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "order_intent_surface_present_flag": fixture.get("order_intent_surface_present_flag"),
        "order_intent_surface_authority": fixture.get("order_intent_surface_authority"),
        "final_ready": False,
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        packet[field] = False
    for field in NO_AUTHORITY_TRUE_FIELDS:
        packet[field] = True
    if case_id is not None:
        packet["fixture_case_id"] = case_id
        packet["expected_reason_code"] = case.get("expected_reason_code")
    failures.extend(validate_review_packet(packet, upstream))
    return packet, failures


def validate_review_packet(packet: dict[str, Any], upstream: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field, expected in (
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("roadmap_pr_label", ROADMAP_PR_LABEL),
        ("gate_scope", GATE_SCOPE),
        ("review_scope", REVIEW_SCOPE),
        ("review_authority_class", REVIEW_AUTHORITY_CLASS),
        ("owner_review_request_authority_class", OWNER_REVIEW_REQUEST_AUTHORITY_CLASS),
        ("requesting_agent_authority_class", REQUESTING_AGENT_AUTHORITY_CLASS),
        ("owner_decision_option_authority_class", OWNER_DECISION_OPTION_AUTHORITY_CLASS),
    ):
        if packet.get(field) != expected:
            failures.append(f"packet.{field} must be {expected}")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: packet.{field} must be false")
    for field in NO_AUTHORITY_TRUE_FIELDS:
        if packet.get(field) is not True:
            failures.append(f"packet.{field} must be true")
    for field in ZERO_COUNT_FIELDS:
        if packet.get(field) != 0:
            failures.append(f"packet.{field} must be zero")
    if packet.get("owner_decision_option_set") != list(OWNER_DECISION_OPTION_ORDER):
        failures.append("packet.owner_decision_option_set order mismatch")
    if packet.get("replay_result_packet_ref") == packet.get("paper_result_packet_ref"):
        failures.append("replay_result_packet_ref and paper_result_packet_ref must remain separate")
    if packet.get("replay_paper_result_separation_preserved_flag") is not True:
        failures.append("replay_paper_result_separation_preserved_flag must be true")
    valid_count = packet.get("valid_owner_review_item_count")
    blocked_count = packet.get("blocked_owner_review_item_count")
    if valid_count == 1 and blocked_count != 0:
        failures.append("valid packet cannot also have blocked owner review items")
    if valid_count == 0 and blocked_count != 1:
        failures.append("blocked packet must have exactly one blocked owner review item")
    items = _list_of_mappings(packet.get("owner_review_items"))
    blocked_items = _list_of_mappings(packet.get("blocked_owner_review_items"))
    active_items = items if items else blocked_items
    if not active_items:
        failures.append("packet must include owner review or blocked owner review item")
        return failures
    item = active_items[0]
    if items:
        lineage = _list_of_mappings(item.get("selected_stack_lineage_trace"))
        if not _has_required_lineage(lineage):
            failures.append("owner review item must trace selected stack to PR91, PR90, PR89, PR88, and PR87")
        if item.get("owner_decision_state") != "PENDING_OWNER_DECISION":
            failures.append("valid owner review item must remain PENDING_OWNER_DECISION")
        if item.get("owner_decision_created_flag") is not False:
            failures.append("valid owner review item must not create owner decision")
        if item.get("classical_comparator_required_flag") is not True:
            failures.append("quantum-aware owner review item must require classical comparator or fallback")
        if not item.get("classical_comparator_ref"):
            failures.append("quantum-aware owner review item must preserve classical comparator ref")
        if item.get("quantum_applicability_summary", {}).get("backend_execution_created") is not False:
            failures.append("quantum applicability metadata must not create backend execution")
        if item.get("owner_quantum_priority_summary", {}).get("owner_override_external_fact_fabrication_created") is not False:
            failures.append("owner override summary must not fabricate external facts")
        gate_ids = {gate.get("gate_id") for gate in _list_of_mappings(item.get("gate_dependency_matrix"))}
        expected_gate_ids = {
            "SOURCE_EVIDENCE_GATE",
            "ACCEPTED_SOURCE_PACKET_GATE",
            "CONNECTOR_SEMANTIC_GATE",
            "RUNTIME_CASH_GATE",
            "RISK_REVIEW_GATE",
            "ORDER_ROUTER_FINAL_AUTHORITY_GATE",
            "OWNER_DECISION_GATE",
            "DASHBOARD_APPROVAL_GATE",
        }
        if gate_ids != expected_gate_ids:
            failures.append("gate_dependency_matrix must preserve source/connector/runtime/risk/order/owner/dashboard gates")
    pr91_packet = upstream.get("dual_result_review_parameter_stack_packet", {})
    if items and pr91_packet:
        pr91_items = _list_of_mappings(pr91_packet.get("review_items"))
        pr91_ids = {item.get("review_item_id") for item in pr91_items}
        if item.get("dual_result_review_item_id") not in pr91_ids:
            failures.append("owner review item must derive from PR91 dual-result review item")
    return failures


def validate_fixture(
    fixture: dict[str, Any],
    registry: dict[str, Any],
    upstream: dict[str, Any],
) -> tuple[list[str], dict[str, Any], list[dict[str, Any]]]:
    failures: list[str] = []
    for field, expected in (
        ("mode", "SOURCE_REQUIRED"),
        ("execution", "DISABLED"),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("gate_scope", GATE_SCOPE),
        ("review_scope", REVIEW_SCOPE),
        ("review_authority_class", REVIEW_AUTHORITY_CLASS),
        ("owner_review_request_authority_class", OWNER_REVIEW_REQUEST_AUTHORITY_CLASS),
        ("requesting_agent_authority_class", REQUESTING_AGENT_AUTHORITY_CLASS),
        ("owner_decision_state", "PENDING_OWNER_DECISION"),
        ("owner_decision_option_authority_class", OWNER_DECISION_OPTION_AUTHORITY_CLASS),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "review_contract_only_flag",
        *NO_AUTHORITY_TRUE_FIELDS,
    ):
        if fixture.get(field) is not True:
            failures.append(f"fixture.{field} must be true")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if fixture.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: fixture.{field} must be false")

    if fixture.get("owner_decision_option_set") != list(OWNER_DECISION_OPTION_ORDER):
        failures.append("fixture.owner_decision_option_set order mismatch")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = [str(case.get("case_id") or "") for case in cases]
    missing_cases = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing_cases:
        failures.append(f"fixture.fixture_cases missing case IDs {', '.join(missing_cases)}")
    for case in cases:
        code = case.get("expected_reason_code")
        if code not in REASON_CODE_ORDER:
            failures.append(f"fixture case {case.get('case_id')} has unknown expected_reason_code")
        if case.get("synthetic_case_only") is not True:
            failures.append(f"fixture case {case.get('case_id')} must be synthetic_case_only")

    packet, packet_failures = build_owner_live_promotion_review_parameter_stack_packet(
        registry,
        fixture,
        upstream,
    )
    failures.extend(packet_failures)
    for count_field in (
        "expected_dual_result_review_item_count",
        "expected_owner_review_request_count",
        "expected_valid_owner_review_item_count",
        "expected_blocked_owner_review_item_count",
        "expected_rejected_owner_review_item_count",
        "expected_pending_owner_decision_count",
        "expected_owner_approval_receipt_created_count",
        "expected_owner_override_receipt_created_count",
        "expected_live_promotion_created_count",
        "expected_canary_eligibility_created_count",
        "expected_source_retrieval_count",
        "expected_source_acceptance_count",
        "expected_connector_binding_count",
        "expected_runtime_cash_receipt_count",
        "expected_replay_execution_count",
        "expected_paper_execution_count",
        "expected_order_submission_count",
        "expected_order_authoritative_item_count",
    ):
        packet_field = count_field.removeprefix("expected_")
        if packet.get(packet_field) != fixture.get(count_field):
            failures.append(f"packet.{packet_field} must match fixture.{count_field}")

    case_packets: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case.get("case_id"))
        case_packet, case_failures = build_owner_live_promotion_review_parameter_stack_packet(
            registry,
            fixture,
            upstream,
            case_id=case_id,
        )
        failures.extend(case_failures)
        if case_packet.get("valid_owner_review_item_count") != case.get(
            "expected_valid_owner_review_item_count"
        ):
            failures.append(f"fixture case {case_id} valid count mismatch")
        expected_reason = case.get("expected_reason_code")
        all_reason_codes = set(case_packet.get("review_reason_codes", [])) | set(
            case_packet.get("blocked_reason_codes", [])
        )
        if expected_reason not in all_reason_codes:
            failures.append(f"fixture case {case_id} missing expected reason code {expected_reason}")
        case_packets.append(case_packet)
    return failures, packet, case_packets


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    forbidden_paths = (
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalMenu.report.json"),
        pathlib.Path("docs/master_plan/generated/OwnerDashboardApprovalStaticScreen.report.json"),
    )
    for path in forbidden_paths:
        if _resolve(repo_root, path).exists():
            failures.append(f"PR92 must not create later-scope artifact: {path.as_posix()}")
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
            "OWNER_LIVE_PROMOTION_REVIEW_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    return pr91_gate.validate_validator_static_surface(validator_path)


def _boundary_proof_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "agents_may_request": True,
        "agents_may_approve": False,
        "owner_decision_option_schema_created": True,
        "owner_decision_created": packet.get("owner_decision_created_flag"),
        "owner_approval_receipt_created": packet.get("owner_approval_receipt_created_flag"),
        "owner_override_receipt_created": packet.get("owner_override_receipt_created_flag"),
        "live_promotion_created": packet.get("live_promotion_created_flag"),
        "canary_eligibility_created": packet.get("canary_eligibility_created_flag"),
        "pr93_queue_forwardability_metadata_created": True,
        "pr93_queue_registry_created": packet.get("pr93_owner_approval_request_queue_created_flag"),
        "pr94_receipt_forwardability_metadata_created": True,
        "pr94_receipt_authoring_gate_created": packet.get("pr94_owner_override_receipt_created_flag"),
        "pr95_dashboard_menu_forwardability_metadata_created": True,
        "pr95_dashboard_menu_created": packet.get("pr95_dashboard_approval_menu_created_flag"),
        "pr96_dashboard_screen_forwardability_metadata_created": True,
        "pr96_dashboard_screen_created": packet.get("pr96_dashboard_approval_static_screen_created_flag"),
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
    items = _list_of_mappings(packet.get("owner_review_items"))
    item = items[0] if items else {}
    lineage = _list_of_mappings(item.get("selected_stack_lineage_trace"))
    artifact_ids = _lineage_artifact_ids(lineage)
    boundary = _boundary_proof_from_packet(packet)
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "branch": metadata.get("branch"),
        "base_head": metadata.get("base_head"),
        "expected_baseline_ancestor": EXPECTED_BASELINE_ANCESTOR,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "semantic_task_id_source": metadata.get("semantic_task_id_source"),
        "validator_marker": SUCCESS_MARKER,
        "validator_marker_source": metadata.get("validator_marker_source"),
        "owner_live_promotion_review_gate_registry_id": registry.get(
            "owner_live_promotion_review_gate_registry_id"
        ),
        "owner_live_promotion_review_parameter_stack_packet_contract_id": registry.get(
            "owner_live_promotion_review_parameter_stack_packet_contract_id"
        ),
        "gate_scope": registry.get("gate_scope"),
        "review_scope": REVIEW_SCOPE,
        "review_authority_class": REVIEW_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "review_contract_only_flag": True,
        "review_inputs": list(REVIEW_INPUT_ORDER),
        "review_outputs": list(REVIEW_OUTPUT_ORDER),
        "review_policy": copy.deepcopy(registry.get("review_policy")),
        "blocked_review_policy": copy.deepcopy(registry.get("blocked_review_policy")),
        "owner_decision_option_set": list(OWNER_DECISION_OPTION_ORDER),
        "deterministic_review_chain": list(DETERMINISTIC_REVIEW_CHAIN),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "upstream_dependencies": copy.deepcopy(registry.get("upstream_dependencies")),
        "future_consumers": copy.deepcopy(registry.get("future_consumers")),
        "upstream_dual_result_review_packet_ref": copy.deepcopy(
            registry.get("upstream_dual_result_review_packet_ref")
        ),
        "stage1_owner_live_promotion_review_contract_ref": copy.deepcopy(
            registry.get("stage1_owner_live_promotion_review_contract_ref")
        ),
        "stage1_owner_approval_receipt_boundary_ref": copy.deepcopy(
            registry.get("stage1_owner_approval_receipt_boundary_ref")
        ),
        "stage1_three_venue_canary_eligibility_contract_ref": copy.deepcopy(
            registry.get("stage1_three_venue_canary_eligibility_contract_ref")
        ),
        "source_connector_runtime_order_boundary_refs": copy.deepcopy(
            registry.get("source_connector_runtime_order_boundary_refs")
        ),
        "owner_live_promotion_review_parameter_stack_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "dual_result_review_item_count": packet.get("dual_result_review_item_count"),
        "owner_review_request_count": packet.get("owner_review_request_count"),
        "valid_owner_review_item_count": packet.get("valid_owner_review_item_count"),
        "blocked_owner_review_item_count": packet.get("blocked_owner_review_item_count"),
        "rejected_owner_review_item_count": packet.get("rejected_owner_review_item_count"),
        "pending_owner_decision_count": packet.get("pending_owner_decision_count"),
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
        "real_optimizer_execution_count": packet.get("real_optimizer_execution_count"),
        "quantum_backend_execution_count": packet.get("quantum_backend_execution_count"),
        "quantum_simulator_execution_count": packet.get("quantum_simulator_execution_count"),
        "deterministic_static_owner_review": True,
        "no_randomness": True,
        "no_wall_clock_identity": True,
        "owner_review_entries_derived_only_from_pr91_dual_result_review_packet": True,
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
        "trade_context_and_route_lineage_preserved": bool(
            item.get("trade_context_ref") and item.get("routed_selection_universe_ref")
        ),
        "scoring_ranking_arbitration_lineage_preserved": bool(
            item.get("scoring_policy_refs")
            and item.get("ranking_contract_ref")
            and item.get("optimizer_arbitration_policy_ref")
        ),
        "quantum_policy_lineage_preserved": bool(
            item.get("quantum_applicability_summary")
            and item.get("owner_quantum_priority_summary")
        ),
        "stable_selected_stack_id": packet.get("selected_stack_id"),
        "stable_owner_review_packet_id": packet.get(
            "owner_live_promotion_review_parameter_stack_packet_id"
        ),
        "stable_owner_review_item_ids": [
            review_item.get("owner_review_item_id") for review_item in items
        ],
        "owner_decision_state": packet.get("owner_decision_state"),
        "owner_approval_receipt_created": packet.get("owner_approval_receipt_created_flag"),
        "repeated_run_test": True,
        "missing_non_forwardable_pr91_fail_closed_behavior": True,
        "source_connector_runtime_cash_blocker_fail_closed_behavior": True,
        "auto_promotion_approval_fabrication_fail_closed_behavior": True,
        "quantum_metadata_consumed": bool(item.get("quantum_applicability_summary")),
        "owner_quantum_policy_consumed": bool(item.get("owner_quantum_priority_summary")),
        "classical_comparator_or_fallback_preserved": bool(item.get("classical_comparator_ref")),
        "quantum_classical_static_owner_review_metadata": True,
        "backend_execution_count": 0,
        "simulator_execution_count": 0,
        "quantum_advantage_claim_created": False,
        **boundary,
        "order_intent_adjacent_surface_inherited": packet.get("order_intent_surface_present_flag"),
        "order_intent_authority_created": packet.get("order_authority_created_flag"),
        "order_submission_allowed": packet.get("order_submission_allowed_flag"),
        "live_routing_allowed": packet.get("live_routing_allowed_flag"),
        "source_retrieval_acceptance_created": False,
        "accepted_source_packet_created": packet.get("accepted_source_packet_created_flag"),
        "connector_semantic_binding_created": packet.get("connector_semantic_binding_created_flag"),
        "runtime_cash_receipt_created": packet.get("runtime_cash_receipt_created_flag"),
        "replay_execution_created": packet.get("replay_execution_created_flag"),
        "paper_execution_created": packet.get("paper_execution_created_flag"),
        "real_replay_paper_result_created": False,
        "live_order_authority_created": packet.get("order_authority_created_flag"),
        "atomicrows_bundle_jsonl_created": packet.get("atomicrows_bundle_jsonl_created"),
        "atomicrows_bundle_sha256_created": packet.get("atomicrows_bundle_sha256_created"),
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "master_plan_edited": False,
        "final_ready": False,
    }
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

    metadata_failures, metadata = validate_pr92_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_gate_payload(registry, repo_root=repo_root))
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
