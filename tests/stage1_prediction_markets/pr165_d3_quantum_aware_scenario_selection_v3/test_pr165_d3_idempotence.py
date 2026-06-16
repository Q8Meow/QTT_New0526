from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any

from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.report_writer import build_payloads_with_shards

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import REPO_ROOT


REQUIRED_EXACT_REPORTS = (
    "PR165_D3_FinalSummary.report.json",
    "PR165_D3_ReportManifest.report.json",
    "PR165_D3_RowCountLedger.report.json",
    "PR165_D3_AuthorityAudit.report.json",
    "PR165_D3_NoProfitAudit.report.json",
    "PR165_D3_OrphanAudit.report.json",
    "PR165_D3_NoOrphanProof.report.json",
    "PR165_D3_StatusDriftAudit.report.json",
)
# The builder remains the manual exhaustive write/rebuild path. PR/main CI uses
# this bounded deterministic contract to avoid branch-guarded artifact writes.


def _receipt(message: str) -> None:
    print(f"PR165_D3_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=c,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR165_D3_ReportManifest.report.json",
    )


def test_pr165_d3_idempotence():
    started = time.perf_counter()
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(REPO_ROOT)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(REPO_ROOT)
    second = _bounded_snapshot(second_payloads, second_shards)

    assert_bounded_idempotence_equal(first, second)
    _receipt(f"stage=complete elapsed_seconds={time.perf_counter() - started:.3f}")
