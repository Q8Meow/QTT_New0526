"""Canonical FormulaExecutionContractV1 and orthogonal computability."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from types import MappingProxyType
from typing import Callable, Mapping

from .authority import CapabilityEnvelopeV1, assert_no_effect_authority
from .context import ComputationContextKeyV1
from .dependency_graph import CompiledDependencyGraphV1
from .errors import (
    ComputationControlPlaneError,
    ContractValidationError,
    ReasonCode,
)
from .identity_adapter import IdentityViewV1
from .models import (
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    ComputabilityStateResultV1,
    ComputabilityTerminalRouteV1,
    ComputationBindingProfileV1,
    InputOriginV1,
    ParameterApplicationTargetV1,
    ComputationImplementationV1,
    ContextualComputabilityResolutionV1,
    GoldenVectorV1,
    OracleContractV1,
)


class ComponentKindV1(StrEnum):
    FORMULA = "FORMULA"
    ALGORITHM = "ALGORITHM"


class LatencyClassV1(StrEnum):
    POINT_IN_TIME = "POINT_IN_TIME"
    SNAPSHOT = "SNAPSHOT"
    NEARLINE = "NEARLINE"
    OFFLINE = "OFFLINE"


@dataclass(frozen=True, slots=True)
class CertifiedMathIdentityRefV1:
    math_id: str
    registry_owner: str = "QKUComputationControlPlaneV1"
    registry_version: str = "ST10_FROZEN_MATH_REGISTRY_V1"

    def __post_init__(self) -> None:
        from .implementation_registry import (
            IMPLEMENTATION_REGISTRY,
            TRANCHE_A_MATH_IDS,
        )

        allowed_versions = (
            frozenset({"ST10_FROZEN_MATH_REGISTRY_V1"})
            if self.math_id in TRANCHE_A_MATH_IDS
            else frozenset(
                {
                    "ST10_FROZEN_MATH_REGISTRY_V1",
                    "ST12_TRANCHE_B_MATH_REGISTRY_V1_1R1",
                }
            )
        )
        if (
            not isinstance(self.math_id, str)
            or self.math_id not in IMPLEMENTATION_REGISTRY
            or self.registry_owner != "QKUComputationControlPlaneV1"
            or self.registry_version not in allowed_versions
        ):
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "math identity must be an exact reference to the frozen registry",
            )


@dataclass(frozen=True, slots=True)
class RP5CCanonicalIdentityBindingV1:
    identities: tuple[IdentityViewV1, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.identities, tuple)
            or not self.identities
            or any(
                not isinstance(identity, IdentityViewV1)
                for identity in self.identities
            )
            or len({identity.identity_row_id for identity in self.identities})
            != len(self.identities)
            or len({identity.library_version for identity in self.identities}) != 1
            or any(
                identity.source_owner != "RP5C_IDENTITY_LIBRARY"
                for identity in self.identities
            )
        ):
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "RP5C identity binding must contain unique verified owner views",
            )
        qku_ids = tuple(
            identity.qku_id for identity in self.identities if identity.qku_id
        )
        formula_ids = tuple(
            identity.formula_id
            for identity in self.identities
            if identity.formula_id
        )
        if len(qku_ids) != len(set(qku_ids)) or len(formula_ids) != len(
            set(formula_ids)
        ):
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "RP5C identity binding contains duplicate canonical identities",
            )

    @property
    def canonical_qku_ids(self) -> tuple[str, ...]:
        return tuple(
            identity.qku_id for identity in self.identities if identity.qku_id
        )

    @property
    def canonical_formula_ids(self) -> tuple[str, ...]:
        return tuple(
            identity.formula_id
            for identity in self.identities
            if identity.formula_id
        )


CanonicalIdentityBindingV1 = (
    CertifiedMathIdentityRefV1 | RP5CCanonicalIdentityBindingV1
)


@dataclass(frozen=True, slots=True)
class TypedDataContractFieldV1:
    name: str
    type_name: str
    shape: str
    unit: str
    basis: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (
                self.name,
                self.type_name,
                self.shape,
                self.unit,
                self.basis,
            )
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "typed data fields require exact name, type, shape, unit, and basis",
            )


@dataclass(frozen=True, slots=True)
class MathIOContractV1:
    math_id: str
    certified_name: str
    inputs: tuple[TypedDataContractFieldV1, ...]
    outputs: tuple[TypedDataContractFieldV1, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.math_id, str)
            or not self.math_id
            or not isinstance(self.certified_name, str)
            or not self.certified_name
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "math I/O identity and name are required",
            )
        for name in ("inputs", "outputs"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(
                    not isinstance(value, TypedDataContractFieldV1)
                    for value in values
                )
                or len({value.name for value in values}) != len(values)
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"math {name} must be a nonempty unique typed field tuple",
                )


def _io(
    math_id: str,
    certified_name: str,
    inputs: tuple[tuple[str, str, str, str, str], ...],
    output: tuple[str, str, str, str, str],
) -> MathIOContractV1:
    return MathIOContractV1(
        math_id,
        certified_name,
        tuple(TypedDataContractFieldV1(*value) for value in inputs),
        (TypedDataContractFieldV1(*output),),
    )


_MATH_IO_ROWS = (
    _io(
        "MATH-01",
        "BINARY_IMPLIED_PROBABILITY",
        (
            ("contract_price", "Decimal", "scalar", "currency", "per_contract"),
            (
                "payout_per_winning_contract",
                "Decimal",
                "scalar",
                "currency",
                "per_contract",
            ),
        ),
        ("p_market", "Decimal", "scalar", "probability", "unit_interval"),
    ),
    _io(
        "MATH-02",
        "PROBABILITY_EDGE",
        (
            (
                "calibrated_model_probability",
                "float64",
                "scalar",
                "probability",
                "unit_interval",
            ),
            (
                "market_implied_probability",
                "float64",
                "scalar",
                "probability",
                "unit_interval",
            ),
        ),
        (
            "edge_probability",
            "float64",
            "scalar",
            "probability_points",
            "absolute_difference",
        ),
    ),
    _io(
        "MATH-03",
        "ORDERBOOK_MIDPOINT",
        (
            ("best_bid", "Decimal", "scalar", "currency", "per_contract"),
            ("best_ask", "Decimal", "scalar", "currency", "per_contract"),
        ),
        ("mid", "Decimal", "scalar", "currency", "per_contract"),
    ),
    _io(
        "MATH-04",
        "FULL_SPREAD",
        (
            ("best_bid", "Decimal", "scalar", "currency", "per_contract"),
            ("best_ask", "Decimal", "scalar", "currency", "per_contract"),
        ),
        ("spread", "Decimal", "scalar", "currency", "per_contract"),
    ),
    _io(
        "MATH-05",
        "RELATIVE_SPREAD",
        (
            ("best_bid", "Decimal", "scalar", "currency", "per_contract"),
            ("best_ask", "Decimal", "scalar", "currency", "per_contract"),
        ),
        ("relative_spread", "Decimal", "scalar", "fraction", "dimensionless"),
    ),
    _io(
        "MATH-06",
        "BINARY_CONTRACT_EXPECTED_NET_CASH",
        (
            ("quantity", "Decimal", "scalar", "contracts", "quantity"),
            ("p", "float64", "scalar", "probability", "unit_interval"),
            ("win_cash", "Decimal", "scalar", "currency", "per_contract"),
            ("lose_cash", "Decimal", "scalar", "currency", "per_contract"),
            ("acquisition_cost", "Decimal", "scalar", "currency", "total"),
            ("fees", "Decimal", "scalar", "currency", "total"),
            ("expected_slippage", "Decimal", "scalar", "currency", "total"),
            ("expected_impact", "Decimal", "scalar", "currency", "total"),
        ),
        ("expected_net_cash", "Decimal", "scalar", "currency", "net_total"),
    ),
    _io(
        "MATH-07",
        "MULTI_OUTCOME_EXPECTED_NET_CASH",
        (
            (
                "probabilities",
                "float64",
                "vector",
                "probability",
                "unit_interval",
            ),
            ("payoffs", "Decimal", "vector", "currency", "per_contract"),
            (
                "quantity_and_friction_terms",
                "typed Decimal record",
                "record",
                "declared",
                "declared",
            ),
        ),
        ("expected_net_cash", "Decimal", "scalar", "currency", "net_total"),
    ),
    _io(
        "MATH-08",
        "BRIER_SCORE",
        (
            (
                "p",
                "float64",
                "scalar_or_vector",
                "probability",
                "unit_interval",
            ),
            ("y", "0/1", "scalar_or_one_hot_vector", "outcome", "resolved"),
        ),
        (
            "brier_score",
            "float64",
            "scalar",
            "squared_probability",
            "per_sample",
        ),
    ),
    _io(
        "MATH-09",
        "LOG_LOSS",
        (
            (
                "p",
                "active probability dtype",
                "declared",
                "probability",
                "unit_interval",
            ),
            ("y", "resolved label", "declared", "outcome", "resolved"),
        ),
        ("log_loss", "float64", "scalar", "nats", "per_sample"),
    ),
    _io(
        "MATH-10",
        "EXPECTED_CALIBRATION_ERROR",
        (
            (
                "probabilities",
                "float64",
                "vector",
                "probability",
                "unit_interval",
            ),
            ("outcomes", "binary", "vector", "outcome", "resolved"),
            (
                "bin_edges",
                "monotone float64",
                "vector",
                "probability",
                "unit_interval",
            ),
        ),
        ("ece", "float64", "scalar", "probability", "absolute_gap"),
    ),
    _io(
        "MATH-11",
        "WILSON_SCORE_INTERVAL",
        (
            ("successes", "int", "scalar", "count", "successes"),
            ("trials", "int", "scalar", "count", "trials"),
            ("confidence", "float64", "scalar", "fraction", "coverage"),
        ),
        (
            "interval",
            "[float64,float64]",
            "pair",
            "probability",
            "lower_upper",
        ),
    ),
    _io(
        "MATH-12",
        "BENJAMINI_HOCHBERG",
        (
            ("p_values", "float64", "vector", "probability", "p_value"),
            ("q", "float64", "scalar", "fraction", "FDR_target"),
        ),
        (
            "rejections_and_adjusted_p",
            "typed vector",
            "vector",
            "probability",
            "adjusted_p",
        ),
    ),
    _io(
        "MATH-13",
        "BENJAMINI_YEKUTIELI",
        (
            ("p_values", "float64", "vector", "probability", "p_value"),
            ("q", "float64", "scalar", "fraction", "FDR_target"),
        ),
        (
            "rejections_and_adjusted_p",
            "typed vector",
            "vector",
            "probability",
            "adjusted_p",
        ),
    ),
    _io(
        "MATH-14",
        "STATIONARY_BOOTSTRAP_MEAN_INTERVAL",
        (
            ("series", "float64", "vector", "declared", "observations"),
            (
                "expected_block_length",
                "float64",
                "scalar",
                "observations",
                "block_length",
            ),
        ),
        (
            "bootstrap_distribution_and_interval",
            "typed record",
            "record",
            "statistic",
            "declared_unit",
        ),
    ),
    _io(
        "MATH-15",
        "WHITE_REALITY_CHECK",
        (
            (
                "loss_differentials",
                "float64",
                "matrix[time,candidate]",
                "common_loss_basis",
                "benchmark_candidate",
            ),
        ),
        (
            "reality_check_receipt",
            "typed statistical result",
            "record",
            "probability",
            "p_value",
        ),
    ),
    _io(
        "MATH-46",
        "QUBO_UPPER_TRIANGULAR_CONVENTION",
        (
            (
                "Q",
                "float64",
                "upper_triangular_coefficient_map",
                "normalized_objective",
                "quadratic",
            ),
            (
                "c",
                "float64",
                "scalar",
                "normalized_objective",
                "offset",
            ),
        ),
        (
            "qubo_model",
            "typed coefficient model",
            "record",
            "normalized_objective",
            "upper_triangular",
        ),
    ),
    _io(
        "MATH-47",
        "QUBO_TO_ISING_TRANSFORM",
        (
            (
                "QUBO",
                "MATH-46 model",
                "record",
                "normalized_objective",
                "upper_triangular",
            ),
        ),
        (
            "ising_model",
            "h,J,offset",
            "record",
            "normalized_objective",
            "energy_equivalent",
        ),
    ),
    _io(
        "MATH-48",
        "CONSTRAINED_QUADRATIC_MODEL",
        (
            (
                "variables",
                "typed variable registry",
                "registry",
                "declared",
                "domains_and_bounds",
            ),
            (
                "objective_and_constraints",
                "typed expressions",
                "record",
                "normalized",
                "objective_and_constraints",
            ),
        ),
        (
            "cqm",
            "constrained quadratic model",
            "record",
            "normalized_objective",
            "declared_sense",
        ),
    ),
    _io(
        "MATH-49",
        "DISCRETE_QUADRATIC_MODEL",
        (
            (
                "discrete_variables",
                "case registries",
                "registry",
                "symbolic",
                "case_labels",
            ),
            (
                "biases",
                "float64 maps",
                "maps",
                "normalized_objective",
                "linear_and_pairwise",
            ),
        ),
        (
            "dqm",
            "discrete quadratic model",
            "record",
            "normalized_objective",
            "case_preserving",
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class CertifiedMathSpecificationRowV1:
    """Exact B payload row retained without minting another math registry."""

    math_spec_id: str
    name: str
    specification_version: str
    original_row_json: str

    def __post_init__(self) -> None:
        for name in (
            "math_spec_id",
            "name",
            "specification_version",
            "original_row_json",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"certified math {name} is required",
                )
        row = json.loads(self.original_row_json)
        if (
            not isinstance(row, dict)
            or row.get("math_spec_id") != self.math_spec_id
            or row.get("name") != self.name
            or row.get("specification_version") != self.specification_version
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_MATH_SPECIFICATION"
            or row.get("specification_gap_count") != 0
            or row.get("codex_online_research_allowed")
            or row.get("codex_research_required")
            or row.get("live_order_authority")
            or row.get("qpu_execution_allowed")
            or row.get("profit_or_advantage_claim_allowed")
        ):
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                f"{self.math_spec_id} is not a terminal no-effect math row",
            )


_TRANCHE_B_MATH_SPECIFICATION_ROWS_JSON = r'''
[{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-01.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"rounding":"none before display"},"deterministic_seed_policy":"FIXED_TEST_SEED_101; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require 0 <= contract_price <= payout.","Reject negative or nonfinite input."],"family":"MARKET_PROBABILITY","formal_derivation_ref":"FORMAL_DERIVATION::MATH-01","formula":"p_market = contract_price / payout_per_winning_contract","golden_vector_ref":"GOLDEN::MATH-01","implementation_algorithm":["Validate payout > 0.","Divide in Decimal context precision 34.","Return exact typed probability."],"independent_oracle_ref":"ORACLE::MATH-01","input_shapes":{"contract_price":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","payout_per_winning_contract":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"contract_price","type":"Decimal","unit":"currency/contract"},{"name":"payout_per_winning_contract","type":"Decimal","unit":"currency/contract"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Complement probability and venue payout identity","math_spec_id":"MATH-01","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"BINARY_IMPLIED_PROBABILITY","output":{"name":"p_market","type":"Decimal","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_01.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::045"],"source_identity_refs":["FORMAL_DERIVATION::MATH-01","METHOD::MATH-01::BINARY_IMPLIED_PROBABILITY","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-01","METHOD::MATH-01::BINARY_IMPLIED_PROBABILITY","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-01","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"contract_price":"currency/contract","payout_per_winning_contract":"currency/contract"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-02.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"calibration_required":true},"deterministic_seed_policy":"FIXED_TEST_SEED_201; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Each probability must be in [0,1].","Uncalibrated model probability is ineligible for order planning."],"family":"ALPHA","formal_derivation_ref":"FORMAL_DERIVATION::MATH-02","formula":"edge_probability = calibrated_model_probability - market_implied_probability","golden_vector_ref":"GOLDEN::MATH-02","implementation_algorithm":["Validate both probabilities.","Subtract without clipping.","Carry calibration and market-source receipts."],"independent_oracle_ref":"ORACLE::MATH-02","input_shapes":{"calibrated_model_probability":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","market_implied_probability":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"calibrated_model_probability","type":"float64","unit":"probability"},{"name":"market_implied_probability","type":"float64","unit":"probability"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"No-trade alternative on the same net friction basis","math_spec_id":"MATH-02","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"PROBABILITY_EDGE","output":{"name":"edge_probability","type":"float64","unit":"probability points"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_02.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":[],"source_identity_refs":["FORMAL_DERIVATION::MATH-02","METHOD::MATH-02::PROBABILITY_EDGE"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-02","METHOD::MATH-02::PROBABILITY_EDGE"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-02","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"calibrated_model_probability":"probability","market_implied_probability":"probability"},"output":"probability points"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-03.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"rounding":"no tick quantization for analytic midpoint"},"deterministic_seed_policy":"FIXED_TEST_SEED_301; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require 0 <= best_bid <= best_ask <= payout.","Reject crossed book unless explicitly typed as auction state."],"family":"MICROSTRUCTURE","formal_derivation_ref":"FORMAL_DERIVATION::MATH-03","formula":"mid = (best_bid + best_ask) / 2","golden_vector_ref":"GOLDEN::MATH-03","implementation_algorithm":["Read best levels from a sequence-valid snapshot.","Add and divide by two in Decimal.","Validate 0 <= midpoint <= payout and emit the declared currency-per-contract unit without tick quantization."],"independent_oracle_ref":"ORACLE::MATH-03","input_shapes":{"best_ask":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","best_bid":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"best_bid","type":"Decimal","unit":"currency/contract"},{"name":"best_ask","type":"Decimal","unit":"currency/contract"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Last trade and one-sided fallback are diagnostics only","math_spec_id":"MATH-03","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"ORDERBOOK_MIDPOINT","output":{"name":"mid","type":"Decimal","unit":"currency/contract"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_03.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":[],"source_identity_refs":["FORMAL_DERIVATION::MATH-03","METHOD::MATH-03::ORDERBOOK_MIDPOINT","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-03","METHOD::MATH-03::ORDERBOOK_MIDPOINT","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-03","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"best_ask":"currency/contract","best_bid":"currency/contract"},"output":"currency/contract"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-04.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{},"deterministic_seed_policy":"FIXED_TEST_SEED_401; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require ask >= bid.","No value for one-sided book unless an explicit proxy policy is bound."],"family":"MICROSTRUCTURE","formal_derivation_ref":"FORMAL_DERIVATION::MATH-04","formula":"spread = best_ask - best_bid","golden_vector_ref":"GOLDEN::MATH-04","implementation_algorithm":["Subtract in Decimal.","Preserve source tick basis.","Validate nonnegative spread on a noncrossed book, preserve the source tick basis, and emit a typed crossed-book failure otherwise."],"independent_oracle_ref":"ORACLE::MATH-04","input_shapes":{"best_ask":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","best_bid":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"best_bid","type":"Decimal","unit":"currency/contract"},{"name":"best_ask","type":"Decimal","unit":"currency/contract"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Half-spread implementation-cost component","math_spec_id":"MATH-04","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"FULL_SPREAD","output":{"name":"spread","type":"Decimal","unit":"currency/contract"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_04.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":[],"source_identity_refs":["FORMAL_DERIVATION::MATH-04","METHOD::MATH-04::FULL_SPREAD","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-04","METHOD::MATH-04::FULL_SPREAD","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-04","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"best_ask":"currency/contract","best_bid":"currency/contract"},"output":"currency/contract"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-05.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{},"deterministic_seed_policy":"FIXED_TEST_SEED_501; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require midpoint > 0.","Reject crossed or stale book."],"family":"MICROSTRUCTURE","formal_derivation_ref":"FORMAL_DERIVATION::MATH-05","formula":"relative_spread = (best_ask - best_bid) / midpoint","golden_vector_ref":"GOLDEN::MATH-05","implementation_algorithm":["Compute midpoint using MATH-03.","Divide spread by midpoint.","Reject midpoint <= 0, compute the ratio in Decimal precision 34 without implicit quantization, and validate a finite dimensionless output."],"independent_oracle_ref":"ORACLE::MATH-05","input_shapes":{"best_ask":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","best_bid":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"best_bid","type":"Decimal","unit":"currency/contract"},{"name":"best_ask","type":"Decimal","unit":"currency/contract"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Absolute spread retained in receipt","math_spec_id":"MATH-05","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"RELATIVE_SPREAD","output":{"name":"relative_spread","type":"Decimal","unit":"fraction"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_05.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":[],"source_identity_refs":["FORMAL_DERIVATION::MATH-05","METHOD::MATH-05::RELATIVE_SPREAD","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-05","METHOD::MATH-05::RELATIVE_SPREAD","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES","VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-05","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"best_ask":"currency/contract","best_bid":"currency/contract"},"output":"fraction"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-06.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"financial_context_precision":34,"rounding":"ROUND_HALF_EVEN at ledger currency scale"},"deterministic_seed_policy":"FIXED_TEST_SEED_601; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require p in [0,1], quantity >= 0 and finite cash terms.","No fee or impact omission is allowed."],"family":"EXPECTED_UTILITY","formal_derivation_ref":"FORMAL_DERIVATION::MATH-06","formula":"E_net = quantity * (p * win_cash + (1-p) * lose_cash) - acquisition_cost - fees - expected_slippage - expected_impact","golden_vector_ref":"GOLDEN::MATH-06","implementation_algorithm":["Convert p to Decimal from its canonical string representation.","Compute each term separately.","Reconcile gross minus each friction component."],"independent_oracle_ref":"ORACLE::MATH-06","input_shapes":{"acquisition_cost":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","expected_impact":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","expected_slippage":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","fees":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","lose_cash":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","p":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","quantity":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","win_cash":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"quantity","type":"Decimal","unit":"contracts"},{"name":"p","type":"float64","unit":"probability"},{"name":"win_cash","type":"Decimal","unit":"currency/contract"},{"name":"lose_cash","type":"Decimal","unit":"currency/contract"},{"name":"acquisition_cost","type":"Decimal","unit":"currency"},{"name":"fees","type":"Decimal","unit":"currency"},{"name":"expected_slippage","type":"Decimal","unit":"currency"},{"name":"expected_impact","type":"Decimal","unit":"currency"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Realized net cash and no-trade zero-exposure alternative","math_spec_id":"MATH-06","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"BINARY_CONTRACT_EXPECTED_NET_CASH","output":{"name":"expected_net_cash","type":"Decimal","unit":"currency"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_06.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":[],"source_identity_refs":["FORMAL_DERIVATION::MATH-06","METHOD::MATH-06::BINARY_CONTRACT_EXPECTED_NET_CASH"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-06","METHOD::MATH-06::BINARY_CONTRACT_EXPECTED_NET_CASH"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-06","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"acquisition_cost":"currency","expected_impact":"currency","expected_slippage":"currency","fees":"currency","lose_cash":"currency/contract","p":"probability","quantity":"contracts","win_cash":"currency/contract"},"output":"currency"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-07.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"probability_sum_tolerance":"8 * float64 machine epsilon per outcome, followed by explicit normalization receipt only if within tolerance"},"deterministic_seed_policy":"FIXED_TEST_SEED_701; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require all p_k >= 0 and sum approximately one.","Reject silent renormalization outside tolerance."],"family":"EXPECTED_UTILITY","formal_derivation_ref":"FORMAL_DERIVATION::MATH-07","formula":"E_net = quantity * sum_k p_k * payoff_k - acquisition_cost - fees - expected_slippage - expected_impact","golden_vector_ref":"GOLDEN::MATH-07","implementation_algorithm":["Validate aligned vectors.","Use compensated float summation for probability check.","Convert probabilities to canonical Decimal strings for cash multiplication."],"independent_oracle_ref":"ORACLE::MATH-07","input_shapes":{"payoffs":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","probabilities":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","quantity_and_friction_terms":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"probabilities","type":"float64 vector","unit":"probability"},{"name":"payoffs","type":"Decimal vector","unit":"currency/contract"},{"name":"quantity_and_friction_terms","type":"typed Decimal record","unit":"declared"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Outcome-by-outcome realized settlement reconciliation","math_spec_id":"MATH-07","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"MULTI_OUTCOME_EXPECTED_NET_CASH","output":{"name":"expected_net_cash","type":"Decimal","unit":"currency"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_07.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":[],"source_identity_refs":["FORMAL_DERIVATION::MATH-07","METHOD::MATH-07::MULTI_OUTCOME_EXPECTED_NET_CASH"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-07","METHOD::MATH-07::MULTI_OUTCOME_EXPECTED_NET_CASH"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-07","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"payoffs":"currency/contract","probabilities":"probability","quantity_and_friction_terms":"declared"},"output":"currency"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-08.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"aggregation":"MEAN_PER_SAMPLE","minimum_resolved_window":500},"deterministic_seed_policy":"FIXED_TEST_SEED_801; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["No unresolved outcome.","No nonfinite prediction."],"family":"PROPER_SCORING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-08","formula":"binary: BS=(p-y)^2; multiclass: BS=sum_k (p_k-y_k)^2","golden_vector_ref":"GOLDEN::MATH-08","implementation_algorithm":["Validate probability simplex.","Compute per sample.","Aggregate mean with compensated summation."],"independent_oracle_ref":"ORACLE::MATH-08","input_shapes":{"p":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","y":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"p","type":"float64 scalar or vector","unit":"probability"},{"name":"y","type":"0/1 scalar or one-hot vector","unit":"outcome"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Climatology and market-implied score on identical observations","math_spec_id":"MATH-08","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"BRIER_SCORE","output":{"name":"brier_score","type":"float64","unit":"squared probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_08.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::046"],"source_identity_refs":["FORMAL_DERIVATION::MATH-08","METHOD::MATH-08::BRIER_SCORE"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-08","METHOD::MATH-08::BRIER_SCORE"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-08","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"p":"probability","y":"outcome"},"output":"squared probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-09.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"aggregation":"MEAN_PER_SAMPLE","clip_epsilon":"machine epsilon of active probability dtype; float64 fallback 2.220446049250313e-16","minimum_resolved_window":500},"deterministic_seed_policy":"FIXED_TEST_SEED_901; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require resolved label and p in [0,1] before numeric clip.","Reject NaN or infinite output."],"family":"PROPER_SCORING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-09","formula":"binary: LL=-[y*ln(p_clip)+(1-y)*ln(1-p_clip)]; multiclass: LL=-sum_k y_k ln(p_k_clip)","golden_vector_ref":"GOLDEN::MATH-09","implementation_algorithm":["Clip only for logarithm evaluation and retain original p in receipt.","Use natural logarithm.","Aggregate per sample."],"independent_oracle_ref":"ORACLE::MATH-09","input_shapes":{"p":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","y":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"p","type":"active probability dtype","unit":"probability"},{"name":"y","type":"resolved label","unit":"outcome"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Climatology and market-implied log loss","math_spec_id":"MATH-09","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"LOG_LOSS","output":{"name":"log_loss","type":"float64","unit":"nats/sample"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_09.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::047"],"source_identity_refs":["FORMAL_DERIVATION::MATH-09","METHOD::MATH-09::LOG_LOSS"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-09","METHOD::MATH-09::LOG_LOSS"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-09","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"p":"probability","y":"outcome"},"output":"nats/sample"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-10.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"binning":"equal-frequency preferred; exact bin policy from parameter registry"},"deterministic_seed_policy":"FIXED_TEST_SEED_1001; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require N > 0 and strictly monotone edges covering [0,1].","Do not report empty-bin confidence as zero evidence."],"family":"CALIBRATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-10","formula":"ECE=sum_b (n_b/N) * abs(mean_confidence_b - empirical_frequency_b)","golden_vector_ref":"GOLDEN::MATH-10","implementation_algorithm":["Assign every sample to exactly one bin.","Compute weighted absolute gap.","Return bin counts and gaps."],"independent_oracle_ref":"ORACLE::MATH-10","input_shapes":{"bin_edges":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","outcomes":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","probabilities":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"probabilities","type":"float64 vector","unit":"probability"},{"name":"outcomes","type":"binary vector","unit":"outcome"},{"name":"bin_edges","type":"monotone float64 vector","unit":"probability"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Reliability diagram, Brier and log-loss comparators","math_spec_id":"MATH-10","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"EXPECTED_CALIBRATION_ERROR","output":{"name":"ece","type":"float64","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_10.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::048"],"source_identity_refs":["FORMAL_DERIVATION::MATH-10","METHOD::MATH-10::EXPECTED_CALIBRATION_ERROR"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-10","METHOD::MATH-10::EXPECTED_CALIBRATION_ERROR"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-10","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"bin_edges":"probability","outcomes":"outcome","probabilities":"probability"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-11.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"confidence":0.95,"z":"inverse_normal_cdf(1-(1-confidence)/2)"},"deterministic_seed_policy":"FIXED_TEST_SEED_1101; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require n > 0, 0 <= x <= n and 0 < confidence < 1."],"family":"STATISTICAL_INTERVAL","formal_derivation_ref":"FORMAL_DERIVATION::MATH-11","formula":"center=(phat+z^2/(2n))/(1+z^2/n); half=z/(1+z^2/n)*sqrt(phat(1-phat)/n+z^2/(4n^2))","golden_vector_ref":"GOLDEN::MATH-11","implementation_algorithm":["Compute phat=x/n.","Compute center and half-width.","Clip final endpoints to [0,1]."],"independent_oracle_ref":"ORACLE::MATH-11","input_shapes":{"confidence":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","successes":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","trials":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"successes","type":"int","unit":"count"},{"name":"trials","type":"int","unit":"count"},{"name":"confidence","type":"float64","unit":"fraction"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Exact binomial interval for small-n diagnostic when tractable","math_spec_id":"MATH-11","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"WILSON_SCORE_INTERVAL","output":{"name":"interval","type":"[float64,float64]","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_11.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::049"],"source_identity_refs":["FORMAL_DERIVATION::MATH-11","METHOD::MATH-11::WILSON_SCORE_INTERVAL","METHOD::ST10-SOURCE_23::WILSON_SCORE_INTERVAL"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-11","METHOD::MATH-11::WILSON_SCORE_INTERVAL","METHOD::ST10-SOURCE_23::WILSON_SCORE_INTERVAL"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-11","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"confidence":"fraction","successes":"count","trials":"count"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-12.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"q":0.05},"deterministic_seed_policy":"FIXED_TEST_SEED_1201; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require nonempty finite p-values in [0,1] and q in (0,1)."],"family":"MULTIPLE_TESTING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-12","formula":"k=max{i: p_(i) <= i*q/m}; reject ranks 1..k","golden_vector_ref":"GOLDEN::MATH-12","implementation_algorithm":["Stable-sort p-values with original indices.","Find largest admissible rank.","Compute monotone adjusted p-values backward."],"independent_oracle_ref":"ORACLE::MATH-12","input_shapes":{"p_values":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","q":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"p_values","type":"float64 vector","unit":"probability"},{"name":"q","type":"float64","unit":"FDR target"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"BY under arbitrary dependence","math_spec_id":"MATH-12","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"BENJAMINI_HOCHBERG","output":{"name":"rejections_and_adjusted_p","type":"typed vector","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_12.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::050"],"source_identity_refs":["FORMAL_DERIVATION::MATH-12","METHOD::MATH-12::BENJAMINI_HOCHBERG","METHOD::ST10-SOURCE_21::BENJAMINI_AND_HOCHBERG_FALSE_DISCOVERY_RATE"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-12","METHOD::MATH-12::BENJAMINI_HOCHBERG","METHOD::ST10-SOURCE_21::BENJAMINI_AND_HOCHBERG_FALSE_DISCOVERY_RATE"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-12","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"p_values":"probability","q":"FDR target"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-13.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"q":0.05},"deterministic_seed_policy":"FIXED_TEST_SEED_1301; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Same domain guards as BH."],"family":"MULTIPLE_TESTING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-13","formula":"c_m=sum_{j=1}^m 1/j; k=max{i: p_(i) <= i*q/(m*c_m)}","golden_vector_ref":"GOLDEN::MATH-13","implementation_algorithm":["Compute harmonic correction deterministically.","Apply BH mechanics with q/c_m.","Return correction in receipt."],"independent_oracle_ref":"ORACLE::MATH-13","input_shapes":{"p_values":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","q":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"p_values","type":"float64 vector","unit":"probability"},{"name":"q","type":"float64","unit":"FDR target"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"BH when dependence assumptions are justified","math_spec_id":"MATH-13","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"BENJAMINI_YEKUTIELI","output":{"name":"rejections_and_adjusted_p","type":"typed vector","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_13.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::051"],"source_identity_refs":["FORMAL_DERIVATION::MATH-13","METHOD::MATH-13::BENJAMINI_YEKUTIELI","METHOD::ST10-SOURCE_22::BENJAMINI_AND_YEKUTIELI_FDR_UNDER_DEPENDENCY"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-13","METHOD::MATH-13::BENJAMINI_YEKUTIELI","METHOD::ST10-SOURCE_22::BENJAMINI_AND_YEKUTIELI_FDR_UNDER_DEPENDENCY"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-13","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"p_values":"probability","q":"FDR target"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-14.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"interval":"percentile unless method-specific studentization is declared","repetitions":1000,"seed":"required explicit"},"deterministic_seed_policy":"FIXED_TEST_SEED_1401; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require series length >= 2 and 1 <= L <= series length.","Seed and block length must be recorded."],"family":"BOOTSTRAP","formal_derivation_ref":"FORMAL_DERIVATION::MATH-14","formula":"blocks have geometric length with restart probability 1/L; statistic is recomputed on each circular resample","golden_vector_ref":"GOLDEN::MATH-14","implementation_algorithm":["Draw a random start at each restart.","Continue current block with probability 1-1/L using circular index.","Recompute statistic 1000 times."],"independent_oracle_ref":"ORACLE::MATH-14","input_shapes":{"expected_block_length":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","series":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"series","type":"float64 vector","unit":"declared"},{"name":"expected_block_length","type":"float64","unit":"observations"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"IID bootstrap only as a rejected negative control for dependent series","math_spec_id":"MATH-14","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"STATIONARY_BOOTSTRAP_MEAN_INTERVAL","output":{"name":"bootstrap_distribution_and_interval","type":"typed record","unit":"statistic unit"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_14.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::052"],"source_identity_refs":["FORMAL_DERIVATION::MATH-14","METHOD::MATH-14::STATIONARY_BOOTSTRAP_MEAN_INTERVAL","METHOD::ST10-SOURCE_24::POLITIS_AND_ROMANO_STATIONARY_BOOTSTRAP"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-14","METHOD::MATH-14::STATIONARY_BOOTSTRAP_MEAN_INTERVAL","METHOD::ST10-SOURCE_24::POLITIS_AND_ROMANO_STATIONARY_BOOTSTRAP"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-14","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"expected_block_length":"observations","series":"declared"},"output":"statistic unit"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-15.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"alpha":0.05,"bootstrap":"stationary","repetitions":1000},"deterministic_seed_policy":"FIXED_TEST_SEED_1501; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require aligned finite losses and declared benchmark sign convention.","No post-hoc candidate removal."],"family":"MODEL_RISK","formal_derivation_ref":"FORMAL_DERIVATION::MATH-15","formula":"T=max_j sqrt(n)*mean(d_j); p=Pr_bootstrap(max_j sqrt(n)*(mean(d_j*)-mean(d_j)) >= T)","golden_vector_ref":"GOLDEN::MATH-15","implementation_algorithm":["Use full material candidate matrix.","Center under null.","Apply common stationary-bootstrap indices to every candidate.","Compute max-statistic p-value."],"independent_oracle_ref":"ORACLE::MATH-15","input_shapes":{"loss_differentials":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"loss_differentials","type":"float64 matrix [time,candidate]","unit":"common loss basis"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Hansen SPA and unadjusted best-candidate statistic","math_spec_id":"MATH-15","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"WHITE_REALITY_CHECK","output":{"name":"reality_check_receipt","type":"typed statistical result","unit":"p-value"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_15.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::053"],"source_identity_refs":["FORMAL_DERIVATION::MATH-15","METHOD::MATH-15::WHITE_REALITY_CHECK","METHOD::ST10-SOURCE_25::WHITE_REALITY_CHECK_FOR_DATA_SNOOPING"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-15","METHOD::MATH-15::WHITE_REALITY_CHECK","METHOD::ST10-SOURCE_25::WHITE_REALITY_CHECK_FOR_DATA_SNOOPING"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-15","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"loss_differentials":"common loss basis"},"output":"p-value"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-16.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"alpha":0.05,"bootstrap":"stationary","nested":false,"repetitions":1000,"studentize":true},"deterministic_seed_policy":"FIXED_TEST_SEED_1601; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require at least five material candidates by master-plan gate.","Reject zero or nonfinite studentization variance."],"family":"MODEL_RISK","formal_derivation_ref":"FORMAL_DERIVATION::MATH-16","formula":"studentized maximum of positive benchmark loss differentials with bootstrap null centering","golden_vector_ref":"GOLDEN::MATH-16","implementation_algorithm":["Estimate candidate-specific variance consistently.","Apply SPA null recentering.","Use common bootstrap draws.","Report statistic and p-value."],"independent_oracle_ref":"ORACLE::MATH-16","input_shapes":{"loss_differentials":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"loss_differentials","type":"float64 matrix [time,candidate]","unit":"common loss basis"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"White Reality Check","math_spec_id":"MATH-16","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"HANSEN_SPA","output":{"name":"spa_receipt","type":"typed statistical result","unit":"p-value"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_16.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::054"],"source_identity_refs":["FORMAL_DERIVATION::MATH-16","METHOD::MATH-16::HANSEN_SPA","METHOD::ST10-SOURCE_26::HANSEN_TEST_FOR_SUPERIOR_PREDICTIVE_ABILITY"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-16","METHOD::MATH-16::HANSEN_SPA","METHOD::ST10-SOURCE_26::HANSEN_TEST_FOR_SUPERIOR_PREDICTIVE_ABILITY"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-16","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"loss_differentials":"common loss basis"},"output":"p-value"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-17.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"reference_sharpe":"explicit required"},"deterministic_seed_policy":"FIXED_TEST_SEED_1701; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require n>1 and positive finite denominator.","Annualization basis must match SR_hat and SR_ref."],"family":"MODEL_RISK","formal_derivation_ref":"FORMAL_DERIVATION::MATH-17","formula":"PSR=Phi((SR_hat-SR_ref)*sqrt(n-1)/sqrt(1-gamma3*SR_hat+((gamma4-1)/4)*SR_hat^2))","golden_vector_ref":"GOLDEN::MATH-17","implementation_algorithm":["Compute denominator term.","Standardize Sharpe difference.","Apply standard normal CDF."],"independent_oracle_ref":"ORACLE::MATH-17","input_shapes":{"SR_hat":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","SR_ref":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","gamma3":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","gamma4":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","n":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"SR_hat","type":"float64","unit":"Sharpe on declared basis"},{"name":"SR_ref","type":"float64","unit":"same Sharpe basis"},{"name":"n","type":"int","unit":"independent-equivalent observations"},{"name":"gamma3","type":"float64","unit":"sample skewness"},{"name":"gamma4","type":"float64","unit":"non-excess kurtosis"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Block-bootstrap Sharpe uncertainty","math_spec_id":"MATH-17","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"PROBABILISTIC_SHARPE_RATIO","output":{"name":"psr","type":"float64","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_17.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::055"],"source_identity_refs":["FORMAL_DERIVATION::MATH-17","METHOD::MATH-17::PROBABILISTIC_SHARPE_RATIO","METHOD::ST10-SOURCE_29::BAILEY_AND_LOPEZ_DE_PRADO_THE_SHARPE_RATIO_EFFICIENT_FRONTIER"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-17","METHOD::MATH-17::PROBABILISTIC_SHARPE_RATIO","METHOD::ST10-SOURCE_29::BAILEY_AND_LOPEZ_DE_PRADO_THE_SHARPE_RATIO_EFFICIENT_FRONTIER"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-17","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"SR_hat":"Sharpe on declared basis","SR_ref":"same Sharpe basis","gamma3":"sample skewness","gamma4":"non-excess kurtosis","n":"independent-equivalent observations"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-18.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"trial_count":"EFFECTIVE_INDEPENDENT_TRIALS_IF_AVAILABLE_ELSE_MATERIAL_TRIAL_COUNT_WITH_DISCLOSURE"},"deterministic_seed_policy":"FIXED_TEST_SEED_1801; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require effective trial count >= 1 and full material trial inventory.","Never use only the winning trials."],"family":"MODEL_RISK","formal_derivation_ref":"FORMAL_DERIVATION::MATH-18","formula":"DSR=PSR(SR_hat, SR_ref=E[max Sharpe under N_eff trials]); expected-max threshold uses trial Sharpe variance and extreme-value approximation","golden_vector_ref":"GOLDEN::MATH-18","implementation_algorithm":["Estimate cross-trial Sharpe variance.","Compute expected maximum reference threshold using Euler-Mascheroni extreme-value approximation.","Call MATH-17 using that threshold."],"independent_oracle_ref":"ORACLE::MATH-18","input_shapes":{"candidate_moments":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","effective_trial_count":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","trial_sharpes":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"trial_sharpes","type":"float64 vector","unit":"common Sharpe basis"},{"name":"effective_trial_count","type":"float64","unit":"independent-equivalent trials"},{"name":"candidate_moments","type":"typed record","unit":"declared"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Raw PSR against fixed reference Sharpe","math_spec_id":"MATH-18","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"DEFLATED_SHARPE_RATIO","output":{"name":"dsr","type":"float64","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_18.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::056"],"source_identity_refs":["FORMAL_DERIVATION::MATH-18","METHOD::MATH-18::DEFLATED_SHARPE_RATIO","METHOD::ST10-SOURCE_28::BAILEY_AND_LOPEZ_DE_PRADO_DEFLATED_SHARPE_RATIO"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-18","METHOD::MATH-18::DEFLATED_SHARPE_RATIO","METHOD::ST10-SOURCE_28::BAILEY_AND_LOPEZ_DE_PRADO_DEFLATED_SHARPE_RATIO"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-18","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"candidate_moments":"declared","effective_trial_count":"independent-equivalent trials","trial_sharpes":"common Sharpe basis"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-19.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"S":16,"metric":"annualized net-after-cost Sharpe by default","partition_policy":"EQUAL_CONTIGUOUS_TIME_BLOCKS"},"deterministic_seed_policy":"FIXED_TEST_SEED_1901; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require S even, adequate observations per block and full material trial inventory.","No random subset of combinations."],"family":"MODEL_RISK","formal_derivation_ref":"FORMAL_DERIVATION::MATH-19","formula":"PBO = fraction of CSCV splits for which logit(relative OOS rank of IS winner) <= 0","golden_vector_ref":"GOLDEN::MATH-19","implementation_algorithm":["Partition time into S contiguous blocks.","Enumerate every S/2 training-block combination.","Select IS winner.","Rank its OOS performance and compute logit.","PBO is the nonpositive-logit fraction."],"independent_oracle_ref":"ORACLE::MATH-19","input_shapes":{"S":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","performance_matrix":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"performance_matrix","type":"float64 matrix [time,trial]","unit":"declared metric"},{"name":"S","type":"even int","unit":"contiguous partitions"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"DSR with effective trials","math_spec_id":"MATH-19","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"PROBABILITY_OF_BACKTEST_OVERFITTING","output":{"name":"pbo_receipt","type":"typed result","unit":"probability"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_19.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::057"],"source_identity_refs":["FORMAL_DERIVATION::MATH-19","METHOD::MATH-19::PROBABILITY_OF_BACKTEST_OVERFITTING","METHOD::ST10-SOURCE_27::BAILEY_ET_AL_PROBABILITY_OF_BACKTEST_OVERFITTING"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-19","METHOD::MATH-19::PROBABILITY_OF_BACKTEST_OVERFITTING","METHOD::ST10-SOURCE_27::BAILEY_ET_AL_PROBABILITY_OF_BACKTEST_OVERFITTING"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-19","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"S":"contiguous partitions","performance_matrix":"declared metric"},"output":"probability"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-20.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"embargo":"declared maximum look-forward horizon","folds":"resolved from parameter registry","purge":"LABEL_HORIZON_AND_EVENT_OVERLAP_DRIVEN"},"deterministic_seed_policy":"FIXED_TEST_SEED_2001; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["No arbitrary percentage embargo.","Reject missing interval metadata for overlapping labels."],"family":"VALIDATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-20","formula":"remove training samples whose information/label intervals overlap the validation interval; embargo samples inside declared post-validation look-forward horizon","golden_vector_ref":"GOLDEN::MATH-20","implementation_algorithm":["Construct validation intervals.","Purge every overlapping training interval.","Apply exact embargo after each validation interval.","Record removed indices and reasons."],"independent_oracle_ref":"ORACLE::MATH-20","input_shapes":{"embargo_horizon":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","folds":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","sample_intervals":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"sample_intervals","type":"ordered [start,end] intervals","unit":"event time"},{"name":"folds","type":"int","unit":"count"},{"name":"embargo_horizon","type":"duration","unit":"time"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Walk-forward for non-overlapping labels","math_spec_id":"MATH-20","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"PURGED_KFOLD_WITH_EMBARGO","output":{"name":"split_indices","type":"typed fold registry","unit":"indices"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_20.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::058"],"source_identity_refs":["FORMAL_DERIVATION::MATH-20","METHOD::MATH-20::PURGED_KFOLD_WITH_EMBARGO"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-20","METHOD::MATH-20::PURGED_KFOLD_WITH_EMBARGO"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-20","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"embargo_horizon":"time","folds":"count","sample_intervals":"event time"},"output":"indices"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-21.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"activation":"only when multiple backtest paths are required","path_policy":"all declared combinations"},"deterministic_seed_policy":"FIXED_TEST_SEED_2101; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require 1 <= k < N and sufficient support per path.","No cherry-picking paths."],"family":"VALIDATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-21","formula":"enumerate declared combinations of test groups; purge interval overlap and embargo each test path; aggregate path-wise results without post-hoc path selection","golden_vector_ref":"GOLDEN::MATH-21","implementation_algorithm":["Partition chronologically.","Enumerate group combinations.","Apply MATH-20 purge and embargo to each path.","Aggregate all paths with declared statistic."],"independent_oracle_ref":"ORACLE::MATH-21","input_shapes":{"N_groups":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","k_test_groups":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","sample_intervals":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"sample_intervals","type":"ordered intervals","unit":"event time"},{"name":"N_groups","type":"int","unit":"count"},{"name":"k_test_groups","type":"int","unit":"count"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Purged K-fold and walk-forward","math_spec_id":"MATH-21","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"COMBINATORIAL_PURGED_CROSS_VALIDATION","output":{"name":"cpcv_paths","type":"typed path registry","unit":"indices"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_21.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::059"],"source_identity_refs":["FORMAL_DERIVATION::MATH-21","METHOD::MATH-21::COMBINATORIAL_PURGED_CROSS_VALIDATION"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-21","METHOD::MATH-21::COMBINATORIAL_PURGED_CROSS_VALIDATION"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-21","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"N_groups":"count","k_test_groups":"count","sample_intervals":"event time"},"output":"indices"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-22.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"cross_fitting":"required","primary":true,"support_gate":"required"},"deterministic_seed_policy":"FIXED_TEST_SEED_2201; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require mu>0 wherever pi>0.","Reject unsupported target action.","Record weight distribution and effective sample size."],"family":"OFF_POLICY_EVALUATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-22","formula":"DR_i=sum_a pi(a|x_i) qhat(x_i,a) + [pi(a_i|x_i)/mu(a_i|x_i)] * [r_i-qhat(x_i,a_i)]; estimate=mean_i DR_i","golden_vector_ref":"GOLDEN::MATH-22","implementation_algorithm":["Cross-fit qhat so each row is predicted out of fold.","Compute target-policy direct term.","Add importance residual correction.","Average and bootstrap by dependence unit."],"independent_oracle_ref":"ORACLE::MATH-22","input_shapes":{"behavior_propensity":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","cross_fitted_reward_model":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","logged_context_action_reward":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","target_policy_probability":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"logged_context_action_reward","type":"typed rows","unit":"declared"},{"name":"behavior_propensity","type":"float64","unit":"probability"},{"name":"target_policy_probability","type":"float64","unit":"probability"},{"name":"cross_fitted_reward_model","type":"callable predictions","unit":"reward"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"IPS, SNIPS and SWITCH","math_spec_id":"MATH-22","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"DOUBLY_ROBUST_OFF_POLICY_EVALUATION","output":{"name":"dr_value_and_uncertainty","type":"typed result","unit":"reward"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_22.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::060"],"source_identity_refs":["FORMAL_DERIVATION::MATH-22","METHOD::MATH-22::DOUBLY_ROBUST_OFF_POLICY_EVALUATION"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-22","METHOD::MATH-22::DOUBLY_ROBUST_OFF_POLICY_EVALUATION"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-22","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"behavior_propensity":"probability","cross_fitted_reward_model":"reward","logged_context_action_reward":"declared","target_policy_probability":"probability"},"output":"reward"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-23.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"role":"mandatory comparator"},"deterministic_seed_policy":"FIXED_TEST_SEED_2301; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require positive logged propensity and support.","Any clipping must be parameterized and separately reported."],"family":"OFF_POLICY_EVALUATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-23","formula":"IPS=mean_i [pi(a_i|x_i)/mu(a_i|x_i)] r_i","golden_vector_ref":"GOLDEN::MATH-23","implementation_algorithm":["Compute exact importance weights.","Multiply observed reward.","Average and return weight diagnostics."],"independent_oracle_ref":"ORACLE::MATH-23","input_shapes":{"logged_rows":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"logged_rows","type":"typed rows","unit":"declared"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"DR and SNIPS","math_spec_id":"MATH-23","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"INVERSE_PROPENSITY_SCORE_OPE","output":{"name":"ips_value","type":"float64","unit":"reward"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_23.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::061"],"source_identity_refs":["FORMAL_DERIVATION::MATH-23","METHOD::MATH-23::INVERSE_PROPENSITY_SCORE_OPE"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-23","METHOD::MATH-23::INVERSE_PROPENSITY_SCORE_OPE"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-23","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"logged_rows":"declared"},"output":"reward"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-24.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"role":"mandatory comparator"},"deterministic_seed_policy":"FIXED_TEST_SEED_2401; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require nonnegative finite weights and positive total weight."],"family":"OFF_POLICY_EVALUATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-24","formula":"SNIPS=sum_i w_i r_i / sum_i w_i","golden_vector_ref":"GOLDEN::MATH-24","implementation_algorithm":["Compute numerator and denominator with compensated summation.","Divide and report effective sample size.","Reject a nonpositive or nonfinite normalized-weight denominator, compute effective sample size independently, and compare under the declared numerical tolerance."],"independent_oracle_ref":"ORACLE::MATH-24","input_shapes":{"rewards":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","weights":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"weights","type":"float64 vector","unit":"ratio"},{"name":"rewards","type":"float64 vector","unit":"reward"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"DR and IPS","math_spec_id":"MATH-24","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"SELF_NORMALIZED_IPS","output":{"name":"snips_value","type":"float64","unit":"reward"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_24.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::062"],"source_identity_refs":["FORMAL_DERIVATION::MATH-24","METHOD::MATH-24::SELF_NORMALIZED_IPS"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-24","METHOD::MATH-24::SELF_NORMALIZED_IPS"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-24","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"rewards":"reward","weights":"ratio"},"output":"reward"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-25.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"tau":"NO_FIXED_GUESS; deterministic nested validation over declared grid"},"deterministic_seed_policy":"FIXED_TEST_SEED_2501; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Require predeclared grid and support.","No selection on final evaluation outcomes."],"family":"OFF_POLICY_EVALUATION","formal_derivation_ref":"FORMAL_DERIVATION::MATH-25","formula":"use importance correction when w_i <= tau and direct reward-model estimate when w_i > tau; tau selected by nested offline estimated-MSE validation","golden_vector_ref":"GOLDEN::MATH-25","implementation_algorithm":["For each tau, compute nested validation bias/variance or estimated-MSE criterion.","Select minimum criterion with smallest-tau deterministic tie-break.","Refit on full outer training data and evaluate held-out data."],"independent_oracle_ref":"ORACLE::MATH-25","input_shapes":{"DR_inputs":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","tau_grid":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"DR_inputs","type":"typed OPE rows","unit":"declared"},{"name":"tau_grid","type":"ordered positive vector","unit":"importance ratio"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"DR, IPS and SNIPS","math_spec_id":"MATH-25","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"SWITCH_OPE","output":{"name":"switch_value_and_selected_tau","type":"typed result","unit":"reward"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_25.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::063"],"source_identity_refs":["FORMAL_DERIVATION::MATH-25","METHOD::MATH-25::SWITCH_OPE"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-25","METHOD::MATH-25::SWITCH_OPE"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-25","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"DR_inputs":"declared","tau_grid":"importance ratio"},"output":"reward"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-36.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"level_order":"ascending, best is last"},"deterministic_seed_policy":"FIXED_TEST_SEED_3601; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Reject missing payout basis, invalid levels or sequence-stale book."],"family":"PROVIDER_MARKET_DATA","formal_derivation_ref":"FORMAL_DERIVATION::MATH-36","formula":"for unit payout, implied opposite ask = 1 - opposite_side_best_bid; generalized ask = payout - opposite_bid","golden_vector_ref":"GOLDEN::MATH-36","implementation_algorithm":["Parse both ladders.","Take highest bid as last level.","Derive opposite ask only when payout identity is verified.","Record derivation provenance."],"independent_oracle_ref":"ORACLE::MATH-36","input_shapes":{"no_bids":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","payout":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","yes_bids":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"yes_bids","type":"Decimal levels","unit":"currency"},{"name":"no_bids","type":"Decimal levels","unit":"currency"},{"name":"payout","type":"Decimal","unit":"currency"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Direct executable ask if future provider schema supplies it","math_spec_id":"MATH-36","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"KALSHI_BINARY_BOOK_TRANSFORM","output":{"name":"derived_yes_and_no_touches","type":"typed Decimal record","unit":"currency"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_36.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::074"],"source_identity_refs":["FORMAL_DERIVATION::MATH-36","METHOD::MATH-36::KALSHI_BINARY_BOOK_TRANSFORM","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-36","METHOD::MATH-36::KALSHI_BINARY_BOOK_TRANSFORM","VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-36","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"no_bids":"currency","payout":"currency","yes_bids":"currency"},"output":"currency"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-46.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"diagonal_representation":"linear binary terms stored on diagonal"},"deterministic_seed_policy":"FIXED_TEST_SEED_4601; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["All coefficients finite.","Original objective and scaling receipt required."],"family":"QUANTUM_MAPPING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-46","formula":"E(x)=c + sum_i Q_ii x_i + sum_{i<j} Q_ij x_i x_j, x_i in {0,1}","golden_vector_ref":"GOLDEN::MATH-46","implementation_algorithm":["Canonicalize each unordered pair to i<j.","Sum duplicate coefficients deterministically.","Drop only exact zeros after declared scaling."],"independent_oracle_ref":"ORACLE::MATH-46","input_shapes":{"Q":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","c":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"Q","type":"float64 upper-triangular coefficient map","unit":"normalized objective"},{"name":"c","type":"float64","unit":"same"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Direct original-objective recomputation","math_spec_id":"MATH-46","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"QUBO_UPPER_TRIANGULAR_CONVENTION","output":{"name":"qubo_model","type":"typed coefficient model","unit":"normalized objective"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_46.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::081"],"source_identity_refs":["FORMAL_DERIVATION::MATH-46","LIBRARY::DWAVE_OCEAN_9_4_0","METHOD::MATH-46::QUBO_UPPER_TRIANGULAR_CONVENTION"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-46","LIBRARY::DWAVE_OCEAN_9_4_0","METHOD::MATH-46::QUBO_UPPER_TRIANGULAR_CONVENTION"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-46","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"Q":"normalized objective","c":"same"},"output":"normalized objective"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-47.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"spin_domain":"{-1,+1}"},"deterministic_seed_policy":"FIXED_TEST_SEED_4701; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Energy parity tolerance must be derived from coefficient scale and float precision.","No sign-convention ambiguity."],"family":"QUANTUM_MAPPING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-47","formula":"x_i=(1-s_i)/2; h_i=-Q_ii/2-sum_{j!=i}Q_min(i,j),max(i,j)/4; J_ij=Q_ij/4; offset=c+sum_i Q_ii/2+sum_{i<j}Q_ij/4","golden_vector_ref":"GOLDEN::MATH-47","implementation_algorithm":["Apply coefficient formulas exactly.","Enumerate all assignments for small fixture problems.","For larger cases, verify random assignment parity with deterministic seed."],"independent_oracle_ref":"ORACLE::MATH-47","input_shapes":{"QUBO":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"QUBO","type":"MATH-46 model","unit":"normalized objective"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"QUBO energy on interpreted binary assignment","math_spec_id":"MATH-47","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"QUBO_TO_ISING_TRANSFORM","output":{"name":"ising_model","type":"h,J,offset","unit":"same objective"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_47.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::082"],"source_identity_refs":["FORMAL_DERIVATION::MATH-47","LIBRARY::QISKIT_OPTIMIZATION_0_7_0","METHOD::MATH-47::QUBO_TO_ISING_TRANSFORM"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-47","LIBRARY::QISKIT_OPTIMIZATION_0_7_0","METHOD::MATH-47::QUBO_TO_ISING_TRANSFORM"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-47","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"QUBO":"normalized objective"},"output":"same objective"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-48.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"constraint_route":"native CQM when semantics and backend support it; otherwise explicit proven conversion"},"deterministic_seed_policy":"FIXED_TEST_SEED_4801; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Reject unsupported real-variable quadratic terms or hidden constraints.","Feasibility recheck mandatory."],"family":"QUANTUM_MAPPING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-48","formula":"min/max declared quadratic objective subject to explicit linear/quadratic constraints over binary, integer and supported real variables","golden_vector_ref":"GOLDEN::MATH-48","implementation_algorithm":["Create variables with exact bounds.","Add objective.","Add each named constraint with sense and RHS.","Persist label crosswalk."],"independent_oracle_ref":"ORACLE::MATH-48","input_shapes":{"objective_and_constraints":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","variables":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"variables","type":"typed variable registry","unit":"declared"},{"name":"objective_and_constraints","type":"typed expressions","unit":"normalized"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"Classical MILP/MIQP on identical formulation","math_spec_id":"MATH-48","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"CONSTRAINED_QUADRATIC_MODEL","output":{"name":"cqm","type":"constrained quadratic model","unit":"normalized objective"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_48.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::083"],"source_identity_refs":["FORMAL_DERIVATION::MATH-48","LIBRARY::DWAVE_OCEAN_9_4_0","METHOD::MATH-48::CONSTRAINED_QUADRATIC_MODEL"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-48","LIBRARY::DWAVE_OCEAN_9_4_0","METHOD::MATH-48::CONSTRAINED_QUADRATIC_MODEL"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-48","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"objective_and_constraints":"normalized","variables":"declared"},"output":"normalized objective"}},{"allowed_lane":"REPLAY_PAPER_AND_OFFLINE_ONLY","assumptions":["All inputs satisfy the declared domain for MATH-49.","All time-varying inputs are point-in-time and version-pinned.","No provider, private-state, order, or QPU effect is implied by this specification."],"boundary_behavior":"USE_EXPLICIT_CLOSED_OR_OPEN_DOMAIN_BOUNDARIES_FROM_GUARDS; REJECT_OUT_OF_DOMAIN; DO_NOT_CLIP_UNLESS_FORMULA_EXPLICITLY_REQUIRES_CLIPPING","certified_input_origin":"STEP12_RESEARCH_COMPLETE_IMPLEMENTATION_SPEC_RETAINED_AND_REVALIDATED","codex_online_research_allowed":false,"codex_research_required":false,"day1_defaults":{"use":"multi-case categorical decisions"},"deterministic_seed_policy":"FIXED_TEST_SEED_4901; RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC","domain_and_fail_closed_guards":["Reject duplicate cases, unknown interactions or silent one-hot expansion."],"family":"QUANTUM_MAPPING","formal_derivation_ref":"FORMAL_DERIVATION::MATH-49","formula":"one discrete variable selects exactly one case; linear and pairwise case biases define energy without manual one-hot penalty","golden_vector_ref":"GOLDEN::MATH-49","implementation_algorithm":["Create each variable with ordered cases.","Assign linear case biases and pairwise case interactions.","Persist interpret-back map."],"independent_oracle_ref":"ORACLE::MATH-49","input_shapes":{"biases":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE","discrete_variables":"SCALAR_OR_EXPLICITLY_DECLARED_SEQUENCE"},"inputs":[{"name":"discrete_variables","type":"case registries","unit":"symbolic"},{"name":"biases","type":"float64 maps","unit":"normalized objective"}],"live_order_authority":false,"mandatory_comparator_or_reconciliation":"One-hot QUBO with proved penalty and classical enumeration for small fixtures","math_spec_id":"MATH-49","missing_stale_invalid_nonfinite_behavior":"REJECT_WITH_TYPED_REASON; NEVER_COERCE_MISSING_STALE_NAN_INFINITY_OR_INVALID_DOMAIN_TO_ZERO","name":"DISCRETE_QUADRATIC_MODEL","output":{"name":"dqm","type":"discrete quadratic model","unit":"normalized objective"},"output_shape":"SCALAR_OR_EXPLICITLY_DECLARED_STRUCTURE","owner_authorization_required_before_implementation":true,"precision_and_rounding_policy":"DECIMAL_CONTEXT_PRECISION_34_ROUND_HALF_EVEN_AT_FINANCIAL_BOUNDARIES; FLOAT64_ONLY_WHERE_METHOD_REQUIRES_WITH_DECLARED_TOLERANCE; NO_IMPLICIT_QUANTIZATION","production_implementation_target":"src/qtt/stage1_prediction_markets/qku_computation_control_plane/math/math_49.py","profit_or_advantage_claim_allowed":false,"qpu_execution_allowed":false,"registered_classical_fallback":"SAME_FORMULATION_DETERMINISTIC_REFERENCE_OR_NO_TRADE","research_completeness_state":"COMPLETE_TERMINAL_MATH_SPECIFICATION","semantic_status":"COMPLETE_RESEARCHED_IMPLEMENTATION_SPECIFICATION","source_claim_binding_rule_refs":["ST12-SOURCE-RULE::084"],"source_identity_refs":["FORMAL_DERIVATION::MATH-49","LIBRARY::DWAVE_OCEAN_9_4_0","METHOD::MATH-49::DISCRETE_QUADRATIC_MODEL"],"source_ref_resolution":"RESOLVE_THROUGH_STEP12_SOURCE_REF_CROSSWALK","source_refs":["FORMAL_DERIVATION::MATH-49","LIBRARY::DWAVE_OCEAN_9_4_0","METHOD::MATH-49::DISCRETE_QUADRATIC_MODEL"],"specification_gap_count":0,"specification_version":"1.1R1","state_and_time_semantics":"PURE_ON_VERSION_PINNED_INPUT_SNAPSHOT; NO_FUTURE_DATA; STATEFUL_METHODS_REQUIRE_DECLARED_SEED_SPLIT_OR_LEDGER_INPUT","template_id":"MATH-49","tie_break_policy":"STABLE_INPUT_ORDER_THEN_CANONICAL_ID_ASCENDING_UNLESS_METHOD_DECLARES_STRONGER_RULE","unit_and_basis_contract":{"basis":"EXACT_FORMULA_DECLARED_BASIS_NO_HIDDEN_GROSS_NET_OR_TIME_CONVERSION","inputs":{"biases":"normalized objective","discrete_variables":"symbolic"},"output":"normalized objective"}}]
'''


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _load_tranche_b_math_rows() -> tuple[dict[str, object], ...]:
    rows = json.loads(_TRANCHE_B_MATH_SPECIFICATION_ROWS_JSON)
    if (
        not isinstance(rows, list)
        or len(rows) != 30
        or any(not isinstance(row, dict) for row in rows)
        or len({str(row["math_spec_id"]) for row in rows}) != 30
    ):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            "Tranche-B math payload must contain 30 unique rows",
        )
    return tuple(rows)


_TRANCHE_B_MATH_ROWS = _load_tranche_b_math_rows()
TRANCHE_B_MATH_SPECIFICATIONS = tuple(
    CertifiedMathSpecificationRowV1(
        math_spec_id=str(row["math_spec_id"]),
        name=str(row["name"]),
        specification_version=str(row["specification_version"]),
        original_row_json=_canonical_json(row),
    )
    for row in _TRANCHE_B_MATH_ROWS
)


def _certified_io(row: dict[str, object]) -> MathIOContractV1:
    inputs = row["inputs"]
    if isinstance(inputs, dict):
        input_rows = (inputs,)
    elif isinstance(inputs, list) and inputs:
        input_rows = tuple(inputs)
    else:
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{row['math_spec_id']} inputs are malformed",
        )
    shapes = row["input_shapes"]
    units = row["unit_and_basis_contract"]
    output = row["output"]
    if (
        not isinstance(shapes, dict)
        or not isinstance(units, dict)
        or not isinstance(units.get("inputs"), dict)
        or not isinstance(output, dict)
    ):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{row['math_spec_id']} I/O semantics are malformed",
        )
    basis = str(units["basis"])
    typed_inputs = tuple(
        TypedDataContractFieldV1(
            name=str(item["name"]),
            type_name=str(item["type"]),
            shape=str(shapes[str(item["name"])]),
            unit=str(units["inputs"][str(item["name"])]),
            basis=basis,
        )
        for item in input_rows
        if isinstance(item, dict)
    )
    if len(typed_inputs) != len(input_rows):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{row['math_spec_id']} input rows are malformed",
        )
    typed_output = TypedDataContractFieldV1(
        name=str(output["name"]),
        type_name=str(output["type"]),
        shape=str(row["output_shape"]),
        unit=str(output["unit"]),
        basis=basis,
    )
    return MathIOContractV1(
        math_id=str(row["math_spec_id"]),
        certified_name=str(row["name"]),
        inputs=typed_inputs,
        outputs=(typed_output,),
    )


_EXISTING_MATH_IO_IDS = frozenset(row.math_id for row in _MATH_IO_ROWS)
_MATH_IO_ROWS = _MATH_IO_ROWS + tuple(
    _certified_io(row)
    for row in _TRANCHE_B_MATH_ROWS
    if str(row["math_spec_id"]) not in _EXISTING_MATH_IO_IDS
)
_MATH_IO_ROWS = tuple(
    sorted(_MATH_IO_ROWS, key=lambda row: int(row.math_id.split("-")[1]))
)
MATH_IO_CONTRACTS: Mapping[str, MathIOContractV1] = MappingProxyType(
    {row.math_id: row for row in _MATH_IO_ROWS}
)
if (
    len(MATH_IO_CONTRACTS) != len(_MATH_IO_ROWS)
    or len(MATH_IO_CONTRACTS) != 30
    or len(TRANCHE_B_MATH_SPECIFICATIONS) != 30
):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "math I/O identities must be unique",
    )


class RequirementResolutionStateV1(StrEnum):
    EXACT_REQUIREMENTS = "EXACT_REQUIREMENTS"
    EXPLICITLY_CERTIFIED_EMPTY_REQUIREMENTS = (
        "EXPLICITLY_CERTIFIED_EMPTY_REQUIREMENTS"
    )
    UNRESOLVED_REQUIREMENTS_FAIL_CLOSED = (
        "UNRESOLVED_REQUIREMENTS_FAIL_CLOSED"
    )


@dataclass(frozen=True, slots=True)
class ParameterApplicationBindingV1:
    parameter_policy_id: str
    primary_target: ParameterApplicationTargetV1
    secondary_validation_targets: tuple[ParameterApplicationTargetV1, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.parameter_policy_id, str) or not self.parameter_policy_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "parameter application requires an exact policy identity",
            )
        if not isinstance(self.primary_target, ParameterApplicationTargetV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "parameter application target must be typed",
            )
        if (
            not isinstance(self.secondary_validation_targets, tuple)
            or any(
                not isinstance(value, ParameterApplicationTargetV1)
                for value in self.secondary_validation_targets
            )
            or len(set(self.secondary_validation_targets))
            != len(self.secondary_validation_targets)
            or self.primary_target
            is ParameterApplicationTargetV1.RECEIPT_ONLY_NONMATERIAL
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_APPLICATION_UNBOUND,
                "material parameter applications must be exact and behavioral",
            )


@dataclass(frozen=True, slots=True)
class ExecutionControlBindingV1:
    control_name: str
    owner_rule_ref: str
    required_from_caller: bool
    fixed_default: str | None
    caller_override_allowed: bool
    application_target: ParameterApplicationTargetV1 = (
        ParameterApplicationTargetV1.EXECUTION_CONTROL
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.control_name, str)
            or not self.control_name
            or not isinstance(self.owner_rule_ref, str)
            or not self.owner_rule_ref
            or type(self.required_from_caller) is not bool
            or type(self.caller_override_allowed) is not bool
            or not isinstance(self.application_target, ParameterApplicationTargetV1)
            or self.application_target
            is not ParameterApplicationTargetV1.EXECUTION_CONTROL
            or (
                self.fixed_default is not None
                and (
                    not isinstance(self.fixed_default, str)
                    or not self.fixed_default
                )
            )
            or (self.required_from_caller and self.fixed_default is not None)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "execution-control ownership must be exact and non-conflicting",
            )


@dataclass(frozen=True, slots=True)
class ComponentExecutionRequirementV1:
    canonical_component_id: str
    certified_math_id: str
    per_input_accepted_origin_classes: tuple[
        tuple[str, tuple[InputOriginV1, ...]], ...
    ]
    per_input_source_claim_binding_rule_refs: tuple[
        tuple[str, tuple[str, ...]], ...
    ]
    source_claim_binding_rule_refs: tuple[str, ...]
    required_parameter_policy_ids: tuple[str, ...]
    parameter_application_bindings: tuple[ParameterApplicationBindingV1, ...]
    execution_control_bindings: tuple[ExecutionControlBindingV1, ...]
    allowed_computation_modes: tuple[str, ...]
    consumer_scope: tuple[str, ...]
    registered_failure_fallback_route: str
    terminal_requirement_resolution_state: RequirementResolutionStateV1
    terminal_resolution_evidence_refs: tuple[str, ...]
    missing_owner_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "canonical_component_id",
            "certified_math_id",
            "registered_failure_fallback_route",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"component requirement {name} is required",
                )
        if not isinstance(
            self.terminal_requirement_resolution_state,
            RequirementResolutionStateV1,
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "component requirement resolution state must be typed",
            )
        if (
            not isinstance(self.per_input_accepted_origin_classes, tuple)
            or not self.per_input_accepted_origin_classes
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or not isinstance(item[1], tuple)
                or not item[1]
                or any(not isinstance(origin, InputOriginV1) for origin in item[1])
                or len(set(item[1])) != len(item[1])
                for item in self.per_input_accepted_origin_classes
            )
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "per-input origins must be exact typed tuples",
            )
        input_names = tuple(
            item[0] for item in self.per_input_accepted_origin_classes
        )
        if len(set(input_names)) != len(input_names):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "component requirement input identities must be unique",
            )
        source_input_names = tuple(
            item[0] for item in self.per_input_source_claim_binding_rule_refs
        )
        if (
            not isinstance(
                self.per_input_source_claim_binding_rule_refs,
                tuple,
            )
            or source_input_names != input_names
            or any(
                not isinstance(item[1], tuple)
                or any(not isinstance(ref, str) or not ref for ref in item[1])
                or len(set(item[1])) != len(item[1])
                for item in self.per_input_source_claim_binding_rule_refs
            )
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "per-input source rules must align exactly with input origins",
            )
        for name in (
            "source_claim_binding_rule_refs",
            "required_parameter_policy_ids",
            "allowed_computation_modes",
            "consumer_scope",
            "terminal_resolution_evidence_refs",
            "missing_owner_refs",
        ):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or any(not isinstance(value, str) or not value for value in values)
                or len(set(values)) != len(values)
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a unique immutable text tuple",
                )
        application_ids = tuple(
            item.parameter_policy_id
            for item in self.parameter_application_bindings
        )
        unresolved = (
            self.terminal_requirement_resolution_state
            is RequirementResolutionStateV1.UNRESOLVED_REQUIREMENTS_FAIL_CLOSED
        )
        if (
            not isinstance(self.parameter_application_bindings, tuple)
            or any(
                not isinstance(item, ParameterApplicationBindingV1)
                for item in self.parameter_application_bindings
            )
            or len(set(application_ids)) != len(application_ids)
            or (
                not unresolved
                and application_ids != self.required_parameter_policy_ids
            )
            or (
                unresolved
                and not set(application_ids)
                <= set(self.required_parameter_policy_ids)
            )
        ):
            raise ContractValidationError(
                ReasonCode.PARAMETER_APPLICATION_UNBOUND,
                "required parameters need one ordered primary application",
            )
        if (
            not isinstance(self.execution_control_bindings, tuple)
            or any(
                not isinstance(item, ExecutionControlBindingV1)
                for item in self.execution_control_bindings
            )
            or len(
                {
                    item.control_name
                    for item in self.execution_control_bindings
                }
            )
            != len(self.execution_control_bindings)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "execution-control bindings must be unique typed rows",
            )
        if unresolved != bool(self.missing_owner_refs):
            raise ContractValidationError(
                ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED,
                "unresolved requirements must name their exact missing owner refs",
            )
        if (
            self.terminal_requirement_resolution_state
            is RequirementResolutionStateV1.EXPLICITLY_CERTIFIED_EMPTY_REQUIREMENTS
            and (
                self.required_parameter_policy_ids
                or any(
                    refs
                    for _, refs in self.per_input_source_claim_binding_rule_refs
                )
            )
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "explicitly empty runtime requirements cannot contain bindings",
            )

    def accepted_origins_for(self, input_field_id: str) -> tuple[InputOriginV1, ...]:
        try:
            return dict(self.per_input_accepted_origin_classes)[input_field_id]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.REQUIRED_INPUT_MISSING,
                f"unknown requirement input: {input_field_id}",
            ) from exc

    def source_rules_for(self, input_field_id: str) -> tuple[str, ...]:
        try:
            return dict(self.per_input_source_claim_binding_rule_refs)[
                input_field_id
            ]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.SOURCE_BINDING_REQUIRED,
                f"unknown source-requirement input: {input_field_id}",
            ) from exc


_EXACT_EXTERNAL_SOURCE_RULE_REFS: Mapping[str, tuple[str, str]] = (
    MappingProxyType(
        {
            "VENUE::ST10-SOURCE_02::KALSHI_ORDERBOOK_RESPONSES": (
                "ST12-SOURCE-RULE::002",
                "ST10-SOURCE::02",
            ),
            "VENUE::ST10-SOURCE_07::POLYMARKET_GLOBAL_GET_ORDER_BOOK": (
                "ST12-SOURCE-RULE::007",
                "ST10-SOURCE::07",
            ),
        }
    )
)
_EXACT_METHOD_SOURCE_RULE_REFS: Mapping[str, tuple[str, str]] = (
    MappingProxyType(
        {
            "METHOD::ST10-SOURCE_21::BENJAMINI_AND_HOCHBERG_FALSE_DISCOVERY_RATE": (
                "ST12-SOURCE-RULE::021",
                "ST10-SOURCE::21",
            ),
            "METHOD::ST10-SOURCE_22::BENJAMINI_AND_YEKUTIELI_FDR_UNDER_DEPENDENCY": (
                "ST12-SOURCE-RULE::022",
                "ST10-SOURCE::22",
            ),
            "METHOD::ST10-SOURCE_23::WILSON_SCORE_INTERVAL": (
                "ST12-SOURCE-RULE::023",
                "ST10-SOURCE::23",
            ),
            "METHOD::ST10-SOURCE_24::POLITIS_AND_ROMANO_STATIONARY_BOOTSTRAP": (
                "ST12-SOURCE-RULE::024",
                "ST10-SOURCE::24",
            ),
            "METHOD::ST10-SOURCE_25::WHITE_REALITY_CHECK_FOR_DATA_SNOOPING": (
                "ST12-SOURCE-RULE::025",
                "ST10-SOURCE::25",
            ),
            "METHOD::ST10-SOURCE_26::HANSEN_TEST_FOR_SUPERIOR_PREDICTIVE_ABILITY": (
                "ST12-SOURCE-RULE::026",
                "ST10-SOURCE::26",
            ),
            "METHOD::ST10-SOURCE_27::BAILEY_ET_AL_PROBABILITY_OF_BACKTEST_OVERFITTING": (
                "ST12-SOURCE-RULE::027",
                "ST10-SOURCE::27",
            ),
            "METHOD::ST10-SOURCE_28::BAILEY_AND_LOPEZ_DE_PRADO_DEFLATED_SHARPE_RATIO": (
                "ST12-SOURCE-RULE::028",
                "ST10-SOURCE::28",
            ),
            "METHOD::ST10-SOURCE_29::BAILEY_AND_LOPEZ_DE_PRADO_THE_SHARPE_RATIO_EFFICIENT_FRONTIER": (
                "ST12-SOURCE-RULE::029",
                "ST10-SOURCE::29",
            ),
        }
    )
)
_MATERIAL_PARAMETER_APPLICATIONS: Mapping[
    str,
    tuple[
        ParameterApplicationTargetV1,
        tuple[ParameterApplicationTargetV1, ...],
    ],
] = MappingProxyType(
    {
        "ST10-PARAM::2212": (
            ParameterApplicationTargetV1.PRE_CALL_ADMISSION_GUARD,
            (ParameterApplicationTargetV1.POST_CALL_OUTPUT_VALIDATOR,),
        ),
        "ST10-PARAM::2213": (
            ParameterApplicationTargetV1.PRE_CALL_ADMISSION_GUARD,
            (ParameterApplicationTargetV1.POST_CALL_OUTPUT_VALIDATOR,),
        ),
    }
)


def _execution_control_bindings(
    row: dict[str, object],
) -> tuple[ExecutionControlBindingV1, ...]:
    math_id = str(row["math_spec_id"])
    seed_policy = str(row["deterministic_seed_policy"])
    defaults = row["day1_defaults"]
    if not isinstance(defaults, dict):
        raise ContractValidationError(
            ReasonCode.OWNER_DATA_MALFORMED,
            f"{math_id} day-one defaults must be an exact object",
        )
    controls: list[ExecutionControlBindingV1] = []
    if (
        math_id in {"MATH-14", "MATH-15", "MATH-16"}
        and "RUNTIME_SEED_EXPLICIT_IN_RECEIPT_WHEN_STOCHASTIC"
        in seed_policy
    ):
        controls.append(
            ExecutionControlBindingV1(
                control_name="seed",
                owner_rule_ref=f"{math_id}::deterministic_seed_policy",
                required_from_caller=True,
                fixed_default=None,
                caller_override_allowed=True,
            )
        )
    repetitions = defaults.get("repetitions")
    if isinstance(repetitions, int) and not isinstance(repetitions, bool):
        controls.append(
            ExecutionControlBindingV1(
                control_name="replicates",
                owner_rule_ref=f"{math_id}::day1_defaults.repetitions",
                required_from_caller=False,
                fixed_default=str(repetitions),
                caller_override_allowed=False,
            )
        )
    alpha = defaults.get("alpha")
    if isinstance(alpha, int | float) and not isinstance(alpha, bool):
        controls.append(
            ExecutionControlBindingV1(
                control_name="alpha",
                owner_rule_ref=f"{math_id}::day1_defaults.alpha",
                required_from_caller=False,
                fixed_default=str(alpha),
                caller_override_allowed=False,
            )
        )
    return tuple(controls)


def _build_component_execution_requirements(
) -> tuple[ComponentExecutionRequirementV1, ...]:
    from .bindings import get_source_claim_binding_rule
    from .parameter_policy import (
        TRANCHE_B_PARAMETER_POLICIES,
        get_parameter_policy,
    )

    requirements: list[ComponentExecutionRequirementV1] = []
    for row in _TRANCHE_B_MATH_ROWS:
        math_id = str(row["math_spec_id"])
        name = str(row["name"])
        io_contract = MATH_IO_CONTRACTS[math_id]
        source_identities = tuple(str(value) for value in row["source_identity_refs"])
        external_rule_refs: list[str] = []
        lineage_rule_refs: list[str] = []
        missing: list[str] = []
        exact_nonexternal_identities = {
            str(row["formal_derivation_ref"]),
            f"METHOD::{math_id}::{name}",
            "LIBRARY::DWAVE_OCEAN_9_4_0",
            "LIBRARY::QISKIT_OPTIMIZATION_0_7_0",
        }
        for source_identity in source_identities:
            if source_identity in _EXACT_EXTERNAL_SOURCE_RULE_REFS:
                external_rule_refs.append(
                    _EXACT_EXTERNAL_SOURCE_RULE_REFS[source_identity][0]
                )
            elif source_identity in _EXACT_METHOD_SOURCE_RULE_REFS:
                lineage_rule_refs.append(
                    _EXACT_METHOD_SOURCE_RULE_REFS[source_identity][0]
                )
            elif source_identity not in exact_nonexternal_identities:
                missing.append(f"SOURCE_REF_CROSSWALK::{source_identity}")
        external_rules = tuple(dict.fromkeys(external_rule_refs))
        declared_rules = tuple(
            str(value) for value in row["source_claim_binding_rule_refs"]
        )
        all_source_rules = tuple(
            dict.fromkeys(
                (*declared_rules, *lineage_rule_refs, *external_rules)
            )
        )
        origins: list[tuple[str, tuple[InputOriginV1, ...]]] = []
        source_rules_by_input: list[tuple[str, tuple[str, ...]]] = []
        for field in io_contract.inputs:
            accepted: list[InputOriginV1] = []
            if external_rules:
                accepted.append(InputOriginV1.CANONICAL_SOURCE_STATE)
            if (
                math_id == "MATH-02"
                and field.name == "market_implied_probability"
            ):
                accepted.append(InputOriginV1.IN_PROCESS_DERIVED_VALUE)
            accepted.append(
                InputOriginV1.OWNER_SUPPLIED_PURE_COMPUTATION_INPUT
            )
            origins.append((field.name, tuple(accepted)))
            source_rules_by_input.append((field.name, external_rules))

        formal_ref = str(row["formal_derivation_ref"])
        parameter_ids = tuple(
            sorted(
                policy.parameter_id
                for policy in TRANCHE_B_PARAMETER_POLICIES
                if formal_ref in policy.effective_source_state_refs
            )
        )
        applications: list[ParameterApplicationBindingV1] = []
        for parameter_id in parameter_ids:
            application = _MATERIAL_PARAMETER_APPLICATIONS.get(parameter_id)
            if application is None:
                missing.append(f"PARAMETER_APPLICATION::{parameter_id}")
                continue
            primary, secondary = application
            applications.append(
                ParameterApplicationBindingV1(
                    parameter_policy_id=parameter_id,
                    primary_target=primary,
                    secondary_validation_targets=secondary,
                )
            )
        for rule_id in all_source_rules:
            try:
                rule = get_source_claim_binding_rule(rule_id)
            except ComputationControlPlaneError:
                missing.append(f"SOURCE_CLAIM_RULE::{rule_id}")
            else:
                if rule.math_spec_ref is not None and rule.math_spec_ref != math_id:
                    missing.append(
                        f"SOURCE_CLAIM_CONSUMER::{rule_id}::{math_id}"
                    )
        for parameter_id in parameter_ids:
            try:
                get_parameter_policy(parameter_id)
            except ComputationControlPlaneError:
                missing.append(f"PARAMETER_POLICY::{parameter_id}")

        if missing:
            state = (
                RequirementResolutionStateV1.UNRESOLVED_REQUIREMENTS_FAIL_CLOSED
            )
        elif external_rules or parameter_ids or any(
            InputOriginV1.IN_PROCESS_DERIVED_VALUE in accepted
            for _, accepted in origins
        ):
            state = RequirementResolutionStateV1.EXACT_REQUIREMENTS
        else:
            state = (
                RequirementResolutionStateV1.EXPLICITLY_CERTIFIED_EMPTY_REQUIREMENTS
            )
        requirements.append(
            ComponentExecutionRequirementV1(
                canonical_component_id=f"{math_id}::{name}",
                certified_math_id=math_id,
                per_input_accepted_origin_classes=tuple(origins),
                per_input_source_claim_binding_rule_refs=tuple(
                    source_rules_by_input
                ),
                source_claim_binding_rule_refs=all_source_rules,
                required_parameter_policy_ids=parameter_ids,
                parameter_application_bindings=tuple(applications),
                execution_control_bindings=_execution_control_bindings(row),
                allowed_computation_modes=(
                    "CONTRACT_ONLY",
                    "REPLAY",
                    "PAPER",
                ),
                consumer_scope=(
                    "QKUComputationControlPlaneServiceV1",
                    "READINESS1",
                    "PRETRADE1",
                    "SVC1",
                    "AGENT-ORCH1",
                ),
                registered_failure_fallback_route=(
                    "FALLBACK::NO_EFFECT_FAIL_CLOSED"
                ),
                terminal_requirement_resolution_state=state,
                terminal_resolution_evidence_refs=(
                    formal_ref,
                    (
                        f"CERTIFIED_RUNTIME_REQUIREMENTS::{math_id}"
                        if state
                        is RequirementResolutionStateV1.EXACT_REQUIREMENTS
                        else (
                            f"CERTIFIED_EMPTY_REQUIREMENTS::{math_id}"
                            if state
                            is RequirementResolutionStateV1.EXPLICITLY_CERTIFIED_EMPTY_REQUIREMENTS
                            else f"UNRESOLVED_REQUIREMENTS::{math_id}"
                        )
                    ),
                ),
                missing_owner_refs=tuple(dict.fromkeys(missing)),
            )
        )
    return tuple(requirements)


COMPONENT_EXECUTION_REQUIREMENTS = _build_component_execution_requirements()
COMPONENT_EXECUTION_REQUIREMENT_BY_MATH_ID: Mapping[
    str, ComponentExecutionRequirementV1
] = MappingProxyType(
    {
        requirement.certified_math_id: requirement
        for requirement in COMPONENT_EXECUTION_REQUIREMENTS
    }
)
if (
    len(COMPONENT_EXECUTION_REQUIREMENTS) != 30
    or len(COMPONENT_EXECUTION_REQUIREMENT_BY_MATH_ID) != 30
    or len(
        {
            requirement.canonical_component_id
            for requirement in COMPONENT_EXECUTION_REQUIREMENTS
        }
    )
    != 30
    or set(COMPONENT_EXECUTION_REQUIREMENT_BY_MATH_ID)
    != {row.math_spec_id for row in TRANCHE_B_MATH_SPECIFICATIONS}
    or any(
        tuple(
            field.name
            for field in MATH_IO_CONTRACTS[
                requirement.certified_math_id
            ].inputs
        )
        != tuple(
            field_name
            for field_name, _ in requirement.per_input_accepted_origin_classes
        )
        for requirement in COMPONENT_EXECUTION_REQUIREMENTS
    )
):
    raise ContractValidationError(
        ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED,
        "component execution requirements must cover the exact 30-row universe",
    )


def get_component_execution_requirement(
    canonical_component_id: str,
) -> ComponentExecutionRequirementV1:
    if not isinstance(canonical_component_id, str) or not canonical_component_id:
        raise ContractValidationError(
            ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED,
            "component requirement identity must be nonempty text",
        )
    direct = COMPONENT_EXECUTION_REQUIREMENT_BY_MATH_ID.get(
        canonical_component_id
    )
    if direct is not None:
        return direct
    exact = tuple(
        requirement
        for requirement in COMPONENT_EXECUTION_REQUIREMENTS
        if requirement.canonical_component_id == canonical_component_id
    )
    if len(exact) != 1:
        raise ContractValidationError(
            ReasonCode.EXECUTION_REQUIREMENTS_UNRESOLVED,
            f"unknown component execution requirement: {canonical_component_id}",
        )
    return exact[0]


@dataclass(frozen=True, slots=True)
class FormulaExecutionContractV1:
    canonical_component_id: str
    canonical_qku_ids: tuple[str, ...]
    canonical_formula_id_or_null: str | None
    canonical_algorithm_id_or_null: str | None
    semantic_version: str
    contract_version: str
    component_kind: ComponentKindV1
    identity_authority_state: CanonicalIdentityBindingV1
    specification_ref: str
    implementation_ref: str
    binding_profile_ref: str
    parameter_policy_refs: tuple[str, ...]
    dependency_graph_ref: str
    oracle_pack_ref: str
    evidence_bundle_ref: str
    mode_eligibility_ref: str
    registered_fallback_ref: str
    latency_class: LatencyClassV1
    consumer_refs: tuple[str, ...]
    typed_input_contract: tuple[TypedDataContractFieldV1, ...]
    typed_output_contract: tuple[TypedDataContractFieldV1, ...]
    context_key: ComputationContextKeyV1
    authority_envelope: CapabilityEnvelopeV1

    def __post_init__(self) -> None:
        for name in (
            "canonical_component_id",
            "semantic_version",
            "contract_version",
            "specification_ref",
            "implementation_ref",
            "binding_profile_ref",
            "dependency_graph_ref",
            "oracle_pack_ref",
            "evidence_bundle_ref",
            "mode_eligibility_ref",
            "registered_fallback_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.INCOMPLETE_CONTRACT,
                    f"{name} is required",
                )
        if (
            not isinstance(self.canonical_qku_ids, tuple)
            or any(
                not isinstance(value, str) or not value
                for value in self.canonical_qku_ids
            )
            or len(set(self.canonical_qku_ids)) != len(self.canonical_qku_ids)
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "canonical_qku_ids must be a unique typed tuple",
            )
        if (
            self.canonical_formula_id_or_null is None
        ) == (
            self.canonical_algorithm_id_or_null is None
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "exactly one canonical formula or algorithm identity is required",
            )
        for name in (
            "canonical_formula_id_or_null",
            "canonical_algorithm_id_or_null",
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be nonempty text when present",
                )
        if not isinstance(self.component_kind, ComponentKindV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "component_kind must be typed",
            )
        if not isinstance(
            self.identity_authority_state,
            CertifiedMathIdentityRefV1 | RP5CCanonicalIdentityBindingV1,
        ):
            raise ContractValidationError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "identity_authority_state must be a typed canonical binding",
            )
        if self.contract_version != "1.0.0":
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "FormulaExecutionContractV1 contract_version must be 1.0.0",
            )
        if (
            self.mode_eligibility_ref != "MODE::CONTRACT_ONLY"
            or self.registered_fallback_ref
            != "FALLBACK::NO_EFFECT_FAIL_CLOSED"
        ):
            raise ContractValidationError(
                ReasonCode.CAPABILITY_DENIED,
                "formula contracts require exact no-effect mode and fallback refs",
            )
        for name in ("parameter_policy_refs", "consumer_refs"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or (name == "consumer_refs" and not values)
                or any(
                    not isinstance(value, str) or not value for value in values
                )
                or len(set(values)) != len(values)
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a unique typed tuple",
                )
        for name in ("typed_input_contract", "typed_output_contract"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or any(
                    not isinstance(value, TypedDataContractFieldV1)
                    for value in values
                )
                or len({value.name for value in values}) != len(values)
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a complete unique typed schema",
                )
        if not isinstance(self.context_key, ComputationContextKeyV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "context_key must be a typed ComputationContextKeyV1",
            )
        if not isinstance(self.authority_envelope, CapabilityEnvelopeV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "authority_envelope must be typed",
            )
        assert_no_effect_authority(self.authority_envelope)
        if not isinstance(self.latency_class, LatencyClassV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "latency_class must be typed",
            )
        from .implementation_registry import IMPLEMENTATION_REGISTRY
        from .oracle_contracts import GOLDEN_VECTOR_BY_MATH_ID, ORACLE_BY_MATH_ID
        from .parameter_policy import get_parameter_policy

        for parameter_id in self.parameter_policy_refs:
            get_parameter_policy(parameter_id)
        if isinstance(self.identity_authority_state, CertifiedMathIdentityRefV1):
            math_id = self.identity_authority_state.math_id
            implementation = IMPLEMENTATION_REGISTRY[math_id]
            io_contract = MATH_IO_CONTRACTS[math_id]
            if (
                self.canonical_qku_ids
                or self.canonical_formula_id_or_null != math_id
                or self.canonical_algorithm_id_or_null is not None
                or self.component_kind is not ComponentKindV1.FORMULA
                or self.canonical_component_id
                != f"{math_id}::{implementation.name}"
                or self.semantic_version
                != implementation.contract.specification_version
                or self.specification_ref
                != f"SPECIFICATION::{math_id}::{self.semantic_version}"
                or self.implementation_ref
                != implementation.contract.implementation_id
                or self.oracle_pack_ref != ORACLE_BY_MATH_ID[math_id].oracle_id
                or self.evidence_bundle_ref
                != GOLDEN_VECTOR_BY_MATH_ID[math_id].vector_id
                or self.typed_input_contract != io_contract.inputs
                or self.typed_output_contract != io_contract.outputs
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    "math contract identity, version, or I/O lineage is inconsistent",
                )
        else:
            if (
                self.canonical_qku_ids
                != self.identity_authority_state.canonical_qku_ids
                or self.canonical_formula_id_or_null
                not in self.identity_authority_state.canonical_formula_ids
            ):
                raise ContractValidationError(
                    ReasonCode.OWNER_DATA_CONTRADICTORY,
                    "RP5C contract identity does not equal the verified owner views",
                )


# The historical name is an alias to the same canonical class, not an envelope owner.
CompiledComputationEnvelopeV1 = FormulaExecutionContractV1


def _dependency_graph_ref(graph: CompiledDependencyGraphV1) -> str:
    ordered = ",".join(graph.topological_order) if graph.topological_order else "EMPTY"
    return f"DEPENDENCY_GRAPH::{ordered}"


def _latency_class(graph: CompiledDependencyGraphV1) -> LatencyClassV1:
    order = {
        "POINT_IN_TIME": 0,
        "SNAPSHOT": 1,
        "NEARLINE": 2,
        "OFFLINE": 3,
    }
    value = max(
        (node.timing_class for node in graph.nodes),
        key=lambda item: order[item],
        default="OFFLINE",
    )
    return LatencyClassV1(value)


class ComputationContractCompilerV1:
    """Compile one canonical, version-pinned, no-effect formula contract."""

    @staticmethod
    def compile(
        *,
        identity_binding: CanonicalIdentityBindingV1,
        implementation: ComputationImplementationV1,
        binding: ComputationBindingProfileV1,
        dependency_graph: CompiledDependencyGraphV1,
        oracle: OracleContractV1,
        golden_vector: GoldenVectorV1,
        context: ComputationContextKeyV1,
        parameter_ids: tuple[str, ...] = (),
        consumer_refs: tuple[str, ...] = ("QKUComputationControlPlaneV1",),
        authority: CapabilityEnvelopeV1 | None = None,
    ) -> FormulaExecutionContractV1:
        if not isinstance(identity_binding, CertifiedMathIdentityRefV1):
            raise ContractValidationError(
                ReasonCode.UNKNOWN_IMPLEMENTATION,
                "RP5C identity is verified but has no certified math implementation binding",
            )
        typed_inputs = (
            (implementation, ComputationImplementationV1, "implementation"),
            (binding, ComputationBindingProfileV1, "binding"),
            (dependency_graph, CompiledDependencyGraphV1, "dependency_graph"),
            (oracle, OracleContractV1, "oracle"),
            (golden_vector, GoldenVectorV1, "golden_vector"),
            (context, ComputationContextKeyV1, "context"),
        )
        for value, expected_type, field_name in typed_inputs:
            if not isinstance(value, expected_type):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{field_name} must be a typed {expected_type.__name__}",
                )
        from .implementation_registry import IMPLEMENTATION_REGISTRY
        from .parameter_policy import get_parameter_policy

        math_id = identity_binding.math_id
        registered = IMPLEMENTATION_REGISTRY[math_id]
        io_contract = MATH_IO_CONTRACTS[math_id]
        if (
            implementation != registered.contract
            or oracle.math_spec_id != math_id
            or golden_vector.math_spec_id != math_id
            or golden_vector.oracle_id != oracle.oracle_id
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "implementation, oracle, vector, or deterministic-seed lineage differs",
            )
        expected_bindings = tuple(
            (field.name, field.unit, field.basis)
            for field in io_contract.inputs
        )
        actual_bindings = tuple(
            (field.field_name, field.unit, field.basis)
            for field in binding.input_bindings
        )
        if actual_bindings != expected_bindings:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "binding fields, units, and bases must exactly equal the math contract",
            )
        if binding.source_bindings and context.source_epoch_id not in {
            source.effective_epoch for source in binding.source_bindings
        }:
            raise ContractValidationError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "context source epoch is absent from the source bindings",
            )
        for parameter_id in parameter_ids:
            get_parameter_policy(parameter_id)
        envelope_authority = authority or CapabilityEnvelopeV1()
        assert_no_effect_authority(envelope_authority)
        return FormulaExecutionContractV1(
            canonical_component_id=f"{math_id}::{registered.name}",
            canonical_qku_ids=(),
            canonical_formula_id_or_null=math_id,
            canonical_algorithm_id_or_null=None,
            semantic_version=implementation.specification_version,
            contract_version="1.0.0",
            component_kind=ComponentKindV1.FORMULA,
            identity_authority_state=identity_binding,
            specification_ref=(
                f"SPECIFICATION::{math_id}::{implementation.specification_version}"
            ),
            implementation_ref=implementation.implementation_id,
            binding_profile_ref=f"{binding.binding_id}@{binding.version}",
            parameter_policy_refs=parameter_ids,
            dependency_graph_ref=_dependency_graph_ref(dependency_graph),
            oracle_pack_ref=oracle.oracle_id,
            evidence_bundle_ref=golden_vector.vector_id,
            mode_eligibility_ref="MODE::CONTRACT_ONLY",
            registered_fallback_ref="FALLBACK::NO_EFFECT_FAIL_CLOSED",
            latency_class=_latency_class(dependency_graph),
            consumer_refs=consumer_refs,
            typed_input_contract=io_contract.inputs,
            typed_output_contract=io_contract.outputs,
            context_key=context,
            authority_envelope=envelope_authority,
        )


class ContextualComputabilityResolverV1:
    """Resolve four orthogonal states without creating any authority."""

    @staticmethod
    def resolve(
        contract: FormulaExecutionContractV1,
        *,
        implementation_callable: Callable[..., object] | None,
        oracle: OracleContractV1 | None,
        golden_vector: GoldenVectorV1 | None,
        context_bindings_exact: bool,
        source_epoch_exact: bool,
        units_and_basis_exact: bool,
        parameter_bindings_exact: bool,
        dependency_closure_complete: bool,
        fallback_closure_complete: bool,
        no_orphan_consumers: bool,
        dependency_receipt_refs: tuple[str, ...] = (),
        oracle_receipt_refs: tuple[str, ...] = (),
    ) -> ContextualComputabilityResolutionV1:
        if not isinstance(contract, FormulaExecutionContractV1):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "computability requires FormulaExecutionContractV1",
            )
        flags = (
            context_bindings_exact,
            source_epoch_exact,
            units_and_basis_exact,
            parameter_bindings_exact,
            dependency_closure_complete,
            fallback_closure_complete,
            no_orphan_consumers,
        )
        if any(type(value) is not bool for value in flags):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "computability evidence flags must be exact booleans",
            )
        for name, values in (
            ("dependency_receipt_refs", dependency_receipt_refs),
            ("oracle_receipt_refs", oracle_receipt_refs),
        ):
            if (
                not isinstance(values, tuple)
                or any(
                    not isinstance(value, str) or not value for value in values
                )
                or len(values) != len(set(values))
            ):
                raise ContractValidationError(
                    ReasonCode.INVALID_CONTRACT,
                    f"{name} must be a unique immutable string tuple",
                )
        from .implementation_registry import get_math_callable
        from .oracle_contracts import get_golden_vector, get_oracle

        math_id = contract.canonical_formula_id_or_null
        assert math_id is not None
        specification = ComputabilityStateResultV1(
            ComputabilityClassV1.SPECIFICATION_COMPUTABLE,
            True,
            (),
            (),
            (),
            ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION,
        )
        fixture_blockers: list[ComputabilityBlockerCodeV1] = []
        if implementation_callable is not get_math_callable(math_id):
            fixture_blockers.append(
                ComputabilityBlockerCodeV1.IMPLEMENTATION_CALLABLE_MISSING
            )
        if oracle != get_oracle(math_id) or oracle.production_import_allowed:
            fixture_blockers.append(
                ComputabilityBlockerCodeV1.INDEPENDENT_ORACLE_MISSING
            )
        if (
            golden_vector != get_golden_vector(math_id)
            or golden_vector.production_import_allowed
        ):
            fixture_blockers.append(
                ComputabilityBlockerCodeV1.INDEPENDENT_VECTOR_MISSING
            )
        fixture = ComputabilityStateResultV1(
            ComputabilityClassV1.FIXTURE_COMPUTABLE,
            not fixture_blockers,
            tuple(fixture_blockers),
            (),
            oracle_receipt_refs,
            (
                ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
                if not fixture_blockers
                else ComputabilityTerminalRouteV1.FIXTURE_MATERIALIZATION
            ),
        )
        context_blockers: list[ComputabilityBlockerCodeV1] = []
        if not context_bindings_exact:
            context_blockers.append(
                ComputabilityBlockerCodeV1.CONTEXT_BINDING_MISMATCH
            )
        if not source_epoch_exact:
            context_blockers.append(
                ComputabilityBlockerCodeV1.SOURCE_EPOCH_MISMATCH
            )
        if not units_and_basis_exact:
            context_blockers.append(
                ComputabilityBlockerCodeV1.UNIT_OR_BASIS_MISMATCH
            )
        if not parameter_bindings_exact:
            context_blockers.append(
                ComputabilityBlockerCodeV1.PARAMETER_BINDING_MISMATCH
            )
        try:
            contract.context_key.assert_fresh()
        except ContractValidationError as exc:
            if exc.reason_code is not ReasonCode.STALE_CONTEXT:
                raise
            context_blockers.append(ComputabilityBlockerCodeV1.CONTEXT_STALE)
        try:
            assert_no_effect_authority(contract.authority_envelope)
        except ContractValidationError:
            context_blockers.append(
                ComputabilityBlockerCodeV1.AUTHORITY_ENVELOPE_INVALID
            )
        context_state = ComputabilityStateResultV1(
            ComputabilityClassV1.CONTEXT_COMPUTABLE,
            not context_blockers,
            tuple(context_blockers),
            dependency_receipt_refs,
            (),
            (
                ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
                if not context_blockers
                else ComputabilityTerminalRouteV1.CONTEXT_REBINDING
            ),
        )
        stack_blockers: list[ComputabilityBlockerCodeV1] = []
        if not dependency_closure_complete:
            stack_blockers.append(
                ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE
            )
        if not fallback_closure_complete:
            stack_blockers.append(
                ComputabilityBlockerCodeV1.FALLBACK_CLOSURE_INCOMPLETE
            )
        if not no_orphan_consumers:
            stack_blockers.append(ComputabilityBlockerCodeV1.ORPHAN_CONSUMER)
        if not context_state.computable:
            stack_blockers.extend(
                blocker
                for blocker in context_state.blocker_codes
                if blocker not in stack_blockers
            )
        if not specification.computable:
            stack_blockers.append(
                ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE
            )
        if not fixture.computable:
            stack_blockers.extend(
                blocker
                for blocker in fixture.blocker_codes
                if blocker not in stack_blockers
            )
        stack = ComputabilityStateResultV1(
            ComputabilityClassV1.STACK_COMPUTABLE,
            not stack_blockers,
            tuple(stack_blockers),
            dependency_receipt_refs,
            oracle_receipt_refs,
            (
                ComputabilityTerminalRouteV1.CONTRACT_ONLY_COMPUTATION
                if not stack_blockers
                else ComputabilityTerminalRouteV1.STACK_CLOSURE
            ),
        )
        return ContextualComputabilityResolutionV1(
            specification,
            fixture,
            context_state,
            stack,
        )
