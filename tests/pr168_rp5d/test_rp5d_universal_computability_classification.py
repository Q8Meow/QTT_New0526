from __future__ import annotations

from ._helpers import report, rows


def test_every_rp5c_identity_has_universal_coverage_and_computability_state() -> None:
    run = report("rp5d_run_receipt.report.json")
    coverage = rows("rp5d_universal_coverage.jsonl")
    materialization = rows("rp5d_comp_materialization.jsonl")

    assert len(coverage) == run["rp5c_identity_count"]
    assert len(materialization) == run["rp5c_identity_count"]
    assert {row["identity_ref"] for row in coverage} == {row["identity_ref"] for row in materialization}
