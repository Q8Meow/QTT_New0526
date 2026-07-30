"""Orthogonal specification, fixture, context, and stack computability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .context import ComputationContextKeyV1
from .errors import (
    FreshnessError,
    InputAuthorityError,
    PointInTimeError,
    ReasonCode,
)
from .implementation_registry import IMPLEMENTATION_REGISTRY
from .input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    FormulaInputResolutionV1,
    FormulaInputResolverV1,
)
from .models import (
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    ComputabilityStateResultV1,
    ComputabilityTerminalRouteV1,
    ContextualComputabilityResolutionV1,
)
from .oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
    ORACLE_BY_MATH_ID,
)
from .specification import (
    FROZEN_FORMULA_INPUT_CONTRACTS,
    FROZEN_FORMULA_REQUIREMENTS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from .stack_resolver import REGISTERED_FORMULA_STACKS


@dataclass(frozen=True, slots=True)
class ContextualComputabilitySnapshotV1:
    math_spec_id: str
    context_id: str
    resolution: ContextualComputabilityResolutionV1
    input_resolution: FormulaInputResolutionV1 | None
    registered_stack_id: str | None
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            not self.math_spec_id
            or not self.context_id
            or not isinstance(
                self.resolution, ContextualComputabilityResolutionV1
            )
            or self.no_authority_flag is not True
        ):
            raise InputAuthorityError(
                ReasonCode.INVALID_CONTRACT,
                "contextual computability snapshot is malformed",
            )


def _state(
    state: ComputabilityClassV1,
    blockers: tuple[ComputabilityBlockerCodeV1, ...],
    *,
    receipts: tuple[str, ...] = (),
    oracle_receipts: tuple[str, ...] = (),
    route: ComputabilityTerminalRouteV1,
) -> ComputabilityStateResultV1:
    return ComputabilityStateResultV1(
        state=state,
        computable=not blockers,
        blocker_codes=blockers,
        dependency_receipt_refs=receipts,
        oracle_receipt_refs=oracle_receipts,
        terminal_route=route,
    )


def _context_blocker(
    exc: InputAuthorityError | PointInTimeError | FreshnessError,
) -> tuple[ComputabilityBlockerCodeV1, ComputabilityTerminalRouteV1]:
    code = exc.reason_code.value
    if code.endswith("INPUT_OWNER_MISSING"):
        return (
            ComputabilityBlockerCodeV1.INPUT_OWNER_MISSING,
            ComputabilityTerminalRouteV1.OWNER_PACKET_REFRESH,
        )
    if code.endswith("INPUT_OWNER_MISMATCH"):
        return (
            ComputabilityBlockerCodeV1.INPUT_OWNER_MISMATCH,
            ComputabilityTerminalRouteV1.CONTEXT_REBINDING,
        )
    if code.endswith("INPUT_PACKET_MISMATCH"):
        return (
            ComputabilityBlockerCodeV1.INPUT_PACKET_MISMATCH,
            ComputabilityTerminalRouteV1.CONTEXT_REBINDING,
        )
    if code.endswith("INPUT_SCHEMA_MISMATCH"):
        return (
            ComputabilityBlockerCodeV1.INPUT_SCHEMA_MISMATCH,
            ComputabilityTerminalRouteV1.CONTEXT_REBINDING,
        )
    if code.endswith("INPUT_SCOPE_MISMATCH"):
        return (
            ComputabilityBlockerCodeV1.INPUT_SCOPE_MISMATCH,
            ComputabilityTerminalRouteV1.CONTEXT_REBINDING,
        )
    if code.endswith("SOURCE_CONFLICT"):
        return (
            ComputabilityBlockerCodeV1.SOURCE_CONFLICT,
            ComputabilityTerminalRouteV1.SOURCE_RECONCILIATION,
        )
    if code.endswith("POINT_IN_TIME_VIOLATION"):
        return (
            ComputabilityBlockerCodeV1.POINT_IN_TIME_VIOLATION,
            ComputabilityTerminalRouteV1.OWNER_PACKET_REFRESH,
        )
    if code.endswith("FRESHNESS_VIOLATION") or code.endswith(
        "SOURCE_EPOCH_STALE"
    ):
        return (
            ComputabilityBlockerCodeV1.FRESHNESS_VIOLATION,
            ComputabilityTerminalRouteV1.OWNER_PACKET_REFRESH,
        )
    return (
        ComputabilityBlockerCodeV1.INPUT_VALUE_CONFLICT,
        ComputabilityTerminalRouteV1.CONTEXT_REBINDING,
    )


class FrozenContextualComputabilityResolverV1:
    """Resolve each state independently and preserve research completeness."""

    @staticmethod
    def resolve(
        math_spec_id: str,
        *,
        context: ComputationContextKeyV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertions: Mapping[str, object] | None = None,
        required_stack_id: str | None = None,
    ) -> ContextualComputabilitySnapshotV1:
        specification_closed = (
            math_spec_id in FROZEN_FORMULA_REQUIREMENTS
            and math_spec_id in FROZEN_FORMULA_INPUT_CONTRACTS
            and math_spec_id in FROZEN_NAMED_OUTPUT_CONTRACTS
        )
        specification_blockers = (
            ()
            if specification_closed
            else (
                ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE,
            )
        )
        fixture_closed = (
            math_spec_id in IMPLEMENTATION_REGISTRY
            and math_spec_id in ORACLE_BY_MATH_ID
            and math_spec_id in GOLDEN_VECTOR_BY_MATH_ID
        )
        fixture_blockers = (
            ()
            if fixture_closed
            else (
                ComputabilityBlockerCodeV1.IMPLEMENTATION_CALLABLE_MISSING,
            )
        )

        input_resolution: FormulaInputResolutionV1 | None = None
        context_blockers: tuple[ComputabilityBlockerCodeV1, ...] = ()
        context_route = ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
        if specification_closed:
            try:
                input_resolution = FormulaInputResolverV1.resolve(
                    math_spec_id,
                    context=context,
                    owner_registry=owner_registry,
                    caller_assertions=caller_assertions,
                )
            except (InputAuthorityError, PointInTimeError, FreshnessError) as exc:
                blocker, context_route = _context_blocker(exc)
                context_blockers = (blocker,)
        else:
            context_blockers = (
                ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE,
            )
            context_route = ComputabilityTerminalRouteV1.SPECIFICATION_OWNER_REVIEW

        registered_stack_id: str | None = None
        stack_blockers = context_blockers
        stack_route = context_route
        if not stack_blockers and required_stack_id is not None:
            stack = REGISTERED_FORMULA_STACKS.get(required_stack_id)
            if stack is None or math_spec_id not in stack.component_ids:
                stack_blockers = (
                    ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK,
                )
                stack_route = ComputabilityTerminalRouteV1.NO_RESULT_NO_TRADE
            else:
                registered_stack_id = stack.stack_id
                stack_route = ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION

        resolution = ContextualComputabilityResolutionV1(
            specification=_state(
                ComputabilityClassV1.SPECIFICATION_COMPUTABLE,
                specification_blockers,
                route=(
                    ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
                    if not specification_blockers
                    else ComputabilityTerminalRouteV1.SPECIFICATION_OWNER_REVIEW
                ),
            ),
            fixture=_state(
                ComputabilityClassV1.FIXTURE_COMPUTABLE,
                fixture_blockers,
                oracle_receipts=(
                    (f"ORACLE::{math_spec_id}::V3_4",)
                    if not fixture_blockers
                    else ()
                ),
                route=(
                    ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
                    if not fixture_blockers
                    else ComputabilityTerminalRouteV1.FIXTURE_MATERIALIZATION
                ),
            ),
            context=_state(
                ComputabilityClassV1.CONTEXT_COMPUTABLE,
                context_blockers,
                receipts=(
                    input_resolution.receipt_refs
                    if input_resolution is not None
                    else ()
                ),
                route=context_route,
            ),
            stack=_state(
                ComputabilityClassV1.STACK_COMPUTABLE,
                stack_blockers,
                receipts=(
                    input_resolution.receipt_refs
                    if input_resolution is not None and not stack_blockers
                    else ()
                ),
                route=stack_route,
            ),
        )
        return ContextualComputabilitySnapshotV1(
            math_spec_id=math_spec_id,
            context_id=context.context_id,
            resolution=resolution,
            input_resolution=input_resolution,
            registered_stack_id=registered_stack_id,
        )
