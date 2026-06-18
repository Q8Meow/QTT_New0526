from tests.pr162e.helpers import records


def test_execution_tca_decomposition_fields_exist():
    rows = records("PR162E_ExecutionTCAPlugin.report.json")
    assert rows
    row = rows[0]
    assert row["plugin_id"]
    registry = records("PR162E_PluginRegistry.report.json")
    full = next(item for item in registry if item["plugin_id"] == row["plugin_id"])
    assert "implementation_shortfall" in full["execution_tca_decomposition"]
