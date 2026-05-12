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
from tools import validate_qtt_trade_context_packet as trade_context_gate  # noqa: E402
from tools import (  # noqa: E402
    validate_atomicrows_parameter_selection_universe_registry as universe_registry_gate,
)
from tools import (  # noqa: E402
    validate_atomicrows_parameter_selection_universe_consumer_gate as consumer_gate,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_trade_context_selection_universe_routing_gate.schema.json"
)
DEFAULT_PRODUCTION_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsTradeContextSelectionUniverseRoutingGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_trade_context_selection_universe_routing_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
)

PR80_SCHEMA = consumer_gate.DEFAULT_SCHEMA
PR80_GATE = consumer_gate.DEFAULT_PRODUCTION_GATE
PR80_REPORT = consumer_gate.DEFAULT_REPORT
PR80_VALIDATOR = pathlib.Path("tools") / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
PR79_SCHEMA = consumer_gate.PR79_SCHEMA
PR79_REGISTRY = consumer_gate.PR79_REGISTRY
PR79_REPORT = consumer_gate.PR79_REPORT
PR79_VALIDATOR = consumer_gate.PR79_VALIDATOR
PR78_SCHEMA = consumer_gate.PR78_SCHEMA
PR78_REGISTRY = consumer_gate.PR78_REGISTRY
PR78_REPORT = consumer_gate.PR78_REPORT
PR78_VALIDATOR = consumer_gate.PR78_VALIDATOR
PR77_SCHEMA = consumer_gate.PR77_SCHEMA
PR77_REGISTRY = consumer_gate.PR77_REGISTRY
PR77_REPORT = consumer_gate.PR77_REPORT
PR77_VALIDATOR = consumer_gate.PR77_VALIDATOR
PR73_SCHEMA = consumer_gate.PR73_SCHEMA
PR73_REGISTRY = consumer_gate.PR73_REGISTRY
PR73_REPORT = consumer_gate.PR73_REPORT
PR73_VALIDATOR = consumer_gate.PR73_VALIDATOR
PR74_SCHEMA = consumer_gate.PR74_SCHEMA
PR74_REGISTRY = consumer_gate.PR74_REGISTRY
PR74_REPORT = consumer_gate.PR74_REPORT
PR74_VALIDATOR = consumer_gate.PR74_VALIDATOR
PR75_SCHEMA = consumer_gate.PR75_SCHEMA
PR75_REGISTRY = consumer_gate.PR75_REGISTRY
PR75_REPORT = consumer_gate.PR75_REPORT
PR75_VALIDATOR = consumer_gate.PR75_VALIDATOR

CANONICAL_BUNDLE_JSONL = consumer_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = consumer_gate.CANONICAL_BUNDLE_SHA256
MASTER_PLAN_CURRENT = consumer_gate.MASTER_PLAN_CURRENT
PR76_SHORT_TEST = consumer_gate.PR76_SHORT_TEST
PR76_OLD_LONG_TEST = consumer_gate.PR76_OLD_LONG_TEST

ROUTING_GATE_ID = "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE"
ROUTING_GATE_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-TRADE-CONTEXT-ROUTING-GATE"
AUTHORITY_CLASS = (
    "STATIC_TRADE_CONTEXT_TO_SELECTION_UNIVERSE_ROUTING_GATE_ONLY_NOT_SELECTION_"
    "NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
REPORT_ID = "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_REPORT"
REPORT_VERSION = "v1"
REPORT_AUTHORITY_CLASS = (
    "STATIC_ROUTE_ELIGIBILITY_REPORT_NOT_SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
VALIDATOR_NAME = "validate_trade_context_selection_universe_routing_gate.py"
SUCCESS_MARKER = "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK"
FAILURE_MARKER = "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_FAILED"

PR80_SUCCESS_MARKER = consumer_gate.SUCCESS_MARKER
PR79_SUCCESS_MARKER = consumer_gate.PR79_SUCCESS_MARKER
PR78_SUCCESS_MARKER = consumer_gate.PR78_SUCCESS_MARKER
PR77_SUCCESS_MARKER = consumer_gate.PR77_SUCCESS_MARKER
PR73_SUCCESS_MARKER = consumer_gate.PR73_SUCCESS_MARKER
PR74_SUCCESS_MARKER = consumer_gate.PR74_SUCCESS_MARKER
PR75_SUCCESS_MARKER = consumer_gate.PR75_SUCCESS_MARKER

REQUIRED_SELECTION_UNIVERSE_IDS = consumer_gate.REQUIRED_SELECTION_UNIVERSE_IDS
TRADE_CONTEXT_REQUIRED_FIELDS = trade_context_gate.MINIMUM_REQUIRED_PACKET_FIELDS
ROUTING_MATCH_FIELDS = universe_registry_gate.TRADE_CONTEXT_FILTER_FIELDS
OWNER_OVERRIDE_TOKENS = trade_context_gate.OWNER_OVERRIDE_TOKEN_VALUES
ACTIVE_OWNER_OVERRIDE_TOKENS = tuple(token for token in OWNER_OVERRIDE_TOKENS if token != "NONE")

ROUTE_SCOPE = "STATIC_TRADE_CONTEXT_TO_SELECTION_UNIVERSE_ELIGIBILITY_ONLY"
ROUTING_CONSUMER_CLASS = "TRADE_CONTEXT_ROUTING_GATE_CONSUMER_FUTURE_PR81"
ROUTING_REFERENCE_MODE = "FUTURE_PR81_ROUTING_INPUT_REFERENCE_ONLY"

SCHEMA_REQUIRED_FIELDS = (
    "routing_gate_id",
    "routing_gate_version",
    "authority_class",
    "semantic_task_id",
    "depends_on_selection_universe_consumer_gate",
    "depends_on_selection_universe_registry",
    "depends_on_qtt_trade_context_packet",
    "depends_on_edge_parameter_stack_selection_packet",
    "depends_on_parameter_stack_role_taxonomy",
    "depends_on_parameter_stack_completeness_gate",
    "depends_on_parameter_stack_compatibility_gate",
    "required_selection_universe_ids",
    "required_trade_context_fields",
    "routing_match_dimensions",
    "routing_request_contract",
    "route_output_contract",
    "routing_static_policy",
    "owner_override_policy",
    "source_evidence_boundary_policy",
    "connector_semantic_boundary_policy",
    "runtime_live_order_boundary_policy",
    "quantum_forward_policy",
    "future_consumer_contract",
    "forbidden_output_fields_policy",
    "explicit_no_claim_flags",
    "validation_invariants",
    "production_readiness",
    "final_ready",
)
REQUEST_REQUIRED_FIELDS = (
    "routing_request_id",
    "trade_context",
    "requesting_agent_role",
    "requesting_agent_id",
    "consumer_class",
    "trade_context_reference_mode",
    "requested_universe_ids",
    "owner_override_forced_universe_ids",
    "universe_binding_required",
    "universe_binding_present",
)
ROUTE_OUTPUT_FALSE_FIELDS = (
    "route_is_selection",
    "stack_selection_created",
    "score_breakdown_created",
    "optimizer_arbitration_created",
    "runtime_authority_created",
    "live_authority_created",
    "order_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "profit_evidence_created",
    "random_selection_used",
    "owner_override_external_fact_fabrication_created",
)
ROUTING_STATIC_TRUE_FIELDS = (
    "routing_gate_is_static_only",
    "trade_context_to_selection_universe_static_routing_gate_created",
    "routing_report_created",
    "deterministic_universe_sort_required",
    "consumer_gate_access_required",
)
ROUTING_STATIC_FALSE_FIELDS = (
    "random_routing_allowed",
    "stack_selection_created",
    "selected_stack_authority_created",
    "scoring_created",
    "ranking_created",
    "score_breakdown_created",
    "optimizer_arbitration_created",
    "candidate_stack_generation_created",
    "replay_paper_execution_created",
    "runtime_live_order_authority_created",
    "route_result_authority_created",
    "final_ready_created_by_this_pr",
)
OWNER_TRUE_FIELDS = (
    "owner_override_supported",
    "owner_override_satisfies_internal_routing_eligibility_only",
    "owner_override_may_force_static_route_eligibility_internal_only",
)
OWNER_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_fill",
    "owner_override_fabricates_replay_result",
    "owner_override_fabricates_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_alpha_evidence",
    "owner_override_fabricates_latency_superiority_evidence",
    "owner_override_fabricates_execution_superiority_evidence",
    "owner_override_fabricates_quantum_advantage_evidence",
    "owner_override_fabricates_profit_evidence",
)
SOURCE_TRUE_FIELDS = (
    "routing_source_dependency_values_are_static_labels_only",
    "external_fact_requires_accepted_source_packet",
    "market_data_fact_requires_accepted_source_packet",
    "liquidity_fact_requires_accepted_source_packet",
    "connector_semantic_requires_accepted_source_packet",
)
SOURCE_FALSE_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "source_fact_acceptance_created",
    "owner_policy_may_authorize_external_fact_value",
)
CONNECTOR_TRUE_FIELDS = (
    "routing_gate_does_not_unlock_connector_semantics",
    "connector_unlock_requires_accepted_target_field_packet",
    "connector_unlock_requires_fresh_revalidation_state",
    "connector_unlock_requires_target_field_scope_match",
)
CONNECTOR_FALSE_FIELDS = (
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "connector_semantic_value_created",
)
RUNTIME_TRUE_FIELDS = (
    "routing_gate_is_not_runtime_signal",
    "routing_gate_is_not_live_order_instruction",
)
RUNTIME_FALSE_FIELDS = (
    "runtime_artifacts_created",
    "runtime_resolver_execution_created",
    "private_state_fetch_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "order_authority_created",
    "order_intent_authority_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
    "replay_execution_created",
    "paper_execution_created",
    "profit_evidence_created",
)
QUANTUM_TRUE_FIELDS = (
    "quantum_route_candidate_flag_supported",
    "quantum_forward_metadata_preserved_flag",
    "future_quantum_applicability_registry_required",
    "future_owner_quantum_priority_policy_required",
    "strongest_classical_comparator_required_before_quantum_advantage_claim",
    "fallback_bundle_required_before_quantum_runtime_use",
)
QUANTUM_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_score_created",
    "quantum_ranking_created",
    "quantum_selection_created",
    "optimizer_arbitration_created",
)
FUTURE_TRUE_FIELDS = (
    "quantum_applicability_classification_registry_may_consume",
    "owner_quantum_priority_policy_registry_may_consume",
    "scoring_policy_registry_may_consume",
    "parameter_stack_scoring_ranking_gate_may_consume",
    "quantum_classical_optimizer_arbitration_gate_may_consume",
    "candidate_parameter_stack_generation_gate_may_consume",
    "trade_context_parameter_stack_selection_gate_may_consume",
)
FUTURE_FALSE_FIELDS = (
    "this_pr_performs_stack_selection",
    "this_pr_performs_scoring",
    "this_pr_performs_ranking",
    "this_pr_performs_optimizer_arbitration",
    "this_pr_generates_candidate_stacks",
    "this_pr_executes_replay_or_paper",
    "this_pr_executes_runtime_or_live",
)
EXPLICIT_NO_CLAIM_FALSE_FIELDS = (
    "stack_selection_created",
    "selected_stack_authority_created",
    "scoring_created",
    "ranking_created",
    "score_breakdown_created",
    "optimizer_arbitration_created",
    "candidate_stack_generation_created",
    "selected_stack_handoff_created",
    "runtime_authority_created",
    "runtime_artifacts_created",
    "runtime_resolver_execution_created",
    "live_authority_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "private_state_fetch_created",
    "order_authority_created",
    "order_intent_authority_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_results_created",
    "paper_results_created",
    "profit_evidence_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "source_fact_acceptance_created",
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "connector_semantic_value_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_score_created",
    "quantum_ranking_created",
    "quantum_selection_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "alpha_evidence_created",
    "atomicrows_bundle_rows_created",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "atomicrows_bundle_hash_authority_created",
    "runtime_cash_value_created",
    "external_fact_value_created",
    "market_data_fact_created",
    "liquidity_fact_created",
)
PRODUCTION_READINESS_EXPECTED = {
    "trade_context_selection_universe_routing_gate_ready": True,
    "production_trade_context_routing_evaluated": False,
    "production_routing_ready": False,
    "production_selection_ready": False,
    "final_ready": False,
}

REASON_CODE_ORDER = (
    "ROUTE_ALLOWED_EXPLICIT_MATCH",
    "ROUTE_ALLOWED_OWNER_OVERRIDE_INTERNAL_ONLY",
    "ROUTE_BLOCKED_PLATFORM_MISMATCH",
    "ROUTE_BLOCKED_MARKET_TYPE_MISMATCH",
    "ROUTE_BLOCKED_VENUE_SCOPE_MISMATCH",
    "ROUTE_BLOCKED_STRATEGY_CLASS_MISMATCH",
    "ROUTE_BLOCKED_EDGE_TYPE_MISMATCH",
    "ROUTE_BLOCKED_LATENCY_CLASS_MISMATCH",
    "ROUTE_BLOCKED_CAPITAL_INTENSITY_MISMATCH",
    "ROUTE_BLOCKED_RISK_MODE_MISMATCH",
    "ROUTE_BLOCKED_LIQUIDITY_CONTEXT_MISMATCH",
    "ROUTE_BLOCKED_TIME_HORIZON_MISMATCH",
    "ROUTE_BLOCKED_QUANTUM_PRIORITY_MODE_MISMATCH",
    "ROUTE_BLOCKED_OWNER_OVERRIDE_BASIS_MISMATCH",
    "ROUTE_BLOCKED_CONSUMER_ACCESS_MISSING",
    "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED",
    "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_FIELD",
    "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE",
    "ROUTE_BLOCKED_MISSING_REQUIRED_TRADE_CONTEXT_FIELD",
    "ROUTE_BLOCKED_EMPTY_REQUIRED_TRADE_CONTEXT_FIELD",
    "ROUTE_BLOCKED_UNKNOWN_UNIVERSE",
    "ROUTE_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "ROUTE_BLOCKED_OWNER_OVERRIDE_MISSING_UNIVERSE",
    "ROUTE_BLOCKED_OWNER_OVERRIDE_CONSUMER_RELATIONSHIP_MISSING",
    "ROUTE_BLOCKED_RANDOM_ROUTING_FORBIDDEN",
    "ROUTE_BLOCKED_SELECTION_FORBIDDEN",
    "ROUTE_BLOCKED_SCORE_BREAKDOWN_FORBIDDEN",
    "ROUTE_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
    "ROUTE_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
    "ROUTE_BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_FORBIDDEN",
    "ROUTE_BLOCKED_CONNECTOR_SEMANTIC_BINDING_FORBIDDEN",
    "ROUTE_BLOCKED_QUANTUM_BACKEND_EXECUTION_FORBIDDEN",
    "ROUTE_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
    "ROUTE_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN",
)
ALLOWED_REASON_CODES = set(REASON_CODE_ORDER)
FIELD_MISMATCH_REASON = {
    "platform": "ROUTE_BLOCKED_PLATFORM_MISMATCH",
    "market_type": "ROUTE_BLOCKED_MARKET_TYPE_MISMATCH",
    "venue_scope": "ROUTE_BLOCKED_VENUE_SCOPE_MISMATCH",
    "strategy_class": "ROUTE_BLOCKED_STRATEGY_CLASS_MISMATCH",
    "edge_type": "ROUTE_BLOCKED_EDGE_TYPE_MISMATCH",
    "latency_sensitivity_class": "ROUTE_BLOCKED_LATENCY_CLASS_MISMATCH",
    "capital_intensity_class": "ROUTE_BLOCKED_CAPITAL_INTENSITY_MISMATCH",
    "risk_mode": "ROUTE_BLOCKED_RISK_MODE_MISMATCH",
    "liquidity_context": "ROUTE_BLOCKED_LIQUIDITY_CONTEXT_MISMATCH",
    "time_horizon": "ROUTE_BLOCKED_TIME_HORIZON_MISMATCH",
    "quantum_priority_mode": "ROUTE_BLOCKED_QUANTUM_PRIORITY_MODE_MISMATCH",
    "owner_override_basis": "ROUTE_BLOCKED_OWNER_OVERRIDE_BASIS_MISMATCH",
}
CONSUMER_BLOCK_REASON = {
    "UNKNOWN_UNIVERSE_ID_BLOCKED": "ROUTE_BLOCKED_UNKNOWN_UNIVERSE",
    "UNKNOWN_AGENT_ROLE_BLOCKED": "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED",
    "UNKNOWN_CONSUMER_CLASS_BLOCKED": "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED",
    "MISSING_UNIVERSE_BINDING_BLOCKED": "ROUTE_BLOCKED_CONSUMER_ACCESS_MISSING",
    "DISALLOWED_AGENT_UNIVERSE_PAIR_BLOCKED": "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED",
    "DISALLOWED_CONSUMER_CLASS_BLOCKED": "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED",
    "DISALLOWED_TRADE_CONTEXT_REFERENCE_MODE_BLOCKED": "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED",
}
FORBIDDEN_ROUTE_REPORT_FIELDS = (
    "score_breakdown",
    "ranking",
    "ranking_fields",
    "ranked_universe_ids",
    "optimizer_arbitration",
    "optimizer_arbitration_result",
    "runtime_route",
    "live_route",
    "order_route",
    "source_acceptance",
    "connector_semantic_binding",
    "quantum_backend_result",
    "quantum_advantage",
    "profit_evidence",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "ROUTING_PASS_KALSHI_BINARY_SHORT_HORIZON",
    "ROUTING_PASS_POLYMARKET_EVENT_MARKET_MOMENTUM",
    "ROUTING_PASS_FORECASTEX_IBKR_EVENT_RISK_HEDGE",
    "ROUTING_PASS_QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION_STATIC_ONLY",
    "ROUTING_PASS_OWNER_OVERRIDE_INTERNAL_ONLY",
    "ROUTING_BLOCK_UNKNOWN_PLATFORM",
    "ROUTING_BLOCK_UNKNOWN_MARKET_TYPE",
    "ROUTING_BLOCK_UNKNOWN_VENUE_SCOPE",
    "ROUTING_BLOCK_UNKNOWN_STRATEGY_CLASS",
    "ROUTING_BLOCK_UNKNOWN_EDGE_TYPE",
    "ROUTING_BLOCK_UNKNOWN_LATENCY_SENSITIVITY_CLASS",
    "ROUTING_BLOCK_UNKNOWN_CAPITAL_INTENSITY_CLASS",
    "ROUTING_BLOCK_UNKNOWN_RISK_MODE",
    "ROUTING_BLOCK_UNKNOWN_LIQUIDITY_CONTEXT",
    "ROUTING_BLOCK_UNKNOWN_TIME_HORIZON",
    "ROUTING_BLOCK_UNKNOWN_QUANTUM_PRIORITY_MODE",
    "ROUTING_BLOCK_UNKNOWN_OWNER_OVERRIDE_BASIS",
    "ROUTING_BLOCK_UNKNOWN_TRADE_CONTEXT_FIELD",
    "ROUTING_BLOCK_UNKNOWN_UNIVERSE_ID",
    "ROUTING_BLOCK_MISSING_REQUIRED_UNIVERSE_ID",
    "ROUTING_BLOCK_DUPLICATE_UNIVERSE_ID",
    "ROUTING_BLOCK_MISSING_CONSUMER_ACCESS",
    "ROUTING_BLOCK_CONSUMER_ACCESS_DENIED",
    "ROUTING_BLOCK_RANDOM_ROUTING_ATTEMPT",
    "ROUTING_BLOCK_SELECTED_STACK_ID_AUTHORITY",
    "ROUTING_BLOCK_SCORE_BREAKDOWN",
    "ROUTING_BLOCK_RANKING_FIELDS",
    "ROUTING_BLOCK_OPTIMIZER_ARBITRATION",
    "ROUTING_BLOCK_RUNTIME_LIVE_ORDER_AUTHORITY",
    "ROUTING_BLOCK_SOURCE_RETRIEVAL_OR_ACCEPTANCE",
    "ROUTING_BLOCK_CONNECTOR_SEMANTIC_BINDING",
    "ROUTING_BLOCK_QUANTUM_BACKEND_EXECUTION",
    "ROUTING_BLOCK_QUANTUM_ADVANTAGE_CLAIM",
    "ROUTING_BLOCK_PROFIT_EVIDENCE",
    "ROUTING_BLOCK_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    "ROUTING_BLOCK_OWNER_OVERRIDE_MISSING_UNIVERSE",
    "ROUTING_BLOCK_ATOMICROWS_BUNDLE_JSONL_CREATED",
    "ROUTING_BLOCK_ATOMICROWS_BUNDLE_SHA256_CREATED",
    "ROUTING_DETERMINISM_BYTE_STABLE_REPORT",
    "ROUTING_DETERMINISM_ELIGIBLE_UNIVERSE_ORDER",
    "ROUTING_DETERMINISM_BLOCKED_UNIVERSE_ORDER",
    "ROUTING_DETERMINISM_REASON_CODE_ORDER",
    "ROUTING_DETERMINISM_NO_TIMESTAMP_UUID_RANDOM_ENV_OR_PLATFORM_PATH",
)


@dataclass(frozen=True)
class ValidationResult:
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: JSON file is invalid: {path}: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label}{failure}" for failure in validate_json_schema_subset(payload, schema)]


def _expect_policy_fields(
    payload: dict[str, Any],
    section: str,
    true_fields: Sequence[str],
    false_fields: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get(section))
    for field in true_fields:
        if policy.get(field) is not True:
            failures.append(f"{label}.{section}.{field} must be true")
    for field in false_fields:
        if policy.get(field) is not False:
            failures.append(f"{label}.{section}.{field} must be false")
    return failures


def _flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("explicit_no_claim_flags")).get(field))


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def _universe_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(universe.get("universe_id")): universe
        for universe in _list_of_mappings(registry.get("universe_definitions"))
    }


def _matrix_by_universe(gate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("universe_id")): row
        for row in _list_of_mappings(gate.get("allowed_universe_consumption_matrix"))
    }


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(dict.fromkeys(str(value) for value in values))


def _sort_reason_codes(codes: Iterable[str]) -> list[str]:
    order = {code: index for index, code in enumerate(REASON_CODE_ORDER)}
    return sorted(dict.fromkeys(codes), key=lambda code: (order.get(code, 999), code))


def _owner_override_token(trade_context: dict[str, Any]) -> str:
    return str(_mapping(trade_context.get("owner_override_basis")).get("owner_override_token", ""))


def _owner_override_active(trade_context: dict[str, Any]) -> bool:
    return _owner_override_token(trade_context) in ACTIVE_OWNER_OVERRIDE_TOKENS


def _owner_override_external_fact_attempt(payload: dict[str, Any]) -> bool:
    basis = _mapping(payload.get("owner_override_basis"))
    return any(basis.get(field) is not False for field in trade_context_gate.OWNER_OVERRIDE_BASIS_FALSE_FIELDS)


def _routing_access_request(
    request: dict[str, Any],
    universe_id: str,
    trade_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "universe_id": universe_id,
        "requesting_agent_role": request.get("requesting_agent_role"),
        "requesting_agent_id": request.get("requesting_agent_id"),
        "consumer_class": request.get("consumer_class"),
        "trade_context_reference_mode": request.get("trade_context_reference_mode"),
        "universe_binding_required": request.get("universe_binding_required"),
        "universe_binding_present": request.get("universe_binding_present"),
        "owner_override_token": _owner_override_token(trade_context),
    }


def _consumer_relationship_known(
    consumer_access_gate: dict[str, Any],
    request: dict[str, Any],
    universe_id: str,
) -> bool:
    row = _matrix_by_universe(consumer_access_gate).get(universe_id)
    if not row:
        return False
    if row.get("owner_override_supported") is not True:
        return False
    if request.get("requesting_agent_role") not in consumer_gate._agent_roles_from_charter_schema(repo_root()):
        return False
    if request.get("consumer_class") not in consumer_access_gate.get("authorized_consumer_classes", []):
        return False
    if request.get("trade_context_reference_mode") not in row.get("allowed_trade_context_reference_modes", []):
        return False
    return True


def _field_value_for_match(trade_context: dict[str, Any], field: str) -> str:
    if field == "owner_override_basis":
        return _owner_override_token(trade_context)
    return str(trade_context.get(field, ""))


def _route_reason_from_access(access_reason: str) -> str:
    return CONSUMER_BLOCK_REASON.get(access_reason, "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED")


def _canonical_universe_ids_from_registry(registry: dict[str, Any]) -> list[str]:
    return sorted(str(universe.get("universe_id")) for universe in _list_of_mappings(registry.get("universe_definitions")))


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list):
        return ["PR81 schema root required must be a list"]
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR81 schema missing required root field {field}")
    if schema.get("additionalProperties") is not False:
        failures.append("PR81 schema must be strict with additionalProperties false")
    properties = _mapping(schema.get("properties"))
    if _mapping(properties.get("routing_gate_id")).get("const") != ROUTING_GATE_ID:
        failures.append("PR81 schema routing_gate_id const mismatch")
    if _mapping(properties.get("routing_gate_version")).get("const") != ROUTING_GATE_VERSION:
        failures.append("PR81 schema routing_gate_version const mismatch")
    if _mapping(properties.get("semantic_task_id")).get("const") != SEMANTIC_TASK_ID:
        failures.append("PR81 schema semantic_task_id const mismatch")
    if _mapping(properties.get("authority_class")).get("const") != AUTHORITY_CLASS:
        failures.append("PR81 schema authority_class const mismatch")
    if _mapping(properties.get("required_selection_universe_ids")).get("const") != list(
        REQUIRED_SELECTION_UNIVERSE_IDS
    ):
        failures.append("PR81 schema required_selection_universe_ids const mismatch")
    if _mapping(properties.get("required_trade_context_fields")).get("const") != list(
        TRADE_CONTEXT_REQUIRED_FIELDS
    ):
        failures.append("PR81 schema required_trade_context_fields const mismatch")
    if _mapping(properties.get("routing_match_dimensions")).get("const") != [
        *ROUTING_MATCH_FIELDS,
        "consumer_class",
        "requesting_agent_role",
    ]:
        failures.append("PR81 schema routing_match_dimensions const mismatch")
    return failures


def validate_dependencies(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    failures: list[str] = []
    failures.extend(consumer_gate.validate_pr73_dependency(root))
    failures.extend(consumer_gate.validate_pr74_dependency(root))
    failures.extend(consumer_gate.validate_pr75_dependency(root))
    _edge_schema, _edge_packet, pr77_failures = consumer_gate.validate_pr77_dependency(root)
    failures.extend(pr77_failures)
    trade_schema, trade_packet, pr78_failures = consumer_gate.validate_pr78_dependency(root)
    failures.extend(pr78_failures)
    _pr79_schema, registry, _pr79_report, pr79_failures = consumer_gate.validate_pr79_dependency(root)
    failures.extend(pr79_failures)

    for label, rel_path in (
        ("PR80_CONSUMER_GATE_SCHEMA", PR80_SCHEMA),
        ("PR80_CONSUMER_GATE", PR80_GATE),
        ("PR80_CONSUMER_GATE_REPORT", PR80_REPORT),
        ("PR80_CONSUMER_GATE_VALIDATOR", PR80_VALIDATOR),
    ):
        if not (root / rel_path).exists():
            failures.append(f"PR80_CONSUMER_GATE_DEPENDENCY_BLOCK: {label} missing")
    consumer_access_gate: dict[str, Any] = {}
    if not failures or (root / PR80_GATE).exists():
        try:
            consumer_access_gate = consumer_gate.load_yaml(root / PR80_GATE)
        except (OSError, RegistryParseError) as exc:
            failures.append(f"PR80_CONSUMER_GATE_DEPENDENCY_BLOCK: gate malformed: {exc}")
    if (root / PR80_REPORT).exists():
        try:
            report = load_json(root / PR80_REPORT)
            if report.get("validation_marker") != PR80_SUCCESS_MARKER:
                failures.append("PR80_CONSUMER_GATE_DEPENDENCY_BLOCK: report marker mismatch")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"PR80_CONSUMER_GATE_DEPENDENCY_BLOCK: report malformed: {exc}")

    pr80_result = consumer_gate.validate(
        repo_root=root,
        schema_path=PR80_SCHEMA,
        production_gate_path=PR80_GATE,
        fixture_path=consumer_gate.DEFAULT_FIXTURE,
        output_path=None,
    )
    if not pr80_result.ok:
        failures.append(
            "PR80_CONSUMER_GATE_DEPENDENCY_BLOCK: "
            + "; ".join(pr80_result.failures)
        )

    failures.extend(consumer_gate.validate_repair_pr76_dependency(root))
    return trade_schema, trade_packet, registry, consumer_access_gate, failures


def validate_required_universes(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures: list[str] = []
    failures.extend(universe_registry_gate.validate_required_universes(registry, label))
    failures.extend(universe_registry_gate.validate_universe_uniqueness(registry, label))
    ids = _canonical_universe_ids_from_registry(registry)
    unknown = sorted(set(ids) - set(REQUIRED_SELECTION_UNIVERSE_IDS))
    if unknown:
        failures.append(f"{label}: unknown universe IDs present {unknown}")
    return failures


def _enum_allowed_values() -> dict[str, tuple[str, ...]]:
    return {
        "platform": trade_context_gate.PLATFORM_VALUES,
        "market_type": trade_context_gate.MARKET_TYPE_VALUES,
        "venue_scope": trade_context_gate.VENUE_SCOPE_VALUES,
        "strategy_class": trade_context_gate.STRATEGY_CLASS_VALUES,
        "edge_type": trade_context_gate.EDGE_TYPE_VALUES,
        "order_intent_type": trade_context_gate.ORDER_INTENT_TYPE_VALUES,
        "latency_sensitivity_class": trade_context_gate.LATENCY_SENSITIVITY_CLASS_VALUES,
        "capital_intensity_class": trade_context_gate.CAPITAL_INTENSITY_CLASS_VALUES,
        "risk_mode": trade_context_gate.RISK_MODE_VALUES,
        "liquidity_context": trade_context_gate.LIQUIDITY_CONTEXT_VALUES,
        "time_horizon": trade_context_gate.TIME_HORIZON_VALUES,
        "quantum_priority_mode": trade_context_gate.QUANTUM_PRIORITY_MODE_VALUES,
    }


def validate_trade_context_fields(trade_context: dict[str, Any], label: str = "trade_context") -> list[str]:
    failures: list[str] = []
    unknown_fields = sorted(set(trade_context) - set(TRADE_CONTEXT_REQUIRED_FIELDS))
    if unknown_fields:
        failures.append(
            f"{label}: ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_FIELD unexpected fields {unknown_fields}"
        )
    for field in TRADE_CONTEXT_REQUIRED_FIELDS:
        if field not in trade_context:
            failures.append(f"{label}: ROUTE_BLOCKED_MISSING_REQUIRED_TRADE_CONTEXT_FIELD {field}")
            continue
        value = trade_context.get(field)
        if value in ("", None, [], {}):
            failures.append(f"{label}: ROUTE_BLOCKED_EMPTY_REQUIRED_TRADE_CONTEXT_FIELD {field}")

    enums = _enum_allowed_values()
    for field, allowed in enums.items():
        value = trade_context.get(field)
        if field in trade_context and value not in allowed:
            failures.append(f"{label}: ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE {field}={value!r}")

    basis = _mapping(trade_context.get("owner_override_basis"))
    basis_required = (
        "owner_override_present",
        "owner_override_token",
        "owner_override_scope",
        "owner_override_satisfaction_basis",
        "owner_override_internal_workflow_only",
    )
    for field in basis_required:
        if field not in basis:
            failures.append(f"{label}.owner_override_basis missing {field}")
    if basis.get("owner_override_token") not in OWNER_OVERRIDE_TOKENS:
        failures.append(
            f"{label}: ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE owner_override_token={basis.get('owner_override_token')!r}"
        )
    if basis.get("owner_override_scope") not in trade_context_gate.OWNER_OVERRIDE_SCOPE_VALUES:
        failures.append(
            f"{label}: ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE owner_override_scope={basis.get('owner_override_scope')!r}"
        )
    if basis.get("owner_override_internal_workflow_only") is not True:
        failures.append(f"{label}.owner_override_basis must be internal workflow only")
    for field in trade_context_gate.OWNER_OVERRIDE_BASIS_FALSE_FIELDS:
        if basis.get(field) is not False:
            failures.append(f"{label}: ROUTE_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT {field}")
    return failures


def validate_routing_request(request: dict[str, Any], label: str = "routing_request") -> list[str]:
    failures: list[str] = []
    for field in REQUEST_REQUIRED_FIELDS:
        if field not in request:
            failures.append(f"{label} missing required field {field}")
    trade_context = _mapping(request.get("trade_context"))
    failures.extend(validate_trade_context_fields(trade_context, f"{label}.trade_context"))

    requested = request.get("requested_universe_ids")
    if not isinstance(requested, list) or not requested:
        failures.append(f"{label}.requested_universe_ids must be a nonempty deterministic list")
    elif requested != sorted(requested):
        failures.append(f"{label}.requested_universe_ids must be sorted by universe_id ascending")
    elif len(requested) != len(dict.fromkeys(requested)):
        failures.append(f"{label}.requested_universe_ids contains duplicate universe_id")
    else:
        for universe_id in requested:
            if universe_id not in REQUIRED_SELECTION_UNIVERSE_IDS:
                failures.append(f"{label}: ROUTE_BLOCKED_UNKNOWN_UNIVERSE {universe_id}")

    forced = request.get("owner_override_forced_universe_ids")
    if not isinstance(forced, list):
        failures.append(f"{label}.owner_override_forced_universe_ids must be a deterministic list")
    elif forced != sorted(forced):
        failures.append(f"{label}.owner_override_forced_universe_ids must be sorted")
    elif len(forced) != len(dict.fromkeys(forced)):
        failures.append(f"{label}.owner_override_forced_universe_ids contains duplicate universe_id")
    elif forced and not _owner_override_active(trade_context):
        failures.append(f"{label}.owner_override_forced_universe_ids requires active owner override")
    else:
        for universe_id in forced:
            if universe_id not in REQUIRED_SELECTION_UNIVERSE_IDS:
                failures.append(f"{label}: ROUTE_BLOCKED_OWNER_OVERRIDE_MISSING_UNIVERSE {universe_id}")

    if request.get("requesting_agent_role") not in consumer_gate.AGENT_ROLE_NAMES:
        failures.append(f"{label}.requesting_agent_role unknown")
    if request.get("consumer_class") not in consumer_gate.AUTHORIZED_CONSUMER_CLASSES:
        failures.append(f"{label}.consumer_class unknown")
    if request.get("trade_context_reference_mode") != ROUTING_REFERENCE_MODE:
        failures.append(f"{label}.trade_context_reference_mode must be {ROUTING_REFERENCE_MODE}")
    if request.get("universe_binding_required") is not True:
        failures.append(f"{label}.universe_binding_required must be true")
    if not isinstance(request.get("universe_binding_present"), bool):
        failures.append(f"{label}.universe_binding_present must be boolean")
    return failures


def evaluate_routes(
    *,
    gate: dict[str, Any],
    registry: dict[str, Any],
    consumer_access_gate: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    trade_context = _mapping(request.get("trade_context"))
    requested_ids = [str(item) for item in request.get("requested_universe_ids", [])]
    universe_by_id = _universe_by_id(registry)
    forced_ids = set(str(item) for item in request.get("owner_override_forced_universe_ids", []))
    owner_override_active = _owner_override_active(trade_context)
    owner_policy = _mapping(gate.get("owner_override_policy"))
    owner_external_attempt = _owner_override_external_fact_attempt(trade_context) or any(
        owner_policy.get(field) is not False for field in OWNER_FALSE_FIELDS
    )
    candidates: list[dict[str, Any]] = []

    for universe_id in sorted(requested_ids):
        reasons: list[str] = []
        universe = universe_by_id.get(universe_id)
        if universe is None:
            reasons.append("ROUTE_BLOCKED_UNKNOWN_UNIVERSE")
            explicit_field_match = False
            access = {
                "normal_access_allowed": False,
                "owner_override_access_allowed": False,
                "final_internal_access_allowed": False,
                "block_reason_codes": ["UNKNOWN_UNIVERSE_ID_BLOCKED"],
            }
        else:
            filters = _mapping(universe.get("static_membership_filters"))
            for field in ROUTING_MATCH_FIELDS:
                allowed_values = filters.get(field)
                value = _field_value_for_match(trade_context, field)
                if not isinstance(allowed_values, list) or value not in allowed_values:
                    reasons.append(FIELD_MISMATCH_REASON[field])
            explicit_field_match = not reasons
            access_request = _routing_access_request(request, universe_id, trade_context)
            access = consumer_gate.evaluate_consumer_access(consumer_access_gate, access_request)
            if access["normal_access_allowed"] is not True:
                if universe_id not in _matrix_by_universe(consumer_access_gate):
                    reasons.append("ROUTE_BLOCKED_CONSUMER_ACCESS_MISSING")
                else:
                    for access_reason in access["block_reason_codes"]:
                        reasons.append(_route_reason_from_access(str(access_reason)))

        owner_override_eligible = False
        if owner_override_active and universe_id in forced_ids:
            if universe is None:
                reasons.append("ROUTE_BLOCKED_OWNER_OVERRIDE_MISSING_UNIVERSE")
            elif owner_external_attempt:
                reasons.append("ROUTE_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT")
            elif _consumer_relationship_known(consumer_access_gate, request, universe_id):
                owner_override_eligible = True
                reasons.append("ROUTE_ALLOWED_OWNER_OVERRIDE_INTERNAL_ONLY")
            else:
                reasons.append("ROUTE_BLOCKED_OWNER_OVERRIDE_CONSUMER_RELATIONSHIP_MISSING")

        explicit_eligible = (
            universe is not None
            and explicit_field_match
            and access["normal_access_allowed"] is True
        )
        if explicit_eligible:
            reasons.append("ROUTE_ALLOWED_EXPLICIT_MATCH")

        final_eligible = explicit_eligible or owner_override_eligible
        candidate = {
            "universe_id": universe_id,
            "explicit_field_match": explicit_eligible,
            "consumer_access_normal_allowed": access["normal_access_allowed"] is True,
            "route_eligible": final_eligible,
            "route_eligible_by_owner_override": owner_override_eligible,
            "reason_codes": _sort_reason_codes(reasons),
        }
        candidates.append(candidate)
    return {
        "route_candidates": candidates,
        "eligible_universe_ids": [
            item["universe_id"]
            for item in candidates
            if item["explicit_field_match"] and item["consumer_access_normal_allowed"]
        ],
        "owner_override_eligible_universe_ids": [
            item["universe_id"] for item in candidates if item["route_eligible_by_owner_override"]
        ],
        "final_route_eligible_universe_ids": [
            item["universe_id"] for item in candidates if item["route_eligible"]
        ],
        "blocked_universes": [
            {
                "universe_id": item["universe_id"],
                "blocked_reason_codes": [
                    code
                    for code in item["reason_codes"]
                    if not code.startswith("ROUTE_ALLOWED_")
                ],
            }
            for item in candidates
            if not item["route_eligible"]
        ],
        "owner_override_applied": any(item["route_eligible_by_owner_override"] for item in candidates),
    }


def build_report(
    *,
    root: pathlib.Path,
    gate: dict[str, Any],
    registry: dict[str, Any],
    consumer_access_gate: dict[str, Any],
    schema_path: pathlib.Path,
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    request = _mapping(gate.get("routing_request_contract"))
    trade_context = _mapping(request.get("trade_context"))
    route_eval = evaluate_routes(
        gate=gate,
        registry=registry,
        consumer_access_gate=consumer_access_gate,
        request=request,
    )
    output_contract = _mapping(gate.get("route_output_contract"))
    report = {
        "accepted_source_packets_created": False,
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "blocked_universes": route_eval["blocked_universes"],
        "candidate_stack_generation_created": False,
        "connector_semantic_binding_created": False,
        "consumer_class": request.get("consumer_class"),
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "depends_on_pr77_edge_packet_schema": True,
        "depends_on_pr78_trade_context_packet_schema": True,
        "depends_on_pr79_selection_universe_registry": True,
        "depends_on_pr80_selection_universe_consumer_gate": True,
        "eligible_universe_ids": route_eval["eligible_universe_ids"],
        "final_route_eligible_universe_ids": route_eval["final_route_eligible_universe_ids"],
        "fixture_path": _as_posix(fixture_path),
        "live_authority_created": False,
        "order_authority_created": False,
        "optimizer_arbitration_created": False,
        "owner_override_applied": route_eval["owner_override_applied"],
        "owner_override_basis": _owner_override_token(trade_context),
        "owner_override_eligible_universe_ids": route_eval["owner_override_eligible_universe_ids"],
        "owner_override_external_fact_fabrication_created": False,
        "profit_evidence_created": False,
        "production_gate_path": _as_posix(production_gate_path),
        "quantum_advantage_claim_created": False,
        "quantum_backend_execution_created": False,
        "quantum_forward_metadata": {
            "future_owner_quantum_priority_policy_required": True,
            "future_quantum_applicability_registry_required": True,
            "optimizer_arbitration_created": False,
            "quantum_advantage_claim_created": False,
            "quantum_backend_execution_created": False,
            "quantum_forward_metadata_preserved_flag": True,
            "quantum_priority_mode": trade_context.get("quantum_priority_mode"),
            "quantum_route_candidate_flag": "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION"
            in request.get("requested_universe_ids", []),
        },
        "random_selection_used": False,
        "report_version": REPORT_VERSION,
        "requested_universe_ids": request.get("requested_universe_ids", []),
        "requesting_agent_role": request.get("requesting_agent_role"),
        "route_candidates": route_eval["route_candidates"],
        "route_is_selection": False,
        "route_scope": ROUTE_SCOPE,
        "routing_gate_id": ROUTING_GATE_ID,
        "routing_report_id": REPORT_ID,
        "routing_request_id": request.get("routing_request_id"),
        "runtime_authority_created": False,
        "schema_path": _as_posix(schema_path),
        "score_breakdown_created": False,
        "selected_stack_id": None,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "source_acceptance_created": False,
        "source_retrieval_created": False,
        "stack_selection_created": False,
        "trade_context_id": trade_context.get("trade_context_id"),
        "validation_marker": SUCCESS_MARKER,
        "validator": VALIDATOR_NAME,
    }
    for field in ROUTE_OUTPUT_FALSE_FIELDS:
        if field in output_contract:
            report[field] = False
    return report


def validate_report(report: dict[str, Any], label: str = "report") -> list[str]:
    failures: list[str] = []
    expected_values: dict[str, Any] = {
        "routing_report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_NAME,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "route_scope": ROUTE_SCOPE,
        "route_is_selection": False,
        "stack_selection_created": False,
        "selected_stack_id": None,
        "score_breakdown_created": False,
        "optimizer_arbitration_created": False,
        "runtime_authority_created": False,
        "live_authority_created": False,
        "order_authority_created": False,
        "source_retrieval_created": False,
        "source_acceptance_created": False,
        "connector_semantic_binding_created": False,
        "quantum_backend_execution_created": False,
        "quantum_advantage_claim_created": False,
        "profit_evidence_created": False,
        "random_selection_used": False,
        "owner_override_external_fact_fabrication_created": False,
        "depends_on_pr80_selection_universe_consumer_gate": True,
        "depends_on_pr79_selection_universe_registry": True,
        "depends_on_pr78_trade_context_packet_schema": True,
        "depends_on_pr77_edge_packet_schema": True,
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "validation_marker": SUCCESS_MARKER,
    }
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected!r}")
    for field in FORBIDDEN_ROUTE_REPORT_FIELDS:
        if field in report:
            failures.append(f"{label}: forbidden route output field present {field}")
    if report.get("eligible_universe_ids") != sorted(report.get("eligible_universe_ids", [])):
        failures.append(f"{label}.eligible_universe_ids must be sorted by universe_id")
    if report.get("owner_override_eligible_universe_ids") != sorted(
        report.get("owner_override_eligible_universe_ids", [])
    ):
        failures.append(f"{label}.owner_override_eligible_universe_ids must be sorted")
    if report.get("final_route_eligible_universe_ids") != sorted(
        report.get("final_route_eligible_universe_ids", [])
    ):
        failures.append(f"{label}.final_route_eligible_universe_ids must be sorted")

    blocked = _list_of_mappings(report.get("blocked_universes"))
    blocked_ids = [str(item.get("universe_id")) for item in blocked]
    if blocked_ids != sorted(blocked_ids):
        failures.append(f"{label}.blocked_universes must be sorted by universe_id")
    for item in blocked:
        uid = str(item.get("universe_id"))
        if uid not in REQUIRED_SELECTION_UNIVERSE_IDS:
            failures.append(f"{label}.blocked_universes unknown universe_id {uid}")
        codes = item.get("blocked_reason_codes")
        if not isinstance(codes, list) or not codes:
            failures.append(f"{label}.{uid}.blocked_reason_codes must be nonempty")
            continue
        if codes != _sort_reason_codes(codes):
            failures.append(f"{label}.{uid}.blocked_reason_codes must be deterministic")
        unknown_codes = sorted(set(str(code) for code in codes) - ALLOWED_REASON_CODES)
        if unknown_codes:
            failures.append(f"{label}.{uid}.blocked_reason_codes unknown {unknown_codes}")

    candidates = _list_of_mappings(report.get("route_candidates"))
    candidate_ids = [str(item.get("universe_id")) for item in candidates]
    if candidate_ids != sorted(candidate_ids):
        failures.append(f"{label}.route_candidates must be sorted by universe_id")
    for item in candidates:
        codes = item.get("reason_codes")
        if not isinstance(codes, list) or not codes:
            failures.append(f"{label}.{item.get('universe_id')}.reason_codes must be nonempty")
            continue
        if codes != _sort_reason_codes(codes):
            failures.append(f"{label}.{item.get('universe_id')}.reason_codes must be deterministic")
        unknown_codes = sorted(set(str(code) for code in codes) - ALLOWED_REASON_CODES)
        if unknown_codes:
            failures.append(f"{label}.{item.get('universe_id')}.reason_codes unknown {unknown_codes}")
    quantum = _mapping(report.get("quantum_forward_metadata"))
    for field in (
        "quantum_forward_metadata_preserved_flag",
        "future_quantum_applicability_registry_required",
        "future_owner_quantum_priority_policy_required",
    ):
        if quantum.get(field) is not True:
            failures.append(f"{label}.quantum_forward_metadata.{field} must be true")
    for field in (
        "quantum_backend_execution_created",
        "quantum_advantage_claim_created",
        "optimizer_arbitration_created",
    ):
        if quantum.get(field) is not False:
            failures.append(f"{label}.quantum_forward_metadata.{field} must be false")
    failures.extend(validate_report_deterministic_content(report, label))
    return failures


def validate_report_deterministic_content(report: dict[str, Any], label: str = "report") -> list[str]:
    failures: list[str] = []
    text = serialize_report(report)
    if report != json.loads(text):
        failures.append(f"{label} output is not deterministic sorted JSON")
    if re.search(r"[A-Za-z]:\\", text):
        failures.append(f"{label} contains platform-specific absolute path")
    if re.search(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        text,
    ):
        failures.append(f"{label} contains UUID-shaped nondeterministic value")
    if re.search(r"\b20\d{2}-\d{2}-\d{2}[T ][0-2]\d:[0-5]\d", text):
        failures.append(f"{label} contains timestamp-shaped nondeterministic value")
    if re.search(r"\b(?:HOME|USERPROFILE|APPDATA|TMP|TEMP)=", text):
        failures.append(f"{label} contains environment-shaped value")
    return failures


def validate_route_output_contract(gate: dict[str, Any], label: str = "gate") -> list[str]:
    failures: list[str] = []
    contract = _mapping(gate.get("route_output_contract"))
    if contract.get("routing_report_id") != REPORT_ID:
        failures.append(f"{label}.route_output_contract.routing_report_id mismatch")
    if contract.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append(f"{label}.route_output_contract.semantic_task_id mismatch")
    if contract.get("route_scope") != ROUTE_SCOPE:
        failures.append(f"{label}.route_output_contract.route_scope mismatch")
    for field in ROUTE_OUTPUT_FALSE_FIELDS:
        if contract.get(field) is not False:
            failures.append(f"{label}.route_output_contract.{field} must be false")
    if contract.get("selected_stack_id") is not None:
        failures.append(f"{label}.route_output_contract.selected_stack_id must be null")
    reason_codes = contract.get("allowed_reason_codes")
    if reason_codes != list(REASON_CODE_ORDER):
        failures.append(f"{label}.route_output_contract.allowed_reason_codes must match canonical order")
    return failures


def validate_policy_sections(gate: dict[str, Any], label: str = "gate") -> list[str]:
    failures: list[str] = []
    failures.extend(
        _expect_policy_fields(
            gate,
            "routing_static_policy",
            ROUTING_STATIC_TRUE_FIELDS,
            ROUTING_STATIC_FALSE_FIELDS,
            label,
        )
    )
    failures.extend(
        _expect_policy_fields(gate, "owner_override_policy", OWNER_TRUE_FIELDS, OWNER_FALSE_FIELDS, label)
    )
    failures.extend(
        _expect_policy_fields(
            gate,
            "source_evidence_boundary_policy",
            SOURCE_TRUE_FIELDS,
            SOURCE_FALSE_FIELDS,
            label,
        )
    )
    failures.extend(
        _expect_policy_fields(
            gate,
            "connector_semantic_boundary_policy",
            CONNECTOR_TRUE_FIELDS,
            CONNECTOR_FALSE_FIELDS,
            label,
        )
    )
    failures.extend(
        _expect_policy_fields(
            gate,
            "runtime_live_order_boundary_policy",
            RUNTIME_TRUE_FIELDS,
            RUNTIME_FALSE_FIELDS,
            label,
        )
    )
    failures.extend(
        _expect_policy_fields(
            gate,
            "quantum_forward_policy",
            QUANTUM_TRUE_FIELDS,
            QUANTUM_FALSE_FIELDS,
            label,
        )
    )
    failures.extend(
        _expect_policy_fields(
            gate,
            "future_consumer_contract",
            FUTURE_TRUE_FIELDS,
            FUTURE_FALSE_FIELDS,
            label,
        )
    )
    for field in EXPLICIT_NO_CLAIM_FALSE_FIELDS:
        if _flag(gate, field) is not False:
            failures.append(f"{label}.explicit_no_claim_flags.{field} must be false")
    return failures


def validate_forbidden_output_fields(payload: dict[str, Any], label: str = "payload") -> list[str]:
    failures: list[str] = []
    for field in FORBIDDEN_ROUTE_REPORT_FIELDS:
        if field in payload:
            failures.append(f"{label}: forbidden output field present {field}")
    selected = payload.get("selected_stack_id")
    if selected is not None:
        failures.append(f"{label}: selected_stack_id must remain null or absent")
    return failures


def validate_no_forbidden_claims(artifact_texts: Iterable[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    forbidden_true_snippets = (
        "route_is_selection: true",
        '"route_is_selection": true',
        "stack_selection_created: true",
        '"stack_selection_created": true',
        "score_breakdown_created: true",
        '"score_breakdown_created": true',
        "optimizer_arbitration_created: true",
        '"optimizer_arbitration_created": true',
        "runtime_authority_created: true",
        '"runtime_authority_created": true',
        "live_authority_created: true",
        '"live_authority_created": true',
        "order_authority_created: true",
        '"order_authority_created": true',
        "source_retrieval_created: true",
        '"source_retrieval_created": true',
        "source_acceptance_created: true",
        '"source_acceptance_created": true',
        "connector_semantic_binding_created: true",
        '"connector_semantic_binding_created": true',
        "quantum_backend_execution_created: true",
        '"quantum_backend_execution_created": true',
        "quantum_advantage_claim_created: true",
        '"quantum_advantage_claim_created": true',
        "profit_evidence_created: true",
        '"profit_evidence_created": true',
        "random_selection_used: true",
        '"random_selection_used": true',
    )
    for label, text in artifact_texts:
        lowered = text.lower()
        if "expected_profit" in lowered or "profit_claim" in lowered:
            failures.append(f"{label}: forbidden profit claim wording")
        for snippet in forbidden_true_snippets:
            if snippet in text:
                failures.append(f"{label}: forbidden true boundary {snippet}")
    return failures


def validate_no_forbidden_artifacts(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if (root / CANONICAL_BUNDLE_JSONL).exists():
        failures.append("ATOMICROWS_BUNDLE_FORBIDDEN_ARTIFACT_BLOCK")
    if (root / CANONICAL_BUNDLE_SHA256).exists():
        failures.append("ATOMICROWS_BUNDLE_SHA_FORBIDDEN_ARTIFACT_BLOCK")
    return failures


def validate_master_plan_not_modified(root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "--", str(MASTER_PLAN_CURRENT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode == 0:
        return []
    if completed.returncode == 1:
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR81"]
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {completed.stderr.strip()}"]


def validate_validator_source_static(root: pathlib.Path) -> list[str]:
    text = (root / pathlib.Path("tools") / VALIDATOR_NAME).read_text(encoding="utf-8")
    patterns = {
        "random import": r"^\s*(?:import\s+random\b|from\s+random\s+import\b)",
        "random call": r"\brandom\.",
        "uuid import": r"^\s*(?:import\s+uuid\b|from\s+uuid\s+import\b)",
        "uuid call": r"\buuid\.",
        "datetime.now": r"\bdatetime\.now\s*\(",
        "time.time": r"\btime\.time\s*\(",
        "environment read": r"\bos\.environ\b",
    }
    return [
        f"PR81 validator uses forbidden nondeterministic surface {label}"
        for label, pattern in patterns.items()
        if re.search(pattern, text, flags=re.MULTILINE)
    ]


def validate_gate_document(
    *,
    gate: dict[str, Any],
    schema: dict[str, Any],
    registry: dict[str, Any],
    consumer_access_gate: dict[str, Any],
    root: pathlib.Path,
    label: str,
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(gate, schema, label))
    failures.extend(validate_required_universes(registry, "PR79 registry"))
    if gate.get("required_selection_universe_ids") != list(REQUIRED_SELECTION_UNIVERSE_IDS):
        failures.append(f"{label}.required_selection_universe_ids mismatch")
    if gate.get("required_trade_context_fields") != list(TRADE_CONTEXT_REQUIRED_FIELDS):
        failures.append(f"{label}.required_trade_context_fields mismatch")
    expected_dimensions = [*ROUTING_MATCH_FIELDS, "consumer_class", "requesting_agent_role"]
    if gate.get("routing_match_dimensions") != expected_dimensions:
        failures.append(f"{label}.routing_match_dimensions mismatch")
    failures.extend(validate_routing_request(_mapping(gate.get("routing_request_contract")), f"{label}.routing_request_contract"))
    failures.extend(validate_route_output_contract(gate, label))
    failures.extend(validate_policy_sections(gate, label))
    failures.extend(validate_forbidden_output_fields(gate, label))
    if gate.get("production_readiness") != PRODUCTION_READINESS_EXPECTED:
        failures.append(f"{label}.production_readiness mismatch")
    if gate.get("final_ready") is not False:
        failures.append(f"{label}.final_ready must be false")

    report = build_report(
        root=root,
        gate=gate,
        registry=registry,
        consumer_access_gate=consumer_access_gate,
        schema_path=DEFAULT_SCHEMA,
        production_gate_path=DEFAULT_PRODUCTION_GATE,
        fixture_path=DEFAULT_FIXTURE,
    )
    failures.extend(validate_report(report, f"{label}.generated_report"))
    if label == "production_gate" and report.get("eligible_universe_ids") != ["KALSHI_BINARY_SHORT_HORIZON"]:
        failures.append("production_gate generated report must route only KALSHI_BINARY_SHORT_HORIZON explicitly")
    return failures, report


def _gate_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    gate = copy.deepcopy(fixture)
    for field in ("fixture_id", "fixture_version", "mode", "execution", "fixture_cases"):
        gate.pop(field, None)
    return gate


def _case_gate_registry_consumer_report(
    fixture: dict[str, Any],
    case: dict[str, Any],
    registry: dict[str, Any],
    consumer_access_gate: dict[str, Any],
    root: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    gate = _gate_from_fixture(fixture)
    case_registry = copy.deepcopy(registry)
    case_consumer_gate = copy.deepcopy(consumer_access_gate)
    request = _mapping(gate.get("routing_request_contract"))

    if isinstance(case.get("request_overrides"), dict):
        _deep_update(request, case["request_overrides"])
    if isinstance(case.get("trade_context_overrides"), dict):
        _deep_update(_mapping(request.get("trade_context")), case["trade_context_overrides"])
    if isinstance(case.get("trade_context_extra_fields"), dict):
        _mapping(request.get("trade_context")).update(case["trade_context_extra_fields"])
    if isinstance(case.get("gate_overrides"), dict):
        _deep_update(gate, case["gate_overrides"])
    if isinstance(case.get("consumer_gate_overrides"), dict):
        _deep_update(case_consumer_gate, case["consumer_gate_overrides"])

    remove_universe = case.get("remove_universe_id")
    if isinstance(remove_universe, str):
        case_registry["required_selection_universe_ids"] = [
            uid for uid in case_registry.get("required_selection_universe_ids", []) if uid != remove_universe
        ]
        case_registry["universe_definitions"] = [
            universe
            for universe in _list_of_mappings(case_registry.get("universe_definitions"))
            if universe.get("universe_id") != remove_universe
        ]
    if case.get("duplicate_universe_id") is True:
        definitions = _list_of_mappings(case_registry.get("universe_definitions"))
        if definitions:
            case_registry["universe_definitions"] = [*definitions, copy.deepcopy(definitions[0])]
    remove_consumer_access = case.get("remove_consumer_access_universe_id")
    if isinstance(remove_consumer_access, str):
        case_consumer_gate["allowed_universe_consumption_matrix"] = [
            row
            for row in _list_of_mappings(case_consumer_gate.get("allowed_universe_consumption_matrix"))
            if row.get("universe_id") != remove_consumer_access
        ]

    report = build_report(
        root=root,
        gate=gate,
        registry=case_registry,
        consumer_access_gate=case_consumer_gate,
        schema_path=DEFAULT_SCHEMA,
        production_gate_path=DEFAULT_PRODUCTION_GATE,
        fixture_path=DEFAULT_FIXTURE,
    )
    if isinstance(case.get("report_overrides"), dict):
        _deep_update(report, case["report_overrides"])
    return gate, case_registry, case_consumer_gate, report


def validate_fixture_cases(
    fixture: dict[str, Any],
    schema: dict[str, Any],
    registry: dict[str, Any],
    consumer_access_gate: dict[str, Any],
    root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    cases = {str(case.get("case_id")): case for case in _list_of_mappings(fixture.get("fixture_cases"))}
    missing = sorted(set(REQUIRED_FIXTURE_CASE_IDS) - set(cases))
    if missing:
        failures.append(f"PR81_FIXTURE_CASES_MISSING: {missing}")
    fixture_gate = _gate_from_fixture(fixture)
    base_failures, _base_report = validate_gate_document(
        gate=fixture_gate,
        schema=schema,
        registry=registry,
        consumer_access_gate=consumer_access_gate,
        root=root,
        label="fixture_gate",
    )
    if base_failures:
        failures.append(f"fixture_gate base invalid: {base_failures}")

    for case_id in REQUIRED_FIXTURE_CASE_IDS:
        case = cases.get(case_id)
        if case is None:
            continue
        gate, case_registry, case_consumer_gate, report = _case_gate_registry_consumer_report(
            fixture,
            case,
            registry,
            consumer_access_gate,
            root,
        )
        case_failures: list[str] = []
        case_failures.extend(validate_routing_request(_mapping(gate.get("routing_request_contract")), f"fixture_case.{case_id}"))
        case_failures.extend(validate_required_universes(case_registry, f"fixture_case.{case_id}.registry"))
        case_failures.extend(validate_policy_sections(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_report(report, f"fixture_case.{case_id}.report"))

        expected_reason = case.get("expected_reason_code")
        reason_observed = False
        meta_failures: list[str] = []
        if isinstance(expected_reason, str):
            all_codes = [
                str(code)
                for candidate in _list_of_mappings(report.get("route_candidates"))
                for code in candidate.get("reason_codes", [])
            ]
            all_codes.extend(
                str(code)
                for blocked in _list_of_mappings(report.get("blocked_universes"))
                for code in blocked.get("blocked_reason_codes", [])
            )
            reason_observed = expected_reason in all_codes or any(
                expected_reason in item for item in case_failures
            )
            if not reason_observed:
                meta_failures.append(f"expected reason {expected_reason} not observed")

        expected_valid = case.get("expected_schema_valid") is True
        if meta_failures:
            failures.append(f"{case_id}: {meta_failures}")
            continue
        if not expected_valid and reason_observed and isinstance(expected_reason, str):
            case_failures.append(f"{expected_reason} observed")
        if expected_valid and case_failures:
            failures.append(f"{case_id}: expected valid but failed {case_failures}")
        if not expected_valid and not case_failures:
            failures.append(f"{case_id}: expected fail-closed validation failure")
    return failures


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate(
    *,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    _trade_schema, _trade_packet, registry, consumer_access_gate, dependency_failures = validate_dependencies(root)
    failures.extend(dependency_failures)

    schema, schema_failures = _load_json_checked(root / schema_path, "PR81_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_gate = load_yaml(root / production_gate_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR81_PRODUCTION_GATE_MALFORMED: {exc}"]),
            report=None,
        )
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR81_FIXTURE_MALFORMED: {exc}"]),
            report=None,
        )

    if schema:
        gate_failures, report = validate_gate_document(
            gate=production_gate,
            schema=schema,
            registry=registry,
            consumer_access_gate=consumer_access_gate,
            root=root,
            label="production_gate",
        )
        failures.extend(gate_failures)
        failures.extend(validate_fixture_cases(fixture, schema, registry, consumer_access_gate, root))
    else:
        report = build_report(
            root=root,
            gate=production_gate,
            registry=registry,
            consumer_access_gate=consumer_access_gate,
            schema_path=schema_path,
            production_gate_path=production_gate_path,
            fixture_path=fixture_path,
        )

    second_report = build_report(
        root=root,
        gate=production_gate,
        registry=registry,
        consumer_access_gate=consumer_access_gate,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR81 report is not deterministic")

    artifact_texts = (
        (_as_posix(schema_path), _read_text(root / schema_path)),
        (_as_posix(production_gate_path), _read_text(root / production_gate_path)),
        ("generated_report", serialize_report(report)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))
    failures.extend(validate_validator_source_static(root))
    failures.extend(validate_report(report))

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--production-gate", default=str(DEFAULT_PRODUCTION_GATE))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        production_gate_path=pathlib.Path(args.production_gate),
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
