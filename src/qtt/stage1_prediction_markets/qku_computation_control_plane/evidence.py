"""Canonical ST12-F lane, divergence, review, and evidence-bundle owner."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
import math
from threading import Lock
from types import MappingProxyType
from typing import Mapping, Protocol

from .agent_policy import (
    AgentCapabilityDecisionV1,
)
from .context import ComputationContextKeyV1, exact_decimal, parse_utc
from .errors import (
    AuthorityDeniedError,
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
from .llm_gateway import (
    CanonicalNumericEvidenceValueV1,
    DeterministicEvidenceAnnotationContractV1,
)
from .model_risk import ModelRiskControlStateV1, ModelRiskEvidenceAssessmentV1
from .models import (
    BuildEvidenceBundleRequestV1,
    ComputationExecutionReceiptV1,
    FrozenFormulaOutputV1,
    NO_EFFECTS_V1,
    RegisterReplayPaperResultRequestV1,
    StackResultV1,
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
    DurableComputationExecutionReceiptRecordV1,
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    ST12FEvidenceControlReceiptRecordV1,
    ST12FReceiptClassV1,
)
from .serialization import deterministic_json, safe_json_loads
from .economic_math import TRANCHE_C_MATH_SPECIFICATIONS
from .implementation_registry import (
    CURRENT_IMPLEMENTATION_REGISTRY,
    TRANCHE_C_IMPLEMENTATION_REGISTRY,
)
from .specification import CURRENT_FORMULA_REQUIREMENTS
from .stack_resolver import REGISTERED_FORMULA_STACKS


LANE_RESULT_SCHEMA_VERSION_V1 = "QTT_ST12F_LANE_RESULT_CONTRACTS_V1_4"
LANE_RESULT_CONTRACT_VERSION_V1 = "1.4"
DIVERGENCE_SCHEMA_VERSION_V1 = "QTT_ST12F_DIVERGENCE_ASSESSMENT_V1_4"
EVIDENCE_BUNDLE_SCHEMA_VERSION_V1 = "QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4"
EVIDENCE_BUNDLE_CONTRACT_VERSION_V1 = "1.4"
ST12F_EVIDENCE_IDENTITIES_V1 = tuple(
    f"MATH-{number:02d}" for number in (*range(1, 46), 50, 51, 52)
)
ST12F_STATIC_NOT_APPLICABLE_MATH_IDS_V1 = (
    "MATH-01",
    "MATH-02",
    "MATH-03",
    "MATH-04",
    "MATH-05",
    "MATH-06",
    "MATH-07",
    "MATH-34",
    "MATH-35",
    "MATH-36",
)


@dataclass(frozen=True, slots=True)
class StaticEvidenceApplicabilityProofV1:
    """Deterministic proof that one non-metric math identity is out of scope."""

    proof_id: str
    math_spec_id: str
    component_or_template_ref: str
    input_lock_id: str
    formula_requirement_ref: str
    implementation_registry_ref: str
    dependency_graph_ref: str
    reason: str

    def __post_init__(self) -> None:
        for name in (
            "proof_id",
            "math_spec_id",
            "component_or_template_ref",
            "input_lock_id",
            "formula_requirement_ref",
            "implementation_registry_ref",
            "dependency_graph_ref",
            "reason",
        ):
            _text(getattr(self, name), name)
        expected_id = (
            "ST12F-STATIC-NOT-APPLICABLE::"
            f"{self.math_spec_id}::{self.component_or_template_ref}::"
            f"{self.input_lock_id}"
        )
        if (
            self.math_spec_id not in ST12F_STATIC_NOT_APPLICABLE_MATH_IDS_V1
            or self.proof_id != expected_id
            or not (
                self.math_spec_id in CURRENT_FORMULA_REQUIREMENTS
                or self.math_spec_id in TRANCHE_C_MATH_SPECIFICATIONS
            )
            or not (
                self.math_spec_id in CURRENT_IMPLEMENTATION_REGISTRY
                or self.math_spec_id in TRANCHE_C_IMPLEMENTATION_REGISTRY
            )
            or self.formula_requirement_ref
            != f"CURRENT_FORMULA_REQUIREMENTS::{self.math_spec_id}"
            or self.implementation_registry_ref
            != f"CURRENT_IMPLEMENTATION_REGISTRY::{self.math_spec_id}"
            or self.dependency_graph_ref
            != f"CompiledDependencyGraphV1::{self.component_or_template_ref}"
            or self.reason != "NOT_REQUIRED_BY_COMPONENT_DEPENDENCY_GRAPH"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "static applicability proof differs from the exact allowlist",
            )

    @classmethod
    def for_scope(
        cls,
        *,
        math_spec_id: str,
        component_or_template_ref: str,
        input_lock_id: str,
    ) -> "StaticEvidenceApplicabilityProofV1":
        return cls(
            proof_id=(
                "ST12F-STATIC-NOT-APPLICABLE::"
                f"{math_spec_id}::{component_or_template_ref}::{input_lock_id}"
            ),
            math_spec_id=math_spec_id,
            component_or_template_ref=component_or_template_ref,
            input_lock_id=input_lock_id,
            formula_requirement_ref=(
                f"CURRENT_FORMULA_REQUIREMENTS::{math_spec_id}"
            ),
            implementation_registry_ref=(
                f"CURRENT_IMPLEMENTATION_REGISTRY::{math_spec_id}"
            ),
            dependency_graph_ref=(
                f"CompiledDependencyGraphV1::{component_or_template_ref}"
            ),
            reason="NOT_REQUIRED_BY_COMPONENT_DEPENDENCY_GRAPH",
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


@dataclass(frozen=True, slots=True)
class EvidenceOutputBindingV1:
    math_spec_id: str
    output_name: str
    output_type: str
    output_unit: str
    metric_id: str
    static_not_applicable_allowed: bool


ST12F_EVIDENCE_OUTPUT_BINDINGS_V1 = (
    EvidenceOutputBindingV1("MATH-01", "p_market", "Decimal", "probability", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-02", "edge_probability", "float64", "probability points", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-03", "mid", "Decimal", "currency/contract", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-04", "spread", "Decimal", "currency/contract", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-05", "relative_spread", "Decimal", "fraction", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-06", "expected_net_cash", "Decimal", "currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-07", "expected_net_cash", "Decimal", "currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-08", "brier_score", "float64", "squared probability", "ST12F-METRIC::001", False),
    EvidenceOutputBindingV1("MATH-09", "log_loss", "float64", "nats/sample", "ST12F-METRIC::002", False),
    EvidenceOutputBindingV1("MATH-10", "ece", "float64", "probability", "ST12F-METRIC::003", False),
    EvidenceOutputBindingV1("MATH-11", "interval", "[float64,float64]", "probability", "ST12F-METRIC::004", False),
    EvidenceOutputBindingV1("MATH-12", "rejections_and_adjusted_p", "typed vector", "probability", "ST12F-METRIC::005", False),
    EvidenceOutputBindingV1("MATH-13", "rejections_and_adjusted_p", "typed vector", "probability", "ST12F-METRIC::006", False),
    EvidenceOutputBindingV1("MATH-14", "bootstrap_distribution_and_interval", "typed record", "statistic unit", "ST12F-METRIC::007", False),
    EvidenceOutputBindingV1("MATH-15", "reality_check_receipt", "typed statistical result", "p-value", "ST12F-METRIC::008", False),
    EvidenceOutputBindingV1("MATH-16", "spa_receipt", "typed statistical result", "p-value", "ST12F-METRIC::009", False),
    EvidenceOutputBindingV1("MATH-17", "psr", "float64", "probability", "ST12F-METRIC::010", False),
    EvidenceOutputBindingV1("MATH-18", "dsr", "float64", "probability", "ST12F-METRIC::011", False),
    EvidenceOutputBindingV1("MATH-19", "pbo_receipt", "typed result", "probability", "ST12F-METRIC::012", False),
    EvidenceOutputBindingV1("MATH-20", "split_indices", "typed fold registry", "indices", "ST12F-METRIC::013", False),
    EvidenceOutputBindingV1("MATH-21", "cpcv_paths", "typed path registry", "indices", "ST12F-METRIC::014", False),
    EvidenceOutputBindingV1("MATH-22", "dr_value_and_uncertainty", "typed result", "reward", "ST12F-METRIC::015", False),
    EvidenceOutputBindingV1("MATH-23", "ips_value", "float64", "reward", "ST12F-METRIC::016", False),
    EvidenceOutputBindingV1("MATH-24", "snips_value", "float64", "reward", "ST12F-METRIC::017", False),
    EvidenceOutputBindingV1("MATH-25", "switch_value_and_selected_tau", "typed result", "reward", "ST12F-METRIC::018", False),
    EvidenceOutputBindingV1("MATH-26", "evi", "Decimal", "same utility basis", "ST12F-METRIC::019", False),
    EvidenceOutputBindingV1("MATH-27", "full_kelly_fraction", "Decimal", "fraction of approved risk capital", "ST12F-METRIC::020", False),
    EvidenceOutputBindingV1("MATH-28", "bounded_fraction", "Decimal", "fraction of approved risk capital", "ST12F-METRIC::021", False),
    EvidenceOutputBindingV1("MATH-29", "utility", "float64", "return-equivalent utility", "ST12F-METRIC::022", False),
    EvidenceOutputBindingV1("MATH-30", "cvar", "float64", "loss", "ST12F-METRIC::023", False),
    EvidenceOutputBindingV1("MATH-31", "expected_shortfall", "float64", "loss", "ST12F-METRIC::024", False),
    EvidenceOutputBindingV1("MATH-32", "implementation_shortfall", "Decimal", "currency", "ST12F-METRIC::025", False),
    EvidenceOutputBindingV1("MATH-33", "spread_cost", "Decimal", "currency", "ST12F-METRIC::026", False),
    EvidenceOutputBindingV1("MATH-34", "fee", "Decimal", "settlement currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-35", "signed_fee_or_rebate", "Decimal", "USD", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-36", "derived_yes_and_no_touches", "typed Decimal record", "currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-37", "fill_probability", "float64", "probability", "ST12F-METRIC::027", False),
    EvidenceOutputBindingV1("MATH-38", "expected_fill_quantity", "Decimal", "units", "ST12F-METRIC::028", False),
    EvidenceOutputBindingV1("MATH-39", "queue_ahead_estimate", "Decimal", "units", "ST12F-METRIC::029", False),
    EvidenceOutputBindingV1("MATH-40", "adverse_selection_cost", "Decimal", "currency", "ST12F-METRIC::030", False),
    EvidenceOutputBindingV1("MATH-41", "decayed_edge", "float64", "same edge", "ST12F-METRIC::031", False),
    EvidenceOutputBindingV1("MATH-42", "impact_fraction", "float64", "fraction of price", "ST12F-METRIC::032", False),
    EvidenceOutputBindingV1("MATH-43", "capacity_penalty", "float64", "utility", "ST12F-METRIC::033", False),
    EvidenceOutputBindingV1("MATH-44", "shrunk_covariance", "float64 matrix", "return covariance", "ST12F-METRIC::034", False),
    EvidenceOutputBindingV1("MATH-45", "gate_decision", "enum and LCB value", "declared", "ST12F-METRIC::035", False),
    EvidenceOutputBindingV1("MATH-50", "recomputed_objective", "typed quantum validation", "declared trace and economic bases", "ST12F-METRIC::036", False),
    EvidenceOutputBindingV1("MATH-51", "recomputed_objective", "typed quantum validation", "declared trace and economic bases", "ST12F-METRIC::037", False),
    EvidenceOutputBindingV1("MATH-52", "benchmark_delta_packet", "typed multi-metric record", "declared metrics", "ST12F-METRIC::038", False),
)

_EVIDENCE_OUTPUT_BINDING_BY_MATH_ID_V1 = MappingProxyType(
    {row.math_spec_id: row for row in ST12F_EVIDENCE_OUTPUT_BINDINGS_V1}
)

ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1: Mapping[str, str] = MappingProxyType(
    {
        "MATH-08": "per_sample_squared_probability",
        "MATH-09": "per_sample_natural_log_loss",
        "MATH-10": "absolute_calibration_gap",
        "MATH-11": "lower_upper_probability_interval",
        "MATH-12": "adjusted_p_and_rejection_mask",
        "MATH-13": "adjusted_p_and_rejection_mask",
        "MATH-14": "bootstrap_statistic_distribution_and_interval",
        "MATH-15": "benchmark_candidate_loss_differential_p_value",
        "MATH-16": "superior_predictive_ability_p_value",
        "MATH-17": "probability_sharpe_exceeds_benchmark",
        "MATH-18": "multiple_testing_adjusted_sharpe_probability",
        "MATH-19": "probability_of_backtest_overfitting",
        "MATH-20": "purged_fold_score_distribution",
        "MATH-21": "combinatorial_purged_path_score_distribution",
        "MATH-22": "off_policy_value_same_reward_basis",
        "MATH-23": "importance_weighted_policy_value",
        "MATH-24": "self_normalized_importance_policy_value",
        "MATH-25": "switch_estimator_policy_value",
        "MATH-26": "expected_value_of_information_per_decision",
        "MATH-27": "wealth_fraction",
        "MATH-28": "bounded_fractional_wealth_fraction",
        "MATH-29": "portfolio_weight_vector_and_objective",
        "MATH-30": "tail_loss_at_declared_alpha",
        "MATH-31": "historical_expected_shortfall_at_declared_alpha",
        "MATH-32": "arrival_to_execution_total_shortfall",
        "MATH-33": "quoted_spread_cost",
        "MATH-37": "fill_probability_on_declared_horizon",
        "MATH-38": "filled_fraction_of_requested_quantity",
        "MATH-39": "queue_position_or_ahead_quantity",
        "MATH-40": "post_fill_adverse_price_move_cost",
        "MATH-41": "remaining_edge_fraction_at_latency",
        "MATH-42": "square_root_impact_cost",
        "MATH-43": "capacity_crowding_penalty_or_limit",
        "MATH-44": "shrunk_covariance_matrix",
        "MATH-45": "execution_adjusted_lower_confidence_bound",
        "MATH-50": "trace_recomputed_objective_validation",
        "MATH-51": "trace_recomputed_objective_and_variance_validation",
        "MATH-52": "same_basis_quantum_classical_no_trade_comparison",
    }
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
            valid = (
                len(self.evidence_record_refs) == 1
                and not self.blocker_codes
                and not self.proof_refs
            )
        elif self.disposition is EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON:
            valid = (
                bool(self.blocker_codes)
                and not self.evidence_record_refs
                and not self.proof_refs
            )
        else:
            valid = (
                len(self.proof_refs) == 1
                and not self.evidence_record_refs
                and not self.blocker_codes
            )
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
        if identities != ST12F_EVIDENCE_IDENTITIES_V1:
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
class RegisteredLaneResultOutcomeV1:
    registered_result: ReplayResultContractV1 | PaperResultContractV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        value = self.registered_result
        if type(value) not in {ReplayResultContractV1, PaperResultContractV1}:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "lane outcome requires one exact REPLAY or PAPER contract",
            )
        _refs(self.receipt_refs, "receipt_refs")
        if value.fixture_only_not_evidence:
            expected: tuple[str, ...] = ()
        else:
            lane = "REPLAY" if type(value) is ReplayResultContractV1 else "PAPER"
            expected = (
                f"ST12F-RECEIPT::{value.result_id}::{lane}_REGISTRATION",
            )
        if self.receipt_refs != expected:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "lane outcome receipt refs differ from the exact produced receipt",
            )


@dataclass(frozen=True, slots=True)
class BuiltEvidenceBundleOutcomeV1:
    evidence_bundle: ComputationEvidenceBundleV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        bundle = self.evidence_bundle
        if type(bundle) is not ComputationEvidenceBundleV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "bundle outcome requires one exact evidence bundle",
            )
        _refs(self.receipt_refs, "receipt_refs", required=True)
        expected = [
            f"ST12F-RECEIPT::{bundle.evidence_bundle_version}::"
            "EVIDENCE_BUNDLE_VERSION"
        ]
        if (
            bundle.terminal_state
            is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
        ):
            if (
                type(bundle.d_evidence_reference_projection)
                is not ST12FEvidenceReferenceV1
                or type(bundle.g_handoff_projection)
                is not FToGHandoffReferencesV1
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "closed outcome lacks its exact D/G projections",
                )
            expected.extend(
                (
                    "ST12F-RECEIPT::"
                    f"{bundle.d_evidence_reference_projection.reference_id}::"
                    "D_EVIDENCE_REFERENCE",
                    "ST12F-RECEIPT::"
                    f"{bundle.g_handoff_projection.handoff_id}::"
                    "G_HANDOFF_REFERENCE",
                )
            )
        if self.receipt_refs != tuple(expected):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "bundle outcome receipt refs differ from exact public production",
            )


@dataclass(frozen=True, slots=True)
class RegisterEvidenceControlRequestV1:
    """Private request for durable non-review ST12-F control custody."""

    request_id: str
    requested_at: datetime
    principal_id: str
    context: ComputationContextKeyV1
    idempotency_key: str
    traceparent: str
    tracestate: str
    input_lock_id: str

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "principal_id",
            "idempotency_key",
            "traceparent",
            "input_lock_id",
        ):
            _text(getattr(self, name), name)
        if not isinstance(self.tracestate, str):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "tracestate must be text",
            )
        if type(self.context) is not ComputationContextKeyV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private control request requires one exact context",
            )
        object.__setattr__(
            self,
            "requested_at",
            parse_utc(self.requested_at, field_name="requested_at"),
        )

    @classmethod
    def from_bundle_request(
        cls,
        request: BuildEvidenceBundleRequestV1,
        *,
        idempotency_suffix: str,
    ) -> "RegisterEvidenceControlRequestV1":
        if type(request) is not BuildEvidenceBundleRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private control request source must be exact OP15 custody",
            )
        _text(idempotency_suffix, "idempotency_suffix")
        return cls(
            request_id=f"{request.request_id}::CONTROL::{idempotency_suffix}",
            requested_at=request.requested_at,
            principal_id=request.principal_id,
            context=request.context,
            idempotency_key=(
                f"{request.idempotency_key}::CONTROL::{idempotency_suffix}"
            ),
            traceparent=request.traceparent,
            tracestate=request.tracestate,
            input_lock_id=request.input_lock_id,
        )


@dataclass(frozen=True, slots=True)
class EvidenceCacheSnapshotV1:
    generation: int
    effective_watermark: datetime
    recorded_watermark: datetime
    lane_results: Mapping[object, object]
    slot_results: Mapping[object, object]
    divergence: Mapping[object, object]
    bundles: Mapping[object, object]
    current_bundles: Mapping[object, object]
    reviews: Mapping[object, object]
    d_references: Mapping[object, object]
    g_handoffs: Mapping[object, object]

    def __post_init__(self) -> None:
        if (
            isinstance(self.generation, bool)
            or not isinstance(self.generation, int)
            or self.generation < 0
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "cache generation must be a nonnegative integer",
            )
        object.__setattr__(
            self,
            "effective_watermark",
            parse_utc(
                self.effective_watermark,
                field_name="effective_watermark",
            ),
        )
        object.__setattr__(
            self,
            "recorded_watermark",
            parse_utc(
                self.recorded_watermark,
                field_name="recorded_watermark",
            ),
        )
        for name in (
            "lane_results",
            "slot_results",
            "divergence",
            "bundles",
            "current_bundles",
            "reviews",
            "d_references",
            "g_handoffs",
        ):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    f"cache {name} must be a mapping",
                )
            object.__setattr__(self, name, MappingProxyType(dict(value)))


@dataclass(frozen=True, slots=True)
class _EvidenceAdmissionResultV1:
    component_versions: Mapping[str, object]
    stack_versions: Mapping[str, object]
    provenance_refs: tuple[str, ...]
    negative_states: tuple[str, ...]
    divergence: DivergenceAssessmentV1 | None
    model_risk: ModelRiskEvidenceAssessmentV1 | None
    review: IndependentReviewRecordV1 | None


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
    def resolve_input_lock(
        self,
        input_lock_id: str,
        *,
        decision_cutoff: datetime,
    ) -> ImmutableReplayPaperInputLockV1: ...

    def resolve_expected_slot(
        self,
        compilation_id: str,
        lane: str,
        expected_result_contract_id: str,
        *,
        decision_cutoff: datetime,
    ) -> object: ...


class IndependentReviewResolverProtocolV1(Protocol):
    def resolve_review(
        self,
        review_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> IndependentReviewRecordV1: ...


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


class AgentOrchDecisionReceiptReaderProtocolV1(Protocol):
    def list_decision_receipts(self) -> tuple[dict[str, object], ...]: ...


class IndependentEvidenceReviewV1:
    """Private segregated producer for pre-OP15 independent-review custody."""

    def __init__(
        self,
        cohort_resolver: CohortCompilationResolverProtocolV1,
        persistence_adapter: PersistenceAdapterV1,
        agent_orch_service: AgentOrchDecisionReceiptReaderProtocolV1,
    ) -> None:
        if (
            not isinstance(persistence_adapter, PersistenceAdapterV1)
            or persistence_adapter.availability
            is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE
        ):
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "independent review requires available ST12-C persistence",
            )
        if not callable(getattr(cohort_resolver, "resolve_input_lock", None)):
            raise ContractValidationError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "independent review requires the canonical input-lock resolver",
            )
        if not callable(
            getattr(agent_orch_service, "list_decision_receipts", None)
        ):
            raise AuthorityDeniedError(
                ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
                "independent review requires the Agent-Orch receipt reader",
            )
        self._cohort_resolver = cohort_resolver
        self._persistence = persistence_adapter
        self._agent_orch_service = agent_orch_service

    def review_ready_bundle(
        self,
        review: IndependentReviewRecordV1,
        authority_decision: AgentCapabilityDecisionV1,
        *,
        principal_id: str,
        context_ref: str,
        component_or_template_ref: str,
        traceparent: str,
        tracestate: str,
    ) -> EconomicReceiptEventSpineV1:
        if type(review) is not IndependentReviewRecordV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "review producer requires the exact independent-review record",
            )
        for name, value in (
            ("principal_id", principal_id),
            ("context_ref", context_ref),
            ("component_or_template_ref", component_or_template_ref),
            ("traceparent", traceparent),
        ):
            _text(value, name)
        if not isinstance(tracestate, str):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "tracestate must be text",
            )
        authority_valid = (
            type(authority_decision) is AgentCapabilityDecisionV1
            and authority_decision.authorizes_independent_review(
                principal_id=principal_id,
                reviewer_identity=review.reviewer_identity,
                authority_receipt_ref=review.authority_receipt_ref,
                context_ref=context_ref,
                input_lock_id=review.input_lock_id,
                component_or_template_ref=component_or_template_ref,
            )
        )
        rows = self._agent_orch_service.list_decision_receipts()
        matching_rows = tuple(
            row
            for row in rows
            if isinstance(row, Mapping)
            and row.get("projection_ref")
            == authority_decision.agent_orch_receipt_ref
            and row.get("task_id") == authority_decision.task_id
            and row.get("principal_id") == principal_id
            and row.get("current_agent_id") == review.reviewer_identity
            and row.get("operation_id") == "build_evidence_bundle"
            and row.get("context_ref") == context_ref
            and row.get("control_plane_only") is True
            and row.get("runtime_side_effect_allowed") is False
        ) if type(authority_decision) is AgentCapabilityDecisionV1 else ()
        if not authority_valid or len(matching_rows) != 1:
            raise AuthorityDeniedError(
                ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
                "review authority does not match one pre-existing Agent-Orch receipt",
            )

        cutoff = review.reviewed_at
        parent_rows = tuple(
            row
            for row in self._persistence.reconstruct_as_of(
                effective_cutoff=cutoff,
                recorded_cutoff=cutoff,
                aggregate_scope=(),
            )
            if type(row) is EconomicReceiptEventSpineV1
            and row.record_id == review.prior_bundle_ref
        )
        if len(parent_rows) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review parent is not durable before the review cutoff",
            )
        parent_spine = parent_rows[0]
        if (
            type(parent_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or parent_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review parent is not an evidence-bundle receipt",
            )
        parent = parent_spine.typed_payload.reconstruct(
            ComputationEvidenceBundleV1
        )
        lock = self._cohort_resolver.resolve_input_lock(
            review.input_lock_id,
            decision_cutoff=cutoff,
        )
        if (
            parent.terminal_state
            is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            or parent.evidence_id != review.evidence_id
            or parent.input_lock_id != review.input_lock_id
            or parent.component_or_template_ref != component_or_template_ref
            or parent.evidence_bundle_version == review.evidence_bundle_version
            or review.reviewed_source_epoch_refs != _source_epoch_refs(lock)
            or review.bundle_producer_identity == review.reviewer_identity
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review does not bind the exact READY parent, candidate, lock, or scope",
            )

        record_id = (
            f"ST12F-RECEIPT::{review.review_id}::INDEPENDENT_REVIEW_VERSION"
        )
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=record_id,
            receipt_class=ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
            operation_id="ST12F-PRIVATE::INDEPENDENT_REVIEW",
            request_id=authority_decision.request_id,
            idempotency_key=(
                f"{authority_decision.idempotency_key}::REVIEW::{review.review_id}"
            ),
            contract_type=type(review).__name__,
            contract_id=review.review_id,
            contract_version=review.contract_version,
            input_lock_id_or_explicit_absence=review.input_lock_id,
            parent_version_ref_or_explicit_absence=review.prior_bundle_ref,
            canonical_contract_json=review.canonical_json(),
            source_record_refs=(
                review.prior_bundle_ref,
                review.authority_receipt_ref,
            ),
            parameter_value_refs=lock.parameter_value_refs,
            source_epoch_refs=_source_epoch_refs(lock),
            typed_reason_codes=review.blocker_codes,
            terminal_state=review.decision.value,
            fixture_only_not_evidence=False,
        )
        spine = EconomicReceiptEventSpineV1(
            record_id=record_id,
            record_type=EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL,
            schema_version="QTT_ST12F_EVIDENCE_CONTROL_RECEIPT_SPINE_V1",
            semantic_owner="IndependentEvidenceReviewV1",
            implementation_owner="IndependentEvidenceReviewV1",
            context_ref=context_ref,
            effective_at=review.reviewed_at,
            recorded_at=review.reviewed_at,
            causation_id=lock.causation_id,
            correlation_id=lock.correlation_id,
            traceparent=traceparent,
            tracestate=tracestate,
            sequence=0,
            aggregate_id=review.review_id,
            aggregate_version=1,
            authority_class="INDEPENDENT_REVIEW_NO_EFFECT",
            typed_payload=payload,
            no_effect_flags=NO_EFFECTS_V1,
        )
        transition = StateTransitionReceiptV1(
            transition_id=f"ST12F-CONTROL-STATE::{record_id}",
            aggregate_id=f"ST12F-CONTROL::{record_id}",
            transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
            prior_state="NEW",
            event_class="ST12F_INDEPENDENT_REVIEW_COMMITTED",
            candidate_state="ACTIVE",
            disposition=TransitionDispositionV1.ACCEPTED,
            event_identity=record_id,
            aggregate_version_before=0,
            aggregate_version_after=1,
            effective_at=review.reviewed_at,
            recorded_at=review.reviewed_at,
            reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
            reconciliation_required=False,
        )
        transaction = self._persistence.begin_transaction()
        try:
            self._persistence.insert_receipt_record(transaction, spine)
            self._persistence.insert_state_transition(transaction, transition)
            transaction.commit()
        except BaseException:
            if transaction.is_active:
                transaction.rollback()
            raise
        persisted = self._persistence.get_record(record_id)
        if type(persisted) is not EconomicReceiptEventSpineV1:
            raise PersistenceContractError(
                ReasonCode.OWNER_DATA_MISSING,
                "committed independent-review receipt is absent",
            )
        return persisted


class ComputationEvidenceServiceV1:
    """One evidence owner over injected compiler, review, and ST12-C owners."""

    supports_typed_reference_query = True

    def __init__(
        self,
        cohort_resolver: CohortCompilationResolverProtocolV1,
        persistence_adapter: PersistenceAdapterV1,
        *,
        bundle_candidate_resolver: EvidenceBundleCandidateResolverProtocolV1 | None = None,
        producer_identity: str = "ComputationEvidenceServiceV1",
    ) -> None:
        if not isinstance(persistence_adapter, PersistenceAdapterV1) or persistence_adapter.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "OP14/OP15 require existing available ST12-C persistence")
        if not callable(getattr(cohort_resolver, "resolve_input_lock", None)) or not callable(getattr(cohort_resolver, "resolve_expected_slot", None)):
            raise ContractValidationError(ReasonCode.INPUT_OWNER_MISMATCH, "evidence service requires the canonical compiler resolver")
        self._cohort_resolver = cohort_resolver
        self._persistence = persistence_adapter
        self._bundle_candidate_resolver = bundle_candidate_resolver
        self._producer_identity = _text(producer_identity, "producer_identity")
        minimum = datetime.min.replace(tzinfo=UTC)
        self._cache_snapshot = EvidenceCacheSnapshotV1(
            generation=0,
            effective_watermark=minimum,
            recorded_watermark=minimum,
            lane_results={},
            slot_results={},
            divergence={},
            bundles={},
            current_bundles={},
            reviews={},
            d_references={},
            g_handoffs={},
        )
        self._cache_publication_lock = Lock()
        now = datetime.now(UTC)
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=now,
            recorded_cutoff=now,
        )

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

    def _records_as_of(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> tuple[object, ...]:
        effective = parse_utc(effective_cutoff, field_name="effective_cutoff")
        recorded = parse_utc(recorded_cutoff, field_name="recorded_cutoff")
        return self._persistence.reconstruct_as_of(
            effective_cutoff=effective,
            recorded_cutoff=recorded,
            aggregate_scope=(),
        )

    def _durable_receipt_spines(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> tuple[EconomicReceiptEventSpineV1, ...]:
        rows = self._persistence.reconstruct_as_of(
            effective_cutoff=parse_utc(
                effective_cutoff,
                field_name="effective_cutoff",
            ),
            recorded_cutoff=parse_utc(
                recorded_cutoff,
                field_name="recorded_cutoff",
            ),
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

    def _durable_computation_spines(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> tuple[EconomicReceiptEventSpineV1, ...]:
        return tuple(
            sorted(
                (
                    row
                    for row in self._records_as_of(
                        effective_cutoff=effective_cutoff,
                        recorded_cutoff=recorded_cutoff,
                    )
                    if type(row) is EconomicReceiptEventSpineV1
                    and row.record_type
                    is EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
                    and type(row.typed_payload)
                    is DurableComputationExecutionReceiptRecordV1
                ),
                key=lambda row: (row.recorded_at, row.record_id),
            )
        )

    def _spine_as_of(
        self,
        record_ref: str,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> EconomicReceiptEventSpineV1:
        matches = tuple(
            row
            for row in self._records_as_of(
                effective_cutoff=effective_cutoff,
                recorded_cutoff=recorded_cutoff,
            )
            if type(row) is EconomicReceiptEventSpineV1
            and row.record_id == record_ref
        )
        if len(matches) != 1:
            raise PersistenceContractError(
                ReasonCode.OWNER_DATA_MISSING,
                "receipt is absent at the explicit effective/recorded cutoff",
            )
        return matches[0]

    def _validate_receipt_lock_metadata(
        self,
        spine: EconomicReceiptEventSpineV1,
        *,
        decision_cutoff: datetime,
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
            payload.input_lock_id_or_explicit_absence,
            decision_cutoff=decision_cutoff,
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

    @staticmethod
    def _validate_contract_visibility(
        value: object,
        *,
        evaluation_time: datetime,
    ) -> None:
        evaluation = parse_utc(
            evaluation_time,
            field_name="evaluation_time",
        )
        observed = getattr(value, "observed_at", None)
        if observed is None:
            observed = getattr(value, "reviewed_at", None)
        valid_until = getattr(value, "valid_until", None)
        if (
            isinstance(observed, datetime)
            and evaluation < parse_utc(observed, field_name="observed_at")
        ) or (
            isinstance(valid_until, datetime)
            and evaluation > parse_utc(valid_until, field_name="valid_until")
        ):
            raise ContractValidationError(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "contract is not visible at the explicit decision cutoff",
            )

    def _rebuild_caches_from_durable_receipts(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> EvidenceCacheSnapshotV1:
        effective = parse_utc(effective_cutoff, field_name="effective_cutoff")
        recorded = parse_utc(recorded_cutoff, field_name="recorded_cutoff")
        observed_snapshot = self._cache_snapshot
        effective = max(effective, observed_snapshot.effective_watermark)
        recorded = max(recorded, observed_snapshot.recorded_watermark)
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
        for spine in self._durable_receipt_spines(
            effective_cutoff=effective,
            recorded_cutoff=recorded,
        ):
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class in {
                ST12FReceiptClassV1.COHORT_COMPILATION,
                ST12FReceiptClassV1.INPUT_LOCK,
            }:
                continue
            expected_type = self._contract_type_for_receipt_class(payload.receipt_class)
            value = payload.reconstruct(expected_type)
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=recorded,
            )
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
        candidate = EvidenceCacheSnapshotV1(
            generation=0,
            effective_watermark=effective,
            recorded_watermark=recorded,
            lane_results=lane_results,
            slot_results=slots,
            divergence=divergence,
            bundles=bundles,
            current_bundles=current,
            reviews=reviews,
            d_references=d_references,
            g_handoffs=g_handoffs,
        )
        with self._cache_publication_lock:
            current_snapshot = self._cache_snapshot
            if (
                current_snapshot.effective_watermark > effective
                or current_snapshot.recorded_watermark > recorded
            ):
                return current_snapshot
            published = replace(
                candidate,
                generation=current_snapshot.generation + 1,
            )
            self._cache_snapshot = published
            return published

    def _load_contract(
        self,
        record_ref: str,
        expected_type: type[object],
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> object:
        spine = self._spine_as_of(
            record_ref,
            effective_cutoff=effective_cutoff,
            recorded_cutoff=recorded_cutoff,
        )
        if type(spine) is not EconomicReceiptEventSpineV1 or type(spine.typed_payload) is not ST12FEvidenceControlReceiptRecordV1:
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "typed ST12-F receipt is absent")
        value = spine.typed_payload.reconstruct(expected_type)
        self._validate_receipt_lock_metadata(
            spine,
            decision_cutoff=recorded_cutoff,
        )
        self._validate_contract_visibility(
            value,
            evaluation_time=effective_cutoff,
        )
        return value

    def resolve_lane_result(
        self,
        result_id: str,
        lane: str,
        *,
        decision_cutoff: datetime,
    ) -> ReplayResultContractV1 | PaperResultContractV1:
        expected_type = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1 if lane == "PAPER" else None
        if expected_type is None:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "lane must be exact")
        receipt_ref = f"ST12F-RECEIPT::{result_id}::{lane}_REGISTRATION"
        value = self._load_contract(
            receipt_ref,
            expected_type,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        if type(value) is not expected_type:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "REPLAY/PAPER packets are non-interchangeable")
        return value  # type: ignore[return-value]

    def resolve_bundle(
        self,
        bundle_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> ComputationEvidenceBundleV1:
        value = self._load_contract(
            bundle_ref,
            ComputationEvidenceBundleV1,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        return value  # type: ignore[return-value]

    def resolve_review(
        self,
        review_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> IndependentReviewRecordV1:
        receipt_ref = (
            review_ref
            if review_ref.startswith("ST12F-RECEIPT::")
            else f"ST12F-RECEIPT::{review_ref}::INDEPENDENT_REVIEW_VERSION"
        )
        value = self._load_contract(
            receipt_ref,
            IndependentReviewRecordV1,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        return value  # type: ignore[return-value]

    def resolve_control_receipt(
        self,
        receipt_ref: str,
        expected_type: type[object],
        *,
        decision_cutoff: datetime,
    ) -> object:
        """Canonical read path for every OP14/OP15 receipt class."""

        return self._load_contract(
            receipt_ref,
            expected_type,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )

    def resolve_g_handoff(
        self,
        handoff_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> FToGHandoffReferencesV1:
        receipt_ref = (
            handoff_ref
            if handoff_ref.startswith("ST12F-RECEIPT::")
            else f"ST12F-RECEIPT::{handoff_ref}::G_HANDOFF_REFERENCE"
        )
        value = self._load_contract(
            receipt_ref,
            FToGHandoffReferencesV1,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        return value  # type: ignore[return-value]

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
        request: (
            RegisterReplayPaperResultRequestV1
            | BuildEvidenceBundleRequestV1
            | RegisterEvidenceControlRequestV1
        ),
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
        operation_id = (
            "ST10-OP::14"
            if type(request) is RegisterReplayPaperResultRequestV1
            else "ST10-OP::15"
            if type(request) is BuildEvidenceBundleRequestV1
            else "ST12F-PRIVATE::REGISTER_CONTROL"
        )
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=record_id,
            receipt_class=receipt_class,
            operation_id=operation_id,
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
        request: (
            RegisterReplayPaperResultRequestV1
            | BuildEvidenceBundleRequestV1
            | RegisterEvidenceControlRequestV1
        ),
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
    ) -> RegisteredLaneResultOutcomeV1:
        initialize_st12f_parameter_registry_v1()
        if type(request) is not RegisterReplayPaperResultRequestV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP14 delegate requires exact request")
        value = lane_packet_from_typed_record_v1(request.result_packet, lane=request.lane) if packet is None else packet
        expected_type = ReplayResultContractV1 if request.lane == "REPLAY" else PaperResultContractV1
        if type(value) is not expected_type:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "OP14 rejects cross-lane packet substitution")
        lock = self._cohort_resolver.resolve_input_lock(
            request.input_lock_id,
            decision_cutoff=request.requested_at,
        )
        if value.input_lock_id != lock.input_lock_id or request.input_lock_id != lock.input_lock_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "caller and packet lock assertions differ from canonical lock")
        slot = self._cohort_resolver.resolve_expected_slot(
            request.cohort_instance_id,
            request.lane,
            value.expected_result_contract_id,
            decision_cutoff=request.requested_at,
        )
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
        durable_lanes, durable_slots = self._durable_lane_index(
            decision_cutoff=request.requested_at,
        )
        existing_id = durable_slots.get(natural_slot)
        if existing_id is not None:
            existing = durable_lanes[existing_id]
            if deterministic_json(existing) == deterministic_json(value):
                receipt_class = (
                    ST12FReceiptClassV1.REPLAY_REGISTRATION
                    if request.lane == "REPLAY"
                    else ST12FReceiptClassV1.PAPER_REGISTRATION
                )
                return RegisteredLaneResultOutcomeV1(
                    registered_result=existing,
                    receipt_refs=(
                        f"ST12F-RECEIPT::{existing.result_id}::"
                        f"{receipt_class.value}",
                    ),
                )
            raise ContractValidationError(ReasonCode.ST12F_RESULT_SLOT_CONFLICT, "a competing result already owns this immutable slot")
        if value.fixture_only_not_evidence:
            return RegisteredLaneResultOutcomeV1(value, ())
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
            check_lanes, check_slots = self._durable_lane_index(
                decision_cutoff=request.requested_at,
            )
            owner_id = check_slots.get(natural_slot)
            if (
                owner_id is not None
                and deterministic_json(check_lanes[owner_id])
                == deterministic_json(value)
            ):
                receipt_class = (
                    ST12FReceiptClassV1.REPLAY_REGISTRATION
                    if request.lane == "REPLAY"
                    else ST12FReceiptClassV1.PAPER_REGISTRATION
                )
                return RegisteredLaneResultOutcomeV1(
                    registered_result=check_lanes[owner_id],
                    receipt_refs=(
                        f"ST12F-RECEIPT::{owner_id}::{receipt_class.value}",
                    ),
                )
            if owner_id is not None:
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "a competing durable result owns this immutable natural slot",
                ) from exc
            raise
        committed = persisted.typed_payload.reconstruct(expected_type)
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        return RegisteredLaneResultOutcomeV1(
            registered_result=committed,  # type: ignore[arg-type]
            receipt_refs=(persisted.record_id,),
        )

    def _durable_lane_index(
        self,
        *,
        decision_cutoff: datetime,
    ) -> tuple[
        dict[str, ReplayResultContractV1 | PaperResultContractV1],
        dict[tuple[str, str, str, str], str],
    ]:
        lanes: dict[str, ReplayResultContractV1 | PaperResultContractV1] = {}
        slots: dict[tuple[str, str, str, str], str] = {}
        for spine in self._durable_receipt_spines(
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        ):
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
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=decision_cutoff,
            )
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

    def _validate_divergence(
        self,
        assessment: DivergenceAssessmentV1,
        *,
        decision_cutoff: datetime,
    ) -> None:
        if type(assessment) is not DivergenceAssessmentV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "divergence must be exact typed contract")
        replay = self.resolve_lane_result(
            assessment.replay_result_ref,
            "REPLAY",
            decision_cutoff=decision_cutoff,
        )
        paper = self.resolve_lane_result(
            assessment.paper_result_ref,
            "PAPER",
            decision_cutoff=decision_cutoff,
        )
        if replay.input_lock_id != assessment.input_lock_id or paper.input_lock_id != assessment.input_lock_id or replay.cohort_template_id != assessment.cohort_template_id or paper.cohort_template_id != assessment.cohort_template_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "divergence inputs do not share one lock/template")

    def register_control(
        self,
        request: RegisterEvidenceControlRequestV1,
        contract: object,
    ) -> EconomicReceiptEventSpineV1:
        """Private durable writer for the four non-review control classes."""

        if type(request) is not RegisterEvidenceControlRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "control registration requires the exact private request",
            )
        allowed = {
            DivergenceAssessmentV1,
            ModelRiskEvidenceAssessmentV1,
            QuantumTraceValidationReceiptV1,
            DeterministicEvidenceAnnotationContractV1,
        }
        if type(contract) not in allowed:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private control registration rejects bundle, review, D, and G custody",
            )
        lock = self._cohort_resolver.resolve_input_lock(
            request.input_lock_id,
            decision_cutoff=request.requested_at,
        )
        if getattr(contract, "input_lock_id", None) != lock.input_lock_id:
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "control input lock differs from the private request",
            )
        if type(contract) is DivergenceAssessmentV1:
            self._validate_divergence(
                contract,
                decision_cutoff=request.requested_at,
            )
        spine = self._receipt(request=request, contract=contract, input_lock=lock)
        receipt_class, *_ = self._contract_receipt_parts(contract)
        persisted = self._persist_many(
            request=request,
            spines=(spine,),
            primary_record_ref=spine.record_id,
            identity_class=f"ST12F-PRIVATE::REGISTER_CONTROL::{receipt_class.value}",
        )
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        return persisted

    def build_bundle(
        self,
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1 | None = None,
    ) -> BuiltEvidenceBundleOutcomeV1:
        initialize_st12f_parameter_registry_v1()
        if type(request) is not BuildEvidenceBundleRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "OP15 requires the exact public request",
            )
        if candidate is None and self._bundle_candidate_resolver is not None:
            candidate = self._bundle_candidate_resolver.resolve_bundle_candidate(request)
        if type(candidate) is not ComputationEvidenceBundleV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP15 requires exact request and canonical candidate")
        lock = self._cohort_resolver.resolve_input_lock(
            request.input_lock_id,
            decision_cutoff=request.requested_at,
        )
        if candidate.input_lock_id != lock.input_lock_id or candidate.component_or_template_ref != request.component_id or request.required_lanes != ("REPLAY", "PAPER"):
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "OP15 scope differs from canonical lock/component/dual lane")
        bundle_record_ref = f"ST12F-RECEIPT::{candidate.evidence_bundle_version}::EVIDENCE_BUNDLE_VERSION"
        try:
            existing_bundle_spine = self._spine_as_of(
                bundle_record_ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
        except PersistenceContractError:
            existing_bundle_spine = None
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
            existing_refs: list[str] = [bundle_record_ref]
            if candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
                assert type(candidate.d_evidence_reference_projection) is ST12FEvidenceReferenceV1
                assert type(candidate.g_handoff_projection) is FToGHandoffReferencesV1
                existing_refs.extend(
                    (
                        f"ST12F-RECEIPT::{candidate.d_evidence_reference_projection.reference_id}::D_EVIDENCE_REFERENCE",
                        f"ST12F-RECEIPT::{candidate.g_handoff_projection.handoff_id}::G_HANDOFF_REFERENCE",
                    )
                )
            for ref in existing_refs:
                self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            return BuiltEvidenceBundleOutcomeV1(
                evidence_bundle=existing_bundle,
                receipt_refs=tuple(existing_refs),
            )
        previous_ref = self._durable_current_bundle_ref(
            candidate.evidence_id,
            candidate.input_lock_id,
            candidate.component_or_template_ref,
            decision_cutoff=request.requested_at,
        )
        expected_parent = previous_ref or "EXPLICIT_ABSENCE"
        previous = (
            None
            if previous_ref is None
            else self.resolve_bundle(
                previous_ref,
                decision_cutoff=request.requested_at,
            )
        )
        self._validate_bundle_transition(previous, candidate)

        replay = (
            None
            if candidate.replay_result_ref == "EXPLICIT_ABSENCE"
            else self.resolve_lane_result(
                candidate.replay_result_ref,
                "REPLAY",
                decision_cutoff=request.requested_at,
            )
        )
        paper = (
            None
            if candidate.paper_result_ref == "EXPLICIT_ABSENCE"
            else self.resolve_lane_result(
                candidate.paper_result_ref,
                "PAPER",
                decision_cutoff=request.requested_at,
            )
        )
        self._validate_bundle_lanes(candidate, lock, replay, paper)
        admission = self._admit_bundle_evidence(
            request=request,
            candidate=candidate,
            lock=lock,
            replay=replay,
            paper=paper,
        )
        divergence = admission.divergence
        if divergence is not None:
            if divergence.assessment_id != candidate.divergence_assessment_ref:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle divergence reference differs from its contract",
                )
            self._validate_divergence(
                divergence,
                decision_cutoff=request.requested_at,
            )
        self._validate_bundle_divergence(candidate, divergence)
        model_risk = admission.model_risk
        review = admission.review
        self._validate_bundle_model_risk(
            request=request,
            previous_ref=previous_ref,
            previous=previous,
            candidate=candidate,
            lock=lock,
            model_risk=model_risk,
            review=review,
        )
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
            lock=lock,
        )

        self._validate_closed_projections(
            candidate,
            bundle_record_ref=bundle_record_ref,
            lock=lock,
        )
        bundle_spine = self._receipt(
            request=request,
            contract=candidate,
            input_lock=lock,
            bundle_parent_ref=expected_parent,
        )
        spines: list[EconomicReceiptEventSpineV1] = [bundle_spine]
        if candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
            assert type(candidate.d_evidence_reference_projection) is ST12FEvidenceReferenceV1
            assert type(candidate.g_handoff_projection) is FToGHandoffReferencesV1
            spines.extend(
                (
                    self._receipt(request=request, contract=candidate.d_evidence_reference_projection, input_lock=lock),
                    self._receipt(request=request, contract=candidate.g_handoff_projection, input_lock=lock),
                )
            )
        parent_aggregate = (
            "ST12F-BUNDLE-PARENT::"
            f"{candidate.evidence_id}::{candidate.input_lock_id}::"
            f"{candidate.component_or_template_ref}::ROOT"
            if previous_ref is None
            else f"ST12F-BUNDLE-PARENT::{previous_ref}"
        )
        parent_edge = StateTransitionReceiptV1(
            transition_id=(
                f"{parent_aggregate}::CHILD::{bundle_spine.record_id}"
            ),
            aggregate_id=parent_aggregate,
            transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
            prior_state="NEW",
            event_class="ST12F_BUNDLE_CHILD_PUBLISHED",
            candidate_state="ACTIVE",
            disposition=TransitionDispositionV1.ACCEPTED,
            event_identity=bundle_spine.record_id,
            aggregate_version_before=0,
            aggregate_version_after=1,
            effective_at=request.requested_at,
            recorded_at=request.requested_at,
            reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
            reconciliation_required=False,
        )
        try:
            persisted = self._persist_many(
                request=request,
                spines=tuple(spines),
                primary_record_ref=bundle_spine.record_id,
                identity_class="ST10-OP::15",
                extra_transitions=(parent_edge,),
            )
        except PersistenceContractError as exc:
            try:
                concurrent = self._spine_as_of(
                    bundle_record_ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                raise exc
            if (
                type(concurrent.typed_payload)
                is not ST12FEvidenceControlReceiptRecordV1
                or concurrent.typed_payload.receipt_class
                is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
            ):
                raise exc
            concurrent_bundle = concurrent.typed_payload.reconstruct(
                ComputationEvidenceBundleV1
            )
            if deterministic_json(concurrent_bundle) != deterministic_json(candidate):
                raise exc
            concurrent_refs = tuple(row.record_id for row in spines)
            for ref in concurrent_refs:
                self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            return BuiltEvidenceBundleOutcomeV1(
                evidence_bundle=concurrent_bundle,
                receipt_refs=concurrent_refs,
            )
        value = persisted.typed_payload.reconstruct(ComputationEvidenceBundleV1)
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        return BuiltEvidenceBundleOutcomeV1(
            evidence_bundle=value,
            receipt_refs=tuple(row.record_id for row in spines),
        )

    def _durable_current_bundle_ref(
        self,
        evidence_id: str,
        input_lock_id: str,
        component_or_template_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> str | None:
        matches: list[
            tuple[str, ComputationEvidenceBundleV1, str]
        ] = []
        for spine in self._durable_receipt_spines(
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        ):
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
                continue
            value = payload.reconstruct(ComputationEvidenceBundleV1)
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=decision_cutoff,
            )
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

    @staticmethod
    def _ordered_unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(values))

    @staticmethod
    def _validate_bound_output_value(
        value: object,
        *,
        output_type: str,
    ) -> None:
        def finite_numeric(item: object) -> bool:
            if isinstance(item, bool):
                return False
            if isinstance(item, int):
                return True
            if isinstance(item, float):
                return math.isfinite(item)
            if isinstance(item, str):
                try:
                    return exact_decimal(item, field_name="actual_value").is_finite()
                except ContractValidationError:
                    return False
            return False

        valid = False
        if output_type == "Decimal":
            valid = finite_numeric(value)
        elif output_type == "float64":
            valid = (
                not isinstance(value, bool)
                and isinstance(value, int | float)
                and math.isfinite(float(value))
            )
        elif output_type == "[float64,float64]":
            valid = (
                isinstance(value, list)
                and len(value) == 2
                and all(finite_numeric(item) for item in value)
            )
        elif output_type == "float64 matrix":
            valid = (
                isinstance(value, list)
                and bool(value)
                and all(isinstance(row, list) and bool(row) for row in value)
                and len({len(row) for row in value}) == 1
                and all(finite_numeric(item) for row in value for item in row)
            )
        elif output_type in {
            "typed vector",
            "typed fold registry",
            "typed path registry",
        }:
            valid = isinstance(value, list) and bool(value)
        elif output_type in {
            "typed record",
            "typed statistical result",
            "typed result",
            "typed Decimal record",
            "enum and LCB value",
            "typed multi-metric record",
        }:
            valid = isinstance(value, Mapping) and bool(value)
        if not valid:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable evidence output has the wrong type or a nonfinite value",
            )

    def _validate_computation_evidence_receipt(
        self,
        spine: EconomicReceiptEventSpineV1,
        *,
        binding: EvidenceOutputBindingV1,
        lock: ImmutableReplayPaperInputLockV1,
        component_or_template_ref: str,
        decision_cutoff: datetime,
    ) -> tuple[str, QuantumClassicalNoTradeComparisonV1 | None]:
        if (
            spine.record_type
            is not EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
            or type(spine.typed_payload)
            is not DurableComputationExecutionReceiptRecordV1
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "executed evidence does not resolve to a durable computation receipt",
            )
        payload = spine.typed_payload
        receipt = payload.existing_receipt
        expected_implementation = str(
            lock.implementation_versions.get(binding.math_spec_id, "")
        )
        if (
            payload.record_id != spine.record_id
            or receipt.specification_id != binding.math_spec_id
            or not expected_implementation
            or receipt.implementation_id != expected_implementation
            or payload.input_snapshot_ref != lock.input_lock_id
            or payload.consumer_ref != component_or_template_ref
            or payload.failure_code is not None
            or payload.no_order_authority_flag is not True
            or spine.effective_at > decision_cutoff
            or spine.recorded_at > decision_cutoff
            or payload.output_unit != binding.output_unit
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "durable computation receipt fails its math/lock/scope/version/cutoff join",
            )
        expected_basis = ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1.get(
            binding.math_spec_id
        )
        if expected_basis is not None and payload.output_basis != expected_basis:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "metric evidence output basis differs from the owner matrix",
            )
        output = safe_json_loads(receipt.output_json)
        if not isinstance(output, Mapping) or binding.output_name not in output:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable computation output omits its exact canonical value path",
            )
        actual = output[binding.output_name]
        self._validate_bound_output_value(actual, output_type=binding.output_type)
        comparison: QuantumClassicalNoTradeComparisonV1 | None = None
        if binding.math_spec_id == "MATH-52":
            try:
                comparison = QuantumClassicalNoTradeComparisonV1.from_canonical_mapping(
                    actual
                )
            except (ContractValidationError, TypeError, ValueError) as exc:
                raise ContractValidationError(
                    ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                    "MATH-52 output is not the exact 11-dimensional comparison",
                ) from exc
            if (
                comparison.input_lock_id != lock.input_lock_id
                or len(fields(comparison.comparison_basis)) != 11
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                    "MATH-52 comparison differs from the lock or 11-dimensional basis",
                )
        return receipt.implementation_id, comparison

    def _validate_quantum_evidence_receipt(
        self,
        spine: EconomicReceiptEventSpineV1,
        *,
        math_spec_id: str,
        lock: ImmutableReplayPaperInputLockV1,
        decision_cutoff: datetime,
    ) -> str:
        if (
            type(spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-50/51 evidence is not a quantum trace-validation receipt",
            )
        value = spine.typed_payload.reconstruct(
            QuantumTraceValidationReceiptV1
        )
        self._validate_receipt_lock_metadata(
            spine,
            decision_cutoff=decision_cutoff,
        )
        implementation = str(lock.implementation_versions.get(math_spec_id, ""))
        if (
            value.math_spec_id != math_spec_id
            or value.input_lock_id != lock.input_lock_id
            or not implementation
            or not set(_source_epoch_refs(lock))
            <= set(value.comparison_basis.version_epoch_pins)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "quantum evidence differs from exact math, lock, implementation, or epochs",
            )
        return implementation

    @staticmethod
    def _flatten_dispositions(
        candidate: ComputationEvidenceBundleV1,
    ) -> tuple[EvidenceIdentityDispositionV1, ...]:
        rows = tuple(
            row
            for section_name in _SECTION_FIELDS_V1
            for row in getattr(candidate, section_name).identity_dispositions
        )
        if tuple(row.evidence_identity for row in rows) != ST12F_EVIDENCE_IDENTITIES_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "evidence dispositions differ from exact owner math order",
            )
        return rows

    def _stack_truth(
        self,
        request: BuildEvidenceBundleRequestV1,
        *,
        consumed_refs: set[str],
        component_receipt_refs: Mapping[str, str],
    ) -> tuple[Mapping[str, object], tuple[str, ...]]:
        stack_rows: list[tuple[str, str, object]] = []
        declared_membership = False
        for ref in request.evidence_record_refs:
            if ref in consumed_refs:
                continue
            try:
                spine = self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                continue
            if (
                spine.record_type
                is not EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
                or type(spine.typed_payload)
                is not DurableComputationExecutionReceiptRecordV1
            ):
                continue
            payload = spine.typed_payload
            output = safe_json_loads(payload.existing_receipt.output_json)
            if not isinstance(output, Mapping):
                continue
            declared = output.get("stack_id")
            if payload.existing_receipt.specification_id.startswith("STACK::"):
                if not isinstance(declared, str) or not declared:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack receipt output omits stack_id",
                    )
                stack = REGISTERED_FORMULA_STACKS.get(declared)
                component_outputs = output.get("component_outputs")
                expected_stack_fields = {
                    field.name for field in fields(StackResultV1)
                }
                if (
                    stack is None
                    or set(output) != expected_stack_fields
                    or payload.existing_receipt.specification_id
                    != f"STACK::{declared}"
                    or payload.input_snapshot_ref != request.input_lock_id
                    or payload.consumer_ref != request.component_id
                    or not isinstance(component_outputs, list)
                    or output.get("no_authority_flag") is not True
                    or output.get("terminal_route")
                    != "DETERMINISTIC_DEPENDENCY_CLOSED_STACK_RESULT"
                    or not isinstance(output.get("result_id"), str)
                    or not output["result_id"]
                    or not isinstance(output.get("evidence_refs"), list)
                    or not isinstance(output.get("conversion_receipt_refs"), list)
                ):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack receipt differs from the exact StackResultV1 contract",
                    )
                if tuple(output["evidence_refs"]) != payload.dependency_receipt_refs:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack result evidence refs differ from durable dependencies",
                    )
                ordered_component_refs: list[str] = []
                ordered_math_ids: list[str] = []
                expected_component_fields = {
                    field.name for field in fields(FrozenFormulaOutputV1)
                }
                for component_output in component_outputs:
                    if not isinstance(component_output, Mapping):
                        raise ContractValidationError(
                            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                            "stack component output is not a canonical mapping",
                        )
                    refs = component_output.get("receipt_refs")
                    math_spec_id = component_output.get("math_spec_id")
                    implementation_id = component_output.get("implementation_id")
                    dependency_payload: object | None = None
                    if isinstance(refs, list) and len(refs) == 1:
                        try:
                            dependency_spine = self._spine_as_of(
                                str(refs[0]),
                                effective_cutoff=request.requested_at,
                                recorded_cutoff=request.requested_at,
                            )
                        except PersistenceContractError:
                            dependency_spine = None
                        if (
                            dependency_spine is not None
                            and dependency_spine.record_type
                            is EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
                            and type(dependency_spine.typed_payload)
                            is DurableComputationExecutionReceiptRecordV1
                        ):
                            dependency_payload = dependency_spine.typed_payload
                    if (
                        set(component_output) != expected_component_fields
                        or not isinstance(refs, list)
                        or len(refs) != 1
                        or component_output.get("no_authority_flag") is not True
                        or not isinstance(math_spec_id, str)
                        or math_spec_id not in component_receipt_refs
                        or refs[0] != component_receipt_refs[math_spec_id]
                        or type(dependency_payload)
                        is not DurableComputationExecutionReceiptRecordV1
                        or dependency_payload.existing_receipt.specification_id
                        != math_spec_id
                        or implementation_id
                        != dependency_payload.existing_receipt.implementation_id
                    ):
                        raise ContractValidationError(
                            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                            "stack component output differs from exact durable custody",
                        )
                    ordered_math_ids.append(math_spec_id)
                    ordered_component_refs.append(str(refs[0]))
                if (
                    tuple(ordered_math_ids) != stack.component_ids
                    or tuple(ordered_component_refs)
                    != payload.dependency_receipt_refs
                ):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack component and dependency order differs from registry",
                    )
                if not set(ordered_component_refs) <= set(component_receipt_refs.values()):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack dependency refs are not consumed component receipts",
                    )
                stack_rows.append((declared, ref, stack.stack_version))
                consumed_refs.add(ref)
            elif isinstance(declared, str) and declared in REGISTERED_FORMULA_STACKS:
                declared_membership = True
        if declared_membership and not stack_rows:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "component receipt declares stack membership without stack custody",
            )
        if len({row[0] for row in stack_rows}) != len(stack_rows):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "duplicate durable stack receipts were consumed",
            )
        ordered = tuple(sorted(stack_rows, key=lambda row: row[0]))
        return (
            MappingProxyType({stack_id: version for stack_id, _, version in ordered}),
            tuple(ref for _, ref, _ in ordered),
        )

    def _find_control_in_request(
        self,
        request: BuildEvidenceBundleRequestV1,
        receipt_class: ST12FReceiptClassV1,
        expected_type: type[object],
    ) -> tuple[object | None, str | None]:
        matches: list[tuple[object, str]] = []
        for ref in request.evidence_record_refs:
            try:
                spine = self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                continue
            if (
                type(spine) is EconomicReceiptEventSpineV1
                and type(spine.typed_payload) is ST12FEvidenceControlReceiptRecordV1
                and spine.typed_payload.receipt_class is receipt_class
            ):
                value = spine.typed_payload.reconstruct(expected_type)
                self._validate_receipt_lock_metadata(
                    spine,
                    decision_cutoff=request.requested_at,
                )
                self._validate_contract_visibility(
                    value,
                    evaluation_time=request.requested_at,
                )
                matches.append((value, ref))
        if len(matches) > 1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "OP15 evidence roster contains duplicate control classes",
            )
        return (None, None) if not matches else matches[0]

    def _find_review_for_request(
        self,
        request: BuildEvidenceBundleRequestV1,
    ) -> tuple[IndependentReviewRecordV1 | None, str | None]:
        durable, receipt_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
            IndependentReviewRecordV1,
        )
        if durable is not None:
            assert type(durable) is IndependentReviewRecordV1
            return durable, receipt_ref
        return None, None

    def _admit_bundle_evidence(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
        replay: ReplayResultContractV1 | None,
        paper: PaperResultContractV1 | None,
    ) -> _EvidenceAdmissionResultV1:
        dispositions = self._flatten_dispositions(candidate)
        consumed: set[str] = set()
        lock_ref = f"ST12F-RECEIPT::{lock.input_lock_id}::INPUT_LOCK"
        lane_refs = candidate.lane_execution_receipt_refs
        for ref in (lock_ref, *lane_refs):
            self._spine_as_of(
                ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
            consumed.add(ref)

        component_versions: dict[str, object] = {}
        component_receipt_refs: dict[str, str] = {}
        math_refs: list[str] = []
        quantum_refs: dict[str, str] = {}
        math52_ref: str | None = None
        static_refs: list[str] = []
        disposition_negative: list[str] = []
        actual_metric_ids: list[str] = []
        for disposition in dispositions:
            math_spec_id = disposition.evidence_identity
            binding = _EVIDENCE_OUTPUT_BINDING_BY_MATH_ID_V1[math_spec_id]
            if (
                disposition.disposition
                is EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON
            ):
                disposition_negative.extend(
                    f"DISPOSITION::{math_spec_id}::{code.value}"
                    for code in disposition.blocker_codes
                )
                continue
            if (
                disposition.disposition
                is EvidenceIdentityDispositionStateV1.NOT_APPLICABLE_WITH_PROOF
            ):
                if not binding.static_not_applicable_allowed:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "metric evidence cannot be replaced by static N/A proof",
                    )
                proof = StaticEvidenceApplicabilityProofV1.for_scope(
                    math_spec_id=math_spec_id,
                    component_or_template_ref=candidate.component_or_template_ref,
                    input_lock_id=lock.input_lock_id,
                )
                if disposition.proof_refs != (proof.proof_id,):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                        "static N/A reference does not reconstruct to the exact proof",
                    )
                static_refs.append(proof.proof_id)
                consumed.add(proof.proof_id)
                continue

            ref = disposition.evidence_record_refs[0]
            if ref not in request.evidence_record_refs:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "executed disposition receipt is absent from the OP15 roster",
                )
            spine = self._spine_as_of(
                ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
            if math_spec_id in {"MATH-50", "MATH-51"}:
                implementation = self._validate_quantum_evidence_receipt(
                    spine,
                    math_spec_id=math_spec_id,
                    lock=lock,
                    decision_cutoff=request.requested_at,
                )
                quantum_refs[math_spec_id] = ref
            else:
                implementation, _comparison = (
                    self._validate_computation_evidence_receipt(
                        spine,
                        binding=binding,
                        lock=lock,
                        component_or_template_ref=(
                            candidate.component_or_template_ref
                        ),
                        decision_cutoff=request.requested_at,
                    )
                )
                if math_spec_id == "MATH-52":
                    math52_ref = ref
                else:
                    math_refs.append(ref)
            component_versions[math_spec_id] = implementation
            component_receipt_refs[math_spec_id] = ref
            consumed.add(ref)
            if binding.metric_id != "EXPLICIT_ABSENCE":
                actual_metric_ids.append(binding.metric_id)

        complete_states = {
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.STALE,
            EvidenceBundleTerminalStateV1.SUPERSEDED,
        }
        expected_metric_ids = tuple(
            row.metric_id for row in ST12F_EVIDENCE_METRIC_DEFINITIONS_V1
        )
        if (
            candidate.terminal_state in complete_states
            and tuple(actual_metric_ids) != expected_metric_ids
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "complete bundle lacks all 38 ordered actual metric values",
            )

        divergence, divergence_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT,
            DivergenceAssessmentV1,
        )
        model_risk, model_risk_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT,
            ModelRiskEvidenceAssessmentV1,
        )
        annotation, annotation_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION,
            DeterministicEvidenceAnnotationContractV1,
        )
        review, review_ref = self._find_review_for_request(request)
        for ref in (divergence_ref, model_risk_ref, annotation_ref, review_ref):
            if ref is not None:
                consumed.add(ref)

        stack_versions, stack_refs = self._stack_truth(
            request,
            consumed_refs=consumed,
            component_receipt_refs=component_receipt_refs,
        )
        stale_or_supersession_refs: list[str] = []
        for ref in request.evidence_record_refs:
            if ref in consumed:
                continue
            if candidate.terminal_state not in {
                EvidenceBundleTerminalStateV1.STALE,
                EvidenceBundleTerminalStateV1.SUPERSEDED,
            }:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "OP15 roster contains an unconsumed evidence reference",
                )
            spine = self._spine_as_of(
                ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
            if (
                type(spine.typed_payload)
                is not ST12FEvidenceControlReceiptRecordV1
                or spine.typed_payload.receipt_class
                not in {
                    ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION,
                    ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
                    ST12FReceiptClassV1.D_EVIDENCE_REFERENCE,
                }
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "STALE/SUPERSEDED proof reference is not durable custody",
                )
            stale_or_supersession_refs.append(ref)
            consumed.add(ref)

        provenance = self._ordered_unique(
            [
                lock_ref,
                *lane_refs,
                *math_refs,
                *stack_refs,
                *(() if divergence_ref is None else (divergence_ref,)),
                *(() if model_risk_ref is None else (model_risk_ref,)),
                *(() if "MATH-50" not in quantum_refs else (quantum_refs["MATH-50"],)),
                *(() if "MATH-51" not in quantum_refs else (quantum_refs["MATH-51"],)),
                *(() if math52_ref is None else (math52_ref,)),
                *(() if annotation_ref is None else (annotation_ref,)),
                *(() if review_ref is None else (review_ref,)),
                *stale_or_supersession_refs,
                *static_refs,
            ]
        )
        if (
            len(request.evidence_record_refs) != len(provenance)
            or set(request.evidence_record_refs) != set(provenance)
        ):
            raise ContractValidationError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "OP15 evidence roster differs from the exact consumed-reference union",
            )

        negative: list[str] = []
        if replay is not None:
            negative.extend(
                f"REPLAY_FAILURE::{value}" for value in replay.failure_states
            )
        if paper is not None:
            negative.extend(
                f"PAPER_FAILURE::{value}" for value in paper.failure_states
            )
        if type(divergence) is DivergenceAssessmentV1:
            negative.extend(
                f"DIVERGENCE::{code.value}" for code in divergence.typed_blockers
            )
        negative.extend(disposition_negative)
        if type(model_risk) is ModelRiskEvidenceAssessmentV1:
            review_validated = (
                type(review) is IndependentReviewRecordV1
                and review.decision is IndependentReviewDecisionV1.VALIDATED
            )
            negative.extend(
                f"NO_TRADE::{row.condition_id}"
                for row in model_risk.no_trade_condition_outcomes
                if row.active
                and not (
                    row.condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
                    and review_validated
                )
            )
            negative.extend(
                f"MODEL_RISK::{row.control_id}"
                for row in model_risk.control_evidence
                if row.state
                is ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON
            )
        if type(review) is IndependentReviewRecordV1:
            negative.extend(
                f"REVIEW::{code.value}" for code in review.blocker_codes
            )
        negative.extend(
            f"LIFECYCLE::{code.value}" for code in candidate.blocker_codes
        )
        exact_negative = self._ordered_unique(negative)
        if (
            dict(candidate.actual_executed_component_versions)
            != component_versions
            or dict(candidate.actual_executed_stack_versions)
            != dict(stack_versions)
            or candidate.source_and_provenance_refs != provenance
            or candidate.failure_and_negative_evidence_states != exact_negative
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "caller bundle truth fields differ from durable canonical reconstruction",
            )
        return _EvidenceAdmissionResultV1(
            component_versions=MappingProxyType(component_versions),
            stack_versions=stack_versions,
            provenance_refs=provenance,
            negative_states=exact_negative,
            divergence=(
                divergence if type(divergence) is DivergenceAssessmentV1 else None
            ),
            model_risk=(
                model_risk
                if type(model_risk) is ModelRiskEvidenceAssessmentV1
                else None
            ),
            review=(review if type(review) is IndependentReviewRecordV1 else None),
        )

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

    def _validate_bundle_model_risk(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        previous_ref: str | None,
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
        model_risk: ModelRiskEvidenceAssessmentV1 | None,
        review: IndependentReviewRecordV1 | None,
    ) -> None:
        if candidate.terminal_state not in {
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
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
        basis = model_risk.adjudication_basis
        lane_values = tuple(
            row for row in (basis.replay_lane, basis.paper_lane) if row is not None
        )
        if (
            model_risk.input_lock_id != candidate.input_lock_id
            or basis.expected_component_or_template_ref
            != candidate.component_or_template_ref
            or len(lane_values) != 2
            or any(
                row.input_lock_id != candidate.input_lock_id
                or row.component_or_template_ref
                != candidate.component_or_template_ref
                or not row.observed_at
                <= request.requested_at
                <= row.valid_until
                for row in lane_values
            )
            or not basis.evaluated_at
            <= request.requested_at
            <= basis.required_evidence_valid_until
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "model-risk assessment differs from the bundle lock/scope/cutoff join",
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
        review_condition = next(
            row
            for row in model_risk.no_trade_condition_outcomes
            if row.condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
        )
        if (
            candidate.terminal_state
            is EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
        ):
            if (
                not review_condition.active
                or review is not None
                or model_risk.terminal_state != "READY_FOR_INDEPENDENT_REVIEW"
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_MODEL_RISK_VETO,
                    "READY model risk must preserve only the review-pending condition",
                )
            return
        if candidate.terminal_state is EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED:
            if (
                type(review) is not IndependentReviewRecordV1
                or review.decision is not IndependentReviewDecisionV1.REJECTED
                or not review_condition.active
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_MODEL_RISK_VETO,
                    "rejected bundle requires the pre-existing rejected review join",
                )
            return
        review_ref = (
            None
            if review is None
            else f"ST12F-RECEIPT::{review.review_id}::INDEPENDENT_REVIEW_VERSION"
        )
        model_risk_ref = (
            f"ST12F-RECEIPT::{model_risk.assessment_id}::MODEL_RISK_ASSESSMENT"
        )
        if (
            type(review) is not IndependentReviewRecordV1
            or review.decision is not IndependentReviewDecisionV1.VALIDATED
            or previous_ref is None
            or previous is None
            or previous.terminal_state
            is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            or review.prior_bundle_ref != previous_ref
            or review.evidence_bundle_version != candidate.evidence_bundle_version
            or review_ref is None
            or basis.independent_review_receipt_ref != review_ref
            or review_condition.active
            or any(row.active for row in model_risk.no_trade_condition_outcomes)
            or model_risk.terminal_state != "CLOSED_INDEPENDENTLY_VALIDATED"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "closed model risk lacks exact parent/candidate/review reconciliation",
            )
        model_risk_spine = self._spine_as_of(
            model_risk_ref,
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        review_spine = self._spine_as_of(
            review_ref,
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        if (
            type(model_risk_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or model_risk_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT
            or model_risk_spine.typed_payload.operation_id
            != "ST12F-PRIVATE::REGISTER_CONTROL"
            or model_risk_spine.implementation_owner
            != "ComputationEvidenceServiceV1"
            or type(review_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or review_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION
            or not review_spine.recorded_at
            <= model_risk_spine.recorded_at
            <= request.requested_at
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "model-risk and review receipts do not preserve pre-existing segregated custody",
            )
        model_risk.assert_independent_review_join(
            assessment_receipt_ref=model_risk_ref,
            parent_ready_bundle_ref=previous_ref,
            reviewed_parent_bundle_ref=review.prior_bundle_ref,
            candidate_bundle_version=candidate.evidence_bundle_version,
            reviewed_candidate_bundle_version=review.evidence_bundle_version,
            review_receipt_ref=review_ref,
            reviewer_authority_receipt_ref=review.authority_receipt_ref,
            input_lock_id=lock.input_lock_id,
            component_or_template_ref=candidate.component_or_template_ref,
            source_epoch_refs=model_risk_spine.typed_payload.source_epoch_refs,
            reviewed_source_epoch_refs=review.reviewed_source_epoch_refs,
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
            review_recorded_at=review_spine.recorded_at,
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
            if state is EvidenceBundleTerminalStateV1.SUPERSEDED:
                return
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
        review_spine: EconomicReceiptEventSpineV1 | None = None
        if type(review) is IndependentReviewRecordV1:
            review_ref = (
                f"ST12F-RECEIPT::{review.review_id}::INDEPENDENT_REVIEW_VERSION"
            )
            try:
                review_spine = self._spine_as_of(
                    review_ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                review_spine = None
        if (
            type(review) is not IndependentReviewRecordV1
            or type(review_spine) is not EconomicReceiptEventSpineV1
            or type(review_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or review_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION
            or review_spine.typed_payload.operation_id
            != "ST12F-PRIVATE::INDEPENDENT_REVIEW"
            or review_spine.implementation_owner != "IndependentEvidenceReviewV1"
            or review_spine.typed_payload.request_id == request.request_id
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
        lock: ImmutableReplayPaperInputLockV1,
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
                or previous is None
                or type(prior_reference) is not ST12FEvidenceReferenceV1
                or prior_reference.evidence_ref != previous_ref
                or prior_reference.evidence_state
                is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_BUNDLE_STALE,
                    "CLOSED to STALE requires an exact prior closed D reference",
                )
            current = self._cohort_resolver.canonical_snapshot
            context_fields = (
                "market_scope",
                "venue_scope",
                "instrument_scope",
                "data_semantics_version",
                "venue_semantics_version",
                "accounting_definition",
                "fee_assumptions",
                "spread_assumptions",
                "slippage_assumptions",
                "fill_and_queue_assumptions",
                "latency_and_staleness_assumptions",
                "capacity_and_crowding_assumptions",
                "portfolio_and_cash_context",
                "resampling_policy",
                "scenario_set_id",
            )
            stale_triggers = (
                prior_reference.valid_until < request.requested_at,
                dict(current.source_epochs) != dict(lock.source_epochs),
                current.parameter_policy_version != lock.parameter_policy_version
                or current.parameter_value_refs != lock.parameter_value_refs,
                dict(current.formula_specification_versions)
                != dict(lock.formula_specification_versions)
                or dict(current.implementation_versions)
                != dict(lock.implementation_versions),
                any(
                    getattr(current, name) != getattr(lock, name)
                    for name in context_fields
                ),
            )
            if not any(stale_triggers):
                raise ContractValidationError(
                    ReasonCode.ST12F_BUNDLE_STALE,
                    "CLOSED to STALE requires a mechanically proven TTL, source-epoch, parameter, implementation, or context change",
                )
            return
        if state is not EvidenceBundleTerminalStateV1.SUPERSEDED:
            return
        if previous_ref is None or previous is None:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "CLOSED to SUPERSEDED requires a durable closed predecessor",
            )

        durable_spines = self._durable_receipt_spines(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
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
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=request.requested_at,
            )
            if (
                newer.terminal_state
                is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
                or newer.evidence_id != previous.evidence_id
                or newer.component_or_template_ref
                != previous.component_or_template_ref
                or newer.input_lock_id == previous.input_lock_id
            ):
                continue
            newer_lock = self._cohort_resolver.resolve_input_lock(
                newer.input_lock_id,
                decision_cutoff=request.requested_at,
            )
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
                or reference.source_epoch_refs != _source_epoch_refs(newer_lock)
                or not reference.observed_at
                <= request.requested_at
                <= reference.valid_until
                or self._durable_current_bundle_ref(
                    newer.evidence_id,
                    newer.input_lock_id,
                    newer.component_or_template_ref,
                    decision_cutoff=request.requested_at,
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
                or reference_receipt_ref not in request.evidence_record_refs
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
                    or review_spine.record_id not in request.evidence_record_refs
                    or review_payload.operation_id
                    != "ST12F-PRIVATE::INDEPENDENT_REVIEW"
                    or review_spine.implementation_owner
                    != "IndependentEvidenceReviewV1"
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
                    and review_payload.request_id != request.request_id
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

    def receipt_exists(
        self,
        receipt_ref: str,
        *,
        evaluated_at: datetime,
    ) -> bool:
        cutoff = parse_utc(evaluated_at, field_name="evaluated_at")
        try:
            matches = tuple(
                row
                for row in self._records_as_of(
                    effective_cutoff=cutoff,
                    recorded_cutoff=cutoff,
                )
                if getattr(row, "record_id", None) == receipt_ref
            )
        except PersistenceContractError:
            return False
        return len(matches) == 1

    def resolve_numeric_evidence(
        self,
        *,
        numeric_fact_id: str,
        evidence_ref: str,
        evaluated_at: datetime,
    ) -> CanonicalNumericEvidenceValueV1:
        cutoff = parse_utc(evaluated_at, field_name="evaluated_at")
        durable_spines = self._durable_receipt_spines(
            effective_cutoff=cutoff,
            recorded_cutoff=cutoff,
        )
        matches: list[
            tuple[
                EconomicReceiptEventSpineV1,
                DeterministicEvidenceAnnotationContractV1,
                CanonicalNumericEvidenceValueV1,
            ]
        ] = []
        for spine in durable_spines:
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if (
                payload.receipt_class
                is not ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION
            ):
                continue
            annotation = payload.reconstruct(
                DeterministicEvidenceAnnotationContractV1
            )
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=cutoff,
            )
            self._validate_contract_visibility(
                annotation,
                evaluation_time=cutoff,
            )
            for value in annotation.canonical_numeric_evidence:
                if (
                    value.numeric_fact_id == numeric_fact_id
                    and value.evidence_ref == evidence_ref
                ):
                    matches.append((spine, annotation, value))
        if not matches:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact is absent from canonical annotation custody at the explicit cutoff",
            )
        canonical_values = {
            deterministic_json(value) for _, _, value in matches
        }
        if len(canonical_values) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact has conflicting canonical annotation custody",
            )
        annotation_spine, annotation, value = max(
            matches,
            key=lambda row: (
                row[0].recorded_at,
                row[0].effective_at,
                row[0].record_id,
            ),
        )
        d_matches: list[
            tuple[EconomicReceiptEventSpineV1, ST12FEvidenceReferenceV1]
        ] = []
        for spine in durable_spines:
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
                continue
            reference = payload.reconstruct(ST12FEvidenceReferenceV1)
            if reference.evidence_ref != evidence_ref:
                continue
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=cutoff,
            )
            self._validate_contract_visibility(
                reference,
                evaluation_time=cutoff,
            )
            d_matches.append((spine, reference))
        if len(d_matches) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact requires one exact visible D evidence reference",
            )
        d_spine, reference = d_matches[0]
        bundle = self.resolve_bundle(
            evidence_ref,
            decision_cutoff=cutoff,
        )
        current_ref = self._durable_current_bundle_ref(
            bundle.evidence_id,
            bundle.input_lock_id,
            bundle.component_or_template_ref,
            decision_cutoff=cutoff,
        )
        if (
            value.evidence_bundle_ref != evidence_ref
            or evidence_ref not in annotation.evidence_bundle_refs
            or bundle.terminal_state
            is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
            or bundle.d_evidence_reference_projection != reference
            or current_ref != evidence_ref
            or reference.evidence_state
            is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or value.input_lock_id != bundle.input_lock_id
            or value.input_lock_id != annotation.input_lock_id
            or value.source_epoch_refs != reference.source_epoch_refs
            or value.source_epoch_refs != annotation.source_epoch_refs
            or not value.observed_at <= cutoff <= value.valid_until
            or value.evidence_receipt_ref != d_spine.record_id
            or value.numeric_recheck_receipt_ref != annotation_spine.record_id
            or not self.receipt_exists(
                value.evidence_receipt_ref,
                evaluated_at=cutoff,
            )
            or not self.receipt_exists(
                value.numeric_recheck_receipt_ref,
                evaluated_at=cutoff,
            )
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact differs from current canonical bundle, D, lock, epoch, or recheck custody",
            )
        return value

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
            durable_spines = self._durable_receipt_spines(
                effective_cutoff=observed,
                recorded_cutoff=observed,
            )
            for spine in durable_spines:
                payload = spine.typed_payload
                assert type(payload) is ST12FEvidenceControlReceiptRecordV1
                if payload.receipt_class is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
                    continue
                reference = payload.reconstruct(ST12FEvidenceReferenceV1)
                self._validate_receipt_lock_metadata(
                    spine,
                    decision_cutoff=observed,
                )
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
            decision_cutoff=observed,
        )
        try:
            bundle = self.resolve_bundle(
                reference.evidence_ref,
                decision_cutoff=observed,
            )
        except (ContractValidationError, PersistenceContractError):
            return unavailable()
        if (
            reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or reference.evidence_ref != current_bundle_ref
            or reference.evidence_ref
            not in {row.record_id for row in durable_spines}
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
        snapshot = self._cache_snapshot
        return MappingProxyType(
            {
                "lane_results": snapshot.lane_results,
                "slot_results": snapshot.slot_results,
                "divergence": snapshot.divergence,
                "bundles": snapshot.bundles,
                "current_bundles": snapshot.current_bundles,
                "reviews": snapshot.reviews,
                "d_references": snapshot.d_references,
                "g_handoffs": snapshot.g_handoffs,
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
