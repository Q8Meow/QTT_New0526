"""Canonical ST12-F lane, divergence, review, and evidence-bundle owner."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
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
from .model_risk import ModelRiskControlStateV1, ModelRiskEvidenceAssessmentV1
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
from .quantum_benchmark import (
    QuantumClassicalNoTradeComparisonV1,
    QuantumTraceValidationReceiptV1,
)
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


_EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1 = MappingProxyType(
    {
        (
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        ): "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
        (
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        ): "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
        (
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        ): "SEPARATE_REVIEW_RECEIPT_PASS_AND_ZERO_HARD_VETOES",
        (
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
        ): "SEPARATE_REVIEW_RECEIPT_REJECT",
        (
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.STALE,
        ): "TTL_SOURCE_EPOCH_PARAMETER_IMPLEMENTATION_OR_CONTEXT_CHANGE",
        (
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.SUPERSEDED,
        ): "NEWER_VALIDATED_BUNDLE_VERSION_SAME_IDENTITY",
    }
)

_EVIDENCE_BUNDLE_INITIAL_STATES_V1 = frozenset(
    {
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT,
        EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
    }
)


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
    handoff_id: str
    contract_version: str
    input_lock_id: str
    source_epoch_refs: tuple[str, ...]
    observed_at: datetime
    valid_until: datetime
    terminal_state: str
    evidence_bundle_ref: str
    no_trade_blocker_refs: tuple[str, ...]
    champion_challenger_evidence_refs: tuple[str, ...]
    portfolio_utility_refs: tuple[str, ...]
    quantum_classical_comparison_receipt_ref: str
    read_only: bool = True

    def __post_init__(self) -> None:
        _text(self.handoff_id, "handoff_id")
        _text(self.input_lock_id, "input_lock_id")
        if self.contract_version != "1.4":
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "F-to-G handoff contract version differs",
            )
        _refs(self.source_epoch_refs, "source_epoch_refs", required=True)
        observed = parse_utc(self.observed_at, field_name="observed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "valid_until", valid_until)
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.ST12F_BUNDLE_STALE,
                "F-to-G validity precedes observation",
            )
        if self.terminal_state != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "F-to-G handoff requires a closed independently validated bundle",
            )
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
        payload["source_epoch_refs"] = tuple(payload["source_epoch_refs"])
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
            payload["d_evidence_reference_projection"] = (
                ST12FEvidenceReferenceV1.from_canonical_mapping(
                    payload["d_evidence_reference_projection"]
                )
            )
        if payload["g_handoff_projection"] != "UNAVAILABLE":
            payload["g_handoff_projection"] = FToGHandoffReferencesV1.from_canonical_mapping(payload["g_handoff_projection"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class FToDEvidenceReferenceQueryV1:
    """Exact read-only D query; it carries no activation or execution authority."""

    query_id: str
    requested_evidence_id: str
    requested_component_or_template_ref: str
    expected_input_lock_id: str
    expected_source_epoch_refs: tuple[str, ...]
    evaluated_at: datetime
    request_read_lineage_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "query_id",
            "requested_evidence_id",
            "requested_component_or_template_ref",
            "expected_input_lock_id",
        ):
            _text(getattr(self, name), name)
        _refs(
            self.expected_source_epoch_refs,
            "expected_source_epoch_refs",
            required=True,
        )
        _refs(
            self.request_read_lineage_refs,
            "request_read_lineage_refs",
            required=True,
        )
        object.__setattr__(
            self,
            "evaluated_at",
            parse_utc(self.evaluated_at, field_name="evaluated_at"),
        )


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

    supports_typed_reference_query = True

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
        self._slot_results: dict[tuple[str, str, str, str], str] = {}
        self._divergence: dict[str, DivergenceAssessmentV1] = {}
        self._bundles: dict[str, ComputationEvidenceBundleV1] = {}
        self._current_bundle_by_identity: dict[tuple[str, str, str], str] = {}
        self._reviews: dict[str, IndependentReviewRecordV1] = {}
        self._d_references: dict[str, ST12FEvidenceReferenceV1] = {}
        self._g_handoffs: dict[str, FToGHandoffReferencesV1] = {}
        self._last_committed_receipt_refs: tuple[str, ...] = ()
        self._rebuild_caches_from_durable_receipts()

    @staticmethod
    def _contract_type_for_receipt_class(
        receipt_class: ST12FReceiptClassV1,
    ) -> type[object]:
        mapping: Mapping[ST12FReceiptClassV1, type[object]] = {
            ST12FReceiptClassV1.REPLAY_REGISTRATION: ReplayResultContractV1,
            ST12FReceiptClassV1.PAPER_REGISTRATION: PaperResultContractV1,
            ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT: DivergenceAssessmentV1,
            ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT: ModelRiskEvidenceAssessmentV1,
            ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION: QuantumTraceValidationReceiptV1,
            ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION: DeterministicEvidenceAnnotationContractV1,
            ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION: ComputationEvidenceBundleV1,
            ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION: IndependentReviewRecordV1,
            ST12FReceiptClassV1.D_EVIDENCE_REFERENCE: ST12FEvidenceReferenceV1,
            ST12FReceiptClassV1.G_HANDOFF_REFERENCE: FToGHandoffReferencesV1,
        }
        try:
            return mapping[receipt_class]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "receipt class is not owned by OP14/OP15",
            ) from exc

    def _durable_receipt_spines(self) -> tuple[EconomicReceiptEventSpineV1, ...]:
        maximum = datetime.max.replace(tzinfo=UTC)
        rows = self._persistence.reconstruct_as_of(
            effective_cutoff=maximum,
            recorded_cutoff=maximum,
            aggregate_scope=(),
        )
        return tuple(
            sorted(
                (
                    row
                    for row in rows
                    if type(row) is EconomicReceiptEventSpineV1
                    and type(row.typed_payload) is ST12FEvidenceControlReceiptRecordV1
                ),
                key=lambda row: (row.recorded_at, row.record_id),
            )
        )

    def _validate_receipt_lock_metadata(
        self,
        spine: EconomicReceiptEventSpineV1,
    ) -> None:
        payload = spine.typed_payload
        assert type(payload) is ST12FEvidenceControlReceiptRecordV1
        if payload.input_lock_id_or_explicit_absence == "EXPLICIT_ABSENCE":
            if payload.parameter_value_refs or payload.source_epoch_refs:
                raise ContractValidationError(
                    ReasonCode.SCHEMA_MISMATCH,
                    "lock-absent receipt carries parameter or epoch pins",
                )
            return
        lock = self._cohort_resolver.resolve_input_lock(
            payload.input_lock_id_or_explicit_absence
        )
        if (
            payload.parameter_value_refs != lock.parameter_value_refs
            or payload.source_epoch_refs != _source_epoch_refs(lock)
        ):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "receipt parameter or epoch pins differ from the canonical input lock",
            )

    @staticmethod
    def _natural_slot(
        value: ReplayResultContractV1 | PaperResultContractV1,
        lane: str,
    ) -> tuple[str, str, str, str]:
        return (
            value.input_lock_id,
            lane,
            value.cohort_template_id,
            value.expected_result_contract_id,
        )

    def _rebuild_caches_from_durable_receipts(self) -> None:
        lane_results: dict[str, ReplayResultContractV1 | PaperResultContractV1] = {}
        slots: dict[tuple[str, str, str, str], str] = {}
        divergence: dict[str, DivergenceAssessmentV1] = {}
        bundles: dict[str, ComputationEvidenceBundleV1] = {}
        bundle_rows: list[
            tuple[str, ComputationEvidenceBundleV1, str]
        ] = []
        current: dict[tuple[str, str, str], str] = {}
        reviews: dict[str, IndependentReviewRecordV1] = {}
        d_references: dict[str, ST12FEvidenceReferenceV1] = {}
        g_handoffs: dict[str, FToGHandoffReferencesV1] = {}
        for spine in self._durable_receipt_spines():
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class in {
                ST12FReceiptClassV1.COHORT_COMPILATION,
                ST12FReceiptClassV1.INPUT_LOCK,
            }:
                continue
            expected_type = self._contract_type_for_receipt_class(payload.receipt_class)
            value = payload.reconstruct(expected_type)
            self._validate_receipt_lock_metadata(spine)
            if type(value) in {ReplayResultContractV1, PaperResultContractV1}:
                lane = (
                    "REPLAY"
                    if type(value) is ReplayResultContractV1
                    else "PAPER"
                )
                assert isinstance(value, ReplayResultContractV1 | PaperResultContractV1)
                slot = self._natural_slot(value, lane)
                if (
                    value.result_id in lane_results
                    and deterministic_json(lane_results[value.result_id])
                    != deterministic_json(value)
                ):
                    raise ContractValidationError(
                        ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                        "durable result identity binds competing canonical packets",
                    )
                previous_id = slots.get(slot)
                if previous_id is not None and deterministic_json(lane_results[previous_id]) != deterministic_json(value):
                    raise ContractValidationError(
                        ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                        "durable natural slot has competing canonical packets",
                    )
                lane_results[value.result_id] = value
                slots[slot] = value.result_id
            elif type(value) is DivergenceAssessmentV1:
                divergence[value.assessment_id] = value
            elif type(value) is ComputationEvidenceBundleV1:
                bundles[spine.record_id] = value
                bundles[value.evidence_bundle_version] = value
                bundle_rows.append(
                    (
                        spine.record_id,
                        value,
                        payload.parent_version_ref_or_explicit_absence,
                    )
                )
            elif type(value) is IndependentReviewRecordV1:
                reviews[value.review_id] = value
                reviews[spine.record_id] = value
            elif type(value) is ST12FEvidenceReferenceV1:
                d_references[value.reference_id] = value
                d_references[spine.record_id] = value
            elif type(value) is FToGHandoffReferencesV1:
                g_handoffs[value.handoff_id] = value
                g_handoffs[spine.record_id] = value
        identities = {
            (
                value.evidence_id,
                value.input_lock_id,
                value.component_or_template_ref,
            )
            for _, value, _ in bundle_rows
        }
        for identity in identities:
            current[identity] = self._bundle_leaf_ref(
                tuple(
                    row
                    for row in bundle_rows
                    if (
                        row[1].evidence_id,
                        row[1].input_lock_id,
                        row[1].component_or_template_ref,
                    )
                    == identity
                )
            )
        self._lane_results = lane_results
        self._slot_results = slots
        self._divergence = divergence
        self._bundles = bundles
        self._current_bundle_by_identity = current
        self._reviews = reviews
        self._d_references = d_references
        self._g_handoffs = g_handoffs

    def _load_contract(self, record_ref: str, expected_type: type[object]) -> object:
        spine = self._persistence.get_record(record_ref)
        if type(spine) is not EconomicReceiptEventSpineV1 or type(spine.typed_payload) is not ST12FEvidenceControlReceiptRecordV1:
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "typed ST12-F receipt is absent")
        value = spine.typed_payload.reconstruct(expected_type)
        self._validate_receipt_lock_metadata(spine)
        return value

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

    def resolve_review(self, review_ref: str) -> IndependentReviewRecordV1:
        value = self._reviews.get(review_ref)
        if value is None:
            receipt_ref = (
                review_ref
                if review_ref.startswith("ST12F-RECEIPT::")
                else f"ST12F-RECEIPT::{review_ref}::INDEPENDENT_REVIEW_VERSION"
            )
            value = self._load_contract(receipt_ref, IndependentReviewRecordV1)  # type: ignore[assignment]
            self._reviews[review_ref] = value
            self._reviews[receipt_ref] = value
        return value

    def resolve_control_receipt(
        self,
        receipt_ref: str,
        expected_type: type[object],
    ) -> object:
        """Canonical read path for every OP14/OP15 receipt class."""

        return self._load_contract(receipt_ref, expected_type)

    @property
    def last_committed_receipt_refs(self) -> tuple[str, ...]:
        return self._last_committed_receipt_refs

    @staticmethod
    def _contract_receipt_parts(
        contract: object,
    ) -> tuple[
        ST12FReceiptClassV1,
        str,
        str,
        tuple[str, ...],
        str,
        tuple[ReasonCode, ...],
    ]:
        if type(contract) is ReplayResultContractV1:
            return (
                ST12FReceiptClassV1.REPLAY_REGISTRATION,
                contract.result_id,
                "EXPLICIT_ABSENCE",
                (contract.run_reference,),
                "REPLAY_REGISTERED",
                (),
            )
        if type(contract) is PaperResultContractV1:
            return (
                ST12FReceiptClassV1.PAPER_REGISTRATION,
                contract.result_id,
                "EXPLICIT_ABSENCE",
                (contract.run_reference,),
                "PAPER_REGISTERED",
                (),
            )
        if type(contract) is DivergenceAssessmentV1:
            return (
                ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT,
                contract.assessment_id,
                "EXPLICIT_ABSENCE",
                (contract.replay_result_ref, contract.paper_result_ref),
                contract.terminal_state.value,
                contract.typed_blockers,
            )
        if type(contract) is ModelRiskEvidenceAssessmentV1:
            return (
                ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT,
                contract.assessment_id,
                "EXPLICIT_ABSENCE",
                contract.receipt_refs,
                contract.terminal_state,
                contract.blocker_codes,
            )
        if type(contract) is QuantumTraceValidationReceiptV1:
            return (
                ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION,
                contract.receipt_id,
                "EXPLICIT_ABSENCE",
                (
                    contract.trace_id,
                    contract.strongest_classical_receipt_ref,
                    contract.no_trade_receipt_ref,
                ),
                contract.terminal_state,
                (),
            )
        if type(contract) is DeterministicEvidenceAnnotationContractV1:
            return (
                ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION,
                contract.annotation_id,
                "EXPLICIT_ABSENCE",
                tuple(
                    dict.fromkeys(
                        (
                            *contract.evidence_bundle_refs,
                            *(row.evidence_receipt_ref for row in contract.canonical_numeric_evidence),
                            *contract.deterministic_numeric_recheck_receipt_refs,
                        )
                    )
                ),
                "ANNOTATION_VALIDATED_NO_EFFECT",
                (),
            )
        if type(contract) is ComputationEvidenceBundleV1:
            return (
                ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION,
                contract.evidence_bundle_version,
                "EXPLICIT_ABSENCE",
                contract.source_and_provenance_refs,
                contract.terminal_state.value,
                contract.blocker_codes,
            )
        if type(contract) is IndependentReviewRecordV1:
            return (
                ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
                contract.review_id,
                contract.prior_bundle_ref,
                (contract.prior_bundle_ref, contract.authority_receipt_ref),
                contract.decision.value,
                contract.blocker_codes,
            )
        if type(contract) is ST12FEvidenceReferenceV1:
            return (
                ST12FReceiptClassV1.D_EVIDENCE_REFERENCE,
                contract.reference_id,
                contract.evidence_ref,
                (contract.evidence_ref,),
                contract.terminal_state,
                (),
            )
        if type(contract) is FToGHandoffReferencesV1:
            return (
                ST12FReceiptClassV1.G_HANDOFF_REFERENCE,
                contract.handoff_id,
                contract.evidence_bundle_ref,
                tuple(
                    dict.fromkeys(
                        (
                            contract.evidence_bundle_ref,
                            *contract.no_trade_blocker_refs,
                            *contract.champion_challenger_evidence_refs,
                            *contract.portfolio_utility_refs,
                            contract.quantum_classical_comparison_receipt_ref,
                        )
                    )
                ),
                contract.terminal_state,
                (),
            )
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "OP14/OP15 contract is outside the receipt allowlist",
        )

    def _receipt(
        self,
        *,
        request: RegisterReplayPaperResultRequestV1 | BuildEvidenceBundleRequestV1,
        contract: object,
        input_lock: ImmutableReplayPaperInputLockV1,
        bundle_parent_ref: str | None = None,
    ) -> EconomicReceiptEventSpineV1:
        (
            receipt_class,
            contract_id,
            parent_ref,
            source_refs,
            terminal_state,
            reason_codes,
        ) = self._contract_receipt_parts(contract)
        if receipt_class is ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
            if bundle_parent_ref is None:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle receipt construction requires the service-resolved durable parent",
                )
            parent_ref = _text(bundle_parent_ref, "bundle_parent_ref")
        elif bundle_parent_ref is not None:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "non-bundle receipt cannot carry a bundle parent override",
            )
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

    def _persist_many(
        self,
        *,
        request: RegisterReplayPaperResultRequestV1 | BuildEvidenceBundleRequestV1,
        spines: tuple[EconomicReceiptEventSpineV1, ...],
        primary_record_ref: str,
        identity_class: str,
        extra_transitions: tuple[StateTransitionReceiptV1, ...] = (),
    ) -> EconomicReceiptEventSpineV1:
        if not spines or primary_record_ref not in {row.record_id for row in spines}:
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "atomic ST12-F persistence requires a primary receipt",
            )
        canonical_request = deterministic_json(
            {
                "request": safe_json_loads(canonical_request_json_v1(request)),
                "contracts": [
                    safe_json_loads(row.typed_payload.canonical_contract_json)
                    for row in spines
                ],
            }
        )
        claim = IdempotencyClaimReceiptV1(
            claim_id=f"ST12F-IDEMPOTENCY::{request.idempotency_key}::{identity_class}",
            idempotency_key=request.idempotency_key,
            identity_class=identity_class,
            canonical_request_json=canonical_request,
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
            for spine in spines:
                self._persistence.insert_receipt_record(transaction, spine)
                self._persistence.insert_state_transition(
                    transaction,
                    StateTransitionReceiptV1(
                        transition_id=f"ST12F-CONTROL-STATE::{spine.record_id}",
                        aggregate_id=f"ST12F-CONTROL::{spine.record_id}",
                        transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
                        prior_state="NEW",
                        event_class="ST12F_CONTROL_RECEIPT_COMMITTED",
                        candidate_state="ACTIVE",
                        disposition=TransitionDispositionV1.ACCEPTED,
                        event_identity=spine.record_id,
                        aggregate_version_before=0,
                        aggregate_version_after=1,
                        effective_at=spine.effective_at,
                        recorded_at=spine.recorded_at,
                        reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                        reconciliation_required=False,
                    ),
                )
            for transition in extra_transitions:
                self._persistence.insert_state_transition(transaction, transition)
            self._persistence.insert_state_transition(
                transaction,
                StateTransitionReceiptV1(
                    transition_id=f"{claim.claim_id}::ACQUIRED",
                    aggregate_id=claim.claim_id,
                    transition_family="IDEMPOTENCY_CLAIM_STATE_MACHINE_V1",
                    prior_state="UNSEEN",
                    event_class=f"{identity_class}_ACQUIRED",
                    candidate_state="ACQUIRED",
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
                    aggregate_version_before=1,
                    aggregate_version_after=2,
                    effective_at=request.requested_at,
                    recorded_at=request.requested_at,
                    reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                    reconciliation_required=False,
                ),
            )
            self._persistence.bind_idempotency_result(
                transaction,
                acquisition.claim_ref,
                primary_record_ref,
                request.requested_at,
            )
            transaction.commit()
            primary = self._persistence.get_record(primary_record_ref)
            if type(primary) is not EconomicReceiptEventSpineV1:
                raise PersistenceContractError(
                    ReasonCode.OWNER_DATA_MISSING,
                    "committed primary ST12-F receipt is absent",
                )
            return primary
        except BaseException:
            if transaction.is_active:
                transaction.rollback()
            raise

    def register_result(
        self,
        request: RegisterReplayPaperResultRequestV1,
        packet: ReplayResultContractV1 | PaperResultContractV1 | None = None,
    ) -> ReplayResultContractV1 | PaperResultContractV1:
        self._last_committed_receipt_refs = ()
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
        natural_slot = self._natural_slot(value, request.lane)
        durable_lanes, durable_slots = self._durable_lane_index()
        existing_id = durable_slots.get(natural_slot)
        if existing_id is not None:
            existing = durable_lanes[existing_id]
            if deterministic_json(existing) == deterministic_json(value):
                receipt_class = (
                    ST12FReceiptClassV1.REPLAY_REGISTRATION
                    if request.lane == "REPLAY"
                    else ST12FReceiptClassV1.PAPER_REGISTRATION
                )
                self._last_committed_receipt_refs = (
                    f"ST12F-RECEIPT::{existing.result_id}::{receipt_class.value}",
                )
                return existing
            raise ContractValidationError(ReasonCode.ST12F_RESULT_SLOT_CONFLICT, "a competing result already owns this immutable slot")
        if value.fixture_only_not_evidence:
            return value
        spine = self._receipt(
            request=request,
            contract=value,
            input_lock=lock,
        )
        slot_identity = "::".join(natural_slot)
        slot_transition = StateTransitionReceiptV1(
            transition_id=f"ST12F-NATURAL-SLOT::{slot_identity}::OWNED",
            aggregate_id=f"ST12F-NATURAL-SLOT::{slot_identity}",
            transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
            prior_state="NEW",
            event_class="ST12F_RESULT_SLOT_OWNED",
            candidate_state="ACTIVE",
            disposition=TransitionDispositionV1.ACCEPTED,
            event_identity=spine.record_id,
            aggregate_version_before=0,
            aggregate_version_after=1,
            effective_at=value.closed_at,
            recorded_at=value.closed_at,
            reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
            reconciliation_required=False,
        )
        try:
            persisted = self._persist_many(
                request=request,
                spines=(spine,),
                primary_record_ref=spine.record_id,
                identity_class="ST10-OP::14",
                extra_transitions=(slot_transition,),
            )
        except PersistenceContractError as exc:
            check_lanes, check_slots = self._durable_lane_index()
            owner_id = check_slots.get(natural_slot)
            if owner_id is not None and deterministic_json(check_lanes[owner_id]) != deterministic_json(value):
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "a competing durable result owns this immutable natural slot",
                ) from exc
            raise
        committed = persisted.typed_payload.reconstruct(expected_type)
        self._lane_results[value.result_id] = committed  # type: ignore[assignment]
        self._slot_results[natural_slot] = value.result_id
        self._last_committed_receipt_refs = (persisted.record_id,)
        return committed  # type: ignore[return-value]

    def _durable_lane_index(
        self,
    ) -> tuple[
        dict[str, ReplayResultContractV1 | PaperResultContractV1],
        dict[tuple[str, str, str, str], str],
    ]:
        lanes: dict[str, ReplayResultContractV1 | PaperResultContractV1] = {}
        slots: dict[tuple[str, str, str, str], str] = {}
        for spine in self._durable_receipt_spines():
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class not in {
                ST12FReceiptClassV1.REPLAY_REGISTRATION,
                ST12FReceiptClassV1.PAPER_REGISTRATION,
            }:
                continue
            lane = (
                "REPLAY"
                if payload.receipt_class is ST12FReceiptClassV1.REPLAY_REGISTRATION
                else "PAPER"
            )
            expected = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1
            value = payload.reconstruct(expected)
            assert isinstance(value, ReplayResultContractV1 | PaperResultContractV1)
            self._validate_receipt_lock_metadata(spine)
            if (
                value.result_id in lanes
                and deterministic_json(lanes[value.result_id])
                != deterministic_json(value)
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "durable result identity binds competing canonical packets",
                )
            slot = self._natural_slot(value, lane)
            owner = slots.get(slot)
            if owner is not None and deterministic_json(lanes[owner]) != deterministic_json(value):
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "durable natural slot contains competing results",
                )
            lanes[value.result_id] = value
            slots[slot] = value.result_id
        return lanes, slots

    def _validate_divergence(self, assessment: DivergenceAssessmentV1) -> None:
        if type(assessment) is not DivergenceAssessmentV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "divergence must be exact typed contract")
        replay = self.resolve_lane_result(assessment.replay_result_ref, "REPLAY")
        paper = self.resolve_lane_result(assessment.paper_result_ref, "PAPER")
        if replay.input_lock_id != assessment.input_lock_id or paper.input_lock_id != assessment.input_lock_id or replay.cohort_template_id != assessment.cohort_template_id or paper.cohort_template_id != assessment.cohort_template_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "divergence inputs do not share one lock/template")

    def register_divergence(
        self,
        assessment: DivergenceAssessmentV1,
        request: BuildEvidenceBundleRequestV1,
    ) -> DivergenceAssessmentV1:
        """Persist divergence through the existing OP15 transaction contract."""

        if type(request) is not BuildEvidenceBundleRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "divergence registration requires the existing OP15 request",
            )
        self._validate_divergence(assessment)
        lock = self._cohort_resolver.resolve_input_lock(assessment.input_lock_id)
        spine = self._receipt(request=request, contract=assessment, input_lock=lock)
        persisted = self._persist_many(
            request=request,
            spines=(spine,),
            primary_record_ref=spine.record_id,
            identity_class="ST10-OP::15::DIVERGENCE",
        )
        value = persisted.typed_payload.reconstruct(DivergenceAssessmentV1)
        self._divergence[value.assessment_id] = value
        self._last_committed_receipt_refs = (persisted.record_id,)
        return value

    def build_bundle(
        self,
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1 | None = None,
        *,
        control_contracts: tuple[object, ...] | None = None,
    ) -> ComputationEvidenceBundleV1:
        self._last_committed_receipt_refs = ()
        initialize_st12f_parameter_registry_v1()
        if candidate is None and self._bundle_candidate_resolver is not None:
            candidate = self._bundle_candidate_resolver.resolve_bundle_candidate(request)
        if control_contracts is None and callable(
            getattr(self._bundle_candidate_resolver, "resolve_control_contracts", None)
        ):
            control_contracts = tuple(
                self._bundle_candidate_resolver.resolve_control_contracts(request)
            )
        controls = () if control_contracts is None else control_contracts
        if type(request) is not BuildEvidenceBundleRequestV1 or type(candidate) is not ComputationEvidenceBundleV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP15 requires exact request and canonical candidate")
        if not isinstance(controls, tuple):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "OP15 control contracts must be an immutable tuple",
            )
        lock = self._cohort_resolver.resolve_input_lock(request.input_lock_id)
        if candidate.input_lock_id != lock.input_lock_id or candidate.component_or_template_ref != request.component_id or request.required_lanes != ("REPLAY", "PAPER"):
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "OP15 scope differs from canonical lock/component/dual lane")
        if candidate.source_and_provenance_refs != request.evidence_record_refs:
            raise ContractValidationError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "bundle provenance must equal the exact OP15 evidence roster",
            )
        bundle_record_ref = f"ST12F-RECEIPT::{candidate.evidence_bundle_version}::EVIDENCE_BUNDLE_VERSION"
        existing_bundle_spine = self._persistence.get_record(bundle_record_ref)
        if existing_bundle_spine is not None:
            if type(existing_bundle_spine) is not EconomicReceiptEventSpineV1:
                raise PersistenceContractError(
                    ReasonCode.PERSISTENCE_CONFLICT,
                    "bundle version identity is owned by a non-receipt record",
                )
            existing_bundle = existing_bundle_spine.typed_payload.reconstruct(
                ComputationEvidenceBundleV1
            )
            if deterministic_json(existing_bundle) != deterministic_json(candidate):
                raise PersistenceContractError(
                    ReasonCode.PERSISTENCE_CONFLICT,
                    "immutable bundle version already binds different evidence",
                )
            existing_refs = [bundle_record_ref]
            if candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
                assert type(candidate.d_evidence_reference_projection) is ST12FEvidenceReferenceV1
                assert type(candidate.g_handoff_projection) is FToGHandoffReferencesV1
                existing_refs.extend(
                    (
                        f"ST12F-RECEIPT::{candidate.d_evidence_reference_projection.reference_id}::D_EVIDENCE_REFERENCE",
                        f"ST12F-RECEIPT::{candidate.g_handoff_projection.handoff_id}::G_HANDOFF_REFERENCE",
                    )
                )
            self._last_committed_receipt_refs = tuple(existing_refs)
            return existing_bundle
        previous_ref = self._durable_current_bundle_ref(
            candidate.evidence_id,
            candidate.input_lock_id,
            candidate.component_or_template_ref,
        )
        expected_parent = previous_ref or "EXPLICIT_ABSENCE"
        previous = None if previous_ref is None else self.resolve_bundle(previous_ref)
        self._validate_bundle_transition(previous, candidate)

        replay = None if candidate.replay_result_ref == "EXPLICIT_ABSENCE" else self.resolve_lane_result(candidate.replay_result_ref, "REPLAY")
        paper = None if candidate.paper_result_ref == "EXPLICIT_ABSENCE" else self.resolve_lane_result(candidate.paper_result_ref, "PAPER")
        self._validate_bundle_lanes(candidate, lock, replay, paper)

        control_by_type: dict[type[object], object] = {}
        allowed_control_types = {
            DivergenceAssessmentV1,
            ModelRiskEvidenceAssessmentV1,
            QuantumTraceValidationReceiptV1,
            DeterministicEvidenceAnnotationContractV1,
            IndependentReviewRecordV1,
        }
        for control in controls:
            if type(control) not in allowed_control_types:
                raise ContractValidationError(
                    ReasonCode.SCHEMA_MISMATCH,
                    "OP15 control tuple contains a non-control contract",
                )
            self._contract_receipt_parts(control)
            if type(control) in control_by_type:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "OP15 carries duplicate control contract types",
                )
            if getattr(control, "input_lock_id", lock.input_lock_id) != lock.input_lock_id:
                raise ContractValidationError(
                    ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                    "OP15 control contract differs from the canonical input lock",
                )
            control_by_type[type(control)] = control

        divergence = control_by_type.get(DivergenceAssessmentV1)
        if divergence is None and candidate.divergence_assessment_ref != "EXPLICIT_ABSENCE":
            receipt_ref = f"ST12F-RECEIPT::{candidate.divergence_assessment_ref}::DIVERGENCE_ASSESSMENT"
            if self._persistence.get_record(receipt_ref) is not None:
                divergence = self._load_contract(receipt_ref, DivergenceAssessmentV1)
        if divergence is not None:
            assert type(divergence) is DivergenceAssessmentV1
            if divergence.assessment_id != candidate.divergence_assessment_ref:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle divergence reference differs from its contract",
                )
            self._validate_divergence(divergence)
        self._validate_bundle_divergence(candidate, divergence)

        model_risk = control_by_type.get(ModelRiskEvidenceAssessmentV1)
        if model_risk is None:
            model_risk = self._find_control_in_request(
                request,
                ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT,
                ModelRiskEvidenceAssessmentV1,
            )
        self._validate_bundle_model_risk(candidate, model_risk)

        review = control_by_type.get(IndependentReviewRecordV1)
        if review is None:
            review = self._find_review_for_request(request)
        self._validate_bundle_review(
            request=request,
            lock=lock,
            previous_ref=previous_ref,
            previous=previous,
            candidate=candidate,
            review=review,
        )
        self._validate_bundle_transition_guard(
            request=request,
            previous_ref=previous_ref,
            previous=previous,
            candidate=candidate,
        )

        self._validate_closed_projections(
            candidate,
            bundle_record_ref=bundle_record_ref,
            lock=lock,
        )
        spines: list[EconomicReceiptEventSpineV1] = []
        effective_controls = list(controls)
        if (
            type(review) is IndependentReviewRecordV1
            and IndependentReviewRecordV1 not in control_by_type
        ):
            effective_controls.append(review)
        for control in effective_controls:
            receipt_class, contract_id, *_ = self._contract_receipt_parts(control)
            receipt_ref = f"ST12F-RECEIPT::{contract_id}::{receipt_class.value}"
            existing = self._persistence.get_record(receipt_ref)
            if existing is None:
                spines.append(self._receipt(request=request, contract=control, input_lock=lock))
            elif type(existing) is not EconomicReceiptEventSpineV1 or deterministic_json(existing.typed_payload.reconstruct(type(control))) != deterministic_json(control):
                raise PersistenceContractError(
                    ReasonCode.PERSISTENCE_CONFLICT,
                    "OP15 control receipt identity already binds different evidence",
                )
        bundle_spine = self._receipt(
            request=request,
            contract=candidate,
            input_lock=lock,
            bundle_parent_ref=expected_parent,
        )
        spines.append(bundle_spine)
        if candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
            assert type(candidate.d_evidence_reference_projection) is ST12FEvidenceReferenceV1
            assert type(candidate.g_handoff_projection) is FToGHandoffReferencesV1
            spines.extend(
                (
                    self._receipt(request=request, contract=candidate.d_evidence_reference_projection, input_lock=lock),
                    self._receipt(request=request, contract=candidate.g_handoff_projection, input_lock=lock),
                )
            )
        persisted = self._persist_many(
            request=request,
            spines=tuple(spines),
            primary_record_ref=bundle_spine.record_id,
            identity_class="ST10-OP::15",
        )
        value = persisted.typed_payload.reconstruct(ComputationEvidenceBundleV1)
        self._rebuild_caches_from_durable_receipts()
        self._last_committed_receipt_refs = tuple(row.record_id for row in spines)
        return value

    def _durable_current_bundle_ref(
        self,
        evidence_id: str,
        input_lock_id: str,
        component_or_template_ref: str,
    ) -> str | None:
        matches: list[
            tuple[str, ComputationEvidenceBundleV1, str]
        ] = []
        for spine in self._durable_receipt_spines():
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
                continue
            value = payload.reconstruct(ComputationEvidenceBundleV1)
            self._validate_receipt_lock_metadata(spine)
            if (
                value.evidence_id == evidence_id
                and value.input_lock_id == input_lock_id
                and value.component_or_template_ref == component_or_template_ref
            ):
                matches.append(
                    (
                        spine.record_id,
                        value,
                        payload.parent_version_ref_or_explicit_absence,
                    )
                )
        return None if not matches else self._bundle_leaf_ref(tuple(matches))

    @staticmethod
    def _bundle_leaf_ref(
        rows: tuple[tuple[str, ComputationEvidenceBundleV1, str], ...],
    ) -> str:
        by_ref = {record_ref: value for record_ref, value, _ in rows}
        parent_by_ref = {record_ref: parent for record_ref, _, parent in rows}
        if len(by_ref) != len(rows) or len(parent_by_ref) != len(rows):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage repeats an immutable receipt identity",
            )
        missing_parents = {
            parent
            for parent in parent_by_ref.values()
            if parent != "EXPLICIT_ABSENCE" and parent not in by_ref
        }
        if missing_parents:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage has a missing parent receipt",
            )

        children_by_ref: dict[str, list[str]] = {ref: [] for ref in by_ref}
        for child_ref, parent_ref in parent_by_ref.items():
            if parent_ref != "EXPLICIT_ABSENCE":
                children_by_ref[parent_ref].append(child_ref)
        if any(len(children) > 1 for children in children_by_ref.values()):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage is branched",
            )

        for start_ref in by_ref:
            visited: set[str] = set()
            current_ref = start_ref
            while current_ref != "EXPLICIT_ABSENCE":
                if current_ref in visited:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "durable bundle lineage is cyclic",
                    )
                visited.add(current_ref)
                current_ref = parent_by_ref[current_ref]

        roots = tuple(
            ref
            for ref, parent_ref in parent_by_ref.items()
            if parent_ref == "EXPLICIT_ABSENCE"
        )
        leaves = tuple(
            ref for ref, children in children_by_ref.items() if not children
        )
        if len(roots) != 1 or len(leaves) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage is disconnected",
            )

        traversed: set[str] = set()
        current_ref = roots[0]
        previous: ComputationEvidenceBundleV1 | None = None
        while True:
            traversed.add(current_ref)
            current = by_ref[current_ref]
            ComputationEvidenceServiceV1._validate_bundle_transition(
                previous,
                current,
            )
            children = children_by_ref[current_ref]
            if not children:
                break
            previous = current
            current_ref = children[0]
        if traversed != set(by_ref):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage is disconnected",
            )
        return leaves[0]

    def _find_control_in_request(
        self,
        request: BuildEvidenceBundleRequestV1,
        receipt_class: ST12FReceiptClassV1,
        expected_type: type[object],
    ) -> object | None:
        matches: list[object] = []
        for ref in request.evidence_record_refs:
            spine = self._persistence.get_record(ref)
            if (
                type(spine) is EconomicReceiptEventSpineV1
                and type(spine.typed_payload) is ST12FEvidenceControlReceiptRecordV1
                and spine.typed_payload.receipt_class is receipt_class
            ):
                matches.append(spine.typed_payload.reconstruct(expected_type))
        if len(matches) > 1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "OP15 evidence roster contains duplicate control classes",
            )
        return None if not matches else matches[0]

    def _find_review_for_request(
        self,
        request: BuildEvidenceBundleRequestV1,
    ) -> IndependentReviewRecordV1 | None:
        durable = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
            IndependentReviewRecordV1,
        )
        if durable is not None:
            assert type(durable) is IndependentReviewRecordV1
            return durable
        if self._review_resolver is None:
            return None
        candidates: list[IndependentReviewRecordV1] = []
        for ref in request.evidence_record_refs:
            try:
                candidate = self._review_resolver.resolve_review(ref)
            except (ContractValidationError, PersistenceContractError, KeyError):
                continue
            if type(candidate) is IndependentReviewRecordV1:
                candidates.append(candidate)
        if len(candidates) > 1:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "OP15 resolves more than one independent review",
            )
        return None if not candidates else candidates[0]

    @staticmethod
    def _validate_bundle_transition(
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
    ) -> None:
        state = candidate.terminal_state
        if candidate.independent_review_state != state.value:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "bundle review state differs from its immutable terminal state",
            )
        if previous is None:
            if state not in _EVIDENCE_BUNDLE_INITIAL_STATES_V1:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle lifecycle root is not owner-certified",
                )
            return
        if (
            candidate.evidence_id != previous.evidence_id
            or candidate.input_lock_id != previous.input_lock_id
            or candidate.component_or_template_ref
            != previous.component_or_template_ref
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "bundle lifecycle transition changes its exact three-part identity",
            )
        if (
            candidate.evidence_bundle_version == previous.evidence_bundle_version
            or (previous.terminal_state, state)
            not in _EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "bundle lifecycle transition or immutable version identity is invalid",
            )

    @staticmethod
    def _validate_bundle_lanes(
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
        replay: ReplayResultContractV1 | None,
        paper: PaperResultContractV1 | None,
    ) -> None:
        state = candidate.terminal_state
        if (replay is None) != (state is EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "missing REPLAY evidence requires its exact immutable incomplete state",
            )
        if (paper is None) != (state is EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "missing PAPER evidence requires its exact immutable incomplete state",
            )
        present = tuple(row for row in (replay, paper) if row is not None)
        if any(
            row.fixture_only_not_evidence
            or row.input_lock_id != lock.input_lock_id
            or row.cohort_template_id != candidate.component_or_template_ref
            for row in present
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
                "bundle lanes must be real evidence under one exact lock and template",
            )
        expected_receipts = tuple(
            f"ST12F-RECEIPT::{row.result_id}::{('REPLAY' if type(row) is ReplayResultContractV1 else 'PAPER')}_REGISTRATION"
            for row in present
        )
        if candidate.lane_execution_receipt_refs != expected_receipts:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "bundle lane receipt references are not the exact committed spine IDs",
            )
        if state in {
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
            EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.STALE,
        } and not candidate.blocker_codes:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "incomplete, rejected, or stale bundle requires typed blockers",
            )

    @staticmethod
    def _validate_bundle_divergence(
        candidate: ComputationEvidenceBundleV1,
        divergence: object | None,
    ) -> None:
        state = candidate.terminal_state
        missing_lane = state in {
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        }
        if missing_lane:
            valid = (
                candidate.divergence_assessment_ref == "EXPLICIT_ABSENCE"
                and divergence is None
            )
        else:
            expected_terminal = (
                DivergenceTerminalStateV1.INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE
                if state is EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT
                else DivergenceTerminalStateV1.CONSISTENT_WITHIN_LOCKED_THRESHOLDS
            )
            valid = (
                type(divergence) is DivergenceAssessmentV1
                and candidate.divergence_assessment_ref
                == divergence.assessment_id
                and candidate.replay_result_ref == divergence.replay_result_ref
                and candidate.paper_result_ref == divergence.paper_result_ref
                and divergence.terminal_state is expected_terminal
            )
        if not valid:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "bundle lifecycle state lacks its exact dual-lane divergence proof",
            )

    @staticmethod
    def _validate_bundle_model_risk(
        candidate: ComputationEvidenceBundleV1,
        model_risk: object | None,
    ) -> None:
        if candidate.terminal_state not in {
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        }:
            return
        if type(model_risk) is not ModelRiskEvidenceAssessmentV1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "READY/CLOSED bundle requires a typed model-risk assessment",
            )
        comparison = model_risk.permanent_no_trade_comparison
        non_review_veto = any(
            row.active and row.condition_id != "INDEPENDENT_REVIEW_NOT_CLOSED"
            for row in model_risk.no_trade_condition_outcomes
        )
        controls_pass = all(
            row.state is not ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON
            and row.current
            for row in model_risk.control_evidence
        )
        if (
            non_review_veto
            or not controls_pass
            or comparison.execution_adjusted_lcb <= 0
            or comparison.candidate_utility <= comparison.strongest_classical_utility
            or comparison.candidate_utility <= comparison.no_trade_utility
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "READY/CLOSED bundle has an unresolved deterministic hard veto",
            )

    def _validate_bundle_review(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        lock: ImmutableReplayPaperInputLockV1,
        previous_ref: str | None,
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
        review: object | None,
    ) -> None:
        state = candidate.terminal_state
        if state not in {
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        }:
            if review is not None:
                raise ContractValidationError(
                    ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                    "non-review lifecycle state cannot consume a review decision",
                )
            return
        expected_decision = (
            IndependentReviewDecisionV1.REJECTED
            if state is EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED
            else IndependentReviewDecisionV1.VALIDATED
        )
        if (
            type(review) is not IndependentReviewRecordV1
            or previous_ref is None
            or previous is None
            or previous.terminal_state is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            or review.prior_bundle_ref != previous_ref
            or review.evidence_id != candidate.evidence_id
            or review.evidence_bundle_version != candidate.evidence_bundle_version
            or review.input_lock_id != lock.input_lock_id
            or review.bundle_producer_identity != self._producer_identity
            or review.reviewer_identity == self._producer_identity
            or review.decision is not expected_decision
            or review.reviewed_source_epoch_refs != _source_epoch_refs(lock)
            or not review.reviewed_at <= request.requested_at <= review.valid_until
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review does not bind the exact prior/candidate/version/lock/epoch custody",
            )

    def _validate_bundle_transition_guard(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        previous_ref: str | None,
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
    ) -> None:
        state = candidate.terminal_state
        if state is EvidenceBundleTerminalStateV1.STALE:
            prior_reference = (
                None
                if previous is None
                else previous.d_evidence_reference_projection
            )
            if (
                previous_ref is None
                or type(prior_reference) is not ST12FEvidenceReferenceV1
                or prior_reference.evidence_ref != previous_ref
                or prior_reference.evidence_state
                is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
                or request.requested_at <= prior_reference.valid_until
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_BUNDLE_STALE,
                    "CLOSED to STALE requires exact expiry of the prior closed D reference",
                )
            return
        if state is not EvidenceBundleTerminalStateV1.SUPERSEDED:
            return
        if previous_ref is None or previous is None:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "CLOSED to SUPERSEDED requires a durable closed predecessor",
            )

        durable_spines = self._durable_receipt_spines()
        spines_by_ref = {spine.record_id: spine for spine in durable_spines}
        prior_spine = spines_by_ref.get(previous_ref)
        if prior_spine is None:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "CLOSED to SUPERSEDED predecessor receipt is not durable",
            )

        for spine in durable_spines:
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if (
                payload.receipt_class
                is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
                or spine.record_id == previous_ref
                or spine.record_id not in request.evidence_record_refs
                or not prior_spine.recorded_at
                < spine.recorded_at
                <= request.requested_at
            ):
                continue
            newer = payload.reconstruct(ComputationEvidenceBundleV1)
            self._validate_receipt_lock_metadata(spine)
            if (
                newer.terminal_state
                is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
                or newer.evidence_id != previous.evidence_id
                or newer.component_or_template_ref
                != previous.component_or_template_ref
                or newer.evidence_bundle_version
                == previous.evidence_bundle_version
            ):
                continue
            reference = newer.d_evidence_reference_projection
            if (
                type(reference) is not ST12FEvidenceReferenceV1
                or reference.evidence_state
                is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
                or reference.evidence_ref != spine.record_id
                or reference.evidence_id != newer.evidence_id
                or reference.component_or_template_ref
                != newer.component_or_template_ref
                or reference.input_lock_id != newer.input_lock_id
                or reference.evidence_bundle_version
                != newer.evidence_bundle_version
                or not reference.observed_at
                <= request.requested_at
                <= reference.valid_until
                or self._durable_current_bundle_ref(
                    newer.evidence_id,
                    newer.input_lock_id,
                    newer.component_or_template_ref,
                )
                != spine.record_id
            ):
                continue
            reference_receipt_ref = (
                f"ST12F-RECEIPT::{reference.reference_id}::D_EVIDENCE_REFERENCE"
            )
            reference_spine = spines_by_ref.get(reference_receipt_ref)
            if (
                reference_spine is None
                or type(reference_spine.typed_payload)
                is not ST12FEvidenceControlReceiptRecordV1
                or reference_spine.typed_payload.receipt_class
                is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE
                or reference_spine.typed_payload.reconstruct(
                    ST12FEvidenceReferenceV1
                )
                != reference
            ):
                continue
            independently_reviewed = False
            for review_spine in durable_spines:
                review_payload = review_spine.typed_payload
                assert type(review_payload) is ST12FEvidenceControlReceiptRecordV1
                if (
                    review_payload.receipt_class
                    is not ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION
                ):
                    continue
                review = review_payload.reconstruct(IndependentReviewRecordV1)
                if (
                    review.prior_bundle_ref
                    == payload.parent_version_ref_or_explicit_absence
                    and review.evidence_id == newer.evidence_id
                    and review.evidence_bundle_version
                    == newer.evidence_bundle_version
                    and review.input_lock_id == newer.input_lock_id
                    and review.decision is IndependentReviewDecisionV1.VALIDATED
                    and review.bundle_producer_identity == self._producer_identity
                    and review.reviewer_identity != self._producer_identity
                    and review.reviewed_source_epoch_refs
                    == reference.source_epoch_refs
                    and review.reviewed_at
                    <= request.requested_at
                    <= review.valid_until
                ):
                    independently_reviewed = True
                    break
            if independently_reviewed:
                return
        raise ContractValidationError(
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
            "CLOSED to SUPERSEDED requires a referenced, newer, current, valid, independently reviewed closed bundle",
        )

    @staticmethod
    def _validate_closed_projections(
        candidate: ComputationEvidenceBundleV1,
        *,
        bundle_record_ref: str,
        lock: ImmutableReplayPaperInputLockV1,
    ) -> None:
        if candidate.terminal_state is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
            return
        reference = candidate.d_evidence_reference_projection
        handoff = candidate.g_handoff_projection
        if (
            type(reference) is not ST12FEvidenceReferenceV1
            or type(handoff) is not FToGHandoffReferencesV1
            or reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or reference.evidence_id != candidate.evidence_id
            or reference.evidence_ref != bundle_record_ref
            or reference.evidence_bundle_version != candidate.evidence_bundle_version
            or reference.component_or_template_ref != candidate.component_or_template_ref
            or reference.input_lock_id != lock.input_lock_id
            or reference.source_epoch_refs != _source_epoch_refs(lock)
            or reference.lane != "REPLAY_PAPER"
            or reference.terminal_state != candidate.terminal_state.value
            or reference.no_effect_flags != NO_EFFECTS_V1
            or handoff.evidence_bundle_ref != bundle_record_ref
            or handoff.input_lock_id != lock.input_lock_id
            or handoff.source_epoch_refs != _source_epoch_refs(lock)
            or handoff.terminal_state != candidate.terminal_state.value
            or not handoff.read_only
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "closed bundle D/G projections differ from canonical custody",
            )

    def read_evidence_reference(
        self,
        context: object,
        *,
        causation_id: str,
        correlation_id: str,
        query: FToDEvidenceReferenceQueryV1 | None = None,
    ) -> ST12FEvidenceReferenceV1:
        observed = parse_utc(getattr(context, "as_of"), field_name="as_of")

        def unavailable() -> ST12FEvidenceReferenceV1:
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

        if (
            type(query) is not FToDEvidenceReferenceQueryV1
            or query.evaluated_at != observed
        ):
            return unavailable()
        candidates: list[tuple[EconomicReceiptEventSpineV1, ST12FEvidenceReferenceV1]] = []
        try:
            for spine in self._durable_receipt_spines():
                payload = spine.typed_payload
                assert type(payload) is ST12FEvidenceControlReceiptRecordV1
                if payload.receipt_class is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
                    continue
                reference = payload.reconstruct(ST12FEvidenceReferenceV1)
                self._validate_receipt_lock_metadata(spine)
                if (
                    reference.evidence_id == query.requested_evidence_id
                    and reference.component_or_template_ref
                    == query.requested_component_or_template_ref
                    and reference.input_lock_id == query.expected_input_lock_id
                ):
                    candidates.append((spine, reference))
        except (ContractValidationError, PersistenceContractError):
            return unavailable()
        if not candidates:
            return unavailable()
        _, reference = candidates[-1]
        current_bundle_ref = self._durable_current_bundle_ref(
            reference.evidence_id,
            reference.input_lock_id,
            reference.component_or_template_ref,
        )
        try:
            bundle = self.resolve_bundle(reference.evidence_ref)
        except (ContractValidationError, PersistenceContractError):
            return unavailable()
        if (
            reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or reference.evidence_ref != current_bundle_ref
            or reference.evidence_ref not in {row.record_id for row in self._durable_receipt_spines()}
            or reference.component_or_template_ref != query.requested_component_or_template_ref
            or reference.input_lock_id != query.expected_input_lock_id
            or reference.source_epoch_refs != query.expected_source_epoch_refs
            or reference.terminal_state != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value
            or reference.lane != "REPLAY_PAPER"
            or reference.no_effect_flags != NO_EFFECTS_V1
            or not reference.observed_at <= query.evaluated_at <= reference.valid_until
            or bundle.evidence_id != query.requested_evidence_id
            or bundle.component_or_template_ref != query.requested_component_or_template_ref
            or bundle.input_lock_id != query.expected_input_lock_id
            or bundle.evidence_bundle_version != reference.evidence_bundle_version
            or bundle.terminal_state is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
            or bundle.d_evidence_reference_projection != reference
        ):
            return unavailable()
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
                "reviews": MappingProxyType(self._reviews),
                "d_references": MappingProxyType(self._d_references),
                "g_handoffs": MappingProxyType(self._g_handoffs),
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
