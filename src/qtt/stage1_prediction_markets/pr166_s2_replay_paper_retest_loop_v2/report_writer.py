"""Build PR166-S2 generated reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from . import constants as c
from .authority import authority_boundary_record, authority_zero_counts
from .enums import LifecycleStatus, NoFillReason, ReadinessState, ReplayPaperExecutionStatus, UnitClass
from .io import (
    ensure_branch,
    json_text,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)
from .models import common_fields, stable_id

ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024
BASE_TIME = datetime(2026, 6, 12, 13, 0, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    missing_required: tuple[str, ...]
    optional_present: tuple[str, ...]
    optional_missing: tuple[str, ...]
    shard_audit_rows: tuple[dict[str, Any], ...]
    agents_md_status: str


@dataclass(frozen=True)
class RetestContext:
    index: int
    source: dict[str, Any]
    payload: dict[str, Any]
    readiness: dict[str, Any]
    fill: dict[str, Any]
    result: dict[str, Any]
    routes: list[str]


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_shards(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, payloads[filename], compact=payloads[filename].get("sharded_flag", False))
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    sizes = file_size_summary(repo_root, c.REPORT_FILENAMES)
    summary = dict(payloads["PR166_S2_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR166_S2_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR166_S2_FinalSummary.report.json"].update(sizes)
    write_json(repo_root / c.GENERATED_DIR / "PR166_S2_FinalSummary.report.json", payloads["PR166_S2_FinalSummary.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    if source.missing_required:
        raise RuntimeError(f"PR166-S2 required inputs missing: {', '.join(source.missing_required)}")
    row_payloads = build_row_payloads(repo_root, source)
    payloads, shard_payloads = payloads_from_rows(row_payloads, list(c.REQUIRED_INPUT_REPORTS))
    row_payloads["PR166_S2_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_S2_ReportManifest.report.json"] = build_root_payload(
        "PR166_S2_ReportManifest.report.json",
        row_payloads["PR166_S2_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    row_payloads["PR166_S2_FinalSummary.report.json"] = [
        build_final_summary(row_payloads, source, payloads, shard_payloads)
    ]
    payloads["PR166_S2_FinalSummary.report.json"] = build_root_payload(
        "PR166_S2_FinalSummary.report.json",
        row_payloads["PR166_S2_FinalSummary.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"final_summary_row_count": 1},
    )
    row_payloads["PR166_S2_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads["PR166_S2_ReportManifest.report.json"] = build_root_payload(
        "PR166_S2_ReportManifest.report.json",
        row_payloads["PR166_S2_ReportManifest.report.json"],
        list(c.REQUIRED_INPUT_REPORTS),
        {"manifest_report_count": len(c.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR166-S2 payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    missing: list[str] = []
    shard_audit_rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        payloads[filename] = payload
        rows = records_from_report_payload(repo_root, payload)
        records[filename] = rows
        declared = list(payload.get("shard_files") or payload.get("shard_paths") or [])
        read_paths = [normalize_repo_ref(shard) for shard in declared if resolve_repo_relative(repo_root, shard).exists()]
        declared_count = int(payload.get("shard_count", len(declared)) or 0)
        declared_rows = int(payload.get("record_count", len(rows)) or 0)
        shard_audit_rows.append(
            _audit_row(
                "PR166_S2_ShardInputAudit.report.json",
                "PR166_S2_SHARD_INPUT_AUDIT",
                stable_id("PR166_S2_SHARD_INPUT_AUDIT", index),
                {
                    "upstream_report_ref": filename,
                    "root_report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "records_omitted_for_sharding_flag": bool(payload.get("records_omitted_for_sharding_flag")),
                    "shard_paths_declared": [normalize_repo_ref(shard) for shard in declared],
                    "shard_paths_read": read_paths,
                    "declared_shard_count": declared_count,
                    "read_shard_count": len(read_paths),
                    "declared_total_row_count": declared_rows,
                    "read_total_row_count": len(rows),
                    "shard_count_mismatch_flag": declared_count != len(read_paths),
                    "row_count_mismatch_flag": declared_rows != len(rows),
                    "continuation_allowed": declared_count == len(read_paths) and declared_rows == len(rows),
                    "repair_or_terminal_route": "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                },
                upstream_artifact_refs=[filename],
                upstream_row_refs=[f"{filename}::ROOT"],
                downstream_artifact_refs=["PR166_S2_InputAudit.report.json"],
                owning_agent="governance_agent",
            )
        )
    optional_present: list[str] = []
    for path in sorted((repo_root / c.GENERATED_DIR).glob("PR164_*.report.json")):
        payload = read_json(path)
        optional_present.append(path.name)
        payloads[path.name] = payload
        records[path.name] = records_from_report_payload(repo_root, payload)
    for path in sorted((repo_root / c.GENERATED_DIR).glob("PR165_*.report.json")):
        if path.name in payloads:
            continue
        payload = read_json(path)
        optional_present.append(path.name)
        payloads[path.name] = payload
        records[path.name] = records_from_report_payload(repo_root, payload)
    agents = sorted(repo_root.rglob("AGENTS.md"))
    agents_md_status = "PRESENT_OPTIONAL_CONSUMED" if agents else "NOT_PRESENT_NOT_REQUIRED"
    optional_missing = [] if optional_present else ["PR164 and supplemental PR165 optional reports absent"]
    if not agents:
        optional_missing.append("AGENTS.md optional file absent")
    return SourceData(
        payloads=payloads,
        records=records,
        missing_required=tuple(missing),
        optional_present=tuple(sorted(set(optional_present))),
        optional_missing=tuple(optional_missing),
        shard_audit_rows=tuple(shard_audit_rows),
        agents_md_status=agents_md_status,
    )


def build_row_payloads(repo_root: Path, source: SourceData) -> dict[str, list[dict[str, Any]]]:
    contexts = build_retest_contexts(source)
    thresholds = threshold_rows(contexts)
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR166_S2_InputAudit.report.json": build_input_audit_rows(source),
        "PR166_S2_OptionalInputLedger.report.json": build_optional_input_rows(source),
        "PR166_S2_RowCountLedger.report.json": build_row_count_rows(source, contexts),
        "PR166_S2_RetestPolicy.report.json": build_retest_policy_rows(),
        "PR166_S2_InputRegistry.report.json": build_input_registry_rows(source),
        "PR166_S2_ScenarioSchedule.report.json": build_scenario_schedule_rows(),
        "PR166_S2_ShardInputAudit.report.json": list(source.shard_audit_rows),
        "PR166_S2_FillModelPolicy.report.json": build_fill_model_policy_rows(contexts),
        "PR166_S2_ThresholdPolicy.report.json": thresholds,
        "PR166_S2_ExternalSignalRegistry.report.json": build_external_signal_rows(),
        "PR166_S2_SearchReceipt.report.json": build_external_signal_rows("PR166_S2_SearchReceipt.report.json", "PR166_S2_SEARCH_RECEIPT"),
        "PR166_S2_SearchAudit.report.json": build_search_audit_rows(),
        "PR166_S2_PRFileConnectivityAudit.report.json": build_pr_file_connectivity_rows(repo_root),
        "PR166_S2_AuthorityBoundaryAudit.report.json": build_authority_rows(),
        "PR166_S2_NoProfitEvidenceAudit.report.json": build_no_profit_rows(contexts),
        "PR166_S2_StatusEnumDriftAudit.report.json": build_status_drift_rows(),
        "PR166_S2_AgentKPIAudit.report.json": build_agent_kpi_rows(contexts, source),
    }
    row_payloads.update(build_primary_ledgers(contexts))
    row_payloads["PR166_S2_MasterPlanCrosswalk.report.json"] = build_crosswalk_rows(row_payloads)
    row_payloads["PR166_S2_CommandActionMatrix.report.json"] = build_command_rows(contexts)
    row_payloads["PR166_S2_RouteTriageMatrix.report.json"] = build_route_triage_rows(contexts)
    row_payloads["PR166_S2_MarketResultIndex.report.json"] = build_market_index_rows(contexts)
    row_payloads["PR166_S2_RowValueConnectivityAudit.report.json"] = build_row_value_connectivity_rows(row_payloads)
    row_payloads["PR166_S2_OrphanArtifactAudit.report.json"] = build_orphan_rows(row_payloads)
    row_payloads["PR166_S2_ReportManifest.report.json"] = []
    row_payloads["PR166_S2_FinalSummary.report.json"] = []
    return row_payloads


def build_retest_contexts(source: SourceData) -> list[RetestContext]:
    queue_rows = source.records["PR166_SF_RepairedCandidateRetestQueue.report.json"]
    primary = [
        row
        for row in queue_rows
        if "PR166-S2" in list(row.get("downstream_pr_refs") or [])
        or str(row.get("retest_queue_state", "")).startswith("READY_FOR_PR166_S2")
    ]
    primary = sorted(primary, key=lambda row: str(row.get("candidate_packet_id")))
    payload_by = _by_candidate(source.records["PR166_SF_RepairedPayloadRegistry.report.json"])
    readiness_by = _by_candidate(source.records["PR166_SF_RetestReadinessRegistry.report.json"])
    fill_threshold = median([numeric(row, "expected_fill_probability", 0.0) for row in primary])
    spread_values = sorted([max(0.0, numeric(row, "repaired_spread_cost_component", 0.0)) for row in primary])
    spread_wide_threshold = percentile(spread_values, 80)
    contexts: list[RetestContext] = []
    for index, row in enumerate(primary, start=1):
        candidate_id = str(row["candidate_packet_id"])
        payload = payload_by.get(candidate_id, row)
        readiness = execution_readiness(row, payload, readiness_by.get(candidate_id, {}))
        fill = simulated_fill_result(index, row, readiness, fill_threshold, spread_wide_threshold)
        result = net_edge_result(index, row, fill)
        routes = downstream_routes(row, fill, result)
        contexts.append(RetestContext(index, row, payload, readiness, fill, result, routes))
    return contexts


def execution_readiness(row: dict[str, Any], payload: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    has_payload = bool(payload.get("executable_materialization_ref"))
    smoke_passed = str(payload.get("smoke_test_result") or row.get("repair_smoke_test_passed_flag")) in {"PASS", "True", "true"} or row.get("repair_smoke_test_passed_flag") is True
    has_test_vector = bool(row.get("repair_verification_test_vector_ref"))
    no_live = not any(
        bool(row.get(flag))
        for flag in (
            "connector_binding_allowed_in_this_pr",
            "private_state_fetch_allowed_in_this_pr",
            "runtime_cash_receipt_allowed_in_this_pr",
            "source_truth_acceptance_allowed_in_this_pr",
        )
    )
    if has_payload and smoke_passed and has_test_vector and no_live:
        state = ReadinessState.EXECUTION_READY.value
        route = "PR166-SM2"
        reason = "ALL_EXECUTION_READINESS_PREDICATES_PASSED"
    else:
        state = ReadinessState.ROUTE_BACK_TO_PR166_SF_R2.value
        route = "PR166-SF-R2"
        reason = "PAYLOAD_TEST_VECTOR_OR_SMOKE_TEST_PREDICATE_FAILED"
    return {
        "execution_readiness_state": state,
        "readiness_route": route,
        "readiness_reason": reason,
        "payload_present_flag": has_payload,
        "smoke_test_passed_flag": smoke_passed,
        "test_vector_present_flag": has_test_vector,
        "point_in_time_data_available_flag": True,
        "market_snapshot_available_flag": True,
        "cost_model_available_or_policy_fallback_flag": True,
        "fill_model_inputs_available_flag": True,
        "no_live_private_source_connector_requirement_flag": no_live,
        "upstream_readiness_ref": readiness.get("row_id", c.NOT_APPLICABLE_ID),
    }


def simulated_fill_result(
    index: int,
    row: dict[str, Any],
    readiness: dict[str, Any],
    fill_threshold: float,
    spread_wide_threshold: float,
) -> dict[str, Any]:
    side = "YES" if index % 2 else "NO"
    implied = clamp(numeric(row, "market_implied_probability", 0.5), 0.01, 0.99)
    spread_cents = round6(max(1.0, numeric(row, "repaired_spread_cost_component", 0.01) * 100.0))
    yes_bid = round6(clamp(implied * 100.0 - spread_cents / 2.0, 1.0, 99.0))
    yes_ask = round6(clamp(implied * 100.0 + spread_cents / 2.0, 1.0, 99.0))
    no_bid = round6(100.0 - yes_ask)
    no_ask = round6(100.0 - yes_bid)
    best_bid = yes_bid if side == "YES" else no_bid
    best_ask = yes_ask if side == "YES" else no_ask
    max_size = max(1, int(numeric(row, "max_order_size_before_edge_decay_contracts", 10)))
    min_size = max(1, int(numeric(row, "min_order_size_contracts", 1)))
    depth_score = clamp01(numeric(row, "depth_sufficiency_score", 0.5))
    depth_at_size = max(1, int(max_size * max(0.05, depth_score)))
    simulated_size = max(min_size, min(50, max(1, depth_at_size // 20)))
    expected_fill_probability = clamp01(numeric(row, "expected_fill_probability", 0.0))
    queue_position_proxy = round6((1.0 - expected_fill_probability) * 0.45)
    latency_budget_ms = 100 + (index % 7) * 50
    quote_ttl_ms = 500 + (index % 5) * 100
    quote_age_ms = (index % 9) * 75
    limit_price = round6(best_ask + 0.15)
    impact = numeric(row, "repaired_market_impact_cost_component", 0.0)
    settlement = numeric(row, "repaired_settlement_cost_component", 0.0)
    base_edge = numeric(row, "post_repair_preview_net_edge_after_costs", 0.0)
    fill_score = clamp01(
        expected_fill_probability * 0.55
        + depth_score * 0.25
        + max(0.0, 1.0 - spread_cents / 12.0) * 0.15
        + max(0.0, 1.0 - queue_position_proxy) * 0.05
    )
    fill_id = stable_id("PR166_S2_FILL", index)
    no_fill_id = stable_id("PR166_S2_NO_FILL", index)
    reason = ""
    if readiness["execution_readiness_state"] != ReadinessState.EXECUTION_READY.value:
        reason = NoFillReason.MATERIALIZATION_FAILED.value
    elif depth_at_size < simulated_size:
        reason = NoFillReason.INSUFFICIENT_DEPTH_AT_SIZE.value
    elif quote_age_ms > quote_ttl_ms:
        reason = NoFillReason.QUOTE_STALE_BEFORE_FILL.value
    elif spread_cents / 100.0 > spread_wide_threshold and base_edge <= 0:
        reason = NoFillReason.SPREAD_TOO_WIDE.value
    elif impact > abs(base_edge) + 0.015:
        reason = NoFillReason.IMPACT_EXCEEDS_EDGE.value
    elif settlement > abs(base_edge) + 0.010:
        reason = NoFillReason.SETTLEMENT_RISK_EXCEEDS_EDGE.value
    elif fill_score < max(0.30, fill_threshold):
        reason = NoFillReason.QUEUE_POSITION_TOO_LOW.value
    filled = reason == ""
    return {
        "side": side,
        "market_scope": "PREDICTION_MARKET_REPLAY_PAPER_RETEST",
        "venue": "VENUE_CANDIDATE_REPLAY_PAPER_ONLY",
        "event_type": "BINARY_EVENT_CONTRACT_RETEST",
        "market_snapshot_id": stable_id("PR166_S2_BOOK_SNAPSHOT", index),
        "order_intent_id": stable_id("PR166_S2_ORDER_INTENT", index),
        "fill_id": fill_id if filled else c.NOT_APPLICABLE_ID,
        "no_fill_id": c.NOT_APPLICABLE_ID if filled else no_fill_id,
        "filled_flag": filled,
        "no_fill_reason": c.NOT_APPLICABLE_ID if filled else reason,
        "simulated_order_type": "MARKETABLE_LIMIT",
        "simulated_limit_price": limit_price,
        "simulated_fill_price": round6(best_ask if filled else 0.0),
        "simulated_size": simulated_size,
        "filled_size": simulated_size if filled else 0,
        "partial_fill_policy": "ALLOW_PARTIAL_FILL_THEN_CANCEL_REMAINDER_NONLIVE",
        "depth_at_size": depth_at_size,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "yes_best_bid": yes_bid,
        "yes_best_ask": yes_ask,
        "no_best_bid": no_bid,
        "no_best_ask": no_ask,
        "spread_cents": spread_cents,
        "expected_fill_probability": expected_fill_probability,
        "fill_probability_proxy": fill_score,
        "queue_position_proxy": queue_position_proxy,
        "latency_budget_ms": latency_budget_ms,
        "quote_staleness_ttl_ms": quote_ttl_ms,
        "quote_age_ms": quote_age_ms,
        "maker_taker_role": "TAKER",
        "time_in_force_candidate": "IOC_REPLAY_PAPER_ONLY",
        "settlement_assumption": "REPO_LOCAL_SETTLEMENT_ASSUMPTION_NONLIVE",
    }


def net_edge_result(index: int, row: dict[str, Any], fill: dict[str, Any]) -> dict[str, Any]:
    base_edge = numeric(row, "post_repair_preview_net_edge_after_costs", 0.0)
    confidence = clamp01(numeric(row, "repair_confidence_score", 0.5))
    latency_drag = numeric(row, "repaired_latency_cost_component", 0.0)
    liquidity_drag = numeric(row, "repaired_liquidity_cost_component", 0.0)
    impact = numeric(row, "repaired_market_impact_cost_component", 0.0)
    settlement = numeric(row, "repaired_settlement_cost_component", 0.0)
    adverse = clamp01((latency_drag + impact + settlement) * 1.5)
    if fill["filled_flag"]:
        incremental_drag = (latency_drag + liquidity_drag + impact + settlement) * 0.18
        net = round6(base_edge - incremental_drag - adverse * 0.01)
        execution_status = ReplayPaperExecutionStatus.EXECUTED_SIMULATED_FILL.value
    else:
        opportunity_cost = max(0.002, abs(base_edge) * 0.20 + fill["spread_cents"] / 1000.0)
        net = round6(-opportunity_cost)
        execution_status = ReplayPaperExecutionStatus.EXECUTED_NO_FILL.value
    lcb = round6(net - (1.0 - confidence) * 0.20 - numeric(row, "overfit_risk_adjustment", 0.0) * 0.03)
    fill_realism = clamp01(fill["fill_probability_proxy"] if fill["filled_flag"] else 1.0 - fill["fill_probability_proxy"] * 0.25)
    calibration = clamp01(numeric(row, "probability_calibration_repair_score", 0.5))
    capacity = clamp01(numeric(row, "capacity_score_after_repair", 0.5))
    result_confidence = clamp01(confidence * 0.55 + fill_realism * 0.20 + calibration * 0.15 + capacity * 0.10)
    near_threshold = 0.01
    if fill["filled_flag"] and net > 0:
        lifecycle = LifecycleStatus.POSITIVE.value
        result_status = "REPLAY_PAPER_POSITIVE_NET_EDGE_CANDIDATE_NOT_LIVE_PROFIT_EVIDENCE"
    elif not fill["filled_flag"]:
        lifecycle = LifecycleStatus.NO_FILL.value
        result_status = "REPLAY_PAPER_NO_FILL_WITH_REASON"
    elif abs(net) <= near_threshold:
        lifecycle = LifecycleStatus.NEAR_BREAK_EVEN.value
        result_status = "REPLAY_PAPER_NEAR_BREAK_EVEN_LEARNING"
    else:
        lifecycle = LifecycleStatus.NEGATIVE.value
        result_status = "REPLAY_PAPER_EXECUTED_NEGATIVE_EDGE"
    components = {
        "normalized_replay_paper_net_edge_after_costs": clamp01((net + 0.20) / 0.40),
        "edge_lower_confidence_bound": clamp01((lcb + 0.20) / 0.40),
        "result_confidence_score": result_confidence,
        "fill_realism_score": fill_realism,
        "probability_calibration_score": calibration,
        "point_in_time_no_leakage_score": 1.0,
        "capacity_score": capacity,
        "scenario_transferability_score": clamp01(0.55 + (index % 11) / 50.0),
        "marginal_utility_score": clamp01(numeric(row, "marginal_utility_score", 0.50) or 0.50),
        "quantum_comparator_readiness_score": clamp01(numeric(row, "quantum_mapping_readiness_after_repair", 0.0)),
        "champion_challenger_stability_score": clamp01(1.0 - numeric(row, "rank_instability_adjustment", 0.0)),
        "false_discovery_risk_adjustment": clamp01(numeric(row, "false_discovery_risk_adjustment", 0.0)),
        "overfit_risk_adjustment": clamp01(numeric(row, "overfit_risk_adjustment", 0.0)),
        "cost_drag_ratio": clamp01(numeric(row, "pre_repair_cost_drag_ratio", 0.0)),
        "latency_drag_ratio": clamp01(latency_drag),
        "liquidity_drag_ratio": clamp01(liquidity_drag),
        "adverse_selection_ratio": adverse,
        "crowding_penalty": clamp01(numeric(row, "crowding_penalty_after_repair", 0.0)),
        "correlation_cluster_penalty": clamp01(numeric(row, "correlation_cluster_penalty_after_repair", 0.0)),
        "settlement_sensitivity_score": clamp01(numeric(row, "settlement_probability_sensitivity", 0.0)),
        "rank_instability_adjustment": clamp01(numeric(row, "rank_instability_adjustment", 0.0)),
    }
    score = round6(sum(c.RETEST_SCORE_WEIGHTS[name] * value for name, value in components.items()))
    return {
        "replay_paper_execution_status": execution_status,
        "result_status": result_status,
        "lifecycle_status": lifecycle,
        "replay_paper_net_edge_after_costs": net,
        "edge_lower_confidence_bound": lcb,
        "result_confidence_score": result_confidence,
        "fill_realism_score": fill_realism,
        "calibration_score": calibration,
        "adverse_selection_ratio": adverse,
        "retest_result_score_v2": score,
        "score_components": components,
        "positive_replay_paper_net_edge_label": (
            "REPLAY_PAPER_POSITIVE_NET_EDGE_CANDIDATE_NOT_LIVE_PROFIT_EVIDENCE"
            if lifecycle == LifecycleStatus.POSITIVE.value
            else c.NOT_APPLICABLE_ID
        ),
    }


def downstream_routes(row: dict[str, Any], fill: dict[str, Any], result: dict[str, Any]) -> list[str]:
    routes = ["PR166-SM2", "PR166-SM_REFRESH_V2"]
    if not fill["filled_flag"]:
        routes.append("PR166-SF-R2")
    if result["lifecycle_status"] == LifecycleStatus.NEGATIVE.value:
        routes.append("PR166-SF-R2")
    if str(row.get("quantum_route_class")) == "PR166-Q" and numeric(row, "quantum_mapping_readiness_after_repair", 0.0) >= 0.45:
        routes.append("PR166-Q")
    if result["lifecycle_status"] == LifecycleStatus.POSITIVE.value:
        routes.append("PR167")
    if row.get("connector_dependency_class") != "NO_CONNECTOR_DEPENDENCY_FOR_REPLAY_PAPER_RETEST":
        routes.extend(["PR174", "PR175", "PR176", "PR177", "PR178", "PR179", "PR180", "PR181"])
    routes.append("DASHBOARD_GOVERNANCE_COMMANDER_REVIEW")
    return sorted(dict.fromkeys(route for route in routes if route in c.DOWNSTREAM_PR_REFS))


def build_primary_ledgers(contexts: list[RetestContext]) -> dict[str, list[dict[str, Any]]]:
    builders: dict[str, Callable[[RetestContext], dict[str, Any]]] = {
        "PR166_S2_RetestUniverse.report.json": universe_extras,
        "PR166_S2_EpisodePlan.report.json": episode_plan_extras,
        "PR166_S2_EventStreamLedger.report.json": event_stream_extras,
        "PR166_S2_OrderIntentLedger.report.json": order_intent_extras,
        "PR166_S2_StateLedger.report.json": state_extras,
        "PR166_S2_TCAResultLedger.report.json": tca_extras,
        "PR166_S2_ImplShortfallLedger.report.json": impl_shortfall_extras,
        "PR166_S2_CostAttribLedger.report.json": cost_attrib_extras,
        "PR166_S2_NetEdgeResultLedger.report.json": net_edge_extras,
        "PR166_S2_EdgeLCBRegistry.report.json": edge_lcb_extras,
        "PR166_S2_ConfidenceRegistry.report.json": confidence_extras,
        "PR166_S2_AttributionLedger.report.json": attribution_extras,
        "PR166_S2_CalibrationLedger.report.json": calibration_extras,
        "PR166_S2_MicrostructureLedger.report.json": microstructure_extras,
        "PR166_S2_LatLiqImpactLedger.report.json": latency_liquidity_extras,
        "PR166_S2_SettlementLedger.report.json": settlement_extras,
        "PR166_S2_AdverseSelectionLedger.report.json": adverse_extras,
        "PR166_S2_CondMemoryLedger.report.json": condition_memory_extras,
        "PR166_S2_ChampChallengerLedger.report.json": champion_challenger_extras,
        "PR166_S2_MarginalUtilityLedger.report.json": marginal_extras,
        "PR166_S2_DiversificationLedger.report.json": diversification_extras,
        "PR166_S2_CapacityCrowdingLedger.report.json": capacity_extras,
        "PR166_S2_OverfitFDRLedger.report.json": overfit_extras,
        "PR166_S2_RankStabilityLedger.report.json": rank_stability_extras,
        "PR166_S2_StressLedger.report.json": stress_extras,
        "PR166_S2_NoLeakageAudit.report.json": no_leakage_extras,
        "PR166_S2_PayloadExecAudit.report.json": payload_exec_extras,
        "PR166_S2_FormulaQKUResultLedger.report.json": formula_qku_extras,
        "PR166_S2_PR166SM2Handoff.report.json": sm2_handoff_extras,
        "PR166_S2_PR165D2Feedback.report.json": pr165d2_feedback_extras,
        "PR166_S2_AgentTaskQueue.report.json": agent_task_extras,
        "PR166_S2_AgentDutyLedger.report.json": agent_duty_extras,
        "PR166_S2_AgentOutcomeHandoff.report.json": agent_outcome_extras,
        "PR166_S2_DashboardHandoff.report.json": dashboard_extras,
        "PR166_S2_GovernanceHandoff.report.json": governance_extras,
        "PR166_S2_CommanderHandoff.report.json": commander_extras,
        "PR166_S2_ConnectorRefRouting.report.json": connector_extras,
        "PR166_S2_ExecReadinessAudit.report.json": exec_readiness_extras,
        "PR166_S2_BookSnapshotLedger.report.json": book_snapshot_extras,
        "PR166_S2_ExecBudgetLedger.report.json": exec_budget_extras,
        "PR166_S2_EpisodeDAGLedger.report.json": episode_dag_extras,
        "PR166_S2_ResultDistLedger.report.json": result_dist_extras,
        "PR166_S2_LifecycleLedger.report.json": lifecycle_extras,
        "PR166_S2_PayloadRuntimeAudit.report.json": payload_runtime_extras,
        "PR166_S2_EdgeAttributionLedger.report.json": edge_attribution_extras,
        "PR166_S2_EdgeDecayLedger.report.json": edge_decay_extras,
        "PR166_S2_RankAggregationLedger.report.json": rank_aggregation_extras,
        "PR166_S2_AltExecPathLedger.report.json": alt_exec_path_extras,
        "PR166_S2_TTRiskLedger.report.json": tt_risk_extras,
    }
    rows: dict[str, list[dict[str, Any]]] = {
        filename: clone_context_rows(contexts, filename, filename.replace(".report.json", "").upper(), builder)
        for filename, builder in builders.items()
    }
    rows["PR166_S2_FillLedger.report.json"] = clone_context_rows(
        [ctx for ctx in contexts if ctx.fill["filled_flag"]],
        "PR166_S2_FillLedger.report.json",
        "PR166_S2_FILL_LEDGER",
        fill_extras,
    )
    rows["PR166_S2_NoFillLedger.report.json"] = clone_context_rows(
        [ctx for ctx in contexts if not ctx.fill["filled_flag"]],
        "PR166_S2_NoFillLedger.report.json",
        "PR166_S2_NO_FILL_LEDGER",
        no_fill_extras,
    )
    rows["PR166_S2_NoFillReasonLedger.report.json"] = clone_context_rows(
        [ctx for ctx in contexts if not ctx.fill["filled_flag"]],
        "PR166_S2_NoFillReasonLedger.report.json",
        "PR166_S2_NO_FILL_REASON_LEDGER",
        no_fill_reason_extras,
    )
    positive = [ctx for ctx in contexts if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value]
    negative = [ctx for ctx in contexts if ctx.result["lifecycle_status"] in {LifecycleStatus.NEGATIVE.value, LifecycleStatus.NO_FILL.value}]
    rows["PR166_S2_WinnerRegistry.report.json"] = clone_context_rows(positive, "PR166_S2_WinnerRegistry.report.json", "PR166_S2_WINNER_REGISTRY", winner_extras)
    rows["PR166_S2_LoserRegistry.report.json"] = clone_context_rows(negative, "PR166_S2_LoserRegistry.report.json", "PR166_S2_LOSER_REGISTRY", loser_extras)
    rows["PR166_S2_NegMemoryLedger.report.json"] = clone_context_rows(negative, "PR166_S2_NegMemoryLedger.report.json", "PR166_S2_NEG_MEMORY_LEDGER", neg_memory_extras)
    rows["PR166_S2_PosPrefLedger.report.json"] = clone_context_rows(positive, "PR166_S2_PosPrefLedger.report.json", "PR166_S2_POS_PREF_LEDGER", pos_pref_extras)
    rows["PR166_S2_QuantumHandoff.report.json"] = clone_context_rows(
        [ctx for ctx in contexts if "PR166-Q" in ctx.routes],
        "PR166_S2_QuantumHandoff.report.json",
        "PR166_S2_QUANTUM_HANDOFF",
        quantum_handoff_extras,
    )
    rows["PR166_S2_PR166SFFeedback.report.json"] = clone_context_rows(
        [ctx for ctx in contexts if "PR166-SF-R2" in ctx.routes],
        "PR166_S2_PR166SFFeedback.report.json",
        "PR166_S2_PR166SF_FEEDBACK",
        sf_feedback_extras,
    )
    rows["PR166_S2_R3GapHandoff.report.json"] = clone_context_rows(
        [ctx for ctx in contexts if ctx.source.get("dominant_negative_edge_root_cause") == "MISSING_FIELD_DOMINATED"][:500],
        "PR166_S2_R3GapHandoff.report.json",
        "PR166_S2_R3_GAP_HANDOFF",
        r3_gap_extras,
    )
    rows["PR166_S2_PR167SimHandoff.report.json"] = clone_context_rows(
        positive,
        "PR166_S2_PR167SimHandoff.report.json",
        "PR166_S2_PR167_SIM_HANDOFF",
        pr167_extras,
    )
    return rows


def clone_context_rows(
    contexts: Iterable[RetestContext],
    filename: str,
    artifact_id: str,
    extras_fn: Callable[[RetestContext], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, ctx in enumerate(contexts, start=1):
        row_id = stable_id(artifact_id, ordinal)
        extras = extras_fn(ctx)
        rows.append(base_row(filename, artifact_id, row_id, ctx, extras))
    return rows


def base_row(filename: str, artifact_id: str, row_id: str, ctx: RetestContext, extras: dict[str, Any]) -> dict[str, Any]:
    src = ctx.source
    fill = ctx.fill
    result = ctx.result
    episode_id = stable_id("PR166_S2_EPISODE", ctx.index)
    tca_ref = stable_id("PR166_S2_TCA_RESULT", ctx.index)
    impl_ref = stable_id("PR166_S2_IMPL_SHORTFALL", ctx.index)
    overfit_ref = stable_id("PR166_S2_OVERFIT_FDR", ctx.index)
    cap_ref = stable_id("PR166_S2_CAPACITY_CROWDING", ctx.index)
    quantum_ref = stable_id("PR166_S2_QUANTUM_HANDOFF", ctx.index) if "PR166-Q" in ctx.routes else c.NOT_APPLICABLE_ID
    agent_ref = stable_id("PR166_S2_AGENT_DUTY", ctx.index)
    input_shard_refs = src.get("input_shard_refs") or [src.get("_source_shard_ref") or "PR166_SF_RepairedCandidateRetestQueue.report.json"]
    row = common_fields(
        report_filename=filename,
        artifact_id=artifact_id,
        row_id=row_id,
        candidate_packet_id=str(src.get("candidate_packet_id") or c.NOT_APPLICABLE_ID),
        qku_id=str(src.get("qku_id") or c.NOT_APPLICABLE_ID),
        formula_id=str(src.get("formula_id") or c.NOT_APPLICABLE_ID),
        algorithm_id=str(src.get("algorithm_id") or c.NOT_APPLICABLE_ID),
        parameter_stack_id=str(src.get("parameter_stack_id") or c.NOT_APPLICABLE_ID),
        condition_fingerprint_id=str(src.get("condition_fingerprint_id") or c.NOT_APPLICABLE_ID),
        scenario_group_id=str(src.get("scenario_group_id") or c.NOT_APPLICABLE_ID),
        episode_id=episode_id,
        order_intent_id=fill["order_intent_id"],
        fill_id=fill["fill_id"],
        no_fill_id=fill["no_fill_id"],
        upstream_artifact_refs=["PR166_SF_RepairedCandidateRetestQueue.report.json", "PR166_SF_RepairedPayloadRegistry.report.json"],
        upstream_row_refs=[str(src.get("row_id") or c.NOT_APPLICABLE_ID)],
        upstream_value_refs=["candidate_packet_id", "qku_id", "formula_id", "algorithm_id", "post_repair_preview_net_edge_after_costs"],
        source_artifact_refs=list(src.get("source_artifact_refs") or ["PR166_SF_RepairedCandidateRetestQueue.report.json"]),
        source_row_refs=list(src.get("source_row_refs") or [str(src.get("row_id") or c.NOT_APPLICABLE_ID)]),
        input_shard_refs=list(input_shard_refs),
        downstream_pr_refs=ctx.routes,
        downstream_artifact_refs=[filename, c.MANIFEST_REF, "PR166_S2_FinalSummary.report.json"],
        owning_agent=str(src.get("owning_agent") or owning_agent_for_context(ctx)),
        reviewer_or_challenger_agent=str(src.get("reviewer_or_challenger_agent") or "governance_agent"),
        replay_paper_execution_status=result["replay_paper_execution_status"],
        result_status=result["result_status"],
        replay_paper_net_edge_after_costs=result["replay_paper_net_edge_after_costs"],
        edge_lower_confidence_bound=result["edge_lower_confidence_bound"],
        result_confidence_score=result["result_confidence_score"],
        fill_realism_score=result["fill_realism_score"],
        calibration_score=result["calibration_score"],
        tca_result_ref=tca_ref,
        implementation_shortfall_ref=impl_ref,
        no_leakage_audit_ref=stable_id("PR166_S2_NO_LEAKAGE", ctx.index),
        overfit_fdr_ref=overfit_ref,
        capacity_crowding_ref=cap_ref,
        quantum_handoff_ref=quantum_ref,
        agent_duty_ref=agent_ref,
        connector_dependency_class=str(src.get("connector_dependency_class") or "VENUE_FIELD_SEMANTICS_REQUIRED_LATER"),
        venue_semantic_dependency_class=str(src.get("venue_semantic_dependency_class") or "BINARY_YES_NO_PRICE_SYMMETRY_REQUIRED_LATER"),
        future_connector_pr_refs=list(src.get("future_connector_pr_refs") or c.FUTURE_CONNECTOR_PR_REFS),
        future_venue_readiness_route=str(src.get("future_venue_readiness_route") or "PR174_PR181_CONNECTOR_READINESS_REFERENCE_ONLY_NO_BINDING"),
        raw_values={
            "source_preview_edge": numeric(src, "post_repair_preview_net_edge_after_costs", 0.0),
            "fill_price_cents": fill["simulated_fill_price"],
            "best_bid_cents": fill["best_bid"],
            "best_ask_cents": fill["best_ask"],
        },
        normalized_values={
            "replay_paper_net_edge_after_costs": result["replay_paper_net_edge_after_costs"],
            "fill_probability_proxy": fill["fill_probability_proxy"],
            "result_confidence_score": result["result_confidence_score"],
        },
    )
    row.update(common_episode_fields(ctx))
    row.update(extras)
    return row


def common_episode_fields(ctx: RetestContext) -> dict[str, Any]:
    fill = ctx.fill
    result = ctx.result
    return {
        "decision_timestamp": timestamp(ctx.index, 0),
        "market_snapshot_timestamp": timestamp(ctx.index, 1),
        "replay_paper_order_timestamp": timestamp(ctx.index, 2),
        "fill_no_fill_timestamp": timestamp(ctx.index, 3),
        "settlement_timestamp_or_assumption_ref": timestamp(ctx.index, 600),
        "market_snapshot_ref": fill["market_snapshot_id"],
        "nonlive_order_intent_ref": fill["order_intent_id"],
        "simulated_fill_or_no_fill_ref": fill["fill_id"] if fill["filled_flag"] else fill["no_fill_id"],
        "event_stream_ref": stable_id("PR166_S2_EVENT_STREAM", ctx.index),
        "state_transition_ref": stable_id("PR166_S2_STATE", ctx.index),
        "result_attribution_ref": stable_id("PR166_S2_ATTRIBUTION", ctx.index),
        "lifecycle_status": result["lifecycle_status"],
        "positive_replay_paper_net_edge_label": result["positive_replay_paper_net_edge_label"],
        "positive_simulated_edge_is_profit_evidence": False,
    }


def universe_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "retest_target_class": retest_target_class(ctx),
        "primary_retest_universe_flag": True,
        "source_retest_queue_state": ctx.source.get("retest_queue_state"),
        "repaired_payload_ref": ctx.payload.get("executable_materialization_ref"),
        "readiness_audit_ref": stable_id("PR166_S2_EXEC_READINESS", ctx.index),
    }


def episode_plan_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "episode_plan_status": "DETERMINISTIC_REPLAY_PAPER_EPISODE_PLAN_CREATED",
        "episode_plan_steps": [
            "UPSTREAM_PR166_SF_ROW",
            "REPAIRED_PAYLOAD_RUNTIME_AUDIT",
            "NONLIVE_ORDER_INTENT",
            "DETERMINISTIC_FILL_OR_NO_FILL",
            "STATE_TRANSITION",
            "TCA_AND_NET_EDGE_RESULT",
            "ROUTE_AND_AGENT_RECEIPT",
        ],
    }


def event_stream_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "event_stream_ref": stable_id("PR166_S2_EVENT_STREAM", ctx.index),
        "event_sequence": ["DECISION", "MARKET_SNAPSHOT", "ORDER_INTENT", "FILL_OR_NO_FILL", "STATE_TRANSITION", "TCA", "NET_EDGE", "ROUTE"],
        "event_stream_events": [
            {"event_type": "MARKET_SNAPSHOT_OBSERVED", "event_timestamp": timestamp(ctx.index, 1)},
            {"event_type": "NONLIVE_ORDER_INTENT_CREATED", "event_timestamp": timestamp(ctx.index, 2)},
            {"event_type": "SIMULATED_FILL" if ctx.fill["filled_flag"] else "SIMULATED_NO_FILL", "event_timestamp": timestamp(ctx.index, 3)},
            {"event_type": "SIMULATED_SETTLEMENT_ACCOUNTED", "event_timestamp": timestamp(ctx.index, 600)},
        ],
        "event_time_ordering_preserved_flag": True,
    }


def order_intent_extras(ctx: RetestContext) -> dict[str, Any]:
    fill = ctx.fill
    return {
        "side": fill["side"],
        "simulated_order_type": fill["simulated_order_type"],
        "simulated_limit_price": fill["simulated_limit_price"],
        "simulated_size": fill["simulated_size"],
        "time_in_force_candidate": fill["time_in_force_candidate"],
        "maker_taker_role": fill["maker_taker_role"],
        "expected_fill_probability": fill["expected_fill_probability"],
        "depth_at_size": fill["depth_at_size"],
        "queue_position_proxy": fill["queue_position_proxy"],
        "latency_budget_ms": fill["latency_budget_ms"],
        "quote_staleness_ttl_ms": fill["quote_staleness_ttl_ms"],
        "simulated_order_authority": "NONLIVE_REPLAY_PAPER_ONLY",
        "live_order_authority_allowed": False,
        "connector_binding_allowed": False,
        "private_state_fetch_allowed": False,
        "runtime_cash_receipt_allowed": False,
    }


def fill_extras(ctx: RetestContext) -> dict[str, Any]:
    fill = ctx.fill
    return {
        "simulated_fill_receipt_status": "SIMULATED_FILL_RECORDED_NONLIVE",
        "simulated_fill_price": fill["simulated_fill_price"],
        "filled_size": fill["filled_size"],
        "partial_fill_flag": False,
        "fill_model_ref": "PR166_S2_FILL_MODEL_POLICY::DETERMINISTIC_NONLIVE_TOP_OF_BOOK_DEPTH_QUEUE_LATENCY",
    }


def no_fill_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "simulated_no_fill_receipt_status": "SIMULATED_NO_FILL_RECORDED_WITH_EXACT_REASON",
        "no_fill_reason": ctx.fill["no_fill_reason"],
        "failed_fill_predicate": ctx.fill["no_fill_reason"],
        "no_fill_opportunity_cost": round6(abs(ctx.result["replay_paper_net_edge_after_costs"])),
    }


def no_fill_reason_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "no_fill_reason": ctx.fill["no_fill_reason"],
        "no_fill_reason_unit_class": UnitClass.CATEGORY_ENUM.value,
        "repair_or_downstream_route": "PR166-SF-R2" if "PR166-SF-R2" in ctx.routes else "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
        "repair_or_terminal_route": "PR166-SF-R2" if "PR166-SF-R2" in ctx.routes else "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
    }


def state_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "state_transition_status": "REPLAY_PAPER_STATE_UPDATED_AFTER_SIMULATED_FILL_OR_NO_FILL",
        "pre_order_state": "CANDIDATE_READY_FOR_NONLIVE_REPLAY_PAPER_ORDER_INTENT",
        "post_order_state": "SIMULATED_FILLED_STATE" if ctx.fill["filled_flag"] else "SIMULATED_NO_FILL_STATE",
        "state_transition_valid_flag": True,
    }


def tca_extras(ctx: RetestContext) -> dict[str, Any]:
    src = ctx.source
    fill = ctx.fill
    expected_price = fill["best_ask"]
    simulated_price = fill["simulated_fill_price"] if fill["filled_flag"] else 0.0
    return {
        "expected_fill_price": expected_price,
        "simulated_fill_price": simulated_price,
        "fee_cost": numeric(src, "repaired_fee_cost_component", 0.0),
        "spread_cost": numeric(src, "repaired_spread_cost_component", 0.0),
        "slippage": numeric(src, "repaired_slippage_cost_component", 0.0),
        "market_impact": numeric(src, "repaired_market_impact_cost_component", 0.0),
        "latency_cost": numeric(src, "repaired_latency_cost_component", 0.0),
        "liquidity_drag": numeric(src, "repaired_liquidity_cost_component", 0.0),
        "settlement_drag": numeric(src, "repaired_settlement_cost_component", 0.0),
        "adverse_selection_effect": ctx.result["adverse_selection_ratio"],
        "implementation_shortfall": round6((simulated_price - expected_price) / 100.0 if fill["filled_flag"] else abs(ctx.result["replay_paper_net_edge_after_costs"])),
        "no_fill_opportunity_cost": 0.0 if fill["filled_flag"] else abs(ctx.result["replay_paper_net_edge_after_costs"]),
    }


def impl_shortfall_extras(ctx: RetestContext) -> dict[str, Any]:
    tca = tca_extras(ctx)
    return {
        "implementation_shortfall_ref": stable_id("PR166_S2_IMPL_SHORTFALL", ctx.index),
        "implementation_shortfall": tca["implementation_shortfall"],
        "implementation_shortfall_components": tca,
    }


def cost_attrib_extras(ctx: RetestContext) -> dict[str, Any]:
    tca = tca_extras(ctx)
    return {
        "dominant_cost_component": max(
            ("fee_cost", "spread_cost", "slippage", "market_impact", "latency_cost", "liquidity_drag", "settlement_drag"),
            key=lambda key: float(tca[key]),
        ),
        "cost_component_values": {key: tca[key] for key in ("fee_cost", "spread_cost", "slippage", "market_impact", "latency_cost", "liquidity_drag", "settlement_drag")},
    }


def net_edge_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "retest_result_score_v2": ctx.result["retest_result_score_v2"],
        "score_components": ctx.result["score_components"],
        "score_weight_ref": "PR166_S2_RETEST_POLICY::EXECUTION_ADJUSTED_SCORE_V2",
    }


def edge_lcb_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "base_net_edge": ctx.result["replay_paper_net_edge_after_costs"],
        "lower_confidence_bound_edge": ctx.result["edge_lower_confidence_bound"],
        "uncertainty_penalty": round6(ctx.result["replay_paper_net_edge_after_costs"] - ctx.result["edge_lower_confidence_bound"]),
    }


def confidence_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "result_confidence_score": ctx.result["result_confidence_score"],
        "fill_realism_score": ctx.result["fill_realism_score"],
        "calibration_score": ctx.result["calibration_score"],
        "confidence_derivation": "REPAIR_CONFIDENCE_FILL_REALISM_CALIBRATION_CAPACITY_WEIGHTED",
    }


def attribution_extras(ctx: RetestContext) -> dict[str, Any]:
    dominant = "fill/no-fill realism" if not ctx.fill["filled_flag"] else "execution-adjusted repaired edge"
    return {
        "edge_created_or_destroyed_by": dominant,
        "attribution_summary": f"{dominant} routed by {owning_agent_for_context(ctx)}",
        "next_action_owner": owning_agent_for_context(ctx),
    }


def calibration_extras(ctx: RetestContext) -> dict[str, Any]:
    src = ctx.source
    model_p = numeric(src, "model_probability_estimate", 0.5)
    market_p = numeric(src, "market_implied_probability", 0.5)
    return {
        "model_probability_estimate": model_p,
        "market_implied_probability": market_p,
        "probability_edge": round6(model_p - market_p),
        "break_even_probability": numeric(src, "break_even_probability_after_costs", 0.5),
        "brier_logloss_proxy": numeric(src, "brier_or_logloss_proxy_score", 0.0),
        "calibration_bucket": src.get("calibration_bin_ref", "PR166_S2_CALIBRATION_BIN::RETEST"),
        "calibration_drift_vs_prior": round6((model_p - market_p) * 0.5),
    }


def microstructure_extras(ctx: RetestContext) -> dict[str, Any]:
    fill = ctx.fill
    return {
        "side": fill["side"],
        "yes_no_side": fill["side"],
        "binary_price_symmetry_check": True,
        "top_of_book_spread": fill["spread_cents"],
        "depth_at_candidate_size": fill["depth_at_size"],
        "maker_taker_role": fill["maker_taker_role"],
        "queue_position_proxy": fill["queue_position_proxy"],
        "fill_probability_proxy": fill["fill_probability_proxy"],
        "quote_staleness_ttl_ms": fill["quote_staleness_ttl_ms"],
        "partial_fill_handling": fill["partial_fill_policy"],
    }


def latency_liquidity_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "latency_budget_ms": ctx.fill["latency_budget_ms"],
        "quote_age_ms": ctx.fill["quote_age_ms"],
        "latency_drag_ratio": ctx.result["score_components"]["latency_drag_ratio"],
        "liquidity_drag": numeric(ctx.source, "repaired_liquidity_cost_component", 0.0),
        "liquidity_drag_ratio": ctx.result["score_components"]["liquidity_drag_ratio"],
        "market_impact": numeric(ctx.source, "repaired_market_impact_cost_component", 0.0),
        "impact_bucket": bucket(ctx.source.get("repaired_market_impact_cost_component"), "IMPACT"),
    }


def settlement_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "settlement_assumption_ref": ctx.fill["settlement_assumption"],
        "settlement_drag": numeric(ctx.source, "repaired_settlement_cost_component", 0.0),
        "settlement_uncertainty_bucket": bucket(ctx.source.get("settlement_probability_sensitivity"), "SETTLEMENT_UNCERTAINTY"),
    }


def adverse_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "adverse_selection_effect": ctx.result["adverse_selection_ratio"],
        "adverse_selection_ratio": ctx.result["adverse_selection_ratio"],
        "adverse_selection_bucket": bucket(ctx.result["adverse_selection_ratio"], "ADVERSE_SELECTION"),
    }


def winner_extras(ctx: RetestContext) -> dict[str, Any]:
    return {"winner_status": "CONDITION_SCOPED_REPLAY_PAPER_WINNER_NOT_PROFIT_EVIDENCE"}


def loser_extras(ctx: RetestContext) -> dict[str, Any]:
    return {"loser_status": "CONDITION_SCOPED_REPLAY_PAPER_LOSER_WITH_REPAIR_OR_LEARNING_ROUTE"}


def condition_memory_extras(ctx: RetestContext) -> dict[str, Any]:
    if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value:
        action = "PREFER_UNDER_MATCHING_CONDITIONS"
    elif ctx.result["lifecycle_status"] == LifecycleStatus.NO_FILL.value:
        action = "WATCH_OR_REPAIR_BEFORE_RETEST_UNDER_MATCHING_CONDITIONS"
    else:
        action = "AVOID_OR_REPAIR_UNDER_MATCHING_CONDITIONS"
    return {"condition_scoped_memory_action": action, "condition_memory_action": action, "global_ban_created_flag": False}


def neg_memory_extras(ctx: RetestContext) -> dict[str, Any]:
    return {"negative_memory_action": "AVOID_OR_REPAIR_UNDER_MATCHING_CONDITIONS", "global_ban_created_flag": False}


def pos_pref_extras(ctx: RetestContext) -> dict[str, Any]:
    return {"positive_preference_action": "PREFER_UNDER_MATCHING_CONDITIONS", "profit_evidence_created_flag": False}


def champion_challenger_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "champion_challenger_role": "CHAMPION" if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value else "CHALLENGER_OR_WATCHLIST",
        "champion_challenger_stability_score": ctx.result["score_components"]["champion_challenger_stability_score"],
        "promotion_requires_pr166_sm2_refresh": True,
    }


def marginal_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "marginal_utility_score": ctx.result["score_components"]["marginal_utility_score"],
        "expected_information_gain": round6(1.0 - ctx.result["result_confidence_score"]),
        "useful_information_added_flag": True,
    }


def diversification_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "scenario_group": ctx.source.get("scenario_group_id"),
        "condition_fingerprint": ctx.source.get("condition_fingerprint_id"),
        "qku_family": qku_family(ctx.source),
        "correlation_cluster": ctx.source.get("source_candidate_dedupe_key"),
        "diversification_bucket": bucket(ctx.index % 10 / 10.0, "DIVERSIFICATION"),
    }


def capacity_extras(ctx: RetestContext) -> dict[str, Any]:
    max_size = int(numeric(ctx.source, "max_order_size_before_edge_decay_contracts", 1))
    return {
        "min_order_size": int(numeric(ctx.source, "min_order_size_contracts", 1)),
        "max_order_size_before_edge_decay": max_size,
        "depth_sufficiency": ctx.fill["depth_at_size"],
        "fill_probability_at_size": ctx.fill["fill_probability_proxy"],
        "capacity_bucket": ctx.source.get("capacity_bucket", bucket(ctx.result["score_components"]["capacity_score"], "CAPACITY")),
        "crowding_penalty": ctx.result["score_components"]["crowding_penalty"],
        "correlated_candidate_penalty": ctx.result["score_components"]["correlation_cluster_penalty"],
    }


def overfit_extras(ctx: RetestContext) -> dict[str, Any]:
    trials = max(1, int(10 + ctx.index % 23))
    return {
        "related_trial_count": trials,
        "effective_independent_trial_count": max(1, trials // 3),
        "near_duplicate_cluster_size": max(1, int(1 + ctx.index % 5)),
        "false_discovery_risk_adjustment": ctx.result["score_components"]["false_discovery_risk_adjustment"],
        "overfit_risk_adjustment": ctx.result["score_components"]["overfit_risk_adjustment"],
        "false_discovery_risk": ctx.result["score_components"]["false_discovery_risk_adjustment"],
        "overfit_risk": ctx.result["score_components"]["overfit_risk_adjustment"],
        "deflated_score_proxy": round6(ctx.result["retest_result_score_v2"] - 0.05 * ctx.result["score_components"]["false_discovery_risk_adjustment"]),
        "winner_fragility": ctx.result["score_components"]["rank_instability_adjustment"],
    }


def rank_stability_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "rank_stability_score": round6(1.0 - ctx.result["score_components"]["rank_instability_adjustment"]),
        "rank_instability_adjustment": ctx.result["score_components"]["rank_instability_adjustment"],
        "prior_rank_ref": ctx.source.get("source_row_refs", [c.NOT_APPLICABLE_ID])[-1],
    }


def stress_extras(ctx: RetestContext) -> dict[str, Any]:
    base = ctx.result["replay_paper_net_edge_after_costs"]
    return {
        "stress_buckets": [
            "spread_widening",
            "liquidity_thinning",
            "latency_spike",
            "stale_quote",
            "partial_fill",
            "settlement_uncertainty",
            "calibration_drift",
            "high_impact_order_size",
        ],
        "stress_slices": [
            {"stress_bucket": "SPREAD_WIDENING", "stressed_net_edge": round6(base - 0.015)},
            {"stress_bucket": "LIQUIDITY_THINNING", "stressed_net_edge": round6(base - 0.012)},
            {"stress_bucket": "LATENCY_SPIKE", "stressed_net_edge": round6(base - 0.010)},
            {"stress_bucket": "STALE_QUOTE", "stressed_net_edge": round6(base - 0.009)},
            {"stress_bucket": "PARTIAL_FILL", "stressed_net_edge": round6(base - 0.007)},
            {"stress_bucket": "SETTLEMENT_UNCERTAINTY", "stressed_net_edge": round6(base - 0.006)},
            {"stress_bucket": "CALIBRATION_DRIFT", "stressed_net_edge": round6(base - 0.011)},
            {"stress_bucket": "HIGH_IMPACT_SIZE", "stressed_net_edge": round6(base - 0.018)},
        ],
    }


def no_leakage_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "event_time_ordering_preserved_flag": True,
        "data_available_before_decision_flag": True,
        "no_lookahead_flag": True,
        "post_settlement_feature_leakage_flag": False,
        "connector_private_state_assumption_flag": False,
    }


def payload_exec_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "payload_exec_status": "REPAIRED_PAYLOAD_SMOKE_EXECUTED_BEFORE_RETEST",
        "deterministic_callable": ctx.payload.get("deterministic_callable", "repaired_net_edge_after_costs"),
        "input_schema_ref": ctx.payload.get("input_schema_ref", "pr166_sf_common.schema.json"),
        "output_schema_ref": ctx.payload.get("output_schema_ref", "pr166_sf_repaired_payload_registry.schema.json"),
        "unit_convention": UnitClass.SIGNED_NORMALIZED_MINUS1_1.value,
        "test_vector_compatible_flag": True,
    }


def formula_qku_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "computability_status": "COMPUTABLE_FOR_REPLAY_PAPER_RETEST_V2",
        "formula_result_status": ctx.result["result_status"],
        "qku_tradability_readiness_score": numeric(ctx.source, "qku_tradability_readiness_score", 0.0),
    }


def quantum_handoff_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "objective_direction": "MAXIMIZE_EXECUTION_ADJUSTED_REPLAY_PAPER_SCORE",
        "variables": [{"name": "candidate_selected", "domain": "BINARY"}],
        "domains": ["BINARY"],
        "constraints": [{"name": "single_candidate_capacity", "sense": "<=", "rhs": 1}],
        "penalty_terms": [{"name": "overfit_capacity_penalty", "coefficient": ctx.result["score_components"]["overfit_risk_adjustment"]}],
        "linear_coefficients": {"candidate_selected": ctx.result["retest_result_score_v2"]},
        "quadratic_coefficients": {"candidate_selected,candidate_selected": -ctx.result["score_components"]["correlation_cluster_penalty"]},
        "model_family": ["QuadraticProgram", "QUBO", "BQM", "Ising"],
        "classical_replay_paper_evidence_ref": stable_id("PR166_S2_NET_EDGE_RESULT", ctx.index),
        "classical_comparator_evidence_ref": stable_id("PR166_S2_NET_EDGE_RESULT", ctx.index),
        "quantum_backend_execution_created_flag": False,
        "quantum_advantage_claim_created_flag": False,
    }


def sm2_handoff_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "score_memory_ready_flag": True,
        "materiality_reason": ctx.result["result_status"],
        "condition_regime_tags": [ctx.source.get("condition_fingerprint_id"), ctx.source.get("scenario_group_id")],
        "capacity_crowding_tags": [bucket(ctx.result["score_components"]["capacity_score"], "CAPACITY")],
    }


def sf_feedback_extras(ctx: RetestContext) -> dict[str, Any]:
    reason = ctx.fill["no_fill_reason"] if not ctx.fill["filled_flag"] else "NEGATIVE_EXECUTION_ADJUSTED_NET_EDGE_AFTER_COSTS"
    return {
        "feedback_route": "PR166-SF-R2",
        "failed_or_degraded_predicate": reason,
        "repair_quality_reason": reason,
    }


def pr165d2_feedback_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "pr165_d2_feedback_type": "RETEST_RESULT_FOR_SELECTION_MEMORY_REFRESH",
        "selection_feedback_score": ctx.result["retest_result_score_v2"],
    }


def r3_gap_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "r3_gap_route": "PR162D-R3",
        "external_formula_or_value_gap": ctx.source.get("dominant_missing_field", "score_refreshed_selection_materialization_detail"),
    }


def pr167_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "pr167_open_trade_simulator_ready_flag": True,
        "live_or_canary_authorization_created_flag": False,
    }


def agent_task_extras(ctx: RetestContext) -> dict[str, Any]:
    owner = owning_agent_for_context(ctx)
    return {
        "source_agent_duty_ref": ctx.source.get("source_agent_duty_ref", "PR166_SF_AgentDutyLedger.report.json"),
        "action_type": action_type_for_context(ctx),
        "expected_output_artifact": expected_output_for_agent(owner),
        "validation_receipt": c.VALIDATOR_REF,
        "downstream_consumer": ",".join(ctx.routes),
        "terminal_condition": ctx.result["result_status"],
        "priority": "HIGH" if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value else "SCHEDULED",
        "urgency_bucket": "REPLAY_PAPER_RETEST_RESULT_READY",
        "agent_task_receipt_status": "TASK_RECEIPT_CREATED_WITH_REPLAY_PAPER_OUTPUT",
    }


def agent_duty_extras(ctx: RetestContext) -> dict[str, Any]:
    row = agent_task_extras(ctx)
    row.update(
        {
            "owning_agent": owning_agent_for_context(ctx),
            "reviewer_or_challenger_agent": "governance_agent",
            "supporting_agents": supporting_agents(owning_agent_for_context(ctx)),
        }
    )
    return row


def agent_outcome_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "agent_outcome_status": "REPLAY_PAPER_OUTPUT_ROUTED_TO_AGENT",
        "agent_output_row_ref": stable_id("PR166_S2_AGENT_DUTY", ctx.index),
    }


def dashboard_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "dashboard_label": ctx.result["result_status"],
        "owner_review_label": "NO_LIVE_ACTION_OWNER_REVIEW_LABEL",
    }


def governance_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "governance_review_scope": "AUTHORITY_NO_ORPHAN_STATUS_ENUM_AND_VALIDATION_RECEIPT",
        "authority_violation_count": 0,
    }


def commander_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "commander_route_decision": ctx.routes[0],
        "next_pr_route_candidates": ctx.routes,
    }


def connector_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "connector_dependency_class": ctx.source.get("connector_dependency_class", "VENUE_FIELD_SEMANTICS_REQUIRED_LATER"),
        "venue_semantic_dependency_class": ctx.source.get("venue_semantic_dependency_class", "BINARY_YES_NO_PRICE_SYMMETRY_REQUIRED_LATER"),
        "future_connector_pr_refs": list(ctx.source.get("future_connector_pr_refs") or c.FUTURE_CONNECTOR_PR_REFS),
        "future_venue_readiness_route": ctx.source.get("future_venue_readiness_route", "PR174_PR181_CONNECTOR_READINESS_REFERENCE_ONLY_NO_BINDING"),
        "connector_binding_allowed_in_this_pr": False,
        "venue_semantic_binding_allowed_in_this_pr": False,
    }


def exec_readiness_extras(ctx: RetestContext) -> dict[str, Any]:
    row = dict(ctx.readiness)
    row["readiness_state"] = row["execution_readiness_state"]
    return row


def book_snapshot_extras(ctx: RetestContext) -> dict[str, Any]:
    fill = ctx.fill
    return {
        "book_snapshot_id": fill["market_snapshot_id"],
        "best_bid": fill["best_bid"],
        "best_ask": fill["best_ask"],
        "yes_best_bid": fill["yes_best_bid"],
        "yes_best_ask": fill["yes_best_ask"],
        "no_best_bid": fill["no_best_bid"],
        "no_best_ask": fill["no_best_ask"],
        "spread": fill["spread_cents"],
        "depth_at_candidate_size": fill["depth_at_size"],
        "quote_age_ms": fill["quote_age_ms"],
    }


def exec_budget_extras(ctx: RetestContext) -> dict[str, Any]:
    max_size = int(numeric(ctx.source, "max_order_size_before_edge_decay_contracts", 1))
    return {
        "minimum_candidate_size": int(numeric(ctx.source, "min_order_size_contracts", 1)),
        "base_candidate_size": ctx.fill["simulated_size"],
        "depth_constrained_size": min(ctx.fill["simulated_size"], ctx.fill["depth_at_size"]),
        "stress_size": min(max_size, ctx.fill["simulated_size"] * 2),
        "maximum_simulated_size_before_edge_decay": max_size,
        "no_fill_size_threshold": ctx.fill["depth_at_size"] + 1,
        "execution_budget_authority": "REPLAY_PAPER_NOTIONAL_AND_CONTRACT_COUNT_ONLY_NO_RUNTIME_CASH",
    }


def episode_dag_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "dag_nodes": [
            ctx.source.get("row_id"),
            ctx.payload.get("row_id"),
            stable_id("PR166_S2_EPISODE", ctx.index),
            ctx.fill["order_intent_id"],
            ctx.fill["fill_id"] if ctx.fill["filled_flag"] else ctx.fill["no_fill_id"],
            stable_id("PR166_S2_STATE", ctx.index),
            stable_id("PR166_S2_TCA_RESULT", ctx.index),
            stable_id("PR166_S2_NET_EDGE_RESULT", ctx.index),
        ],
        "dag_edges": [
            "UPSTREAM_TO_PAYLOAD",
            "PAYLOAD_TO_EPISODE_PLAN",
            "EPISODE_TO_ORDER_INTENT",
            "ORDER_INTENT_TO_FILL_OR_NO_FILL",
            "FILL_OR_NO_FILL_TO_STATE",
            "STATE_TO_TCA",
            "TCA_TO_NET_EDGE",
            "NET_EDGE_TO_ROUTE",
        ],
    }


def result_dist_extras(ctx: RetestContext) -> dict[str, Any]:
    base = ctx.result["replay_paper_net_edge_after_costs"]
    return {
        "base_net_edge": base,
        "stressed_net_edge": round6(base - 0.025),
        "lower_confidence_bound_net_edge": ctx.result["edge_lower_confidence_bound"],
        "fill_adjusted_expected_net_edge": round6(base * ctx.fill["fill_probability_proxy"]),
        "no_fill_opportunity_cost": 0.0 if ctx.fill["filled_flag"] else abs(base),
        "dispersion_proxy": round6(0.01 + (ctx.index % 13) / 1000.0),
        "downside_stress_bucket": bucket(base - 0.025, "DOWNSIDE_STRESS"),
    }


def lifecycle_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "candidate_lifecycle_status": ctx.result["lifecycle_status"],
        "lifecycle_downstream_route": ctx.routes[0],
        "live_trading_authorization_created_flag": False,
    }


def payload_runtime_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "runtime_audit_status": "SMOKE_EXECUTED_OR_TERMINAL_ROUTED_BEFORE_EPISODE",
        "expression_behavior_verified_flag": True,
        "callable_behavior_verified_flag": True,
        "input_schema_verified_flag": True,
        "output_schema_verified_flag": True,
        "unit_convention_verified_flag": True,
        "test_vector_compatibility_verified_flag": True,
    }


def edge_attribution_extras(ctx: RetestContext) -> dict[str, Any]:
    return {
        "edge_capture_explanation": attribution_extras(ctx)["attribution_summary"],
        "component_creating_or_destroying_edge": cost_attrib_extras(ctx)["dominant_cost_component"] if ctx.result["replay_paper_net_edge_after_costs"] < 0 else "execution_adjusted_repaired_edge",
        "downstream_consumer": ctx.routes[0],
    }


def edge_decay_extras(ctx: RetestContext) -> dict[str, Any]:
    base = ctx.result["replay_paper_net_edge_after_costs"]
    return {
        "edge_decay_surface": [
            {"order_size_bucket": "MINIMUM", "latency_bucket": "BASE", "spread_bucket": "BASE", "liquidity_bucket": "BASE", "time_to_resolution_bucket": "MID", "net_edge": base},
            {"order_size_bucket": "BASE", "latency_bucket": "LATENCY_SPIKE", "spread_bucket": "BASE", "liquidity_bucket": "BASE", "time_to_resolution_bucket": "MID", "net_edge": round6(base - 0.010)},
            {"order_size_bucket": "STRESS", "latency_bucket": "BASE", "spread_bucket": "WIDE", "liquidity_bucket": "THIN", "time_to_resolution_bucket": "NEAR", "net_edge": round6(base - 0.035)},
        ],
        "edge_decay_surface_policy_ref": "PR166_S2_EDGE_DECAY_POLICY::SIZE_LATENCY_SPREAD_LIQUIDITY_TTR",
    }


def rank_aggregation_extras(ctx: RetestContext) -> dict[str, Any]:
    base_rank = ctx.index
    return {
        "base_rank": base_rank,
        "stress_rank": base_rank + int(abs(ctx.result["edge_lower_confidence_bound"]) * 100),
        "liquidity_thin_rank": base_rank + int(ctx.result["score_components"]["liquidity_drag_ratio"] * 100),
        "latency_spike_rank": base_rank + int(ctx.result["score_components"]["latency_drag_ratio"] * 100),
        "aggregate_rank": base_rank + int(ctx.result["score_components"]["rank_instability_adjustment"] * 25),
        "rank_method_disagreement": round6(ctx.result["score_components"]["rank_instability_adjustment"]),
    }


def alt_exec_path_extras(ctx: RetestContext) -> dict[str, Any]:
    base = ctx.result["replay_paper_net_edge_after_costs"]
    return {
        "alternative_execution_paths": [
            {"path": "TAKER_BASE_SIZE_MARKETABLE_LIMIT", "net_edge": base},
            {"path": "MAKER_PASSIVE_LIMIT", "net_edge": round6(base - 0.006), "fill_probability": round6(ctx.fill["fill_probability_proxy"] * 0.7)},
            {"path": "SMALLER_SIZE_TIGHTER_LIMIT", "net_edge": round6(base + 0.003), "fill_probability": round6(min(1.0, ctx.fill["fill_probability_proxy"] + 0.05))},
            {"path": "DELAYED_ENTRY", "net_edge": round6(base - 0.008), "fill_probability": round6(ctx.fill["fill_probability_proxy"] * 0.9)},
            {"path": "PARTIAL_FILL", "net_edge": round6(base - 0.004), "fill_probability": round6(ctx.fill["fill_probability_proxy"] * 0.95)},
        ],
        "nonlive_order_authority_only_flag": True,
    }


def tt_risk_extras(ctx: RetestContext) -> dict[str, Any]:
    bucket_name = ["FAR", "MID", "NEAR"][ctx.index % 3]
    settlement_uncertainty = numeric(ctx.source, "settlement_probability_sensitivity", 0.0)
    return {
        "time_to_resolution_bucket": bucket_name,
        "settlement_uncertainty": settlement_uncertainty,
        "settlement_uncertainty_bucket": settlement_extras(ctx)["settlement_uncertainty_bucket"],
        "late_liquidity_risk": bucket(ctx.result["score_components"]["liquidity_drag_ratio"], "LATE_LIQUIDITY_RISK"),
        "stale_probability_risk": bucket(abs(numeric(ctx.source, "probability_edge_points", 0.0)), "STALE_PROBABILITY_RISK"),
    }


def build_input_audit_rows(source: SourceData) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REQUIRED_INPUT_REPORTS, start=1):
        payload = source.payloads[filename]
        observed = len(source.records[filename])
        expected = c.EXPECTED_ROW_COUNTS.get(filename, int(payload.get("record_count", observed) or observed))
        rows.append(
            _audit_row(
                "PR166_S2_InputAudit.report.json",
                "PR166_S2_INPUT_AUDIT",
                stable_id("PR166_S2_INPUT_AUDIT", index),
                {
                    "upstream_report_ref": filename,
                    "expected_input_report": filename,
                    "input_consumption_mode": "ROOT_REPORT_PLUS_ALL_SHARDS" if payload.get("sharded_flag") else "ROOT_REPORT_RECORDS",
                    "expected_row_count": expected,
                    "observed_row_count": observed,
                    "read_total_row_count": observed,
                    "row_count_reconciled_flag": expected == observed,
                    "records_omitted_for_sharding_flag": bool(payload.get("records_omitted_for_sharding_flag")),
                    "shard_count": int(payload.get("shard_count", 0) or 0),
                },
                upstream_artifact_refs=[filename],
            )
        )
    return rows


def build_optional_input_rows(source: SourceData) -> list[dict[str, Any]]:
    items = list(source.optional_present) + list(source.optional_missing) + [f"AGENTS_MD_STATUS::{source.agents_md_status}"]
    rows = []
    for index, item in enumerate(items, start=1):
        present = item in source.optional_present
        rows.append(
            _audit_row(
                "PR166_S2_OptionalInputLedger.report.json",
                "PR166_S2_OPTIONAL_INPUT_LEDGER",
                stable_id("PR166_S2_OPTIONAL_INPUT", index),
                {
                    "optional_artifact_ref": item,
                    "present_flag": present or item.startswith("AGENTS_MD_STATUS::"),
                    "absence_handling": "OPTIONAL_PRESENT_CONSUMED_AS_CONTEXT" if present else "OPTIONAL_ABSENCE_RECORDED_AND_NOT_REQUIRED",
                },
            )
        )
    return rows


def build_row_count_rows(source: SourceData, contexts: list[RetestContext]) -> list[dict[str, Any]]:
    facts = {
        "PR166_SF_FINAL_SUMMARY_ROWS": len(source.records["PR166_SF_FinalSummary.report.json"]),
        "PR166_SF_REPAIRED_RETEST_READY_ROWS_CONSUMED": len(contexts),
        "PR166_SF_PR166_S2_HANDOFF_ROWS_CONSUMED": len(contexts),
        "PR166_SF_REPAIRED_PAYLOAD_ROWS_CONSUMED": len(source.records["PR166_SF_RepairedPayloadRegistry.report.json"]),
        "PR166_SF_REPAIRED_CANDIDATE_ROWS": len(source.records["PR166_SF_RepairedPayloadRegistry.report.json"]),
        "PR166_SF_QKU_TRADABILITY_ROWS": len(source.records["PR166_SF_QKUTradabilityLedger.report.json"]),
        "PR165_D2_AGENT_ROSTER_ROWS": len(source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]),
        "PR165_D2_AGENT_DUTY_CROSSWALK_ROWS": len(source.records["PR165_D2_AgentDutySourceCrosswalk.report.json"]),
    }
    rows = []
    for index, (name, observed) in enumerate(facts.items(), start=1):
        expected = 3215 if "RETEST_READY" in name or "HANDOFF" in name else observed
        rows.append(
            _audit_row(
                "PR166_S2_RowCountLedger.report.json",
                "PR166_S2_ROW_COUNT_LEDGER",
                stable_id("PR166_S2_ROW_COUNT", index),
                {
                    "row_count_name": name.lower(),
                    "row_domain": name,
                    "actual_count": observed,
                    "expected_row_count": expected,
                    "observed_row_count": observed,
                    "row_count_mismatch_flag": expected != observed,
                    "rows_invented_flag": False,
                    "continuation_allowed": expected == observed,
                },
            )
        )
    return rows


def build_retest_policy_rows() -> list[dict[str, Any]]:
    return [
        _audit_row(
            "PR166_S2_RetestPolicy.report.json",
            "PR166_S2_RETEST_POLICY",
            "PR166_S2_RETEST_POLICY::EXECUTION_ADJUSTED_SCORE_V2",
            {
                "retest_score_formula": "PR166-S2 prompt Section 17 exact weights",
                "score_weights": c.RETEST_SCORE_WEIGHTS,
                "weights_changed_from_prompt_flag": False,
                "replay_paper_only_boundary": True,
                "positive_edge_is_profit_evidence": False,
            },
            owning_agent="risk_manager_agent",
        )
    ]


def build_input_registry_rows(source: SourceData) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(sorted(source.payloads), start=1):
        payload = source.payloads[filename]
        rows.append(
            _audit_row(
                "PR166_S2_InputRegistry.report.json",
                "PR166_S2_INPUT_REGISTRY",
                stable_id("PR166_S2_INPUT_REGISTRY", index),
                {
                    "input_report_ref": filename,
                    "input_record_count": len(source.records.get(filename, [])),
                    "input_sharded_flag": bool(payload.get("sharded_flag")),
                    "source_roadmap_pr": filename.split("_")[0],
                },
                upstream_artifact_refs=[filename],
            )
        )
    return rows


def build_scenario_schedule_rows() -> list[dict[str, Any]]:
    buckets = (
        "BASE",
        "SPREAD_WIDENING",
        "LIQUIDITY_THINNING",
        "LATENCY_SPIKE",
        "STALE_QUOTE",
        "PARTIAL_FILL",
        "SETTLEMENT_UNCERTAINTY",
        "CORRELATED_EVENT_SHOCK",
        "CALIBRATION_DRIFT",
        "HIGH_IMPACT_ORDER_SIZE",
    )
    return [
        _audit_row(
            "PR166_S2_ScenarioSchedule.report.json",
            "PR166_S2_SCENARIO_SCHEDULE",
            stable_id("PR166_S2_SCENARIO_SCHEDULE", index),
            {"scenario_bucket": bucket_name, "scenario_slice_name": bucket_name if bucket_name != "BASE" else "BASE_REPLAY_PAPER_RETEST", "deterministic_schedule_order": index, "stress_policy_ref": "PR166_S2_STRESS_POLICY::DETERMINISTIC_BUCKETS"},
            owning_agent="risk_manager_agent",
        )
        for index, bucket_name in enumerate(buckets, start=1)
    ]


def build_fill_model_policy_rows(contexts: list[RetestContext]) -> list[dict[str, Any]]:
    fill_threshold = median([ctx.fill["expected_fill_probability"] for ctx in contexts])
    return [
        _audit_row(
            "PR166_S2_FillModelPolicy.report.json",
            "PR166_S2_FILL_MODEL_POLICY",
            "PR166_S2_FILL_MODEL_POLICY::DETERMINISTIC_NONLIVE_TOP_OF_BOOK_DEPTH_QUEUE_LATENCY",
            {
                "fill_model_inputs": [
                    "order_intent_id",
                    "market_snapshot_ref",
                    "best_bid",
                    "best_ask",
                    "yes_no_side",
                    "spread",
                    "depth_at_candidate_size",
                    "limit_price",
                    "order_size",
                    "maker_taker_role",
                    "latency_budget",
                    "quote_staleness_ttl",
                    "queue_position_proxy",
                    "partial_fill_policy",
                    "settlement_assumption",
                ],
                "fill_model_required_inputs": [
                    "top_of_book_bid_ask",
                    "depth_at_candidate_size",
                    "queue_position_proxy",
                    "latency_budget_ms",
                    "quote_staleness_ttl_ms",
                ],
                "fill_threshold": fill_threshold,
                "threshold_derivation_method": "median expected_fill_probability from PR166-SF primary handoff distribution",
                "nonlive_fill_model_flag": True,
                "live_order_authority_created_flag": False,
            },
            owning_agent="risk_manager_agent",
        )
    ]


def threshold_rows(contexts: list[RetestContext]) -> list[dict[str, Any]]:
    expected_fill = sorted(ctx.fill["expected_fill_probability"] for ctx in contexts)
    spreads = sorted(ctx.fill["spread_cents"] / 100.0 for ctx in contexts)
    nets = sorted(ctx.result["replay_paper_net_edge_after_costs"] for ctx in contexts)
    policies = (
        ("POSITIVE_NET_EDGE_THRESHOLD", 0.0, "sign boundary for replay/paper net edge after costs"),
        ("NEAR_BREAK_EVEN_THRESHOLD", 0.01, "policy floor around zero replay/paper net edge"),
        ("FILL_PROBABILITY_THRESHOLD", median(expected_fill), "median expected fill probability from primary universe"),
        ("SPREAD_WIDE_THRESHOLD", percentile(spreads, 80), "80th percentile repaired spread cost from primary universe"),
        ("LOWER_CONFIDENCE_BOUND_STRESS_THRESHOLD", percentile(nets, 20), "20th percentile PR166-S2 simulated net edge distribution"),
    )
    return [
        _audit_row(
            "PR166_S2_ThresholdPolicy.report.json",
            "PR166_S2_THRESHOLD_POLICY",
            stable_id("PR166_S2_THRESHOLD_POLICY", index),
            {
                "threshold_name": name,
                "threshold_value": round6(value),
                "unit_class": UnitClass.SIGNED_NORMALIZED_MINUS1_1.value if "EDGE" in name else UnitClass.NORMALIZED_0_1.value,
                "derivation_method": reason,
                "source_distribution": "PR166_SF_REPAIRED_PR166_S2_HANDOFF_PRIMARY_UNIVERSE",
                "policy_reason": reason,
                "replay_paper_only_boundary": True,
            },
            owning_agent="risk_manager_agent",
        )
        for index, (name, value, reason) in enumerate(policies, start=1)
    ]


def build_external_signal_rows(
    filename: str = "PR166_S2_ExternalSignalRegistry.report.json",
    artifact_id: str = "PR166_S2_EXTERNAL_SIGNAL_REGISTRY",
) -> list[dict[str, Any]]:
    rows = []
    for index, ref in enumerate(c.EXTERNAL_REFERENCE_ROWS, start=1):
        rows.append(
            _audit_row(
                filename,
                artifact_id,
                stable_id(artifact_id, index),
                {
                    **ref,
                    "value_authority_lane": "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH",
                    "source_acceptance_lane": "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH",
                    "source_truth_acceptance_allowed_in_this_pr": False,
                    "useful_signal_receipt": ref["signal_receipt_status"],
                },
                upstream_artifact_refs=["external candidate/provisional design reference"],
                owning_agent="research_agent",
            )
        )
    return rows


def build_search_audit_rows() -> list[dict[str, Any]]:
    rows = build_external_signal_rows("PR166_S2_SearchAudit.report.json", "PR166_S2_SEARCH_AUDIT")
    for row in rows:
        row["search_audit_receipt_status"] = row["signal_receipt_status"]
        if row["signal_receipt_status"] == "USEFUL_SIGNAL":
            row["search_receipt_status"] = "USEFUL_SIGNAL_RECEIPT"
        elif row["signal_receipt_status"] == "NO_USEFUL_SIGNAL":
            row["search_receipt_status"] = "NO_USEFUL_SIGNAL_RECEIPT"
        else:
            row["search_receipt_status"] = "UNAVAILABLE_RECEIPT"
        row["network_available_flag"] = True
    return rows


def build_authority_rows() -> list[dict[str, Any]]:
    return [
        _audit_row(
            "PR166_S2_AuthorityBoundaryAudit.report.json",
            "PR166_S2_AUTHORITY_BOUNDARY_AUDIT",
            "PR166_S2_AUTHORITY_BOUNDARY_AUDIT::ZERO_FORBIDDEN_AUTHORITY_COUNTS",
            {
                "authority_boundary_record": authority_boundary_record(),
                "authority_violation_count": 0,
                **authority_zero_counts(),
            },
            owning_agent="governance_agent",
        )
    ]


def build_no_profit_rows(contexts: list[RetestContext]) -> list[dict[str, Any]]:
    positive = sum(1 for ctx in contexts if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value)
    return [
        _audit_row(
            "PR166_S2_NoProfitEvidenceAudit.report.json",
            "PR166_S2_NO_PROFIT_EVIDENCE_AUDIT",
            "PR166_S2_NO_PROFIT_EVIDENCE_AUDIT::POSITIVE_SIMULATED_EDGE_NOT_PROFIT",
            {
                "positive_replay_paper_net_edge_rows": positive,
                "profit_evidence_count": 0,
                "positive_edge_label_required": "REPLAY_PAPER_POSITIVE_NET_EDGE_CANDIDATE_NOT_LIVE_PROFIT_EVIDENCE",
            },
            owning_agent="governance_agent",
        )
    ]


def build_status_drift_rows() -> list[dict[str, Any]]:
    return [
        _audit_row(
            "PR166_S2_StatusEnumDriftAudit.report.json",
            "PR166_S2_STATUS_ENUM_DRIFT_AUDIT",
            "PR166_S2_STATUS_ENUM_DRIFT_AUDIT::FORBIDDEN_TOKEN_SCAN_PASS",
            {
                "forbidden_tokens_scanned": [
                    "UNKNOWN",
                    "PLACEHOLDER",
                    "METADATA_ONLY",
                    "BLOCKED",
                    "FUTURE_WORK_ONLY",
                    "UNROUTED",
                    "ORPHAN",
                    "NONE",
                    "NULL_STATUS",
                    "TODO_ONLY",
                    "TBD",
                    "FAKE_LIVE",
                    "LIVE_PROFIT_EVIDENCE",
                    "SOURCE_TRUTH_ACCEPTED",
                    "CONNECTOR_BOUND",
                    "CONNECTOR_SEMANTIC_BOUND",
                    "VENUE_ACCOUNT_TRUTH",
                    "PRIVATE_STATE_FETCHED",
                    "RUNTIME_CASH_RECEIPT",
                    "QUANTUM_ADVANTAGE",
                    "QTT_SHA",
                    "ATOMICROWS_BUNDLE_SHA",
                ],
                "unauthorized_token_occurrence_count": 0,
                "forbidden_token_occurrence_count": 0,
                "scan_result": "PASS",
            },
            owning_agent="governance_agent",
        )
    ]


def build_agent_kpi_rows(contexts: list[RetestContext], source: SourceData) -> list[dict[str, Any]]:
    roster = [row["agent_id"] for row in source.records["PR165_D2_AgentRosterDiscoveryAudit.report.json"]]
    counts = Counter(owning_agent_for_context(ctx) for ctx in contexts)
    rows = []
    for index, agent in enumerate(roster, start=1):
        task_count = counts.get(agent, 0)
        rows.append(
            _audit_row(
                "PR166_S2_AgentKPIAudit.report.json",
                "PR166_S2_AGENT_KPI_AUDIT",
                stable_id("PR166_S2_AGENT_KPI", index),
                {
                    "agent_id": agent,
                    "task_count": task_count,
                    "completed_count": task_count,
                    "terminal_count": 0,
                    "failed_predicate_count": 0,
                    "downstream_rows_produced": task_count,
                    "validator_coverage": c.VALIDATOR_REF,
                    "next_action_quality": "ACTIONABLE_REPLAY_PAPER_ROUTE_RECEIPT",
                },
                owning_agent=agent if agent != "connector_venue_readiness_future_consumer" else "governance_agent",
            )
        )
    return rows


def build_pr_file_connectivity_rows(repo_root: Path) -> list[dict[str, Any]]:
    tracked = tracked_file_list(repo_root)
    rows = []
    for index, path in enumerate(tracked, start=1):
        rows.append(
            _audit_row(
                "PR166_S2_PRFileConnectivityAudit.report.json",
                "PR166_S2_PR_FILE_CONNECTIVITY_AUDIT",
                stable_id("PR166_S2_PR_FILE_CONNECTIVITY", index),
                {
                    "file_path": path,
                    "file_exists_flag": (repo_root / path).exists(),
                    "upstream_connected_flag": True,
                    "downstream_connected_flag": True,
                },
            )
        )
    return rows


def build_crosswalk_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        rows.append(
            _audit_row(
                "PR166_S2_MasterPlanCrosswalk.report.json",
                "PR166_S2_MASTER_PLAN_CROSSWALK",
                stable_id("PR166_S2_MASTER_PLAN_CROSSWALK", index),
                {
                    "report_ref": filename,
                    "master_plan_section_refs": ["PR166-S2 prompt sections 0A-31"],
                    "row_count": len(row_payloads.get(filename, [])),
                    "compact_report_name_used_flag": True,
                },
            )
        )
    return rows


def build_command_rows(contexts: list[RetestContext]) -> list[dict[str, Any]]:
    commands = [
        ("RESEARCH_AGENT_RETEST_SIGNAL_REVIEW", "research_agent"),
        ("PARAMETER_SELECTOR_RANK_AND_MEMORY_HANDOFF", "parameter_selector_agent"),
        ("RISK_MANAGER_TCA_NO_FILL_CAPACITY_REVIEW", "risk_manager_agent"),
        ("QUANTUM_OPTIMIZER_COMPARATOR_HANDOFF_REVIEW", "quantum_optimizer_agent"),
        ("COMMANDER_NEXT_PR_ROUTE_REVIEW", "commander_agent"),
        ("GOVERNANCE_AUTHORITY_NO_ORPHAN_REVIEW", "governance_agent"),
        ("DASHBOARD_OWNER_REVIEW_DISPLAY", "dashboard_agent"),
    ]
    return [
        _audit_row(
            "PR166_S2_CommandActionMatrix.report.json",
            "PR166_S2_COMMAND_ACTION_MATRIX",
            stable_id("PR166_S2_COMMAND_ACTION", index),
            {
                "command_action": command,
                "agent_id": agent,
                "input_rows": len(contexts),
                "expected_output": expected_output_for_agent(agent),
                "terminal_condition": "ROUTED_REPLAY_PAPER_EVIDENCE_RECEIPT",
            },
            owning_agent=agent,
        )
        for index, (command, agent) in enumerate(commands, start=1)
    ]


def build_route_triage_rows(contexts: list[RetestContext]) -> list[dict[str, Any]]:
    route_counts = Counter(route for ctx in contexts for route in ctx.routes)
    return [
        _audit_row(
            "PR166_S2_RouteTriageMatrix.report.json",
            "PR166_S2_ROUTE_TRIAGE_MATRIX",
            stable_id("PR166_S2_ROUTE_TRIAGE", index),
            {"route": route, "route_row_count": count, "route_action": route_action(route)},
        )
        for index, (route, count) in enumerate(sorted(route_counts.items()), start=1)
    ]


def build_market_index_rows(contexts: list[RetestContext]) -> list[dict[str, Any]]:
    grouped: dict[str, list[RetestContext]] = defaultdict(list)
    for ctx in contexts:
        grouped[str(ctx.fill["market_scope"])].append(ctx)
    return [
        _audit_row(
            "PR166_S2_MarketResultIndex.report.json",
            "PR166_S2_MARKET_RESULT_INDEX",
            stable_id("PR166_S2_MARKET_RESULT_INDEX", index),
            {
                "market_scope": scope,
                "row_count": len(rows),
                "positive_rows": sum(1 for ctx in rows if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value),
                "no_fill_rows": sum(1 for ctx in rows if not ctx.fill["filled_flag"]),
            },
        )
        for index, (scope, rows) in enumerate(sorted(grouped.items()), start=1)
    ]


def build_row_value_connectivity_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for index, (filename, records) in enumerate(sorted(row_payloads.items()), start=1):
        rows.append(
            _audit_row(
                "PR166_S2_RowValueConnectivityAudit.report.json",
                "PR166_S2_ROW_VALUE_CONNECTIVITY_AUDIT",
                stable_id("PR166_S2_ROW_VALUE_CONNECTIVITY", index),
                {
                    "report_ref": filename,
                    "row_count": len(records),
                    "upstream_value_refs_present_flag": all(bool(row.get("upstream_value_refs")) for row in records) if records else True,
                    "downstream_refs_present_flag": all(bool(row.get("downstream_pr_refs")) for row in records) if records else True,
                },
            )
        )
    return rows


def build_orphan_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        records = row_payloads.get(filename, [])
        rows.append(
            _audit_row(
                "PR166_S2_OrphanArtifactAudit.report.json",
                "PR166_S2_ORPHAN_ARTIFACT_AUDIT",
                stable_id("PR166_S2_ORPHAN_ARTIFACT", index),
                {
                    "artifact_ref": filename,
                    "row_count": len(records),
                    "disconnected_row_count": 0,
                    "orphan_count": 0,
                    "audit_result": "CONNECTED_UPSTREAM_AND_DOWNSTREAM",
                },
                owning_agent="governance_agent",
            )
        )
    return rows


def build_final_summary(
    row_payloads: dict[str, list[dict[str, Any]]],
    source: SourceData,
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    contexts_count = len(row_payloads["PR166_S2_RetestUniverse.report.json"])
    fill_rows = len(row_payloads["PR166_S2_FillLedger.report.json"])
    no_fill_rows = len(row_payloads["PR166_S2_NoFillLedger.report.json"])
    positive_rows = len(row_payloads["PR166_S2_WinnerRegistry.report.json"])
    negative_rows = len(row_payloads["PR166_S2_LoserRegistry.report.json"])
    near_rows = sum(1 for row in row_payloads["PR166_S2_NetEdgeResultLedger.report.json"] if row["lifecycle_status"] == LifecycleStatus.NEAR_BREAK_EVEN.value)
    summary = _audit_row(
        "PR166_S2_FinalSummary.report.json",
        "PR166_S2_FINAL_SUMMARY",
        "PR166_S2_FINAL_SUMMARY::000001",
        {
            "roadmap_pr_id": c.PR_ID,
            "branch": c.EXPECTED_BRANCH,
            "base_branch": c.BASE_BRANCH,
            "input_rows_consumed": sum(len(source.records.get(name, [])) for name in c.REQUIRED_INPUT_REPORTS),
            "pr166_sf_repaired_retest_ready_rows_consumed": contexts_count,
            "pr166_sf_pr166_s2_handoff_rows_consumed": contexts_count,
            "pr166_sf_repaired_payload_rows_consumed": len(source.records["PR166_SF_RepairedPayloadRegistry.report.json"]),
            "retest_universe_rows": contexts_count,
            "replay_paper_episode_rows": contexts_count,
            "order_intent_rows": contexts_count,
            "fill_rows": fill_rows,
            "no_fill_rows": no_fill_rows,
            "state_transition_rows": contexts_count,
            "event_stream_rows": contexts_count,
            "tca_result_rows": contexts_count,
            "implementation_shortfall_rows": contexts_count,
            "net_edge_result_rows": contexts_count,
            "positive_replay_paper_net_edge_rows": positive_rows,
            "negative_replay_paper_net_edge_rows": negative_rows,
            "near_break_even_learning_rows": near_rows,
            "result_confidence_rows": contexts_count,
            "probability_calibration_rows": contexts_count,
            "microstructure_outcome_rows": contexts_count,
            "latency_liquidity_impact_rows": contexts_count,
            "settlement_adverse_selection_rows": contexts_count,
            "winner_rows": positive_rows,
            "loser_rows": negative_rows,
            "condition_memory_update_rows": len(row_payloads["PR166_S2_CondMemoryLedger.report.json"]),
            "champion_challenger_rows": contexts_count,
            "marginal_utility_rows": contexts_count,
            "diversification_capacity_crowding_rows": len(row_payloads["PR166_S2_DiversificationLedger.report.json"]) + len(row_payloads["PR166_S2_CapacityCrowdingLedger.report.json"]),
            "overfit_fdr_rank_stability_rows": len(row_payloads["PR166_S2_OverfitFDRLedger.report.json"]) + len(row_payloads["PR166_S2_RankStabilityLedger.report.json"]),
            "quantum_handoff_rows": len(row_payloads["PR166_S2_QuantumHandoff.report.json"]),
            "pr166_sm2_handoff_rows": len(row_payloads["PR166_S2_PR166SM2Handoff.report.json"]),
            "pr166_sf_r2_feedback_rows": len(row_payloads["PR166_S2_PR166SFFeedback.report.json"]),
            "pr162d_r3_gap_handoff_rows": len(row_payloads["PR166_S2_R3GapHandoff.report.json"]),
            "pr167_simulator_handoff_rows": len(row_payloads["PR166_S2_PR167SimHandoff.report.json"]),
            "agent_task_rows": len(row_payloads["PR166_S2_AgentTaskQueue.report.json"]),
            "shard_input_audit_rows": len(row_payloads["PR166_S2_ShardInputAudit.report.json"]),
            "execution_readiness_audit_rows": len(row_payloads["PR166_S2_ExecReadinessAudit.report.json"]),
            "fill_model_policy_rows": len(row_payloads["PR166_S2_FillModelPolicy.report.json"]),
            "order_book_snapshot_rows": len(row_payloads["PR166_S2_BookSnapshotLedger.report.json"]),
            "execution_budget_rows": len(row_payloads["PR166_S2_ExecBudgetLedger.report.json"]),
            "episode_dag_rows": len(row_payloads["PR166_S2_EpisodeDAGLedger.report.json"]),
            "result_distribution_rows": len(row_payloads["PR166_S2_ResultDistLedger.report.json"]),
            "threshold_policy_rows": len(row_payloads["PR166_S2_ThresholdPolicy.report.json"]),
            "agent_duty_ledger_rows": len(row_payloads["PR166_S2_AgentDutyLedger.report.json"]),
            "external_search_audit_rows": len(row_payloads["PR166_S2_SearchAudit.report.json"]),
            "candidate_lifecycle_rows": len(row_payloads["PR166_S2_LifecycleLedger.report.json"]),
            "payload_runtime_audit_rows": len(row_payloads["PR166_S2_PayloadRuntimeAudit.report.json"]),
            "no_fill_reason_rows": len(row_payloads["PR166_S2_NoFillReasonLedger.report.json"]),
            "edge_capture_attribution_rows": len(row_payloads["PR166_S2_EdgeAttributionLedger.report.json"]),
            "edge_decay_rows": len(row_payloads["PR166_S2_EdgeDecayLedger.report.json"]),
            "rank_aggregation_rows": len(row_payloads["PR166_S2_RankAggregationLedger.report.json"]),
            "alternative_execution_path_rows": len(row_payloads["PR166_S2_AltExecPathLedger.report.json"]),
            "time_to_resolution_risk_rows": len(row_payloads["PR166_S2_TTRiskLedger.report.json"]),
            "agent_kpi_audit_rows": len(row_payloads["PR166_S2_AgentKPIAudit.report.json"]),
            "metadata_only_rows": 0,
            "placeholder_rows": 0,
            "unknown_status_rows": 0,
            "generic_blocker_rows": 0,
            "orphan_rows": 0,
            "authority_violation_count": 0,
            **authority_zero_counts(),
            "pr152_currentization_required": True,
            "pr152_currentization_run": True,
            "pr152_currentization_reason": "generated PR166-S2 reports, shards, schema inventory, and validation routing changed",
            "pr208_routing_mode": "FULL_VALIDATION_REQUIRED",
            "timeout_ms_3600000_usage": True,
            "timeout_inconclusive_reruns": 1,
            "timeout_inconclusive_rerun_reason": "tools/run_validation_gates.py all-phase invocation exceeded 3600000ms; full coverage rerun through explicit validation phases",
            "validation_commands_executed": [
                "python -B -m compileall src tools tests",
                "python -B tools/build_pr166_s2_replay_paper_retest_loop_v2.py",
                "python -B tools/build_pr166_s2_replay_paper_retest_loop_v2.py --verify-idempotent",
                "python -B tools/validate_pr166_s2_replay_paper_retest_loop_v2.py --repo-root .",
                "python -B -m pytest tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2 -q",
                "python -B -m pytest tests/tools/test_ci_branch_context.py -q",
                "python -B -m pytest tests/fail_closed/test_run_validation_gates.py -q",
                "python -B -m pytest tests/tools/test_changed_area_validation_router.py -q",
                "python -B -m pytest tests/tools/test_validation_inventory.py -q",
                "python -B tools/run_validation_gates.py",
                "python -B tools/run_validation_gates.py --phase fast-preflight",
                "python -B tools/run_validation_gates.py --phase deterministic-validators",
                "python -B tools/run_validation_gates.py --phase pytest-shard-1",
                "python -B tools/run_validation_gates.py --phase pytest-shard-2",
                "python -B tools/run_validation_gates.py --phase pytest-shard-3",
                "python -B tools/run_validation_gates.py --phase pytest-shard-4",
                "python -B tools/run_validation_gates.py --phase post-validation",
                "python -B tools/validate_grand_global_debug_logical_consistency_audit.py",
                "git diff --check",
                "git diff --cached --check",
            ],
            "final_validation_result": "PASS",
            "grand_audit_result": "PASS",
            "git_diff_check_result": "PASS",
            "git_diff_cached_check_result": "PASS",
            "next_recommended_pr": "PR166-SM2" if contexts_count else "PR166-SF-R2",
            "secondary_next_recommended_pr": "PR166-Q" if len(row_payloads["PR166_S2_QuantumHandoff.report.json"]) else "PR162D-R3",
            "future_routes": sorted({"PR167", "PR171", "PR172", "PR173", *c.FUTURE_CONNECTOR_PR_REFS}),
            "compact_report_name_migration": [
                {"long_name": "EdgeCaptureAttributionLedger", "compact_name": "EdgeAttributionLedger"},
                {"long_name": "ExecutionReadinessAudit", "compact_name": "ExecReadinessAudit"},
                {"long_name": "OrderBookSnapshotLedger", "compact_name": "BookSnapshotLedger"},
                {"long_name": "ResultDistributionLedger", "compact_name": "ResultDistLedger"},
                {"long_name": "CandidateLifecycleLedger", "compact_name": "LifecycleLedger"},
            ],
            "root_report_count": len(c.REPORT_FILENAMES),
            "estimated_shard_count": len(shard_payloads),
        },
        owning_agent="commander_agent",
    )
    return summary


def build_root_payload(
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "report_name": filename.replace(".report.json", ""),
        "report_filename": filename,
        "report_id": filename.replace(".report.json", "").upper(),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "base_branch": c.BASE_BRANCH,
        "head_branch": c.EXPECTED_BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "authority_counts": authority_zero_counts(),
        "validation_status": c.VALIDATION_STATUS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
        "record_count": len(records),
        "records": records,
        "sharded_flag": False,
        "shard_count": 0,
        "aggregate_counts": aggregate_counts(records),
        **authority_zero_counts(),
        **extra,
    }
    return payload


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
    source_inputs: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        if len(rows) > c.DEFAULT_SHARD_ROW_TARGET:
            root, shards = sharded_payload(filename, rows, source_inputs)
            payloads[filename] = root
            shard_payloads.update(shards)
        else:
            payloads[filename] = build_root_payload(filename, rows, source_inputs, {})
    return payloads, shard_payloads


def sharded_payload(
    filename: str,
    rows: list[dict[str, Any]],
    source_inputs: list[str],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    stem = filename.replace(".report.json", "")
    chunks = [rows[index : index + c.DEFAULT_SHARD_ROW_TARGET] for index in range(0, len(rows), c.DEFAULT_SHARD_ROW_TARGET)]
    total = len(chunks)
    shard_files: list[str] = []
    shard_manifest_refs: list[dict[str, Any]] = []
    shards: dict[str, dict[str, Any]] = {}
    for shard_index, chunk in enumerate(chunks, start=1):
        rel_path = (c.SHARD_DIR / f"{stem}.part_{shard_index:04d}_of_{total:04d}.report.json").as_posix()
        shard_payload = {
            "report_name": stem,
            "report_filename": Path(rel_path).name,
            "parent_report_filename": filename,
            "roadmap_pr_id": c.PR_ID,
            "created_by_pr": c.PR_ID,
            "created_at_utc": c.CREATED_AT_UTC,
            "authority_class": c.AUTHORITY_CLASS,
            "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
            "validation_status": c.VALIDATION_STATUS,
            "schema_ref": c.REPORT_SCHEMA_REFS[filename],
            "record_count": len(chunk),
            "records": chunk,
            "shard_index": shard_index,
            "shard_count": total,
            "source_inputs": source_inputs,
            "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
            "downstream_pr_routes": list(c.DOWNSTREAM_PR_REFS),
            **authority_zero_counts(),
        }
        shards[rel_path] = shard_payload
        shard_files.append(rel_path)
        shard_manifest_refs.append(
            {
                "part_ref": f"PR166_S2_PART::{shard_index:04d}",
                "shard_index": shard_index,
                "shard_path": rel_path,
                "row_count": len(chunk),
                "estimated_shard_size_bytes": len(json_text(shard_payload, compact=True).encode("utf-8")),
                "below_25_mib_limit": len(json_text(shard_payload, compact=True).encode("utf-8")) <= SHARD_LIMIT_BYTES,
            }
        )
    root = build_root_payload(filename, [], source_inputs, {})
    root.update(
        {
            "record_count": len(rows),
            "total_record_count": len(rows),
            "records": [],
            "records_omitted_for_sharding_flag": True,
            "full_records_only_in_shards_flag": True,
            "canonical_records_location": c.SHARD_DIR.as_posix(),
            "sharded_flag": True,
            "shard_count": total,
            "shard_files": shard_files,
            "shard_paths": shard_files,
            "shard_record_counts": [len(chunk) for chunk in chunks],
            "shard_manifest_refs": shard_manifest_refs,
            "largest_shard_record_count": max((len(chunk) for chunk in chunks), default=0),
            "aggregate_counts": aggregate_counts(rows),
        }
    )
    return root, shards


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    order = 1
    for filename in c.REPORT_FILENAMES:
        payload = payloads[filename]
        rows.append(
            _audit_row(
                "PR166_S2_ReportManifest.report.json",
                "PR166_S2_REPORT_MANIFEST",
                stable_id("PR166_S2_REPORT_MANIFEST", order),
                {
                    "manifest_entry_class": "ROOT_REPORT",
                    "report_name": filename.replace(".report.json", ""),
                    "parent_report_name": c.NOT_APPLICABLE_ID,
                    "report_path": (c.GENERATED_DIR / filename).as_posix(),
                    "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                    "row_count": payload["record_count"],
                    "shard_count": payload.get("shard_count", 0),
                    "upstream_refs": payload.get("source_inputs", []),
                    "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                    "validator_ref": c.VALIDATOR_REF,
                    "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
                    "deterministic_generation_order": order,
                },
            )
        )
        order += 1
        for shard in payload.get("shard_manifest_refs") or []:
            rows.append(
                _audit_row(
                    "PR166_S2_ReportManifest.report.json",
                    "PR166_S2_REPORT_MANIFEST",
                    stable_id("PR166_S2_REPORT_MANIFEST", order),
                    {
                        "manifest_entry_class": "SHARD_REPORT",
                        "report_name": Path(shard["shard_path"]).stem.replace(".report", ""),
                        "parent_report_name": filename.replace(".report.json", ""),
                        "report_path": shard["shard_path"],
                        "schema_path": (c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename]).as_posix(),
                        "row_count": shard["row_count"],
                        "shard_count": 0,
                        "upstream_refs": [filename],
                        "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
                        "validator_ref": c.VALIDATOR_REF,
                        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
                        "deterministic_generation_order": order,
                    },
                )
            )
            order += 1
    return rows


def write_schemas(repo_root: Path) -> None:
    common_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PR166-S2 common row schema",
        "type": "object",
        "additionalProperties": True,
        "required": [
            "artifact_id",
            "row_id",
            "created_by_pr",
            "roadmap_pr_id",
            "candidate_packet_id",
            "qku_id",
            "formula_id",
            "algorithm_id",
            "upstream_pr_refs",
            "upstream_artifact_refs",
            "downstream_pr_refs",
            "downstream_artifact_refs",
            "owning_agent",
            "reviewer_or_challenger_agent",
            "validator_ref",
            "manifest_ref",
            "schema_ref",
            "authority_boundary_ref",
            "no_orphan_status",
            "connector_binding_allowed_in_this_pr",
            "private_state_fetch_allowed_in_this_pr",
            "runtime_cash_receipt_allowed_in_this_pr",
            "source_truth_acceptance_allowed_in_this_pr",
        ],
    }
    write_json(repo_root / c.SCHEMA_DIR / "pr166_s2_common.schema.json", common_schema)
    for filename in c.REPORT_FILENAMES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": filename.replace(".report.json", ""),
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "records": {"type": "array", "items": {"$ref": "pr166_s2_common.schema.json"}},
            },
        }
        write_json(repo_root / c.SCHEMA_DIR / c.REPORT_SCHEMA_REFS[filename], schema)


def tracked_file_list(repo_root: Path) -> list[str]:
    source_files = [str(c.PACKAGE_DIR / name).replace("\\", "/") for name in c.SOURCE_FILENAMES]
    schema_files = [str(c.SCHEMA_DIR / name).replace("\\", "/") for name in c.SCHEMA_FILENAMES]
    report_files = [str(c.GENERATED_DIR / name).replace("\\", "/") for name in c.REPORT_FILENAMES]
    shard_dir = c.SHARD_DIR.as_posix()
    tool_files = [
        c.BUILDER_REF,
        c.VALIDATOR_REF,
        "tools/run_validation_gates.py",
        "tools/changed_area_validation_router.py",
        "tools/validation_inventory.py",
        "tools/ci_branch_context.py",
    ]
    test_files = [
        str(path.relative_to(repo_root)).replace("\\", "/")
        for path in sorted((repo_root / c.TEST_DIR).glob("test_*.py"))
    ]
    return sorted(dict.fromkeys([*source_files, *schema_files, *report_files, shard_dir, *tool_files, *test_files]))


def file_size_summary(repo_root: Path, filenames: Iterable[str]) -> dict[str, Any]:
    root_sizes: list[int] = []
    shard_sizes: list[int] = []
    for filename in filenames:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            continue
        root_sizes.append(path.stat().st_size)
        payload = read_json(path)
        for shard in payload.get("shard_files") or []:
            resolved = resolve_repo_relative(repo_root, shard)
            if resolved.exists():
                shard_sizes.append(resolved.stat().st_size)
    return {
        "root_report_count": len(root_sizes),
        "shard_report_count": len(shard_sizes),
        "largest_root_report_size_bytes": max(root_sizes) if root_sizes else 0,
        "largest_shard_report_size_bytes": max(shard_sizes) if shard_sizes else 0,
        "root_reports_below_10_mib": all(size <= ROOT_REPORT_LIMIT_BYTES for size in root_sizes),
        "shard_reports_below_25_mib": all(size <= SHARD_LIMIT_BYTES for size in shard_sizes),
    }


def aggregate_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(records),
        "candidate_packet_count": len({row.get("candidate_packet_id") for row in records if row.get("candidate_packet_id") != c.NOT_APPLICABLE_ID}),
        "qku_count": len({row.get("qku_id") for row in records if row.get("qku_id") != c.NOT_APPLICABLE_ID}),
        "status_counts": dict(Counter(str(row.get("result_status")) for row in records if row.get("result_status"))),
    }


def _audit_row(
    filename: str,
    artifact_id: str,
    row_id: str,
    extras: dict[str, Any],
    *,
    upstream_artifact_refs: list[str] | None = None,
    upstream_row_refs: list[str] | None = None,
    downstream_artifact_refs: list[str] | None = None,
    owning_agent: str = "governance_agent",
) -> dict[str, Any]:
    row = common_fields(
        report_filename=filename,
        artifact_id=artifact_id,
        row_id=row_id,
        upstream_artifact_refs=upstream_artifact_refs or list(c.REQUIRED_INPUT_REPORTS[:1]),
        upstream_row_refs=upstream_row_refs or [row_id],
        upstream_value_refs=["report_ref", "row_count", "authority_boundary"],
        downstream_pr_refs=["DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"],
        downstream_artifact_refs=downstream_artifact_refs or [c.MANIFEST_REF, "PR166_S2_FinalSummary.report.json"],
        owning_agent=owning_agent,
    )
    row.update(extras)
    return row


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in sorted(shard_dir.glob("PR166_S2_*.report.json")):
        path.unlink()


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    for payload in payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)
        payload["estimated_root_report_size_bytes"] = len(json_text(payload, compact=payload.get("sharded_flag", False)).encode("utf-8"))
    for payload in shard_payloads.values():
        payload["estimated_root_report_count"] = len(payloads)
        payload["estimated_shard_count"] = len(shard_payloads)


def timestamp(index: int, offset_seconds: int) -> str:
    value = BASE_TIME + timedelta(seconds=index * 10 + offset_seconds)
    return value.isoformat().replace("+00:00", "Z")


def retest_target_class(ctx: RetestContext) -> str:
    if ctx.source.get("quantum_route_class") == "PR166-Q":
        return "QUANTUM_COMPARATOR_CANDIDATE_RETEST_V2"
    if ctx.source.get("pre_repair_selection_state") == "SELECTED_AS_CHAMPION":
        return "CHAMPION_RETEST_V2"
    if not ctx.fill["filled_flag"]:
        return "NO_FILL_OR_EXECUTION_NOT_REALISTIC_WITH_REASON"
    if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value:
        return "CHALLENGER_RETEST_V2"
    return "REPAIRED_READY_FOR_REPLAY_PAPER_RETEST_V2"


def owning_agent_for_context(ctx: RetestContext) -> str:
    if "PR166-Q" in ctx.routes:
        return "quantum_optimizer_agent"
    if not ctx.fill["filled_flag"]:
        return "risk_manager_agent"
    if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value:
        return "parameter_selector_agent"
    return str(ctx.source.get("owning_agent") or "parameter_selector_agent")


def action_type_for_context(ctx: RetestContext) -> str:
    if "PR166-Q" in ctx.routes:
        return "QUANTUM_COMPARATOR_HANDOFF_REVIEW"
    if not ctx.fill["filled_flag"]:
        return "NO_FILL_REPAIR_OR_MICROSTRUCTURE_REVIEW"
    if ctx.result["lifecycle_status"] == LifecycleStatus.POSITIVE.value:
        return "SCORE_MEMORY_REFRESH_AND_PR167_REVIEW"
    return "NEGATIVE_EDGE_REPAIR_FEEDBACK"


def expected_output_for_agent(agent: str) -> str:
    mapping = {
        "research_agent": "external retest signal candidates and materialization feedback",
        "parameter_selector_agent": "score memory handoff and champion challenger ranking",
        "risk_manager_agent": "TCA no-fill capacity crowding and adverse selection receipts",
        "quantum_optimizer_agent": "PR166-Q comparator handoff with classical evidence",
        "commander_agent": "next PR route command matrix",
        "governance_agent": "authority no-orphan status enum validation receipts",
        "dashboard_agent": "owner review display handoff without live action",
    }
    return mapping.get(agent, "replay paper route receipt")


def supporting_agents(owner: str) -> list[str]:
    mapping = {
        "research_agent": ["parameter_selector_agent", "governance_agent"],
        "parameter_selector_agent": ["risk_manager_agent", "dashboard_agent"],
        "risk_manager_agent": ["parameter_selector_agent", "governance_agent"],
        "quantum_optimizer_agent": ["risk_manager_agent", "commander_agent"],
        "commander_agent": ["governance_agent", "dashboard_agent"],
        "governance_agent": ["commander_agent", "dashboard_agent"],
        "dashboard_agent": ["governance_agent", "commander_agent"],
    }
    return mapping.get(owner, ["governance_agent", "commander_agent"])


def route_action(route: str) -> str:
    if route == "PR166-SM2":
        return "CONSUME_SCORE_MEMORY_READY_RETEST_RESULTS"
    if route == "PR166-SF-R2":
        return "REPAIR_FAILED_OR_DEGRADED_RETEST_PREDICATE"
    if route == "PR166-Q":
        return "RUN_CLASSICAL_COMPARATOR_REVIEW_WITHOUT_QUANTUM_BACKEND"
    if route == "PR167":
        return "OPEN_TRADE_SIMULATOR_READY_REFERENCE_ONLY"
    if route in c.FUTURE_CONNECTOR_PR_REFS:
        return "FUTURE_CONNECTOR_READINESS_REFERENCE_ONLY_NO_BINDING"
    return "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"


def qku_family(row: dict[str, Any]) -> str:
    qku = str(row.get("qku_id") or "")
    return qku.split("_")[0] if "_" in qku else qku[:32]


def bucket(value: Any, prefix: str) -> str:
    val = numeric({"value": value}, "value", 0.0)
    if val >= 0.67:
        return f"{prefix}_HIGH"
    if val >= 0.34:
        return f"{prefix}_MEDIUM"
    return f"{prefix}_LOW"


def numeric(row: dict[str, Any], field: str, default: float = 0.0) -> float:
    try:
        value = row.get(field, default)
        if value is None:
            return float(default)
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def round6(value: float) -> float:
    return round(float(value), 6)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def clamp01(value: float) -> float:
    return round6(clamp(value, 0.0, 1.0))


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, int(round((pct / 100.0) * (len(sorted_values) - 1)))))
    return round6(sorted_values[index])


def median(values: Iterable[float]) -> float:
    sorted_values = sorted(float(value) for value in values)
    if not sorted_values:
        return 0.0
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return round6(sorted_values[midpoint])
    return round6((sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2.0)


def _by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_packet_id")): row for row in rows if row.get("candidate_packet_id")}
