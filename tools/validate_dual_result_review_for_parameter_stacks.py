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
from tools import validate_replay_paper_candidate_stack_competition_gate as pr90_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "dual_result_review_for_parameter_stacks.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "DualResultReviewForParameterStacks.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_dual_result_review_for_parameter_stacks.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "DualResultReviewForParameterStacks.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr90_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr90_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr90_gate.MASTER_PLAN_CURRENT

GATE_REGISTRY_ID = "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_GATE"
PACKET_CONTRACT_ID = "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_V1"
REPORT_ID = "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #91"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-DUAL-RESULT-REVIEW-FOR-PARAMETER-STACKS"
TARGET_BRANCH = "pr91-dual-result-review-parameter-stack-gate"
EXPECTED_BASELINE_ANCESTOR = "886916d"
GATE_SCOPE = "STATIC_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_ONLY"
REVIEW_SCOPE = "STATIC_ONLY"
REVIEW_AUTHORITY_CLASS = (
    "STATIC_DUAL_RESULT_REVIEW_NOT_REPLAY_EXECUTION_NOT_PAPER_EXECUTION_"
    "NOT_LIVE_PROMOTION_NOT_ORDER_AUTHORITY"
)
SYNTHETIC_FIXTURE_AUTHORITY_CLASS = (
    "STATIC_SYNTHETIC_SCHEMA_VALIDATION_ONLY_NOT_EXECUTION_NOT_EVIDENCE"
)
ORDER_INTENT_PREVIEW_AUTHORITY = pr90_gate.ORDER_INTENT_PREVIEW_AUTHORITY
SUCCESS_MARKER = "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_OK"
FAILURE_MARKER = "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr90_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr90_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr90_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)
REPAIR_BRANCH_PREFIX = ci_branch_context.REPAIR_BRANCH_PREFIX

ROLE_ORDER = pr90_gate.ROLE_ORDER
DEPENDENCY_ORDER = pr90_gate.DEPENDENCY_ORDER + (
    "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
)
DEPENDENCY_MARKERS = {
    **pr90_gate.DEPENDENCY_MARKERS,
    "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE": pr90_gate.SUCCESS_MARKER,
}
STAGE1_STATIC_CONTRACT_REPORTS = pr90_gate.STAGE1_STATIC_CONTRACT_REPORTS
FUTURE_CONSUMER_ORDER = (
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
    "PR105_PR151_STAGE1_RUNTIME_LIVE_LAUNCH_CLOSURE_CONSUMERS",
)
REVIEW_INPUT_ORDER = (
    "PR90_static_replay_paper_candidate_stack_competition_packet",
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
    "Stage1_concurrent_replay_paper_input_identity_static_contract",
    "Stage1_replay_result_packet_boundary_static_ref_only",
    "Stage1_paper_result_packet_boundary_static_ref_only",
    "Stage1_dual_result_review_input_contract_static_ref_only",
    "Stage1_replay_paper_comparison_matrix_static_ref_only",
)
REVIEW_OUTPUT_ORDER = (
    "static_dual_result_review_parameter_stack_packet",
    "static_review_item_descriptors",
    "static_synthetic_replay_result_packet_shape_refs_only",
    "static_synthetic_paper_result_packet_shape_refs_only",
    "static_comparison_matrix_descriptor",
    "static_fail_closed_review_case_packets",
    "pr92_owner_review_forwardability_metadata_no_review_created",
    "no_replay_execution_boundary",
    "no_paper_execution_boundary",
    "no_real_result_packet_boundary",
    "no_order_authority_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "no_profit_evidence_boundary",
)
DETERMINISTIC_REVIEW_CHAIN = (
    "PR90_competition_packet_required",
    "PR90_competition_entry_required",
    "selected_stack_lineage_to_PR90_PR89_PR88_PR87_required",
    "trade_context_and_routed_selection_universe_lineage_required",
    "role_completion_and_compatibility_required",
    "blocked_rows_absent",
    "source_dependency_state_static_only",
    "scoring_ranking_arbitration_lineage_required",
    "quantum_policy_lineage_with_classical_comparator_or_fallback",
    "owner_override_internal_basis_only_when_recorded",
    "separate_replay_and_paper_result_packet_refs_required",
    "shared_input_identity_required",
    "runtime_resolver_snapshot_input_lock_and_owner_policy_snapshot_required",
    "synthetic_result_fixtures_schema_validation_only_not_evidence",
    "comparison_matrix_refs_only_no_metric_values",
    "no_result_merge_overwrite_collapse",
    "pass_route_only_to_pr92_owner_review_required_not_created",
    "lexicographic_review_packet_and_item_ids",
)
REASON_CODE_ORDER = (
    "DUAL_RESULT_REVIEW_ALLOWED_STATIC_SYNTHETIC_SCHEMA_VALIDATION_ONLY",
    "DUAL_RESULT_REVIEW_ALLOWED_PR90_COMPETITION_PACKET",
    "DUAL_RESULT_REVIEW_ALLOWED_PR89_HANDOFF_PACKET_LINEAGE",
    "DUAL_RESULT_REVIEW_ALLOWED_PR88_SELECTION_PACKET_LINEAGE",
    "DUAL_RESULT_REVIEW_ALLOWED_PR87_CANDIDATE_PACKET_LINEAGE",
    "DUAL_RESULT_REVIEW_ALLOWED_TRADE_CONTEXT_ROUTE_LINEAGE",
    "DUAL_RESULT_REVIEW_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE",
    "DUAL_RESULT_REVIEW_ALLOWED_QUANTUM_POLICY_LINEAGE",
    "DUAL_RESULT_REVIEW_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
    "DUAL_RESULT_REVIEW_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
    "DUAL_RESULT_REVIEW_ALLOWED_SEPARATE_REPLAY_AND_PAPER_RESULT_REFS",
    "DUAL_RESULT_REVIEW_ALLOWED_SHARED_INPUT_IDENTITY_MATCH",
    "DUAL_RESULT_REVIEW_ALLOWED_RUNTIME_RESOLVER_INPUT_LOCK_OWNER_POLICY_MATCH",
    "DUAL_RESULT_REVIEW_ALLOWED_SYNTHETIC_RESULT_FIXTURE_NOT_EVIDENCE",
    "DUAL_RESULT_REVIEW_ALLOWED_COMPARISON_MATRIX_STATIC_METADATA_ONLY",
    "DUAL_RESULT_REVIEW_ALLOWED_PR92_BOUNDARY_NO_OWNER_REVIEW_CREATED",
    "DUAL_RESULT_REVIEW_ALLOWED_NEGATIVE_ROUTE_STATIC_ONLY",
    "DUAL_RESULT_REVIEW_ALLOWED_AMBIGUOUS_ROUTE_STATIC_ONLY",
    "DUAL_RESULT_REVIEW_ALLOWED_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
    "DUAL_RESULT_REVIEW_BLOCKED_PENDING_REAL_RESULTS",
    "DUAL_RESULT_REVIEW_BLOCKED_MISSING_PR90_COMPETITION_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_MISSING_COMPETITION_ENTRY",
    "DUAL_RESULT_REVIEW_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR90_PR89_PR88_PR87",
    "DUAL_RESULT_REVIEW_BLOCKED_MISSING_REPLAY_RESULT_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_MISSING_PAPER_RESULT_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_SHARED_INPUT_IDENTITY_MISMATCH",
    "DUAL_RESULT_REVIEW_BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_MISMATCH",
    "DUAL_RESULT_REVIEW_BLOCKED_INPUT_LOCK_MISMATCH",
    "DUAL_RESULT_REVIEW_BLOCKED_OWNER_POLICY_SNAPSHOT_MISMATCH",
    "DUAL_RESULT_REVIEW_BLOCKED_STALE_REPLAY_RESULT_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_STALE_PAPER_RESULT_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_INVALID_REPLAY_RESULT_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_INVALID_PAPER_RESULT_PACKET",
    "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_RESULT_SEPARATION_VIOLATION",
    "DUAL_RESULT_REVIEW_BLOCKED_RESULT_MERGE_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_RESULT_OVERWRITE_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_RESULT_COLLAPSE_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_OWNER_APPROVAL_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_BLOCKER_REDUCTION_FORBIDDEN",
    "DUAL_RESULT_REVIEW_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR91_METADATA_VERIFIED",
    "PASS_VALID_STATIC_DUAL_RESULT_REVIEW_SCHEMA_FIXTURE",
    "PASS_COMPETITION_LINEAGE_TO_PR90_PR89_PR88_PR87",
    "PASS_SAME_SHARED_INPUT_IDENTITY_ACCEPTED",
    "BLOCK_REPLAY_PAPER_INPUT_IDENTITY_MISMATCH",
    "BLOCK_RUNTIME_RESOLVER_SNAPSHOT_MISMATCH",
    "BLOCK_INPUT_LOCK_MISMATCH",
    "BLOCK_OWNER_POLICY_SNAPSHOT_MISMATCH",
    "BLOCK_MISSING_REPLAY_RESULT_PACKET",
    "BLOCK_MISSING_PAPER_RESULT_PACKET",
    "BLOCK_STALE_REPLAY_RESULT_PACKET",
    "BLOCK_STALE_PAPER_RESULT_PACKET",
    "BLOCK_INVALID_REPLAY_RESULT_PACKET",
    "BLOCK_INVALID_PAPER_RESULT_PACKET",
    "BLOCK_REPLAY_PAPER_RESULT_MERGE",
    "BLOCK_REPLAY_PAPER_RESULT_OVERWRITE",
    "BLOCK_REPLAY_PAPER_RESULT_COLLAPSE",
    "PASS_NEGATIVE_ROUTE_STATIC_ONLY",
    "PASS_AMBIGUOUS_ROUTE_STATIC_ONLY",
    "PASS_QUANTUM_AWARE_WITH_CLASSICAL_COMPARATOR",
    "PASS_QUANTUM_CLASSICAL_STATIC_COMPARISON_METADATA_ONLY",
    "PASS_OWNER_THRESHOLD_POLICY_REF_NO_APPROVAL",
    "PASS_OWNER_OVERRIDE_INTERNAL_BASIS",
    "PASS_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
    "BLOCK_LIVE_PROMOTION_ATTEMPT",
    "BLOCK_OWNER_APPROVAL_ATTEMPT",
    "BLOCK_CANARY_ELIGIBILITY_ATTEMPT",
    "BLOCK_EXECUTABLE_ORDER_INTENT_ATTEMPT",
    "BLOCK_ORDER_AUTHORITY_ATTEMPT",
    "BLOCK_RUNTIME_CASH_CLAIM",
    "BLOCK_ATOMICROWS_BUNDLE_ATTEMPT",
    "BLOCK_BLOCKER_REDUCTION_CLAIM",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "PASS_PR92_BOUNDARY_REQUIRED_NOT_CREATED",
)

NO_AUTHORITY_FALSE_FIELDS = (
    "source_retrieval_created_flag",
    "source_acceptance_created_flag",
    "connector_semantic_binding_created_flag",
    "runtime_cash_receipt_created_flag",
    "live_trade_authority_created_flag",
    "order_intent_authority_created",
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
    "owner_live_promotion_review_created_flag",
    "pr92_owner_live_promotion_review_created_flag",
    "owner_approval_created_flag",
    "canary_eligibility_created_flag",
    "live_promotion_created_flag",
    "classical_optimizer_execution_created_flag",
    "quantum_optimizer_execution_created_flag",
    "optimizer_execution_created_flag",
    "quantum_backend_execution_created_flag",
    "quantum_simulator_execution_created_flag",
    "profit_evidence_created_flag",
    "quantum_advantage_claim_created_flag",
    "latency_superiority_claim_created_flag",
    "execution_superiority_claim_created_flag",
    "random_identity_used",
    "wall_clock_identity_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "blocker_reduction_claim_created_flag",
)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_cash_receipt_created",
    "private_state_fetch_created",
    "replay_execution_created",
    "paper_execution_created",
    "real_replay_result_packet_created",
    "real_paper_result_packet_created",
    "replay_result_packet_created",
    "paper_result_packet_created",
    "result_values_created",
    "owner_live_promotion_review_created",
    "owner_approval_created",
    "canary_eligibility_created",
    "live_promotion_created",
    "order_submission_created",
    "order_cancellation_created",
    "fill_receipt_created",
    "classical_optimizer_execution_created",
    "quantum_optimizer_execution_created",
    "optimizer_execution_created",
    "backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "profit_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "dual_result_review_packet_is_executable_order_intent",
    "dual_result_review_packet_is_live_order_authority",
    "synthetic_result_fixture_is_real_evidence",
    "comparison_matrix_creates_live_authority",
    "pr92_owner_review_created",
)
FIELD_REASON_CODES = {
    "source_retrieval_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "source_acceptance_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "connector_semantic_binding_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN",
    "live_trade_authority_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "order_intent_authority_created": "DUAL_RESULT_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "executable_order_intent_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
    "order_authority_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "order_submission_allowed_flag": "DUAL_RESULT_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "live_routing_allowed_flag": "DUAL_RESULT_REVIEW_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "connector_binding_allowed_flag": "DUAL_RESULT_REVIEW_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "replay_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "paper_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "real_replay_result_packet_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "real_paper_result_packet_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "result_values_created_from_execution_flag": "DUAL_RESULT_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "owner_live_promotion_review_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_FORBIDDEN",
    "pr92_owner_live_promotion_review_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_OWNER_LIVE_PROMOTION_REVIEW_FORBIDDEN",
    "owner_approval_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_OWNER_APPROVAL_FORBIDDEN",
    "canary_eligibility_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN",
    "live_promotion_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "classical_optimizer_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_backend_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "profit_evidence_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "execution_superiority_claim_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "random_identity_used": "DUAL_RESULT_REVIEW_BLOCKED_SHARED_INPUT_IDENTITY_MISMATCH",
    "wall_clock_identity_used": "DUAL_RESULT_REVIEW_BLOCKED_SHARED_INPUT_IDENTITY_MISMATCH",
    "atomicrows_bundle_jsonl_created": "DUAL_RESULT_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "DUAL_RESULT_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "blocker_reduction_claim_created_flag": "DUAL_RESULT_REVIEW_BLOCKED_BLOCKER_REDUCTION_FORBIDDEN",
}
SOURCE_ALLOWED_STATES = {"STATIC_SOURCE_DEPENDENCY_LABELS_ONLY"}
REQUIRED_MASTER_PLAN_PRINCIPLES = {
    "REPLAY_AND_PAPER_MUST_EMIT_SEPARATE_RESULT_PACKETS",
    "DUAL_RESULT_REVIEW_REFERENCES_BOTH_LANES_WITHOUT_MERGE",
    "DUAL_RESULT_REVIEW_REQUIRES_MATCHING_SHARED_INPUT_IDENTITY",
    "DUAL_RESULT_REVIEW_REQUIRES_MATCHING_RUNTIME_SNAPSHOT_INPUT_LOCK_OWNER_POLICY",
    "DUAL_RESULT_REVIEW_NON_LIVE_ROUTE_STATES_ONLY",
    "PASS_STATE_ROUTES_ONLY_TO_OWNER_LIVE_PROMOTION_REVIEW_REQUIRED",
    "NO_AUTOMATIC_LIVE_PROMOTION_OR_OWNER_APPROVAL",
    "ATOMICROWS_INVENTORY_NOT_TRADER",
    "NO_SINGLE_PARAMETER_OR_ALGORITHM_STACKS",
    "MINIMUM_REQUIRED_STACK_ROLES",
    "BLOCKED_ROWS_EXCLUDED_FROM_ACTIVE_STACKS_HANDOFF_COMPETITION_AND_REVIEW",
    "QUANTUM_RANK_REFINE_ONLY_NO_DIRECT_LIVE_AUTHORITY",
    "CLASSICAL_EXECUTION_GATES_AND_EXECUTION_ROUTER_REMAIN_FINAL",
    "SOURCE_CONNECTOR_CASH_ORDER_FACTS_REQUIRE_ACCEPTED_OR_RUNTIME_RECEIPTS",
    "NO_FABRICATION_BOUNDARY",
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
    return pr90_gate.load_yaml(path)


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
    return ci_branch_context.is_downstream_or_main_validation_branch(branch, after_pr=91)


def validate_pr91_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 91), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 91), None)
    if roadmap_entry is None:
        failures.append("PR91 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR91 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Dual-result review for parameter stacks"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Dual-result review for parameter stacks"),
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
        failures.append("upstream_dependencies must preserve PR77-PR90 dependency order")
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


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumer_ids = [
        item.get("consumer_id") for item in _list_of_mappings(payload.get("future_consumers"))
    ]
    if consumer_ids != list(FUTURE_CONSUMER_ORDER):
        failures.append("future_consumers must preserve PR92 then runtime/live order")
    for item in _list_of_mappings(payload.get("future_consumers")):
        if item.get("pr91_creates_consumer_execution") is not False:
            failures.append(f"{item.get('consumer_id')} must not create consumer execution")
    return failures


def validate_review_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = payload.get("review_policy")
    if not isinstance(policy, dict):
        return ["review_policy must be an object"]
    true_fields = (
        "stable_sort_required",
        "review_items_derive_only_from_pr90_competition_packet",
        "selected_stack_lineage_to_pr90_pr89_pr88_pr87_required",
        "replay_result_packet_ref_required_for_schema_fixture",
        "paper_result_packet_ref_required_for_schema_fixture",
        "replay_and_paper_result_refs_must_be_distinct",
        "shared_input_identity_match_required",
        "runtime_resolver_snapshot_match_required",
        "input_lock_match_required",
        "owner_policy_snapshot_match_required",
        "synthetic_result_fixtures_are_not_evidence",
        "quantum_candidates_require_classical_comparator_or_fallback",
    )
    false_fields = (
        "random_identity_allowed",
        "wall_clock_identity_allowed",
        "comparison_metric_values_real_allowed",
        "result_merge_allowed",
        "result_overwrite_allowed",
        "result_collapse_allowed",
        "pr92_owner_live_promotion_review_created",
        "owner_approval_created",
        "live_promotion_created",
        "order_submission_allowed",
        "live_routing_allowed",
        "connector_binding_allowed",
    )
    for field in true_fields:
        if policy.get(field) is not True:
            failures.append(f"review_policy.{field} must be true")
    for field in false_fields:
        if policy.get(field) is not False:
            failures.append(f"review_policy.{field} must be false")
    if policy.get("pass_route_next_required_state") != "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED":
        failures.append("review_policy.pass_route_next_required_state must be OWNER_LIVE_PROMOTION_REVIEW_REQUIRED")
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
    if policy.get("blocked_items_enter_active_review_status") is not False:
        failures.append("blocked_review_policy.blocked_items_enter_active_review_status must be false")
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
        ("dual_result_review_gate_registry_id", GATE_REGISTRY_ID),
        ("dual_result_review_parameter_stack_packet_contract_id", PACKET_CONTRACT_ID),
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
    pr90_upstream_failures, pr90_upstream = pr90_gate.validate_upstream_reports(repo_root)
    failures.extend(pr90_upstream_failures)

    pr90_report, pr90_failures = _load_json_checked(
        repo_root / pr90_gate.DEFAULT_REPORT,
        "PR90_REPORT",
    )
    failures.extend(pr90_failures)
    failures.extend(_validate_report_marker(pr90_report, pr90_gate.SUCCESS_MARKER, "PR90"))
    stage1_reports: dict[str, dict[str, Any]] = {}
    for artifact_id, path, report_type in STAGE1_STATIC_CONTRACT_REPORTS:
        report, report_failures = _load_json_checked(repo_root / path, artifact_id)
        failures.extend(report_failures)
        if report is None:
            continue
        if report.get("report_type") != report_type:
            failures.append(f"{artifact_id} report_type must be {report_type}")
        if report.get("created_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
            failures.append(f"{artifact_id} must be static deterministic")
        stage1_reports[artifact_id] = report
    if pr90_report is None:
        return failures, {}

    competition_packet = pr90_report.get("replay_paper_candidate_stack_competition_packet")
    if not isinstance(competition_packet, dict):
        failures.append("PR90 report replay_paper_candidate_stack_competition_packet missing")
        competition_packet = {}
    competition_entries = _list_of_mappings(competition_packet.get("competition_entries"))
    return failures, {
        **pr90_upstream,
        "pr90_report": pr90_report,
        "replay_paper_candidate_stack_competition_packet": competition_packet,
        "competition_entries": competition_entries,
        "competition_entries_by_id": _first_by_key(competition_entries, "competition_entry_id"),
        "competition_entries_by_stack_id": _first_by_key(competition_entries, "selected_stack_id"),
        "stage1_static_contract_reports": stage1_reports,
    }


def _case_by_id(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        if case.get("case_id") == case_id:
            return case
    raise ValueError(f"unknown fixture case_id {case_id}")


def _competition_entry_for_fixture(
    upstream: dict[str, Any], fixture: dict[str, Any]
) -> dict[str, Any] | None:
    selected_stack_id = fixture.get("expected_selected_stack_id")
    if not isinstance(selected_stack_id, str):
        return None
    return copy.deepcopy(upstream.get("competition_entries_by_stack_id", {}).get(selected_stack_id))


def _selected_stack_lineage_trace(
    entry: dict[str, Any],
    competition_packet: dict[str, Any],
    fixture: dict[str, Any],
) -> list[dict[str, Any]]:
    lineage = [
        {
            "artifact_id": "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
            "artifact_ref": fixture.get("upstream_replay_paper_competition_packet_ref"),
            "validation_marker": pr90_gate.SUCCESS_MARKER,
        },
        {
            "artifact_id": "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
            "artifact_ref": fixture.get("upstream_selected_stack_handoff_packet_ref"),
            "validation_marker": pr90_gate.pr89_gate.SUCCESS_MARKER,
        },
    ]
    for step in _list_of_mappings(entry.get("selected_stack_lineage_trace")):
        lineage.append(copy.deepcopy(step))
    if not any(step.get("artifact_id") == "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE" for step in lineage):
        lineage.append(
            {
                "artifact_id": "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
                "artifact_ref": fixture.get("upstream_trade_context_selection_packet_ref"),
                "validation_marker": pr90_gate.pr89_gate.pr88_gate.SUCCESS_MARKER,
            }
        )
    if not any(step.get("artifact_id") == "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE" for step in lineage):
        lineage.append(
            {
                "artifact_id": "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
                "artifact_ref": fixture.get("upstream_candidate_generation_packet_ref"),
                "validation_marker": pr90_gate.pr89_gate.pr88_gate.pr87_gate.SUCCESS_MARKER,
            }
        )
    if not any(step.get("artifact_id") == "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE" for step in lineage):
        lineage.append(
            {
                "artifact_id": "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE",
                "artifact_ref": competition_packet.get("upstream_routed_selection_universe_ref"),
                "validation_marker": "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK",
            }
        )
    return lineage


def _has_required_lineage(lineage: list[dict[str, Any]]) -> bool:
    artifact_ids = {str(step.get("artifact_id") or "") for step in lineage}
    return {
        "PR90_QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
        "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
        "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
        "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
        "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE",
    }.issubset(artifact_ids)


def _block_codes_for_case(
    entry: dict[str, Any] | None,
    competition_packet: dict[str, Any],
    fixture: dict[str, Any],
    case: dict[str, Any] | None,
    lineage: list[dict[str, Any]],
) -> list[str]:
    block_codes: list[str] = []
    if not competition_packet:
        block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_MISSING_PR90_COMPETITION_PACKET")
    if entry is None:
        block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_MISSING_COMPETITION_ENTRY")
        return _sort_reason_codes(block_codes)
    if not _has_required_lineage(lineage):
        block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR90_PR89_PR88_PR87")
    if entry.get("source_dependency_state") not in SOURCE_ALLOWED_STATES:
        block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_MISSING_COMPETITION_ENTRY")
    if entry.get("quantum_candidate_type") != "CLASSICAL_ONLY" and not entry.get("classical_comparator_ref"):
        block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_MISSING_COMPETITION_ENTRY")
    if case is not None:
        if case.get("missing_replay_result_packet") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_MISSING_REPLAY_RESULT_PACKET")
        if case.get("missing_paper_result_packet") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_MISSING_PAPER_RESULT_PACKET")
        if case.get("shared_input_identity_mismatch") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_SHARED_INPUT_IDENTITY_MISMATCH")
        if case.get("runtime_resolver_snapshot_mismatch") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_MISMATCH")
        if case.get("input_lock_mismatch") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_INPUT_LOCK_MISMATCH")
        if case.get("owner_policy_snapshot_mismatch") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_OWNER_POLICY_SNAPSHOT_MISMATCH")
        if case.get("stale_replay_result_packet") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_STALE_REPLAY_RESULT_PACKET")
        if case.get("stale_paper_result_packet") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_STALE_PAPER_RESULT_PACKET")
        if case.get("invalid_replay_result_packet") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_INVALID_REPLAY_RESULT_PACKET")
        if case.get("invalid_paper_result_packet") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_INVALID_PAPER_RESULT_PACKET")
        if case.get("result_merge_detected") is True:
            block_codes.extend(
                [
                    "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_RESULT_SEPARATION_VIOLATION",
                    "DUAL_RESULT_REVIEW_BLOCKED_RESULT_MERGE_FORBIDDEN",
                ]
            )
        if case.get("result_overwrite_detected") is True:
            block_codes.extend(
                [
                    "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_RESULT_SEPARATION_VIOLATION",
                    "DUAL_RESULT_REVIEW_BLOCKED_RESULT_OVERWRITE_FORBIDDEN",
                ]
            )
        if case.get("result_collapse_detected") is True:
            block_codes.extend(
                [
                    "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_RESULT_SEPARATION_VIOLATION",
                    "DUAL_RESULT_REVIEW_BLOCKED_RESULT_COLLAPSE_FORBIDDEN",
                ]
            )
        if case.get("live_promotion_attempt") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_LIVE_PROMOTION_FORBIDDEN")
        if case.get("owner_approval_attempt") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_OWNER_APPROVAL_FORBIDDEN")
        if case.get("canary_eligibility_attempt") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_CANARY_ELIGIBILITY_FORBIDDEN")
        if case.get("executable_order_intent_attempt") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN")
        if case.get("order_authority_attempt") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_ORDER_AUTHORITY_FORBIDDEN")
        if case.get("runtime_cash_claim") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_RUNTIME_CASH_FORBIDDEN")
        if case.get("atomicrows_bundle_attempt") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN")
        if case.get("blocker_reduction_claim") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_BLOCKER_REDUCTION_FORBIDDEN")
        if case.get("profit_evidence_claim") is True:
            block_codes.append("DUAL_RESULT_REVIEW_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN")
    return _sort_reason_codes(block_codes)


def _identity_material(
    entry: dict[str, Any],
    competition_packet: dict[str, Any],
    fixture: dict[str, Any],
) -> dict[str, str]:
    selected_stack_id = str(entry.get("selected_stack_id") or fixture.get("expected_selected_stack_id"))
    input_lock_id = str(
        competition_packet.get("replay_paper_input_lock_id")
        or f"PR91_STATIC_REPLAY_PAPER_INPUT_LOCK__{selected_stack_id}"
    )
    shared_identity = str(
        competition_packet.get("replay_paper_input_identity_digest_or_static_ref")
        or _digest(("PR91_SHARED_INPUT_IDENTITY", selected_stack_id, input_lock_id))
    )
    runtime_snapshot_ref = f"PR91_STATIC_RUNTIME_RESOLVER_SNAPSHOT_REF__{selected_stack_id}"
    owner_policy_snapshot_ref = str(fixture.get("owner_policy_snapshot_ref"))
    owner_policy_snapshot_digest = _digest((owner_policy_snapshot_ref, input_lock_id, shared_identity))
    return {
        "selected_stack_id": selected_stack_id,
        "input_lock_id": input_lock_id,
        "shared_identity": shared_identity,
        "runtime_snapshot_ref": runtime_snapshot_ref,
        "runtime_snapshot_digest": _digest((runtime_snapshot_ref, input_lock_id)),
        "owner_policy_snapshot_ref": owner_policy_snapshot_ref,
        "owner_policy_snapshot_digest": owner_policy_snapshot_digest,
    }


def _result_packet_shape(
    *,
    lane: str,
    entry: dict[str, Any],
    fixture: dict[str, Any],
    identity: dict[str, str],
    packet_ref: str | None,
    validity_state: str,
) -> dict[str, Any]:
    lane_upper = lane.upper()
    return {
        f"{lane}_result_packet_ref": packet_ref,
        "result_packet_shape_type": f"PR91_STATIC_SYNTHETIC_{lane_upper}_RESULT_PACKET_SHAPE_ONLY",
        "selected_stack_id": entry.get("selected_stack_id"),
        "competition_entry_id": entry.get("competition_entry_id"),
        "authority_class": SYNTHETIC_FIXTURE_AUTHORITY_CLASS,
        "synthetic_fixture_flag": True,
        "static_schema_validation_only_flag": True,
        "not_execution_evidence_flag": True,
        "not_profit_evidence_flag": True,
        "not_replay_or_paper_pass_fail_proof_flag": True,
        "validity_state": validity_state,
        "replay_paper_input_lock_id": identity["input_lock_id"],
        "replay_paper_input_identity_digest_or_static_ref": identity["shared_identity"],
        "runtime_resolver_snapshot_ref": identity["runtime_snapshot_ref"],
        "runtime_resolver_snapshot_digest": identity["runtime_snapshot_digest"],
        "owner_policy_snapshot_ref": identity["owner_policy_snapshot_ref"],
        "owner_policy_snapshot_digest": identity["owner_policy_snapshot_digest"],
        "metric_values_created_from_execution_flag": False,
        "result_values_created_from_execution_flag": False,
        "real_result_packet_created_flag": False,
    }


def _comparison_matrix(
    entry: dict[str, Any],
    fixture: dict[str, Any],
    identity: dict[str, str],
    replay_ref: str | None,
    paper_ref: str | None,
) -> dict[str, Any]:
    matrix_id = f"PR91_COMPARISON_MATRIX__{entry.get('selected_stack_id')}"
    metric_fields = list(fixture.get("comparison_metric_fields_declared", []))
    metric_pair_records = [
        {
            "metric_pair_id": f"PR91_METRIC_PAIR__{field}",
            "metric_field": field,
            "replay_metric_ref": f"{replay_ref}#{field}" if replay_ref else None,
            "paper_metric_ref": f"{paper_ref}#{field}" if paper_ref else None,
            "metric_value_real_flag": False,
            "metric_merge_allowed_flag": False,
            "metric_overwrite_allowed_flag": False,
            "metric_collapse_allowed_flag": False,
            "metric_average_for_promotion_allowed_flag": False,
            "static_comparison_only_flag": True,
        }
        for field in metric_fields
    ]
    return {
        "comparison_matrix_id": matrix_id,
        "comparison_matrix_digest_or_static_ref": _digest(
            (matrix_id, entry.get("competition_entry_id"), replay_ref, paper_ref, metric_fields)
        ),
        "record_authority_class": (
            "STATIC_REPLAY_PAPER_COMPARISON_MATRIX_ONLY_NOT_RESULT_MERGE_NOT_PROMOTION_AUTHORITY"
        ),
        "selected_stack_id": entry.get("selected_stack_id"),
        "competition_entry_id": entry.get("competition_entry_id"),
        "replay_result_packet_ref": replay_ref,
        "paper_result_packet_ref": paper_ref,
        "replay_paper_input_identity_digest_or_static_ref": identity["shared_identity"],
        "comparison_metric_fields_declared": metric_fields,
        "comparison_metric_values_real_flag": False,
        "metric_pair_records": metric_pair_records,
        "net_profit_review_supported_flag": True,
        "latency_review_supported_flag": True,
        "risk_review_supported_flag": True,
        "quantum_vs_classical_review_supported_flag": True,
        "negative_lane_metrics_preserved_flag": True,
        "result_merge_allowed_flag": False,
        "result_overwrite_allowed_flag": False,
        "result_collapse_allowed_flag": False,
        "live_authority_created_flag": False,
        "profit_evidence_created_flag": False,
    }


def _review_item(
    entry: dict[str, Any],
    fixture: dict[str, Any],
    competition_packet: dict[str, Any],
    identity: dict[str, str],
    lineage: list[dict[str, Any]],
    replay_ref: str | None,
    paper_ref: str | None,
    review_state: str,
    routing_state: str,
    valid: bool,
    case: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "review_item_id": f"PR91_REVIEW_ITEM__{entry.get('selected_stack_id')}",
        "selected_stack_id": entry.get("selected_stack_id"),
        "selected_candidate_stack_id": entry.get("selected_candidate_stack_id"),
        "competition_entry_id": entry.get("competition_entry_id"),
        "selected_by_pr88_packet_ref": entry.get("selected_by_pr88_packet_ref"),
        "handoff_by_pr89_packet_ref": entry.get("handoff_by_pr89_packet_ref"),
        "competition_by_pr90_packet_ref": fixture.get("upstream_replay_paper_competition_packet_ref"),
        "candidate_from_pr87_packet_ref": entry.get("candidate_from_pr87_packet_ref"),
        "trade_context_ref": entry.get("trade_context_ref"),
        "routed_selection_universe_ref": entry.get("routed_selection_universe_ref"),
        "venue_scope": entry.get("venue_scope"),
        "platform_scope": entry.get("platform_scope"),
        "market_type": entry.get("market_type"),
        "strategy_class": entry.get("strategy_class"),
        "edge_type": entry.get("edge_type"),
        "latency_sensitivity_class": entry.get("latency_sensitivity_class"),
        "capital_intensity_class": entry.get("capital_intensity_class"),
        "source_dependency_state": entry.get("source_dependency_state"),
        "required_role_completion_state": entry.get("required_role_completion_state"),
        "compatibility_state": entry.get("compatibility_state"),
        "blocker_state": entry.get("blocker_state"),
        "blocked_row_ids_and_reasons": copy.deepcopy(entry.get("blocked_row_ids_and_reasons", [])),
        "signal_family_ids": copy.deepcopy(entry.get("signal_family_ids", [])),
        "scoring_family_ids": copy.deepcopy(entry.get("scoring_family_ids", [])),
        "normalization_family_ids": copy.deepcopy(entry.get("normalization_family_ids", [])),
        "risk_family_ids": copy.deepcopy(entry.get("risk_family_ids", [])),
        "execution_family_ids": copy.deepcopy(entry.get("execution_family_ids", [])),
        "capital_family_ids": copy.deepcopy(entry.get("capital_family_ids", [])),
        "latency_family_ids": copy.deepcopy(entry.get("latency_family_ids", [])),
        "error_guard_family_ids": copy.deepcopy(entry.get("error_guard_family_ids", [])),
        "quantum_advisory_family_ids": copy.deepcopy(entry.get("quantum_advisory_family_ids", [])),
        "scoring_policy_refs": copy.deepcopy(entry.get("scoring_policy_refs", [])),
        "ranking_contract_ref": entry.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": entry.get("optimizer_arbitration_policy_ref"),
        "quantum_applicability_summary": copy.deepcopy(entry.get("quantum_applicability_summary", {})),
        "owner_quantum_priority_summary": copy.deepcopy(entry.get("owner_quantum_priority_summary", {})),
        "classical_comparator_required_flag": entry.get("classical_comparator_required_flag"),
        "classical_comparator_ref": entry.get("classical_comparator_ref"),
        "quantum_candidate_type": entry.get("quantum_candidate_type"),
        "selected_stack_lineage_trace": lineage,
        "replay_result_packet_ref": replay_ref,
        "paper_result_packet_ref": paper_ref,
        "replay_result_packet_validity_state": (
            "PRESENT_VALID_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY" if replay_ref else "MISSING"
        ),
        "paper_result_packet_validity_state": (
            "PRESENT_VALID_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY" if paper_ref else "MISSING"
        ),
        "shared_identity_state": (
            "MISMATCH" if case and case.get("shared_input_identity_mismatch") is True else "MATCH"
        ),
        "runtime_resolver_snapshot_state": (
            "MISMATCH" if case and case.get("runtime_resolver_snapshot_mismatch") is True else "MATCH"
        ),
        "input_lock_state": "MISMATCH" if case and case.get("input_lock_mismatch") is True else "MATCH",
        "owner_policy_snapshot_state": (
            "MISMATCH" if case and case.get("owner_policy_snapshot_mismatch") is True else "MATCH"
        ),
        "comparison_state": "STATIC_SCHEMA_VALIDATION_ONLY_NOT_EVIDENCE" if valid else "BLOCKED",
        "routing_state": routing_state,
        "review_state": review_state,
        "pr92_owner_review_forwardable_flag": False,
        "pr92_owner_review_created_flag": False,
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
    }


def build_dual_result_review_parameter_stack_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    del registry
    failures: list[str] = []
    case = _case_by_id(fixture, case_id) if case_id is not None else None
    competition_packet = copy.deepcopy(
        upstream.get("replay_paper_candidate_stack_competition_packet", {})
    )
    entry = _competition_entry_for_fixture(upstream, fixture)
    if entry is None:
        entry = {}
    lineage = _selected_stack_lineage_trace(entry, competition_packet, fixture)
    identity = _identity_material(entry, competition_packet, fixture)
    block_codes = _block_codes_for_case(
        entry if entry else None,
        competition_packet,
        fixture,
        case,
        lineage,
    )
    valid = not block_codes
    route_override = str(case.get("route_override")) if case and case.get("route_override") else None
    review_state = route_override or ("BLOCKED_PENDING_REAL_RESULTS" if valid else block_codes[0])
    routing_state = review_state
    if "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_RESULT_SEPARATION_VIOLATION" in block_codes:
        review_state = "DUAL_RESULT_REVIEW_BLOCKED_REPLAY_PAPER_RESULT_SEPARATION_VIOLATION"
        routing_state = review_state

    replay_ref = None if case and case.get("missing_replay_result_packet") is True else str(
        fixture.get("replay_result_packet_ref")
    )
    paper_ref = None if case and case.get("missing_paper_result_packet") is True else str(
        fixture.get("paper_result_packet_ref")
    )
    if case and case.get("shared_input_identity_mismatch") is True:
        paper_identity = _digest(("MISMATCHED_PAPER_IDENTITY", identity["shared_identity"]))
    else:
        paper_identity = identity["shared_identity"]

    replay_validity = "PRESENT_VALID_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY"
    paper_validity = "PRESENT_VALID_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY"
    if case and case.get("stale_replay_result_packet") is True:
        replay_validity = "STALE_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY"
    if case and case.get("stale_paper_result_packet") is True:
        paper_validity = "STALE_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY"
    if case and case.get("invalid_replay_result_packet") is True:
        replay_validity = "INVALID_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY"
    if case and case.get("invalid_paper_result_packet") is True:
        paper_validity = "INVALID_STATIC_SYNTHETIC_SCHEMA_SHAPE_ONLY"
    if replay_ref is None:
        replay_validity = "MISSING"
    if paper_ref is None:
        paper_validity = "MISSING"

    replay_shape = _result_packet_shape(
        lane="replay",
        entry=entry,
        fixture=fixture,
        identity=identity,
        packet_ref=replay_ref,
        validity_state=replay_validity,
    )
    paper_shape = _result_packet_shape(
        lane="paper",
        entry=entry,
        fixture=fixture,
        identity={**identity, "shared_identity": paper_identity},
        packet_ref=paper_ref,
        validity_state=paper_validity,
    )
    comparison_matrix = _comparison_matrix(entry, fixture, identity, replay_ref, paper_ref)
    review_item = _review_item(
        entry,
        fixture,
        competition_packet,
        identity,
        lineage,
        replay_ref,
        paper_ref,
        review_state,
        routing_state,
        valid,
        case,
    )
    reason_codes = (
        _sort_reason_codes(
            (
                "DUAL_RESULT_REVIEW_ALLOWED_STATIC_SYNTHETIC_SCHEMA_VALIDATION_ONLY",
                "DUAL_RESULT_REVIEW_ALLOWED_PR90_COMPETITION_PACKET",
                "DUAL_RESULT_REVIEW_ALLOWED_PR89_HANDOFF_PACKET_LINEAGE",
                "DUAL_RESULT_REVIEW_ALLOWED_PR88_SELECTION_PACKET_LINEAGE",
                "DUAL_RESULT_REVIEW_ALLOWED_PR87_CANDIDATE_PACKET_LINEAGE",
                "DUAL_RESULT_REVIEW_ALLOWED_TRADE_CONTEXT_ROUTE_LINEAGE",
                "DUAL_RESULT_REVIEW_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE",
                "DUAL_RESULT_REVIEW_ALLOWED_QUANTUM_POLICY_LINEAGE",
                "DUAL_RESULT_REVIEW_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
                "DUAL_RESULT_REVIEW_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
                "DUAL_RESULT_REVIEW_ALLOWED_SEPARATE_REPLAY_AND_PAPER_RESULT_REFS",
                "DUAL_RESULT_REVIEW_ALLOWED_SHARED_INPUT_IDENTITY_MATCH",
                "DUAL_RESULT_REVIEW_ALLOWED_RUNTIME_RESOLVER_INPUT_LOCK_OWNER_POLICY_MATCH",
                "DUAL_RESULT_REVIEW_ALLOWED_SYNTHETIC_RESULT_FIXTURE_NOT_EVIDENCE",
                "DUAL_RESULT_REVIEW_ALLOWED_COMPARISON_MATRIX_STATIC_METADATA_ONLY",
                "DUAL_RESULT_REVIEW_ALLOWED_PR92_BOUNDARY_NO_OWNER_REVIEW_CREATED",
                "DUAL_RESULT_REVIEW_ALLOWED_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
                "DUAL_RESULT_REVIEW_BLOCKED_PENDING_REAL_RESULTS",
            )
        )
        if valid
        else block_codes
    )
    if case and case.get("negative_or_ambiguous_route") is True:
        allowed_code = str(case.get("expected_reason_code"))
        reason_codes = _sort_reason_codes([*reason_codes, allowed_code])

    packet_status = (
        "STATIC_DUAL_RESULT_REVIEW_PARAMETER_STACK_PACKET_SCHEMA_VALIDATED_PENDING_REAL_RESULTS"
        if valid
        else block_codes[0]
    )
    blocked_items = []
    if not valid:
        blocked_items.append(
            {
                "review_item_id": "BLOCKED_DUAL_RESULT_REVIEW_PARAMETER_STACK_ITEM",
                "selected_stack_id": entry.get("selected_stack_id") or fixture.get("expected_selected_stack_id"),
                "competition_entry_id": entry.get("competition_entry_id"),
                "blocked_reason_codes": block_codes,
                "active_review_created": False,
                "owner_live_promotion_review_created_flag": False,
                "owner_approval_created_flag": False,
                "live_promotion_created_flag": False,
                "order_authority_created_flag": False,
            }
        )

    packet: dict[str, Any] = {
        "dual_result_review_parameter_stack_packet_id": fixture.get(
            "dual_result_review_parameter_stack_packet_id"
        ),
        "schema_version": fixture.get("schema_version"),
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "review_scope": REVIEW_SCOPE,
        "review_authority_class": REVIEW_AUTHORITY_CLASS,
        "packet_status": packet_status,
        "fixture_case_id": None if case is None else case.get("case_id"),
        "upstream_replay_paper_competition_packet_ref": fixture.get(
            "upstream_replay_paper_competition_packet_ref"
        ),
        "upstream_replay_paper_competition_packet_digest_or_static_ref": fixture.get(
            "upstream_replay_paper_competition_packet_digest_or_static_ref"
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
        "selected_stack_id": entry.get("selected_stack_id") if entry else None,
        "selected_candidate_stack_id": entry.get("selected_candidate_stack_id") if entry else None,
        "selected_candidate_generation_key": entry.get("deterministic_generation_key") if entry else None,
        "selected_stack_lineage_trace": lineage,
        "selected_stack_digest_or_static_ref": _digest(
            (
                fixture.get("upstream_replay_paper_competition_packet_ref"),
                entry.get("selected_stack_id"),
                entry.get("competition_entry_id"),
            )
        ),
        "competition_entry_id": entry.get("competition_entry_id") if entry else None,
        "competition_manifest_id": fixture.get("competition_manifest_id"),
        "replay_paper_input_lock_id": identity["input_lock_id"],
        "replay_paper_input_identity_digest_or_static_ref": identity["shared_identity"],
        "replay_lane_input_descriptor_ref": competition_packet.get("replay_lane_input_descriptor_ref"),
        "paper_lane_input_descriptor_ref": competition_packet.get("paper_lane_input_descriptor_ref"),
        "replay_lane_contract_ref": competition_packet.get("replay_lane_contract_ref"),
        "paper_lane_contract_ref": competition_packet.get("paper_lane_contract_ref"),
        "replay_result_packet_ref": replay_ref,
        "paper_result_packet_ref": paper_ref,
        "replay_result_packet_authority_class": SYNTHETIC_FIXTURE_AUTHORITY_CLASS,
        "paper_result_packet_authority_class": SYNTHETIC_FIXTURE_AUTHORITY_CLASS,
        "replay_result_packet_is_synthetic_fixture_flag": True,
        "paper_result_packet_is_synthetic_fixture_flag": True,
        "synthetic_fixture_authority_class": SYNTHETIC_FIXTURE_AUTHORITY_CLASS,
        "shared_input_identity_match_flag": paper_identity == identity["shared_identity"],
        "runtime_resolver_snapshot_match_flag": not (
            case and case.get("runtime_resolver_snapshot_mismatch") is True
        ),
        "input_lock_match_flag": not (case and case.get("input_lock_mismatch") is True),
        "owner_policy_snapshot_match_flag": not (
            case and case.get("owner_policy_snapshot_mismatch") is True
        ),
        "replay_paper_result_separation_preserved_flag": not bool(
            case
            and (
                case.get("result_merge_detected") is True
                or case.get("result_overwrite_detected") is True
                or case.get("result_collapse_detected") is True
            )
        ),
        "result_merge_detected_flag": bool(case and case.get("result_merge_detected") is True),
        "result_overwrite_detected_flag": bool(case and case.get("result_overwrite_detected") is True),
        "result_collapse_detected_flag": bool(case and case.get("result_collapse_detected") is True),
        "comparison_matrix_id": comparison_matrix["comparison_matrix_id"],
        "comparison_matrix_digest_or_static_ref": comparison_matrix[
            "comparison_matrix_digest_or_static_ref"
        ],
        "comparison_metric_fields_declared": list(fixture.get("comparison_metric_fields_declared", [])),
        "comparison_metric_values_real_flag": False,
        "net_profit_review_supported_flag": True,
        "latency_review_supported_flag": True,
        "risk_review_supported_flag": True,
        "quantum_vs_classical_review_supported_flag": True,
        "owner_thresholds_policy_ref": fixture.get("owner_thresholds_policy_ref"),
        "owner_thresholds_authority_class": fixture.get("owner_thresholds_authority_class"),
        "review_state": review_state,
        "review_reason_codes": reason_codes,
        "negative_or_ambiguous_route": bool(case and case.get("negative_or_ambiguous_route") is True),
        "owner_live_promotion_review_required_flag": True,
        "pr92_owner_live_promotion_review_required_flag": True,
        "pr92_owner_live_promotion_review_created_flag": False,
        "owner_approval_created_flag": False,
        "live_promotion_created_flag": False,
        "canary_eligibility_created_flag": False,
        "replay_execution_created_flag": False,
        "paper_execution_created_flag": False,
        "result_values_created_from_execution_flag": False,
        "optimizer_execution_created_flag": False,
        "quantum_backend_execution_created_flag": False,
        "quantum_simulator_execution_created_flag": False,
        "order_submission_allowed_flag": False,
        "live_routing_allowed_flag": False,
        "connector_binding_allowed_flag": False,
        "source_dependency_state": fixture.get("source_dependency_state"),
        "source_retrieval_created_flag": False,
        "source_acceptance_created_flag": False,
        "connector_semantic_binding_created_flag": False,
        "runtime_cash_receipt_created_flag": False,
        "live_trade_authority_created_flag": False,
        "no_order_authority_flag": True,
        "no_runtime_execution_flag": True,
        "no_replay_execution_flag": True,
        "no_paper_execution_flag": True,
        "no_live_promotion_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
        "no_live_trade_authority_flag": True,
        "review_items": [review_item] if valid else [],
        "blocked_review_items": blocked_items,
        "rejected_review_items": [],
        "synthetic_replay_result_packet_shape": replay_shape,
        "synthetic_paper_result_packet_shape": paper_shape,
        "comparison_matrix": comparison_matrix,
        "future_pass_route_if_real_results_validate": "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED",
        "pr92_owner_review_forwardable_flag": False,
        "pr92_owner_review_created_flag": False,
        "competition_entry_count": 1 if entry else 0,
        "replay_result_ref_count": 1 if replay_ref else 0,
        "paper_result_ref_count": 1 if paper_ref else 0,
        "valid_review_item_count": 1 if valid else 0,
        "blocked_review_item_count": 0 if valid else 1,
        "rejected_review_item_count": 0,
        "synthetic_fixture_result_ref_count": int(bool(replay_ref)) + int(bool(paper_ref)),
        "real_result_packet_created_count": 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "owner_live_promotion_review_packet_count": 0,
        "owner_approval_count": 0,
        "live_promotion_count": 0,
        "order_authoritative_item_count": 0,
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        packet.setdefault(field, False)
    return packet, failures


def validate_review_packet(packet: dict[str, Any], upstream: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in (
        "no_order_authority_flag",
        "no_runtime_execution_flag",
        "no_replay_execution_flag",
        "no_paper_execution_flag",
        "no_live_promotion_flag",
        "no_quantum_backend_execution_flag",
        "no_profit_evidence_flag",
        "no_live_trade_authority_flag",
        "owner_live_promotion_review_required_flag",
        "pr92_owner_live_promotion_review_required_flag",
    ):
        if packet.get(field) is not True:
            failures.append(f"packet.{field} must be true")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: packet.{field} must be false")
    for field in (
        "real_result_packet_created_count",
        "replay_execution_count",
        "paper_execution_count",
        "owner_live_promotion_review_packet_count",
        "owner_approval_count",
        "live_promotion_count",
        "order_authoritative_item_count",
    ):
        if packet.get(field) != 0:
            failures.append(f"packet.{field} must be zero")
    ready = packet.get("valid_review_item_count") == 1
    review_items = _list_of_mappings(packet.get("review_items"))
    blocked_items = _list_of_mappings(packet.get("blocked_review_items"))
    if ready:
        if len(review_items) != 1:
            failures.append("valid review packet must contain exactly one review item")
        if blocked_items:
            failures.append("valid review packet must not contain blocked review items")
    else:
        if review_items:
            failures.append("blocked review packet must not contain active review items")
        if not blocked_items:
            failures.append("blocked review packet must retain blocked diagnostic item")
    if packet.get("replay_result_packet_ref") and packet.get("paper_result_packet_ref"):
        if packet.get("replay_result_packet_ref") == packet.get("paper_result_packet_ref"):
            failures.append("replay and paper result packet refs must be separate")
    for shape_field in ("synthetic_replay_result_packet_shape", "synthetic_paper_result_packet_shape"):
        shape = packet.get(shape_field)
        if not isinstance(shape, dict):
            failures.append(f"{shape_field} must be an object")
            continue
        if shape.get("authority_class") != SYNTHETIC_FIXTURE_AUTHORITY_CLASS:
            failures.append(f"{shape_field}.authority_class must be synthetic schema validation only")
        for field in (
            "synthetic_fixture_flag",
            "static_schema_validation_only_flag",
            "not_execution_evidence_flag",
            "not_profit_evidence_flag",
            "not_replay_or_paper_pass_fail_proof_flag",
        ):
            if shape.get(field) is not True:
                failures.append(f"{shape_field}.{field} must be true")
        for field in (
            "metric_values_created_from_execution_flag",
            "result_values_created_from_execution_flag",
            "real_result_packet_created_flag",
        ):
            if shape.get(field) is not False:
                failures.append(f"{shape_field}.{field} must be false")
    matrix = packet.get("comparison_matrix")
    if not isinstance(matrix, dict):
        failures.append("comparison_matrix must be an object")
    else:
        if matrix.get("comparison_metric_values_real_flag") is not False:
            failures.append("comparison_matrix must not contain real metric values")
        for field in (
            "result_merge_allowed_flag",
            "result_overwrite_allowed_flag",
            "result_collapse_allowed_flag",
            "live_authority_created_flag",
            "profit_evidence_created_flag",
        ):
            if matrix.get(field) is not False:
                failures.append(f"comparison_matrix.{field} must be false")
    if ready and review_items:
        item = review_items[0]
        if item.get("competition_entry_id") not in upstream.get("competition_entries_by_id", {}):
            failures.append("review item must derive from PR90 competition entry")
        lineage = _list_of_mappings(item.get("selected_stack_lineage_trace"))
        if not _has_required_lineage(lineage):
            failures.append("review item lineage must trace to PR90, PR89, PR88, PR87, and route")
        if item.get("quantum_candidate_type") != "CLASSICAL_ONLY" and not item.get("classical_comparator_ref"):
            failures.append("quantum-aware review item requires classical comparator")
        if item.get("pr92_owner_review_forwardable_flag") is not False:
            failures.append("PR91 synthetic fixture must not be forwardable to PR92 as real evidence")
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
        ("synthetic_fixture_authority_class", SYNTHETIC_FIXTURE_AUTHORITY_CLASS),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "review_contract_only_flag",
        "no_order_authority_flag",
        "no_runtime_execution_flag",
        "no_replay_execution_flag",
        "no_paper_execution_flag",
        "no_live_promotion_flag",
        "no_quantum_backend_execution_flag",
        "no_profit_evidence_flag",
        "no_live_trade_authority_flag",
    ):
        if fixture.get(field) is not True:
            failures.append(f"fixture.{field} must be true")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if fixture.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: fixture.{field} must be false")

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

    packet, packet_failures = build_dual_result_review_parameter_stack_packet(
        registry,
        fixture,
        upstream,
    )
    failures.extend(packet_failures)
    failures.extend(validate_review_packet(packet, upstream))
    for count_field in (
        "expected_competition_entry_count",
        "expected_replay_result_ref_count",
        "expected_paper_result_ref_count",
        "expected_valid_review_item_count",
        "expected_blocked_review_item_count",
        "expected_rejected_review_item_count",
        "expected_synthetic_fixture_result_ref_count",
        "expected_real_result_packet_created_count",
        "expected_replay_execution_count",
        "expected_paper_execution_count",
        "expected_owner_live_promotion_review_packet_count",
        "expected_owner_approval_count",
        "expected_live_promotion_count",
        "expected_order_authoritative_item_count",
    ):
        packet_field = count_field.replace("expected_", "")
        if fixture.get(count_field) != packet.get(packet_field):
            failures.append(f"default fixture {packet_field} mismatch")
    if packet.get("review_state") != fixture.get("expected_review_state"):
        failures.append("default fixture review_state mismatch")
    if packet.get("selected_stack_id") != fixture.get("expected_selected_stack_id"):
        failures.append("default fixture selected_stack_id mismatch")

    case_packets: list[dict[str, Any]] = []
    for case in cases:
        case_packet, case_failures = build_dual_result_review_parameter_stack_packet(
            registry,
            fixture,
            upstream,
            case_id=str(case.get("case_id")),
        )
        failures.extend(case_failures)
        failures.extend(validate_review_packet(case_packet, upstream))
        expected_count = case.get("expected_valid_review_item_count")
        if (
            expected_count is not None
            and case_packet.get("valid_review_item_count") != expected_count
        ):
            failures.append(f"{case.get('case_id')} valid review item count mismatch")
        expected_state = case.get("expected_review_state")
        if expected_state is not None and case_packet.get("review_state") != expected_state:
            failures.append(f"{case.get('case_id')} review_state mismatch")
        expected_code = case.get("expected_reason_code")
        reason_codes = list(case_packet.get("review_reason_codes", []))
        blocked_codes = [
            code
            for item in _list_of_mappings(case_packet.get("blocked_review_items"))
            for code in item.get("blocked_reason_codes", [])
        ]
        if expected_code not in reason_codes and expected_code not in blocked_codes:
            failures.append(f"{case.get('case_id')} missing expected reason code {expected_code}")
        case_packets.append(case_packet)

    pr92 = fixture.get("pr92_boundary_fixture")
    if not isinstance(pr92, dict):
        failures.append("fixture.pr92_boundary_fixture must be an object")
    else:
        if pr92.get("pr92_owner_live_promotion_review_required_flag") is not True:
            failures.append("PR92 boundary fixture must require owner live-promotion review")
        for field in (
            "pr92_owner_live_promotion_review_created_flag",
            "owner_approval_created_flag",
            "live_promotion_created_flag",
        ):
            if pr92.get(field) is not False:
                failures.append(f"PR92 boundary fixture {field} must be false")
    return failures, packet, case_packets


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "DUAL_RESULT_REVIEW_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
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
            "DUAL_RESULT_REVIEW_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
            f"{MASTER_PLAN_CURRENT.as_posix()} has local diff"
        ]
    return [f"git diff check failed for {MASTER_PLAN_CURRENT.as_posix()}: {completed.stderr.strip()}"]


def validate_validator_static_surface(validator_path: pathlib.Path) -> list[str]:
    text = validator_path.read_text(encoding="utf-8")
    forbidden_tokens = (
        "import " + "random",
        "from " + "random",
        "import " + "uuid",
        "from " + "uuid",
        "datetime" + ".now",
        "time" + ".time",
        "os" + ".environ",
        "requests" + ".",
        "urllib" + ".request",
        "http" + ".client",
        "socket" + ".",
    )
    return [
        f"validator contains forbidden nondeterministic or network token {token}"
        for token in forbidden_tokens
        if token in text
    ]


def build_report(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    packet: dict[str, Any],
    case_packets: list[dict[str, Any]],
    upstream: dict[str, Any],
    metadata: dict[str, Any],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    review_items = _list_of_mappings(packet.get("review_items"))
    item = review_items[0] if review_items else {}
    comparison_matrix = packet.get("comparison_matrix") if isinstance(packet.get("comparison_matrix"), dict) else {}
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
        "dual_result_review_gate_registry_id": registry.get("dual_result_review_gate_registry_id"),
        "dual_result_review_parameter_stack_packet_contract_id": registry.get(
            "dual_result_review_parameter_stack_packet_contract_id"
        ),
        "gate_scope": registry.get("gate_scope"),
        "review_scope": REVIEW_SCOPE,
        "review_authority_class": REVIEW_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "review_contract_only_flag": True,
        "synthetic_fixture_authority_class": SYNTHETIC_FIXTURE_AUTHORITY_CLASS,
        "review_inputs": list(REVIEW_INPUT_ORDER),
        "review_outputs": list(REVIEW_OUTPUT_ORDER),
        "review_policy": copy.deepcopy(registry.get("review_policy")),
        "blocked_review_policy": copy.deepcopy(registry.get("blocked_review_policy")),
        "deterministic_review_chain": list(DETERMINISTIC_REVIEW_CHAIN),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "upstream_dependencies": copy.deepcopy(registry.get("upstream_dependencies")),
        "future_consumers": copy.deepcopy(registry.get("future_consumers")),
        "upstream_replay_paper_competition_packet_ref": copy.deepcopy(
            registry.get("upstream_replay_paper_competition_packet_ref")
        ),
        "stage1_concurrent_replay_paper_contract_ref": copy.deepcopy(
            registry.get("stage1_concurrent_replay_paper_contract_ref")
        ),
        "stage1_dual_result_review_contract_ref": copy.deepcopy(
            registry.get("stage1_dual_result_review_contract_ref")
        ),
        "stage1_dual_result_static_schema_refs": list(
            registry.get("stage1_dual_result_static_schema_refs", [])
        ),
        "upstream_replay_paper_competition_packet_id": upstream.get(
            "replay_paper_candidate_stack_competition_packet", {}
        ).get("replay_paper_candidate_stack_competition_packet_id"),
        "upstream_selected_stack_handoff_packet_id": upstream.get(
            "replay_paper_candidate_stack_competition_packet", {}
        ).get("upstream_selected_stack_handoff_packet_ref"),
        "upstream_trade_context_selection_packet_id": upstream.get(
            "replay_paper_candidate_stack_competition_packet", {}
        ).get("upstream_trade_context_selection_packet_ref"),
        "upstream_candidate_generation_packet_id": upstream.get(
            "replay_paper_candidate_stack_competition_packet", {}
        ).get("upstream_candidate_generation_packet_ref"),
        "dual_result_review_parameter_stack_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "competition_entry_count": packet.get("competition_entry_count"),
        "replay_result_ref_count": packet.get("replay_result_ref_count"),
        "paper_result_ref_count": packet.get("paper_result_ref_count"),
        "valid_review_item_count": packet.get("valid_review_item_count"),
        "blocked_review_item_count": packet.get("blocked_review_item_count"),
        "rejected_review_item_count": packet.get("rejected_review_item_count"),
        "synthetic_fixture_result_ref_count": packet.get("synthetic_fixture_result_ref_count"),
        "real_result_packet_created_count": packet.get("real_result_packet_created_count"),
        "replay_execution_count": packet.get("replay_execution_count"),
        "paper_execution_count": packet.get("paper_execution_count"),
        "owner_live_promotion_review_packet_count": packet.get(
            "owner_live_promotion_review_packet_count"
        ),
        "owner_approval_count": packet.get("owner_approval_count"),
        "live_promotion_count": packet.get("live_promotion_count"),
        "order_authoritative_item_count": packet.get("order_authoritative_item_count"),
        "selected_stack_id": packet.get("selected_stack_id"),
        "selected_candidate_stack_id": packet.get("selected_candidate_stack_id"),
        "selected_candidate_generation_key": packet.get("selected_candidate_generation_key"),
        "selected_stack_lineage_trace": copy.deepcopy(packet.get("selected_stack_lineage_trace", [])),
        "selected_stack_digest_or_static_ref": packet.get("selected_stack_digest_or_static_ref"),
        "competition_entry_id": packet.get("competition_entry_id"),
        "competition_manifest_id": packet.get("competition_manifest_id"),
        "replay_paper_input_lock_id": packet.get("replay_paper_input_lock_id"),
        "replay_paper_input_identity_digest_or_static_ref": packet.get(
            "replay_paper_input_identity_digest_or_static_ref"
        ),
        "replay_lane_input_descriptor_ref": packet.get("replay_lane_input_descriptor_ref"),
        "paper_lane_input_descriptor_ref": packet.get("paper_lane_input_descriptor_ref"),
        "replay_result_packet_ref": packet.get("replay_result_packet_ref"),
        "paper_result_packet_ref": packet.get("paper_result_packet_ref"),
        "comparison_matrix_id": comparison_matrix.get("comparison_matrix_id"),
        "comparison_matrix_digest_or_static_ref": comparison_matrix.get(
            "comparison_matrix_digest_or_static_ref"
        ),
        "deterministic_static_review": True,
        "no_randomness": True,
        "no_wall_clock_identity": True,
        "review_entries_derived_only_from_pr90_competition_packet": True,
        "selected_stack_lineage_traces_to_pr90_competition_packet": True,
        "selected_stack_lineage_traces_to_pr89_handoff_packet": True,
        "selected_stack_lineage_traces_to_pr88_selection_packet": True,
        "selected_stack_lineage_traces_to_pr87_candidate_packet": True,
        "trade_context_and_route_lineage_preserved": True,
        "scoring_ranking_arbitration_lineage_preserved": True,
        "quantum_policy_lineage_preserved": True,
        "classical_comparator_or_fallback_preserved_for_quantum_selected_stack": bool(
            item.get("classical_comparator_ref")
        ),
        "quantum_classical_static_comparison_metadata_declared": True,
        "owner_override_records_basis_without_external_fact_fabrication": True,
        "owner_threshold_policy_static_only": True,
        "replay_and_paper_result_refs_separate": (
            packet.get("replay_result_packet_ref") != packet.get("paper_result_packet_ref")
        ),
        "shared_input_identity_match_required": True,
        "shared_input_identity_match_for_valid_fixture": packet.get(
            "shared_input_identity_match_flag"
        ),
        "runtime_resolver_snapshot_match_for_valid_fixture": packet.get(
            "runtime_resolver_snapshot_match_flag"
        ),
        "input_lock_match_for_valid_fixture": packet.get("input_lock_match_flag"),
        "owner_policy_snapshot_match_for_valid_fixture": packet.get(
            "owner_policy_snapshot_match_flag"
        ),
        "synthetic_result_fixtures_are_not_evidence": True,
        "comparison_metric_values_real_flag": False,
        "pass_route_only_to_pr92_owner_review_required": True,
        "pr92_forwardability_metadata_created": True,
        "pr92_owner_live_promotion_review_required_flag": packet.get(
            "pr92_owner_live_promotion_review_required_flag"
        ),
        "pr92_owner_live_promotion_review_created_flag": False,
        "pr92_owner_review_created": False,
        "owner_approval_created_flag": False,
        "live_promotion_created_flag": False,
        "final_ready": False,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "real_optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "live_order_authority": False,
        "result_boundary_refs_are_not_result_packets": True,
    }
    for field in REPORT_FALSE_FIELDS:
        report[field] = False
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

    metadata_failures, metadata = validate_pr91_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_gate_payload(registry, repo_root=repo_root))
    fixture_failures, packet, case_packets = validate_fixture(
        fixture,
        registry,
        upstream,
    )
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
