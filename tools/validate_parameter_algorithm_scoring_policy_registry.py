#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "scoring"
    / "parameter_algorithm_scoring_policy_registry.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "scoring"
    / "ParameterAlgorithmScoringPolicyRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "scoring"
    / "synthetic_parameter_algorithm_scoring_policy_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "ParameterAlgorithmScoringPolicyRegistry.report.json"
)

PR82_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "quantum"
    / "QuantumApplicabilityClassificationRegistry.yaml"
)
PR82_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QuantumApplicabilityClassificationRegistry.report.json"
)
PR83_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "quantum"
    / "OwnerQuantumPriorityPolicyRegistry.yaml"
)
PR83_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "OwnerQuantumPriorityPolicyRegistry.report.json"
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

POLICY_REGISTRY_ID = "QTT_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY"
REPORT_ID = "QTT_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY_REPORT"
POLICY_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-PARAMETER-AND-ALGORITHM-SCORING-POLICY-REGISTRY"
POLICY_SCOPE = "STATIC_PARAMETER_AND_ALGORITHM_SCORING_FORMULA_REGISTRY_ONLY"
PR82_SEMANTIC_TASK_ID = "ROADMAP-QUANTUM-APPLICABILITY-REGISTRY"
PR83_SEMANTIC_TASK_ID = "ROADMAP-OWNER-QUANTUM-PRIORITY-POLICY"
PR82_SUCCESS_MARKER = "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK"
PR83_SUCCESS_MARKER = "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK"
SUCCESS_MARKER = "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK"
FAILURE_MARKER = "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_FAILED"

COMPONENT_ORDER = (
    "agent_binding_score",
    "lifecycle_status_score",
    "owner_override_score",
    "platform_applicability_score",
    "market_type_applicability_score",
    "strategy_fit_score",
    "latency_fit_score",
    "risk_fit_score",
    "replay_paper_score",
    "optimizer_score",
    "runtime_readiness_score",
    "quantum_applicability_score",
    "expected_net_profit_score",
    "drawdown_penalty",
    "complexity_penalty",
    "source_currentness_penalty",
    "execution_cost_penalty",
    "owner_priority_boost",
    "quantum_priority_multiplier",
    "owner_quantum_priority_boost",
    "quantum_boost",
    "base_score",
    "final_selection_score",
)
LINEAGE_REQUIRED_COMPONENTS = (
    "agent_binding_score",
    "lifecycle_status_score",
    "owner_override_score",
    "platform_applicability_score",
    "market_type_applicability_score",
    "strategy_fit_score",
    "latency_fit_score",
    "risk_fit_score",
    "replay_paper_score",
    "optimizer_score",
    "runtime_readiness_score",
    "quantum_applicability_score",
    "expected_net_profit_score",
    "drawdown_penalty",
    "complexity_penalty",
    "source_currentness_penalty",
    "execution_cost_penalty",
    "owner_priority_boost",
    "owner_quantum_priority_boost",
    "quantum_boost",
    "base_score",
    "final_selection_score",
)
FORMULA_ORDER = (
    "PENALTY_COMPONENTS_FORMULA",
    "READINESS_COMPONENTS_FORMULA",
    "BASE_SCORE_FORMULA",
    "QUANTUM_BOOST_FORMULA",
    "FINAL_SELECTION_SCORE_FORMULA",
)
FORMULA_OUTPUT_ORDER = (
    "combined_penalty_score",
    "readiness_score",
    "base_score",
    "quantum_boost",
    "final_selection_score",
)
FORMULA_EXPECTATIONS = {
    "PENALTY_COMPONENTS_FORMULA": {
        "output_name": "combined_penalty_score",
        "output_class": "PENALTY_FORMULA_OUTPUT",
        "deterministic_order": 10,
        "formula_expression": "drawdown_penalty + complexity_penalty + source_currentness_penalty + execution_cost_penalty",
        "allowed_input_components": (
            "drawdown_penalty",
            "complexity_penalty",
            "source_currentness_penalty",
            "execution_cost_penalty",
        ),
    },
    "READINESS_COMPONENTS_FORMULA": {
        "output_name": "readiness_score",
        "output_class": "READINESS_FORMULA_OUTPUT",
        "deterministic_order": 20,
        "formula_expression": "runtime_readiness_score - source_currentness_penalty",
        "allowed_input_components": (
            "runtime_readiness_score",
            "source_currentness_penalty",
        ),
    },
    "BASE_SCORE_FORMULA": {
        "output_name": "base_score",
        "output_class": "SCORE_FORMULA_OUTPUT",
        "deterministic_order": 30,
        "formula_expression": (
            "0.10*agent_binding_score + 0.08*lifecycle_status_score + "
            "0.08*owner_override_score + 0.08*platform_applicability_score + "
            "0.08*market_type_applicability_score + 0.10*strategy_fit_score + "
            "0.08*latency_fit_score + 0.08*risk_fit_score + "
            "0.08*replay_paper_score + 0.08*optimizer_score + "
            "0.08*readiness_score + 0.05*expected_net_profit_score + "
            "0.03*owner_priority_boost - combined_penalty_score"
        ),
        "allowed_input_components": (
            "agent_binding_score",
            "lifecycle_status_score",
            "owner_override_score",
            "platform_applicability_score",
            "market_type_applicability_score",
            "strategy_fit_score",
            "latency_fit_score",
            "risk_fit_score",
            "replay_paper_score",
            "optimizer_score",
            "readiness_score",
            "expected_net_profit_score",
            "owner_priority_boost",
            "combined_penalty_score",
        ),
    },
    "QUANTUM_BOOST_FORMULA": {
        "output_name": "quantum_boost",
        "output_class": "BOOST_FORMULA_OUTPUT",
        "deterministic_order": 40,
        "formula_expression": "quantum_applicability_score * quantum_priority_multiplier * owner_quantum_priority_boost",
        "allowed_input_components": (
            "quantum_applicability_score",
            "quantum_priority_multiplier",
            "owner_quantum_priority_boost",
        ),
    },
    "FINAL_SELECTION_SCORE_FORMULA": {
        "output_name": "final_selection_score",
        "output_class": "SCORE_FORMULA_OUTPUT",
        "deterministic_order": 50,
        "formula_expression": "base_score + quantum_boost",
        "allowed_input_components": ("base_score", "quantum_boost"),
    },
}
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
)
DEPENDENCY_MARKERS = {
    "PR65_QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY": "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_OK",
    "PR66_QTT_AGENT_ALGORITHM_BINDING_REGISTRY": "QTT_AGENT_ALGORITHM_BINDING_REGISTRY_OK",
    "PR67_QTT_AGENT_ALGORITHM_CONSUMER_GATE": "QTT_AGENT_ALGORITHM_CONSUMER_GATE_OK",
    "PR68_QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE": "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_OK",
    "PR73_ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY": "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK",
    "PR74_ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE": "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK",
    "PR75_ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE": "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK",
    "PR77_EDGE_PARAMETER_STACK_SELECTION_PACKET": "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK",
    "PR78_QTT_TRADE_CONTEXT_PACKET": "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK",
    "PR79_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY": "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_OK",
    "PR80_ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE": "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK",
    "PR81_QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE": "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK",
    "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY": PR82_SUCCESS_MARKER,
    "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY": PR83_SUCCESS_MARKER,
}
FUTURE_CONSUMER_ORDER = (
    "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE",
    "PR86_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE",
    "PR87_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
    "PR88_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
    "PR89_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
    "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
)
PR82_LABEL_ORDER = (
    "TRUE_QUANTUM",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUANTUM_INSPIRED",
    "QUBO_COMPATIBLE",
    "ISING_COMPATIBLE",
    "QAOA_COMPATIBLE",
    "VQE_COMPATIBLE",
    "ANNEALING_COMPATIBLE",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE",
    "CLASSICAL_ONLY",
)
PR83_MODE_ORDER = (
    "QUANTUM_NEUTRAL",
    "QUANTUM_PREFERRED",
    "QUANTUM_STRONGLY_PREFERRED",
    "QUANTUM_FIRST",
    "OWNER_FORCED_QUANTUM",
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK",
)
PR83_MULTIPLIER_MIN = 1.00
PR83_MULTIPLIER_MAX = 1.50
REASON_CODE_ORDER = (
    "SCORING_POLICY_ALLOWED_FORMULA_REGISTRY_ONLY",
    "SCORING_POLICY_ALLOWED_STATIC_METADATA_ONLY",
    "SCORING_POLICY_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
    "SCORING_POLICY_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
    "SCORING_POLICY_ALLOWED_CLASSICAL_COMPARATOR",
    "SCORING_POLICY_ALLOWED_OWNER_INTERNAL_PRIORITY",
    "SCORING_POLICY_ALLOWED_FUTURE_REPLAY_PAPER_COMPONENT_PLACEHOLDER",
    "SCORING_POLICY_ALLOWED_FUTURE_OPTIMIZER_COMPONENT_PLACEHOLDER",
    "SCORING_POLICY_ALLOWED_FUTURE_RUNTIME_READINESS_PLACEHOLDER",
    "SCORING_POLICY_ALLOWED_EXPECTED_NET_PROFIT_PLACEHOLDER_NOT_EVIDENCE",
    "SCORING_POLICY_BLOCKED_UNKNOWN_COMPONENT",
    "SCORING_POLICY_BLOCKED_DUPLICATE_COMPONENT",
    "SCORING_POLICY_BLOCKED_MISSING_REQUIRED_COMPONENT",
    "SCORING_POLICY_BLOCKED_UNKNOWN_FORMULA",
    "SCORING_POLICY_BLOCKED_DUPLICATE_FORMULA",
    "SCORING_POLICY_BLOCKED_MISSING_REQUIRED_FORMULA",
    "SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT",
    "SCORING_POLICY_BLOCKED_INVALID_FORMULA_OUTPUT",
    "SCORING_POLICY_BLOCKED_FORMULA_EXECUTION_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_RANKING_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_SELECTION_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_RANDOM_POLICY_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "SCORING_POLICY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
BLOCKED_POLICY_ORDER = (
    "UNKNOWN_SCORING_COMPONENT",
    "DUPLICATE_SCORING_COMPONENT",
    "MISSING_REQUIRED_SCORING_COMPONENT",
    "UNKNOWN_FORMULA_DEFINITION",
    "DUPLICATE_FORMULA_DEFINITION",
    "MISSING_REQUIRED_FORMULA_DEFINITION",
    "INVALID_FORMULA_INPUT_COMPONENT",
    "INVALID_FORMULA_OUTPUT",
    "FORMULA_EXECUTION_CLAIM",
    "SCORING_RESULT_CLAIM",
    "RANKING_CLAIM",
    "SELECTION_CLAIM",
    "OPTIMIZER_EXECUTION_CLAIM",
    "OPTIMIZER_ARBITRATION_CLAIM",
    "BACKEND_EXECUTION_CLAIM",
    "SIMULATOR_EXECUTION_CLAIM",
    "REPLAY_PAPER_RESULT_CLAIM",
    "RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM",
    "SOURCE_RETRIEVAL_CLAIM",
    "SOURCE_ACCEPTANCE_CLAIM",
    "CONNECTOR_BINDING_CLAIM",
    "RUNTIME_CASH_RECEIPT_CLAIM",
    "PRIVATE_STATE_FETCH_CLAIM",
    "PROFIT_EVIDENCE_CLAIM",
    "QUANTUM_ADVANTAGE_CLAIM",
    "LATENCY_SUPERIORITY_CLAIM",
    "EXECUTION_SUPERIORITY_CLAIM",
    "RANDOM_POLICY_ATTEMPT",
    "ATOMICROWS_BUNDLE_JSONL_CREATION",
    "ATOMICROWS_BUNDLE_SHA256_CREATION",
)
COMPONENT_FALSE_FIELDS = (
    "creates_real_score",
    "creates_runtime_evidence",
    "creates_profit_evidence",
    "creates_quantum_advantage_evidence",
    "creates_latency_superiority_evidence",
    "creates_execution_superiority_evidence",
    "creates_optimizer_execution",
    "creates_runtime_readiness_receipt",
    "creates_replay_paper_result",
    "creates_source_retrieval",
    "creates_source_acceptance",
    "creates_venue_fee_tick_cost_fact",
)
FORMULA_FALSE_FIELDS = (
    "formula_execution_created",
    "scoring_result_created",
    "ranking_created",
    "selection_created",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "scoring_execution_created",
    "ranking_created",
    "selection_created",
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
    "random_scoring_policy_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
    "formula_execution_created",
    "scoring_result_created",
    "selection_created",
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
)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_REGISTRY_VALIDATES",
    "PASS_REQUIRED_COMPONENTS_PRESENT",
    "PASS_REQUIRED_FORMULAS_PRESENT",
    "PASS_BASE_SCORE_FORMULA_ONLY",
    "PASS_QUANTUM_BOOST_FORMULA_PR82_PR83_METADATA",
    "PASS_FINAL_SELECTION_SCORE_FORMULA_ONLY",
    "PASS_EXPECTED_NET_PROFIT_PLACEHOLDER_NOT_EVIDENCE",
    "PASS_LATENCY_FIT_PLACEHOLDER_NOT_SUPERIORITY",
    "PASS_OPTIMIZER_PLACEHOLDER_NOT_EXECUTION",
    "PASS_RUNTIME_READINESS_PLACEHOLDER_NOT_RECEIPT",
    "PASS_REPLAY_PAPER_PLACEHOLDER_NOT_RESULT",
    "PASS_SOURCE_CURRENTNESS_PLACEHOLDER_NOT_SOURCE_AUTHORITY",
    "PASS_EXECUTION_COST_PLACEHOLDER_NOT_VENUE_FACT",
    "PASS_OWNER_OVERRIDE_INTERNAL_ONLY",
    "PASS_PR82_METADATA_CONSUMED",
    "PASS_PR83_POLICY_CONSUMED",
    "PASS_FUTURE_CONSUMERS_PR85_TO_PR92",
    "PASS_NO_UNAUTHORIZED_ARTIFACTS",
    "BLOCK_MISSING_SEMANTIC_TASK_ID",
    "BLOCK_WRONG_SEMANTIC_TASK_ID",
    "BLOCK_MISSING_REQUIRED_COMPONENT",
    "BLOCK_DUPLICATE_COMPONENT",
    "BLOCK_UNKNOWN_COMPONENT",
    "BLOCK_MISSING_REQUIRED_FORMULA",
    "BLOCK_DUPLICATE_FORMULA",
    "BLOCK_UNKNOWN_FORMULA",
    "BLOCK_UNKNOWN_FORMULA_INPUT",
    "BLOCK_UNKNOWN_FORMULA_OUTPUT",
    "BLOCK_QUANTUM_BOOST_MISSING_QUANTUM_APPLICABILITY_SCORE",
    "BLOCK_QUANTUM_BOOST_MISSING_QUANTUM_PRIORITY_MULTIPLIER",
    "BLOCK_QUANTUM_BOOST_MISSING_OWNER_QUANTUM_PRIORITY_BOOST",
    "BLOCK_FINAL_SELECTION_SCORE_MISSING_BASE_SCORE",
    "BLOCK_FINAL_SELECTION_SCORE_MISSING_QUANTUM_BOOST",
    "BLOCK_FORMULA_EXECUTION_CLAIM",
    "BLOCK_SCORING_RESULT_CLAIM",
    "BLOCK_RANKING_CLAIM",
    "BLOCK_SELECTION_CLAIM",
    "BLOCK_OPTIMIZER_EXECUTION_CLAIM",
    "BLOCK_OPTIMIZER_ARBITRATION_CLAIM",
    "BLOCK_BACKEND_EXECUTION_CLAIM",
    "BLOCK_SIMULATOR_EXECUTION_CLAIM",
    "BLOCK_REPLAY_PAPER_RESULT_CLAIM",
    "BLOCK_RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM",
    "BLOCK_SOURCE_RETRIEVAL_CLAIM",
    "BLOCK_SOURCE_ACCEPTANCE_CLAIM",
    "BLOCK_CONNECTOR_BINDING_CLAIM",
    "BLOCK_RUNTIME_CASH_RECEIPT_CLAIM",
    "BLOCK_PRIVATE_STATE_FETCH_CLAIM",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "BLOCK_LATENCY_SUPERIORITY_CLAIM",
    "BLOCK_EXECUTION_SUPERIORITY_CLAIM",
    "BLOCK_RANDOM_POLICY_ATTEMPT",
    "BLOCK_ATOMICROWS_BUNDLE_JSONL",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
    "BLOCK_OLD_LONG_RUNTIME_RESOLVER_FILENAME",
)


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
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = load_yaml_subset(path)
    if not isinstance(value, dict):
        raise ValueError(f"registry root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: JSON file is invalid: {path}: {exc}"]


def _load_yaml_checked(
    path: pathlib.Path, label: str
) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: registry file is missing: {path}"]
    try:
        return load_yaml(path), []
    except (OSError, ValueError, RegistryParseError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: registry file is invalid: {path}: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label}{failure}" for failure in validate_json_schema_subset(payload, schema)]


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _component_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("component_name") or ""): item for item in _list_of_mappings(payload.get("scoring_components"))}


def _formula_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("formula_id") or ""): item for item in _list_of_mappings(payload.get("formula_definitions"))}


def _sort_by_order(values: Iterable[str], order: Sequence[str]) -> list[str]:
    index = {value: position for position, value in enumerate(order)}
    return sorted(dict.fromkeys(str(value) for value in values), key=lambda value: (index.get(value, 999), value))


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order(codes, REASON_CODE_ORDER)


def _reason_code_for_false_field(field: str) -> str:
    field_map = {
        "formula_execution_allowed": "SCORING_POLICY_BLOCKED_FORMULA_EXECUTION_FORBIDDEN",
        "formula_execution_created": "SCORING_POLICY_BLOCKED_FORMULA_EXECUTION_FORBIDDEN",
        "scoring_execution_created": "SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN",
        "scoring_result_allowed": "SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN",
        "scoring_result_created": "SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN",
        "ranking_result_allowed": "SCORING_POLICY_BLOCKED_RANKING_FORBIDDEN",
        "ranking_created": "SCORING_POLICY_BLOCKED_RANKING_FORBIDDEN",
        "selected_stack_allowed": "SCORING_POLICY_BLOCKED_SELECTION_FORBIDDEN",
        "selection_created": "SCORING_POLICY_BLOCKED_SELECTION_FORBIDDEN",
        "optimizer_execution_created": "SCORING_POLICY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
        "optimizer_arbitration_created": "SCORING_POLICY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
        "backend_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "quantum_backend_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "qaoa_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "vqe_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "annealing_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "qubo_solve_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "ising_solve_execution_created": "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "quantum_simulator_execution_created": "SCORING_POLICY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
        "replay_execution_created": "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
        "paper_execution_created": "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
        "runtime_authority_created": "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "live_authority_created": "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "order_authority_created": "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        "source_retrieval_created": "SCORING_POLICY_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
        "source_acceptance_created": "SCORING_POLICY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        "connector_semantic_binding_created": "SCORING_POLICY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
        "runtime_cash_receipt_created": "SCORING_POLICY_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
        "private_state_fetch_created": "SCORING_POLICY_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
        "expected_profit_claim_created": "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "profit_evidence_created": "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "quantum_advantage_claim_created": "SCORING_POLICY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
        "latency_superiority_claim_created": "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
        "execution_superiority_claim_created": "SCORING_POLICY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
        "random_scoring_policy_used": "SCORING_POLICY_BLOCKED_RANDOM_POLICY_FORBIDDEN",
        "random_policy_used": "SCORING_POLICY_BLOCKED_RANDOM_POLICY_FORBIDDEN",
        "atomicrows_bundle_jsonl_created": "SCORING_POLICY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
        "atomicrows_bundle_sha256_created": "SCORING_POLICY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
        "creates_optimizer_execution": "SCORING_POLICY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
        "creates_replay_paper_result": "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
        "creates_source_retrieval": "SCORING_POLICY_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
        "creates_source_acceptance": "SCORING_POLICY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        "creates_profit_evidence": "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
        "creates_quantum_advantage_evidence": "SCORING_POLICY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
        "creates_latency_superiority_evidence": "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
        "creates_execution_superiority_evidence": "SCORING_POLICY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    }
    return field_map.get(field, "SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN")


def validate_dependencies(payload: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    dependencies = _list_of_mappings(payload.get("upstream_dependencies"))
    ids = [str(item.get("artifact_id") or "") for item in dependencies]
    if ids != list(DEPENDENCY_ORDER):
        missing = [item for item in DEPENDENCY_ORDER if item not in ids]
        unknown = [item for item in ids if item not in DEPENDENCY_ORDER]
        if missing:
            failures.append(f"REGISTRY.upstream_dependencies missing artifact IDs {', '.join(missing)}")
        if unknown:
            failures.append(f"REGISTRY.upstream_dependencies has unknown artifact IDs {', '.join(unknown)}")
        failures.append("REGISTRY.upstream_dependencies must use canonical deterministic PR65-PR83 order")
    for dependency in dependencies:
        artifact_id = str(dependency.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker is None:
            failures.append(f"unknown dependency artifact_id {artifact_id}")
            continue
        if dependency.get("validation_marker") != expected_marker:
            failures.append(f"{artifact_id}.validation_marker must be {expected_marker}")
        for field in ("registry_path", "report_path", "validator_path"):
            path_value = dependency.get(field)
            if not isinstance(path_value, str) or not path_value:
                failures.append(f"{artifact_id}.{field} must be a non-empty string")
                continue
            if not (repo_root / pathlib.Path(path_value)).exists():
                failures.append(f"{artifact_id}.{field} is missing: {path_value}")
        validator_path = dependency.get("validator_path")
        if isinstance(validator_path, str):
            validator_abs = repo_root / pathlib.Path(validator_path)
            if validator_abs.exists() and expected_marker not in validator_abs.read_text(encoding="utf-8"):
                failures.append(f"{artifact_id}.validator_path does not expose marker {expected_marker}")
    return failures


def validate_future_consumers(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    consumers = _list_of_mappings(payload.get("future_consumers"))
    ids = [str(item.get("consumer_id") or "") for item in consumers]
    if ids != list(FUTURE_CONSUMER_ORDER):
        missing = [item for item in FUTURE_CONSUMER_ORDER if item not in ids]
        unknown = [item for item in ids if item not in FUTURE_CONSUMER_ORDER]
        if missing:
            failures.append(f"REGISTRY.future_consumers missing IDs {', '.join(missing)}")
        if unknown:
            failures.append(f"REGISTRY.future_consumers has unknown IDs {', '.join(unknown)}")
        failures.append("REGISTRY.future_consumers must use canonical PR85-PR92 order")
    for consumer in consumers:
        consumer_id = str(consumer.get("consumer_id") or "")
        if consumer.get("pr84_creates_consumer_execution") is not False:
            failures.append(f"{consumer_id}.pr84_creates_consumer_execution must be false")
    return failures


def validate_pr82_registry(repo_root: pathlib.Path) -> tuple[list[str], set[str]]:
    failures: list[str] = []
    registry, registry_failures = _load_yaml_checked(_resolve(repo_root, PR82_REGISTRY), "PR82_REGISTRY")
    report, report_failures = _load_json_checked(_resolve(repo_root, PR82_REPORT), "PR82_REPORT")
    failures.extend(registry_failures)
    failures.extend(report_failures)
    if registry is None or report is None:
        return failures, set()
    if registry.get("semantic_task_id") != PR82_SEMANTIC_TASK_ID:
        failures.append(f"PR82_REGISTRY.semantic_task_id must be {PR82_SEMANTIC_TASK_ID}")
    if registry.get("registry_scope") != "STATIC_QUANTUM_APPLICABILITY_METADATA_ONLY":
        failures.append("PR82_REGISTRY.registry_scope must be STATIC_QUANTUM_APPLICABILITY_METADATA_ONLY")
    if registry.get("static_only_flag") is not True:
        failures.append("PR82_REGISTRY.static_only_flag must be true")
    if registry.get("metadata_only_flag") is not True:
        failures.append("PR82_REGISTRY.metadata_only_flag must be true")
    if registry.get("classification_labels") != list(PR82_LABEL_ORDER):
        failures.append("PR82_REGISTRY.classification_labels must match canonical PR82 label order")
    if report.get("validation_marker") != PR82_SUCCESS_MARKER:
        failures.append(f"PR82_REPORT.validation_marker must be {PR82_SUCCESS_MARKER}")
    for field in (
        "backend_execution_created",
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "optimizer_arbitration_created",
        "scoring_execution_created",
        "ranking_created",
        "selection_created",
        "quantum_advantage_claim_created",
        "profit_evidence_created",
    ):
        if registry.get(field) is not False:
            failures.append(f"PR82_REGISTRY.{field} must be false")
        if report.get(field) is not False:
            failures.append(f"PR82_REPORT.{field} must be false")
    labels = set(str(label) for label in registry.get("classification_labels", []) if isinstance(label, str))
    return failures, labels


def validate_pr83_policy(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any] | None]:
    failures: list[str] = []
    registry, registry_failures = _load_yaml_checked(_resolve(repo_root, PR83_REGISTRY), "PR83_REGISTRY")
    report, report_failures = _load_json_checked(_resolve(repo_root, PR83_REPORT), "PR83_REPORT")
    failures.extend(registry_failures)
    failures.extend(report_failures)
    if registry is None or report is None:
        return failures, None
    if registry.get("semantic_task_id") != PR83_SEMANTIC_TASK_ID:
        failures.append(f"PR83_REGISTRY.semantic_task_id must be {PR83_SEMANTIC_TASK_ID}")
    if registry.get("policy_scope") != "STATIC_OWNER_QUANTUM_PRIORITY_POLICY_ONLY":
        failures.append("PR83_REGISTRY.policy_scope must be STATIC_OWNER_QUANTUM_PRIORITY_POLICY_ONLY")
    if registry.get("static_only_flag") is not True:
        failures.append("PR83_REGISTRY.static_only_flag must be true")
    if registry.get("metadata_only_flag") is not True:
        failures.append("PR83_REGISTRY.metadata_only_flag must be true")
    if registry.get("supported_quantum_priority_modes") != list(PR83_MODE_ORDER):
        failures.append("PR83_REGISTRY.supported_quantum_priority_modes must match canonical PR83 mode order")
    multiplier = registry.get("quantum_priority_multiplier")
    if not isinstance(multiplier, (int, float)) or isinstance(multiplier, bool):
        failures.append("PR83_REGISTRY.quantum_priority_multiplier must be numeric")
    elif not PR83_MULTIPLIER_MIN <= float(multiplier) <= PR83_MULTIPLIER_MAX:
        failures.append("PR83_REGISTRY.quantum_priority_multiplier must be bounded 1.00 to 1.50")
    if report.get("validation_marker") != PR83_SUCCESS_MARKER:
        failures.append(f"PR83_REPORT.validation_marker must be {PR83_SUCCESS_MARKER}")
    if report.get("pr82_quantum_applicability_registry_consumed") is not True:
        failures.append("PR83_REPORT.pr82_quantum_applicability_registry_consumed must be true")
    for field in (
        "backend_execution_created",
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "optimizer_execution_created",
        "optimizer_arbitration_created",
        "scoring_execution_created",
        "ranking_created",
        "selection_created",
        "runtime_authority_created",
        "live_authority_created",
        "order_authority_created",
        "source_retrieval_created",
        "source_acceptance_created",
        "connector_semantic_binding_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_advantage_claim_created",
        "profit_evidence_created",
        "latency_superiority_claim_created",
        "execution_superiority_claim_created",
    ):
        if registry.get(field) is not False:
            failures.append(f"PR83_REGISTRY.{field} must be false")
        if report.get(field) is not False:
            failures.append(f"PR83_REPORT.{field} must be false")
    return failures, registry


def validate_root_policy(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    exact_values = {
        "policy_registry_id": POLICY_REGISTRY_ID,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "policy_scope": POLICY_SCOPE,
        "policy_version": POLICY_VERSION,
        "pr82_quantum_applicability_registry_path": PR82_REGISTRY.as_posix(),
        "pr83_owner_quantum_priority_policy_registry_path": PR83_REGISTRY.as_posix(),
    }
    for field, expected in exact_values.items():
        if payload.get(field) != expected:
            failures.append(f"REGISTRY.{field} must be {expected}")
    for field in ("static_only_flag", "metadata_only_flag", "formula_registry_only_flag", "formula_definition_allowed"):
        if payload.get(field) is not True:
            failures.append(f"REGISTRY.{field} must be true")
    false_root_fields = (
        "formula_execution_allowed",
        "scoring_result_allowed",
        "ranking_result_allowed",
        "selected_stack_allowed",
        "final_ready",
    )
    for field in false_root_fields:
        if payload.get(field) is not False:
            failures.append(f"{_reason_code_for_false_field(field)}: REGISTRY.{field} must be false")
    if payload.get("pr82_quantum_applicability_metadata_consumed") is not True:
        failures.append("REGISTRY.pr82_quantum_applicability_metadata_consumed must be true")
    if payload.get("pr83_owner_quantum_priority_policy_consumed") is not True:
        failures.append("REGISTRY.pr83_owner_quantum_priority_policy_consumed must be true")
    if payload.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("REGISTRY.reason_codes must match canonical deterministic reason code order")
    no_authority = payload.get("required_no_authority_flags")
    if not isinstance(no_authority, dict):
        failures.append("REGISTRY.required_no_authority_flags must be an object")
    else:
        fields = list(no_authority)
        if fields != list(NO_AUTHORITY_FALSE_FIELDS):
            failures.append("REGISTRY.required_no_authority_flags must use canonical deterministic no-authority field order")
        for field in NO_AUTHORITY_FALSE_FIELDS:
            if no_authority.get(field) is not False:
                failures.append(f"{_reason_code_for_false_field(field)}: REGISTRY.required_no_authority_flags.{field} must be false")
    return failures


def validate_scoring_components(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    components = _list_of_mappings(payload.get("scoring_components"))
    names = [str(item.get("component_name") or "") for item in components]
    if names != list(COMPONENT_ORDER):
        missing = [name for name in COMPONENT_ORDER if name not in names]
        unknown = [name for name in names if name not in COMPONENT_ORDER]
        if missing:
            failures.append(f"SCORING_POLICY_BLOCKED_MISSING_REQUIRED_COMPONENT: missing components {', '.join(missing)}")
        if unknown:
            failures.append(f"SCORING_POLICY_BLOCKED_UNKNOWN_COMPONENT: unknown components {', '.join(unknown)}")
        failures.append("REGISTRY.scoring_components must use canonical deterministic component order")
    seen: set[str] = set()
    for name in names:
        if name in seen:
            failures.append(f"SCORING_POLICY_BLOCKED_DUPLICATE_COMPONENT: duplicate component {name}")
        seen.add(name)
    if not set(LINEAGE_REQUIRED_COMPONENTS).issubset(set(names)):
        missing_lineage = [name for name in LINEAGE_REQUIRED_COMPONENTS if name not in names]
        failures.append(f"SCORING_POLICY_BLOCKED_MISSING_REQUIRED_COMPONENT: missing lineage components {', '.join(missing_lineage)}")

    by_name = _component_map(payload)
    for name in COMPONENT_ORDER:
        component = by_name.get(name)
        if component is None:
            continue
        expected_id = name.upper()
        if component.get("component_id") != expected_id:
            failures.append(f"{name}.component_id must be {expected_id}")
        for field in COMPONENT_FALSE_FIELDS:
            if component.get(field) is not False:
                failures.append(f"{_reason_code_for_false_field(field)}: {name}.{field} must be false")
        for field in ("component_class", "input_source_class", "allowed_value_range", "default_static_placeholder_value", "future_required_gate", "boundary_note"):
            if not isinstance(component.get(field), str) or not component.get(field):
                failures.append(f"{name}.{field} must be a non-empty string")

    component_checks = {
        "expected_net_profit_score": (
            ("creates_profit_evidence", False, "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
            ("default_static_placeholder_value", "NOT_PROFIT_EVIDENCE", "SCORING_POLICY_ALLOWED_EXPECTED_NET_PROFIT_PLACEHOLDER_NOT_EVIDENCE"),
        ),
        "latency_fit_score": (
            ("creates_latency_superiority_evidence", False, "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
            ("default_static_placeholder_value", "NOT_EVIDENCE", "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
        ),
        "optimizer_score": (
            ("creates_optimizer_execution", False, "SCORING_POLICY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
            ("default_static_placeholder_value", "NOT_EXECUTION", "SCORING_POLICY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ),
        "runtime_readiness_score": (
            ("creates_runtime_readiness_receipt", False, "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
            ("default_static_placeholder_value", "NOT_RECEIPT", "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ),
        "replay_paper_score": (
            ("creates_replay_paper_result", False, "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
            ("default_static_placeholder_value", "NOT_RESULT", "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
        ),
        "source_currentness_penalty": (
            ("creates_source_retrieval", False, "SCORING_POLICY_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN"),
            ("creates_source_acceptance", False, "SCORING_POLICY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN"),
        ),
        "execution_cost_penalty": (
            ("creates_venue_fee_tick_cost_fact", False, "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
            ("default_static_placeholder_value", "NOT_VENUE_FACT", "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ),
    }
    for component_name, checks in component_checks.items():
        component = by_name.get(component_name, {})
        for field, expected, code in checks:
            value = component.get(field)
            if isinstance(expected, bool) and value is not expected:
                failures.append(f"{code}: {component_name}.{field} must be {str(expected).lower()}")
            elif isinstance(expected, str) and expected not in str(value):
                failures.append(f"{code}: {component_name}.{field} must contain {expected}")

    if by_name.get("owner_override_score", {}).get("internal_only_flag") is not True:
        failures.append("SCORING_POLICY_ALLOWED_OWNER_INTERNAL_PRIORITY: owner_override_score.internal_only_flag must be true")
    if by_name.get("owner_override_score", {}).get("creates_source_retrieval") is not False:
        failures.append("SCORING_POLICY_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN: owner_override_score cannot fabricate source facts")
    if by_name.get("quantum_applicability_score", {}).get("consumes_pr82_quantum_applicability_metadata") is not True:
        failures.append("SCORING_POLICY_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA: quantum_applicability_score must consume PR82 metadata")
    for name in ("quantum_priority_multiplier", "owner_quantum_priority_boost"):
        if by_name.get(name, {}).get("consumes_pr83_owner_quantum_priority_policy") is not True:
            failures.append(f"SCORING_POLICY_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY: {name} must consume PR83 policy metadata")
        if by_name.get(name, {}).get("internal_only_flag") is not True:
            failures.append(f"SCORING_POLICY_ALLOWED_OWNER_INTERNAL_PRIORITY: {name}.internal_only_flag must be true")
    for name in ("quantum_boost", "final_selection_score"):
        component = by_name.get(name, {})
        if component.get("creates_real_score") is not False:
            failures.append(f"SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN: {name}.creates_real_score must be false")
    return failures


def validate_formula_definitions(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    formulas = _list_of_mappings(payload.get("formula_definitions"))
    formula_ids = [str(item.get("formula_id") or "") for item in formulas]
    if formula_ids != list(FORMULA_ORDER):
        missing = [formula_id for formula_id in FORMULA_ORDER if formula_id not in formula_ids]
        unknown = [formula_id for formula_id in formula_ids if formula_id not in FORMULA_ORDER]
        if missing:
            failures.append(f"SCORING_POLICY_BLOCKED_MISSING_REQUIRED_FORMULA: missing formulas {', '.join(missing)}")
        if unknown:
            failures.append(f"SCORING_POLICY_BLOCKED_UNKNOWN_FORMULA: unknown formulas {', '.join(unknown)}")
        failures.append("REGISTRY.formula_definitions must use canonical deterministic formula order")
    seen: set[str] = set()
    for formula_id in formula_ids:
        if formula_id in seen:
            failures.append(f"SCORING_POLICY_BLOCKED_DUPLICATE_FORMULA: duplicate formula {formula_id}")
        seen.add(formula_id)

    allowed_component_names = set(str(name) for name in COMPONENT_ORDER)
    prior_outputs: set[str] = set()
    allowed_outputs = set(FORMULA_OUTPUT_ORDER)
    for expected_id in FORMULA_ORDER:
        formula = _formula_map(payload).get(expected_id)
        if formula is None:
            continue
        expected = FORMULA_EXPECTATIONS[expected_id]
        for field in FORMULA_FALSE_FIELDS:
            if formula.get(field) is not False:
                failures.append(f"{_reason_code_for_false_field(field)}: {expected_id}.{field} must be false")
        if formula.get("formula_definition_type") != "SYMBOLIC_STATIC_FORMULA_DEFINITION_ONLY":
            failures.append(f"{expected_id}.formula_definition_type must be SYMBOLIC_STATIC_FORMULA_DEFINITION_ONLY")
        for field in ("output_name", "output_class", "deterministic_order", "formula_expression"):
            if formula.get(field) != expected[field]:
                failures.append(f"{expected_id}.{field} must be {expected[field]}")
        expected_inputs = list(expected["allowed_input_components"])
        actual_inputs = formula.get("allowed_input_components")
        if actual_inputs != expected_inputs:
            failures.append(f"SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT: {expected_id}.allowed_input_components must be {expected_inputs}")
        if formula.get("output_name") not in allowed_outputs:
            failures.append(f"SCORING_POLICY_BLOCKED_INVALID_FORMULA_OUTPUT: {expected_id}.output_name is not allowed")
        for input_name in actual_inputs if isinstance(actual_inputs, list) else []:
            if input_name not in allowed_component_names and input_name not in prior_outputs:
                failures.append(f"SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT: {expected_id} references unknown input {input_name}")
        output_name = formula.get("output_name")
        if isinstance(output_name, str):
            prior_outputs.add(output_name)

    quantum = _formula_map(payload).get("QUANTUM_BOOST_FORMULA", {})
    quantum_inputs = set(quantum.get("allowed_input_components", []))
    for input_name in ("quantum_applicability_score", "quantum_priority_multiplier", "owner_quantum_priority_boost"):
        if input_name not in quantum_inputs:
            failures.append(f"SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT: QUANTUM_BOOST_FORMULA must reference {input_name}")
    quantum_sources = set(str(item) for item in quantum.get("upstream_metadata_sources", []) if isinstance(item, str))
    if "PR82_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY" not in quantum_sources:
        failures.append("SCORING_POLICY_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA: QUANTUM_BOOST_FORMULA must reference PR82 metadata")
    if "PR83_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY" not in quantum_sources:
        failures.append("SCORING_POLICY_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY: QUANTUM_BOOST_FORMULA must reference PR83 policy")

    final = _formula_map(payload).get("FINAL_SELECTION_SCORE_FORMULA", {})
    final_inputs = set(final.get("allowed_input_components", []))
    if "base_score" not in final_inputs:
        failures.append("SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT: FINAL_SELECTION_SCORE_FORMULA must reference base_score")
    if "quantum_boost" not in final_inputs:
        failures.append("SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT: FINAL_SELECTION_SCORE_FORMULA must reference quantum_boost")
    if final.get("selection_created") is not False:
        failures.append("SCORING_POLICY_BLOCKED_SELECTION_FORBIDDEN: FINAL_SELECTION_SCORE_FORMULA.selection_created must be false")
    return failures


def validate_blocked_policies(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    blocked = _list_of_mappings(payload.get("blocked_policies"))
    blocked_ids = [str(item.get("policy_id") or "") for item in blocked]
    if blocked_ids != list(BLOCKED_POLICY_ORDER):
        failures.append("REGISTRY.blocked_policies must use canonical deterministic blocked policy order")
    if len(blocked) != len(BLOCK_REASON_CODES):
        failures.append("REGISTRY.blocked_policies must cover each blocked reason code exactly once")
    for index, entry in enumerate(blocked):
        codes = entry.get("blocked_reason_codes")
        if not isinstance(codes, list) or not codes:
            failures.append(f"REGISTRY.blocked_policies[{index}].blocked_reason_codes must be a non-empty list")
            continue
        unknown_codes = [str(code) for code in codes if str(code) not in REASON_CODE_ORDER]
        if unknown_codes:
            failures.append(f"REGISTRY.blocked_policies[{index}].blocked_reason_codes has unknown codes {', '.join(unknown_codes)}")
        if [str(code) for code in codes] != _sort_reason_codes(str(code) for code in codes):
            failures.append(f"REGISTRY.blocked_policies[{index}].blocked_reason_codes must use canonical deterministic order")
        if index < len(BLOCK_REASON_CODES) and codes != [BLOCK_REASON_CODES[index]]:
            failures.append(f"REGISTRY.blocked_policies[{index}].blocked_reason_codes must be {[BLOCK_REASON_CODES[index]]}")
    return failures


def validate_policy_payload(payload: dict[str, Any], *, label: str = "REGISTRY") -> list[str]:
    failures: list[str] = []
    for failure in validate_root_policy(payload):
        failures.append(failure if failure.startswith("REGISTRY.") or ":" in failure else f"{label}.{failure}")
    failures.extend(validate_future_consumers(payload))
    failures.extend(validate_scoring_components(payload))
    failures.extend(validate_formula_definitions(payload))
    failures.extend(validate_blocked_policies(payload))
    return failures


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    if fixture.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"fixture.semantic_task_id must be {SEMANTIC_TASK_ID}")
    if fixture.get("policy_scope") != POLICY_SCOPE:
        failures.append(f"fixture.policy_scope must be {POLICY_SCOPE}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "formula_registry_only_flag",
    ):
        if fixture.get(field) is not True:
            failures.append(f"fixture.{field} must be true")
    for field in ("formula_execution_created", *NO_AUTHORITY_FALSE_FIELDS):
        if fixture.get(field) is not False:
            failures.append(f"fixture.{field} must be false")
    cases = _list_of_mappings(fixture.get("fixture_cases"))
    case_ids = [str(case.get("case_id") or "") for case in cases]
    missing = [case_id for case_id in REQUIRED_FIXTURE_CASE_IDS if case_id not in case_ids]
    if missing:
        failures.append(f"fixture.fixture_cases missing case IDs {', '.join(missing)}")
    for case in cases:
        expected_code = case.get("expected_reason_code")
        if expected_code not in REASON_CODE_ORDER:
            failures.append(f"fixture case {case.get('case_id')} has unknown expected_reason_code")
        if case.get("synthetic_case_only") is not True:
            failures.append(f"fixture case {case.get('case_id')} must be synthetic_case_only")
    return failures


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if (_resolve(repo_root, CANONICAL_BUNDLE_JSONL)).exists():
        failures.append(
            "SCORING_POLICY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN: "
            f"{CANONICAL_BUNDLE_JSONL.as_posix()} must be absent"
        )
    if (_resolve(repo_root, CANONICAL_BUNDLE_SHA256)).exists():
        failures.append(
            "SCORING_POLICY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
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
        return [f"{MASTER_PLAN_CURRENT.as_posix()} has local diff; PR84 must not edit it"]
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


def build_report(payload: dict[str, Any], pr82_labels: set[str], pr83_policy: dict[str, Any] | None) -> dict[str, Any]:
    components = [_component_map(payload)[name] for name in COMPONENT_ORDER if name in _component_map(payload)]
    formulas = [_formula_map(payload)[formula_id] for formula_id in FORMULA_ORDER if formula_id in _formula_map(payload)]
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "policy_registry_id": payload.get("policy_registry_id"),
        "semantic_task_id": payload.get("semantic_task_id"),
        "policy_scope": payload.get("policy_scope"),
        "policy_version": POLICY_VERSION,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "formula_registry_only_flag": True,
        "formula_definition_allowed": True,
        "formula_execution_allowed": False,
        "formula_execution_created": False,
        "scoring_execution_created": False,
        "scoring_result_created": False,
        "ranking_created": False,
        "selection_created": False,
        "selected_stack_created": False,
        "pr82_quantum_applicability_metadata_consumed": True,
        "pr83_owner_quantum_priority_policy_consumed": True,
        "pr82_applicability_labels": _sort_by_order(pr82_labels, PR82_LABEL_ORDER),
        "pr83_default_quantum_priority_mode": None if pr83_policy is None else pr83_policy.get("default_quantum_priority_mode"),
        "pr83_quantum_priority_multiplier": None if pr83_policy is None else pr83_policy.get("quantum_priority_multiplier"),
        "component_count": len(components),
        "scoring_component_names": list(COMPONENT_ORDER),
        "lineage_required_component_names": list(LINEAGE_REQUIRED_COMPONENTS),
        "scoring_components": copy.deepcopy(components),
        "formula_count": len(formulas),
        "formula_ids": list(FORMULA_ORDER),
        "formula_outputs": list(FORMULA_OUTPUT_ORDER),
        "formula_definitions": copy.deepcopy(formulas),
        "upstream_dependency_ids": list(DEPENDENCY_ORDER),
        "future_consumer_ids": list(FUTURE_CONSUMER_ORDER),
        "blocked_policy_ids": list(BLOCKED_POLICY_ORDER),
        "reason_codes": list(REASON_CODE_ORDER),
        "required_no_authority_flags": dict(payload.get("required_no_authority_flags", {})),
        "deterministic_component_ordering": True,
        "deterministic_formula_ordering": True,
        "deterministic_dependency_ordering": True,
        "deterministic_future_consumer_ordering": True,
        "deterministic_reason_code_ordering": True,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "expected_net_profit_score_is_profit_evidence": False,
        "latency_fit_score_is_latency_superiority_evidence": False,
        "optimizer_score_is_optimizer_execution": False,
        "runtime_readiness_score_is_runtime_receipt": False,
        "replay_paper_score_is_replay_paper_result": False,
        "source_currentness_penalty_is_source_authority": False,
        "execution_cost_penalty_is_venue_fact": False,
        "owner_override_score_can_fabricate_external_facts": False,
        "quantum_boost_is_quantum_advantage_evidence": False,
        "final_selection_score_is_selected_stack_or_trade": False,
        "candidate_stack_generation_created": False,
        "source_retrieval_execution_created": False,
        "source_acceptance_execution_created": False,
        "runtime_resolver_execution_created": False,
        "private_state_fetch_execution_created": False,
        "balance_fetch_created": False,
        "open_order_fetch_created": False,
        "order_submission_created": False,
        "order_cancellation_created": False,
        "order_reduction_created": False,
        "fill_receipt_created": False,
        "walk_forward_execution_created": False,
        "backend_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_solve_execution_created": False,
        "ising_solve_execution_created": False,
        "dashboard_runtime_service_created": False,
        "telegram_runtime_service_created": False,
        "final_ready": False,
    }
    for field in NO_AUTHORITY_FALSE_FIELDS:
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
    failures.extend(validate_fixture(fixture))
    pr82_failures, pr82_labels = validate_pr82_registry(repo_root)
    failures.extend(pr82_failures)
    pr83_failures, pr83_policy = validate_pr83_policy(repo_root)
    failures.extend(pr83_failures)
    failures.extend(validate_dependencies(registry, repo_root))
    failures.extend(validate_policy_payload(registry, label="REGISTRY"))
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

    report = build_report(registry, pr82_labels, pr83_policy)
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
