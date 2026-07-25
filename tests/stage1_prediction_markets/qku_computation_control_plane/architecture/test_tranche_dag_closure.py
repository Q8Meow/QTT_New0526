from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (
    DependencyGraphCompilerV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    DependencyEdgeV1,
    DependencyNodeV1,
)


def test_selected_tranche_contract_includes_upstream_closure_only() -> None:
    nodes = tuple(
        DependencyNodeV1(name, "CONTRACT", "OFFLINE")
        for name in ("models", "registry", "validation")
    )
    edges = (
        DependencyEdgeV1(
            "models", "registry", "CONTRACT", "CONTRACT", "OFFLINE"
        ),
        DependencyEdgeV1(
            "registry", "validation", "CONTRACT", "CONTRACT", "OFFLINE"
        ),
    )
    graph = DependencyGraphCompilerV1.compile(nodes, edges)
    assert graph.selected_closure(("validation",)) == (
        "models",
        "registry",
        "validation",
    )
