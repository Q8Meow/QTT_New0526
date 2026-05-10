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
    / "atomicrows_lifecycle_consumer_gate.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_lifecycle_consumer_gate_blocked.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleConsumerGate.report.json"
)

REPORT_TYPE = "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_FINAL_INCOMPLETE"

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
    "consumer_classes",
    "attempted_consumer_access",
    "authority_boundary",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_PR54_ATOMICROWS_LIFECYCLE_CONSUMER_GATE_BLOCKED_FIXTURE",
    "fixture_version": "PR54_ATOMICROWS_LIFECYCLE_CONSUMER_GATE_BLOCKED_FIXTURE_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_CONSUMER_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_CONSUMER_AUTHORITY"
    ),
    "surface_kind": "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_STATIC",
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
    "consumer_class",
    "declared_consumer_access_allowed",
}

CONSUMER_CLASSES = (
    "INVENTORY_INDEX",
    "RESEARCH_TRIAGE",
    "SOURCE_EVIDENCE_RETRIEVAL",
    "RANGE_VALIDATION",
    "REPLAY_CANDIDATE_SELECTION",
    "PAPER_CANDIDATE_SELECTION",
    "OPTIMIZER_SEARCH",
    "OPTIMIZER_DEFAULTS",
    "RISK_MODEL_INPUT",
    "SIZING_MODEL_INPUT",
    "QUANTUM_CIRCUIT_CONSTRUCTION",
    "QUANTUM_BACKEND_EXECUTION",
    "RUNTIME_RESOLVER_INPUT",
    "LIVE_ORDER_ROUTING",
    "LIVE_EXECUTION",
)

PASSIVE_RESEARCH_CONSUMERS = {"INVENTORY_INDEX", "RESEARCH_TRIAGE"}
SOURCE_RESEARCH_CONSUMERS = PASSIVE_RESEARCH_CONSUMERS | {
    "SOURCE_EVIDENCE_RETRIEVAL"
}
RANGE_RESEARCH_CONSUMERS = PASSIVE_RESEARCH_CONSUMERS | {"RANGE_VALIDATION"}
REPLAY_PAPER_CONSUMERS = {"REPLAY_CANDIDATE_SELECTION", "PAPER_CANDIDATE_SELECTION"}
OPTIMIZER_CONSUMERS = {"OPTIMIZER_SEARCH", "OPTIMIZER_DEFAULTS"}
RUNTIME_CONSUMERS = {"RUNTIME_RESOLVER_INPUT"}
LIVE_CONSUMERS = {"LIVE_ORDER_ROUTING", "LIVE_EXECUTION"}
QUANTUM_CONSUMERS = {"QUANTUM_CIRCUIT_CONSTRUCTION", "QUANTUM_BACKEND_EXECUTION"}
UNLOCK_NEVER_BY_DEFAULT_CONSUMERS = (
    OPTIMIZER_CONSUMERS | RUNTIME_CONSUMERS | LIVE_CONSUMERS | QUANTUM_CONSUMERS
)


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class AccessEvaluation:
    attempt: dict[str, Any]
    decision: GateDecision
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


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _evidence_items(entry: dict[str, Any]) -> tuple[str, ...]:
    evidence = entry.get("evidence_required")
    if not isinstance(evidence, list):
        return ()
    return tuple(item for item in evidence if isinstance(item, str) and item)


def _has_source_requirement(entry: dict[str, Any]) -> bool:
    return _present_string(entry.get("source_authority_class")) and bool(
        _evidence_items(entry)
    )


def _has_range_requirement(entry: dict[str, Any]) -> bool:
    return entry.get("range_required") is True or entry.get("allowed_range") is not None


def _has_promotion_requirement(entry: dict[str, Any]) -> bool:
    return _present_string(entry.get("promotion_gate"))


def _replay_paper_candidate_prerequisites_present(entry: dict[str, Any]) -> bool:
    return (
        _has_source_requirement(entry)
        and _has_range_requirement(entry)
        and _has_promotion_requirement(entry)
    )


def _replay_paper_validation_receipts_present(entry: dict[str, Any]) -> bool:
    return _present_string(entry.get("replay_validation_receipt_id")) and _present_string(
        entry.get("paper_validation_receipt_id")
    )


def _optimizer_prerequisites_pass(entry: dict[str, Any]) -> bool:
    optimizer = _mapping(entry.get("optimizer_eligibility"))
    if optimizer.get("eligible") is not True:
        return False
    for field in (
        "range_validated",
        "source_evidence_accepted",
        "evidence_validated",
        "promotion_gate_validated",
    ):
        if optimizer.get(field) is not True:
            return False
    if not _present_string(optimizer.get("receipt_id")):
        return False
    if not _has_source_requirement(entry):
        return False
    if not _has_promotion_requirement(entry):
        return False
    if entry.get("range_required") is True and entry.get("allowed_range") is None:
        return False
    return True


def _runtime_prerequisites_pass(entry: dict[str, Any]) -> bool:
    runtime = _mapping(entry.get("runtime_eligibility"))
    return (
        entry.get("lifecycle_status") in {"RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE"}
        and _optimizer_prerequisites_pass(entry)
        and runtime.get("eligible") is True
        and _present_string(runtime.get("runtime_receipt_id"))
    )


def _live_prerequisites_pass(entry: dict[str, Any]) -> bool:
    live = _mapping(entry.get("live_eligibility"))
    return (
        entry.get("lifecycle_status") == "LIVE_ELIGIBLE"
        and _runtime_prerequisites_pass(entry)
        and live.get("eligible") is True
        and _present_string(live.get("live_receipt_id"))
        and _present_string(live.get("owner_approval_receipt_id"))
    )


def _quantum_backend_prerequisites_pass(entry: dict[str, Any]) -> bool:
    if entry.get("classical_or_quantum") != "QUANTUM":
        return False
    if not _runtime_prerequisites_pass(entry):
        return False
    evidence_text = " ".join(_evidence_items(entry)).lower()
    authority_class = str(entry.get("source_authority_class") or "").lower()
    explicit_backend_evidence = (
        ("backend" in evidence_text or "provider" in evidence_text)
        and ("backend" in authority_class or "provider" in authority_class)
    )
    return explicit_backend_evidence


def decide_consumer_access(entry: dict[str, Any], consumer_class: str) -> GateDecision:
    if consumer_class not in CONSUMER_CLASSES:
        return GateDecision(False, "unknown consumer class")

    status = entry.get("lifecycle_status")
    if status not in lifecycle_builder.LIFECYCLE_STATUSES:
        return GateDecision(False, "unknown lifecycle status")

    if consumer_class in QUANTUM_CONSUMERS:
        if _quantum_backend_prerequisites_pass(entry):
            return GateDecision(True, "explicit quantum backend/provider evidence present")
        return GateDecision(
            False,
            "quantum backend consumers require explicit backend/provider evidence",
        )

    if status == "INVENTORY_ONLY":
        return GateDecision(
            consumer_class in PASSIVE_RESEARCH_CONSUMERS,
            "inventory-only lifecycle permits only inventory/research triage",
        )

    if status == "RESEARCH_CANDIDATE":
        return GateDecision(
            consumer_class in SOURCE_RESEARCH_CONSUMERS,
            "research candidate permits inventory/research/source-evidence surfaces",
        )

    if status == "SOURCE_EVIDENCE_REQUIRED":
        if consumer_class in UNLOCK_NEVER_BY_DEFAULT_CONSUMERS or consumer_class in {
            "RISK_MODEL_INPUT",
            "SIZING_MODEL_INPUT",
        }:
            return GateDecision(False, "source evidence is required before active use")
        return GateDecision(
            consumer_class in SOURCE_RESEARCH_CONSUMERS,
            "source evidence required permits only source/research surfaces",
        )

    if status == "RANGE_VALIDATED_STATIC_ONLY":
        if consumer_class in UNLOCK_NEVER_BY_DEFAULT_CONSUMERS:
            return GateDecision(False, "static range validation is not active use")
        return GateDecision(
            consumer_class in RANGE_RESEARCH_CONSUMERS,
            "static range validation permits only research/range surfaces",
        )

    if status == "REPLAY_PAPER_CANDIDATE":
        if consumer_class in PASSIVE_RESEARCH_CONSUMERS:
            return GateDecision(True, "candidate remains visible to passive research")
        if consumer_class in REPLAY_PAPER_CONSUMERS:
            return GateDecision(
                _replay_paper_candidate_prerequisites_present(entry),
                "replay/paper candidate selection requires source/range/promotion requirements",
            )
        return GateDecision(False, "replay/paper candidate is not active-use eligible")

    if status == "REPLAY_PAPER_VALIDATED":
        if consumer_class in PASSIVE_RESEARCH_CONSUMERS | REPLAY_PAPER_CONSUMERS:
            return GateDecision(True, "validated replay/paper record remains reviewable")
        if consumer_class == "OPTIMIZER_SEARCH":
            return GateDecision(
                _replay_paper_validation_receipts_present(entry),
                "optimizer search requires replay/paper validation receipt fields",
            )
        return GateDecision(False, "replay/paper validation does not grant this consumer")

    if status == "OPTIMIZER_ELIGIBLE":
        if consumer_class in PASSIVE_RESEARCH_CONSUMERS:
            return GateDecision(True, "optimizer-eligible row remains inventory visible")
        if consumer_class in OPTIMIZER_CONSUMERS:
            return GateDecision(
                _optimizer_prerequisites_pass(entry),
                "optimizer consumers require source/range/evidence/promotion gates",
            )
        return GateDecision(False, "optimizer eligibility does not grant runtime/live use")

    if status == "RUNTIME_ELIGIBLE":
        if consumer_class in PASSIVE_RESEARCH_CONSUMERS:
            return GateDecision(True, "runtime-eligible row remains inventory visible")
        if consumer_class in OPTIMIZER_CONSUMERS:
            return GateDecision(
                _optimizer_prerequisites_pass(entry),
                "runtime lifecycle preserves optimizer prerequisites",
            )
        if consumer_class in RUNTIME_CONSUMERS:
            return GateDecision(
                _runtime_prerequisites_pass(entry),
                "runtime resolver input requires runtime receipts",
            )
        return GateDecision(False, "runtime eligibility does not grant live use")

    if status == "LIVE_ELIGIBLE":
        if consumer_class in PASSIVE_RESEARCH_CONSUMERS:
            return GateDecision(True, "live-eligible row remains inventory visible")
        if consumer_class in OPTIMIZER_CONSUMERS:
            return GateDecision(
                _optimizer_prerequisites_pass(entry),
                "live lifecycle preserves optimizer prerequisites",
            )
        if consumer_class in RUNTIME_CONSUMERS:
            return GateDecision(
                _runtime_prerequisites_pass(entry),
                "live lifecycle preserves runtime prerequisites",
            )
        if consumer_class in LIVE_CONSUMERS:
            return GateDecision(
                _live_prerequisites_pass(entry),
                "live consumers require live receipts and owner approval",
            )
        return GateDecision(False, "live lifecycle does not grant this consumer")

    if status == "QUARANTINED_UNPROVEN":
        return GateDecision(
            consumer_class in PASSIVE_RESEARCH_CONSUMERS,
            "quarantined rows permit only inventory/quarantine research review",
        )

    if status == "RETIRED_NOT_USEFUL":
        return GateDecision(
            consumer_class == "INVENTORY_INDEX",
            "retired rows permit only inventory/audit visibility",
        )

    return GateDecision(False, "lifecycle status is fail-closed")


def _evaluate_attempts(
    fixture: dict[str, Any],
    entries: Sequence[dict[str, Any]],
) -> tuple[list[AccessEvaluation], list[str]]:
    lookup = _entry_lookup(entries)
    evaluations: list[AccessEvaluation] = []
    failures: list[str] = []
    attempts = fixture.get("attempted_consumer_access")
    if not isinstance(attempts, list) or not attempts:
        return [], ["fixture.attempted_consumer_access must be a non-empty list"]

    seen_attempt_ids: set[str] = set()
    for index, attempt in enumerate(attempts):
        label = f"attempted_consumer_access[{index}]"
        invalid_reasons: list[str] = []
        if not isinstance(attempt, dict):
            failures.append(f"{label} must be an object")
            continue
        field_failures = _require_exact_fields(attempt, ATTEMPT_FIELDS, label)
        invalid_reasons.extend(field_failures)
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
                f"{label}: exactly one of atomic_parameter_row_id or row_pattern_id must be set"
            )

        identity = _attempt_identifier(attempt)
        entry = lookup.get(identity)
        if entry is None:
            invalid_reasons.append(f"{label}: unknown lifecycle registry identity {identity}")
            entry = {"lifecycle_status": "<unknown>"}

        consumer_class = attempt.get("consumer_class")
        if consumer_class not in CONSUMER_CLASSES:
            invalid_reasons.append(f"{label}: unknown consumer class {consumer_class!r}")
            consumer_class = str(consumer_class or "")

        decision = decide_consumer_access(entry, consumer_class)
        declared_allowed = attempt.get("declared_consumer_access_allowed")
        if not isinstance(declared_allowed, bool):
            invalid_reasons.append(
                f"{label}.declared_consumer_access_allowed must be boolean"
            )
        elif declared_allowed is not decision.allowed:
            invalid_reasons.append(
                f"{label}: declared_consumer_access_allowed={declared_allowed} "
                f"but gate decision is {decision.allowed} for {identity}/{consumer_class}"
            )

        if declared_allowed is True and decision.allowed is False:
            invalid_reasons.append(
                f"{label}: prohibited consumer access was declared allowed"
            )

        status = entry.get("lifecycle_status")
        if status not in lifecycle_builder.LIFECYCLE_STATUSES:
            invalid_reasons.append(f"{label}: unknown lifecycle status {status!r}")

        evaluation = AccessEvaluation(
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
        "attempted_consumer_access_count": len(evaluations),
        "allowed_consumer_access_count": len(allowed_evaluations),
        "blocked_consumer_access_count": blocked_count,
        "invalid_consumer_access_count": invalid_count,
        "optimizer_access_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("consumer_class") in OPTIMIZER_CONSUMERS
        ),
        "runtime_access_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("consumer_class") in RUNTIME_CONSUMERS
        ),
        "live_access_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("consumer_class") in LIVE_CONSUMERS
        ),
        "quantum_backend_execution_allowed_count": sum(
            1
            for evaluation in allowed_evaluations
            if evaluation.attempt.get("consumer_class") == "QUANTUM_BACKEND_EXECUTION"
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
        "attempted_consumer_access_count": 0,
        "allowed_consumer_access_count": 0,
        "blocked_consumer_access_count": 0,
        "invalid_consumer_access_count": 0,
        "optimizer_access_allowed_count": 0,
        "runtime_access_allowed_count": 0,
        "live_access_allowed_count": 0,
        "quantum_backend_execution_allowed_count": 0,
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

    if fixture.get("consumer_classes") != list(CONSUMER_CLASSES):
        failures.append("fixture.consumer_classes must contain the exact consumer enum")

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
        "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_STATIC_VALIDATION"
    ]:
        failures.append(
            "fixture.validation_hook_ids must contain only "
            "ATOMICROWS_LIFECYCLE_CONSUMER_GATE_STATIC_VALIDATION"
        )

    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]

    consumer_class = defs.get("consumer_class")
    if not isinstance(consumer_class, dict) or consumer_class.get("enum") != list(
        CONSUMER_CLASSES
    ):
        failures.append("schema.$defs.consumer_class must contain the exact enum")

    lifecycle_status = defs.get("lifecycle_status")
    if not isinstance(lifecycle_status, dict) or lifecycle_status.get("enum") != list(
        lifecycle_builder.LIFECYCLE_STATUSES
    ):
        failures.append("schema.$defs.lifecycle_status must contain the exact enum")

    report_schema = defs.get("lifecycle_gate_report")
    if isinstance(report_schema, dict):
        required = report_schema.get("required")
        if required != list(_empty_report()):
            failures.append("schema.$defs.lifecycle_gate_report.required is not exact")
    else:
        failures.append("schema.$defs.lifecycle_gate_report must be an object")
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
    report_schema = defs.get("lifecycle_gate_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.lifecycle_gate_report must be an object"]
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
            "optimizer_access_allowed_count",
            "runtime_access_allowed_count",
            "live_access_allowed_count",
            "quantum_backend_execution_allowed_count",
        ):
            if report.get(field) != 0:
                failures.append(f"report.{field} must be 0 for this PR")

        if output_path is not None and not failures:
            write_report(report, root / output_path)

    if mode == "final" and (report is None or report.get("final_ready") is not True):
        failures.append(
            "final mode incomplete: AtomicRows lifecycle coverage is not complete"
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
            f"attempted={report.get('attempted_consumer_access_count', 0)} "
            f"allowed={report.get('allowed_consumer_access_count', 0)} "
            f"blocked={report.get('blocked_consumer_access_count', 0)} "
            f"invalid={report.get('invalid_consumer_access_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
