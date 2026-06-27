from __future__ import annotations

from ._helpers import report, rows


def test_value_lineage_covers_material_fields_without_orphans() -> None:
    run = report("rp5d_run_receipt.report.json")
    lineage = rows("rp5d_value_lineage.jsonl")

    assert len(lineage) == run["value_lineage_row_count"]
    assert all(row["orphan_flag"] is False for row in lineage)
    assert all(row["source_artifact_ref"] for row in lineage)
    assert all(row["generated_artifact_ref"] for row in lineage)
