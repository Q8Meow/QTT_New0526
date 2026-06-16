from __future__ import annotations

from copy import deepcopy
import json
import time
from typing import Any

from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest.report_writer import build_payloads_with_shards

from .helpers import REPO_ROOT


REQUIRED_EXACT_REPORTS = (
    "PR166_SF_R2_FinalSummary.report.json",
    "PR166_SF_R2_ReportManifest.report.json",
    "PR166_SF_R2_RowCountLedger.report.json",
    "PR166_SF_R2_AuthorityAudit.report.json",
    "PR166_SF_R2_NoProfitAudit.report.json",
    "PR166_SF_R2_OrphanAudit.report.json",
    "PR166_SF_R2_StatusDriftAudit.report.json",
)
# The builder's --verify-idempotent CLI remains the manual exhaustive byte-for-byte
# rebuild mode. This PR-CI test is the bounded deterministic contract.


def _receipt(message: str) -> None:
    print(f"PR166_SF_R2_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _stable_row_key(row: dict[str, Any]) -> tuple[str, str]:
    preferred = (
        "row_id",
        "candidate_packet_id",
        "repair_action_id",
        "repaired_packet_id",
        "report_name",
    )
    for field in preferred:
        value = row.get(field)
        if value not in (None, ""):
            return (field, str(value))
    return ("canonical_json", json.dumps(row, sort_keys=True, separators=(",", ":")))


def _sample_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    ordered = sorted(rows, key=_stable_row_key)
    indexes = sorted({0, len(ordered) // 2, len(ordered) - 1})
    return [deepcopy(ordered[index]) for index in indexes]


def _report_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_name": payload.get("report_name"),
        "schema_ref": payload.get("schema_ref"),
        "record_count": payload.get("record_count"),
        "sharded_flag": payload.get("sharded_flag"),
        "records_omitted_for_sharding_flag": payload.get(
            "records_omitted_for_sharding_flag"
        ),
        "shard_count": payload.get("shard_count"),
        "shard_files": tuple(payload.get("shard_files") or ()),
    }


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    missing = sorted(set(REQUIRED_EXACT_REPORTS) - set(payloads))
    assert not missing, f"bounded idempotence missing required reports: {missing}"
    return {
        "required_exact_reports": {
            filename: deepcopy(payloads[filename])
            for filename in REQUIRED_EXACT_REPORTS
        },
        "report_envelopes": {
            filename: _report_envelope(payloads[filename])
            for filename in c.REPORT_FILENAMES
        },
        "sampled_shards": {
            shard_ref: {
                "report_name": payload.get("report_name"),
                "schema_ref": payload.get("schema_ref"),
                "record_count": payload.get("record_count"),
                "sampled_rows": _sample_rows(list(payload.get("records") or [])),
            }
            for shard_ref, payload in sorted(shard_payloads.items())
        },
    }


def bounded_idempotence_differences(
    left: dict[str, Any],
    right: dict[str, Any],
) -> tuple[str, ...]:
    differences: list[str] = []
    for section in ("required_exact_reports", "report_envelopes", "sampled_shards"):
        left_values = left.get(section, {})
        right_values = right.get(section, {})
        for key in sorted(set(left_values) | set(right_values)):
            if left_values.get(key) != right_values.get(key):
                differences.append(f"{section}:{key}")
    return tuple(differences)


def assert_bounded_idempotence_equal(
    left: dict[str, Any],
    right: dict[str, Any],
) -> None:
    differences = bounded_idempotence_differences(left, right)
    assert not differences, "bounded idempotence drift: " + ", ".join(differences)


def test_pr166_sf_r2_bounded_idempotence_contract_is_deterministic():
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
            "PR166_SF_R2_FinalSummary.report.json": {
                "record_count": 1,
                "records": [{"converted_positive_rows": 150}],
            },
            "PR166_SF_R2_ReportManifest.report.json": {
                "record_count": 2,
                "records": [{"report_name": "one"}, {"report_name": "two"}],
            },
            "PR166_SF_R2_RowCountLedger.report.json": {
                "record_count": 1,
                "records": [{"report_name": "ledger", "record_count": 77}],
            },
            "PR166_SF_R2_AuthorityAudit.report.json": {
                "record_count": 1,
                "records": [{"live_order_authority_count": 0}],
            },
            "PR166_SF_R2_NoProfitAudit.report.json": {
                "record_count": 1,
                "records": [{"profit_evidence_count": 0}],
            },
            "PR166_SF_R2_OrphanAudit.report.json": {
                "record_count": 1,
                "records": [{"orphan_rows": 0}],
            },
            "PR166_SF_R2_StatusDriftAudit.report.json": {
                "record_count": 1,
                "records": [{"status_drift_count": 0}],
            },
        },
        "report_envelopes": {
            "PR166_SF_R2_FinalSummary.report.json": {
                "report_name": "PR166_SF_R2_FinalSummary.report.json",
                "record_count": 1,
            }
        },
        "sampled_shards": {
            "docs/master_plan/generated/pr166_sf_r2_shards/sample.report.json": {
                "report_name": "sample",
                "schema_ref": "sample.schema.json",
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
    right["required_exact_reports"]["PR166_SF_R2_ReportManifest.report.json"][
        "records"
    ][0]["report_name"] = "changed"

    assert bounded_idempotence_differences(left, right) == (
        "required_exact_reports:PR166_SF_R2_ReportManifest.report.json",
    )


def test_bounded_idempotence_detects_changed_final_summary_count():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["required_exact_reports"]["PR166_SF_R2_FinalSummary.report.json"][
        "records"
    ][0]["converted_positive_rows"] = 151

    assert bounded_idempotence_differences(left, right) == (
        "required_exact_reports:PR166_SF_R2_FinalSummary.report.json",
    )


def test_bounded_idempotence_detects_changed_authority_no_profit_orphan_audit_field():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["required_exact_reports"]["PR166_SF_R2_AuthorityAudit.report.json"][
        "records"
    ][0]["live_order_authority_count"] = 1
    right["required_exact_reports"]["PR166_SF_R2_NoProfitAudit.report.json"][
        "records"
    ][0]["profit_evidence_count"] = 1
    right["required_exact_reports"]["PR166_SF_R2_OrphanAudit.report.json"][
        "records"
    ][0]["orphan_rows"] = 1

    assert bounded_idempotence_differences(left, right) == (
        "required_exact_reports:PR166_SF_R2_AuthorityAudit.report.json",
        "required_exact_reports:PR166_SF_R2_NoProfitAudit.report.json",
        "required_exact_reports:PR166_SF_R2_OrphanAudit.report.json",
    )


def test_bounded_idempotence_detects_changed_sampled_shard_row():
    left = _fixture_snapshot()
    right = deepcopy(left)
    right["sampled_shards"][
        "docs/master_plan/generated/pr166_sf_r2_shards/sample.report.json"
    ]["sampled_rows"][1]["value"] = 200

    assert bounded_idempotence_differences(left, right) == (
        "sampled_shards:docs/master_plan/generated/pr166_sf_r2_shards/sample.report.json",
    )


def test_bounded_idempotence_snapshot_is_deterministic():
    left = _fixture_snapshot()
    right = deepcopy(left)

    assert bounded_idempotence_differences(left, right) == ()
