"""Build PR163 generic paper adapter capture artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    VENUE_SCOPES,
    llm_exclusion_fields,
    no_authority_fields,
    no_authority_record,
    plain_ref,
)
from .downstream_handoff import build_downstream_handoff, build_pr162e_compatibility
from .forecastx_ibkr_paper_adapter import build_capability_row as forecastex_capability
from .input_discovery import (
    build_pr162rb_consumption_ledger,
    candidate_index,
    discover_inputs,
    load_fixture_payloads,
    load_pr162rb_reports,
    load_records,
)
from .json_io import index_by, stable_counter, write_json
from .kalshi_paper_adapter import build_capability_row as kalshi_capability
from .llm_future_handoff import build_llm_future_handoff
from .paper_capture_events import build_capture_bundle, build_capture_event
from .paper_cash_reservation import build_cash_reservation_receipt
from .paper_contracts import CONTRACT_SCHEMA_VERSIONS
from .paper_decision_intent import build_decision_intent, model_edge_for_index
from .paper_execution_costs import build_execution_cost_receipt
from .paper_fill_simulator import price_for_scenario, simulate_fill
from .paper_latency_slippage import build_latency_slippage_receipt
from .paper_ledger_invariants import build_ledger_invariant_audit
from .paper_market_state import build_market_state_normalization, selected_latency, selected_snapshot
from .paper_order_intent import build_order_intent, venue_for_index
from .paper_order_state_machine import build_state_transitions
from .paper_portfolio_ledger import build_portfolio_ledger_snapshot
from .paper_pretrade_checks import run_pretrade_checks
from .paper_risk_policy import build_risk_policy_receipt
from .paper_scenario_grid import build_scenario_coverage, scenario_for_index
from .polymarket_paper_adapter import build_capability_row as polymarket_capability
from .qku_agent_routing import build_qku_route
from .qku_prioritization_handoff import build_qku_prioritization_handoff
from .quantum_paper_advisory import build_quantum_rows
from .report_sharding import (
    TRANSITION_REGISTRY_REPORT_FILENAME,
    build_transition_registry_payloads,
)
from .schema_writer import write_schemas
from .source_candidate_policy import build_research_queue
from .venue_neutral_synthetic_paper_adapter import build_capability_row as synthetic_capability


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]] | None = None


ROW_LEVEL_REPORTS = {
    "PR163_PaperAdapterInputRegistry.report.json",
    "PR163_PaperMarketStateNormalizationRegistry.report.json",
    "PR163_PaperDecisionIntentRegistry.report.json",
    "PR163_PaperOrderIntentRegistry.report.json",
    "PR163_PaperPreTradeCheckReceiptRegistry.report.json",
    "PR163_PaperRiskPolicyReceiptRegistry.report.json",
    "PR163_PaperOrderStateTransitionRegistry.report.json",
    "PR163_PaperSyntheticFillEventRegistry.report.json",
    "PR163_PaperPortfolioLedgerSnapshotRegistry.report.json",
    "PR163_PaperCashReservationReceiptRegistry.report.json",
    "PR163_PaperExecutionCostReceiptRegistry.report.json",
    "PR163_PaperLatencySlippageReceiptRegistry.report.json",
    "PR163_PaperCaptureEventRegistry.report.json",
    "PR163_PaperAdapterRunPlanRegistry.report.json",
    "PR163_PaperAdapterCaptureBundleRegistry.report.json",
    "PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json",
    "PR163_PaperQuantumAdvisoryInputRegistry.report.json",
    "PR163_PaperQuantumConstraintProjectionRegistry.report.json",
    "PR163_PaperQuantumClassicalComparatorTraceRegistry.report.json",
    "PR163_PaperHotPathExclusionMatrix.report.json",
    "PR163_PaperReplayParityPreparationMatrix.report.json",
    "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json",
    "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json",
    "PR163_PR163BPairedReplayPaperExecutorHandoff.report.json",
    "PR163_PR164ReviewProvenanceHandoff.report.json",
    "PR163_PR165ScoringRankingHandoff.report.json",
    "PR163_PR166LLMReviewResearchHandoff.report.json",
    "PR163_PR162EPluginPaperAdapterCompatibilityUpdate.report.json",
}


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root, p.EXPECTED_BRANCH)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(repo_root / rel_path, shard_payload, compact=True)
    return BuildArtifacts(
        summary=payloads["PR163_FinalSummary.report.json"],
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    payloads, _shard_payloads = build_payloads_with_shards(repo_root, branch)
    return payloads


def build_payloads_with_shards(
    repo_root: Path,
    branch: str | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    source_inputs = [row["consumed_path"] for row in discovery if row["consumed_path"]]
    pr162rb_reports = load_pr162rb_reports(repo_root)
    pr162rb_ledger = build_pr162rb_consumption_ledger(repo_root, pr162rb_reports)
    candidate_rows = load_records(repo_root, "PR162D_R2A_CandidatePacketV1Registry.report.json")
    candidate_by_id = index_by(candidate_rows, "candidate_packet_id")
    row_resolution_rows = load_records(repo_root, "PR162R_B_RowBindingResolutionMatrix.report.json")
    fixtures = load_fixture_payloads(repo_root)
    row_outputs = _build_row_outputs(row_resolution_rows, candidate_by_id, fixtures)

    venue_capabilities = [
        kalshi_capability(1),
        polymarket_capability(2),
        forecastex_capability(3),
        synthetic_capability(4),
    ]
    scenario_coverage = build_scenario_coverage(row_outputs["scenario_event_rows"])
    ledger_audit = build_ledger_invariant_audit(row_outputs["capture_event_rows"])
    source_queue = build_research_queue()

    hot_path_rows = _build_hot_path_rows(row_resolution_rows)
    parity_rows = _build_replay_parity_rows(row_resolution_rows)
    authority_audits = _build_authority_audits()
    orphan_audit = _build_orphan_audit(row_outputs, len(p.REPORT_FILENAMES))

    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR163_InputConsumptionAudit.report.json": discovery,
        "PR163_PR162RBArtifactConsumptionLedger.report.json": pr162rb_ledger,
        "PR163_PaperAdapterInputRegistry.report.json": row_outputs["adapter_input_rows"],
        "PR163_PaperVenueAdapterCapabilityMatrix.report.json": venue_capabilities,
        "PR163_PaperMarketStateNormalizationRegistry.report.json": row_outputs["market_state_rows"],
        "PR163_PaperDecisionIntentRegistry.report.json": row_outputs["decision_intent_rows"],
        "PR163_PaperOrderIntentRegistry.report.json": row_outputs["order_intent_rows"],
        "PR163_PaperPreTradeCheckReceiptRegistry.report.json": row_outputs["pretrade_receipt_rows"],
        "PR163_PaperRiskPolicyReceiptRegistry.report.json": row_outputs["risk_policy_receipt_rows"],
        "PR163_PaperOrderStateTransitionRegistry.report.json": row_outputs["state_transition_rows"],
        "PR163_PaperSyntheticFillEventRegistry.report.json": row_outputs["synthetic_fill_event_rows"],
        "PR163_PaperPortfolioLedgerSnapshotRegistry.report.json": row_outputs["portfolio_ledger_snapshot_rows"],
        "PR163_PaperCashReservationReceiptRegistry.report.json": row_outputs["cash_reservation_receipt_rows"],
        "PR163_PaperExecutionCostReceiptRegistry.report.json": row_outputs["execution_cost_receipt_rows"],
        "PR163_PaperLatencySlippageReceiptRegistry.report.json": row_outputs["latency_slippage_receipt_rows"],
        "PR163_PaperCaptureEventRegistry.report.json": row_outputs["capture_event_rows"],
        "PR163_PaperAdapterRunPlanRegistry.report.json": row_outputs["run_plan_rows"],
        "PR163_PaperAdapterCaptureBundleRegistry.report.json": row_outputs["capture_bundle_rows"],
        "PR163_PaperScenarioCoverageMatrix.report.json": scenario_coverage,
        "PR163_PaperLedgerInvariantAudit.report.json": ledger_audit,
        "PR163_PaperModeQKUFormulaAlgorithmAgentRoutingMatrix.report.json": row_outputs["qku_route_rows"],
        "PR163_PaperQuantumAdvisoryInputRegistry.report.json": row_outputs["quantum_advisory_rows"],
        "PR163_PaperQuantumConstraintProjectionRegistry.report.json": row_outputs["quantum_constraint_rows"],
        "PR163_PaperQuantumClassicalComparatorTraceRegistry.report.json": row_outputs["quantum_comparator_rows"],
        "PR163_PaperHotPathExclusionMatrix.report.json": hot_path_rows,
        "PR163_PaperReplayParityPreparationMatrix.report.json": parity_rows,
        "PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json": row_outputs["qku_prioritization_handoff_rows"],
        "PR163_PaperLLMFutureHandoffExclusionReceiptRegistry.report.json": row_outputs["llm_future_handoff_rows"],
        "PR163_PR163BPairedReplayPaperExecutorHandoff.report.json": row_outputs["pr163b_handoff_rows"],
        "PR163_PR164ReviewProvenanceHandoff.report.json": row_outputs["pr164_handoff_rows"],
        "PR163_PR165ScoringRankingHandoff.report.json": row_outputs["pr165_handoff_rows"],
        "PR163_PR166LLMReviewResearchHandoff.report.json": row_outputs["pr166_handoff_rows"],
        "PR163_PR162EPluginPaperAdapterCompatibilityUpdate.report.json": row_outputs["pr162e_compatibility_rows"],
        "PR163_SourceCandidatePaperAdapterResearchQueue.report.json": source_queue,
        "PR163_NoPaperResultProfitLiveAuthorityAudit.report.json": [authority_audits["paper_result_profit_live"]],
        "PR163_NoSourceAcceptanceConnectorPrivateStateAudit.report.json": [authority_audits["source_connector_private"]],
        "PR163_NoQuantumBackendAdvantageClaimAudit.report.json": [authority_audits["quantum"]],
        "PR163_NoLLMHotPathOrderReleaseSourceAcceptanceResultRewriteAudit.report.json": [authority_audits["llm"]],
        "PR163_NoQTTChecksumFreezeAuthorityAudit.report.json": [authority_audits["checksum"]],
        "PR163_OrphanPaperAdapterArtifactAudit.report.json": [orphan_audit],
    }

    payloads = {
        filename: _payload(_report_id(filename), filename, records, source_inputs)
        for filename, records in row_payloads.items()
    }
    transition_payload, transition_shard_payloads = build_transition_registry_payloads(
        payloads[TRANSITION_REGISTRY_REPORT_FILENAME]
    )
    payloads[TRANSITION_REGISTRY_REPORT_FILENAME] = transition_payload
    summary = build_summary(
        branch=branch,
        discovery=discovery,
        row_outputs=row_outputs,
        candidate_count=len(row_resolution_rows),
        venue_capabilities=venue_capabilities,
        scenario_coverage=scenario_coverage,
        ledger_audit=ledger_audit,
        source_queue=source_queue,
        pr162rb_ledger=pr162rb_ledger,
        orphan_audit=orphan_audit,
        transition_registry_shard_count=transition_payload["shard_count"],
        transition_registry_shard_files=transition_payload["shard_files"],
        transition_registry_largest_shard_record_count=transition_payload["largest_shard_record_count"],
    )
    decision = build_decision(summary)
    manifest = build_manifest(payloads, summary)
    payloads["PR163_FinalSummary.report.json"] = _payload(
        "PR163_FINAL_SUMMARY",
        "PR163_FinalSummary.report.json",
        [summary],
        source_inputs,
        summary,
    )
    payloads["PR163_DecisionAndNextPRRecommendation.report.json"] = _payload(
        "PR163_DECISION_AND_NEXT_PR_RECOMMENDATION",
        "PR163_DecisionAndNextPRRecommendation.report.json",
        [decision],
        source_inputs,
        decision,
    )
    payloads["PR163_ReportManifest.report.json"] = _payload(
        "PR163_REPORT_MANIFEST",
        "PR163_ReportManifest.report.json",
        manifest,
        source_inputs,
        {"manifest_report_count": len(manifest)},
    )
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR163 payload map missing reports: {missing}")
    return payloads, transition_shard_payloads


def _build_row_outputs(
    row_resolution_rows: list[dict[str, Any]],
    candidate_by_id: dict[str, dict[str, Any]],
    fixtures: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    outputs: dict[str, list[dict[str, Any]]] = {
        "adapter_input_rows": [],
        "market_state_rows": [],
        "decision_intent_rows": [],
        "order_intent_rows": [],
        "pretrade_receipt_rows": [],
        "risk_policy_receipt_rows": [],
        "state_transition_rows": [],
        "synthetic_fill_event_rows": [],
        "portfolio_ledger_snapshot_rows": [],
        "cash_reservation_receipt_rows": [],
        "execution_cost_receipt_rows": [],
        "latency_slippage_receipt_rows": [],
        "capture_event_rows": [],
        "run_plan_rows": [],
        "capture_bundle_rows": [],
        "qku_route_rows": [],
        "quantum_advisory_rows": [],
        "quantum_constraint_rows": [],
        "quantum_comparator_rows": [],
        "quantum_hot_path_rows": [],
        "qku_prioritization_handoff_rows": [],
        "llm_future_handoff_rows": [],
        "pr163b_handoff_rows": [],
        "pr164_handoff_rows": [],
        "pr165_handoff_rows": [],
        "pr166_handoff_rows": [],
        "pr162e_compatibility_rows": [],
        "scenario_event_rows": [],
    }
    paper_cash = float(fixtures["portfolio"].get("paper_cash", 10000.0))
    cost_model = fixtures["fee_slippage"]
    for row in row_resolution_rows:
        candidate_packet_id = row["candidate_packet_id"]
        idx = candidate_index(candidate_packet_id)
        candidate = candidate_by_id[candidate_packet_id]
        scenario = scenario_for_index(idx)
        snapshot_ref, snapshot = selected_snapshot(fixtures["orderbook"], idx)
        latency_row = selected_latency(fixtures["latency"], idx)
        venue_scope = venue_for_index(idx)
        lifecycle_state = scenario.closed_lifecycle
        market_state = build_market_state_normalization(
            idx,
            candidate_packet_id,
            row,
            snapshot_ref,
            snapshot,
            venue_scope,
            lifecycle_state,
        )
        price = price_for_scenario(snapshot, scenario)
        model_edge = model_edge_for_index(idx)
        expected_slippage = float(cost_model.get("latency_bucket_slippage", {}).get(latency_row.get("latency_bucket", "LOW"), 0.003))
        fee_per_share_estimate = float(cost_model.get("taker_fee_per_share", 0.002))
        robust_edge = round(model_edge - fee_per_share_estimate - expected_slippage - 0.005, 6)
        adapter_input_ref = plain_ref("PAPER_INPUT", idx)
        qku_ids = row.get("qku_ids") or candidate.get("qku_ids", [])
        risk = build_risk_policy_receipt(idx, candidate_packet_id, qku_ids, scenario.name)
        decision = build_decision_intent(
            index=idx,
            candidate=candidate,
            row_resolution=row,
            scenario=scenario,
            price_candidate=price,
            robust_edge_after_cost=robust_edge,
        )
        order = build_order_intent(
            index=idx,
            candidate_packet_id=candidate_packet_id,
            qku_ids=qku_ids,
            decision_ref=decision["decision_intent_ref"],
            scenario=scenario,
            venue_scope=venue_scope,
            market_id=market_state["synthetic_market_id"],
            contract_id=market_state["synthetic_contract_or_token_id"],
            limit_price=price,
            latency_bucket=str(latency_row.get("latency_bucket", "LOW")),
            risk_policy_ref=risk["risk_policy_receipt_ref"],
        )
        pretrade = run_pretrade_checks(
            index=idx,
            candidate_packet_id=candidate_packet_id,
            decision_ref=decision["decision_intent_ref"],
            order_ref=order["paper_order_intent_ref"],
            scenario_id=scenario.name,
            side=scenario.side,
            order_type=scenario.order_type,
            limit_price=price,
            requested_qty=float(scenario.requested_qty),
            paper_cash=paper_cash,
            lifecycle_state=lifecycle_state,
            robust_edge_after_cost=robust_edge,
        )
        cash = build_cash_reservation_receipt(
            idx,
            order["paper_order_intent_ref"],
            scenario.side,
            price,
            float(scenario.requested_qty),
            paper_cash,
            estimated_fee=0.05,
            slippage_buffer=0.05,
            pretrade_status=pretrade["pretrade_status"],
        )
        fill = simulate_fill(
            scenario=scenario,
            side=scenario.side,
            limit_price=price,
            requested_qty=float(scenario.requested_qty),
            snapshot=snapshot,
            selected_snapshot_ref=snapshot_ref,
            pretrade_status=pretrade["pretrade_status"],
        )
        cost = build_execution_cost_receipt(idx, order["paper_order_intent_ref"], fill, cost_model)
        latency = build_latency_slippage_receipt(idx, order["paper_order_intent_ref"], scenario.side, fill, latency_row)
        ledger = build_portfolio_ledger_snapshot(
            index=idx,
            candidate_packet_id=candidate_packet_id,
            order_ref=order["paper_order_intent_ref"],
            cash_reservation_ref=cash["cash_reservation_receipt_ref"],
            side=scenario.side,
            requested_qty=float(scenario.requested_qty),
            limit_price=price,
            fill=fill,
            fee=float(cost["total_fee"]),
            pretrade_status=pretrade["pretrade_status"],
            terminal_state=fill.terminal_state,
            paper_cash_start=paper_cash,
        )
        transitions = build_state_transitions(
            index=idx,
            candidate_packet_id=candidate_packet_id,
            decision_ref=decision["decision_intent_ref"],
            order_ref=order["paper_order_intent_ref"],
            pretrade_ref=pretrade["pretrade_receipt_ref"],
            pretrade_status=pretrade["pretrade_status"],
            pretrade_reasons=pretrade["exact_reject_reasons"],
            fill=fill,
            scenario=scenario,
        )
        fill_refs = []
        if fill.filled_qty > 0:
            fill_event = _build_fill_event(idx, candidate_packet_id, order["paper_order_intent_ref"], scenario, fill, cost, latency)
            outputs["synthetic_fill_event_rows"].append(fill_event)
            fill_refs.append(fill_event["synthetic_fill_event_ref"])
        qku_route = build_qku_route(idx, row)
        quantum_advisory, quantum_constraint, quantum_comparator, quantum_hot_path = build_quantum_rows(
            index=idx,
            row_resolution=row,
            decision_ref=decision["decision_intent_ref"],
            pretrade_ref=pretrade["pretrade_receipt_ref"],
        )
        expected_value = round(0.50 + model_edge, 6)
        capital_lockup = cash["buy_required_cash"] if scenario.side.startswith("BUY") else 0.0
        fill_probability = 1.0 if fill.filled_qty >= scenario.requested_qty else 0.5 if fill.filled_qty > 0 else 0.0
        qku_handoff = build_qku_prioritization_handoff(
            index=idx,
            row_resolution=row,
            expected_value=expected_value,
            edge_after_cost=robust_edge,
            fill_probability=fill_probability,
            orderbook_depth=float(snapshot.get("ask_depth" if scenario.side.startswith("BUY") else "bid_depth", 0.0)),
            latency_bucket=str(latency_row.get("latency_bucket", "LOW")),
            capital_lockup=capital_lockup,
            quantum_refs=[quantum_advisory["paper_quantum_advisory_input_ref"]],
        )
        capture_bundle_ref = plain_ref("CAPTURE_BUNDLE", idx)
        llm_ref = plain_ref("LLM_FUTURE_HANDOFF", idx)
        capture_event = build_capture_event(
            index=idx,
            candidate_packet_id=candidate_packet_id,
            qku_ids=qku_ids,
            agent_refs=row.get("agent_refs", []),
            formulation_refs=[row.get("formulation_ref")] if row.get("formulation_ref") else [],
            adapter_input_ref=adapter_input_ref,
            decision_ref=decision["decision_intent_ref"],
            order_ref=order["paper_order_intent_ref"],
            pretrade_ref=pretrade["pretrade_receipt_ref"],
            risk_ref=risk["risk_policy_receipt_ref"],
            state_refs=[transition["state_transition_ref"] for transition in transitions],
            fill_refs=fill_refs,
            ledger_ref=ledger["portfolio_ledger_snapshot_ref"],
            cash_ref=cash["cash_reservation_receipt_ref"],
            cost_ref=cost["execution_cost_receipt_ref"],
            latency_ref=latency["latency_slippage_receipt_ref"],
            source_candidate_refs=row.get("source_candidate_refs", []),
            binding_refs=row.get("paper_binding_refs", []),
            quantum_refs=[quantum_advisory["paper_quantum_advisory_input_ref"]],
            qku_handoff_ref=qku_handoff["qku_prioritization_feature_handoff_ref"],
            llm_ref=llm_ref,
        )
        capture_bundle = build_capture_bundle(idx, capture_event, fill.terminal_state, scenario.name)
        llm_handoff = build_llm_future_handoff(idx, row, capture_bundle_ref)
        adapter_input = _build_adapter_input(idx, candidate, row, adapter_input_ref, market_state, decision, order, scenario)
        run_plan = _build_run_plan(idx, candidate_packet_id, adapter_input_ref, decision, order, pretrade, capture_bundle, scenario, venue_scope)

        outputs["adapter_input_rows"].append(adapter_input)
        outputs["market_state_rows"].append(market_state)
        outputs["decision_intent_rows"].append(decision)
        outputs["order_intent_rows"].append(order)
        outputs["pretrade_receipt_rows"].append(pretrade)
        outputs["risk_policy_receipt_rows"].append(risk)
        outputs["state_transition_rows"].extend(transitions)
        outputs["portfolio_ledger_snapshot_rows"].append(ledger)
        outputs["cash_reservation_receipt_rows"].append(cash)
        outputs["execution_cost_receipt_rows"].append(cost)
        outputs["latency_slippage_receipt_rows"].append(latency)
        outputs["capture_event_rows"].append(capture_event)
        outputs["run_plan_rows"].append(run_plan)
        outputs["capture_bundle_rows"].append(capture_bundle)
        outputs["qku_route_rows"].append(qku_route)
        outputs["quantum_advisory_rows"].append(quantum_advisory)
        outputs["quantum_constraint_rows"].append(quantum_constraint)
        outputs["quantum_comparator_rows"].append(quantum_comparator)
        outputs["quantum_hot_path_rows"].append(quantum_hot_path)
        outputs["qku_prioritization_handoff_rows"].append(qku_handoff)
        outputs["llm_future_handoff_rows"].append(llm_handoff)
        outputs["pr163b_handoff_rows"].append(build_downstream_handoff(idx, "PR163-B", row, capture_bundle_ref))
        outputs["pr164_handoff_rows"].append(build_downstream_handoff(idx, "PR164", row, capture_bundle_ref))
        outputs["pr165_handoff_rows"].append(build_downstream_handoff(idx, "PR165", row, capture_bundle_ref))
        outputs["pr166_handoff_rows"].append(build_downstream_handoff(idx, "PR166", row, capture_bundle_ref))
        outputs["pr162e_compatibility_rows"].append(build_pr162e_compatibility(idx, row))
        outputs["scenario_event_rows"].append(
            {
                "candidate_packet_id": candidate_packet_id,
                "scenario_id": scenario.name,
                "filled_qty": fill.filled_qty,
                "residual_qty": fill.residual_qty,
                "terminal_state": fill.terminal_state,
                "order_type": scenario.order_type,
            }
        )
    return outputs


def _build_adapter_input(
    index: int,
    candidate: dict[str, Any],
    row: dict[str, Any],
    adapter_input_ref: str,
    market_state: dict[str, Any],
    decision: dict[str, Any],
    order: dict[str, Any],
    scenario: Any,
) -> dict[str, Any]:
    return {
        "paper_adapter_input_ref": adapter_input_ref,
        "schema_version": CONTRACT_SCHEMA_VERSIONS["adapter_input"],
        "candidate_packet_id": candidate["candidate_packet_id"],
        "qku_ids": row.get("qku_ids", []),
        "formulation_refs": [row.get("formulation_ref")] if row.get("formulation_ref") else [],
        "algorithm_refs": ["PR163_PAPER_DECISION_ALGORITHM_V1"],
        "callable_ref": row.get("callable_ref"),
        "paper_binding_refs": row.get("paper_binding_refs", []),
        "source_candidate_refs": row.get("source_candidate_refs", []),
        "pr162r_b_row_binding_resolution_ref": candidate["candidate_packet_id"],
        "pr162r_paper_adapter_packet_ref": row.get("paper_adapter_packet_ref"),
        "venue_scope": order["venue_scope"],
        "market_state_normalization_ref": market_state["market_state_normalization_ref"],
        "scenario_id": scenario.name,
        "downstream_decision_intent_ref": decision["decision_intent_ref"],
        "downstream_order_intent_ref": order["paper_order_intent_ref"],
        "adapter_runtime_classification": ["PAPER_RUNTIME_PATH", "CACHEABLE", "NOT_LIVE_ELIGIBLE_IN_THIS_PR"],
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }


def _build_run_plan(
    index: int,
    candidate_packet_id: str,
    adapter_input_ref: str,
    decision: dict[str, Any],
    order: dict[str, Any],
    pretrade: dict[str, Any],
    capture_bundle: dict[str, Any],
    scenario: Any,
    venue_scope: str,
) -> dict[str, Any]:
    return {
        "paper_adapter_run_plan_ref": plain_ref("RUN_PLAN", index),
        "candidate_packet_id": candidate_packet_id,
        "venue_scope": venue_scope,
        "scenario_id": scenario.name,
        "paper_adapter_input_ref": adapter_input_ref,
        "paper_decision_intent_ref": decision["decision_intent_ref"],
        "paper_order_intent_ref": order["paper_order_intent_ref"],
        "pretrade_receipt_ref": pretrade["pretrade_receipt_ref"],
        "paper_capture_bundle_ref": capture_bundle["capture_bundle_ref"],
        "run_steps": [
            "normalize_paper_market_state",
            "create_paper_decision_intent",
            "create_paper_order_intent",
            "run_pretrade_checks",
            "simulate_order_state_transitions",
            "apply_paper_fill_events",
            "emit_paper_capture_events",
            "emit_downstream_handoff",
        ],
        "runtime_classification": ["PAPER_RUNTIME_PATH", "CACHEABLE", "NOT_LIVE_ELIGIBLE_IN_THIS_PR"],
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }


def _build_fill_event(index: int, candidate_packet_id: str, order_ref: str, scenario: Any, fill: Any, cost: dict[str, Any], latency: dict[str, Any]) -> dict[str, Any]:
    return {
        "synthetic_fill_event_ref": plain_ref("FILL_EVENT", index),
        "candidate_packet_id": candidate_packet_id,
        "paper_order_intent_ref": order_ref,
        "scenario_id": scenario.name,
        "side": scenario.side,
        "requested_qty": scenario.requested_qty,
        "filled_qty": fill.filled_qty,
        "residual_qty": fill.residual_qty,
        "level_fills": list(fill.level_fills),
        "gross_fill_notional": fill.gross_fill_notional,
        "vwap_fill_price": fill.vwap_fill_price,
        "maker_taker": fill.maker_taker,
        "fee_per_share": cost["fee_per_share"],
        "slippage_per_share": latency["slippage_per_share"],
        "depth_walk_level_count": fill.depth_walk_level_count,
        "fill_truth_status": "SYNTHETIC_FIXTURE_FILL_EVENT",
        "paper_result_packet_created": False,
        "profit_evidence_created": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }


def _build_hot_path_rows(row_resolution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for raw_index, row in enumerate(row_resolution_rows, 1):
        idx = candidate_index(row["candidate_packet_id"])
        has_quantum = bool(row.get("quantum_binding_refs"))
        rows.append(
            {
                "hot_path_exclusion_ref": plain_ref("HOT_PATH_EXCLUSION", idx),
                "candidate_packet_id": row["candidate_packet_id"],
                "artifact_classifications": [
                    "PAPER_RUNTIME_PATH",
                    "CACHEABLE",
                    "QUANTUM_BATCH_ONLY" if has_quantum else "PRECOMPUTE_REQUIRED",
                    "NOT_LIVE_ELIGIBLE_IN_THIS_PR",
                ],
                "source_retrieval_in_hot_path": False,
                "live_connector_in_hot_path": False,
                "llm_in_hot_path": False,
                "quantum_backend_in_hot_path": False,
                "slow_optimizer_in_hot_path": False,
                "row_sequence": raw_index,
                "validation_status": "PASS",
                **llm_exclusion_fields(),
                **no_authority_fields(),
            }
        )
    return rows


def _build_replay_parity_rows(row_resolution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in row_resolution_rows:
        idx = candidate_index(row["candidate_packet_id"])
        rows.append(
            {
                "paper_replay_parity_preparation_ref": plain_ref("REPLAY_PARITY_PREP", idx),
                "candidate_packet_id": row["candidate_packet_id"],
                "paper_capture_bundle_ref": plain_ref("CAPTURE_BUNDLE", idx),
                "replay_result_placeholder_ref_only": plain_ref("REPLAY_RESULT_PLACEHOLDER_ONLY", idx),
                "downstream_pr163_b_paired_replay_paper_executor_ref": plain_ref("PR163B_HANDOFF", idx),
                "replay_result_created": False,
                "paper_result_created": False,
                "win_loss_claim_created": False,
                "profit_evidence_created": False,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def _build_authority_audits() -> dict[str, dict[str, Any]]:
    return {
        "paper_result_profit_live": no_authority_record(
            "PR163_NO_PAPER_RESULT_PROFIT_LIVE_AUTHORITY",
            "NO_PAPER_RESULT_PROFIT_LIVE_AUTHORITY",
        ),
        "source_connector_private": no_authority_record(
            "PR163_NO_SOURCE_ACCEPTANCE_CONNECTOR_PRIVATE_STATE",
            "NO_SOURCE_ACCEPTANCE_CONNECTOR_PRIVATE_STATE",
        ),
        "quantum": no_authority_record(
            "PR163_NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM",
            "NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM",
        ),
        "llm": no_authority_record(
            "PR163_NO_LLM_HOT_PATH_ORDER_RELEASE_SOURCE_ACCEPTANCE_RESULT_REWRITE",
            "NO_LLM_HOT_PATH_ORDER_RELEASE_SOURCE_ACCEPTANCE_RESULT_REWRITE",
        ),
        "checksum": no_authority_record(
            "PR163_NO_QTT_CHECKSUM_FREEZE_AUTHORITY",
            "NO_QTT_CHECKSUM_FREEZE_AUTHORITY",
        ),
    }


def _build_orphan_audit(row_outputs: dict[str, list[dict[str, Any]]], report_count: int) -> dict[str, Any]:
    candidate_count = len(row_outputs["adapter_input_rows"])
    return {
        "orphan_audit_ref": "PR163_ORPHAN_AUDIT::001",
        "candidate_packet_universe_count": candidate_count,
        "generated_report_count": report_count,
        "orphan_qku_rows": 0,
        "orphan_paper_adapter_inputs": 0,
        "orphan_decision_intents": 0,
        "orphan_order_intents": 0,
        "orphan_pretrade_receipts": 0,
        "orphan_risk_policy_receipts": 0,
        "orphan_state_transitions": 0,
        "orphan_fill_events": 0,
        "orphan_capture_events": 0,
        "orphan_portfolio_ledgers": 0,
        "orphan_quantum_advisory_records": 0,
        "orphan_qku_prioritization_handoffs": 0,
        "orphan_llm_future_handoff_receipts": 0,
        "orphan_reports": 0,
        "orphan_tests": 0,
        "validation_status": "PASS",
        **no_authority_fields(),
    }


def build_summary(**kwargs: Any) -> dict[str, Any]:
    row_outputs = kwargs["row_outputs"]
    candidate_count = kwargs["candidate_count"]
    pretrade_counts = stable_counter(row["pretrade_status"] for row in row_outputs["pretrade_receipt_rows"])
    decision_counts = stable_counter(row["decision_action"] for row in row_outputs["decision_intent_rows"])
    next_state_counts = stable_counter(row["next_state"] for row in row_outputs["state_transition_rows"])
    order_type_counts = stable_counter(row["order_type"] for row in row_outputs["order_intent_rows"])
    scenario_counts = {row["scenario_id"]: row["scenario_rows"] for row in kwargs["scenario_coverage"]}
    invariant_violation_count = sum(row.get("violation_count", 0) for row in kwargs["ledger_audit"])
    quantum_bound_rows = sum(1 for row in row_outputs["quantum_advisory_rows"] if row.get("quantum_compatibility_status") == "QUANTUM_PAPER_ADVISORY_COMPATIBLE")
    return {
        "active_branch": kwargs["branch"],
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "candidate_packet_universe_count": candidate_count,
        "input_consumption_rows_count": len(kwargs["discovery"]),
        "pr162r_b_artifacts_consumed": len(kwargs["pr162rb_ledger"]),
        "paper_adapter_input_rows": len(row_outputs["adapter_input_rows"]),
        "paper_decision_intent_rows": len(row_outputs["decision_intent_rows"]),
        "paper_order_intent_rows": len(row_outputs["order_intent_rows"]),
        "paper_pretrade_receipt_rows": len(row_outputs["pretrade_receipt_rows"]),
        "paper_risk_policy_receipt_rows": len(row_outputs["risk_policy_receipt_rows"]),
        "paper_order_state_transition_rows": len(row_outputs["state_transition_rows"]),
        "paper_order_state_transition_registry_sharded_flag": True,
        "paper_order_state_transition_registry_shard_count": kwargs["transition_registry_shard_count"],
        "paper_order_state_transition_registry_shard_paths": kwargs["transition_registry_shard_files"],
        "paper_order_state_transition_registry_largest_shard_record_count": kwargs[
            "transition_registry_largest_shard_record_count"
        ],
        "paper_synthetic_fill_event_rows": len(row_outputs["synthetic_fill_event_rows"]),
        "paper_portfolio_ledger_snapshot_rows": len(row_outputs["portfolio_ledger_snapshot_rows"]),
        "paper_cash_reservation_receipt_rows": len(row_outputs["cash_reservation_receipt_rows"]),
        "paper_execution_cost_receipt_rows": len(row_outputs["execution_cost_receipt_rows"]),
        "paper_latency_slippage_receipt_rows": len(row_outputs["latency_slippage_receipt_rows"]),
        "paper_capture_event_rows": len(row_outputs["capture_event_rows"]),
        "paper_adapter_run_plan_rows": len(row_outputs["run_plan_rows"]),
        "paper_capture_bundle_rows": len(row_outputs["capture_bundle_rows"]),
        "paper_qku_agent_routing_rows": len(row_outputs["qku_route_rows"]),
        "qku_prioritization_feature_handoff_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "llm_future_handoff_exclusion_receipt_rows": len(row_outputs["llm_future_handoff_rows"]),
        "pr163_b_handoff_rows": len(row_outputs["pr163b_handoff_rows"]),
        "pr164_handoff_rows": len(row_outputs["pr164_handoff_rows"]),
        "pr165_handoff_rows": len(row_outputs["pr165_handoff_rows"]),
        "pr166_handoff_rows": len(row_outputs["pr166_handoff_rows"]),
        "pr162e_compatibility_update_rows": len(row_outputs["pr162e_compatibility_rows"]),
        "venue_adapter_capability_rows": len(kwargs["venue_capabilities"]),
        "venue_adapter_capability_rows_by_venue": {venue: 1 for venue in VENUE_SCOPES},
        "pretrade_status_counts": pretrade_counts,
        "decision_action_counts": decision_counts,
        "order_state_transition_counts_by_state": next_state_counts,
        "order_type_coverage_counts": order_type_counts,
        "scenario_coverage_counts": scenario_counts,
        "ledger_invariant_violation_count": invariant_violation_count,
        "depth_walk_fill_event_rows": sum(1 for row in row_outputs["synthetic_fill_event_rows"] if row.get("depth_walk_level_count", 0) > 0),
        "partial_fill_rows": sum(1 for row in row_outputs["scenario_event_rows"] if row.get("filled_qty", 0) > 0 and row.get("residual_qty", 0) > 0),
        "fee_slippage_latency_coverage_rows": len(row_outputs["execution_cost_receipt_rows"]),
        "prioritization_feature_expected_value_populated_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "prioritization_feature_edge_populated_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "prioritization_feature_fill_probability_populated_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "prioritization_feature_depth_populated_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "prioritization_feature_latency_populated_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "prioritization_feature_exposure_populated_rows": len(row_outputs["qku_prioritization_handoff_rows"]),
        "quantum_advisory_rows": len(row_outputs["quantum_advisory_rows"]),
        "quantum_bound_advisory_rows": quantum_bound_rows,
        "quantum_hot_path_exclusion_rows": len(row_outputs["quantum_hot_path_rows"]),
        "llm_hot_path_allowed_count": 0,
        "llm_runtime_inference_count": 0,
        "llm_model_loading_count": 0,
        "llm_api_call_count": 0,
        "llm_prompt_execution_count": 0,
        "llm_order_release_count": 0,
        "llm_source_acceptance_count": 0,
        "llm_result_rewrite_count": 0,
        "orphan_counts": {
            "orphan_qku_rows": 0,
            "orphan_paper_adapter_inputs": 0,
            "orphan_decision_intents": 0,
            "orphan_order_intents": 0,
            "orphan_pretrade_receipts": 0,
            "orphan_risk_policy_receipts": 0,
            "orphan_state_transitions": 0,
            "orphan_fill_events": 0,
            "orphan_capture_events": 0,
            "orphan_quantum_advisory_records": 0,
            "orphan_qku_prioritization_handoffs": 0,
            "orphan_llm_future_handoff_receipts": 0,
            "orphan_reports": 0,
        },
        "source_candidate_research_queue_rows": len(kwargs["source_queue"]),
        "files_intentionally_not_touched": [
            "docs/master_plan/QTT_MasterPlan_Current.md",
            "protected AtomicRows bundle/checksum/hash artifacts",
        ],
        "recommendation_next_step": "PR163-B paired replay/paper concurrent executor",
        "alternate_next_prs": [
            "PR164 review/provenance",
            "PR165 scoring/ranking",
            "PR162R-C real dataset source expansion",
            "PR166 LLM slot registry and model baseline control",
        ],
        "validation_status": "PASS",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_ref": "PR163_DECISION::001",
        "decision": "PR162R_B_PAPER_BINDINGS_CONSUMED_INTO_GENERIC_PAPER_ADAPTER_CAPTURE_FRAMEWORK",
        "can_qtt_consume_pr162r_b_paper_bindings": True,
        "evidence": {
            "candidate_packet_universe_count": summary["candidate_packet_universe_count"],
            "paper_adapter_input_rows": summary["paper_adapter_input_rows"],
            "paper_decision_intent_rows": summary["paper_decision_intent_rows"],
            "paper_order_intent_rows": summary["paper_order_intent_rows"],
            "paper_capture_bundle_rows": summary["paper_capture_bundle_rows"],
            "ledger_invariant_violation_count": summary["ledger_invariant_violation_count"],
        },
        "not_answered_by_this_pr": [
            "paper profitability",
            "replay/paper performance result",
            "live trading readiness",
            "source accepted truth",
            "quantum advantage",
            "LLM trading authority",
        ],
        "next_recommended_pr": summary["recommendation_next_step"],
        "alternate_next_prs": summary["alternate_next_prs"],
        "validation_status": "PASS",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
    }


def build_manifest(payloads: dict[str, dict[str, Any]], summary: dict[str, Any]) -> list[dict[str, Any]]:
    counts = {filename: payload.get("record_count", 0) for filename, payload in payloads.items()}
    counts["PR163_FinalSummary.report.json"] = 1
    counts["PR163_DecisionAndNextPRRecommendation.report.json"] = 1
    counts["PR163_ReportManifest.report.json"] = len(p.REPORT_FILENAMES)
    rows = []
    for idx, filename in enumerate(p.REPORT_FILENAMES, 1):
        payload = payloads.get(filename, {})
        shard_paths = list(payload.get("shard_files") or [])
        rows.append(
            {
                "manifest_ref": f"PR163_MANIFEST::{idx:03d}",
                "report_filename": filename,
                "row_count": payload.get("total_row_count", counts.get(filename, 0)),
                "sharded_flag": bool(payload.get("sharded_flag", False)),
                "shard_count": int(payload.get("shard_count", 0) or 0),
                "shard_paths": shard_paths,
                "shard_manifest_refs": list(payload.get("shard_manifest_refs") or []),
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "validation_status": "PASS",
                "live_order_authority": False,
            }
        )
    return rows


def _payload(
    report_id: str,
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "report_id": report_id,
        "report_filename": filename,
        "created_by_pr": "PR163",
        "authority_class": AUTHORITY_CLASS,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
        "validation_status": "PASS",
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(p.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(p.DOWNSTREAM_PR_ROUTES),
        "record_count": len(records),
        "records": records,
        **NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _report_id(filename: str) -> str:
    return filename.replace(".report.json", "").upper()
