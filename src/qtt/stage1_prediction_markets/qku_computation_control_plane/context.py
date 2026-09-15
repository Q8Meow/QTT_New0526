"""Explicit point-in-time and Decimal context ownership."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
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


# F12 exact-input ports; legacy datetime and numeric behavior stays above.
def _native_require(value: bool, code: str) -> None:
    if not value:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, code)


def _native_reference_reason(error: ContractValidationError, allowed: frozenset[str]) -> str | None:
    # Only exact failures produced by this selected reference layer are translated.
    if type(error) is not ContractValidationError or error.reason_code is not ReasonCode.INVALID_CONTRACT:
        return None
    for detail in allowed:
        if error.args == (f"{ReasonCode.INVALID_CONTRACT}: {detail}",):
            return detail
    return None

def _native_text(value: object) -> str:
    _native_require(type(value) is str and bool(value) and (value == value.strip()), 'TEXT')
    _native_require(
        all((ord(c) >= 32 and ord(c) != 127 and (not 55296 <= ord(c) <= 57343) for c in value)),
        'TEXT'
    )
    return value

def _native_ident(x):
    _native_text(x)
    _native_require(
        len(x) <= 256 and (not any((ord(c) < 33 or 127 <= ord(c) < 160 for c in x))),
        'IDENTITY'
    )
    return x

def _native_obj(x, required, optional=()):
    _native_require(
        type(x) is dict and set(required) <= set(x) and (set(x) <= set(required) | set(optional)),
        'NATIVE_FIELDS'
    )
    return x

def _native_scalar(value: object, kind: str) -> bool:
    """F12's selected boolean specialization; no numeric scalar branch is claimed."""
    _native_require(type(kind) is str and kind == "bool", "UNREGISTERED_SCALAR")
    _native_require(type(value) is bool, "BOOLEAN")
    return value

def _native_utc_nanoseconds(value):
    """RFC3339 instant to exact epoch ns, including numeric offsets.

    No leap-second conversion owner is bound. Unknown -00:00 offset is rejected;
    normalized UTC must stay within calendar years 1..9999. No float is used.
    """
    _native_require(type(value) is str, 'UTC_NANOSECONDS')
    m = re.fullmatch(
        '(\\d{4}-\\d\\d-\\d\\dT\\d\\d:\\d\\d:\\d\\d)(?:\\.(\\d{1,9}))?(Z|[+-]\\d\\d:\\d\\d)',
        value,
        flags=re.ASCII
    )
    _native_require(m is not None and m[3] != '-00:00', 'UTC_NANOSECONDS')
    # CPython accepts ISO 24:00 midnight; F12's RFC3339 subset does not.
    _native_require(int(m[1][11:13]) < 24, 'UTC_NANOSECONDS')
    try:
        dt = datetime.fromisoformat(m[1] + ('+00:00' if m[3] == 'Z' else m[3])).astimezone(timezone.utc)
    except (ValueError, OverflowError) as e:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'UTC_NANOSECONDS') from e
    if m[3] != 'Z':
        _native_require(int(m[3][1:3]) < 24 and int(m[3][4:6]) < 60, 'UTC_NANOSECONDS')
    delta = dt - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1000000000 + int((m[2] or '').ljust(9, '0') or '0')

def _native_utc_receipt_pair(value):
    """One exact UTC conversion owner for V1/V3 compatibility projections."""
    ns = _native_utc_nanoseconds(value)
    dt = datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    delta = dt - datetime(1970, 1, 1, tzinfo=timezone.utc)
    floor_us = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    remainder = ns - floor_us * 1000
    _native_require(0 <= remainder < 1000, 'PIT_TIME_PROJECTION_MISMATCH')
    stamp = f'{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
    return {
        'source_text': value,
        'utc_ns_text': str(ns),
        'canonical_utc': stamp + f'.{ns % 1000000000:09d}Z',
        'receipt_utc_floor': dt.isoformat(timespec='microseconds').replace('+00:00', 'Z'),
        'nanosecond_remainder': remainder
    }


def _native_bounded_decimal(value: object) -> Decimal:
    """The selected raw-token domain; independent of ambient Decimal precision."""
    _native_require(type(value) is Decimal and value.is_finite(), "NUMBER")
    _native_require(not (value == 0 and value.is_signed()), "NUMBER")
    digits = value.as_tuple().digits
    exponent = value.as_tuple().exponent
    _native_require(
        len(digits) <= 128 and type(exponent) is int and -128 <= exponent <= 128,
        "NUMBER_BOUND",
    )
    _native_require(value == 0 or -100 <= value.adjusted() <= 100, "NUMBER_BOUND")
    return value


# F14 selected Retail-US value helpers; the F12 boolean specialization is unchanged.
from fractions import Fraction


def _native_retail_decimal_string_v1(value: object) -> Decimal:
    _native_require(type(value) is str and re.fullmatch('-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?', value) is not None, 'DECIMAL_TEXT')
    _native_require(len(value) <= 128, 'DECIMAL_BOUND')
    result = Decimal(value)
    _native_require(result.is_finite() and (not (result == 0 and result.is_signed())), 'DECIMAL_DOMAIN')
    return result


def _native_retail_finite_decimal_text_v1(value: Fraction) -> str:
    """Exact finite-decimal rendering from a rational; independent of Decimal context."""
    f = Fraction(value)
    n, d = (f.numerator, f.denominator)
    twos = fives = 0
    while d % 2 == 0:
        d //= 2
        twos += 1
    while d % 5 == 0:
        d //= 5
        fives += 1
    _native_require(d == 1, 'NONTERMINATING_DECIMAL')
    scale = max(twos, fives)
    n *= 2 ** (scale - twos) * 5 ** (scale - fives)
    digits = str(abs(n)).rjust(scale + 1, '0')
    if scale:
        digits = (digits[:-scale] + '.' + digits[-scale:]).rstrip('0').rstrip('.')
    return ('-' if n < 0 else '') + digits if n else '0'


def _native_retail_known_v1(value, required):
    _native_require(type(value) is dict and set(required) <= set(value), 'REQUIRED_NATIVE_FIELD')
    return value


def _native_retail_rows_v1(value, maximum):
    _native_require(type(maximum) is int and 0 < maximum <= 10000, 'ROW_BUDGET')
    _native_require(type(value) is list and len(value) <= maximum, 'ROW_BOUND')
    return value


def _native_retail_scalar_v1(x, kind):
    if kind == 'id':
        return _native_ident(x)
    if kind == 'bool':
        _native_require(type(x) is bool, 'BOOLEAN')
        return x
    if kind == 'decimal':
        return _native_retail_decimal_string_v1(x)
    if kind == 'number':
        _native_require(type(x) in (int, Decimal), 'JSON_NUMBER')
        return _native_bounded_decimal(Decimal(x))
    if kind == 'integer':
        q = _native_retail_scalar_v1(x, 'number')
        _native_require(q == q.to_integral_value() and 0 <= q <= 2 ** 63 - 1, 'INTEGER')
        return int(q)
    if kind == 'seconds_string':
        _native_require(type(x) is str and re.fullmatch('[1-9][0-9]{0,18}', x) is not None and (int(x) < 2 ** 63), 'SECONDS_STRING')
        return int(x)
    if kind == 'utc':
        _native_require(type(x) is str and re.fullmatch('\\d{4}-\\d\\d-\\d\\dT\\d\\d:\\d\\d:\\d\\d(?:\\.\\d{1,6})?Z', x) is not None, 'UTC')
        try:
            return datetime.fromisoformat(x.replace('Z', '+00:00'))
        except ValueError as e:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'UTC') from e
    if kind.startswith('enum:'):
        _native_require(type(x) is str and x in kind[5:].split(','), 'ENUM')
        return x
    if kind == 'ids':
        _native_require(type(x) is list and len(x) <= 100, 'LIST_BOUND')
        vals = [_native_ident(v) for v in x]
        _native_require(len(set(vals)) == len(vals), 'DUPLICATE_IDENTITY')
        return vals
    if kind == 'money':
        _native_obj(x, ('value', 'currency'))
        _native_ident(x['currency'])
        return _native_retail_scalar_v1(x['value'], 'decimal')
    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'UNREGISTERED_SCALAR')


def _native_retail_nonnegative_v1(value, kind='decimal'):
    result = _native_retail_scalar_v1(value, kind)
    _native_require(result >= 0, 'NONNEGATIVE')
    return result


def _native_retail_exact_text_v1(value):
    return _native_retail_finite_decimal_text_v1(Fraction(value))
# F14 uses detached internal mappings; exact dict/list projections are made only
# at the preserved native and storage predicate boundaries.
def _f14_freeze_v1(value):
    from collections.abc import Mapping
    from types import MappingProxyType
    if isinstance(value, Mapping):
        return MappingProxyType({key: _f14_freeze_v1(item) for key, item in value.items()})
    if type(value) in (list, tuple):
        return tuple(_f14_freeze_v1(item) for item in value)
    if type(value) is set:
        return frozenset(value)
    return value


def _f14_plain_v1(value):
    from collections.abc import Mapping
    if isinstance(value, Mapping):
        return {key: _f14_plain_v1(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_f14_plain_v1(item) for item in value]
    return value
