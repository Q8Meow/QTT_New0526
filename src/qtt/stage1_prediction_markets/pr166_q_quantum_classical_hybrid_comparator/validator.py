"""Fail-closed validator for PR166-Q generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .authority import FORBIDDEN_AUTHORITY_FLAGS, ZERO_AUTHORITY_KEYS
from .io import read_json, records_from_report_payload, resolve_repo_relative


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


ROW_REQUIRED_FIELDS = (
    "row_id",
    "source_pr",
    "upstream_row_ref",
    "root_report_ref",
    "root_report_consumption_ref",
    "universal_artifact_consumer_ref",
    "qku_id",
    "qku_family",
    "formula_id",
    "algorithm_id",
    "parameter_stack_id",
    "execution_route_id",
    "market_scope",
    "prediction_market_stage1_applicability",
    "candidate_authority_class",
    "source_provenance_class",
    "official_source_flag",
    "non_official_candidate_flag",
    "owner_seeded_flag",
    "web_research_seeded_flag",
    "social_research_seeded_flag",
    "institutional_research_seeded_flag",
    "external_candidate_intake_ref",
    "classical_candidate_flag",
    "quantum_inspired_candidate_flag",
    "true_quantum_ready_candidate_flag",
    "hybrid_candidate_flag",
    "objective_direction",
    "objective_terms",
    "decision_variables",
    "variable_domains",
    "constraints",
    "penalty_terms",
    "linear_coefficients",
    "quadratic_coefficients",
    "higher_order_terms",
    "constraint_handling_mode",
    "qubo_ready_flag",
    "bqm_ready_flag",
    "ising_ready_flag",
    "cqm_ready_flag",
    "dqm_ready_flag",
    "quadratic_program_ready_flag",
    "mapping_gap_reason",
    "classical_baseline_solver_class",
    "quantum_inspired_solver_class",
    "hybrid_solver_class",
    "gross_expected_edge_candidate",
    "expected_net_profit_per_order_candidate",
    "execution_adjusted_score",
    "tca_adjusted_score",
    "latency_adjusted_score",
    "queue_risk_adjusted_score",
    "risk_adjusted_score",
    "downside_risk_adjusted_score",
    "cvar_proxy_score",
    "overfit_adjusted_score",
    "false_discovery_penalty",
    "pbo_proxy",
    "deflated_score_proxy",
    "capacity_adjusted_score",
    "crowding_adjusted_score",
    "marginal_utility_score",
    "quantum_repair_triage_flag",
    "quantum_repair_triage_ref",
    "champion_challenger_role",
    "regime_condition",
    "memory_state",
    "replay_candidate_flag",
    "paper_candidate_flag",
    "owning_agent_id",
    "reviewer_agent_id",
    "challenger_agent_id",
    "upstream_refs",
    "downstream_refs",
    "validation_refs",
    "no_orphan_proof_ref",
    "computability_disposition",
    "fill_action_ref",
    "repair_route_ref",
    "exclusion_reason",
    "created_by_pr",
    "deterministic_sort_key",
)


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {
        filename: records_from_report_payload(repo_root, payload)
        for filename, payload in reports.items()
    }
    _validate_payload_contracts(repo_root, reports, records, failures)
    _validate_manifest(reports, records, failures)
    _validate_row_contracts(records, failures)
    _validate_counts(records, failures)
    _validate_authority(reports, records, failures)
    _validate_computability(records, failures)
    _validate_quantum_readiness(records, failures)
    _validate_tca(records, failures)
    _validate_source_ledgers(records, failures)
    _validate_no_orphans(records, failures)
    _validate_no_forbidden_sidecars(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-Q report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR166-Q report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in c.SCHEMA_FILENAMES:
        path = repo_root / c.SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR166-Q schema: {filename}")
        if filename.startswith("p_r166_q"):
            failures.append(f"letter-split PR166-Q schema name forbidden: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in c.STRICT_INPUT_REPORTS:
        if not (repo_root / c.GENERATED_DIR / filename).exists():
            failures.append(f"missing PR166-Q upstream input: {filename}")


def _validate_payload_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("roadmap_pr_id") == c.PR_ID, failures, f"{filename} roadmap_pr_id mismatch")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("authority_boundary_ref") == c.AUTHORITY_BOUNDARY_REF, failures, f"{filename} authority boundary mismatch")
        _expect(payload.get("validation_status") == c.VALIDATION_STATUS, failures, f"{filename} validation status mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema ref mismatch")
        _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} record_count mismatch")
        path = repo_root / c.GENERATED_DIR / filename
        _expect(path.stat().st_size <= c.ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} root report exceeds size limit")
        if filename in c.ROW_LEVEL_REPORTS:
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("records") == [], failures, f"{filename} compact root duplicated sharded rows")
            _expect(payload.get("records_omitted_for_sharding_flag") is True, failures, f"{filename} missing omitted flag")
            _expect(payload.get("shard_files"), failures, f"{filename} missing shard files")
        for shard_ref in payload.get("shard_files") or []:
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"{filename} missing shard {shard_ref}")
            if shard_path.exists():
                _expect(shard_path.stat().st_size <= c.SHARD_LIMIT_BYTES, failures, f"{shard_ref} exceeds shard size limit")
                shard_payload = read_json(shard_path)
                _expect(shard_payload.get("parent_report_filename") == filename, failures, f"{shard_ref} parent mismatch")
                _expect(shard_payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{shard_ref} schema mismatch")


def _validate_manifest(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR166_Q_ReportManifest.report.json"]
    root_rows = [row for row in manifest if row.get("manifest_entry_class") == "ROOT_REPORT"]
    shard_rows = [row for row in manifest if row.get("manifest_entry_class") == "SHARD_REPORT"]
    listed_roots = {row["report_filename"] for row in root_rows}
    _expect(listed_roots == set(c.REPORT_FILENAMES), failures, "manifest root reports do not match constants")
    expected_shards = {
        ref["shard_path"]: (filename, int(ref["row_count"]))
        for filename, payload in reports.items()
        for ref in (payload.get("shard_manifest_refs") or [])
    }
    listed_shards = {row["report_path"] for row in shard_rows}
    _expect(listed_shards == set(expected_shards), failures, "manifest shard reports do not match payloads")
    for row in root_rows:
        filename = row["report_filename"]
        _expect(row["row_count"] == reports[filename]["record_count"], failures, f"manifest row count mismatch {filename}")
        _expect(row["schema_path"].endswith(c.REPORT_SCHEMA_REFS[filename]), failures, f"manifest schema mismatch {filename}")


def _validate_row_contracts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for field in ROW_REQUIRED_FIELDS:
                value = row.get(field)
                _expect(value not in ("", None), failures, f"{filename} {row.get('row_id')} missing {field}")
            for list_field in ("upstream_refs", "downstream_refs", "validation_refs"):
                _expect(isinstance(row.get(list_field), list) and row[list_field], failures, f"{filename} {row.get('row_id')} missing list {list_field}")
            _expect(row.get("computability_disposition") in c.COMPUTABILITY_DISPOSITIONS, failures, f"{filename} bad computability disposition")
            _expect(row.get("champion_challenger_role") in c.CHAMPION_ROLES, failures, f"{filename} bad champion role")
            for forbidden in c.FORBIDDEN_COMPUTABILITY_DISPOSITIONS:
                _expect(row.get("computability_disposition") != forbidden, failures, f"{filename} forbidden computability {forbidden}")


def _validate_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    expected_quantum = 559
    for filename in c.ROW_LEVEL_REPORTS:
        _expect(len(records[filename]) == expected_quantum, failures, f"{filename} expected 559 rows")
    _expect(len(records["PR166_Q_RootReportConsumptionLedger.report.json"]) == 109, failures, "PR166-SM3 root report count mismatch")
    summary = records["PR166_Q_FinalSummary.report.json"][0]
    _expect(summary["actual_consumed_quantum_comparator_row_count"] == expected_quantum, failures, "summary quantum row count mismatch")
    _expect(summary["pr166_sm3_root_report_count_discovered"] == 109, failures, "summary root report count mismatch")


def _validate_authority(
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        for key in ZERO_AUTHORITY_KEYS:
            _expect(payload.get(key, 0) == 0, failures, f"{filename} authority count not zero: {key}")
    for filename, rows in records.items():
        for row in rows:
            for key in ZERO_AUTHORITY_KEYS:
                _expect(row.get(key, 0) == 0, failures, f"{filename} row {row.get('row_id')} authority count not zero: {key}")
            for flag in FORBIDDEN_AUTHORITY_FLAGS:
                _expect(row.get(flag) is False, failures, f"{filename} row {row.get('row_id')} authority flag not false: {flag}")


def _validate_computability(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_Q_ComputabilityDispositionLedger.report.json"]
    for row in rows:
        _expect(row["computability_disposition"] == "COMPUTABLE_NOW", failures, f"{row['row_id']} not computable now")
        _expect(row["fill_action_ref"], failures, f"{row['row_id']} missing fill action ref")
        _expect(row["repair_route_ref"], failures, f"{row['row_id']} missing repair route ref")
        _expect(row["metadata_only_ready_flag"] is False, failures, f"{row['row_id']} metadata-only flag true")
        _expect(row["solver_label_only_ready_flag"] is False, failures, f"{row['row_id']} solver-only flag true")
        _expect(row["placeholder_ready_flag"] is False, failures, f"{row['row_id']} placeholder flag true")
        _expect(row["future_consumer_note_only_ready_flag"] is False, failures, f"{row['row_id']} future-only flag true")


def _validate_quantum_readiness(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR166_Q_QuantumStructuralReadiness.report.json"]
    for row in rows:
        _expect(row["qubo_ready_flag"] is True and row["binary_variables"], failures, f"{row['row_id']} QUBO not ready")
        _expect(row["bqm_ready_flag"] is True and row["bqm_representation_candidate"]["linear"], failures, f"{row['row_id']} BQM not ready")
        _expect(row["ising_ready_flag"] is True and row["ising_representation_candidate"]["h"], failures, f"{row['row_id']} Ising not ready")
        _expect(row["cqm_ready_flag"] is True and row["cqm_representation_candidate"]["constraints"], failures, f"{row['row_id']} CQM not ready")
        _expect(row["dqm_ready_flag"] is True and row["dqm_representation_candidate"]["cases"], failures, f"{row['row_id']} DQM not ready")
        _expect(row["quadratic_program_ready_flag"] is True and row["quadratic_program_representation_candidate"]["variables"], failures, f"{row['row_id']} QuadraticProgram not ready")
        _expect(row["quantum_backend_execution_flag"] is False, failures, f"{row['row_id']} backend execution flag true")
        _expect(row["quantum_advantage_claim_flag"] is False, failures, f"{row['row_id']} advantage flag true")


def _validate_tca(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_Q_TCADecomposition.report.json"]:
        parts = [
            row["explicit_fee_component"],
            row["bid_ask_spread_component"],
            row["slippage_component"],
            row["impact_component"],
            row["latency_component"],
            row["no_fill_opportunity_cost_component"],
            row["settlement_finality_component"],
            row["market_state_mismatch_component"],
            row["model_vs_execution_gap_component"],
            row["adverse_selection_cost_component"],
        ]
        _expect(round(sum(parts), 6) == row["total_transaction_cost_estimate"], failures, f"{row['row_id']} TCA sum mismatch")
    for row in records["PR166_Q_ExecutionAdjustedRanking.report.json"]:
        _expect(row["final_executable_edge_score"] == row["execution_adjusted_score"], failures, f"{row['row_id']} executable score mismatch")


def _validate_source_ledgers(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    source_rows = records["PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json"]
    _expect(len(source_rows) >= 12, failures, "source reading ledger too small")
    for row in source_rows:
        _expect(row["no_source_truth_acceptance_flag"] is True, failures, f"{row['row_id']} source truth flag missing")
        _expect(row["source_locator_or_query"], failures, f"{row['row_id']} missing source locator")
        _expect(row["candidate_values_extracted_count"] >= 0, failures, f"{row['row_id']} bad candidate count")
    for row in records["PR166_Q_ExternalCandidateIntakeLedger.report.json"]:
        _expect(row["candidate_authority_class"] == "REPLAY_PAPER_CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH", failures, f"{row['row_id']} bad authority class")


def _validate_no_orphans(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR166_Q_RootReportConsumptionLedger.report.json"]:
        _expect(row["consumed_by_PR166_Q_flag"] is True, failures, f"{row['row_id']} root report not consumed")
        _expect(row["no_orphan_proof_ref"], failures, f"{row['row_id']} missing no-orphan proof")
    for row in records["PR166_Q_UniversalArtifactConsumerMap.report.json"]:
        terminal = bool(row.get("terminal_flag"))
        _expect(terminal or row.get("consumed_by_report"), failures, f"{row['row_id']} artifact orphan")
        if terminal:
            _expect(row.get("terminal_reason") not in ("", None), failures, f"{row['row_id']} terminal without reason")
    for row in records["PR166_Q_NoOrphanProof.report.json"]:
        _expect(row["no_orphan_status"].startswith("CONNECTED_"), failures, f"{row['row_id']} no-orphan status bad")


def _validate_no_forbidden_sidecars(repo_root: Path, failures: list[str]) -> None:
    forbidden = [
        *repo_root.glob("docs/master_plan/generated/PR166_Q_*.sha256"),
        *repo_root.glob("docs/master_plan/generated/PR166_Q_*checksum*.json"),
        *repo_root.glob("docs/master_plan/generated/PR166_Q_*digest*.json"),
    ]
    _expect(not forbidden, failures, f"forbidden PR166-Q hash/checksum/digest sidecars: {forbidden}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
