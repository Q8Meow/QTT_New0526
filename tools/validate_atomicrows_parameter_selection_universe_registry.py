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
    / "atomicrows_parameter_selection_universe_registry.schema.json"
)
DEFAULT_PRODUCTION_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterSelectionUniverseRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_selection_universe_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterSelectionUniverseRegistry.report.json"
)

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

REGISTRY_ID = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY"
REGISTRY_VERSION = "v1"
SEMANTIC_TASK_ID = "ROADMAP-SELECTION-UNIVERSE-REGISTRY"
AUTHORITY_CLASS = (
    "STATIC_PARAMETER_SELECTION_UNIVERSE_REGISTRY_ONLY_NOT_CONSUMER_GATE_NOT_ROUTING_"
    "NOT_SELECTION_NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
REPORT_ID = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_REPORT"
REPORT_VERSION = "v1"
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_CONSUMER_GATE_NOT_ROUTING_NOT_SELECTION_NOT_SCORING_"
    "NOT_RUNTIME_AUTHORITY"
)
VALIDATOR_NAME = "validate_atomicrows_parameter_selection_universe_registry.py"
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_REGISTRY_FAILED"

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
REQUIRED_STACK_ROLES = (
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
ROLE_FAMILY_FIELD_BY_ROLE = {
    "SIGNAL": "selected_signal_family_ids",
    "SCORING": "selected_scoring_family_ids",
    "NORMALIZATION": "selected_normalization_family_ids",
    "RISK": "selected_risk_family_ids",
    "EXECUTION": "selected_execution_family_ids",
    "CAPITAL": "selected_capital_family_ids",
    "LATENCY": "selected_latency_family_ids",
    "ERROR_GUARD": "selected_error_guard_family_ids",
    "QUANTUM_ADVISORY": "selected_quantum_advisory_family_ids",
}
TRADE_CONTEXT_FILTER_FIELDS = (
    "platform",
    "market_type",
    "venue_scope",
    "strategy_class",
    "edge_type",
    "latency_sensitivity_class",
    "capital_intensity_class",
    "risk_mode",
    "liquidity_context",
    "time_horizon",
    "quantum_priority_mode",
    "owner_override_basis",
)
EDGE_SHARED_FIELDS = (
    "venue_scope",
    "edge_type",
    "strategy_class",
    "market_type",
    "latency_sensitivity_class",
    "capital_intensity_class",
)
SCHEMA_REQUIRED_FIELDS = (
    "registry_id",
    "registry_version",
    "authority_class",
    "semantic_task_id",
    "depends_on_qtt_trade_context_packet",
    "depends_on_edge_parameter_stack_selection_packet",
    "depends_on_parameter_stack_role_taxonomy",
    "depends_on_parameter_stack_completeness_gate",
    "depends_on_parameter_stack_compatibility_gate",
    "depends_on_qtt_agent_algorithm_foundation",
    "depends_on_atomicrows_lifecycle_and_binding_foundation",
    "required_selection_universe_ids",
    "universe_definitions",
    "registry_static_policy",
    "universe_membership_policy",
    "owner_override_policy",
    "source_evidence_boundary_policy",
    "connector_semantic_boundary_policy",
    "runtime_live_order_boundary_policy",
    "quantum_universe_policy",
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
REGISTRY_STATIC_TRUE_FIELDS = (
    "selection_universe_registry_is_static_only",
    "universe_definitions_are_static",
    "universe_membership_filters_are_deterministic",
)
REGISTRY_STATIC_FALSE_FIELDS = (
    "random_universe_selection_allowed",
    "dynamic_membership_evaluation_created",
    "member_row_ids_created",
    "selection_universe_consumer_gate_created",
    "trade_context_to_selection_universe_routing_created",
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
MEMBERSHIP_TRUE_FIELDS = ("membership_defined_by_static_filters_only",)
MEMBERSHIP_FALSE_FIELDS = (
    "membership_evaluated_against_atomicrows_bundle",
    "membership_evaluated_against_live_data",
    "membership_evaluated_against_source_retrieval",
    "membership_evaluated_against_connector_semantics",
    "membership_evaluated_against_private_state",
    "membership_evaluated_against_runtime_cash",
    "membership_uses_random_sampling",
    "membership_uses_current_timestamp",
    "membership_uses_external_api_call",
)
BUNDLE_TRUE_FIELDS = (
    "atomicrows_bundle_jsonl_required_for_live_use",
    "atomicrows_bundle_sha_required_for_freeze_authority",
    "universe_registry_does_not_require_bundle_for_static_schema",
)
BUNDLE_FALSE_FIELDS = (
    "universe_registry_creates_bundle_rows",
    "universe_registry_creates_bundle_jsonl",
    "universe_registry_creates_bundle_sha256",
    "universe_registry_creates_bundle_hash_authority",
    "member_row_ids_created_by_this_pr",
    "production_membership_evaluated_by_this_pr",
)
OWNER_OVERRIDE_TRUE_FIELDS = (
    "owner_override_supported",
    "owner_override_satisfies_internal_selection_universe_registry_readiness_only",
    "owner_override_may_force_static_universe_availability_internal_only",
)
OWNER_OVERRIDE_FALSE_FIELDS = (
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
    "universe_source_dependency_values_are_static_labels_only",
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
    "selection_universe_registry_does_not_unlock_connector_semantics",
)
CONNECTOR_FALSE_FIELDS = (
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "connector_semantic_value_created",
)
RUNTIME_TRUE_FIELDS = (
    "selection_universe_registry_is_not_runtime_signal",
    "selection_universe_registry_is_not_live_order_instruction",
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
    "quantum_optimized_portfolio_selection_universe_required",
    "quantum_universe_static_metadata_only",
    "quantum_applicability_mode_static_metadata_only",
    "quantum_priority_mode_compatibility_static_metadata_only",
    "quantum_advisory_stack_role_required",
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
    "selection_universe_consumer_gate_may_consume",
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
EXPLICIT_NO_CLAIM_FALSE_FIELDS = (
    "selection_universe_consumer_gate_created",
    "trade_context_routing_created",
    "selection_universe_routing_created",
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
    "production_membership_evaluated",
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
FORBIDDEN_FIXTURE_CASE_IDS = (
    "SELECTION_UNIVERSE_REGISTRY_VALID_STATIC_ONLY",
    "SELECTION_UNIVERSE_BLOCKED_MISSING_KALSHI_BINARY_SHORT_HORIZON",
    "SELECTION_UNIVERSE_BLOCKED_MISSING_POLYMARKET_EVENT_MARKET_MOMENTUM",
    "SELECTION_UNIVERSE_BLOCKED_MISSING_FORECASTEX_IBKR_EVENT_RISK_HEDGE",
    "SELECTION_UNIVERSE_BLOCKED_MISSING_QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION",
    "SELECTION_UNIVERSE_BLOCKED_DUPLICATE_UNIVERSE_ID",
    "SELECTION_UNIVERSE_BLOCKED_RANDOM_MEMBERSHIP_SELECTION",
    "SELECTION_UNIVERSE_BLOCKED_DYNAMIC_RUNTIME_MEMBERSHIP_EVALUATION",
    "SELECTION_UNIVERSE_BLOCKED_MEMBER_ROW_ID_CREATION",
    "SELECTION_UNIVERSE_BLOCKED_ROUTE_OUTPUT_CREATION",
    "SELECTION_UNIVERSE_BLOCKED_SELECTED_STACK_ID_CREATION",
    "SELECTION_UNIVERSE_BLOCKED_SCORING_OUTPUT_CREATION",
    "SELECTION_UNIVERSE_BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT",
    "SELECTION_UNIVERSE_BLOCKED_CONNECTOR_SEMANTIC_ATTEMPT",
    "SELECTION_UNIVERSE_BLOCKED_RUNTIME_LIVE_ORDER_ATTEMPT",
    "SELECTION_UNIVERSE_BLOCKED_QUANTUM_BACKEND_ATTEMPT",
    "SELECTION_UNIVERSE_BLOCKED_QUANTUM_ADVANTAGE_CLAIM",
    "OWNER_OVERRIDE_SATISFIED_INTERNAL_SELECTION_UNIVERSE_REGISTRY_READINESS_ONLY",
    "OWNER_GLOBAL_OVERRIDE_DOES_NOT_FABRICATE_EXTERNAL_FACTS_OR_EVIDENCE",
)
PRODUCTION_READINESS_EXPECTED = {
    "atomicrows_parameter_selection_universe_registry_ready": True,
    "production_selection_universe_registry_evaluated": False,
    "production_selection_universe_registry_ready": False,
    "production_universe_membership_evaluated": False,
    "production_routing_evaluated": False,
    "production_routing_ready": False,
    "production_selection_ready": False,
    "final_ready": False,
}
QUANTUM_PORTFOLIO_ALLOWED_MODES = {
    "TRUE_QUANTUM_CANDIDATE_STATIC_METADATA_ONLY",
    "QUANTUM_INSPIRED_CANDIDATE_STATIC_METADATA_ONLY",
    "HYBRID_CLASSICAL_QUANTUM_CANDIDATE_STATIC_METADATA_ONLY",
    "QUBO_COMPATIBLE_STATIC_METADATA",
    "ISING_COMPATIBLE_STATIC_METADATA",
    "QAOA_COMPATIBLE_STATIC_METADATA",
    "VQE_COMPATIBLE_STATIC_METADATA",
    "ANNEALING_COMPATIBLE_STATIC_METADATA",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_STATIC_METADATA",
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


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return validate_json_schema_subset(payload, schema, path=label)


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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


def _fixture_to_registry(fixture: dict[str, Any]) -> dict[str, Any]:
    registry = copy.deepcopy(fixture)
    for fixture_only_field in ("fixture_id", "fixture_version", "mode", "execution", "fixture_cases"):
        registry.pop(fixture_only_field, None)
    return registry


def _universe_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(universe.get("universe_id")): universe
        for universe in _list_of_mappings(registry.get("universe_definitions"))
    }


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
    stderr = completed.stderr.strip()
    stdout = completed.stdout.strip()
    return [f"{label}_VALIDATION_BLOCK: marker {marker} missing stdout={stdout!r} stderr={stderr!r}"]


def _roles_from_schema_const(schema: dict[str, Any]) -> list[str]:
    role_schema = _mapping(_mapping(schema.get("properties")).get("required_stack_roles"))
    roles = role_schema.get("const")
    return list(roles) if isinstance(roles, list) else []


def _require_files(root: pathlib.Path, paths: Sequence[tuple[str, pathlib.Path]], marker: str) -> list[str]:
    failures: list[str] = []
    for label, rel_path in paths:
        if not (root / rel_path).exists():
            failures.append(f"{marker}: {label} missing")
    return failures


def validate_pr73_dependency(root: pathlib.Path) -> list[str]:
    failures = _require_files(
        root,
        (
            ("PR73_ROLE_TAXONOMY_SCHEMA", PR73_SCHEMA),
            ("PR73_ROLE_TAXONOMY_REGISTRY", PR73_REGISTRY),
            ("PR73_ROLE_TAXONOMY_REPORT", PR73_REPORT),
            ("PR73_ROLE_TAXONOMY_VALIDATOR", PR73_VALIDATOR),
        ),
        "PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK",
    )
    if failures:
        return failures
    schema = load_json(root / PR73_SCHEMA)
    registry = load_yaml(root / PR73_REGISTRY)
    report = load_json(root / PR73_REPORT)
    if _roles_from_schema_const(schema) != list(REQUIRED_STACK_ROLES):
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: schema role order mismatch")
    if registry.get("required_stack_roles") != list(REQUIRED_STACK_ROLES):
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: registry role order mismatch")
    if report.get("validation_marker") != PR73_SUCCESS_MARKER:
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: report marker mismatch")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=PR73_REPORT,
            validator_path=PR73_VALIDATOR,
            marker=PR73_SUCCESS_MARKER,
            label="PR73_ROLE_TAXONOMY",
        )
    )
    return failures


def validate_pr74_dependency(root: pathlib.Path) -> list[str]:
    failures = _require_files(
        root,
        (
            ("PR74_COMPLETENESS_SCHEMA", PR74_SCHEMA),
            ("PR74_COMPLETENESS_GATE", PR74_REGISTRY),
            ("PR74_COMPLETENESS_REPORT", PR74_REPORT),
            ("PR74_COMPLETENESS_VALIDATOR", PR74_VALIDATOR),
        ),
        "PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK",
    )
    if failures:
        return failures
    registry = load_yaml(root / PR74_REGISTRY)
    report = load_json(root / PR74_REPORT)
    if registry.get("required_stack_roles") != list(REQUIRED_STACK_ROLES):
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: registry role order mismatch")
    if report.get("validation_marker") != PR74_SUCCESS_MARKER:
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: report marker mismatch")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=PR74_REPORT,
            validator_path=PR74_VALIDATOR,
            marker=PR74_SUCCESS_MARKER,
            label="PR74_COMPLETENESS_GATE",
        )
    )
    return failures


def validate_pr75_dependency(root: pathlib.Path) -> list[str]:
    failures = _require_files(
        root,
        (
            ("PR75_COMPATIBILITY_SCHEMA", PR75_SCHEMA),
            ("PR75_COMPATIBILITY_GATE", PR75_REGISTRY),
            ("PR75_COMPATIBILITY_REPORT", PR75_REPORT),
            ("PR75_COMPATIBILITY_VALIDATOR", PR75_VALIDATOR),
        ),
        "PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK",
    )
    if failures:
        return failures
    registry = load_yaml(root / PR75_REGISTRY)
    report = load_json(root / PR75_REPORT)
    if registry.get("required_stack_roles") != list(REQUIRED_STACK_ROLES):
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: registry role order mismatch")
    if report.get("validation_marker") != PR75_SUCCESS_MARKER:
        failures.append("PR75_COMPATIBILITY_GATE_DEPENDENCY_BLOCK: report marker mismatch")
    failures.extend(
        _dependency_report_or_validator_ok(
            root=root,
            report_path=PR75_REPORT,
            validator_path=PR75_VALIDATOR,
            marker=PR75_SUCCESS_MARKER,
            label="PR75_COMPATIBILITY_GATE",
        )
    )
    return failures


def validate_pr77_dependency(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    failures = _require_files(
        root,
        (
            ("PR77_EDGE_PACKET_SCHEMA", PR77_SCHEMA),
            ("PR77_EDGE_PACKET_REGISTRY", PR77_REGISTRY),
            ("PR77_EDGE_PACKET_REPORT", PR77_REPORT),
            ("PR77_EDGE_PACKET_VALIDATOR", PR77_VALIDATOR),
        ),
        "PR77_EDGE_PACKET_SCHEMA_DEPENDENCY_BLOCK",
    )
    edge_schema = load_json(root / PR77_SCHEMA) if (root / PR77_SCHEMA).exists() else {}
    edge_packet = load_yaml(root / PR77_REGISTRY) if (root / PR77_REGISTRY).exists() else {}
    if not failures:
        report = load_json(root / PR77_REPORT)
        if report.get("validation_marker") != PR77_SUCCESS_MARKER:
            failures.append("PR77_EDGE_PACKET_SCHEMA_DEPENDENCY_BLOCK: report marker mismatch")
        if edge_packet.get("required_stack_role_family_fields") != ROLE_FAMILY_FIELD_BY_ROLE:
            failures.append("PR77_EDGE_PACKET_SCHEMA_DEPENDENCY_BLOCK: role family mapping mismatch")
        failures.extend(
            _dependency_report_or_validator_ok(
                root=root,
                report_path=PR77_REPORT,
                validator_path=PR77_VALIDATOR,
                marker=PR77_SUCCESS_MARKER,
                label="PR77_EDGE_PACKET_SCHEMA",
            )
        )
    return edge_schema, edge_packet, failures


def validate_pr78_dependency(root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    failures = _require_files(
        root,
        (
            ("PR78_TRADE_CONTEXT_SCHEMA", PR78_SCHEMA),
            ("PR78_TRADE_CONTEXT_REGISTRY", PR78_REGISTRY),
            ("PR78_TRADE_CONTEXT_REPORT", PR78_REPORT),
            ("PR78_TRADE_CONTEXT_VALIDATOR", PR78_VALIDATOR),
        ),
        "PR78_TRADE_CONTEXT_PACKET_SCHEMA_DEPENDENCY_BLOCK",
    )
    trade_schema = load_json(root / PR78_SCHEMA) if (root / PR78_SCHEMA).exists() else {}
    trade_packet = load_yaml(root / PR78_REGISTRY) if (root / PR78_REGISTRY).exists() else {}
    if not failures:
        report = load_json(root / PR78_REPORT)
        if report.get("validation_marker") != PR78_SUCCESS_MARKER:
            failures.append("PR78_TRADE_CONTEXT_PACKET_SCHEMA_DEPENDENCY_BLOCK: report marker mismatch")
        minimum_fields = trade_packet.get("minimum_required_packet_fields")
        for field in TRADE_CONTEXT_FILTER_FIELDS:
            if field != "owner_override_basis" and field not in minimum_fields:
                failures.append(f"PR78_TRADE_CONTEXT_PACKET_SCHEMA_DEPENDENCY_BLOCK: {field} missing")
        if "owner_override_basis" not in minimum_fields:
            failures.append("PR78_TRADE_CONTEXT_PACKET_SCHEMA_DEPENDENCY_BLOCK: owner_override_basis missing")
        failures.extend(
            _dependency_report_or_validator_ok(
                root=root,
                report_path=PR78_REPORT,
                validator_path=PR78_VALIDATOR,
                marker=PR78_SUCCESS_MARKER,
                label="PR78_TRADE_CONTEXT_PACKET_SCHEMA",
            )
        )
    return trade_schema, trade_packet, failures


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
        failures.append("PRE_PR79_REPAIR_NOT_APPLIED_BLOCK")
    if (root / PR76_OLD_LONG_TEST).exists():
        failures.append("OLD_LONG_RUNTIME_RESOLVER_TEST_REINTRODUCED_BLOCK")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = set(schema.get("required", []))
    properties = _mapping(schema.get("properties"))
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR79_SCHEMA_REQUIRED_FIELD_MISSING: {field}")
        if field not in properties:
            failures.append(f"PR79_SCHEMA_PROPERTY_MISSING: {field}")
    if schema.get("additionalProperties") is not False:
        failures.append("PR79_SCHEMA_MUST_BE_STRICT_ADDITIONAL_PROPERTIES_FALSE")
    return failures


def _expect_policy_fields(
    payload: dict[str, Any],
    true_fields: Sequence[str],
    false_fields: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    for field in true_fields:
        if payload.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in false_fields:
        if payload.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_required_universes(registry: dict[str, Any], label: str = "registry") -> list[str]:
    ids = [str(item.get("universe_id")) for item in _list_of_mappings(registry.get("universe_definitions"))]
    failures: list[str] = []
    if registry.get("required_selection_universe_ids") != list(REQUIRED_SELECTION_UNIVERSE_IDS):
        failures.append(f"{label}.required_selection_universe_ids must match canonical required universes")
    for universe_id in REQUIRED_SELECTION_UNIVERSE_IDS:
        if universe_id not in ids:
            failures.append(f"{label}: missing required universe {universe_id}")
    return failures


def validate_universe_uniqueness(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        universe_id = str(universe.get("universe_id"))
        if universe_id in seen:
            failures.append(f"{label}: duplicate universe_id {universe_id}")
        seen.add(universe_id)
    return failures


def validate_universe_static_policies(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures: list[str] = []
    failures.extend(
        _expect_policy_fields(
            _mapping(registry.get("registry_static_policy")),
            REGISTRY_STATIC_TRUE_FIELDS,
            REGISTRY_STATIC_FALSE_FIELDS,
            f"{label}.registry_static_policy",
        )
    )
    failures.extend(
        _expect_policy_fields(
            _mapping(registry.get("universe_membership_policy")),
            MEMBERSHIP_TRUE_FIELDS,
            MEMBERSHIP_FALSE_FIELDS,
            f"{label}.universe_membership_policy",
        )
    )
    failures.extend(
        _expect_policy_fields(
            _mapping(registry.get("atomicrows_bundle_dependency_policy")),
            BUNDLE_TRUE_FIELDS,
            BUNDLE_FALSE_FIELDS,
            f"{label}.atomicrows_bundle_dependency_policy",
        )
    )
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        uid = str(universe.get("universe_id"))
        if universe.get("universe_authority_class") != "STATIC_SELECTION_UNIVERSE_DEFINITION_ONLY_NOT_ROUTING_NOT_SELECTION_NOT_RUNTIME_AUTHORITY":
            failures.append(f"{label}.{uid}.universe_authority_class invalid")
        if universe.get("universe_membership_rule_type") != "STATIC_DETERMINISTIC_FILTERS_ONLY":
            failures.append(f"{label}.{uid}.universe_membership_rule_type must be static deterministic")
        if universe.get("deterministic_filter_keys") != list(TRADE_CONTEXT_FILTER_FIELDS):
            failures.append(f"{label}.{uid}.deterministic_filter_keys mismatch")
        failures.extend(
            _expect_policy_fields(
                _mapping(universe.get("atomicrows_bundle_dependency_policy")),
                BUNDLE_TRUE_FIELDS,
                BUNDLE_FALSE_FIELDS,
                f"{label}.{uid}.atomicrows_bundle_dependency_policy",
            )
        )
        flags = _mapping(universe.get("no_claim_flags"))
        for field, value in flags.items():
            if value is not False:
                failures.append(f"{label}.{uid}.no_claim_flags.{field} must be false")
    return failures


def _enum_from_property(schema: dict[str, Any], field: str) -> set[str]:
    prop = _mapping(_mapping(schema.get("properties")).get(field))
    values = prop.get("enum")
    return set(values) if isinstance(values, list) else set()


def validate_trade_context_alignment(
    registry: dict[str, Any],
    trade_schema: dict[str, Any],
    trade_packet: dict[str, Any],
    label: str = "registry",
) -> list[str]:
    failures: list[str] = []
    minimum_fields = set(trade_packet.get("minimum_required_packet_fields", []))
    for field in TRADE_CONTEXT_FILTER_FIELDS:
        if field not in minimum_fields:
            failures.append(f"{label}: trade-context field {field} missing from PR78 minimum fields")
    enum_by_field = {
        field: _enum_from_property(trade_schema, field)
        for field in TRADE_CONTEXT_FILTER_FIELDS
        if field != "owner_override_basis"
    }
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        uid = str(universe.get("universe_id"))
        filters = _mapping(universe.get("trade_context_field_filters"))
        static_filters = _mapping(universe.get("static_membership_filters"))
        for field in TRADE_CONTEXT_FILTER_FIELDS:
            if field not in filters:
                failures.append(f"{label}.{uid}.trade_context_field_filters missing {field}")
            if field not in static_filters:
                failures.append(f"{label}.{uid}.static_membership_filters missing {field}")
        if filters != static_filters:
            failures.append(f"{label}.{uid}.trade_context_field_filters must equal static_membership_filters")
        for field, allowed in enum_by_field.items():
            values = filters.get(field)
            if not isinstance(values, list) or not values:
                failures.append(f"{label}.{uid}.{field} filters must be a non-empty list")
                continue
            unknown = sorted(set(values) - allowed)
            if unknown:
                failures.append(f"{label}.{uid}.{field} values not in PR78 enum: {unknown}")
    return failures


def validate_edge_packet_alignment(
    registry: dict[str, Any],
    edge_packet: dict[str, Any],
    label: str = "registry",
) -> list[str]:
    failures: list[str] = []
    minimum = set(edge_packet.get("minimum_required_packet_fields", []))
    for field in EDGE_SHARED_FIELDS:
        if field not in minimum:
            failures.append(f"{label}: PR77 EDGE packet missing shared field {field}")
    if edge_packet.get("required_stack_role_family_fields") != ROLE_FAMILY_FIELD_BY_ROLE:
        failures.append(f"{label}: PR77 role-family mapping mismatch")
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        uid = str(universe.get("universe_id"))
        filters = _mapping(universe.get("trade_context_field_filters"))
        for field in EDGE_SHARED_FIELDS:
            if field not in filters:
                failures.append(f"{label}.{uid}: EDGE shared field {field} missing from filters")
    return failures


def validate_stack_role_alignment(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures: list[str] = []
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        uid = str(universe.get("universe_id"))
        if universe.get("required_stack_roles") != list(REQUIRED_STACK_ROLES):
            failures.append(f"{label}.{uid}.required_stack_roles order mismatch")
        if _mapping(universe.get("required_role_family_fields")) != ROLE_FAMILY_FIELD_BY_ROLE:
            failures.append(f"{label}.{uid}.required_role_family_fields mismatch")
        if "QUANTUM_ADVISORY" not in universe.get("required_stack_roles", []):
            failures.append(f"{label}.{uid}.required_stack_roles missing QUANTUM_ADVISORY")
    return failures


def validate_required_universe_characteristics(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures: list[str] = []
    universes = _universe_by_id(registry)
    kalshi = universes.get("KALSHI_BINARY_SHORT_HORIZON", {})
    if kalshi:
        if "KALSHI" not in kalshi.get("platform_scope", []):
            failures.append(f"{label}.KALSHI_BINARY_SHORT_HORIZON platform_scope missing KALSHI")
        if not {"BINARY_OUTCOME", "PREDICTION_MARKET"}.issubset(set(kalshi.get("market_type_scope", []))):
            failures.append(f"{label}.KALSHI_BINARY_SHORT_HORIZON market_type_scope incomplete")
        if "SINGLE_PLATFORM" not in kalshi.get("venue_scope", []):
            failures.append(f"{label}.KALSHI_BINARY_SHORT_HORIZON venue_scope missing SINGLE_PLATFORM")
        if not ({"LATENCY_MEDIUM_STATIC_CONTEXT_ONLY", "LATENCY_HIGH_STATIC_CONTEXT_ONLY"} & set(kalshi.get("latency_sensitivity_classes", []))):
            failures.append(f"{label}.KALSHI_BINARY_SHORT_HORIZON latency class missing")
        if not ({"CAPITAL_LOW_STATIC_CONTEXT_ONLY", "CAPITAL_MEDIUM_STATIC_CONTEXT_ONLY"} & set(kalshi.get("capital_intensity_classes", []))):
            failures.append(f"{label}.KALSHI_BINARY_SHORT_HORIZON capital class missing")

    polymarket = universes.get("POLYMARKET_EVENT_MARKET_MOMENTUM", {})
    if polymarket:
        if "POLYMARKET" not in polymarket.get("platform_scope", []):
            failures.append(f"{label}.POLYMARKET_EVENT_MARKET_MOMENTUM platform_scope missing POLYMARKET")
        if not {"EVENT_MARKET", "PREDICTION_MARKET"}.issubset(set(polymarket.get("market_type_scope", []))):
            failures.append(f"{label}.POLYMARKET_EVENT_MARKET_MOMENTUM market_type_scope incomplete")
        if "SINGLE_PLATFORM" not in polymarket.get("venue_scope", []):
            failures.append(f"{label}.POLYMARKET_EVENT_MARKET_MOMENTUM venue_scope missing SINGLE_PLATFORM")
        if "MOMENTUM_CANDIDATE_STATIC_ONLY" not in polymarket.get("strategy_class_scope", []):
            failures.append(f"{label}.POLYMARKET_EVENT_MARKET_MOMENTUM strategy missing")
        if not ({"MICROSTRUCTURE_EDGE_STATIC_ONLY", "RESEARCH_EDGE_STATIC_ONLY"} & set(polymarket.get("edge_type_scope", []))):
            failures.append(f"{label}.POLYMARKET_EVENT_MARKET_MOMENTUM edge type missing")

    forecastex = universes.get("FORECASTEX_IBKR_EVENT_RISK_HEDGE", {})
    if forecastex:
        if "FORECASTEX_IBKR" not in forecastex.get("platform_scope", []):
            failures.append(f"{label}.FORECASTEX_IBKR_EVENT_RISK_HEDGE platform_scope missing FORECASTEX_IBKR")
        if not ({"FORECAST_CONTRACT", "EVENT_MARKET", "PREDICTION_MARKET"} & set(forecastex.get("market_type_scope", []))):
            failures.append(f"{label}.FORECASTEX_IBKR_EVENT_RISK_HEDGE market_type_scope missing")
        if "SINGLE_PLATFORM" not in forecastex.get("venue_scope", []):
            failures.append(f"{label}.FORECASTEX_IBKR_EVENT_RISK_HEDGE venue_scope missing SINGLE_PLATFORM")
        if "EVENT_RISK_HEDGE_CANDIDATE_STATIC_ONLY" not in forecastex.get("strategy_class_scope", []):
            failures.append(f"{label}.FORECASTEX_IBKR_EVENT_RISK_HEDGE strategy missing")
        if not ({"RISK_CONSERVATIVE_STATIC_CONTEXT_ONLY", "RISK_BALANCED_STATIC_CONTEXT_ONLY"} & set(forecastex.get("risk_modes", []))):
            failures.append(f"{label}.FORECASTEX_IBKR_EVENT_RISK_HEDGE risk mode missing")

    quantum = universes.get("QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION", {})
    if quantum:
        if not ({"MULTI_PLATFORM_PARALLEL", "SYNTHETIC_PLATFORM_SCHEMA_ONLY"} & set(quantum.get("platform_scope", []))):
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION platform scope missing")
        if not ({"MULTI_PLATFORM_PARALLEL", "CROSS_VENUE_STATIC_CONTEXT_ONLY"} & set(quantum.get("venue_scope", []))):
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION venue scope missing")
        if "QUANTUM_OPTIMIZATION_CANDIDATE_STATIC_ONLY" not in quantum.get("strategy_class_scope", []):
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION strategy missing")
        if "QUANTUM_ADVISORY_EDGE_STATIC_ONLY" not in quantum.get("edge_type_scope", []):
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION edge type missing")
        if "QUANTUM_ADVISORY" not in quantum.get("required_stack_roles", []):
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION required stack roles missing QUANTUM_ADVISORY")
        if quantum.get("quantum_applicability_mode") not in QUANTUM_PORTFOLIO_ALLOWED_MODES:
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION quantum applicability mode invalid")
        if "OWNER_QUANTUM_PRIORITY_POLICY_PENDING_PR83" not in quantum.get("quantum_priority_mode_compatibility", []):
            failures.append(f"{label}.QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION missing PR83 pending compatibility")
    return failures


def validate_owner_override_policy(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures = _expect_policy_fields(
        _mapping(registry.get("owner_override_policy")),
        OWNER_OVERRIDE_TRUE_FIELDS,
        OWNER_OVERRIDE_FALSE_FIELDS,
        f"{label}.owner_override_policy",
    )
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        failures.extend(
            _expect_policy_fields(
                _mapping(universe.get("owner_override_policy")),
                OWNER_OVERRIDE_TRUE_FIELDS,
                OWNER_OVERRIDE_FALSE_FIELDS,
                f"{label}.{universe.get('universe_id')}.owner_override_policy",
            )
        )
    return failures


def validate_quantum_universe_boundary(registry: dict[str, Any], label: str = "registry") -> list[str]:
    return _expect_policy_fields(
        _mapping(registry.get("quantum_universe_policy")),
        QUANTUM_TRUE_FIELDS,
        QUANTUM_FALSE_FIELDS,
        f"{label}.quantum_universe_policy",
    )


def validate_source_evidence_boundary(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures = _expect_policy_fields(
        _mapping(registry.get("source_evidence_boundary_policy")),
        SOURCE_TRUE_FIELDS,
        SOURCE_FALSE_FIELDS,
        f"{label}.source_evidence_boundary_policy",
    )
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        source = _mapping(universe.get("source_dependency_policy"))
        for field in (
            "source_retrieval_created",
            "source_acceptance_created",
            "accepted_source_packets_created",
            "market_data_fact_created",
            "liquidity_fact_created",
            "connector_semantic_value_created",
        ):
            if source.get(field) is not False:
                failures.append(f"{label}.{universe.get('universe_id')}.source_dependency_policy.{field} must be false")
        if source.get("source_dependency_values_static_labels_only") is not True:
            failures.append(f"{label}.{universe.get('universe_id')}.source_dependency_policy must be static labels only")
    return failures


def validate_connector_semantic_boundary(registry: dict[str, Any], label: str = "registry") -> list[str]:
    return _expect_policy_fields(
        _mapping(registry.get("connector_semantic_boundary_policy")),
        CONNECTOR_TRUE_FIELDS,
        CONNECTOR_FALSE_FIELDS,
        f"{label}.connector_semantic_boundary_policy",
    )


def validate_runtime_live_order_boundary(registry: dict[str, Any], label: str = "registry") -> list[str]:
    return _expect_policy_fields(
        _mapping(registry.get("runtime_live_order_boundary_policy")),
        RUNTIME_TRUE_FIELDS,
        RUNTIME_FALSE_FIELDS,
        f"{label}.runtime_live_order_boundary_policy",
    )


def validate_future_consumer_contract(registry: dict[str, Any], label: str = "registry") -> list[str]:
    failures = _expect_policy_fields(
        _mapping(registry.get("future_consumer_contract")),
        FUTURE_CONSUMER_TRUE_FIELDS,
        FUTURE_CONSUMER_FALSE_FIELDS,
        f"{label}.future_consumer_contract",
    )
    for universe in _list_of_mappings(registry.get("universe_definitions")):
        failures.extend(
            _expect_policy_fields(
                _mapping(universe.get("future_consumer_contract")),
                FUTURE_CONSUMER_TRUE_FIELDS,
                FUTURE_CONSUMER_FALSE_FIELDS,
                f"{label}.{universe.get('universe_id')}.future_consumer_contract",
            )
        )
    return failures


def validate_forbidden_output_fields(payload: dict[str, Any], label: str = "payload") -> list[str]:
    failures: list[str] = []
    for path, key, _value in _walk(payload):
        if key in FORBIDDEN_OUTPUT_FIELDS:
            failures.append(f"{label}: forbidden output field present at {path}")
    return failures


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
        "profit evidence id",
        "quantum advantage proof",
    )
    for label, text in artifact_texts:
        lowered = text.lower()
        for fragment in forbidden_fragments:
            if fragment in lowered:
                failures.append(f"{label}: forbidden fixture/artifact text {fragment}")
    return failures


def validate_no_forbidden_artifacts(root: pathlib.Path) -> list[str]:
    failures: list[str] = []
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
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR79"]
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {completed.stderr.strip()}"]


def _flag(registry: dict[str, Any], field: str) -> bool:
    return bool(_mapping(registry.get("explicit_no_claim_flags")).get(field))


def _policy_bool(registry: dict[str, Any], section: str, field: str) -> bool:
    return bool(_mapping(registry.get(section)).get(field))


def _case_registry_from_fixture(fixture: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    registry = _fixture_to_registry(fixture)
    remove_ids = set(case.get("remove_universe_ids", []))
    if remove_ids:
        registry["universe_definitions"] = [
            universe
            for universe in _list_of_mappings(registry.get("universe_definitions"))
            if universe.get("universe_id") not in remove_ids
        ]
    duplicate_id = case.get("duplicate_universe_id")
    if isinstance(duplicate_id, str):
        for universe in _list_of_mappings(registry.get("universe_definitions")):
            if universe.get("universe_id") == duplicate_id:
                registry["universe_definitions"].append(copy.deepcopy(universe))
                break
    overrides = case.get("registry_overrides")
    if isinstance(overrides, dict):
        _deep_update(registry, overrides)
    universe_overrides = case.get("universe_overrides")
    if isinstance(universe_overrides, dict):
        universes = _universe_by_id(registry)
        for uid, override in universe_overrides.items():
            if uid in universes and isinstance(override, dict):
                _deep_update(universes[uid], override)
    forbidden_field = case.get("forbidden_output_field")
    if isinstance(forbidden_field, str):
        if forbidden_field == "routed_universe_ids":
            registry[forbidden_field] = ["SYNTHETIC_FORBIDDEN_ROUTED_UNIVERSE"]
        elif forbidden_field == "score_breakdown":
            registry[forbidden_field] = {"SYNTHETIC_SCORE": "FORBIDDEN"}
        else:
            registry[forbidden_field] = "SYNTHETIC_FORBIDDEN_OUTPUT_FIELD"
    return registry


def validate_fixture_cases(fixture: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cases = {
        str(case.get("case_id")): case
        for case in _list_of_mappings(fixture.get("fixture_cases"))
    }
    missing_cases = sorted(set(FORBIDDEN_FIXTURE_CASE_IDS) - set(cases))
    if missing_cases:
        failures.append(f"PR79_FIXTURE_CASES_MISSING: {missing_cases}")

    for case_id in FORBIDDEN_FIXTURE_CASE_IDS:
        case = cases.get(case_id)
        if not case:
            continue
        case_registry = _case_registry_from_fixture(fixture, case)
        case_failures: list[str] = []
        case_failures.extend(schema_subset_failures(case_registry, schema, f"fixture_case.{case_id}"))
        case_failures.extend(validate_required_universes(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_universe_uniqueness(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_universe_static_policies(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_owner_override_policy(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_quantum_universe_boundary(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_source_evidence_boundary(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_connector_semantic_boundary(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_runtime_live_order_boundary(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_future_consumer_contract(case_registry, f"fixture_case.{case_id}"))
        case_failures.extend(validate_forbidden_output_fields(case_registry, f"fixture_case.{case_id}"))
        expected_valid = case.get("expected_schema_valid") is True
        if expected_valid and case_failures:
            failures.append(f"{case_id}: expected valid but failed {case_failures}")
        if not expected_valid and not case_failures:
            failures.append(f"{case_id}: expected fail-closed validation failure")
    return failures


def validate_production_registry(
    registry: dict[str, Any],
    schema: dict[str, Any],
    trade_schema: dict[str, Any],
    trade_packet: dict[str, Any],
    edge_packet: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(registry, schema, "production_registry"))
    failures.extend(validate_required_universes(registry))
    failures.extend(validate_universe_uniqueness(registry))
    failures.extend(validate_universe_static_policies(registry))
    failures.extend(validate_trade_context_alignment(registry, trade_schema, trade_packet))
    failures.extend(validate_edge_packet_alignment(registry, edge_packet))
    failures.extend(validate_stack_role_alignment(registry))
    failures.extend(validate_required_universe_characteristics(registry))
    failures.extend(validate_owner_override_policy(registry))
    failures.extend(validate_quantum_universe_boundary(registry))
    failures.extend(validate_source_evidence_boundary(registry))
    failures.extend(validate_connector_semantic_boundary(registry))
    failures.extend(validate_runtime_live_order_boundary(registry))
    failures.extend(validate_future_consumer_contract(registry))
    failures.extend(validate_forbidden_output_fields(registry, "production_registry"))
    for field in EXPLICIT_NO_CLAIM_FALSE_FIELDS:
        if _flag(registry, field) is not False:
            failures.append(f"production_registry.explicit_no_claim_flags.{field} must be false")
    if registry.get("production_readiness") != PRODUCTION_READINESS_EXPECTED:
        failures.append("production_registry.production_readiness mismatch")
    if registry.get("final_ready") is not False:
        failures.append("production_registry.final_ready must be false")
    return failures


def build_report(
    *,
    root: pathlib.Path,
    production_registry: dict[str, Any],
    schema_path: pathlib.Path,
    production_registry_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    static = _mapping(production_registry.get("registry_static_policy"))
    membership = _mapping(production_registry.get("universe_membership_policy"))
    readiness = _mapping(production_registry.get("production_readiness"))
    quantum = _mapping(production_registry.get("quantum_universe_policy"))
    owner = _mapping(production_registry.get("owner_override_policy"))
    source = _mapping(production_registry.get("source_evidence_boundary_policy"))
    connector = _mapping(production_registry.get("connector_semantic_boundary_policy"))
    runtime = _mapping(production_registry.get("runtime_live_order_boundary_policy"))
    ids = {universe.get("universe_id") for universe in _list_of_mappings(production_registry.get("universe_definitions"))}
    return {
        "accepted_source_packets_created": source.get("accepted_source_packets_created") or _flag(production_registry, "accepted_source_packets_created"),
        "agent_algorithm_foundation_dependencies_present": True,
        "atomicrows_bundle_hash_authority_created": _flag(production_registry, "atomicrows_bundle_hash_authority_created"),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_rows_created": _flag(production_registry, "atomicrows_bundle_rows_created"),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "atomicrows_lifecycle_binding_dependencies_present": True,
        "atomicrows_parameter_selection_universe_registry_ready": readiness.get("atomicrows_parameter_selection_universe_registry_ready"),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "candidate_stack_generation_created": static.get("candidate_stack_generation_created") or _flag(production_registry, "candidate_stack_generation_created"),
        "cash_receipts_created": runtime.get("cash_receipts_created") or _flag(production_registry, "cash_receipts_created"),
        "connector_semantic_binding_created": connector.get("connector_semantic_binding_created") or _flag(production_registry, "connector_semantic_binding_created"),
        "connector_semantic_value_created": connector.get("connector_semantic_value_created") or _flag(production_registry, "connector_semantic_value_created"),
        "connector_semantics_created": connector.get("connector_semantics_created") or _flag(production_registry, "connector_semantics_created"),
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "depends_on_pr75_compatibility_gate": True,
        "depends_on_pr77_edge_packet_schema": True,
        "depends_on_pr78_trade_context_packet_schema": True,
        "dynamic_membership_evaluation_created": static.get("dynamic_membership_evaluation_created"),
        "edge_packet_shared_fields_aligned": True,
        "external_fact_value_created": _flag(production_registry, "external_fact_value_created"),
        "fallback_bundle_required_before_quantum_runtime_use": quantum.get("fallback_bundle_required_before_quantum_runtime_use"),
        "fill_receipts_created": runtime.get("fill_receipts_created") or _flag(production_registry, "fill_receipts_created"),
        "final_ready": readiness.get("final_ready"),
        "fixture_path": _as_posix(fixture_path),
        "forecastex_ibkr_event_risk_hedge_present": "FORECASTEX_IBKR_EVENT_RISK_HEDGE" in ids,
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": quantum.get("future_optimizer_arbitration_gate_required_before_optimizer_choice"),
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": quantum.get("future_owner_quantum_priority_policy_required_before_quantum_priority_selection"),
        "future_quantum_applicability_registry_required_before_quantum_selection": quantum.get("future_quantum_applicability_registry_required_before_quantum_selection"),
        "kalshi_binary_short_horizon_present": "KALSHI_BINARY_SHORT_HORIZON" in ids,
        "liquidity_fact_created": _flag(production_registry, "liquidity_fact_created"),
        "live_evidence_required_before_profit_claim": quantum.get("live_evidence_required_before_profit_claim"),
        "live_readiness_created": runtime.get("live_readiness_created") or _flag(production_registry, "live_readiness_created"),
        "market_data_fact_created": _flag(production_registry, "market_data_fact_created"),
        "member_row_ids_created": static.get("member_row_ids_created"),
        "optimizer_arbitration_created": static.get("optimizer_arbitration_created") or _flag(production_registry, "optimizer_arbitration_created"),
        "order_authority_created": runtime.get("order_authority_created") or _flag(production_registry, "order_authority_created"),
        "order_intent_authority_created": runtime.get("order_intent_authority_created") or _flag(production_registry, "order_intent_authority_created"),
        "order_receipts_created": runtime.get("order_receipts_created") or _flag(production_registry, "order_receipts_created"),
        "owner_override_fabricates_accepted_source_packet": owner.get("owner_override_fabricates_accepted_source_packet"),
        "owner_override_fabricates_connector_semantic": owner.get("owner_override_fabricates_connector_semantic"),
        "owner_override_fabricates_external_fact": owner.get("owner_override_fabricates_external_fact"),
        "owner_override_fabricates_order_receipt": owner.get("owner_override_fabricates_order_receipt"),
        "owner_override_fabricates_profit_evidence": owner.get("owner_override_fabricates_profit_evidence"),
        "owner_override_fabricates_quantum_backend_execution": owner.get("owner_override_fabricates_quantum_backend_execution"),
        "owner_override_fabricates_replay_paper_result": owner.get("owner_override_fabricates_replay_paper_result"),
        "owner_override_fabricates_runtime_cash_receipt": owner.get("owner_override_fabricates_runtime_cash_receipt"),
        "owner_override_satisfies_internal_selection_universe_registry_readiness_only": owner.get("owner_override_satisfies_internal_selection_universe_registry_readiness_only"),
        "paper_execution_created": _flag(production_registry, "paper_execution_created"),
        "paper_results_created": _flag(production_registry, "paper_results_created"),
        "polymarket_event_market_momentum_present": "POLYMARKET_EVENT_MARKET_MOMENTUM" in ids,
        "private_state_fetch_created": runtime.get("private_state_fetch_created") or _flag(production_registry, "private_state_fetch_created"),
        "production_registry_path": _as_posix(production_registry_path),
        "production_routing_evaluated": readiness.get("production_routing_evaluated"),
        "production_routing_ready": readiness.get("production_routing_ready"),
        "production_selection_ready": readiness.get("production_selection_ready"),
        "production_selection_universe_registry_evaluated": readiness.get("production_selection_universe_registry_evaluated"),
        "production_selection_universe_registry_ready": readiness.get("production_selection_universe_registry_ready"),
        "production_universe_membership_evaluated": readiness.get("production_universe_membership_evaluated"),
        "profit_evidence_created": runtime.get("profit_evidence_created") or _flag(production_registry, "profit_evidence_created"),
        "quantum_advantage_claim_created": quantum.get("quantum_advantage_claim_created") or _flag(production_registry, "quantum_advantage_claim_created"),
        "quantum_applicability_mode_static_metadata_only": quantum.get("quantum_applicability_mode_static_metadata_only"),
        "quantum_arbitration_created": quantum.get("quantum_arbitration_created") or _flag(production_registry, "quantum_arbitration_created"),
        "quantum_backend_evidence_created": _flag(production_registry, "quantum_backend_evidence_created"),
        "quantum_optimized_portfolio_selection_present": "QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION" in ids,
        "quantum_optimized_portfolio_selection_universe_required": quantum.get("quantum_optimized_portfolio_selection_universe_required"),
        "quantum_priority_mode_compatibility_static_metadata_only": quantum.get("quantum_priority_mode_compatibility_static_metadata_only"),
        "quantum_selection_created": quantum.get("quantum_selection_created") or _flag(production_registry, "quantum_selection_created"),
        "quantum_universe_static_metadata_only": quantum.get("quantum_universe_static_metadata_only"),
        "random_universe_selection_allowed": static.get("random_universe_selection_allowed"),
        "ranking_created": static.get("ranking_created") or _flag(production_registry, "ranking_created"),
        "replay_execution_created": _flag(production_registry, "replay_execution_created"),
        "replay_paper_evidence_required_before_advantage_claim": quantum.get("replay_paper_evidence_required_before_advantage_claim"),
        "replay_results_created": _flag(production_registry, "replay_results_created"),
        "repair_pr76_long_path_fix_present": (root / PR76_SHORT_TEST).exists() and not (root / PR76_OLD_LONG_TEST).exists(),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "required_role_family_fields_aligned_with_edge_packet": True,
        "required_stack_roles_order_valid": True,
        "required_universe_count": len(REQUIRED_SELECTION_UNIVERSE_IDS),
        "required_universe_ids_present": REQUIRED_SELECTION_UNIVERSE_IDS == tuple(production_registry.get("required_selection_universe_ids", [])),
        "route_result_created": static.get("route_result_created") or _flag(production_registry, "route_result_created"),
        "runtime_artifacts_created": runtime.get("runtime_artifacts_created") or _flag(production_registry, "runtime_artifacts_created"),
        "runtime_live_use_created": runtime.get("runtime_live_use_created") or _flag(production_registry, "runtime_live_use_created"),
        "runtime_resolver_execution_created": runtime.get("runtime_resolver_execution_created") or _flag(production_registry, "runtime_resolver_execution_created"),
        "schema_path": _as_posix(schema_path),
        "scoring_created": static.get("scoring_created") or _flag(production_registry, "scoring_created"),
        "selected_stack_created": static.get("selected_stack_created"),
        "selection_universe_consumer_gate_created": static.get("selection_universe_consumer_gate_created") or _flag(production_registry, "selection_universe_consumer_gate_created"),
        "semantic_task_id": SEMANTIC_TASK_ID,
        "source_acceptance_created": source.get("source_acceptance_created") or _flag(production_registry, "source_acceptance_created"),
        "source_retrieval_created": source.get("source_retrieval_created") or _flag(production_registry, "source_retrieval_created"),
        "stack_selection_created": static.get("stack_selection_created") or _flag(production_registry, "stack_selection_created"),
        "strongest_classical_comparator_required_before_quantum_advantage_claim": quantum.get("strongest_classical_comparator_required_before_quantum_advantage_claim"),
        "trade_context_field_filters_aligned": True,
        "trade_context_to_selection_universe_routing_created": static.get("trade_context_to_selection_universe_routing_created"),
        "universe_definitions_are_static": static.get("universe_definitions_are_static"),
        "universe_ids_unique": len(ids) == len(_list_of_mappings(production_registry.get("universe_definitions"))),
        "universe_membership_filters_are_deterministic": static.get("universe_membership_filters_are_deterministic"),
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
        "universe_ids_unique": True,
        "kalshi_binary_short_horizon_present": True,
        "polymarket_event_market_momentum_present": True,
        "forecastex_ibkr_event_risk_hedge_present": True,
        "quantum_optimized_portfolio_selection_present": True,
        "universe_definitions_are_static": True,
        "universe_membership_filters_are_deterministic": True,
        "random_universe_selection_allowed": False,
        "dynamic_membership_evaluation_created": False,
        "member_row_ids_created": False,
        "route_result_created": False,
        "trade_context_to_selection_universe_routing_created": False,
        "selection_universe_consumer_gate_created": False,
        "selected_stack_created": False,
        "stack_selection_created": False,
        "scoring_created": False,
        "ranking_created": False,
        "optimizer_arbitration_created": False,
        "candidate_stack_generation_created": False,
        "required_stack_roles_order_valid": True,
        "required_role_family_fields_aligned_with_edge_packet": True,
        "trade_context_field_filters_aligned": True,
        "edge_packet_shared_fields_aligned": True,
        "atomicrows_parameter_selection_universe_registry_ready": True,
        "production_selection_universe_registry_evaluated": False,
        "production_selection_universe_registry_ready": False,
        "production_universe_membership_evaluated": False,
        "production_routing_evaluated": False,
        "production_routing_ready": False,
        "production_selection_ready": False,
        "final_ready": False,
        "quantum_optimized_portfolio_selection_universe_required": True,
        "quantum_universe_static_metadata_only": True,
        "quantum_applicability_mode_static_metadata_only": True,
        "quantum_priority_mode_compatibility_static_metadata_only": True,
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
        "owner_override_satisfies_internal_selection_universe_registry_readiness_only": True,
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
        "order_authority_created": False,
        "order_intent_authority_created": False,
        "cash_receipts_created": False,
        "order_receipts_created": False,
        "fill_receipts_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "replay_results_created": False,
        "paper_results_created": False,
        "profit_evidence_created": False,
        "atomicrows_bundle_sha256_exists": False,
        "atomicrows_bundle_rows_created": False,
        "atomicrows_bundle_hash_authority_created": False,
        "schema_path": _as_posix(DEFAULT_SCHEMA),
        "production_registry_path": _as_posix(DEFAULT_PRODUCTION_REGISTRY),
        "fixture_path": _as_posix(DEFAULT_FIXTURE),
        "validation_marker": SUCCESS_MARKER,
    }
    if not isinstance(report.get("atomicrows_bundle_jsonl_exists"), bool):
        failures.append("report.atomicrows_bundle_jsonl_exists must be boolean")
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
    production_registry_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    failures.extend(validate_pr73_dependency(root))
    failures.extend(validate_pr74_dependency(root))
    failures.extend(validate_pr75_dependency(root))
    edge_schema, edge_packet, pr77_failures = validate_pr77_dependency(root)
    del edge_schema
    failures.extend(pr77_failures)
    trade_schema, trade_packet, pr78_failures = validate_pr78_dependency(root)
    failures.extend(pr78_failures)
    failures.extend(validate_agent_algorithm_foundation_dependencies(root))
    failures.extend(validate_atomicrows_lifecycle_binding_dependencies(root))
    failures.extend(validate_repair_pr76_dependency(root))

    schema, schema_failures = _load_json_checked(root / schema_path, "PR79_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_registry = load_yaml(root / production_registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR79_PRODUCTION_REGISTRY_MALFORMED: {exc}"]),
            report=None,
        )
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR79_FIXTURE_MALFORMED: {exc}"]),
            report=None,
        )

    if schema:
        failures.extend(
            validate_production_registry(
                production_registry,
                schema,
                trade_schema,
                trade_packet,
                edge_packet,
            )
        )
        fixture_registry = _fixture_to_registry(fixture)
        failures.extend(schema_subset_failures(fixture, schema, "fixture"))
        failures.extend(validate_required_universes(fixture_registry, "fixture"))
        failures.extend(validate_universe_uniqueness(fixture_registry, "fixture"))
        failures.extend(validate_universe_static_policies(fixture_registry, "fixture"))
        failures.extend(validate_stack_role_alignment(fixture_registry, "fixture"))
        failures.extend(validate_required_universe_characteristics(fixture_registry, "fixture"))
        failures.extend(validate_forbidden_output_fields(fixture_registry, "fixture"))
        failures.extend(validate_fixture_cases(fixture, schema))

    artifact_texts = (
        (_as_posix(schema_path), _read_text(root / schema_path)),
        (_as_posix(production_registry_path), _read_text(root / production_registry_path)),
        (_as_posix(fixture_path), _read_text(root / fixture_path)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        root=root,
        production_registry=production_registry,
        schema_path=schema_path,
        production_registry_path=production_registry_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        root=root,
        production_registry=production_registry,
        schema_path=schema_path,
        production_registry_path=production_registry_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR79 report is not deterministic")
    failures.extend(validate_no_forbidden_claims((("generated_report", serialize_report(report)),)))
    failures.extend(_report_safety_failures(report))

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--production-registry", default=str(DEFAULT_PRODUCTION_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        production_registry_path=pathlib.Path(args.production_registry),
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
