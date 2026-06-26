from __future__ import annotations

from ._helpers import load_rows


def test_rp5c_file_to_derived_route_crosswalk_covers_sources() -> None:
    source_rows = load_rows("source_artifact_consumption_ledger")
    crosswalk = load_rows("file_to_derived_route_crosswalk")

    assert len(crosswalk) == len(source_rows)
    assert all(row["responsibility_group_refs"] for row in crosswalk)
    assert all(row["derived_route_resolution_refs"] for row in crosswalk)
    assert all(row["validator_refs"] for row in crosswalk)
