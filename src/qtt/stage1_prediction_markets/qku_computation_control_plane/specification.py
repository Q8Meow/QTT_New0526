"""Central compiler for complete computation-contract envelopes."""

from __future__ import annotations

from dataclasses import dataclass

from .authority import CapabilityEnvelopeV1, assert_no_effect_authority
from .context import ComputationContextKeyV1
from .dependency_graph import CompiledDependencyGraphV1
from .errors import ContractValidationError, ReasonCode
from .models import (
    ComputationBindingProfileV1,
    ComputationImplementationV1,
    ComputationSpecificationV1,
    GoldenVectorV1,
    OracleContractV1,
    UnitBindingV1,
)


@dataclass(frozen=True, slots=True)
class CompiledComputationEnvelopeV1:
    specification: ComputationSpecificationV1
    implementation: ComputationImplementationV1
    binding: ComputationBindingProfileV1
    dependency_graph: CompiledDependencyGraphV1
    oracle: OracleContractV1
    golden_vector: GoldenVectorV1
    context: ComputationContextKeyV1
    authority: CapabilityEnvelopeV1


class ComputationContractCompilerV1:
    """Compile only typed, version-pinned, no-effect contracts."""

    @staticmethod
    def compile(
        *,
        qku_id: str,
        formula_id: str,
        specification_version: str,
        implementation: ComputationImplementationV1,
        binding: ComputationBindingProfileV1,
        dependency_graph: CompiledDependencyGraphV1,
        oracle: OracleContractV1,
        golden_vector: GoldenVectorV1,
        context: ComputationContextKeyV1,
        units: tuple[UnitBindingV1, ...],
        parameter_ids: tuple[str, ...] = (),
        deterministic_seed: int | None = None,
        authority: CapabilityEnvelopeV1 | None = None,
    ) -> CompiledComputationEnvelopeV1:
        typed_inputs = (
            (implementation, ComputationImplementationV1, "implementation"),
            (binding, ComputationBindingProfileV1, "binding"),
            (
                dependency_graph,
                CompiledDependencyGraphV1,
                "dependency_graph",
            ),
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
        if not isinstance(units, tuple) or any(
            not isinstance(unit, UnitBindingV1) for unit in units
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "units must be a tuple of UnitBindingV1 values",
            )
        envelope_authority = (
            authority if authority is not None else CapabilityEnvelopeV1()
        )
        assert_no_effect_authority(envelope_authority)
        context.assert_fresh()
        if implementation.math_spec_id != formula_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "implementation does not match requested formula",
            )
        if implementation.specification_version != specification_version:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "implementation and requested specification versions differ",
            )
        if oracle.math_spec_id != formula_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT, "oracle does not match requested formula"
            )
        if golden_vector.math_spec_id != formula_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "golden vector does not match requested formula",
            )
        if golden_vector.oracle_id != oracle.oracle_id:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "golden vector and oracle lineage do not match",
            )
        if implementation.seed_required and deterministic_seed is None:
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "seed-controlled implementation requires an explicit seed",
            )
        if binding.input_bindings != units:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "declared units must exactly match the binding input units",
            )
        if binding.source_bindings and context.source_epoch_id not in {
            item.effective_epoch for item in binding.source_bindings
        }:
            raise ContractValidationError(
                ReasonCode.SOURCE_EPOCH_MISSING,
                "context source epoch is absent from the source bindings",
            )
        from .parameter_policy import get_parameter_policy

        for parameter_id in parameter_ids:
            get_parameter_policy(parameter_id)
        specification = ComputationSpecificationV1(
            qku_id=qku_id,
            formula_id=formula_id,
            specification_version=specification_version,
            implementation_id=implementation.implementation_id,
            binding_id=binding.binding_id,
            oracle_id=oracle.oracle_id,
            context_key=context.stable_key,
            units=units,
            parameter_ids=parameter_ids,
            dependency_ids=dependency_graph.topological_order,
            source_epoch_ids=tuple(
                item.effective_epoch for item in binding.source_bindings
            ),
            deterministic_seed=deterministic_seed,
        )
        return CompiledComputationEnvelopeV1(
            specification=specification,
            implementation=implementation,
            binding=binding,
            dependency_graph=dependency_graph,
            oracle=oracle,
            golden_vector=golden_vector,
            context=context,
            authority=envelope_authority,
        )
