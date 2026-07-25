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
    Overflow,
    ROUND_HALF_EVEN,
)

from .errors import ContractValidationError, NumericDomainError, ReasonCode


DECIMAL_PRECISION = 34
DECIMAL_ROUNDING = ROUND_HALF_EVEN


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
    try:
        result = (
            value
            if isinstance(value, Decimal)
            else decimal_context_v1().create_decimal(value)
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise NumericDomainError(
            ReasonCode.INVALID_NUMERIC_INPUT, f"{field_name} is not a valid Decimal"
        ) from exc
    if not result.is_finite():
        raise NumericDomainError(
            ReasonCode.NONFINITE_NUMERIC_INPUT, f"{field_name} must be finite"
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
