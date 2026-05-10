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
from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_lifecycle_promotion_receipt_gate.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_lifecycle_promotion_receipt_gate_blocked.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecyclePromotionReceiptGate.report.json"
)

REPORT_TYPE = "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_FINAL_INCOMPLETE"
)

RECEIPT_TYPES = (
    "OWNER_RESEARCH_TRIAGE_RECEIPT",
    "SOURCE_EVIDENCE_TARGET_RECEIPT",
    "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",
    "RANGE_VALIDATION_RECEIPT",
    "REPLAY_PAPER_CANDIDATE_RECEIPT",
    "REPLAY_RESULT_RECEIPT",
    "PAPER_RESULT_RECEIPT",
    "DUAL_RESULT_REVIEW_RECEIPT",
    "OPTIMIZER_ELIGIBILITY_RECEIPT",
    "RUNTIME_ELIGIBILITY_RECEIPT",
    "LIVE_OWNER_APPROVAL_RECEIPT",
    "LIVE_CANARY_ELIGIBILITY_RECEIPT",
    "QUARANTINE_RECEIPT",
    "RETIREMENT_RECEIPT",
)

REQUIRED_PROMOTION_TRANSITIONS = (
    "INVENTORY_ONLY->RESEARCH_CANDIDATE",
    "RESEARCH_CANDIDATE->SOURCE_EVIDENCE_REQUIRED",
    "SOURCE_EVIDENCE_REQUIRED->RANGE_VALIDATED_STATIC_ONLY",
    "RANGE_VALIDATED_STATIC_ONLY->REPLAY_PAPER_CANDIDATE",
    "REPLAY_PAPER_CANDIDATE->REPLAY_PAPER_VALIDATED",
    "REPLAY_PAPER_VALIDATED->OPTIMIZER_ELIGIBLE",
    "OPTIMIZER_ELIGIBLE->RUNTIME_ELIGIBLE",
    "RUNTIME_ELIGIBLE->LIVE_ELIGIBLE",
    "ANY_NON_RETIRED_STATUS->QUARANTINED_UNPROVEN",
    "ANY_NON_LIVE_STATUS->RETIRED_NOT_USEFUL",
)

STATIC_TRANSITION_RECEIPTS: dict[tuple[str, str], str] = {
    ("INVENTORY_ONLY", "RESEARCH_CANDIDATE"): "OWNER_RESEARCH_TRIAGE_RECEIPT",
    ("RESEARCH_CANDIDATE", "SOURCE_EVIDENCE_REQUIRED"): (
        "SOURCE_EVIDENCE_TARGET_RECEIPT"
    ),
    ("SOURCE_EVIDENCE_REQUIRED", "RANGE_VALIDATED_STATIC_ONLY"): (
        "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT"
    ),
    ("RANGE_VALIDATED_STATIC_ONLY", "REPLAY_PAPER_CANDIDATE"): (
        "REPLAY_PAPER_CANDIDATE_RECEIPT"
    ),
    ("REPLAY_PAPER_CANDIDATE", "REPLAY_PAPER_VALIDATED"): (
        "DUAL_RESULT_REVIEW_RECEIPT"
    ),
    ("REPLAY_PAPER_VALIDATED", "OPTIMIZER_ELIGIBLE"): (
        "OPTIMIZER_ELIGIBILITY_RECEIPT"
    ),
    ("OPTIMIZER_ELIGIBLE", "RUNTIME_ELIGIBLE"): "RUNTIME_ELIGIBILITY_RECEIPT",
    ("RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE"): "LIVE_OWNER_APPROVAL_RECEIPT",
}

SUPPORTING_LOCATOR_FIELDS = (
    "source_evidence_target_receipt_locator",
    "source_evidence_acceptance_receipt_locator",
    "range_validation_receipt_locator",
    "replay_paper_candidate_receipt_locator",
    "replay_result_receipt_locator",
    "paper_result_receipt_locator",
    "dual_result_review_receipt_locator",
    "optimizer_eligibility_receipt_locator",
    "runtime_eligibility_receipt_locator",
    "live_owner_approval_receipt_locator",
    "live_canary_eligibility_receipt_locator",
    "quantum_backend_provider_evidence_locator",
    "quarantine_reason_receipt_locator",
    "retirement_reason_receipt_locator",
)

RECEIPT_TYPE_LOCATOR_FIELD = {
    "OWNER_RESEARCH_TRIAGE_RECEIPT": None,
    "SOURCE_EVIDENCE_TARGET_RECEIPT": "source_evidence_target_receipt_locator",
    "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT": (
        "source_evidence_acceptance_receipt_locator"
    ),
    "RANGE_VALIDATION_RECEIPT": "range_validation_receipt_locator",
    "REPLAY_PAPER_CANDIDATE_RECEIPT": "replay_paper_candidate_receipt_locator",
    "REPLAY_RESULT_RECEIPT": "replay_result_receipt_locator",
    "PAPER_RESULT_RECEIPT": "paper_result_receipt_locator",
    "DUAL_RESULT_REVIEW_RECEIPT": "dual_result_review_receipt_locator",
    "OPTIMIZER_ELIGIBILITY_RECEIPT": "optimizer_eligibility_receipt_locator",
    "RUNTIME_ELIGIBILITY_RECEIPT": "runtime_eligibility_receipt_locator",
    "LIVE_OWNER_APPROVAL_RECEIPT": "live_owner_approval_receipt_locator",
    "LIVE_CANARY_ELIGIBILITY_RECEIPT": "live_canary_eligibility_receipt_locator",
    "QUARANTINE_RECEIPT": "quarantine_reason_receipt_locator",
    "RETIREMENT_RECEIPT": "retirement_reason_receipt_locator",
}

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
    "receipt_types",
    "required_promotion_transitions",
    "attempted_promotions",
    "authority_boundary",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_PR55_ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_BLOCKED_FIXTURE"
    ),
    "fixture_version": (
        "PR55_ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_BLOCKED_FIXTURE_V1"
    ),
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_PROMOTION_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_PROMOTION_AUTHORITY"
    ),
    "surface_kind": "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "registry_path": str(lifecycle_builder.DEFAULT_REGISTRY).replace("\\", "/"),
    "lifecycle_report_path": str(lifecycle_builder.DEFAULT_OUTPUT).replace("\\", "/"),
}

ATTEMPT_FIELDS = {
    "attempt_id",
    "atomic_parameter_row_id",
    "row_pattern_id",
    "from_status",
    "to_status",
    "receipt",
    "declared_promotion_allowed",
}

RECEIPT_FIELDS = {
    "receipt_type",
    "receipt_id",
    "receipt_path",
    "receipt_locator",
    "approving_authority_class",
    "evidence_scope",
    "deterministic_created_at_utc",
    "source_evidence_required",
    "range_validation_required",
    "replay_paper_required",
    "owner_approval_required",
    "runtime_receipt_required",
    "live_receipt_required",
    "quantum_backend_provider_evidence_required",
    "supporting_receipt_locators",
}

RECEIPT_FLAG_FIELDS = (
    "source_evidence_required",
    "range_validation_required",
    "replay_paper_required",
    "owner_approval_required",
    "runtime_receipt_required",
    "live_receipt_required",
    "quantum_backend_provider_evidence_required",
)


@dataclass(frozen=True)
class PromotionDecision:
    allowed: bool
    reason: str
    missing_receipt: bool = False
    mismatched_receipt_type: bool = False
    missing_evidence_locator_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromotionEvaluation:
    attempt: dict[str, Any]
    decision: PromotionDecision
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
    field = RECEIPT_TYPE_LOCATOR_FIELD.get(receipt_type)
    if field is None:
        return False
    return _present_string(_supporting_locators(receipt).get(field))


def expected_receipt_type(from_status: str, to_status: str) -> str | None:
    if to_status == "QUARANTINED_UNPROVEN" and from_status != "RETIRED_NOT_USEFUL":
        return "QUARANTINE_RECEIPT"
    if to_status == "RETIRED_NOT_USEFUL" and from_status != "LIVE_ELIGIBLE":
        return "RETIREMENT_RECEIPT"
    return STATIC_TRANSITION_RECEIPTS.get((from_status, to_status))


def _required_receipt_types(
    *,
    from_status: str,
    to_status: str,
    entry: dict[str, Any],
) -> tuple[str, ...]:
    required: list[str] = []
    if to_status == "RANGE_VALIDATED_STATIC_ONLY":
        required.extend(
            [
                "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",
                "RANGE_VALIDATION_RECEIPT",
            ]
        )
    elif to_status == "REPLAY_PAPER_CANDIDATE":
        required.extend(
            [
                "RANGE_VALIDATION_RECEIPT",
                "REPLAY_PAPER_CANDIDATE_RECEIPT",
            ]
        )
    elif to_status == "REPLAY_PAPER_VALIDATED":
        required.extend(
            [
                "REPLAY_RESULT_RECEIPT",
                "PAPER_RESULT_RECEIPT",
                "DUAL_RESULT_REVIEW_RECEIPT",
            ]
        )
    elif to_status == "OPTIMIZER_ELIGIBLE":
        required.extend(
            [
                "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",
                "RANGE_VALIDATION_RECEIPT",
                "REPLAY_RESULT_RECEIPT",
                "PAPER_RESULT_RECEIPT",
            ]
        )
    elif to_status == "RUNTIME_ELIGIBLE":
        required.append("RUNTIME_ELIGIBILITY_RECEIPT")
    elif to_status == "LIVE_ELIGIBLE":
        required.extend(
            [
                "LIVE_OWNER_APPROVAL_RECEIPT",
                "LIVE_CANARY_ELIGIBILITY_RECEIPT",
            ]
        )
    elif to_status == "SOURCE_EVIDENCE_REQUIRED":
        required.append("SOURCE_EVIDENCE_TARGET_RECEIPT")

    if (
        entry.get("classical_or_quantum") == "QUANTUM"
        and to_status in {"RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE"}
    ):
        required.append("QUANTUM_BACKEND_PROVIDER_EVIDENCE")
    if to_status == "QUARANTINED_UNPROVEN":
        required.append("QUARANTINE_RECEIPT")
    if to_status == "RETIRED_NOT_USEFUL":
        required.append("RETIREMENT_RECEIPT")
    return tuple(dict.fromkeys(required))


def _required_flags(from_status: str, to_status: str) -> dict[str, bool]:
    del from_status
    return {
        "source_evidence_required": to_status
        in {
            "SOURCE_EVIDENCE_REQUIRED",
            "RANGE_VALIDATED_STATIC_ONLY",
            "OPTIMIZER_ELIGIBLE",
        },
        "range_validation_required": to_status
        in {
            "RANGE_VALIDATED_STATIC_ONLY",
            "REPLAY_PAPER_CANDIDATE",
            "OPTIMIZER_ELIGIBLE",
        },
        "replay_paper_required": to_status
        in {
            "REPLAY_PAPER_CANDIDATE",
            "REPLAY_PAPER_VALIDATED",
            "OPTIMIZER_ELIGIBLE",
        },
        "owner_approval_required": to_status == "LIVE_ELIGIBLE",
        "runtime_receipt_required": to_status == "RUNTIME_ELIGIBLE",
        "live_receipt_required": to_status == "LIVE_ELIGIBLE",
    }


def _flag_locator_present(receipt: dict[str, Any], flag: str) -> bool:
    locators = _supporting_locators(receipt)
    if flag == "source_evidence_required":
        return any(
            [
                _locator_for_receipt_type_present(
                    receipt,
                    "SOURCE_EVIDENCE_TARGET_RECEIPT",
                ),
                _locator_for_receipt_type_present(
                    receipt,
                    "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT",
                ),
            ]
        )
    if flag == "range_validation_required":
        return _locator_for_receipt_type_present(receipt, "RANGE_VALIDATION_RECEIPT")
    if flag == "replay_paper_required":
        return any(
            [
                _locator_for_receipt_type_present(
                    receipt,
                    "REPLAY_PAPER_CANDIDATE_RECEIPT",
                ),
                _locator_for_receipt_type_present(receipt, "REPLAY_RESULT_RECEIPT"),
                _locator_for_receipt_type_present(receipt, "PAPER_RESULT_RECEIPT"),
                _locator_for_receipt_type_present(receipt, "DUAL_RESULT_REVIEW_RECEIPT"),
            ]
        )
    if flag == "owner_approval_required":
        return _locator_for_receipt_type_present(receipt, "LIVE_OWNER_APPROVAL_RECEIPT")
    if flag == "runtime_receipt_required":
        return _locator_for_receipt_type_present(receipt, "RUNTIME_ELIGIBILITY_RECEIPT")
    if flag == "live_receipt_required":
        return _locator_for_receipt_type_present(
            receipt,
            "LIVE_CANARY_ELIGIBILITY_RECEIPT",
        )
    if flag == "quantum_backend_provider_evidence_required":
        return _present_string(locators.get("quantum_backend_provider_evidence_locator"))
    return True


def _missing_evidence_locator_reasons(
    *,
    entry: dict[str, Any],
    from_status: str,
    to_status: str,
    receipt: dict[str, Any],
) -> tuple[str, ...]:
    missing: list[str] = []
    for flag, required in _required_flags(from_status, to_status).items():
        if required and receipt.get(flag) is not True:
            missing.append(f"{flag} must be true for {from_status}->{to_status}")
        if receipt.get(flag) is True and not _flag_locator_present(receipt, flag):
            missing.append(f"{flag} is true without corresponding receipt locator")

    if (
        entry.get("classical_or_quantum") == "QUANTUM"
        and to_status in {"RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE"}
    ):
        if receipt.get("quantum_backend_provider_evidence_required") is not True:
            missing.append(
                "quantum_backend_provider_evidence_required must be true for "
                "quantum runtime promotion"
            )
        elif not _flag_locator_present(
            receipt,
            "quantum_backend_provider_evidence_required",
        ):
            missing.append(
                "quantum backend/provider evidence is required for quantum runtime "
                "promotion"
            )

    for receipt_type in _required_receipt_types(
        from_status=from_status,
        to_status=to_status,
        entry=entry,
    ):
        if receipt_type == "QUANTUM_BACKEND_PROVIDER_EVIDENCE":
            continue
        if not _locator_for_receipt_type_present(receipt, receipt_type):
            missing.append(f"{receipt_type} locator is required")

    return tuple(dict.fromkeys(missing))


def decide_promotion(
    entry: dict[str, Any],
    from_status: str,
    to_status: str,
    receipt: dict[str, Any] | None,
) -> PromotionDecision:
    statuses = set(lifecycle_builder.LIFECYCLE_STATUSES)
    if from_status not in statuses:
        return PromotionDecision(False, "unknown from_status")
    if to_status not in statuses:
        return PromotionDecision(False, "unknown to_status")

    expected_type = expected_receipt_type(from_status, to_status)
    if expected_type is None:
        return PromotionDecision(False, "unsupported lifecycle promotion transition")

    if not isinstance(receipt, dict):
        return PromotionDecision(
            False,
            "promotion receipt is missing; direct YAML edit alone is blocked",
            missing_receipt=True,
        )

    actual_type = receipt.get("receipt_type")
    if actual_type != expected_type:
        return PromotionDecision(
            False,
            f"receipt type {actual_type!r} does not match {expected_type}",
            mismatched_receipt_type=True,
        )

    if not _top_level_receipt_locator_present(receipt):
        return PromotionDecision(
            False,
            "promotion receipt must include receipt_path or receipt_locator",
            missing_evidence_locator_reasons=(
                "promotion receipt must include receipt_path or receipt_locator",
            ),
        )

    missing = _missing_evidence_locator_reasons(
        entry=entry,
        from_status=from_status,
        to_status=to_status,
        receipt=receipt,
    )
    if missing:
        return PromotionDecision(
            False,
            "promotion receipt evidence locator requirements are incomplete",
            missing_evidence_locator_reasons=missing,
        )

    return PromotionDecision(True, "promotion receipt evidence gate satisfied")


def _validate_receipt_shape(receipt: Any, label: str) -> list[str]:
    if receipt is None:
        return []
    if not isinstance(receipt, dict):
        return [f"{label}.receipt must be an object or null"]
    failures = _require_exact_fields(receipt, RECEIPT_FIELDS, f"{label}.receipt")
    if receipt.get("receipt_type") not in RECEIPT_TYPES:
        failures.append(f"{label}.receipt.receipt_type is not allowed")
    for field in (
        "receipt_id",
        "approving_authority_class",
        "evidence_scope",
    ):
        if not _present_string(receipt.get(field)):
            failures.append(f"{label}.receipt.{field} must be a non-empty string")
    if not (
        receipt.get("deterministic_created_at_utc")
        == DETERMINISTIC_GENERATED_AT
    ):
        failures.append(
            f"{label}.receipt.deterministic_created_at_utc must be "
            f"{DETERMINISTIC_GENERATED_AT}"
        )
    if not _top_level_receipt_locator_present(receipt):
        failures.append(f"{label}.receipt must include receipt_path or receipt_locator")
    for field in RECEIPT_FLAG_FIELDS:
        if not isinstance(receipt.get(field), bool):
            failures.append(f"{label}.receipt.{field} must be boolean")
    supporting = receipt.get("supporting_receipt_locators")
    if not isinstance(supporting, dict):
        failures.append(f"{label}.receipt.supporting_receipt_locators must be an object")
    else:
        failures.extend(
            _require_exact_fields(
                supporting,
                set(SUPPORTING_LOCATOR_FIELDS),
                f"{label}.receipt.supporting_receipt_locators",
            )
        )
        for field in SUPPORTING_LOCATOR_FIELDS:
            value = supporting.get(field)
            if value is not None and not _present_string(value):
                failures.append(
                    f"{label}.receipt.supporting_receipt_locators.{field} "
                    "must be a non-empty string or null"
                )
    return failures


def _evaluate_attempts(
    fixture: dict[str, Any],
    entries: Sequence[dict[str, Any]],
) -> tuple[list[PromotionEvaluation], list[str]]:
    lookup = _entry_lookup(entries)
    evaluations: list[PromotionEvaluation] = []
    failures: list[str] = []
    attempts = fixture.get("attempted_promotions")
    if not isinstance(attempts, list) or not attempts:
        return [], ["fixture.attempted_promotions must be a non-empty list"]

    seen_attempt_ids: set[str] = set()
    for index, attempt in enumerate(attempts):
        label = f"attempted_promotions[{index}]"
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

        row_id = attempt.get("atomic_parameter_row_id")
        pattern_id = attempt.get("row_pattern_id")
        row_present = _present_string(row_id)
        pattern_present = _present_string(pattern_id)
        if row_present == pattern_present:
            invalid_reasons.append(
                f"{label}: exactly one of atomic_parameter_row_id or row_pattern_id "
                "must be set"
            )

        identity = _attempt_identifier(attempt)
        entry = lookup.get(identity)
        if entry is None:
            invalid_reasons.append(f"{label}: unknown lifecycle registry identity {identity}")
            entry = {"lifecycle_status": "<unknown>", "classical_or_quantum": "CLASSICAL"}

        from_status = str(attempt.get("from_status") or "")
        to_status = str(attempt.get("to_status") or "")
        if from_status not in lifecycle_builder.LIFECYCLE_STATUSES:
            invalid_reasons.append(f"{label}: unknown from_status {from_status!r}")
        if to_status not in lifecycle_builder.LIFECYCLE_STATUSES:
            invalid_reasons.append(f"{label}: unknown to_status {to_status!r}")

        invalid_reasons.extend(_validate_receipt_shape(attempt.get("receipt"), label))
        decision = decide_promotion(
            entry,
            from_status,
            to_status,
            attempt.get("receipt"),
        )

        declared_allowed = attempt.get("declared_promotion_allowed")
        if not isinstance(declared_allowed, bool):
            invalid_reasons.append(f"{label}.declared_promotion_allowed must be boolean")
        elif declared_allowed is not decision.allowed:
            invalid_reasons.append(
                f"{label}: declared_promotion_allowed={declared_allowed} "
                f"but gate decision is {decision.allowed} for "
                f"{identity}/{from_status}->{to_status}"
            )

        if declared_allowed is True and decision.allowed is False:
            invalid_reasons.append(f"{label}: prohibited lifecycle promotion was allowed")

        evaluation = PromotionEvaluation(
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
    final_ready = (
        lifecycle_report.get("final_ready") is True
        and invalid_count == 0
        and _authority_boundary_all_false(entries, fixture, lifecycle_report)
    )
    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "attempted_promotion_count": len(evaluations),
        "allowed_promotion_count": len(allowed_evaluations),
        "blocked_promotion_count": blocked_count,
        "invalid_promotion_count": invalid_count,
        "optimizer_promotion_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("to_status") == "OPTIMIZER_ELIGIBLE"
        ),
        "runtime_promotion_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("to_status") == "RUNTIME_ELIGIBLE"
        ),
        "live_promotion_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("to_status") == "LIVE_ELIGIBLE"
        ),
        "quantum_backend_promotion_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if _mapping(
                _mapping(evaluation.attempt.get("receipt")).get(
                    "supporting_receipt_locators"
                )
            ).get("quantum_backend_provider_evidence_locator")
        ),
        "missing_receipt_count": sum(
            1 for evaluation in evaluations if evaluation.decision.missing_receipt
        ),
        "mismatched_receipt_type_count": sum(
            1
            for evaluation in evaluations
            if evaluation.decision.mismatched_receipt_type
        ),
        "missing_evidence_locator_count": sum(
            len(evaluation.decision.missing_evidence_locator_reasons)
            for evaluation in evaluations
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
        "attempted_promotion_count": 0,
        "allowed_promotion_count": 0,
        "blocked_promotion_count": 0,
        "invalid_promotion_count": 0,
        "optimizer_promotion_allowed_count": 0,
        "runtime_promotion_allowed_count": 0,
        "live_promotion_allowed_count": 0,
        "quantum_backend_promotion_allowed_count": 0,
        "missing_receipt_count": 0,
        "mismatched_receipt_type_count": 0,
        "missing_evidence_locator_count": 0,
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

    if fixture.get("receipt_types") != list(RECEIPT_TYPES):
        failures.append("fixture.receipt_types must contain the exact receipt enum")
    if fixture.get("required_promotion_transitions") != list(
        REQUIRED_PROMOTION_TRANSITIONS
    ):
        failures.append(
            "fixture.required_promotion_transitions must contain the exact transition list"
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
        "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_STATIC_VALIDATION"
    ]:
        failures.append(
            "fixture.validation_hook_ids must contain only "
            "ATOMICROWS_LIFECYCLE_PROMOTION_RECEIPT_GATE_STATIC_VALIDATION"
        )

    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]

    receipt_type = defs.get("receipt_type")
    if not isinstance(receipt_type, dict) or receipt_type.get("enum") != list(
        RECEIPT_TYPES
    ):
        failures.append("schema.$defs.receipt_type must contain the exact enum")

    lifecycle_status = defs.get("lifecycle_status")
    if not isinstance(lifecycle_status, dict) or lifecycle_status.get("enum") != list(
        lifecycle_builder.LIFECYCLE_STATUSES
    ):
        failures.append("schema.$defs.lifecycle_status must contain the exact enum")

    report_schema = defs.get("promotion_receipt_gate_report")
    if isinstance(report_schema, dict):
        required = report_schema.get("required")
        if required != list(_empty_report()):
            failures.append(
                "schema.$defs.promotion_receipt_gate_report.required is not exact"
            )
    else:
        failures.append("schema.$defs.promotion_receipt_gate_report must be an object")
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


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs", {})
    report_schema = defs.get("promotion_receipt_gate_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.promotion_receipt_gate_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    lifecycle_report_path: pathlib.Path,
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
        if report.get("authority_boundary_all_false") is not True:
            failures.append("report.authority_boundary_all_false must be true")
        for field in (
            "optimizer_promotion_allowed_count",
            "runtime_promotion_allowed_count",
            "live_promotion_allowed_count",
            "quantum_backend_promotion_allowed_count",
        ):
            if report.get(field) != 0:
                failures.append(f"report.{field} must be 0 for this PR")

        if output_path is not None and not failures:
            write_report(report, root / output_path)

    if mode == "final" and (report is None or report.get("final_ready") is not True):
        failures.append(
            "final mode incomplete: AtomicRows lifecycle promotion coverage is not "
            "complete"
        )
    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(lifecycle_builder.DEFAULT_REGISTRY))
    parser.add_argument("--lifecycle-report", default=str(lifecycle_builder.DEFAULT_OUTPUT))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        lifecycle_report_path=pathlib.Path(args.lifecycle_report),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"attempted={report.get('attempted_promotion_count', 0)} "
            f"allowed={report.get('allowed_promotion_count', 0)} "
            f"blocked={report.get('blocked_promotion_count', 0)} "
            f"invalid={report.get('invalid_promotion_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
