"""Evidence-derived contextual and stack computability."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256

from .authority import assert_no_effect_authority
from .errors import ComputationControlPlaneError, ReasonCode
from .fallback import REGISTERED_FALLBACK_RESOLVER
from .freshness import FreshnessStateV1
from .implementation_registry import IMPLEMENTATION_REGISTRY, get_math_callable
from .input_resolver import InputResolutionReceiptV1
from .models import (
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    ComputationReadinessStateV1,
    ComputabilityStateResultV1,
    ComputabilityTerminalRouteV1,
    ContextualComputabilityResolutionV1,
)
from .oracle_contracts import get_golden_vector, get_oracle
from .parameter_policy import ResolvedParameterV1
from .point_in_time import PointInTimeStateV1
from .specification import (
    FormulaExecutionContractV1,
    MATH_IO_CONTRACTS,
    TRANCHE_B_MATH_SPECIFICATIONS,
    ContextualComputabilityResolverV1,
)
from .stack_resolver import ApplicableStackResolutionReceiptV1


@dataclass(frozen=True, slots=True)
class EvidenceDerivedComputabilityReceiptV1:
    receipt_id: str
    component_id: str
    resolution: ContextualComputabilityResolutionV1
    derived_predicates: tuple[tuple[str, bool], ...]
    evidence_refs: tuple[str, ...]
    blocker_reason_codes: tuple[ReasonCode, ...]
    readiness_state: ComputationReadinessStateV1
    producer_ref: str
    consumer_refs: tuple[str, ...]
    terminal_route: str
    caller_assertion_flags_consumed: bool = False
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.caller_assertion_flags_consumed) is not bool
            or self.caller_assertion_flags_consumed
            or type(self.no_authority_flag) is not bool
            or not self.no_authority_flag
        ):
            raise ValueError(
                "evidence-derived computability cannot consume assertion flags "
                "or create authority"
            )
        if (
            not isinstance(self.derived_predicates, tuple)
            or not self.derived_predicates
            or any(
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not item[0]
                or type(item[1]) is not bool
                for item in self.derived_predicates
            )
            or len({item[0] for item in self.derived_predicates})
            != len(self.derived_predicates)
        ):
            raise ValueError("derived computability predicates must be unique typed pairs")
        if not isinstance(
            self.readiness_state,
            ComputationReadinessStateV1,
        ) or self.resolution.readiness_state is not self.readiness_state:
            raise ValueError("computability readiness must be explicitly typed")


class EvidenceDerivedContextualComputabilityResolverV1:
    """Collect typed evidence, then delegate four-state reduction to Tranche A."""

    @staticmethod
    def resolve(
        *,
        contract: FormulaExecutionContractV1,
        input_resolution: InputResolutionReceiptV1,
        parameter_resolutions: tuple[ResolvedParameterV1, ...] = (),
        stack_resolution: ApplicableStackResolutionReceiptV1 | None = None,
        consumer_refs: tuple[str, ...] = (
            "READINESS1",
            "PRETRADE1",
            "SVC1",
            "AGENT-ORCH1",
        ),
    ) -> EvidenceDerivedComputabilityReceiptV1:
        if not isinstance(contract, FormulaExecutionContractV1):
            raise ValueError("contract must be FormulaExecutionContractV1")
        if not isinstance(input_resolution, InputResolutionReceiptV1):
            raise ValueError("input resolution must be typed evidence")
        math_id = contract.canonical_formula_id_or_null
        if (
            math_id is None
            or input_resolution.component_id != math_id
            or input_resolution.parameter_policy_refs
            != contract.parameter_policy_refs
        ):
            raise ValueError("contract and input-resolution identity lineage differs")
        if (
            not isinstance(parameter_resolutions, tuple)
            or any(
                not isinstance(value, ResolvedParameterV1)
                for value in parameter_resolutions
            )
            or len(
                {
                    value.parameter_id
                    for value in parameter_resolutions
                }
            )
            != len(parameter_resolutions)
        ):
            raise ValueError(
                "parameter resolutions must be unique typed receipts"
            )
        if stack_resolution is not None and (
            not isinstance(stack_resolution, ApplicableStackResolutionReceiptV1)
            or math_id not in stack_resolution.component_ids
        ):
            raise ValueError("stack resolution does not contain the component")
        if (
            not isinstance(consumer_refs, tuple)
            or not consumer_refs
            or any(not isinstance(ref, str) or not ref for ref in consumer_refs)
            or len(set(consumer_refs)) != len(consumer_refs)
        ):
            raise ValueError("consumer refs must be a unique nonempty tuple")

        certified_specs = {
            row.math_spec_id: row for row in TRANCHE_B_MATH_SPECIFICATIONS
        }
        specification_complete = (
            math_id in certified_specs
            and math_id in MATH_IO_CONTRACTS
            and contract.typed_input_contract == MATH_IO_CONTRACTS[math_id].inputs
            and contract.typed_output_contract == MATH_IO_CONTRACTS[math_id].outputs
            and contract.specification_ref.startswith(f"SPECIFICATION::{math_id}::")
        )

        required_rows = tuple(row for row in input_resolution.inputs if row.required)
        context_bindings_exact = bool(required_rows) and all(
            row.resolved
            and row.point_in_time_receipt is not None
            and row.point_in_time_receipt.state is PointInTimeStateV1.AVAILABLE
            for row in required_rows
        )
        source_epoch_exact = bool(required_rows) and all(
            row.point_in_time_receipt is not None
            and row.point_in_time_receipt.source_epoch_id
            == contract.context_key.source_epoch_id
            for row in required_rows
        )
        units_and_basis_exact = bool(required_rows) and all(
            row.supplied_unit == row.required_unit
            and row.supplied_basis == row.required_basis
            or row.conversion_receipt is not None
            and row.conversion_receipt.required_unit == row.required_unit
            and row.conversion_receipt.required_basis == row.required_basis
            for row in required_rows
        )
        point_in_time_available = bool(required_rows) and all(
            row.point_in_time_receipt is not None
            and row.point_in_time_receipt.available
            for row in required_rows
        )
        freshness_complete = bool(required_rows) and all(
            row.freshness_receipt is not None
            and row.freshness_receipt.state is FreshnessStateV1.FRESH
            for row in required_rows
        )

        parameter_by_id = {
            value.parameter_id: value for value in parameter_resolutions
        }
        parameter_bindings_exact = (
            tuple(parameter_by_id) == contract.parameter_policy_refs
            and all(value.computable for value in parameter_resolutions)
            and input_resolution.parameter_resolution_receipt_refs
            == tuple(value.receipt_id for value in parameter_resolutions)
        )
        parameter_receipt_refs = [
            value.receipt_id for value in parameter_resolutions
        ]
        blocker_reasons: list[ReasonCode] = list(input_resolution.blocker_codes)
        for parameter_id in contract.parameter_policy_refs:
            resolved = parameter_by_id.get(parameter_id)
            if resolved is None:
                blocker_reasons.append(
                    ReasonCode.PARAMETER_RUNTIME_BINDING_REQUIRED
                )
            elif resolved.blocker_reason_code is not None:
                blocker_reasons.append(resolved.blocker_reason_code)

        implementation_registered = (
            math_id in IMPLEMENTATION_REGISTRY
            and contract.implementation_ref
            == IMPLEMENTATION_REGISTRY[math_id].contract.implementation_id
        )
        oracle = get_oracle(math_id) if implementation_registered else None
        vector = get_golden_vector(math_id) if implementation_registered else None
        oracle_vector_complete = bool(
            oracle
            and vector
            and oracle.oracle_id == contract.oracle_pack_ref
            and vector.vector_id == contract.evidence_bundle_ref
            and not oracle.production_import_allowed
            and not oracle.primary_validator_import_allowed
            and not vector.production_import_allowed
        )

        if stack_resolution is None:
            dependency_closure_complete = (
                input_resolution.computable
                and bool(contract.dependency_graph_ref)
            )
            fallback_refs = (contract.registered_fallback_ref,)
            no_orphan_consumers = bool(
                contract.consumer_refs
                and input_resolution.downstream_consumer_refs
            )
            dependency_refs = (
                contract.dependency_graph_ref,
                input_resolution.receipt_id,
            )
        else:
            dependency_closure_complete = (
                input_resolution.computable
                and stack_resolution.dependency_closure
                == stack_resolution.compiled_graph.topological_order
                and set(stack_resolution.component_ids)
                == set(stack_resolution.dependency_closure)
            )
            fallback_refs = stack_resolution.fallback_closure
            no_orphan_consumers = bool(
                stack_resolution.consumer_routes
                and set(consumer_refs) <= set(stack_resolution.consumer_routes)
            )
            dependency_refs = (
                stack_resolution.receipt_id,
                input_resolution.receipt_id,
            )
        fallback_closure_complete = True
        for fallback_ref in fallback_refs:
            try:
                REGISTERED_FALLBACK_RESOLVER.get(fallback_ref)
            except ComputationControlPlaneError as exc:
                fallback_closure_complete = False
                blocker_reasons.append(exc.reason_code)

        authority_envelope_valid = True
        try:
            assert_no_effect_authority(contract.authority_envelope)
        except ComputationControlPlaneError as exc:
            authority_envelope_valid = False
            blocker_reasons.append(exc.reason_code)

        derived = (
            ("specification_complete", specification_complete),
            ("implementation_registered", implementation_registered),
            ("oracle_vector_complete", oracle_vector_complete),
            ("context_bindings_exact", context_bindings_exact),
            ("source_epoch_exact", source_epoch_exact),
            ("units_and_basis_exact", units_and_basis_exact),
            ("parameter_bindings_exact", parameter_bindings_exact),
            ("point_in_time_available", point_in_time_available),
            ("freshness_complete", freshness_complete),
            ("dependency_closure_complete", dependency_closure_complete),
            ("fallback_closure_complete", fallback_closure_complete),
            ("no_orphan_consumers", no_orphan_consumers),
            ("authority_envelope_valid", authority_envelope_valid),
        )

        low_level = ContextualComputabilityResolverV1.resolve(
            contract,
            implementation_callable=(
                get_math_callable(math_id)
                if implementation_registered
                else None
            ),
            oracle=oracle if oracle_vector_complete else None,
            golden_vector=vector if oracle_vector_complete else None,
            context_bindings_exact=(
                specification_complete
                and context_bindings_exact
                and point_in_time_available
                and freshness_complete
            ),
            source_epoch_exact=source_epoch_exact,
            units_and_basis_exact=units_and_basis_exact,
            parameter_bindings_exact=parameter_bindings_exact,
            dependency_closure_complete=dependency_closure_complete,
            fallback_closure_complete=fallback_closure_complete,
            no_orphan_consumers=no_orphan_consumers,
            dependency_receipt_refs=dependency_refs,
            oracle_receipt_refs=(
                ()
                if not oracle_vector_complete
                else (oracle.oracle_id, vector.vector_id)
            ),
        )
        if not specification_complete:
            specification_state = ComputabilityStateResultV1(
                state=ComputabilityClassV1.SPECIFICATION_COMPUTABLE,
                computable=False,
                blocker_codes=(
                    ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE,
                ),
                dependency_receipt_refs=(),
                oracle_receipt_refs=(),
                terminal_route=(
                    ComputabilityTerminalRouteV1.SPECIFICATION_OWNER_REVIEW
                ),
            )
            stack_blockers = tuple(
                dict.fromkeys(
                    (
                        *low_level.stack.blocker_codes,
                        ComputabilityBlockerCodeV1.SPECIFICATION_SEMANTICS_INCOMPLETE,
                    )
                )
            )
            low_level = ContextualComputabilityResolutionV1(
                specification=specification_state,
                fixture=low_level.fixture,
                context=low_level.context,
                stack=ComputabilityStateResultV1(
                    state=ComputabilityClassV1.STACK_COMPUTABLE,
                    computable=False,
                    blocker_codes=stack_blockers,
                    dependency_receipt_refs=dependency_refs,
                    oracle_receipt_refs=low_level.stack.oracle_receipt_refs,
                    terminal_route=ComputabilityTerminalRouteV1.STACK_CLOSURE,
                ),
            )

        if not specification_complete:
            blocker_reasons.append(ReasonCode.INCOMPLETE_CONTRACT)
        if not implementation_registered:
            blocker_reasons.append(ReasonCode.UNKNOWN_IMPLEMENTATION)
        if not oracle_vector_complete:
            blocker_reasons.append(ReasonCode.ORACLE_NOT_INDEPENDENT)
        if not authority_envelope_valid:
            blocker_reasons.append(ReasonCode.CAPABILITY_DENIED)
        aggregate = tuple(dict.fromkeys(blocker_reasons))
        low_level = replace(
            low_level,
            readiness_state=input_resolution.source_readiness_state,
        )
        evidence_refs = tuple(
            dict.fromkeys(
                (
                    contract.specification_ref,
                    contract.implementation_ref,
                    contract.oracle_pack_ref,
                    contract.evidence_bundle_ref,
                    input_resolution.receipt_id,
                    *dependency_refs,
                    *parameter_receipt_refs,
                    *fallback_refs,
                )
            )
        )
        digest = "|".join(
            (
                math_id,
                contract.context_key.stable_key,
                *(f"{name}:{value}" for name, value in derived),
                *evidence_refs,
            )
        )
        return EvidenceDerivedComputabilityReceiptV1(
            receipt_id=(
                "COMPUTABILITY::"
                + sha256(digest.encode("utf-8")).hexdigest()
            ),
            component_id=math_id,
            resolution=low_level,
            derived_predicates=derived,
            evidence_refs=evidence_refs,
            blocker_reason_codes=aggregate,
            readiness_state=input_resolution.source_readiness_state,
            producer_ref="EvidenceDerivedContextualComputabilityResolverV1",
            consumer_refs=consumer_refs,
            terminal_route=(
                (
                    "QKUComputationControlPlaneServiceV1::"
                    "SOURCE_CONTEXT_COMPUTATION"
                )
                if low_level.stack.computable
                and input_resolution.source_readiness_state
                is ComputationReadinessStateV1.SOURCE_CONTEXT_COMPUTABLE
                else (
                    "QKUComputationControlPlaneServiceV1::"
                    "PURE_COMPUTATION_ONLY"
                )
                if low_level.stack.computable
                else "AGENT-ORCH1::TYPED_REMEDIATION_DAG"
            ),
        )
