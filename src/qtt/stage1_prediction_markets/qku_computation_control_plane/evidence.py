"""Canonical ST12-F lane, divergence, review, and evidence-bundle owner."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
import math
from types import MappingProxyType
from typing import Mapping, Protocol

from .context import exact_decimal, parse_utc
from .errors import (
    ContractValidationError,
    IdempotencyContractError,
    PersistenceContractError,
    ReasonCode,
)
from .idempotency import (
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    IdempotencyOutcomeV1,
    canonical_request_json_v1,
)
from .input_lock import ImmutableReplayPaperInputLockV1, ST12F_TEMPLATE_IDS_V1
from .lifecycle import StateTransitionReceiptV1, TransitionDispositionV1
from .llm_gateway import DeterministicEvidenceAnnotationContractV1
from .model_risk import ModelRiskEvidenceAssessmentV1
from .models import (
    BuildEvidenceBundleRequestV1,
    NO_EFFECTS_V1,
    RegisterReplayPaperResultRequestV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
    TypedValueKindV1,
    TypedValueRecordV1,
)
from .parameter_policy import initialize_st12f_parameter_registry_v1
from .persistence import PersistenceAdapterV1, PersistenceAvailabilityV1
from .quantum_benchmark import QuantumClassicalNoTradeComparisonV1
from .receipts import (
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    ST12FEvidenceControlReceiptRecordV1,
    ST12FReceiptClassV1,
)
from .serialization import deterministic_json, safe_json_loads


LANE_RESULT_SCHEMA_VERSION_V1 = "QTT_ST12F_LANE_RESULT_CONTRACTS_V1_4"
LANE_RESULT_CONTRACT_VERSION_V1 = "1.4"
DIVERGENCE_SCHEMA_VERSION_V1 = "QTT_ST12F_DIVERGENCE_ASSESSMENT_V1_4"
EVIDENCE_BUNDLE_SCHEMA_VERSION_V1 = "QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4"
EVIDENCE_BUNDLE_CONTRACT_VERSION_V1 = "1.4"
ST12F_EVIDENCE_IDENTITIES_V1 = tuple(
    f"MATH-{number:02d}" for number in (*range(1, 46), 50, 51, 52)
)


@dataclass(frozen=True, slots=True)
class EvidenceMetricDefinitionV1:
    metric_id: str
    name: str
    family: str
    direction: str
    math_spec_ref: str
    canonical_owner: str
    actual_value_required: bool
    pass_label_substitution_allowed: bool
    fixture_may_be_empirical_evidence: bool

    def __post_init__(self) -> None:
        if any(
            not isinstance(getattr(self, name), str)
            or not getattr(self, name)
            or getattr(self, name) != getattr(self, name).strip()
            for name in ("metric_id", "name", "family", "direction", "math_spec_ref", "canonical_owner")
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "metric definition identities must be canonical text",
            )
        if (
            self.actual_value_required is not True
            or self.pass_label_substitution_allowed is not False
            or self.fixture_may_be_empirical_evidence is not False
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "metric definitions require values and forbid label/fixture substitution",
            )


ST12F_EVIDENCE_METRIC_DEFINITIONS_V1 = (
    EvidenceMetricDefinitionV1("ST12F-METRIC::001", "BrierScore", "CALIBRATION", "LOWER_IS_BETTER", "MATH-08", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::002", "LogLoss", "CALIBRATION", "LOWER_IS_BETTER", "MATH-09", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::003", "ExpectedCalibrationError", "CALIBRATION", "LOWER_IS_BETTER", "MATH-10", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::004", "WilsonInterval", "UNCERTAINTY", "INTERVAL", "MATH-11", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::005", "BenjaminiHochberg", "FDR", "CONTROL", "MATH-12", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::006", "BenjaminiYekutieli", "FDR", "CONTROL", "MATH-13", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::007", "StationaryBootstrap", "DEPENDENCE", "INTERVAL", "MATH-14", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::008", "WhiteRealityCheck", "DATA_SNOOPING", "TEST", "MATH-15", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::009", "HansenSPA", "DATA_SNOOPING", "TEST", "MATH-16", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::010", "ProbabilisticSharpeRatio", "RISK_ADJUSTED", "HIGHER_IS_BETTER", "MATH-17", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::011", "DeflatedSharpeRatio", "MULTIPLE_TESTING", "HIGHER_IS_BETTER", "MATH-18", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::012", "ProbabilityOfBacktestOverfitting", "OVERFIT", "LOWER_IS_BETTER", "MATH-19", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::013", "PurgedKFold", "LEAKAGE", "CONTROL", "MATH-20", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::014", "CombinatorialPurgedCV", "LEAKAGE", "CONTROL", "MATH-21", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::015", "DoublyRobustOPE", "OPE", "ESTIMATE", "MATH-22", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::016", "IPS", "OPE", "ESTIMATE", "MATH-23", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::017", "SNIPS", "OPE", "ESTIMATE", "MATH-24", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::018", "SWITCHOPE", "OPE", "ESTIMATE", "MATH-25", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::019", "ExpectedValueOfInformation", "RESEARCH_ALLOCATION", "HIGHER_IS_BETTER", "MATH-26", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::020", "Kelly", "SIZING", "BOUNDED", "MATH-27", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::021", "FractionalKelly", "SIZING", "BOUNDED", "MATH-28", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::022", "MeanVariance", "PORTFOLIO", "OPTIMIZE", "MATH-29", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::023", "CVaR", "TAIL_RISK", "LOWER_IS_BETTER", "MATH-30", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::024", "HistoricalES", "TAIL_RISK", "LOWER_IS_BETTER", "MATH-31", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::025", "ImplementationShortfall", "TCA", "LOWER_IS_BETTER", "MATH-32", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::026", "SpreadCost", "TCA", "LOWER_IS_BETTER", "MATH-33", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::027", "FillProbability", "FILL", "HIGHER_IS_BETTER", "MATH-37", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::028", "PartialFill", "FILL", "ESTIMATE", "MATH-38", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::029", "QueueEstimate", "QUEUE", "ESTIMATE", "MATH-39", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::030", "AdverseSelection", "TCA", "LOWER_IS_BETTER", "MATH-40", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::031", "LatencyDecay", "LATENCY", "HIGHER_REMAINING_EDGE_IS_BETTER", "MATH-41", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::032", "SquareRootImpact", "IMPACT", "LOWER_IS_BETTER", "MATH-42", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::033", "CapacityCrowding", "CAPACITY", "LOWER_IS_BETTER", "MATH-43", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::034", "CovarianceShrinkage", "PORTFOLIO", "PSD_REQUIRED", "MATH-44", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::035", "LCBNoTradeGate", "NO_TRADE", "STRICTLY_POSITIVE_TO_TRADE", "MATH-45", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::036", "QAOATraceValidation", "QUANTUM_TRACE", "VALIDATION_ONLY", "MATH-50", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::037", "VQETraceValidation", "QUANTUM_TRACE", "VALIDATION_ONLY", "MATH-51", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::038", "QuantumClassicalUtility", "QUANTUM_BENCHMARK", "SAME_BASIS_ONLY", "MATH-52", "ComputationEvidenceServiceV1", True, False, False),
)


def _text(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be bounded canonical text",
        )
    return value


def _refs(value: object, name: str, *, required: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item or item != item.strip() for item in value)
        or len(value) != len(set(value))
        or (required and not value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be an ordered unique reference tuple",
        )
    return value


def _reason_tuple(value: object, name: str) -> tuple[ReasonCode, ...]:
    if (
        not isinstance(value, tuple)
        or any(type(code) is not ReasonCode for code in value)
        or len(value) != len(set(value))
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be an ordered unique ReasonCode tuple",
        )
    return value


def _freeze(value: object, name: str) -> object:
    if value is None or type(value) in {bool, int, str} or isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(
                ReasonCode.NONFINITE_NUMERIC_INPUT,
                f"{name} contains a nonfinite value",
            )
        return value
    if isinstance(value, tuple | list):
        return tuple(_freeze(item, name) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) or not key for key in value):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                f"{name} contains an invalid mapping key",
            )
        return MappingProxyType(
            {
                key: _freeze(item, f"{name}.{key}")
                for key, item in sorted(value.items())
            }
        )
    raise ContractValidationError(
        ReasonCode.CONTRACT_OR_TYPE_INVALID,
        f"{name} contains unsupported {type(value).__name__}",
    )


def _mapping(value: object, name: str, *, required: bool = True) -> Mapping[str, object]:
    frozen = _freeze(value, name)
    if not isinstance(frozen, Mapping) or (required and not frozen):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{name} must be an immutable mapping",
        )
    return frozen


def _from_json_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            f"{name} must be a mapping",
        )
    return value


def _lane_post_init(value: object, *, lane: str) -> None:
    if getattr(value, "schema_version") != LANE_RESULT_SCHEMA_VERSION_V1 or getattr(
        value, "contract_version"
    ) != LANE_RESULT_CONTRACT_VERSION_V1:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            f"{lane} result schema or contract version differs",
        )
    template_id = _text(getattr(value, "cohort_template_id"), "cohort_template_id")
    if template_id not in ST12F_TEMPLATE_IDS_V1:
        raise ContractValidationError(
            ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
            "lane result template is not a certified cohort member",
        )
    expected = f"ST12F-{lane}-CONTRACT::{template_id}"
    if getattr(value, "expected_result_contract_id") != expected:
        raise ContractValidationError(
            ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
            "lane packet expected-result identity differs from its exact lane",
        )
    for name in (
        "result_id",
        "input_lock_id",
        "run_reference",
        "producer_identity",
        "accounting_definition",
    ):
        _text(getattr(value, name), name)
    for name in (
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
    ):
        object.__setattr__(value, name, _mapping(getattr(value, name), name))
    for name in ("failure_states", "limitations"):
        _refs(getattr(value, name), name)
    cutoff = parse_utc(getattr(value, "point_in_time_cutoff"), field_name="point_in_time_cutoff")
    started = parse_utc(getattr(value, "started_at"), field_name="started_at")
    completed = parse_utc(getattr(value, "completed_at"), field_name="completed_at")
    available = parse_utc(getattr(value, "available_at"), field_name="available_at")
    closed = parse_utc(getattr(value, "closed_at"), field_name="closed_at")
    if not cutoff <= started <= completed <= available <= closed:
        raise ContractValidationError(
            ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
            "lane result timestamps violate point-in-time sequence",
        )
    for name, parsed in (
        ("point_in_time_cutoff", cutoff),
        ("started_at", started),
        ("completed_at", completed),
        ("available_at", available),
        ("closed_at", closed),
    ):
        object.__setattr__(value, name, parsed)
    if type(getattr(value, "fixture_only_not_evidence")) is not bool:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "fixture_only_not_evidence must be an exact boolean",
        )


def _lane_from_mapping(cls: type[object], value: object) -> object:
    if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "lane-result payload field roster differs from the exact 26 fields",
        )
    payload = dict(value)
    for name in (
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
    ):
        payload[name] = _from_json_mapping(payload[name], name)
    payload["failure_states"] = tuple(payload["failure_states"])
    payload["limitations"] = tuple(payload["limitations"])
    return cls(**payload)


@dataclass(frozen=True, slots=True)
class ReplayResultContractV1:
    result_id: str
    schema_version: str
    contract_version: str
    cohort_template_id: str
    expected_result_contract_id: str
    input_lock_id: str
    run_reference: str
    producer_identity: str
    implementation_versions: Mapping[str, object]
    source_epochs: Mapping[str, object]
    point_in_time_cutoff: datetime
    accounting_definition: str
    scenario_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    economic_metrics: Mapping[str, object]
    tca_metrics: Mapping[str, object]
    fill_metrics: Mapping[str, object]
    latency_metrics: Mapping[str, object]
    capacity_metrics: Mapping[str, object]
    failure_states: tuple[str, ...]
    limitations: tuple[str, ...]
    started_at: datetime
    completed_at: datetime
    available_at: datetime
    closed_at: datetime
    fixture_only_not_evidence: bool

    def __post_init__(self) -> None:
        _lane_post_init(self, lane="REPLAY")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ReplayResultContractV1":
        return _lane_from_mapping(cls, value)  # type: ignore[return-value]

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class PaperResultContractV1:
    result_id: str
    schema_version: str
    contract_version: str
    cohort_template_id: str
    expected_result_contract_id: str
    input_lock_id: str
    run_reference: str
    producer_identity: str
    implementation_versions: Mapping[str, object]
    source_epochs: Mapping[str, object]
    point_in_time_cutoff: datetime
    accounting_definition: str
    scenario_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    economic_metrics: Mapping[str, object]
    tca_metrics: Mapping[str, object]
    fill_metrics: Mapping[str, object]
    latency_metrics: Mapping[str, object]
    capacity_metrics: Mapping[str, object]
    failure_states: tuple[str, ...]
    limitations: tuple[str, ...]
    started_at: datetime
    completed_at: datetime
    available_at: datetime
    closed_at: datetime
    fixture_only_not_evidence: bool

    def __post_init__(self) -> None:
        _lane_post_init(self, lane="PAPER")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "PaperResultContractV1":
        return _lane_from_mapping(cls, value)  # type: ignore[return-value]

    def canonical_json(self) -> str:
        return deterministic_json(self)


class DivergenceTerminalStateV1(StrEnum):
    CONSISTENT_WITHIN_LOCKED_THRESHOLDS = "CONSISTENT_WITHIN_LOCKED_THRESHOLDS"
    MATERIAL_DIVERGENCE_REVIEW_REQUIRED = "MATERIAL_DIVERGENCE_REVIEW_REQUIRED"
    INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE = (
        "INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE"
    )


@dataclass(frozen=True, slots=True)
class DivergenceAssessmentV1:
    assessment_id: str
    schema_version: str
    contract_version: str
    input_lock_id: str
    cohort_template_id: str
    replay_result_ref: str
    paper_result_ref: str
    metric_deltas: Mapping[str, Decimal]
    directional_agreement: bool
    calibration_delta: Decimal | None
    execution_cost_delta: Decimal | None
    fill_delta: Decimal | None
    latency_delta: Decimal | None
    capacity_delta: Decimal | None
    regime_delta: Decimal | None
    threshold_policy_refs: tuple[str, ...]
    typed_blockers: tuple[ReasonCode, ...]
    terminal_state: DivergenceTerminalStateV1

    def __post_init__(self) -> None:
        if self.schema_version != DIVERGENCE_SCHEMA_VERSION_V1 or self.contract_version != "1.4":
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "divergence schema differs")
        for name in (
            "assessment_id",
            "input_lock_id",
            "cohort_template_id",
            "replay_result_ref",
            "paper_result_ref",
        ):
            _text(getattr(self, name), name)
        if self.cohort_template_id not in ST12F_TEMPLATE_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
                "divergence template is outside the cohort",
            )
        deltas = _mapping(self.metric_deltas, "metric_deltas", required=False)
        converted: dict[str, Decimal] = {}
        for key, value in deltas.items():
            converted[key] = exact_decimal(value, field_name=f"metric_deltas.{key}")
        object.__setattr__(self, "metric_deltas", MappingProxyType(converted))
        if type(self.directional_agreement) is not bool:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "directional agreement must be boolean")
        for name in (
            "calibration_delta",
            "execution_cost_delta",
            "fill_delta",
            "latency_delta",
            "capacity_delta",
            "regime_delta",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, exact_decimal(value, field_name=name))
        _refs(self.threshold_policy_refs, "threshold_policy_refs")
        _reason_tuple(self.typed_blockers, "typed_blockers")
        if type(self.terminal_state) is not DivergenceTerminalStateV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "divergence terminal state must be typed")
        missing_delta = any(
            getattr(self, name) is None
            for name in (
                "calibration_delta",
                "execution_cost_delta",
                "fill_delta",
                "latency_delta",
                "capacity_delta",
                "regime_delta",
            )
        )
        incomparable = self.terminal_state is DivergenceTerminalStateV1.INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE
        if bool(missing_delta or self.typed_blockers) != incomparable:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "missing/conflicting deltas must remain explicit and incomparable",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "DivergenceAssessmentV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "divergence fields differ")
        payload = dict(value)
        payload["terminal_state"] = DivergenceTerminalStateV1(payload["terminal_state"])
        payload["typed_blockers"] = tuple(ReasonCode(code) for code in payload["typed_blockers"])
        payload["threshold_policy_refs"] = tuple(payload["threshold_policy_refs"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class EvidenceIdentityDispositionStateV1(StrEnum):
    APPLICABLE_EXECUTED_AND_RECEIPTED = "APPLICABLE_EXECUTED_AND_RECEIPTED"
    APPLICABLE_BLOCKED_WITH_TYPED_REASON = "APPLICABLE_BLOCKED_WITH_TYPED_REASON"
    NOT_APPLICABLE_WITH_PROOF = "NOT_APPLICABLE_WITH_PROOF"


@dataclass(frozen=True, slots=True)
class EvidenceIdentityDispositionV1:
    evidence_identity: str
    disposition: EvidenceIdentityDispositionStateV1
    evidence_record_refs: tuple[str, ...]
    blocker_codes: tuple[ReasonCode, ...]
    proof_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.evidence_identity not in ST12F_EVIDENCE_IDENTITIES_V1 or type(self.disposition) is not EvidenceIdentityDispositionStateV1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "evidence identity or disposition is outside the closed registry",
            )
        _refs(self.evidence_record_refs, "evidence_record_refs")
        _reason_tuple(self.blocker_codes, "blocker_codes")
        _refs(self.proof_refs, "proof_refs")
        if self.disposition is EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED:
            valid = bool(self.evidence_record_refs) and not self.blocker_codes
        elif self.disposition is EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON:
            valid = bool(self.blocker_codes)
        else:
            valid = bool(self.proof_refs) and not self.evidence_record_refs
        if not valid:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "evidence disposition lacks its required receipt, blocker, or proof",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "EvidenceIdentityDispositionV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "evidence disposition fields differ")
        payload = dict(value)
        payload["disposition"] = EvidenceIdentityDispositionStateV1(payload["disposition"])
        payload["evidence_record_refs"] = tuple(payload["evidence_record_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        payload["proof_refs"] = tuple(payload["proof_refs"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class EvidenceSectionV1:
    section_id: str
    identity_dispositions: tuple[EvidenceIdentityDispositionV1, ...]

    def __post_init__(self) -> None:
        _text(self.section_id, "section_id")
        if (
            not isinstance(self.identity_dispositions, tuple)
            or not self.identity_dispositions
            or any(type(row) is not EvidenceIdentityDispositionV1 for row in self.identity_dispositions)
            or len({row.evidence_identity for row in self.identity_dispositions}) != len(self.identity_dispositions)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "evidence section requires unique typed dispositions",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "EvidenceSectionV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "evidence section fields differ")
        return cls(
            section_id=value["section_id"],
            identity_dispositions=tuple(
                EvidenceIdentityDispositionV1.from_canonical_mapping(row)
                for row in value["identity_dispositions"]
            ),
        )


class EvidenceBundleTerminalStateV1(StrEnum):
    INCOMPLETE_MISSING_REPLAY = "INCOMPLETE_MISSING_REPLAY"
    INCOMPLETE_MISSING_PAPER = "INCOMPLETE_MISSING_PAPER"
    INCOMPLETE_CONFLICT = "INCOMPLETE_CONFLICT"
    READY_FOR_INDEPENDENT_REVIEW = "READY_FOR_INDEPENDENT_REVIEW"
    INDEPENDENT_REVIEW_REJECTED = "INDEPENDENT_REVIEW_REJECTED"
    CLOSED_INDEPENDENTLY_VALIDATED = "CLOSED_INDEPENDENTLY_VALIDATED"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


class IndependentReviewDecisionV1(StrEnum):
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class IndependentReviewRecordV1:
    review_id: str
    schema_version: str
    contract_version: str
    prior_bundle_ref: str
    evidence_id: str
    evidence_bundle_version: str
    input_lock_id: str
    reviewer_identity: str
    bundle_producer_identity: str
    authority_receipt_ref: str
    reviewed_source_epoch_refs: tuple[str, ...]
    decision: IndependentReviewDecisionV1
    blocker_codes: tuple[ReasonCode, ...]
    reviewed_at: datetime
    valid_until: datetime
    no_self_review: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != "QTT_ST12F_INDEPENDENT_REVIEW_RECORD_V1_4" or self.contract_version != "1.4":
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "independent review schema differs")
        for name in (
            "review_id",
            "prior_bundle_ref",
            "evidence_id",
            "evidence_bundle_version",
            "input_lock_id",
            "reviewer_identity",
            "bundle_producer_identity",
            "authority_receipt_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.reviewed_source_epoch_refs, "reviewed_source_epoch_refs", required=True)
        _reason_tuple(self.blocker_codes, "blocker_codes")
        if type(self.decision) is not IndependentReviewDecisionV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "review decision must be typed")
        reviewed = parse_utc(self.reviewed_at, field_name="reviewed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "reviewed_at", reviewed)
        object.__setattr__(self, "valid_until", valid_until)
        if reviewed > valid_until:
            raise ContractValidationError(ReasonCode.ST12F_BUNDLE_STALE, "review validity precedes review")
        if type(self.no_self_review) is not bool or not self.no_self_review or self.reviewer_identity == self.bundle_producer_identity:
            raise ContractValidationError(ReasonCode.ST12F_SELF_REVIEW_FORBIDDEN, "bundle producer cannot independently review its own bundle")
        if (self.decision is IndependentReviewDecisionV1.VALIDATED and self.blocker_codes) or (
            self.decision is IndependentReviewDecisionV1.REJECTED and not self.blocker_codes
        ):
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "review decision and blockers differ")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "IndependentReviewRecordV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "independent review fields differ")
        payload = dict(value)
        payload["decision"] = IndependentReviewDecisionV1(payload["decision"])
        payload["reviewed_source_epoch_refs"] = tuple(payload["reviewed_source_epoch_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class FToGHandoffReferencesV1:
    evidence_bundle_ref: str
    no_trade_blocker_refs: tuple[str, ...]
    champion_challenger_evidence_refs: tuple[str, ...]
    portfolio_utility_refs: tuple[str, ...]
    quantum_classical_comparison_receipt_ref: str
    read_only: bool = True

    def __post_init__(self) -> None:
        _text(self.evidence_bundle_ref, "evidence_bundle_ref")
        for name in (
            "no_trade_blocker_refs",
            "champion_challenger_evidence_refs",
            "portfolio_utility_refs",
        ):
            _refs(getattr(self, name), name)
        _text(self.quantum_classical_comparison_receipt_ref, "quantum_classical_comparison_receipt_ref")
        if type(self.read_only) is not bool or not self.read_only:
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "F-to-G handoff is read-only")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "FToGHandoffReferencesV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "F-to-G handoff fields differ")
        payload = dict(value)
        for name in (
            "no_trade_blocker_refs",
            "champion_challenger_evidence_refs",
            "portfolio_utility_refs",
        ):
            payload[name] = tuple(payload[name])
        return cls(**payload)


_SECTION_FIELDS_V1 = (
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
)


@dataclass(frozen=True, slots=True)
class ComputationEvidenceBundleV1:
    evidence_id: str
    schema_version: str
    contract_version: str
    evidence_bundle_version: str
    component_or_template_ref: str
    input_lock_id: str
    actual_executed_component_versions: Mapping[str, object]
    actual_executed_stack_versions: Mapping[str, object]
    replay_result_ref: str
    paper_result_ref: str
    divergence_assessment_ref: str
    lane_execution_receipt_refs: tuple[str, ...]
    calibration_and_probability_quality: EvidenceSectionV1
    transaction_cost_decomposition: EvidenceSectionV1
    fill_and_queue_quality: EvidenceSectionV1
    latency_and_staleness: EvidenceSectionV1
    capacity_and_crowding: EvidenceSectionV1
    portfolio_marginal_contribution: EvidenceSectionV1
    false_discovery_and_overfit_controls: EvidenceSectionV1
    regime_and_scenario_outcomes: EvidenceSectionV1
    uncertainty_and_model_risk_reserves: EvidenceSectionV1
    agent_and_model_disagreement: EvidenceSectionV1
    no_trade_comparison: EvidenceSectionV1
    independent_review_state: str
    failure_and_negative_evidence_states: tuple[str, ...]
    source_and_provenance_refs: tuple[str, ...]
    d_evidence_reference_projection: ST12FEvidenceReferenceV1 | str
    g_handoff_projection: FToGHandoffReferencesV1 | str
    terminal_state: EvidenceBundleTerminalStateV1
    blocker_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        if self.schema_version != EVIDENCE_BUNDLE_SCHEMA_VERSION_V1 or self.contract_version != EVIDENCE_BUNDLE_CONTRACT_VERSION_V1:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "evidence-bundle schema differs")
        for name in (
            "evidence_id",
            "evidence_bundle_version",
            "component_or_template_ref",
            "input_lock_id",
            "replay_result_ref",
            "paper_result_ref",
            "divergence_assessment_ref",
            "independent_review_state",
        ):
            _text(getattr(self, name), name)
        object.__setattr__(self, "actual_executed_component_versions", _mapping(self.actual_executed_component_versions, "actual_executed_component_versions", required=False))
        object.__setattr__(self, "actual_executed_stack_versions", _mapping(self.actual_executed_stack_versions, "actual_executed_stack_versions", required=False))
        _refs(self.lane_execution_receipt_refs, "lane_execution_receipt_refs")
        _refs(self.failure_and_negative_evidence_states, "failure_and_negative_evidence_states")
        _refs(self.source_and_provenance_refs, "source_and_provenance_refs", required=True)
        _reason_tuple(self.blocker_codes, "blocker_codes")
        if type(self.terminal_state) is not EvidenceBundleTerminalStateV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "bundle terminal state must be typed")
        dispositions: list[EvidenceIdentityDispositionV1] = []
        for field_name in _SECTION_FIELDS_V1:
            section = getattr(self, field_name)
            if type(section) is not EvidenceSectionV1 or section.section_id != field_name:
                raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID, "bundle evidence section identity differs")
            dispositions.extend(section.identity_dispositions)
        identities = tuple(row.evidence_identity for row in dispositions)
        if len(dispositions) != 48 or len(set(identities)) != 48 or set(identities) != set(ST12F_EVIDENCE_IDENTITIES_V1):
            raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID, "bundle must dispose every one of the 48 evidence identities exactly once")
        closed = self.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
        if closed:
            if (
                type(self.d_evidence_reference_projection) is not ST12FEvidenceReferenceV1
                or self.d_evidence_reference_projection.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
                or type(self.g_handoff_projection) is not FToGHandoffReferencesV1
                or self.blocker_codes
                or self.independent_review_state != self.terminal_state.value
            ):
                raise ContractValidationError(ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED, "closed bundle requires segregated validation and exact projections")
        elif self.d_evidence_reference_projection != "UNAVAILABLE" or self.g_handoff_projection != "UNAVAILABLE":
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "non-closed bundle cannot project to D or G")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ComputationEvidenceBundleV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "bundle payload differs from exact 30-field roster")
        payload = dict(value)
        for name in _SECTION_FIELDS_V1:
            payload[name] = EvidenceSectionV1.from_canonical_mapping(payload[name])
        payload["lane_execution_receipt_refs"] = tuple(payload["lane_execution_receipt_refs"])
        payload["failure_and_negative_evidence_states"] = tuple(payload["failure_and_negative_evidence_states"])
        payload["source_and_provenance_refs"] = tuple(payload["source_and_provenance_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        payload["terminal_state"] = EvidenceBundleTerminalStateV1(payload["terminal_state"])
        if payload["d_evidence_reference_projection"] != "UNAVAILABLE":
            d_value = dict(payload["d_evidence_reference_projection"])
            d_value["evidence_state"] = ST12FEvidenceStateV1(d_value["evidence_state"])
            d_value["source_epoch_refs"] = tuple(d_value["source_epoch_refs"])
            d_value["no_effect_flags"] = NO_EFFECTS_V1
            payload["d_evidence_reference_projection"] = ST12FEvidenceReferenceV1(**d_value)
        if payload["g_handoff_projection"] != "UNAVAILABLE":
            payload["g_handoff_projection"] = FToGHandoffReferencesV1.from_canonical_mapping(payload["g_handoff_projection"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class CohortCompilationResolverProtocolV1(Protocol):
    def resolve_input_lock(self, input_lock_id: str) -> ImmutableReplayPaperInputLockV1: ...
    def resolve_expected_slot(self, compilation_id: str, lane: str, expected_result_contract_id: str) -> object: ...


class IndependentReviewResolverProtocolV1(Protocol):
    def resolve_review(self, review_ref: str) -> IndependentReviewRecordV1: ...


class EvidenceBundleCandidateResolverProtocolV1(Protocol):
    def resolve_bundle_candidate(
        self, request: BuildEvidenceBundleRequestV1
    ) -> ComputationEvidenceBundleV1: ...


def lane_packet_from_typed_record_v1(
    record: TypedValueRecordV1,
    *,
    lane: str,
) -> ReplayResultContractV1 | PaperResultContractV1:
    if type(record) is not TypedValueRecordV1:
        raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "lane packet wrapper must be exact TypedValueRecordV1")
    raw = {field.name: field.value for field in record.fields}
    expected_fields = {field.name for field in fields(ReplayResultContractV1)}
    if set(raw) != expected_fields:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "typed lane packet does not carry the exact 26-field roster")
    json_fields = {
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
        "failure_states",
        "limitations",
    }
    time_fields = {"point_in_time_cutoff", "started_at", "completed_at", "available_at", "closed_at"}
    payload: dict[str, object] = {}
    for field in record.fields:
        if field.name in json_fields:
            if field.kind is not TypedValueKindV1.TEXT:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, f"{field.name} must contain canonical JSON text")
            payload[field.name] = safe_json_loads(field.value)
        elif field.name in time_fields:
            if field.kind is not TypedValueKindV1.TEXT:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, f"{field.name} must contain a UTC timestamp")
            payload[field.name] = parse_utc(field.value, field_name=field.name)
        elif field.name == "fixture_only_not_evidence":
            if field.kind is not TypedValueKindV1.BOOLEAN:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "fixture flag must be typed boolean")
            payload[field.name] = field.value
        else:
            if field.kind is not TypedValueKindV1.TEXT:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, f"{field.name} must be typed text")
            payload[field.name] = field.value
    cls = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1 if lane == "PAPER" else None
    if cls is None:
        raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "lane must be exact REPLAY or PAPER")
    return cls.from_canonical_mapping(payload)


def _source_epoch_refs(lock: ImmutableReplayPaperInputLockV1) -> tuple[str, ...]:
    return tuple(f"{key}={lock.source_epochs[key]}" for key in sorted(lock.source_epochs))


class ComputationEvidenceServiceV1:
    """One evidence owner over injected compiler, review, and ST12-C owners."""

    def __init__(
        self,
        cohort_resolver: CohortCompilationResolverProtocolV1,
        persistence_adapter: PersistenceAdapterV1,
        *,
        independent_review_resolver: IndependentReviewResolverProtocolV1 | None = None,
        bundle_candidate_resolver: EvidenceBundleCandidateResolverProtocolV1 | None = None,
        producer_identity: str = "ComputationEvidenceServiceV1",
    ) -> None:
        if not isinstance(persistence_adapter, PersistenceAdapterV1) or persistence_adapter.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "OP14/OP15 require existing available ST12-C persistence")
        if not callable(getattr(cohort_resolver, "resolve_input_lock", None)) or not callable(getattr(cohort_resolver, "resolve_expected_slot", None)):
            raise ContractValidationError(ReasonCode.INPUT_OWNER_MISMATCH, "evidence service requires the canonical compiler resolver")
        self._cohort_resolver = cohort_resolver
        self._persistence = persistence_adapter
        self._review_resolver = independent_review_resolver
        self._bundle_candidate_resolver = bundle_candidate_resolver
        self._producer_identity = _text(producer_identity, "producer_identity")
        self._lane_results: dict[str, ReplayResultContractV1 | PaperResultContractV1] = {}
        self._slot_results: dict[tuple[str, str], str] = {}
        self._divergence: dict[str, DivergenceAssessmentV1] = {}
        self._bundles: dict[str, ComputationEvidenceBundleV1] = {}
        self._current_bundle_by_identity: dict[tuple[str, str], str] = {}

    def _load_contract(self, record_ref: str, expected_type: type[object]) -> object:
        spine = self._persistence.get_record(record_ref)
        if type(spine) is not EconomicReceiptEventSpineV1 or type(spine.typed_payload) is not ST12FEvidenceControlReceiptRecordV1:
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "typed ST12-F receipt is absent")
        return spine.typed_payload.reconstruct(expected_type)

    def resolve_lane_result(self, result_id: str, lane: str) -> ReplayResultContractV1 | PaperResultContractV1:
        value = self._lane_results.get(result_id)
        expected_type = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1 if lane == "PAPER" else None
        if expected_type is None:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "lane must be exact")
        if value is None:
            receipt_ref = f"ST12F-RECEIPT::{result_id}::{lane}_REGISTRATION"
            value = self._load_contract(receipt_ref, expected_type)  # type: ignore[assignment]
            self._lane_results[result_id] = value
        if type(value) is not expected_type:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "REPLAY/PAPER packets are non-interchangeable")
        return value

    def resolve_bundle(self, bundle_ref: str) -> ComputationEvidenceBundleV1:
        value = self._bundles.get(bundle_ref)
        if value is None:
            value = self._load_contract(bundle_ref, ComputationEvidenceBundleV1)  # type: ignore[assignment]
            self._bundles[bundle_ref] = value
        return value

    def _receipt(
        self,
        *,
        request: RegisterReplayPaperResultRequestV1 | BuildEvidenceBundleRequestV1,
        receipt_class: ST12FReceiptClassV1,
        contract: object,
        contract_id: str,
        input_lock: ImmutableReplayPaperInputLockV1,
        parent_ref: str = "EXPLICIT_ABSENCE",
        source_refs: tuple[str, ...] = (),
        terminal_state: str,
        reason_codes: tuple[ReasonCode, ...] = (),
    ) -> EconomicReceiptEventSpineV1:
        record_id = f"ST12F-RECEIPT::{contract_id}::{receipt_class.value}"
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=record_id,
            receipt_class=receipt_class,
            operation_id="ST10-OP::14" if type(request) is RegisterReplayPaperResultRequestV1 else "ST10-OP::15",
            request_id=request.request_id,
            idempotency_key=request.idempotency_key,
            contract_type=type(contract).__name__,
            contract_id=contract_id,
            contract_version=getattr(contract, "contract_version"),
            input_lock_id_or_explicit_absence=input_lock.input_lock_id,
            parent_version_ref_or_explicit_absence=parent_ref,
            canonical_contract_json=deterministic_json(contract),
            source_record_refs=source_refs,
            parameter_value_refs=input_lock.parameter_value_refs,
            source_epoch_refs=_source_epoch_refs(input_lock),
            typed_reason_codes=reason_codes,
            terminal_state=terminal_state,
            fixture_only_not_evidence=False,
        )
        return EconomicReceiptEventSpineV1(
            record_id=record_id,
            record_type=EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL,
            schema_version="QTT_ST12F_EVIDENCE_CONTROL_RECEIPT_SPINE_V1",
            semantic_owner="ComputationEvidenceServiceV1",
            implementation_owner="ComputationEvidenceServiceV1",
            context_ref=request.context.context_id,
            effective_at=input_lock.decision_time,
            recorded_at=request.requested_at,
            causation_id=input_lock.causation_id,
            correlation_id=input_lock.correlation_id,
            traceparent=request.traceparent,
            tracestate=request.tracestate,
            sequence=0,
            aggregate_id=contract_id,
            aggregate_version=1,
            authority_class="EVIDENCE_CUSTODY_NO_EFFECT",
            typed_payload=payload,
            no_effect_flags=NO_EFFECTS_V1,
        )

    def _persist_one(
        self,
        *,
        request: RegisterReplayPaperResultRequestV1 | BuildEvidenceBundleRequestV1,
        spine: EconomicReceiptEventSpineV1,
        identity_class: str,
    ) -> EconomicReceiptEventSpineV1:
        claim = IdempotencyClaimReceiptV1(
            claim_id=f"ST12F-IDEMPOTENCY::{request.idempotency_key}::{identity_class}",
            idempotency_key=request.idempotency_key,
            identity_class=identity_class,
            canonical_request_json=canonical_request_json_v1(request),
            claim_state=IdempotencyClaimStateV1.ACQUIRED,
            result_record_ref=None,
            created_at=request.requested_at,
            completed_at=None,
            failure_code=None,
        )
        transaction = self._persistence.begin_transaction()
        try:
            acquisition = self._persistence.acquire_idempotency_claim(transaction, claim)
            if acquisition.outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD:
                transaction.rollback()
                original = self._persistence.get_record(acquisition.original_result_ref or "")
                if type(original) is not EconomicReceiptEventSpineV1:
                    raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "idempotent result receipt is absent")
                return original
            if acquisition.outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD:
                raise IdempotencyContractError(ReasonCode.IDEMPOTENCY_CONFLICT, "same key binds a different canonical request")
            if acquisition.outcome is not IdempotencyOutcomeV1.ACQUIRED:
                raise IdempotencyContractError(ReasonCode.IDEMPOTENCY_IN_PROGRESS, "same canonical request is already in progress")
            self._persistence.insert_receipt_record(transaction, spine)
            self._persistence.insert_state_transition(
                transaction,
                StateTransitionReceiptV1(
                    transition_id=f"{claim.claim_id}::COMPLETED",
                    aggregate_id=claim.claim_id,
                    transition_family="IDEMPOTENCY_CLAIM_STATE_MACHINE_V1",
                    prior_state="ACQUIRED",
                    event_class=f"{identity_class}_COMPLETED",
                    candidate_state="COMPLETED",
                    disposition=TransitionDispositionV1.ACCEPTED,
                    event_identity=request.request_id,
                    aggregate_version_before=0,
                    aggregate_version_after=1,
                    effective_at=request.requested_at,
                    recorded_at=request.requested_at,
                    reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                    reconciliation_required=False,
                ),
            )
            self._persistence.bind_idempotency_result(transaction, acquisition.claim_ref, spine.record_id, request.requested_at)
            transaction.commit()
            return spine
        except BaseException:
            if transaction.is_active:
                transaction.rollback()
            raise

    def register_result(
        self,
        request: RegisterReplayPaperResultRequestV1,
        packet: ReplayResultContractV1 | PaperResultContractV1 | None = None,
    ) -> ReplayResultContractV1 | PaperResultContractV1:
        initialize_st12f_parameter_registry_v1()
        if type(request) is not RegisterReplayPaperResultRequestV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP14 delegate requires exact request")
        value = lane_packet_from_typed_record_v1(request.result_packet, lane=request.lane) if packet is None else packet
        expected_type = ReplayResultContractV1 if request.lane == "REPLAY" else PaperResultContractV1
        if type(value) is not expected_type:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "OP14 rejects cross-lane packet substitution")
        lock = self._cohort_resolver.resolve_input_lock(request.input_lock_id)
        if value.input_lock_id != lock.input_lock_id or request.input_lock_id != lock.input_lock_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "caller and packet lock assertions differ from canonical lock")
        slot = self._cohort_resolver.resolve_expected_slot(request.cohort_instance_id, request.lane, value.expected_result_contract_id)
        if (
            getattr(slot, "input_lock_id", None) != lock.input_lock_id
            or getattr(slot, "cohort_template_id", None) != value.cohort_template_id
            or value.point_in_time_cutoff != lock.point_in_time_cutoff
            or dict(value.implementation_versions) != dict(lock.implementation_versions)
            or dict(value.source_epochs) != dict(lock.source_epochs)
            or value.accounting_definition != deterministic_json(lock.accounting_definition)
        ):
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "lane packet differs from exact lock/slot/version/epoch/accounting pins")
        natural_slot = (lock.input_lock_id, value.expected_result_contract_id)
        existing_id = self._slot_results.get(natural_slot)
        if existing_id is not None:
            existing = self._lane_results[existing_id]
            if deterministic_json(existing) == deterministic_json(value):
                return existing
            raise ContractValidationError(ReasonCode.ST12F_RESULT_SLOT_CONFLICT, "a competing result already owns this immutable slot")
        self._lane_results[value.result_id] = value
        self._slot_results[natural_slot] = value.result_id
        if value.fixture_only_not_evidence:
            return value
        receipt_class = ST12FReceiptClassV1.REPLAY_REGISTRATION if request.lane == "REPLAY" else ST12FReceiptClassV1.PAPER_REGISTRATION
        spine = self._receipt(
            request=request,
            receipt_class=receipt_class,
            contract=value,
            contract_id=value.result_id,
            input_lock=lock,
            source_refs=(value.run_reference,),
            terminal_state=f"{request.lane}_REGISTERED",
        )
        self._persist_one(request=request, spine=spine, identity_class="ST10-OP::14")
        return value

    def register_divergence(self, assessment: DivergenceAssessmentV1) -> None:
        if type(assessment) is not DivergenceAssessmentV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "divergence must be exact typed contract")
        replay = self.resolve_lane_result(assessment.replay_result_ref, "REPLAY")
        paper = self.resolve_lane_result(assessment.paper_result_ref, "PAPER")
        if replay.input_lock_id != assessment.input_lock_id or paper.input_lock_id != assessment.input_lock_id or replay.cohort_template_id != assessment.cohort_template_id or paper.cohort_template_id != assessment.cohort_template_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "divergence inputs do not share one lock/template")
        self._divergence[assessment.assessment_id] = assessment

    def build_bundle(
        self,
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1 | None = None,
    ) -> ComputationEvidenceBundleV1:
        initialize_st12f_parameter_registry_v1()
        if candidate is None and self._bundle_candidate_resolver is not None:
            candidate = self._bundle_candidate_resolver.resolve_bundle_candidate(request)
        if type(request) is not BuildEvidenceBundleRequestV1 or type(candidate) is not ComputationEvidenceBundleV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP15 requires exact request and canonical candidate")
        lock = self._cohort_resolver.resolve_input_lock(request.input_lock_id)
        if candidate.input_lock_id != lock.input_lock_id or candidate.component_or_template_ref != request.component_id or request.required_lanes != ("REPLAY", "PAPER"):
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "OP15 scope differs from canonical lock/component/dual lane")
        replay = self.resolve_lane_result(candidate.replay_result_ref, "REPLAY")
        paper = self.resolve_lane_result(candidate.paper_result_ref, "PAPER")
        if replay.fixture_only_not_evidence or paper.fixture_only_not_evidence:
            raise ContractValidationError(ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE, "fixture packets cannot be persisted or counted as evidence")
        if replay.input_lock_id != lock.input_lock_id or paper.input_lock_id != lock.input_lock_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "bundle lanes do not share the canonical lock")
        if candidate.divergence_assessment_ref not in self._divergence:
            raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_INCOMPLETE, "bundle divergence assessment is unresolved")
        previous_ref = self._current_bundle_by_identity.get((candidate.evidence_id, candidate.input_lock_id))
        closed = candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
        if closed:
            review_refs = [ref for ref in request.evidence_record_refs if self._review_resolver is not None and ref.startswith("ST12F-REVIEW::")]
            if len(review_refs) != 1 or previous_ref is None or self._review_resolver is None:
                raise ContractValidationError(ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED, "closed version requires one separate pre-existing review and prior version")
            review = self._review_resolver.resolve_review(review_refs[0])
            previous = self.resolve_bundle(previous_ref)
            if (
                type(review) is not IndependentReviewRecordV1
                or review.prior_bundle_ref != previous_ref
                or review.evidence_id != candidate.evidence_id
                or review.input_lock_id != lock.input_lock_id
                or review.bundle_producer_identity == review.reviewer_identity
                or review.bundle_producer_identity != self._producer_identity
                or review.decision is not IndependentReviewDecisionV1.VALIDATED
                or review.reviewed_source_epoch_refs != _source_epoch_refs(lock)
                or review.valid_until < request.requested_at
                or previous.terminal_state is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            ):
                raise ContractValidationError(ReasonCode.ST12F_SELF_REVIEW_FORBIDDEN, "independent review does not close the exact prior bundle version")
        elif candidate.terminal_state is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW:
            raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_INCOMPLETE, "initial OP15 bundle must be ready for independent review")
        spine = self._receipt(
            request=request,
            receipt_class=ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION,
            contract=candidate,
            contract_id=candidate.evidence_bundle_version,
            input_lock=lock,
            parent_ref=previous_ref or "EXPLICIT_ABSENCE",
            source_refs=request.evidence_record_refs,
            terminal_state=candidate.terminal_state.value,
            reason_codes=candidate.blocker_codes,
        )
        persisted = self._persist_one(request=request, spine=spine, identity_class="ST10-OP::15")
        value = persisted.typed_payload.reconstruct(ComputationEvidenceBundleV1)
        self._bundles[persisted.record_id] = value
        self._bundles[value.evidence_bundle_version] = value
        self._current_bundle_by_identity[(value.evidence_id, value.input_lock_id)] = persisted.record_id
        return value

    def read_evidence_reference(
        self,
        context: object,
        *,
        causation_id: str,
        correlation_id: str,
    ) -> ST12FEvidenceReferenceV1:
        context_id = _text(getattr(context, "context_id", ""), "context_id")
        candidates = [
            bundle
            for bundle in self._bundles.values()
            if bundle.component_or_template_ref == context_id
            and bundle.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
        ]
        if not candidates:
            observed = parse_utc(getattr(context, "as_of"), field_name="as_of")
            return ST12FEvidenceReferenceV1(
                evidence_state=ST12FEvidenceStateV1.EVIDENCE_INSUFFICIENT_FAIL_CLOSED,
                evidence_ref="EXPLICIT_ABSENCE",
                lane="REPLAY_PAPER",
                dataset_grade_ref="EXPLICIT_ABSENCE",
                venue_semantic_binding_ref="EXPLICIT_ABSENCE",
                cross_venue_equivalence_ref="EXPLICIT_ABSENCE",
                observed_at=observed,
                valid_until=observed,
                policy_version="ST12F_EVIDENCE_POLICY_V1_4",
                causation_id=causation_id,
                correlation_id=correlation_id,
            )
        bundle = sorted(candidates, key=lambda item: item.evidence_bundle_version)[-1]
        reference = bundle.d_evidence_reference_projection
        if type(reference) is not ST12FEvidenceReferenceV1:
            raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_INCOMPLETE, "closed bundle lacks its canonical D projection")
        if reference.causation_id != causation_id or reference.correlation_id != correlation_id:
            raise ContractValidationError(ReasonCode.INPUT_SCOPE_MISMATCH, "F reference causation/correlation differs from request")
        return reference

    @property
    def immutable_indexes(self) -> Mapping[str, Mapping[object, object]]:
        return MappingProxyType(
            {
                "lane_results": MappingProxyType(self._lane_results),
                "slot_results": MappingProxyType(self._slot_results),
                "divergence": MappingProxyType(self._divergence),
                "bundles": MappingProxyType(self._bundles),
                "current_bundles": MappingProxyType(self._current_bundle_by_identity),
            }
        )


if (
    len(fields(ReplayResultContractV1)) != 26
    or len(fields(PaperResultContractV1)) != 26
    or len(fields(DivergenceAssessmentV1)) != 18
    or len(fields(ComputationEvidenceBundleV1)) != 30
    or len(ST12F_EVIDENCE_IDENTITIES_V1) != 48
):
    raise ContractValidationError(
        ReasonCode.SCHEMA_MISMATCH,
        "ST12-F canonical contract denominator differs from owner closure",
    )
