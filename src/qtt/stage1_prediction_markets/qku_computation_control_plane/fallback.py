"""Typed deterministic fallback translation at the sole public boundary."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .errors import (
    AuthorityDeniedError,
    ComputationControlPlaneError,
    ContextualComputabilityError,
    ContractValidationError,
    DependencyGraphError,
    FormulaExecutionError,
    FreshnessError,
    InputAuthorityError,
    NumericDomainError,
    OperationBoundaryError,
    OutputContractError,
    ParameterPolicyError,
    PointInTimeError,
    ReasonCode,
    SourcePolicyError,
    StackResolutionError,
    UnitConversionError,
)
from .models import OperationBlockerCodeV1, OperationStatusV1


EXPECTED_PUBLIC_OPERATION_ERRORS = (
    AuthorityDeniedError,
    ContextualComputabilityError,
    ContractValidationError,
    DependencyGraphError,
    FormulaExecutionError,
    FreshnessError,
    InputAuthorityError,
    NumericDomainError,
    OperationBoundaryError,
    OutputContractError,
    ParameterPolicyError,
    PointInTimeError,
    SourcePolicyError,
    StackResolutionError,
    UnitConversionError,
)


@dataclass(frozen=True, slots=True)
class FallbackDispositionV1:
    status: OperationStatusV1
    blocker_code: OperationBlockerCodeV1
    terminal_route: str
    reason_code: str
    numeric_result_emitted: bool = False
    selected_stack_fabricated: bool = False
    runtime_effect_authorized: bool = False

    def __post_init__(self) -> None:
        if (
            self.status is OperationStatusV1.SUCCEEDED
            or not self.terminal_route
            or not self.reason_code
            or self.numeric_result_emitted
            or self.selected_stack_fabricated
            or self.runtime_effect_authorized
        ):
            raise OperationBoundaryError(
                ReasonCode.OPERATION_BLOCKED,
                "fallback dispositions must be fail-closed and no-effect",
            )


_BLOCKER_BY_REASON_SUFFIX: Mapping[str, OperationBlockerCodeV1] = MappingProxyType(
    {
        "NO_APPLICABLE_STACK": OperationBlockerCodeV1.NO_APPLICABLE_STACK,
        "INPUT_OWNER_MISSING": OperationBlockerCodeV1.INPUT_OWNER_MISSING,
        "INPUT_OWNER_MISMATCH": OperationBlockerCodeV1.INPUT_OWNER_MISMATCH,
        "INPUT_PACKET_MISMATCH": OperationBlockerCodeV1.INPUT_PACKET_MISMATCH,
        "INPUT_SCHEMA_MISMATCH": OperationBlockerCodeV1.INPUT_SCHEMA_MISMATCH,
        "INPUT_SCOPE_MISMATCH": OperationBlockerCodeV1.INPUT_SCOPE_MISMATCH,
        "INPUT_VALUE_CONFLICT": OperationBlockerCodeV1.INPUT_VALUE_CONFLICT,
        "POINT_IN_TIME_VIOLATION": OperationBlockerCodeV1.POINT_IN_TIME_VIOLATION,
        "FRESHNESS_VIOLATION": OperationBlockerCodeV1.FRESHNESS_VIOLATION,
        "STALE_CONTEXT": OperationBlockerCodeV1.CONTEXT_STALE,
        "SOURCE_EPOCH_STALE": OperationBlockerCodeV1.FRESHNESS_VIOLATION,
        "SOURCE_CONFLICT": OperationBlockerCodeV1.SOURCE_CONFLICT,
        "PARAMETER_OWNER_MISSING": OperationBlockerCodeV1.PARAMETER_OWNER_MISSING,
        "PARAMETER_BINDING_MISMATCH": (
            OperationBlockerCodeV1.PARAMETER_BINDING_MISMATCH
        ),
        "UNIT_CONVERSION_FAILED": OperationBlockerCodeV1.UNIT_CONVERSION_FAILED,
        "UNIT_CONVERSION_FORBIDDEN": OperationBlockerCodeV1.UNIT_CONVERSION_FAILED,
        "DEPENDENCY_CLOSURE_FAILED": OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED,
        "DEPENDENCY_CYCLE": OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED,
        "OUTPUT_SCHEMA_MISMATCH": OperationBlockerCodeV1.OUTPUT_SCHEMA_MISMATCH,
        "FORMULA_EXECUTION_REJECTED": (
            OperationBlockerCodeV1.FORMULA_EXECUTION_REJECTED
        ),
        "OUT_OF_DOMAIN": OperationBlockerCodeV1.FORMULA_EXECUTION_REJECTED,
        "INVALID_NUMERIC_INPUT": (
            OperationBlockerCodeV1.FORMULA_EXECUTION_REJECTED
        ),
        "NONFINITE_NUMERIC_INPUT": (
            OperationBlockerCodeV1.FORMULA_EXECUTION_REJECTED
        ),
        "CAPABILITY_DENIED": OperationBlockerCodeV1.AUTHORITY_DENIED,
        "RUNTIME_EFFECT_FORBIDDEN": OperationBlockerCodeV1.RUNTIME_EFFECT_FORBIDDEN,
    }
)


class PublicFallbackBoundaryV1:
    """Translate only explicitly typed expected errors; programming errors escape."""

    @staticmethod
    def translate(exc: ComputationControlPlaneError) -> FallbackDispositionV1:
        reason = exc.reason_code.value
        suffix = reason.removeprefix("ST12A_").removeprefix("ST12B_")
        blocker = _BLOCKER_BY_REASON_SUFFIX.get(
            suffix, OperationBlockerCodeV1.INVALID_REQUEST
        )
        rejected = blocker in {
            OperationBlockerCodeV1.INVALID_REQUEST,
            OperationBlockerCodeV1.AUTHORITY_DENIED,
            OperationBlockerCodeV1.FORMULA_EXECUTION_REJECTED,
            OperationBlockerCodeV1.OUTPUT_SCHEMA_MISMATCH,
        }
        route_by_blocker = {
            OperationBlockerCodeV1.NO_APPLICABLE_STACK: "NO_RESULT_NO_TRADE",
            OperationBlockerCodeV1.INPUT_OWNER_MISSING: "OWNER_PACKET_REFRESH",
            OperationBlockerCodeV1.INPUT_OWNER_MISMATCH: "CONTEXT_REBINDING",
            OperationBlockerCodeV1.INPUT_PACKET_MISMATCH: "CONTEXT_REBINDING",
            OperationBlockerCodeV1.INPUT_SCHEMA_MISMATCH: "CONTEXT_REBINDING",
            OperationBlockerCodeV1.INPUT_SCOPE_MISMATCH: "CONTEXT_REBINDING",
            OperationBlockerCodeV1.INPUT_VALUE_CONFLICT: "CONTEXT_REBINDING",
            OperationBlockerCodeV1.POINT_IN_TIME_VIOLATION: "OWNER_PACKET_REFRESH",
            OperationBlockerCodeV1.FRESHNESS_VIOLATION: "OWNER_PACKET_REFRESH",
            OperationBlockerCodeV1.SOURCE_CONFLICT: "SOURCE_RECONCILIATION",
            OperationBlockerCodeV1.PARAMETER_OWNER_MISSING: (
                "PARAMETER_OWNER_REFRESH"
            ),
            OperationBlockerCodeV1.PARAMETER_BINDING_MISMATCH: (
                "PARAMETER_OWNER_REFRESH"
            ),
            OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED: "STACK_CLOSURE",
            OperationBlockerCodeV1.UNIT_CONVERSION_FAILED: "STACK_CLOSURE",
            OperationBlockerCodeV1.RUNTIME_EFFECT_FORBIDDEN: "NO_EFFECT_RECORD",
        }
        return FallbackDispositionV1(
            status=(
                OperationStatusV1.REJECTED
                if rejected
                else OperationStatusV1.BLOCKED
            ),
            blocker_code=blocker,
            terminal_route=route_by_blocker.get(blocker, "REJECT_TYPED_REQUEST"),
            reason_code=reason,
        )
