from __future__ import annotations

from .conftest import REPO_ROOT
from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results import constants as c
from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.report_writer import (
    build_payloads_with_shards,
)
from typing import Any


REQUIRED_EXACT_REPORTS = (
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ReportManifest.report.json",
    "PR166_SM_AuthorityBoundaryAudit.report.json",
    "PR166_SM_OrphanArtifactAudit.report.json",
    "PR166_SM_StatusEnumDriftAudit.report.json",
)
# The builder's --verify-idempotent CLI remains the manual exhaustive
# byte-for-byte rebuild mode. This PR-CI test is the bounded deterministic
# contract over count-bearing reports, manifest coverage, and sampled shards.


def _receipt(message: str) -> None:
    print(f"PR166_SM_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=c,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR166_SM_ReportManifest.report.json",
    )


def test_pr166_sm_payload_build_is_idempotent():
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(REPO_ROOT)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(REPO_ROOT)
    second = _bounded_snapshot(second_payloads, second_shards)

    assert_bounded_idempotence_equal(first, second)
    _receipt("stage=complete")
