from tests.pr162e.helpers import records


def test_universal_lineage_has_plugin_and_file_artifacts():
    rows = records("PR162E_UniversalArtifactLineageMap.report.json")
    assert any(row["artifact_type"] == "PLUGIN_ROW" for row in rows)
    assert any(row["artifact_type"] == "REPORT" for row in rows)
    assert all(row["no_orphan_status"] == "PASS" for row in rows)
