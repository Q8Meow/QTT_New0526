#!/usr/bin/env python3
"""Canonical data-only receipts for inherited independent-math row evidence.

This module owns receipt shape, canonical serialization, parsing, and structural
validation.  It deliberately owns no mathematical procedure, production
implementation import, or expected-value selection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
import json
import math
from types import MappingProxyType


SCHEMA_VERSION = "ST12_INHERITED_MATH_ROW_EVIDENCE_V1"
EVIDENCE_PREFIX = SCHEMA_VERSION
EVIDENCE_TIER = "INHERITED_INDEPENDENT_ROW_EXECUTION"
TERMINAL_STATE = "INDEPENDENT_ROW_EVIDENCE_VALIDATED"

INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT = (
    "INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT"
)
PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT = (
    "PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT"
)
INDEPENDENCE_CLASSES = frozenset(
    {
        INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
        PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT,
    }
)

NO_PRODUCTION_SYSTEM_UNDER_TEST = (
    "NOT_APPLICABLE_WITH_TYPED_REASON::NO_PRODUCTION_SYSTEM_UNDER_TEST"
)
EXPECTED_RESULT_SOURCE = "INDEPENDENT_RECONSTRUCTION"

EXPECTED_DOMAIN_MATH_IDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "ACCOUNTING": tuple(f"MATH-{number:02d}" for number in range(26, 37)),
        "EXECUTION": ("MATH-37", "MATH-38"),
        "D": ("MATH-39",),
        "MODEL_RISK": ("MATH-45",),
        "QUANTUM": ("MATH-50", "MATH-51", "MATH-52"),
    }
)

EXPECTED_DOMAIN_OWNER: Mapping[str, str] = MappingProxyType(
    {
        "ACCOUNTING": (
            "tools/independent_validate_qku_computation_control_plane_accounting.py"
        ),
        "EXECUTION": (
            "tools/independent_validate_qku_computation_control_plane_execution.py"
        ),
        "D": "tools/independent_validate_qku_computation_control_plane_d.py",
        "MODEL_RISK": (
            "tools/independent_validate_qku_computation_control_plane_model_risk.py"
        ),
        "QUANTUM": (
            "tools/independent_validate_qku_computation_control_plane_quantum.py"
        ),
    }
)

EXPECTED_COMPARISON_POLICY_BY_MATH_ID: Mapping[str, str] = MappingProxyType(
    {
        "MATH-26": "ABS_TOL_1E-15",
        "MATH-27": "EXACT_DECIMAL",
        "MATH-28": "EXACT_DECIMAL",
        "MATH-29": "EXACT_DECIMAL",
        "MATH-30": "ABS_TOL_1E-15",
        "MATH-31": "ABS_TOL_1E-15",
        "MATH-32": "EXACT_DECIMAL",
        "MATH-33": "EXACT_DECIMAL",
        "MATH-34": "EXACT_DECIMAL_AND_5DP_BOUNDARY",
        "MATH-35": "EXACT_DECIMAL_AND_BANKERS_CENT_BOUNDARY",
        "MATH-36": "EXACT_DECIMAL",
        "MATH-37": "BOOLEAN_INVARIANTS",
        "MATH-38": "EXACT_DECIMAL",
        "MATH-39": "EXACT_DECIMAL",
        "MATH-45": "ABS_TOL_1E-15",
        "MATH-50": "EXACT_DECIMAL_AND_TYPED_BASIS_INVARIANTS",
        "MATH-51": "EXACT_DECIMAL_AND_TYPED_BASIS_INVARIANTS",
        "MATH-52": "LEXICOGRAPHIC_FEASIBILITY_UTILITY_RESOURCE_LATENCY_TIEBREAK",
    }
)

EXPECTED_INDEPENDENCE_CLASS_BY_DOMAIN: Mapping[str, str] = MappingProxyType(
    {
        "ACCOUNTING": INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
        "EXECUTION": INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
        "D": INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
        "MODEL_RISK": (
            PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT
        ),
        "QUANTUM": PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT,
    }
)


class MathRowReceiptValidationError(ValueError):
    """A machine receipt is malformed, inconsistent, or semantically false."""


@dataclass(frozen=True, slots=True)
class IndependentMathRowEvidenceV1:
    math_id: str
    domain_owner: str
    oracle_id: str
    golden_vector_id: str
    comparison_policy: str
    evidence_tier: str
    observed_result: object
    boundary_or_invariant_observation: object
    negative_or_abstention_observation: object
    formula_or_procedure_mutation_observation: object
    domain_guard_observation: object
    precision_or_tolerance_observation: object
    source_unit_or_binding_observation: object
    independence_class: str
    production_system_under_test_invocation_count: int
    production_expected_value_import_count: int
    production_oracle_call_count: int
    external_effect_count: int
    terminal_state: str


@dataclass(frozen=True, slots=True)
class IndependentMathEvidenceEnvelopeV1:
    schema_version: str
    domain: str
    ordered_math_ids: tuple[str, ...]
    row_count: int
    denominators: Mapping[str, int]
    rows: tuple[IndependentMathRowEvidenceV1, ...]


_ROW_FIELDS = frozenset(field.name for field in fields(IndependentMathRowEvidenceV1))
_ENVELOPE_FIELDS = frozenset(
    field.name for field in fields(IndependentMathEvidenceEnvelopeV1)
)
_OBSERVATION_FIELDS = (
    "boundary_or_invariant_observation",
    "negative_or_abstention_observation",
    "formula_or_procedure_mutation_observation",
    "domain_guard_observation",
    "precision_or_tolerance_observation",
    "source_unit_or_binding_observation",
)
_OBSERVATION_PAYLOAD_FIELDS = frozenset({"operation", "outcome", "evidence"})
_RESULT_PAYLOAD_FIELDS = frozenset(
    {
        "independent_observation",
        "independent_expected_result",
        "system_under_test_observation",
        "comparison_passed",
        "expected_result_source",
    }
)
_DENOMINATOR_FIELDS = frozenset(
    {
        "row_count",
        "terminal_row_count",
        "observed_result_count",
        "boundary_or_invariant_observation_count",
        "negative_or_abstention_observation_count",
        "formula_or_procedure_mutation_observation_count",
        "domain_guard_observation_count",
        "precision_or_tolerance_observation_count",
        "source_unit_or_binding_observation_count",
        "independent_reference_row_count",
        "production_system_under_test_row_count",
        "production_system_under_test_invocation_count",
        "production_expected_value_import_count",
        "production_oracle_call_count",
        "external_effect_count",
        "marker_only_row_count",
        "declared_step_only_observation_count",
    }
)


def evidence_observation(
    operation: str,
    outcome: str,
    evidence: Mapping[str, object],
) -> Mapping[str, object]:
    """Build one exact operation/observation payload without formula authority."""

    if not isinstance(operation, str) or not operation.strip():
        raise MathRowReceiptValidationError("observation operation is required")
    if not isinstance(outcome, str) or not outcome.strip():
        raise MathRowReceiptValidationError("observation outcome is required")
    if not isinstance(evidence, Mapping) or not evidence:
        raise MathRowReceiptValidationError("observation evidence must be nonempty")
    return MappingProxyType(
        {
            "operation": operation,
            "outcome": outcome,
            "evidence": MappingProxyType(dict(evidence)),
        }
    )


def observed_result(
    *,
    independent_observation: Mapping[str, object],
    independent_expected_result: Mapping[str, object],
    system_under_test_observation: Mapping[str, object] | str,
    comparison_passed: bool,
) -> Mapping[str, object]:
    """Build one result payload with an explicit independent expected source."""

    return MappingProxyType(
        {
            "independent_observation": MappingProxyType(
                dict(independent_observation)
            ),
            "independent_expected_result": MappingProxyType(
                dict(independent_expected_result)
            ),
            "system_under_test_observation": (
                MappingProxyType(dict(system_under_test_observation))
                if isinstance(system_under_test_observation, Mapping)
                else system_under_test_observation
            ),
            "comparison_passed": comparison_passed,
            "expected_result_source": EXPECTED_RESULT_SOURCE,
        }
    )


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise MathRowReceiptValidationError("nonfinite Decimal is forbidden")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise MathRowReceiptValidationError("naive datetime is forbidden")
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        raise MathRowReceiptValidationError("nonfinite float is forbidden")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise MathRowReceiptValidationError(
        f"unsupported receipt value type: {type(value).__name__}"
    )


def _freeze_receipt_value(value: object) -> object:
    """Recursively freeze parsed JSON so the immutable record is not shallow."""

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                str(key): _freeze_receipt_value(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze_receipt_value(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise MathRowReceiptValidationError("nonfinite parsed number is forbidden")
    return value


def _row_payload(row: IndependentMathRowEvidenceV1) -> dict[str, object]:
    return {
        field.name: _json_ready(getattr(row, field.name))
        for field in fields(IndependentMathRowEvidenceV1)
    }


def envelope_payload(
    envelope: IndependentMathEvidenceEnvelopeV1,
) -> dict[str, object]:
    return {
        "schema_version": envelope.schema_version,
        "domain": envelope.domain,
        "ordered_math_ids": list(envelope.ordered_math_ids),
        "row_count": envelope.row_count,
        "denominators": _json_ready(envelope.denominators),
        "rows": [_row_payload(row) for row in envelope.rows],
    }


def _is_declared_step_only(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    lowered = {str(key).lower() for key in value}
    return bool(
        lowered
        & {
            "algorithm_steps",
            "declared_steps",
            "declared_steps_only",
            "independent_algorithm_steps",
        }
    )


def _is_marker_only(value: object) -> bool:
    if isinstance(value, str):
        return "VALIDATED" in value and "::" not in value
    if isinstance(value, Mapping) and len(value) == 1:
        only_value = next(iter(value.values()))
        return isinstance(only_value, str) and "VALIDATED" in only_value
    return False


def _validate_observation(name: str, value: object) -> None:
    if not isinstance(value, Mapping) or set(value) != _OBSERVATION_PAYLOAD_FIELDS:
        raise MathRowReceiptValidationError(
            f"{name} must contain exactly operation/outcome/evidence"
        )
    if not isinstance(value["operation"], str) or not value["operation"].strip():
        raise MathRowReceiptValidationError(f"{name} operation is absent")
    if not isinstance(value["outcome"], str) or not value["outcome"].strip():
        raise MathRowReceiptValidationError(f"{name} outcome is absent")
    evidence = value["evidence"]
    if not isinstance(evidence, Mapping) or not evidence:
        raise MathRowReceiptValidationError(f"{name} evidence is absent")
    if _is_marker_only(evidence):
        raise MathRowReceiptValidationError(f"{name} is marker-only evidence")
    if _is_declared_step_only(evidence):
        raise MathRowReceiptValidationError(f"{name} is declared-step prose")


def _validate_result(row: IndependentMathRowEvidenceV1) -> None:
    value = row.observed_result
    if not isinstance(value, Mapping) or set(value) != _RESULT_PAYLOAD_FIELDS:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: observed_result field set differs"
        )
    independent = value["independent_observation"]
    expected = value["independent_expected_result"]
    if not isinstance(independent, Mapping) or not independent:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: independent observation is absent"
        )
    if not isinstance(expected, Mapping) or not expected:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: independent expected result is absent"
        )
    if _is_marker_only(independent) or _is_declared_step_only(independent):
        raise MathRowReceiptValidationError(
            f"{row.math_id}: independent observation is not execution evidence"
        )
    if value["expected_result_source"] != EXPECTED_RESULT_SOURCE:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: production result was used as expected truth"
        )
    if value["comparison_passed"] is not True:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: independent comparison did not pass"
        )
    sut = value["system_under_test_observation"]
    if row.independence_class == INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT:
        if sut != NO_PRODUCTION_SYSTEM_UNDER_TEST:
            raise MathRowReceiptValidationError(
                f"{row.math_id}: reference-only row claims a production SUT"
            )
    elif not isinstance(sut, Mapping) or not sut:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: SUT row lacks a separate production observation"
        )


def validate_row(row: IndependentMathRowEvidenceV1, *, domain: str) -> None:
    expected_ids = EXPECTED_DOMAIN_MATH_IDS.get(domain)
    if expected_ids is None or row.math_id not in expected_ids:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: row is outside domain {domain}"
        )
    if row.domain_owner != EXPECTED_DOMAIN_OWNER[domain]:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: wrong domain owner"
        )
    if row.oracle_id != f"ORACLE::{row.math_id}":
        raise MathRowReceiptValidationError(f"{row.math_id}: wrong oracle identity")
    if row.golden_vector_id != f"GOLDEN::{row.math_id}":
        raise MathRowReceiptValidationError(f"{row.math_id}: wrong vector identity")
    if row.comparison_policy != EXPECTED_COMPARISON_POLICY_BY_MATH_ID[row.math_id]:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: false comparison policy"
        )
    if row.evidence_tier != EVIDENCE_TIER:
        raise MathRowReceiptValidationError(f"{row.math_id}: wrong evidence tier")
    if row.terminal_state != TERMINAL_STATE:
        raise MathRowReceiptValidationError(f"{row.math_id}: false terminal state")
    if row.independence_class not in INDEPENDENCE_CLASSES:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: unknown independence class"
        )
    if row.independence_class != EXPECTED_INDEPENDENCE_CLASS_BY_DOMAIN[domain]:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: independence class differs from domain owner"
        )
    for field_name in (
        "production_system_under_test_invocation_count",
        "production_expected_value_import_count",
        "production_oracle_call_count",
        "external_effect_count",
    ):
        count = getattr(row, field_name)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise MathRowReceiptValidationError(
                f"{row.math_id}: {field_name} must be a nonnegative integer"
            )
    if row.production_expected_value_import_count != 0:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: production expected-value import is forbidden"
        )
    if row.production_oracle_call_count != 0:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: production oracle call is forbidden"
        )
    if row.external_effect_count != 0:
        raise MathRowReceiptValidationError(
            f"{row.math_id}: external effects are forbidden"
        )
    if (
        row.independence_class
        == INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT
        and row.production_system_under_test_invocation_count != 0
    ):
        raise MathRowReceiptValidationError(
            f"{row.math_id}: reference-only row invoked production"
        )
    if (
        row.independence_class
        == PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT
        and row.production_system_under_test_invocation_count <= 0
    ):
        raise MathRowReceiptValidationError(
            f"{row.math_id}: SUT row has no observed production invocation"
        )
    _validate_result(row)
    for name in _OBSERVATION_FIELDS:
        _validate_observation(name, getattr(row, name))


def evidence_denominators(
    rows: Sequence[IndependentMathRowEvidenceV1],
) -> Mapping[str, int]:
    row_tuple = tuple(rows)
    return MappingProxyType(
        {
            "row_count": len(row_tuple),
            "terminal_row_count": sum(
                row.terminal_state == TERMINAL_STATE for row in row_tuple
            ),
            "observed_result_count": sum(
                isinstance(row.observed_result, Mapping) for row in row_tuple
            ),
            "boundary_or_invariant_observation_count": sum(
                isinstance(row.boundary_or_invariant_observation, Mapping)
                for row in row_tuple
            ),
            "negative_or_abstention_observation_count": sum(
                isinstance(row.negative_or_abstention_observation, Mapping)
                for row in row_tuple
            ),
            "formula_or_procedure_mutation_observation_count": sum(
                isinstance(row.formula_or_procedure_mutation_observation, Mapping)
                for row in row_tuple
            ),
            "domain_guard_observation_count": sum(
                isinstance(row.domain_guard_observation, Mapping)
                for row in row_tuple
            ),
            "precision_or_tolerance_observation_count": sum(
                isinstance(row.precision_or_tolerance_observation, Mapping)
                for row in row_tuple
            ),
            "source_unit_or_binding_observation_count": sum(
                isinstance(row.source_unit_or_binding_observation, Mapping)
                for row in row_tuple
            ),
            "independent_reference_row_count": sum(
                row.independence_class
                == INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT
                for row in row_tuple
            ),
            "production_system_under_test_row_count": sum(
                row.independence_class
                == PRODUCTION_SYSTEM_UNDER_TEST_WITH_INDEPENDENT_EXPECTED_RESULT
                for row in row_tuple
            ),
            "production_system_under_test_invocation_count": sum(
                row.production_system_under_test_invocation_count
                for row in row_tuple
            ),
            "production_expected_value_import_count": sum(
                row.production_expected_value_import_count for row in row_tuple
            ),
            "production_oracle_call_count": sum(
                row.production_oracle_call_count for row in row_tuple
            ),
            "external_effect_count": sum(row.external_effect_count for row in row_tuple),
            "marker_only_row_count": sum(
                _is_marker_only(row.observed_result) for row in row_tuple
            ),
            "declared_step_only_observation_count": sum(
                _is_declared_step_only(row.observed_result) for row in row_tuple
            ),
        }
    )


def build_envelope(
    domain: str,
    rows: Sequence[IndependentMathRowEvidenceV1],
) -> IndependentMathEvidenceEnvelopeV1:
    row_tuple = tuple(rows)
    expected_ids = EXPECTED_DOMAIN_MATH_IDS.get(domain)
    if expected_ids is None:
        raise MathRowReceiptValidationError(f"unknown receipt domain: {domain}")
    envelope = IndependentMathEvidenceEnvelopeV1(
        schema_version=SCHEMA_VERSION,
        domain=domain,
        ordered_math_ids=expected_ids,
        row_count=len(row_tuple),
        denominators=evidence_denominators(row_tuple),
        rows=row_tuple,
    )
    validate_envelope(envelope)
    return envelope


def validate_envelope(envelope: IndependentMathEvidenceEnvelopeV1) -> None:
    if not isinstance(envelope.schema_version, str):
        raise MathRowReceiptValidationError("receipt schema version must be text")
    if envelope.schema_version != SCHEMA_VERSION:
        raise MathRowReceiptValidationError("receipt schema version differs")
    if not isinstance(envelope.domain, str):
        raise MathRowReceiptValidationError("receipt domain must be text")
    expected_ids = EXPECTED_DOMAIN_MATH_IDS.get(envelope.domain)
    if expected_ids is None:
        raise MathRowReceiptValidationError("receipt domain is unknown")
    if envelope.ordered_math_ids != expected_ids:
        raise MathRowReceiptValidationError("receipt ordered math IDs differ")
    actual_ids = tuple(row.math_id for row in envelope.rows)
    if actual_ids != expected_ids:
        raise MathRowReceiptValidationError("receipt rows are missing, extra, or reordered")
    if len(set(actual_ids)) != len(actual_ids):
        raise MathRowReceiptValidationError("receipt contains a duplicate row")
    if (
        isinstance(envelope.row_count, bool)
        or not isinstance(envelope.row_count, int)
        or envelope.row_count != len(envelope.rows)
        or envelope.row_count != len(expected_ids)
    ):
        raise MathRowReceiptValidationError("receipt row count differs")
    for row in envelope.rows:
        validate_row(row, domain=envelope.domain)
    calculated = evidence_denominators(envelope.rows)
    if set(envelope.denominators) != _DENOMINATOR_FIELDS:
        raise MathRowReceiptValidationError("receipt denominator field set differs")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in envelope.denominators.values()
    ):
        raise MathRowReceiptValidationError(
            "receipt denominators must be nonnegative integers"
        )
    if dict(envelope.denominators) != dict(calculated):
        raise MathRowReceiptValidationError("receipt denominator values differ")
    if (
        calculated["terminal_row_count"] != envelope.row_count
        or calculated["observed_result_count"] != envelope.row_count
        or calculated["boundary_or_invariant_observation_count"]
        != envelope.row_count
        or calculated["negative_or_abstention_observation_count"]
        != envelope.row_count
        or calculated["formula_or_procedure_mutation_observation_count"]
        != envelope.row_count
        or calculated["domain_guard_observation_count"] != envelope.row_count
        or calculated["precision_or_tolerance_observation_count"]
        != envelope.row_count
        or calculated["source_unit_or_binding_observation_count"]
        != envelope.row_count
        or calculated["production_expected_value_import_count"] != 0
        or calculated["production_oracle_call_count"] != 0
        or calculated["external_effect_count"] != 0
        or calculated["marker_only_row_count"] != 0
        or calculated["declared_step_only_observation_count"] != 0
    ):
        raise MathRowReceiptValidationError(
            "receipt completeness or independence denominator failed"
        )


def canonical_envelope_json(envelope: IndependentMathEvidenceEnvelopeV1) -> str:
    validate_envelope(envelope)
    return json.dumps(
        envelope_payload(envelope),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def format_evidence_line(envelope: IndependentMathEvidenceEnvelopeV1) -> str:
    return f"{EVIDENCE_PREFIX} {canonical_envelope_json(envelope)}"


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise MathRowReceiptValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> object:
    raise MathRowReceiptValidationError(f"nonfinite JSON constant: {value}")


def parse_evidence_line(line: str) -> IndependentMathEvidenceEnvelopeV1:
    prefix, separator, payload_text = line.partition(" ")
    if prefix != EVIDENCE_PREFIX or separator != " " or not payload_text:
        raise MathRowReceiptValidationError("receipt prefix or payload is absent")
    try:
        payload = json.loads(
            payload_text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise MathRowReceiptValidationError(f"malformed receipt JSON: {exc}") from exc
    if not isinstance(payload, Mapping) or set(payload) != _ENVELOPE_FIELDS:
        raise MathRowReceiptValidationError("receipt top-level field set differs")
    raw_rows = payload["rows"]
    if not isinstance(raw_rows, list):
        raise MathRowReceiptValidationError("receipt rows must be a list")
    rows: list[IndependentMathRowEvidenceV1] = []
    for raw in raw_rows:
        if not isinstance(raw, Mapping) or set(raw) != _ROW_FIELDS:
            raise MathRowReceiptValidationError("receipt row field set differs")
        rows.append(
            IndependentMathRowEvidenceV1(
                **{
                    str(key): _freeze_receipt_value(value)
                    for key, value in raw.items()
                }
            )
        )
    ordered_ids = payload["ordered_math_ids"]
    if not isinstance(ordered_ids, list) or any(
        not isinstance(value, str) for value in ordered_ids
    ):
        raise MathRowReceiptValidationError("ordered_math_ids must be text rows")
    denominators = payload["denominators"]
    if not isinstance(denominators, Mapping):
        raise MathRowReceiptValidationError("denominators must be a mapping")
    envelope = IndependentMathEvidenceEnvelopeV1(
        schema_version=payload["schema_version"],
        domain=payload["domain"],
        ordered_math_ids=tuple(ordered_ids),
        row_count=payload["row_count"],
        denominators=MappingProxyType(dict(denominators)),
        rows=tuple(rows),
    )
    validate_envelope(envelope)
    return envelope
