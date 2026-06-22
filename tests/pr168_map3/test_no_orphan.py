from __future__ import annotations

from tests.pr168_map3._helpers import all_records, assert_minimum_counts


def test_online_scouting_rows_have_no_orphan_routes_and_no_forbidden_authority() -> None:
    assert_minimum_counts()
    for row in all_records():
        assert row.get("no_orphan_status") == "NO_ORPHAN_LINKED"
        assert row.get("accepted_truth_flag") is not True
        assert row.get("champion_allowed_flag") is not True
        assert row.get("live_candidate_allowed_flag") is not True
        assert row.get("authority_class") not in {"REAL_POSITIVE", "REAL_NEGATIVE"}
