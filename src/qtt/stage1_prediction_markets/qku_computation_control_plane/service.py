"""Synchronous pure in-process Tranche-B computation service."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .bindings import BindingResolverV1
from .context import canonical_probability_decimal, finite_float
from .contextual_computability import (
    EvidenceDerivedComputabilityReceiptV1,
    EvidenceDerivedContextualComputabilityResolverV1,
)
from .dependency_graph import CompiledDependencyGraphV1, DependencyGraphCompilerV1
from .errors import (
    ComputationControlPlaneError,
    ComputationServiceError,
    ReasonCode,
)
from .fallback import (
    FallbackResolutionReceiptV1,
    REGISTERED_FALLBACK_RESOLVER,
)
from .freshness import (
    DeadlineBudgetV1,
    DeadlineReceiptV1,
    DeadlineResolverV1,
    FreshnessPolicyV1,
)
from .implementation_registry import (
    DiscreteLinearBiasV1,
    DiscretePairwiseBiasV1,
    DiscreteVariableV1,
    LinearTermV1,
    ObjectiveScalingReceiptV1,
    QuadraticConstraintV1,
    QuadraticTermV1,
    QuadraticVariableV1,
    QuantityAndFrictionTermsV1,
    QuboModelV1,
    QuboUpperTermV1,
    get_math_callable,
    get_math_implementation,
    TRANCHE_A_MATH_IDS,
)
from .identity_adapter import IdentityViewV1, RP5CIdentityAdapterV1
from .input_resolver import (
    ContextualInputValueV1,
    InputResolutionReceiptV1,
    RequiredInputResolverV1,
)
from .models import (
    BuildEvidenceBundleRequestV1,
    BuildEvidenceBundleResponseV1,
    CandidateProposalV1,
    CompareWithNoTradeRequestV1,
    CompareWithNoTradeResponseV1,
    CompileReplayPaperCohortRequestV1,
    CompileReplayPaperCohortResponseV1,
    ComponentResultV1,
    ComputationExecutionReceiptV1,
    ComputabilityClassV1,
    ComputeComponentRequestV1,
    ComputeComponentResponseV1,
    ComputeStackRequestV1,
    ComputeStackResponseV1,
    DependencyNodeV1,
    EvidenceBundleResultV1,
    EvaluateTradePlanRequestV1,
    EvaluateTradePlanResponseV1,
    ExplainResolutionRequestV1,
    ExplainResolutionResponseV1,
    GetSnapshotViewRequestV1,
    GetSnapshotViewResponseV1,
    IdentityResolutionV1,
    InputResolutionV1,
    MaterializationWorkOrderV1,
    NoTradeComparisonV1,
    ObjectiveSense,
    OperationBlockerCodeV1,
    OperationRequestEnvelopeV1,
    OperationResponseEnvelopeV1,
    OperationStatusV1,
    RegisterReplayPaperResultRequestV1,
    RegisterReplayPaperResultResponseV1,
    ReplayPaperCohortCompilationV1,
    ReplayPaperResultRegistrationV1,
    RequestMaterializationWorkOrderRequestV1,
    RequestMaterializationWorkOrderResponseV1,
    ResolutionExplanationV1,
    ResolveApplicableStackRequestV1,
    ResolveApplicableStackResponseV1,
    ResolveContextualComputabilityRequestV1,
    ResolveContextualComputabilityResponseV1,
    ResolveIdentityRequestV1,
    ResolveIdentityResponseV1,
    ResolveRequiredInputsRequestV1,
    ResolveRequiredInputsResponseV1,
    SnapshotViewV1,
    StackResolutionV1,
    StackResultV1,
    SubmitCandidateProposalRequestV1,
    SubmitCandidateProposalResponseV1,
    TradePlanEvaluationV1,
    TypedValueKindV1,
    TypedValueRecordV1,
    TypedValueV1,
    UnitBindingV1,
    VariableDomain,
)
from .oracle_contracts import get_golden_vector, get_oracle
from .point_in_time import (
    PointInTimeEvidenceV1,
    PointInTimeFieldClassV1,
)
from .serialization import deterministic_json, safe_json_loads
from .specification import (
    CertifiedMathIdentityRefV1,
    ComputationContractCompilerV1,
    FormulaExecutionContractV1,
    MATH_IO_CONTRACTS,
)
from .stack_resolver import (
    ApplicableStackResolutionReceiptV1,
    ApplicableStackResolverV1,
    StackApplicabilityContextV1,
)
from .unit_conversion import (
    EMPTY_UNIT_CONVERSION_REGISTRY,
    UnitConversionRegistryV1,
)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComputationServiceError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class ComponentExecutionControlsV1:
    """Explicit procedural controls absent from the frozen top-level schema."""

    seed: int | None = None
    replicates: int | None = None
    confidence: float | None = None
    alpha: float | None = None
    mean_block_length: float | None = None

    def __post_init__(self) -> None:
        for name in ("seed", "replicates"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                raise ComputationServiceError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a positive integer when declared",
                )
        for name in ("confidence", "alpha", "mean_block_length"):
            value = getattr(self, name)
            if value is not None:
                numeric = finite_float(value, field_name=name)
                if numeric <= 0:
                    raise ComputationServiceError(
                        ReasonCode.INVALID_CONTRACT,
                        f"{name} must be positive when declared",
                    )
                object.__setattr__(self, name, numeric)


@dataclass(frozen=True, slots=True)
class TrancheBComputationExecutionReceiptV1(ComputationExecutionReceiptV1):
    input_json: str = "{}"
    callable_version: str = ""
    output_schema_ref: str = ""
    input_receipt_ref: str = ""
    computability_receipt_ref: str = ""
    point_in_time_receipt_refs: tuple[str, ...] = ()
    freshness_receipt_refs: tuple[str, ...] = ()
    conversion_receipt_refs: tuple[str, ...] = ()
    dependency_receipt_refs: tuple[str, ...] = ()
    fallback_receipt_ref: str | None = None
    deadline_receipt_ref: str | None = None
    consumer_refs: tuple[str, ...] = ()
    terminal_route: str = ""

    def __post_init__(self) -> None:
        ComputationExecutionReceiptV1.__post_init__(self)
        safe_json_loads(self.input_json)
        for name in (
            "callable_version",
            "output_schema_ref",
            "input_receipt_ref",
            "computability_receipt_ref",
            "terminal_route",
        ):
            _required_text(getattr(self, name), name)
        for name in (
            "point_in_time_receipt_refs",
            "freshness_receipt_refs",
            "conversion_receipt_refs",
            "dependency_receipt_refs",
            "consumer_refs",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ComputationServiceError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a unique immutable text tuple",
                )
        if self.deadline_receipt_ref is not None:
            _required_text(self.deadline_receipt_ref, "deadline_receipt_ref")


@dataclass(frozen=True, slots=True)
class ComponentComputationResultV1(ComponentResultV1):
    component_id: str = ""
    output_values: TypedValueRecordV1 | None = None
    input_resolution_receipt: InputResolutionReceiptV1 | None = None
    computability_receipt: EvidenceDerivedComputabilityReceiptV1 | None = None
    execution_receipt: TrancheBComputationExecutionReceiptV1 | None = None
    fallback_receipt: FallbackResolutionReceiptV1 | None = None
    blocker_reason_codes: tuple[ReasonCode, ...] = ()

    def __post_init__(self) -> None:
        ComponentResultV1.__post_init__(self)
        _required_text(self.component_id, "component_id")
        if self.output_values is not None and not isinstance(
            self.output_values,
            TypedValueRecordV1,
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "component output must be a typed record",
            )
        if (
            not isinstance(self.blocker_reason_codes, tuple)
            or any(
                not isinstance(value, ReasonCode)
                for value in self.blocker_reason_codes
            )
            or len(set(self.blocker_reason_codes))
            != len(self.blocker_reason_codes)
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "component blockers must be a unique typed tuple",
            )
        if bool(self.blocker_reason_codes) == bool(self.execution_receipt):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "successful components require execution receipts; blocked ones do not",
            )
        if (self.execution_receipt is None) == (self.output_values is not None):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "component output presence must equal execution-receipt presence",
            )


@dataclass(frozen=True, slots=True)
class StackExecutionReceiptV1:
    receipt_id: str
    selected_stack_id: str
    component_receipt_refs: tuple[str, ...]
    topological_order: tuple[str, ...]
    edge_consumption_refs: tuple[str, ...]
    final_output_json: str
    dependency_graph_ref: str
    fallback_receipt_ref: str | None
    consumer_refs: tuple[str, ...]
    terminal_route: str
    provider_effect: bool = False
    private_state_effect: bool = False
    replay_or_paper_execution_effect: bool = False
    qpu_effect: bool = False
    mode_or_grant_effect: bool = False
    order_release_effect: bool = False

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "selected_stack_id",
            "dependency_graph_ref",
            "terminal_route",
        ):
            _required_text(getattr(self, name), name)
        safe_json_loads(self.final_output_json)
        for name, nonempty in (
            ("component_receipt_refs", True),
            ("topological_order", True),
            ("edge_consumption_refs", False),
            ("consumer_refs", True),
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or (nonempty and not values)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ComputationServiceError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a unique immutable text tuple",
                )
        if len(self.component_receipt_refs) != len(self.topological_order):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "stack receipt requires one component receipt per topological node",
            )
        if self.fallback_receipt_ref is not None:
            _required_text(self.fallback_receipt_ref, "fallback_receipt_ref")
        effect_flags = (
            self.provider_effect,
            self.private_state_effect,
            self.replay_or_paper_execution_effect,
            self.qpu_effect,
            self.mode_or_grant_effect,
            self.order_release_effect,
        )
        if any(type(value) is not bool for value in effect_flags) or any(
            effect_flags
        ):
            raise ComputationServiceError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "stack receipts must preserve every prohibited effect at zero",
            )


@dataclass(frozen=True, slots=True)
class StackComputationResultV1(StackResultV1):
    selected_stack_id: str = ""
    component_results: tuple[ComponentComputationResultV1, ...] = ()
    output_values: TypedValueRecordV1 | None = None
    execution_receipt: StackExecutionReceiptV1 | None = None
    blocker_reason_codes: tuple[ReasonCode, ...] = ()

    def __post_init__(self) -> None:
        StackResultV1.__post_init__(self)
        _required_text(self.selected_stack_id, "selected_stack_id")
        if (
            not isinstance(self.component_results, tuple)
            or any(
                not isinstance(item, ComponentComputationResultV1)
                for item in self.component_results
            )
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "stack component results must be typed and immutable",
            )
        if self.output_values is not None and not isinstance(
            self.output_values,
            TypedValueRecordV1,
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "stack output must be a typed record",
            )
        if (
            not isinstance(self.blocker_reason_codes, tuple)
            or any(
                not isinstance(value, ReasonCode)
                for value in self.blocker_reason_codes
            )
            or len(set(self.blocker_reason_codes))
            != len(self.blocker_reason_codes)
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "stack blockers must be a unique typed tuple",
            )
        if bool(self.blocker_reason_codes) == bool(self.execution_receipt):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "successful stacks require one receipt; blocked stacks do not",
            )
        if (self.execution_receipt is None) == (self.output_values is not None):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "stack output presence must equal execution-receipt presence",
            )


@dataclass(frozen=True, slots=True)
class DetailedStackResolutionV1(StackResolutionV1):
    selected_stack_id: str = ""
    component_ids: tuple[str, ...] = ()
    topological_order: tuple[str, ...] = ()
    resolution_receipt: ApplicableStackResolutionReceiptV1 | None = None

    def __post_init__(self) -> None:
        StackResolutionV1.__post_init__(self)
        _required_text(self.selected_stack_id, "selected_stack_id")
        if (
            not self.component_ids
            or self.component_ids != self.topological_order
            or not isinstance(
                self.resolution_receipt,
                ApplicableStackResolutionReceiptV1,
            )
            or self.resolution_receipt.selected_stack_id
            != self.selected_stack_id
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "detailed stack resolution must equal its typed resolver receipt",
            )


@dataclass(frozen=True, slots=True)
class DetailedInputResolutionV1(InputResolutionV1):
    component_receipts: tuple[InputResolutionReceiptV1, ...] = ()

    def __post_init__(self) -> None:
        InputResolutionV1.__post_init__(self)
        if (
            not isinstance(self.component_receipts, tuple)
            or any(
                not isinstance(item, InputResolutionReceiptV1)
                for item in self.component_receipts
            )
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "input-resolution result receipts must be typed",
            )


@dataclass(frozen=True, slots=True)
class StructuredResolutionExplanationV1(ResolutionExplanationV1):
    trusted_typed_input_facts: tuple[str, ...] = ()
    owner_preferences_and_candidate_assertions: tuple[str, ...] = ()
    formula_and_implementation_lineage: tuple[str, ...] = ()
    dependency_and_conversion_lineage: tuple[str, ...] = ()
    units_bases_precision_and_rounding: tuple[str, ...] = ()
    point_in_time_and_freshness_state: tuple[str, ...] = ()
    parameter_policy_resolution: tuple[str, ...] = ()
    uncertainty_and_model_limitations: tuple[str, ...] = ()
    typed_agent_disagreements: tuple[str, ...] = ()
    blockers_and_hard_veto_state: tuple[str, ...] = ()
    fallback_state: tuple[str, ...] = ()
    downstream_consumers: tuple[str, ...] = ()
    next_safe_routes: tuple[str, ...] = ()
    forbidden_effects: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ResolutionExplanationV1.__post_init__(self)
        for name in (
            "trusted_typed_input_facts",
            "owner_preferences_and_candidate_assertions",
            "formula_and_implementation_lineage",
            "dependency_and_conversion_lineage",
            "units_bases_precision_and_rounding",
            "point_in_time_and_freshness_state",
            "parameter_policy_resolution",
            "uncertainty_and_model_limitations",
            "typed_agent_disagreements",
            "blockers_and_hard_veto_state",
            "fallback_state",
            "downstream_consumers",
            "next_safe_routes",
            "forbidden_effects",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ComputationServiceError(
                    ReasonCode.INVALID_CONTRACT,
                    f"explanation section {name} must be typed text",
                )


@dataclass(frozen=True, slots=True)
class TrancheBServiceBindingV1:
    operation_id: str
    operation_name: str
    service_method: str
    implementation_state: str
    downstream_routes: tuple[str, ...]
    pure_in_process: bool = True
    external_or_durable_effect_allowed: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.pure_in_process) is not bool
            or not self.pure_in_process
            or type(self.external_or_durable_effect_allowed) is not bool
            or self.external_or_durable_effect_allowed
        ):
            raise ComputationServiceError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "service bindings must remain pure in-process",
            )


_SERVICE_BINDING_ROWS = (
    ("ST10-OP::01", "resolve_identity", "resolve_identity", "DELEGATED_CANONICAL_OWNER"),
    (
        "ST10-OP::02",
        "resolve_contextual_computability",
        "resolve_contextual_computability",
        "REAL_EVIDENCE_DERIVED_RESOLVER",
    ),
    (
        "ST10-OP::03",
        "resolve_applicable_stack",
        "resolve_applicable_stack",
        "REAL_DETERMINISTIC_RESOLVER",
    ),
    (
        "ST10-OP::04",
        "resolve_required_inputs",
        "resolve_required_inputs",
        "REAL_TYPED_INPUT_RESOLVER",
    ),
    (
        "ST10-OP::05",
        "compute_component",
        "compute_component",
        "REAL_REGISTERED_CALLABLE_EXECUTION",
    ),
    (
        "ST10-OP::06",
        "compute_stack",
        "compute_stack",
        "REAL_DEPENDENCY_CLOSED_EXECUTION",
    ),
    (
        "ST10-OP::07",
        "compare_with_no_trade",
        "compare_with_no_trade",
        "PURE_SCOPE_OR_TYPED_BLOCKER",
    ),
    (
        "ST10-OP::08",
        "evaluate_trade_plan",
        "evaluate_trade_plan",
        "PURE_SCOPE_OR_TYPED_BLOCKER",
    ),
    ("ST10-OP::09", "get_snapshot_view", "get_snapshot_view", "READ_ONLY_ROUTE"),
    (
        "ST10-OP::10",
        "explain_resolution",
        "explain_resolution",
        "STRUCTURED_DETERMINISTIC_NO_LLM",
    ),
    (
        "ST10-OP::11",
        "submit_candidate_proposal",
        "submit_candidate_proposal",
        "OWNER_REVIEW_ROUTE_ONLY",
    ),
    (
        "ST10-OP::12",
        "request_materialization_work_order",
        "request_materialization_work_order",
        "TYPED_WORK_ORDER_ROUTE_ONLY",
    ),
    (
        "ST10-OP::13",
        "compile_replay_paper_cohort",
        "compile_replay_paper_cohort",
        "CONTRACT_COMPILATION_NO_CAMPAIGN",
    ),
    (
        "ST10-OP::14",
        "register_replay_paper_result",
        "register_replay_paper_result",
        "PREEXISTING_RESULT_ROUTING_ONLY",
    ),
    (
        "ST10-OP::15",
        "build_evidence_bundle",
        "build_evidence_bundle",
        "EVIDENCE_ROUTING_ONLY",
    ),
)

TRANCHE_B_SERVICE_BINDINGS: Mapping[str, TrancheBServiceBindingV1] = (
    MappingProxyType(
        {
            operation_id: TrancheBServiceBindingV1(
                operation_id=operation_id,
                operation_name=operation_name,
                service_method=method,
                implementation_state=state,
                downstream_routes=(
                    "READINESS1",
                    "PRETRADE1",
                    "SVC1",
                    "AGENT-ORCH1",
                ),
            )
            for operation_id, operation_name, method, state in _SERVICE_BINDING_ROWS
        }
    )
)


def output_schema_ref(component_id: str) -> str:
    implementation = get_math_implementation(component_id)
    return (
        f"OUTPUT_SCHEMA::{component_id}::"
        f"{implementation.contract.specification_version}"
    )


_REASON_TO_OPERATION_BLOCKER = {
    ReasonCode.POINT_IN_TIME_UNAVAILABLE: (
        OperationBlockerCodeV1.POINT_IN_TIME_UNAVAILABLE
    ),
    ReasonCode.REVISION_LEAKAGE: (
        OperationBlockerCodeV1.POINT_IN_TIME_UNAVAILABLE
    ),
    ReasonCode.FIELD_STALE: OperationBlockerCodeV1.CONTEXT_STALE,
    ReasonCode.FRESHNESS_UNKNOWN: OperationBlockerCodeV1.FRESHNESS_UNKNOWN,
    ReasonCode.REQUIRED_INPUT_MISSING: OperationBlockerCodeV1.INPUT_MISSING,
    ReasonCode.REQUIRED_INPUT_STALE: OperationBlockerCodeV1.CONTEXT_STALE,
    ReasonCode.INPUT_TYPE_MISMATCH: OperationBlockerCodeV1.INPUT_INVALID,
    ReasonCode.DEPENDENCY_UNIT_MISMATCH: (
        OperationBlockerCodeV1.UNIT_OR_BASIS_INCOMPATIBLE
    ),
    ReasonCode.UNIT_CONVERSION_UNKNOWN: (
        OperationBlockerCodeV1.UNIT_OR_BASIS_INCOMPATIBLE
    ),
    ReasonCode.BASIS_CONVERSION_FORBIDDEN: (
        OperationBlockerCodeV1.UNIT_OR_BASIS_INCOMPATIBLE
    ),
    ReasonCode.DEADLINE_EXHAUSTED: (
        OperationBlockerCodeV1.DEADLINE_EXHAUSTED
    ),
    ReasonCode.UNKNOWN_IMPLEMENTATION: (
        OperationBlockerCodeV1.IDENTITY_UNVERIFIED
    ),
    ReasonCode.ORACLE_NOT_INDEPENDENT: (
        OperationBlockerCodeV1.ORACLE_UNAVAILABLE
    ),
    ReasonCode.OUTPUT_SCHEMA_MISMATCH: OperationBlockerCodeV1.OUTPUT_INVALID,
    ReasonCode.NONFINITE_NUMERIC_INPUT: OperationBlockerCodeV1.INPUT_INVALID,
    ReasonCode.OUT_OF_DOMAIN: OperationBlockerCodeV1.INPUT_INVALID,
    ReasonCode.PARAMETER_CALIBRATION_REQUIRED: (
        OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED
    ),
    ReasonCode.STACK_NOT_APPLICABLE: OperationBlockerCodeV1.STACK_INCOMPLETE,
    ReasonCode.STACK_NOT_COMPUTABLE: OperationBlockerCodeV1.STACK_INCOMPLETE,
    ReasonCode.REQUEST_LIMIT_EXCEEDED: (
        OperationBlockerCodeV1.REQUEST_BOUND_EXCEEDED
    ),
    ReasonCode.BACKPRESSURE_FAIL_CLOSED: (
        OperationBlockerCodeV1.BACKPRESSURE_FAIL_CLOSED
    ),
}


def _operation_blockers(
    reasons: tuple[ReasonCode, ...],
) -> tuple[OperationBlockerCodeV1, ...]:
    return tuple(
        dict.fromkeys(
            _REASON_TO_OPERATION_BLOCKER.get(
                reason,
                OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED,
            )
            for reason in reasons
        )
    )


def _id(prefix: str, *parts: str) -> str:
    return f"{prefix}::{sha256('|'.join(parts).encode('utf-8')).hexdigest()}"


def _response_common(
    request: OperationRequestEnvelopeV1,
    *,
    status: OperationStatusV1,
    blockers: tuple[OperationBlockerCodeV1, ...],
    receipt_refs: tuple[str, ...],
) -> dict[str, object]:
    return {
        "response_id": _id(
            "RESPONSE",
            request.operation_name,
            request.idempotency_key,
            request.context.stable_key,
        ),
        "operation_name": request.operation_name,
        "request_id": request.request_id,
        "completed_at": request.context.as_of,
        "status": status,
        "context": request.context,
        "warnings": (),
        "blocker_codes": blockers,
        "receipt_refs": receipt_refs,
        "traceparent": request.traceparent,
        "tracestate": request.tracestate,
    }


def _result_id(request: OperationRequestEnvelopeV1) -> str:
    return _id(
        "RESULT",
        request.operation_name,
        request.idempotency_key,
        request.context.stable_key,
    )


def _structured_rows(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list) or not value:
        raise ComputationServiceError(
            ReasonCode.INPUT_TYPE_MISMATCH,
            f"{field_name} must be a nonempty JSON array",
        )
    return value


def _invoke_registered_callable(
    component_id: str,
    arguments: Mapping[str, object],
    controls: ComponentExecutionControlsV1,
) -> object:
    """Map certified schema names to the exact registered callable boundary."""

    callable_ = get_math_callable(component_id)
    values = dict(arguments)
    if component_id == "MATH-07":
        friction = values["quantity_and_friction_terms"]
        if not isinstance(friction, dict):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "quantity_and_friction_terms must be an object",
            )
        values["quantity_and_friction_terms"] = QuantityAndFrictionTermsV1(
            **friction
        )
    elif component_id == "MATH-14":
        if controls.seed is None or controls.replicates is None:
            raise ComputationServiceError(
                ReasonCode.PARAMETER_CALIBRATION_REQUIRED,
                "MATH-14 requires explicit seed and replicate controls",
            )
        values.update(seed=controls.seed, replicates=controls.replicates)
        if controls.confidence is not None:
            values["confidence"] = controls.confidence
    elif component_id in {"MATH-15", "MATH-16"}:
        if controls.seed is None or controls.replicates is None:
            raise ComputationServiceError(
                ReasonCode.PARAMETER_CALIBRATION_REQUIRED,
                f"{component_id} requires explicit seed and replicate controls",
            )
        values.update(seed=controls.seed, replicates=controls.replicates)
        if controls.alpha is not None:
            values["alpha"] = controls.alpha
        if controls.mean_block_length is not None:
            values["mean_block_length"] = controls.mean_block_length
    elif component_id == "MATH-17":
        values = {
            "sharpe_hat": values["SR_hat"],
            "sharpe_ref": values["SR_ref"],
            "n": values["n"],
            "skewness": values["gamma3"],
            "kurtosis": values["gamma4"],
        }
    elif component_id == "MATH-20":
        intervals = _structured_rows(values["sample_intervals"], "sample_intervals")
        folds = values["folds"]
        if (
            isinstance(folds, bool)
            or not isinstance(folds, int)
            or not 2 <= folds <= len(intervals)
        ):
            raise ComputationServiceError(
                ReasonCode.OUT_OF_DOMAIN,
                "MATH-20 folds must be in [2, sample_count]",
            )
        fold_indices = tuple(
            tuple(
                index
                for index in range(len(intervals))
                if index * folds // len(intervals) == fold
            )
            for fold in range(folds)
        )
        return tuple(
            callable_(
                intervals,
                test_indices=test_indices,
                embargo_horizon=values["embargo_horizon"],
            )
            for test_indices in fold_indices
        )
    elif component_id == "MATH-21":
        intervals = _structured_rows(values["sample_intervals"], "sample_intervals")
        if len(intervals) < values["N_groups"]:
            raise ComputationServiceError(
                ReasonCode.OUT_OF_DOMAIN,
                "MATH-21 needs at least one interval per declared group",
            )
        values = {
            "N_groups": values["N_groups"],
            "k_test_groups": values["k_test_groups"],
        }
    elif component_id == "MATH-22":
        logged = _structured_rows(
            values["logged_context_action_reward"],
            "logged_context_action_reward",
        )
        reward_model = _structured_rows(
            values["cross_fitted_reward_model"],
            "cross_fitted_reward_model",
        )
        behavior = values["behavior_propensity"]
        target = values["target_policy_probability"]
        if len(logged) != len(reward_model):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "MATH-22 logged rows and cross-fitted predictions must align",
            )
        samples = []
        for row, prediction in zip(logged, reward_model, strict=True):
            if not isinstance(row, dict) or not isinstance(prediction, dict):
                raise ComputationServiceError(
                    ReasonCode.INPUT_TYPE_MISMATCH,
                    "MATH-22 rows and reward predictions must be objects",
                )
            samples.append(
                {
                    "mu_logged": behavior,
                    "pi_logged": target,
                    "pi_q_sum": prediction["pi_q_sum"],
                    "q_logged": prediction["q_logged"],
                    "reward": row["reward"],
                }
            )
        values = {"samples": samples}
    elif component_id == "MATH-23":
        rows = _structured_rows(values["logged_rows"], "logged_rows")
        weights: list[object] = []
        rewards: list[object] = []
        for row in rows:
            if not isinstance(row, dict):
                raise ComputationServiceError(
                    ReasonCode.INPUT_TYPE_MISMATCH,
                    "MATH-23 logged rows must be objects",
                )
            mu = finite_float(row["behavior_propensity"], field_name="behavior_propensity")
            pi = finite_float(row["target_policy_probability"], field_name="target_policy_probability")
            if mu <= 0:
                raise ComputationServiceError(
                    ReasonCode.OUT_OF_DOMAIN,
                    "MATH-23 requires positive logged propensity",
                )
            weights.append(pi / mu)
            rewards.append(row["reward"])
        values = {"weights": weights, "rewards": rewards}
    elif component_id == "MATH-25":
        rows = _structured_rows(values["DR_inputs"], "DR_inputs")
        taus = _structured_rows(values["tau_grid"], "tau_grid")
        parsed_rows = []
        criteria: dict[float, list[float]] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ComputationServiceError(
                    ReasonCode.INPUT_TYPE_MISMATCH,
                    "MATH-25 DR inputs must be objects",
                )
            parsed_rows.append(row)
            validation = row.get("validation_squared_error_by_tau")
            if not isinstance(validation, dict):
                raise ComputationServiceError(
                    ReasonCode.PARAMETER_CALIBRATION_REQUIRED,
                    "MATH-25 requires nested validation criteria; no tau default exists",
                )
            for tau in taus:
                numeric_tau = finite_float(tau, field_name="tau")
                key = str(tau)
                if key not in validation:
                    raise ComputationServiceError(
                        ReasonCode.PARAMETER_CALIBRATION_REQUIRED,
                        "MATH-25 validation criterion is incomplete for the tau grid",
                    )
                criteria.setdefault(numeric_tau, []).append(
                    finite_float(validation[key], field_name="estimated_mse")
                )
        selected_tau = min(
            criteria,
            key=lambda tau: (sum(criteria[tau]) / len(criteria[tau]), tau),
        )
        values = {
            "weights": [row["weight"] for row in parsed_rows],
            "rewards": [row["reward"] for row in parsed_rows],
            "direct_estimates": [
                row["direct_estimate"] for row in parsed_rows
            ],
            "tau": selected_tau,
        }
    elif component_id == "MATH-46":
        q = values["Q"]
        if not isinstance(q, dict):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "MATH-46 Q must be a typed coefficient object",
            )
        scaling = q.get("scaling_receipt")
        if not isinstance(scaling, dict):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "MATH-46 requires original-objective scaling lineage",
            )
        values = {
            "diagonal": q["diagonal"],
            "upper_terms": tuple(
                QuboUpperTermV1(**item) for item in q.get("upper_terms", [])
            ),
            "offset": values["c"],
            "assignment": q["assignment"],
            "scaling_receipt": ObjectiveScalingReceiptV1(**scaling),
        }
    elif component_id == "MATH-47":
        q = values["QUBO"]
        if not isinstance(q, dict):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "MATH-47 QUBO must be a typed object",
            )
        values = {
            "qubo": QuboModelV1(
                diagonal=tuple(q["diagonal"]),
                upper_terms=tuple(
                    QuboUpperTermV1(**item)
                    for item in q.get("upper_terms", [])
                ),
                offset=q["offset"],
                scaling_receipt=ObjectiveScalingReceiptV1(
                    **q["scaling_receipt"]
                ),
            )
        }
    elif component_id == "MATH-48":
        variable_rows = _structured_rows(values["variables"], "variables")
        expressions = values["objective_and_constraints"]
        if not isinstance(expressions, dict):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "MATH-48 expressions must be a typed object",
            )
        variables = tuple(
            QuadraticVariableV1(
                name=row["name"],
                domain=VariableDomain(row["domain"]),
                lower=row["lower"],
                upper=row["upper"],
            )
            for row in variable_rows
            if isinstance(row, dict)
        )
        linear = tuple(
            LinearTermV1(**row)
            for row in expressions.get("objective_linear", [])
        )
        quadratic = tuple(
            QuadraticTermV1(**row)
            for row in expressions.get("objective_quadratic", [])
        )
        constraints = tuple(
            QuadraticConstraintV1(
                constraint_id=row["constraint_id"],
                linear_terms=tuple(
                    LinearTermV1(**item)
                    for item in row.get("linear_terms", [])
                ),
                quadratic_terms=tuple(
                    QuadraticTermV1(**item)
                    for item in row.get("quadratic_terms", [])
                ),
                sense=row["sense"],
                rhs=row["rhs"],
            )
            for row in expressions.get("constraints", [])
        )
        values = {
            "variables": variables,
            "objective_linear": linear,
            "objective_quadratic": quadratic,
            "constraints": constraints,
            "objective_sense": ObjectiveSense(
                expressions["objective_sense"]
            ),
        }
    elif component_id == "MATH-49":
        variables_value = values["discrete_variables"]
        biases = values["biases"]
        if not isinstance(variables_value, dict) or not isinstance(biases, dict):
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "MATH-49 variable and bias registries must be objects",
            )
        values = {
            "variables": tuple(
                DiscreteVariableV1(name, tuple(cases))
                for name, cases in sorted(variables_value.items())
            ),
            "linear_biases": tuple(
                DiscreteLinearBiasV1(**row)
                for row in biases.get("linear_biases", [])
            ),
            "pairwise_biases": tuple(
                DiscretePairwiseBiasV1(**row)
                for row in biases.get("pairwise_biases", [])
            ),
        }
    return callable_(**values)


def _typed_output(
    component_id: str,
    output: object,
) -> TypedValueRecordV1:
    fields = MATH_IO_CONTRACTS[component_id].outputs
    if len(fields) != 1:
        raise ComputationServiceError(
            ReasonCode.OUTPUT_SCHEMA_MISMATCH,
            "registered component output schemas must be explicitly routed",
        )
    expected = fields[0]
    normalized = expected.type_name.casefold()
    if normalized == "decimal":
        if not isinstance(output, Decimal) or not output.is_finite():
            raise ComputationServiceError(
                ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                f"{component_id} did not return its declared Decimal output",
            )
        value = TypedValueV1(
            expected.name,
            TypedValueKindV1.DECIMAL,
            output,
            expected.unit,
            expected.basis,
        )
    elif normalized == "float64":
        numeric = finite_float(output, field_name=expected.name)
        value = TypedValueV1(
            expected.name,
            TypedValueKindV1.FLOAT64,
            numeric,
            expected.unit,
            expected.basis,
        )
    elif normalized in {"int", "integer"}:
        if isinstance(output, bool) or not isinstance(output, int):
            raise ComputationServiceError(
                ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                f"{component_id} did not return an integer",
            )
        value = TypedValueV1(
            expected.name,
            TypedValueKindV1.INTEGER,
            output,
            expected.unit,
            expected.basis,
        )
    else:
        value = TypedValueV1(
            expected.name,
            TypedValueKindV1.TEXT,
            deterministic_json(output),
            expected.unit,
            expected.basis,
        )
    return TypedValueRecordV1((value,))


_DOWNSTREAM_CONSUMERS = (
    "READINESS1",
    "PRETRADE1",
    "SVC1",
    "AGENT-ORCH1",
)
_NO_EFFECTS = (
    "NO_PROVIDER_EFFECT",
    "NO_PRIVATE_STATE_EFFECT",
    "NO_REPLAY_PAPER_EXECUTION_EFFECT",
    "NO_QPU_EFFECT",
    "NO_MODE_OR_GRANT_EFFECT",
    "NO_ORDER_RELEASE_EFFECT",
)


@dataclass(frozen=True, slots=True)
class AgentDutyRouteV1:
    agent_id: str
    historical_duty_source: str
    current_orchestration_owner: str
    operation_ids: tuple[str, ...]
    upstream_refs: tuple[str, ...]
    downstream_refs: tuple[str, ...]
    reviewer_ref: str
    terminal_route: str
    authority_non_effects: tuple[str, ...] = _NO_EFFECTS


@dataclass(frozen=True, slots=True)
class InstitutionalFeatureSocketV1:
    feature_id: str
    canonical_owner: str
    field_ids: tuple[str, ...]
    type_unit_basis: str
    point_in_time_and_freshness: str
    materiality: str
    unavailable_disposition: str
    operation_ids: tuple[str, ...]
    responsible_agent: str
    downstream_consumer: str
    implements_economic_engine: bool = False

    def __post_init__(self) -> None:
        if type(self.implements_economic_engine) is not bool or (
            self.implements_economic_engine
        ):
            raise ComputationServiceError(
                ReasonCode.CAPABILITY_DENIED,
                "institutional sockets validate and route; they do not duplicate engines",
            )


AGENT_DUTY_ROUTES: tuple[AgentDutyRouteV1, ...] = (
    AgentDutyRouteV1(
        "research_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        ("ST10-OP::02", "ST10-OP::04", "ST10-OP::10", "ST10-OP::12"),
        (
            "PR165_D2_ExternalSelectionSignalCandidateRegistry",
            "PR165_D2_QKUFormulaAlgorithmComputabilityRouting",
        ),
        ("PR162D-R3::MATERIALIZATION_TASKS",),
        "governance_agent",
        "AGENT-ORCH1::TYPED_RESEARCH_WORK_ORDER_NO_WEB_EFFECT",
    ),
    AgentDutyRouteV1(
        "parameter_selector_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        ("ST10-OP::03", "ST10-OP::04", "ST10-OP::05", "ST10-OP::06"),
        (
            "PR165_D2_NetEdgeAdjustedCandidateRanking",
            "PR165_D2_ReplayPaperRetestBatchV2",
        ),
        ("PR166-S_RETEST_LOOP_V2", "PR166-SF::REPAIR_HANDOFF"),
        "governance_agent",
        "AGENT-ORCH1::EXACT_PARAMETER_BINDING_OR_CALIBRATION_BLOCKER",
    ),
    AgentDutyRouteV1(
        "risk_manager_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        (
            "ST10-OP::02",
            "ST10-OP::04",
            "ST10-OP::06",
            "ST10-OP::07",
            "ST10-OP::08",
            "ST10-OP::10",
        ),
        (
            "PR165_D2_TCADecompositionSelectionLedger",
            "PR165_D2_FalseDiscoveryOverfitSelectionControl",
        ),
        ("PRETRADE1::RISK_REVIEW", "AGENT-ORCH1::GOVERNANCE_TASK"),
        "governance_agent",
        "AGENT-ORCH1::HARD_BLOCKER_OR_REGISTERED_FALLBACK",
    ),
    AgentDutyRouteV1(
        "quantum_optimizer_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        ("ST10-OP::03", "ST10-OP::05", "ST10-OP::06", "ST10-OP::10"),
        ("PR165_D2_QuantumCandidatePriorityV2",),
        ("PR166-Q", "PR162E-Q"),
        "governance_agent",
        "PR162E-Q::STRUCTURAL_READINESS_OR_CLASSICAL_NO_TRADE",
    ),
    AgentDutyRouteV1(
        "commander_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        (
            "ST10-OP::02",
            "ST10-OP::03",
            "ST10-OP::06",
            "ST10-OP::09",
            "ST10-OP::10",
            "ST10-OP::12",
            "ST10-OP::13",
            "ST10-OP::14",
        ),
        ("PR165_D2_RouteTriageMatrix", "PR165_D2_CommandActionMatrix"),
        ("AGENT-ORCH1::SERVICE_OPERATION_DAG",),
        "governance_agent",
        "AGENT-ORCH1::DEADLINE_RETRY_QUARANTINE_OR_TERMINAL_ROUTE",
    ),
    AgentDutyRouteV1(
        "governance_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        (
            "ST10-OP::01",
            "ST10-OP::02",
            "ST10-OP::10",
            "ST10-OP::11",
            "ST10-OP::12",
            "ST10-OP::15",
        ),
        ("PR165_D2_AuthorityBoundaryAudit", "PR165_D2_OrphanArtifactAudit"),
        ("SVC1::AUDIT_READ_MODEL",),
        "governance_agent",
        "AGENT-ORCH1::PROVENANCE_RIGHTS_AND_NO_ORPHAN_AUDIT",
    ),
    AgentDutyRouteV1(
        "dashboard_agent",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        ("ST10-OP::09", "ST10-OP::10", "ST10-OP::15"),
        (
            "PR165_D2_DashboardSelectionHandoff",
            "PR165_D2_MarketSpecificSelectionIndex",
        ),
        ("SVC1::ONE_WAY_OWNER_READ_MODEL",),
        "governance_agent",
        "SVC1::OWNER_DISPLAY_NO_SECOND_STATE_STORE",
    ),
    AgentDutyRouteV1(
        "connector_venue_readiness_future_consumer",
        "PR165_D2_AgentRosterDiscoveryAudit+AgentDutySourceCrosswalk",
        "AGENT-ORCH1::AgentOrchService",
        ("ST10-OP::04", "ST10-OP::09", "ST10-OP::10", "ST10-OP::12"),
        ("PR165_D2_ConnectorVenueReadinessReferenceRouting",),
        ("PR174..PR181::TYPED_REFERENCE_ROUTES",),
        "governance_agent",
        "AGENT-ORCH1::FUTURE_HANDOFF_NO_PROVIDER_OR_WRITE",
    ),
)


INSTITUTIONAL_FEATURE_SOCKETS: tuple[InstitutionalFeatureSocketV1, ...] = (
    InstitutionalFeatureSocketV1(
        "execution_adjusted_ranking",
        "RANK4",
        ("rank_order", "rank_score"),
        "typed rank refs; owner-declared score basis",
        "version-pinned snapshot and owner TTL",
        "OPTIONAL_UNTIL_OWNER_PROJECTION_PRESENT",
        "RANK4::TYPED_UNAVAILABLE_WORK_ORDER",
        ("ST10-OP::03", "ST10-OP::07"),
        "parameter_selector_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "tca_decomposition",
        "PRETRADE1",
        ("tca_rank", "accounting_tca_view_ref"),
        "typed currency/fraction components on declared basis",
        "decision as-of and PRETRADE1 TTL",
        "MATERIAL_FOR_TRADE_PLAN_EVALUATION",
        "PRETRADE1::TCA_PREREQUISITE_UNAVAILABLE",
        ("ST10-OP::04", "ST10-OP::07", "ST10-OP::08"),
        "risk_manager_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "overfit_multiple_testing_fdr",
        "RANK4",
        ("fdr_rank", "overfit_state_ref"),
        "typed state/reference; declared hypothesis-family basis",
        "evaluation cutoff and validation-epoch TTL",
        "MATERIAL_WHEN_CERTIFIED_STACK_REQUIRES",
        "RANK4::FDR_STATE_UNAVAILABLE",
        ("ST10-OP::03", "ST10-OP::08"),
        "risk_manager_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "portfolio_diversification",
        "PRETRADE1",
        ("port_div_rank", "correlation_state_ref"),
        "typed dimensionless/correlation basis refs",
        "portfolio snapshot as-of and owner TTL",
        "MATERIAL_WHEN_PORTFOLIO_CONTEXT_REQUIRED",
        "PRETRADE1::PORTFOLIO_STATE_UNAVAILABLE",
        ("ST10-OP::03", "ST10-OP::08"),
        "risk_manager_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "capacity_crowding",
        "PRETRADE1",
        ("capacity_rank", "capacity_crowding_ref"),
        "typed quantity/currency basis refs",
        "market snapshot as-of and owner TTL",
        "MATERIAL_WHEN_CAPACITY_REQUIRED",
        "PRETRADE1::CAPACITY_STATE_UNAVAILABLE",
        ("ST10-OP::04", "ST10-OP::08"),
        "risk_manager_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "champion_challenger_no_trade_identity",
        "RANK4",
        ("champ_prev", "chall_prev", "chall_reason", "no_trade_candidate_id"),
        "canonical immutable identity refs",
        "selection input-lock and evidence epoch",
        "MATERIAL_WHEN_COMPARISON_REQUESTED",
        "RANK4::SELECTION_IDENTITY_UNAVAILABLE_OR_NO_TRADE",
        ("ST10-OP::03", "ST10-OP::07"),
        "parameter_selector_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "regime_conditioned_memory_prior",
        "MEM1",
        ("context_signature", "prior_only_score", "memory_ttl_state"),
        "typed prior/reference; never observed fact",
        "exact context signature and MEM1 TTL",
        "OPTIONAL_PRIOR_ONLY",
        "MEM1::PRIOR_UNAVAILABLE_NO_NEUTRAL_SUBSTITUTE",
        ("ST10-OP::03", "ST10-OP::10"),
        "risk_manager_agent",
        "LATER_EVIDENCE_OWNER",
    ),
    InstitutionalFeatureSocketV1(
        "portfolio_marginal_utility",
        "RANK4",
        ("marg_util_rank", "portfolio_marginal_utility_ref"),
        "typed owner-declared utility basis ref",
        "portfolio snapshot as-of and owner TTL",
        "MATERIAL_WHEN_OBJECTIVE_REQUIRES",
        "RANK4::MARGINAL_UTILITY_UNAVAILABLE",
        ("ST10-OP::03", "ST10-OP::08"),
        "risk_manager_agent",
        "TRANCHE_F_OR_POST_STEP12",
    ),
    InstitutionalFeatureSocketV1(
        "quantum_structural_readiness",
        "QOPT1+PR162E-Q",
        (
            "mapping_family",
            "converter_version",
            "original_model_feasibility",
            "classical_fallback_ref",
        ),
        "normalized objective plus economic interpret-back refs",
        "version-pinned mapping and latency/TTL state",
        "OPTIONAL_STRUCTURAL_READINESS_ONLY",
        "PR162E-Q::CLASSICAL_OR_NO_TRADE",
        ("ST10-OP::03", "ST10-OP::05", "ST10-OP::06", "ST10-OP::10"),
        "quantum_optimizer_agent",
        "POST_STEP12_QUANTUM_EVIDENCE_OWNER",
    ),
)


if (
    len(AGENT_DUTY_ROUTES) != 8
    or len({row.agent_id for row in AGENT_DUTY_ROUTES}) != 8
    or len(INSTITUTIONAL_FEATURE_SOCKETS) != 9
    or len({row.feature_id for row in INSTITUTIONAL_FEATURE_SOCKETS}) != 9
):
    raise ComputationServiceError(
        ReasonCode.INVALID_CONTRACT,
        "agent-route and institutional-socket identities must be exact and unique",
    )


def _component_graph(component_id: str) -> CompiledDependencyGraphV1:
    output = MATH_IO_CONTRACTS[component_id].outputs[0]
    return DependencyGraphCompilerV1.compile(
        (
            DependencyNodeV1(
                node_id=component_id,
                output_unit=output.unit,
                timing_class="SNAPSHOT",
                output_basis=output.basis,
                output_field_ids=tuple(
                    field.name for field in MATH_IO_CONTRACTS[component_id].outputs
                ),
                consumer_refs=_DOWNSTREAM_CONSUMERS,
            ),
        ),
        (),
    )


def _component_contract(
    component_id: str,
    context,
    *,
    dependency_graph: CompiledDependencyGraphV1 | None = None,
    parameter_ids: tuple[str, ...] = (),
) -> FormulaExecutionContractV1:
    io_contract = MATH_IO_CONTRACTS[component_id]
    binding = BindingResolverV1.build(
        binding_id=f"ST12B-BINDING::{component_id}::{context.context_id}",
        version="1.1R1",
        inputs=tuple(
            UnitBindingV1(field.name, field.unit, field.basis)
            for field in io_contract.inputs
        ),
        sources=(),
        venue_scope=(),
    )
    identity = CertifiedMathIdentityRefV1(
        component_id,
        registry_version=(
            "ST10_FROZEN_MATH_REGISTRY_V1"
            if component_id in TRANCHE_A_MATH_IDS
            else "ST12_TRANCHE_B_MATH_REGISTRY_V1_1R1"
        ),
    )
    implementation = get_math_implementation(component_id).contract
    return ComputationContractCompilerV1.compile(
        identity_binding=identity,
        implementation=implementation,
        binding=binding,
        dependency_graph=dependency_graph or _component_graph(component_id),
        oracle=get_oracle(component_id),
        golden_vector=get_golden_vector(component_id),
        context=context,
        parameter_ids=parameter_ids,
        consumer_refs=_DOWNSTREAM_CONSUMERS,
    )


def _identity_snapshot(repo_root: Path) -> tuple[IdentityViewV1, ...]:
    """Load the current RP5C owner once, then expose only typed adapter views."""

    from tools.pr168_rp5c_library_reader import load_library

    library = load_library(repo_root)
    identity_ids = tuple(
        sorted(
            str(row["identity_row_id"])
            for row in library["immutable_qku_formula_library"]
            if row.get("qku_id") or row.get("formula_id")
        )
    )
    return RP5CIdentityAdapterV1(repo_root).load_rows(identity_ids)


def _fallback_for(
    *,
    component_id: str,
    reason: ReasonCode,
    mode: str,
) -> FallbackResolutionReceiptV1 | None:
    registered = REGISTERED_FALLBACK_RESOLVER.get(
        "FALLBACK::NO_EFFECT_FAIL_CLOSED"
    )
    if reason not in registered.trigger_reason_codes:
        return None
    return REGISTERED_FALLBACK_RESOLVER.resolve(
        fallback_id=registered.fallback_id,
        source_component_id=component_id,
        trigger_reason_code=reason,
        supplied_unit="DECLARED",
        required_unit="DECLARED",
        supplied_basis="DECLARED",
        required_basis="DECLARED",
        timing_class="SNAPSHOT",
        freshness_state="UNKNOWN_FAIL_CLOSED",
        mode=mode,
        consumer_ref="QKUComputationControlPlaneServiceV1",
    )


class QKUComputationControlPlaneServiceV1:
    """The one synchronous, pure, agent-facing Tranche-B computation surface."""

    def __init__(
        self,
        *,
        repo_root: str | Path,
        conversion_registry: UnitConversionRegistryV1 = (
            EMPTY_UNIT_CONVERSION_REGISTRY
        ),
        identity_views: tuple[IdentityViewV1, ...] | None = None,
    ) -> None:
        root = Path(repo_root).resolve()
        if not root.is_dir():
            raise ComputationServiceError(
                ReasonCode.OWNER_DATA_MISSING,
                "repository root is unavailable",
            )
        self._repo_root = root
        self._stack_resolver = ApplicableStackResolverV1(repo_root=root)
        self._input_resolver = RequiredInputResolverV1(
            conversion_registry=conversion_registry
        )
        views = (
            _identity_snapshot(root)
            if identity_views is None
            else identity_views
        )
        if (
            not isinstance(views, tuple)
            or any(not isinstance(view, IdentityViewV1) for view in views)
            or len({view.identity_row_id for view in views}) != len(views)
        ):
            raise ComputationServiceError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "RP5C identity snapshot must contain unique typed views",
            )
        self._identity_views = tuple(
            sorted(views, key=lambda view: view.identity_row_id)
        )
        self._identity_index: Mapping[str, tuple[IdentityViewV1, ...]] = (
            MappingProxyType(self._build_identity_index(self._identity_views))
        )
        self._operation_by_name: Mapping[str, TrancheBServiceBindingV1] = (
            MappingProxyType(
                {
                    row.operation_name: row
                    for row in TRANCHE_B_SERVICE_BINDINGS.values()
                }
            )
        )
        if (
            len(self._operation_by_name) != 15
            or tuple(self._operation_by_name)
            != tuple(row[1] for row in _SERVICE_BINDING_ROWS)
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "the immutable service binding map must cover all 15 operations",
            )

    @staticmethod
    def _build_identity_index(
        views: tuple[IdentityViewV1, ...],
    ) -> dict[str, tuple[IdentityViewV1, ...]]:
        mutable: dict[str, list[IdentityViewV1]] = {}
        for view in views:
            for identity in (
                view.identity_row_id,
                view.qku_id,
                view.formula_id,
            ):
                if identity:
                    mutable.setdefault(identity, []).append(view)
        return {
            key: tuple(sorted(value, key=lambda view: view.identity_row_id))
            for key, value in mutable.items()
        }

    @property
    def service_bindings(self) -> Mapping[str, TrancheBServiceBindingV1]:
        return TRANCHE_B_SERVICE_BINDINGS

    @property
    def rp5e_owner_run_id(self) -> str:
        return self._stack_resolver.rp5e_snapshot.run_id

    @property
    def identity_snapshot_count(self) -> int:
        return len(self._identity_views)

    def execute(
        self,
        request: OperationRequestEnvelopeV1,
        **typed_evidence: object,
    ) -> OperationResponseEnvelopeV1:
        if not isinstance(request, OperationRequestEnvelopeV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "service request must be a typed operation envelope",
            )
        try:
            binding = self._operation_by_name[request.operation_name]
        except KeyError as exc:
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "operation is not present in the immutable service-binding map",
            ) from exc
        method = getattr(self, binding.service_method)
        return method(request, **typed_evidence)

    def resolve_identity(
        self,
        request: ResolveIdentityRequestV1,
    ) -> ResolveIdentityResponseV1:
        if not isinstance(request, ResolveIdentityRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "resolve_identity requires its exact typed request",
            )
        query_fields = request.identity_query.fields
        if any(
            field.kind is not TypedValueKindV1.TEXT
            or field.unit != "identity"
            or field.basis != "canonical"
            for field in query_fields
        ):
            reasons = (OperationBlockerCodeV1.INVALID_REQUEST,)
            matches: tuple[IdentityViewV1, ...] = ()
        else:
            values = tuple(str(field.value) for field in query_fields)
            owner_matches = tuple(
                dict.fromkeys(
                    view
                    for value in values
                    for view in self._identity_index.get(value, ())
                )
            )
            math_matches = tuple(
                value for value in values if value in MATH_IO_CONTRACTS
            )
            reasons = (
                ()
                if len(owner_matches) + len(math_matches) == 1
                else (OperationBlockerCodeV1.IDENTITY_UNVERIFIED,)
            )
            matches = owner_matches
        evidence_refs = tuple(
            dict.fromkeys(
                (
                    *(
                        f"RP5C::{view.identity_row_id}::{view.library_version}"
                        for view in matches
                    ),
                    *(
                        f"QKUComputationControlPlaneV1::{math_id}::"
                        f"{get_math_implementation(math_id).contract.specification_version}"
                        for math_id in (
                            str(field.value)
                            for field in query_fields
                            if str(field.value) in MATH_IO_CONTRACTS
                        )
                    ),
                )
            )
        )
        result = IdentityResolutionV1(
            result_id=_result_id(request),
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::CANONICAL_IDENTITY"
                if not reasons
                else "governance_agent::IDENTITY_RECONCILIATION"
            ),
            evidence_refs=evidence_refs,
        )
        return ResolveIdentityResponseV1(
            **_response_common(
                request,
                status=(
                    OperationStatusV1.SUCCEEDED
                    if not reasons
                    else OperationStatusV1.BLOCKED
                ),
                blockers=reasons,
                receipt_refs=evidence_refs,
            ),
            identity_resolution=result,
        )

    def _resolve_inputs(
        self,
        *,
        component_id: str,
        context,
        supplied_values: TypedValueRecordV1 | None,
        contextual_evidence: tuple[ContextualInputValueV1, ...],
        dependency_graph: CompiledDependencyGraphV1 | None = None,
        dependency_refs: tuple[str, ...] = (),
        parameter_ids: tuple[str, ...] = (),
    ) -> tuple[FormulaExecutionContractV1, InputResolutionReceiptV1]:
        contract = _component_contract(
            component_id,
            context,
            dependency_graph=dependency_graph,
            parameter_ids=parameter_ids,
        )
        if supplied_values is None:
            receipt = self._input_resolver.unresolved_requirements(
                component_id=component_id,
                context=context,
                dependency_refs=dependency_refs,
                parameter_policy_refs=parameter_ids,
                downstream_consumer_refs=_DOWNSTREAM_CONSUMERS,
            )
        else:
            receipt = self._input_resolver.resolve(
                component_id=component_id,
                context=context,
                supplied_values=supplied_values,
                contextual_evidence=contextual_evidence,
                formula_contract=contract,
                dependency_refs=dependency_refs,
                downstream_consumer_refs=_DOWNSTREAM_CONSUMERS,
            )
        return contract, receipt

    def resolve_required_inputs(
        self,
        request: ResolveRequiredInputsRequestV1,
        *,
        supplied_values_by_component: Mapping[
            str, TypedValueRecordV1
        ] | None = None,
        contextual_evidence_by_component: Mapping[
            str, tuple[ContextualInputValueV1, ...]
        ] | None = None,
    ) -> ResolveRequiredInputsResponseV1:
        if not isinstance(request, ResolveRequiredInputsRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "resolve_required_inputs requires its exact typed request",
            )
        values = supplied_values_by_component or {}
        evidence = contextual_evidence_by_component or {}
        receipts: list[InputResolutionReceiptV1] = []
        reasons: list[ReasonCode] = []
        for component_id in request.component_ids:
            _, receipt = self._resolve_inputs(
                component_id=component_id,
                context=request.context,
                supplied_values=values.get(component_id),
                contextual_evidence=evidence.get(component_id, ()),
            )
            receipts.append(receipt)
            reasons.extend(receipt.blocker_codes)
        aggregate = tuple(dict.fromkeys(reasons))
        result = DetailedInputResolutionV1(
            result_id=_result_id(request),
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::TYPED_INPUTS"
                if not aggregate
                else "research_agent::INPUT_MATERIALIZATION_WORK_ORDER"
            ),
            evidence_refs=tuple(receipt.receipt_id for receipt in receipts),
            component_receipts=tuple(receipts),
        )
        blockers = _operation_blockers(aggregate)
        return ResolveRequiredInputsResponseV1(
            **_response_common(
                request,
                status=(
                    OperationStatusV1.SUCCEEDED
                    if not blockers
                    else OperationStatusV1.BLOCKED
                ),
                blockers=blockers,
                receipt_refs=result.evidence_refs,
            ),
            input_resolution=result,
        )

    def resolve_contextual_computability(
        self,
        request: ResolveContextualComputabilityRequestV1,
        *,
        supplied_values: TypedValueRecordV1 | None = None,
        contextual_evidence: tuple[ContextualInputValueV1, ...] = (),
        stack_resolution: ApplicableStackResolutionReceiptV1 | None = None,
    ) -> ResolveContextualComputabilityResponseV1:
        if not isinstance(request, ResolveContextualComputabilityRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "computability resolution requires its exact typed request",
            )
        contract, input_receipt = self._resolve_inputs(
            component_id=request.component_id,
            context=request.context,
            supplied_values=supplied_values,
            contextual_evidence=contextual_evidence,
            dependency_graph=(
                None
                if stack_resolution is None
                else stack_resolution.compiled_graph
            ),
            dependency_refs=(
                ()
                if stack_resolution is None
                else (stack_resolution.receipt_id,)
            ),
        )
        receipt = EvidenceDerivedContextualComputabilityResolverV1.resolve(
            contract=contract,
            input_resolution=input_receipt,
            stack_resolution=stack_resolution,
            consumer_refs=_DOWNSTREAM_CONSUMERS,
        )
        required_states = {
            state: getattr(
                receipt.resolution,
                {
                    ComputabilityClassV1.SPECIFICATION_COMPUTABLE: "specification",
                    ComputabilityClassV1.FIXTURE_COMPUTABLE: "fixture",
                    ComputabilityClassV1.CONTEXT_COMPUTABLE: "context",
                    ComputabilityClassV1.STACK_COMPUTABLE: "stack",
                }[state],
            )
            for state in request.required_computability_classes
        }
        blockers = (
            ()
            if all(state.computable for state in required_states.values())
            else _operation_blockers(
                receipt.blocker_reason_codes
                or (ReasonCode.STACK_NOT_COMPUTABLE,)
            )
        )
        return ResolveContextualComputabilityResponseV1(
            **_response_common(
                request,
                status=(
                    OperationStatusV1.SUCCEEDED
                    if not blockers
                    else OperationStatusV1.BLOCKED
                ),
                blockers=blockers,
                receipt_refs=(receipt.receipt_id,),
            ),
            computability=receipt.resolution,
        )

    def resolve_applicable_stack(
        self,
        request: ResolveApplicableStackRequestV1,
        *,
        applicability: StackApplicabilityContextV1,
    ) -> ResolveApplicableStackResponseV1:
        if (
            not isinstance(request, ResolveApplicableStackRequestV1)
            or not isinstance(applicability, StackApplicabilityContextV1)
            or applicability.trade_plan_candidate_id
            != request.trade_plan_candidate_id
            or applicability.context_key != request.context
            or applicability.required_roles != request.required_launch_roles
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "stack request and typed applicability evidence must be exact",
            )
        receipt = self._stack_resolver.resolve(applicability)
        result = DetailedStackResolutionV1(
            result_id=_result_id(request),
            terminal_route=receipt.terminal_route,
            evidence_refs=(
                receipt.receipt_id,
                *receipt.rp5e_consumed_refs,
                *receipt.retained_evidence_refs,
            ),
            selected_stack_id=receipt.selected_stack_id,
            component_ids=receipt.component_ids,
            topological_order=receipt.compiled_graph.topological_order,
            resolution_receipt=receipt,
        )
        return ResolveApplicableStackResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=(receipt.receipt_id,),
            ),
            stack_resolution=result,
        )

    def _compute_component_result(
        self,
        request: ComputeComponentRequestV1,
        *,
        contextual_evidence: tuple[ContextualInputValueV1, ...],
        controls: ComponentExecutionControlsV1,
        dependency_graph: CompiledDependencyGraphV1 | None = None,
        stack_resolution: ApplicableStackResolutionReceiptV1 | None = None,
        dependency_refs: tuple[str, ...] = (),
        parameter_ids: tuple[str, ...] = (),
        deadline_budget: DeadlineBudgetV1 | None = None,
        mode: str = "CONTRACT_ONLY",
    ) -> ComponentComputationResultV1:
        contract, input_receipt = self._resolve_inputs(
            component_id=request.component_id,
            context=request.context,
            supplied_values=request.input_values,
            contextual_evidence=contextual_evidence,
            dependency_graph=dependency_graph,
            dependency_refs=dependency_refs,
            parameter_ids=parameter_ids,
        )
        computability = (
            EvidenceDerivedContextualComputabilityResolverV1.resolve(
                contract=contract,
                input_resolution=input_receipt,
                stack_resolution=stack_resolution,
                consumer_refs=_DOWNSTREAM_CONSUMERS,
            )
        )
        reasons: list[ReasonCode] = list(input_receipt.blocker_codes)
        if request.expected_output_schema_ref != output_schema_ref(
            request.component_id
        ):
            reasons.append(ReasonCode.OUTPUT_SCHEMA_MISMATCH)
        deadline_receipt: DeadlineReceiptV1 | None = None
        if deadline_budget is not None:
            deadline_receipt = DeadlineResolverV1.resolve(deadline_budget)
            reasons.extend(deadline_receipt.blocker_codes)
        if not computability.resolution.stack.computable:
            reasons.extend(computability.blocker_reason_codes)
            if not reasons:
                reasons.append(ReasonCode.STACK_NOT_COMPUTABLE)
        reasons_tuple = tuple(dict.fromkeys(reasons))
        if reasons_tuple:
            fallback = _fallback_for(
                component_id=request.component_id,
                reason=reasons_tuple[0],
                mode=mode,
            )
            evidence_refs = tuple(
                dict.fromkeys(
                    (
                        input_receipt.receipt_id,
                        computability.receipt_id,
                        *(
                            ()
                            if deadline_receipt is None
                            else (deadline_receipt.receipt_id,)
                        ),
                        *((fallback.receipt_id,) if fallback else ()),
                    )
                )
            )
            return ComponentComputationResultV1(
                result_id=_id(
                    "COMPONENT-RESULT",
                    request.idempotency_key,
                    request.component_id,
                    input_receipt.receipt_id,
                ),
                terminal_route=(
                    fallback.resolved_target
                    if fallback is not None
                    else "AGENT-ORCH1::TYPED_COMPONENT_REMEDIATION"
                ),
                evidence_refs=evidence_refs,
                component_id=request.component_id,
                input_resolution_receipt=input_receipt,
                computability_receipt=computability,
                fallback_receipt=fallback,
                blocker_reason_codes=reasons_tuple,
            )

        try:
            raw_output = _invoke_registered_callable(
                request.component_id,
                input_receipt.arguments,
                controls,
            )
            output_values = _typed_output(request.component_id, raw_output)
            if deadline_budget is not None:
                deadline_receipt = DeadlineResolverV1.resolve(deadline_budget)
                if not deadline_receipt.within_budget:
                    raise ComputationServiceError(
                        ReasonCode.DEADLINE_EXHAUSTED,
                        "component execution exhausted its monotonic deadline",
                    )
        except ComputationControlPlaneError as exc:
            fallback = _fallback_for(
                component_id=request.component_id,
                reason=exc.reason_code,
                mode=mode,
            )
            evidence_refs = tuple(
                dict.fromkeys(
                    (
                        input_receipt.receipt_id,
                        computability.receipt_id,
                        *(
                            ()
                            if deadline_receipt is None
                            else (deadline_receipt.receipt_id,)
                        ),
                        *((fallback.receipt_id,) if fallback else ()),
                    )
                )
            )
            return ComponentComputationResultV1(
                result_id=_id(
                    "COMPONENT-RESULT",
                    request.idempotency_key,
                    request.component_id,
                    input_receipt.receipt_id,
                    exc.reason_code.value,
                ),
                terminal_route=(
                    fallback.resolved_target
                    if fallback is not None
                    else "AGENT-ORCH1::TYPED_COMPONENT_REMEDIATION"
                ),
                evidence_refs=evidence_refs,
                component_id=request.component_id,
                input_resolution_receipt=input_receipt,
                computability_receipt=computability,
                fallback_receipt=fallback,
                blocker_reason_codes=(exc.reason_code,),
            )

        implementation = get_math_implementation(request.component_id).contract
        execution = TrancheBComputationExecutionReceiptV1(
            receipt_id=_id(
                "EXECUTION",
                request.component_id,
                input_receipt.receipt_id,
                deterministic_json(output_values),
            ),
            specification_id=contract.specification_ref,
            implementation_id=implementation.implementation_id,
            input_version=request.context.input_version,
            output_json=deterministic_json(output_values),
            input_json=deterministic_json(input_receipt.arguments),
            callable_version=implementation.specification_version,
            output_schema_ref=request.expected_output_schema_ref,
            input_receipt_ref=input_receipt.receipt_id,
            computability_receipt_ref=computability.receipt_id,
            point_in_time_receipt_refs=tuple(
                row.point_in_time_receipt.receipt_id
                for row in input_receipt.inputs
                if row.point_in_time_receipt is not None
            ),
            freshness_receipt_refs=tuple(
                row.freshness_receipt.receipt_id
                for row in input_receipt.inputs
                if row.freshness_receipt is not None
            ),
            conversion_receipt_refs=tuple(
                row.conversion_receipt.receipt_id
                for row in input_receipt.inputs
                if row.conversion_receipt is not None
            ),
            dependency_receipt_refs=dependency_refs,
            deadline_receipt_ref=(
                None
                if deadline_receipt is None
                else deadline_receipt.receipt_id
            ),
            consumer_refs=_DOWNSTREAM_CONSUMERS,
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::PURE_COMPONENT_RESULT"
            ),
        )
        return ComponentComputationResultV1(
            result_id=_id(
                "COMPONENT-RESULT",
                request.idempotency_key,
                request.component_id,
                execution.receipt_id,
            ),
            terminal_route=execution.terminal_route,
            evidence_refs=(
                input_receipt.receipt_id,
                computability.receipt_id,
                execution.receipt_id,
            ),
            component_id=request.component_id,
            output_values=output_values,
            input_resolution_receipt=input_receipt,
            computability_receipt=computability,
            execution_receipt=execution,
        )

    def compute_component(
        self,
        request: ComputeComponentRequestV1,
        *,
        contextual_evidence: tuple[ContextualInputValueV1, ...],
        controls: ComponentExecutionControlsV1 = ComponentExecutionControlsV1(),
        parameter_ids: tuple[str, ...] = (),
        deadline_budget: DeadlineBudgetV1 | None = None,
        mode: str = "CONTRACT_ONLY",
    ) -> ComputeComponentResponseV1:
        if (
            not isinstance(request, ComputeComponentRequestV1)
            or not isinstance(controls, ComponentExecutionControlsV1)
            or not isinstance(contextual_evidence, tuple)
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "compute_component requires exact typed request and evidence",
            )
        result = self._compute_component_result(
            request,
            contextual_evidence=contextual_evidence,
            controls=controls,
            parameter_ids=parameter_ids,
            deadline_budget=deadline_budget,
            mode=mode,
        )
        blockers = _operation_blockers(result.blocker_reason_codes)
        receipt_refs = tuple(
            dict.fromkeys(
                (
                    *result.evidence_refs,
                    *(
                        ()
                        if result.execution_receipt is None
                        else (result.execution_receipt.receipt_id,)
                    ),
                )
            )
        )
        return ComputeComponentResponseV1(
            **_response_common(
                request,
                status=(
                    OperationStatusV1.SUCCEEDED
                    if not blockers
                    else OperationStatusV1.BLOCKED
                ),
                blockers=blockers,
                receipt_refs=receipt_refs,
            ),
            component_result=result,
        )

    @staticmethod
    def _derived_edge_input(
        *,
        edge,
        upstream_result: ComponentComputationResultV1,
        upstream_evidence: tuple[ContextualInputValueV1, ...],
        context,
    ) -> tuple[TypedValueV1, ContextualInputValueV1, str]:
        if (
            upstream_result.output_values is None
            or upstream_result.execution_receipt is None
        ):
            raise ComputationServiceError(
                ReasonCode.STACK_NOT_COMPUTABLE,
                "a material dependency has no executed upstream output",
            )
        upstream_fields = {
            field.name: field for field in upstream_result.output_values.fields
        }
        try:
            supplied = upstream_fields[edge.upstream_output_field]
        except KeyError as exc:
            raise ComputationServiceError(
                ReasonCode.OUTPUT_SCHEMA_MISMATCH,
                "dependency edge names an absent upstream output field",
            ) from exc
        downstream_field = next(
            field
            for field in MATH_IO_CONTRACTS[edge.downstream_id].inputs
            if field.name == edge.downstream_input_field
        )
        normalized = downstream_field.type_name.casefold()
        if normalized == "float64":
            if supplied.kind is TypedValueKindV1.DECIMAL:
                numeric = finite_float(
                    canonical_probability_decimal(
                        supplied.value,
                        field_name=edge.downstream_input_field,
                    ),
                    field_name=edge.downstream_input_field,
                )
                conversion_class = (
                    "DECLARED_DECIMAL_TO_FLOAT64_METHOD_BOUNDARY"
                )
            elif supplied.kind is TypedValueKindV1.FLOAT64:
                numeric = finite_float(
                    supplied.value,
                    field_name=edge.downstream_input_field,
                )
                conversion_class = "IDENTITY_FLOAT64_BOUNDARY"
            else:
                raise ComputationServiceError(
                    ReasonCode.INPUT_TYPE_MISMATCH,
                    "dependency output cannot satisfy downstream float64 schema",
                )
            routed_value = TypedValueV1(
                edge.downstream_input_field,
                TypedValueKindV1.FLOAT64,
                numeric,
                downstream_field.unit,
                downstream_field.basis,
            )
        elif normalized == "decimal" and supplied.kind is TypedValueKindV1.DECIMAL:
            routed_value = TypedValueV1(
                edge.downstream_input_field,
                TypedValueKindV1.DECIMAL,
                supplied.value,
                downstream_field.unit,
                downstream_field.basis,
            )
            conversion_class = "IDENTITY_DECIMAL_BOUNDARY"
        else:
            raise ComputationServiceError(
                ReasonCode.INPUT_TYPE_MISMATCH,
                "dependency output type has no registered downstream method boundary",
            )
        if (
            supplied.unit != edge.supplied_unit
            or supplied.basis != edge.supplied_basis
            or routed_value.unit != edge.required_unit
            or routed_value.basis != edge.required_basis
        ):
            raise ComputationServiceError(
                ReasonCode.DEPENDENCY_UNIT_MISMATCH,
                "routed edge units or bases differ from the compiled graph",
            )
        if not upstream_evidence:
            raise ComputationServiceError(
                ReasonCode.POINT_IN_TIME_UNAVAILABLE,
                "derived dependency requires its material upstream evidence",
            )
        pit_rows = tuple(item.point_in_time for item in upstream_evidence)
        ttl_values = tuple(
            item.freshness_policy.ttl for item in upstream_evidence
        )
        derived_ttl = (
            None
            if any(value is None for value in ttl_values)
            else min(value for value in ttl_values if value is not None)
        )
        execution_ref = upstream_result.execution_receipt.receipt_id
        edge_ref = (
            f"EDGE::{edge.upstream_id}.{edge.upstream_output_field}->"
            f"{edge.downstream_id}.{edge.downstream_input_field}::"
            f"{conversion_class}::{execution_ref}"
        )
        pit = PointInTimeEvidenceV1(
            evidence_id=edge_ref,
            field_id=edge.downstream_input_field,
            field_class=PointInTimeFieldClassV1.OBSERVATION,
            observed_time=max(row.observed_time for row in pit_rows),
            effective_time=max(row.effective_time for row in pit_rows),
            source_available_time=max(
                row.source_available_time for row in pit_rows
            ),
            strategy_available_time=max(
                row.strategy_available_time for row in pit_rows
            ),
            received_time=max(row.received_time for row in pit_rows),
            processed_time=max(row.processed_time for row in pit_rows),
            as_of_time=context.as_of,
            source_epoch_id=context.source_epoch_id,
            source_revision_id=execution_ref,
        )
        freshness = FreshnessPolicyV1(
            policy_id=f"DERIVED-MATERIAL-MIN-TTL::{edge_ref}",
            ttl=derived_ttl,
            parameter_policy_ref="DERIVED_FROM_MATERIAL_UPSTREAM_TTL_POLICIES",
            stale_behavior="FAIL_CLOSED_OR_REGISTERED_FALLBACK",
        )
        evidence = ContextualInputValueV1(
            typed_value=routed_value,
            point_in_time=pit,
            freshness_policy=freshness,
            source_identity=(
                "QKUComputationControlPlaneServiceV1::REGISTERED_CALLABLE_OUTPUT"
            ),
            source_state_id=execution_ref,
            source_epoch_id=context.source_epoch_id,
            rights_state="IN_PROCESS_DERIVED_NO_RIGHTS_EXPANSION",
            value_lineage_ref=edge_ref,
            precision_policy=conversion_class,
            rounding_policy="NO_IMPLICIT_QUANTIZATION",
            producer_ref=edge.upstream_id,
            consumer_refs=(
                edge.downstream_id,
                "QKUComputationControlPlaneServiceV1",
            ),
            fallback_ref="FALLBACK::NO_EFFECT_FAIL_CLOSED",
        )
        return routed_value, evidence, edge_ref

    def compute_stack(
        self,
        request: ComputeStackRequestV1,
        *,
        applicability: StackApplicabilityContextV1,
        contextual_evidence: tuple[ContextualInputValueV1, ...],
        controls_by_component: Mapping[
            str, ComponentExecutionControlsV1
        ] | None = None,
        parameter_ids_by_component: Mapping[str, tuple[str, ...]] | None = None,
        deadline_budget: DeadlineBudgetV1 | None = None,
    ) -> ComputeStackResponseV1:
        if (
            not isinstance(request, ComputeStackRequestV1)
            or not isinstance(applicability, StackApplicabilityContextV1)
            or not isinstance(contextual_evidence, tuple)
            or applicability.context_key != request.context
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "compute_stack requires exact typed request, context, and evidence",
            )
        stack_resolution = self._stack_resolver.resolve(applicability)
        template = self._stack_resolver.template(stack_resolution.template_id)
        initial_reasons: list[ReasonCode] = []
        if request.stack_id not in {
            stack_resolution.template_id,
            stack_resolution.selected_stack_id,
        }:
            initial_reasons.append(ReasonCode.STACK_NOT_APPLICABLE)
        if request.component_ids != stack_resolution.component_ids:
            initial_reasons.append(ReasonCode.STACK_NOT_COMPUTABLE)
        external_names = tuple(
            field_name
            for _, field_name in stack_resolution.external_input_fields
        )
        if len(external_names) != len(set(external_names)):
            initial_reasons.append(ReasonCode.STACK_NOT_COMPUTABLE)
        supplied_names = tuple(field.name for field in request.input_values.fields)
        evidence_names = tuple(
            item.typed_value.name for item in contextual_evidence
        )
        if set(supplied_names) != set(external_names):
            initial_reasons.append(ReasonCode.REQUIRED_INPUT_MISSING)
        if set(evidence_names) != set(external_names):
            initial_reasons.append(ReasonCode.REQUIRED_INPUT_MISSING)
        deadline_receipt: DeadlineReceiptV1 | None = None
        if deadline_budget is not None:
            deadline_receipt = DeadlineResolverV1.resolve(deadline_budget)
            initial_reasons.extend(deadline_receipt.blocker_codes)
        if initial_reasons:
            reasons = tuple(dict.fromkeys(initial_reasons))
            fallback = _fallback_for(
                component_id=stack_resolution.component_ids[0],
                reason=reasons[0],
                mode=applicability.mode,
            )
            result = StackComputationResultV1(
                result_id=_id(
                    "STACK-RESULT",
                    request.idempotency_key,
                    stack_resolution.selected_stack_id,
                    *(reason.value for reason in reasons),
                ),
                terminal_route=(
                    fallback.resolved_target
                    if fallback is not None
                    else "AGENT-ORCH1::TYPED_STACK_REMEDIATION_DAG"
                ),
                evidence_refs=tuple(
                    dict.fromkeys(
                        (
                            stack_resolution.receipt_id,
                            *(
                                ()
                                if deadline_receipt is None
                                else (deadline_receipt.receipt_id,)
                            ),
                            *((fallback.receipt_id,) if fallback else ()),
                        )
                    )
                ),
                selected_stack_id=stack_resolution.selected_stack_id,
                blocker_reason_codes=reasons,
            )
            blockers = _operation_blockers(reasons)
            return ComputeStackResponseV1(
                **_response_common(
                    request,
                    status=OperationStatusV1.BLOCKED,
                    blockers=blockers,
                    receipt_refs=result.evidence_refs,
                ),
                stack_result=result,
            )

        controls_map = controls_by_component or {}
        parameter_map = parameter_ids_by_component or {}
        external_values = {
            field.name: field for field in request.input_values.fields
        }
        external_evidence = {
            item.typed_value.name: item for item in contextual_evidence
        }
        routed_values: dict[tuple[str, str], TypedValueV1] = {}
        routed_evidence: dict[
            tuple[str, str], ContextualInputValueV1
        ] = {}
        component_results: list[ComponentComputationResultV1] = []
        component_evidence: dict[
            str, tuple[ContextualInputValueV1, ...]
        ] = {}
        edge_consumption_refs: list[str] = []
        failed_components: list[str] = []

        for component_id in stack_resolution.compiled_graph.topological_order:
            io_contract = MATH_IO_CONTRACTS[component_id]
            fields: list[TypedValueV1] = []
            evidence_rows: list[ContextualInputValueV1] = []
            for field in io_contract.inputs:
                key = (component_id, field.name)
                if key in routed_values:
                    fields.append(routed_values[key])
                    evidence_rows.append(routed_evidence[key])
                elif field.name in external_values:
                    fields.append(external_values[field.name])
                    evidence_rows.append(external_evidence[field.name])
            component_evidence[component_id] = tuple(evidence_rows)
            component_request = ComputeComponentRequestV1(
                request_id=f"{request.request_id}::{component_id}",
                operation_name="compute_component",
                requested_at=request.requested_at,
                principal_id=request.principal_id,
                capability_bundle_id=request.capability_bundle_id,
                context=request.context,
                idempotency_key=(
                    f"{request.idempotency_key}::COMPONENT::{component_id}"
                ),
                traceparent=request.traceparent,
                tracestate=request.tracestate,
                component_id=component_id,
                input_values=TypedValueRecordV1(tuple(fields)),
                expected_output_schema_ref=output_schema_ref(component_id),
            )
            incoming_edge_refs = tuple(
                ref
                for ref in edge_consumption_refs
                if f"->{component_id}." in ref
            )
            result = self._compute_component_result(
                component_request,
                contextual_evidence=tuple(evidence_rows),
                controls=controls_map.get(
                    component_id,
                    ComponentExecutionControlsV1(),
                ),
                dependency_graph=stack_resolution.compiled_graph,
                stack_resolution=stack_resolution,
                dependency_refs=(
                    stack_resolution.receipt_id,
                    *incoming_edge_refs,
                ),
                parameter_ids=parameter_map.get(component_id, ()),
                deadline_budget=deadline_budget,
                mode=applicability.mode,
            )
            component_results.append(result)
            if result.blocker_reason_codes:
                failed_components.append(component_id)
                break

            for edge in stack_resolution.compiled_graph.edges:
                if edge.upstream_id != component_id:
                    continue
                routed, derived, edge_ref = self._derived_edge_input(
                    edge=edge,
                    upstream_result=result,
                    upstream_evidence=component_evidence[component_id],
                    context=request.context,
                )
                routed_values[
                    (edge.downstream_id, edge.downstream_input_field)
                ] = routed
                routed_evidence[
                    (edge.downstream_id, edge.downstream_input_field)
                ] = derived
                edge_consumption_refs.append(edge_ref)

        if failed_components:
            impacted = stack_resolution.compiled_graph.propagate_failures(
                tuple(failed_components)
            )
            first_failure = next(
                item
                for item in component_results
                if item.blocker_reason_codes
            )
            reasons = tuple(
                dict.fromkeys(
                    (
                        *first_failure.blocker_reason_codes,
                        ReasonCode.STACK_NOT_COMPUTABLE,
                    )
                )
            )
            fallback = first_failure.fallback_receipt or _fallback_for(
                component_id=failed_components[0],
                reason=reasons[0],
                mode=applicability.mode,
            )
            evidence_refs = tuple(
                dict.fromkeys(
                    (
                        stack_resolution.receipt_id,
                        *(item.result_id for item in component_results),
                        *edge_consumption_refs,
                        *(f"IMPACTED::{item}" for item in impacted),
                        *((fallback.receipt_id,) if fallback else ()),
                    )
                )
            )
            stack_result = StackComputationResultV1(
                result_id=_id(
                    "STACK-RESULT",
                    request.idempotency_key,
                    stack_resolution.selected_stack_id,
                    *(reason.value for reason in reasons),
                ),
                terminal_route=(
                    fallback.resolved_target
                    if fallback is not None
                    else "AGENT-ORCH1::TYPED_STACK_REMEDIATION_DAG"
                ),
                evidence_refs=evidence_refs,
                selected_stack_id=stack_resolution.selected_stack_id,
                component_results=tuple(component_results),
                blocker_reason_codes=reasons,
            )
            return ComputeStackResponseV1(
                **_response_common(
                    request,
                    status=OperationStatusV1.BLOCKED,
                    blockers=_operation_blockers(reasons),
                    receipt_refs=evidence_refs,
                ),
                stack_result=stack_result,
            )

        if deadline_budget is not None:
            deadline_receipt = DeadlineResolverV1.resolve(deadline_budget)
            if not deadline_receipt.within_budget:
                reasons = (ReasonCode.DEADLINE_EXHAUSTED,)
                fallback = _fallback_for(
                    component_id=stack_resolution.component_ids[-1],
                    reason=reasons[0],
                    mode=applicability.mode,
                )
                stack_result = StackComputationResultV1(
                    result_id=_id(
                        "STACK-RESULT",
                        request.idempotency_key,
                        stack_resolution.selected_stack_id,
                        reasons[0].value,
                    ),
                    terminal_route=(
                        fallback.resolved_target
                        if fallback is not None
                        else "commander_agent::DEADLINE_REMEDIATION"
                    ),
                    evidence_refs=tuple(
                        dict.fromkeys(
                            (
                                stack_resolution.receipt_id,
                                deadline_receipt.receipt_id,
                                *(
                                    (fallback.receipt_id,)
                                    if fallback
                                    else ()
                                ),
                            )
                        )
                    ),
                    selected_stack_id=stack_resolution.selected_stack_id,
                    component_results=tuple(component_results),
                    blocker_reason_codes=reasons,
                )
                return ComputeStackResponseV1(
                    **_response_common(
                        request,
                        status=OperationStatusV1.BLOCKED,
                        blockers=_operation_blockers(reasons),
                        receipt_refs=stack_result.evidence_refs,
                    ),
                    stack_result=stack_result,
                )

        final_result = component_results[-1]
        assert (
            final_result.output_values is not None
            and final_result.execution_receipt is not None
        )
        stack_receipt = StackExecutionReceiptV1(
            receipt_id=_id(
                "STACK-EXECUTION",
                stack_resolution.selected_stack_id,
                *(
                    item.execution_receipt.receipt_id
                    for item in component_results
                    if item.execution_receipt is not None
                ),
                *edge_consumption_refs,
            ),
            selected_stack_id=stack_resolution.selected_stack_id,
            component_receipt_refs=tuple(
                item.execution_receipt.receipt_id
                for item in component_results
                if item.execution_receipt is not None
            ),
            topological_order=(
                stack_resolution.compiled_graph.topological_order
            ),
            edge_consumption_refs=tuple(edge_consumption_refs),
            final_output_json=deterministic_json(
                final_result.output_values
            ),
            dependency_graph_ref=stack_resolution.receipt_id,
            fallback_receipt_ref=None,
            consumer_refs=_DOWNSTREAM_CONSUMERS,
            terminal_route=(
                "QKUComputationControlPlaneServiceV1::PURE_STACK_RESULT"
            ),
        )
        stack_result = StackComputationResultV1(
            result_id=_id(
                "STACK-RESULT",
                request.idempotency_key,
                stack_receipt.receipt_id,
            ),
            terminal_route=stack_receipt.terminal_route,
            evidence_refs=(
                stack_resolution.receipt_id,
                stack_receipt.receipt_id,
                *edge_consumption_refs,
            ),
            selected_stack_id=stack_resolution.selected_stack_id,
            component_results=tuple(component_results),
            output_values=final_result.output_values,
            execution_receipt=stack_receipt,
        )
        return ComputeStackResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=stack_result.evidence_refs,
            ),
            stack_result=stack_result,
        )

    def compare_with_no_trade(
        self,
        request: CompareWithNoTradeRequestV1,
    ) -> CompareWithNoTradeResponseV1:
        if not isinstance(request, CompareWithNoTradeRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "compare_with_no_trade requires its exact typed request",
            )
        blocker = OperationBlockerCodeV1.DOWNSTREAM_PREREQUISITE_UNAVAILABLE
        comparison = NoTradeComparisonV1(
            result_id=_result_id(request),
            terminal_route=(
                "PRETRADE1::SAME_BASIS_TCA_RISK_CASH_COMPARISON_REQUIRED"
            ),
            evidence_refs=(
                request.trade_plan_candidate_id,
                request.no_trade_candidate_id,
                request.comparison_basis,
            ),
        )
        return CompareWithNoTradeResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.BLOCKED,
                blockers=(blocker,),
                receipt_refs=comparison.evidence_refs,
            ),
            comparison=comparison,
        )

    def evaluate_trade_plan(
        self,
        request: EvaluateTradePlanRequestV1,
    ) -> EvaluateTradePlanResponseV1:
        if not isinstance(request, EvaluateTradePlanRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "evaluate_trade_plan requires its exact typed request",
            )
        blocker = OperationBlockerCodeV1.DOWNSTREAM_PREREQUISITE_UNAVAILABLE
        evaluation = TradePlanEvaluationV1(
            result_id=_result_id(request),
            terminal_route=(
                "PRETRADE1::VALIDATE_TCA_RISK_CASH_AND_NO_TRADE_PREREQUISITES"
            ),
            evidence_refs=(
                request.trade_plan_candidate_id,
                request.stack_id,
                request.accounting_tca_view_ref,
                request.risk_cash_state_ref,
                request.no_trade_candidate_id,
            ),
        )
        return EvaluateTradePlanResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.BLOCKED,
                blockers=(blocker,),
                receipt_refs=evaluation.evidence_refs,
            ),
            evaluation=evaluation,
        )

    def get_snapshot_view(
        self,
        request: GetSnapshotViewRequestV1,
    ) -> GetSnapshotViewResponseV1:
        if not isinstance(request, GetSnapshotViewRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "get_snapshot_view requires its exact typed request",
            )
        snapshot = SnapshotViewV1(
            result_id=_result_id(request),
            terminal_route="HOTPATH::LATER_SNAPSHOT_CANDIDATE_HANDOFF_ONLY",
            evidence_refs=(request.snapshot_id, request.view_class),
        )
        return GetSnapshotViewResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.BLOCKED,
                blockers=(
                    OperationBlockerCodeV1.DOWNSTREAM_PREREQUISITE_UNAVAILABLE,
                ),
                receipt_refs=snapshot.evidence_refs,
            ),
            snapshot_view=snapshot,
        )

    def explain_resolution(
        self,
        request: ExplainResolutionRequestV1,
        *,
        resolution: ComponentComputationResultV1
        | StackComputationResultV1
        | None = None,
        owner_preferences_and_candidate_assertions: tuple[str, ...] = (),
        typed_agent_disagreements: tuple[str, ...] = (),
    ) -> ExplainResolutionResponseV1:
        if (
            not isinstance(request, ExplainResolutionRequestV1)
            or not isinstance(owner_preferences_and_candidate_assertions, tuple)
            or not isinstance(typed_agent_disagreements, tuple)
        ):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "explanation requires exact typed request and immutable evidence",
            )
        supplied_refs = (
            ()
            if resolution is None
            else resolution.evidence_refs
        )
        valid_receipt = (
            resolution is not None
            and request.resolution_receipt_id
            in {
                resolution.result_id,
                *supplied_refs,
            }
        )
        component_rows = (
            ()
            if resolution is None
            else (
                (resolution,)
                if isinstance(resolution, ComponentComputationResultV1)
                else resolution.component_results
            )
        )
        trusted: list[str] = []
        formula_lineage: list[str] = []
        dependency_lineage: list[str] = []
        unit_lineage: list[str] = []
        time_lineage: list[str] = []
        parameter_lineage: list[str] = []
        blockers: list[str] = []
        fallback_rows: list[str] = []
        downstream: list[str] = []
        next_routes: list[str] = []
        for component in component_rows:
            input_receipt = component.input_resolution_receipt
            if input_receipt is not None:
                for row in input_receipt.inputs:
                    trusted.append(
                        deterministic_json(
                            {
                                "component_id": component.component_id,
                                "field_id": row.input_field_id,
                                "state": row.state.value,
                                "value": row.resolved_value,
                                "source_identity": row.source_identity,
                                "source_epoch_id": row.source_epoch_id,
                            }
                        )
                    )
                    unit_lineage.append(
                        f"{component.component_id}.{row.input_field_id}::"
                        f"{row.supplied_unit}/{row.supplied_basis}->"
                        f"{row.required_unit}/{row.required_basis}::"
                        f"{row.precision_policy}::{row.rounding_policy}"
                    )
                    if row.point_in_time_receipt is not None:
                        time_lineage.append(
                            f"{row.point_in_time_receipt.receipt_id}::"
                            f"{row.point_in_time_receipt.state.value}"
                        )
                    if row.freshness_receipt is not None:
                        time_lineage.append(
                            f"{row.freshness_receipt.receipt_id}::"
                            f"{row.freshness_receipt.state.value}"
                        )
                parameter_lineage.extend(input_receipt.parameter_policy_refs)
                dependency_lineage.extend(input_receipt.dependency_refs)
                downstream.extend(input_receipt.downstream_consumer_refs)
            if component.execution_receipt is not None:
                execution = component.execution_receipt
                formula_lineage.append(
                    f"{execution.specification_id}::{execution.implementation_id}::"
                    f"{execution.callable_version}"
                )
                dependency_lineage.extend(
                    (
                        *execution.dependency_receipt_refs,
                        *execution.conversion_receipt_refs,
                    )
                )
                downstream.extend(execution.consumer_refs)
                if (
                    not execution.dependency_receipt_refs
                    and not execution.conversion_receipt_refs
                ):
                    dependency_lineage.append(
                        f"{component.component_id}::"
                        "NO_DEPENDENCY_OR_CONVERSION_REQUIRED"
                    )
            blockers.extend(
                reason.value for reason in component.blocker_reason_codes
            )
            if component.fallback_receipt is not None:
                fallback_rows.append(
                    f"{component.fallback_receipt.fallback_id}->"
                    f"{component.fallback_receipt.resolved_target}::"
                    f"{component.fallback_receipt.semantic_limitation}"
                )
            next_routes.append(component.terminal_route)
        if isinstance(resolution, StackComputationResultV1):
            if resolution.execution_receipt is not None:
                dependency_lineage.extend(
                    (
                        resolution.execution_receipt.dependency_graph_ref,
                        *resolution.execution_receipt.edge_consumption_refs,
                    )
                )
                downstream.extend(
                    resolution.execution_receipt.consumer_refs
                )
            blockers.extend(
                reason.value for reason in resolution.blocker_reason_codes
            )
            next_routes.append(resolution.terminal_route)

        def bounded(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
            return tuple(dict.fromkeys(values))[: request.max_evidence_items]

        explanation = StructuredResolutionExplanationV1(
            result_id=_result_id(request),
            terminal_route=(
                "SVC1::DETERMINISTIC_OWNER_READ_MODEL"
                if valid_receipt
                else "governance_agent::RESOLUTION_RECEIPT_REBINDING"
            ),
            evidence_refs=bounded(
                (
                    request.resolution_receipt_id,
                    *supplied_refs,
                )
            ),
            trusted_typed_input_facts=bounded(trusted),
            owner_preferences_and_candidate_assertions=bounded(
                owner_preferences_and_candidate_assertions
            ),
            formula_and_implementation_lineage=bounded(formula_lineage),
            dependency_and_conversion_lineage=bounded(dependency_lineage),
            units_bases_precision_and_rounding=bounded(unit_lineage),
            point_in_time_and_freshness_state=bounded(time_lineage),
            parameter_policy_resolution=bounded(parameter_lineage),
            uncertainty_and_model_limitations=(
                "PURE_COMPUTATION_ONLY_NO_PROFIT_OR_LIVE_READINESS_CLAIM",
                "MISSING_LATER_TRANCHE_EVIDENCE_REMAINS_UNAVAILABLE",
            ),
            typed_agent_disagreements=bounded(typed_agent_disagreements),
            blockers_and_hard_veto_state=bounded(blockers),
            fallback_state=bounded(fallback_rows),
            downstream_consumers=bounded(downstream),
            next_safe_routes=bounded(next_routes),
            forbidden_effects=_NO_EFFECTS,
        )
        response_blockers = (
            ()
            if valid_receipt
            else (OperationBlockerCodeV1.DEPENDENCY_UNRESOLVED,)
        )
        return ExplainResolutionResponseV1(
            **_response_common(
                request,
                status=(
                    OperationStatusV1.SUCCEEDED
                    if not response_blockers
                    else OperationStatusV1.BLOCKED
                ),
                blockers=response_blockers,
                receipt_refs=explanation.evidence_refs,
            ),
            explanation=explanation,
        )

    def submit_candidate_proposal(
        self,
        request: SubmitCandidateProposalRequestV1,
    ) -> SubmitCandidateProposalResponseV1:
        if not isinstance(request, SubmitCandidateProposalRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "candidate proposal requires its exact typed request",
            )
        proposal = CandidateProposalV1(
            result_id=_result_id(request),
            terminal_route="governance_agent::OWNER_REVIEW_NO_SOURCE_PROMOTION",
            evidence_refs=request.source_candidate_refs,
        )
        return SubmitCandidateProposalResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=proposal.evidence_refs,
            ),
            proposal=proposal,
        )

    def request_materialization_work_order(
        self,
        request: RequestMaterializationWorkOrderRequestV1,
    ) -> RequestMaterializationWorkOrderResponseV1:
        if not isinstance(request, RequestMaterializationWorkOrderRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "materialization work order requires its exact typed request",
            )
        work_order = MaterializationWorkOrderV1(
            result_id=_result_id(request),
            terminal_route="AGENT-ORCH1::TYPED_MATERIALIZATION_TASK",
            evidence_refs=tuple(
                dict.fromkeys(
                    (
                        *request.missing_contract_ids,
                        *(reason.value for reason in request.reason_codes),
                        request.requested_owner,
                    )
                )
            ),
        )
        return RequestMaterializationWorkOrderResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=work_order.evidence_refs,
            ),
            work_order=work_order,
        )

    def compile_replay_paper_cohort(
        self,
        request: CompileReplayPaperCohortRequestV1,
    ) -> CompileReplayPaperCohortResponseV1:
        if not isinstance(request, CompileReplayPaperCohortRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "cohort compilation requires its exact typed request",
            )
        compilation = ReplayPaperCohortCompilationV1(
            result_id=_result_id(request),
            terminal_route=(
                "RuntimePlatformV1::LATER_COHORT_HANDOFF_NO_CAMPAIGN_EXECUTION"
            ),
            evidence_refs=tuple(
                dict.fromkeys(
                    (
                        *request.template_ids,
                        *request.requested_lanes,
                        request.input_lock_id,
                    )
                )
            ),
        )
        return CompileReplayPaperCohortResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=compilation.evidence_refs,
            ),
            cohort_compilation=compilation,
        )

    def register_replay_paper_result(
        self,
        request: RegisterReplayPaperResultRequestV1,
    ) -> RegisterReplayPaperResultResponseV1:
        if not isinstance(request, RegisterReplayPaperResultRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "result routing requires its exact typed request",
            )
        registration = ReplayPaperResultRegistrationV1(
            result_id=_result_id(request),
            terminal_route=(
                "RuntimePlatformV1::APPEND_ONLY_HANDOFF_INTERFACE_NO_WRITE_EFFECT"
            ),
            evidence_refs=(
                request.cohort_instance_id,
                request.lane,
                request.input_lock_id,
            ),
        )
        return RegisterReplayPaperResultResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=registration.evidence_refs,
            ),
            registration=registration,
        )

    def build_evidence_bundle(
        self,
        request: BuildEvidenceBundleRequestV1,
    ) -> BuildEvidenceBundleResponseV1:
        if not isinstance(request, BuildEvidenceBundleRequestV1):
            raise ComputationServiceError(
                ReasonCode.INVALID_CONTRACT,
                "evidence bundle requires its exact typed request",
            )
        bundle = EvidenceBundleResultV1(
            result_id=_result_id(request),
            terminal_route="READINESS1::TYPED_EVIDENCE_PROJECTION",
            evidence_refs=tuple(
                dict.fromkeys(
                    (
                        request.component_id,
                        request.input_lock_id,
                        *request.evidence_record_refs,
                        *request.required_lanes,
                    )
                )
            ),
        )
        return BuildEvidenceBundleResponseV1(
            **_response_common(
                request,
                status=OperationStatusV1.SUCCEEDED,
                blockers=(),
                receipt_refs=bundle.evidence_refs,
            ),
            evidence_bundle=bundle,
        )
