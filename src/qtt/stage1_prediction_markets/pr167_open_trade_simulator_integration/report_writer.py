"""Build PR167 open-trade simulator generated reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from . import constants as c
from .authority import (
    authority_boundary_record,
    authority_false_flags,
    authority_zero_counts,
    simulator_true_flags,
)
from .io import (
    ensure_branch,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    input_counts: dict[str, int]


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
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payloads[filename],
            compact=bool(payloads[filename].get("sharded_flag")),
        )
    for rel_path, payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), payload, compact=True)
    return BuildArtifacts(
        summary=dict(payloads["PR167_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    contexts = build_candidate_contexts(source)
    selected = select_actual_sim_subset(contexts)
    sim_rows = assign_simulator_roles([materialize_sim_row(ctx, selected) for ctx in contexts])
    row_payloads = build_row_payloads(source, sim_rows)
    row_payloads["PR167_ReportManifest.report.json"] = []
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    for _ in range(3):
        row_payloads["PR167_ReportManifest.report.json"] = build_manifest_rows(payloads)
        payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR167_ReportConsumerCrosswalk.report.json"] = build_crosswalk_rows(payloads)
    row_payloads["PR167_ArtifactMap.report.json"] = build_artifact_map_rows(payloads, shard_payloads)
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR167_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"{c.PR_ID} payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}
    missing: list[str] = []
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        rows = records_from_report_payload(repo_root, payload)
        payloads[filename] = payload
        records[filename] = rows
        counts[filename] = len(rows)
    if missing:
        raise RuntimeError(f"{c.PR_ID} required inputs missing: {', '.join(missing)}")
    bad_counts = {
        name: counts[name]
        for name in c.EXPECTED_559_INPUTS
        if counts.get(name) != 559
    }
    if bad_counts:
        details = ", ".join(f"{name}={count}" for name, count in sorted(bad_counts.items()))
        raise RuntimeError(f"{c.PR_ID} upstream 559-count input drift: {details}")
    return SourceData(payloads=payloads, records=records, input_counts=counts)


def build_candidate_contexts(source: SourceData) -> list[dict[str, Any]]:
    primary = _sorted_rows(source.records["PR162E_Q_To_PR167.report.json"])
    companion_names = (
        "PR162E_Q_OpenTradeSimMap.report.json",
        "PR162E_Q_QUBORecipe.report.json",
        "PR162E_Q_BQMRecipe.report.json",
        "PR162E_Q_IsingRecipe.report.json",
        "PR162E_Q_CQMRecipe.report.json",
        "PR162E_Q_DQMRecipe.report.json",
        "PR162E_Q_QuadProgramRecipe.report.json",
        "PR162E_Q_HybridRecipe.report.json",
        "PR162E_Q_SolutionInterpretBack.report.json",
        "PR162E_Q_TestVectors.report.json",
        "PR162E_Q_MapProof.report.json",
        "PR162E_Q_FeasibilityChecks.report.json",
        "PR162E_Q_TCAMapImpact.report.json",
        "PR162E_Q_OverfitFDRMapRisk.report.json",
        "PR162E_Q_PortfolioUtilityMap.report.json",
        "PR162E_Q_RegimeMapMemory.report.json",
        "PR166_QC_OpenTradeSimHandoff.report.json",
        "PR166_QC_To_PR167.report.json",
        "PR166_QC_TCAEvidence.report.json",
        "PR166_QC_FillNoFillEvidence.report.json",
        "PR166_QC_LatencyEvidence.report.json",
        "PR166_QC_QueueRiskEvidence.report.json",
        "PR166_QC_CapacityCrowdingEvidence.report.json",
        "PR166_QC_OverfitFDRRetest.report.json",
        "PR166_QC_PortfolioUtility.report.json",
        "PR166_QC_ChampChallengerPaper.report.json",
        "PR166_QC_StillNegativeAfterCosts.report.json",
        "PR166_QC_ReplayPaperRepairLab.report.json",
        "PR166_QC_OwnerDashboardReview.report.json",
        "PR166_QC_ConnectorRouteReadiness.report.json",
    )
    companions = {name: _sorted_rows(source.records[name]) for name in companion_names}
    contexts: list[dict[str, Any]] = []
    for index, row in enumerate(primary, start=1):
        companion = {name: rows[index - 1] if index <= len(rows) else {} for name, rows in companions.items()}
        contexts.append({"index": index, "map": row, "companions": companion})
    return contexts


def select_actual_sim_subset(contexts: list[dict[str, Any]]) -> set[str]:
    cap = c.SIM_CAPS["max_actual_sim_rows_default_ci"]
    selected: set[str] = set()
    per_lane: Counter[str] = Counter()
    ranked = sorted(contexts, key=lambda ctx: (-_selection_score(ctx), _primary_ref(ctx)))

    for ctx in ranked:
        if len(selected) >= cap:
            return selected
        if _open_trade_route(ctx):
            selected.add(_primary_ref(ctx))

    strata: tuple[tuple[str, Callable[[dict[str, Any]], bool]], ...] = (
        ("paper_champion", lambda ctx: bool(ctx["map"].get("paper_champion_flag"))),
        ("paper_challenger", lambda ctx: bool(ctx["map"].get("paper_challenger_flag"))),
        ("paper_retest", lambda ctx: bool(ctx["map"].get("paper_retest_flag"))),
        ("still_negative", lambda ctx: bool(ctx["map"].get("still_negative_after_costs_flag"))),
        ("repair_lab", lambda ctx: str(ctx["companions"]["PR166_QC_ReplayPaperRepairLab.report.json"].get("repair_row_id") or "")),
        ("mapping_champion", lambda ctx: str(ctx["map"].get("champion_challenger_role")) == "paper champion"),
        ("mapping_challenger", lambda ctx: str(ctx["map"].get("champion_challenger_role")) == "paper challenger"),
        ("qubo_ready", lambda ctx: str(ctx["map"].get("model_family_selected")) == "QUBO"),
        ("bqm_ready", lambda ctx: str(ctx["map"].get("model_family_selected")) == "BQM"),
        ("ising_ready", lambda ctx: str(ctx["map"].get("model_family_selected")) == "Ising"),
        ("cqm_ready", lambda ctx: str(ctx["map"].get("model_family_selected")) == "CQM"),
        ("dqm_ready", lambda ctx: str(ctx["map"].get("model_family_selected")) == "DQM"),
        ("quad_ready", lambda ctx: str(ctx["map"].get("model_family_selected")) == "QuadraticProgram"),
        ("hybrid_ready", lambda ctx: bool(ctx["map"].get("hybrid_mapping_flag", True))),
        ("high_fill_tca_sensitivity", lambda ctx: _float(ctx["map"].get("TCA_sensitivity"), 0.0) >= 0.18),
        ("high_queue_latency_sensitivity", lambda ctx: _float(ctx["map"].get("latency_sensitivity"), 0.0) >= 0.18),
        ("high_portability", lambda ctx: bool(ctx["map"].get("future_market_portability_flag"))),
    )
    lane_cap = c.SIM_CAPS["max_rows_per_lane_default_ci"]
    for lane, predicate in strata:
        for ctx in ranked:
            if len(selected) >= cap:
                return selected
            ref = _primary_ref(ctx)
            if ref in selected or per_lane[lane] >= lane_cap:
                continue
            if predicate(ctx):
                selected.add(ref)
                per_lane[lane] += 1
    for ctx in ranked:
        if len(selected) >= cap:
            break
        selected.add(_primary_ref(ctx))
    return selected


def materialize_sim_row(ctx: dict[str, Any], selected: set[str]) -> dict[str, Any]:
    idx = int(ctx["index"])
    row = ctx["map"]
    comp = ctx["companions"]
    qc = comp["PR166_QC_To_PR167.report.json"]
    qc_open = comp["PR166_QC_OpenTradeSimHandoff.report.json"]
    tca = comp["PR166_QC_TCAEvidence.report.json"]
    queue = comp["PR166_QC_QueueRiskEvidence.report.json"]
    latency = comp["PR166_QC_LatencyEvidence.report.json"]
    capacity = comp["PR166_QC_CapacityCrowdingEvidence.report.json"]
    overfit = comp["PR166_QC_OverfitFDRRetest.report.json"]
    portfolio = comp["PR166_QC_PortfolioUtility.report.json"]
    regime = comp["PR162E_Q_RegimeMapMemory.report.json"]

    actual = _primary_ref(ctx) in selected
    structural_only = not actual
    refs = _refs(idx)
    model_family = str(row.get("model_family_selected") or row.get("model_family") or "Hybrid")
    base_expected = _float(row.get("expected_net_profit_per_order_candidate"), _float(qc.get("expected_net_profit_per_order_candidate"), -0.01))
    upstream_tca = _float(tca.get("total_tca_estimate"), _float(row.get("total_tca_estimate"), 0.02))
    fee = _float(tca.get("explicit_fee_component"), 0.0015 + (idx % 5) * 0.0001)
    spread_component = _float(tca.get("bid_ask_spread_component"), _float(row.get("bid_ask_spread_component"), 0.0025))
    slippage = _float(tca.get("slippage_component"), 0.002 + (idx % 7) * 0.00012)
    impact = _float(tca.get("impact_component"), 0.0018 + (idx % 11) * 0.00008)
    latency_component = _float(tca.get("latency_component"), 0.0004 + (idx % 3) * 0.0001)
    no_fill_cost = _float(tca.get("no_fill_opportunity_cost_component"), 0.0015 + (idx % 13) * 0.00007)
    settlement = _float(tca.get("settlement_finality_component"), 0.0007 + (idx % 5) * 0.00004)
    model_gap_component = _float(tca.get("model_vs_execution_gap_component"), _float(row.get("model_execution_gap_component"), 0.0012))

    fill = _clamp(_float(qc.get("fill_probability_score"), _float(row.get("fill_probability_score"), 0.62)), 0.0, 1.0)
    no_fill = _round(1.0 - fill)
    partial_fill = _round(_clamp(0.12 + no_fill * 0.45 + (idx % 7) * 0.01, 0.0, 0.95))
    queue_survival = _clamp(_float(queue.get("queue_risk_adjusted_score"), _float(row.get("queue_risk_adjusted_score"), 0.7)), 0.0, 1.0)
    latency_score = _clamp(_float(latency.get("latency_adjusted_score"), _float(row.get("latency_adjusted_score"), 0.6)), 0.0, 1.0)
    capacity_score = _clamp(_float(capacity.get("capacity_adjusted_score"), _float(row.get("capacity_adjusted_score"), 0.55)), 0.0, 1.0)
    crowding_score = _clamp(_float(capacity.get("crowding_adjusted_score"), _float(row.get("crowding_adjusted_score"), 0.55)), 0.0, 1.0)
    false_discovery = _round(_float(overfit.get("false_discovery_penalty"), _float(row.get("false_discovery_penalty"), 0.04)))
    pbo = _round(_float(overfit.get("probability_of_backtest_overfitting_proxy"), 0.18))

    price = _round(_clamp(_float(row.get("normalized_price"), 0.42 + (idx % 47) * 0.006), 0.02, 0.98))
    tick_spread = _round(_clamp(0.01 + spread_component * 3.0 + (idx % 4) * 0.002, 0.01, 0.12))
    best_bid = _round(_clamp(price - tick_spread / 2.0, 0.01, 0.98))
    best_ask = _round(_clamp(price + tick_spread / 2.0, 0.02, 0.99))
    midpoint = _round((best_bid + best_ask) / 2.0)
    quantity = _round(10.0 + (idx % c.SIM_CAPS["max_order_size_buckets_default_ci"]) * 5.0)
    queue_ahead = _round(20.0 + (idx % 13) * 7.0 + quantity * 0.4)
    queue_behind = _round(14.0 + (idx % 11) * 5.0)
    imbalance = _round((queue_behind - queue_ahead) / max(queue_ahead + queue_behind, 1.0))
    depth = _round(queue_ahead + queue_behind + 30.0 + (idx % 9) * 3.0)
    queue_position = _round(queue_ahead / max(depth, 1.0))
    time_to_fill = int(round((1.0 - fill) * 1800 + queue_position * 900 + (idx % 8) * 75))
    simulated_latency = int(round(35 + (1.0 - latency_score) * 180 + (idx % 9) * 6 + (12 if model_family in {"QUBO", "BQM", "Ising"} else 6)))
    latency_budget = 220 if actual else 160
    latency_breach = simulated_latency > latency_budget or latency_score < 0.28
    adverse = _round(max(0.0, -imbalance) * 0.006 + (0.004 if idx % 17 == 0 else 0.0))
    stale_book_penalty = _round(0.006 if idx % 19 == 0 else 0.001 + (idx % 5) * 0.0001)
    cancel_degradation = _round((1.0 - queue_survival) * 0.011 + (idx % 4) * 0.0007)
    implementation_shortfall = _round(
        fee + spread_component + slippage + impact + latency_component + no_fill_cost + adverse + settlement + model_gap_component
    )
    total_tca = _round(max(upstream_tca, implementation_shortfall + stale_book_penalty + cancel_degradation * 0.4))
    quantum_precompute_benefit = _round(0.004 + (0.006 if model_family in {"QUBO", "BQM", "Ising"} else 0.003))
    expected_net = _round(
        base_expected
        + fill * 0.009
        + queue_survival * 0.004
        + quantum_precompute_benefit
        - total_tca * 0.22
        - no_fill * 0.012
        - (simulated_latency / 100000.0)
        - false_discovery * 0.06
    )
    expected_delta = _round(expected_net - base_expected)
    route_scores = _route_scores(fill, total_tca, simulated_latency, adverse, queue_survival, expected_net)
    selected_route = max(route_scores, key=route_scores.get)
    selected_route_score = route_scores[selected_route]
    score = _round(
        _clamp(
            fill * 0.22
            + partial_fill * 0.04
            + queue_survival * 0.16
            + latency_score * 0.10
            + max(0.0, 1.0 - total_tca * 8.0) * 0.15
            + capacity_score * 0.08
            + crowding_score * 0.05
            + _clamp(expected_net + 0.05, 0.0, 0.2) * 0.75
            + route_scores["hybrid_selects_classical_executes_route_score"] * 0.10
            - false_discovery * 0.10
            - pbo * 0.04
            - stale_book_penalty,
            0.0,
            1.0,
        )
    )
    failure_reason = _failure_reason(
        actual=actual,
        still_negative=bool(row.get("still_negative_after_costs_flag")),
        expected_net=expected_net,
        fill=fill,
        partial_fill=partial_fill,
        latency_breach=latency_breach,
        queue_survival=queue_survival,
        total_tca=total_tca,
        capacity_score=capacity_score,
        adverse=adverse,
        stale_book_penalty=stale_book_penalty,
        cancel_degradation=cancel_degradation,
        model_gap_component=model_gap_component,
    )
    survival = actual and not failure_reason and expected_net > 0
    paper_role = str(row.get("champion_challenger_role") or qc.get("champion_challenger_role") or "no-trade nonlive")
    structural_reason = "" if actual else "STRUCTURAL_RUNTIME_CAP_NONLIVE_RECEIPT_WITH_DOWNSTREAM_ROUTE"
    lifecycle = _lifecycle_trace(idx, actual, survival, failure_reason, structural_reason)
    row_payload = {
        **_base_report_row("PR167_SimEligibility.report.json", idx),
        "row_id": f"PR167_SIM::{idx:05d}",
        "source_pr": c.PR_ID,
        "source_pr162e_q_handoff_ref": _primary_ref(ctx),
        "source_pr166_qc_handoff_ref": str(qc.get("row_id") or qc_open.get("row_id") or c.NOT_APPLICABLE),
        "upstream_pr162e_q_row_ref": _primary_ref(ctx),
        "upstream_pr166_qc_row_ref": str(qc.get("row_id") or qc_open.get("row_id") or c.NOT_APPLICABLE),
        "upstream_pr166_qb_row_ref": str(row.get("upstream_pr166_qb_row_ref") or qc.get("upstream_pr166_qb_row_ref") or c.NOT_APPLICABLE),
        "upstream_pr166_q_row_ref": str(row.get("upstream_pr166_q_row_ref") or qc.get("upstream_pr166_q_row_ref") or c.NOT_APPLICABLE),
        "qku_id": str(row.get("qku_id") or qc.get("qku_id") or c.NOT_APPLICABLE),
        "qku_family": str(row.get("qku_family") or qc.get("qku_family") or _family_from_id(row.get("qku_id", ""), "QKU")),
        "formula_id": str(row.get("formula_id") or qc.get("formula_id") or c.NOT_APPLICABLE),
        "algorithm_id": str(row.get("algorithm_id") or qc.get("algorithm_id") or c.NOT_APPLICABLE),
        "parameter_stack_id": str(row.get("parameter_stack_id") or qc.get("parameter_stack_id") or c.NOT_APPLICABLE),
        "execution_route_id": str(row.get("execution_route_id") or qc.get("execution_route_id") or f"PR167_EXEC_ROUTE::{idx:05d}"),
        "model_family_selected": model_family,
        "qku_family_cluster": str(row.get("QKU_family_cluster") or row.get("qku_family_cluster") or "QKU_FAMILY_CLUSTER"),
        "formula_family_cluster": str(row.get("formula_family_cluster") or "FORMULA_FAMILY_CLUSTER"),
        "algorithm_family_cluster": str(row.get("algorithm_family_cluster") or "ALGORITHM_FAMILY_CLUSTER"),
        "quantum_model_family_cluster": f"QUANTUM_MODEL_CLUSTER::{model_family}",
        "quantum_recipe_ref": _quantum_recipe_ref(model_family, idx, row),
        "hybrid_recipe_ref": str(row.get("hybrid_recipe_ref") or refs["hybrid"]),
        "classical_fallback_ref": str(row.get("classical_fallback_ref") or qc.get("classical_fallback_ref") or refs["classical"]),
        "solution_interpret_back_ref": str(row.get("solution_interpret_back_ref") or refs["interpret"]),
        "proof_vector_ref": str(row.get("proof_vector_ref") or refs["proof"]),
        "test_vector_ref": str(row.get("test_vector_ref") or refs["test"]),
        "market_scope": str(row.get("market_scope") or qc.get("market_scope") or "PREDICTION_MARKET_STAGE1_NONLIVE_SIMULATOR_SCOPE"),
        "stage1_prediction_market_flag": True,
        "future_market_portability_flag": True,
        "simulator_disposition": "SIM_EXECUTED_BOUNDED_NONLIVE",
        "simulator_quality_grade": "G_STRUCTURAL_ONLY_RESIDUAL",
        "open_trade_sim_route_flag": _open_trade_route(ctx),
        "paper_champion_flag": bool(row.get("paper_champion_flag")) or bool(qc.get("paper_champion_flag")),
        "paper_challenger_flag": bool(row.get("paper_challenger_flag")) or bool(qc.get("paper_challenger_flag")),
        "paper_retest_flag": bool(row.get("paper_retest_flag")) or bool(qc.get("paper_retest_flag")),
        "still_negative_after_costs_flag": bool(row.get("still_negative_after_costs_flag")) or bool(qc.get("still_negative_after_costs_flag")),
        "actual_sim_subset_flag": actual,
        "structural_only_flag": structural_only,
        "structural_only_reason": structural_reason,
        "sim_budget_ref": "PR167_SIM_BUDGET::00001",
        "sim_subset_reason": "ACTUAL_OPEN_TRADE_ROUTE_OR_STRATIFIED_CAPPED_SELECTION" if actual else structural_reason,
        "order_intent_ref": refs["order_intent"],
        "shadow_order_audit_ref": refs["shadow"],
        "order_side": "BUY" if idx % 2 else "SELL",
        "YES_NO_side": str(row.get("YES_NO_side") or ("YES" if idx % 2 else "NO")),
        "normalized_price": price,
        "normalized_quantity": quantity,
        "order_size_bucket": f"SIZE_BUCKET_{1 + (idx % c.SIM_CAPS['max_order_size_buckets_default_ci'])}",
        "time_in_force_candidate": "IOC" if selected_route == "aggressive_limit_route_score" else "GTC_SIM_BOUNDED" if actual else "STRUCTURAL_TIF_ROUTE",
        "maker_taker_route_candidate": "MAKER_OR_CANCEL_SIM" if selected_route.startswith("passive") else "TAKER_STYLE_SIM_NO_LIVE",
        "passive_aggressive_route_candidate": selected_route.replace("_score", ""),
        "cancel_replace_policy_candidate": "MAX_4_ATTEMPTS_STALE_OR_QUEUE_DECAY_TRIGGERED",
        "order_book_state_ref": refs["book"],
        "book_state_provenance": "generated_structural" if actual else "structural_unavailable",
        "synthetic_book_flag": True,
        "synthetic_book_reason": "DETERMINISTIC_REPO_LOCAL_BOOK_PROXY_NO_CONNECTOR_CALL",
        "synthetic_book_penalty": stale_book_penalty,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": tick_spread,
        "midpoint": midpoint,
        "bid_depth_levels": _depth_levels(best_bid, "bid", idx),
        "ask_depth_levels": _depth_levels(best_ask, "ask", idx),
        "depth_at_price": depth,
        "depth_at_candidate_price": depth,
        "queue_position_proxy": queue_position,
        "queue_ahead_proxy": queue_ahead,
        "queue_behind_proxy": queue_behind,
        "queue_imbalance_proxy": imbalance,
        "liquidity_bucket": _liquidity_bucket(depth),
        "stale_book_flag": stale_book_penalty >= 0.006,
        "queue_priority_assumption": "PRICE_TIME_PRIORITY_PROXY",
        "queue_decay_assumption": "CANCEL_AND_MARKET_ORDER_DEPLETION_PROXY",
        "cancel_rate_proxy": _round(0.04 + (idx % 9) * 0.006),
        "market_order_arrival_proxy": _round(0.06 + fill * 0.08),
        "queue_survival_score": queue_survival,
        "time_to_fill_proxy_ms": time_to_fill,
        "queue_depletion_probability_proxy": _round(fill * queue_survival),
        "fill_probability_score": fill,
        "partial_fill_probability_score": partial_fill,
        "no_fill_risk_score": no_fill,
        "expected_fill_quantity_candidate": _round(quantity * fill),
        "expected_unfilled_quantity_candidate": _round(quantity * no_fill),
        "fill_time_proxy_ms": time_to_fill,
        "fill_model_reason": "DETERMINISTIC_FILL_PROXY_FROM_PR166_QC_EVIDENCE_AND_BOOK_DEPTH",
        "decision_latency_ms_candidate": int(round(12 + (idx % 5) * 2)),
        "model_lookup_latency_ms_candidate": int(round(8 + (idx % 7))),
        "quantum_precompute_latency_ms_candidate": int(round(18 + (idx % 11) * 2)),
        "classical_fallback_latency_ms_candidate": int(round(6 + (idx % 4))),
        "order_intent_latency_ms_candidate": int(round(9 + (idx % 6))),
        "simulated_order_path_latency_ms": simulated_latency,
        "latency_budget_ms": latency_budget,
        "simulated_latency_ms": simulated_latency,
        "latency_breach_flag": latency_breach,
        "precompute_only_flag": True,
        "hot_path_allowed_flag": False,
        "explicit_fee_component": fee,
        "spread_component": spread_component,
        "slippage_component": slippage,
        "impact_component": impact,
        "latency_component": latency_component,
        "no_fill_opportunity_cost_component": no_fill_cost,
        "adverse_selection_component": adverse,
        "settlement_finality_component": settlement,
        "model_execution_gap_component": model_gap_component,
        "implementation_shortfall_proxy": implementation_shortfall,
        "total_TCA_candidate": total_tca,
        "TCA_reason_codes": ["FEE", "SPREAD", "SLIPPAGE", "IMPACT", "LATENCY", "NO_FILL", "ADVERSE_SELECTION", "MODEL_EXECUTION_GAP"],
        "decision_price": price,
        "simulated_execution_price": _round(price + (tick_spread * 0.5 if idx % 2 else -tick_spread * 0.5)),
        "simulated_arrival_price": midpoint,
        "explicit_cost_component": fee,
        "implicit_cost_component": _round(spread_component + slippage + impact),
        "opportunity_cost_component": no_fill_cost,
        "delay_cost_component": latency_component,
        "total_implementation_shortfall_candidate": implementation_shortfall,
        "implementation_shortfall_reason_codes": ["EXPLICIT", "IMPLICIT", "OPPORTUNITY", "DELAY", "MODEL_EXECUTION_GAP"],
        "expected_net_profit_per_order_candidate": expected_net,
        "expected_value_delta_candidate": expected_delta,
        "counterfactual_route_ref": refs["counterfactual"],
        **route_scores,
        "selected_counterfactual_winner": selected_route,
        "counterfactual_score_delta_vs_classical": _round(route_scores["hybrid_selects_classical_executes_route_score"] - route_scores["classical_fallback_route_score"]),
        "counterfactual_score_delta_vs_no_trade": _round(selected_route_score - route_scores["no_trade_route_score"]),
        "counterfactual_reason": "SAME_BOOK_ROUTE_COMPARISON_BOUNDED_NONLIVE",
        "execution_adjusted_score": score,
        "tca_adjusted_score": _round(_clamp(1.0 - total_tca * 7.0, 0.0, 1.0)),
        "latency_adjusted_score": latency_score,
        "queue_risk_adjusted_score": queue_survival,
        "capacity_adjusted_score": capacity_score,
        "crowding_adjusted_score": crowding_score,
        "risk_adjusted_score": _round(_clamp(score - adverse - stale_book_penalty - cancel_degradation, 0.0, 1.0)),
        "overfit_adjusted_score": _round(_clamp(score - false_discovery - pbo * 0.05, 0.0, 1.0)),
        "false_discovery_penalty": false_discovery,
        "marginal_utility_score": _round(_float(portfolio.get("final_marginal_utility_evidence_score"), _float(row.get("final_marginal_utility_mapping_score"), 0.5))),
        "simulator_survival_flag": survival,
        "simulator_failure_reason": failure_reason,
        "paper_only_flag": (not actual and paper_role != "no-trade nonlive"),
        "simulator_champion_flag": False,
        "simulator_challenger_flag": False,
        "simulator_watch_flag": False,
        "simulator_retest_flag": bool(row.get("paper_retest_flag")) or bool(qc.get("paper_retest_flag")),
        "simulator_repair_flag": bool(row.get("still_negative_after_costs_flag")) or bool(failure_reason),
        "promotion_firewall_ref": refs["firewall"],
        "no_trade_nonlive_flag": paper_role == "no-trade nonlive" or (actual and bool(failure_reason) and expected_net <= 0),
        "plugin_needed_flag": bool(row.get("automapper_needed_flag")) or model_family in {"CQM", "DQM", "QuadraticProgram"},
        "owner_agent_intake_needed_flag": bool(row.get("owner_dashboard_review_flag")) or bool(row.get("still_negative_after_costs_flag")),
        "owner_dashboard_review_flag": bool(row.get("owner_dashboard_review_flag")) or bool(qc.get("owner_dashboard_review_flag")),
        "connector_route_readiness_ref": refs["connector"],
        "market_portability_ref": refs["market"],
        "report_consumer_crosswalk_ref": "PR167_ReportConsumerCrosswalk.report.json",
        "upstream_report_use_ref": "PR167_UpstreamReportUse.report.json",
        "downstream_pr166_qc_retest_route_ref": refs["to_pr166_qc"],
        "downstream_pr162e_route_ref": refs["to_pr162e"],
        "downstream_pr162f_route_ref": refs["to_pr162f"],
        "downstream_owner_dashboard_route_ref": refs["to_dashboard"],
        "downstream_cloud_switchboard_route_ref": refs["to_cloud"],
        "downstream_future_connector_route_ref": refs["to_future"],
        "owning_agent_id": "Open Trade Simulator Agent",
        "reviewer_agent_id": "Governance",
        "challenger_agent_id": "Classical Comparator Agent",
        "agent_duty_ref": "PR165_D2_AgentDutySourceCrosswalk.report.json",
        "action_required": "SIMULATOR_RETEST_OR_REPAIR_ROUTE",
        "upstream_refs": [
            _primary_ref(ctx),
            str(qc.get("row_id") or qc_open.get("row_id") or c.NOT_APPLICABLE),
            "PR166_QC_OpenTradeSimHandoff.report.json",
            "PR162E_Q_OpenTradeSimMap.report.json",
        ],
        "downstream_refs": list(c.DOWNSTREAM_PR_REFS),
        "validation_refs": [c.VALIDATOR_REF],
        "no_orphan_proof_ref": refs["no_orphan"],
        "lifecycle_state": lifecycle[-1]["lifecycle_state"],
        "lifecycle_trace": lifecycle,
        "trial_family_id": str(overfit.get("trial_family_id") or row.get("trial_family_id") or f"PR167_TRIAL_FAMILY::{idx % 37:03d}"),
        "near_duplicate_cluster_id": str(overfit.get("near_duplicate_cluster_id") or f"PR167_NEAR_DUP::{idx % 53:03d}"),
        "effective_independent_trial_count": int(_float(overfit.get("effective_independent_trial_count"), 1 + (idx % 23))),
        "family_wise_selection_pressure": _round(_float(overfit.get("family_wise_selection_pressure"), 0.18 + (idx % 9) * 0.01)),
        "deflated_score_proxy": _round(_clamp(score - false_discovery, 0.0, 1.0)),
        "probability_of_backtest_overfitting_proxy": pbo,
        "simulator_instability_penalty": _round((1.0 - queue_survival) * 0.03 + no_fill * 0.02),
        "replay_instability_penalty": _round(_float(overfit.get("replay_instability_penalty"), 0.01 + (idx % 5) * 0.002)),
        "paper_instability_penalty": _round(_float(overfit.get("paper_instability_penalty"), 0.012 + (idx % 7) * 0.002)),
        "replay_paper_simulator_divergence_penalty": _round(abs(expected_delta) * 0.08 + no_fill * 0.01),
        "rank_stability_score": _round(_clamp(1.0 - false_discovery - pbo * 0.1, 0.0, 1.0)),
        "repeated_test_inflation_penalty": _round(false_discovery * 0.6),
        "holdout_walk_forward_eligibility_flag": True,
        "CPCV_purged_walk_forward_route_flag": True,
        "event_cluster": str(portfolio.get("event_cluster") or row.get("event_cluster") or f"EVENT_CLUSTER::{idx % 41:03d}"),
        "question_market_cluster": str(portfolio.get("question_market_cluster") or f"QUESTION_MARKET_CLUSTER::{idx % 29:03d}"),
        "regime_cluster": str(regime.get("regime_cluster") or f"REGIME_CLUSTER::{idx % 17:03d}"),
        "time_to_resolution_bucket": str(portfolio.get("time_to_resolution_bucket") or f"TTR_BUCKET_{idx % 6}"),
        "liquidity_bucket": _liquidity_bucket(depth),
        "correlation_proxy_bucket": str(portfolio.get("correlation_proxy_bucket") or f"CORRELATION_BUCKET_{idx % 5}"),
        "diversification_contribution": _round(_float(portfolio.get("diversification_contribution"), 0.12 + (idx % 9) * 0.01)),
        "concentration_penalty": _round(_float(portfolio.get("concentration_penalty"), 0.03 + (idx % 7) * 0.004)),
        "marginal_expected_net_edge": expected_net,
        "marginal_diversification_benefit": _round(0.01 + (idx % 5) * 0.002),
        "marginal_risk_cost": _round((1.0 - score) * 0.018),
        "marginal_latency_cost": _round(simulated_latency / 100000.0),
        "marginal_capacity_cost": _round((1.0 - capacity_score) * 0.012),
        "marginal_crowding_cost": _round((1.0 - crowding_score) * 0.011),
        "marginal_simulator_learning_value": _round(0.02 if actual else 0.006),
        "marginal_replay_paper_learning_value": _round(0.014 if bool(row.get("paper_retest_flag")) else 0.006),
        "marginal_open_trade_simulator_value": _round(0.025 if actual else 0.005),
        "final_marginal_utility_sim_score": _round(_clamp(expected_net + score * 0.2 + (0.03 if actual else 0.005), 0.0, 1.0)),
        "regime_id": str(regime.get("regime_id") or f"PR167_REGIME::{idx % 17:03d}"),
        "market_state_id": f"PR167_MARKET_STATE::{idx % c.SIM_CAPS['max_order_book_states_default_ci']:03d}",
        "liquidity_regime": "THIN" if depth < 80 else "NORMAL",
        "volatility_regime": "ELEVATED" if idx % 7 == 0 else "NORMAL",
        "spread_regime": "WIDE" if tick_spread > 0.05 else "NORMAL",
        "time_to_resolution_regime": f"TTR_REGIME_{idx % 6}",
        "event_category_regime": f"EVENT_CATEGORY_{idx % 8}",
        "benchmark_success_failure_memory": str(row.get("benchmark_success_failure_memory") or "BENCHMARK_MEMORY_NOTED"),
        "replay_success_failure_memory": str(qc.get("replay_success_failure_memory") or "REPLAY_MEMORY_NOTED"),
        "paper_success_failure_memory": str(qc.get("paper_success_failure_memory") or "PAPER_MEMORY_NOTED"),
        "mapping_success_failure_memory": str(row.get("mapping_success_failure_memory") or "MAPPING_MEMORY_NOTED"),
        "simulator_success_failure_memory": "SIM_SURVIVED" if survival else "SIM_REPAIR_OR_STRUCTURAL_ROUTE",
        "negative_memory_overlay": "STILL_NEGATIVE_AFTER_COSTS" if bool(row.get("still_negative_after_costs_flag")) else "NO_NEGATIVE_OVERLAY",
        "no_fill_memory": "HIGH_NO_FILL_RISK" if no_fill > 0.45 else "NO_FILL_RISK_TRACKED",
        "cooldown_retest_eligibility": "ELIGIBLE_AFTER_REPLAY_PAPER_RETEST",
        "condition_scoped_warning": failure_reason or structural_reason or "NO_SIMULATOR_WARNING",
        "scenario_similarity_key": str(regime.get("scenario_similarity_key") or f"PR167_SCENARIO::{idx % 97:03d}"),
    }
    row_payload.update(_report_refs(idx))
    row_payload.update(_route_explain_fields(row_payload))
    return row_payload


def assign_simulator_roles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    survivors = sorted(
        [row for row in rows if row["simulator_survival_flag"]],
        key=lambda row: (-row["execution_adjusted_score"], row["deterministic_sort_key"]),
    )
    champion_refs = {row["row_id"] for row in survivors[:8]}
    challenger_refs = {row["row_id"] for row in survivors[8:32]}
    watch_refs = {row["row_id"] for row in survivors[32:64]}
    for row in rows:
        ref = row["row_id"]
        row["simulator_champion_flag"] = ref in champion_refs
        row["simulator_challenger_flag"] = ref in challenger_refs
        row["simulator_watch_flag"] = ref in watch_refs
        row["simulator_retest_flag"] = row["simulator_retest_flag"] or row["simulator_survival_flag"] or row["actual_sim_subset_flag"]
        if row["simulator_champion_flag"]:
            row["simulator_disposition"] = "SIM_CHAMPION_CANDIDATE_NONLIVE"
            row["simulator_quality_grade"] = "A_SIM_SURVIVOR_STRONG_NONLIVE"
        elif row["simulator_challenger_flag"]:
            row["simulator_disposition"] = "SIM_CHALLENGER_CANDIDATE_NONLIVE"
            row["simulator_quality_grade"] = "B_SIM_CHALLENGER_NONLIVE"
        elif row["simulator_watch_flag"]:
            row["simulator_disposition"] = "SIM_WATCH_CANDIDATE_NONLIVE"
            row["simulator_quality_grade"] = "B_SIM_CHALLENGER_NONLIVE"
        elif row["simulator_survival_flag"]:
            row["simulator_disposition"] = "SIM_SURVIVED_OPEN_TRADE_SIM_NONLIVE"
            row["simulator_quality_grade"] = "B_SIM_CHALLENGER_NONLIVE"
        elif row["actual_sim_subset_flag"] and row["simulator_failure_reason"]:
            row["simulator_disposition"] = _disposition_for_failure(row["simulator_failure_reason"])
            row["simulator_quality_grade"] = "E_FAILED_AFTER_TCA_LATENCY_FILL_RISK"
        elif row["simulator_repair_flag"]:
            row["simulator_disposition"] = "SIM_REPAIR_PROPOSAL_CREATED"
            row["simulator_quality_grade"] = "D_REPAIR_REQUIRED"
        elif row["paper_only_flag"]:
            row["simulator_disposition"] = "SIM_REMAINS_PAPER_ONLY"
            row["simulator_quality_grade"] = "C_PAPER_ONLY_RETEST_REQUIRED"
        elif row["owner_dashboard_review_flag"]:
            row["simulator_disposition"] = "SIM_ROUTED_TO_OWNER_DASHBOARD_REVIEW"
            row["simulator_quality_grade"] = "F_INSUFFICIENT_BOOK_DATA_ROUTE_REQUIRED"
        else:
            row["simulator_disposition"] = "SIM_REMAINS_NO_TRADE_NONLIVE"
            row["simulator_quality_grade"] = "G_STRUCTURAL_ONLY_RESIDUAL"
        row["primary_failure_reason"] = row["simulator_failure_reason"] or "NOT_FAILED_SIMULATOR_ROUTE"
        row["secondary_failure_reasons"] = _secondary_failure_reasons(row)
        row["survival_reason"] = _survival_reason(row)
        row["live_ready_flag"] = False
        row["future_live_authority_pr_required_flag"] = True
        row["replay_paper_retest_required_flag"] = True
        row["owner_review_required_flag"] = bool(row["owner_dashboard_review_flag"])
        row["allowed_next_routes"] = [
            row["downstream_pr166_qc_retest_route_ref"],
            row["downstream_pr162e_route_ref"],
            row["downstream_pr162f_route_ref"],
            row["downstream_owner_dashboard_route_ref"],
        ]
        row["prohibited_next_routes"] = ["LIVE_ORDER_EXECUTION", "REAL_FILL_RECEIPT", "PROFIT_EVIDENCE", "CONNECTOR_BINDING"]
    return rows


def build_row_payloads(source: SourceData, sim_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {filename: [] for filename in c.REPORT_FILENAMES}
    rows["PR167_InputConsumption.report.json"] = build_input_consumption_rows(source)
    rows["PR167_UpstreamReportUse.report.json"] = build_upstream_report_use_rows(source)
    rows["PR167_SourceSimParams.report.json"] = build_source_rows()
    rows["PR167_SimBudget.report.json"] = [build_budget_row(source, sim_rows)]
    for filename in c.ROW_REPORTS:
        rows[filename] = [row_for_report(filename, row, index) for index, row in enumerate(sim_rows, start=1)]
    rows["PR167_FinalSummary.report.json"] = [build_final_summary(source, sim_rows)]
    return rows


def build_input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.STRICT_INPUT_REPORTS, start=1):
        count = source.input_counts[filename]
        expected = 559 if filename in c.EXPECTED_559_INPUTS else count
        rows.append(
            {
                **_base_report_row("PR167_InputConsumption.report.json", index),
                "row_id": f"PR167_INPUT::{index:05d}",
                "source_report_ref": filename,
                "source_report_path": f"docs/master_plan/generated/{filename}",
                "expanded_record_count": count,
                "expected_record_count": expected,
                "record_count_matches_expected_flag": count == expected,
                "consumption_status": "CONSUMED_FOR_PR167_OPEN_TRADE_SIMULATOR",
                "consumed_for_purpose": "SIMULATOR_INPUT_LINEAGE_EXECUTION_MODEL_ROUTE_AND_NO_ORPHAN_CONSUMPTION",
                "routed_report_refs": [
                    "PR167_SimEligibility.report.json",
                    "PR167_CounterfactualRouteSim.report.json",
                    "PR167_NoOrphanProof.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_connector_binding_flag": True,
                "no_profit_evidence_flag": True,
                "no_backend_execution_flag": True,
                "no_live_order_execution_flag": True,
            }
        )
    return rows


def build_upstream_report_use_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.STRICT_INPUT_REPORTS, start=1):
        rows.append(
            {
                **_base_report_row("PR167_UpstreamReportUse.report.json", index),
                "row_id": f"PR167_UPSTREAM_USE::{index:05d}",
                "upstream_report_id": filename.removesuffix(".report.json"),
                "upstream_report_path": f"docs/master_plan/generated/{filename}",
                "source_pr": _source_pr_for_report(filename),
                "source_report_family": _report_family(filename),
                "consumed_by_pr167_flag": True,
                "consumed_for_purpose": "OPEN_TRADE_SIMULATOR_MODEL_ROUTE_EVIDENCE_OR_AGENT_CROSSWALK",
                "row_refs_used_count": source.input_counts[filename],
                "fields_used": _fields_used_for_report(source, filename),
                "owning_agent_id": "Open Trade Simulator Agent",
                "downstream_report_refs": [
                    "PR167_SimEligibility.report.json",
                    "PR167_ReportConsumerCrosswalk.report.json",
                    "PR167_ArtifactMap.report.json",
                ],
                "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
                "terminal_flag": False,
                "terminal_reason": "",
                "validation_ref": c.VALIDATOR_REF,
            }
        )
    return rows


def build_source_rows() -> list[dict[str, Any]]:
    specs = (
        ("SRC_PR167_QUEUE_REACTIVE_LOB", "research_order_book_queue_model", False, "https://arxiv.org/html/2501.08822v1", 7, 8, 7, 7, 3, 4, 2, 2, 4, 2, 3, 2, 5, 3),
        ("SRC_PR167_QUEUE_POSITION_VALUE", "research_queue_position_valuation", False, "https://moallemi.com/ciamac/papers/queue-value-2016.pdf", 5, 7, 6, 6, 2, 3, 1, 1, 3, 2, 2, 1, 4, 2),
        ("SRC_PR167_FILL_POST_FILL_TRADEOFF", "research_fill_probability_adverse_selection", False, "https://papers.ssrn.com/sol3/Delivery.cfm/5074873.pdf?abstractid=5074873", 4, 6, 6, 5, 2, 5, 1, 2, 4, 2, 2, 1, 4, 2),
        ("SRC_PR167_TCA_IMPLEMENTATION_SHORTFALL", "research_tca_implementation_shortfall", False, "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2807317", 4, 2, 2, 1, 2, 8, 6, 5, 5, 1, 1, 1, 4, 2),
        ("SRC_PR167_PREDICTION_MARKET_MICROSTRUCTURE", "research_prediction_market_microstructure", False, "https://arxiv.org/html/2604.24366v1", 5, 7, 5, 4, 3, 5, 2, 3, 4, 3, 2, 2, 5, 5),
        ("SRC_PR167_DEPM_MICROSTRUCTURE_SOK", "research_decentralized_prediction_market_microstructure", False, "https://arxiv.org/html/2510.15612v1", 4, 6, 4, 4, 4, 4, 2, 3, 4, 3, 2, 2, 4, 5),
        ("SRC_PR167_BACKTEST_OVERFIT_CPCV", "research_overfit_false_discovery", False, "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID4686376_code4361537.pdf?abstractid=4686376&mirid=1", 3, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 4, 2),
        ("SRC_PR167_QISKIT_QUAD_PROGRAM", "official_quantum_mapping_docs", True, "https://qiskit-community.github.io/qiskit-optimization/tutorials/01_quadratic_program.html", 2, 1, 1, 1, 2, 1, 1, 1, 1, 0, 0, 0, 2, 2),
        ("SRC_PR167_DWAVE_MODELS", "official_quantum_model_docs", True, "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html", 2, 1, 1, 1, 2, 1, 1, 1, 1, 0, 0, 0, 2, 2),
        ("SRC_PR167_BRAKET_HYBRID_ROUTE_ONLY", "official_cloud_quantum_route_docs", True, "https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html", 1, 0, 0, 0, 3, 1, 1, 1, 1, 0, 0, 0, 2, 3),
        ("SRC_PR167_SHADOW_PAPER_WORKFLOW", "non_official_shadow_paper_workflow", False, "https://ml4trading.io/docs/live/", 3, 3, 2, 2, 5, 2, 2, 2, 2, 4, 4, 4, 5, 2),
        ("SRC_PR167_PAPER_TRADING_AUDIT_LOGS", "non_official_paper_trading_audit_patterns", False, "https://algovantis.com/paper-trading-workflow-for-validating-algorithmic-execution-logic/", 3, 3, 2, 2, 5, 2, 2, 2, 2, 5, 5, 4, 5, 2),
    )
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        (
            source_id,
            source_type,
            official,
            locator,
            sim_count,
            book_count,
            fill_count,
            queue_count,
            queue_survival_count,
            latency_count,
            tca_count,
            shortfall_count,
            capacity_count,
            circuit_count,
            shadow_count,
            ladder_count,
            repair_count,
            portability_count,
        ) = spec
        rows.append(
            {
                **_base_report_row("PR167_SourceSimParams.report.json", index),
                "row_id": f"PR167_SOURCE::{index:05d}",
                "source_id": source_id,
                "source_type": source_type,
                "official_flag": official,
                "non_official_flag": not official,
                "source_locator_or_query": locator,
                "simulator_parameters_extracted_count": sim_count,
                "order_book_parameters_extracted_count": book_count,
                "fill_model_parameters_extracted_count": fill_count,
                "queue_risk_parameters_extracted_count": queue_count,
                "queue_survival_parameters_extracted_count": queue_survival_count,
                "latency_parameters_extracted_count": latency_count,
                "TCA_parameters_extracted_count": tca_count,
                "implementation_shortfall_parameters_extracted_count": shortfall_count,
                "capacity_parameters_extracted_count": capacity_count,
                "circuit_breaker_patterns_extracted_count": circuit_count,
                "shadow_order_patterns_extracted_count": shadow_count,
                "route_ladder_patterns_extracted_count": ladder_count,
                "repair_strategy_parameters_extracted_count": repair_count,
                "future_market_portability_notes_count": portability_count,
                "candidate_values_extracted_count": sim_count + book_count + fill_count + queue_count + tca_count,
                "rejected_reason": "",
                "routed_report_refs": [
                    "PR167_OrderBookState.report.json",
                    "PR167_FillNoFillSim.report.json",
                    "PR167_TCASim.report.json",
                    "PR167_OpenTradeRiskControls.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_connector_binding_flag": True,
                "no_profit_evidence_flag": True,
                "no_backend_execution_flag": True,
                "no_live_order_execution_flag": True,
            }
        )
    return rows


def build_budget_row(source: SourceData, rows: list[dict[str, Any]]) -> dict[str, Any]:
    actual = [row for row in rows if row["actual_sim_subset_flag"]]
    open_trade_count = sum(1 for row in source.records["PR166_QC_OpenTradeSimHandoff.report.json"] if row.get("open_trade_sim_route_flag") is True)
    return {
        **_base_report_row("PR167_SimBudget.report.json", 1),
        "row_id": "PR167_SIM_BUDGET::00001",
        **c.SIM_CAPS,
        "actual_sim_subset_size": len(actual),
        "actual_rows_per_lane": dict(sorted(Counter(row["sim_subset_reason"] for row in actual).items())),
        "pr166_qc_open_trade_sim_handoff_flagged_count": open_trade_count,
        "open_trade_route_rows_included_in_actual_subset_count": sum(1 for row in actual if row.get("open_trade_sim_route_flag")),
        "subset_selection_policy": (
            "DETERMINISTIC_STRATIFIED_SELECTION_INCLUDES_ALL_PR166_QC_OPEN_TRADE_ROUTES_"
            "THEN_CHAMPION_CHALLENGER_RETEST_STILL_NEGATIVE_REPAIR_MODEL_FAMILY_SENSITIVITY"
        ),
        "manual_or_nightly_expansion_required_for_larger_rows_flag": True,
        "no_unbounded_simulation_execution_flag": True,
        "no_connector_calls_allowed_flag": True,
        "no_live_order_execution_allowed_flag": True,
        "no_backend_execution_flag": True,
        "validation_refs": [c.VALIDATOR_REF],
    }


def row_for_report(filename: str, row: dict[str, Any], index: int) -> dict[str, Any]:
    output = dict(row)
    output["artifact_id"] = filename.removesuffix(".report.json")
    output["deterministic_sort_key"] = f"{filename}::{index:05d}"
    output["row_id"] = _row_id_for_report(filename, index)
    output["source_sim_row_ref"] = f"PR167_SIM::{index:05d}"
    if filename == "PR167_OrderIntent.report.json":
        output.update(_order_intent_fields(output, index))
    elif filename == "PR167_ShadowOrderAudit.report.json":
        output.update(_shadow_fields(output, index))
    elif filename == "PR167_OrderBookState.report.json":
        output.update(_book_fields(output, index))
    elif filename == "PR167_PriceSideNorm.report.json":
        output.update(_price_norm_fields(output, index))
    elif filename == "PR167_OrderLifecycle.report.json":
        output.update(_lifecycle_fields(output, index))
    elif filename == "PR167_OrderAggressionLadder.report.json":
        output.update(_aggression_fields(output, index))
    elif filename == "PR167_CounterfactualRouteSim.report.json":
        output.update(_counterfactual_fields(output, index))
    elif filename == "PR167_FillNoFillSim.report.json":
        output.update(_fill_fields(output, index))
    elif filename == "PR167_PartialFillSim.report.json":
        output.update(_partial_fill_fields(output, index))
    elif filename == "PR167_QueuePositionSim.report.json":
        output.update(_queue_position_fields(output, index))
    elif filename == "PR167_QueueSurvivalSim.report.json":
        output.update(_queue_survival_fields(output, index))
    elif filename == "PR167_LatencySim.report.json":
        output.update(_latency_fields(output, index))
    elif filename == "PR167_TCASim.report.json":
        output.update(_tca_fields(output, index))
    elif filename == "PR167_ImplementationShortfallSim.report.json":
        output.update(_shortfall_fields(output, index))
    elif filename == "PR167_SlippageImpactSim.report.json":
        output.update(_slippage_impact_fields(output, index))
    elif filename == "PR167_AdverseSelectionSim.report.json":
        output.update(_adverse_fields(output, index))
    elif filename == "PR167_CancelReplaceSim.report.json":
        output.update(_cancel_replace_fields(output, index))
    elif filename == "PR167_CapacityCrowdingSim.report.json":
        output.update(_capacity_fields(output, index))
    elif filename == "PR167_SettlementFinalitySim.report.json":
        output.update(_settlement_fields(output, index))
    elif filename == "PR167_ModelExecutionGap.report.json":
        output.update(_model_gap_fields(output, index))
    elif filename == "PR167_ClassicalFallbackSim.report.json":
        output.update(_classical_fields(output, index))
    elif filename == "PR167_QuantumHybridSim.report.json":
        output.update(_quantum_hybrid_fields(output, index))
    elif filename == "PR167_SimSurvivorRegistry.report.json":
        output.update(_survivor_fields(output, index))
    elif filename == "PR167_SimFailureRegistry.report.json":
        output.update(_failure_fields(output, index))
    elif filename == "PR167_SimPaperOnlyRegistry.report.json":
        output.update(_paper_only_fields(output, index))
    elif filename == "PR167_SimChampChallenger.report.json":
        output.update(_champ_challenger_fields(output, index))
    elif filename == "PR167_SimPromotionFirewall.report.json":
        output.update(_firewall_fields(output, index))
    elif filename == "PR167_SimRetestRepair.report.json":
        output.update(_repair_fields(output, index))
    elif filename == "PR167_ExecutionAdjustedSimRank.report.json":
        output.update(_rank_fields(output, index))
    elif filename == "PR167_SimCalibrationCoverage.report.json":
        output.update(_coverage_fields(output, index))
    elif filename == "PR167_OpenTradeRiskControls.report.json":
        output.update(_risk_control_fields(output, index))
    elif filename == "PR167_NoLiveAuthorityBoundary.report.json":
        output.update(_no_live_boundary_fields(output, index))
    elif filename == "PR167_OwnerDashboardReview.report.json":
        output.update(_dashboard_fields(output, index))
    elif filename == "PR167_PluginNeeds.report.json":
        output.update(_plugin_fields(output, index))
    elif filename == "PR167_OwnerAgentIntakeNeeds.report.json":
        output.update(_intake_fields(output, index))
    elif filename == "PR167_ConnectorRouteReady.report.json":
        output.update(_connector_fields(output, index))
    elif filename == "PR167_MarketPortability.report.json":
        output.update(_market_fields(output, index))
    elif filename == "PR167_AgentWorkOrders.report.json":
        output.update(_agent_work_order_fields(output, index))
    elif filename == "PR167_AgentDAG.report.json":
        output.update(_agent_dag_fields(output, index))
    elif filename == "PR167_NoOrphanProof.report.json":
        output.update(_no_orphan_fields(output, index))
    elif filename.startswith("PR167_To_"):
        output.update(_handoff_fields(filename, output, index))
    return output


def build_final_summary(source: SourceData, rows: list[dict[str, Any]]) -> dict[str, Any]:
    dispositions = Counter(row["simulator_disposition"] for row in rows)
    grades = Counter(row["simulator_quality_grade"] for row in rows)
    open_trade_count = sum(1 for row in source.records["PR166_QC_OpenTradeSimHandoff.report.json"] if row.get("open_trade_sim_route_flag") is True)
    summary = {
        **_base_report_row("PR167_FinalSummary.report.json", 1),
        "row_id": "PR167_FINALSUMMARY::00001",
        "consumed_pr167_handoff_rows": len(rows),
        "expected_pr167_handoff_rows": 559,
        "input_record_counts": dict(sorted(source.input_counts.items())),
        "upstream_report_consumption_count": len(c.STRICT_INPUT_REPORTS),
        "pr166_qc_open_trade_sim_handoff_count": open_trade_count,
        "pr162e_q_open_trade_sim_route_count": sum(1 for row in source.records["PR162E_Q_OpenTradeSimMap.report.json"] if row.get("open_trade_sim_route_flag") is True),
        "simulator_disposition_counts": dict(sorted(dispositions.items())),
        "simulator_quality_grade_counts": dict(sorted(grades.items())),
        "actual_sim_subset_count": sum(1 for row in rows if row["actual_sim_subset_flag"]),
        "simulator_budget_caps": dict(c.SIM_CAPS),
        "order_intent_rows": len(rows),
        "shadow_order_audit_rows": len(rows),
        "order_book_state_rows": len(rows),
        "price_side_normalization_rows": len(rows),
        "order_aggression_ladder_rows": len(rows),
        "counterfactual_route_sim_rows": len(rows),
        "fill_no_fill_rows": len(rows),
        "partial_fill_rows": len(rows),
        "queue_position_rows": len(rows),
        "queue_survival_rows": len(rows),
        "latency_rows": len(rows),
        "tca_rows": len(rows),
        "implementation_shortfall_rows": len(rows),
        "adverse_selection_rows": len(rows),
        "capacity_crowding_rows": len(rows),
        "cancel_replace_rows": len(rows),
        "settlement_finality_rows": len(rows),
        "model_execution_gap_rows": len(rows),
        "classical_fallback_rows": len(rows),
        "quantum_hybrid_rows": len(rows),
        "simulator_survivor_count": sum(1 for row in rows if row["simulator_survival_flag"]),
        "simulator_failure_count": sum(1 for row in rows if row["simulator_failure_reason"]),
        "simulator_champion_count": sum(1 for row in rows if row["simulator_champion_flag"]),
        "simulator_challenger_count": sum(1 for row in rows if row["simulator_challenger_flag"]),
        "simulator_watch_count": sum(1 for row in rows if row["simulator_watch_flag"]),
        "simulator_retest_count": sum(1 for row in rows if row["simulator_retest_flag"]),
        "simulator_repair_count": sum(1 for row in rows if row["simulator_repair_flag"]),
        "paper_only_count": sum(1 for row in rows if row["paper_only_flag"]),
        "no_trade_nonlive_count": sum(1 for row in rows if row["no_trade_nonlive_flag"]),
        "owner_dashboard_review_count": sum(1 for row in rows if row["owner_dashboard_review_flag"]),
        "plugin_needs_count": sum(1 for row in rows if row["plugin_needed_flag"]),
        "owner_agent_intake_needs_count": sum(1 for row in rows if row["owner_agent_intake_needed_flag"]),
        "connector_route_readiness_count": len(rows),
        "market_portability_rows": len(rows),
        "report_consumer_crosswalk_rows": len(c.STRICT_INPUT_REPORTS) + len(c.REPORT_FILENAMES),
        "agent_work_order_rows": len(rows),
        "agent_dag_rows": len(rows),
        "no_orphan_rows": len(rows),
        "downstream_pr166_qc_retest_handoff_count": len(rows),
        "downstream_pr162e_handoff_count": len(rows),
        "downstream_pr162f_handoff_count": len(rows),
        "downstream_owner_dashboard_handoff_count": len(rows),
        "downstream_cloud_switchboard_handoff_count": len(rows),
        "downstream_future_connectors_handoff_count": len(rows),
        "forbidden_authority_counts_all_zero_flag": True,
        "dashboard_ui_implemented_flag": False,
        "live_ready_rows": 0,
        **authority_zero_counts(),
    }
    return summary


def build_crosswalk_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(_crosswalk_row(index, filename, produced_by=_source_pr_for_report(filename), consumed=True))
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(_crosswalk_row(index, filename, produced_by=c.PR_ID, consumed=False, payload=payloads.get(filename)))
        index += 1
    return rows


def build_artifact_map_rows(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(_artifact_map_row(index, f"PR167_CONSUMED::{filename}", f"docs/master_plan/generated/{filename}", "consumed_upstream_report", produced_by=_source_pr_for_report(filename)))
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(_artifact_map_row(index, f"PR167_REPORT::{filename}", f"docs/master_plan/generated/{filename}", "generated_root_report", produced_by=c.PR_ID))
        index += 1
    for shard_path in sorted(shard_payloads):
        rows.append(_artifact_map_row(index, f"PR167_SHARD::{Path(shard_path).name}", shard_path, "generated_shard_report", produced_by=c.PR_ID))
        index += 1
    for filename in schema_filenames():
        rows.append(_artifact_map_row(index, f"PR167_SCHEMA::{filename}", f"{c.SCHEMA_DIR.as_posix()}/{filename}", "generated_schema", produced_by=c.PR_ID))
        index += 1
    for tool_path in (c.BUILDER_REF, c.VALIDATOR_REF):
        rows.append(_artifact_map_row(index, f"PR167_TOOL::{tool_path}", tool_path, "tool_entrypoint", produced_by=c.PR_ID))
        index += 1
    return rows


def payloads_from_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        sharded = filename in c.ROW_REPORTS and len(rows) > 0
        shard_files: list[str] = []
        shard_manifest_refs: list[dict[str, Any]] = []
        if sharded:
            chunks = _chunks(rows, c.DEFAULT_SHARD_ROW_TARGET)
            for shard_index, chunk in enumerate(chunks, start=1):
                shard_name = f"{filename.removesuffix('.report.json')}.part_{shard_index:04d}_of_{len(chunks):04d}.report.json"
                shard_path = c.SHARD_DIR / shard_name
                shard_ref = shard_path.as_posix()
                shard_files.append(shard_ref)
                shard_manifest_refs.append({"shard_index": shard_index, "shard_path": shard_ref, "row_count": len(chunk)})
                shard_payloads[shard_ref] = {
                    **_report_metadata(filename, len(chunk), sharded=False),
                    "records": chunk,
                    "shard_index": shard_index,
                    "shard_count": len(chunks),
                    "root_report_ref": f"docs/master_plan/generated/{filename}",
                }
        payload = _report_metadata(filename, len(rows), sharded=sharded)
        if sharded:
            payload.update(
                {
                    "records": [],
                    "records_omitted_for_sharding_flag": True,
                    "shard_count": len(shard_files),
                    "shard_files": shard_files,
                    "shard_manifest_refs": shard_manifest_refs,
                }
            )
        else:
            payload["records"] = rows
        payloads[filename] = payload
    return payloads, shard_payloads


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        payload = payloads.get(filename, {})
        rows.append(
            {
                **_base_report_row("PR167_ReportManifest.report.json", index),
                "row_id": f"PR167_MANIFEST::{index:05d}",
                "report_ref": filename,
                "report_path": f"docs/master_plan/generated/{filename}",
                "record_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref") or schema_filename(filename),
                "sharded_flag": bool(payload.get("sharded_flag")),
                "shard_files": payload.get("shard_files", []),
                "consumer_report_refs": [
                    "PR167_ReportConsumerCrosswalk.report.json",
                    "PR167_ArtifactMap.report.json",
                    "PR167_NoOrphanProof.report.json",
                ],
                "terminal_flag": False,
                "terminal_reason": "",
            }
        )
    return rows


def write_schemas(repo_root: Path) -> None:
    for filename in schema_filenames():
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": filename,
            "type": "object",
            "required": ["report_name", "roadmap_pr_id", "created_by_pr", "schema_ref", "record_count", "records"],
            "properties": {
                "report_name": {"type": "string"},
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "schema_ref": {"const": filename},
                "record_count": {"type": "integer", "minimum": 0},
                "records": {"type": "array"},
                "sharded_flag": {"type": "boolean"},
                "shard_files": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / filename, schema)


def schema_filenames() -> tuple[str, ...]:
    return tuple(schema_filename(filename) for filename in c.REPORT_FILENAMES)


def schema_filename(report_filename: str) -> str:
    stem = report_filename.removesuffix(".report.json").replace("PR167", "pr167")
    for acronym in ("TCA", "FDR", "DAG", "QC"):
        stem = stem.replace(acronym, f"_{acronym.lower()}_")
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", stem).replace("__", "_").strip("_").lower()
    return f"{snake}.schema.json"


def _report_metadata(filename: str, record_count: int, *, sharded: bool) -> dict[str, Any]:
    return {
        "report_name": filename,
        "report_filename": filename,
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "schema_ref": schema_filename(filename),
        "builder_ref": c.BUILDER_REF,
        "validator_ref": c.VALIDATOR_REF,
        "validation_status": c.VALIDATION_STATUS,
        "source_input_reports": list(c.STRICT_INPUT_REPORTS),
        "record_count": record_count,
        "sharded_flag": sharded,
        **authority_zero_counts(),
    }


def _base_report_row(report_name: str, index: int) -> dict[str, Any]:
    return {
        "artifact_id": report_name.removesuffix(".report.json"),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "validation_status": c.VALIDATION_STATUS,
        "validator_ref": c.VALIDATOR_REF,
        "builder_ref": c.BUILDER_REF,
        "deterministic_sort_key": f"{report_name}::{index:05d}",
        "terminal_flag": False,
        "terminal_reason": "",
        **authority_zero_counts(),
        **authority_false_flags(),
        **simulator_true_flags(),
    }


def _crosswalk_row(index: int, filename: str, *, produced_by: str, consumed: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        **_base_report_row("PR167_ReportConsumerCrosswalk.report.json", index),
        "row_id": f"PR167_CROSSWALK::{index:05d}",
        "report_id": filename.removesuffix(".report.json"),
        "report_path": f"docs/master_plan/generated/{filename}",
        "producer_module": "upstream_generated_report" if consumed else c.PACKAGE_IMPORT,
        "producer_pr": produced_by,
        "owning_agent_id": "Governance",
        "consuming_agent_ids": ["Governance", "Commander", "Open Trade Simulator Agent"],
        "consuming_downstream_reports": [
            "PR167_ArtifactMap.report.json",
            "PR167_NoOrphanProof.report.json",
            "PR167_FinalSummary.report.json",
        ],
        "consuming_downstream_prs": list(c.DOWNSTREAM_PR_REFS),
        "dashboard_visibility_flag": filename in {"PR167_OwnerDashboardReview.report.json", "PR167_FinalSummary.report.json"},
        "governance_visibility_flag": True,
        "commander_visibility_flag": True,
        "terminal_flag": False,
        "terminal_reason": "",
        "no_orphan_proof_ref": "PR167_NoOrphanProof.report.json",
        "record_count": 0 if payload is None else payload.get("record_count", 0),
    }


def _artifact_map_row(index: int, artifact_id: str, artifact_path: str, artifact_type: str, *, produced_by: str) -> dict[str, Any]:
    return {
        **_base_report_row("PR167_ArtifactMap.report.json", index),
        "row_id": f"PR167_ARTIFACTMAP::{index:05d}",
        "artifact_id": artifact_id,
        "artifact_path": normalize_repo_ref(artifact_path),
        "artifact_type": artifact_type,
        "produced_by_pr": produced_by,
        "consumed_by_module": c.PACKAGE_IMPORT,
        "consumed_by_report": "PR167_ReportConsumerCrosswalk.report.json",
        "consumed_by_agent": "Open Trade Simulator Agent",
        "consumed_by_downstream_pr": list(c.DOWNSTREAM_PR_REFS),
        "terminal_flag": False,
        "terminal_reason": "",
        "validation_ref": c.VALIDATOR_REF,
        "owner_review_ref": "PR167_OwnerDashboardReview.report.json",
    }


def _refs(index: int) -> dict[str, str]:
    return {
        "order_intent": f"PR167_ORDER_INTENT::{index:05d}",
        "shadow": f"PR167_SHADOW_ORDER::{index:05d}",
        "book": f"PR167_BOOK_STATE::{index:05d}",
        "counterfactual": f"PR167_COUNTERFACTUAL::{index:05d}",
        "firewall": f"PR167_FIREWALL::{index:05d}",
        "connector": f"PR167_CONNECTOR_ROUTE::{index:05d}",
        "market": f"PR167_MARKET_PORTABILITY::{index:05d}",
        "no_orphan": f"PR167_NO_ORPHAN::{index:05d}",
        "classical": f"PR167_CLASSICAL_FALLBACK::{index:05d}",
        "hybrid": f"PR167_QUANTUM_HYBRID::{index:05d}",
        "interpret": f"PR162E_Q_INTERPRET::{index:05d}",
        "proof": f"PR162E_Q_PROOF::{index:05d}",
        "test": f"PR162E_Q_TEST_VECTOR::{index:05d}",
        "to_pr166_qc": f"PR167_TO_PR166_QC_RETEST::{index:05d}",
        "to_pr162e": f"PR167_TO_PR162E::{index:05d}",
        "to_pr162f": f"PR167_TO_PR162F::{index:05d}",
        "to_dashboard": f"PR167_TO_OWNER_DASHBOARD::{index:05d}",
        "to_cloud": f"PR167_TO_CLOUD_SWITCHBOARD::{index:05d}",
        "to_future": f"PR167_TO_FUTURE_CONNECTORS::{index:05d}",
    }


def _report_refs(index: int) -> dict[str, str]:
    return {
        "sim_eligibility_ref": f"PR167_SIMELIGIBILITY::{index:05d}",
        "sim_subset_selection_ref": f"PR167_SIMSUBSETSELECTION::{index:05d}",
        "fill_no_fill_sim_ref": f"PR167_FILLNOFILLSIM::{index:05d}",
        "partial_fill_sim_ref": f"PR167_PARTIALFILLSIM::{index:05d}",
        "queue_position_sim_ref": f"PR167_QUEUEPOSITIONSIM::{index:05d}",
        "queue_survival_sim_ref": f"PR167_QUEUESURVIVALSIM::{index:05d}",
        "latency_sim_ref": f"PR167_LATENCYSIM::{index:05d}",
        "tca_sim_ref": f"PR167_TCASIM::{index:05d}",
        "implementation_shortfall_sim_ref": f"PR167_IMPLEMENTATIONSHORTFALLSIM::{index:05d}",
        "calibration_coverage_ref": f"PR167_SIMCALIBRATIONCOVERAGE::{index:05d}",
    }


def _row_id_for_report(filename: str, index: int) -> str:
    stem = filename.removesuffix(".report.json").replace("PR167_", "").upper()
    return f"PR167_{stem}::{index:05d}"


def _order_intent_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "order_intent_id": f"PR167_ORDER_INTENT::{index:05d}",
        "source_handoff_ref": row["source_pr162e_q_handoff_ref"],
        "quantum_precompute_ref": row["quantum_recipe_ref"],
        "side": row["order_side"],
        "price_candidate": row["normalized_price"],
        "quantity_candidate": row["normalized_quantity"],
        "expected_edge_candidate": row["expected_value_delta_candidate"],
        "no_live_authority_flag": True,
    }


def _shadow_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "shadow_order_id": f"PR167_SHADOW_ORDER::{index:05d}",
        "order_intent_ref": row["order_intent_ref"],
        "simulator_only_flag": True,
        "real_order_id": None,
        "audit_reason": "SHADOW_ORDER_AUDIT_NONLIVE_SIMULATOR_ONLY",
        "downstream_review_ref": row["downstream_owner_dashboard_route_ref"],
    }


def _book_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "book_state_id": f"PR167_BOOK_STATE::{index:05d}",
        "source_row_ref": row["source_sim_row_ref"],
        "book_state_provenance": row["book_state_provenance"],
        "structural_only_reason": row["structural_only_reason"],
        "no_connector_binding_flag": True,
        "no_live_market_call_flag": True,
    }


def _price_norm_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "price_side_norm_id": f"PR167_PRICE_SIDE_NORM::{index:05d}",
        "price_unit": "PREDICTION_MARKET_PRICE_0_TO_1",
        "probability_unit": "PROBABILITY_0_TO_1",
        "edge_unit": "EXPECTED_NET_PROFIT_PER_ORDER_CANDIDATE_NOT_EVIDENCE",
        "order_size_unit": "CONTRACTS_OR_SHARES_NORMALIZED",
        "TCA_unit": "NORMALIZED_PRICE_POINTS",
        "latency_unit": "MILLISECONDS",
        "fill_probability_unit": "PROBABILITY_0_TO_1",
        "normalized_probability": row["normalized_price"] if row["YES_NO_side"] == "YES" else _round(1.0 - row["normalized_price"]),
        "normalized_expected_edge": row["expected_value_delta_candidate"],
        "normalized_expected_net_profit_per_order_candidate": row["expected_net_profit_per_order_candidate"],
    }


def _lifecycle_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "order_lifecycle_id": f"PR167_LIFECYCLE::{index:05d}",
        "lifecycle_states": row["lifecycle_trace"],
        "transition_reason": row["lifecycle_trace"][-1]["transition_reason"],
        "timestamp_order_index": len(row["lifecycle_trace"]),
        "simulated_not_real_flag": True,
        "shadow_order_flag": True,
        "no_live_authority_flag": True,
        "downstream_route_ref": row["downstream_pr166_qc_retest_route_ref"],
    }


def _aggression_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    selected = row["selected_counterfactual_winner"]
    return {
        "aggression_ladder_id": f"PR167_AGGRESSION::{index:05d}",
        "selected_route": selected,
        "route_selection_reason": "MAX_SCORE_UNDER_SAME_BOOK_STATE_BOUNDED_NONLIVE",
        "maker_taker_assumption": row["maker_taker_route_candidate"],
        "expected_fill_delta_by_route": _round(row["fill_probability_score"] - row["no_fill_risk_score"]),
        "expected_TCA_delta_by_route": _round(-row["total_TCA_candidate"]),
        "expected_latency_delta_by_route": _round(-row["simulated_latency_ms"] / 100000.0),
        "expected_adverse_selection_delta_by_route": _round(-row["adverse_selection_component"]),
        "no_live_authority_flag": True,
    }


def _counterfactual_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "counterfactual_route_id": f"PR167_COUNTERFACTUAL::{index:05d}",
        "not_profit_evidence_flag": True,
        "no_live_authority_flag": True,
    }


def _fill_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "fill_no_fill_sim_id": f"PR167_FILL_NO_FILL::{index:05d}",
        "structural_only_reason": row["structural_only_reason"],
    }


def _partial_fill_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "partial_fill_sim_id": f"PR167_PARTIAL_FILL::{index:05d}",
        "partial_fill_model_reason": "PARTIAL_FILL_PROXY_FROM_QUEUE_AHEAD_DEPTH_AND_FILL_PROBABILITY",
        "structural_only_reason": row["structural_only_reason"],
    }


def _queue_position_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "queue_position_sim_id": f"PR167_QUEUE_POSITION::{index:05d}",
        "queue_position_model_reason": "PRICE_TIME_PRIORITY_QUEUE_AHEAD_PROXY",
    }


def _queue_survival_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "queue_survival_sim_id": f"PR167_QUEUE_SURVIVAL::{index:05d}",
        "queue_risk_reason": "QUEUE_SURVIVAL_FROM_CANCEL_RATE_MARKET_ORDER_ARRIVAL_AND_IMBALANCE_PROXY",
    }


def _latency_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "latency_sim_id": f"PR167_LATENCY::{index:05d}",
        "simulated_order_path_latency_ms": row["simulated_latency_ms"],
        "precompute_only_flag": True,
        "hot_path_allowed_flag": False,
    }


def _tca_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {"tca_sim_id": f"PR167_TCA::{index:05d}", "not_profit_evidence_flag": True}


def _shortfall_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "implementation_shortfall_sim_id": f"PR167_IMPLEMENTATION_SHORTFALL::{index:05d}",
        "not_profit_evidence_flag": True,
    }


def _slippage_impact_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "slippage_impact_sim_id": f"PR167_SLIPPAGE_IMPACT::{index:05d}",
        "slippage_score": _round(_clamp(1.0 - row["slippage_component"] * 20.0, 0.0, 1.0)),
        "impact_score": _round(_clamp(1.0 - row["impact_component"] * 20.0, 0.0, 1.0)),
    }


def _adverse_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "adverse_selection_sim_id": f"PR167_ADVERSE_SELECTION::{index:05d}",
        "adverse_selection_proxy": row["adverse_selection_component"],
        "queue_imbalance_adverse_selection_proxy": _round(max(0.0, -row["queue_imbalance_proxy"])),
        "price_move_against_order_proxy": _round(row["adverse_selection_component"] + row["synthetic_book_penalty"]),
        "stale_signal_proxy": row["synthetic_book_penalty"],
        "downstream_repair_route_ref": row["downstream_pr166_qc_retest_route_ref"],
    }


def _cancel_replace_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    attempts = c.SIM_CAPS["max_cancel_replace_attempts_default_ci"]
    return {
        "cancel_replace_sim_id": f"PR167_CANCEL_REPLACE::{index:05d}",
        "max_cancel_replace_attempts": attempts,
        "cancel_trigger_reason": "STALE_BOOK_OR_QUEUE_DECAY_TRIGGER",
        "replace_trigger_reason": "PRICE_IMPROVEMENT_OR_NO_FILL_RISK_TRIGGER",
        "stale_order_cancel_flag": bool(row["stale_book_flag"]),
        "queue_position_loss_proxy": _round((1.0 - row["queue_survival_score"]) * 0.25),
        "latency_added_by_replace_ms": attempts * 12,
        "cancel_replace_score": _round(_clamp(row["queue_survival_score"] - attempts * 0.02, 0.0, 1.0)),
        "no_live_authority_flag": True,
    }


def _capacity_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "capacity_crowding_sim_id": f"PR167_CAPACITY_CROWDING::{index:05d}",
        "capacity_estimate": _round(row["depth_at_price"] * 0.12),
        "market_depth_proxy": row["depth_at_price"],
        "participation_cap_candidate": _round(min(row["normalized_quantity"], row["depth_at_price"] * 0.1)),
        "liquidity_availability": row["liquidity_bucket"],
        "size_sensitivity": _round(row["normalized_quantity"] / max(row["depth_at_price"], 1.0)),
        "spread_sensitivity": row["spread"],
        "crowding_estimate": _round(1.0 - row["crowding_adjusted_score"]),
        "crowding_warning_reason": "CROWDING_TRACKED_NO_LIVE_AUTHORITY",
    }


def _settlement_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "settlement_finality_sim_id": f"PR167_SETTLEMENT_FINALITY::{index:05d}",
        "event_resolution_dependency": "PREDICTION_MARKET_EVENT_RESOLUTION_SOURCE_NOT_ACCEPTED_AS_TRUTH",
        "settlement_finality_risk": row["settlement_finality_component"],
        "ambiguity_risk_proxy": _round(row["settlement_finality_component"] * 2.0),
        "market_resolution_state_proxy": "UNRESOLVED_SIMULATOR_PROXY",
        "settlement_penalty_candidate": row["settlement_finality_component"],
        "finality_adjusted_score": _round(_clamp(1.0 - row["settlement_finality_component"] * 20.0, 0.0, 1.0)),
        "no_source_truth_acceptance_flag": True,
    }


def _model_gap_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "model_execution_gap_id": f"PR167_MODEL_EXECUTION_GAP::{index:05d}",
        "model_decision_price": row["decision_price"],
        "model_execution_gap": row["model_execution_gap_component"],
        "model_execution_gap_reason": "MODEL_DECISION_TO_SIMULATED_EXECUTION_TRANSLATION_GAP_PROXY",
        "downstream_repair_route_ref": row["downstream_pr166_qc_retest_route_ref"],
    }


def _classical_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "classical_fallback_sim_id": f"PR167_CLASSICAL_FALLBACK::{index:05d}",
        "classical_fallback_available": True,
        "classical_fallback_score": row["classical_fallback_route_score"],
    }


def _quantum_hybrid_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "quantum_hybrid_sim_id": f"PR167_QUANTUM_HYBRID::{index:05d}",
        "quantum_precompute_available": True,
        "quantum_hybrid_selection_score": row["quantum_precompute_route_score"],
        "hybrid_selects_classical_executes_flag": True,
        "true_quantum_structural_only_flag": True,
        "quantum_backend_execution_flag": False,
        "cloud_backend_execution_flag": False,
        "no_live_authority_flag": True,
    }


def _survivor_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "survivor_id": f"PR167_SURVIVOR::{index:05d}",
        "source_sim_row_ref": row["source_sim_row_ref"],
        "survival_reason": row["survival_reason"],
        "TCA_score": row["tca_adjusted_score"],
        "fill_score": row["fill_probability_score"],
        "latency_score": row["latency_adjusted_score"],
        "queue_risk_score": row["queue_risk_adjusted_score"],
        "capacity_score": row["capacity_adjusted_score"],
        "overfit_score": row["overfit_adjusted_score"],
        "marginal_utility_score": row["marginal_utility_score"],
        "downstream_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "no_live_authority_flag": True,
    }


def _failure_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    reason = row["primary_failure_reason"]
    return {
        "failure_id": f"PR167_FAILURE::{index:05d}",
        "primary_failure_reason": reason,
        "failed_due_to_fill_no_fill_flag": reason == "FILL_NO_FILL_RISK",
        "failed_due_to_partial_fill_flag": reason == "PARTIAL_FILL_INSUFFICIENT",
        "failed_due_to_latency_flag": reason == "LATENCY_BREACH",
        "failed_due_to_queue_risk_flag": reason == "QUEUE_RISK",
        "failed_due_to_queue_survival_flag": reason == "QUEUE_SURVIVAL",
        "failed_due_to_TCA_flag": reason == "TCA_DRAG",
        "failed_due_to_implementation_shortfall_flag": reason == "IMPLEMENTATION_SHORTFALL",
        "failed_due_to_capacity_crowding_flag": reason == "CAPACITY_CROWDING",
        "failed_due_to_adverse_selection_flag": reason == "ADVERSE_SELECTION",
        "failed_due_to_stale_book_flag": reason == "STALE_BOOK",
        "failed_due_to_cancel_replace_flag": reason == "CANCEL_REPLACE_DEGRADATION",
        "failed_due_to_model_execution_gap_flag": reason == "MODEL_EXECUTION_GAP",
        "repair_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "no_live_authority_flag": True,
    }


def _paper_only_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "paper_only_id": f"PR167_PAPER_ONLY::{index:05d}",
        "paper_only_reason": "STRUCTURAL_RUNTIME_CAP_OR_PAPER_RETEST_ROUTE" if row["paper_only_flag"] else "NOT_PAPER_ONLY",
    }


def _champ_challenger_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "sim_champ_challenger_id": f"PR167_CHAMP_CHALLENGER::{index:05d}",
        "simulator_champion": row["simulator_champion_flag"],
        "simulator_challenger": row["simulator_challenger_flag"],
        "simulator_watch": row["simulator_watch_flag"],
        "simulator_retest": row["simulator_retest_flag"],
        "simulator_repair": row["simulator_repair_flag"],
        "paper_only": row["paper_only_flag"],
        "no_trade_nonlive": row["no_trade_nonlive_flag"],
        "plugin_needed": row["plugin_needed_flag"],
        "owner_agent_intake_needed": row["owner_agent_intake_needed_flag"],
        "owner_dashboard_review_needed": row["owner_dashboard_review_flag"],
    }


def _firewall_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "firewall_row_id": f"PR167_FIREWALL::{index:05d}",
        "source_sim_row_ref": row["source_sim_row_ref"],
        "simulator_survivor_flag": row["simulator_survival_flag"],
        "blocker_reasons": row["secondary_failure_reasons"] or ["FUTURE_LIVE_AUTHORITY_PR_REQUIRED"],
        "no_live_authority_flag": True,
    }


def _repair_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "repair_row_id": f"PR167_REPAIR::{index:05d}",
        "primary_failure_reason": row["primary_failure_reason"],
        "repair_family": _repair_family(row),
        "proposed_price_delta": _round(-row["spread"] * 0.25),
        "proposed_size_delta": _round(-row["normalized_quantity"] * 0.2),
        "proposed_time_in_force_delta": "SWITCH_TO_SHORTER_TIF_FOR_STALE_OR_NO_FILL_RISK",
        "proposed_cancel_replace_delta": "REDUCE_REPLACE_ATTEMPTS_IF_QUEUE_LOSS_DOMINATES",
        "proposed_route_delta": "COMPARE_NEAR_TOUCH_AND_NO_TRADE_ROUTE_IN_RETEST",
        "expected_fill_delta_candidate": _round(row["no_fill_risk_score"] * 0.08),
        "expected_latency_delta_candidate": _round(-row["simulated_latency_ms"] / 100000.0),
        "expected_TCA_delta_candidate": _round(-row["total_TCA_candidate"] * 0.12),
        "expected_implementation_shortfall_delta_candidate": _round(-row["implementation_shortfall_proxy"] * 0.1),
        "expected_queue_risk_delta_candidate": _round((1.0 - row["queue_survival_score"]) * 0.06),
        "expected_net_profit_delta_candidate": _round(max(0.0, -row["expected_net_profit_per_order_candidate"]) * 0.25),
        "downstream_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "owning_agent_id": "Execution/TCA Agent",
        "reviewer_agent_id": "Governance",
        "not_profit_evidence_flag": True,
        "no_live_authority_flag": True,
    }


def _rank_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "rank_row_id": f"PR167_RANK::{index:05d}",
        "execution_adjusted_expected_edge": row["expected_net_profit_per_order_candidate"],
        "lower_confidence_bound_edge": _round(row["expected_net_profit_per_order_candidate"] - row["false_discovery_penalty"] * 0.2),
        "quantum_precompute_benefit": _round(row["quantum_precompute_route_score"] - row["classical_fallback_route_score"]),
        "classical_fallback_safety_bonus": 0.01,
        "hot_path_penalty": 0.02,
        "repair_potential_bonus": 0.008 if row["simulator_repair_flag"] else 0.002,
    }


def _coverage_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "simulator_row_ref": row["source_sim_row_ref"],
        "book_state_count": 1 if row["actual_sim_subset_flag"] else 0,
        "scenario_count": 1 if row["actual_sim_subset_flag"] else 0,
        "seed_count": c.SIM_CAPS["max_random_seeds_default_ci"] if row["actual_sim_subset_flag"] else 0,
        "price_level_count": min(c.SIM_CAPS["max_price_levels_default_ci"], 3),
        "queue_position_count": min(c.SIM_CAPS["max_queue_positions_default_ci"], 3),
        "order_size_bucket_count": 1,
        "coverage_score": _round(0.72 if row["actual_sim_subset_flag"] else 0.28),
        "calibration_source": "PR166_QC_REPLAY_PAPER_EVIDENCE_PLUS_GENERATED_STRUCTURAL_BOOK",
        "confidence_bucket": "SIM_COVERAGE_MEDIUM" if row["actual_sim_subset_flag"] else "STRUCTURAL_ONLY_LOW",
    }


def _risk_control_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "risk_control_id": f"PR167_RISK_CONTROL::{index:05d}",
        "kill_switch_required_flag": True,
        "max_order_size_candidate": min(row["normalized_quantity"], 25.0),
        "max_latency_ms_candidate": row["latency_budget_ms"],
        "min_fill_probability_candidate": 0.55,
        "max_TCA_candidate": 0.04,
        "max_implementation_shortfall_candidate": 0.04,
        "max_queue_risk_candidate": 0.45,
        "max_capacity_usage_candidate": 0.1,
        "max_crowding_candidate": 0.45,
        "stale_book_block_flag": row["stale_book_flag"],
        "adverse_selection_block_flag": row["adverse_selection_component"] > 0.006,
        "cancel_replace_limit_required_flag": True,
        "future_live_pr_required_flag": True,
    }


def _no_live_boundary_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "boundary_row_id": f"PR167_NO_LIVE_BOUNDARY::{index:05d}",
        "authority_boundary_verified_flag": True,
        "simulated_fill_is_real_fill_flag": False,
        "simulated_pnl_is_profit_evidence_flag": False,
    }


def _dashboard_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dashboard_review_id": f"PR167_DASHBOARD_REVIEW::{index:05d}",
        "reason_for_owner_review": _dashboard_reason(row),
        "failed_after_costs_flag": row["simulator_failure_reason"] in {"TCA_DRAG", "IMPLEMENTATION_SHORTFALL"} or row["expected_net_profit_per_order_candidate"] < 0,
        "repair_needed_flag": row["simulator_repair_flag"],
        "replay_paper_summary": f"retest={row['simulator_retest_flag']}; paper_only={row['paper_only_flag']}",
        "simulator_summary": f"disposition={row['simulator_disposition']}; grade={row['simulator_quality_grade']}; actual={row['actual_sim_subset_flag']}",
        "future_dashboard_pr_ref": "FUTURE_OWNER_DASHBOARD_REVIEW_NO_UI_IN_PR167",
        "dashboard_ui_implemented_flag": False,
    }


def _plugin_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "plugin_need_id": f"PR167_PLUGIN_NEED::{index:05d}",
        "needed_plugin_family": f"OPEN_TRADE_SIMULATOR_{row['model_family_selected']}_ADAPTER",
        "simulator_interface_candidate": "bounded_open_trade_simulator_receipt_interface",
        "order_book_model_interface_candidate": "deterministic_book_state_proxy_interface",
        "fill_model_interface_candidate": "fill_partial_no_fill_probability_interface",
        "TCA_model_interface_candidate": "tca_slippage_impact_shortfall_interface",
        "latency_model_interface_candidate": "decision_precompute_classical_order_path_latency_interface",
        "replay_paper_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "downstream_pr162e_ref": row["downstream_pr162e_route_ref"],
    }


def _intake_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "intake_need_id": f"PR167_INTAKE_NEED::{index:05d}",
        "owner_question": "Confirm acceptable simulator assumptions before replay/paper retest promotion route?",
        "agent_research_task": "Collect better order book, queue position, TCA, latency, and stale-book parameters.",
        "missing_formula_component": "ORDER_SIZE_PRICE_QUEUE_POSITION_TIF_CONFIDENCE_COVERAGE",
        "missing_parameter_component": "BOOK_DEPTH_FILL_LATENCY_CANCEL_REPLACE_CAPACITY_THRESHOLDS",
        "missing_order_book_component": "LIVE_CONNECTOR_BOOK_NOT_BOUND_IN_PR167",
        "missing_simulator_component": "EXPANDED_SCENARIO_COVERAGE_BEYOND_DEFAULT_CI_CAP",
        "missing_source_component": "SOURCE_TRUTH_NOT_ACCEPTED_ROUTE_TO_REVIEW",
        "candidate_assumption_ref": "PR167_SourceSimParams.report.json",
        "replay_paper_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "downstream_pr162f_ref": row["downstream_pr162f_route_ref"],
    }


def _connector_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "connector_route_id": f"PR167_CONNECTOR_ROUTE::{index:05d}",
        "future_connector_family": "PREDICTION_MARKET_CLOB_CONNECTOR_ROUTE_ONLY",
        "future_market_family": "prediction_market",
        "required_data_fields": ["event_id", "market_id", "book_snapshot", "queue_position", "fee_schedule", "latency", "settlement_state"],
        "missing_data_fields": ["connector_semantics", "private_account_state", "live_order_permission"],
        "candidate_source_refs": ["PR167_SourceSimParams.report.json"],
        "no_current_connector_binding_flag": True,
        "no_source_truth_acceptance_flag": True,
        "no_private_state_fetch_flag": True,
        "downstream_connector_pr_ref": row["downstream_future_connector_route_ref"],
    }


def _market_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "compatible_future_market_families": list(c.FUTURE_MARKET_FAMILIES),
        "market_specific_inputs_required": ["order_book", "fee_schedule", "tick_size", "settlement_finality", "position_limits"],
        "execution_route_portability_class": "ROUTE_METADATA_ONLY_NO_LIVE_AUTHORITY",
        "data_binding_portability_class": "CANDIDATE_FIELDS_ONLY_NO_SOURCE_TRUTH",
        "connector_required_future_flag": True,
        "no_current_connector_binding_flag": True,
        "downstream_future_market_pr_ref": "FUTURE_MARKET_PLATFORM_PORTABILITY_PR",
    }


def _agent_work_order_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "work_order_id": f"PR167_WORK_ORDER::{index:05d}",
        "source_artifact_ref": "PR167_SimEligibility.report.json",
        "source_row_ref": row["source_sim_row_ref"],
        "task_type": row["simulator_disposition"],
        "task_priority": "HIGH" if row["simulator_champion_flag"] or row["simulator_failure_reason"] else "MEDIUM",
        "expected_input_refs": row["upstream_refs"],
        "expected_output_refs": row["downstream_refs"],
        "downstream_agent_refs": ["Replay Agent", "Paper Agent", "Execution/TCA Agent", "Dashboard/Owner Review Agent"],
        "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
        "review_required_flag": True,
        "escalation_required_flag": row["simulator_failure_reason"] != "",
        "terminal_flag": False,
        "terminal_reason": "",
    }


def _agent_dag_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dag_node_id": f"PR167_DAG::{index:05d}",
        "upstream_pr_refs": ["PR166-QC", "PR162E-Q", "PR166-QB", "PR166-Q", "PR165-D2"],
        "upstream_row_refs": row["upstream_refs"],
        "simulator_receipt_route": row["source_sim_row_ref"],
        "replay_route": row["downstream_pr166_qc_retest_route_ref"],
        "plugin_framework_route": row["downstream_pr162e_route_ref"],
        "owner_agent_intake_route": row["downstream_pr162f_route_ref"],
        "connector_readiness_route": row["downstream_future_connector_route_ref"],
        "future_cloud_switchboard_route": row["downstream_cloud_switchboard_route_ref"],
        "future_owner_dashboard_route": row["downstream_owner_dashboard_route_ref"],
        "downstream_agent_refs": ["Open Trade Simulator Agent", "Execution/TCA Agent", "Replay Agent", "Paper Agent"],
        "dashboard_visibility_flag": row["owner_dashboard_review_flag"],
        "governance_visibility_flag": True,
        "commander_visibility_flag": True,
        "no_orphan_proof": row["no_orphan_proof_ref"],
        "expected_agent_output_artifact": "PR167_SimRetestRepair.report.json",
    }


def _no_orphan_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "no_orphan_id": f"PR167_NO_ORPHAN::{index:05d}",
        "no_orphan_status": "NO_ORPHAN",
        "artifact_refs_checked": [
            "PR167_SimEligibility.report.json",
            "PR167_OrderIntent.report.json",
            "PR167_ShadowOrderAudit.report.json",
            "PR167_ReportConsumerCrosswalk.report.json",
            "PR167_ArtifactMap.report.json",
        ],
        "responsible_agent_ref": row["owning_agent_id"],
        "downstream_consumer_refs": row["downstream_refs"],
        "orphan_count": 0,
        "terminal_flag": False,
        "terminal_reason": "",
    }


def _handoff_fields(filename: str, row: dict[str, Any], index: int) -> dict[str, Any]:
    route = filename.removesuffix(".report.json").replace("PR167_To_", "")
    return {
        "handoff_id": f"PR167_TO_{route.upper()}::{index:05d}",
        "source_sim_row_ref": row["source_sim_row_ref"],
        "downstream_pr_ref": _downstream_pr_for_route(route),
        "downstream_route": route,
        "handoff_reason": _handoff_reason(route, row),
        "simulator_disposition": row["simulator_disposition"],
        "simulator_quality_grade": row["simulator_quality_grade"],
        "order_intent_ref": row["order_intent_ref"],
        "shadow_order_audit_ref": row["shadow_order_audit_ref"],
        "counterfactual_route_ref": row["counterfactual_route_ref"],
        "classical_fallback_ref": row["classical_fallback_ref"],
        "hybrid_recipe_ref": row["hybrid_recipe_ref"],
        "no_live_authority_flag": True,
        "no_connector_binding_flag": True,
        "no_profit_evidence_flag": True,
    }


def _sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda item: str(item.get("deterministic_sort_key") or item.get("row_id")))


def _primary_ref(ctx: dict[str, Any]) -> str:
    return str(ctx["map"].get("row_id") or f"PR162E_Q_TO_PR167::{int(ctx['index']):05d}")


def _open_trade_route(ctx: dict[str, Any]) -> bool:
    return bool(ctx["map"].get("open_trade_sim_route_flag")) or bool(ctx["companions"]["PR166_QC_OpenTradeSimHandoff.report.json"].get("open_trade_sim_route_flag"))


def _selection_score(ctx: dict[str, Any]) -> float:
    row = ctx["map"]
    qc = ctx["companions"]["PR166_QC_To_PR167.report.json"]
    score = _float(row.get("expected_net_profit_per_order_candidate"), 0.0) * 10.0
    score += _float(row.get("fill_probability_score"), _float(qc.get("fill_probability_score"), 0.5)) * 0.8
    score += _float(row.get("queue_risk_adjusted_score"), _float(qc.get("queue_risk_adjusted_score"), 0.5)) * 0.4
    score += 3.0 if _open_trade_route(ctx) else 0.0
    score += 1.5 if bool(row.get("paper_champion_flag")) else 0.0
    score += 1.0 if bool(row.get("paper_challenger_flag")) else 0.0
    score += 0.7 if bool(row.get("paper_retest_flag")) else 0.0
    score += 0.6 if bool(row.get("still_negative_after_costs_flag")) else 0.0
    return score


def _failure_reason(
    *,
    actual: bool,
    still_negative: bool,
    expected_net: float,
    fill: float,
    partial_fill: float,
    latency_breach: bool,
    queue_survival: float,
    total_tca: float,
    capacity_score: float,
    adverse: float,
    stale_book_penalty: float,
    cancel_degradation: float,
    model_gap_component: float,
) -> str:
    if not actual:
        return ""
    if still_negative and expected_net <= 0:
        return "TCA_DRAG"
    if fill < 0.42:
        return "FILL_NO_FILL_RISK"
    if partial_fill > 0.68 and fill < 0.58:
        return "PARTIAL_FILL_INSUFFICIENT"
    if latency_breach:
        return "LATENCY_BREACH"
    if queue_survival < 0.38:
        return "QUEUE_SURVIVAL"
    if total_tca > 0.055:
        return "IMPLEMENTATION_SHORTFALL"
    if capacity_score < 0.34:
        return "CAPACITY_CROWDING"
    if adverse > 0.008:
        return "ADVERSE_SELECTION"
    if stale_book_penalty >= 0.006:
        return "STALE_BOOK"
    if cancel_degradation > 0.012:
        return "CANCEL_REPLACE_DEGRADATION"
    if model_gap_component > 0.008:
        return "MODEL_EXECUTION_GAP"
    if expected_net <= 0:
        return "TCA_DRAG"
    return ""


def _disposition_for_failure(reason: str) -> str:
    mapping = {
        "FILL_NO_FILL_RISK": "SIM_FAILED_FILL_NO_FILL",
        "PARTIAL_FILL_INSUFFICIENT": "SIM_FAILED_PARTIAL_FILL_INSUFFICIENT",
        "LATENCY_BREACH": "SIM_FAILED_LATENCY",
        "QUEUE_RISK": "SIM_FAILED_QUEUE_RISK",
        "QUEUE_SURVIVAL": "SIM_FAILED_QUEUE_SURVIVAL",
        "TCA_DRAG": "SIM_FAILED_TCA",
        "CAPACITY_CROWDING": "SIM_FAILED_CAPACITY_CROWDING",
        "ADVERSE_SELECTION": "SIM_FAILED_ADVERSE_SELECTION",
        "STALE_BOOK": "SIM_FAILED_STALE_BOOK",
        "CANCEL_REPLACE_DEGRADATION": "SIM_FAILED_CANCEL_REPLACE_DEGRADATION",
        "MODEL_EXECUTION_GAP": "SIM_FAILED_MODEL_EXECUTION_GAP",
        "IMPLEMENTATION_SHORTFALL": "SIM_FAILED_IMPLEMENTATION_SHORTFALL",
    }
    return mapping.get(reason, "SIM_REPAIR_PROPOSAL_CREATED")


def _secondary_failure_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if row["no_fill_risk_score"] > 0.35:
        reasons.append("NO_FILL_RISK")
    if row["partial_fill_probability_score"] > 0.45:
        reasons.append("PARTIAL_FILL_RISK")
    if row["latency_breach_flag"]:
        reasons.append("LATENCY_BREACH")
    if row["queue_survival_score"] < 0.55:
        reasons.append("QUEUE_SURVIVAL_RISK")
    if row["total_TCA_candidate"] > 0.035:
        reasons.append("TCA_DRAG")
    if row["stale_book_flag"]:
        reasons.append("STALE_BOOK")
    if row["model_execution_gap_component"] > 0.004:
        reasons.append("MODEL_EXECUTION_GAP")
    return reasons


def _survival_reason(row: dict[str, Any]) -> str:
    if row["simulator_survival_flag"]:
        return "SURVIVED_BOUNDED_NONLIVE_SIM_AFTER_FILL_TCA_LATENCY_QUEUE_CAPACITY_AND_COUNTERFACTUAL_CHECKS"
    if row["structural_only_flag"]:
        return row["structural_only_reason"]
    return f"NOT_SURVIVOR::{row['primary_failure_reason']}"


def _route_scores(fill: float, total_tca: float, latency_ms: int, adverse: float, queue_survival: float, expected_net: float) -> dict[str, float]:
    latency_penalty = latency_ms / 1000.0 * 0.006
    return {
        "classical_fallback_route_score": _round(_clamp(expected_net + fill * 0.08 - total_tca - latency_penalty, -1.0, 1.0)),
        "quantum_precompute_route_score": _round(_clamp(expected_net + fill * 0.09 - total_tca * 0.92 - latency_penalty + 0.008, -1.0, 1.0)),
        "hybrid_selects_classical_executes_route_score": _round(_clamp(expected_net + fill * 0.1 + queue_survival * 0.03 - total_tca * 0.9 - latency_penalty + 0.01, -1.0, 1.0)),
        "passive_limit_route_score": _round(_clamp(expected_net + queue_survival * 0.05 - total_tca * 0.7 - adverse * 0.5, -1.0, 1.0)),
        "near_touch_limit_route_score": _round(_clamp(expected_net + fill * 0.06 - total_tca * 0.9 - adverse, -1.0, 1.0)),
        "mid_route_score": _round(_clamp(expected_net + fill * 0.04 - total_tca * 0.82 - adverse * 0.7, -1.0, 1.0)),
        "aggressive_limit_route_score": _round(_clamp(expected_net + fill * 0.11 - total_tca * 1.2 - adverse * 1.4, -1.0, 1.0)),
        "no_trade_route_score": 0.0,
    }


def _lifecycle_trace(idx: int, actual: bool, survival: bool, failure_reason: str, structural_reason: str) -> list[dict[str, Any]]:
    states = [
        "CANDIDATE_SELECTED",
        "ORDER_INTENT_CREATED",
        "SHADOW_ORDER_CREATED",
        "BOOK_STATE_ATTACHED",
        "PRICE_SIDE_NORMALIZED",
        "SIZE_BUCKET_ASSIGNED",
        "AGGRESSION_ROUTE_SELECTED",
        "QUEUE_POSITION_ESTIMATED",
        "QUEUE_SURVIVAL_ESTIMATED",
        "FILL_PROBABILITY_ESTIMATED",
        "TCA_ESTIMATED",
        "IMPLEMENTATION_SHORTFALL_ESTIMATED",
        "LATENCY_ESTIMATED",
        "CAPACITY_CROWDING_CHECKED",
        "CANCEL_REPLACE_POLICY_EVALUATED",
        "COUNTERFACTUAL_ROUTE_COMPARED",
    ]
    if not actual:
        states.append("SIMULATED_PAPER_ONLY" if "RUNTIME_CAP" in structural_reason else "SIMULATED_NO_TRADE_NONLIVE")
    elif survival:
        states.append("SIMULATED_FILLED" if idx % 3 else "SIMULATED_PARTIAL_FILL")
    elif failure_reason in {"FILL_NO_FILL_RISK", "TCA_DRAG"}:
        states.append("SIMULATED_NO_FILL")
    elif failure_reason in {"LATENCY_BREACH", "STALE_BOOK", "CAPACITY_CROWDING"}:
        states.append("SIMULATED_REJECTED_BY_RISK")
    else:
        states.append("SIMULATED_CANCELLED")
    return [
        {
            "lifecycle_state": state,
            "transition_reason": failure_reason or structural_reason or "BOUNDED_NONLIVE_TRANSITION",
            "timestamp_order_index": order,
            "simulated_not_real_flag": True,
            "shadow_order_flag": True,
            "no_live_authority_flag": True,
            "downstream_route_ref": f"PR167_TO_PR166_QC_RETEST::{idx:05d}",
        }
        for order, state in enumerate(states, start=1)
    ]


def _depth_levels(price: float, side: str, idx: int) -> list[dict[str, Any]]:
    levels: list[dict[str, Any]] = []
    direction = -1 if side == "bid" else 1
    for level in range(1, 4):
        levels.append(
            {
                "level": level,
                "price": _round(_clamp(price + direction * level * 0.01, 0.01, 0.99)),
                "quantity": _round(20 + (idx % 7) * 4 + level * 5),
            }
        )
    return levels


def _liquidity_bucket(depth: float) -> str:
    if depth >= 150:
        return "HIGH_LIQUIDITY"
    if depth >= 90:
        return "MEDIUM_LIQUIDITY"
    return "THIN_LIQUIDITY"


def _quantum_recipe_ref(model_family: str, idx: int, row: dict[str, Any]) -> str:
    key_map = {
        "QUBO": "qubo_recipe_ref",
        "BQM": "bqm_recipe_ref",
        "Ising": "ising_recipe_ref",
        "CQM": "cqm_recipe_ref",
        "DQM": "dqm_recipe_ref",
        "QuadraticProgram": "quadratic_program_recipe_ref",
    }
    key = key_map.get(model_family, "hybrid_recipe_ref")
    return str(row.get(key) or row.get("hybrid_recipe_ref") or f"PR162E_Q_{model_family.upper()}_RECIPE::{idx:05d}")


def _route_explain_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "passive_limit_route_score": row["passive_limit_route_score"],
        "near_touch_limit_route_score": row["near_touch_limit_route_score"],
        "aggressive_limit_route_score": row["aggressive_limit_route_score"],
        "no_trade_route_score": row["no_trade_route_score"],
        "selected_route": row["selected_counterfactual_winner"],
        "route_selection_reason": row["counterfactual_reason"],
    }


def _repair_family(row: dict[str, Any]) -> str:
    reason = row["primary_failure_reason"]
    mapping = {
        "FILL_NO_FILL_RISK": "no-fill risk repair",
        "PARTIAL_FILL_INSUFFICIENT": "partial-fill repair",
        "LATENCY_BREACH": "latency reduction repair",
        "QUEUE_SURVIVAL": "queue-survival repair",
        "TCA_DRAG": "TCA reduction repair",
        "IMPLEMENTATION_SHORTFALL": "implementation-shortfall reduction repair",
        "CAPACITY_CROWDING": "capacity/crowding repair",
        "ADVERSE_SELECTION": "adverse-selection reduction repair",
        "STALE_BOOK": "stale-book repair",
        "CANCEL_REPLACE_DEGRADATION": "cancel/replace policy repair",
        "MODEL_EXECUTION_GAP": "classical fallback tightening repair",
    }
    if reason in mapping:
        return mapping[reason]
    if row["plugin_needed_flag"]:
        return "plugin support route repair"
    if row["owner_agent_intake_needed_flag"]:
        return "owner/agent formula intake route repair"
    return "replay/paper retest route repair"


def _dashboard_reason(row: dict[str, Any]) -> str:
    if row["simulator_champion_flag"] or row["simulator_challenger_flag"]:
        return "SIMULATOR_SURVIVOR_REQUIRES_OWNER_REVIEW_BEFORE_ANY_FUTURE_AUTHORITY"
    if row["simulator_failure_reason"]:
        return f"SIMULATOR_FAILURE_REVIEW::{row['simulator_failure_reason']}"
    if row["owner_agent_intake_needed_flag"]:
        return "OWNER_AGENT_INTAKE_REQUIRED_FOR_MISSING_ASSUMPTIONS"
    return "ROUTE_VISIBILITY_AND_NO_LIVE_AUTHORITY_CONFIRMATION"


def _handoff_reason(route: str, row: dict[str, Any]) -> str:
    if route == "PR166_QC_Retest":
        return "SIMULATOR_OUTPUT_REQUIRES_REPLAY_PAPER_RETEST_BEFORE_ANY_FUTURE_PROMOTION"
    if route == "PR162E":
        return "SIMULATOR_PLUGIN_INTERFACE_NEED_ROUTE_ONLY"
    if route == "PR162F":
        return "OWNER_AGENT_INTAKE_FOR_MISSING_SIMULATOR_OR_FORMULA_ASSUMPTION"
    if route == "OwnerDashboard":
        return "OWNER_DASHBOARD_REVIEW_READY_NO_UI_IMPLEMENTED"
    if route == "CloudSwitchboard":
        return "FUTURE_CLOUD_SWITCHBOARD_ROUTE_NO_BACKEND_EXECUTION"
    if route == "FutureConnectors":
        return "FUTURE_CONNECTOR_READINESS_ROUTE_NO_BINDING"
    return row["simulator_disposition"]


def _downstream_pr_for_route(route: str) -> str:
    mapping = {
        "PR166_QC_Retest": "PR166-QC-R2-OR-SUCCESSOR-REPLAY-PAPER-RETEST",
        "PR162E": "PR162E",
        "PR162F": "PR162F",
        "OwnerDashboard": "FUTURE_OWNER_DASHBOARD_REVIEW",
        "CloudSwitchboard": "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT_NO_EXECUTION",
        "FutureConnectors": "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
    }
    return mapping.get(route, "FUTURE_DOWNSTREAM_ROUTE")


def _source_pr_for_report(filename: str) -> str:
    if filename.startswith("PR166_QC_"):
        return "PR166-QC"
    if filename.startswith("PR162E_Q_"):
        return "PR162E-Q"
    if filename.startswith("PR165_D2_"):
        return "PR165-D2"
    return "UPSTREAM"


def _report_family(filename: str) -> str:
    return filename.removesuffix(".report.json").split("_", 2)[-1]


def _fields_used_for_report(source: SourceData, filename: str) -> list[str]:
    rows = source.records.get(filename) or []
    if not rows:
        return []
    preferred = [
        "row_id",
        "qku_id",
        "formula_id",
        "algorithm_id",
        "expected_net_profit_per_order_candidate",
        "fill_probability_score",
        "total_tca_estimate",
        "open_trade_sim_route_flag",
        "deterministic_sort_key",
    ]
    keys = set(rows[0])
    return [key for key in preferred if key in keys] or sorted(keys)[:12]


def _family_from_id(value: object, fallback: str) -> str:
    text = str(value or "")
    if "::" in text:
        return text.split("::", 1)[0]
    if "-" in text:
        return text.split("-", 1)[0]
    return fallback


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _chunks(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)] or [[]]


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR167_*.report.json"):
        path.unlink()
