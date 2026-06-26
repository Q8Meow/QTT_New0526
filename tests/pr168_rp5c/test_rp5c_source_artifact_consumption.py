from __future__ import annotations

from ._helpers import load_rows


def test_rp5c_source_artifact_rows_are_routed() -> None:
    rows = load_rows("source_artifact_consumption_ledger")
    coverage = load_rows("input_artifact_to_identity_coverage")

    assert len(rows) == len(coverage)
    assert rows
    for row in rows:
        assert row["source_artifact_row_id"]
        assert row["source_file_path"]
        assert row["consumption_status"]
        assert row["raw_legacy_decision_authority_allowed_flag"] is False
        assert row["derived_route_resolution_refs"]
        assert row["downstream_pr_refs"]
        assert row["validator_refs"]
