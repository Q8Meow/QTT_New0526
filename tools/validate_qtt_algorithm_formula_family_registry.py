#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Sequence

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
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "algorithms"
    / "qtt_algorithm_formula_family_registry.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "algorithms"
    / "QTTAlgorithmFormulaFamilyRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "algorithms"
    / "synthetic_qtt_algorithm_formula_family_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAlgorithmFormulaFamilyReport.json"
)
AGENT_CHARTER_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "agents"
    / "QTTAgentRoleOperatingCharterRegistry.yaml"
)
MASTER_PLAN = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REGISTRY_TYPE = "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY"
REGISTRY_VERSION = "v1"
REPORT_TYPE = "QTT_ALGORITHM_FORMULA_FAMILY_REPORT"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
ARCHITECTURE_EMPHASIS = (
    "INSTITUTIONAL_ALGORITHM_FORMULA_FAMILY_REGISTRY_NOT_FLAT_ENUM"
)
OWNER_OVERRIDE_SATISFACTION_BASIS = (
    "OWNER_GLOBAL_OVERRIDE_SATISFIES_QTT_INTERNAL_WORKFLOW_REQUIREMENTS"
)
FORMULA_DEFAULT_POLICY = (
    "ADOPT_MASTER_PLAN_OR_SOURCE_EVIDENCE_DEFAULTS_ONLY_NO_GUESSWORK"
)
FORMULA_VALUE_RANGE_POLICY = (
    "NO_NUMERIC_RANGE_UNLESS_MASTER_PLAN_OR_ACCEPTED_SOURCE_EVIDENCE_OR_OWNER_APPROVED_CANONICAL_PACKET"
)
STATIC_FORWARD_REFERENCE_ONLY = "STATIC_FORWARD_REFERENCE_ONLY"
FINAL_STATUS = (
    "STATIC_ALGORITHM_FORMULA_FAMILY_DECLARED_NOT_FINAL_PRODUCTION_READY_OWNER_OVERRIDE_SUPPORTED"
)
SUCCESS_MARKER = "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_OK"
FAILURE_MARKER = "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_FAILED"
FINAL_INCOMPLETE_MARKER = "QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_FINAL_INCOMPLETE"

TOP_FIELDS = (
    "registry_type",
    "registry_version",
    "deterministic_output",
    "generated_at_utc",
    "source_of_family_substance",
    "agent_charter_registry_dependency",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr65_is_scope_boundary_not_algorithm_authority",
    "architecture_emphasis",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "agent_algorithm_binding_created",
    "agent_algorithm_consumer_gate_created",
    "final_ready",
    "algorithm_families",
)

FIXTURE_EXTRA_FIELDS = (
    "execution",
    "mode",
)

FAMILY_FIELDS = (
    "algorithm_family_id",
    "algorithm_family_name",
    "algorithm_family_description",
    "family_category",
    "classical_or_quantum",
    "formula_class",
    "formula_expression_profile",
    "formula_authority_class",
    "formula_default_policy",
    "formula_value_range_policy",
    "input_parameter_families",
    "output_signal_type",
    "output_artifact_types",
    "authorized_agent_roles",
    "authorized_consumer_classes",
    "trade_context_applicability",
    "latency_class",
    "risk_class",
    "capital_class",
    "market_context_scope",
    "platform_scope",
    "optimizer_compatibility",
    "quantum_applicability",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
    "deterministic_selection_role",
    "scoring_ranking_role",
    "quantum_classical_arbitration_role",
    "strongest_classical_comparator_required",
    "fallback_bundle_required",
    "replay_paper_evidence_required_before_advantage_claim",
    "live_evidence_required_before_profit_claim",
    "runtime_live_order_authority_created",
    "direct_order_submission_allowed",
    "execution_router_required_for_live_order_path",
    "owner_override_supported",
    "owner_override_satisfaction_basis",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority",
    "agent_binding_required_before_consumption",
    "consumer_gate_required_before_consumption",
    "source_evidence_requirement_class",
    "connector_requirement_class",
    "runtime_resolver_requirement_class",
    "replay_paper_requirement_class",
    "risk_gate_requirement_class",
    "sizing_gate_requirement_class",
    "latency_gate_requirement_class",
    "validation_gate_requirement_class",
    "master_plan_doctrine_terms_used",
    "master_plan_family_derivation_summary",
    "agent_charter_roles_validated",
    "final_qtt_internal_status",
)

ARRAY_FIELDS = {
    "input_parameter_families",
    "output_artifact_types",
    "authorized_agent_roles",
    "authorized_consumer_classes",
    "trade_context_applicability",
    "market_context_scope",
    "platform_scope",
    "optimizer_compatibility",
    "quantum_applicability",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
    "master_plan_doctrine_terms_used",
    "agent_charter_roles_validated",
}

FAMILY_ORDER = (
    "CLASSICAL_SIGNAL_ALGORITHM",
    "CLASSICAL_SCORING_ALGORITHM",
    "CLASSICAL_RISK_ALGORITHM",
    "CLASSICAL_SIZING_ALGORITHM",
    "CLASSICAL_EXECUTION_ALGORITHM",
    "CLASSICAL_LATENCY_ALGORITHM",
    "QUANTUM_INSPIRED_OPTIMIZER",
    "TRUE_QUANTUM_OPTIMIZER",
    "HYBRID_CLASSICAL_QUANTUM_OPTIMIZER",
    "QUBO_COMPATIBLE_ALGORITHM",
    "ISING_COMPATIBLE_ALGORITHM",
    "QAOA_COMPATIBLE_ALGORITHM",
    "VQE_COMPATIBLE_ALGORITHM",
    "ANNEALING_COMPATIBLE_ALGORITHM",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_ALGORITHM",
)

FAMILY_IDS = {
    name: f"QTT_ALGORITHM_FAMILY_{index:03d}_{name}"
    for index, name in enumerate(FAMILY_ORDER, start=1)
}

CLASSICAL_FAMILY_NAMES = FAMILY_ORDER[:6]
QUANTUM_OR_COMPATIBLE_FAMILY_NAMES = FAMILY_ORDER[6:]

AGENT_ROLE_ORDER = (
    "OWNER",
    "ORCHESTRATOR_AGENT",
    "MASTER_PLAN_AGENT",
    "ATOMICROWS_AGENT",
    "ATOMICROWS_RESEARCH_AGENT",
    "ATOMICROWS_LIFECYCLE_AGENT",
    "SOURCE_EVIDENCE_AGENT",
    "CONNECTOR_AGENT",
    "RUNTIME_RESOLVER_AGENT",
    "REPLAY_AGENT",
    "PAPER_AGENT",
    "DUAL_RESULT_REVIEW_AGENT",
    "OPTIMIZER_AGENT",
    "RISK_AGENT",
    "SIZING_AGENT",
    "EXECUTION_LATENCY_AGENT",
    "ORDER_ROUTER_AGENT",
    "LIVE_CANARY_AGENT",
    "QUANTUM_RESEARCH_AGENT",
    "QUANTUM_BACKEND_AGENT",
    "DASHBOARD_AGENT",
    "GOVERNANCE_AGENT",
    "VALIDATION_AGENT",
    "COMPLIANCE_MARKER_AGENT",
    "OWNER_APPROVAL_REQUEST_AGENT",
)

FORMULA_AUTHORITY_CLASSES = (
    "MASTER_PLAN_STATIC_DOCTRINE",
    "OWNER_POLICY_STATIC_DOCTRINE",
    "SOURCE_EVIDENCE_REQUIRED_FOR_NUMERIC_VALUES",
    "PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
    "STATIC_FORWARD_REFERENCE_ONLY",
)

FORMULA_EXPRESSION_PROFILES = (
    "SYMBOLIC_SIGNAL_TRANSFORMATION",
    "SYMBOLIC_SCORING_FUNCTION",
    "SYMBOLIC_RISK_CONSTRAINT_FUNCTION",
    "SYMBOLIC_SIZING_POLICY_FUNCTION",
    "SYMBOLIC_EXECUTION_POLICY_FUNCTION",
    "SYMBOLIC_LATENCY_COST_FUNCTION",
    "SYMBOLIC_QUBO_OBJECTIVE",
    "SYMBOLIC_ISING_HAMILTONIAN",
    "SYMBOLIC_QAOA_OBJECTIVE",
    "SYMBOLIC_VQE_OBJECTIVE",
    "SYMBOLIC_ANNEALING_ENERGY_OBJECTIVE",
    "SYMBOLIC_QUANTUM_PORTFOLIO_OBJECTIVE",
    "SYMBOLIC_HYBRID_ARBITRATION_FUNCTION",
)

REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "source_of_family_substance",
    "agent_charter_registry_dependency",
    "master_plan_followed_as_controlling_doctrine",
    "agent_charter_registry_used_for_role_validation",
    "existing_pr_patterns_used_for_style_only",
    "pr65_is_scope_boundary_not_algorithm_authority",
    "architecture_emphasis",
    "algorithm_family_count",
    "required_algorithm_family_count",
    "required_algorithm_families_present_count",
    "missing_algorithm_family_count",
    "classical_algorithm_family_count",
    "quantum_or_quantum_compatible_algorithm_family_count",
    "families_with_formula_class_count",
    "families_with_formula_expression_profile_count",
    "families_with_authorized_agent_roles_count",
    "families_with_valid_agent_roles_count",
    "families_with_input_parameter_families_count",
    "families_with_output_signal_type_count",
    "families_with_trade_context_applicability_count",
    "families_with_optimizer_compatibility_count",
    "families_with_quantum_applicability_count",
    "families_with_owner_override_supported_count",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "quantum_hybrid_families_requiring_strongest_classical_comparator_count",
    "quantum_hybrid_families_requiring_fallback_bundle_count",
    "quantum_hybrid_families_requiring_replay_paper_evidence_count",
    "families_requiring_live_evidence_before_profit_claim_count",
    "owner_quantum_priority_supported_count",
    "owner_can_force_quantum_priority_count",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "agent_algorithm_binding_created",
    "agent_algorithm_consumer_gate_created",
    "final_ready",
    "authority_boundary_all_false",
)

TOP_CONST_EXPECTATIONS = {
    "registry_type": REGISTRY_TYPE,
    "registry_version": REGISTRY_VERSION,
    "deterministic_output": True,
    "generated_at_utc": DETERMINISTIC_GENERATED_AT,
    "source_of_family_substance": MASTER_PLAN.as_posix(),
    "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
    "master_plan_followed_as_controlling_doctrine": True,
    "agent_charter_registry_used_for_role_validation": True,
    "existing_pr_patterns_used_for_style_only": True,
    "pr65_is_scope_boundary_not_algorithm_authority": True,
    "architecture_emphasis": ARCHITECTURE_EMPHASIS,
    "owner_global_override_authority": True,
    "owner_override_satisfies_all_qtt_internal_requirements": True,
    "chatgpt_authority_over_owner": False,
    "codex_authority_over_owner": False,
    "qtt_agent_authority_over_owner": False,
    "quantum_forward_design_supported": True,
    "quantum_evidence_claim_created": False,
    "alpha_evidence_claim_created": False,
    "profit_evidence_claim_created": False,
    "latency_superiority_evidence_claim_created": False,
    "execution_superiority_evidence_claim_created": False,
    "runtime_artifact_created": False,
    "live_artifact_created": False,
    "order_artifact_created": False,
    "source_acceptance_artifact_created": False,
    "connector_binding_artifact_created": False,
    "runtime_resolver_snapshot_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "quantum_backend_artifact_created": False,
    "bundle_file_present": False,
    "bundle_sha_present": False,
    "uses_pr_number_as_authority": False,
    "agent_algorithm_binding_created": False,
    "agent_algorithm_consumer_gate_created": False,
    "final_ready": False,
}

FALSE_TOP_FLAGS = tuple(
    field for field, expected in TOP_CONST_EXPECTATIONS.items() if expected is False
)

PR_NUMBER_PATTERN = re.compile(
    r"\bPR\s*#?\s*\d+\b|(?<![A-Za-z])pr\d+\b",
    re.IGNORECASE,
)
NUMERIC_RANGE_PATTERN = re.compile(
    r"(?<!FAMILY_)\b\d+(?:\.\d+)?\s*(?:-|to|\.\.)\s*\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FamilySpec:
    name: str
    description: str
    category: str
    classical_or_quantum: str
    formula_class: str
    expression_profile: str
    authority_class: str
    input_parameters: tuple[str, ...]
    output_signal_type: str
    output_artifacts: tuple[str, ...]
    roles: tuple[str, ...]
    consumers: tuple[str, ...]
    trade_contexts: tuple[str, ...]
    latency_class: str
    risk_class: str
    capital_class: str
    market_context: tuple[str, ...]
    platform_scope: tuple[str, ...]
    optimizer_compatibility: tuple[str, ...]
    quantum_applicability: tuple[str, ...]
    quantum_algorithm_access: tuple[str, ...]
    quantum_parameter_access: tuple[str, ...]
    deterministic_role: str
    scoring_role: str
    arbitration_role: str
    source_requirement: str
    connector_requirement: str
    runtime_requirement: str
    replay_paper_requirement: str
    risk_gate_requirement: str
    sizing_gate_requirement: str
    latency_gate_requirement: str
    validation_gate_requirement: str
    doctrine_terms: tuple[str, ...]
    derivation_summary: str


COMMON_DOCTRINE = (
    "edge_hypothesis_packet_required_before_parameter_stack_selection_flag",
    "edge_parameter_stack_selection_required_flag",
    "single_parameter_or_single_algorithm_trade_selection_allowed_flag",
    "atomicrows_bundle_is_parameter_algorithm_inventory_not_trader_flag",
    "execution_router_remains_final_order_submission_authority_flag",
)

QUANTUM_DOCTRINE = (
    "quantum_optimizer_replay_paper_candidate_trigger_allowed_flag",
    "quantum_optimizer_direct_live_order_submission_allowed_flag",
    "quantum_optimizer_live_trade_intent_creation_owner_mutable_after_all_gates_flag",
    "true_quantum_backend_setup_boundary",
    "quantum_advisory_result_requires_classical_comparator",
)

QUANTUM_ACCESS = (
    "TRUE_QUANTUM",
    "QUANTUM_INSPIRED",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUBO_COMPATIBLE",
    "ISING_COMPATIBLE",
    "QAOA_COMPATIBLE",
    "VQE_COMPATIBLE",
    "ANNEALING_COMPATIBLE",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE",
    "OWNER_QUANTUM_PRIORITY",
    "OWNER_FORCED_QUANTUM",
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK",
    "STRONGEST_CLASSICAL_COMPARATOR_REQUIRED",
    "FALLBACK_BUNDLE_REQUIRED",
    "REPLAY_PAPER_EVIDENCE_REQUIRED_BEFORE_ADVANTAGE_CLAIM",
    "LIVE_EVIDENCE_REQUIRED_BEFORE_PROFIT_CLAIM",
)

QUANTUM_PARAMETER_ACCESS = (
    "QUBO_SYMBOLIC_OBJECTIVE_PARAMETERS",
    "ISING_SYMBOLIC_MAPPING_PARAMETERS",
    "QAOA_SYMBOLIC_OBJECTIVE_PARAMETERS",
    "VQE_SYMBOLIC_OBJECTIVE_PARAMETERS",
    "ANNEALING_SYMBOLIC_ENERGY_PARAMETERS",
    "QUANTUM_PORTFOLIO_SYMBOLIC_OBJECTIVE_PARAMETERS",
    "OWNER_QUANTUM_PRIORITY_POLICY_PARAMETERS",
    "CLASSICAL_COMPARATOR_BASELINE_PARAMETERS",
)

CLASSICAL_QUANTUM_ACCESS = (
    "NO_TRUE_QUANTUM_BACKEND_ACCESS",
    "MAY_FEED_QUANTUM_ARBITRATION_AS_CLASSICAL_INPUT",
)

CLASSICAL_QUANTUM_PARAMETERS = (
    "CLASSICAL_COMPARATOR_PARAMETER_SURFACE",
    "NO_BACKEND_PARAMETER_ACCESS",
)

FAMILY_SPECS: tuple[FamilySpec, ...] = (
    FamilySpec(
        name="CLASSICAL_SIGNAL_ALGORITHM",
        description=(
            "Produces candidate signal features, edge indicators, microstructure signals, "
            "event-probability signals, and other non-live signal artifacts for later "
            "scoring and stack construction."
        ),
        category="SIGNAL_GENERATION",
        classical_or_quantum="CLASSICAL",
        formula_class="SIGNAL_TRANSFORMATION_FORMULA_CLASS",
        expression_profile="SYMBOLIC_SIGNAL_TRANSFORMATION",
        authority_class="MASTER_PLAN_STATIC_DOCTRINE",
        input_parameters=(
            "EDGE_HYPOTHESIS_PARAMETERS",
            "MICROSTRUCTURE_FEATURE_PARAMETERS",
            "SOURCE_DERIVED_FEATURE_PARAMETERS",
            "ATOMICROWS_PARAMETER_ALGORITHM_INVENTORY",
        ),
        output_signal_type="SIGNAL_FEATURE_CANDIDATE_SET",
        output_artifacts=("STATIC_SIGNAL_FEATURE_FAMILY_SURFACE",),
        roles=(
            "OPTIMIZER_AGENT",
            "ATOMICROWS_RESEARCH_AGENT",
            "REPLAY_AGENT",
            "PAPER_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("OPTIMIZER_SEARCH", "REPLAY_PAPER_SELECTION", "VALIDATION_GATE"),
        trade_contexts=("EDGE_HYPOTHESIS_CONTEXT", "RESEARCH_SIGNAL_CONTEXT"),
        latency_class="CONTROL_PLANE_OR_REPLAY_PAPER",
        risk_class="NON_ORDER_SIGNAL_ONLY",
        capital_class="NO_CAPITAL_AUTHORITY",
        market_context=("PREDICTION_MARKET_EDGE_CONTEXT", "MICROSTRUCTURE_SIGNAL_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "SOURCE_EVIDENCE_DEPENDENT"),
        optimizer_compatibility=(
            "DETERMINISTIC_SIGNAL_FAMILY_SELECTION_INPUT",
            "OPTIMIZER_CANDIDATE_FEATURE_INPUT",
        ),
        quantum_applicability=CLASSICAL_QUANTUM_ACCESS,
        quantum_algorithm_access=CLASSICAL_QUANTUM_ACCESS,
        quantum_parameter_access=CLASSICAL_QUANTUM_PARAMETERS,
        deterministic_role="DETERMINISTIC_SIGNAL_FAMILY_SELECTION",
        scoring_role="PROVIDES_SCORING_FEATURE_INPUTS",
        arbitration_role="CLASSICAL_INPUT_TO_FUTURE_QUANTUM_CLASSICAL_ARBITRATION",
        source_requirement=(
            "SOURCE_EVIDENCE_REQUIRED_FOR_SOURCE_DEPENDENT_FEATURES_NO_ACCEPTANCE_CREATED"
        ),
        connector_requirement="CONNECTOR_FACTS_REQUIRED_BEFORE_CONNECTOR_DEPENDENT_USE",
        runtime_requirement="RUNTIME_RESOLVER_NOT_CREATED_STATIC_SIGNAL_SURFACE_ONLY",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_SIGNAL_PROMOTION",
        risk_gate_requirement="RISK_GATE_CONSUMES_DOWNSTREAM_ONLY",
        sizing_gate_requirement="SIZING_GATE_NOT_AUTHORIZED_BY_SIGNAL_FAMILY",
        latency_gate_requirement="LIVE_PATH_EXCLUDED_UNTIL_LATER_APPROVAL",
        validation_gate_requirement="STATIC_VALIDATION_AND_CONSUMER_GATE_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, "microstructure_feature_family_names"),
        derivation_summary=(
            "Derived from the master-plan edge hypothesis, microstructure feature, "
            "AtomicRows inventory, and no single-algorithm direct-trade doctrines."
        ),
    ),
    FamilySpec(
        name="CLASSICAL_SCORING_ALGORITHM",
        description=(
            "Scores and ranks parameter stacks, signals, algorithms, candidates, replay "
            "or paper outputs, and trade-context candidates using deterministic policy."
        ),
        category="SCORING_RANKING",
        classical_or_quantum="CLASSICAL",
        formula_class="SCORING_RANKING_FORMULA_CLASS",
        expression_profile="SYMBOLIC_SCORING_FUNCTION",
        authority_class="MASTER_PLAN_STATIC_DOCTRINE",
        input_parameters=(
            "PARAMETER_STACK_CANDIDATES",
            "SIGNAL_OUTPUTS",
            "REPLAY_PAPER_RESULTS",
            "TRADE_CONTEXT_CANDIDATES",
        ),
        output_signal_type="DETERMINISTIC_SCORE_RANK_VECTOR",
        output_artifacts=("STATIC_SCORING_RANKING_SURFACE",),
        roles=(
            "OPTIMIZER_AGENT",
            "RISK_AGENT",
            "DUAL_RESULT_REVIEW_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("OPTIMIZER_ARBITRATION", "DUAL_RESULT_REVIEW", "VALIDATION_GATE"),
        trade_contexts=("PARAMETER_STACK_SELECTION_CONTEXT", "COMPARATOR_CONTEXT"),
        latency_class="CONTROL_PLANE_PRECOMPUTED",
        risk_class="ADVISORY_SCORING_NOT_RISK_APPROVAL",
        capital_class="NO_CAPITAL_AUTHORITY",
        market_context=("MULTI_CANDIDATE_SELECTION_CONTEXT", "REPLAY_PAPER_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "FUTURE_CONNECTOR_AWARE_AFTER_GATES"),
        optimizer_compatibility=(
            "PRIMARY_DETERMINISTIC_RANKING_INPUT",
            "STRONGEST_CLASSICAL_COMPARATOR_INPUT",
        ),
        quantum_applicability=(
            "STRONGEST_CLASSICAL_COMPARATOR_CANDIDATE",
            "QUANTUM_CHALLENGER_BASELINE_INPUT",
        ),
        quantum_algorithm_access=CLASSICAL_QUANTUM_ACCESS,
        quantum_parameter_access=CLASSICAL_QUANTUM_PARAMETERS,
        deterministic_role="PRIMARY_DETERMINISTIC_RANKING",
        scoring_role="CANONICAL_CLASSICAL_SCORING_AND_RANKING_SURFACE",
        arbitration_role="STRONGEST_CLASSICAL_COMPARATOR_FOR_QUANTUM_CHALLENGERS",
        source_requirement="SOURCE_EVIDENCE_REQUIRED_FOR_SOURCE_DEPENDENT_SCORES",
        connector_requirement="CONNECTOR_SEMANTICS_REQUIRED_FOR_CONNECTOR_DEPENDENT_SCORES",
        runtime_requirement="RUNTIME_SNAPSHOT_REQUIRED_BEFORE_RUNTIME_SCORES",
        replay_paper_requirement="REPLAY_PAPER_COMPARISON_REQUIRED_BEFORE_PROMOTION",
        risk_gate_requirement="RISK_GATE_MUST_CONSUME_OR_VETO_SCORE_OUTPUTS",
        sizing_gate_requirement="SIZING_GATE_NOT_AUTHORIZED_BY_SCORE_ALONE",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_BEFORE_LIVE_PATH_USE",
        validation_gate_requirement="DETERMINISTIC_RANKING_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, "scoring", "ranking"),
        derivation_summary=(
            "Derived from deterministic stack selection, strongest classical comparator, "
            "replay-paper competition, and no random selection doctrine."
        ),
    ),
    FamilySpec(
        name="CLASSICAL_RISK_ALGORITHM",
        description=(
            "Evaluates exposure, drawdown, kill-switch, stale or conflicted inputs, "
            "source and connector readiness, and risk veto surfaces."
        ),
        category="RISK_CONTROL",
        classical_or_quantum="CLASSICAL",
        formula_class="RISK_CONSTRAINT_FORMULA_CLASS",
        expression_profile="SYMBOLIC_RISK_CONSTRAINT_FUNCTION",
        authority_class="MASTER_PLAN_STATIC_DOCTRINE",
        input_parameters=(
            "RISK_LIMIT_PARAMETERS",
            "EXPOSURE_PARAMETERS",
            "SOURCE_CONNECTOR_RESOLVER_READINESS",
            "KILL_SWITCH_STATE",
        ),
        output_signal_type="RISK_GATE_DECISION_SURFACE",
        output_artifacts=("STATIC_RISK_CONTROL_SURFACE",),
        roles=(
            "RISK_AGENT",
            "SIZING_AGENT",
            "ORDER_ROUTER_AGENT",
            "LIVE_CANARY_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("RISK_GATE", "SIZING_GATE", "ORDER_ROUTER", "VALIDATION_GATE"),
        trade_contexts=("PRETRADE_RISK_CONTEXT", "LIVE_CANARY_ELIGIBILITY_CONTEXT"),
        latency_class="LIVE_PRETRADE_LIGHTWEIGHT_AFTER_GATES",
        risk_class="FAIL_CLOSED_RISK_CONTROL",
        capital_class="CAPITAL_PROTECTION_ONLY",
        market_context=("VENUE_READINESS_CONTEXT", "RISK_EXPOSURE_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "CONNECTOR_READINESS_DEPENDENT"),
        optimizer_compatibility=("OPTIMIZER_OUTPUT_RISK_FILTER", "RISK_VETO_SURFACE"),
        quantum_applicability=("RISK_CONSTRAINT_INPUT_TO_QUANTUM_OBJECTIVES",),
        quantum_algorithm_access=CLASSICAL_QUANTUM_ACCESS,
        quantum_parameter_access=CLASSICAL_QUANTUM_PARAMETERS,
        deterministic_role="DETERMINISTIC_RISK_ELIGIBILITY_FILTER",
        scoring_role="RISK_ADJUSTS_OR_VETOES_RANKED_CANDIDATES",
        arbitration_role="RISK_GATE_BOUNDS_QUANTUM_CLASSICAL_ARBITRATION",
        source_requirement="SOURCE_EVIDENCE_REQUIRED_FOR_RISK_INPUTS",
        connector_requirement="CONNECTOR_READINESS_REQUIRED_BEFORE_CONNECTOR_RISK_USE",
        runtime_requirement="RUNTIME_RESOLVER_INPUTS_REQUIRED_BEFORE_RUNTIME_RISK",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_FOR_RISK_PROMOTION_EVIDENCE",
        risk_gate_requirement="PRIMARY_RISK_GATE_FAIL_CLOSED_ON_UNKNOWN_STALE_CONFLICTED",
        sizing_gate_requirement="SIZING_GATE_MUST_CONSUME_RISK_APPROVAL",
        latency_gate_requirement="LATENCY_GATE_MUST_PRESERVE_FAIL_CLOSED_RISK",
        validation_gate_requirement="RISK_FAIL_CLOSED_VALIDATION_REQUIRED",
        doctrine_terms=(
            *COMMON_DOCTRINE,
            "source_dependent_live_or_shadow_field_still_requires_accepted_source_packet",
        ),
        derivation_summary=(
            "Derived from fail-closed source, connector, resolver, risk, canary, and "
            "execution-router readiness boundaries."
        ),
    ),
    FamilySpec(
        name="CLASSICAL_SIZING_ALGORITHM",
        description=(
            "Converts approved risk and capital constraints into candidate sizing "
            "recommendations after runtime cash and source prerequisites exist."
        ),
        category="SIZING_CAPITAL",
        classical_or_quantum="CLASSICAL",
        formula_class="SIZING_POLICY_FORMULA_CLASS",
        expression_profile="SYMBOLIC_SIZING_POLICY_FUNCTION",
        authority_class="SOURCE_EVIDENCE_REQUIRED_FOR_NUMERIC_VALUES",
        input_parameters=(
            "CAPITAL_POLICY_PARAMETERS",
            "RISK_APPROVED_CANDIDATES",
            "RUNTIME_CASH_COMPONENT_FIELD_MAP",
            "SIZING_CONSTRAINTS",
        ),
        output_signal_type="SIZING_RECOMMENDATION_CANDIDATE",
        output_artifacts=("STATIC_SIZING_CAPITAL_SURFACE",),
        roles=("SIZING_AGENT", "RISK_AGENT", "OPTIMIZER_AGENT", "VALIDATION_AGENT"),
        consumers=("SIZING_GATE", "RISK_GATE", "OPTIMIZER_SEARCH", "VALIDATION_GATE"),
        trade_contexts=("CAPITAL_ALLOCATION_CONTEXT", "RISK_APPROVED_CANDIDATE_CONTEXT"),
        latency_class="PRETRADE_AFTER_RUNTIME_CASH_RECEIPTS",
        risk_class="RISK_APPROVED_SIZING_ONLY",
        capital_class="CAPITAL_CONSTRAINT_CONSUMER_NO_BALANCE_FABRICATION",
        market_context=("MULTI_VENUE_CAPITAL_CONTEXT", "POSITION_SIZE_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "RUNTIME_CASH_DEPENDENT"),
        optimizer_compatibility=("OPTIMIZER_CANDIDATE_SIZE_INPUT", "CAPITAL_CONSTRAINT_FILTER"),
        quantum_applicability=("QUANTUM_PORTFOLIO_CONSTRAINT_INPUT",),
        quantum_algorithm_access=CLASSICAL_QUANTUM_ACCESS,
        quantum_parameter_access=CLASSICAL_QUANTUM_PARAMETERS,
        deterministic_role="DETERMINISTIC_SIZING_POLICY_SELECTION",
        scoring_role="CAPITAL_ADJUSTS_RANKED_CANDIDATES_AFTER_RISK",
        arbitration_role="SIZING_CONSTRAINTS_BOUND_OPTIMIZER_ARBITRATION",
        source_requirement="ACCEPTED_SOURCE_PACKET_REQUIRED_FOR_CASH_COMPONENT_SEMANTICS",
        connector_requirement="CONNECTOR_SEMANTICS_REQUIRED_BEFORE_BALANCE_FIELD_USE",
        runtime_requirement="RUNTIME_CASH_RECEIPT_REQUIRED_BEFORE_RUNTIME_SIZING",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_FOR_SIZING_PROMOTION",
        risk_gate_requirement="RISK_APPROVAL_REQUIRED_BEFORE_SIZING",
        sizing_gate_requirement="PRIMARY_SIZING_GATE_NO_CASH_FABRICATION",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_BEFORE_LIVE_SIZING_USE",
        validation_gate_requirement="CASH_AND_SIZING_NO_GUESSWORK_VALIDATION_REQUIRED",
        doctrine_terms=(
            *COMMON_DOCTRINE,
            "runtime_cash_component_field_map_requires_accepted_source_packet_per_component_flag",
        ),
        derivation_summary=(
            "Derived from runtime cash component map, accepted source packet, risk-before-sizing, "
            "and no fabricated balance doctrines."
        ),
    ),
    FamilySpec(
        name="CLASSICAL_EXECUTION_ALGORITHM",
        description=(
            "Defines future execution policy, routing constraints, order-intent "
            "transformation rules, venue policy references, throttle controls, reject "
            "controls, and execution router compatibility."
        ),
        category="EXECUTION_POLICY",
        classical_or_quantum="CLASSICAL",
        formula_class="EXECUTION_POLICY_FORMULA_CLASS",
        expression_profile="SYMBOLIC_EXECUTION_POLICY_FUNCTION",
        authority_class="MASTER_PLAN_STATIC_DOCTRINE",
        input_parameters=(
            "ORDER_INTENT_POLICY_PARAMETERS",
            "VENUE_EXECUTION_CONSTRAINTS",
            "ROUTER_COMPATIBILITY_PARAMETERS",
            "THROTTLE_REJECT_ERROR_CONTROLS",
        ),
        output_signal_type="EXECUTION_POLICY_CONSTRAINT_SURFACE",
        output_artifacts=("STATIC_EXECUTION_POLICY_SURFACE",),
        roles=(
            "ORDER_ROUTER_AGENT",
            "EXECUTION_LATENCY_AGENT",
            "RISK_AGENT",
            "LIVE_CANARY_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("ORDER_ROUTER", "EXECUTION_LATENCY_GATE", "RISK_GATE", "VALIDATION_GATE"),
        trade_contexts=("ORDER_INTENT_TRANSFORMATION_CONTEXT", "ROUTER_POLICY_CONTEXT"),
        latency_class="LIVE_ORDER_PATH_ONLY_AFTER_ALL_GATES",
        risk_class="ROUTER_COMPATIBLE_EXECUTION_POLICY",
        capital_class="NO_CAPITAL_CREATION",
        market_context=("VENUE_EXECUTION_CONTEXT", "ORDER_ROUTING_CONTEXT"),
        platform_scope=("CONNECTOR_DEPENDENT_AFTER_BINDING", "EXECUTION_ROUTER_REQUIRED"),
        optimizer_compatibility=("EXECUTION_COST_CONSTRAINT_INPUT", "ROUTER_POLICY_FILTER"),
        quantum_applicability=("EXECUTION_OPTIMIZATION_ADVISORY_INPUT_ONLY",),
        quantum_algorithm_access=CLASSICAL_QUANTUM_ACCESS,
        quantum_parameter_access=CLASSICAL_QUANTUM_PARAMETERS,
        deterministic_role="DETERMINISTIC_EXECUTION_POLICY_SELECTION",
        scoring_role="EXECUTION_POLICY_ADJUSTS_CANDIDATE_RANKING_AFTER_GATES",
        arbitration_role="EXECUTION_ROUTER_REMAINS_FINAL_FOR_LIVE_ORDER_PATH",
        source_requirement="SOURCE_EVIDENCE_REQUIRED_FOR_VENUE_EXECUTION_FACTS",
        connector_requirement="CONNECTOR_BINDING_REQUIRED_BEFORE_VENUE_POLICY_USE",
        runtime_requirement="RUNTIME_ORDER_CONTEXT_REQUIRED_BEFORE_RUNTIME_POLICY",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_EXECUTION_POLICY_PROMOTION",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_EXECUTION_POLICY_USE",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ORDER_INTENT_SIZE_USE",
        latency_gate_requirement="EXECUTION_LATENCY_GATE_REQUIRED_BEFORE_LIVE_PATH_USE",
        validation_gate_requirement="EXECUTION_ROUTER_AUTHORITY_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, "execution_router_remains_final_order_submission_authority_flag"),
        derivation_summary=(
            "Derived from the execution router final authority, no direct order submission, "
            "and staged order-intent boundary doctrines."
        ),
    ),
    FamilySpec(
        name="CLASSICAL_LATENCY_ALGORITHM",
        description=(
            "Classifies latency sensitivity, live-path exclusion rules, precomputed "
            "source and cash snapshot policy, execution-quality timing constraints, "
            "and control-plane separation."
        ),
        category="LATENCY_CONTROL",
        classical_or_quantum="CLASSICAL",
        formula_class="LATENCY_COST_FORMULA_CLASS",
        expression_profile="SYMBOLIC_LATENCY_COST_FUNCTION",
        authority_class="MASTER_PLAN_STATIC_DOCTRINE",
        input_parameters=(
            "LATENCY_SENSITIVITY_PARAMETERS",
            "PRECOMPUTED_SNAPSHOT_PARAMETERS",
            "EXECUTION_TIMING_CONSTRAINTS",
            "CONTROL_PLANE_SEPARATION_POLICY",
        ),
        output_signal_type="LATENCY_CLASSIFICATION_SURFACE",
        output_artifacts=("STATIC_LATENCY_CONTROL_SURFACE",),
        roles=(
            "EXECUTION_LATENCY_AGENT",
            "ORDER_ROUTER_AGENT",
            "OPTIMIZER_AGENT",
            "RISK_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("EXECUTION_LATENCY_GATE", "ORDER_ROUTER", "OPTIMIZER_SEARCH", "VALIDATION_GATE"),
        trade_contexts=("LIVE_PRETRADE_LATENCY_CONTEXT", "CONTROL_PLANE_SEPARATION_CONTEXT"),
        latency_class="LIVE_PATH_GUARD_WITH_CONTROL_PLANE_EXCLUSION",
        risk_class="LATENCY_DEPENDENCY_RISK_CONTROL",
        capital_class="NO_CAPITAL_AUTHORITY",
        market_context=("LOW_LATENCY_PRETRADE_CONTEXT", "EXECUTION_QUALITY_CONTEXT"),
        platform_scope=("LIVE_PRETRADE_PATH_GUARD", "CONTROL_PLANE_BOUNDARY"),
        optimizer_compatibility=("LATENCY_COST_INPUT", "LIVE_PATH_ELIGIBILITY_FILTER"),
        quantum_applicability=("QUANTUM_BACKEND_LIVE_PATH_EXCLUSION_INPUT",),
        quantum_algorithm_access=CLASSICAL_QUANTUM_ACCESS,
        quantum_parameter_access=CLASSICAL_QUANTUM_PARAMETERS,
        deterministic_role="DETERMINISTIC_LATENCY_CLASS_SELECTION",
        scoring_role="LATENCY_COST_ADJUSTS_RANKING_WHEN_POLICY_ALLOWS",
        arbitration_role="BLOCKS_HEAVY_BACKEND_WORK_FROM_LIVE_PRETRADE_PATH",
        source_requirement="SOURCE_EVIDENCE_REQUIRED_FOR_TIMING_FACTS",
        connector_requirement="CONNECTOR_LATENCY_FACTS_REQUIRE_ACCEPTED_SOURCE_OR_RECEIPT",
        runtime_requirement="PRECOMPUTED_RUNTIME_SNAPSHOT_REQUIRED_FOR_LIVE_PATH",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_FOR_LATENCY_POLICY_PROMOTION",
        risk_gate_requirement="RISK_GATE_MUST_SEE_LATENCY_DEPENDENCY_STATE",
        sizing_gate_requirement="SIZING_GATE_MUST_NOT_DEPEND_ON_HEAVY_CONTROL_PLANE",
        latency_gate_requirement="PRIMARY_LATENCY_GATE_CONTROL_PLANE_EXCLUSION",
        validation_gate_requirement="LIVE_PRETRADE_PATH_EXCLUSION_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, "limited_live_canary_live_path_must_not_call_llm_or_quantum_backend"),
        derivation_summary=(
            "Derived from live pretrade path exclusion doctrine for source retrieval, "
            "replay, dashboard, LLM, quantum backend, and other control-plane work."
        ),
    ),
)

QUANTUM_FAMILY_SPECS: tuple[FamilySpec, ...] = (
    FamilySpec(
        name="QUANTUM_INSPIRED_OPTIMIZER",
        description=(
            "Optimizes parameter stacks, candidate portfolios, scoring surfaces, and "
            "combinatorial selection problems with quantum-inspired methods while "
            "remaining classical execution."
        ),
        category="OPTIMIZER",
        classical_or_quantum="QUANTUM_INSPIRED",
        formula_class="QUANTUM_INSPIRED_OPTIMIZER_FORMULA_CLASS",
        expression_profile="SYMBOLIC_HYBRID_ARBITRATION_FUNCTION",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=(
            "PARAMETER_STACK_SELECTION_UNIVERSE",
            "SCORING_SURFACE",
            "COMBINATORIAL_SELECTION_OBJECTIVE",
            "CLASSICAL_COMPARATOR_BASELINE",
        ),
        output_signal_type="OPTIMIZER_CANDIDATE_SET",
        output_artifacts=("STATIC_QUANTUM_INSPIRED_OPTIMIZER_SURFACE",),
        roles=("OPTIMIZER_AGENT", "QUANTUM_RESEARCH_AGENT", "RISK_AGENT", "SIZING_AGENT", "VALIDATION_AGENT"),
        consumers=("OPTIMIZER_ARBITRATION", "QUANTUM_RESEARCH", "RISK_GATE", "VALIDATION_GATE"),
        trade_contexts=("PARAMETER_STACK_OPTIMIZATION_CONTEXT", "REPLAY_PAPER_CANDIDATE_CONTEXT"),
        latency_class="CONTROL_PLANE_REPLAY_PAPER_ONLY",
        risk_class="ADVISORY_OPTIMIZER_REQUIRES_RISK_GATE",
        capital_class="CAPITAL_CONSTRAINT_INPUT_ONLY",
        market_context=("COMBINATORIAL_SELECTION_CONTEXT", "PORTFOLIO_CANDIDATE_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "NO_BACKEND_CALL_REQUIRED"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_QUANTUM_INSPIRED_CANDIDATE_GENERATION",
        scoring_role="CHALLENGER_OPTIMIZER_RANKED_AGAINST_CLASSICAL_COMPARATOR",
        arbitration_role="HYBRID_COMPARE_THEN_CLASSICAL_FALLBACK_OR_OWNER_QUANTUM_PRIORITY",
        source_requirement="SOURCE_EVIDENCE_OR_PRIMARY_RESEARCH_REQUIRED_FOR_OBJECTIVE_DETAIL",
        connector_requirement="CONNECTOR_DEPENDENCIES_NOT_CREATED_STATIC_OPTIMIZER_SURFACE_ONLY",
        runtime_requirement="NO_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_TO_KEEP_HEAVY_WORK_OFF_LIVE_PATH",
        validation_gate_requirement="COMPARATOR_AND_FALLBACK_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE),
        derivation_summary=(
            "Derived from quantum optimizer candidate, strongest classical comparator, "
            "fallback, replay-paper, owner quantum priority, and no direct order doctrines."
        ),
    ),
    FamilySpec(
        name="TRUE_QUANTUM_OPTIMIZER",
        description=(
            "Defines future true quantum optimizer candidates, backend-compatible objective "
            "mapping, quantum primitive readiness placeholders, and true-quantum boundaries."
        ),
        category="OPTIMIZER",
        classical_or_quantum="TRUE_QUANTUM",
        formula_class="TRUE_QUANTUM_OPTIMIZER_FORMULA_CLASS",
        expression_profile="SYMBOLIC_HYBRID_ARBITRATION_FUNCTION",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=(
            "BACKEND_COMPATIBLE_OBJECTIVE_SURFACE",
            "QUANTUM_PRIMITIVE_READINESS_POLICY",
            "CLASSICAL_COMPARATOR_BASELINE",
            "OWNER_BACKEND_POLICY_PARAMETERS",
        ),
        output_signal_type="TRUE_QUANTUM_OPTIMIZER_CANDIDATE_SURFACE",
        output_artifacts=("STATIC_TRUE_QUANTUM_OPTIMIZER_SURFACE",),
        roles=(
            "QUANTUM_RESEARCH_AGENT",
            "QUANTUM_BACKEND_AGENT",
            "OPTIMIZER_AGENT",
            "VALIDATION_AGENT",
            "OWNER_APPROVAL_REQUEST_AGENT",
        ),
        consumers=("QUANTUM_RESEARCH", "QUANTUM_BACKEND_READINESS", "OPTIMIZER_ARBITRATION", "VALIDATION_GATE"),
        trade_contexts=("FUTURE_TRUE_QUANTUM_RESEARCH_CONTEXT", "OWNER_APPROVED_BACKEND_CONTEXT"),
        latency_class="CONTROL_PLANE_BACKEND_ONLY_NOT_LIVE_PRETRADE",
        risk_class="ADVISORY_REQUIRES_OWNER_AND_RISK_GATES",
        capital_class="NO_CAPITAL_AUTHORITY",
        market_context=("QUANTUM_OBJECTIVE_RESEARCH_CONTEXT", "COMPARATOR_CONTEXT"),
        platform_scope=("BACKEND_ADVISORY_ONLY", "OWNER_APPROVAL_REQUIRED_BEFORE_BACKEND_USE"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_TRUE_QUANTUM_CANDIDATE_REGISTRATION",
        scoring_role="TRUE_QUANTUM_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR",
        arbitration_role="OWNER_APPROVED_BACKEND_CANDIDATE_WITH_CLASSICAL_FALLBACK",
        source_requirement="PRIMARY_RESEARCH_OR_OWNER_APPROVED_CANONICAL_PACKET_REQUIRED",
        connector_requirement="NO_CONNECTOR_BINDING_CREATED",
        runtime_requirement="NO_RUNTIME_BACKEND_EXECUTION_OR_RESOLVER_SNAPSHOT_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_TO_KEEP_BACKEND_OFF_LIVE_PRETRADE_PATH",
        validation_gate_requirement="OWNER_APPROVAL_COMPARATOR_FALLBACK_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "quantum_backend_advisory_registry_must_precede_backend_specific_quantum_tasks"),
        derivation_summary=(
            "Derived from true quantum backend advisory boundaries, comparator and fallback "
            "requirements, owner approval, and no backend execution in this static registry."
        ),
    ),
    FamilySpec(
        name="HYBRID_CLASSICAL_QUANTUM_OPTIMIZER",
        description=(
            "Supports hybrid compare-then-select, hybrid scoring, classical baseline plus "
            "quantum challenger, quantum tie-break, and owner-forced quantum policy."
        ),
        category="OPTIMIZER_ARBITRATION",
        classical_or_quantum="HYBRID_CLASSICAL_QUANTUM",
        formula_class="HYBRID_ARBITRATION_FORMULA_CLASS",
        expression_profile="SYMBOLIC_HYBRID_ARBITRATION_FUNCTION",
        authority_class="MASTER_PLAN_STATIC_DOCTRINE",
        input_parameters=(
            "CLASSICAL_BASELINE_SCORE_SURFACE",
            "QUANTUM_CHALLENGER_SCORE_SURFACE",
            "OWNER_QUANTUM_PRIORITY_POLICY",
            "FALLBACK_BUNDLE_POLICY",
        ),
        output_signal_type="HYBRID_ARBITRATION_DECISION_SURFACE",
        output_artifacts=("STATIC_HYBRID_ARBITRATION_SURFACE",),
        roles=(
            "OPTIMIZER_AGENT",
            "QUANTUM_RESEARCH_AGENT",
            "RISK_AGENT",
            "SIZING_AGENT",
            "EXECUTION_LATENCY_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("OPTIMIZER_ARBITRATION", "RISK_GATE", "SIZING_GATE", "EXECUTION_LATENCY_GATE", "VALIDATION_GATE"),
        trade_contexts=("HYBRID_ARBITRATION_CONTEXT", "OWNER_FORCED_QUANTUM_PRIORITY_CONTEXT"),
        latency_class="CONTROL_PLANE_ARBITRATION_WITH_LIVE_PATH_GUARD",
        risk_class="ADVISORY_ARBITRATION_REQUIRES_RISK_GATE",
        capital_class="CAPITAL_CONSTRAINT_AWARE_AFTER_SIZING_GATE",
        market_context=("PARAMETER_STACK_ARBITRATION_CONTEXT", "PORTFOLIO_CANDIDATE_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "OWNER_POLICY_COMPATIBLE"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_HYBRID_ARBITRATION",
        scoring_role="COMPARES_CLASSICAL_BASELINE_AND_QUANTUM_CHALLENGER",
        arbitration_role="HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_WHEN_POLICY_ALLOWS",
        source_requirement="SOURCE_EVIDENCE_REQUIRED_FOR_SOURCE_DEPENDENT_ARBITRATION_INPUTS",
        connector_requirement="CONNECTOR_DEPENDENCIES_NOT_CREATED_STATIC_ARBITRATION_ONLY",
        runtime_requirement="NO_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_FOR_QUANTUM_LIVE_PATH_EXCLUSION",
        validation_gate_requirement="DETERMINISTIC_ARBITRATION_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE),
        derivation_summary=(
            "Derived from deterministic stack arbitration, owner quantum priority, "
            "strongest classical comparator, fallback bundle, and replay-paper doctrines."
        ),
    ),
    FamilySpec(
        name="QUBO_COMPATIBLE_ALGORITHM",
        description=(
            "Maps candidate stack, portfolio, and selection objectives into "
            "QUBO-compatible symbolic formulation surfaces."
        ),
        category="QUANTUM_FORMULATION",
        classical_or_quantum="QUANTUM_COMPATIBLE",
        formula_class="QUBO_OBJECTIVE_FORMULA_CLASS",
        expression_profile="SYMBOLIC_QUBO_OBJECTIVE",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=("SELECTION_OBJECTIVE_TERMS", "CONSTRAINT_PENALTY_SYMBOLS", "CLASSICAL_COMPARATOR_BASELINE"),
        output_signal_type="QUBO_SYMBOLIC_OBJECTIVE_SURFACE",
        output_artifacts=("STATIC_QUBO_FORMULATION_SURFACE",),
        roles=("QUANTUM_RESEARCH_AGENT", "OPTIMIZER_AGENT", "QUANTUM_BACKEND_AGENT", "VALIDATION_AGENT"),
        consumers=("QUANTUM_RESEARCH", "OPTIMIZER_ARBITRATION", "QUANTUM_BACKEND_READINESS", "VALIDATION_GATE"),
        trade_contexts=("SYMBOLIC_OBJECTIVE_MAPPING_CONTEXT", "COMBINATORIAL_SELECTION_CONTEXT"),
        latency_class="CONTROL_PLANE_SYMBOLIC_FORMULATION",
        risk_class="SYMBOLIC_ONLY_REQUIRES_RISK_CONSTRAINT_BINDING",
        capital_class="CAPITAL_CONSTRAINT_SYMBOLIC_INPUT_ONLY",
        market_context=("SELECTION_OBJECTIVE_CONTEXT", "PORTFOLIO_OBJECTIVE_CONTEXT"),
        platform_scope=("BACKEND_ADVISORY_ONLY", "SYMBOLIC_FORMULATION_ONLY"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_QUBO_FORMULATION_SELECTION",
        scoring_role="QUBO_OBJECTIVE_MAY_FEED_OPTIMIZER_SCORING_AFTER_BINDING",
        arbitration_role="QUBO_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR_AND_FALLBACK",
        source_requirement="SOURCE_EVIDENCE_OR_OWNER_APPROVED_CANONICAL_PACKET_REQUIRED_FOR_EXACT_COEFFICIENTS",
        connector_requirement="NO_CONNECTOR_BINDING_CREATED",
        runtime_requirement="NO_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_CONSTRAINT_MAPPING_REQUIRED_BEFORE_LIVE_USE",
        sizing_gate_requirement="SIZING_CONSTRAINT_MAPPING_REQUIRED_BEFORE_LIVE_USE",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_BEFORE_ANY_LIVE_PATH_USE",
        validation_gate_requirement="SYMBOLIC_FORMULATION_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "QUBO"),
        derivation_summary=(
            "Derived from quantum-compatible formulation and optimizer arbitration doctrine; "
            "it records symbolic QUBO surfaces without coefficient or backend claims."
        ),
    ),
    FamilySpec(
        name="ISING_COMPATIBLE_ALGORITHM",
        description=(
            "Maps selection, risk, and portfolio objectives into Ising-compatible "
            "symbolic formulation surfaces."
        ),
        category="QUANTUM_FORMULATION",
        classical_or_quantum="QUANTUM_COMPATIBLE",
        formula_class="ISING_HAMILTONIAN_FORMULA_CLASS",
        expression_profile="SYMBOLIC_ISING_HAMILTONIAN",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=("SPIN_VARIABLE_MAPPING_POLICY", "OBJECTIVE_HAMILTONIAN_SYMBOLS", "CLASSICAL_COMPARATOR_BASELINE"),
        output_signal_type="ISING_SYMBOLIC_OBJECTIVE_SURFACE",
        output_artifacts=("STATIC_ISING_FORMULATION_SURFACE",),
        roles=("QUANTUM_RESEARCH_AGENT", "OPTIMIZER_AGENT", "QUANTUM_BACKEND_AGENT", "VALIDATION_AGENT"),
        consumers=("QUANTUM_RESEARCH", "OPTIMIZER_ARBITRATION", "QUANTUM_BACKEND_READINESS", "VALIDATION_GATE"),
        trade_contexts=("SYMBOLIC_HAMILTONIAN_CONTEXT", "SELECTION_RISK_PORTFOLIO_CONTEXT"),
        latency_class="CONTROL_PLANE_SYMBOLIC_FORMULATION",
        risk_class="SYMBOLIC_ONLY_REQUIRES_RISK_CONSTRAINT_BINDING",
        capital_class="CAPITAL_CONSTRAINT_SYMBOLIC_INPUT_ONLY",
        market_context=("SELECTION_OBJECTIVE_CONTEXT", "RISK_OBJECTIVE_CONTEXT"),
        platform_scope=("BACKEND_ADVISORY_ONLY", "SYMBOLIC_FORMULATION_ONLY"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_ISING_FORMULATION_SELECTION",
        scoring_role="ISING_OBJECTIVE_MAY_FEED_OPTIMIZER_SCORING_AFTER_BINDING",
        arbitration_role="ISING_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR_AND_FALLBACK",
        source_requirement="SOURCE_EVIDENCE_OR_OWNER_APPROVED_CANONICAL_PACKET_REQUIRED_FOR_EXACT_TERMS",
        connector_requirement="NO_CONNECTOR_BINDING_CREATED",
        runtime_requirement="NO_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_CONSTRAINT_MAPPING_REQUIRED_BEFORE_LIVE_USE",
        sizing_gate_requirement="SIZING_CONSTRAINT_MAPPING_REQUIRED_BEFORE_LIVE_USE",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_BEFORE_ANY_LIVE_PATH_USE",
        validation_gate_requirement="SYMBOLIC_HAMILTONIAN_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "Ising"),
        derivation_summary=(
            "Derived from quantum-compatible objective mapping doctrine; it records "
            "symbolic Ising surfaces without numeric Hamiltonian or backend claims."
        ),
    ),
    FamilySpec(
        name="QAOA_COMPATIBLE_ALGORITHM",
        description=(
            "Defines QAOA-compatible symbolic objectives and circuit-profile readiness "
            "surfaces for future backend work."
        ),
        category="QUANTUM_ALGORITHM",
        classical_or_quantum="TRUE_QUANTUM_COMPATIBLE",
        formula_class="QAOA_OBJECTIVE_FORMULA_CLASS",
        expression_profile="SYMBOLIC_QAOA_OBJECTIVE",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=("QUBO_OR_ISING_OBJECTIVE_SURFACE", "CIRCUIT_PROFILE_READINESS_POLICY", "CLASSICAL_COMPARATOR_BASELINE"),
        output_signal_type="QAOA_SYMBOLIC_OBJECTIVE_SURFACE",
        output_artifacts=("STATIC_QAOA_COMPATIBILITY_SURFACE",),
        roles=("QUANTUM_RESEARCH_AGENT", "QUANTUM_BACKEND_AGENT", "OPTIMIZER_AGENT", "VALIDATION_AGENT"),
        consumers=("QUANTUM_RESEARCH", "QUANTUM_BACKEND_READINESS", "OPTIMIZER_ARBITRATION", "VALIDATION_GATE"),
        trade_contexts=("FUTURE_QAOA_RESEARCH_CONTEXT", "BACKEND_READINESS_CONTEXT"),
        latency_class="CONTROL_PLANE_BACKEND_ONLY_NOT_LIVE_PRETRADE",
        risk_class="ADVISORY_REQUIRES_RISK_GATE_BEFORE_PROMOTION",
        capital_class="NO_CAPITAL_AUTHORITY",
        market_context=("QUANTUM_OBJECTIVE_CONTEXT", "COMBINATORIAL_SELECTION_CONTEXT"),
        platform_scope=("BACKEND_ADVISORY_ONLY", "NO_PRIMITIVE_EXECUTION_CREATED"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_QAOA_COMPATIBILITY_SELECTION",
        scoring_role="QAOA_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR",
        arbitration_role="QAOA_ROUTE_REQUIRES_FALLBACK_AND_OWNER_POLICY_WHEN_BACKEND_BOUND",
        source_requirement="PRIMARY_RESEARCH_REQUIRED_FOR_CIRCUIT_DETAIL_NO_DEFAULT_DEPTH_GUESS",
        connector_requirement="NO_CONNECTOR_BINDING_CREATED",
        runtime_requirement="NO_RUNTIME_OR_BACKEND_EXECUTION_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_TO_KEEP_BACKEND_OFF_LIVE_PRETRADE_PATH",
        validation_gate_requirement="NO_SHOT_OR_DEPTH_DEFAULT_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "QAOA", "quantum primitive"),
        derivation_summary=(
            "Derived from true-quantum compatible objective and backend boundary doctrine; "
            "it records QAOA readiness without shot counts, depth defaults, or backend calls."
        ),
    ),
    FamilySpec(
        name="VQE_COMPATIBLE_ALGORITHM",
        description=(
            "Defines VQE-compatible symbolic objective and ansatz-readiness surfaces for "
            "future research and backend compatibility."
        ),
        category="QUANTUM_ALGORITHM",
        classical_or_quantum="TRUE_QUANTUM_COMPATIBLE",
        formula_class="VQE_OBJECTIVE_FORMULA_CLASS",
        expression_profile="SYMBOLIC_VQE_OBJECTIVE",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=("VARIATIONAL_OBJECTIVE_SURFACE", "ANSATZ_READINESS_POLICY", "CLASSICAL_COMPARATOR_BASELINE"),
        output_signal_type="VQE_SYMBOLIC_OBJECTIVE_SURFACE",
        output_artifacts=("STATIC_VQE_COMPATIBILITY_SURFACE",),
        roles=("QUANTUM_RESEARCH_AGENT", "QUANTUM_BACKEND_AGENT", "OPTIMIZER_AGENT", "VALIDATION_AGENT"),
        consumers=("QUANTUM_RESEARCH", "QUANTUM_BACKEND_READINESS", "OPTIMIZER_ARBITRATION", "VALIDATION_GATE"),
        trade_contexts=("FUTURE_VQE_RESEARCH_CONTEXT", "VARIATIONAL_OBJECTIVE_CONTEXT"),
        latency_class="CONTROL_PLANE_BACKEND_ONLY_NOT_LIVE_PRETRADE",
        risk_class="ADVISORY_REQUIRES_RISK_GATE_BEFORE_PROMOTION",
        capital_class="NO_CAPITAL_AUTHORITY",
        market_context=("VARIATIONAL_OBJECTIVE_CONTEXT", "PORTFOLIO_RESEARCH_CONTEXT"),
        platform_scope=("BACKEND_ADVISORY_ONLY", "NO_ANSATZ_DEFAULT_CREATED"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_VQE_COMPATIBILITY_SELECTION",
        scoring_role="VQE_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR",
        arbitration_role="VQE_ROUTE_REQUIRES_FALLBACK_AND_OWNER_POLICY_WHEN_BACKEND_BOUND",
        source_requirement="PRIMARY_RESEARCH_REQUIRED_FOR_ANSATZ_DETAIL_NO_DEFAULT_GUESS",
        connector_requirement="NO_CONNECTOR_BINDING_CREATED",
        runtime_requirement="NO_RUNTIME_OR_BACKEND_EXECUTION_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_TO_KEEP_BACKEND_OFF_LIVE_PRETRADE_PATH",
        validation_gate_requirement="NO_ANSATZ_DEFAULT_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "VQE", "quantum primitive"),
        derivation_summary=(
            "Derived from variational quantum research and backend boundary doctrine; "
            "it records VQE compatibility without ansatz defaults or backend execution."
        ),
    ),
    FamilySpec(
        name="ANNEALING_COMPATIBLE_ALGORITHM",
        description=(
            "Defines annealing-compatible energy and objective formulations for future "
            "selection, risk, portfolio, or combinatorial optimization."
        ),
        category="QUANTUM_ALGORITHM",
        classical_or_quantum="TRUE_QUANTUM_OR_QUANTUM_INSPIRED_COMPATIBLE",
        formula_class="ANNEALING_ENERGY_FORMULA_CLASS",
        expression_profile="SYMBOLIC_ANNEALING_ENERGY_OBJECTIVE",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=("ENERGY_OBJECTIVE_TERMS", "CONSTRAINT_SYMBOLS", "CLASSICAL_COMPARATOR_BASELINE"),
        output_signal_type="ANNEALING_SYMBOLIC_ENERGY_SURFACE",
        output_artifacts=("STATIC_ANNEALING_COMPATIBILITY_SURFACE",),
        roles=("QUANTUM_RESEARCH_AGENT", "QUANTUM_BACKEND_AGENT", "OPTIMIZER_AGENT", "RISK_AGENT", "VALIDATION_AGENT"),
        consumers=("QUANTUM_RESEARCH", "QUANTUM_BACKEND_READINESS", "OPTIMIZER_ARBITRATION", "RISK_GATE", "VALIDATION_GATE"),
        trade_contexts=("ANNEALING_OBJECTIVE_CONTEXT", "COMBINATORIAL_SELECTION_CONTEXT"),
        latency_class="CONTROL_PLANE_BACKEND_ONLY_NOT_LIVE_PRETRADE",
        risk_class="ADVISORY_REQUIRES_RISK_CONSTRAINT_MAPPING",
        capital_class="CAPITAL_CONSTRAINT_SYMBOLIC_INPUT_ONLY",
        market_context=("SELECTION_OBJECTIVE_CONTEXT", "PORTFOLIO_OBJECTIVE_CONTEXT"),
        platform_scope=("BACKEND_ADVISORY_ONLY", "NO_ANNEALING_SCHEDULE_CREATED"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_ANNEALING_COMPATIBILITY_SELECTION",
        scoring_role="ANNEALING_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR",
        arbitration_role="ANNEALING_ROUTE_REQUIRES_FALLBACK_AND_OWNER_POLICY_WHEN_BACKEND_BOUND",
        source_requirement="PRIMARY_RESEARCH_REQUIRED_FOR_ANNEALING_DETAIL_NO_SCHEDULE_GUESS",
        connector_requirement="NO_CONNECTOR_BINDING_CREATED",
        runtime_requirement="NO_RUNTIME_OR_BACKEND_EXECUTION_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_ANY_LIVE_INTENT_PATH",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_TO_KEEP_BACKEND_OFF_LIVE_PRETRADE_PATH",
        validation_gate_requirement="NO_ANNEALING_SCHEDULE_DEFAULT_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "annealing"),
        derivation_summary=(
            "Derived from quantum and quantum-inspired annealing compatibility doctrine; "
            "it records symbolic energy surfaces without schedule values or backend calls."
        ),
    ),
    FamilySpec(
        name="QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_ALGORITHM",
        description=(
            "Defines quantum-compatible portfolio, position, and stack allocation "
            "formulations across candidate stacks, venues, risks, costs, and constraints."
        ),
        category="PORTFOLIO_OPTIMIZATION",
        classical_or_quantum="HYBRID_CLASSICAL_QUANTUM",
        formula_class="QUANTUM_PORTFOLIO_OBJECTIVE_FORMULA_CLASS",
        expression_profile="SYMBOLIC_QUANTUM_PORTFOLIO_OBJECTIVE",
        authority_class="PRIMARY_RESEARCH_REQUIRED_FOR_FORMULA_DETAIL",
        input_parameters=("PORTFOLIO_CANDIDATE_STACKS", "RISK_CONSTRAINT_SYMBOLS", "SIZING_CONSTRAINT_SYMBOLS", "CLASSICAL_COMPARATOR_BASELINE"),
        output_signal_type="QUANTUM_PORTFOLIO_OBJECTIVE_SURFACE",
        output_artifacts=("STATIC_QUANTUM_PORTFOLIO_OPTIMIZATION_SURFACE",),
        roles=(
            "OPTIMIZER_AGENT",
            "QUANTUM_RESEARCH_AGENT",
            "RISK_AGENT",
            "SIZING_AGENT",
            "EXECUTION_LATENCY_AGENT",
            "VALIDATION_AGENT",
        ),
        consumers=("OPTIMIZER_ARBITRATION", "RISK_GATE", "SIZING_GATE", "EXECUTION_LATENCY_GATE", "VALIDATION_GATE"),
        trade_contexts=("PORTFOLIO_ALLOCATION_CONTEXT", "STACK_SELECTION_CONTEXT", "OWNER_QUANTUM_PRIORITY_CONTEXT"),
        latency_class="CONTROL_PLANE_PORTFOLIO_OPTIMIZATION_WITH_LIVE_PATH_GUARD",
        risk_class="REQUIRES_RISK_AND_SIZING_GATES_BEFORE_LIVE_USE",
        capital_class="CAPITAL_CONSTRAINT_SYMBOLIC_INPUT_ONLY",
        market_context=("MULTI_STACK_PORTFOLIO_CONTEXT", "MULTI_VENUE_ALLOCATION_CONTEXT"),
        platform_scope=("VENUE_NEUTRAL", "FUTURE_CONNECTOR_AWARE_AFTER_GATES"),
        optimizer_compatibility=QUANTUM_ACCESS,
        quantum_applicability=QUANTUM_ACCESS,
        quantum_algorithm_access=QUANTUM_ACCESS,
        quantum_parameter_access=QUANTUM_PARAMETER_ACCESS,
        deterministic_role="DETERMINISTIC_QUANTUM_PORTFOLIO_FORMULATION_SELECTION",
        scoring_role="PORTFOLIO_CHALLENGER_REQUIRES_CLASSICAL_COMPARATOR",
        arbitration_role="HYBRID_PORTFOLIO_ARBITRATION_WITH_CLASSICAL_FALLBACK",
        source_requirement="SOURCE_EVIDENCE_OR_OWNER_APPROVED_CANONICAL_PACKET_REQUIRED_FOR_EXACT_OBJECTIVE_VALUES",
        connector_requirement="CONNECTOR_BINDING_REQUIRED_BEFORE_VENUE_DEPENDENT_PORTFOLIO_USE",
        runtime_requirement="NO_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        replay_paper_requirement="REPLAY_PAPER_REQUIRED_BEFORE_ADVANTAGE_OR_PROMOTION_CLAIM",
        risk_gate_requirement="RISK_GATE_REQUIRED_BEFORE_FUTURE_LIVE_USE",
        sizing_gate_requirement="SIZING_GATE_REQUIRED_BEFORE_FUTURE_LIVE_USE",
        latency_gate_requirement="LATENCY_GATE_REQUIRED_BEFORE_FUTURE_LIVE_PATH_USE",
        validation_gate_requirement="PORTFOLIO_COMPARATOR_FALLBACK_VALIDATION_REQUIRED",
        doctrine_terms=(*COMMON_DOCTRINE, *QUANTUM_DOCTRINE, "portfolio optimization"),
        derivation_summary=(
            "Derived from portfolio optimization, parameter-stack selection, comparator, "
            "fallback, risk, sizing, and execution-latency gate doctrines."
        ),
    ),
)

ALL_FAMILY_SPECS = (*FAMILY_SPECS, *QUANTUM_FAMILY_SPECS)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def serialize_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_json(value), encoding="utf-8")


def _family_from_spec(spec: FamilySpec, *, synthetic: bool = False) -> dict[str, Any]:
    quantum_family = spec.name in QUANTUM_OR_COMPATIBLE_FAMILY_NAMES
    description = (
        f"Synthetic fixture for {spec.name} preserving deterministic consumption, "
        "emission, role, gate, owner override, and quantum boundary fields."
        if synthetic
        else spec.description
    )
    derivation = (
        "Synthetic valid fixture derived from the master-plan doctrine search terms "
        "and existing agent charter role set."
        if synthetic
        else spec.derivation_summary
    )
    return {
        "algorithm_family_id": FAMILY_IDS[spec.name],
        "algorithm_family_name": spec.name,
        "algorithm_family_description": description,
        "family_category": spec.category,
        "classical_or_quantum": spec.classical_or_quantum,
        "formula_class": spec.formula_class,
        "formula_expression_profile": spec.expression_profile,
        "formula_authority_class": spec.authority_class,
        "formula_default_policy": FORMULA_DEFAULT_POLICY,
        "formula_value_range_policy": FORMULA_VALUE_RANGE_POLICY,
        "input_parameter_families": list(spec.input_parameters),
        "output_signal_type": spec.output_signal_type,
        "output_artifact_types": list(spec.output_artifacts),
        "authorized_agent_roles": list(spec.roles),
        "authorized_consumer_classes": list(spec.consumers),
        "trade_context_applicability": list(spec.trade_contexts),
        "latency_class": spec.latency_class,
        "risk_class": spec.risk_class,
        "capital_class": spec.capital_class,
        "market_context_scope": list(spec.market_context),
        "platform_scope": list(spec.platform_scope),
        "optimizer_compatibility": list(spec.optimizer_compatibility),
        "quantum_applicability": list(spec.quantum_applicability),
        "quantum_algorithm_family_access": list(spec.quantum_algorithm_access),
        "quantum_parameter_family_access": list(spec.quantum_parameter_access),
        "deterministic_selection_role": spec.deterministic_role,
        "scoring_ranking_role": spec.scoring_role,
        "quantum_classical_arbitration_role": spec.arbitration_role,
        "strongest_classical_comparator_required": quantum_family,
        "fallback_bundle_required": quantum_family,
        "replay_paper_evidence_required_before_advantage_claim": True,
        "live_evidence_required_before_profit_claim": True,
        "runtime_live_order_authority_created": False,
        "direct_order_submission_allowed": False,
        "execution_router_required_for_live_order_path": True,
        "owner_override_supported": True,
        "owner_override_satisfaction_basis": OWNER_OVERRIDE_SATISFACTION_BASIS,
        "owner_quantum_priority_supported": quantum_family,
        "owner_can_force_quantum_priority": quantum_family,
        "agent_binding_required_before_consumption": True,
        "consumer_gate_required_before_consumption": True,
        "source_evidence_requirement_class": spec.source_requirement,
        "connector_requirement_class": spec.connector_requirement,
        "runtime_resolver_requirement_class": spec.runtime_requirement,
        "replay_paper_requirement_class": spec.replay_paper_requirement,
        "risk_gate_requirement_class": spec.risk_gate_requirement,
        "sizing_gate_requirement_class": spec.sizing_gate_requirement,
        "latency_gate_requirement_class": spec.latency_gate_requirement,
        "validation_gate_requirement_class": spec.validation_gate_requirement,
        "master_plan_doctrine_terms_used": list(spec.doctrine_terms),
        "master_plan_family_derivation_summary": derivation,
        "agent_charter_roles_validated": list(spec.roles),
        "final_qtt_internal_status": FINAL_STATUS,
    }


def build_registry(*, synthetic: bool = False) -> dict[str, Any]:
    registry = {field: TOP_CONST_EXPECTATIONS[field] for field in TOP_FIELDS if field != "algorithm_families"}
    registry["algorithm_families"] = [
        _family_from_spec(spec, synthetic=synthetic) for spec in ALL_FAMILY_SPECS
    ]
    if synthetic:
        registry["execution"] = "DISABLED"
        registry["mode"] = "SOURCE_REQUIRED"
    return registry


def build_report(
    registry: dict[str, Any],
    *,
    agent_roles: set[str] | None = None,
    repo_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    agent_roles = set(AGENT_ROLE_ORDER) if agent_roles is None else agent_roles
    root = pathlib.Path(".") if repo_root is None else repo_root
    families = [
        family for family in registry.get("algorithm_families", []) if isinstance(family, dict)
    ]
    required_names = set(FAMILY_ORDER)
    present_names = {
        str(family.get("algorithm_family_name"))
        for family in families
        if isinstance(family.get("algorithm_family_name"), str)
    }
    quantum_families = [
        family
        for family in families
        if family.get("algorithm_family_name") in QUANTUM_OR_COMPATIBLE_FAMILY_NAMES
    ]
    false_boundary_values = {
        field: registry.get(field) is False for field in FALSE_TOP_FLAGS
    }
    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_family_substance": MASTER_PLAN.as_posix(),
        "agent_charter_registry_dependency": AGENT_CHARTER_REGISTRY.as_posix(),
        "master_plan_followed_as_controlling_doctrine": True,
        "agent_charter_registry_used_for_role_validation": True,
        "existing_pr_patterns_used_for_style_only": True,
        "pr65_is_scope_boundary_not_algorithm_authority": True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "algorithm_family_count": len(families),
        "required_algorithm_family_count": len(FAMILY_ORDER),
        "required_algorithm_families_present_count": len(required_names & present_names),
        "missing_algorithm_family_count": len(required_names - present_names),
        "classical_algorithm_family_count": sum(
            1 for family in families if family.get("classical_or_quantum") == "CLASSICAL"
        ),
        "quantum_or_quantum_compatible_algorithm_family_count": len(quantum_families),
        "families_with_formula_class_count": sum(1 for family in families if family.get("formula_class")),
        "families_with_formula_expression_profile_count": sum(
            1 for family in families if family.get("formula_expression_profile")
        ),
        "families_with_authorized_agent_roles_count": sum(
            1 for family in families if family.get("authorized_agent_roles")
        ),
        "families_with_valid_agent_roles_count": sum(
            1
            for family in families
            if family.get("authorized_agent_roles")
            and all(role in agent_roles for role in family.get("authorized_agent_roles", []))
        ),
        "families_with_input_parameter_families_count": sum(
            1 for family in families if family.get("input_parameter_families")
        ),
        "families_with_output_signal_type_count": sum(
            1 for family in families if family.get("output_signal_type")
        ),
        "families_with_trade_context_applicability_count": sum(
            1 for family in families if family.get("trade_context_applicability")
        ),
        "families_with_optimizer_compatibility_count": sum(
            1 for family in families if family.get("optimizer_compatibility")
        ),
        "families_with_quantum_applicability_count": sum(
            1 for family in families if family.get("quantum_applicability")
        ),
        "families_with_owner_override_supported_count": sum(
            1 for family in families if family.get("owner_override_supported") is True
        ),
        "quantum_forward_design_supported": registry.get("quantum_forward_design_supported") is True,
        "quantum_evidence_claim_created": registry.get("quantum_evidence_claim_created") is True,
        "alpha_evidence_claim_created": registry.get("alpha_evidence_claim_created") is True,
        "profit_evidence_claim_created": registry.get("profit_evidence_claim_created") is True,
        "latency_superiority_evidence_claim_created": registry.get("latency_superiority_evidence_claim_created") is True,
        "execution_superiority_evidence_claim_created": registry.get("execution_superiority_evidence_claim_created") is True,
        "quantum_hybrid_families_requiring_strongest_classical_comparator_count": sum(
            1 for family in quantum_families if family.get("strongest_classical_comparator_required") is True
        ),
        "quantum_hybrid_families_requiring_fallback_bundle_count": sum(
            1 for family in quantum_families if family.get("fallback_bundle_required") is True
        ),
        "quantum_hybrid_families_requiring_replay_paper_evidence_count": sum(
            1
            for family in quantum_families
            if family.get("replay_paper_evidence_required_before_advantage_claim") is True
        ),
        "families_requiring_live_evidence_before_profit_claim_count": sum(
            1 for family in families if family.get("live_evidence_required_before_profit_claim") is True
        ),
        "owner_quantum_priority_supported_count": sum(
            1 for family in families if family.get("owner_quantum_priority_supported") is True
        ),
        "owner_can_force_quantum_priority_count": sum(
            1 for family in families if family.get("owner_can_force_quantum_priority") is True
        ),
        "runtime_artifact_created": registry.get("runtime_artifact_created") is True,
        "live_artifact_created": registry.get("live_artifact_created") is True,
        "order_artifact_created": registry.get("order_artifact_created") is True,
        "source_acceptance_artifact_created": registry.get("source_acceptance_artifact_created") is True,
        "connector_binding_artifact_created": registry.get("connector_binding_artifact_created") is True,
        "runtime_resolver_snapshot_created": registry.get("runtime_resolver_snapshot_created") is True,
        "replay_execution_created": registry.get("replay_execution_created") is True,
        "paper_execution_created": registry.get("paper_execution_created") is True,
        "quantum_backend_artifact_created": registry.get("quantum_backend_artifact_created") is True,
        "bundle_file_present": (root / CANONICAL_BUNDLE).exists(),
        "bundle_sha_present": (root / CANONICAL_BUNDLE_SHA).exists(),
        "uses_pr_number_as_authority": registry.get("uses_pr_number_as_authority") is True
        or _uses_pr_number_as_authority_values(registry),
        "agent_algorithm_binding_created": registry.get("agent_algorithm_binding_created") is True,
        "agent_algorithm_consumer_gate_created": registry.get("agent_algorithm_consumer_gate_created") is True,
        "final_ready": registry.get("final_ready") is True,
        "authority_boundary_all_false": all(false_boundary_values.values()),
    }
    return report


def build_schema() -> dict[str, Any]:
    string_schema = {"type": "string", "minLength": 1}
    array_schema = {"type": "array", "minItems": 1, "items": string_schema}
    family_properties: dict[str, Any] = {}
    for field in FAMILY_FIELDS:
        if field in ARRAY_FIELDS:
            family_properties[field] = array_schema
        elif field in {
            "strongest_classical_comparator_required",
            "fallback_bundle_required",
            "owner_quantum_priority_supported",
            "owner_can_force_quantum_priority",
        }:
            family_properties[field] = {"type": "boolean"}
        elif field in {
            "replay_paper_evidence_required_before_advantage_claim",
            "live_evidence_required_before_profit_claim",
            "execution_router_required_for_live_order_path",
            "owner_override_supported",
            "agent_binding_required_before_consumption",
            "consumer_gate_required_before_consumption",
        }:
            family_properties[field] = {"const": True}
        elif field in {"runtime_live_order_authority_created", "direct_order_submission_allowed"}:
            family_properties[field] = {"const": False}
        else:
            family_properties[field] = string_schema
    family_properties["algorithm_family_id"] = {"enum": [FAMILY_IDS[name] for name in FAMILY_ORDER]}
    family_properties["algorithm_family_name"] = {"enum": list(FAMILY_ORDER)}
    family_properties["formula_expression_profile"] = {"enum": list(FORMULA_EXPRESSION_PROFILES)}
    family_properties["formula_authority_class"] = {"enum": list(FORMULA_AUTHORITY_CLASSES)}
    family_properties["formula_default_policy"] = {"const": FORMULA_DEFAULT_POLICY}
    family_properties["formula_value_range_policy"] = {"const": FORMULA_VALUE_RANGE_POLICY}
    family_properties["owner_override_satisfaction_basis"] = {
        "const": OWNER_OVERRIDE_SATISFACTION_BASIS
    }
    family_properties["final_qtt_internal_status"] = {"const": FINAL_STATUS}
    family_properties["authorized_agent_roles"] = {
        "type": "array",
        "minItems": 1,
        "items": {"$ref": "#/$defs/agent_role"},
    }
    family_properties["agent_charter_roles_validated"] = {
        "type": "array",
        "minItems": 1,
        "items": {"$ref": "#/$defs/agent_role"},
    }

    top_properties: dict[str, Any] = {}
    for field, expected in TOP_CONST_EXPECTATIONS.items():
        top_properties[field] = {"const": expected}
    top_properties["execution"] = {"const": "DISABLED"}
    top_properties["mode"] = {"const": "SOURCE_REQUIRED"}
    top_properties["algorithm_families"] = {
        "type": "array",
        "minItems": len(FAMILY_ORDER),
        "maxItems": len(FAMILY_ORDER),
        "uniqueItems": True,
        "items": {"$ref": "#/$defs/algorithm_family"},
    }
    report_properties: dict[str, Any] = {}
    for field in REPORT_FIELDS:
        if field in {
            "report_type",
            "generated_at_utc",
            "source_of_family_substance",
            "agent_charter_registry_dependency",
            "architecture_emphasis",
        }:
            report_properties[field] = {"type": "string"}
        elif field in {
            "deterministic_output",
            "master_plan_followed_as_controlling_doctrine",
            "agent_charter_registry_used_for_role_validation",
            "existing_pr_patterns_used_for_style_only",
            "pr65_is_scope_boundary_not_algorithm_authority",
            "quantum_forward_design_supported",
            "quantum_evidence_claim_created",
            "alpha_evidence_claim_created",
            "profit_evidence_claim_created",
            "latency_superiority_evidence_claim_created",
            "execution_superiority_evidence_claim_created",
            "runtime_artifact_created",
            "live_artifact_created",
            "order_artifact_created",
            "source_acceptance_artifact_created",
            "connector_binding_artifact_created",
            "runtime_resolver_snapshot_created",
            "replay_execution_created",
            "paper_execution_created",
            "quantum_backend_artifact_created",
            "bundle_file_present",
            "bundle_sha_present",
            "uses_pr_number_as_authority",
            "agent_algorithm_binding_created",
            "agent_algorithm_consumer_gate_created",
            "final_ready",
            "authority_boundary_all_false",
        }:
            report_properties[field] = {"type": "boolean"}
        else:
            report_properties[field] = {"type": "integer"}
    report_properties["report_type"] = {"const": REPORT_TYPE}
    report_properties["deterministic_output"] = {"const": True}
    report_properties["generated_at_utc"] = {"const": DETERMINISTIC_GENERATED_AT}
    report_properties["source_of_family_substance"] = {"const": MASTER_PLAN.as_posix()}
    report_properties["agent_charter_registry_dependency"] = {
        "const": AGENT_CHARTER_REGISTRY.as_posix()
    }
    report_properties["architecture_emphasis"] = {"const": ARCHITECTURE_EMPHASIS}

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://qtt.local/schemas/algorithms/qtt_algorithm_formula_family_registry.schema.json",
        "title": "QTT Algorithm Formula Family Registry",
        "description": (
            "Static deterministic institutional QTT algorithm and formula family "
            "registry schema. It defines family duties, symbolic formula profiles, "
            "agent role compatibility, owner override support, deterministic ranking, "
            "quantum-forward arbitration, and no-evidence/no-runtime boundaries."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": top_properties,
        "required": list(TOP_FIELDS),
        "$defs": {
            "agent_role": {"enum": list(AGENT_ROLE_ORDER)},
            "algorithm_family_id": {"enum": [FAMILY_IDS[name] for name in FAMILY_ORDER]},
            "algorithm_family_name": {"enum": list(FAMILY_ORDER)},
            "algorithm_family": {
                "type": "object",
                "additionalProperties": False,
                "properties": family_properties,
                "required": list(FAMILY_FIELDS),
            },
            "algorithm_formula_family_report": {
                "type": "object",
                "additionalProperties": False,
                "properties": report_properties,
                "required": list(REPORT_FIELDS),
            },
        },
    }


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is invalid: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError(f"registry must contain an object: {path}")
        return value
    return load_yaml_subset(path)


def _load_registry(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"registry file is missing: {path}"]
    try:
        return load_registry(path), []
    except (json.JSONDecodeError, RegistryParseError, ValueError) as exc:
        return None, [f"registry file is invalid: {path}: {exc}"]


def _load_agent_roles(path: pathlib.Path) -> tuple[set[str], list[str]]:
    registry, failures = _load_registry(path)
    if registry is None:
        return set(), failures
    charters = registry.get("agent_charters")
    if not isinstance(charters, list):
        return set(), ["agent charter registry must contain agent_charters"]
    roles = {
        charter.get("agent_role")
        for charter in charters
        if isinstance(charter, dict) and isinstance(charter.get("agent_role"), str)
    }
    if not roles:
        return set(), ["agent charter registry has no agent roles"]
    return roles, []


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: Sequence[str],
    label: str,
) -> list[str]:
    expected = set(expected_fields)
    failures: list[str] = []
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _walk_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return values
    return [value]


def _uses_pr_number_as_authority_values(value: Any) -> bool:
    for item in _walk_values(value):
        if isinstance(item, str) and PR_NUMBER_PATTERN.search(item):
            return True
    return False


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(TOP_FIELDS):
        failures.append("schema.required must match top-level registry fields")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    if defs.get("agent_role", {}).get("enum") != list(AGENT_ROLE_ORDER):
        failures.append("schema.$defs.agent_role must contain exact agent roles")
    if defs.get("algorithm_family_id", {}).get("enum") != [
        FAMILY_IDS[name] for name in FAMILY_ORDER
    ]:
        failures.append("schema.$defs.algorithm_family_id must contain exact family ids")
    if defs.get("algorithm_family_name", {}).get("enum") != list(FAMILY_ORDER):
        failures.append("schema.$defs.algorithm_family_name must contain exact family order")
    family_def = defs.get("algorithm_family")
    if not isinstance(family_def, dict):
        failures.append("schema.$defs.algorithm_family must be an object")
    elif family_def.get("required") != list(FAMILY_FIELDS):
        failures.append("schema.$defs.algorithm_family.required must match family fields")
    report_def = defs.get("algorithm_formula_family_report")
    if not isinstance(report_def, dict):
        failures.append("schema.$defs.algorithm_formula_family_report must be an object")
    elif report_def.get("required") != list(REPORT_FIELDS):
        failures.append("schema report required fields must match report fields")
    return failures


def _validate_top_level(
    value: dict[str, Any],
    *,
    label: str,
    schema: dict[str, Any] | None,
) -> list[str]:
    expected_fields = (
        (*TOP_FIELDS, *FIXTURE_EXTRA_FIELDS) if label == "fixture" else TOP_FIELDS
    )
    failures = _require_exact_fields(value, expected_fields, label)
    for field, expected in TOP_CONST_EXPECTATIONS.items():
        if value.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected!r}")
    if label == "fixture":
        if value.get("mode") != "SOURCE_REQUIRED":
            failures.append("fixture.mode must be SOURCE_REQUIRED")
        if value.get("execution") != "DISABLED":
            failures.append("fixture.execution must be DISABLED")
    if schema is not None:
        failures.extend(validate_json_schema_subset(value, schema))
    return failures


def _validate_family(
    family: dict[str, Any],
    *,
    index: int,
    agent_roles: set[str],
) -> list[str]:
    label = f"algorithm_families[{index}]"
    failures = _require_exact_fields(family, FAMILY_FIELDS, label)
    for field in ARRAY_FIELDS:
        value = family.get(field)
        if not isinstance(value, list) or not value:
            failures.append(f"{label}.{field} must be a non-empty array")
        elif not all(isinstance(item, str) and item.strip() for item in value):
            failures.append(f"{label}.{field} must contain only non-empty strings")
    for field in FAMILY_FIELDS:
        if field in ARRAY_FIELDS or isinstance(family.get(field), bool):
            continue
        value = family.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{label}.{field} must be a non-empty string")
    roles = family.get("authorized_agent_roles", [])
    for role in roles if isinstance(roles, list) else []:
        if role not in agent_roles:
            failures.append(f"{label}.authorized_agent_roles has unknown role {role}")
    if family.get("agent_charter_roles_validated") != roles:
        failures.append(f"{label}.agent_charter_roles_validated must match authorized_agent_roles")
    if family.get("formula_default_policy") != FORMULA_DEFAULT_POLICY:
        failures.append(f"{label}.formula_default_policy is invalid")
    if family.get("formula_value_range_policy") != FORMULA_VALUE_RANGE_POLICY:
        failures.append(f"{label}.formula_value_range_policy is invalid")
    if family.get("formula_authority_class") not in FORMULA_AUTHORITY_CLASSES:
        failures.append(f"{label}.formula_authority_class is invalid")
    if family.get("formula_expression_profile") not in FORMULA_EXPRESSION_PROFILES:
        failures.append(f"{label}.formula_expression_profile is invalid")
    if family.get("owner_override_supported") is not True:
        failures.append(f"{label}.owner_override_supported must be true")
    if family.get("owner_override_satisfaction_basis") != OWNER_OVERRIDE_SATISFACTION_BASIS:
        failures.append(f"{label}.owner_override_satisfaction_basis is invalid")
    for field in (
        "runtime_live_order_authority_created",
        "direct_order_submission_allowed",
    ):
        if family.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    for field in (
        "live_evidence_required_before_profit_claim",
        "execution_router_required_for_live_order_path",
        "agent_binding_required_before_consumption",
        "consumer_gate_required_before_consumption",
    ):
        if family.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    if family.get("final_qtt_internal_status") != FINAL_STATUS:
        failures.append(f"{label}.final_qtt_internal_status is invalid")
    for field, value in family.items():
        if field == "algorithm_family_id":
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str) and NUMERIC_RANGE_PATTERN.search(item):
                failures.append(f"{label}.{field} claims numeric range without authority")
    return failures


def _validate_families(
    value: dict[str, Any],
    *,
    label: str,
    agent_roles: set[str],
) -> list[str]:
    families = value.get("algorithm_families")
    if not isinstance(families, list):
        return [f"{label}.algorithm_families must be a list"]
    failures: list[str] = []
    if len(families) != len(FAMILY_ORDER):
        failures.append(f"{label}.algorithm_families must contain exactly {len(FAMILY_ORDER)} families")
    names: list[str] = []
    ids: list[str] = []
    for index, expected_name in enumerate(FAMILY_ORDER):
        if index >= len(families):
            continue
        family = families[index]
        if not isinstance(family, dict):
            failures.append(f"{label}.algorithm_families[{index}] must be an object")
            continue
        names.append(family.get("algorithm_family_name"))
        ids.append(family.get("algorithm_family_id"))
        if family.get("algorithm_family_name") != expected_name:
            failures.append(
                f"{label}.algorithm_families[{index}].algorithm_family_name must be {expected_name}"
            )
        if family.get("algorithm_family_id") != FAMILY_IDS[expected_name]:
            failures.append(
                f"{label}.algorithm_families[{index}].algorithm_family_id must be {FAMILY_IDS[expected_name]}"
            )
        failures.extend(_validate_family(family, index=index, agent_roles=agent_roles))
    if len(set(names)) != len(names):
        failures.append(f"{label}.algorithm_families must have unique algorithm_family_name values")
    if len(set(ids)) != len(ids):
        failures.append(f"{label}.algorithm_families must have unique algorithm_family_id values")

    family_by_name = {
        family.get("algorithm_family_name"): family
        for family in families
        if isinstance(family, dict)
    }
    for name in CLASSICAL_FAMILY_NAMES:
        if family_by_name.get(name, {}).get("classical_or_quantum") != "CLASSICAL":
            failures.append(f"{label}.{name} must be classical")
    for name in QUANTUM_OR_COMPATIBLE_FAMILY_NAMES:
        family = family_by_name.get(name, {})
        if family.get("classical_or_quantum") == "CLASSICAL":
            failures.append(f"{label}.{name} must be quantum or quantum-compatible")
        for field in (
            "strongest_classical_comparator_required",
            "fallback_bundle_required",
            "replay_paper_evidence_required_before_advantage_claim",
            "owner_quantum_priority_supported",
            "owner_can_force_quantum_priority",
        ):
            if family.get(field) is not True:
                failures.append(f"{label}.{name}.{field} must be true")
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    report_schema = defs.get("algorithm_formula_family_report")
    if not isinstance(report_schema, dict):
        return ["schema report definition is missing"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_15_fields = (
        "algorithm_family_count",
        "required_algorithm_family_count",
        "required_algorithm_families_present_count",
        "families_with_formula_class_count",
        "families_with_formula_expression_profile_count",
        "families_with_authorized_agent_roles_count",
        "families_with_valid_agent_roles_count",
        "families_with_input_parameter_families_count",
        "families_with_output_signal_type_count",
        "families_with_trade_context_applicability_count",
        "families_with_optimizer_compatibility_count",
        "families_with_quantum_applicability_count",
        "families_with_owner_override_supported_count",
        "families_requiring_live_evidence_before_profit_claim_count",
    )
    for field in expected_15_fields:
        if report.get(field) != len(FAMILY_ORDER):
            failures.append(f"report.{field} must be {len(FAMILY_ORDER)}")
    exact_counts = {
        "missing_algorithm_family_count": 0,
        "classical_algorithm_family_count": len(CLASSICAL_FAMILY_NAMES),
        "quantum_or_quantum_compatible_algorithm_family_count": len(QUANTUM_OR_COMPATIBLE_FAMILY_NAMES),
    }
    for field, expected in exact_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    true_fields = (
        "deterministic_output",
        "master_plan_followed_as_controlling_doctrine",
        "agent_charter_registry_used_for_role_validation",
        "existing_pr_patterns_used_for_style_only",
        "pr65_is_scope_boundary_not_algorithm_authority",
        "quantum_forward_design_supported",
        "authority_boundary_all_false",
    )
    for field in true_fields:
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    false_fields = (
        "quantum_evidence_claim_created",
        "alpha_evidence_claim_created",
        "profit_evidence_claim_created",
        "latency_superiority_evidence_claim_created",
        "execution_superiority_evidence_claim_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "bundle_file_present",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "agent_algorithm_binding_created",
        "agent_algorithm_consumer_gate_created",
        "final_ready",
    )
    for field in false_fields:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    for field in (
        "quantum_hybrid_families_requiring_strongest_classical_comparator_count",
        "quantum_hybrid_families_requiring_fallback_bundle_count",
        "quantum_hybrid_families_requiring_replay_paper_evidence_count",
        "owner_quantum_priority_supported_count",
        "owner_can_force_quantum_priority_count",
    ):
        if report.get(field, 0) < len(QUANTUM_OR_COMPATIBLE_FAMILY_NAMES):
            failures.append(f"report.{field} must be at least {len(QUANTUM_OR_COMPATIBLE_FAMILY_NAMES)}")
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must use deterministic sentinel")
    if report.get("source_of_family_substance") != MASTER_PLAN.as_posix():
        failures.append("report.source_of_family_substance must point to master plan")
    if report.get("agent_charter_registry_dependency") != AGENT_CHARTER_REGISTRY.as_posix():
        failures.append("report.agent_charter_registry_dependency is invalid")
    if report.get("architecture_emphasis") != ARCHITECTURE_EMPHASIS:
        failures.append("report.architecture_emphasis is invalid")
    if report != json.loads(serialize_json(report)):
        failures.append("report serialization must be deterministic")
    return failures


def _master_plan_has_no_diff(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--", MASTER_PLAN.as_posix()],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return [f"git diff for master plan failed: {completed.stderr.strip()}"]
    if completed.stdout.strip():
        return [f"{MASTER_PLAN.as_posix()} must have no diff"]
    return []


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    registry_path: pathlib.Path,
    fixture_path: pathlib.Path,
    agent_registry_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json(root / schema_path)
    registry, registry_failures = _load_registry(root / registry_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    agent_roles, agent_role_failures = _load_agent_roles(root / agent_registry_path)
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)
    failures.extend(agent_role_failures)

    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if registry is not None:
        failures.extend(_validate_top_level(registry, label="registry", schema=schema))
        failures.extend(_validate_families(registry, label="registry", agent_roles=agent_roles))
        if _uses_pr_number_as_authority_values(registry):
            failures.append("registry must not use a delivery label as authority")
    if fixture is not None:
        failures.extend(_validate_top_level(fixture, label="fixture", schema=schema))
        failures.extend(_validate_families(fixture, label="fixture", agent_roles=agent_roles))
        if _uses_pr_number_as_authority_values(fixture):
            failures.append("fixture must not use a delivery label as authority")

    failures.extend(
        validate_current_atomicrows_bundle_state(
            root,
            label="QTT algorithm formula family registry",
        )
    )
    failures.extend(_master_plan_has_no_diff(root))

    report = build_report(registry or {}, agent_roles=agent_roles, repo_root=root)
    second_report = build_report(registry or {}, agent_roles=agent_roles, repo_root=root)
    if report != second_report:
        failures.append("generated algorithm formula family report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: static algorithm formula family registry is not production-ready"
        )

    if output_path is not None and not failures:
        write_json(root / output_path, report)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def write_static_artifacts(repo_root: pathlib.Path) -> None:
    root = repo_root.resolve()
    schema = build_schema()
    registry = build_registry(synthetic=False)
    fixture = build_registry(synthetic=True)
    report = build_report(registry, agent_roles=set(AGENT_ROLE_ORDER), repo_root=root)
    write_json(root / DEFAULT_SCHEMA, schema)
    write_json(root / DEFAULT_REGISTRY, registry)
    write_json(root / DEFAULT_FIXTURE, fixture)
    write_json(root / DEFAULT_REPORT, report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev", "final"], default="dev")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--agent-registry", default=str(AGENT_CHARTER_REGISTRY))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    parser.add_argument("--write-static-artifacts", action="store_true")
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    if args.write_static_artifacts:
        write_static_artifacts(repo_root)

    result = validate(
        mode=args.mode,
        repo_root=repo_root,
        schema_path=pathlib.Path(args.schema),
        registry_path=pathlib.Path(args.registry),
        fixture_path=pathlib.Path(args.fixture),
        agent_registry_path=pathlib.Path(args.agent_registry),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"families={report.get('algorithm_family_count', 0)} "
            f"quantum_or_compatible="
            f"{report.get('quantum_or_quantum_compatible_algorithm_family_count', 0)} "
            f"final_ready={report.get('final_ready', None)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
