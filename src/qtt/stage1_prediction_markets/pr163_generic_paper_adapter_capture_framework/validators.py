"""Fail-closed validator for PR163 generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    validate_pr163_ref,
    validate_record_authority,
)
from .json_io import read_json, records_from_payload
from .paper_pretrade_checks import REQUIRED_CHECKS
from .paper_scenario_grid import SCENARIOS


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports = _load_reports(repo_root, failures)
    _validate_schemas(repo_root, failures)
    _validate_required_pr162rb_inputs(repo_root, failures)
    if failures:
        return ValidationResult(False, tuple(failures))
    _validate_common_contracts(reports, failures)
    summary = reports["PR163_FinalSummary.report.json"]
    _validate_summary(summary, failures)
    _validate_materialized_universe(reports, summary, failures)
    _validate_pretrade(reports, failures)
    _validate_state_machine(reports, failures)
    _validate_fill_simulator(reports, failures)
    _validate_ledger(reports, summary, failures)
    _validate_scenarios(reports, failures)
    _validate_qku_quantum_llm_handoffs(reports, summary, failures)
    _validate_authority(summary, reports, failures)
    _validate_plain_refs(reports, failures)
    _validate_manifest(reports, failures)
    return ValidationResult(not failures, tuple(failures))


def _load_reports(repo_root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        path = repo_root / p.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR163 report: {filename}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR163 report is not an object: {filename}")
            continue
        reports[filename] = payload
    return reports


def _validate_schemas(repo_root: Path, failures: list[str]) -> None:
    for filename in p.SCHEMA_FILENAMES:
        if not p.schema_path(repo_root, filename).exists():
            failures.append(f"missing PR163 schema: {filename}")


def _validate_required_pr162rb_inputs(repo_root: Path, failures: list[str]) -> None:
    for filename in p.PR162RB_REQUIRED_ARTIFACTS:
        if not (repo_root / p.GENERATED_DIR / filename).exists():
            failures.append(f"missing required PR162R-B artifact: {filename}")


def _validate_common_contracts(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_filename") == filename, failures, f"{filename} report_filename mismatch")
        _expect(payload.get("created_by_pr") == "PR163", failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == AUTHORITY_CLASS, failures, f"{filename} authority_class mismatch")
        _expect(payload.get("validation_status") == "PASS", failures, f"{filename} validation_status must be PASS")
        _expect(isinstance(payload.get("records"), list), failures, f"{filename} missing records list")
        _expect(payload.get("record_count") == len(payload.get("records", [])), failures, f"{filename} record_count mismatch")
        for key, expected in NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(key) is expected, failures, f"{filename} top-level authority flag drift: {key}")
        for record in records_from_payload(payload):
            failures.extend(validate_record_authority(record).failures)


def _validate_summary(summary_payload: dict[str, Any], failures: list[str]) -> None:
    summary = records_from_payload(summary_payload)[0]
    candidate_count = summary.get("candidate_packet_universe_count", 0)
    _expect(candidate_count > 0, failures, "candidate_packet_universe_count <= 0")
    for field in (
        "paper_adapter_input_rows",
        "paper_decision_intent_rows",
        "paper_pretrade_receipt_rows",
        "paper_adapter_run_plan_rows",
        "paper_qku_agent_routing_rows",
        "qku_prioritization_feature_handoff_rows",
        "llm_future_handoff_exclusion_receipt_rows",
        "pr163_b_handoff_rows",
        "pr164_handoff_rows",
        "pr165_handoff_rows",
        "pr166_handoff_rows",
    ):
        _expect(summary.get(field) == candidate_count, failures, f"{field} must equal candidate universe")
    for field in (
        "paper_order_intent_rows",
        "paper_order_state_transition_rows",
        "paper_synthetic_fill_event_rows",
        "paper_portfolio_ledger_snapshot_rows",
        "paper_cash_reservation_receipt_rows",
        "paper_execution_cost_receipt_rows",
        "paper_latency_slippage_receipt_rows",
        "paper_capture_event_rows",
        "paper_capture_bundle_rows",
    ):
        _expect(summary.get(field, 0) > 0, failures, f"{field} must be materialized")
    _expect(summary.get("venue_adapter_capability_rows") == 4, failures, "venue adapter capability rows must be 4")
    _expect(summary.get("ledger_invariant_violation_count") == 0, failures, "ledger invariant violations must be zero")
    _expect(summary.get("depth_walk_fill_event_rows", 0) > 0, failures, "depth walk coverage missing")
    _expect(summary.get("partial_fill_rows", 0) > 0, failures, "partial fill coverage missing")
    _expect(summary.get("quantum_advisory_rows", 0) >= summary.get("candidate_packet_universe_count", 0), failures, "quantum advisory coverage missing")
    _expect(summary.get("quantum_bound_advisory_rows", 0) >= 1160, failures, "quantum-bound advisory rows below PR162R-B target")
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(key) == expected, failures, f"summary boundary count drift: {key}={summary.get(key)}")


def _validate_materialized_universe(reports: dict[str, dict[str, Any]], summary_payload: dict[str, Any], failures: list[str]) -> None:
    candidate_count = records_from_payload(summary_payload)[0]["candidate_packet_universe_count"]
    row_reports = {
        "PR163_PaperAdapterInputRegistry.report.json",
        "PR163_PaperDecisionIntentRegistry.report.json",
        "PR163_PaperOrderIntentRegistry.report.json",
        "PR163_PaperPreTradeCheckReceiptRegistry.report.json",
        "PR163_PaperRiskPolicyReceiptRegistry.report.json",
        "PR163_PaperPortfolioLedgerSnapshotRegistry.report.json",
        "PR163_PaperCashReservationReceiptRegistry.report.json",
        "PR163_PaperExecutionCostReceiptRegistry.report.json",
        "PR163_PaperLatencySlippageReceiptRegistry.report.json",
        "PR163_PaperCaptureEventRegistry.report.json",
        "PR163_PaperAdapterRunPlanRegistry.report.json",
        "PR163_PaperAdapterCaptureBundleRegistry.report.json",
        "PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json",
        "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json",
        "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json",
        "PR163_PR163BPairedReplayPaperExecutorHandoff.report.json",
        "PR163_PR164ReviewProvenanceHandoff.report.json",
        "PR163_PR165ScoringRankingHandoff.report.json",
        "PR163_PR166LLMReviewResearchHandoff.report.json",
    }
    for filename in row_reports:
        _expect(len(records_from_payload(reports[filename])) == candidate_count, failures, f"{filename} must cover universe")


def _validate_pretrade(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR163_PaperPreTradeCheckReceiptRegistry.report.json"])
    _expect(any(row.get("pretrade_status") == "PAPER_PRETRADE_PASS" for row in rows), failures, "no pretrade pass rows")
    _expect(any(row.get("pretrade_status") == "PAPER_PRETRADE_REJECT_WITH_EXACT_REASON" for row in rows), failures, "no exact pretrade rejection rows")
    for row in rows:
        checks = row.get("check_results", {})
        for check in REQUIRED_CHECKS:
            _expect(check in checks, failures, f"pretrade check missing: {check}")
        if row.get("pretrade_status") != "PAPER_PRETRADE_PASS":
            _expect(row.get("exact_reject_reasons"), failures, "pretrade rejection lacks exact reason")
        _expect("BLOCKER" not in str(row), failures, "pretrade row uses BLOCKER")


def _validate_state_machine(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR163_PaperOrderStateTransitionRegistry.report.json"])
    _expect(rows, failures, "state transition registry empty")
    next_states = {row.get("next_state") for row in rows}
    for required in (
        "DECISION_INTENT_CREATED",
        "INTENT_CREATED",
        "PRETRADE_CHECKED",
        "ACCEPTED_TO_PAPER_OMS",
        "RESTING",
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELLED",
        "EXPIRED",
        "REJECTED",
        "STALE_QUOTE_REJECTED",
        "INSUFFICIENT_CASH_REJECTED",
        "INVALID_TICK_REJECTED",
        "INVALID_LIFECYCLE_REJECTED",
    ):
        _expect(required in next_states, failures, f"state coverage missing: {required}")
    for row in rows:
        _expect(row.get("sequence_number", 0) > 0, failures, "state transition sequence missing")
        _expect(row.get("consumed_input_refs"), failures, "state transition consumed refs missing")


def _validate_fill_simulator(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR163_PaperSyntheticFillEventRegistry.report.json"])
    _expect(rows, failures, "synthetic fill event registry empty")
    for row in rows:
        filled = float(row.get("filled_qty", 0.0))
        requested = float(row.get("requested_qty", 0.0))
        levels = row.get("level_fills", [])
        _expect(filled <= requested + 0.000001, failures, "fill quantity exceeds requested quantity")
        _expect(levels, failures, "filled event lacks depth walk level fills")
        level_total = sum(float(level["fill_qty_at_level"]) for level in levels)
        _expect(abs(level_total - filled) <= 0.000001, failures, "level fills do not sum to filled quantity")
        for level in levels:
            _expect(float(level["fill_qty_at_level"]) <= float(level["available_level_size"]) + 0.000001, failures, "level fill exceeds available depth")
        _expect(float(row.get("vwap_fill_price", 0.0)) > 0.0, failures, "fill event lacks positive VWAP")
        _expect(float(row.get("fee_per_share", 0.0)) >= 0.0, failures, "fee per share negative")
        _expect(float(row.get("slippage_per_share", 0.0)) >= 0.0, failures, "slippage per share negative")


def _validate_ledger(reports: dict[str, dict[str, Any]], summary_payload: dict[str, Any], failures: list[str]) -> None:
    audit_rows = records_from_payload(reports["PR163_PaperLedgerInvariantAudit.report.json"])
    _expect(audit_rows, failures, "ledger invariant audit missing")
    for row in audit_rows:
        _expect(row.get("violation_count") == 0, failures, f"ledger invariant violation: {row.get('invariant_name')}")
    snapshots = records_from_payload(reports["PR163_PaperPortfolioLedgerSnapshotRegistry.report.json"])
    for row in snapshots:
        lhs = round(float(row["paper_cash_start"]) - float(row["reserved_cash"]) - float(row["spent_cash"]) + float(row["received_cash"]), 6)
        rhs = round(float(row["paper_cash_end"]), 6)
        _expect(abs(lhs - rhs) <= 0.000001, failures, "ledger cash equation drift")
        _expect(float(row["reserved_cash"]) >= 0.0, failures, "reserved cash negative")
        _expect(float(row["available_paper_cash"]) >= 0.0, failures, "available paper cash negative")
        _expect(row.get("runtime_cash_receipt_created") is False, failures, "runtime cash receipt created")
        _expect(row.get("private_state_fetched") is False, failures, "private state fetched")


def _validate_scenarios(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR163_PaperScenarioCoverageMatrix.report.json"])
    by_name = {row["scenario_id"]: row for row in rows}
    for scenario in SCENARIOS:
        row = by_name.get(scenario.name)
        _expect(row is not None, failures, f"scenario missing: {scenario.name}")
        if row:
            _expect(row.get("scenario_rows", 0) > 0, failures, f"scenario has zero rows: {scenario.name}")
    for required in (
        "MARKETABLE_BUY_FULL_FILL",
        "PARTIAL_FILL_BUY",
        "FOK_KILL_NO_FILL",
        "FAK_PARTIAL_FILL_CANCEL_RESIDUAL",
        "POST_ONLY_REJECT_MARKETABLE",
        "STALE_QUOTE_REJECT",
        "INSUFFICIENT_CASH_REJECT",
        "INVALID_TICK_REJECT",
    ):
        _expect(required in by_name and by_name[required]["scenario_rows"] > 0, failures, f"required scenario coverage missing: {required}")


def _validate_qku_quantum_llm_handoffs(reports: dict[str, dict[str, Any]], summary_payload: dict[str, Any], failures: list[str]) -> None:
    summary = records_from_payload(summary_payload)[0]
    candidate_count = summary["candidate_packet_universe_count"]
    for filename in (
        "PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json",
        "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json",
        "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json",
    ):
        _expect(len(records_from_payload(reports[filename])) == candidate_count, failures, f"{filename} count mismatch")
    for row in records_from_payload(reports["PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json"]):
        for field in (
            "expected_value_ref_or_value",
            "edge_after_fees_slippage_spread",
            "fill_probability_candidate",
            "orderbook_depth_ref_or_value",
            "latency_sensitivity_bucket",
            "capital_lockup_estimate",
            "event_exposure_ref_or_value",
            "settlement_risk_ref_or_value",
            "data_quality_tier",
            "quantum_compatibility_status",
        ):
            _expect(field in row, failures, f"qku prioritization handoff lacks {field}")
        _expect(row.get("no_score_created") is True, failures, "qku handoff created score")
        _expect(row.get("no_rank_created") is True, failures, "qku handoff created rank")
        _expect(row.get("no_promotion_created") is True, failures, "qku handoff created promotion")
        _expect(row.get("replay_result_created") is False, failures, "qku handoff created replay result")
        _expect(row.get("paper_result_created") is False, failures, "qku handoff created paper result")
    for row in records_from_payload(reports["PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json"]):
        for field in (
            "llm_hot_path_allowed",
            "llm_live_order_release_allowed",
            "llm_source_acceptance_allowed",
            "llm_result_rewrite_allowed",
            "no_llm_runtime_inference",
            "no_llm_model_loading",
            "no_llm_api_call",
            "no_llm_prompt_execution",
            "no_llm_order_release",
            "no_llm_source_acceptance",
            "no_llm_result_rewrite",
        ):
            expected = False if field.endswith("_allowed") else True
            _expect(row.get(field) is expected, failures, f"LLM exclusion field drift: {field}")
    quantum_rows = records_from_payload(reports["PR163_PaperQuantumAdvisoryInputRegistry.report.json"])
    _expect(len(quantum_rows) == candidate_count, failures, "quantum advisory row count mismatch")
    _expect(sum(1 for row in quantum_rows if row.get("quantum_compatibility_status") == "QUANTUM_PAPER_ADVISORY_COMPATIBLE") >= 1160, failures, "quantum compatible advisory rows below 1160")


def _validate_authority(summary_payload: dict[str, Any], reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = records_from_payload(summary_payload)[0]
    for key, expected in BOUNDARY_COUNT_FIELDS.items():
        _expect(summary.get(key) == expected, failures, f"authority count drift: {key}")
    for key in (
        "llm_hot_path_allowed_count",
        "llm_runtime_inference_count",
        "llm_model_loading_count",
        "llm_api_call_count",
        "llm_prompt_execution_count",
        "llm_order_release_count",
        "llm_source_acceptance_count",
        "llm_result_rewrite_count",
    ):
        _expect(summary.get(key) == 0, failures, f"LLM authority count drift: {key}")
    for filename in (
        "PR163_NoPaperResultProfitLiveAuthorityAudit.report.json",
        "PR163_NoSourceAcceptanceConnectorPrivateStateAudit.report.json",
        "PR163_NoQuantumBackendAdvantageClaimAudit.report.json",
        "PR163_NoLLMHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json",
        "PR163_NoQTTChecksumFreezeAuthorityAudit.report.json",
    ):
        rows = records_from_payload(reports[filename])
        _expect(len(rows) == 1, failures, f"{filename} must have one audit row")
        for key, expected in BOUNDARY_COUNT_FIELDS.items():
            _expect(rows[0].get(key) == expected, failures, f"{filename} boundary count drift: {key}")


def _validate_plain_refs(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for filename, payload in reports.items():
        text = str(payload)
        _expect("AtomicRows.bundle.sha256" not in text, failures, f"{filename} contains AtomicRows.bundle.sha256")
        for record in records_from_payload(payload):
            for key, value in record.items():
                if isinstance(value, str) and key.endswith("_ref") and value.startswith("PR163_"):
                    failures.extend(validate_pr163_ref(value).failures)
                elif isinstance(value, list) and key.endswith("_refs"):
                    for item in value:
                        if isinstance(item, str) and item.startswith("PR163_"):
                            failures.extend(validate_pr163_ref(item).failures)


def _validate_manifest(reports: dict[str, dict[str, Any]], failures: list[str]) -> None:
    rows = records_from_payload(reports["PR163_ReportManifest.report.json"])
    filenames = {row.get("report_filename") for row in rows}
    _expect(filenames == set(p.REPORT_FILENAMES), failures, "manifest report filename set mismatch")
    counts = {filename: reports[filename].get("record_count", 0) for filename in reports if filename != "PR163_ReportManifest.report.json"}
    for row in rows:
        filename = row["report_filename"]
        if filename == "PR163_ReportManifest.report.json":
            _expect(row["row_count"] == len(p.REPORT_FILENAMES), failures, "manifest self row count mismatch")
        elif filename in counts:
            _expect(row["row_count"] == counts[filename], failures, f"manifest row count mismatch: {filename}")


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
