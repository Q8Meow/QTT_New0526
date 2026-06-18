from tests.pr162e.helpers import records


def test_champion_challenger_arbitration_fields_exist():
    row = records("PR162E_PluginChampChallenger.report.json")[0]
    assert row["champion_plugin_id"]
    assert row["challenger_plugin_ids"]
    assert row["owner_review_route"] == "PR162E_To_OwnerDashboard.report.json"
