"""The one centralized QKUComputationControlPlaneV1 service extension."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping

from .contextual_computability import (
    FrozenContextualComputabilityResolverV1,
)
from .errors import (
    AuthorityDeniedError,
    ComputationControlPlaneError,
    ContractValidationError,
    InputAuthorityError,
    NoTradeReoptimizationRouteError,
    OwnerAdapterError,
    ParameterPolicyError,
    ReasonCode,
    StackResolutionError,
)
from .agent_policy import (
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
    POLICY_VERSION,
)
from .fallback import (
    EXPECTED_PUBLIC_OPERATION_ERRORS,
    PublicFallbackBoundaryV1,
)
from .implementation_registry import (
    CURRENT_IMPLEMENTATION_REGISTRY,
    IMPLEMENTATION_REGISTRY,
    invoke_current_formula,
    invoke_formula_v34,
)
from .latency_policy import (
    ResourceUsageV1,
    build_latency_measurement,
    evaluate_latency_profile,
    local_duration_now_ns,
    validate_resource_bounds,
)
from .mode_snapshot_policy import (
    MODE_SNAPSHOT_CANDIDATE_KIND,
    ModeSnapshotCandidateInputsV1,
    evaluate_mode_snapshot_candidate,
    pre_f_unavailable_reference,
    validate_current_kill_submit_state,
)
from .identity_adapter import RP5CIdentityAdapterV1
from .persistence import PersistenceAdapterV1
from .receipts import materialize_mode_snapshot_control_receipts
from .protocols import (
    AgentCapabilityAdmissionProtocolV1,
    ModeSnapshotCandidateInputProtocolV1,
    ModeSnapshotOwnerProjectionProtocolV1,
    OwnerProjectionViewV1,
)
from .input_resolver import (
    CanonicalOwnerPacketRegistryV1,
    CurrentModeSnapshotInputResolverV1,
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
    ComputationExecutionContextV1,
    EvaluateTradePlanRequestV1,
    EvaluateTradePlanResponseV1,
    ExplainResolutionRequestV1,
    ExplainResolutionResponseV1,
    FrozenFormulaOutputV1,
    GetSnapshotViewRequestV1,
    GetSnapshotViewResponseV1,
    IdentityResolutionV1,
    InputResolutionV1,
    ImplementationVersionPinV1,
    MaterializationWorkOrderV1,
    LatencyBudgetProfileV1,
    LatencyMeasurementLabelsV1,
    LatencyMeasurementV1,
    ModeSnapshotCandidateProposalResultV1,
    NoTradeComparisonV1,
    OperationBlockerCodeV1,
    OperationRequestEnvelopeV1,
    OperationStatusV1,
    RequestMaterializationWorkOrderRequestV1,
    RequestMaterializationWorkOrderResponseV1,
    ResourceBoundsProfileV1,
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
    ST12FEvidenceStateV1,
    StackResolutionV1,
    StackResultV1,
    SubmitCandidateProposalRequestV1,
    SubmitCandidateProposalResponseV1,
    TradePlanEvaluationV1,
    TypedValueRecordV1,
)
from .specification import (
    CURRENT_FORMULA_REQUIREMENTS,
    CURRENT_NAMED_OUTPUT_CONTRACTS,
    FROZEN_FORMULA_REQUIREMENTS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from .stack_resolver import (
    ApplicableStackResolverV1,
    REGISTERED_FORMULA_STACKS,
)


def _assertions(record: TypedValueRecordV1) -> Mapping[str, object]:
    return MappingProxyType({field.name: field.value for field in record.fields})


_D_PROPOSAL_FIELDS = (
    "candidate_contract_id",
    "computation_bundle_ref",
    "context_ref",
    "formula_spec_refs",
    "implementation_version_pins",
    "binding_profile_ref",
    "parameter_policy_snapshot_ref",
    "parameter_value_refs",
    "source_epoch_refs",
    "receipt_lineage_refs",
    "readiness_state_ref",
    "pretrade_state_ref",
    "owner_action_policy_ref",
    "current_mode",
    "requested_mode",
    "expected_owner_state_ref",
    "candidate_version",
)


def _d_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{field_name} must be canonical comma-delimited text",
        )
    values = tuple(value.split(","))
    if (
        any(not item or item != item.strip() for item in values)
        or len(values) != len(set(values))
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{field_name} must contain unique canonical identities",
        )
    return values


def _validate_d_proposed_specification(
    request: SubmitCandidateProposalRequestV1,
    inputs: ModeSnapshotCandidateInputsV1,
) -> None:
    fields = _assertions(request.proposed_specification)
    if tuple(fields) != _D_PROPOSAL_FIELDS or set(fields) != set(_D_PROPOSAL_FIELDS):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "D proposal must contain exactly the frozen typed field roster",
        )
    if any(not isinstance(value, str) for value in fields.values()):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "D proposal fields must be typed canonical text references",
        )
    if fields["candidate_contract_id"] != MODE_SNAPSHOT_CANDIDATE_KIND:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "candidate contract identity does not match the allowlisted D kind",
        )
    pin_tokens = _d_text_tuple(
        fields["implementation_version_pins"],
        "implementation_version_pins",
    )
    try:
        proposed_pins = tuple(
            ImplementationVersionPinV1(*token.split("=", 1))
            for token in pin_tokens
            if token.count("=") == 1
        )
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(
            ReasonCode.PARAMETER_POLICY_OR_PIN_INVALID,
            "implementation pins must use exact math_spec_id=implementation_id text",
        ) from exc
    comparisons = (
        (fields["computation_bundle_ref"], inputs.computation_bundle_ref),
        (fields["context_ref"], inputs.context_ref),
        (_d_text_tuple(fields["formula_spec_refs"], "formula_spec_refs"), inputs.formula_spec_refs),
        (proposed_pins, inputs.implementation_version_pins),
        (fields["binding_profile_ref"], inputs.binding_profile_ref),
        (fields["parameter_policy_snapshot_ref"], inputs.parameter_policy_snapshot_ref),
        (_d_text_tuple(fields["parameter_value_refs"], "parameter_value_refs"), inputs.parameter_value_refs),
        (_d_text_tuple(fields["source_epoch_refs"], "source_epoch_refs"), inputs.source_epoch_refs),
        (_d_text_tuple(fields["receipt_lineage_refs"], "receipt_lineage_refs"), inputs.receipt_lineage_refs),
        (fields["readiness_state_ref"], inputs.readiness_state_ref),
        (fields["pretrade_state_ref"], inputs.pretrade_state_ref),
        (fields["owner_action_policy_ref"], inputs.owner_action_policy_ref),
        (fields["current_mode"], inputs.current_mode),
        (fields["requested_mode"], inputs.requested_mode),
        (fields["expected_owner_state_ref"], inputs.expected_owner_state_ref),
        (fields["candidate_version"], inputs.candidate_version),
    )
    if len(proposed_pins) != len(pin_tokens) or any(
        proposed != resolved for proposed, resolved in comparisons
    ):
        raise ContractValidationError(
            ReasonCode.SNAPSHOT_PIN_CONFLICT,
            "caller proposal differs from exact current-owner resolved pins",
        )


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
    execution_context: ComputationExecutionContextV1,
    receipt_refs: tuple[str, ...],
) -> FrozenFormulaOutputV1:
    implementation = CURRENT_IMPLEMENTATION_REGISTRY[math_spec_id]
    requirement = CURRENT_FORMULA_REQUIREMENTS[math_spec_id]
    schema = CURRENT_NAMED_OUTPUT_CONTRACTS[math_spec_id]
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
        execution_context=execution_context,
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
        ComputabilityBlockerCodeV1.CONTEXT_BINDING_MISMATCH: (
            OperationBlockerCodeV1.CONTEXT_BINDING_INVALID
        ),
        ComputabilityBlockerCodeV1.PARAMETER_BINDING_MISMATCH: (
            OperationBlockerCodeV1.PARAMETER_BINDING_MISMATCH
        ),
        ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE: (
            OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED
        ),
    }
)


ST12B_FROZEN_PACKAGE_VERSION = "3.4"


def _contextual_admission_blockers(
    exc: ComputationControlPlaneError,
) -> tuple[
    ComputabilityBlockerCodeV1 | None,
    ComputabilityBlockerCodeV1 | None,
]:
    if exc.reason_code is ReasonCode.NO_APPLICABLE_STACK:
        return None, ComputabilityBlockerCodeV1.NO_APPLICABLE_STACK
    if exc.reason_code is ReasonCode.PARAMETER_BINDING_MISMATCH:
        return ComputabilityBlockerCodeV1.PARAMETER_BINDING_MISMATCH, None
    if exc.reason_code is ReasonCode.DEPENDENCY_CLOSURE_FAILED:
        return ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE, None
    return ComputabilityBlockerCodeV1.CONTEXT_BINDING_MISMATCH, None


def _admit_computation_plan(
    *,
    execution_context: ComputationExecutionContextV1,
    ordered_component_ids: tuple[str, ...],
    selected_stack_id: str | None,
) -> None:
    """The service's sole typed admission path for an exact computation plan."""

    if not isinstance(execution_context, ComputationExecutionContextV1):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            "computation admission requires the execution-context subtype",
        )
    if (
        not isinstance(ordered_component_ids, tuple)
        or not ordered_component_ids
        or any(
            not isinstance(component_id, str) or not component_id
            for component_id in ordered_component_ids
        )
        or len(set(ordered_component_ids)) != len(ordered_component_ids)
    ):
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "computation admission requires an ordered unique component tuple",
        )
    unknown = tuple(
        component_id
        for component_id in ordered_component_ids
        if component_id not in CURRENT_IMPLEMENTATION_REGISTRY
    )
    if unknown:
        raise ContractValidationError(
            ReasonCode.UNKNOWN_IMPLEMENTATION,
            f"unknown registered components: {unknown}",
        )
    if (
        execution_context.binding_profile_version
        != ST12B_FROZEN_PACKAGE_VERSION
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            "binding profile version differs from frozen package 3.4",
        )
    if (
        execution_context.parameter_policy_version
        != ST12B_FROZEN_PACKAGE_VERSION
    ):
        raise ParameterPolicyError(
            ReasonCode.PARAMETER_BINDING_MISMATCH,
            "parameter policy version differs from frozen package 3.4",
        )
    if selected_stack_id is None:
        if (
            execution_context.dependency_graph_id is not None
            or execution_context.dependency_graph_version is not None
        ):
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                "a standalone plan cannot carry a dependency graph",
            )
    else:
        if execution_context.dependency_graph_id != selected_stack_id:
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                "selected stack differs from the execution-context graph",
            )
        try:
            stack = REGISTERED_FORMULA_STACKS[selected_stack_id]
        except KeyError as exc:
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                f"no registered stack exists for {selected_stack_id}",
            ) from exc
        if (
            execution_context.dependency_graph_version != stack.stack_version
            or ordered_component_ids != stack.component_ids
        ):
            raise StackResolutionError(
                ReasonCode.NO_APPLICABLE_STACK,
                "stack version or ordered component membership differs",
            )
    expected_pins = tuple(
        ImplementationVersionPinV1(
            math_spec_id=component_id,
            implementation_id=CURRENT_IMPLEMENTATION_REGISTRY[
                component_id
            ].contract.implementation_id,
        )
        for component_id in ordered_component_ids
    )
    if execution_context.implementation_versions != expected_pins:
        raise StackResolutionError(
            ReasonCode.DEPENDENCY_CLOSURE_FAILED,
            "implementation pins do not exactly match the operation plan",
        )


def _admit_agent_request(
    service: "QKUComputationControlPlaneV1",
    request: OperationRequestEnvelopeV1,
) -> AgentCapabilityDecisionV1:
    """The single mandatory fail-closed admission path for all public methods."""

    resolver = service.agent_capability_resolver
    if not isinstance(resolver, AgentCapabilityAdmissionProtocolV1):
        raise AuthorityDeniedError(
            ReasonCode.TASK_ENVELOPE_MISSING,
            "a typed ST12-E admission owner is required before operation work",
        )
    decision = resolver.admit_operation(request)
    if not isinstance(decision, AgentCapabilityDecisionV1):
        raise AuthorityDeniedError(
            ReasonCode.TASK_ENVELOPE_MISSING,
            "the admission owner returned no compatible typed decision",
        )
    if (
        decision.request_id != request.request_id
        or decision.principal_id != request.principal_id
        or decision.operation_id != request.operation_name
        or decision.idempotency_key != request.idempotency_key
        or decision.policy_version != POLICY_VERSION
        or decision.runtime_effect_authorized is not False
    ):
        raise AuthorityDeniedError(
            ReasonCode.TASK_SCOPE_MISMATCH,
            "the typed admission decision does not bind the exact request",
        )
    if decision.decision_state is (
        AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST
    ):
        return decision
    if decision.decision_state is (
        AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED
    ):
        raise NoTradeReoptimizationRouteError(decision)
    reason = (
        decision.reason_codes[0]
        if decision.reason_codes
        else ReasonCode.CAPABILITY_DENIED
    )
    raise AuthorityDeniedError(reason, decision.decision_id)


def _submit_mode_snapshot_candidate(
    self,
    request: SubmitCandidateProposalRequestV1,
    capability_decision: AgentCapabilityDecisionV1,
    *,
    admission_ns: int,
) -> SubmitCandidateProposalResponseV1:
    """Private D body under the existing admitted public operation."""

    resolver = self.mode_snapshot_input_resolver
    if (
        type(resolver) is not CurrentModeSnapshotInputResolverV1
        or resolver.owner_registry is not self.owner_registry
    ):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MISSING,
            "D requires the concrete current resolver bound to the service registry",
        )
    stage_values = {name: 0 for name in (
        "central_capability_admission_ns",
        "request_validation_ns",
        "identity_and_context_resolution_ns",
        "parameter_and_source_binding_ns",
        "snapshot_candidate_resolution_ns",
        "formula_compute_ns",
        "output_validation_ns",
        "receipt_materialization_ns",
        "owner_projection_ns",
    )}
    stage_values["central_capability_admission_ns"] = admission_ns

    identity_started = local_duration_now_ns()
    inputs = resolver.resolve_mode_snapshot_inputs(
        request,
        capability_decision,
    )
    stage_values["identity_and_context_resolution_ns"] = (
        local_duration_now_ns() - identity_started
    )
    if type(inputs) is not ModeSnapshotCandidateInputsV1 or (
        inputs.request_id != request.request_id
        or inputs.principal_id != request.principal_id
        or inputs.task_id != capability_decision.task_id
        or inputs.current_agent_id != capability_decision.current_agent_id
        or inputs.capability_decision_ref != capability_decision.decision_id
        or inputs.context_ref != request.context.context_id
    ):
        raise ContractValidationError(
            ReasonCode.IDENTITY_OR_VERSION_UNRESOLVED,
            "D resolved inputs do not bind the admitted request and task",
        )

    measurement_ref = f"LATENCY-MEASUREMENT::{request.request_id}"
    source_candidate_refs: tuple[str, ...] = ()
    safety_blocked = bool(
        validate_current_kill_submit_state(
            inputs.kill_submit_state,
            evaluated_at=inputs.evaluated_at,
        )
    )
    expected_evidence = pre_f_unavailable_reference(
        observed_at=request.context.as_of,
        valid_until=request.context.as_of + request.context.maximum_age,
        causation_id=inputs.causation_id,
        correlation_id=inputs.correlation_id,
    )
    if (
        inputs.evidence_reference != expected_evidence
        or inputs.evidence_reference.evidence_state
        is not ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
    ):
        raise OwnerAdapterError(
            ReasonCode.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED,
            "current pre-F D service accepts only the canonical unavailable reference",
        )
    evidence_blocked = (
        inputs.evidence_reference.evidence_state
        is ST12FEvidenceStateV1.EVIDENCE_UNAVAILABLE_F_NOT_IMPLEMENTED
    )
    if not safety_blocked and not evidence_blocked:
        validation_started = local_duration_now_ns()
        _validate_d_proposed_specification(request, inputs)
        stage_values["request_validation_ns"] = (
            local_duration_now_ns() - validation_started
        )

        binding_started = local_duration_now_ns()
        source_candidate_refs = request.source_candidate_refs
        usage = ResourceUsageV1(
            input_cardinality=len(request.proposed_specification.fields),
            input_bytes=sum(
                len(field.name) + len(str(field.value))
                for field in request.proposed_specification.fields
            ),
            dependency_depth=len(inputs.formula_spec_refs),
            bootstrap_repetitions=0,
            concurrency=1,
        )
        resources_closed = not validate_resource_bounds(
            usage,
            self.resource_bounds_profile,
        )
        if not resources_closed:
            raise ContractValidationError(
                ReasonCode.RESOURCE_BOUND_EXCEEDED,
                "D proposal body exceeds the exact owner-supplied resource bounds",
            )
        inputs = replace(
            inputs,
            latency_profile_present=self.latency_budget_profile is not None,
            latency_measurement_ref_or_explicit_absence=measurement_ref,
        )
        stage_values["parameter_and_source_binding_ns"] = (
            local_duration_now_ns() - binding_started
        )
    else:
        # Current safety and pre-F evidence blocks precede proposal/schema/body reads.
        inputs = replace(
            inputs,
            latency_profile_present=self.latency_budget_profile is not None,
            latency_measurement_ref_or_explicit_absence=measurement_ref,
        )

    candidate_started = local_duration_now_ns()
    mode_snapshot_result = evaluate_mode_snapshot_candidate(inputs)
    stage_values["snapshot_candidate_resolution_ns"] = (
        local_duration_now_ns() - candidate_started
    )
    output_started = local_duration_now_ns()
    if type(mode_snapshot_result) is not ModeSnapshotCandidateProposalResultV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "D policy returned no exact typed proposal result",
        )
    stage_values["output_validation_ns"] = (
        local_duration_now_ns() - output_started
    )

    def materialize_measurement(
        result: ModeSnapshotCandidateProposalResultV1,
    ) -> LatencyMeasurementV1:
        decision = result.mode_snapshot_decision
        return build_latency_measurement(
            measurement_ref=measurement_ref,
            stage_values_ns=stage_values,
            labels=LatencyMeasurementLabelsV1(
                cold_or_warm="WARM",
                concurrency_level=1,
                platform_profile_id=(
                    self.latency_budget_profile.profile_id
                    if self.latency_budget_profile is not None
                    else "EXPLICIT_ABSENCE"
                ),
                operation_id=request.operation_name,
                success_or_blocker=decision.allow_candidate_state.value,
                fallback_used=(
                    decision.fallback_route
                    not in {
                        "CONTINUE_NO_EFFECT",
                        "RETURN_DECISION_NO_EFFECT",
                    }
                ),
            ),
            rejection_count=(
                0
                if decision.allow_candidate_state.value
                == "ELIGIBLE_NOT_ACTIVATED"
                else 1
            ),
        )

    measurement = materialize_measurement(mode_snapshot_result)
    latency_decision = evaluate_latency_profile(
        measurement,
        self.latency_budget_profile,
    )
    if (
        latency_decision.promotion_sensitive_allow_blocked
        and inputs.latency_profile_present
    ):
        inputs = replace(inputs, latency_profile_present=False)
        mode_snapshot_result = evaluate_mode_snapshot_candidate(inputs)
        measurement = materialize_measurement(mode_snapshot_result)

    owner_started = local_duration_now_ns()
    from .protocols import ExistingOwnerProjectionAdapterV1

    projection_adapter = ExistingOwnerProjectionAdapterV1(resolver.repo_root)
    final_projection = projection_adapter.project_mode_snapshot(
        mode_snapshot_result.mode_snapshot_decision,
        inputs.evidence_reference,
        inputs.kill_submit_state,
        snapshot_version=inputs.candidate_version,
        svc_view=projection_adapter.load_svc(),
    )
    mode_snapshot_result = replace(
        mode_snapshot_result,
        owner_projection_or_explicit_absence=final_projection,
    )
    stage_values["owner_projection_ns"] = (
        local_duration_now_ns() - owner_started
    )
    measurement = materialize_measurement(mode_snapshot_result)

    receipt_started = local_duration_now_ns()
    control_receipts = materialize_mode_snapshot_control_receipts(
        mode_snapshot_result,
        parameter_value_refs=inputs.parameter_value_refs,
        effective_at=request.requested_at,
        recorded_at=request.requested_at,
        traceparent=request.traceparent,
        tracestate=request.tracestate,
    )
    control_refs = tuple(row.record_id for row in control_receipts)
    if control_refs != mode_snapshot_result.control_receipt_refs:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "D response control refs differ from the emitted receipt spine",
        )
    stage_values["receipt_materialization_ns"] = (
        local_duration_now_ns() - receipt_started
    )
    measurement = materialize_measurement(mode_snapshot_result)

    decision = mode_snapshot_result.mode_snapshot_decision
    succeeded = decision.allow_candidate_state.value == "ELIGIBLE_NOT_ACTIVATED"
    blocker = () if succeeded else (
        OperationBlockerCodeV1.EVIDENCE_REFERENCE_UNAVAILABLE
        if decision.allow_candidate_state.value == "EVIDENCE_UNAVAILABLE"
        else OperationBlockerCodeV1.KILL_OR_SUBMIT_DISABLED
        if decision.reason_codes[0]
        in {
            ReasonCode.KILL_OR_SUBMIT_DISABLED,
            ReasonCode.KILL_SUBMIT_DISABLED_OR_SAFETY_BLOCK,
        }
        else OperationBlockerCodeV1.LATENCY_PROFILE_REQUIRED
        if decision.reason_codes[0] is ReasonCode.LATENCY_PROFILE_REQUIRED
        else OperationBlockerCodeV1.MODE_SNAPSHOT_BLOCKED,
    )
    proposal = CandidateProposalV1(
        **_result_common(
            request,
            terminal_route=decision.fallback_route,
            evidence_refs=(
                *source_candidate_refs,
                *control_refs,
                measurement.measurement_ref,
            ),
        ),
        candidate_id=(
            mode_snapshot_result.snapshot_transition_proposal.target_candidate_ref
        ),
        proposal_state=decision.allow_candidate_state.value,
        mode_snapshot_result=mode_snapshot_result,
    )
    return SubmitCandidateProposalResponseV1(
        **_common_response(
            request,
            status=(
                OperationStatusV1.SUCCEEDED
                if succeeded
                else OperationStatusV1.BLOCKED
            ),
            blocker_codes=blocker,
            receipt_refs=(*control_refs, measurement.measurement_ref),
        ),
        proposal=proposal,
    )

@dataclass(frozen=True, slots=True)
class QKUComputationControlPlaneV1:
    """One bounded service; it owns no provider, private state, LLM, or QPU."""

    owner_registry: CanonicalOwnerPacketRegistryV1
    agent_capability_resolver: AgentCapabilityAdmissionProtocolV1
    identity_adapter: RP5CIdentityAdapterV1 | None = None
    persistence_adapter: PersistenceAdapterV1 | None = None
    mode_snapshot_input_resolver: ModeSnapshotCandidateInputProtocolV1 | None = None
    mode_snapshot_owner_projection_adapter: ModeSnapshotOwnerProjectionProtocolV1 | None = None
    mode_snapshot_svc_view: OwnerProjectionViewV1 | None = None
    latency_budget_profile: LatencyBudgetProfileV1 | None = None
    resource_bounds_profile: ResourceBoundsProfileV1 | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.owner_registry, CanonicalOwnerPacketRegistryV1
        ) or (
            self.identity_adapter is not None
            and not isinstance(self.identity_adapter, RP5CIdentityAdapterV1)
        ) or (
            self.persistence_adapter is not None
            and not isinstance(self.persistence_adapter, PersistenceAdapterV1)
        ) or not isinstance(
            self.agent_capability_resolver,
            AgentCapabilityAdmissionProtocolV1,
        ) or (
            self.mode_snapshot_input_resolver is not None
            and not isinstance(
                self.mode_snapshot_input_resolver,
                ModeSnapshotCandidateInputProtocolV1,
            )
        ) or (
            self.mode_snapshot_owner_projection_adapter is not None
            and not isinstance(
                self.mode_snapshot_owner_projection_adapter,
                ModeSnapshotOwnerProjectionProtocolV1,
            )
        ) or (
            self.mode_snapshot_svc_view is not None
            and type(self.mode_snapshot_svc_view) is not OwnerProjectionViewV1
        ) or (
            self.latency_budget_profile is not None
            and type(self.latency_budget_profile) is not LatencyBudgetProfileV1
        ) or (
            self.resource_bounds_profile is not None
            and type(self.resource_bounds_profile) is not ResourceBoundsProfileV1
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "service requires canonical packets and one typed admission owner",
            )

    def resolve_identity(
        self, request: ResolveIdentityRequestV1
    ) -> ResolveIdentityResponseV1:
        _admit_agent_request(self, request)
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
            if isinstance(candidate, str) and candidate in CURRENT_IMPLEMENTATION_REGISTRY:
                identity_ref = candidate
                evidence_refs = (
                    CURRENT_IMPLEMENTATION_REGISTRY[
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
        _admit_agent_request(self, request)
        context = request.context
        assert isinstance(context, ComputationExecutionContextV1)
        context_admission_blocker = None
        stack_admission_blocker = None
        selected_stack_id = context.dependency_graph_id
        ordered_component_ids = (request.component_id,)
        if selected_stack_id in REGISTERED_FORMULA_STACKS:
            ordered_component_ids = REGISTERED_FORMULA_STACKS[
                selected_stack_id
            ].component_ids
        try:
            _admit_computation_plan(
                execution_context=context,
                ordered_component_ids=ordered_component_ids,
                selected_stack_id=selected_stack_id,
            )
        except EXPECTED_PUBLIC_OPERATION_ERRORS as exc:
            (
                context_admission_blocker,
                stack_admission_blocker,
            ) = _contextual_admission_blockers(exc)
        snapshot = FrozenContextualComputabilityResolverV1.resolve(
            request.component_id,
            context=context,
            owner_registry=self.owner_registry,
            required_stack_id=selected_stack_id,
            context_admission_blocker=context_admission_blocker,
            stack_admission_blocker=stack_admission_blocker,
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
                receipt_refs=snapshot.receipt_refs,
            ),
            computability=snapshot.resolution,
        )

    def resolve_applicable_stack(
        self, request: ResolveApplicableStackRequestV1
    ) -> ResolveApplicableStackResponseV1:
        _admit_agent_request(self, request)
        component_ids = tuple(request.required_launch_roles)
        try:
            context = request.context
            assert isinstance(context, ComputationExecutionContextV1)
            if context.dependency_graph_id is None:
                raise StackResolutionError(
                    ReasonCode.NO_APPLICABLE_STACK,
                    "applicable-stack resolution requires a selected graph",
                )
            _admit_computation_plan(
                execution_context=context,
                ordered_component_ids=component_ids,
                selected_stack_id=context.dependency_graph_id,
            )
            stack = ApplicableStackResolverV1.resolve(
                stack_id=context.dependency_graph_id,
                stack_version=context.dependency_graph_version or "",
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
        _admit_agent_request(self, request)
        names: list[str] = []
        packet_refs: list[str] = []
        receipt_refs: list[str] = []
        try:
            context = request.context
            assert isinstance(context, ComputationExecutionContextV1)
            _admit_computation_plan(
                execution_context=context,
                ordered_component_ids=request.component_ids,
                selected_stack_id=None,
            )
            for component_id in request.component_ids:
                resolved = FormulaInputResolverV1.resolve(
                    component_id,
                    context=context,
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
        _admit_agent_request(self, request)
        try:
            context = request.context
            assert isinstance(context, ComputationExecutionContextV1)
            _admit_computation_plan(
                execution_context=context,
                ordered_component_ids=(request.component_id,),
                selected_stack_id=None,
            )
            if request.component_id not in CURRENT_IMPLEMENTATION_REGISTRY:
                raise ContractValidationError(
                    ReasonCode.UNKNOWN_IMPLEMENTATION,
                    f"unknown registered component: {request.component_id}",
                )
            schema = CURRENT_NAMED_OUTPUT_CONTRACTS[request.component_id]
            if request.expected_output_schema_ref != schema.schema_id:
                raise ContractValidationError(
                    ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                    "requested output schema differs from the frozen formula schema",
                )
            resolved = FormulaInputResolverV1.resolve(
                request.component_id,
                context=context,
                owner_registry=self.owner_registry,
                caller_assertions=_assertions(request.input_values),
            )
            value = (
                invoke_current_formula(
                    request.component_id, resolved.authoritative_values
                )
                if request.component_id == "MATH-39"
                else invoke_formula_v34(
                    request.component_id, resolved.authoritative_values
                )
            )
            output = _frozen_output(
                request.component_id,
                value,
                execution_context=context,
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
        _admit_agent_request(self, request)
        try:
            context = request.context
            assert isinstance(context, ComputationExecutionContextV1)
            _admit_computation_plan(
                execution_context=context,
                ordered_component_ids=request.component_ids,
                selected_stack_id=request.stack_id,
            )
            assertions = _assertions(request.input_values)
            assertions_by_math: dict[str, dict[str, object]] = {
                component_id: {} for component_id in request.component_ids
            }
            for name, value in assertions.items():
                if "." not in name:
                    raise ContractValidationError(
                        ReasonCode.INVALID_CONTRACT,
                        "stack assertions must use MATH-ID.input_name keys",
                    )
                component_id, input_name = name.split(".", 1)
                if component_id not in assertions_by_math:
                    raise ContractValidationError(
                        ReasonCode.INVALID_CONTRACT,
                        f"stack assertion names unknown component {component_id}",
                    )
                assertions_by_math[component_id][input_name] = value
            execution = ApplicableStackResolverV1.execute(
                stack_id=request.stack_id,
                component_ids=request.component_ids,
                context=context,
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
                    execution_context=context,
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
        _admit_agent_request(self, request)
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
        _admit_agent_request(self, request)
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
        _admit_agent_request(self, request)
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
        _admit_agent_request(self, request)
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
        admission_started = local_duration_now_ns()
        capability_decision = _admit_agent_request(self, request)
        admission_ns = local_duration_now_ns() - admission_started
        # The candidate discriminator is deliberately read only after the
        # mandatory central ST12-E admission above.
        if request.candidate_kind == MODE_SNAPSHOT_CANDIDATE_KIND:
            return _submit_mode_snapshot_candidate(
                self,
                request,
                capability_decision,
                admission_ns=admission_ns,
            )
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
        _admit_agent_request(self, request)
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
