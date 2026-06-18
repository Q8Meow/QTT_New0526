from tests.pr162e.helpers import records


def test_value_lineage_map_covers_plugin_scores():
    rows = records("PR162E_ValueLineageMap.report.json")
    assert len(rows) == 559
    assert all(row["score_components"] for row in rows)
