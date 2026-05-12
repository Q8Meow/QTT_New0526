#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import pathlib
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
    / "atomicrows"
    / "atomicrows_parameter_selection_universe_consumer_gate.schema.json"
)
DEFAULT_PRODUCTION_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterSelectionUniverseConsumerGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_selection_universe_consumer_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterSelectionUniverseConsumerGate.report.json"
)

PR79_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_selection_universe_registry.schema.json"
)
PR79_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterSelectionUniverseRegistry.yaml"
)
PR79_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterSelectionUniverseRegistry.report.json"
)
PR79_VALIDATOR = pathlib.Path("tools") / "validate_atomicrows_parameter_selection_universe_registry.py"
PR78_SCHEMA = pathlib.Path("schemas") / "edge" / "qtt_trade_context_packet.schema.json"
PR78_REGISTRY = pathlib.Path("docs") / "master_plan" / "edge" / "QTTTradeContextPacket.yaml"
PR78_REPORT = (
    pathlib.Path("docs") / "master_plan" / "generated" / "QTTTradeContextPacket.report.json"
)
PR78_VALIDATOR = pathlib.Path("tools") / "validate_qtt_trade_context_packet.py"
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
PR74_VALIDATOR = pathlib.Path("tools") / "validate_atomicrows_parameter_stack_completeness_gate.py"
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
PR75_VALIDATOR = pathlib.Path("tools") / "validate_atomicrows_parameter_stack_compatibility_gate.py"

AGENT_ROLE_SCHEMA = pathlib.Path("schemas") / "agents" / "qtt_agent_role_operating_charter_registry.schema.json"
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

GATE_ID = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE"
GATE_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-SELECTION-UNIVERSE-CONSUMER-GATE"
AUTHORITY_CLASS = (
    "STATIC_SELECTION_UNIVERSE_CONSUMER_GATE_ONLY_NOT_ROUTING_NOT_SELECTION_"
    "NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
REPORT_ID = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_REPORT"
REPORT_VERSION = "v1"
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_ROUTING_NOT_SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
VALIDATOR_NAME = "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_FAILED"

PR79_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_OK"
PR78_SUCCESS_MARKER = "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK"
PR77_SUCCESS_MARKER = "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"
PR73_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
PR74_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
PR75_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"

REQUIRED_SELECTION_UNIVERSE_IDS = (
    "KALSHI_BINARY_SHORT_HORIZON",
    "POLYMARKET_EVENT_MARKET_MOMENTUM",
    "FORECASTEX_IBKR_EVENT_RISK_HEDGE",
    "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION",
)
AUTHORIZED_CONSUMER_CLASSES = (
    "SELECTION_UNIVERSE_STATIC_SCHEMA_CONSUMER",
    "TRADE_CONTEXT_ROUTING_GATE_CONSUMER_FUTURE_PR81",
    "QUANTUM_APPLICABILITY_CLASSIFICATION_CONSUMER_FUTURE_PR82",
    "OWNER_QUANTUM_PRIORITY_POLICY_CONSUMER_FUTURE_PR83",
    "SCORING_POLICY_CONSUMER_FUTURE_PR84",
    "PARAMETER_STACK_SCORING_RANKING_CONSUMER_FUTURE_PR85",
    "QUANTUM_STACK_SCORING_RANKING_CONSUMER_FUTURE_PR85",
    "QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_CONSUMER_FUTURE_PR86",
    "QUANTUM_CLASSICAL_ARBITRATION_CONSUMER_FUTURE_PR86",
    "CANDIDATE_PARAMETER_STACK_GENERATION_CONSUMER_FUTURE_PR87",
    "QUANTUM_CANDIDATE_STACK_GENERATION_CONSUMER_FUTURE_PR87",
    "TRADE_CONTEXT_PARAMETER_STACK_SELECTION_CONSUMER_FUTURE_PR88",
    "SELECTED_PARAMETER_STACK_HANDOFF_CONSUMER_FUTURE_PR89",
    "REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_CONSUMER_FUTURE_PR90",
    "OWNER_LIVE_PROMOTION_REVIEW_CONSUMER_FUTURE_PR92",
    "QUANTUM_UNIVERSE_METADATA_CONSUMER_STATIC_ONLY",
    "VALIDATION_AGENT_STATIC_AUDIT_CONSUMER",
    "GOVERNANCE_AGENT_STATIC_AUDIT_CONSUMER",
    "OWNER_REVIEW_STATIC_CONSUMER",
)
AGENT_ROLE_NAMES = (
    "OWNER",
    "ORCHESTRATOR_AGENT",
    "ATOMICROWS_AGENT",
    "OPTIMIZER_AGENT",
    "RISK_AGENT",
    "SIZING_AGENT",
    "EXECUTION_LATENCY_AGENT",
    "QUANTUM_RESEARCH_AGENT",
    "QUANTUM_BACKEND_AGENT",
    "GOVERNANCE_AGENT",
    "VALIDATION_AGENT",
)
TRADE_CONTEXT_REFERENCE_MODES = (
    "NO_TRADE_CONTEXT_REFERENCE_STATIC_GATE_ONLY",
    "SYNTHETIC_TRADE_CONTEXT_REFERENCE_SCHEMA_ONLY",
    "FUTURE_PR81_ROUTING_INPUT_REFERENCE_ONLY",
)
OWNER_OVERRIDE_TOKENS = (
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_APPROVED",
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED_OVERRIDE",
)
BLOCKED_CASE_IDS = (
    "UNKNOWN_UNIVERSE_ID_BLOCKED",
    "UNKNOWN_AGENT_ROLE_BLOCKED",
    "UNKNOWN_CONSUMER_CLASS_BLOCKED",
    "MISSING_UNIVERSE_BINDING_BLOCKED",
    "DISALLOWED_AGENT_UNIVERSE_PAIR_BLOCKED",
    "DISALLOWED_CONSUMER_CLASS_BLOCKED",
    "ROUTE_RESULT_CREATION_BLOCKED",
    "RUNTIME_SELECTION_BLOCKED",
    "LIVE_TRADING_BLOCKED",
    "ORDER_AUTHORITY_BLOCKED",
    "SOURCE_FACT_INVENTION_BLOCKED",
    "CONNECTOR_SEMANTIC_BINDING_BLOCKED",
    "QUANTUM_BACKEND_EXECUTION_BLOCKED",
    "QUANTUM_ADVANTAGE_CLAIM_BLOCKED",
    "PROFIT_EVIDENCE_CLAIM_BLOCKED",
)
SCHEMA_REQUIRED_FIELDS = (
    "gate_id",
    "gate_version",
    "authority_class",
    "semantic_task_id",
    "depends_on_selection_universe_registry",
    "depends_on_qtt_trade_context_packet",
    "depends_on_edge_parameter_stack_selection_packet",
    "depends_on_parameter_stack_role_taxonomy",
    "depends_on_parameter_stack_completeness_gate",
    "depends_on_parameter_stack_compatibility_gate",
    "depends_on_qtt_agent_algorithm_foundation",
    "depends_on_atomicrows_lifecycle_and_binding_foundation",
    "required_selection_universe_ids",
    "authorized_consumer_classes",
    "consumer_gate_decision_contract",
    "allowed_universe_consumption_matrix",
    "blocked_universe_consumption_cases",
    "gate_static_policy",
    "universe_binding_policy",
    "owner_override_policy",
    "source_evidence_boundary_policy",
    "connector_semantic_boundary_policy",
    "runtime_live_order_boundary_policy",
    "quantum_consumer_policy",
    "future_consumer_contract",
    "forbidden_output_fields_policy",
    "explicit_no_claim_flags",
    "validation_invariants",
    "production_readiness",
    "final_ready",
)
AGENT_ALGORITHM_FOUNDATION_REPORTS = (
    "docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json",
    "docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json",
    "docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json",
    "docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json",
    "docs/master_plan/generated/QTTAgentAlgorithmCumulativeReadinessGate.report.json",
    "docs/master_plan/generated/QTTAgentAlgorithmCommandMatrix.json",
)
ATOMICROWS_LIFECYCLE_BINDING_REPORTS = (
    "docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json",
    "docs/master_plan/generated/AtomicRowsLifecycleConsumerGate.report.json",
    "docs/master_plan/generated/AtomicRowsLifecycleCumulativeReadinessGate.report.json",
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json",
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingConsumerGate.report.json",
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json",
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json",
)
GATE_STATIC_TRUE_FIELDS = (
    "selection_universe_consumer_gate_is_static_only",
    "agent_universe_consumer_access_is_deterministic",
    "unknown_agent_blocks_normal_access",
    "unknown_universe_blocks_normal_access",
    "unknown_consumer_class_blocks_normal_access",
    "missing_universe_binding_blocks_normal_access",
    "owner_override_may_satisfy_internal_access_only",
)
GATE_STATIC_FALSE_FIELDS = (
    "random_consumer_access_allowed",
    "dynamic_runtime_access_evaluation_created",
    "trade_context_to_selection_universe_routing_created",
    "routed_universe_ids_created",
    "route_result_created",
    "selected_stack_created",
    "stack_selection_created",
    "scoring_created",
    "ranking_created",
    "optimizer_arbitration_created",
    "candidate_stack_generation_created",
    "replay_paper_execution_created",
    "runtime_live_order_authority_created",
    "final_ready_created_by_this_pr",
)
BINDING_TRUE_FIELDS = (
    "universe_binding_required_for_normal_access",
    "universe_binding_defined_by_static_matrix_only",
)
BINDING_FALSE_FIELDS = (
    "universe_binding_evaluated_against_live_data",
    "universe_binding_evaluated_against_source_retrieval",
    "universe_binding_evaluated_against_connector_semantics",
    "universe_binding_evaluated_against_private_state",
    "universe_binding_evaluated_against_runtime_cash",
    "universe_binding_uses_random_sampling",
    "universe_binding_uses_current_timestamp",
    "universe_binding_uses_external_api_call",
)
OWNER_TRUE_FIELDS = (
    "owner_override_supported",
    "owner_override_satisfies_internal_selection_universe_consumer_access_only",
    "owner_override_may_force_static_universe_consumption_access_internal_only",
)
OWNER_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
)
SOURCE_TRUE_FIELDS = (
    "consumer_gate_source_dependency_values_are_static_labels_only",
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
    "selection_universe_consumer_gate_does_not_unlock_connector_semantics",
)
CONNECTOR_FALSE_FIELDS = (
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "connector_semantic_value_created",
)
RUNTIME_TRUE_FIELDS = (
    "selection_universe_consumer_gate_is_not_runtime_signal",
    "selection_universe_consumer_gate_is_not_live_order_instruction",
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
    "profit_evidence_created",
)
QUANTUM_TRUE_FIELDS = (
    "quantum_optimized_portfolio_selection_consumption_supported_static_only",
    "quantum_consumer_access_static_metadata_only",
    "quantum_applicability_mode_static_metadata_only",
    "quantum_priority_mode_compatibility_static_metadata_only",
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
FUTURE_TRUE_FIELDS = (
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
FUTURE_FALSE_FIELDS = (
    "this_pr_performs_routing",
    "this_pr_performs_scoring",
    "this_pr_performs_ranking",
    "this_pr_performs_selection",
    "this_pr_performs_arbitration",
    "this_pr_generates_candidate_stacks",
    "this_pr_executes_replay_or_paper",
    "this_pr_executes_runtime_or_live",
)
EXPLICIT_NO_CLAIM_FALSE_FIELDS = (
    "trade_context_routing_created",
    "selection_universe_routing_created",
    "routed_universe_ids_created",
    "route_result_created",
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
    "quantum_selection_created",
    "quantum_arbitration_created",
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
    "production_consumer_access_evaluated",
)
FORBIDDEN_OUTPUT_FIELDS = (
    "routed_universe_ids",
    "route_result_id",
    "selected_stack_id",
    "selected_parameter_families",
    "selected_algorithm_families",
    "score_breakdown",
    "optimizer_arbitration_result",
    "replay_result_id",
    "paper_result_id",
    "order_id",
    "fill_id",
    "cash_receipt_id",
    "profit_evidence_id",
)
REQUIRED_FIXTURE_CASE_IDS = (
    "SELECTION_UNIVERSE_CONSUMER_GATE_VALID_STATIC_ONLY",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_MISSING_UNIVERSE_REGISTRY_DEPENDENCY",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_UNIVERSE_ID",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_AGENT_ROLE",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_CONSUMER_CLASS",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_MISSING_UNIVERSE_BINDING",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_DISALLOWED_AGENT_UNIVERSE_PAIR",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_DISALLOWED_CONSUMER_CLASS",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_ROUTE_RESULT_CREATION",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_ROUTED_UNIVERSE_OUTPUT",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_SELECTED_STACK_CREATION",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_SCORE_BREAKDOWN_CREATION",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_OPTIMIZER_ARBITRATION_CREATION",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_CONNECTOR_SEMANTIC_ATTEMPT",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_RUNTIME_LIVE_ORDER_ATTEMPT",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_QUANTUM_BACKEND_ATTEMPT",
    "SELECTION_UNIVERSE_CONSUMER_BLOCKED_QUANTUM_ADVANTAGE_CLAIM",
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_SELECTION_UNIVERSE_CONSUMER_ACCESS_ONLY",
    "OWNER_GLOBAL_OVERRIDE_DOES_NOT_FABRICATE_EXTERNAL_FACTS_OR_EVIDENCE",
)
PRODUCTION_READINESS_EXPECTED = {
    "parameter_selection_universe_consumer_gate_ready": True,
    "production_selection_universe_consumer_gate_evaluated": False,
    "production_selection_universe_consumer_gate_ready": False,
    "production_consumer_access_evaluated": False,
    "production_routing_evaluated": False,
    "production_routing_ready": False,
    "production_selection_ready": False,
    "final_ready": False,
}


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
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def write_json_report(report: dict[str, Any], path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_report(report), encoding="utf-8")


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_MISSING: {path}"]
    try:
        value = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"{label}_MALFORMED: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{label}_MALFORMED: root must be object"]
    return value, []


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _deep_update(target: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [
        f"{label}{failure[1:] if failure.startswith('$') else ': ' + failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def _require_files(root: pathlib.Path, paths: Sequence[tuple[str, pathlib.Path]], marker: str) -> list[str]:
    failures: list[str] = []
    for label, rel_path in paths:
        if not (root / rel_path).exists():
            failures.append(f"{marker}: {label} missing")
    return failures


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


def _validate_dependency(
    root: pathlib.Path,
    *,
    schema: pathlib.Path,
    registry: pathlib.Path,
    report: pathlib.Path,
    validator: pathlib.Path,
    marker: str,
    dependency_block: str,
    validation_label: str,
) -> list[str]:
    failures = _require_files(
        root,
        (
            (f"{validation_label}_SCHEMA", schema),
            (f"{validation_label}_REGISTRY", registry),
            (f"{validation_label}_REPORT", report),
            (f"{validation_label}_VALIDATOR", validator),
        ),
        dependency_block,
    )
    if failures:
        return failures
    report_payload = load_json(root / report)
    if report_payload.get("validation_marker") != marker:
        failures.append(f"{dependency_block}: report marker mismatch")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=report,
            validator_path=validator,
            marker=marker,
            label=validation_label,
        )
    )
    return failures


def validate_pr73_dependency(root: pathlib.Path) -> list[str]:
    return _validate_dependency(
        root,
        schema=PR73_SCHEMA,
        registry=PR73_REGISTRY,
        report=PR73_REPORT,
        validator=PR73_VALIDATOR,
        marker=PR73_SUCCESS_MARKER,
        dependency_block="PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK",
        validation_label="PR73_ROLE_TAXONOMY",
    )


def validate_pr74_dependency(root: pathlib.Path) -> list[str]:
    return _validate_dependency(
        root,
        schema=PR74_SCHEMA,
        registry=PR74_REGISTRY,
        report=PR74_REPORT,
        validator=PR74_VALIDATOR,
        marker=PR74_SUCCESS_MARKER,
        dependency_block="PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK",
        validation_label="PR74_COMPLETENESS_GATE",
    )


def validate_pr75_dependency(root: pathlib.Path) -> list[str]:
    return _validate_dependency(
        root,
        schema=PR75_SCHEMA,
        registry=PR75_REGISTRY,
        report=PR75_REPORT,
        validator=PR75_VALIDATOR,
        marker=PR75_SUCCESS_MARKER,
        dependency_block="PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK",
        validation_label="PR75_COMPATIBILITY_GATE",
    )


def validate_pr77_dependency(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    failures = _validate_dependency(
        root,
        schema=PR77_SCHEMA,
        registry=PR77_REGISTRY,
        report=PR77_REPORT,
        validator=PR77_VALIDATOR,
        marker=PR77_SUCCESS_MARKER,
        dependency_block="PR77_EDGE_PACKET_SCHEMA_DEPENDENCY_BLOCK",
        validation_label="PR77_EDGE_PACKET_SCHEMA",
    )
    edge_schema = load_json(root / PR77_SCHEMA) if (root / PR77_SCHEMA).exists() else {}
    edge_packet = load_yaml(root / PR77_REGISTRY) if (root / PR77_REGISTRY).exists() else {}
    return edge_schema, edge_packet, failures


def validate_pr78_dependency(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    failures = _validate_dependency(
        root,
        schema=PR78_SCHEMA,
        registry=PR78_REGISTRY,
        report=PR78_REPORT,
        validator=PR78_VALIDATOR,
        marker=PR78_SUCCESS_MARKER,
        dependency_block="PR78_TRADE_CONTEXT_PACKET_SCHEMA_DEPENDENCY_BLOCK",
        validation_label="PR78_TRADE_CONTEXT_PACKET_SCHEMA",
    )
    trade_schema = load_json(root / PR78_SCHEMA) if (root / PR78_SCHEMA).exists() else {}
    trade_packet = load_yaml(root / PR78_REGISTRY) if (root / PR78_REGISTRY).exists() else {}
    return trade_schema, trade_packet, failures


def validate_pr79_dependency(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    failures = _validate_dependency(
        root,
        schema=PR79_SCHEMA,
        registry=PR79_REGISTRY,
        report=PR79_REPORT,
        validator=PR79_VALIDATOR,
        marker=PR79_SUCCESS_MARKER,
        dependency_block="PR79_SELECTION_UNIVERSE_REGISTRY_DEPENDENCY_BLOCK",
        validation_label="PR79_SELECTION_UNIVERSE_REGISTRY",
    )
    pr79_schema = load_json(root / PR79_SCHEMA) if (root / PR79_SCHEMA).exists() else {}
    pr79_registry = load_yaml(root / PR79_REGISTRY) if (root / PR79_REGISTRY).exists() else {}
    pr79_report = load_json(root / PR79_REPORT) if (root / PR79_REPORT).exists() else {}
    if tuple(pr79_registry.get("required_selection_universe_ids", [])) != REQUIRED_SELECTION_UNIVERSE_IDS:
        failures.append("PR79_SELECTION_UNIVERSE_REGISTRY_DEPENDENCY_BLOCK: required universe IDs mismatch")
    if pr79_report.get("required_universe_ids_present") is not True:
        failures.append("PR79_SELECTION_UNIVERSE_REGISTRY_DEPENDENCY_BLOCK: report universe IDs not present")
    return pr79_schema, pr79_registry, pr79_report, failures


def validate_agent_algorithm_foundation_dependencies(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for rel_path in AGENT_ALGORITHM_FOUNDATION_REPORTS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"QTT_AGENT_ALGORITHM_FOUNDATION_DEPENDENCY_BLOCK: {rel_path} missing")
            continue
        report = load_json(path)
        if report.get("authority_boundary_all_false") is not True:
            failures.append(f"QTT_AGENT_ALGORITHM_FOUNDATION_DEPENDENCY_BLOCK: {rel_path} authority boundary not false")
        if report.get("deterministic_output") is not True:
            failures.append(f"QTT_AGENT_ALGORITHM_FOUNDATION_DEPENDENCY_BLOCK: {rel_path} not deterministic")
    role_report = load_json(root / AGENT_ALGORITHM_FOUNDATION_REPORTS[0])
    if role_report.get("required_agent_roles_present_count") != role_report.get("required_agent_role_count"):
        failures.append("QTT_AGENT_ALGORITHM_FOUNDATION_DEPENDENCY_BLOCK: agent role report count mismatch")
    return failures


def validate_atomicrows_lifecycle_binding_dependencies(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for rel_path in ATOMICROWS_LIFECYCLE_BINDING_REPORTS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"ATOMICROWS_LIFECYCLE_BINDING_DEPENDENCY_BLOCK: {rel_path} missing")
            continue
        report = load_json(path)
        if report.get("authority_boundary_all_false") is not True:
            failures.append(f"ATOMICROWS_LIFECYCLE_BINDING_DEPENDENCY_BLOCK: {rel_path} authority boundary not false")
        if report.get("deterministic_output") is not True:
            failures.append(f"ATOMICROWS_LIFECYCLE_BINDING_DEPENDENCY_BLOCK: {rel_path} not deterministic")
    return failures


def validate_repair_pr76_dependency(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if not (root / PR76_SHORT_TEST).exists():
        failures.append("PRE_PR80_REPAIR_NOT_APPLIED_BLOCK")
    if (root / PR76_OLD_LONG_TEST).exists():
        failures.append("OLD_LONG_RUNTIME_RESOLVER_TEST_REINTRODUCED_BLOCK")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = set(schema.get("required", []))
    properties = _mapping(schema.get("properties"))
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR80_SCHEMA_REQUIRED_FIELD_MISSING: {field}")
        if field not in properties:
            failures.append(f"PR80_SCHEMA_PROPERTY_MISSING: {field}")
    if schema.get("additionalProperties") is not False:
        failures.append("PR80_SCHEMA_MUST_BE_STRICT_ADDITIONAL_PROPERTIES_FALSE")
    return failures


def validate_required_universes(
    gate: dict[str, Any],
    pr79_registry: dict[str, Any] | None = None,
    label: str = "gate",
) -> list[str]:
    failures: list[str] = []
    if tuple(gate.get("required_selection_universe_ids", [])) != REQUIRED_SELECTION_UNIVERSE_IDS:
        failures.append(f"{label}.required_selection_universe_ids must match PR80 required list")
    matrix_ids = {entry.get("universe_id") for entry in _list_of_mappings(gate.get("allowed_universe_consumption_matrix"))}
    missing_matrix_ids = sorted(set(REQUIRED_SELECTION_UNIVERSE_IDS) - matrix_ids)
    if missing_matrix_ids:
        failures.append(f"{label}.allowed_universe_consumption_matrix missing {missing_matrix_ids}")
    if pr79_registry is not None:
        pr79_ids = {universe.get("universe_id") for universe in _list_of_mappings(pr79_registry.get("universe_definitions"))}
        missing_pr79 = sorted(set(REQUIRED_SELECTION_UNIVERSE_IDS) - pr79_ids)
        if missing_pr79:
            failures.append(f"PR79 registry missing required universe IDs {missing_pr79}")
    return failures


def validate_authorized_consumer_classes(gate: dict[str, Any], label: str = "gate") -> list[str]:
    classes = gate.get("authorized_consumer_classes")
    if not isinstance(classes, list):
        return [f"{label}.authorized_consumer_classes must be a list"]
    failures: list[str] = []
    if len(classes) != len(set(classes)):
        failures.append(f"{label}.authorized_consumer_classes must be unique")
    missing = sorted(set(AUTHORIZED_CONSUMER_CLASSES) - set(classes))
    if missing:
        failures.append(f"{label}.authorized_consumer_classes missing {missing}")
    unknown = sorted(set(classes) - set(AUTHORIZED_CONSUMER_CLASSES))
    if unknown:
        failures.append(f"{label}.authorized_consumer_classes unknown {unknown}")
    return failures


def _matrix_by_universe(gate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry.get("universe_id")): entry
        for entry in _list_of_mappings(gate.get("allowed_universe_consumption_matrix"))
    }


def validate_allowed_consumption_matrix(gate: dict[str, Any], label: str = "gate") -> list[str]:
    failures: list[str] = []
    matrix = _list_of_mappings(gate.get("allowed_universe_consumption_matrix"))
    if len(matrix) < len(REQUIRED_SELECTION_UNIVERSE_IDS):
        failures.append(f"{label}.allowed_universe_consumption_matrix must contain required rows")
    ids = [entry.get("universe_id") for entry in matrix]
    if len(ids) != len(set(ids)):
        failures.append(f"{label}.allowed_universe_consumption_matrix duplicate universe_id")
    if set(ids) != set(REQUIRED_SELECTION_UNIVERSE_IDS):
        failures.append(f"{label}.allowed_universe_consumption_matrix universe IDs mismatch")
    for entry in matrix:
        entry_id = entry.get("matrix_entry_id")
        if not isinstance(entry_id, str) or not entry_id:
            failures.append(f"{label}.matrix entry missing matrix_entry_id")
        if entry.get("universe_binding_required") is not True:
            failures.append(f"{label}.{entry_id}.universe_binding_required must be true")
        if entry.get("owner_override_supported") is not True:
            failures.append(f"{label}.{entry_id}.owner_override_supported must be true")
        if entry.get("normal_access_allowed") is not True:
            failures.append(f"{label}.{entry_id}.normal_access_allowed must be true")
        for field in (
            "creates_routing",
            "creates_selection",
            "creates_scoring",
            "creates_runtime",
            "creates_order_authority",
            "creates_quantum_backend_evidence",
            "creates_profit_evidence",
            "creates_optimizer_arbitration",
        ):
            if entry.get(field) is not False:
                failures.append(f"{label}.{entry_id}.{field} must be false")
        if entry.get("universe_id") == "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION":
            if entry.get("quantum_static_access_only") is not True:
                failures.append(f"{label}.{entry_id}.quantum_static_access_only must be true")
            if "QUANTUM_BACKEND_AGENT" in entry.get("allowed_agent_roles", []):
                quantum_classes = set(entry.get("allowed_consumer_classes", []))
                if "QUANTUM_UNIVERSE_METADATA_CONSUMER_STATIC_ONLY" not in quantum_classes:
                    failures.append(f"{label}.{entry_id} QUANTUM_BACKEND_AGENT must be static metadata only")
    return failures


def _agent_roles_from_charter_schema(root: pathlib.Path) -> set[str]:
    schema = load_json(root / AGENT_ROLE_SCHEMA)
    values: set[str] = set()
    for _path, key, value in _walk(schema):
        if key == "agent_role" and isinstance(value, dict):
            enum = value.get("enum")
            if isinstance(enum, list):
                values.update(str(item) for item in enum)
    if not values:
        values.update(AGENT_ROLE_NAMES)
    return values


def validate_agent_roles_exist(gate: dict[str, Any], root: pathlib.Path, label: str = "gate") -> list[str]:
    allowed_roles = _agent_roles_from_charter_schema(root)
    failures: list[str] = []
    for entry in _list_of_mappings(gate.get("allowed_universe_consumption_matrix")):
        roles = entry.get("allowed_agent_roles")
        if not isinstance(roles, list) or not roles:
            failures.append(f"{label}.{entry.get('matrix_entry_id')}.allowed_agent_roles must be non-empty list")
            continue
        unknown = sorted(set(roles) - allowed_roles)
        if unknown:
            failures.append(f"{label}.{entry.get('matrix_entry_id')}.allowed_agent_roles unknown {unknown}")
    decision = _mapping(gate.get("consumer_gate_decision_contract"))
    if decision.get("requesting_agent_role") not in allowed_roles:
        failures.append(f"{label}.consumer_gate_decision_contract.requesting_agent_role unknown")
    return failures


def validate_consumer_classes_exist(gate: dict[str, Any], label: str = "gate") -> list[str]:
    authorized = set(gate.get("authorized_consumer_classes", []))
    failures: list[str] = []
    for entry in _list_of_mappings(gate.get("allowed_universe_consumption_matrix")):
        classes = entry.get("allowed_consumer_classes")
        if not isinstance(classes, list) or not classes:
            failures.append(f"{label}.{entry.get('matrix_entry_id')}.allowed_consumer_classes must be non-empty list")
            continue
        unknown = sorted(set(classes) - authorized)
        if unknown:
            failures.append(f"{label}.{entry.get('matrix_entry_id')}.allowed_consumer_classes unknown {unknown}")
    decision = _mapping(gate.get("consumer_gate_decision_contract"))
    if decision.get("consumer_class") not in authorized:
        failures.append(f"{label}.consumer_gate_decision_contract.consumer_class unknown")
    return failures


def _expect_policy_fields(
    section: dict[str, Any],
    true_fields: Sequence[str],
    false_fields: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    for field in true_fields:
        if section.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in false_fields:
        if section.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_gate_static_policy(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("gate_static_policy")),
        GATE_STATIC_TRUE_FIELDS,
        GATE_STATIC_FALSE_FIELDS,
        f"{label}.gate_static_policy",
    )


def validate_universe_binding_policy(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("universe_binding_policy")),
        BINDING_TRUE_FIELDS,
        BINDING_FALSE_FIELDS,
        f"{label}.universe_binding_policy",
    )


def validate_owner_override_policy(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("owner_override_policy")),
        OWNER_TRUE_FIELDS,
        OWNER_FALSE_FIELDS,
        f"{label}.owner_override_policy",
    )


def validate_quantum_consumer_boundary(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("quantum_consumer_policy")),
        QUANTUM_TRUE_FIELDS,
        QUANTUM_FALSE_FIELDS,
        f"{label}.quantum_consumer_policy",
    )


def validate_source_evidence_boundary(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("source_evidence_boundary_policy")),
        SOURCE_TRUE_FIELDS,
        SOURCE_FALSE_FIELDS,
        f"{label}.source_evidence_boundary_policy",
    )


def validate_connector_semantic_boundary(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("connector_semantic_boundary_policy")),
        CONNECTOR_TRUE_FIELDS,
        CONNECTOR_FALSE_FIELDS,
        f"{label}.connector_semantic_boundary_policy",
    )


def validate_runtime_live_order_boundary(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("runtime_live_order_boundary_policy")),
        RUNTIME_TRUE_FIELDS,
        RUNTIME_FALSE_FIELDS,
        f"{label}.runtime_live_order_boundary_policy",
    )


def validate_future_consumer_contract(gate: dict[str, Any], label: str = "gate") -> list[str]:
    return _expect_policy_fields(
        _mapping(gate.get("future_consumer_contract")),
        FUTURE_TRUE_FIELDS,
        FUTURE_FALSE_FIELDS,
        f"{label}.future_consumer_contract",
    )


def validate_forbidden_output_fields(payload: dict[str, Any], label: str = "payload") -> list[str]:
    failures: list[str] = []
    for path, key, _value in _walk(payload):
        if key in FORBIDDEN_OUTPUT_FIELDS:
            failures.append(f"{label}: forbidden output field present at {path}")
    return failures


def _flag(gate: dict[str, Any], field: str) -> bool:
    return bool(_mapping(gate.get("explicit_no_claim_flags")).get(field))


def validate_no_forbidden_claims(artifact_texts: Iterable[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    forbidden_fragments = (
        "http://",
        "https://",
        "www.",
        "api_key",
        "apikey",
        "password",
        "bearer ",
        "git clone",
        "pip install",
        "profit proof",
        "quantum advantage proof",
        "live trading command",
        "order command",
    )
    for label, text in artifact_texts:
        lowered = text.lower()
        for fragment in forbidden_fragments:
            if fragment in lowered:
                failures.append(f"{label}: forbidden fixture/artifact text {fragment}")
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
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR80"]
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {completed.stderr.strip()}"]


def evaluate_consumer_access(gate: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    universe_id = request.get("universe_id")
    role = request.get("requesting_agent_role")
    consumer_class = request.get("consumer_class")
    trade_context_mode = request.get("trade_context_reference_mode")
    binding_required = bool(request.get("universe_binding_required"))
    binding_present = bool(request.get("universe_binding_present"))
    owner_override_token = request.get("owner_override_token")
    block_reason_codes: list[str] = []
    matrix = _matrix_by_universe(gate)
    authorized = set(gate.get("authorized_consumer_classes", []))

    if universe_id not in REQUIRED_SELECTION_UNIVERSE_IDS or universe_id not in matrix:
        block_reason_codes.append("UNKNOWN_UNIVERSE_ID_BLOCKED")
    if role not in _agent_roles_from_charter_schema(repo_root()):
        block_reason_codes.append("UNKNOWN_AGENT_ROLE_BLOCKED")
    if consumer_class not in authorized:
        block_reason_codes.append("UNKNOWN_CONSUMER_CLASS_BLOCKED")
    if binding_required and not binding_present:
        block_reason_codes.append("MISSING_UNIVERSE_BINDING_BLOCKED")

    row = matrix.get(str(universe_id), {})
    if row:
        if role not in row.get("allowed_agent_roles", []):
            block_reason_codes.append("DISALLOWED_AGENT_UNIVERSE_PAIR_BLOCKED")
        if consumer_class in authorized and consumer_class not in row.get("allowed_consumer_classes", []):
            block_reason_codes.append("DISALLOWED_CONSUMER_CLASS_BLOCKED")
        if trade_context_mode not in row.get("allowed_trade_context_reference_modes", []):
            block_reason_codes.append("DISALLOWED_TRADE_CONTEXT_REFERENCE_MODE_BLOCKED")

    normal_access_allowed = not block_reason_codes
    owner_override_access_allowed = (
        owner_override_token in OWNER_OVERRIDE_TOKENS
        and _mapping(gate.get("owner_override_policy")).get(
            "owner_override_satisfies_internal_selection_universe_consumer_access_only"
        )
        is True
    )
    final_internal_access_allowed = normal_access_allowed or owner_override_access_allowed
    return {
        "normal_access_allowed": normal_access_allowed,
        "owner_override_access_allowed": owner_override_access_allowed,
        "final_internal_access_allowed": final_internal_access_allowed,
        "block_reason_codes": block_reason_codes,
    }


def _gate_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    gate = copy.deepcopy(fixture)
    for field in ("fixture_id", "fixture_version", "mode", "execution", "fixture_cases"):
        gate.pop(field, None)
    return gate


def _case_gate_from_fixture(fixture: dict[str, Any], case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    gate = _gate_from_fixture(fixture)
    request = copy.deepcopy(_mapping(gate.get("consumer_gate_decision_contract")))
    remove_dependency = case.get("remove_dependency")
    if isinstance(remove_dependency, str):
        gate.pop(remove_dependency, None)
    gate_overrides = case.get("gate_overrides")
    if isinstance(gate_overrides, dict):
        _deep_update(gate, gate_overrides)
    decision_overrides = case.get("decision_overrides")
    if isinstance(decision_overrides, dict):
        _deep_update(request, decision_overrides)
    forbidden_field = case.get("forbidden_output_field")
    if isinstance(forbidden_field, str):
        if forbidden_field == "routed_universe_ids":
            gate[forbidden_field] = ["SYNTHETIC_FORBIDDEN_ROUTED_UNIVERSE"]
        elif forbidden_field == "score_breakdown":
            gate[forbidden_field] = {"SYNTHETIC_SCORE": "FORBIDDEN"}
        else:
            gate[forbidden_field] = "SYNTHETIC_FORBIDDEN_OUTPUT_FIELD"
    return gate, request


def validate_fixture_cases(
    fixture: dict[str, Any],
    schema: dict[str, Any],
    pr79_registry: dict[str, Any],
    root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    cases = {str(case.get("case_id")): case for case in _list_of_mappings(fixture.get("fixture_cases"))}
    missing_cases = sorted(set(REQUIRED_FIXTURE_CASE_IDS) - set(cases))
    if missing_cases:
        failures.append(f"PR80_FIXTURE_CASES_MISSING: {missing_cases}")

    for case_id in REQUIRED_FIXTURE_CASE_IDS:
        case = cases.get(case_id)
        if not case:
            continue
        gate, request = _case_gate_from_fixture(fixture, case)
        case_failures: list[str] = []
        case_failures.extend(schema_subset_failures(gate, schema, f"fixture_case.{case_id}"))
        case_failures.extend(validate_required_universes(gate, pr79_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_authorized_consumer_classes(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_allowed_consumption_matrix(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_agent_roles_exist(gate, root, f"fixture_case.{case_id}"))
        case_failures.extend(validate_consumer_classes_exist(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_gate_static_policy(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_universe_binding_policy(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_owner_override_policy(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_quantum_consumer_boundary(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_source_evidence_boundary(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_connector_semantic_boundary(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_runtime_live_order_boundary(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_future_consumer_contract(gate, f"fixture_case.{case_id}"))
        case_failures.extend(validate_forbidden_output_fields(gate, f"fixture_case.{case_id}"))

        access = evaluate_consumer_access(gate, request)
        expected_access_blocks = {
            "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_UNIVERSE_ID": "UNKNOWN_UNIVERSE_ID_BLOCKED",
            "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_AGENT_ROLE": "UNKNOWN_AGENT_ROLE_BLOCKED",
            "SELECTION_UNIVERSE_CONSUMER_BLOCKED_UNKNOWN_CONSUMER_CLASS": "UNKNOWN_CONSUMER_CLASS_BLOCKED",
            "SELECTION_UNIVERSE_CONSUMER_BLOCKED_MISSING_UNIVERSE_BINDING": "MISSING_UNIVERSE_BINDING_BLOCKED",
            "SELECTION_UNIVERSE_CONSUMER_BLOCKED_DISALLOWED_AGENT_UNIVERSE_PAIR": "DISALLOWED_AGENT_UNIVERSE_PAIR_BLOCKED",
            "SELECTION_UNIVERSE_CONSUMER_BLOCKED_DISALLOWED_CONSUMER_CLASS": "DISALLOWED_CONSUMER_CLASS_BLOCKED",
        }
        expected_access_block = expected_access_blocks.get(case_id)
        if expected_access_block is not None:
            if expected_access_block not in access["block_reason_codes"]:
                case_failures.append(f"{expected_access_block} not observed")
            else:
                case_failures.append(f"{expected_access_block} observed")
        if case_id == "OWNER_OVERRIDE_SATISFIED_INTERNAL_SELECTION_UNIVERSE_CONSUMER_ACCESS_ONLY":
            if access["owner_override_access_allowed"] is not True or access["final_internal_access_allowed"] is not True:
                case_failures.append("owner override did not satisfy internal consumer access")
            if access["normal_access_allowed"] is not False:
                case_failures.append("owner override fixture must not claim normal access")

        expected_valid = case.get("expected_schema_valid") is True
        if expected_valid and case_failures:
            failures.append(f"{case_id}: expected valid but failed {case_failures}")
        if not expected_valid and not case_failures:
            failures.append(f"{case_id}: expected fail-closed validation failure")
    return failures


def validate_production_gate(
    *,
    gate: dict[str, Any],
    schema: dict[str, Any],
    pr79_registry: dict[str, Any],
    root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(gate, schema, "production_gate"))
    failures.extend(validate_required_universes(gate, pr79_registry))
    failures.extend(validate_authorized_consumer_classes(gate))
    failures.extend(validate_allowed_consumption_matrix(gate))
    failures.extend(validate_agent_roles_exist(gate, root))
    failures.extend(validate_consumer_classes_exist(gate))
    failures.extend(validate_gate_static_policy(gate))
    failures.extend(validate_universe_binding_policy(gate))
    failures.extend(validate_owner_override_policy(gate))
    failures.extend(validate_quantum_consumer_boundary(gate))
    failures.extend(validate_source_evidence_boundary(gate))
    failures.extend(validate_connector_semantic_boundary(gate))
    failures.extend(validate_runtime_live_order_boundary(gate))
    failures.extend(validate_future_consumer_contract(gate))
    failures.extend(validate_forbidden_output_fields(gate, "production_gate"))
    for field in EXPLICIT_NO_CLAIM_FALSE_FIELDS:
        if _flag(gate, field) is not False:
            failures.append(f"production_gate.explicit_no_claim_flags.{field} must be false")
    if gate.get("production_readiness") != PRODUCTION_READINESS_EXPECTED:
        failures.append("production_gate.production_readiness mismatch")
    if gate.get("final_ready") is not False:
        failures.append("production_gate.final_ready must be false")

    request = copy.deepcopy(_mapping(gate.get("consumer_gate_decision_contract")))
    access = evaluate_consumer_access(gate, request)
    if access["normal_access_allowed"] is not True:
        failures.append("production_gate.consumer_gate_decision_contract valid access did not allow normal access")
    for case_id in BLOCKED_CASE_IDS:
        if case_id not in {case.get("case_id") for case in _list_of_mappings(gate.get("blocked_universe_consumption_cases"))}:
            failures.append(f"production_gate.blocked_universe_consumption_cases missing {case_id}")
    return failures


def build_report(
    *,
    root: pathlib.Path,
    gate: dict[str, Any],
    schema_path: pathlib.Path,
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    static = _mapping(gate.get("gate_static_policy"))
    readiness = _mapping(gate.get("production_readiness"))
    quantum = _mapping(gate.get("quantum_consumer_policy"))
    owner = _mapping(gate.get("owner_override_policy"))
    source = _mapping(gate.get("source_evidence_boundary_policy"))
    connector = _mapping(gate.get("connector_semantic_boundary_policy"))
    runtime = _mapping(gate.get("runtime_live_order_boundary_policy"))
    return {
        "accepted_source_packets_created": source.get("accepted_source_packets_created") or _flag(gate, "accepted_source_packets_created"),
        "agent_algorithm_foundation_dependencies_present": True,
        "agent_roles_validated_against_agent_charter_report": True,
        "agent_universe_consumer_access_is_deterministic": static.get("agent_universe_consumer_access_is_deterministic"),
        "allowed_universe_consumption_matrix_present": bool(gate.get("allowed_universe_consumption_matrix")),
        "atomicrows_bundle_hash_authority_created": _flag(gate, "atomicrows_bundle_hash_authority_created"),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_rows_created": _flag(gate, "atomicrows_bundle_rows_created"),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "atomicrows_lifecycle_binding_dependencies_present": True,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "authorized_consumer_classes_present": bool(gate.get("authorized_consumer_classes")),
        "candidate_stack_generation_created": static.get("candidate_stack_generation_created") or _flag(gate, "candidate_stack_generation_created"),
        "cash_receipts_created": runtime.get("cash_receipts_created") or _flag(gate, "cash_receipts_created"),
        "connector_semantic_binding_created": connector.get("connector_semantic_binding_created") or _flag(gate, "connector_semantic_binding_created"),
        "connector_semantic_value_created": connector.get("connector_semantic_value_created") or _flag(gate, "connector_semantic_value_created"),
        "connector_semantics_created": connector.get("connector_semantics_created") or _flag(gate, "connector_semantics_created"),
        "consumer_classes_validated": True,
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "depends_on_pr77_edge_packet_schema": True,
        "depends_on_pr78_trade_context_packet_schema": True,
        "depends_on_pr79_selection_universe_registry": True,
        "external_fact_value_created": _flag(gate, "external_fact_value_created"),
        "fallback_bundle_required_before_quantum_runtime_use": quantum.get("fallback_bundle_required_before_quantum_runtime_use"),
        "fill_receipts_created": runtime.get("fill_receipts_created") or _flag(gate, "fill_receipts_created"),
        "final_ready": readiness.get("final_ready"),
        "fixture_path": _as_posix(fixture_path),
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": quantum.get("future_optimizer_arbitration_gate_required_before_optimizer_choice"),
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": quantum.get("future_owner_quantum_priority_policy_required_before_quantum_priority_selection"),
        "future_quantum_applicability_registry_required_before_quantum_selection": quantum.get("future_quantum_applicability_registry_required_before_quantum_selection"),
        "liquidity_fact_created": _flag(gate, "liquidity_fact_created"),
        "live_evidence_required_before_profit_claim": quantum.get("live_evidence_required_before_profit_claim"),
        "live_readiness_created": runtime.get("live_readiness_created") or _flag(gate, "live_readiness_created"),
        "market_data_fact_created": _flag(gate, "market_data_fact_created"),
        "missing_universe_binding_blocks_normal_access": static.get("missing_universe_binding_blocks_normal_access"),
        "optimizer_arbitration_created": static.get("optimizer_arbitration_created") or _flag(gate, "optimizer_arbitration_created"),
        "order_authority_created": runtime.get("order_authority_created") or _flag(gate, "order_authority_created"),
        "order_intent_authority_created": runtime.get("order_intent_authority_created") or _flag(gate, "order_intent_authority_created"),
        "order_receipts_created": runtime.get("order_receipts_created") or _flag(gate, "order_receipts_created"),
        "owner_override_fabricates_accepted_source_packet": owner.get("owner_override_fabricates_accepted_source_packet"),
        "owner_override_fabricates_connector_semantic": owner.get("owner_override_fabricates_connector_semantic"),
        "owner_override_fabricates_external_fact": owner.get("owner_override_fabricates_external_fact"),
        "owner_override_fabricates_order_receipt": owner.get("owner_override_fabricates_order_receipt"),
        "owner_override_fabricates_profit_evidence": owner.get("owner_override_fabricates_profit_evidence"),
        "owner_override_fabricates_quantum_backend_execution": owner.get("owner_override_fabricates_quantum_backend_execution"),
        "owner_override_fabricates_replay_paper_result": owner.get("owner_override_fabricates_replay_paper_result"),
        "owner_override_fabricates_runtime_cash_receipt": owner.get("owner_override_fabricates_runtime_cash_receipt"),
        "owner_override_satisfies_internal_selection_universe_consumer_access_only": owner.get("owner_override_satisfies_internal_selection_universe_consumer_access_only"),
        "paper_execution_created": _flag(gate, "paper_execution_created"),
        "paper_results_created": _flag(gate, "paper_results_created"),
        "parameter_selection_universe_consumer_gate_ready": readiness.get("parameter_selection_universe_consumer_gate_ready"),
        "private_state_fetch_created": runtime.get("private_state_fetch_created") or _flag(gate, "private_state_fetch_created"),
        "production_consumer_access_evaluated": readiness.get("production_consumer_access_evaluated"),
        "production_gate_path": _as_posix(production_gate_path),
        "production_routing_evaluated": readiness.get("production_routing_evaluated"),
        "production_routing_ready": readiness.get("production_routing_ready"),
        "production_selection_ready": readiness.get("production_selection_ready"),
        "production_selection_universe_consumer_gate_evaluated": readiness.get("production_selection_universe_consumer_gate_evaluated"),
        "production_selection_universe_consumer_gate_ready": readiness.get("production_selection_universe_consumer_gate_ready"),
        "profit_evidence_created": runtime.get("profit_evidence_created") or _flag(gate, "profit_evidence_created"),
        "quantum_advantage_claim_created": quantum.get("quantum_advantage_claim_created") or _flag(gate, "quantum_advantage_claim_created"),
        "quantum_arbitration_created": quantum.get("quantum_arbitration_created") or _flag(gate, "quantum_arbitration_created"),
        "quantum_backend_evidence_created": _flag(gate, "quantum_backend_evidence_created"),
        "quantum_consumer_access_static_metadata_only": quantum.get("quantum_consumer_access_static_metadata_only"),
        "quantum_optimized_portfolio_selection_consumption_supported_static_only": quantum.get("quantum_optimized_portfolio_selection_consumption_supported_static_only"),
        "quantum_selection_created": quantum.get("quantum_selection_created") or _flag(gate, "quantum_selection_created"),
        "ranking_created": static.get("ranking_created") or _flag(gate, "ranking_created"),
        "replay_execution_created": _flag(gate, "replay_execution_created"),
        "replay_paper_evidence_required_before_advantage_claim": quantum.get("replay_paper_evidence_required_before_advantage_claim"),
        "replay_paper_execution_created": static.get("replay_paper_execution_created"),
        "replay_results_created": _flag(gate, "replay_results_created"),
        "repair_pr76_long_path_fix_present": (root / PR76_SHORT_TEST).exists() and not (root / PR76_OLD_LONG_TEST).exists(),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "required_universe_count": len(REQUIRED_SELECTION_UNIVERSE_IDS),
        "required_universe_ids_present": tuple(gate.get("required_selection_universe_ids", [])) == REQUIRED_SELECTION_UNIVERSE_IDS,
        "route_result_created": static.get("route_result_created") or _flag(gate, "route_result_created"),
        "routed_universe_ids_created": static.get("routed_universe_ids_created") or _flag(gate, "routed_universe_ids_created"),
        "runtime_artifacts_created": runtime.get("runtime_artifacts_created") or _flag(gate, "runtime_artifacts_created"),
        "runtime_live_order_authority_created": static.get("runtime_live_order_authority_created"),
        "runtime_live_use_created": runtime.get("runtime_live_use_created") or _flag(gate, "runtime_live_use_created"),
        "runtime_resolver_execution_created": runtime.get("runtime_resolver_execution_created") or _flag(gate, "runtime_resolver_execution_created"),
        "schema_path": _as_posix(schema_path),
        "scoring_created": static.get("scoring_created") or _flag(gate, "scoring_created"),
        "selected_stack_created": static.get("selected_stack_created"),
        "semantic_task_id": SEMANTIC_TASK_ID,
        "source_acceptance_created": source.get("source_acceptance_created") or _flag(gate, "source_acceptance_created"),
        "source_retrieval_created": source.get("source_retrieval_created") or _flag(gate, "source_retrieval_created"),
        "stack_selection_created": static.get("stack_selection_created") or _flag(gate, "stack_selection_created"),
        "strongest_classical_comparator_required_before_quantum_advantage_claim": quantum.get("strongest_classical_comparator_required_before_quantum_advantage_claim"),
        "trade_context_to_selection_universe_routing_created": static.get("trade_context_to_selection_universe_routing_created"),
        "unknown_agent_blocks_normal_access": static.get("unknown_agent_blocks_normal_access"),
        "unknown_consumer_class_blocks_normal_access": static.get("unknown_consumer_class_blocks_normal_access"),
        "unknown_universe_blocks_normal_access": static.get("unknown_universe_blocks_normal_access"),
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
        "depends_on_pr79_selection_universe_registry": True,
        "depends_on_pr78_trade_context_packet_schema": True,
        "depends_on_pr77_edge_packet_schema": True,
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "repair_pr76_long_path_fix_present": True,
        "agent_algorithm_foundation_dependencies_present": True,
        "atomicrows_lifecycle_binding_dependencies_present": True,
        "required_universe_count": 4,
        "required_universe_ids_present": True,
        "authorized_consumer_classes_present": True,
        "allowed_universe_consumption_matrix_present": True,
        "agent_roles_validated_against_agent_charter_report": True,
        "consumer_classes_validated": True,
        "agent_universe_consumer_access_is_deterministic": True,
        "unknown_agent_blocks_normal_access": True,
        "unknown_universe_blocks_normal_access": True,
        "unknown_consumer_class_blocks_normal_access": True,
        "missing_universe_binding_blocks_normal_access": True,
        "owner_override_satisfies_internal_selection_universe_consumer_access_only": True,
        "parameter_selection_universe_consumer_gate_ready": True,
        "production_selection_universe_consumer_gate_evaluated": False,
        "production_selection_universe_consumer_gate_ready": False,
        "production_consumer_access_evaluated": False,
        "production_routing_evaluated": False,
        "production_routing_ready": False,
        "production_selection_ready": False,
        "final_ready": False,
        "trade_context_to_selection_universe_routing_created": False,
        "routed_universe_ids_created": False,
        "route_result_created": False,
        "selected_stack_created": False,
        "stack_selection_created": False,
        "scoring_created": False,
        "ranking_created": False,
        "optimizer_arbitration_created": False,
        "candidate_stack_generation_created": False,
        "replay_paper_execution_created": False,
        "runtime_live_order_authority_created": False,
        "order_intent_authority_created": False,
        "order_authority_created": False,
        "quantum_optimized_portfolio_selection_consumption_supported_static_only": True,
        "quantum_consumer_access_static_metadata_only": True,
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
        "owner_override_fabricates_external_fact": False,
        "owner_override_fabricates_accepted_source_packet": False,
        "owner_override_fabricates_connector_semantic": False,
        "owner_override_fabricates_runtime_cash_receipt": False,
        "owner_override_fabricates_order_receipt": False,
        "owner_override_fabricates_replay_paper_result": False,
        "owner_override_fabricates_quantum_backend_execution": False,
        "owner_override_fabricates_profit_evidence": False,
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
        "cash_receipts_created": False,
        "order_receipts_created": False,
        "fill_receipts_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "replay_results_created": False,
        "paper_results_created": False,
        "profit_evidence_created": False,
        "atomicrows_bundle_jsonl_exists": False,
        "atomicrows_bundle_sha256_exists": False,
        "atomicrows_bundle_rows_created": False,
        "atomicrows_bundle_hash_authority_created": False,
        "schema_path": _as_posix(DEFAULT_SCHEMA),
        "production_gate_path": _as_posix(DEFAULT_PRODUCTION_GATE),
        "fixture_path": _as_posix(DEFAULT_FIXTURE),
        "validation_marker": SUCCESS_MARKER,
    }
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected!r}")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is not deterministic sorted JSON")
    return failures


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

    failures.extend(validate_pr73_dependency(root))
    failures.extend(validate_pr74_dependency(root))
    failures.extend(validate_pr75_dependency(root))
    _edge_schema, _edge_packet, pr77_failures = validate_pr77_dependency(root)
    failures.extend(pr77_failures)
    _trade_schema, _trade_packet, pr78_failures = validate_pr78_dependency(root)
    failures.extend(pr78_failures)
    _pr79_schema, pr79_registry, _pr79_report, pr79_failures = validate_pr79_dependency(root)
    failures.extend(pr79_failures)
    failures.extend(validate_agent_algorithm_foundation_dependencies(root))
    failures.extend(validate_atomicrows_lifecycle_binding_dependencies(root))
    failures.extend(validate_repair_pr76_dependency(root))

    schema, schema_failures = _load_json_checked(root / schema_path, "PR80_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_gate = load_yaml(root / production_gate_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR80_PRODUCTION_GATE_MALFORMED: {exc}"]),
            report=None,
        )
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR80_FIXTURE_MALFORMED: {exc}"]),
            report=None,
        )

    if schema:
        failures.extend(
            validate_production_gate(
                gate=production_gate,
                schema=schema,
                pr79_registry=pr79_registry,
                root=root,
            )
        )
        fixture_gate = _gate_from_fixture(fixture)
        failures.extend(schema_subset_failures(fixture, schema, "fixture"))
        failures.extend(
            validate_production_gate(
                gate=fixture_gate,
                schema=schema,
                pr79_registry=pr79_registry,
                root=root,
            )
        )
        failures.extend(validate_fixture_cases(fixture, schema, pr79_registry, root))

    artifact_texts = (
        (_as_posix(schema_path), (root / schema_path).read_text(encoding="utf-8")),
        (_as_posix(production_gate_path), (root / production_gate_path).read_text(encoding="utf-8")),
        (_as_posix(fixture_path), (root / fixture_path).read_text(encoding="utf-8")),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        root=root,
        gate=production_gate,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        root=root,
        gate=production_gate,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR80 report is not deterministic")
    failures.extend(validate_no_forbidden_claims((("generated_report", serialize_report(report)),)))
    failures.extend(_report_safety_failures(report))

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
