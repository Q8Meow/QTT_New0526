from collections import Counter
from .conftest import assert_rows


def test_pr166_sf_target_universe_covers_required_lanes(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_TargetUniverseRegistry.report.json")
    assert len(rows) == 6502
    states = Counter(row["pre_repair_selection_state"] for row in rows)
    assert states["ROUTE_TO_PR166_SF_REPAIR_BEFORE_RETEST"] == 537
    assert states["EXCLUDED_BY_NEGATIVE_NET_EDGE_WITH_REASON"] == 3150
    assert states["SELECTED_AS_CHAMPION"] + states["SELECTED_AS_DIVERSIFYING_CANDIDATE"] == 298
