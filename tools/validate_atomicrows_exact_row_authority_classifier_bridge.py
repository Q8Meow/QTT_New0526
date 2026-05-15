#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import dataclass
import json
import pathlib
import re
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_bundle as builder  # noqa: E402
from tools import validate_atomicrows_bundle_builder_deterministic_assembly_gate as pr99_gate  # noqa: E402
from tools import validate_atomicrows_bundle_row_family_source_files as pr98_gate  # noqa: E402
from tools import validate_atomicrows_bundle_sha_freeze_authority_gate as pr100_gate  # noqa: E402
from tools import validate_atomicrows_full_bundle_row_expansion_plan as pr97_gate  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)


DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_exact_row_authority_classifier_bridge.schema.json"
)
DEFAULT_CONFIG = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomicrows"
    / "AtomicRowsExactRowAuthorityClassifierBridge.yaml"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsExactRowAuthorityClassifierBridge.report.json"
)

REPORT_TYPE = "ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_REPORT"
ARTIFACT_ID = "ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE"
ARTIFACT_VERSION = "v1"
REPAIR_SCOPE = "ATOMICROWS_4183_EXACT_ROW_MATERIALIZATION_GAP_REPAIR"
AUTHORITY_CLASS = "STATIC_REPAIR_BRIDGE_NOT_EXACT_ROWS_NOT_BUNDLE_NOT_SHA_NOT_FREEZE"
GATE_MODE = "BRIDGE_READY_EXACT_ROWS_NOT_CREATED"
TARGET_BRANCH = "repair/atomicrows-exact-row-authority-classifier-bridge"
SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_FAILED"

MASTER_PLAN_CURRENT = pr97_gate.MASTER_PLAN_CURRENT
CANONICAL_BUNDLE_JSONL = pr97_gate.CANONICAL_BUNDLE_JSONL
CANONICAL_BUNDLE_SHA256 = pr97_gate.CANONICAL_BUNDLE_SHA256
EXACT_ROW_SOURCES_DIR = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "exact_row_sources"
)

REQUIRED_AUTHORITY_CLASSES = (
    "INTERNAL_MASTER_PLAN_VALUE",
    "INTERNAL_REPO_ARTIFACT_VALUE",
    "INTERNAL_ROADMAP_VALUE",
    "OWNER_POLICY_VALUE",
    "OWNER_APPROVAL_REQUIRED",
    "ACCEPTED_SOURCE_EVIDENCE_REQUIRED",
    "RUNTIME_RECEIPT_REQUIRED",
    "REPLAY_RESULT_REQUIRED",
    "PAPER_RESULT_REQUIRED",
    "OPTIMIZER_RESULT_REQUIRED",
    "QUANTUM_BACKEND_RECEIPT_REQUIRED",
    "BLOCKED_PENDING_FUTURE_SCOPE",
    "NOT_APPLICABLE_BY_DESIGN",
)
INTERNAL_AUTHORITY_CLASSES = (
    "INTERNAL_MASTER_PLAN_VALUE",
    "INTERNAL_REPO_ARTIFACT_VALUE",
    "INTERNAL_ROADMAP_VALUE",
    "OWNER_POLICY_VALUE",
)
REQUIRED_FIELD_FILL_RULE_IDS = (
    "INTERNAL_CURRENT_REPO_VALUE_RULE",
    "OWNER_POLICY_VALUE_RULE",
    "EXTERNAL_FACT_RULE",
    "RUNTIME_PRIVATE_STATE_RULE",
    "REPLAY_RESULT_RULE",
    "PAPER_RESULT_RULE",
    "OPTIMIZER_RESULT_RULE",
    "QUANTUM_BACKEND_RESULT_RULE",
    "UNCLEAR_AUTHORITY_RULE",
    "NO_FABRICATION_RULE",
)
FIELD_FILL_RULE_EXPECTATIONS = {
    "EXTERNAL_FACT_RULE": (
        ("ACCEPTED_SOURCE_EVIDENCE_REQUIRED",),
        "SOURCE_EVIDENCE_REQUIRED",
    ),
    "RUNTIME_PRIVATE_STATE_RULE": (
        ("RUNTIME_RECEIPT_REQUIRED",),
        "RUNTIME_RECEIPT_REQUIRED",
    ),
    "REPLAY_RESULT_RULE": (("REPLAY_RESULT_REQUIRED",), "REPLAY_RESULT_REQUIRED"),
    "PAPER_RESULT_RULE": (("PAPER_RESULT_REQUIRED",), "PAPER_RESULT_REQUIRED"),
    "OPTIMIZER_RESULT_RULE": (
        ("OPTIMIZER_RESULT_REQUIRED",),
        "OPTIMIZER_RESULT_REQUIRED",
    ),
    "QUANTUM_BACKEND_RESULT_RULE": (
        ("QUANTUM_BACKEND_RECEIPT_REQUIRED",),
        "QUANTUM_BACKEND_RECEIPT_REQUIRED",
    ),
}
REQUIRED_EXACT_ROW_SOURCE_FILES = (
    "001_signal_features.exact_rows.jsonl",
    "002_scoring_ranking.exact_rows.jsonl",
    "003_normalization_calibration.exact_rows.jsonl",
    "004_risk_control.exact_rows.jsonl",
    "005_execution_connector_boundary.exact_rows.jsonl",
    "006_capital_sizing_cash.exact_rows.jsonl",
    "007_latency_routing.exact_rows.jsonl",
    "008_error_guard_fail_closed.exact_rows.jsonl",
    "009_lifecycle_agent_binding.exact_rows.jsonl",
    "010_source_evidence_connector_semantic.exact_rows.jsonl",
    "011_replay_paper_validation.exact_rows.jsonl",
    "012_quantum_advisory_optimization.exact_rows.jsonl",
    "013_quantum_qubo_ising_metadata.exact_rows.jsonl",
    "014_quantum_qaoa_vqe_annealing_metadata.exact_rows.jsonl",
    "015_quantum_portfolio_hybrid_comparator.exact_rows.jsonl",
)
REQUIRED_FUTURE_ROW_SCHEMA_FIELDS = (
    "row_id",
    "row_family_id",
    "row_family_name",
    "canonical_order",
    "row_index_within_family",
    "global_row_index",
    "row_kind",
    "row_scope",
    "activation_state",
    "lifecycle_state",
    "owner_review_state",
    "parameter_role",
    "algorithm_role",
    "agent_role",
    "consumer_class",
    "strategy_class",
    "venue_scope",
    "market_type_scope",
    "quantum_applicability_class",
    "quantum_execution_allowed",
    "quantum_advantage_claim_allowed",
    "authority_fields",
    "blocked_reason_codes",
    "source_evidence_requirements",
    "runtime_receipt_requirements",
    "replay_paper_requirements",
    "quantum_backend_requirements",
    "agent_eligibility",
    "live_order_authority_allowed",
    "direct_quantum_order_authority_allowed",
    "profit_evidence_created",
    "latency_evidence_created",
    "execution_superiority_evidence_created",
    "quantum_advantage_evidence_created",
)
REQUIRED_GOVERNANCE_ROW_KINDS = (
    "AGENT_ROW_ACCESS_POLICY",
    "AGENT_FAMILY_ACCESS_POLICY",
    "AGENT_PARAMETER_ACCESS_POLICY",
    "AGENT_ALGORITHM_ACCESS_POLICY",
    "AGENT_QUANTUM_ROW_ACCESS_POLICY",
    "AGENT_LIVE_MODE_ACCESS_POLICY",
)
REQUIRED_ACCESS_STATES = (
    "ACCESS_DENIED_DEFAULT",
    "ACCESS_ALLOWED_STATIC_RESEARCH_ONLY",
    "ACCESS_ALLOWED_REPLAY_ONLY",
    "ACCESS_ALLOWED_PAPER_ONLY",
    "ACCESS_ALLOWED_REPLAY_AND_PAPER",
    "ACCESS_ALLOWED_OWNER_REVIEW_ONLY",
    "ACCESS_ALLOWED_RUNTIME_READ_ONLY",
    "ACCESS_ALLOWED_LIVE_ADJACENT_NO_ORDER",
    "ACCESS_ALLOWED_LIVE_ORDER_INTENT_ONLY",
    "ACCESS_ALLOWED_LIVE_ORDER_ROUTER_ONLY",
    "BLOCKED_SOURCE_EVIDENCE_REQUIRED",
    "BLOCKED_RUNTIME_RECEIPT_REQUIRED",
    "BLOCKED_OWNER_APPROVAL_REQUIRED",
    "BLOCKED_AGENT_BINDING_MISSING",
    "BLOCKED_ALGORITHM_BINDING_MISSING",
    "BLOCKED_COMMAND_MATRIX_MISSING",
    "BLOCKED_QUANTUM_BACKEND_RECEIPT_REQUIRED",
    "BLOCKED_UNKNOWN_ELIGIBILITY_STATE",
)
REQUIRED_ACCESS_DECISION_STEPS = (
    "ROW_ACTIVE",
    "ROW_FAMILY_ACTIVE",
    "ROW_NOT_BLOCKED_BY_SOURCE_RUNTIME_REPLAY_PAPER_OPTIMIZER_QUANTUM_OR_BACKEND_REQUIREMENTS",
    "AGENT_ROLE_ELIGIBLE",
    "SPECIFIC_AGENT_ELIGIBLE",
    "AGENT_TASK_TYPE_ELIGIBLE",
    "TRADING_MODE_ALLOWED",
    "VENUE_AND_MARKET_TYPE_ALLOWED",
    "REQUIRED_AGENT_BINDING_PRESENT",
    "ALGORITHM_BINDING_PASSES",
    "COMMAND_MATRIX_ALLOWS_ACTION",
    "OWNER_POLICY_ALLOWS_OR_OVERRIDES",
    "LIVE_ORDER_AUTHORITY_STILL_FALSE_UNLESS_LATER_EXPLICITLY_OPENED",
)
REQUIRED_CROSS_REFERENCE_FAMILIES = (
    "001_signal_features",
    "002_scoring_ranking",
    "003_normalization_calibration",
    "004_risk_control",
    "005_execution_connector_boundary",
    "006_capital_sizing_cash",
    "007_latency_routing",
    "008_error_guard_fail_closed",
    "009_lifecycle_agent_binding",
    "010_source_evidence_connector_semantic",
    "011_replay_paper_validation",
    "012_quantum_advisory_optimization",
    "013_quantum_qubo_ising_metadata",
    "014_quantum_qaoa_vqe_annealing_metadata",
    "015_quantum_portfolio_hybrid_comparator",
)
REQUIRED_ARCHITECTURE_COMPONENTS = (
    "ROW_FAMILY_EXPANSION_MANIFEST",
    "FIELD_AUTHORITY_CLASSIFIER",
    "DETERMINISTIC_ROW_GENERATOR",
    "OWNER_REVIEW_GATE",
    "BUNDLE_MATERIALIZER",
    "SHA_FREEZE_MATERIALIZER",
    "FINAL_READINESS_GATE",
)
NO_AUTHORITY_FALSE_FIELDS = (
    "exact_rows_created",
    "atomicrows_bundle_jsonl_created",
    "atomicrows_bundle_sha256_created",
    "sha_computed",
    "freeze_authority_created",
    "final_readiness_created",
    "runtime_live_order_authority_created",
    "source_fact_authority_created",
    "connector_semantic_authority_created",
    "profit_evidence_created",
    "latency_evidence_created",
    "execution_superiority_evidence_created",
    "quantum_backend_authority_created",
    "quantum_advantage_evidence_created",
)
AGENT_DENY_FALSE_FIELDS = (
    "row_existence_grants_access",
    "family_membership_grants_access",
    "parameter_existence_grants_access",
    "algorithm_applicability_grants_access",
    "quantum_applicability_grants_access",
    "owner_quantum_priority_grants_access",
    "replay_paper_eligibility_grants_live_access",
    "static_selection_eligibility_grants_order_authority",
    "static_handoff_eligibility_grants_order_authority",
    "live_use_allowed_default",
    "direct_order_authority_allowed_default",
    "direct_quantum_order_authority_allowed_default",
)
AGENT_BLOCK_TRUE_FIELDS = (
    "required_for_every_future_exact_row",
    "deny_by_default",
    "missing_agent_binding_blocks_access",
    "missing_algorithm_binding_blocks_access",
    "missing_command_matrix_blocks_access",
    "unknown_eligibility_state_blocks_access",
    "owner_override_allowed_for_internal_access",
    "owner_override_cannot_create_external_fact_or_runtime_receipt",
    "owner_override_cannot_create_agent_live_order_authority_without_later_live_scope",
)
DEFAULT_AGENT_ELIGIBILITY_ARRAY_FIELDS = (
    "eligible_agent_role_ids",
    "eligible_agent_ids",
    "eligible_consumer_classes",
    "eligible_task_types",
    "eligible_trading_modes",
    "eligible_venue_scope",
    "eligible_market_type_scope",
    "prohibited_agent_role_ids",
    "prohibited_agent_ids",
    "prohibited_task_types",
    "required_agent_capabilities",
    "required_agent_binding_refs",
    "required_algorithm_binding_refs",
    "required_command_matrix_refs",
    "required_owner_approval_refs",
)
FUTURE_VALIDATOR_TRUE_FIELDS = (
    "exact_row_source_files_exist_before_bundle_creation",
    "total_exact_row_count_equals_4183",
    "all_15_exact_row_family_files_exist",
    "per_family_counts_sum_to_4183",
    "row_ids_unique",
    "global_row_indexes_unique_and_contiguous",
    "family_local_row_indexes_unique_and_contiguous",
    "every_row_has_authority_class_for_every_field",
    "every_internal_value_has_source_pointer",
    "every_blocked_null_value_has_block_code",
    "every_row_has_agent_eligibility",
    "every_row_has_owner_review_state",
    "every_row_has_activation_state",
    "no_external_fact_is_invented",
    "no_runtime_receipt_is_invented",
    "no_replay_paper_result_is_invented",
    "no_optimizer_result_is_invented",
    "no_quantum_backend_output_is_invented",
    "no_profit_latency_execution_superiority_or_quantum_advantage_evidence_is_invented",
)
FORBIDDEN_ARTIFACT_PATHS = (
    CANONICAL_BUNDLE_JSONL,
    CANONICAL_BUNDLE_SHA256,
    pathlib.Path("docs")
    / "master_plan"
    / "atomic_rows"
    / "AtomicRowsBundleFreezeAuthority.yaml",
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsFullBundleFinalReadinessGate.report.json",
)
FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS = (
    "hashlib",
    "requests",
    "qiskit",
    "dwave",
    "cirq",
    "pennylane",
    "dimod",
    "neal",
)
FORBIDDEN_CALL_NAMES = (
    "builder.main",
    "builder.materialize_bundle_if_allowed",
    "materialize_bundle_if_allowed",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]
    report: dict[str, Any] | None
    info_lines: tuple[str, ...] = ()


def _resolve(root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else root / path


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    value = pr97_gate.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


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
        return None, [f"{label} invalid JSON: {path.as_posix()}: {exc}"]


def _load_yaml_checked(path: pathlib.Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return load_yaml(path), []
    except FileNotFoundError:
        return None, [f"{label} missing: {path.as_posix()}"]
    except Exception as exc:
        return None, [f"{label} invalid YAML/JSON: {path.as_posix()}: {exc}"]


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    return [f"{label} {failure}" for failure in validate_json_schema_subset(payload, schema)]


def _require_exact_list(
    failures: list[str],
    *,
    label: str,
    actual: Any,
    expected: Sequence[str],
) -> None:
    if actual != list(expected):
        failures.append(f"{label} must exactly match canonical order")


def _require_true_fields(
    failures: list[str],
    mapping: dict[str, Any],
    fields: Sequence[str],
    *,
    prefix: str,
) -> None:
    for field in fields:
        if mapping.get(field) is not True:
            failures.append(f"{prefix}.{field} must be true")


def _require_false_fields(
    failures: list[str],
    mapping: dict[str, Any],
    fields: Sequence[str],
    *,
    prefix: str,
) -> None:
    for field in fields:
        if mapping.get(field) is not False:
            failures.append(f"{prefix}.{field} must be false")


def validate_identity_and_static_flags(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    checks = (
        ("artifact_id", ARTIFACT_ID),
        ("artifact_version", ARTIFACT_VERSION),
        ("repair_scope", REPAIR_SCOPE),
        ("authority_class", AUTHORITY_CLASS),
        ("gate_mode", GATE_MODE),
        ("target_total_row_count", 4183),
        ("target_total_row_count_status", "PLANNING_ONLY_UNTIL_EXACT_ROWS_GENERATED"),
        ("exact_rows_created_by_this_pr", False),
        ("bundle_created_by_this_pr", False),
        ("sha_created_by_this_pr", False),
        ("freeze_created_by_this_pr", False),
        ("final_readiness_created_by_this_pr", False),
        ("next_required_repair_pr", "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST"),
    )
    for key, expected in checks:
        if config.get(key) != expected:
            failures.append(f"config.{key} must be {expected!r}")

    pr97 = _mapping(config.get("pr97_state"))
    if pr97.get("expansion_plan_present") is not True:
        failures.append("pr97_state.expansion_plan_present must be true")
    if pr97.get("target_total_rows") != 4183:
        failures.append("pr97_state.target_total_rows must be 4183")
    if pr97.get("exact_rows_created") is not False:
        failures.append("pr97_state.exact_rows_created must be false")

    pr98 = _mapping(config.get("pr98_state"))
    if pr98.get("row_family_source_files_present") is not True:
        failures.append("pr98_state.row_family_source_files_present must be true")
    if pr98.get("row_family_source_file_count") != 15:
        failures.append("pr98_state.row_family_source_file_count must be 15")
    if pr98.get("source_files_are_blueprints_only") is not True:
        failures.append("pr98_state.source_files_are_blueprints_only must be true")
    if pr98.get("exact_source_rows_created") is not False:
        failures.append("pr98_state.exact_source_rows_created must be false")

    pr99 = _mapping(config.get("pr99_state"))
    if pr99.get("path_b_blocked_state_preserved") is not True:
        failures.append("pr99_state.path_b_blocked_state_preserved must be true")
    if pr99.get("bundle_materialization_allowed_now") is not False:
        failures.append("pr99_state.bundle_materialization_allowed_now must be false")
    if pr99.get("bundle_created") is not False:
        failures.append("pr99_state.bundle_created must be false")

    pr100 = _mapping(config.get("pr100_state"))
    if pr100.get("sha_freeze_gate_blocked_state_preserved") is not True:
        failures.append("pr100_state.sha_freeze_gate_blocked_state_preserved must be true")
    if pr100.get("sha_created") is not False:
        failures.append("pr100_state.sha_created must be false")
    if pr100.get("freeze_created") is not False:
        failures.append("pr100_state.freeze_created must be false")

    return failures


def validate_authority_and_field_rules(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    _require_exact_list(
        failures,
        label="authority_classes",
        actual=config.get("authority_classes"),
        expected=REQUIRED_AUTHORITY_CLASSES,
    )

    handling_entries = _list_of_mappings(config.get("field_authority_handling"))
    handling_by_class = {
        str(entry.get("authority_class")): entry for entry in handling_entries
    }
    if tuple(handling_by_class) != REQUIRED_AUTHORITY_CLASSES:
        failures.append("field_authority_handling must cover every authority class in order")
    for authority in REQUIRED_AUTHORITY_CLASSES:
        entry = handling_by_class.get(authority, {})
        if not entry.get("value_policy"):
            failures.append(f"{authority} must have a deterministic value_policy")
        if authority in INTERNAL_AUTHORITY_CLASSES:
            if entry.get("source_pointer_required") is not True:
                failures.append(f"{authority} must require source_pointer")
            if entry.get("block_code_required") is not False:
                failures.append(f"{authority} must not require block_code")
            if entry.get("block_code") is not None:
                failures.append(f"{authority} block_code must be null")
        else:
            if entry.get("source_pointer_required") is not False:
                failures.append(f"{authority} must not require source_pointer")
            if entry.get("block_code_required") is not True:
                failures.append(f"{authority} must require block_code")
            if not entry.get("block_code"):
                failures.append(f"{authority} must declare a nonblank block_code")

    rules = _list_of_mappings(config.get("field_fill_rules"))
    rule_by_id = {str(rule.get("rule_id")): rule for rule in rules}
    if tuple(rule_by_id) != REQUIRED_FIELD_FILL_RULE_IDS:
        failures.append("field_fill_rules must match canonical deterministic order")
    for rule_id, (authorities, block_code) in FIELD_FILL_RULE_EXPECTATIONS.items():
        rule = rule_by_id.get(rule_id, {})
        if tuple(rule.get("authority_classes") or []) != authorities:
            failures.append(f"{rule_id} must use authority_classes {authorities}")
        if rule.get("block_code") != block_code:
            failures.append(f"{rule_id} must use block_code {block_code}")
        if rule.get("value_policy") != "LEAVE_VALUE_NULL":
            failures.append(f"{rule_id} must leave value null")
    internal_rule = rule_by_id.get("INTERNAL_CURRENT_REPO_VALUE_RULE", {})
    if tuple(internal_rule.get("authority_classes") or []) != INTERNAL_AUTHORITY_CLASSES[:3]:
        failures.append("INTERNAL_CURRENT_REPO_VALUE_RULE must cover internal repo authority classes")
    if internal_rule.get("block_code") is not None:
        failures.append("INTERNAL_CURRENT_REPO_VALUE_RULE block_code must be null")
    owner_rule = rule_by_id.get("OWNER_POLICY_VALUE_RULE", {})
    if owner_rule.get("authority_classes") != ["OWNER_POLICY_VALUE"]:
        failures.append("OWNER_POLICY_VALUE_RULE must use OWNER_POLICY_VALUE")
    if owner_rule.get("block_code") is not None:
        failures.append("OWNER_POLICY_VALUE_RULE block_code must be null")
    unclear_rule = rule_by_id.get("UNCLEAR_AUTHORITY_RULE", {})
    if tuple(unclear_rule.get("authority_classes") or []) != (
        "OWNER_APPROVAL_REQUIRED",
        "BLOCKED_PENDING_FUTURE_SCOPE",
    ):
        failures.append("UNCLEAR_AUTHORITY_RULE must block on owner approval or future scope")
    no_fabrication_rule = rule_by_id.get("NO_FABRICATION_RULE", {})
    if "NO_BLANKS_NO_GUESSING" not in str(no_fabrication_rule.get("value_policy")):
        failures.append("NO_FABRICATION_RULE must explicitly forbid blanks and guessing")
    if "NO_RUNTIME_RECEIPT_INVENTION" not in str(no_fabrication_rule.get("value_policy")):
        failures.append("NO_FABRICATION_RULE must forbid runtime receipt invention")
    if "NO_QUANTUM_BACKEND_OUTPUT_INVENTION" not in str(no_fabrication_rule.get("value_policy")):
        failures.append("NO_FABRICATION_RULE must forbid quantum backend output invention")
    return failures


def validate_row_doctrine_and_architecture(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    doctrine = _mapping(config.get("row_field_doctrine"))
    _require_true_fields(
        failures,
        doctrine,
        (
            "every_future_exact_row_field_requires_value_or_null",
            "every_future_exact_row_field_requires_authority_class",
            "internally_sourced_fields_require_source_pointer",
            "blocked_fields_require_block_code",
            "every_future_exact_row_field_requires_owner_review_state",
            "every_future_exact_row_field_requires_activation_state",
            "every_future_exact_row_requires_agent_eligibility_block",
        ),
        prefix="row_field_doctrine",
    )
    _require_false_fields(
        failures,
        doctrine,
        (
            "unknown_authority_allowed",
            "blank_authority_class_allowed",
            "non_null_external_fact_without_accepted_source_evidence_allowed",
            "runtime_private_account_order_fill_cash_without_receipt_allowed",
            "replay_paper_values_without_result_packets_allowed",
            "optimizer_quantum_backend_values_without_receipts_allowed",
            "profit_latency_execution_superiority_quantum_advantage_without_future_evidence_allowed",
        ),
        prefix="row_field_doctrine",
    )

    architecture = _mapping(config.get("canonical_row_fill_architecture"))
    _require_true_fields(
        failures,
        architecture,
        (
            "defined",
            "row_family_expansion_manifest_future_only",
            "field_authority_classifier_required",
            "deterministic_row_generator_future_only",
            "owner_review_gate_future_only",
            "bundle_materializer_future_only",
            "sha_freeze_materializer_future_only",
            "final_readiness_gate_future_only",
        ),
        prefix="canonical_row_fill_architecture",
    )
    components = _list_of_mappings(architecture.get("AtomicRowsExactRowMaterializationBridge"))
    component_ids = tuple(str(item.get("component_id")) for item in components)
    if component_ids != REQUIRED_ARCHITECTURE_COMPONENTS:
        failures.append("AtomicRowsExactRowMaterializationBridge components must match canonical order")
    component_by_id = {str(item.get("component_id")): item for item in components}
    if component_by_id.get("ROW_FAMILY_EXPANSION_MANIFEST", {}).get("creates_rows_by_itself") is not False:
        failures.append("row family expansion manifest must not create rows by itself")
    if component_by_id.get("FIELD_AUTHORITY_CLASSIFIER", {}).get("refuses_unknown_authority") is not True:
        failures.append("field authority classifier must refuse unknown authority")
    if component_by_id.get("DETERMINISTIC_ROW_GENERATOR", {}).get("future_pr_only") is not True:
        failures.append("deterministic row generator must be future-only")
    if component_by_id.get("BUNDLE_MATERIALIZER", {}).get("mutates_row_content_during_bundle_build") is not False:
        failures.append("bundle materializer must not mutate row content during bundle build")
    if component_by_id.get("SHA_FREEZE_MATERIALIZER", {}).get("computes_sha_only_over_exact_bundle_bytes") is not True:
        failures.append("SHA/freeze materializer must compute SHA only over exact bundle bytes")
    if component_by_id.get("FINAL_READINESS_GATE", {}).get("future_pr_only") is not True:
        failures.append("final readiness gate must be future-only")
    return failures


def validate_future_file_id_schema_and_sequence(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    strategy = _mapping(config.get("future_row_file_strategy"))
    if strategy.get("exact_row_source_directory") != EXACT_ROW_SOURCES_DIR.as_posix() + "/":
        failures.append("future exact row source directory path mismatch")
    _require_exact_list(
        failures,
        label="future_row_file_strategy.exact_row_source_files",
        actual=strategy.get("exact_row_source_files"),
        expected=REQUIRED_EXACT_ROW_SOURCE_FILES,
    )
    if strategy.get("bundle_output") != CANONICAL_BUNDLE_JSONL.as_posix():
        failures.append("future bundle output path mismatch")
    if strategy.get("sha_output") != CANONICAL_BUNDLE_SHA256.as_posix():
        failures.append("future SHA output path mismatch")
    if strategy.get("future_only_no_files_created_by_this_pr") is not True:
        failures.append("future_row_file_strategy must be future-only")
    future_proofs = _mapping(strategy.get("future_validators_must_prove"))
    _require_true_fields(
        failures,
        future_proofs,
        FUTURE_VALIDATOR_TRUE_FIELDS,
        prefix="future_row_file_strategy.future_validators_must_prove",
    )

    law = _mapping(config.get("future_row_id_law"))
    checks = (
        ("format", "AR_EXACT_<family_number>_<family_slug>_<six_digit_family_index>"),
        ("example", "AR_EXACT_012_QUANTUM_ADVISORY_OPTIMIZATION_000001"),
        ("deterministic", True),
        ("hand_invented_ad_hoc_ids_allowed", False),
        ("row_ids_encode_family_number_family_slug_and_family_local_index", True),
        ("row_order", "FAMILY_ORDER_THEN_ROW_INDEX_WITHIN_FAMILY"),
        (
            "global_row_index_rule",
            "CUMULATIVE_PRIOR_FAMILY_ROW_COUNT_PLUS_ROW_INDEX_WITHIN_FAMILY",
        ),
    )
    for key, expected in checks:
        if law.get(key) != expected:
            failures.append(f"future_row_id_law.{key} must be {expected!r}")

    schema_doctrine = _mapping(config.get("future_exact_row_schema_doctrine"))
    if schema_doctrine.get("defined") is not True:
        failures.append("future exact-row schema doctrine must be defined")
    _require_exact_list(
        failures,
        label="future_exact_row_schema_doctrine.required_fields",
        actual=schema_doctrine.get("required_fields"),
        expected=REQUIRED_FUTURE_ROW_SCHEMA_FIELDS,
    )
    _require_false_fields(
        failures,
        schema_doctrine,
        (
            "live_order_authority_allowed_default",
            "direct_quantum_order_authority_allowed_default",
            "quantum_execution_allowed_default",
            "quantum_advantage_claim_allowed_default",
            "profit_evidence_created_default",
            "latency_evidence_created_default",
            "execution_superiority_evidence_created_default",
            "quantum_advantage_evidence_created_default",
        ),
        prefix="future_exact_row_schema_doctrine",
    )
    _require_true_fields(
        failures,
        schema_doctrine,
        (
            "live_order_authority_allowed_false_unless_later_owner_approved_live_scope_opens_it",
            "quantum_execution_allowed_false_unless_later_backend_execution_scope_opens_it",
            "quantum_advantage_claim_allowed_false_unless_later_evidence_scope_opens_it",
        ),
        prefix="future_exact_row_schema_doctrine",
    )

    sequence = _mapping(config.get("recovery_pr_sequence_doctrine"))
    if sequence.get("defined") is not True:
        failures.append("recovery PR sequence doctrine must be defined")
    sequence_rows = _list_of_mappings(sequence.get("sequence"))
    expected_sequence = (
        "Repair PR A",
        "Repair PR B",
        "Repair PR C",
        "Repair PR D",
        "Repair PR E",
        "Repair PR F",
        "Roadmap PR #101",
    )
    if tuple(str(item.get("repair_pr")) for item in sequence_rows) != expected_sequence:
        failures.append("recovery PR sequence must match Repair PR A-F then Roadmap PR #101")
    if sequence_rows and sequence_rows[0].get("creates_exact_rows") is not False:
        failures.append("Repair PR A must create no exact rows")
    return failures


def validate_agent_governance(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    governance = _mapping(config.get("agent_eligibility_governance"))
    _require_true_fields(
        failures,
        governance,
        AGENT_BLOCK_TRUE_FIELDS,
        prefix="agent_eligibility_governance",
    )
    _require_false_fields(
        failures,
        governance,
        AGENT_DENY_FALSE_FIELDS,
        prefix="agent_eligibility_governance",
    )
    block = _mapping(governance.get("default_agent_eligibility_block"))
    for field in DEFAULT_AGENT_ELIGIBILITY_ARRAY_FIELDS:
        if block.get(field) != []:
            failures.append(f"default_agent_eligibility_block.{field} must be []")
    block_checks = (
        ("access_decision_default", "DENY"),
        ("access_grant_state", "BLOCKED_UNTIL_AGENT_BINDING_AND_OWNER_POLICY_PASS"),
        ("live_use_allowed", False),
        ("direct_order_authority_allowed", False),
        ("direct_quantum_order_authority_allowed", False),
        ("owner_override_allowed_for_internal_access", True),
        ("owner_override_cannot_create_external_fact_or_runtime_receipt", True),
    )
    for key, expected in block_checks:
        if block.get(key) != expected:
            failures.append(f"default_agent_eligibility_block.{key} must be {expected!r}")

    _require_exact_list(
        failures,
        label="future_governance_row_kinds",
        actual=config.get("future_governance_row_kinds"),
        expected=REQUIRED_GOVERNANCE_ROW_KINDS,
    )
    _require_exact_list(
        failures,
        label="access_states",
        actual=config.get("access_states"),
        expected=REQUIRED_ACCESS_STATES,
    )
    _require_exact_list(
        failures,
        label="agent_access_evaluator_decision_order",
        actual=config.get("agent_access_evaluator_decision_order"),
        expected=REQUIRED_ACCESS_DECISION_STEPS,
    )
    if config.get("agent_access_default_decision") != "DENY":
        failures.append("agent_access_default_decision must be DENY")
    family_governance = _mapping(config.get("future_exact_row_family_governance"))
    if family_governance.get("primary_policy_row_file") != "009_lifecycle_agent_binding.exact_rows.jsonl":
        failures.append("future agent governance rows must primarily live in family 009")
    _require_exact_list(
        failures,
        label="future_exact_row_family_governance.policy_rows_may_cross_reference_families",
        actual=family_governance.get("policy_rows_may_cross_reference_families"),
        expected=REQUIRED_CROSS_REFERENCE_FAMILIES,
    )
    return failures


def validate_no_authority_claims(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    no_authority = _mapping(config.get("no_authority_created"))
    _require_false_fields(
        failures,
        no_authority,
        NO_AUTHORITY_FALSE_FIELDS,
        prefix="no_authority_created",
    )
    return failures


def validate_config_payload(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(schema_subset_failures(config, schema, "CONFIG"))
    failures.extend(validate_identity_and_static_flags(config))
    failures.extend(validate_authority_and_field_rules(config))
    failures.extend(validate_row_doctrine_and_architecture(config))
    failures.extend(validate_future_file_id_schema_and_sequence(config))
    failures.extend(validate_agent_governance(config))
    failures.extend(validate_no_authority_claims(config))
    return failures


def validate_upstream_state(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    pr97_plan, pr97_plan_failures = _load_yaml_checked(
        _resolve(repo_root, pr97_gate.DEFAULT_PRODUCTION_PLAN), "PR97_PLAN"
    )
    pr97_report, pr97_report_failures = _load_json_checked(
        _resolve(repo_root, pr97_gate.DEFAULT_REPORT), "PR97_REPORT"
    )
    pr98_report, pr98_report_failures = _load_json_checked(
        _resolve(repo_root, pr98_gate.DEFAULT_REPORT), "PR98_REPORT"
    )
    pr99_report, pr99_report_failures = _load_json_checked(
        _resolve(repo_root, pr99_gate.DEFAULT_REPORT), "PR99_REPORT"
    )
    pr100_report, pr100_report_failures = _load_json_checked(
        _resolve(repo_root, pr100_gate.DEFAULT_REPORT), "PR100_REPORT"
    )
    failures.extend(pr97_plan_failures)
    failures.extend(pr97_report_failures)
    failures.extend(pr98_report_failures)
    failures.extend(pr99_report_failures)
    failures.extend(pr100_report_failures)

    source_file_count_found = 0
    source_blueprints_found_count = 0
    exact_source_rows_found_count = 0
    pr98_blueprints_are_not_exact_rows = False
    inputs, input_failures = builder.load_bundle_inputs(
        repo_root=repo_root,
        builder_config_path=pr99_gate.DEFAULT_BUILDER_CONFIG,
    )
    failures.extend(input_failures)
    if inputs is not None:
        summary = inputs.source_summary
        source_file_count_found = len(summary.source_files)
        source_blueprints_found_count = len(summary.blueprints)
        exact_source_rows_found_count = len(summary.exact_rows)
        pr98_blueprints_are_not_exact_rows = (
            source_file_count_found == 15
            and source_blueprints_found_count == 15
            and exact_source_rows_found_count == 0
        )
        if source_file_count_found != 15:
            failures.append(f"PR98 source file count must be 15, got {source_file_count_found}")
        if source_blueprints_found_count != 15:
            failures.append(
                f"PR98 source blueprint count must be 15, got {source_blueprints_found_count}"
            )
        if exact_source_rows_found_count != 0:
            failures.append(
                f"exact source rows must remain absent, got {exact_source_rows_found_count}"
            )
        if summary.missing_source_files:
            failures.append("PR98 source files missing: " + ", ".join(summary.missing_source_files))
        if summary.unknown_source_files:
            failures.append("unknown PR98 source files found: " + ", ".join(summary.unknown_source_files))
        if builder.build_allowed(inputs):
            failures.append("PR99 builder inputs must remain blocked")

    if pr97_plan and pr97_plan.get("target_total_row_count") != 4183:
        failures.append("PR97 plan target_total_row_count must be 4183")
    if pr97_report and pr97_report.get("validation_marker") != pr97_gate.SUCCESS_MARKER:
        failures.append("PR97 report validation marker mismatch")
    if pr98_report and pr98_report.get("validation_marker") != pr98_gate.SUCCESS_MARKER:
        failures.append("PR98 report validation marker mismatch")
    if pr99_report and pr99_report.get("validation_marker") != pr99_gate.SUCCESS_MARKER:
        failures.append("PR99 report validation marker mismatch")
    if pr100_report and pr100_report.get("validator_stdout_marker") != pr100_gate.SUCCESS_MARKER:
        failures.append("PR100 report validator_stdout_marker mismatch")

    pr99_path_b = bool(
        pr99_report
        and pr99_report.get("build_path_decision") == builder.PATH_DECISION
        and pr99_report.get("build_allowed_flag") is False
    )
    if not pr99_path_b:
        failures.append("PR99 Path B blocked state must remain current")

    pr100_blocked = bool(
        pr100_report
        and pr100_report.get("gate_mode") == "BLOCKED"
        and pr100_report.get("sha_computed") is False
        and pr100_report.get("freeze_authority_created") is False
    )
    if not pr100_blocked:
        failures.append("PR100 SHA/freeze gate must remain blocked")

    return failures, {
        "pr97_expansion_plan_present": pr97_plan is not None,
        "pr97_report_present": pr97_report is not None,
        "pr97_target_total_rows": (pr97_plan or {}).get("target_total_row_count"),
        "pr98_report_present": pr98_report is not None,
        "pr98_source_file_count_found": source_file_count_found,
        "pr98_source_blueprints_found_count": source_blueprints_found_count,
        "pr98_exact_source_rows_found_count": exact_source_rows_found_count,
        "pr98_blueprints_are_not_exact_rows": pr98_blueprints_are_not_exact_rows,
        "pr99_report_present": pr99_report is not None,
        "pr99_path_b_remains_current_blocked_state": pr99_path_b,
        "pr100_report_present": pr100_report is not None,
        "pr100_sha_freeze_gate_remains_blocked": pr100_blocked,
    }


def validate_no_forbidden_artifacts(repo_root: pathlib.Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    for path in FORBIDDEN_ARTIFACT_PATHS:
        if _resolve(repo_root, path).exists():
            failures.append(f"forbidden artifact exists: {path.as_posix()}")

    atomic_rows_dir = _resolve(repo_root, pathlib.Path("docs") / "master_plan" / "atomic_rows")
    exact_row_files: list[str] = []
    if atomic_rows_dir.exists():
        exact_row_files = sorted(
            path.relative_to(repo_root).as_posix()
            for path in atomic_rows_dir.rglob("*.exact_rows.jsonl")
        )
    if exact_row_files:
        failures.append("forbidden exact row source files exist: " + ", ".join(exact_row_files))

    exact_source_dir_abs = _resolve(repo_root, EXACT_ROW_SOURCES_DIR)
    exact_source_dir_exists = exact_source_dir_abs.exists()
    if exact_source_dir_exists and not exact_source_dir_abs.is_dir():
        failures.append(f"exact row source path is not a directory: {EXACT_ROW_SOURCES_DIR.as_posix()}")

    return failures, {
        "AtomicRows.bundle.jsonl": not _resolve(repo_root, CANONICAL_BUNDLE_JSONL).exists(),
        "AtomicRows.bundle.sha256": not _resolve(repo_root, CANONICAL_BUNDLE_SHA256).exists(),
        "exact_row_sources": len(exact_row_files) == 0,
        "exact_row_source_directory_exists": exact_source_dir_exists,
        "exact_row_source_files_found": exact_row_files,
    }


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    return pr98_gate.validate_master_plan_not_modified(repo_root)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def validate_static_surface(path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path.as_posix()} is not valid Python: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = [alias.name.split(".", 1)[0].lower() for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots = [node.module.split(".", 1)[0].lower()]
        else:
            imported_roots = []
        for root in imported_roots:
            if root in FORBIDDEN_STATIC_SURFACE_IMPORT_ROOTS:
                failures.append(f"{path.name} imports forbidden runtime/quantum module {root}")
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALL_NAMES:
                failures.append(f"{path.name} calls forbidden materializing function {call_name}")
    return failures


def build_report(
    *,
    config: dict[str, Any],
    upstream: dict[str, Any],
    forbidden_artifacts_absent: dict[str, Any],
    schema_path: pathlib.Path,
    config_path: pathlib.Path,
    report_path: pathlib.Path,
) -> dict[str, Any]:
    agent_governance = copy.deepcopy(_mapping(config.get("agent_eligibility_governance")))
    return {
        "report_type": REPORT_TYPE,
        "artifact_id": ARTIFACT_ID,
        "artifact_version": ARTIFACT_VERSION,
        "repair_scope": REPAIR_SCOPE,
        "authority_class": AUTHORITY_CLASS,
        "gate_mode": GATE_MODE,
        "validation_result": "PASS",
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_marker": SUCCESS_MARKER,
        "validator_stdout_marker": SUCCESS_MARKER,
        "schema_path": schema_path.as_posix(),
        "config_path": config_path.as_posix(),
        "report_path": report_path.as_posix(),
        "bridge_created": True,
        "exact_rows_created": False,
        "atomicrows_bundle_jsonl_created": False,
        "atomicrows_bundle_sha256_created": False,
        "sha_computed": False,
        "freeze_authority_created": False,
        "final_readiness_created": False,
        "current_target_total_rows": 4183,
        "target_total_row_count_is_planning_only_until_exact_rows_generated": True,
        "pr97_expansion_plan_present": upstream.get("pr97_expansion_plan_present"),
        "pr98_blueprints_are_not_exact_rows": upstream.get("pr98_blueprints_are_not_exact_rows"),
        "pr99_path_b_remains_current_blocked_state": upstream.get(
            "pr99_path_b_remains_current_blocked_state"
        ),
        "pr100_sha_freeze_gate_remains_blocked": upstream.get(
            "pr100_sha_freeze_gate_remains_blocked"
        ),
        "canonical_row_fill_architecture_defined": True,
        "future_row_file_strategy_defined": True,
        "future_row_id_law_defined": True,
        "future_exact_row_schema_doctrine_defined": True,
        "recovery_pr_sequence_doctrine_defined": True,
        "exact_row_source_directory_defined": True,
        "exact_row_source_files_defined_for_15_families": True,
        "bundle_materializer_future_only": True,
        "sha_freeze_materializer_future_only": True,
        "final_readiness_gate_future_only": True,
        "agent_eligibility_governance_required": True,
        "agent_access_policy_rows_required": True,
        "deny_by_default_agent_access_policy_required": True,
        "row_existence_does_not_grant_agent_access": True,
        "family_membership_does_not_grant_agent_access": True,
        "parameter_existence_does_not_grant_agent_access": True,
        "algorithm_applicability_does_not_grant_agent_access": True,
        "quantum_applicability_does_not_grant_agent_access": True,
        "owner_quantum_priority_does_not_grant_agent_access": True,
        "replay_paper_eligibility_does_not_grant_live_access": True,
        "static_selection_eligibility_does_not_grant_order_authority": True,
        "static_handoff_eligibility_does_not_grant_order_authority": True,
        "missing_agent_binding_blocks_access": True,
        "missing_algorithm_binding_blocks_access": True,
        "missing_command_matrix_blocks_access": True,
        "unknown_eligibility_state_blocks_access": True,
        "live_use_allowed_default": False,
        "direct_order_authority_allowed_default": False,
        "direct_quantum_order_authority_allowed_default": False,
        "owner_override_cannot_create_agent_live_order_authority_without_later_live_scope": True,
        "owner_approval_cannot_fabricate_bundle_rows_or_external_evidence": True,
        "forbidden_artifacts_absent": {
            "AtomicRows.bundle.jsonl": forbidden_artifacts_absent.get(
                "AtomicRows.bundle.jsonl"
            ),
            "AtomicRows.bundle.sha256": forbidden_artifacts_absent.get(
                "AtomicRows.bundle.sha256"
            ),
            "exact_row_sources": forbidden_artifacts_absent.get("exact_row_sources"),
        },
        "exact_row_source_directory_exists": forbidden_artifacts_absent.get(
            "exact_row_source_directory_exists"
        ),
        "exact_row_source_files_found": forbidden_artifacts_absent.get(
            "exact_row_source_files_found"
        ),
        "master_plan_unchanged": True,
        "authority_classes": list(REQUIRED_AUTHORITY_CLASSES),
        "field_authority_handling": copy.deepcopy(config.get("field_authority_handling")),
        "field_fill_rules": copy.deepcopy(config.get("field_fill_rules")),
        "row_field_doctrine": copy.deepcopy(config.get("row_field_doctrine")),
        "canonical_row_fill_architecture": copy.deepcopy(
            config.get("canonical_row_fill_architecture")
        ),
        "future_row_file_strategy": copy.deepcopy(config.get("future_row_file_strategy")),
        "future_row_id_law": copy.deepcopy(config.get("future_row_id_law")),
        "future_exact_row_schema_doctrine": copy.deepcopy(
            config.get("future_exact_row_schema_doctrine")
        ),
        "recovery_pr_sequence_doctrine": copy.deepcopy(
            config.get("recovery_pr_sequence_doctrine")
        ),
        "agent_eligibility_governance": agent_governance,
        "future_governance_row_kinds": list(REQUIRED_GOVERNANCE_ROW_KINDS),
        "access_states": list(REQUIRED_ACCESS_STATES),
        "agent_access_evaluator_decision_order": list(REQUIRED_ACCESS_DECISION_STEPS),
        "agent_access_default_decision": "DENY",
        "future_exact_row_family_governance": copy.deepcopy(
            config.get("future_exact_row_family_governance")
        ),
        "no_authority_created": copy.deepcopy(config.get("no_authority_created")),
        "upstream_status": copy.deepcopy(upstream),
        "next_required_repair_pr": "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST",
    }


def validate_report_is_deterministic(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    first = serialize_report(report)
    second = serialize_report(copy.deepcopy(report))
    if first != second:
        failures.append("generated report serialization is not byte-stable")
    if report != json.loads(first):
        failures.append("generated report serialization is not deterministic sorted JSON")
    if report.get("generated_at_utc") != "STATIC_DETERMINISTIC_NO_WALL_CLOCK":
        failures.append("generated report must use deterministic generated_at_utc sentinel")
    forbidden_patterns = (
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        re.compile(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        re.compile(r"[A-Za-z]:\\\\"),
        re.compile(r"\\\\"),
    )
    for pattern in forbidden_patterns:
        if pattern.search(first):
            failures.append("generated report contains nondeterministic or platform-specific content")
            break
    return failures


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    checks = (
        ("report_type", REPORT_TYPE),
        ("artifact_id", ARTIFACT_ID),
        ("validation_result", "PASS"),
        ("validator_stdout_marker", SUCCESS_MARKER),
        ("bridge_created", True),
        ("exact_rows_created", False),
        ("atomicrows_bundle_jsonl_created", False),
        ("atomicrows_bundle_sha256_created", False),
        ("sha_computed", False),
        ("freeze_authority_created", False),
        ("final_readiness_created", False),
        ("current_target_total_rows", 4183),
        ("target_total_row_count_is_planning_only_until_exact_rows_generated", True),
        ("pr97_expansion_plan_present", True),
        ("pr98_blueprints_are_not_exact_rows", True),
        ("pr99_path_b_remains_current_blocked_state", True),
        ("pr100_sha_freeze_gate_remains_blocked", True),
        ("canonical_row_fill_architecture_defined", True),
        ("future_row_file_strategy_defined", True),
        ("future_row_id_law_defined", True),
        ("future_exact_row_schema_doctrine_defined", True),
        ("recovery_pr_sequence_doctrine_defined", True),
        ("agent_eligibility_governance_required", True),
        ("agent_access_policy_rows_required", True),
        ("deny_by_default_agent_access_policy_required", True),
        ("live_use_allowed_default", False),
        ("direct_order_authority_allowed_default", False),
        ("direct_quantum_order_authority_allowed_default", False),
        ("next_required_repair_pr", "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST"),
    )
    for key, expected in checks:
        if report.get(key) != expected:
            failures.append(f"report.{key} must be {expected!r}")
    forbidden_absent = _mapping(report.get("forbidden_artifacts_absent"))
    for key in ("AtomicRows.bundle.jsonl", "AtomicRows.bundle.sha256", "exact_row_sources"):
        if forbidden_absent.get(key) is not True:
            failures.append(f"report.forbidden_artifacts_absent.{key} must be true")
    _require_exact_list(
        failures,
        label="report.authority_classes",
        actual=report.get("authority_classes"),
        expected=REQUIRED_AUTHORITY_CLASSES,
    )
    _require_exact_list(
        failures,
        label="report.future_governance_row_kinds",
        actual=report.get("future_governance_row_kinds"),
        expected=REQUIRED_GOVERNANCE_ROW_KINDS,
    )
    _require_exact_list(
        failures,
        label="report.access_states",
        actual=report.get("access_states"),
        expected=REQUIRED_ACCESS_STATES,
    )
    no_authority = _mapping(report.get("no_authority_created"))
    _require_false_fields(
        failures,
        no_authority,
        NO_AUTHORITY_FALSE_FIELDS,
        prefix="report.no_authority_created",
    )
    failures.extend(validate_report_is_deterministic(report))
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    config_path: pathlib.Path = DEFAULT_CONFIG,
    output_path: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    schema_abs = _resolve(repo_root, schema_path)
    config_abs = _resolve(repo_root, config_path)
    output_abs = _resolve(repo_root, output_path)

    failures: list[str] = []
    schema, schema_failures = _load_json_checked(schema_abs, "SCHEMA")
    config, config_failures = _load_yaml_checked(config_abs, "CONFIG")
    failures.extend(schema_failures)
    failures.extend(config_failures)
    if schema is None or config is None:
        return ValidationResult(False, tuple(failures), None)

    upstream_failures, upstream = validate_upstream_state(repo_root)
    failures.extend(upstream_failures)
    forbidden_failures, forbidden_artifacts_absent = validate_no_forbidden_artifacts(repo_root)
    failures.extend(forbidden_failures)
    failures.extend(validate_master_plan_not_modified(repo_root))
    failures.extend(validate_static_surface(repo_root / "tools" / pathlib.Path(__file__).name))
    failures.extend(validate_config_payload(config, schema))

    report = build_report(
        config=config,
        upstream=upstream,
        forbidden_artifacts_absent=forbidden_artifacts_absent,
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    second_report = build_report(
        config=copy.deepcopy(config),
        upstream=copy.deepcopy(upstream),
        forbidden_artifacts_absent=copy.deepcopy(forbidden_artifacts_absent),
        schema_path=schema_path,
        config_path=config_path,
        report_path=output_path,
    )
    if report != second_report:
        failures.append("generated report is not deterministic across builds")
    failures.extend(validate_report(report))

    if failures:
        return ValidationResult(False, tuple(failures), report)

    write_json_report(report, output_abs)
    return ValidationResult(True, tuple(), report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate AtomicRows exact-row authority classifier bridge."
    )
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", dest="output_path", type=pathlib.Path, default=DEFAULT_REPORT)
    parser.add_argument("--report-out", dest="output_path", type=pathlib.Path)
    args = parser.parse_args(argv)

    result = validate(
        repo_root=args.repo_root,
        schema_path=args.schema,
        config_path=args.config,
        output_path=args.output_path,
    )
    if result.ok:
        print(SUCCESS_MARKER)
        for line in result.info_lines:
            print(line)
        return 0

    print(FAILURE_MARKER, file=sys.stderr)
    for line in result.info_lines:
        print(line, file=sys.stderr)
    for failure in result.failures:
        print(failure, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
