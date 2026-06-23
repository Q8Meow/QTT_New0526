from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_source_to_retest_maps_useful_sources() -> None:
    assert_recovery1_valid()
    assert all(row["source_to_retest_mapping_status"] != "REJECTED_WITH_REASON" for row in rows("source_to_retest"))
