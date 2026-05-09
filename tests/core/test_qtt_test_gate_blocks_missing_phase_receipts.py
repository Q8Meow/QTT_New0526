from __future__ import annotations

from pathlib import Path

from tools import qtt_test_gate


def _touch_required_receipts(root: Path, *, skip_path: str) -> None:
    for spec in qtt_test_gate.REQUIRED_RECEIPTS:
        for path_text in spec["paths"]:
            if path_text == skip_path:
                continue
            path = root / path_text
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")


def test_missing_prior_phase_receipt_blocks_cumulative_gate(tmp_path):
    missing_path = (
        "tests/fixtures/runtime_orchestration/"
        "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
    )
    _touch_required_receipts(tmp_path, skip_path=missing_path)

    report = qtt_test_gate.build_report(
        repo_root=tmp_path,
        phase=qtt_test_gate.PHASE,
        strict_no_claim=True,
    )

    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "stage1_runtime_scaffold_gate_receipt_present"
    )
    assert report["status"] == "FAIL"
    assert receipt["satisfied"] is False
    assert receipt["status"] == "MISSING_BLOCKED"
    assert any("stage1_runtime_scaffold_gate_receipt_present" in finding for finding in report["findings"])

