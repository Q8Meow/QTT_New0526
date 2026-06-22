from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_new_ids_are_forward_only_and_non_hash_authority() -> None:
    rows = records("PR168_MAP3_NewIDs.report.json")
    assert rows
    for row in rows:
        assert row["not_upstream_exact_before_map3_flag"] is True
        assert row["canonical_from_pr168_map3_forward_flag"] is True
        assert "sha" not in row["new_id"].lower()
        assert "hash" not in row["new_id"].lower()
