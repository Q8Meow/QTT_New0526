from __future__ import annotations

from pathlib import Path

import pytest

from tools import qtt_test_gate


def _report() -> dict:
    return qtt_test_gate.build_report(
        repo_root=Path("."),
        phase=qtt_test_gate.PHASE,
        strict_no_claim=True,
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


@pytest.mark.parametrize("flag", sorted(qtt_test_gate.NO_CLAIM_FLAGS))
def test_qtt_test_gate_report_cannot_flip_no_claim_flags_true(flag):
    report = _report()
    report["no_claim_flags"][flag] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, flag)


@pytest.mark.parametrize("flag", sorted(qtt_test_gate.STATIC_AUTHORITY_FLAGS))
def test_qtt_test_gate_static_metadata_cannot_claim_authority(flag):
    report = _report()
    report["metadata"][flag] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, flag)


def test_qtt_test_gate_blocks_replay_paper_live_blocker_and_profit_claims():
    report = _report()
    report["no_claim_flags"]["replay_paper_result_claim"] = True
    report["no_claim_flags"]["live_reachability_claim"] = True
    report["no_claim_flags"]["blocker_reduction_claim"] = True
    report["no_claim_flags"]["profit_claim"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    for fragment in [
        "replay_paper_result_claim",
        "live_reachability_claim",
        "blocker_reduction_claim",
        "profit_claim",
    ]:
        _assert_failure_contains(failures, fragment)

