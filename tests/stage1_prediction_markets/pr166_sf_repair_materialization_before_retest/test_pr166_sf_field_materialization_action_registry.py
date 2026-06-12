from .conftest import assert_rows


def test_pr166_sf_field_materialization_registry_covers_targets(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_FieldMaterializationRegistry.report.json")
    assert len(rows) == 6502
    assert all(row["materialization_action"] for row in rows[:50])
    assert all(row["materialization_actuality_score"] == 1.0 for row in rows[:50])
