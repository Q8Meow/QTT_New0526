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
from tools import validate_quantum_classical_optimizer_arbitration_gate as pr86_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "candidate_parameter_stack_generation_gate.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "CandidateParameterStackGenerationGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_candidate_parameter_stack_generation_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "CandidateParameterStackGenerationGate.report.json"
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

GATE_REGISTRY_ID = "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE"
GATE_ID = "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_V1"
REPORT_ID = "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_REPORT"
POLICY_VERSION = "v1"
ROADMAP_PR_LABEL = "PR #87"
GITHUB_PR_NUMBER_POLICY = "may differ"
SEMANTIC_TASK_ID = "ROADMAP-CANDIDATE-PARAMETER-STACK-GENERATION-GATE"
TARGET_BRANCH = "pr87-candidate-parameter-stack-generation-gate"
EXPECTED_BASELINE_ANCESTOR = "8b87f44"
GATE_SCOPE = "STATIC_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_ONLY"
GENERATION_SCOPE = "STATIC_ONLY"
GENERATION_AUTHORITY_CLASS = (
    "STATIC_CANDIDATE_GENERATION_GATE_NOT_SELECTION_NOT_EXECUTION"
)
SUCCESS_MARKER = "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK"
FAILURE_MARKER = "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_FAILED"
CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_MODE_ACTIVE"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"

ROLE_ORDER = (
    "SIGNAL",
    "SCORING",
    "NORMALIZATION",
    "RISK",
    "EXECUTION",
    "CAPITAL",
    "LATENCY",
    "ERROR_GUARD",
    "QUANTUM_ADVISORY",
)
DEPENDENCY_ORDER = (
    "PR73_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY",
    "PR74_ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE",
    "PR75_ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE",
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
)
DEPENDENCY_MARKERS = {
    "PR73_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY": "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK",
    "PR74_ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE": "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK",
    "PR75_ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE": "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK",
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
}
FUTURE_CONSUMER_ORDER = (
    "PR88_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
    "PR89_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
    "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
    "PR105_PR151_STAGE1_RUNTIME_LIVE_LAUNCH_CLOSURE_CONSUMERS",
)
GENERATION_INPUT_ORDER = (
    "synthetic_static_candidate_seed_descriptors",
    "PR81_routed_selection_universe_metadata",
    "PR79_selection_universe_registry_metadata",
    "PR82_quantum_applicability_metadata",
    "PR83_owner_quantum_priority_policy_metadata",
    "PR84_scoring_policy_registry",
    "PR85_static_ranked_candidate_descriptor_metadata",
    "PR86_static_optimizer_arbitration_metadata",
    "PR73_PR74_PR75_role_completeness_and_compatibility_metadata",
)
GENERATION_OUTPUT_ORDER = (
    "static_candidate_generation_packet",
    "active_candidate_stack_descriptors",
    "blocked_candidate_stack_descriptors",
    "generation_reason_codes",
    "no_selection_boundary",
    "no_runtime_execution_boundary",
    "no_backend_execution_boundary",
    "pr88_pr90_forwardable_boundary",
)
DETERMINISTIC_SORT_KEY_ORDER = (
    "active_candidate_status_before_blocked",
    "role_completion_state",
    "compatibility_state",
    "owner_override_internal_inclusion_order_when_recorded",
    "owner_quantum_priority_policy_when_enabled",
    "quantum_applicability_metadata_with_classical_comparator_preserved",
    "latency_sensitivity_static_metadata",
    "risk_family_static_metadata",
    "lexicographic_candidate_family_tuple",
    "lexicographic_candidate_stack_id",
)
REASON_CODE_ORDER = (
    "CANDIDATE_GENERATION_ALLOWED_STATIC_FIXTURE_ONLY",
    "CANDIDATE_GENERATION_ALLOWED_ROUTED_SELECTION_UNIVERSE_METADATA",
    "CANDIDATE_GENERATION_ALLOWED_SELECTION_UNIVERSE_METADATA",
    "CANDIDATE_GENERATION_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
    "CANDIDATE_GENERATION_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
    "CANDIDATE_GENERATION_ALLOWED_PR84_SCORING_POLICY",
    "CANDIDATE_GENERATION_ALLOWED_PR85_RANKING_CONTRACT",
    "CANDIDATE_GENERATION_ALLOWED_PR86_OPTIMIZER_ARBITRATION_METADATA",
    "CANDIDATE_GENERATION_ALLOWED_CLASSICAL_COMPARATOR",
    "CANDIDATE_GENERATION_ALLOWED_CLASSICAL_FALLBACK",
    "CANDIDATE_GENERATION_ALLOWED_OWNER_OVERRIDE_INTERNAL_ORDER_ONLY",
    "CANDIDATE_GENERATION_ALLOWED_MULTIPLE_STATIC_CANDIDATES",
    "CANDIDATE_GENERATION_ALLOWED_PR88_PR90_FORWARDABLE_NOT_SELECTED",
    "CANDIDATE_GENERATION_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR",
    "CANDIDATE_GENERATION_BLOCKED_DUPLICATE_CANDIDATE_STACK",
    "CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_FIELD",
    "CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_ROLE",
    "CANDIDATE_GENERATION_BLOCKED_INCOMPATIBLE_ROLE_TUPLE",
    "CANDIDATE_GENERATION_BLOCKED_SOURCE_DEPENDENCY_STATE",
    "CANDIDATE_GENERATION_BLOCKED_UNKNOWN_QUANTUM_CANDIDATE_TYPE",
    "CANDIDATE_GENERATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR",
    "CANDIDATE_GENERATION_BLOCKED_INSUFFICIENT_CANDIDATE_STACKS",
    "CANDIDATE_GENERATION_BLOCKED_RANDOM_GENERATION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_WALL_CLOCK_IDENTITY_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_FINAL_SELECTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "CANDIDATE_GENERATION_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_PR87_METADATA_VERIFIED",
    "PASS_VALID_MULTI_CANDIDATE_GENERATION",
    "PASS_DETERMINISTIC_CANDIDATE_IDS_AND_ORDERING",
    "PASS_QUANTUM_PREFERRED_WITH_CLASSICAL_COMPARATOR",
    "PASS_OWNER_OVERRIDE_INTERNAL_ORDER_NO_FABRICATION",
    "PASS_BLOCKED_MISSING_ROLE_TRACEABLE",
    "PASS_BLOCKED_INCOMPATIBLE_ROLE_TUPLE_TRACEABLE",
    "PASS_INSUFFICIENT_CANDIDATE_COUNT_FAILS_CLOSED",
    "PASS_PR88_PR90_BOUNDARY_NOT_SELECTED_NOT_EXECUTED",
    "BLOCK_RANDOM_GENERATION_POLICY",
    "BLOCK_WALL_CLOCK_IDENTITY_POLICY",
    "BLOCK_FINAL_SELECTION_CLAIM",
    "BLOCK_SELECTED_STACK_CLAIM",
    "BLOCK_ORDER_AUTHORITY_CLAIM",
    "BLOCK_REPLAY_PAPER_EXECUTION_CLAIM",
    "BLOCK_OPTIMIZER_EXECUTION_CLAIM",
    "BLOCK_QUANTUM_BACKEND_OR_SIMULATOR_CLAIM",
    "BLOCK_SOURCE_CONNECTOR_RUNTIME_CASH_CLAIM",
    "BLOCK_PROFIT_OR_ADVANTAGE_CLAIM",
    "BLOCK_ATOMICROWS_BUNDLE_JSONL",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
)
EXPECTED_ACTIVE_CANDIDATE_IDS = (
    "PR87_CANDIDATE_STACK__OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
    "PR87_CANDIDATE_STACK__QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
    "PR87_CANDIDATE_STACK__HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
    "PR87_CANDIDATE_STACK__CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
)
EXPECTED_BLOCKED_CANDIDATE_IDS = (
    "PR87_CANDIDATE_STACK__BLOCKED_INCOMPATIBLE_ROLE_TUPLE_FIXTURE",
    "PR87_CANDIDATE_STACK__BLOCKED_MISSING_SIGNAL_ROLE_FIXTURE",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "final_selection_created",
    "selected_stack_created",
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
    "random_generation_used",
    "wall_clock_identity_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
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
    "static_candidate_generation_packet_is_final_selection",
    "static_candidate_generation_packet_is_live_order_authority",
    "static_candidate_generation_packet_is_trading_signal",
    "quantum_applicability_metadata_is_backend_evidence",
    "owner_quantum_priority_fabricates_external_facts",
    "owner_override_fabricates_external_facts",
    "future_pr88_trade_context_selection_implemented",
    "future_pr89_selected_stack_handoff_implemented",
    "future_pr90_replay_paper_competition_implemented",
    "future_live_authority_implemented",
)
FIELD_REASON_CODES = {
    "final_selection_created": "CANDIDATE_GENERATION_BLOCKED_FINAL_SELECTION_FORBIDDEN",
    "selected_stack_created": "CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "selected_stack_id_emitted": "CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "selected_trade_created": "CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "live_authority_created": "CANDIDATE_GENERATION_BLOCKED_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "order_authority_created": "CANDIDATE_GENERATION_BLOCKED_ORDER_AUTHORITY_FORBIDDEN",
    "source_retrieval_created": "CANDIDATE_GENERATION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "source_acceptance_created": "CANDIDATE_GENERATION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "connector_semantic_binding_created": "CANDIDATE_GENERATION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created": "CANDIDATE_GENERATION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "private_state_fetch_created": "CANDIDATE_GENERATION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "replay_execution_created": "CANDIDATE_GENERATION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "paper_execution_created": "CANDIDATE_GENERATION_BLOCKED_REPLAY_PAPER_EXECUTION_FORBIDDEN",
    "classical_optimizer_execution_created": "CANDIDATE_GENERATION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created": "CANDIDATE_GENERATION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created": "CANDIDATE_GENERATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "backend_execution_created": "CANDIDATE_GENERATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_backend_execution_created": "CANDIDATE_GENERATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created": "CANDIDATE_GENERATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "qaoa_execution_created": "CANDIDATE_GENERATION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "vqe_execution_created": "CANDIDATE_GENERATION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "annealing_execution_created": "CANDIDATE_GENERATION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "qubo_solve_execution_created": "CANDIDATE_GENERATION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "ising_solve_execution_created": "CANDIDATE_GENERATION_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "profit_evidence_created": "CANDIDATE_GENERATION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created": "CANDIDATE_GENERATION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created": "CANDIDATE_GENERATION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "execution_superiority_claim_created": "CANDIDATE_GENERATION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "random_generation_used": "CANDIDATE_GENERATION_BLOCKED_RANDOM_GENERATION_FORBIDDEN",
    "wall_clock_identity_used": "CANDIDATE_GENERATION_BLOCKED_WALL_CLOCK_IDENTITY_FORBIDDEN",
    "atomicrows_bundle_jsonl_created": "CANDIDATE_GENERATION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "CANDIDATE_GENERATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
}
SOURCE_BLOCKED_STATES = {
    "BLOCKED",
    "SOURCE_MISSING",
    "NEGATIVE_NET_PROFIT",
    "UNKNOWN",
    "OWNER_PENDING",
    "REJECTED",
    "DORMANT_WITHOUT_REHAB_ROUTE",
}
OWNER_MODE_ORDER = {
    "OWNER_FORCED_QUANTUM": 0,
    "QUANTUM_FIRST": 1,
    "QUANTUM_STRONGLY_PREFERRED": 2,
    "QUANTUM_PREFERRED": 3,
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK": 4,
    "QUANTUM_NEUTRAL": 5,
}
QUANTUM_TYPE_ORDER = {
    "TRUE_QUANTUM": 0,
    "HYBRID_CLASSICAL_QUANTUM": 1,
    "QUANTUM_INSPIRED": 2,
    "QUBO_COMPATIBLE": 3,
    "ISING_COMPATIBLE": 4,
    "QAOA_COMPATIBLE": 5,
    "VQE_COMPATIBLE": 6,
    "ANNEALING_COMPATIBLE": 7,
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE": 8,
    "CLASSICAL_ONLY": 9,
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
    return pr86_gate.load_yaml(path)


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
    except Exception as exc:  # pragma: no cover - defensive detail for validator CLI
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:  # pragma: no cover - defensive detail for validator CLI
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
    return ci_branch_context.is_downstream_or_main_validation_branch(branch, after_pr=87)


def validate_pr87_roadmap_metadata(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    info_lines: list[str] = []
    github_actions = _github_actions_active()
    roadmap = load_json(_resolve(repo_root, ROADMAP_INDEX))
    blueprint = load_json(_resolve(repo_root, BLUEPRINT_INDEX))
    roadmap_entries = _list_of_mappings(roadmap.get("pr_entries"))
    blueprint_entries = _list_of_mappings(blueprint.get("entries"))
    roadmap_entry = next((item for item in roadmap_entries if item.get("number") == 87), None)
    blueprint_entry = next((item for item in blueprint_entries if item.get("number") == 87), None)
    if roadmap_entry is None:
        failures.append("PR87 roadmap index entry missing")
        roadmap_entry = {}
    if blueprint_entry is None:
        failures.append("PR87 blueprint index entry missing")
        blueprint_entry = {}

    checks = (
        ("roadmap.delivery_label", roadmap_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("roadmap.title", roadmap_entry.get("title"), "Candidate parameter-stack generation gate"),
        ("roadmap.branch", roadmap_entry.get("branch"), TARGET_BRANCH),
        ("roadmap.marker", roadmap_entry.get("marker"), SUCCESS_MARKER),
        ("blueprint.delivery_label", blueprint_entry.get("delivery_label"), ROADMAP_PR_LABEL),
        ("blueprint.title", blueprint_entry.get("title"), "Candidate parameter-stack generation gate"),
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
        failures.append("upstream_dependencies must use canonical PR73-PR86 dependency order")
    for dependency in _list_of_mappings(payload.get("upstream_dependencies")):
        artifact_id = str(dependency.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker is None:
            failures.append(f"unknown upstream dependency {artifact_id}")
            continue
        if dependency.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id} validation_marker must be {expected_marker}")
        for field in ("registry_path", "report_path", "validator_path"):
            value = dependency.get(field)
            if not isinstance(value, str) or not value:
                failures.append(f"{artifact_id}.{field} missing")
            elif not _resolve(repo_root, pathlib.Path(value)).exists():
                failures.append(f"{artifact_id}.{field} path missing: {value}")
    return failures


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumer_ids = [
        str(item.get("consumer_id") or "")
        for item in _list_of_mappings(payload.get("future_consumers"))
    ]
    if consumer_ids != list(FUTURE_CONSUMER_ORDER):
        failures.append("future_consumers must use canonical PR88+ order")
    for consumer in _list_of_mappings(payload.get("future_consumers")):
        if consumer.get("pr87_creates_consumer_execution") is not False:
            failures.append(
                f"{consumer.get('consumer_id')}.pr87_creates_consumer_execution must be false"
            )
    return failures


def validate_generation_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = payload.get("generation_policy")
    if not isinstance(policy, dict):
        return ["generation_policy must be an object"]
    expected = {
        "generation_policy_id": "CANDIDATE_PARAMETER_STACK_GENERATION_POLICY_V1",
        "generation_contract_version": "v1",
        "minimum_valid_candidate_stack_count": 2,
        "maximum_total_candidate_stack_count": 8,
        "stable_sort_required": True,
        "random_generation_allowed": False,
        "wall_clock_identity_allowed": False,
        "selected_stack_id_emitted": False,
        "final_selection_created": False,
        "owner_override_can_force_internal_inclusion_order": True,
        "owner_quantum_priority_can_affect_static_generation_order": True,
        "quantum_candidates_require_classical_comparator_or_fallback": True,
        "replay_paper_competition_required_for_active_candidates": True,
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            failures.append(f"generation_policy.{field} must be {value}")
    if policy.get("candidate_status_order") != [
        "ACTIVE_CANDIDATE_STACK",
        "BLOCKED_CANDIDATE_STACK",
    ]:
        failures.append("generation_policy.candidate_status_order must be active then blocked")
    if policy.get("deterministic_sort_key_order") != list(DETERMINISTIC_SORT_KEY_ORDER):
        failures.append("generation_policy.deterministic_sort_key_order mismatch")
    return failures


def validate_blocked_candidate_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = payload.get("blocked_candidate_policy")
    if not isinstance(policy, dict):
        return ["blocked_candidate_policy must be an object"]
    if policy.get("blocked_candidate_policy_id") != "CANDIDATE_PARAMETER_STACK_GENERATION_BLOCKED_POLICY_V1":
        failures.append("blocked_candidate_policy.blocked_candidate_policy_id mismatch")
    if policy.get("blocked_candidates_remain_traceable") is not True:
        failures.append("blocked candidates must remain traceable")
    if policy.get("blocked_candidates_enter_active_candidate_status") is not False:
        failures.append("blocked candidates must not enter active candidate status")
    if policy.get("blocked_candidates_retain_reason_codes") is not True:
        failures.append("blocked candidates must retain reason codes")
    if policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
        failures.append("blocked_candidate_policy.blocked_reason_code_order mismatch")
    return failures


def validate_no_authority_flags(
    payload: dict[str, Any], *, field_path: str = "required_no_authority_flags"
) -> list[str]:
    failures: list[str] = []
    flags = payload.get("required_no_authority_flags")
    if not isinstance(flags, dict):
        return [f"{field_path} must be an object"]
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if flags.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: {field_path}.{field} must be false")
    return failures


def validate_gate_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    expected_fields = {
        "gate_registry_id": GATE_REGISTRY_ID,
        "candidate_generation_gate_id": GATE_ID,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "gate_scope": GATE_SCOPE,
        "policy_version": POLICY_VERSION,
        "generation_scope": GENERATION_SCOPE,
        "generation_authority_class": GENERATION_AUTHORITY_CLASS,
        "final_ready": False,
    }
    for field, expected in expected_fields.items():
        if payload.get(field) != expected:
            failures.append(f"registry.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "candidate_generation_contract_only_flag",
    ):
        if payload.get(field) is not True:
            failures.append(f"registry.{field} must be true")
    if payload.get("required_stack_roles") != list(ROLE_ORDER):
        failures.append("registry.required_stack_roles must match PR73/PR74/PR75 role order")
    if payload.get("generation_inputs") != list(GENERATION_INPUT_ORDER):
        failures.append("registry.generation_inputs mismatch")
    if payload.get("generation_outputs") != list(GENERATION_OUTPUT_ORDER):
        failures.append("registry.generation_outputs mismatch")
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("registry.reason_codes must use canonical order")
    if payload.get("stage1_prediction_market_contexts") != [
        "KALSHI",
        "POLYMARKET",
        "FORECASTEX_IBKR",
    ]:
        failures.append("registry.stage1_prediction_market_contexts mismatch")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_generation_policy(payload))
    failures.extend(validate_blocked_candidate_policy(payload))
    failures.extend(validate_no_authority_flags(payload))
    if len(_list_of_mappings(payload.get("master_plan_principles_consumed"))) < 7:
        failures.append("registry.master_plan_principles_consumed must record all PR87 master-plan principles")
    return failures


def _validate_report_marker(report: dict[str, Any] | None, marker: str, label: str) -> list[str]:
    if report is None:
        return [f"{label} report missing"]
    if report.get("validation_marker") != marker:
        return [f"{label} report validation_marker must be {marker}"]
    return []


def validate_upstream_reports(
    repo_root: pathlib.Path,
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr82_failures, pr82_labels = pr86_gate.pr85_gate.pr84_gate.validate_pr82_registry(repo_root)
    pr83_failures, pr83_policy = pr86_gate.pr85_gate.pr84_gate.validate_pr83_policy(repo_root)
    pr84_failures, pr84_policy = pr86_gate.pr85_gate.validate_pr84_policy(repo_root)
    pr85_failures, pr85_report = pr86_gate.validate_pr85_gate(repo_root)
    failures.extend(pr82_failures)
    failures.extend(pr83_failures)
    failures.extend(pr84_failures)
    failures.extend(pr85_failures)

    pr81_report, pr81_report_failures = _load_json_checked(
        repo_root
        / "docs"
        / "master_plan"
        / "generated"
        / "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json",
        "PR81_REPORT",
    )
    pr86_registry, pr86_registry_failures = _load_yaml_checked(
        repo_root / pr86_gate.DEFAULT_PRODUCTION_REGISTRY,
        "PR86_REGISTRY",
    )
    pr86_report, pr86_report_failures = _load_json_checked(
        repo_root / pr86_gate.DEFAULT_REPORT,
        "PR86_REPORT",
    )
    failures.extend(pr81_report_failures)
    failures.extend(pr86_registry_failures)
    failures.extend(pr86_report_failures)
    if pr81_report is not None:
        failures.extend(
            _validate_report_marker(
                pr81_report,
                "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK",
                "PR81",
            )
        )
    if pr86_registry is not None:
        if pr86_registry.get("semantic_task_id") != pr86_gate.SEMANTIC_TASK_ID:
            failures.append("PR86 registry semantic_task_id mismatch")
        if pr86_registry.get("gate_scope") != pr86_gate.GATE_SCOPE:
            failures.append("PR86 registry gate_scope mismatch")
    failures.extend(_validate_report_marker(pr86_report, pr86_gate.SUCCESS_MARKER, "PR86"))

    return failures, {
        "pr82_labels": _sort_by_order(
            pr82_labels, pr86_gate.pr85_gate.pr84_gate.PR82_LABEL_ORDER
        ),
        "pr83_modes": list(pr86_gate.pr85_gate.pr84_gate.PR83_MODE_ORDER),
        "pr83_default_mode": None if pr83_policy is None else pr83_policy.get("default_quantum_priority_mode"),
        "pr84_formula_ids": [] if pr84_policy is None else [
            item.get("formula_id")
            for item in _list_of_mappings(pr84_policy.get("formula_definitions"))
        ],
        "pr85_candidate_descriptor_ids": [] if pr85_report is None else list(
            pr85_report.get("candidate_descriptor_ids", [])
        ),
        "pr85_ranked_candidate_descriptor_ids": [] if pr85_report is None else list(
            pr85_report.get("ranked_candidate_descriptor_ids", [])
        ),
        "pr85_blocked_candidate_descriptor_ids": [] if pr85_report is None else list(
            pr85_report.get("blocked_candidate_descriptor_ids", [])
        ),
        "pr86_arbitration_fixture_ids": [] if pr86_report is None else list(
            pr86_report.get("arbitration_fixture_ids", [])
        ),
        "pr86_ordered_fixture_ids": [] if pr86_report is None else list(
            pr86_report.get("arbitration_ordered_fixture_ids", [])
        ),
        "pr81_eligible_universe_ids": [] if pr81_report is None else list(
            pr81_report.get("final_route_eligible_universe_ids", [])
        ),
    }


def _candidate_stack_id(seed_id: str) -> str:
    return f"PR87_CANDIDATE_STACK__{seed_id}"


def _role_tuple(role_map: dict[str, Any]) -> str:
    return "|".join(f"{role}:{role_map.get(role, 'MISSING_ROLE')}" for role in ROLE_ORDER)


def _candidate_family_tuple(seed: dict[str, Any]) -> str:
    families: list[str] = []
    for field in (
        "signal_family_ids",
        "scoring_family_ids",
        "normalization_family_ids",
        "risk_family_ids",
        "execution_family_ids",
        "capital_family_ids",
        "latency_family_ids",
        "error_guard_family_ids",
        "quantum_advisory_family_ids",
    ):
        value = seed.get(field)
        if isinstance(value, list):
            families.extend(str(item) for item in value)
    return "|".join(sorted(families))


def _missing_roles(seed: dict[str, Any]) -> list[str]:
    role_map = seed.get("selected_stack_role_map")
    if not isinstance(role_map, dict):
        return list(ROLE_ORDER)
    return [role for role in ROLE_ORDER if role not in role_map]


def _reason_code_list(value: Any, label: str, failures: list[str]) -> list[str]:
    if not isinstance(value, list):
        failures.append(f"CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_FIELD: {label} must be a list")
        return []
    codes = [str(code) for code in value]
    for code in codes:
        if code not in REASON_CODE_ORDER:
            failures.append(f"CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_FIELD: {label} has unknown reason code {code}")
    if codes != _sort_reason_codes(codes):
        failures.append(f"{label} must use canonical reason-code order")
    return codes


def _blocked_reasons_for_seed(
    seed: dict[str, Any],
    *,
    seed_ids: set[str],
    upstream: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    required_fields = (
        "seed_descriptor_id",
        "candidate_authority_class",
        "platform_scope",
        "venue_scope",
        "market_type",
        "strategy_class",
        "edge_type",
        "latency_sensitivity_class",
        "capital_intensity_class",
        "source_dependency_state",
        "selected_stack_role_map",
        "quantum_candidate_type",
        "owner_quantum_priority_mode",
        "scoring_policy_refs",
        "ranking_contract_ref",
        "optimizer_arbitration_policy_ref",
        "optimizer_arbitration_fixture_ref",
        "pr85_candidate_descriptor_ref",
        "role_completion_state",
        "compatibility_state",
        "blocker_state",
        "generation_reason_codes",
    )
    for field in required_fields:
        if field not in seed:
            reasons.append("CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_FIELD")
    if _missing_roles(seed):
        reasons.append("CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_ROLE")
    if seed.get("role_completion_state") != "ROLE_COMPLETE":
        reasons.append("CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_ROLE")
    if seed.get("compatibility_state") != "COMPATIBLE_ROLE_TUPLE":
        reasons.append("CANDIDATE_GENERATION_BLOCKED_INCOMPATIBLE_ROLE_TUPLE")
    if seed.get("source_dependency_state") in SOURCE_BLOCKED_STATES:
        reasons.append("CANDIDATE_GENERATION_BLOCKED_SOURCE_DEPENDENCY_STATE")
    quantum_type = str(seed.get("quantum_candidate_type") or "")
    if quantum_type not in upstream.get("pr82_labels", []):
        reasons.append("CANDIDATE_GENERATION_BLOCKED_UNKNOWN_QUANTUM_CANDIDATE_TYPE")
    if quantum_type != "CLASSICAL_ONLY":
        comparator = seed.get("classical_comparator_ref")
        if not isinstance(comparator, str) or not comparator or comparator not in seed_ids:
            reasons.append("CANDIDATE_GENERATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR")
    if seed.get("owner_quantum_priority_mode") not in upstream.get("pr83_modes", []):
        reasons.append("CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_FIELD")
    if seed.get("pr85_candidate_descriptor_ref") not in upstream.get("pr85_candidate_descriptor_ids", []):
        reasons.append("CANDIDATE_GENERATION_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR")
    if seed.get("optimizer_arbitration_fixture_ref") not in upstream.get("pr86_arbitration_fixture_ids", []):
        reasons.append("CANDIDATE_GENERATION_BLOCKED_MISSING_REQUIRED_FIELD")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if seed.get(field) is True:
            reasons.append(FIELD_REASON_CODES[field])
    if seed.get("owner_override_external_fact_fabrication_created") is True:
        reasons.append("CANDIDATE_GENERATION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN")
    return _sort_reason_codes(dict.fromkeys(reasons))


def _seed_to_candidate(
    seed: dict[str, Any],
    *,
    index: int,
    blocked_reasons: list[str],
    registry: dict[str, Any],
) -> dict[str, Any]:
    seed_id = str(seed.get("seed_descriptor_id") or "")
    role_map = seed.get("selected_stack_role_map")
    if not isinstance(role_map, dict):
        role_map = {}
    candidate_status = (
        "BLOCKED_CANDIDATE_STACK" if blocked_reasons else "ACTIVE_CANDIDATE_STACK"
    )
    generation_reason_codes = _sort_reason_codes(
        [
            *[str(code) for code in seed.get("generation_reason_codes", [])],
            *blocked_reasons,
        ]
    )
    deterministic_generation_key = "|".join(
        [
            "PR87",
            seed_id,
            str(seed.get("platform_scope") or ""),
            str(seed.get("market_type") or ""),
            _role_tuple(role_map),
        ]
    )
    return {
        "candidate_stack_id": _candidate_stack_id(seed_id),
        "candidate_index": index,
        "seed_descriptor_id": seed_id,
        "deterministic_generation_key": deterministic_generation_key,
        "candidate_authority_class": "STATIC_CANDIDATE_STACK_DESCRIPTOR_NOT_SELECTION_NOT_EXECUTION",
        "platform_scope": seed.get("platform_scope"),
        "venue_scope": seed.get("venue_scope"),
        "market_type": seed.get("market_type"),
        "strategy_class": seed.get("strategy_class"),
        "edge_type": seed.get("edge_type"),
        "latency_sensitivity_class": seed.get("latency_sensitivity_class"),
        "capital_intensity_class": seed.get("capital_intensity_class"),
        "source_dependency_state": seed.get("source_dependency_state"),
        "signal_family_ids": list(seed.get("signal_family_ids", [])),
        "scoring_family_ids": list(seed.get("scoring_family_ids", [])),
        "normalization_family_ids": list(seed.get("normalization_family_ids", [])),
        "risk_family_ids": list(seed.get("risk_family_ids", [])),
        "execution_family_ids": list(seed.get("execution_family_ids", [])),
        "capital_family_ids": list(seed.get("capital_family_ids", [])),
        "latency_family_ids": list(seed.get("latency_family_ids", [])),
        "error_guard_family_ids": list(seed.get("error_guard_family_ids", [])),
        "quantum_advisory_family_ids": list(seed.get("quantum_advisory_family_ids", [])),
        "selected_stack_role_map": copy.deepcopy(role_map),
        "quantum_applicability_summary": {
            "quantum_applicability_labels": list(seed.get("quantum_applicability_labels", [])),
            "quantum_candidate_type": seed.get("quantum_candidate_type"),
            "metadata_source": registry.get("quantum_applicability_source"),
            "backend_execution_created": False,
            "simulator_execution_created": False,
            "quantum_advantage_claim_created": False,
        },
        "owner_quantum_priority_summary": {
            "owner_quantum_priority_mode": seed.get("owner_quantum_priority_mode"),
            "owner_override_basis": seed.get("owner_override_basis"),
            "owner_override_internal_only_flag": seed.get("owner_override_internal_only_flag"),
            "owner_override_external_fact_fabrication_created": False,
            "metadata_source": registry.get("owner_quantum_priority_source"),
        },
        "classical_comparator_required_flag": seed.get("classical_comparator_required_flag"),
        "classical_comparator_ref": seed.get("classical_comparator_ref"),
        "quantum_candidate_type": seed.get("quantum_candidate_type"),
        "scoring_policy_refs": list(seed.get("scoring_policy_refs", [])),
        "ranking_contract_ref": seed.get("ranking_contract_ref"),
        "optimizer_arbitration_policy_ref": seed.get("optimizer_arbitration_policy_ref"),
        "optimizer_arbitration_fixture_ref": seed.get("optimizer_arbitration_fixture_ref"),
        "pr85_candidate_descriptor_ref": seed.get("pr85_candidate_descriptor_ref"),
        "role_completion_state": seed.get("role_completion_state"),
        "compatibility_state": seed.get("compatibility_state"),
        "blocker_state": "NO_BLOCKERS" if not blocked_reasons else seed.get("blocker_state"),
        "blocked_row_ids_and_reasons": copy.deepcopy(seed.get("blocked_row_ids_and_reasons", [])),
        "generation_reason_codes": generation_reason_codes,
        "blocked_reason_codes": blocked_reasons,
        "candidate_status": candidate_status,
        "replay_paper_competition_required_flag": candidate_status == "ACTIVE_CANDIDATE_STACK",
        "owner_review_required_flag": True,
        "no_final_selection_flag": True,
        "no_live_order_authority_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_backend_execution_flag": True,
        "final_selection_created": False,
        "selected_stack_created": False,
        "live_authority_created": False,
        "order_authority_created": False,
        "runtime_cash_receipt_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "classical_optimizer_execution_created": False,
        "quantum_optimizer_execution_created": False,
        "optimizer_execution_created": False,
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "profit_evidence_created": False,
        "quantum_advantage_claim_created": False,
    }


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    status_rank = 0 if candidate.get("candidate_status") == "ACTIVE_CANDIDATE_STACK" else 1
    role_rank = 0 if candidate.get("role_completion_state") == "ROLE_COMPLETE" else 1
    compatibility_rank = 0 if candidate.get("compatibility_state") == "COMPATIBLE_ROLE_TUPLE" else 1
    owner_summary = candidate.get("owner_quantum_priority_summary")
    owner_mode = ""
    owner_order = 999
    if isinstance(owner_summary, dict):
        owner_mode = str(owner_summary.get("owner_quantum_priority_mode") or "")
        if owner_summary.get("owner_override_basis") == "OWNER_GLOBAL_OVERRIDE":
            owner_order = 1
    quantum_type = str(candidate.get("quantum_candidate_type") or "")
    return (
        status_rank,
        role_rank,
        compatibility_rank,
        owner_order,
        OWNER_MODE_ORDER.get(owner_mode, 999),
        QUANTUM_TYPE_ORDER.get(quantum_type, 999),
        str(candidate.get("latency_sensitivity_class") or ""),
        "|".join(candidate.get("risk_family_ids", [])),
        _candidate_family_tuple(candidate),
        str(candidate.get("candidate_stack_id") or ""),
    )


def build_candidate_generation_packet(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    upstream: dict[str, Any],
    *,
    seed_filter: set[str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    seeds = _list_of_mappings(fixture.get("candidate_seed_descriptors"))
    if seed_filter is not None:
        seeds = [seed for seed in seeds if seed.get("seed_descriptor_id") in seed_filter]
    seed_ids = {str(seed.get("seed_descriptor_id") or "") for seed in seeds}
    if len(seed_ids) != len(seeds):
        failures.append("CANDIDATE_GENERATION_BLOCKED_DUPLICATE_CANDIDATE_STACK: duplicate seed descriptor IDs")

    raw_candidates: list[dict[str, Any]] = []
    for seed in seeds:
        seed_failures: list[str] = []
        seed_id = str(seed.get("seed_descriptor_id") or "")
        seed_codes = _reason_code_list(
            seed.get("generation_reason_codes"),
            f"{seed_id}.generation_reason_codes",
            seed_failures,
        )
        failures.extend(seed_failures)
        blocked_reasons = _blocked_reasons_for_seed(seed, seed_ids=seed_ids, upstream=upstream)
        expected_status = seed.get("expected_candidate_status")
        actual_status = "BLOCKED_CANDIDATE_STACK" if blocked_reasons else "ACTIVE_CANDIDATE_STACK"
        if expected_status != actual_status:
            failures.append(f"{seed_id}.expected_candidate_status must be {actual_status}")
        if actual_status == "ACTIVE_CANDIDATE_STACK" and any(code in BLOCK_REASON_CODES for code in seed_codes):
            failures.append(f"{seed_id} active candidate must not carry blocked reason codes")
        raw_candidates.append(
            _seed_to_candidate(
                seed,
                index=1,
                blocked_reasons=blocked_reasons,
                registry=registry,
            )
        )

    ordered_candidates = sorted(raw_candidates, key=_candidate_sort_key)
    for index, candidate in enumerate(ordered_candidates, start=1):
        candidate["candidate_index"] = index

    active_candidates = [
        candidate
        for candidate in ordered_candidates
        if candidate.get("candidate_status") == "ACTIVE_CANDIDATE_STACK"
    ]
    blocked_candidates = [
        candidate
        for candidate in ordered_candidates
        if candidate.get("candidate_status") == "BLOCKED_CANDIDATE_STACK"
    ]
    min_count = registry.get("generation_policy", {}).get(
        "minimum_valid_candidate_stack_count", 2
    )
    packet_status = (
        "STATIC_CANDIDATE_GENERATION_PACKET_READY"
        if len(active_candidates) >= min_count
        else "BLOCKED_INSUFFICIENT_CANDIDATE_STACKS"
    )
    packet_reason_codes = _sort_reason_codes(
        [
            "CANDIDATE_GENERATION_ALLOWED_STATIC_FIXTURE_ONLY",
            "CANDIDATE_GENERATION_ALLOWED_ROUTED_SELECTION_UNIVERSE_METADATA",
            "CANDIDATE_GENERATION_ALLOWED_SELECTION_UNIVERSE_METADATA",
            "CANDIDATE_GENERATION_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
            "CANDIDATE_GENERATION_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
            "CANDIDATE_GENERATION_ALLOWED_PR84_SCORING_POLICY",
            "CANDIDATE_GENERATION_ALLOWED_PR85_RANKING_CONTRACT",
            "CANDIDATE_GENERATION_ALLOWED_PR86_OPTIMIZER_ARBITRATION_METADATA",
            "CANDIDATE_GENERATION_ALLOWED_MULTIPLE_STATIC_CANDIDATES",
            "CANDIDATE_GENERATION_ALLOWED_PR88_PR90_FORWARDABLE_NOT_SELECTED",
            *(
                ["CANDIDATE_GENERATION_BLOCKED_INSUFFICIENT_CANDIDATE_STACKS"]
                if packet_status == "BLOCKED_INSUFFICIENT_CANDIDATE_STACKS"
                else []
            ),
        ]
    )
    packet = {
        "candidate_generation_packet_id": fixture.get("candidate_generation_packet_id"),
        "schema_version": POLICY_VERSION,
        "roadmap_pr_label": ROADMAP_PR_LABEL,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "github_pr_number_policy": GITHUB_PR_NUMBER_POLICY,
        "generation_scope": GENERATION_SCOPE,
        "generation_authority_class": GENERATION_AUTHORITY_CLASS,
        "packet_status": packet_status,
        "routed_selection_universe_ref": fixture.get("routed_selection_universe_ref"),
        "selection_universe_fingerprint_or_static_ref": fixture.get("selection_universe_fingerprint_or_static_ref"),
        "upstream_quantum_applicability_ref": registry.get("quantum_applicability_source", {}).get("artifact_id"),
        "upstream_owner_quantum_priority_ref": registry.get("owner_quantum_priority_source", {}).get("artifact_id"),
        "upstream_scoring_policy_ref": registry.get("scoring_policy_source", {}).get("artifact_id"),
        "upstream_scoring_ranking_gate_ref": registry.get("scoring_ranking_gate_source", {}).get("artifact_id"),
        "upstream_optimizer_arbitration_ref": registry.get("optimizer_arbitration_source", {}).get("artifact_id"),
        "source_dependency_state": fixture.get("source_dependency_state"),
        "candidate_stack_generation_count": len(active_candidates),
        "total_candidate_stack_descriptor_count": len(ordered_candidates),
        "blocked_candidate_stack_count": len(blocked_candidates),
        "active_candidate_stack_ids": [candidate["candidate_stack_id"] for candidate in active_candidates],
        "blocked_candidate_stack_ids": [candidate["candidate_stack_id"] for candidate in blocked_candidates],
        "generation_reason_codes": packet_reason_codes,
        "replay_paper_competition_required_flag": fixture.get("replay_paper_competition_required_flag"),
        "owner_review_required_flag": fixture.get("owner_review_required_flag"),
        "not_final_selection_flag": True,
        "no_order_authority_flag": True,
        "no_runtime_execution_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_profit_evidence_flag": True,
        "candidate_stacks": ordered_candidates,
    }
    return packet, failures


def validate_candidate_generation_packet(packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if "selected_stack_id" in packet:
        failures.append("CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN: packet must not emit selected_stack_id")
    candidates = _list_of_mappings(packet.get("candidate_stacks"))
    ids = [str(candidate.get("candidate_stack_id") or "") for candidate in candidates]
    if len(ids) != len(set(ids)):
        failures.append("CANDIDATE_GENERATION_BLOCKED_DUPLICATE_CANDIDATE_STACK: duplicate candidate_stack_id")
    active = [candidate for candidate in candidates if candidate.get("candidate_status") == "ACTIVE_CANDIDATE_STACK"]
    blocked = [candidate for candidate in candidates if candidate.get("candidate_status") == "BLOCKED_CANDIDATE_STACK"]
    if packet.get("candidate_stack_generation_count") != len(active):
        failures.append("candidate_stack_generation_count must equal active candidate count")
    if len(active) < 2 and packet.get("packet_status") != "BLOCKED_INSUFFICIENT_CANDIDATE_STACKS":
        failures.append("CANDIDATE_GENERATION_BLOCKED_INSUFFICIENT_CANDIDATE_STACKS: insufficient active candidates must fail closed")
    if len(active) >= 2 and packet.get("packet_status") != "STATIC_CANDIDATE_GENERATION_PACKET_READY":
        failures.append("packet_status must be ready when multiple active candidates are generated")
    if [candidate["candidate_stack_id"] for candidate in active] != list(EXPECTED_ACTIVE_CANDIDATE_IDS) and len(active) == len(EXPECTED_ACTIVE_CANDIDATE_IDS):
        failures.append("active candidate stack ordering mismatch")
    if [candidate["candidate_stack_id"] for candidate in blocked] != list(EXPECTED_BLOCKED_CANDIDATE_IDS) and len(blocked) == len(EXPECTED_BLOCKED_CANDIDATE_IDS):
        failures.append("blocked candidate stack ordering mismatch")
    for index, candidate in enumerate(candidates, start=1):
        if candidate.get("candidate_index") != index:
            failures.append(f"{candidate.get('candidate_stack_id')}.candidate_index must be {index}")
        if candidate.get("candidate_status") == "ACTIVE_CANDIDATE_STACK":
            if candidate.get("blocked_reason_codes"):
                failures.append(f"{candidate.get('candidate_stack_id')} active candidate must not have blocked reason codes")
            if candidate.get("blocked_row_ids_and_reasons"):
                failures.append(f"{candidate.get('candidate_stack_id')} active candidate must not include blocked rows")
        else:
            if not candidate.get("blocked_reason_codes"):
                failures.append(f"{candidate.get('candidate_stack_id')} blocked candidate must include blocked reason codes")
        if candidate.get("quantum_candidate_type") != "CLASSICAL_ONLY":
            if candidate.get("classical_comparator_required_flag") is not True:
                failures.append(f"{candidate.get('candidate_stack_id')} quantum candidate must require comparator")
            if not candidate.get("classical_comparator_ref"):
                failures.append(f"{candidate.get('candidate_stack_id')} quantum candidate must preserve comparator ref")
        for field in (
            "no_final_selection_flag",
            "no_live_order_authority_flag",
            "no_runtime_cash_receipt_flag",
            "no_backend_execution_flag",
        ):
            if candidate.get(field) is not True:
                failures.append(f"{candidate.get('candidate_stack_id')}.{field} must be true")
        for field in (
            "final_selection_created",
            "selected_stack_created",
            "live_authority_created",
            "order_authority_created",
            "runtime_cash_receipt_created",
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
            if candidate.get(field) is not False:
                failures.append(f"{FIELD_REASON_CODES.get(field, field)}: {candidate.get('candidate_stack_id')}.{field} must be false")
    return failures


def validate_fixture(
    fixture: dict[str, Any],
    registry: dict[str, Any],
    upstream: dict[str, Any],
) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    failures: list[str] = []
    for field, expected in (
        ("mode", "SOURCE_REQUIRED"),
        ("execution", "DISABLED"),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("gate_scope", GATE_SCOPE),
        ("generation_scope", GENERATION_SCOPE),
        ("generation_authority_class", GENERATION_AUTHORITY_CLASS),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "candidate_generation_contract_only_flag",
        "replay_paper_competition_required_flag",
        "owner_review_required_flag",
        "not_final_selection_flag",
        "no_order_authority_flag",
        "no_runtime_execution_flag",
        "no_quantum_backend_execution_flag",
        "no_profit_evidence_flag",
    ):
        if fixture.get(field) is not True:
            failures.append(f"fixture.{field} must be true")
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if fixture.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: fixture.{field} must be false")
    if fixture.get("selected_stack_id_emitted") is not False:
        failures.append("CANDIDATE_GENERATION_BLOCKED_SELECTED_STACK_FORBIDDEN: fixture.selected_stack_id_emitted must be false")

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

    packet, packet_failures = build_candidate_generation_packet(registry, fixture, upstream)
    failures.extend(packet_failures)
    failures.extend(validate_candidate_generation_packet(packet))

    insufficient = fixture.get("insufficient_candidate_count_case")
    if not isinstance(insufficient, dict):
        failures.append("fixture.insufficient_candidate_count_case must be an object")
        insufficient_packet: dict[str, Any] = {}
    else:
        filter_ids = set(str(item) for item in insufficient.get("candidate_seed_descriptor_ids", []))
        insufficient_packet, insufficient_failures = build_candidate_generation_packet(
            registry,
            fixture,
            upstream,
            seed_filter=filter_ids,
        )
        failures.extend(insufficient_failures)
        if insufficient_packet.get("packet_status") != "BLOCKED_INSUFFICIENT_CANDIDATE_STACKS":
            failures.append("CANDIDATE_GENERATION_BLOCKED_INSUFFICIENT_CANDIDATE_STACKS: insufficient case must fail closed")
        if insufficient.get("expected_reason_code") not in insufficient_packet.get("generation_reason_codes", []):
            failures.append("insufficient case expected reason code missing")

    handoff = fixture.get("pr88_pr90_handoff_boundary_fixture")
    if not isinstance(handoff, dict):
        failures.append("fixture.pr88_pr90_handoff_boundary_fixture must be an object")
    else:
        if handoff.get("packet_is_forwardable_to_pr88_static_selection_gate") is not True:
            failures.append("PR88 handoff boundary must be forwardable")
        if handoff.get("packet_is_forwardable_to_pr90_replay_paper_competition_gate") is not True:
            failures.append("PR90 handoff boundary must be forwardable")
        for field in (
            "final_selection_created",
            "replay_execution_created",
            "paper_execution_created",
            "order_authority_created",
        ):
            if handoff.get(field) is not False:
                failures.append(f"handoff boundary {field} must be false")
        if handoff.get("selected_stack_id") is not None:
            failures.append("handoff boundary selected_stack_id must be null")
    return failures, packet, insufficient_packet


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists():
        failures.append(
            "CANDIDATE_GENERATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
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
            "CANDIDATE_GENERATION_BLOCKED_MASTER_PLAN_EDIT_FORBIDDEN: "
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
    insufficient_packet: dict[str, Any],
    upstream: dict[str, Any],
    metadata: dict[str, Any],
    repo_root: pathlib.Path,
) -> dict[str, Any]:
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
        "candidate_generation_gate_id": registry.get("candidate_generation_gate_id"),
        "gate_scope": registry.get("gate_scope"),
        "generation_scope": GENERATION_SCOPE,
        "generation_authority_class": GENERATION_AUTHORITY_CLASS,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "candidate_generation_contract_only_flag": True,
        "routed_selection_universe_source": copy.deepcopy(registry.get("routed_selection_universe_source")),
        "selection_universe_source": copy.deepcopy(registry.get("selection_universe_source")),
        "quantum_applicability_source": copy.deepcopy(registry.get("quantum_applicability_source")),
        "owner_quantum_priority_source": copy.deepcopy(registry.get("owner_quantum_priority_source")),
        "scoring_policy_source": copy.deepcopy(registry.get("scoring_policy_source")),
        "scoring_ranking_gate_source": copy.deepcopy(registry.get("scoring_ranking_gate_source")),
        "optimizer_arbitration_source": copy.deepcopy(registry.get("optimizer_arbitration_source")),
        "required_stack_roles": list(ROLE_ORDER),
        "pr81_eligible_universe_ids": list(upstream.get("pr81_eligible_universe_ids", [])),
        "pr82_quantum_applicability_labels": list(upstream.get("pr82_labels", [])),
        "pr83_supported_quantum_priority_modes": list(upstream.get("pr83_modes", [])),
        "pr83_default_quantum_priority_mode": upstream.get("pr83_default_mode"),
        "pr84_formula_ids": list(upstream.get("pr84_formula_ids", [])),
        "pr85_candidate_descriptor_ids": list(upstream.get("pr85_candidate_descriptor_ids", [])),
        "pr85_ranked_candidate_descriptor_ids": list(upstream.get("pr85_ranked_candidate_descriptor_ids", [])),
        "pr85_blocked_candidate_descriptor_ids": list(upstream.get("pr85_blocked_candidate_descriptor_ids", [])),
        "pr86_arbitration_fixture_ids": list(upstream.get("pr86_arbitration_fixture_ids", [])),
        "pr86_ordered_fixture_ids": list(upstream.get("pr86_ordered_fixture_ids", [])),
        "generation_inputs": list(GENERATION_INPUT_ORDER),
        "generation_outputs": list(GENERATION_OUTPUT_ORDER),
        "generation_policy": copy.deepcopy(registry.get("generation_policy")),
        "blocked_candidate_policy": copy.deepcopy(registry.get("blocked_candidate_policy")),
        "deterministic_sort_key_order": list(DETERMINISTIC_SORT_KEY_ORDER),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "candidate_generation_packet": copy.deepcopy(packet),
        "candidate_generation_packet_id": packet.get("candidate_generation_packet_id"),
        "candidate_generation_packet_status": packet.get("packet_status"),
        "candidate_stack_generation_count": packet.get("candidate_stack_generation_count"),
        "active_candidate_stack_ids": list(packet.get("active_candidate_stack_ids", [])),
        "blocked_candidate_stack_ids": list(packet.get("blocked_candidate_stack_ids", [])),
        "insufficient_candidate_count_case_packet_status": insufficient_packet.get("packet_status"),
        "insufficient_candidate_count_case_reason_codes": list(insufficient_packet.get("generation_reason_codes", [])),
        "pr88_pr90_handoff_boundary": copy.deepcopy(fixture.get("pr88_pr90_handoff_boundary_fixture")),
        "master_plan_principles_consumed": copy.deepcopy(registry.get("master_plan_principles_consumed")),
        "deterministic_candidate_generation": True,
        "deterministic_candidate_ids": True,
        "deterministic_candidate_ordering": True,
        "deterministic_blocked_candidate_ordering": True,
        "deterministic_upstream_dependency_ordering": True,
        "deterministic_future_consumer_ordering": True,
        "deterministic_reason_code_ordering": True,
        "multiple_candidate_stacks_generated": packet.get("candidate_stack_generation_count", 0) >= 2,
        "role_completeness_enforced": True,
        "compatibility_state_enforced": True,
        "blocked_rows_enter_active_candidate_status": False,
        "owner_quantum_priority_static_policy_metadata_only": True,
        "owner_override_records_basis_without_external_fact_fabrication": True,
        "quantum_metadata_static_advisory_policy_gated": True,
        "classical_comparator_or_fallback_preserved_for_quantum_candidates": True,
        "replay_paper_competition_required_flag": True,
        "owner_review_required_flag": True,
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
        "final_selection": False,
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

    metadata_failures, metadata = validate_pr87_roadmap_metadata(repo_root)
    info_lines = tuple(metadata.get("ci_info_lines", ()))
    failures.extend(metadata_failures)
    upstream_failures, upstream = validate_upstream_reports(repo_root)
    failures.extend(upstream_failures)
    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_gate_payload(registry, repo_root=repo_root))
    fixture_validation_failures, packet, insufficient_packet = validate_fixture(
        fixture,
        registry,
        upstream,
    )
    failures.extend(fixture_validation_failures)
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

    report = build_report(
        registry,
        fixture,
        packet,
        insufficient_packet,
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
