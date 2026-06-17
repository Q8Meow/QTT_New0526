from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit import paths as p
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.report_builder import build_payloads_with_shards


REQUIRED_EXACT_REPORTS = (
    "PR164_FinalSummary.report.json",
    "PR164_DecisionAndNextPRRecommendation.report.json",
    "PR164_ReportManifest.report.json",
    "PR164_CentralAuthorityDecisionLedger.report.json",
    "PR164_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR164_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR164_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR164_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR164_OrphanArtifactAudit.report.json",
)
# The builder's --verify-idempotent CLI remains the manual exhaustive
# byte-for-byte rebuild path. PR/main CI uses this bounded deterministic
# contract over required root reports, manifest coverage, and sampled shards.


def _receipt(message: str) -> None:
    print(f"PR164_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=p,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR164_ReportManifest.report.json",
    )


def test_pr164_repeat_run_determinism():
    root = Path(".").resolve()
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(root, p.EXPECTED_BRANCH)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(root, p.EXPECTED_BRANCH)
    second = _bounded_snapshot(second_payloads, second_shards)

    assert_bounded_idempotence_equal(first, second)
    _receipt("stage=complete")
