from tests.pr162e.helpers import load_report, plugin_rows


def test_no_metadata_only_or_label_only_rows_pass():
    assert load_report("PR162E_PluginRegistry.report.json")["metadata_only_count"] == 0
    assert load_report("PR162E_PluginRegistry.report.json")["solver_label_only_count"] == 0
    assert all(row["test_vector_refs"] for row in plugin_rows() if row["plugin_materialization_status"] != "TERMINAL_NO_TRADE_NONLIVE")
