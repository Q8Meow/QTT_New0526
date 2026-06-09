"""Fail-closed validator for PR165 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .central_scoring_reason_codes import FORBIDDEN_SCATTERED_LITERALS
from .json_io import read_json, records_from_payload
from .repair_routing_vocab import BASE_AGENT_ROUTES, POST_LAUNCH_REPAIR_STATES
from .report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, load_report_records
from .scoring_authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    validate_record_authority,
)
from .scoring_status_vocab import (
    COMPUTABILITY_STATUSES_ACTIVE,
    COMPUTABILITY_STATUSES_REMAINING,
    SCATTERED_LITERAL_SCAN_EXCLUDED_PATH_NAMES,
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    _validate_no_scattered_literals(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    _validate_counts(records, failures)
    _validate_global_rows(records["PR165_GlobalCandidateRanking.report.json"], failures)
    _validate_model_risk(records["PR165_ModelRiskPenaltyRegistry.report.json"], failures)
    _validate_repair_rows(records["PR165_RepairRoutingHandoffRegistry.report.json"], failures)
    _validate_remaining(rows=records["PR165_Remaining2858ComputabilityMaterializationPlan.report.json"], failures=failures)
    _validate_regime_ranking(records, failures)
    _validate_external_scouting(records, failures)
    _validate_manifest(repo_root, reports, records, failures)
    _validate_authority(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR165 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR165 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR165 schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for rel_path in p.REQUIRED_INPUTS:
        if not (repo_root / rel_path).exists():
            failures.append(f"missing required PR165 upstream artifact: {rel_path}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR165", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(payload.get("vocab_refs"), failures, f"{filename} missing central vocab refs")
        if filename in p.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root must not duplicate row records")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("record_count") == len(records[filename]), failures, f"{filename} sharded row count mismatch")
        else:
            _expect(payload.get("record_count") == len(records_from_payload(payload)), failures, f"{filename} record_count mismatch")
        for key, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(key) is expected, failures, f"{filename} top-level authority flag drift: {key}")
        path = repo_root / p.GENERATED_DIR / filename
        if path.exists():
            _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds root report limit")
        for shard_path in payload.get("shard_files") or []:
            resolved = p.resolve_repo_relative(repo_root, shard_path)
            _expect(resolved.exists(), failures, f"{filename} missing shard: {shard_path}")
            if resolved.exists():
                _expect(resolved.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_path} exceeds shard limit")
        for record in records[filename]:
            failures.extend(validate_record_authority(record).failures)


def _validate_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR165_FinalSummary.report.json"][0]
    expectations = {
        "scored_candidate_rows": ("PR165_GlobalCandidateRanking.report.json", 6502),
        "global_ranking_rows": ("PR165_GlobalCandidateRanking.report.json", 6502),
        "score_component_rows": ("PR165_CandidateScoreComponentRegistry.report.json", 6502),
        "score_explainability_rows": ("PR165_ScoreExplainabilityLedger.report.json", 6502),
        "candidate_value_materialization_rows": ("PR165_CandidateValueMaterializationRegistry.report.json", 6502),
        "score_formula_coverage_rows": ("PR165_ScoreFormulaCoverageMap.report.json", 6502),
        "score_test_vector_coverage_rows": ("PR165_ScoreTestVectorCoverageMap.report.json", 6502),
        "probability_calibration_rows": ("PR165_ProbabilityCalibrationScoreRegistry.report.json", 6502),
        "expected_value_rows": ("PR165_ExpectedValueScoreRegistry.report.json", 6502),
        "lineage_graph_counts": ("PR165_LineageGraph.report.json", 6502),
        "remaining_materialization_plan_rows": ("PR165_Remaining2858ComputabilityMaterializationPlan.report.json", 2858),
    }
    for summary_field, (filename, expected) in expectations.items():
        actual = len(records[filename])
        _expect(actual == expected, failures, f"{filename} expected {expected} rows got {actual}")
        if isinstance(summary.get(summary_field), dict):
            continue
        _expect(summary.get(summary_field) in (actual, expected), failures, f"summary {summary_field} mismatch")
    _expect(len(records["PR165_ScoreFormulaRegistry.report.json"]) > 0, failures, "score formula registry empty")
    _expect(len(records["PR165_ScoreTestVectorRegistry.report.json"]) > 0, failures, "score test vector registry empty")
    _expect(len(records["PR165_RegimeSlicedRanking.report.json"]) > 6502, failures, "regime ranking must exceed scored rows")
    _expect(len(records["PR165_RepairRoutingHandoffRegistry.report.json"]) > 0, failures, "repair routing rows missing")
    _expect(
        len(records["PR165_RepairRetestRouteRegistry.report.json"]) == len(records["PR165_RepairRoutingHandoffRegistry.report.json"]),
        failures,
        "repair retest rows mismatch",
    )
    _expect(
        len(records["PR165_CandidateVersionRepairPlan.report.json"]) == len(records["PR165_RepairRoutingHandoffRegistry.report.json"]),
        failures,
        "candidate version repair plan rows mismatch",
    )
    _expect(len(records["PR165_PR165BNegativeMemoryCandidateHandoff.report.json"]) > 0, failures, "PR165-B handoff missing")
    _expect(len(records["PR165_PR162D_R3PriorityHandoff.report.json"]) == 2858, failures, "PR162D-R3 handoff row mismatch")
    _expect(len(records["PR165_PluginPriorityHandoff.report.json"]) > 0, failures, "plugin priority handoff missing")
    _expect(len(records["PR165_DashboardScoreHandoff.report.json"]) == 6502, failures, "dashboard handoff row mismatch")
    for field in ("metadata_only_rows", "placeholder_only_rows", "future_consumer_only_rows", "unknown_status_rows"):
        _expect(summary.get(field) == 0, failures, f"{field} must be zero")
    _expect(summary.get("orphan_counts_all_0") is True, failures, "orphan counts not all zero")
    _expect(summary.get("authority_counts_all_0") is True, failures, "authority counts not all zero")


def _validate_global_rows(rows: list[dict[str, Any]], failures: list[str]) -> None:
    required = (
        "qku_id",
        "candidate_packet_id",
        "source_candidate_refs",
        "upstream_pr_refs",
        "upstream_report_refs",
        "computability_status",
        "computability_recipe_ref",
        "score_formula_ref",
        "score_test_vector_ref",
        "deterministic_score_component_record",
        "composite_score",
        "global_rank",
        "regime_rank_refs",
        "score_decomposition",
        "score_confidence_tier",
        "rank_stability_bucket",
        "score_lower_bound",
        "score_upper_bound",
        "replay_paper_evidence_ref",
        "TCA_evidence_ref_or_candidate_estimate_ref",
        "latency_evidence_ref_or_candidate_estimate_ref",
        "model_risk_ref",
        "quantum_compatibility_ref",
        "lineage_graph_ref",
        "top_positive_factors",
        "top_negative_factors",
        "penalty_factors",
        "repair_routing_ref",
        "post_launch_repair_state",
        "next_agent_action",
        "upstream_agent_routes",
        "downstream_agent_routes",
        "PR165_B_negative_memory_handoff_status",
        "PR162D_R3_priority_status_when_applicable",
        "plugin_priority_status_when_applicable",
        "dashboard_handoff_status",
        "authority_boundary_record",
    )
    ranks = [row.get("global_rank") for row in rows]
    _expect(ranks == list(range(1, len(rows) + 1)), failures, "global ranks are not deterministic contiguous ranks")
    for row in rows:
        for field in required:
            _expect(bool(row.get(field)) or field == "global_rank", failures, f"global rank row missing {field}")
        _expect(row.get("computability_status") in COMPUTABILITY_STATUSES_ACTIVE, failures, "active row has invalid computability status")
        _expect(row.get("post_launch_repair_state") in POST_LAUNCH_REPAIR_STATES, failures, "invalid repair state")
        _expect(isinstance(row.get("composite_score"), (int, float)), failures, "composite_score missing numeric value")
        _expect(0 <= row["composite_score"] <= 100, failures, "composite_score outside range")
        _expect(row.get("score_decomposition"), failures, "score decomposition missing")
        downstream = set(row.get("downstream_agent_routes") or [])
        for agent in BASE_AGENT_ROUTES:
            _expect(agent in downstream, failures, f"candidate missing downstream agent {agent}")


def _validate_model_risk(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        for field in (
            "model_purpose",
            "model_intended_use",
            "model_assumptions",
            "model_limitations",
            "model_limitations_count",
            "validation_coverage_score",
            "outcome_analysis_score",
            "monitoring_readiness_score",
            "third_party_or_non_official_source_penalty",
            "independent_review_required_flag",
            "model_materiality_tier",
            "model_risk_penalty",
            "model_risk_route",
        ):
            _expect(row.get(field) not in (None, "", []), failures, f"model risk row missing {field}")
        _expect(isinstance(row.get("model_risk_penalty"), (int, float)), failures, "model risk penalty non-numeric")
        if row.get("model_materiality_tier") in {"HIGH_AGENT_SELECTION_IMPACT", "CRITICAL_FUTURE_LIVE_ADJACENT"}:
            _expect(row.get("independent_review_required_flag") is True, failures, "high materiality row lacks independent review flag")
        route = set(row.get("model_risk_route") or [])
        for agent in ("risk_agent", "governance_agent", "dashboard_future_consumer"):
            _expect(agent in route, failures, f"model risk route missing {agent}")


def _validate_repair_rows(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        for field in (
            "repair_reason_codes",
            "responsible_repair_agent",
            "required_materialization_action",
            "missing_or_weak_fields",
            "downstream_retest_route",
            "downstream_consumer",
            "candidate_version",
            "parent_candidate_version",
            "authority_boundary",
        ):
            _expect(bool(row.get(field)), failures, f"repair row missing {field}")
        _expect(row.get("live_selection_allowed") is False, failures, "repair row permits live selection")


def _validate_remaining(rows: list[dict[str, Any]], failures: list[str]) -> None:
    for row in rows:
        _expect(row.get("computability_status") in COMPUTABILITY_STATUSES_REMAINING, failures, "remaining row invalid computability status")
        for field in (
            "missing_variable_families",
            "missing_value_families",
            "candidate_source_search_plan",
            "candidate_formula_algorithm_plan",
            "likely_responsible_agent",
            "likely_downstream_pr",
            "replay_paper_route_after_materialization",
            "quantum_compatibility_rescue_route",
            "repair_retest_route",
            "materialization_recipe_ref",
        ):
            _expect(bool(row.get(field)), failures, f"remaining materialization row missing {field}")


def _validate_regime_ranking(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    categories = {row.get("regime_category") for row in records["PR165_RegimeSlicedRanking.report.json"]}
    expected = {
        "venue",
        "event_type",
        "binary_vs_multi_outcome",
        "liquidity_bucket",
        "spread_bucket",
        "latency_bucket",
        "time_to_resolution_bucket",
        "market_maturity_bucket",
        "volatility_bucket",
        "fee_slippage_bucket",
        "quantum_compatible_family",
        "repair_family",
        "risk_tier",
        "model_risk_tier",
        "agent_ownership",
        "source_provenance_tier",
        "negative_memory_candidate_status",
        "hot_path_lane",
    }
    _expect(expected.issubset(categories), failures, "regime ranking missing required categories")


def _validate_external_scouting(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    _expect(len(records["PR165_ExternalCandidateScoutingLedger.report.json"]) >= 50, failures, "external candidate records below target")
    _expect(len(records["PR165_ExternalFormulaAndParameterCandidateRegistry.report.json"]) >= 20, failures, "external formula records below target")
    _expect(len(records["PR165_ExternalQuantumMappingTemplateCandidateRegistry.report.json"]) >= 10, failures, "external quantum records below target")
    for filename in (
        "PR165_ExternalCandidateScoutingLedger.report.json",
        "PR165_ExternalFormulaAndParameterCandidateRegistry.report.json",
        "PR165_ExternalQuantumMappingTemplateCandidateRegistry.report.json",
    ):
        for row in records[filename]:
            _expect(row.get("source_url"), failures, f"{filename} row missing source_url")
            _expect(row.get("validation_status") == "PASS", failures, f"{filename} row validation drift")


def _validate_manifest(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    manifest = records["PR165_ReportManifest.report.json"]
    filenames = {row["report_filename"] for row in manifest}
    _expect(filenames == set(p.REPORT_FILENAMES), failures, "manifest does not cover every PR165 root report")
    listed_shards = {shard for row in manifest for shard in row.get("shard_paths", [])}
    actual_shards = {path.relative_to(repo_root).as_posix() for path in (repo_root / p.SHARD_DIR).glob("*.json")}
    _expect(actual_shards == listed_shards, failures, "manifest shard listing does not match pr165_shards directory")
    for filename in p.REPORT_FILENAMES:
        _expect(filename in reports, failures, f"manifest references missing root report {filename}")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename in (
        "PR165_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
        "PR165_NoQTTChecksumFreezeAuthorityAudit.report.json",
        "PR165_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR165_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    ):
        row = records[filename][0]
        for key, expected in BOUNDARY_COUNT_FIELDS.items():
            _expect(row.get(key) == expected, failures, f"{filename} authority count drift: {key}")
        _expect(row.get("all_authority_counts_zero") is True, failures, f"{filename} authority summary not zero")
    for row in records["PR165_QuantumFormulationMaterializationRegistry.report.json"]:
        _expect(row.get("quantum_backend_execution_count") == 0, failures, "quantum backend execution count drift")
        _expect(row.get("quantum_advantage_claim_count") == 0, failures, "quantum advantage claim count drift")


def _validate_no_scattered_literals(repo_root: Path, failures: list[str]) -> None:
    scan_paths = [
        repo_root / p.PACKAGE_DIR,
        repo_root / p.TEST_DIR,
        repo_root / "tools/build_pr165_evidence_backed_scoring_ranking.py",
        repo_root / "tools/validate_pr165_evidence_backed_scoring_ranking.py",
    ]
    approved = set(SCATTERED_LITERAL_SCAN_EXCLUDED_PATH_NAMES)
    for base in scan_paths:
        paths = [base] if base.is_file() else list(base.rglob("*")) if base.exists() else []
        for path in paths:
            if path.suffix not in {".py", ".json"}:
                continue
            if path.name in approved:
                continue
            text = path.read_text(encoding="utf-8")
            for literal in FORBIDDEN_SCATTERED_LITERALS:
                if literal in text:
                    failures.append(f"scattered PR165 forbidden literal {literal!r} in {path.relative_to(repo_root).as_posix()}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
