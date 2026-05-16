#!/usr/bin/env python3
"""Generate the AtomicRows D2/E0 exact-row agent-family eligibility matrix.

The generated manifest is static metadata only. It reads the existing
exact-row JSONL source files and writes one deterministic coverage record per
source row. It does not write bundles, hashes, runtime artifacts, source
receipts, connector bindings, replay/paper outputs, optimizer outputs, quantum
outputs, scores, ranks, selections, or live/order artifacts.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import generate_atomicrows_exact_row_source_files as source_generator


REPO_ROOT = _REPO_ROOT
DEFAULT_MANIFEST = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsExactRowAgentFamilyEligibilityMatrix.yaml"
)
SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_GENERATED"

MANIFEST_ID = "ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX"
MANIFEST_VERSION = "v1"
REPAIR_PR_ID = "REPAIR_PR_D2_E0_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX"
AUTHORITY_CLASS = (
    "STATIC_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_AND_SCORING_RANKING_READINESS_ONLY"
)
OVERLAY_AUTHORITY_CLASS = (
    "STATIC_SCORING_RANKING_READINESS_ONLY_NOT_SCORING_EXECUTION_NOT_RANKING_EXECUTION_NOT_SELECTION"
)
REPORT_PATH = "docs/master_plan/generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json"

FUTURE_CONSUMER_PRS: tuple[str, ...] = (
    "PR_84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY",
    "PR_85_PARAMETER_STACK_SCORING_RANKING_GATE",
    "PR_86_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE",
    "PR_87_CANDIDATE_PARAMETER_STACK_GENERATION_GATE",
    "PR_88_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE",
    "PR_89_SELECTED_PARAMETER_STACK_HANDOFF_PACKET",
    "PR_90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE",
    "PR_91_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS",
    "PR_92_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS",
)

ALLOWED_AGENT_FAMILY_CLASSES: tuple[str, ...] = (
    "ALLOW_STATIC_READ",
    "ALLOW_STATIC_RESEARCH",
    "ALLOW_STATIC_VALIDATION",
    "ALLOW_STATIC_PLANNING",
    "ALLOW_STATIC_RISK_REVIEW",
    "ALLOW_STATIC_SELECTION_PREPARATION",
    "ALLOW_STATIC_SCORING_PREPARATION",
    "ALLOW_STATIC_REPLAY_PAPER_PREPARATION",
    "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    "ALLOW_STATIC_DASHBOARD_REPORTING",
    "ALLOW_STATIC_AGENT_GOVERNANCE_REVIEW",
    "ALLOW_QUANTUM_METADATA_REVIEW",
    "ALLOW_QUANTUM_ADVISORY_METADATA_ONLY",
    "ALLOW_QUBO_ISING_METADATA_ONLY",
    "ALLOW_QAOA_VQE_ANNEALING_METADATA_ONLY",
    "ALLOW_QUANTUM_PORTFOLIO_COMPARATOR_METADATA_ONLY",
)

BLOCKED_AUTHORITY_CLASSES: tuple[str, ...] = (
    "BLOCK_LIVE_ORDER_AUTHORITY",
    "BLOCK_FINAL_ORDER_SUBMISSION_AUTHORITY",
    "BLOCK_LIVE_TRADE_INTENT_AUTHORITY",
    "BLOCK_CONNECTOR_AUTHORITY",
    "BLOCK_SOURCE_FACT_AUTHORITY",
    "BLOCK_RUNTIME_CASH_AUTHORITY",
    "BLOCK_ORDER_FILL_ACCOUNT_RECEIPT_AUTHORITY",
    "BLOCK_QUANTUM_BACKEND_AUTHORITY",
    "BLOCK_QUANTUM_SIMULATOR_AUTHORITY",
    "BLOCK_QUANTUM_PROVIDER_AUTHORITY",
    "BLOCK_OPTIMIZER_EXECUTION",
    "BLOCK_SCORING_EXECUTION",
    "BLOCK_RANKING_EXECUTION",
    "BLOCK_SELECTION_EXECUTION",
    "BLOCK_CANDIDATE_STACK_GENERATION",
    "BLOCK_REPLAY_PAPER_EXECUTION",
    "BLOCK_BUNDLE_AUTHORITY",
    "BLOCK_SHA_FREEZE_AUTHORITY",
    "BLOCK_FINAL_READINESS_AUTHORITY",
    "BLOCK_PROFIT_OR_SUPERIORITY_CLAIM",
    "BLOCK_QUANTUM_ADVANTAGE_CLAIM",
)

FORBIDDEN_AUTHORITY_BOOL_FIELDS: tuple[str, ...] = (
    "live_order_authority_allowed",
    "final_order_submission_authority_allowed",
    "live_trade_intent_authority_allowed",
    "scoring_execution_allowed",
    "ranking_execution_allowed",
    "selection_execution_allowed",
    "candidate_stack_generation_allowed",
    "optimizer_execution_allowed",
    "replay_execution_allowed",
    "paper_execution_allowed",
    "source_fact_authority_allowed",
    "connector_authority_allowed",
    "runtime_cash_authority_allowed",
    "quantum_backend_authority_allowed",
    "quantum_simulator_authority_allowed",
    "quantum_provider_authority_allowed",
    "profit_evidence_allowed",
    "expected_profit_proof_allowed",
    "latency_superiority_evidence_allowed",
    "execution_superiority_evidence_allowed",
    "quantum_advantage_evidence_allowed",
    "bundle_authority_allowed",
    "sha_freeze_authority_allowed",
    "final_readiness_authority_allowed",
)

SCORING_READINESS_DECISIONS: tuple[str, ...] = (
    "SCORING_READY_STATIC_METADATA_ONLY",
    "SCORING_READY_PENDING_SOURCE_EVIDENCE",
    "SCORING_READY_PENDING_REPLAY_PAPER",
    "SCORING_READY_PENDING_OWNER_REVIEW",
    "SCORING_READY_PENDING_BUNDLE_MATERIALIZATION",
    "SCORING_BLOCKED_BY_ROW_AUTHORITY",
    "SCORING_BLOCKED_BY_SOURCE_DEPENDENCY",
    "SCORING_BLOCKED_BY_CONNECTOR_DEPENDENCY",
    "SCORING_BLOCKED_BY_RUNTIME_DEPENDENCY",
    "SCORING_BLOCKED_BY_QUANTUM_BACKEND_DEPENDENCY",
    "SCORING_BLOCKED_BY_LIVE_AUTHORITY_BOUNDARY",
    "SCORING_BLOCKED_BY_UNKNOWN_OR_UNSUPPORTED_ROW_CLASS",
)

FUTURE_SCORE_COMPONENT_INPUT_LABELS: tuple[str, ...] = (
    "AGENT_BINDING_SCORE_INPUT",
    "LIFECYCLE_STATUS_SCORE_INPUT",
    "OWNER_OVERRIDE_SCORE_INPUT",
    "PLATFORM_APPLICABILITY_SCORE_INPUT",
    "MARKET_TYPE_APPLICABILITY_SCORE_INPUT",
    "STRATEGY_FIT_SCORE_INPUT",
    "LATENCY_FIT_SCORE_INPUT",
    "RISK_FIT_SCORE_INPUT",
    "REPLAY_PAPER_SCORE_INPUT",
    "OPTIMIZER_SCORE_INPUT",
    "RUNTIME_READINESS_SCORE_INPUT",
    "QUANTUM_APPLICABILITY_SCORE_INPUT",
    "EXPECTED_NET_PROFIT_SCORE_INPUT",
    "DRAWDOWN_PENALTY_INPUT",
    "COMPLEXITY_PENALTY_INPUT",
    "SOURCE_CURRENTNESS_PENALTY_INPUT",
    "EXECUTION_COST_PENALTY_INPUT",
    "OWNER_PRIORITY_BOOST_INPUT",
    "QUANTUM_BOOST_INPUT",
    "FINAL_SELECTION_SCORE_INPUT",
)

FUTURE_STACK_ROLE_LABELS: tuple[str, ...] = (
    "SIGNAL_ROLE",
    "SCORING_ROLE",
    "NORMALIZATION_ROLE",
    "RISK_ROLE",
    "EXECUTION_BOUNDARY_ROLE",
    "CAPITAL_SIZING_ROLE",
    "LATENCY_ROUTING_ROLE",
    "ERROR_GUARD_ROLE",
    "AGENT_LIFECYCLE_BINDING_ROLE",
    "SOURCE_EVIDENCE_ROLE",
    "REPLAY_PAPER_VALIDATION_ROLE",
    "QUANTUM_ADVISORY_ROLE",
    "QUBO_ISING_METADATA_ROLE",
    "QAOA_VQE_ANNEALING_METADATA_ROLE",
    "QUANTUM_PORTFOLIO_COMPARATOR_ROLE",
)

FAMILY_ROLE: dict[str, str] = {
    "001_signal_features": "SIGNAL_ROLE",
    "002_scoring_ranking": "SCORING_ROLE",
    "003_normalization_calibration": "NORMALIZATION_ROLE",
    "004_risk_control": "RISK_ROLE",
    "005_execution_connector_boundary": "EXECUTION_BOUNDARY_ROLE",
    "006_capital_sizing_cash": "CAPITAL_SIZING_ROLE",
    "007_latency_routing": "LATENCY_ROUTING_ROLE",
    "008_error_guard_fail_closed": "ERROR_GUARD_ROLE",
    "009_lifecycle_agent_binding": "AGENT_LIFECYCLE_BINDING_ROLE",
    "010_source_evidence_connector_semantic": "SOURCE_EVIDENCE_ROLE",
    "011_replay_paper_validation": "REPLAY_PAPER_VALIDATION_ROLE",
    "012_quantum_advisory_optimization": "QUANTUM_ADVISORY_ROLE",
    "013_quantum_qubo_ising_metadata": "QUBO_ISING_METADATA_ROLE",
    "014_quantum_qaoa_vqe_annealing_metadata": "QAOA_VQE_ANNEALING_METADATA_ROLE",
    "015_quantum_portfolio_hybrid_comparator": "QUANTUM_PORTFOLIO_COMPARATOR_ROLE",
}

FAMILY_SCORE_LABELS: dict[str, tuple[str, ...]] = {
    "001_signal_features": (
        "PLATFORM_APPLICABILITY_SCORE_INPUT",
        "MARKET_TYPE_APPLICABILITY_SCORE_INPUT",
        "STRATEGY_FIT_SCORE_INPUT",
        "EXPECTED_NET_PROFIT_SCORE_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "002_scoring_ranking": FUTURE_SCORE_COMPONENT_INPUT_LABELS,
    "003_normalization_calibration": (
        "COMPLEXITY_PENALTY_INPUT",
        "SOURCE_CURRENTNESS_PENALTY_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "004_risk_control": (
        "RISK_FIT_SCORE_INPUT",
        "DRAWDOWN_PENALTY_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "005_execution_connector_boundary": (
        "LATENCY_FIT_SCORE_INPUT",
        "EXECUTION_COST_PENALTY_INPUT",
    ),
    "006_capital_sizing_cash": (
        "RISK_FIT_SCORE_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
        "DRAWDOWN_PENALTY_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "007_latency_routing": (
        "LATENCY_FIT_SCORE_INPUT",
        "EXECUTION_COST_PENALTY_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "008_error_guard_fail_closed": (
        "RISK_FIT_SCORE_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
        "DRAWDOWN_PENALTY_INPUT",
    ),
    "009_lifecycle_agent_binding": (
        "AGENT_BINDING_SCORE_INPUT",
        "LIFECYCLE_STATUS_SCORE_INPUT",
        "OWNER_OVERRIDE_SCORE_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
    ),
    "010_source_evidence_connector_semantic": (
        "SOURCE_CURRENTNESS_PENALTY_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
    ),
    "011_replay_paper_validation": (
        "REPLAY_PAPER_SCORE_INPUT",
        "RUNTIME_READINESS_SCORE_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "012_quantum_advisory_optimization": (
        "QUANTUM_APPLICABILITY_SCORE_INPUT",
        "QUANTUM_BOOST_INPUT",
        "OPTIMIZER_SCORE_INPUT",
        "OWNER_PRIORITY_BOOST_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
    "013_quantum_qubo_ising_metadata": (
        "QUANTUM_APPLICABILITY_SCORE_INPUT",
        "QUANTUM_BOOST_INPUT",
        "OPTIMIZER_SCORE_INPUT",
    ),
    "014_quantum_qaoa_vqe_annealing_metadata": (
        "QUANTUM_APPLICABILITY_SCORE_INPUT",
        "QUANTUM_BOOST_INPUT",
        "OPTIMIZER_SCORE_INPUT",
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        "QUANTUM_APPLICABILITY_SCORE_INPUT",
        "QUANTUM_BOOST_INPUT",
        "OPTIMIZER_SCORE_INPUT",
        "EXPECTED_NET_PROFIT_SCORE_INPUT",
        "EXECUTION_COST_PENALTY_INPUT",
        "RISK_FIT_SCORE_INPUT",
        "FINAL_SELECTION_SCORE_INPUT",
    ),
}

FAMILY_ALLOWED_CLASSES: dict[str, tuple[str, ...]] = {
    "001_signal_features": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_SELECTION_PREPARATION",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_STATIC_DASHBOARD_REPORTING",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "002_scoring_ranking": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_SELECTION_PREPARATION",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_STATIC_DASHBOARD_REPORTING",
    ),
    "003_normalization_calibration": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_SCORING_PREPARATION",
    ),
    "004_risk_control": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_RISK_REVIEW",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "005_execution_connector_boundary": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "006_capital_sizing_cash": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_RISK_REVIEW",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "007_latency_routing": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "008_error_guard_fail_closed": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_RISK_REVIEW",
        "ALLOW_STATIC_AGENT_GOVERNANCE_REVIEW",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
        "ALLOW_STATIC_DASHBOARD_REPORTING",
    ),
    "009_lifecycle_agent_binding": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_AGENT_GOVERNANCE_REVIEW",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
        "ALLOW_STATIC_DASHBOARD_REPORTING",
    ),
    "010_source_evidence_connector_semantic": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "011_replay_paper_validation": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_PLANNING",
        "ALLOW_STATIC_REPLAY_PAPER_PREPARATION",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "012_quantum_advisory_optimization": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_SELECTION_PREPARATION",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_QUANTUM_METADATA_REVIEW",
        "ALLOW_QUANTUM_ADVISORY_METADATA_ONLY",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "013_quantum_qubo_ising_metadata": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_QUANTUM_METADATA_REVIEW",
        "ALLOW_QUBO_ISING_METADATA_ONLY",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "014_quantum_qaoa_vqe_annealing_metadata": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_QUANTUM_METADATA_REVIEW",
        "ALLOW_QAOA_VQE_ANNEALING_METADATA_ONLY",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        "ALLOW_STATIC_READ",
        "ALLOW_STATIC_RESEARCH",
        "ALLOW_STATIC_VALIDATION",
        "ALLOW_STATIC_SELECTION_PREPARATION",
        "ALLOW_STATIC_SCORING_PREPARATION",
        "ALLOW_QUANTUM_METADATA_REVIEW",
        "ALLOW_QUANTUM_PORTFOLIO_COMPARATOR_METADATA_ONLY",
        "ALLOW_STATIC_OWNER_REVIEW_REQUEST",
    ),
}

FAMILY_SCORING_DECISION: dict[str, str] = {
    "001_signal_features": "SCORING_READY_PENDING_SOURCE_EVIDENCE",
    "002_scoring_ranking": "SCORING_READY_STATIC_METADATA_ONLY",
    "003_normalization_calibration": "SCORING_READY_STATIC_METADATA_ONLY",
    "004_risk_control": "SCORING_READY_STATIC_METADATA_ONLY",
    "005_execution_connector_boundary": "SCORING_BLOCKED_BY_CONNECTOR_DEPENDENCY",
    "006_capital_sizing_cash": "SCORING_BLOCKED_BY_RUNTIME_DEPENDENCY",
    "007_latency_routing": "SCORING_READY_STATIC_METADATA_ONLY",
    "008_error_guard_fail_closed": "SCORING_READY_STATIC_METADATA_ONLY",
    "009_lifecycle_agent_binding": "SCORING_READY_PENDING_OWNER_REVIEW",
    "010_source_evidence_connector_semantic": "SCORING_BLOCKED_BY_SOURCE_DEPENDENCY",
    "011_replay_paper_validation": "SCORING_READY_PENDING_REPLAY_PAPER",
    "012_quantum_advisory_optimization": "SCORING_READY_STATIC_METADATA_ONLY",
    "013_quantum_qubo_ising_metadata": "SCORING_READY_STATIC_METADATA_ONLY",
    "014_quantum_qaoa_vqe_annealing_metadata": "SCORING_READY_STATIC_METADATA_ONLY",
    "015_quantum_portfolio_hybrid_comparator": "SCORING_READY_STATIC_METADATA_ONLY",
}

FAMILY_REASON_CODES: dict[str, tuple[str, ...]] = {
    "001_signal_features": (
        "D2_E0_ALLOW_SIGNAL_STATIC_METADATA",
        "D2_E0_BLOCK_SIGNAL_TO_ORDER_AUTHORITY",
        "D2_E0_SOURCE_EVIDENCE_REQUIRED_BEFORE_FACT_AUTHORITY",
    ),
    "002_scoring_ranking": (
        "D2_E0_ALLOW_SCORING_RANKING_PREPARATION_ONLY",
        "D2_E0_BLOCK_SCORING_EXECUTION",
        "D2_E0_BLOCK_RANKING_EXECUTION",
    ),
    "003_normalization_calibration": (
        "D2_E0_ALLOW_NORMALIZATION_CALIBRATION_REVIEW",
        "D2_E0_BLOCK_RUNTIME_NORMALIZATION_EXECUTION",
    ),
    "004_risk_control": (
        "D2_E0_ALLOW_STATIC_RISK_REVIEW",
        "D2_E0_BLOCK_LIVE_RISK_RELEASE_AUTHORITY",
    ),
    "005_execution_connector_boundary": (
        "D2_E0_ALLOW_CONNECTOR_BOUNDARY_PLANNING_ONLY",
        "D2_E0_BLOCK_CONNECTOR_SEMANTIC_BINDING",
        "D2_E0_BLOCK_ORDER_ROUTING",
    ),
    "006_capital_sizing_cash": (
        "D2_E0_ALLOW_CAPITAL_POLICY_REVIEW_ONLY",
        "D2_E0_BLOCK_RUNTIME_CASH_RECEIPTS",
        "D2_E0_BLOCK_BALANCE_ACCOUNT_PRIVATE_STATE_SEMANTICS",
    ),
    "007_latency_routing": (
        "D2_E0_ALLOW_STATIC_LATENCY_ROUTING_ARCHITECTURE_REVIEW",
        "D2_E0_BLOCK_LATENCY_SUPERIORITY_EVIDENCE",
        "D2_E0_BLOCK_LIVE_ROUTER_AUTHORITY",
    ),
    "008_error_guard_fail_closed": (
        "D2_E0_ALLOW_FAIL_CLOSED_VALIDATION_REVIEW",
        "D2_E0_REINFORCE_DENY_BY_DEFAULT",
        "D2_E0_BLOCK_RUNTIME_KILL_SWITCH_AUTHORITY",
    ),
    "009_lifecycle_agent_binding": (
        "D2_E0_ALLOW_AGENT_GOVERNANCE_REVIEW_ONLY",
        "D2_E0_BLOCK_AGENT_SELF_APPROVAL",
        "D2_E0_BLOCK_LIVE_AGENT_AUTHORITY",
    ),
    "010_source_evidence_connector_semantic": (
        "D2_E0_ALLOW_SOURCE_EVIDENCE_WORKFLOW_READINESS_REVIEW",
        "D2_E0_BLOCK_ACCEPTED_SOURCE_FACTS",
        "D2_E0_BLOCK_CONNECTOR_SEMANTIC_VALUES",
    ),
    "011_replay_paper_validation": (
        "D2_E0_ALLOW_REPLAY_PAPER_PREPARATION_REVIEW",
        "D2_E0_BLOCK_REPLAY_EXECUTION",
        "D2_E0_BLOCK_PAPER_EXECUTION",
        "D2_E0_BLOCK_PROFIT_EVIDENCE",
    ),
    "012_quantum_advisory_optimization": (
        "D2_E0_ALLOW_QUANTUM_ADVISORY_METADATA_REVIEW",
        "D2_E0_BLOCK_OPTIMIZER_EXECUTION",
        "D2_E0_BLOCK_QUANTUM_BACKEND_EXECUTION",
        "D2_E0_BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    ),
    "013_quantum_qubo_ising_metadata": (
        "D2_E0_ALLOW_QUBO_ISING_METADATA_REVIEW",
        "D2_E0_BLOCK_QUBO_ISING_SOLVING",
        "D2_E0_BLOCK_QUANTUM_BACKEND_EXECUTION",
    ),
    "014_quantum_qaoa_vqe_annealing_metadata": (
        "D2_E0_ALLOW_QAOA_VQE_ANNEALING_METADATA_REVIEW",
        "D2_E0_BLOCK_QAOA_VQE_ANNEALING_EXECUTION",
        "D2_E0_BLOCK_QUANTUM_BACKEND_EXECUTION",
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        "D2_E0_ALLOW_QUANTUM_PORTFOLIO_COMPARATOR_METADATA_REVIEW",
        "D2_E0_BLOCK_PORTFOLIO_OPTIMIZER_EXECUTION",
        "D2_E0_BLOCK_PROFIT_AND_SUPERIORITY_CLAIMS",
    ),
}

REGISTRY_REFS: tuple[dict[str, str], ...] = (
    {
        "registry_id": "QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY",
        "registry_path": "docs/master_plan/agents/QTTAgentRoleOperatingCharterRegistry.yaml",
        "report_path": "docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json",
        "validator_path": "tools/validate_qtt_agent_role_operating_charter_registry.py",
    },
    {
        "registry_id": "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY",
        "registry_path": "docs/master_plan/algorithms/QTTAlgorithmFormulaFamilyRegistry.yaml",
        "report_path": "docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json",
        "validator_path": "tools/validate_qtt_algorithm_formula_family_registry.py",
    },
    {
        "registry_id": "QTT_AGENT_ALGORITHM_BINDING_REGISTRY",
        "registry_path": "docs/master_plan/agent_algorithm/QTTAgentAlgorithmBindingRegistry.yaml",
        "report_path": "docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json",
        "validator_path": "tools/validate_qtt_agent_algorithm_binding_registry.py",
    },
    {
        "registry_id": "QTT_AGENT_ALGORITHM_CONSUMER_GATE",
        "registry_path": "docs/master_plan/agent_algorithm/QTTAgentAlgorithmConsumerGate.yaml",
        "report_path": "docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json",
        "validator_path": "tools/validate_qtt_agent_algorithm_consumer_gate.py",
    },
    {
        "registry_id": "QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE",
        "registry_path": "docs/master_plan/agent_algorithm/QTTAgentAlgorithmCumulativeReadinessGate.yaml",
        "report_path": "docs/master_plan/generated/QTTAgentAlgorithmCumulativeReadinessGate.report.json",
        "validator_path": "tools/validate_qtt_agent_algorithm_cumulative_readiness_gate.py",
    },
    {
        "registry_id": "QTT_AGENT_ALGORITHM_COMMAND_MATRIX",
        "registry_path": "docs/master_plan/agent_algorithm/QTTAgentAlgorithmCommandMatrix.yaml",
        "report_path": "docs/master_plan/generated/QTTAgentAlgorithmCommandMatrix.json",
        "validator_path": "tools/validate_qtt_agent_algorithm_command_matrix.py",
    },
    {
        "registry_id": "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX",
        "registry_path": "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json",
        "validator_path": "tools/validate_atomicrows_parameter_agent_binding_command_matrix.py",
    },
    {
        "registry_id": "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsResearchProvenanceEvidenceTierClassification.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsResearchProvenanceEvidenceTierClassification.report.json",
        "validator_path": "tools/validate_atomicrows_research_provenance_evidence_tier_classification.py",
    },
    {
        "registry_id": "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsParameterStackRoleTaxonomy.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterStackRoleTaxonomy.report.json",
        "validator_path": "tools/validate_atomicrows_parameter_stack_role_taxonomy.py",
    },
    {
        "registry_id": "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsParameterStackCompletenessGate.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterStackCompletenessGate.report.json",
        "validator_path": "tools/validate_atomicrows_parameter_stack_completeness_gate.py",
    },
    {
        "registry_id": "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsParameterStackCompatibilityGate.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterStackCompatibilityGate.report.json",
        "validator_path": "tools/validate_atomicrows_parameter_stack_compatibility_gate.py",
    },
    {
        "registry_id": "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY",
        "registry_path": "docs/master_plan/quantum/QuantumApplicabilityClassificationRegistry.yaml",
        "report_path": "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json",
        "validator_path": "tools/validate_quantum_applicability_classification_registry.py",
    },
    {
        "registry_id": "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY",
        "registry_path": "docs/master_plan/quantum/OwnerQuantumPriorityPolicyRegistry.yaml",
        "report_path": "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json",
        "validator_path": "tools/validate_owner_quantum_priority_policy_registry.py",
    },
    {
        "registry_id": "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE",
        "registry_path": "docs/master_plan/governance/QTTOwnerOverrideReceiptAuthoringGate.yaml",
        "report_path": "docs/master_plan/generated/OwnerOverrideReceiptAuthoringGate.report.json",
        "validator_path": "tools/validate_owner_override_receipt_authoring_gate.py",
    },
)

EXTENSION_SLOT_IDS: tuple[str, ...] = (
    "future_agent_additions",
    "future_specialist_pod_additions",
    "future_row_additions",
    "future_parameter_additions",
    "future_algorithm_additions",
    "future_formula_additions",
    "future_scoring_feature_additions",
    "future_stack_role_additions",
    "future_trade_context_field_additions",
    "future_market_type_additions",
    "future_strategy_class_additions",
    "future_quantum_strategy_additions",
    "future_quantum_backend_research_additions",
    "future_quantum_provider_source_packet_additions",
    "future_research_agent_findings",
    "future_owner_findings",
    "future_owner_quantum_priority_updates",
    "future_owner_scoring_weight_updates",
    "future_owner_latency_priority_updates",
    "future_owner_expected_net_profit_priority_updates",
    "future_replay_paper_candidate_metadata",
    "future_optimizer_arbitration_metadata",
    "future_bundle_materialization_handoff",
    "future_dashboard_reporting_fields",
)


def _digest_source_line(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def _stable_identity(row: dict[str, Any]) -> str:
    return (
        f"{row['row_id']}::{row['row_index']}::{row['family_id']}::"
        f"{row['source_file_path']}"
    )


def _load_exact_source_rows(repo_root: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in source_generator.build_family_plans():
        path = repo_root / pathlib.Path(plan.exact_rows_file_path)
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            row["_source_record_digest"] = _digest_source_line(line)
            rows.append(row)
    return rows


def _unknown_trade_context_metadata(family_id: str) -> dict[str, str]:
    return {
        "platform_scope_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "venue_scope_metadata_only": "UNKNOWN_PENDING_SOURCE_EVIDENCE",
        "market_type_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "strategy_class_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "edge_type_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "latency_sensitivity_class_metadata_only": (
            "UNKNOWN_PENDING_REGISTRY"
            if family_id != "007_latency_routing"
            else "STATIC_LOW_LATENCY_ARCHITECTURE_REVIEW_ONLY"
        ),
        "capital_intensity_class_metadata_only": (
            "UNKNOWN_PENDING_REGISTRY"
            if family_id != "006_capital_sizing_cash"
            else "STATIC_CAPITAL_POLICY_REVIEW_ONLY"
        ),
        "risk_mode_metadata_only": (
            "UNKNOWN_PENDING_REGISTRY"
            if family_id != "004_risk_control"
            else "STATIC_RISK_POLICY_REVIEW_ONLY"
        ),
        "liquidity_context_metadata_only": "UNKNOWN_PENDING_SOURCE_EVIDENCE",
        "source_dependency_state_metadata_only": (
            "BLOCKED_BY_SOURCE_DEPENDENCY"
            if family_id in {"001_signal_features", "010_source_evidence_connector_semantic"}
            else "UNKNOWN_PENDING_SOURCE_EVIDENCE"
        ),
        "quantum_priority_mode_metadata_only": (
            "UNKNOWN_PENDING_OWNER_REVIEW"
            if family_id in source_generator.QUANTUM_FORWARD_FAMILY_IDS
            else "NOT_APPLICABLE_TO_ROW_FAMILY"
        ),
        "owner_override_basis_metadata_only": "UNKNOWN_PENDING_OWNER_REVIEW",
    }


def _source_currentness_dependency(family_id: str) -> str:
    if family_id in {"001_signal_features", "010_source_evidence_connector_semantic"}:
        return "BLOCKED_BY_SOURCE_DEPENDENCY"
    return "UNKNOWN_PENDING_SOURCE_EVIDENCE"


def _runtime_dependency(family_id: str) -> str:
    if family_id in {"005_execution_connector_boundary", "006_capital_sizing_cash"}:
        return "BLOCKED_BY_RUNTIME_DEPENDENCY"
    return "UNKNOWN_PENDING_REGISTRY"


def _replay_paper_dependency(family_id: str) -> str:
    if family_id == "011_replay_paper_validation":
        return "UNKNOWN_PENDING_REPLAY_PAPER"
    return "UNKNOWN_PENDING_REPLAY_PAPER"


def _quantum_applicability_class(row: dict[str, Any]) -> str:
    if row["family_id"] in source_generator.QUANTUM_FORWARD_FAMILY_IDS:
        return row["quantum_metadata"]["quantum_metadata_class"]
    return "NOT_APPLICABLE_TO_ROW_FAMILY"


def _blocked_stack_roles(eligible_role: str) -> list[dict[str, str]]:
    return [
        {
            "role_label": role,
            "block_reason_code": "BLOCKED_BY_DIFFERENT_EXACT_ROW_FAMILY_ROLE",
        }
        for role in FUTURE_STACK_ROLE_LABELS
        if role != eligible_role
    ]


def build_row_coverage_record(row: dict[str, Any]) -> dict[str, Any]:
    family_id = row["family_id"]
    eligible_score_components = list(FAMILY_SCORE_LABELS[family_id])
    eligible_stack_role = FAMILY_ROLE[family_id]
    record: dict[str, Any] = {
        "exact_row_id": row["row_id"],
        "row_index": row["row_index"],
        "family_id": family_id,
        "family_name": row["family_label"],
        "source_file": row["source_file_path"],
        "source_record_stable_identity": _stable_identity(row),
        "source_record_digest": row["_source_record_digest"],
        "source_row_class": row["row_class"],
        "source_subfamily_id": row["subfamily_id"],
        "source_agent_eligibility_placeholder": row["agent_eligibility"][
            "default_agent_eligibility_state"
        ],
        "source_quantum_metadata_class": row["quantum_metadata"]["quantum_metadata_class"],
        "agent_family_eligibility_decision": "ALLOW_STATIC_METADATA_ONLY_FAIL_CLOSED",
        "agent_family_eligibility_reason_codes": [
            "D2_E0_EXACT_ROW_COVERED",
            "D2_E0_DENY_BY_DEFAULT_EXECUTION_PRESERVED",
            *FAMILY_REASON_CODES[family_id],
        ],
        "allowed_agent_family_classes": list(FAMILY_ALLOWED_CLASSES[family_id]),
        "blocked_agent_family_classes": list(BLOCKED_AUTHORITY_CLASSES),
        "allowed_static_actions": list(FAMILY_ALLOWED_CLASSES[family_id]),
        "blocked_authority_classes": list(BLOCKED_AUTHORITY_CLASSES),
        "owner_override_applicability": "OWNER_INTERNAL_WORKFLOW_POLICY_METADATA_ONLY",
        "owner_override_limits": {
            "may_prioritize_future_review": True,
            "may_approve_future_extension_pr_direction": True,
            "cannot_fabricate_external_facts": True,
            "cannot_grant_live_order_authority": True,
            "cannot_grant_quantum_backend_authority": True,
            "cannot_bypass_source_or_runtime_receipts": True,
        },
        "future_extension_required_flag": True,
        "future_extension_reason_codes": [
            "FUTURE_VERSIONED_PR_REQUIRED_FOR_RUNTIME_OR_LIVE_USE",
            "FUTURE_SCHEMA_VALIDATOR_AND_TEST_UPDATE_REQUIRED",
        ],
        "scoring_readiness_decision": FAMILY_SCORING_DECISION[family_id],
        "scoring_readiness_reason_codes": [
            "D2_E0_SCORING_READINESS_METADATA_ONLY",
            "D2_E0_NO_COMPUTED_SCORE",
            "D2_E0_NO_RANKING_OR_SELECTION",
        ],
        "eligible_future_score_components": eligible_score_components,
        "blocked_future_score_components": [
            label
            for label in FUTURE_SCORE_COMPONENT_INPUT_LABELS
            if label not in eligible_score_components
        ],
        "eligible_future_stack_roles": [eligible_stack_role],
        "blocked_future_stack_roles": _blocked_stack_roles(eligible_stack_role),
        "trade_context_applicability_metadata": _unknown_trade_context_metadata(family_id),
        "platform_applicability_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "market_type_applicability_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "strategy_fit_metadata_only": "UNKNOWN_PENDING_REGISTRY",
        "latency_fit_metadata_only": (
            "STATIC_LOW_LATENCY_METADATA_ONLY"
            if family_id == "007_latency_routing"
            else "UNKNOWN_PENDING_REGISTRY"
        ),
        "risk_fit_metadata_only": (
            "STATIC_RISK_REVIEW_METADATA_ONLY"
            if family_id in {"004_risk_control", "006_capital_sizing_cash", "008_error_guard_fail_closed", "015_quantum_portfolio_hybrid_comparator"}
            else "UNKNOWN_PENDING_REGISTRY"
        ),
        "capital_fit_metadata_only": (
            "STATIC_CAPITAL_POLICY_METADATA_ONLY"
            if family_id == "006_capital_sizing_cash"
            else "UNKNOWN_PENDING_REGISTRY"
        ),
        "source_currentness_dependency_class": _source_currentness_dependency(family_id),
        "runtime_readiness_dependency_class": _runtime_dependency(family_id),
        "replay_paper_dependency_class": _replay_paper_dependency(family_id),
        "quantum_applicability_metadata_class": _quantum_applicability_class(row),
        "owner_priority_applicability_metadata_only": "UNKNOWN_PENDING_OWNER_REVIEW",
        "candidate_stack_generation_eligible_future_only": True,
        "ranking_contract_input_eligible_future_only": True,
        "selection_contract_input_eligible_future_only": True,
        "optimizer_arbitration_input_eligible_future_only": True,
        "replay_paper_competition_input_eligible_future_only": True,
        "dashboard_reporting_input_eligible_static_only": True,
        "owner_review_request_input_eligible_static_only": True,
    }
    for field in FORBIDDEN_AUTHORITY_BOOL_FIELDS:
        record[field] = False
    return record


def _family_distribution() -> list[dict[str, Any]]:
    distribution: list[dict[str, Any]] = []
    for plan in source_generator.build_family_plans():
        distribution.append(
            {
                "family_id": plan.family_id,
                "family_name": plan.family_label,
                "row_range_start": plan.start_row_index,
                "row_range_end": plan.end_row_index,
                "expected_row_count": plan.row_count,
                "source_file": plan.exact_rows_file_path,
                "quantum_forward_family": plan.quantum_forward_family_flag,
                "agent_governance_family": plan.agent_governance_family_flag,
            }
        )
    return distribution


def _family_policy(plan: source_generator.FamilyPlan) -> dict[str, Any]:
    return {
        "family_id": plan.family_id,
        "family_name": plan.family_label,
        "row_range_start": plan.start_row_index,
        "row_range_end": plan.end_row_index,
        "expected_row_count": plan.row_count,
        "row_class_scope": list(source_generator.ROW_CLASSES_BY_FAMILY[plan.family_id]),
        "allowed_static_eligibility_classes": list(FAMILY_ALLOWED_CLASSES[plan.family_id]),
        "required_block_classes": list(BLOCKED_AUTHORITY_CLASSES),
        "agent_family_allow_rules": [
            "ALLOW_ONLY_STATIC_METADATA_ACTIONS",
            "ALLOW_NO_RUNTIME_OR_LIVE_AGENT_AUTHORITY",
        ],
        "agent_family_block_rules": list(BLOCKED_AUTHORITY_CLASSES),
        "scoring_readiness_policy": {
            "decision": FAMILY_SCORING_DECISION[plan.family_id],
            "metadata_only": True,
            "computed_scores_allowed": False,
            "ranking_execution_allowed": False,
            "selection_execution_allowed": False,
        },
        "future_score_component_input_policy": {
            "eligible_labels": list(FAMILY_SCORE_LABELS[plan.family_id]),
            "labels_are_future_input_eligibility_only": True,
            "numeric_scores_created": False,
        },
        "future_stack_role_policy": {
            "eligible_role": FAMILY_ROLE[plan.family_id],
            "single_row_trade_stack_blocked": True,
            "single_parameter_trade_stack_blocked": True,
            "single_algorithm_trade_stack_blocked": True,
            "role_complete_multi_row_stack_preparation_allowed_future_metadata_only": True,
        },
        "trade_context_readiness_policy": {
            "metadata_only": True,
            "unknown_values_fail_closed": True,
            "selection_execution_allowed": False,
        },
        "low_latency_readiness_policy": {
            "static_precomputed_metadata_only": True,
            "live_hot_path_implemented": False,
            "live_path_source_retrieval_allowed": False,
            "live_path_quantum_backend_call_allowed": False,
            "live_path_llm_call_allowed": False,
        },
        "expected_net_profit_readiness_policy": {
            "future_input_label_allowed_when_listed": "EXPECTED_NET_PROFIT_SCORE_INPUT"
            in FAMILY_SCORE_LABELS[plan.family_id],
            "profit_evidence_created": False,
            "numeric_expected_profit_created": False,
        },
        "source_connector_policy": {
            "source_fact_authority_allowed": False,
            "connector_semantic_authority_allowed": False,
            "source_retrieval_execution_allowed": False,
            "source_acceptance_execution_allowed": False,
        },
        "runtime_live_policy": {
            "runtime_authority_allowed": False,
            "live_order_authority_allowed": False,
            "final_order_submission_authority_allowed": False,
            "live_trade_intent_authority_allowed": False,
        },
        "quantum_metadata_policy": {
            "quantum_metadata_only": plan.quantum_forward_family_flag,
            "quantum_backend_authority_allowed": False,
            "quantum_simulator_authority_allowed": False,
            "quantum_provider_authority_allowed": False,
            "quantum_advantage_claim_allowed": False,
        },
        "owner_override_policy": {
            "owner_internal_workflow_policy_allowed": True,
            "owner_override_cannot_fabricate_external_facts": True,
            "owner_override_cannot_grant_live_or_backend_authority": True,
        },
        "extension_policy": {
            "future_versioned_pr_required": True,
            "manifest_schema_validator_tests_required": True,
            "live_backend_connector_profit_authority_default": False,
        },
        "reason_codes": list(FAMILY_REASON_CODES[plan.family_id]),
    }


def _overlay() -> dict[str, Any]:
    return {
        "overlay_id": "ATOMICROWS_D2_E0_ALL_ROW_SCORING_RANKING_READINESS_OVERLAY",
        "overlay_version": "v1",
        "authority_class": OVERLAY_AUTHORITY_CLASS,
        "source_exact_row_count": source_generator.EXPECTED_TOTAL_ROWS,
        "coverage_required": True,
        "future_consumer_prs": list(FUTURE_CONSUMER_PRS),
        "scoring_feature_definitions": [
            {
                "input_label": label,
                "label_kind": "FUTURE_INPUT_ELIGIBILITY_ONLY",
                "computed_value_created_by_d2_e0": False,
                "numeric_value_created_by_d2_e0": False,
            }
            for label in FUTURE_SCORE_COMPONENT_INPUT_LABELS
        ],
        "future_score_component_input_labels": list(FUTURE_SCORE_COMPONENT_INPUT_LABELS),
        "future_stack_role_input_labels": list(FUTURE_STACK_ROLE_LABELS),
        "row_scoring_readiness_contract": {
            "one_decision_per_exact_row_required": True,
            "allowed_decisions": list(SCORING_READINESS_DECISIONS),
            "future_input_labels_are_not_scores": True,
            "computed_scores_allowed": False,
            "ranking_allowed": False,
            "selection_allowed": False,
        },
        "family_scoring_readiness_policies": [
            {
                "family_id": plan.family_id,
                "scoring_readiness_decision": FAMILY_SCORING_DECISION[plan.family_id],
                "eligible_future_score_components": list(FAMILY_SCORE_LABELS[plan.family_id]),
                "eligible_future_stack_role": FAMILY_ROLE[plan.family_id],
                "metadata_only": True,
            }
            for plan in source_generator.build_family_plans()
        ],
        "trade_context_selection_readiness_policy": {
            "future_trade_order_specific_selection_preparation_only": True,
            "selection_execution_allowed": False,
            "single_row_trade_stack_blocked": True,
            "single_parameter_trade_stack_blocked": True,
            "single_algorithm_trade_stack_blocked": True,
            "role_complete_multi_row_stack_preparation_allowed_future_metadata_only": True,
            "missing_required_stack_role_blocks_future_replay_paper_and_live_path": True,
            "atomicrows_is_inventory_and_authority_ledger_not_trader": True,
        },
        "low_latency_readiness_policy": {
            "static_precomputed_metadata_only": True,
            "live_path_source_retrieval_allowed": False,
            "live_path_quantum_backend_call_allowed": False,
            "live_path_llm_call_allowed": False,
            "live_path_replay_paper_call_allowed": False,
            "live_path_optimizer_execution_allowed": False,
            "live_path_schema_discovery_allowed": False,
            "runtime_file_mutation_allowed": False,
            "future_hot_path_consumes_prevalidated_manifests_and_reports_only": True,
        },
        "expected_net_profit_readiness_policy": {
            "future_expected_net_profit_input_eligibility_allowed": True,
            "profit_evidence_created": False,
            "numeric_expected_profit_created": False,
            "cost_adjusted_net_profit_result_created": False,
        },
        "risk_drawdown_readiness_policy": {
            "future_risk_and_drawdown_input_eligibility_allowed": True,
            "runtime_risk_release_authority_created": False,
            "live_order_release_authority_created": False,
        },
        "source_currentness_readiness_policy": {
            "future_source_currentness_input_eligibility_allowed": True,
            "source_retrieval_execution_allowed": False,
            "source_acceptance_execution_allowed": False,
            "accepted_source_fact_authority_allowed": False,
        },
        "execution_cost_readiness_policy": {
            "future_execution_cost_input_eligibility_allowed": True,
            "connector_semantic_binding_allowed": False,
            "order_routing_allowed": False,
            "execution_superiority_claim_allowed": False,
        },
        "quantum_scoring_readiness_policy": {
            "quantum_forward_families": sorted(source_generator.QUANTUM_FORWARD_FAMILY_IDS),
            "metadata_only": True,
            "classical_comparator_and_fallback_required_for_future": True,
            "future_owner_approved_true_quantum_extension_slots_supported": True,
            "quantum_backend_authority_allowed": False,
            "quantum_simulator_authority_allowed": False,
            "quantum_provider_authority_allowed": False,
            "quantum_advantage_claim_allowed": False,
        },
        "owner_priority_readiness_policy": {
            "owner_internal_priority_metadata_allowed": True,
            "owner_override_may_prioritize_future_review": True,
            "owner_override_cannot_fabricate_external_or_runtime_evidence": True,
            "owner_override_cannot_grant_live_order_or_quantum_backend_authority": True,
        },
        "optimizer_arbitration_readiness_policy": {
            "future_optimizer_arbitration_input_eligibility_allowed": True,
            "optimizer_execution_allowed": False,
            "optimizer_output_created": False,
        },
        "replay_paper_competition_readiness_policy": {
            "future_replay_paper_competition_input_eligibility_allowed": True,
            "replay_execution_allowed": False,
            "paper_execution_allowed": False,
            "replay_or_paper_result_created": False,
        },
        "forbidden_execution_claims": [
            "FORBID_SCORING_EXECUTION",
            "FORBID_RANKING_EXECUTION",
            "FORBID_SELECTION_EXECUTION",
            "FORBID_CANDIDATE_STACK_GENERATION",
            "FORBID_OPTIMIZER_OUTPUT",
            "FORBID_REPLAY_PAPER_RESULT",
            "FORBID_PROFIT_OR_SUPERIORITY_EVIDENCE",
            "FORBID_QUANTUM_ADVANTAGE_CLAIM",
        ],
        "validator_contract": {
            "validator_path": "tools/validate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
            "schema_path": "schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_matrix.schema.json",
            "record_schema_path": "schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_record.schema.json",
            "success_marker": "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_OK",
        },
        "future_handoff": {
            "status": "STATIC_METADATA_ONLY_READY_FOR_FUTURE_SCORING_POLICY_AND_RANKING_GATES",
            "future_pr84_handoff_ready": True,
            "future_pr85_handoff_ready": True,
            "future_pr86_handoff_ready": True,
            "future_pr87_handoff_ready": True,
            "future_pr88_handoff_ready": True,
            "future_pr89_handoff_ready": True,
            "future_pr90_plus_handoff_ready": True,
        },
    }


def _extension_slot(slot_id: str) -> dict[str, Any]:
    return {
        "slot_id": slot_id,
        "future_versioned_pr_required": True,
        "manifest_update_required": True,
        "schema_update_required_if_fields_change": True,
        "validator_update_required": True,
        "generated_report_update_required": True,
        "tests_required": True,
        "validation_gate_update_required_when_applicable": True,
        "explicit_owner_approval_required_if_workflow_authority_changes": True,
        "accepted_source_packets_required_if_external_facts_change": True,
        "replay_paper_receipts_required_if_validation_results_claimed": True,
        "no_live_authority_by_default": True,
        "no_backend_authority_by_default": True,
        "no_connector_authority_by_default": True,
        "no_profit_evidence_by_default": True,
    }


def build_manifest(repo_root: pathlib.Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    rows = _load_exact_source_rows(repo_root)
    row_coverage_records = [build_row_coverage_record(row) for row in rows]
    return {
        "manifest_id": MANIFEST_ID,
        "manifest_version": MANIFEST_VERSION,
        "repair_pr_id": REPAIR_PR_ID,
        "authority_class": AUTHORITY_CLASS,
        "created_for": "REPAIR_PR_D2_E0_STATIC_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_AND_SCORING_RANKING_READINESS",
        "source_materialization_manifest_ref": "docs/master_plan/atomicrows/AtomicRowsExactRowSourceMaterializationManifest.yaml",
        "source_exact_row_directory": source_generator.EXACT_ROW_SOURCES_DIR.as_posix() + "/",
        "expected_source_family_file_count": source_generator.EXPECTED_FAMILY_COUNT,
        "expected_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "expected_family_distribution": _family_distribution(),
        "policy_summary": {
            "d2_e0_is_exact_row_coverage_policy": True,
            "d2_e0_is_agent_family_eligibility_metadata": True,
            "d2_e0_is_scoring_ranking_readiness_metadata": True,
            "d2_e0_is_future_stack_selection_preparation_metadata": True,
            "d2_e0_is_future_quantum_advisory_preparation_metadata": True,
            "d2_e0_executes_scoring_ranking_selection_optimizer_replay_paper_live": False,
            "d2_e0_creates_bundle_sha_freeze_final_readiness": False,
        },
        "eligibility_class_definitions": [
            {
                "eligibility_class": value,
                "metadata_only": True,
                "runtime_or_live_authority_created": False,
            }
            for value in ALLOWED_AGENT_FAMILY_CLASSES
        ],
        "forbidden_authority_classes": list(BLOCKED_AUTHORITY_CLASSES),
        "scoring_ranking_readiness_overlay": _overlay(),
        "agent_family_registry_refs": [REGISTRY_REFS[0]],
        "agent_algorithm_registry_refs": list(REGISTRY_REFS[1:6]),
        "atomicrows_parameter_agent_binding_refs": [REGISTRY_REFS[6]],
        "owner_governance_refs": [
            REGISTRY_REFS[12],
            REGISTRY_REFS[13],
            {
                "registry_id": "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY",
                "registry_path": "docs/master_plan/governance/QTTOwnerGlobalOverrideAuthority.yaml",
                "report_path": "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json",
                "validator_path": "tools/validate_qtt_owner_global_override_authority.py",
            },
        ],
        "family_policies": [
            _family_policy(plan) for plan in source_generator.build_family_plans()
        ],
        "row_coverage_strategy": {
            "strategy": "EXPLICIT_GENERATED_PER_ROW_RECORDS_IN_MANIFEST",
            "generator_path": "tools/generate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
            "source_digest_algorithm": "SHA256_OF_EXACT_JSONL_LINE_UTF8",
            "ordering": "FAMILY_ID_THEN_ROW_INDEX_ASCENDING",
            "coverage_records_expected": source_generator.EXPECTED_TOTAL_ROWS,
            "scoring_readiness_records_expected": source_generator.EXPECTED_TOTAL_ROWS,
        },
        "row_coverage_records": row_coverage_records,
        "extension_slots": {
            slot_id: _extension_slot(slot_id) for slot_id in EXTENSION_SLOT_IDS
        },
        "validation_contract": {
            "validator_path": "tools/validate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
            "schema_path": "schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_matrix.schema.json",
            "record_schema_path": "schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_record.schema.json",
            "report_path": REPORT_PATH,
            "success_marker": "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_OK",
            "forbidden_artifacts": [
                source_generator.FUTURE_BUNDLE_PATH.as_posix(),
                source_generator.FUTURE_BUNDLE_SHA_PATH.as_posix(),
            ],
        },
        "no_claim_boundary": {
            "trading_ready_claim_allowed": False,
            "live_ready_claim_allowed": False,
            "profit_ready_claim_allowed": False,
            "profit_evidence_allowed": False,
            "latency_superiority_evidence_allowed": False,
            "execution_superiority_evidence_allowed": False,
            "quantum_advantage_evidence_allowed": False,
            "final_readiness_authority_allowed": False,
        },
        "future_pr_handoff": {
            "repair_pr_e_bundle_materialization_future_only": True,
            "future_bundle_materialization_executed_by_d2_e0": False,
            "future_sha_freeze_executed_by_d2_e0": False,
            "future_final_readiness_executed_by_d2_e0": False,
            "future_consumer_prs": list(FUTURE_CONSUMER_PRS),
        },
        "generated_report_path": REPORT_PATH,
    }


def render_manifest(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, sort_keys=False) + "\n"


def _normalize_generated_newlines(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def _existing_newline(raw: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in raw else b"\n"


def _apply_newline_style(raw_lf: bytes, newline: bytes) -> bytes:
    if newline == b"\n":
        return raw_lf
    return raw_lf.replace(b"\n", newline)


def write_manifest(
    repo_root: pathlib.Path = REPO_ROOT,
    manifest_path: pathlib.Path = DEFAULT_MANIFEST,
) -> pathlib.Path:
    repo_root = repo_root.resolve()
    manifest = build_manifest(repo_root)
    path = repo_root / manifest_path
    path.parent.mkdir(parents=True, exist_ok=True)
    desired_lf = render_manifest(manifest).encode("utf-8")
    newline = b"\n"
    if path.exists():
        current = path.read_bytes()
        if _normalize_generated_newlines(current) == desired_lf:
            return path
        newline = _existing_newline(current)
    path.write_bytes(_apply_newline_style(desired_lf, newline))
    return path


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        print("generate_atomicrows_exact_row_agent_family_eligibility_matrix.py does not accept arguments", file=sys.stderr)
        return 2
    write_manifest(REPO_ROOT, DEFAULT_MANIFEST)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
