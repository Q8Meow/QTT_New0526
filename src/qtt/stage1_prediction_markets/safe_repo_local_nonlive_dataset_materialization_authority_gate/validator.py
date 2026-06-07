"""Fail-closed PR162A artifact validator."""

from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
from pathlib import Path
from typing import Any

from . import constants as c
from .dataset_normalization import NORMALIZED_FIELDS
from .json_io import read_json, read_jsonl, records_from_payload
from .loaders import load_pr161f_records
from .paths import normalize_shard_ref, resolve_repo_relative


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))

    _validate_common_report_contracts(reports, failures)
    manifest_by_report = _manifest_by_report(
        reports[c.SHARD_MANIFEST_REPORT_FILENAME],
        failures,
    )
    _validate_manifest_paths(repo_root, reports, manifest_by_report, failures)
    loaded = {
        filename: _load_records(repo_root, filename, reports[filename], manifest_by_report, failures)
        for filename in c.REPORT_FILENAMES
        if filename != c.SHARD_MANIFEST_REPORT_FILENAME
    }
    if failures:
        return ValidationResult(False, tuple(failures))

    _validate_mandatory_inputs(repo_root, reports, failures)
    _validate_pr161f_input_consumption(repo_root, loaded, failures)
    _validate_source_discovery(loaded, failures)
    _validate_fetch_plans(repo_root, loaded, failures)
    _validate_dataset_materialization(repo_root, loaded, failures)
    _validate_normalized_inventory(repo_root, loaded, failures)
    _validate_data_quality_and_missing_values(loaded, failures)
    _validate_mappings(loaded, failures)
    _validate_pr162_rerun_readiness(loaded, failures)
    _validate_pr163_blocked(loaded, failures)
    _validate_quantum_bridge(loaded, failures)
    _validate_agent_handoff(loaded, failures)
    _validate_forbidden_authority_scan(repo_root, reports, loaded, failures)
    _validate_pr152_currentization(repo_root, reports, loaded, failures)
    _validate_no_absolute_paths(reports, loaded, failures)
    _validate_git_guardrails(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162A report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162A report is not an object: {path}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        path = repo_root / c.SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162A schema: {path}")


def _validate_common_report_contracts(
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority class mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(isinstance(payload.get("source_inputs"), list), failures, f"{filename} missing source_inputs")
        _expect(tuple(payload.get("upstream_pr_refs") or ()) == c.UPSTREAM_PR_REFS, failures, f"{filename} upstream refs mismatch")
        for route in c.DOWNSTREAM_PR_ROUTES:
            _expect(route in payload.get("downstream_pr_routes", []), failures, f"{filename} missing downstream route {route}")
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation status must pass")
        for code in payload.get("blocker_codes") or []:
            _expect(code in c.BLOCKER_CODES, failures, f"{filename} blocker code not centralized: {code}")


def _validate_mandatory_inputs(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    summary = reports["PR162A_FinalSummary.report.json"]
    source_inputs = summary.get("source_inputs") or []
    _expect(
        bool(source_inputs),
        failures,
        "PR162A final summary must record consumed mandatory inputs",
    )
    for ref in c.REQUIRED_INPUT_REPORTS:
        _expect((repo_root / ref).exists(), failures, f"mandatory PR162A input missing: {ref}")
    _expect(
        any((repo_root / ref).exists() for ref in c.PR136_SECTION_CROSSWALK_ALIASES),
        failures,
        "PR136 section crosswalk alias input is missing",
    )
    _expect(
        summary.get("pr136_orchestration_artifacts_consumed_flag") is True,
        failures,
        "PR162A must consume PR136 orchestration artifacts",
    )
    _expect(
        summary.get("pr161c_pr161d_pr161e_pr161f_pr162_inputs_consumed_flag") is True,
        failures,
        "PR162A must consume PR161C/PR161D/PR161E/PR161F/PR162 inputs",
    )


def _validate_pr161f_input_consumption(
    repo_root: Path,
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    pr161f = load_pr161f_records(repo_root)
    _expect(len(pr161f["PR161F_ExecutorInputRegistry.report.json"]) == 9360, failures, "PR162A must consume 9360 executor inputs")
    _expect(len(pr161f["PR161F_ReplayRunRequestRegistry.report.json"]) == 9360, failures, "PR162A must consume 9360 replay requests")
    _expect(len(pr161f["PR161F_PaperRunRequestRegistry.report.json"]) == 9360, failures, "PR162A must consume 9360 paper requests")
    _expect(len(pr161f["PR161F_PairedReplayPaperRunPlan.report.json"]) == 9360, failures, "PR162A must consume 9360 paired run plans")
    _expect(len(pr161f["PR161F_QuantumClassicalHybridRunPlan.report.json"]) == 4525, failures, "PR162A must consume 4525 quantum/classical/hybrid run plans")
    _expect(
        len(loaded["PR162A_MarketScenarioQKUMappingMatrix.report.json"]) == 9360,
        failures,
        "PR162A QKU mapping must cover every PR161F executor input",
    )


def _validate_source_discovery(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162A_SourceDiscoveryCandidateRegistry.report.json"]
    _expect(len(records) >= 8, failures, "PR162A source discovery should retain useful public/research/quantum candidates")
    source_classes = {
        source_class
        for record in records
        for source_class in record.get("source_classes", [])
    }
    for source_class in (
        "OFFICIAL_SOURCE_CANDIDATE",
        "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE",
        "OFFICIAL_PUBLIC_PRICE_HISTORY_CANDIDATE",
        "OFFICIAL_PUBLIC_OHLC_EVENT_HISTORY_CANDIDATE",
        "RESEARCH_SOURCE_CANDIDATE",
        "CLASSICAL_METHOD_CANDIDATE",
        "HYBRID_METHOD_CANDIDATE",
        "QUANTUM_METHOD_CANDIDATE",
        "QUANTUM_BACKEND_DOC_CANDIDATE",
        "QUANTUM_ALGORITHM_DOC_CANDIDATE",
        "QUANTUM_PARAMETER_RANGE_CANDIDATE",
        "QUANTUM_ENCODING_CANDIDATE",
    ):
        _expect(source_class in source_classes, failures, f"missing source class candidate: {source_class}")
    for record in records:
        _expect(record.get("candidate_only_flag") is True, failures, f"source candidate not candidate-only: {record['record_id']}")
        _expect(record.get("accepted_as_official_fact_flag") is False, failures, f"source candidate accepted as fact: {record['record_id']}")
        _expect(record.get("creates_connector_semantics") is False, failures, f"source candidate created connector semantics: {record['record_id']}")
        _expect(record.get("access_rights_status") in c.ACCESS_RIGHTS_STATUSES, failures, f"source access status not centralized: {record['record_id']}")


def _validate_fetch_plans(
    repo_root: Path,
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json"]
    _expect(records, failures, "PR162A must emit fetch plans")
    fetch_plan_path = repo_root / c.FETCH_PLAN_DIR / "pr162a_fetch_plan_and_owner_materialization_queue.json"
    _expect(fetch_plan_path.exists(), failures, "PR162A fetch plan data file missing")
    for record in records:
        _expect(record.get("ci_requires_network") is False, failures, f"fetch plan requires CI network: {record['record_id']}")
        _expect(record.get("execute_in_pr162a_default_build_flag") is False, failures, f"fetch plan executes in default build: {record['record_id']}")
        caps = record.get("bounded_fetch_caps") or {}
        _expect(int(caps.get("max_rows", 0)) <= 1000, failures, f"fetch plan row cap drift: {record['record_id']}")
        _expect(int(caps.get("max_bytes", 0)) <= 250000, failures, f"fetch plan byte cap drift: {record['record_id']}")
        params = record.get("owner_command_parameters") or {}
        if params.get("requires_credentials"):
            _expect(
                record.get("access_rights_status") == "AUTHENTICATION_REQUIRED_BLOCKED",
                failures,
                f"credentialed fetch plan not blocked: {record['record_id']}",
            )


def _validate_dataset_materialization(
    repo_root: Path,
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    datasets = loaded["PR162A_DatasetMaterializationManifest.report.json"]
    _expect(len(datasets) >= 4, failures, "PR162A must emit materialized and blocked dataset candidates")
    by_id = {record["dataset_id"]: record for record in datasets}
    run_capable = by_id.get(c.KALSHI_RUN_CAPABLE_DATASET_ID)
    _expect(run_capable is not None, failures, "run-capable Kalshi tiny dataset missing")
    if run_capable:
        _expect(run_capable["run_capable_flag"] is True, failures, "Kalshi tiny dataset must be run-capable candidate")
        _expect(run_capable["candidate_only_flag"] is True, failures, "Kalshi tiny dataset must remain candidate-only")
        _expect(run_capable["adapter_mechanics_fixture_flag"] is True, failures, "Kalshi tiny dataset must be mechanics fixture-ready")
        _expect(run_capable["dataset_seed_candidate_flag"] is True, failures, "Kalshi tiny dataset must remain seed-candidate-ready")
        _expect(run_capable["venue_scope"] == "KALSHI", failures, "Kalshi tiny dataset venue scope drift")
        _expect(run_capable["source_class"] == "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE", failures, "Kalshi tiny dataset source class drift")
        _expect(run_capable["data_quality_status"] in {"PASS", "WARNING_CANDIDATE_ONLY"}, failures, "Kalshi tiny dataset data quality status drift")
        _expect(run_capable["schema_validation_status"] == "PASS", failures, "Kalshi tiny dataset schema validation drift")
        _expect(run_capable["normalization_status"] == "NORMALIZED", failures, "Kalshi tiny dataset normalization drift")
        _expect(run_capable["leakage_audit_status"] == "PASS", failures, "Kalshi tiny dataset leakage audit drift")
        _expect(run_capable["dataset_coverage_state"] == c.VENUE_SCOPED_RUN_CAPABLE_READY, failures, "Kalshi tiny dataset coverage state drift")
        _expect(run_capable["strict_pr161f_run_plan_coverage_count"] == 0, failures, "Kalshi tiny dataset fabricated PR161F strict coverage")
        _expect(
            run_capable["dataset_authority_class"] == "REPO_LOCAL_OFFICIAL_PUBLIC_HISTORICAL_DATASET_CANDIDATE",
            failures,
            "Kalshi tiny dataset authority class drift",
        )
        for key in ("raw_candidate_relative_posix_path", "relative_posix_path"):
            _validate_dataset_path(repo_root, run_capable.get(key), failures, f"Kalshi {key}")
    for dataset_id in (c.SYNTHETIC_BLOCKED_DATASET_ID, c.POLYMARKET_METADATA_DATASET_ID, c.IBKR_BLOCKED_DATASET_ID):
        _expect(dataset_id in by_id, failures, f"blocked dataset candidate missing: {dataset_id}")
    synthetic = by_id.get(c.SYNTHETIC_BLOCKED_DATASET_ID)
    if synthetic:
        _expect(synthetic["run_capable_flag"] is False, failures, "synthetic fixture became run-capable")
        _expect(synthetic["blocker_code"] == "PR162A_BLOCKED_SYNTHETIC_ONLY", failures, "synthetic fixture blocker drift")
    ibkr = by_id.get(c.IBKR_BLOCKED_DATASET_ID)
    if ibkr:
        _expect(ibkr["credential_required_flag"] is True, failures, "IBKR ForecastEx auth blocker lost credential flag")
        _expect(ibkr["run_capable_flag"] is False, failures, "IBKR ForecastEx auth candidate became run-capable")
    safety = loaded["PR162A_DatasetSafetyAndForbiddenPathScan.report.json"]
    _expect(all(record["path_allowlist_status"] == "PASS" for record in safety), failures, "dataset path allowlist scan failed")
    _expect(all(record["forbidden_path_scan_status"] == "PASS" for record in safety), failures, "dataset forbidden path scan failed")


def _validate_normalized_inventory(
    repo_root: Path,
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    rows = loaded["PR162A_NormalizedDatasetInventory.report.json"]
    _expect(len(rows) == 2, failures, "Kalshi tiny normalized dataset should contain exactly two rows")
    normalized_path = repo_root / c.KALSHI_TINY_NORMALIZED_PATH
    _expect(normalized_path.exists(), failures, "normalized dataset JSONL missing")
    if normalized_path.exists():
        _expect(read_jsonl(normalized_path) == rows, failures, "normalized JSONL does not match report inventory")
    performance_fragments = ("pnl", "profit", "return", "sharpe", "win_rate", "drawdown", "hit_rate", "fill_quality")
    for row in rows:
        for field in NORMALIZED_FIELDS:
            _expect(field in row, failures, f"normalized field missing: {field} in {row.get('record_id')}")
        _expect(row.get("created_by_pr") == c.PR_ID, failures, f"normalized row created_by_pr mismatch: {row.get('record_id')}")
        _expect(row.get("settlement_status_candidate") is None, failures, f"settlement leakage in normalized row: {row['record_id']}")
        _expect(row.get("resolution_candidate") is None, failures, f"resolution leakage in normalized row: {row['record_id']}")
        missing_reasons = row.get("missing_value_reasons") or {}
        for field in row.get("missing_value_flags") or []:
            _expect(field in missing_reasons, failures, f"missing value flag lacks reason: {row['record_id']}:{field}")
            _expect(row.get(field) is None, failures, f"missing value flag not represented as null: {row['record_id']}:{field}")
        row_text = _stringify(row).lower()
        for fragment in performance_fragments:
            _expect(fragment not in row_text, failures, f"performance evidence field found in normalized row: {fragment}")


def _validate_data_quality_and_missing_values(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    audit = loaded["PR162A_DataQualityLeakageAndTimeWindowAudit.report.json"]
    _expect(len(audit) == 1, failures, "data quality audit must contain one dataset audit")
    if audit:
        record = audit[0]
        _expect(record["data_quality_status"] == "PASS", failures, "data quality audit must pass")
        _expect(record["leakage_audit_status"] == "PASS", failures, "leakage audit must pass")
        _expect(record["pre_resolution_feature_separation_status"] == "PASS", failures, "pre-resolution feature separation failed")
        _expect(record["post_resolution_label_exclusion_status"] == "PASS", failures, "post-resolution label exclusion failed")
        _expect(record["performance_metric_creation_status"] == "NOT_CREATED", failures, "performance metric was created")
    missing = loaded["PR162A_MissingValueCandidateRegistry.report.json"]
    _expect(len(missing) >= 6, failures, "missing-value candidate registry should record explicit null reasons")
    for record in missing:
        _expect(record["value_fabricated_flag"] is False, failures, f"missing value fabricated: {record['record_id']}")
        _expect(record["candidate_imputation_status"] == "CANDIDATE_IMPUTATION_ONLY_NOT_APPLIED", failures, f"imputation status drift: {record['record_id']}")


def _validate_mappings(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    mappings = loaded["PR162A_MarketScenarioQKUMappingMatrix.report.json"]
    run_capable = [record for record in mappings if record["run_capable_dataset_available_flag"]]
    seed_only = [
        record
        for record in mappings
        if record["seed_candidate_mapping_flag"] and not record["run_capable_dataset_available_flag"]
    ]
    blocked_without_dataset = [
        record
        for record in mappings
        if not record["seed_candidate_mapping_flag"] and not record["run_capable_dataset_available_flag"]
    ]
    _expect(len(run_capable) == 0, failures, "tiny Kalshi dataset must not make QKUs run-capable")
    _expect(len(seed_only) == 9354, failures, "PR162A seed/mechanics QKU count should be 9354")
    _expect(len(blocked_without_dataset) == 6, failures, "PR162A unmappable QKU count should be 6")
    for record in run_capable:
        _expect(record["dataset_candidate_refs"] == [c.KALSHI_RUN_CAPABLE_DATASET_ID], failures, f"run-capable QKU lacks dataset ref: {record['qku_id']}")
        _expect(record["mapping_status"] == "MAPPED_TO_RUN_CAPABLE_CANDIDATE", failures, f"run-capable QKU status drift: {record['qku_id']}")
        _expect(record["strict_coverage_proof_status"] == "PASS", failures, f"run-capable QKU lacks strict proof: {record['qku_id']}")
        _expect(all(record["strict_coverage_proof"].values()), failures, f"run-capable QKU proof not strict: {record['qku_id']}")
    for record in seed_only:
        _expect(record["dataset_candidate_refs"] == [c.KALSHI_RUN_CAPABLE_DATASET_ID], failures, f"seed QKU lacks dataset ref: {record['qku_id']}")
        _expect(record["mapping_status"] == "MAPPED_TO_CANDIDATE_BLOCKED_FROM_RUN", failures, f"seed QKU status drift: {record['qku_id']}")
        _expect(record["blocker_code"] == c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS, failures, f"seed QKU blocker drift: {record['qku_id']}")
        _expect(record["adapter_mechanics_fixture_mapping_flag"] is True, failures, f"seed QKU lacks adapter mechanics flag: {record['qku_id']}")
        _expect(record["real_artifact_candidate_creation_allowed_flag"] is False, failures, f"seed QKU allows real artifact candidates: {record['qku_id']}")
        _expect(record["strict_row_count_coverage_flag"] is False, failures, f"seed QKU row-count proof unexpectedly passed: {record['qku_id']}")
        _expect(c.RUN_CAPABLE_BLOCKED_INSUFFICIENT_ROWS in record["coverage_blocker_codes"], failures, f"seed QKU lacks row-count blocker: {record['qku_id']}")
    for record in blocked_without_dataset:
        _expect(record["mapping_status"] == "BLOCKED_UNMAPPABLE_QKU", failures, f"blocked QKU mapping status drift: {record['qku_id']}")
        _expect(record["blocker_code"] == c.RUN_CAPABLE_BLOCKED_QKU_SCOPE_TOO_BROAD, failures, f"blocked QKU blocker drift: {record['qku_id']}")
    orphan_count = sum(
        1
        for record in mappings
        if record["mapping_status"] != "BLOCKED_UNMAPPABLE_QKU"
        and not record.get("dataset_candidate_refs")
    )
    _expect(orphan_count == 0, failures, "non-rejected dataset mappings contain orphans")
    coverage = loaded["PR162A_PR161FRunPlanDatasetCoverageBridge.report.json"]
    _expect(len(coverage) == len(mappings), failures, "PR161F coverage bridge count mismatch")
    _expect(
        sum(1 for record in coverage if record["strict_run_capable_coverage_flag"]) == 0,
        failures,
        "PR161F coverage bridge fabricated strict run-capable coverage",
    )


def _validate_pr162_rerun_readiness(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162A_PR162AdapterRerunReadinessBridge.report.json"]
    ready = [record for record in records if record["both_lanes_rerun_ready_flag"]]
    blocked = [record for record in records if not record["both_lanes_rerun_ready_flag"]]
    _expect(len(ready) == 0, failures, "tiny Kalshi dataset must not create PR162 rerun-ready QKUs")
    _expect(len(blocked) == 9360, failures, "PR162 rerun-blocked count should be 9360")
    _expect(
        all(record["downstream_pr_route"] == "PR162B_RERUN_PR162_WITH_PR162A_DATASETS" for record in ready),
        failures,
        "ready records must route to PR162B/PR162R, not PR163 directly",
    )
    _expect(
        all(record["remaining_blocker_code"] == "NONE" for record in ready),
        failures,
        "ready records must not retain blockers",
    )
    for record in records:
        if record["both_lanes_rerun_ready_flag"]:
            _expect(record["strict_run_capable_coverage_flag"] is True, failures, f"rerun-ready without strict coverage: {record['qku_id']}")
            _expect(record["real_artifact_candidate_creation_allowed_flag"] is True, failures, f"rerun-ready without artifact candidate permission: {record['qku_id']}")
        else:
            _expect(record["remaining_blocker_code"] != "NONE", failures, f"blocked rerun lacks blocker: {record['qku_id']}")
            _expect(record["recommended_next_step"] in {"MORE_DATA_REQUIRED", "OWNER_MATERIALIZE_MORE_DATASET_COVERAGE"}, failures, f"blocked rerun next step drift: {record['qku_id']}")
            _expect(record["real_artifact_candidate_creation_allowed_flag"] is False, failures, f"blocked rerun allows real artifact candidate: {record['qku_id']}")
            _expect(record["pr162b_real_artifact_candidate_allowed_flag"] is False, failures, f"blocked PR162B allows real artifact candidate: {record['qku_id']}")
            _expect(record["pr162r_real_artifact_candidate_allowed_flag"] is False, failures, f"blocked PR162R allows real artifact candidate: {record['qku_id']}")


def _validate_pr163_blocked(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162A_PR163ReadinessBlockerStatus.report.json"]
    _expect(len(records) == 1, failures, "PR163 blocker status must contain one record")
    if records:
        record = records[0]
        _expect(record["pr163_ready_flag"] is False, failures, "PR163 cannot be marked ready by PR162A datasets alone")
        _expect(record["validated_real_nonlive_replay_artifacts_exist_flag"] is False, failures, "PR163 replay artifact precondition fabricated")
        _expect(record["validated_real_nonlive_paper_artifacts_exist_flag"] is False, failures, "PR163 paper artifact precondition fabricated")
        _expect(record["result_packet_eligibility_gates_satisfied_flag"] is False, failures, "result packet eligibility fabricated")


def _validate_quantum_bridge(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    bridge = loaded["PR162A_QuantumQKUDatasetFeatureBridge.report.json"]
    work_orders = loaded["PR162A_QuantumFeatureMaterializationWorkOrderQueue.report.json"]
    _expect(len(bridge) == 4525, failures, "quantum dataset feature bridge must cover 4525 QKUs")
    _expect(len(work_orders) == len(bridge), failures, "quantum work-order count mismatch")
    ready = [record for record in bridge if record["run_capable_dataset_available_flag"]]
    seed_only = [record for record in bridge if record["feature_seed_candidate_only_flag"]]
    blocked = [
        record
        for record in bridge
        if not record["run_capable_dataset_available_flag"]
        and not record["feature_seed_candidate_only_flag"]
    ]
    _expect(len(ready) == 0, failures, "tiny Kalshi dataset must not create quantum run-capable features")
    _expect(len(seed_only) == 4519, failures, "PR162A quantum seed-only QKU count should be 4519")
    _expect(len(blocked) == 6, failures, "PR162A quantum blocked-data QKU count should be 6")
    for record in bridge:
        _expect(record["feature_family_candidates"], failures, f"quantum feature families missing: {record['qku_id']}")
        for feature in record["feature_family_candidates"]:
            _expect(feature in c.QUANTUM_FEATURE_FAMILIES, failures, f"quantum feature not centralized: {feature}")
        if record["feature_seed_candidate_only_flag"]:
            _expect(record["quantum_feature_materialization_status"] == "FEATURE_SEED_CANDIDATE_ONLY", failures, f"quantum seed-only status drift: {record['qku_id']}")
            _expect(record["run_capable_dataset_available_flag"] is False, failures, f"quantum seed-only marked run-capable: {record['qku_id']}")
        _expect(record["quantum_backend_execution_created_flag"] is False, failures, f"quantum backend execution created: {record['qku_id']}")
        _expect(record["quantum_simulator_execution_created_flag"] is False, failures, f"quantum simulator execution created: {record['qku_id']}")
        _expect(record["optimizer_execution_created_flag"] is False, failures, f"optimizer execution created: {record['qku_id']}")
        _expect(record["live_hot_path_admissibility"] in c.LIVE_HOT_PATH_ADMISSIBILITY_STATES, failures, f"live hot path state not centralized: {record['qku_id']}")
    for record in work_orders:
        _expect(record["execute_quantum_backend_flag"] is False, failures, f"quantum backend work order executes: {record['qku_id']}")
        _expect(record["execute_quantum_simulator_flag"] is False, failures, f"quantum simulator work order executes: {record['qku_id']}")
        _expect(record["execute_optimizer_flag"] is False, failures, f"optimizer work order executes: {record['qku_id']}")
        _expect(
            record["real_artifact_candidate_creation_allowed_flag"]
            is (record["work_order_status"] == "READY_FOR_PR162B_PR162R_REAL_RERUN_INPUT"),
            failures,
            f"quantum work order artifact permission drift: {record['qku_id']}",
        )


def _validate_agent_handoff(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162A_QTTAgentDatasetHandoffBridge.report.json"]
    _expect({record["agent_id"] for record in records} == set(c.AGENT_ROLES), failures, "QTT agent handoff role coverage mismatch")
    for record in records:
        _expect(record["runtime_agent_execution_created_flag"] is False, failures, f"agent runtime execution created: {record['agent_id']}")
        _expect(record["self_authorizing_trading_allowed_flag"] is False, failures, f"agent self-authorized trading: {record['agent_id']}")
        _expect(record["permission_expansion_created_flag"] is False, failures, f"agent permission expansion: {record['agent_id']}")
        _expect(record["live_write_secret_access_allowed_flag"] is False, failures, f"agent live-write secret access: {record['agent_id']}")
        _expect(record["order_routing_allowed_flag"] is False, failures, f"agent order routing allowed: {record['agent_id']}")


def _validate_forbidden_authority_scan(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    scan = loaded["PR162A_ForbiddenAuthorityScan.report.json"][0]
    _expect(scan["scan_status"] == "PASS", failures, "forbidden authority scan report must pass")
    _expect(scan["no_scattered_hardcoded_policy_scan_status"] == "PASS", failures, "no-scattered-policy scan report must pass")
    _expect(scan["hidden_network_call_scan_status"] == "PASS", failures, "hidden network call scan report must pass")
    _expect(scan["orphan_non_rejected_qku_dataset_mapping_count"] == 0, failures, "forbidden scan reports orphan mappings")
    _scan_source_policy_literals(repo_root, failures)
    _scan_hidden_network_calls(repo_root, failures)
    all_text = _stringify(list(reports.values())) + "\n" + _stringify(list(loaded.values()))
    lower_text = all_text.lower()
    forbidden_fragments = (
        "profit guarantee",
        "quantum advantage evidence",
        "live order receipt",
        "private account state fetched",
        "qaoa executed",
        "vqe executed",
        "qubo solved",
        "ising solved",
    )
    for fragment in forbidden_fragments:
        _expect(fragment not in lower_text, failures, f"forbidden authority wording found: {fragment}")
    sidecar_name = "AtomicRows.bundle" + ".sha256"
    _expect(sidecar_name not in all_text, failures, "forbidden AtomicRows sidecar reference found")


def _validate_pr152_currentization(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    summary = reports["PR162A_FinalSummary.report.json"]
    summary_records = loaded["PR162A_FinalSummary.report.json"]
    _expect(len(summary_records) == 1, failures, "PR162A final summary must contain one record")
    containers = [summary, *summary_records[:1]]
    for container in containers:
        # PR152 is executed as its own validation gate. PR162A only validates
        # the settled currentization contract recorded in its final summary.
        _expect(
            container.get("pr152_currentization_result")
            == c.PR152_CURRENTIZATION_RESULT_PASS,
            failures,
            "PR162A final summary PR152 currentization result must be confirmed pass",
        )
        _expect(
            container.get("pr152_currentization_failure_count") == 0,
            failures,
            "PR162A final summary PR152 currentization failure count must be zero",
        )
        _expect(
            container.get("pr152_currentization_failure_samples") == [],
            failures,
            "PR162A final summary PR152 currentization failure samples must be empty",
        )
        _expect(
            container.get("pr152_currentization_validation_command")
            == c.PR152_CURRENTIZATION_VALIDATION_COMMAND,
            failures,
            "PR162A final summary PR152 currentization command drift",
        )
        _expect(
            container.get("pr152_currentization_report_ref")
            == c.PR152_CURRENTIZATION_REPORT_REF,
            failures,
            "PR162A final summary PR152 currentization report ref drift",
        )


def _validate_no_absolute_paths(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    text = _stringify(list(reports.values())) + "\n" + _stringify(list(loaded.values()))
    _expect(not re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text), failures, "generated reports contain Windows absolute path")
    _expect("\\Users\\" not in text and "/Users/" not in text, failures, "generated reports contain local user path")


def _validate_git_guardrails(repo_root: Path, failures: list[str]) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    changed = {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}
    _expect(
        "docs/master_plan/QTT_MasterPlan_Current.md" not in changed,
        failures,
        "PR162A must not mutate QTT_MasterPlan_Current.md",
    )
    _expect(
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl" not in changed,
        failures,
        "PR162A must not mutate AtomicRows.bundle.jsonl",
    )
    sidecar_ref = "docs/master_plan/atomic_rows/" + "AtomicRows.bundle" + ".sha256"
    _expect(sidecar_ref not in changed, failures, "PR162A must not create forbidden AtomicRows sidecar")


def _validate_dataset_path(
    repo_root: Path,
    path_ref: Any,
    failures: list[str],
    label: str,
) -> None:
    _expect(isinstance(path_ref, str) and path_ref, failures, f"{label} missing")
    if not isinstance(path_ref, str):
        return
    _expect("\\" not in path_ref, failures, f"{label} must be POSIX relative")
    _expect(not re.match(r"^[A-Za-z]:[\\/]", path_ref), failures, f"{label} must not be absolute")
    _expect(any(path_ref.startswith(prefix) for prefix in c.ALLOWED_DATASET_PATH_PREFIXES), failures, f"{label} outside dataset path allowlist")
    _expect(not any(pattern in path_ref.lower() for pattern in c.FORBIDDEN_PATH_PATTERNS), failures, f"{label} contains forbidden path pattern")
    path = resolve_repo_relative(repo_root, path_ref)
    _expect(path.exists(), failures, f"{label} path missing: {path_ref}")


def _manifest_by_report(manifest: dict[str, Any], failures: list[str]) -> dict[str, dict[str, Any]]:
    by_report: dict[str, dict[str, Any]] = {}
    for record in records_from_payload(manifest):
        report_filename = record.get("report_filename")
        if not isinstance(report_filename, str):
            failures.append("PR162A shard manifest record missing report_filename")
            continue
        if report_filename in by_report:
            failures.append(f"duplicate PR162A shard manifest record: {report_filename}")
            continue
        by_report[report_filename] = record
    return by_report


def _validate_manifest_paths(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    manifest_by_report: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    expected = {filename for filename, payload in reports.items() if payload.get("sharded_flag")}
    _expect(set(manifest_by_report) == expected, failures, "PR162A shard manifest must list exactly sharded reports")
    manifest = reports[c.SHARD_MANIFEST_REPORT_FILENAME]
    _expect(manifest.get("all_shard_refs_posix_relative_flag") is True, failures, "PR162A shard manifest path portability failed")
    for report_filename, record in manifest_by_report.items():
        payload = reports[report_filename]
        shard_files = record.get("shard_files") or []
        _expect(payload.get("records") == [], failures, f"sharded top-level report duplicated records: {report_filename}")
        _expect(int(record.get("shard_count", -1)) == len(shard_files), failures, f"PR162A shard count mismatch: {report_filename}")
        for index, shard_ref in enumerate(shard_files, start=1):
            normalized = normalize_shard_ref(repo_root, shard_ref)
            _expect(normalized == shard_ref, failures, f"PR162A shard ref must already be normalized: {shard_ref}")
            _expect("\\" not in shard_ref, failures, f"PR162A shard ref must be POSIX: {shard_ref}")
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"missing PR162A shard file: {shard_ref}")
            shard_payload = read_json(shard_path)
            _expect(shard_payload.get("parent_report_filename") == report_filename, failures, f"PR162A shard parent mismatch: {shard_ref}")
            _expect(shard_payload.get("shard_index") == index, failures, f"PR162A shard index mismatch: {shard_ref}")


def _load_records(
    repo_root: Path,
    filename: str,
    payload: dict[str, Any],
    manifest_by_report: dict[str, dict[str, Any]],
    failures: list[str],
) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        records = records_from_payload(payload)
        _expect(int(payload.get("record_count", len(records))) == len(records), failures, f"record_count mismatch: {filename}")
        return records
    manifest_record = manifest_by_report.get(filename)
    if manifest_record is None:
        failures.append(f"missing PR162A shard manifest record for {filename}")
        return []
    merged: list[dict[str, Any]] = []
    for shard_ref in manifest_record.get("shard_files") or []:
        shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
        merged.extend(records_from_payload(shard_payload))
    _expect(int(manifest_record.get("total_record_count", -1)) == len(merged), failures, f"manifest total mismatch: {filename}")
    _expect(int(payload.get("total_record_count", -1)) == len(merged), failures, f"payload total mismatch: {filename}")
    return merged


def _scan_source_policy_literals(repo_root: Path, failures: list[str]) -> None:
    allowed = set(c.BLOCKER_CODES) | set(c.SOURCE_CLASSES) | set(c.DATASET_AUTHORITY_CLASSES)
    source_roots = [
        repo_root / "src/qtt/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate",
        repo_root / "tools/build_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        repo_root / "tools/validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        repo_root / "tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate",
    ]
    patterns = (
        re.compile(r'"(PR162A_(?:BLOCKED|PR162B|PR162R)[A-Z0-9_]+)"'),
        re.compile(r'"(PR163_BLOCKED_[A-Z0-9_]+)"'),
        re.compile(r'"(QUANTUM_BLOCKED_[A-Z0-9_]+)"'),
        re.compile(r'"((?:OFFICIAL|RESEARCH|THIRD|SOCIAL|WEB|INSTITUTIONAL|OWNER|CLASSICAL|HYBRID|QUANTUM)[A-Z0-9_]+_CANDIDATE)"'),
        re.compile(r'"(REPO_LOCAL_[A-Z0-9_]+|FETCH_PLAN_ONLY_NOT_MATERIALIZED|LIVE_OR_PRIVATE_DATASET_BLOCKED)"'),
    )
    for root in source_roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*.py")) if root.exists() else []
        for path in candidates:
            if path.name in c.NO_SCATTERED_POLICY_ALLOWLIST:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                for match in pattern.findall(text):
                    _expect(
                        match in allowed,
                        failures,
                        f"policy literal outside central registry: {path.relative_to(repo_root).as_posix()}:{match}",
                    )


def _scan_hidden_network_calls(repo_root: Path, failures: list[str]) -> None:
    roots = [
        repo_root / "src/qtt/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate",
        repo_root / "tools/build_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
        repo_root / "tools/validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
    ]
    forbidden = ("requests.", "httpx.", "urllib.request", "socket.", "websocket", "pip install")
    for root in roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*.py")) if root.exists() else []
        for path in candidates:
            if path.name == "validator.py":
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden:
                _expect(fragment not in text, failures, f"hidden network call pattern in {path.relative_to(repo_root).as_posix()}: {fragment}")


def _stringify(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join([str(key) + "\n" + _stringify(item) for key, item in value.items()])
    if isinstance(value, list | tuple | set):
        return "\n".join(_stringify(item) for item in value)
    return str(value)


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
