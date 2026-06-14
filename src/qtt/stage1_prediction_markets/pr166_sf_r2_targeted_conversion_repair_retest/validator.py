"""Fail-closed validator for PR166-SF-R2 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import ZERO_AUTHORITY_KEYS
from .enums import ALLOWED_CONVERSION_STATUSES, ALLOWED_CONVERSION_TIERS, ALLOWED_NO_ORPHAN_STATUSES, FORBIDDEN_STATUS_VALUES
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
    "pr166_sm2_conversion_plan_ref",
    "pr166_sm2_repair_priority_ref",
    "pr166_sm2_break_even_gap_ref",
    "pr166_s2_retest_result_ref",
    "repair_action_id",
    "repair_action_type",
    "repair_feasibility_score",
    "pre_repair_net_edge_after_costs",
    "repaired_preview_net_edge_after_costs",
    "retested_net_edge_after_costs",
    "edge_lower_confidence_bound",
    "result_confidence_score",
    "cost_cut_ref",
    "fill_boost_ref",
    "calibration_boost_ref",
    "parameter_uplift_ref",
    "quantum_repair_ref",
    "tca_ref",
    "fill_ref",
    "no_fill_ref",
    "calibration_ref",
    "microstructure_ref",
    "overfit_fdr_ref",
    "capacity_crowding_ref",
    "rank_stability_ref",
    "conversion_status",
    "conversion_reason",
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
    "repair_frontier_ref",
    "repair_ablation_ref",
    "repair_sensitivity_ref",
    "conversion_proof_ref",
    "cost_floor_ref",
    "fill_probability_model_ref",
    "calibration_uplift_proof_ref",
    "parameter_bound_audit_ref",
    "quantum_objective_map_ref",
    "holdout_replay_ref",
    "positive_capacity_ref",
    "launch_candidate_filter_ref",
    "runtime_safety_handoff_ref",
    "deterministic_sort_key",
    "connector_dependency_class",
    "venue_semantic_dependency_class",
    "future_connector_pr_refs",
    "connector_binding_allowed_in_this_pr",
    "live_order_authority_allowed_in_this_pr",
    "profit_evidence_allowed_in_this_pr",
    "quantum_backend_execution_allowed_in_this_pr",
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
    _validate_repair_coverage(records, failures)
    _validate_conversion_truth(records, failures)
    _validate_summary_counts(records, failures)
    _validate_authority(records, failures)
    _validate_status_drift(repo_root, reports, records, failures)
    _validate_compact_names(repo_root, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-SF-R2 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-SF-R2 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / filename).exists():
            failures.append(f"missing PR166-SF-R2 schema: {filename}")
        if filename.startswith("p_r166_s_f_r2"):
            failures.append(f"letter-split PR166-SF-R2 schema name forbidden: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.REQUIRED_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR166-SF-R2 upstream input: {filename}")


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
    manifest = records["PR166_SF_R2_ReportManifest.report.json"]
    root_rows = [row for row in manifest if row.get("manifest_entry_class") == "ROOT_REPORT"]
    shard_rows = [row for row in manifest if row.get("manifest_entry_class") == "SHARD_REPORT"]
    listed = {row["report_name"] + ".report.json" for row in root_rows}
    _expect(listed == set(c.REPORT_FILENAMES), failures, "manifest root reports do not match PR166-SF-R2 required reports")
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
            _expect(row.get("live_order_authority_allowed_in_this_pr") is False, failures, f"{filename} live authority flag invalid")
            _expect(row.get("profit_evidence_allowed_in_this_pr") is False, failures, f"{filename} profit evidence flag invalid")
            _expect(row.get("quantum_backend_execution_allowed_in_this_pr") is False, failures, f"{filename} quantum backend flag invalid")
            for route in row.get("downstream_pr_refs") or []:
                _expect(route in c.DOWNSTREAM_PR_REFS, failures, f"{filename} row invalid downstream route {route}")
            for key in ZERO_AUTHORITY_KEYS:
                _expect(int(row.get(key, 0) or 0) == 0, failures, f"{filename} row nonzero authority key {key}")
            status = row.get("conversion_status")
            if filename not in c.SUMMARY_REPORTS and status:
                _expect(status in ALLOWED_CONVERSION_STATUSES, failures, f"{filename} row invalid conversion_status {status}")
            tier = row.get("conversion_tier")
            if tier:
                _expect(tier in ALLOWED_CONVERSION_TIERS, failures, f"{filename} row invalid conversion_tier {tier}")


def _validate_repair_coverage(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    universe = records["PR166_SF_R2_RepairUniverse.report.json"]
    _expect(len(universe) == 3213, failures, "repair universe must cover 3213 negative rows")
    all_neg_ids = {row["candidate_packet_id"] for row in records["PR166_SF_R2_AllNegIntake.report.json"]}
    universe_ids = {row["candidate_packet_id"] for row in universe}
    _expect(all_neg_ids == universe_ids, failures, "all-negative intake and repair universe candidate sets differ")
    for report in (
        "PR166_SF_R2_RepairActionLedger.report.json",
        "PR166_SF_R2_RepairedPacketRegistry.report.json",
        "PR166_SF_R2_RetestUniverse.report.json",
        "PR166_SF_R2_ConvProof.report.json",
        "PR166_SF_R2_RepairFrontier.report.json",
        "PR166_SF_R2_HoldoutReplay.report.json",
    ):
        ids = {row["candidate_packet_id"] for row in records[report]}
        _expect(ids == universe_ids, failures, f"{report} does not cover every repair universe row")
    outcomes = (
        len(records["PR166_SF_R2_PosConversion.report.json"])
        + len(records["PR166_SF_R2_StillNegative.report.json"])
        + len(records["PR166_SF_R2_NoFillLedger.report.json"])
        + len(records["PR166_SF_R2_TerminalRows.report.json"])
    )
    _expect(outcomes == 3213, failures, "terminal outcome registries do not partition 3213 rows")


def _validate_conversion_truth(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_SF_R2_PosConversion.report.json"]:
        _expect(row["conversion_status"] == "REPAIRED_AND_RETESTED_POSITIVE", failures, f"positive row bad status {row['row_id']}")
        _expect(float(row["retested_net_edge_after_costs"]) > 0, failures, f"positive row nonpositive retested edge {row['row_id']}")
        _expect(row.get("preview_only_conversion") is False, failures, f"positive row preview-only {row['row_id']}")
        _expect(row.get("profit_evidence_count", 0) == 0, failures, f"positive row profit evidence {row['row_id']}")
        _expect(row.get("converted_positive_label") == "REPAIRED_REPLAY_PAPER_POSITIVE_EDGE_NOT_PROFIT_EVIDENCE", failures, f"positive row label mismatch {row['row_id']}")
    for row in records["PR166_SF_R2_StillNegative.report.json"]:
        _expect(float(row["retested_net_edge_after_costs"]) <= 0, failures, f"still-negative row positive edge {row['row_id']}")
    for row in records["PR166_SF_R2_NoFillLedger.report.json"]:
        _expect(row["conversion_status"] == "REPAIRED_AND_NO_FILL", failures, f"no-fill row bad status {row['row_id']}")
        _expect(row["no_fill_ref"] != c.NOT_APPLICABLE_ID, failures, f"no-fill row missing no_fill_ref {row['row_id']}")
    proofs = records["PR166_SF_R2_ConvProof.report.json"]
    _expect(len(proofs) == 3213, failures, "conversion proof ledger must cover all 3213 rows")
    for row in proofs:
        _expect(row.get("preview_only_repair_estimate") is False, failures, f"proof row preview-only {row['row_id']}")
        _expect(len(row.get("conversion_proof_chain") or []) >= 7, failures, f"proof chain too short {row['row_id']}")
    launch_rows = records["PR166_SF_R2_LaunchCandidateFilter.report.json"]
    for row in launch_rows:
        _expect(row.get("launch_authorized") is False, failures, f"launch row authorized live {row['row_id']}")
        _expect(row.get("future_launch_candidate_label") != "LIVE_CANARY_APPROVED", failures, f"launch row forbidden label {row['row_id']}")


def _validate_summary_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR166_SF_R2_FinalSummary.report.json"][0]
    equality = {
        "pr166_sm2_handoff_rows": len(records["PR166_SF_R2_HandoffIntake.report.json"]),
        "all_negative_conversion_plan_rows": len(records["PR166_SF_R2_AllNegIntake.report.json"]),
        "repaired_candidate_packet_rows": len(records["PR166_SF_R2_RepairedPacketRegistry.report.json"]),
        "converted_positive_rows": len(records["PR166_SF_R2_PosConversion.report.json"]),
        "still_negative_rows": len(records["PR166_SF_R2_StillNegative.report.json"]),
        "no_fill_rows": len(records["PR166_SF_R2_NoFillLedger.report.json"]),
        "terminal_rows": len(records["PR166_SF_R2_TerminalRows.report.json"]),
        "repair_failure_rows": len(records["PR166_SF_R2_RepairFailure.report.json"]),
        "repair_frontier_rows": len(records["PR166_SF_R2_RepairFrontier.report.json"]),
        "repair_ablation_rows": len(records["PR166_SF_R2_RepairAblation.report.json"]),
        "repair_sensitivity_rows": len(records["PR166_SF_R2_RepairSensitivity.report.json"]),
        "conversion_proof_rows": len(records["PR166_SF_R2_ConvProof.report.json"]),
        "quantum_objective_map_rows": len(records["PR166_SF_R2_QuantumObjectiveMap.report.json"]),
        "holdout_replay_rows": len(records["PR166_SF_R2_HoldoutReplay.report.json"]),
        "launch_candidate_filter_rows": len(records["PR166_SF_R2_LaunchCandidateFilter.report.json"]),
        "runtime_safety_handoff_rows": len(records["PR166_SF_R2_RuntimeSafetyHandoff.report.json"]),
        "pr166_q_handoff_rows": len(records["PR166_SF_R2_PR166QHandoff.report.json"]),
        "pr166_sm3_handoff_rows": len(records["PR166_SF_R2_PR166SM3Handoff.report.json"]),
        "pr165_d3_handoff_rows": len(records["PR166_SF_R2_PR165D3Handoff.report.json"]),
        "pr167_handoff_rows": len(records["PR166_SF_R2_PR167Handoff.report.json"]),
    }
    for field, expected in equality.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} mismatch")
    exact = {
        "pr166_sm2_handoff_rows": 3213,
        "all_negative_conversion_plan_rows": 3213,
        "repaired_candidate_packet_rows": 3213,
        "repair_frontier_rows": 3213,
        "conversion_proof_rows": 3213,
        "holdout_replay_rows": 3213,
        "pr166_q_handoff_rows": 559,
    }
    for field, expected in exact.items():
        _expect(summary.get(field) == expected, failures, f"summary {field} expected {expected}")
    _expect(summary.get("converted_positive_rows", 0) > 0, failures, "expected at least one repaired replay/paper positive")
    _expect(summary.get("next_recommended_pr") in {"PR166-SM3", "PR166-Q", "PR166-SF-R3"}, failures, "invalid next recommendation")
    _expect(summary.get("secondary_next_recommended_pr") == "PR166-Q", failures, "secondary next recommendation must be PR166-Q")
    for field in ("metadata_only_count", "placeholder_count", "unknown_status_count", "orphan_count", "authority_violation_count", *ZERO_AUTHORITY_KEYS):
        _expect(summary.get(field) == 0, failures, f"summary {field} must be zero")


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
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    audit = records["PR166_SF_R2_StatusDriftAudit.report.json"][0]
    _expect(audit["unauthorized_token_occurrence_count"] == 0, failures, "status drift audit nonzero")
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
        if filename.endswith("PR166_SF_R2_StatusDriftAudit.report.json") and path and path[-1] == "forbidden_scope_audit_tokens_checked":
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
        "PR166_SF_R2_PRFileConnectivityAudit.report.json",
        "PR166_SF_R2_RowValueConnectivityAudit.report.json",
        "PR166_SF_R2_AuthorityBoundaryAudit.report.json",
        "PR166_SF_R2_NoProfitEvidenceAudit.report.json",
        "PR166_SF_R2_OrphanArtifactAudit.report.json",
    )
    for name in forbidden:
        _expect(not (generated / name).exists(), failures, f"old long-name alias must not exist: {name}")
    for path in (repo_root / c.SHARD_DIR).glob("*.report.json"):
        _expect(".part_" in path.name, failures, f"PR166-SF-R2 shard name missing compact part token: {path.name}")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    for path in (repo_root / c.GENERATED_DIR).glob("PR166_SF_R2*.sha256"):
        failures.append(f"forbidden PR166-SF-R2 sha256 sidecar created: {path}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
