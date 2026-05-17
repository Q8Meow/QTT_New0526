#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

SUCCESS_MARKER = "STAGE1_PACKET_SCHEMA_GATE_STATIC_VALIDATION_OK"
FAILURE_MARKER = "STAGE1_PACKET_SCHEMA_GATE_STATIC_VALIDATION_FAILED"

SCHEMA_AUTHORITY_CLASS = "STATIC_STAGE1_PACKET_SCHEMA_CONTRACT_ONLY"
PACKET_AUTHORITY_CLASS = "SCHEMA_ONLY_STATIC_PACKET_NOT_RUNTIME_AUTHORITY"
VALIDATION_HOOK = "STAGE1_PACKET_SCHEMA_GATE_STATIC_AUDIT"
PLACEHOLDER = "SOURCE_REQUIRED_PLACEHOLDER"
PARAMETER_REVITALIZATION_ALLOWED_STATUSES = [
    "REQUIRED",
    "BLOCKED_PENDING_IMPLEMENTATION",
]

CANONICAL_BUNDLE_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA_RELATIVE_PATH = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)

EXPECTED_PACKET_FAMILIES = [
    "stage1_connector_fact_packet",
    "stage1_source_packet_to_code_binding",
    "stage1_resolver_snapshot_packet",
    "stage1_resolver_input_lock_packet",
    "stage1_replay_paper_run_input_manifest",
    "stage1_replay_result_packet",
    "stage1_paper_result_packet",
    "stage1_dual_result_review_packet",
    "stage1_transition_gate_packet",
    "stage1_comparable_contract_event_match_packet",
    "stage1_arbitrage_comparability_gate_packet",
    "stage1_dashboard_duration_change_packet",
    "stage1_capital_cash_component_receipt",
    "stage1_limited_live_canary_result_packet",
    "stage1_owner_live_promotion_review_packet",
    "stage1_packet_schema_gate_report",
]

EXPECTED_SCHEMA_FILES = {
    family: f"{family}.schema.json"
    for family in EXPECTED_PACKET_FAMILIES
}

COMMON_SCHEMA_CONST_EXPECTATIONS = {
    "schema_authority_class": SCHEMA_AUTHORITY_CLASS,
    "packet_authority_class": PACKET_AUTHORITY_CLASS,
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "schema_only_static_audit": True,
    "contracts_only": True,
    "generated_derivative_gate_receipt_required": True,
    "source_evidence_gate_confirmation_receipt_required": True,
    "source_required_placeholder_policy": PLACEHOLDER,
    "accepted_source_packets_required_before_connector_facts": True,
    "source_fact_acceptance_allowed": False,
    "connector_binding_allowed": False,
    "exact_market_selection_allowed": False,
    "runtime_creation_allowed": False,
    "live_reachability_allowed": False,
    "order_authority_allowed": False,
    "blocker_reduction_allowed": False,
    "profit_claim_allowed": False,
    "atomicrows_authority_allowed": False,
}

COMMON_SCHEMA_FIELDS = set(COMMON_SCHEMA_CONST_EXPECTATIONS) | {
    "packet_family",
    "packet_version",
    "parameter_revitalization_gate_status",
}

SPECIFIC_SCHEMA_CONST_EXPECTATIONS = {
    "stage1_connector_fact_packet": {
        "connector_source_dependent_fields_value": PLACEHOLDER,
    },
    "stage1_source_packet_to_code_binding": {
        "code_binding_allowed_without_source_acceptance": False,
    },
    "stage1_resolver_snapshot_packet": {
        "runtime_resolver_snapshot_creation_allowed": False,
    },
    "stage1_resolver_input_lock_packet": {
        "runtime_input_lock_creation_allowed": False,
    },
    "stage1_replay_paper_run_input_manifest": {
        "replay_execution_allowed": False,
        "paper_execution_allowed": False,
    },
    "stage1_replay_result_packet": {
        "result_lane": "REPLAY",
        "runtime_result_creation_allowed": False,
        "merge_with_paper_allowed": False,
    },
    "stage1_paper_result_packet": {
        "result_lane": "PAPER",
        "runtime_result_creation_allowed": False,
        "merge_with_replay_allowed": False,
    },
    "stage1_dual_result_review_packet": {
        "dual_review_may_compare": True,
        "dual_review_may_overwrite_replay": False,
        "dual_review_may_overwrite_paper": False,
    },
    "stage1_transition_gate_packet": {
        "shadow_mandatory_before_canary": False,
        "live_transition_execution_allowed": False,
    },
    "stage1_comparable_contract_event_match_packet": {
        "exact_contract_event_match_claim_allowed": False,
    },
    "stage1_arbitrage_comparability_gate_packet": {
        "arbitrage_execution_allowed": False,
        "profit_evidence_creation_allowed": False,
    },
    "stage1_dashboard_duration_change_packet": {
        "dashboard_runtime_update_allowed": False,
    },
    "stage1_capital_cash_component_receipt": {
        "schema_receipt_only": True,
        "real_runtime_cash_receipt_created": False,
        "private_state_fetch_allowed": False,
    },
    "stage1_limited_live_canary_result_packet": {
        "risk_caps_required": True,
        "owner_review_required": True,
        "fail_closed_receipts_required": True,
        "runtime_canary_execution_allowed": False,
    },
    "stage1_owner_live_promotion_review_packet": {
        "risk_caps_required": True,
        "owner_review_required": True,
        "fail_closed_receipts_required": True,
        "live_promotion_authority_allowed": False,
    },
    "stage1_packet_schema_gate_report": {
        "gate_report_only": True,
    },
}

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "validation_mode",
    "deterministic_output",
    "expected_schema_families",
    "schema_contracts",
    "prerequisite_gate_receipts",
    "source_dependency_policy",
    "lane_separation_policy",
    "live_transition_policy",
    "capital_cash_policy",
    "atomicrows_authority_state",
    "authority_scope_flags",
    "forbidden_action_flags",
    "no_claim_flags",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR33_STAGE1_PACKET_SCHEMA_GATE_BLOCKED_FIXTURE",
    "fixture_version": "PR33_STAGE1_PACKET_SCHEMA_GATE_BLOCKED_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_STAGE1_RUNTIME_AUTHORITY"
    ),
    "schema_authority_class": SCHEMA_AUTHORITY_CLASS,
    "surface_kind": "STAGE1_PACKET_SCHEMA_GATE_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "validation_mode": "STATIC_SCHEMA_ONLY_NON_MUTATING_AUDIT",
    "deterministic_output": True,
}

SCHEMA_CONTRACT_FIELDS = {
    "packet_family",
    "schema_path",
    "schema_exists_required",
    "schema_contract_only",
    "source_required_mode_required",
    "disabled_execution_required",
    "accepted_source_packets_required_before_connector_facts",
    "exact_selection_allowed",
    "source_fact_acceptance_allowed",
    "connector_binding_allowed",
    "runtime_creation_allowed",
    "live_reachability_allowed",
    "order_authority_allowed",
    "blocker_reduction_allowed",
    "profit_claim_allowed",
    "atomicrows_authority_allowed",
}

SCHEMA_CONTRACT_EXPECTED_FLAGS = {
    "schema_exists_required": True,
    "schema_contract_only": True,
    "source_required_mode_required": True,
    "disabled_execution_required": True,
    "accepted_source_packets_required_before_connector_facts": True,
    "exact_selection_allowed": False,
    "source_fact_acceptance_allowed": False,
    "connector_binding_allowed": False,
    "runtime_creation_allowed": False,
    "live_reachability_allowed": False,
    "order_authority_allowed": False,
    "blocker_reduction_allowed": False,
    "profit_claim_allowed": False,
    "atomicrows_authority_allowed": False,
}

PREREQUISITE_RECEIPT_EXPECTATIONS = {
    "generated_derivative_gate_receipt_required": True,
    "generated_derivative_gate_receipt_status": "REQUIRED",
    "source_evidence_gate_confirmation_receipt_required": True,
    "source_evidence_gate_confirmation_receipt_status": "REQUIRED",
    "parameter_revitalization_gate_required": True,
    "parameter_revitalization_gate_status": "BLOCKED_PENDING_IMPLEMENTATION",
    "parameter_revitalization_gate_satisfied": False,
    "schema_gate_authority_scope": "SCHEMA_ONLY_STATIC_AUDIT",
}

SOURCE_DEPENDENCY_EXPECTATIONS = {
    "accepted_source_packets_exist": False,
    "accepted_source_packets_created": False,
    "connector_source_dependent_fields_must_remain_placeholder": True,
    "connector_source_dependent_fields_value": PLACEHOLDER,
    "source_retrieval_claimed": False,
    "source_fact_acceptance_claimed": False,
    "connector_binding_claimed": False,
}

LANE_SEPARATION_EXPECTATIONS = {
    "replay_schema_family": "stage1_replay_result_packet",
    "paper_schema_family": "stage1_paper_result_packet",
    "replay_and_paper_schemas_separate": True,
    "replay_paper_merge_allowed": False,
    "replay_execution_claimed": False,
    "paper_execution_claimed": False,
    "runtime_replay_result_packet_created": False,
    "runtime_paper_result_packet_created": False,
    "dual_result_review_may_compare": True,
    "dual_result_review_may_overwrite_replay": False,
    "dual_result_review_may_overwrite_paper": False,
}

LIVE_TRANSITION_EXPECTATIONS = {
    "transition_schema_family": "stage1_transition_gate_packet",
    "shadow_mandatory_before_canary": False,
    "limited_live_canary_schema_family": "stage1_limited_live_canary_result_packet",
    "owner_live_promotion_review_schema_family": "stage1_owner_live_promotion_review_packet",
    "canary_risk_caps_required": True,
    "canary_owner_review_required": True,
    "canary_fail_closed_receipts_required": True,
    "owner_promotion_risk_caps_required": True,
    "owner_promotion_owner_review_required": True,
    "owner_promotion_fail_closed_receipts_required": True,
    "limited_live_canary_execution_claimed": False,
    "owner_live_promotion_claimed": False,
    "live_reachability_claimed": False,
    "order_authority_claimed": False,
}

CAPITAL_CASH_EXPECTATIONS = {
    "schema_family": "stage1_capital_cash_component_receipt",
    "schema_receipt_only": True,
    "real_runtime_cash_receipt_created": False,
    "balance_fetch_claimed": False,
    "account_state_fetch_claimed": False,
    "private_state_fetch_claimed": False,
}

ATOMICROWS_STATE_EXPECTATIONS = {
    "canonical_bundle_path": str(CANONICAL_BUNDLE_RELATIVE_PATH),
    "canonical_bundle_sha_path": str(CANONICAL_BUNDLE_SHA_RELATIVE_PATH),
    "canonical_bundle_present": True,
    "canonical_bundle_sha_present": False,
    "atomicrows_bundle_creation_claimed": False,
    "atomicrows_hash_creation_claimed": False,
    "atomicrows_sha_authority_claimed": False,
    "atomicrows_row_creation_claimed": False,
    "atomicrows_completion_claimed": False,
    "claims_4183_row_completion": False,
    "freeze_authority_claimed": False,
}

AUTHORITY_SCOPE_FLAG_EXPECTATIONS = {
    "static_schema_gate_only": True,
    "static_validation_only": True,
    "non_mutating_validator": True,
    "schemas_are_contracts_only": True,
    "generated_derivative_gate_receipt_required": True,
    "source_evidence_gate_confirmation_receipt_required": True,
    "parameter_revitalization_gate_required": True,
    "parameter_revitalization_gate_blocked_or_required": True,
    "source_required_placeholders_required": True,
    "replay_and_paper_schemas_separate": True,
    "dual_result_review_compare_only": True,
    "limited_live_canary_requires_risk_caps_owner_review_fail_closed": True,
    "owner_promotion_requires_risk_caps_owner_review_fail_closed": True,
    "capital_cash_schema_receipt_only": True,
    "source_retrieval_allowed": False,
    "source_fact_acceptance_allowed": False,
    "accepted_source_packet_creation_allowed": False,
    "connector_binding_allowed": False,
    "exact_market_selection_allowed": False,
    "runtime_resolver_snapshot_creation_allowed": False,
    "replay_execution_allowed": False,
    "paper_execution_allowed": False,
    "replay_paper_merge_allowed": False,
    "dual_result_overwrite_allowed": False,
    "shadow_mandatory_before_canary_allowed": False,
    "live_reachability_allowed": False,
    "private_state_fetch_allowed": False,
    "order_authority_allowed": False,
    "blocker_reduction_allowed": False,
    "profit_claim_allowed": False,
    "atomicrows_authority_allowed": False,
    "freeze_authority_allowed": False,
}

FORBIDDEN_ACTION_FLAGS = {
    "source_retrieval_enabled",
    "source_fact_acceptance_enabled",
    "accepted_source_packet_creation_enabled",
    "accepted_source_evidence_packet_creation_enabled",
    "connector_binding_enabled",
    "connector_semantic_binding_enabled",
    "exact_market_selection_enabled",
    "exact_contract_selection_enabled",
    "exact_event_selection_enabled",
    "exact_symbol_selection_enabled",
    "exact_venue_selection_enabled",
    "live_venue_selection_enabled",
    "runtime_resolver_snapshot_creation_enabled",
    "replay_execution_enabled",
    "paper_execution_enabled",
    "runtime_replay_result_packet_creation_enabled",
    "runtime_paper_result_packet_creation_enabled",
    "replay_paper_merge_enabled",
    "dual_result_review_overwrite_enabled",
    "shadow_mandatory_before_canary_enabled",
    "limited_live_canary_without_risk_caps_enabled",
    "limited_live_canary_without_owner_review_enabled",
    "limited_live_canary_without_fail_closed_receipts_enabled",
    "real_runtime_cash_receipt_creation_enabled",
    "private_state_fetch_enabled",
    "balance_fetch_enabled",
    "account_state_fetch_enabled",
    "live_reachability_enabled",
    "order_execution_authority_enabled",
    "order_submit_enabled",
    "order_cancel_enabled",
    "order_reduce_enabled",
    "order_close_enabled",
    "blocker_reduction_enabled",
    "profit_claim_enabled",
    "profit_evidence_creation_enabled",
    "atomicrows_bundle_creation_enabled",
    "atomicrows_bundle_hash_creation_enabled",
    "atomicrows_sha_computation_enabled",
    "atomicrows_sha_authority_enabled",
    "atomicrows_row_creation_enabled",
    "atomicrows_completion_claim_enabled",
    "freeze_authority_enabled",
    "neural_training_enabled",
    "neural_inference_enabled",
}

NO_CLAIM_FLAGS = {
    "claims_source_retrieval",
    "claims_source_fact_acceptance",
    "creates_accepted_source_packets",
    "creates_accepted_source_evidence_packets",
    "binds_connector_semantics",
    "selects_exact_markets",
    "selects_exact_contracts",
    "selects_exact_events",
    "selects_exact_symbols",
    "selects_exact_venues",
    "selects_live_venues",
    "creates_runtime_resolver_snapshots",
    "executes_replay",
    "executes_paper",
    "creates_runtime_replay_result_packets",
    "creates_runtime_paper_result_packets",
    "merges_replay_and_paper_results",
    "allows_dual_result_overwrite",
    "makes_shadow_mandatory_before_canary",
    "omits_canary_risk_caps",
    "omits_canary_owner_review",
    "omits_canary_fail_closed_receipts",
    "creates_real_runtime_cash_receipts",
    "fetches_private_state",
    "fetches_balances",
    "fetches_account_state",
    "creates_live_reachability",
    "creates_order_authority",
    "submits_orders",
    "cancels_orders",
    "reduces_orders",
    "closes_orders",
    "claims_blocker_reduction",
    "creates_profit_evidence",
    "creates_profit_claim",
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "computes_atomicrows_sha",
    "claims_atomicrows_sha_authority",
    "creates_atomicrows_rows",
    "creates_atomicrows_row_records",
    "claims_atomicrows_completion",
    "claims_4183_row_completion",
    "creates_freeze_authority",
}

FORBIDDEN_ROW_RECORD_KEYS = {
    "row",
    "rows",
    "row_record",
    "row_records",
    "atomic_row",
    "atomic_rows",
    "atomicrows_row",
    "atomicrows_rows",
    "atomicrows_row_record",
    "atomicrows_row_records",
    "bundle_row",
    "bundle_rows",
}

FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "http",
    "https",
    "kalshi",
    "polymarket",
    "forecastx",
    "forecastex",
    "ibkr",
    "interactivebrokers",
    "secret_key",
    "client_secret",
    "sk_live",
    "pk_live",
    "bearer ",
    "password",
    "account_id",
    "owner_uploaded_private_doc_locator",
    "-----begin",
}


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is not valid JSON: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _properties(definition: dict[str, Any]) -> dict[str, Any]:
    properties = definition.get("properties", {})
    return properties if isinstance(properties, dict) else {}


def _const_value(definition: dict[str, Any], property_name: str) -> Any:
    prop = _properties(definition).get(property_name, {})
    return prop.get("const") if isinstance(prop, dict) else None


def _require_exact_fields(value: dict[str, Any], fields: set[str], label: str) -> list[str]:
    failures: list[str] = []
    missing = sorted(fields - set(value))
    unexpected = sorted(set(value) - fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _validate_const_map(
    value: dict[str, Any],
    expected: dict[str, Any],
    label: str,
) -> list[str]:
    failures = _require_exact_fields(value, set(expected), label)
    for field, expected_value in sorted(expected.items()):
        if value.get(field) != expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    return failures


def _validate_bool_map(
    value: dict[str, Any],
    expected: dict[str, bool] | set[str],
    label: str,
) -> list[str]:
    expected_values = (
        {field: False for field in expected}
        if isinstance(expected, set)
        else dict(expected)
    )
    return _validate_const_map(value, expected_values, label)


def _mapping(value: dict[str, Any], field: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    item = value.get(field)
    if not isinstance(item, dict):
        return None, [f"{label}.{field} must be an object"]
    return item, []


def _walk(value: Any, path: str = "fixture"):
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


def _canonical_path(root: pathlib.Path, rel_path: pathlib.PurePosixPath) -> pathlib.Path:
    return root / pathlib.Path(*rel_path.parts)


def _actual_atomicrows_presence(repo_root: pathlib.Path) -> tuple[bool, bool]:
    root = repo_root.resolve()
    bundle_path = _canonical_path(root, CANONICAL_BUNDLE_RELATIVE_PATH)
    sha_path = _canonical_path(root, CANONICAL_BUNDLE_SHA_RELATIVE_PATH)
    return bundle_path.exists(), sha_path.exists()


def _validate_schema_file_set(schema_dir: pathlib.Path) -> list[str]:
    failures: list[str] = []
    if not schema_dir.is_dir():
        return [f"schema directory is missing: {schema_dir}"]

    observed = sorted(path.name for path in schema_dir.glob("*.schema.json"))
    expected = sorted(EXPECTED_SCHEMA_FILES.values())
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    if missing:
        failures.append(f"stage1 schema directory missing schema files: {', '.join(missing)}")
    if extra:
        failures.append(f"stage1 schema directory has unexpected schema files: {', '.join(extra)}")
    return failures


def _validate_schema_contract(schema: dict[str, Any], family: str, schema_path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    expected_id = f"https://qtt.local/schemas/stage1_prediction_markets/{schema_path.name}"
    if schema.get("$id") != expected_id:
        failures.append(f"{schema_path.name}.$id must be {expected_id}")
    if schema.get("type") != "object":
        failures.append(f"{schema_path.name}.type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(f"{schema_path.name}.additionalProperties must be false")

    properties = _properties(schema)
    required = schema.get("required")
    if not isinstance(required, list):
        failures.append(f"{schema_path.name}.required must be a list")
        required_fields: set[str] = set()
    else:
        required_fields = set(required)
        if len(required) != len(required_fields):
            failures.append(f"{schema_path.name}.required must not contain duplicate fields")

    expected_fields = COMMON_SCHEMA_FIELDS | set(
        SPECIFIC_SCHEMA_CONST_EXPECTATIONS[family]
    )
    failures.extend(_require_exact_fields(properties, expected_fields, f"{schema_path.name}.properties"))
    missing_required = sorted(expected_fields - required_fields)
    unexpected_required = sorted(required_fields - expected_fields)
    if missing_required:
        failures.append(f"{schema_path.name} missing required fields: {', '.join(missing_required)}")
    if unexpected_required:
        failures.append(
            f"{schema_path.name} has unexpected required fields: {', '.join(unexpected_required)}"
        )

    if _const_value(schema, "packet_family") != family:
        failures.append(f"{schema_path.name}.packet_family must be const {family}")
    if _const_value(schema, "packet_version") != f"{family}.v1":
        failures.append(f"{schema_path.name}.packet_version must be const {family}.v1")

    for field, expected in sorted(COMMON_SCHEMA_CONST_EXPECTATIONS.items()):
        if _const_value(schema, field) != expected:
            failures.append(f"{schema_path.name}.{field} must be const {expected}")

    parameter_gate = properties.get("parameter_revitalization_gate_status", {})
    if not isinstance(parameter_gate, dict) or parameter_gate.get("enum") != (
        PARAMETER_REVITALIZATION_ALLOWED_STATUSES
    ):
        failures.append(
            f"{schema_path.name}.parameter_revitalization_gate_status must allow only "
            "REQUIRED or BLOCKED_PENDING_IMPLEMENTATION"
        )

    for field, expected in sorted(SPECIFIC_SCHEMA_CONST_EXPECTATIONS[family].items()):
        if _const_value(schema, field) != expected:
            failures.append(f"{schema_path.name}.{field} must be const {expected}")
    return failures


def _validate_schema_surfaces(schema_dir: pathlib.Path) -> list[str]:
    failures = _validate_schema_file_set(schema_dir)
    for family in EXPECTED_PACKET_FAMILIES:
        schema_path = schema_dir / EXPECTED_SCHEMA_FILES[family]
        schema, schema_failures = _load_json(schema_path)
        failures.extend(schema_failures)
        if schema is not None:
            failures.extend(_validate_schema_contract(schema, family, schema_path))
    return failures


def _validate_schema_contracts(
    contracts: Any,
    *,
    schema_dir: pathlib.Path,
) -> list[str]:
    if not isinstance(contracts, list):
        return ["schema_contracts must be a list"]
    failures: list[str] = []
    if len(contracts) != len(EXPECTED_PACKET_FAMILIES):
        failures.append(
            "schema_contracts must contain exactly one contract per expected packet family"
        )

    seen_families: list[str] = []
    for index, contract in enumerate(contracts):
        label = f"schema_contracts[{index}]"
        if not isinstance(contract, dict):
            failures.append(f"{label} must be an object")
            continue
        failures.extend(_require_exact_fields(contract, SCHEMA_CONTRACT_FIELDS, label))
        family = contract.get("packet_family")
        seen_families.append(family) if isinstance(family, str) else None
        if family not in EXPECTED_SCHEMA_FILES:
            failures.append(f"{label}.packet_family must be an expected Stage-1 family")
            continue
        expected_path = pathlib.PurePosixPath(
            "schemas/stage1_prediction_markets"
        ) / EXPECTED_SCHEMA_FILES[family]
        if contract.get("schema_path") != str(expected_path):
            failures.append(f"{label}.schema_path must be {expected_path}")
        if not (schema_dir / EXPECTED_SCHEMA_FILES[family]).exists():
            failures.append(f"{label}.schema_path target must exist")
        for field, expected in sorted(SCHEMA_CONTRACT_EXPECTED_FLAGS.items()):
            if contract.get(field) != expected:
                failures.append(f"{label}.{field} must be {expected}")

    if seen_families != EXPECTED_PACKET_FAMILIES:
        failures.append("schema_contracts must preserve the expected Stage-1 family order")
    return failures


def _validate_prerequisite_receipts(receipts: dict[str, Any]) -> list[str]:
    failures = _validate_const_map(
        receipts,
        PREREQUISITE_RECEIPT_EXPECTATIONS,
        "prerequisite_gate_receipts",
    )
    status = receipts.get("parameter_revitalization_gate_status")
    if status not in PARAMETER_REVITALIZATION_ALLOWED_STATUSES:
        failures.append(
            "prerequisite_gate_receipts.parameter_revitalization_gate_status must be "
            "REQUIRED or BLOCKED_PENDING_IMPLEMENTATION"
        )
    return failures


def _validate_atomicrows_state(
    state: dict[str, Any],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures = _validate_const_map(
        state,
        ATOMICROWS_STATE_EXPECTATIONS,
        "atomicrows_authority_state",
    )
    bundle_present, sha_present = _actual_atomicrows_presence(repo_root)
    if state.get("canonical_bundle_present") is not bundle_present:
        failures.append(
            "atomicrows_authority_state.canonical_bundle_present must match "
            f"filesystem presence {bundle_present}"
        )
    if state.get("canonical_bundle_sha_present") is not sha_present:
        failures.append(
            "atomicrows_authority_state.canonical_bundle_sha_present must match "
            f"filesystem presence {sha_present}"
        )
    failures.extend(
        validate_current_atomicrows_bundle_state(
            repo_root,
            label="Stage-1 packet schema validation",
        )
    )
    return failures


def _validate_no_forbidden_claims(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    must_be_false = (
        FORBIDDEN_ACTION_FLAGS
        | NO_CLAIM_FLAGS
        | {
            field
            for field, expected in AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in SOURCE_DEPENDENCY_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in LANE_SEPARATION_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in LIVE_TRANSITION_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in CAPITAL_CASH_EXPECTATIONS.items()
            if expected is False
        }
        | {
            field
            for field, expected in ATOMICROWS_STATE_EXPECTATIONS.items()
            if expected is False
        }
    )
    must_be_true = (
        {
            field
            for field, expected in AUTHORITY_SCOPE_FLAG_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in SOURCE_DEPENDENCY_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in LANE_SEPARATION_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in LIVE_TRANSITION_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in CAPITAL_CASH_EXPECTATIONS.items()
            if expected is True
        }
        | {
            field
            for field, expected in PREREQUISITE_RECEIPT_EXPECTATIONS.items()
            if expected is True
        }
    )

    for path, key, item in _walk(fixture):
        if key in must_be_false and item is not False:
            failures.append(f"{path} must be false")
        if key in must_be_true and item is not True:
            failures.append(f"{path} must be true")
        if key in FORBIDDEN_ROW_RECORD_KEYS:
            failures.append(f"{path} must not contain AtomicRows row records")
        if key == "connector_source_dependent_fields_value" and item != PLACEHOLDER:
            failures.append(f"{path} must remain {PLACEHOLDER}")
        if key == "parameter_revitalization_gate_status" and item not in (
            PARAMETER_REVITALIZATION_ALLOWED_STATUSES
        ):
            failures.append(
                f"{path} must be REQUIRED or BLOCKED_PENDING_IMPLEMENTATION"
            )
        if isinstance(item, str):
            lowered = item.lower()
            if path.startswith("fixture.schema_contracts") and key == "schema_path":
                continue
            if path.startswith("fixture.atomicrows_authority_state") and key in {
                "canonical_bundle_path",
                "canonical_bundle_sha_path",
            }:
                continue
            for fragment in sorted(FORBIDDEN_TEXT_FRAGMENTS):
                if fragment in lowered:
                    failures.append(
                        f"{path} contains forbidden live/source/private fragment: {fragment}"
                    )
    return failures


def validate_stage1_packet_schema_gate_fixture(
    fixture: dict[str, Any],
    *,
    repo_root: pathlib.Path,
    schema_dir: pathlib.Path,
) -> list[str]:
    failures = _require_exact_fields(
        fixture,
        ROOT_FIELDS,
        "stage1 packet schema gate fixture",
    )
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(f"stage1 packet schema gate fixture.{field} must be {expected}")

    if fixture.get("expected_schema_families") != EXPECTED_PACKET_FAMILIES:
        failures.append("expected_schema_families must match the Stage-1 packet family set")

    failures.extend(
        _validate_schema_contracts(
            fixture.get("schema_contracts"),
            schema_dir=schema_dir,
        )
    )

    prerequisites, prerequisite_failures = _mapping(
        fixture,
        "prerequisite_gate_receipts",
        "stage1 packet schema gate fixture",
    )
    failures.extend(prerequisite_failures)
    if prerequisites is not None:
        failures.extend(_validate_prerequisite_receipts(prerequisites))

    source_dependency, source_failures = _mapping(
        fixture,
        "source_dependency_policy",
        "stage1 packet schema gate fixture",
    )
    failures.extend(source_failures)
    if source_dependency is not None:
        failures.extend(
            _validate_const_map(
                source_dependency,
                SOURCE_DEPENDENCY_EXPECTATIONS,
                "source_dependency_policy",
            )
        )

    lane_policy, lane_failures = _mapping(
        fixture,
        "lane_separation_policy",
        "stage1 packet schema gate fixture",
    )
    failures.extend(lane_failures)
    if lane_policy is not None:
        failures.extend(
            _validate_const_map(
                lane_policy,
                LANE_SEPARATION_EXPECTATIONS,
                "lane_separation_policy",
            )
        )

    live_policy, live_failures = _mapping(
        fixture,
        "live_transition_policy",
        "stage1 packet schema gate fixture",
    )
    failures.extend(live_failures)
    if live_policy is not None:
        failures.extend(
            _validate_const_map(
                live_policy,
                LIVE_TRANSITION_EXPECTATIONS,
                "live_transition_policy",
            )
        )

    capital_cash, cash_failures = _mapping(
        fixture,
        "capital_cash_policy",
        "stage1 packet schema gate fixture",
    )
    failures.extend(cash_failures)
    if capital_cash is not None:
        failures.extend(
            _validate_const_map(
                capital_cash,
                CAPITAL_CASH_EXPECTATIONS,
                "capital_cash_policy",
            )
        )

    atomicrows, atomicrows_failures = _mapping(
        fixture,
        "atomicrows_authority_state",
        "stage1 packet schema gate fixture",
    )
    failures.extend(atomicrows_failures)
    if atomicrows is not None:
        failures.extend(_validate_atomicrows_state(atomicrows, repo_root=repo_root))

    authority, authority_failures = _mapping(
        fixture,
        "authority_scope_flags",
        "stage1 packet schema gate fixture",
    )
    failures.extend(authority_failures)
    if authority is not None:
        failures.extend(
            _validate_bool_map(
                authority,
                AUTHORITY_SCOPE_FLAG_EXPECTATIONS,
                "authority_scope_flags",
            )
        )

    forbidden_actions, action_failures = _mapping(
        fixture,
        "forbidden_action_flags",
        "stage1 packet schema gate fixture",
    )
    failures.extend(action_failures)
    if forbidden_actions is not None:
        failures.extend(
            _validate_bool_map(
                forbidden_actions,
                FORBIDDEN_ACTION_FLAGS,
                "forbidden_action_flags",
            )
        )

    no_claims, no_claim_failures = _mapping(
        fixture,
        "no_claim_flags",
        "stage1 packet schema gate fixture",
    )
    failures.extend(no_claim_failures)
    if no_claims is not None:
        failures.extend(_validate_bool_map(no_claims, NO_CLAIM_FLAGS, "no_claim_flags"))

    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")

    failures.extend(_validate_no_forbidden_claims(fixture))
    return failures


def validate_static_surface(
    *,
    repo_root: pathlib.Path,
    schema_dir: pathlib.Path,
    fixture_path: pathlib.Path,
) -> list[str]:
    failures = _validate_schema_surfaces(schema_dir)
    fixture, fixture_failures = _load_json(fixture_path)
    failures.extend(fixture_failures)
    if fixture is not None:
        failures.extend(
            validate_stage1_packet_schema_gate_fixture(
                fixture,
                repo_root=repo_root,
                schema_dir=schema_dir,
            )
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--schema-dir", required=True)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    failures = validate_static_surface(
        repo_root=pathlib.Path(args.repo_root),
        schema_dir=pathlib.Path(args.schema_dir),
        fixture_path=pathlib.Path(args.fixture),
    )
    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
