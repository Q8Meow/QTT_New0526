#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder  # noqa: E402
from tools import validate_atomicrows_lifecycle_promotion_receipt_gate as promotion_gate  # noqa: E402
from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_lifecycle_registry_mutation_guard.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_lifecycle_registry_mutation_guard_blocked.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleRegistryMutationGuard.report.json"
)

REPORT_TYPE = "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_FINAL_INCOMPLETE"
)

MUTATION_CLASSES = (
    "STATUS_CHANGE",
    "PARAMETER_FAMILY_CHANGE",
    "CLASSICAL_OR_QUANTUM_CHANGE",
    "OWNER_SECTION_ID_CHANGE",
    "LINKED_CAPABILITY_ID_CHANGE",
    "UNIT_CHANGE",
    "SCALE_CHANGE",
    "ALLOWED_RANGE_CHANGE",
    "DEFAULT_VALUE_POLICY_CHANGE",
    "SOURCE_AUTHORITY_CLASS_CHANGE",
    "EVIDENCE_REQUIRED_CHANGE",
    "OPTIMIZER_ELIGIBILITY_CHANGE",
    "RUNTIME_ELIGIBILITY_CHANGE",
    "LIVE_ELIGIBILITY_CHANGE",
    "RESEARCH_ROUTE_CHANGE",
    "PROMOTION_GATE_CHANGE",
    "QUARANTINE_REASON_CHANGE",
    "RETIREMENT_REASON_CHANGE",
    "ROW_ID_ADDITION",
    "ROW_ID_REMOVAL",
    "OWNER_OVERRIDE_MUTATION",
)

OWNER_OVERRIDE_RECEIPT_TYPES = (
    "OWNER_LIFECYCLE_OVERRIDE_RECEIPT",
    "OWNER_PROMOTION_OVERRIDE_RECEIPT",
)

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "deterministic_output",
    "registry_path",
    "lifecycle_report_path",
    "promotion_receipt_gate_report_path",
    "mutation_classes",
    "owner_override_receipt_types",
    "attempted_mutations",
    "authority_boundary",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_PR56_ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_BLOCKED_FIXTURE"
    ),
    "fixture_version": (
        "PR56_ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_BLOCKED_FIXTURE_V1"
    ),
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_MUTATION_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_MUTATION_AUTHORITY"
    ),
    "surface_kind": "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "registry_path": str(lifecycle_builder.DEFAULT_REGISTRY).replace("\\", "/"),
    "lifecycle_report_path": str(lifecycle_builder.DEFAULT_OUTPUT).replace("\\", "/"),
    "promotion_receipt_gate_report_path": str(promotion_gate.DEFAULT_REPORT).replace(
        "\\",
        "/",
    ),
}

ATTEMPT_FIELDS = {
    "attempt_id",
    "mutation_class",
    "atomic_parameter_row_id",
    "row_pattern_id",
    "from_status",
    "to_status",
    "before_value",
    "after_value",
    "receipt",
    "owner_override_receipt",
    "declared_mutation_allowed",
}

OWNER_OVERRIDE_RECEIPT_FIELDS = {
    "receipt_type",
    "receipt_id",
    "receipt_path",
    "receipt_locator",
    "deterministic_created_at_utc",
    "atomic_parameter_row_id",
    "row_pattern_id",
    "mutation_class",
    "from_status",
    "to_status",
    "owner_override_reason",
    "owner_approval_scope",
    "owner_approval_limit",
    "owner_approval_expiry_or_review_required",
    "risk_acknowledgement",
    "waives_internal_policy_gate",
    "external_fact_claims",
    "fabricates_accepted_source_evidence",
    "fabricates_runtime_receipt",
    "fabricates_live_order_receipt",
    "fabricates_quantum_backend_evidence",
    "fabricates_replay_or_paper_result",
    "fabricates_cash_receipt",
    "fabricates_profit_evidence",
    "grants_optimizer_authority",
    "grants_runtime_authority",
    "grants_live_authority",
    "grants_order_authority",
    "grants_quantum_backend_authority",
    "grants_default_value_authority",
    "live_execution_gate_receipt_locator",
    "owner_live_approval_receipt_locator",
}

STATUS_RISK_RANK = {
    "RETIRED_NOT_USEFUL": -2,
    "QUARANTINED_UNPROVEN": -1,
    "INVENTORY_ONLY": 0,
    "RESEARCH_CANDIDATE": 1,
    "SOURCE_EVIDENCE_REQUIRED": 2,
    "RANGE_VALIDATED_STATIC_ONLY": 3,
    "REPLAY_PAPER_CANDIDATE": 4,
    "REPLAY_PAPER_VALIDATED": 5,
    "OPTIMIZER_ELIGIBLE": 6,
    "RUNTIME_ELIGIBLE": 7,
    "LIVE_ELIGIBLE": 8,
}

ACTIVE_AUTHORITY_STATUSES = {
    "OPTIMIZER_ELIGIBLE",
    "RUNTIME_ELIGIBLE",
    "LIVE_ELIGIBLE",
}

PASSIVE_ADDITION_STATUSES = {"INVENTORY_ONLY", "RESEARCH_CANDIDATE"}


@dataclass(frozen=True)
class GuardDecision:
    allowed: bool
    reason: str
    authority_increasing: bool = False
    missing_receipt: bool = False
    mismatched_receipt: bool = False
    owner_override_used: bool = False
    owner_override_blocked: bool = False
    owner_override_external_fact_fabrication_blocked: bool = False
    optimizer_authority: bool = False
    runtime_authority: bool = False
    live_authority: bool = False
    quantum_backend_authority: bool = False


@dataclass(frozen=True)
class MutationEvaluation:
    attempt: dict[str, Any]
    decision: GuardDecision
    invalid_reasons: tuple[str, ...]

    @property
    def invalid(self) -> bool:
        return bool(self.invalid_reasons)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


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


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    missing = sorted(expected_fields - set(value))
    unexpected = sorted(set(value) - expected_fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _present_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _string_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str) and item)
    if _present_string(value):
        return (str(value),)
    return ()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _entry_identifier(entry: dict[str, Any]) -> str:
    row_id = entry.get("atomic_parameter_row_id")
    pattern_id = entry.get("row_pattern_id")
    if _present_string(row_id):
        return str(row_id)
    if _present_string(pattern_id):
        return str(pattern_id)
    return "<missing-row-id-or-pattern-id>"


def _attempt_identifier(attempt: dict[str, Any]) -> str:
    row_id = attempt.get("atomic_parameter_row_id")
    pattern_id = attempt.get("row_pattern_id")
    if _present_string(row_id):
        return str(row_id)
    if _present_string(pattern_id):
        return str(pattern_id)
    return "<missing-row-id-or-pattern-id>"


def _entry_lookup(entries: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for entry in entries:
        for field in ("atomic_parameter_row_id", "row_pattern_id"):
            value = entry.get(field)
            if _present_string(value):
                lookup[str(value)] = entry
    return lookup


def _top_level_receipt_locator_present(receipt: dict[str, Any]) -> bool:
    return _present_string(receipt.get("receipt_path")) or _present_string(
        receipt.get("receipt_locator")
    )


def _supporting_locators(receipt: dict[str, Any]) -> dict[str, Any]:
    return _mapping(receipt.get("supporting_receipt_locators"))


def _locator_for_receipt_type_present(
    receipt: dict[str, Any],
    receipt_type: str,
) -> bool:
    if receipt.get("receipt_type") == receipt_type:
        return _top_level_receipt_locator_present(receipt)
    field = promotion_gate.RECEIPT_TYPE_LOCATOR_FIELD.get(receipt_type)
    if field is None:
        return False
    return _present_string(_supporting_locators(receipt).get(field))


def _quantum_backend_locator_present(receipt: dict[str, Any]) -> bool:
    return _present_string(
        _supporting_locators(receipt).get("quantum_backend_provider_evidence_locator")
    )


def _normal_receipt_decision(
    receipt: Any,
    *,
    required_types: Sequence[str],
    required_supporting_locators: Sequence[str] = (),
    quantum_backend_evidence_required: bool = False,
) -> GuardDecision:
    if not isinstance(receipt, dict):
        return GuardDecision(
            False,
            "required receipt is missing; direct YAML edit alone is blocked",
            missing_receipt=True,
        )
    receipt_type = receipt.get("receipt_type")
    if receipt_type not in required_types:
        return GuardDecision(
            False,
            f"receipt type {receipt_type!r} does not match {tuple(required_types)!r}",
            mismatched_receipt=True,
        )
    if not _top_level_receipt_locator_present(receipt):
        return GuardDecision(
            False,
            "receipt must include receipt_path or receipt_locator",
            mismatched_receipt=True,
        )
    supporting = _supporting_locators(receipt)
    for locator_field in required_supporting_locators:
        if not _present_string(supporting.get(locator_field)):
            return GuardDecision(
                False,
                f"{locator_field} is required",
                mismatched_receipt=True,
            )
    if quantum_backend_evidence_required and not _quantum_backend_locator_present(receipt):
        return GuardDecision(
            False,
            "quantum backend/provider evidence is required",
            mismatched_receipt=True,
            quantum_backend_authority=True,
        )
    return GuardDecision(True, "matching receipt gate satisfied")


def _eligible(value: Any) -> bool:
    return _mapping(value).get("eligible") is True


def _status_authority_increasing(from_status: str, to_status: str) -> bool:
    if from_status in {"QUARANTINED_UNPROVEN", "RETIRED_NOT_USEFUL"}:
        return to_status not in {"QUARANTINED_UNPROVEN", "RETIRED_NOT_USEFUL"}
    return STATUS_RISK_RANK.get(to_status, -99) > STATUS_RISK_RANK.get(from_status, -99)


def _source_authority_rank(value: Any) -> int:
    text = str(value or "").upper()
    if not text:
        return 0
    if "NOT_SOURCE_FACT" in text or "RESEARCH_INPUT" in text:
        return 0
    if "ACCEPTED" in text or "CURRENT_MASTER_PLAN_EXPLICIT_SOURCE" in text:
        return 2
    if "SOURCE_BACKED" in text or "SOURCE_AUTHORITY" in text:
        return 2
    if "BACKEND" in text or "PROVIDER" in text:
        return 2
    return 1


def _default_policy_grants_active_authority(value: Any) -> bool:
    text = str(value or "").upper()
    positive_tokens = (
        "OPTIMIZER_DEFAULT",
        "RUNTIME_DEFAULT",
        "LIVE_DEFAULT",
        "ACTIVE_DEFAULT",
        "DEFAULT_AUTHORITY",
        "GRANT_DEFAULT",
    )
    return any(token in text for token in positive_tokens)


def _promotion_gate_relaxed(before_value: Any, after_value: Any) -> bool:
    before_text = str(before_value or "")
    after_text = str(after_value or "")
    if before_text and not after_text:
        return True
    after_upper = after_text.upper()
    return any(token in after_upper for token in ("RELAXED", "REMOVED", "BYPASS"))


def _quantum_backend_authority(value: Any) -> bool:
    text = str(value or "").upper()
    return "QUANTUM_BACKEND" in text or "BACKEND_EXECUTABLE" in text or (
        "PROVIDER" in text and "QUANTUM" in text
    )


def _all_authority_boundary_false(entry: dict[str, Any]) -> bool:
    boundary = _mapping(entry.get("authority_boundary"))
    return all(
        boundary.get(field) is False
        for field in lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS
    )


def _safe_inventory_or_research_addition(entry: dict[str, Any]) -> bool:
    status = entry.get("lifecycle_status")
    return (
        status in PASSIVE_ADDITION_STATUSES
        and _eligible(entry.get("optimizer_eligibility")) is False
        and _eligible(entry.get("runtime_eligibility")) is False
        and _eligible(entry.get("live_eligibility")) is False
        and not _default_policy_grants_active_authority(
            entry.get("default_value_policy"),
        )
        and not _quantum_backend_authority(entry.get("source_authority_class"))
        and _all_authority_boundary_false(entry)
    )


def _owner_receipt_fabricates_external_facts(receipt: dict[str, Any]) -> bool:
    if _string_list(receipt.get("external_fact_claims")):
        return True
    for field in (
        "fabricates_accepted_source_evidence",
        "fabricates_runtime_receipt",
        "fabricates_live_order_receipt",
        "fabricates_quantum_backend_evidence",
        "fabricates_replay_or_paper_result",
        "fabricates_cash_receipt",
        "fabricates_profit_evidence",
    ):
        if receipt.get(field) is True:
            return True
    return False


def _owner_receipt_silently_grants_external_authority(receipt: dict[str, Any]) -> bool:
    for field in (
        "grants_optimizer_authority",
        "grants_runtime_authority",
        "grants_live_authority",
        "grants_order_authority",
        "grants_quantum_backend_authority",
        "grants_default_value_authority",
    ):
        if receipt.get(field) is True:
            return True
    return False


def _validate_owner_override_receipt_shape(receipt: Any, label: str) -> list[str]:
    if receipt is None:
        return []
    if not isinstance(receipt, dict):
        return [f"{label}.owner_override_receipt must be an object or null"]
    failures = _require_exact_fields(
        receipt,
        OWNER_OVERRIDE_RECEIPT_FIELDS,
        f"{label}.owner_override_receipt",
    )
    if receipt.get("receipt_type") not in OWNER_OVERRIDE_RECEIPT_TYPES:
        failures.append(f"{label}.owner_override_receipt.receipt_type is not allowed")
    for field in (
        "receipt_id",
        "owner_override_reason",
        "owner_approval_scope",
        "owner_approval_limit",
        "owner_approval_expiry_or_review_required",
        "risk_acknowledgement",
    ):
        if not _present_string(receipt.get(field)):
            failures.append(
                f"{label}.owner_override_receipt.{field} must be a non-empty string"
            )
    if not _top_level_receipt_locator_present(receipt):
        failures.append(
            f"{label}.owner_override_receipt must include receipt_path or "
            "receipt_locator"
        )
    if receipt.get("deterministic_created_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append(
            f"{label}.owner_override_receipt.deterministic_created_at_utc must be "
            f"{DETERMINISTIC_GENERATED_AT}"
        )
    if receipt.get("mutation_class") not in MUTATION_CLASSES:
        failures.append(f"{label}.owner_override_receipt.mutation_class is not allowed")
    statuses = set(lifecycle_builder.LIFECYCLE_STATUSES)
    if receipt.get("from_status") not in statuses:
        failures.append(f"{label}.owner_override_receipt.from_status is not allowed")
    if receipt.get("to_status") not in statuses:
        failures.append(f"{label}.owner_override_receipt.to_status is not allowed")
    row_present = _present_string(receipt.get("atomic_parameter_row_id"))
    pattern_present = _present_string(receipt.get("row_pattern_id"))
    if row_present == pattern_present:
        failures.append(
            f"{label}.owner_override_receipt: exactly one target identity is required"
        )
    if not isinstance(receipt.get("external_fact_claims"), list):
        failures.append(
            f"{label}.owner_override_receipt.external_fact_claims must be a list"
        )
    else:
        for index, item in enumerate(receipt.get("external_fact_claims", [])):
            if not _present_string(item):
                failures.append(
                    f"{label}.owner_override_receipt.external_fact_claims[{index}] "
                    "must be a non-empty string"
                )
    for field in OWNER_OVERRIDE_RECEIPT_FIELDS:
        if field.startswith("fabricates_") or field.startswith("grants_"):
            if not isinstance(receipt.get(field), bool):
                failures.append(
                    f"{label}.owner_override_receipt.{field} must be boolean"
                )
    if not isinstance(receipt.get("waives_internal_policy_gate"), bool):
        failures.append(
            f"{label}.owner_override_receipt.waives_internal_policy_gate must be boolean"
        )
    for field in (
        "live_execution_gate_receipt_locator",
        "owner_live_approval_receipt_locator",
        "receipt_path",
        "receipt_locator",
    ):
        value = receipt.get(field)
        if value is not None and not _present_string(value):
            failures.append(
                f"{label}.owner_override_receipt.{field} must be a non-empty "
                "string or null"
            )
    return failures


def _owner_override_decision(
    attempt: dict[str, Any],
    *,
    authority_increasing: bool,
) -> GuardDecision:
    receipt = attempt.get("owner_override_receipt")
    if not isinstance(receipt, dict):
        return GuardDecision(
            False,
            "owner override receipt is missing",
            missing_receipt=True,
            owner_override_blocked=True,
        )
    if _owner_receipt_fabricates_external_facts(receipt):
        return GuardDecision(
            False,
            "owner override may not fabricate external facts or evidence receipts",
            owner_override_used=True,
            owner_override_blocked=True,
            owner_override_external_fact_fabrication_blocked=True,
        )
    if _owner_receipt_silently_grants_external_authority(receipt):
        return GuardDecision(
            False,
            "owner override may not silently grant runtime/live/order/profit authority",
            owner_override_used=True,
            owner_override_blocked=True,
        )
    if authority_increasing and attempt.get("mutation_class") != "OWNER_OVERRIDE_MUTATION":
        return GuardDecision(
            False,
            "owner override cannot replace external evidence receipts",
            owner_override_used=True,
            owner_override_blocked=True,
            missing_receipt=True,
        )
    return GuardDecision(
        True,
        "scoped owner override receipt permits internal-policy-only mutation",
        owner_override_used=True,
    )


def _authority_profile(
    attempt: dict[str, Any],
    entry: dict[str, Any] | None,
) -> GuardDecision:
    mutation_class = str(attempt.get("mutation_class") or "")
    from_status = str(attempt.get("from_status") or "")
    to_status = str(attempt.get("to_status") or "")
    before_value = attempt.get("before_value")
    after_value = attempt.get("after_value")
    authority_increasing = False
    optimizer_authority = False
    runtime_authority = False
    live_authority = False
    quantum_authority = False

    if mutation_class == "STATUS_CHANGE":
        authority_increasing = _status_authority_increasing(from_status, to_status)
        optimizer_authority = to_status == "OPTIMIZER_ELIGIBLE"
        runtime_authority = to_status == "RUNTIME_ELIGIBLE"
        live_authority = to_status == "LIVE_ELIGIBLE"
        if entry and entry.get("classical_or_quantum") == "QUANTUM":
            quantum_authority = to_status in {"RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE"}
    elif mutation_class == "EVIDENCE_REQUIRED_CHANGE":
        authority_increasing = bool(_string_list(before_value)) and not bool(
            _string_list(after_value)
        )
    elif mutation_class == "OPTIMIZER_ELIGIBILITY_CHANGE":
        authority_increasing = not _eligible(before_value) and _eligible(after_value)
        optimizer_authority = authority_increasing
    elif mutation_class == "RUNTIME_ELIGIBILITY_CHANGE":
        authority_increasing = not _eligible(before_value) and _eligible(after_value)
        runtime_authority = authority_increasing
    elif mutation_class == "LIVE_ELIGIBILITY_CHANGE":
        authority_increasing = not _eligible(before_value) and _eligible(after_value)
        live_authority = authority_increasing
    elif mutation_class == "SOURCE_AUTHORITY_CLASS_CHANGE":
        authority_increasing = _source_authority_rank(after_value) > _source_authority_rank(
            before_value
        )
        quantum_authority = _quantum_backend_authority(after_value)
    elif mutation_class == "ALLOWED_RANGE_CHANGE":
        authority_increasing = before_value != after_value and after_value is not None
    elif mutation_class == "DEFAULT_VALUE_POLICY_CHANGE":
        authority_increasing = _default_policy_grants_active_authority(after_value)
        optimizer_authority = authority_increasing
        runtime_authority = "RUNTIME" in str(after_value or "").upper()
        live_authority = "LIVE" in str(after_value or "").upper()
    elif mutation_class == "CLASSICAL_OR_QUANTUM_CHANGE":
        quantum_authority = _quantum_backend_authority(after_value)
        authority_increasing = quantum_authority
    elif mutation_class == "PROMOTION_GATE_CHANGE":
        authority_increasing = _promotion_gate_relaxed(before_value, after_value)
    elif mutation_class == "ROW_ID_ADDITION":
        after_entry = _mapping(after_value)
        authority_increasing = not _safe_inventory_or_research_addition(after_entry)
        optimizer_authority = _eligible(after_entry.get("optimizer_eligibility"))
        runtime_authority = _eligible(after_entry.get("runtime_eligibility"))
        live_authority = _eligible(after_entry.get("live_eligibility"))
        quantum_authority = _quantum_backend_authority(
            after_entry.get("source_authority_class"),
        )
    elif mutation_class == "OWNER_OVERRIDE_MUTATION":
        receipt = _mapping(attempt.get("owner_override_receipt"))
        optimizer_authority = receipt.get("grants_optimizer_authority") is True
        runtime_authority = receipt.get("grants_runtime_authority") is True
        live_authority = receipt.get("grants_live_authority") is True
        quantum_authority = receipt.get("grants_quantum_backend_authority") is True
        authority_increasing = any(
            (optimizer_authority, runtime_authority, live_authority, quantum_authority)
        )

    return GuardDecision(
        False,
        "authority profile only",
        authority_increasing=authority_increasing,
        optimizer_authority=optimizer_authority,
        runtime_authority=runtime_authority,
        live_authority=live_authority,
        quantum_backend_authority=quantum_authority,
    )


def _required_receipt_decision(
    attempt: dict[str, Any],
    entry: dict[str, Any] | None,
    profile: GuardDecision,
) -> GuardDecision:
    mutation_class = attempt.get("mutation_class")
    receipt = attempt.get("receipt")

    if mutation_class == "STATUS_CHANGE":
        promotion = promotion_gate.decide_promotion(
            entry or {"classical_or_quantum": "CLASSICAL"},
            str(attempt.get("from_status") or ""),
            str(attempt.get("to_status") or ""),
            receipt,
        )
        return GuardDecision(
            promotion.allowed,
            promotion.reason,
            authority_increasing=profile.authority_increasing,
            missing_receipt=promotion.missing_receipt,
            mismatched_receipt=(
                promotion.mismatched_receipt_type
                or bool(promotion.missing_evidence_locator_reasons)
            ),
            optimizer_authority=profile.optimizer_authority,
            runtime_authority=profile.runtime_authority,
            live_authority=profile.live_authority,
            quantum_backend_authority=profile.quantum_backend_authority,
        )

    if mutation_class == "OPTIMIZER_ELIGIBILITY_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("OPTIMIZER_ELIGIBILITY_RECEIPT",),
            required_supporting_locators=(
                "source_evidence_acceptance_receipt_locator",
                "range_validation_receipt_locator",
                "replay_result_receipt_locator",
                "paper_result_receipt_locator",
            ),
        )
    elif mutation_class == "RUNTIME_ELIGIBILITY_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("RUNTIME_ELIGIBILITY_RECEIPT",),
        )
    elif mutation_class == "LIVE_ELIGIBILITY_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("LIVE_OWNER_APPROVAL_RECEIPT",),
            required_supporting_locators=("live_canary_eligibility_receipt_locator",),
        )
    elif mutation_class == "SOURCE_AUTHORITY_CLASS_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",),
            quantum_backend_evidence_required=profile.quantum_backend_authority,
        )
    elif mutation_class == "ALLOWED_RANGE_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("RANGE_VALIDATION_RECEIPT",),
        )
    elif mutation_class == "DEFAULT_VALUE_POLICY_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("OPTIMIZER_ELIGIBILITY_RECEIPT",),
            required_supporting_locators=(
                "source_evidence_acceptance_receipt_locator",
                "range_validation_receipt_locator",
                "replay_result_receipt_locator",
                "paper_result_receipt_locator",
            ),
        )
    elif mutation_class == "CLASSICAL_OR_QUANTUM_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("RUNTIME_ELIGIBILITY_RECEIPT",),
            quantum_backend_evidence_required=True,
        )
    elif mutation_class == "PROMOTION_GATE_CHANGE":
        return _owner_override_decision(
            attempt,
            authority_increasing=profile.authority_increasing,
        )
    elif mutation_class == "EVIDENCE_REQUIRED_CHANGE":
        decision = _normal_receipt_decision(
            receipt,
            required_types=("SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",),
        )
    elif mutation_class == "ROW_ID_ADDITION":
        if not profile.authority_increasing:
            return GuardDecision(
                True,
                "row addition defaults to inventory/research-only authority",
            )
        decision = _normal_receipt_decision(
            receipt,
            required_types=("SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",),
        )
    else:
        return GuardDecision(
            False,
            "required receipt mapping is missing for authority-increasing mutation",
            missing_receipt=True,
        )

    return GuardDecision(
        decision.allowed,
        decision.reason,
        authority_increasing=profile.authority_increasing,
        missing_receipt=decision.missing_receipt,
        mismatched_receipt=decision.mismatched_receipt,
        optimizer_authority=profile.optimizer_authority,
        runtime_authority=profile.runtime_authority,
        live_authority=profile.live_authority,
        quantum_backend_authority=profile.quantum_backend_authority,
    )


def decide_mutation(
    entry: dict[str, Any] | None,
    attempt: dict[str, Any],
) -> GuardDecision:
    mutation_class = attempt.get("mutation_class")
    profile = _authority_profile(attempt, entry)

    owner_receipt_present = isinstance(attempt.get("owner_override_receipt"), dict)
    if mutation_class == "OWNER_OVERRIDE_MUTATION":
        return _owner_override_decision(
            attempt,
            authority_increasing=profile.authority_increasing,
        )
    if owner_receipt_present and not profile.authority_increasing:
        return _owner_override_decision(attempt, authority_increasing=False)

    if mutation_class == "ROW_ID_REMOVAL":
        if _present_string(attempt.get("before_value")) or _present_string(
            attempt.get("after_value")
        ):
            return GuardDecision(True, "row removal has quarantine/retirement reason")
        decision = _normal_receipt_decision(
            attempt.get("receipt"),
            required_types=("RETIREMENT_RECEIPT", "QUARANTINE_RECEIPT"),
        )
        return GuardDecision(
            decision.allowed,
            decision.reason,
            missing_receipt=decision.missing_receipt,
            mismatched_receipt=decision.mismatched_receipt,
        )

    if profile.authority_increasing or mutation_class == "STATUS_CHANGE":
        return _required_receipt_decision(attempt, entry, profile)

    return GuardDecision(True, "non-authority-increasing registry mutation is allowed")


def _validate_attempt_identity_and_status(
    *,
    attempt: dict[str, Any],
    entry: dict[str, Any] | None,
    lookup: dict[str, dict[str, Any]],
    label: str,
) -> list[str]:
    failures: list[str] = []
    row_id = attempt.get("atomic_parameter_row_id")
    pattern_id = attempt.get("row_pattern_id")
    row_present = _present_string(row_id)
    pattern_present = _present_string(pattern_id)
    if row_present == pattern_present:
        failures.append(
            f"{label}: exactly one of atomic_parameter_row_id or row_pattern_id "
            "must be set"
        )
    identity = _attempt_identifier(attempt)
    if attempt.get("mutation_class") == "ROW_ID_ADDITION":
        if identity in lookup:
            failures.append(f"{label}: row addition identity already exists {identity}")
    elif entry is None:
        failures.append(f"{label}: unknown lifecycle registry identity {identity}")

    statuses = set(lifecycle_builder.LIFECYCLE_STATUSES)
    from_status = attempt.get("from_status")
    to_status = attempt.get("to_status")
    if from_status not in statuses:
        failures.append(f"{label}: unknown from_status {from_status!r}")
    if to_status not in statuses:
        failures.append(f"{label}: unknown to_status {to_status!r}")
    if (
        entry is not None
        and attempt.get("mutation_class") != "ROW_ID_ADDITION"
        and from_status != entry.get("lifecycle_status")
    ):
        failures.append(
            f"{label}: from_status must match registry status "
            f"{entry.get('lifecycle_status')!r}"
        )
    return failures


def _evaluate_attempts(
    fixture: dict[str, Any],
    entries: Sequence[dict[str, Any]],
) -> tuple[list[MutationEvaluation], list[str]]:
    lookup = _entry_lookup(entries)
    evaluations: list[MutationEvaluation] = []
    failures: list[str] = []
    attempts = fixture.get("attempted_mutations")
    if not isinstance(attempts, list) or not attempts:
        return [], ["fixture.attempted_mutations must be a non-empty list"]

    seen_attempt_ids: set[str] = set()
    for index, attempt in enumerate(attempts):
        label = f"attempted_mutations[{index}]"
        invalid_reasons: list[str] = []
        if not isinstance(attempt, dict):
            failures.append(f"{label} must be an object")
            continue
        invalid_reasons.extend(_require_exact_fields(attempt, ATTEMPT_FIELDS, label))

        attempt_id = attempt.get("attempt_id")
        if not _present_string(attempt_id):
            invalid_reasons.append(f"{label}.attempt_id must be a non-empty string")
        elif str(attempt_id) in seen_attempt_ids:
            invalid_reasons.append(f"{label}.attempt_id is duplicated")
        else:
            seen_attempt_ids.add(str(attempt_id))

        mutation_class = attempt.get("mutation_class")
        if mutation_class not in MUTATION_CLASSES:
            invalid_reasons.append(f"{label}: unknown mutation_class {mutation_class!r}")

        identity = _attempt_identifier(attempt)
        entry = lookup.get(identity)
        invalid_reasons.extend(
            _validate_attempt_identity_and_status(
                attempt=attempt,
                entry=entry,
                lookup=lookup,
                label=label,
            )
        )

        invalid_reasons.extend(
            promotion_gate._validate_receipt_shape(attempt.get("receipt"), label)
        )
        invalid_reasons.extend(
            _validate_owner_override_receipt_shape(
                attempt.get("owner_override_receipt"),
                label,
            )
        )

        owner_receipt = attempt.get("owner_override_receipt")
        if isinstance(owner_receipt, dict):
            for field in ("mutation_class", "from_status", "to_status"):
                if owner_receipt.get(field) != attempt.get(field):
                    invalid_reasons.append(
                        f"{label}.owner_override_receipt.{field} must match attempt"
                    )
            if _entry_identifier(owner_receipt) != identity:
                invalid_reasons.append(
                    f"{label}.owner_override_receipt identity must match attempt"
                )

        decision = decide_mutation(entry, attempt)
        declared_allowed = attempt.get("declared_mutation_allowed")
        if not isinstance(declared_allowed, bool):
            invalid_reasons.append(
                f"{label}.declared_mutation_allowed must be boolean"
            )
        elif declared_allowed is not decision.allowed:
            invalid_reasons.append(
                f"{label}: declared_mutation_allowed={declared_allowed} "
                f"but guard decision is {decision.allowed} for "
                f"{identity}/{mutation_class}"
            )
        if declared_allowed is True and decision.allowed is False:
            invalid_reasons.append(f"{label}: prohibited registry mutation was allowed")

        evaluation = MutationEvaluation(
            attempt=attempt,
            decision=decision,
            invalid_reasons=tuple(invalid_reasons),
        )
        evaluations.append(evaluation)
        failures.extend(invalid_reasons)
    return evaluations, failures


def _authority_boundary_all_false(
    registry_entries: Sequence[dict[str, Any]],
    fixture: dict[str, Any],
    lifecycle_report: dict[str, Any],
) -> bool:
    registry_all_false = all(
        entry.get("authority_boundary", {}).get(field) is False
        for entry in registry_entries
        for field in lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS
    )
    fixture_boundary = _mapping(fixture.get("authority_boundary"))
    fixture_all_false = all(
        fixture_boundary.get(field) is False
        for field in lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS
    )
    return (
        registry_all_false
        and fixture_all_false
        and lifecycle_report.get("authority_boundary_all_false") is True
    )


def build_report(
    *,
    fixture: dict[str, Any],
    registry: dict[str, Any],
    lifecycle_report: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    entries = registry.get("entries", [])
    if not isinstance(entries, list):
        return _empty_report(), ["registry.entries must be a list"]

    evaluations, failures = _evaluate_attempts(fixture, entries)
    invalid_count = sum(1 for evaluation in evaluations if evaluation.invalid)
    allowed_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.decision.allowed and not evaluation.invalid
    ]
    blocked_count = len(evaluations) - len(allowed_evaluations) - invalid_count
    owner_override_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.attempt.get("mutation_class") == "OWNER_OVERRIDE_MUTATION"
        or isinstance(evaluation.attempt.get("owner_override_receipt"), dict)
    ]
    final_ready = (
        lifecycle_report.get("final_ready") is True
        and invalid_count == 0
        and _authority_boundary_all_false(entries, fixture, lifecycle_report)
    )
    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "attempted_mutation_count": len(evaluations),
        "allowed_mutation_count": len(allowed_evaluations),
        "blocked_mutation_count": blocked_count,
        "invalid_mutation_count": invalid_count,
        "authority_increasing_mutation_count": sum(
            1 for evaluation in evaluations if evaluation.decision.authority_increasing
        ),
        "authority_increasing_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.decision.authority_increasing
        ),
        "status_change_count": sum(
            1
            for evaluation in evaluations
            if evaluation.attempt.get("mutation_class") == "STATUS_CHANGE"
        ),
        "status_change_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("mutation_class") == "STATUS_CHANGE"
        ),
        "optimizer_authority_mutation_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.decision.optimizer_authority
        ),
        "runtime_authority_mutation_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.decision.runtime_authority
        ),
        "live_authority_mutation_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.decision.live_authority
        ),
        "quantum_backend_authority_mutation_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.decision.quantum_backend_authority
        ),
        "row_addition_count": sum(
            1
            for evaluation in evaluations
            if evaluation.attempt.get("mutation_class") == "ROW_ID_ADDITION"
        ),
        "row_removal_count": sum(
            1
            for evaluation in evaluations
            if evaluation.attempt.get("mutation_class") == "ROW_ID_REMOVAL"
        ),
        "missing_receipt_count": sum(
            1 for evaluation in evaluations if evaluation.decision.missing_receipt
        ),
        "mismatched_receipt_count": sum(
            1 for evaluation in evaluations if evaluation.decision.mismatched_receipt
        ),
        "owner_override_mutation_count": len(owner_override_evaluations),
        "owner_override_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.decision.owner_override_used
        ),
        "owner_override_blocked_count": sum(
            1
            for evaluation in owner_override_evaluations
            if evaluation.decision.owner_override_blocked
            or not evaluation.decision.allowed
        ),
        "owner_override_external_fact_fabrication_blocked_count": sum(
            1
            for evaluation in evaluations
            if evaluation.decision.owner_override_external_fact_fabrication_blocked
        ),
        "final_ready": final_ready,
        "authority_boundary_all_false": _authority_boundary_all_false(
            entries,
            fixture,
            lifecycle_report,
        ),
    }
    return report, failures


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "attempted_mutation_count": 0,
        "allowed_mutation_count": 0,
        "blocked_mutation_count": 0,
        "invalid_mutation_count": 0,
        "authority_increasing_mutation_count": 0,
        "authority_increasing_allowed_count": 0,
        "status_change_count": 0,
        "status_change_allowed_count": 0,
        "optimizer_authority_mutation_allowed_count": 0,
        "runtime_authority_mutation_allowed_count": 0,
        "live_authority_mutation_allowed_count": 0,
        "quantum_backend_authority_mutation_allowed_count": 0,
        "row_addition_count": 0,
        "row_removal_count": 0,
        "missing_receipt_count": 0,
        "mismatched_receipt_count": 0,
        "owner_override_mutation_count": 0,
        "owner_override_allowed_count": 0,
        "owner_override_blocked_count": 0,
        "owner_override_external_fact_fabrication_blocked_count": 0,
        "final_ready": False,
        "authority_boundary_all_false": False,
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _validate_fixture_shape(
    *,
    fixture: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(fixture, ROOT_FIELDS, "fixture")
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")

    if fixture.get("mutation_classes") != list(MUTATION_CLASSES):
        failures.append("fixture.mutation_classes must contain the exact mutation enum")
    if fixture.get("owner_override_receipt_types") != list(
        OWNER_OVERRIDE_RECEIPT_TYPES
    ):
        failures.append(
            "fixture.owner_override_receipt_types must contain the exact owner "
            "override receipt enum"
        )

    boundary = fixture.get("authority_boundary")
    if not isinstance(boundary, dict):
        failures.append("fixture.authority_boundary must be an object")
    else:
        failures.extend(
            _require_exact_fields(
                boundary,
                set(lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS),
                "fixture.authority_boundary",
            )
        )
        for field in lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS:
            if boundary.get(field) is not False:
                failures.append(f"fixture.authority_boundary.{field} must remain false")

    if fixture.get("validation_hook_ids") != [
        "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_STATIC_VALIDATION"
    ]:
        failures.append(
            "fixture.validation_hook_ids must contain only "
            "ATOMICROWS_LIFECYCLE_REGISTRY_MUTATION_GUARD_STATIC_VALIDATION"
        )

    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]

    mutation_class = defs.get("mutation_class")
    if not isinstance(mutation_class, dict) or mutation_class.get("enum") != list(
        MUTATION_CLASSES
    ):
        failures.append("schema.$defs.mutation_class must contain the exact enum")

    owner_receipt_type = defs.get("owner_override_receipt_type")
    if not isinstance(owner_receipt_type, dict) or owner_receipt_type.get(
        "enum"
    ) != list(OWNER_OVERRIDE_RECEIPT_TYPES):
        failures.append(
            "schema.$defs.owner_override_receipt_type must contain the exact enum"
        )

    lifecycle_status = defs.get("lifecycle_status")
    if not isinstance(lifecycle_status, dict) or lifecycle_status.get("enum") != list(
        lifecycle_builder.LIFECYCLE_STATUSES
    ):
        failures.append("schema.$defs.lifecycle_status must contain the exact enum")

    report_schema = defs.get("mutation_guard_report")
    if isinstance(report_schema, dict):
        required = report_schema.get("required")
        if required != list(_empty_report()):
            failures.append("schema.$defs.mutation_guard_report.required is not exact")
    else:
        failures.append("schema.$defs.mutation_guard_report must be an object")
    return failures


def _validate_lifecycle_report(
    *,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    lifecycle_report_path: pathlib.Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    expected = lifecycle_builder.build_report(
        repo_root=repo_root,
        registry_path=registry_path,
    )
    actual, failures = _load_json(repo_root / lifecycle_report_path)
    if actual is not None and actual != expected:
        failures.append(
            "generated parameter lifecycle report is stale or non-deterministic: "
            f"{lifecycle_report_path.as_posix()}"
        )
    if actual is not None:
        if actual.get("deterministic_output") is not True:
            failures.append("lifecycle report deterministic_output must be true")
        if actual.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
            failures.append("lifecycle report generated_at_utc must be deterministic")
        if actual.get("authority_boundary_all_false") is not True:
            failures.append("lifecycle report authority_boundary_all_false must be true")
    return actual, failures


def _validate_promotion_gate_report(
    *,
    repo_root: pathlib.Path,
    promotion_gate_report_path: pathlib.Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    report, failures = _load_json(repo_root / promotion_gate_report_path)
    if report is not None:
        if report.get("report_type") != promotion_gate.REPORT_TYPE:
            failures.append("promotion receipt gate report_type is invalid")
        if report.get("deterministic_output") is not True:
            failures.append("promotion receipt gate report deterministic_output is invalid")
        if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
            failures.append(
                "promotion receipt gate report generated_at_utc must be deterministic"
            )
        for field in (
            "optimizer_promotion_allowed_count",
            "runtime_promotion_allowed_count",
            "live_promotion_allowed_count",
            "quantum_backend_promotion_allowed_count",
        ):
            if report.get(field) != 0:
                failures.append(f"promotion receipt gate report.{field} must be 0")
    return report, failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs", {})
    report_schema = defs.get("mutation_guard_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.mutation_guard_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    lifecycle_report_path: pathlib.Path,
    promotion_gate_report_path: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    try:
        registry = lifecycle_builder.load_registry(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    schema, schema_failures = _load_json(root / schema_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_failures)
    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if fixture is not None:
        failures.extend(_validate_fixture_shape(fixture=fixture, schema=schema))

    lifecycle_report, lifecycle_failures = _validate_lifecycle_report(
        repo_root=root,
        registry_path=registry_path,
        lifecycle_report_path=lifecycle_report_path,
    )
    failures.extend(lifecycle_failures)

    _, promotion_report_failures = _validate_promotion_gate_report(
        repo_root=root,
        promotion_gate_report_path=promotion_gate_report_path,
    )
    failures.extend(promotion_report_failures)

    report: dict[str, Any] | None = None
    if fixture is not None and lifecycle_report is not None:
        report, report_failures = build_report(
            fixture=fixture,
            registry=registry,
            lifecycle_report=lifecycle_report,
        )
        failures.extend(report_failures)
        failures.extend(_validate_report_schema(report, schema))
        if report.get("deterministic_output") is not True:
            failures.append("report.deterministic_output must be true")
        if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
            failures.append("report.generated_at_utc must be deterministic sentinel")
        if report != json.loads(serialize_report(report)):
            failures.append("report output is nondeterministic")
        if report.get("authority_boundary_all_false") is not True:
            failures.append("report.authority_boundary_all_false must be true")
        for field in (
            "optimizer_authority_mutation_allowed_count",
            "runtime_authority_mutation_allowed_count",
            "live_authority_mutation_allowed_count",
            "quantum_backend_authority_mutation_allowed_count",
        ):
            if report.get(field) != 0:
                failures.append(f"report.{field} must be 0 for this PR")
        if report.get("final_ready") is not False:
            failures.append("report.final_ready must remain false for this PR")

        if output_path is not None and not failures:
            write_report(report, root / output_path)

    if mode == "final" and (report is None or report.get("final_ready") is not True):
        failures.append(
            "final mode incomplete: AtomicRows lifecycle registry mutation coverage "
            "is not complete"
        )
    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(lifecycle_builder.DEFAULT_REGISTRY))
    parser.add_argument("--lifecycle-report", default=str(lifecycle_builder.DEFAULT_OUTPUT))
    parser.add_argument(
        "--promotion-gate-report",
        default=str(promotion_gate.DEFAULT_REPORT),
    )
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        lifecycle_report_path=pathlib.Path(args.lifecycle_report),
        promotion_gate_report_path=pathlib.Path(args.promotion_gate_report),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"attempted={report.get('attempted_mutation_count', 0)} "
            f"allowed={report.get('allowed_mutation_count', 0)} "
            f"blocked={report.get('blocked_mutation_count', 0)} "
            f"invalid={report.get('invalid_mutation_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
