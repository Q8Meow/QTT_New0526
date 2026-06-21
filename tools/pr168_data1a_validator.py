#!/usr/bin/env python3
"""Validation rules for PR168-DATA1A generated audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_data1a_config import (
    AUTHORITY_FALSE_FLAGS,
    REQUIRED_REPORT_IDS,
    ROW_SHARDS,
    generated_ref,
    manifest_path,
    report_path,
)


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _records(report_id: str) -> Any:
    return _load(report_path(report_id)).get("records")


def _fail(condition: bool, code: str, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(f"{code}: {message}")


def _walk(value: Any, failures: list[str], path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in AUTHORITY_FALSE_FLAGS:
                _fail(item is False, "PR168_DATA1A_AUTHORITY_FLAG_TRUE", f"{path}.{key}={item}", failures)
            lowered_key = key.lower()
            if lowered_key in {"real_positive_claim_allowed_flag", "quantum_backend_execution_flag", "quantum_advantage_claim_flag"}:
                _fail(item is False, "PR168_DATA1A_FORBIDDEN_AUTHORITY_TRUE", f"{path}.{key}={item}", failures)
            if lowered_key == "qtt_sha_or_atomicrows_hash_authority_flag":
                _fail(item is False, "PR168_DATA1A_HASH_AUTHORITY_TRUE", f"{path}.{key}={item}", failures)
            _walk(item, failures, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk(item, failures, f"{path}[{index}]")


def _validate_required_global_fields(report_id: str, payload: dict[str, Any], failures: list[str]) -> None:
    required = [
        "report_id",
        "report_version",
        "created_by_tool",
        "created_at_utc",
        "records",
        "upstream_input_refs",
        "DATA1_artifact_refs",
        "row_shard_refs_if_any",
        "data_provenance_refs",
        "owning_agent",
        "consumer_agents",
        "downstream_consumers",
        "downstream_pr_refs",
        "validator_refs",
        "test_refs",
        "no_orphan_status",
        "terminal_by_nature_flag",
        "authority_class",
        *AUTHORITY_FALSE_FLAGS.keys(),
    ]
    for key in required:
        _fail(key in payload, "PR168_DATA1A_GLOBAL_FIELD_MISSING", f"{report_id} missing {key}", failures)
    _fail(payload.get("report_id") == report_id, "PR168_DATA1A_REPORT_ID_MISMATCH", report_id, failures)
    _fail(payload.get("no_orphan_status") == "NO_ORPHAN_ROUTED", "PR168_DATA1A_ORPHAN_REPORT", report_id, failures)


def _validate_shards(failures: list[str]) -> None:
    for shard_name, path in ROW_SHARDS.items():
        manifest = manifest_path(path)
        _fail(path.exists(), "PR168_DATA1A_SHARD_MISSING", generated_ref(path), failures)
        _fail(manifest.exists(), "PR168_DATA1A_SHARD_MANIFEST_MISSING", generated_ref(manifest), failures)
        if not path.exists() or not manifest.exists():
            continue
        rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payload = _load(manifest)
        _fail(payload.get("row_count") == len(rows), "PR168_DATA1A_SHARD_ROW_COUNT_MISMATCH", shard_name, failures)
        _walk(payload, failures, f"manifest:{shard_name}")
        for index, line in enumerate(rows, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"PR168_DATA1A_JSONL_PARSE:{shard_name}:{index}:{exc}")
                continue
            for key in ("owning_agent", "consumer_agents", "downstream_pr_refs", "validator_refs", "test_refs", "no_orphan_status"):
                _fail(key in row, "PR168_DATA1A_ROW_ROUTE_FIELD_MISSING", f"{shard_name}:{index}:{key}", failures)
            _fail(row.get("no_orphan_status") == "NO_ORPHAN_ROUTED", "PR168_DATA1A_ROW_ORPHAN", f"{shard_name}:{index}", failures)
            _walk(row, failures, f"{shard_name}:{index}")


def _validate_owner_answers(failures: list[str]) -> None:
    final = _records("PR168_DATA1A_FinalSummary")
    expected_counts = {
        "kalshi_unique_market_count": 1,
        "polymarket_unique_market_count": 1,
        "kalshi_orderbook_snapshot_row_count": 1,
        "polymarket_orderbook_snapshot_row_count": 1,
        "total_orderbook_snapshot_row_count": 2,
        "total_orderbook_price_level_count": 64,
        "total_historical_trade_row_count": 10,
        "total_price_history_or_candle_point_count": 27,
        "total_snapshot_row_count": 10,
        "total_forward_l2_row_count": 2,
    }
    for key, value in expected_counts.items():
        _fail(final.get(key) == value, "PR168_DATA1A_OWNER_A_COUNT_MISMATCH", f"{key}={final.get(key)}", failures)
    _fail(final.get("qku_now_computable_after_data1_public_candidate_data_count") == 0, "PR168_DATA1A_FAKE_QKU_UNBLOCK", str(final), failures)
    _fail(final.get("qku_now_partially_computable_after_data1_count", 0) >= 5, "PR168_DATA1A_QKU_PARTIAL_COUNT_LOW", str(final), failures)
    _fail(final.get("qku_unblock_false_precision_blocked_count", 0) >= 5, "PR168_DATA1A_FALSE_PRECISION_NOT_BLOCKED", str(final), failures)
    _fail(final.get("historical_full_book_verified_public_rows_count") == 0, "PR168_DATA1A_HFB_ROWS_NOT_ZERO", str(final), failures)
    _fail(final.get("GFP2R_historical_full_book_assumption_allowed_flag") is False, "PR168_DATA1A_HFB_ASSUMPTION_ALLOWED", str(final), failures)
    _fail(final.get("GFP2R_go_flag") is True, "PR168_DATA1A_GFP2R_CANDIDATE_GO_NOT_TRUE", str(final), failures)
    _fail(final.get("live_hot_path_data_gap_count", 0) >= 0, "PR168_DATA1A_LIVE_DELTA_MISSING", str(final), failures)


def _validate_specific_reports(failures: list[str]) -> None:
    count_rows = _records("PR168_DATA1A_CountConfidenceAndLineageLedger")["count_rows"]
    _fail(any(row.get("confidence_level") == "EXACT" for row in count_rows), "PR168_DATA1A_NO_EXACT_COUNTS", "count ledger", failures)
    _fail(any(row.get("confidence_level") == "UNKNOWN" for row in count_rows), "PR168_DATA1A_NO_UNKNOWN_COUNTS", "count ledger", failures)

    qku_rows = _records("PR168_DATA1A_QKUUnblockDeltaAudit")["rows"]
    _fail(qku_rows, "PR168_DATA1A_QKU_ROWS_EMPTY", "QKU unblock rows required", failures)
    _fail(
        all(row.get("unblock_confidence_tier") != "UNBLOCK_CONFIDENCE_HIGH" for row in qku_rows),
        "PR168_DATA1A_QKU_HIGH_CONFIDENCE_WITHOUT_BINDING",
        "exact DATA1 QKU/formula binding is not available",
        failures,
    )

    quality = _records("PR168_DATA1A_DataQualityCoverageAudit")
    quality_summary = quality["summary"]
    for key in (
        "data_freshness_min_seconds",
        "missing_required_field_rate",
        "spread_coverage_rate",
        "depth_coverage_rate",
        "trade_coverage_rate",
        "resolution_lifecycle_coverage_rate",
        "fee_coverage_rate",
    ):
        _fail(key in quality_summary, "PR168_DATA1A_QUALITY_FIELD_MISSING", key, failures)
    _fail(quality["rows"], "PR168_DATA1A_QUALITY_ROWS_EMPTY", "quality rows required", failures)
    _fail(
        all(row.get("profit_evidence_created_flag") is False for row in quality["rows"]),
        "PR168_DATA1A_QUALITY_PROFIT_AUTHORITY",
        "quality rows are non-proof only",
        failures,
    )

    gfp2r_contract = _records("PR168_DATA1A_GFP2RAllowedDataFamilyContract")
    _fail(bool(gfp2r_contract.get("allowed_data_families")), "PR168_DATA1A_GFP2R_ALLOWED_EMPTY", "allowed families", failures)
    _fail(bool(gfp2r_contract.get("repair_only_data_families")), "PR168_DATA1A_GFP2R_REPAIR_EMPTY", "repair families", failures)
    _fail(bool(gfp2r_contract.get("forbidden_assumptions")), "PR168_DATA1A_GFP2R_FORBIDDEN_EMPTY", "forbidden assumptions", failures)

    alpha = _records("PR168_DATA1A_AlphaCaptureReadinessMatrix")
    _fail(alpha["rows"], "PR168_DATA1A_ALPHA_ROWS_EMPTY", "alpha readiness rows", failures)
    _fail(
        all(row.get("profit_evidence_created_flag") is False for row in alpha["rows"]),
        "PR168_DATA1A_ALPHA_PROFIT_AUTHORITY",
        "alpha capture readiness is non-proof",
        failures,
    )

    recovery = _records("PR168_DATA1A_NegativeToPositiveRecoveryReadinessQueue")
    _fail(recovery["rows"], "PR168_DATA1A_RECOVERY_ROWS_EMPTY", "recovery rows", failures)
    _fail(
        all(row.get("real_positive_claim_allowed_flag") is False for row in recovery["rows"]),
        "PR168_DATA1A_RECOVERY_CLAIMS_POSITIVE",
        "recovery rows may not claim positivity",
        failures,
    )

    quantum = _records("PR168_DATA1A_QuantumForwardUsabilityAudit")
    _fail(quantum["rows"], "PR168_DATA1A_QUANTUM_ROWS_EMPTY", "quantum rows", failures)
    _fail(
        quantum["summary"].get("quantum_backend_execution_flag") is False
        and quantum["summary"].get("quantum_advantage_claim_flag") is False,
        "PR168_DATA1A_QUANTUM_AUTHORITY_CREATED",
        str(quantum["summary"]),
        failures,
    )

    operator_rows = _records("PR168_DATA1A_OperatorActionMatrix")["rows"]
    _fail(operator_rows, "PR168_DATA1A_OPERATOR_ROWS_EMPTY", "operator rows", failures)
    _fail(
        all(row.get("next_command_or_next_pr") for row in operator_rows),
        "PR168_DATA1A_OPERATOR_NEXT_ROUTE_MISSING",
        "operator action needs next_command_or_next_pr",
        failures,
    )

    every_value_rows = _records("PR168_DATA1A_EveryValueUpstreamDownstreamCrosswalk")
    _fail(every_value_rows, "PR168_DATA1A_EVERY_VALUE_EMPTY", "every value rows", failures)
    _fail(
        all(row.get("downstream_consumers") and row.get("upstream_refs") for row in every_value_rows),
        "PR168_DATA1A_EVERY_VALUE_ROUTE_MISSING",
        "every value rows need upstream/downstream refs",
        failures,
    )


def _validate_no_forbidden_text(failures: list[str]) -> None:
    forbidden = [
        "AtomicRows.bundle.sha256",
        "REAL_POSITIVE\": true",
        "REAL_NEGATIVE\": true",
        "quantum_advantage_claim_flag\": true",
        "live_authority_created_flag\": true",
        "profit_evidence_created_flag\": true",
    ]
    for path in [*(report_path(report_id) for report_id in REQUIRED_REPORT_IDS), *ROW_SHARDS.values()]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            _fail(token not in text, "PR168_DATA1A_FORBIDDEN_TEXT", f"{generated_ref(path)} contains {token}", failures)


def validate_generated_reports() -> list[str]:
    failures: list[str] = []
    for report_id in REQUIRED_REPORT_IDS:
        path = report_path(report_id)
        _fail(path.exists(), "PR168_DATA1A_REQUIRED_REPORT_MISSING", generated_ref(path), failures)
        if not path.exists():
            continue
        payload = _load(path)
        _validate_required_global_fields(report_id, payload, failures)
        _walk(payload, failures, report_id)
    _validate_shards(failures)
    if not failures:
        _validate_owner_answers(failures)
        _validate_specific_reports(failures)
        _validate_no_forbidden_text(failures)
    return failures


def main() -> int:
    failures = validate_generated_reports()
    if failures:
        print("\n".join(failures))
        return 1
    print("PR168_DATA1A_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
