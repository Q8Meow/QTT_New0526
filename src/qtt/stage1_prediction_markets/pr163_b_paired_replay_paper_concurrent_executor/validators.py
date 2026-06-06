"""Fail-closed validator for PR163-B generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    validate_pr163_b_ref,
    validate_record_authority,
)
from .json_io import read_json, records_from_payload
from .report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES, load_report_records
from .scenario_stress import STRESS_DIMENSIONS


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_inputs(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    records = {filename: load_report_records(repo_root, payload) for filename, payload in reports.items()}
    _validate_common_contracts(repo_root, reports, records, failures)
    summary = records["PR163_B_FinalSummary.report.json"][0]
    candidate_count = int(summary.get("candidate_packet_universe_count", 0))
    _validate_materialization_counts(records, summary, candidate_count, failures)
    _validate_not_queue_only(summary, failures)
    _validate_replay_paper(records, summary, failures)
    _validate_leakage(records, failures)
    _validate_fill_integrity(records, failures)
    _validate_tca(records, failures)
    _validate_remediation(records, summary, failures)
    _validate_stress(records, summary, failures)
    _validate_source_boundary(records, failures)
    _validate_authority(summary, records, failures)
    _validate_plain_refs(records, failures)
    _validate_manifest(reports, records, failures)
    _validate_orphans(records, failures)
    _validate_no_root_scratch(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR163-B report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR163-B report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR163-B schema: {filename}")


def _validate_required_inputs(repo_root: Path, failures: list[str]) -> None:
    required = (
        "PR162D_R2A_CandidatePacketV1Registry.report.json",
        *p.PR162RB_REQUIRED_ARTIFACTS,
        *p.PR163_REQUIRED_ARTIFACTS,
    )
    for filename in required:
        if not (repo_root / p.GENERATED_DIR / filename).exists():
            failures.append(f"missing required upstream artifact: {filename}")


def _validate_common_contracts(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    records: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR163-B", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        if filename in p.ROW_LEVEL_REPORTS:
            _expect(payload.get("records") == [], failures, f"{filename} compact root must not duplicate row records")
            _expect(payload.get("sharded_flag") is True, failures, f"{filename} must be sharded")
            _expect(payload.get("record_count") == payload.get("total_row_count"), failures, f"{filename} root row count mismatch")
        else:
            _expect(payload.get("record_count") == len(records_from_payload(payload)), failures, f"{filename} record_count mismatch")
        for key, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(key) is expected, failures, f"{filename} top-level authority flag drift: {key}")
        path = repo_root / p.GENERATED_DIR / filename
        if filename.startswith("PR163_B_") and path.exists():
            _expect(path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES, failures, f"{filename} exceeds 10 MiB root report limit")
        for shard_path in payload.get("shard_files") or []:
            resolved = p.resolve_repo_relative(repo_root, shard_path)
            _expect(resolved.exists(), failures, f"{filename} missing shard: {shard_path}")
            if resolved.exists():
                _expect(resolved.stat().st_size <= SHARD_LIMIT_BYTES, failures, f"{shard_path} exceeds 25 MiB shard limit")
        for record in records[filename]:
            failures.extend(validate_record_authority(record).failures)


def _validate_materialization_counts(
    records: dict[str, list[dict[str, Any]]],
    summary: dict[str, Any],
    candidate_count: int,
    failures: list[str],
) -> None:
    _expect(candidate_count > 0, failures, "candidate_packet_universe_count <= 0")
    equal_reports = {
        "paired_run_input_rows": "PR163_B_PairedReplayPaperRunInputRegistry.report.json",
        "paired_clock_rows": "PR163_B_PairedReplayPaperClockRegistry.report.json",
        "input_lock_rows": "PR163_B_ReplayPaperInputLockReceiptRegistry.report.json",
        "leakage_guard_rows": "PR163_B_ReplayPaperLeakageAsOfGuardReceiptRegistry.report.json",
        "replay_trace_or_exact_reason_rows": "PR163_B_ReplayLaneExecutionTraceRegistry.report.json",
        "paper_trace_rows": "PR163_B_PaperLaneExecutionTraceRegistry.report.json",
        "fill_integrity_or_exact_reason_rows": "PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json",
        "alignment_receipt_rows": "PR163_B_ReplayPaperAlignmentReceiptRegistry.report.json",
        "comparison_candidate_rows": "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json",
        "divergence_classification_rows": "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json",
        "rejection_remediation_rows": "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json",
        "transaction_cost_analysis_rows": "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
        "walk_forward_holdout_rows": "PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json",
        "quantum_carry_forward_rows": "PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json",
        "llm_future_review_handoff_rows": "PR163_B_ReplayPaperLLMFutureReviewHandoffRegistry.report.json",
        "qku_formula_algorithm_agent_routing_rows": "PR163_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
        "pr164_handoff_rows": "PR163_B_PR164ReviewProvenanceHandoff.report.json",
        "pr165_handoff_rows": "PR163_B_PR165ScoringRankingHandoff.report.json",
        "pr166_handoff_rows": "PR163_B_PR166LLMReviewResearchHandoff.report.json",
    }
    for field, filename in equal_reports.items():
        _expect(summary.get(field) == candidate_count, failures, f"{field} must equal candidate universe")
        _expect(len(records[filename]) == candidate_count, failures, f"{filename} must cover candidate universe")
    _expect(summary.get("execution_outcome_candidate_rows") == candidate_count * 3, failures, "outcome candidate rows must include replay/paper/paired lanes")
    _expect(summary.get("replay_result_candidate_rows") == candidate_count, failures, "replay result candidate rows must equal universe")
    _expect(summary.get("paper_result_candidate_rows") == candidate_count, failures, "paper result candidate rows must equal universe")
    _expect(summary.get("paired_result_candidate_rows") == candidate_count, failures, "paired result candidate rows must equal universe")
    _expect(summary.get("scenario_stress_rows", 0) == candidate_count * len(STRESS_DIMENSIONS), failures, "scenario stress rows must cover every dimension per candidate")
    _expect(summary.get("paired_comparison_complete_rows", 0) >= 4108, failures, "paired comparison complete rows below minimum")
    _expect(summary.get("quantum_bound_carry_forward_rows", 0) >= 1160, failures, "quantum carry-forward rows below PR162R-B quantum-bound target")


def _validate_not_queue_only(summary: dict[str, Any], failures: list[str]) -> None:
    for field in (
        "replay_trace_rows",
        "paper_trace_rows",
        "comparison_candidate_rows",
        "divergence_classification_rows",
        "rejection_remediation_rows",
        "transaction_cost_analysis_rows",
        "leakage_guard_rows",
        "fill_integrity_receipt_rows",
    ):
        _expect(summary.get(field, 0) > 0, failures, f"{field} missing; PR163-B would be metadata/queue-only")


def _validate_replay_paper(records: dict[str, list[dict[str, Any]]], summary: dict[str, Any], failures: list[str]) -> None:
    replay_rows = records["PR163_B_ReplayLaneExecutionTraceRegistry.report.json"]
    paper_rows = records["PR163_B_PaperLaneExecutionTraceRegistry.report.json"]
    comparison_rows = records["PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json"]
    divergence_rows = records["PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json"]
    _expect(any(row["replay_truth_status"] != "REPLAY_DISABLED_WITH_EXACT_REASON" for row in replay_rows), failures, "all replay traces disabled")
    _expect(any(row["paper_truth_status"] != "PAPER_DISABLED_WITH_EXACT_REASON" for row in paper_rows), failures, "all paper traces disabled")
    _expect(any(row["comparison_status"] == "PAIRED_COMPARISON_COMPLETE" for row in comparison_rows), failures, "all comparisons non-comparable")
    divergence_classes = set()
    for row in divergence_rows:
        divergence_classes.update(row.get("divergence_classes", []))
    for required in (
        "PAPER_PASS_REPLAY_PASS",
        "PAPER_PASS_REPLAY_REJECT",
        "PAPER_REJECT_REPLAY_PASS",
        "PAPER_REJECT_REPLAY_REJECT",
    ):
        _expect(required in divergence_classes, failures, f"missing pass/reject divergence class: {required}")
    _expect(summary.get("divergence_counts_by_class"), failures, "no divergence classes recorded")


def _validate_leakage(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_B_ReplayPaperLeakageAsOfGuardReceiptRegistry.report.json"]:
        _expect(row["future_data_used"] is False, failures, "future data used")
        _expect(row["post_decision_trade_used_for_pretrade"] is False, failures, "post-decision trade used for pretrade")
        _expect(row["post_resolution_field_used_for_pretrade"] is False, failures, "post-resolution field used for pretrade")
        _expect(row["lookahead_leakage_detected"] is False, failures, "lookahead leakage detected")
        _expect(row["settlement_label_available_before_decision"] is False, failures, "settlement label available before decision")
        _expect(row.get("source_as_of_time"), failures, "source_as_of_time missing")
        _expect(row.get("feature_as_of_time"), failures, "feature_as_of_time missing")


def _validate_fill_integrity(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json"]:
        requested = float(row["requested_qty"])
        replay_filled = float(row["replay_filled_qty"])
        paper_filled = float(row["paper_filled_qty"])
        _expect(replay_filled <= requested + 0.000001, failures, "replay filled quantity exceeds requested")
        _expect(paper_filled <= requested + 0.000001, failures, "paper filled quantity exceeds requested")
        _expect(abs(float(row["replay_level_fill_qty_sum"]) - replay_filled) <= 0.000001, failures, "replay level fills inconsistent")
        if paper_filled > 0:
            _expect(abs(float(row["paper_level_fill_qty_sum"]) - paper_filled) <= 0.000001, failures, "paper level fills inconsistent")
        if row["order_type"] == "FOK" and replay_filled > 0:
            _expect(abs(replay_filled - requested) <= 0.000001, failures, "FOK partial replay fill allowed")
        if row["order_type"] == "FAK":
            _expect(float(row["paper_unfilled_qty"]) >= 0, failures, "FAK residual invalid")
        if row["order_type"] == "POST_ONLY":
            _expect(paper_filled == 0, failures, "post-only marketable order filled")


def _validate_tca(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for row in records["PR163_B_TransactionCostAnalysisCandidateRegistry.report.json"]:
        for field in (
            "edge_before_cost",
            "edge_after_cost_replay",
            "edge_after_cost_paper",
            "replay_fees",
            "paper_fees",
            "replay_slippage",
            "paper_slippage",
            "replay_spread_cost",
            "paper_spread_cost",
            "replay_implementation_shortfall_candidate",
            "paper_implementation_shortfall_candidate",
        ):
            _expect(field in row, failures, f"TCA field missing: {field}")
        _expect(row["cost_model_truth_status"], failures, "TCA source status missing")
        _expect(row["no_profit_evidence"] is True, failures, "TCA labeled as profit evidence")


def _validate_remediation(records: dict[str, list[dict[str, Any]]], summary: dict[str, Any], failures: list[str]) -> None:
    rows = records["PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json"]
    rejected = [row for row in rows if row["paper_pretrade_status"] != "PAPER_PRETRADE_PASS"]
    _expect(len(rejected) == summary.get("pr163_reported_paper_pretrade_rejected_rows"), failures, "PR163 rejected rows not fully represented")
    _expect(any(row["remediation_family"].startswith("VALID_") for row in rejected), failures, "valid rejection classification missing")
    _expect(any(row["repairability"] == "REPAIRABLE_PRE_LAUNCH" for row in rejected), failures, "artificial repairable rejection classification missing")
    for row in rejected:
        _expect(row.get("downstream_pr164_ref"), failures, "rejected row missing PR164 handoff")
        _expect(row.get("downstream_pr165_ref"), failures, "rejected row missing PR165 handoff")
        _expect(row.get("no_forced_pass") is True, failures, "remediation forces unsafe candidate to pass")


def _validate_stress(records: dict[str, list[dict[str, Any]]], summary: dict[str, Any], failures: list[str]) -> None:
    rows = records["PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json"]
    dims = {row["stress_dimension"] for row in rows}
    _expect(dims == set(STRESS_DIMENSIONS), failures, "stress dimension coverage mismatch")
    for dim in STRESS_DIMENSIONS:
        _expect(summary.get("stress_coverage_counts", {}).get(dim, 0) > 0, failures, f"stress dimension has zero rows: {dim}")


def _validate_source_boundary(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    row = records["PR163_B_SourceEvidenceBoundaryAudit.report.json"][0]
    _expect(row["owner_definitions_treated_as_external_fact_authority"] is False, failures, "owner definitions treated as external fact authority")
    _expect(row["retrieval_target_readiness_treated_as_accepted_source_fact"] is False, failures, "retrieval readiness treated as accepted fact")
    _expect(row["candidate_source_packet_unlocks_connector_semantics"] is False, failures, "candidate source unlocks connector semantics")
    _expect(row["source_acceptance_count"] == 0, failures, "source acceptance count > 0")
    _expect(row["connector_binding_count"] == 0, failures, "connector binding count > 0")


def _validate_authority(summary: dict[str, Any], records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(key) == expected, failures, f"summary boundary count drift: {key}={summary.get(key)}")
    for filename, rows in records.items():
        for row in rows:
            for key, expected in BOUNDARY_COUNT_FIELDS.items():
                if key in row:
                    _expect(row[key] == expected, failures, f"{filename} boundary count drift: {key}={row[key]}")
            _expect("AtomicRows.bundle.sha256" not in str(row), failures, "AtomicRows.bundle.sha256 appears")


def _validate_plain_refs(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    for filename, rows in records.items():
        for row in rows:
            for key, value in row.items():
                if isinstance(value, str) and value.startswith("PR163B_") and (key.endswith("_ref") or key.endswith("_id")):
                    failures.extend(validate_pr163_b_ref(value).failures)
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.startswith("PR163B_"):
                            failures.extend(validate_pr163_b_ref(item).failures)


def _validate_manifest(reports: dict[str, dict[str, Any]], records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    rows = records["PR163_B_ReportManifest.report.json"]
    _expect({row["report_filename"] for row in rows} == set(p.REPORT_FILENAMES), failures, "manifest does not list every report")
    for row in rows:
        payload = reports[row["report_filename"]]
        _expect(row["row_count"] == payload.get("total_row_count", payload.get("record_count", 0)), failures, f"manifest row count mismatch: {row['report_filename']}")
        if row["report_filename"] in p.ROW_LEVEL_REPORTS:
            _expect(row["sharded_flag"] is True, failures, f"manifest missing sharded flag: {row['report_filename']}")
            _expect(row["shard_paths"] == payload.get("shard_files"), failures, f"manifest shard paths mismatch: {row['report_filename']}")


def _validate_orphans(records: dict[str, list[dict[str, Any]]], failures: list[str]) -> None:
    row = records["PR163_B_OrphanReplayPaperArtifactAudit.report.json"][0]
    for key, value in row.items():
        if key.startswith("orphan_") and key.endswith("_ref") is False:
            _expect(value == 0, failures, f"orphan count nonzero: {key}={value}")


def _validate_no_root_scratch(repo_root: Path, failures: list[str]) -> None:
    for path in repo_root.iterdir():
        if not path.is_file():
            continue
        name = path.name
        if name.startswith("PR163_B") and path.suffix.lower() in {".txt", ".json", ".zip"}:
            failures.append(f"root-level PR163-B scratch artifact exists: {name}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
