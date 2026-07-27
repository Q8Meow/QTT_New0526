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
