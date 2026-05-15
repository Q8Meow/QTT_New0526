#!/usr/bin/env python3
"""Lightweight post-Repair-PR-D materialization sentinel.

This module intentionally does not import the full D validator. Pre-D validators
use it to distinguish the historical pre-D absence state from the valid post-D
materialization state without creating recursive validation-gate dependencies.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass


D_MANIFEST_PATH = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsExactRowSourceMaterializationManifest.yaml"
)
D_REPORT_PATH = pathlib.Path(
    "docs/master_plan/generated/AtomicRowsExactRowSourceMaterialization.report.json"
)
EXACT_ROW_SOURCES_DIR = pathlib.Path("docs/master_plan/atomic_rows/exact_row_sources")
BUNDLE_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
BUNDLE_SHA_PATH = pathlib.Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
EXPECTED_TOTAL_ROWS = 4183
EXPECTED_FILE_NAMES = (
    "001_signal_features.exact_rows.jsonl",
    "002_scoring_ranking.exact_rows.jsonl",
    "003_normalization_calibration.exact_rows.jsonl",
    "004_risk_control.exact_rows.jsonl",
    "005_execution_connector_boundary.exact_rows.jsonl",
    "006_capital_sizing_cash.exact_rows.jsonl",
    "007_latency_routing.exact_rows.jsonl",
    "008_error_guard_fail_closed.exact_rows.jsonl",
    "009_lifecycle_agent_binding.exact_rows.jsonl",
    "010_source_evidence_connector_semantic.exact_rows.jsonl",
    "011_replay_paper_validation.exact_rows.jsonl",
    "012_quantum_advisory_optimization.exact_rows.jsonl",
    "013_quantum_qubo_ising_metadata.exact_rows.jsonl",
    "014_quantum_qaoa_vqe_annealing_metadata.exact_rows.jsonl",
    "015_quantum_portfolio_hybrid_comparator.exact_rows.jsonl",
)


@dataclass(frozen=True)
class PostDMaterializationState:
    allowed: bool
    failures: tuple[str, ...]
    manifest_present: bool
    report_present: bool
    exact_row_sources_directory_present: bool
    exact_row_source_file_count: int
    exact_row_source_record_count: int
    bundle_absent: bool
    bundle_sha_absent: bool


def _load_report(repo_root: pathlib.Path) -> dict:
    return json.loads((repo_root / D_REPORT_PATH).read_text(encoding="utf-8"))


def check_post_d_materialization_state(repo_root: pathlib.Path) -> PostDMaterializationState:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    manifest_present = (repo_root / D_MANIFEST_PATH).exists()
    report_present = (repo_root / D_REPORT_PATH).exists()
    exact_dir = repo_root / EXACT_ROW_SOURCES_DIR
    exact_dir_present = exact_dir.is_dir()
    bundle_absent = not (repo_root / BUNDLE_PATH).exists()
    bundle_sha_absent = not (repo_root / BUNDLE_SHA_PATH).exists()
    actual_files = (
        tuple(sorted(path.name for path in exact_dir.glob("*.exact_rows.jsonl")))
        if exact_dir_present
        else tuple()
    )
    record_count = 0
    for name in actual_files:
        path = exact_dir / name
        record_count += len(path.read_text(encoding="utf-8").splitlines())

    if not manifest_present:
        failures.append("D materialization manifest missing")
    if not report_present:
        failures.append("D materialization report missing")
    if not exact_dir_present:
        failures.append("exact_row_sources directory missing")
    if actual_files != EXPECTED_FILE_NAMES:
        failures.append("exact-row source files do not match the 15 D family files")
    if record_count != EXPECTED_TOTAL_ROWS:
        failures.append("exact-row source record count is not 4183")
    if not bundle_absent:
        failures.append("AtomicRows.bundle.jsonl must remain absent")
    if not bundle_sha_absent:
        failures.append("AtomicRows.bundle.sha256 must remain absent")

    if report_present:
        try:
            report = _load_report(repo_root)
        except Exception as exc:
            failures.append(f"D materialization report could not be loaded: {exc}")
            report = {}
        if report.get("validation_result") != "PASS_EXACT_ROW_SOURCE_MATERIALIZATION_ONLY":
            failures.append("D materialization report validation_result is not PASS")
        if report.get("exact_row_source_file_count") != 15:
            failures.append("D materialization report file count is not 15")
        if report.get("exact_row_source_record_count") != EXPECTED_TOTAL_ROWS:
            failures.append("D materialization report row count is not 4183")
        transition = report.get("post_d_transition_audit", {})
        if not isinstance(transition, dict):
            transition = {}
        for field in (
            "exact_row_sources_directory_present_by_repair_pr_d",
            "c_and_c1_did_not_create_rows",
            "rows_created_by_repair_pr_d_only",
            "bundle_still_absent",
            "sha_still_absent",
        ):
            if transition.get(field) is not True:
                failures.append(f"D materialization report post_d_transition_audit.{field} must be true")

    return PostDMaterializationState(
        allowed=not failures,
        failures=tuple(failures),
        manifest_present=manifest_present,
        report_present=report_present,
        exact_row_sources_directory_present=exact_dir_present,
        exact_row_source_file_count=len(actual_files),
        exact_row_source_record_count=record_count,
        bundle_absent=bundle_absent,
        bundle_sha_absent=bundle_sha_absent,
    )
