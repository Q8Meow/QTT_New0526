from tests.pr162e.helpers import records


def test_read_receipt_covers_repo_and_online_sources():
    rows = records("PR162E_ReadReceipt.report.json")
    assert any(row.get("artifact_path", "").endswith("PR167_PluginNeeds.report.json") for row in rows)
    assert any(row.get("source_url") for row in rows)
    assert all(row.get("source_truth_accepted") is False for row in rows if row.get("source_url"))
