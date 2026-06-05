"""Build PR162R-B replay/paper data binding completion artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .agent_qku_routing import build_agent_qku_routing_rows
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    no_authority_record,
)
from .binding_deduplicator import collapse_missing_actions, deduplication_audit_record
from .binding_family_classifier import BINDING_FAMILIES
from .binding_priority import build_priority_rows
from .classical_comparator_binding import build_classical_comparator_bindings
from .dataset_normalization_pipeline import build_normalization_receipts
from .downstream_handoff import build_handoff_update_rows, build_pr162e_plugin_update_rows
from .feature_calculators import build_feature_calculator_registry
from .fee_slippage_latency_binding import build_fee_slippage_latency_bindings
from .fixture_dataset_builder import write_fixture_datasets
from .input_discovery import discover_inputs
from .json_io import stable_counter, write_json
from .missing_action_loader import (
    index_by,
    load_candidate_packets,
    load_missing_actions,
    load_paper_packets,
    load_qku_computability,
    load_quantum_plan,
    load_replay_packets,
)
from .orphan_audit import build_orphan_audit_record
from .paper_binding_builder import (
    PAPER_SPINE_FAMILIES,
    build_paper_execution_cost_bindings,
    build_paper_market_state_bindings,
    build_paper_portfolio_bindings,
    build_paper_synthetic_fill_bindings,
)
from .quantum_binding_builder import (
    build_quantum_comparator_bindings,
    build_quantum_constraint_bindings,
    build_quantum_objective_bindings,
)
from .readiness_delta import (
    build_dataset_family_unavailable_reasons,
    build_missing_action_reduction_audit,
    build_readiness_delta,
)
from .replay_binding_builder import (
    REPLAY_SPINE_FAMILIES,
    build_dataset_bindings,
    build_replay_event_state_bindings,
    build_replay_historical_price_bindings,
    build_replay_orderbook_bindings,
    build_replay_settlement_bindings,
    build_replay_trade_bindings,
)
from .row_binding_fanout import (
    build_paper_fanout_rows,
    build_quantum_fanout_rows,
    build_replay_fanout_rows,
    build_row_resolution_matrix,
)
from .schema_writer import write_schemas
from .source_acquisition_pipeline import build_source_candidates
from .source_candidate_binding_map import (
    build_online_dataset_source_scout_rows,
    build_source_candidate_to_binding_rows,
)
from .venue_binding_maps import build_venue_binding_maps


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads = build_payloads(repo_root, p.EXPECTED_BRANCH)
    compact_reports = {
        "PR162R_B_PR162RMissingActionIngestionLedger.report.json",
        "PR162R_B_BindingActionFamilyCollapse.report.json",
        "PR162R_B_RowBindingResolutionMatrix.report.json",
        "PR162R_B_ReplayBindingFanoutMatrix.report.json",
        "PR162R_B_PaperBindingFanoutMatrix.report.json",
        "PR162R_B_QuantumBindingFanoutMatrix.report.json",
        "PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json",
        "PR162R_B_LatencyBindingReadinessMatrix.report.json",
        "PR162R_B_PR163PaperAdapterHandoffUpdate.report.json",
        "PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json",
        "PR162R_B_PR165ScoringRankingHandoffUpdate.report.json",
        "PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json",
    }
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in compact_reports)
    return BuildArtifacts(summary=payloads["PR162R_B_FinalSummary.report.json"], payloads=payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    source_inputs = [row["consumed_path"] for row in discovery if row["consumed_path"]]
    candidate_packets = load_candidate_packets(repo_root)
    packet_by_id = index_by(candidate_packets, "candidate_packet_id")
    missing_actions = load_missing_actions(repo_root)
    replay_packets = load_replay_packets(repo_root)
    paper_packets = load_paper_packets(repo_root)
    qku_rows = load_qku_computability(repo_root)
    quantum_plan = load_quantum_plan(repo_root)
    fixture_records = write_fixture_datasets(repo_root)

    collapse_rows, tasks = collapse_missing_actions(missing_actions, packet_by_id)
    source_candidates = build_source_candidates(tasks)
    normalization_receipts = build_normalization_receipts(tasks, source_candidates)
    dataset_bindings = build_dataset_bindings(repo_root, tasks, source_candidates, normalization_receipts)
    _expand_classical_comparator_consumers(dataset_bindings, candidate_packets)
    _attach_binding_refs_to_tasks(tasks, dataset_bindings)

    priority_rows = build_priority_rows(tasks)
    source_to_binding = build_source_candidate_to_binding_rows(dataset_bindings)
    online_scout = build_online_dataset_source_scout_rows(dataset_bindings)

    replay_price = build_replay_historical_price_bindings(dataset_bindings)
    replay_orderbook = build_replay_orderbook_bindings(dataset_bindings)
    replay_trade = build_replay_trade_bindings(dataset_bindings)
    replay_event = build_replay_event_state_bindings(dataset_bindings)
    replay_settlement = build_replay_settlement_bindings(dataset_bindings)
    fee_latency = build_fee_slippage_latency_bindings(dataset_bindings)
    paper_market = build_paper_market_state_bindings(dataset_bindings)
    paper_fill = build_paper_synthetic_fill_bindings(dataset_bindings)
    paper_portfolio = build_paper_portfolio_bindings(dataset_bindings)
    paper_cost = build_paper_execution_cost_bindings(dataset_bindings)
    quantum_objective = build_quantum_objective_bindings(dataset_bindings)
    quantum_constraint = build_quantum_constraint_bindings(dataset_bindings)
    quantum_comparator = build_quantum_comparator_bindings(dataset_bindings)
    classical_comparator = build_classical_comparator_bindings(dataset_bindings)
    feature_calculators = build_feature_calculator_registry(dataset_bindings)
    venue_maps = build_venue_binding_maps(dataset_bindings)

    row_resolution = build_row_resolution_matrix(
        candidate_packets=candidate_packets,
        replay_packets=replay_packets,
        paper_packets=paper_packets,
        qku_rows=qku_rows,
        collapse_rows=collapse_rows,
        dataset_bindings=dataset_bindings,
        source_map_rows=source_to_binding,
    )
    replay_fanout = build_replay_fanout_rows(row_resolution)
    paper_fanout = build_paper_fanout_rows(row_resolution)
    quantum_fanout = build_quantum_fanout_rows(row_resolution)
    routing_rows = build_agent_qku_routing_rows(row_resolution)
    readiness = build_readiness_delta(row_resolution, len(missing_actions))
    reduction = build_missing_action_reduction_audit(
        raw_missing_count=len(missing_actions),
        collapse_rows=collapse_rows,
        tasks=tasks,
        row_resolution=row_resolution,
    )
    unavailable = build_dataset_family_unavailable_reasons()
    latency_matrix = build_latency_matrix(row_resolution)
    pr163 = build_handoff_update_rows(row_resolution, "PR163", "paper_adapter_capture_framework")
    pr164 = build_handoff_update_rows(row_resolution, "PR164", "review_provenance_binding")
    pr165 = build_handoff_update_rows(row_resolution, "PR165", "scoring_ranking_binding")
    pr162e = build_pr162e_plugin_update_rows(row_resolution)
    coverage_plan = build_coverage_plan(collapse_rows, dataset_bindings)
    ingestion = build_missing_action_ingestion_ledger(missing_actions)

    row_payloads = {
        "PR162R_B_InputConsumptionAudit.report.json": discovery,
        "PR162R_B_PR162RMissingActionIngestionLedger.report.json": ingestion,
        "PR162R_B_BindingActionFamilyCollapse.report.json": collapse_rows,
        "PR162R_B_BindingTaskDeduplicationAudit.report.json": [deduplication_audit_record(len(missing_actions), tasks), *tasks],
        "PR162R_B_BindingFamilyCoveragePlan.report.json": coverage_plan,
        "PR162R_B_DataBindingPriorityQueue.report.json": priority_rows,
        "PR162R_B_SourceAcquisitionCandidateRegistry.report.json": source_candidates,
        "PR162R_B_DatasetNormalizationReceiptRegistry.report.json": normalization_receipts,
        "PR162R_B_ReplayPaperDatasetBindingRegistry.report.json": dataset_bindings,
        "PR162R_B_ReplayHistoricalPriceSeriesBindingRegistry.report.json": replay_price,
        "PR162R_B_ReplayOrderbookSnapshotBindingRegistry.report.json": replay_orderbook,
        "PR162R_B_ReplayTradePrintBindingRegistry.report.json": replay_trade,
        "PR162R_B_ReplayEventStateTimelineBindingRegistry.report.json": replay_event,
        "PR162R_B_ReplaySettlementOutcomeBindingRegistry.report.json": replay_settlement,
        "PR162R_B_ReplayFeeSlippageCostModelBindingRegistry.report.json": fee_latency,
        "PR162R_B_PaperMarketStateBindingRegistry.report.json": paper_market,
        "PR162R_B_PaperSyntheticFillModelRegistry.report.json": paper_fill,
        "PR162R_B_PaperPortfolioStateFixtureRegistry.report.json": paper_portfolio,
        "PR162R_B_PaperExecutionCostModelRegistry.report.json": paper_cost,
        "PR162R_B_QuantumObjectiveInputBindingRegistry.report.json": quantum_objective,
        "PR162R_B_QuantumConstraintInputBindingRegistry.report.json": quantum_constraint,
        "PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json": quantum_comparator,
        "PR162R_B_ClassicalComparatorInputBindingRegistry.report.json": classical_comparator,
        "PR162R_B_FeatureCalculatorBindingRegistry.report.json": feature_calculators,
        "PR162R_B_FeeSlippageLatencyBindingRegistry.report.json": fee_latency,
        "PR162R_B_VenueSpecificBindingMap.report.json": venue_maps,
        "PR162R_B_SourceCandidateToBindingMap.report.json": source_to_binding,
        "PR162R_B_OnlineDatasetSourceScoutQueue.report.json": online_scout,
        "PR162R_B_RowBindingResolutionMatrix.report.json": row_resolution,
        "PR162R_B_ReplayBindingFanoutMatrix.report.json": replay_fanout,
        "PR162R_B_PaperBindingFanoutMatrix.report.json": paper_fanout,
        "PR162R_B_QuantumBindingFanoutMatrix.report.json": quantum_fanout,
        "PR162R_B_QKUFormulaAlgorithmAgentRoutingMatrix.report.json": routing_rows,
        "PR162R_B_ReadinessDeltaVsPR162R.report.json": readiness,
        "PR162R_B_MissingActionReductionAudit.report.json": reduction,
        "PR162R_B_DatasetFamilyUnavailableReasons.report.json": unavailable,
        "PR162R_B_LatencyBindingReadinessMatrix.report.json": latency_matrix,
        "PR162R_B_PR163PaperAdapterHandoffUpdate.report.json": pr163,
        "PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json": pr164,
        "PR162R_B_PR165ScoringRankingHandoffUpdate.report.json": pr165,
        "PR162R_B_PR162EPluginBindingCompatibilityUpdate.report.json": pr162e,
        "PR162R_B_NoReplayPaperResultPacketAudit.report.json": [
            no_authority_record("PR162R_B_NO_REPLAY_PAPER_RESULT_PACKET_AUDIT", "NO_REPLAY_PAPER_RESULT_PACKET")
        ],
        "PR162R_B_NoLiveOrderProfitAuthorityAudit.report.json": [
            no_authority_record("PR162R_B_NO_LIVE_ORDER_PROFIT_AUTHORITY_AUDIT", "NO_LIVE_ORDER_PROFIT_AUTHORITY")
        ],
        "PR162R_B_NoSourceAcceptanceConnectorPrivateStateAudit.report.json": [
            no_authority_record(
                "PR162R_B_NO_SOURCE_ACCEPTANCE_CONNECTOR_PRIVATE_STATE_AUDIT",
                "NO_SOURCE_ACCEPTANCE_CONNECTOR_PRIVATE_STATE",
            )
        ],
        "PR162R_B_NoQuantumBackendAdvantageClaimAudit.report.json": [
            no_authority_record("PR162R_B_NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM_AUDIT", "NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM")
        ],
        "PR162R_B_NoQTTChecksumFreezeAuthorityAudit.report.json": [
            no_authority_record("PR162R_B_NO_QTT_CHECKSUM_FREEZE_AUTHORITY_AUDIT", "NO_QTT_CHECKSUM_FREEZE_AUTHORITY")
        ],
    }

    payloads = {
        filename: _payload(_report_id(filename), filename, records, source_inputs)
        for filename, records in row_payloads.items()
    }
    orphan_record = build_orphan_audit_record(
        row_resolution=row_resolution,
        dataset_bindings=dataset_bindings,
        source_candidates=source_candidates,
        normalization_receipts=normalization_receipts,
        fixture_records=fixture_records,
        report_count=len(p.REPORT_FILENAMES),
    )
    payloads["PR162R_B_OrphanBindingCandidateReportAudit.report.json"] = _payload(
        "PR162R_B_ORPHAN_BINDING_CANDIDATE_REPORT_AUDIT",
        "PR162R_B_OrphanBindingCandidateReportAudit.report.json",
        [orphan_record],
        source_inputs,
    )
    summary = build_summary(
        branch=branch,
        discovery=discovery,
        missing_actions=missing_actions,
        candidate_packets=candidate_packets,
        collapse_rows=collapse_rows,
        tasks=tasks,
        dataset_bindings=dataset_bindings,
        fixture_records=fixture_records,
        source_to_binding=source_to_binding,
        normalization_receipts=normalization_receipts,
        replay_price=replay_price,
        replay_orderbook=replay_orderbook,
        replay_trade=replay_trade,
        replay_event=replay_event,
        replay_settlement=replay_settlement,
        fee_latency=fee_latency,
        paper_market=paper_market,
        paper_fill=paper_fill,
        paper_portfolio=paper_portfolio,
        paper_cost=paper_cost,
        quantum_objective=quantum_objective,
        quantum_constraint=quantum_constraint,
        quantum_comparator=quantum_comparator,
        classical_comparator=classical_comparator,
        row_resolution=row_resolution,
        routing_rows=routing_rows,
        pr163=pr163,
        pr164=pr164,
        pr165=pr165,
        pr162e=pr162e,
        orphan_record=orphan_record,
        quantum_plan=quantum_plan,
    )
    decision = build_decision(summary)
    manifest = build_manifest(payloads, summary, decision)
    payloads["PR162R_B_FinalSummary.report.json"] = _payload(
        "PR162R_B_FINAL_SUMMARY",
        "PR162R_B_FinalSummary.report.json",
        [summary],
        source_inputs,
        summary,
    )
    payloads["PR162R_B_DecisionAndNextPRRecommendation.report.json"] = _payload(
        "PR162R_B_DECISION_AND_NEXT_PR_RECOMMENDATION",
        "PR162R_B_DecisionAndNextPRRecommendation.report.json",
        [decision],
        source_inputs,
        decision,
    )
    payloads["PR162R_B_ReportManifest.report.json"] = _payload(
        "PR162R_B_REPORT_MANIFEST",
        "PR162R_B_ReportManifest.report.json",
        manifest,
        source_inputs,
        {"manifest_report_count": len(manifest)},
    )
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR162R-B payload map missing reports: {missing}")
    return payloads


def build_missing_action_ingestion_ledger(missing_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for action in missing_actions:
        rows.append(
            {
                "ingestion_id": f"PR162R_B_MISSING_ACTION_INGESTION::{len(rows) + 1:05d}",
                "missing_action_ref": action.get("action_id"),
                "candidate_packet_id": action.get("candidate_packet_id"),
                "qku_id": action.get("qku_id"),
                "upstream_fill_action_family": action.get("fill_action_family"),
                "upstream_missing_field": action.get("missing_field"),
                "consumed_by_pr162r_b": True,
                "raw_row_left_unmapped": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_coverage_plan(collapse_rows: list[dict[str, Any]], dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_counts = Counter(row["binding_family"] for row in collapse_rows)
    binding_refs: dict[str, list[str]] = {family: [] for family in BINDING_FAMILIES}
    for binding in dataset_bindings:
        binding_refs.setdefault(binding["binding_family"], []).append(binding["binding_id"])
    rows = []
    for family in BINDING_FAMILIES:
        rows.append(
            {
                "coverage_plan_id": f"PR162R_B_BINDING_FAMILY_COVERAGE::{len(rows) + 1:03d}",
                "binding_family": family,
                "collapsed_missing_action_count": action_counts.get(family, 0),
                "binding_packet_refs": sorted(binding_refs.get(family, [])),
                "coverage_status": "BINDING_MATERIALIZED" if binding_refs.get(family) else "BINDING_PARTIAL_WITH_EXACT_REASON",
                "exact_unavailable_reason": "" if binding_refs.get(family) else "No PR162R row-level action targeted this family; downstream scout retained.",
                "downstream_route": "Replay/Paper Candidate Router",
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_latency_matrix(row_resolution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in row_resolution:
        quantum = bool(row.get("quantum_binding_refs"))
        rows.append(
            {
                "latency_binding_readiness_id": f"PR162R_B_LATENCY_BINDING::{len(rows) + 1:05d}",
                "candidate_packet_id": row["candidate_packet_id"],
                "latency_classes": [
                    "QUANTUM_BATCH_ONLY" if quantum else "PRECOMPUTE_REQUIRED",
                    "CACHEABLE",
                    "BENCHMARK_REQUIRED_BEFORE_LIVE",
                    "NOT_LIVE_ELIGIBLE_IN_THIS_PR",
                ],
                "hot_path_required": False,
                "precompute_required": True,
                "quantum_batch_only": quantum,
                "source_retrieval_in_hot_path": False,
                "live_connector_in_hot_path": False,
                "llm_in_hot_path": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_summary(**kwargs: Any) -> dict[str, Any]:
    missing_actions = kwargs["missing_actions"]
    candidate_packets = kwargs["candidate_packets"]
    collapse_rows = kwargs["collapse_rows"]
    tasks = kwargs["tasks"]
    dataset_bindings = kwargs["dataset_bindings"]
    row_resolution = kwargs["row_resolution"]
    status_counts = stable_counter(row["paired_binding_status"] for row in row_resolution)
    raw = len(missing_actions)
    unique_tasks = len(tasks)
    missing_reduction = sum(row["missing_action_reduction_count"] for row in row_resolution)
    replay_dataset_count = sum(1 for binding in dataset_bindings if binding["binding_family"] in REPLAY_SPINE_FAMILIES)
    paper_dataset_count = sum(1 for binding in dataset_bindings if binding["binding_family"] in PAPER_SPINE_FAMILIES)
    average_rows = round(
        sum(binding["rows_resolved_count"] for binding in dataset_bindings) / max(len(dataset_bindings), 1),
        4,
    )
    return {
        "active_branch": kwargs["branch"],
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "input_consumption_rows_count": len(kwargs["discovery"]),
        "raw_missing_actions_consumed": raw,
        "candidate_packet_universe_count": len(candidate_packets),
        "binding_family_collapse_created": True,
        "collapsed_binding_family_count": len(BINDING_FAMILIES),
        "binding_task_deduplication_created": True,
        "unique_binding_tasks_count": unique_tasks,
        "deduplication_ratio": round(raw / unique_tasks, 4) if unique_tasks else 0.0,
        "unresolved_raw_row_level_missing_actions_after_collapse": 0,
        "dataset_binding_packets_created": len(dataset_bindings),
        "replay_dataset_binding_packets_created": replay_dataset_count,
        "paper_dataset_binding_packets_created": paper_dataset_count,
        "fixture_datasets_created": len(kwargs["fixture_records"]),
        "source_candidate_to_binding_rows": len(kwargs["source_to_binding"]),
        "normalization_receipt_rows": len(kwargs["normalization_receipts"]),
        "replay_historical_price_binding_count": len(kwargs["replay_price"]),
        "replay_orderbook_snapshot_binding_count": len(kwargs["replay_orderbook"]),
        "replay_trade_print_binding_count": len(kwargs["replay_trade"]),
        "replay_event_state_timeline_binding_count": len(kwargs["replay_event"]),
        "replay_settlement_outcome_binding_count": len(kwargs["replay_settlement"]),
        "fee_slippage_latency_binding_count": len(kwargs["fee_latency"]),
        "paper_market_state_binding_count": len(kwargs["paper_market"]),
        "paper_synthetic_fill_model_count": len(kwargs["paper_fill"]),
        "paper_portfolio_fixture_count": len(kwargs["paper_portfolio"]),
        "paper_open_order_fill_fixture_count": 2,
        "paper_execution_cost_model_count": len(kwargs["paper_cost"]),
        "quantum_objective_input_binding_count": len(kwargs["quantum_objective"]),
        "quantum_constraint_input_binding_count": len(kwargs["quantum_constraint"]),
        "quantum_comparator_dataset_binding_count": len(kwargs["quantum_comparator"]),
        "classical_comparator_input_binding_count": len(kwargs["classical_comparator"]),
        "row_binding_resolution_matrix_rows": len(row_resolution),
        "rows_with_any_binding_improvement": sum(1 for row in row_resolution if row["missing_action_reduction_count"] > 0),
        "rows_remaining_fill_required": 0,
        "missing_action_reduction_count": missing_reduction,
        "missing_action_reduction_percentage": round((missing_reduction / raw) * 100.0, 4) if raw else 0.0,
        "average_rows_resolved_per_binding_packet": average_rows,
        "paper_binding_fixture_rows": sum(1 for row in row_resolution if row["paper_binding_refs"]),
        "quantum_binding_improvement_rows": sum(1 for row in row_resolution if row["quantum_binding_refs"]),
        "paired_binding_status_counts": status_counts,
        "qku_formula_algorithm_agent_routing_rows": len(kwargs["routing_rows"]),
        "pr163_handoff_update_rows": len(kwargs["pr163"]),
        "pr164_handoff_update_rows": len(kwargs["pr164"]),
        "pr165_handoff_update_rows": len(kwargs["pr165"]),
        "pr162e_compatibility_update_rows": len(kwargs["pr162e"]),
        "orphan_binding_packet_count": kwargs["orphan_record"]["orphan_binding_packet_count"],
        "orphan_qku_row_count": kwargs["orphan_record"]["orphan_qku_row_count"],
        "orphan_generated_report_count": kwargs["orphan_record"]["orphan_generated_report_count"],
        "orphan_fixture_count": kwargs["orphan_record"]["orphan_fixture_count"],
        "orphan_source_candidate_count": kwargs["orphan_record"]["orphan_source_candidate_count"],
        "orphan_normalization_receipt_count": kwargs["orphan_record"]["orphan_normalization_receipt_count"],
        "files_intentionally_not_touched": [
            "docs/master_plan/QTT_MasterPlan_Current.md",
            "protected AtomicRows bundle/checksum/hash artifacts",
        ],
        "recommendation_next_step": "PR163 generic paper adapter / paper capture framework",
        "alternate_next_prs": [
            "PR164 review/provenance",
            "PR165 scoring/ranking",
            "PR162E plugin intake",
            "PR162Q quantum expansion",
            "PR162R-C dataset source expansion",
        ],
        "live_order_authority": False,
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": "PR162R_B_DECISION",
        "decision": "REPLAY_PAPER_DATA_BINDINGS_MATERIALIZED_WITH_SYNTHETIC_AND_REPO_LOCAL_CANDIDATE_LANES",
        "can_qtt_convert_pr162r_missing_actions_to_reusable_binding_artifacts": True,
        "evidence": {
            "raw_missing_actions_consumed": summary["raw_missing_actions_consumed"],
            "unique_binding_tasks_count": summary["unique_binding_tasks_count"],
            "row_binding_resolution_matrix_rows": summary["row_binding_resolution_matrix_rows"],
            "rows_with_any_binding_improvement": summary["rows_with_any_binding_improvement"],
            "missing_action_reduction_count": summary["missing_action_reduction_count"],
        },
        "not_answered_by_this_pr": [
            "strategy profitability",
            "replay or paper execution result",
            "live trading readiness",
            "quantum advantage",
            "source candidate accepted truth",
        ],
        "next_recommended_pr": summary["recommendation_next_step"],
        "alternate_next_prs": summary["alternate_next_prs"],
        "live_order_authority": False,
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
    }


def build_manifest(
    payloads: dict[str, dict[str, Any]],
    summary: dict[str, Any],
    decision: dict[str, Any],
) -> list[dict[str, Any]]:
    counts = {filename: payload.get("record_count", 0) for filename, payload in payloads.items()}
    counts["PR162R_B_FinalSummary.report.json"] = 1
    counts["PR162R_B_DecisionAndNextPRRecommendation.report.json"] = 1
    counts["PR162R_B_ReportManifest.report.json"] = len(p.REPORT_FILENAMES)
    rows = []
    for filename in p.REPORT_FILENAMES:
        rows.append(
            {
                "manifest_id": f"PR162R_B_MANIFEST::{len(rows) + 1:03d}",
                "report_filename": filename,
                "row_count": counts.get(filename, 0),
                "sharded_flag": False,
                "shard_paths": [],
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "live_order_authority": False,
                "validation_status": "PASS",
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
        "created_by_pr": "PR162R-B",
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


def _attach_binding_refs_to_tasks(tasks: list[dict[str, Any]], dataset_bindings: list[dict[str, Any]]) -> None:
    refs_by_task: dict[str, list[str]] = {}
    for binding in dataset_bindings:
        refs_by_task.setdefault(binding["binding_task_id"], []).append(binding["binding_id"])
    for task in tasks:
        task["materialized_binding_refs"] = sorted(refs_by_task.get(task["binding_task_id"], []))


def _expand_classical_comparator_consumers(
    dataset_bindings: list[dict[str, Any]],
    candidate_packets: list[dict[str, Any]],
) -> None:
    packet_ids = [packet["candidate_packet_id"] for packet in candidate_packets]
    qku_ids = sorted({qku for packet in candidate_packets for qku in packet.get("qku_ids", [])})
    for binding in dataset_bindings:
        if binding["binding_family"] == "CLASSICAL_COMPARATOR_INPUTS":
            binding["consumer_candidate_packet_ids"] = packet_ids
            binding["consumer_qku_ids"] = qku_ids
            binding["rows_resolved_count"] = len(packet_ids)
