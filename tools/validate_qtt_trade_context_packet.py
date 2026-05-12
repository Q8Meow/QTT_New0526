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

DEFAULT_SCHEMA = pathlib.Path("schemas") / "edge" / "qtt_trade_context_packet.schema.json"
DEFAULT_PRODUCTION_PACKET = (
    pathlib.Path("docs") / "master_plan" / "edge" / "QTTTradeContextPacket.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "edge"
    / "synthetic_qtt_trade_context_packet.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTTradeContextPacket.report.json"
)

PR77_SCHEMA = pathlib.Path("schemas") / "edge" / "edge_parameter_stack_selection_packet.schema.json"
PR77_REGISTRY = (
    pathlib.Path("docs") / "master_plan" / "edge" / "EDGEParameterStackSelectionPacket.yaml"
)
PR77_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "EDGEParameterStackSelectionPacket.report.json"
)
PR77_VALIDATOR = pathlib.Path("tools") / "validate_edge_parameter_stack_selection_packet.py"
PR73_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_stack_role_taxonomy.schema.json"
)
PR73_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackRoleTaxonomy.yaml"
)
PR73_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackRoleTaxonomy.report.json"
)
PR73_VALIDATOR = pathlib.Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"
PR74_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_stack_completeness_gate.schema.json"
)
PR74_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackCompletenessGate.yaml"
)
PR74_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackCompletenessGate.report.json"
)
PR74_VALIDATOR = (
    pathlib.Path("tools") / "validate_atomicrows_parameter_stack_completeness_gate.py"
)
PR75_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_stack_compatibility_gate.schema.json"
)
PR75_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackCompatibilityGate.yaml"
)
PR75_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackCompatibilityGate.report.json"
)
PR75_VALIDATOR = (
    pathlib.Path("tools") / "validate_atomicrows_parameter_stack_compatibility_gate.py"
)

CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
PR76_SHORT_TEST = (
    pathlib.Path("tests")
    / "source_evidence"
    / "test_runtime_resolver_allowlist_live_blocks.py"
)
PR76_OLD_LONG_TEST = (
    pathlib.Path("tests")
    / "source_evidence"
    / "test_stage1_runtime_resolver_snapshot_consumer_allowlist_blocks_direct_live_dual_review_dashboard.py"
)

PACKET_ID = "QTT_TRADE_CONTEXT_PACKET"
PACKET_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-TRADE-CONTEXT-SCHEMA"
AUTHORITY_CLASS = (
    "STATIC_TRADE_CONTEXT_PACKET_SCHEMA_ONLY_NOT_ROUTING_NOT_SELECTION_NOT_SCORING_"
    "NOT_RUNTIME_AUTHORITY"
)
REPORT_ID = "QTT_TRADE_CONTEXT_PACKET_SCHEMA_REPORT"
REPORT_VERSION = "v1"
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_ROUTING_NOT_SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
VALIDATOR_NAME = "validate_qtt_trade_context_packet.py"
SUCCESS_MARKER = "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK"
FAILURE_MARKER = "QTT_TRADE_CONTEXT_PACKET_SCHEMA_FAILED"

PR77_SUCCESS_MARKER = "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"
PR73_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
PR74_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
PR75_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"

MINIMUM_REQUIRED_PACKET_FIELDS = (
    "trade_context_id",
    "platform",
    "market_type",
    "venue_scope",
    "strategy_class",
    "edge_type",
    "order_intent_type",
    "latency_sensitivity_class",
    "capital_intensity_class",
    "risk_mode",
    "liquidity_context",
    "time_horizon",
    "owner_override_basis",
    "quantum_priority_mode",
)
SHARED_EDGE_FIELDS = (
    "venue_scope",
    "edge_type",
    "strategy_class",
    "market_type",
    "latency_sensitivity_class",
    "capital_intensity_class",
)
SCHEMA_REQUIRED_FIELDS = (
    "packet_id",
    "packet_version",
    "authority_class",
    "semantic_task_id",
    "depends_on_edge_parameter_stack_selection_packet",
    "depends_on_parameter_stack_role_taxonomy",
    "depends_on_parameter_stack_completeness_gate",
    "depends_on_parameter_stack_compatibility_gate",
    "minimum_required_packet_fields",
    "shared_fields_aligned_with_edge_packet",
    *MINIMUM_REQUIRED_PACKET_FIELDS,
    "context_static_policy",
    "static_packet_policy",
    "order_intent_boundary_policy",
    "owner_override_policy",
    "source_evidence_boundary_policy",
    "connector_semantic_boundary_policy",
    "runtime_live_order_boundary_policy",
    "quantum_priority_boundary_policy",
    "future_consumer_contract",
    "forbidden_output_fields_policy",
    "explicit_no_claim_flags",
    "validation_invariants",
    "production_readiness",
    "final_ready",
)

PLATFORM_VALUES = (
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
    "MULTI_PLATFORM_PARALLEL",
    "SYNTHETIC_PLATFORM_SCHEMA_ONLY",
)
MARKET_TYPE_VALUES = (
    "PREDICTION_MARKET",
    "EVENT_MARKET",
    "BINARY_OUTCOME",
    "MULTI_OUTCOME",
    "FORECAST_CONTRACT",
    "SYNTHETIC_MARKET_TYPE_SCHEMA_ONLY",
)
VENUE_SCOPE_VALUES = (
    "SINGLE_PLATFORM",
    "MULTI_PLATFORM_PARALLEL",
    "CROSS_VENUE_STATIC_CONTEXT_ONLY",
    "SYNTHETIC_VENUE_SCOPE_SCHEMA_ONLY",
)
STRATEGY_CLASS_VALUES = (
    "MARKET_MAKING_CANDIDATE_STATIC_ONLY",
    "MOMENTUM_CANDIDATE_STATIC_ONLY",
    "ARBITRAGE_CANDIDATE_STATIC_ONLY",
    "EVENT_RISK_HEDGE_CANDIDATE_STATIC_ONLY",
    "LIQUIDITY_SENSITIVE_CANDIDATE_STATIC_ONLY",
    "QUANTUM_OPTIMIZATION_CANDIDATE_STATIC_ONLY",
    "SYNTHETIC_STRATEGY_SCHEMA_ONLY",
)
EDGE_TYPE_VALUES = (
    "OWNER_SUBMITTED_EDGE_STATIC_ONLY",
    "RESEARCH_EDGE_STATIC_ONLY",
    "MICROSTRUCTURE_EDGE_STATIC_ONLY",
    "SOURCE_DECLARED_EDGE_STATIC_ONLY",
    "QUANTUM_ADVISORY_EDGE_STATIC_ONLY",
    "SYNTHETIC_EDGE_SCHEMA_ONLY",
)
ORDER_INTENT_TYPE_VALUES = (
    "NO_ORDER_INTENT_SCHEMA_ONLY",
    "CANDIDATE_ORDER_INTENT_NON_AUTHORITATIVE",
    "REPLAY_PAPER_ORDER_INTENT_STATIC_ONLY",
    "OWNER_REVIEW_REQUIRED_BEFORE_ORDER_AUTHORITY",
    "SYNTHETIC_ORDER_INTENT_SCHEMA_ONLY",
)
LATENCY_SENSITIVITY_CLASS_VALUES = (
    "LATENCY_LOW_STATIC_CONTEXT_ONLY",
    "LATENCY_MEDIUM_STATIC_CONTEXT_ONLY",
    "LATENCY_HIGH_STATIC_CONTEXT_ONLY",
    "LATENCY_ULTRA_LOW_CANDIDATE_STATIC_ONLY",
    "LATENCY_SOURCE_PACKET_REQUIRED_BEFORE_LIVE_USE",
)
CAPITAL_INTENSITY_CLASS_VALUES = (
    "CAPITAL_PAPER_ONLY_STATIC_CONTEXT",
    "CAPITAL_LOW_STATIC_CONTEXT_ONLY",
    "CAPITAL_MEDIUM_STATIC_CONTEXT_ONLY",
    "CAPITAL_HIGH_STATIC_CONTEXT_ONLY",
    "CAPITAL_OWNER_DEFINED_INTERNAL_ONLY",
    "CAPITAL_RUNTIME_RECEIPT_REQUIRED_BEFORE_LIVE_USE",
)
RISK_MODE_VALUES = (
    "RISK_OFF_SCHEMA_ONLY",
    "RISK_CONSERVATIVE_STATIC_CONTEXT_ONLY",
    "RISK_BALANCED_STATIC_CONTEXT_ONLY",
    "RISK_AGGRESSIVE_CANDIDATE_STATIC_ONLY",
    "RISK_OWNER_OVERRIDE_INTERNAL_ONLY",
    "SYNTHETIC_RISK_MODE_SCHEMA_ONLY",
)
LIQUIDITY_CONTEXT_VALUES = (
    "LIQUIDITY_UNKNOWN_STATIC_CONTEXT_ONLY",
    "LIQUIDITY_LOW_STATIC_CONTEXT_ONLY",
    "LIQUIDITY_MEDIUM_STATIC_CONTEXT_ONLY",
    "LIQUIDITY_HIGH_STATIC_CONTEXT_ONLY",
    "LIQUIDITY_SOURCE_PACKET_REQUIRED_BEFORE_CONNECTOR_OR_LIVE_USE",
    "SYNTHETIC_LIQUIDITY_CONTEXT_SCHEMA_ONLY",
)
TIME_HORIZON_VALUES = (
    "INTRADAY_STATIC_CONTEXT_ONLY",
    "SHORT_HORIZON_STATIC_CONTEXT_ONLY",
    "EVENT_DRIVEN_STATIC_CONTEXT_ONLY",
    "MULTI_DAY_STATIC_CONTEXT_ONLY",
    "OWNER_DEFINED_TIME_HORIZON_INTERNAL_ONLY",
    "SYNTHETIC_TIME_HORIZON_SCHEMA_ONLY",
)
QUANTUM_PRIORITY_MODE_VALUES = (
    "QUANTUM_NEUTRAL",
    "QUANTUM_PREFERRED",
    "QUANTUM_STRONGLY_PREFERRED",
    "QUANTUM_FIRST_REQUESTED_STATIC_ONLY",
    "OWNER_FORCED_QUANTUM_REQUESTED_STATIC_ONLY",
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_REQUESTED_STATIC_ONLY",
    "QUANTUM_PRIORITY_POLICY_PENDING_PR83",
)
OWNER_OVERRIDE_TOKEN_VALUES = (
    "NONE",
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_APPROVED",
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED_OVERRIDE",
)
OWNER_OVERRIDE_SCOPE_VALUES = (
    "NONE",
    "INTERNAL_TRADE_CONTEXT_SCHEMA_READINESS_ONLY",
    "INTERNAL_ROUTING_REQUEST_CONTEXT_ONLY",
    "INTERNAL_QUANTUM_PRIORITY_REQUEST_CONTEXT_ONLY",
    "INTERNAL_OWNER_DEFINED_CONTEXT_ONLY",
)

DEPENDENCY_OBJECTS = {
    "depends_on_edge_parameter_stack_selection_packet": {
        "schema_path": "schemas/edge/edge_parameter_stack_selection_packet.schema.json",
        "registry_path": "docs/master_plan/edge/EDGEParameterStackSelectionPacket.yaml",
        "report_path": "docs/master_plan/generated/EDGEParameterStackSelectionPacket.report.json",
        "validator_path": "tools/validate_edge_parameter_stack_selection_packet.py",
        "validation_marker": PR77_SUCCESS_MARKER,
    },
    "depends_on_parameter_stack_role_taxonomy": {
        "schema_path": "schemas/atomicrows/atomicrows_parameter_stack_role_taxonomy.schema.json",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsParameterStackRoleTaxonomy.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterStackRoleTaxonomy.report.json",
        "validator_path": "tools/validate_atomicrows_parameter_stack_role_taxonomy.py",
        "validation_marker": PR73_SUCCESS_MARKER,
    },
    "depends_on_parameter_stack_completeness_gate": {
        "schema_path": "schemas/atomicrows/atomicrows_parameter_stack_completeness_gate.schema.json",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsParameterStackCompletenessGate.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterStackCompletenessGate.report.json",
        "validator_path": "tools/validate_atomicrows_parameter_stack_completeness_gate.py",
        "validation_marker": PR74_SUCCESS_MARKER,
    },
    "depends_on_parameter_stack_compatibility_gate": {
        "schema_path": "schemas/atomicrows/atomicrows_parameter_stack_compatibility_gate.schema.json",
        "registry_path": "docs/master_plan/atomicrows/AtomicRowsParameterStackCompatibilityGate.yaml",
        "report_path": "docs/master_plan/generated/AtomicRowsParameterStackCompatibilityGate.report.json",
        "validator_path": "tools/validate_atomicrows_parameter_stack_compatibility_gate.py",
        "validation_marker": PR75_SUCCESS_MARKER,
    },
}

CONTEXT_STATIC_TRUE_FIELDS = ("trade_context_is_static_schema_only",)
CONTEXT_STATIC_FALSE_FIELDS = (
    "trade_context_routes_selection_universe",
    "trade_context_selects_stack",
    "trade_context_scores_stack",
    "trade_context_ranks_stack",
    "trade_context_arbitrates_optimizer",
    "trade_context_executes_replay_or_paper",
    "trade_context_executes_runtime_or_live",
    "final_ready_created_by_this_pr",
)
ORDER_INTENT_TRUE_FIELDS = (
    "order_intent_type_is_static_context_only",
    "future_order_router_authority_required_before_order_submission",
)
ORDER_INTENT_FALSE_FIELDS = (
    "order_intent_type_creates_order_authority",
    "order_intent_type_creates_order_receipt",
    "order_intent_type_creates_fill_receipt",
    "order_intent_type_submits_order",
    "order_intent_type_cancels_order",
    "order_intent_type_reduces_order",
    "order_intent_type_closes_position",
)
OWNER_OVERRIDE_BASIS_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
)
OWNER_OVERRIDE_POLICY_FALSE_FIELDS = OWNER_OVERRIDE_BASIS_FALSE_FIELDS
SOURCE_TRUE_FIELDS = (
    "source_dependent_context_values_are_static_labels_only",
    "owner_policy_may_authorize_retrieval_scope",
    "external_fact_requires_accepted_source_packet",
    "market_data_fact_requires_accepted_source_packet",
    "liquidity_fact_requires_accepted_source_packet",
    "connector_semantic_requires_accepted_source_packet",
)
SOURCE_FALSE_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "owner_policy_may_authorize_external_fact_value",
)
CONNECTOR_TRUE_FIELDS = (
    "connector_unlock_requires_accepted_target_field_packet",
    "connector_unlock_requires_fresh_revalidation_state",
    "connector_unlock_requires_target_field_scope_match",
    "trade_context_does_not_unlock_connector_semantics",
)
CONNECTOR_FALSE_FIELDS = (
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "connector_semantic_value_created",
)
RUNTIME_TRUE_FIELDS = (
    "trade_context_is_not_runtime_signal",
    "trade_context_is_not_live_order_instruction",
)
RUNTIME_FALSE_FIELDS = (
    "runtime_artifacts_created",
    "runtime_resolver_execution_created",
    "private_state_fetch_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "order_authority_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
    "profit_evidence_created",
)
QUANTUM_TRUE_FIELDS = (
    "quantum_priority_mode_required",
    "quantum_priority_mode_static_context_only",
    "future_quantum_applicability_registry_required_before_quantum_selection",
    "future_owner_quantum_priority_policy_required_before_quantum_priority_selection",
    "future_optimizer_arbitration_gate_required_before_optimizer_choice",
    "strongest_classical_comparator_required_before_quantum_advantage_claim",
    "fallback_bundle_required_before_quantum_runtime_use",
    "replay_paper_evidence_required_before_advantage_claim",
    "live_evidence_required_before_profit_claim",
)
QUANTUM_FALSE_FIELDS = (
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_scoring_created",
    "quantum_ranking_created",
    "quantum_selection_created",
    "quantum_arbitration_created",
)
FUTURE_CONSUMER_TRUE_FIELDS = (
    "edge_parameter_stack_selection_packet_may_reference",
    "atomicrows_parameter_selection_universe_registry_may_consume",
    "parameter_selection_universe_consumer_gate_may_consume",
    "trade_context_to_selection_universe_routing_gate_may_consume",
    "quantum_applicability_classification_registry_may_consume",
    "owner_quantum_priority_policy_registry_may_consume",
    "scoring_policy_registry_may_consume",
    "parameter_stack_scoring_ranking_gate_may_consume",
    "quantum_classical_optimizer_arbitration_gate_may_consume",
    "candidate_parameter_stack_generation_gate_may_consume",
    "trade_context_parameter_stack_selection_gate_may_consume",
    "selected_parameter_stack_handoff_packet_may_consume",
    "replay_paper_candidate_stack_competition_gate_may_consume",
)
FUTURE_CONSUMER_FALSE_FIELDS = (
    "this_pr_performs_selection_universe_registry",
    "this_pr_performs_selection_universe_consumer_gate",
    "this_pr_performs_routing",
    "this_pr_performs_scoring",
    "this_pr_performs_ranking",
    "this_pr_performs_selection",
    "this_pr_performs_arbitration",
    "this_pr_generates_candidate_stacks",
    "this_pr_executes_replay_or_paper",
    "this_pr_executes_runtime_or_live",
)
FORBIDDEN_OUTPUT_FIELDS = (
    "selected_stack_id",
    "selected_parameter_families",
    "selected_algorithm_families",
    "selection_universe_ids",
    "route_result_id",
    "score_breakdown",
    "optimizer_arbitration_result",
    "replay_result_id",
    "paper_result_id",
    "order_id",
    "fill_id",
    "cash_receipt_id",
    "profit_evidence_id",
)
FORBIDDEN_OUTPUT_POLICY_TRUE_FIELDS = (
    "selected_stack_id_forbidden_in_trade_context",
    "selected_parameter_families_forbidden_in_trade_context",
    "selected_algorithm_families_forbidden_in_trade_context",
    "selection_universe_ids_forbidden_as_output_in_this_pr",
    "route_result_id_forbidden_in_this_pr",
    "score_breakdown_forbidden_in_this_pr",
    "optimizer_arbitration_result_forbidden_in_this_pr",
    "replay_result_id_forbidden_in_this_pr",
    "paper_result_id_forbidden_in_this_pr",
    "order_id_forbidden_in_this_pr",
    "fill_id_forbidden_in_this_pr",
    "cash_receipt_id_forbidden_in_this_pr",
    "profit_evidence_id_forbidden_in_this_pr",
)
EXPLICIT_NO_CLAIM_FALSE_FIELDS = (
    "trade_context_routing_created",
    "selection_universe_registry_created",
    "selection_universe_consumer_gate_created",
    "selected_stack_authority_created",
    "stack_selection_created",
    "scoring_created",
    "ranking_created",
    "optimizer_arbitration_created",
    "candidate_stack_generation_created",
    "selected_stack_handoff_created",
    "order_intent_authority_created",
    "order_authority_created",
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "connector_semantic_value_created",
    "runtime_artifacts_created",
    "runtime_resolver_execution_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "private_state_fetch_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
    "replay_execution_created",
    "paper_execution_created",
    "replay_results_created",
    "paper_results_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
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
    "qtt_trade_context_packet_schema_ready": True,
    "production_trade_context_evaluated": False,
    "production_trade_context_ready": False,
    "production_routing_evaluated": False,
    "production_routing_ready": False,
    "production_selection_ready": False,
    "final_ready": False,
}
FIXTURE_CASE_IDS = (
    "TRADE_CONTEXT_PACKET_SCHEMA_VALID_STATIC_ONLY",
    "TRADE_CONTEXT_BLOCKED_MISSING_TRADE_CONTEXT_ID",
    "TRADE_CONTEXT_BLOCKED_MISSING_PLATFORM",
    "TRADE_CONTEXT_BLOCKED_MISSING_MARKET_TYPE",
    "TRADE_CONTEXT_BLOCKED_MISSING_ORDER_INTENT_TYPE",
    "TRADE_CONTEXT_BLOCKED_MISSING_QUANTUM_PRIORITY_MODE",
    "TRADE_CONTEXT_BLOCKED_ORDER_AUTHORITY_ATTEMPT",
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_TRADE_CONTEXT_READINESS_ONLY",
    "TRADE_CONTEXT_BLOCKED_LIQUIDITY_FACT_WITHOUT_ACCEPTED_SOURCE_PACKET",
    "TRADE_CONTEXT_BLOCKED_EXTERNAL_FACT_AUTHORITY_ATTEMPT",
    "TRADE_CONTEXT_BLOCKED_CONNECTOR_SEMANTIC_ATTEMPT",
    "TRADE_CONTEXT_BLOCKED_RUNTIME_LIVE_ORDER_ATTEMPT",
    "TRADE_CONTEXT_BLOCKED_QUANTUM_SELECTION_ATTEMPT",
    "TRADE_CONTEXT_BLOCKED_QUANTUM_BACKEND_ATTEMPT",
    "TRADE_CONTEXT_BLOCKED_QUANTUM_ADVANTAGE_CLAIM",
    "TRADE_CONTEXT_BLOCKED_SELECTED_STACK_ID_FIELD",
    "TRADE_CONTEXT_BLOCKED_SELECTION_UNIVERSE_OUTPUT_FIELD",
    "TRADE_CONTEXT_BLOCKED_SCORE_BREAKDOWN_FIELD",
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


def _dependency_report_or_validator_ok(
    *,
    root: pathlib.Path,
    report_path: pathlib.Path,
    validator_path: pathlib.Path,
    marker: str,
    label: str,
) -> list[str]:
    report_file = root / report_path
    if report_file.exists():
        try:
            report = load_json(report_file)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return [f"{label}_REPORT_MALFORMED: {exc}"]
        if report.get("validation_marker") == marker:
            return []

    completed = subprocess.run(
        [sys.executable, str(root / validator_path)],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode == 0 and marker in completed.stdout.split():
        return []
    return [
        f"{label}_VALIDATION_BLOCK: marker {marker} missing "
        f"stdout={completed.stdout.strip()!r} stderr={completed.stderr.strip()!r}"
    ]


def _validate_dependency_files(
    *,
    root: pathlib.Path,
    label: str,
    schema_path: pathlib.Path,
    registry_path: pathlib.Path,
    report_path: pathlib.Path,
    validator_path: pathlib.Path,
    marker: str,
    missing_block: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    failures: list[str] = []
    for item_label, rel_path in (
        ("SCHEMA", schema_path),
        ("REGISTRY", registry_path),
        ("REPORT", report_path),
        ("VALIDATOR", validator_path),
    ):
        if not (root / rel_path).exists():
            failures.append(f"{missing_block}: {label}_{item_label} missing")
    if failures:
        return {}, {}, {}, failures

    try:
        schema = load_json(root / schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"{missing_block}: {label}_SCHEMA malformed: {exc}")
        schema = {}
    try:
        registry = load_yaml(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        failures.append(f"{missing_block}: {label}_REGISTRY malformed: {exc}")
        registry = {}
    try:
        report = load_json(root / report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"{missing_block}: {label}_REPORT malformed: {exc}")
        report = {}

    if not failures:
        failures.extend(
            _dependency_report_or_validator_ok(
                root=root,
                report_path=report_path,
                validator_path=validator_path,
                marker=marker,
                label=label,
            )
        )
    return schema, registry, report, failures


def validate_pr73_dependency(root: pathlib.Path) -> list[str]:
    _, _, _, failures = _validate_dependency_files(
        root=root,
        label="PR73_ROLE_TAXONOMY",
        schema_path=PR73_SCHEMA,
        registry_path=PR73_REGISTRY,
        report_path=PR73_REPORT,
        validator_path=PR73_VALIDATOR,
        marker=PR73_SUCCESS_MARKER,
        missing_block="PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK",
    )
    return failures


def validate_pr74_dependency(root: pathlib.Path) -> list[str]:
    _, _, _, failures = _validate_dependency_files(
        root=root,
        label="PR74_COMPLETENESS_GATE",
        schema_path=PR74_SCHEMA,
        registry_path=PR74_REGISTRY,
        report_path=PR74_REPORT,
        validator_path=PR74_VALIDATOR,
        marker=PR74_SUCCESS_MARKER,
        missing_block="PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK",
    )
    return failures


def validate_pr75_dependency(root: pathlib.Path) -> list[str]:
    _, _, _, failures = _validate_dependency_files(
        root=root,
        label="PR75_COMPATIBILITY_GATE",
        schema_path=PR75_SCHEMA,
        registry_path=PR75_REGISTRY,
        report_path=PR75_REPORT,
        validator_path=PR75_VALIDATOR,
        marker=PR75_SUCCESS_MARKER,
        missing_block="PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK",
    )
    return failures


def validate_pr77_dependency(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    schema, registry, _, failures = _validate_dependency_files(
        root=root,
        label="PR77_EDGE_PACKET_SCHEMA",
        schema_path=PR77_SCHEMA,
        registry_path=PR77_REGISTRY,
        report_path=PR77_REPORT,
        validator_path=PR77_VALIDATOR,
        marker=PR77_SUCCESS_MARKER,
        missing_block="PR77_EDGE_PACKET_SCHEMA_DEPENDENCY_BLOCK",
    )
    return schema, registry, failures


def validate_repair_pr76_dependency(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if not (root / PR76_SHORT_TEST).exists():
        failures.append("PRE_PR78_REPAIR_NOT_APPLIED_BLOCK")
    if (root / PR76_OLD_LONG_TEST).exists():
        failures.append("OLD_LONG_RUNTIME_RESOLVER_TEST_REINTRODUCED_BLOCK")
    return failures


def _enum_from_schema(schema: dict[str, Any], field: str) -> list[str]:
    value = _mapping(_mapping(schema.get("properties")).get(field)).get("enum")
    return list(value) if isinstance(value, list) else []


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list):
        return ["PR78 schema root required must be a list"]
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR78 schema missing required root field {field}")
    if schema.get("additionalProperties") is not False:
        failures.append("PR78 schema must be strict with additionalProperties false")

    properties = _mapping(schema.get("properties"))
    if _mapping(properties.get("packet_id")).get("const") != PACKET_ID:
        failures.append("PR78 schema packet_id const mismatch")
    if _mapping(properties.get("packet_version")).get("const") != PACKET_VERSION:
        failures.append("PR78 schema packet_version const mismatch")
    if _mapping(properties.get("authority_class")).get("const") != AUTHORITY_CLASS:
        failures.append("PR78 schema authority_class const mismatch")
    if _mapping(properties.get("semantic_task_id")).get("const") != SEMANTIC_TASK_ID:
        failures.append("PR78 schema semantic_task_id const mismatch")
    if _mapping(properties.get("minimum_required_packet_fields")).get("const") != list(
        MINIMUM_REQUIRED_PACKET_FIELDS
    ):
        failures.append("PR78 schema minimum_required_packet_fields const mismatch")
    if _mapping(properties.get("shared_fields_aligned_with_edge_packet")).get("const") != list(
        SHARED_EDGE_FIELDS
    ):
        failures.append("PR78 schema shared_fields_aligned_with_edge_packet const mismatch")

    expected_enums = {
        "platform": PLATFORM_VALUES,
        "market_type": MARKET_TYPE_VALUES,
        "venue_scope": VENUE_SCOPE_VALUES,
        "strategy_class": STRATEGY_CLASS_VALUES,
        "edge_type": EDGE_TYPE_VALUES,
        "order_intent_type": ORDER_INTENT_TYPE_VALUES,
        "latency_sensitivity_class": LATENCY_SENSITIVITY_CLASS_VALUES,
        "capital_intensity_class": CAPITAL_INTENSITY_CLASS_VALUES,
        "risk_mode": RISK_MODE_VALUES,
        "liquidity_context": LIQUIDITY_CONTEXT_VALUES,
        "time_horizon": TIME_HORIZON_VALUES,
        "quantum_priority_mode": QUANTUM_PRIORITY_MODE_VALUES,
    }
    for field, values in expected_enums.items():
        if _enum_from_schema(schema, field) != list(values):
            failures.append(f"PR78 schema {field} enum mismatch")

    owner_basis = _mapping(_mapping(schema.get("$defs")).get("owner_override_basis"))
    owner_props = _mapping(owner_basis.get("properties"))
    if _mapping(owner_props.get("owner_override_token")).get("enum") != list(
        OWNER_OVERRIDE_TOKEN_VALUES
    ):
        failures.append("PR78 schema owner_override_token enum mismatch")
    if _mapping(owner_props.get("owner_override_scope")).get("enum") != list(
        OWNER_OVERRIDE_SCOPE_VALUES
    ):
        failures.append("PR78 schema owner_override_scope enum mismatch")

    no_claim_required = _mapping(_mapping(schema.get("$defs")).get("explicit_no_claim_flags")).get(
        "required"
    )
    if no_claim_required != list(EXPLICIT_NO_CLAIM_FALSE_FIELDS):
        failures.append("PR78 schema explicit_no_claim_flags required field order mismatch")
    for field in FORBIDDEN_OUTPUT_FIELDS:
        if field in properties:
            failures.append(f"PR78 schema must not define forbidden output field {field}")
    return failures


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


def _looks_like_uuid(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            value,
        )
    )


def validate_required_fields(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    minimum = payload.get("minimum_required_packet_fields")
    if minimum != list(MINIMUM_REQUIRED_PACKET_FIELDS):
        failures.append(f"{label}.minimum_required_packet_fields mismatch")
    for field in MINIMUM_REQUIRED_PACKET_FIELDS:
        if field not in payload:
            failures.append(f"{label} missing required trade-context field {field}")
    trade_context_id = payload.get("trade_context_id")
    if not isinstance(trade_context_id, str) or not trade_context_id:
        failures.append(f"{label}.trade_context_id must be a nonempty deterministic string")
    elif _looks_like_uuid(trade_context_id):
        failures.append(f"{label}.trade_context_id must not be a random UUID")
    return failures


def validate_shared_edge_alignment(
    *,
    schema: dict[str, Any],
    production_packet: dict[str, Any],
    edge_schema: dict[str, Any],
    edge_packet: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    schema_required = set(schema.get("required", []))
    schema_properties = set(_mapping(schema.get("properties")))
    edge_required = set(edge_schema.get("required", []))
    edge_properties = set(_mapping(edge_schema.get("properties")))
    edge_minimum = set(edge_packet.get("minimum_required_packet_fields", []))

    for field in SHARED_EDGE_FIELDS:
        if field not in schema_required or field not in schema_properties:
            failures.append(f"PR78 schema shared field missing: {field}")
        if field not in edge_required or field not in edge_properties or field not in edge_minimum:
            failures.append(f"PR77 EDGE shared field missing: {field}")
    if production_packet.get("shared_fields_aligned_with_edge_packet") != list(SHARED_EDGE_FIELDS):
        failures.append("production_packet.shared_fields_aligned_with_edge_packet mismatch")
    return failures


def validate_context_static_policy(payload: dict[str, Any], label: str) -> list[str]:
    failures = _expect_policy_fields(
        payload,
        "context_static_policy",
        CONTEXT_STATIC_TRUE_FIELDS,
        CONTEXT_STATIC_FALSE_FIELDS,
        label,
    )
    failures.extend(
        _expect_policy_fields(
            payload,
            "static_packet_policy",
            CONTEXT_STATIC_TRUE_FIELDS,
            CONTEXT_STATIC_FALSE_FIELDS,
            label,
        )
    )
    return failures


def validate_owner_override_policy(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    basis = _mapping(payload.get("owner_override_basis"))
    if basis.get("owner_override_internal_workflow_only") is not True:
        failures.append(f"{label}.owner_override_basis must be internal workflow only")
    if basis.get("owner_override_token") not in OWNER_OVERRIDE_TOKEN_VALUES:
        failures.append(f"{label}.owner_override_token invalid")
    if basis.get("owner_override_scope") not in OWNER_OVERRIDE_SCOPE_VALUES:
        failures.append(f"{label}.owner_override_scope invalid")
    if basis.get("owner_override_token") == "OWNER_GLOBAL_OVERRIDE":
        if basis.get("owner_override_present") is not True:
            failures.append(f"{label}.OWNER_GLOBAL_OVERRIDE must set owner_override_present true")
        if basis.get("owner_override_scope") != "INTERNAL_TRADE_CONTEXT_SCHEMA_READINESS_ONLY":
            failures.append(f"{label}.OWNER_GLOBAL_OVERRIDE scope must remain internal")
        if (
            basis.get("owner_override_satisfaction_basis")
            != "OWNER_GLOBAL_OVERRIDE_SATISFIED_INTERNAL_TRADE_CONTEXT_READINESS_ONLY"
        ):
            failures.append(f"{label}.OWNER_GLOBAL_OVERRIDE satisfaction basis mismatch")
    for field in OWNER_OVERRIDE_BASIS_FALSE_FIELDS:
        if basis.get(field) is not False:
            failures.append(f"{label}.owner_override_basis.{field} must be false")

    policy = _mapping(payload.get("owner_override_policy"))
    if policy.get("owner_override_supported") is not True:
        failures.append(f"{label}.owner_override_policy.owner_override_supported must be true")
    if policy.get("owner_override_satisfies_internal_trade_context_readiness_only") is not True:
        failures.append(
            f"{label}.owner_override_policy must satisfy internal trade-context readiness only"
        )
    for field in OWNER_OVERRIDE_POLICY_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"{label}.owner_override_policy.{field} must be false")
    return failures


def validate_order_intent_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures = _expect_policy_fields(
        payload,
        "order_intent_boundary_policy",
        ORDER_INTENT_TRUE_FIELDS,
        ORDER_INTENT_FALSE_FIELDS,
        label,
    )
    if payload.get("order_intent_type") not in ORDER_INTENT_TYPE_VALUES:
        failures.append(f"{label}.order_intent_type invalid")
    return failures


def validate_quantum_priority_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures = _expect_policy_fields(
        payload,
        "quantum_priority_boundary_policy",
        QUANTUM_TRUE_FIELDS,
        QUANTUM_FALSE_FIELDS,
        label,
    )
    if payload.get("quantum_priority_mode") not in QUANTUM_PRIORITY_MODE_VALUES:
        failures.append(f"{label}.quantum_priority_mode invalid")
    return failures


def validate_source_evidence_boundary(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "source_evidence_boundary_policy",
        SOURCE_TRUE_FIELDS,
        SOURCE_FALSE_FIELDS,
        label,
    )


def validate_connector_semantic_boundary(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "connector_semantic_boundary_policy",
        CONNECTOR_TRUE_FIELDS,
        CONNECTOR_FALSE_FIELDS,
        label,
    )


def validate_runtime_live_order_boundary(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "runtime_live_order_boundary_policy",
        RUNTIME_TRUE_FIELDS,
        RUNTIME_FALSE_FIELDS,
        label,
    )


def validate_future_consumer_contract(payload: dict[str, Any], label: str) -> list[str]:
    return _expect_policy_fields(
        payload,
        "future_consumer_contract",
        FUTURE_CONSUMER_TRUE_FIELDS,
        FUTURE_CONSUMER_FALSE_FIELDS,
        label,
    )


def validate_forbidden_output_fields(payload: dict[str, Any], label: str) -> list[str]:
    failures = _expect_policy_fields(
        payload,
        "forbidden_output_fields_policy",
        FORBIDDEN_OUTPUT_POLICY_TRUE_FIELDS,
        (),
        label,
    )
    for field in FORBIDDEN_OUTPUT_FIELDS:
        if field in payload:
            failures.append(f"{label}.{field} is forbidden in trade context packet")
    return failures


def validate_no_forbidden_flags(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    flags = _mapping(payload.get("explicit_no_claim_flags"))
    for field in EXPLICIT_NO_CLAIM_FALSE_FIELDS:
        if flags.get(field) is not False:
            failures.append(f"{label}.explicit_no_claim_flags.{field} must be false")
    if payload.get("final_ready") is not False:
        failures.append(f"{label}.final_ready must be false")
    return failures


def validate_production_packet(
    production_packet: dict[str, Any],
    schema: dict[str, Any],
    edge_schema: dict[str, Any],
    edge_packet: dict[str, Any],
) -> list[str]:
    failures = schema_subset_failures(production_packet, schema, "production_packet")
    if production_packet.get("packet_id") != PACKET_ID:
        failures.append("production_packet.packet_id mismatch")
    if production_packet.get("packet_version") != PACKET_VERSION:
        failures.append("production_packet.packet_version mismatch")
    if production_packet.get("authority_class") != AUTHORITY_CLASS:
        failures.append("production_packet.authority_class mismatch")
    if production_packet.get("semantic_task_id") != SEMANTIC_TASK_ID:
        failures.append("production_packet.semantic_task_id mismatch")
    for section, expected in DEPENDENCY_OBJECTS.items():
        if _mapping(production_packet.get(section)) != expected:
            failures.append(f"production_packet.{section} dependency mismatch")
    failures.extend(validate_required_fields(production_packet, "production_packet"))
    failures.extend(
        validate_shared_edge_alignment(
            schema=schema,
            production_packet=production_packet,
            edge_schema=edge_schema,
            edge_packet=edge_packet,
        )
    )
    failures.extend(validate_context_static_policy(production_packet, "production_packet"))
    failures.extend(validate_order_intent_boundary(production_packet, "production_packet"))
    failures.extend(validate_owner_override_policy(production_packet, "production_packet"))
    failures.extend(validate_quantum_priority_boundary(production_packet, "production_packet"))
    failures.extend(validate_source_evidence_boundary(production_packet, "production_packet"))
    failures.extend(validate_connector_semantic_boundary(production_packet, "production_packet"))
    failures.extend(validate_runtime_live_order_boundary(production_packet, "production_packet"))
    failures.extend(validate_future_consumer_contract(production_packet, "production_packet"))
    failures.extend(validate_forbidden_output_fields(production_packet, "production_packet"))
    failures.extend(validate_no_forbidden_flags(production_packet, "production_packet"))
    if _mapping(production_packet.get("production_readiness")) != PRODUCTION_READINESS_EXPECTED:
        failures.append("production_packet.production_readiness mismatch")
    return failures


def _base_packet_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    metadata_fields = {"fixture_id", "fixture_version", "mode", "execution", "fixture_cases"}
    return {
        key: copy.deepcopy(value)
        for key, value in fixture.items()
        if key not in metadata_fields
    }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def case_packet_from_fixture(fixture: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    packet = _deep_merge(_base_packet_from_fixture(fixture), _mapping(case.get("packet_overrides")))
    for field in case.get("missing_fields", []):
        if isinstance(field, str):
            packet.pop(field, None)
    return packet


def _case_by_id(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(case.get("case_id")): case
        for case in _list_of_mappings(fixture.get("fixture_cases"))
    }


def _normal_packet_ready(packet: dict[str, Any]) -> bool:
    readiness = _mapping(packet.get("production_readiness"))
    return (
        readiness.get("production_trade_context_ready") is True
        and readiness.get("production_routing_ready") is True
        and readiness.get("production_selection_ready") is True
        and packet.get("final_ready") is True
    )


def validate_fixture_cases(fixture: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(fixture, schema, "fixture")
    if fixture.get("fixture_id") != "SYNTHETIC_QTT_TRADE_CONTEXT_PACKET_FIXTURE":
        failures.append("fixture.fixture_id mismatch")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    failures.extend(validate_required_fields(fixture, "fixture"))
    failures.extend(validate_context_static_policy(fixture, "fixture"))
    failures.extend(validate_order_intent_boundary(fixture, "fixture"))
    failures.extend(validate_owner_override_policy(fixture, "fixture"))
    failures.extend(validate_quantum_priority_boundary(fixture, "fixture"))
    failures.extend(validate_source_evidence_boundary(fixture, "fixture"))
    failures.extend(validate_connector_semantic_boundary(fixture, "fixture"))
    failures.extend(validate_runtime_live_order_boundary(fixture, "fixture"))
    failures.extend(validate_future_consumer_contract(fixture, "fixture"))
    failures.extend(validate_forbidden_output_fields(fixture, "fixture"))
    failures.extend(validate_no_forbidden_flags(fixture, "fixture"))

    cases = _case_by_id(fixture)
    if list(cases) != list(FIXTURE_CASE_IDS):
        failures.append("fixture case order or IDs mismatch")

    for case_id in FIXTURE_CASE_IDS:
        case = _mapping(cases.get(case_id))
        if case.get("synthetic_case_only") is not True:
            failures.append(f"{case_id} must be synthetic only")
        packet = case_packet_from_fixture(fixture, case)
        case_failures = schema_subset_failures(packet, schema, case_id)
        expected_schema_valid = case.get("expected_schema_valid")
        if bool(case_failures) == bool(expected_schema_valid):
            failures.append(f"{case_id} schema validity did not match expected")
        if _normal_packet_ready(packet) != case.get("expected_normal_packet_ready"):
            failures.append(f"{case_id} normal packet readiness mismatch")

    for case_id, missing_field in (
        ("TRADE_CONTEXT_BLOCKED_MISSING_TRADE_CONTEXT_ID", "trade_context_id"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_PLATFORM", "platform"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_MARKET_TYPE", "market_type"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_ORDER_INTENT_TYPE", "order_intent_type"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_QUANTUM_PRIORITY_MODE", "quantum_priority_mode"),
    ):
        packet = case_packet_from_fixture(fixture, _mapping(cases.get(case_id)))
        if not any(missing_field in failure for failure in schema_subset_failures(packet, schema, case_id)):
            failures.append(f"{case_id} must fail for missing {missing_field}")

    owner_case = case_packet_from_fixture(
        fixture,
        _mapping(cases.get("OWNER_OVERRIDE_SATISFIED_INTERNAL_TRADE_CONTEXT_READINESS_ONLY")),
    )
    owner_basis = _mapping(owner_case.get("owner_override_basis"))
    if owner_basis.get("owner_override_token") != "OWNER_GLOBAL_OVERRIDE":
        failures.append("owner override fixture case must record OWNER_GLOBAL_OVERRIDE")
    failures.extend(validate_owner_override_policy(owner_case, "owner_override_fixture_case"))

    expected_blocking_cases = (
        "TRADE_CONTEXT_BLOCKED_ORDER_AUTHORITY_ATTEMPT",
        "TRADE_CONTEXT_BLOCKED_LIQUIDITY_FACT_WITHOUT_ACCEPTED_SOURCE_PACKET",
        "TRADE_CONTEXT_BLOCKED_EXTERNAL_FACT_AUTHORITY_ATTEMPT",
        "TRADE_CONTEXT_BLOCKED_CONNECTOR_SEMANTIC_ATTEMPT",
        "TRADE_CONTEXT_BLOCKED_RUNTIME_LIVE_ORDER_ATTEMPT",
        "TRADE_CONTEXT_BLOCKED_QUANTUM_SELECTION_ATTEMPT",
        "TRADE_CONTEXT_BLOCKED_QUANTUM_BACKEND_ATTEMPT",
        "TRADE_CONTEXT_BLOCKED_QUANTUM_ADVANTAGE_CLAIM",
        "TRADE_CONTEXT_BLOCKED_SELECTED_STACK_ID_FIELD",
        "TRADE_CONTEXT_BLOCKED_SELECTION_UNIVERSE_OUTPUT_FIELD",
        "TRADE_CONTEXT_BLOCKED_SCORE_BREAKDOWN_FIELD",
    )
    for case_id in expected_blocking_cases:
        packet = case_packet_from_fixture(fixture, _mapping(cases.get(case_id)))
        if not schema_subset_failures(packet, schema, case_id):
            failures.append(f"{case_id} must fail closed")
    return failures


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _forbidden_text_patterns() -> tuple[tuple[str, str], ...]:
    return (
        ("REAL_HTTP_LOCATOR", "http" + "://"),
        ("REAL_HTTPS_LOCATOR", "https" + "://"),
        ("REAL_WWW_LOCATOR", "www" + "."),
        ("SECRET_LIKE_API_KEY", "api" + " key"),
        ("SECRET_LIKE_API_KEY_UNDERSCORE", "api" + "_key"),
        ("SECRET_LIKE_PRIVATE_KEY", "private" + " key"),
        ("SECRET_LIKE_BEARER_TOKEN", "bearer" + " token"),
        ("CLONE_COMMAND", "git clone"),
        ("INSTALL_COMMAND", "pip install"),
        ("ORDER_COMMAND", "place order"),
        ("LIVE_TRADE_COMMAND", "live trading command"),
    )


def validate_no_forbidden_claims(artifact_texts: Iterable[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    for label, text in artifact_texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern in lowered:
                failures.append(f"{label}: forbidden static packet text {code}")
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
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR78"]
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {completed.stderr.strip()}"]


def _flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("explicit_no_claim_flags")).get(field))


def _policy_flag(payload: dict[str, Any], section: str, field: str) -> bool:
    return bool(_mapping(payload.get(section)).get(field))


def build_report(
    *,
    root: pathlib.Path,
    production_packet: dict[str, Any],
    schema_path: pathlib.Path,
    production_packet_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    readiness = _mapping(production_packet.get("production_readiness"))
    context = _mapping(production_packet.get("context_static_policy"))
    order = _mapping(production_packet.get("order_intent_boundary_policy"))
    owner = _mapping(production_packet.get("owner_override_policy"))
    quantum = _mapping(production_packet.get("quantum_priority_boundary_policy"))
    source = _mapping(production_packet.get("source_evidence_boundary_policy"))
    connector = _mapping(production_packet.get("connector_semantic_boundary_policy"))
    runtime = _mapping(production_packet.get("runtime_live_order_boundary_policy"))
    forbidden = _mapping(production_packet.get("forbidden_output_fields_policy"))

    return {
        "accepted_source_packets_created": source.get("accepted_source_packets_created")
        or _flag(production_packet, "accepted_source_packets_created"),
        "all_required_trade_context_fields_present": all(
            field in production_packet for field in MINIMUM_REQUIRED_PACKET_FIELDS
        ),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "candidate_stack_generation_created": _flag(
            production_packet, "candidate_stack_generation_created"
        ),
        "cash_receipts_created": runtime.get("cash_receipts_created")
        or _flag(production_packet, "cash_receipts_created"),
        "connector_semantic_binding_created": connector.get(
            "connector_semantic_binding_created"
        )
        or _flag(production_packet, "connector_semantic_binding_created"),
        "connector_semantic_value_created": connector.get("connector_semantic_value_created")
        or _flag(production_packet, "connector_semantic_value_created"),
        "connector_semantics_created": connector.get("connector_semantics_created")
        or _flag(production_packet, "connector_semantics_created"),
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "depends_on_pr77_edge_packet_schema": True,
        "edge_type_required": "edge_type" in production_packet,
        "execution_superiority_claim_created": _flag(
            production_packet, "execution_superiority_claim_created"
        ),
        "external_fact_value_created": _flag(production_packet, "external_fact_value_created"),
        "fallback_bundle_required_before_quantum_runtime_use": quantum.get(
            "fallback_bundle_required_before_quantum_runtime_use"
        ),
        "fill_receipts_created": runtime.get("fill_receipts_created")
        or _flag(production_packet, "fill_receipts_created"),
        "final_ready": production_packet.get("final_ready"),
        "fixture_path": _as_posix(fixture_path),
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": quantum.get(
            "future_optimizer_arbitration_gate_required_before_optimizer_choice"
        ),
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": quantum.get(
            "future_owner_quantum_priority_policy_required_before_quantum_priority_selection"
        ),
        "future_quantum_applicability_registry_required_before_quantum_selection": quantum.get(
            "future_quantum_applicability_registry_required_before_quantum_selection"
        ),
        "latency_superiority_claim_created": _flag(
            production_packet, "latency_superiority_claim_created"
        ),
        "live_evidence_required_before_profit_claim": quantum.get(
            "live_evidence_required_before_profit_claim"
        ),
        "live_readiness_created": runtime.get("live_readiness_created")
        or _flag(production_packet, "live_readiness_created"),
        "liquidity_fact_created": _flag(production_packet, "liquidity_fact_created"),
        "market_data_fact_created": _flag(production_packet, "market_data_fact_created"),
        "optimizer_arbitration_created": _flag(
            production_packet, "optimizer_arbitration_created"
        ),
        "optimizer_arbitration_result_forbidden_in_this_pr": forbidden.get(
            "optimizer_arbitration_result_forbidden_in_this_pr"
        ),
        "order_authority_created": runtime.get("order_authority_created")
        or _flag(production_packet, "order_authority_created"),
        "order_intent_type_creates_fill_receipt": order.get(
            "order_intent_type_creates_fill_receipt"
        ),
        "order_intent_type_creates_order_authority": order.get(
            "order_intent_type_creates_order_authority"
        ),
        "order_intent_type_creates_order_receipt": order.get(
            "order_intent_type_creates_order_receipt"
        ),
        "order_intent_type_is_static_context_only": order.get(
            "order_intent_type_is_static_context_only"
        ),
        "order_intent_type_required": "order_intent_type" in production_packet,
        "order_intent_type_submits_order": order.get("order_intent_type_submits_order"),
        "order_receipts_created": runtime.get("order_receipts_created")
        or _flag(production_packet, "order_receipts_created"),
        "owner_override_fabricates_accepted_source_packet": owner.get(
            "owner_override_fabricates_accepted_source_packet"
        ),
        "owner_override_fabricates_connector_semantic": owner.get(
            "owner_override_fabricates_connector_semantic"
        ),
        "owner_override_fabricates_external_fact": owner.get(
            "owner_override_fabricates_external_fact"
        ),
        "owner_override_fabricates_order_receipt": owner.get(
            "owner_override_fabricates_order_receipt"
        ),
        "owner_override_fabricates_profit_evidence": owner.get(
            "owner_override_fabricates_profit_evidence"
        ),
        "owner_override_fabricates_quantum_backend_execution": owner.get(
            "owner_override_fabricates_quantum_backend_execution"
        ),
        "owner_override_fabricates_replay_paper_result": owner.get(
            "owner_override_fabricates_replay_paper_result"
        ),
        "owner_override_fabricates_runtime_cash_receipt": owner.get(
            "owner_override_fabricates_runtime_cash_receipt"
        ),
        "owner_override_satisfies_internal_trade_context_readiness_only": owner.get(
            "owner_override_satisfies_internal_trade_context_readiness_only"
        ),
        "paper_execution_created": _flag(production_packet, "paper_execution_created"),
        "paper_results_created": _flag(production_packet, "paper_results_created"),
        "private_state_fetch_created": runtime.get("private_state_fetch_created")
        or _flag(production_packet, "private_state_fetch_created"),
        "production_packet_path": _as_posix(production_packet_path),
        "production_routing_evaluated": readiness.get("production_routing_evaluated"),
        "production_routing_ready": readiness.get("production_routing_ready"),
        "production_selection_ready": readiness.get("production_selection_ready"),
        "production_trade_context_evaluated": readiness.get(
            "production_trade_context_evaluated"
        ),
        "production_trade_context_ready": readiness.get("production_trade_context_ready"),
        "profit_evidence_created": runtime.get("profit_evidence_created")
        or _flag(production_packet, "profit_evidence_created"),
        "qtt_trade_context_packet_schema_ready": readiness.get(
            "qtt_trade_context_packet_schema_ready"
        ),
        "quantum_advantage_claim_created": quantum.get("quantum_advantage_claim_created")
        or _flag(production_packet, "quantum_advantage_claim_created"),
        "quantum_arbitration_created": quantum.get("quantum_arbitration_created"),
        "quantum_backend_evidence_created": _flag(
            production_packet, "quantum_backend_evidence_created"
        ),
        "quantum_priority_mode_required": quantum.get("quantum_priority_mode_required"),
        "quantum_priority_mode_static_context_only": quantum.get(
            "quantum_priority_mode_static_context_only"
        ),
        "quantum_selection_created": quantum.get("quantum_selection_created"),
        "ranking_created": _flag(production_packet, "ranking_created"),
        "replay_execution_created": _flag(production_packet, "replay_execution_created"),
        "replay_paper_evidence_required_before_advantage_claim": quantum.get(
            "replay_paper_evidence_required_before_advantage_claim"
        ),
        "replay_results_created": _flag(production_packet, "replay_results_created"),
        "repair_pr76_long_path_fix_present": (root / PR76_SHORT_TEST).exists()
        and not (root / PR76_OLD_LONG_TEST).exists(),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "route_result_id_forbidden_in_this_pr": forbidden.get(
            "route_result_id_forbidden_in_this_pr"
        ),
        "runtime_artifacts_created": runtime.get("runtime_artifacts_created")
        or _flag(production_packet, "runtime_artifacts_created"),
        "runtime_live_use_created": runtime.get("runtime_live_use_created")
        or _flag(production_packet, "runtime_live_use_created"),
        "runtime_resolver_execution_created": runtime.get("runtime_resolver_execution_created")
        or _flag(production_packet, "runtime_resolver_execution_created"),
        "schema_path": _as_posix(schema_path),
        "score_breakdown_forbidden_in_this_pr": forbidden.get(
            "score_breakdown_forbidden_in_this_pr"
        ),
        "scoring_created": _flag(production_packet, "scoring_created"),
        "selected_algorithm_families_forbidden_in_trade_context": forbidden.get(
            "selected_algorithm_families_forbidden_in_trade_context"
        ),
        "selected_parameter_families_forbidden_in_trade_context": forbidden.get(
            "selected_parameter_families_forbidden_in_trade_context"
        ),
        "selected_stack_authority_created": _flag(
            production_packet, "selected_stack_authority_created"
        ),
        "selected_stack_handoff_created": _flag(
            production_packet, "selected_stack_handoff_created"
        ),
        "selected_stack_id_forbidden_in_trade_context": forbidden.get(
            "selected_stack_id_forbidden_in_trade_context"
        ),
        "selection_universe_ids_forbidden_as_output_in_this_pr": forbidden.get(
            "selection_universe_ids_forbidden_as_output_in_this_pr"
        ),
        "selection_universe_registry_created": _flag(
            production_packet, "selection_universe_registry_created"
        ),
        "semantic_task_id": SEMANTIC_TASK_ID,
        "shared_fields_aligned_with_edge_packet": True,
        "source_acceptance_created": source.get("source_acceptance_created")
        or _flag(production_packet, "source_acceptance_created"),
        "source_retrieval_created": source.get("source_retrieval_created")
        or _flag(production_packet, "source_retrieval_created"),
        "stack_selection_created": _flag(production_packet, "stack_selection_created"),
        "strongest_classical_comparator_required_before_quantum_advantage_claim": quantum.get(
            "strongest_classical_comparator_required_before_quantum_advantage_claim"
        ),
        "trade_context_arbitrates_optimizer": context.get(
            "trade_context_arbitrates_optimizer"
        ),
        "trade_context_executes_replay_or_paper": context.get(
            "trade_context_executes_replay_or_paper"
        ),
        "trade_context_executes_runtime_or_live": context.get(
            "trade_context_executes_runtime_or_live"
        ),
        "trade_context_is_static_schema_only": context.get(
            "trade_context_is_static_schema_only"
        ),
        "trade_context_ranks_stack": context.get("trade_context_ranks_stack"),
        "trade_context_routes_selection_universe": context.get(
            "trade_context_routes_selection_universe"
        ),
        "trade_context_scores_stack": context.get("trade_context_scores_stack"),
        "trade_context_selects_stack": context.get("trade_context_selects_stack"),
        "validation_marker": SUCCESS_MARKER,
        "validator": VALIDATOR_NAME,
    }


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_values: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_NAME,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "semantic_task_id": SEMANTIC_TASK_ID,
        "depends_on_pr77_edge_packet_schema": True,
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "repair_pr76_long_path_fix_present": True,
        "all_required_trade_context_fields_present": True,
        "shared_fields_aligned_with_edge_packet": True,
        "qtt_trade_context_packet_schema_ready": True,
        "production_trade_context_evaluated": False,
        "production_trade_context_ready": False,
        "production_routing_evaluated": False,
        "production_routing_ready": False,
        "production_selection_ready": False,
        "final_ready": False,
        "trade_context_is_static_schema_only": True,
        "trade_context_routes_selection_universe": False,
        "trade_context_selects_stack": False,
        "trade_context_scores_stack": False,
        "trade_context_ranks_stack": False,
        "trade_context_arbitrates_optimizer": False,
        "trade_context_executes_replay_or_paper": False,
        "trade_context_executes_runtime_or_live": False,
        "order_intent_type_required": True,
        "order_intent_type_is_static_context_only": True,
        "order_intent_type_creates_order_authority": False,
        "order_intent_type_submits_order": False,
        "order_intent_type_creates_order_receipt": False,
        "order_intent_type_creates_fill_receipt": False,
        "owner_override_satisfies_internal_trade_context_readiness_only": True,
        "owner_override_fabricates_external_fact": False,
        "owner_override_fabricates_accepted_source_packet": False,
        "owner_override_fabricates_connector_semantic": False,
        "owner_override_fabricates_runtime_cash_receipt": False,
        "owner_override_fabricates_order_receipt": False,
        "owner_override_fabricates_replay_paper_result": False,
        "owner_override_fabricates_quantum_backend_execution": False,
        "owner_override_fabricates_profit_evidence": False,
        "quantum_priority_mode_required": True,
        "quantum_priority_mode_static_context_only": True,
        "future_quantum_applicability_registry_required_before_quantum_selection": True,
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": True,
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": True,
        "strongest_classical_comparator_required_before_quantum_advantage_claim": True,
        "fallback_bundle_required_before_quantum_runtime_use": True,
        "replay_paper_evidence_required_before_advantage_claim": True,
        "live_evidence_required_before_profit_claim": True,
        "quantum_backend_evidence_created": False,
        "quantum_advantage_claim_created": False,
        "quantum_selection_created": False,
        "quantum_arbitration_created": False,
        "source_retrieval_created": False,
        "source_acceptance_created": False,
        "accepted_source_packets_created": False,
        "external_fact_value_created": False,
        "market_data_fact_created": False,
        "liquidity_fact_created": False,
        "connector_semantics_created": False,
        "connector_semantic_binding_created": False,
        "connector_semantic_value_created": False,
        "runtime_artifacts_created": False,
        "runtime_resolver_execution_created": False,
        "live_readiness_created": False,
        "runtime_live_use_created": False,
        "private_state_fetch_created": False,
        "order_authority_created": False,
        "cash_receipts_created": False,
        "order_receipts_created": False,
        "fill_receipts_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "replay_results_created": False,
        "paper_results_created": False,
        "profit_evidence_created": False,
        "selected_stack_id_forbidden_in_trade_context": True,
        "selected_parameter_families_forbidden_in_trade_context": True,
        "selected_algorithm_families_forbidden_in_trade_context": True,
        "selection_universe_ids_forbidden_as_output_in_this_pr": True,
        "route_result_id_forbidden_in_this_pr": True,
        "score_breakdown_forbidden_in_this_pr": True,
        "optimizer_arbitration_result_forbidden_in_this_pr": True,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "schema_path": _as_posix(DEFAULT_SCHEMA),
        "production_packet_path": _as_posix(DEFAULT_PRODUCTION_PACKET),
        "fixture_path": _as_posix(DEFAULT_FIXTURE),
        "validation_marker": SUCCESS_MARKER,
    }
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected!r}")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is not deterministic sorted JSON")
    return failures


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate(
    *,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    production_packet_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    failures.extend(validate_pr73_dependency(root))
    failures.extend(validate_pr74_dependency(root))
    failures.extend(validate_pr75_dependency(root))
    edge_schema, edge_packet, pr77_failures = validate_pr77_dependency(root)
    failures.extend(pr77_failures)
    failures.extend(validate_repair_pr76_dependency(root))

    schema, schema_failures = _load_json_checked(root / schema_path, "PR78_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_packet = load_yaml(root / production_packet_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR78_PRODUCTION_PACKET_MALFORMED: {exc}"]),
            report=None,
        )
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR78_FIXTURE_MALFORMED: {exc}"]),
            report=None,
        )

    if schema:
        failures.extend(
            validate_production_packet(
                production_packet,
                schema,
                edge_schema,
                edge_packet,
            )
        )
        failures.extend(validate_fixture_cases(fixture, schema))
    else:
        failures.extend(validate_required_fields(production_packet, "production_packet"))
        failures.extend(validate_required_fields(fixture, "fixture"))

    artifact_texts = (
        (_as_posix(schema_path), _read_text(root / schema_path)),
        (_as_posix(production_packet_path), _read_text(root / production_packet_path)),
        (_as_posix(fixture_path), _read_text(root / fixture_path)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        root=root,
        production_packet=production_packet,
        schema_path=schema_path,
        production_packet_path=production_packet_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        root=root,
        production_packet=production_packet,
        schema_path=schema_path,
        production_packet_path=production_packet_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR78 report is not deterministic")
    failures.extend(validate_no_forbidden_claims((("generated_report", serialize_report(report)),)))
    failures.extend(_report_safety_failures(report))

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--production-packet", default=str(DEFAULT_PRODUCTION_PACKET))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        production_packet_path=pathlib.Path(args.production_packet),
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
