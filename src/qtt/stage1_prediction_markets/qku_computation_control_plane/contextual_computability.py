"""Orthogonal specification, fixture, context, and stack computability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .errors import (
    ComputationControlPlaneError,
    FreshnessError,
    InputAuthorityError,
    PointInTimeError,
    ReasonCode,
    StackResolutionError,
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
    ComputationExecutionContextV1,
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
from .stack_resolver import (
    REGISTERED_FORMULA_STACKS,
    _SelectedStackContextClosureV1,
    _preflight_registered_stack_context_closure,
)


@dataclass(frozen=True, slots=True)
class ContextualComputabilitySnapshotV1:
    math_spec_id: str
    execution_context: ComputationExecutionContextV1
    resolution: ContextualComputabilityResolutionV1
    input_resolution: FormulaInputResolutionV1 | None
    registered_stack_id: str | None
    stack_closure: _SelectedStackContextClosureV1 | None = None
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            not self.math_spec_id
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or not isinstance(
                self.resolution, ContextualComputabilityResolutionV1
            )
            or (
                self.input_resolution is not None
                and self.input_resolution.execution_context
                is not self.execution_context
            )
            or (
                self.stack_closure is not None
                and (
                    self.stack_closure.execution_context
                    is not self.execution_context
                    or self.stack_closure.no_authority_flag is not True
                )
            )
            or self.no_authority_flag is not True
        ):
            raise InputAuthorityError(
                ReasonCode.INVALID_CONTRACT,
                "contextual computability snapshot is malformed",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id

    @property
    def receipt_refs(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    *(
                        self.input_resolution.receipt_refs
                        if self.input_resolution is not None
                        else ()
                    ),
                    *(
                        self.stack_closure.receipt_refs
                        if self.stack_closure is not None
                        else ()
                    ),
                )
            )
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
    failure: ReasonCode | ComputationControlPlaneError,
) -> tuple[ComputabilityBlockerCodeV1, ComputabilityTerminalRouteV1]:
    reason_code = (
        failure
        if isinstance(failure, ReasonCode)
        else failure.reason_code
    )
    code = reason_code.value
    if reason_code is ReasonCode.NO_APPLICABLE_STACK:
        return (
            ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK,
            ComputabilityTerminalRouteV1.NO_RESULT_NO_TRADE,
        )
    if reason_code is ReasonCode.DEPENDENCY_CLOSURE_FAILED:
        return (
            ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE,
            ComputabilityTerminalRouteV1.STACK_CLOSURE,
        )
    if reason_code is ReasonCode.UNKNOWN_IMPLEMENTATION:
        return (
            ComputabilityBlockerCodeV1.IMPLEMENTATION_CALLABLE_MISSING,
            ComputabilityTerminalRouteV1.FIXTURE_MATERIALIZATION,
        )
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
        context: ComputationExecutionContextV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertions: Mapping[str, object] | None = None,
        required_stack_id: str | None = None,
        context_admission_blocker: ComputabilityBlockerCodeV1 | None = None,
        stack_admission_blocker: ComputabilityBlockerCodeV1 | None = None,
    ) -> ContextualComputabilitySnapshotV1:
        if not isinstance(context, ComputationExecutionContextV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "contextual computability requires the execution-context subtype",
            )
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

        stack_closure: _SelectedStackContextClosureV1 | None = None
        stack_preflight_failure: ReasonCode | None = None
        if (
            required_stack_id is not None
            and context_admission_blocker is None
            and stack_admission_blocker is None
        ):
            selected_stack = REGISTERED_FORMULA_STACKS.get(required_stack_id)
            if selected_stack is None:
                stack_preflight_failure = ReasonCode.NO_APPLICABLE_STACK
            else:
                try:
                    stack_closure = (
                        _preflight_registered_stack_context_closure(
                            stack_id=required_stack_id,
                            stack_version=(
                                context.dependency_graph_version or ""
                            ),
                            component_ids=selected_stack.component_ids,
                            context=context,
                            owner_registry=owner_registry,
                        )
                    )
                except StackResolutionError as exc:
                    stack_preflight_failure = exc.reason_code

        component_closure = (
            stack_closure.component_for(math_spec_id)
            if stack_closure is not None
            else None
        )
        input_resolution: FormulaInputResolutionV1 | None = None
        context_receipts: tuple[str, ...] = ()
        context_blockers: tuple[ComputabilityBlockerCodeV1, ...] = (
            (context_admission_blocker,)
            if context_admission_blocker is not None
            else ()
        )
        context_route = ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
        if specification_closed and not context_blockers:
            if component_closure is not None:
                context_receipts = component_closure.receipt_refs
                if component_closure.blocker_reasons:
                    dispositions = tuple(
                        _context_blocker(reason)
                        for reason in component_closure.blocker_reasons
                    )
                    context_blockers = tuple(
                        dict.fromkeys(
                            blocker for blocker, _route in dispositions
                        )
                    )
                    context_route = dispositions[0][1]
                elif not component_closure.dependency_producible_input_refs:
                    try:
                        input_resolution = FormulaInputResolverV1.resolve(
                            math_spec_id,
                            context=context,
                            owner_registry=owner_registry,
                            caller_assertions=caller_assertions,
                        )
                        context_receipts = input_resolution.receipt_refs
                    except (
                        InputAuthorityError,
                        PointInTimeError,
                        FreshnessError,
                    ) as exc:
                        blocker, context_route = _context_blocker(exc)
                        context_blockers = (blocker,)
            else:
                try:
                    input_resolution = FormulaInputResolverV1.resolve(
                        math_spec_id,
                        context=context,
                        owner_registry=owner_registry,
                        caller_assertions=caller_assertions,
                    )
                    context_receipts = input_resolution.receipt_refs
                except (
                    InputAuthorityError,
                    PointInTimeError,
                    FreshnessError,
                ) as exc:
                    blocker, context_route = _context_blocker(exc)
                    context_blockers = (blocker,)
        elif not specification_closed:
            context_blockers = (
                ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE,
            )
            context_route = (
                ComputabilityTerminalRouteV1.SPECIFICATION_OWNER_REVIEW
            )
        else:
            context_route = ComputabilityTerminalRouteV1.CONTEXT_REBINDING

        registered_stack_id: str | None = None
        stack_receipts = (
            stack_closure.receipt_refs
            if stack_closure is not None
            else ()
        )
        stack_blockers: tuple[ComputabilityBlockerCodeV1, ...] = ()
        stack_route = ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
        if stack_admission_blocker is not None:
            stack_blockers = (stack_admission_blocker,)
            stack_route = (
                ComputabilityTerminalRouteV1.NO_RESULT_NO_TRADE
                if stack_admission_blocker
                is ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK
                else ComputabilityTerminalRouteV1.STACK_CLOSURE
            )
        elif required_stack_id is None:
            stack_blockers = (ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK,)
            stack_route = ComputabilityTerminalRouteV1.NO_RESULT_NO_TRADE
        elif stack_preflight_failure is not None:
            blocker, stack_route = _context_blocker(
                stack_preflight_failure
            )
            stack_blockers = (blocker,)
        elif stack_closure is None:
            stack_blockers = (
                context_blockers
                if context_blockers
                else (ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK,)
            )
            stack_route = (
                context_route
                if context_blockers
                else ComputabilityTerminalRouteV1.NO_RESULT_NO_TRADE
            )
        elif component_closure is None:
            stack_blockers = (ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK,)
            stack_route = ComputabilityTerminalRouteV1.NO_RESULT_NO_TRADE
        elif stack_closure.full_stack_blocker_reasons:
            dispositions = tuple(
                _context_blocker(reason)
                for reason in stack_closure.full_stack_blocker_reasons
            )
            stack_blockers = tuple(
                dict.fromkeys(blocker for blocker, _route in dispositions)
            )
            stack_route = dispositions[0][1]
        else:
            registered_stack_id = stack_closure.stack_id
            stack_route = (
                ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
            )

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
                receipts=context_receipts,
                route=context_route,
            ),
            stack=_state(
                ComputabilityClassV1.STACK_COMPUTABLE,
                stack_blockers,
                receipts=stack_receipts,
                route=stack_route,
            ),
        )
        return ContextualComputabilitySnapshotV1(
            math_spec_id=math_spec_id,
            execution_context=context,
            resolution=resolution,
            input_resolution=input_resolution,
            registered_stack_id=registered_stack_id,
            stack_closure=stack_closure,
        )
