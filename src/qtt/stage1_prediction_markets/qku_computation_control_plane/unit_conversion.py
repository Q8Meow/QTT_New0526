"""Allowlisted, receipt-producing ST12-B type/unit/basis conversions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Callable, Mapping

from .context import finite_float
from .errors import ReasonCode, UnitConversionError
from .models import ComputationExecutionContextV1


class ConversionIdentityV1(StrEnum):
    DECIMAL_PROBABILITY_TO_FINITE_FLOAT64 = (
        "CONVERSION::DECIMAL_PROBABILITY_TO_FINITE_FLOAT64_V1"
    )


@dataclass(frozen=True, slots=True)
class UnitBasisDescriptorV1:
    type_name: str
    shape: str
    unit: str
    basis: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value
            for value in (self.type_name, self.shape, self.unit, self.basis)
        ):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_FAILED,
                "conversion descriptors require exact type, shape, unit, and basis",
            )


@dataclass(frozen=True, slots=True)
class UnitConversionReceiptV1:
    receipt_id: str
    conversion_id: ConversionIdentityV1
    conversion_version: str
    source: UnitBasisDescriptorV1
    target: UnitBasisDescriptorV1
    source_value: object
    converted_value: object
    rounding_and_precision: str
    execution_context: ComputationExecutionContextV1
    failure_disposition: str
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            not self.receipt_id
            or self.conversion_version != "1.0.0"
            or not self.rounding_and_precision
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or not self.failure_disposition
            or self.no_authority_flag is not True
        ):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_FAILED,
                "conversion receipt is incomplete",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


def _decimal_probability_to_float64(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise UnitConversionError(
            ReasonCode.UNIT_CONVERSION_FAILED,
            "the data edge requires an actual Decimal producer result",
        )
    if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
        raise UnitConversionError(
            ReasonCode.UNIT_CONVERSION_FAILED,
            "producer Decimal probability must be finite and in [0,1]",
        )
    converted = finite_float(value, field_name="producer_probability")
    if not 0.0 <= converted <= 1.0:
        raise UnitConversionError(
            ReasonCode.UNIT_CONVERSION_FAILED,
            "converted float64 probability is outside [0,1]",
        )
    return converted


_CONVERTERS: Mapping[ConversionIdentityV1, Callable[[object], object]] = (
    MappingProxyType(
        {
            ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64: (
                _decimal_probability_to_float64
            )
        }
    )
)


class UnitConversionOwnerV1:
    """The sole conversion owner; identity conversions are never implicit."""

    @staticmethod
    def convert(
        *,
        conversion_id: ConversionIdentityV1,
        value: object,
        source: UnitBasisDescriptorV1,
        target: UnitBasisDescriptorV1,
        context: ComputationExecutionContextV1,
        receipt_id: str,
    ) -> tuple[object, UnitConversionReceiptV1]:
        if not isinstance(conversion_id, ConversionIdentityV1):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_FORBIDDEN,
                "conversion identity is not allowlisted",
            )
        if not isinstance(source, UnitBasisDescriptorV1) or not isinstance(
            target, UnitBasisDescriptorV1
        ):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_FAILED,
                "typed source and target descriptors are required",
            )
        if not isinstance(context, ComputationExecutionContextV1):
            raise UnitConversionError(
                ReasonCode.UNIT_CONVERSION_FAILED,
                "conversion requires the exact execution context",
            )
        if conversion_id is ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64:
            expected_source = UnitBasisDescriptorV1(
                "Decimal",
                "scalar",
                "dimensionless",
                "winning payout-normalized probability",
            )
            expected_target = UnitBasisDescriptorV1(
                "float64",
                "scalar",
                "probability points",
                "unit interval",
            )
            if source != expected_source or target != expected_target:
                raise UnitConversionError(
                    ReasonCode.UNIT_CONVERSION_FORBIDDEN,
                    "source/target type, shape, unit, or basis differs from the edge",
                )
        converted = _CONVERTERS[conversion_id](value)
        receipt = UnitConversionReceiptV1(
            receipt_id=receipt_id,
            conversion_id=conversion_id,
            conversion_version="1.0.0",
            source=source,
            target=target,
            source_value=value,
            converted_value=converted,
            rounding_and_precision=(
                "EXACT_DECIMAL_TO_NEAREST_FINITE_IEEE754_BINARY64; "
                "NO_PRECONVERSION_ROUNDING"
            ),
            execution_context=context,
            failure_disposition="DEPENDENCY_UNRESOLVED_BLOCK_CONTEXT_AND_STACK",
        )
        return converted, receipt
