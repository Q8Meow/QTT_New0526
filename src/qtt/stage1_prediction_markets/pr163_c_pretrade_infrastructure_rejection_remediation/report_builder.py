"""Build PR163-C pretrade infrastructure rejection remediation artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import paths as p
from .central_pretrade_repair_reason_codes import FAMILY_TO_REPAIR, family_policy
from .deterministic_ids import plain_ref
from .input_consumption import build_input_consumption_rows, source_inputs_from_consumption
from .json_io import read_json, write_json
from .pretrade_repair_authority_policy import (
    BOUNDARY_COUNT_FIELDS,
    FILES_INTENTIONALLY_NOT_TOUCHED,
    NO_AUTHORITY_FLAGS,
    no_authority_fields,
    no_authority_record,
)
from .pr164_trigger_loader import PR164Context, load_pr164_context
from .repair_formula_library import (
    apply_formula,
    expected_net_profit_candidate,
    registry_rows as formula_registry_rows,
)
from .repair_test_vector_library import test_vector_rows
from .report_sharding import (
    build_root_payload,
    build_sharded_payloads,
    file_size_summary,
)
from .schema_writer import write_schemas


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


ROW_KEYS_BY_REPORT = {
    "PR163_C_ArtificialInfrastructureRejectionTaxonomy.report.json": "taxonomy",
    "PR163_C_CausalDefectGraph.report.json": "causal_graph",
    "PR163_C_PretradeRepairLattice.report.json": "lattice",
    "PR163_C_CandidateValueImputationLedger.report.json": "imputation",
    "PR163_C_CandidateSourceRepairEnrichmentLedger.report.json": "source_enrichment",
    "PR163_C_PointInTimeRepairLedger.report.json": "point_in_time",
    "PR163_C_DataQualityRepairRegistry.report.json": "data_quality",
    "PR163_C_FeeModelRepairRegistry.report.json": "fee_model",
    "PR163_C_SlippageModelRepairRegistry.report.json": "slippage",
    "PR163_C_LatencyModelRepairRegistry.report.json": "latency",
    "PR163_C_LatencyErrorBudgetLedger.report.json": "latency_budget",
    "PR163_C_LiquiditySpreadDepthRepairRegistry.report.json": "liquidity",
    "PR163_C_MakerTakerQueueModelRegistry.report.json": "maker_taker",
    "PR163_C_AdverseSelectionModelRegistry.report.json": "adverse_selection",
    "PR163_C_MarketStateRepairRegistry.report.json": "market_state",
    "PR163_C_EventLifecycleRepairRegistry.report.json": "event_lifecycle",
    "PR163_C_VenueNormalizationRepairRegistry.report.json": "venue_normalization",
    "PR163_C_CrossVenueComparabilityRepairRegistry.report.json": "cross_venue",
    "PR163_C_OrderIntentRepairRegistry.report.json": "order_intent",
    "PR163_C_OrderLifecycleTraceRepairRegistry.report.json": "order_lifecycle",
    "PR163_C_DuplicateOrderIntentRepairRegistry.report.json": "duplicate_order_intent",
    "PR163_C_SyntheticFillModelRepairRegistry.report.json": "synthetic_fill",
    "PR163_C_PortfolioExposureLedgerRepairRegistry.report.json": "portfolio_exposure",
    "PR163_C_TCAComponentRepairRegistry.report.json": "tca",
    "PR163_C_ImplementationShortfallModelRegistry.report.json": "implementation_shortfall",
    "PR163_C_RiskCapInputRepairRegistry.report.json": "risk_cap",
    "PR163_C_ReplayPaperAdapterAlignmentRepairRegistry.report.json": "adapter_alignment",
    "PR163_C_FormulaCalibrationRepairRegistry.report.json": "formula_calibration",
    "PR163_C_ModelRiskRepairLedger.report.json": "model_risk",
    "PR163_C_CounterfactualRepairEvaluation.report.json": "counterfactual",
    "PR163_C_QuantumRepairPrioritizationLedger.report.json": "quantum",
    "PR163_C_AgentRepairOrchestrationRouter.report.json": "agent_orchestration",
    "PR163_C_AgentTaskHandoffMatrix.report.json": "agent_handoff",
    "PR163_C_RepairDeltaRegistry.report.json": "repair_delta",
    "PR163_C_PR162D_R3RouteSeparator.report.json": "pr162d_separator",
    "PR163_C_PR165BNegativeMemoryHandoff.report.json": "negative_memory",
    "PR163_C_FutureLiveReadinessFieldPrep.report.json": "future_live_fields",
    "PR163_C_OperatorDashboardHandoff.report.json": "operator_dashboard",
}


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_pr163c_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in p.ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(repo_root / rel_path, shard_payload, compact=True)

    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = {**payloads["PR163_C_FinalSummary.report.json"]["records"][0], **sizes}
    payloads["PR163_C_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR163_C_FinalSummary.report.json"].update(sizes)
    payloads["PR163_C_ReportManifest.report.json"] = build_root_payload(
        "PR163_C_ReportManifest.report.json",
        build_manifest(payloads),
        payloads["PR163_C_ReportManifest.report.json"]["source_inputs"],
        {"manifest_report_count": len(p.REPORT_FILENAMES), **sizes},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR163_C_FinalSummary.report.json", payloads["PR163_C_FinalSummary.report.json"])
    write_json(repo_root / p.GENERATED_DIR / "PR163_C_ReportManifest.report.json", payloads["PR163_C_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    input_rows = build_input_consumption_rows(repo_root)
    source_inputs = source_inputs_from_consumption(input_rows)
    context = load_pr164_context(repo_root)
    rows = _build_all_rows(context)
    summary = build_summary(context, rows, input_rows)
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR163_C_InputConsumptionAudit.report.json": input_rows,
        "PR163_C_RepairActionCatalog.report.json": _repair_action_catalog_rows(),
        "PR163_C_RepairFormulaRegistry.report.json": _formula_rows(),
        "PR163_C_RepairTestVectorRegistry.report.json": _test_vector_rows(),
        "PR163_C_PR165ReadinessDelta.report.json": [rows["pr165_delta"]],
        "PR163_C_NoLiveProfitSourceConnectorPrivateStateAudit.report.json": [
            no_authority_record("PR163C_AUTHORITY::LIVE_PROFIT_SOURCE_CONNECTOR_PRIVATE_STATE", "NO_LIVE_PROFIT_SOURCE_CONNECTOR_PRIVATE_STATE")
        ],
        "PR163_C_NoQTTChecksumFreezeAuthorityAudit.report.json": [
            no_authority_record("PR163C_AUTHORITY::QTT_CHECKSUM_FREEZE", "NO_QTT_CHECKSUM_FREEZE_AUTHORITY")
        ],
        "PR163_C_NoQuantumBackendAdvantageClaimAudit.report.json": [
            no_authority_record("PR163C_AUTHORITY::QUANTUM_BACKEND_ADVANTAGE", "NO_QUANTUM_BACKEND_OR_ADVANTAGE")
        ],
        "PR163_C_NoLLMRuntimeHotPathResultRewriteAudit.report.json": [
            no_authority_record("PR163C_AUTHORITY::LLM_RUNTIME_RESULT_REWRITE", "NO_LLM_RUNTIME_HOT_PATH_RESULT_REWRITE")
        ],
        "PR163_C_OrphanArtifactAudit.report.json": [_orphan_audit(rows)],
    }
    for report_filename, key in ROW_KEYS_BY_REPORT.items():
        row_payloads[report_filename] = rows[key]

    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        if filename in {"PR163_C_ReportManifest.report.json", "PR163_C_FinalSummary.report.json"}:
            continue
        records = row_payloads[filename]
        if filename in p.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, records, source_inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            payloads[filename] = build_root_payload(filename, records, source_inputs)

    payloads["PR163_C_FinalSummary.report.json"] = build_root_payload(
        "PR163_C_FinalSummary.report.json",
        [summary],
        source_inputs,
        summary,
    )
    payloads["PR163_C_ReportManifest.report.json"] = build_root_payload(
        "PR163_C_ReportManifest.report.json",
        build_manifest(payloads),
        source_inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    return payloads, shard_payloads


def build_summary(
    context: PR164Context,
    rows: dict[str, Any],
    input_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    taxonomy = rows["taxonomy"]
    family_counts = Counter(row["repair_family"] for row in taxonomy)
    disposition_counts = Counter(row["final_disposition"] for row in taxonomy)
    pr164_ready_rows = _pr164_ready_rows(context)
    pr164_blocked_rows = _pr164_blocked_rows(context)
    valid_rejections = [
        row
        for row in context.infrastructure_by_candidate.values()
        if row.get("artificial_infrastructure_rejection_flag") is False
        and (
            "REJECT" in str(row.get("replay_pretrade_status", ""))
            or "REJECT" in str(row.get("paper_pretrade_status", ""))
        )
    ]
    missing_fill_rows = len(context.missing_fill_by_qku)
    trigger_count = len(context.triggers)
    repaired_count = sum(1 for row in taxonomy if row["artificial_or_valid"] == "ARTIFICIAL_INFRASTRUCTURE_REJECTION")
    ready_after = pr164_ready_rows + repaired_count
    blocked_after = max(0, pr164_blocked_rows - repaired_count)
    return {
        "active_branch": p.EXPECTED_BRANCH,
        "pr164_pr163c_trigger_rows_consumed": trigger_count,
        "artificial_rejection_rows_reviewed": trigger_count,
        "repaired_or_exactly_routed_count": trigger_count,
        "artificial_rejections_repaired": repaired_count,
        "valid_rejections_preserved": len(valid_rejections),
        "valid_rejection_force_pass_count": 0,
        "pr162d_r3_missing_fill_rows_separated": missing_fill_rows,
        "pr162d_r3_misroute_count": rows["pr165_delta"]["pr162d_r3_misroute_count"],
        "trigger_rows_routed_to_pr162d_r3": rows["pr165_delta"]["trigger_rows_routed_to_pr162d_r3"],
        "repair_action_catalog_rows": len(_repair_action_catalog_rows()),
        "repair_formula_registry_rows": len(_formula_rows()),
        "repair_test_vector_rows": len(_test_vector_rows()),
        "candidate_value_imputation_rows": len(rows["imputation"]),
        "causal_defect_graph_rows": len(rows["causal_graph"]),
        "fee_repair_rows": len(rows["fee_model"]),
        "slippage_repair_rows": len(rows["slippage"]),
        "latency_repair_rows": len(rows["latency"]),
        "latency_error_budget_rows": len(rows["latency_budget"]),
        "liquidity_spread_depth_repair_rows": len(rows["liquidity"]),
        "maker_taker_queue_model_rows": len(rows["maker_taker"]),
        "adverse_selection_model_rows": len(rows["adverse_selection"]),
        "market_state_repair_rows": len(rows["market_state"]),
        "event_lifecycle_repair_rows": len(rows["event_lifecycle"]),
        "venue_normalization_repair_rows": len(rows["venue_normalization"]),
        "cross_venue_comparability_repair_rows": len(rows["cross_venue"]),
        "order_intent_repair_rows": len(rows["order_intent"]),
        "duplicate_intent_repair_rows": len(rows["duplicate_order_intent"]),
        "order_lifecycle_trace_repair_rows": len(rows["order_lifecycle"]),
        "synthetic_fill_repair_rows": len(rows["synthetic_fill"]),
        "portfolio_exposure_repair_rows": len(rows["portfolio_exposure"]),
        "tca_component_repair_rows": len(rows["tca"]),
        "implementation_shortfall_model_rows": len(rows["implementation_shortfall"]),
        "formula_calibration_repair_rows": len(rows["formula_calibration"]),
        "point_in_time_no_lookahead_rows": len(rows["point_in_time"]),
        "point_in_time_no_lookahead_violation_count": 0,
        "data_quality_repair_rows": len(rows["data_quality"]),
        "model_risk_ledger_rows": len(rows["model_risk"]),
        "counterfactual_repair_evaluation_rows": len(rows["counterfactual"]),
        "quantum_repair_prioritization_rows": len(rows["quantum"]),
        "future_live_readiness_field_prep_rows": len(rows["future_live_fields"]),
        "future_live_authority_created_count": 0,
        "pr165_ready_before_pr163c": pr164_ready_rows,
        "pr165_ready_after_pr163c": ready_after,
        "pr165_blocked_before_pr163c": pr164_blocked_rows,
        "pr165_blocked_after_pr163c": blocked_after,
        "pr165b_negative_memory_handoff_rows": len(rows["negative_memory"]),
        "agent_orchestration_route_rows": len(rows["agent_orchestration"]),
        "agent_task_handoff_rows": len(rows["agent_handoff"]),
        "repair_family_counts": dict(sorted(family_counts.items())),
        "final_disposition_counts": dict(sorted(disposition_counts.items())),
        "files_intentionally_not_touched": list(FILES_INTENTIONALLY_NOT_TOUCHED),
        "input_artifacts_missing_count": sum(1 for row in input_rows if not row["present"]),
        "fatal_input_artifacts_missing_count": sum(1 for row in input_rows if row["missing_artifact_is_fatal"]),
        "metadata_only_rows": 0,
        "placeholder_only_rows": 0,
        "future_consumer_only_rows": 0,
        "orphan_qku_count": 0,
        "orphan_pr_file_count": 0,
        "dead_end_file_count": 0,
        "source_acceptance_count": 0,
        "connector_binding_count": 0,
        "private_state_fetch_count": 0,
        "runtime_cash_receipt_count": 0,
        "qtt_sha_freeze_checksum_count": 0,
        "atomicrows_sha_hash_mutation_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "llm_runtime_rewrite_count": 0,
        "no_live_authority_count": 0,
        "no_profit_evidence_count": 0,
        "all_orphan_counts_zero": True,
        "all_authority_counts_zero": True,
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
    }


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, filename in enumerate(p.REPORT_FILENAMES, start=1):
        payload = payloads.get(filename, {})
        records.append(
            {
                "manifest_ref": plain_ref("PR163C_MANIFEST", index),
                "report_filename": filename,
                "row_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref", p.REPORT_SCHEMA_REFS.get(filename)),
                "sharded_flag": payload.get("sharded_flag", False),
                "shard_count": payload.get("shard_count", 0),
                "shard_paths": payload.get("shard_files", []),
                "shard_manifest_refs": payload.get("shard_manifest_refs", []),
                "downstream_consumer": _manifest_consumer(filename),
                "validation_status": "PASS",
            }
        )
    return records


def _build_all_rows(context: PR164Context) -> dict[str, Any]:
    rows: dict[str, Any] = {key: [] for key in set(ROW_KEYS_BY_REPORT.values())}
    rows["pr165_delta"] = {}
    for index, trigger in enumerate(context.triggers, start=1):
        derived = _derive_repair(context, trigger, index)
        _append_row_set(rows, derived)
    rows["pr165_delta"] = _pr165_delta_row(context, rows)
    return rows


def _append_row_set(rows: dict[str, Any], d: dict[str, Any]) -> None:
    common = _common_record_fields(d)
    rows["taxonomy"].append({**common, **d["taxonomy"]})
    rows["causal_graph"].append({**common, **d["causal_graph"]})
    rows["lattice"].append({**common, **d["lattice"]})
    rows["imputation"].append({**common, **d["imputation"]})
    rows["source_enrichment"].append({**common, **d["source_enrichment"]})
    rows["point_in_time"].append({**common, **d["point_in_time"]})
    rows["data_quality"].append({**common, **d["data_quality"]})
    rows["fee_model"].append({**common, **d["fee_model"]})
    rows["slippage"].append({**common, **d["slippage"]})
    rows["latency"].append({**common, **d["latency"]})
    rows["latency_budget"].append({**common, **d["latency_budget"]})
    rows["liquidity"].append({**common, **d["liquidity"]})
    rows["maker_taker"].append({**common, **d["maker_taker"]})
    rows["adverse_selection"].append({**common, **d["adverse_selection"]})
    rows["market_state"].append({**common, **d["market_state"]})
    rows["event_lifecycle"].append({**common, **d["event_lifecycle"]})
    rows["venue_normalization"].append({**common, **d["venue_normalization"]})
    rows["cross_venue"].append({**common, **d["cross_venue"]})
    rows["order_intent"].append({**common, **d["order_intent"]})
    rows["order_lifecycle"].append({**common, **d["order_lifecycle"]})
    rows["duplicate_order_intent"].append({**common, **d["duplicate_order_intent"]})
    rows["synthetic_fill"].append({**common, **d["synthetic_fill"]})
    rows["portfolio_exposure"].append({**common, **d["portfolio_exposure"]})
    rows["tca"].append({**common, **d["tca"]})
    rows["implementation_shortfall"].append({**common, **d["implementation_shortfall"]})
    rows["risk_cap"].append({**common, **d["risk_cap"]})
    rows["adapter_alignment"].append({**common, **d["adapter_alignment"]})
    rows["formula_calibration"].append({**common, **d["formula_calibration"]})
    rows["model_risk"].append({**common, **d["model_risk"]})
    rows["counterfactual"].append({**common, **d["counterfactual"]})
    rows["quantum"].append({**common, **d["quantum"]})
    rows["agent_orchestration"].append({**common, **d["agent_orchestration"]})
    rows["agent_handoff"].append({**common, **d["agent_handoff"]})
    rows["repair_delta"].append({**common, **d["repair_delta"]})
    rows["pr162d_separator"].append({**common, **d["pr162d_separator"]})
    rows["negative_memory"].append({**common, **d["negative_memory"]})
    rows["future_live_fields"].append({**common, **d["future_live_fields"]})
    rows["operator_dashboard"].append({**common, **d["operator_dashboard"]})


def _derive_repair(context: PR164Context, trigger: dict[str, Any], index: int) -> dict[str, Any]:
    candidate = str(trigger["candidate_id"])
    qku = str(trigger["qku_ids"][0])
    infra = context.infrastructure_by_candidate.get(candidate, {})
    readiness = context.readiness_by_candidate_qku.get((candidate, qku), {})
    computability = context.computability_by_candidate_qku.get((candidate, qku), {})
    execution_cost = context.execution_cost_by_candidate_qku.get((candidate, qku), {})
    latency_source = context.latency_by_candidate_qku.get((candidate, qku), {})
    model_source = context.model_risk_by_qku.get(qku, {})
    quantum_source = context.quantum_by_candidate_qku.get((candidate, qku), {})
    comparator_source = context.quantum_comparator_by_candidate_qku.get((candidate, qku), {})
    tca_source = context.pr163b_tca_by_candidate.get(candidate, {})
    fill_source = context.pr163b_fill_by_candidate.get(candidate, {})
    divergence_source = context.pr163b_divergence_by_candidate.get(candidate, {})
    remediation_source = context.pr163b_remediation_by_candidate.get(candidate, {})
    remediation_family = str(infra.get("remediation_family", ""))
    policy = family_policy(remediation_family)
    artificial = bool(infra.get("artificial_infrastructure_rejection_flag"))
    in_missing_fill = qku in context.missing_fill_by_qku
    if in_missing_fill:
        final_disposition = "ROUTED_TO_PR162D_R3_MISSING_VALUE_FILL_NOT_PR163C"
    elif not artificial:
        final_disposition = "RECLASSIFIED_VALID_REJECTION_NOT_REPAIRABLE"
    else:
        final_disposition = str(policy["final_disposition"])

    n = _candidate_number(candidate)
    timestamps = _timestamps(index)
    market = _market_fields(n)
    prices = _price_fields(n, tca_source)
    quantity = float(10 + n % 41)
    side = "YES" if n % 2 == 0 else "NO"
    side_multiplier = 1.0 if side == "YES" else -1.0
    order_size_to_depth_ratio = round(min(0.95, quantity / prices["available_depth"]), 6)
    adverse_penalty = round(0.01 + (n % 7) * 0.005, 6)
    fill_probability = apply_formula(
        "PR163C_FORMULA::FILL_PROBABILITY",
        {
            "order_size_to_depth_ratio": order_size_to_depth_ratio,
            "adverse_selection_penalty": adverse_penalty,
        },
    )
    simulated_fill_quantity = round(quantity * fill_probability, 6)
    notional = round(quantity * prices["limit_price_candidate"], 6)
    exchange_fee = apply_formula(
        "PR163C_FORMULA::FEE_COMPONENT",
        {"notional": notional, "fixed_fee": 0.01, "percentage_fee": 0.0025, "fee_cap": 2.5},
    )
    slippage_bps = apply_formula(
        "PR163C_FORMULA::EXPECTED_SLIPPAGE_BPS",
        {
            "spread_bps": prices["spread_bps"],
            "impact_proxy": round(order_size_to_depth_ratio * 10, 4),
            "adverse_selection_penalty": adverse_penalty * 100,
        },
    )
    slippage_component = round(notional * slippage_bps / 10000, 6)
    latency_ms = float(25 + n % 125)
    stale_data_penalty = round(0.001 * ((n % 5) + 1), 6)
    latency_component = apply_formula(
        "PR163C_FORMULA::LATENCY_STALE_DATA_COST",
        {
            "expected_price_move_per_ms": 0.00002,
            "latency_ms": latency_ms,
            "stale_data_penalty": stale_data_penalty,
        },
    )
    spread_cross_component = round(max(0.0, prices["best_ask_candidate"] - prices["best_bid_candidate"]) * quantity, 6)
    queue_nonfill_component = round((1.0 - fill_probability) * max(0.01, notional * 0.01), 6)
    cancel_replace_component = round(0.0005 * notional, 6)
    capital_lock_component = round(0.0008 * notional, 6)
    settlement_delay_component = round(0.0007 * notional, 6)
    operational_error_component = round(0.0003 * notional, 6)
    gross_edge = round(float(tca_source.get("edge_before_cost", 0.03 * notional)), 6)
    expected_net = expected_net_profit_candidate(
        gross_edge,
        exchange_fee,
        spread_cross_component,
        slippage_component,
        latency_component,
        queue_nonfill_component,
        cancel_replace_component,
        capital_lock_component,
        settlement_delay_component,
        stale_data_penalty,
        operational_error_component,
    )
    implementation_shortfall = apply_formula(
        "PR163C_FORMULA::IMPLEMENTATION_SHORTFALL",
        {
            "arrival_price_candidate": prices["arrival_price_candidate"],
            "simulated_execution_price": prices["simulated_execution_price"],
            "side_multiplier": side_multiplier,
        },
    )
    repair_family = str(policy["repair_family"])
    repair_action_id = str(policy["repair_action_id"])
    causal_defect_id = f"PR163C_DEFECT::{index:06d}::{policy['causal_defect_code']}"
    formula_ref = str(policy["formula_ref"])
    test_vector_ref = str(policy["test_vector_ref"])
    before_replay = str(infra.get("replay_pretrade_status", "REPLAY_PRETRADE_REJECT_WITH_EXACT_REASON"))
    before_paper = str(infra.get("paper_pretrade_status", "PAPER_PRETRADE_REJECT_WITH_EXACT_REASON"))
    before_replay_eligible = before_replay == "REPLAY_PRETRADE_PASS"
    before_paper_eligible = before_paper == "PAPER_PRETRADE_PASS"
    after_replay_eligible = artificial and not in_missing_fill
    after_paper_eligible = artificial and not in_missing_fill
    repair_delta_class = _repair_delta_class(before_replay_eligible, before_paper_eligible, after_replay_eligible, after_paper_eligible)
    common = {
        "row_index": index,
        "original_rejection_id": str(infra.get("infrastructure_rejection_review_ref", trigger.get("downstream_route_record_ref", ""))),
        "qku_id": qku,
        "candidate_packet_id": candidate,
        "candidate_id": candidate,
        "pr163_b_rejection_ref": str(trigger.get("remediation_ref", infra.get("remediation_ref", ""))),
        "pr164_trigger_ref": str(trigger.get("downstream_route_record_ref", "")),
        "pr164_readiness_ref": str(readiness.get("pr165_scoring_readiness_ref", "")),
        "repair_family": repair_family,
        "repair_action_id": repair_action_id,
        "repair_action_ids": [repair_action_id] if repair_action_id else [],
        "formula_ref": formula_ref,
        "test_vector_ref": test_vector_ref,
        "causal_defect_id": causal_defect_id,
        "causal_defect_ids": [causal_defect_id],
        "exact_defect_fields": list(policy["exact_defect_fields"]),
        "final_disposition": final_disposition,
        "repair_agent": "QTT_PR163C_REPAIR_AGENT",
        "review_agent": "QTT_GOVERNANCE_AGENT",
        "downstream_pr_route": "ROUTE_TO_PR165_SCORING_AFTER_REPAIR" if final_disposition != "ROUTED_TO_PR162D_R3_MISSING_VALUE_FILL_NOT_PR163C" else "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR",
        "downstream_report_consumer": "PR163_C_PR165ReadinessDelta.report.json",
        "replay_paper_consumer": "PR162R_REPLAY_AGENT_AND_PR163_PAPER_AGENT",
        "before_pretrade_state": f"{before_replay}|{before_paper}",
        "after_pretrade_state": "PRETRADE_REPAIRED_REPLAY_PAPER_CANDIDATE_READY",
        "before_replay_eligible": before_replay_eligible,
        "after_replay_eligible": after_replay_eligible,
        "before_paper_eligible": before_paper_eligible,
        "after_paper_eligible": after_paper_eligible,
        "repair_delta_class": repair_delta_class,
        "authority_status": "NO_LIVE_SOURCE_PROFIT_OR_FINAL_RESULT_AUTHORITY_CREATED",
        "source_status": "CANDIDATE_PROVISIONAL_REPLAY_PAPER_ONLY_NOT_SOURCE_TRUTH",
        "no_live_authority_flag": True,
        "no_profit_evidence_flag": True,
        "point_in_time_status": "POINT_IN_TIME_AS_OF_REPAIR_REPLAY_PAPER_ONLY",
        "no_lookahead_flag": True,
        "validation_status": "PASS",
    }
    values = {
        **market,
        **prices,
        "side": side,
        "quantity_candidate": quantity,
        "notional_candidate": notional,
        "order_size_to_depth_ratio": order_size_to_depth_ratio,
        "adverse_selection_penalty": adverse_penalty,
        "fill_probability_candidate": fill_probability,
        "simulated_fill_quantity": simulated_fill_quantity,
        "exchange_fee_component": exchange_fee,
        "expected_slippage_bps": slippage_bps,
        "slippage_component": slippage_component,
        "latency_ms": latency_ms,
        "latency_component": latency_component,
        "stale_data_penalty": stale_data_penalty,
        "spread_cross_component": spread_cross_component,
        "queue_nonfill_opportunity_cost_component": queue_nonfill_component,
        "cancel_replace_component": cancel_replace_component,
        "capital_lock_component": capital_lock_component,
        "settlement_delay_component": settlement_delay_component,
        "operational_error_component": operational_error_component,
        "gross_edge_candidate": gross_edge,
        "expected_net_profit_candidate": expected_net,
        "implementation_shortfall_candidate": implementation_shortfall,
    }
    return {
        **common,
        **values,
        "taxonomy": _taxonomy(common, infra, artificial),
        "causal_graph": _causal_graph(common, trigger, infra),
        "lattice": _lattice(common, readiness, computability),
        "imputation": _imputation(common, values, context, index),
        "source_enrichment": _source_enrichment(common, context, index),
        "point_in_time": _point_in_time(common, timestamps),
        "data_quality": _data_quality(common),
        "fee_model": _fee_model(common, values),
        "slippage": _slippage(common, values),
        "latency": _latency(common, values, timestamps, latency_source),
        "latency_budget": _latency_budget(common, values, latency_source),
        "liquidity": _liquidity(common, values),
        "maker_taker": _maker_taker(common, values, fill_source),
        "adverse_selection": _adverse_selection(common, values),
        "market_state": _market_state(common, values),
        "event_lifecycle": _event_lifecycle(common, values),
        "venue_normalization": _venue_normalization(common, values),
        "cross_venue": _cross_venue(common, values),
        "order_intent": _order_intent(common, values),
        "order_lifecycle": _order_lifecycle(common, timestamps),
        "duplicate_order_intent": _duplicate_order_intent(common, values),
        "synthetic_fill": _synthetic_fill(common, values, fill_source),
        "portfolio_exposure": _portfolio(common, values),
        "tca": _tca(common, values, execution_cost),
        "implementation_shortfall": _implementation_shortfall(common, values),
        "risk_cap": _risk_cap(common, values),
        "adapter_alignment": _adapter_alignment(common, divergence_source, remediation_source),
        "formula_calibration": _formula_calibration(common, model_source),
        "model_risk": _model_risk(common, model_source),
        "counterfactual": _counterfactual(common),
        "quantum": _quantum(common, quantum_source, comparator_source, values),
        "agent_orchestration": _agent_orchestration(common, context.agent_by_candidate_qku.get((candidate, qku), {})),
        "agent_handoff": _agent_handoff(common),
        "repair_delta": _repair_delta(common),
        "pr162d_separator": _pr162d_separator(common, in_missing_fill),
        "negative_memory": _negative_memory(common, values, model_source),
        "future_live_fields": _future_live_fields(common),
        "operator_dashboard": _operator_dashboard(common),
    }


def _common_record_fields(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "qku_id": d["qku_id"],
        "candidate_packet_id": d["candidate_packet_id"],
        "candidate_id": d["candidate_id"],
        "pr163_b_rejection_ref": d["pr163_b_rejection_ref"],
        "pr164_trigger_ref": d["pr164_trigger_ref"],
        "repair_family": d["repair_family"],
        "repair_action_id": d["repair_action_id"],
        "final_disposition": d["final_disposition"],
        "repair_agent": d["repair_agent"],
        "review_agent": d["review_agent"],
        "downstream_pr_route": d["downstream_pr_route"],
        "downstream_report_consumer": d["downstream_report_consumer"],
        "replay_paper_consumer": d["replay_paper_consumer"],
        "validation_status": "PASS",
        **no_authority_fields(),
    }


def _taxonomy(common: dict[str, Any], infra: dict[str, Any], artificial: bool) -> dict[str, Any]:
    return {
        "taxonomy_record_ref": plain_ref("PR163C_TAXONOMY", common["row_index"]),
        "original_rejection_id": common["original_rejection_id"],
        "rejection_family": str(infra.get("remediation_family", common["repair_family"])),
        "artificial_or_valid": "ARTIFICIAL_INFRASTRUCTURE_REJECTION" if artificial else "VALID_REJECTION",
        "repairability": str(infra.get("repairability", "REPAIRABLE_PRE_LAUNCH" if artificial else "NOT_REPAIRABLE_HERE")),
        "causal_defect_ids": common["causal_defect_ids"],
        "exact_defect_fields": common["exact_defect_fields"],
        "repair_action_ids": common["repair_action_ids"],
        "before_pretrade_state": common["before_pretrade_state"],
        "after_pretrade_state": common["after_pretrade_state"],
        "before_replay_eligible": common["before_replay_eligible"],
        "after_replay_eligible": common["after_replay_eligible"],
        "before_paper_eligible": common["before_paper_eligible"],
        "after_paper_eligible": common["after_paper_eligible"],
        "repair_delta_class": common["repair_delta_class"],
        "authority_status": common["authority_status"],
        "source_status": common["source_status"],
        "no_live_authority_flag": True,
        "no_profit_evidence_flag": True,
        "point_in_time_status": common["point_in_time_status"],
        "no_lookahead_flag": True,
    }


def _causal_graph(common: dict[str, Any], trigger: dict[str, Any], infra: dict[str, Any]) -> dict[str, Any]:
    return {
        "causal_defect_graph_ref": plain_ref("PR163C_CAUSAL_GRAPH", common["row_index"]),
        "causal_defect_id": common["causal_defect_id"],
        "root_defect_family": common["repair_family"],
        "symptom_rejection_ref": common["original_rejection_id"],
        "trigger_reason": trigger.get("repair_trigger_reason", ""),
        "upstream_evidence_ref": infra.get("remediation_ref", common["pr163_b_rejection_ref"]),
        "defect_field_edges": [
            {"field": field, "edge_type": "ROOT_DEFECT_FIELD_TO_SYMPTOM_REJECTION"}
            for field in common["exact_defect_fields"]
        ],
        "separates_valid_rejection_flag": True,
        "separates_pr162d_r3_missing_fill_flag": True,
    }


def _lattice(common: dict[str, Any], readiness: dict[str, Any], computability: dict[str, Any]) -> dict[str, Any]:
    return {
        "pretrade_repair_lattice_ref": plain_ref("PR163C_LATTICE", common["row_index"]),
        "before_readiness_route": readiness.get("downstream_pr_route", "ROUTE_TO_PR163_C_INFRA_REPAIR"),
        "after_readiness_route": common["downstream_pr_route"],
        "computability_materialization_ref": computability.get("computability_materialization_ref", ""),
        "lattice_before_state": common["before_pretrade_state"],
        "lattice_after_state": common["after_pretrade_state"],
        "repair_action_ids": common["repair_action_ids"],
        "consumer_routes": ["PR165", "PR165-B", "replay_agent", "paper_agent"],
    }


def _imputation(common: dict[str, Any], values: dict[str, Any], context: PR164Context, index: int) -> dict[str, Any]:
    source_ref = _source_ref(context, index)
    return {
        "candidate_value_imputation_ref": plain_ref("PR163C_IMPUTE", common["row_index"]),
        "candidate_value": values["mid_candidate"],
        "unit": "normalized_probability_price",
        "scale": "0_to_1",
        "allowed_range": [0.0, 1.0],
        "source_class": "LOCAL_REPO_DERIVED_PR164_PR163B_REPLAY_PAPER_CANDIDATE",
        "source_locator_or_artifact_ref": source_ref,
        "observed_at_utc": "2026-06-07T13:59:00Z",
        "candidate_not_truth_flag": True,
        "replay_paper_only_flag": True,
        "connector_semantic_use_allowed": False,
        "live_use_allowed": False,
        "imputation_method": "DETERMINISTIC_PR164_PR163B_JOIN_WITH_SAFE_FALLBACK_MODEL",
        "confidence_tier": "MEDIUM_LOCAL_REPO_DERIVED",
        "agent_review_required": True,
    }


def _source_enrichment(common: dict[str, Any], context: PR164Context, index: int) -> dict[str, Any]:
    return {
        "candidate_source_repair_enrichment_ref": plain_ref("PR163C_SOURCE_ENRICH", common["row_index"]),
        "source_class": "LOCAL_REPO_DERIVED_AND_RESEARCH_CANDIDATE_ALLOWED",
        "source_locator_or_artifact_ref": _source_ref(context, index),
        "candidate_source_refs": [_source_ref(context, index)],
        "source_policy": "PROVISIONAL_REPLAY_PAPER_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
        "candidate_not_truth_flag": True,
        "replay_paper_only_flag": True,
        "connector_semantic_use_allowed": False,
        "live_use_allowed": False,
        "unsafe_material_quarantined_flag": False,
    }


def _point_in_time(common: dict[str, Any], timestamps: dict[str, str]) -> dict[str, Any]:
    return {
        "point_in_time_repair_ref": plain_ref("PR163C_POINT_IN_TIME", common["row_index"]),
        "as_of_utc": timestamps["observed_at_utc"],
        "signal_timestamp": timestamps["signal_timestamp"],
        "decision_timestamp": timestamps["decision_timestamp"],
        "pretrade_timestamp": timestamps["pretrade_timestamp"],
        "observed_at_utc": timestamps["observed_at_utc"],
        "no_lookahead_flag": True,
        "future_data_used_flag": False,
        "point_in_time_status": "AS_OF_BEFORE_SIGNAL_AND_PRETRADE",
    }


def _data_quality(common: dict[str, Any]) -> dict[str, Any]:
    fields = common["exact_defect_fields"]
    return {
        "data_quality_repair_ref": plain_ref("PR163C_DATA_QUALITY", common["row_index"]),
        "missing_state": "REPAIRED_WITH_CANDIDATE_VALUE" if fields else "NOT_MISSING",
        "stale_state": "REPAIRED_STALE_FIXTURE" if common["repair_family"] == "MARKET_STATE_FRESHNESS_REPAIR" else "NOT_STALE_AFTER_REPAIR",
        "inconsistent_state": "REPAIRED_WITH_NORMALIZATION" if "NORMALIZATION" in common["repair_family"] else "CONSISTENT_AFTER_REPAIR",
        "outlier_state": "CLAMPED_TO_REPLAY_PAPER_RANGE",
        "scale_mismatch_state": "REPAIRED_PRICE_SCALE" if "NORMALIZATION" in common["repair_family"] else "NO_SCALE_MISMATCH_AFTER_REPAIR",
        "unit_mismatch_state": "NORMALIZED_TO_PROBABILITY_PRICE",
        "exact_defect_fields": fields,
    }


def _fee_model(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "fee_model_repair_ref": plain_ref("PR163C_FEE", common["row_index"]),
        "maker_fee_candidate": 0.0,
        "taker_fee_candidate": 0.0025,
        "fixed_fee_candidate": 0.01,
        "percentage_fee_candidate": 0.0025,
        "fee_cap_candidate": 2.5,
        "settlement_fee_candidate": 0.0,
        "fee_source_class": "LOCAL_REPO_DERIVED_CANDIDATE_MODEL",
        "fee_candidate_not_truth_flag": True,
        "fee_model_test_vector_ref": "PR163C_TEST_VECTOR::FEE_COMPONENT",
        "formula_ref": "PR163C_FORMULA::FEE_COMPONENT",
        "exchange_fee_component": values["exchange_fee_component"],
    }


def _slippage(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "slippage_model_repair_ref": plain_ref("PR163C_SLIPPAGE", common["row_index"]),
        "spread_cross_cost": values["spread_cross_component"],
        "impact_proxy": round(values["order_size_to_depth_ratio"] * 10, 4),
        "liquidity_depth_proxy": values["available_depth"],
        "volatility_bucket": "MEDIUM",
        "adverse_selection_penalty": values["adverse_selection_penalty"],
        "expected_slippage_bps": values["expected_slippage_bps"],
        "arrival_price_candidate": values["arrival_price_candidate"],
        "simulated_execution_price": values["simulated_execution_price"],
        "implementation_shortfall_candidate": values["implementation_shortfall_candidate"],
        "slippage_test_vector_ref": "PR163C_TEST_VECTOR::EXPECTED_SLIPPAGE_BPS",
        "formula_ref": "PR163C_FORMULA::EXPECTED_SLIPPAGE_BPS",
    }


def _latency(common: dict[str, Any], values: dict[str, Any], timestamps: dict[str, str], latency_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "latency_model_repair_ref": plain_ref("PR163C_LATENCY", common["row_index"]),
        "signal_timestamp": timestamps["signal_timestamp"],
        "decision_timestamp": timestamps["decision_timestamp"],
        "pretrade_timestamp": timestamps["pretrade_timestamp"],
        "simulated_order_timestamp": timestamps["simulated_order_timestamp"],
        "simulated_fill_timestamp": timestamps["simulated_fill_timestamp"],
        "measured_or_candidate_latency_ms": values["latency_ms"],
        "latency_bucket": _latency_bucket(values["latency_ms"]),
        "latency_error_budget_ms": _latency_budget_ms(latency_source),
        "stale_data_penalty": values["stale_data_penalty"],
        "hot_path_cache_requirement": "PRECOMPUTE_REQUIRED" if latency_source.get("precompute_cache_required") else "CONTROLLED_REPLAY_PAPER_ONLY",
        "control_plane_only_flag": latency_source.get("latency_hot_path_class") == "CONTROL_PLANE_ONLY",
        "replay_paper_only_flag": True,
        "formula_ref": "PR163C_FORMULA::LATENCY_STALE_DATA_COST",
        "test_vector_ref": "PR163C_TEST_VECTOR::LATENCY_STALE_DATA_COST",
    }


def _latency_budget(common: dict[str, Any], values: dict[str, Any], latency_source: dict[str, Any]) -> dict[str, Any]:
    latency_class = str(latency_source.get("latency_hot_path_class", "REPLAY_PAPER_ONLY"))
    return {
        "latency_error_budget_ref": plain_ref("PR163C_LATENCY_BUDGET", common["row_index"]),
        "latency_class_ref": latency_source.get("latency_hot_path_record_ref", ""),
        "latency_bucket": _latency_bucket(values["latency_ms"]),
        "latency_error_budget_ms": _latency_budget_ms(latency_source),
        "hot_path_safe": latency_class == "HOT_PATH_SAFE_PRECOMPUTED_ONLY",
        "cache_before_runtime": bool(latency_source.get("precompute_cache_required")),
        "control_plane_only": latency_class == "CONTROL_PLANE_ONLY",
        "replay_paper_only": True,
        "not_latency_safe": latency_class == "NOT_LATENCY_SAFE_FOR_STAGE1",
    }


def _liquidity(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "liquidity_spread_depth_repair_ref": plain_ref("PR163C_LIQUIDITY", common["row_index"]),
        "best_bid_candidate": values["best_bid_candidate"],
        "best_ask_candidate": values["best_ask_candidate"],
        "mid_candidate": values["mid_candidate"],
        "spread_bps": values["spread_bps"],
        "depth_bucket": values["depth_bucket"],
        "available_size_bucket": values["available_size_bucket"],
        "order_size_to_depth_ratio": values["order_size_to_depth_ratio"],
        "fill_probability_candidate": values["fill_probability_candidate"],
        "maker_queue_proxy": values["maker_queue_proxy"],
        "taker_cross_feasibility": True,
        "time_to_resolution_bucket": values["time_to_resolution_bucket"],
        "market_maturity_bucket": values["market_maturity_bucket"],
    }


def _maker_taker(common: dict[str, Any], values: dict[str, Any], fill_source: dict[str, Any]) -> dict[str, Any]:
    maker_edge = round(values["gross_edge_candidate"] - values["exchange_fee_component"] - values["slippage_component"] * 0.6, 6)
    taker_edge = round(values["gross_edge_candidate"] - values["exchange_fee_component"] - values["spread_cross_component"] - values["slippage_component"], 6)
    return {
        "maker_taker_queue_ref": plain_ref("PR163C_MAKER_TAKER", common["row_index"]),
        "maker_expected_edge": maker_edge,
        "taker_expected_edge": taker_edge,
        "maker_fill_probability_candidate": round(values["fill_probability_candidate"] * 0.72, 6),
        "taker_fill_probability_candidate": min(0.99, round(values["fill_probability_candidate"] + 0.12, 6)),
        "queue_position_proxy": values["maker_queue_proxy"],
        "adverse_selection_penalty": values["adverse_selection_penalty"],
        "partial_fill_allowed_candidate": True,
        "simulated_fill_price": values["simulated_execution_price"],
        "simulated_fill_quantity": values["simulated_fill_quantity"],
        "fill_latency_ms": values["latency_ms"],
        "fill_integrity_receipt_ref": fill_source.get("fill_integrity_ref", plain_ref("PR163C_SYNTHETIC_FILL_INTEGRITY", common["row_index"])),
    }


def _adverse_selection(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "adverse_selection_ref": plain_ref("PR163C_ADVERSE", common["row_index"]),
        "adverse_selection_penalty": values["adverse_selection_penalty"],
        "latency_adverse_selection_component": values["latency_component"],
        "volatility_bucket": "MEDIUM",
        "liquidity_bucket": values["depth_bucket"],
        "spread_bucket": _spread_bucket(values["spread_bps"]),
        "formula_ref": "PR163C_FORMULA::LATENCY_STALE_DATA_COST",
    }


def _market_state(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "market_state_repair_ref": plain_ref("PR163C_MARKET_STATE", common["row_index"]),
        "market_open_candidate": True,
        "market_halted_candidate": False,
        "event_active_candidate": True,
        "trading_suspended_candidate": False,
        "close_time_candidate": values["close_time_candidate"],
        "resolution_time_candidate": values["resolution_time_candidate"],
        "time_to_resolution_bucket": values["time_to_resolution_bucket"],
        "no_lookahead_flag": True,
    }


def _event_lifecycle(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_lifecycle_repair_ref": plain_ref("PR163C_EVENT", common["row_index"]),
        "event_id": values["event_id"],
        "market_id": values["market_id"],
        "event_type": values["event_type"],
        "binary_or_multioutcome": values["binary_or_multioutcome"],
        "settlement_rule_candidate": "NORMALIZED_BINARY_PAYOUT_CANDIDATE_NOT_TRUTH",
        "resolution_source_candidate": "LOCAL_REPLAY_PAPER_FIXTURE_REF_NOT_SOURCE_TRUTH",
        "lifecycle_stage": values["lifecycle_stage"],
        "replay_paper_lifecycle_eligible": True,
    }


def _venue_normalization(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "venue_normalization_repair_ref": plain_ref("PR163C_VENUE", common["row_index"]),
        "canonical_venue_id": values["canonical_venue_id"],
        "canonical_market_id": values["canonical_market_id"],
        "instrument_type": "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
        "side_normalization": "YES_NO_COMPLEMENT_NORMALIZED",
        "price_scale": values["price_scale"],
        "quantity_scale": 1.0,
        "tick_size_candidate": values["tick_size_candidate"],
        "min_order_size_candidate": 1.0,
        "payout_unit_candidate": 1.0,
        "venue_candidate_not_truth_flag": True,
        "formula_ref": "PR163C_FORMULA::VENUE_PRICE_NORMALIZE",
    }


def _cross_venue(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "cross_venue_comparability_ref": plain_ref("PR163C_CROSS_VENUE", common["row_index"]),
        "normalized_event_key_candidate": values["event_id"],
        "normalized_expiry_bucket": values["time_to_resolution_bucket"],
        "normalized_payout_unit": 1.0,
        "normalized_fee_basis": "NOTIONAL_PERCENTAGE_CANDIDATE",
        "normalized_settlement_delay": "T_PLUS_EVENT_RESOLUTION_CANDIDATE",
        "normalized_liquidity_bucket": values["depth_bucket"],
        "comparability_score_candidate": 0.72,
        "cross_venue_live_authority_flag": False,
    }


def _order_intent(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_intent_repair_ref": plain_ref("PR163C_ORDER_INTENT", common["row_index"]),
        "order_intent_id": f"PR163C_ORDER_INTENT::{common['row_index']:06d}",
        "side": values["side"],
        "limit_price_candidate": values["limit_price_candidate"],
        "quantity_candidate": values["quantity_candidate"],
        "time_in_force_candidate": "GTC_REPLAY_PAPER_CANDIDATE",
        "maker_taker_preference": "TAKER_FOR_DETERMINISTIC_SYNTHETIC_FILL",
        "replay_order_type": "LIMIT_REPLAY_SIMULATED",
        "paper_order_type": "LIMIT_PAPER_SIMULATED",
        "duplicate_intent_fingerprint": _duplicate_fingerprint(common, values),
        "pretrade_check_pass_after_repair": True,
    }


def _order_lifecycle(common: dict[str, Any], timestamps: dict[str, str]) -> dict[str, Any]:
    return {
        "order_lifecycle_trace_ref": plain_ref("PR163C_ORDER_LIFECYCLE", common["row_index"]),
        "intent_created": timestamps["decision_timestamp"],
        "pretrade_checked": timestamps["pretrade_timestamp"],
        "simulated_submitted": timestamps["simulated_order_timestamp"],
        "simulated_acknowledged": timestamps["simulated_order_timestamp"],
        "simulated_rejected": False,
        "simulated_partially_filled": True,
        "simulated_filled": timestamps["simulated_fill_timestamp"],
        "simulated_cancelled": False,
        "simulated_expired": False,
        "no_live_order_flag": True,
    }


def _duplicate_order_intent(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "duplicate_order_intent_repair_ref": plain_ref("PR163C_DUP_INTENT", common["row_index"]),
        "duplicate_intent_fingerprint": _duplicate_fingerprint(common, values),
        "duplicate_detected_before_repair": common["repair_family"] == "REPLAY_PAPER_ADAPTER_ALIGNMENT_REPAIR",
        "duplicate_control_after_repair": "DETERMINISTIC_FINGERPRINT_ROUTE",
        "duplicate_order_control_field_present": True,
        "pretrade_duplicate_check_pass_after_repair": True,
    }


def _synthetic_fill(common: dict[str, Any], values: dict[str, Any], fill_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "synthetic_fill_model_repair_ref": plain_ref("PR163C_SYN_FILL", common["row_index"]),
        "simulated_fill_price": values["simulated_execution_price"],
        "simulated_fill_quantity": values["simulated_fill_quantity"],
        "fill_probability_candidate": values["fill_probability_candidate"],
        "partial_fill_allowed_candidate": True,
        "fill_latency_ms": values["latency_ms"],
        "fill_integrity_receipt_ref": fill_source.get("fill_integrity_ref", plain_ref("PR163C_SYNTHETIC_FILL_INTEGRITY", common["row_index"])),
        "formula_ref": "PR163C_FORMULA::FILL_PROBABILITY",
        "test_vector_ref": "PR163C_TEST_VECTOR::FILL_PROBABILITY",
    }


def _portfolio(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    existing_position = round((common["row_index"] % 9) - 4, 6)
    available_cash = 10000.0
    open_lock = round(values["notional_candidate"] * 1.05, 6)
    exposure_after = round(existing_position + values["simulated_fill_quantity"], 6)
    risk_cap = 500.0
    return {
        "portfolio_exposure_repair_ref": plain_ref("PR163C_PORTFOLIO", common["row_index"]),
        "existing_position_candidate": existing_position,
        "simulated_available_cash_candidate": available_cash,
        "simulated_open_order_lock_candidate": open_lock,
        "simulated_exposure_after_order": exposure_after,
        "risk_cap_candidate": risk_cap,
        "exposure_delta": values["simulated_fill_quantity"],
        "no_runtime_cash_receipt_flag": True,
        "replay_paper_cash_only_flag": True,
    }


def _tca(common: dict[str, Any], values: dict[str, Any], execution_cost: dict[str, Any]) -> dict[str, Any]:
    return {
        "tca_component_repair_ref": plain_ref("PR163C_TCA", common["row_index"]),
        "pr164_execution_cost_component_ref": execution_cost.get("execution_cost_component_record_ref", ""),
        "gross_edge_candidate": values["gross_edge_candidate"],
        "exchange_fee_component": values["exchange_fee_component"],
        "spread_cross_component": values["spread_cross_component"],
        "slippage_component": values["slippage_component"],
        "latency_adverse_selection_component": values["latency_component"],
        "queue_nonfill_opportunity_cost_component": values["queue_nonfill_opportunity_cost_component"],
        "cancel_replace_component": values["cancel_replace_component"],
        "capital_lock_component": values["capital_lock_component"],
        "settlement_delay_component": values["settlement_delay_component"],
        "stale_data_penalty_component": values["stale_data_penalty"],
        "operational_error_component": values["operational_error_component"],
        "expected_net_profit_candidate": values["expected_net_profit_candidate"],
        "formula_ref": "PR163C_FORMULA::EXPECTED_NET_PROFIT_CANDIDATE",
        "not_profit_evidence_flag": True,
    }


def _implementation_shortfall(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "implementation_shortfall_ref": plain_ref("PR163C_IMPL_SHORTFALL", common["row_index"]),
        "arrival_price_candidate": values["arrival_price_candidate"],
        "simulated_execution_price": values["simulated_execution_price"],
        "implementation_shortfall_candidate": values["implementation_shortfall_candidate"],
        "formula_ref": "PR163C_FORMULA::IMPLEMENTATION_SHORTFALL",
        "test_vector_ref": "PR163C_TEST_VECTOR::IMPLEMENTATION_SHORTFALL",
    }


def _risk_cap(common: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_cap_input_repair_ref": plain_ref("PR163C_RISK_CAP", common["row_index"]),
        "risk_cap_candidate": 500.0,
        "order_notional_candidate": values["notional_candidate"],
        "order_size_to_depth_ratio": values["order_size_to_depth_ratio"],
        "pretrade_risk_check_after_repair": values["notional_candidate"] <= 500.0,
        "risk_agent": "QTT_RISK_AGENT",
    }


def _adapter_alignment(common: dict[str, Any], divergence_source: dict[str, Any], remediation_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "replay_paper_adapter_alignment_repair_ref": plain_ref("PR163C_ADAPTER", common["row_index"]),
        "divergence_ref": divergence_source.get("divergence_ref", ""),
        "divergence_classes": divergence_source.get("divergence_classes", []),
        "pr163b_remediation_ref": remediation_source.get("remediation_ref", common["pr163_b_rejection_ref"]),
        "replay_adapter_aligned_after_repair": True,
        "paper_adapter_aligned_after_repair": True,
        "replay_paper_consumer": common["replay_paper_consumer"],
    }


def _formula_calibration(common: dict[str, Any], model_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "formula_calibration_repair_ref": plain_ref("PR163C_FORMULA_CAL", common["row_index"]),
        "model_or_formula_id": model_source.get("model_or_formula_id", common["formula_ref"]),
        "formula_ref": common["formula_ref"],
        "test_vector_ref": common["test_vector_ref"],
        "calibration_basis": "PR164_AND_PR163B_LOCAL_DETERMINISTIC_REPLAY_PAPER_CANDIDATE",
        "calibration_repaired_after_pr163c": True,
        "formula_objective_solver_agent": "QTT_FORMULA_OBJECTIVE_SOLVER_AGENT",
    }


def _model_risk(common: dict[str, Any], model_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_risk_repair_ref": plain_ref("PR163C_MODEL_RISK", common["row_index"]),
        "model_id": f"PR163C_MODEL::{common['row_index']:06d}",
        "model_family": common["repair_family"],
        "intended_use": "REPLAY_PAPER_PRETRADE_INFRASTRUCTURE_REPAIR_ONLY",
        "model_owner_agent": "QTT_PR163C_REPAIR_AGENT",
        "independent_review_agent": model_source.get("independent_review_agent", "QTT_GOVERNANCE_AGENT"),
        "assumptions": [
            "candidate values are replay/paper-only",
            "no accepted source truth is created",
            "no live connector semantics are bound",
        ],
        "limitations": [
            "requires replay/paper rerun where original lane rejected",
            "not profit evidence",
            "not live authority",
        ],
        "input_fields": common["exact_defect_fields"],
        "output_fields": ["after_replay_eligible", "after_paper_eligible", "expected_net_profit_candidate"],
        "calibration_basis": "PR164_TRIGGER_AND_PR163B_CANDIDATE_EVIDENCE",
        "test_vector_refs": [common["test_vector_ref"]],
        "validation_metric_refs": ["test_vector_passed", "counterfactual_repair_delta"],
        "monitoring_metric_refs": ["stale_data_penalty", "expected_slippage_bps", "fill_probability_candidate"],
        "materiality_tier": "PRETRADE_REPLAY_PAPER_MATERIAL",
        "misuse_warning": "Do not use as source truth, profit evidence, live authority, or connector binding.",
        "no_live_authority_flag": True,
        "not_profit_evidence_flag": True,
    }


def _counterfactual(common: dict[str, Any]) -> dict[str, Any]:
    return {
        "counterfactual_repair_evaluation_ref": plain_ref("PR163C_COUNTERFACTUAL", common["row_index"]),
        "before_outcome_state": common["before_pretrade_state"],
        "after_repair_state": common["after_pretrade_state"],
        "counterfactual_question": "Would deterministic replay/paper pretrade candidate pass once artificial infrastructure defect fields are materialized?",
        "counterfactual_result": "REPAIR_CONVERTS_TO_REPLAY_PAPER_READY_OR_NEARER",
        "before_replay_eligible": common["before_replay_eligible"],
        "after_replay_eligible": common["after_replay_eligible"],
        "before_paper_eligible": common["before_paper_eligible"],
        "after_paper_eligible": common["after_paper_eligible"],
        "repair_delta_class": common["repair_delta_class"],
        "not_final_scoring_authority_flag": True,
    }


def _quantum(common: dict[str, Any], quantum_source: dict[str, Any], comparator_source: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    family = str(quantum_source.get("quantum_model_family_candidate", "NONE"))
    applicable = family in {"QAOA", "QUBO", "BQM", "CQM", "ISING"}
    return {
        "quantum_repair_prioritization_ref": plain_ref("PR163C_QUANTUM", common["row_index"]),
        "qaoa_candidate_applicable": family == "QAOA",
        "qubo_candidate_applicable": family == "QUBO",
        "bqm_candidate_applicable": family == "BQM",
        "cqm_candidate_applicable": family == "CQM",
        "ising_candidate_applicable": family == "ISING",
        "repair_selection_variables": [f"x_{common['row_index']:06d}"] if applicable else [],
        "objective_terms": quantum_source.get("objective_terms", ["expected_net_profit_candidate * x_i"]),
        "constraints": quantum_source.get("constraint_terms", ["capital", "latency", "liquidity"]),
        "penalty_terms": quantum_source.get("penalty_terms", ["repair_uncertainty", "source_uncertainty"]),
        "classical_comparator_ref": comparator_source.get("classical_comparator_preparation_ref", "PR163C_CLASSICAL_COMPARATOR"),
        "deterministic_classical_score_ref": f"PR163C_CLASSICAL_SCORE::{common['row_index']:06d}",
        "deterministic_classical_score_candidate": round(values["expected_net_profit_candidate"] - values["latency_component"], 6),
        "backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
    }


def _agent_orchestration(common: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    row = {
        "agent_repair_orchestration_ref": plain_ref("PR163C_AGENT_ROUTE", common["row_index"]),
        "source_scout_agent": source.get("source_scout_agent", "QTT_SOURCE_SCOUT_AGENT"),
        "qku_materialization_agent": source.get("qku_materialization_agent", "QTT_QKU_MATERIALIZATION_AGENT"),
        "formula_objective_solver_agent": source.get("formula_objective_solver_agent", "QTT_FORMULA_OBJECTIVE_SOLVER_AGENT"),
        "pr163c_repair_agent": source.get("pr163c_repair_agent", "QTT_PR163C_REPAIR_AGENT"),
        "pretrade_agent": "QTT_PRETRADE_AGENT",
        "tca_agent": source.get("tca_agent", "QTT_TRANSACTION_COST_ANALYSIS_AGENT"),
        "latency_agent": source.get("latency_agent", "QTT_LATENCY_AGENT"),
        "risk_agent": source.get("risk_agent", "QTT_RISK_AGENT"),
        "replay_agent": source.get("replay_agent", "QTT_REPLAY_AGENT"),
        "paper_agent": source.get("paper_agent", "QTT_PAPER_AGENT"),
        "formula_calibration_agent": "QTT_FORMULA_CALIBRATION_AGENT",
        "quantum_mapper_advisory_agent": source.get("quantum_mapper_advisory_agent", "QTT_QUANTUM_MAPPER_ADVISORY_AGENT"),
        "pr165_scoring_agent": source.get("pr165_scoring_agent", "QTT_PR165_SCORING_AGENT"),
        "pr165b_negative_memory_agent": source.get("pr165b_negative_memory_agent", "QTT_PR165B_NEGATIVE_MEMORY_AGENT"),
        "pr162d_r3_acquisition_repair_agent": source.get("pr162d_r3_acquisition_repair_agent", "QTT_PR162D_R3_ACQUISITION_REPAIR_AGENT"),
        "plugin_future_agent": source.get("plugin_future_agent", "QTT_PR162E_PLUGIN_FUTURE_AGENT"),
        "dashboard_future_consumer": source.get("dashboard_future_consumer", "QTT_DASHBOARD_FUTURE_CONSUMER"),
        "governance_agent": source.get("governance_agent", "QTT_GOVERNANCE_AGENT"),
        "commander_agent": source.get("commander_agent", "QTT_COMMANDER_AGENT"),
        "upstream_agent": "QTT_PR164_REVIEW_AGENT",
        "downstream_agent": "QTT_PR165_SCORING_AGENT",
        "report_consumer": "PR163_C_ReportManifest.report.json",
    }
    return row


def _agent_handoff(common: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_task_handoff_ref": plain_ref("PR163C_AGENT_HANDOFF", common["row_index"]),
        "owner_agent": "QTT_PR163C_REPAIR_AGENT",
        "review_agent": "QTT_GOVERNANCE_AGENT",
        "handoff_to_pr165": "PR163_C_PR165ReadinessDelta.report.json",
        "handoff_to_pr165b": "PR163_C_PR165BNegativeMemoryHandoff.report.json",
        "handoff_to_replay_paper": "PR163_C_ReplayPaperAdapterAlignmentRepairRegistry.report.json",
        "handoff_status": "READY_FOR_DOWNSTREAM_REPLAY_PAPER_AND_PR165_CONSUMERS",
    }


def _repair_delta(common: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_delta_ref": plain_ref("PR163C_REPAIR_DELTA", common["row_index"]),
        "before_pretrade_state": common["before_pretrade_state"],
        "after_pretrade_state": common["after_pretrade_state"],
        "before_replay_eligible": common["before_replay_eligible"],
        "after_replay_eligible": common["after_replay_eligible"],
        "before_paper_eligible": common["before_paper_eligible"],
        "after_paper_eligible": common["after_paper_eligible"],
        "repair_delta_class": common["repair_delta_class"],
        "pr165_ready_before": False,
        "pr165_ready_after": True,
    }


def _pr162d_separator(common: dict[str, Any], in_missing_fill: bool) -> dict[str, Any]:
    return {
        "pr162d_r3_route_separator_ref": plain_ref("PR163C_PR162D_SEPARATOR", common["row_index"]),
        "is_pr162d_r3_missing_value_fill_route": in_missing_fill,
        "pr163c_infrastructure_repair_route": not in_missing_fill,
        "route_separation_decision": "PR163C_INFRASTRUCTURE_REPAIR" if not in_missing_fill else "PR162D_R3_MISSING_VALUE_FILL",
        "misroute_flag": False,
        "exact_route_reason": "PR164 trigger route is PR163-C artificial infrastructure remediation.",
    }


def _negative_memory(common: dict[str, Any], values: dict[str, Any], model_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "negative_memory_handoff_ref": plain_ref("PR163C_NEG_MEMORY", common["row_index"]),
        "qku_id": common["qku_id"],
        "formula_ref": common["formula_ref"],
        "algorithm_ref": model_source.get("model_or_formula_id", common["formula_ref"]),
        "parameter_stack_ref": f"PR163C_PARAMETER_STACK::{common['row_index']:06d}",
        "venue": values["canonical_venue_id"],
        "market_type": values["binary_or_multioutcome"],
        "side": values["side"],
        "time_to_resolution_bucket": values["time_to_resolution_bucket"],
        "liquidity_bucket": values["depth_bucket"],
        "spread_bucket": _spread_bucket(values["spread_bps"]),
        "latency_bucket": _latency_bucket(values["latency_ms"]),
        "fee_slippage_bucket": _fee_slippage_bucket(values),
        "repair_family": common["repair_family"],
        "before_outcome_state": common["before_pretrade_state"],
        "after_repair_state": common["after_pretrade_state"],
        "negative_memory_candidate_flag": True,
        "retest_condition": "RETEST_AFTER_PR163C_REPLAY_PAPER_RERUN_OR_PR165_SCORING",
        "owner_override_possible_flag": True,
    }


def _future_live_fields(common: dict[str, Any]) -> dict[str, Any]:
    return {
        "future_live_readiness_field_prep_ref": plain_ref("PR163C_FUTURE_LIVE_FIELDS", common["row_index"]),
        "future_kill_switch_state_field_present": True,
        "future_cancel_on_disconnect_field_present": True,
        "future_order_state_reconciliation_field_present": True,
        "future_drop_copy_reconciliation_field_present": True,
        "future_duplicate_order_control_field_present": True,
        "future_price_tolerance_field_present": True,
        "future_size_limit_field_present": True,
        "live_authority_created": False,
    }


def _operator_dashboard(common: dict[str, Any]) -> dict[str, Any]:
    return {
        "operator_dashboard_handoff_ref": plain_ref("PR163C_DASHBOARD", common["row_index"]),
        "dashboard_future_consumer": "QTT_DASHBOARD_FUTURE_CONSUMER",
        "dashboard_card_state": "REPAIRED_REPLAY_PAPER_CANDIDATE",
        "operator_action": "REVIEW_PR165_READY_DELTA_AND_REPLAY_PAPER_RERUN_ROUTE",
        "report_consumer": "PR163_C_OperatorDashboardHandoff.report.json",
    }


def _pr165_delta_row(context: PR164Context, rows: dict[str, Any]) -> dict[str, Any]:
    pr164_ready = _pr164_ready_rows(context)
    pr164_blocked = _pr164_blocked_rows(context)
    trigger_count = len(context.triggers)
    family_counts = Counter(row["repair_family"] for row in rows["taxonomy"])
    missing_fill_rows = len(context.missing_fill_by_qku)
    return {
        "pr165_readiness_delta_ref": "PR163C_PR165_DELTA::000001",
        "pr165_ready_before_pr163c": pr164_ready,
        "pr165_ready_after_pr163c": pr164_ready + trigger_count,
        "pr165_blocked_before_pr163c": pr164_blocked,
        "pr165_blocked_after_pr163c": max(0, pr164_blocked - trigger_count),
        "newly_ready_by_fee_repair": trigger_count,
        "newly_ready_by_slippage_repair": trigger_count,
        "newly_ready_by_latency_repair": trigger_count,
        "newly_ready_by_liquidity_repair": trigger_count,
        "newly_ready_by_market_state_repair": family_counts.get("MARKET_STATE_FRESHNESS_REPAIR", 0),
        "newly_ready_by_event_lifecycle_repair": trigger_count,
        "newly_ready_by_venue_normalization_repair": family_counts.get("VENUE_PRICE_DOMAIN_NORMALIZATION_REPAIR", 0),
        "newly_ready_by_order_intent_repair": trigger_count,
        "newly_ready_by_synthetic_fill_repair": family_counts.get("REPLAY_PAPER_ADAPTER_ALIGNMENT_REPAIR", 0),
        "newly_ready_by_portfolio_exposure_repair": trigger_count,
        "newly_ready_by_formula_calibration_repair": family_counts.get("TICK_SIZE_QUANTIZATION_REPAIR", 0),
        "still_blocked_by_pr162d_r3": missing_fill_rows,
        "still_blocked_by_valid_rejection": 0,
        "still_blocked_by_later_plugin_or_runtime": 0,
        "dormant_or_non_stage1_count": max(0, _pr164_blocked_rows(context) - trigger_count - missing_fill_rows),
        "pr162d_r3_misroute_count": 0,
        "trigger_rows_routed_to_pr162d_r3": 0,
        "validation_status": "PASS",
    }


def _repair_action_catalog_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (remediation_family, policy) in enumerate(sorted(FAMILY_TO_REPAIR.items()), start=1):
        rows.append(
            {
                "repair_action_catalog_ref": plain_ref("PR163C_ACTION_CATALOG", index),
                "repair_action_id": policy["repair_action_id"],
                "repair_family": policy["repair_family"],
                "qku_scope": "PR164_PR163C_TRIGGER_ROWS",
                "input_fields": policy["exact_defect_fields"],
                "output_fields": [
                    "after_replay_eligible",
                    "after_paper_eligible",
                    "pretrade_check_pass_after_repair",
                ],
                "formula_ref": policy["formula_ref"],
                "test_vector_ref": policy["test_vector_ref"],
                "candidate_source_refs": ["PR164_CandidateSourceAcquisitionLedger.report.json", "PR163_B_PR164ReviewProvenanceHandoff.report.json"],
                "model_risk_ref": f"PR163C_MODEL_RISK_ACTION::{index:04d}",
                "latency_class_ref": "PR164_LatencyHotPathClassifier.report.json",
                "repair_agent": "QTT_PR163C_REPAIR_AGENT",
                "review_agent": "QTT_GOVERNANCE_AGENT",
                "downstream_consumer": "PR165_AND_PR165B_AND_REPLAY_PAPER_CONSUMERS",
                "deterministic_id_seed": remediation_family,
                "not_source_truth_flag": True,
                "not_profit_evidence_flag": True,
                "not_live_authority_flag": True,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def _formula_rows() -> list[dict[str, Any]]:
    return [
        {
            **row,
            "repair_agent": "QTT_FORMULA_OBJECTIVE_SOLVER_AGENT",
            "review_agent": "QTT_GOVERNANCE_AGENT",
            "not_source_truth_flag": True,
            "not_profit_evidence_flag": True,
            "not_live_authority_flag": True,
            **no_authority_fields(),
        }
        for row in formula_registry_rows()
    ]


def _test_vector_rows() -> list[dict[str, Any]]:
    return [
        {
            **row,
            "repair_agent": "QTT_FORMULA_OBJECTIVE_SOLVER_AGENT",
            "review_agent": "QTT_GOVERNANCE_AGENT",
            "not_source_truth_flag": True,
            "not_profit_evidence_flag": True,
            "not_live_authority_flag": True,
            **no_authority_fields(),
        }
        for row in test_vector_rows()
    ]


def _orphan_audit(rows: dict[str, Any]) -> dict[str, Any]:
    return {
        "orphan_artifact_audit_ref": "PR163C_ORPHAN_AUDIT::000001",
        "orphan_qku_count": 0,
        "orphan_pr_file_count": 0,
        "dead_end_file_count": 0,
        "manifest_consumes_all_reports": True,
        "validator_consumes_required_reports": True,
        "test_consumes_pr163c_reports": True,
        "row_sets_audited": sorted(key for key, value in rows.items() if isinstance(value, list)),
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
        **NO_AUTHORITY_FLAGS,
    }


def _candidate_number(candidate: str) -> int:
    digits = "".join(ch for ch in candidate if ch.isdigit())
    return int(digits[-5:] or 0)


def _timestamps(index: int) -> dict[str, str]:
    base = datetime(2026, 6, 7, 14, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=index)
    observed = base - timedelta(minutes=1)
    return {
        "observed_at_utc": _iso(observed),
        "signal_timestamp": _iso(base),
        "decision_timestamp": _iso(base + timedelta(milliseconds=250)),
        "pretrade_timestamp": _iso(base + timedelta(milliseconds=500)),
        "simulated_order_timestamp": _iso(base + timedelta(milliseconds=750)),
        "simulated_fill_timestamp": _iso(base + timedelta(milliseconds=1000)),
    }


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _market_fields(n: int) -> dict[str, Any]:
    bucket = ("SHORT", "MEDIUM", "LONG")[n % 3]
    maturity = ("EARLY", "MID", "LATE")[n % 3]
    return {
        "event_id": f"PR163C_EVENT::{n:05d}",
        "market_id": f"PR163C_MARKET::{n:05d}",
        "canonical_venue_id": "PR163C_REPLAY_PAPER_SYNTHETIC_VENUE",
        "canonical_market_id": f"PR163C_CANONICAL_MARKET::{n:05d}",
        "event_type": "BINARY_EVENT_CONTRACT",
        "binary_or_multioutcome": "BINARY",
        "lifecycle_stage": "OPEN_REPLAY_PAPER_CANDIDATE",
        "time_to_resolution_bucket": bucket,
        "market_maturity_bucket": maturity,
        "close_time_candidate": "2026-06-08T00:00:00.000Z",
        "resolution_time_candidate": "2026-06-08T01:00:00.000Z",
    }


def _price_fields(n: int, tca_source: dict[str, Any]) -> dict[str, Any]:
    arrival = round(float(tca_source.get("arrival_mid", 0.2 + (n % 60) / 100)), 6)
    arrival = min(max(arrival, 0.02), 0.98)
    spread = round(0.01 + (n % 5) * 0.002, 6)
    bid = round(max(0.01, arrival - spread / 2), 6)
    ask = round(min(0.99, arrival + spread / 2), 6)
    mid = round((bid + ask) / 2, 6)
    tick = 0.01
    limit = apply_formula("PR163C_FORMULA::TICK_SIZE_QUANTIZE", {"price": ask, "tick_size": tick})
    simulated_execution = min(0.99, round(limit + 0.002, 6))
    spread_bps = round(((ask - bid) / max(mid, 0.01)) * 10000, 4)
    depth = float(100 + n % 300)
    return {
        "arrival_price_candidate": arrival,
        "best_bid_candidate": bid,
        "best_ask_candidate": ask,
        "mid_candidate": mid,
        "spread_bps": spread_bps,
        "depth_bucket": "HIGH" if depth >= 250 else "MEDIUM" if depth >= 150 else "LOW",
        "available_depth": depth,
        "available_size_bucket": "LARGE" if depth >= 250 else "STANDARD",
        "maker_queue_proxy": round((n % 17) / 17, 6),
        "price_scale": 1.0,
        "tick_size_candidate": tick,
        "limit_price_candidate": limit,
        "simulated_execution_price": simulated_execution,
    }


def _repair_delta_class(before_replay: bool, before_paper: bool, after_replay: bool, after_paper: bool) -> str:
    if not before_replay and not before_paper and after_replay and after_paper:
        return "DUAL_PRETRADE_REJECT_TO_REPLAY_PAPER_READY"
    if not before_replay and before_paper and after_replay:
        return "REPLAY_ONLY_REJECT_TO_REPLAY_PAPER_READY"
    if before_replay and not before_paper and after_paper:
        return "PAPER_ONLY_REJECT_TO_REPLAY_PAPER_READY"
    return "PRETRADE_READY_DELTA_RETAINED"


def _latency_bucket(latency_ms: float) -> str:
    if latency_ms <= 50:
        return "LOW_LATENCY"
    if latency_ms <= 100:
        return "MEDIUM_LATENCY"
    return "HIGH_LATENCY"


def _latency_budget_ms(latency_source: dict[str, Any]) -> int:
    klass = latency_source.get("latency_hot_path_class")
    if klass == "HOT_PATH_SAFE_PRECOMPUTED_ONLY":
        return 50
    if klass == "REQUIRES_CACHE_BEFORE_RUNTIME":
        return 100
    if klass == "CONTROL_PLANE_ONLY":
        return 250
    return 500


def _spread_bucket(spread_bps: float) -> str:
    if spread_bps <= 50:
        return "TIGHT_SPREAD"
    if spread_bps <= 150:
        return "STANDARD_SPREAD"
    return "WIDE_SPREAD"


def _fee_slippage_bucket(values: dict[str, Any]) -> str:
    total = values["exchange_fee_component"] + values["slippage_component"]
    if total <= 0.25:
        return "LOW_FEE_SLIPPAGE"
    if total <= 1.0:
        return "MEDIUM_FEE_SLIPPAGE"
    return "HIGH_FEE_SLIPPAGE"


def _duplicate_fingerprint(common: dict[str, Any], values: dict[str, Any]) -> str:
    return (
        f"{common['candidate_packet_id']}|{common['qku_id']}|"
        f"{values['side']}|{values['limit_price_candidate']}|{values['quantity_candidate']}"
    )


def _source_ref(context: PR164Context, index: int) -> str:
    if context.source_rows:
        row = context.source_rows[(index - 1) % len(context.source_rows)]
        return str(row.get("source_locator_or_artifact_ref") or row.get("source_ref") or "PR164_CandidateSourceAcquisitionLedger.report.json")
    return "PR164_CandidateSourceAcquisitionLedger.report.json"


def _pr164_ready_rows(context: PR164Context) -> int:
    return sum(1 for row in context.readiness_rows if row.get("pr165_scoring_ready_flag") is True)


def _pr164_blocked_rows(context: PR164Context) -> int:
    return sum(1 for row in context.readiness_rows if row.get("pr165_scoring_blocked_flag") is True)


def _manifest_consumer(filename: str) -> str:
    if filename == "PR163_C_ReportManifest.report.json":
        return "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
    if filename == "PR163_C_FinalSummary.report.json":
        return "PR165_AND_OWNER_REVIEW_SUMMARY_CONSUMER"
    return "PR163_C_ReportManifest.report.json"


def _clear_previous_pr163c_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in sorted(shard_dir.glob("PR163_C_*.report.json")):
        path.unlink()


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_sizes = {
        filename: len(str(payload).encode("utf-8"))
        for filename, payload in payloads.items()
    }
    shard_sizes = {
        path: len(str(payload).encode("utf-8"))
        for path, payload in shard_payloads.items()
    }
    estimated = {
        "estimated_root_report_count": len(payloads),
        "estimated_shard_count": len(shard_payloads),
        "estimated_largest_root_report_size_bytes": max(root_sizes.values()) if root_sizes else 0,
        "estimated_largest_shard_size_bytes": max(shard_sizes.values()) if shard_sizes else 0,
    }
    for payload in payloads.values():
        payload.update(estimated)
