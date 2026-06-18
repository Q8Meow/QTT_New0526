from tests.pr162e.helpers import records


def test_file_consumer_map_covers_generated_reports():
    rows = records("PR162E_FileConsumerMap.report.json")
    paths = {row["artifact_path"] for row in rows}
    assert "docs/master_plan/generated/PR162E_PluginRegistry.report.json" in paths
    assert "docs/master_plan/generated/PR162E_FinalSummary.report.json" in paths
