#!/usr/bin/env python3
"""Independent ST12-C execution/no-effect validation without production imports."""

from __future__ import annotations

import ast
import base64
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import (
    Context,
    Decimal,
    DivisionByZero,
    FloatOperation,
    InvalidOperation,
    localcontext,
    Overflow,
    ROUND_HALF_EVEN,
)
import json
from pathlib import Path
import sys
import zlib


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.qku_independent_math_row_receipt import (  # noqa: E402
    EVIDENCE_TIER,
    INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
    NO_PRODUCTION_SYSTEM_UNDER_TEST,
    TERMINAL_STATE,
    IndependentMathRowEvidenceV1,
    build_envelope,
    evidence_observation,
    format_evidence_line,
    observed_result,
)

PACKAGE = REPO_ROOT / "src" / "qtt" / "stage1_prediction_markets" / "qku_computation_control_plane"
SUCCESS = "QKU_EXECUTION_INDEPENDENTLY_VALIDATED"
SERVICE_METHODS = (
    "resolve_identity", "resolve_contextual_computability", "resolve_applicable_stack",
    "resolve_required_inputs", "compute_component", "compute_stack", "compare_with_no_trade",
    "evaluate_trade_plan", "get_snapshot_view", "explain_resolution",
    "submit_candidate_proposal", "request_materialization_work_order",
    "compile_replay_paper_cohort", "register_replay_paper_result", "build_evidence_bundle",
)
FORBIDDEN_METHODS = {"submit", "cancel", "amend", "sign", "dispatch", "send"}
NEW_MODULES = (
    "economic_math.py", "receipts.py", "persistence.py", "migrations.py", "outbox.py",
    "transaction.py", "idempotency.py", "rollback.py", "accounting.py", "lifecycle.py",
    "sqlite_reference.py",
    "cohort_compiler.py", "input_lock.py", "evidence.py", "model_risk.py",
    "quantum_benchmark.py", "llm_gateway.py",
)


class _IndependentArtifactRejection(ValueError):
    def __init__(self, failure_family: str, message: str) -> None:
        self.failure_family = failure_family
        super().__init__(message)


_INDEPENDENT_DECIMAL_PRECISION = 34
_INDEPENDENT_DECIMAL_ROUNDING = ROUND_HALF_EVEN


def _independent_decimal_context() -> Context:
    context = Context(
        prec=_INDEPENDENT_DECIMAL_PRECISION,
        rounding=_INDEPENDENT_DECIMAL_ROUNDING,
    )
    context.traps[FloatOperation] = True
    context.traps[InvalidOperation] = True
    context.traps[DivisionByZero] = True
    context.traps[Overflow] = True
    return context


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _IndependentArtifactRejection(
            "MODEL_ARTIFACT_REQUIRED", f"{name} is required"
        )
    return value


def _decimal(value: object, name: str) -> Decimal:
    if isinstance(value, (bool, float)):
        raise _IndependentArtifactRejection(
            "FLOAT_DECIMAL_CONTAMINATION",
            f"{name} must be Decimal, canonical string, or integer",
        )
    try:
        if isinstance(value, Decimal):
            result = value
        elif isinstance(value, (str, int)):
            result = _independent_decimal_context().create_decimal(value)
        else:
            raise TypeError(f"unsupported exact-Decimal input type: {type(value).__name__}")
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise _IndependentArtifactRejection(
            "INVALID_NUMERIC_INPUT", f"{name} is not a valid Decimal"
        ) from exc
    if not result.is_finite():
        raise _IndependentArtifactRejection(
            "NONFINITE_NUMERIC_INPUT", f"{name} must be finite"
        )
    return result


def _utc(value: datetime | str, name: str) -> datetime:
    try:
        result = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise _IndependentArtifactRejection(
            "MODEL_ARTIFACT_REQUIRED", f"{name} must be an ISO datetime"
        ) from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise _IndependentArtifactRejection(
            "MODEL_ARTIFACT_REQUIRED", f"{name} must be timezone-aware"
        )
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class _IndependentFillProbabilityArtifactV1:
    artifact_id: str
    artifact_version: str
    feature_schema_ref: str
    calibration_receipt_ref: str
    scope_ref: str
    horizon_seconds: int
    probability: object
    feature_snapshot_ref: str
    feature_observed_at: datetime | str
    evaluated_at: datetime | str
    artifact_valid_until: datetime | str
    maximum_feature_age: timedelta
    calibration_state: str

    def __post_init__(self) -> None:
        for name in (
            "artifact_id",
            "artifact_version",
            "feature_schema_ref",
            "calibration_receipt_ref",
            "scope_ref",
            "feature_snapshot_ref",
            "calibration_state",
        ):
            _text(getattr(self, name), name)
        if (
            isinstance(self.horizon_seconds, bool)
            or not isinstance(self.horizon_seconds, int)
            or self.horizon_seconds <= 0
        ):
            raise _IndependentArtifactRejection(
                "OUT_OF_DOMAIN", "horizon_seconds must be positive"
            )
        probability = _decimal(self.probability, "probability")
        if probability < 0 or probability > 1:
            raise _IndependentArtifactRejection(
                "OUT_OF_DOMAIN", "probability must be in [0,1]"
            )
        observed = _utc(self.feature_observed_at, "feature_observed_at")
        evaluated = _utc(self.evaluated_at, "evaluated_at")
        valid_until = _utc(self.artifact_valid_until, "artifact_valid_until")
        if (
            not isinstance(self.maximum_feature_age, timedelta)
            or self.maximum_feature_age <= timedelta(0)
        ):
            raise _IndependentArtifactRejection(
                "MODEL_ARTIFACT_REQUIRED",
                "maximum_feature_age must be explicit and positive",
            )
        if (
            self.calibration_state != "VALIDATED"
            or evaluated < observed
            or evaluated - observed > self.maximum_feature_age
            or evaluated >= valid_until
        ):
            raise _IndependentArtifactRejection(
                "MODEL_ARTIFACT_REQUIRED",
                "model calibration, validity, or feature freshness gate failed",
            )
        object.__setattr__(self, "probability", probability)
        object.__setattr__(self, "feature_observed_at", observed)
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "artifact_valid_until", valid_until)


def _independent_fill_probability(
    artifact: _IndependentFillProbabilityArtifactV1 | None,
    *,
    feature_schema_ref: str,
    scope_ref: str,
    horizon_seconds: int,
) -> Decimal:
    if artifact is None:
        raise _IndependentArtifactRejection(
            "MODEL_ARTIFACT_REQUIRED", "no default fill-probability model exists"
        )
    if (
        artifact.feature_schema_ref != feature_schema_ref
        or artifact.scope_ref != scope_ref
        or artifact.horizon_seconds != horizon_seconds
    ):
        raise _IndependentArtifactRejection(
            "MODEL_ARTIFACT_REQUIRED",
            "model artifact is outside declared schema, scope, or horizon",
        )
    assert isinstance(artifact.probability, Decimal)
    return artifact.probability


@dataclass(frozen=True, slots=True)
class _IndependentFillDistributionArtifactV1:
    artifact_id: str
    artifact_version: str
    source_binding_ref: str
    scope_ref: str
    horizon_seconds: int
    evaluated_at: datetime | str
    artifact_valid_until: datetime | str
    order_quantity: object
    normalization_tolerance: object
    fill_quantity_distribution: tuple[tuple[object, object], ...]

    def __post_init__(self) -> None:
        for name in (
            "artifact_id",
            "artifact_version",
            "source_binding_ref",
            "scope_ref",
        ):
            _text(getattr(self, name), name)
        if (
            isinstance(self.horizon_seconds, bool)
            or not isinstance(self.horizon_seconds, int)
            or self.horizon_seconds <= 0
        ):
            raise _IndependentArtifactRejection(
                "MODEL_ARTIFACT_REQUIRED",
                "distribution horizon must be explicit and positive",
            )
        evaluated = _utc(self.evaluated_at, "evaluated_at")
        valid_until = _utc(self.artifact_valid_until, "artifact_valid_until")
        if (
            evaluated >= valid_until
            or not isinstance(self.fill_quantity_distribution, tuple)
            or not self.fill_quantity_distribution
        ):
            raise _IndependentArtifactRejection(
                "MODEL_ARTIFACT_REQUIRED", "distribution artifact is stale or empty"
            )
        maximum = _decimal(self.order_quantity, "order_quantity")
        tolerance = _decimal(self.normalization_tolerance, "normalization_tolerance")
        if maximum < 0 or tolerance < 0:
            raise _IndependentArtifactRejection(
                "OUT_OF_DOMAIN", "distribution bounds must be nonnegative"
            )
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "artifact_valid_until", valid_until)
        object.__setattr__(self, "order_quantity", maximum)
        object.__setattr__(self, "normalization_tolerance", tolerance)


@dataclass(frozen=True, slots=True)
class _IndependentExpectedFillComputationV1:
    probability_sum: Decimal
    weighted_sum: Decimal
    normalized_expected_fill: Decimal


def _independent_expected_fill_computation(
    artifact: _IndependentFillDistributionArtifactV1 | None,
) -> _IndependentExpectedFillComputationV1:
    if artifact is None or not isinstance(
        artifact, _IndependentFillDistributionArtifactV1
    ):
        raise _IndependentArtifactRejection(
            "MODEL_ARTIFACT_REQUIRED", "a versioned fill distribution is required"
        )
    maximum = artifact.order_quantity
    tolerance = artifact.normalization_tolerance
    assert isinstance(maximum, Decimal) and isinstance(tolerance, Decimal)
    if tolerance >= 1:
        raise _IndependentArtifactRejection(
            "OUT_OF_DOMAIN", "normalization tolerance must be less than one"
        )
    probability_sum = Decimal(0)
    weighted_sum = Decimal(0)
    with localcontext(_independent_decimal_context()) as context:
        for index, item in enumerate(artifact.fill_quantity_distribution):
            if not isinstance(item, tuple) or len(item) != 2:
                raise _IndependentArtifactRejection(
                    "INVALID_CONTRACT",
                    "distribution rows must be (quantity, probability)",
                )
            quantity = _decimal(item[0], f"distribution[{index}].quantity")
            probability = _decimal(item[1], f"distribution[{index}].probability")
            if quantity < 0 or probability < 0 or probability > 1:
                raise _IndependentArtifactRejection(
                    "OUT_OF_DOMAIN", "distribution quantity/probability is invalid"
                )
            if quantity > maximum:
                raise _IndependentArtifactRejection(
                    "OUT_OF_DOMAIN", "fill support exceeds order quantity"
                )
            probability_sum = context.add(probability_sum, probability)
            weighted_sum = context.add(
                weighted_sum, context.multiply(quantity, probability)
            )
    if probability_sum <= 0 or abs(probability_sum - Decimal(1)) > tolerance:
        raise _IndependentArtifactRejection(
            "OUT_OF_DOMAIN",
            "fill probabilities exceed the explicitly declared normalization tolerance",
        )
    with localcontext(_independent_decimal_context()) as context:
        normalized_expected_fill = context.divide(weighted_sum, probability_sum)
    if normalized_expected_fill < 0 or normalized_expected_fill > maximum:
        raise _IndependentArtifactRejection(
            "OUT_OF_DOMAIN", "expected fill is outside order support"
        )
    return _IndependentExpectedFillComputationV1(
        probability_sum=probability_sum,
        weighted_sum=weighted_sum,
        normalized_expected_fill=normalized_expected_fill,
    )


def _independent_expected_fill(
    artifact: _IndependentFillDistributionArtifactV1 | None,
) -> Decimal:
    return _independent_expected_fill_computation(artifact).normalized_expected_fill


def _assigned_literal(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal {name}")


def _archive_rows(path: Path, name: str) -> tuple[dict[str, object], ...]:
    payload = _assigned_literal(path, name)
    if not isinstance(payload, str):
        raise ValueError(f"{name} is not literal text")
    text = zlib.decompress(base64.b85decode(payload.encode("ascii"))).decode(
        "utf-8-sig"
    )
    rows = tuple(json.loads(line) for line in text.splitlines() if line.strip())
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{name} contains a nonobject")
    return rows


def _capture_rejection(callable_, family: str, message: str) -> dict[str, object]:
    try:
        callable_()
    except _IndependentArtifactRejection as exc:
        if exc.failure_family != family or message not in str(exc):
            raise ValueError(
                f"wrong independent rejection: {exc.failure_family}::{exc}"
            ) from exc
        return {
            "failure_family": exc.failure_family,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    raise ValueError(f"expected rejection {family}::{message} was accepted")


def _independent_decimal_boundary_evidence() -> dict[str, object]:
    high_precision_text = "0.12345678901234567890123456789012345"
    expected_string_conversion = Decimal(
        "0.1234567890123456789012345678901234"
    )
    parsed_string = _decimal(high_precision_text, "high_precision_string")
    parsed_integer = _decimal(100, "integer_input")
    decimal_input = Decimal(high_precision_text)
    preserved_decimal = _decimal(decimal_input, "decimal_input")

    class _NumericLookingObject:
        def __str__(self) -> str:
            return "0.5"

    if (
        parsed_string != expected_string_conversion
        or parsed_integer != Decimal(100)
        or preserved_decimal is not decimal_input
        or preserved_decimal != decimal_input
    ):
        raise ValueError("independent exact-Decimal accepted-input contract differs")

    rejected_inputs = {
        "bool": _capture_rejection(
            lambda: _decimal(True, "bool_input"),
            "FLOAT_DECIMAL_CONTAMINATION",
            "must be Decimal, canonical string, or integer",
        ),
        "float": _capture_rejection(
            lambda: _decimal(0.5, "float_input"),
            "FLOAT_DECIMAL_CONTAMINATION",
            "must be Decimal, canonical string, or integer",
        ),
        "invalid_text": _capture_rejection(
            lambda: _decimal("not-a-number", "invalid_text"),
            "INVALID_NUMERIC_INPUT",
            "is not a valid Decimal",
        ),
        "nonfinite_text": _capture_rejection(
            lambda: _decimal("NaN", "nonfinite_text"),
            "NONFINITE_NUMERIC_INPUT",
            "must be finite",
        ),
        "unsupported_object": _capture_rejection(
            lambda: _decimal(_NumericLookingObject(), "unsupported_object"),
            "INVALID_NUMERIC_INPUT",
            "is not a valid Decimal",
        ),
    }
    return {
        "accepted_numeric_input_classes": {
            "canonical_string": {
                "input": high_precision_text,
                "observed": parsed_string,
                "fresh_context_create_decimal": True,
            },
            "integer": {
                "input": 100,
                "observed": parsed_integer,
                "fresh_context_create_decimal": True,
            },
            "Decimal": {
                "input": decimal_input,
                "observed": preserved_decimal,
                "input_object_preserved": preserved_decimal is decimal_input,
            },
        },
        "rejected_numeric_input_classes": rejected_inputs,
        "precision": _INDEPENDENT_DECIMAL_PRECISION,
        "rounding": "ROUND_HALF_EVEN",
        "string_and_integer_input_conversion": "FRESH_CONTEXT_CREATE_DECIMAL",
        "decimal_object_input_conversion": "PRESERVE_EXACT_OBJECT",
        "invalid_input_rejection": rejected_inputs["invalid_text"],
        "nonfinite_input_rejection": rejected_inputs["nonfinite_text"],
        "float_contamination_rejection": rejected_inputs["float"],
    }


def _fill_probability_fixture(
    horizon: int,
    probability: object,
    **overrides: object,
) -> _IndependentFillProbabilityArtifactV1:
    observed = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, object] = {
        "artifact_id": f"GOLDEN::MODEL::{horizon}",
        "artifact_version": "1",
        "feature_schema_ref": "GOLDEN::FEATURES",
        "calibration_receipt_ref": "GOLDEN::CALIBRATION",
        "scope_ref": "GOLDEN::SCOPE",
        "horizon_seconds": horizon,
        "probability": probability,
        "feature_snapshot_ref": f"GOLDEN::FEATURE-SNAPSHOT::{horizon}",
        "feature_observed_at": observed,
        "evaluated_at": observed + timedelta(seconds=1),
        "artifact_valid_until": observed + timedelta(minutes=1),
        "maximum_feature_age": timedelta(seconds=5),
        "calibration_state": "VALIDATED",
    }
    values.update(overrides)
    return _IndependentFillProbabilityArtifactV1(**values)  # type: ignore[arg-type]


def _distribution_fixture(
    distribution: tuple[tuple[object, object], ...],
    **overrides: object,
) -> _IndependentFillDistributionArtifactV1:
    evaluated = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, object] = {
        "artifact_id": "GOLDEN::DISTRIBUTION",
        "artifact_version": "1",
        "source_binding_ref": "GOLDEN::SOURCE",
        "scope_ref": "GOLDEN::SCOPE",
        "horizon_seconds": 30,
        "evaluated_at": evaluated,
        "artifact_valid_until": evaluated + timedelta(minutes=1),
        "order_quantity": "100",
        "normalization_tolerance": "0",
        "fill_quantity_distribution": distribution,
    }
    values.update(overrides)
    return _IndependentFillDistributionArtifactV1(**values)  # type: ignore[arg-type]


def _validate_execution_math_owner_ast(
    economic_tree: ast.Module,
    context_tree: ast.Module,
    independent_tree: ast.Module,
) -> None:
    def function(tree: ast.Module, name: str) -> ast.FunctionDef:
        return next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )

    def assigned_expression(tree: ast.Module, name: str) -> ast.expr:
        return next(
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
        )

    def context_call_has_contract(
        function_node: ast.FunctionDef,
        precision: str | int,
        rounding: str,
    ) -> bool:
        for call in (
            node for node in ast.walk(function_node) if isinstance(node, ast.Call)
        ):
            if not isinstance(call.func, ast.Name) or call.func.id != "Context":
                continue
            keywords = {keyword.arg: keyword.value for keyword in call.keywords}
            precision_node = keywords.get("prec")
            rounding_node = keywords.get("rounding")
            precision_matches = (
                isinstance(precision, int)
                and isinstance(precision_node, ast.Constant)
                and precision_node.value == precision
            ) or (
                isinstance(precision, str)
                and isinstance(precision_node, ast.Name)
                and precision_node.id == precision
            )
            if (
                precision_matches
                and isinstance(rounding_node, ast.Name)
                and rounding_node.id == rounding
            ):
                return True
        return False

    def enabled_decimal_traps(function_node: ast.FunctionDef) -> set[str]:
        traps: set[str] = set()
        for node in ast.walk(function_node):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Subscript)
                and isinstance(node.targets[0].value, ast.Attribute)
                and node.targets[0].value.attr == "traps"
                and isinstance(node.targets[0].slice, ast.Name)
                and isinstance(node.value, ast.Constant)
                and node.value.value is True
            ):
                traps.add(node.targets[0].slice.id)
        return traps

    required_traps = {
        "FloatOperation",
        "InvalidOperation",
        "DivisionByZero",
        "Overflow",
    }
    production_context = function(context_tree, "decimal_context_v1")
    precision_assignment = assigned_expression(context_tree, "DECIMAL_PRECISION")
    rounding_assignment = assigned_expression(context_tree, "DECIMAL_ROUNDING")
    if (
        not isinstance(precision_assignment, ast.Constant)
        or precision_assignment.value != 34
        or not isinstance(rounding_assignment, ast.Name)
        or rounding_assignment.id != "ROUND_HALF_EVEN"
        or not context_call_has_contract(
            production_context, "DECIMAL_PRECISION", "DECIMAL_ROUNDING"
        )
        or enabled_decimal_traps(production_context) != required_traps
    ):
        raise ValueError("production exact-Decimal context contract differs")

    production_exact_decimal = function(context_tree, "exact_decimal")
    production_type_checks = {
        node.args[1].id
        for node in ast.walk(production_exact_decimal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
    }
    production_reason_families = {
        node.attr
        for node in ast.walk(production_exact_decimal)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "ReasonCode"
    }
    production_create_decimal_calls = tuple(
        node
        for node in ast.walk(production_exact_decimal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create_decimal"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "value"
    )
    production_decimal_preservation = any(
        isinstance(node, ast.IfExp)
        and isinstance(node.body, ast.Name)
        and node.body.id == "value"
        and any(
            isinstance(child, ast.Name) and child.id == "Decimal"
            for child in ast.walk(node.test)
        )
        for node in ast.walk(production_exact_decimal)
    )
    production_exception_types = {
        child.id
        for handler in ast.walk(production_exact_decimal)
        if isinstance(handler, ast.ExceptHandler) and handler.type is not None
        for child in ast.walk(handler.type)
        if isinstance(child, ast.Name)
    }
    if (
        not {"bool", "float", "Decimal"} <= production_type_checks
        or len(production_create_decimal_calls) != 1
        or not production_decimal_preservation
        or not {"InvalidOperation", "ValueError", "TypeError"}
        <= production_exception_types
        or not {
            "FLOAT_DECIMAL_CONTAMINATION",
            "INVALID_NUMERIC_INPUT",
            "NONFINITE_NUMERIC_INPUT",
        }
        <= production_reason_families
        or not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "is_finite"
            for node in ast.walk(production_exact_decimal)
        )
    ):
        raise ValueError("production exact_decimal input-boundary contract differs")

    production_decimal_adapter = function(economic_tree, "_decimal")
    adapter_calls = tuple(
        node
        for node in ast.walk(production_decimal_adapter)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "exact_decimal"
    )
    if len(adapter_calls) != 1:
        raise ValueError("economic_math._decimal no longer delegates to exact_decimal")

    independent_context = function(independent_tree, "_independent_decimal_context")
    independent_decimal = function(independent_tree, "_decimal")
    independent_precision = assigned_expression(
        independent_tree, "_INDEPENDENT_DECIMAL_PRECISION"
    )
    independent_rounding = assigned_expression(
        independent_tree, "_INDEPENDENT_DECIMAL_ROUNDING"
    )
    if (
        not isinstance(independent_precision, ast.Constant)
        or independent_precision.value != 34
        or not isinstance(independent_rounding, ast.Name)
        or independent_rounding.id != "ROUND_HALF_EVEN"
        or not context_call_has_contract(
            independent_context,
            "_INDEPENDENT_DECIMAL_PRECISION",
            "_INDEPENDENT_DECIMAL_ROUNDING",
        )
        or enabled_decimal_traps(independent_context) != required_traps
    ):
        raise ValueError("independent exact-Decimal context contract differs")

    independent_type_checks = {
        child.id
        for node in ast.walk(independent_decimal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        and len(node.args) >= 2
        for child in ast.walk(node.args[1])
        if isinstance(child, ast.Name)
    }
    independent_failure_families = {
        node.value
        for node in ast.walk(independent_decimal)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value
        in {
            "FLOAT_DECIMAL_CONTAMINATION",
            "INVALID_NUMERIC_INPUT",
            "NONFINITE_NUMERIC_INPUT",
        }
    }
    independent_create_decimal_calls = tuple(
        node
        for node in ast.walk(independent_decimal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create_decimal"
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Name)
        and node.func.value.func.id == "_independent_decimal_context"
    )
    decimal_str_calls = tuple(
        node
        for node in ast.walk(independent_decimal)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Decimal"
        and node.args
        and isinstance(node.args[0], ast.Call)
        and isinstance(node.args[0].func, ast.Name)
        and node.args[0].func.id == "str"
    )
    decimal_object_preservation = any(
        isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Name)
        and node.value.id == "value"
        and any(
            isinstance(target, ast.Name) and target.id == "result"
            for target in node.targets
        )
        for node in ast.walk(independent_decimal)
    )
    if (
        not {"bool", "float", "Decimal", "str", "int"}
        <= independent_type_checks
        or len(independent_create_decimal_calls) != 1
        or decimal_str_calls
        or not decimal_object_preservation
        or independent_failure_families
        != {
            "FLOAT_DECIMAL_CONTAMINATION",
            "INVALID_NUMERIC_INPUT",
            "NONFINITE_NUMERIC_INPUT",
        }
    ):
        raise ValueError("independent exact-Decimal input-boundary contract differs")

    tree = economic_tree
    artifact = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "FillProbabilityModelArtifactV1"
    )
    fields = tuple(
        node.target.id
        for node in artifact.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )
    if fields != (
        "artifact_id",
        "artifact_version",
        "feature_schema_ref",
        "calibration_receipt_ref",
        "scope_ref",
        "horizon_seconds",
        "probability",
        "feature_snapshot_ref",
        "feature_observed_at",
        "evaluated_at",
        "artifact_valid_until",
        "maximum_feature_age",
        "calibration_state",
    ):
        raise ValueError("MATH-37 production artifact field contract differs")
    artifact_post_init = next(
        node
        for node in artifact.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )
    if not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_probability"
        and node.args
        and isinstance(node.args[0], ast.Attribute)
        and isinstance(node.args[0].value, ast.Name)
        and node.args[0].value.id == "self"
        and node.args[0].attr == "probability"
        for node in ast.walk(artifact_post_init)
    ):
        raise ValueError("MATH-37 probability no longer passes through _probability")
    fill_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "fill_probability_v1"
    )
    source = ast.unparse(fill_function)
    for token in (
        "artifact is None",
        "feature_schema_ref",
        "scope_ref",
        "horizon_seconds",
        "artifact.probability",
    ):
        if token not in source:
            raise ValueError(f"MATH-37 production owner guard differs: {token}")

    distribution_artifact = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "FillQuantityDistributionArtifactV1"
    )
    distribution_fields = tuple(
        node.target.id
        for node in distribution_artifact.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )
    if distribution_fields != (
        "artifact_id",
        "artifact_version",
        "source_binding_ref",
        "scope_ref",
        "horizon_seconds",
        "evaluated_at",
        "artifact_valid_until",
        "order_quantity",
        "normalization_tolerance",
        "fill_quantity_distribution",
    ):
        raise ValueError("MATH-38 production artifact field contract differs")
    distribution_artifact_source = ast.unparse(distribution_artifact)
    for token in (
        "distribution horizon must be explicit and positive",
        "distribution artifact is stale or empty",
        "_nonnegative(self.order_quantity, 'order_quantity')",
        "_nonnegative(self.normalization_tolerance, 'normalization_tolerance')",
    ):
        if token not in distribution_artifact_source:
            raise ValueError(
                f"MATH-38 production artifact guard differs: {token}"
            )
    expected_fill_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "expected_partial_fill_quantity_v1"
    )
    expected_fill_source = ast.unparse(expected_fill_function)
    for token in (
        "artifact is None",
        "FillQuantityDistributionArtifactV1",
        "artifact.normalization_tolerance",
        "localcontext(decimal_context_v1())",
        "probability_sum",
        "_nonnegative(item[0]",
        "_probability(item[1]",
        "context.add(probability_sum, probability)",
        "context.multiply(quantity, probability)",
        "abs(probability_sum - Decimal(1)) > tolerance",
        "context.divide(expected, probability_sum)",
        "quantity > maximum",
        "distribution rows must be (quantity, probability)",
        "fill probabilities exceed the explicitly declared normalization tolerance",
        "expected fill is outside order support",
    ):
        if token not in expected_fill_source:
            raise ValueError(f"MATH-38 production owner guard differs: {token}")
    expected_fill_calls = tuple(
        node
        for node in ast.walk(expected_fill_function)
        if isinstance(node, ast.Call)
    )
    if not any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "divide"
        and len(call.args) == 2
        and isinstance(call.args[1], ast.Name)
        and call.args[1].id == "probability_sum"
        for call in expected_fill_calls
    ):
        raise ValueError("MATH-38 production normalization division differs")
    typed_rejections = {
        call.func.id
        for call in expected_fill_calls
        if isinstance(call.func, ast.Name)
        and call.func.id in {"ContractValidationError", "NumericDomainError"}
    }
    if typed_rejections != {"ContractValidationError", "NumericDomainError"}:
        raise ValueError("MATH-38 production typed rejection contract differs")

    independent_probability_artifact = next(
        node
        for node in independent_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "_IndependentFillProbabilityArtifactV1"
    )
    independent_distribution_artifact = next(
        node
        for node in independent_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "_IndependentFillDistributionArtifactV1"
    )
    independent_expected_fill = function(
        independent_tree, "_independent_expected_fill_computation"
    )
    independent_boundary_source = "\n".join(
        (
            ast.unparse(independent_probability_artifact),
            ast.unparse(independent_distribution_artifact),
            ast.unparse(independent_expected_fill),
        )
    )
    for token in (
        "_decimal(self.probability, 'probability')",
        "_decimal(self.order_quantity, 'order_quantity')",
        "_decimal(self.normalization_tolerance, 'normalization_tolerance')",
        "_decimal(item[0], f'distribution[{index}].quantity')",
        "_decimal(item[1], f'distribution[{index}].probability')",
        "localcontext(_independent_decimal_context())",
    ):
        if token not in independent_boundary_source:
            raise ValueError(
                f"independent MATH-37/MATH-38 Decimal boundary differs: {token}"
            )


def _build_execution_receipt_rows(
    oracles: tuple[dict[str, object], ...],
    vectors: tuple[dict[str, object], ...],
) -> tuple[IndependentMathRowEvidenceV1, ...]:
    oracle_by_id = {str(row["math_spec_ref"]): row for row in oracles}
    vector_by_id = {str(row["math_spec_ref"]): row for row in vectors}
    decimal_boundary = _independent_decimal_boundary_evidence()

    oracle37 = oracle_by_id["MATH-37"]
    vector37 = vector_by_id["MATH-37"]
    horizons = vector37["inputs"]["same_order_context_horizons_seconds"]  # type: ignore[index]
    if horizons != [1, 5, 30]:
        raise ValueError("MATH-37 tracked horizon roster differs")
    artifacts = tuple(
        _fill_probability_fixture(horizon, probability)
        for horizon, probability in zip(horizons, ("0.1", "0.4", "0.8"), strict=True)
    )
    probabilities = tuple(
        _independent_fill_probability(
            artifact,
            feature_schema_ref="GOLDEN::FEATURES",
            scope_ref="GOLDEN::SCOPE",
            horizon_seconds=horizon,
        )
        for artifact, horizon in zip(artifacts, horizons, strict=True)
    )
    high_precision_text = "0.12345678901234567890123456789012345"
    high_precision_string_probability = _independent_fill_probability(
        _fill_probability_fixture(5, high_precision_text),
        feature_schema_ref="GOLDEN::FEATURES",
        scope_ref="GOLDEN::SCOPE",
        horizon_seconds=5,
    )
    high_precision_decimal_input = Decimal(high_precision_text)
    high_precision_decimal_artifact = _fill_probability_fixture(
        5, high_precision_decimal_input
    )
    high_precision_decimal_probability = _independent_fill_probability(
        high_precision_decimal_artifact,
        feature_schema_ref="GOLDEN::FEATURES",
        scope_ref="GOLDEN::SCOPE",
        horizon_seconds=5,
    )
    if (
        high_precision_string_probability
        != Decimal("0.1234567890123456789012345678901234")
        or high_precision_decimal_probability != high_precision_decimal_input
        or high_precision_decimal_artifact.probability
        is not high_precision_decimal_input
    ):
        raise ValueError("MATH-37 exact-Decimal input-boundary execution differs")
    actual37 = {
        "calibration_receipt_required": all(
            bool(artifact.calibration_receipt_ref) for artifact in artifacts
        ),
        "probabilities_bounded_0_1": all(0 <= value <= 1 for value in probabilities),
        "probability_non_decreasing_by_horizon": probabilities
        == tuple(sorted(probabilities)),
    }
    expected37 = vector37["expected"]
    if actual37 != expected37:
        raise ValueError("MATH-37 independent artifact result differs")
    missing_rejection = _capture_rejection(
        lambda: _independent_fill_probability(
            None,
            feature_schema_ref="GOLDEN::FEATURES",
            scope_ref="GOLDEN::SCOPE",
            horizon_seconds=5,
        ),
        "MODEL_ARTIFACT_REQUIRED",
        "no default fill-probability model exists",
    )
    negative37 = {
        "missing_artifact": missing_rejection,
        "stale_artifact": _capture_rejection(
            lambda: _fill_probability_fixture(
                5,
                "0.4",
                evaluated_at=datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
                artifact_valid_until=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            ),
            "MODEL_ARTIFACT_REQUIRED",
            "model calibration, validity, or feature freshness gate failed",
        ),
        "uncalibrated_artifact": _capture_rejection(
            lambda: _fill_probability_fixture(5, "0.4", calibration_state="PENDING"),
            "MODEL_ARTIFACT_REQUIRED",
            "model calibration, validity, or feature freshness gate failed",
        ),
        "nonfinite_probability": _capture_rejection(
            lambda: _fill_probability_fixture(5, "NaN"),
            "NONFINITE_NUMERIC_INPUT",
            "probability must be finite",
        ),
        "invalid_numeric_probability": _capture_rejection(
            lambda: _fill_probability_fixture(5, "not-a-number"),
            "INVALID_NUMERIC_INPUT",
            "probability is not a valid Decimal",
        ),
        "float_contamination": _capture_rejection(
            lambda: _fill_probability_fixture(5, 0.4),
            "FLOAT_DECIMAL_CONTAMINATION",
            "probability must be Decimal, canonical string, or integer",
        ),
    }
    binding37 = {
        name: _capture_rejection(
            lambda artifact=artifact, schema=schema, scope=scope, horizon=horizon: _independent_fill_probability(
                artifact,
                feature_schema_ref=schema,
                scope_ref=scope,
                horizon_seconds=horizon,
            ),
            "MODEL_ARTIFACT_REQUIRED",
            "model artifact is outside declared schema, scope, or horizon",
        )
        for name, artifact, schema, scope, horizon in (
            (
                "wrong_schema",
                artifacts[1],
                "GOLDEN::FEATURES::OTHER",
                "GOLDEN::SCOPE",
                5,
            ),
            (
                "wrong_scope",
                artifacts[1],
                "GOLDEN::FEATURES",
                "GOLDEN::SCOPE::OTHER",
                5,
            ),
            (
                "wrong_horizon",
                artifacts[1],
                "GOLDEN::FEATURES",
                "GOLDEN::SCOPE",
                30,
            ),
        )
    }
    boundary_artifact = _fill_probability_fixture(
        5,
        "0",
        evaluated_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=5),
    )
    upper_boundary = _fill_probability_fixture(5, "1")
    boundary37 = {
        "probability_zero": str(
            _independent_fill_probability(
                boundary_artifact,
                feature_schema_ref="GOLDEN::FEATURES",
                scope_ref="GOLDEN::SCOPE",
                horizon_seconds=5,
            )
        ),
        "probability_one": str(
            _independent_fill_probability(
                upper_boundary,
                feature_schema_ref="GOLDEN::FEATURES",
                scope_ref="GOLDEN::SCOPE",
                horizon_seconds=5,
            )
        ),
        "maximum_feature_age_inclusive": True,
    }
    precision37 = {
        "exact_maximum_age_probability": boundary37["probability_zero"],
        "over_maximum_age_rejection": _capture_rejection(
            lambda: _fill_probability_fixture(
                5,
                "0.4",
                evaluated_at=datetime(2026, 1, 1, tzinfo=UTC)
                + timedelta(seconds=5, microseconds=1),
            ),
            "MODEL_ARTIFACT_REQUIRED",
            "model calibration, validity, or feature freshness gate failed",
        ),
        "exact_decimal_input_boundary": {
            "shared_owner_execution": decimal_boundary,
            "high_precision_string_input": high_precision_text,
            "high_precision_string_observed": high_precision_string_probability,
            "high_precision_decimal_input": high_precision_decimal_input,
            "high_precision_decimal_observed": high_precision_decimal_probability,
            "decimal_object_preserved": (
                high_precision_decimal_artifact.probability
                is high_precision_decimal_input
            ),
            "production_owner_contract_guard": "STATIC_AST_EXECUTED",
        },
    }
    mutated_probability = _independent_fill_probability(
        replace(artifacts[1], probability=Decimal("0.5")),
        feature_schema_ref="GOLDEN::FEATURES",
        scope_ref="GOLDEN::SCOPE",
        horizon_seconds=5,
    )
    if mutated_probability == probabilities[1]:
        raise ValueError("MATH-37 probability mutation was not observed")

    oracle38 = oracle_by_id["MATH-38"]
    vector38 = vector_by_id["MATH-38"]
    distribution_rows = vector38["inputs"]["fill_quantity_distribution"]  # type: ignore[index]
    distribution = tuple(
        (row["quantity"], row["probability"]) for row in distribution_rows
    )
    artifact38 = _distribution_fixture(distribution)
    computation38 = _independent_expected_fill_computation(artifact38)
    expected_fill = computation38.normalized_expected_fill
    actual38 = {
        "expected_fill_quantity": expected_fill,
        "probability_sum": computation38.probability_sum,
        "weighted_sum": computation38.weighted_sum,
        "normalized_expected_fill": computation38.normalized_expected_fill,
    }
    expected38 = vector38["expected"]
    if expected_fill != _decimal(  # type: ignore[index]
        expected38["expected_fill_quantity"], "tracked_expected_fill_quantity"
    ):
        raise ValueError("MATH-38 independent expectation differs")
    mutated_distribution = _distribution_fixture(
        (("0", ".3"), ("50", ".3"), ("100", ".4"))
    )
    mutated_fill = _independent_expected_fill(mutated_distribution)
    if mutated_fill != Decimal("55") or mutated_fill == expected_fill:
        raise ValueError("MATH-38 distribution mutation was not observed")
    boundary_fill = _independent_expected_fill(_distribution_fixture((("0", "1"),)))
    negative38 = {
        "missing": _capture_rejection(
            lambda: _independent_expected_fill(None),
            "MODEL_ARTIFACT_REQUIRED",
            "a versioned fill distribution is required",
        ),
        "empty": _capture_rejection(
            lambda: _distribution_fixture(()),
            "MODEL_ARTIFACT_REQUIRED",
            "distribution artifact is stale or empty",
        ),
        "stale": _capture_rejection(
            lambda: _distribution_fixture(
                distribution,
                artifact_valid_until=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            "MODEL_ARTIFACT_REQUIRED",
            "distribution artifact is stale or empty",
        ),
        "malformed": _capture_rejection(
            lambda: _independent_expected_fill(
                _distribution_fixture((("0", ".2", "EXTRA"),))  # type: ignore[arg-type]
            ),
            "INVALID_CONTRACT",
            "distribution rows must be (quantity, probability)",
        ),
        "nonnormalized": _capture_rejection(
            lambda: _independent_expected_fill(
                _distribution_fixture((("0", ".2"), ("100", ".7")))
            ),
            "OUT_OF_DOMAIN",
            "fill probabilities exceed",
        ),
        "over_quantity": _capture_rejection(
            lambda: _independent_expected_fill(
                _distribution_fixture((("0", ".2"), ("101", ".8")))
            ),
            "OUT_OF_DOMAIN",
            "fill support exceeds order quantity",
        ),
        "decimal_input_boundary": {
            "float_order_quantity": _capture_rejection(
                lambda: _distribution_fixture(
                    distribution, order_quantity=100.0
                ),
                "FLOAT_DECIMAL_CONTAMINATION",
                "order_quantity must be Decimal, canonical string, or integer",
            ),
            "float_normalization_tolerance": _capture_rejection(
                lambda: _distribution_fixture(
                    distribution, normalization_tolerance=0.0
                ),
                "FLOAT_DECIMAL_CONTAMINATION",
                "normalization_tolerance must be Decimal, canonical string, or integer",
            ),
            "float_distribution_quantity": _capture_rejection(
                lambda: _independent_expected_fill(
                    _distribution_fixture(((0.0, "0.5"), ("100", "0.5")))
                ),
                "FLOAT_DECIMAL_CONTAMINATION",
                "distribution[0].quantity must be Decimal, canonical string, or integer",
            ),
            "float_distribution_probability": _capture_rejection(
                lambda: _independent_expected_fill(
                    _distribution_fixture((("0", 0.5), ("100", "0.5")))
                ),
                "FLOAT_DECIMAL_CONTAMINATION",
                "distribution[0].probability must be Decimal, canonical string, or integer",
            ),
            "invalid_numeric_text": _capture_rejection(
                lambda: _independent_expected_fill(
                    _distribution_fixture(
                        (("not-a-number", "0.5"), ("100", "0.5"))
                    )
                ),
                "INVALID_NUMERIC_INPUT",
                "distribution[0].quantity is not a valid Decimal",
            ),
            "nonfinite_numeric_text": _capture_rejection(
                lambda: _independent_expected_fill(
                    _distribution_fixture((("0", "NaN"), ("100", "0.5")))
                ),
                "NONFINITE_NUMERIC_INPUT",
                "distribution[0].probability must be finite",
            ),
            "boolean_input": _capture_rejection(
                lambda: _distribution_fixture(distribution, order_quantity=True),
                "FLOAT_DECIMAL_CONTAMINATION",
                "order_quantity must be Decimal, canonical string, or integer",
            ),
        },
    }
    domain38 = _capture_rejection(
        lambda: _independent_expected_fill(
            _distribution_fixture((("-1", ".2"), ("100", ".8")))
        ),
        "OUT_OF_DOMAIN",
        "distribution quantity/probability is invalid",
    )
    within_tolerance = _independent_expected_fill_computation(
        _distribution_fixture(
            (("0", ".2"), ("50", ".3"), ("100", ".5000000000005")),
            normalization_tolerance="0.000000000001",
        )
    )
    if within_tolerance != _IndependentExpectedFillComputationV1(
        probability_sum=Decimal("1.0000000000005"),
        weighted_sum=Decimal("65.0000000000500"),
        normalized_expected_fill=Decimal(
            "65.00000000001749999999999125000000"
        ),
    ):
        raise ValueError("MATH-38 within-tolerance normalization differs")
    exact_tolerance = _independent_expected_fill_computation(
        _distribution_fixture(
            (("0", ".2"), ("50", ".3"), ("100", ".500000000001")),
            normalization_tolerance="0.000000000001",
        )
    )
    if exact_tolerance != _IndependentExpectedFillComputationV1(
        probability_sum=Decimal("1.000000000001"),
        weighted_sum=Decimal("65.000000000100"),
        normalized_expected_fill=Decimal(
            "65.00000000003499999999996500000000"
        ),
    ):
        raise ValueError("MATH-38 exact-tolerance normalization differs")
    outside_tolerance = _capture_rejection(
        lambda: _independent_expected_fill(
            _distribution_fixture(
                (("0", ".2"), ("50", ".3"), ("100", ".500000000002")),
                normalization_tolerance="0.000000000001",
            )
        ),
        "OUT_OF_DOMAIN",
        "fill probabilities exceed",
    )
    high_precision_rounding = _independent_expected_fill_computation(
        _distribution_fixture(
            (
                ("76.619839145498174104090161033962172", "0.5"),
                ("0", "0.5"),
            ),
            normalization_tolerance="0",
        )
    )
    high_precision_expected = Decimal("38.30991957274908705204508051698108")
    high_precision_false_result = Decimal("38.30991957274908705204508051698109")
    if (
        high_precision_rounding.probability_sum != Decimal("1.0")
        or high_precision_rounding.normalized_expected_fill
        != high_precision_expected
        or high_precision_rounding.normalized_expected_fill
        == high_precision_false_result
    ):
        raise ValueError("MATH-38 exact-Decimal input-time rounding differs")
    negative38.update(
        {
            "zero_probability_sum": _capture_rejection(
                lambda: _independent_expected_fill(
                    _distribution_fixture((("0", "0"), ("100", "0")))
                ),
                "OUT_OF_DOMAIN",
                "fill probabilities exceed",
            ),
            "probability_above_one": _capture_rejection(
                lambda: _independent_expected_fill(
                    _distribution_fixture((("0", "0"), ("100", "1.0000000000001")))
                ),
                "OUT_OF_DOMAIN",
                "distribution quantity/probability is invalid",
            ),
        }
    )
    binding38 = {
        "missing_source": _capture_rejection(
            lambda: _distribution_fixture(distribution, source_binding_ref=""),
            "MODEL_ARTIFACT_REQUIRED",
            "source_binding_ref is required",
        ),
        "invalid_horizon": _capture_rejection(
            lambda: _distribution_fixture(distribution, horizon_seconds=0),
            "MODEL_ARTIFACT_REQUIRED",
            "distribution horizon must be explicit and positive",
        ),
        "order_quantity_custody": negative38["over_quantity"],
    }

    shared = {
        "domain_owner": (
            "tools/independent_validate_qku_computation_control_plane_execution.py"
        ),
        "evidence_tier": EVIDENCE_TIER,
        "independence_class": INDEPENDENT_REFERENCE_NO_PRODUCTION_RUNTIME_IMPORT,
        "production_system_under_test_invocation_count": 0,
        "production_expected_value_import_count": 0,
        "production_oracle_call_count": 0,
        "external_effect_count": 0,
        "terminal_state": TERMINAL_STATE,
    }
    return (
        IndependentMathRowEvidenceV1(
            math_id="MATH-37",
            oracle_id=str(oracle37["oracle_id"]),
            golden_vector_id=str(vector37["vector_id"]),
            comparison_policy=str(vector37["comparison_policy"]),
            observed_result=observed_result(
                independent_observation=actual37,
                independent_expected_result=expected37,  # type: ignore[arg-type]
                system_under_test_observation=NO_PRODUCTION_SYSTEM_UNDER_TEST,
                comparison_passed=True,
            ),
            boundary_or_invariant_observation=evidence_observation(
                "FILL_PROBABILITY_ENDPOINT_AND_FEATURE_AGE_BOUNDARIES",
                "BOUNDARY_PASS",
                boundary37,
            ),
            negative_or_abstention_observation=evidence_observation(
                "FILL_PROBABILITY_ARTIFACT_REJECTION_AND_ABSTENTION_MATRIX",
                "TYPED_REJECTION",
                negative37,
            ),
            formula_or_procedure_mutation_observation=evidence_observation(
                "CALIBRATED_PROBABILITY_OUTPUT_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {
                    "input_path": ["probability"],
                    "baseline_value": str(probabilities[1]),
                    "replacement_value": "0.5",
                    "baseline_result": str(probabilities[1]),
                    "mutated_result": str(mutated_probability),
                },
            ),
            domain_guard_observation=evidence_observation(
                "POSITIVE_INTEGER_HORIZON_GUARD",
                "TYPED_REJECTION",
                _capture_rejection(
                    lambda: _fill_probability_fixture(0, "0.4"),
                    "OUT_OF_DOMAIN",
                    "horizon_seconds must be positive",
                ),
            ),
            precision_or_tolerance_observation=evidence_observation(
                "MAXIMUM_FEATURE_AGE_INCLUSIVE_BOUNDARY",
                "BOUNDARY_PASS_AND_TYPED_REJECTION",
                precision37,
            ),
            source_unit_or_binding_observation=evidence_observation(
                "FEATURE_SCHEMA_SCOPE_AND_HORIZON_BINDING_MUTATIONS",
                "TYPED_REJECTION",
                binding37,
            ),
            **shared,
        ),
        IndependentMathRowEvidenceV1(
            math_id="MATH-38",
            oracle_id=str(oracle38["oracle_id"]),
            golden_vector_id=str(vector38["vector_id"]),
            comparison_policy=str(vector38["comparison_policy"]),
            observed_result=observed_result(
                independent_observation=actual38,
                independent_expected_result=expected38,  # type: ignore[arg-type]
                system_under_test_observation=NO_PRODUCTION_SYSTEM_UNDER_TEST,
                comparison_passed=True,
            ),
            boundary_or_invariant_observation=evidence_observation(
                "ZERO_FILL_EXACT_NORMALIZATION_BOUNDARY",
                "BOUNDARY_PASS",
                {"distribution": [["0", "1"]], "observed_result": boundary_fill},
            ),
            negative_or_abstention_observation=evidence_observation(
                "FILL_DISTRIBUTION_REJECTION_MATRIX",
                "TYPED_REJECTION",
                negative38,
            ),
            formula_or_procedure_mutation_observation=evidence_observation(
                "FILL_DISTRIBUTION_PROBABILITY_MUTATION",
                "OBSERVED_OUTPUT_CHANGE",
                {
                    "baseline_distribution": distribution,
                    "mutated_distribution": mutated_distribution.fill_quantity_distribution,
                    "baseline_result": expected_fill,
                    "mutated_result": mutated_fill,
                },
            ),
            domain_guard_observation=evidence_observation(
                "NONNEGATIVE_FILL_QUANTITY_GUARD",
                "TYPED_REJECTION",
                domain38,
            ),
            precision_or_tolerance_observation=evidence_observation(
                "EXPLICIT_NORMALIZATION_TOLERANCE_BOUNDARY",
                "BOUNDARY_PASS_AND_TYPED_REJECTION",
                {
                    "normalization_tolerance": "0.000000000001",
                    "within_tolerance": {
                        "probability_sum": within_tolerance.probability_sum,
                        "weighted_sum": within_tolerance.weighted_sum,
                        "normalized_expected_fill": (
                            within_tolerance.normalized_expected_fill
                        ),
                        "accepted": True,
                    },
                    "exact_tolerance": {
                        "probability_sum": exact_tolerance.probability_sum,
                        "weighted_sum": exact_tolerance.weighted_sum,
                        "normalized_expected_fill": (
                            exact_tolerance.normalized_expected_fill
                        ),
                        "accepted": True,
                    },
                    "outside_tolerance_rejection": outside_tolerance,
                    "exact_decimal_input_boundary": {
                        "shared_owner_execution": decimal_boundary,
                        "high_precision_distribution": [
                            ["76.619839145498174104090161033962172", "0.5"],
                            ["0", "0.5"],
                        ],
                        "probability_sum": high_precision_rounding.probability_sum,
                        "weighted_sum": high_precision_rounding.weighted_sum,
                        "normalized_expected_fill": (
                            high_precision_rounding.normalized_expected_fill
                        ),
                        "prior_false_result_rejected": (
                            high_precision_rounding.normalized_expected_fill
                            != high_precision_false_result
                        ),
                        "production_owner_contract_guard": "STATIC_AST_EXECUTED",
                    },
                },
            ),
            source_unit_or_binding_observation=evidence_observation(
                "SOURCE_HORIZON_AND_ORDER_QUANTITY_CUSTODY_MUTATIONS",
                "TYPED_REJECTION",
                binding38,
            ),
            **shared,
        ),
    )


def _tree(name: str) -> ast.Module:
    path = PACKAGE / name
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _class_methods(tree: ast.Module, class_name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"))
    raise ValueError(f"missing class {class_name}")


def _assigned_tuple(tree: ast.Module, name: str) -> tuple[object, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, tuple):
                return value
    raise ValueError(f"missing tuple {name}")


def _class_method_node(
    tree: ast.Module, class_name: str, method_name: str
) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise ValueError(f"missing {class_name}.{method_name}")


def _assigned_value(function: ast.FunctionDef, name: str) -> ast.expr:
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
        ):
            return node.value
    raise ValueError(f"missing assignment {name}")


def _attributes(node: ast.AST) -> set[str]:
    return {
        child.attr for child in ast.walk(node)
        if isinstance(child, ast.Attribute)
    }


def _call_order(tree: ast.Module) -> tuple[str, ...]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "execute":
            calls: list[tuple[int, int, str]] = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Attribute) and isinstance(child.func.value.value, ast.Name) and child.func.value.value.id == "self" and child.func.value.attr == "_adapter":
                    calls.append((child.lineno, child.col_offset, child.func.attr))
            return tuple(name for _, _, name in sorted(calls))
    raise ValueError("unit-of-work execute method missing")


def main() -> int:
    failures: list[str] = []
    receipt_rows: tuple[IndependentMathRowEvidenceV1, ...] = ()
    try:
        trees = {name: _tree(name) for name in NEW_MODULES}
        service_tree = _tree("service.py")
        validation_tree = _tree("validation.py")
        context_tree = _tree("context.py")
        independent_tree = ast.parse(
            Path(__file__).read_text(encoding="utf-8"), filename=__file__
        )
        _validate_execution_math_owner_ast(
            trees["economic_math.py"], context_tree, independent_tree
        )
    except (OSError, SyntaxError) as exc:
        print(f"source parse failed: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        failures.append(str(exc))
    try:
        oracles = _archive_rows(
            PACKAGE / "oracle_contracts.py", "_ST12C_ORACLE_ARCHIVE_B85"
        )
        vectors = _archive_rows(
            PACKAGE / "oracle_contracts.py", "_ST12C_VECTOR_ARCHIVE_B85"
        )
        receipt_rows = _build_execution_receipt_rows(oracles, vectors)
    except (
        OSError,
        SyntaxError,
        ValueError,
        KeyError,
        TypeError,
        zlib.error,
    ) as exc:
        failures.append(f"execution row-receipt reconstruction failed: {exc}")
    try:
        if _class_methods(service_tree, "QKUComputationControlPlaneV1") != SERVICE_METHODS:
            failures.append("existing public service method roster changed")
        gates = _assigned_tuple(trees["lifecycle.py"], "PREFLIGHT_GATE_CLASSES")
        if gates != ("SOURCE", "MODEL", "FRESHNESS", "VENUE", "CAP", "RISK", "CASH", "ACCOUNTING", "CONDUCT", "KILL", "MODE", "SNAPSHOT", "IDEMPOTENCY"):
            failures.append("preflight gate roster is not exact")
    except ValueError as exc:
        failures.append(str(exc))
    defined = {
        node.name
        for tree in trees.values()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if defined & FORBIDDEN_METHODS:
        failures.append(f"provider-write method implemented: {sorted(defined & FORBIDDEN_METHODS)}")
    forbidden_imports = {"requests", "httpx", "socket", "subprocess", "asyncio", "multiprocessing"}
    for name, tree in trees.items():
        roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        if roots & forbidden_imports:
            failures.append(f"forbidden operational import in {name}: {sorted(roots & forbidden_imports)}")
        if "sqlite3" in roots and name != "sqlite_reference.py":
            failures.append(f"SQLite ownership leaked into {name}")
    lifecycle_text = (PACKAGE / "lifecycle.py").read_text(encoding="utf-8")
    outbox_text = (PACKAGE / "outbox.py").read_text(encoding="utf-8")
    persistence_text = (PACKAGE / "persistence.py").read_text(encoding="utf-8")
    idempotency_text = (PACKAGE / "idempotency.py").read_text(encoding="utf-8")
    if "ExecutionRouterV1_FUTURE_SOLE_OWNER_NOT_IMPLEMENTED" not in lifecycle_text:
        failures.append("future sole release authority boundary missing")
    if "RECORDED_NOT_DISPATCHABLE" not in outbox_text or "OUTBOX_DISPATCHER_IMPLEMENTED = False" not in outbox_text:
        failures.append("outbox no-dispatch contract missing")
    if "NO_DEFAULT_REQUIRES_SEPARATE_RUNTIME_PLATFORM_AUTHORIZATION_AND_BENCHMARK" not in (PACKAGE / "migrations.py").read_text(encoding="utf-8"):
        failures.append("production persistence blocker missing")
    if "REFERENCE_STORE_LIFETIME_NO_TIME_BASED_PURGE_API" not in idempotency_text or "deterministic_json" not in idempotency_text:
        failures.append("idempotency canonical-text/retention law missing")
    persistence_methods = set(_class_methods(trees["persistence.py"], "PersistenceAdapterV1"))
    expected_methods = {
        "availability", "begin_transaction", "insert_receipt_record", "insert_value_lineage_edge",
        "insert_economic_event", "insert_journal_transaction", "insert_journal_posting",
        "insert_state_transition", "acquire_idempotency_claim", "bind_idempotency_result",
        "insert_outbox_intent", "insert_reversal_link", "insert_reconciliation_break",
        "load_committed_reversal_history", "get_record", "get_idempotency_result",
        "reconstruct_as_of",
    }
    if persistence_methods != expected_methods:
        failures.append(f"typed persistence interface mismatch: {sorted(persistence_methods ^ expected_methods)}")
    for module_name, class_name in (
        ("persistence.py", "InMemoryPersistenceAdapterV1"),
        ("sqlite_reference.py", "SQLiteReferenceAdapterV1"),
    ):
        if "load_committed_reversal_history" not in _class_methods(
            trees[module_name],
            class_name,
        ):
            failures.append(
                f"{class_name}: committed reversal-history read contract missing"
            )
    try:
        atomic_post_init = _class_method_node(
            trees["transaction.py"],
            "TrancheCAtomicRecordSetV1",
            "__post_init__",
        )
        journal_is_reversal = _assigned_value(
            atomic_post_init, "journal_is_reversal"
        )
        reversal_link_count = _assigned_value(
            atomic_post_init, "reversal_link_count"
        )
        bijection_compare = any(
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == "journal_is_reversal"
            and any(
                isinstance(child, ast.Name)
                and child.id == "reversal_link_count"
                for comparator in node.comparators
                for child in ast.walk(comparator)
            )
            for node in ast.walk(atomic_post_init)
        )
        bounded_link_count = any(
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == "reversal_link_count"
            and any(isinstance(operator, ast.NotIn) for operator in node.ops)
            for node in ast.walk(atomic_post_init)
        )
        if (
            not {"journal_transaction", "reversal_of_transaction_id"}
            <= _attributes(journal_is_reversal)
            or "reversal_links" not in _attributes(reversal_link_count)
            or not bijection_compare
            or not bounded_link_count
            or not {
                "original_event_or_transaction_ref",
                "reversal_transaction_ref",
                "reversal_event_ref",
                "economic_event_refs",
            } <= _attributes(atomic_post_init)
        ):
            failures.append(
                "atomic record set does not enforce reversal-journal/link bijection"
            )

        execute = _class_method_node(
            trees["transaction.py"], "TrancheCUnitOfWorkV1", "execute"
        )
        original_reversal_ref = _assigned_value(execute, "original_reversal_ref")
        history_calls = tuple(
            node for node in ast.walk(execute)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "load_committed_reversal_history"
        )
        history_uses_typed_ref = (
            len(history_calls) == 1
            and len(history_calls[0].args) >= 2
            and isinstance(history_calls[0].args[1], ast.Name)
            and history_calls[0].args[1].id == "original_reversal_ref"
        )
        typed_admission = any(
            isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Name)
                and child.id == "original_reversal_ref"
                for child in ast.walk(node.test)
            )
            for node in ast.walk(execute)
        )
        bool_link_gates = tuple(
            node for node in ast.walk(execute)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "bool"
            and any(
                isinstance(child, ast.Attribute)
                and child.attr == "reversal_links"
                for child in ast.walk(node)
            )
        )
        if (
            not {"journal_transaction", "reversal_of_transaction_id"}
            <= _attributes(original_reversal_ref)
            or not typed_admission
            or not history_uses_typed_ref
            or bool_link_gates
            or not {
                "reversal_links",
                "original_event_or_transaction_ref",
                "reversal_transaction_ref",
                "reversal_event_ref",
                "economic_event_refs",
            } <= _attributes(execute)
        ):
            failures.append(
                "unit of work does not derive reversal history admission from the typed journal"
            )
    except ValueError as exc:
        failures.append(str(exc))
    ordered = _call_order(trees["transaction.py"])
    required_order = (
        "acquire_idempotency_claim", "load_committed_reversal_history",
        "insert_receipt_record", "insert_economic_event",
        "insert_value_lineage_edge", "insert_journal_transaction", "insert_journal_posting",
        "insert_state_transition", "insert_outbox_intent", "insert_reversal_link",
        "insert_reconciliation_break", "bind_idempotency_result",
    )
    positions = [ordered.index(name) if name in ordered else -1 for name in required_order]
    if -1 in positions or positions != sorted(positions):
        failures.append(f"atomic unit-of-work call order mismatch: {ordered}")
    identity_fields = _class_methods(trees["lifecycle.py"], "EconomicIdentitySetV1")
    # A frozen dataclass has only __post_init__ as a method; inspect annotated fields instead.
    identity_class = next(node for node in trees["lifecycle.py"].body if isinstance(node, ast.ClassDef) and node.name == "EconomicIdentitySetV1")
    identity_names = tuple(node.target.id for node in identity_class.body if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name))
    if identity_names != ("semantic_economic_intent_id", "command_id", "attempt_id", "provider_request_id", "request_id", "trace_id", "transaction_id", "event_id"):
        failures.append("economic identity separation fields are not exact")
    fill_distribution = ((Decimal(0), Decimal(".2")), (Decimal(50), Decimal(".3")), (Decimal(100), Decimal(".5")))
    if sum((quantity * probability for quantity, probability in fill_distribution), Decimal(0)) != Decimal(65):
        failures.append("independent expected partial-fill oracle failed")
    probabilities = (Decimal(".1"), Decimal(".4"), Decimal(".8"))
    if not all(Decimal(0) <= value <= Decimal(1) for value in probabilities) or tuple(sorted(probabilities)) != probabilities:
        failures.append("independent fill-probability structural invariant failed")
    blocker_mapping = next(
        (node.value for node in validation_tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ST12C_LATER_PHASE_BLOCKERS" for target in node.targets)),
        None,
    )
    if not isinstance(blocker_mapping, ast.Call) or not blocker_mapping.args or not isinstance(blocker_mapping.args[0], ast.Dict) or len(blocker_mapping.args[0].keys) != 9:
        failures.append("nine later-phase blockers are not explicit")
    matrix_root = REPO_ROOT / "tests" / "stage1_prediction_markets" / "qku_computation_control_plane"
    if not (matrix_root / "accounting" / "test_contract_matrix.py").is_file() or not (matrix_root / "execution" / "test_contract_matrix.py").is_file():
        failures.append("centralized contract matrices are missing")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(format_evidence_line(build_envelope("EXECUTION", receipt_rows)))
    print(f"{SUCCESS} controls=9 identities=8 gates=13 lifecycle=NO_WRITE effects=0 blockers=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
