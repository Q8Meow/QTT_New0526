from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_source_triangulation_groups_sources_without_truth_promotion() -> None:
    rows = records("PR168_MAP3_SourceTriangulation.report.json")
    assert any(row["source_count"] > 1 for row in rows)
    for row in rows:
        assert row["source_urls"]
        assert row["source_tiers"]
        assert row["candidate_only_flag"] is True
        assert row["accepted_truth_flag"] is False
