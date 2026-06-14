"""Fail-closed validator for PR166-SM3 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import (
    ALLOWED_DOWNSTREAM_ROUTES,
    ALLOWED_EVIDENCE_CLASSES,
    ALLOWED_LINEAGE_CONFLICT_STATUSES,
    ALLOWED_LINEAGE_STATUSES,
    ALLOWED_MEMORY_UPDATE_TYPES,
    ALLOWED_NO_ORPHAN_STATUSES,
    FORBIDDEN_STATUS_VALUES,
)
from .io import read_json, records_from_report_payload, resolve_repo_relative
from .report_writer import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


ROW_REQUIRED_FIELDS = (
    "artifact_id",
    "row_id",
    "created_by_pr",
    "roadmap_pr_id",
    "candidate_packet_id",
    "qku_id",
    "formula_id",
    "algorithm_id",
    "parameter_stack_id",
    "condition_fingerprint_id",
    "scenario_group_id",
    "upstream_pr_refs",
    "upstream_artifact_refs",
    "upstream_row_refs",
    "upstream_value_refs",
    "source_roadmap_pr_refs",
    "source_artifact_refs",
    "source_row_refs",
    "input_shard_refs",
    "pr166_sf_r2_result_ref",
    "pr166_sf_r2_conversion_proof_ref",
    "pr166_sf_r2_holdout_ref",
    "pr166_sf_r2_tca_ref",
    "pr166_sf_r2_quantum_ref",
    "pr166_sm2_score_ref",
    "pr166_sm2_memory_ref",
    "prior_pr166_sm_score_ref",
    "prior_pr166_sm_memory_ref",
    "prior_pr166_sm2_score_ref",
    "prior_pr166_sm2_memory_ref",
    "prior_pr166_sm2_conversion_plan_ref",
    "prior_pr166_sf_r2_result_ref",
    "score_delta_from_pr166_sm",
    "score_delta_from_pr166_sm2",
    "memory_delta_from_pr166_sm",
    "memory_delta_from_pr166_sm2",
    "evidence_lineage_status",
    "lineage_conflict_status",
    "lineage_conflict_resolution",
    "lineage_audit_ref",
    "score_delta_lineage_ref",
    "memory_delta_lineage_ref",
    "lineage_conflict_ref",
    "downstream_owner_agent",
    "downstream_consumer_pr",
    "score_policy_ref",
    "memory_policy_ref",
    "prior_score",
    "refreshed_score",
    "score_delta",
    "memory_update_type",
    "memory_scope",
    "memory_decay_policy",
    "memory_supersession_policy",
    "retry_cooldown_suppression_policy",
    "evidence_class",
    "replay_paper_positive_flag",
    "profit_evidence_allowed_in_this_pr",
    "live_order_authority_allowed_in_this_pr",
    "connector_binding_allowed_in_this_pr",
    "quantum_backend_execution_allowed_in_this_pr",
    "edge_lower_confidence_bound",
    "result_confidence_score",
    "holdout_robustness_score",
    "tca_score_ref",
    "fill_ref",
    "no_fill_ref",
    "calibration_ref",
    "microstructure_ref",
    "overfit_fdr_ref",
    "capacity_crowding_ref",
    "rank_stability_ref",
    "quantum_readiness_ref",
    "qku_combo_score_ref",
    "best_combo_ref",
    "still_neg_recovery_ref",
    "positive_expansion_queue_ref",
    "evidence_quality_ref",
    "positive_durability_ref",
    "alpha_attribution_ref",
    "ic_decay_ref",
    "deflated_metric_ref",
    "model_risk_ref",
    "qku_hypergraph_ref",
    "combo_optimizer_ref",
    "quantum_qku_portfolio_ref",
    "quantum_fallback_ref",
    "latency_budget_ref",
    "hot_path_cache_ref",
    "selection_frontier_ref",
    "agent_consumer_map_ref",
    "row_dag_ref",
    "owner_review_queue_ref",
    "live_prep_needs_ref",
    "replay_paper_lane_map_ref",
    "quantum_combo_ready_ref",
    "score_explain_ref",
    "downstream_pr_refs",
    "downstream_artifact_refs",
    "downstream_agent_consumers",
    "owning_agent",
    "reviewer_or_challenger_agent",
    "validator_ref",
    "schema_ref",
    "manifest_ref",
    "authority_boundary_ref",
    "no_orphan_status",
    "terminal_status_flag",
    "terminal_status_reason",
    "deterministic_sort_key",
    "connector_dependency_class",
    "venue_semantic_dependency_class",
    "future_connector_pr_refs",
    "future_venue_readiness_route",
)


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: records_from_report_payload(repo_root, payload) for filename, payload in reports.items()}
    _validate_payload_contracts(repo_root, reports, records, failures)
    _validate_manifest(reports, records, failures)
    _validate_row_contracts(records, failures)
    _validate_row_counts(records, failures)
    _validate_score_memory(records, failures)
    _validate_authority(records, failures)
    _validate_status_drift(repo_root, reports, failures)
    _validate_compact_names(repo_root, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SM3 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-SM3 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        path = repo_root / c.SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SM3 schema: {filename}")
        if filename.startswith("p_r166_s_m3"):
            failures.append(f"letter-split PR166-SM3 schema name forbidden: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.STRICT_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR166-SM3 upstream input: {filename}")


def _validate_payload_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("roadmap_pr_id") == c.PR_ID, failures, f"{filename} roadmap_pr_id mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("authority_boundary_ref") == c.AUTHORITY_BOUNDARY_REF, failures, f"{filename} authority boundary mismatch")
        _expect(payload.get("validation_status") == c.VALIDATION_STATUS, failures, f"{filename} validation status mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema ref mismatch")
        _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} record_count mismatch")
        path = repo_root / c.GENERATED_DIR / filename
        _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} root report exceeds size limit")
        if filename in c.ROW_LEVEL_REPORTS:
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("records") == [], failures, f"{filename} compact root duplicated sharded rows")
            _expect(payload.get("records_omitted_for_sharding_flag") is True, failures, f"{filename} missing omitted sharding flag")
            if payload.get("record_count", 0):
                _expect(payload.get("shard_files"), failures, f"{filename} missing shard files")
        for shard_ref in payload.get("shard_files") or []:
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"{filename} missing shard {shard_ref}")
            if shard_path.exists():
                _expect(shard_path.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_ref} exceeds shard size limit")
                shard_payload = read_json(shard_path)
                _expect(shard_payload.get("parent_report_filename") == filename, failures, f"{shard_ref} parent mismatch")
                _expect(shard_payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{shard_ref} schema mismatch")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR166_SM3_ReportManifest.report.json"]
    root_rows = [row for row in manifest if row.get("manifest_entry_class") == "ROOT_REPORT"]
    shard_rows = [row for row in manifest if row.get("manifest_entry_class") == "SHARD_REPORT"]
    listed = {row["report_name"] + ".report.json" for row in root_rows}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "manifest root reports do not match PR166-SM3 required reports")
    expected_shards: dict[str, tuple[str, int]] = {}
    for filename, payload in reports.items():
        for shard in payload.get("shard_manifest_refs") or []:
            expected_shards[shard["shard_path"]] = (filename, int(shard["row_count"]))
    listed_shards = {row["report_path"] for row in shard_rows}
    _expect(listed_shards == set(expected_shards), failures, "manifest shard reports do not match generated shards")
    for row in root_rows:
        filename = row["report_name"] + ".report.json"
        _expect(row["row_count"] == reports[filename]["record_count"], failures, f"manifest row count mismatch {filename}")
        _expect(row["schema_path"].endswith(c.REPORT_SCHEMA_REFS[filename]), failures, f"manifest schema mismatch {filename}")


def _validate_row_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for field in ROW_REQUIRED_FIELDS:
                value = row.get(field)
                _expect(value not in ("", None), failures, f"{filename} row {row.get('row_id')} missing {field}")
                if field in {
                    "upstream_pr_refs",
                    "upstream_artifact_refs",
                    "upstream_row_refs",
                    "source_roadmap_pr_refs",
                    "source_artifact_refs",
                    "source_row_refs",
                    "input_shard_refs",
                    "downstream_pr_refs",
                    "downstream_artifact_refs",
                    "downstream_agent_consumers",
                    "future_connector_pr_refs",
                }:
                    _expect(value != [], failures, f"{filename} row {row.get('row_id')} empty {field}")
            _expect(row.get("created_by_pr") == c.PR_ID, failures, f"{filename} row created_by_pr mismatch")
            _expect(row.get("roadmap_pr_id") == c.PR_ID, failures, f"{filename} row roadmap_pr_id mismatch")
            _expect(row.get("validator_ref") == c.VALIDATOR_REF, failures, f"{filename} row validator mismatch")
            _expect(row.get("manifest_ref") == c.MANIFEST_REF, failures, f"{filename} row manifest mismatch")
            _expect(row.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} row schema mismatch")
            _expect(row.get("authority_boundary_ref") == c.AUTHORITY_BOUNDARY_REF, failures, f"{filename} row authority boundary mismatch")
            _expect(row.get("no_orphan_status") in ALLOWED_NO_ORPHAN_STATUSES, failures, f"{filename} row invalid no_orphan_status {row.get('no_orphan_status')}")
            _expect(row.get("evidence_class") in ALLOWED_EVIDENCE_CLASSES, failures, f"{filename} row invalid evidence_class {row.get('evidence_class')}")
            _expect(row.get("memory_update_type") in ALLOWED_MEMORY_UPDATE_TYPES, failures, f"{filename} row invalid memory_update_type {row.get('memory_update_type')}")
            _expect(row.get("evidence_lineage_status") in ALLOWED_LINEAGE_STATUSES, failures, f"{filename} row invalid lineage status {row.get('evidence_lineage_status')}")
            _expect(row.get("lineage_conflict_status") in ALLOWED_LINEAGE_CONFLICT_STATUSES, failures, f"{filename} row invalid conflict status {row.get('lineage_conflict_status')}")
            _expect(row.get("connector_binding_allowed_in_this_pr") is False, failures, f"{filename} connector binding flag invalid")
            _expect(row.get("live_order_authority_allowed_in_this_pr") is False, failures, f"{filename} live authority flag invalid")
            _expect(row.get("profit_evidence_allowed_in_this_pr") is False, failures, f"{filename} profit evidence flag invalid")
            _expect(row.get("quantum_backend_execution_allowed_in_this_pr") is False, failures, f"{filename} quantum backend flag invalid")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in ALLOWED_DOWNSTREAM_ROUTES, failures, f"{filename} row invalid downstream route {route}")
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")


def _validate_row_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    expected = {
        "PR166_SM3_ResultIntake.report.json": 3213,
        "PR166_SM3_PosEvidence.report.json": 150,
        "PR166_SM3_StillNegMemory.report.json": 2882,
        "PR166_SM3_NoFillMemory.report.json": 183,
        "PR166_SM3_ConvProofMemory.report.json": 3213,
        "PR166_SM3_HoldoutMemory.report.json": 3213,
        "PR166_SM3_ScoreRegistry.report.json": 3215,
        "PR166_SM3_MemoryLedger.report.json": 3215,
        "PR166_SM3_StillNegRecovery.report.json": 3065,
        "PR166_SM3_QuantumPriority.report.json": 559,
        "PR166_SM3_PR166QHandoff.report.json": 559,
        "PR166_SM3_LineageAudit.report.json": 3215,
        "PR166_SM3_ScoreDeltaLineage.report.json": 3215,
        "PR166_SM3_MemoryDeltaLineage.report.json": 3215,
        "PR166_SM3_LineageConflict.report.json": 3215,
    }
    for filename, count in expected.items():
        _expect(len(records[filename]) == count, failures, f"{filename} expected {count} rows")
    summary = records["PR166_SM3_FinalSummary.report.json"][0]
    equality = {
        "pr166_sf_r2_positive_conversion_rows": 148,
        "prior_positive_rows": 2,
        "total_positive_evidence_rows": len(records["PR166_SM3_PosEvidence.report.json"]),
        "still_negative_rows": len(records["PR166_SM3_StillNegMemory.report.json"]),
        "no_fill_rows": len(records["PR166_SM3_NoFillMemory.report.json"]),
        "conversion_proof_rows": len(records["PR166_SM3_ConvProofMemory.report.json"]),
        "holdout_replay_rows": len(records["PR166_SM3_HoldoutMemory.report.json"]),
        "refreshed_score_rows": len(records["PR166_SM3_ScoreRegistry.report.json"]),
        "refreshed_memory_rows": len(records["PR166_SM3_MemoryLedger.report.json"]),
        "still_neg_recovery_rows": len(records["PR166_SM3_StillNegRecovery.report.json"]),
        "qku_combo_score_rows": len(records["PR166_SM3_QKUComboScore.report.json"]),
        "best_combo_rows": len(records["PR166_SM3_BestComboRegistry.report.json"]),
        "quantum_priority_rows": len(records["PR166_SM3_QuantumPriority.report.json"]),
        "lineage_audit_rows": len(records["PR166_SM3_LineageAudit.report.json"]),
        "score_delta_lineage_rows": len(records["PR166_SM3_ScoreDeltaLineage.report.json"]),
        "memory_delta_lineage_rows": len(records["PR166_SM3_MemoryDeltaLineage.report.json"]),
        "lineage_conflict_rows": len(records["PR166_SM3_LineageConflict.report.json"]),
    }
    for field, expected_value in equality.items():
        _expect(summary.get(field) == expected_value, failures, f"summary {field} mismatch")
    for field in ZERO_AUTHORITY_KEYS:
        _expect(summary.get(field, 0) == 0, failures, f"summary {field} must be zero")


def _validate_score_memory(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    score_rows = records["PR166_SM3_ScoreRegistry.report.json"]
    positive_rows = records["PR166_SM3_PosEvidence.report.json"]
    _expect(sum(1 for row in positive_rows if row.get("replay_paper_positive_flag") is True) == 150, failures, "positive evidence flags must total 150")
    for row in score_rows[:50]:
        vector = row.get("score_component_vector")
        _expect(isinstance(vector, dict) and len(vector) >= 20, failures, f"score row missing component vector {row.get('row_id')}")
        _expect(row.get("score_explain_ref") not in ("", None), failures, f"score row missing score_explain_ref {row.get('row_id')}")
    for row in records["PR166_SM3_QuantumPriority.report.json"]:
        _expect(row.get("quantum_status") == "QUANTUM_COMPARATOR_READY_NOT_BACKEND_EXECUTED", failures, f"quantum row bad status {row.get('row_id')}")
        _expect(row.get("quantum_backend_execution_allowed_in_this_pr") is False, failures, f"quantum row backend flag invalid {row.get('row_id')}")
    for row in records["PR166_SM3_LivePrepNeeds.report.json"]:
        _expect(row.get("live_prep_need_status") == "FUTURE_REFERENCE_ONLY_NO_LIVE_IMPLEMENTATION", failures, f"live prep row bad status {row.get('row_id')}")
        _expect(row.get("live_order_authority_allowed_in_this_pr") is False, failures, f"live prep row live flag invalid {row.get('row_id')}")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} nonzero {key}")
            _expect(row.get("live_canary_approved") is not True, failures, f"{filename} live canary approved")
            _expect(row.get("owner_approved_live") is not True, failures, f"{filename} owner approved live")
            _expect(row.get("source_truth_accepted") is not True, failures, f"{filename} source truth accepted")
            _expect(row.get("connector_truth_accepted") is not True, failures, f"{filename} connector truth accepted")
            _expect(row.get("quantum_backend_executed") is not True, failures, f"{filename} quantum backend executed")
            _expect(row.get("quantum_advantage_proven") is not True, failures, f"{filename} quantum advantage proven")


def _validate_status_drift(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        for token in _exact_forbidden_values(filename, payload):
            failures.append(f"forbidden token {token} found outside explicit status audit field in {filename}")
        for shard_ref in payload.get("shard_files") or []:
            shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
            for token in _exact_forbidden_values(shard_ref, shard_payload):
                failures.append(f"forbidden token {token} found outside explicit status audit field in {shard_ref}")


def _exact_forbidden_values(filename: str, payload: Any) -> list[str]:
    found: list[str] = []

    def walk(value: Any, path: tuple[str, ...]) -> None:
        if filename.endswith("PR166_SM3_StatusDriftAudit.report.json") and path and path[-1] == "forbidden_scope_audit_tokens_checked":
            return
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, (*path, str(key)))
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, (*path, str(index)))
            return
        if isinstance(value, str) and value in FORBIDDEN_STATUS_VALUES:
            found.append(value)

    walk(payload, ())
    return found


def _validate_compact_names(repo_root: Path, failures: list[str]) -> None:
    generated = repo_root / c.GENERATED_DIR
    forbidden = (
        "PR166_SM3_PRFileConnectivityAudit.report.json",
        "PR166_SM3_RowValueConnectivityAudit.report.json",
        "PR166_SM3_AuthorityBoundaryAudit.report.json",
        "PR166_SM3_NoProfitEvidenceAudit.report.json",
        "PR166_SM3_OrphanArtifactAudit.report.json",
    )
    for name in forbidden:
        _expect(not (generated / name).exists(), failures, f"old long-name alias must not exist: {name}")
    for path in (repo_root / c.SHARD_DIR).glob("*.report.json"):
        _expect(".part_" in path.name, failures, f"PR166-SM3 shard name missing compact part token: {path.name}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    for path in (repo_root / c.GENERATED_DIR).glob("PR166_SM3*.sha256"):
        failures.append(f"forbidden PR166-SM3 sha256 sidecar created: {path}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
