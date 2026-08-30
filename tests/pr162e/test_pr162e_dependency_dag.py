import pytest

from src.qtt.plugins.contracts import (
    PluginPackageContractError,
    PluginPackageReasonCodeV1,
)
from src.qtt.plugins.dag import (
    compile_selected_package_dependency_order_v1,
    has_cycle,
    topological_order,
)
from src.qtt.plugins.registry import build_selected_component_package_manifest_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    stage1_launch_graph_projection_v2,
)
from tests.pr162e.helpers import records


def test_dependency_dag_is_acyclic_and_ordered():
    rows = records("PR162E_PluginDependencyDAG.report.json")
    orders = [row["topological_order_index"] for row in rows]
    assert orders == sorted(orders)
    assert all(row["cycle_detection_status"] == "NO_CYCLE" for row in rows)

    manifest = build_selected_component_package_manifest_v1(
        stage1_launch_graph_projection_v2()
    )
    node_ids = tuple(entry.package_component_id for entry in manifest.entries)
    edges = manifest.dependency_edges
    expected_order = (
        "S1PKG::ROLE-01",
        "S1PKG::ROLE-02",
        "S1PKG::ROLE-03",
        "S1PKG::ROLE-04",
        "S1PKG::ROLE-05",
        "S1PKG::ROLE-06",
        "S1PKG::ROLE-07",
        "S1PKG::ROLE-08",
        "S1PKG::ROLE-09",
        "S1PKG::ROLE-10",
        "S1PKG::ROLE-12",
        "S1PKG::ROLE-11",
        "S1PKG::ROLE-13",
        "S1PKG::ROLE-14",
        "S1PKG::ROLE-15",
        "S1PKG::ROLE-16",
        "S1PKG::ROLE-17",
        "S1PKG::ROLE-18",
        "S1PKG::ROLE-19",
        "S1PKG::ROLE-20",
        "S1PKG::ROLE-26",
        "S1PKG::ROLE-22",
        "S1PKG::ROLE-27",
        "S1PKG::ROLE-28",
        "S1PKG::ROLE-21",
        "S1PKG::ROLE-23",
        "S1PKG::ROLE-24",
        "S1PKG::ROLE-25",
    )
    assert len(node_ids) == 28
    assert len(edges) == 102
    assert len(set(edges)) == 102
    assert ("S1PKG::ROLE-12", "S1PKG::ROLE-11") in edges
    assert compile_selected_package_dependency_order_v1(node_ids, edges) == (
        expected_order
    )
    assert compile_selected_package_dependency_order_v1(
        tuple(reversed(node_ids)),
        tuple(reversed(edges)),
    ) == expected_order

    mutation_matrix = (
        (
            (*node_ids, node_ids[0]),
            edges,
            PluginPackageReasonCodeV1.NODE_DUPLICATE,
        ),
        (
            node_ids,
            (*edges, edges[0]),
            PluginPackageReasonCodeV1.EDGE_DUPLICATE,
        ),
        (
            node_ids,
            (*edges[:-1], ("S1PKG::ROLE-99", node_ids[-1])),
            PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE,
        ),
        (
            node_ids,
            (*edges[:-1], (node_ids[-1], node_ids[-1])),
            PluginPackageReasonCodeV1.SELF_EDGE,
        ),
        (
            ("NODE-A", "NODE-B"),
            (("NODE-A", "NODE-B"), ("NODE-B", "NODE-A")),
            PluginPackageReasonCodeV1.DEPENDENCY_CYCLE,
        ),
    )
    for mutated_nodes, mutated_edges, expected_reason in mutation_matrix:
        with pytest.raises(PluginPackageContractError) as error:
            compile_selected_package_dependency_order_v1(
                mutated_nodes,
                mutated_edges,
            )
        assert error.value.reason_code is expected_reason

    legacy_rows = [
        {"node_id": "NODE-B", "dependency_node_ids": ["NODE-A"]},
        {"node_id": "NODE-A"},
    ]
    assert topological_order(legacy_rows) == ["NODE-A", "NODE-B"]
    assert has_cycle(legacy_rows) is False
    assert has_cycle(
        [
            {"node_id": "NODE-A", "dependency_node_ids": ["NODE-B"]},
            {"node_id": "NODE-B", "dependency_node_ids": ["NODE-A"]},
        ]
    ) is True
    with pytest.raises(PluginPackageContractError) as malformed_legacy:
        topological_order(
            [{"node_id": "NODE-A", "dependency_node_ids": "NODE-B"}]
        )
    assert malformed_legacy.value.reason_code is (
        PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID
    )
