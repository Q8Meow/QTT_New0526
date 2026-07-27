import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (
    DependencyGraphCompilerV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    DependencyGraphError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    DependencyEdgeV1,
    DependencyNodeV1,
)


def test_dependency_graph_orders_closure_and_rejects_cycles() -> None:
    nodes = (
        DependencyNodeV1("a", "USD", "SNAPSHOT"),
        DependencyNodeV1("b", "USD", "SNAPSHOT"),
    )
    forward = DependencyEdgeV1("a", "b", "USD", "USD", "SNAPSHOT")
    graph = DependencyGraphCompilerV1.compile(nodes, (forward,))
    assert graph.topological_order == ("a", "b")
    assert graph.selected_closure(("b",)) == ("a", "b")
    reverse = DependencyEdgeV1("b", "a", "USD", "USD", "SNAPSHOT")
    with pytest.raises(DependencyGraphError) as caught:
        DependencyGraphCompilerV1.compile(nodes, (forward, reverse))
    assert caught.value.reason_code is ReasonCode.DEPENDENCY_CYCLE
