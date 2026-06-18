from tests.pr162e.helpers import records


def test_dependency_dag_is_acyclic_and_ordered():
    rows = records("PR162E_PluginDependencyDAG.report.json")
    orders = [row["topological_order_index"] for row in rows]
    assert orders == sorted(orders)
    assert all(row["cycle_detection_status"] == "NO_CYCLE" for row in rows)
