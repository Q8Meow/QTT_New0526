from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_builds_fixture_credential_alias_readiness_for_three_stage1_venues():
    venue_ids = {record["venue_id"] for record in support.alias_records() if "venue_id" in record}

    assert venue_ids == support.stage1_venues()
    assert support.main_report()["venue_alias_count"] == 3
    assert support.main_report()["alias_record_count"] == 4
