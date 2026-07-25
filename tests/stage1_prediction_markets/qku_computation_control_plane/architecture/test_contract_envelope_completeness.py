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
    get_math_implementation,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    DependencyNodeV1,
    UnitBindingV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    get_golden_vector,
    get_oracle,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    ComputationContractCompilerV1,
)


def test_complete_typed_contract_envelope_compiles() -> None:
    unit = UnitBindingV1("contract_price", "USD", "PER_CONTRACT")
    binding = BindingResolverV1.build(
        binding_id="binding-v1",
        version="1",
        inputs=(unit,),
        sources=(),
    )
    graph = DependencyGraphCompilerV1.compile(
        (DependencyNodeV1("price", "USD", "SNAPSHOT"),),
        (),
    )
    moment = datetime(2026, 7, 24, 12, tzinfo=UTC)
    context = ComputationContextKeyV1(
        "ctx",
        moment,
        moment,
        "source-epoch",
        "input-v1",
        timedelta(minutes=1),
    )
    envelope = ComputationContractCompilerV1.compile(
        qku_id="QKU-TEST",
        formula_id="MATH-01",
        specification_version="1.1R1",
        implementation=get_math_implementation("MATH-01").contract,
        binding=binding,
        dependency_graph=graph,
        oracle=get_oracle("MATH-01"),
        golden_vector=get_golden_vector("MATH-01"),
        context=context,
        units=(unit,),
    )
    assert envelope.specification.formula_id == "MATH-01"
    assert envelope.specification.dependency_ids == ("price",)
    assert not envelope.authority.provider_connection_allowed
