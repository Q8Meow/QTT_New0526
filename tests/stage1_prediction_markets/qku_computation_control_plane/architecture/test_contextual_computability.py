from datetime import UTC, datetime, timedelta

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    BindingResolverV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    ComputationContextKeyV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (
    DependencyGraphCompilerV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    get_math_callable,
    get_math_implementation,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    ComputabilityBlockerCodeV1,
    ComputabilityClassV1,
    UnitBindingV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    get_golden_vector,
    get_oracle,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    CertifiedMathIdentityRefV1,
    ComputationContractCompilerV1,
    ContextualComputabilityResolverV1,
    MATH_IO_CONTRACTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    OPERATION_SCHEMA_REGISTRY,
)


def _contract(*, stale: bool = False):
    math_id = "MATH-01"
    moment = datetime(2026, 7, 24, 12, tzinfo=UTC)
    observed = moment - timedelta(hours=1) if stale else moment
    io_contract = MATH_IO_CONTRACTS[math_id]
    return ComputationContractCompilerV1.compile(
        identity_binding=CertifiedMathIdentityRefV1(math_id),
        implementation=get_math_implementation(math_id).contract,
        binding=BindingResolverV1.build(
            binding_id="binding::computability",
            version="1",
            inputs=tuple(
                UnitBindingV1(field.name, field.unit, field.basis)
                for field in io_contract.inputs
            ),
            sources=(),
        ),
        dependency_graph=DependencyGraphCompilerV1.compile((), ()),
        oracle=get_oracle(math_id),
        golden_vector=get_golden_vector(math_id),
        context=ComputationContextKeyV1(
            "context::computability",
            moment,
            observed,
            "source-epoch",
            "input-v1",
            timedelta(minutes=5),
        ),
    )


def _resolve(contract, **overrides):
    values = {
        "implementation_callable": get_math_callable("MATH-01"),
        "oracle": get_oracle("MATH-01"),
        "golden_vector": get_golden_vector("MATH-01"),
        "context_bindings_exact": True,
        "source_epoch_exact": True,
        "units_and_basis_exact": True,
        "parameter_bindings_exact": True,
        "dependency_closure_complete": True,
        "fallback_closure_complete": True,
        "no_orphan_consumers": True,
        "dependency_receipt_refs": ("dependency::closed",),
        "oracle_receipt_refs": ("oracle::verified",),
    }
    values.update(overrides)
    return ContextualComputabilityResolverV1.resolve(contract, **values)


def test_four_computability_states_are_independent_and_no_authority() -> None:
    resolution = _resolve(_contract())
    states = (
        resolution.specification,
        resolution.fixture,
        resolution.context,
        resolution.stack,
    )
    assert tuple(state.state for state in states) == tuple(ComputabilityClassV1)
    assert all(state.computable for state in states)
    assert all(state.no_authority_flag for state in states)
    assert all(not state.blocker_codes for state in states)
    assert resolution.fixture.oracle_receipt_refs == ("oracle::verified",)
    assert resolution.stack.dependency_receipt_refs == ("dependency::closed",)
    assert (
        OPERATION_SCHEMA_REGISTRY["ST10-OP::02"].resolver_name
        == "ContextualComputabilityResolverV1.resolve"
    )


def test_stale_context_blocks_context_and_stack_only() -> None:
    resolution = _resolve(_contract(stale=True))
    assert resolution.specification.computable
    assert resolution.fixture.computable
    assert not resolution.context.computable
    assert not resolution.stack.computable
    assert resolution.context.blocker_codes == (
        ComputabilityBlockerCodeV1.CONTEXT_STALE,
    )
    assert ComputabilityBlockerCodeV1.CONTEXT_STALE in (
        resolution.stack.blocker_codes
    )


def test_fixture_and_stack_failures_do_not_rewrite_other_states() -> None:
    missing_fixture = _resolve(_contract(), implementation_callable=None)
    assert missing_fixture.specification.computable
    assert not missing_fixture.fixture.computable
    assert missing_fixture.context.computable
    assert not missing_fixture.stack.computable
    assert (
        ComputabilityBlockerCodeV1.IMPLEMENTATION_CALLABLE_MISSING
        in missing_fixture.fixture.blocker_codes
    )

    open_stack = _resolve(
        _contract(),
        dependency_closure_complete=False,
        fallback_closure_complete=False,
        no_orphan_consumers=False,
    )
    assert open_stack.specification.computable
    assert open_stack.fixture.computable
    assert open_stack.context.computable
    assert not open_stack.stack.computable
    assert open_stack.stack.blocker_codes == (
        ComputabilityBlockerCodeV1.DEPENDENCY_CLOSURE_INCOMPLETE,
        ComputabilityBlockerCodeV1.FALLBACK_CLOSURE_INCOMPLETE,
        ComputabilityBlockerCodeV1.ORPHAN_CONSUMER,
    )
