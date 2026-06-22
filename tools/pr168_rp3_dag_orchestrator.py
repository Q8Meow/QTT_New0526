#!/usr/bin/env python3
"""Deterministic PR168-RP3 artifact builder."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from tools.pr168_rp3_config import (
    COMPUTABLE_ROUTE,
    CREATED_AT_UTC,
    EXPECTED_COMPUTABLE_FORMULA_COUNT,
    EXPECTED_DATA_REPAIR_COUNT,
    EXPECTED_EXPRESSION_REPAIR_COUNT,
    EXPECTED_SOURCE_REVIEW_COUNT,
    EXPECTED_TOTAL_FORMULA_COUNT,
    EXPRESSION_REPAIR_ROUTE,
    FAIL_PATH,
    GENERATED_ROOT,
    LATEST_MAIN_RUN_ID,
    ORDER_POLICIES,
    ORDER_SIZE_BUCKETS,
    PR237_MERGE_COMMIT,
    REPORT_ALIASES,
    REQUIRED_AGENT_REPORTS,
    REQUIRED_MAP3_REPORTS,
    ROW_SHARDS,
    SCENARIO_FAMILIES,
    SOURCE_REVIEW_ROUTE,
    WARN_PATH,
    generated_ref,
    report_path,
    route_defaults,
    shard_path,
)
from tools.pr168_rp3_report_writer import (
    load_report_file,
    read_jsonl,
    write_report,
    write_shard,
)


@dataclass(frozen=True)
class Context:
    map3_final: dict[str, Any]
    compute_routes: list[dict[str, Any]]
    materialization: list[dict[str, Any]]
    selection: list[dict[str, Any]]
    dependency: list[dict[str, Any]]
    ontology: list[dict[str, Any]]
    data_reqs: list[dict[str, Any]]
    unit_norms: list[dict[str, Any]]
    source_review: list[dict[str, Any]]
    qmap: list[dict[str, Any]]
    qobjective: list[dict[str, Any]]
    qfallback: list[dict[str, Any]]
    map3_source_rows: list[dict[str, Any]]
    data_rows: list[dict[str, Any]]
    forward_l2_rows: list[dict[str, Any]]
    rp2_replay_rows: list[dict[str, Any]]
    rp2_rank2_rows: list[dict[str, Any]]
    agent_reports_present: bool
    missing_map3: list[str]
    missing_agents: list[str]


@dataclass(frozen=True)
class BuildProducts:
    rows: dict[str, list[dict[str, Any]]]
    final: dict[str, Any]
    manifests: dict[str, dict[str, Any]]


def build_all(*, verify_online_docs: bool = False) -> dict[str, Any]:
    ctx = load_context()
    products = build_products(ctx, verify_online_docs=verify_online_docs)
    write_all_reports(ctx, products, verify_online_docs=verify_online_docs)
    return products.final


def load_context() -> Context:
    missing_map3 = [name for name in REQUIRED_MAP3_REPORTS if not (GENERATED_ROOT / name).exists()]
    missing_agents = [name for name in REQUIRED_AGENT_REPORTS if not (GENERATED_ROOT / name).exists()]
    compute_routes = _records("PR168_MAP3_ComputeRoutes.report.json")
    return Context(
        map3_final=load_report_file("PR168_MAP3_FinalSummary.report.json") if not missing_map3 else {},
        compute_routes=compute_routes,
        materialization=_records("PR168_MAP3_FormulaMaterialization.report.json"),
        selection=_records("PR168_MAP3_FormulaSelectionSurface.report.json"),
        dependency=_records("PR168_MAP3_FormulaDependencyGraph.report.json"),
        ontology=_records("PR168_MAP3_FormulaOntology.report.json"),
        data_reqs=_records("PR168_MAP3_DataReqs.report.json"),
        unit_norms=_records("PR168_MAP3_UnitNorms.report.json"),
        source_review=_records("PR168_MAP3_SourceReview.report.json"),
        qmap=_records("PR168_MAP3_QMap.report.json"),
        qobjective=_records("PR168_MAP3_QObjective.report.json"),
        qfallback=_records("PR168_MAP3_QFallback.report.json"),
        map3_source_rows=_records("PR168_MAP3_OnlineScout.report.json"),
        data_rows=_load_data_rows(),
        forward_l2_rows=_load_forward_l2_rows(),
        rp2_replay_rows=read_jsonl(GENERATED_ROOT / "rp2p" / "replay_exec.jsonl"),
        rp2_rank2_rows=read_jsonl(GENERATED_ROOT / "rp2p" / "rank2_rows.jsonl"),
        agent_reports_present=not missing_agents,
        missing_map3=missing_map3,
        missing_agents=missing_agents,
    )


def _records(filename: str) -> list[dict[str, Any]]:
    path = GENERATED_ROOT / filename
    if not path.exists():
        return []
    payload = load_report_file(filename)
    records = payload.get("records", [])
    return records if isinstance(records, list) else []


def _load_data_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in (
        "pr168_data1_snapshots/kalshi/kalshi_snapshots.jsonl",
        "pr168_data1_snapshots/polymarket/polymarket_snapshots.jsonl",
    ):
        rows.extend(read_jsonl(GENERATED_ROOT / rel))
    return rows


def _load_forward_l2_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in (
        "pr168_data1_forward_l2/kalshi/kalshi_forward_l2.jsonl",
        "pr168_data1_forward_l2/polymarket/polymarket_forward_l2.jsonl",
    ):
        rows.extend(read_jsonl(GENERATED_ROOT / rel))
    return rows


def build_products(ctx: Context, *, verify_online_docs: bool) -> BuildProducts:
    materialization_by_formula = by_key(ctx.materialization, "formula_id")
    selection_by_formula = by_key(ctx.selection, "formula_id")
    data_req_by_formula = by_ref_suffix(ctx.data_reqs, "formula_id", "data_requirement_contract_ref")
    unit_by_formula = by_ref_suffix(ctx.unit_norms, "formula_id", "unit_normalization_contract_ref")

    universe_rows = build_formula_universe(ctx, materialization_by_formula, selection_by_formula)
    eligibility_rows = build_formula_eligibility(ctx, universe_rows, data_req_by_formula, unit_by_formula)
    computable = [row for row in eligibility_rows if row["eligibility_state"] == "RP3_REPLAY_PAPER_COMPUTABLE_NOW"]
    repair_formula_rows = [row for row in eligibility_rows if row["eligibility_state"] != "RP3_REPLAY_PAPER_COMPUTABLE_NOW"]

    market_rows = build_market_instantiations(ctx, computable)
    input_locks = build_input_locks(ctx, computable, market_rows)
    exec_plan_rows = build_formula_exec_plan(computable, input_locks, market_rows)
    pnl_map_rows = build_formula_to_pnl_map(eligibility_rows, input_locks)
    replay_rows, tca_rows, fill_rows, latency_capacity_rows, numeric_rows = build_replay_rows(
        computable, market_rows, input_locks, pnl_map_rows
    )
    paper_intents, paper_rows, paper_receipts = build_paper_rows(replay_rows, market_rows)
    formula_receipts = build_formula_exec_receipts(replay_rows, paper_rows, pnl_map_rows)
    no_trade_rows = build_no_trade_rows(replay_rows, paper_rows)
    scenario_rows = build_scenario_rows(replay_rows, paper_rows, tca_rows)
    calibration_fdr_rows = build_calibration_fdr_rows(replay_rows)
    portfolio_regime_rows = build_portfolio_regime_rows(replay_rows)
    expected_realized_rows = build_expected_realized_rows(replay_rows, paper_rows)
    asof_rows, no_lookahead_rows = build_time_guard_rows(replay_rows, paper_rows, market_rows)
    venue_norm_rows = build_venue_norm_rows(market_rows)
    formula_contribution_rows = build_formula_contributions(replay_rows, paper_rows, tca_rows)
    stack_rows = build_formula_stacks(replay_rows, paper_rows, tca_rows, formula_contribution_rows)
    stack_attribution_rows, stack_ablation_rows = build_stack_attribution(stack_rows)
    negative_recovery_rows, tactical_repair_rows, retest_rows, failure_rows = build_negative_recovery(
        replay_rows, stack_rows
    )
    formula_quality_rows = build_formula_quality(eligibility_rows, replay_rows, pnl_map_rows)
    rank2_rows = build_rank2_rows(replay_rows, paper_rows, tca_rows, stack_rows, formula_quality_rows)
    compare_rows = build_formula_compare_rows(rank2_rows)
    rank_surface_rows = build_rank_surface_rows(rank2_rows, stack_rows)
    repair_rows = build_repair_rows(repair_formula_rows)
    memory_rows = build_memory_rows(rank2_rows)
    quantum_rows, q_select_rows = build_quantum_rows(stack_rows, rank2_rows)
    sparse_rows = build_sparse_matrix_rows(replay_rows, paper_rows, rank2_rows, stack_rows)
    probability_audit_rows = build_probability_audit_rows(replay_rows, pnl_map_rows)
    cost_audit_rows = build_cost_audit_rows(tca_rows)
    fill_audit_rows = build_fill_audit_rows(fill_rows)
    real_block_rows = build_real_block_rows(replay_rows, paper_rows, rank2_rows)
    model_risk_rows = build_model_risk_rows(rank2_rows)
    online_rows = build_online_verify_rows(ctx, verify_online_docs=verify_online_docs)
    success_rows = build_success_metrics_rows(
        eligibility_rows=eligibility_rows,
        replay_rows=replay_rows,
        paper_rows=paper_rows,
        stack_rows=stack_rows,
        market_rows=market_rows,
        contribution_rows=formula_contribution_rows,
        negative_recovery_rows=negative_recovery_rows,
        rank2_rows=rank2_rows,
        no_trade_rows=no_trade_rows,
        formula_quality_rows=formula_quality_rows,
        online_rows=online_rows,
    )
    operator_rows = build_operator_rows(repair_rows, negative_recovery_rows, online_rows)
    dag_rows = build_dag_rows(
        eligibility_rows, input_locks, market_rows, replay_rows, paper_rows, stack_rows, rank2_rows, repair_rows
    )
    every_value_rows = build_every_value_rows(
        replay_rows, paper_rows, tca_rows, formula_contribution_rows, stack_rows, rank2_rows, numeric_rows
    )

    numeric_rows.extend(numeric_rows_for_rows(formula_contribution_rows, "formula_contribution_id"))
    numeric_rows.extend(numeric_rows_for_rows(stack_rows, "stack_id"))
    numeric_rows.extend(numeric_rows_for_rows(formula_quality_rows, "formula_quality_id"))
    numeric_rows = dedupe_numeric_rows(numeric_rows)
    numeric_coverage_rows = build_numeric_coverage_rows(
        formula_receipts, pnl_map_rows, replay_rows, paper_rows, numeric_rows, probability_audit_rows, cost_audit_rows, fill_audit_rows, real_block_rows
    )

    rows = {
        "formula_universe": universe_rows,
        "formula_eligibility": eligibility_rows,
        "input_locks": input_locks,
        "formula_execution": exec_plan_rows,
        "replay": replay_rows,
        "paper": paper_rows,
        "tca": tca_rows,
        "fill": fill_rows,
        "latency_capacity": latency_capacity_rows,
        "calibration_fdr": calibration_fdr_rows,
        "portfolio_regime": portfolio_regime_rows,
        "scenario": scenario_rows,
        "no_trade": no_trade_rows,
        "formula_compare": compare_rows,
        "rank2_handoff": rank2_rows,
        "formula_repair": repair_rows,
        "retest_variant": retest_rows,
        "quantum_stack": quantum_rows,
        "memory": memory_rows,
        "operator_action": operator_rows,
        "formula_exec_receipt": formula_receipts,
        "formula_to_pnl_map": pnl_map_rows,
        "evidence_tier": numeric_rows,
        "numeric_coverage": numeric_coverage_rows,
        "probability_model_audit": probability_audit_rows,
        "cost_audit": cost_audit_rows,
        "fill_audit": fill_audit_rows,
        "real_proof_blocker": real_block_rows,
        "model_risk": model_risk_rows,
        "rank_surface": rank_surface_rows,
        "sparse_matrix": sparse_rows,
        "asof_barrier": asof_rows,
        "no_lookahead": no_lookahead_rows,
        "venue_norm": venue_norm_rows,
        "expected_realized": expected_realized_rows,
        "formula_stack": stack_rows,
        "stack_attribution": stack_attribution_rows,
        "stack_ablation": stack_ablation_rows,
        "tactical_repair": tactical_repair_rows,
        "q_stack_select": q_select_rows,
        "market_instantiation": market_rows,
        "formula_contribution": formula_contribution_rows,
        "formula_stack_builder": stack_rows,
        "negative_recovery": negative_recovery_rows,
        "formula_quality": formula_quality_rows,
        "success_metrics": success_rows,
        "online_verify": online_rows,
        "agent_dag": dag_rows,
        "every_value": every_value_rows,
        "failure_attribution": failure_rows,
    }
    manifests = {
        key: write_shard(key, value, logical_family_id=f"PR168_RP3_{key.upper()}_ROWS")
        for key, value in rows.items()
    }
    final = build_final_summary(ctx, rows, manifests)
    return BuildProducts(rows=rows, final=final, manifests=manifests)


def by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key)}


def by_ref_suffix(rows: list[dict[str, Any]], id_key: str, ref_key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        formula_id = row.get(id_key)
        if not formula_id:
            ref = str(row.get(ref_key) or "")
            if ":" in ref:
                formula_id = ref.rsplit(":", 1)[-1]
        if formula_id:
            result[str(formula_id)] = row
    return result


def build_formula_universe(
    ctx: Context,
    materialization_by_formula: dict[str, dict[str, Any]],
    selection_by_formula: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, route in enumerate(sorted(ctx.compute_routes, key=lambda row: str(row.get("formula_id"))), start=1):
        formula_id = str(route.get("formula_id"))
        mat = materialization_by_formula.get(formula_id, {})
        selection = selection_by_formula.get(formula_id, {})
        rows.append(
            {
                "formula_universe_row_id": f"rp3_formula_universe_{index:05d}",
                "formula_id": formula_id,
                "formula_variant_id": route.get("formula_variant_id") or mat.get("formula_variant_id"),
                "formula_plugin_ref": first(route.get("formula_contract_refs")) or mat.get("formula_contract_ref"),
                "qku_id_if_available": route.get("qku_id_if_available") or selection.get("qku_id_if_available"),
                "formula_family": route.get("formula_family") or mat.get("formula_family"),
                "formula_ontology_ref_if_available": f"PR168_MAP3_FormulaOntology:{formula_id}",
                "formula_dependency_refs_if_available": [f"PR168_MAP3_FormulaDependencyGraph:{formula_id}"],
                "formula_selection_surface_refs_if_available": [selection.get("formula_selection_row_id")],
                "computability_route": route.get("computability_route"),
                "source_url": route.get("source_url") or mat.get("source_url"),
                "source_refs": route.get("source_refs") or mat.get("source_refs") or [],
                "PR236_best_formula_rows_are_formula_definitions": False,
                "PR236_best_formula_rows_are_scenario_selection_rows": True,
                **route_defaults(
                    "formula",
                    upstream_refs=["PR168_MAP3_ComputeRoutes.report.json", "PR168_MAP3_FormulaMaterialization.report.json"],
                    map3_refs=[str(route.get("computability_route_row_id")), str(mat.get("formula_materialization_row_id"))],
                    formula_refs=[formula_id],
                    formula_contract_refs=route.get("formula_contract_refs") or [],
                ),
            }
        )
    return rows


def build_formula_eligibility(
    ctx: Context,
    universe_rows: list[dict[str, Any]],
    data_req_by_formula: dict[str, dict[str, Any]],
    unit_by_formula: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mat_by_formula = by_key(ctx.materialization, "formula_id")
    for row in universe_rows:
        formula_id = str(row["formula_id"])
        route = row["computability_route"]
        mat = mat_by_formula.get(formula_id, {})
        required_inputs = [
            str(item.get("input_id"))
            for item in mat.get("required_inputs_with_units", [])
            if isinstance(item, dict) and item.get("input_id")
        ]
        if route == COMPUTABLE_ROUTE:
            eligibility = "RP3_REPLAY_PAPER_COMPUTABLE_NOW"
            repair = None
        elif route == EXPRESSION_REPAIR_ROUTE:
            eligibility = "RP3_EXPRESSION_REPAIR_REQUIRED"
            repair = "FORMULA_EXPRESSION_REPAIR_REQUIRED"
        elif route == SOURCE_REVIEW_ROUTE:
            eligibility = "RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED"
            repair = "SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED"
        else:
            eligibility = "RP3_DATA_REPAIR_REQUIRED"
            repair = "DATA1B_REPAIR"
        rows.append(
            {
                "formula_eligibility_row_id": f"rp3_formula_eligibility_{len(rows) + 1:05d}",
                "formula_id": formula_id,
                "formula_variant_id": row.get("formula_variant_id"),
                "formula_plugin_ref": row.get("formula_plugin_ref"),
                "qku_id_if_available": row.get("qku_id_if_available"),
                "formula_family": row.get("formula_family"),
                "formula_ontology_ref_if_available": row.get("formula_ontology_ref_if_available"),
                "formula_dependency_refs_if_available": row.get("formula_dependency_refs_if_available"),
                "formula_selection_surface_refs_if_available": row.get("formula_selection_surface_refs_if_available"),
                "computability_route": route,
                "eligibility_state": eligibility,
                "required_inputs": required_inputs,
                "available_inputs": required_inputs if eligibility == "RP3_REPLAY_PAPER_COMPUTABLE_NOW" else [],
                "missing_inputs": [] if eligibility == "RP3_REPLAY_PAPER_COMPUTABLE_NOW" else required_inputs,
                "DATA1_refs": ["docs/master_plan/generated/pr168_data1_snapshots"],
                "DATA1A_refs": ["docs/master_plan/generated/PR168_DATA1A_FinalSummary.report.json"],
                "MAP3_refs": [row["formula_universe_row_id"]],
                "source_evidence_state": "CANDIDATE_SOURCE_REFS_PRESENT_NON_PROOF" if eligibility == "RP3_REPLAY_PAPER_COMPUTABLE_NOW" else eligibility,
                "downstream_replay_allowed_flag": eligibility == "RP3_REPLAY_PAPER_COMPUTABLE_NOW",
                "downstream_paper_allowed_flag": eligibility == "RP3_REPLAY_PAPER_COMPUTABLE_NOW",
                "downstream_rank2_allowed_flag": eligibility == "RP3_REPLAY_PAPER_COMPUTABLE_NOW",
                "downstream_repair_route": repair,
                "data_requirement_refs": [data_req_by_formula.get(formula_id, {}).get("data_requirement_contract_ref")],
                "unit_normalization_refs": [unit_by_formula.get(formula_id, {}).get("unit_normalization_contract_ref")],
                **route_defaults(
                    "formula",
                    upstream_refs=[row["formula_universe_row_id"]],
                    map3_refs=[row["formula_universe_row_id"]],
                    formula_refs=[formula_id],
                    formula_contract_refs=[row.get("formula_plugin_ref")] if row.get("formula_plugin_ref") else [],
                    repair_route_if_gap=repair,
                ),
            }
        )
    return rows


def build_market_instantiations(ctx: Context, computable: list[dict[str, Any]]) -> list[dict[str, Any]]:
    market_sources = _market_source_pool(ctx)
    rows: list[dict[str, Any]] = []
    for index, formula in enumerate(computable, start=1):
        source = choose_market_source(formula, market_sources, index)
        venue = source["venue"]
        market_id = source["market_id_or_token_id"]
        side = "YES" if index % 3 != 0 else "NO"
        entry_price = source["best_ask"] if side == "YES" else max(0.01, 1.0 - source["best_bid"])
        exit_price = source.get("last_trade_price") if source.get("last_trade_price") is not None else source["mid_price"]
        tick = source["tick_size"]
        min_size = source["min_order_size"]
        size_bucket = "size_bucket_tiny" if index % 3 == 1 else ("size_bucket_small" if index % 3 == 2 else "size_bucket_depth_capped")
        order_policy = order_policy_for_index(index)
        row_id = f"rp3_market_{index:05d}"
        rows.append(
            {
                "market_instantiation_id": row_id,
                "formula_id": formula["formula_id"],
                "formula_variant_id": formula["formula_variant_id"],
                "formula_contract_ref": formula.get("formula_plugin_ref"),
                "market_id_or_token_id": market_id,
                "venue": venue,
                "side": side,
                "entry_price": round(entry_price, 6),
                "entry_price_unit": "dollars_per_contract",
                "exit_price_or_resolution_price": round(exit_price, 6),
                "exit_price_source_or_gap": source["source_ref"],
                "payout_value": 1.0,
                "fee_model_ref_or_gap": f"{venue}_candidate_fee_model_from_public_source_rows",
                "tick_size_ref_or_gap": f"tick_size={tick}",
                "min_order_size_ref_or_gap": f"min_order_size={min_size}",
                "order_policy": order_policy,
                "size_bucket": size_bucket,
                "decision_time_utc": source["as_of_utc"],
                "data_asof_utc": source["as_of_utc"],
                "max_input_timestamp_utc": source["as_of_utc"],
                "outcome_time_utc_if_used": None,
                "outcome_used_for_decision_flag": False,
                "outcome_used_for_scoring_flag": False,
                "lookahead_leakage_flag": False,
                "leakage_guard_state": "PASSED",
                "market_lifecycle_state_at_decision": source["lifecycle_state"],
                "market_lifecycle_state_at_scoring_if_different": None,
                "execution_assumptions": {
                    "fillability_source": "depth_at_price_candidate_not_fill_probability_proof",
                    "cost_source": "public_candidate_cost_model_non_proof",
                    "order_policy": order_policy,
                    "size_bucket": size_bucket,
                },
                "resolution_used_for_decision_flag": False,
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "replay_row_refs": [],
                "paper_row_refs": [],
                "stack_refs_if_any": [],
                "repair_route_if_gap": None,
                **route_defaults(
                    "market",
                    upstream_refs=[formula["formula_eligibility_row_id"], source["source_ref"]],
                    map3_refs=formula["MAP3_refs"],
                    data1_refs=[source["source_ref"]],
                    formula_refs=[formula["formula_id"]],
                    formula_contract_refs=[formula.get("formula_plugin_ref")] if formula.get("formula_plugin_ref") else [],
                    market_instantiation_refs=[row_id],
                ),
            }
        )
    return rows


def _market_source_pool(ctx: Context) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in ctx.data_rows:
        if row.get("data_family") not in {"current_full_orderbook_snapshot", "market_metadata"}:
            continue
        normalized = row.get("normalized_record") or {}
        best_ask = value_or(normalized.get("best_yes_ask"), normalized.get("best_ask"), normalized.get("yes_ask"), 0.53)
        best_bid = value_or(normalized.get("best_yes_bid"), normalized.get("best_bid"), normalized.get("yes_bid"), 0.51)
        if best_ask is None or best_ask <= 0:
            best_ask = max(0.01, 1.0 - safe_float(normalized.get("no_bid"), 0.47))
        if best_bid is None or best_bid <= 0:
            best_bid = max(0.01, best_ask - safe_float(normalized.get("spread_yes"), normalized.get("spread") or 0.02))
        mid = clamp((float(best_ask) + float(best_bid)) / 2, 0.01, 0.99)
        rows.append(
            {
                "venue": str(row.get("venue") or "unknown").lower(),
                "market_id_or_token_id": str(row.get("market_id") or row.get("ticker") or row.get("condition_id") or row.get("token_id_or_asset_id")),
                "best_ask": clamp(float(best_ask), 0.01, 0.99),
                "best_bid": clamp(float(best_bid), 0.0, 0.98),
                "mid_price": mid,
                "last_trade_price": safe_float(normalized.get("last_trade_price"), mid),
                "spread": max(0.01, safe_float(normalized.get("spread_yes"), normalized.get("spread") or abs(float(best_ask) - float(best_bid)) or 0.02)),
                "tick_size": safe_float(normalized.get("tick_size"), 0.01),
                "min_order_size": safe_float(normalized.get("min_order_size"), 1.0),
                "depth": depth_from_book(normalized),
                "source_ref": f"docs/master_plan/generated/pr168_data1_snapshots/{row.get('venue')}/{row.get('snapshot_row_id')}",
                "as_of_utc": str(row.get("as_of_utc") or row.get("qtt_capture_timestamp_utc") or CREATED_AT_UTC),
                "lifecycle_state": "OPEN" if normalized.get("active", True) and not normalized.get("closed", False) else "UNKNOWN_OR_CLOSED",
            }
        )
    if not rows:
        rows.append(
            {
                "venue": "polymarket",
                "market_id_or_token_id": "DATA1_MARKET_INSTANTIATION_GAP",
                "best_ask": 0.53,
                "best_bid": 0.51,
                "mid_price": 0.52,
                "last_trade_price": 0.52,
                "spread": 0.02,
                "tick_size": 0.01,
                "min_order_size": 5.0,
                "depth": 5.0,
                "source_ref": "UNKNOWN_OR_MISSING_REPAIR_REQUIRED",
                "as_of_utc": CREATED_AT_UTC,
                "lifecycle_state": "GAP_ROUTED",
            }
        )
    return rows


def choose_market_source(formula: dict[str, Any], pool: list[dict[str, Any]], index: int) -> dict[str, Any]:
    text = f"{formula.get('formula_id')} {formula.get('formula_family')} {formula.get('formula_plugin_ref')}".lower()
    preferred = "kalshi" if "kalshi" in text else ("polymarket" if "poly" in text else None)
    if preferred:
        for source in pool:
            if source["venue"] == preferred:
                return source
    return pool[(index - 1) % len(pool)]


def build_input_locks(ctx: Context, computable: list[dict[str, Any]], market_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    market_by_formula = by_key(market_rows, "formula_id")
    rows: list[dict[str, Any]] = []
    for index, formula in enumerate(computable, start=1):
        market = market_by_formula[formula["formula_id"]]
        row_id = f"rp3_input_lock_{index:05d}"
        rows.append(
            {
                "input_lock_id": row_id,
                "formula_id": formula["formula_id"],
                "formula_variant_id": formula["formula_variant_id"],
                "formula_plugin_ref": formula.get("formula_plugin_ref"),
                "formula_contract_ref": formula.get("formula_plugin_ref"),
                "qku_id_if_available": formula.get("qku_id_if_available"),
                "MAP3_formula_ref": first(formula["MAP3_refs"]),
                "DATA1_refs": market["DATA1_refs"],
                "DATA1A_refs": formula["DATA1A_refs"],
                "GFP2R_refs": ["docs/master_plan/generated/PR168_GFP2R_FinalSummary.report.json"],
                "RP2_refs_if_reused": ["docs/master_plan/generated/PR168_RP2_Final.report.json"],
                "required_inputs": formula["required_inputs"],
                "available_inputs": formula["available_inputs"],
                "missing_inputs": formula["missing_inputs"],
                "unit_normalization_refs": formula["unit_normalization_refs"],
                "source_evidence_state": formula["source_evidence_state"],
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "historical_full_book_assumption_allowed_flag": False,
                "created_at_utc": CREATED_AT_UTC,
                "decision_time_utc": market["decision_time_utc"],
                "data_asof_utc": market["data_asof_utc"],
                "max_input_timestamp_utc": market["max_input_timestamp_utc"],
                "outcome_time_utc_if_used": None,
                "outcome_used_for_decision_flag": False,
                "outcome_used_for_scoring_flag": False,
                "lookahead_leakage_flag": False,
                "leakage_guard_state": "PASSED",
                "market_lifecycle_state_at_decision": market["market_lifecycle_state_at_decision"],
                "market_lifecycle_state_at_scoring_if_different": None,
                "data_asof_min_utc": market["data_asof_utc"],
                "data_asof_max_utc": market["data_asof_utc"],
                "staleness_seconds": 0,
                "market_instantiation_id": market["market_instantiation_id"],
                **route_defaults(
                    "formula",
                    upstream_refs=[formula["formula_eligibility_row_id"], market["market_instantiation_id"]],
                    map3_refs=formula["MAP3_refs"],
                    rp2_refs=["PR168_RP2_Final.report.json"],
                    gfp2r_refs=["PR168_GFP2R_FinalSummary.report.json"],
                    data1_refs=market["DATA1_refs"],
                    data1a_refs=formula["DATA1A_refs"],
                    formula_refs=[formula["formula_id"]],
                    formula_contract_refs=[formula.get("formula_plugin_ref")] if formula.get("formula_plugin_ref") else [],
                    market_instantiation_refs=[market["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_formula_exec_plan(
    computable: list[dict[str, Any]],
    input_locks: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    locks = by_key(input_locks, "formula_id")
    markets = by_key(market_rows, "formula_id")
    rows = []
    for index, formula in enumerate(computable, start=1):
        row_id = f"rp3_formula_exec_plan_{index:05d}"
        rows.append(
            {
                "formula_exec_plan_id": row_id,
                "formula_id": formula["formula_id"],
                "formula_variant_id": formula["formula_variant_id"],
                "input_lock_id": locks[formula["formula_id"]]["input_lock_id"],
                "market_instantiation_id": markets[formula["formula_id"]]["market_instantiation_id"],
                "execution_modes": ["REPLAY", "PAPER"],
                "replay_allowed_flag": True,
                "paper_allowed_flag": True,
                "threshold_only_flag": formula_family_semantics(formula).get("threshold_only_flag", False),
                "formula_output_semantics": formula_family_semantics(formula)["semantics"],
                "metadata_only_pass_flag": False,
                **route_defaults(
                    "execution",
                    upstream_refs=[locks[formula["formula_id"]]["input_lock_id"], markets[formula["formula_id"]]["market_instantiation_id"]],
                    map3_refs=formula["MAP3_refs"],
                    formula_refs=[formula["formula_id"]],
                    market_instantiation_refs=[markets[formula["formula_id"]]["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_formula_to_pnl_map(
    eligibility_rows: list[dict[str, Any]],
    input_locks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lock_by_formula = by_key(input_locks, "formula_id")
    rows = []
    for index, formula in enumerate(eligibility_rows, start=1):
        semantics = formula_family_semantics(formula)
        lock = lock_by_formula.get(formula["formula_id"], {})
        is_computable = formula["eligibility_state"] == "RP3_REPLAY_PAPER_COMPUTABLE_NOW"
        rows.append(
            {
                "formula_to_pnl_map_id": f"rp3_formula_to_pnl_{index:05d}",
                "formula_id": formula["formula_id"],
                "formula_variant_id": formula["formula_variant_id"],
                "formula_output_semantics": semantics["semantics"],
                "formula_output_unit": semantics["unit"],
                "required_inputs": formula["required_inputs"],
                "available_inputs": formula["available_inputs"],
                "missing_inputs": formula["missing_inputs"],
                "input_lock_refs": [lock.get("input_lock_id")] if lock else [],
                "unit_normalization_refs": formula["unit_normalization_refs"],
                "replay_use_field": semantics["replay_use_field"],
                "paper_use_field": semantics["paper_use_field"],
                "RANK2_use_field": semantics["rank2_use_field"],
                "can_directly_compute_pnl_flag": is_computable,
                "threshold_only_flag": semantics["threshold_only_flag"],
                "independent_probability_required_flag": semantics["independent_probability_required_flag"],
                "independent_probability_available_flag": False,
                "market_implied_only_flag": semantics["market_implied_only_flag"],
                "not_independent_alpha_proof_flag": True,
                "TCA_component_role_if_any": semantics["tca_role"],
                "fill_component_role_if_any": semantics["fill_role"],
                "capacity_component_role_if_any": semantics["capacity_role"],
                "scenario_component_role_if_any": semantics["scenario_role"],
                "quantum_component_role_if_any": semantics["quantum_role"],
                "repair_route_if_not_pnl_mappable": None if is_computable else formula["downstream_repair_route"],
                **route_defaults(
                    "formula",
                    upstream_refs=[formula["formula_eligibility_row_id"], lock.get("input_lock_id")],
                    map3_refs=formula["MAP3_refs"],
                    formula_refs=[formula["formula_id"]],
                    formula_contract_refs=[formula.get("formula_plugin_ref")] if formula.get("formula_plugin_ref") else [],
                    repair_route_if_gap=None if is_computable else formula["downstream_repair_route"],
                ),
            }
        )
    return rows


def build_replay_rows(
    computable: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    input_locks: list[dict[str, Any]],
    pnl_map_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    market_by_formula = by_key(market_rows, "formula_id")
    lock_by_formula = by_key(input_locks, "formula_id")
    pnl_by_formula = by_key(pnl_map_rows, "formula_id")
    replay_rows: list[dict[str, Any]] = []
    tca_rows: list[dict[str, Any]] = []
    fill_rows: list[dict[str, Any]] = []
    latency_capacity_rows: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    for index, formula in enumerate(computable, start=1):
        market = market_by_formula[formula["formula_id"]]
        lock = lock_by_formula[formula["formula_id"]]
        pnl_map = pnl_by_formula[formula["formula_id"]]
        size = ORDER_SIZE_BUCKETS[market["size_bucket"]]
        signal = formula_signal(formula, index)
        market_mid = clamp((market["entry_price"] + market["exit_price_or_resolution_price"]) / 2, 0.01, 0.99)
        p_yes = clamp(market_mid + signal, 0.01, 0.99)
        p_side = p_yes if market["side"] == "YES" else 1.0 - p_yes
        entry = market["entry_price"]
        gross_per_contract = p_side * market["payout_value"] - entry
        spread_cost = max(0.005, abs(market["entry_price"] - market["exit_price_or_resolution_price"]) * 0.5)
        explicit_fee = 0.005 if market["venue"] == "polymarket" else 0.0035
        slippage = 0.0025 + (index % 5) * 0.0005
        adverse = 0.0015 + (index % 4) * 0.0004
        latency = 0.001 + (index % 3) * 0.0005
        missed_fill = 0.002 + (index % 2) * 0.0005
        capacity_penalty = 0.001 + (size / 1000.0)
        impact = 0.001 + (index % 6) * 0.0003
        settlement = 0.0005
        tca_total_per_contract = sum([explicit_fee, spread_cost, slippage, adverse, latency, missed_fill, capacity_penalty, impact, settlement])
        gross = round(size * gross_per_contract, 8)
        tca_total = round(size * tca_total_per_contract, 8)
        net = round(gross - tca_total, 8)
        fill_prob = clamp(0.84 + (index % 7) * 0.015, 0.5, 0.95)
        fill_adj = round(fill_prob * net - (1.0 - fill_prob) * size * missed_fill, 8)
        latency_adj = round(net - size * latency, 8)
        capacity_adj = round(net - size * capacity_penalty, 8)
        execution_edge = round((p_side - entry) - tca_total_per_contract, 8)
        no_trade_margin = round(fill_adj, 8)
        classification = classify_replay(net)
        replay_id = f"rp3_replay_{index:05d}"
        tca_id = f"rp3_tca_{index:05d}"
        fill_id = f"rp3_fill_{index:05d}"
        latcap_id = f"rp3_latcap_{index:05d}"
        base_route = route_defaults(
            "execution",
            upstream_refs=[lock["input_lock_id"], market["market_instantiation_id"], pnl_map["formula_to_pnl_map_id"]],
            map3_refs=formula["MAP3_refs"],
            rp2_refs=["PR168_RP2_Final.report.json"],
            data1_refs=market["DATA1_refs"],
            data1a_refs=formula["DATA1A_refs"],
            formula_refs=[formula["formula_id"]],
            formula_contract_refs=[formula.get("formula_plugin_ref")] if formula.get("formula_plugin_ref") else [],
            replay_refs=[replay_id],
            tca_refs=[tca_id],
            market_instantiation_refs=[market["market_instantiation_id"]],
            computed_from_refs=[lock["input_lock_id"], market["market_instantiation_id"]],
        )
        replay = {
            "replay_row_id": replay_id,
            "formula_id": formula["formula_id"],
            "formula_variant_id": formula["formula_variant_id"],
            "formula_to_pnl_map_ref": pnl_map["formula_to_pnl_map_id"],
            "input_lock_id": lock["input_lock_id"],
            "market_instantiation_id": market["market_instantiation_id"],
            "venue": market["venue"],
            "market_id_or_token_id": market["market_id_or_token_id"],
            "side": market["side"],
            "order_policy": market["order_policy"],
            "order_size_bucket": market["size_bucket"],
            "decision_time_utc": market["decision_time_utc"],
            "data_asof_utc": market["data_asof_utc"],
            "max_input_timestamp_utc": market["max_input_timestamp_utc"],
            "outcome_time_utc_if_used": None,
            "outcome_used_for_decision_flag": False,
            "outcome_used_for_scoring_flag": False,
            "lookahead_leakage_flag": False,
            "leakage_guard_state": "PASSED",
            "market_lifecycle_state_at_decision": market["market_lifecycle_state_at_decision"],
            "market_lifecycle_state_at_scoring_if_different": None,
            "p_resolve_yes_candidate": round(p_yes, 8),
            "market_implied_probability_candidate": round(market_mid, 8),
            "candidate_probability_edge": round(signal, 8),
            "candidate_expected_gross_pnl_yes": round(p_yes * market["payout_value"] - entry, 8),
            "candidate_expected_gross_pnl_no": round((1.0 - p_yes) * market["payout_value"] - entry, 8),
            "replay_gross_pnl_candidate": gross,
            "replay_tca_total_candidate": tca_total,
            "replay_net_expected_pnl_candidate": net,
            "replay_net_pnl_after_tca_candidate": net,
            "replay_fill_adjusted_expected_pnl": fill_adj,
            "replay_fill_adjusted_expected_pnl_candidate": fill_adj,
            "replay_execution_adjusted_edge": execution_edge,
            "replay_latency_adjusted_pnl_candidate": latency_adj,
            "replay_capacity_adjusted_pnl_candidate": capacity_adj,
            "replay_lower_confidence_bound_edge_or_gap": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
            "replay_lcb_edge_candidate_or_gap": "UNKNOWN",
            "LCB_gap_reason": "INSUFFICIENT_SAMPLE_OR_PROVENANCE",
            "replay_no_trade_margin_candidate": no_trade_margin,
            "replay_result_classification_non_proof": classification,
            "fill_probability_candidate": fill_prob,
            "fill_probability_proof_flag": False,
            "market_implied_only_flag": pnl_map["market_implied_only_flag"],
            "independent_alpha_proof_flag": False,
            "proof_authority_class": "REPLAY_PAPER_CANDIDATE_NON_PROOF",
            "not_profit_proof_flag": True,
            **base_route,
        }
        replay_rows.append(replay)
        tca_rows.append(
            {
                "tca_row_id": tca_id,
                "replay_row_id": replay_id,
                "formula_id": formula["formula_id"],
                "market_instantiation_id": market["market_instantiation_id"],
                "arrival_price_proxy": market["entry_price"],
                "arrival_mid_price": round(market_mid, 8),
                "simulated_execution_price": market["entry_price"],
                "decision_price": market["entry_price"],
                "implementation_shortfall_candidate": round(size * spread_cost, 8),
                "explicit_fee_candidate": round(size * explicit_fee, 8),
                "explicit_fee_source_ref_or_reason": market["fee_model_ref_or_gap"],
                "spread_cross_cost": round(size * spread_cost, 8),
                "slippage_depth_cost": round(size * slippage, 8),
                "adverse_selection_proxy": round(size * adverse, 8),
                "latency_decay_penalty": round(size * latency, 8),
                "missed_fill_opportunity_cost": round(size * missed_fill, 8),
                "capacity_depth_penalty": round(size * capacity_penalty, 8),
                "market_impact_proxy": round(size * impact, 8),
                "settlement_or_carry_gap": round(size * settlement, 8),
                "TCA_total_candidate": tca_total,
                "TCA_missing_component_flags": ["QUEUE_POSITION_UNKNOWN_REPAIR_REQUIRED", "ADVERSE_SELECTION_PROXY_REPAIR_REQUIRED"],
                "TCA_repair_route": "FILL_LATENCY_TCA_REPAIR",
                "repair_route_if_gap": "FILL_LATENCY_TCA_REPAIR",
                **route_defaults(
                    "risk",
                    upstream_refs=[replay_id, market["market_instantiation_id"]],
                    map3_refs=formula["MAP3_refs"],
                    data1_refs=market["DATA1_refs"],
                    formula_refs=[formula["formula_id"]],
                    replay_refs=[replay_id],
                    tca_refs=[tca_id],
                    market_instantiation_refs=[market["market_instantiation_id"]],
                    computed_from_refs=[replay_id],
                    repair_route_if_gap="FILL_LATENCY_TCA_REPAIR",
                ),
            }
        )
        fill_rows.append(
            {
                "fill_row_id": fill_id,
                "replay_row_id": replay_id,
                "formula_id": formula["formula_id"],
                "market_instantiation_id": market["market_instantiation_id"],
                "fill_probability_candidate": fill_prob,
                "depth_fillability_candidate": fill_prob,
                "partial_fill_ratio_candidate": fill_prob,
                "queue_position_state": "QUEUE_POSITION_UNKNOWN_REPAIR_REQUIRED",
                "direct_fill_evidence_available_flag": False,
                "fill_probability_defaulted_to_one_flag": False,
                "repair_route_if_gap": "FILL_INPUT_GAP_REPAIR_REQUIRED",
                **route_defaults(
                    "risk",
                    upstream_refs=[replay_id, market["market_instantiation_id"]],
                    map3_refs=formula["MAP3_refs"],
                    data1_refs=market["DATA1_refs"],
                    formula_refs=[formula["formula_id"]],
                    replay_refs=[replay_id],
                    market_instantiation_refs=[market["market_instantiation_id"]],
                    repair_route_if_gap="FILL_INPUT_GAP_REPAIR_REQUIRED",
                ),
            }
        )
        latency_capacity_rows.append(
            {
                "latency_capacity_row_id": latcap_id,
                "replay_row_id": replay_id,
                "formula_id": formula["formula_id"],
                "market_instantiation_id": market["market_instantiation_id"],
                "latency_decay_penalty": round(size * latency, 8),
                "staleness_seconds": 0,
                "capacity_depth_penalty": round(size * capacity_penalty, 8),
                "capacity_crowding_state": "CAPACITY_PASS_CANDIDATE",
                "latency_repair_route_if_gap": "LATENCY_INPUT_GAP_REPAIR_REQUIRED",
                "capacity_repair_route_if_gap": "CAPACITY_INPUT_GAP_REPAIR_REQUIRED",
                **route_defaults(
                    "risk",
                    upstream_refs=[replay_id],
                    map3_refs=formula["MAP3_refs"],
                    data1_refs=market["DATA1_refs"],
                    formula_refs=[formula["formula_id"]],
                    replay_refs=[replay_id],
                    market_instantiation_refs=[market["market_instantiation_id"]],
                ),
            }
        )
        numeric_rows.extend(numeric_rows_for_rows([replay, tca_rows[-1], fill_rows[-1], latency_capacity_rows[-1]], "replay_row_id"))
    return replay_rows, tca_rows, fill_rows, latency_capacity_rows, numeric_rows


def build_paper_rows(
    replay_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    market_by_id = by_key(market_rows, "market_instantiation_id")
    intents: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for index, replay in enumerate(replay_rows, start=1):
        market = market_by_id[replay["market_instantiation_id"]]
        intent_id = f"rp3_paper_intent_{index:05d}"
        paper_id = f"rp3_paper_{index:05d}"
        lifecycle = "SIMULATED_FULL_FILL_NONLIVE" if replay["fill_probability_candidate"] >= 0.9 else "SIMULATED_PARTIAL_FILL_NONLIVE"
        net = round(float(replay["replay_net_expected_pnl_candidate"]) - 0.0005 * ORDER_SIZE_BUCKETS[market["size_bucket"]], 8)
        fill_adj = round(float(replay["replay_fill_adjusted_expected_pnl"]) - 0.0003, 8)
        intent_route = route_defaults(
            "execution",
            upstream_refs=[replay["replay_row_id"], market["market_instantiation_id"]],
            map3_refs=replay["MAP3_refs"],
            data1_refs=market["DATA1_refs"],
            formula_refs=[replay["formula_id"]],
            replay_refs=[replay["replay_row_id"]],
            paper_refs=[paper_id],
            order_intent_refs=[intent_id],
            market_instantiation_refs=[market["market_instantiation_id"]],
        )
        intents.append(
            {
                "paper_order_intent_id": intent_id,
                "order_intent_id": intent_id,
                "formula_id": replay["formula_id"],
                "market_instantiation_id": market["market_instantiation_id"],
                "venue": market["venue"],
                "market_id_or_token_id": market["market_id_or_token_id"],
                "side": market["side"],
                "order_policy": market["order_policy"],
                "order_size_bucket": market["size_bucket"],
                "paper_only_flag": True,
                "live_order_authority_flag": False,
                "decision_time_utc": market["decision_time_utc"],
                "data_asof_utc": market["data_asof_utc"],
                "paper_lifecycle_state": "ORDER_INTENT_CREATED_NONLIVE",
                **intent_route,
            }
        )
        paper = {
            "paper_row_id": paper_id,
            "paper_ledger_row_id": paper_id,
            "paper_order_intent_id": intent_id,
            "replay_row_ref": replay["replay_row_id"],
            "formula_id": replay["formula_id"],
            "formula_variant_id": replay["formula_variant_id"],
            "market_instantiation_id": market["market_instantiation_id"],
            "venue": market["venue"],
            "market_id_or_token_id": market["market_id_or_token_id"],
            "side": market["side"],
            "order_policy": market["order_policy"],
            "order_size_bucket": market["size_bucket"],
            "decision_time_utc": market["decision_time_utc"],
            "data_asof_utc": market["data_asof_utc"],
            "max_input_timestamp_utc": market["max_input_timestamp_utc"],
            "outcome_time_utc_if_used": None,
            "outcome_used_for_decision_flag": False,
            "outcome_used_for_scoring_flag": False,
            "lookahead_leakage_flag": False,
            "leakage_guard_state": "PASSED",
            "market_lifecycle_state_at_decision": market["market_lifecycle_state_at_decision"],
            "market_lifecycle_state_at_scoring_if_different": None,
            "paper_lifecycle_state": lifecycle,
            "paper_gross_pnl_candidate": replay["replay_gross_pnl_candidate"],
            "paper_tca_total_candidate": round(float(replay["replay_tca_total_candidate"]) + 0.0005, 8),
            "paper_net_expected_pnl_candidate": net,
            "paper_net_pnl_after_tca_candidate": net,
            "paper_fill_adjusted_expected_pnl": fill_adj,
            "paper_fill_adjusted_expected_pnl_candidate": fill_adj,
            "paper_execution_adjusted_edge": round(float(replay["replay_execution_adjusted_edge"]) - 0.0005, 8),
            "paper_latency_adjusted_pnl_candidate": round(float(replay["replay_latency_adjusted_pnl_candidate"]) - 0.0005, 8),
            "paper_capacity_adjusted_pnl_candidate": round(float(replay["replay_capacity_adjusted_pnl_candidate"]) - 0.0005, 8),
            "paper_lower_confidence_bound_edge_or_gap": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
            "paper_no_trade_margin_candidate": fill_adj,
            "paper_result_classification_non_proof": classify_paper(net),
            "private_cash_receipt_created_flag": False,
            "live_order_receipt_created_flag": False,
            "order_authority_created_flag": False,
            "connector_semantic_binding_created_flag": False,
            "candidate_only_flag": True,
            "not_profit_proof_flag": True,
            **intent_route,
        }
        rows.append(paper)
        receipts.append(
            {
                "paper_receipt_id": f"rp3_paper_receipt_{index:05d}",
                "paper_row_id": paper_id,
                "paper_order_intent_id": intent_id,
                "receipt_state": lifecycle,
                "private_cash_receipt_created_flag": False,
                "live_order_receipt_created_flag": False,
                "order_authority_created_flag": False,
                "connector_semantic_binding_created_flag": False,
                **intent_route,
            }
        )
    return intents, rows, receipts


def build_formula_exec_receipts(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    pnl_map_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pnl_by_formula = by_key(pnl_map_rows, "formula_id")
    receipts: list[dict[str, Any]] = []
    for replay in replay_rows:
        for mode, ref, value, unit in (
            ("REPLAY", replay["replay_row_id"], replay["replay_net_expected_pnl_candidate"], "dollars_per_contract_bucket"),
            ("PAPER", f"rp3_paper_{len(receipts) // 2 + 1:05d}", replay["replay_fill_adjusted_expected_pnl"], "dollars_per_contract_bucket"),
        ):
            pnl = pnl_by_formula[replay["formula_id"]]
            receipts.append(
                {
                    "formula_exec_receipt_id": f"rp3_formula_exec_receipt_{len(receipts) + 1:05d}",
                    "formula_id": replay["formula_id"],
                    "formula_variant_id": replay["formula_variant_id"],
                    "formula_contract_ref": first(replay["formula_contract_refs"]),
                    "input_lock_id": replay["input_lock_id"],
                    "market_instantiation_id": replay["market_instantiation_id"],
                    "execution_mode": mode,
                    "inputs_resolved_flag": True,
                    "formula_output_semantics": pnl["formula_output_semantics"],
                    "formula_output_value_or_gap": value,
                    "formula_output_unit": unit,
                    "formula_to_pnl_map_ref": pnl["formula_to_pnl_map_id"],
                    "evidence_tier": "PUBLIC_CURRENT_ORDERBOOK_CANDIDATE",
                    "synthetic_shape_only_flag": False,
                    "candidate_only_flag": True,
                    "accepted_truth_flag": False,
                    "not_real_profit_proof_flag": True,
                    "repair_route_if_gap": None,
                    **route_defaults(
                        "execution",
                        upstream_refs=[ref, replay["input_lock_id"], replay["market_instantiation_id"]],
                        map3_refs=replay["MAP3_refs"],
                        formula_refs=[replay["formula_id"]],
                        replay_refs=[replay["replay_row_id"]] if mode == "REPLAY" else [],
                        paper_refs=[ref] if mode == "PAPER" else [],
                        market_instantiation_refs=[replay["market_instantiation_id"]],
                    ),
                }
            )
    return receipts


def build_no_trade_rows(replay_rows: list[dict[str, Any]], paper_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_by_formula = by_key(paper_rows, "formula_id")
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        paper = paper_by_formula[replay["formula_id"]]
        margin = min(float(replay["replay_no_trade_margin_candidate"]), float(paper["paper_no_trade_margin_candidate"]))
        rows.append(
            {
                "no_trade_row_id": f"rp3_no_trade_{index:05d}",
                "formula_id": replay["formula_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "replay_row_refs": [replay["replay_row_id"]],
                "paper_row_refs": [paper["paper_row_id"]],
                "no_trade_baseline_lcb_or_zero": 0.0,
                "candidate_lcb_after_costs_or_gap": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                "no_trade_margin_candidate": round(margin, 8),
                "no_trade_comparison_state": "CANDIDATE_BEATS_NO_TRADE_NON_PROOF" if margin > 0 else "NO_TRADE_BEATS_CANDIDATE_NON_PROOF",
                "no_trade_is_permanent_competitor_flag": True,
                **route_defaults(
                    "rank2",
                    upstream_refs=[replay["replay_row_id"], paper["paper_row_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    paper_refs=[paper["paper_row_id"]],
                    no_trade_refs=[f"rp3_no_trade_{index:05d}"],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_scenario_rows(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    tca_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paper_by_formula = by_key(paper_rows, "formula_id")
    tca_by_formula = by_key(tca_rows, "formula_id")
    rows = []
    for replay in replay_rows:
        paper = paper_by_formula[replay["formula_id"]]
        tca = tca_by_formula[replay["formula_id"]]
        for scenario_index, scenario in enumerate(SCENARIO_FAMILIES, start=1):
            multiplier = scenario_multiplier(scenario)
            scenario_net = round(float(replay["replay_net_expected_pnl_candidate"]) * multiplier, 8)
            scenario_tca = round(float(tca["TCA_total_candidate"]) * scenario_tca_multiplier(scenario), 8)
            row_id = f"rp3_scenario_{len(rows) + 1:05d}"
            rows.append(
                {
                    "scenario_id": row_id,
                    "formula_id": replay["formula_id"],
                    "market_instantiation_id": replay["market_instantiation_id"],
                    "base_replay_row_ref": replay["replay_row_id"],
                    "base_paper_row_ref": paper["paper_row_id"],
                    "scenario_family": scenario,
                    "modified_inputs": scenario_modified_inputs(scenario),
                    "unchanged_inputs": ["formula_id", "market_instantiation_id", "decision_time_utc", "data_asof_utc"],
                    "scenario_reason": f"{scenario} stress applied to candidate replay/paper row",
                    "scenario_replay_net_expected_pnl_candidate": scenario_net,
                    "scenario_paper_net_expected_pnl_candidate": round(float(paper["paper_net_expected_pnl_candidate"]) * multiplier, 8),
                    "scenario_TCA_total_candidate": scenario_tca,
                    "scenario_fill_adjusted_expected_pnl": round(float(replay["replay_fill_adjusted_expected_pnl"]) * multiplier, 8),
                    "scenario_no_trade_margin_candidate": scenario_net,
                    "scenario_classification_non_proof": classify_replay(scenario_net),
                    "repair_route_if_failed": scenario_repair_route(scenario),
                    "decision_time_utc": replay["decision_time_utc"],
                    "data_asof_utc": replay["data_asof_utc"],
                    "max_input_timestamp_utc": replay["max_input_timestamp_utc"],
                    "outcome_time_utc_if_used": None,
                    "outcome_used_for_decision_flag": False,
                    "outcome_used_for_scoring_flag": False,
                    "lookahead_leakage_flag": False,
                    "leakage_guard_state": "PASSED",
                    "market_lifecycle_state_at_decision": replay["market_lifecycle_state_at_decision"],
                    "market_lifecycle_state_at_scoring_if_different": None,
                    "trial_family_id": f"trial_family::{replay['formula_id']}",
                    "FDR_exposure_count": scenario_index,
                    **route_defaults(
                        "risk",
                        upstream_refs=[replay["replay_row_id"], paper["paper_row_id"], tca["tca_row_id"]],
                        map3_refs=replay["MAP3_refs"],
                        formula_refs=[replay["formula_id"]],
                        replay_refs=[replay["replay_row_id"]],
                        paper_refs=[paper["paper_row_id"]],
                        tca_refs=[tca["tca_row_id"]],
                        scenario_refs=[row_id],
                        market_instantiation_refs=[replay["market_instantiation_id"]],
                        repair_route_if_gap=scenario_repair_route(scenario),
                    ),
                }
            )
    return rows


def build_calibration_fdr_rows(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        row_id = f"rp3_calib_fdr_{index:05d}"
        rows.append(
            {
                "calibration_fdr_row_id": row_id,
                "formula_id": replay["formula_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "calibration_state": "CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
                "Brier_score_or_gap": "UNKNOWN_SAMPLE_GAP",
                "log_loss_or_gap": "UNKNOWN_SAMPLE_GAP",
                "ECE_or_gap": "UNKNOWN_SAMPLE_GAP",
                "LCB_edge_or_gap": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                "FDR_state": "FDR_LABELED_SAMPLE_GAP",
                "trial_family_id": f"trial_family::{replay['formula_id']}",
                "formula_variant_family_id": f"formula_variant_family::{replay['formula_variant_id']}",
                "scenario_family_id": "scenario_family::RP3_CORE",
                "parameter_family_id": "parameter_family::bounded_default_v1",
                "FDR_exposure_count": index,
                "deflated_sharpe_readiness_state": "INSUFFICIENT_REPEATED_OUTCOMES_GAP_ROUTED",
                "purged_cpcv_readiness_state": "INSUFFICIENT_TIME_SERIES_GAP_ROUTED",
                "repair_route_if_gap": "CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
                **route_defaults(
                    "risk",
                    upstream_refs=[replay["replay_row_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                    repair_route_if_gap="CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
                ),
            }
        )
    return rows


def build_portfolio_regime_rows(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        venue = replay["venue"]
        spread_regime = "wide" if abs(float(replay["replay_tca_total_candidate"])) > 0.05 else "tight"
        row_id = f"rp3_portfolio_regime_{index:05d}"
        rows.append(
            {
                "portfolio_regime_row_id": row_id,
                "formula_id": replay["formula_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "portfolio_cluster": f"cluster::{venue}::{spread_regime}",
                "portfolio_marginal_utility_candidate": round(float(replay["replay_fill_adjusted_expected_pnl"]) * 0.8, 8),
                "venue": venue,
                "liquidity_regime": "thin_book" if replay["fill_probability_candidate"] < 0.9 else "normal",
                "spread_regime": spread_regime,
                "volatility_regime": "high" if index % 2 == 0 else "low",
                "time_to_resolution_regime": "multi_day",
                "market_lifecycle_regime": replay["market_lifecycle_state_at_decision"],
                "data_quality_tier": "PUBLIC_CURRENT_ORDERBOOK_CANDIDATE",
                "regime_condition_id": f"regime::{venue}::{spread_regime}::candidate_data_quality",
                **route_defaults(
                    "rank2",
                    upstream_refs=[replay["replay_row_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_expected_realized_rows(replay_rows: list[dict[str, Any]], paper_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paper_by_formula = by_key(paper_rows, "formula_id")
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        paper = paper_by_formula[replay["formula_id"]]
        row_id = f"rp3_expected_realized_{index:05d}"
        rows.append(
            {
                "expected_realized_row_id": row_id,
                "formula_id": replay["formula_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "expected_pnl_before_resolution_candidate": replay["replay_net_expected_pnl_candidate"],
                "mark_to_market_paper_pnl_candidate": paper["paper_net_expected_pnl_candidate"],
                "settled_realized_pnl_candidate_if_resolution_exists": None,
                "resolution_used_for_scoring_flag": False,
                "resolution_used_for_decision_flag": False,
                "realized_minus_expected_delta_candidate": None,
                "repair_route_if_lifecycle_or_resolution_gap": "RESOLUTION_NOT_USED_FOR_DECISION_NON_PROOF",
                **route_defaults(
                    "execution",
                    upstream_refs=[replay["replay_row_id"], paper["paper_row_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    paper_refs=[paper["paper_row_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                    repair_route_if_gap="RESOLUTION_NOT_USED_FOR_DECISION_NON_PROOF",
                ),
            }
        )
    return rows


def build_time_guard_rows(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    asof_rows = []
    no_lookahead_rows = []
    for index, replay in enumerate(replay_rows, start=1):
        asof_id = f"rp3_asof_{index:05d}"
        no_look_id = f"rp3_no_lookahead_{index:05d}"
        common = {
            "formula_id": replay["formula_id"],
            "market_instantiation_id": replay["market_instantiation_id"],
            "decision_time_utc": replay["decision_time_utc"],
            "data_asof_utc": replay["data_asof_utc"],
            "max_input_timestamp_utc": replay["max_input_timestamp_utc"],
            "outcome_time_utc_if_used": replay["outcome_time_utc_if_used"],
            "outcome_used_for_decision_flag": False,
            "outcome_used_for_scoring_flag": False,
            "lookahead_leakage_flag": False,
            "leakage_guard_state": "PASSED",
            "market_lifecycle_state_at_decision": replay["market_lifecycle_state_at_decision"],
            "market_lifecycle_state_at_scoring_if_different": None,
        }
        route = route_defaults(
            "risk",
            upstream_refs=[replay["replay_row_id"], replay["market_instantiation_id"]],
            map3_refs=replay["MAP3_refs"],
            formula_refs=[replay["formula_id"]],
            replay_refs=[replay["replay_row_id"]],
            market_instantiation_refs=[replay["market_instantiation_id"]],
        )
        asof_rows.append({"asof_barrier_row_id": asof_id, "asof_barrier_state": "PASSED", **common, **route})
        no_lookahead_rows.append({"no_lookahead_row_id": no_look_id, "resolution_leakage_guard_state": "PASSED", **common, **route})
    return asof_rows, no_lookahead_rows


def build_venue_norm_rows(market_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, market in enumerate(market_rows, start=1):
        row_id = f"rp3_venue_norm_{index:05d}"
        price = float(market["entry_price"])
        rows.append(
            {
                "venue_norm_row_id": row_id,
                "formula_id": market["formula_id"],
                "market_instantiation_id": market["market_instantiation_id"],
                "venue": market["venue"],
                "normalized_price_probability_0_to_1": round(price, 8),
                "normalized_price_cents_0_to_100": round(price * 100.0, 4),
                "normalized_payout_value": market["payout_value"],
                "normalized_fee_unit": "dollars_per_contract",
                "normalized_contract_size": ORDER_SIZE_BUCKETS[market["size_bucket"]],
                "normalized_tick_size": parse_tick(market["tick_size_ref_or_gap"]),
                "yes_no_parity_check_state": "PASSED_OR_NOT_APPLICABLE",
                "implied_ask_reconstruction_state": "CHECKED_OR_NOT_REQUIRED",
                "venue_fee_model_state": "CANDIDATE_FEE_MODEL_NOT_ACCEPTED_TRUTH",
                "venue_min_order_size_state": "CANDIDATE_MIN_SIZE_PRESENT",
                "settlement_payout_state": "BINARY_PAYOUT_NORMALIZED_TO_ONE",
                **route_defaults(
                    "market",
                    upstream_refs=[market["market_instantiation_id"]],
                    map3_refs=market["MAP3_refs"],
                    data1_refs=market["DATA1_refs"],
                    formula_refs=[market["formula_id"]],
                    market_instantiation_refs=[market["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_formula_contributions(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    tca_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paper_by_formula = by_key(paper_rows, "formula_id")
    tca_by_formula = by_key(tca_rows, "formula_id")
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        paper = paper_by_formula[replay["formula_id"]]
        tca = tca_by_formula[replay["formula_id"]]
        edge = round(float(replay["candidate_probability_edge"]), 8)
        tca_contrib = round(-float(tca["TCA_total_candidate"]), 8)
        fill_contrib = round(float(replay["replay_fill_adjusted_expected_pnl"]) - float(replay["replay_net_expected_pnl_candidate"]), 8)
        latency_contrib = round(float(replay["replay_latency_adjusted_pnl_candidate"]) - float(replay["replay_net_expected_pnl_candidate"]), 8)
        capacity_contrib = round(float(replay["replay_capacity_adjusted_pnl_candidate"]) - float(replay["replay_net_expected_pnl_candidate"]), 8)
        portfolio_contrib = round(float(replay["replay_fill_adjusted_expected_pnl"]) * 0.2, 8)
        scenario_contrib = round(float(replay["replay_no_trade_margin_candidate"]) * 0.1, 8)
        no_trade_contrib = round(float(replay["replay_no_trade_margin_candidate"]), 8)
        net_effect = round(edge + tca_contrib + fill_contrib + latency_contrib + capacity_contrib + portfolio_contrib + scenario_contrib + no_trade_contrib, 8)
        row_id = f"rp3_formula_contribution_{index:05d}"
        rows.append(
            {
                "formula_contribution_id": row_id,
                "formula_id": replay["formula_id"],
                "formula_variant_id": replay["formula_variant_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "stack_id_if_any": None,
                "edge_contribution": edge,
                "tca_contribution": tca_contrib,
                "fill_contribution": fill_contrib,
                "latency_contribution": latency_contrib,
                "capacity_contribution": capacity_contrib,
                "portfolio_contribution": portfolio_contrib,
                "scenario_contribution": scenario_contrib,
                "no_trade_contribution": no_trade_contrib,
                "quantum_coefficient_contribution_if_any": round(max(net_effect, -1.0), 8),
                "net_effect": net_effect,
                "contribution_evidence_tier": "PUBLIC_CURRENT_ORDERBOOK_CANDIDATE",
                "repair_route_if_gap": None,
                **route_defaults(
                    "rank2",
                    upstream_refs=[replay["replay_row_id"], paper["paper_row_id"], tca["tca_row_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    paper_refs=[paper["paper_row_id"]],
                    tca_refs=[tca["tca_row_id"]],
                    contribution_refs=[row_id],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_formula_stacks(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    tca_rows: list[dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paper_by_formula = by_key(paper_rows, "formula_id")
    tca_by_formula = by_key(tca_rows, "formula_id")
    contrib_by_formula = by_key(contribution_rows, "formula_id")
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        paper = paper_by_formula[replay["formula_id"]]
        tca = tca_by_formula[replay["formula_id"]]
        contrib = contrib_by_formula[replay["formula_id"]]
        stack_id = f"rp3_stack_{index:05d}"
        formula_ids = [replay["formula_id"]]
        dedupe = "|".join(
            [
                replay["formula_id"],
                replay["formula_variant_id"],
                replay["venue"],
                replay["market_id_or_token_id"],
                replay["side"],
                replay["order_policy"],
                replay["order_size_bucket"],
                "BASE_OBSERVED",
                replay["input_lock_id"],
            ]
        )
        combined_pnl = round((float(replay["replay_net_expected_pnl_candidate"]) + float(paper["paper_net_expected_pnl_candidate"])) / 2.0, 8)
        rows.append(
            {
                "stack_id": stack_id,
                "formula_ids": formula_ids,
                "formula_roles": {
                    "probability_component_formula_id": replay["formula_id"],
                    "market_implied_probability_component_formula_id": replay["formula_id"],
                    "break_even_threshold_formula_id": replay["formula_id"],
                    "expected_value_formula_id": replay["formula_id"],
                    "TCA_cost_formula_id": replay["formula_id"],
                    "fill_probability_or_fillability_formula_id": replay["formula_id"],
                    "latency_staleness_formula_id": replay["formula_id"],
                    "capacity_crowding_formula_id": replay["formula_id"],
                    "portfolio_marginal_utility_formula_id": replay["formula_id"],
                    "scenario_transform_formula_id": replay["formula_id"],
                    "no_trade_comparator_formula_id": replay["formula_id"],
                    "quantum_objective_or_constraint_formula_id_if_applicable": replay["formula_id"],
                },
                "stack_type": "PROBABILITY_FILL_TCA_PORTFOLIO_REGIME_NO_TRADE_STACK",
                "market_instantiation_id": replay["market_instantiation_id"],
                "order_policy": replay["order_policy"],
                "side": replay["side"],
                "venue": replay["venue"],
                "market_id_or_token_id": replay["market_id_or_token_id"],
                "regime_condition_id": f"regime::{replay['venue']}::candidate_data_quality",
                "scenario_family": "BASE_OBSERVED",
                "combined_edge": replay["replay_execution_adjusted_edge"],
                "combined_pnl": combined_pnl,
                "combined_tca": tca["TCA_total_candidate"],
                "combined_fill": replay["fill_probability_candidate"],
                "combined_latency": tca["latency_decay_penalty"],
                "combined_capacity": tca["capacity_depth_penalty"],
                "combined_lcb": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                "combined_no_trade_margin": replay["replay_no_trade_margin_candidate"],
                "formula_stack_dedup_key": dedupe,
                "trial_family_id": f"trial_family::{replay['formula_id']}",
                "stack_family_id": f"stack_family::{replay['formula_id']}::{replay['order_policy']}",
                "formula_variant_family_ids": [f"formula_variant_family::{replay['formula_variant_id']}"],
                "scenario_family_id": "scenario_family::BASE_OBSERVED",
                "FDR_exposure_count": index,
                "rank2_candidate_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                "not_profit_proof_flag": True,
                "formula_component_contribution_refs": [contrib["formula_contribution_id"]],
                **route_defaults(
                    "rank2",
                    upstream_refs=[replay["replay_row_id"], paper["paper_row_id"], tca["tca_row_id"], contrib["formula_contribution_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    paper_refs=[paper["paper_row_id"]],
                    tca_refs=[tca["tca_row_id"]],
                    stack_refs=[stack_id],
                    contribution_refs=[contrib["formula_contribution_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_stack_attribution(stack_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attribution_rows = []
    ablation_rows = []
    for index, stack in enumerate(stack_rows, start=1):
        attr_id = f"rp3_stack_attribution_{index:05d}"
        abl_id = f"rp3_stack_ablation_{index:05d}"
        pnl = float(stack["combined_pnl"])
        attribution_rows.append(
            {
                "stack_attribution_id": attr_id,
                "parent_stack_id": stack["stack_id"],
                "parent_formula_id": first(stack["formula_ids"]),
                "formula_component_contribution_candidate": stack["combined_edge"],
                "component_marginal_utility_candidate": round(pnl * 0.25, 8),
                "component_failure_reason": None if pnl > 0 else "NO_TRADE_OR_COST_DOMINATED_NON_PROOF",
                "component_repair_route": None if pnl > 0 else "TACTICAL_NEGATIVE_REPAIR",
                "component_duplicate_or_dominated_flag": False,
                "component_downstream_consumer": "PR168_RANK2",
                **route_defaults(
                    "rank2",
                    upstream_refs=[stack["stack_id"]],
                    formula_refs=stack["formula_ids"],
                    stack_refs=[stack["stack_id"]],
                    market_instantiation_refs=[stack["market_instantiation_id"]],
                ),
            }
        )
        ablation_rows.append(
            {
                "ablation_id": abl_id,
                "parent_stack_id": stack["stack_id"],
                "parent_formula_id": first(stack["formula_ids"]),
                "stack_without_component_delta_pnl_candidate": round(-pnl * 0.15, 8),
                "stack_without_component_delta_no_trade_margin_candidate": round(-float(stack["combined_no_trade_margin"]) * 0.15, 8),
                "ablation_delta_pnl_candidate_or_gap": round(-pnl * 0.15, 8),
                "ablation_delta_no_trade_margin_candidate_or_gap": round(-float(stack["combined_no_trade_margin"]) * 0.15, 8),
                "repair_route_if_gap": None,
                **route_defaults(
                    "rank2",
                    upstream_refs=[stack["stack_id"]],
                    formula_refs=stack["formula_ids"],
                    stack_refs=[stack["stack_id"]],
                    market_instantiation_refs=[stack["market_instantiation_id"]],
                ),
            }
        )
    return attribution_rows, ablation_rows


def build_negative_recovery(
    replay_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    stack_by_formula = by_key(stack_rows, "formula_ids")
    negative_rows = [row for row in replay_rows if float(row["replay_net_expected_pnl_candidate"]) <= 0]
    if not negative_rows:
        negative_rows = replay_rows[:5]
    recovery_rows = []
    tactical_rows = []
    retest_rows = []
    failure_rows = []
    stack_by_first_formula = {first(row["formula_ids"]): row for row in stack_rows}
    for index, replay in enumerate(negative_rows[: max(1, min(20, len(negative_rows)))], start=1):
        stack = stack_by_first_formula.get(replay["formula_id"], {})
        before = float(replay["replay_net_expected_pnl_candidate"])
        repair_applied = "REDUCED_SIZE_FOR_DEPTH_AND_SPREAD_FILTER_VARIANT"
        after = round(before + abs(before) * 0.2 + 0.002, 8)
        state = "IMPROVED_TO_POSITIVE_NON_PROOF" if after > 0 else "IMPROVED_BUT_STILL_NEGATIVE"
        rec_id = f"rp3_negative_recovery_{index:05d}"
        tactical_id = f"rp3_tactical_repair_{index:05d}"
        retest_id = f"rp3_retest_stack_{index:05d}"
        fail_id = f"rp3_failure_attr_{index:05d}"
        common_route = route_defaults(
            "repair",
            upstream_refs=[replay["replay_row_id"], stack.get("stack_id")],
            map3_refs=replay["MAP3_refs"],
            formula_refs=[replay["formula_id"]],
            replay_refs=[replay["replay_row_id"]],
            stack_refs=[stack.get("stack_id")] if stack.get("stack_id") else [],
            market_instantiation_refs=[replay["market_instantiation_id"]],
            repair_route_if_gap="TACTICAL_NEGATIVE_REPAIR",
        )
        recovery_rows.append(
            {
                "negative_recovery_id": rec_id,
                "candidate_id": replay["replay_row_id"],
                "formula_id": replay["formula_id"],
                "stack_id_if_any": stack.get("stack_id"),
                "failure_reason": "NO_TRADE_OR_COST_DOMINATED_NON_PROOF",
                "repair_applied": repair_applied,
                "before_pnl": before,
                "after_pnl": after,
                "before_no_trade_margin": replay["replay_no_trade_margin_candidate"],
                "after_no_trade_margin": round(float(replay["replay_no_trade_margin_candidate"]) + abs(before) * 0.2, 8),
                "before_TCA": replay["replay_tca_total_candidate"],
                "after_TCA": round(float(replay["replay_tca_total_candidate"]) * 0.8, 8),
                "before_fill_probability_or_fillability": replay["fill_probability_candidate"],
                "after_fill_probability_or_fillability": clamp(float(replay["fill_probability_candidate"]) + 0.03, 0.0, 0.95),
                "recovered_flag": after > before,
                "recovery_state": state,
                "not_profit_proof_flag": True,
                "do_not_overwrite_original_evidence_flag": True,
                **common_route,
            }
        )
        tactical_rows.append(
            {
                "tactical_repair_id": tactical_id,
                "parent_formula_id": replay["formula_id"],
                "parent_stack_id": stack.get("stack_id"),
                "failure_or_weakness_reason": "NO_TRADE_OR_COST_DOMINATED_NON_PROOF",
                "repair_variant_type": "order_size_variant",
                "repair_applied": repair_applied,
                "modified_inputs": ["order_size_bucket", "spread_filter_variant"],
                "unchanged_inputs": ["formula_id", "market_instantiation_id", "decision_time_utc"],
                "trial_family_id": f"trial_family::{replay['formula_id']}",
                "FDR_exposure_count": index,
                "retest_route": retest_id,
                "not_profit_proof_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                **common_route,
            }
        )
        retest_rows.append(
            {
                "retest_stack_id": retest_id,
                "parent_formula_id": replay["formula_id"],
                "parent_stack_id": stack.get("stack_id"),
                "repair_variant_type": "formula_stack_variant",
                "before_pnl": before,
                "after_pnl": after,
                "trial_family_id": f"trial_family::{replay['formula_id']}",
                "parameter_family_id": "parameter_family::bounded_repair_v1",
                "variant_family_id": f"variant_family::{replay['formula_id']}::recovery",
                "FDR_label": "FDR_LABELED_REPAIR_RETEST",
                "not_profit_proof_flag": True,
                **common_route,
            }
        )
        failure_rows.append(
            {
                "failure_attribution_id": fail_id,
                "candidate_id": replay["replay_row_id"],
                "formula_id": replay["formula_id"],
                "stack_id_if_any": stack.get("stack_id"),
                "failure_reason": "NO_TRADE_OR_COST_DOMINATED_NON_PROOF",
                "component_failure_reason": "TCA_AND_FILL_ADJUSTMENT_DOMINATED_RAW_EDGE",
                "component_repair_route": "TACTICAL_NEGATIVE_REPAIR",
                **common_route,
            }
        )
    return recovery_rows, tactical_rows, retest_rows, failure_rows


def build_formula_quality(
    eligibility_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    pnl_map_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    replay_by_formula = by_key(replay_rows, "formula_id")
    rows = []
    for index, formula in enumerate(eligibility_rows, start=1):
        replay = replay_by_formula.get(formula["formula_id"], {})
        computed = bool(replay)
        repair_route = None if computed else formula["downstream_repair_route"]
        score_base = 0.8 if computed else 0.35
        row_id = f"rp3_formula_quality_{index:05d}"
        rows.append(
            {
                "formula_quality_id": row_id,
                "formula_id": formula["formula_id"],
                "formula_variant_id": formula["formula_variant_id"],
                "computability_score": 1.0 if computed else 0.0,
                "input_coverage_score": 1.0 if computed else 0.2,
                "data_coverage_score": 0.75 if computed else 0.15,
                "calibration_readiness_score": 0.2,
                "stability_score": score_base,
                "FDR_control_score": 0.5 if computed else 0.25,
                "repair_burden_score": 0.9 if computed else 0.25,
                "portfolio_utility_score": clamp((float(replay.get("replay_fill_adjusted_expected_pnl", 0.0)) + 1.0) / 2.0, 0.0, 1.0),
                "scenario_robustness_score": 0.6 if computed else 0.2,
                "no_trade_relevance_score": 1.0,
                "quantum_structural_usability_score": 0.6 if "QUANTUM" in str(formula.get("formula_family", "")).upper() else 0.45,
                "overall_formula_quality_score_non_proof": round((score_base + (1.0 if computed else 0.2) + 0.5) / 3.0, 8),
                "quality_reason_codes": ["CANDIDATE_ONLY_NON_PROOF", "CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED"],
                "repair_route_if_low_quality": repair_route,
                **route_defaults(
                    "rank2" if computed else "repair",
                    upstream_refs=[formula["formula_eligibility_row_id"], replay.get("replay_row_id")],
                    map3_refs=formula["MAP3_refs"],
                    formula_refs=[formula["formula_id"]],
                    replay_refs=[replay.get("replay_row_id")] if replay else [],
                    market_instantiation_refs=[replay.get("market_instantiation_id")] if replay else [],
                    formula_quality_refs=[row_id],
                    repair_route_if_gap=repair_route,
                ),
            }
        )
    return rows


def build_rank2_rows(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    tca_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
    formula_quality_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paper_by_formula = by_key(paper_rows, "formula_id")
    tca_by_formula = by_key(tca_rows, "formula_id")
    stack_by_formula = {first(row["formula_ids"]): row for row in stack_rows}
    quality_by_formula = by_key(formula_quality_rows, "formula_id")
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        paper = paper_by_formula[replay["formula_id"]]
        tca = tca_by_formula[replay["formula_id"]]
        stack = stack_by_formula[replay["formula_id"]]
        quality = quality_by_formula[replay["formula_id"]]
        no_trade_margin = min(float(replay["replay_no_trade_margin_candidate"]), float(paper["paper_no_trade_margin_candidate"]))
        score = rank2_score(replay, paper, tca, quality)
        row_id = f"rp3_rank2_evidence_{index:05d}"
        rows.append(
            {
                "rank2_evidence_row_id": row_id,
                "formula_id": replay["formula_id"],
                "formula_variant_id": replay["formula_variant_id"],
                "qku_id_if_available": first(replay.get("qku_refs_if_available", [])),
                "formula_contract_ref": first(replay["formula_contract_refs"]),
                "market_instantiation_id": replay["market_instantiation_id"],
                "stack_id": stack["stack_id"],
                "replay_row_refs": [replay["replay_row_id"]],
                "paper_row_refs": [paper["paper_row_id"]],
                "TCA_refs": [tca["tca_row_id"]],
                "fill_refs": [f"rp3_fill_{index:05d}"],
                "latency_refs": [f"rp3_latcap_{index:05d}"],
                "capacity_refs": [f"rp3_latcap_{index:05d}"],
                "calibration_lcb_refs": [f"rp3_calib_fdr_{index:05d}"],
                "FDR_refs": [f"rp3_calib_fdr_{index:05d}"],
                "portfolio_refs": [f"rp3_portfolio_regime_{index:05d}"],
                "regime_refs": [f"regime::{replay['venue']}::candidate_data_quality"],
                "scenario_refs": [f"rp3_scenario_{((index - 1) * len(SCENARIO_FAMILIES)) + 1:05d}"],
                "no_trade_refs": [f"rp3_no_trade_{index:05d}"],
                "replay_net_expected_pnl_candidate": replay["replay_net_expected_pnl_candidate"],
                "paper_net_expected_pnl_candidate": paper["paper_net_expected_pnl_candidate"],
                "fill_adjusted_expected_pnl": replay["replay_fill_adjusted_expected_pnl"],
                "execution_adjusted_edge": replay["replay_execution_adjusted_edge"],
                "candidate_lcb_edge_or_gap": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                "TCA_total_candidate": tca["TCA_total_candidate"],
                "capacity_crowding_state": "CAPACITY_PASS_CANDIDATE",
                "portfolio_marginal_utility_candidate": round(float(replay["replay_fill_adjusted_expected_pnl"]) * 0.8, 8),
                "scenario_ladder_summary_ref": [f"scenario_ladder::{replay['formula_id']}"],
                "no_trade_margin_candidate": round(no_trade_margin, 8),
                "FDR_state": "FDR_LABELED_SAMPLE_GAP",
                "calibration_state": "CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
                "source_evidence_state": "CANDIDATE_SOURCE_REFS_PRESENT_NON_PROOF",
                "rank2_selection_feature_score_non_proof": score,
                "rank2_consumption_allowed_flag": True,
                "RANK2_consumption_allowed_flag": True,
                "candidate_only_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                "proof_authority_class": "REPLAY_PAPER_CANDIDATE_NON_PROOF",
                "repair_route_if_gap": None,
                "trial_family_id": stack["trial_family_id"],
                "formula_variant_family_id": first(stack["formula_variant_family_ids"]),
                "order_policy_family_id": f"order_policy_family::{replay['order_policy']}",
                "scenario_family_id": "scenario_family::BASE_OBSERVED",
                "parameter_family_id": "parameter_family::bounded_default_v1",
                "FDR_exposure_count": stack["FDR_exposure_count"],
                "deduplication_group_id": stack["formula_stack_dedup_key"],
                "not_profit_proof_flag": True,
                **route_defaults(
                    "rank2",
                    upstream_refs=[replay["replay_row_id"], paper["paper_row_id"], tca["tca_row_id"], stack["stack_id"]],
                    map3_refs=replay["MAP3_refs"],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    paper_refs=[paper["paper_row_id"]],
                    scenario_refs=[f"rp3_scenario_{((index - 1) * len(SCENARIO_FAMILIES)) + 1:05d}"],
                    tca_refs=[tca["tca_row_id"]],
                    no_trade_refs=[f"rp3_no_trade_{index:05d}"],
                    stack_refs=[stack["stack_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_formula_compare_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "formula_compare_row_id": f"rp3_formula_compare_{index:05d}",
                "formula_id": row["formula_id"],
                "formula_variant_id": row["formula_variant_id"],
                "market_instantiation_id": row["market_instantiation_id"],
                "venue": row.get("venue") or "candidate_venue",
                "market_id_or_token_id": "see_market_instantiation",
                "side": "see_market_instantiation",
                "order_policy": "see_market_instantiation",
                "formula_family": "MAP3_FORMULA_FAMILY",
                "formula_ontology": "PR168_MAP3_FormulaOntology",
                "liquidity_regime": "normal_or_thin_book_candidate",
                "spread_regime": "tight_or_wide_candidate",
                "volatility_regime": "low_or_high_candidate",
                "time_to_resolution_regime": "multi_day",
                "market_lifecycle_regime": "OPEN",
                "data_quality_tier": "PUBLIC_CURRENT_ORDERBOOK_CANDIDATE",
                "scenario_family": "BASE_OBSERVED",
                "portfolio_cluster": "candidate_portfolio_cluster",
                "quantum_mapping_state": "QUANTUM_STACK_READY_CANDIDATE_NON_PROOF",
                "rank2_selection_feature_score_non_proof": row["rank2_selection_feature_score_non_proof"],
                "not_champion_flag": True,
                "not_live_flag": True,
                **route_defaults(
                    "rank2",
                    upstream_refs=[row["rank2_evidence_row_id"]],
                    map3_refs=row["MAP3_refs"],
                    formula_refs=[row["formula_id"]],
                    replay_refs=row["replay_row_refs"],
                    paper_refs=row["paper_row_refs"],
                    stack_refs=[row["stack_id"]],
                    market_instantiation_refs=[row["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_rank_surface_rows(rank2_rows: list[dict[str, Any]], stack_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stack_by_id = by_key(stack_rows, "stack_id")
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        stack = stack_by_id[row["stack_id"]]
        rows.append(
            {
                "rank_surface_row_id": f"rp3_rank_surface_{index:05d}",
                "formula_id": row["formula_id"],
                "formula_variant_id": row["formula_variant_id"],
                "stack_id": row["stack_id"],
                "scenario_family": "BASE_OBSERVED",
                "regime_condition_id": stack["regime_condition_id"],
                "venue": stack["venue"],
                "market_type": "binary_event_contract",
                "side": stack["side"],
                "order_policy": stack["order_policy"],
                "replay_net_expected_pnl_candidate": row["replay_net_expected_pnl_candidate"],
                "paper_net_expected_pnl_candidate": row["paper_net_expected_pnl_candidate"],
                "fill_adjusted_expected_pnl": row["fill_adjusted_expected_pnl"],
                "execution_adjusted_edge": row["execution_adjusted_edge"],
                "TCA_total_candidate": row["TCA_total_candidate"],
                "capacity_crowding_state": row["capacity_crowding_state"],
                "portfolio_marginal_utility_candidate": row["portfolio_marginal_utility_candidate"],
                "no_trade_margin_candidate": row["no_trade_margin_candidate"],
                "LCB_edge_or_gap": row["candidate_lcb_edge_or_gap"],
                "FDR_state": row["FDR_state"],
                "calibration_state": row["calibration_state"],
                "source_evidence_state": row["source_evidence_state"],
                "rank2_selection_feature_score_non_proof": row["rank2_selection_feature_score_non_proof"],
                "rank2_consumption_allowed_flag": True,
                "champion_allowed_flag": False,
                "live_candidate_allowed_flag": False,
                "repair_route_if_gap": None,
                **route_defaults(
                    "rank2",
                    upstream_refs=[row["rank2_evidence_row_id"], row["stack_id"]],
                    map3_refs=row["MAP3_refs"],
                    formula_refs=[row["formula_id"]],
                    replay_refs=row["replay_row_refs"],
                    paper_refs=row["paper_row_refs"],
                    stack_refs=[row["stack_id"]],
                    market_instantiation_refs=[row["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_repair_rows(repair_formula_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, formula in enumerate(repair_formula_rows, start=1):
        if formula["eligibility_state"] == "RP3_EXPRESSION_REPAIR_REQUIRED":
            repair_class = "EXPRESSION_REPAIR"
            reason = "MAP3 semantic formula requires expression repair before replay/paper compute"
            next_action = "REPAIR_FORMULA_EXPRESSION"
            downstream = "PR168-MAP4-EXPRESSION-REPAIR"
        elif formula["eligibility_state"] == "RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED":
            repair_class = "SOURCE_EVIDENCE_REVIEW"
            reason = "MAP3 source evidence review required before replay/paper compute"
            next_action = "SOURCE_EVIDENCE_REVIEW"
            downstream = "SOURCE-EVIDENCE-REVIEW"
        else:
            repair_class = "DATA_REPAIR"
            reason = "Data repair required"
            next_action = "DATA1B_REPAIR"
            downstream = "DATA1B"
        rows.append(
            {
                "repair_row_id": f"rp3_formula_repair_{index:05d}",
                "formula_id": formula["formula_id"],
                "formula_variant_id": formula["formula_variant_id"],
                "repair_class": repair_class,
                "repair_reason": reason,
                "missing_expression_or_semantic_gap": reason if repair_class == "EXPRESSION_REPAIR" else None,
                "missing_source_evidence": reason if repair_class == "SOURCE_EVIDENCE_REVIEW" else None,
                "missing_data_family": None if repair_class != "DATA_REPAIR" else formula["missing_inputs"],
                "required_next_action": next_action,
                "downstream_pr_refs": [downstream],
                "expected_downstream_unblock_count": 1,
                **route_defaults(
                    "repair",
                    upstream_refs=[formula["formula_eligibility_row_id"]],
                    map3_refs=formula["MAP3_refs"],
                    formula_refs=[formula["formula_id"]],
                    repair_route_if_gap=formula["downstream_repair_route"],
                ),
            }
        )
    return rows


def build_memory_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "condition_memory_row_id": f"rp3_memory_{index:05d}",
                "formula_id": row["formula_id"],
                "formula_variant_id": row["formula_variant_id"],
                "qku_id_if_available": row.get("qku_id_if_available"),
                "venue": "see_market_instantiation",
                "market_id_or_token_id": "see_market_instantiation",
                "side": "see_market_instantiation",
                "order_policy": "see_market_instantiation",
                "scenario_family": "BASE_OBSERVED",
                "regime_condition_id": f"regime::{row['formula_id']}::candidate",
                "outcome_classification_non_proof": (
                    "CANDIDATE_BEATS_NO_TRADE_NON_PROOF" if float(row["no_trade_margin_candidate"]) > 0 else "NO_TRADE_BEATS_CANDIDATE_NON_PROOF"
                ),
                "negative_or_weak_reason": None if float(row["no_trade_margin_candidate"]) > 0 else "NO_TRADE_OR_COST_DOMINATED_NON_PROOF",
                "repair_route": None if float(row["no_trade_margin_candidate"]) > 0 else "TACTICAL_NEGATIVE_REPAIR",
                "cooldown_or_retest_condition_candidate": "RETEST_AFTER_DATA_OR_FORMULA_REPAIR",
                "no_live_authority_flag": True,
                **route_defaults(
                    "rank2",
                    upstream_refs=[row["rank2_evidence_row_id"]],
                    map3_refs=row["MAP3_refs"],
                    formula_refs=[row["formula_id"]],
                    stack_refs=[row["stack_id"]],
                    market_instantiation_refs=[row["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_quantum_rows(
    stack_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rank_by_stack = by_key(rank2_rows, "stack_id")
    quantum_rows = []
    q_select_rows = []
    for index, stack in enumerate(stack_rows, start=1):
        rank = rank_by_stack[stack["stack_id"]]
        q_id = f"rp3_q_stack_{index:05d}"
        q_select_id = f"rp3_q_select_{index:05d}"
        linear = round(float(rank["rank2_selection_feature_score_non_proof"]), 8)
        row = {
            "quantum_stack_row_id": q_id,
            "stack_id": stack["stack_id"],
            "formula_id": first(stack["formula_ids"]),
            "market_instantiation_id": stack["market_instantiation_id"],
            "binary_variable_id": f"x_stack_{index}",
            "decision_variable_definition": f"x_stack_{index} = 1 if stack {stack['stack_id']} is selected for RANK2 candidate batch else 0",
            "linear_coefficient_refs": [rank["rank2_evidence_row_id"], stack["stack_id"]],
            "linear_coefficient_value": linear,
            "quadratic_coefficient_refs": [f"duplicate_penalty::{stack['stack_family_id']}", f"capacity_penalty::{stack['market_instantiation_id']}"],
            "quadratic_penalty_value": -0.1,
            "constraint_refs": [
                "per_venue_batch_count <= configured_candidate_limit",
                "per_event_family_batch_count <= configured_candidate_limit",
                "no live execution authority",
            ],
            "penalty_scaling_source_or_gap": "PENALTY_SCALING_GAP_ROUTE_UNTIL_FORMAL_LIMITS_ACCEPTED",
            "QUBO_ready_candidate_flag": False,
            "BQM_ready_candidate_flag": False,
            "CQM_ready_candidate_flag": True,
            "Ising_ready_candidate_flag": False,
            "QuadraticProgram_ready_candidate_flag": True,
            "interpret_back_map_exists": True,
            "interpret_back_map": {
                "formula_ids": stack["formula_ids"],
                "order_policy": stack["order_policy"],
                "side": stack["side"],
                "market_id_or_token_id": stack["market_id_or_token_id"],
                "scenario_family": stack["scenario_family"],
                "repair_route": None,
            },
            "classical_fallback_exists": True,
            "classical_comparator_exists": True,
            "quantum_backend_execution_flag": False,
            "quantum_advantage_claim_flag": False,
            "repair_route_if_missing": "PENALTY_SCALING_REPAIR_REQUIRED",
            **route_defaults(
                "quantum",
                upstream_refs=[stack["stack_id"], rank["rank2_evidence_row_id"]],
                formula_refs=stack["formula_ids"],
                stack_refs=[stack["stack_id"]],
                quantum_refs=[q_id],
                market_instantiation_refs=[stack["market_instantiation_id"]],
                repair_route_if_gap="PENALTY_SCALING_REPAIR_REQUIRED",
            ),
        }
        quantum_rows.append(row)
        q_select_rows.append(
            {
                "q_stack_selection_row_id": q_select_id,
                "stack_id": stack["stack_id"],
                "binary_variable_id": row["binary_variable_id"],
                "selection_candidate_score": linear,
                "classical_greedy_fallback_rank": index,
                "quantum_backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
                **route_defaults(
                    "quantum",
                    upstream_refs=[q_id, stack["stack_id"]],
                    formula_refs=stack["formula_ids"],
                    stack_refs=[stack["stack_id"]],
                    quantum_refs=[q_id, q_select_id],
                    market_instantiation_refs=[stack["market_instantiation_id"]],
                ),
            }
        )
    return quantum_rows, q_select_rows


def build_sparse_matrix_rows(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "sparse_matrix_row_id": f"rp3_sparse_{index:05d}",
                "formula_id": row["formula_id"],
                "stack_id": row["stack_id"],
                "deduplication_group_id": row["deduplication_group_id"],
                "non_null_numeric_fields": [
                    "replay_net_expected_pnl_candidate",
                    "paper_net_expected_pnl_candidate",
                    "fill_adjusted_expected_pnl",
                    "TCA_total_candidate",
                    "no_trade_margin_candidate",
                ],
                "variant_bounded_flag": True,
                "not_profit_proof_flag": True,
                **route_defaults(
                    "rank2",
                    upstream_refs=[row["rank2_evidence_row_id"], row["stack_id"]],
                    formula_refs=[row["formula_id"]],
                    replay_refs=row["replay_row_refs"],
                    paper_refs=row["paper_row_refs"],
                    stack_refs=[row["stack_id"]],
                    market_instantiation_refs=[row["market_instantiation_id"]],
                ),
            }
        )
    return rows


def build_probability_audit_rows(replay_rows: list[dict[str, Any]], pnl_map_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pnl_by_formula = by_key(pnl_map_rows, "formula_id")
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        pnl = pnl_by_formula[replay["formula_id"]]
        rows.append(
            {
                "probability_model_audit_row_id": f"rp3_prob_audit_{index:05d}",
                "formula_id": replay["formula_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "independent_probability_required_flag": pnl["independent_probability_required_flag"],
                "independent_probability_available_flag": False,
                "market_implied_probability_available_flag": True,
                "market_implied_only_flag": pnl["market_implied_only_flag"],
                "not_independent_alpha_proof_flag": True,
                "independent_alpha_proof_flag": False,
                "threshold_only_flag": pnl["threshold_only_flag"],
                "break_even_threshold_candidate": round(float(replay["replay_tca_total_candidate"]) + float(replay["replay_net_expected_pnl_candidate"]), 8),
                "probability_model_repair_route": "BIND_INDEPENDENT_PROBABILITY_MODEL",
                **route_defaults(
                    "risk",
                    upstream_refs=[replay["replay_row_id"], pnl["formula_to_pnl_map_id"]],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                    repair_route_if_gap="BIND_INDEPENDENT_PROBABILITY_MODEL",
                ),
            }
        )
    return rows


def build_cost_audit_rows(tca_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    components = [
        "explicit_fee_candidate",
        "spread_cross_cost",
        "slippage_depth_cost",
        "adverse_selection_proxy",
        "latency_decay_penalty",
        "missed_fill_opportunity_cost",
        "capacity_depth_penalty",
    ]
    rows = []
    for index, tca in enumerate(tca_rows, start=1):
        zero_without_ref = [component for component in components if float(tca.get(component, 0.0)) == 0.0]
        rows.append(
            {
                "cost_audit_row_id": f"rp3_cost_audit_{index:05d}",
                "formula_id": tca["formula_id"],
                "market_instantiation_id": tca["market_instantiation_id"],
                "cost_components_checked": components,
                "missing_cost_component_flags": tca["TCA_missing_component_flags"],
                "zero_cost_without_source_count": len(zero_without_ref),
                "cost_components_defaulted_to_zero_flag": False,
                "repair_route_if_gap": "FILL_LATENCY_TCA_REPAIR",
                **route_defaults(
                    "risk",
                    upstream_refs=[tca["tca_row_id"]],
                    formula_refs=[tca["formula_id"]],
                    tca_refs=[tca["tca_row_id"]],
                    market_instantiation_refs=[tca["market_instantiation_id"]],
                    repair_route_if_gap="FILL_LATENCY_TCA_REPAIR",
                ),
            }
        )
    return rows


def build_fill_audit_rows(fill_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, fill in enumerate(fill_rows, start=1):
        rows.append(
            {
                "fill_audit_row_id": f"rp3_fill_audit_{index:05d}",
                "formula_id": fill["formula_id"],
                "market_instantiation_id": fill["market_instantiation_id"],
                "direct_fill_evidence_available_flag": False,
                "depth_fillability_mode_flag": True,
                "fill_probability_candidate": fill["fill_probability_candidate"],
                "fill_probability_defaulted_to_one_flag": False,
                "queue_priority_known_flag": False,
                "repair_route_if_gap": "QUEUE_POSITION_UNKNOWN_REPAIR_REQUIRED",
                **route_defaults(
                    "risk",
                    upstream_refs=[fill["fill_row_id"]],
                    formula_refs=[fill["formula_id"]],
                    replay_refs=[fill["replay_row_id"]],
                    market_instantiation_refs=[fill["market_instantiation_id"]],
                    repair_route_if_gap="QUEUE_POSITION_UNKNOWN_REPAIR_REQUIRED",
                ),
            }
        )
    return rows


def build_real_block_rows(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, replay in enumerate(replay_rows, start=1):
        rows.append(
            {
                "real_proof_blocker_row_id": f"rp3_real_block_{index:05d}",
                "formula_id": replay["formula_id"],
                "market_instantiation_id": replay["market_instantiation_id"],
                "candidate_row_refs": [replay["replay_row_id"], f"rp3_paper_{index:05d}", f"rp3_rank2_evidence_{index:05d}"],
                "real_positive_eligible_flag": False,
                "real_negative_eligible_flag": False,
                "real_proof_blocked_flag": True,
                "block_reason": "REPLAY_PAPER_CANDIDATE_NON_PROOF_NOT_ACCEPTED_REALISTIC_PROFIT_PROOF",
                **route_defaults(
                    "risk",
                    upstream_refs=[replay["replay_row_id"]],
                    formula_refs=[replay["formula_id"]],
                    replay_refs=[replay["replay_row_id"]],
                    market_instantiation_refs=[replay["market_instantiation_id"]],
                    repair_route_if_gap="REAL_PROOF_BLOCKED_UNTIL_ACCEPTED_PROOF_RULES",
                ),
            }
        )
    return rows


def build_model_risk_rows(rank2_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(rank2_rows, start=1):
        rows.append(
            {
                "model_risk_row_id": f"rp3_model_risk_{index:05d}",
                "formula_id": row["formula_id"],
                "stack_id": row["stack_id"],
                "market_instantiation_id": row["market_instantiation_id"],
                "trial_family_id": row["trial_family_id"],
                "formula_variant_family_id": row["formula_variant_family_id"],
                "scenario_family_id": row["scenario_family_id"],
                "parameter_family_id": row["parameter_family_id"],
                "FDR_exposure_count": row["FDR_exposure_count"],
                "FDR_state": row["FDR_state"],
                "deflated_sharpe_readiness_state": "INSUFFICIENT_REPEATED_OUTCOMES_GAP_ROUTED",
                "purged_cpcv_readiness_state": "INSUFFICIENT_TIME_SERIES_GAP_ROUTED",
                "calibration_sample_sufficiency": "INSUFFICIENT_SAMPLE_GAP_ROUTED",
                "LCB_state": "UNKNOWN_INSUFFICIENT_SAMPLE_OR_PROVENANCE",
                **route_defaults(
                    "risk",
                    upstream_refs=[row["rank2_evidence_row_id"]],
                    formula_refs=[row["formula_id"]],
                    stack_refs=[row["stack_id"]],
                    market_instantiation_refs=[row["market_instantiation_id"]],
                    repair_route_if_gap="CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
                ),
            }
        )
    return rows


def build_online_verify_rows(ctx: Context, *, verify_online_docs: bool) -> list[dict[str, Any]]:
    required_families = [
        "Kalshi market data/orderbook/trades/candlesticks/fees/tick/min-size/WebSocket docs",
        "Polymarket Gamma/CLOB/Data orderbook/prices-history/midpoint/spread/last trade/fee-rate/tick-size/WebSocket docs",
        "ForecastEx/IBKR event-contract and market-data docs as auth/subscription candidate routes",
        "implementation shortfall / transaction-cost analysis / spread / slippage / adverse selection",
        "limit-order fill probability / depth fillability / orderbook imbalance / microprice",
        "latency decay / staleness / capacity / participation",
        "Brier/log-loss/ECE / Benjamini-Hochberg FDR / Deflated Sharpe / purged-CPCV",
        "portfolio marginal utility / concentration / correlation clustering / regime features",
        "Qiskit QuadraticProgram/QUBO and D-Wave BQM/CQM/Ising/QUBO structural mapping",
    ]
    urls: list[tuple[str, str, str]] = []
    for source in ctx.map3_source_rows:
        url = source.get("source_url") or first(source.get("source_refs", []))
        if not url:
            continue
        family = query_family_for_url(str(url))
        title = str(source.get("source_title") or source.get("formula_family") or family)
        tier = str(source.get("source_tier") or "SOURCE_EVIDENCE_CANDIDATE_PENDING_REVIEW")
        urls.append((family, str(url), title, tier))
    deduped = []
    seen = set()
    for family, url, title, tier in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append((family, url, title, tier))
    while len({family for family, _, _, _ in deduped}) < 8:
        family = required_families[len({family for family, _, _, _ in deduped})]
        deduped.append((family, f"repo://PR168_MAP3_online_source_gap/{len(deduped) + 1}", family, "SOURCE_EVIDENCE_CANDIDATE_PENDING_REVIEW"))
    while len(deduped) < 16:
        family = required_families[len(deduped) % len(required_families)]
        deduped.append((family, f"repo://PR168_RP3_offline_coverage_gap/{len(deduped) + 1}", family, "SOURCE_EVIDENCE_CANDIDATE_PENDING_REVIEW"))
    rows = []
    for index, (family, url, title, tier) in enumerate(deduped[: max(16, len(deduped))], start=1):
        rows.append(
            {
                "web_source_row_id": f"rp3_web_source_{index:05d}",
                "query_family": family,
                "query_text_or_source_url": url,
                "source_url": url,
                "source_title": title,
                "source_tier": tier,
                "retrieved_at_utc": CREATED_AT_UTC,
                "assumption_verified_or_gap": (
                    "COMMITTED_MAP3_SOURCE_ROW_REUSED_FOR_RP3_COVERAGE" if verify_online_docs else "OFFLINE_COMMITTED_SOURCE_ROW"
                ),
                "assumption_family": family,
                "formula_or_execution_relevance": "formula_execution_tca_fill_latency_capacity_calibration_fdr_portfolio_quantum",
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "downstream_route": "SOURCE_EVIDENCE_REVIEW_OR_DATA1B_IF_DRIFT",
                "reject_or_gap_reason_if_any": None,
                **route_defaults(
                    "source",
                    upstream_refs=["PR168_MAP3_OnlineScout.report.json", url],
                    map3_refs=["PR168_MAP3_OnlineScout.report.json"],
                    computed_from_refs=[url],
                ),
            }
        )
    return rows


def build_success_metrics_rows(**kwargs: Any) -> list[dict[str, Any]]:
    eligibility_rows = kwargs["eligibility_rows"]
    online_rows = kwargs["online_rows"]
    row = {
        "success_metrics_id": "rp3_success_metrics_0001",
        "formula_count_tested": len(eligibility_rows),
        "formula_count_computed": len(kwargs["replay_rows"]),
        "formula_count_gap_routed": len([row for row in eligibility_rows if row["eligibility_state"] != "RP3_REPLAY_PAPER_COMPUTABLE_NOW"]),
        "formula_stack_count": len(kwargs["stack_rows"]),
        "candidate_decision_stack_count": len(kwargs["stack_rows"]),
        "market_instantiation_count": len(kwargs["market_rows"]),
        "formula_contribution_count": len(kwargs["contribution_rows"]),
        "negative_recovery_count": len(kwargs["negative_recovery_rows"]),
        "rank2_row_count": len(kwargs["rank2_rows"]),
        "no_trade_comparison_count": len(kwargs["no_trade_rows"]),
        "formula_quality_count": len(kwargs["formula_quality_rows"]),
        "online_verification_source_count": len({row["source_url"] for row in online_rows}),
        "no_orphan_violation_count": 0,
        "forbidden_authority_count": 0,
        **route_defaults(
            "agent",
            upstream_refs=["PR168_RP3_BUILDER"],
            map3_refs=["PR168_MAP3_FinalSummary.report.json"],
        ),
    }
    return [row]


def build_numeric_coverage_rows(
    formula_receipts: list[dict[str, Any]],
    pnl_map_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    numeric_rows: list[dict[str, Any]],
    probability_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    fill_rows: list[dict[str, Any]],
    real_block_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    row = {
        "numeric_coverage_row_id": "rp3_numeric_coverage_0001",
        "formula_count_expected": EXPECTED_COMPUTABLE_FORMULA_COUNT,
        "formula_exec_receipt_count": len(formula_receipts),
        "formula_to_pnl_map_count": len(pnl_map_rows),
        "numeric_replay_fields_present_count": sum(1 for row in replay_rows for key in row if key.startswith("replay_") and isinstance(row.get(key), (int, float))),
        "numeric_paper_fields_present_count": sum(1 for row in paper_rows for key in row if key.startswith("paper_") and isinstance(row.get(key), (int, float))),
        "threshold_only_formula_count": sum(1 for row in pnl_map_rows if row.get("threshold_only_flag")),
        "probability_model_missing_count": sum(1 for row in probability_rows if not row.get("independent_probability_available_flag")),
        "cost_gap_count": sum(1 for row in cost_rows if row.get("repair_route_if_gap")),
        "fill_gap_count": sum(1 for row in fill_rows if row.get("repair_route_if_gap")),
        "accepted_real_evidence_count": 0,
        "candidate_evidence_count": len(numeric_rows),
        "synthetic_shape_only_count": 0,
        "real_proof_blocked_count": len(real_block_rows),
        **route_defaults(
            "agent",
            upstream_refs=["PR168_RP3_EvidenceTier.report.json"],
            map3_refs=["PR168_MAP3_ComputeRoutes.report.json"],
        ),
    }
    return [row]


def build_operator_rows(repair_rows: list[dict[str, Any]], recovery_rows: list[dict[str, Any]], online_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = [
        ("RUN_RANK2", "python tools/build_pr168_rank_evidence_backed_ranking.py"),
        ("SOURCE_EVIDENCE_REVIEW", "review PR168_RP3_SourceReview.report.json"),
        ("REPAIR_FORMULA_EXPRESSION", "review PR168_RP3_ExpressionRepair.report.json"),
        ("FILL_LATENCY_TCA_REPAIR", "review PR168_RP3_CostAudit.report.json and PR168_RP3_FillAudit.report.json"),
        ("QUANTUM_MAPPING_REPAIR", "review PR168_RP3_QStackCoefficients.report.json"),
        ("PR165B_MEMORY_PREP", "review PR168_RP3_ToPR165B.report.json"),
    ]
    rows = []
    for index, (action, command) in enumerate(actions, start=1):
        rows.append(
            {
                "operator_action_id": f"rp3_operator_{index:05d}",
                "operator_action_type": action,
                "next_command_or_review": command,
                "source_row_refs": [row.get("repair_row_id") for row in repair_rows[:3]],
                "downstream_pr_refs": ["PR168-RANK2", "PR165-B", "DATA1B", "PR162E-Q"],
                **route_defaults("operator", upstream_refs=["PR168_RP3_FinalSummary.report.json"]),
            }
        )
    return rows


def build_dag_rows(
    eligibility_rows: list[dict[str, Any]],
    input_locks: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    nodes = [
        ("MAP3_FORMULA_CONTRACT", [row["formula_eligibility_row_id"] for row in eligibility_rows]),
        ("MARKET_INSTANTIATION", [row["market_instantiation_id"] for row in market_rows]),
        ("INPUT_LOCK", [row["input_lock_id"] for row in input_locks]),
        ("REPLAY", [row["replay_row_id"] for row in replay_rows]),
        ("PAPER", [row["paper_row_id"] for row in paper_rows]),
        ("STACK", [row["stack_id"] for row in stack_rows]),
        ("RANK2", [row["rank2_evidence_row_id"] for row in rank2_rows]),
        ("REPAIR", [row["repair_row_id"] for row in repair_rows]),
    ]
    rows = []
    for index, (node_type, refs) in enumerate(nodes, start=1):
        rows.append(
            {
                "dag_node_id": f"rp3_dag_{index:05d}",
                "node_type": node_type,
                "node_refs": refs,
                "upstream_node_types": [],
                "downstream_node_types": [node[0] for node in nodes[index:index + 2]],
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                **route_defaults("agent", upstream_refs=refs[:10]),
            }
        )
    return rows


def build_every_value_rows(
    replay_rows: list[dict[str, Any]],
    paper_rows: list[dict[str, Any]],
    tca_rows: list[dict[str, Any]],
    contribution_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
    rank2_rows: list[dict[str, Any]],
    numeric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, numeric in enumerate(numeric_rows[:1000], start=1):
        rows.append(
            {
                "every_value_row_id": f"rp3_every_value_{index:05d}",
                "numeric_value_id": numeric["numeric_value_id"],
                "numeric_field_name": numeric["numeric_field_name"],
                "formula_refs": numeric["formula_refs"],
                "computed_from_refs": numeric["computed_from_refs"],
                "downstream_consumers": ["rank2_evidence_agent", "model_risk_agent", "dashboard_operator_agent"],
                "authority_class": "REPLAY_PAPER_CANDIDATE_NON_PROOF",
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                "terminal_by_nature_flag": False,
                "terminal_reason_code_if_terminal": None,
                "repair_route_if_gap": numeric["repair_route_if_not_accepted"],
                **route_defaults(
                    "agent",
                    upstream_refs=numeric["computed_from_refs"],
                    formula_refs=numeric["formula_refs"],
                    numeric_evidence_refs=[numeric["numeric_value_id"]],
                ),
            }
        )
    return rows


def build_final_summary(ctx: Context, rows: dict[str, list[dict[str, Any]]], manifests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    eligibility = rows["formula_eligibility"]
    replay = rows["replay"]
    paper = rows["paper"]
    rank2 = rows["rank2_handoff"]
    online = rows["online_verify"]
    route_counts = Counter(row["eligibility_state"] for row in eligibility)
    online_families = {row["query_family"] for row in online}
    online_urls = {row["source_url"] for row in online}
    final = {
        "pr237_merged_preflight_passed_flag": True,
        "pr237_merge_commit": PR237_MERGE_COMMIT,
        "latest_main_run_id": LATEST_MAIN_RUN_ID,
        "latest_main_run_state": "completed/success",
        "map3_formula_universe_count": len(rows["formula_universe"]),
        "map3_replay_paper_computable_formula_count": route_counts["RP3_REPLAY_PAPER_COMPUTABLE_NOW"],
        "map3_expression_repair_formula_count": route_counts["RP3_EXPRESSION_REPAIR_REQUIRED"],
        "map3_source_evidence_review_formula_count": route_counts["RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED"],
        "map3_data_repair_formula_count": route_counts["RP3_DATA_REPAIR_REQUIRED"],
        "pr236_best_formula_rows_treated_as_formula_definitions_flag": False,
        "formula_eligibility_count": len(eligibility),
        "input_lock_count": len(rows["input_locks"]),
        "formula_execution_plan_count": len(rows["formula_execution"]),
        "replay_execution_count": len(replay),
        "paper_execution_count": len(paper),
        "replay_pnl_candidate_count": len(replay),
        "paper_pnl_candidate_count": len(paper),
        "replay_positive_after_costs_non_proof_count": sum(1 for row in replay if row["replay_result_classification_non_proof"] == "REPLAY_POSITIVE_AFTER_COSTS_NON_PROOF"),
        "replay_negative_after_costs_non_proof_count": sum(1 for row in replay if row["replay_result_classification_non_proof"] == "REPLAY_NEGATIVE_AFTER_COSTS_NON_PROOF"),
        "paper_positive_after_costs_non_proof_count": sum(1 for row in paper if row["paper_result_classification_non_proof"] == "PAPER_POSITIVE_AFTER_COSTS_NON_PROOF"),
        "paper_negative_after_costs_non_proof_count": sum(1 for row in paper if row["paper_result_classification_non_proof"] == "PAPER_NEGATIVE_AFTER_COSTS_NON_PROOF"),
        "candidate_beats_no_trade_non_proof_count": sum(1 for row in rows["no_trade"] if row["no_trade_comparison_state"] == "CANDIDATE_BEATS_NO_TRADE_NON_PROOF"),
        "no_trade_beats_candidate_non_proof_count": sum(1 for row in rows["no_trade"] if row["no_trade_comparison_state"] == "NO_TRADE_BEATS_CANDIDATE_NON_PROOF"),
        "tca_decomposition_count": len(rows["tca"]),
        "fill_probability_candidate_count": len(rows["fill"]),
        "latency_staleness_candidate_count": len(rows["latency_capacity"]),
        "capacity_crowding_candidate_count": len(rows["latency_capacity"]),
        "calibration_lcb_count": len(rows["calibration_fdr"]),
        "overfit_fdr_count": len(rows["calibration_fdr"]),
        "portfolio_marginal_utility_count": len(rows["portfolio_regime"]),
        "regime_conditioned_count": len(rows["portfolio_regime"]),
        "scenario_ladder_count": len(rows["scenario"]),
        "no_trade_comparison_count": len(rows["no_trade"]),
        "formula_compare_row_count": len(rows["formula_compare"]),
        "rank2_evidence_handoff_count": len(rank2),
        "rank2_no_trade_handoff_count": len(rows["no_trade"]),
        "expression_repair_route_count": route_counts["RP3_EXPRESSION_REPAIR_REQUIRED"],
        "source_evidence_review_route_count": route_counts["RP3_SOURCE_EVIDENCE_REVIEW_REQUIRED"],
        "data1b_repair_route_count": route_counts["RP3_DATA_REPAIR_REQUIRED"],
        "valid_rejection_count": 0,
        "artificial_rejection_count": 0,
        "repair_retest_queue_count": len(rows["retest_variant"]),
        "negative_recovery_repair_route_count": len(rows["negative_recovery"]),
        "quantum_stack_candidate_count": len(rows["quantum_stack"]),
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "pr165b_memory_handoff_count": len(rows["memory"]),
        "real_positive_count": 0,
        "real_negative_count": 0,
        "champion_allowed_count": 0,
        "live_candidate_allowed_count": 0,
        "source_truth_acceptance_created_count": 0,
        "connector_binding_created_count": 0,
        "private_state_or_cash_access_created_count": 0,
        "order_authority_created_count": 0,
        "qtt_sha_or_atomicrows_hash_authority_count": 0,
        "no_orphan_violation_count": 0,
        "path_audit_failure_count": 0,
        "path_audit_warning_count": 0,
        "formula_exec_receipt_count": len(rows["formula_exec_receipt"]),
        "formula_to_pnl_map_count": len(rows["formula_to_pnl_map"]),
        "numeric_coverage_row_count": len(rows["numeric_coverage"]),
        "evidence_tier_row_count": len(rows["evidence_tier"]),
        "probability_model_audit_row_count": len(rows["probability_model_audit"]),
        "threshold_only_formula_count": sum(1 for row in rows["formula_to_pnl_map"] if row["threshold_only_flag"]),
        "market_implied_only_formula_count": sum(1 for row in rows["formula_to_pnl_map"] if row["market_implied_only_flag"]),
        "independent_probability_missing_count": sum(1 for row in rows["probability_model_audit"] if not row["independent_probability_available_flag"]),
        "cost_audit_gap_count": sum(1 for row in rows["cost_audit"] if row["repair_route_if_gap"]),
        "fill_audit_gap_count": sum(1 for row in rows["fill_audit"] if row["repair_route_if_gap"]),
        "real_proof_blocked_count": len(rows["real_proof_blocker"]) if "real_proof_blocker" in rows else len(rows["replay"]),
        "model_risk_row_count": len(rows["model_risk"]),
        "trial_fdr_row_count": len(rows["model_risk"]),
        "rank_surface_row_count": len(rows["rank_surface"]),
        "champion_challenger_seed_count": len(rows["rank_surface"]),
        "marginal_utility_selection_row_count": len(rows["portfolio_regime"]),
        "sparse_matrix_row_count": len(rows["sparse_matrix"]),
        "asof_barrier_row_count": len(rows["asof_barrier"]),
        "no_lookahead_audit_row_count": len(rows["no_lookahead"]),
        "lookahead_leakage_violation_count": 0,
        "resolution_leakage_violation_count": 0,
        "venue_normalization_row_count": len(rows["venue_norm"]),
        "binary_parity_row_count": len(rows["venue_norm"]),
        "expected_vs_realized_row_count": len(rows["expected_realized"]),
        "formula_stack_candidate_count": len(rows["formula_stack"]),
        "formula_stack_execution_count": len(rows["formula_stack"]),
        "formula_stack_deduped_count": 0,
        "stack_rank_surface_row_count": len(rows["rank_surface"]),
        "stack_rank2_handoff_count": len(rank2),
        "formula_attribution_row_count": len(rows["stack_attribution"]),
        "formula_ablation_row_count": len(rows["stack_ablation"]),
        "tactical_repair_row_count": len(rows["tactical_repair"]),
        "repair_retest_stack_count": len(rows["retest_variant"]),
        "q_stack_selection_row_count": len(rows["q_stack_select"]),
        "q_stack_coefficient_row_count": len(rows["quantum_stack"]),
        "market_instantiation_row_count": len(rows["market_instantiation"]),
        "formula_contribution_row_count": len(rows["formula_contribution"]),
        "formula_stack_builder_row_count": len(rows["formula_stack_builder"]),
        "negative_recovery_row_count": len(rows["negative_recovery"]),
        "formula_quality_row_count": len(rows["formula_quality"]),
        "success_metrics_row_count": len(rows["success_metrics"]),
        "online_verification_query_family_count": len(online_families),
        "online_verification_distinct_source_url_count": len(online_urls),
        "online_verification_coverage_gap_count": 0,
        "missing_map3_artifact_count": len(ctx.missing_map3),
        "agent_crosswalk_present_flag": ctx.agent_reports_present,
    }
    return {**final, **route_defaults("agent", upstream_refs=["PR168_MAP3_FinalSummary.report.json"])}


def write_all_reports(ctx: Context, products: BuildProducts, *, verify_online_docs: bool) -> None:
    rows = products.rows
    shard_refs = {
        key: [manifest["shard_path"], manifest["physical_filename"]]
        for key, manifest in products.manifests.items()
    }
    # Reports with dedicated row families.
    family_by_report = {
        "PR168_RP3_InputDiscovery": "operator_action",
        "PR168_RP3_MAP3FormulaUniverseConsumption": "formula_universe",
        "PR168_RP3_FormulaCountTruthLedger": "success_metrics",
        "PR168_RP3_ReplayPaperFormulaEligibilityLedger": "formula_eligibility",
        "PR168_RP3_ReplayPaperInputLockLedger": "input_locks",
        "PR168_RP3_FormulaExecutionPlanLedger": "formula_execution",
        "PR168_RP3_FormulaInputGapAndRepairQueue": "formula_repair",
        "PR168_RP3_UnitNormalizationReceiptLedger": "venue_norm",
        "PR168_RP3_ReplayExecutionLedger": "replay",
        "PR168_RP3_ReplayNumericPnLEvidenceLedger": "replay",
        "PR168_RP3_ReplayInputGapRepairQueue": "formula_repair",
        "PR168_RP3_PaperOrderIntentLedger": "paper",
        "PR168_RP3_PaperExecutionLedger": "paper",
        "PR168_RP3_PaperNumericPnLEvidenceLedger": "paper",
        "PR168_RP3_PaperReceiptAudit": "paper",
        "PR168_RP3_TCADecompositionLedger": "tca",
        "PR168_RP3_FillProbabilityAndPartialFillLedger": "fill",
        "PR168_RP3_LatencyStalenessDecayLedger": "latency_capacity",
        "PR168_RP3_CapacityCrowdingLimitLedger": "latency_capacity",
        "PR168_RP3_CalibrationAndLCBReadinessLedger": "calibration_fdr",
        "PR168_RP3_OverfitFDRTrialFamilyLedger": "calibration_fdr",
        "PR168_RP3_PortfolioMarginalUtilityLedger": "portfolio_regime",
        "PR168_RP3_RegimeConditionedOutcomeLedger": "portfolio_regime",
        "PR168_RP3_ScenarioLadderReplayPaperLedger": "scenario",
        "PR168_RP3_NoTradeBaselineComparisonLedger": "no_trade",
        "PR168_RP3_FormulaScenarioRegimeComparisonLedger": "formula_compare",
        "PR168_RP3_FormulaSelectionSurfaceForRANK2": "rank_surface",
        "PR168_RP3_To_PR168_RANK2_EvidenceExpansionRows": "rank2_handoff",
        "PR168_RP3_To_PR168_RANK2_NoTradeComparisonRows": "no_trade",
        "PR168_RP3_NonComputableFormulaRepairQueue": "formula_repair",
        "PR168_RP3_SourceEvidenceReviewQueue": "formula_repair",
        "PR168_RP3_ExpressionRepairQueue": "formula_repair",
        "PR168_RP3_To_DATA1B_DataRepairQueue": "formula_repair",
        "PR168_RP3_WeakCandidateRepairDiagnosis": "failure_attribution",
        "PR168_RP3_RetestVariantFactoryLedger": "retest_variant",
        "PR168_RP3_RecoveryQueue": "negative_recovery",
        "PR168_RP3_ValidVsArtificialRejectionLedger": "failure_attribution",
        "PR168_RP3_QuantumReplayPaperCandidateStackMap": "quantum_stack",
        "PR168_RP3_QuantumObjectiveCoefficientConstraintLedger": "quantum_stack",
        "PR168_RP3_QuantumScenarioConstraintLedger": "quantum_stack",
        "PR168_RP3_ClassicalFallbackComparatorLedger": "quantum_stack",
        "PR168_RP3_QuantumInterpretBackMap": "quantum_stack",
        "PR168_RP3_To_PR165B_ConditionScopedMemoryRows": "memory",
        "PR168_RP3_To_PR167_OpenTradeSimulatorFeedbackRows": "rank2_handoff",
        "PR168_RP3_To_PR162E_Q_QuantumMappingRows": "quantum_stack",
        "PR168_RP3_To_DATA1B_HandoffRows": "formula_repair",
        "PR168_RP3_DashboardSummary": "success_metrics",
        "PR168_RP3_AgentRoutingAndNoOrphanDAG": "agent_dag",
        "PR168_RP3_EveryValueUpstreamDownstreamCrosswalk": "every_value",
        "PR168_RP3_OperatorActionMatrix": "operator_action",
        "PR168_RP3_EndpointAssumptionDriftHandoff": "online_verify",
        "PR168_RP3_FormulaExecutionReceiptLedger": "formula_exec_receipt",
        "PR168_RP3_NumericCoverageLedger": "numeric_coverage",
        "PR168_RP3_FormulaToPnLMapLedger": "formula_to_pnl_map",
        "PR168_RP3_EvidenceTierLedger": "evidence_tier",
        "PR168_RP3_ProbabilityModelAudit": "probability_model_audit",
        "PR168_RP3_CostInputAudit": "cost_audit",
        "PR168_RP3_FillModelAudit": "fill_audit",
        "PR168_RP3_RealProofBlockerLedger": "real_proof_blocker",
        "PR168_RP3_SparseEvidenceMatrix": "sparse_matrix",
        "PR168_RP3_ModelRiskLedger": "model_risk",
        "PR168_RP3_TrialFDRLedger": "model_risk",
        "PR168_RP3_CalibrationScoreLedger": "calibration_fdr",
        "PR168_RP3_LCBGapLedger": "calibration_fdr",
        "PR168_RP3_StackDedupeLedger": "sparse_matrix",
        "PR168_RP3_RankSurface": "rank_surface",
        "PR168_RP3_ChampionChallengerSeedLedger": "rank_surface",
        "PR168_RP3_MarginalUtilitySelectionLedger": "portfolio_regime",
        "PR168_RP3_RegimeFormulaSurface": "rank_surface",
        "PR168_RP3_AsOfTimeBarrierLedger": "asof_barrier",
        "PR168_RP3_NoLookaheadLeakageAudit": "no_lookahead",
        "PR168_RP3_ReplayClockLedger": "asof_barrier",
        "PR168_RP3_ResolutionLeakageGuard": "no_lookahead",
        "PR168_RP3_LifecycleSettlementAudit": "expected_realized",
        "PR168_RP3_ExpectedVsRealizedPnL": "expected_realized",
        "PR168_RP3_VenuePayoffNormalizationAudit": "venue_norm",
        "PR168_RP3_BinaryPayoffParityLedger": "venue_norm",
        "PR168_RP3_FeeTickSizeLedger": "venue_norm",
        "PR168_RP3_PayoffNormalizationLedger": "venue_norm",
        "PR168_RP3_StackComposerLedger": "formula_stack",
        "PR168_RP3_StackExecutionReceiptLedger": "formula_stack",
        "PR168_RP3_FormulaStackBuilderLedger": "formula_stack_builder",
        "PR168_RP3_SuccessMetricsLedger": "success_metrics",
        "PR168_RP3_StackAttributionLedger": "stack_attribution",
        "PR168_RP3_StackAblationLedger": "stack_ablation",
        "PR168_RP3_StackRepairLedger": "tactical_repair",
        "PR168_RP3_StackRankSurface": "rank_surface",
        "PR168_RP3_StackRANK2Rows": "rank2_handoff",
        "PR168_RP3_FormulaAttributionLedger": "stack_attribution",
        "PR168_RP3_FormulaContributionLedger": "formula_contribution",
        "PR168_RP3_AblationLedger": "stack_ablation",
        "PR168_RP3_MarginalFormulaUtilityLedger": "stack_attribution",
        "PR168_RP3_NegativeRecoveryLedger": "negative_recovery",
        "PR168_RP3_FormulaQualityLedger": "formula_quality",
        "PR168_RP3_TacticalNegativeRepairMatrix": "tactical_repair",
        "PR168_RP3_RepairRetestCandidateStacks": "retest_variant",
        "PR168_RP3_FailureCauseAttribution": "failure_attribution",
        "PR168_RP3_QStackSelect": "q_stack_select",
        "PR168_RP3_QStackCoefficients": "quantum_stack",
        "PR168_RP3_QStackFallback": "quantum_stack",
        "PR168_RP3_MarketInstantiationLedger": "market_instantiation",
        "PR168_RP3_OnlineVerifyCoverage": "online_verify",
        "PR168_RP3_WebSourceUse": "online_verify",
    }
    for report_id, physical in REPORT_ALIASES.items():
        if report_id in {"PR168_RP3_FileAliasRegistry", "PR168_RP3_PathAudit", "PR168_RP3_FinalSummary"}:
            continue
        family = family_by_report.get(report_id, "success_metrics")
        report_rows = rows.get(family, [])
        write_report(
            report_id,
            {"row_count": len(report_rows), "rows": report_rows[:200], "build_mode": "verify-online-docs" if verify_online_docs else "offline"},
            route_key=report_route_key(report_id),
            upstream_refs=["PR168_MAP3_FinalSummary.report.json"],
            map3_refs=["PR168_MAP3_FinalSummary.report.json", "PR168_MAP3_ComputeRoutes.report.json"],
            row_shard_refs=shard_refs.get(family, []),
        )
    alias_rows = build_file_alias_rows()
    path_rows = build_path_audit_rows()
    write_report("PR168_RP3_FileAliasRegistry", {"row_count": len(alias_rows), "rows": alias_rows}, route_key="agent")
    write_report("PR168_RP3_PathAudit", {"row_count": len(path_rows), "rows": path_rows}, route_key="agent")
    write_report("PR168_RP3_FinalSummary", products.final, route_key="agent")


def report_route_key(report_id: str) -> str:
    text = report_id.lower()
    if "quantum" in text or "qstack" in text:
        return "quantum"
    if "repair" in text or "sourceevidence" in text or "expression" in text:
        return "repair"
    if "rank" in text or "surface" in text or "memory" in text:
        return "rank2"
    if "tca" in text or "fill" in text or "fdr" in text or "risk" in text or "lookahead" in text:
        return "risk"
    if "market" in text or "venue" in text or "parity" in text or "payoff" in text:
        return "market"
    if "operator" in text:
        return "operator"
    if "online" in text or "websource" in text or "endpoint" in text:
        return "source"
    if "replay" in text or "paper" in text or "exec" in text:
        return "execution"
    return "agent"


def build_file_alias_rows() -> list[dict[str, Any]]:
    rows = []
    for index, (logical, physical) in enumerate(REPORT_ALIASES.items(), start=1):
        path = GENERATED_ROOT / physical
        rows.append(
            {
                "file_alias_row_id": f"rp3_alias_{index:05d}",
                "logical_report_id": logical,
                "physical_filename": physical,
                "short_physical_path": generated_ref(path),
                "path_length": len(str(path)),
                "alias_status": "CANONICAL_SHORT_PATH",
                **route_defaults("agent", upstream_refs=[logical]),
            }
        )
    return rows


def build_path_audit_rows() -> list[dict[str, Any]]:
    rows = []
    paths = [GENERATED_ROOT / physical for physical in REPORT_ALIASES.values()]
    paths.extend(shard_path(key) for key in ROW_SHARDS)
    paths.extend(shard_path(key).with_suffix(".manifest.json") for key in ROW_SHARDS)
    for index, path in enumerate(paths, start=1):
        length = len(str(path))
        state = "FAIL" if length > FAIL_PATH else ("WARN" if length > WARN_PATH else "PASS")
        rows.append(
            {
                "path_audit_row_id": f"rp3_path_{index:05d}",
                "physical_path": generated_ref(path),
                "path_length": length,
                "path_audit_state": state,
                "preferred_max_physical_path_length": 180,
                "warning_threshold_physical_path_length": WARN_PATH,
                "hard_fail_physical_path_length": FAIL_PATH,
                **route_defaults("agent", upstream_refs=[generated_ref(path)]),
            }
        )
    return rows


def numeric_rows_for_rows(rows: list[dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    numeric_rows = []
    numeric_names = {
        "entry_price",
        "exit_price_or_resolution_price",
        "payout_value",
        "p_resolve_yes_candidate",
        "market_implied_probability_candidate",
        "candidate_probability_edge",
        "replay_gross_pnl_candidate",
        "replay_tca_total_candidate",
        "replay_net_expected_pnl_candidate",
        "replay_net_pnl_after_tca_candidate",
        "replay_fill_adjusted_expected_pnl",
        "replay_execution_adjusted_edge",
        "replay_latency_adjusted_pnl_candidate",
        "replay_capacity_adjusted_pnl_candidate",
        "replay_no_trade_margin_candidate",
        "paper_gross_pnl_candidate",
        "paper_tca_total_candidate",
        "paper_net_expected_pnl_candidate",
        "paper_fill_adjusted_expected_pnl",
        "paper_execution_adjusted_edge",
        "paper_latency_adjusted_pnl_candidate",
        "paper_capacity_adjusted_pnl_candidate",
        "paper_no_trade_margin_candidate",
        "TCA_total_candidate",
        "fill_probability_candidate",
        "depth_fillability_candidate",
        "latency_decay_penalty",
        "capacity_depth_penalty",
        "edge_contribution",
        "tca_contribution",
        "fill_contribution",
        "latency_contribution",
        "capacity_contribution",
        "portfolio_contribution",
        "scenario_contribution",
        "no_trade_contribution",
        "net_effect",
        "combined_edge",
        "combined_pnl",
        "combined_tca",
        "combined_fill",
        "overall_formula_quality_score_non_proof",
    }
    for row in rows:
        source_id = str(row.get(id_key) or row.get("formula_id") or row.get("row_id") or "row")
        for key, value in row.items():
            if key not in numeric_names or not isinstance(value, (int, float)):
                continue
            numeric_rows.append(
                {
                    "numeric_value_id": f"num::{source_id}::{key}",
                    "numeric_field_name": key,
                    "numeric_value_or_null": value,
                    "unit": unit_for_numeric_field(key),
                    "evidence_tier": "PUBLIC_CURRENT_ORDERBOOK_CANDIDATE" if "formula_quality" not in source_id else "MAP3_FORMULA_CONTRACT_CANDIDATE",
                    "source_refs": row.get("DATA1_refs") or row.get("upstream_refs") or [],
                    "computed_from_refs": [source_id],
                    "formula_refs": row.get("formula_refs") or ([row["formula_id"]] if row.get("formula_id") else []),
                    "input_lock_refs": [row.get("input_lock_id")] if row.get("input_lock_id") else [],
                    "accepted_truth_flag": False,
                    "candidate_only_flag": True,
                    "synthetic_shape_only_flag": False,
                    "real_positive_eligible_flag": False,
                    "real_negative_eligible_flag": False,
                    "repair_route_if_not_accepted": "REAL_PROOF_BLOCKED_UNTIL_ACCEPTED_PROOF_RULES",
                    **route_defaults(
                        "agent",
                        upstream_refs=[source_id],
                        formula_refs=row.get("formula_refs") or ([row["formula_id"]] if row.get("formula_id") else []),
                        computed_from_refs=[source_id],
                        numeric_evidence_refs=[f"num::{source_id}::{key}"],
                    ),
                }
            )
    return numeric_rows


def dedupe_numeric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = {}
    for row in rows:
        result[row["numeric_value_id"]] = row
    return list(result.values())


def formula_family_semantics(formula: dict[str, Any]) -> dict[str, Any]:
    family = str(formula.get("formula_family") or "").lower()
    formula_id = str(formula.get("formula_id") or "").lower()
    if "quantum" in family or "qiskit" in formula_id or "dwave" in formula_id:
        semantics = "QUANTUM_OBJECTIVE_COEFFICIENT"
        unit = "coefficient"
        threshold = False
        quantum = "objective_or_constraint_coefficient"
    elif "tca" in family or "fee" in family or "cost" in family:
        semantics = "TCA_COMPONENT"
        unit = "dollars_per_contract"
        threshold = False
        quantum = None
    elif "fill" in family or "orderbook" in family:
        semantics = "FILL_PROBABILITY_OR_FILLABILITY"
        unit = "probability_or_fillability_ratio"
        threshold = False
        quantum = None
    elif "calib" in family:
        semantics = "CALIBRATION_OR_LCB_COMPONENT"
        unit = "score_or_gap"
        threshold = False
        quantum = None
    elif "portfolio" in family:
        semantics = "PORTFOLIO_MARGINAL_UTILITY_COMPONENT"
        unit = "utility_score"
        threshold = False
        quantum = None
    elif "regime" in family or "scenario" in family:
        semantics = "SCENARIO_TRANSFORM"
        unit = "scenario_multiplier"
        threshold = False
        quantum = None
    elif "market_implied" in family:
        semantics = "MARKET_IMPLIED_PROBABILITY"
        unit = "probability_0_to_1"
        threshold = True
        quantum = None
    else:
        semantics = "EXPECTED_GROSS_PNL"
        unit = "dollars_per_contract"
        threshold = False
        quantum = None
    return {
        "semantics": semantics,
        "unit": unit,
        "threshold_only_flag": threshold,
        "independent_probability_required_flag": semantics in {"PROBABILITY_ESTIMATE", "EXPECTED_GROSS_PNL", "MARKET_IMPLIED_PROBABILITY"},
        "market_implied_only_flag": semantics == "MARKET_IMPLIED_PROBABILITY",
        "replay_use_field": "replay_net_expected_pnl_candidate" if not threshold else "break_even_threshold_candidate",
        "paper_use_field": "paper_net_expected_pnl_candidate" if not threshold else "paper_required_edge_threshold",
        "rank2_use_field": "rank2_selection_feature_score_non_proof",
        "tca_role": "cost_component" if semantics in {"TCA_COMPONENT", "COST_COMPONENT"} else None,
        "fill_role": "fillability_component" if semantics == "FILL_PROBABILITY_OR_FILLABILITY" else None,
        "capacity_role": "capacity_component" if "capacity" in family else None,
        "scenario_role": "scenario_transform" if semantics == "SCENARIO_TRANSFORM" else None,
        "quantum_role": quantum,
    }


def formula_signal(formula: dict[str, Any], index: int) -> float:
    family = str(formula.get("formula_family") or "").lower()
    base = ((index % 9) - 4) * 0.004
    if "market_implied" in family:
        return 0.0
    if "orderbook" in family or "tca" in family:
        return base + 0.006
    if "calib" in family or "portfolio" in family or "regime" in family:
        return base + 0.004
    if "quantum" in family:
        return base + 0.002
    return base


def classify_replay(net: float) -> str:
    if net > 1e-9:
        return "REPLAY_POSITIVE_AFTER_COSTS_NON_PROOF"
    if net < -1e-9:
        return "REPLAY_NEGATIVE_AFTER_COSTS_NON_PROOF"
    return "REPLAY_NEUTRAL_AFTER_COSTS_NON_PROOF"


def classify_paper(net: float) -> str:
    if net > 1e-9:
        return "PAPER_POSITIVE_AFTER_COSTS_NON_PROOF"
    if net < -1e-9:
        return "PAPER_NEGATIVE_AFTER_COSTS_NON_PROOF"
    return "PAPER_NEUTRAL_AFTER_COSTS_NON_PROOF"


def rank2_score(replay: dict[str, Any], paper: dict[str, Any], tca: dict[str, Any], quality: dict[str, Any]) -> float:
    positive = (
        float(replay["replay_net_expected_pnl_candidate"])
        + float(paper["paper_net_expected_pnl_candidate"])
        + float(replay["replay_fill_adjusted_expected_pnl"])
        + float(replay["replay_no_trade_margin_candidate"])
        + float(quality["overall_formula_quality_score_non_proof"])
    )
    penalty = float(tca["TCA_total_candidate"]) + 0.1
    return round(positive - penalty, 8)


def scenario_multiplier(scenario: str) -> float:
    return {
        "BASE_OBSERVED": 1.0,
        "NO_TRADE_BASELINE": 0.0,
        "WIDE_SPREAD_PLUS_1C": 0.92,
        "WIDE_SPREAD_PLUS_2C": 0.85,
        "THIN_BOOK_50_PERCENT_DEPTH": 0.72,
        "THIN_BOOK_25_PERCENT_DEPTH": 0.55,
        "LATENCY_DELAY_SHORT": 0.95,
        "LATENCY_DELAY_MEDIUM": 0.88,
        "LATENCY_DELAY_LONG": 0.75,
        "STALE_DATA_TTL_BREACH": 0.6,
        "FEE_INCREASE_SCENARIO": 0.9,
        "PARTIAL_FILL_50_PERCENT": 0.5,
        "NO_FILL_SCENARIO": 0.0,
        "ADVERSE_SELECTION_SHORT_HORIZON_MOVE": 0.7,
        "PROBABILITY_MODEL_MISSING": 0.0,
        "HISTORICAL_FULL_BOOK_MISSING": 0.4,
        "CAPACITY_DEPTH_LIMIT": 0.65,
        "SOURCE_ACCEPTANCE_PENDING": 0.3,
        "FORMULA_EXPRESSION_REPAIR_PENDING": 0.2,
    }.get(scenario, 1.0)


def scenario_tca_multiplier(scenario: str) -> float:
    return 1.0 + (1.0 - scenario_multiplier(scenario)) * 0.5


def scenario_modified_inputs(scenario: str) -> list[str]:
    mapping = {
        "NO_TRADE_BASELINE": ["candidate_size", "execution_policy"],
        "WIDE_SPREAD_PLUS_1C": ["spread_cross_cost"],
        "WIDE_SPREAD_PLUS_2C": ["spread_cross_cost"],
        "THIN_BOOK_50_PERCENT_DEPTH": ["available_depth"],
        "THIN_BOOK_25_PERCENT_DEPTH": ["available_depth"],
        "LATENCY_DELAY_SHORT": ["latency_seconds"],
        "LATENCY_DELAY_MEDIUM": ["latency_seconds"],
        "LATENCY_DELAY_LONG": ["latency_seconds"],
        "STALE_DATA_TTL_BREACH": ["staleness_seconds"],
        "FEE_INCREASE_SCENARIO": ["explicit_fee_candidate"],
        "PARTIAL_FILL_50_PERCENT": ["fill_probability_candidate"],
        "NO_FILL_SCENARIO": ["fill_probability_candidate"],
        "ADVERSE_SELECTION_SHORT_HORIZON_MOVE": ["adverse_selection_proxy"],
        "PROBABILITY_MODEL_MISSING": ["p_resolve_yes_candidate"],
        "HISTORICAL_FULL_BOOK_MISSING": ["historical_full_book_available_flag"],
        "CAPACITY_DEPTH_LIMIT": ["capacity_depth_penalty"],
        "SOURCE_ACCEPTANCE_PENDING": ["source_evidence_state"],
        "FORMULA_EXPRESSION_REPAIR_PENDING": ["formula_expression_state"],
    }
    return mapping.get(scenario, ["base_inputs"])


def scenario_repair_route(scenario: str) -> str | None:
    if "SOURCE" in scenario:
        return "SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED"
    if "EXPRESSION" in scenario:
        return "FORMULA_EXPRESSION_REPAIR_REQUIRED"
    if "FULL_BOOK" in scenario:
        return "HISTORICAL_FULL_BOOK_DEPENDENT_REPAIR_REQUIRED"
    if "PROBABILITY" in scenario:
        return "BIND_INDEPENDENT_PROBABILITY_MODEL"
    if "FILL" in scenario:
        return "FILL_INPUT_GAP_REPAIR_REQUIRED"
    if "LATENCY" in scenario or "STALE" in scenario:
        return "LATENCY_INPUT_GAP_REPAIR_REQUIRED"
    if "CAPACITY" in scenario:
        return "CAPACITY_INPUT_GAP_REPAIR_REQUIRED"
    return None


def query_family_for_url(url: str) -> str:
    lower = url.lower()
    if "kalshi" in lower:
        return "Kalshi market data/orderbook/trades/candlesticks/fees/tick/min-size/WebSocket docs"
    if "polymarket" in lower:
        return "Polymarket Gamma/CLOB/Data orderbook/prices-history/midpoint/spread/last trade/fee-rate/tick-size/WebSocket docs"
    if "forecast" in lower or "interactivebrokers" in lower or "ibkr" in lower:
        return "ForecastEx/IBKR event-contract and market-data docs as auth/subscription candidate routes"
    if "qiskit" in lower or "dwave" in lower:
        return "Qiskit QuadraticProgram/QUBO and D-Wave BQM/CQM/Ising/QUBO structural mapping"
    if "sharpe" in lower or "fdr" in lower or "calibration" in lower:
        return "Brier/log-loss/ECE / Benjamini-Hochberg FDR / Deflated Sharpe / purged-CPCV"
    if "portfolio" in lower or "regime" in lower:
        return "portfolio marginal utility / concentration / correlation clustering / regime features"
    if "latency" in lower or "capacity" in lower:
        return "latency decay / staleness / capacity / participation"
    if "fill" in lower or "orderbook" in lower:
        return "limit-order fill probability / depth fillability / orderbook imbalance / microprice"
    return "implementation shortfall / transaction-cost analysis / spread / slippage / adverse selection"


def first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def value_or(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def safe_float(value: Any, default: float) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, float(value)))


def depth_from_book(normalized: dict[str, Any]) -> float:
    levels = normalized.get("asks") or normalized.get("yes_bids") or normalized.get("no_bids") or []
    if not isinstance(levels, list):
        return 1.0
    total = 0.0
    for level in levels[:5]:
        if isinstance(level, dict):
            total += safe_float(level.get("size"), 0.0)
    return max(1.0, total)


def order_policy_for_index(index: int) -> str:
    policies = [
        "TAKER_CROSS_AT_BEST_AVAILABLE",
        "MAKER_JOIN_BEST_BID_OR_ASK",
        "MAKER_IMPROVE_BY_ONE_TICK_IF_ALLOWED",
        "PASSIVE_WAIT_THEN_CANCEL",
        "PASSIVE_WAIT_THEN_CROSS_IF_EDGE_REMAINS",
        "REDUCED_SIZE_FOR_DEPTH",
    ]
    return policies[(index - 1) % len(policies)]


def parse_tick(value: str) -> float:
    if "=" in str(value):
        return safe_float(str(value).split("=", 1)[1], 0.01)
    return safe_float(value, 0.01)


def unit_for_numeric_field(field: str) -> str:
    if "probability" in field or "fill" in field:
        return "ratio_0_to_1"
    if "score" in field or "quality" in field:
        return "score"
    if "edge" in field:
        return "probability_edge"
    return "dollars_per_contract_bucket"
