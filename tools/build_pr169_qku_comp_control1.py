#!/usr/bin/env python3
"""Build the single PR169 CONTROL1 decision-computation registry.

This is a build-time writer only.  It imports immutable RP5C identity and
lineage facts, registers the explicit PR162D-R2A callable inventory, and
preserves the owner-supplied 213 requirements without inheriting the reverted
implementation's execution or equivalence claims.  It never reads private
state, executes connectors or QPUs, releases orders, or promotes a mode.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence


REGISTRY_SCHEMA_VERSION = "1.0"
BUILDER_NAME = "tools/build_pr169_qku_comp_control1.py"
VALIDATOR_NAME = "tools/validate_pr169_qku_comp_control1.py"
GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_qku_comp_control1")

RP5C_PREFIX = Path("docs/master_plan/generated/rp5c")
RP5C_DEDUPE = RP5C_PREFIX / "identity_deduplication_ledger.jsonl"
RP5C_LINEAGE = RP5C_PREFIX / "qku_formula_identity_lineage.jsonl"
RP5C_CANONICAL_LIBRARY = RP5C_PREFIX / "immutable_qku_formula_library.jsonl"
RP5C_LIBRARIES = (
    RP5C_PREFIX / "immutable_qku_library.jsonl",
    RP5C_PREFIX / "immutable_formula_library.jsonl",
    RP5C_PREFIX / "immutable_qku_formula_library.jsonl",
)
RP5C_GROUP_CUSTODY_KEY_VERSION = "RP5C_SOURCE_GROUP_CUSTODY_KEY_V1"
RP5C_GROUP_KEY_FIELDS = (
    "identity_type",
    "qku_id",
    "formula_id",
    "formula_variant_id",
    "formula_expression_ref",
    "plugin_ref",
)
PR165_D2_ROSTER = Path(
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"
)

EXPECTED_RP5C_IDENTITIES = 10_189
EXPECTED_FORMULA_IMPLEMENTATIONS = 61
EXPECTED_ALGORITHM_IMPLEMENTATIONS = 30
EXPECTED_QUANTUM_FORMULATIONS = 25
EXPECTED_QUANTUM_CALLABLE_FAMILIES = 9
EXPECTED_OWNER_REQUIREMENTS = 213

_SEMANTIC_CORE_FIELDS = (
    "component_kind",
    "family_template_ref_or_null",
    "complete_mathematical_or_procedural_definition",
    "objective_sense_or_null",
    "assumptions",
    "hard_constraints",
    "soft_preferences",
    "domain_and_boundary_behavior",
    "state_and_time_semantics",
    "input_schema",
    "output_schema",
    "units_and_bases",
    "output_accounting_class",
    "missing_stale_nonfinite_behavior",
    "precision_and_rounding",
    "parameter_schema_and_default_provenance",
    "requirements",
    "latency_class",
    "risk_materiality",
    "failure_domain_tags",
    "classical_fallback",
    "quantum",
)

# This inventory is owner-supplied requirement evidence.  Only card identity,
# family, and requested name were inspected from the negative-regression PR;
# none of its callable, alias, PASS, route, or implementation claims survive.
_OWNER_REQUIREMENT_TEXT = (
    "A01=TOTAL_REALIZED_NET_CASH A02=BRANCH_NET_CASH A03=EXPECTED_NET_CASH_SCENARIO A04=ROBUST_NET_CASH_INTERVAL A05=NET_CASH_LCB_UCB A06=NET_CASH_VELOCITY A07=CAPITAL_TIME_EFFICIENCY A08=REQUIRED_EXIT_PROFIT A09=DEPTH_WALK_SELL_PROCEEDS A10=DEPTH_WALK_BUY_COST A11=EXECUTABLE_EXIT_NET_CASH A12=FILL_ADJUSTED_EXECUTABLE_NET_CASH A13=PARTIAL_HARVEST_NET_CASH A14=PNL_STATE_CLASSIFICATION A15=EXIT_NOW_VALUE A16=CONTINUE_HOLDING_VALUE A17=HOLD_TO_SETTLEMENT_VALUE A18=HEDGE_OFFSET_VALUE A19=REVERSE_VALUE A20=FORWARD_ACTION_VALUE A21=CONTINUATION_HYSTERESIS A22=REENTRY_EDGE_HURDLE A23=CAPITAL_OPPORTUNITY_COST A24=RISK_RESERVE_HURDLE A25=NO_TRADE_MARGIN A26=CAMPAIGN_CASH_AGGREGATES A27=CAMPAIGN_CAPACITY_FRONTIER A28=CAMPAIGN_REMAINING_CAPACITY A29=EVIDENCE_STOP_STATISTICS A30=VENUE_FEE_GENERIC A31=FEE_CURVE_PRODUCT A32=MAKER_REBATE_SHARE A33=NET_QUOTE_UTILITY "
    "B01=IMPLEMENTATION_SHORTFALL B02=TCA_DECOMPOSITION_RECONCILIATION B03=EFFECTIVE_ARRIVAL_PRICE B04=REALIZED_SPREAD B05=SIGNED_MARKOUT B06=SPREAD_COST B07=DEPTH_IMPACT B08=LATENCY_DECAY_COST B09=FILL_SURVIVAL_HAZARD B10=QUEUE_AHEAD_DEPLETION B11=ORDERBOOK_IMBALANCE B12=MICROPRICE B13=ORDER_FLOW_IMBALANCE B14=HAWKES_INTENSITY_CANDIDATE B15=MAKER_TAKER_ROUTE_UTILITY B16=CANCEL_REPLACE_VALUE B17=AVELLANEDA_STOIKOV_RESERVATION_PRICE B18=AVELLANEDA_STOIKOV_HALF_SPREAD B19=INVENTORY_SKEW B20=RATE_LIMIT_BUDGET B21=ORDER_GROUP_ROLLING_USAGE "
    "C01=BRIER_SCORE C02=LOG_LOSS C03=EXPECTED_CALIBRATION_ERROR C04=CALIBRATION_SLOPE_INTERCEPT C05=WEIGHTED_EFFECTIVE_SAMPLE_SIZE C06=AUTOCORRELATION_EFFECTIVE_SAMPLE_SIZE C07=CLUSTER_EVENT_EFFECTIVE_SAMPLE_SIZE C08=DEPENDENCE_AWARE_BOOTSTRAP_LCB C09=ANYTIME_EVIDENCE_PROCESS C10=BENJAMINI_HOCHBERG_FDR C11=BENJAMINI_YEKUTIEL_FDR C12=PROBABILISTIC_SHARPE_RATIO C13=DEFLATED_SHARPE_RATIO C14=PBO_CSCV C15=WHITE_REALITY_CHECK C16=HANSEN_SPA C17=STEPM_MULTIPLE_COMPARISON C18=MODEL_CONFIDENCE_SET C19=PAIRED_CHALLENGER_DELTA C20=RANK_STABILITY C21=PROBABILITY_OF_POSITIVE_NET_CASH C22=MINIMUM_TRACK_RECORD_LENGTH C23=CONFORMAL_INTERVAL_CANDIDATE C24=TRIAL_FAMILY_EFFECTIVE_COUNT C25=DIFFERENTIAL_SHARPE "
    "D01=FINANCIAL_LOSS_CVAR D02=ROBUST_CVAR D03=MEAN_VARIANCE_UTILITY D04=MARGINAL_RISK_CONTRIBUTION D05=EXPOSURE_HERFINDAHL D06=DIVERSIFICATION_ENTROPY D07=CORRELATION_INTERACTION_PENALTY D08=FRACTIONAL_KELLY_ROBUST D09=MAX_DRAWDOWN D10=CAPITAL_UTILIZATION D11=PORTFOLIO_MARGINAL_UTILITY D12=CAPITAL_TIME_ROTATION D13=EVENT_EXPOSURE_NETTING D14=TIME_BUCKET_CAPITAL D15=ENTROPIC_RISK_CANDIDATE D16=DISTRIBUTIONALLY_ROBUST_UTILITY D17=LEXICOGRAPHIC_ECONOMIC_OBJECTIVE D18=EPSILON_CONSTRAINED_PARETO D19=CONDITION_SCOPED_SHRINKAGE D20=CHAMPION_CHALLENGER_REGRET D21=VALUE_OF_INFORMATION D22=EXPERIMENT_DESIGN_UTILITY D23=IPS_OFF_POLICY_VALUE D24=SNIPS_OFF_POLICY_VALUE D25=DOUBLY_ROBUST_POLICY_VALUE D26=NO_TRADE_RECOVERY_DISTANCE D27=REGIME_ROBUSTNESS D28=AGENT_DISAGREEMENT_VECTOR D29=PARETO_DOMINANCE D30=ADAPTIVE_SEARCH_BUDGET "
    "E01=COMPLETE_SET_BUY_MARGIN E02=COMPLETE_SET_SELL_MARGIN E03=OUTCOME_SUM_CONSISTENCY E04=COMPLEMENT_CONSISTENCY E05=LOGICAL_IMPLICATION E06=INTERSECTION_BOUND E07=DATE_MONOTONICITY E08=SUBSET_SUPERSET E09=CROSS_VENUE_PARITY_MARGIN E10=SIMULTANEOUS_FILL_PROBABILITY E11=BASKET_EXECUTABLE_UTILITY E12=LOGICAL_ARBITRAGE_HYPERGRAPH_OBJECTIVE "
    "F01=DISCRETE_TRADE_ALTERNATIVE_SELECTION F02=QUANTUM_ROBUST_ECONOMIC_OBJECTIVE F03=QUBO_CANONICAL F04=BQM_CANONICAL F05=QUBO_TO_ISING F06=COEFFICIENT_SCALING F07=PENALTY_SUFFICIENCY F08=ONE_HOT_CONSTRAINT F09=FIXED_CARDINALITY_CONSTRAINT F10=BOUNDED_BINARY_ENCODING F11=UNARY_ENCODING F12=MIXED_RADIX_ENCODING F13=GRAY_CODE_ENCODING F14=DOMAIN_WALL_ENCODING F15=QAOA_EXPECTATION F16=WARM_START_QAOA_ANGLE F17=VARIATIONAL_CVAR_AGGREGATOR F18=SAMPLE_SELECTION_MARGINAL F19=SAMPLE_PAIRWISE_COSELECTION F20=SOLUTION_ENTROPY F21=HAMMING_DIVERSITY F22=NEAR_OPTIMAL_CLUSTER_COUNT F23=SELECTION_OVERLAP F24=OBJECTIVE_GAP F25=ECONOMIC_UTILITY_GAP F26=CONSTRAINT_DISAGREEMENT F27=PORTFOLIO_EXPOSURE_DISAGREEMENT F28=TRADE_PLAN_DISAGREEMENT F29=COEFFICIENT_STRESS_SENSITIVITY F30=QUANTUM_SOLUTION_FRAGILITY F31=QUANTUM_REGIME_ROBUSTNESS F32=QUANTUM_ECONOMIC_UTILITY F33=QPU_IMPROVEMENT_PER_COST F34=QPU_IMPROVEMENT_PER_SECOND F35=QUANTUM_VALUE_OF_INFORMATION F36=QAE_NORMALIZED_EXPECTATION F37=QAE_TAIL_PROBABILITY F38=QAE_CVAR_CANDIDATE F39=FEASIBLE_SAMPLE_RATE F40=CHAIN_BREAK_FRACTION F41=TIME_TO_FIRST_FEASIBLE F42=TIME_TO_BEST F43=EMBEDDING_GAUGE_STABILITY F44=REVERSE_ANNEAL_IMPROVEMENT F45=POSTPROCESSING_IMPROVEMENT F46=QUANTUM_RESOURCE_ESTIMATE "
    "G01=SHRINKAGE_COVARIANCE G02=COMPONENT_CVAR G03=RISK_BUDGET_PARITY_OBJECTIVE G04=SQUARE_ROOT_MARKET_IMPACT_CANDIDATE G05=EXECUTION_SCHEDULE_MEAN_VARIANCE G06=CUSUM_DRIFT_STATISTIC G07=BAYESIAN_MODEL_AVERAGING_WEIGHT G08=ENTROPY_REGULARIZED_ALLOCATION G09=OPTIMIZATION_TARGET_SUCCESS_RATE G10=QUANTUM_TIME_TO_SOLUTION G11=MITIGATION_VARIANCE_OVERHEAD G12=NEYMAN_SHOT_ALLOCATION G13=BACKEND_CALIBRATION_DRIFT_VECTOR G14=PARETO_HYPERVOLUME_IMPROVEMENT "
    "H01=COHERENT_PROBABILITY_QP_PROJECTION H02=DATE_LADDER_ISOTONIC_PROJECTION H03=EXECUTABLE_BREAK_EVEN_PROBABILITY H04=CALIBRATED_EXECUTABLE_EDGE_LCB H05=LIQUIDITY_ADJUSTED_CVAR H06=WORST_CASE_REGRET H07=COMPETING_RISKS_FILL_CIF H08=FORMULATION_EQUIVALENCE_RESIDUAL H09=PENALTY_DOMINANCE_RATIO H10=QUANTUM_CONTRIBUTION_ATTRIBUTION H11=PROBLEM_FINGERPRINT_DISTANCE H12=VARIATIONAL_GRADIENT_SNR H13=QPU_RESULT_EXPIRY_PROBABILITY H14=SCENARIO_CASHFLOW_RECONCILIATION_RESIDUAL "
    "I01=AGENT_STAGE_QKU_UNIVERSE I02=AGENT_EXECUTABLE_QKU_UNIVERSE I03=CONTEXT_CANDIDATE_QKU_UNIVERSE I04=FORMULA_INPUT_RESOLUTION_COVERAGE I05=CONTEXT_RECIPE_SIMILARITY I06=RECIPE_PRIOR_UTILITY I07=FORMULA_RESULT_FRESHNESS I08=END_TO_END_DECISION_LATENCY I09=LATENCY_BUDGET_SLACK I10=FORMULA_WORK_ITEM_PRIORITY_VECTOR "
    "J01=WASSERSTEIN_ROBUST_UTILITY J02=CHANCE_CONSTRAINED_FEASIBILITY J03=DISTRIBUTION_SHIFT_TEST J04=LOG_DETERMINANT_DIVERSITY J05=RARE_EVENT_IMPORTANCE_SAMPLING J06=PRIMAL_DUAL_OPTIMALITY_CERTIFICATE J07=CERTIFIED_QUBO_SPARSIFICATION_QUANTIZATION J08=SYMMETRY_BREAKING_ORBIT_REDUCTION"
)


class BuildError(RuntimeError):
    """Fail-closed deterministic builder error."""


class _Deadline:
    def __init__(self, timeout_ms: int) -> None:
        if timeout_ms <= 0:
            raise BuildError("timeout_ms must be positive")
        self._deadline = time.monotonic() + timeout_ms / 1000.0

    def check(self, operation: str) -> None:
        if time.monotonic() > self._deadline:
            raise TimeoutError(f"CONTROL1 builder timeout during {operation}")


def _json_line(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"


def _stable_json_value(value: Any) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sorted_unique_values(values: Iterable[Any]) -> list[Any]:
    """Canonicalize only record collections whose order has no semantics."""

    by_value: dict[str, Any] = {}
    for value in values:
        copied = copy.deepcopy(value)
        by_value.setdefault(_stable_json_value(copied), copied)
    return [by_value[key] for key in sorted(by_value)]


def _normalize_compiler_candidate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Match the compiler's reuse normalization on the first admission.

    This is syntactic input normalization, not an admission or merge path.  It
    prevents a record first admitted by the private compiler from changing on
    the next identical batch solely because reuse canonicalizes unordered
    metadata collections.
    """

    normalized = copy.deepcopy(dict(record))
    normalized["origin_cohorts"] = sorted(
        {str(value) for value in normalized.get("origin_cohorts", [])}
    )
    for field_name in ("provenance", "relations"):
        normalized[field_name] = _sorted_unique_values(
            normalized.get(field_name, [])
        )
    uses = normalized.get("uses")
    if isinstance(uses, dict):
        for field_name in (
            "decision_roles",
            "decision_outputs",
            "market_family_tags",
            "qku_role_bindings",
            "consumer_class_tags",
        ):
            uses[field_name] = _sorted_unique_values(uses.get(field_name, []))
    definition = normalized.get("definition")
    if isinstance(definition, dict):
        for field_name in (
            "implementation_versions",
            "oracle_and_test_refs",
            "equivalence_proof_refs",
        ):
            definition[field_name] = _sorted_unique_values(
                definition.get(field_name, [])
            )
    bindings = normalized.get("bindings", [])
    if isinstance(bindings, list):
        normalized["bindings"] = sorted(
            bindings,
            key=lambda value: (
                str(value.get("binding_id", ""))
                if isinstance(value, Mapping)
                else "",
                _stable_json_value(value),
            ),
        )
    return normalized


def _iter_jsonl(path: Path, deadline: _Deadline) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        raise BuildError(f"required source is missing: {path.as_posix()}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 10_000 == 0:
                deadline.check(path.name)
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise BuildError(
                    f"invalid JSONL at {path.as_posix()}:{line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise BuildError(
                    f"non-object JSONL row at {path.as_posix()}:{line_number}"
                )
            yield value


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BuildError(f"required source is missing: {path.as_posix()}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"required object JSON source is invalid: {path.as_posix()}")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _owner_requirements() -> tuple[tuple[str, str, str], ...]:
    rows: list[tuple[str, str, str]] = []
    for token in _OWNER_REQUIREMENT_TEXT.split():
        card_id, semantic_key = token.split("=", 1)
        rows.append((card_id, semantic_key, card_id[0]))
    if len(rows) != EXPECTED_OWNER_REQUIREMENTS:
        raise BuildError(
            f"owner requirement inventory changed: {len(rows)} != {EXPECTED_OWNER_REQUIREMENTS}"
        )
    if len({card_id for card_id, _, _ in rows}) != len(rows):
        raise BuildError("owner requirement card IDs are not unique")
    return tuple(rows)


def _latency_class(source_value: str | None) -> str:
    return {
        "HOT_PATH_ELIGIBLE_CANDIDATE": "HOTPATH_CANDIDATE",
        "PRECOMPUTE_REQUIRED": "BATCH_PRECOMPUTE",
        "QUANTUM_BATCH_ONLY": "HOTPATH_FORBIDDEN",
    }.get(str(source_value), "OFFLINE_RESEARCH")


def _decision_roles(domain_family: str, *, quantum: bool = False) -> list[str]:
    if quantum:
        return ["QUANTUM_MAPPING_OR_COMPARATOR", "RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"]
    token = domain_family.lower()
    roles: list[str] = []
    if any(part in token for part in ("probability", "calibration", "expected_value")):
        roles.append("PROBABILITY_FAIR_VALUE_UNCERTAINTY")
    if any(part in token for part in ("latency", "slippage", "liquidity", "microstructure")):
        roles.append("LIQUIDITY_FILL_CAPACITY_AND_ADVERSE_SELECTION")
    if any(part in token for part in ("risk", "capital", "portfolio")):
        roles.append("PORTFOLIO_EVENT_VENUE_EXPOSURE")
    if any(part in token for part in ("cost", "fee", "tca")):
        roles.append("TCA_ACCOUNTING_AND_RECONCILIATION")
    if any(part in token for part in ("objective", "constraint", "solver", "selection")):
        roles.append("INTERNAL_SUPPORT")
    return sorted(set(roles or ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"]))


def _family_decision_roles(family: str) -> list[str]:
    return {
        "A": ["EXPECTED_NET_CASH", "EXECUTABLE_EXIT_OR_SETTLEMENT"],
        "B": ["TCA_ACCOUNTING_AND_RECONCILIATION", "LIQUIDITY_FILL_CAPACITY_AND_ADVERSE_SELECTION"],
        "C": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
        "D": ["PORTFOLIO_EVENT_VENUE_EXPOSURE", "NO_TRADE_OR_ALTERNATIVE_CAPITAL_USE"],
        "E": ["EXECUTABLE_ENTRY_ECONOMICS"],
        "F": ["QUANTUM_MAPPING_OR_COMPARATOR"],
        "G": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION", "QUANTUM_MAPPING_OR_COMPARATOR"],
        "H": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION", "QUANTUM_MAPPING_OR_COMPARATOR"],
        "I": ["INTERNAL_SUPPORT"],
        "J": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
    }[family]


def _blank_quantum() -> dict[str, Any]:
    return {
        "applicability_state": "NOT_APPLICABLE_OR_NOT_YET_PROVEN",
        "original_economic_problem_ref": None,
        "problem_family": None,
        "formulation_candidates": [],
        "selected_formulation_or_none": None,
        "variable_encoding": None,
        "objective_map": None,
        "constraint_map": None,
        "penalty_policy": None,
        "coefficient_scaling": None,
        "precision_and_quantization": None,
        "decomposition_or_embedding": None,
        "warm_start": None,
        "optimizer_and_version": None,
        "shots_reads_or_sampling_policy": None,
        "seed_resampling_policy": None,
        "inverse_map": None,
        "original_model_feasibility_check": None,
        "same_formulation_classical_comparator": None,
        "local_exact_or_small_instance_parity": None,
        "fallback": "DETERMINISTIC_CLASSICAL_FALLBACK_REQUIRED_IF_PROMOTED",
        "maturity_ceiling": "SPECIFIED",
    }


def _definition(
    *,
    display_name: str,
    description: str,
    component_kind: str,
    complete_definition: str,
    inputs: Sequence[Mapping[str, Any]] = (),
    outputs: Sequence[Mapping[str, Any]] = (),
    units: Mapping[str, Any] | None = None,
    requirements: Sequence[Mapping[str, Any]] = (),
    latency_class: str = "OFFLINE_RESEARCH",
    implementation_versions: Sequence[Mapping[str, Any]] = (),
    oracle_refs: Sequence[Mapping[str, Any] | str] = (),
    quantum: Mapping[str, Any] | None = None,
    inventory_class: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "display_name": display_name,
        "description": description,
        "component_kind": component_kind,
        "family_template_ref_or_null": None,
        "complete_mathematical_or_procedural_definition": complete_definition,
        "objective_sense_or_null": None,
        "assumptions": [],
        "hard_constraints": [],
        "soft_preferences": [],
        "domain_and_boundary_behavior": "CONTROL_PLANE_TYPED_VALIDATION_REQUIRED",
        "state_and_time_semantics": "STATELESS_SAME_REQUEST_UNLESS_SOURCE_PROCEDURE_DECLARES_OTHERWISE",
        "input_schema": [dict(item) for item in inputs],
        "output_schema": [dict(item) for item in outputs],
        "units_and_bases": dict(units or {}),
        "output_accounting_class": "NON_ACCOUNTING_UNLESS_OUTPUT_SCHEMA_EXPLICITLY_IDENTIFIES_ACCOUNTING",
        "missing_stale_nonfinite_behavior": "FAIL_CLOSED_AT_CONTROL_PLANE_BOUNDARY",
        "precision_and_rounding": "SOURCE_IMPLEMENTATION_PRECISION_WITH_EXPLICIT_CONTROL_PLANE_BOUNDARY_CONVERSION",
        "parameter_schema_and_default_provenance": [],
        "requirements": [dict(item) for item in requirements],
        "latency_class": latency_class,
        "risk_materiality": {
            "economic_materiality": "REQUIRES_CONTEXT_CLASSIFICATION",
            "complexity": "SOURCE_DECLARED",
            "data_dependency": "TYPED_INPUT_LOCK_REQUIRED",
            "latency_sensitivity": latency_class,
            "external_provider_dependency": False,
            "quantum_backend_dependency": False,
            "independent_validation_strength_required": "INDEPENDENT_ORACLE",
            "monitoring_revalidation_cadence": "BEFORE_ANY_PROMOTION",
        },
        "failure_domain_tags": ["MISSING_INPUT", "STALE_INPUT", "NONFINITE_INPUT", "DOMAIN_ERROR"],
        "classical_fallback": "FAIL_CLOSED_UNLESS_EXPLICIT_BINDING_FALLBACK_EXISTS",
        "quantum": dict(quantum or _blank_quantum()),
        "implementation_versions": [dict(item) for item in implementation_versions],
        "oracle_and_test_refs": [copy.deepcopy(item) for item in oracle_refs],
        "equivalence_proof_refs": [],
    }
    if inventory_class is not None:
        value["implementation_inventory_class"] = inventory_class
    return value


def _agent_access_policy(agent_ids: Sequence[str], *, compute: bool) -> dict[str, Any]:
    compute_roles = {
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
    }
    policies: dict[str, Any] = {}
    for agent_id in sorted(set(agent_ids)):
        operations = ["status", "explain"]
        if compute and agent_id in compute_roles:
            operations = ["resolve", "compute", "status", "explain"]
        policy: dict[str, Any] = {
            "control_plane_operations": operations,
            "mode_ceiling": "FIXTURE_NONLIVE",
            "order_release_authority": False,
            "source_truth_authority": False,
        }
        if agent_id in {"research_agent", "quantum_optimizer_agent"}:
            policy["research_operations"] = ["propose_batch_item"]
        policies[agent_id] = policy
    return policies


def _binding(
    component_id: str,
    *,
    binding_id: str,
    agent_ids: Sequence[str],
    implementation_version: str | None,
    exact_action: str | None,
    fixture_ref: str | None = None,
    requirements_ready: bool = False,
    oracle_ready: bool = False,
    dormant: bool = False,
) -> dict[str, Any]:
    implementation_ready = implementation_version is not None
    specification_ready = fixture_ref is not None
    readiness = {
        "specification": "PASS" if specification_ready else "REQUIRED",
        "implementation": "PASS" if implementation_ready else "REQUIRED",
        "inputs": "PASS" if fixture_ref else "REQUIRED",
        "requirements": "PASS" if requirements_ready else "REQUIRED",
        "oracle": "PASS" if oracle_ready else "REQUIRED",
        "context": "PASS" if fixture_ref else "REQUIRED",
        "evidence": "FIXTURE" if fixture_ref else "NONE",
        "authorization": "NOT_ELIGIBLE",
    }
    return {
        "binding_id": binding_id,
        "market": "MARKET_AGNOSTIC_RESEARCH_FIXTURE" if fixture_ref else "UNRESOLVED",
        "venue": "NO_VENUE",
        "context_selector": {
            "context_family": "IMMUTABLE_FIXTURE" if fixture_ref else "SOURCE_IDENTITY_REVIEW",
            "component_id": component_id,
        },
        "qku_binding_selector_or_null": None,
        "supported_modes": ["FIXTURE_NONLIVE"] if fixture_ref else [],
        "mode_state": (
            {
                "FIXTURE_NONLIVE": {
                    "evidence": "FIXTURE",
                    "authorization": "NOT_ELIGIBLE",
                }
            }
            if fixture_ref
            else {}
        ),
        "as_of_policy": "IMMUTABLE_FIXTURE" if fixture_ref else "NOT_RESOLVED",
        "selected_implementation_version": implementation_version,
        "binding_version": "1.0",
        "selected_parameter_policy": {
            "policy": "SOURCE_FIXTURE_VALUES_NOT_RUNTIME_DEFAULTS" if fixture_ref else "UNRESOLVED",
            "default_provenance": fixture_ref,
            "optimizer_version": None,
            "calibration_ref": None,
            "seed_policy": "DETERMINISTIC_NO_SEED" if fixture_ref else None,
            "fallback": "FAIL_CLOSED",
            "revalidation": "REQUIRED_BEFORE_PROMOTION",
        },
        "input_source_bindings": ([{"fixture_ref": fixture_ref}] if fixture_ref else []),
        "venue_semantic_version": None,
        "portfolio_state_requirement": "NONE_FOR_FIXTURE" if fixture_ref else "UNRESOLVED",
        "cash_state_requirement": "NONE_FOR_FIXTURE" if fixture_ref else "UNRESOLVED",
        "freshness_and_TTL": {
            "policy": "IMMUTABLE_FIXTURE" if fixture_ref else "UNRESOLVED",
            "ttl_seconds": None,
        },
        "point_in_time_policy": "FIXTURE_LOCK_ONLY" if fixture_ref else "UNRESOLVED",
        "requirement_context_policy": "SAME_FIXTURE_INPUT_LOCK" if fixture_ref else "UNRESOLVED",
        "selected_requirement_alternatives": [],
        "readiness": readiness,
        "derived_state": (
            "RETIRED"
            if dormant
            else "CONTEXT_READY"
            if all(
                readiness[key] == "PASS"
                for key in ("specification", "implementation", "inputs", "requirements", "oracle", "context")
            )
            else "SPECIFIED"
        ),
        "exact_resolution_action_or_null": exact_action,
        "evidence_summary": (
            {
                "evidence_ceiling": "FIXTURE",
                "fixture_ref": fixture_ref,
                "empirical_market_evidence": False,
                "limitations": ["NO_REPLAY_PAPER_SHADOW_DRYRUN_CANARY_OR_LIVE_EVIDENCE"],
            }
            if fixture_ref
            else {
                "evidence_ceiling": "NONE",
                "empirical_market_evidence": False,
                "limitations": ["SOURCE_IDENTITY_ONLY"],
            }
        ),
        "agent_access_policy": _agent_access_policy(agent_ids, compute=fixture_ref is not None),
        "fallback_policy": {"behavior": "FAIL_CLOSED", "component_id": None},
        "runtime_snapshot_ref_or_null": None,
        "activation_state": "DORMANT_PRESERVED" if dormant else "INACTIVE_NONLIVE",
        "rollback_target_or_null": None,
        "upstream_value_lineage": ([fixture_ref] if fixture_ref else []),
        "downstream_consumer_classes": ["CONTROL1_INDEPENDENT_VALIDATOR"],
        "producer_owner": "CONTROL1_CENTRAL_BUILDER",
        "validator_refs": [VALIDATOR_NAME],
        "terminal_disposition_or_null": exact_action if dormant else None,
    }


def _record(
    *,
    component_id: str,
    record_state: str,
    origins: Sequence[str],
    definition: Mapping[str, Any],
    decision_roles: Sequence[str],
    bindings: Sequence[Mapping[str, Any]],
    provenance: Sequence[Mapping[str, Any]],
    qku_roles: Sequence[Mapping[str, Any]] = (),
    market_tags: Sequence[str] = (),
    relations: Sequence[Mapping[str, Any]] = (),
    producer_owner: str = "CONTROL1_CENTRAL_BUILDER",
) -> dict[str, Any]:
    return {
        "canonical_component_id": component_id,
        "semantic_version": "1.0",
        "record_state": record_state,
        "origin_cohorts": sorted(set(origins)),
        "definition": copy.deepcopy(dict(definition)),
        "uses": {
            "decision_roles": sorted(set(decision_roles)),
            "decision_outputs": [
                item.get("name")
                for item in definition.get("output_schema", [])
                if isinstance(item, Mapping) and item.get("name")
            ],
            "market_family_tags": sorted(set(market_tags)),
            "qku_role_bindings": [copy.deepcopy(dict(item)) for item in qku_roles],
            "consumer_class_tags": ["CONTROL1_FACADE", "CONTROL1_INDEPENDENT_VALIDATOR"],
        },
        "bindings": [copy.deepcopy(dict(item)) for item in bindings],
        "provenance": [copy.deepcopy(dict(item)) for item in provenance],
        "relations": [copy.deepcopy(dict(item)) for item in relations],
        "governance": {
            "producer_owner": producer_owner,
            "validator_refs": [VALIDATOR_NAME],
            "reviewer_or_challenger_owner": "OWNER_DESIGNATED_INDEPENDENT_AUDITOR",
            "change_authority": "CONTROL1_CENTRAL_BUILDER_REVIEWED_GIT_PR_ONLY",
        },
    }


def _expansion_batch(
    *,
    batch_id: str,
    origin: str,
    source_refs: Sequence[str],
    source_classification: str,
    items: Sequence[dict[str, Any]],
    requested_evidence_modes: Sequence[str] = ("NONE",),
    requested_promotion_ceiling: str = "SPECIFIED",
) -> dict[str, Any]:
    """Return the one transient ExpansionBatchV1-compatible intake shape."""

    prepared_items: list[dict[str, Any]] = []
    intended_contexts: dict[str, dict[str, Any]] = {}
    for source_item in items:
        item = copy.deepcopy(source_item)
        record = item.get("record") if isinstance(item.get("record"), Mapping) else item
        if not isinstance(record, Mapping):
            raise BuildError("expansion batch item must contain one computation record")
        if "record" not in item:
            component_id = str(record.get("canonical_component_id", ""))
            item = {
                "record": copy.deepcopy(dict(record)),
                "case": f"SOURCE_INTAKE::{component_id}",
                "equivalence_decision": "NO",
                "nonidentical_relation": "DISTINCT",
            }
        item["record"] = _normalize_compiler_candidate_record(
            _batch_item_record(item)
        )
        record = item["record"]
        prepared_items.append(item)
        for binding in record.get("bindings", []):
            if not isinstance(binding, Mapping):
                continue
            modes = [str(mode) for mode in binding.get("supported_modes", [])]
            if not modes:
                modes = [None]
            for mode in modes:
                context = {
                    "market": copy.deepcopy(binding.get("market", "ANY")),
                    "venue": copy.deepcopy(binding.get("venue", "ANY")),
                }
                if mode is not None:
                    context["mode"] = mode
                intended_contexts[_json_line(context)] = context
    return {
        "batch_id": batch_id,
        "batch_origin": origin,
        "submitted_by": "CONTROL1_CENTRAL_BUILDER",
        # This is an actual build-intake timestamp, not source/evidence time or
        # a canonical identity.  It is transient and is never written into the
        # registry or acceptance surface.
        "submission_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_refs": sorted(set(source_refs)),
        "source_classification": source_classification,
        "intended_market_venue_modes": [
            intended_contexts[key] for key in sorted(intended_contexts)
        ],
        "items": prepared_items,
        "requested_evidence_modes": sorted(set(requested_evidence_modes)),
        "requested_promotion_ceiling": requested_promotion_ceiling,
    }


def _load_agent_ids(repo_root: Path) -> tuple[str, ...]:
    payload = _read_json(repo_root / PR165_D2_ROSTER)
    ids = sorted(
        {
            str(row["agent_id"])
            for row in payload.get("records", [])
            if isinstance(row, dict) and row.get("agent_id")
        }
    )
    expected = {
        "research_agent",
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
        "governance_agent",
        "dashboard_agent",
        "connector_venue_readiness_future_consumer",
    }
    if set(ids) != expected:
        raise BuildError(
            "PR165-D2 roster drift requires explicit policy review: "
            f"expected={sorted(expected)!r}, actual={ids!r}"
        )
    return tuple(ids)


def _rp5c_component_id(source_identity_id: str) -> str:
    prefix = "RP5C_IDENTITY_"
    if not source_identity_id.startswith(prefix):
        raise BuildError(f"invalid RP5C source identity: {source_identity_id}")
    suffix = source_identity_id.removeprefix(prefix)
    if len(suffix) != 8 or not suffix.isdigit():
        raise BuildError(f"invalid RP5C source identity suffix: {source_identity_id}")
    return f"QTT.COMP.RP5C.{suffix}"


def _rp5c_group_custody_key(row: Mapping[str, Any]) -> dict[str, str]:
    """Reconstruct RP5C's stable, structured source-group custody key.

    RP5C's ``duplicate_group_id`` is an ordinal derived from sorted enumeration
    and therefore is current-source evidence, not a stable identity key.  This
    six-field tuple is the exact grouping input used by the RP5C owner.  It is
    retained as structured text (never a hash) and is explicitly not CONTROL1
    semantic-equivalence proof.
    """

    return {
        "key_version": RP5C_GROUP_CUSTODY_KEY_VERSION,
        **{field: str(row.get(field) or "") for field in RP5C_GROUP_KEY_FIELDS},
    }


def _rp5c_group_custody_tuple(value: Mapping[str, Any]) -> tuple[str, ...]:
    expected = {"key_version", *RP5C_GROUP_KEY_FIELDS}
    if set(value) != expected:
        raise BuildError(
            "RP5C source-group custody key fields drift: "
            f"expected={sorted(expected)!r}, actual={sorted(value)!r}"
        )
    if value.get("key_version") != RP5C_GROUP_CUSTODY_KEY_VERSION:
        raise BuildError(f"unsupported RP5C source-group custody key: {value!r}")
    if any(not isinstance(value.get(field), str) for field in RP5C_GROUP_KEY_FIELDS):
        raise BuildError(f"non-text RP5C source-group custody key: {value!r}")
    return tuple(str(value[field]) for field in RP5C_GROUP_KEY_FIELDS)


def _load_rp5c_group_custody_keys(
    repo_root: Path, deadline: _Deadline
) -> dict[str, tuple[str, dict[str, str], tuple[str, ...]]]:
    """Map current canonical source identities to stable group custody keys."""

    by_canonical: dict[str, tuple[str, dict[str, str], tuple[str, ...]]] = {}
    key_owners: dict[tuple[str, ...], str] = {}
    for row in _iter_jsonl(repo_root / RP5C_CANONICAL_LIBRARY, deadline):
        canonical = str(row.get("canonical_identity_row_id") or "")
        _rp5c_component_id(canonical)
        group_id = str(row.get("duplicate_group_id") or "")
        if not group_id:
            raise BuildError(f"RP5C canonical library row lacks duplicate group: {canonical}")
        key_payload = _rp5c_group_custody_key(row)
        key = _rp5c_group_custody_tuple(key_payload)
        if canonical in by_canonical:
            raise BuildError(f"duplicate RP5C canonical library identity: {canonical}")
        prior = key_owners.get(key)
        if prior is not None:
            raise BuildError(
                "RP5C canonical library custody key maps to multiple identities: "
                f"{prior}, {canonical}"
            )
        by_canonical[canonical] = (group_id, key_payload, key)
        key_owners[key] = canonical
    if len(by_canonical) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "RP5C canonical-library custody-key coverage drift: "
            f"{len(by_canonical)} != {EXPECTED_RP5C_IDENTITIES}"
        )
    return by_canonical


def _accepted_rp5c_group_map(
    base_records: Sequence[Mapping[str, Any]],
) -> tuple[dict[tuple[str, ...], str], dict[str, Mapping[str, Any]]]:
    """Recover stable CONTROL1 IDs from structured RP5C custody keys."""

    key_to_component: dict[tuple[str, ...], str] = {}
    component_to_record: dict[str, Mapping[str, Any]] = {}
    for record in base_records:
        origins = {str(value) for value in record.get("origin_cohorts", ())}
        if "RP5C_BASELINE" not in origins:
            continue
        component_id = str(record.get("canonical_component_id") or "")
        if not component_id.startswith("QTT.COMP.RP5C."):
            raise BuildError(f"accepted RP5C record has invalid component ID: {component_id!r}")
        key_payloads = [
            relation.get("source_group_custody_key")
            for relation in record.get("relations", ())
            if isinstance(relation, Mapping)
            and relation.get("relation_type")
            == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
        ]
        if len(key_payloads) != 1 or not isinstance(key_payloads[0], Mapping):
            raise BuildError(
                f"accepted RP5C record lacks one stable source-group custody key: {component_id}"
            )
        key = _rp5c_group_custody_tuple(key_payloads[0])
        prior = key_to_component.get(key)
        if prior is not None and prior != component_id:
            raise BuildError(
                "accepted RP5C source-group custody key maps to multiple components: "
                f"{prior}, {component_id}"
            )
        if component_id in component_to_record:
            raise BuildError(f"duplicate accepted RP5C component: {component_id}")
        key_to_component[key] = component_id
        component_to_record[component_id] = record
    if key_to_component and len(key_to_component) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "accepted RP5C source-group custody-key coverage drift: "
            f"{len(key_to_component)} != {EXPECTED_RP5C_IDENTITIES}"
        )
    return key_to_component, component_to_record


def _rp5c_provenance(
    source_ref: str,
    source_row_ref: str,
    fields: Sequence[str],
    component_id: str,
    relation: str,
    *,
    source_local_identity: str | None = None,
) -> dict[str, Any]:
    return {
        "source_artifact_ref": source_ref,
        "source_row_ref": source_row_ref,
        "source_local_identity_or_name": source_local_identity or component_id,
        "source_fields_consumed": list(fields),
        "source_relation": relation,
        "canonical_target_ref": component_id,
        "proof_refs": [],
    }


def _build_rp5c_batch(
    repo_root: Path,
    agent_ids: Sequence[str],
    deadline: _Deadline,
    base_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    accepted_key_map, accepted_records = _accepted_rp5c_group_map(base_records)
    source_group_keys = _load_rp5c_group_custody_keys(repo_root, deadline)
    records: dict[str, dict[str, Any]] = {}
    metadata: dict[str, dict[str, Any]] = {}
    source_to_component: dict[str, str] = {}
    source_members: dict[str, set[str]] = {}
    member_owner: dict[str, str] = {}
    current_group_ids: set[str] = set()
    current_group_keys: set[tuple[str, ...]] = set()
    expected_lineage_rows = 0
    dedupe_ref = RP5C_DEDUPE.as_posix()
    for row in _iter_jsonl(repo_root / RP5C_DEDUPE, deadline):
        source_identity_id = str(row.get("canonical_identity_row_id") or "")
        if not source_identity_id:
            raise BuildError("RP5C dedupe row lacks canonical_identity_row_id")
        source_component_id = _rp5c_component_id(source_identity_id)
        if source_identity_id in source_to_component:
            raise BuildError(f"duplicate RP5C source canonical identity: {source_identity_id}")
        group_id = str(row.get("duplicate_group_id") or "")
        if not group_id or group_id in current_group_ids:
            raise BuildError(f"duplicate or empty RP5C duplicate group: {group_id!r}")
        current_group_ids.add(group_id)
        source_key_entry = source_group_keys.get(source_identity_id)
        if source_key_entry is None:
            raise BuildError(
                "RP5C dedupe canonical identity lacks canonical-library custody key: "
                f"{source_identity_id}"
            )
        library_group_id, group_key_payload, group_key = source_key_entry
        if library_group_id != group_id:
            raise BuildError(
                "RP5C dedupe/canonical-library duplicate-group mismatch: "
                f"{source_identity_id}: {group_id} != {library_group_id}"
            )
        if group_key in current_group_keys:
            raise BuildError(
                f"RP5C dedupe rows repeat a stable source-group custody key: {group_key!r}"
            )
        current_group_keys.add(group_key)
        if accepted_key_map:
            component_id = accepted_key_map.get(group_key, "")
            if not component_id:
                raise BuildError(
                    "RP5C source-group custody-key set added an unknown group: "
                    f"{group_key_payload!r}"
                )
        else:
            component_id = source_component_id
        if component_id in records:
            raise BuildError(f"duplicate RP5C canonical identity: {component_id}")
        source_to_component[source_identity_id] = component_id
        members = [str(value) for value in row.get("duplicate_member_identity_row_ids", [])]
        if int(row.get("duplicate_member_count", len(members))) != len(members):
            raise BuildError(f"RP5C duplicate member count mismatch: {component_id}")
        member_set = set(members)
        if len(member_set) != len(members) or source_identity_id not in member_set:
            raise BuildError(f"RP5C duplicate member integrity mismatch: {component_id}")
        for member in members:
            _rp5c_component_id(member)
            if member in member_owner:
                raise BuildError(
                    f"RP5C duplicate member belongs to multiple groups: {member}"
                )
            member_owner[member] = source_identity_id
        source_members[source_identity_id] = member_set
        expected_lineage_rows += len(members)
        exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
        definition = _definition(
            display_name=component_id,
            description=(
                "Immutable RP5C baseline identity preserved without treating the "
                "baseline grouping as CONTROL1 semantic equivalence proof."
            ),
            component_kind="SPECIFICATION_REQUIRED",
            complete_definition=exact_action,
        )
        records[component_id] = _record(
            component_id=component_id,
            record_state="PROVISIONAL",
            origins=["RP5C_BASELINE"],
            definition=definition,
            decision_roles=["INTERNAL_SUPPORT"],
            bindings=[],
            provenance=[
                _rp5c_provenance(
                    dedupe_ref,
                    str(row.get("row_id") or component_id),
                    (
                        "canonical_identity_row_id",
                        "dedupe_status",
                        "duplicate_group_id",
                        "duplicate_member_count",
                        "duplicate_member_identity_row_ids",
                    ),
                    component_id,
                    "IMMUTABLE_BASELINE_GROUPING_NOT_SEMANTIC_PROOF",
                    source_local_identity=source_identity_id,
                )
            ],
            relations=[
                {
                    "relation_type": "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF",
                    "source_group_custody_key": group_key_payload,
                    "source_duplicate_group_id": group_id,
                    "source_dedupe_status": row.get("dedupe_status"),
                    "member_identity_row_ids": members,
                    "direct_semantic_equivalence_proven": False,
                    "exact_proof_action": (
                        f"MISSING_DIRECT_SEMANTIC_EQUIVALENCE_PROOF: {component_id}"
                        if len(members) > 1
                        else None
                    ),
                }
            ],
            producer_owner="RP5C_IMMUTABLE_BASELINE_VIA_CONTROL1_BUILDER",
        )
        metadata[component_id] = {
            "source_identity_id": source_identity_id,
            "names": set(),
            "identity_types": set(),
            "market_tags": set(),
            "qku_roles": {},
            "stage1_seed": False,
            "dormant": False,
            "lineage_occurrence_count": 0,
            "lineage_identity_row_ids": set(),
            "lineage_source_artifact_row_ids": set(),
            "lineage_provenance_tiers": set(),
            "lineage_custody_route_refs": set(),
        }

    if accepted_key_map and current_group_keys != set(accepted_key_map):
        missing = sorted(set(accepted_key_map) - current_group_keys)[:10]
        added = sorted(current_group_keys - set(accepted_key_map))[:10]
        raise BuildError(
            "RP5C source-group custody-key set drift: "
            f"missing={missing}, added={added}"
        )
    if set(source_group_keys) != set(source_to_component):
        missing = sorted(set(source_group_keys) - set(source_to_component))[:10]
        extra = sorted(set(source_to_component) - set(source_group_keys))[:10]
        raise BuildError(
            "RP5C canonical-library/dedupe identity closure drift: "
            f"missing={missing}, extra={extra}"
        )
    if len(records) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "RP5C canonical identity count drift: "
            f"{len(records)} != {EXPECTED_RP5C_IDENTITIES}"
        )

    for relative_path in RP5C_LIBRARIES:
        source_ref = relative_path.as_posix()
        for row in _iter_jsonl(repo_root / relative_path, deadline):
            source_identity_id = str(row.get("canonical_identity_row_id") or "")
            component_id = source_to_component.get(source_identity_id, "")
            if component_id not in records:
                raise BuildError(
                    f"{source_ref} references unknown canonical identity {source_identity_id!r}"
                )
            meta = metadata[component_id]
            identity_type = str(row.get("identity_type") or row.get("qku_type") or "")
            if identity_type:
                meta["identity_types"].add(identity_type)
            for field in ("qku_id", "formula_id", "formula_variant_id"):
                if row.get(field):
                    meta["names"].add(str(row[field]))
            for field in ("market_family", "qku_family", "formula_family"):
                value = str(row.get(field) or "")
                if value and "unknown" not in value.lower():
                    meta["market_tags"].add(value)
            meta["stage1_seed"] = bool(meta["stage1_seed"] or row.get("stage1_seed_inclusion_flag"))
            meta["dormant"] = bool(meta["dormant"] or row.get("stage1_dormant_future_market_flag"))
            qku_id = row.get("qku_id")
            if qku_id:
                role_key = (
                    str(qku_id),
                    str(row.get("ontology_category") or "SEMANTICS_UNRESOLVED"),
                    str(row.get("market_family") or "UNRESOLVED"),
                )
                meta["qku_roles"][role_key] = {
                    "qku_id": str(qku_id),
                    "role_or_decision_stage": role_key[1],
                    "market_family": role_key[2],
                    "stack_root_or_direct_component": None,
                    "selection_rule_if_container": None,
                    "agent_policy_tags": sorted(set(row.get("agent_responsibility_group_refs", []))),
                    "source_refs": [source_ref, str(row.get("identity_row_id") or component_id)],
                    "exact_resolution_action": f"MISSING_SEMANTIC_SPECIFICATION: {component_id}",
                }
            records[component_id]["provenance"].append(
                _rp5c_provenance(
                    source_ref,
                    str(row.get("identity_row_id") or component_id),
                    (
                        "canonical_identity_row_id",
                        "identity_type",
                        "qku_id",
                        "formula_id",
                        "formula_variant_id",
                        "source_artifact_ref",
                        "source_artifact_row_id",
                        "source_line_or_json_path",
                        "formula_expression_ref",
                        "market_family",
                        "ontology_category",
                        "stage1_seed_inclusion_flag",
                        "stage1_dormant_future_market_flag",
                    ),
                    component_id,
                    "IMMUTABLE_BASELINE_LIBRARY_ROW",
                    source_local_identity=source_identity_id,
                )
            )
            if row.get("source_artifact_row_id"):
                meta["lineage_source_artifact_row_ids"].add(str(row["source_artifact_row_id"]))

    lineage_ref = RP5C_LINEAGE.as_posix()
    lineage_rows = 0
    lineage_members: set[str] = set()
    for row in _iter_jsonl(repo_root / RP5C_LINEAGE, deadline):
        lineage_rows += 1
        source_identity_id = str(row.get("canonical_identity_row_id") or "")
        component_id = source_to_component.get(source_identity_id, "")
        if component_id not in records:
            raise BuildError(f"RP5C lineage references unknown identity {source_identity_id!r}")
        identity_row_id = str(row.get("identity_row_id") or "")
        if (
            not identity_row_id
            or member_owner.get(identity_row_id) != source_identity_id
            or identity_row_id not in source_members[source_identity_id]
        ):
            raise BuildError(
                "RP5C lineage member/canonical mismatch: "
                f"canonical={source_identity_id!r}, member={identity_row_id!r}"
            )
        if identity_row_id in lineage_members:
            raise BuildError(f"RP5C lineage repeats member identity: {identity_row_id}")
        lineage_members.add(identity_row_id)
        meta = metadata[component_id]
        meta["lineage_occurrence_count"] += 1
        meta["lineage_identity_row_ids"].add(identity_row_id)
        if row.get("source_artifact_row_id"):
            meta["lineage_source_artifact_row_ids"].add(str(row["source_artifact_row_id"]))
        if row.get("provenance_tier"):
            meta["lineage_provenance_tiers"].add(str(row["provenance_tier"]))
        meta["lineage_custody_route_refs"].update(
            str(value) for value in row.get("custody_route_refs", [])
        )
    if lineage_rows != expected_lineage_rows or lineage_members != set(member_owner):
        missing = sorted(set(member_owner) - lineage_members)[:10]
        extra = sorted(lineage_members - set(member_owner))[:10]
        raise BuildError(
            "RP5C lineage/dedupe closure drift: "
            f"lineage={lineage_rows}, dedupe_members={expected_lineage_rows}, "
            f"missing={missing}, extra={extra}"
        )

    for component_id, record in records.items():
        meta = metadata[component_id]
        names = sorted(meta["names"])
        identity_types = {value.upper() for value in meta["identity_types"]}
        if names:
            record["definition"]["display_name"] = names[0]
        if "QKU" in identity_types and "FORMULA" not in identity_types:
            record["definition"]["component_kind"] = "QKU_SELECTION_POLICY"
        elif "FORMULA" in identity_types:
            record["definition"]["component_kind"] = "PURE_FORMULA"
        record["uses"]["market_family_tags"] = sorted(meta["market_tags"])
        preserved_qku_roles = sorted(
            meta["qku_roles"].values(),
            key=lambda row: (
                row["qku_id"], row["role_or_decision_stage"], row["market_family"]
            ),
        )
        for role in preserved_qku_roles:
            role["runtime_root_eligibility"] = (
                "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            )
        record["uses"]["qku_role_bindings"] = preserved_qku_roles
        source_dormant = bool(meta["dormant"] and not meta["stage1_seed"])
        # RP5C supplies immutable identity/custody evidence, not complete
        # CONTROL1 semantics.  control.py correctly treats PROVISIONAL as an
        # active candidate state and defaults a null QKU root to the containing
        # record.  Therefore any incomplete RP5C row carrying preserved QKU
        # roles must remain non-runtime until a later proof-backed semantic
        # record supplies one direct root or selection policy.  We preserve the
        # source roles verbatim and do not invent a selector or choose a winner.
        incomplete_role_import = bool(preserved_qku_roles)
        dormant = bool(source_dormant or incomplete_role_import)
        record["record_state"] = "DORMANT_PRESERVED" if dormant else "PROVISIONAL"
        exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
        if incomplete_role_import:
            record["relations"].append(
                {
                    "relation_type": "RP5C_RUNTIME_ROOT_INELIGIBILITY",
                    "runtime_root_eligible": False,
                    "preserved_qku_role_count": len(preserved_qku_roles),
                    "source_stage1_dormant": source_dormant,
                    "reason": (
                        "INCOMPLETE_IMPORTED_SEMANTICS_CANNOT_BE_A_RUNTIME_QKU_ROOT"
                    ),
                    "exact_resolution_action": exact_action,
                    "selector_or_root_invented": False,
                    "qku_roles_erased": False,
                }
            )
        source_identity_id = str(meta["source_identity_id"])
        record["bindings"] = [
            _binding(
                component_id,
                binding_id=f"BINDING.RP5C.REVIEW.{component_id.removeprefix('QTT.COMP.RP5C.')}",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
                dormant=dormant,
            )
        ]
        record["provenance"].append(
            _rp5c_provenance(
                lineage_ref,
                f"canonical_identity:{component_id}",
                (
                    "identity_row_id",
                    "source_artifact_row_id",
                    "provenance_tier",
                    "custody_route_refs",
                    "no_deletion_flag",
                ),
                component_id,
                "IMMUTABLE_LINEAGE_SUMMARY",
                source_local_identity=source_identity_id,
            )
        )
        record["relations"].append(
            {
                "relation_type": "RP5C_SOURCE_LINEAGE_SUMMARY",
                "source_canonical_identity_row_id": source_identity_id,
                "source_occurrence_count": meta["lineage_occurrence_count"],
                "identity_row_ids": sorted(meta["lineage_identity_row_ids"]),
                "source_artifact_row_ids": sorted(meta["lineage_source_artifact_row_ids"]),
                "provenance_tiers": sorted(meta["lineage_provenance_tiers"]),
                "custody_route_refs": sorted(meta["lineage_custody_route_refs"]),
                "immutable_original_preserved": True,
            }
        )
        record["provenance"].sort(
            key=lambda row: (str(row["source_artifact_ref"]), str(row["source_row_ref"]))
        )

        accepted = accepted_records.get(component_id)
        if accepted is not None:
            if str(accepted.get("semantic_version")) != str(record.get("semantic_version")):
                raise BuildError(f"RP5C semantic version drift requires successor: {component_id}")
            if _semantic_core(accepted) != _semantic_core(record):
                raise BuildError(f"RP5C semantic-core drift requires successor: {component_id}")

    ordered = [records[key] for key in sorted(records)]
    return _expansion_batch(
        batch_id="EXPANSION.RP5C.BASELINE",
        origin="RP5C_BASELINE",
        source_refs=[dedupe_ref, lineage_ref, *(path.as_posix() for path in RP5C_LIBRARIES)],
        source_classification="OWNER_SUBMITTED",
        items=ordered,
        requested_evidence_modes=("NONE",),
        requested_promotion_ceiling="NOT_ELIGIBLE",
    )


def _import_r2a_modules(repo_root: Path) -> tuple[Any, Any, Any]:
    root_text = str(repo_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    base = "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations"
    try:
        return (
            importlib.import_module(f"{base}.formula_seed_library"),
            importlib.import_module(f"{base}.algorithm_seed_library"),
            importlib.import_module(f"{base}.quantum_seed_library"),
        )
    except ModuleNotFoundError as exc:
        raise BuildError(f"unable to import PR162D-R2A implementation inventory: {exc}") from exc


def _implementation_entry(
    *,
    version: str,
    callable_ref: str,
    latency_class: str,
    precision: str,
    memoizable: bool,
    proof_basis: str,
    security_state: str = "EXPLICIT_CONTROL_PLANE_ALLOWLIST_REQUIRED",
) -> dict[str, Any]:
    return {
        "implementation_version": version,
        "callable_or_solver_ref": callable_ref,
        "code_owner": "PR162D_R2A_SOURCE_OWNER",
        "supported_platforms": ["WINDOWS", "LINUX"],
        "pinned_dependencies": ["PYTHON_STANDARD_LIBRARY_OR_REPOSITORY_PINNED_DEPENDENCIES"],
        "determinism_seed_policy": "DETERMINISTIC_GIVEN_IDENTICAL_TYPED_INPUTS",
        "precision": precision,
        "latency_class": latency_class,
        "security_state": security_state,
        "memoizable": memoizable,
        "memoizable_proof_basis": proof_basis,
        "fallback": "FAIL_CLOSED",
    }


def _optional_native_implementation(component_id: str) -> dict[str, Any] | None:
    """Use a Decimal-native implementation only when control explicitly allows it."""
    mapping = getattr(_control_module(), "NATIVE_IMPLEMENTATIONS", None)
    if not isinstance(mapping, Mapping):
        raise BuildError("control owner lacks its explicit NATIVE_IMPLEMENTATIONS allowlist")
    native_ref_by_component = {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY": "qtt.computation_control.native:decimal_implied_probability",
        "QTT.COMP.FORMULA.PROBABILITY_EDGE": "qtt.computation_control.native:decimal_probability_edge",
        "QTT.COMP.FORMULA.MID_PRICE": "qtt.computation_control.native:decimal_mid_price",
        "QTT.COMP.FORMULA.SPREAD": "qtt.computation_control.native:decimal_spread",
        "QTT.COMP.FORMULA.RELATIVE_SPREAD": "qtt.computation_control.native:decimal_relative_spread",
    }
    ref = native_ref_by_component.get(component_id)
    if ref is None:
        return None
    candidate = mapping.get(ref)
    if not callable(candidate):
        raise BuildError(f"control native implementation allowlist drift: {ref}")
    value = _implementation_entry(
        version="control-native-decimal-v1",
        callable_ref=ref,
        latency_class="PRETRADE_BOUNDED",
        precision="DECIMAL_EXACT_BOUNDARY",
        memoizable=True,
        proof_basis="CONTROL_MODULE_EXPLICIT_NATIVE_ALLOWLIST_AND_INDEPENDENT_CONTROL1_ORACLE",
        security_state="CONTROL1_NATIVE_ALLOWLIST",
    )
    value["code_owner"] = "CONTROL1_PRIVATE_RUNTIME"
    return value


def _closed_requirements(formula_id: str) -> list[dict[str, Any]]:
    requirement = {
        "required_semantic_version_constraint": "==1.0",
        "required_or_optional": "REQUIRED",
        "unit_or_basis_conversion": "IDENTITY",
        "timing_and_freshness_constraint": "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
        "activation_condition": "ALWAYS",
        "fallback_component_id_or_null": None,
        "failure_behavior": "FAIL_CLOSED",
    }
    if formula_id == "PROBABILITY_EDGE":
        return [
            {
                **requirement,
                "required_component_id_or_source_selector": "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
                "requirement_role": "IMPLIED_PROBABILITY_INPUT",
                "producer_output_name": "implied_probability",
                "consumer_input_name": "implied_probability",
            }
        ]
    if formula_id == "RELATIVE_SPREAD":
        return [
            {
                **requirement,
                "required_component_id_or_source_selector": "QTT.COMP.FORMULA.MID_PRICE",
                "requirement_role": "MID_PRICE_DENOMINATOR",
                "producer_output_name": "mid_price",
                "consumer_input_name": "mid_price",
            },
            {
                **requirement,
                "required_component_id_or_source_selector": "QTT.COMP.FORMULA.SPREAD",
                "requirement_role": "ABSOLUTE_SPREAD_NUMERATOR",
                "producer_output_name": "spread",
                "consumer_input_name": "spread",
            },
        ]
    return []


def _source_provenance(
    *,
    source_ref: str,
    row_ref: str,
    local_name: str,
    fields: Sequence[str],
    target: str,
    relation: str = "DIRECT_IMPLEMENTATION_CANDIDATE",
) -> dict[str, Any]:
    return {
        "source_artifact_ref": source_ref,
        "source_row_ref": row_ref,
        "source_local_identity_or_name": local_name,
        "source_fields_consumed": list(fields),
        "source_relation": relation,
        "canonical_target_ref": target,
        "proof_refs": [],
    }


def _closed_formula_fixture_inputs(spec: Any) -> dict[str, Any]:
    """Return one facade-level fixture lock for the closed arithmetic subgraphs."""

    fixtures: dict[str, dict[str, Any]] = {
        "IMPLIED_PROBABILITY": {"price": "0.43", "payout": "1"},
        # The implied probability is dependency-owned and therefore is not a
        # caller fixture input for this root.
        "PROBABILITY_EDGE": {"p_model": "0.58", "price": "0.43", "payout": "1"},
        "MID_PRICE": {"best_bid": "0.42", "best_ask": "0.46"},
        "SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
        # Both spread and midpoint are dependency-owned for this root.
        "RELATIVE_SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
    }
    return copy.deepcopy(fixtures.get(spec.formula_id, dict(spec.test_inputs)))


def _closed_formula_domain(formula_id: str) -> str | None:
    """Pin the domain in which the source and Decimal implementations agree."""

    return {
        "IMPLIED_PROBABILITY": (
            "price and payout are finite Decimal-compatible values; payout >= 1e-9; "
            "0 <= price <= payout; output is price/payout in [0,1]"
        ),
        "PROBABILITY_EDGE": (
            "p_model and dependency-produced implied_probability are finite probabilities "
            "in [0,1]; output is their signed difference"
        ),
        "MID_PRICE": "finite prices satisfying 0 <= best_bid <= best_ask",
        "SPREAD": "finite prices satisfying 0 <= best_bid <= best_ask",
        "RELATIVE_SPREAD": (
            "dependency-produced spread is nonnegative and dependency-produced mid_price "
            "is at least 1e-9"
        ),
    }.get(formula_id)


def _schema_type(value: Any) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "FINITE_REAL"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, Mapping):
        return "TYPED_OBJECT"
    if isinstance(value, (list, tuple)):
        return "TYPED_SEQUENCE"
    if value is None:
        return "NULLABLE_VALUE"
    return "SOURCE_DECLARED_TYPED_VALUE"


def _formula_record(spec: Any, agent_ids: Sequence[str]) -> dict[str, Any]:
    component_id = f"QTT.COMP.FORMULA.{spec.formula_id}"
    latency = _latency_class(spec.latency_class)
    implementation_versions = [
        _implementation_entry(
            version="r2a-owner-template-v1",
            callable_ref=spec.callable_ref,
            latency_class=latency,
            precision="SOURCE_PYTHON_FLOAT_REQUIRES_TYPED_BOUNDARY_VALIDATION",
            memoizable=False,
            proof_basis="INDEPENDENT_SIDE_EFFECT_AND_NUMERICAL_REUSE_PROOF_REQUIRED",
        )
    ]
    native = _optional_native_implementation(component_id)
    if native is not None:
        implementation_versions.append(native)
    selected_version = native["implementation_version"] if native else "r2a-owner-template-v1"
    closed = spec.formula_id in {
        "IMPLIED_PROBABILITY",
        "PROBABILITY_EDGE",
        "MID_PRICE",
        "SPREAD",
        "RELATIVE_SPREAD",
    }
    requirements = _closed_requirements(spec.formula_id)
    closed_input_units: dict[str, dict[str, str]] = {
        "IMPLIED_PROBABILITY": {"price": "price", "payout": "price"},
        "PROBABILITY_EDGE": {
            "p_model": "probability",
            "implied_probability": "probability",
        },
        "MID_PRICE": {"best_bid": "price", "best_ask": "price"},
        "SPREAD": {"best_bid": "price", "best_ask": "price"},
        "RELATIVE_SPREAD": {"spread": "price_delta", "mid_price": "price"},
    }
    input_units = closed_input_units.get(spec.formula_id, {})
    input_schema = [
        {
            "name": name,
            "type": "SOURCE_DECLARED_NUMERIC_OR_SEQUENCE",
            "required": True,
            "unit_or_basis": input_units.get(name, "EXACT_RUNTIME_UNIT_REQUIRED"),
        }
        for name in spec.required_inputs
    ]
    output_schema = [
        {
            "name": name,
            "type": "SOURCE_DECLARED_NUMERIC_OR_STRUCTURE",
            "unit_or_basis": spec.units_or_type_hints.get(name, "EXACT_UNIT_REQUIRED"),
        }
        for name in spec.outputs
    ]
    oracle_refs: list[Mapping[str, Any] | str] = [
        {
            "ref": f"docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json#{spec.formula_id}",
            "oracle_class": "SOURCE_DERIVED_FIXTURE_NOT_INDEPENDENT",
        }
    ]
    if closed:
        oracle_refs.append(
            {
                "ref": f"tests/pr169_qku_comp_control1/test_control1.py::oracle_{spec.formula_id.lower()}",
                "oracle_class": "INDEPENDENT_DECIMAL_OR_EXACT_ARITHMETIC",
            }
        )
    definition = _definition(
        display_name=spec.formula_id,
        description=f"PR162D-R2A owner-template formula candidate: {spec.expression}",
        component_kind="PURE_FORMULA",
        complete_definition=spec.expression,
        inputs=input_schema,
        outputs=output_schema,
        units={**input_units, **dict(spec.units_or_type_hints)},
        requirements=requirements,
        latency_class=latency,
        implementation_versions=implementation_versions,
        oracle_refs=oracle_refs,
        inventory_class="FORMULA",
    )
    definition["family_template_ref_or_null"] = None
    definition["assumptions"] = [
        "OWNER_TEMPLATE_SEMANTICS_REQUIRE_INDEPENDENT_DOMAIN_AND_BOUNDARY_REVIEW"
    ]
    definition["precision_and_rounding"] = (
        "DECIMAL_EXACT_CONTROL_NATIVE" if native else "SOURCE_PYTHON_FLOAT_NONLIVE_FIXTURE_ONLY"
    )
    closed_domain = _closed_formula_domain(spec.formula_id)
    if closed_domain is not None:
        definition["domain_and_boundary_behavior"] = closed_domain
    action = None if closed else f"MISSING_INDEPENDENT_ORACLE: {component_id}@1.0"
    fixture_ref = f"PR162D_R2A_TV_FORMULA::{spec.formula_id}"
    binding = _binding(
        component_id,
        binding_id=f"BINDING.FIXTURE.FORMULA.{spec.formula_id}",
        agent_ids=agent_ids,
        implementation_version=selected_version,
        exact_action=action,
        fixture_ref=fixture_ref,
        requirements_ready=True,
        oracle_ready=closed,
    )
    return _record(
        component_id=component_id,
        record_state="CANONICAL_ACCEPTED",
        origins=["PR162D_IMPLEMENTATION_BACKED"],
        definition=definition,
        decision_roles=_decision_roles(spec.domain_family_key),
        bindings=[binding],
        provenance=[
            _source_provenance(
                source_ref=(
                    "src/qtt/stage1_prediction_markets/"
                    "pr162d_r2a_real_formulations/formula_seed_library.py"
                ),
                row_ref=f"formula_specs[{spec.formula_id}]",
                local_name=spec.formula_id,
                fields=(
                    "formula_id",
                    "expression",
                    "callable_ref",
                    "required_inputs",
                    "outputs",
                    "units_or_type_hints",
                    "domain_family_key",
                    "subfamily_key",
                    "variant_key",
                    "latency_class",
                ),
                target=component_id,
            )
        ],
        market_tags=[spec.domain_family_key],
    )


def _algorithm_record(spec: Any, agent_ids: Sequence[str]) -> dict[str, Any]:
    component_id = f"QTT.COMP.ALGORITHM.{spec.algorithm_id}"
    latency = _latency_class(spec.latency_class)
    units = {
        **{name: "SOURCE_DECLARED_TYPED_INPUT_BASIS" for name in spec.required_inputs},
        **{name: "SOURCE_DECLARED_TYPED_OUTPUT_BASIS" for name in spec.outputs},
    }
    definition = _definition(
        display_name=spec.algorithm_id,
        description="PR162D-R2A deterministic procedure candidate.",
        component_kind="NUMERICAL_ALGORITHM",
        complete_definition=spec.procedure,
        inputs=[
            {
                "name": name,
                "type": "SOURCE_DECLARED_TYPED_VALUE",
                "required": True,
                "unit_or_basis": "EXACT_RUNTIME_CONTRACT_REQUIRED",
            }
            for name in spec.required_inputs
        ],
        outputs=[
            {
                "name": name,
                "type": "SOURCE_DECLARED_TYPED_VALUE",
                "unit_or_basis": "SOURCE_DECLARED",
            }
            for name in spec.outputs
        ],
        units=units,
        latency_class=latency,
        implementation_versions=[
            _implementation_entry(
                version="r2a-owner-template-v1",
                callable_ref=spec.callable_ref,
                latency_class=latency,
                precision="SOURCE_PROCEDURE_TYPED_OUTPUT",
                memoizable=False,
                proof_basis="ALGORITHM_REUSE_SAFETY_REQUIRES_INDEPENDENT_PROOF",
            )
        ],
        oracle_refs=[
            {
                "ref": f"docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json#{spec.algorithm_id}",
                "oracle_class": "SOURCE_DERIVED_FIXTURE_NOT_INDEPENDENT",
            }
        ],
        inventory_class="ALGORITHM",
    )
    definition["failure_domain_tags"] = sorted(
        set(definition["failure_domain_tags"]) | set(spec.failure_modes)
    )
    action = f"MISSING_INDEPENDENT_ORACLE: {component_id}@1.0"
    return _record(
        component_id=component_id,
        record_state="CANONICAL_ACCEPTED",
        origins=["PR162D_IMPLEMENTATION_BACKED"],
        definition=definition,
        decision_roles=_decision_roles(spec.domain_family_key),
        bindings=[
            _binding(
                component_id,
                binding_id=f"BINDING.FIXTURE.ALGORITHM.{spec.algorithm_id}",
                agent_ids=agent_ids,
                implementation_version="r2a-owner-template-v1",
                exact_action=action,
                fixture_ref=f"PR162D_R2A_TV_ALGORITHM::{spec.algorithm_id}",
                requirements_ready=True,
                oracle_ready=False,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref=(
                    "src/qtt/stage1_prediction_markets/"
                    "pr162d_r2a_real_formulations/algorithm_seed_library.py"
                ),
                row_ref=f"algorithm_specs[{spec.algorithm_id}]",
                local_name=spec.algorithm_id,
                fields=(
                    "algorithm_id",
                    "procedure",
                    "callable_ref",
                    "required_inputs",
                    "outputs",
                    "domain_family_key",
                    "subfamily_key",
                    "variant_key",
                    "failure_modes",
                    "latency_class",
                ),
                target=component_id,
            )
        ],
        market_tags=[spec.domain_family_key],
    )


_QUANTUM_BUILDER_INPUT_KEYS: Mapping[str, tuple[str, ...]] = {
    "build_qubo_market_bundle_selection": ("candidates", "covariance", "budget", "max_exposure"),
    "build_cqm_constrained_capital_allocation": ("candidates", "capital_budget", "max_exposure"),
    "build_qubo_parameter_stack_selection": ("candidates", "incompatibility"),
    "build_latency_adjusted_opportunity_selection": ("candidates",),
    "build_ising_binary_selection": ("candidates", "h", "J"),
    "build_qaoa_candidate_selection_shape": ("candidates", "covariance", "budget", "max_exposure"),
    "build_annealing_candidate_selection_shape": ("candidates", "covariance", "budget", "max_exposure"),
    "build_bqm_risk_balanced_selection": ("candidates", "covariance", "budget", "max_exposure"),
    "build_cqm_route_fill_allocation": ("candidates", "route_fill_budget"),
}


def _quantum_callable_contract(
    representative: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    builder_name = representative.build_shape.__name__
    required_keys = _QUANTUM_BUILDER_INPUT_KEYS.get(builder_name)
    if required_keys is None:
        raise BuildError(f"unreviewed quantum builder input contract: {builder_name}")
    missing = sorted(set(required_keys) - set(representative.test_inputs))
    if missing:
        raise BuildError(f"quantum builder fixture lacks required inputs: {builder_name}: {missing}")
    fixture_inputs = {
        key: copy.deepcopy(representative.test_inputs[key]) for key in required_keys
    }
    shape = representative.build_shape(copy.deepcopy(fixture_inputs))
    if not isinstance(shape, Mapping) or not shape:
        raise BuildError(f"quantum builder returned no structural mapping: {builder_name}")
    input_units = {
        "candidates": "ORIGINAL_ECONOMIC_CANDIDATE_FIELDS_WITH_DECLARED_UNITS",
        "covariance": "PAIRWISE_RISK_COVARIANCE_BASIS",
        "budget": "ORIGINAL_ECONOMIC_CAPITAL_BASIS",
        "capital_budget": "ORIGINAL_ECONOMIC_CAPITAL_BASIS",
        "max_exposure": "ORIGINAL_ECONOMIC_EXPOSURE_BASIS",
        "incompatibility": "DIMENSIONLESS_PAIRWISE_INDICATOR",
        "h": "ISING_LINEAR_ENERGY_COEFFICIENT",
        "J": "ISING_PAIRWISE_ENERGY_COEFFICIENT",
        "route_fill_budget": "ROUTE_FILL_COST_BASIS",
    }
    output_units = {
        "objective": "SYMBOLIC_OBJECTIVE_PRESERVING_DECLARED_ECONOMIC_OR_ENERGY_BASIS",
        "coefficients": "STRUCTURED_COEFFICIENTS_WITH_SOURCE_FIELD_LINEAGE",
        "variables": "ENCODED_VARIABLE_DECLARATIONS",
        "domains": "ENCODED_DOMAIN_DECLARATIONS",
        "constraints": "ENCODED_CONSTRAINT_DECLARATIONS",
        "penalties": "ENCODED_PENALTY_DECLARATIONS",
        "shape_type": "FORMULATION_CLASS_LABEL",
        "backend_execution": "BOOLEAN_NON_EXECUTION_FLAG",
        "quantum_advantage_claim": "BOOLEAN_NO_ADVANTAGE_CLAIM_FLAG",
    }
    input_schema = [
        {
            "name": key,
            "type": _schema_type(fixture_inputs[key]),
            "required": True,
            "unit_or_basis": input_units[key],
        }
        for key in required_keys
    ]
    output_schema = [
        {
            "name": key,
            "type": _schema_type(shape[key]),
            "unit_or_basis": output_units.get(key, "STRUCTURAL_MAPPING_METADATA"),
        }
        for key in sorted(shape)
    ]
    units = {
        **{key: input_units[key] for key in required_keys},
        **{
            key: output_units.get(key, "STRUCTURAL_MAPPING_METADATA")
            for key in sorted(shape)
        },
    }
    return fixture_inputs, input_schema, output_schema, units


def _quantum_family_record(specs: Sequence[Any], agent_ids: Sequence[str]) -> dict[str, Any]:
    ordered_specs = sorted(specs, key=lambda value: value.quantum_formulation_id)
    representative = ordered_specs[0]
    builder_name = representative.build_shape.__name__.removeprefix("build_").upper()
    component_id = f"QTT.COMP.QUANTUM.{builder_name}"
    callable_ref = representative.callable_ref
    if any(spec.callable_ref != callable_ref for spec in ordered_specs):
        raise BuildError(f"quantum callable family is not callable-stable: {builder_name}")
    fixture_inputs, input_schema, output_schema, units = _quantum_callable_contract(
        representative
    )
    original_model_id = f"QTT.COMP.ECONOMIC_MODEL.{builder_name}"
    quantum = {
        "applicability_state": "SPECIFIED_MAPPING_CANDIDATE",
        "original_economic_problem_ref": original_model_id,
        "problem_family": representative.subfamily_key,
        "formulation_candidates": [spec.quantum_formulation_id for spec in ordered_specs],
        "selected_formulation_or_none": None,
        "variable_encoding": sorted(set(representative.variables)),
        "objective_map": representative.objective,
        "constraint_map": list(representative.constraints),
        "penalty_policy": list(representative.penalties),
        "coefficient_scaling": "SOURCE_TEMPLATE_REQUIRES_INDEPENDENT_SENSITIVITY_PROOF",
        "precision_and_quantization": "SOURCE_PYTHON_FLOAT_STRUCTURAL_SHAPE_ONLY",
        "decomposition_or_embedding": None,
        "warm_start": None,
        "optimizer_and_version": None,
        "shots_reads_or_sampling_policy": None,
        "seed_resampling_policy": "DETERMINISTIC_LOCAL_SHAPE_NO_QPU_SAMPLING",
        "inverse_map": "MISSING_FEASIBLE_INVERSE_MAP_PROOF",
        "original_model_feasibility_check": "MISSING_ORIGINAL_MODEL_PARITY_PROOF",
        "same_formulation_classical_comparator": sorted(
            {spec.classical_comparator_ref for spec in ordered_specs}
        ),
        "local_exact_or_small_instance_parity": "REQUIRED",
        "fallback": "DETERMINISTIC_CLASSICAL_COMPARATOR_REQUIRED",
        "maturity_ceiling": "SPECIFIED",
    }
    definition = _definition(
        display_name=builder_name,
        description=(
            "One callable-family record preserving all PR162D quantum formulation "
            "roles without treating an encoding as an alias of its economic model."
        ),
        component_kind="QUANTUM_FORMULATION",
        complete_definition=representative.objective,
        inputs=input_schema,
        outputs=output_schema,
        units=units,
        latency_class="HOTPATH_FORBIDDEN",
        implementation_versions=[
            _implementation_entry(
                version="r2a-owner-template-v1",
                callable_ref=callable_ref,
                latency_class="HOTPATH_FORBIDDEN",
                precision="SOURCE_PYTHON_FLOAT_STRUCTURAL_SHAPE_ONLY",
                memoizable=False,
                proof_basis="ORIGINAL_MODEL_MAPPING_AND_INVERSE_PARITY_REQUIRED",
            )
        ],
        oracle_refs=[
            {
                "ref": f"docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json#{builder_name}",
                "oracle_class": "STRUCTURAL_SOURCE_FIXTURE_NOT_ORIGINAL_MODEL_PARITY",
            }
        ],
        quantum=quantum,
        inventory_class="QUANTUM_CALLABLE_FAMILY",
    )
    definition["risk_materiality"]["quantum_backend_dependency"] = False
    action = f"MISSING_QUANTUM_ORIGINAL_MODEL_LOCAL_PARITY: {component_id}@1.0"
    provenance = [
        _source_provenance(
            source_ref=(
                "src/qtt/stage1_prediction_markets/"
                "pr162d_r2a_real_formulations/quantum_seed_library.py"
            ),
            row_ref=f"quantum_specs[{spec.quantum_formulation_id}]",
            local_name=spec.quantum_formulation_id,
            fields=(
                "quantum_formulation_id",
                "objective",
                "callable_ref",
                "variables",
                "domains",
                "constraints",
                "penalties",
                "mapping_rationale",
                "classical_comparator_ref",
            ),
            target=component_id,
            relation="CALLABLE_FAMILY_ROLE_PRESERVED_NO_EQUIVALENCE_TO_ORIGINAL_MODEL",
        )
        for spec in ordered_specs
    ]
    return _record(
        component_id=component_id,
        record_state="CANONICAL_ACCEPTED",
        origins=["PR162D_IMPLEMENTATION_BACKED", "PR162E_Q_QUANTUM_MAPPING"],
        definition=definition,
        decision_roles=_decision_roles(representative.domain_family_key, quantum=True),
        bindings=[
            _binding(
                component_id,
                binding_id=f"BINDING.FIXTURE.QUANTUM.{builder_name}",
                agent_ids=agent_ids,
                implementation_version="r2a-owner-template-v1",
                exact_action=action,
                fixture_ref=f"PR162D_R2A_TV_QUANTUM_FAMILY::{builder_name}",
                requirements_ready=True,
                oracle_ready=False,
            )
        ],
        provenance=provenance,
        relations=[
            {
                "relation_type": "ENCODES_OR_MAPS",
                "canonical_target_ref": original_model_id,
                "proof_refs": [
                    (
                        "src/qtt/stage1_prediction_markets/"
                        "pr162d_r2a_real_formulations/quantum_seed_library.py::"
                        f"{representative.build_shape.__name__}"
                    )
                ],
                "mapping_state": "STRUCTURAL_MAPPING_CANDIDATE_LOCAL_PARITY_REQUIRED",
                "alias_equivalence_claim": False,
            },
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": original_model_id,
                "proof_refs": [
                    "CONTROL1_PROOF::ORIGINAL_ECONOMIC_MODEL_AND_ENCODED_VARIABLE_OBJECTIVE_ARE_DISTINCT"
                ],
                "direct_distinction_basis": (
                    "The original economic decision model and its encoded variables, "
                    "penalties, coefficient scaling, and inverse map have different semantics."
                ),
            },
        ],
        market_tags=[representative.domain_family_key],
    )


def _original_economic_model_record(
    quantum_record: Mapping[str, Any], agent_ids: Sequence[str]
) -> dict[str, Any]:
    quantum_id = str(quantum_record["canonical_component_id"])
    quantum_definition = quantum_record["definition"]
    component_id = str(quantum_definition["quantum"]["original_economic_problem_ref"])
    exact_action = f"MISSING_ORIGINAL_ECONOMIC_MODEL_SPECIFICATION: {component_id}@1.0"
    definition = _definition(
        display_name=component_id.rsplit(".", 1)[-1],
        description=(
            "Provisional original economic-model target required to keep the "
            "economic decision model distinct from its quantum encoding."
        ),
        component_kind="OPTIMIZATION_PROGRAM",
        complete_definition=exact_action,
        inputs=quantum_definition["input_schema"],
        outputs=[
            {
                "name": "selected_candidate_ids",
                "type": "TYPED_SEQUENCE",
                "unit_or_basis": "ORIGINAL_ECONOMIC_DECISION_IDENTITIES",
            },
            {
                "name": "original_objective_value",
                "type": "FINITE_REAL",
                "unit_or_basis": "ORIGINAL_ECONOMIC_OBJECTIVE_BASIS_REQUIRED",
            },
        ],
        units={
            **dict(quantum_definition["units_and_bases"]),
            "selected_candidate_ids": "ORIGINAL_ECONOMIC_DECISION_IDENTITIES",
            "original_objective_value": "ORIGINAL_ECONOMIC_OBJECTIVE_BASIS_REQUIRED",
        },
        latency_class="BATCH_PRECOMPUTE",
    )
    definition["objective_sense_or_null"] = "REQUIRES_INDEPENDENT_ORIGINAL_MODEL_CLOSE"
    definition["assumptions"] = [
        "THE_ENCODING_OBJECTIVE_IS_NOT_ACCEPTED_AS_THE ORIGINAL_ECONOMIC_MODEL",
        "VARIABLE_DOMAINS_CONSTRAINTS_UNITS_AND_INVERSE_INTERPRETATION_REQUIRE_DIRECT_PROOF",
    ]
    return _record(
        component_id=component_id,
        record_state="PROVISIONAL",
        origins=["PR162E_Q_QUANTUM_MAPPING", "POST_LAUNCH_EXPANSION_BATCH"],
        definition=definition,
        decision_roles=["INTERNAL_SUPPORT", "RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
        bindings=[
            _binding(
                component_id,
                binding_id=f"BINDING.RESEARCH.ECONOMIC_MODEL.{component_id.rsplit('.', 1)[-1]}",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref=(
                    "src/qtt/stage1_prediction_markets/"
                    "pr162d_r2a_real_formulations/quantum_seed_library.py"
                ),
                row_ref=f"quantum_mapping_target[{quantum_id}]",
                local_name=component_id,
                fields=("objective", "variables", "domains", "constraints", "test_inputs"),
                target=component_id,
                relation="ORIGINAL_MODEL_TARGET_EXTRACTED_BUT_NOT_PROVEN_BY_ENCODING",
            )
        ],
        relations=[
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": quantum_id,
                "proof_refs": [
                    "CONTROL1_PROOF::ORIGINAL_ECONOMIC_MODEL_AND_ENCODED_VARIABLE_OBJECTIVE_ARE_DISTINCT"
                ],
                "direct_distinction_basis": (
                    "Original economic variables, constraints, units, and decision "
                    "interpretation cannot be aliased to an encoding."
                ),
            }
        ],
        market_tags=["quantum_original_economic_model_candidate"],
    )


def _true_new_synthetic_record(agent_ids: Sequence[str]) -> dict[str, Any]:
    component_id = "QTT.COMP.RESEARCH.BOUNDED_PROBABILITY_DISTANCE"
    exact_action = f"MISSING_IMPLEMENTATION: {component_id}@1.0"
    definition = _definition(
        display_name="BOUNDED_PROBABILITY_DISTANCE",
        description=(
            "Bounded synthetic expansion candidate used to prove truthful new-record "
            "intake without claiming production readiness."
        ),
        component_kind="PURE_FORMULA",
        complete_definition="probability_distance = abs(p_left - p_right)",
        inputs=[
            {
                "name": "p_left",
                "type": "FINITE_DECIMAL_COMPATIBLE",
                "required": True,
                "unit_or_basis": "PROBABILITY_DECIMAL_0_TO_1",
            },
            {
                "name": "p_right",
                "type": "FINITE_DECIMAL_COMPATIBLE",
                "required": True,
                "unit_or_basis": "PROBABILITY_DECIMAL_0_TO_1",
            },
        ],
        outputs=[
            {
                "name": "probability_distance",
                "type": "FINITE_DECIMAL_COMPATIBLE",
                "unit_or_basis": "NONNEGATIVE_PROBABILITY_DELTA_0_TO_1",
            }
        ],
        units={
            "p_left": "PROBABILITY_DECIMAL_0_TO_1",
            "p_right": "PROBABILITY_DECIMAL_0_TO_1",
            "probability_distance": "NONNEGATIVE_PROBABILITY_DELTA_0_TO_1",
        },
    )
    definition["domain_and_boundary_behavior"] = (
        "p_left and p_right must be finite probabilities in [0,1]; output is in [0,1]"
    )
    return _record(
        component_id=component_id,
        record_state="PROVISIONAL",
        origins=["POST_LAUNCH_EXPANSION_BATCH"],
        definition=definition,
        decision_roles=["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
        bindings=[
            _binding(
                component_id,
                binding_id="BINDING.RESEARCH.BOUNDED_PROBABILITY_DISTANCE",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
                fixture_ref="CONTROL1_SYNTHETIC_EXPANSION::BOUNDED_PROBABILITY_DISTANCE",
                requirements_ready=True,
                oracle_ready=False,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref="tests/pr169_qku_comp_control1/test_control1.py",
                row_ref="synthetic_expansion_case[TRUE_NEW]",
                local_name="BOUNDED_PROBABILITY_DISTANCE",
                fields=("complete_semantics", "domain", "units", "nonlive_promotion_ceiling"),
                target=component_id,
                relation="SYNTHETIC_TRUE_NEW_PROVISIONAL_INTAKE",
            ),
            _source_provenance(
                source_ref="tests/pr169_qku_comp_control1/test_control1.py",
                row_ref="synthetic_expansion_case[QKU_ROLE_ADDITION]",
                local_name="NO_SYNTHETIC_QKU_CREATED",
                fields=("qku_role_proposal", "terminal_disposition"),
                target=component_id,
                relation="QKU_ROLE_PROPOSAL_REJECTED_PENDING_EXISTING_QKU_AUTHORITY_AND_DIRECT_ROLE_PROOF",
            ),
        ],
        relations=[
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": "QTT.COMP.FORMULA.PROBABILITY_CALIBRATION_ERROR",
                "proof_refs": [
                    (
                        "src/qtt/stage1_prediction_markets/"
                        "pr162d_r2a_real_formulations/formula_seed_library.py::"
                        "compute_probability_calibration_error"
                    )
                ],
                "direct_distinction_basis": (
                    "Absolute symmetric distance differs from the signed observed-minus-predicted "
                    "calibration error in sign, ports, and boundary interpretation."
                ),
            }
        ],
        market_tags=["synthetic_expansion_nonlive"],
    )


def _apply_semantic_reuse_evidence(records: Sequence[dict[str, Any]]) -> None:
    by_id = {str(record["canonical_component_id"]): record for record in records}
    implied = by_id["QTT.COMP.FORMULA.IMPLIED_PROBABILITY"]
    alias_name = "CONTROL1_SYNTHETIC_EXACT_ALIAS.IMPLIED_PROBABILITY"
    alias_proof = {
        "proof_id": "CONTROL1.DIRECT_EQUIVALENCE.IMPLIED_PROBABILITY.SYNTHETIC_ALIAS",
        "proof_class": "DIRECT_TYPED_SEMANTIC_AND_DIFFERENTIAL_FIXTURE_PROOF",
        "canonical_target_ref": implied["canonical_component_id"],
        "normalized_semantics": (
            "price/payout for finite 0<=price<=payout and payout>=1e-9; "
            "probability output in [0,1]"
        ),
        "units_domains_boundaries_time_state_requirements_match": True,
        "proof_refs": [
            "tests/pr169_qku_comp_control1/test_control1.py::test_expansion_compiler_reuses_only_with_direct_proof_and_is_idempotent",
            "tests/pr169_qku_comp_control1/test_control1.py::test_cycle_unit_nonfinite_passthrough_and_money_defects_fail_closed",
        ],
    }
    implied["definition"]["equivalence_proof_refs"].append(alias_proof)
    implied["relations"].append(
        {
            "relation_type": "ALIAS_OF",
            "source_identity_or_alias": alias_name,
            "canonical_target_ref": implied["canonical_component_id"],
            "canonical_target_version": implied["semantic_version"],
            "proof_refs": list(alias_proof["proof_refs"]),
            "direct_proof_id": alias_proof["proof_id"],
        }
    )
    implied["provenance"].extend(
        [
            _source_provenance(
                source_ref="tests/pr169_qku_comp_control1/test_control1.py",
                row_ref="synthetic_expansion_case[EXACT_DUPLICATE]",
                local_name="CONTROL1_SYNTHETIC_EXACT_DUPLICATE.IMPLIED_PROBABILITY",
                fields=("complete_typed_semantics", "fixture_vectors", "direct_proof"),
                target=implied["canonical_component_id"],
                relation="EXACT_DUPLICATE_REUSED_PROVENANCE_ONLY",
            ),
            _source_provenance(
                source_ref="tests/pr169_qku_comp_control1/test_control1.py",
                row_ref="synthetic_expansion_case[PROVENANCE_ONLY]",
                local_name="CONTROL1_SYNTHETIC_PROVENANCE_ONLY.IMPLIED_PROBABILITY",
                fields=("source_locator", "source_relation"),
                target=implied["canonical_component_id"],
                relation="PROVENANCE_ONLY_REUSE_NO_NEW_RECORD",
            ),
        ]
    )
    selected_policy = implied["bindings"][0]["selected_parameter_policy"]
    selected_policy["expansion_case_refs"] = [
        "CONTROL1_SYNTHETIC_EXPANSION::BINDING_UPDATE_REUSED_EXISTING_CONTEXT_FAMILY",
        "CONTROL1_SYNTHETIC_EXPANSION::PARAMETER_POLICY_PROVENANCE_UPDATE",
    ]
    selected_policy["parameter_values_changed"] = False

    family_target = "QTT.COMP.FORMULA.NET_EDGE"
    family_members = (
        "QTT.COMP.FORMULA.RELATIVE_SPREAD",
        "QTT.COMP.FORMULA.CAPITAL_UTILIZATION",
        "QTT.COMP.FORMULA.EXPOSURE_UTILIZATION",
        "QTT.COMP.FORMULA.COST_TO_BUDGET_RATIO",
    )
    family_domain = (
        "finite numerator and denominator in one declared contextual scalar basis; "
        "denominator >= 1e-9; output is a finite dimensionless ratio"
    )
    family_proof_refs = [
        (
            "src/qtt/stage1_prediction_markets/"
            "pr162d_r2a_real_formulations/formula_seed_library.py::"
            "compute_net_edge,compute_relative_spread,compute_capital_utilization,"
            "compute_exposure_utilization,compute_cost_to_budget_ratio"
        ),
        "CONTROL1_DIRECT_PROOF::SAFE_RATIO_OPERATOR_DOMAIN_BOUNDARY_AND_DIMENSIONAL_SIGNATURE",
    ]
    for family_id in (family_target, *family_members):
        family_definition = by_id[family_id]["definition"]
        family_definition["family_template_ref_or_null"] = family_target
        family_definition["domain_and_boundary_behavior"] = family_domain
        for input_entry in family_definition["input_schema"][:2]:
            input_entry["unit_or_basis"] = "SAME_CONTEXTUAL_SCALAR_BASIS"
        family_definition["output_schema"][0]["unit_or_basis"] = "DIMENSIONLESS_RATIO"
        family_definition["units_and_bases"] = {
            family_definition["input_schema"][0]["name"]: "SAME_CONTEXTUAL_SCALAR_BASIS",
            family_definition["input_schema"][1]["name"]: "SAME_CONTEXTUAL_SCALAR_BASIS",
            family_definition["output_schema"][0]["name"]: "DIMENSIONLESS_RATIO",
        }
    # A family template never erases a member's concrete port contract.  The
    # closed RELATIVE_SPREAD DAG is pinned to the exact producer units used by
    # MID_PRICE and SPREAD while retaining the proof-backed ratio-family link.
    relative_definition = by_id["QTT.COMP.FORMULA.RELATIVE_SPREAD"]["definition"]
    relative_units = {
        "spread": "price_delta",
        "mid_price": "price",
        "relative_spread": "ratio",
    }
    for entry in (
        *relative_definition["input_schema"],
        *relative_definition["output_schema"],
    ):
        entry["unit_or_basis"] = relative_units[str(entry["name"])]
    relative_definition["units_and_bases"] = relative_units
    for member_id in family_members:
        member = by_id[member_id]
        member["definition"]["equivalence_proof_refs"].append(
            {
                "proof_id": f"CONTROL1.FAMILY_SAFE_RATIO.{member_id.rsplit('.', 1)[-1]}",
                "proof_class": "DIRECT_PARAMETERIZED_FAMILY_COMPATIBILITY",
                "canonical_target_ref": family_target,
                "operator_shape": "numerator/max(denominator,1e-9)",
                "complete_compatibility_dimensions": [
                    "OPERATOR",
                    "DIMENSIONLESS_OUTPUT",
                    "DENOMINATOR_FLOOR",
                    "STATELESS_SAME_REQUEST",
                    "FAIL_CLOSED_NONFINITE_BOUNDARY",
                ],
                "proof_refs": family_proof_refs,
            }
        )
        member["relations"].append(
            {
                "relation_type": "FAMILY_BINDING_OF",
                "canonical_target_ref": family_target,
                "proof_refs": family_proof_refs,
                "parameter_mapping": {
                    "numerator": member["definition"]["input_schema"][0]["name"],
                    "denominator": member["definition"]["input_schema"][1]["name"],
                    "output": member["definition"]["output_schema"][0]["name"],
                    "epsilon": "1e-9",
                },
                "alias_equivalence_claim": False,
            }
        )

    yes_record = by_id["QTT.COMP.FORMULA.YES_EV"]
    no_record = by_id["QTT.COMP.FORMULA.NO_EV"]
    distinct_proof = [
        (
            "src/qtt/stage1_prediction_markets/"
            "pr162d_r2a_real_formulations/formula_seed_library.py::"
            "compute_yes_ev,compute_no_ev"
        ),
        "CONTROL1_DIRECT_PROOF::YES_AND_NO_EVENT_PAYOFF_PORTS_AND_PROBABILITY_COMPLEMENT_DIFFER",
    ]
    for source, target in ((yes_record, no_record), (no_record, yes_record)):
        source["relations"].append(
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": target["canonical_component_id"],
                "proof_refs": distinct_proof,
                "direct_distinction_basis": (
                    "YES and NO expected-value procedures use different price ports and "
                    "complemented probability semantics; shared cost terms do not make them aliases."
                ),
            }
        )

    for record in records:
        record["relations"].sort(
            key=lambda relation: (
                str(relation.get("relation_type", "")),
                str(relation.get("source_identity_or_alias", "")),
                str(relation.get("canonical_target_ref", "")),
            )
        )
        record["provenance"].sort(
            key=lambda row: (str(row["source_artifact_ref"]), str(row["source_row_ref"]))
        )


def _verify_fixed_source_fixtures(
    formula_specs: Sequence[Any],
    algorithm_specs: Sequence[Any],
    quantum_by_callable: Mapping[str, Sequence[Any]],
) -> dict[str, Any]:
    """Invoke bounded source fixtures without persisting any fixture vectors."""

    counts: Counter[str] = Counter()
    for spec in formula_specs:
        output = spec.compute(copy.deepcopy(dict(spec.test_inputs)))
        if not isinstance(output, Mapping):
            raise BuildError(f"formula fixture returned non-object: {spec.formula_id}")
        _json_line(output)
        counts["FORMULA"] += 1
    for spec in algorithm_specs:
        output = spec.implementation(copy.deepcopy(dict(spec.test_inputs)))
        if not isinstance(output, Mapping):
            raise BuildError(f"algorithm fixture returned non-object: {spec.algorithm_id}")
        _json_line(output)
        counts["ALGORITHM"] += 1
    for callable_ref, specs in sorted(quantum_by_callable.items()):
        representative = sorted(specs, key=lambda value: value.quantum_formulation_id)[0]
        fixture_inputs, _, output_schema, _ = _quantum_callable_contract(representative)
        output = representative.build_shape(copy.deepcopy(fixture_inputs))
        if not isinstance(output, Mapping):
            raise BuildError(f"quantum fixture returned non-object: {callable_ref}")
        if set(output) != {str(entry["name"]) for entry in output_schema}:
            raise BuildError(f"quantum fixture/schema key drift: {callable_ref}")
        _json_line(output)
        counts["QUANTUM_CALLABLE_FAMILY"] += 1
    total = sum(counts.values())
    expected = (
        EXPECTED_FORMULA_IMPLEMENTATIONS
        + EXPECTED_ALGORITHM_IMPLEMENTATIONS
        + EXPECTED_QUANTUM_CALLABLE_FAMILIES
    )
    if total != expected:
        raise BuildError(f"ephemeral fixture invocation count drift: {total} != {expected}")
    closed_leaf_fields = {
        formula_id: sorted(_closed_formula_fixture_inputs(spec))
        for spec in formula_specs
        if (formula_id := str(spec.formula_id))
        in {
            "IMPLIED_PROBABILITY",
            "PROBABILITY_EDGE",
            "MID_PRICE",
            "SPREAD",
            "RELATIVE_SPREAD",
        }
    }
    return {
        "source_fixture_invocation_counts": dict(sorted(counts.items())),
        "source_fixture_invocation_total": total,
        "persisted_fixture_vector_count": 0,
        "closed_facade_leaf_fixture_field_names": dict(sorted(closed_leaf_fields.items())),
        "closed_root_dependency_owned_input_count": 0,
    }


def _build_control1_expansion_proof_batch(
    pr162d_records: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
) -> dict[str, Any]:
    by_id = {
        str(record["canonical_component_id"]): copy.deepcopy(dict(record))
        for record in pr162d_records
    }
    quantum_records = [
        record
        for record in pr162d_records
        if str(record["canonical_component_id"]).startswith("QTT.COMP.QUANTUM.")
    ]
    original_model_records = [
        _original_economic_model_record(record, agent_ids)
        for record in sorted(
            quantum_records, key=lambda row: str(row["canonical_component_id"])
        )
    ]

    source_ref = "tests/pr169_qku_comp_control1/test_control1.py"
    implied = by_id["QTT.COMP.FORMULA.IMPLIED_PROBABILITY"]

    def occurrence(case: str) -> dict[str, Any]:
        candidate = copy.deepcopy(implied)
        candidate["provenance"].append(
            _source_provenance(
                source_ref=source_ref,
                row_ref=f"compiler_expansion_case[{case}]",
                local_name=f"CONTROL1_COMPILER_{case}",
                fields=("complete_typed_semantics", "compiler_outcome"),
                target=str(candidate["canonical_component_id"]),
                relation=f"COMPILER_EXPANSION_{case}",
            )
        )
        return candidate

    exact_duplicate = occurrence("EXACT_DUPLICATE")
    provenance_only = occurrence("PROVENANCE_ONLY")

    alias = occurrence("NAME_ALIAS")
    alias_id = "QTT.COMP.EXPANSION.IMPLIED_PROBABILITY_DIRECT_ALIAS"
    alias["canonical_component_id"] = alias_id
    alias["record_state"] = "PROVISIONAL"
    alias["origin_cohorts"] = ["POST_LAUNCH_EXPANSION_BATCH"]
    alias["relations"] = []
    alias["definition"]["equivalence_proof_refs"] = []
    for provenance in alias["provenance"]:
        provenance["canonical_target_ref"] = alias_id

    binding_update = occurrence("NEW_BINDING")
    new_binding = copy.deepcopy(binding_update["bindings"][0])
    new_binding["binding_id"] = "BINDING.RESEARCH.COMPILER.NEW_BINDING"
    new_binding["market"] = "CONTROL1_SYNTHETIC_MARKET"
    new_binding["context_selector"] = {
        "context_family": "CONTROL1_SYNTHETIC_BINDING_PROOF",
        "component_id": str(implied["canonical_component_id"]),
    }
    new_binding["supported_modes"] = []
    new_binding["mode_state"] = {}
    new_binding["readiness"] = {
        "specification": "PASS",
        "implementation": "PASS",
        "inputs": "REQUIRED",
        "requirements": "PASS",
        "oracle": "REQUIRED",
        "context": "REQUIRED",
        "evidence": "NONE",
        "authorization": "NOT_ELIGIBLE",
    }
    new_binding["derived_state"] = "VERIFIED"
    new_binding["exact_resolution_action_or_null"] = (
        "MISSING_INPUT_BINDING: CONTROL1_SYNTHETIC_MARKET"
    )
    new_binding["evidence_summary"] = {
        "evidence_ceiling": "NONE",
        "empirical_market_evidence": False,
        "limitations": ["SYNTHETIC_BINDING_COMPILER_PROOF_ONLY"],
    }
    new_binding["input_source_bindings"] = []
    new_binding["upstream_value_lineage"] = []
    binding_update["bindings"].append(new_binding)

    parameter_update = occurrence("NEW_PARAMETER_POLICY")
    parameter_update["bindings"][0]["selected_parameter_policy"] = {
        **dict(parameter_update["bindings"][0]["selected_parameter_policy"]),
        "expansion_compiler_case_ref": (
            "CONTROL1_SYNTHETIC_EXPANSION::PARAMETER_POLICY_PROVENANCE_UPDATE"
        ),
        "parameter_values_changed": False,
    }

    family = copy.deepcopy(by_id["QTT.COMP.FORMULA.NET_EDGE"])
    family_id = "QTT.COMP.EXPANSION.SAFE_RATIO_FAMILY_BINDING"
    family["canonical_component_id"] = family_id
    family["record_state"] = "PROVISIONAL"
    family["origin_cohorts"] = ["POST_LAUNCH_EXPANSION_BATCH"]
    family["provenance"] = [
        _source_provenance(
            source_ref=source_ref,
            row_ref="compiler_expansion_case[COMPATIBLE_FAMILY_MEMBER]",
            local_name="CONTROL1_SAFE_RATIO_FAMILY_BINDING",
            fields=("operator", "units", "domain", "boundary", "requirements"),
            target=family_id,
            relation="COMPILER_EXPANSION_COMPATIBLE_FAMILY_MEMBER",
        )
    ]
    family["relations"] = [
        {
            "relation_type": "FAMILY_BINDING_OF",
            "canonical_target_ref": "QTT.COMP.FORMULA.NET_EDGE",
            "proof_refs": [
                "tests/pr169_qku_comp_control1/test_control1.py::test_expansion_compiler_executes_build_owned_proof_and_is_idempotent"
            ],
        }
    ]

    true_new = _true_new_synthetic_record(agent_ids)
    similar_distinct = copy.deepcopy(true_new)
    distinct_id = "QTT.COMP.RESEARCH.SIGNED_PROBABILITY_DISTANCE"
    similar_distinct["canonical_component_id"] = distinct_id
    similar_distinct["definition"]["display_name"] = "SIGNED_PROBABILITY_DISTANCE"
    similar_distinct["definition"]["description"] = (
        "Bounded signed probability difference retained as distinct from absolute distance."
    )
    similar_distinct["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "signed_probability_distance = p_left - p_right"
    similar_distinct["definition"]["output_schema"] = [
        {
            "name": "signed_probability_distance",
            "type": "FINITE_DECIMAL_COMPATIBLE",
            "unit_or_basis": "SIGNED_PROBABILITY_DELTA_MINUS_1_TO_1",
        }
    ]
    similar_distinct["definition"]["units_and_bases"] = {
        "p_left": "PROBABILITY_DECIMAL_0_TO_1",
        "p_right": "PROBABILITY_DECIMAL_0_TO_1",
        "signed_probability_distance": "SIGNED_PROBABILITY_DELTA_MINUS_1_TO_1",
    }
    similar_distinct["uses"]["decision_outputs"] = ["signed_probability_distance"]
    similar_distinct["bindings"][0]["binding_id"] = (
        "BINDING.RESEARCH.SIGNED_PROBABILITY_DISTANCE"
    )
    similar_distinct["bindings"][0]["context_selector"]["component_id"] = distinct_id
    similar_distinct["bindings"][0]["exact_resolution_action_or_null"] = (
        f"MISSING_IMPLEMENTATION: {distinct_id}@1.0"
    )
    similar_distinct["provenance"] = [
        _source_provenance(
            source_ref=source_ref,
            row_ref="compiler_expansion_case[SIMILAR_BUT_DISTINCT]",
            local_name="SIGNED_PROBABILITY_DISTANCE",
            fields=("operator_sign", "output_range", "boundary"),
            target=distinct_id,
            relation="COMPILER_EXPANSION_SIMILAR_BUT_DISTINCT",
        )
    ]
    similar_distinct["relations"] = [
        {
            "relation_type": "DISTINCT_FROM",
            "canonical_target_ref": str(true_new["canonical_component_id"]),
            "proof_refs": [
                "tests/pr169_qku_comp_control1/test_control1.py::test_expansion_compiler_executes_build_owned_proof_and_is_idempotent"
            ],
            "direct_distinction_basis": (
                "Signed difference and absolute distance have different range, sign, and boundary semantics."
            ),
        }
    ]

    quantum_relation = copy.deepcopy(sorted(quantum_records, key=lambda row: str(row["canonical_component_id"]))[0])
    quantum_relation["provenance"].append(
        _source_provenance(
            source_ref=source_ref,
            row_ref="compiler_expansion_case[QUANTUM_ENCODING_RELATION]",
            local_name=str(quantum_relation["canonical_component_id"]),
            fields=("objective_map", "constraint_map", "inverse_map", "fallback"),
            target=str(quantum_relation["canonical_component_id"]),
            relation="COMPILER_EXPANSION_QUANTUM_ENCODING_RELATION",
        )
    )

    items: list[dict[str, Any]] = [
        {"record": exact_duplicate, "case": "EXACT_DUPLICATE"},
        {
            "record": alias,
            "case": "NAME_ALIAS",
            "equivalence_decision": "YES",
            "candidate_alias": "CONTROL1_SYNTHETIC_EXACT_ALIAS.IMPLIED_PROBABILITY",
        },
        {"record": provenance_only, "case": "PROVENANCE_ONLY"},
        {"record": binding_update, "case": "NEW_BINDING"},
        {"record": parameter_update, "case": "NEW_PARAMETER_POLICY"},
        {
            "record": family,
            "case": "COMPATIBLE_FAMILY_MEMBER",
            "equivalence_decision": "NO",
            "nonidentical_relation": "FAMILY_COMPATIBLE",
        },
        {
            "record": similar_distinct,
            "case": "SIMILAR_BUT_DISTINCT",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        {
            "record": true_new,
            "case": "TRUE_NEW",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        {"record": quantum_relation, "case": "QUANTUM_ENCODING_RELATION"},
    ]
    items.extend(
        {
            "record": record,
            "case": f"QUANTUM_ORIGINAL_MODEL::{record['canonical_component_id']}",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        }
        for record in original_model_records
    )
    batch = _expansion_batch(
        batch_id="EXPANSION.CONTROL1.SYNTHETIC.PROOF",
        origin="POST_LAUNCH_EXPANSION_BATCH",
        source_refs=[
            "tests/pr169_qku_comp_control1/test_control1.py",
            "tools/validate_pr169_qku_comp_control1.py",
            (
                "src/qtt/stage1_prediction_markets/"
                "pr162d_r2a_real_formulations/quantum_seed_library.py"
            ),
        ],
        source_classification="OWNER_SUBMITTED",
        items=items,
        requested_evidence_modes=("NONE", "FIXTURE"),
        requested_promotion_ceiling="STACK_READY",
    )
    # These proposals are intentionally not admitted as compiler items: one
    # would mint a synthetic QKU authority and the other would fabricate a new
    # implementation version without new reviewed code.  Their exact
    # rejection is reported separately from compiler-derived outcomes.
    batch["pre_compiler_rejections"] = [
        {
            "case": "QKU_ROLE_ADDITION",
            "decision": "REJECTED_BEFORE_ADMISSION",
            "exact_reason": "MISSING_EXISTING_QKU_AUTHORITY_AND_DIRECT_ROLE_PROOF",
        },
        {
            "case": "NEW_IMPLEMENTATION",
            "decision": "REJECTED_BEFORE_ADMISSION",
            "exact_reason": "NO_NEW_REVIEWED_IMPLEMENTATION_CODE_IN_THIS_BATCH",
        },
    ]
    return batch


def _build_pr162d_batch(
    repo_root: Path, agent_ids: Sequence[str], deadline: _Deadline
) -> dict[str, Any]:
    formula_module, algorithm_module, quantum_module = _import_r2a_modules(repo_root)
    formula_specs = list(formula_module.formula_specs())
    algorithm_specs = list(algorithm_module.algorithm_specs())
    quantum_specs = list(quantum_module.quantum_specs())
    quantum_by_callable: dict[str, list[Any]] = defaultdict(list)
    for spec in quantum_specs:
        quantum_by_callable[spec.callable_ref].append(spec)
    actual = (
        len(formula_specs),
        len(algorithm_specs),
        len(quantum_specs),
        len(quantum_by_callable),
    )
    expected = (
        EXPECTED_FORMULA_IMPLEMENTATIONS,
        EXPECTED_ALGORITHM_IMPLEMENTATIONS,
        EXPECTED_QUANTUM_FORMULATIONS,
        EXPECTED_QUANTUM_CALLABLE_FAMILIES,
    )
    if actual != expected:
        raise BuildError(f"PR162D callable inventory drift: {actual!r} != {expected!r}")
    deadline.check("PR162D callable inventory")
    fixture_metrics = _verify_fixed_source_fixtures(
        formula_specs, algorithm_specs, quantum_by_callable
    )
    records = [_formula_record(spec, agent_ids) for spec in formula_specs]
    records.extend(_algorithm_record(spec, agent_ids) for spec in algorithm_specs)
    quantum_records = [
        _quantum_family_record(specs, agent_ids)
        for _, specs in sorted(quantum_by_callable.items())
    ]
    records.extend(quantum_records)
    _apply_semantic_reuse_evidence(records)
    if len({row["canonical_component_id"] for row in records}) != len(records):
        raise BuildError("PR162D canonical component IDs are not unique")
    records.sort(key=lambda row: row["canonical_component_id"])
    batch = _expansion_batch(
        batch_id="EXPANSION.PR162D.EXPLICIT_IMPLEMENTATIONS",
        origin="PR162D_IMPLEMENTATION_BACKED",
        source_refs=[
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py",
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/algorithm_seed_library.py",
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/quantum_seed_library.py",
        ],
        source_classification="OWNER_SUBMITTED",
        items=records,
        requested_evidence_modes=("FIXTURE",),
        requested_promotion_ceiling="STACK_READY",
    )
    batch["ephemeral_fixture_metrics"] = fixture_metrics
    return batch


def _owner_requirement_record(
    card_id: str, semantic_key: str, family: str, agent_ids: Sequence[str]
) -> dict[str, Any]:
    component_id = f"QTT.COMP.OWNER_REQUIREMENT.{semantic_key}"
    exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {card_id}"
    definition = _definition(
        display_name=semantic_key,
        description=(
            f"Owner-supplied requirement {card_id}; requested name is preserved, "
            "but mathematics, domains, requirements, and implementation remain unresolved."
        ),
        component_kind="SPECIFICATION_REQUIRED",
        complete_definition=exact_action,
    )
    definition["owner_requirement_crosswalk"] = {
        "owner_requirement_id": card_id,
        "original_requested_name": semantic_key,
        "original_text_ref": f"OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY::{card_id}",
        "component_kind": "SPECIFICATION_REQUIRED",
        "semantic_decomposition": {
            "status": "SPECIFICATION_REQUIRED",
            "known_requested_name": semantic_key,
            "missing_semantics": [
                "MATHEMATICAL_OR_PROCEDURAL_DEFINITION",
                "INPUT_OUTPUT_UNITS_AND_BASES",
                "DOMAIN_BOUNDARY_TIME_AND_STATE_SEMANTICS",
                "TYPED_REQUIREMENTS",
                "INDEPENDENT_ORACLE",
            ],
            "candidate_interpretations": [],
        },
        "canonical_component_target": component_id,
        "qku_role_binding_refs": [],
        "implementation_status": "MISSING_IMPLEMENTATION_UNTIL_SPECIFICATION_CLOSES",
        "binding_readiness_status": "SPECIFICATION_REQUIRED",
        "agent_policy": "RESEARCH_STATUS_EXPLAIN_AND_PROPOSE_BATCH_ITEM_ONLY",
        "decision_roles": _family_decision_roles(family),
        "evidence_route": "INDEPENDENT_ORACLE_THEN_NONLIVE_EVIDENCE_LANES",
        "exact_resolution_action": exact_action,
        "responsible_agent": "research_agent",
        "required_source_or_derivation": "OWNER_OR_DOMAIN_AUTHORITY_COMPLETE_SEMANTIC_SPECIFICATION",
        "exact_acceptance_test": "INDEPENDENT_SEMANTIC_SPECIFICATION_AND_ORACLE_REQUIRED",
        "priority_and_launch_role": "UNRANKED_UNTIL_SEMANTIC_DECOMPOSITION",
    }
    return _record(
        component_id=component_id,
        record_state="PROVISIONAL",
        origins=["OWNER_REQUIREMENT_213"],
        definition=definition,
        decision_roles=_family_decision_roles(family),
        bindings=[
            _binding(
                component_id,
                binding_id=f"BINDING.OWNER_REQUIREMENT.REVIEW.{card_id}",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref="OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY",
                row_ref=card_id,
                local_name=semantic_key,
                fields=("card_id", "formula_family", "semantic_key"),
                target=component_id,
                relation="PROVISIONAL_OWNER_REQUIREMENT_NO_INHERITED_IMPLEMENTATION_CLAIM",
            )
        ],
        market_tags=[f"OWNER_REQUIREMENT_FAMILY_{family}"],
        producer_owner="OWNER_REQUIREMENT_INTAKE_VIA_CONTROL1_BUILDER",
    )


def _build_owner_requirement_batch(
    agent_ids: Sequence[str], deadline: _Deadline
) -> dict[str, Any]:
    records = [
        _owner_requirement_record(card_id, semantic_key, family, agent_ids)
        for card_id, semantic_key, family in _owner_requirements()
    ]
    deadline.check("owner requirement inventory")
    if len({record["canonical_component_id"] for record in records}) != len(records):
        raise BuildError("owner requirement component IDs are not unique")
    records.sort(key=lambda row: row["canonical_component_id"])
    return _expansion_batch(
        batch_id="EXPANSION.OWNER_REQUIREMENT.213",
        origin="OWNER_REQUIREMENT_213",
        source_refs=[
            "OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY",
            "OWNER_PROVIDED_MASTER_PLAN_CURRENT#owner-requirement-doctrine",
            "OWNER_CONTROLLING_PROMPT_PR169_QKU_COMP_CONTROL1_V5_1#section-12",
        ],
        source_classification="OWNER_SUBMITTED",
        items=records,
        requested_evidence_modes=("NONE",),
        requested_promotion_ceiling="SPECIFIED",
    )


def _build_registry_and_batches(
    repo_root: Path,
    deadline: _Deadline,
    base_records: Sequence[Mapping[str, Any]] = (),
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    tuple[str, ...],
    list[dict[str, Any]],
]:
    repo_root = repo_root.resolve()
    agent_ids = _load_agent_ids(repo_root)
    rp5c_batch = _build_rp5c_batch(repo_root, agent_ids, deadline, base_records)
    pr162d_batch = _build_pr162d_batch(repo_root, agent_ids, deadline)
    pr162d_records = [
        copy.deepcopy(dict(item["record"]))
        for item in pr162d_batch["items"]
        if isinstance(item, Mapping) and isinstance(item.get("record"), Mapping)
    ]
    batches = [
        rp5c_batch,
        pr162d_batch,
        _build_control1_expansion_proof_batch(pr162d_records, agent_ids),
        _build_owner_requirement_batch(agent_ids, deadline),
    ]
    records, compiler_reports = _compile_batches(base_records, batches, deadline)
    _validate_registry(records, deadline)
    return records, batches, agent_ids, compiler_reports


def build_registry(repo_root: str | Path) -> list[dict[str, Any]]:
    """Build and return the deterministic logical registry without publishing it."""
    records, _, _, _ = _build_registry_and_batches(
        Path(repo_root), _Deadline(3_600_000)
    )
    return records


def _control_module() -> Any:
    """Load the single fixed CONTROL1 implementation owner, never a caller path."""

    for module_name in ("qtt.computation_control.control", "src.qtt.computation_control.control"):
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
    raise BuildError("the fixed qtt.computation_control.control owner is not importable")


def _control_storage_policy() -> dict[str, Any]:
    policy = getattr(_control_module(), "STORAGE_POLICY", None)
    if not isinstance(policy, Mapping):
        raise BuildError("control owner does not expose its centralized STORAGE_POLICY")
    return dict(policy)


def _validate_record_with_control(record: Mapping[str, Any]) -> None:
    helper = getattr(_control_module(), "_validate_record_shape", None)
    if not callable(helper):
        raise BuildError("control owner lacks required private record-shape validator")
    result = helper(record)
    if result is False:
        raise BuildError(
            f"control shape validation rejected {record.get('canonical_component_id')}"
        )


def _batch_item_record(item: Mapping[str, Any]) -> Mapping[str, Any]:
    record = item.get("record")
    if isinstance(record, Mapping):
        return record
    if "canonical_component_id" in item and "definition" in item:
        return item
    raise BuildError("typed expansion item has no materialized record")


def _compile_batches(
    base_records: Sequence[Mapping[str, Any]],
    batches: Sequence[Mapping[str, Any]],
    deadline: _Deadline,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run every current cohort through the one private expansion compiler."""

    compiler = getattr(_control_module(), "_compile_expansion_batch", None)
    if not callable(compiler):
        raise BuildError("control owner lacks its private expansion compiler")
    records = [copy.deepcopy(dict(record)) for record in base_records]
    reports: list[dict[str, Any]] = []
    for batch in batches:
        deadline.check(f"compile {batch.get('batch_id', '<unknown>')}")
        before_ids = {str(record["canonical_component_id"]) for record in records}
        try:
            candidate_records, delta, raw_report = compiler(records, batch)
        except Exception as exc:
            raise BuildError(
                f"expansion compiler rejected {batch.get('batch_id')}: {exc}"
            ) from exc
        if not isinstance(candidate_records, (list, tuple)):
            raise BuildError("expansion compiler did not return candidate records")
        if not isinstance(raw_report, Mapping):
            raise BuildError("expansion compiler did not return its outcome report")
        delta_value = delta.as_dict() if hasattr(delta, "as_dict") else vars(delta)
        if not isinstance(delta_value, Mapping) or delta_value.get(
            "registry_schema_version"
        ) != REGISTRY_SCHEMA_VERSION:
            raise BuildError("expansion compiler returned an incompatible transient delta")
        records = [copy.deepcopy(dict(record)) for record in candidate_records]
        after_ids = {str(record["canonical_component_id"]) for record in records}

        cases_by_component: dict[str, list[str]] = defaultdict(list)
        ordered_items = sorted(
            (
                item
                for item in batch.get("items", [])
                if isinstance(item, Mapping)
            ),
            key=lambda item: (
                str(_batch_item_record(item).get("canonical_component_id", "")),
                str(_batch_item_record(item).get("semantic_version", "")),
                _json_line(item),
            ),
        )
        for item in ordered_items:
            component_id = str(
                _batch_item_record(item).get("canonical_component_id", "")
            )
            cases_by_component[component_id].append(
                str(item.get("case", f"SOURCE_INTAKE::{component_id}"))
            )

        report = copy.deepcopy(dict(raw_report))
        annotated_outcomes: list[dict[str, Any]] = []
        for raw_outcome in report.get("outcomes", []):
            if not isinstance(raw_outcome, Mapping):
                raise BuildError("expansion compiler emitted a non-object outcome")
            outcome = copy.deepcopy(dict(raw_outcome))
            component_id = str(outcome.get("candidate", ""))
            cases = cases_by_component.get(component_id, [])
            if not cases:
                raise BuildError(
                    f"compiler outcome has no source batch item: {component_id}"
                )
            outcome["case"] = cases.pop(0)
            outcome["new_record_count"] = int(
                component_id not in before_ids
                and component_id in after_ids
                and str(outcome.get("canonical_target")) == component_id
            )
            annotated_outcomes.append(outcome)
        if any(cases for cases in cases_by_component.values()):
            raise BuildError("compiler omitted one or more typed batch item outcomes")
        report["outcomes"] = annotated_outcomes
        report["transient_delta"] = {
            key: copy.deepcopy(value)
            for key, value in delta_value.items()
            if key
            in {
                "batch_id",
                "registry_schema_version",
                "added_component_ids",
                "changed_component_ids",
                "retired_component_ids",
                "added_binding_ids",
                "changed_binding_ids",
                "removed_binding_ids",
                "affected_dependent_ids",
                "affected_consumer_classes",
            }
        }
        report["pre_compiler_rejections"] = copy.deepcopy(
            list(batch.get("pre_compiler_rejections", []))
        )
        reports.append(report)
    return sorted(records, key=lambda row: (row["canonical_component_id"], row["semantic_version"])), reports


def _semantic_core(record: Mapping[str, Any]) -> dict[str, Any]:
    definition = record.get("definition", {})
    return {field: copy.deepcopy(definition.get(field)) for field in _SEMANTIC_CORE_FIELDS}


def _validate_registry(records: Sequence[Mapping[str, Any]], deadline: _Deadline) -> None:
    required_top = {
        "canonical_component_id",
        "semantic_version",
        "record_state",
        "origin_cohorts",
        "definition",
        "uses",
        "bindings",
        "provenance",
        "relations",
        "governance",
    }
    ids: set[str] = set()
    implementation_counts: Counter[str] = Counter()
    owner_requirement_count = 0
    for index, record in enumerate(records):
        if index % 1_000 == 0:
            deadline.check("registry shape validation")
        missing = sorted(required_top - set(record))
        if missing:
            raise BuildError(
                f"record {record.get('canonical_component_id')} lacks fields: {missing}"
            )
        component_id = str(record["canonical_component_id"])
        if not component_id or component_id in ids:
            raise BuildError(f"duplicate or empty canonical component ID: {component_id!r}")
        ids.add(component_id)
        if record["record_state"] not in {
            "PROVISIONAL",
            "UNDER_REVIEW",
            "CANONICAL_ACCEPTED",
            "SUPERSEDED",
            "DORMANT_PRESERVED",
            "REJECTED_INVALID",
            "INAPPLICABLE_WITH_PROOF",
        }:
            raise BuildError(f"invalid record state for {component_id}")
        definition = record["definition"]
        for field in _SEMANTIC_CORE_FIELDS:
            if field not in definition:
                raise BuildError(f"definition {component_id} lacks semantic field {field}")
        qku_roles = record.get("uses", {}).get("qku_role_bindings", [])
        incomplete_rp5c_role_import = bool(
            component_id.startswith("QTT.COMP.RP5C.")
            and qku_roles
            and str(definition.get("complete_mathematical_or_procedural_definition", ""))
            .startswith("MISSING_SEMANTIC_SPECIFICATION:")
        )
        if incomplete_rp5c_role_import:
            if record["record_state"] in {
                "CANONICAL_ACCEPTED",
                "PROVISIONAL",
                "UNDER_REVIEW",
            }:
                raise BuildError(
                    f"incomplete RP5C QKU role import exposed an active runtime root: {component_id}"
                )
            for role in qku_roles:
                if role.get("runtime_root_eligibility") != (
                    "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
                ):
                    raise BuildError(
                        f"incomplete RP5C QKU role lacks runtime ineligibility: {component_id}"
                    )
                if role.get("stack_root_or_direct_component") is not None:
                    raise BuildError(
                        f"builder invented an RP5C runtime root without semantics: {component_id}"
                    )
                if role.get("selection_rule_if_container") is not None:
                    raise BuildError(
                        f"builder invented an RP5C selection rule without semantics: {component_id}"
                    )
        inventory_class = definition.get("implementation_inventory_class")
        if inventory_class is not None:
            if inventory_class not in {"FORMULA", "ALGORITHM", "QUANTUM_CALLABLE_FAMILY"}:
                raise BuildError(f"invalid implementation inventory class for {component_id}")
            implementation_counts[inventory_class] += 1
        for implementation in definition.get("implementation_versions", []):
            if "fixture_inputs" in implementation or "test_inputs" in implementation:
                raise BuildError(
                    f"fixture vector embedded in canonical implementation metadata: {component_id}"
                )
        if definition.get("owner_requirement_crosswalk"):
            owner_requirement_count += 1
        for binding in record["bindings"]:
            if not binding.get("binding_id"):
                raise BuildError(f"empty binding ID for {component_id}")
            readiness = binding.get("readiness", {})
            if readiness.get("authorization") != "NOT_ELIGIBLE":
                raise BuildError(f"builder may not authorize binding {binding['binding_id']}")
            if binding.get("runtime_snapshot_ref_or_null") is not None:
                raise BuildError(f"builder may not create runtime snapshot for {component_id}")
            if binding.get("exact_resolution_action_or_null") in {
                "TBD",
                "SCOPED_GAP",
                "future consumer",
                "metadata only",
                "solver compatible",
                "route later",
                "placeholder",
            }:
                raise BuildError(f"generic terminal text in {component_id}")
        _json_line(record)
        _validate_record_with_control(record)

    expected_implementation_counts = {
        "FORMULA": EXPECTED_FORMULA_IMPLEMENTATIONS,
        "ALGORITHM": EXPECTED_ALGORITHM_IMPLEMENTATIONS,
        "QUANTUM_CALLABLE_FAMILY": EXPECTED_QUANTUM_CALLABLE_FAMILIES,
    }
    if dict(implementation_counts) != expected_implementation_counts:
        raise BuildError(
            "implementation-backed definition counts drift: "
            f"{dict(implementation_counts)!r} != {expected_implementation_counts!r}"
        )
    if owner_requirement_count != EXPECTED_OWNER_REQUIREMENTS:
        raise BuildError(
            f"owner requirement coverage drift: {owner_requirement_count} != {EXPECTED_OWNER_REQUIREMENTS}"
        )
    rp5c_count = sum(component_id.startswith("QTT.COMP.RP5C.") for component_id in ids)
    if rp5c_count != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(f"RP5C coverage drift: {rp5c_count} != {EXPECTED_RP5C_IDENTITIES}")

    # Independently derive the requirement graph and reject unresolved targets
    # or cycles before any physical layout is staged.
    graph: dict[str, set[str]] = {component_id: set() for component_id in ids}
    for record in records:
        component_id = str(record["canonical_component_id"])
        for requirement in record["definition"].get("requirements", []):
            target = requirement.get("required_component_id_or_source_selector")
            if target not in ids:
                raise BuildError(f"unresolved canonical requirement {component_id} -> {target}")
            if not str(target).startswith(("QTT.", "RP5C_")):
                raise BuildError(f"source-local requirement remained after compile: {target}")
            graph[component_id].add(str(target))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise BuildError(f"post-canonicalization requirement cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(graph[node]):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for component_id in sorted(ids):
        visit(component_id)


def _read_registry_layout(out_dir: Path, deadline: _Deadline) -> list[dict[str, Any]]:
    deadline.check("load accepted cumulative registry")
    loader = getattr(_control_module(), "_load_logical_registry", None)
    if not callable(loader):
        raise BuildError("control owner lacks its hardened logical registry loader")
    try:
        records, _ = loader(out_dir)
    except FileNotFoundError:
        return []
    except Exception as exc:
        raise BuildError(f"invalid accepted CONTROL1 registry layout: {exc}") from exc
    if not isinstance(records, list):
        raise BuildError("control logical registry loader returned invalid records")
    return [copy.deepcopy(dict(record)) for record in records]


def _accepted_base_ref(repo_root: Path) -> str:
    """Return the PR branch's exact VCS merge-base with required ``main``."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "HEAD", "origin/main"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BuildError(f"cannot resolve accepted Git base: {exc}") from exc
    base_ref = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40}", base_ref):
        detail = result.stderr.strip()
        raise BuildError(f"cannot resolve required origin/main merge-base: {detail}")
    return base_ref


def _git_base_tree_paths(
    repo_root: Path, base_ref: str, prefix: Path
) -> set[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-tree",
                "-r",
                "-z",
                "--name-only",
                base_ref,
                "--",
                f"{prefix.as_posix()}/",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BuildError(f"cannot enumerate accepted Git base tree: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BuildError(f"cannot enumerate accepted Git base tree: {detail}")
    try:
        return {
            value.decode("utf-8", errors="strict")
            for value in result.stdout.split(b"\0")
            if value
        }
    except UnicodeDecodeError as exc:
        raise BuildError(f"invalid accepted Git base path encoding: {exc}") from exc


def _materialize_git_base_path(
    repo_root: Path, base_ref: str, relative_path: Path, destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as handle:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "show",
                    f"{base_ref}:{relative_path.as_posix()}",
                ],
                stdin=subprocess.DEVNULL,
                stdout=handle,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        destination.unlink(missing_ok=True)
        raise BuildError(f"cannot read accepted Git base path {relative_path}: {exc}") from exc
    if result.returncode != 0:
        destination.unlink(missing_ok=True)
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BuildError(f"cannot read accepted Git base path {relative_path}: {detail}")


def _read_accepted_registry_from_base(
    repo_root: Path, deadline: _Deadline
) -> list[dict[str, Any]]:
    """Read the cumulative accepted registry from the required base branch.

    Generated files already present in the worktree may be a staged candidate,
    so they are never promoted to accepted base state merely by existing.  Git
    is used only as VCS metadata; no QTT digest or content identity is created.
    """

    base_ref = _accepted_base_ref(repo_root)
    single_rel = GENERATED_PREFIX / "registry.jsonl"
    manifest_rel = GENERATED_PREFIX / "registry.manifest.json"
    tree_paths = _git_base_tree_paths(repo_root, base_ref, GENERATED_PREFIX)
    if not tree_paths:
        return []
    prefix_text = f"{GENERATED_PREFIX.as_posix()}/"
    relative_names: set[str] = set()
    for path_text in tree_paths:
        if not path_text.startswith(prefix_text):
            raise BuildError(f"accepted Git base escaped CONTROL1 prefix: {path_text}")
        relative = path_text.removeprefix(prefix_text)
        if not relative or Path(relative).name != relative:
            raise BuildError(f"accepted Git base contains nested CONTROL1 path: {path_text}")
        relative_names.add(relative)
    has_single = single_rel.name in relative_names
    has_manifest = manifest_rel.name in relative_names
    shard_names = {
        name
        for name in relative_names
        if name.startswith("registry.part-") and name.endswith(".jsonl")
    }
    allowed_names = {"acceptance.report.json", *shard_names}
    if has_single:
        allowed_names.add(single_rel.name)
    if has_manifest:
        allowed_names.add(manifest_rel.name)
    unexpected = sorted(relative_names - allowed_names)
    if unexpected:
        raise BuildError(f"accepted Git base contains unexpected CONTROL1 files: {unexpected}")
    if "acceptance.report.json" not in relative_names:
        raise BuildError("accepted Git base lacks acceptance.report.json")
    if has_single and (has_manifest or shard_names):
        raise BuildError("accepted Git base contains two CONTROL1 physical layouts")
    if has_manifest != bool(shard_names):
        raise BuildError(
            "accepted Git base has incomplete sharded layout: "
            f"manifest={has_manifest}, shards={sorted(shard_names)!r}"
        )
    if not has_single and not has_manifest:
        raise BuildError("accepted Git base has no CONTROL1 registry layout")
    with tempfile.TemporaryDirectory(prefix="qtt-control1-accepted-base-") as temporary:
        staged = Path(temporary)
        if has_single:
            _materialize_git_base_path(
                repo_root, base_ref, single_rel, staged / single_rel.name
            )
        else:
            manifest_path = staged / manifest_rel.name
            _materialize_git_base_path(repo_root, base_ref, manifest_rel, manifest_path)
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise BuildError(f"invalid accepted Git base manifest: {exc}") from exc
            partitions = manifest.get("partitions") if isinstance(manifest, Mapping) else None
            if not isinstance(partitions, list) or not partitions:
                raise BuildError("accepted Git base manifest has no partitions")
            names: set[str] = set()
            for partition in partitions:
                name = str(partition.get("file") or "") if isinstance(partition, Mapping) else ""
                if (
                    not name.startswith("registry.part-")
                    or not name.endswith(".jsonl")
                    or Path(name).name != name
                    or name in names
                ):
                    raise BuildError(f"unsafe accepted Git base shard name: {name!r}")
                names.add(name)
                relative = GENERATED_PREFIX / name
                _materialize_git_base_path(
                    repo_root, base_ref, relative, staged / name
                )
                deadline.check("materialize accepted Git base registry")
            if names != shard_names:
                raise BuildError(
                    "accepted Git base manifest/shard set mismatch: "
                    f"declared={sorted(names)!r}, tree={sorted(shard_names)!r}"
                )
        return _read_registry_layout(staged, deadline)


def _load_cumulative_base_records(
    repo_root: Path, target: Path, deadline: _Deadline
) -> list[dict[str, Any]]:
    """Load only accepted Git-base state, independent of output location."""

    del target  # Physical candidate location is never an acceptance authority.
    return _read_accepted_registry_from_base(repo_root, deadline)


def _derive_update(
    base_records: Sequence[Mapping[str, Any]], candidate_records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    helper = getattr(_control_module(), "_derive_registry_update", None)
    if not callable(helper):
        raise BuildError("control owner lacks required transient RegistryUpdateV1 derivation")
    result = helper(
        base_records,
        candidate_records,
        batch_id="TRANSIENT.CONTROL1.BUILD",
    )
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    elif hasattr(result, "__dict__") and not isinstance(result, Mapping):
        result = vars(result)
    if not isinstance(result, Mapping):
        raise BuildError("control _derive_registry_update returned a non-mapping")
    value = dict(result)
    if value.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise BuildError("registry delta schema version is incompatible")
    return value


def _measure_registry(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    serialized_bytes = 0
    max_record_bytes = 0
    for record in records:
        size = len(_json_line(record).encode("utf-8"))
        serialized_bytes += size
        max_record_bytes = max(max_record_bytes, size)
    started = time.perf_counter()
    index = {str(record["canonical_component_id"]): record for record in records}
    index_build_ms = round((time.perf_counter() - started) * 1000.0, 3)
    if len(index) != len(records):
        raise BuildError("index construction detected duplicate canonical IDs")
    return {
        "logical_registry_rows": len(records),
        "logical_registry_serialized_bytes": serialized_bytes,
        "maximum_record_serialized_bytes": max_record_bytes,
        "index_build_ms": index_build_ms,
    }


def _write_layout(
    records: Sequence[Mapping[str, Any]],
    out_dir: Path,
    *,
    force_layout: str,
    measurements: Mapping[str, Any],
    shape_validation_ms: float,
) -> dict[str, Any]:
    helper = getattr(_control_module(), "_write_registry_layout", None)
    if not callable(helper):
        raise BuildError("control owner lacks the sole logical-registry layout writer")
    policy = _control_storage_policy()
    reasons: list[str] = []
    effective_layout = force_layout
    if force_layout != "auto":
        reasons.append(f"FORCED_{force_layout.upper()}")
    else:
        measured_checks = (
            (
                measurements["logical_registry_rows"]
                > int(policy["single_file_max_rows"]),
                "ROW_COUNT",
            ),
            (
                measurements["logical_registry_serialized_bytes"]
                > int(policy["single_file_max_serialized_bytes"]),
                "SERIALIZED_BYTES",
            ),
            (
                measurements["maximum_record_serialized_bytes"]
                > int(policy["max_record_serialized_bytes"]),
                "MAXIMUM_RECORD_SIZE",
            ),
            (
                measurements["index_build_ms"]
                > int(policy["single_file_max_index_build_ms"]),
                "INDEX_BUILD_TIME",
            ),
            (
                shape_validation_ms
                > int(policy["single_file_max_validation_ms"]),
                "VALIDATION_TIME",
            ),
            (
                measurements["logical_registry_serialized_bytes"]
                > int(policy["diff_size_budget_bytes"]),
                "DIFF_SIZE_BUDGET",
            ),
        )
        reasons = [name for exceeded, name in measured_checks if exceeded]
        if reasons:
            effective_layout = "sharded"
        else:
            reasons.append("WITHIN_CONTROL_STORAGE_POLICY")
    result = helper(records, out_dir, force_layout=effective_layout)
    if result is None:
        result = {}
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    elif hasattr(result, "__dict__") and not isinstance(result, Mapping):
        result = vars(result)
    if not isinstance(result, Mapping):
        raise BuildError("control _write_registry_layout returned a non-mapping")
    inspected = _inspect_layout(out_dir)
    inspected["control_writer_result"] = dict(result)
    inspected["policy_reasons"] = reasons
    inspected["storage_policy"] = policy
    return inspected


def _inspect_layout(out_dir: Path) -> dict[str, Any]:
    full = out_dir / "registry.jsonl"
    manifest = out_dir / "registry.manifest.json"
    shards = sorted(out_dir.glob("registry.part-*.jsonl"))
    if full.is_file() and (manifest.is_file() or shards):
        raise BuildError("writer emitted two active physical registry layouts")
    if full.is_file():
        return {"layout": "single", "shard_count": 0, "registry_files": [full.name]}
    if manifest.is_file() and shards:
        return {
            "layout": "sharded",
            "shard_count": len(shards),
            "registry_files": [manifest.name, *(path.name for path in shards)],
        }
    raise BuildError("writer did not emit one complete active registry layout")


def _source_closure() -> list[dict[str, Any]]:
    return [
        {
            "semantic_domain": "RP5C immutable identities, QKU roles, duplicate-member custody, lineage",
            "current_owner": "RP5C_IMMUTABLE_BASELINE",
            "accepted_sources": [
                RP5C_DEDUPE.as_posix(),
                RP5C_LINEAGE.as_posix(),
                *(path.as_posix() for path in RP5C_LIBRARIES),
            ],
            "fields_consumed": [
                "canonical_identity_row_id",
                "identity_row_id",
                "duplicate_group_id",
                "duplicate_member_identity_row_ids",
                "identity_type",
                "qku_id",
                "formula_id",
                "formula_variant_id",
                "formula_expression_ref",
                "plugin_ref",
                "source_artifact_row_id",
                "source_line_or_json_path",
                "market_family",
                "ontology_category",
                "stage1_seed_inclusion_flag",
                "stage1_dormant_future_market_flag",
            ],
            "record_destination": "ComputationRecordV1 provenance/relations/uses/bindings",
            "use": "BUILD_TIME_ONLY",
            "forbidden_mutation": (
                "RP5C source rows remain immutable; ordinal source IDs are evidence, "
                "the structured six-field custody key preserves CONTROL1 continuity, "
                "and neither is semantic-equivalence or runtime authority"
            ),
            "conflict_resolution": "baseline provenance, not continuing write or runtime authority",
        },
        {
            "semantic_domain": "PR162D formulas, deterministic algorithms, quantum shape callables",
            "current_owner": "PR162D_R2A_REAL_FORMULATIONS",
            "accepted_sources": [
                "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py",
                "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/algorithm_seed_library.py",
                "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/quantum_seed_library.py",
            ],
            "fields_consumed": [
                "identity",
                "expression_or_procedure_or_objective",
                "explicit_callable_ref",
                "typed_port_names",
                "unit_hints",
                "family_and_variant",
                "latency_class",
                "fixture_reference",
            ],
            "record_destination": "ComputationRecordV1 definition/uses/fixture binding/provenance",
            "use": "BUILD_TIME_REGISTRATION_AND_RUNTIME_ALLOWLIST_REFERENCE",
            "forbidden_mutation": "no caller-selected module path and no inherited live authority",
            "conflict_resolution": "source-derived fixtures are invocation evidence, not independent oracles",
        },
        {
            "semantic_domain": "owner-supplied 213 mathematical and procedural requests",
            "current_owner": "OWNER_REQUIREMENT_INTAKE",
            "accepted_sources": [
                "OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY",
                "MASTER_PLAN_OWNER_REQUIREMENT_DOCTRINE",
                "CONTROL1_PROMPT_SECTION_12",
            ],
            "fields_consumed": ["card_id", "family", "requested_semantic_name"],
            "record_destination": "provisional ComputationRecordV1 owner_requirement_crosswalk",
            "use": "BUILD_TIME_ONLY_UNTIL_SPECIFICATION_CLOSES",
            "forbidden_mutation": "no restored implementation, callable, alias, PASS, or route claim",
            "conflict_resolution": "reverted/closed PR is negative evidence and inventory custody only",
        },
        {
            "semantic_domain": "PR165-D2 agent roster and duties",
            "current_owner": "PR165_D2_AGENT_ROSTER",
            "accepted_sources": [PR165_D2_ROSTER.as_posix()],
            "fields_consumed": ["agent_id", "agent_family", "agent_role", "authority_boundary"],
            "record_destination": "bindings.agent_access_policy",
            "use": "BUILD_TIME_POLICY_DERIVATION",
            "forbidden_mutation": "no second roster and no permission expansion",
            "conflict_resolution": "classification policy, never per-formula routes",
        },
        {
            "semantic_domain": "MAP3/RP5D/R1/RP5E/PR162B/GFP source closure",
            "current_owner": "EXISTING_HISTORICAL_AND_CURRENT_SOURCE_OWNERS",
            "accepted_sources": [
                "PR168_MAP3_CURRENT_EQUIVALENTS",
                "PR168_RP5D_CURRENT_EQUIVALENTS",
                "PR168_RP5D_R1_CURRENT_EQUIVALENTS",
                "PR168_RP5E_CURRENT_EQUIVALENTS",
                "PR162B_CURRENT_EQUIVALENTS",
                "PR168_GFP_REAL_COMPUTATION_CURRENT_EQUIVALENT",
            ],
            "fields_consumed": ["manifest_counts", "current_owner", "implementation_and_evidence_caveats"],
            "record_destination": "acceptance limitations and exact later compiler intake action",
            "use": "AUDIT_AND_CURRENT_OWNER_REFERENCE",
            "forbidden_mutation": "no duplicate registry, copied graph, or unproven equivalence",
            "conflict_resolution": "not duplicated into this compact builder without direct semantic proof",
        },
    ]


def _run_scale_probe(record_count: int) -> dict[str, Any]:
    if record_count < 0:
        raise BuildError("scale_probe_records cannot be negative")
    if record_count == 0:
        return {
            "executed": False,
            "requested_records": 0,
            "exact_action": "RUN_WITH_SCALE_PROBE_RECORDS_AT_LEAST_10000_FOR_OPT_IN_PROBE",
        }
    started = time.perf_counter()
    rows = [
        {
            "canonical_component_id": f"QTT.SCALE.PROBE.{index:06d}",
            "semantic_version": "1.0",
            "requirements": ([f"QTT.SCALE.PROBE.{index - 1:06d}"] if index else []),
        }
        for index in range(record_count)
    ]
    materialization_ms = round((time.perf_counter() - started) * 1000.0, 3)
    started = time.perf_counter()
    index = {row["canonical_component_id"]: row for row in rows}
    index_build_ms = round((time.perf_counter() - started) * 1000.0, 3)
    lookup_ids = [
        "QTT.SCALE.PROBE.000000",
        f"QTT.SCALE.PROBE.{record_count // 2:06d}",
        f"QTT.SCALE.PROBE.{record_count - 1:06d}",
    ]
    started = time.perf_counter()
    selected = [index[component_id] for component_id in lookup_ids]
    lookup_ms = round((time.perf_counter() - started) * 1000.0, 6)
    return {
        "executed": True,
        "requested_records": record_count,
        "fixed_seed_or_order_policy": "DETERMINISTIC_SEQUENTIAL_SYNTHETIC_IDS_NO_RANDOMNESS",
        "materialization_ms": materialization_ms,
        "index_build_ms": index_build_ms,
        "representative_indexed_lookup_ms": lookup_ms,
        "representative_lookup_count": len(selected),
        "records_examined_per_lookup": 1,
        "persistent_artifact_created": False,
        "latency_or_profit_claim": False,
    }


def _delta_summary(delta: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "added_component_ids",
        "changed_component_ids",
        "retired_component_ids",
        "added_binding_ids",
        "changed_binding_ids",
        "removed_binding_ids",
        "affected_dependent_ids",
    )
    summary = {f"{field}_count": len(delta.get(field, [])) for field in fields}
    summary["affected_consumer_classes"] = sorted(
        set(delta.get("affected_consumer_classes", []))
    )
    summary["registry_schema_version"] = delta.get("registry_schema_version")
    summary["persistent_delta_written"] = False
    return summary


def _acceptance_report(
    records: Sequence[Mapping[str, Any]],
    batches: Sequence[Mapping[str, Any]],
    compiler_reports: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
    layout: Mapping[str, Any],
    measurements: Mapping[str, Any],
    delta: Mapping[str, Any],
    scale_probe: Mapping[str, Any],
    *,
    base_record_count: int,
    shape_validation_ms: float,
    total_build_ms: float,
) -> dict[str, Any]:
    state_counts = Counter(str(row["record_state"]) for row in records)
    origin_counts: Counter[str] = Counter()
    inventory_counts: Counter[str] = Counter()
    decision_role_counts: Counter[str] = Counter()
    exact_actions: Counter[str] = Counter()
    semantic_relation_counts: Counter[str] = Counter()
    provenance_relation_counts: Counter[str] = Counter()
    native_implementation_count = 0
    qku_role_count = 0
    requirements_count = 0
    for record in records:
        origin_counts.update(record.get("origin_cohorts", []))
        inventory_class = record.get("definition", {}).get("implementation_inventory_class")
        if inventory_class:
            inventory_counts[str(inventory_class)] += 1
        decision_role_counts.update(record.get("uses", {}).get("decision_roles", []))
        qku_role_count += len(record.get("uses", {}).get("qku_role_bindings", []))
        requirements_count += len(record.get("definition", {}).get("requirements", []))
        for implementation in record.get("definition", {}).get("implementation_versions", []):
            if implementation.get("code_owner") == "CONTROL1_PRIVATE_RUNTIME":
                native_implementation_count += 1
        for relation in record.get("relations", []):
            relation_type = str(relation.get("relation_type", ""))
            if relation_type in {
                "ALIAS_OF",
                "FAMILY_BINDING_OF",
                "SUCCESSOR_OF",
                "ENCODES_OR_MAPS",
                "DISTINCT_FROM",
                "SUPERSEDES",
            }:
                semantic_relation_counts[relation_type] += 1
        provenance_relation_counts.update(
            str(entry.get("source_relation", ""))
            for entry in record.get("provenance", [])
        )
        for binding in record.get("bindings", []):
            action = binding.get("exact_resolution_action_or_null")
            if action:
                exact_actions[str(action).split(":", 1)[0]] += 1
    owner_records = [
        row for row in records if row.get("definition", {}).get("owner_requirement_crosswalk")
    ]
    rp5c_records = [
        row for row in records if str(row["canonical_component_id"]).startswith("QTT.COMP.RP5C.")
    ]
    rp5c_incomplete_role_records = [
        row
        for row in rp5c_records
        if row.get("uses", {}).get("qku_role_bindings")
        and str(
            row.get("definition", {}).get(
                "complete_mathematical_or_procedural_definition", ""
            )
        ).startswith("MISSING_SEMANTIC_SPECIFICATION:")
    ]
    active_rp5c_qku_contexts: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in rp5c_records:
        if row.get("record_state") not in {
            "CANONICAL_ACCEPTED",
            "PROVISIONAL",
            "UNDER_REVIEW",
        }:
            continue
        for role in row.get("uses", {}).get("qku_role_bindings", []):
            active_rp5c_qku_contexts[
                (
                    str(role.get("qku_id", "")),
                    str(role.get("role_or_decision_stage", "")),
                    str(role.get("market_family", "")),
                )
            ].add(str(row["canonical_component_id"]))
    ambiguous_active_rp5c_context_count = sum(
        len(root_ids) > 1 for root_ids in active_rp5c_qku_contexts.values()
    )
    fixture_ready = [
        row["canonical_component_id"]
        for row in records
        if any(binding.get("derived_state") == "CONTEXT_READY" for binding in row.get("bindings", []))
    ]
    pr162d_fixture_metrics = next(
        (
            dict(batch["ephemeral_fixture_metrics"])
            for batch in batches
            if batch.get("batch_id") == "EXPANSION.PR162D.EXPLICIT_IMPLEMENTATIONS"
        ),
        {},
    )
    synthetic_report = next(
        (
            report
            for report in compiler_reports
            if report.get("batch_id") == "EXPANSION.CONTROL1.SYNTHETIC.PROOF"
        ),
        {},
    )
    advertised_cases = {
        "EXACT_DUPLICATE",
        "NAME_ALIAS",
        "PROVENANCE_ONLY",
        "NEW_BINDING",
        "NEW_PARAMETER_POLICY",
        "COMPATIBLE_FAMILY_MEMBER",
        "SIMILAR_BUT_DISTINCT",
        "TRUE_NEW",
        "QUANTUM_ENCODING_RELATION",
    }
    synthetic_case_outcomes = [
        {
            key: copy.deepcopy(value)
            for key, value in outcome.items()
            if key
            in {
                "case",
                "candidate",
                "decision",
                "canonical_target",
                "new_record_count",
            }
        }
        for outcome in synthetic_report.get("outcomes", [])
        if isinstance(outcome, Mapping) and outcome.get("case") in advertised_cases
    ]
    synthetic_rejections = [
        copy.deepcopy(dict(item))
        for item in synthetic_report.get("pre_compiler_rejections", [])
        if isinstance(item, Mapping)
    ]
    compiler_batch_summaries = []
    for report in compiler_reports:
        decision_counts = Counter(
            str(outcome.get("decision", ""))
            for outcome in report.get("outcomes", [])
            if isinstance(outcome, Mapping)
        )
        transient_delta = report.get("transient_delta", {})
        compiler_batch_summaries.append(
            {
                "batch_id": report.get("batch_id"),
                "items_read": report.get("items_read"),
                "bounded_candidate_bucket_count": report.get(
                    "bounded_candidate_bucket_count"
                ),
                "all_pairs_proof_attempted": report.get(
                    "all_pairs_proof_attempted"
                ),
                "outcome_decision_counts": dict(sorted(decision_counts.items())),
                "delta_counts": {
                    field: len(transient_delta.get(field, []))
                    for field in (
                        "added_component_ids",
                        "changed_component_ids",
                        "retired_component_ids",
                        "added_binding_ids",
                        "changed_binding_ids",
                        "removed_binding_ids",
                        "affected_dependent_ids",
                        "affected_consumer_classes",
                    )
                },
            }
        )
    return {
        "report_type": "PR169_QKU_COMP_CONTROL1_ACCEPTANCE_REPORT",
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "builder": BUILDER_NAME,
        "independent_validator": VALIDATOR_NAME,
        "overall_acceptance_authority": "INDEPENDENT_VALIDATOR_AND_OWNER_AUDIT_REQUIRED",
        "builder_authored_overall_pass": False,
        "source_closure": _source_closure(),
        "source_precedence_conflict_resolutions": [
            {
                "conflict": "RP5C described a permanent identity/write authority",
                "resolution": "RP5C IDs and lineage are immutable baseline provenance inside the one CONTROL1 registry; runtime direct access is absent",
            },
            {
                "conflict": "historical dedupe/family labels resemble semantic proof",
                "resolution": "all RP5C groups remain provisional or dormant and explicitly lack CONTROL1 direct equivalence proof",
            },
            {
                "conflict": "PR162D expected vectors are produced by source implementations",
                "resolution": "fixture invocation is preserved but independent oracle remains REQUIRED except the five exact closed-stack arithmetic nodes",
            },
            {
                "conflict": "reverted implementation claimed all 213 callable",
                "resolution": "only owner card IDs/families/names survive; all 213 are provisional with MISSING_SEMANTIC_SPECIFICATION actions",
            },
            {
                "conflict": "25 quantum rows share nine builder callables",
                "resolution": "nine callable-family records preserve every source formulation role; no encoding is aliased to an original economic model",
            },
        ],
        "expansion_batches": [
            {
                "batch_id": batch["batch_id"],
                "batch_origin": batch["batch_origin"],
                "source_classification": batch["source_classification"],
                "source_refs": batch["source_refs"],
                "item_count": len(batch["items"]),
                "promotion_ceiling": batch["requested_promotion_ceiling"],
            }
            for batch in batches
        ],
        "expansion_compiler": {
            "continuing_intake_path_count": 1,
            "parallel_merge_or_admission_path_count": 0,
            "batch_summaries": compiler_batch_summaries,
        },
        "counts": {
            "logical_registry_rows": len(records),
            "base_registry_rows_loaded": base_record_count,
            "record_state_counts": dict(sorted(state_counts.items())),
            "origin_cohort_counts": dict(sorted(origin_counts.items())),
            "decision_role_counts": dict(sorted(decision_role_counts.items())),
            "qku_role_binding_count": qku_role_count,
            "canonical_requirement_count": requirements_count,
            "exact_action_class_counts": dict(sorted(exact_actions.items())),
        },
        "rp5c_baseline": {
            "canonical_identity_records": len(rp5c_records),
            "expected_canonical_identity_records": EXPECTED_RP5C_IDENTITIES,
            "accepted_runtime_identity_authority_created": False,
            "direct_runtime_rp5c_access_created": False,
            "preserved_qku_role_binding_count": sum(
                len(row.get("uses", {}).get("qku_role_bindings", []))
                for row in rp5c_records
            ),
            "incomplete_qku_role_record_count": len(rp5c_incomplete_role_records),
            "incomplete_qku_role_active_runtime_root_count": sum(
                row.get("record_state")
                in {"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"}
                for row in rp5c_incomplete_role_records
            ),
            "ambiguous_active_qku_context_count": ambiguous_active_rp5c_context_count,
            "selector_or_root_invented_for_incomplete_import_count": sum(
                bool(
                    role.get("stack_root_or_direct_component")
                    or role.get("selection_rule_if_container")
                )
                for row in rp5c_incomplete_role_records
                for role in row.get("uses", {}).get("qku_role_bindings", [])
            ),
            "record_states": dict(
                sorted(Counter(row["record_state"] for row in rp5c_records).items())
            ),
        },
        "implementation_registration": {
            "definition_inventory_counts": dict(sorted(inventory_counts.items())),
            "expected_formula_count": EXPECTED_FORMULA_IMPLEMENTATIONS,
            "expected_algorithm_count": EXPECTED_ALGORITHM_IMPLEMENTATIONS,
            "source_quantum_formulation_count": EXPECTED_QUANTUM_FORMULATIONS,
            "expected_quantum_callable_family_count": EXPECTED_QUANTUM_CALLABLE_FAMILIES,
            "explicit_allowlist_required": True,
            "control_native_implementation_append_count": native_implementation_count,
            "fixture_context_ready_component_ids": sorted(fixture_ready),
            "source_fixture_is_independent_oracle": False,
            "ephemeral_fixture_validation": pr162d_fixture_metrics,
            "persisted_fixture_vector_count": 0,
        },
        "semantic_reuse": {
            "direct_relation_counts": dict(sorted(semantic_relation_counts.items())),
            "source_disposition_kind_count": len(provenance_relation_counts),
            "exact_duplicate_reuse_count": provenance_relation_counts[
                "EXACT_DUPLICATE_REUSED_PROVENANCE_ONLY"
            ],
            "provenance_only_reuse_count": provenance_relation_counts[
                "PROVENANCE_ONLY_REUSE_NO_NEW_RECORD"
            ],
            "synthetic_case_outcomes": synthetic_case_outcomes,
            "synthetic_pre_compiler_rejections": synthetic_rejections,
            "synthetic_case_count": len(synthetic_case_outcomes)
            + len(synthetic_rejections),
            "successor_claim_count": semantic_relation_counts["SUCCESSOR_OF"],
            "qku_role_proposal_rejected_without_synthetic_qku_count": provenance_relation_counts[
                "QKU_ROLE_PROPOSAL_REJECTED_PENDING_EXISTING_QKU_AUTHORITY_AND_DIRECT_ROLE_PROOF"
            ],
        },
        "owner_requirement_213": {
            "inventory_count": len(owner_records),
            "coverage_denominator": EXPECTED_OWNER_REQUIREMENTS,
            "provisional_count": sum(row["record_state"] == "PROVISIONAL" for row in owner_records),
            "inherited_prior_implementation_claim_count": 0,
            "inherited_prior_alias_or_pass_claim_count": 0,
            "exact_action": "MISSING_SEMANTIC_SPECIFICATION_PER_CARD",
        },
        "requirements_compiled_dag": {
            "persistent_dag_written": False,
            "canonical_requirement_count": requirements_count,
            "source_local_selector_count": 0,
            "cycle_count": 0,
            "closed_fixture_roots": [
                "QTT.COMP.FORMULA.PROBABILITY_EDGE",
                "QTT.COMP.FORMULA.RELATIVE_SPREAD",
            ],
            "closed_fixture_upstreams": [
                "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
                "QTT.COMP.FORMULA.MID_PRICE",
                "QTT.COMP.FORMULA.SPREAD",
            ],
        },
        "quantum": {
            "source_formulations": EXPECTED_QUANTUM_FORMULATIONS,
            "callable_family_records": inventory_counts["QUANTUM_CALLABLE_FAMILY"],
            "distinct_original_economic_model_target_count": sum(
                str(row["canonical_component_id"]).startswith("QTT.COMP.ECONOMIC_MODEL.")
                for row in records
            ),
            "encodes_or_maps_relation_count": semantic_relation_counts["ENCODES_OR_MAPS"],
            "maturity_ceiling": "SPECIFIED",
            "local_original_model_parity_claim_count": 0,
            "qpu_backend_call_count": 0,
            "quantum_advantage_claim_count": 0,
            "exact_action": "MISSING_QUANTUM_ORIGINAL_MODEL_LOCAL_PARITY_PER_CALLABLE_FAMILY",
        },
        "pr165_d2_agent_policy": {
            "source_ref": PR165_D2_ROSTER.as_posix(),
            "agent_ids": list(agent_ids),
            "policy_basis": "CLASSIFICATION_BASED_NO_PER_FORMULA_ROUTE",
            "mode_ceiling": "FIXTURE_NONLIVE",
            "order_release_authority_count": 0,
            "source_truth_authority_count": 0,
        },
        "storage": {
            **dict(measurements),
            "active_physical_layout": layout.get("layout"),
            "active_physical_layout_count": 1,
            "shard_count": layout.get("shard_count", 0),
            "registry_files": sorted(layout.get("registry_files", [])),
            "policy_reasons": layout.get("policy_reasons", []),
            "storage_policy": _control_storage_policy(),
            "simultaneous_full_and_sharded_layout_count": 0,
            "qtt_generated_hash_checksum_or_digest_count": 0,
        },
        "transient_registry_update": _delta_summary(delta),
        "scale_probe": dict(scale_probe),
        "measurements": {
            "shape_validation_ms": round(shape_validation_ms, 3),
            "total_build_and_stage_ms": round(total_build_ms, 3),
        },
        "acceptance_diagnostics": {
            "public_control_plane_facade_count_created_by_builder": 0,
            "logical_decision_computation_registry_count": 1,
            "canonical_persistent_record_type_count": 1,
            "persistent_dag_registry_count": 0,
            "persistent_duplicate_equivalence_registry_count": 0,
            "persistent_registry_update_event_log_count": 0,
            "parallel_formula_library_count": 0,
            "runtime_direct_historical_library_access_count": 0,
            "embedded_bulk_evidence_payload_count": 0,
            "persisted_fixture_vector_count": 0,
            "connector_private_state_call_count": 0,
            "order_release_count": 0,
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "shadow_execution_count": 0,
            "live_execution_count": 0,
            "profit_or_quantum_advantage_claim_count": 0,
        },
        "truthful_limitations": [
            "RP5C baseline rows preserve identity and custody but generally lack complete computation semantics.",
            "PR162D source callables commonly use Python float and require typed Decimal/accounting boundaries before financial use.",
            "PR162D source-derived expected vectors are fixture invocation evidence, not independent production oracles.",
            "Only implied-probability/probability-edge and mid/spread/relative-spread fixture subgraphs are closed here.",
            "MAP3 labels, RP5D readiness tiers, R1 synthetic smoke values, and RP5E previews are not computation or equivalence proof.",
            "GFP and PR162B remain current implementation owners requiring direct callable review and proof-backed semantic intake; they are not copied into a parallel formula library.",
            "No replay, PAPER, shadow, dry-run, canary, live, private-state, connector, QPU, cash, fill, PnL, or order evidence is created.",
            "No source record is promoted merely from a count, name, source ID, family label, or fixture result.",
        ],
    }


def _resolve_safe_output_target(repo_root: Path, out_dir: str | Path) -> Path:
    """Confine publication to the owned canonical root or an empty temp target."""

    target = Path(out_dir)
    if not target.is_absolute():
        target = repo_root / target
    target = target.resolve()
    if target == repo_root or any(part.lower() == ".codex_inputs" for part in target.parts):
        raise BuildError(f"unsafe CONTROL1 output directory: {target}")
    canonical = (repo_root / GENERATED_PREFIX).resolve()
    if target == canonical:
        return target
    try:
        target.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise BuildError(
            "non-canonical CONTROL1 output may not create or replace repository paths: "
            f"{target}"
        )
    temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        target.relative_to(temp_root)
    except ValueError as exc:
        raise BuildError(
            "non-canonical CONTROL1 output must be a disposable temporary path: "
            f"{target}"
        ) from exc
    if target == temp_root:
        raise BuildError("refusing to publish over the system temporary root")
    if target.exists():
        if not target.is_dir() or any(target.iterdir()):
            raise BuildError(
                "non-canonical CONTROL1 temporary output must not replace existing content: "
                f"{target}"
            )
    return target


def _publish_directory(staged: Path, target: Path) -> None:
    parent = target.parent.resolve()
    target_resolved = target.resolve()
    if target_resolved == parent:
        raise BuildError("refusing to publish over output parent")
    backup = parent / f".{target.name}.previous"
    if backup.exists():
        raise BuildError(f"stale CONTROL1 publication backup requires review: {backup}")
    if not target.exists():
        os.replace(staged, target)
        return
    os.replace(target, backup)
    try:
        os.replace(staged, target)
    except BaseException:
        os.replace(backup, target)
        raise
    shutil.rmtree(backup)


def build(
    repo_root: str | Path,
    out_dir: str | Path = GENERATED_PREFIX,
    *,
    timeout_ms: int = 3_600_000,
    force_layout: str = "auto",
    scale_probe_records: int = 0,
) -> dict[str, Any]:
    """Build, validate, and atomically publish the CONTROL1 generated surface."""
    started = time.perf_counter()
    root = Path(repo_root).resolve()
    if not root.is_dir():
        raise BuildError(f"repository root does not exist: {root}")
    root_text = str(root)
    if root_text not in sys.path:
        # Direct ``python tools/...`` execution places only ``tools`` on
        # sys.path.  Add the fixed reviewed repository root before loading the
        # single CONTROL1 owner; no caller-selected module path is accepted.
        sys.path.insert(0, root_text)
    target = _resolve_safe_output_target(root, out_dir)
    deadline = _Deadline(timeout_ms)
    lock_path = target.parent / f".{target.name}.writer.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise BuildError(f"concurrent or stale CONTROL1 writer lock: {lock_path}") from exc
    os.close(lock_fd)
    staged: Path | None = None
    try:
        base_records = _load_cumulative_base_records(root, target, deadline)
        records, batches, agent_ids, compiler_reports = _build_registry_and_batches(
            root,
            deadline,
            base_records,
        )
        validation_started = time.perf_counter()
        _validate_registry(records, deadline)
        shape_validation_ms = (time.perf_counter() - validation_started) * 1000.0
        measurements = _measure_registry(records)
        delta = _derive_update(base_records, records)
        if delta.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
            raise BuildError("transient RegistryUpdateV1 schema mismatch")
        scale_probe = _run_scale_probe(scale_probe_records)
        deadline.check("pre-publication staging")
        staged = Path(
            tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent))
        )
        # The layout writer owns creation of its output directory.  The
        # tempfile name itself is untracked and never becomes a generated file.
        staged.rmdir()
        layout = _write_layout(
            records,
            staged,
            force_layout=force_layout,
            measurements=measurements,
            shape_validation_ms=shape_validation_ms,
        )
        layout = {**layout, **_inspect_layout(staged)}
        report = _acceptance_report(
            records,
            batches,
            compiler_reports,
            agent_ids,
            layout,
            measurements,
            delta,
            scale_probe,
            base_record_count=len(base_records),
            shape_validation_ms=shape_validation_ms,
            total_build_ms=(time.perf_counter() - started) * 1000.0,
        )
        _write_json(staged / "acceptance.report.json", report)
        actual_files = sorted(path.name for path in staged.iterdir() if path.is_file())
        expected_files = sorted([*layout["registry_files"], "acceptance.report.json"])
        if actual_files != expected_files:
            raise BuildError(
                f"unexpected CONTROL1 generated surface: {actual_files!r} != {expected_files!r}"
            )
        deadline.check("atomic publication")
        _publish_directory(staged, target)
        staged = None
        return {
            "output_dir": str(target),
            "logical_registry_rows": len(records),
            "active_physical_layout": layout["layout"],
            "shard_count": layout["shard_count"],
            "registry_files": layout["registry_files"],
            "acceptance_report": "acceptance.report.json",
            "transient_registry_update": _delta_summary(delta),
            "independent_validation_required": True,
        }
    finally:
        if staged is not None and staged.exists():
            shutil.rmtree(staged)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", type=int, default=3_600_000)
    parser.add_argument(
        "--force-layout",
        choices=("auto", "single", "sharded"),
        default="auto",
    )
    parser.add_argument("--scale-probe-records", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = build(
        args.repo_root,
        args.out_dir,
        timeout_ms=args.timeout_ms,
        force_layout=args.force_layout,
        scale_probe_records=args.scale_probe_records,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
