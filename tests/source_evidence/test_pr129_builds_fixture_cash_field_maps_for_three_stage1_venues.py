from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_pr129_builds_fixture_cash_field_maps_for_three_stage1_venues():
    field_maps = support.field_maps()

    assert {record["venue_id"] for record in field_maps} == support.stage1_venues()
    assert len(field_maps) == 21
    for venue_id in support.stage1_venues():
        venue_records = [record for record in field_maps if record["venue_id"] == venue_id]
        assert {record["cash_component_class"] for record in venue_records} == (
            support.component_classes()
        )
        assert all(record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT" for record in venue_records)
