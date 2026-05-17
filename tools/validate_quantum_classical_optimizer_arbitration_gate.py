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

from tools import validate_parameter_stack_scoring_and_ranking_gate as pr85_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "quantum"
    / "quantum_classical_optimizer_arbitration_gate.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "quantum"
    / "QuantumClassicalOptimizerArbitrationGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "quantum"
    / "synthetic_quantum_classical_optimizer_arbitration_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QuantumClassicalOptimizerArbitrationGate.report.json"
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

GATE_REGISTRY_ID = "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE"
GATE_ID = "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_V1"
REPORT_ID = "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_REPORT"
POLICY_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-QUANTUM-CLASSICAL-OPTIMIZER-ARBITRATION-GATE"
GATE_SCOPE = "STATIC_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_CONTRACT_ONLY"
SUCCESS_MARKER = "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK"
FAILURE_MARKER = "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_FAILED"

ARBITRATION_MODE_ORDER = (
    "CLASSICAL_BASELINE",
    "QUANTUM_CHALLENGER",
    "HYBRID_COMPARE_THEN_SELECT",
    "QUANTUM_FIRST",
    "OWNER_FORCED_QUANTUM",
    "OWNER_FORCED_CLASSICAL",
)
ARBITRATION_DECISION_ORDER = (
    "USE_CLASSICAL_BASELINE_FIXTURE",
    "USE_QUANTUM_CHALLENGER_FIXTURE",
    "USE_HYBRID_COMPARISON_FIXTURE",
    "USE_QUANTUM_FIRST_FIXTURE",
    "USE_OWNER_FORCED_QUANTUM_FIXTURE",
    "USE_OWNER_FORCED_CLASSICAL_FIXTURE",
    "BLOCK_ARBITRATION_FIXTURE",
)
VALID_DECISION_BY_MODE = {
    "CLASSICAL_BASELINE": "USE_CLASSICAL_BASELINE_FIXTURE",
    "QUANTUM_CHALLENGER": "USE_QUANTUM_CHALLENGER_FIXTURE",
    "HYBRID_COMPARE_THEN_SELECT": "USE_HYBRID_COMPARISON_FIXTURE",
    "QUANTUM_FIRST": "USE_QUANTUM_FIRST_FIXTURE",
    "OWNER_FORCED_QUANTUM": "USE_OWNER_FORCED_QUANTUM_FIXTURE",
    "OWNER_FORCED_CLASSICAL": "USE_OWNER_FORCED_CLASSICAL_FIXTURE",
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
    "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY",
    "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE",
)
DEPENDENCY_MARKERS = {
    **pr85_gate.DEPENDENCY_MARKERS,
    "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY": pr85_gate.pr84_gate.SUCCESS_MARKER,
    "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE": pr85_gate.SUCCESS_MARKER,
}
FUTURE_CONSUMER_ORDER = (
    "PR87_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
    "PR88_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
    "PR89_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
    "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR91_DUAL_RESULT_REVIEW_PARAMETER_STACKS",
    "PR92_OWNER_LIVE_PROMOTION_REVIEW_PARAMETER_STACKS",
    "PR105_PR151_STAGE1_RUNTIME_LIVE_LAUNCH_CLOSURE_CONSUMERS",
)
ARBITRATION_INPUT_ORDER = (
    "synthetic_optimizer_output_fixtures",
    "PR85_static_ranked_candidate_descriptor_fixtures",
    "PR84_scoring_policy_registry",
    "PR83_owner_quantum_priority_policy_registry",
    "PR82_quantum_applicability_classification_registry",
    "classical_baseline_fixture_metadata",
    "quantum_challenger_fixture_metadata",
    "owner_override_basis",
    "blocked_arbitration_policy",
    "tie_break_policy",
)
ARBITRATION_OUTPUT_ORDER = (
    "static_arbitration_fixture_decisions",
    "blocked_arbitration_fixtures",
    "arbitration_reason_codes",
    "no_selection_boundary",
    "no_optimizer_execution_boundary",
    "no_backend_execution_boundary",
)
TIE_BREAK_ORDER = (
    "valid_for_arbitration_flag_true_before_false",
    "non_blocked_fixture_before_blocked_fixture",
    "owner_forced_mode_with_valid_owner_basis_before_non_forced_mode_if_owner_policy_permits",
    "higher_pr85_final_selection_score_fixture_metadata",
    "higher_pr85_base_score_fixture_metadata",
    "quantum_mode_wins_tie_only_if_pr83_owner_quantum_priority_permits_quantum_tie_break",
    "classical_baseline_wins_tie_if_quantum_not_permitted_stale_unsupported_missing_comparator_or_blocked",
    "lower_total_penalty_lower_uncertainty_metadata",
    "lexicographic_arbitration_fixture_id",
)
REASON_CODE_ORDER = (
    "OPTIMIZER_ARBITRATION_ALLOWED_STATIC_FIXTURE_ONLY",
    "OPTIMIZER_ARBITRATION_ALLOWED_CLASSICAL_BASELINE_FIXTURE",
    "OPTIMIZER_ARBITRATION_ALLOWED_QUANTUM_CHALLENGER_FIXTURE",
    "OPTIMIZER_ARBITRATION_ALLOWED_HYBRID_COMPARE_THEN_SELECT_FIXTURE",
    "OPTIMIZER_ARBITRATION_ALLOWED_QUANTUM_FIRST_FIXTURE",
    "OPTIMIZER_ARBITRATION_ALLOWED_OWNER_FORCED_QUANTUM_INTERNAL_ONLY",
    "OPTIMIZER_ARBITRATION_ALLOWED_OWNER_FORCED_CLASSICAL_INTERNAL_ONLY",
    "OPTIMIZER_ARBITRATION_ALLOWED_PR82_QUANTUM_APPLICABILITY_METADATA",
    "OPTIMIZER_ARBITRATION_ALLOWED_PR83_OWNER_QUANTUM_PRIORITY_POLICY",
    "OPTIMIZER_ARBITRATION_ALLOWED_PR84_SCORING_POLICY",
    "OPTIMIZER_ARBITRATION_ALLOWED_PR85_RANKING_FIXTURE",
    "OPTIMIZER_ARBITRATION_ALLOWED_CLASSICAL_COMPARATOR",
    "OPTIMIZER_ARBITRATION_ALLOWED_CLASSICAL_FALLBACK",
    "OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_ARBITRATION_MODE",
    "OPTIMIZER_ARBITRATION_BLOCKED_DUPLICATE_ARBITRATION_FIXTURE",
    "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD",
    "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR",
    "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_QUANTUM_CHALLENGER",
    "OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL",
    "OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_OWNER_QUANTUM_PRIORITY_MODE",
    "OPTIMIZER_ARBITRATION_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS",
    "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_PRIORITY_NOT_PERMITTED",
    "OPTIMIZER_ARBITRATION_BLOCKED_RANDOM_ARBITRATION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS",
    "OPTIMIZER_ARBITRATION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_REAL_OPTIMIZER_RESULT_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "OPTIMIZER_ARBITRATION_BLOCKED_FINAL_SELECTION_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
)
BLOCK_REASON_CODES = tuple(code for code in REASON_CODE_ORDER if "_BLOCKED_" in code)
REQUIRED_ARBITRATION_FIXTURE_IDS = (
    "CLASSICAL_BASELINE_FIXTURE",
    "QUANTUM_CHALLENGER_FIXTURE",
    "HYBRID_COMPARE_THEN_SELECT_FIXTURE",
    "QUANTUM_FIRST_FIXTURE",
    "OWNER_FORCED_QUANTUM_FIXTURE",
    "OWNER_FORCED_CLASSICAL_FIXTURE",
    "BLOCKED_BACKEND_EXECUTION_ATTEMPT_FIXTURE",
    "BLOCKED_MISSING_CLASSICAL_COMPARATOR_FIXTURE",
    "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_A",
    "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_B",
)
EXPECTED_ORDERED_VALID_FIXTURE_IDS = (
    "OWNER_FORCED_QUANTUM_FIXTURE",
    "OWNER_FORCED_CLASSICAL_FIXTURE",
    "QUANTUM_FIRST_FIXTURE",
    "QUANTUM_CHALLENGER_FIXTURE",
    "HYBRID_COMPARE_THEN_SELECT_FIXTURE",
    "CLASSICAL_BASELINE_FIXTURE",
    "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_A",
    "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_B",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "PASS_REGISTRY_VALIDATES",
    "PASS_ALL_REQUIRED_ARBITRATION_MODES_PRESENT",
    "PASS_FIXTURES_SYNTHETIC_STATIC_ONLY",
    "PASS_PR82_METADATA_CONSUMED",
    "PASS_PR83_POLICY_CONSUMED",
    "PASS_PR84_POLICY_CONSUMED",
    "PASS_PR85_RANKING_CONSUMED",
    "PASS_CLASSICAL_BASELINE_COMPARATOR_VALID",
    "PASS_QUANTUM_CHALLENGER_REQUIRES_APPLICABILITY_AND_NO_BACKEND",
    "PASS_HYBRID_REQUIRES_CLASSICAL_AND_QUANTUM_FIXTURES",
    "PASS_QUANTUM_FIRST_POLICY_GATED_AND_FALLBACK",
    "PASS_OWNER_FORCED_QUANTUM_INTERNAL_ONLY",
    "PASS_OWNER_FORCED_CLASSICAL_INTERNAL_ONLY",
    "PASS_DETERMINISTIC_ARBITRATION_DECISIONS",
    "PASS_DETERMINISTIC_TIE_BREAK",
    "PASS_BLOCKED_BACKEND_EXECUTION_ATTEMPT_TRACEABLE",
    "PASS_BLOCKED_MISSING_CLASSICAL_COMPARATOR_TRACEABLE",
    "PASS_HIGHEST_PRIORITY_NOT_FINAL_SELECTION",
    "PASS_STATIC_DECISION_NOT_LIVE_ORDER_AUTHORITY",
    "PASS_PR87_SCOPE_NOT_IMPLEMENTED",
    "PASS_PR88_SCOPE_NOT_IMPLEMENTED",
    "PASS_NO_RUNTIME_LIVE_ORDER_SOURCE_CONNECTOR_PROFIT_BACKEND_ARTIFACT",
    "BLOCK_MISSING_SEMANTIC_TASK_ID",
    "BLOCK_WRONG_SEMANTIC_TASK_ID",
    "BLOCK_MISSING_PR82_DEPENDENCY",
    "BLOCK_MISSING_PR83_DEPENDENCY",
    "BLOCK_MISSING_PR84_DEPENDENCY",
    "BLOCK_MISSING_PR85_DEPENDENCY",
    "BLOCK_UNKNOWN_ARBITRATION_MODE",
    "BLOCK_DUPLICATE_ARBITRATION_FIXTURE_ID",
    "BLOCK_FIXTURE_NOT_SYNTHETIC_STATIC",
    "BLOCK_REAL_OPTIMIZER_RESULT_CLAIM",
    "BLOCK_CLASSICAL_OPTIMIZER_EXECUTION_CLAIM",
    "BLOCK_QUANTUM_OPTIMIZER_EXECUTION_CLAIM",
    "BLOCK_BACKEND_EXECUTION_CLAIM",
    "BLOCK_SIMULATOR_EXECUTION_CLAIM",
    "BLOCK_QAOA_EXECUTION_CLAIM",
    "BLOCK_VQE_EXECUTION_CLAIM",
    "BLOCK_ANNEALING_EXECUTION_CLAIM",
    "BLOCK_QUBO_SOLVE_CLAIM",
    "BLOCK_ISING_SOLVE_CLAIM",
    "BLOCK_UNKNOWN_PR82_APPLICABILITY_LABEL",
    "BLOCK_UNKNOWN_PR83_PRIORITY_MODE",
    "BLOCK_MISSING_PR84_SCORING_POLICY_REFERENCE",
    "BLOCK_MISSING_PR85_RANKING_REFERENCE",
    "BLOCK_HYBRID_WITHOUT_CLASSICAL_COMPARATOR",
    "BLOCK_HYBRID_WITHOUT_QUANTUM_CHALLENGER",
    "BLOCK_QUANTUM_FIRST_WITHOUT_OWNER_PERMISSION",
    "BLOCK_OWNER_FORCED_QUANTUM_WITHOUT_OWNER_BASIS",
    "BLOCK_OWNER_FORCED_CLASSICAL_WITHOUT_OWNER_OR_FAILSAFE_BASIS",
    "BLOCK_RANDOM_ARBITRATION_POLICY",
    "BLOCK_AMBIGUOUS_TIE_BREAK",
    "BLOCK_REAL_GENERATED_CANDIDATE_STACK_CLAIM",
    "BLOCK_FINAL_SELECTION_CLAIM",
    "BLOCK_SELECTED_STACK_CLAIM",
    "BLOCK_REPLAY_PAPER_RESULT_CLAIM",
    "BLOCK_RUNTIME_LIVE_ORDER_AUTHORITY_CLAIM",
    "BLOCK_SOURCE_RETRIEVAL_ACCEPTANCE_CLAIM",
    "BLOCK_CONNECTOR_SEMANTIC_BINDING_CLAIM",
    "BLOCK_RUNTIME_CASH_RECEIPT_CLAIM",
    "BLOCK_PRIVATE_STATE_FETCH_CLAIM",
    "BLOCK_PROFIT_EVIDENCE_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "BLOCK_LATENCY_SUPERIORITY_CLAIM",
    "BLOCK_EXECUTION_SUPERIORITY_CLAIM",
    "BLOCK_ATOMICROWS_BUNDLE_JSONL",
    "BLOCK_ATOMICROWS_BUNDLE_SHA256",
    "BLOCK_OLD_LONG_RUNTIME_RESOLVER_FILENAME",
    "DETERMINISM_VALIDATOR_TWICE_BYTE_STABLE_REPORT",
    "DETERMINISM_FIXTURE_ORDERING",
    "DETERMINISM_DECISION_ORDERING",
    "DETERMINISM_BLOCKED_FIXTURE_ORDERING",
    "DETERMINISM_TIE_BREAK_OUTPUT",
    "DETERMINISM_UPSTREAM_DEPENDENCY_ORDERING",
    "DETERMINISM_FUTURE_CONSUMER_ORDERING",
    "DETERMINISM_REASON_CODE_ORDERING",
    "DETERMINISM_NO_TIMESTAMP_UUID_RANDOM_ENV_TEMP_ABSOLUTE_PATH_LEAK",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "classical_optimizer_execution_created",
    "quantum_optimizer_execution_created",
    "optimizer_execution_created",
    "optimizer_arbitration_execution_created",
    "backend_execution_created",
    "real_optimizer_result_created",
    "quantum_backend_execution_created",
    "quantum_simulator_execution_created",
    "qaoa_execution_created",
    "vqe_execution_created",
    "annealing_execution_created",
    "qubo_solve_execution_created",
    "ising_solve_execution_created",
    "real_candidate_stack_generation_created",
    "generated_candidate_stack_claim_created",
    "real_generated_candidate_claim_created",
    "final_selection_created",
    "selected_stack_created",
    "selected_trade_created",
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
    "random_arbitration_used",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
)
ARBITRATION_FIXTURE_FALSE_FIELDS = tuple(
    field
    for field in NO_AUTHORITY_FALSE_FIELDS
    if field
    not in {
        "optimizer_arbitration_execution_created",
        "real_candidate_stack_generation_created",
        "generated_candidate_stack_claim_created",
        "selected_trade_created",
        "expected_profit_claim_created",
        "random_arbitration_used",
        "atomicrows_bundle_jsonl_created",
        "atomicrows_bundle_sha256_created",
    }
) + ("selected_stack_claim_created",)
REPORT_FALSE_FIELDS = NO_AUTHORITY_FALSE_FIELDS + (
    "source_retrieval_execution_created",
    "source_acceptance_execution_created",
    "runtime_resolver_execution_created",
    "private_state_fetch_execution_created",
    "balance_fetch_created",
    "open_order_fetch_created",
    "order_submission_created",
    "order_cancellation_created",
    "order_replacement_created",
    "order_reduction_created",
    "order_close_created",
    "fill_receipt_created",
    "settlement_finality_receipt_created",
    "walk_forward_execution_created",
    "dashboard_runtime_service_created",
    "telegram_runtime_service_created",
    "optimizer_arbitration_fixture_is_optimizer_result",
    "static_arbitration_decision_is_final_selected_stack",
    "static_arbitration_decision_is_live_order_authority",
    "static_arbitration_decision_is_trading_signal",
    "expected_net_profit_metadata_is_profit_evidence",
    "latency_metadata_is_latency_superiority_evidence",
    "quantum_applicability_score_is_backend_evidence",
    "quantum_arbitration_preference_is_quantum_advantage",
    "owner_forced_quantum_fabricates_external_facts",
    "future_pr87_candidate_generation_implemented",
    "future_pr88_trade_context_selection_implemented",
    "future_pr90_replay_paper_competition_implemented",
    "future_live_authority_implemented",
)
FIELD_REASON_CODES = {
    "classical_optimizer_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_arbitration_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "backend_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "real_optimizer_result_created": "OPTIMIZER_ARBITRATION_BLOCKED_REAL_OPTIMIZER_RESULT_FORBIDDEN",
    "quantum_backend_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "quantum_simulator_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "qaoa_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "vqe_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "annealing_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "qubo_solve_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "ising_solve_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_ISING_SOLVE_FORBIDDEN",
    "real_candidate_stack_generation_created": "OPTIMIZER_ARBITRATION_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "generated_candidate_stack_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "real_generated_candidate_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM",
    "final_selection_created": "OPTIMIZER_ARBITRATION_BLOCKED_FINAL_SELECTION_FORBIDDEN",
    "selected_stack_created": "OPTIMIZER_ARBITRATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "selected_stack_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "selected_trade_created": "OPTIMIZER_ARBITRATION_BLOCKED_SELECTED_STACK_FORBIDDEN",
    "replay_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "paper_execution_created": "OPTIMIZER_ARBITRATION_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN",
    "runtime_authority_created": "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "live_authority_created": "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "order_authority_created": "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "source_retrieval_created": "OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN",
    "source_acceptance_created": "OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
    "connector_semantic_binding_created": "OPTIMIZER_ARBITRATION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
    "runtime_cash_receipt_created": "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN",
    "private_state_fetch_created": "OPTIMIZER_ARBITRATION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN",
    "expected_profit_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "profit_evidence_created": "OPTIMIZER_ARBITRATION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
    "quantum_advantage_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "latency_superiority_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
    "execution_superiority_claim_created": "OPTIMIZER_ARBITRATION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
    "random_arbitration_used": "OPTIMIZER_ARBITRATION_BLOCKED_RANDOM_ARBITRATION_FORBIDDEN",
    "atomicrows_bundle_jsonl_created": "OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN",
    "atomicrows_bundle_sha256_created": "OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN",
}
ATTEMPT_REASON_CODES = {
    "classical_optimizer_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN",
    "quantum_optimizer_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN",
    "optimizer_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
    "real_optimizer_result_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_REAL_OPTIMIZER_RESULT_FORBIDDEN",
    "backend_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
    "simulator_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    "qaoa_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_QAOA_EXECUTION_FORBIDDEN",
    "vqe_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_VQE_EXECUTION_FORBIDDEN",
    "annealing_execution_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
    "qubo_solve_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_QUBO_SOLVE_FORBIDDEN",
    "ising_solve_claimed": "OPTIMIZER_ARBITRATION_BLOCKED_ISING_SOLVE_FORBIDDEN",
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
    return pr85_gate.load_yaml(path)


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


def _sort_by_order(values: Iterable[str], order: Sequence[str]) -> list[str]:
    order_map = {value: index for index, value in enumerate(order)}
    return sorted((str(value) for value in values), key=lambda value: order_map.get(value, 9999))


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    return _sort_by_order((str(code) for code in codes), REASON_CODE_ORDER)


def _decimal(value: Any, label: str, failures: list[str]) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS: {label} must be numeric")
        return None
    return Decimal(str(value)).quantize(SCORE_QUANT)


def _mode_policy_map(pr83_policy: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if pr83_policy is None:
        return {}
    return {
        str(policy.get("mode")): policy
        for policy in _list_of_mappings(pr83_policy.get("mode_policies"))
    }


def _mode_enabled(mode: str, mode_policies: dict[str, dict[str, Any]]) -> bool:
    return mode in mode_policies and mode_policies[mode].get("mode_enabled") is True


def _quantum_priority_permitted(mode: str, mode_policies: dict[str, dict[str, Any]]) -> bool:
    if not _mode_enabled(mode, mode_policies):
        return False
    policy = mode_policies[mode]
    return bool(policy.get("tie_breaker_enabled") or policy.get("owner_can_force"))


def _owner_forced_mode(fixture: dict[str, Any]) -> bool:
    return fixture.get("arbitration_mode") in {
        "OWNER_FORCED_QUANTUM",
        "OWNER_FORCED_CLASSICAL",
    }


def _has_owner_or_failsafe_basis(fixture: dict[str, Any]) -> bool:
    basis = fixture.get("owner_override_basis")
    return isinstance(basis, str) and basis not in {"", "NONE"}


def _is_quantum_mode(fixture: dict[str, Any]) -> bool:
    return fixture.get("arbitration_mode") in {
        "QUANTUM_CHALLENGER",
        "HYBRID_COMPARE_THEN_SELECT",
        "QUANTUM_FIRST",
        "OWNER_FORCED_QUANTUM",
    }


def _is_classical_mode(fixture: dict[str, Any]) -> bool:
    return fixture.get("arbitration_mode") in {
        "CLASSICAL_BASELINE",
        "OWNER_FORCED_CLASSICAL",
    }


def _source_refs() -> dict[str, dict[str, str]]:
    return {
        "quantum_applicability_source": {
            "artifact_id": "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY",
            "registry_path": "docs/master_plan/quantum/QuantumApplicabilityClassificationRegistry.yaml",
            "report_path": "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json",
            "validator_path": "tools/validate_quantum_applicability_classification_registry.py",
            "validation_marker": "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK",
        },
        "owner_quantum_priority_source": {
            "artifact_id": "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY",
            "registry_path": "docs/master_plan/quantum/OwnerQuantumPriorityPolicyRegistry.yaml",
            "report_path": "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json",
            "validator_path": "tools/validate_owner_quantum_priority_policy_registry.py",
            "validation_marker": "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK",
        },
        "scoring_policy_source": {
            "artifact_id": "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY",
            "registry_path": "docs/master_plan/scoring/ParameterAlgorithmScoringPolicyRegistry.yaml",
            "report_path": "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
            "validator_path": "tools/validate_parameter_algorithm_scoring_policy_registry.py",
            "validation_marker": "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK",
        },
        "scoring_ranking_gate_source": {
            "artifact_id": "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE",
            "registry_path": "docs/master_plan/selection/ParameterStackScoringAndRankingGate.yaml",
            "report_path": "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json",
            "validator_path": "tools/validate_parameter_stack_scoring_and_ranking_gate.py",
            "validation_marker": "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK",
        },
    }


def _validate_source_refs(registry: dict[str, Any], repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for field, expected in _source_refs().items():
        source = registry.get(field)
        if not isinstance(source, dict):
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: registry.{field} must be an object")
            continue
        for key, expected_value in expected.items():
            if source.get(key) != expected_value:
                failures.append(
                    "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: "
                    f"registry.{field}.{key} must be {expected_value}"
                )
        for path_key in ("registry_path", "report_path", "validator_path"):
            path_value = source.get(path_key)
            if isinstance(path_value, str) and not (repo_root / path_value).exists():
                failures.append(
                    "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: "
                    f"registry.{field}.{path_key} path is missing: {path_value}"
                )
    return failures


def validate_gate_payload(registry: dict[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for field, expected in (
        ("gate_registry_id", GATE_REGISTRY_ID),
        ("optimizer_arbitration_gate_id", GATE_ID),
        ("semantic_task_id", SEMANTIC_TASK_ID),
        ("gate_scope", GATE_SCOPE),
        ("policy_version", POLICY_VERSION),
    ):
        if registry.get(field) != expected:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: registry.{field} must be {expected}")
    for field in (
        "static_only_flag",
        "metadata_only_flag",
        "synthetic_fixture_only_flag",
        "optimizer_arbitration_contract_only_flag",
    ):
        if registry.get(field) is not True:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: registry.{field} must be true")

    failures.extend(_validate_source_refs(registry, repo_root))

    dependency_ids = [str(item.get("artifact_id") or "") for item in _list_of_mappings(registry.get("upstream_dependencies"))]
    if dependency_ids != list(DEPENDENCY_ORDER):
        missing = [dependency for dependency in DEPENDENCY_ORDER if dependency not in dependency_ids]
        if missing:
            failures.append(
                "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: "
                f"registry.upstream_dependencies missing {', '.join(missing)}"
            )
        failures.append("registry.upstream_dependencies must use canonical deterministic PR65-PR85 order")
    for dependency in _list_of_mappings(registry.get("upstream_dependencies")):
        artifact_id = str(dependency.get("artifact_id") or "")
        expected_marker = DEPENDENCY_MARKERS.get(artifact_id)
        if expected_marker and dependency.get("validation_marker") != expected_marker:
            failures.append(f"dependency {artifact_id} validation_marker must be {expected_marker}")
        for path_key in ("registry_path", "report_path", "validator_path"):
            path_value = dependency.get(path_key)
            if isinstance(path_value, str) and not (repo_root / path_value).exists():
                failures.append(f"dependency {artifact_id}.{path_key} path is missing: {path_value}")

    future_ids = [str(item.get("consumer_id") or "") for item in _list_of_mappings(registry.get("future_consumers"))]
    if future_ids != list(FUTURE_CONSUMER_ORDER):
        failures.append("registry.future_consumers must use canonical deterministic PR87-PR92 plus PR105-PR151 order")
    for consumer in _list_of_mappings(registry.get("future_consumers")):
        if consumer.get("pr86_creates_consumer_execution") is not False:
            failures.append(f"{consumer.get('consumer_id')}.pr86_creates_consumer_execution must be false")

    if registry.get("arbitration_modes") != list(ARBITRATION_MODE_ORDER):
        failures.append("OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_ARBITRATION_MODE: registry.arbitration_modes must match canonical modes")
    if registry.get("arbitration_inputs") != list(ARBITRATION_INPUT_ORDER):
        failures.append("registry.arbitration_inputs must use canonical deterministic order")
    if registry.get("arbitration_outputs") != list(ARBITRATION_OUTPUT_ORDER):
        failures.append("registry.arbitration_outputs must use canonical deterministic order")

    policy = registry.get("arbitration_policy")
    if not isinstance(policy, dict):
        failures.append("OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: registry.arbitration_policy must be an object")
    else:
        if policy.get("stable_sort_required") is not True:
            failures.append("OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS: stable_sort_required must be true")
        if policy.get("random_arbitration_allowed") is not False:
            failures.append("OPTIMIZER_ARBITRATION_BLOCKED_RANDOM_ARBITRATION_FORBIDDEN: random_arbitration_allowed must be false")
        if policy.get("final_selection_created") is not False or policy.get("selected_stack_created") is not False:
            failures.append("OPTIMIZER_ARBITRATION_BLOCKED_FINAL_SELECTION_FORBIDDEN: arbitration policy must not create selection")
        if policy.get("tie_break_order") != list(TIE_BREAK_ORDER):
            failures.append("OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS: tie_break_order must match canonical PR86 order")

    blocked_policy = registry.get("blocked_arbitration_policy")
    if not isinstance(blocked_policy, dict):
        failures.append("OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: registry.blocked_arbitration_policy must be an object")
    else:
        for field, expected in (
            ("blocked_fixtures_remain_traceable", True),
            ("blocked_fixtures_receive_static_decision_only", True),
            ("blocked_fixtures_retain_reason_codes", True),
        ):
            if blocked_policy.get(field) is not expected:
                failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: blocked_arbitration_policy.{field} must be {str(expected).lower()}")
        if blocked_policy.get("blocked_reason_code_order") != list(BLOCK_REASON_CODES):
            failures.append("registry.blocked_arbitration_policy.blocked_reason_code_order must match canonical blocked reason-code order")

    if registry.get("reason_codes") != list(REASON_CODE_ORDER):
        failures.append("registry.reason_codes must use canonical deterministic reason-code order")

    flags = registry.get("required_no_authority_flags")
    if not isinstance(flags, dict):
        failures.append("OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: required_no_authority_flags must be an object")
    else:
        for field in NO_AUTHORITY_FALSE_FIELDS:
            if flags.get(field) is not False:
                failures.append(f"{FIELD_REASON_CODES[field]}: required_no_authority_flags.{field} must be false")
    if registry.get("stage1_prediction_market_contexts") != ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"]:
        failures.append("registry.stage1_prediction_market_contexts must be KALSHI, POLYMARKET, FORECASTEX_IBKR")
    if registry.get("final_ready") is not False:
        failures.append("registry.final_ready must be false")
    return failures


def validate_pr85_gate(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any] | None]:
    failures: list[str] = []
    registry_path = repo_root / pr85_gate.DEFAULT_PRODUCTION_REGISTRY
    report_path = repo_root / pr85_gate.DEFAULT_REPORT
    registry, registry_failures = _load_yaml_checked(registry_path, "PR85_REGISTRY")
    report, report_failures = _load_json_checked(report_path, "PR85_REPORT")
    failures.extend(registry_failures)
    failures.extend(report_failures)
    if registry is None or report is None:
        return failures, None
    if registry.get("semantic_task_id") != pr85_gate.SEMANTIC_TASK_ID:
        failures.append("PR85 registry semantic_task_id mismatch")
    if registry.get("gate_scope") != pr85_gate.GATE_SCOPE:
        failures.append("PR85 registry gate_scope mismatch")
    if report.get("validation_marker") != pr85_gate.SUCCESS_MARKER:
        failures.append("PR85 report validation_marker mismatch")
    if report.get("ranked_candidate_descriptor_ids") != [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]:
        failures.append("PR85 report ranked_candidate_descriptor_ids mismatch")
    if report.get("future_pr86_optimizer_arbitration_implemented") is not False:
        failures.append("PR85 report must leave PR86 optimizer arbitration unimplemented")
    return failures, report


def _pr85_candidate_ids(pr85_report: dict[str, Any] | None) -> set[str]:
    if pr85_report is None:
        return set()
    ids: set[str] = set()
    for key in (
        "candidate_descriptor_ids",
        "ranked_candidate_descriptor_ids",
        "blocked_candidate_descriptor_ids",
    ):
        value = pr85_report.get(key)
        if isinstance(value, list):
            ids.update(str(item) for item in value)
    return ids


def _score_key(fixture: dict[str, Any], mode_policies: dict[str, dict[str, Any]]) -> tuple[Any, ...]:
    mode = str(fixture.get("arbitration_mode") or "")
    owner_mode = str(fixture.get("owner_quantum_priority_mode") or "")
    forced_rank = 0 if _owner_forced_mode(fixture) and _has_owner_or_failsafe_basis(fixture) else 1
    quantum_tie_rank = 0 if _is_quantum_mode(fixture) and _quantum_priority_permitted(owner_mode, mode_policies) else 1
    if _is_classical_mode(fixture) and not _quantum_priority_permitted(owner_mode, mode_policies):
        quantum_tie_rank = 0
    return (
        0 if fixture.get("valid_for_arbitration_flag") is True else 1,
        0 if fixture.get("arbitration_decision") != "BLOCK_ARBITRATION_FIXTURE" else 1,
        forced_rank,
        -Decimal(str(fixture.get("final_selection_score_fixture_metadata", 0))).quantize(SCORE_QUANT),
        -Decimal(str(fixture.get("base_score_fixture_metadata", 0))).quantize(SCORE_QUANT),
        quantum_tie_rank,
        Decimal(str(fixture.get("total_penalty_metadata", 0))).quantize(SCORE_QUANT),
        Decimal(str(fixture.get("uncertainty_metadata", 0))).quantize(SCORE_QUANT),
        str(fixture.get("arbitration_fixture_id") or ""),
        mode,
    )


def _validate_reason_code_list(value: Any, label: str, failures: list[str]) -> list[str]:
    if not isinstance(value, list):
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label} must be a list")
        return []
    codes = [str(code) for code in value]
    for code in codes:
        if code not in REASON_CODE_ORDER:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label} has unknown reason code {code}")
    if codes != _sort_reason_codes(codes):
        failures.append(f"{label} must use canonical deterministic reason-code order")
    return codes


def validate_arbitration_fixture(
    fixture: dict[str, Any],
    *,
    fixture_ids: set[str],
    pr82_labels: set[str],
    pr83_policy: dict[str, Any] | None,
    pr85_candidate_ids: set[str],
) -> list[str]:
    failures: list[str] = []
    fixture_id = str(fixture.get("arbitration_fixture_id") or "")
    label = f"fixture {fixture_id}"
    mode = str(fixture.get("arbitration_mode") or "")
    owner_mode = str(fixture.get("owner_quantum_priority_mode") or "")
    mode_policies = _mode_policy_map(pr83_policy)

    if mode not in ARBITRATION_MODE_ORDER:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_ARBITRATION_MODE: {label}.arbitration_mode {mode}")
    if fixture.get("arbitration_fixture_source") != "SYNTHETIC_STATIC_FIXTURE_ONLY":
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.arbitration_fixture_source must be SYNTHETIC_STATIC_FIXTURE_ONLY")
    if fixture.get("arbitration_fixture_authority") != "NON_RUNTIME_NON_LIVE_TEST_FIXTURE":
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.arbitration_fixture_authority must be NON_RUNTIME_NON_LIVE_TEST_FIXTURE")
    if fixture.get("arbitration_decision_authority") != "STATIC_FIXTURE_ONLY_NOT_SELECTION":
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.arbitration_decision_authority must be STATIC_FIXTURE_ONLY_NOT_SELECTION")
    if fixture.get("scoring_ranking_gate_source") != "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE":
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.scoring_ranking_gate_source must reference PR85")
    if fixture.get("score_breakdown_source") not in pr85_candidate_ids:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.score_breakdown_source must reference a PR85 candidate descriptor")
    candidate_ids = fixture.get("candidate_descriptor_fixture_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.candidate_descriptor_fixture_ids must be non-empty")
    else:
        unknown = [str(candidate_id) for candidate_id in candidate_ids if str(candidate_id) not in pr85_candidate_ids]
        if unknown:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.candidate_descriptor_fixture_ids unknown PR85 ids {', '.join(unknown)}")

    if owner_mode not in pr85_gate.pr84_gate.PR83_MODE_ORDER:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_OWNER_QUANTUM_PRIORITY_MODE: {label}.owner_quantum_priority_mode {owner_mode}")
    labels = fixture.get("quantum_applicability_labels")
    if not isinstance(labels, list) or not labels:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL: {label}.quantum_applicability_labels must be non-empty")
    else:
        unknown_labels = [str(item) for item in labels if str(item) not in pr82_labels]
        if unknown_labels:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL: {label} unknown labels {', '.join(unknown_labels)}")
        if _is_quantum_mode(fixture) and set(labels) == {"CLASSICAL_ONLY"}:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL: {label} quantum mode cannot be CLASSICAL_ONLY only")

    reason_codes = _validate_reason_code_list(fixture.get("arbitration_reason_codes"), f"{label}.arbitration_reason_codes", failures)
    blocked_codes = _validate_reason_code_list(fixture.get("blocked_reason_codes"), f"{label}.blocked_reason_codes", failures)
    valid = fixture.get("valid_for_arbitration_flag") is True
    decision = fixture.get("arbitration_decision")
    if decision not in ARBITRATION_DECISION_ORDER:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.arbitration_decision unknown")
    if valid:
        if decision != VALID_DECISION_BY_MODE.get(mode):
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.arbitration_decision must match mode")
        if blocked_codes:
            failures.append(f"{label}.blocked_reason_codes must be empty for valid fixtures")
    else:
        if decision != "BLOCK_ARBITRATION_FIXTURE":
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label} invalid fixtures must use BLOCK_ARBITRATION_FIXTURE")
        if not blocked_codes:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label} blocked fixtures must retain blocked_reason_codes")

    if "OPTIMIZER_ARBITRATION_ALLOWED_STATIC_FIXTURE_ONLY" not in reason_codes:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label} must include static fixture reason")

    if fixture.get("classical_comparator_required") is True and fixture.get("classical_comparator_present") is not True:
        if valid or "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR" not in blocked_codes:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR: {label} requires classical comparator")
    if mode in {"QUANTUM_CHALLENGER", "HYBRID_COMPARE_THEN_SELECT", "QUANTUM_FIRST", "OWNER_FORCED_QUANTUM"}:
        if fixture.get("classical_baseline_fixture_id") != "CLASSICAL_BASELINE_FIXTURE" and valid:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR: {label}.classical_baseline_fixture_id must reference CLASSICAL_BASELINE_FIXTURE")
    if mode == "HYBRID_COMPARE_THEN_SELECT":
        if fixture.get("classical_baseline_fixture_id") != "CLASSICAL_BASELINE_FIXTURE":
            if valid or "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR" not in blocked_codes:
                failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR: {label} hybrid mode requires classical baseline")
        challenger_id = fixture.get("quantum_challenger_fixture_id")
        if challenger_id not in fixture_ids:
            if valid or "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_QUANTUM_CHALLENGER" not in blocked_codes:
                failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_QUANTUM_CHALLENGER: {label} hybrid mode requires quantum challenger")
    if mode == "QUANTUM_FIRST":
        if owner_mode != "QUANTUM_FIRST" or not _quantum_priority_permitted(owner_mode, mode_policies):
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_PRIORITY_NOT_PERMITTED: {label} QUANTUM_FIRST must be PR83-permitted")
        if fixture.get("fallback_to_classical_available") is not True:
            failures.append(f"OPTIMIZER_ARBITRATION_ALLOWED_CLASSICAL_FALLBACK: {label}.fallback_to_classical_available must be true")
    if mode == "OWNER_FORCED_QUANTUM":
        if not _has_owner_or_failsafe_basis(fixture):
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS: {label} owner basis required")
        if pr83_policy is not None and pr83_policy.get("owner_can_force_quantum_selection") is not True:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_PRIORITY_NOT_PERMITTED: {label} PR83 owner force disabled")
        if owner_mode != "OWNER_FORCED_QUANTUM" or not _mode_enabled(owner_mode, mode_policies):
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_PRIORITY_NOT_PERMITTED: {label} owner-forced quantum mode not PR83-enabled")
        if fixture.get("owner_forced_quantum_applied") is not True:
            failures.append(f"OPTIMIZER_ARBITRATION_ALLOWED_OWNER_FORCED_QUANTUM_INTERNAL_ONLY: {label}.owner_forced_quantum_applied must be true")
    if mode == "OWNER_FORCED_CLASSICAL":
        if not _has_owner_or_failsafe_basis(fixture):
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS: {label} owner/fail-safe basis required")
        if fixture.get("owner_forced_classical_applied") is not True:
            failures.append(f"OPTIMIZER_ARBITRATION_ALLOWED_OWNER_FORCED_CLASSICAL_INTERNAL_ONLY: {label}.owner_forced_classical_applied must be true")
    if fixture.get("quantum_priority_applied") is True and not _quantum_priority_permitted(owner_mode, mode_policies):
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_PRIORITY_NOT_PERMITTED: {label}.quantum_priority_applied requires PR83 permission")
    if fixture.get("owner_override_internal_only_flag") is not True:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS: {label}.owner_override_internal_only_flag must be true")
    if fixture.get("owner_override_external_fact_fabrication_created") is not False:
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN: {label}.owner_override_external_fact_fabrication_created must be false")

    for field in ARBITRATION_FIXTURE_FALSE_FIELDS:
        if fixture.get(field) is not False:
            failures.append(f"{FIELD_REASON_CODES[field]}: {label}.{field} must be false")

    attempted_claims = fixture.get("attempted_forbidden_execution_claims", {})
    if not isinstance(attempted_claims, dict):
        failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: {label}.attempted_forbidden_execution_claims must be an object")
    else:
        for claim_field, reason_code in ATTEMPT_REASON_CODES.items():
            if attempted_claims.get(claim_field) is True:
                if valid or decision != "BLOCK_ARBITRATION_FIXTURE":
                    failures.append(f"{reason_code}: {label} attempted claim must be blocked")
                if reason_code not in blocked_codes:
                    failures.append(f"{reason_code}: {label}.blocked_reason_codes must include attempted claim block")

    for numeric_field in (
        "final_selection_score_fixture_metadata",
        "base_score_fixture_metadata",
        "total_penalty_metadata",
        "uncertainty_metadata",
    ):
        _decimal(fixture.get(numeric_field), f"{label}.{numeric_field}", failures)
    return failures


def validate_fixture(
    fixture: dict[str, Any],
    *,
    pr82_labels: set[str],
    pr83_policy: dict[str, Any] | None,
    pr85_report: dict[str, Any] | None,
) -> list[str]:
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
        "optimizer_arbitration_contract_only_flag",
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

    arbitration_fixtures = _list_of_mappings(fixture.get("optimizer_arbitration_fixtures"))
    fixture_ids = [str(item.get("arbitration_fixture_id") or "") for item in arbitration_fixtures]
    if fixture_ids != list(REQUIRED_ARBITRATION_FIXTURE_IDS):
        missing = [item for item in REQUIRED_ARBITRATION_FIXTURE_IDS if item not in fixture_ids]
        unknown = [item for item in fixture_ids if item not in REQUIRED_ARBITRATION_FIXTURE_IDS]
        if missing:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD: missing fixtures {', '.join(missing)}")
        if unknown:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_ARBITRATION_MODE: unknown fixtures {', '.join(unknown)}")
        failures.append("fixture.optimizer_arbitration_fixtures must use canonical deterministic fixture order")
    seen: set[str] = set()
    for fixture_id in fixture_ids:
        if fixture_id in seen:
            failures.append(f"OPTIMIZER_ARBITRATION_BLOCKED_DUPLICATE_ARBITRATION_FIXTURE: duplicate fixture {fixture_id}")
        seen.add(fixture_id)

    fixture_id_set = set(fixture_ids)
    pr85_candidate_ids = _pr85_candidate_ids(pr85_report)
    for arbitration_fixture in arbitration_fixtures:
        failures.extend(
            validate_arbitration_fixture(
                arbitration_fixture,
                fixture_ids=fixture_id_set,
                pr82_labels=pr82_labels,
                pr83_policy=pr83_policy,
                pr85_candidate_ids=pr85_candidate_ids,
            )
        )

    mode_policies = _mode_policy_map(pr83_policy)
    valid_fixtures = [
        item for item in arbitration_fixtures if item.get("valid_for_arbitration_flag") is True
    ]
    expected_order = sorted(valid_fixtures, key=lambda item: _score_key(item, mode_policies))
    expected_ids = [str(item.get("arbitration_fixture_id")) for item in expected_order]
    if expected_ids != list(EXPECTED_ORDERED_VALID_FIXTURE_IDS):
        failures.append(
            "OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS: fixture order must resolve to "
            f"{list(EXPECTED_ORDERED_VALID_FIXTURE_IDS)}"
        )
    for index, item in enumerate(expected_order, start=1):
        if item.get("arbitration_order") != index:
            failures.append(
                "OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS: "
                f"{item.get('arbitration_fixture_id')}.arbitration_order must be {index}"
            )
    if expected_ids[-2:] != [
        "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_A",
        "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_B",
    ]:
        failures.append("OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS: tiebreak stability fixtures must resolve lexicographically")
    return failures


def validate_filesystem_boundaries(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if (_resolve(repo_root, CANONICAL_BUNDLE_SHA256)).exists():
        failures.append(
            "OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN: "
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
        return [f"{MASTER_PLAN_CURRENT.as_posix()} has local diff; PR86 must not edit it"]
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


def _report_arbitration_fixture(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "arbitration_fixture_id": item.get("arbitration_fixture_id"),
        "arbitration_mode": item.get("arbitration_mode"),
        "arbitration_fixture_source": item.get("arbitration_fixture_source"),
        "arbitration_fixture_authority": item.get("arbitration_fixture_authority"),
        "arbitration_decision": item.get("arbitration_decision"),
        "arbitration_decision_authority": item.get("arbitration_decision_authority"),
        "arbitration_order": item.get("arbitration_order"),
        "valid_for_arbitration_flag": item.get("valid_for_arbitration_flag"),
        "classical_baseline_fixture_id": item.get("classical_baseline_fixture_id"),
        "quantum_challenger_fixture_id": item.get("quantum_challenger_fixture_id"),
        "hybrid_comparison_fixture_id": item.get("hybrid_comparison_fixture_id"),
        "owner_quantum_priority_mode": item.get("owner_quantum_priority_mode"),
        "owner_override_basis": item.get("owner_override_basis"),
        "score_breakdown_source": item.get("score_breakdown_source"),
        "candidate_descriptor_fixture_ids": list(item.get("candidate_descriptor_fixture_ids", [])),
        "arbitration_reason_codes": list(item.get("arbitration_reason_codes", [])),
        "blocked_reason_codes": list(item.get("blocked_reason_codes", [])),
        "classical_comparator_required": item.get("classical_comparator_required"),
        "classical_comparator_present": item.get("classical_comparator_present"),
        "quantum_challenger_allowed": item.get("quantum_challenger_allowed"),
        "quantum_priority_applied": item.get("quantum_priority_applied"),
        "owner_forced_quantum_applied": item.get("owner_forced_quantum_applied"),
        "owner_forced_classical_applied": item.get("owner_forced_classical_applied"),
        "fallback_to_classical_available": item.get("fallback_to_classical_available"),
        "no_trade_available_as_future_safety_placeholder": item.get("no_trade_available_as_future_safety_placeholder"),
        "final_selection_score_fixture_metadata": item.get("final_selection_score_fixture_metadata"),
        "base_score_fixture_metadata": item.get("base_score_fixture_metadata"),
        "total_penalty_metadata": item.get("total_penalty_metadata"),
        "uncertainty_metadata": item.get("uncertainty_metadata"),
        "selected_stack_created": False,
        "optimizer_execution_created": False,
        "backend_execution_created": False,
        "profit_evidence_created": False,
        "quantum_advantage_claim_created": False,
    }


def build_report(
    registry: dict[str, Any],
    fixture: dict[str, Any],
    pr82_labels: set[str],
    pr83_policy: dict[str, Any] | None,
    pr84_policy: dict[str, Any] | None,
    pr85_report: dict[str, Any] | None,
    repo_root: pathlib.Path,
) -> dict[str, Any]:
    arbitration_fixtures = _list_of_mappings(fixture.get("optimizer_arbitration_fixtures"))
    mode_policies = _mode_policy_map(pr83_policy)
    valid_fixtures = [item for item in arbitration_fixtures if item.get("valid_for_arbitration_flag") is True]
    blocked_fixtures = [item for item in arbitration_fixtures if item.get("valid_for_arbitration_flag") is not True]
    ordered_fixtures = sorted(valid_fixtures, key=lambda item: _score_key(item, mode_policies))
    blocked_sorted = sorted(blocked_fixtures, key=lambda item: str(item.get("arbitration_fixture_id") or ""))
    ordered_ids = [str(item.get("arbitration_fixture_id")) for item in ordered_fixtures]
    blocked_ids = [str(item.get("arbitration_fixture_id")) for item in blocked_sorted]
    report: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": POLICY_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "gate_registry_id": registry.get("gate_registry_id"),
        "optimizer_arbitration_gate_id": registry.get("optimizer_arbitration_gate_id"),
        "semantic_task_id": registry.get("semantic_task_id"),
        "gate_scope": registry.get("gate_scope"),
        "policy_version": POLICY_VERSION,
        "static_only_flag": True,
        "metadata_only_flag": True,
        "synthetic_fixture_only_flag": True,
        "optimizer_arbitration_contract_only_flag": True,
        "quantum_applicability_source": copy.deepcopy(registry.get("quantum_applicability_source")),
        "owner_quantum_priority_source": copy.deepcopy(registry.get("owner_quantum_priority_source")),
        "scoring_policy_source": copy.deepcopy(registry.get("scoring_policy_source")),
        "scoring_ranking_gate_source": copy.deepcopy(registry.get("scoring_ranking_gate_source")),
        "pr82_quantum_applicability_labels": _sort_by_order(pr82_labels, pr85_gate.pr84_gate.PR82_LABEL_ORDER),
        "pr83_supported_quantum_priority_modes": list(pr85_gate.pr84_gate.PR83_MODE_ORDER),
        "pr83_default_quantum_priority_mode": None if pr83_policy is None else pr83_policy.get("default_quantum_priority_mode"),
        "pr84_formula_ids": [] if pr84_policy is None else [item.get("formula_id") for item in _list_of_mappings(pr84_policy.get("formula_definitions"))],
        "pr85_ranked_candidate_descriptor_ids": [] if pr85_report is None else list(pr85_report.get("ranked_candidate_descriptor_ids", [])),
        "pr85_blocked_candidate_descriptor_ids": [] if pr85_report is None else list(pr85_report.get("blocked_candidate_descriptor_ids", [])),
        "arbitration_modes": list(ARBITRATION_MODE_ORDER),
        "arbitration_decisions": list(ARBITRATION_DECISION_ORDER),
        "arbitration_inputs": list(ARBITRATION_INPUT_ORDER),
        "arbitration_outputs": list(ARBITRATION_OUTPUT_ORDER),
        "arbitration_policy": copy.deepcopy(registry.get("arbitration_policy")),
        "tie_break_order": list(TIE_BREAK_ORDER),
        "stable_sort_required": True,
        "random_arbitration_allowed": False,
        "arbitration_fixture_count": len(arbitration_fixtures),
        "valid_arbitration_fixture_count": len(valid_fixtures),
        "blocked_arbitration_fixture_count": len(blocked_fixtures),
        "arbitration_fixture_ids": [str(item.get("arbitration_fixture_id")) for item in arbitration_fixtures],
        "arbitration_ordered_fixture_ids": ordered_ids,
        "static_arbitration_fixture_decision_ids": ordered_ids,
        "blocked_arbitration_fixture_ids": blocked_ids,
        "highest_priority_arbitration_fixture_id": ordered_ids[0] if ordered_ids else None,
        "static_arbitration_fixture_decisions": [_report_arbitration_fixture(item) for item in ordered_fixtures],
        "blocked_arbitration_fixtures": [_report_arbitration_fixture(item) for item in blocked_sorted],
        "upstream_dependency_ids": list(DEPENDENCY_ORDER),
        "future_consumer_ids": list(FUTURE_CONSUMER_ORDER),
        "reason_codes": list(REASON_CODE_ORDER),
        "blocked_reason_codes": list(BLOCK_REASON_CODES),
        "deterministic_arbitration_fixture_ordering": True,
        "deterministic_arbitration_decision_ordering": True,
        "deterministic_blocked_fixture_ordering": True,
        "deterministic_tie_break_output": True,
        "deterministic_upstream_dependency_ordering": True,
        "deterministic_future_consumer_ordering": True,
        "deterministic_reason_code_ordering": True,
        "classical_baseline_comparator_valid": True,
        "quantum_priority_owner_policy_gated": True,
        "owner_forced_quantum_internal_only": True,
        "owner_forced_classical_internal_or_failsafe_only": True,
        "no_selection_boundary": True,
        "no_optimizer_execution_boundary": True,
        "no_backend_execution_boundary": True,
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
    pr82_failures, pr82_labels = pr85_gate.pr84_gate.validate_pr82_registry(repo_root)
    failures.extend(pr82_failures)
    pr83_failures, pr83_policy = pr85_gate.pr84_gate.validate_pr83_policy(repo_root)
    failures.extend(pr83_failures)
    pr84_failures, pr84_policy = pr85_gate.validate_pr84_policy(repo_root)
    failures.extend(pr84_failures)
    pr85_failures, pr85_report = validate_pr85_gate(repo_root)
    failures.extend(pr85_failures)
    failures.extend(
        validate_fixture(
            fixture,
            pr82_labels=pr82_labels,
            pr83_policy=pr83_policy,
            pr85_report=pr85_report,
        )
    )
    failures.extend(validate_filesystem_boundaries(repo_root))
    failures.extend(validate_master_plan_diff(repo_root))
    failures.extend(validate_validator_static_surface(repo_root / pathlib.Path(__file__).relative_to(_REPO_ROOT)))

    report = build_report(
        registry,
        fixture,
        pr82_labels,
        pr83_policy,
        pr84_policy,
        pr85_report,
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
