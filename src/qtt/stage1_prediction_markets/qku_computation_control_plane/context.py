"""Explicit point-in-time and Decimal context ownership."""

from __future__ import annotations

from dataclasses import dataclass
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
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_UP,
    ROUND_UP,
)
from enum import StrEnum

from .errors import ContractValidationError, NumericDomainError, ReasonCode


DECIMAL_PRECISION = 34
DECIMAL_ROUNDING = ROUND_HALF_EVEN


class QuantizationRoundingV1(StrEnum):
    """Allowlisted Decimal rounding modes; no module-local implicit default."""

    HALF_EVEN = ROUND_HALF_EVEN
    HALF_UP = ROUND_HALF_UP
    HALF_DOWN = ROUND_HALF_DOWN
    DOWN = ROUND_DOWN
    UP = ROUND_UP
    FLOOR = ROUND_FLOOR
    CEILING = ROUND_CEILING


def decimal_context_v1() -> Context:
    context = Context(prec=DECIMAL_PRECISION, rounding=DECIMAL_ROUNDING)
    context.traps[FloatOperation] = True
    context.traps[InvalidOperation] = True
    context.traps[DivisionByZero] = True
    context.traps[Overflow] = True
    return context


def exact_decimal(value: Decimal | str | int, *, field_name: str = "value") -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise NumericDomainError(
            ReasonCode.FLOAT_DECIMAL_CONTAMINATION,
            f"{field_name} must be Decimal, canonical string, or integer",
        )
    if not isinstance(value, (Decimal, str, int)):
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT,
            f"{field_name} is not a valid Decimal",
        )
    try:
        result = (
            value
            if isinstance(value, Decimal)
            else decimal_context_v1().create_decimal(value)
        )
    except (InvalidOperation, Overflow, ValueError, TypeError) as exc:
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT, f"{field_name} is not a valid Decimal"
        ) from exc
    if not result.is_finite():
        raise NumericDomainError(
            ReasonCode.NONFINITE_NUMERIC_INPUT, f"{field_name} must be finite"
        )
    return result


def canonical_probability_decimal(
    value: Decimal | str | int | float,
    *,
    field_name: str = "probability",
) -> Decimal:
    """Convert a probability without weakening the general Decimal boundary.

    Python floats are accepted only on explicitly declared probability surfaces.
    Their canonical value is constructed from Python's shortest round-trip text;
    ``Decimal(float)`` is never used.
    """

    if isinstance(value, bool) or not isinstance(value, Decimal | str | int | float):
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT,
            f"{field_name} must be a Decimal, canonical string, integer, or float",
        )
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise NumericDomainError(
                ReasonCode.NONFINITE_NUMERIC_INPUT,
                f"{field_name} must be finite",
            )
        result = exact_decimal(repr(value), field_name=field_name)
    else:
        result = exact_decimal(value, field_name=field_name)
    if result < Decimal(0) or result > Decimal(1):
        raise NumericDomainError(
            ReasonCode.OUT_OF_DOMAIN,
            f"{field_name} must be in [0, 1]",
        )
    return result


def finite_float(
    value: float | int | str | Decimal,
    *,
    field_name: str = "value",
) -> float:
    if isinstance(value, bool) or not isinstance(
        value, float | int | str | Decimal
    ):
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT, f"{field_name} must be numeric"
        )
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT, f"{field_name} must be numeric"
        ) from exc
    if result != result or result in (float("inf"), float("-inf")):
        raise NumericDomainError(
            ReasonCode.NONFINITE_NUMERIC_INPUT, f"{field_name} must be finite"
        )
    return result


def parse_utc(value: datetime | str, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, f"{field_name} must be ISO-8601"
            ) from exc
    else:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT, f"{field_name} must be datetime or ISO-8601"
        )
    if parsed.tzinfo is None:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT, f"{field_name} must be timezone-aware"
        )
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class QuantizationPolicyV1:
    """One field- and binding-specific quantization boundary."""

    policy_id: str
    field_id: str
    increment: Decimal | str | int
    rounding: QuantizationRoundingV1
    unit: str
    currency_or_asset: str
    basis: str
    scale: int
    source_binding_ref: str

    def __post_init__(self) -> None:
        for name in (
            "policy_id",
            "field_id",
            "unit",
            "currency_or_asset",
            "basis",
            "source_binding_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"quantization {name} is required",
                )
        increment = exact_decimal(self.increment, field_name="increment")
        if increment <= 0:
            raise NumericDomainError(
                ReasonCode.OUT_OF_DOMAIN,
                "quantization increment must be positive",
            )
        if not isinstance(self.rounding, QuantizationRoundingV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "rounding must be an allowlisted QuantizationRoundingV1",
            )
        if isinstance(self.scale, bool) or not isinstance(self.scale, int) or self.scale < 0:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "quantization scale must be a nonnegative integer",
            )
        if increment.as_tuple().exponent != -self.scale:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "quantization increment exponent must match declared scale",
            )
        object.__setattr__(self, "increment", increment)


@dataclass(frozen=True, slots=True)
class QuantizationReceiptV1:
    receipt_id: str
    policy_ref: str
    field_id: str
    pre_value: Decimal
    post_value: Decimal
    residual: Decimal
    unit: str
    currency_or_asset: str
    basis: str
    scale: int
    rounding: QuantizationRoundingV1

    def __post_init__(self) -> None:
        for name in ("receipt_id", "policy_ref", "field_id", "unit", "currency_or_asset", "basis"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"quantization receipt {name} is required",
                )
        pre = exact_decimal(self.pre_value, field_name="pre_value")
        post = exact_decimal(self.post_value, field_name="post_value")
        residual = exact_decimal(self.residual, field_name="residual")
        if pre - post != residual:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "quantization residual must equal pre_value - post_value",
            )
        if isinstance(self.scale, bool) or not isinstance(self.scale, int) or self.scale < 0:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "quantization receipt scale must be nonnegative integer")
        if not isinstance(self.rounding, QuantizationRoundingV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "quantization receipt rounding must be allowlisted")
        if post.as_tuple().exponent != -self.scale:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "quantized value precision does not match the receipt scale",
            )
        object.__setattr__(self, "pre_value", pre)
        object.__setattr__(self, "post_value", post)
        object.__setattr__(self, "residual", residual)


def quantize_decimal_v1(
    value: Decimal | str | int,
    *,
    policy: QuantizationPolicyV1,
    receipt_id: str,
) -> QuantizationReceiptV1:
    """Quantize exactly once through the declared typed policy."""

    if not isinstance(policy, QuantizationPolicyV1):
        raise ContractValidationError(
            ReasonCode.QUANTIZATION_POLICY_MISSING,
            "a typed quantization policy is required",
        )
    pre = exact_decimal(value, field_name=policy.field_id)
    with localcontext(decimal_context_v1()) as context:
        units = context.divide(pre, policy.increment)
        rounded_units = units.to_integral_value(rounding=policy.rounding.value)
        post = context.quantize(
            context.multiply(rounded_units, policy.increment),
            policy.increment,
        )
        residual = context.subtract(pre, post)
    return QuantizationReceiptV1(
        receipt_id=receipt_id,
        policy_ref=policy.policy_id,
        field_id=policy.field_id,
        pre_value=pre,
        post_value=post,
        residual=residual,
        unit=policy.unit,
        currency_or_asset=policy.currency_or_asset,
        basis=policy.basis,
        scale=policy.scale,
        rounding=policy.rounding,
    )


@dataclass(frozen=True, slots=True)
class ComputationContextKeyV1:
    context_id: str
    as_of: datetime
    observed_at: datetime
    source_epoch_id: str
    input_version: str
    maximum_age: timedelta

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (
                self.context_id,
                self.source_epoch_id,
                self.input_version,
            )
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "context id, source epoch, and input version are required",
            )
        object.__setattr__(self, "as_of", parse_utc(self.as_of, field_name="as_of"))
        object.__setattr__(
            self, "observed_at", parse_utc(self.observed_at, field_name="observed_at")
        )
        if (
            not isinstance(self.maximum_age, timedelta)
            or self.maximum_age <= timedelta(0)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "maximum_age must be positive"
            )
        if self.observed_at > self.as_of:
            raise ContractValidationError(
                ReasonCode.FUTURE_CONTEXT,
                "observed_at cannot be later than the point-in-time as_of",
            )

    @property
    def stable_key(self) -> str:
        return "|".join(
            (
                self.context_id,
                self.as_of.isoformat(),
                self.observed_at.isoformat(),
                self.source_epoch_id,
                self.input_version,
            )
        )

    def assert_fresh(self) -> None:
        if self.as_of - self.observed_at > self.maximum_age:
            raise ContractValidationError(
                ReasonCode.STALE_CONTEXT,
                "context observation exceeds the declared maximum age",
            )
