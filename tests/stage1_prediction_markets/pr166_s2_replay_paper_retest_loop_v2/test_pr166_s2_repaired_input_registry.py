from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_input_registry_links_schemas_and_sources():
    rows = assert_report_rows("PR166_S2_InputRegistry.report.json")
    assert any(row["input_report_ref"] == "PR166_SF_RepairedPayloadRegistry.report.json" for row in rows)
    assert all(row["schema_ref"].endswith(".schema.json") for row in rows[:25])
