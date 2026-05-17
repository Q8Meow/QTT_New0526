#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

from tools import (  # noqa: E402
    validate_atomicrows_owner_submitted_research_source_intake_registry as pr71_gate,
)
from tools import (  # noqa: E402
    validate_atomicrows_research_provenance_evidence_tier_classification as pr70_gate,
)
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
    / "atomicrows_research_source_to_candidate_family_gate.schema.json"
)
DEFAULT_GATE = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsResearchSourceToCandidateFamilyGate.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_research_source_to_candidate_family_gate.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
)
DEFAULT_PR70_SCHEMA = pr70_gate.DEFAULT_SCHEMA
DEFAULT_PR70_REGISTRY = pr70_gate.DEFAULT_REGISTRY
DEFAULT_PR70_REPORT = pr70_gate.DEFAULT_REPORT
DEFAULT_PR71_SCHEMA = pr71_gate.DEFAULT_SCHEMA
DEFAULT_PR71_REGISTRY = pr71_gate.DEFAULT_REGISTRY
DEFAULT_PR71_REPORT = pr71_gate.DEFAULT_REPORT

CANONICAL_BUNDLE_JSONL = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA256 = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)
MASTER_PLAN_CURRENT = (
    pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
)

GATE_ID = "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE"
GATE_VERSION = "v1"
REPORT_ID = "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_REPORT"
REPORT_VERSION = "v1"
VALIDATOR_NAME = "validate_atomicrows_research_source_to_candidate_family_gate.py"
AUTHORITY_CLASS = (
    "STATIC_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_NOT_SOURCE_FACT_NOT_"
    "ACCEPTED_PACKET_NOT_ATOMICROWS_BUNDLE_NOT_RUNTIME_AUTHORITY"
)
REPORT_AUTHORITY_CLASS = (
    "STATIC_VALIDATION_REPORT_NOT_SOURCE_FACT_NOT_ACCEPTED_PACKET_NOT_"
    "ATOMICROWS_BUNDLE_NOT_RUNTIME_AUTHORITY"
)
SUCCESS_MARKER = "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_OK"
FAILURE_MARKER = "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_FINAL_INCOMPLETE"
)
SYNTHETIC_LOCATOR = "SYNTHETIC_LOCATOR_NO_EXTERNAL_FETCH"
SYNTHETIC_INTAKE_PREFIX = "SYNTHETIC-OSRSIR-"
SYNTHETIC_PACKET_PREFIXES = (
    "SYNTHETIC-CANDIDATE-PARAMETER-FAMILY-PACKET-",
    "SYNTHETIC-CANDIDATE-ALGORITHM-FAMILY-PACKET-",
    "SYNTHETIC-CANDIDATE-AGENT-BINDING-REQUEST-",
    "SYNTHETIC-OWNER-OVERRIDE-RECEIPT-REFERENCE-",
)

CANONICAL_SOURCE_TYPES = tuple(pr70_gate.CANONICAL_SOURCE_TYPES)
CANDIDATE_ROUTES_SUPPORTED = (
    "RESEARCH_ARCHIVE_ONLY",
    "PR72_PARAMETER_FAMILY_CANDIDATE_REVIEW",
    "PR72_ALGORITHM_FAMILY_CANDIDATE_REVIEW",
    "PR72_AGENT_BINDING_REQUEST_REVIEW",
    "PR72_OWNER_OVERRIDE_RECEIPT_REFERENCE_REVIEW",
    "RETRIEVAL_TARGET_REVIEW_ONLY",
    "OWNER_REVIEW_REQUIRED",
    "BLOCKED_NO_OWNER_APPROVAL",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE",
)
OUTPUT_PACKET_TYPES = (
    "candidate_parameter_family_packet",
    "candidate_algorithm_family_packet",
    "candidate_agent_binding_request",
    "owner_override_receipt_reference",
)
QUANTUM_ROUTES_SUPPORTED = (
    "NONE",
    "QUANTUM_RESEARCH_REVIEW",
    "QUANTUM_OPTIMIZER_CANDIDATE_REVIEW",
    "TRUE_QUANTUM_REVIEW",
    "QUANTUM_INSPIRED_REVIEW",
    "HYBRID_CLASSICAL_QUANTUM_REVIEW",
    "QUBO_COMPATIBILITY_REVIEW",
    "ISING_COMPATIBILITY_REVIEW",
    "QAOA_COMPATIBILITY_REVIEW",
    "VQE_COMPATIBILITY_REVIEW",
    "ANNEALING_COMPATIBILITY_REVIEW",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_REVIEW",
    "OWNER_FORCED_QUANTUM_REVIEW",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE",
)
TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED = (
    "OWNER_UNSET_PENDING_REVIEW",
    "NONE",
    "TRUE_QUANTUM_OPTIMIZER",
    "QUANTUM_INSPIRED_OPTIMIZER",
    "HYBRID_CLASSICAL_QUANTUM_OPTIMIZER",
    "QUBO_COMPATIBLE_ALGORITHM",
    "ISING_COMPATIBLE_ALGORITHM",
    "QAOA_COMPATIBLE_ALGORITHM",
    "VQE_COMPATIBLE_ALGORITHM",
    "ANNEALING_COMPATIBLE_ALGORITHM",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_ALGORITHM",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_FAMILY",
)
FUTURE_QUANTUM_FLAGS_SUPPORTED = (
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
OWNER_OVERRIDE_SATISFACTION_BASES = (
    "OWNER_UNSET",
    "OWNER_APPROVED",
    "OWNER_GLOBAL_OVERRIDE",
    "OWNER_OVERRIDE_SATISFIED",
    "OWNER_APPROVED_OVERRIDE",
    "SYNTHETIC_NOT_REAL_OWNER_APPROVAL",
)
NO_CLAIM_FIELDS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "accepted_source_packets_created",
    "connector_semantics_created",
    "runtime_artifacts_created",
    "live_readiness_created",
    "order_authority_created",
    "cash_receipts_created",
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
    "runtime_live_use_created",
)
FORBIDDEN_ARTIFACT_FLAG_FIELDS = (
    "source_retrieval",
    "source_acceptance",
    "accepted_source_packets",
    "connector_semantics",
    "runtime_artifacts",
    "runtime_receipts",
    "live_receipts",
    "order_receipts",
    "cash_receipts",
    "replay_results",
    "paper_results",
    "live_readiness",
    "order_authority",
    "profit_evidence",
    "quantum_backend_evidence",
    "quantum_advantage_claim",
    "latency_superiority_claim",
    "execution_superiority_claim",
    "atomicrows_bundle_rows",
    "atomicrows_bundle_jsonl",
    "atomicrows_bundle_sha256",
    "ranking",
    "scoring",
    "optimizer_arbitration",
    "trade_context_routing",
    "runtime_live_use",
)
TOP_LEVEL_FALSE_FIELDS = (
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_packets",
    "creates_connector_semantics",
    "creates_runtime_artifacts",
    "creates_atomicrows_bundle_rows",
    "creates_atomicrows_bundle_jsonl",
    "creates_atomicrows_bundle_sha256",
    "creates_replay_results",
    "creates_paper_results",
    "creates_live_readiness",
    "creates_order_authority",
    "creates_cash_receipts",
    "creates_profit_evidence",
    "creates_quantum_backend_evidence",
    "creates_quantum_advantage_claim",
    "creates_latency_superiority_claim",
    "creates_execution_superiority_claim",
    "creates_ranking",
    "creates_scoring",
    "creates_optimizer_arbitration",
    "creates_trade_context_routing",
    "creates_runtime_or_live_trading_authority",
    "implements_random_selection",
    "implements_stack_selection",
    "real_candidate_outputs_invented",
    "production_conversion_ready",
    "final_ready",
)
TOP_LEVEL_TRUE_FIELDS = (
    "synthetic_fixture_only",
    "conversion_gate_contract_ready",
)
OWNER_OVERRIDE_TRUE_FIELDS = (
    "owner_override_supported",
    "owner_override_satisfaction_basis_supported",
    "owner_override_satisfies_internal_workflow_only",
)
OWNER_OVERRIDE_FALSE_FIELDS = (
    "owner_override_fabricates_external_fact",
    "owner_override_fabricates_accepted_source_packet",
    "owner_override_fabricates_runtime_cash_receipt",
    "owner_override_fabricates_order_receipt",
    "owner_override_fabricates_replay_paper_result",
    "owner_override_fabricates_quantum_backend_execution",
    "owner_override_fabricates_profit_evidence",
)
PRODUCTION_OUTPUT_ARRAY_FIELDS = (
    "candidate_parameter_family_packets",
    "candidate_algorithm_family_packets",
    "candidate_agent_binding_requests",
    "owner_override_receipt_references",
)
COUNT_FIELDS_BY_OUTPUT = {
    "candidate_parameter_family_packets": "candidate_parameter_family_packet_count",
    "candidate_algorithm_family_packets": "candidate_algorithm_family_packet_count",
    "candidate_agent_binding_requests": "candidate_agent_binding_request_count",
    "owner_override_receipt_references": "owner_override_receipt_reference_count",
}
PACKET_DEF_BY_OUTPUT = {
    "candidate_parameter_family_packets": "candidate_parameter_family_packet",
    "candidate_algorithm_family_packets": "candidate_algorithm_family_packet",
    "candidate_agent_binding_requests": "candidate_agent_binding_request",
    "owner_override_receipt_references": "owner_override_receipt_reference",
}
PACKET_ID_FIELD_BY_TYPE = {
    "candidate_parameter_family_packet": "candidate_parameter_family_packet_id",
    "candidate_algorithm_family_packet": "candidate_algorithm_family_packet_id",
    "candidate_agent_binding_request": "candidate_agent_binding_request_id",
    "owner_override_receipt_reference": "owner_override_receipt_reference_id",
}
ROUTE_TO_OUTPUT_TYPE = {
    "PR72_PARAMETER_FAMILY_CANDIDATE_REVIEW": "candidate_parameter_family_packet",
    "PR72_ALGORITHM_FAMILY_CANDIDATE_REVIEW": "candidate_algorithm_family_packet",
    "PR72_AGENT_BINDING_REQUEST_REVIEW": "candidate_agent_binding_request",
    "PR72_OWNER_OVERRIDE_RECEIPT_REFERENCE_REVIEW": (
        "owner_override_receipt_reference"
    ),
}
NO_OUTPUT_ROUTES = {
    "RESEARCH_ARCHIVE_ONLY",
    "RETRIEVAL_TARGET_REVIEW_ONLY",
    "OWNER_REVIEW_REQUIRED",
    "BLOCKED_NO_OWNER_APPROVAL",
    "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE",
}

CONVERSION_RULES = (
    {
        "candidate_route": "PR72_PARAMETER_FAMILY_CANDIDATE_REVIEW",
        "produced_output_packet_type": "candidate_parameter_family_packet",
        "produces_candidate_packet": True,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "PR72_ALGORITHM_FAMILY_CANDIDATE_REVIEW",
        "produced_output_packet_type": "candidate_algorithm_family_packet",
        "produces_candidate_packet": True,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "PR72_AGENT_BINDING_REQUEST_REVIEW",
        "produced_output_packet_type": "candidate_agent_binding_request",
        "produces_candidate_packet": True,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "PR72_OWNER_OVERRIDE_RECEIPT_REFERENCE_REVIEW",
        "produced_output_packet_type": "owner_override_receipt_reference",
        "produces_candidate_packet": True,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "RESEARCH_ARCHIVE_ONLY",
        "produced_output_packet_type": None,
        "produces_candidate_packet": False,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "RETRIEVAL_TARGET_REVIEW_ONLY",
        "produced_output_packet_type": None,
        "produces_candidate_packet": False,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "OWNER_REVIEW_REQUIRED",
        "produced_output_packet_type": None,
        "produces_candidate_packet": False,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "BLOCKED_NO_OWNER_APPROVAL",
        "produced_output_packet_type": None,
        "produces_candidate_packet": False,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
    {
        "candidate_route": "SYNTHETIC_FIXTURE_ONLY_NOT_REAL_ROUTE",
        "produced_output_packet_type": None,
        "produces_candidate_packet": False,
        "production_requires_owner_approval_or_override": True,
        "synthetic_fixture_only_allowed": True,
    },
)
VALIDATION_INVARIANTS = (
    "Production candidate outputs must be empty while owner intake production entries are empty.",
    "Production output counts must match production output arrays.",
    "Supported source types must exactly match the provenance classifier.",
    "Candidate routes must exactly match the route universe.",
    "Output packet types must exactly match the four roadmap output types.",
    "Source acceptance must not be created.",
    "Runtime live order profit and quantum backend authority must not be created.",
    "AtomicRows bundle rows must not be created.",
    "Ranking scoring arbitration and trade context routing must not be implemented.",
)
GATE_REQUIRED_FIELDS = (
    "gate_id",
    "gate_version",
    "authority_class",
    "depends_on_research_provenance_classifier",
    "depends_on_owner_submitted_research_source_intake_registry",
    "supported_source_types",
    "supported_candidate_routes",
    "output_packet_types",
    "conversion_rules",
    "quantum_forward_conversion_policy",
    "production_input_summary",
    "production_outputs",
    "forbidden_artifact_flags",
    *TOP_LEVEL_FALSE_FIELDS[:23],
    "implements_random_selection",
    "implements_stack_selection",
    "owner_override_policy",
    "validation_invariants",
    "candidate_parameter_family_packet_count",
    "candidate_algorithm_family_packet_count",
    "candidate_agent_binding_request_count",
    "owner_override_receipt_reference_count",
    "real_candidate_outputs_invented",
    "synthetic_fixture_only",
    "conversion_gate_contract_ready",
    "production_conversion_ready",
    "final_ready",
)
CANDIDATE_PARAMETER_PACKET_FIELDS = (
    "candidate_parameter_family_packet_id",
    "packet_type",
    "source_intake_id",
    "source_type",
    "source_locator_reference",
    "owner_note_reference",
    "research_hypothesis",
    "target_parameter_family",
    "candidate_status",
    "candidate_authority_class",
    "candidate_route",
    "source_evidence_acceptance_required_before_use",
    "atomicrows_bundle_creation_allowed",
    "runtime_use_allowed",
    "replay_paper_required_before_promotion",
    "owner_approved",
    "owner_override_satisfaction_basis",
    "owner_override_internal_workflow_only",
    "external_fact_fabrication_allowed",
    "quantum_relevance_requested",
    "quantum_route_requested",
    "target_quantum_algorithm_family",
    "owner_quantum_priority_requested",
    "deterministic_trace",
    "no_claim_flags",
)
CANDIDATE_ALGORITHM_PACKET_FIELDS = (
    "candidate_algorithm_family_packet_id",
    "packet_type",
    "source_intake_id",
    "source_type",
    "source_locator_reference",
    "owner_note_reference",
    "research_hypothesis",
    "target_algorithm_family",
    "candidate_status",
    "candidate_authority_class",
    "candidate_route",
    "source_evidence_acceptance_required_before_use",
    "algorithm_binding_authority_created",
    "runtime_use_allowed",
    "replay_paper_required_before_promotion",
    "owner_approved",
    "owner_override_satisfaction_basis",
    "owner_override_internal_workflow_only",
    "external_fact_fabrication_allowed",
    "quantum_relevance_requested",
    "quantum_route_requested",
    "target_quantum_algorithm_family",
    "owner_quantum_priority_requested",
    "deterministic_trace",
    "no_claim_flags",
)
CANDIDATE_AGENT_BINDING_REQUEST_FIELDS = (
    "candidate_agent_binding_request_id",
    "packet_type",
    "source_intake_id",
    "target_agent_role",
    "target_parameter_family",
    "target_algorithm_family",
    "binding_request_status",
    "request_authority_class",
    "candidate_route",
    "binding_created",
    "consumer_gate_bypass_created",
    "runtime_use_allowed",
    "owner_approved",
    "owner_override_satisfaction_basis",
    "owner_override_internal_workflow_only",
    "external_fact_fabrication_allowed",
    "quantum_relevance_requested",
    "quantum_route_requested",
    "target_quantum_algorithm_family",
    "owner_quantum_priority_requested",
    "deterministic_trace",
    "no_claim_flags",
)
OWNER_OVERRIDE_RECEIPT_REFERENCE_FIELDS = (
    "owner_override_receipt_reference_id",
    "packet_type",
    "source_intake_id",
    "owner_approved",
    "owner_override_satisfaction_basis",
    "owner_override_reference_status",
    "reference_authority_class",
    "receipt_created_by_this_gate",
    "owner_override_internal_workflow_only",
    "external_fact_fabrication_allowed",
    "accepted_source_packet_fabrication_allowed",
    "runtime_cash_receipt_fabrication_allowed",
    "order_receipt_fabrication_allowed",
    "replay_paper_result_fabrication_allowed",
    "quantum_backend_execution_fabrication_allowed",
    "profit_evidence_fabrication_allowed",
    "deterministic_trace",
    "no_claim_flags",
)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_posix(path: pathlib.Path | str) -> str:
    return pathlib.Path(path).as_posix()


def _read_text_if_exists(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return load_yaml_subset(path)


def load_fixture(path: pathlib.Path) -> dict[str, Any]:
    return load_json(path)


def _load_json_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_DEPENDENCY_MISSING: JSON file is missing: {path}"]
    try:
        return load_json(path), []
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"{label}_DEPENDENCY_MALFORMED: JSON file is invalid: {path}: {exc}"]


def _require_exact_keys(
    value: dict[str, Any],
    expected_fields: Sequence[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    expected = set(expected_fields)
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
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


def _pr70_source_types_from_registry(registry: dict[str, Any]) -> list[str]:
    ids = registry.get("source_type_ids_canonical_order")
    if isinstance(ids, list):
        return [str(item) for item in ids]
    entries = registry.get("source_types")
    if isinstance(entries, list):
        return [
            str(entry.get("source_type"))
            for entry in entries
            if isinstance(entry, dict) and entry.get("source_type") is not None
        ]
    return []


def _schema_enum(schema: dict[str, Any], def_name: str) -> list[str]:
    enum_value = _mapping(_mapping(schema.get("$defs")).get(def_name)).get("enum")
    if not isinstance(enum_value, list):
        return []
    return [str(item) for item in enum_value if item is not None]


def validate_pr70_dependency(
    *,
    repo_root: pathlib.Path,
    pr70_schema_path: pathlib.Path,
    pr70_registry_path: pathlib.Path,
    pr70_report_path: pathlib.Path,
) -> tuple[list[str], list[str]]:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json_checked(root / pr70_schema_path, "PR70_CLASSIFIER")
    report, report_failures = _load_json_checked(root / pr70_report_path, "PR70_CLASSIFIER")
    failures.extend(schema_failures)
    failures.extend(report_failures)
    try:
        registry = load_yaml(root / pr70_registry_path)
    except (OSError, RegistryParseError) as exc:
        failures.append(f"PR70_CLASSIFIER_DEPENDENCY_MALFORMED: registry is invalid: {exc}")
        registry = {}

    expected = list(CANONICAL_SOURCE_TYPES)
    observed = (
        ("schema", _schema_enum(schema or {}, "source_type_id")),
        ("registry", _pr70_source_types_from_registry(registry)),
        (
            "report",
            [str(item) for item in _mapping(report).get("source_type_ids", [])],
        ),
    )
    for label, source_types in observed:
        if source_types != expected:
            failures.append(
                f"PR70_SOURCE_TYPE_UNIVERSE_MISMATCH: {label} source types must match exactly"
            )
    if registry.get("source_type_count") != len(expected):
        failures.append("PR70_SOURCE_TYPE_COUNT_MISMATCH: registry count must be 14")
    expected_report_values = {
        "source_type_count": len(expected),
        "required_source_type_count": len(expected),
        "required_source_types_present_count": len(expected),
        "forbidden_source_type_boundary_true_count": 0,
        "source_retrieval_executed": False,
        "source_acceptance_executed": False,
        "accepted_source_packet_created": False,
        "connector_binding_created": False,
        "runtime_artifact_created": False,
        "live_artifact_created": False,
        "order_artifact_created": False,
        "profit_evidence_created": False,
        "latency_superiority_evidence_created": False,
        "execution_superiority_evidence_created": False,
        "quantum_advantage_evidence_created": False,
        "quantum_backend_artifact_created": False,
        "bundle_sha_present": False,
        "uses_pr_number_as_authority": False,
        "final_ready": False,
    }
    for field, expected_value in expected_report_values.items():
        if _mapping(report).get(field) != expected_value:
            failures.append(
                f"PR70_REPORT_INVARIANT_MISMATCH: report.{field} must be {expected_value!r}"
            )
    if not isinstance(_mapping(report).get("bundle_file_present"), bool):
        failures.append("PR70_REPORT_INVARIANT_MISMATCH: report.bundle_file_present must be boolean")
    return expected, failures


def validate_pr71_dependency(
    *,
    repo_root: pathlib.Path,
    pr71_schema_path: pathlib.Path,
    pr71_registry_path: pathlib.Path,
    pr71_report_path: pathlib.Path,
    pr70_source_types: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json_checked(
        root / pr71_schema_path, "PR71_INTAKE_REGISTRY"
    )
    report, report_failures = _load_json_checked(
        root / pr71_report_path, "PR71_INTAKE_REGISTRY"
    )
    failures.extend(schema_failures)
    failures.extend(report_failures)
    try:
        registry = load_yaml(root / pr71_registry_path)
    except (OSError, RegistryParseError) as exc:
        failures.append(f"PR71_INTAKE_REGISTRY_DEPENDENCY_MALFORMED: registry is invalid: {exc}")
        registry = {}

    if _schema_enum(schema or {}, "source_type_id") != list(pr70_source_types):
        failures.append("PR71_SOURCE_TYPE_UNIVERSE_MISMATCH: schema source types must match PR70")
    expected_registry_values = {
        "real_owner_intake_entry_count": 0,
        "intake_entries": [],
        "real_owner_intakes_invented": False,
        "synthetic_fixture_only": True,
        "final_ready": False,
    }
    for field, expected_value in expected_registry_values.items():
        if registry.get(field) != expected_value:
            failures.append(
                f"PR71_PRODUCTION_STATE_MISMATCH: registry.{field} must be {expected_value!r}"
            )
    if registry.get("supported_source_types") != list(pr70_source_types):
        failures.append("PR71_SUPPORTED_SOURCE_TYPES_MISMATCH: registry must match PR70")

    expected_report_values = {
        "depends_on_pr70_classifier": True,
        "pr70_source_type_count_observed": len(pr70_source_types),
        "production_intake_entries_count": 0,
        "real_owner_intake_entry_count": 0,
        "real_owner_intakes_invented": False,
        "synthetic_fixture_only": True,
        "fixture_contains_only_synthetic_entries": True,
        "final_ready": False,
        "validation_marker": pr71_gate.SUCCESS_MARKER,
    }
    for field, expected_value in expected_report_values.items():
        if _mapping(report).get(field) != expected_value:
            failures.append(
                f"PR71_REPORT_INVARIANT_MISMATCH: report.{field} must be {expected_value!r}"
            )
    return registry, report or {}, failures


def validate_supported_source_types(
    gate: dict[str, Any],
    schema: dict[str, Any],
    pr70_source_types: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    expected = list(pr70_source_types)
    if gate.get("supported_source_types") != expected:
        failures.append("SUPPORTED_SOURCE_TYPES_MISMATCH: gate must match PR70 exactly")
    if _schema_enum(schema, "source_type_id") != expected:
        failures.append("SCHEMA_SOURCE_TYPES_MISMATCH: schema must match PR70 exactly")
    return failures


def validate_candidate_routes(gate: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = list(CANDIDATE_ROUTES_SUPPORTED)
    if gate.get("supported_candidate_routes") != expected:
        failures.append("CANDIDATE_ROUTE_UNIVERSE_MISMATCH: gate route list is not canonical")
    if _schema_enum(schema, "candidate_route") != expected:
        failures.append("SCHEMA_CANDIDATE_ROUTE_UNIVERSE_MISMATCH: route enum is not canonical")
    return failures


def validate_output_packet_types(gate: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = list(OUTPUT_PACKET_TYPES)
    if gate.get("output_packet_types") != expected:
        failures.append("OUTPUT_PACKET_TYPES_MISMATCH: gate packet types are not canonical")
    if _schema_enum(schema, "output_packet_type") != expected:
        failures.append("SCHEMA_OUTPUT_PACKET_TYPES_MISMATCH: output packet enum is not canonical")
    return failures


def validate_schema_required_fields(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(GATE_REQUIRED_FIELDS):
        failures.append("schema.required must match PR72 gate required fields")
    defs = _mapping(schema.get("$defs"))
    expected_required = {
        "candidate_parameter_family_packet": CANDIDATE_PARAMETER_PACKET_FIELDS,
        "candidate_algorithm_family_packet": CANDIDATE_ALGORITHM_PACKET_FIELDS,
        "candidate_agent_binding_request": CANDIDATE_AGENT_BINDING_REQUEST_FIELDS,
        "owner_override_receipt_reference": OWNER_OVERRIDE_RECEIPT_REFERENCE_FIELDS,
        "no_claim_flags": NO_CLAIM_FIELDS,
    }
    for def_name, required_fields in expected_required.items():
        definition = _mapping(defs.get(def_name))
        if definition.get("additionalProperties") is not False:
            failures.append(f"schema.$defs.{def_name}.additionalProperties must be false")
        if definition.get("required") != list(required_fields):
            failures.append(f"schema.$defs.{def_name}.required must be exact")
    if _schema_enum(schema, "candidate_route") != list(CANDIDATE_ROUTES_SUPPORTED):
        failures.append("schema.$defs.candidate_route enum must be canonical")
    if _schema_enum(schema, "output_packet_type") != list(OUTPUT_PACKET_TYPES):
        failures.append("schema.$defs.output_packet_type enum must be canonical")
    if _schema_enum(schema, "quantum_route") != list(QUANTUM_ROUTES_SUPPORTED):
        failures.append("schema.$defs.quantum_route enum must be canonical")
    if _schema_enum(schema, "target_quantum_algorithm_family") != list(
        TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED
    ):
        failures.append("schema.$defs.target_quantum_algorithm_family enum must be canonical")
    return failures


def validate_production_outputs_empty(
    gate: dict[str, Any],
    *,
    pr71_registry: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    summary = _mapping(gate.get("production_input_summary"))
    outputs = _mapping(gate.get("production_outputs"))
    expected_summary = {
        "production_intake_entries_count": 0,
        "real_owner_intake_entry_count": 0,
        "intake_entries_empty": True,
        "real_owner_intakes_invented": False,
        "source_registry_synthetic_fixture_only": True,
    }
    if pr71_registry.get("intake_entries") != []:
        failures.append("PR71_INTAKE_NOT_EMPTY: PR72 production conversion must fail closed")
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            failures.append(f"PRODUCTION_INPUT_SUMMARY_MISMATCH: {field} must be {expected!r}")
    for output_field in PRODUCTION_OUTPUT_ARRAY_FIELDS:
        if outputs.get(output_field) != []:
            failures.append(f"PRODUCTION_OUTPUTS_NOT_EMPTY: {output_field} must be empty")
    expected_counts = {
        "candidate_parameter_family_packet_count": 0,
        "candidate_algorithm_family_packet_count": 0,
        "candidate_agent_binding_request_count": 0,
        "owner_override_receipt_reference_count": 0,
    }
    for field, expected in expected_counts.items():
        if gate.get(field) != expected:
            failures.append(f"PRODUCTION_OUTPUT_COUNT_MISMATCH: gate.{field} must be {expected}")
    return failures


def validate_count_consistency(gate: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    outputs = _mapping(gate.get("production_outputs"))
    for output_field, count_field in COUNT_FIELDS_BY_OUTPUT.items():
        value = outputs.get(output_field)
        if not isinstance(value, list):
            failures.append(f"COUNT_CONSISTENCY_FAILED: {output_field} must be a list")
            continue
        if gate.get(count_field) != len(value):
            failures.append(
                f"COUNT_CONSISTENCY_FAILED: {count_field} must match {output_field}"
            )
    return failures


def validate_gate_payload(
    gate: dict[str, Any],
    *,
    schema: dict[str, Any],
    pr70_source_types: Sequence[str],
    pr71_registry: dict[str, Any],
    production: bool,
) -> list[str]:
    failures: list[str] = []
    failures.extend(_require_exact_keys(gate, GATE_REQUIRED_FIELDS, "gate"))
    failures.extend(validate_json_schema_subset(gate, schema))
    if gate.get("gate_id") != GATE_ID:
        failures.append("gate.gate_id must be canonical")
    if gate.get("gate_version") != GATE_VERSION:
        failures.append("gate.gate_version must be v1")
    if gate.get("authority_class") != AUTHORITY_CLASS:
        failures.append("gate.authority_class must be canonical")
    expected_pr70_dependency = {
        "schema_path": _as_posix(DEFAULT_PR70_SCHEMA),
        "registry_path": _as_posix(DEFAULT_PR70_REGISTRY),
        "report_path": _as_posix(DEFAULT_PR70_REPORT),
    }
    expected_pr71_dependency = {
        "schema_path": _as_posix(DEFAULT_PR71_SCHEMA),
        "registry_path": _as_posix(DEFAULT_PR71_REGISTRY),
        "report_path": _as_posix(DEFAULT_PR71_REPORT),
    }
    if gate.get("depends_on_research_provenance_classifier") != expected_pr70_dependency:
        failures.append("PR70_DEPENDENCY_POINTER_MISMATCH: gate dependency paths must be canonical")
    if (
        gate.get("depends_on_owner_submitted_research_source_intake_registry")
        != expected_pr71_dependency
    ):
        failures.append("PR71_DEPENDENCY_POINTER_MISMATCH: gate dependency paths must be canonical")
    failures.extend(validate_supported_source_types(gate, schema, pr70_source_types))
    failures.extend(validate_candidate_routes(gate, schema))
    failures.extend(validate_output_packet_types(gate, schema))
    if gate.get("conversion_rules") != [dict(rule) for rule in CONVERSION_RULES]:
        failures.append("CONVERSION_RULES_MISMATCH: conversion rules must be canonical")
    quantum_policy = _mapping(gate.get("quantum_forward_conversion_policy"))
    expected_quantum_values = {
        "quantum_metadata_only": True,
        "supported_quantum_routes": list(QUANTUM_ROUTES_SUPPORTED),
        "target_quantum_algorithm_families_supported": list(
            TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED
        ),
        "future_quantum_flags_supported": list(FUTURE_QUANTUM_FLAGS_SUPPORTED),
        "quantum_backend_execution_created": False,
        "quantum_advantage_claim_created": False,
        "replay_paper_evidence_required_before_advantage_claim": True,
        "live_evidence_required_before_profit_claim": True,
    }
    for field, expected in expected_quantum_values.items():
        if quantum_policy.get(field) != expected:
            failures.append(f"QUANTUM_POLICY_MISMATCH: {field} must be {expected!r}")
    if gate.get("validation_invariants") != list(VALIDATION_INVARIANTS):
        failures.append("VALIDATION_INVARIANTS_MISMATCH: invariants must be canonical")
    for field in TOP_LEVEL_FALSE_FIELDS:
        if gate.get(field) is not False:
            failures.append(f"NO_CLAIM_FLAG_TRUE: gate.{field} must be false")
    for field in TOP_LEVEL_TRUE_FIELDS:
        if gate.get(field) is not True:
            failures.append(f"GATE_TRUE_INVARIANT_FALSE: gate.{field} must be true")
    flags = _mapping(gate.get("forbidden_artifact_flags"))
    failures.extend(_require_exact_keys(flags, FORBIDDEN_ARTIFACT_FLAG_FIELDS, "forbidden_artifact_flags"))
    for field in FORBIDDEN_ARTIFACT_FLAG_FIELDS:
        if flags.get(field) is not False:
            failures.append(f"FORBIDDEN_ARTIFACT_FLAG_TRUE: {field} must be false")
    policy = _mapping(gate.get("owner_override_policy"))
    failures.extend(
        _require_exact_keys(
            policy,
            (*OWNER_OVERRIDE_TRUE_FIELDS, *OWNER_OVERRIDE_FALSE_FIELDS),
            "owner_override_policy",
        )
    )
    for field in OWNER_OVERRIDE_TRUE_FIELDS:
        if policy.get(field) is not True:
            failures.append(f"OWNER_OVERRIDE_POLICY_MISMATCH: {field} must be true")
    for field in OWNER_OVERRIDE_FALSE_FIELDS:
        if policy.get(field) is not False:
            failures.append(f"OWNER_OVERRIDE_POLICY_MISMATCH: {field} must be false")
    failures.extend(validate_count_consistency(gate))
    if production:
        failures.extend(validate_production_outputs_empty(gate, pr71_registry=pr71_registry))
    return failures


def _fixture_cases(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(fixture.get("fixture_cases"))


def _fixture_conversion_case(fixture: dict[str, Any]) -> dict[str, Any]:
    for case in _fixture_cases(fixture):
        if case.get("case_id") == "SYNTHETIC_DETERMINISTIC_CONVERSION_CASE":
            return case
    return {}


def _fixture_entries(case: dict[str, Any]) -> list[dict[str, Any]]:
    return _list_of_mappings(case.get("synthetic_source_intake_entries"))


def _fixture_outputs(case: dict[str, Any]) -> dict[str, Any]:
    return _mapping(case.get("synthetic_outputs"))


def _all_fixture_output_packets(case: dict[str, Any]) -> list[dict[str, Any]]:
    outputs = _fixture_outputs(case)
    packets: list[dict[str, Any]] = []
    for output_field in PRODUCTION_OUTPUT_ARRAY_FIELDS:
        packets.extend(_list_of_mappings(outputs.get(output_field)))
    return packets


def validate_traceability_to_synthetic_intake(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    entries = _fixture_entries(case)
    intake_ids = {
        str(entry.get("source_intake_id"))
        for entry in entries
        if isinstance(entry.get("source_intake_id"), str)
    }
    for packet in _all_fixture_output_packets(case):
        packet_type = str(packet.get("packet_type"))
        packet_id_field = PACKET_ID_FIELD_BY_TYPE.get(packet_type, "")
        packet_id = str(packet.get(packet_id_field))
        source_intake_id = packet.get("source_intake_id")
        if source_intake_id not in intake_ids:
            failures.append(
                f"TRACEABILITY_FAILED: {packet_id} does not trace to synthetic intake"
            )
        trace = _mapping(packet.get("deterministic_trace"))
        if trace.get("source_intake_id") != source_intake_id:
            failures.append(f"TRACEABILITY_FAILED: {packet_id} trace source mismatch")
        if trace.get("deterministic_packet_id") != packet_id:
            failures.append(f"TRACEABILITY_FAILED: {packet_id} trace packet id mismatch")
        if not any(packet_id.startswith(prefix) for prefix in SYNTHETIC_PACKET_PREFIXES):
            failures.append(f"SYNTHETIC_PACKET_ID_REQUIRED: {packet_id}")
    return failures


def validate_no_output_claims(packet: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    no_claims = _mapping(packet.get("no_claim_flags"))
    failures.extend(_require_exact_keys(no_claims, NO_CLAIM_FIELDS, f"{label}.no_claim_flags"))
    for field in NO_CLAIM_FIELDS:
        if no_claims.get(field) is not False:
            failures.append(f"{label}.no_claim_flags.{field} must be false")
    trace = _mapping(packet.get("deterministic_trace"))
    for field in (
        "random_selection_used",
        "ranking_used",
        "scoring_used",
        "optimizer_arbitration_used",
        "trade_context_routing_used",
    ):
        if trace.get(field) is not False:
            failures.append(f"{label}.deterministic_trace.{field} must be false")
    packet_false_fields = (
        "external_fact_fabrication_allowed",
        "runtime_use_allowed",
        "atomicrows_bundle_creation_allowed",
        "algorithm_binding_authority_created",
        "binding_created",
        "consumer_gate_bypass_created",
        "receipt_created_by_this_gate",
        "accepted_source_packet_fabrication_allowed",
        "runtime_cash_receipt_fabrication_allowed",
        "order_receipt_fabrication_allowed",
        "replay_paper_result_fabrication_allowed",
        "quantum_backend_execution_fabrication_allowed",
        "profit_evidence_fabrication_allowed",
    )
    for field in packet_false_fields:
        if field in packet and packet.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if packet.get("owner_override_internal_workflow_only") is not True:
        failures.append(f"{label}.owner_override_internal_workflow_only must be true")
    return failures


def validate_synthetic_fixture_conversion(
    fixture: dict[str, Any],
    *,
    schema: dict[str, Any],
    pr70_source_types: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    expected_root_fields = (
        "fixture_id",
        "fixture_version",
        "mode",
        "execution",
        "fixture_cases",
    )
    failures.extend(_require_exact_keys(fixture, expected_root_fields, "fixture"))
    if fixture.get("mode") != "SOURCE_REQUIRED":
        failures.append("fixture.mode must be SOURCE_REQUIRED")
    if fixture.get("execution") != "DISABLED":
        failures.append("fixture.execution must be DISABLED")
    cases = _fixture_cases(fixture)
    if [case.get("case_id") for case in cases] != [
        "SYNTHETIC_EMPTY_PRODUCTION_GATE_CASE",
        "SYNTHETIC_DETERMINISTIC_CONVERSION_CASE",
    ]:
        failures.append("fixture cases must be in canonical order")
    if cases:
        empty_case = cases[0]
        if empty_case.get("synthetic_source_intake_entries") != []:
            failures.append("empty production fixture case must have no synthetic entries")
        if _mapping(empty_case.get("production_input_summary")).get(
            "production_intake_entries_count"
        ) != 0:
            failures.append("empty production fixture case count must be zero")
        empty_outputs = _mapping(empty_case.get("production_outputs"))
        for output_field in PRODUCTION_OUTPUT_ARRAY_FIELDS:
            if empty_outputs.get(output_field) != []:
                failures.append(f"empty production fixture {output_field} must be empty")

    case = _fixture_conversion_case(fixture)
    if not case:
        return failures + ["fixture conversion case is missing"]
    entries = _fixture_entries(case)
    outputs = _fixture_outputs(case)
    if len(entries) != 8:
        failures.append("synthetic conversion case must contain eight synthetic entries")
    entry_by_id: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries, start=1):
        label = f"synthetic_source_intake_entries[{index}]"
        failures.extend(_require_exact_keys(entry, pr71_gate.ENTRY_REQUIRED_FIELDS, label))
        source_intake_id = entry.get("source_intake_id")
        if not isinstance(source_intake_id, str) or not source_intake_id.startswith(
            SYNTHETIC_INTAKE_PREFIX
        ):
            failures.append(f"{label}.source_intake_id must be synthetic")
            continue
        if source_intake_id in entry_by_id:
            failures.append(f"{label}.source_intake_id is duplicated")
        entry_by_id[source_intake_id] = entry
        if entry.get("source_type") not in pr70_source_types:
            failures.append(f"{label}.source_type must be supported by PR70")
        if entry.get("source_locator") != SYNTHETIC_LOCATOR:
            failures.append(f"{label}.source_locator must be {SYNTHETIC_LOCATOR}")
        if entry.get("candidate_route") not in CANDIDATE_ROUTES_SUPPORTED:
            failures.append(f"{label}.candidate_route is unsupported")
        if entry.get("owner_approved") is not False:
            failures.append(f"{label}.owner_approved must be false")
        if entry.get("owner_override_satisfaction_basis") != "SYNTHETIC_NOT_REAL_OWNER_APPROVAL":
            failures.append(f"{label}.owner_override_satisfaction_basis must be synthetic")
        if entry.get("quantum_route_requested") not in QUANTUM_ROUTES_SUPPORTED:
            failures.append(f"{label}.quantum_route_requested is unsupported")
        if entry.get("target_quantum_algorithm_family") not in TARGET_QUANTUM_ALGORITHM_FAMILIES_SUPPORTED:
            failures.append(f"{label}.target_quantum_algorithm_family is unsupported")

    defs = _mapping(schema.get("$defs"))
    observed_counts: dict[str, int] = {}
    observed_by_source: dict[str, list[str]] = {}
    for output_field in PRODUCTION_OUTPUT_ARRAY_FIELDS:
        packets = _list_of_mappings(outputs.get(output_field))
        observed_counts[COUNT_FIELDS_BY_OUTPUT[output_field]] = len(packets)
        packet_schema = _mapping(defs.get(PACKET_DEF_BY_OUTPUT[output_field]))
        for index, packet in enumerate(packets, start=1):
            label = f"synthetic_outputs.{output_field}[{index}]"
            failures.extend(
                validate_json_schema_subset(packet, packet_schema, root_schema=schema, path=label)
            )
            failures.extend(validate_no_output_claims(packet, label))
            packet_type = packet.get("packet_type")
            source_intake_id = str(packet.get("source_intake_id"))
            observed_by_source.setdefault(source_intake_id, []).append(str(packet_type))
            route = packet.get("candidate_route")
            trace = _mapping(packet.get("deterministic_trace"))
            if route is None:
                route = trace.get("candidate_route")
            if packet_type != ROUTE_TO_OUTPUT_TYPE.get(str(route)):
                failures.append(f"{label} has packet type that does not match route")
            if trace.get("output_packet_type") != packet_type:
                failures.append(f"{label}.deterministic_trace.output_packet_type mismatch")

    expected_counts = _mapping(case.get("expected_output_counts"))
    for count_field, observed in observed_counts.items():
        if expected_counts.get(count_field) != observed:
            failures.append(f"SYNTHETIC_COUNT_MISMATCH: {count_field} must be {observed}")
    expected_ids = {
        "SYNTHETIC-CANDIDATE-PARAMETER-FAMILY-PACKET-001",
        "SYNTHETIC-CANDIDATE-ALGORITHM-FAMILY-PACKET-001",
        "SYNTHETIC-CANDIDATE-AGENT-BINDING-REQUEST-001",
        "SYNTHETIC-OWNER-OVERRIDE-RECEIPT-REFERENCE-001",
    }
    observed_ids = {
        str(packet.get(PACKET_ID_FIELD_BY_TYPE.get(str(packet.get("packet_type")), "")))
        for packet in _all_fixture_output_packets(case)
    }
    if observed_ids != expected_ids:
        failures.append("SYNTHETIC_PACKET_IDS_MISMATCH: deterministic packet IDs changed")

    route_expectations = _list_of_mappings(case.get("route_expectations"))
    for expectation in route_expectations:
        source_intake_id = str(expectation.get("source_intake_id"))
        route = str(expectation.get("candidate_route"))
        expected_packet_type = expectation.get("expected_output_packet_type")
        expected_count = expectation.get("expected_output_count")
        entry = entry_by_id.get(source_intake_id)
        if not entry:
            failures.append(f"ROUTE_EXPECTATION_MISSING_ENTRY: {source_intake_id}")
            continue
        if entry.get("candidate_route") != route:
            failures.append(f"ROUTE_EXPECTATION_MISMATCH: {source_intake_id} route mismatch")
        observed_types = observed_by_source.get(source_intake_id, [])
        if len(observed_types) != expected_count:
            failures.append(f"ROUTE_OUTPUT_COUNT_MISMATCH: {source_intake_id}")
        if expected_packet_type is None:
            if observed_types:
                failures.append(f"ROUTE_OUTPUT_UNAUTHORIZED: {source_intake_id}")
        elif observed_types != [expected_packet_type]:
            failures.append(f"ROUTE_OUTPUT_TYPE_MISMATCH: {source_intake_id}")
    for entry in entries:
        source_intake_id = str(entry.get("source_intake_id"))
        if entry.get("candidate_route") in NO_OUTPUT_ROUTES and source_intake_id in observed_by_source:
            failures.append(f"NO_OUTPUT_ROUTE_PRODUCED_PACKET: {source_intake_id}")

    failures.extend(validate_traceability_to_synthetic_intake(case))
    return failures


def fixture_contains_only_synthetic_entries(fixture: dict[str, Any]) -> bool:
    for case in _fixture_cases(fixture):
        for entry in _fixture_entries(case):
            if (
                not isinstance(entry.get("source_intake_id"), str)
                or not str(entry.get("source_intake_id")).startswith(SYNTHETIC_INTAKE_PREFIX)
                or entry.get("source_locator") != SYNTHETIC_LOCATOR
                or entry.get("owner_approved") is not False
                or entry.get("owner_override_satisfaction_basis")
                != "SYNTHETIC_NOT_REAL_OWNER_APPROVAL"
            ):
                return False
        for packet in _all_fixture_output_packets(case):
            packet_type = str(packet.get("packet_type"))
            packet_id = str(packet.get(PACKET_ID_FIELD_BY_TYPE.get(packet_type, "")))
            if not any(packet_id.startswith(prefix) for prefix in SYNTHETIC_PACKET_PREFIXES):
                return False
            if packet.get("owner_approved") is not False:
                return False
    return True


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
        ("ACCOUNT_BALANCE_CLAIM", "account" + " balance"),
        ("OPEN_ORDERS_CLAIM", "open" + " orders"),
        ("RUNTIME_CASH_CLAIM", "runtime" + " cash"),
        ("EXTERNAL_REPO_CLONE_COMMAND", "git" + " clone"),
        ("PACKAGE_INSTALL_COMMAND_PIP", "pip" + " install"),
        ("PACKAGE_INSTALL_COMMAND_NPM", "npm" + " install"),
        ("PACKAGE_INSTALL_COMMAND_UV", "uv" + " pip"),
        ("LIVE_ORDER_COMMAND_CLAIM", "live order" + " submitted"),
        ("ORDER_COMMAND_CANCEL", "cancel" + " order"),
        ("ORDER_COMMAND_REPLACE", "replace" + " order"),
        ("PROFIT_GUARANTEE_CLAIM", "guaranteed" + " profit"),
        ("PROFIT_RISK_FREE_CLAIM", "risk-free" + " profit"),
        ("QUANTUM_ADVANTAGE_PROOF_CLAIM", "quantum advantage" + " proven"),
        ("QUANTUM_BACKEND_EXECUTION_CLAIM", "backend" + " executed"),
        ("REPLAY_PROOF_CLAIM", "replay passed" + " as proof"),
        ("PAPER_PROOF_CLAIM", "paper passed" + " as proof"),
        ("SOURCE_ACCEPTANCE_CLAIM", "accepted source packet" + " created"),
        ("CONNECTOR_SEMANTIC_CLAIM", "connector semantic binding" + " created"),
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
        ("ORDER_FILL_CLAIM", re.compile(r"\bfills\b", re.IGNORECASE)),
    )


def forbidden_text_findings(texts: Sequence[tuple[str, str]]) -> dict[str, bool]:
    findings = {
        "real_urls_present": False,
        "real_source_claims_present": False,
        "secrets_present": False,
        "account_data_present": False,
        "external_repo_commands_present": False,
        "package_install_commands_present": False,
        "order_commands_present": False,
        "live_trading_commands_present": False,
        "forbidden_claims_present": False,
        "replay_paper_proof_claims_present": False,
        "profit_claims_present": False,
        "quantum_backend_evidence_claims_present": False,
        "quantum_advantage_claims_present": False,
    }
    url_codes = {"REAL_HTTP_LOCATOR", "REAL_HTTPS_LOCATOR", "REAL_WWW_LOCATOR"}
    secret_codes = {
        "SECRET_LIKE_API_KEY",
        "SECRET_LIKE_API_KEY_UNDERSCORE",
        "SECRET_LIKE_PRIVATE_KEY",
        "SECRET_LIKE_BEARER_TOKEN",
        "SECRET_LIKE_PASSWORD",
        "SECRET_LIKE_AWS_ACCESS_KEY",
    }
    account_codes = {
        "PRIVATE_ACCOUNT_STATE",
        "ACCOUNT_BALANCE_CLAIM",
        "OPEN_ORDERS_CLAIM",
        "ORDER_FILL_CLAIM",
    }
    source_claim_codes = {
        "SOURCE_ACCEPTANCE_CLAIM",
        "CONNECTOR_SEMANTIC_CLAIM",
        "ORDER_FILL_CLAIM",
    }
    package_codes = {
        "PACKAGE_INSTALL_COMMAND_PIP",
        "PACKAGE_INSTALL_COMMAND_NPM",
        "PACKAGE_INSTALL_COMMAND_UV",
    }
    order_codes = {
        "LIVE_ORDER_COMMAND_CLAIM",
        "ORDER_COMMAND_CANCEL",
        "ORDER_COMMAND_REPLACE",
        "OPEN_ORDERS_CLAIM",
        "ORDER_FILL_CLAIM",
    }
    live_codes = {"LIVE_ORDER_COMMAND_CLAIM", "LIVE_ELIGIBLE_CLAIM"}
    replay_paper_codes = {"REPLAY_PROOF_CLAIM", "PAPER_PROOF_CLAIM"}
    profit_codes = {"PROFIT_GUARANTEE_CLAIM", "PROFIT_RISK_FREE_CLAIM"}
    quantum_backend_codes = {"QUANTUM_BACKEND_EXECUTION_CLAIM"}
    quantum_advantage_codes = {"QUANTUM_ADVANTAGE_PROOF_CLAIM"}
    for _, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() not in lowered:
                continue
            findings["forbidden_claims_present"] = True
            findings["real_urls_present"] |= code in url_codes
            findings["secrets_present"] |= code in secret_codes
            findings["account_data_present"] |= code in account_codes
            findings["real_source_claims_present"] |= code in source_claim_codes
            findings["external_repo_commands_present"] |= code == "EXTERNAL_REPO_CLONE_COMMAND"
            findings["package_install_commands_present"] |= code in package_codes
            findings["order_commands_present"] |= code in order_codes
            findings["live_trading_commands_present"] |= code in live_codes
            findings["replay_paper_proof_claims_present"] |= code in replay_paper_codes
            findings["profit_claims_present"] |= code in profit_codes
            findings["quantum_backend_evidence_claims_present"] |= code in quantum_backend_codes
            findings["quantum_advantage_claims_present"] |= code in quantum_advantage_codes
        for code, pattern in _forbidden_text_regexes():
            if not pattern.search(text):
                continue
            findings["forbidden_claims_present"] = True
            findings["secrets_present"] |= code in secret_codes
            findings["account_data_present"] |= code in account_codes
            findings["real_source_claims_present"] |= code in source_claim_codes
            findings["order_commands_present"] |= code in order_codes
    return findings


def validate_no_forbidden_claims(texts: Sequence[tuple[str, str]]) -> list[str]:
    failures: list[str] = []
    for label, text in texts:
        lowered = text.lower()
        for code, pattern in _forbidden_text_patterns():
            if pattern.lower() in lowered:
                failures.append(f"{code}: forbidden text appears in {label}")
        for code, pattern in _forbidden_text_regexes():
            if pattern.search(text):
                failures.append(f"{code}: forbidden text appears in {label}")
    return failures


def validate_no_real_urls(texts: Sequence[tuple[str, str]]) -> list[str]:
    return [
        failure
        for failure in validate_no_forbidden_claims(texts)
        if "REAL_HTTP" in failure or "REAL_HTTPS" in failure or "REAL_WWW" in failure
    ]


def validate_no_secret_like_values(texts: Sequence[tuple[str, str]]) -> list[str]:
    secret_markers = ("SECRET_LIKE", "PRIVATE_ACCOUNT_STATE", "ACCOUNT_BALANCE")
    return [
        failure
        for failure in validate_no_forbidden_claims(texts)
        if any(marker in failure for marker in secret_markers)
    ]


def validate_no_forbidden_artifacts(repo_root: pathlib.Path) -> list[str]:
    root = repo_root.resolve()
    failures: list[str] = []
    if (root / CANONICAL_BUNDLE_SHA256).exists():
        failures.append(f"FORBIDDEN_ARTIFACT_EXISTS: {_as_posix(CANONICAL_BUNDLE_SHA256)}")
    return failures


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", _as_posix(MASTER_PLAN_CURRENT)],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return [
            "MASTER_PLAN_EDIT_GUARD_UNAVAILABLE: git diff failed: "
            + completed.stderr.strip()
        ]
    if completed.stdout.strip():
        return ["MASTER_PLAN_EDIT_FORBIDDEN_FOR_PR72"]
    return []


def _flag_from_gate(gate: dict[str, Any], field: str, *, default: bool = False) -> bool:
    return bool(gate.get(field, default))


def _flag_from_forbidden_flags(
    gate: dict[str, Any],
    field: str,
    *,
    default: bool = False,
) -> bool:
    return bool(_mapping(gate.get("forbidden_artifact_flags")).get(field, default))


def _synthetic_conversion_case_count(fixture: dict[str, Any]) -> int:
    return sum(
        1
        for case in _fixture_cases(fixture)
        if case.get("case_id") == "SYNTHETIC_DETERMINISTIC_CONVERSION_CASE"
    )


def _synthetic_count(fixture: dict[str, Any], output_field: str) -> int:
    case = _fixture_conversion_case(fixture)
    return len(_list_of_mappings(_fixture_outputs(case).get(output_field)))


def build_report(
    *,
    repo_root: pathlib.Path,
    gate: dict[str, Any],
    fixture: dict[str, Any],
    pr70_source_types: Sequence[str],
    pr71_registry: dict[str, Any],
    artifact_findings: dict[str, bool],
    pr70_report_path: pathlib.Path,
    pr71_report_path: pathlib.Path,
    fixture_path: pathlib.Path,
) -> dict[str, Any]:
    root = repo_root.resolve()
    outputs = _mapping(gate.get("production_outputs"))
    summary = _mapping(gate.get("production_input_summary"))
    policy = _mapping(gate.get("owner_override_policy"))
    return {
        "accepted_source_packets_created": _flag_from_gate(
            gate, "creates_accepted_source_packets"
        ),
        "account_data_present": artifact_findings.get("account_data_present", False),
        "atomicrows_bundle_jsonl_exists": (root / CANONICAL_BUNDLE_JSONL).exists(),
        "atomicrows_bundle_rows_created": _flag_from_gate(
            gate, "creates_atomicrows_bundle_rows"
        ),
        "atomicrows_bundle_sha256_exists": (root / CANONICAL_BUNDLE_SHA256).exists(),
        "authority_class": REPORT_AUTHORITY_CLASS,
        "candidate_agent_binding_request_count": len(
            _list_of_mappings(outputs.get("candidate_agent_binding_requests"))
        ),
        "candidate_algorithm_family_packet_count": len(
            _list_of_mappings(outputs.get("candidate_algorithm_family_packets"))
        ),
        "candidate_parameter_family_packet_count": len(
            _list_of_mappings(outputs.get("candidate_parameter_family_packets"))
        ),
        "cash_receipts_created": _flag_from_gate(gate, "creates_cash_receipts"),
        "connector_semantics_created": _flag_from_gate(
            gate, "creates_connector_semantics"
        ),
        "conversion_gate_contract_ready": gate.get("conversion_gate_contract_ready"),
        "depends_on_pr70_classifier": True,
        "depends_on_pr71_intake_registry": True,
        "execution_superiority_claim_created": _flag_from_gate(
            gate, "creates_execution_superiority_claim"
        ),
        "external_repo_commands_present": artifact_findings.get(
            "external_repo_commands_present", False
        ),
        "final_ready": gate.get("final_ready"),
        "fixture_contains_only_synthetic_entries": fixture_contains_only_synthetic_entries(
            fixture
        ),
        "fixture_path": _as_posix(fixture_path),
        "latency_superiority_claim_created": _flag_from_gate(
            gate, "creates_latency_superiority_claim"
        ),
        "live_readiness_created": _flag_from_gate(gate, "creates_live_readiness"),
        "live_receipts_created": _flag_from_forbidden_flags(gate, "live_receipts"),
        "live_trading_commands_present": artifact_findings.get(
            "live_trading_commands_present", False
        ),
        "optimizer_arbitration_created": _flag_from_gate(
            gate, "creates_optimizer_arbitration"
        ),
        "order_authority_created": _flag_from_gate(gate, "creates_order_authority"),
        "order_commands_present": artifact_findings.get("order_commands_present", False),
        "order_receipts_created": _flag_from_forbidden_flags(gate, "order_receipts"),
        "output_packet_type_count": len(gate.get("output_packet_types", [])),
        "owner_override_fabricates_accepted_source_packet": policy.get(
            "owner_override_fabricates_accepted_source_packet"
        ),
        "owner_override_fabricates_external_fact": policy.get(
            "owner_override_fabricates_external_fact"
        ),
        "owner_override_fabricates_order_receipt": policy.get(
            "owner_override_fabricates_order_receipt"
        ),
        "owner_override_fabricates_profit_evidence": policy.get(
            "owner_override_fabricates_profit_evidence"
        ),
        "owner_override_fabricates_quantum_backend_execution": policy.get(
            "owner_override_fabricates_quantum_backend_execution"
        ),
        "owner_override_fabricates_replay_paper_result": policy.get(
            "owner_override_fabricates_replay_paper_result"
        ),
        "owner_override_fabricates_runtime_cash_receipt": policy.get(
            "owner_override_fabricates_runtime_cash_receipt"
        ),
        "owner_override_receipt_reference_count": len(
            _list_of_mappings(outputs.get("owner_override_receipt_references"))
        ),
        "owner_override_satisfies_internal_workflow_only": policy.get(
            "owner_override_satisfies_internal_workflow_only"
        ),
        "owner_override_supported": policy.get("owner_override_supported"),
        "package_install_commands_present": artifact_findings.get(
            "package_install_commands_present", False
        ),
        "paper_results_created": _flag_from_gate(gate, "creates_paper_results"),
        "pr70_classifier_report_path": _as_posix(pr70_report_path),
        "pr70_source_type_count_observed": len(pr70_source_types),
        "pr71_intake_entries_empty": pr71_registry.get("intake_entries") == [],
        "pr71_intake_registry_report_path": _as_posix(pr71_report_path),
        "pr71_real_owner_intake_entry_count": pr71_registry.get(
            "real_owner_intake_entry_count"
        ),
        "pr71_real_owner_intakes_invented": pr71_registry.get(
            "real_owner_intakes_invented"
        ),
        "production_conversion_ready": gate.get("production_conversion_ready"),
        "production_intake_entries_count": summary.get("production_intake_entries_count"),
        "profit_evidence_created": _flag_from_gate(gate, "creates_profit_evidence"),
        "quantum_advantage_claim_created": _flag_from_gate(
            gate, "creates_quantum_advantage_claim"
        ),
        "quantum_backend_evidence_created": _flag_from_gate(
            gate, "creates_quantum_backend_evidence"
        ),
        "ranking_created": _flag_from_gate(gate, "creates_ranking"),
        "real_candidate_outputs_invented": gate.get("real_candidate_outputs_invented"),
        "real_source_claims_present": artifact_findings.get(
            "real_source_claims_present", False
        ),
        "real_urls_present": artifact_findings.get("real_urls_present", False),
        "replay_results_created": _flag_from_gate(gate, "creates_replay_results"),
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "runtime_artifacts_created": _flag_from_gate(gate, "creates_runtime_artifacts"),
        "runtime_receipts_created": _flag_from_forbidden_flags(gate, "runtime_receipts"),
        "scoring_created": _flag_from_gate(gate, "creates_scoring"),
        "secrets_present": artifact_findings.get("secrets_present", False),
        "source_acceptance_created": _flag_from_gate(gate, "accepts_source_facts"),
        "source_retrieval_created": _flag_from_gate(gate, "retrieves_source_facts"),
        "supported_candidate_route_count": len(gate.get("supported_candidate_routes", [])),
        "supported_source_type_count": len(gate.get("supported_source_types", [])),
        "synthetic_candidate_agent_binding_request_count": _synthetic_count(
            fixture, "candidate_agent_binding_requests"
        ),
        "synthetic_candidate_algorithm_family_packet_count": _synthetic_count(
            fixture, "candidate_algorithm_family_packets"
        ),
        "synthetic_candidate_parameter_family_packet_count": _synthetic_count(
            fixture, "candidate_parameter_family_packets"
        ),
        "synthetic_conversion_case_count": _synthetic_conversion_case_count(fixture),
        "synthetic_fixture_only": gate.get("synthetic_fixture_only"),
        "synthetic_owner_override_receipt_reference_count": _synthetic_count(
            fixture, "owner_override_receipt_references"
        ),
        "trade_context_routing_created": _flag_from_gate(
            gate, "creates_trade_context_routing"
        ),
        "validation_marker": SUCCESS_MARKER,
        "validator": VALIDATOR_NAME,
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_json_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_values: dict[str, Any] = {
        "report_id": REPORT_ID,
        "report_version": REPORT_VERSION,
        "validator": VALIDATOR_NAME,
        "authority_class": REPORT_AUTHORITY_CLASS,
        "depends_on_pr70_classifier": True,
        "pr70_source_type_count_observed": len(CANONICAL_SOURCE_TYPES),
        "depends_on_pr71_intake_registry": True,
        "pr71_real_owner_intake_entry_count": 0,
        "pr71_intake_entries_empty": True,
        "pr71_real_owner_intakes_invented": False,
        "supported_source_type_count": len(CANONICAL_SOURCE_TYPES),
        "supported_candidate_route_count": len(CANDIDATE_ROUTES_SUPPORTED),
        "output_packet_type_count": len(OUTPUT_PACKET_TYPES),
        "production_intake_entries_count": 0,
        "candidate_parameter_family_packet_count": 0,
        "candidate_algorithm_family_packet_count": 0,
        "candidate_agent_binding_request_count": 0,
        "owner_override_receipt_reference_count": 0,
        "real_candidate_outputs_invented": False,
        "synthetic_fixture_only": True,
        "fixture_contains_only_synthetic_entries": True,
        "synthetic_conversion_case_count": 1,
        "synthetic_candidate_parameter_family_packet_count": 1,
        "synthetic_candidate_algorithm_family_packet_count": 1,
        "synthetic_candidate_agent_binding_request_count": 1,
        "synthetic_owner_override_receipt_reference_count": 1,
        "owner_override_supported": True,
        "owner_override_satisfies_internal_workflow_only": True,
        "conversion_gate_contract_ready": True,
        "production_conversion_ready": False,
        "final_ready": False,
        "validation_marker": SUCCESS_MARKER,
    }
    false_fields = (
        "real_urls_present",
        "real_source_claims_present",
        "secrets_present",
        "account_data_present",
        "external_repo_commands_present",
        "package_install_commands_present",
        "order_commands_present",
        "live_trading_commands_present",
        "source_retrieval_created",
        "source_acceptance_created",
        "accepted_source_packets_created",
        "connector_semantics_created",
        "runtime_artifacts_created",
        "runtime_receipts_created",
        "live_receipts_created",
        "order_receipts_created",
        "cash_receipts_created",
        "replay_results_created",
        "paper_results_created",
        "live_readiness_created",
        "order_authority_created",
        "profit_evidence_created",
        "quantum_backend_evidence_created",
        "quantum_advantage_claim_created",
        "latency_superiority_claim_created",
        "execution_superiority_claim_created",
        "ranking_created",
        "scoring_created",
        "optimizer_arbitration_created",
        "trade_context_routing_created",
        "atomicrows_bundle_rows_created",
        "atomicrows_bundle_sha256_exists",
        "owner_override_fabricates_external_fact",
        "owner_override_fabricates_accepted_source_packet",
        "owner_override_fabricates_runtime_cash_receipt",
        "owner_override_fabricates_order_receipt",
        "owner_override_fabricates_replay_paper_result",
        "owner_override_fabricates_quantum_backend_execution",
        "owner_override_fabricates_profit_evidence",
    )
    for field in false_fields:
        expected_values[field] = False
    if not isinstance(report.get("atomicrows_bundle_jsonl_exists"), bool):
        failures.append("report.atomicrows_bundle_jsonl_exists must be boolean")
    for field, expected in expected_values.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected!r}")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is not deterministic JSON")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    gate_path: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
    pr70_schema_path: pathlib.Path = DEFAULT_PR70_SCHEMA,
    pr70_registry_path: pathlib.Path = DEFAULT_PR70_REGISTRY,
    pr70_report_path: pathlib.Path = DEFAULT_PR70_REPORT,
    pr71_schema_path: pathlib.Path = DEFAULT_PR71_SCHEMA,
    pr71_registry_path: pathlib.Path = DEFAULT_PR71_REGISTRY,
    pr71_report_path: pathlib.Path = DEFAULT_PR71_REPORT,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    pr70_source_types, pr70_failures = validate_pr70_dependency(
        repo_root=root,
        pr70_schema_path=pr70_schema_path,
        pr70_registry_path=pr70_registry_path,
        pr70_report_path=pr70_report_path,
    )
    failures.extend(pr70_failures)
    pr71_registry, pr71_report, pr71_failures = validate_pr71_dependency(
        repo_root=root,
        pr71_schema_path=pr71_schema_path,
        pr71_registry_path=pr71_registry_path,
        pr71_report_path=pr71_report_path,
        pr70_source_types=pr70_source_types,
    )
    failures.extend(pr71_failures)

    try:
        gate = load_yaml(root / gate_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)
    try:
        fixture = load_fixture(root / fixture_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)
    schema, schema_failures = _load_json_checked(root / schema_path, "PR72_SCHEMA")
    failures.extend(schema_failures)
    if schema is None:
        schema = {}
    else:
        failures.extend(validate_schema_required_fields(schema))
        failures.extend(
            validate_gate_payload(
                gate,
                schema=schema,
                pr70_source_types=pr70_source_types,
                pr71_registry=pr71_registry,
                production=True,
            )
        )
        failures.extend(
            validate_synthetic_fixture_conversion(
                fixture,
                schema=schema,
                pr70_source_types=pr70_source_types,
            )
        )

    artifact_texts = (
        (_as_posix(schema_path), _read_text_if_exists(root / schema_path)),
        (_as_posix(gate_path), _read_text_if_exists(root / gate_path)),
        (_as_posix(fixture_path), _read_text_if_exists(root / fixture_path)),
    )
    artifact_findings = forbidden_text_findings(artifact_texts)
    failures.extend(validate_no_forbidden_claims(artifact_texts))
    failures.extend(validate_no_forbidden_artifacts(root))
    failures.extend(validate_master_plan_not_modified(root))

    report = build_report(
        repo_root=root,
        gate=gate,
        fixture=fixture,
        pr70_source_types=pr70_source_types,
        pr71_registry=pr71_registry,
        artifact_findings=artifact_findings,
        pr70_report_path=pr70_report_path,
        pr71_report_path=pr71_report_path,
        fixture_path=fixture_path,
    )
    second_report = build_report(
        repo_root=root,
        gate=gate,
        fixture=fixture,
        pr70_source_types=pr70_source_types,
        pr71_registry=pr71_registry,
        artifact_findings=artifact_findings,
        pr70_report_path=pr70_report_path,
        pr71_report_path=pr71_report_path,
        fixture_path=fixture_path,
    )
    if report != second_report:
        failures.append("generated PR72 report is not deterministic")
    report_text = serialize_report(report)
    failures.extend(validate_no_forbidden_claims((("generated_report", report_text),)))
    failures.extend(_report_safety_failures(report))
    if pr71_report.get("validation_marker") != pr71_gate.SUCCESS_MARKER:
        failures.append("PR71_REPORT_MARKER_MISMATCH: dependency marker must be canonical")

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: research-source-to-candidate-family gate is "
            "static review-only metadata"
        )

    if output_path is not None and not failures:
        write_json_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="dev", choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--gate", default=str(DEFAULT_GATE))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    parser.add_argument("--pr70-schema", default=str(DEFAULT_PR70_SCHEMA))
    parser.add_argument("--pr70-registry", default=str(DEFAULT_PR70_REGISTRY))
    parser.add_argument("--pr70-report", default=str(DEFAULT_PR70_REPORT))
    parser.add_argument("--pr71-schema", default=str(DEFAULT_PR71_SCHEMA))
    parser.add_argument("--pr71-registry", default=str(DEFAULT_PR71_REGISTRY))
    parser.add_argument("--pr71-report", default=str(DEFAULT_PR71_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        gate_path=pathlib.Path(args.gate),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
        pr70_schema_path=pathlib.Path(args.pr70_schema),
        pr70_registry_path=pathlib.Path(args.pr70_registry),
        pr70_report_path=pathlib.Path(args.pr70_report),
        pr71_schema_path=pathlib.Path(args.pr71_schema),
        pr71_registry_path=pathlib.Path(args.pr71_registry),
        pr71_report_path=pathlib.Path(args.pr71_report),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(marker)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
