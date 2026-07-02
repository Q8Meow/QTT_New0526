from tests.pr169_dash1.conftest import jsonl


def test_dag_contains_required_upstream_downstream_routes() -> None:
    rows = jsonl("dag.generated.jsonl")
    node_kinds = {row["node_kind"] for row in rows}
    assert "RP5G evidence" in node_kinds
    assert "RANK4 ranking" in node_kinds
    assert "QOPT1 optimization" in node_kinds
    assert "VS2 paper-intent packet" in node_kinds
    assert "MEM1 memory" in node_kinds
    assert any("TG1" in row["activation_route"] for row in rows)
    assert all(row["no_orphan_ref"] == "owner_dashboard_no_orphan.report.json" for row in rows)
