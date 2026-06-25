from tests.pr168_rp5b._helpers import final_summary, load_rows


def test_active_artifact_registry_exists() -> None:
    rows = load_rows("active_artifact_registry_rows")
    assert len(rows) == final_summary()["active_registry_row_count"]
    assert any(row["artifact_family"] == "LEGACY_SEMANTIC_SUPERSESSION" for row in rows)
    assert all(row["downstream_refs"] for row in rows)
    assert all("RAW_LEGACY_REPORT_DECISION_AUTHORITY" in row["forbidden_consumers"] for row in rows)
