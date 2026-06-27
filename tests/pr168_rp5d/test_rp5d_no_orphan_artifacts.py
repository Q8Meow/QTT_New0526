from __future__ import annotations

from ._helpers import report, rows


def test_no_orphan_artifact_and_qku_formula_proofs_are_zero_orphan() -> None:
    run = report("rp5d_run_receipt.report.json")
    artifacts = rows("rp5d_no_orphan_artifacts.jsonl")
    qkus = rows("rp5d_no_orphan_qku_formula.jsonl")

    assert run["orphan_artifact_count"] == 0
    assert run["orphan_qku_count"] == 0
    assert run["orphan_formula_count"] == 0
    assert all(row["orphan_flag"] is False for row in artifacts)
    assert all(row["orphan_identity_flag"] is False for row in qkus)
    assert all(row["orphan_qku_flag"] is False for row in qkus)
    assert all(row["orphan_formula_flag"] is False for row in qkus)
