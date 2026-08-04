"""Fail-closed errors for the Tranche-A computation control plane."""

from __future__ import annotations

from enum import StrEnum


class ReasonCode(StrEnum):
    INVALID_CONTRACT = "ST12A_INVALID_CONTRACT"
    INCOMPLETE_CONTRACT = "ST12A_INCOMPLETE_CONTRACT"
    UNKNOWN_IMPLEMENTATION = "ST12A_UNKNOWN_IMPLEMENTATION"
    INVALID_NUMERIC_INPUT = "ST12A_INVALID_NUMERIC_INPUT"
    NONFINITE_NUMERIC_INPUT = "ST12A_NONFINITE_NUMERIC_INPUT"
    FLOAT_DECIMAL_CONTAMINATION = "ST12A_FLOAT_DECIMAL_CONTAMINATION"
    OUT_OF_DOMAIN = "ST12A_OUT_OF_DOMAIN"
    STALE_CONTEXT = "ST12A_STALE_CONTEXT"
    FUTURE_CONTEXT = "ST12A_FUTURE_CONTEXT"
    SOURCE_EPOCH_MISSING = "ST12A_SOURCE_EPOCH_MISSING"
    SOURCE_EPOCH_STALE = "ST12A_SOURCE_EPOCH_STALE"
    SOURCE_CONFLICT = "ST12A_SOURCE_CONFLICT"
    SOURCE_RIGHTS_BLOCKED = "ST12A_SOURCE_RIGHTS_BLOCKED"
    UNKNOWN_LIFECYCLE_STATE = "ST12A_UNKNOWN_LIFECYCLE_STATE"
    PARAMETER_UNKNOWN = "ST12A_PARAMETER_UNKNOWN"
    PARAMETER_NOT_EDITABLE = "ST12A_PARAMETER_NOT_EDITABLE"
    PARAMETER_OUT_OF_POLICY = "ST12A_PARAMETER_OUT_OF_POLICY"
    OWNER_DATA_MISSING = "ST12A_OWNER_DATA_MISSING"
    OWNER_DATA_MALFORMED = "ST12A_OWNER_DATA_MALFORMED"
    OWNER_DATA_CONTRADICTORY = "ST12A_OWNER_DATA_CONTRADICTORY"
    OWNER_DATA_STALE = "ST12A_OWNER_DATA_STALE"
    DEPENDENCY_UNKNOWN = "ST12A_DEPENDENCY_UNKNOWN"
    DEPENDENCY_CYCLE = "ST12A_DEPENDENCY_CYCLE"
    DEPENDENCY_UNIT_MISMATCH = "ST12A_DEPENDENCY_UNIT_MISMATCH"
    DEPENDENCY_TIMING_MISMATCH = "ST12A_DEPENDENCY_TIMING_MISMATCH"
    PATH_UNSAFE = "ST12A_PATH_UNSAFE"
    SERIALIZATION_UNSAFE = "ST12A_SERIALIZATION_UNSAFE"
    SECRET_MATERIAL_REJECTED = "ST12A_SECRET_MATERIAL_REJECTED"
    CAPABILITY_DENIED = "ST12A_CAPABILITY_DENIED"
    RUNTIME_EFFECT_FORBIDDEN = "ST12A_RUNTIME_EFFECT_FORBIDDEN"
    ORACLE_NOT_INDEPENDENT = "ST12A_ORACLE_NOT_INDEPENDENT"
    VALIDATION_FAILED = "ST12A_VALIDATION_FAILED"
    NO_APPLICABLE_STACK = "ST12B_NO_APPLICABLE_STACK"
    INPUT_OWNER_MISSING = "ST12B_INPUT_OWNER_MISSING"
    INPUT_OWNER_MISMATCH = "ST12B_INPUT_OWNER_MISMATCH"
    INPUT_PACKET_MISMATCH = "ST12B_INPUT_PACKET_MISMATCH"
    INPUT_SCHEMA_MISMATCH = "ST12B_INPUT_SCHEMA_MISMATCH"
    INPUT_SCOPE_MISMATCH = "ST12B_INPUT_SCOPE_MISMATCH"
    INPUT_VALUE_CONFLICT = "ST12B_INPUT_VALUE_CONFLICT"
    POINT_IN_TIME_VIOLATION = "ST12B_POINT_IN_TIME_VIOLATION"
    FRESHNESS_VIOLATION = "ST12B_FRESHNESS_VIOLATION"
    PARAMETER_OWNER_MISSING = "ST12B_PARAMETER_OWNER_MISSING"
    PARAMETER_BINDING_MISMATCH = "ST12B_PARAMETER_BINDING_MISMATCH"
    UNIT_CONVERSION_FORBIDDEN = "ST12B_UNIT_CONVERSION_FORBIDDEN"
    UNIT_CONVERSION_FAILED = "ST12B_UNIT_CONVERSION_FAILED"
    DEPENDENCY_CLOSURE_FAILED = "ST12B_DEPENDENCY_CLOSURE_FAILED"
    OUTPUT_SCHEMA_MISMATCH = "ST12B_OUTPUT_SCHEMA_MISMATCH"
    FORMULA_EXECUTION_REJECTED = "ST12B_FORMULA_EXECUTION_REJECTED"
    OPERATION_BLOCKED = "ST12B_OPERATION_BLOCKED"
    ACCOUNTING_IMBALANCE = "ST12C_ACCOUNTING_IMBALANCE"
    UNIT_BASIS_MISMATCH = "ST12C_UNIT_BASIS_MISMATCH"
    QUANTIZATION_POLICY_MISSING = "ST12C_QUANTIZATION_POLICY_MISSING"
    IDEMPOTENCY_CONFLICT = "ST12C_IDEMPOTENCY_CONFLICT"
    IDEMPOTENCY_IN_PROGRESS = "ST12C_IDEMPOTENCY_IN_PROGRESS"
    DUPLICATE_EVENT_CONFLICT = "ST12C_DUPLICATE_EVENT_CONFLICT"
    PERSISTENCE_CONFLICT = "ST12C_PERSISTENCE_CONFLICT"
    PERSISTENCE_UNAVAILABLE = "ST12C_PERSISTENCE_UNAVAILABLE"
    SCHEMA_MISMATCH = "ST12C_SCHEMA_MISMATCH"
    APPEND_ONLY_VIOLATION = "ST12C_APPEND_ONLY_VIOLATION"
    TRANSACTION_STATE_INVALID = "ST12C_TRANSACTION_STATE_INVALID"
    TRANSACTION_RETRY_EXHAUSTED = "ST12C_TRANSACTION_RETRY_EXHAUSTED"
    REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT = "REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT"
    ILLEGAL_STATE_TRANSITION = "ST12C_ILLEGAL_STATE_TRANSITION"
    RECONCILIATION_REQUIRED = "ST12C_RECONCILIATION_REQUIRED"
    REVERSAL_INVALID = "ST12C_REVERSAL_INVALID"
    MODEL_ARTIFACT_REQUIRED = "ST12C_MODEL_ARTIFACT_REQUIRED"
    RATE_LIMIT_BUDGET_REQUIRED = "ST12C_RATE_LIMIT_BUDGET_REQUIRED"
    OUTBOX_DISPATCH_FORBIDDEN = "ST12C_OUTBOX_DISPATCH_FORBIDDEN"
    SUBMIT_DISABLED = "ST12C_SUBMIT_DISABLED"
    PRINCIPAL_UNKNOWN = "ST12E_PRINCIPAL_UNKNOWN"
    PRINCIPAL_AMBIGUOUS = "ST12E_PRINCIPAL_AMBIGUOUS"
    SOURCE_AGENT_ID_UNMAPPED = "ST12E_SOURCE_AGENT_ID_UNMAPPED"
    SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY = (
        "ST12E_SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY"
    )
    ROLE_MISMATCH = "ST12E_ROLE_MISMATCH"
    DUTY_MISMATCH = "ST12E_DUTY_MISMATCH"
    TASK_ENVELOPE_MISSING = "ST12E_TASK_ENVELOPE_MISSING"
    TASK_ENVELOPE_STALE = "ST12E_TASK_ENVELOPE_STALE"
    TASK_SCOPE_MISMATCH = "ST12E_TASK_SCOPE_MISMATCH"
    OPERATION_NOT_ALLOWED = "ST12E_OPERATION_NOT_ALLOWED"
    QKU_SCOPE_MISMATCH = "ST12E_QKU_SCOPE_MISMATCH"
    FORMULA_SCOPE_MISMATCH = "ST12E_FORMULA_SCOPE_MISMATCH"
    DATA_SCOPE_MISMATCH = "ST12E_DATA_SCOPE_MISMATCH"
    TOOL_SCOPE_MISMATCH = "ST12E_TOOL_SCOPE_MISMATCH"
    ACTION_SCOPE_MISMATCH = "ST12E_ACTION_SCOPE_MISMATCH"
    CONTEXT_SCOPE_MISMATCH = "ST12E_CONTEXT_SCOPE_MISMATCH"
    PARAMETER_SCOPE_MISMATCH = "ST12E_PARAMETER_SCOPE_MISMATCH"
    BUDGET_EXCEEDED = "ST12E_BUDGET_EXCEEDED"
    DEADLINE_EXCEEDED = "ST12E_DEADLINE_EXCEEDED"
    RETRY_NOT_ALLOWED = "ST12E_RETRY_NOT_ALLOWED"
    SEGREGATION_OF_DUTIES_VIOLATION = (
        "ST12E_SEGREGATION_OF_DUTIES_VIOLATION"
    )
    SELF_PROMOTION_FORBIDDEN = "ST12E_SELF_PROMOTION_FORBIDDEN"
    SELF_QUARANTINE_RELEASE_FORBIDDEN = (
        "ST12E_SELF_QUARANTINE_RELEASE_FORBIDDEN"
    )
    PEER_CHALLENGE_REQUIRED = "ST12E_PEER_CHALLENGE_REQUIRED"
    TRUST_STATE_INSUFFICIENT = "ST12E_TRUST_STATE_INSUFFICIENT"
    QUARANTINED = "ST12E_QUARANTINED"
    MEMORY_PRIOR_REVALIDATION_REQUIRED = (
        "ST12E_MEMORY_PRIOR_REVALIDATION_REQUIRED"
    )
    LLM_ADVISORY_ONLY = "ST12E_LLM_ADVISORY_ONLY"
    LLM_TOOL_NOT_ALLOWED = "ST12E_LLM_TOOL_NOT_ALLOWED"
    UNTRUSTED_CONTENT_INSTRUCTION_REJECTED = (
        "ST12E_UNTRUSTED_CONTENT_INSTRUCTION_REJECTED"
    )
    DIRECT_PROVIDER_FORBIDDEN = "ST12E_DIRECT_PROVIDER_FORBIDDEN"
    PRIVATE_STATE_FORBIDDEN = "ST12E_PRIVATE_STATE_FORBIDDEN"
    SOURCE_TRUTH_FORBIDDEN = "ST12E_SOURCE_TRUTH_FORBIDDEN"
    REPLAY_PAPER_EFFECT_FORBIDDEN = "ST12E_REPLAY_PAPER_EFFECT_FORBIDDEN"
    LLM_INFERENCE_FORBIDDEN = "ST12E_LLM_INFERENCE_FORBIDDEN"
    QPU_EFFECT_FORBIDDEN = "ST12E_QPU_EFFECT_FORBIDDEN"
    MODE_ACTIVATION_FORBIDDEN = "ST12E_MODE_ACTIVATION_FORBIDDEN"
    ORDER_RELEASE_FORBIDDEN = "ST12E_ORDER_RELEASE_FORBIDDEN"
    CAPITAL_EFFECT_FORBIDDEN = "ST12E_CAPITAL_EFFECT_FORBIDDEN"
    SAFETY_STATE_MISSING = "ST12E_SAFETY_STATE_MISSING"
    SAFETY_STATE_STALE = "ST12E_SAFETY_STATE_STALE"
    SAFETY_STATE_CONFLICT = "ST12E_SAFETY_STATE_CONFLICT"
    EXECUTION_ROUTER_BYPASS_FORBIDDEN = (
        "ST12E_EXECUTION_ROUTER_BYPASS_FORBIDDEN"
    )
    NO_TRADE_REOPTIMIZATION_REQUIRED = (
        "ST12E_NO_TRADE_REOPTIMIZATION_REQUIRED"
    )
    OWNER_REVIEW_REQUIRED = "ST12E_OWNER_REVIEW_REQUIRED"


class ComputationControlPlaneError(ValueError):
    """Base typed failure carrying a stable fail-closed reason code."""

    def __init__(self, reason_code: ReasonCode, message: str) -> None:
        self.reason_code = reason_code
        super().__init__(f"{reason_code}: {message}")


class ContractValidationError(ComputationControlPlaneError):
    """A typed computation-envelope or data-contract violation."""


class NumericDomainError(ComputationControlPlaneError):
    """A typed mathematical-domain, precision, or finiteness violation."""


class SourcePolicyError(ComputationControlPlaneError):
    """A typed source identity, epoch, rights, or currentization violation."""


class ParameterPolicyError(ComputationControlPlaneError):
    """A typed parameter identity, editability, or bounds violation."""


class OwnerAdapterError(ComputationControlPlaneError):
    """A typed read-only canonical-owner consumption violation."""


class DependencyGraphError(ComputationControlPlaneError):
    """A typed dependency identity, cycle, timing, or unit violation."""


class AuthorityDeniedError(ComputationControlPlaneError):
    """A typed denial at the default-deny capability boundary."""


class NoTradeReoptimizationRouteError(AuthorityDeniedError):
    """Typed no-effect control flow preserving the complete NO_TRADE packet."""

    def __init__(self, decision: object) -> None:
        self.decision = decision
        decision_id = str(getattr(decision, "decision_id", "") or "MISSING")
        terminal_route = str(
            getattr(decision, "terminal_route", "") or "MISSING"
        )
        super().__init__(
            ReasonCode.NO_TRADE_REOPTIMIZATION_REQUIRED,
            f"{decision_id} routed to {terminal_route}",
        )


class SerializationSafetyError(ComputationControlPlaneError):
    """A typed deterministic-serialization or relative-path safety violation."""


class PointInTimeError(ComputationControlPlaneError):
    """A deterministic point-in-time field-class law was violated."""


class FreshnessError(ComputationControlPlaneError):
    """An accepted owner packet is stale or lacks freshness lineage."""


class InputAuthorityError(ComputationControlPlaneError):
    """A value did not come from its frozen canonical owner interface."""


class UnitConversionError(ComputationControlPlaneError):
    """A conversion was missing, forbidden, or outside its exact domain."""


class ContextualComputabilityError(ComputationControlPlaneError):
    """A strict contextual-computability resolver could not close its state."""


class StackResolutionError(ComputationControlPlaneError):
    """The exact dependency stack could not be selected or closed."""


class FormulaExecutionError(ComputationControlPlaneError):
    """A registered formula rejected a typed execution request."""


class OutputContractError(ComputationControlPlaneError):
    """A formula result did not satisfy its frozen named-output contract."""


class OperationBoundaryError(ComputationControlPlaneError):
    """An expected typed failure reached the public operation boundary."""


class AccountingContractError(ComputationControlPlaneError):
    """A Tranche-C accounting, unit, cash, TCA, or reversal law failed."""


class PersistenceContractError(ComputationControlPlaneError):
    """A backend-neutral persistence or append-only law failed."""


class IdempotencyContractError(ComputationControlPlaneError):
    """An economic idempotency, duplicate, or replay law failed."""


class TransactionContractError(ComputationControlPlaneError):
    """A Tranche-C atomic unit-of-work law failed."""


class LifecycleContractError(ComputationControlPlaneError):
    """A no-write lifecycle, custody, freshness, or rate-budget law failed."""
