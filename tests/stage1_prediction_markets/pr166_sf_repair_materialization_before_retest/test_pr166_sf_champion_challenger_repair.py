from .conftest import assert_rows


def test_pr166_sf_champion_challenger_roles_exist(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairChampionChallengerLedger.report.json")
    roles = {row["repair_role"] for row in rows}
    assert "REPAIR_CHAMPION" in roles
    assert "REPAIR_CHALLENGER" in roles
