from __future__ import annotations

from copy import deepcopy
import time
from typing import Any

from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_idempotence_differences,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.report_writer import build_payloads_with_shards

from .helpers import REPO_ROOT


REQUIRED_EXACT_REPORTS = (
    "PR166_SM2_FinalSummary.report.json",
    "PR166_SM2_ReportManifest.report.json",
    "PR166_SM2_RowCountLedger.report.json",
    "PR166_SM2_AuthorityAudit.report.json",
    "PR166_SM2_NoProfitAudit.report.json",
    "PR166_SM2_OrphanAudit.report.json",
    "PR166_SM2_StatusDriftAudit.report.json",
)
# The builder's --verify-idempotent CLI remains the manual exhaustive
# byte-for-byte rebuild mode. This PR-CI test is the bounded deterministic
# contract over count-bearing reports, manifest coverage, and sampled shards.


def _receipt(message: str) -> None:
    print(f"PR166_SM2_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=c,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR166_SM2_ReportManifest.report.json",
    )


def test_pr166_sm2_bounded_idempotence_contract_is_deterministic():
    started = time.perf_counter()
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(REPO_ROOT)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(REPO_ROOT)
    second = _bounded_snapshot(second_payloads, second_shards)
    assert_bounded_idempotence_equal(first, second)

    elapsed = time.perf_counter() - started
    _receipt(f"stage=complete elapsed_seconds={elapsed:.3f}")


def _fixture_snapshot() -> dict[str, Any]:
    return {
        "required_exact_reports": {
            "PR166_SM2_FinalSummary.report.json": {
                "record_count": 1,
                "records": [{"refreshed_score_rows": 3215}],
            },
            "PR166_SM2_ReportManifest.report.json": {
                "record_count": 2,
                "records": [
                    {"report_name": "PR166_SM2_FinalSummary"},
                    {"report_name": "PR166_SM2_RowCountLedger"},
                ],
            },
            "PR166_SM2_RowCountLedger.report.json": {
                "record_count": 1,
                "records": [{"report_name": "ledger", "row_count": 77}],
            },
            "PR166_SM2_AuthorityAudit.report.json": {
                "record_count": 1,
                "records": [{"live_order_authority_count": 0}],
            },
            "PR166_SM2_NoProfitAudit.report.json": {
                "record_count": 1,
                "records": [{"profit_evidence_count": 0}],
            },
            "PR166_SM2_OrphanAudit.report.json": {
                "record_count": 1,
                "records": [{"orphan_rows": 0}],
            },
            "PR166_SM2_StatusDriftAudit.report.json": {
                "record_count": 1,
                "records": [{"status_drift_count": 0}],
            },
        },
        "report_envelopes": {
            "PR166_SM2_FinalSummary.report.json": {
                "report_filename": "PR166_SM2_FinalSummary.report.json",
                "record_count": 1,
            }
        },
        "manifest_coverage": {
            "PR166_SM2_ReportManifest.report.json": {
                "constant_report_filenames": (
                    "PR166_SM2_FinalSummary.report.json",
                    "PR166_SM2_RowCountLedger.report.json",
                ),
                "constant_schema_filenames": (
                    "pr166_sm2_common.schema.json",
                    "pr166_sm2_final_summary.schema.json",
                    "pr166_sm2_row_count_ledger.schema.json",
                ),
                "manifest_root_report_filenames": (
                    "PR166_SM2_FinalSummary.report.json",
                    "PR166_SM2_RowCountLedger.report.json",
                ),
                "manifest_root_schema_paths": (
                    "src/qtt/stage1_prediction_markets/"
                    "pr166_sm2_score_memory_refresh_v2/schemas/"
                    "pr166_sm2_final_summary.schema.json",
                    "src/qtt/stage1_prediction_markets/"
                    "pr166_sm2_score_memory_refresh_v2/schemas/"
                    "pr166_sm2_row_count_ledger.schema.json",
                ),
                "manifest_root_entry_count": 2,
                "manifest_shard_entry_count": 1,
                "manifest_shard_report_paths": (
                    "docs/master_plan/generated/pr166_sm2_shards/sample.report.json",
                ),
            }
        },
        "sampled_shards": {
            "docs/master_plan/generated/pr166_sm2_shards/sample.report.json": {
                "report_filename": "sample.report.json",
                "parent_report_filename": "PR166_SM2_ScoreRegistry.report.json",
                "schema_ref": "pr166_sm2_score_registry.schema.json",
                "record_count": 3,
                "sampled_rows": [
                    {"row_id": "a", "value": 1},
                    {"row_id": "b", "value": 2},
                    {"row_id": "c", "value": 3},
                ],
            }
        },
    }


def test_bounded_idempotence_detects_changed_top_level_required_report():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["required_exact_reports"]["PR166_SM2_ReportManifest.report.json"][
        "records"
    ][0]["report_name"] = "changed"

    assert bounded_idempotence_differences(left, right) == (
        "required_exact_reports:PR166_SM2_ReportManifest.report.json",
    )


def test_bounded_idempotence_detects_changed_final_summary_count():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["required_exact_reports"]["PR166_SM2_FinalSummary.report.json"][
        "records"
    ][0]["refreshed_score_rows"] = 3216

    assert bounded_idempotence_differences(left, right) == (
        "required_exact_reports:PR166_SM2_FinalSummary.report.json",
    )


def test_bounded_idempotence_detects_changed_authority_no_profit_orphan_audit_field():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["required_exact_reports"]["PR166_SM2_AuthorityAudit.report.json"][
        "records"
    ][0]["live_order_authority_count"] = 1
    right["required_exact_reports"]["PR166_SM2_NoProfitAudit.report.json"][
        "records"
    ][0]["profit_evidence_count"] = 1
    right["required_exact_reports"]["PR166_SM2_OrphanAudit.report.json"][
        "records"
    ][0]["orphan_rows"] = 1

    assert bounded_idempotence_differences(left, right) == (
        "required_exact_reports:PR166_SM2_AuthorityAudit.report.json",
        "required_exact_reports:PR166_SM2_NoProfitAudit.report.json",
        "required_exact_reports:PR166_SM2_OrphanAudit.report.json",
    )


def test_bounded_idempotence_detects_changed_sampled_shard_row():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["sampled_shards"][
        "docs/master_plan/generated/pr166_sm2_shards/sample.report.json"
    ]["sampled_rows"][1]["value"] = 200

    assert bounded_idempotence_differences(left, right) == (
        "sampled_shards:docs/master_plan/generated/pr166_sm2_shards/sample.report.json",
    )


def test_bounded_idempotence_detects_missing_manifest_report_entry():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["manifest_coverage"]["PR166_SM2_ReportManifest.report.json"][
        "manifest_root_report_filenames"
    ] = ("PR166_SM2_FinalSummary.report.json",)

    assert bounded_idempotence_differences(left, right) == (
        "manifest_coverage:PR166_SM2_ReportManifest.report.json",
    )


def test_bounded_idempotence_snapshot_is_deterministic():
    left = _fixture_snapshot()
    right = deepcopy(left)

    assert bounded_idempotence_differences(left, right) == ()
