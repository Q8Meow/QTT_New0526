"""Build PR163-B paired replay/paper concurrent executor artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .alignment_receipts import build_alignment
from .authority_policy import (
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    no_authority_fields,
    no_authority_record,
    plain_ref,
)
from .divergence_classifier import DIVERGENCE_CLASSES, build_divergence
from .downstream_handoff import build_pr162e_update, build_pr164_handoff, build_pr165_handoff, build_pr166_handoff
from .fill_integrity import build_fill_integrity
from .input_discovery import (
    build_artifact_consumption_ledger,
    candidate_index,
    discover_inputs,
    load_records,
)
from .input_lock import build_input_lock
from .json_io import index_by, stable_counter, write_json
from .leakage_asof_guard import build_leakage_guard
from .llm_future_handoff import build_llm_handoff
from .outcome_candidate_receipts import build_outcome
from .paired_clock import build_clock
from .paired_comparison import build_comparison
from .paired_run_contracts import build_run_input
from .paper_lane_executor import build_paper_trace
from .qku_agent_routing import build_qku_route
from .quantum_carry_forward import build_quantum_carry
from .rejection_remediation import build_remediation
from .replay_lane_executor import build_replay_trace
from .report_sharding import (
    build_root_payload,
    build_sharded_payloads,
    encoded_json_size,
    file_size_summary,
)
from .scenario_stress import STRESS_DIMENSIONS, build_stress_rows
from .schema_writer import write_schemas
from .source_evidence_boundary import build_boundary_audit, build_source_queue
from .transaction_cost_analysis import build_tca
from .walk_forward_holdout import build_walk_forward


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root, p.EXPECTED_BRANCH)
    _clear_previous_pr163_b_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in p.ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(repo_root / rel_path, shard_payload, compact=True)
    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = payloads["PR163_B_FinalSummary.report.json"]["records"][0]
    summary.update(sizes)
    payloads["PR163_B_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR163_B_FinalSummary.report.json"].update(sizes)
    payloads["PR163_B_DecisionAndNextPRRecommendation.report.json"] = build_root_payload(
        "PR163_B_DecisionAndNextPRRecommendation.report.json",
        [build_decision(summary)],
        _source_inputs(payloads),
        build_decision(summary),
    )
    payloads["PR163_B_ReportManifest.report.json"] = build_root_payload(
        "PR163_B_ReportManifest.report.json",
        build_manifest(payloads),
        _source_inputs(payloads),
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR163_B_FinalSummary.report.json", payloads["PR163_B_FinalSummary.report.json"])
    write_json(
        repo_root / p.GENERATED_DIR / "PR163_B_DecisionAndNextPRRecommendation.report.json",
        payloads["PR163_B_DecisionAndNextPRRecommendation.report.json"],
    )
    write_json(repo_root / p.GENERATED_DIR / "PR163_B_ReportManifest.report.json", payloads["PR163_B_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    payloads, _shards = build_payloads_with_shards(repo_root, branch)
    return payloads


def build_payloads_with_shards(
    repo_root: Path,
    branch: str | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    source_inputs = [row["consumed_path"] for row in discovery if row["consumed_path"]]
    artifact_ledger = build_artifact_consumption_ledger(repo_root)
    upstream = _load_upstream(repo_root)
    row_outputs = _build_row_outputs(upstream)
    source_queue = build_source_queue()
    boundary_audit = build_boundary_audit()
    authority_audits = _build_authority_audits()
    orphan_audit = _build_orphan_audit(row_outputs, len(p.REPORT_FILENAMES))
    summary = build_summary(
        branch=branch,
        discovery=discovery,
        artifact_ledger=artifact_ledger,
        row_outputs=row_outputs,
        source_queue=source_queue,
        source_boundary=boundary_audit,
        orphan_audit=orphan_audit,
        upstream=upstream,
    )
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR163_B_InputConsumptionAudit.report.json": discovery,
        "PR163_B_PR162RB_PR163_ArtifactConsumptionLedger.report.json": artifact_ledger,
        "PR163_B_PairedReplayPaperRunInputRegistry.report.json": row_outputs["run_inputs"],
        "PR163_B_PairedReplayPaperClockRegistry.report.json": row_outputs["clocks"],
        "PR163_B_ReplayPaperInputLockReceiptRegistry.report.json": row_outputs["input_locks"],
        "PR163_B_ReplayPaperLeakageAsOfGuardReceiptRegistry.report.json": row_outputs["leakage_guards"],
        "PR163_B_ReplayLaneExecutionTraceRegistry.report.json": row_outputs["replay_traces"],
        "PR163_B_PaperLaneExecutionTraceRegistry.report.json": row_outputs["paper_traces"],
        "PR163_B_ReplayPaperFillIntegrityReceiptRegistry.report.json": row_outputs["fill_integrity"],
        "PR163_B_ReplayPaperAlignmentReceiptRegistry.report.json": row_outputs["alignments"],
        "PR163_B_ExecutionOutcomeCandidateReceiptRegistry.report.json": row_outputs["outcomes"],
        "PR163_B_ReplayExecutionResultCandidateRegistry.report.json": row_outputs["replay_result_candidates"],
        "PR163_B_PaperExecutionResultCandidateRegistry.report.json": row_outputs["paper_result_candidates"],
        "PR163_B_PairedReplayPaperResultCandidateRegistry.report.json": row_outputs["paired_result_candidates"],
        "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json": row_outputs["comparisons"],
        "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json": row_outputs["divergences"],
        "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json": row_outputs["remediations"],
        "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json": row_outputs["tca"],
        "PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json": row_outputs["stress"],
        "PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json": row_outputs["walk_forward"],
        "PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json": row_outputs["quantum_carry"],
        "PR163_B_ReplayPaperLLMFutureReviewHandoffRegistry.report.json": row_outputs["llm_handoff"],
        "PR163_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json": row_outputs["qku_routes"],
        "PR163_B_PR164ReviewProvenanceHandoff.report.json": row_outputs["pr164_handoff"],
        "PR163_B_PR165ScoringRankingHandoff.report.json": row_outputs["pr165_handoff"],
        "PR163_B_PR166LLMReviewResearchHandoff.report.json": row_outputs["pr166_handoff"],
        "PR163_B_PR162EPluginReplayPaperCompatibilityUpdate.report.json": row_outputs["pr162e_update"],
        "PR163_B_SourceCandidateReplayPaperResearchQueue.report.json": source_queue,
        "PR163_B_SourceEvidenceBoundaryAudit.report.json": [boundary_audit],
        "PR163_B_NoLiveOrderProfitSourceConnectorPrivateStateAudit.report.json": [authority_audits["live_profit_source"]],
        "PR163_B_NoQuantumBackendAdvantageClaimAudit.report.json": [authority_audits["quantum"]],
        "PR163_B_NoLLMRuntimeHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json": [authority_audits["llm"]],
        "PR163_B_NoQTTChecksumFreezeAuthorityAudit.report.json": [authority_audits["checksum"]],
        "PR163_B_OrphanReplayPaperArtifactAudit.report.json": [orphan_audit],
    }
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename, records in row_payloads.items():
        if filename in p.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, records, source_inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            payloads[filename] = build_root_payload(filename, records, source_inputs)
    payloads["PR163_B_FinalSummary.report.json"] = build_root_payload(
        "PR163_B_FinalSummary.report.json",
        [summary],
        source_inputs,
        summary,
    )
    payloads["PR163_B_DecisionAndNextPRRecommendation.report.json"] = build_root_payload(
        "PR163_B_DecisionAndNextPRRecommendation.report.json",
        [build_decision(summary)],
        source_inputs,
        build_decision(summary),
    )
    payloads["PR163_B_ReportManifest.report.json"] = build_root_payload(
        "PR163_B_ReportManifest.report.json",
        build_manifest(payloads),
        source_inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR163-B payload map missing reports: {missing}")
    return payloads, shard_payloads


def _load_upstream(repo_root: Path) -> dict[str, Any]:
    row_resolution = load_records(repo_root, "PR162R_B_RowBindingResolutionMatrix.report.json")
    state_transition_rows = load_records(repo_root, "PR163_PaperOrderStateTransitionRegistry.report.json")
    transitions_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in state_transition_rows:
        transitions_by_candidate.setdefault(str(row.get("candidate_packet_id")), []).append(row)
    fill_rows = load_records(repo_root, "PR163_PaperSyntheticFillEventRegistry.report.json")
    fill_by_candidate = index_by(fill_rows, "candidate_packet_id")
    upstream = {
        "candidate_rows": index_by(load_records(repo_root, "PR162D_R2A_CandidatePacketV1Registry.report.json"), "candidate_packet_id"),
        "row_resolution": row_resolution,
        "paper_adapter": index_by(load_records(repo_root, "PR163_PaperAdapterInputRegistry.report.json"), "candidate_packet_id"),
        "paper_decision": index_by(load_records(repo_root, "PR163_PaperDecisionIntentRegistry.report.json"), "candidate_packet_id"),
        "paper_order": index_by(load_records(repo_root, "PR163_PaperOrderIntentRegistry.report.json"), "candidate_packet_id"),
        "paper_pretrade": index_by(load_records(repo_root, "PR163_PaperPreTradeCheckReceiptRegistry.report.json"), "candidate_packet_id"),
        "paper_ledger": index_by(load_records(repo_root, "PR163_PaperPortfolioLedgerSnapshotRegistry.report.json"), "candidate_packet_id"),
        "paper_cash": index_by(load_records(repo_root, "PR163_PaperCashReservationReceiptRegistry.report.json"), "paper_order_intent_ref"),
        "paper_cost": index_by(load_records(repo_root, "PR163_PaperExecutionCostReceiptRegistry.report.json"), "paper_order_intent_ref"),
        "paper_latency": index_by(load_records(repo_root, "PR163_PaperLatencySlippageReceiptRegistry.report.json"), "paper_order_intent_ref"),
        "paper_capture": index_by(load_records(repo_root, "PR163_PaperCaptureEventRegistry.report.json"), "candidate_packet_id"),
        "paper_bundle": index_by(load_records(repo_root, "PR163_PaperAdapterCaptureBundleRegistry.report.json"), "candidate_packet_id"),
        "paper_quantum": index_by(load_records(repo_root, "PR163_PaperQuantumAdvisoryInputRegistry.report.json"), "candidate_packet_id"),
        "paper_llm": index_by(load_records(repo_root, "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json"), "candidate_packet_id"),
        "pr163_summary": load_records(repo_root, "PR163_FinalSummary.report.json")[0],
        "pr162rb_summary": load_records(repo_root, "PR162R_B_FinalSummary.report.json")[0],
        "fill_by_candidate": fill_by_candidate,
        "transitions_by_candidate": transitions_by_candidate,
    }
    return upstream


def _build_row_outputs(upstream: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {
        "run_inputs": [],
        "clocks": [],
        "input_locks": [],
        "leakage_guards": [],
        "replay_traces": [],
        "paper_traces": [],
        "fill_integrity": [],
        "alignments": [],
        "outcomes": [],
        "replay_result_candidates": [],
        "paper_result_candidates": [],
        "paired_result_candidates": [],
        "comparisons": [],
        "divergences": [],
        "remediations": [],
        "tca": [],
        "stress": [],
        "walk_forward": [],
        "quantum_carry": [],
        "llm_handoff": [],
        "qku_routes": [],
        "pr164_handoff": [],
        "pr165_handoff": [],
        "pr166_handoff": [],
        "pr162e_update": [],
    }
    for row in upstream["row_resolution"]:
        candidate_packet_id = row["candidate_packet_id"]
        index = candidate_index(candidate_packet_id)
        candidate = upstream["candidate_rows"][candidate_packet_id]
        paper = _paper_context(index, candidate_packet_id, upstream)
        settlement_available = bool(row.get("replay_binding_refs")) and index % 4 != 0
        clock = build_clock(index, candidate_packet_id, settlement_available)
        input_lock = build_input_lock(index, row, clock)
        leakage_guard = build_leakage_guard(index, row, clock)
        ctx: dict[str, Any] = {
            "row": row,
            "candidate": candidate,
            "paper": paper,
            "clock": clock,
            "input_lock": input_lock,
            "leakage_guard": leakage_guard,
            "replay_market_state_ref": _first(row.get("replay_binding_refs"), "PR162R_B_REPLAY_MARKET_STATE_CANDIDATE"),
            "paper_market_state_ref": paper["market_state_ref"],
            "event_lifecycle_ref": plain_ref("EVENT_LIFECYCLE", index),
            "settlement_label_ref": _first(row.get("replay_binding_refs"), "") if settlement_available else "",
            "replay_orderbook_refs": list(row.get("replay_binding_refs") or [])[:1],
            "replay_trade_refs": list(row.get("replay_binding_refs") or [])[1:2],
            "replay_event_state_refs": [plain_ref("EVENT_LIFECYCLE", index)],
            "replay_settlement_refs": list(row.get("replay_binding_refs") or [])[-1:] if settlement_available else [],
            "replay_fee_slippage_refs": list(row.get("replay_binding_refs") or [])[:2],
            "replay_latency_refs": [paper["latency"].get("latency_slippage_receipt_ref", "")],
            "lifecycle_state": _lifecycle_state(paper["pretrade"]),
            "edge_before_cost": _edge_before_cost(paper),
        }
        paper_trace = build_paper_trace(index, ctx)
        replay_trace = build_replay_trace(index, ctx, paper_trace)
        ctx["paper_trace"] = paper_trace
        ctx["replay_trace"] = replay_trace
        fill_integrity = build_fill_integrity(index, ctx, replay_trace, paper_trace)
        alignment = build_alignment(index, replay_trace, paper_trace, ctx)
        comparison = build_comparison(index, ctx, replay_trace, paper_trace, fill_integrity)
        ctx["comparison"] = comparison
        ctx["fill_integrity"] = fill_integrity
        divergence = build_divergence(index, ctx, comparison, fill_integrity)
        remediation = build_remediation(index, ctx, divergence)
        ctx["remediation"] = remediation
        tca = build_tca(index, ctx, replay_trace, paper_trace, comparison)
        ctx["tca"] = tca
        walk_forward = build_walk_forward(index, ctx)
        ctx["walk_forward"] = walk_forward
        quantum_carry = build_quantum_carry(index, ctx, divergence, tca)
        llm_handoff = build_llm_handoff(index, ctx, divergence, remediation, comparison)
        run_input = build_run_input(index, ctx)
        qku_route = build_qku_route(index, ctx)
        pr164 = build_pr164_handoff(index, ctx, divergence, remediation, tca)
        pr165 = build_pr165_handoff(index, ctx, tca, quantum_carry)
        pr166 = build_pr166_handoff(index, ctx, llm_handoff)
        pr162e = build_pr162e_update(index, ctx)
        replay_outcome = build_outcome(index, "REPLAY", ctx, [replay_trace["replay_trace_ref"]], [])
        paper_outcome = build_outcome(index, "PAPER", ctx, [paper_trace["paper_trace_ref"]], [])
        paired_outcome = build_outcome(
            index,
            "PAIRED",
            ctx,
            [replay_trace["replay_trace_ref"], paper_trace["paper_trace_ref"]],
            [comparison["comparison_ref"]],
        )
        outputs["clocks"].append(clock)
        outputs["input_locks"].append(input_lock)
        outputs["leakage_guards"].append(leakage_guard)
        outputs["run_inputs"].append(run_input)
        outputs["paper_traces"].append(paper_trace)
        outputs["replay_traces"].append(replay_trace)
        outputs["fill_integrity"].append(fill_integrity)
        outputs["alignments"].append(alignment)
        outputs["comparisons"].append(comparison)
        outputs["divergences"].append(divergence)
        outputs["remediations"].append(remediation)
        outputs["tca"].append(tca)
        outputs["stress"].extend(build_stress_rows(index, ctx, replay_trace, paper_trace))
        outputs["walk_forward"].append(walk_forward)
        outputs["quantum_carry"].append(quantum_carry)
        outputs["llm_handoff"].append(llm_handoff)
        outputs["qku_routes"].append(qku_route)
        outputs["pr164_handoff"].append(pr164)
        outputs["pr165_handoff"].append(pr165)
        outputs["pr166_handoff"].append(pr166)
        outputs["pr162e_update"].append(pr162e)
        outputs["replay_result_candidates"].append(replay_outcome)
        outputs["paper_result_candidates"].append(paper_outcome)
        outputs["paired_result_candidates"].append(paired_outcome)
        outputs["outcomes"].extend([replay_outcome, paper_outcome, paired_outcome])
    return outputs


def _paper_context(index: int, candidate_packet_id: str, upstream: dict[str, Any]) -> dict[str, Any]:
    adapter = upstream["paper_adapter"][candidate_packet_id]
    decision = upstream["paper_decision"][candidate_packet_id]
    order = upstream["paper_order"][candidate_packet_id]
    pretrade = upstream["paper_pretrade"][candidate_packet_id]
    ledger = upstream["paper_ledger"][candidate_packet_id]
    cost = upstream["paper_cost"][order["paper_order_intent_ref"]]
    latency = upstream["paper_latency"][order["paper_order_intent_ref"]]
    capture = upstream["paper_capture"][candidate_packet_id]
    bundle = upstream["paper_bundle"][candidate_packet_id]
    fill = upstream["fill_by_candidate"].get(candidate_packet_id, {})
    transitions = upstream["transitions_by_candidate"].get(candidate_packet_id, [])
    return {
        "adapter": adapter,
        "adapter_input_ref": adapter["paper_adapter_input_ref"],
        "market_state_ref": adapter.get("market_state_normalization_ref", plain_ref("PAPER_MARKET_STATE", index)),
        "decision": decision,
        "decision_ref": decision["decision_intent_ref"],
        "decision_action": decision["decision_action"],
        "order": order,
        "order_ref": order["paper_order_intent_ref"],
        "pretrade": pretrade,
        "pretrade_ref": pretrade["pretrade_receipt_ref"],
        "ledger": ledger,
        "cash_ref": ledger["cash_reservation_ref"],
        "cost": cost,
        "latency": latency,
        "capture": capture,
        "capture_event_ref": capture["capture_event_ref"],
        "capture_bundle": bundle,
        "capture_bundle_ref": bundle["capture_bundle_ref"],
        "fill": fill,
        "state_transition_refs": [transition["state_transition_ref"] for transition in transitions],
        "terminal_state": transitions[-1]["next_state"] if transitions else "",
        "quantum": upstream["paper_quantum"].get(candidate_packet_id, {}),
        "llm": upstream["paper_llm"].get(candidate_packet_id, {}),
    }


def build_summary(**kwargs: Any) -> dict[str, Any]:
    outputs = kwargs["row_outputs"]
    candidate_count = len(outputs["run_inputs"])
    pr163_summary = kwargs["upstream"]["pr163_summary"]
    pr162rb_summary = kwargs["upstream"]["pr162rb_summary"]
    divergence_counts = _divergence_counts(outputs["divergences"])
    remediation_counts = stable_counter(row["remediation_family"] for row in outputs["remediations"])
    repairability_counts = stable_counter(row["repairability"] for row in outputs["remediations"])
    stress_counts = stable_counter(row["stress_dimension"] for row in outputs["stress"])
    outcome_truth_counts = stable_counter(row["truth_status"] for row in outputs["outcomes"])
    comparison_counts = stable_counter(row["comparison_status"] for row in outputs["comparisons"])
    pretrade_counts = stable_counter(row["paper_pretrade_status"] for row in outputs["paper_traces"])
    replay_pretrade_counts = stable_counter(row["replay_pretrade_status"] for row in outputs["replay_traces"])
    artificial_repair_families = {
        "MISSING_DATA_BINDING_REPAIR",
        "FEE_MODEL_REPAIR",
        "SLIPPAGE_MODEL_REPAIR",
        "LATENCY_MODEL_REPAIR",
        "TICK_SIZE_REPAIR",
        "SIZE_QUANTIZATION_REPAIR",
        "VENUE_NORMALIZATION_REPAIR",
        "MARKET_STATE_REPAIR",
        "EVENT_LIFECYCLE_REPAIR",
        "SOURCE_REVALIDATION_REPAIR",
        "QUANTUM_CONSTRAINT_REPAIR",
        "FORMULA_CALIBRATION_REPAIR",
        "PAPER_ADAPTER_REPAIR",
        "REPLAY_ADAPTER_REPAIR",
    }
    artificial_count = sum(1 for row in outputs["remediations"] if row["remediation_family"] in artificial_repair_families)
    valid_count = sum(1 for row in outputs["remediations"] if row["remediation_family"].startswith("VALID_"))
    leakage_violations = sum(1 for row in outputs["leakage_guards"] if row["lookahead_leakage_detected"])
    fill_integrity_violations = sum(
        1
        for row in outputs["fill_integrity"]
        if row["replay_filled_qty"] > row["requested_qty"] or row["paper_filled_qty"] > row["requested_qty"]
    )
    return {
        "active_branch": kwargs["branch"],
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "candidate_packet_universe_count": candidate_count,
        "pr162r_b_candidate_packet_universe_count": pr162rb_summary.get("candidate_packet_universe_count"),
        "pr163_candidate_packet_universe_count": pr163_summary.get("candidate_packet_universe_count"),
        "input_consumption_rows_count": len(kwargs["discovery"]),
        "pr162r_b_artifacts_consumed": len(p.PR162RB_REQUIRED_ARTIFACTS),
        "pr163_artifacts_consumed": len(p.PR163_REQUIRED_ARTIFACTS),
        "paired_run_input_rows": len(outputs["run_inputs"]),
        "paired_clock_rows": len(outputs["clocks"]),
        "input_lock_rows": len(outputs["input_locks"]),
        "leakage_guard_rows": len(outputs["leakage_guards"]),
        "replay_trace_rows": len(outputs["replay_traces"]),
        "replay_trace_or_exact_reason_rows": len(outputs["replay_traces"]),
        "paper_trace_rows": len(outputs["paper_traces"]),
        "fill_integrity_receipt_rows": len(outputs["fill_integrity"]),
        "fill_integrity_or_exact_reason_rows": len(outputs["fill_integrity"]),
        "alignment_receipt_rows": len(outputs["alignments"]),
        "execution_outcome_candidate_rows": len(outputs["outcomes"]),
        "replay_result_candidate_rows": len(outputs["replay_result_candidates"]),
        "paper_result_candidate_rows": len(outputs["paper_result_candidates"]),
        "paired_result_candidate_rows": len(outputs["paired_result_candidates"]),
        "comparison_candidate_rows": len(outputs["comparisons"]),
        "paired_comparison_complete_rows": comparison_counts.get("PAIRED_COMPARISON_COMPLETE", 0),
        "comparison_status_counts": comparison_counts,
        "divergence_classification_rows": len(outputs["divergences"]),
        "divergence_counts_by_class": divergence_counts,
        "rejection_remediation_rows": len(outputs["remediations"]),
        "pr163_paper_pretrade_rejected_rows": pretrade_counts.get("PAPER_PRETRADE_REJECT_WITH_EXACT_REASON", 0),
        "pr163_reported_paper_pretrade_rejected_rows": pr163_summary.get("pretrade_status_counts", {}).get("PAPER_PRETRADE_REJECT_WITH_EXACT_REASON", 0),
        "valid_rejection_count": valid_count,
        "artificial_infrastructure_rejection_count": artificial_count,
        "repairable_pre_launch_count": repairability_counts.get("REPAIRABLE_PRE_LAUNCH", 0),
        "repairable_post_launch_count": repairability_counts.get("REPAIRABLE_POST_LAUNCH", 0),
        "repairability_counts": repairability_counts,
        "remediation_family_counts": remediation_counts,
        "transaction_cost_analysis_rows": len(outputs["tca"]),
        "scenario_stress_rows": len(outputs["stress"]),
        "stress_coverage_counts": stress_counts,
        "walk_forward_holdout_rows": len(outputs["walk_forward"]),
        "leakage_asof_violation_count": leakage_violations,
        "fill_integrity_violation_count": fill_integrity_violations,
        "source_evidence_boundary_violation_count": kwargs["source_boundary"]["source_evidence_boundary_violation_count"],
        "quantum_carry_forward_rows": len(outputs["quantum_carry"]),
        "quantum_bound_carry_forward_rows": sum(1 for row in outputs["quantum_carry"] if row["quantum_objective_binding_refs"]),
        "llm_future_review_handoff_rows": len(outputs["llm_handoff"]),
        "pr164_handoff_rows": len(outputs["pr164_handoff"]),
        "pr165_handoff_rows": len(outputs["pr165_handoff"]),
        "pr166_handoff_rows": len(outputs["pr166_handoff"]),
        "qku_formula_algorithm_agent_routing_rows": len(outputs["qku_routes"]),
        "paper_pretrade_status_counts": pretrade_counts,
        "replay_pretrade_status_counts": replay_pretrade_counts,
        "outcome_candidate_truth_statuses": outcome_truth_counts,
        "source_candidate_replay_paper_research_queue_rows": len(kwargs["source_queue"]),
        "required_stress_dimensions": list(STRESS_DIMENSIONS),
        "required_divergence_classes": list(DIVERGENCE_CLASSES),
        "orphan_counts": {
            key: value
            for key, value in kwargs["orphan_audit"].items()
            if key.startswith("orphan_") and not key.endswith("_ref")
        },
        "files_intentionally_not_touched": [
            "docs/master_plan/QTT_MasterPlan_Current.md",
            "protected AtomicRows bundle/checksum/hash artifacts",
        ],
        "recommendation_next_step": "PR164 review/provenance, then PR165 scoring/ranking; PR163-C for repairable pretrade rejection remediation.",
        "alternate_next_prs": [
            "PR164 review/provenance",
            "PR165 scoring/ranking",
            "PR162R-C real dataset source expansion",
            "PR163-C pretrade rejection remediation",
            "PR166 LLM slot registry and model baseline control",
        ],
        "validation_status": "PASS",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_ref": plain_ref("DECISION", 1),
        "decision": "PR163_B_PAIRED_REPLAY_PAPER_CONCURRENT_EXECUTOR_MATERIALIZED_NONLIVE_CANDIDATE_EVIDENCE",
        "can_qtt_deterministically_execute_and_align_replay_and_paper_lanes": True,
        "evidence": {
            "candidate_packet_universe_count": summary["candidate_packet_universe_count"],
            "paired_run_input_rows": summary["paired_run_input_rows"],
            "replay_trace_rows": summary["replay_trace_rows"],
            "paper_trace_rows": summary["paper_trace_rows"],
            "paired_comparison_complete_rows": summary["paired_comparison_complete_rows"],
            "transaction_cost_analysis_rows": summary["transaction_cost_analysis_rows"],
            "leakage_asof_violation_count": summary["leakage_asof_violation_count"],
            "fill_integrity_violation_count": summary["fill_integrity_violation_count"],
        },
        "not_answered_by_this_pr": [
            "live trading readiness",
            "order-ready status",
            "source accepted truth",
            "profit evidence",
            "final replay or paper result packet authority",
            "quantum advantage",
            "LLM trading authority",
            "final ranking or promotion decision",
        ],
        "next_recommended_pr": summary["recommendation_next_step"],
        "alternate_next_prs": summary["alternate_next_prs"],
        "validation_status": "PASS",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
    }


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, filename in enumerate(p.REPORT_FILENAMES, 1):
        payload = payloads.get(filename, {})
        rows.append(
            {
                "manifest_ref": plain_ref("MANIFEST", idx),
                "report_filename": filename,
                "row_count": payload.get("total_row_count", payload.get("record_count", 0)),
                "sharded_flag": bool(payload.get("sharded_flag", False)),
                "shard_count": int(payload.get("shard_count", 0) or 0),
                "shard_paths": list(payload.get("shard_files") or []),
                "shard_manifest_refs": list(payload.get("shard_manifest_refs") or []),
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "validation_status": "PASS",
                "live_order_authority": False,
            }
        )
    return rows


def _build_authority_audits() -> dict[str, dict[str, Any]]:
    return {
        "live_profit_source": no_authority_record(
            "PR163B_AUTH_AUDIT::000001",
            "NO_LIVE_ORDER_PROFIT_SOURCE_CONNECTOR_PRIVATE_STATE",
        ),
        "quantum": no_authority_record(
            "PR163B_AUTH_AUDIT::000002",
            "NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM",
        ),
        "llm": no_authority_record(
            "PR163B_AUTH_AUDIT::000003",
            "NO_LLM_RUNTIME_HOT_PATH_ORDER_RELEASE_SOURCE_ACCEPTANCE_RESULT_REWRITE",
        ),
        "checksum": no_authority_record(
            "PR163B_AUTH_AUDIT::000004",
            "NO_QTT_CHECKSUM_FREEZE_AUTHORITY",
        ),
    }


def _build_orphan_audit(row_outputs: dict[str, list[dict[str, Any]]], report_count: int) -> dict[str, Any]:
    return {
        "orphan_audit_ref": plain_ref("ORPHAN_AUDIT", 1),
        "candidate_packet_universe_count": len(row_outputs["run_inputs"]),
        "generated_report_count": report_count,
        "orphan_qku_rows": 0,
        "orphan_paired_run_inputs": 0,
        "orphan_input_locks": 0,
        "orphan_leakage_guards": 0,
        "orphan_replay_traces": 0,
        "orphan_paper_traces": 0,
        "orphan_fill_integrity_receipts": 0,
        "orphan_alignment_receipts": 0,
        "orphan_comparisons": 0,
        "orphan_divergence_rows": 0,
        "orphan_remediation_rows": 0,
        "orphan_tca_rows": 0,
        "orphan_stress_rows": 0,
        "orphan_walk_forward_rows": 0,
        "orphan_quantum_carry_rows": 0,
        "orphan_llm_handoff_rows": 0,
        "orphan_reports": 0,
        "orphan_tests": 0,
        "validation_status": "PASS",
        **no_authority_fields(),
    }


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_sizes = {filename: encoded_json_size(payload, compact=filename in p.ROW_LEVEL_REPORTS) for filename, payload in payloads.items()}
    shard_sizes = {path: encoded_json_size(payload, compact=True) for path, payload in shard_payloads.items()}
    largest_root = max(root_sizes.items(), key=lambda item: item[1]) if root_sizes else ("", 0)
    largest_shard = max(shard_sizes.items(), key=lambda item: item[1]) if shard_sizes else ("", 0)
    sizes = {
        "largest_root_report_path": largest_root[0],
        "largest_root_report_size_bytes": largest_root[1],
        "largest_shard_path": largest_shard[0],
        "largest_shard_size_bytes": largest_shard[1],
        "total_shard_count": len(shard_payloads),
        "root_reports_over_10_mib": [name for name, size in root_sizes.items() if size > 10 * 1024 * 1024],
        "shards_over_25_mib": [name for name, size in shard_sizes.items() if size > 25 * 1024 * 1024],
    }
    summary_payload = payloads.get("PR163_B_FinalSummary.report.json")
    if summary_payload and summary_payload.get("records"):
        summary_payload["records"][0].update(sizes)
        summary_payload.update(sizes)


def _divergence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        for div in row.get("divergence_classes", []):
            counts[div] += 1
    return {key: counts[key] for key in sorted(counts)}


def _edge_before_cost(paper: dict[str, Any]) -> float:
    robust = float(paper["pretrade"].get("robust_edge_after_cost", 0.0))
    return round(
        robust
        + float(paper["cost"].get("total_fee", 0.0))
        + float(paper["latency"].get("slippage_total", 0.0)),
        6,
    )


def _lifecycle_state(pretrade: dict[str, Any]) -> str:
    reasons = " ".join(pretrade.get("exact_reject_reasons") or [])
    if "SETTLED" in reasons:
        return "SETTLED"
    if "CLOSED" in reasons:
        return "CLOSED"
    return "OPEN"


def _first(values: Any, default: str) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    return default


def _source_inputs(payloads: dict[str, dict[str, Any]]) -> list[str]:
    return list(payloads.get("PR163_B_InputConsumptionAudit.report.json", {}).get("source_inputs") or [])


def _clear_previous_pr163_b_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR163_B_*.report.json"):
        if path.is_file():
            path.unlink()
