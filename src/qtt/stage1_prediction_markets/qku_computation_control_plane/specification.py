"""Canonical FormulaExecutionContractV1 and orthogonal computability."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Callable, Mapping

from .authority import CapabilityEnvelopeV1, assert_no_effect_authority
from .context import ComputationContextKeyV1
from .dependency_graph import CompiledDependencyGraphV1
from .errors import ContractValidationError, ReasonCode
from .identity_adapter import IdentityViewV1
from .models import (
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    ComputabilityStateResultV1,
    ComputabilityTerminalRouteV1,
    ComputationBindingProfileV1,
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
        from .implementation_registry import IMPLEMENTATION_REGISTRY

        if (
            not isinstance(self.math_id, str)
            or self.math_id not in IMPLEMENTATION_REGISTRY
            or self.registry_owner != "QKUComputationControlPlaneV1"
            or self.registry_version != "ST10_FROZEN_MATH_REGISTRY_V1"
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

MATH_IO_CONTRACTS: Mapping[str, MathIOContractV1] = MappingProxyType(
    {row.math_id: row for row in _MATH_IO_ROWS}
)
if len(MATH_IO_CONTRACTS) != len(_MATH_IO_ROWS):
    raise ContractValidationError(
        ReasonCode.INVALID_CONTRACT,
        "math I/O identities must be unique",
    )


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
