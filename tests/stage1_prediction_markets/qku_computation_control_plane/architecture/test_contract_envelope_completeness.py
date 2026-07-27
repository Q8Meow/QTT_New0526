from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    BindingResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (
    DependencyGraphCompilerV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    UnitBindingV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    get_golden_vector,
    get_oracle,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    CertifiedMathIdentityRefV1,
    CompiledComputationEnvelopeV1,
    ComputationContractCompilerV1,
    FormulaExecutionContractV1,
    MATH_IO_CONTRACTS,
    TypedDataContractFieldV1,
)


MANDATORY_FIELDS = (
    "canonical_component_id",
    "canonical_qku_ids",
    "canonical_formula_id_or_null",
    "canonical_algorithm_id_or_null",
    "semantic_version",
    "contract_version",
    "component_kind",
    "identity_authority_state",
    "specification_ref",
    "implementation_ref",
    "binding_profile_ref",
    "parameter_policy_refs",
    "dependency_graph_ref",
    "oracle_pack_ref",
    "evidence_bundle_ref",
    "mode_eligibility_ref",
    "registered_fallback_ref",
    "latency_class",
    "consumer_refs",
    "typed_input_contract",
    "typed_output_contract",
    "context_key",
    "authority_envelope",
)


def _compile(math_id: str) -> FormulaExecutionContractV1:
    io_contract = MATH_IO_CONTRACTS[math_id]
    binding = BindingResolverV1.build(
        binding_id=f"binding::{math_id}",
        version="1",
        inputs=tuple(
            UnitBindingV1(field.name, field.unit, field.basis)
            for field in io_contract.inputs
        ),
        sources=(),
    )
    moment = datetime(2026, 7, 24, 12, tzinfo=UTC)
    return ComputationContractCompilerV1.compile(
        identity_binding=CertifiedMathIdentityRefV1(math_id),
        implementation=IMPLEMENTATION_REGISTRY[math_id].contract,
        binding=binding,
        dependency_graph=DependencyGraphCompilerV1.compile((), ()),
        oracle=get_oracle(math_id),
        golden_vector=get_golden_vector(math_id),
        context=ComputationContextKeyV1(
            f"context::{math_id}",
            moment,
            moment,
            "source-epoch",
            "input-v1",
            timedelta(minutes=1),
        ),
        consumer_refs=(f"consumer::{math_id}",),
    )


def test_all_math_contracts_compile_to_the_one_canonical_envelope() -> None:
    assert CompiledComputationEnvelopeV1 is FormulaExecutionContractV1
    assert tuple(field.name for field in fields(FormulaExecutionContractV1)) == (
        MANDATORY_FIELDS
    )
    contracts = tuple(_compile(math_id) for math_id in IMPLEMENTATION_REGISTRY)
    assert tuple(contract.canonical_formula_id_or_null for contract in contracts) == (
        tuple(IMPLEMENTATION_REGISTRY)
    )
    for contract in contracts:
        math_id = contract.canonical_formula_id_or_null
        assert math_id is not None
        assert contract.typed_input_contract == MATH_IO_CONTRACTS[math_id].inputs
        assert contract.typed_output_contract == MATH_IO_CONTRACTS[math_id].outputs
        assert contract.canonical_qku_ids == ()
        assert not any(
            getattr(contract.authority_envelope, capability.name)
            for capability in fields(contract.authority_envelope)
        )


def test_contract_mutation_matrix_rejects_schema_and_lineage_defects() -> None:
    contract = _compile("MATH-01")
    first = contract.typed_input_contract[0]
    mutations = (
        {"typed_input_contract": contract.typed_input_contract[:-1]},
        {
            "typed_input_contract": (
                *contract.typed_input_contract,
                TypedDataContractFieldV1(
                    "extra",
                    "Decimal",
                    "scalar",
                    "currency",
                    "per_contract",
                ),
            )
        },
        {
            "typed_input_contract": (
                first,
                first,
            )
        },
        {
            "typed_input_contract": (
                replace(first, unit="fraction"),
                contract.typed_input_contract[1],
            )
        },
        {
            "typed_input_contract": (
                replace(first, basis="total"),
                contract.typed_input_contract[1],
            )
        },
        {
            "typed_input_contract": (
                replace(first, type_name="float64"),
                contract.typed_input_contract[1],
            )
        },
        {
            "typed_input_contract": (
                replace(first, shape="vector"),
                contract.typed_input_contract[1],
            )
        },
        {"semantic_version": "9.9.9"},
        {"canonical_formula_id_or_null": "MATH-02"},
        {"mode_eligibility_ref": "MODE::LIVE"},
        {"registered_fallback_ref": "FALLBACK::WRITE"},
    )
    for mutation in mutations:
        with pytest.raises(ContractValidationError):
            replace(contract, **mutation)


def test_compiler_rejects_free_form_identity_and_math_01_payout_omission() -> None:
    math_id = "MATH-01"
    io_contract = MATH_IO_CONTRACTS[math_id]
    incomplete_binding = BindingResolverV1.build(
        binding_id="binding::incomplete",
        version="1",
        inputs=(
            UnitBindingV1(
                io_contract.inputs[0].name,
                io_contract.inputs[0].unit,
                io_contract.inputs[0].basis,
            ),
        ),
        sources=(),
    )
    moment = datetime(2026, 7, 24, 12, tzinfo=UTC)
    common = {
        "implementation": IMPLEMENTATION_REGISTRY[math_id].contract,
        "binding": incomplete_binding,
        "dependency_graph": DependencyGraphCompilerV1.compile((), ()),
        "oracle": get_oracle(math_id),
        "golden_vector": get_golden_vector(math_id),
        "context": ComputationContextKeyV1(
            "context::incomplete",
            moment,
            moment,
            "source-epoch",
            "input-v1",
            timedelta(minutes=1),
        ),
    }
    with pytest.raises(ContractValidationError):
        ComputationContractCompilerV1.compile(
            identity_binding=CertifiedMathIdentityRefV1(math_id),
            **common,
        )
    with pytest.raises(ContractValidationError):
        ComputationContractCompilerV1.compile(
            identity_binding="QKU-FAKE",  # type: ignore[arg-type]
            **common,
        )
