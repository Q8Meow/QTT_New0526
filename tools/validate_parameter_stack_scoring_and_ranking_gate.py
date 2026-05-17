#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from decimal import Decimal
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import validate_parameter_algorithm_scoring_policy_registry as pr84_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "selection"
    / "parameter_stack_scoring_and_ranking_gate.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "selection"
    / "ParameterStackScoringAndRankingGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "selection"
    / "synthetic_parameter_stack_scoring_and_ranking_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "ParameterStackScoringAndRankingGate.report.json"
)

PR84_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "scoring"
    / "ParameterAlgorithmScoringPolicyRegistry.yaml"
)
PR84_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "ParameterAlgorithmScoringPolicyRegistry.report.json"
)
CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
PR76_SHORT_TEST = pathlib.Path(
    "tests/source_evidence/test_runtime_resolver_allowlist_live_blocks.py"
)
PR76_OLD_LONG_TEST = pathlib.Path(
    "tests/source_evidence/"
    "test_stage1_runtime_resolver_snapshot_consumer_allowlist_blocks_direct_live_dual_review_dashboard.py"
)

GATE_REGISTRY_ID = "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE"
GATE_ID = "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_V1"
REPORT_ID = "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_REPORT"
POLICY_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-PARAMETER-STACK-SCORING-AND-RANKING-GATE"
GATE_SCOPE = "STATIC_PARAMETER_STACK_SCORING_AND_RANKING_CONTRACT_ONLY"
SUCCESS_MARKER = "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK"
FAILURE_MARKER = "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_FAILED"

COMPONENT_INPUT_ORDER = tuple(
    name
    for name in pr84_gate.COMPONENT_ORDER
    if name not in ("base_score", "quantum_boost", "final_selection_score")
)
SCORE_BREAKDOWN_ORDER = (
    *COMPONENT_INPUT_ORDER,
    "readiness_score",
    "total_penalty",
    "base_score",
    "quantum_boost",
    "final_selection_score",
)
FORMULA_ORDER = pr84_gate.FORMULA_ORDER
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
    "PR65_QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY",
    "PR66_QTT_AGENT_ALGORITHM_BINDING_REGISTRY",
    "PR67_QTT_AGENT_ALGORITHM_CONSUMER_GATE",
    "PR68_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE",
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
)
DEPENDENCY_MARKERS = {
    **pr84_gate.DEPENDENCY_MARKERS,
    "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY": pr84_gate.SUCCESS_MARKER,
}
FUTURE_CONSUMER_ORDER = (
    "PR86_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE",
    "PR87_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
    "PR88_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
    "PR89_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
    "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
)
RANKING_INPUT_ORDER = (
    "synthetic_candidate_stack_descriptors",
    "scoring_policy_registry",
    "quantum_applicability_registry",
    "owner_quantum_priority_policy_registry",
    "scoring_component_inputs",
    "blocked_candidate_policy",
    "tie_break_policy",
)
RANKING_OUTPUT_ORDER = (
    "static_scored_candidate_descriptors",
    "static_ranked_candidate_descriptors",
    "blocked_candidate_descriptors",
    "score_breakdown",
    "ranking_reason_codes",
    "no_selection_boundary",
)
TIE_BREAK_ORDER = (
    "valid_for_ranking_flag_true_before_false",
    "higher_final_selection_score",
    "higher_base_score",
    "higher_quantum_boost_only_if_owner_quantum_priority_mode_permits_quantum_tie_break",
    "lower_total_penalty",
    "higher_owner_priority_boost_if_owner_policy_permits",
    "lower_complexity_penalty",
    "lexicographic_candidate_stack_descriptor_id",
)
REASON_CODE_ORDER = (
    "STACK_SCORING_RANKING_ALLOWED_STATIC_FIXTURE_ONLY",
    "STACK_SCORING_RANKING_ALLOWED_PR84_FORMULA_POLICY",
    "STACK_SCORING_RANKING_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
    "STACK_SCORING_RANKING_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
    "STACK_SCORING_RANKING_ALLOWED_CLASSICAL_COMPARATOR",
    "STACK_SCORING_RANKING_ALLOWED_QUANTUM_PRIORITY_WHEN_OWNER_ENABLED",
    "STACK_SCORING_RANKING_ALLOWED_HYBRID_TIEBREAK_WITH_CLASSICAL_COMPARATOR",
    "STACK_SCORING_RANKING_ALLOWED_OWNER_INTERNAL_PRIORITY",
    "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR",
    "STACK_SCORING_RANKING_BLOCKED_DUPLICATE_CANDIDATE_DESCRIPTOR",
    "STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD",
    "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_SCORING_COMPONENT",
    "STACK_SCORING_RANKING_BLOCKED_MISSING_SCORE_BREAKDOWN",
    "STACK_SCORING_RANKING_BLOCKED_INVALID_SCORE_TYPE",
    "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL",
    "STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED",
    "STACK_SCORING_RANKING_BLOCKED_CLASSICAL_COMPARATOR_MISSING",
    "STACK_SCORING_RANKING_BLOCKED_RANDOM_RANKING_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS",
    "STACK_SCORING_RANKING_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "STACK_SCORING_RANKING_BLOCKED_FINAL_SELECTION_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_CANDIDATE_IDS = (
    "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
    "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
    "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
    "BLOCKED_INVALID_STACK_FIXTURE",
    "TIE_BREAK_STABILITY_FIXTURE_A",
    "TIE_BREAK_STABILITY_FIXTURE_B",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_REGISTRY_VALIDATES",
    "PASS_ALL_REQUIRED_CANDIDATES_PRESENT",
    "PASS_CANDIDATES_SYNTHETIC_STATIC_ONLY",
    "PASS_PR82_METADATA_CONSUMED",
    "PASS_PR83_POLICY_CONSUMED",
    "PASS_PR84_POLICY_CONSUMED",
    "PASS_DETERMINISTIC_SCORE_BREAKDOWN",
    "PASS_DETERMINISTIC_RANKING",
    "PASS_TIES_RESOLVED_DETERMINISTICALLY",
    "PASS_CLASSICAL_ONLY_COMPARATOR_VALID",
    "PASS_QUANTUM_RANKS_HIGHER_WHEN_OWNER_PERMITS",
    "PASS_HYBRID_TIEBREAK_REQUIRES_CLASSICAL_COMPARATOR",
    "PASS_OWNER_OVERRIDE_INTERNAL_ONLY",
    "PASS_BLOCKED_CANDIDATE_TRACEABLE",
    "PASS_NO_FINAL_SELECTED_STACK",
    "PASS_PR86_PR87_PR88_FUTURE_SCOPE_NOT_IMPLEMENTED",
    "PASS_NO_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_BACKEND_ARTIFACT",
    "BLOCK_MISSING_SEMANTIC_TASK_ID",
    "BLOCK_WRONG_SEMANTIC_TASK_ID",
    "BLOCK_MISSING_PR82_DEPENDENCY",
    "BLOCK_MISSING_PR83_DEPENDENCY",
    "BLOCK_MISSING_PR84_DEPENDENCY",
    "BLOCK_UNKNOWN_CANDIDATE_DESCRIPTOR",
    "BLOCK_DUPLICATE_CANDIDATE_DESCRIPTOR",
    "BLOCK_CANDIDATE_NOT_SYNTHETIC_STATIC",
    "BLOCK_REAL_GENERATED_CANDIDATE_CLAIM",
    "BLOCK_SELECTED_STACK_CLAIM",
    "BLOCK_MISSING_SCORE_BREAKDOWN",
    "BLOCK_MISSING_BASE_SCORE",
    "BLOCK_MISSING_QUANTUM_BOOST",
    "BLOCK_MISSING_FINAL_SELECTION_SCORE",
    "BLOCK_UNKNOWN_SCORING_COMPONENT",
    "BLOCK_UNKNOWN_PR82_APPLICABILITY_LABEL",
    "BLOCK_UNKNOWN_PR83_PRIORITY_MODE",
    "BLOCK_PR84_FORMULA_MISMATCH",
    "BLOCK_RANDOM_RANKING_POLICY",
    "BLOCK_AMBIGUOUS_TIE_BREAK",
    "BLOCK_QUANTUM_PRIORITY_WITH_OWNER_POLICY_NOT_PERMITTED",
    "BLOCK_HYBRID_TIEBREAK_WITHOUT_CLASSICAL_COMPARATOR",
    "BLOCK_FINAL_SELECTION_CLAIM",
    "BLOCK_OPTIMIZER_EXECUTION_CLAIM",
    "BLOCK_OPTIMIZER_ARBITRATION_CLAIM",
    "BLOCK_QUANTUM_BACKEND_EXECUTION_CLAIM",
    "BLOCK_QUANTUM_SIMULATOR_EXECUTION_CLAIM",
    "BLOCK_REPLAY_PAPER_RESULT_CLAIM",
    "BLOCK_RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM",
    "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_CLAIM",
    "BLOCK_CONNECTOR_BINDING_CLAIM",
    "BLOCK_RUNTIME_CASH_RECEIPT_CLAIM",
    "BLOCK_PRIVATE_STATE_FETCH_CLAIM",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "BLOCK_LATENCY_SUPERIORITY_CLAIM",
    "BLOCK_EXECUTION_SUPERIORITY_CLAIM",
    "BLOCK_ATOMICROWS_BUNDLE_JSONL",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
    "BLOCK_OLD_LONG_RUNTIME_RESOLVER_FILENAME",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "real_candidate_stack_generation_created",
    "generated_candidate_stack_claim_created",
    "final_selection_created",
    "selected_stack_created",
    "selected_trade_created",
    "optimizer_execution_created",
    "optimizer_arbitration_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "replay_execution_created",
    "paper_execution_created",
    "runtime_authority_created",
    "live_authority_created",
    "order_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_cash_receipt_created",
    "private_state_fetch_created",
    "expected_profit_claim_created",
    "profit_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "random_ranking_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
)
CANDIDATE_FALSE_FIELDS = (
    "real_generated_candidate_claim_created",
    "selected_stack_claim_created",
    "profit_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "runtime_authority_created",
    "live_authority_created",
    "order_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "runtime_cash_receipt_created",
    "private_state_fetch_created",
    "optimizer_execution_created",
    "optimizer_arbitration_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "replay_execution_created",
    "paper_execution_created",
    "final_selection_created",
    "selected_stack_created",
)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
    "backend_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solve_execution_created",
    "ising_solve_execution_created",
    "source_retrieval_execution_created",
    "source_acceptance_execution_created",
    "runtime_resolver_execution_created",
    "private_state_fetch_execution_created",
    "balance_fetch_created",
    "open_order_fetch_created",
    "order_submission_created",
    "order_cancellation_created",
    "order_reduction_created",
    "fill_receipt_created",
    "walk_forward_execution_created",
    "dashboard_runtime_service_created",
    "telegram_runtime_service_created",
    "scoring_is_real_trading_evidence",
    "expected_net_profit_score_is_profit_evidence",
    "latency_fit_score_is_latency_superiority_evidence",
    "optimizer_score_is_optimizer_execution",
    "runtime_readiness_score_is_runtime_receipt",
    "replay_paper_score_is_replay_paper_result",
    "source_currentness_penalty_is_source_authority",
    "execution_cost_penalty_is_venue_fact",
    "owner_override_can_fabricate_external_facts",
    "quantum_boost_is_quantum_advantage_evidence",
    "highest_ranked_candidate_is_final_selected_stack",
    "ranking_fixture_is_trading_signal",
    "final_selection_score_is_final_selection",
    "real_candidate_stack_generation_created_by_pr85",
    "future_pr86_optimizer_arbitration_implemented",
    "future_pr87_candidate_generation_implemented",
    "future_pr88_trade_context_selection_implemented",
)

FIELD_REASON_CODES = {
    "real_candidate_stack_generation_created": "STACK_SCORING_RANKING_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "generated_candidate_stack_claim_created": "STACK_SCORING_RANKING_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "final_selection_created": "STACK_SCORING_RANKING_BLOCKED_FINAL_SELECTION_FORBIDDEN",
    "selected_stack_created": "STACK_SCORING_RANKING_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "selected_trade_created": "STACK_SCORING_RANKING_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "optimizer_execution_created": "STACK_SCORING_RANKING_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_arbitration_created": "STACK_SCORING_RANKING_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
    "quantum_backend_execution_created": "STACK_SCORING_RANKING_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created": "STACK_SCORING_RANKING_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "replay_execution_created": "STACK_SCORING_RANKING_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "paper_execution_created": "STACK_SCORING_RANKING_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "runtime_authority_created": "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "live_authority_created": "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "order_authority_created": "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "source_retrieval_created": "STACK_SCORING_RANKING_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "source_acceptance_created": "STACK_SCORING_RANKING_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "connector_semantic_binding_created": "STACK_SCORING_RANKING_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created": "STACK_SCORING_RANKING_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "private_state_fetch_created": "STACK_SCORING_RANKING_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "expected_profit_claim_created": "STACK_SCORING_RANKING_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "profit_evidence_created": "STACK_SCORING_RANKING_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created": "STACK_SCORING_RANKING_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created": "STACK_SCORING_RANKING_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "execution_superiority_claim_created": "STACK_SCORING_RANKING_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "random_ranking_used": "STACK_SCORING_RANKING_BLOCKED_RANDOM_RANKING_FORBIDDEN",
    "atomicrows_bundle_jsonl_created": "STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
    "real_generated_candidate_claim_created": "STACK_SCORING_RANKING_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "selected_stack_claim_created": "STACK_SCORING_RANKING_BLOCKED_SELECTED_STACK_FORBIDDEN",
}
SCORE_QUANT = Decimal("0.000001")


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return pr84_gate.load_yaml(path)


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
        return None, [f"{label} invalid JSON: {exc}"]


def _load_yaml_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:
        return None, [f"{label} invalid YAML subset: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label}{failure}" for failure in validate_json_schema_subset(payload, schema)]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    order = {code: index for index, code in enumerate(REASON_CODE_ORDER)}
    return sorted((str(code) for code in codes), key=lambda code: order.get(code, 9999))


def _decimal(value: Any, label: str, failures: list[str]) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_INVALID_SCORE_TYPE: {label} must be deterministic numeric")
        return None
    return Decimal(str(value)).quantize(SCORE_QUANT)


def _json_number(value: Decimal) -> int | float:
    normalized = value.quantize(SCORE_QUANT).normalize()
    if normalized == normalized.to_integral_value():
        return int(normalized)
    return float(normalized)


def _formula_scores(inputs: dict[str, Any], failures: list[str], label: str) -> dict[str, Decimal] | None:
    values: dict[str, Decimal] = {}
    for name in COMPONENT_INPUT_ORDER:
        parsed = _decimal(inputs.get(name), f"{label}.scoring_component_inputs.{name}", failures)
        if parsed is None:
            return None
        values[name] = parsed

    total_penalty = (
        values["drawdown_penalty"]
        + values["complexity_penalty"]
        + values["source_currentness_penalty"]
        + values["execution_cost_penalty"]
    ).quantize(SCORE_QUANT)
    readiness_score = (
        values["runtime_readiness_score"] - values["source_currentness_penalty"]
    ).quantize(SCORE_QUANT)
    base_score = (
        Decimal("0.10") * values["agent_binding_score"]
        + Decimal("0.08") * values["lifecycle_status_score"]
        + Decimal("0.08") * values["owner_override_score"]
        + Decimal("0.08") * values["platform_applicability_score"]
        + Decimal("0.08") * values["market_type_applicability_score"]
        + Decimal("0.10") * values["strategy_fit_score"]
        + Decimal("0.08") * values["latency_fit_score"]
        + Decimal("0.08") * values["risk_fit_score"]
        + Decimal("0.08") * values["replay_paper_score"]
        + Decimal("0.08") * values["optimizer_score"]
        + Decimal("0.08") * readiness_score
        + Decimal("0.05") * values["expected_net_profit_score"]
        + Decimal("0.03") * values["owner_priority_boost"]
        - total_penalty
    ).quantize(SCORE_QUANT)
    quantum_boost = (
        values["quantum_applicability_score"]
        * values["quantum_priority_multiplier"]
        * values["owner_quantum_priority_boost"]
    ).quantize(SCORE_QUANT)
    final_selection_score = (base_score + quantum_boost).quantize(SCORE_QUANT)

    values["readiness_score"] = readiness_score
    values["total_penalty"] = total_penalty
    values["base_score"] = base_score
    values["quantum_boost"] = quantum_boost
    values["final_selection_score"] = final_selection_score
    return values


def _mode_policy_map(pr83_policy: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(pr83_policy, dict):
        return {}
    return {
        str(policy.get("mode")): policy
        for policy in _list_of_mappings(pr83_policy.get("mode_policies"))
    }


def _quantum_tie_allowed(mode: str, mode_policies: dict[str, dict[str, Any]]) -> bool:
    policy = mode_policies.get(mode, {})
    return policy.get("tie_breaker_enabled") is True and mode != "QUANTUM_NEUTRAL"


def validate_dependencies(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    dependencies = _list_of_mappings(payload.get("upstream_dependencies"))
    dependency_ids = [str(item.get("artifact_id") or "") for item in dependencies]
    if dependency_ids != list(DEPENDENCY_ORDER):
        for dependency_id in DEPENDENCY_ORDER:
            if dependency_id not in dependency_ids:
                failures.append(
                    "STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: "
                    f"missing upstream dependency {dependency_id}"
                )
        unknown = [dependency_id for dependency_id in dependency_ids if dependency_id not in DEPENDENCY_ORDER]
        if unknown:
            failures.append(f"unknown upstream dependencies {', '.join(unknown)}")
        failures.append("REGISTRY.upstream_dependencies must use canonical PR65-PR84 order")
    for dependency in dependencies:
        artifact_id = str(dependency.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker is not None and dependency.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id}.validation_marker must be {expected_marker}")
        for field in ("registry_path", "report_path", "validator_path"):
            raw = dependency.get(field)
            if not isinstance(raw, str) or not raw:
                failures.append(f"{artifact_id}.{field} must be a non-empty path")
                continue
            if not _resolve(repo_root, pathlib.Path(raw)).exists():
                failures.append(f"{artifact_id}.{field} path is missing: {raw}")
    return failures


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumers = _list_of_mappings(payload.get("future_consumers"))
    consumer_ids = [str(item.get("consumer_id") or "") for item in consumers]
    if consumer_ids != list(FUTURE_CONSUMER_ORDER):
        failures.append("REGISTRY.future_consumers must use canonical PR86-PR92 order")
    for consumer in consumers:
        consumer_id = str(consumer.get("consumer_id") or "")
        if consumer.get("pr85_creates_consumer_execution") is not False:
            failures.append(f"{consumer_id}.pr85_creates_consumer_execution must be false")
    return failures


def validate_ranking_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("ranking_inputs") != list(RANKING_INPUT_ORDER):
        failures.append("REGISTRY.ranking_inputs must use canonical deterministic order")
    if payload.get("ranking_outputs") != list(RANKING_OUTPUT_ORDER):
        failures.append("REGISTRY.ranking_outputs must use canonical deterministic order")
    policy = payload.get("ranking_policy")
    if not isinstance(policy, dict):
        return ["REGISTRY.ranking_policy must be an object"]
    if policy.get("tie_break_order") != list(TIE_BREAK_ORDER):
        failures.append("STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: tie_break_order must match canonical PR85 order")
    if policy.get("random_sort_allowed") is not False:
        failures.append("STACK_SCORING_RANKING_BLOCKED_RANDOM_RANKING_FORBIDDEN: random_sort_allowed must be false")
    if policy.get("stable_sort_required") is not True:
        failures.append("STACK_SCORING_RANKING_BLOCKED_RANDOM_RANKING_FORBIDDEN: stable_sort_required must be true")
    if policy.get("rank_assignment_policy") != "SEQUENTIAL_RANK":
        failures.append("REGISTRY.ranking_policy.rank_assignment_policy must be SEQUENTIAL_RANK")
    if policy.get("final_selection_created") is not False:
        failures.append("STACK_SCORING_RANKING_BLOCKED_FINAL_SELECTION_FORBIDDEN: ranking_policy.final_selection_created must be false")
    if policy.get("selected_stack_created") is not False:
        failures.append("STACK_SCORING_RANKING_BLOCKED_SELECTED_STACK_FORBIDDEN: ranking_policy.selected_stack_created must be false")
    return failures


def validate_reason_codes(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("REGISTRY.reason_codes must use canonical deterministic reason code order")
    blocked_policy = payload.get("blocked_candidate_policy")
    if not isinstance(blocked_policy, dict):
        failures.append("REGISTRY.blocked_candidate_policy must be an object")
        return failures
    if blocked_policy.get("blocked_candidates_remain_traceable") is not True:
        failures.append("REGISTRY.blocked_candidate_policy.blocked_candidates_remain_traceable must be true")
    if blocked_policy.get("blocked_candidates_ranked") is not False:
        failures.append("REGISTRY.blocked_candidate_policy.blocked_candidates_ranked must be false")
    if blocked_policy.get("blocked_candidates_retain_reason_codes") is not True:
        failures.append("REGISTRY.blocked_candidate_policy.blocked_candidates_retain_reason_codes must be true")
    if blocked_policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
        failures.append("REGISTRY.blocked_candidate_policy.blocked_reason_code_order must cover blocked reason codes in canonical order")
    return failures


def validate_no_authority_flags(payload: dict[str, Any], *, field_path: str = "REGISTRY.required_no_authority_flags") -> list[str]:
    failures: list[str] = []
    flags = payload.get("required_no_authority_flags")
    if not isinstance(flags, dict):
        return [f"{field_path} must be an object"]
    for field in NO_AUTHORITY_FALSE_FIELDS:
        if flags.get(field) is not False:
            code = FIELD_REASON_CODES[field]
            failures.append(f"{code}: {field_path}.{field} must be false")
    return failures


def validate_gate_payload(payload: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    expected = {
        "gate_registry_id": GATE_REGISTRY_ID,
        "parameter_stack_scoring_ranking_gate_id": GATE_ID,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "gate_scope": GATE_SCOPE,
        "policy_version": POLICY_VERSION,
    }
    for field, expected_value in expected.items():
        if payload.get(field) != expected_value:
            failures.append(f"REGISTRY.{field} must be {expected_value}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "scoring_ranking_contract_only_flag",
        "static_candidate_descriptor_fixture_only",
    ):
        if payload.get(field) is not True:
            failures.append(f"REGISTRY.{field} must be true")
    if payload.get("stage1_prediction_market_contexts") != ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]:
        failures.append("REGISTRY.stage1_prediction_market_contexts must preserve canonical Stage-1 prediction-market order")
    if payload.get("final_ready") is not False:
        failures.append("REGISTRY.final_ready must be false")
    failures.extend(validate_dependencies(payload, repo_root))
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_ranking_policy(payload))
    failures.extend(validate_reason_codes(payload))
    failures.extend(validate_no_authority_flags(payload))
    return failures


def validate_pr84_policy(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any] | None]:
    failures: list[str] = []
    registry, registry_failures = _load_yaml_checked(_resolve(repo_root, PR84_REGISTRY), "PR84_REGISTRY")
    report, report_failures = _load_json_checked(_resolve(repo_root, PR84_REPORT), "PR84_REPORT")
    failures.extend(registry_failures)
    failures.extend(report_failures)
    if registry is None or report is None:
        return failures, None
    if registry.get("semantic_task_id") != pr84_gate.SEMANTIC_TASK_ID:
        failures.append(f"PR84_REGISTRY.semantic_task_id must be {pr84_gate.SEMANTIC_TASK_ID}")
    if registry.get("policy_scope") != pr84_gate.POLICY_SCOPE:
        failures.append(f"PR84_REGISTRY.policy_scope must be {pr84_gate.POLICY_SCOPE}")
    if report.get("validation_marker") != pr84_gate.SUCCESS_MARKER:
        failures.append(f"PR84_REPORT.validation_marker must be {pr84_gate.SUCCESS_MARKER}")
    failures.extend(pr84_gate.validate_policy_payload(registry, label="PR84_REGISTRY"))
    formulas = _list_of_mappings(registry.get("formula_definitions"))
    if [item.get("formula_id") for item in formulas] != list(FORMULA_ORDER):
        failures.append("STACK_SCORING_RANKING_ALLOWED_PR84_FORMULA_POLICY: PR84 formula order must match canonical formulas")
    for field in pr84_gate.NO_AUTHORITY_FALSE_FIELDS:
        if report.get(field) is not False:
            failures.append(f"PR84_REPORT.{field} must be false")
    return failures, registry


def _candidate_id_map(candidates: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(candidate.get("candidate_stack_descriptor_id") or ""): candidate
        for candidate in candidates
    }


def _candidate_is_quantum_applicable(candidate: dict[str, Any]) -> bool:
    labels = candidate.get("quantum_applicability_labels")
    if not isinstance(labels, list):
        return False
    return any(label != "CLASSICAL_ONLY" for label in labels)


def validate_candidate_descriptor(
    candidate: dict[str, Any],
    *,
    candidate_ids: set[str],
    pr82_labels: set[str],
    mode_policies: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Decimal] | None]:
    failures: list[str] = []
    candidate_id = str(candidate.get("candidate_stack_descriptor_id") or "")
    label = f"candidate {candidate_id or '<missing>'}"
    if not candidate_id:
        failures.append("STACK_SCORING_RANKING_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR: candidate_stack_descriptor_id must be non-empty")
    if candidate.get("candidate_descriptor_source") != "SYNTHETIC_STATIC_FIXTURE_ONLY":
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.candidate_descriptor_source must be SYNTHETIC_STATIC_FIXTURE_ONLY")
    if candidate.get("candidate_descriptor_authority") != "NON_RUNTIME_NON_LIVE_TEST_FIXTURE":
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.candidate_descriptor_authority must be NON_RUNTIME_NON_LIVE_TEST_FIXTURE")
    if candidate.get("scoring_policy_registry_id") != pr84_gate.POLICY_REGISTRY_ID:
        failures.append(f"STACK_SCORING_RANKING_ALLOWED_PR84_FORMULA_POLICY: {label}.scoring_policy_registry_id must reference PR84")
    for field in CANDIDATE_FALSE_FIELDS:
        if candidate.get(field) is not False:
            code = FIELD_REASON_CODES.get(field, "STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD")
            failures.append(f"{code}: {label}.{field} must be false")
    if candidate.get("eligible_for_future_selection_flag") is not False:
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_FINAL_SELECTION_FORBIDDEN: {label}.eligible_for_future_selection_flag must be false in PR85")
    if candidate.get("owner_override_external_fact_fabrication_created") is not False:
        failures.append(f"STACK_SCORING_RANKING_ALLOWED_OWNER_INTERNAL_PRIORITY: {label}.owner_override_external_fact_fabrication_created must be false")

    valid = candidate.get("valid_for_ranking_flag")
    if not isinstance(valid, bool):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.valid_for_ranking_flag must be boolean")
        valid = False

    rank = candidate.get("rank")
    blocked_codes = candidate.get("blocked_reason_codes")
    if not isinstance(blocked_codes, list):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.blocked_reason_codes must be a list")
        blocked_codes = []
    reason_codes = [str(code) for code in blocked_codes]
    if reason_codes != _sort_reason_codes(reason_codes):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: {label}.blocked_reason_codes must use canonical order")
    unknown_reason_codes = [code for code in reason_codes if code not in REASON_CODE_ORDER]
    if unknown_reason_codes:
        failures.append(f"{label}.blocked_reason_codes has unknown codes {', '.join(unknown_reason_codes)}")
    if valid:
        if reason_codes:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label} valid candidates must not have blocked_reason_codes")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: {label}.rank must be positive integer")
    else:
        if rank is not None:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: {label} blocked candidates must not receive a rank")
        if not reason_codes:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label} blocked candidates must retain reason codes")

    labels = candidate.get("quantum_applicability_labels")
    if not isinstance(labels, list) or not labels:
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.quantum_applicability_labels must be non-empty")
        labels = []
    unknown_labels = [str(item) for item in labels if str(item) not in pr82_labels]
    if unknown_labels and (valid or "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL" not in reason_codes):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL: {label} unknown labels {', '.join(unknown_labels)}")

    mode = str(candidate.get("owner_quantum_priority_mode") or "")
    if mode not in mode_policies:
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED: {label}.owner_quantum_priority_mode is unknown")

    if not valid:
        return failures, None

    for field in ("selected_parameter_family_ids", "selected_algorithm_family_ids"):
        value = candidate.get(field)
        if not isinstance(value, list) or not value:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.{field} must be non-empty")
    role_map = candidate.get("selected_stack_role_map")
    if not isinstance(role_map, dict):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.selected_stack_role_map must be an object")
    else:
        missing_roles = [role for role in ROLE_ORDER if role not in role_map]
        if missing_roles:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label} missing stack roles {', '.join(missing_roles)}")

    inputs = candidate.get("scoring_component_inputs")
    if not isinstance(inputs, dict):
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label}.scoring_component_inputs must be an object")
        inputs = {}
    if list(inputs) != list(COMPONENT_INPUT_ORDER):
        missing = [name for name in COMPONENT_INPUT_ORDER if name not in inputs]
        unknown = [name for name in inputs if name not in COMPONENT_INPUT_ORDER]
        if missing:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD: {label} missing scoring inputs {', '.join(missing)}")
        if unknown:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_UNKNOWN_SCORING_COMPONENT: {label} unknown scoring inputs {', '.join(unknown)}")
        failures.append(f"{label}.scoring_component_inputs must use canonical PR84 component order")

    breakdown = candidate.get("score_breakdown")
    if not isinstance(breakdown, dict) or not breakdown:
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_SCORE_BREAKDOWN: {label}.score_breakdown must be present")
        return failures, None
    if list(breakdown) != list(SCORE_BREAKDOWN_ORDER):
        missing = [name for name in SCORE_BREAKDOWN_ORDER if name not in breakdown]
        unknown = [name for name in breakdown if name not in SCORE_BREAKDOWN_ORDER]
        if missing:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_MISSING_SCORE_BREAKDOWN: {label} missing score_breakdown fields {', '.join(missing)}")
        if unknown:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_UNKNOWN_SCORING_COMPONENT: {label} unknown score_breakdown fields {', '.join(unknown)}")
        failures.append(f"{label}.score_breakdown must use canonical deterministic order")

    computed = _formula_scores(inputs, failures, label)
    if computed is None:
        return failures, None
    for name in SCORE_BREAKDOWN_ORDER:
        actual = _decimal(breakdown.get(name), f"{label}.score_breakdown.{name}", failures)
        if actual is None:
            continue
        if actual != computed[name]:
            failures.append(
                "STACK_SCORING_RANKING_ALLOWED_PR84_FORMULA_POLICY: "
                f"{label}.score_breakdown.{name} must equal deterministic PR84 formula value "
                f"{_json_number(computed[name])}"
            )

    quantum_boost = computed["quantum_boost"]
    is_quantum = _candidate_is_quantum_applicable(candidate)
    comparator_id = candidate.get("classical_comparator_candidate_descriptor_id")
    comparator_required = (
        is_quantum
        or mode == "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK"
        or mode_policies.get(mode, {}).get("classical_comparator_required") is True
    )
    if comparator_required:
        if candidate.get("classical_comparator_metadata_present") is not True:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_CLASSICAL_COMPARATOR_MISSING: {label} requires classical comparator metadata")
        if not isinstance(comparator_id, str) or comparator_id not in candidate_ids or comparator_id == candidate_id:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_CLASSICAL_COMPARATOR_MISSING: {label} requires a valid classical comparator candidate ID")

    if quantum_boost > Decimal("0"):
        if not _quantum_tie_allowed(mode, mode_policies):
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED: {label} quantum_boost is not permitted by owner quantum priority mode {mode}")
        if candidate.get("quantum_priority_applied_flag") is not True:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED: {label}.quantum_priority_applied_flag must be true when quantum_boost is positive")
    elif candidate.get("quantum_priority_applied_flag") is not False:
        failures.append(f"STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED: {label}.quantum_priority_applied_flag must be false without quantum_boost")

    owner_override_score = computed["owner_override_score"]
    if candidate.get("owner_override_applied") is True or owner_override_score > Decimal("0"):
        if candidate.get("owner_override_internal_only_flag") is not True:
            failures.append(f"STACK_SCORING_RANKING_ALLOWED_OWNER_INTERNAL_PRIORITY: {label}.owner_override_internal_only_flag must be true")
        if candidate.get("owner_override_external_fact_fabrication_created") is not False:
            failures.append(f"STACK_SCORING_RANKING_ALLOWED_OWNER_INTERNAL_PRIORITY: {label}.owner_override_external_fact_fabrication_created must be false")
    return failures, computed


def _ranking_sort_key(
    candidate: dict[str, Any],
    scores: dict[str, Decimal],
    mode_policies: dict[str, dict[str, Any]],
) -> tuple[Any, ...]:
    mode = str(candidate.get("owner_quantum_priority_mode") or "")
    quantum_tie_value = scores["quantum_boost"] if _quantum_tie_allowed(mode, mode_policies) else Decimal("0")
    owner_priority_value = scores["owner_priority_boost"] if mode != "QUANTUM_NEUTRAL" else Decimal("0")
    return (
        -scores["final_selection_score"],
        -scores["base_score"],
        -quantum_tie_value,
        scores["total_penalty"],
        -owner_priority_value,
        scores["complexity_penalty"],
        str(candidate.get("candidate_stack_descriptor_id") or ""),
    )


def validate_fixture(
    fixture: dict[str, Any],
    *,
    pr82_labels: set[str],
    pr83_policy: dict[str, Any] | None,
) -> tuple[list[str], dict[str, dict[str, Decimal]]]:
    failures: list[str] = []
    for field, expected in (
        ("mode", "SOURCE_REQUIRED"),
        ("execution", "DISABLED"),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("gate_scope", GATE_SCOPE),
    ):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "scoring_ranking_contract_only_flag",
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
        expected_code = case.get("expected_reason_code")
        if expected_code not in REASON_CODE_ORDER:
            failures.append(f"fixture case {case.get('case_id')} has unknown expected_reason_code")
        if case.get("synthetic_case_only") is not True:
            failures.append(f"fixture case {case.get('case_id')} must be synthetic_case_only")

    candidates = _list_of_mappings(fixture.get("candidate_stack_descriptors"))
    candidate_ids = [str(candidate.get("candidate_stack_descriptor_id") or "") for candidate in candidates]
    if candidate_ids != list(REQUIRED_CANDIDATE_IDS):
        missing = [candidate_id for candidate_id in REQUIRED_CANDIDATE_IDS if candidate_id not in candidate_ids]
        unknown = [candidate_id for candidate_id in candidate_ids if candidate_id not in REQUIRED_CANDIDATE_IDS]
        if missing:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR: missing candidates {', '.join(missing)}")
        if unknown:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR: unknown candidates {', '.join(unknown)}")
        failures.append("fixture.candidate_stack_descriptors must use canonical deterministic candidate order")
    seen: set[str] = set()
    for candidate_id in candidate_ids:
        if candidate_id in seen:
            failures.append(f"STACK_SCORING_RANKING_BLOCKED_DUPLICATE_CANDIDATE_DESCRIPTOR: duplicate candidate {candidate_id}")
        seen.add(candidate_id)

    mode_policies = _mode_policy_map(pr83_policy)
    score_by_candidate: dict[str, dict[str, Decimal]] = {}
    candidate_id_set = set(candidate_ids)
    for candidate in candidates:
        candidate_failures, scores = validate_candidate_descriptor(
            candidate,
            candidate_ids=candidate_id_set,
            pr82_labels=pr82_labels,
            mode_policies=mode_policies,
        )
        failures.extend(candidate_failures)
        candidate_id = str(candidate.get("candidate_stack_descriptor_id") or "")
        if scores is not None:
            score_by_candidate[candidate_id] = scores

    valid_candidates = [
        candidate for candidate in candidates if candidate.get("valid_for_ranking_flag") is True
    ]
    if len(valid_candidates) != len(score_by_candidate):
        failures.append("STACK_SCORING_RANKING_BLOCKED_MISSING_SCORE_BREAKDOWN: every valid candidate must have deterministic scores")
        return failures, score_by_candidate

    expected_order = sorted(
        valid_candidates,
        key=lambda candidate: _ranking_sort_key(
            candidate,
            score_by_candidate[str(candidate.get("candidate_stack_descriptor_id"))],
            mode_policies,
        ),
    )
    expected_rank_ids = [str(candidate["candidate_stack_descriptor_id"]) for candidate in expected_order]
    actual_rank_ids = [
        str(candidate["candidate_stack_descriptor_id"])
        for candidate in sorted(valid_candidates, key=lambda candidate: candidate.get("rank"))
    ]
    if expected_rank_ids != actual_rank_ids:
        failures.append(
            "STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: candidate ranks must match deterministic tie-break order "
            f"{expected_rank_ids}"
        )
    for index, candidate in enumerate(expected_order, start=1):
        if candidate.get("rank") != index:
            failures.append(
                "STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: "
                f"{candidate.get('candidate_stack_descriptor_id')}.rank must be {index}"
            )
    if expected_rank_ids[:2] != [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
    ]:
        failures.append("STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED: quantum-priority fixtures must rank higher only under PR83 policy")
    if expected_rank_ids[-2:] != ["TIE_BREAK_STABILITY_FIXTURE_A", "TIE_BREAK_STABILITY_FIXTURE_B"]:
        failures.append("STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS: tie-break stability fixtures must resolve lexicographically")
    return failures, score_by_candidate


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if (_resolve(repo_root, CANONICAL_BUNDLE_SHA256)).exists():
        failures.append(
            "STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
        )
    if not (_resolve(repo_root, PR76_SHORT_TEST)).exists():
        failures.append(f"PR76 short runtime resolver allowlist test is missing: {PR76_SHORT_TEST.as_posix()}")
    if (_resolve(repo_root, PR76_OLD_LONG_TEST)).exists():
        failures.append(f"old long runtime resolver allowlist filename must remain absent: {PR76_OLD_LONG_TEST.as_posix()}")
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
        return [f"{MASTER_PLAN_CURRENT.as_posix()} has local diff; PR85 must not edit it"]
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
    return [f"validator contains forbidden nondeterministic or network token {token}" for token in forbidden_tokens if token in text]


def _report_candidate(candidate: dict[str, Any], scores: dict[str, Decimal] | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "candidate_stack_descriptor_id": candidate.get("candidate_stack_descriptor_id"),
        "candidate_descriptor_source": candidate.get("candidate_descriptor_source"),
        "candidate_descriptor_authority": candidate.get("candidate_descriptor_authority"),
        "valid_for_ranking_flag": candidate.get("valid_for_ranking_flag"),
        "rank": candidate.get("rank"),
        "rank_reason_codes": list(candidate.get("rank_reason_codes", [])),
        "blocked_reason_codes": list(candidate.get("blocked_reason_codes", [])),
        "eligible_for_future_selection_flag": False,
        "real_generated_candidate_claim_created": False,
        "selected_stack_claim_created": False,
        "profit_evidence_created": False,
        "quantum_advantage_claim_created": False,
    }
    if scores is not None:
        result["score_breakdown"] = {
            name: _json_number(scores[name]) for name in SCORE_BREAKDOWN_ORDER
        }
    else:
        result["score_breakdown"] = {}
    return result


def build_report(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    score_by_candidate: dict[str, dict[str, Decimal]],
    pr82_labels: set[str],
    pr83_policy: dict[str, Any] | None,
    pr84_policy: dict[str, Any] | None,
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    candidates = _list_of_mappings(fixture.get("candidate_stack_descriptors"))
    valid_candidates = [candidate for candidate in candidates if candidate.get("valid_for_ranking_flag") is True]
    blocked_candidates = [candidate for candidate in candidates if candidate.get("valid_for_ranking_flag") is False]
    mode_policies = _mode_policy_map(pr83_policy)
    ranked_candidates = sorted(
        valid_candidates,
        key=lambda candidate: _ranking_sort_key(
            candidate,
            score_by_candidate[str(candidate.get("candidate_stack_descriptor_id"))],
            mode_policies,
        ),
    )
    ranked_ids = [str(candidate.get("candidate_stack_descriptor_id")) for candidate in ranked_candidates]
    blocked_ids = sorted(str(candidate.get("candidate_stack_descriptor_id")) for candidate in blocked_candidates)
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "gate_registry_id": registry.get("gate_registry_id"),
        "parameter_stack_scoring_ranking_gate_id": registry.get("parameter_stack_scoring_ranking_gate_id"),
        "semantic_task_id": registry.get("semantic_task_id"),
        "gate_scope": registry.get("gate_scope"),
        "policy_version": POLICY_VERSION,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "scoring_ranking_contract_only_flag": True,
        "static_candidate_descriptor_fixture_only": True,
        "policy_source": copy.deepcopy(registry.get("policy_source")),
        "quantum_applicability_source": copy.deepcopy(registry.get("quantum_applicability_source")),
        "owner_quantum_priority_source": copy.deepcopy(registry.get("owner_quantum_priority_source")),
        "pr82_quantum_applicability_labels": pr84_gate._sort_by_order(pr82_labels, pr84_gate.PR82_LABEL_ORDER),
        "pr83_supported_quantum_priority_modes": list(pr84_gate.PR83_MODE_ORDER),
        "pr83_default_quantum_priority_mode": None if pr83_policy is None else pr83_policy.get("default_quantum_priority_mode"),
        "pr84_formula_ids": [] if pr84_policy is None else [item.get("formula_id") for item in _list_of_mappings(pr84_policy.get("formula_definitions"))],
        "ranking_policy": copy.deepcopy(registry.get("ranking_policy")),
        "ranking_inputs": list(RANKING_INPUT_ORDER),
        "ranking_outputs": list(RANKING_OUTPUT_ORDER),
        "tie_break_order": list(TIE_BREAK_ORDER),
        "rank_assignment_policy": "SEQUENTIAL_RANK",
        "score_sort_order": "DESCENDING_FINAL_SELECTION_SCORE",
        "stable_sort_required": True,
        "random_sort_allowed": False,
        "candidate_descriptor_count": len(candidates),
        "valid_candidate_descriptor_count": len(valid_candidates),
        "blocked_candidate_descriptor_count": len(blocked_candidates),
        "candidate_descriptor_ids": [str(candidate.get("candidate_stack_descriptor_id")) for candidate in candidates],
        "ranked_candidate_descriptor_ids": ranked_ids,
        "blocked_candidate_descriptor_ids": blocked_ids,
        "highest_ranked_candidate_descriptor_id": ranked_ids[0] if ranked_ids else None,
        "static_scored_candidate_descriptors": [
            _report_candidate(
                candidate,
                score_by_candidate.get(str(candidate.get("candidate_stack_descriptor_id"))),
            )
            for candidate in candidates
        ],
        "static_ranked_candidate_descriptors": [
            _report_candidate(candidate, score_by_candidate[str(candidate.get("candidate_stack_descriptor_id"))])
            for candidate in ranked_candidates
        ],
        "blocked_candidate_descriptors": [
            _report_candidate(candidate, None) for candidate in sorted(blocked_candidates, key=lambda item: str(item.get("candidate_stack_descriptor_id")))
        ],
        "upstream_dependency_ids": list(DEPENDENCY_ORDER),
        "future_consumer_ids": list(FUTURE_CONSUMER_ORDER),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "deterministic_candidate_descriptor_ordering": True,
        "deterministic_score_breakdown_ordering": True,
        "deterministic_ranking_ordering": True,
        "deterministic_blocked_candidate_ordering": True,
        "deterministic_tie_break_output": True,
        "deterministic_upstream_dependency_ordering": True,
        "deterministic_future_consumer_ordering": True,
        "deterministic_reason_code_ordering": True,
        "no_selection_boundary": True,
        "classical_only_comparator_valid": True,
        "hybrid_tiebreak_requires_classical_comparator": True,
        "quantum_priority_owner_policy_gated": True,
        "atomicrows_bundle_jsonl_exists": _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": False,
        "final_ready": False,
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
        failures.append("generated report must use the deterministic generated_at_utc sentinel")
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

    failures.extend(schema_subset_failures(registry, schema, "REGISTRY"))
    failures.extend(validate_gate_payload(registry, repo_root=repo_root))
    pr82_failures, pr82_labels = pr84_gate.validate_pr82_registry(repo_root)
    failures.extend(pr82_failures)
    pr83_failures, pr83_policy = pr84_gate.validate_pr83_policy(repo_root)
    failures.extend(pr83_failures)
    pr84_failures, pr84_policy = validate_pr84_policy(repo_root)
    failures.extend(pr84_failures)
    fixture_failures, score_by_candidate = validate_fixture(
        fixture,
        pr82_labels=pr82_labels,
        pr83_policy=pr83_policy,
    )
    failures.extend(fixture_failures)
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

    report = build_report(
        registry,
        fixture,
        score_by_candidate,
        pr82_labels,
        pr83_policy,
        pr84_policy,
        repo_root,
    )
    failures.extend(validate_report_is_deterministic(report))

    if failures:
        return ValidationResult(False, tuple(failures), report)

    write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report)


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
        return 0

    print(FAILURE_MARKER)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
