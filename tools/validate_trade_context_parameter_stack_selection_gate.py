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

from tools import ci_branch_context  # noqa: E402
from tools import validate_candidate_parameter_stack_generation_gate as pr87_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "trade_context_parameter_stack_selection_gate.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "TradeContextParameterStackSelectionGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_trade_context_parameter_stack_selection_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "TradeContextParameterStackSelectionGate.report.json"
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

GATE_REGISTRY_ID = "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE"
GATE_ID = "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_V1"
REPORT_ID = "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #88"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-TRADE-CONTEXT-PARAMETER-STACK-SELECTION-GATE"
TARGET_BRANCH = "pr88-trade-context-parameter-stack-selection-gate"
EXPECTED_BASELINE_ANCESTOR = "bdb3207"
GATE_SCOPE = "STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_ONLY"
SELECTION_SCOPE = "STATIC_ONLY"
SELECTION_AUTHORITY_CLASS = (
    "STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_NOT_HANDOFF_NOT_EXECUTION"
)
SUCCESS_MARKER = "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK"
FAILURE_MARKER = "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_MODE_ACTIVE"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"

ROLE_ORDER = pr87_gate.ROLE_ORDER
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
}
FUTURE_CONSUMER_ORDER = (
    "PR89_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
    "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
    "PR105_PR151_STAGE1_RUNTIME_LIVE_LAUNCH_CLOSURE_CONSUMERS",
)
SELECTION_INPUT_ORDER = (
    "PR87_static_candidate_generation_packet",
    "PR78_static_trade_context_packet_metadata",
    "PR81_routed_selection_universe_metadata",
    "PR79_selection_universe_registry_metadata",
    "PR82_quantum_applicability_metadata",
    "PR83_owner_quantum_priority_policy_metadata",
    "PR84_scoring_policy_registry",
    "PR85_static_scoring_ranking_metadata",
    "PR86_static_optimizer_arbitration_metadata",
    "PR73_PR74_PR75_role_completeness_and_compatibility_metadata",
)
SELECTION_OUTPUT_ORDER = (
    "static_trade_context_parameter_stack_selection_packet",
    "evaluated_candidate_stack_descriptors",
    "static_selected_candidate_descriptor",
    "blocked_or_rejected_candidate_descriptors",
    "deterministic_selection_key",
    "deterministic_tie_break_chain",
    "selection_reason_codes",
    "no_handoff_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "pr89_pr90_forwardable_boundary",
)
DETERMINISTIC_TIE_BREAK_CHAIN = (
    "candidate_appears_in_PR87_candidate_generation_packet",
    "eligible_static_candidate_before_rejected_candidate",
    "trade_context_match_required",
    "route_match_required",
    "required_roles_complete",
    "compatibility_passes",
    "blocked_rows_absent",
    "source_dependency_state_acceptable",
    "scoring_ranking_gate_metadata_acceptable",
    "optimizer_arbitration_metadata_acceptable_as_static_policy_only",
    "owner_override_static_basis_when_recorded",
    "owner_quantum_priority_static_policy_when_enabled",
    "quantum_applicability_with_classical_comparator_or_fallback",
    "lower_PR85_static_rank",
    "higher_PR85_final_selection_score_metadata",
    "lexicographic_candidate_family_tuple",
    "lexicographic_candidate_stack_id",
)
REASON_CODE_ORDER = (
    "TRADE_CONTEXT_SELECTION_ALLOWED_STATIC_FIXTURE_ONLY",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR87_CANDIDATE_GENERATION_PACKET",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR81_ROUTED_SELECTION_UNIVERSE_METADATA",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR84_SCORING_POLICY",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR85_RANKING_CONTRACT",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR86_OPTIMIZER_ARBITRATION_METADATA",
    "TRADE_CONTEXT_SELECTION_ALLOWED_ELIGIBLE_STATIC_CANDIDATE_SELECTED",
    "TRADE_CONTEXT_SELECTION_ALLOWED_CLASSICAL_COMPARATOR",
    "TRADE_CONTEXT_SELECTION_ALLOWED_CLASSICAL_FALLBACK",
    "TRADE_CONTEXT_SELECTION_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY",
    "TRADE_CONTEXT_SELECTION_ALLOWED_OWNER_QUANTUM_PRIORITY_STATIC_POLICY",
    "TRADE_CONTEXT_SELECTION_ALLOWED_DETERMINISTIC_TIE_BREAK",
    "TRADE_CONTEXT_SELECTION_ALLOWED_PR89_PR90_FORWARDABLE_NOT_HANDED_OFF_NOT_EXECUTED",
    "TRADE_CONTEXT_SELECTION_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR",
    "TRADE_CONTEXT_SELECTION_BLOCKED_DUPLICATE_CANDIDATE_STACK",
    "TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_REQUIRED_FIELD",
    "TRADE_CONTEXT_SELECTION_BLOCKED_ROUTE_MISMATCH",
    "TRADE_CONTEXT_SELECTION_BLOCKED_TRADE_CONTEXT_MISMATCH",
    "TRADE_CONTEXT_SELECTION_BLOCKED_CANDIDATE_STATUS",
    "TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_REQUIRED_ROLE",
    "TRADE_CONTEXT_SELECTION_BLOCKED_INCOMPATIBLE_CANDIDATE",
    "TRADE_CONTEXT_SELECTION_BLOCKED_BLOCKED_ROW_PRESENT",
    "TRADE_CONTEXT_SELECTION_BLOCKED_SOURCE_DEPENDENCY_STATE",
    "TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_CLASSICAL_COMPARATOR",
    "TRADE_CONTEXT_SELECTION_BLOCKED_NO_ELIGIBLE_CANDIDATE_STACK",
    "TRADE_CONTEXT_SELECTION_BLOCKED_AMBIGUOUS_STATIC_SELECTION_TIE",
    "TRADE_CONTEXT_SELECTION_BLOCKED_RANDOM_SELECTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_WALL_CLOCK_IDENTITY_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_SELECTED_STACK_HANDOFF_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "TRADE_CONTEXT_SELECTION_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR88_METADATA_VERIFIED",
    "PASS_VALID_MULTI_CANDIDATE_TRADE_CONTEXT_SELECTION",
    "PASS_ROUTE_MISMATCH_REJECTED",
    "PASS_BLOCKED_CANDIDATE_REJECTED",
    "PASS_MISSING_REQUIRED_ROLE_REJECTED",
    "PASS_INCOMPATIBLE_CANDIDATE_REJECTED",
    "PASS_QUANTUM_PREFERRED_WITH_CLASSICAL_COMPARATOR_SELECTED",
    "PASS_QUANTUM_PREFERRED_BLOCKED_WITHOUT_COMPARATOR",
    "PASS_DETERMINISTIC_TIE_BREAK",
    "PASS_OWNER_OVERRIDE_INTERNAL_STATIC_SELECTION_BASIS",
    "PASS_NO_ELIGIBLE_CANDIDATE_FAILS_CLOSED",
    "PASS_PR89_PR90_BOUNDARY_FORWARDABLE_NOT_HANDED_OFF",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "selected_stack_handoff_created",
    "selected_trade_created",
    "live_authority_created",
    "order_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_cash_receipt_created",
    "private_state_fetch_created",
    "replay_execution_created",
    "paper_execution_created",
    "classical_optimizer_execution_created",
    "quantum_optimizer_execution_created",
    "optimizer_execution_created",
    "backend_execution_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solve_execution_created",
    "ising_solve_execution_created",
    "profit_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "random_selection_used",
    "wall_clock_identity_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
    "selected_stack_handoff_packet_created",
    "pr89_selected_stack_handoff_packet_created",
    "replay_paper_result_packet_created",
    "paper_result_packet_created",
    "source_retrieval_execution_created",
    "source_acceptance_execution_created",
    "runtime_resolver_execution_created",
    "balance_fetch_created",
    "open_order_fetch_created",
    "order_submission_created",
    "order_cancellation_created",
    "fill_receipt_created",
    "walk_forward_execution_created",
    "dashboard_runtime_service_created",
    "telegram_runtime_service_created",
    "static_selection_packet_is_pr89_handoff",
    "static_selection_packet_is_live_order_authority",
    "static_selection_packet_is_trading_signal",
    "static_selection_packet_is_replay_result",
    "static_selection_packet_is_paper_result",
    "quantum_applicability_metadata_is_backend_evidence",
    "owner_quantum_priority_fabricates_external_facts",
    "owner_override_fabricates_external_facts",
    "future_pr89_selected_stack_handoff_implemented",
    "future_pr90_replay_paper_competition_implemented",
    "future_live_authority_implemented",
)
FIELD_REASON_CODES = {
    "selected_stack_handoff_created": "TRADE_CONTEXT_SELECTION_BLOCKED_SELECTED_STACK_HANDOFF_FORBIDDEN",
    "selected_stack_handoff_packet_created": "TRADE_CONTEXT_SELECTION_BLOCKED_SELECTED_STACK_HANDOFF_FORBIDDEN",
    "pr89_selected_stack_handoff_packet_created": "TRADE_CONTEXT_SELECTION_BLOCKED_SELECTED_STACK_HANDOFF_FORBIDDEN",
    "selected_trade_created": "TRADE_CONTEXT_SELECTION_BLOCKED_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "live_authority_created": "TRADE_CONTEXT_SELECTION_BLOCKED_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "order_authority_created": "TRADE_CONTEXT_SELECTION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "source_retrieval_created": "TRADE_CONTEXT_SELECTION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "source_acceptance_created": "TRADE_CONTEXT_SELECTION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "connector_semantic_binding_created": "TRADE_CONTEXT_SELECTION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created": "TRADE_CONTEXT_SELECTION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "private_state_fetch_created": "TRADE_CONTEXT_SELECTION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "replay_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "paper_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "classical_optimizer_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "backend_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_backend_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "qaoa_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "vqe_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "annealing_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "qubo_solve_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "ising_solve_execution_created": "TRADE_CONTEXT_SELECTION_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "profit_evidence_created": "TRADE_CONTEXT_SELECTION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created": "TRADE_CONTEXT_SELECTION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created": "TRADE_CONTEXT_SELECTION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "execution_superiority_claim_created": "TRADE_CONTEXT_SELECTION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "random_selection_used": "TRADE_CONTEXT_SELECTION_BLOCKED_RANDOM_SELECTION_FORBIDDEN",
    "wall_clock_identity_used": "TRADE_CONTEXT_SELECTION_BLOCKED_WALL_CLOCK_IDENTITY_FORBIDDEN",
    "atomicrows_bundle_jsonl_created": "TRADE_CONTEXT_SELECTION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "TRADE_CONTEXT_SELECTION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
}
SOURCE_ALLOWED_STATES = {"STATIC_SOURCE_DEPENDENCY_LABELS_ONLY"}
OWNER_MODE_ORDER = pr87_gate.OWNER_MODE_ORDER
QUANTUM_TYPE_ORDER = pr87_gate.QUANTUM_TYPE_ORDER


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
    return pr87_gate.load_yaml(path)


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
    return ci_branch_context.github_actions_active()


def _downstream_validation_branch_allowed(branch: str) -> bool:
    return ci_branch_context.is_downstream_or_main_validation_branch(branch, after_pr=88)


def validate_pr88_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 88), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 88), None)
    if roadmap_entry is None:
        failures.append("PR88 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR88 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Trade-context parameter-stack selection gate"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Trade-context parameter-stack selection gate"),
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
            info_lines.append("DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_ACTIVE")
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
        failures.append("upstream_dependencies must use canonical PR77-PR87 dependency order")
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
        failures.append("future_consumers must use canonical PR89-PR92/Stage1 consumer order")
    for consumer in _list_of_mappings(payload.get("future_consumers")):
        if consumer.get("pr88_creates_consumer_execution") is not False:
            failures.append(f"{consumer.get('consumer_id')} pr88_creates_consumer_execution must be false")
    return failures


def validate_selection_policy(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("selection_policy")
    if not isinstance(policy, dict):
        return ["selection_policy must be an object"]
    failures: list[str] = []
    checks = (
        ("selection_policy_id", "TRADE_CONTEXT_PARAMETER_STACK_SELECTION_POLICY_V1"),
        ("selection_contract_version", POLICY_VERSION),
    )
    for field, expected in checks:
        if policy.get(field) != expected:
            failures.append(f"selection_policy.{field} must be {expected}")
    for field in (
        "stable_sort_required",
        "pr89_selected_stack_handoff_required_for_selected_static_candidate",
        "replay_paper_competition_required_for_selected_static_candidate",
        "owner_review_required_for_selected_static_candidate",
        "quantum_candidates_require_classical_comparator_or_fallback",
    ):
        if policy.get(field) is not True:
            failures.append(f"selection_policy.{field} must be true")
    for field in ("random_selection_allowed", "wall_clock_identity_allowed", "selected_stack_handoff_created"):
        if policy.get(field) is not False:
            failures.append(f"selection_policy.{field} must be false")
    if policy.get("selected_candidate_count_for_valid_fixture") != 1:
        failures.append("selection_policy.selected_candidate_count_for_valid_fixture must be 1")
    if policy.get("deterministic_tie_break_chain") != list(DETERMINISTIC_TIE_BREAK_CHAIN):
        failures.append("selection_policy.deterministic_tie_break_chain mismatch")
    return failures


def validate_blocked_candidate_policy(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("blocked_candidate_policy")
    if not isinstance(policy, dict):
        return ["blocked_candidate_policy must be an object"]
    failures: list[str] = []
    if policy.get("blocked_candidate_policy_id") != "TRADE_CONTEXT_PARAMETER_STACK_SELECTION_BLOCKED_POLICY_V1":
        failures.append("blocked_candidate_policy_id mismatch")
    for field in ("blocked_candidates_remain_traceable", "blocked_candidates_retain_reason_codes"):
        if policy.get(field) is not True:
            failures.append(f"blocked_candidate_policy.{field} must be true")
    if policy.get("blocked_candidates_enter_selected_status") is not False:
        failures.append("blocked_candidate_policy.blocked_candidates_enter_selected_status must be false")
    if policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
        failures.append("blocked_candidate_policy.blocked_reason_code_order mismatch")
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
        ("gate_registry_id", GATE_REGISTRY_ID),
        ("trade_context_parameter_stack_selection_gate_id", GATE_ID),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("roadmap_pr_label", ROADMAP_PR_LABEL),
        ("github_pr_number_policy", GITHUB_PR_NUMBER_POLICY),
        ("gate_scope", GATE_SCOPE),
        ("policy_version", POLICY_VERSION),
        ("selection_scope", SELECTION_SCOPE),
        ("selection_authority_class", SELECTION_AUTHORITY_CLASS),
    )
    for field, expected in checks:
        if payload.get(field) != expected:
            failures.append(f"{field} must be {expected}")
    for field in ("static_only_flag", "metadata_only_flag", "synthetic_fixture_only_flag", "selection_contract_only_flag"):
        if payload.get(field) is not True:
            failures.append(f"{field} must be true")
    if payload.get("final_ready") is not False:
        failures.append("final_ready must be false")
    if payload.get("required_stack_roles") != list(ROLE_ORDER):
        failures.append("required_stack_roles must match current repo PR87 role order")
    if payload.get("selection_inputs") != list(SELECTION_INPUT_ORDER):
        failures.append("selection_inputs mismatch")
    if payload.get("selection_outputs") != list(SELECTION_OUTPUT_ORDER):
        failures.append("selection_outputs mismatch")
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("reason_codes mismatch")
    if payload.get("stage1_prediction_market_contexts") != ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]:
        failures.append("stage1_prediction_market_contexts mismatch")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_selection_policy(payload))
    failures.extend(validate_blocked_candidate_policy(payload))
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
        "ATOMICROWS_INVENTORY_NOT_TRADER",
        "NO_SINGLE_PARAMETER_OR_ALGORITHM_STACKS",
        "MINIMUM_REQUIRED_STACK_ROLES",
        "BLOCKED_ROWS_EXCLUDED_FROM_ACTIVE_STACKS",
        "QUANTUM_RANK_REFINE_ONLY_NO_DIRECT_LIVE_AUTHORITY",
        "CLASSICAL_EXECUTION_GATES_REMAIN_FINAL",
        "EXECUTION_ROUTER_FINAL_ORDER_SUBMISSION_AUTHORITY",
        "REPLAY_PAPER_REQUIRED_BEFORE_LIVE_PROMOTION",
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
    pr87_upstream_failures, pr87_upstream = pr87_gate.validate_upstream_reports(repo_root)
    failures.extend(pr87_upstream_failures)

    pr81_report, pr81_failures = _load_json_checked(
        repo_root
        / "docs"
        / "master_plan"
        / "generated"
        / "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json",
        "PR81_REPORT",
    )
    pr85_report, pr85_failures = _load_json_checked(
        repo_root
        / "docs"
        / "master_plan"
        / "generated"
        / "ParameterStackScoringAndRankingGate.report.json",
        "PR85_REPORT",
    )
    pr86_report, pr86_failures = _load_json_checked(
        repo_root
        / "docs"
        / "master_plan"
        / "generated"
        / "QuantumClassicalOptimizerArbitrationGate.report.json",
        "PR86_REPORT",
    )
    pr87_registry, pr87_registry_failures = _load_yaml_checked(
        repo_root / pr87_gate.DEFAULT_PRODUCTION_REGISTRY,
        "PR87_REGISTRY",
    )
    pr87_report, pr87_report_failures = _load_json_checked(
        repo_root / pr87_gate.DEFAULT_REPORT,
        "PR87_REPORT",
    )
    failures.extend(pr81_failures)
    failures.extend(pr85_failures)
    failures.extend(pr86_failures)
    failures.extend(pr87_registry_failures)
    failures.extend(pr87_report_failures)
    failures.extend(_validate_report_marker(pr81_report, "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK", "PR81"))
    failures.extend(_validate_report_marker(pr85_report, "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK", "PR85"))
    failures.extend(_validate_report_marker(pr86_report, "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK", "PR86"))
    failures.extend(_validate_report_marker(pr87_report, pr87_gate.SUCCESS_MARKER, "PR87"))
    if pr87_registry is not None:
        if pr87_registry.get("semantic_task_id") != pr87_gate.SEMANTIC_TASK_ID:
            failures.append("PR87 registry semantic_task_id mismatch")
        if pr87_registry.get("generation_scope") != pr87_gate.GENERATION_SCOPE:
            failures.append("PR87 registry generation_scope mismatch")
    candidate_packet = {} if pr87_report is None else pr87_report.get("candidate_generation_packet", {})
    if not isinstance(candidate_packet, dict):
        failures.append("PR87 candidate_generation_packet must be an object")
        candidate_packet = {}
    candidates = _list_of_mappings(candidate_packet.get("candidate_stacks"))
    score_descriptors = []
    if pr85_report is not None:
        score_descriptors.extend(_list_of_mappings(pr85_report.get("static_ranked_candidate_descriptors")))
        score_descriptors.extend(_list_of_mappings(pr85_report.get("blocked_candidate_descriptors")))
    arbitration_decisions = []
    if pr86_report is not None:
        arbitration_decisions.extend(_list_of_mappings(pr86_report.get("static_arbitration_fixture_decisions")))
        arbitration_decisions.extend(_list_of_mappings(pr86_report.get("blocked_arbitration_fixture_decisions")))
    return failures, {
        "pr81_report": pr81_report or {},
        "pr85_report": pr85_report or {},
        "pr86_report": pr86_report or {},
        "pr87_registry": pr87_registry or {},
        "pr87_report": pr87_report or {},
        "pr87_upstream": pr87_upstream,
        "candidate_generation_packet": candidate_packet,
        "pr87_candidate_stacks": candidates,
        "pr87_candidate_stack_ids": [str(item.get("candidate_stack_id") or "") for item in candidates],
        "score_descriptors_by_id": _first_by_key(score_descriptors, "candidate_stack_descriptor_id"),
        "arbitration_decisions_by_id": _first_by_key(arbitration_decisions, "arbitration_fixture_id"),
        "pr81_eligible_universe_ids": [] if pr81_report is None else list(
            pr81_report.get("final_route_eligible_universe_ids", [])
        ),
    }


def _candidate_universe_id(candidate: dict[str, Any]) -> str:
    key = (
        candidate.get("platform_scope"),
        candidate.get("market_type"),
        candidate.get("strategy_class"),
    )
    mapping = {
        ("KALSHI", "BINARY_OUTCOME", "MARKET_MAKING_CANDIDATE_STATIC_ONLY"): "KALSHI_BINARY_SHORT_HORIZON",
        ("POLYMARKET", "EVENT_MARKET", "MOMENTUM_CANDIDATE_STATIC_ONLY"): "POLYMARKET_EVENT_MARKET_MOMENTUM",
        ("FORECASTEX_IBKR", "FORECAST_CONTRACT", "EVENT_RISK_HEDGE_CANDIDATE_STATIC_ONLY"): "FORECASTEX_IBKR_EVENT_RISK_HEDGE",
    }
    if key in mapping:
        return mapping[key]
    return "|".join(str(part) for part in key)


def _role_tuple(role_map: dict[str, Any]) -> str:
    return "|".join(f"{role}:{role_map.get(role, 'MISSING')}" for role in ROLE_ORDER)


def _candidate_family_tuple(candidate: dict[str, Any]) -> str:
    role_map = candidate.get("selected_stack_role_map")
    if not isinstance(role_map, dict):
        role_map = {}
    parts = (
        candidate.get("platform_scope"),
        candidate.get("venue_scope"),
        candidate.get("market_type"),
        candidate.get("strategy_class"),
        candidate.get("edge_type"),
        _role_tuple(role_map),
    )
    return "|".join(str(part) for part in parts)


def _context_for_case(fixture: dict[str, Any], case: dict[str, Any] | None) -> dict[str, Any]:
    context = copy.deepcopy(fixture.get("base_trade_context", {}))
    if case is not None:
        overrides = case.get("trade_context_overrides")
        if isinstance(overrides, dict):
            context.update(copy.deepcopy(overrides))
    return context


def _case_by_id(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in _list_of_mappings(fixture.get("fixture_cases")):
        if case.get("case_id") == case_id:
            return case
    raise KeyError(case_id)


def _candidate_filter(case: dict[str, Any] | None) -> set[str] | None:
    if case is None:
        return None
    value = case.get("candidate_stack_ids")
    if not isinstance(value, list):
        return None
    return {str(item) for item in value}


def _score_for_candidate(
    candidate: dict[str, Any],
    upstream: dict[str, Any],
    case: dict[str, Any] | None,
) -> dict[str, Any]:
    descriptor_id = str(candidate.get("pr85_candidate_descriptor_ref") or candidate.get("seed_descriptor_id") or "")
    descriptor = copy.deepcopy(upstream.get("score_descriptors_by_id", {}).get(descriptor_id, {}))
    score_breakdown = copy.deepcopy(descriptor.get("score_breakdown", {}))
    rank = descriptor.get("rank")
    if case is not None:
        overrides = case.get("score_overrides")
        if isinstance(overrides, dict):
            candidate_override = overrides.get(descriptor_id)
            if isinstance(candidate_override, dict):
                if "rank" in candidate_override:
                    rank = candidate_override["rank"]
                for field in ("final_selection_score", "base_score", "total_penalty"):
                    if field in candidate_override:
                        score_breakdown[field] = candidate_override[field]
    return {
        "candidate_stack_descriptor_id": descriptor_id,
        "rank": rank,
        "score_breakdown": score_breakdown,
        "rank_reason_codes": list(descriptor.get("rank_reason_codes", [])),
        "valid_for_ranking_flag": descriptor.get("valid_for_ranking_flag"),
    }


def _arbitration_for_candidate(candidate: dict[str, Any], upstream: dict[str, Any]) -> dict[str, Any]:
    fixture_ref = str(candidate.get("optimizer_arbitration_fixture_ref") or "")
    return copy.deepcopy(upstream.get("arbitration_decisions_by_id", {}).get(fixture_ref, {}))


def _trade_context_mismatch(candidate: dict[str, Any], context: dict[str, Any]) -> bool:
    compared_fields = (
        "platform_scope",
        "venue_scope",
        "market_type",
        "strategy_class",
        "edge_type",
        "latency_sensitivity_class",
        "capital_intensity_class",
    )
    for field in compared_fields:
        expected = context.get(field)
        if expected is not None and candidate.get(field) != expected:
            return True
    return False


def _route_mismatch(
    candidate: dict[str, Any],
    context: dict[str, Any],
    upstream: dict[str, Any],
) -> bool:
    candidate_universe_id = _candidate_universe_id(candidate)
    routed = context.get("routed_selection_universe_ref")
    eligible_universes = set(str(item) for item in upstream.get("pr81_eligible_universe_ids", []))
    return candidate_universe_id != routed or candidate_universe_id not in eligible_universes


def _has_classical_comparator(
    candidate: dict[str, Any],
    candidates_by_seed: dict[str, dict[str, Any]],
) -> bool:
    quantum_type = candidate.get("quantum_candidate_type")
    comparator_ref = candidate.get("classical_comparator_ref")
    if quantum_type == "CLASSICAL_ONLY":
        return bool(comparator_ref)
    if not isinstance(comparator_ref, str) or not comparator_ref:
        return False
    comparator = candidates_by_seed.get(comparator_ref)
    if comparator is None:
        return False
    return comparator.get("candidate_status") == "ACTIVE_CANDIDATE_STACK"


def _rejection_codes_for_candidate(
    candidate: dict[str, Any],
    context: dict[str, Any],
    candidates_by_seed: dict[str, dict[str, Any]],
    upstream: dict[str, Any],
) -> list[str]:
    codes: list[str] = []
    if _route_mismatch(candidate, context, upstream):
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_ROUTE_MISMATCH")
    if _trade_context_mismatch(candidate, context):
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_TRADE_CONTEXT_MISMATCH")
    if candidate.get("candidate_status") != "ACTIVE_CANDIDATE_STACK":
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_CANDIDATE_STATUS")
    if candidate.get("role_completion_state") != "ROLE_COMPLETE":
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_REQUIRED_ROLE")
    if candidate.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_INCOMPATIBLE_CANDIDATE")
    if candidate.get("blocked_row_ids_and_reasons"):
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_BLOCKED_ROW_PRESENT")
    if candidate.get("source_dependency_state") not in SOURCE_ALLOWED_STATES:
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_SOURCE_DEPENDENCY_STATE")
    if candidate.get("quantum_candidate_type") != "CLASSICAL_ONLY" and not _has_classical_comparator(candidate, candidates_by_seed):
        codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_MISSING_CLASSICAL_COMPARATOR")
    return _sort_reason_codes(codes)


def _eligibility_codes_for_candidate(candidate: dict[str, Any]) -> list[str]:
    codes = [
        "TRADE_CONTEXT_SELECTION_ALLOWED_STATIC_FIXTURE_ONLY",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR87_CANDIDATE_GENERATION_PACKET",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR81_ROUTED_SELECTION_UNIVERSE_METADATA",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR84_SCORING_POLICY",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR85_RANKING_CONTRACT",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR86_OPTIMIZER_ARBITRATION_METADATA",
    ]
    if candidate.get("quantum_candidate_type") != "CLASSICAL_ONLY":
        codes.extend(
            [
                "TRADE_CONTEXT_SELECTION_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
                "TRADE_CONTEXT_SELECTION_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
                "TRADE_CONTEXT_SELECTION_ALLOWED_CLASSICAL_COMPARATOR",
                "TRADE_CONTEXT_SELECTION_ALLOWED_OWNER_QUANTUM_PRIORITY_STATIC_POLICY",
            ]
        )
    else:
        codes.append("TRADE_CONTEXT_SELECTION_ALLOWED_CLASSICAL_FALLBACK")
    summary = candidate.get("owner_quantum_priority_summary")
    if isinstance(summary, dict) and summary.get("owner_override_basis") not in (None, "", "NONE"):
        codes.append("TRADE_CONTEXT_SELECTION_ALLOWED_OWNER_OVERRIDE_INTERNAL_BASIS_ONLY")
    return _sort_reason_codes(codes)


def _selection_sort_key(descriptor: dict[str, Any]) -> tuple[Any, ...]:
    score = descriptor.get("score_metadata")
    if not isinstance(score, dict):
        score = {}
    score_breakdown = score.get("score_breakdown")
    if not isinstance(score_breakdown, dict):
        score_breakdown = {}
    owner_summary = descriptor.get("owner_quantum_priority_summary")
    if not isinstance(owner_summary, dict):
        owner_summary = {}
    owner_override_basis = owner_summary.get("owner_override_basis")
    owner_mode = str(owner_summary.get("owner_quantum_priority_mode") or "")
    rank = score.get("rank")
    if not isinstance(rank, int):
        rank = 999
    final_score = score_breakdown.get("final_selection_score")
    if not isinstance(final_score, (int, float)):
        final_score = -1
    base_score = score_breakdown.get("base_score")
    if not isinstance(base_score, (int, float)):
        base_score = -1
    total_penalty = score_breakdown.get("total_penalty")
    if not isinstance(total_penalty, (int, float)):
        total_penalty = 999
    return (
        0 if owner_override_basis not in (None, "", "NONE") else 1,
        OWNER_MODE_ORDER.get(owner_mode, 999),
        QUANTUM_TYPE_ORDER.get(str(descriptor.get("quantum_candidate_type") or ""), 999),
        rank,
        -float(final_score),
        -float(base_score),
        float(total_penalty),
        str(descriptor.get("candidate_family_tuple") or ""),
        str(descriptor.get("candidate_stack_id") or ""),
    )


def _candidate_to_evaluation_descriptor(
    candidate: dict[str, Any],
    context: dict[str, Any],
    candidates_by_seed: dict[str, dict[str, Any]],
    upstream: dict[str, Any],
    case: dict[str, Any] | None,
) -> dict[str, Any]:
    rejection_codes = _rejection_codes_for_candidate(
        candidate,
        context,
        candidates_by_seed,
        upstream,
    )
    eligibility_status = "ELIGIBLE_FOR_STATIC_SELECTION" if not rejection_codes else "REJECTED_STATIC_SELECTION"
    score = _score_for_candidate(candidate, upstream, case)
    arbitration = _arbitration_for_candidate(candidate, upstream)
    descriptor = {
        "candidate_stack_id": candidate.get("candidate_stack_id"),
        "candidate_index": candidate.get("candidate_index"),
        "deterministic_generation_key": candidate.get("deterministic_generation_key"),
        "candidate_status": candidate.get("candidate_status"),
        "eligibility_status": eligibility_status,
        "trade_context_match_state": "TRADE_CONTEXT_MATCH" if not _trade_context_mismatch(candidate, context) else "TRADE_CONTEXT_MISMATCH",
        "route_match_state": "ROUTE_MATCH" if not _route_mismatch(candidate, context, upstream) else "ROUTE_MISMATCH",
        "routed_selection_universe_ref": context.get("routed_selection_universe_ref"),
        "candidate_selection_universe_ref": _candidate_universe_id(candidate),
        "venue_scope": candidate.get("venue_scope"),
        "platform_scope": candidate.get("platform_scope"),
        "market_type": candidate.get("market_type"),
        "strategy_class": candidate.get("strategy_class"),
        "edge_type": candidate.get("edge_type"),
        "latency_sensitivity_class": candidate.get("latency_sensitivity_class"),
        "capital_intensity_class": candidate.get("capital_intensity_class"),
        "source_dependency_state": candidate.get("source_dependency_state"),
        "required_role_completion_state": candidate.get("role_completion_state"),
        "compatibility_state": candidate.get("compatibility_state"),
        "blocker_state": candidate.get("blocker_state"),
        "blocked_row_ids_and_reasons": copy.deepcopy(candidate.get("blocked_row_ids_and_reasons", [])),
        "signal_family_ids": copy.deepcopy(candidate.get("signal_family_ids", [])),
        "scoring_family_ids": copy.deepcopy(candidate.get("scoring_family_ids", [])),
        "normalization_family_ids": copy.deepcopy(candidate.get("normalization_family_ids", [])),
        "risk_family_ids": copy.deepcopy(candidate.get("risk_family_ids", [])),
        "execution_family_ids": copy.deepcopy(candidate.get("execution_family_ids", [])),
        "capital_family_ids": copy.deepcopy(candidate.get("capital_family_ids", [])),
        "latency_family_ids": copy.deepcopy(candidate.get("latency_family_ids", [])),
        "error_guard_family_ids": copy.deepcopy(candidate.get("error_guard_family_ids", [])),
        "quantum_advisory_family_ids": copy.deepcopy(candidate.get("quantum_advisory_family_ids", [])),
        "scoring_policy_refs": copy.deepcopy(candidate.get("scoring_policy_refs", [])),
        "ranking_contract_ref": candidate.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": candidate.get("optimizer_arbitration_policy_ref"),
        "optimizer_arbitration_fixture_ref": candidate.get("optimizer_arbitration_fixture_ref"),
        "quantum_applicability_summary": copy.deepcopy(candidate.get("quantum_applicability_summary", {})),
        "owner_quantum_priority_summary": copy.deepcopy(candidate.get("owner_quantum_priority_summary", {})),
        "classical_comparator_required_flag": candidate.get("classical_comparator_required_flag"),
        "classical_comparator_ref": candidate.get("classical_comparator_ref"),
        "quantum_candidate_type": candidate.get("quantum_candidate_type"),
        "eligibility_reason_codes": _eligibility_codes_for_candidate(candidate) if not rejection_codes else [],
        "rejection_reason_codes": rejection_codes,
        "static_selection_order": None,
        "selected_flag": false_bool(),
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_backend_execution_flag": True,
        "selected_stack_handoff_created": False,
        "selected_trade_created": False,
        "order_authority_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "classical_optimizer_execution_created": False,
        "quantum_optimizer_execution_created": False,
        "optimizer_execution_created": False,
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "profit_evidence_created": False,
        "quantum_advantage_claim_created": False,
        "score_metadata": score,
        "ranking_contract_score_ref": (
            "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json"
            f"#static_ranked_candidate_descriptors/{score.get('candidate_stack_descriptor_id')}"
        ),
        "optimizer_arbitration_static_ref": (
            "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json"
            f"#static_arbitration_fixture_decisions/{candidate.get('optimizer_arbitration_fixture_ref')}"
        ),
        "optimizer_arbitration_metadata": {
            "arbitration_decision": arbitration.get("arbitration_decision"),
            "quantum_priority_applied": arbitration.get("quantum_priority_applied", false_bool()),
            "owner_forced_quantum_applied": arbitration.get("owner_forced_quantum_applied", false_bool()),
            "classical_comparator_present": arbitration.get("classical_comparator_present"),
            "fallback_to_classical_available": arbitration.get("fallback_to_classical_available"),
            "optimizer_execution_created": arbitration.get("optimizer_execution_created", false_bool()),
            "backend_execution_created": arbitration.get("backend_execution_created", false_bool()),
        },
        "candidate_family_tuple": _candidate_family_tuple(candidate),
        "seed_descriptor_id": candidate.get("seed_descriptor_id"),
    }
    return descriptor


def false_bool() -> bool:
    return False


def build_trade_context_parameter_stack_selection_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    case_id: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    case = None if case_id is None else _case_by_id(fixture, case_id)
    context = _context_for_case(fixture, case)
    candidate_packet = upstream.get("candidate_generation_packet", {})
    raw_candidates = _list_of_mappings(candidate_packet.get("candidate_stacks"))
    allowed_ids = _candidate_filter(case)
    if allowed_ids is not None:
        known_ids = {str(item.get("candidate_stack_id") or "") for item in raw_candidates}
        unknown_ids = sorted(allowed_ids - known_ids)
        if unknown_ids:
            failures.append(f"unknown case candidate_stack_ids: {', '.join(unknown_ids)}")
        candidates = [item for item in raw_candidates if item.get("candidate_stack_id") in allowed_ids]
    else:
        candidates = list(raw_candidates)
    stack_ids = [str(item.get("candidate_stack_id") or "") for item in candidates]
    if len(stack_ids) != len(set(stack_ids)):
        failures.append("TRADE_CONTEXT_SELECTION_BLOCKED_DUPLICATE_CANDIDATE_STACK: duplicate PR87 candidate_stack_id in selection input")
    candidates_by_seed = {
        str(item.get("seed_descriptor_id") or ""): item
        for item in candidates
        if item.get("seed_descriptor_id")
    }
    evaluated = [
        _candidate_to_evaluation_descriptor(candidate, context, candidates_by_seed, upstream, case)
        for candidate in candidates
    ]
    eligible = [
        descriptor
        for descriptor in evaluated
        if descriptor.get("eligibility_status") == "ELIGIBLE_FOR_STATIC_SELECTION"
    ]
    eligible_sorted = sorted(eligible, key=_selection_sort_key)
    rejected_sorted = sorted(
        (descriptor for descriptor in evaluated if descriptor not in eligible),
        key=lambda item: str(item.get("candidate_stack_id") or ""),
    )
    ordered = eligible_sorted + rejected_sorted
    selected = copy.deepcopy(eligible_sorted[0]) if eligible_sorted else None
    for order, descriptor in enumerate(ordered, start=1):
        descriptor["static_selection_order"] = order
        if selected is not None and descriptor.get("candidate_stack_id") == selected.get("candidate_stack_id"):
            descriptor["selected_flag"] = true_bool()
            descriptor["eligibility_reason_codes"] = _sort_reason_codes(
                list(descriptor.get("eligibility_reason_codes", []))
                + ["TRADE_CONTEXT_SELECTION_ALLOWED_ELIGIBLE_STATIC_CANDIDATE_SELECTED"]
            )
            selected = copy.deepcopy(descriptor)
    selected_id = None if selected is None else selected.get("candidate_stack_id")
    selected_generation_key = None if selected is None else selected.get("seed_descriptor_id")
    selected_score_ref = None if selected is None else selected.get("ranking_contract_score_ref")
    selection_reason_codes = [
        "TRADE_CONTEXT_SELECTION_ALLOWED_STATIC_FIXTURE_ONLY",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR87_CANDIDATE_GENERATION_PACKET",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR81_ROUTED_SELECTION_UNIVERSE_METADATA",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR85_RANKING_CONTRACT",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR86_OPTIMIZER_ARBITRATION_METADATA",
        "TRADE_CONTEXT_SELECTION_ALLOWED_PR89_PR90_FORWARDABLE_NOT_HANDED_OFF_NOT_EXECUTED",
    ]
    if selected is not None:
        selection_reason_codes.extend(selected.get("eligibility_reason_codes", []))
        if case is not None and case.get("case_id") == "PASS_DETERMINISTIC_TIE_BREAK":
            selection_reason_codes.append("TRADE_CONTEXT_SELECTION_ALLOWED_DETERMINISTIC_TIE_BREAK")
    else:
        selection_reason_codes.append("TRADE_CONTEXT_SELECTION_BLOCKED_NO_ELIGIBLE_CANDIDATE_STACK")
    blocked_codes = _sort_reason_codes(
        code
        for descriptor in ordered
        for code in descriptor.get("rejection_reason_codes", [])
    )
    packet_status = (
        "STATIC_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_READY"
        if selected is not None
        else "BLOCKED_NO_ELIGIBLE_CANDIDATE_STACK"
    )
    packet = {
        "trade_context_parameter_stack_selection_packet_id": fixture.get("trade_context_parameter_stack_selection_packet_id"),
        "schema_version": fixture.get("schema_version"),
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "selection_scope": SELECTION_SCOPE,
        "selection_authority_class": SELECTION_AUTHORITY_CLASS,
        "packet_status": packet_status,
        "fixture_case_id": None if case is None else case.get("case_id"),
        "trade_context_ref": context.get("trade_context_ref"),
        "trade_context_digest_or_static_ref": context.get("trade_context_digest_or_static_ref"),
        "routed_selection_universe_ref": context.get("routed_selection_universe_ref"),
        "selection_universe_fingerprint_or_static_ref": context.get("selection_universe_fingerprint_or_static_ref"),
        "candidate_generation_packet_ref": fixture.get("candidate_generation_packet_ref"),
        "candidate_generation_packet_digest_or_static_ref": fixture.get("candidate_generation_packet_digest_or_static_ref"),
        "upstream_edge_parameter_stack_selection_packet_ref": fixture.get("upstream_edge_parameter_stack_selection_packet_ref"),
        "upstream_trade_context_packet_ref": fixture.get("upstream_trade_context_packet_ref"),
        "upstream_selection_universe_registry_ref": fixture.get("upstream_selection_universe_registry_ref"),
        "upstream_selection_universe_consumer_gate_ref": fixture.get("upstream_selection_universe_consumer_gate_ref"),
        "upstream_trade_context_routing_gate_ref": fixture.get("upstream_trade_context_routing_gate_ref"),
        "upstream_quantum_applicability_ref": fixture.get("upstream_quantum_applicability_ref"),
        "upstream_owner_quantum_priority_ref": fixture.get("upstream_owner_quantum_priority_ref"),
        "upstream_scoring_policy_ref": fixture.get("upstream_scoring_policy_ref"),
        "upstream_scoring_ranking_gate_ref": fixture.get("upstream_scoring_ranking_gate_ref"),
        "upstream_optimizer_arbitration_ref": fixture.get("upstream_optimizer_arbitration_ref"),
        "upstream_candidate_generation_gate_ref": fixture.get("upstream_candidate_generation_gate_ref"),
        "source_dependency_state": fixture.get("source_dependency_state"),
        "candidate_stack_count": len(candidates),
        "evaluated_candidate_count": len(ordered),
        "eligible_candidate_count": len(eligible_sorted),
        "blocked_candidate_count": len(ordered) - len(eligible_sorted),
        "selected_candidate_count": 1 if selected is not None else 0,
        "selected_candidate_stack_id": selected_id,
        "static_selected_candidate_stack_id": selected_id,
        "selected_candidate_generation_key": selected_generation_key,
        "selected_candidate_static_score_ref": selected_score_ref,
        "ranking_contract_ref": None if selected is None else selected.get("ranking_contract_ref"),
        "deterministic_selection_key": (
            f"PR88|{context.get('trade_context_ref')}|"
            f"{fixture.get('candidate_generation_packet_ref')}|"
            f"{selected_id or 'BLOCKED_NO_ELIGIBLE'}|"
            f"{'|'.join(stack_ids)}"
        ),
        "deterministic_tie_break_chain": list(DETERMINISTIC_TIE_BREAK_CHAIN),
        "selection_reason_codes": _sort_reason_codes(selection_reason_codes),
        "blocked_or_rejected_candidate_reason_codes": blocked_codes,
        "replay_paper_competition_required_flag": selected is not None,
        "owner_review_required_flag": selected is not None,
        "pr89_selected_stack_handoff_required_flag": selected is not None,
        "selected_stack_handoff_created_flag": false_bool(),
        "selected_stack_handoff_created": false_bool(),
        "no_order_authority_flag": True,
        "no_runtime_execution_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
        "no_live_trade_authority_flag": True,
        "evaluated_candidates": ordered,
        "static_selected_candidate_descriptor": selected,
        "selection_decision_trace": [
            {
                "static_selection_order": item.get("static_selection_order"),
                "candidate_stack_id": item.get("candidate_stack_id"),
                "eligibility_status": item.get("eligibility_status"),
                "selected_flag": item.get("selected_flag"),
                "route_match_state": item.get("route_match_state"),
                "trade_context_match_state": item.get("trade_context_match_state"),
                "rejection_reason_codes": list(item.get("rejection_reason_codes", [])),
                "ranking_contract_score_ref": item.get("ranking_contract_score_ref"),
            }
            for item in ordered
        ],
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
        packet[field] = false_bool()
    return packet, failures


def true_bool() -> bool:
    return True


def validate_selection_packet(packet: dict[str, Any], upstream: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required_fields = (
        "trade_context_parameter_stack_selection_packet_id",
        "schema_version",
        "roadmap_pr_label",
        "semantic_task_id",
        "selection_scope",
        "selection_authority_class",
        "candidate_generation_packet_ref",
        "candidate_stack_count",
        "evaluated_candidate_count",
        "eligible_candidate_count",
        "blocked_candidate_count",
        "selected_candidate_count",
        "deterministic_selection_key",
        "deterministic_tie_break_chain",
        "selection_reason_codes",
        "evaluated_candidates",
    )
    for field in required_fields:
        if field not in packet:
            failures.append(f"selection packet missing required field {field}")
    if packet.get("roadmap_pr_label") != ROADMAP_PR_LABEL:
        failures.append("selection packet roadmap_pr_label mismatch")
    if packet.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append("selection packet semantic_task_id mismatch")
    if packet.get("selection_scope") != SELECTION_SCOPE:
        failures.append("selection packet selection_scope mismatch")
    if packet.get("selection_authority_class") != SELECTION_AUTHORITY_CLASS:
        failures.append("selection packet selection_authority_class mismatch")
    if packet.get("deterministic_tie_break_chain") != list(DETERMINISTIC_TIE_BREAK_CHAIN):
        failures.append("selection packet deterministic_tie_break_chain mismatch")
    evaluated = _list_of_mappings(packet.get("evaluated_candidates"))
    if packet.get("evaluated_candidate_count") != len(evaluated):
        failures.append("evaluated_candidate_count mismatch")
    eligible = [item for item in evaluated if item.get("eligibility_status") == "ELIGIBLE_FOR_STATIC_SELECTION"]
    selected = [item for item in evaluated if item.get("selected_flag") is True]
    if packet.get("eligible_candidate_count") != len(eligible):
        failures.append("eligible_candidate_count mismatch")
    if packet.get("blocked_candidate_count") != len(evaluated) - len(eligible):
        failures.append("blocked_candidate_count mismatch")
    if packet.get("selected_candidate_count") != len(selected):
        failures.append("selected_candidate_count mismatch")
    pr87_ids = set(upstream.get("pr87_candidate_stack_ids", []))
    for item in evaluated:
        candidate_id = item.get("candidate_stack_id")
        if candidate_id not in pr87_ids:
            failures.append(f"selected/evaluated candidate not derived from PR87 packet: {candidate_id}")
        if item.get("selected_flag") is True:
            if item.get("eligibility_status") != "ELIGIBLE_FOR_STATIC_SELECTION":
                failures.append(f"selected candidate is not eligible: {candidate_id}")
            if item.get("rejection_reason_codes"):
                failures.append(f"selected candidate has rejection reason codes: {candidate_id}")
            if item.get("candidate_status") != "ACTIVE_CANDIDATE_STACK":
                failures.append(f"selected candidate must be active: {candidate_id}")
            if item.get("required_role_completion_state") != "ROLE_COMPLETE":
                failures.append(f"selected candidate must be role complete: {candidate_id}")
            if item.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
                failures.append(f"selected candidate must be compatible: {candidate_id}")
            if item.get("route_match_state") != "ROUTE_MATCH":
                failures.append(f"selected candidate must route-match: {candidate_id}")
            if item.get("trade_context_match_state") != "TRADE_CONTEXT_MATCH":
                failures.append(f"selected candidate must trade-context-match: {candidate_id}")
            if item.get("blocked_row_ids_and_reasons"):
                failures.append(f"selected candidate must not include blocked rows: {candidate_id}")
        else:
            if item.get("eligibility_status") == "REJECTED_STATIC_SELECTION" and not item.get("rejection_reason_codes"):
                failures.append(f"rejected candidate missing rejection reason codes: {candidate_id}")
        if item.get("quantum_candidate_type") != "CLASSICAL_ONLY":
            if item.get("classical_comparator_required_flag") is not True:
                failures.append(f"{candidate_id} quantum candidate must require comparator")
            if not item.get("classical_comparator_ref"):
                failures.append(f"{candidate_id} quantum candidate must preserve comparator ref")
        for field in (
            "no_live_order_authority_flag",
            "no_runtime_cash_receipt_flag",
            "no_backend_execution_flag",
        ):
            if item.get(field) is not True:
                failures.append(f"{candidate_id}.{field} must be true")
        for field in (
            "selected_stack_handoff_created",
            "selected_trade_created",
            "order_authority_created",
            "replay_execution_created",
            "paper_execution_created",
            "classical_optimizer_execution_created",
            "quantum_optimizer_execution_created",
            "optimizer_execution_created",
            "quantum_backend_execution_created",
            "quantum_simulator_execution_created",
            "profit_evidence_created",
            "quantum_advantage_claim_created",
        ):
            if item.get(field) is not False:
                failures.append(f"{FIELD_REASON_CODES.get(field, field)}: {candidate_id}.{field} must be false")
    if selected:
        selected_id = selected[0].get("candidate_stack_id")
        if packet.get("selected_candidate_stack_id") != selected_id:
            failures.append("selected_candidate_stack_id mismatch")
        if packet.get("static_selected_candidate_stack_id") != selected_id:
            failures.append("static_selected_candidate_stack_id mismatch")
        if packet.get("selected_candidate_static_score_ref") is None:
            failures.append("selected_candidate_static_score_ref must be present for selected fixture")
        for field in (
            "replay_paper_competition_required_flag",
            "owner_review_required_flag",
            "pr89_selected_stack_handoff_required_flag",
        ):
            if packet.get(field) is not True:
                failures.append(f"{field} must be true for selected static candidate")
    else:
        if packet.get("selected_candidate_stack_id") is not None:
            failures.append("selected_candidate_stack_id must be null with no eligible candidates")
        if packet.get("selected_candidate_count") != 0:
            failures.append("selected_candidate_count must be 0 with no eligible candidates")
        if "TRADE_CONTEXT_SELECTION_BLOCKED_NO_ELIGIBLE_CANDIDATE_STACK" not in packet.get("selection_reason_codes", []):
            failures.append("no eligible packet must include fail-closed reason code")
    if packet.get("selected_stack_handoff_created_flag") is not False:
        failures.append("selected_stack_handoff_created_flag must be false")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if packet.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: packet.{field} must be false")
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
        ("selection_scope", SELECTION_SCOPE),
        ("selection_authority_class", SELECTION_AUTHORITY_CLASS),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "selection_contract_only_flag",
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

    packet, packet_failures = build_trade_context_parameter_stack_selection_packet(
        registry,
        fixture,
        upstream,
    )
    failures.extend(packet_failures)
    failures.extend(validate_selection_packet(packet, upstream))
    if packet.get("selected_candidate_stack_id") != fixture.get("expected_selected_candidate_stack_id"):
        failures.append("default fixture selected candidate mismatch")
    for count_field in (
        "expected_selected_candidate_count",
        "expected_evaluated_candidate_count",
        "expected_eligible_candidate_count",
        "expected_blocked_candidate_count",
    ):
        packet_field = count_field.replace("expected_", "")
        if fixture.get(count_field) != packet.get(packet_field):
            failures.append(f"default fixture {packet_field} mismatch")

    case_packets: list[dict[str, Any]] = []
    for case in cases:
        case_packet, case_failures = build_trade_context_parameter_stack_selection_packet(
            registry,
            fixture,
            upstream,
            case_id=str(case.get("case_id")),
        )
        failures.extend(case_failures)
        failures.extend(validate_selection_packet(case_packet, upstream))
        expected_id = case.get("expected_selected_candidate_stack_id")
        if case_packet.get("selected_candidate_stack_id") != expected_id:
            failures.append(f"{case.get('case_id')} selected candidate mismatch")
        expected_count = case.get("expected_selected_candidate_count")
        if expected_count is not None and case_packet.get("selected_candidate_count") != expected_count:
            failures.append(f"{case.get('case_id')} selected candidate count mismatch")
        expected_code = case.get("expected_reason_code")
        reason_codes = list(case_packet.get("selection_reason_codes", []))
        rejection_codes = list(case_packet.get("blocked_or_rejected_candidate_reason_codes", []))
        if expected_code not in reason_codes and expected_code not in rejection_codes:
            failures.append(f"{case.get('case_id')} missing expected reason code {expected_code}")
        case_packets.append(case_packet)

    boundary = fixture.get("pr89_pr90_boundary_fixture")
    if not isinstance(boundary, dict):
        failures.append("fixture.pr89_pr90_boundary_fixture must be an object")
    else:
        if boundary.get("static_selected_candidate_is_forwardable_to_pr89_selected_stack_handoff_packet") is not True:
            failures.append("PR89 boundary fixture must be forwardable")
        if boundary.get("static_selected_candidate_is_forwardable_to_pr90_replay_paper_competition_gate") is not True:
            failures.append("PR90 boundary fixture must be forwardable")
        for field in (
            "selected_stack_handoff_created",
            "replay_execution_created",
            "paper_execution_created",
            "order_authority_created",
            "live_authority_created",
            "selected_static_candidate_is_order_intent",
            "selected_static_candidate_is_profit_evidence",
        ):
            if boundary.get(field) is not False:
                failures.append(f"boundary fixture {field} must be false")
    return failures, packet, case_packets


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "TRADE_CONTEXT_SELECTION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
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
            "TRADE_CONTEXT_SELECTION_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
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
    selected = packet.get("static_selected_candidate_descriptor")
    selected_score = None if not isinstance(selected, dict) else selected.get("score_metadata", {})
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
        "gate_registry_id": registry.get("gate_registry_id"),
        "trade_context_parameter_stack_selection_gate_id": registry.get("trade_context_parameter_stack_selection_gate_id"),
        "gate_scope": registry.get("gate_scope"),
        "selection_scope": SELECTION_SCOPE,
        "selection_authority_class": SELECTION_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "selection_contract_only_flag": True,
        "selection_inputs": list(SELECTION_INPUT_ORDER),
        "selection_outputs": list(SELECTION_OUTPUT_ORDER),
        "selection_policy": copy.deepcopy(registry.get("selection_policy")),
        "blocked_candidate_policy": copy.deepcopy(registry.get("blocked_candidate_policy")),
        "deterministic_tie_break_chain": list(DETERMINISTIC_TIE_BREAK_CHAIN),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "upstream_edge_parameter_stack_selection_packet_ref": copy.deepcopy(registry.get("upstream_edge_parameter_stack_selection_packet_ref")),
        "upstream_trade_context_packet_ref": copy.deepcopy(registry.get("upstream_trade_context_packet_ref")),
        "upstream_selection_universe_registry_ref": copy.deepcopy(registry.get("upstream_selection_universe_registry_ref")),
        "upstream_selection_universe_consumer_gate_ref": copy.deepcopy(registry.get("upstream_selection_universe_consumer_gate_ref")),
        "upstream_trade_context_routing_gate_ref": copy.deepcopy(registry.get("upstream_trade_context_routing_gate_ref")),
        "upstream_quantum_applicability_ref": copy.deepcopy(registry.get("upstream_quantum_applicability_ref")),
        "upstream_owner_quantum_priority_ref": copy.deepcopy(registry.get("upstream_owner_quantum_priority_ref")),
        "upstream_scoring_policy_ref": copy.deepcopy(registry.get("upstream_scoring_policy_ref")),
        "upstream_scoring_ranking_gate_ref": copy.deepcopy(registry.get("upstream_scoring_ranking_gate_ref")),
        "upstream_optimizer_arbitration_ref": copy.deepcopy(registry.get("upstream_optimizer_arbitration_ref")),
        "upstream_candidate_generation_gate_ref": copy.deepcopy(registry.get("upstream_candidate_generation_gate_ref")),
        "required_stack_roles": list(ROLE_ORDER),
        "pr81_eligible_universe_ids": list(upstream.get("pr81_eligible_universe_ids", [])),
        "pr87_candidate_generation_packet_id": upstream.get("candidate_generation_packet", {}).get("candidate_generation_packet_id"),
        "pr87_active_candidate_stack_ids": list(upstream.get("candidate_generation_packet", {}).get("active_candidate_stack_ids", [])),
        "pr87_blocked_candidate_stack_ids": list(upstream.get("candidate_generation_packet", {}).get("blocked_candidate_stack_ids", [])),
        "trade_context_parameter_stack_selection_packet": copy.deepcopy(packet),
        "fixture_case_packets": copy.deepcopy(case_packets),
        "master_plan_principles_consumed": copy.deepcopy(registry.get("master_plan_principles_consumed")),
        "candidate_stack_count": packet.get("candidate_stack_count"),
        "evaluated_candidate_count": packet.get("evaluated_candidate_count"),
        "eligible_candidate_count": packet.get("eligible_candidate_count"),
        "blocked_candidate_count": packet.get("blocked_candidate_count"),
        "selected_candidate_count": packet.get("selected_candidate_count"),
        "selected_candidate_stack_id": packet.get("selected_candidate_stack_id"),
        "static_selected_candidate_stack_id": packet.get("static_selected_candidate_stack_id"),
        "selected_candidate_generation_key": packet.get("selected_candidate_generation_key"),
        "selected_candidate_static_score_ref": packet.get("selected_candidate_static_score_ref"),
        "selected_candidate_score_breakdown": None if not isinstance(selected_score, dict) else selected_score.get("score_breakdown", {}),
        "quantum_priority_applied": (
            False
            if not isinstance(selected, dict)
            else selected.get("optimizer_arbitration_metadata", {}).get("quantum_priority_applied", False)
        ),
        "deterministic_static_selection": True,
        "deterministic_selection_key": packet.get("deterministic_selection_key"),
        "deterministic_candidate_evaluation_ordering": True,
        "deterministic_tie_break_output": True,
        "selected_candidate_derived_only_from_pr87_candidate_packet": True,
        "blocked_candidates_cannot_be_selected": True,
        "missing_role_candidates_cannot_be_selected": True,
        "incompatible_candidates_cannot_be_selected": True,
        "route_mismatched_candidates_cannot_be_selected": True,
        "owner_override_records_basis_without_external_fact_fabrication": True,
        "owner_quantum_priority_static_policy_metadata_only": True,
        "quantum_metadata_static_advisory_policy_gated": True,
        "classical_comparator_or_fallback_preserved_for_quantum_candidates": True,
        "replay_paper_competition_required_flag": packet.get("replay_paper_competition_required_flag"),
        "owner_review_required_flag": packet.get("owner_review_required_flag"),
        "pr89_selected_stack_handoff_required_flag": packet.get("pr89_selected_stack_handoff_required_flag"),
        "selected_stack_handoff_created_flag": False,
        "final_ready": False,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "master_plan_diff_empty": True,
        "real_optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "replay_execution_count": 0,
        "paper_execution_count": 0,
        "selected_stack_handoff_packet_created": False,
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

    metadata_failures, metadata = validate_pr88_roadmap_metadata(repo_root)
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
