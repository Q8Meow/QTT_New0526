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

from tools import validate_selected_parameter_stack_handoff_packet as pr89_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "replay_paper_candidate_stack_competition_gate.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "ReplayPaperCandidateStackCompetitionGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_replay_paper_candidate_stack_competition_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "ReplayPaperCandidateStackCompetitionGate.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = pr89_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr89_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = pr89_gate.MASTER_PLAN_CURRENT

GATE_REGISTRY_ID = "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE"
GATE_CONTRACT_ID = "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_V1"
REPORT_ID = "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #90"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-REPLAY-PAPER-CANDIDATE-STACK-COMPETITION-GATE"
TARGET_BRANCH = "pr90-replay-paper-candidate-stack-competition-gate"
EXPECTED_BASELINE_ANCESTOR = "6523103"
GATE_SCOPE = "STATIC_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_ONLY"
COMPETITION_SCOPE = "STATIC_ONLY"
COMPETITION_AUTHORITY_CLASS = (
    "STATIC_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_NOT_REPLAY_EXECUTION_"
    "NOT_PAPER_EXECUTION_NOT_RESULTS_NOT_LIVE_AUTHORITY"
)
ORDER_INTENT_PREVIEW_AUTHORITY = pr89_gate.ORDER_INTENT_PREVIEW_AUTHORITY
SUCCESS_MARKER = "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_OK"
FAILURE_MARKER = "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = pr89_gate.CI_DETACHED_HEAD_MODE_MARKER
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = pr89_gate.CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    pr89_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
)

ROLE_ORDER = pr89_gate.ROLE_ORDER
DEPENDENCY_ORDER = pr89_gate.DEPENDENCY_ORDER + (
    "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
)
DEPENDENCY_MARKERS = {
    **pr89_gate.DEPENDENCY_MARKERS,
    "PR89_QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET": pr89_gate.SUCCESS_MARKER,
}
FUTURE_CONSUMER_ORDER = (
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
    "PR105_PR151_STAGE1_RUNTIME_LIVE_LAUNCH_CLOSURE_CONSUMERS",
)
STAGE1_STATIC_CONTRACT_REPORTS = (
    (
        "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK",
        pathlib.Path("docs")
        / "master_plan"
        / "generated"
        / "Stage1RuntimeResolverToReplayPaperHandoff.report.json",
        "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_REPORT",
    ),
    (
        "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK",
        pathlib.Path("docs")
        / "master_plan"
        / "generated"
        / "Stage1ConcurrentReplayPaperContractCheck.report.json",
        "STAGE1_CONCURRENT_REPLAY_PAPER_EXECUTION_GATE_REPORT",
    ),
    (
        "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK",
        pathlib.Path("docs")
        / "master_plan"
        / "generated"
        / "Stage1DualResultReviewContractCheck.report.json",
        "STAGE1_DUAL_RESULT_REVIEW_GATE_REPORT",
    ),
)
COMPETITION_INPUT_ORDER = (
    "PR89_static_selected_parameter_stack_handoff_packet",
    "PR88_static_trade_context_parameter_stack_selection_packet",
    "PR87_static_candidate_generation_packet",
    "PR78_static_trade_context_packet_metadata",
    "PR81_routed_selection_universe_metadata",
    "PR82_quantum_applicability_metadata",
    "PR83_owner_quantum_priority_policy_metadata",
    "PR84_scoring_policy_registry",
    "PR85_static_scoring_ranking_metadata",
    "PR86_static_optimizer_arbitration_metadata",
    "Stage1_runtime_resolver_to_replay_paper_handoff_static_contract",
    "Stage1_concurrent_replay_paper_input_identity_static_contract",
    "Stage1_concurrent_replay_lane_static_contract",
    "Stage1_concurrent_paper_lane_static_contract",
    "Stage1_replay_result_packet_boundary_static_ref_only",
    "Stage1_paper_result_packet_boundary_static_ref_only",
)
COMPETITION_OUTPUT_ORDER = (
    "static_replay_paper_candidate_stack_competition_packet",
    "static_competition_manifest",
    "static_competition_entry_descriptors",
    "static_replay_lane_input_descriptor",
    "static_paper_lane_input_descriptor",
    "static_replay_paper_input_lock_identity",
    "static_result_boundary_refs_only",
    "pr91_forwardability_metadata_no_review_created",
    "pr92_owner_review_boundary_metadata_no_review_created",
    "no_replay_execution_boundary",
    "no_paper_execution_boundary",
    "no_result_packet_boundary",
    "no_order_authority_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "no_profit_evidence_boundary",
)
DETERMINISTIC_COMPETITION_CHAIN = (
    "PR89_selected_handoff_packet_required",
    "PR89_selected_handoff_item_must_be_pr90_forwardable",
    "selected_stack_id_required_and_unique",
    "selected_stack_lineage_to_PR89_PR88_PR87_required",
    "trade_context_and_routed_selection_universe_lineage_required",
    "role_completion_and_compatibility_required",
    "blocked_rows_absent",
    "source_dependency_state_static_only",
    "scoring_ranking_arbitration_lineage_required",
    "quantum_policy_lineage_with_classical_comparator_or_fallback",
    "owner_override_internal_basis_only_when_recorded",
    "shared_static_input_lock_identity_required",
    "separate_replay_and_paper_lane_descriptors_required",
    "result_boundary_refs_only_no_result_packets",
    "non_authoritative_order_intent_preview_only",
    "lexicographic_competition_packet_and_entry_ids",
)
REASON_CODE_ORDER = (
    "REPLAY_PAPER_COMPETITION_ALLOWED_STATIC_FIXTURE_ONLY",
    "REPLAY_PAPER_COMPETITION_ALLOWED_PR89_HANDOFF_PACKET",
    "REPLAY_PAPER_COMPETITION_ALLOWED_PR88_SELECTION_PACKET",
    "REPLAY_PAPER_COMPETITION_ALLOWED_PR87_CANDIDATE_PACKET",
    "REPLAY_PAPER_COMPETITION_ALLOWED_TRADE_CONTEXT_ROUTE_LINEAGE",
    "REPLAY_PAPER_COMPETITION_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE",
    "REPLAY_PAPER_COMPETITION_ALLOWED_QUANTUM_POLICY_LINEAGE",
    "REPLAY_PAPER_COMPETITION_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
    "REPLAY_PAPER_COMPETITION_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
    "REPLAY_PAPER_COMPETITION_ALLOWED_REPLAY_PAPER_INPUT_LOCK",
    "REPLAY_PAPER_COMPETITION_ALLOWED_SEPARATE_REPLAY_AND_PAPER_LANES",
    "REPLAY_PAPER_COMPETITION_ALLOWED_RESULT_BOUNDARY_REFS_ONLY",
    "REPLAY_PAPER_COMPETITION_ALLOWED_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
    "REPLAY_PAPER_COMPETITION_ALLOWED_PR91_PR92_BOUNDARY_NO_REVIEW_CREATED",
    "REPLAY_PAPER_COMPETITION_ALLOWED_DETERMINISTIC_COMPETITION_IDS",
    "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_PR89_HANDOFF_PACKET",
    "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_SELECTED_STACK_ID",
    "REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_ID_NOT_IN_PR89_HANDOFF",
    "REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_NOT_FORWARDABLE_TO_PR90",
    "REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR89_PR88_PR87",
    "REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_STATUS",
    "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_REQUIRED_ROLE",
    "REPLAY_PAPER_COMPETITION_BLOCKED_INCOMPATIBLE_SELECTED_STACK",
    "REPLAY_PAPER_COMPETITION_BLOCKED_BLOCKED_ROW_PRESENT",
    "REPLAY_PAPER_COMPETITION_BLOCKED_ROUTE_MISMATCH",
    "REPLAY_PAPER_COMPETITION_BLOCKED_SOURCE_DEPENDENCY_STATE",
    "REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_CLASSICAL_COMPARATOR",
    "REPLAY_PAPER_COMPETITION_BLOCKED_NO_COMPETITION_ENTRIES",
    "REPLAY_PAPER_COMPETITION_BLOCKED_AMBIGUOUS_REPLAY_PAPER_INPUT_IDENTITY",
    "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_LANE_MISSING",
    "REPLAY_PAPER_COMPETITION_BLOCKED_PAPER_LANE_MISSING",
    "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE",
    "REPLAY_PAPER_COMPETITION_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_DUAL_RESULT_REVIEW_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_OWNER_APPROVAL_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "REPLAY_PAPER_COMPETITION_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR90_METADATA_VERIFIED",
    "PASS_VALID_REPLAY_PAPER_COMPETITION_MANIFEST_FROM_PR89_HANDOFF",
    "PASS_REPLAY_AND_PAPER_LANE_DESCRIPTORS_FROM_SHARED_INPUT_LOCK",
    "PASS_SELECTED_STACK_LINEAGE_TO_PR89_PR88_PR87",
    "PASS_QUANTUM_PREFERRED_WITH_CLASSICAL_COMPARATOR",
    "PASS_CLASSICAL_COMPARATOR_AND_QUANTUM_STATIC_PAIR",
    "PASS_OWNER_OVERRIDE_INTERNAL_BASIS",
    "PASS_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
    "BLOCK_MISSING_PR89_HANDOFF_PACKET",
    "BLOCK_MISSING_SELECTED_STACK_ID",
    "BLOCK_SELECTED_STACK_NOT_FORWARDABLE",
    "BLOCK_UNTRACEABLE_SELECTED_STACK_LINEAGE",
    "BLOCK_BLOCKED_SELECTED_STACK",
    "BLOCK_INCOMPATIBLE_SELECTED_STACK",
    "BLOCK_MISSING_ROLE_SELECTED_STACK",
    "BLOCK_REPLAY_LANE_MISSING",
    "BLOCK_PAPER_LANE_MISSING",
    "BLOCK_REPLAY_PAPER_INPUT_IDENTITY_MISMATCH",
    "BLOCK_REPLAY_RESULT_PACKET_PRESENT",
    "BLOCK_PAPER_RESULT_PACKET_PRESENT",
    "BLOCK_EXECUTABLE_ORDER_INTENT_PRESENT",
    "BLOCK_NO_COMPETITION_ENTRIES",
    "PASS_PR91_BOUNDARY_FUTURE_RESULTS_REQUIRED_NO_REVIEW_CREATED",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "order_intent_authority_created",
    "order_submission_allowed_flag",
    "live_routing_allowed_flag",
    "connector_binding_allowed_flag",
    "source_retrieval_created_flag",
    "source_acceptance_created_flag",
    "connector_semantic_binding_created_flag",
    "runtime_cash_receipt_created_flag",
    "replay_execution_created_flag",
    "paper_execution_created_flag",
    "replay_result_packet_created_flag",
    "paper_result_packet_created_flag",
    "dual_result_review_created_flag",
    "owner_live_promotion_review_created_flag",
    "classical_optimizer_execution_created_flag",
    "quantum_optimizer_execution_created_flag",
    "optimizer_execution_created_flag",
    "quantum_backend_execution_created_flag",
    "quantum_simulator_execution_created_flag",
    "owner_approval_created_flag",
    "live_trade_authority_created_flag",
    "live_promotion_created_flag",
    "profit_evidence_created_flag",
    "quantum_advantage_claim_created_flag",
    "latency_superiority_claim_created_flag",
    "execution_superiority_claim_created_flag",
    "random_identity_used",
    "wall_clock_identity_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_cash_receipt_created",
    "private_state_fetch_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_result_packet_created",
    "paper_result_packet_created",
    "result_values_created",
    "dual_result_review_created",
    "owner_live_promotion_review_created",
    "classical_optimizer_execution_created",
    "quantum_optimizer_execution_created",
    "optimizer_execution_created",
    "backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "order_submission_created",
    "order_cancellation_created",
    "fill_receipt_created",
    "owner_approval_created",
    "live_promotion_created",
    "profit_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "competition_packet_is_executable_order_intent",
    "competition_packet_is_live_order_authority",
    "competition_packet_is_replay_result",
    "competition_packet_is_paper_result",
    "order_intent_preview_is_authoritative",
    "pr91_execution_review_created",
    "pr92_owner_review_created",
)
FIELD_REASON_CODES = {
    "order_intent_authority_created": "REPLAY_PAPER_COMPETITION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "order_submission_allowed_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "live_routing_allowed_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "connector_binding_allowed_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "source_retrieval_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "source_acceptance_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "connector_semantic_binding_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "replay_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "paper_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "replay_result_packet_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE",
    "paper_result_packet_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE",
    "dual_result_review_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_DUAL_RESULT_REVIEW_FORBIDDEN",
    "owner_live_promotion_review_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "classical_optimizer_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_backend_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "owner_approval_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_OWNER_APPROVAL_FORBIDDEN",
    "live_trade_authority_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "live_promotion_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "profit_evidence_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "execution_superiority_claim_created_flag": "REPLAY_PAPER_COMPETITION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "random_identity_used": "REPLAY_PAPER_COMPETITION_BLOCKED_AMBIGUOUS_REPLAY_PAPER_INPUT_IDENTITY",
    "wall_clock_identity_used": "REPLAY_PAPER_COMPETITION_BLOCKED_AMBIGUOUS_REPLAY_PAPER_INPUT_IDENTITY",
    "atomicrows_bundle_jsonl_created": "REPLAY_PAPER_COMPETITION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "REPLAY_PAPER_COMPETITION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
}
SOURCE_ALLOWED_STATES = {"STATIC_SOURCE_DEPENDENCY_LABELS_ONLY"}
REQUIRED_MASTER_PLAN_PRINCIPLES = {
    "REPLAY_AND_PAPER_CONCURRENT_SEPARATE_LANES_AFTER_SHARED_INPUT_LOCK",
    "REPLAY_PASS_TO_PAPER_SEQUENTIAL_TRANSITION_NOT_ALLOWED",
    "REPLAY_AND_PAPER_RESULTS_REMAIN_SEPARATE",
    "PRE_LIVE_VALIDATION_MODE_CONCURRENT_REPLAY_AND_PAPER_ONLY",
    "PR90_STATIC_MUST_NOT_EXECUTE_REPLAY_OR_PAPER",
    "REPLAY_PAPER_RESULT_PACKETS_ARE_LATER_RUNTIME_ARTIFACTS",
    "DUAL_RESULT_REVIEW_REMAINS_PR91",
    "OWNER_LIVE_PROMOTION_REVIEW_REMAINS_PR92",
    "EDGE_HYPOTHESIS_PACKET_REQUIRED_BEFORE_PARAMETER_STACK_SELECTION",
    "EDGE_PARAMETER_STACK_SELECTION_REQUIRED",
    "SELECTED_PARAMETER_STACK_HANDOFF_STATIC_UNTIL_LATER_GATES",
    "ATOMICROWS_INVENTORY_NOT_TRADER",
    "NO_SINGLE_PARAMETER_OR_ALGORITHM_STACKS",
    "MINIMUM_REQUIRED_STACK_ROLES",
    "BLOCKED_ROWS_EXCLUDED_FROM_ACTIVE_STACKS",
    "QUANTUM_RANK_REFINE_ONLY_NO_DIRECT_LIVE_AUTHORITY",
    "CLASSICAL_EXECUTION_GATES_REMAIN_FINAL",
    "EXECUTION_ROUTER_FINAL_ORDER_SUBMISSION_AUTHORITY",
    "SOURCE_CONNECTOR_CASH_ORDER_FACTS_REQUIRE_ACCEPTED_OR_RUNTIME_RECEIPTS",
    "OWNER_REVIEW_AND_APPROVAL_REMAIN_LATER_GATES",
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
    return pr89_gate.load_yaml(path)


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
    return os.getenv("GITHUB_ACTIONS") == "true"


def _downstream_validation_branch_allowed(branch: str) -> bool:
    if branch == "main":
        return True
    match = re.match(r"^pr(?P<number>[0-9]+)[a-z]*-", branch)
    if match is None:
        return False
    return int(match.group("number")) > 90


def validate_pr90_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 90), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 90), None)
    if roadmap_entry is None:
        failures.append("PR90 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR90 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Replay/paper candidate stack competition gate"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Replay/paper candidate stack competition gate"),
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
        str(item.get("artifact_id") or "")
        for item in _list_of_mappings(payload.get("upstream_dependencies"))
    ]
    if dependency_ids != list(DEPENDENCY_ORDER):
        failures.append("upstream_dependencies must use canonical PR77-PR89 dependency order")
    for dependency in _list_of_mappings(payload.get("upstream_dependencies")):
        artifact_id = str(dependency.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker is None:
            failures.append(f"unknown upstream dependency {artifact_id}")
            continue
        if dependency.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id}.validation_marker must be {expected_marker}")
        for field in ("registry_path", "report_path", "validator_path"):
            rel = dependency.get(field)
            if not isinstance(rel, str) or not rel:
                failures.append(f"{artifact_id}.{field} missing")
                continue
            if not _resolve(repo_root, pathlib.Path(rel)).exists():
                failures.append(f"{artifact_id}.{field} path missing: {rel}")
    return failures


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumer_ids = [
        str(item.get("consumer_id") or "")
        for item in _list_of_mappings(payload.get("future_consumers"))
    ]
    if consumer_ids != list(FUTURE_CONSUMER_ORDER):
        failures.append("future_consumers must use canonical PR91/PR92/Stage1 consumer order")
    for consumer in _list_of_mappings(payload.get("future_consumers")):
        if consumer.get("pr90_creates_consumer_execution") is not False:
            failures.append(
                f"{consumer.get('consumer_id')} pr90_creates_consumer_execution must be false"
            )
    return failures


def validate_competition_policy(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("competition_policy")
    if not isinstance(policy, dict):
        return ["competition_policy must be an object"]
    failures: list[str] = []
    checks = (
        ("competition_policy_id", "REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_POLICY_V1"),
        ("competition_contract_version", POLICY_VERSION),
        ("selected_handoff_item_count_for_valid_fixture", 1),
        ("eligible_competition_entry_count_for_valid_fixture", 1),
        ("order_intent_surface_authority", ORDER_INTENT_PREVIEW_AUTHORITY),
    )
    for field, expected in checks:
        if policy.get(field) != expected:
            failures.append(f"competition_policy.{field} must be {expected}")
    for field in (
        "stable_sort_required",
        "replay_lane_required_for_eligible_entry",
        "paper_lane_required_for_eligible_entry",
        "shared_input_lock_identity_required",
        "replay_and_paper_lanes_must_be_separate",
        "result_boundary_refs_only",
        "pr91_dual_result_review_required",
        "pr92_owner_live_promotion_review_required",
        "quantum_candidates_require_classical_comparator_or_fallback",
    ):
        if policy.get(field) is not True:
            failures.append(f"competition_policy.{field} must be true")
    for field in (
        "random_identity_allowed",
        "wall_clock_identity_allowed",
        "pr91_dual_result_review_created",
        "pr92_owner_live_promotion_review_created",
        "order_submission_allowed",
        "live_routing_allowed",
        "connector_binding_allowed",
    ):
        if policy.get(field) is not False:
            failures.append(f"competition_policy.{field} must be false")
    if policy.get("deterministic_competition_chain") != list(DETERMINISTIC_COMPETITION_CHAIN):
        failures.append("competition_policy.deterministic_competition_chain mismatch")
    return failures


def validate_blocked_competition_policy(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("blocked_competition_policy")
    if not isinstance(policy, dict):
        return ["blocked_competition_policy must be an object"]
    failures: list[str] = []
    if policy.get("blocked_competition_policy_id") != (
        "REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_BLOCKED_POLICY_V1"
    ):
        failures.append("blocked_competition_policy.blocked_competition_policy_id mismatch")
    if policy.get("blocked_or_rejected_entries_remain_traceable") is not True:
        failures.append("blocked_competition_policy must preserve traceable blocked entries")
    if policy.get("blocked_entries_enter_active_competition_status") is not False:
        failures.append("blocked entries must not enter active competition status")
    if policy.get("blocked_entries_retain_reason_codes") is not True:
        failures.append("blocked entries must retain reason codes")
    if policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
        failures.append("blocked_competition_policy.blocked_reason_code_order mismatch")
    return failures


def validate_no_authority_flags(payload: dict[str, Any], *, prefix: str) -> list[str]:
    flags = payload.get("required_no_authority_flags")
    if not isinstance(flags, dict):
        return [f"{prefix}.required_no_authority_flags must be an object"]
    failures: list[str] = []
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if flags.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: {prefix}.{field} must be false")
    return failures


def validate_gate_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    checks = (
        ("competition_gate_registry_id", GATE_REGISTRY_ID),
        ("replay_paper_candidate_stack_competition_packet_contract_id", GATE_CONTRACT_ID),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("roadmap_pr_label", ROADMAP_PR_LABEL),
        ("github_pr_number_policy", GITHUB_PR_NUMBER_POLICY),
        ("gate_scope", GATE_SCOPE),
        ("policy_version", POLICY_VERSION),
        ("competition_scope", COMPETITION_SCOPE),
        ("competition_authority_class", COMPETITION_AUTHORITY_CLASS),
    )
    for field, expected in checks:
        if payload.get(field) != expected:
            failures.append(f"{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "competition_contract_only_flag",
    ):
        if payload.get(field) is not True:
            failures.append(f"{field} must be true")
    if payload.get("final_ready") is not False:
        failures.append("final_ready must be false")
    if payload.get("required_stack_roles") != list(ROLE_ORDER):
        failures.append("required_stack_roles must match current repo PR87/PR88 role order")
    if payload.get("competition_inputs") != list(COMPETITION_INPUT_ORDER):
        failures.append("competition_inputs mismatch")
    if payload.get("competition_outputs") != list(COMPETITION_OUTPUT_ORDER):
        failures.append("competition_outputs mismatch")
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("reason_codes mismatch")
    if payload.get("stage1_prediction_market_contexts") != ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]:
        failures.append("stage1_prediction_market_contexts mismatch")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_competition_policy(payload))
    failures.extend(validate_blocked_competition_policy(payload))
    failures.extend(validate_no_authority_flags(payload, prefix="registry"))
    for field in (
        "upstream_selected_stack_handoff_packet_ref",
        "stage1_runtime_resolver_to_replay_paper_handoff_ref",
        "stage1_concurrent_replay_paper_contract_ref",
        "stage1_dual_result_review_contract_ref",
    ):
        ref = payload.get(field)
        if not isinstance(ref, dict):
            failures.append(f"{field} must be an object")
            continue
        for ref_field in ("report_path", "validator_path"):
            rel = ref.get(ref_field)
            if not isinstance(rel, str) or not _resolve(repo_root, pathlib.Path(rel)).exists():
                failures.append(f"{field}.{ref_field} path missing: {rel}")
        schema_path = ref.get("schema_path")
        if isinstance(schema_path, str) and not _resolve(repo_root, pathlib.Path(schema_path)).exists():
            failures.append(f"{field}.schema_path path missing: {schema_path}")
    for schema_ref in payload.get("stage1_replay_paper_static_schema_refs", []):
        if not _resolve(repo_root, pathlib.Path(str(schema_ref))).exists():
            failures.append(f"stage1 replay/paper schema ref missing: {schema_ref}")
    principles = _list_of_mappings(payload.get("master_plan_principles_consumed"))
    principle_ids = {str(item.get("principle_id") or "") for item in principles}
    missing = sorted(REQUIRED_MASTER_PLAN_PRINCIPLES - principle_ids)
    if missing:
        failures.append(f"master_plan_principles_consumed missing {', '.join(missing)}")
    return failures


def _validate_report_marker(
    report: dict[str, Any] | None,
    expected_marker: str,
    label: str,
) -> list[str]:
    if report is None:
        return []
    marker = report.get("validation_marker") or report.get("validator_marker")
    if marker != expected_marker:
        return [f"{label} report marker must be {expected_marker}"]
    return []


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr89_upstream_failures, pr89_upstream = pr89_gate.validate_upstream_reports(repo_root)
    failures.extend(pr89_upstream_failures)

    pr89_report, pr89_failures = _load_json_checked(
        repo_root / pr89_gate.DEFAULT_REPORT,
        "PR89_REPORT",
    )
    failures.extend(pr89_failures)
    failures.extend(_validate_report_marker(pr89_report, pr89_gate.SUCCESS_MARKER, "PR89"))
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
    if pr89_report is None:
        return failures, {}

    handoff_packet = pr89_report.get("selected_parameter_stack_handoff_packet")
    if not isinstance(handoff_packet, dict):
        failures.append("PR89 report selected_parameter_stack_handoff_packet missing")
        handoff_packet = {}
    selected_handoff_items = _list_of_mappings(handoff_packet.get("selected_handoff_items"))
    return failures, {
        **pr89_upstream,
        "pr89_report": pr89_report,
        "selected_parameter_stack_handoff_packet": handoff_packet,
        "selected_handoff_items": selected_handoff_items,
        "selected_handoff_items_by_id": _first_by_key(selected_handoff_items, "selected_stack_id"),
        "stage1_static_contract_reports": stage1_reports,
    }


def _case_by_id(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        if case.get("case_id") == case_id:
            return case
    raise ValueError(f"unknown fixture case_id {case_id}")


def _selected_stack_id_for_case(
    handoff_packet: dict[str, Any],
    fixture: dict[str, Any],
    case: dict[str, Any] | None,
) -> str | None:
    if case is not None and "selected_stack_id_override" in case:
        value = case.get("selected_stack_id_override")
        return value if isinstance(value, str) else None
    value = handoff_packet.get("selected_stack_id") or fixture.get("expected_selected_stack_id")
    return value if isinstance(value, str) else None


def _selected_item_for_case(
    selected_stack_id: str | None,
    upstream: dict[str, Any],
    case: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if selected_stack_id is None:
        return None
    item = copy.deepcopy(upstream.get("selected_handoff_items_by_id", {}).get(selected_stack_id))
    if not isinstance(item, dict):
        return None
    if case is None:
        return item
    override_map = {
        "pr90_forwardable_flag_override": "pr90_forwardable_flag",
        "blocker_state_override": "blocker_state",
        "blocked_row_ids_and_reasons_override": "blocked_row_ids_and_reasons",
        "compatibility_state_override": "compatibility_state",
        "required_role_completion_state_override": "required_role_completion_state",
    }
    for case_field, item_field in override_map.items():
        if case_field in case:
            item[item_field] = copy.deepcopy(case.get(case_field))
    if case.get("remove_lineage_trace") is True:
        item["selected_stack_lineage_trace"] = []
    return item


def _entry_lineage_trace(
    item: dict[str, Any],
    handoff_packet: dict[str, Any],
) -> list[dict[str, Any]]:
    if "selected_stack_lineage_trace" in item:
        lineage = item.get("selected_stack_lineage_trace")
        return copy.deepcopy(_list_of_mappings(lineage))
    lineage = handoff_packet.get("selected_stack_lineage_trace")
    return copy.deepcopy(_list_of_mappings(lineage))


def _entry_has_required_lineage(lineage: list[dict[str, Any]]) -> bool:
    artifact_ids = {str(step.get("artifact_id") or "") for step in lineage}
    return {
        "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
        "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
        "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE",
    }.issubset(artifact_ids)


def _block_codes_for_item(
    selected_stack_id: str | None,
    item: dict[str, Any] | None,
    handoff_packet: dict[str, Any],
    fixture: dict[str, Any],
    case: dict[str, Any] | None,
) -> list[str]:
    block_codes: list[str] = []
    if selected_stack_id is None:
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_SELECTED_STACK_ID")
    if selected_stack_id is not None and item is None:
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_ID_NOT_IN_PR89_HANDOFF")
        return _sort_reason_codes(block_codes)
    if item is None:
        return _sort_reason_codes(block_codes)

    if item.get("pr90_forwardable_flag") is not True:
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_NOT_FORWARDABLE_TO_PR90")
    lineage = _entry_lineage_trace(item, handoff_packet)
    if not _entry_has_required_lineage(lineage):
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_NOT_TRACEABLE_TO_PR89_PR88_PR87")
    if item.get("required_role_completion_state") != "ROLE_COMPLETE":
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_REQUIRED_ROLE")
    if item.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_INCOMPATIBLE_SELECTED_STACK")
    if item.get("blocker_state") != "NO_BLOCKERS":
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_SELECTED_STACK_STATUS")
    if _list_of_mappings(item.get("blocked_row_ids_and_reasons")):
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_BLOCKED_ROW_PRESENT")
    if item.get("trade_context_ref") != fixture.get("upstream_trade_context_ref"):
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_ROUTE_MISMATCH")
    if item.get("routed_selection_universe_ref") != fixture.get("upstream_routed_selection_universe_ref"):
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_ROUTE_MISMATCH")
    if item.get("source_dependency_state") not in SOURCE_ALLOWED_STATES:
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_SOURCE_DEPENDENCY_STATE")
    quantum_type = item.get("quantum_candidate_type")
    if quantum_type != "CLASSICAL_ONLY" and not item.get("classical_comparator_ref"):
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_CLASSICAL_COMPARATOR")
    if case is not None:
        if case.get("replay_lane_descriptor_present") is False:
            block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_LANE_MISSING")
        if case.get("paper_lane_descriptor_present") is False:
            block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_PAPER_LANE_MISSING")
        if case.get("input_identity_mismatch") is True:
            block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_AMBIGUOUS_REPLAY_PAPER_INPUT_IDENTITY")
        if case.get("replay_result_packet_created_flag_override") is True:
            block_codes.append(
                "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE"
            )
        if case.get("paper_result_packet_created_flag_override") is True:
            block_codes.append(
                "REPLAY_PAPER_COMPETITION_BLOCKED_REPLAY_PAPER_RESULT_CREATED_IN_STATIC_COMPETITION_SCOPE"
            )
        if case.get("executable_order_intent_created_override") is True:
            block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_EXECUTABLE_ORDER_INTENT_FORBIDDEN")
        if case.get("force_no_competition_entries") is True:
            block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_NO_COMPETITION_ENTRIES")
    return _sort_reason_codes(block_codes)


def _input_identity_digest(
    selected_stack_id: str,
    item: dict[str, Any],
    fixture: dict[str, Any],
) -> str:
    return _digest(
        (
            "PR90_REPLAY_PAPER_INPUT_LOCK",
            selected_stack_id,
            item.get("handoff_item_id"),
            fixture.get("upstream_selected_stack_handoff_packet_ref"),
            item.get("trade_context_ref"),
            item.get("routed_selection_universe_ref"),
            item.get("deterministic_generation_key"),
        )
    )


def _lane_descriptor(
    *,
    lane: str,
    selected_stack_id: str,
    item: dict[str, Any],
    input_lock_id: str,
    input_identity_digest: str,
    result_boundary_ref: str,
) -> dict[str, Any]:
    lane_upper = lane.upper()
    return {
        f"{lane}_lane_input_descriptor_id": (
            f"PR90_{lane_upper}_LANE_INPUT_DESCRIPTOR__{selected_stack_id}"
        ),
        "lane_type": f"{lane_upper}_STATIC_LANE_DESCRIPTOR",
        "selected_stack_id": selected_stack_id,
        "selected_candidate_stack_id": item.get("selected_candidate_stack_id"),
        "replay_paper_input_lock_ref": input_lock_id,
        "replay_paper_input_identity_digest_or_static_ref": input_identity_digest,
        "trade_context_ref": item.get("trade_context_ref"),
        "routed_selection_universe_ref": item.get("routed_selection_universe_ref"),
        "lane_execution_allowed_flag": False,
        f"{lane}_execution_created_flag": False,
        f"{lane}_result_packet_created_flag": False,
        f"{lane}_result_expected_later_flag": True,
        f"{lane}_result_boundary_ref": result_boundary_ref,
        "result_values_created_flag": False,
    }


def _competition_entry(
    selected_stack_id: str,
    item: dict[str, Any],
    handoff_packet: dict[str, Any],
    fixture: dict[str, Any],
    *,
    input_lock_id: str,
    input_identity_digest: str,
    replay_lane_descriptor_id: str,
    paper_lane_descriptor_id: str,
) -> dict[str, Any]:
    quantum_type = str(item.get("quantum_candidate_type") or "CLASSICAL_ONLY")
    competition_role = "SELECTED_STACK"
    if quantum_type != "CLASSICAL_ONLY":
        competition_role = "HYBRID_STATIC_PAIR"
    lineage = _entry_lineage_trace(item, handoff_packet)
    return {
        "competition_entry_id": f"PR90_COMPETITION_ENTRY__{selected_stack_id}",
        "selected_stack_id": selected_stack_id,
        "selected_candidate_stack_id": item.get("selected_candidate_stack_id"),
        "candidate_index": item.get("candidate_index"),
        "deterministic_generation_key": item.get("deterministic_generation_key"),
        "selected_by_pr88_packet_ref": fixture.get("upstream_trade_context_selection_packet_ref"),
        "handoff_by_pr89_packet_ref": fixture.get("upstream_selected_stack_handoff_packet_ref"),
        "candidate_from_pr87_packet_ref": item.get("candidate_from_pr87_packet_ref"),
        "trade_context_ref": item.get("trade_context_ref"),
        "routed_selection_universe_ref": item.get("routed_selection_universe_ref"),
        "venue_scope": item.get("venue_scope"),
        "platform_scope": item.get("platform_scope"),
        "market_type": item.get("market_type"),
        "strategy_class": item.get("strategy_class"),
        "edge_type": item.get("edge_type"),
        "latency_sensitivity_class": item.get("latency_sensitivity_class"),
        "capital_intensity_class": item.get("capital_intensity_class"),
        "source_dependency_state": item.get("source_dependency_state"),
        "required_role_completion_state": item.get("required_role_completion_state"),
        "compatibility_state": item.get("compatibility_state"),
        "blocker_state": item.get("blocker_state"),
        "blocked_row_ids_and_reasons": copy.deepcopy(item.get("blocked_row_ids_and_reasons", [])),
        "signal_family_ids": copy.deepcopy(item.get("signal_family_ids", [])),
        "scoring_family_ids": copy.deepcopy(item.get("scoring_family_ids", [])),
        "normalization_family_ids": copy.deepcopy(item.get("normalization_family_ids", [])),
        "risk_family_ids": copy.deepcopy(item.get("risk_family_ids", [])),
        "execution_family_ids": copy.deepcopy(item.get("execution_family_ids", [])),
        "capital_family_ids": copy.deepcopy(item.get("capital_family_ids", [])),
        "latency_family_ids": copy.deepcopy(item.get("latency_family_ids", [])),
        "error_guard_family_ids": copy.deepcopy(item.get("error_guard_family_ids", [])),
        "quantum_advisory_family_ids": copy.deepcopy(item.get("quantum_advisory_family_ids", [])),
        "scoring_policy_refs": [handoff_packet.get("score_breakdown_ref")],
        "ranking_contract_ref": item.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": item.get("optimizer_arbitration_policy_ref"),
        "quantum_applicability_summary": copy.deepcopy(item.get("quantum_applicability_summary", {})),
        "owner_quantum_priority_summary": copy.deepcopy(item.get("owner_quantum_priority_summary", {})),
        "classical_comparator_required_flag": item.get("classical_comparator_required_flag"),
        "classical_comparator_ref": item.get("classical_comparator_ref"),
        "quantum_candidate_type": quantum_type,
        "competition_role": competition_role,
        "static_competition_pair_id": f"PR90_STATIC_PAIR__{selected_stack_id}__CLASSICAL_COMPARATOR",
        "selected_stack_lineage_trace": lineage,
        "replay_lane_required_flag": True,
        "paper_lane_required_flag": True,
        "replay_lane_input_lock_ref": input_lock_id,
        "paper_lane_input_lock_ref": input_lock_id,
        "replay_lane_input_descriptor_id": replay_lane_descriptor_id,
        "paper_lane_input_descriptor_id": paper_lane_descriptor_id,
        "replay_lane_execution_allowed_flag": False,
        "paper_lane_execution_allowed_flag": False,
        "replay_result_expected_later_flag": True,
        "paper_result_expected_later_flag": True,
        "replay_result_packet_created_flag": False,
        "paper_result_packet_created_flag": False,
        "result_values_created_flag": False,
        "pr91_dual_review_forwardable_flag": False,
        "pr91_dual_review_forwardable_after_future_results_flag": True,
        "order_intent_preview_authority_class": item.get("order_intent_preview_authority_class"),
        "order_intent_preview_allowed_flag": item.get("order_intent_preview_allowed_flag"),
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
    }


def build_replay_paper_candidate_stack_competition_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    case = None if case_id is None else _case_by_id(fixture, case_id)
    handoff_packet = copy.deepcopy(upstream.get("selected_parameter_stack_handoff_packet", {}))
    if case is not None and case.get("handoff_packet_available") is False:
        handoff_packet = {}

    block_codes: list[str] = []
    if not handoff_packet:
        block_codes.append("REPLAY_PAPER_COMPETITION_BLOCKED_MISSING_PR89_HANDOFF_PACKET")
        selected_stack_id = None
        item = None
    else:
        selected_stack_id = _selected_stack_id_for_case(handoff_packet, fixture, case)
        item = _selected_item_for_case(selected_stack_id, upstream, case)
        block_codes.extend(
            _block_codes_for_item(selected_stack_id, item, handoff_packet, fixture, case)
        )

    block_codes = _sort_reason_codes(block_codes)
    ready = not block_codes and selected_stack_id is not None and item is not None
    if ready and case is not None and case.get("force_no_competition_entries") is True:
        ready = False
        block_codes = ["REPLAY_PAPER_COMPETITION_BLOCKED_NO_COMPETITION_ENTRIES"]

    selected_count = len(_list_of_mappings(handoff_packet.get("selected_handoff_items"))) if handoff_packet else 0
    eligible_count = 1 if ready else 0
    blocked_count = 0 if ready else 1
    selected_stack_digest = None
    input_lock_id = None
    input_identity_digest = None
    replay_lane_descriptor_id = None
    paper_lane_descriptor_id = None
    replay_descriptor: dict[str, Any] | None = None
    paper_descriptor: dict[str, Any] | None = None
    competition_entries: list[dict[str, Any]] = []
    if ready:
        assert selected_stack_id is not None
        assert item is not None
        selected_stack_digest = _digest((selected_stack_id, item.get("deterministic_generation_key")))
        input_lock_id = f"PR90_REPLAY_PAPER_INPUT_LOCK__{selected_stack_id}"
        input_identity_digest = _input_identity_digest(selected_stack_id, item, fixture)
        replay_lane_descriptor_id = f"PR90_REPLAY_LANE_INPUT_DESCRIPTOR__{selected_stack_id}"
        paper_lane_descriptor_id = f"PR90_PAPER_LANE_INPUT_DESCRIPTOR__{selected_stack_id}"
        replay_descriptor = _lane_descriptor(
            lane="replay",
            selected_stack_id=selected_stack_id,
            item=item,
            input_lock_id=input_lock_id,
            input_identity_digest=input_identity_digest,
            result_boundary_ref=(
                "src/qtt/stage1_prediction_markets/replay_paper/"
                "replay_result_packet_boundary.schema.json"
            ),
        )
        paper_identity_digest = input_identity_digest
        if case is not None and case.get("input_identity_mismatch") is True:
            paper_identity_digest = _digest((input_identity_digest, "MISMATCH"))
        paper_descriptor = _lane_descriptor(
            lane="paper",
            selected_stack_id=selected_stack_id,
            item=item,
            input_lock_id=input_lock_id,
            input_identity_digest=paper_identity_digest,
            result_boundary_ref=(
                "src/qtt/stage1_prediction_markets/replay_paper/"
                "paper_result_packet_boundary.schema.json"
            ),
        )
        competition_entries = [
            _competition_entry(
                selected_stack_id,
                item,
                handoff_packet,
                fixture,
                input_lock_id=input_lock_id,
                input_identity_digest=input_identity_digest,
                replay_lane_descriptor_id=replay_lane_descriptor_id,
                paper_lane_descriptor_id=paper_lane_descriptor_id,
            )
        ]

    reason_codes = (
        _sort_reason_codes(
            (
                "REPLAY_PAPER_COMPETITION_ALLOWED_STATIC_FIXTURE_ONLY",
                "REPLAY_PAPER_COMPETITION_ALLOWED_PR89_HANDOFF_PACKET",
                "REPLAY_PAPER_COMPETITION_ALLOWED_PR88_SELECTION_PACKET",
                "REPLAY_PAPER_COMPETITION_ALLOWED_PR87_CANDIDATE_PACKET",
                "REPLAY_PAPER_COMPETITION_ALLOWED_TRADE_CONTEXT_ROUTE_LINEAGE",
                "REPLAY_PAPER_COMPETITION_ALLOWED_SCORING_RANKING_ARBITRATION_LINEAGE",
                "REPLAY_PAPER_COMPETITION_ALLOWED_QUANTUM_POLICY_LINEAGE",
                "REPLAY_PAPER_COMPETITION_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
                "REPLAY_PAPER_COMPETITION_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
                "REPLAY_PAPER_COMPETITION_ALLOWED_REPLAY_PAPER_INPUT_LOCK",
                "REPLAY_PAPER_COMPETITION_ALLOWED_SEPARATE_REPLAY_AND_PAPER_LANES",
                "REPLAY_PAPER_COMPETITION_ALLOWED_RESULT_BOUNDARY_REFS_ONLY",
                "REPLAY_PAPER_COMPETITION_ALLOWED_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
                "REPLAY_PAPER_COMPETITION_ALLOWED_PR91_PR92_BOUNDARY_NO_REVIEW_CREATED",
                "REPLAY_PAPER_COMPETITION_ALLOWED_DETERMINISTIC_COMPETITION_IDS",
            )
        )
        if ready
        else block_codes
    )
    packet_status = (
        "STATIC_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_PACKET_READY"
        if ready
        else (block_codes[0] if block_codes else "REPLAY_PAPER_COMPETITION_BLOCKED_NO_COMPETITION_ENTRIES")
    )
    blocked_entries = []
    if not ready:
        blocked_entries.append(
            {
                "competition_entry_id": "BLOCKED_REPLAY_PAPER_COMPETITION_ENTRY",
                "selected_stack_id": selected_stack_id,
                "blocked_reason_codes": block_codes
                or ["REPLAY_PAPER_COMPETITION_BLOCKED_NO_COMPETITION_ENTRIES"],
                "active_competition_created": False,
                "replay_execution_created_flag": False,
                "paper_execution_created_flag": False,
                "replay_result_packet_created_flag": False,
                "paper_result_packet_created_flag": False,
                "order_intent_authority_created": False,
            }
        )

    packet: dict[str, Any] = {
        "replay_paper_candidate_stack_competition_packet_id": fixture.get(
            "replay_paper_candidate_stack_competition_packet_id"
        ),
        "schema_version": fixture.get("schema_version"),
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "competition_scope": COMPETITION_SCOPE,
        "competition_authority_class": COMPETITION_AUTHORITY_CLASS,
        "packet_status": packet_status,
        "fixture_case_id": None if case is None else case.get("case_id"),
        "upstream_selected_stack_handoff_packet_ref": fixture.get(
            "upstream_selected_stack_handoff_packet_ref"
        ),
        "upstream_selected_stack_handoff_packet_digest_or_static_ref": fixture.get(
            "upstream_selected_stack_handoff_packet_digest_or_static_ref"
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
        "selected_stack_id": selected_stack_id if ready else None,
        "selected_candidate_stack_id": item.get("selected_candidate_stack_id") if ready and item else None,
        "selected_candidate_generation_key": (
            item.get("selected_candidate_generation_key") if ready and item else None
        ),
        "selected_stack_lineage_trace": (
            _entry_lineage_trace(item, handoff_packet) if ready and item else []
        ),
        "selected_stack_digest_or_static_ref": selected_stack_digest,
        "competition_manifest_id": fixture.get("competition_manifest_id"),
        "competition_manifest_digest_or_static_ref": _digest(
            (
                fixture.get("competition_manifest_id"),
                selected_stack_id,
                fixture.get("upstream_selected_stack_handoff_packet_ref"),
            )
        ),
        "competition_manifest": {
            "competition_manifest_id": fixture.get("competition_manifest_id"),
            "manifest_scope": "STATIC_SELECTED_STACK_REPLAY_PAPER_COMPETITION_PREPARATION_ONLY",
            "selected_stack_ids": [selected_stack_id] if ready and selected_stack_id else [],
            "replay_lane_descriptor_count": 1 if ready else 0,
            "paper_lane_descriptor_count": 1 if ready else 0,
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "replay_result_packet_count": 0,
            "paper_result_packet_count": 0,
        },
        "replay_paper_input_lock_id": input_lock_id,
        "replay_paper_input_identity_digest_or_static_ref": input_identity_digest,
        "replay_lane_input_descriptor_ref": replay_lane_descriptor_id,
        "paper_lane_input_descriptor_ref": paper_lane_descriptor_id,
        "replay_lane_contract_ref": (
            "src/qtt/stage1_prediction_markets/replay_paper/"
            "concurrent_replay_lane_contract.schema.json"
        ),
        "paper_lane_contract_ref": (
            "src/qtt/stage1_prediction_markets/replay_paper/"
            "concurrent_paper_lane_contract.schema.json"
        ),
        "replay_result_boundary_ref": (
            "src/qtt/stage1_prediction_markets/replay_paper/"
            "replay_result_packet_boundary.schema.json"
        ),
        "paper_result_boundary_ref": (
            "src/qtt/stage1_prediction_markets/replay_paper/"
            "paper_result_packet_boundary.schema.json"
        ),
        "dual_result_review_required_flag": True,
        "pr91_dual_result_review_required_flag": True,
        "pr91_dual_result_review_created_flag": False,
        "pr91_dual_review_forwardable_after_future_results_flag": True,
        "pr92_owner_live_promotion_review_required_flag": True,
        "pr92_owner_live_promotion_review_created_flag": False,
        "owner_review_required_flag": True,
        "owner_approval_created_flag": False,
        "source_dependency_state": fixture.get("source_dependency_state"),
        "source_retrieval_created_flag": False,
        "source_acceptance_created_flag": False,
        "connector_semantic_binding_created_flag": False,
        "runtime_cash_receipt_created_flag": False,
        "optimizer_execution_created_flag": False,
        "classical_optimizer_execution_created_flag": False,
        "quantum_optimizer_execution_created_flag": False,
        "quantum_backend_execution_created_flag": False,
        "quantum_simulator_execution_created_flag": False,
        "replay_execution_created_flag": False,
        "paper_execution_created_flag": False,
        "replay_result_packet_created_flag": False,
        "paper_result_packet_created_flag": False,
        "result_values_created_flag": False,
        "profit_evidence_created_flag": False,
        "live_trade_authority_created_flag": False,
        "order_intent_authority_created": False,
        "order_submission_allowed_flag": False,
        "live_routing_allowed_flag": False,
        "connector_binding_allowed_flag": False,
        "no_order_authority_flag": True,
        "no_runtime_execution_flag": True,
        "no_replay_execution_flag": True,
        "no_paper_execution_flag": True,
        "no_result_packet_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
        "no_live_trade_authority_flag": True,
        "random_identity_used": False,
        "wall_clock_identity_used": False,
        "atomicrows_bundle_jsonl_created": False,
        "atomicrows_bundle_sha256_created": False,
        "selection_reason_codes": reason_codes,
        "selected_handoff_item_count": selected_count,
        "eligible_competition_entry_count": eligible_count,
        "rejected_competition_entry_count": 0,
        "blocked_competition_entry_count": blocked_count,
        "replay_lane_descriptor_count": 1 if ready else 0,
        "paper_lane_descriptor_count": 1 if ready else 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "replay_result_packet_count": 0,
        "paper_result_packet_count": 0,
        "dual_result_review_packet_count": 0,
        "order_authoritative_item_count": 0,
        "competition_entries": competition_entries,
        "blocked_competition_entries": blocked_entries,
        "rejected_competition_entries": [],
        "replay_lane_input_descriptors": [replay_descriptor] if replay_descriptor else [],
        "paper_lane_input_descriptors": [paper_descriptor] if paper_descriptor else [],
        "order_intent_preview_surface": {
            "preview_surface_id": "PR90_INHERITED_NON_AUTHORITATIVE_STATIC_ORDER_INTENT_PREVIEW",
            "authority_class": ORDER_INTENT_PREVIEW_AUTHORITY,
            "inherited_from_pr89_handoff_packet_ref": fixture.get(
                "upstream_selected_stack_handoff_packet_ref"
            ),
            "order_intent_preview_allowed_flag": True,
            "executable_order_intent_created": False,
            "order_submission_allowed_flag": False,
            "live_routing_allowed_flag": False,
            "connector_binding_allowed_flag": False,
        },
        "static_stage1_contract_refs": {
            "runtime_resolver_to_replay_paper_handoff_report": (
                "docs/master_plan/generated/Stage1RuntimeResolverToReplayPaperHandoff.report.json"
            ),
            "concurrent_replay_paper_contract_report": (
                "docs/master_plan/generated/Stage1ConcurrentReplayPaperContractCheck.report.json"
            ),
            "dual_result_review_contract_report": (
                "docs/master_plan/generated/Stage1DualResultReviewContractCheck.report.json"
            ),
        },
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        packet.setdefault(field, False)
    return packet, failures


def validate_competition_packet(packet: dict[str, Any], upstream: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in (
        "no_order_authority_flag",
        "no_runtime_execution_flag",
        "no_replay_execution_flag",
        "no_paper_execution_flag",
        "no_result_packet_flag",
        "no_quantum_backend_execution_flag",
        "no_profit_evidence_flag",
        "no_live_trade_authority_flag",
        "dual_result_review_required_flag",
        "pr91_dual_result_review_required_flag",
        "pr92_owner_live_promotion_review_required_flag",
        "owner_review_required_flag",
    ):
        if packet.get(field) is not True:
            failures.append(f"packet.{field} must be true")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: packet.{field} must be false")
    for field in (
        "replay_execution_count",
        "paper_execution_count",
        "replay_result_packet_count",
        "paper_result_packet_count",
        "dual_result_review_packet_count",
        "order_authoritative_item_count",
    ):
        if packet.get(field) != 0:
            failures.append(f"packet.{field} must be zero")
    entries = _list_of_mappings(packet.get("competition_entries"))
    blocked_entries = _list_of_mappings(packet.get("blocked_competition_entries"))
    ready = packet.get("packet_status") == "STATIC_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_PACKET_READY"
    if ready:
        if len(entries) != 1:
            failures.append("ready competition packet must contain exactly one active entry")
        if blocked_entries:
            failures.append("ready competition packet must not contain blocked entries")
    else:
        if entries:
            failures.append("blocked competition packet must not contain active entries")
        if not blocked_entries:
            failures.append("blocked competition packet must retain blocked diagnostic entry")
    if packet.get("replay_lane_descriptor_count") != len(_list_of_mappings(packet.get("replay_lane_input_descriptors"))):
        failures.append("replay lane descriptor count mismatch")
    if packet.get("paper_lane_descriptor_count") != len(_list_of_mappings(packet.get("paper_lane_input_descriptors"))):
        failures.append("paper lane descriptor count mismatch")
    if ready and entries:
        entry = entries[0]
        replay_descriptors = _list_of_mappings(packet.get("replay_lane_input_descriptors"))
        paper_descriptors = _list_of_mappings(packet.get("paper_lane_input_descriptors"))
        if not replay_descriptors or not paper_descriptors:
            failures.append("ready competition packet requires replay and paper descriptors")
        else:
            replay_descriptor = replay_descriptors[0]
            paper_descriptor = paper_descriptors[0]
            replay_id = replay_descriptor.get("replay_lane_input_descriptor_id")
            paper_id = paper_descriptor.get("paper_lane_input_descriptor_id")
            if replay_id == paper_id:
                failures.append("replay and paper lane descriptors must be separate")
            replay_digest = replay_descriptor.get("replay_paper_input_identity_digest_or_static_ref")
            paper_digest = paper_descriptor.get("replay_paper_input_identity_digest_or_static_ref")
            if replay_digest != paper_digest:
                failures.append("replay/paper lane input identity digest mismatch")
            if entry.get("replay_lane_input_descriptor_id") != replay_id:
                failures.append("entry replay lane descriptor link mismatch")
            if entry.get("paper_lane_input_descriptor_id") != paper_id:
                failures.append("entry paper lane descriptor link mismatch")
        if entry.get("selected_stack_id") not in upstream.get("selected_handoff_items_by_id", {}):
            failures.append("competition entry must derive from PR89 selected handoff item")
        lineage = _list_of_mappings(entry.get("selected_stack_lineage_trace"))
        if not _entry_has_required_lineage(lineage):
            failures.append("competition entry lineage must trace to PR88, PR87, and route")
        if entry.get("required_role_completion_state") != "ROLE_COMPLETE":
            failures.append("competition entry must be role complete")
        if entry.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
            failures.append("competition entry must be compatible")
        if entry.get("blocker_state") != "NO_BLOCKERS":
            failures.append("competition entry must be blocker-free")
        if entry.get("quantum_candidate_type") != "CLASSICAL_ONLY" and not entry.get("classical_comparator_ref"):
            failures.append("quantum-aware competition entry requires classical comparator")
        if entry.get("pr91_dual_review_forwardable_flag") is not False:
            failures.append("PR90 entry must not be forwardable to PR91 before future results")
    preview = packet.get("order_intent_preview_surface")
    if not isinstance(preview, dict):
        failures.append("order_intent_preview_surface must be an object")
    else:
        for field in (
            "order_submission_allowed_flag",
            "live_routing_allowed_flag",
            "connector_binding_allowed_flag",
            "executable_order_intent_created",
        ):
            if preview.get(field) is not False:
                failures.append(f"order_intent_preview_surface.{field} must be false")
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
        ("competition_scope", COMPETITION_SCOPE),
        ("competition_authority_class", COMPETITION_AUTHORITY_CLASS),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "competition_contract_only_flag",
        "no_order_authority_flag",
        "no_runtime_execution_flag",
        "no_replay_execution_flag",
        "no_paper_execution_flag",
        "no_result_packet_flag",
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

    packet, packet_failures = build_replay_paper_candidate_stack_competition_packet(
        registry,
        fixture,
        upstream,
    )
    failures.extend(packet_failures)
    failures.extend(validate_competition_packet(packet, upstream))
    if packet.get("selected_stack_id") != fixture.get("expected_selected_stack_id"):
        failures.append("default fixture selected_stack_id mismatch")
    for count_field in (
        "expected_selected_handoff_item_count",
        "expected_eligible_competition_entry_count",
        "expected_rejected_competition_entry_count",
        "expected_blocked_competition_entry_count",
        "expected_replay_lane_descriptor_count",
        "expected_paper_lane_descriptor_count",
        "expected_replay_execution_count",
        "expected_paper_execution_count",
        "expected_replay_result_packet_count",
        "expected_paper_result_packet_count",
        "expected_dual_result_review_packet_count",
        "expected_order_authoritative_item_count",
    ):
        packet_field = count_field.replace("expected_", "")
        if fixture.get(count_field) != packet.get(packet_field):
            failures.append(f"default fixture {packet_field} mismatch")

    case_packets: list[dict[str, Any]] = []
    for case in cases:
        case_packet, case_failures = build_replay_paper_candidate_stack_competition_packet(
            registry,
            fixture,
            upstream,
            case_id=str(case.get("case_id")),
        )
        failures.extend(case_failures)
        failures.extend(validate_competition_packet(case_packet, upstream))
        expected_id = case.get("expected_selected_stack_id")
        if case_packet.get("selected_stack_id") != expected_id:
            failures.append(f"{case.get('case_id')} selected_stack_id mismatch")
        expected_count = case.get("expected_eligible_competition_entry_count")
        if (
            expected_count is not None
            and case_packet.get("eligible_competition_entry_count") != expected_count
        ):
            failures.append(f"{case.get('case_id')} competition entry count mismatch")
        expected_code = case.get("expected_reason_code")
        reason_codes = list(case_packet.get("selection_reason_codes", []))
        blocked_codes = [
            code
            for item in _list_of_mappings(case_packet.get("blocked_competition_entries"))
            for code in item.get("blocked_reason_codes", [])
        ]
        if expected_code not in reason_codes and expected_code not in blocked_codes:
            failures.append(f"{case.get('case_id')} missing expected reason code {expected_code}")
        case_packets.append(case_packet)

    pr91 = fixture.get("pr91_boundary_fixture")
    if not isinstance(pr91, dict):
        failures.append("fixture.pr91_boundary_fixture must be an object")
    else:
        if pr91.get("competition_packet_forwardable_to_pr91_only_after_future_replay_and_paper_results_exist") is not True:
            failures.append("PR91 boundary fixture must require future replay and paper results")
        for field in (
            "pr91_dual_result_review_created_flag",
            "replay_result_packet_created_in_pr90",
            "paper_result_packet_created_in_pr90",
        ):
            if pr91.get(field) is not False:
                failures.append(f"PR91 boundary fixture {field} must be false")
    pr92 = fixture.get("pr92_boundary_fixture")
    if not isinstance(pr92, dict):
        failures.append("fixture.pr92_boundary_fixture must be an object")
    else:
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
            "REPLAY_PAPER_COMPETITION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
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
            "REPLAY_PAPER_COMPETITION_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
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
    entries = _list_of_mappings(packet.get("competition_entries"))
    entry = entries[0] if entries else {}
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
        "competition_gate_registry_id": registry.get("competition_gate_registry_id"),
        "replay_paper_candidate_stack_competition_packet_contract_id": registry.get(
            "replay_paper_candidate_stack_competition_packet_contract_id"
        ),
        "gate_scope": registry.get("gate_scope"),
        "competition_scope": COMPETITION_SCOPE,
        "competition_authority_class": COMPETITION_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "competition_contract_only_flag": True,
        "competition_inputs": list(COMPETITION_INPUT_ORDER),
        "competition_outputs": list(COMPETITION_OUTPUT_ORDER),
        "competition_policy": copy.deepcopy(registry.get("competition_policy")),
        "blocked_competition_policy": copy.deepcopy(registry.get("blocked_competition_policy")),
        "deterministic_competition_chain": list(DETERMINISTIC_COMPETITION_CHAIN),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "upstream_dependencies": copy.deepcopy(registry.get("upstream_dependencies")),
        "future_consumers": copy.deepcopy(registry.get("future_consumers")),
        "upstream_selected_stack_handoff_packet_ref": copy.deepcopy(
            registry.get("upstream_selected_stack_handoff_packet_ref")
        ),
        "stage1_runtime_resolver_to_replay_paper_handoff_ref": copy.deepcopy(
            registry.get("stage1_runtime_resolver_to_replay_paper_handoff_ref")
        ),
        "stage1_concurrent_replay_paper_contract_ref": copy.deepcopy(
            registry.get("stage1_concurrent_replay_paper_contract_ref")
        ),
        "stage1_dual_result_review_contract_ref": copy.deepcopy(
            registry.get("stage1_dual_result_review_contract_ref")
        ),
        "stage1_replay_paper_static_schema_refs": list(
            registry.get("stage1_replay_paper_static_schema_refs", [])
        ),
        "upstream_selected_stack_handoff_packet_id": upstream.get(
            "selected_parameter_stack_handoff_packet", {}
        ).get("selected_parameter_stack_handoff_packet_id"),
        "upstream_trade_context_selection_packet_id": upstream.get(
            "selected_parameter_stack_handoff_packet", {}
        ).get("upstream_trade_context_selection_packet_ref"),
        "upstream_candidate_generation_packet_id": upstream.get(
            "selected_parameter_stack_handoff_packet", {}
        ).get("upstream_candidate_generation_packet_ref"),
        "replay_paper_candidate_stack_competition_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "master_plan_principles_consumed": copy.deepcopy(
            registry.get("master_plan_principles_consumed")
        ),
        "selected_handoff_item_count": packet.get("selected_handoff_item_count"),
        "eligible_competition_entry_count": packet.get("eligible_competition_entry_count"),
        "rejected_competition_entry_count": packet.get("rejected_competition_entry_count"),
        "blocked_competition_entry_count": packet.get("blocked_competition_entry_count"),
        "replay_lane_descriptor_count": packet.get("replay_lane_descriptor_count"),
        "paper_lane_descriptor_count": packet.get("paper_lane_descriptor_count"),
        "replay_execution_count": packet.get("replay_execution_count"),
        "paper_execution_count": packet.get("paper_execution_count"),
        "replay_result_packet_count": packet.get("replay_result_packet_count"),
        "paper_result_packet_count": packet.get("paper_result_packet_count"),
        "dual_result_review_packet_count": packet.get("dual_result_review_packet_count"),
        "order_authoritative_item_count": packet.get("order_authoritative_item_count"),
        "selected_stack_id": packet.get("selected_stack_id"),
        "selected_candidate_stack_id": packet.get("selected_candidate_stack_id"),
        "selected_candidate_generation_key": packet.get("selected_candidate_generation_key"),
        "selected_stack_lineage_trace": copy.deepcopy(packet.get("selected_stack_lineage_trace", [])),
        "selected_stack_digest_or_static_ref": packet.get("selected_stack_digest_or_static_ref"),
        "competition_manifest_id": packet.get("competition_manifest_id"),
        "competition_manifest_digest_or_static_ref": packet.get(
            "competition_manifest_digest_or_static_ref"
        ),
        "replay_paper_input_lock_id": packet.get("replay_paper_input_lock_id"),
        "replay_paper_input_identity_digest_or_static_ref": packet.get(
            "replay_paper_input_identity_digest_or_static_ref"
        ),
        "replay_lane_input_descriptor_ref": packet.get("replay_lane_input_descriptor_ref"),
        "paper_lane_input_descriptor_ref": packet.get("paper_lane_input_descriptor_ref"),
        "deterministic_static_competition": True,
        "no_randomness": True,
        "no_wall_clock_identity": True,
        "competition_entries_derived_only_from_pr89_handoff_packet": True,
        "selected_stack_lineage_traces_to_pr88_selection_packet": True,
        "selected_stack_lineage_traces_to_pr87_candidate_packet": True,
        "trade_context_and_route_lineage_preserved": True,
        "scoring_ranking_arbitration_lineage_preserved": True,
        "quantum_policy_lineage_preserved": True,
        "classical_comparator_or_fallback_preserved_for_quantum_selected_stack": True,
        "quantum_classical_static_competition_pair_declared": (
            entry.get("competition_role") == "HYBRID_STATIC_PAIR"
        ),
        "blocked_candidates_cannot_enter_active_competition": True,
        "missing_role_candidates_cannot_enter_active_competition": True,
        "incompatible_candidates_cannot_enter_active_competition": True,
        "route_mismatched_candidates_cannot_enter_active_competition": True,
        "owner_override_records_basis_without_external_fact_fabrication": True,
        "order_intent_surface_present_flag": fixture.get("order_intent_surface_present_flag"),
        "order_intent_surface_authority": fixture.get("order_intent_surface_authority"),
        "order_intent_authority_created": False,
        "order_submission_allowed_flag": False,
        "live_routing_allowed_flag": False,
        "connector_binding_allowed_flag": False,
        "dual_result_review_required_flag": packet.get("dual_result_review_required_flag"),
        "pr91_dual_result_review_required_flag": packet.get(
            "pr91_dual_result_review_required_flag"
        ),
        "pr91_dual_result_review_created_flag": False,
        "pr91_forwardability_metadata_created": True,
        "pr91_forwardability_requires_future_replay_and_paper_results": True,
        "pr91_execution_review_created": False,
        "pr92_owner_live_promotion_review_required_flag": packet.get(
            "pr92_owner_live_promotion_review_required_flag"
        ),
        "pr92_owner_live_promotion_review_created_flag": False,
        "pr92_owner_review_created": False,
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

    metadata_failures, metadata = validate_pr90_roadmap_metadata(repo_root)
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
