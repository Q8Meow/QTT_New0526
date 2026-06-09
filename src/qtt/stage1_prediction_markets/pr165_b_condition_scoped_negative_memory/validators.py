"""Fail-closed validator for PR165-B generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload
from .negative_memory_action_policy import (
    AGENT_SELECTION_OVERLAY_ACTIONS,
    FORBIDDEN_OVERLAY_ACTIONS,
    requires_repair,
)
from .negative_memory_authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    validate_record_authority,
)
from .negative_memory_reason_codes import (
    FORBIDDEN_SCATTERED_LITERALS,
    SCATTERED_LITERAL_SCAN_EXCLUDED_PATH_NAMES,
)
from .negative_memory_status_vocab import MEMORY_CLASSIFICATIONS, is_non_positive_memory
from .quantum_negative_memory import is_quantum_compatible
from .report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, load_report_records


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
    _validate_manifest(reports, records, failures)
    _validate_counts(records, failures)
    _validate_memory_rows(records, failures)
    _validate_policy_rows(records, failures)
    _validate_quantum(records, failures)
    _validate_external(records, failures)
    _validate_authority(records, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR165-B report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR165-B report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR165-B schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    for rel_path in p.REQUIRED_INPUTS:
        if not (repo_root / rel_path).exists():
            failures.append(f"missing required PR165-B upstream artifact: {rel_path}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR165-B", failures, f"{filename} created_by_pr mismatch")
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


def _validate_manifest(reports: dict[str, dict[str, Any]], records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    manifest = records["PR165_B_ReportManifest.report.json"]
    listed = {row.get("report_filename") for row in manifest}
    _expect(listed == set(p.REPORT_FILENAMES), failures, "manifest does not list exactly the PR165-B reports")
    for row in manifest:
        filename = row["report_filename"]
        _expect(row.get("row_count") == reports[filename].get("record_count"), failures, f"manifest row count mismatch: {filename}")
        for shard_path in row.get("shard_paths") or []:
            _expect(shard_path in reports[filename].get("shard_files", []), failures, f"manifest shard mismatch: {shard_path}")


def _validate_counts(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    summary = records["PR165_B_FinalSummary.report.json"][0]
    expectations = {
        "memory_candidate_rows": ("PR165_B_CandidateVersionMemoryRegistry.report.json", 6502),
        "condition_fingerprint_rows": ("PR165_B_ConditionFingerprintRegistry.report.json", 6502),
        "combination_fingerprint_rows": ("PR165_B_CombinationFingerprintRegistry.report.json", 6502),
        "asof_leakage_audit_rows": ("PR165_B_AsOfLeakageAudit.report.json", 6502),
        "evidence_sufficiency_rows": ("PR165_B_EvidenceSufficiencyRegistry.report.json", 6502),
        "false_discovery_control_rows": ("PR165_B_FalseDiscoveryControlRegistry.report.json", 6502),
        "scenario_outcome_rows": ("PR165_B_ScenarioOutcomeMatrix.report.json", 6502),
        "memory_decay_policy_rows": ("PR165_B_MemoryDecayAndOverridePolicy.report.json", 6502),
        "similarity_match_policy_rows": ("PR165_B_SimilarityMatchPolicyRegistry.report.json", 6502),
        "agent_selection_overlay_rows": ("PR165_B_AgentSelectionOverlayHandoff.report.json", 6502),
        "agent_memory_route_rows": ("PR165_B_AgentMemoryRouter.report.json", 6502),
        "lineage_graph_rows": ("PR165_B_LineageGraph.report.json", 6502),
        "dashboard_handoff_rows": ("PR165_B_DashboardMemoryHandoff.report.json", 6502),
        "governance_handoff_rows": ("PR165_B_GovernanceMemoryHandoff.report.json", 6502),
    }
    for field, (filename, expected) in expectations.items():
        actual = len(records[filename])
        _expect(actual == expected, failures, f"{filename} expected {expected} rows got {actual}")
        _expect(summary.get(field) == actual, failures, f"summary {field} mismatch")
    _expect(summary.get("negative_memory_rows", 0) > 0, failures, "negative memory rows missing")
    _expect(summary.get("positive_memory_rows", 0) > 0, failures, "positive memory rows missing")
    _expect(summary.get("fragile_memory_rows", 0) > 0, failures, "fragile memory rows missing")
    non_positive = summary["negative_memory_rows"]
    for field, filename in (
        ("cooldown_policy_rows", "PR165_B_CooldownPolicyRegistry.report.json"),
        ("retest_policy_rows", "PR165_B_RetestEligibilityRegistry.report.json"),
        ("outcome_attribution_rows", "PR165_B_OutcomeAttributionLedger.report.json"),
        ("counterfactual_attribution_rows", "PR165_B_CounterfactualAttributionLedger.report.json"),
        ("retest_queue_rows", "PR165_B_ReplayPaperRetestQueue.report.json"),
    ):
        _expect(summary.get(field) == len(records[filename]) == non_positive, failures, f"{field} must match non-positive memory rows")
    for field in ("metadata_only_rows", "placeholder_only_rows", "future_consumer_only_rows", "unknown_status_rows", "global_ban_rows", "global_ban_rows_without_structural_invalidity"):
        _expect(summary.get(field) == 0, failures, f"{field} must be zero")
    _expect(summary.get("orphan_counts_all_0") is True, failures, "orphan counts not all zero")
    _expect(summary.get("authority_counts_all_0") is True, failures, "authority counts not all zero")


def _validate_memory_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    required = (
        "candidate_packet_id",
        "qku_id",
        "candidate_version",
        "pr165_global_rank",
        "pr165_regime_rank_refs",
        "score_model_id",
        "score_component_ref",
        "lineage_graph_ref",
        "agent_orchestration_ref",
        "condition_fingerprint_id",
        "combination_fingerprint_id",
        "scenario_outcome_ref",
        "as_of_evidence_ref",
        "leakage_audit_ref",
        "evidence_sufficiency_ref",
        "false_discovery_control_ref",
        "memory_classification",
        "memory_action_policy",
        "memory_confidence_tier",
        "memory_materiality_tier",
        "outcome_attribution_ref",
        "counterfactual_attribution_ref",
        "cooldown_policy_ref",
        "retest_policy_ref",
        "repair_route_ref",
        "allowed_condition_scope_ref",
        "avoid_condition_scope_ref",
        "similarity_match_policy_ref",
        "memory_decay_policy_ref",
        "dashboard_memory_ref",
        "governance_memory_ref",
        "agent_selection_overlay_ref",
        "authority_boundary_ref",
        "downstream_agent_route",
        "downstream_pr_route",
        "dashboard_consumer",
        "governance_consumer",
    )
    condition_ids = {row["condition_fingerprint_id"] for row in records["PR165_B_ConditionFingerprintRegistry.report.json"]}
    combination_ids = {row["combination_fingerprint_id"] for row in records["PR165_B_CombinationFingerprintRegistry.report.json"]}
    for row in records["PR165_B_CandidateVersionMemoryRegistry.report.json"]:
        for field in required:
            _expect(row.get(field) not in (None, "", []), failures, f"memory row missing {field}")
        _expect(row["memory_classification"] in MEMORY_CLASSIFICATIONS, failures, "invalid memory classification")
        _expect(row["condition_fingerprint_id"] in condition_ids, failures, "memory row condition fingerprint not found")
        _expect(row["combination_fingerprint_id"] in combination_ids, failures, "memory row combination fingerprint not found")
        _expect(row.get("source_truth_conversion_by_PR165_B") is False, failures, "source candidate treated as source truth")
        _expect(row.get("live_selection_allowed") is False, failures, "memory row permits live selection")
        if row["memory_classification"] == "STRUCTURAL_INVALIDITY_ARCHIVE_CANDIDATE":
            failures.append("structural invalidity archive candidate must include complete evidence; none expected in PR165-B")


def _validate_policy_rows(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    attribution_ids = {row["candidate_packet_id"] for row in records["PR165_B_OutcomeAttributionLedger.report.json"]}
    counterfactual_ids = {row["candidate_packet_id"] for row in records["PR165_B_CounterfactualAttributionLedger.report.json"]}
    cooldown_ids = {row["candidate_packet_id"] for row in records["PR165_B_CooldownPolicyRegistry.report.json"]}
    retest_ids = {row["candidate_packet_id"] for row in records["PR165_B_RetestEligibilityRegistry.report.json"]}
    repair_ids = {row["candidate_packet_id"] for row in records["PR165_B_RepairRouteHandoffRegistry.report.json"]}
    retest_queue_ids = {row["candidate_packet_id"] for row in records["PR165_B_ReplayPaperRetestQueue.report.json"]}
    for row in records["PR165_B_CandidateVersionMemoryRegistry.report.json"]:
        if is_non_positive_memory(row["memory_classification"]):
            cid = row["candidate_packet_id"]
            _expect(cid in attribution_ids, failures, "non-positive row lacks outcome attribution")
            _expect(cid in counterfactual_ids, failures, "non-positive row lacks counterfactual attribution")
            _expect(cid in cooldown_ids, failures, "non-positive row lacks cooldown policy")
            _expect(cid in retest_ids, failures, "non-positive row lacks retest policy")
            _expect(cid in retest_queue_ids, failures, "non-positive row lacks retest queue entry")
        if requires_repair(row["memory_action_policy"]):
            _expect(row["candidate_packet_id"] in repair_ids, failures, "repair-required row lacks repair route")
    for row in records["PR165_B_OutcomeAttributionLedger.report.json"]:
        _expect(abs(float(row.get("attribution_weight_sum", 0.0)) - 1.0) <= 0.00001, failures, "attribution weights must sum to 1")
    for row in records["PR165_B_SimilarityMatchPolicyRegistry.report.json"]:
        _expect(row.get("nearest_neighbor_memory_confidence_cap") is not None, failures, "similarity row lacks confidence cap")
    for row in records["PR165_B_PositiveConditionScopedPreferenceRegistry.report.json"]:
        for field in (
            "minimum_evidence_sufficiency_score",
            "minimum_false_discovery_adjusted_confidence",
            "minimum_confidence_to_prefer",
            "minimum_liquidity_to_prefer",
            "maximum_spread_to_prefer",
            "maximum_latency_to_prefer",
            "maximum_TCA_to_prefer",
            "model_risk_ceiling",
            "repair_confidence_floor",
            "source_provenance_floor",
        ):
            _expect(row.get(field) not in (None, "", []), failures, f"positive memory row missing {field}")
    for row in records["PR165_B_AgentSelectionOverlayHandoff.report.json"]:
        _expect(row["overlay_action"] in AGENT_SELECTION_OVERLAY_ACTIONS, failures, "invalid overlay action")
        for forbidden in FORBIDDEN_OVERLAY_ACTIONS:
            _expect(row["overlay_action"] != forbidden, failures, "forbidden overlay action used")


def _validate_quantum(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    memory_by_id = {row["candidate_packet_id"]: row for row in records["PR165_B_CandidateVersionMemoryRegistry.report.json"]}
    quantum_ids = {row["candidate_packet_id"] for row in records["PR165_B_QuantumNegativeMemoryRegistry.report.json"]}
    for row in records["PR165_B_QuantumNegativeMemoryRegistry.report.json"]:
        _expect(row.get("quantum_backend_execution_count") == 0, failures, "quantum backend execution count must be zero")
        _expect(row.get("quantum_advantage_claim_count") == 0, failures, "quantum advantage claim count must be zero")
        _expect(row.get("quantum_failure_attribution"), failures, "quantum row lacks failure attribution")
    for row in memory_by_id.values():
        if is_non_positive_memory(row["memory_classification"]) and any("quantum_mapper_advisory_agent" == agent for agent in row["downstream_agent_route"]):
            _expect(row["candidate_packet_id"] in quantum_ids, failures, "quantum-compatible non-positive row lacks quantum attribution")


def _validate_external(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    _expect(len(records["PR165_B_ExternalFailureAttributionCandidateRegistry.report.json"]) >= 50, failures, "external candidate records below target")
    _expect(len(records["PR165_B_ExternalConditionMemoryScoutingLedger.report.json"]) >= 20, failures, "external condition design records below target")
    _expect(len(records["PR165_B_ExternalQuantumFailureAttributionRegistry.report.json"]) >= 10, failures, "external quantum records below target")
    for filename in (
        "PR165_B_ExternalFailureAttributionCandidateRegistry.report.json",
        "PR165_B_ExternalConditionMemoryScoutingLedger.report.json",
        "PR165_B_ExternalMicrostructureConditionRegistry.report.json",
        "PR165_B_ExternalQuantumFailureAttributionRegistry.report.json",
        "PR165_B_ExternalScoutingMappabilityDecisionLedger.report.json",
    ):
        for row in records[filename]:
            _expect(row.get("source_truth_conversion_by_PR165_B") is False, failures, f"{filename} converts source truth")
            _expect(row.get("source_url"), failures, f"{filename} lacks source URL")


def _validate_authority(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key, expected in BOUNDARY_COUNT_FIELDS.items():
                value = row.get(key)
                if value not in (None, expected):
                    failures.append(f"{filename} authority count drift for {key}: {value!r}")


def _validate_no_scattered_literals(repo_root: Path, failures: list[str]) -> None:
    scan_roots = [
        repo_root / p.PACKAGE_DIR,
        repo_root / p.TEST_DIR,
    ]
    scan_files = [
        repo_root / "tools/build_pr165_b_condition_scoped_negative_memory.py",
        repo_root / "tools/validate_pr165_b_condition_scoped_negative_memory.py",
    ]
    for root in scan_roots:
        if root.exists():
            scan_files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".json"})
    generated = repo_root / p.GENERATED_DIR
    if generated.exists():
        scan_files.extend(generated.glob("PR165_B_*.report.json"))
    if (repo_root / p.SHARD_DIR).exists():
        scan_files.extend((repo_root / p.SHARD_DIR).glob("PR165_B_*.report.json"))
    for path in sorted(set(scan_files)):
        if path.name in SCATTERED_LITERAL_SCAN_EXCLUDED_PATH_NAMES:
            continue
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for literal in FORBIDDEN_SCATTERED_LITERALS:
            if " " in literal:
                found = literal in text
            else:
                found = re.search(rf"(?<![a-z0-9_]){re.escape(literal)}(?![a-z0-9_])", text) is not None
            if found:
                failures.append(f"scattered PR165-B literal outside central vocab: {literal!r} in {path.relative_to(repo_root).as_posix()}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
