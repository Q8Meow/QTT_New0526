"""Fail-closed validator for PR166-SM2 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import ALLOWED_CONVERSION_STATES, ALLOWED_NO_ORPHAN_STATUSES, FORBIDDEN_STATUS_VALUES
from .io import read_json, records_from_report_payload, resolve_repo_relative
from .report_writer import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES
from .score_refresh import score_memory_refresh_score_v2


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
    "source_episode_id",
    "upstream_pr_refs",
    "upstream_artifact_refs",
    "upstream_row_refs",
    "upstream_value_refs",
    "source_roadmap_pr_refs",
    "source_artifact_refs",
    "source_row_refs",
    "input_shard_refs",
    "pre_refresh_score",
    "refreshed_score",
    "score_delta",
    "pre_refresh_memory_status",
    "refreshed_memory_status",
    "memory_delta_reason",
    "replay_paper_net_edge_after_costs",
    "edge_lower_confidence_bound",
    "result_confidence_score",
    "tca_result_ref",
    "cost_root_cause_ref",
    "calibration_ref",
    "fill_realism_ref",
    "no_fill_ref",
    "overfit_fdr_ref",
    "rank_stability_ref",
    "capacity_crowding_ref",
    "evidence_depth_ref",
    "shrinkage_ref",
    "ablation_ref",
    "orthogonal_edge_ref",
    "positive_seed_ref",
    "positive_driver_ref",
    "positive_family_ref",
    "convertible_negative_ref",
    "break_even_gap_ref",
    "quantum_priority_ref",
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
    _validate_manifest(reports, records, failures)
    _validate_row_contracts(records, failures)
    _validate_summary_counts(records, failures)
    _validate_score_formula(records, failures)
    _validate_conversion_coverage(records, failures)
    _validate_authority(records, failures)
    _validate_compact_names(repo_root, failures)
    _validate_status_drift(repo_root, reports, records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SM2 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-SM2 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR166-SM2 schema: {filename}")
        if filename.startswith("p_r166_s_m2"):
            failures.append(f"letter-split PR166-SM2 schema name forbidden: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.REQUIRED_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR166-SM2 upstream input: {filename}")


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
    manifest = records["PR166_SM2_ReportManifest.report.json"]
    root_rows = [row for row in manifest if row.get("manifest_entry_class") == "ROOT_REPORT"]
    shard_rows = [row for row in manifest if row.get("manifest_entry_class") == "SHARD_REPORT"]
    listed = {row["report_name"] + ".report.json" for row in root_rows}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "manifest root reports do not match PR166-SM2 required reports")
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
    for row in shard_rows:
        parent, count = expected_shards.get(row["report_path"], ("", -1))
        _expect(row["parent_report_name"] + ".report.json" == parent, failures, f"manifest shard parent mismatch {row['report_path']}")
        _expect(row["row_count"] == count, failures, f"manifest shard row count mismatch {row['report_path']}")


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
            _expect(row.get("no_orphan_status") in ALLOWED_NO_ORPHAN_STATUSES, failures, f"{filename} row invalid no_orphan_status")
            _expect(row.get("connector_binding_allowed_in_this_pr") is False, failures, f"{filename} connector binding flag invalid")
            _expect(row.get("private_state_fetch_allowed_in_this_pr") is False, failures, f"{filename} private state flag invalid")
            _expect(row.get("runtime_cash_receipt_allowed_in_this_pr") is False, failures, f"{filename} runtime cash flag invalid")
            _expect(row.get("source_truth_acceptance_allowed_in_this_pr") is False, failures, f"{filename} source truth flag invalid")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in c.DOWNSTREAM_PR_REFS, failures, f"{filename} row invalid downstream route {route}")
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")
            if "conversion_state" in row:
                _expect(row["conversion_state"] in ALLOWED_CONVERSION_STATES, failures, f"{filename} row invalid conversion state")


def _validate_summary_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_SM2_FinalSummary.report.json"][0]
    equality = {
        "refreshed_score_rows": len(records["PR166_SM2_ScoreRegistry.report.json"]),
        "refreshed_memory_rows": len(records["PR166_SM2_MemoryLedger.report.json"]),
        "rank_delta_rows": len(records["PR166_SM2_RankDeltaRegistry.report.json"]),
        "rank_aggregation_rows": len(records["PR166_SM2_RankAggregation.report.json"]),
        "positive_edge_memory_rows": len(records["PR166_SM2_PosEdgeRegistry.report.json"]),
        "negative_edge_memory_rows": len(records["PR166_SM2_NegEdgeRegistry.report.json"]),
        "all_negative_conversion_plan_rows": len(records["PR166_SM2_AllNegConvPlan.report.json"]),
        "edge_uplift_rows": len(records["PR166_SM2_EdgeUpliftLedger.report.json"]),
        "cost_cut_rows": len(records["PR166_SM2_CostCutLedger.report.json"]),
        "fill_boost_rows": len(records["PR166_SM2_FillBoostLedger.report.json"]),
        "calibration_boost_rows": len(records["PR166_SM2_CalibBoostLedger.report.json"]),
        "parameter_uplift_rows": len(records["PR166_SM2_ParamUpliftLedger.report.json"]),
        "conversion_agent_queue_rows": len(records["PR166_SM2_ConversionAgentQueue.report.json"]),
        "pr166_q_handoff_rows": len(records["PR166_SM2_PR166QHandoff.report.json"]),
        "pr167_handoff_rows": len(records["PR166_SM2_PR167Handoff.report.json"]),
        "pr165_d3_handoff_rows": len(records["PR166_SM2_PR165D3Handoff.report.json"]),
        "memory_dag_rows": len(records["PR166_SM2_MemoryDAGLedger.report.json"]),
        "score_explanation_rows": len(records["PR166_SM2_ScoreExplainLedger.report.json"]),
    }
    for field, expected in equality.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} mismatch")
    exact = {
        "pr166_s2_pr166_sm2_handoff_rows_consumed": 3215,
        "positive_replay_paper_rows_consumed": 2,
        "negative_replay_paper_rows_consumed": 3213,
        "all_negative_conversion_plan_rows": 3213,
        "true_positive_replay_paper_rows_from_PR166_S2": 2,
        "negative_replay_paper_rows_from_PR166_S2": 3213,
        "pr166_sf_r2_feedback_rows_consumed": 3213,
        "pr166_q_handoff_rows_consumed": 559,
        "pr167_handoff_rows_consumed": 2,
        "refreshed_score_rows": 3215,
        "refreshed_memory_rows": 3215,
    }
    for field, expected in exact.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} expected {expected}")
    for field in ("metadata_only_rows", "placeholder_rows", "unknown_status_rows", "generic_blocker_rows", "orphan_rows", "authority_violation_count", *ZERO_AUTHORITY_KEYS):
        _expect(summary.get(field) == 0, failures, f"summary {field} must be zero")
    _expect(summary.get("next_recommended_pr") == "PR166-SF-R2", failures, "next recommendation must prioritize repair backlog")
    _expect(summary.get("secondary_next_recommended_pr") == "PR166-Q", failures, "secondary recommendation must preserve quantum route")
    _expect("owner_audit_alpha_answer" in summary, failures, "summary missing owner alpha answer")
    _expect("owner_audit_connectivity_answer" in summary, failures, "summary missing owner connectivity answer")


def _validate_score_formula(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_SM2_ScoreRegistry.report.json"]
    ranks = sorted(int(row["refreshed_rank"]) for row in rows)
    _expect(ranks == list(range(1, len(rows) + 1)), failures, "score ranks are not contiguous")
    for row in rows:
        components = row.get("score_formula_component_values")
        _expect(isinstance(components, dict), failures, f"score components missing {row.get('row_id')}")
        if isinstance(components, dict):
            expected = score_memory_refresh_score_v2({key: float(value) for key, value in components.items()})
            _expect(abs(expected - float(row["score_memory_refresh_score_v2"])) < 0.00001, failures, f"score formula mismatch {row.get('row_id')}")
            _expect(abs(expected - float(row["refreshed_score"])) < 0.00001, failures, f"refreshed_score mismatch {row.get('row_id')}")
        _expect(row.get("gross_edge_only_ranking_used") is not True, failures, f"gross-only score detected {row.get('row_id')}")


def _validate_conversion_coverage(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    negatives = records["PR166_SM2_NegEdgeRegistry.report.json"]
    plan = records["PR166_SM2_AllNegConvPlan.report.json"]
    _expect(len(plan) == 3213, failures, "all-negative conversion plan must have 3213 rows")
    neg_ids = {row["candidate_packet_id"] for row in negatives}
    plan_ids = {row["candidate_packet_id"] for row in plan}
    _expect(plan_ids == neg_ids, failures, "all-negative conversion plan does not cover exactly negative rows")
    for row in plan:
        _expect(row["conversion_state"] != "", failures, f"conversion state missing {row['row_id']}")
        _expect(row["break_even_gap"] >= 0, failures, f"negative break-even gap {row['row_id']}")
        _expect(row["replay_paper_retest_required"] is True, failures, f"conversion row missing retest requirement {row['row_id']}")
        _expect(row["future_positive_result_claim_allowed_without_retest"] is False, failures, f"conversion row allows false positive claim {row['row_id']}")
        _expect(row["not_profit_evidence"] is True, failures, f"conversion row missing no-profit boundary {row['row_id']}")
    positives = records["PR166_SM2_PosEdgeRegistry.report.json"]
    _expect(len(positives) == 2, failures, "positive replay/paper row count must remain 2")
    expansions = records["PR166_SM2_PosExpansion.report.json"]
    _expect(expansions and all(row["counts_as_positive_replay_paper_result"] is False for row in expansions), failures, "positive expansions counted as positive results")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} nonzero {key}")
    authority = records["PR166_SM2_AuthorityAudit.report.json"][0]
    no_profit = records["PR166_SM2_NoProfitAudit.report.json"][0]
    for key in ZERO_AUTHORITY_KEYS:
        _expect(int(authority.get(key, 0) or 0) == 0, failures, f"authority audit nonzero {key}")
        _expect(int(no_profit.get(key, 0) or 0) == 0, failures, f"no-profit audit nonzero {key}")


def _validate_compact_names(repo_root: Path, failures: list[str]) -> None:
    generated = repo_root / c.GENERATED_DIR
    forbidden = (
        "PR166_SM2_PRFileConnectivityAudit.report.json",
        "PR166_SM2_RowValueConnectivityAudit.report.json",
        "PR166_SM2_AuthorityBoundaryAudit.report.json",
        "PR166_SM2_NoProfitEvidenceAudit.report.json",
        "PR166_SM2_OrphanArtifactAudit.report.json",
    )
    for name in forbidden:
        _expect(not (generated / name).exists(), failures, f"old long-name alias must not exist: {name}")
    for path in (repo_root / c.SHARD_DIR).glob("*.report.json"):
        _expect(".part_" in path.name, failures, f"PR166-SM2 shard name missing compact part token: {path.name}")


def _validate_status_drift(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    audit = records["PR166_SM2_StatusDriftAudit.report.json"][0]
    _expect(audit["unauthorized_token_occurrence_count"] == 0, failures, "status drift audit nonzero")
    allowed_audit_path = (repo_root / c.GENERATED_DIR / "PR166_SM2_StatusDriftAudit.report.json").as_posix()
    for filename, payload in reports.items():
        for token in _exact_forbidden_values(filename, payload):
            failures.append(f"forbidden token {token} found outside explicit status audit field in {filename}")
        for shard_ref in payload.get("shard_files") or []:
            shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
            for token in _exact_forbidden_values(shard_ref, shard_payload):
                failures.append(f"forbidden token {token} found outside explicit status audit field in {shard_ref}")
    _expect(allowed_audit_path.endswith("PR166_SM2_StatusDriftAudit.report.json"), failures, "status audit path mismatch")


def _exact_forbidden_values(filename: str, payload: Any) -> list[str]:
    found: list[str] = []

    def walk(value: Any, path: tuple[str, ...]) -> None:
        if filename.endswith("PR166_SM2_StatusDriftAudit.report.json") and path and path[-1] == "forbidden_scope_audit_tokens_checked":
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


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    for path in (repo_root / c.GENERATED_DIR).glob("PR166_SM2*.sha256"):
        failures.append(f"forbidden PR166-SM2 sha256 sidecar created: {path}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
