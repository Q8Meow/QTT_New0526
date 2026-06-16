"""Validator for PR165-D3 generated artifacts."""
from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import (
    ALLOWED_DOWNSTREAM_ROUTES,
    ALLOWED_NO_ORPHAN_STATUSES,
    ALLOWED_ORDER_LANES,
    ALLOWED_SELECTION_DECISIONS,
    FORBIDDEN_STATUS_VALUES,
)
from .io import read_json, records_from_report_payload, resolve_repo_relative
from .models import REQUIRED_ROW_FIELDS


class PR165D3ValidationError(RuntimeError):
    """Raised when PR165-D3 validation fails."""


def validate_repo(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    root_dir = repo_root / c.GENERATED_DIR
    schema_dir = repo_root / c.SCHEMA_DIR
    payloads: dict[str, dict[str, Any]] = {}
    records_by_report: dict[str, list[dict[str, Any]]] = {}

    for report in c.REPORT_FILENAMES:
        path = root_dir / report
        if not path.exists():
            errors.append(f"missing root report: {path}")
            continue
        payload = read_json(path)
        payloads[report] = payload
        rows = records_from_report_payload(repo_root, payload)
        records_by_report[report] = rows
        expected_schema = c.REPORT_SCHEMA_REFS[report]
        _expect(payload.get("roadmap_pr_id") == c.PR_ID, errors, f"{report}: roadmap_pr_id mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, errors, f"{report}: created_by_pr mismatch")
        _expect(payload.get("report_name") == report, errors, f"{report}: report_name mismatch")
        _expect(payload.get("schema_ref") == expected_schema, errors, f"{report}: schema_ref mismatch")
        _expect(int(payload.get("record_count", -1)) == len(rows), errors, f"{report}: record_count mismatch")
        _expect((schema_dir / expected_schema).exists(), errors, f"{report}: missing schema {expected_schema}")
        _expect(path.stat().st_size <= c.ROOT_REPORT_LIMIT_BYTES, errors, f"{report}: root report exceeds size limit")
        for shard_ref in payload.get("shard_files", []):
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), errors, f"{report}: missing shard {shard_ref}")
            if shard_path.exists():
                shard_payload = read_json(shard_path)
                _expect(shard_payload.get("parent_report") == report, errors, f"{report}: shard parent mismatch {shard_ref}")
                _expect(shard_path.stat().st_size <= c.SHARD_LIMIT_BYTES, errors, f"{report}: shard exceeds size limit {shard_ref}")
        for row in rows:
            _validate_row(report, row, errors)

    _expect((schema_dir / "pr165_d3_common.schema.json").exists(), errors, "missing common schema")
    _expect(len(list(schema_dir.glob("*.schema.json"))) >= len(c.SCHEMA_FILENAMES), errors, "schema inventory is incomplete")

    manifest = records_by_report.get("PR165_D3_ReportManifest.report.json", [])
    _expect(len(manifest) == len(c.REPORT_FILENAMES), errors, "manifest does not cover all required reports")
    manifest_names = {row.get("manifest_report_name") for row in manifest}
    _expect(manifest_names == set(c.REPORT_FILENAMES), errors, "manifest report names do not match required list")

    summary_rows = records_by_report.get("PR165_D3_FinalSummary.report.json", [])
    _expect(len(summary_rows) == 1, errors, "final summary must contain one row")
    if summary_rows:
        _validate_summary(summary_rows[0], records_by_report, errors)

    _validate_generated_forbidden_files(repo_root, errors)
    if errors:
        raise PR165D3ValidationError("\n".join(errors[:200]))
    return {
        "roadmap_pr_id": c.PR_ID,
        "validated_report_count": len(c.REPORT_FILENAMES),
        "validated_schema_count": len(c.SCHEMA_FILENAMES),
        "validated_row_count": sum(len(v) for v in records_by_report.values()),
        "authority_zero_counts_validated": True,
        "forbidden_status_values_absent": True,
    }


def _validate_row(report: str, row: dict[str, Any], errors: list[str]) -> None:
    missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
    _expect(not missing, errors, f"{report}:{row.get('row_id')}: missing fields {missing[:8]}")
    _expect(row.get("created_by_pr") == c.PR_ID, errors, f"{report}:{row.get('row_id')}: created_by_pr mismatch")
    _expect(row.get("roadmap_pr_id") == c.PR_ID, errors, f"{report}:{row.get('row_id')}: roadmap_pr_id mismatch")
    _expect(row.get("selection_decision") in ALLOWED_SELECTION_DECISIONS, errors, f"{report}:{row.get('row_id')}: invalid selection_decision")
    _expect(row.get("selected_lane") in ALLOWED_ORDER_LANES, errors, f"{report}:{row.get('row_id')}: invalid selected_lane")
    _expect(row.get("no_orphan_status") in ALLOWED_NO_ORPHAN_STATUSES, errors, f"{report}:{row.get('row_id')}: invalid no_orphan_status")
    routes = row.get("downstream_pr_refs")
    _expect(isinstance(routes, list) and bool(routes), errors, f"{report}:{row.get('row_id')}: missing downstream routes")
    if isinstance(routes, list):
        invalid_routes = [route for route in routes if route not in ALLOWED_DOWNSTREAM_ROUTES]
        _expect(not invalid_routes, errors, f"{report}:{row.get('row_id')}: invalid downstream routes {invalid_routes}")
    for field in (
        "connector_binding_allowed_in_this_pr",
        "connector_semantic_binding_allowed_in_this_pr",
        "live_order_authority_allowed_in_this_pr",
        "owner_live_approval_allowed_in_this_pr",
        "profit_evidence_allowed_in_this_pr",
        "quantum_backend_execution_allowed_in_this_pr",
    ):
        _expect(row.get(field) is False, errors, f"{report}:{row.get('row_id')}: {field} must be false")
    for key in ZERO_AUTHORITY_KEYS:
        if key in row:
            _expect(row.get(key) == 0, errors, f"{report}:{row.get('row_id')}: {key} must be zero")
    for value in _walk_values(row):
        if isinstance(value, str) and value in FORBIDDEN_STATUS_VALUES:
            errors.append(f"{report}:{row.get('row_id')}: forbidden status value emitted")
    _expect(row.get("schema_ref") == c.REPORT_SCHEMA_REFS[report], errors, f"{report}:{row.get('row_id')}: schema_ref mismatch")
    _expect(row.get("validator_ref") == c.VALIDATOR_REF, errors, f"{report}:{row.get('row_id')}: validator_ref mismatch")


def _validate_summary(summary: dict[str, Any], records_by_report: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    expected_pairs = {
        "generated_root_report_count": len(c.REPORT_FILENAMES),
        "selected_combination_rows": len(records_by_report.get("PR165_D3_SelectedCombos.report.json", [])),
        "champion_rows": len(records_by_report.get("PR165_D3_ChampionSlate.report.json", [])),
        "challenger_rows": len(records_by_report.get("PR165_D3_ChallengerSlate.report.json", [])),
        "watch_rows": len(records_by_report.get("PR165_D3_WatchSlate.report.json", [])),
        "no_trade_decision_rows": len(records_by_report.get("PR165_D3_NoTradeDecisions.report.json", [])),
        "paper_candidate_rows": len(records_by_report.get("PR165_D3_PaperCandidates.report.json", [])),
        "replay_retest_queue_rows": len(records_by_report.get("PR165_D3_ReplayRetestQueue.report.json", [])),
        "repair_route_rows": len(records_by_report.get("PR165_D3_RepairRoute.report.json", [])),
        "quantum_comparator_rows": len(records_by_report.get("PR165_D3_QuantumComboSelect.report.json", [])),
        "non_live_order_candidate_rows": len(records_by_report.get("PR165_D3_OrderCandidateLedger.report.json", [])),
    }
    for key, expected in expected_pairs.items():
        _expect(summary.get(key) == expected, errors, f"final summary {key} mismatch: {summary.get(key)} != {expected}")
    for key in ZERO_AUTHORITY_KEYS:
        _expect(summary.get(key, 0) == 0, errors, f"final summary {key} must be zero")
    _expect(summary.get("selected_rows_are_not_live_or_profit_evidence") is True, errors, "final summary must declare selected rows non-live/non-profit")
    _expect(summary.get("timeout_ms") == 3600000, errors, "final summary timeout_ms must be 3600000")


def _validate_generated_forbidden_files(repo_root: Path, errors: list[str]) -> None:
    for path in (repo_root / c.GENERATED_DIR).glob("PR165_D3_*"):
        if path.suffix in {".sha256", ".sha", ".hash"} or "checksum" in path.name.lower():
            errors.append(f"forbidden hash/checksum artifact generated: {path}")
    shard_dir = repo_root / c.SHARD_DIR
    if shard_dir.exists():
        for path in shard_dir.glob("*"):
            if path.suffix in {".sha256", ".sha", ".hash"} or "checksum" in path.name.lower():
                errors.append(f"forbidden hash/checksum shard generated: {path}")


def _walk_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value


def _expect(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PR165-D3 generated artifacts.")
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args(argv)
    result = validate_repo(args.repo_root)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
