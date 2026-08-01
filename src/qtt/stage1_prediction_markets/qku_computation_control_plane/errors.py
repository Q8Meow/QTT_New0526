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
