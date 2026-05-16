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

from tools import validate_trade_context_parameter_stack_selection_gate as pr88_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "selected_parameter_stack_handoff_packet.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "SelectedParameterStackHandoffPacket.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_selected_parameter_stack_handoff_packet.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "SelectedParameterStackHandoffPacket.report.json"
)

ROADMAP_INDEX = pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

HANDOFF_REGISTRY_ID = "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET"
HANDOFF_CONTRACT_ID = "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_V1"
REPORT_ID = "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #89"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-SELECTED-PARAMETER-STACK-HANDOFF-PACKET"
TARGET_BRANCH = "pr89-selected-parameter-stack-handoff-packet"
EXPECTED_BASELINE_ANCESTOR = "df06d72"
GATE_SCOPE = "STATIC_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_ONLY"
HANDOFF_SCOPE = "STATIC_ONLY"
HANDOFF_AUTHORITY_CLASS = (
    "STATIC_SELECTED_PARAMETER_STACK_HANDOFF_NOT_ORDER_INTENT_NOT_EXECUTION"
)
ORDER_INTENT_PREVIEW_AUTHORITY = "NON_AUTHORITATIVE_STATIC_PREVIEW_ONLY"
SUCCESS_MARKER = "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_OK"
FAILURE_MARKER = "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_MODE_ACTIVE"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    "DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_ACTIVE"
)

ROLE_ORDER = pr88_gate.ROLE_ORDER
DEPENDENCY_ORDER = (
    "PR77_EDGE_PARAMETER_STACK_SELECTION_PACKET",
    "PR78_QTT_TRADE_CONTEXT_PACKET",
    "PR79_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY",
    "PR80_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE",
    "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE",
    "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY",
    "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY",
    "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY",
    "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE",
    "PR86_QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE",
    "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
    "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
)
DEPENDENCY_MARKERS = {
    "PR77_EDGE_PARAMETER_STACK_SELECTION_PACKET": "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK",
    "PR78_QTT_TRADE_CONTEXT_PACKET": "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK",
    "PR79_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY": "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_OK",
    "PR80_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE": "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK",
    "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE": "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK",
    "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY": "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK",
    "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY": "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK",
    "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY": "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK",
    "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE": "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK",
    "PR86_QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE": "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK",
    "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE": "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK",
    "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE": "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK",
}
FUTURE_CONSUMER_ORDER = (
    "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
    "PR105_PR151_STAGE1_RUNTIME_LIVE_LAUNCH_CLOSURE_CONSUMERS",
)
HANDOFF_INPUT_ORDER = (
    "PR88_static_trade_context_parameter_stack_selection_packet",
    "PR87_static_candidate_generation_packet",
    "PR78_static_trade_context_packet_metadata",
    "PR81_routed_selection_universe_metadata",
    "PR82_quantum_applicability_metadata",
    "PR83_owner_quantum_priority_policy_metadata",
    "PR84_scoring_policy_registry",
    "PR85_static_scoring_ranking_metadata",
    "PR86_static_optimizer_arbitration_metadata",
    "PR73_PR74_PR75_role_completeness_and_compatibility_metadata",
)
HANDOFF_OUTPUT_ORDER = (
    "static_selected_parameter_stack_handoff_packet",
    "selected_stack_handoff_item_descriptors",
    "selected_stack_lineage_trace",
    "non_authoritative_order_intent_preview_surface",
    "pr90_forwardable_metadata",
    "replay_paper_input_lock_required_boundary",
    "no_order_authority_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "no_profit_evidence_boundary",
)
DETERMINISTIC_TIE_BREAK_CHAIN = (
    "PR88_selected_candidate_stack_id_required",
    "PR88_static_selected_candidate_descriptor_required",
    "PR88_selected_candidate_must_be_eligible",
    "PR87_candidate_generation_packet_trace_required",
    "trade_context_and_route_lineage_required",
    "role_completion_and_compatibility_required",
    "blocked_rows_absent",
    "source_dependency_state_static_only",
    "scoring_ranking_arbitration_lineage_required",
    "quantum_policy_lineage_with_classical_comparator_or_fallback",
    "owner_override_internal_basis_only_when_recorded",
    "PR90_forwardability_metadata_required",
    "non_authoritative_order_intent_preview_only",
    "lexicographic_selected_stack_id",
)
REASON_CODE_ORDER = (
    "SELECTED_STACK_HANDOFF_ALLOWED_STATIC_FIXTURE_ONLY",
    "SELECTED_STACK_HANDOFF_ALLOWED_PR88_SELECTION_PACKET",
    "SELECTED_STACK_HANDOFF_ALLOWED_PR87_CANDIDATE_PACKET",
    "SELECTED_STACK_HANDOFF_ALLOWED_TRADE_CONTEXT_LINEAGE",
    "SELECTED_STACK_HANDOFF_ALLOWED_ROUTED_SELECTION_UNIVERSE_LINEAGE",
    "SELECTED_STACK_HANDOFF_ALLOWED_SCORING_RANKING_LINEAGE",
    "SELECTED_STACK_HANDOFF_ALLOWED_OPTIMIZER_ARBITRATION_LINEAGE",
    "SELECTED_STACK_HANDOFF_ALLOWED_QUANTUM_POLICY_LINEAGE",
    "SELECTED_STACK_HANDOFF_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
    "SELECTED_STACK_HANDOFF_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
    "SELECTED_STACK_HANDOFF_ALLOWED_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
    "SELECTED_STACK_HANDOFF_ALLOWED_PR90_FORWARDABLE_NOT_EXECUTED",
    "SELECTED_STACK_HANDOFF_ALLOWED_DETERMINISTIC_TIE_BREAK",
    "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_PR88_SELECTION_PACKET",
    "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_SELECTED_STACK_ID",
    "SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_STACK_ID_NOT_IN_PR88_SELECTION",
    "SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_CANDIDATE_NOT_TRACEABLE_TO_PR87",
    "SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_CANDIDATE_STATUS",
    "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_REQUIRED_ROLE",
    "SELECTED_STACK_HANDOFF_BLOCKED_INCOMPATIBLE_CANDIDATE",
    "SELECTED_STACK_HANDOFF_BLOCKED_BLOCKED_ROW_PRESENT",
    "SELECTED_STACK_HANDOFF_BLOCKED_ROUTE_MISMATCH",
    "SELECTED_STACK_HANDOFF_BLOCKED_SOURCE_DEPENDENCY_STATE",
    "SELECTED_STACK_HANDOFF_BLOCKED_MISSING_CLASSICAL_COMPARATOR",
    "SELECTED_STACK_HANDOFF_BLOCKED_NO_ELIGIBLE_HANDOFF_ITEM",
    "SELECTED_STACK_HANDOFF_BLOCKED_AMBIGUOUS_SELECTED_STACK_LINEAGE",
    "SELECTED_STACK_HANDOFF_BLOCKED_RANDOM_IDENTITY_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_WALL_CLOCK_IDENTITY_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_ORDER_INTENT_AUTHORITY_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_ORDER_SUBMISSION_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_REPLAY_PAPER_RESULTS_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_OWNER_APPROVAL_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "SELECTED_STACK_HANDOFF_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR89_METADATA_VERIFIED",
    "PASS_VALID_SELECTED_STACK_HANDOFF_FROM_PR88_SELECTION",
    "PASS_SELECTED_STACK_LINEAGE_TO_PR87_AND_PR88",
    "PASS_QUANTUM_PREFERRED_WITH_CLASSICAL_COMPARATOR",
    "PASS_OWNER_OVERRIDE_INTERNAL_BASIS",
    "PASS_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
    "PASS_REPLAY_PAPER_FORWARDABLE_NO_EXECUTION",
    "BLOCK_MISSING_PR88_SELECTION_PACKET",
    "BLOCK_MISSING_SELECTED_STACK_ID",
    "BLOCK_UNTRACEABLE_SELECTED_STACK_ID",
    "BLOCK_SELECTED_CANDIDATE_NOT_TRACEABLE_TO_PR87",
    "BLOCK_BLOCKED_CANDIDATE",
    "BLOCK_INCOMPATIBLE_CANDIDATE",
    "BLOCK_MISSING_ROLE_CANDIDATE",
    "BLOCK_NO_ELIGIBLE_HANDOFF_ITEM",
    "PASS_PR90_BOUNDARY_FORWARDABLE_NOT_EXECUTED",
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
    "selected_stack_handoff_packet_is_executable_order_intent",
    "selected_stack_handoff_packet_is_live_order_authority",
    "selected_stack_handoff_packet_is_replay_result",
    "selected_stack_handoff_packet_is_paper_result",
    "order_intent_preview_is_authoritative",
    "pr90_execution_created",
)
FIELD_REASON_CODES = {
    "order_intent_authority_created": "SELECTED_STACK_HANDOFF_BLOCKED_ORDER_INTENT_AUTHORITY_FORBIDDEN",
    "order_submission_allowed_flag": "SELECTED_STACK_HANDOFF_BLOCKED_ORDER_SUBMISSION_FORBIDDEN",
    "live_routing_allowed_flag": "SELECTED_STACK_HANDOFF_BLOCKED_LIVE_ROUTING_FORBIDDEN",
    "connector_binding_allowed_flag": "SELECTED_STACK_HANDOFF_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "source_retrieval_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "source_acceptance_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "connector_semantic_binding_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_ORDER_INTENT_AUTHORITY_FORBIDDEN",
    "replay_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "paper_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "replay_result_packet_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_REPLAY_PAPER_RESULTS_FORBIDDEN",
    "paper_result_packet_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_REPLAY_PAPER_RESULTS_FORBIDDEN",
    "classical_optimizer_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_backend_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN",
    "owner_approval_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_OWNER_APPROVAL_FORBIDDEN",
    "live_trade_authority_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "live_promotion_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_LIVE_PROMOTION_FORBIDDEN",
    "profit_evidence_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "execution_superiority_claim_created_flag": "SELECTED_STACK_HANDOFF_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "random_identity_used": "SELECTED_STACK_HANDOFF_BLOCKED_RANDOM_IDENTITY_FORBIDDEN",
    "wall_clock_identity_used": "SELECTED_STACK_HANDOFF_BLOCKED_WALL_CLOCK_IDENTITY_FORBIDDEN",
    "atomicrows_bundle_jsonl_created": "SELECTED_STACK_HANDOFF_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "SELECTED_STACK_HANDOFF_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
}
SOURCE_ALLOWED_STATES = {"STATIC_SOURCE_DEPENDENCY_LABELS_ONLY"}


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
    return pr88_gate.load_yaml(path)


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


def _sort_by_order(values: Iterable[str], order: Sequence[str]) -> list[str]:
    order_index = {value: index for index, value in enumerate(order)}
    return sorted(
        (str(value) for value in values),
        key=lambda item: (order_index.get(item, 999), item),
    )


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order(codes, REASON_CODE_ORDER)


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
    return int(match.group("number")) > 89


def validate_pr89_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 89), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 89), None)
    if roadmap_entry is None:
        failures.append("PR89 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR89 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Selected parameter-stack handoff packet"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Selected parameter-stack handoff packet"),
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
        failures.append("upstream_dependencies must use canonical PR77-PR88 dependency order")
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
        failures.append("future_consumers must use canonical PR90/PR91/PR92/Stage1 consumer order")
    for consumer in _list_of_mappings(payload.get("future_consumers")):
        if consumer.get("pr89_creates_consumer_execution") is not False:
            failures.append(f"{consumer.get('consumer_id')} pr89_creates_consumer_execution must be false")
    return failures


def validate_handoff_policy(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("handoff_policy")
    if not isinstance(policy, dict):
        return ["handoff_policy must be an object"]
    failures: list[str] = []
    checks = (
        ("handoff_policy_id", "SELECTED_PARAMETER_STACK_HANDOFF_POLICY_V1"),
        ("handoff_contract_version", POLICY_VERSION),
        ("selected_handoff_item_count_for_valid_fixture", 1),
        ("order_intent_surface_authority", ORDER_INTENT_PREVIEW_AUTHORITY),
    )
    for field, expected in checks:
        if policy.get(field) != expected:
            failures.append(f"handoff_policy.{field} must be {expected}")
    for field in (
        "stable_sort_required",
        "replay_paper_competition_required_for_selected_handoff",
        "replay_paper_input_lock_required_for_selected_handoff",
        "pr90_competition_gate_required_for_selected_handoff",
        "owner_review_required_for_selected_handoff",
        "quantum_candidates_require_classical_comparator_or_fallback",
    ):
        if policy.get(field) is not True:
            failures.append(f"handoff_policy.{field} must be true")
    for field in (
        "random_identity_allowed",
        "wall_clock_identity_allowed",
        "order_submission_allowed",
        "live_routing_allowed",
        "connector_binding_allowed",
    ):
        if policy.get(field) is not False:
            failures.append(f"handoff_policy.{field} must be false")
    if policy.get("deterministic_tie_break_chain") != list(DETERMINISTIC_TIE_BREAK_CHAIN):
        failures.append("handoff_policy.deterministic_tie_break_chain mismatch")
    return failures


def validate_blocked_handoff_policy(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("blocked_handoff_policy")
    if not isinstance(policy, dict):
        return ["blocked_handoff_policy must be an object"]
    failures: list[str] = []
    if policy.get("blocked_handoff_policy_id") != "SELECTED_PARAMETER_STACK_HANDOFF_BLOCKED_POLICY_V1":
        failures.append("blocked_handoff_policy_id mismatch")
    for field in ("blocked_or_rejected_candidates_remain_traceable", "blocked_candidates_retain_reason_codes"):
        if policy.get(field) is not True:
            failures.append(f"blocked_handoff_policy.{field} must be true")
    if policy.get("blocked_candidates_enter_active_handoff_status") is not False:
        failures.append("blocked_handoff_policy.blocked_candidates_enter_active_handoff_status must be false")
    if policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
        failures.append("blocked_handoff_policy.blocked_reason_code_order mismatch")
    return failures


def validate_no_authority_flags(payload: dict[str, Any], prefix: str = "payload") -> list[str]:
    failures: list[str] = []
    flags = payload.get("required_no_authority_flags", payload)
    if not isinstance(flags, dict):
        return [f"{prefix}.required_no_authority_flags must be an object"]
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if flags.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: {prefix}.{field} must be false")
    return failures


def validate_gate_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    checks = (
        ("handoff_registry_id", HANDOFF_REGISTRY_ID),
        ("selected_parameter_stack_handoff_packet_contract_id", HANDOFF_CONTRACT_ID),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("roadmap_pr_label", ROADMAP_PR_LABEL),
        ("github_pr_number_policy", GITHUB_PR_NUMBER_POLICY),
        ("gate_scope", GATE_SCOPE),
        ("policy_version", POLICY_VERSION),
        ("handoff_scope", HANDOFF_SCOPE),
        ("handoff_authority_class", HANDOFF_AUTHORITY_CLASS),
    )
    for field, expected in checks:
        if payload.get(field) != expected:
            failures.append(f"{field} must be {expected}")
    for field in ("static_only_flag", "metadata_only_flag", "synthetic_fixture_only_flag", "handoff_contract_only_flag"):
        if payload.get(field) is not True:
            failures.append(f"{field} must be true")
    if payload.get("final_ready") is not False:
        failures.append("final_ready must be false")
    if payload.get("required_stack_roles") != list(ROLE_ORDER):
        failures.append("required_stack_roles must match current repo PR87/PR88 role order")
    if payload.get("handoff_inputs") != list(HANDOFF_INPUT_ORDER):
        failures.append("handoff_inputs mismatch")
    if payload.get("handoff_outputs") != list(HANDOFF_OUTPUT_ORDER):
        failures.append("handoff_outputs mismatch")
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("reason_codes mismatch")
    if payload.get("stage1_prediction_market_contexts") != ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]:
        failures.append("stage1_prediction_market_contexts mismatch")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_handoff_policy(payload))
    failures.extend(validate_blocked_handoff_policy(payload))
    failures.extend(validate_no_authority_flags(payload, prefix="registry"))
    source_ref_fields = (
        "upstream_edge_parameter_stack_selection_packet_ref",
        "upstream_trade_context_packet_ref",
        "upstream_selection_universe_registry_ref",
        "upstream_selection_universe_consumer_gate_ref",
        "upstream_trade_context_routing_gate_ref",
        "upstream_quantum_applicability_ref",
        "upstream_owner_quantum_priority_ref",
        "upstream_scoring_policy_ref",
        "upstream_scoring_ranking_gate_ref",
        "upstream_optimizer_arbitration_ref",
        "upstream_candidate_generation_gate_ref",
        "upstream_trade_context_selection_gate_ref",
    )
    for field in source_ref_fields:
        ref = payload.get(field)
        if not isinstance(ref, dict):
            failures.append(f"{field} must be an object")
            continue
        marker = DEPENDENCY_MARKERS.get(str(ref.get("artifact_id") or ""))
        if marker is not None and ref.get("validation_marker") != marker:
            failures.append(f"{field}.validation_marker must be {marker}")
    principles = _list_of_mappings(payload.get("master_plan_principles_consumed"))
    principle_ids = {str(item.get("principle_id") or "") for item in principles}
    required_principles = {
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
        "REPLAY_PAPER_REQUIRED_BEFORE_LIVE_PROMOTION",
        "OWNER_REVIEW_AND_APPROVAL_REMAIN_LATER_GATES",
        "NO_FABRICATION_BOUNDARY",
    }
    missing = sorted(required_principles - principle_ids)
    if missing:
        failures.append(f"master_plan_principles_consumed missing {', '.join(missing)}")
    return failures


def _validate_report_marker(report: dict[str, Any] | None, marker: str, label: str) -> list[str]:
    if report is None:
        return [f"{label} report missing"]
    if report.get("validation_marker") != marker:
        return [f"{label} report validation_marker must be {marker}"]
    return []


def _first_by_key(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        item_key = item.get(key)
        if isinstance(item_key, str) and item_key not in result:
            result[item_key] = item
    return result


def validate_upstream_reports(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr88_upstream_failures, pr88_upstream = pr88_gate.validate_upstream_reports(repo_root)
    failures.extend(pr88_upstream_failures)

    pr87_report, pr87_failures = _load_json_checked(
        repo_root / "docs" / "master_plan" / "generated" / "CandidateParameterStackGenerationGate.report.json",
        "PR87_REPORT",
    )
    pr88_report, pr88_failures = _load_json_checked(
        repo_root / "docs" / "master_plan" / "generated" / "TradeContextParameterStackSelectionGate.report.json",
        "PR88_REPORT",
    )
    failures.extend(pr87_failures)
    failures.extend(pr88_failures)
    failures.extend(_validate_report_marker(pr87_report, "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK", "PR87"))
    failures.extend(_validate_report_marker(pr88_report, "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK", "PR88"))
    if pr87_report is None or pr88_report is None:
        return failures, {}

    selection_packet = pr88_report.get("trade_context_parameter_stack_selection_packet")
    if not isinstance(selection_packet, dict):
        failures.append("PR88 report trade_context_parameter_stack_selection_packet missing")
        selection_packet = {}
    candidate_packet = pr87_report.get("candidate_generation_packet")
    if not isinstance(candidate_packet, dict):
        failures.append("PR87 report candidate_generation_packet missing")
        candidate_packet = {}
    candidate_stacks = _list_of_mappings(candidate_packet.get("candidate_stacks"))
    evaluated_candidates = _list_of_mappings(selection_packet.get("evaluated_candidates"))
    selected_descriptor = selection_packet.get("static_selected_candidate_descriptor")
    if selected_descriptor is not None and not isinstance(selected_descriptor, dict):
        failures.append("PR88 selected descriptor must be an object when present")
        selected_descriptor = None

    return failures, {
        **pr88_upstream,
        "pr87_report": pr87_report,
        "pr88_report": pr88_report,
        "candidate_generation_packet": candidate_packet,
        "trade_context_selection_packet": selection_packet,
        "pr87_candidate_stack_ids": [str(item.get("candidate_stack_id") or "") for item in candidate_stacks],
        "pr87_active_candidate_stack_ids": list(candidate_packet.get("active_candidate_stack_ids", [])),
        "pr87_blocked_candidate_stack_ids": list(candidate_packet.get("blocked_candidate_stack_ids", [])),
        "pr88_evaluated_candidates_by_id": _first_by_key(evaluated_candidates, "candidate_stack_id"),
        "pr87_candidates_by_id": _first_by_key(candidate_stacks, "candidate_stack_id"),
        "pr88_selected_descriptor": selected_descriptor,
    }


def _case_by_id(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        if case.get("case_id") == case_id:
            return case
    raise ValueError(f"unknown fixture case_id {case_id}")


def _selected_stack_id_for_case(
    selection_packet: dict[str, Any], case: dict[str, Any] | None
) -> str | None:
    if case is not None and "selected_stack_id_override" in case:
        value = case.get("selected_stack_id_override")
        return value if isinstance(value, str) else None
    value = selection_packet.get("static_selected_candidate_stack_id")
    if value is None:
        value = selection_packet.get("selected_candidate_stack_id")
    return value if isinstance(value, str) else None


def _selected_descriptor_for_case(
    selected_stack_id: str | None,
    selection_packet: dict[str, Any],
    upstream: dict[str, Any],
    case: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if selected_stack_id is None:
        return None
    evaluated_by_id = dict(upstream.get("pr88_evaluated_candidates_by_id", {}))
    if case is not None and case.get("inject_pr88_selected_descriptor_without_pr87_trace") is True:
        source = selection_packet.get("static_selected_candidate_descriptor")
        if isinstance(source, dict):
            injected = copy.deepcopy(source)
            injected["candidate_stack_id"] = selected_stack_id
            injected["selected_flag"] = True
            evaluated_by_id[selected_stack_id] = injected
    selected_descriptor = selection_packet.get("static_selected_candidate_descriptor")
    if isinstance(selected_descriptor, dict) and selected_descriptor.get("candidate_stack_id") == selected_stack_id:
        return copy.deepcopy(selected_descriptor)
    descriptor = evaluated_by_id.get(selected_stack_id)
    return copy.deepcopy(descriptor) if isinstance(descriptor, dict) else None


def _quantum_candidate_has_comparator(
    descriptor: dict[str, Any],
    upstream: dict[str, Any],
) -> bool:
    if descriptor.get("quantum_candidate_type") == "CLASSICAL_ONLY":
        return True
    comparator_ref = descriptor.get("classical_comparator_ref")
    if not isinstance(comparator_ref, str) or not comparator_ref:
        return False
    candidates_by_id = upstream.get("pr87_candidates_by_id", {})
    candidates = list(candidates_by_id.values()) if isinstance(candidates_by_id, dict) else []
    for candidate in _list_of_mappings(candidates):
        if candidate.get("seed_descriptor_id") == comparator_ref and candidate.get("candidate_status") == "ACTIVE_CANDIDATE_STACK":
            return True
    return False


def _block_codes_for_selected_descriptor(
    selected_stack_id: str | None,
    descriptor: dict[str, Any] | None,
    upstream: dict[str, Any],
    case: dict[str, Any] | None,
) -> list[str]:
    if case is not None and case.get("no_eligible_handoff_item_case") is True:
        return ["SELECTED_STACK_HANDOFF_BLOCKED_NO_ELIGIBLE_HANDOFF_ITEM"]
    if selected_stack_id is None:
        return ["SELECTED_STACK_HANDOFF_BLOCKED_MISSING_SELECTED_STACK_ID"]
    if descriptor is None:
        return ["SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_STACK_ID_NOT_IN_PR88_SELECTION"]
    codes: list[str] = []
    if selected_stack_id not in set(upstream.get("pr87_candidate_stack_ids", [])):
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_CANDIDATE_NOT_TRACEABLE_TO_PR87")
    if descriptor.get("candidate_status") != "ACTIVE_CANDIDATE_STACK":
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_SELECTED_CANDIDATE_STATUS")
    if descriptor.get("required_role_completion_state") != "ROLE_COMPLETE":
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_MISSING_REQUIRED_ROLE")
    if descriptor.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_INCOMPATIBLE_CANDIDATE")
    if descriptor.get("blocked_row_ids_and_reasons"):
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_BLOCKED_ROW_PRESENT")
    if descriptor.get("route_match_state") != "ROUTE_MATCH":
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_ROUTE_MISMATCH")
    if descriptor.get("source_dependency_state") not in SOURCE_ALLOWED_STATES:
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_SOURCE_DEPENDENCY_STATE")
    if not _quantum_candidate_has_comparator(descriptor, upstream):
        codes.append("SELECTED_STACK_HANDOFF_BLOCKED_MISSING_CLASSICAL_COMPARATOR")
    return _sort_reason_codes(codes)


def _selected_role_families(descriptor: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "SIGNAL": copy.deepcopy(descriptor.get("signal_family_ids", [])),
        "SCORING": copy.deepcopy(descriptor.get("scoring_family_ids", [])),
        "NORMALIZATION": copy.deepcopy(descriptor.get("normalization_family_ids", [])),
        "RISK": copy.deepcopy(descriptor.get("risk_family_ids", [])),
        "EXECUTION": copy.deepcopy(descriptor.get("execution_family_ids", [])),
        "CAPITAL": copy.deepcopy(descriptor.get("capital_family_ids", [])),
        "LATENCY": copy.deepcopy(descriptor.get("latency_family_ids", [])),
        "ERROR_GUARD": copy.deepcopy(descriptor.get("error_guard_family_ids", [])),
        "QUANTUM_ADVISORY": copy.deepcopy(descriptor.get("quantum_advisory_family_ids", [])),
    }


def _selected_parameter_families(descriptor: dict[str, Any]) -> list[str]:
    families: list[str] = []
    for values in _selected_role_families(descriptor).values():
        families.extend(str(value) for value in values)
    return sorted(dict.fromkeys(families))


def _selected_algorithm_families(descriptor: dict[str, Any]) -> list[str]:
    families = []
    families.extend(str(value) for value in descriptor.get("scoring_family_ids", []))
    families.extend(str(value) for value in descriptor.get("quantum_advisory_family_ids", []))
    return sorted(dict.fromkeys(families))


def _score_breakdown(descriptor: dict[str, Any]) -> dict[str, Any]:
    score = descriptor.get("score_metadata")
    if not isinstance(score, dict):
        return {}
    breakdown = score.get("score_breakdown")
    return copy.deepcopy(breakdown) if isinstance(breakdown, dict) else {}


def _owner_override_applied(descriptor: dict[str, Any]) -> bool:
    summary = descriptor.get("owner_quantum_priority_summary")
    if not isinstance(summary, dict):
        return False
    return summary.get("owner_override_basis") not in (None, "", "NONE")


def _handoff_item(
    selected_stack_id: str,
    descriptor: dict[str, Any],
    fixture: dict[str, Any],
    selection_packet: dict[str, Any],
) -> dict[str, Any]:
    item = {
        "handoff_item_id": f"PR89_HANDOFF_ITEM__{selected_stack_id}",
        "selected_stack_id": selected_stack_id,
        "selected_candidate_stack_id": selected_stack_id,
        "candidate_index": descriptor.get("candidate_index"),
        "deterministic_generation_key": descriptor.get("deterministic_generation_key"),
        "selected_by_pr88_packet_ref": selection_packet.get("trade_context_parameter_stack_selection_packet_id"),
        "candidate_from_pr87_packet_ref": fixture.get("upstream_candidate_generation_packet_ref"),
        "trade_context_ref": selection_packet.get("trade_context_ref"),
        "routed_selection_universe_ref": selection_packet.get("routed_selection_universe_ref"),
        "venue_scope": descriptor.get("venue_scope"),
        "platform_scope": descriptor.get("platform_scope"),
        "market_type": descriptor.get("market_type"),
        "strategy_class": descriptor.get("strategy_class"),
        "edge_type": descriptor.get("edge_type"),
        "latency_sensitivity_class": descriptor.get("latency_sensitivity_class"),
        "capital_intensity_class": descriptor.get("capital_intensity_class"),
        "source_dependency_state": descriptor.get("source_dependency_state"),
        "required_role_completion_state": descriptor.get("required_role_completion_state"),
        "compatibility_state": descriptor.get("compatibility_state"),
        "blocker_state": descriptor.get("blocker_state"),
        "blocked_row_ids_and_reasons": copy.deepcopy(descriptor.get("blocked_row_ids_and_reasons", [])),
        "signal_family_ids": copy.deepcopy(descriptor.get("signal_family_ids", [])),
        "scoring_family_ids": copy.deepcopy(descriptor.get("scoring_family_ids", [])),
        "normalization_family_ids": copy.deepcopy(descriptor.get("normalization_family_ids", [])),
        "risk_family_ids": copy.deepcopy(descriptor.get("risk_family_ids", [])),
        "execution_family_ids": copy.deepcopy(descriptor.get("execution_family_ids", [])),
        "capital_family_ids": copy.deepcopy(descriptor.get("capital_family_ids", [])),
        "latency_family_ids": copy.deepcopy(descriptor.get("latency_family_ids", [])),
        "error_guard_family_ids": copy.deepcopy(descriptor.get("error_guard_family_ids", [])),
        "quantum_advisory_family_ids": copy.deepcopy(descriptor.get("quantum_advisory_family_ids", [])),
        "scoring_policy_refs": copy.deepcopy(descriptor.get("scoring_policy_refs", [])),
        "ranking_contract_ref": descriptor.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": descriptor.get("optimizer_arbitration_policy_ref"),
        "quantum_applicability_summary": copy.deepcopy(descriptor.get("quantum_applicability_summary", {})),
        "owner_quantum_priority_summary": copy.deepcopy(descriptor.get("owner_quantum_priority_summary", {})),
        "classical_comparator_required_flag": descriptor.get("classical_comparator_required_flag"),
        "classical_comparator_ref": descriptor.get("classical_comparator_ref"),
        "quantum_candidate_type": descriptor.get("quantum_candidate_type"),
        "pr90_forwardable_flag": True,
        "replay_lane_contract_required_flag": True,
        "paper_lane_contract_required_flag": True,
        "order_intent_preview_allowed_flag": True,
        "order_intent_preview_authority_class": ORDER_INTENT_PREVIEW_AUTHORITY,
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        item[field] = False
    return item


def _lineage_trace(
    selected_stack_id: str,
    descriptor: dict[str, Any],
    fixture: dict[str, Any],
    selection_packet: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "lineage_step": 1,
            "artifact_id": "PR88_QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
            "packet_ref": selection_packet.get("trade_context_parameter_stack_selection_packet_id"),
            "selected_candidate_stack_id": selected_stack_id,
            "static_ref": fixture.get("upstream_trade_context_selection_packet_digest_or_static_ref"),
        },
        {
            "lineage_step": 2,
            "artifact_id": "PR87_QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
            "packet_ref": fixture.get("upstream_candidate_generation_packet_ref"),
            "candidate_stack_id": selected_stack_id,
            "deterministic_generation_key": descriptor.get("deterministic_generation_key"),
            "static_ref": fixture.get("upstream_candidate_generation_packet_digest_or_static_ref"),
        },
        {
            "lineage_step": 3,
            "artifact_id": "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE",
            "trade_context_ref": selection_packet.get("trade_context_ref"),
            "routed_selection_universe_ref": selection_packet.get("routed_selection_universe_ref"),
        },
        {
            "lineage_step": 4,
            "artifact_id": "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE",
            "ranking_contract_ref": descriptor.get("ranking_contract_ref"),
            "score_breakdown_ref": descriptor.get("ranking_contract_score_ref"),
        },
        {
            "lineage_step": 5,
            "artifact_id": "PR86_QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE",
            "optimizer_arbitration_policy_ref": descriptor.get("optimizer_arbitration_policy_ref"),
            "optimizer_arbitration_static_ref": descriptor.get("optimizer_arbitration_static_ref"),
        },
        {
            "lineage_step": 6,
            "artifact_id": "PR82_PR83_QUANTUM_POLICY_LINEAGE",
            "quantum_applicability_summary": copy.deepcopy(descriptor.get("quantum_applicability_summary", {})),
            "owner_quantum_priority_summary": copy.deepcopy(descriptor.get("owner_quantum_priority_summary", {})),
        },
    ]


def _base_allowed_reason_codes(descriptor: dict[str, Any] | None = None) -> list[str]:
    codes = [
        "SELECTED_STACK_HANDOFF_ALLOWED_STATIC_FIXTURE_ONLY",
        "SELECTED_STACK_HANDOFF_ALLOWED_PR88_SELECTION_PACKET",
        "SELECTED_STACK_HANDOFF_ALLOWED_PR87_CANDIDATE_PACKET",
        "SELECTED_STACK_HANDOFF_ALLOWED_TRADE_CONTEXT_LINEAGE",
        "SELECTED_STACK_HANDOFF_ALLOWED_ROUTED_SELECTION_UNIVERSE_LINEAGE",
        "SELECTED_STACK_HANDOFF_ALLOWED_SCORING_RANKING_LINEAGE",
        "SELECTED_STACK_HANDOFF_ALLOWED_OPTIMIZER_ARBITRATION_LINEAGE",
        "SELECTED_STACK_HANDOFF_ALLOWED_ORDER_INTENT_PREVIEW_NON_AUTHORITATIVE",
        "SELECTED_STACK_HANDOFF_ALLOWED_PR90_FORWARDABLE_NOT_EXECUTED",
        "SELECTED_STACK_HANDOFF_ALLOWED_DETERMINISTIC_TIE_BREAK",
    ]
    if descriptor is not None and descriptor.get("quantum_candidate_type") != "CLASSICAL_ONLY":
        codes.extend(
            [
                "SELECTED_STACK_HANDOFF_ALLOWED_QUANTUM_POLICY_LINEAGE",
                "SELECTED_STACK_HANDOFF_ALLOWED_CLASSICAL_COMPARATOR_OR_FALLBACK",
            ]
        )
    if descriptor is not None and _owner_override_applied(descriptor):
        codes.append("SELECTED_STACK_HANDOFF_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY")
    return _sort_reason_codes(codes)


def build_selected_parameter_stack_handoff_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    case = None if case_id is None else _case_by_id(fixture, case_id)
    selection_packet = copy.deepcopy(upstream.get("trade_context_selection_packet", {}))
    if case is not None and case.get("selection_packet_available") is False:
        selection_packet = {}

    block_codes: list[str] = []
    descriptor: dict[str, Any] | None = None
    selected_stack_id: str | None = None
    if not selection_packet:
        block_codes.append("SELECTED_STACK_HANDOFF_BLOCKED_MISSING_PR88_SELECTION_PACKET")
    else:
        selected_stack_id = _selected_stack_id_for_case(selection_packet, case)
        descriptor = _selected_descriptor_for_case(selected_stack_id, selection_packet, upstream, case)
        block_codes.extend(_block_codes_for_selected_descriptor(selected_stack_id, descriptor, upstream, case))

    block_codes = _sort_reason_codes(block_codes)
    ready = not block_codes and descriptor is not None and selected_stack_id is not None
    selected_items = [
        _handoff_item(selected_stack_id, descriptor, fixture, selection_packet)
    ] if ready else []
    selected_families = _selected_parameter_families(descriptor) if ready else []
    selected_algorithms = _selected_algorithm_families(descriptor) if ready else []
    selected_role_families = _selected_role_families(descriptor) if ready else {}
    score_breakdown = _score_breakdown(descriptor) if ready else {}
    selected_generation_key = descriptor.get("seed_descriptor_id") if ready else None
    lineage = (
        _lineage_trace(selected_stack_id, descriptor, fixture, selection_packet)
        if ready
        else []
    )
    selected_score_ref = descriptor.get("ranking_contract_score_ref") if ready else None
    quantum_priority = False
    if ready:
        arbitration = descriptor.get("optimizer_arbitration_metadata")
        if isinstance(arbitration, dict):
            quantum_priority = arbitration.get("quantum_priority_applied") is True
    owner_override = _owner_override_applied(descriptor) if ready else False
    owner_basis = None
    if ready:
        summary = descriptor.get("owner_quantum_priority_summary")
        if isinstance(summary, dict):
            owner_basis = summary.get("owner_override_basis")

    packet_status = (
        "STATIC_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_READY"
        if ready
        else (block_codes[0] if block_codes else "SELECTED_STACK_HANDOFF_BLOCKED_NO_ELIGIBLE_HANDOFF_ITEM")
    )
    selected_count = 1 if ready else 0
    blocked_items = []
    if not ready:
        blocked_items.append(
            {
                "handoff_item_id": "BLOCKED_SELECTED_PARAMETER_STACK_HANDOFF_ITEM",
                "selected_stack_id": selected_stack_id,
                "blocked_reason_codes": block_codes or ["SELECTED_STACK_HANDOFF_BLOCKED_NO_ELIGIBLE_HANDOFF_ITEM"],
                "active_handoff_created": False,
            }
        )
    packet = {
        "selected_parameter_stack_handoff_packet_id": fixture.get("selected_parameter_stack_handoff_packet_id"),
        "schema_version": fixture.get("schema_version"),
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "handoff_scope": HANDOFF_SCOPE,
        "handoff_authority_class": HANDOFF_AUTHORITY_CLASS,
        "packet_status": packet_status,
        "fixture_case_id": None if case is None else case.get("case_id"),
        "upstream_trade_context_selection_packet_ref": fixture.get("upstream_trade_context_selection_packet_ref"),
        "upstream_trade_context_selection_packet_digest_or_static_ref": fixture.get("upstream_trade_context_selection_packet_digest_or_static_ref"),
        "upstream_candidate_generation_packet_ref": fixture.get("upstream_candidate_generation_packet_ref"),
        "upstream_candidate_generation_packet_digest_or_static_ref": fixture.get("upstream_candidate_generation_packet_digest_or_static_ref"),
        "upstream_trade_context_ref": selection_packet.get("trade_context_ref") or fixture.get("upstream_trade_context_ref"),
        "upstream_routed_selection_universe_ref": selection_packet.get("routed_selection_universe_ref") or fixture.get("upstream_routed_selection_universe_ref"),
        "selected_stack_id": selected_stack_id if ready else None,
        "selected_candidate_stack_id": selected_stack_id if ready else None,
        "selected_candidate_generation_key": selected_generation_key,
        "selected_parameter_families": selected_families,
        "selected_algorithm_families": selected_algorithms,
        "selected_stack_role_families": selected_role_families,
        "score_breakdown_ref": selected_score_ref,
        "selected_candidate_score_breakdown": score_breakdown,
        "ranking_contract_ref": descriptor.get("ranking_contract_ref") if ready else None,
        "optimizer_arbitration_policy_ref": descriptor.get("optimizer_arbitration_policy_ref") if ready else None,
        "quantum_applicability_ref": registry.get("upstream_quantum_applicability_ref", {}).get("report_path"),
        "owner_quantum_priority_ref": registry.get("upstream_owner_quantum_priority_ref", {}).get("report_path"),
        "quantum_priority_applied": quantum_priority,
        "owner_override_applied": owner_override,
        "owner_override_basis_ref_or_reason_codes": [owner_basis] if owner_basis else [],
        "deterministic_selection_key": selection_packet.get("deterministic_selection_key"),
        "deterministic_handoff_key": (
            f"PR89|{selection_packet.get('trade_context_parameter_stack_selection_packet_id', 'MISSING_PR88_SELECTION')}|"
            f"{selected_stack_id or 'BLOCKED_NO_SELECTED_STACK'}|"
            f"{fixture.get('upstream_candidate_generation_packet_ref')}|"
            f"{selection_packet.get('deterministic_selection_key', 'MISSING_PR88_DETERMINISTIC_KEY')}"
        ),
        "deterministic_tie_break_chain": list(DETERMINISTIC_TIE_BREAK_CHAIN),
        "selection_reason_codes": _sort_reason_codes(_base_allowed_reason_codes(descriptor if ready else None) + block_codes),
        "selected_stack_lineage_trace": lineage,
        "selected_stack_digest_or_static_ref": (
            "docs/master_plan/generated/SelectedParameterStackHandoffPacket.report.json"
            f"#selected_parameter_stack_handoff_packet/selected_stack_lineage_trace/{selected_stack_id}"
            if ready
            else None
        ),
        "replay_paper_competition_required_flag": ready,
        "replay_paper_input_lock_required_flag": ready,
        "pr90_competition_gate_required_flag": ready,
        "order_intent_surface_present_flag": True,
        "order_intent_surface_authority": ORDER_INTENT_PREVIEW_AUTHORITY,
        "owner_review_required_flag": ready,
        "owner_approval_created_flag": False,
        "no_order_authority_flag": True,
        "no_runtime_execution_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
        "no_live_trade_authority_flag": True,
        "selected_handoff_item_count": selected_count,
        "rejected_handoff_item_count": 0,
        "blocked_handoff_item_count": len(blocked_items),
        "replay_paper_forwardable_item_count": selected_count,
        "order_authoritative_item_count": 0,
        "selected_handoff_items": selected_items,
        "rejected_handoff_items": [],
        "blocked_handoff_items": blocked_items,
        "order_intent_preview_surface": {
            "preview_surface_id": "PR89_NON_AUTHORITATIVE_STATIC_ORDER_INTENT_PREVIEW",
            "authority_class": ORDER_INTENT_PREVIEW_AUTHORITY,
            "order_intent_preview_allowed_flag": True,
            "order_submission_allowed_flag": False,
            "live_routing_allowed_flag": False,
            "connector_binding_allowed_flag": False,
            "executable_order_intent_created": False,
        },
        "pr90_forwardable_metadata": {
            "pr90_forwardable_flag": ready,
            "replay_lane_contract_required_flag": ready,
            "paper_lane_contract_required_flag": ready,
            "pr90_execution_created": False,
        },
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        packet[field] = False
    return packet, failures


def validate_handoff_packet(packet: dict[str, Any], upstream: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required_fields = (
        "selected_parameter_stack_handoff_packet_id",
        "schema_version",
        "roadmap_pr_label",
        "semantic_task_id",
        "handoff_scope",
        "handoff_authority_class",
        "packet_status",
        "selected_stack_id",
        "selected_candidate_stack_id",
        "deterministic_handoff_key",
        "deterministic_tie_break_chain",
        "selection_reason_codes",
        "selected_handoff_item_count",
        "blocked_handoff_item_count",
        "replay_paper_forwardable_item_count",
        "order_authoritative_item_count",
        "selected_handoff_items",
        "blocked_handoff_items",
    )
    for field in required_fields:
        if field not in packet:
            failures.append(f"handoff packet missing required field {field}")
    if packet.get("roadmap_pr_label") != ROADMAP_PR_LABEL:
        failures.append("handoff packet roadmap_pr_label mismatch")
    if packet.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append("handoff packet semantic_task_id mismatch")
    if packet.get("handoff_scope") != HANDOFF_SCOPE:
        failures.append("handoff packet handoff_scope mismatch")
    if packet.get("handoff_authority_class") != HANDOFF_AUTHORITY_CLASS:
        failures.append("handoff packet handoff_authority_class mismatch")
    if packet.get("deterministic_tie_break_chain") != list(DETERMINISTIC_TIE_BREAK_CHAIN):
        failures.append("handoff packet deterministic_tie_break_chain mismatch")
    selected_items = _list_of_mappings(packet.get("selected_handoff_items"))
    blocked_items = _list_of_mappings(packet.get("blocked_handoff_items"))
    if packet.get("selected_handoff_item_count") != len(selected_items):
        failures.append("selected_handoff_item_count mismatch")
    if packet.get("blocked_handoff_item_count") != len(blocked_items):
        failures.append("blocked_handoff_item_count mismatch")
    if packet.get("order_authoritative_item_count") != 0:
        failures.append("order_authoritative_item_count must be 0")
    ready = packet.get("packet_status") == "STATIC_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_READY"
    if ready:
        if len(selected_items) != 1:
            failures.append("ready handoff packet must include exactly one selected handoff item")
        selected_stack_id = packet.get("selected_stack_id")
        selection_packet = upstream.get("trade_context_selection_packet", {})
        if selected_stack_id != selection_packet.get("static_selected_candidate_stack_id"):
            failures.append("selected_stack_id must derive from PR88 static_selected_candidate_stack_id")
        if selected_stack_id not in set(upstream.get("pr87_candidate_stack_ids", [])):
            failures.append("selected_stack_id must trace to PR87 candidate packet")
        if packet.get("replay_paper_competition_required_flag") is not True:
            failures.append("ready handoff must require replay/paper competition")
        if packet.get("pr90_competition_gate_required_flag") is not True:
            failures.append("ready handoff must require PR90 competition gate")
        if packet.get("order_intent_surface_authority") != ORDER_INTENT_PREVIEW_AUTHORITY:
            failures.append("ready handoff order intent surface authority mismatch")
        for item in selected_items:
            if item.get("selected_stack_id") != selected_stack_id:
                failures.append("selected handoff item selected_stack_id mismatch")
            if item.get("required_role_completion_state") != "ROLE_COMPLETE":
                failures.append("selected handoff item must be role complete")
            if item.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
                failures.append("selected handoff item must be compatible")
            if item.get("blocked_row_ids_and_reasons"):
                failures.append("selected handoff item must not carry blocked rows")
            if item.get("pr90_forwardable_flag") is not True:
                failures.append("selected handoff item must be PR90 forwardable")
            if item.get("quantum_candidate_type") != "CLASSICAL_ONLY":
                if item.get("classical_comparator_required_flag") is not True:
                    failures.append("quantum selected handoff item must require comparator")
                if not item.get("classical_comparator_ref"):
                    failures.append("quantum selected handoff item must preserve comparator ref")
    else:
        if packet.get("selected_stack_id") is not None:
            failures.append("blocked handoff packet must not emit active selected_stack_id")
        if selected_items:
            failures.append("blocked handoff packet must not include selected_handoff_items")
        if not any(code in BLOCK_REASON_CODES for code in packet.get("selection_reason_codes", [])):
            failures.append("blocked handoff packet must include a blocked reason code")
    if packet.get("order_intent_surface_authority") != ORDER_INTENT_PREVIEW_AUTHORITY:
        failures.append("order_intent_surface_authority mismatch")
    if packet.get("order_intent_surface_present_flag") is not True:
        failures.append("order_intent_surface_present_flag must be true for static preview")
    for field in (
        "no_order_authority_flag",
        "no_runtime_execution_flag",
        "no_quantum_backend_execution_flag",
        "no_profit_evidence_flag",
        "no_live_trade_authority_flag",
    ):
        if packet.get(field) is not True:
            failures.append(f"packet.{field} must be true")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: packet.{field} must be false")
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
        ("handoff_scope", HANDOFF_SCOPE),
        ("handoff_authority_class", HANDOFF_AUTHORITY_CLASS),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "handoff_contract_only_flag",
        "no_order_authority_flag",
        "no_runtime_execution_flag",
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

    packet, packet_failures = build_selected_parameter_stack_handoff_packet(
        registry,
        fixture,
        upstream,
    )
    failures.extend(packet_failures)
    failures.extend(validate_handoff_packet(packet, upstream))
    if packet.get("selected_stack_id") != fixture.get("expected_selected_stack_id"):
        failures.append("default fixture selected_stack_id mismatch")
    for count_field in (
        "expected_selected_handoff_item_count",
        "expected_rejected_handoff_item_count",
        "expected_blocked_handoff_item_count",
        "expected_replay_paper_forwardable_item_count",
        "expected_order_authoritative_item_count",
    ):
        packet_field = count_field.replace("expected_", "")
        if fixture.get(count_field) != packet.get(packet_field):
            failures.append(f"default fixture {packet_field} mismatch")

    case_packets: list[dict[str, Any]] = []
    for case in cases:
        case_packet, case_failures = build_selected_parameter_stack_handoff_packet(
            registry,
            fixture,
            upstream,
            case_id=str(case.get("case_id")),
        )
        failures.extend(case_failures)
        failures.extend(validate_handoff_packet(case_packet, upstream))
        expected_id = case.get("expected_selected_stack_id")
        if case_packet.get("selected_stack_id") != expected_id:
            failures.append(f"{case.get('case_id')} selected_stack_id mismatch")
        expected_count = case.get("expected_selected_handoff_item_count")
        if expected_count is not None and case_packet.get("selected_handoff_item_count") != expected_count:
            failures.append(f"{case.get('case_id')} selected handoff item count mismatch")
        expected_code = case.get("expected_reason_code")
        reason_codes = list(case_packet.get("selection_reason_codes", []))
        blocked_codes = [
            code
            for item in _list_of_mappings(case_packet.get("blocked_handoff_items"))
            for code in item.get("blocked_reason_codes", [])
        ]
        if expected_code not in reason_codes and expected_code not in blocked_codes:
            failures.append(f"{case.get('case_id')} missing expected reason code {expected_code}")
        case_packets.append(case_packet)

    boundary = fixture.get("pr90_boundary_fixture")
    if not isinstance(boundary, dict):
        failures.append("fixture.pr90_boundary_fixture must be an object")
    else:
        if boundary.get("static_selected_stack_handoff_is_forwardable_to_pr90_competition_gate") is not True:
            failures.append("PR90 boundary fixture must be forwardable")
        for field in (
            "replay_execution_created",
            "paper_execution_created",
            "replay_result_packet_created",
            "paper_result_packet_created",
            "order_authority_created",
            "live_authority_created",
            "pr90_execution_created",
        ):
            if boundary.get(field) is not False:
                failures.append(f"PR90 boundary fixture {field} must be false")
    return failures, packet, case_packets


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "SELECTED_STACK_HANDOFF_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
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
            "SELECTED_STACK_HANDOFF_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
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
    selected_items = _list_of_mappings(packet.get("selected_handoff_items"))
    selected_item = selected_items[0] if selected_items else {}
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
        "handoff_registry_id": registry.get("handoff_registry_id"),
        "selected_parameter_stack_handoff_packet_contract_id": registry.get("selected_parameter_stack_handoff_packet_contract_id"),
        "gate_scope": registry.get("gate_scope"),
        "handoff_scope": HANDOFF_SCOPE,
        "handoff_authority_class": HANDOFF_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "handoff_contract_only_flag": True,
        "handoff_inputs": list(HANDOFF_INPUT_ORDER),
        "handoff_outputs": list(HANDOFF_OUTPUT_ORDER),
        "handoff_policy": copy.deepcopy(registry.get("handoff_policy")),
        "blocked_handoff_policy": copy.deepcopy(registry.get("blocked_handoff_policy")),
        "deterministic_tie_break_chain": list(DETERMINISTIC_TIE_BREAK_CHAIN),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "upstream_dependencies": copy.deepcopy(registry.get("upstream_dependencies")),
        "future_consumers": copy.deepcopy(registry.get("future_consumers")),
        "upstream_trade_context_selection_gate_ref": copy.deepcopy(registry.get("upstream_trade_context_selection_gate_ref")),
        "upstream_candidate_generation_gate_ref": copy.deepcopy(registry.get("upstream_candidate_generation_gate_ref")),
        "upstream_trade_context_selection_packet_id": upstream.get("trade_context_selection_packet", {}).get("trade_context_parameter_stack_selection_packet_id"),
        "upstream_candidate_generation_packet_id": upstream.get("candidate_generation_packet", {}).get("candidate_generation_packet_id"),
        "pr88_selected_candidate_stack_id": upstream.get("trade_context_selection_packet", {}).get("selected_candidate_stack_id"),
        "pr88_static_selected_candidate_stack_id": upstream.get("trade_context_selection_packet", {}).get("static_selected_candidate_stack_id"),
        "pr87_active_candidate_stack_ids": list(upstream.get("pr87_active_candidate_stack_ids", [])),
        "pr87_blocked_candidate_stack_ids": list(upstream.get("pr87_blocked_candidate_stack_ids", [])),
        "selected_parameter_stack_handoff_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "master_plan_principles_consumed": copy.deepcopy(registry.get("master_plan_principles_consumed")),
        "selected_handoff_item_count": packet.get("selected_handoff_item_count"),
        "rejected_handoff_item_count": packet.get("rejected_handoff_item_count"),
        "blocked_handoff_item_count": packet.get("blocked_handoff_item_count"),
        "replay_paper_forwardable_item_count": packet.get("replay_paper_forwardable_item_count"),
        "order_authoritative_item_count": packet.get("order_authoritative_item_count"),
        "selected_stack_id": packet.get("selected_stack_id"),
        "selected_candidate_stack_id": packet.get("selected_candidate_stack_id"),
        "selected_candidate_generation_key": packet.get("selected_candidate_generation_key"),
        "selected_stack_lineage_trace": copy.deepcopy(packet.get("selected_stack_lineage_trace", [])),
        "selected_stack_digest_or_static_ref": packet.get("selected_stack_digest_or_static_ref"),
        "score_breakdown_ref": packet.get("score_breakdown_ref"),
        "ranking_contract_ref": packet.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": packet.get("optimizer_arbitration_policy_ref"),
        "quantum_applicability_ref": packet.get("quantum_applicability_ref"),
        "owner_quantum_priority_ref": packet.get("owner_quantum_priority_ref"),
        "quantum_priority_applied": packet.get("quantum_priority_applied"),
        "owner_override_applied": packet.get("owner_override_applied"),
        "owner_override_basis_ref_or_reason_codes": list(packet.get("owner_override_basis_ref_or_reason_codes", [])),
        "deterministic_static_handoff": True,
        "deterministic_handoff_key": packet.get("deterministic_handoff_key"),
        "deterministic_selected_stack_lineage": True,
        "selected_stack_derived_only_from_pr88_selection_packet": True,
        "selected_stack_lineage_traces_to_pr87_candidate_packet": True,
        "trade_context_and_route_lineage_preserved": True,
        "scoring_ranking_arbitration_lineage_preserved": True,
        "quantum_policy_lineage_preserved": True,
        "classical_comparator_or_fallback_preserved_for_quantum_selected_stack": True,
        "blocked_candidates_cannot_be_handed_off_active": True,
        "missing_role_candidates_cannot_be_handed_off_active": True,
        "incompatible_candidates_cannot_be_handed_off_active": True,
        "route_mismatched_candidates_cannot_be_handed_off_active": True,
        "owner_override_records_basis_without_external_fact_fabrication": True,
        "order_intent_surface_present_flag": packet.get("order_intent_surface_present_flag"),
        "order_intent_surface_authority": packet.get("order_intent_surface_authority"),
        "order_intent_authority_created": False,
        "order_submission_allowed_flag": False,
        "live_routing_allowed_flag": False,
        "connector_binding_allowed_flag": False,
        "replay_paper_competition_required_flag": packet.get("replay_paper_competition_required_flag"),
        "replay_paper_input_lock_required_flag": packet.get("replay_paper_input_lock_required_flag"),
        "pr90_competition_gate_required_flag": packet.get("pr90_competition_gate_required_flag"),
        "pr90_forwardable_flag": selected_item.get("pr90_forwardable_flag"),
        "replay_lane_contract_required_flag": selected_item.get("replay_lane_contract_required_flag"),
        "paper_lane_contract_required_flag": selected_item.get("paper_lane_contract_required_flag"),
        "pr90_execution_created": False,
        "final_ready": False,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "real_optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "live_order_authority": False,
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

    metadata_failures, metadata = validate_pr89_roadmap_metadata(repo_root)
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
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

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
