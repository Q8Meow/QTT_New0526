#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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
    / "atomicrows"
    / "atomicrows_parameter_stack_compatibility_gate.schema.json"
)
DEFAULT_PRODUCTION_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsParameterStackCompatibilityGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_stack_compatibility_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterStackCompatibilityGate.report.json"
)
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
PR74_GATE = (
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
CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = (
    pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
)

GATE_ID = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE"
GATE_VERSION = "v1"
REPORT_ID = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_REPORT"
REPORT_VERSION = "v1"
VALIDATOR_NAME = "validate_atomicrows_parameter_stack_compatibility_gate.py"
AUTHORITY_CLASS = (
    "STATIC_PARAMETER_STACK_COMPATIBILITY_GATE_NOT_COMPLETENESS_NOT_STACK_SELECTION_"
    "NOT_SCORING_NOT_RUNTIME_AUTHORITY"
)
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_COMPLETENESS_NOT_STACK_SELECTION_NOT_SCORING_"
    "NOT_RUNTIME_AUTHORITY"
)
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_FAILED"
PR73_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
PR74_SUCCESS_MARKER = "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
OWNER_GLOBAL_OVERRIDE = "OWNER_GLOBAL_OVERRIDE"
OWNER_OVERRIDE_INTERNAL_ONLY = "OWNER_OVERRIDE_SATISFIED_INTERNAL_COMPATIBILITY_ONLY"

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
COMPATIBILITY_STATES = (
    "COMPATIBILITY_COMPLETE",
    "COMPATIBILITY_BLOCKED_UPSTREAM_ROLE_INCOMPLETE",
    "COMPATIBILITY_INCOMPLETE_MISSING_INTERFACE",
    "COMPATIBILITY_INCOMPLETE_INTERFACE_MISMATCH",
    "COMPATIBILITY_INCOMPLETE_DUPLICATE_INTERFACE",
    "COMPATIBILITY_INCOMPATIBLE_AUTHORITY_TRANSITION",
    "COMPATIBILITY_INCOMPATIBLE_SOURCE_FACT_BOUNDARY",
    "COMPATIBILITY_INCOMPATIBLE_CONNECTOR_SEMANTIC_BOUNDARY",
    "COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY",
    "COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY",
    OWNER_OVERRIDE_INTERNAL_ONLY,
    "SYNTHETIC_FIXTURE_ONLY_NOT_PRODUCTION_READY",
)
SCHEMA_REQUIRED_FIELDS = (
    "gate_id",
    "gate_version",
    "authority_class",
    "depends_on_parameter_stack_role_taxonomy",
    "depends_on_parameter_stack_completeness_gate",
    "required_stack_roles",
    "role_interface_contracts",
    "compatibility_cases",
    "compatibility_policy",
    "owner_override_policy",
    "quantum_compatibility_policy",
    "source_evidence_boundary_policy",
    "connector_semantic_boundary_policy",
    "runtime_live_order_boundary_policy",
    "future_consumer_contract",
    "forbidden_artifact_flags",
    "validation_invariants",
    "final_ready",
)
COMPATIBILITY_CASE_REQUIRED_FIELDS = (
    "stack_case_id",
    "stack_case_type",
    "upstream_completeness_state",
    "supplied_role_ids",
    "role_complete",
    "role_interface_bindings",
    "missing_interface_ids",
    "mismatched_interface_ids",
    "duplicate_interface_ids",
    "incompatible_authority_transitions",
    "source_fact_boundary_violations",
    "connector_semantic_boundary_violations",
    "runtime_live_order_boundary_violations",
    "quantum_boundary_violations",
    "owner_override_present",
    "owner_override_satisfaction_basis",
    "compatibility_state",
    "normal_stack_compatibility",
    "owner_override_stack_compatibility",
    "final_stack_compatibility",
    "compatibility_authority_class",
    "runtime_use_allowed",
    "live_use_allowed",
    "order_authority_created",
    "replay_paper_evidence_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "deterministic_trace",
    "no_claim_flags",
)
NO_CLAIM_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "runtime_artifacts_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "private_state_fetch_created",
    "order_authority_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
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
    "ranking_created",
    "scoring_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "stack_selection_created",
    "candidate_stack_generation_created",
    "source_fact_value_created",
    "connector_semantic_value_created",
    "runtime_cash_value_created",
)
EXPLICIT_NO_CLAIM_FIELDS = (
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_packets",
    "creates_connector_semantics",
    "creates_connector_semantic_binding",
    "creates_runtime_artifacts",
    "creates_live_readiness",
    "creates_runtime_live_use",
    "creates_private_state_fetch",
    "creates_order_authority",
    "creates_cash_receipts",
    "creates_order_receipts",
    "creates_fill_receipts",
    "creates_replay_results",
    "creates_paper_results",
    "creates_profit_evidence",
    "creates_quantum_backend_evidence",
    "creates_quantum_advantage_claim",
    "creates_latency_superiority_claim",
    "creates_execution_superiority_claim",
    "creates_atomicrows_bundle_rows",
    "creates_atomicrows_bundle_jsonl",
    "creates_atomicrows_bundle_sha256",
    "creates_ranking",
    "creates_scoring",
    "creates_optimizer_arbitration",
    "creates_trade_context_routing",
    "creates_stack_selection",
    "creates_candidate_stack_generation",
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
CASE_FALSE_FIELDS = (
    "runtime_use_allowed",
    "live_use_allowed",
    "order_authority_created",
    "replay_paper_evidence_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "final_stack_compatibility",
)
REPORT_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_connector_semantic",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
    "production_stack_compatibility_evaluated",
    "production_stack_compatible",
    "production_stack_ready",
    "final_ready",
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "connector_semantic_binding_created",
    "runtime_artifacts_created",
    "live_readiness_created",
    "runtime_live_use_created",
    "private_state_fetch_created",
    "order_authority_created",
    "cash_receipts_created",
    "order_receipts_created",
    "fill_receipts_created",
    "replay_results_created",
    "paper_results_created",
    "profit_evidence_created",
    "quantum_backend_evidence_created",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "ranking_created",
    "scoring_created",
    "optimizer_arbitration_created",
    "trade_context_routing_created",
    "stack_selection_created",
    "candidate_stack_generation_created",
    "atomicrows_bundle_sha256_exists",
)

EXPECTED_ROLE_INTERFACE_CONTRACTS: dict[str, dict[str, Any]] = {
    "SIGNAL": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["SCORING", "NORMALIZATION", "QUANTUM_ADVISORY", "ERROR_GUARD"],
        "allowed_upstream_roles": [],
        "compatibility_notes": [
            "produces_signal_candidate_interface_only",
            "future_runtime_snapshot_consumption_requires_later_gate",
            "preserves_no_order_live_profit_authority",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": [
            "research_input_interface",
            "market_hypothesis_input_interface",
            "future_runtime_resolver_snapshot_interface_later_gate_only",
        ],
        "forbidden_downstream_authorities": [
            "order_authority",
            "live_readiness_authority",
            "profit_evidence_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["signal_candidate_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_SIGNAL_COMPATIBILITY_INTERFACE_NOT_ORDER_NOT_LIVE_NOT_PROFIT_AUTHORITY",
        "role_id": "SIGNAL",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "SCORING": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["NORMALIZATION", "QUANTUM_ADVISORY", "ERROR_GUARD"],
        "allowed_upstream_roles": ["SIGNAL"],
        "compatibility_notes": [
            "consumes_signal_candidate_interface",
            "produces_static_score_candidate_interface_without_ranking",
            "preserves_no_stack_selection_or_live_authority",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": ["signal_candidate_interface"],
        "forbidden_downstream_authorities": [
            "score_computation_authority",
            "stack_ranking_authority",
            "stack_selection_authority",
            "live_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["score_candidate_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_SCORING_COMPATIBILITY_INTERFACE_NOT_RANKING_NOT_SELECTION_NOT_RUNTIME_AUTHORITY",
        "role_id": "SCORING",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "NORMALIZATION": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["RISK", "QUANTUM_ADVISORY", "ERROR_GUARD"],
        "allowed_upstream_roles": ["SIGNAL", "SCORING"],
        "compatibility_notes": [
            "consumes_signal_and_score_candidate_interfaces",
            "produces_normalized_candidate_interface",
            "cannot_create_connector_semantics_or_source_fact_values",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": ["signal_candidate_interface", "score_candidate_interface"],
        "forbidden_downstream_authorities": [
            "connector_semantic_authority",
            "source_fact_fabrication_authority",
            "live_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["normalized_candidate_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_NORMALIZATION_COMPATIBILITY_INTERFACE_NOT_CONNECTOR_SEMANTIC_NOT_SOURCE_FACT_AUTHORITY",
        "role_id": "NORMALIZATION",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "RISK": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["EXECUTION", "CAPITAL", "QUANTUM_ADVISORY", "ERROR_GUARD"],
        "allowed_upstream_roles": ["NORMALIZATION", "CAPITAL"],
        "compatibility_notes": [
            "consumes_normalized_and_capital_candidate_interfaces",
            "produces_risk_constraint_interface",
            "order_lifecycle_authority_remains_forbidden",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": ["normalized_candidate_interface", "capital_candidate_interface"],
        "forbidden_downstream_authorities": [
            "order_submission_authority",
            "order_cancel_authority",
            "order_replace_authority",
            "order_reduce_authority",
            "order_close_authority",
            "live_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["risk_constraint_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_RISK_COMPATIBILITY_INTERFACE_NOT_ORDER_LIFECYCLE_NOT_LIVE_AUTHORITY",
        "role_id": "RISK",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "EXECUTION": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["LATENCY", "ERROR_GUARD"],
        "allowed_upstream_roles": ["RISK", "LATENCY"],
        "compatibility_notes": [
            "consumes_risk_and_latency_constraint_interfaces_as_static_metadata",
            "produces_execution_constraint_interface",
            "execution_router_remains_future_final_order_submission_authority",
        ],
        "connector_semantic_dependency_allowed": True,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": ["risk_constraint_interface", "latency_constraint_interface"],
        "forbidden_downstream_authorities": [
            "order_authority",
            "live_order_authority",
            "order_submission_authority",
            "connector_semantic_binding_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["execution_constraint_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_EXECUTION_COMPATIBILITY_INTERFACE_NOT_ORDER_ROUTER_NOT_RUNTIME_AUTHORITY",
        "role_id": "EXECUTION",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "CAPITAL": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["RISK", "QUANTUM_ADVISORY", "ERROR_GUARD"],
        "allowed_upstream_roles": ["RISK"],
        "compatibility_notes": [
            "consumes_risk_constraint_interface",
            "produces_capital_candidate_interface",
            "cannot_create_cash_receipts_or_private_state_fetches",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": ["risk_constraint_interface"],
        "forbidden_downstream_authorities": [
            "cash_receipt_authority",
            "private_state_fetch_authority",
            "balance_semantic_authority",
            "live_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["capital_candidate_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_CAPITAL_COMPATIBILITY_INTERFACE_NOT_CASH_RECEIPT_NOT_PRIVATE_STATE_AUTHORITY",
        "role_id": "CAPITAL",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "LATENCY": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["EXECUTION", "QUANTUM_ADVISORY", "ERROR_GUARD"],
        "allowed_upstream_roles": ["EXECUTION"],
        "compatibility_notes": [
            "consumes_execution_constraint_interface",
            "produces_latency_constraint_interface",
            "cannot_create_latency_superiority_or_runtime_path_behavior",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": ["execution_constraint_interface"],
        "forbidden_downstream_authorities": [
            "latency_superiority_claim_authority",
            "low_latency_live_path_authority",
            "runtime_path_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["latency_constraint_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_LATENCY_COMPATIBILITY_INTERFACE_NOT_LATENCY_SUPERIORITY_NOT_LIVE_PATH_AUTHORITY",
        "role_id": "LATENCY",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "ERROR_GUARD": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": [],
        "allowed_upstream_roles": [
            "SIGNAL",
            "SCORING",
            "NORMALIZATION",
            "RISK",
            "EXECUTION",
            "CAPITAL",
            "LATENCY",
            "QUANTUM_ADVISORY",
        ],
        "compatibility_notes": [
            "consumes_all_role_interfaces_as_safety_metadata",
            "produces_guardrail_constraint_interface",
            "preserves_fail_closed_behavior_without_silent_bypass",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": [
            "signal_candidate_interface",
            "score_candidate_interface",
            "normalized_candidate_interface",
            "risk_constraint_interface",
            "execution_constraint_interface",
            "capital_candidate_interface",
            "latency_constraint_interface",
            "quantum_advisory_candidate_interface",
        ],
        "forbidden_downstream_authorities": [
            "blocker_bypass_authority",
            "silent_bypass_authority",
            "runtime_disablement_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["guardrail_constraint_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_ERROR_GUARD_COMPATIBILITY_INTERFACE_FAIL_CLOSED_NOT_RUNTIME_DISABLEMENT_AUTHORITY",
        "role_id": "ERROR_GUARD",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
    "QUANTUM_ADVISORY": {
        "accepted_source_packet_required_for_external_fact": True,
        "allowed_downstream_roles": ["ERROR_GUARD"],
        "allowed_upstream_roles": ["SIGNAL", "SCORING", "NORMALIZATION", "RISK", "CAPITAL", "LATENCY"],
        "compatibility_notes": [
            "consumes_candidate_and_constraint_interfaces_as_static_metadata",
            "produces_quantum_advisory_candidate_interface",
            "future_quantum_applicability_registry_required_before_quantum_selection",
        ],
        "connector_semantic_dependency_allowed": False,
        "connector_semantic_requires_accepted_source_packet": True,
        "consumes_interfaces": [
            "signal_candidate_interface",
            "score_candidate_interface",
            "normalized_candidate_interface",
            "risk_constraint_interface",
            "capital_candidate_interface",
            "latency_constraint_interface",
        ],
        "forbidden_downstream_authorities": [
            "quantum_backend_execution_authority",
            "optimizer_arbitration_authority",
            "stack_scoring_authority",
            "stack_ranking_authority",
            "stack_selection_authority",
            "quantum_advantage_claim_authority",
        ],
        "live_order_authority_allowed": False,
        "produces_interfaces": ["quantum_advisory_candidate_interface"],
        "profit_evidence_created": False,
        "quantum_backend_execution_allowed": False,
        "required_authority_class": "STATIC_QUANTUM_ADVISORY_COMPATIBILITY_INTERFACE_NOT_BACKEND_NOT_ARBITRATION_NOT_ADVANTAGE_AUTHORITY",
        "role_id": "QUANTUM_ADVISORY",
        "runtime_artifact_dependency_allowed": False,
        "source_fact_dependency_allowed": True,
    },
}

EXPECTED_COMPATIBLE_BINDINGS = tuple(
    {
        "role_id": role_id,
        "consumes_interface_ids": EXPECTED_ROLE_INTERFACE_CONTRACTS[role_id]["consumes_interfaces"],
        "produces_interface_ids": EXPECTED_ROLE_INTERFACE_CONTRACTS[role_id]["produces_interfaces"],
    }
    for role_id in REQUIRED_STACK_ROLES
)

REQUIRED_CASE_IDS = (
    "SYNTHETIC_ROLE_COMPLETE_ALL_INTERFACES_COMPATIBLE",
    "SYNTHETIC_UPSTREAM_ROLE_INCOMPLETE_BLOCKS_COMPATIBILITY",
    "SYNTHETIC_MISSING_SIGNAL_OUTPUT_INTERFACE_BLOCKS_SCORING",
    "SYNTHETIC_SCORING_CONSUMES_WRONG_SIGNAL_INTERFACE",
    "SYNTHETIC_DUPLICATE_NORMALIZED_CANDIDATE_INTERFACE_BINDING",
    "SYNTHETIC_SIGNAL_PRODUCES_ORDER_AUTHORITY",
    "SYNTHETIC_NORMALIZATION_SOURCE_FACT_WITHOUT_ACCEPTED_PACKET",
    "SYNTHETIC_EXECUTION_CONNECTOR_SEMANTIC_WITHOUT_ACCEPTED_PACKET",
    "SYNTHETIC_EXECUTION_ATTEMPTS_LIVE_ORDER_AUTHORITY",
    "SYNTHETIC_CAPITAL_ATTEMPTS_RUNTIME_CASH_RECEIPT",
    "SYNTHETIC_LATENCY_ATTEMPTS_LATENCY_SUPERIORITY_CLAIM",
    "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_BACKEND_EXECUTION",
    "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_ADVANTAGE_CLAIM",
    "SYNTHETIC_QUANTUM_ADVISORY_MISSING_FUTURE_APPLICABILITY_METADATA",
    "SYNTHETIC_MISSING_INTERFACE_WITH_OWNER_GLOBAL_OVERRIDE",
    "SYNTHETIC_QUANTUM_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
    "SYNTHETIC_SOURCE_FACT_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
    "SYNTHETIC_CONNECTOR_SEMANTIC_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
    "SYNTHETIC_RUNTIME_ORDER_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
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


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"{label}_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {}, [f"{label}_MALFORMED: JSON file is invalid: {path}: {exc}"]


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
        ("SECRET_LIKE_PASSWORD", "pass" + "word"),
        ("PRIVATE_ACCOUNT_STATE", "private account" + " state"),
        ("ACCOUNT_DATA_CLAIM", "account" + " data"),
        ("ORDER_COMMAND_SUBMIT", "submit" + " order"),
        ("ORDER_COMMAND_CANCEL", "cancel" + " order"),
        ("ORDER_COMMAND_REPLACE", "replace" + " order"),
        ("SOURCE_ACCEPTANCE_CLAIM", "accepted source packet" + " created"),
        ("CONNECTOR_SEMANTIC_CLAIM", "connector semantic binding" + " created"),
        ("RUNTIME_AUTHORITY_CLAIM", "runtime authority" + " created"),
        ("REPLAY_PROOF_CLAIM", "replay passed" + " as proof"),
        ("PAPER_PROOF_CLAIM", "paper passed" + " as proof"),
        ("PROFIT_CLAIM", "profit" + " proven"),
        ("QUANTUM_BACKEND_EXECUTION_CLAIM", "backend" + " executed"),
        ("QUANTUM_ADVANTAGE_CLAIM", "quantum advantage" + " proven"),
        ("BUNDLE_JSONL_CREATION_CLAIM", "AtomicRows.bundle.jsonl" + " created"),
        ("BUNDLE_SHA_CREATION_CLAIM", "AtomicRows.bundle.sha256" + " created"),
        ("RANKED_BEST_STACK_CLAIM", "ranked" + " best stack"),
        ("SELECTED_BEST_STACK_CLAIM", "selected" + " best stack"),
        ("OPTIMIZER_ARBITRATION_RESULT_CLAIM", "optimizer arbitration" + " result"),
        ("TRADE_ROUTED_CLAIM", "trade" + " routed"),
        ("LIVE_ELIGIBLE_CLAIM", "live" + " eligible"),
    )


def _forbidden_text_regexes() -> tuple[tuple[str, re.Pattern[str]], ...]:
    return (
        ("SECRET_LIKE_AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    )


def validate_no_forbidden_claims(texts: Sequence[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    for label, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() in lowered:
                failures.append(f"{label}: forbidden fixture or gate text {code}")
        for code, pattern in _forbidden_text_regexes():
            if pattern.search(text):
                failures.append(f"{label}: forbidden fixture or gate text {code}")
    return failures


def _schema_subset_failures(
    payload: dict[str, Any],
    schema: dict[str, Any],
    label: str,
) -> list[str]:
    return [
        f"{label}{failure}"
        for failure in validate_json_schema_subset(payload, schema)
    ]


def _roles_from_schema(schema: dict[str, Any]) -> list[str]:
    roles = _mapping(_mapping(schema.get("properties")).get("required_stack_roles")).get(
        "const"
    )
    return list(roles) if isinstance(roles, list) else []


def validate_pr73_dependency(root: pathlib.Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    for label, rel_path in (
        ("PR73_ROLE_TAXONOMY_SCHEMA", PR73_SCHEMA),
        ("PR73_ROLE_TAXONOMY_REGISTRY", PR73_REGISTRY),
        ("PR73_ROLE_TAXONOMY_REPORT", PR73_REPORT),
        ("PR73_ROLE_TAXONOMY_VALIDATOR", PR73_VALIDATOR),
    ):
        if not (root / rel_path).exists():
            failures.append(f"PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: {label} missing")
    if failures:
        return list(REQUIRED_STACK_ROLES), failures

    schema = load_json(root / PR73_SCHEMA)
    registry = load_yaml(root / PR73_REGISTRY)
    report = load_json(root / PR73_REPORT)
    roles = registry.get("required_stack_roles")
    if roles != list(REQUIRED_STACK_ROLES):
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: registry role order mismatch")
    if _roles_from_schema(schema) != list(REQUIRED_STACK_ROLES):
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: schema role order mismatch")
    if report.get("validation_marker") != PR73_SUCCESS_MARKER:
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: report marker mismatch")
    if report.get("required_stack_roles_order_valid") is not True:
        failures.append("PR73_ROLE_TAXONOMY_DEPENDENCY_BLOCK: report role order invalid")
    return list(roles if isinstance(roles, list) else REQUIRED_STACK_ROLES), failures


def validate_pr74_dependency(
    root: pathlib.Path,
    pr73_roles: Sequence[str],
) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    for label, rel_path in (
        ("PR74_COMPLETENESS_GATE_SCHEMA", PR74_SCHEMA),
        ("PR74_COMPLETENESS_GATE_REGISTRY", PR74_GATE),
        ("PR74_COMPLETENESS_GATE_REPORT", PR74_REPORT),
        ("PR74_COMPLETENESS_GATE_VALIDATOR", PR74_VALIDATOR),
    ):
        if not (root / rel_path).exists():
            failures.append(f"PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: {label} missing")
    if failures:
        return list(REQUIRED_STACK_ROLES), failures

    schema = load_json(root / PR74_SCHEMA)
    gate = load_yaml(root / PR74_GATE)
    report = load_json(root / PR74_REPORT)
    roles = gate.get("required_stack_roles")
    if roles != list(pr73_roles):
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: PR74 role order differs from PR73")
    if _roles_from_schema(schema) != list(pr73_roles):
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: PR74 schema role order differs from PR73")
    if report.get("validation_marker") != PR74_SUCCESS_MARKER:
        failures.append("PR74_COMPLETENESS_GATE_VALIDATION_BLOCK: report marker mismatch")
    if report.get("required_stack_roles_order_valid") is not True:
        failures.append("PR74_COMPLETENESS_GATE_VALIDATION_BLOCK: report role order invalid")

    completed = subprocess.run(
        [sys.executable, str(root / PR74_VALIDATOR)],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0 or PR74_SUCCESS_MARKER not in completed.stdout:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        failures.append(
            "PR74_COMPLETENESS_GATE_VALIDATION_BLOCK: validator did not emit "
            f"{PR74_SUCCESS_MARKER}; stdout={stdout!r}; stderr={stderr!r}"
        )
    return list(roles if isinstance(roles, list) else REQUIRED_STACK_ROLES), failures


def validate_required_roles(
    payload: dict[str, Any],
    expected_roles: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    roles = payload.get("required_stack_roles")
    if roles != list(expected_roles):
        failures.append(f"{label}.required_stack_roles must match PR73/PR74 order")
    if len(roles if isinstance(roles, list) else []) != len(REQUIRED_STACK_ROLES):
        failures.append(f"{label}.required_stack_roles must contain nine roles")
    unknown = sorted(set(roles if isinstance(roles, list) else []) - set(expected_roles))
    if unknown:
        failures.append(f"{label}.required_stack_roles unknown role IDs: {unknown}")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = schema.get("required")
    if not isinstance(required, list):
        return ["PR75 schema root required must be a list"]
    for field in SCHEMA_REQUIRED_FIELDS:
        if field not in required:
            failures.append(f"PR75 schema missing required root field {field}")

    defs = _mapping(schema.get("$defs"))
    contract_required = _mapping(defs.get("role_interface_contract")).get("required")
    for field in (
        "role_id",
        "consumes_interfaces",
        "produces_interfaces",
        "required_authority_class",
        "allowed_upstream_roles",
        "allowed_downstream_roles",
        "forbidden_downstream_authorities",
        "source_fact_dependency_allowed",
        "accepted_source_packet_required_for_external_fact",
        "connector_semantic_dependency_allowed",
        "connector_semantic_requires_accepted_source_packet",
        "runtime_artifact_dependency_allowed",
        "live_order_authority_allowed",
        "quantum_backend_execution_allowed",
        "profit_evidence_created",
        "compatibility_notes",
    ):
        if field not in (contract_required if isinstance(contract_required, list) else []):
            failures.append(f"PR75 schema role_interface_contract missing {field}")

    case_schema = _mapping(defs.get("compatibility_case"))
    case_required = case_schema.get("required")
    if not isinstance(case_required, list):
        failures.append("PR75 schema compatibility_case required must be a list")
    else:
        for field in COMPATIBILITY_CASE_REQUIRED_FIELDS:
            if field not in case_required:
                failures.append(f"PR75 schema compatibility_case missing required field {field}")
    state_enum = _mapping(_mapping(case_schema.get("properties")).get("compatibility_state")).get("enum")
    if state_enum != list(COMPATIBILITY_STATES):
        failures.append("PR75 schema compatibility_state enum mismatch")
    no_claim_required = _mapping(defs.get("no_claim_flags")).get("required")
    if no_claim_required != list(NO_CLAIM_FIELDS):
        failures.append("PR75 schema no_claim_flags required field order mismatch")
    return failures


def _contracts_by_role(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item.get("role_id"): item
        for item in _list_of_mappings(payload.get("role_interface_contracts"))
        if isinstance(item.get("role_id"), str)
    }


def validate_role_interface_contracts(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    contracts = _list_of_mappings(payload.get("role_interface_contracts"))
    role_ids = [contract.get("role_id") for contract in contracts]
    if role_ids != list(REQUIRED_STACK_ROLES):
        failures.append(f"{label}.role_interface_contracts role order mismatch")
    counts = Counter(role_ids)
    duplicates = sorted(role_id for role_id, count in counts.items() if count > 1)
    if duplicates:
        failures.append(f"{label}.role_interface_contracts duplicate roles: {duplicates}")
    unknown = sorted(set(role_ids) - set(REQUIRED_STACK_ROLES))
    if unknown:
        failures.append(f"{label}.role_interface_contracts unknown roles: {unknown}")

    by_role = _contracts_by_role(payload)
    for role_id in REQUIRED_STACK_ROLES:
        contract = by_role.get(role_id)
        if contract is None:
            failures.append(f"{label}.role_interface_contracts missing {role_id}")
            continue
        expected = EXPECTED_ROLE_INTERFACE_CONTRACTS[role_id]
        if contract != expected:
            failures.append(f"{label}.{role_id} role interface contract drifted")
        if contract.get("runtime_artifact_dependency_allowed") is not False:
            failures.append(f"{label}.{role_id} runtime artifact dependency must be false")
        if contract.get("live_order_authority_allowed") is not False:
            failures.append(f"{label}.{role_id} live order authority must be false")
        if contract.get("quantum_backend_execution_allowed") is not False:
            failures.append(f"{label}.{role_id} quantum backend execution must be false")
        if contract.get("profit_evidence_created") is not False:
            failures.append(f"{label}.{role_id} profit evidence must be false")

    signal_produces = set(_mapping(by_role.get("SIGNAL")).get("produces_interfaces", []))
    if "order_authority_interface" in signal_produces or "order_authority" in signal_produces:
        failures.append(f"{label}.SIGNAL cannot produce order authority")
    scoring_forbidden = set(_mapping(by_role.get("SCORING")).get("forbidden_downstream_authorities", []))
    if not {"stack_ranking_authority", "stack_selection_authority"}.issubset(scoring_forbidden):
        failures.append(f"{label}.SCORING must forbid ranking and selection")
    normalization_forbidden = set(_mapping(by_role.get("NORMALIZATION")).get("forbidden_downstream_authorities", []))
    if not {"connector_semantic_authority", "source_fact_fabrication_authority"}.issubset(normalization_forbidden):
        failures.append(f"{label}.NORMALIZATION must forbid source fact and connector semantic authority")
    risk_forbidden = set(_mapping(by_role.get("RISK")).get("forbidden_downstream_authorities", []))
    for authority in (
        "order_submission_authority",
        "order_cancel_authority",
        "order_replace_authority",
        "order_reduce_authority",
        "order_close_authority",
    ):
        if authority not in risk_forbidden:
            failures.append(f"{label}.RISK missing forbidden authority {authority}")
    execution_forbidden = set(_mapping(by_role.get("EXECUTION")).get("forbidden_downstream_authorities", []))
    if "order_authority" not in execution_forbidden:
        failures.append(f"{label}.EXECUTION must forbid order authority")
    capital_forbidden = set(_mapping(by_role.get("CAPITAL")).get("forbidden_downstream_authorities", []))
    if not {"cash_receipt_authority", "private_state_fetch_authority"}.issubset(capital_forbidden):
        failures.append(f"{label}.CAPITAL must forbid cash receipts and private state fetches")
    latency_forbidden = set(_mapping(by_role.get("LATENCY")).get("forbidden_downstream_authorities", []))
    if "latency_superiority_claim_authority" not in latency_forbidden:
        failures.append(f"{label}.LATENCY must forbid latency superiority claims")
    guard_forbidden = set(_mapping(by_role.get("ERROR_GUARD")).get("forbidden_downstream_authorities", []))
    if not {"blocker_bypass_authority", "silent_bypass_authority"}.issubset(guard_forbidden):
        failures.append(f"{label}.ERROR_GUARD must forbid bypass authority")
    quantum_forbidden = set(_mapping(by_role.get("QUANTUM_ADVISORY")).get("forbidden_downstream_authorities", []))
    if not {
        "quantum_backend_execution_authority",
        "optimizer_arbitration_authority",
        "stack_scoring_authority",
        "stack_ranking_authority",
        "stack_selection_authority",
        "quantum_advantage_claim_authority",
    }.issubset(quantum_forbidden):
        failures.append(f"{label}.QUANTUM_ADVISORY must forbid backend arbitration scoring ranking selection and advantage authority")
    return failures


def validate_owner_override_policy(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("owner_override_policy"))
    if policy.get("owner_override_supported") is not True:
        failures.append(f"{label}.owner_override_supported must be true")
    if policy.get("owner_override_satisfies_internal_stack_compatibility_only") is not True:
        failures.append(
            f"{label}.owner_override_satisfies_internal_stack_compatibility_only must be true"
        )
    for field in OWNER_OVERRIDE_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_quantum_compatibility_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("quantum_compatibility_policy"))
    true_fields = (
        "quantum_advisory_role_required_for_normal_completeness",
        "quantum_advisory_role_required_for_normal_compatibility",
        "quantum_advisory_static_compatibility_metadata_only",
        "true_quantum_metadata_supported_for_future_gates",
        "quantum_inspired_metadata_supported_for_future_gates",
        "hybrid_classical_quantum_metadata_supported_for_future_gates",
        "qubo_compatible_metadata_supported_for_future_gates",
        "ising_compatible_metadata_supported_for_future_gates",
        "qaoa_compatible_metadata_supported_for_future_gates",
        "vqe_compatible_metadata_supported_for_future_gates",
        "annealing_compatible_metadata_supported_for_future_gates",
        "quantum_portfolio_optimization_compatible_metadata_supported_for_future_gates",
        "owner_quantum_priority_metadata_supported_for_future_gates",
        "owner_forced_quantum_metadata_supported_for_future_gates",
        "hybrid_compare_then_quantum_tiebreak_metadata_supported_for_future_gates",
        "strongest_classical_comparator_required",
        "fallback_bundle_required",
        "future_quantum_applicability_registry_required_before_quantum_selection",
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection",
        "future_optimizer_arbitration_gate_required_before_optimizer_choice",
        "replay_paper_evidence_required_before_advantage_claim",
        "live_evidence_required_before_profit_claim",
    )
    false_fields = (
        "quantum_backend_execution_created",
        "quantum_advantage_claim_created",
        "quantum_scoring_created",
        "quantum_ranking_created",
        "quantum_selection_created",
        "quantum_arbitration_created",
    )
    for field in true_fields:
        if policy.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in false_fields:
        if policy.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_source_evidence_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("source_evidence_boundary_policy"))
    expected = {
        "source_retrieval_created": False,
        "source_acceptance_created": False,
        "accepted_source_packets_created": False,
        "owner_policy_may_authorize_retrieval_scope": True,
        "owner_policy_may_authorize_external_fact_value": False,
        "external_fact_requires_accepted_source_packet": True,
        "source_fact_boundary_violation_blocks_normal_compatibility": True,
    }
    for field, value in expected.items():
        if policy.get(field) is not value:
            failures.append(f"{label}.{field} must be {value}")
    return failures


def validate_connector_semantic_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("connector_semantic_boundary_policy"))
    expected = {
        "connector_semantics_created": False,
        "connector_semantic_binding_created": False,
        "connector_unlock_requires_accepted_target_field_packet": True,
        "connector_unlock_requires_fresh_revalidation_state": True,
        "connector_unlock_requires_target_field_scope_match": True,
        "retrieval_receipt_does_not_unlock_connector_semantics": True,
        "candidate_source_packet_does_not_unlock_connector_semantics": True,
        "owner_source_definitions_packet_does_not_unlock_connector_semantics": True,
    }
    for field, value in expected.items():
        if policy.get(field) is not value:
            failures.append(f"{label}.{field} must be {value}")
    return failures


def validate_runtime_live_order_boundary(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    policy = _mapping(payload.get("runtime_live_order_boundary_policy"))
    expected = {
        "runtime_artifacts_created": False,
        "live_readiness_created": False,
        "runtime_live_use_created": False,
        "private_state_fetch_created": False,
        "order_authority_created": False,
        "cash_receipts_created": False,
        "order_receipts_created": False,
        "fill_receipts_created": False,
        "profit_evidence_created": False,
        "execution_router_remains_future_final_order_submission_authority": True,
        "compatibility_gate_creates_order_authority": False,
    }
    for field, value in expected.items():
        if policy.get(field) is not value:
            failures.append(f"{label}.{field} must be {value}")
    return failures


def validate_future_consumer_contract(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    contract = _mapping(payload.get("future_consumer_contract"))
    true_fields = (
        "edge_parameter_stack_selection_packet_schema_may_consume",
        "trade_context_packet_schema_may_consume",
        "selection_universe_registry_may_consume",
        "trade_context_to_selection_universe_routing_gate_may_consume",
        "quantum_applicability_classification_registry_may_consume",
        "owner_quantum_priority_policy_registry_may_consume",
        "scoring_policy_registry_may_consume",
        "stack_scoring_ranking_gate_may_consume",
        "optimizer_arbitration_gate_may_consume",
        "candidate_stack_generation_gate_may_consume",
        "trade_context_stack_selection_gate_may_consume",
        "replay_paper_candidate_stack_competition_gate_may_consume",
    )
    false_fields = (
        "this_gate_performs_completeness",
        "this_gate_performs_scoring",
        "this_gate_performs_ranking",
        "this_gate_performs_selection",
        "this_gate_performs_arbitration",
        "this_gate_routes_trade_context",
        "this_gate_executes_replay_or_paper",
        "this_gate_executes_runtime_or_live",
    )
    for field in true_fields:
        if contract.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in false_fields:
        if contract.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    return failures


def validate_no_forbidden_claim_flags(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    explicit = _mapping(payload.get("explicit_no_claim_flags"))
    for field in EXPLICIT_NO_CLAIM_FIELDS:
        if explicit.get(field) is not False:
            failures.append(f"{label}.explicit_no_claim_flags.{field} must be false")
    forbidden = _mapping(payload.get("forbidden_artifact_flags"))
    for field in NO_CLAIM_FIELDS:
        if forbidden.get(field) is not False:
            failures.append(f"{label}.forbidden_artifact_flags.{field} must be false")
    return failures


def validate_production_gate(
    production_gate: dict[str, Any],
    schema: dict[str, Any],
    expected_roles: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    failures.extend(_schema_subset_failures(production_gate, schema, "production_gate"))
    if production_gate.get("gate_id") != GATE_ID:
        failures.append("production_gate.gate_id mismatch")
    if production_gate.get("gate_version") != GATE_VERSION:
        failures.append("production_gate.gate_version mismatch")
    if production_gate.get("authority_class") != AUTHORITY_CLASS:
        failures.append("production_gate.authority_class mismatch")
    if production_gate.get("compatibility_cases") != []:
        failures.append("production_gate.compatibility_cases must be empty")
    failures.extend(validate_required_roles(production_gate, expected_roles, "production_gate"))
    failures.extend(validate_role_interface_contracts(production_gate, "production_gate"))
    failures.extend(validate_owner_override_policy(production_gate, "production_gate"))
    failures.extend(validate_quantum_compatibility_boundary(production_gate, "production_gate"))
    failures.extend(validate_source_evidence_boundary(production_gate, "production_gate"))
    failures.extend(validate_connector_semantic_boundary(production_gate, "production_gate"))
    failures.extend(validate_runtime_live_order_boundary(production_gate, "production_gate"))
    failures.extend(validate_future_consumer_contract(production_gate, "production_gate"))
    failures.extend(validate_no_forbidden_claim_flags(production_gate, "production_gate"))

    policy = _mapping(production_gate.get("compatibility_policy"))
    for field in (
        "upstream_completeness_required_for_normal_compatibility",
        "all_required_role_interfaces_required_for_normal_compatibility",
        "missing_interface_blocks_normal_compatibility",
        "interface_mismatch_blocks_normal_compatibility",
        "duplicate_interface_blocks_normal_compatibility",
        "incompatible_authority_transition_blocks_normal_compatibility",
        "source_fact_boundary_violation_blocks_normal_compatibility",
        "connector_semantic_boundary_violation_blocks_normal_compatibility",
        "runtime_live_order_boundary_violation_blocks_normal_compatibility",
        "quantum_boundary_violation_blocks_normal_compatibility",
        "owner_override_may_satisfy_internal_stack_compatibility",
    ):
        if policy.get(field) is not True:
            failures.append(f"production_gate.compatibility_policy.{field} must be true")
    for field in (
        "owner_override_creates_external_fact",
        "owner_override_creates_runtime_authority",
        "owner_override_creates_live_authority",
        "final_ready_created_by_this_gate",
    ):
        if policy.get(field) is not False:
            failures.append(f"production_gate.compatibility_policy.{field} must be false")
    readiness = _mapping(production_gate.get("production_readiness"))
    expected_readiness = {
        "compatibility_gate_contract_ready": True,
        "production_compatible_stack_count": 0,
        "production_incompatible_stack_count": 0,
        "production_owner_override_satisfied_stack_count": 0,
        "production_stack_compatibility_evaluated": False,
        "production_stack_compatible": False,
        "production_stack_ready": False,
        "final_ready": False,
    }
    for field, value in expected_readiness.items():
        if readiness.get(field) != value:
            failures.append(f"production_gate.production_readiness.{field} must be {value!r}")
    if production_gate.get("final_ready") is not False:
        failures.append("production_gate.final_ready must be false")
    return failures


def _case_by_id(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case.get("stack_case_id"): case
        for case in _list_of_mappings(fixture.get("compatibility_cases"))
        if isinstance(case.get("stack_case_id"), str)
    }


def _case_common_failures(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in CASE_FALSE_FIELDS:
        if case.get(field) is not False:
            failures.append(f"{case.get('stack_case_id')}.{field} must be false")
    for field in NO_CLAIM_FIELDS:
        if _mapping(case.get("no_claim_flags")).get(field) is not False:
            failures.append(f"{case.get('stack_case_id')}.no_claim_flags.{field} must be false")
    roles = case.get("supplied_role_ids")
    unknown = sorted(set(roles if isinstance(roles, list) else []) - set(REQUIRED_STACK_ROLES))
    if unknown:
        failures.append(f"{case.get('stack_case_id')} has unknown roles {unknown}")
    trace = _mapping(case.get("deterministic_trace"))
    for field in (
        "random_selection_used",
        "ranking_used",
        "scoring_used",
        "optimizer_arbitration_used",
        "trade_context_routing_used",
        "stack_selection_used",
        "candidate_stack_generation_used",
        "runtime_evaluation_used",
    ):
        if trace.get(field) is not False:
            failures.append(f"{case.get('stack_case_id')}.deterministic_trace.{field} must be false")
    return failures


def _case_state_failures(
    case: dict[str, Any],
    *,
    state: str,
    boundary_field: str | None = None,
    normal: str = "NORMAL_STACK_BLOCKED",
) -> list[str]:
    failures: list[str] = []
    case_id = str(case.get("stack_case_id"))
    if case.get("compatibility_state") != state:
        failures.append(f"{case_id} compatibility_state must be {state}")
    if case.get("normal_stack_compatibility") != normal:
        failures.append(f"{case_id} normal_stack_compatibility must be {normal}")
    if state == OWNER_OVERRIDE_INTERNAL_ONLY:
        if case.get("owner_override_present") is not True:
            failures.append(f"{case_id} owner override must be present")
        if case.get("owner_override_satisfaction_basis") != OWNER_GLOBAL_OVERRIDE:
            failures.append(f"{case_id} owner override basis must be OWNER_GLOBAL_OVERRIDE")
        if case.get("owner_override_stack_compatibility") != "OWNER_OVERRIDE_INTERNAL_STACK_COMPATIBILITY_SATISFIED":
            failures.append(f"{case_id} owner override compatibility must be internally satisfied")
    elif state == "COMPATIBILITY_COMPLETE":
        if case.get("owner_override_present") is not False:
            failures.append(f"{case_id} owner override must not be present")
        if case.get("owner_override_stack_compatibility") != "OWNER_OVERRIDE_NOT_REQUIRED":
            failures.append(f"{case_id} owner override compatibility must be not required")
    else:
        if case.get("owner_override_present") is not False:
            failures.append(f"{case_id} owner override must not be present")
        if case.get("owner_override_stack_compatibility") != "OWNER_OVERRIDE_NOT_PRESENT":
            failures.append(f"{case_id} owner override compatibility must be not present")
    if boundary_field and not case.get(boundary_field):
        failures.append(f"{case_id}.{boundary_field} must contain a blocking entry")
    return failures


def validate_fixture_cases(
    fixture: dict[str, Any],
    schema: dict[str, Any],
    expected_roles: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    failures.extend(_schema_subset_failures(fixture, schema, "fixture"))
    failures.extend(validate_required_roles(fixture, expected_roles, "fixture"))
    failures.extend(validate_role_interface_contracts(fixture, "fixture"))
    failures.extend(validate_owner_override_policy(fixture, "fixture"))
    failures.extend(validate_quantum_compatibility_boundary(fixture, "fixture"))
    failures.extend(validate_source_evidence_boundary(fixture, "fixture"))
    failures.extend(validate_connector_semantic_boundary(fixture, "fixture"))
    failures.extend(validate_runtime_live_order_boundary(fixture, "fixture"))
    failures.extend(validate_future_consumer_contract(fixture, "fixture"))
    failures.extend(validate_no_forbidden_claim_flags(fixture, "fixture"))
    if fixture.get("fixture_id") != "SYNTHETIC_ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_FIXTURE":
        failures.append("fixture.fixture_id mismatch")
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")

    cases = _case_by_id(fixture)
    if list(cases) != list(REQUIRED_CASE_IDS):
        failures.append("fixture compatibility case order or IDs mismatch")
    for case in cases.values():
        failures.extend(_case_common_failures(case))

    compatible = _mapping(cases.get("SYNTHETIC_ROLE_COMPLETE_ALL_INTERFACES_COMPATIBLE"))
    failures.extend(
        _case_state_failures(
            compatible,
            state="COMPATIBILITY_COMPLETE",
            normal="NORMAL_STACK_COMPATIBLE",
        )
    )
    if compatible.get("supplied_role_ids") != list(REQUIRED_STACK_ROLES):
        failures.append("compatible case supplied_role_ids must match canonical order")
    if compatible.get("role_complete") is not True:
        failures.append("compatible case must be role complete")
    if compatible.get("role_interface_bindings") != list(EXPECTED_COMPATIBLE_BINDINGS):
        failures.append("compatible case interface bindings must match expected contracts")

    upstream = _mapping(cases.get("SYNTHETIC_UPSTREAM_ROLE_INCOMPLETE_BLOCKS_COMPATIBILITY"))
    failures.extend(
        _case_state_failures(
            upstream,
            state="COMPATIBILITY_BLOCKED_UPSTREAM_ROLE_INCOMPLETE",
        )
    )
    if upstream.get("upstream_completeness_state") != "ROLE_INCOMPLETE_MISSING_REQUIRED_ROLE":
        failures.append("upstream incomplete case must carry upstream incomplete state")
    if upstream.get("role_complete") is not False:
        failures.append("upstream incomplete case must not be role complete")

    missing = _mapping(cases.get("SYNTHETIC_MISSING_SIGNAL_OUTPUT_INTERFACE_BLOCKS_SCORING"))
    failures.extend(
        _case_state_failures(
            missing,
            state="COMPATIBILITY_INCOMPLETE_MISSING_INTERFACE",
            boundary_field="missing_interface_ids",
        )
    )
    if missing.get("missing_interface_ids") != ["signal_candidate_interface"]:
        failures.append("missing interface case must identify signal_candidate_interface")

    mismatch = _mapping(cases.get("SYNTHETIC_SCORING_CONSUMES_WRONG_SIGNAL_INTERFACE"))
    failures.extend(
        _case_state_failures(
            mismatch,
            state="COMPATIBILITY_INCOMPLETE_INTERFACE_MISMATCH",
            boundary_field="mismatched_interface_ids",
        )
    )

    duplicate = _mapping(cases.get("SYNTHETIC_DUPLICATE_NORMALIZED_CANDIDATE_INTERFACE_BINDING"))
    failures.extend(
        _case_state_failures(
            duplicate,
            state="COMPATIBILITY_INCOMPLETE_DUPLICATE_INTERFACE",
            boundary_field="duplicate_interface_ids",
        )
    )

    authority = _mapping(cases.get("SYNTHETIC_SIGNAL_PRODUCES_ORDER_AUTHORITY"))
    failures.extend(
        _case_state_failures(
            authority,
            state="COMPATIBILITY_INCOMPATIBLE_AUTHORITY_TRANSITION",
            boundary_field="incompatible_authority_transitions",
        )
    )

    source = _mapping(cases.get("SYNTHETIC_NORMALIZATION_SOURCE_FACT_WITHOUT_ACCEPTED_PACKET"))
    failures.extend(
        _case_state_failures(
            source,
            state="COMPATIBILITY_INCOMPATIBLE_SOURCE_FACT_BOUNDARY",
            boundary_field="source_fact_boundary_violations",
        )
    )

    connector = _mapping(cases.get("SYNTHETIC_EXECUTION_CONNECTOR_SEMANTIC_WITHOUT_ACCEPTED_PACKET"))
    failures.extend(
        _case_state_failures(
            connector,
            state="COMPATIBILITY_INCOMPATIBLE_CONNECTOR_SEMANTIC_BOUNDARY",
            boundary_field="connector_semantic_boundary_violations",
        )
    )

    for case_id in (
        "SYNTHETIC_EXECUTION_ATTEMPTS_LIVE_ORDER_AUTHORITY",
        "SYNTHETIC_CAPITAL_ATTEMPTS_RUNTIME_CASH_RECEIPT",
        "SYNTHETIC_LATENCY_ATTEMPTS_LATENCY_SUPERIORITY_CLAIM",
    ):
        case = _mapping(cases.get(case_id))
        failures.extend(
            _case_state_failures(
                case,
                state="COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY",
                boundary_field="runtime_live_order_boundary_violations",
            )
        )

    for case_id in (
        "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_BACKEND_EXECUTION",
        "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_ADVANTAGE_CLAIM",
        "SYNTHETIC_QUANTUM_ADVISORY_MISSING_FUTURE_APPLICABILITY_METADATA",
    ):
        case = _mapping(cases.get(case_id))
        failures.extend(
            _case_state_failures(
                case,
                state="COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY",
                boundary_field="quantum_boundary_violations",
            )
        )

    for case_id in (
        "SYNTHETIC_MISSING_INTERFACE_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_QUANTUM_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_SOURCE_FACT_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_CONNECTOR_SEMANTIC_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
        "SYNTHETIC_RUNTIME_ORDER_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE",
    ):
        case = _mapping(cases.get(case_id))
        failures.extend(_case_state_failures(case, state=OWNER_OVERRIDE_INTERNAL_ONLY))
        if case_id == "SYNTHETIC_QUANTUM_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE":
            if not case.get("quantum_boundary_violations"):
                failures.append(f"{case_id} must retain blocked quantum boundary trace")
            if _mapping(case.get("no_claim_flags")).get("quantum_backend_evidence_created") is not False:
                failures.append(f"{case_id} must not create quantum backend evidence")
            if _mapping(case.get("no_claim_flags")).get("quantum_advantage_claim_created") is not False:
                failures.append(f"{case_id} must not create quantum advantage claim")
        if case_id == "SYNTHETIC_SOURCE_FACT_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE":
            if _mapping(case.get("no_claim_flags")).get("source_fact_value_created") is not False:
                failures.append(f"{case_id} must not fabricate external facts")
        if case_id == "SYNTHETIC_CONNECTOR_SEMANTIC_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE":
            if _mapping(case.get("no_claim_flags")).get("connector_semantics_created") is not False:
                failures.append(f"{case_id} must not create connector semantics")
        if case_id == "SYNTHETIC_RUNTIME_ORDER_BOUNDARY_WITH_OWNER_GLOBAL_OVERRIDE":
            for field in (
                "runtime_artifacts_created",
                "runtime_live_use_created",
                "order_authority_created",
                "cash_receipts_created",
            ):
                if _mapping(case.get("no_claim_flags")).get(field) is not False:
                    failures.append(f"{case_id} must not create {field}")
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
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR75"]
    stderr = completed.stderr.strip()
    return [f"MASTER_PLAN_DIFF_CHECK_FAILED: {stderr}"]


def _flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("explicit_no_claim_flags")).get(field))


def _owner_flag(payload: dict[str, Any], field: str) -> bool:
    return bool(_mapping(payload.get("owner_override_policy")).get(field))


def _policy_flag(payload: dict[str, Any], policy_name: str, field: str) -> bool:
    return bool(_mapping(payload.get(policy_name)).get(field))


def _case(fixture: dict[str, Any], case_id: str) -> dict[str, Any]:
    return _mapping(_case_by_id(fixture).get(case_id))


def build_report(
    *,
    root: pathlib.Path,
    production_gate: dict[str, Any],
    fixture: dict[str, Any],
    schema_path: pathlib.Path,
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    readiness = _mapping(production_gate.get("production_readiness"))
    policy = _mapping(production_gate.get("compatibility_policy"))
    quantum_policy = _mapping(production_gate.get("quantum_compatibility_policy"))
    complete = _case(fixture, "SYNTHETIC_ROLE_COMPLETE_ALL_INTERFACES_COMPATIBLE")
    upstream = _case(fixture, "SYNTHETIC_UPSTREAM_ROLE_INCOMPLETE_BLOCKS_COMPATIBILITY")
    missing = _case(fixture, "SYNTHETIC_MISSING_SIGNAL_OUTPUT_INTERFACE_BLOCKS_SCORING")
    mismatch = _case(fixture, "SYNTHETIC_SCORING_CONSUMES_WRONG_SIGNAL_INTERFACE")
    duplicate = _case(fixture, "SYNTHETIC_DUPLICATE_NORMALIZED_CANDIDATE_INTERFACE_BINDING")
    authority = _case(fixture, "SYNTHETIC_SIGNAL_PRODUCES_ORDER_AUTHORITY")
    source = _case(fixture, "SYNTHETIC_NORMALIZATION_SOURCE_FACT_WITHOUT_ACCEPTED_PACKET")
    connector = _case(fixture, "SYNTHETIC_EXECUTION_CONNECTOR_SEMANTIC_WITHOUT_ACCEPTED_PACKET")
    runtime = _case(fixture, "SYNTHETIC_EXECUTION_ATTEMPTS_LIVE_ORDER_AUTHORITY")
    quantum = _case(fixture, "SYNTHETIC_QUANTUM_ADVISORY_ATTEMPTS_BACKEND_EXECUTION")
    return {
        "accepted_source_packets_created": _policy_flag(
            production_gate,
            "source_evidence_boundary_policy",
            "accepted_source_packets_created",
        ) or _flag(production_gate, "creates_accepted_source_packets"),
        "all_required_role_interfaces_required_for_normal_compatibility": policy.get(
            "all_required_role_interfaces_required_for_normal_compatibility"
        ),
        "all_role_interface_contracts_present": (
            [contract.get("role_id") for contract in _list_of_mappings(
                production_gate.get("role_interface_contracts")
            )] == list(REQUIRED_STACK_ROLES)
        ),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "candidate_stack_generation_created": _flag(
            production_gate, "creates_candidate_stack_generation"
        ),
        "cash_receipts_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "cash_receipts_created"
        ) or _flag(production_gate, "creates_cash_receipts"),
        "compatibility_gate_contract_ready": readiness.get("compatibility_gate_contract_ready"),
        "complete_compatible_case_passes": (
            complete.get("compatibility_state") == "COMPATIBILITY_COMPLETE"
            and complete.get("normal_stack_compatibility") == "NORMAL_STACK_COMPATIBLE"
        ),
        "connector_semantic_binding_created": _policy_flag(
            production_gate,
            "connector_semantic_boundary_policy",
            "connector_semantic_binding_created",
        ) or _flag(production_gate, "creates_connector_semantic_binding"),
        "connector_semantic_boundary_violation_blocks_normal_compatibility": (
            connector.get("compatibility_state")
            == "COMPATIBILITY_INCOMPATIBLE_CONNECTOR_SEMANTIC_BOUNDARY"
            and connector.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "connector_semantics_created": _policy_flag(
            production_gate,
            "connector_semantic_boundary_policy",
            "connector_semantics_created",
        ) or _flag(production_gate, "creates_connector_semantics"),
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "duplicate_interface_blocks_normal_compatibility": (
            duplicate.get("compatibility_state")
            == "COMPATIBILITY_INCOMPLETE_DUPLICATE_INTERFACE"
            and duplicate.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "execution_superiority_claim_created": _flag(
            production_gate, "creates_execution_superiority_claim"
        ),
        "fill_receipts_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "fill_receipts_created"
        ) or _flag(production_gate, "creates_fill_receipts"),
        "final_ready": production_gate.get("final_ready"),
        "fixture_path": _as_posix(fixture_path),
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": quantum_policy.get(
            "future_optimizer_arbitration_gate_required_before_optimizer_choice"
        ),
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": quantum_policy.get(
            "future_owner_quantum_priority_policy_required_before_quantum_priority_selection"
        ),
        "future_quantum_applicability_registry_required_before_quantum_selection": quantum_policy.get(
            "future_quantum_applicability_registry_required_before_quantum_selection"
        ),
        "incompatible_authority_transition_blocks_normal_compatibility": (
            authority.get("compatibility_state")
            == "COMPATIBILITY_INCOMPATIBLE_AUTHORITY_TRANSITION"
            and authority.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "interface_mismatch_blocks_normal_compatibility": (
            mismatch.get("compatibility_state")
            == "COMPATIBILITY_INCOMPLETE_INTERFACE_MISMATCH"
            and mismatch.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "latency_superiority_claim_created": _flag(
            production_gate, "creates_latency_superiority_claim"
        ),
        "live_evidence_required_before_profit_claim": quantum_policy.get(
            "live_evidence_required_before_profit_claim"
        ),
        "live_readiness_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "live_readiness_created"
        ) or _flag(production_gate, "creates_live_readiness"),
        "missing_interface_blocks_normal_compatibility": (
            missing.get("compatibility_state") == "COMPATIBILITY_INCOMPLETE_MISSING_INTERFACE"
            and missing.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "optimizer_arbitration_created": _flag(
            production_gate, "creates_optimizer_arbitration"
        ),
        "order_authority_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "order_authority_created"
        ) or _flag(production_gate, "creates_order_authority"),
        "order_receipts_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "order_receipts_created"
        ) or _flag(production_gate, "creates_order_receipts"),
        "owner_override_fabricates_accepted_source_packet": _owner_flag(
            production_gate, "owner_override_fabricates_accepted_source_packet"
        ),
        "owner_override_fabricates_connector_semantic": _owner_flag(
            production_gate, "owner_override_fabricates_connector_semantic"
        ),
        "owner_override_fabricates_external_fact": _owner_flag(
            production_gate, "owner_override_fabricates_external_fact"
        ),
        "owner_override_fabricates_order_receipt": _owner_flag(
            production_gate, "owner_override_fabricates_order_receipt"
        ),
        "owner_override_fabricates_profit_evidence": _owner_flag(
            production_gate, "owner_override_fabricates_profit_evidence"
        ),
        "owner_override_fabricates_quantum_backend_execution": _owner_flag(
            production_gate, "owner_override_fabricates_quantum_backend_execution"
        ),
        "owner_override_fabricates_replay_paper_result": _owner_flag(
            production_gate, "owner_override_fabricates_replay_paper_result"
        ),
        "owner_override_fabricates_runtime_cash_receipt": _owner_flag(
            production_gate, "owner_override_fabricates_runtime_cash_receipt"
        ),
        "owner_override_satisfies_internal_stack_compatibility_only": _mapping(
            production_gate.get("owner_override_policy")
        ).get("owner_override_satisfies_internal_stack_compatibility_only"),
        "paper_results_created": _flag(production_gate, "creates_paper_results"),
        "private_state_fetch_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "private_state_fetch_created"
        ) or _flag(production_gate, "creates_private_state_fetch"),
        "production_gate_path": _as_posix(production_gate_path),
        "production_stack_compatibility_evaluated": readiness.get(
            "production_stack_compatibility_evaluated"
        ),
        "production_stack_compatible": readiness.get("production_stack_compatible"),
        "production_stack_ready": readiness.get("production_stack_ready"),
        "profit_evidence_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "profit_evidence_created"
        ) or _flag(production_gate, "creates_profit_evidence"),
        "quantum_advisory_static_compatibility_metadata_only": quantum_policy.get(
            "quantum_advisory_static_compatibility_metadata_only"
        ),
        "quantum_advantage_claim_created": _mapping(
            production_gate.get("quantum_compatibility_policy")
        ).get("quantum_advantage_claim_created") or _flag(
            production_gate, "creates_quantum_advantage_claim"
        ),
        "quantum_backend_evidence_created": _flag(
            production_gate, "creates_quantum_backend_evidence"
        ),
        "quantum_boundary_violation_blocks_normal_compatibility": (
            quantum.get("compatibility_state")
            == "COMPATIBILITY_INCOMPATIBLE_QUANTUM_BOUNDARY"
            and quantum.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "ranking_created": _flag(production_gate, "creates_ranking"),
        "replay_paper_evidence_required_before_advantage_claim": quantum_policy.get(
            "replay_paper_evidence_required_before_advantage_claim"
        ),
        "replay_results_created": _flag(production_gate, "creates_replay_results"),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "required_stack_role_count": len(production_gate.get("required_stack_roles", [])),
        "required_stack_roles_order_valid": production_gate.get("required_stack_roles")
        == list(REQUIRED_STACK_ROLES),
        "role_interface_contract_count": len(
            _list_of_mappings(production_gate.get("role_interface_contracts"))
        ),
        "runtime_artifacts_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "runtime_artifacts_created"
        ) or _flag(production_gate, "creates_runtime_artifacts"),
        "runtime_live_order_boundary_violation_blocks_normal_compatibility": (
            runtime.get("compatibility_state")
            == "COMPATIBILITY_INCOMPATIBLE_RUNTIME_LIVE_ORDER_BOUNDARY"
            and runtime.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "runtime_live_use_created": _policy_flag(
            production_gate, "runtime_live_order_boundary_policy", "runtime_live_use_created"
        ) or _flag(production_gate, "creates_runtime_live_use"),
        "schema_path": _as_posix(schema_path),
        "scoring_created": _flag(production_gate, "creates_scoring"),
        "source_acceptance_created": _policy_flag(
            production_gate, "source_evidence_boundary_policy", "source_acceptance_created"
        ) or _flag(production_gate, "accepts_source_facts"),
        "source_fact_boundary_violation_blocks_normal_compatibility": (
            source.get("compatibility_state")
            == "COMPATIBILITY_INCOMPATIBLE_SOURCE_FACT_BOUNDARY"
            and source.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
        "source_retrieval_created": _policy_flag(
            production_gate, "source_evidence_boundary_policy", "source_retrieval_created"
        ) or _flag(production_gate, "retrieves_source_facts"),
        "stack_selection_created": _flag(production_gate, "creates_stack_selection"),
        "trade_context_routing_created": _flag(
            production_gate, "creates_trade_context_routing"
        ),
        "upstream_completeness_required_for_normal_compatibility": policy.get(
            "upstream_completeness_required_for_normal_compatibility"
        ),
        "upstream_incomplete_blocks_normal_compatibility": (
            upstream.get("compatibility_state")
            == "COMPATIBILITY_BLOCKED_UPSTREAM_ROLE_INCOMPLETE"
            and upstream.get("normal_stack_compatibility") == "NORMAL_STACK_BLOCKED"
        ),
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
        "depends_on_pr73_role_taxonomy": True,
        "depends_on_pr74_completeness_gate": True,
        "required_stack_role_count": len(REQUIRED_STACK_ROLES),
        "required_stack_roles_order_valid": True,
        "role_interface_contract_count": len(REQUIRED_STACK_ROLES),
        "all_role_interface_contracts_present": True,
        "compatibility_gate_contract_ready": True,
        "upstream_completeness_required_for_normal_compatibility": True,
        "all_required_role_interfaces_required_for_normal_compatibility": True,
        "complete_compatible_case_passes": True,
        "upstream_incomplete_blocks_normal_compatibility": True,
        "missing_interface_blocks_normal_compatibility": True,
        "interface_mismatch_blocks_normal_compatibility": True,
        "duplicate_interface_blocks_normal_compatibility": True,
        "incompatible_authority_transition_blocks_normal_compatibility": True,
        "source_fact_boundary_violation_blocks_normal_compatibility": True,
        "connector_semantic_boundary_violation_blocks_normal_compatibility": True,
        "runtime_live_order_boundary_violation_blocks_normal_compatibility": True,
        "quantum_boundary_violation_blocks_normal_compatibility": True,
        "owner_override_satisfies_internal_stack_compatibility_only": True,
        "quantum_advisory_static_compatibility_metadata_only": True,
        "future_quantum_applicability_registry_required_before_quantum_selection": True,
        "future_owner_quantum_priority_policy_required_before_quantum_priority_selection": True,
        "future_optimizer_arbitration_gate_required_before_optimizer_choice": True,
        "replay_paper_evidence_required_before_advantage_claim": True,
        "live_evidence_required_before_profit_claim": True,
        "validation_marker": SUCCESS_MARKER,
    }
    for field in REPORT_FALSE_FIELDS:
        expected_values[field] = False
    if not isinstance(report.get("atomicrows_bundle_jsonl_exists"), bool):
        failures.append("report.atomicrows_bundle_jsonl_exists must be boolean")
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
    production_gate_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    pr73_roles, pr73_failures = validate_pr73_dependency(root)
    failures.extend(pr73_failures)
    pr74_roles, pr74_failures = validate_pr74_dependency(root, pr73_roles)
    failures.extend(pr74_failures)
    if pr74_roles != pr73_roles:
        failures.append("PR74_COMPLETENESS_GATE_DEPENDENCY_BLOCK: PR74 roles differ from PR73")

    schema, schema_failures = _load_json_checked(root / schema_path, "PR75_SCHEMA")
    failures.extend(schema_failures)
    if schema:
        failures.extend(validate_schema_required_fields(schema))

    try:
        production_gate = load_yaml(root / production_gate_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR75_PRODUCTION_GATE_MALFORMED: {exc}"]),
            report=None,
        )
    try:
        fixture = load_json(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(
            failures=tuple(failures + [f"PR75_FIXTURE_MALFORMED: {exc}"]),
            report=None,
        )

    if schema:
        failures.extend(validate_production_gate(production_gate, schema, pr74_roles))
        failures.extend(validate_fixture_cases(fixture, schema, pr74_roles))
    else:
        failures.extend(validate_required_roles(production_gate, pr74_roles, "production_gate"))
        failures.extend(validate_required_roles(fixture, pr74_roles, "fixture"))

    artifact_texts = (
        (_as_posix(schema_path), _read_text(root / schema_path)),
        (_as_posix(production_gate_path), _read_text(root / production_gate_path)),
        (_as_posix(fixture_path), _read_text(root / fixture_path)),
    )
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        root=root,
        production_gate=production_gate,
        fixture=fixture,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        root=root,
        production_gate=production_gate,
        fixture=fixture,
        schema_path=schema_path,
        production_gate_path=production_gate_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR75 report is not deterministic")
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
