"""Fail-closed validator for PR166-S2 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import ALLOWED_LIFECYCLE_STATUSES, ALLOWED_NO_FILL_REASONS, ALLOWED_READINESS_STATES, FORBIDDEN_STATUS_VALUES, LifecycleStatus
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
    "episode_id",
    "order_intent_id",
    "upstream_pr_refs",
    "upstream_artifact_refs",
    "upstream_row_refs",
    "upstream_value_refs",
    "source_roadmap_pr_refs",
    "source_artifact_refs",
    "source_row_refs",
    "input_shard_refs",
    "replay_paper_execution_status",
    "simulated_order_authority",
    "result_status",
    "replay_paper_net_edge_after_costs",
    "edge_lower_confidence_bound",
    "result_confidence_score",
    "tca_result_ref",
    "implementation_shortfall_ref",
    "fill_realism_score",
    "calibration_score",
    "no_leakage_audit_ref",
    "overfit_fdr_ref",
    "capacity_crowding_ref",
    "agent_duty_ref",
    "downstream_pr_refs",
    "downstream_artifact_refs",
    "downstream_agent_consumers",
    "owning_agent",
    "reviewer_or_challenger_agent",
    "validator_ref",
    "manifest_ref",
    "schema_ref",
    "authority_boundary_ref",
    "no_orphan_status",
    "terminal_status_flag",
    "terminal_status_reason",
    "deterministic_sort_key",
    "connector_dependency_class",
    "venue_semantic_dependency_class",
    "future_connector_pr_refs",
    "future_venue_readiness_route",
    "connector_binding_allowed_in_this_pr",
    "private_state_fetch_allowed_in_this_pr",
    "runtime_cash_receipt_allowed_in_this_pr",
    "source_truth_acceptance_allowed_in_this_pr",
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
    _validate_row_contracts(records, failures)
    _validate_manifest(reports, records, failures)
    _validate_summary(records, failures)
    _validate_retest_execution(records, failures)
    _validate_fill_model(records, failures)
    _validate_shard_input_audit(records, failures)
    _validate_authority(records, failures)
    _validate_compact_names(failures)
    _validate_status_drift(repo_root, reports, records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-S2 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-S2 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR166-S2 schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.REQUIRED_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR166-S2 upstream input: {filename}")


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
        _expect(payload.get("validation_status") == c.VALIDATION_STATUS, failures, f"{filename} validation_status mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} record_count mismatch")
        path = repo_root / c.GENERATED_DIR / filename
        _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds root report size limit")
        if payload.get("sharded_flag"):
            _expect(payload.get("records") == [], failures, f"{filename} compact root duplicates sharded rows")
            _expect(payload.get("records_omitted_for_sharding_flag") is True, failures, f"{filename} missing sharding omission flag")
            _expect(payload.get("shard_files"), failures, f"{filename} missing shard files")
        for shard_ref in payload.get("shard_files") or []:
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"{filename} missing shard {shard_ref}")
            if shard_path.exists():
                _expect(shard_path.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_ref} exceeds shard size limit")
                shard_payload = read_json(shard_path)
                _expect(shard_payload.get("parent_report_filename") == filename, failures, f"{shard_ref} parent mismatch")
                _expect(shard_payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{shard_ref} schema mismatch")


def _validate_row_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for field in ROW_REQUIRED_FIELDS:
                value = row.get(field)
                _expect(value not in ("", None), failures, f"{filename} row {row.get('row_id')} missing {field}")
                if field in {"upstream_pr_refs", "upstream_artifact_refs", "upstream_row_refs", "upstream_value_refs", "source_artifact_refs", "source_row_refs", "input_shard_refs", "downstream_pr_refs", "downstream_artifact_refs", "downstream_agent_consumers", "future_connector_pr_refs"}:
                    _expect(value != [], failures, f"{filename} row {row.get('row_id')} empty {field}")
            _expect(row.get("created_by_pr") == c.PR_ID, failures, f"{filename} row created_by_pr mismatch")
            _expect(row.get("roadmap_pr_id") == c.PR_ID, failures, f"{filename} row roadmap_pr_id mismatch")
            _expect(row.get("validator_ref") == c.VALIDATOR_REF, failures, f"{filename} row validator mismatch")
            _expect(row.get("manifest_ref") == c.MANIFEST_REF, failures, f"{filename} row manifest mismatch")
            _expect(row.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} row schema mismatch")
            _expect(row.get("simulated_order_authority") == "NONLIVE_REPLAY_PAPER_ONLY", failures, f"{filename} simulated authority mismatch")
            _expect(row.get("connector_binding_allowed_in_this_pr") is False, failures, f"{filename} row connector binding flag invalid")
            _expect(row.get("private_state_fetch_allowed_in_this_pr") is False, failures, f"{filename} row private state flag invalid")
            _expect(row.get("runtime_cash_receipt_allowed_in_this_pr") is False, failures, f"{filename} row runtime cash flag invalid")
            _expect(row.get("source_truth_acceptance_allowed_in_this_pr") is False, failures, f"{filename} row source truth flag invalid")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in c.DOWNSTREAM_PR_REFS, failures, f"{filename} row invalid downstream route {route}")
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR166_S2_ReportManifest.report.json"]
    root_rows = [row for row in manifest if row.get("manifest_entry_class") == "ROOT_REPORT"]
    shard_rows = [row for row in manifest if row.get("manifest_entry_class") == "SHARD_REPORT"]
    listed = {row["report_name"] + ".report.json" for row in root_rows}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "PR166-S2 manifest does not list exactly required root reports")
    expected_shards: dict[str, tuple[str, int]] = {}
    for filename, payload in reports.items():
        for shard in payload.get("shard_manifest_refs") or []:
            expected_shards[shard["shard_path"]] = (filename, int(shard["row_count"]))
    listed_shards = {row["report_path"] for row in shard_rows}
    _expect(listed_shards == set(expected_shards), failures, "PR166-S2 manifest does not list exactly required shard reports")
    for row in root_rows:
        filename = row["report_name"] + ".report.json"
        _expect(row["row_count"] == reports[filename]["record_count"], failures, f"manifest row count mismatch {filename}")
        _expect(row["schema_path"].endswith(c.REPORT_SCHEMA_REFS[filename]), failures, f"manifest schema mismatch {filename}")
    for row in shard_rows:
        parent, count = expected_shards.get(row["report_path"], ("", -1))
        _expect(row["parent_report_name"] + ".report.json" == parent, failures, f"manifest shard parent mismatch {row['report_path']}")
        _expect(row["row_count"] == count, failures, f"manifest shard row count mismatch {row['report_path']}")


def _validate_summary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_S2_FinalSummary.report.json"][0]
    equality = {
        "retest_universe_rows": len(records["PR166_S2_RetestUniverse.report.json"]),
        "replay_paper_episode_rows": len(records["PR166_S2_EpisodePlan.report.json"]),
        "order_intent_rows": len(records["PR166_S2_OrderIntentLedger.report.json"]),
        "fill_rows": len(records["PR166_S2_FillLedger.report.json"]),
        "no_fill_rows": len(records["PR166_S2_NoFillLedger.report.json"]),
        "net_edge_result_rows": len(records["PR166_S2_NetEdgeResultLedger.report.json"]),
        "shard_input_audit_rows": len(records["PR166_S2_ShardInputAudit.report.json"]),
        "execution_readiness_audit_rows": len(records["PR166_S2_ExecReadinessAudit.report.json"]),
        "agent_duty_ledger_rows": len(records["PR166_S2_AgentDutyLedger.report.json"]),
        "candidate_lifecycle_rows": len(records["PR166_S2_LifecycleLedger.report.json"]),
        "edge_decay_rows": len(records["PR166_S2_EdgeDecayLedger.report.json"]),
        "rank_aggregation_rows": len(records["PR166_S2_RankAggregationLedger.report.json"]),
        "alternative_execution_path_rows": len(records["PR166_S2_AltExecPathLedger.report.json"]),
        "time_to_resolution_risk_rows": len(records["PR166_S2_TTRiskLedger.report.json"]),
    }
    for field, expected in equality.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} mismatch")
    _expect(summary.get("pr166_sf_repaired_retest_ready_rows_consumed") == 3215, failures, "primary PR166-S2 handoff consumption must be 3215")
    _expect(summary.get("fill_rows", 0) + summary.get("no_fill_rows", 0) == summary.get("retest_universe_rows"), failures, "fill plus no-fill must cover primary universe")
    for field in ("metadata_only_rows", "placeholder_rows", "unknown_status_rows", "generic_blocker_rows", "orphan_rows", "authority_violation_count", *ZERO_AUTHORITY_KEYS):
        _expect(summary.get(field) == 0, failures, f"summary {field} must be zero")


def _validate_retest_execution(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    primary = records["PR166_S2_RetestUniverse.report.json"]
    _expect(len(primary) == 3215, failures, "PR166-S2 primary retest universe must be 3215")
    for filename in (
        "PR166_S2_EpisodePlan.report.json",
        "PR166_S2_OrderIntentLedger.report.json",
        "PR166_S2_StateLedger.report.json",
        "PR166_S2_TCAResultLedger.report.json",
        "PR166_S2_NetEdgeResultLedger.report.json",
        "PR166_S2_AttributionLedger.report.json",
        "PR166_S2_LifecycleLedger.report.json",
    ):
        _expect(len(records[filename]) == len(primary), failures, f"{filename} must cover primary universe")
    lifecycle_statuses = {row["candidate_lifecycle_status"] for row in records["PR166_S2_LifecycleLedger.report.json"]}
    _expect(lifecycle_statuses.issubset(ALLOWED_LIFECYCLE_STATUSES), failures, "invalid lifecycle status")
    for row in records["PR166_S2_ExecReadinessAudit.report.json"]:
        _expect(row["execution_readiness_state"] in ALLOWED_READINESS_STATES, failures, f"invalid readiness state {row['row_id']}")


def _validate_fill_model(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    nofills = records["PR166_S2_NoFillLedger.report.json"]
    fills = records["PR166_S2_FillLedger.report.json"]
    _expect(fills or nofills, failures, "fill/no-fill evidence missing")
    for row in records["PR166_S2_OrderIntentLedger.report.json"]:
        _expect(row["simulated_order_authority"] == "NONLIVE_REPLAY_PAPER_ONLY", failures, f"order intent live authority mismatch {row['row_id']}")
        _expect(row["live_order_authority_allowed"] is False, failures, f"order intent live flag invalid {row['row_id']}")
    for row in nofills:
        _expect(row["no_fill_reason"] in ALLOWED_NO_FILL_REASONS, failures, f"invalid no-fill reason {row['row_id']}")
        _expect(row["simulated_no_fill_receipt_status"] == "SIMULATED_NO_FILL_RECORDED_WITH_EXACT_REASON", failures, f"no-fill receipt invalid {row['row_id']}")
    for row in fills:
        _expect(row["simulated_fill_receipt_status"] == "SIMULATED_FILL_RECORDED_NONLIVE", failures, f"fill receipt invalid {row['row_id']}")
    positives = [row for row in records["PR166_S2_NetEdgeResultLedger.report.json"] if row["replay_paper_net_edge_after_costs"] > 0]
    for row in positives:
        _expect(row["positive_replay_paper_net_edge_label"] == "REPLAY_PAPER_POSITIVE_NET_EDGE_CANDIDATE_NOT_LIVE_PROFIT_EVIDENCE", failures, f"positive edge label invalid {row['row_id']}")
        _expect(row.get("profit_evidence_count", 0) == 0, failures, f"positive row profit evidence count invalid {row['row_id']}")


def _validate_shard_input_audit(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_S2_ShardInputAudit.report.json"]
    by_report = {row["upstream_report_ref"]: row for row in rows}
    for report in c.REQUIRED_INPUT_REPORTS:
        _expect(report in by_report, failures, f"shard input audit missing {report}")
    sharded = [row for row in rows if row["records_omitted_for_sharding_flag"]]
    _expect(sharded, failures, "shard input audit must include sharded upstream reports")
    for row in sharded:
        _expect(row["declared_shard_count"] == row["read_shard_count"], failures, f"shard count mismatch {row['upstream_report_ref']}")
        _expect(row["declared_total_row_count"] == row["read_total_row_count"], failures, f"row count mismatch {row['upstream_report_ref']}")
        _expect(row["continuation_allowed"] is True, failures, f"continuation not allowed {row['upstream_report_ref']}")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    audit = records["PR166_S2_AuthorityBoundaryAudit.report.json"][0]
    for key in ZERO_AUTHORITY_KEYS:
        _expect(audit.get(key, 0) == 0, failures, f"authority audit {key} must be zero")
    no_profit = records["PR166_S2_NoProfitEvidenceAudit.report.json"][0]
    _expect(no_profit["profit_evidence_count"] == 0, failures, "profit evidence count must be zero")


def _validate_compact_names(failures: list[str]) -> None:
    for schema_name in c.SCHEMA_FILENAMES:
        _expect(not schema_name.startswith("p_r166"), failures, f"letter-split schema name forbidden: {schema_name}")
        _expect("q_k_u" not in schema_name, failures, f"letter-split qku schema name forbidden: {schema_name}")
        _expect("t_c_a" not in schema_name, failures, f"letter-split tca schema name forbidden: {schema_name}")
        _expect("d_a_g" not in schema_name, failures, f"letter-split dag schema name forbidden: {schema_name}")
        _expect("k_p_i" not in schema_name, failures, f"letter-split kpi schema name forbidden: {schema_name}")
        _expect("s_f_feedback" not in schema_name, failures, f"letter-split sf schema name forbidden: {schema_name}")
    long_aliases = ("PositivePreferenceCandidateLedger", "NegativeMemoryCandidateLedger", "ConditionMemoryUpdateLedger", "ProbabilityCalibrationLedger", "MicrostructureOutcomeLedger", "LatencyLiquidityImpactLedger", "EdgeCaptureAttributionLedger", "ExecutionReadinessAudit", "OrderBookSnapshotLedger", "ResultDistributionLedger", "CandidateLifecycleLedger")
    for filename in c.REPORT_FILENAMES:
        for alias in long_aliases:
            _expect(alias not in filename, failures, f"long alias report forbidden: {filename}")


def _validate_status_drift(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        if filename == "PR166_S2_StatusEnumDriftAudit.report.json":
            continue
        for value in _flatten_values(payload):
            if "\\" in value:
                failures.append(f"{filename} contains backslash path/value: {value}")
            if value in FORBIDDEN_STATUS_VALUES:
                failures.append(f"{filename} contains forbidden status value: {value}")
    for schema_name in c.SCHEMA_FILENAMES:
        schema_text = (repo_root / c.SCHEMA_DIR / schema_name).read_text(encoding="utf-8")
        for token in FORBIDDEN_STATUS_VALUES:
            if f'"{token}"' in schema_text:
                failures.append(f"{schema_name} embeds forbidden status token {token}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    sha_paths = sorted((repo_root / c.GENERATED_DIR).glob("*.sha256"))
    _expect(not sha_paths, failures, f"generated sha256 artifacts found: {[str(path) for path in sha_paths[:5]]}")
    atomic_sha = repo_root / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
    _expect(not atomic_sha.exists(), failures, "AtomicRows.bundle.sha256 must not exist")


def _flatten_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_flatten_values(item))
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(_flatten_values(item))
        return out
    return []


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
