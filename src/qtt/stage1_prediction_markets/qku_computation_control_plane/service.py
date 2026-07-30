"""The one centralized QKUComputationControlPlaneV1 service extension."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .contextual_computability import (
    FrozenContextualComputabilityResolverV1,
)
from .errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    InputAuthorityError,
    OwnerAdapterError,
    ReasonCode,
)
from .fallback import (
    EXPECTED_PUBLIC_OPERATION_ERRORS,
    PublicFallbackBoundaryV1,
)
from .implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    invoke_formula_v34,
)
from .identity_adapter import RP5CIdentityAdapterV1
from .input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    FormulaInputResolverV1,
)
from .models import (
    CandidateProposalV1,
    CompareWithNoTradeRequestV1,
    CompareWithNoTradeResponseV1,
    ComponentResultV1,
    ComputeComponentRequestV1,
    ComputeComponentResponseV1,
    ComputeStackRequestV1,
    ComputeStackResponseV1,
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    EvaluateTradePlanRequestV1,
    EvaluateTradePlanResponseV1,
    ExplainResolutionRequestV1,
    ExplainResolutionResponseV1,
    FrozenFormulaOutputV1,
    GetSnapshotViewRequestV1,
    GetSnapshotViewResponseV1,
    IdentityResolutionV1,
    InputResolutionV1,
    MaterializationWorkOrderV1,
    NoTradeComparisonV1,
    OperationBlockerCodeV1,
    OperationRequestEnvelopeV1,
    OperationStatusV1,
    RequestMaterializationWorkOrderRequestV1,
    RequestMaterializationWorkOrderResponseV1,
    ResolveApplicableStackRequestV1,
    ResolveApplicableStackResponseV1,
    ResolveContextualComputabilityRequestV1,
    ResolveContextualComputabilityResponseV1,
    ResolveIdentityRequestV1,
    ResolveIdentityResponseV1,
    ResolveRequiredInputsRequestV1,
    ResolveRequiredInputsResponseV1,
    ResolutionExplanationV1,
    SnapshotViewV1,
    StackResolutionV1,
    StackResultV1,
    SubmitCandidateProposalRequestV1,
    SubmitCandidateProposalResponseV1,
    TradePlanEvaluationV1,
    TypedValueRecordV1,
)
from .specification import (
    FROZEN_FORMULA_REQUIREMENTS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from .stack_resolver import (
    ApplicableStackResolverV1,
    REGISTERED_FORMULA_STACKS,
)


def _assertions(record: TypedValueRecordV1) -> Mapping[str, object]:
    return MappingProxyType({field.name: field.value for field in record.fields})


def _common_response(
    request: OperationRequestEnvelopeV1,
    *,
    status: OperationStatusV1,
    blocker_codes: tuple[OperationBlockerCodeV1, ...] = (),
    receipt_refs: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "response_id": f"RESPONSE::{request.request_id}",
        "operation_name": request.operation_name,
        "request_id": request.request_id,
        "completed_at": request.requested_at,
        "status": status,
        "context": request.context,
        "warnings": (),
        "blocker_codes": blocker_codes,
        "receipt_refs": receipt_refs,
        "traceparent": request.traceparent,
        "tracestate": request.tracestate,
    }


def _result_common(
    request: OperationRequestEnvelopeV1,
    *,
    terminal_route: str,
    evidence_refs: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "result_id": f"RESULT::{request.request_id}",
        "terminal_route": terminal_route,
        "evidence_refs": evidence_refs,
    }


def _frozen_output(
    math_spec_id: str,
    value: object,
    *,
    context_id: str,
    receipt_refs: tuple[str, ...],
) -> FrozenFormulaOutputV1:
    implementation = IMPLEMENTATION_REGISTRY[math_spec_id]
    requirement = FROZEN_FORMULA_REQUIREMENTS[math_spec_id]
    schema = FROZEN_NAMED_OUTPUT_CONTRACTS[math_spec_id]
    return FrozenFormulaOutputV1(
        math_spec_id=math_spec_id,
        implementation_id=implementation.contract.implementation_id,
        mathematical_semantic_version=(
            requirement.mathematical_semantic_version
        ),
        repository_specification_version=(
            implementation.contract.specification_version
        ),
        output_schema_ref=schema.schema_id,
        output_schema_version=schema.schema_version,
        output_name=schema.output_name,
        value=value,
        context_id=context_id,
        receipt_refs=receipt_refs,
    )


def _blocked_component(
    request: ComputeComponentRequestV1,
    exc: ComputationControlPlaneError,
) -> ComputeComponentResponseV1:
    disposition = PublicFallbackBoundaryV1.translate(exc)
    result = ComponentResultV1(
        **_result_common(
            request,
            terminal_route=disposition.terminal_route,
            evidence_refs=(disposition.reason_code,),
        ),
        component_id=request.component_id,
    )
    return ComputeComponentResponseV1(
        **_common_response(
            request,
            status=disposition.status,
            blocker_codes=(disposition.blocker_code,),
            receipt_refs=(disposition.reason_code,),
        ),
        component_result=result,
    )


def _blocked_stack(
    request: ComputeStackRequestV1,
    exc: ComputationControlPlaneError,
) -> ComputeStackResponseV1:
    disposition = PublicFallbackBoundaryV1.translate(exc)
    result = StackResultV1(
        **_result_common(
            request,
            terminal_route=disposition.terminal_route,
            evidence_refs=(disposition.reason_code,),
        ),
        stack_id=request.stack_id,
    )
    return ComputeStackResponseV1(
        **_common_response(
            request,
            status=disposition.status,
            blocker_codes=(disposition.blocker_code,),
            receipt_refs=(disposition.reason_code,),
        ),
        stack_result=result,
    )


_COMPUTABILITY_TO_OPERATION_BLOCKER = MappingProxyType(
    {
        ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE: (
            OperationBlockerCodeV1.SPECIFICATION_INCOMPLETE
        ),
        ComputabilityBlockerCodeV1.IMPLEMENTATION_CALLABLE_MISSING: (
            OperationBlockerCodeV1.FIXTURE_UNAVAILABLE
        ),
        ComputabilityBlockerCodeV1.INDEPENDENT_ORACLE_MISSING: (
            OperationBlockerCodeV1.ORACLE_UNAVAILABLE
        ),
        ComputabilityBlockerCodeV1.INDEPENDENT_VECTOR_MISSING: (
            OperationBlockerCodeV1.FIXTURE_UNAVAILABLE
        ),
        ComputabilityBlockerCodeV1.INPUT_OWNER_MISSING: (
            OperationBlockerCodeV1.INPUT_OWNER_MISSING
        ),
        ComputabilityBlockerCodeV1.INPUT_OWNER_MISMATCH: (
            OperationBlockerCodeV1.INPUT_OWNER_MISMATCH
        ),
        ComputabilityBlockerCodeV1.INPUT_PACKET_MISMATCH: (
            OperationBlockerCodeV1.INPUT_PACKET_MISMATCH
        ),
        ComputabilityBlockerCodeV1.INPUT_SCHEMA_MISMATCH: (
            OperationBlockerCodeV1.INPUT_SCHEMA_MISMATCH
        ),
        ComputabilityBlockerCodeV1.INPUT_SCOPE_MISMATCH: (
            OperationBlockerCodeV1.INPUT_SCOPE_MISMATCH
        ),
        ComputabilityBlockerCodeV1.INPUT_VALUE_CONFLICT: (
            OperationBlockerCodeV1.INPUT_VALUE_CONFLICT
        ),
        ComputabilityBlockerCodeV1.POINT_IN_TIME_VIOLATION: (
            OperationBlockerCodeV1.POINT_IN_TIME_VIOLATION
        ),
        ComputabilityBlockerCodeV1.FRESHNESS_VIOLATION: (
            OperationBlockerCodeV1.FRESHNESS_VIOLATION
        ),
        ComputabilityBlockerCodeV1.SOURCE_CONFLICT: (
            OperationBlockerCodeV1.SOURCE_CONFLICT
        ),
        ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK: (
            OperationBlockerCodeV1.NO_APPLICABLE_STACK
        ),
    }
)


@dataclass(frozen=True, slots=True)
class QKUComputationControlPlaneV1:
    """One bounded service; it owns no provider, private state, LLM, or QPU."""

    owner_registry: CanonicalOwnerPacketRegistryV1
    identity_adapter: RP5CIdentityAdapterV1 | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.owner_registry, CanonicalOwnerPacketRegistryV1
        ) or (
            self.identity_adapter is not None
            and not isinstance(self.identity_adapter, RP5CIdentityAdapterV1)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "service requires canonical packet and optional RP5C owner adapters",
            )

    def resolve_identity(
        self, request: ResolveIdentityRequestV1
    ) -> ResolveIdentityResponseV1:
        fields = {field.name: field.value for field in request.identity_query.fields}
        selectors = tuple(
            name
            for name in ("math_spec_id", "component_id", "formula_id", "qku_id")
            if name in fields
        )
        identity_ref = ""
        evidence_refs: tuple[str, ...] = ()
        if len(selectors) == 1 and selectors[0] in {
            "math_spec_id",
            "component_id",
        }:
            candidate = fields[selectors[0]]
            if isinstance(candidate, str) and candidate in IMPLEMENTATION_REGISTRY:
                identity_ref = candidate
                evidence_refs = (
                    IMPLEMENTATION_REGISTRY[
                        candidate
                    ].contract.implementation_id,
                )
        elif len(selectors) == 1 and self.identity_adapter is not None:
            selector = selectors[0]
            candidate = fields[selector]
            if isinstance(candidate, str):
                try:
                    view = (
                        self.identity_adapter.get_formula(candidate)
                        if selector == "formula_id"
                        else self.identity_adapter.get_qku(candidate)
                    )
                except OwnerAdapterError:
                    pass
                else:
                    identity_ref = view.identity_row_id
                    evidence_refs = (view.identity_row_id,)
        if not identity_ref:
            blocker = OperationBlockerCodeV1.IDENTITY_UNVERIFIED
            result = IdentityResolutionV1(
                **_result_common(
                    request,
                    terminal_route="IDENTITY_OWNER_REVIEW",
                )
            )
            return ResolveIdentityResponseV1(
                **_common_response(
                    request,
                    status=OperationStatusV1.REJECTED,
                    blocker_codes=(blocker,),
                ),
                identity_resolution=result,
            )
        result = IdentityResolutionV1(
            **_result_common(
                request,
                terminal_route="RETURN_CANONICAL_IDENTITY_VIEW",
                evidence_refs=evidence_refs,
            ),
            identity_ref=identity_ref,
        )
        return ResolveIdentityResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.SUCCEEDED,
                receipt_refs=evidence_refs,
            ),
            identity_resolution=result,
        )

    def resolve_contextual_computability(
        self, request: ResolveContextualComputabilityRequestV1
    ) -> ResolveContextualComputabilityResponseV1:
        snapshot = FrozenContextualComputabilityResolverV1.resolve(
            request.component_id,
            context=request.context,
            owner_registry=self.owner_registry,
        )
        states = {
            state.state: state
            for state in (
                snapshot.resolution.specification,
                snapshot.resolution.fixture,
                snapshot.resolution.context,
                snapshot.resolution.stack,
            )
        }
        blockers = tuple(
            dict.fromkeys(
                _COMPUTABILITY_TO_OPERATION_BLOCKER.get(
                    blocker, OperationBlockerCodeV1.CONTEXT_BINDING_INVALID
                )
                for required in request.required_computability_classes
                for blocker in states[required].blocker_codes
            )
        )
        status = (
            OperationStatusV1.SUCCEEDED
            if not blockers
            else OperationStatusV1.BLOCKED
        )
        return ResolveContextualComputabilityResponseV1(
            **_common_response(
                request,
                status=status,
                blocker_codes=blockers,
                receipt_refs=(
                    snapshot.input_resolution.receipt_refs
                    if snapshot.input_resolution is not None
                    else ()
                ),
            ),
            computability=snapshot.resolution,
        )

    def resolve_applicable_stack(
        self, request: ResolveApplicableStackRequestV1
    ) -> ResolveApplicableStackResponseV1:
        component_ids = tuple(request.required_launch_roles)
        try:
            stack = ApplicableStackResolverV1.resolve(
                stack_id="STACK::MATH-01::MATH-02::V3_4",
                component_ids=component_ids,
            )
        except EXPECTED_PUBLIC_OPERATION_ERRORS as exc:
            disposition = PublicFallbackBoundaryV1.translate(exc)
            result = StackResolutionV1(
                **_result_common(
                    request,
                    terminal_route=disposition.terminal_route,
                    evidence_refs=(disposition.reason_code,),
                )
            )
            return ResolveApplicableStackResponseV1(
                **_common_response(
                    request,
                    status=disposition.status,
                    blocker_codes=(disposition.blocker_code,),
                    receipt_refs=(disposition.reason_code,),
                ),
                stack_resolution=result,
            )
        result = StackResolutionV1(
            **_result_common(
                request,
                terminal_route="EXACT_REGISTERED_STACK",
                evidence_refs=(stack.data_edge_id,),
            ),
            stack_id=stack.stack_id,
            component_ids=stack.component_ids,
            dependency_receipt_refs=(stack.data_edge_id,),
        )
        return ResolveApplicableStackResponseV1(
            **_common_response(request, status=OperationStatusV1.SUCCEEDED),
            stack_resolution=result,
        )

    def resolve_required_inputs(
        self, request: ResolveRequiredInputsRequestV1
    ) -> ResolveRequiredInputsResponseV1:
        names: list[str] = []
        packet_refs: list[str] = []
        receipt_refs: list[str] = []
        try:
            for component_id in request.component_ids:
                resolved = FormulaInputResolverV1.resolve(
                    component_id,
                    context=request.context,
                    owner_registry=self.owner_registry,
                )
                names.extend(
                    f"{component_id}.{row.input_name}" for row in resolved.inputs
                )
                packet_refs.extend(resolved.packet_refs)
                receipt_refs.extend(resolved.receipt_refs)
        except EXPECTED_PUBLIC_OPERATION_ERRORS as exc:
            disposition = PublicFallbackBoundaryV1.translate(exc)
            result = InputResolutionV1(
                **_result_common(
                    request,
                    terminal_route=disposition.terminal_route,
                    evidence_refs=(disposition.reason_code,),
                ),
                component_ids=request.component_ids,
            )
            return ResolveRequiredInputsResponseV1(
                **_common_response(
                    request,
                    status=disposition.status,
                    blocker_codes=(disposition.blocker_code,),
                    receipt_refs=(disposition.reason_code,),
                ),
                input_resolution=result,
            )
        result = InputResolutionV1(
            **_result_common(
                request,
                terminal_route="EXACT_OWNER_INPUTS_RESOLVED",
                evidence_refs=tuple(dict.fromkeys(receipt_refs)),
            ),
            component_ids=request.component_ids,
            resolved_input_names=tuple(names),
            owner_packet_refs=tuple(dict.fromkeys(packet_refs)),
        )
        return ResolveRequiredInputsResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.SUCCEEDED,
                receipt_refs=tuple(dict.fromkeys(receipt_refs)),
            ),
            input_resolution=result,
        )

    def compute_component(
        self, request: ComputeComponentRequestV1
    ) -> ComputeComponentResponseV1:
        try:
            if request.component_id not in IMPLEMENTATION_REGISTRY:
                raise ContractValidationError(
                    ReasonCode.UNKNOWN_IMPLEMENTATION,
                    f"unknown registered component: {request.component_id}",
                )
            schema = FROZEN_NAMED_OUTPUT_CONTRACTS[request.component_id]
            if request.expected_output_schema_ref != schema.schema_id:
                raise ContractValidationError(
                    ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                    "requested output schema differs from the frozen formula schema",
                )
            resolved = FormulaInputResolverV1.resolve(
                request.component_id,
                context=request.context,
                owner_registry=self.owner_registry,
                caller_assertions=_assertions(request.input_values),
            )
            value = invoke_formula_v34(
                request.component_id, resolved.authoritative_values
            )
            output = _frozen_output(
                request.component_id,
                value,
                context_id=request.context.context_id,
                receipt_refs=resolved.receipt_refs,
            )
        except EXPECTED_PUBLIC_OPERATION_ERRORS as exc:
            return _blocked_component(request, exc)
        result = ComponentResultV1(
            **_result_common(
                request,
                terminal_route="DETERMINISTIC_COMPONENT_RESULT",
                evidence_refs=resolved.receipt_refs,
            ),
            component_id=request.component_id,
            formula_output=output,
        )
        return ComputeComponentResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.SUCCEEDED,
                receipt_refs=resolved.receipt_refs,
            ),
            component_result=result,
        )

    def compute_stack(
        self, request: ComputeStackRequestV1
    ) -> ComputeStackResponseV1:
        assertions = _assertions(request.input_values)
        assertions_by_math: dict[str, dict[str, object]] = {
            component_id: {} for component_id in request.component_ids
        }
        for name, value in assertions.items():
            if "." not in name:
                return _blocked_stack(
                    request,
                    ContractValidationError(
                        ReasonCode.INVALID_CONTRACT,
                        "stack assertions must use MATH-ID.input_name keys",
                    ),
                )
            component_id, input_name = name.split(".", 1)
            if component_id not in assertions_by_math:
                return _blocked_stack(
                    request,
                    ContractValidationError(
                        ReasonCode.INVALID_CONTRACT,
                        f"stack assertion names unknown component {component_id}",
                    ),
                )
            assertions_by_math[component_id][input_name] = value
        try:
            execution = ApplicableStackResolverV1.execute(
                stack_id=request.stack_id,
                component_ids=request.component_ids,
                context=request.context,
                owner_registry=self.owner_registry,
                caller_assertions_by_math_id=MappingProxyType(
                    {
                        key: MappingProxyType(value)
                        for key, value in assertions_by_math.items()
                    }
                ),
            )
            outputs = tuple(
                _frozen_output(
                    component_id,
                    value,
                    context_id=request.context.context_id,
                    receipt_refs=resolution.receipt_refs,
                )
                for component_id, value, resolution in zip(
                    request.component_ids,
                    execution.component_outputs,
                    execution.component_inputs,
                    strict=True,
                )
            )
        except EXPECTED_PUBLIC_OPERATION_ERRORS as exc:
            return _blocked_stack(request, exc)
        result = StackResultV1(
            **_result_common(
                request,
                terminal_route="DETERMINISTIC_DEPENDENCY_CLOSED_STACK_RESULT",
                evidence_refs=execution.receipt_refs,
            ),
            stack_id=request.stack_id,
            component_outputs=outputs,
            conversion_receipt_refs=(
                execution.conversion_receipt.receipt_id,
                execution.propagation_receipt.receipt_id,
            ),
        )
        return ComputeStackResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.SUCCEEDED,
                receipt_refs=execution.receipt_refs,
            ),
            stack_result=result,
        )

    def compare_with_no_trade(
        self, request: CompareWithNoTradeRequestV1
    ) -> CompareWithNoTradeResponseV1:
        result = NoTradeComparisonV1(
            **_result_common(
                request,
                terminal_route="PRETRADE1_NO_TRADE_COMPARATOR_REQUIRED",
            ),
            comparison_basis=request.comparison_basis,
            downstream_blocker_ref="PRETRADE1::NO_TRADE_COMPARISON",
        )
        return CompareWithNoTradeResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.BLOCKED,
                blocker_codes=(OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED,),
            ),
            comparison=result,
        )

    def evaluate_trade_plan(
        self, request: EvaluateTradePlanRequestV1
    ) -> EvaluateTradePlanResponseV1:
        result = TradePlanEvaluationV1(
            **_result_common(
                request,
                terminal_route="PRETRADE1_EVALUATION_REQUIRED",
            ),
            downstream_blocker_ref=(
                f"PRETRADE1::{request.trade_plan_candidate_id}"
            ),
        )
        return EvaluateTradePlanResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.BLOCKED,
                blocker_codes=(OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED,),
            ),
            evaluation=result,
        )

    def get_snapshot_view(
        self, request: GetSnapshotViewRequestV1
    ) -> GetSnapshotViewResponseV1:
        try:
            packet = self.owner_registry.packet_by_id(request.snapshot_id)
        except InputAuthorityError as exc:
            disposition = PublicFallbackBoundaryV1.translate(exc)
            result = SnapshotViewV1(
                **_result_common(
                    request, terminal_route=disposition.terminal_route
                ),
                snapshot_id=request.snapshot_id,
                view_class=request.view_class,
            )
            return GetSnapshotViewResponseV1(
                **_common_response(
                    request,
                    status=disposition.status,
                    blocker_codes=(disposition.blocker_code,),
                ),
                snapshot_view=result,
            )
        result = SnapshotViewV1(
            **_result_common(
                request,
                terminal_route="READ_ONLY_OWNER_PACKET_VIEW",
                evidence_refs=(packet.producer_receipt_id,),
            ),
            snapshot_id=packet.packet_id,
            view_class=request.view_class,
        )
        return GetSnapshotViewResponseV1(
            **_common_response(
                request,
                status=OperationStatusV1.SUCCEEDED,
                receipt_refs=(packet.producer_receipt_id,),
            ),
            snapshot_view=result,
        )

    def explain_resolution(
        self, request: ExplainResolutionRequestV1
    ) -> ExplainResolutionResponseV1:
        result = ResolutionExplanationV1(
            **_result_common(
                request,
                terminal_route="READ_ONLY_RESOLUTION_RECEIPT_PROJECTION",
                evidence_refs=(request.resolution_receipt_id,),
            ),
            next_safe_route="FOLLOW_TYPED_RECEIPT_TERMINAL_ROUTE",
        )
        return ExplainResolutionResponseV1(
            **_common_response(request, status=OperationStatusV1.SUCCEEDED),
            explanation=result,
        )

    def submit_candidate_proposal(
        self, request: SubmitCandidateProposalRequestV1
    ) -> SubmitCandidateProposalResponseV1:
        result = CandidateProposalV1(
            **_result_common(
                request,
                terminal_route="OWNER_REVIEW_QUEUE_NO_EFFECT_RECORD",
                evidence_refs=request.source_candidate_refs,
            ),
            candidate_id=f"CANDIDATE::{request.request_id}",
        )
        return SubmitCandidateProposalResponseV1(
            **_common_response(request, status=OperationStatusV1.SUCCEEDED),
            proposal=result,
        )

    def request_materialization_work_order(
        self, request: RequestMaterializationWorkOrderRequestV1
    ) -> RequestMaterializationWorkOrderResponseV1:
        result = MaterializationWorkOrderV1(
            **_result_common(
                request,
                terminal_route="OWNER_WORK_QUEUE_NO_EFFECT_RECORD",
                evidence_refs=request.missing_contract_ids,
            ),
            work_order_id=f"WORK_ORDER::{request.request_id}",
            requested_owner=request.requested_owner,
        )
        return RequestMaterializationWorkOrderResponseV1(
            **_common_response(request, status=OperationStatusV1.SUCCEEDED),
            work_order=result,
        )

if len(REGISTERED_FORMULA_STACKS) != 1 or len(IMPLEMENTATION_REGISTRY) != 30:
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "central service requires exactly 30 components and one registered stack",
    )
