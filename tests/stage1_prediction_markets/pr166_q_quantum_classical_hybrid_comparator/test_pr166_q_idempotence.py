from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any

from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator import constants as c
from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator.report_writer import build_payloads_with_shards

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import REPO_ROOT


REQUIRED_EXACT_REPORTS = (
    "PR166_Q_FinalSummary.report.json",
    "PR166_Q_ReportManifest.report.json",
    "PR166_Q_InputHandoffConsumption.report.json",
    "PR166_Q_RootReportConsumptionLedger.report.json",
    "PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json",
    "PR166_Q_UniversalArtifactConsumerMap.report.json",
)


def _receipt(message: str) -> None:
    print(f"PR166_Q_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=c,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR166_Q_ReportManifest.report.json",
    )


def test_pr166_q_bounded_idempotence_contract_is_deterministic():
    started = time.perf_counter()
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(REPO_ROOT)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(REPO_ROOT)
    second = _bounded_snapshot(second_payloads, second_shards)

    assert_bounded_idempotence_equal(first, second)
    _receipt(f"stage=complete elapsed_seconds={time.perf_counter() - started:.3f}")
