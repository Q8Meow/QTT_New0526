from __future__ import annotations

from ._helpers import report, rows


def test_every_stage1_seed_has_detailed_tiering() -> None:
    run = report("rp5d_run_receipt.report.json")
    stage1 = rows("rp5d_stage1_coverage.jsonl")
    tiers = rows("rp5d_exec_tiers.jsonl")

    assert len(stage1) == run["stage1_seed_identity_count"]
    assert len(tiers) == run["stage1_seed_identity_count"]
    assert all(row["rp5d_tier_ref"] for row in stage1)
