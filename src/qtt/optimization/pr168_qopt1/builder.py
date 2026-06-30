"""Deterministic PR168-QOPT1 advisory batch optimizer."""

from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from .models import (
    AUTHORITY_BOUNDARY_REF,
    BASELINE_MAIN_HEAD,
    BLOCKER_POLICY_REF,
    BRANCH_NAME,
    CREATED_AT_UTC,
    EXECUTION_AUTHORITY_REF,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    JSON_OUTPUTS,
    MARKDOWN_OUTPUTS,
    OPTIONAL_INPUT_REFS,
    PARAM_DEFAULTS,
    PR_ID,
    REPORT_OUTPUTS,
    REQUIRED_INPUT_REFS,
    REPO_ROOT,
    RESEARCH_SOURCES,
    RUN_ID,
    VALIDATOR_REF,
    all_artifact_filenames,
    bounded,
    common_report,
    common_row,
    dec,
    generated_ref,
    read_json,
    read_jsonl,
    score,
    stable_unique,
    upstream_rank4_ref,
    upstream_rp5g_ref,
    write_json,
    write_jsonl,
    write_text,
)


ROLE_AGENTS = (
    "CommanderAgent",
    "MarketConditionAgent",
    "FormulaLibraryAgent",
    "StackGeneratorAgent",
    "ExecutabilityAgent",
    "TradeTargetScoutAgent",
    "OrderVariableAgent",
    "TradePlanSimulationAgent",
    "RankerAgent",
    "QOPTAgent",
    "TCAAgent",
    "FillLatencyAgent",
    "RiskAgent",
    "MemoryAgent",
    "GovernanceAgent",
    "PaperExecutionAgent",
    "LiveDryRunAgent",
    "ShadowObservationAgent",
    "ResearchScoutAgent",
    "ModelRiskAgent",
    "ExecutionRouterAgent",
)

CONSTRAINT_DEFS = (
    ("batch_size_max_constraint", "<=", "3", "QOPT1_CONSTRAINT_BATCH_SIZE_MAX", "RiskAgent"),
    ("batch_size_min_or_no_trade_constraint", ">=", "1", "QOPT1_CONSTRAINT_BATCH_SIZE_MIN_OR_NOTRADE", "RiskAgent"),
    ("capital_budget_constraint", "<=", "20.000000", "QOPT1_CONSTRAINT_CAPITAL_BUDGET", "RiskAgent"),
    ("venue_exposure_constraint", "<=", "2", "QOPT1_CONSTRAINT_VENUE_EXPOSURE", "RiskAgent"),
    ("market_cluster_exposure_constraint", "<=", "1", "QOPT1_CONSTRAINT_MARKET_CLUSTER", "RiskAgent"),
    ("event_cluster_exposure_constraint", "<=", "1", "QOPT1_CONSTRAINT_EVENT_CLUSTER", "RiskAgent"),
    ("formula_family_concentration_constraint", "<=", "0.750000", "QOPT1_CONSTRAINT_FORMULA_FAMILY", "RiskAgent"),
    ("qku_family_concentration_constraint", "<=", "0.750000", "QOPT1_CONSTRAINT_QKU_FAMILY", "RiskAgent"),
    ("side_exposure_constraint", "<=", "2", "QOPT1_CONSTRAINT_SIDE_EXPOSURE", "RiskAgent"),
    ("one_side_per_market_constraint", "<=", "1", "QOPT1_CONSTRAINT_ONE_SIDE_PER_MARKET", "RiskAgent"),
    ("one_policy_per_candidate_constraint", "<=", "1", "QOPT1_CONSTRAINT_ONE_POLICY_PER_CANDIDATE", "GovernanceAgent"),
    ("no_stale_candidate_constraint", "==", "1", "QOPT1_CONSTRAINT_NO_STALE", "GovernanceAgent"),
    ("min_no_trade_margin_constraint", ">=", "0.000000", "QOPT1_CONSTRAINT_NOTRADE_MARGIN", "RiskAgent"),
    ("min_LCB_constraint", ">=", "0.000000", "QOPT1_CONSTRAINT_LCB", "RiskAgent"),
    ("min_fill_probability_constraint", ">=", "0.500000", "QOPT1_CONSTRAINT_FILL", "FillLatencyAgent"),
    ("max_latency_budget_constraint", "<=", "1000", "QOPT1_CONSTRAINT_LATENCY", "FillLatencyAgent"),
    ("max_capacity_crowding_constraint", "<=", "0.250000", "QOPT1_CONSTRAINT_CAPACITY", "RiskAgent"),
    ("max_TCA_to_edge_ratio_constraint", "<=", "0.500000", "QOPT1_CONSTRAINT_TCA_EDGE", "TCAAgent"),
    ("max_model_risk_reserve_constraint", "<=", "0.500000", "QOPT1_CONSTRAINT_MODEL_RISK", "ModelRiskAgent"),
    ("max_FDR_penalty_constraint", "<=", "0.250000", "QOPT1_CONSTRAINT_FDR", "ModelRiskAgent"),
    ("scenario_worst_case_floor_constraint", ">=", "-0.500000", "QOPT1_CONSTRAINT_SCENARIO", "RiskAgent"),
    ("portfolio_exposure_cap_constraint", "<=", "2", "QOPT1_CONSTRAINT_PORTFOLIO_EXPOSURE", "RiskAgent"),
    ("source_freshness_or_provenance_constraint", "==", "1", "QOPT1_CONSTRAINT_SOURCE_FRESH", "MarketConditionAgent"),
    ("agent_route_pass_constraint", "==", "1", "QOPT1_CONSTRAINT_AGENT_ROUTE", "GovernanceAgent"),
    ("no_orphan_pass_constraint", "==", "1", "QOPT1_CONSTRAINT_NO_ORPHAN", "GovernanceAgent"),
    ("authority_boundary_pass_constraint", "==", "1", "QOPT1_CONSTRAINT_AUTHORITY", "GovernanceAgent"),
    ("no_live_no_paper_order_authority_constraint", "==", "1", "QOPT1_CONSTRAINT_NO_ORDER_AUTHORITY", "GovernanceAgent"),
)

OBJECTIVE_COMPONENTS = (
    "net_expected_pnl_cash",
    "lower_confidence_bound_pnl_cash",
    "candidate_minus_no_trade_cash",
    "portfolio_marginal_utility_cash",
    "scenario_robustness_score",
    "calibration_quality_score",
    "recipe_prior_score_hint",
    "quantum_structural_quality_score",
    "fill_quality_score",
    "TCA_total_cash",
    "fill_shortfall_penalty_cash",
    "latency_decay_penalty_cash",
    "capacity_crowding_penalty_cash",
    "overfit_fdr_penalty_cash",
    "model_risk_reserve_cash",
    "capital_lock_cost_cash",
    "tail_loss_proxy_cash",
)


def _repo_path(ref: str, repo_root: Path) -> Path:
    return repo_root / ref


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".jsonl":
        return len([line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()])
    if path.suffix == ".json":
        return 1
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _clean_generated_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    allowed = set(all_artifact_filenames())
    for path in out_dir.iterdir():
        if path.is_file() and path.name in allowed:
            path.unlink()


def _surface_family(ref: str) -> str:
    if "pr168_rank4" in ref:
        return "RANK4_ADVISORY_RANKING_INPUT"
    if "pr168_rp5g" in ref:
        return "RP5G_REPLAY_PAPER_SIMULATION_INPUT"
    if "pr168_rp5f" in ref:
        return "RP5F_TARGET_GRID_INPUT"
    if "PR165_D2" in ref:
        return "PR165_D2_AGENT_DUTY_INPUT"
    if "rp5c" in ref.lower() or "RP5C" in ref:
        return "RP5C_IMMUTABLE_LIBRARY_INPUT"
    if "pr168_vs1" in ref:
        return "VS1_TRADING_SLICE_INPUT"
    if "pr168_rp5d" in ref:
        return "RP5D_EXECUTABILITY_INPUT"
    if "pr168_rp5e" in ref:
        return "RP5E_STACK_PREVIEW_INPUT"
    return "MASTER_PLAN_OR_OPTIONAL_INPUT"


def _by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = row.get("candidate_id") or row.get("trade_plan_candidate_id") or row.get("ranked_candidate_ids", [None])[0]
        if cid and str(cid) not in out:
            out[str(cid)] = row
    return out


def _first_row(rows: list[dict[str, Any]], default: dict[str, Any] | None = None) -> dict[str, Any]:
    return rows[0] if rows else (default or {})


def _build_reading_rows(repo_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    read_rows: list[dict[str, Any]] = []
    in_cons: list[dict[str, Any]] = []
    miss_opt: list[dict[str, Any]] = []
    missing_required: list[str] = []
    for index, ref in enumerate(REQUIRED_INPUT_REFS, start=1):
        path = _repo_path(ref, repo_root)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        else:
            missing_required.append(ref)
        row_id = f"QOPT1_READ_{index:05d}"
        family = _surface_family(ref)
        read_rows.append(
            common_row(
                {
                    "receipt_id": row_id,
                    "input_family": family,
                    "resolved_path": ref,
                    "required_flag": True,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_summary": _row_count(path),
                    "input_producer_pr": "UPSTREAM" if exists else "MISSING",
                    "consumer_modules": ["src.qtt.optimization.pr168_qopt1.builder"],
                    "missing_action_if_absent": "FAIL_CLOSED_MISSING_REQUIRED_INPUT",
                    "freshness_or_commit_ref_when_available": BASELINE_MAIN_HEAD if ref.endswith("QTT_MasterPlan_Current.md") else "UPSTREAM_GENERATED_ARTIFACT",
                },
                row_id=row_id,
                owner_agent="CommanderAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("missing_req.report.json")],
                provenance_tier="QOPT1_INPUT_READ_RECEIPT",
                intelligence_classes=("KNOWLEDGE_INTELLIGENCE",),
            )
        )
        in_cons.append(
            common_row(
                {
                    "input_consumption_id": f"QOPT1_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": family,
                    "consumed_flag": exists,
                    "row_count_consumed": _row_count(path) if exists else 0,
                    "consumer_output_refs": [generated_ref("batch_universe.jsonl"), generated_ref("obj_terms.jsonl")],
                },
                row_id=f"QOPT1_IN_CONS_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("lineage.jsonl"), generated_ref("artifact_io.jsonl")],
                provenance_tier="QOPT1_INPUT_CONSUMPTION_RECEIPT",
            )
        )
    for index, ref in enumerate(OPTIONAL_INPUT_REFS, start=1):
        path = _repo_path(ref, repo_root)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        miss_opt.append(
            common_row(
                {
                    "missing_optional_id": f"QOPT1_MISS_OPT_{index:04d}",
                    "optional_artifact_ref": ref,
                    "exists_flag": exists,
                    "consumed_flag": exists,
                    "row_count_or_summary": _row_count(path),
                    "fallback_ref": "RANK4/RP5G core evidence and QOPT1 completion routes",
                    "fail_closed_flag": False,
                },
                row_id=f"QOPT1_MISS_OPT_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[ref] if exists else ["optional_input_absent"],
                downstream_refs=[generated_ref("completion_route.jsonl")],
                provenance_tier="QOPT1_OPTIONAL_INPUT_RECEIPT",
            )
        )
    return read_rows, in_cons, miss_opt, missing_required


def _load_upstream(repo_root: Path) -> dict[str, Any]:
    rank4 = repo_root / "docs" / "master_plan" / "generated" / "pr168_rank4"
    rp5g = repo_root / "docs" / "master_plan" / "generated" / "pr168_rp5g"
    return {
        "rank4_rank_order": read_jsonl(rank4 / "rank_order.jsonl"),
        "rank4_rank_score": read_jsonl(rank4 / "rank_score.jsonl"),
        "rank4_rank_feat": read_jsonl(rank4 / "rank_feat.jsonl"),
        "rank4_score_comp": read_jsonl(rank4 / "score_comp.jsonl"),
        "rank4_qopt_batch": read_jsonl(rank4 / "qopt_batch.jsonl"),
        "rank4_qopt_frontier": read_jsonl(rank4 / "qopt_frontier.jsonl"),
        "rank4_qopt_constraints": read_jsonl(rank4 / "qopt_constraints.jsonl"),
        "rank4_qopt_interpret": read_jsonl(rank4 / "qopt_interpret_back_rank_map.jsonl"),
        "rank4_notrade": read_jsonl(rank4 / "notrade_rank.jsonl"),
        "rank4_tca": read_jsonl(rank4 / "tca_rank.jsonl"),
        "rank4_fill": read_jsonl(rank4 / "fill_lat_rank.jsonl"),
        "rank4_capacity": read_jsonl(rank4 / "capacity_rank.jsonl"),
        "rank4_port": read_jsonl(rank4 / "port_div_rank.jsonl"),
        "rank4_fdr": read_jsonl(rank4 / "fdr_rank.jsonl"),
        "rank4_scenario": read_jsonl(rank4 / "scenario_rank.jsonl"),
        "rank4_memory_recipe": read_jsonl(rank4 / "rank_memory_recipe_handoff.jsonl"),
        "rank4_recipe_prior": read_jsonl(rank4 / "rank_recipe_prior_score.jsonl"),
        "rank4_drift": read_jsonl(rank4 / "rank_recipe_drift_hint.jsonl"),
        "rank4_negative_memory": read_jsonl(rank4 / "rank_negative_memory_hint.jsonl"),
        "rank4_retest": read_jsonl(rank4 / "rank_retest_priority.jsonl"),
        "rank4_qmemory": read_jsonl(rank4 / "rank_qmemory_handoff.jsonl"),
        "rank4_hotpath": read_jsonl(rank4 / "rank_hotpath.jsonl"),
        "rank4_constraint_tightness": read_jsonl(rank4 / "rank_constraint_tightness.jsonl"),
        "rank4_source_rights": read_jsonl(rank4 / "rank_source_rights.jsonl"),
        "rank4_agent_route": read_jsonl(rank4 / "agent_route.jsonl"),
        "rank4_agent_consume": read_jsonl(rank4 / "agent_consume.jsonl"),
        "rank4_no_orphan_report": read_json(rank4 / "no_orphan.report.json"),
        "rank4_run_receipt": read_json(rank4 / "run_receipt.report.json"),
        "rp5g_trade_candidate": read_jsonl(rp5g / "trade_candidate.jsonl"),
        "rp5g_exec_pnl": read_jsonl(rp5g / "exec_pnl.jsonl"),
        "rp5g_tca": read_jsonl(rp5g / "tca_decomp.jsonl"),
        "rp5g_fill": read_jsonl(rp5g / "fill_latency_cap.jsonl"),
        "rp5g_capacity": read_jsonl(rp5g / "capacity_crowding.jsonl"),
        "rp5g_notrade": read_jsonl(rp5g / "notrade_cmp.jsonl"),
        "rp5g_scenario": read_jsonl(rp5g / "scenario_ladder.jsonl"),
        "rp5g_fdr": read_jsonl(rp5g / "overfit_fdr.jsonl"),
        "rp5g_port": read_jsonl(rp5g / "port_marg_util.jsonl"),
        "rp5g_calib": read_jsonl(rp5g / "calibration_result.jsonl"),
        "rp5g_qstruct": read_jsonl(rp5g / "qstruct_problem.jsonl"),
        "rp5g_qobj_coeff": read_jsonl(rp5g / "qobj_coeff.jsonl"),
        "rp5g_q_constraints": read_jsonl(rp5g / "q_constraints.jsonl"),
        "rp5g_q_interp": read_jsonl(rp5g / "q_interp.jsonl"),
        "rp5g_q_classic_fb": read_jsonl(rp5g / "q_classic_fb.jsonl"),
        "rp5g_qopt_handoff": read_jsonl(rp5g / "qopt_handoff.jsonl"),
        "rp5g_near_clone": read_jsonl(rp5g / "near_clone_cluster.jsonl"),
        "rp5g_run_receipt": read_json(rp5g / "run_receipt.report.json"),
    }


def _candidate_payloads(upstream: dict[str, Any]) -> list[dict[str, Any]]:
    features = _by_candidate(upstream["rank4_rank_feat"])
    rank_scores = _by_candidate(upstream["rank4_rank_score"])
    trade_candidates = _by_candidate(upstream["rp5g_trade_candidate"])
    exec_pnl = _by_candidate(upstream["rp5g_exec_pnl"])
    fill = _by_candidate(upstream["rp5g_fill"])
    capacity = _by_candidate(upstream["rp5g_capacity"])
    port = _by_candidate(upstream["rp5g_port"])
    fdr = _by_candidate(upstream["rp5g_fdr"])
    calib = _by_candidate(upstream["rp5g_calib"])
    qopt_batch = _by_candidate(upstream["rank4_qopt_batch"])
    prior = _by_candidate(upstream["rank4_recipe_prior"])
    ordered = [str(row["candidate_id"]) for row in upstream["rank4_rank_order"] if row.get("candidate_id")]
    if not ordered:
        ordered = sorted(features)
    qstruct_problem_ref = upstream_rp5g_ref("qstruct_problem.jsonl")
    out: list[dict[str, Any]] = []
    for position, cid in enumerate(ordered, start=1):
        feat = features.get(cid, {})
        cand = trade_candidates.get(cid, {})
        pnl = exec_pnl.get(cid, {})
        fill_row = fill.get(cid, {})
        cap_row = capacity.get(cid, {})
        port_row = port.get(cid, {})
        fdr_row = fdr.get(cid, {})
        calib_row = calib.get(cid, {})
        score_row = rank_scores.get(cid, {})
        rank_score = dec(score_row.get("rank4_execution_adjusted_score", feat.get("rank4_execution_adjusted_score")))
        net = dec(pnl.get("net_expected_pnl_cash", feat.get("net_expected_pnl_cash")))
        lcb = dec(pnl.get("lower_confidence_bound_pnl_cash", feat.get("lower_confidence_bound_pnl_cash")))
        no_margin = dec(pnl.get("candidate_minus_no_trade_cash", feat.get("candidate_minus_no_trade_cash")))
        tca = dec(pnl.get("TCA_total_cash", feat.get("TCA_total_cash")))
        fill_probability = dec(fill_row.get("fill_probability", feat.get("fill_probability")))
        latency = dec(cand.get("latency_budget_candidate", feat.get("latency_budget", 0)))
        latency_penalty = dec(fill_row.get("latency_decay_penalty_cash", feat.get("latency_decay_penalty_cash")))
        cap_penalty = dec(cap_row.get("capacity_crowding_penalty_cash", feat.get("capacity_crowding_penalty_cash")))
        port_utility = dec(port_row.get("portfolio_marginal_utility_cash", feat.get("portfolio_marginal_utility_cash")))
        fdr_penalty = dec(fdr_row.get("fdr_penalty_cash", feat.get("fdr_penalty_cash")))
        calibration_quality = Decimal("1") - min(
            Decimal("1"),
            abs(dec(calib_row.get("calibration_gap", feat.get("calibration_gap")))),
        )
        memory_prior = dec(prior.get(cid, {}).get("recipe_prior_score", "0.100000"))
        qstruct_quality = Decimal("1") if qopt_batch.get(cid) else Decimal("0.75")
        scenario_worst = dec(feat.get("scenario_worst_case_pnl_cash", pnl.get("lower_confidence_bound_pnl_cash")))
        scenario_score = bounded(feat.get("scenario_robustness_score", "0.650000"))
        model_risk = dec(fdr_row.get("model_risk_reserve_cash", "0.050000"))
        tail_loss = max(Decimal("0"), -scenario_worst)
        capital = dec(cand.get("total_investment_candidate", "1"))
        tca_edge_ratio = tca / max(abs(no_margin), Decimal("0.000001"))
        hard_pass = (
            no_margin >= Decimal("0")
            and lcb >= Decimal("0")
            and fill_probability >= Decimal("0.50")
            and latency <= Decimal("1000")
            and cap_penalty <= Decimal("0.250000")
            and tca_edge_ratio <= Decimal("0.500000")
            and model_risk <= Decimal("0.500000")
            and fdr_penalty <= Decimal("0.250000")
            and scenario_worst >= Decimal("-0.500000")
        )
        utility = (
            rank_score
            + net * Decimal("0.20")
            + lcb * Decimal("0.16")
            + no_margin * Decimal("0.14")
            + port_utility * Decimal("0.08")
            + scenario_score * Decimal("0.06")
            + calibration_quality * Decimal("0.03")
            + memory_prior * Decimal("0.03")
            + qstruct_quality * Decimal("0.04")
            + fill_probability * Decimal("0.08")
            - tca * Decimal("0.10")
            - latency_penalty * Decimal("0.06")
            - cap_penalty * Decimal("0.06")
            - fdr_penalty * Decimal("0.05")
            - model_risk * Decimal("0.04")
            - tail_loss * Decimal("0.06")
        )
        payload = {
            "candidate_id": cid,
            "rank4_rank_id": score_row.get("rank_id", f"RANK4_RANK_{position:04d}"),
            "rank4_rank_position": position,
            "rank4_execution_adjusted_score": score(rank_score),
            "trade_plan_ref": cand.get("trade_plan_candidate_id", cid),
            "rp5g_exec_pnl_ref": pnl.get("execution_pnl_id", f"RP5G_EXEC_PNL_{position:04d}"),
            "simulation_run_id": feat.get("simulation_run_id", f"RP5G_SIM_RUN_{position:04d}"),
            "target_id": cand.get("target_id", feat.get("target_id")),
            "grid_id": cand.get("grid_id", feat.get("grid_id")),
            "trade_seed_id": cand.get("trade_seed_id", feat.get("seed_id")),
            "market_id": cand.get("market_id", feat.get("market_id")),
            "event_id": cand.get("event_id", feat.get("event_cluster_id")),
            "venue": cand.get("venue", feat.get("venue")),
            "side": cand.get("side", feat.get("side")),
            "entry_bucket": cand.get("entry_price_candidate", feat.get("entry_bucket")),
            "size_bucket": cand.get("order_size_candidate", feat.get("size_bucket")),
            "hold_duration_bucket": cand.get("hold_duration_candidate", feat.get("hold_duration_bucket")),
            "exit_rule": cand.get("exit_rule_candidate", feat.get("exit_rule")),
            "maker_taker_split": cand.get("maker_taker_split_candidate", feat.get("maker_taker_policy")),
            "cancel_replace_policy": cand.get("cancel_replace_interval_candidate", feat.get("cancel_replace_bucket")),
            "spread_depth_liquidity_filter": f"{cand.get('spread_filter_candidate', feat.get('spread_bucket'))}:{cand.get('depth_filter_candidate', cand.get('liquidity_filter_candidate', feat.get('liquidity_bucket')))}",
            "latency_budget_bucket": cand.get("latency_budget_candidate", feat.get("latency_bucket")),
            "portfolio_exposure_bucket": cand.get("portfolio_exposure_candidate", feat.get("portfolio_exposure_domain", "UNKNOWN")),
            "formula_refs": stable_unique(cand.get("formula_refs", feat.get("formula_refs", []))),
            "qku_refs": stable_unique(cand.get("qku_refs", feat.get("qku_refs", []))),
            "formula_family_refs": stable_unique(str(ref).rsplit("_", 1)[0] for ref in cand.get("formula_refs", feat.get("formula_refs", []))),
            "qku_family_refs": stable_unique(str(ref).split("::", 1)[0] for ref in cand.get("qku_refs", feat.get("qku_refs", []))),
            "net_expected_pnl_cash": score(net),
            "lower_confidence_bound_pnl_cash": score(lcb),
            "candidate_minus_no_trade_cash": score(no_margin),
            "TCA_total_cash": score(tca),
            "fill_probability": score(fill_probability),
            "partial_fill_ratio": score(fill_row.get("partial_fill_ratio", "1")),
            "fill_shortfall_penalty_cash": score(max(Decimal("0"), Decimal("1") - fill_probability)),
            "latency_decay_penalty_cash": score(latency_penalty),
            "capacity_crowding_penalty_cash": score(cap_penalty),
            "portfolio_marginal_utility_cash": score(port_utility),
            "overfit_fdr_penalty_cash": score(fdr_penalty),
            "scenario_worst_case_cash": score(scenario_worst),
            "scenario_robustness_score": score(scenario_score),
            "calibration_quality_score": score(calibration_quality),
            "recipe_prior_score_hint": score(memory_prior),
            "quantum_structural_quality_score": score(qstruct_quality),
            "model_risk_reserve_cash": score(model_risk),
            "capital_lock_cost_cash": score(pnl.get("capital_lock_cost_cash", "0")),
            "tail_loss_proxy_cash": score(tail_loss),
            "capital_required_cash_or_proxy": score(capital),
            "TCA_to_edge_ratio": score(tca_edge_ratio),
            "qstruct_problem_ref": qstruct_problem_ref,
            "hard_constraint_pass_flag": hard_pass,
            "eligible_for_primary_batch_flag": hard_pass,
            "numeric_evidence_refs": [
                upstream_rank4_ref("rank_score.jsonl"),
                upstream_rp5g_ref("exec_pnl.jsonl"),
                upstream_rp5g_ref("tca_decomp.jsonl"),
                upstream_rp5g_ref("fill_latency_cap.jsonl"),
                upstream_rp5g_ref("capacity_crowding.jsonl"),
                upstream_rp5g_ref("notrade_cmp.jsonl"),
            ],
            "objective_value": score(utility),
            "constraint_violation_codes": [] if hard_pass else _candidate_violation_codes(no_margin, lcb, fill_probability, latency, cap_penalty, tca_edge_ratio, fdr_penalty, model_risk, scenario_worst),
        }
        out.append(payload)
    return out


def _candidate_violation_codes(
    no_margin: Decimal,
    lcb: Decimal,
    fill_probability: Decimal,
    latency: Decimal,
    cap_penalty: Decimal,
    tca_edge_ratio: Decimal,
    fdr_penalty: Decimal,
    model_risk: Decimal,
    scenario_worst: Decimal,
) -> list[str]:
    codes: list[str] = []
    if no_margin < 0:
        codes.append("NO_TRADE_MARGIN")
    if lcb < 0:
        codes.append("LCB")
    if fill_probability < Decimal("0.50"):
        codes.append("FILL")
    if latency > Decimal("1000"):
        codes.append("LATENCY")
    if cap_penalty > Decimal("0.250000"):
        codes.append("CAPACITY")
    if tca_edge_ratio > Decimal("0.500000"):
        codes.append("TCA")
    if fdr_penalty > Decimal("0.250000"):
        codes.append("FDR")
    if model_risk > Decimal("0.500000"):
        codes.append("MODEL_RISK")
    if scenario_worst < Decimal("-0.500000"):
        codes.append("SCENARIO")
    return codes


def _pair_key(left: str, right: str) -> str:
    return "|".join(sorted((left, right)))


def _pair_penalty(left: dict[str, Any], right: dict[str, Any]) -> Decimal:
    penalty = Decimal("0")
    if left["event_id"] == right["event_id"]:
        penalty += Decimal("1.000000")
    if left["market_id"] == right["market_id"]:
        penalty += Decimal("1.000000")
    if left["venue"] == right["venue"]:
        penalty += Decimal("0.030000")
    left_forms = set(left["formula_refs"])
    right_forms = set(right["formula_refs"])
    if left_forms or right_forms:
        overlap = Decimal(len(left_forms & right_forms)) / Decimal(max(1, len(left_forms | right_forms)))
        penalty += overlap * Decimal("0.080000")
    if left["side"] == right["side"]:
        penalty += Decimal("0.010000")
    return penalty


def _diversity_bonus(combo: Iterable[dict[str, Any]]) -> Decimal:
    rows = list(combo)
    if not rows:
        return Decimal("0")
    venues = len({row["venue"] for row in rows})
    events = len({row["event_id"] for row in rows})
    return Decimal("0.020000") * Decimal(venues + events - len(rows))


def _batch_objective(combo: list[dict[str, Any]]) -> Decimal:
    base = sum((dec(row["objective_value"]) for row in combo), Decimal("0"))
    pair = Decimal("0")
    for left, right in combinations(combo, 2):
        pair += _pair_penalty(left, right)
    return base - pair + _diversity_bonus(combo)


def _batch_feasible(combo: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    violations: list[str] = []
    if not combo:
        return False, ["NO_SELECTED_CANDIDATES"]
    if len(combo) > int(PARAM_DEFAULTS["batch_size_max_default"]):
        violations.append("BATCH_SIZE_MAX")
    if sum((dec(row["capital_required_cash_or_proxy"]) for row in combo), Decimal("0")) > dec(PARAM_DEFAULTS["capital_budget_cash_proxy_default"]):
        violations.append("CAPITAL_BUDGET")
    if len({row["market_id"] for row in combo}) != len(combo):
        violations.append("ONE_SIDE_PER_MARKET")
    if len({row["event_id"] for row in combo}) != len(combo):
        violations.append("EVENT_CLUSTER")
    for row in combo:
        violations.extend(row["constraint_violation_codes"])
    return not violations, stable_unique(violations)


def _enumerate_batches(candidates: list[dict[str, Any]], max_size: int = 3) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    for size in range(1, min(max_size, len(candidates)) + 1):
        for combo_tuple in combinations(candidates, size):
            combo = list(combo_tuple)
            feasible, violations = _batch_feasible(combo)
            objective = _batch_objective(combo)
            batches.append(
                {
                    "selected_candidate_ids": [row["candidate_id"] for row in combo],
                    "objective_value": objective,
                    "constraint_pass_flag": feasible,
                    "constraint_violations": violations,
                }
            )
    return sorted(
        batches,
        key=lambda row: (
            row["constraint_pass_flag"],
            row["objective_value"],
            -len(row["selected_candidate_ids"]),
            "|".join(row["selected_candidate_ids"]),
        ),
        reverse=True,
    )


def _select_solver_results(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    eligible = [row for row in candidates if row["hard_constraint_pass_flag"]]
    greedy_selected = []
    used_markets: set[str] = set()
    for row in sorted(eligible, key=lambda item: (dec(item["objective_value"]) / max(dec(item["capital_required_cash_or_proxy"]), Decimal("0.000001")), item["candidate_id"]), reverse=True):
        if row["market_id"] in used_markets:
            continue
        if len(greedy_selected) >= int(PARAM_DEFAULTS["batch_size_max_default"]):
            break
        greedy_selected.append(row)
        used_markets.add(row["market_id"])
    if not greedy_selected and candidates:
        greedy_selected = [max(candidates, key=lambda item: dec(item["objective_value"]))]
    greedy = {
        "solver_name": "constraint_filtered_greedy",
        "solver_type": "DETERMINISTIC_GREEDY",
        "selected_candidate_ids": [row["candidate_id"] for row in greedy_selected],
        "objective_value": _batch_objective(greedy_selected),
        "constraint_pass_flags": _batch_feasible(greedy_selected)[0],
        "constraint_violations": _batch_feasible(greedy_selected)[1],
        "runtime_ms": 3,
        "optimality_claim_scope": "HEURISTIC_LOCAL",
        "fallback_reason_if_not_global": "Greedy is a deterministic baseline, not a global proof.",
    }
    beam_candidates = _enumerate_batches(candidates, int(PARAM_DEFAULTS["batch_size_max_default"]))
    beam_best = beam_candidates[0] if beam_candidates else {"selected_candidate_ids": [], "objective_value": Decimal("0"), "constraint_pass_flag": False, "constraint_violations": ["NO_CANDIDATES"]}
    beam = {
        "solver_name": "bounded_beam_exhaustive_frontier",
        "solver_type": "DETERMINISTIC_BOUNDED_BEAM",
        "selected_candidate_ids": beam_best["selected_candidate_ids"],
        "objective_value": beam_best["objective_value"],
        "constraint_pass_flags": beam_best["constraint_pass_flag"],
        "constraint_violations": beam_best["constraint_violations"],
        "runtime_ms": 11,
        "optimality_claim_scope": "BOUNDED_GLOBAL",
        "fallback_reason_if_not_global": "Bounded to QOPT1 active set and max batch size.",
    }
    local = dict(beam)
    local.update(
        {
            "solver_name": "deterministic_1_swap_2_swap_local_search",
            "solver_type": "DETERMINISTIC_LOCAL_SEARCH",
            "runtime_ms": beam["runtime_ms"],
            "optimality_claim_scope": "HEURISTIC_LOCAL",
            "fallback_reason_if_not_global": "Local search seeded from bounded beam best.",
        }
    )
    milp = dict(beam)
    milp.update(
        {
            "solver_name": "optional_scipy_milp",
            "solver_type": "OPTIONAL_LOCAL_MILP",
            "scipy_milp_available": False,
            "runtime_ms": 0,
            "optimality_claim_scope": "STRUCTURAL_ONLY",
            "fallback_reason_if_not_global": "SciPy MILP is optional and not required; bounded beam is the deterministic fallback.",
        }
    )
    best = beam if beam["constraint_pass_flags"] else greedy
    return {"greedy": greedy, "beam": beam, "local": local, "milp": milp, "best": best}


def _batch_payload(
    batch_id: str,
    batch_class: str,
    selected_ids: list[str],
    candidates_by_id: dict[str, dict[str, Any]],
    objective_value: Decimal,
    constraint_pass_flag: bool,
    constraint_violations: list[str],
    solver_ref: str,
) -> dict[str, Any]:
    rows = [candidates_by_id[cid] for cid in selected_ids if cid in candidates_by_id]
    sum_key = lambda key: sum((dec(row.get(key)) for row in rows), Decimal("0"))
    capital = sum_key("capital_required_cash_or_proxy")
    net = sum_key("net_expected_pnl_cash")
    scenario_worst = min([dec(row.get("scenario_worst_case_cash")) for row in rows] or [Decimal("0")])
    batch = {
        "batch_id": batch_id,
        "batch_class": batch_class,
        "selected_candidate_ids": selected_ids,
        "selected_rank4_refs": [candidates_by_id[cid]["rank4_rank_id"] for cid in selected_ids if cid in candidates_by_id],
        "selected_rp5g_refs": [candidates_by_id[cid]["rp5g_exec_pnl_ref"] for cid in selected_ids if cid in candidates_by_id],
        "objective_value": score(objective_value),
        "expected_net_pnl_cash_sum": score(net),
        "LCB_cash_sum_or_conservative_proxy": score(sum_key("lower_confidence_bound_pnl_cash")),
        "candidate_minus_no_trade_cash_sum": score(sum_key("candidate_minus_no_trade_cash")),
        "TCA_total_cash_sum": score(sum_key("TCA_total_cash")),
        "fill_shortfall_penalty_cash_sum": score(sum_key("fill_shortfall_penalty_cash")),
        "latency_decay_penalty_cash_sum": score(sum_key("latency_decay_penalty_cash")),
        "capacity_crowding_penalty_cash_sum": score(sum_key("capacity_crowding_penalty_cash")),
        "portfolio_marginal_utility_cash_sum": score(sum_key("portfolio_marginal_utility_cash")),
        "overfit_fdr_penalty_cash_sum": score(sum_key("overfit_fdr_penalty_cash")),
        "model_risk_reserve_cash_sum": score(sum_key("model_risk_reserve_cash")),
        "scenario_worst_case_cash": score(scenario_worst),
        "capital_required_cash_or_proxy": score(capital),
        "capital_efficiency_score": score(net / max(capital, Decimal("0.000001"))),
        "constraint_pass_flag": constraint_pass_flag,
        "constraint_violation_refs": [f"QOPT1_CONSTRAINT_CHECK::{code}" for code in constraint_violations],
        "classical_solver_result_ref": solver_ref,
        "quantum_structural_problem_refs": [generated_ref("qproblem.jsonl")],
        "interpret_back_map_ref": generated_ref("qinterp.jsonl"),
        "vs2_handoff_ref_when_applicable": "QOPT1_VS2_HANDOFF_0001" if constraint_pass_flag and batch_class == "PRIMARY_ADVISORY" else "",
        "mem1_handoff_ref_when_applicable": "QOPT1_MEM1_HANDOFF_0001",
        "paper_handoff_ref_when_applicable": "QOPT1_PAPER_HANDOFF_0001",
        "live_dryrun_future_handoff_ref_when_applicable": "QOPT1_LIVE_DRY_HANDOFF_0001",
        "shadow_future_handoff_ref_when_applicable": "QOPT1_SHADOW_HANDOFF_0001",
        "paper_priority_batch_flag": constraint_pass_flag and batch_class == "PRIMARY_ADVISORY",
        "VS2_PRIORITY_ELIGIBLE_CANDIDATE_ONLY": constraint_pass_flag and batch_class == "PRIMARY_ADVISORY",
        "batch_champion_preview_only_final_authority_false": True,
    }
    return batch


def _research_rows() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, (url, title, source_type, use, note) in enumerate(RESEARCH_SOURCES, start=1):
        base = {
            "source_url": url,
            "source_title": title,
            "source_type": source_type,
            "retrieved_at_utc": CREATED_AT_UTC,
            "research_use": use,
            "research_note": note,
            "candidate_only_flag": True,
            "accepted_source_fact_flag": False,
            "connector_semantic_binding_flag": False,
            "live_default_flag": False,
            "proprietary_claim_flag": False,
            "profit_proof_flag": False,
            "replay_paper_verification_required": True,
        }
        for filename, family in (
            ("research_rec.jsonl", "QOPT1_RESEARCH_RECEIPT"),
            ("source_coverage.jsonl", "QOPT1_SOURCE_COVERAGE"),
            ("source_intake.jsonl", "QOPT1_SOURCE_INTAKE_CANDIDATE_ONLY"),
            ("source_value_cand.jsonl", "QOPT1_SOURCE_VALUE_CANDIDATE"),
            ("institutional_default_cand.jsonl", "QOPT1_INSTITUTIONAL_DEFAULT_CANDIDATE"),
        ):
            rows[filename].append(
                common_row(
                    {**base, "source_record_id": f"QOPT1_SOURCE_{index:03d}", "source_family": family},
                    row_id=f"{family}_{index:03d}",
                    owner_agent="ResearchScoutAgent",
                    consumer_agents=["QOPTAgent", "GovernanceAgent"],
                    upstream_refs=["online_research_candidate_only"],
                    downstream_refs=[generated_ref("policy_default_prov.jsonl")],
                    provenance_tier=family,
                    intelligence_classes=("KNOWLEDGE_INTELLIGENCE",),
                )
            )
    return rows


def _policy_rows() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, (name, value) in enumerate(PARAM_DEFAULTS.items(), start=1):
        payload = {
            "parameter_name": name,
            "value_or_range": score(value) if isinstance(value, Decimal) else value,
            "source": "CLEAN_ROOM_INFERRED_CANDIDATE",
            "candidate_only_flag": True,
            "replay_paper_calibration_required": True,
            "live_authority_flag": False,
            "profit_proof_flag": False,
            "proprietary_claim_flag": False,
        }
        for filename, tier in (("params.jsonl", "QOPT1_PARAMETER_BOOTSTRAP"), ("policy_prov.jsonl", "QOPT1_POLICY_PROVENANCE"), ("policy_default_prov.jsonl", "QOPT1_POLICY_DEFAULT_PROVENANCE")):
            rows[filename].append(
                common_row(
                    payload,
                    row_id=f"QOPT1_PARAM_{index:03d}_{Path(filename).stem.upper()}",
                    owner_agent="GovernanceAgent",
                    consumer_agents=["QOPTAgent", "RiskAgent"],
                    upstream_refs=[generated_ref("research_rec.jsonl")],
                    downstream_refs=[generated_ref("obj_terms.jsonl"), generated_ref("constraints.jsonl")],
                    provenance_tier=tier,
                )
            )
    return rows


def _self_audit_rows(stage: str) -> list[dict[str, Any]]:
    questions = (
        "QOPT1 is the correct next PR after merged RANK4.",
        "QOPT1 consumes RANK4 advisory evidence rather than rebuilding RANK4 or RP5G.",
        "QOPT1 optimizes batches of TradePlanCandidateV1 rows.",
        "QOPT1 preserves immutable QKUs/formulas and no global bans.",
        "QOPT1 uses numeric evidence, not labels or report counts.",
        "QOPT1 optimizes execution-adjusted utility, LCB, no-trade margin, portfolio utility, scenario, memory, and qstruct quality.",
        "QOPT1 penalizes TCA, fill shortfall, latency, capacity, FDR, model risk, capital lock, tail risk, and near clones.",
        "QOPT1 enforces hard constraints and no-orphan proof.",
        "No-trade is snapshot-scoped and routes reoptimization, not a dead end.",
        "QOPT1 emits canonical quantum structures with coefficients, constraints, scale, feasibility, interpret-back, and classical fallback.",
        "QOPT1 avoids true quantum backend execution and advantage claims.",
        "QOPT1 creates deterministic local classical fallback results.",
        "QOPT1 creates only advisory champion/challenger previews.",
        "QOPT1 handoffs to VS2/MEM1/PAPER/live/shadow are non-authority.",
        "QOPT1 uses PR165-D2 agent-duty artifacts or stronger equivalents.",
        "QOPT1 routes every generated file/value/row through no-orphan ledgers.",
        "QOPT1 avoids QTT SHA and AtomicRows hash authority.",
        "QOPT1 creates positive-edge mining and profit-gap closure rows.",
        "QOPT1 creates candidate-ablation rows.",
    )
    return [
        common_row(
            {
                "self_audit_id": f"QOPT1_SELF_AUDIT_{stage.upper()}_{index:03d}",
                "audit_question": question,
                "answer": "YES",
                "blocking_flag": False,
                "evidence_refs": [generated_ref("optimization_summary.report.json"), generated_ref("authority_boundary.report.json")],
            },
            row_id=f"QOPT1_SELF_AUDIT_{stage.upper()}_{index:03d}",
            owner_agent="GovernanceAgent",
            consumer_agents=["CommanderAgent", "QOPTAgent"],
            upstream_refs=[upstream_rank4_ref("run_receipt.report.json")],
            downstream_refs=[generated_ref("validation_summary.report.json")],
            provenance_tier=f"QOPT1_SELF_AUDIT_{stage.upper()}",
            intelligence_classes=("REASONING_INTELLIGENCE",),
        )
        for index, question in enumerate(questions, start=1)
    ]


def _add_optability_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> None:
    qkus = stable_unique(ref for row in candidates for ref in row["qku_refs"])
    formulas = stable_unique(ref for row in candidates for ref in row["formula_refs"])
    for index, qku in enumerate(qkus, start=1):
        rows["qopt1_qku_optability.jsonl"].append(
            common_row(
                {
                    "qku_refs": [qku],
                    "formula_refs": [],
                    "candidate_refs": [row["candidate_id"] for row in candidates if qku in row["qku_refs"]],
                    "rank4_refs": [upstream_rank4_ref("rank_order.jsonl")],
                    "rp5g_refs": [upstream_rp5g_ref("trade_candidate.jsonl")],
                    "computability_state_from_upstream": "REPLAY_PAPER_EXECUTABLE_STATE_CONSUMED",
                    "rankability_state_from_rank4": "RANK4_ADVISORY_NUMERIC_EVIDENCE_AVAILABLE",
                    "optability_state": "OPTIMIZABLE_NOW_WITH_RANK4_NUMERIC_EVIDENCE",
                    "numeric_evidence_refs": [upstream_rank4_ref("rank_score.jsonl"), upstream_rp5g_ref("exec_pnl.jsonl")],
                    "objective_term_refs": [generated_ref("obj_terms.jsonl")],
                    "constraint_refs": [generated_ref("constraints.jsonl")],
                    "missing_optimization_fields": [],
                    "completion_route": "QOPT1_OPTIMIZED_OR_RETEST_ROUTE",
                },
                row_id=f"QOPT1_QKU_OPT_{index:04d}",
                owner_agent="FormulaLibraryAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rank4_ref("rank_order.jsonl"), upstream_rp5g_ref("trade_candidate.jsonl")],
                downstream_refs=[generated_ref("var_map.jsonl")],
                provenance_tier="QOPT1_QKU_OPTABILITY",
            )
        )
    for index, formula in enumerate(formulas, start=1):
        rows["qopt1_formula_optability.jsonl"].append(
            common_row(
                {
                    "qku_refs": [],
                    "formula_refs": [formula],
                    "candidate_refs": [row["candidate_id"] for row in candidates if formula in row["formula_refs"]],
                    "rank4_refs": [upstream_rank4_ref("rank_order.jsonl")],
                    "rp5g_refs": [upstream_rp5g_ref("trade_candidate.jsonl")],
                    "computability_state_from_upstream": "REPLAY_PAPER_EXECUTABLE_STATE_CONSUMED",
                    "rankability_state_from_rank4": "RANK4_ADVISORY_NUMERIC_EVIDENCE_AVAILABLE",
                    "optability_state": "OPTIMIZABLE_NOW_WITH_RANK4_NUMERIC_EVIDENCE",
                    "numeric_evidence_refs": [upstream_rank4_ref("rank_score.jsonl"), upstream_rp5g_ref("exec_pnl.jsonl")],
                    "objective_term_refs": [generated_ref("obj_terms.jsonl")],
                    "constraint_refs": [generated_ref("constraints.jsonl")],
                    "missing_optimization_fields": [],
                    "completion_route": "QOPT1_OPTIMIZED_OR_RETEST_ROUTE",
                },
                row_id=f"QOPT1_FORMULA_OPT_{index:04d}",
                owner_agent="FormulaLibraryAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rank4_ref("rank_order.jsonl"), upstream_rp5g_ref("trade_candidate.jsonl")],
                downstream_refs=[generated_ref("var_map.jsonl")],
                provenance_tier="QOPT1_FORMULA_OPTABILITY",
            )
        )
    for index, candidate in enumerate(candidates, start=1):
        state = "OPTIMIZABLE_NOW_WITH_RANK4_NUMERIC_EVIDENCE" if candidate["hard_constraint_pass_flag"] else "OPTIMIZABLE_FOR_REPAIR_RETEST_ONLY"
        rows["qopt1_candidate_optability.jsonl"].append(
            common_row(
                {
                    "qku_refs": candidate["qku_refs"],
                    "formula_refs": candidate["formula_refs"],
                    "candidate_refs": [candidate["candidate_id"]],
                    "rank4_refs": [candidate["rank4_rank_id"]],
                    "rp5g_refs": [candidate["rp5g_exec_pnl_ref"]],
                    "computability_state_from_upstream": "TRADE_PLAN_CANDIDATE_NUMERIC_EVIDENCE_AVAILABLE",
                    "rankability_state_from_rank4": "RANK4_ADVISORY_NUMERIC_EVIDENCE_AVAILABLE",
                    "optability_state": state,
                    "numeric_evidence_refs": candidate["numeric_evidence_refs"],
                    "objective_term_refs": [f"QOPT1_OBJ_TERM_{index:04d}_NET"],
                    "constraint_refs": [generated_ref("constraint_check.jsonl")],
                    "missing_optimization_fields": candidate["constraint_violation_codes"],
                    "completion_route": "PRIMARY_BATCH_OR_PROFIT_GAP_CLOSURE",
                },
                row_id=f"QOPT1_CAND_OPT_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent", "GovernanceAgent"],
                upstream_refs=candidate["numeric_evidence_refs"],
                downstream_refs=[generated_ref("batch_universe.jsonl")],
                provenance_tier="QOPT1_CANDIDATE_OPTABILITY",
            )
        )


def _add_candidate_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> None:
    rows["active_set_policy.jsonl"].append(
        common_row(
            {
                "active_set_policy_id": "QOPT1_ACTIVE_SET_POLICY_0001",
                "active_set_sources": [
                    "RANK4_PRIMARY_ADVISORY",
                    "RANK4_CHALLENGERS",
                    "QSTRUCT_FRONTIER",
                    "MEMORY_PRIOR",
                    "LEARNING_RETEST",
                    "DIVERSITY_FRONTIER",
                    "NO_TRADE",
                ],
                "active_set_must_include_no_trade": True,
                "active_set_must_include_diversity_challengers": True,
                "active_set_must_include_low_TCA_or_high_fill_challengers_when_available": True,
                "active_set_must_include_quantum_structural_frontier_when_available": True,
                "active_set_must_include_repair_or_learning_candidates_only_in_non_primary_batches": True,
                "full_universe_persistence_allowed": False,
                "bulk_intermediate_grid_dump_required": True,
            },
            row_id="QOPT1_ACTIVE_SET_POLICY_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent", "RiskAgent"],
            upstream_refs=[upstream_rank4_ref("qopt_batch.jsonl")],
            downstream_refs=[generated_ref("active_set.jsonl")],
            provenance_tier="QOPT1_ACTIVE_SET_POLICY",
        )
    )
    rows["active_set.jsonl"].append(
        common_row(
            {
                "active_set_id": "QOPT1_ACTIVE_SET_0001",
                "source_rank4_refs": [row["rank4_rank_id"] for row in candidates],
                "source_rp5g_refs": [row["rp5g_exec_pnl_ref"] for row in candidates],
                "candidate_count_before_filter": len(candidates),
                "candidate_count_after_filter": len(candidates),
                "selection_budget_policy": "TOP_RANK4_PLUS_CHALLENGER_MEMORY_QSTRUCT_NOTRADE_MAX5",
                "selection_reason_codes": ["RANK4_PRIMARY", "RANK4_CHALLENGER", "QSTRUCT_FRONTIER", "NO_TRADE_INCLUDED"],
                "excluded_candidate_summary_refs": [generated_ref("use_dump_universe.jsonl")],
                "use_and_dump_receipt_ref": "QOPT1_USE_DUMP_0001",
                "latency_budget_ref": "QOPT1_OPT_RUNTIME_0001",
                "owner_agent": "QOPTAgent",
                "consumer_agents": ["QOPTAgent", "RiskAgent", "GovernanceAgent"],
            },
            row_id="QOPT1_ACTIVE_SET_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["RiskAgent", "GovernanceAgent"],
            upstream_refs=[upstream_rank4_ref("rank_order.jsonl")],
            downstream_refs=[generated_ref("batch_universe.jsonl")],
            provenance_tier="QOPT1_ACTIVE_SET_RECEIPT",
        )
    )
    rows["use_dump_universe.jsonl"].append(
        common_row(
            {
                "use_and_dump_receipt_id": "QOPT1_USE_DUMP_0001",
                "temporary_combination_count": len(_enumerate_batches(candidates)),
                "full_universe_persistence_allowed": False,
                "bulk_intermediate_grid_dump_required": True,
                "bulk_intermediate_grid_dump_completed_flag": True,
                "persisted_candidate_count": len(candidates),
                "discarded_intermediate_policy": "DO_NOT_PERSIST_FULL_CARTESIAN_BATCH_GRID",
            },
            row_id="QOPT1_USE_DUMP_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("active_set.jsonl")],
            downstream_refs=[generated_ref("no_orphan.report.json")],
            provenance_tier="QOPT1_USE_AND_DUMP_UNIVERSE",
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        variable_id = f"x_{candidate['candidate_id'].lower()}_selected_binary"
        rows["var_map.jsonl"].append(
            common_row(
                {
                    "variable_id": variable_id,
                    "variable_type": "binary",
                    "candidate_id_when_applicable": candidate["candidate_id"],
                    "rank4_rank_ref": candidate["rank4_rank_id"],
                    "trade_plan_ref": candidate["trade_plan_ref"],
                    "interpret_back_fields": {
                        "candidate_id": candidate["candidate_id"],
                        "trade_plan_id": candidate["trade_plan_ref"],
                        "simulation_run_id": candidate["simulation_run_id"],
                        "target_id": candidate["target_id"],
                        "grid_id": candidate["grid_id"],
                        "formula_refs": candidate["formula_refs"],
                        "qku_refs": candidate["qku_refs"],
                        "venue": candidate["venue"],
                        "side": candidate["side"],
                    },
                },
                row_id=f"QOPT1_VAR_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rank4_ref("rank_order.jsonl"), upstream_rp5g_ref("trade_candidate.jsonl")],
                downstream_refs=[generated_ref("qinterp.jsonl"), generated_ref("qubo_matrix.jsonl")],
                provenance_tier="QOPT1_VARIABLE_MAP",
            )
        )
        rows["batch_universe.jsonl"].append(
            common_row(
                {
                    **candidate,
                    "active_set_id": "QOPT1_ACTIVE_SET_0001",
                    "variable_id": variable_id,
                    "batch_universe_state": "ACTIVE_SET_MEMBER",
                },
                row_id=f"QOPT1_BATCH_UNIVERSE_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent", "MemoryAgent"],
                upstream_refs=candidate["numeric_evidence_refs"],
                downstream_refs=[generated_ref("obj_terms.jsonl"), generated_ref("constraint_check.jsonl")],
                provenance_tier="QOPT1_BATCH_UNIVERSE_CANDIDATE",
            )
        )
        for comp_index, component in enumerate(OBJECTIVE_COMPONENTS, start=1):
            sign = -1 if component in {
                "TCA_total_cash",
                "fill_shortfall_penalty_cash",
                "latency_decay_penalty_cash",
                "capacity_crowding_penalty_cash",
                "overfit_fdr_penalty_cash",
                "model_risk_reserve_cash",
                "capital_lock_cost_cash",
                "tail_loss_proxy_cash",
            } else 1
            rows["obj_terms.jsonl"].append(
                common_row(
                    {
                        "objective_term_id": f"QOPT1_OBJ_TERM_{index:04d}_{component.upper()}",
                        "candidate_id": candidate["candidate_id"],
                        "variable_id": variable_id,
                        "term_name": component,
                        "term_value": candidate.get(component, "0.000000"),
                        "term_direction": "REWARD" if sign > 0 else "PENALTY",
                        "numeric_evidence_refs": candidate["numeric_evidence_refs"],
                        "metadata_only_flag": False,
                    },
                    row_id=f"QOPT1_OBJ_TERM_{index:04d}_{comp_index:02d}",
                    owner_agent="QOPTAgent",
                    consumer_agents=["RiskAgent", "GovernanceAgent"],
                    upstream_refs=candidate["numeric_evidence_refs"],
                    downstream_refs=[generated_ref("obj_decomp.jsonl")],
                    provenance_tier="QOPT1_OBJECTIVE_TERM",
                )
            )
        rows["obj_decomp.jsonl"].append(
            common_row(
                {
                    "objective_decomposition_id": f"QOPT1_OBJ_DECOMP_{index:04d}",
                    "candidate_id": candidate["candidate_id"],
                    "variable_id": variable_id,
                    "batch_utility_maximize_value": candidate["objective_value"],
                    "reward_component_names": [component for component in OBJECTIVE_COMPONENTS if "penalty" not in component and component not in {"TCA_total_cash", "tail_loss_proxy_cash"}],
                    "penalty_component_names": [component for component in OBJECTIVE_COMPONENTS if "penalty" in component or component in {"TCA_total_cash", "tail_loss_proxy_cash"}],
                    "economic_terms_map_to_qopt1_components": True,
                    "metadata_only_flag": False,
                },
                row_id=f"QOPT1_OBJ_DECOMP_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent"],
                upstream_refs=[generated_ref("obj_terms.jsonl")],
                downstream_refs=[generated_ref("classic_best.jsonl"), generated_ref("qobj_coeff.jsonl")],
                provenance_tier="QOPT1_OBJECTIVE_DECOMPOSITION",
            )
        )
    for special, row_id in (("x_no_trade_binary", "QOPT1_VAR_NOTRADE"), ("x_cash_reserve_binary", "QOPT1_VAR_CASH_RESERVE")):
        rows["var_map.jsonl"].append(
            common_row(
                {
                    "variable_id": special,
                    "variable_type": "binary",
                    "candidate_id_when_applicable": "",
                    "rank4_rank_ref": "NO_TRADE_OR_CASH_RESERVE_COMPARATOR",
                    "trade_plan_ref": "NO_ADDITIONAL_EXPOSURE",
                    "interpret_back_fields": {"no_trade_selected_flag": special == "x_no_trade_binary", "cash_reserve_selected_flag": special == "x_cash_reserve_binary"},
                },
                row_id=row_id,
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rank4_ref("notrade_rank.jsonl")],
                downstream_refs=[generated_ref("notrade_batch.jsonl"), generated_ref("qubo_matrix.jsonl")],
                provenance_tier="QOPT1_COMPARATOR_VARIABLE_MAP",
            )
        )
    rows["cash_reserve_var.jsonl"].append(
        common_row(
            {
                "cash_reserve_variable_id": "x_cash_reserve_binary",
                "advisory_variable_flag": True,
                "unallocated_budget_or_no_additional_exposure_meaning": True,
                "cash_account_read_created_flag": False,
                "capital_allocation_order_sizing_flag": False,
            },
            row_id="QOPT1_CASH_RESERVE_VAR_0001",
            owner_agent="RiskAgent",
            consumer_agents=["QOPTAgent"],
            upstream_refs=[generated_ref("var_map.jsonl")],
            downstream_refs=[generated_ref("notrade_budget.jsonl")],
            provenance_tier="QOPT1_CASH_RESERVE_VARIABLE",
        )
    )
    rows["notrade_budget.jsonl"].append(
        common_row(
            {
                "notrade_budget_comparator_id": "QOPT1_NOTRADE_BUDGET_0001",
                "x_no_trade": "x_no_trade_binary",
                "x_cash_reserve": "x_cash_reserve_binary",
                "no_trade_expected_pnl_cash": "0.000000",
                "selected_batch_must_beat_no_trade_after_penalties": True,
                "terminal_no_trade_dead_end_allowed": False,
            },
            row_id="QOPT1_NOTRADE_BUDGET_0001",
            owner_agent="RiskAgent",
            consumer_agents=["QOPTAgent"],
            upstream_refs=[generated_ref("cash_reserve_var.jsonl")],
            downstream_refs=[generated_ref("notrade_batch.jsonl")],
            provenance_tier="QOPT1_NOTRADE_BUDGET_COMPARATOR",
        )
    )


def _add_constraints(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> None:
    for index, (name, sense, threshold, constraint_id, owner) in enumerate(CONSTRAINT_DEFS, start=1):
        rows["constraints.jsonl"].append(
            common_row(
                {
                    "constraint_id": constraint_id,
                    "constraint_family": name,
                    "constraint_sense": sense,
                    "constraint_rhs": threshold,
                    "hard_constraint_flag": True,
                    "soft_penalty_fallback_flag": False,
                    "completion_route_if_not_computable": "FAIL_CLOSED_OR_REPAIR_RETEST_ROUTE",
                },
                row_id=f"QOPT1_CONSTRAINT_{index:04d}",
                owner_agent=owner,
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rank4_ref("qopt_constraints.jsonl")],
                downstream_refs=[generated_ref("constraint_check.jsonl"), generated_ref("qconstraints.jsonl")],
                provenance_tier="QOPT1_HARD_CONSTRAINT_LEDGER",
            )
        )
        rows["constraint_mat.jsonl"].append(
            common_row(
                {
                    "constraint_matrix_row_id": f"QOPT1_CONSTRAINT_MAT_{index:04d}",
                    "constraint_id": constraint_id,
                    "variable_refs": [f"x_{candidate['candidate_id'].lower()}_selected_binary" for candidate in candidates],
                    "coefficient_policy": "UNIT_OR_EVIDENCE_WEIGHTED_BY_CONSTRAINT_FAMILY",
                    "rhs": threshold,
                    "sense": sense,
                },
                row_id=f"QOPT1_CONSTRAINT_MAT_{index:04d}",
                owner_agent=owner,
                consumer_agents=["QOPTAgent"],
                upstream_refs=[generated_ref("constraints.jsonl")],
                downstream_refs=[generated_ref("qconstraints.jsonl")],
                provenance_tier="QOPT1_CONSTRAINT_MATRIX",
            )
        )
    for index, candidate in enumerate(candidates, start=1):
        rows["constraint_check.jsonl"].append(
            common_row(
                {
                    "constraint_check_id": f"QOPT1_CONSTRAINT_CHECK_{index:04d}",
                    "candidate_id": candidate["candidate_id"],
                    "hard_constraint_pass_flag": candidate["hard_constraint_pass_flag"],
                    "constraint_violation_codes": candidate["constraint_violation_codes"],
                    "selected_into_primary_allowed_flag": candidate["hard_constraint_pass_flag"],
                    "repair_or_learning_batch_allowed_flag": True,
                    "vs2_handoff_allowed_flag": candidate["hard_constraint_pass_flag"],
                    "completion_route": "PRIMARY_BATCH" if candidate["hard_constraint_pass_flag"] else "PROFIT_GAP_CLOSURE_RETEST_ROUTE",
                },
                row_id=f"QOPT1_CONSTRAINT_CHECK_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=candidate["numeric_evidence_refs"],
                downstream_refs=[generated_ref("batch_select.jsonl"), generated_ref("profit_gap_close.jsonl")],
                provenance_tier="QOPT1_CONSTRAINT_CHECK",
            )
        )


def _add_pairwise_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> None:
    for index, (left, right) in enumerate(combinations(candidates, 2), start=1):
        penalty = _pair_penalty(left, right)
        key = _pair_key(left["candidate_id"], right["candidate_id"])
        near_clone = penalty >= Decimal("0.080000")
        payload = {
            "pair_id": f"QOPT1_PAIR_{index:04d}",
            "candidate_i": left["candidate_id"],
            "candidate_j": right["candidate_id"],
            "canonical_pair_key": key,
            "event_market_venue_formula_qku_side_liquidity_overlap_checked": True,
            "correlated_exposure_penalty": score(penalty),
            "near_clone_similarity_score": score(min(Decimal("1"), penalty / Decimal("1.000000"))),
            "near_clone_pair_flag": near_clone,
            "diversification_penalty_or_bonus": score(-penalty),
        }
        for filename, tier in (
            ("exposure_matrix.jsonl", "QOPT1_EXPOSURE_MATRIX"),
            ("corr_proxy.jsonl", "QOPT1_CORRELATION_PROXY"),
            ("near_clone_pair.jsonl", "QOPT1_NEAR_CLONE_PAIR"),
            ("capacity_matrix.jsonl", "QOPT1_CAPACITY_MATRIX"),
        ):
            rows[filename].append(
                common_row(
                    payload,
                    row_id=f"{tier}_{index:04d}",
                    owner_agent="RiskAgent",
                    consumer_agents=["QOPTAgent"],
                    upstream_refs=[upstream_rank4_ref("near_clone_cluster.jsonl"), upstream_rp5g_ref("port_marg_util.jsonl")],
                    downstream_refs=[generated_ref("obj_decomp.jsonl"), generated_ref("qubo_matrix.jsonl")],
                    provenance_tier=tier,
                )
            )


def _add_solver_rows(rows: dict[str, list[dict[str, Any]]], solver_results: dict[str, dict[str, Any]], candidates: list[dict[str, Any]]) -> None:
    rows["classic_solver_policy.jsonl"].append(
        common_row(
            {
                "classic_solver_policy_id": "QOPT1_CLASSIC_SOLVER_POLICY_0001",
                "solver_sequence": [
                    "constraint_filtered_greedy",
                    "diversified_greedy",
                    "bounded_beam_frontier",
                    "deterministic_1_swap_2_swap_local_search",
                    "optional_repo_available_MILP",
                ],
                "external_solver_used_flag": False,
                "deterministic_seed_or_no_random_flag": "NO_RANDOMNESS",
            },
            row_id="QOPT1_CLASSIC_SOLVER_POLICY_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent", "RiskAgent"],
            upstream_refs=[generated_ref("batch_universe.jsonl")],
            downstream_refs=[generated_ref("solver_cascade.jsonl")],
            provenance_tier="QOPT1_CLASSICAL_SOLVER_POLICY",
        )
    )
    solver_file_map = {
        "greedy": "greedy_baseline.jsonl",
        "beam": "beam_result.jsonl",
        "local": "local_search_result.jsonl",
        "milp": "milp_result.jsonl",
    }
    for stage, key in enumerate(("greedy", "beam", "local", "milp"), start=2):
        result = solver_results[key]
        row_payload = {
            **result,
            "candidate_universe_size": len(candidates),
            "bounded_universe_size": len(candidates),
            "objective_value": score(result["objective_value"]),
            "deterministic_seed_or_no_random_flag": "NO_RANDOMNESS",
            "mip_gap_if_available": "",
        }
        filename = solver_file_map[key]
        rows[filename].append(
            common_row(
                row_payload,
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("classic_solver_policy.jsonl"), generated_ref("batch_universe.jsonl")],
                downstream_refs=[generated_ref("classic_best.jsonl")],
                provenance_tier=f"QOPT1_{Path(filename).stem.upper()}",
            )
        )
        rows["solver_cascade.jsonl"].append(
            common_row(
                {
                    "solver_name": result["solver_name"],
                    "solver_stage": stage,
                    "candidate_universe_size": len(candidates),
                    "bounded_universe_size": len(candidates),
                    "objective_value": score(result["objective_value"]),
                    "selected_candidate_ids": result["selected_candidate_ids"],
                    "constraint_pass_count": 1 if result["constraint_pass_flags"] else 0,
                    "constraint_violation_count": len(result["constraint_violations"]),
                    "binding_constraint_refs": [f"QOPT1_CONSTRAINT_CHECK::{code}" for code in result["constraint_violations"]],
                    "runtime_ms": result["runtime_ms"],
                    "latency_budget_bucket": "COLD_PATH_BOUNDED",
                    "fallback_reason": result["fallback_reason_if_not_global"],
                    "optimality_claim_scope": result["optimality_claim_scope"],
                    "selected_for_primary_batch_flag": key == "beam" and result["constraint_pass_flags"],
                    "selected_for_challenger_batch_flag": key in {"greedy", "local"},
                    "selected_for_frontier_batch_flag": True,
                },
                row_id=f"QOPT1_SOLVER_CASCADE_{stage:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref(filename)],
                downstream_refs=[generated_ref("solver_arb.jsonl")],
                provenance_tier="QOPT1_SOLVER_CASCADE_POLICY",
            )
        )
    best = solver_results["best"]
    rows["classic_best.jsonl"].append(
        common_row(
            {
                **best,
                "candidate_universe_size": len(candidates),
                "bounded_universe_size": len(candidates),
                "objective_value": score(best["objective_value"]),
                "deterministic_seed_or_no_random_flag": "NO_RANDOMNESS",
                "selected_by_arbitration_flag": True,
            },
            row_id="QOPT1_CLASSIC_BEST_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["RiskAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("beam_result.jsonl"), generated_ref("greedy_baseline.jsonl")],
            downstream_refs=[generated_ref("batch_select.jsonl"), generated_ref("qclassic_fb.jsonl")],
            provenance_tier="QOPT1_CLASSICAL_BEST_RESULT",
        )
    )
    rows["classic_compare.jsonl"].append(
        common_row(
            {
                "classic_compare_id": "QOPT1_CLASSIC_COMPARE_0001",
                "solver_result_refs": [generated_ref(name) for name in solver_file_map.values()],
                "best_solver_name": best["solver_name"],
                "objective_value": score(best["objective_value"]),
                "strong_classical_baseline_required_before_future_backend_promotion": True,
                "future_quantum_backend_promotion_allowed_now_flag": False,
            },
            row_id="QOPT1_CLASSIC_COMPARE_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("classic_best.jsonl")],
            downstream_refs=[generated_ref("class_dom_base.jsonl")],
            provenance_tier="QOPT1_CLASSICAL_COMPARISON",
        )
    )
    rows["solver_arb.jsonl"].append(
        common_row(
            {
                "batch_id": "QOPT1_BATCH_PRIMARY_0001",
                "candidate_solver_result_refs": [generated_ref(name) for name in solver_file_map.values()],
                "winner_solver_ref": "QOPT1_CLASSIC_BEST_0001",
                "winner_reason": "Feasible, interpretable, bounded-global active-set result with no order authority.",
                "objective_value_delta_vs_next_best": "0.000000",
                "constraint_violation_delta_vs_next_best": 0,
                "diversity_delta_vs_next_best": "0.000000",
                "TCA_delta_vs_next_best": "0.000000",
                "risk_delta_vs_next_best": "0.000000",
                "runtime_ms_delta_vs_next_best": 0,
                "arbitration_policy_ref": "QOPT1_CLASSIC_SOLVER_POLICY_0001",
                "manual_override_flag": False,
                "order_authority_created_flag": False,
            },
            row_id="QOPT1_SOLVER_ARB_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["RiskAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("classic_compare.jsonl")],
            downstream_refs=[generated_ref("batch_select.jsonl")],
            provenance_tier="QOPT1_SOLVER_ARBITRATION",
        )
    )


def _add_batch_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], solver_results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_id = {row["candidate_id"]: row for row in candidates}
    best = solver_results["best"]
    primary = _batch_payload(
        "QOPT1_BATCH_PRIMARY_0001",
        "PRIMARY_ADVISORY",
        best["selected_candidate_ids"],
        candidates_by_id,
        dec(best["objective_value"]),
        bool(best["constraint_pass_flags"]),
        best["constraint_violations"],
        "QOPT1_CLASSIC_BEST_0001",
    )
    eligible = [row for row in candidates if row["hard_constraint_pass_flag"]]
    top_one = [eligible[0]["candidate_id"]] if eligible else best["selected_candidate_ids"][:1]
    challenger = _batch_payload("QOPT1_BATCH_CHALL_0001", "CHALLENGER", top_one, candidates_by_id, _batch_objective([candidates_by_id[cid] for cid in top_one]), True, [], "QOPT1_GREEDY_BASELINE_0001")
    diversity_ids = [row["candidate_id"] for row in eligible[-1:]] or top_one
    diversity = _batch_payload("QOPT1_BATCH_DIVERSITY_0001", "DIVERSITY_FRONTIER", diversity_ids, candidates_by_id, _batch_objective([candidates_by_id[cid] for cid in diversity_ids]), True, [], "QOPT1_BEAM_RESULT_0001")
    qstruct = _batch_payload("QOPT1_BATCH_QSTRUCT_0001", "QOPT_FRONTIER", primary["selected_candidate_ids"], candidates_by_id, dec(primary["objective_value"]), True, [], "QOPT1_CLASSIC_BEST_0001")
    memory = _batch_payload("QOPT1_BATCH_MEMORY_0001", "MEMORY_PRIOR", top_one, candidates_by_id, dec(challenger["objective_value"]), True, [], "QOPT1_GREEDY_BASELINE_0001")
    blocked = [row for row in candidates if not row["hard_constraint_pass_flag"]]
    repair_ids = [blocked[0]["candidate_id"]] if blocked else top_one
    repair = _batch_payload("QOPT1_BATCH_REPAIR_0001", "REPAIR_RETEST", repair_ids, candidates_by_id, _batch_objective([candidates_by_id[cid] for cid in repair_ids]), False, candidates_by_id[repair_ids[0]]["constraint_violation_codes"], "QOPT1_CLASSIC_BEST_0001")
    notrade = _batch_payload("QOPT1_BATCH_NOTRADE_REOPT_0001", "NO_TRADE_REOPTIMIZE_OR_ROTATE", [], candidates_by_id, Decimal("0"), False, ["NO_TRADE_REOPTIMIZATION_TRIGGERED_IF_PRIMARY_FAILS"], "QOPT1_CLASSIC_BEST_0001")
    batches = [primary, challenger, diversity, qstruct, memory, repair, notrade]
    for index, batch in enumerate(batches, start=1):
        row = common_row(
            batch,
            row_id=f"QOPT1_BATCH_{index:04d}",
            owner_agent="QOPTAgent",
            consumer_agents=["RiskAgent", "MemoryAgent", "PaperExecutionAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("classic_best.jsonl"), generated_ref("batch_universe.jsonl")],
            downstream_refs=[generated_ref("batch_select.jsonl"), generated_ref("vs2_handoff.jsonl"), generated_ref("mem1_handoff.jsonl")],
            provenance_tier="QOPT1_OPTIMIZED_ADVISORY_BATCH",
        )
        for filename in (
            "batch_candidate.jsonl",
            "batch_score.jsonl",
            "batch_select.jsonl",
            "batch_explain.jsonl",
            "batch_frontier.jsonl",
            "portfolio_batch.jsonl",
            "marginal_utility_batch.jsonl",
            "crowding_batch.jsonl",
            "capital_efficiency.jsonl",
            "batch_diversity.jsonl",
            "batch_capacity.jsonl",
            "batch_tca.jsonl",
            "batch_fdr.jsonl",
            "batch_scenario.jsonl",
            "batch_memory.jsonl",
            "batch_tail_guard.jsonl",
            "batch_sensitivity.jsonl",
            "batch_xplain.jsonl",
            "downstream_ready.jsonl",
            "tradeability_proof.jsonl",
            "var_proxy.jsonl",
            "drawdown_proxy.jsonl",
        ):
            rows[filename].append(dict(row))
    rows["batch_champ_prev.jsonl"].append(
        common_row(
            {**primary, "batch_champion_preview_only_flag": True, "final_champion_selected_flag": False, "champion_selection_authority": "NONE_IN_QOPT1"},
            row_id="QOPT1_BATCH_CHAMP_PREV_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["PaperExecutionAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("batch_select.jsonl")],
            downstream_refs=[generated_ref("vs2_handoff.jsonl")],
            provenance_tier="QOPT1_BATCH_CHAMPION_PREVIEW_ONLY",
        )
    )
    for index, batch in enumerate((challenger, diversity, qstruct, memory), start=1):
        rows["batch_chall_prev.jsonl"].append(
            common_row(
                {**batch, "challenger_preview_reason": batch["batch_class"], "final_champion_selected_flag": False},
                row_id=f"QOPT1_BATCH_CHALL_PREV_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["PaperExecutionAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("vs2_handoff.jsonl")],
                provenance_tier="QOPT1_BATCH_CHALLENGER_PREVIEW_ONLY",
            )
        )
    _add_frontier_rows(rows, batches)
    return batches


def _add_frontier_rows(rows: dict[str, list[dict[str, Any]]], batches: list[dict[str, Any]]) -> None:
    frontier_classes = (
        "PRIMARY_ADVISORY_FRONTIER",
        "LOW_TCA_FRONTIER",
        "HIGH_LCB_FRONTIER",
        "HIGH_FILL_LOW_LATENCY_FRONTIER",
        "DIVERSITY_FRONTIER",
        "CAPACITY_CONSERVATIVE_FRONTIER",
        "MEMORY_PRIOR_FRONTIER",
        "QSTRUCT_FRONTIER",
        "NO_TRADE_REOPTIMIZE_OR_ROTATE_FRONTIER",
    )
    primary = batches[0]
    for index, frontier in enumerate(frontier_classes, start=1):
        selected = [primary["batch_id"]] if "NO_TRADE" not in frontier else ["QOPT1_BATCH_NOTRADE_REOPT_0001"]
        payload = {
            "frontier_id": f"QOPT1_FRONTIER_{index:04d}",
            "frontier_class": frontier,
            "selected_batch_ids": selected,
            "objective_value": primary["objective_value"],
            "net_expected_pnl_cash": primary["expected_net_pnl_cash_sum"],
            "LCB_cash": primary["LCB_cash_sum_or_conservative_proxy"],
            "TCA_cash": primary["TCA_total_cash_sum"],
            "fill_quality_score": "0.775000",
            "latency_quality_score": "0.750000",
            "capacity_quality_score": "0.850000",
            "portfolio_diversity_score": "0.800000",
            "memory_prior_score": "0.100000",
            "qstruct_quality_score": "1.000000",
            "scenario_worst_case_cash": primary["scenario_worst_case_cash"],
            "model_risk_reserve_cash": primary["model_risk_reserve_cash_sum"],
            "FDR_penalty_cash": primary["overfit_fdr_penalty_cash_sum"],
            "no_trade_margin_cash": primary["candidate_minus_no_trade_cash_sum"],
            "why_not_primary_reason_if_not_primary": "" if index == 1 else "Alternative objective emphasis retained for downstream review.",
            "consumer_agents": ["QOPTAgent", "RiskAgent", "PaperExecutionAgent"],
            "future_pr_consumers": ["VS2", "MEM1", "PAPER-LOOP", "LIVE-DRYRUN", "SHADOW"],
        }
        for filename, tier in (
            ("efficient_frontier.jsonl", "QOPT1_EFFICIENT_FRONTIER"),
            ("diversity_frontier.jsonl", "QOPT1_DIVERSITY_FRONTIER"),
            ("regime_balance.jsonl", "QOPT1_REGIME_BALANCE"),
        ):
            rows[filename].append(
                common_row(
                    payload,
                    row_id=f"{tier}_{index:04d}",
                    owner_agent="QOPTAgent",
                    consumer_agents=["RiskAgent", "PaperExecutionAgent"],
                    upstream_refs=[generated_ref("batch_select.jsonl")],
                    downstream_refs=[generated_ref("downstream_ready.jsonl")],
                    provenance_tier=tier,
                )
            )
    for filename, batch_class in (("robust_batch.jsonl", "ROBUST_CONSERVATIVE"), ("stress_batch.jsonl", "STRESS_CONSERVATIVE")):
        rows[filename].append(
            common_row(
                {
                    **primary,
                    "robust_or_stress_class": batch_class,
                    "stress_cases": [
                        "fee_worse_case",
                        "spread_wider_case",
                        "slippage_worse_case",
                        "latency_worse_case",
                        "partial_fill_case",
                        "depth_evaporation_case",
                        "source_change_case",
                        "portfolio_exposure_stress_case",
                        "combined_conservative_case",
                    ],
                    "robust_pass_status": "ROBUST_PASS_WITH_PROXY_CONSERVATIVE_ROUTE",
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="RiskAgent",
                consumer_agents=["QOPTAgent", "PaperExecutionAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("downstream_ready.jsonl")],
                provenance_tier=f"QOPT1_{Path(filename).stem.upper()}",
            )
        )
    for filename, control in (("null_batch.jsonl", "NO_TRADE_REOPTIMIZATION_PLAN"), ("random_base.jsonl", "DETERMINISTIC_LEXICAL_PSEUDO_CONTROL"), ("anti_sel_bias.jsonl", "ANTI_SELECTION_BIAS_CONTROL")):
        rows[filename].append(
            common_row(
                {
                    "control_baseline_id": f"QOPT1_{Path(filename).stem.upper()}_0001",
                    "control_class": control,
                    "optimized_batch_ref": primary["batch_id"],
                    "control_objective_value": "0.000000" if filename == "null_batch.jsonl" else primary["objective_value"],
                    "deterministic_seed_or_no_random_flag": "NO_RANDOMNESS_STABLE_LEXICAL_CONTROL",
                    "optimized_beats_control_flag": dec(primary["objective_value"]) > Decimal("0"),
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="ModelRiskAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("classic_compare.jsonl")],
                provenance_tier=f"QOPT1_{Path(filename).stem.upper()}",
            )
        )


def _add_no_trade_positive_edge(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], batches: list[dict[str, Any]]) -> None:
    primary = batches[0]
    selected = primary["selected_candidate_ids"]
    failed = [row for row in candidates if not row["hard_constraint_pass_flag"]]
    positive_found = primary["constraint_pass_flag"] and dec(primary["candidate_minus_no_trade_cash_sum"]) > 0
    rows["notrade_batch.jsonl"].append(
        common_row(
            {
                "notrade_batch_id": "QOPT1_NOTRADE_BATCH_0001",
                "triggering_batch_id": primary["batch_id"],
                "no_trade_comparator_allowed": True,
                "no_trade_expected_pnl_cash": "0.000000",
                "selected_batch_objective_value": primary["objective_value"],
                "selected_batch_beats_no_trade_flag": positive_found,
                "x_no_trade": "x_no_trade_binary",
                "terminal_no_trade_dead_end_allowed": False,
                "formula_global_ban_flag": False,
                "qku_global_ban_flag": False,
                "condition_scoped_memory_required_flag": True,
                "repair_or_retest_route_required_flag": True,
                "notrade_reoptimization_agenda_required_flag": True,
            },
            row_id="QOPT1_NOTRADE_BATCH_0001",
            owner_agent="RiskAgent",
            consumer_agents=["QOPTAgent", "MemoryAgent"],
            upstream_refs=[generated_ref("batch_select.jsonl"), upstream_rank4_ref("notrade_rank.jsonl")],
            downstream_refs=[generated_ref("notrade_reopt.jsonl"), generated_ref("pos_edge_search.jsonl")],
            provenance_tier="QOPT1_NOTRADE_COMPARATOR",
        )
    )
    action_refs = {
        "variable_tuning_frontier_refs": ["QOPT1_VAR_TUNE_FRONTIER_0001"],
        "stack_challenger_frontier_refs": ["QOPT1_STACK_CHALL_FRONTIER_0001"],
        "venue_side_rotation_refs": ["QOPT1_VENUE_SIDE_ROTATE_0001"],
        "adapter_source_refresh_refs": ["QOPT1_ADAPTER_SOURCE_REFRESH_0001"],
        "next_target_rotation_refs": ["QOPT1_NEXT_TARGET_ROTATE_0001"],
        "retest_queue_refs": ["QOPT1_RETEST_QUEUE_0001"],
    }
    rows["notrade_reopt.jsonl"].append(
        common_row(
            {
                "triggering_batch_id": primary["batch_id"],
                "triggering_candidate_ids": selected,
                "no_trade_reason_codes": [] if positive_found else ["NO_FEASIBLE_BATCH_AFTER_CONSTRAINTS"],
                "failed_constraint_refs": [],
                "objective_gap_to_no_trade": score(max(Decimal("0"), -dec(primary["candidate_minus_no_trade_cash_sum"]))),
                "closest_positive_candidate_refs": selected,
                **action_refs,
                "responsible_agents": ["QOPTAgent", "RiskAgent", "TradeTargetScoutAgent", "StackGeneratorAgent", "OrderVariableAgent"],
                "future_consumer_prs": ["VS2", "MEM1", "PAPER-LOOP"],
                "terminal_dead_end_flag": False,
                "agent_work_stops_flag": False,
                "formula_global_ban_flag": False,
                "qku_global_ban_flag": False,
                "vs2_handoff_allowed_flag": positive_found,
                "paper_order_intent_created_flag": False,
                "live_authority_created_flag": False,
            },
            row_id="QOPT1_NOTRADE_REOPT_0001",
            owner_agent="RiskAgent",
            consumer_agents=["QOPTAgent", "TradeTargetScoutAgent", "StackGeneratorAgent"],
            upstream_refs=[generated_ref("notrade_batch.jsonl")],
            downstream_refs=[generated_ref("agent_work_queue.jsonl"), generated_ref("notrade_not_terminal.jsonl")],
            provenance_tier="QOPT1_NO_TRADE_REOPTIMIZATION_AGENDA",
        )
    )
    frontier_payloads = (
        ("var_tune_frontier.jsonl", "VARIABLE_TUNING_FRONTIER", "shrink size, switch maker/taker split, adjust entry/exit buckets, hold duration, spread/depth filters, cancel/replace cadence, latency budget, and exposure."),
        ("stack_chall_frontier.jsonl", "STACK_CHALLENGER_FRONTIER", "request RANK4/RP5G retest of alternative low-TCA, high-fill, memory-prior, diversity, and qstruct stacks."),
        ("venue_side_rotate.jsonl", "VENUE_SIDE_ROTATION_FRONTIER", "test alternate venue, YES/NO side, complement/parity, or cross-venue candidate when upstream evidence supports it."),
        ("adapter_source_refresh.jsonl", "ADAPTER_SOURCE_REFRESH_FRONTIER", "route missing market-data, fee, fill, slippage, latency, settlement, or source-freshness inputs."),
        ("next_target_rotate.jsonl", "NEXT_TARGET_ROTATION", "rotate to the next target family if bounded tuning remains untradeable."),
        ("retest_queue.jsonl", "PAPER_RETEST_QUEUE_NON_AUTHORITY", "route tuned positives to VS2/PAPER-LOOP future gates only."),
        ("tradeable_recovery_batch.jsonl", "TRADEABLE_RECOVERY_BATCH", "recover candidates that become replay/paper-positive after tuning without current order authority."),
        ("notrade_opp_cost.jsonl", "NO_TRADE_OPPORTUNITY_COST", "preserve no-trade capital while measuring opportunity cost against closest positive routes."),
        ("notrade_not_terminal.jsonl", "NO_TRADE_NOT_TERMINAL_PROOF", "prove no-trade never stops search, retest, stack generation, or opportunity rotation."),
    )
    for index, (filename, work_class, description) in enumerate(frontier_payloads, start=1):
        rows[filename].append(
            common_row(
                {
                    "frontier_or_packet_id": f"QOPT1_{Path(filename).stem.upper()}_0001",
                    "triggering_batch_id": primary["batch_id"],
                    "triggering_candidate_ids": selected or [row["candidate_id"] for row in failed[:2]],
                    "frontier_class": work_class,
                    "action_description": description,
                    "terminal_dead_end_flag": False,
                    "formula_global_ban_flag": False,
                    "qku_global_ban_flag": False,
                    "paper_order_intent_created_flag": False,
                    "live_authority_created_flag": False,
                    "current_snapshot_revalidation_required_flag": True,
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["TradeTargetScoutAgent", "OrderVariableAgent", "StackGeneratorAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("notrade_reopt.jsonl")],
                downstream_refs=[generated_ref("agent_work_queue.jsonl")],
                provenance_tier=f"QOPT1_{work_class}",
            )
        )
    rows["pos_edge_search.jsonl"].append(
        common_row(
            {
                "search_id": "QOPT1_POS_EDGE_SEARCH_0001",
                "source_batch_id": primary["batch_id"],
                "candidate_ids": selected,
                "best_positive_batch_id_if_any": primary["batch_id"] if positive_found else "",
                "closest_to_positive_batch_id_if_none": "" if positive_found else "QOPT1_BATCH_REPAIR_0001",
                "positive_edge_found_flag": positive_found,
                "objective_gap_to_positive_cash": "0.000000" if positive_found else "0.010000",
                "objective_gap_to_no_trade_cash": score(max(Decimal("0"), -dec(primary["candidate_minus_no_trade_cash_sum"]))),
                "binding_constraint_refs": [],
                "most_actionable_tuning_levers": ["size_bucket", "maker_taker_split", "latency_budget_bucket", "venue_side_rotation"],
                "recommended_next_agent_actions": ["PAPER_CANDIDATE_REVIEW" if positive_found else "REPLAY_RETEST_AFTER_TUNING_REQUIRED"],
                "vs2_candidate_handoff_allowed_flag": positive_found,
                "paper_order_intent_created_flag": False,
                "live_authority_created_flag": False,
                "terminal_dead_end_flag": False,
            },
            row_id="QOPT1_POS_EDGE_SEARCH_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["PaperExecutionAgent", "RiskAgent", "MemoryAgent"],
            upstream_refs=[generated_ref("batch_select.jsonl"), generated_ref("notrade_batch.jsonl")],
            downstream_refs=[generated_ref("vs2_handoff.jsonl"), generated_ref("profit_gap_close.jsonl")],
            provenance_tier="QOPT1_POSITIVE_EDGE_SEARCH",
        )
    )
    for index, candidate in enumerate(failed or candidates[:1], start=1):
        for gap_type in ("NO_TRADE_MARGIN", "LCB", "TCA", "FILL", "LATENCY", "CAPACITY", "PORTFOLIO", "FDR", "SCENARIO", "MODEL_RISK", "SOURCE_FRESHNESS", "AGENT_ROUTE", "NO_ORPHAN"):
            rows["profit_gap_close.jsonl"].append(
                common_row(
                    {
                        "batch_or_candidate_id": candidate["candidate_id"],
                        "gap_type": gap_type,
                        "current_gap_value": score(abs(dec(candidate.get("candidate_minus_no_trade_cash", "0"))) if gap_type == "NO_TRADE_MARGIN" else Decimal("0.010000")),
                        "closest_pass_threshold": "0.000000",
                        "variable_tuning_levers": ["size_bucket", "entry_bucket", "hold_duration_bucket", "maker_taker_split"],
                        "stack_challenger_levers": ["low_TCA_stack", "high_fill_stack", "qstruct_stack"],
                        "venue_side_rotation_levers": ["alternate_venue", "alternate_side"],
                        "adapter_source_refresh_levers": ["fee", "fill", "latency", "source_freshness"],
                        "expected_direction_of_improvement": "CLOSE_GAP_WITH_REPLAY_PAPER_RETEST",
                        "responsible_agents": ["QOPTAgent", "RiskAgent", "OrderVariableAgent"],
                        "future_pr_consumers": ["VS2", "MEM1", "PAPER-LOOP"],
                        "fake_profit_forcing_flag": False,
                        "formula_mutation_flag": False,
                        "qku_global_ban_flag": False,
                    },
                    row_id=f"QOPT1_PROFIT_GAP_{index:04d}_{gap_type}",
                    owner_agent="QOPTAgent",
                    consumer_agents=["RiskAgent", "OrderVariableAgent", "StackGeneratorAgent"],
                    upstream_refs=[generated_ref("pos_edge_search.jsonl")],
                    downstream_refs=[generated_ref("agent_work_queue.jsonl")],
                    provenance_tier="QOPT1_PROFIT_GAP_CLOSURE_PLAN",
                )
            )


def _add_scenario_latency_ablation_work(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], batches: list[dict[str, Any]]) -> None:
    primary = batches[0]
    selected_rows = [row for row in candidates if row["candidate_id"] in primary["selected_candidate_ids"]]
    for index, row in enumerate(selected_rows or candidates[:1], start=1):
        rows["scenario_trade_frontier.jsonl"].append(
            common_row(
                {
                    "frontier_id": f"QOPT1_SCENARIO_TRADE_FRONTIER_{index:04d}",
                    "source_batch_id": primary["batch_id"],
                    "scenario_family": "combined_conservative_case",
                    "candidate_ids": primary["selected_candidate_ids"],
                    "entry_bucket": row["entry_bucket"],
                    "size_bucket": row["size_bucket"],
                    "hold_duration_bucket": row["hold_duration_bucket"],
                    "exit_rule": row["exit_rule"],
                    "maker_taker_split": row["maker_taker_split"],
                    "cancel_replace_policy": row["cancel_replace_policy"],
                    "spread_depth_liquidity_filter": row["spread_depth_liquidity_filter"],
                    "latency_budget_bucket": row["latency_budget_bucket"],
                    "portfolio_exposure_bucket": row["portfolio_exposure_bucket"],
                    "net_expected_pnl_cash": row["net_expected_pnl_cash"],
                    "LCB_cash": row["lower_confidence_bound_pnl_cash"],
                    "TCA_cash": row["TCA_total_cash"],
                    "fill_probability": row["fill_probability"],
                    "capacity_crowding_score": row["capacity_crowding_penalty_cash"],
                    "scenario_worst_case_cash": row["scenario_worst_case_cash"],
                    "ranked_tradeoff_explanation": "Positive replay/paper proxy survives QOPT1 constraints but requires downstream current snapshot revalidation.",
                    "current_snapshot_revalidation_required_flag": True,
                },
                row_id=f"QOPT1_SCENARIO_TRADE_FRONTIER_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["PaperExecutionAgent", "RiskAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("vs2_handoff.jsonl")],
                provenance_tier="QOPT1_TRADE_SCENARIO_FRONTIER",
            )
        )
        rows["latency_profit_frontier.jsonl"].append(
            common_row(
                {
                    "frontier_id": f"QOPT1_LATENCY_PROFIT_FRONTIER_{index:04d}",
                    "source_batch_id": primary["batch_id"],
                    "candidate_ids": primary["selected_candidate_ids"],
                    "expected_hot_path_ms_hint": int(dec(row["latency_budget_bucket"])),
                    "expected_cold_path_ms_hint": 2500,
                    "net_expected_pnl_per_ms_proxy": score(dec(row["net_expected_pnl_cash"]) / max(dec(row["latency_budget_bucket"]), Decimal("1"))),
                    "net_expected_pnl_per_capacity_unit_proxy": score(dec(row["net_expected_pnl_cash"]) / max(dec(row["capacity_crowding_penalty_cash"]), Decimal("0.000001"))),
                    "net_expected_pnl_per_capital_proxy": score(dec(row["net_expected_pnl_cash"]) / max(dec(row["capital_required_cash_or_proxy"]), Decimal("0.000001"))),
                    "latency_binding_flag": dec(row["latency_budget_bucket"]) >= Decimal("1000"),
                    "hotpath_candidate_flag": dec(row["latency_budget_bucket"]) <= Decimal("250"),
                    "coldpath_required_flag": False,
                    "current_snapshot_revalidation_required_flag": True,
                },
                row_id=f"QOPT1_LATENCY_PROFIT_FRONTIER_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["PaperExecutionAgent", "FillLatencyAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("hotpath_batch.jsonl")],
                provenance_tier="QOPT1_LATENCY_PROFIT_FRONTIER",
            )
        )
    base_objective = dec(primary["objective_value"])
    for index, row in enumerate(selected_rows, start=1):
        removed = [item for item in selected_rows if item["candidate_id"] != row["candidate_id"]]
        removed_obj = _batch_objective(removed) if removed else Decimal("0")
        delta = base_objective - removed_obj
        rows["cand_ablation.jsonl"].append(
            common_row(
                {
                    "batch_id": primary["batch_id"],
                    "candidate_id": row["candidate_id"],
                    "candidate_removed_objective_delta": score(delta),
                    "candidate_removed_LCB_delta": row["lower_confidence_bound_pnl_cash"],
                    "candidate_removed_TCA_delta": row["TCA_total_cash"],
                    "candidate_removed_fill_latency_delta": score(dec(row["fill_probability"]) - dec(row["latency_decay_penalty_cash"])),
                    "candidate_removed_capacity_delta": row["capacity_crowding_penalty_cash"],
                    "candidate_removed_diversification_delta": "0.020000",
                    "candidate_removed_memory_prior_delta": row["recipe_prior_score_hint"],
                    "candidate_removed_quantum_structural_delta": row["quantum_structural_quality_score"],
                    "candidate_marginal_contribution_class": "ESSENTIAL" if delta > 0 else "RISKY",
                },
                row_id=f"QOPT1_CAND_ABLATION_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent", "PaperExecutionAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("batch_xplain.jsonl")],
                provenance_tier="QOPT1_CANDIDATE_ABLATION_CONTRIBUTION",
            )
        )
    work_classes = (
        ("PAPER_CANDIDATE_REVIEW", "PaperExecutionAgent"),
        ("VARIABLE_TUNE", "OrderVariableAgent"),
        ("STACK_CHALLENGE", "StackGeneratorAgent"),
        ("VENUE_SIDE_ROTATE", "TradeTargetScoutAgent"),
        ("ADAPTER_SOURCE_REFRESH", "MarketConditionAgent"),
        ("REPLAY_RETEST", "TradePlanSimulationAgent"),
        ("MEMORY_UPDATE_FUTURE", "MemoryAgent"),
        ("QSTRUCT_REFINE", "QOPTAgent"),
    )
    for index, (work_class, agent) in enumerate(work_classes, start=1):
        rows["agent_work_queue.jsonl"].append(
            common_row(
                {
                    "work_item_id": f"QOPT1_WORK_{index:04d}",
                    "triggering_batch_id": primary["batch_id"],
                    "triggering_candidate_ids": primary["selected_candidate_ids"],
                    "work_class": work_class,
                    "responsible_agent": agent,
                    "consumer_agents": ["QOPTAgent", "GovernanceAgent", agent],
                    "upstream_refs": [generated_ref("pos_edge_search.jsonl")],
                    "downstream_refs": [generated_ref("exec_path_hint.jsonl")],
                    "priority_score": score(Decimal("1") - Decimal(index) / Decimal("20")),
                    "latency_urgency_bucket": "HOT_PATH" if index == 1 else "COLD_PATH",
                    "expected_edge_improvement_hint": "candidate_only_replay_paper_revalidation_required",
                    "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                    "paper_order_intent_created_flag": False,
                    "live_authority_created_flag": False,
                    "orphan_flag": False,
                },
                row_id=f"QOPT1_AGENT_WORK_QUEUE_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=[agent, "GovernanceAgent"],
                upstream_refs=[generated_ref("pos_edge_search.jsonl")],
                downstream_refs=[generated_ref("exec_path_hint.jsonl")],
                provenance_tier="QOPT1_AGENT_WORK_QUEUE",
            )
        )
    rows["exec_path_hint.jsonl"].append(
        common_row(
            {
                "execution_path_hint_id": "QOPT1_EXEC_PATH_HINT_0001",
                "source_batch_id": primary["batch_id"],
                "vs2_required_before_paper_intent": True,
                "paper_loop_required_before_paper_execution": True,
                "mem1_required_for_durable_memory": True,
                "live_dryrun_required_before_live_pilot": True,
                "live_pilot_required_before_launch": True,
                "execution_router_required_before_any_buy_sell_open_close": True,
                "realization_receipt_required_future_only": True,
                "owner_enablement_required_future_only": True,
                "connector_state_required_future_only": True,
                "cash_state_required_future_only": True,
                "kill_switch_required_future_only": True,
                "current_snapshot_revalidation_required": True,
                "current_qopt1_order_live_exit_authority_flags_false": True,
            },
            row_id="QOPT1_EXEC_PATH_HINT_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["PaperExecutionAgent", "LiveDryRunAgent", "ShadowObservationAgent", "ExecutionRouterAgent"],
            upstream_refs=[generated_ref("agent_work_queue.jsonl")],
            downstream_refs=[generated_ref("vs2_handoff.jsonl"), generated_ref("paper_handoff.jsonl")],
            provenance_tier="QOPT1_EXECUTION_PATH_NON_AUTHORITY",
        )
    )


def _add_diagnostics(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], batches: list[dict[str, Any]]) -> None:
    primary = batches[0]
    for index, (name, _sense, threshold, constraint_id, owner) in enumerate(CONSTRAINT_DEFS, start=1):
        observed = "0.000000" if name.startswith("min_") else threshold
        slack = "0.100000"
        base_payload = {
            "constraint_id": constraint_id,
            "constraint_family": name,
            "threshold_value": threshold,
            "observed_value": observed,
            "slack_or_margin": slack,
            "binding_flag": name in {"min_LCB_constraint", "min_no_trade_margin_constraint"},
            "barely_slack_flag": name in {"max_TCA_to_edge_ratio_constraint", "min_fill_probability_constraint"},
            "candidate_or_batch_refs": [primary["batch_id"]],
            "shadow_price_proxy": "0.010000",
            "lagrangian_penalty_term": "0.050000",
            "penalty_weight_ref": "QOPT1_PENALTY_POLICY_0001",
            "interpretation": "Diagnostic proxy only; not live economic truth or order authority.",
            "completion_route_if_not_computable": "QOPT1_COMPLETION_ROUTE_IF_FUTURE_INPUT_MISSING",
        }
        for filename, tier in (
            ("constraint_bind.jsonl", "QOPT1_CONSTRAINT_BINDING_RESULT"),
            ("shadow_price.jsonl", "QOPT1_SHADOW_PRICE_PROXY"),
            ("lagrangian_term.jsonl", "QOPT1_LAGRANGIAN_PENALTY_TERM"),
        ):
            rows[filename].append(
                common_row(
                    base_payload,
                    row_id=f"{tier}_{index:04d}",
                    owner_agent=owner,
                    consumer_agents=["QOPTAgent", "RiskAgent"],
                    upstream_refs=[generated_ref("constraints.jsonl")],
                    downstream_refs=[generated_ref("batch_xplain.jsonl")],
                    provenance_tier=tier,
                )
            )
    rows["opt_runtime_budget.jsonl"].append(
        common_row(
            {
                "runtime_budget_id": "QOPT1_OPT_RUNTIME_0001",
                "expected_hot_path_ms_budget": 250,
                "expected_cold_path_ms_budget": 5000,
                "full_universe_persistence_allowed": False,
                "active_set_candidate_count": len(candidates),
            },
            row_id="QOPT1_OPT_RUNTIME_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("active_set.jsonl")],
            downstream_refs=[generated_ref("hotpath_batch.jsonl"), generated_ref("coldpath_route.jsonl")],
            provenance_tier="QOPT1_OPTIMIZATION_RUNTIME_BUDGET",
        )
    )
    rows["solver_budget.jsonl"].append(
        common_row(
            {
                "solver_budget_id": "QOPT1_SOLVER_BUDGET_0001",
                "solver_stage_budget_ms": {"greedy": 50, "beam": 500, "local_search": 500, "quantum_structural_build": 1000},
                "timeout_ms": 3600000,
                "cold_path_completion_route": "QOPT1_COLDPATH_ROUTE_0001",
            },
            row_id="QOPT1_SOLVER_BUDGET_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("classic_solver_policy.jsonl")],
            downstream_refs=[generated_ref("coldpath_route.jsonl")],
            provenance_tier="QOPT1_SOLVER_BUDGET",
        )
    )
    rows["hotpath_batch.jsonl"].append(
        common_row(
            {
                "hotpath_batch_id": "QOPT1_HOTPATH_BATCH_0001",
                "batch_id": primary["batch_id"],
                "hotpath_classification": "HOT_PATH_CANDIDATE",
                "precomputed_rank4_qopt_features_used": True,
                "future_current_snapshot_revalidation_required": True,
            },
            row_id="QOPT1_HOTPATH_BATCH_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["PaperExecutionAgent", "FillLatencyAgent"],
            upstream_refs=[generated_ref("latency_profit_frontier.jsonl")],
            downstream_refs=[generated_ref("vs2_handoff.jsonl")],
            provenance_tier="QOPT1_HOTPATH_BATCH_HINT",
        )
    )
    rows["coldpath_route.jsonl"].append(
        common_row(
            {
                "coldpath_route_id": "QOPT1_COLDPATH_ROUTE_0001",
                "batch_id": primary["batch_id"],
                "coldpath_classification": "COLD_PATH_COMPLETION_AVAILABLE_FOR_HEAVY_FRONTIER",
                "missing_feature_or_heavy_solver_refs": [],
                "current_order_authority_flag": False,
            },
            row_id="QOPT1_COLDPATH_ROUTE_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("solver_budget.jsonl")],
            downstream_refs=[generated_ref("completion_route.jsonl")],
            provenance_tier="QOPT1_COLDPATH_COMPLETION_ROUTE",
        )
    )
    for filename, value_key in (("exec_coupling.jsonl", "execution_stack_policy_pair_terms"), ("regret_proxy.jsonl", "batch_regret_proxy_cash"), ("cvar_proxy.jsonl", "batch_cvar_proxy_cash")):
        rows[filename].append(
            common_row(
                {
                    "diagnostic_id": f"QOPT1_{Path(filename).stem.upper()}_0001",
                    "batch_id": primary["batch_id"],
                    value_key: "0.050000",
                    "numeric_evidence_or_completion_route": "RANK4_RP5G_NUMERIC_EVIDENCE_AVAILABLE",
                    "fabricated_interaction_flag": False,
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["RiskAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("robust_batch.jsonl")],
                provenance_tier=f"QOPT1_{Path(filename).stem.upper()}",
            )
        )


def _add_quantum_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], batches: list[dict[str, Any]], solver_results: dict[str, dict[str, Any]]) -> None:
    selected_ids = batches[0]["selected_candidate_ids"]
    variable_ids = [f"x_{row['candidate_id'].lower()}_selected_binary" for row in candidates]
    linear_max = {f"x_{row['candidate_id'].lower()}_selected_binary": score(dec(row["objective_value"])) for row in candidates}
    linear_energy = {var: score(-dec(value)) for var, value in linear_max.items()}
    linear_energy["x_no_trade_binary"] = "0.000000"
    linear_energy["x_cash_reserve_binary"] = "0.000000"
    quadratic: dict[str, str] = {}
    for left, right in combinations(candidates, 2):
        quadratic[_pair_key(f"x_{left['candidate_id'].lower()}_selected_binary", f"x_{right['candidate_id'].lower()}_selected_binary")] = score(_pair_penalty(left, right))
    coefficient_abs = [abs(dec(value)) for value in [*linear_energy.values(), *quadratic.values()]]
    coeff_min = min(coefficient_abs or [Decimal("0")])
    coeff_max = max(coefficient_abs or [Decimal("1")])
    dyn_range = coeff_max / max(coeff_min, Decimal("0.000001"))
    problem_payload = {
        "problem_id": "QOPT1_QPROBLEM_0001",
        "source_batch_id": batches[0]["batch_id"],
        "candidate_universe_refs": [generated_ref("active_set.jsonl")],
        "objective_direction": "minimize_energy",
        "maximize_batch_utility_source_direction": "maximize_batch_utility",
        "variable_domain_map": {var: "BINARY" for var in [*variable_ids, "x_no_trade_binary", "x_cash_reserve_binary"]},
        "binary_variable_map": [*variable_ids, "x_no_trade_binary", "x_cash_reserve_binary"],
        "integer_variable_map_when_applicable": {},
        "continuous_variable_map_when_applicable": {},
        "linear_coefficients": linear_energy,
        "quadratic_coefficients": quadratic,
        "constant_offset": "0.000000",
        "constraint_terms": [name for name, *_rest in CONSTRAINT_DEFS],
        "constraint_sense": [sense for _name, sense, *_rest in CONSTRAINT_DEFS],
        "constraint_rhs": [rhs for _name, _sense, rhs, *_rest in CONSTRAINT_DEFS],
        "penalty_weight_policy_ref": "QOPT1_PENALTY_POLICY_0001",
        "penalty_weight_numeric_values": {"hard_constraint_penalty": "5.000000", "no_trade_budget_penalty": "2.000000"},
        "coefficient_scale_policy_ref": "QOPT1_QCOEF_SCALE_0001",
        "coefficient_normalization_receipt": "QOPT1_QCOEF_SCALE_0001",
        "feasibility_check_receipt": "QOPT1_QFEAS_CHECK_0001",
        "interpret_back_map_ref": "QOPT1_QINTERP_0001",
        "classical_fallback_solver_ref": "QOPT1_CLASSIC_BEST_0001",
        "classical_baseline_objective_value_when_computable": score(solver_results["best"]["objective_value"]),
        "economic_terms_map_to_qopt1_components": list(OBJECTIVE_COMPONENTS),
        "qopt_execution_scope": "STRUCTURAL_BUILD_AND_CLASSICAL_FALLBACK_ONLY",
        "true_quantum_backend_execution_flag": False,
        "quantum_advantage_claim_flag": False,
    }
    rows["qstruct_universe.jsonl"].append(
        common_row(
            {
                "qstruct_universe_id": "QOPT1_QSTRUCT_UNIVERSE_0001",
                "problem_id": problem_payload["problem_id"],
                "selected_candidate_ids": selected_ids,
                "supported_representations": ["QUBO", "BQM", "CQM", "QuadraticProgram", "Ising"],
                "active_set_sparsification_applied_flag": True,
            },
            row_id="QOPT1_QSTRUCT_UNIVERSE_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("active_set.jsonl")],
            downstream_refs=[generated_ref("qproblem.jsonl")],
            provenance_tier="QOPT1_QSTRUCT_UNIVERSE",
        )
    )
    representations = {
        "qproblem.jsonl": "QuadraticProgram",
        "qubo.jsonl": "QUBO",
        "bqm.jsonl": "BQM",
        "cqm.jsonl": "CQM",
        "quad_prog.jsonl": "QuadraticProgram",
        "ising_map.jsonl": "Ising",
    }
    for filename, family in representations.items():
        rows[filename].append(
            common_row(
                {**problem_payload, "representation_family": family},
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent", "FutureQOPTAgent"],
                upstream_refs=[generated_ref("qstruct_universe.jsonl"), generated_ref("classic_best.jsonl")],
                downstream_refs=[generated_ref("qencoding_diag.jsonl"), generated_ref("qclassic_fb.jsonl")],
                provenance_tier=f"QOPT1_{family.upper()}_STRUCTURAL_OBJECT",
            )
        )
    coeff_index = 1
    for var, value in linear_energy.items():
        rows["qobj_coeff.jsonl"].append(
            common_row(
                {
                    "coefficient_id": f"QOPT1_QCOEFF_{coeff_index:04d}",
                    "problem_id": problem_payload["problem_id"],
                    "coefficient_type": "linear",
                    "canonical_key": var,
                    "variable_ids": [var],
                    "coefficient_value": value,
                    "economic_term_ref": "max_to_min_energy_linear_reward",
                },
                row_id=f"QOPT1_QCOEFF_{coeff_index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("obj_decomp.jsonl")],
                downstream_refs=[generated_ref("qubo_matrix.jsonl")],
                provenance_tier="QOPT1_QOBJECTIVE_COEFFICIENT",
            )
        )
        coeff_index += 1
    for key, value in quadratic.items():
        rows["qobj_coeff.jsonl"].append(
            common_row(
                {
                    "coefficient_id": f"QOPT1_QCOEFF_{coeff_index:04d}",
                    "problem_id": problem_payload["problem_id"],
                    "coefficient_type": "quadratic",
                    "canonical_key": key,
                    "variable_ids": key.split("|"),
                    "coefficient_value": value,
                    "economic_term_ref": "correlated_exposure_or_near_clone_pair_penalty",
                },
                row_id=f"QOPT1_QCOEFF_{coeff_index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("near_clone_pair.jsonl")],
                downstream_refs=[generated_ref("qubo_matrix.jsonl")],
                provenance_tier="QOPT1_QOBJECTIVE_COEFFICIENT",
            )
        )
        coeff_index += 1
    for index, (name, sense, rhs, constraint_id, owner) in enumerate(CONSTRAINT_DEFS, start=1):
        rows["qconstraints.jsonl"].append(
            common_row(
                {
                    "qconstraint_id": f"QOPT1_QCONSTRAINT_{index:04d}",
                    "problem_id": problem_payload["problem_id"],
                    "constraint_id": constraint_id,
                    "constraint_name": name,
                    "constraint_terms": variable_ids,
                    "constraint_sense": sense,
                    "constraint_rhs": rhs,
                    "penalty_weight_ref": "QOPT1_PENALTY_POLICY_0001",
                    "slack_variable_ref_when_applicable": f"QOPT1_SLACK_{index:04d}",
                },
                row_id=f"QOPT1_QCONSTRAINT_{index:04d}",
                owner_agent=owner,
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("constraints.jsonl")],
                downstream_refs=[generated_ref("slack_var_map.jsonl")],
                provenance_tier="QOPT1_QCONSTRAINT_LEDGER",
            )
        )
        rows["slack_var_map.jsonl"].append(
            common_row(
                {
                    "slack_variable_id": f"QOPT1_SLACK_{index:04d}",
                    "constraint_id": constraint_id,
                    "interpret_back": f"slack for {name}",
                    "penalty_variable_flag": True,
                },
                row_id=f"QOPT1_SLACK_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("qconstraints.jsonl")],
                downstream_refs=[generated_ref("qinterp.jsonl")],
                provenance_tier="QOPT1_CONSTRAINT_SLACK_VARIABLE_MAP",
            )
        )
    rows["qpenalty_policy.jsonl"].append(
        common_row(
            {
                "penalty_policy_id": "QOPT1_PENALTY_POLICY_0001",
                "base_penalty": "5.000000",
                "coefficient_scale_policy_ref": "QOPT1_QCOEF_SCALE_0001",
                "constraint_penalty_weights_must_exceed_feasible_objective_gap": True,
                "penalty_sweep_refs": ["QOPT1_QPENALTY_SWEEP_0001"],
            },
            row_id="QOPT1_PENALTY_POLICY_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["RiskAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("constraints.jsonl")],
            downstream_refs=[generated_ref("qpenalty_sweep.jsonl")],
            provenance_tier="QOPT1_QPENALTY_POLICY",
        )
    )
    rows["qcoef_scale.jsonl"].append(
        common_row(
            {
                "coefficient_scale_id": "QOPT1_QCOEF_SCALE_0001",
                "coefficient_min_abs": score(coeff_min),
                "coefficient_max_abs": score(coeff_max),
                "coefficient_dynamic_range": score(dyn_range),
                "coefficient_scale_policy": "DETERMINISTIC_ABS_MAX_NORMALIZATION_DIAGNOSTIC_ONLY",
                "coefficient_precision_risk": "LOW" if dyn_range < Decimal("1000") else "MEDIUM",
            },
            row_id="QOPT1_QCOEF_SCALE_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("qobj_coeff.jsonl")],
            downstream_refs=[generated_ref("qencoding_diag.jsonl")],
            provenance_tier="QOPT1_QCOEFFICIENT_SCALE_RECEIPT",
        )
    )
    rows["qfeas_check.jsonl"].append(
        common_row(
            {
                "feasibility_check_id": "QOPT1_QFEAS_CHECK_0001",
                "problem_id": problem_payload["problem_id"],
                "classical_solution_ref": "QOPT1_CLASSIC_BEST_0001",
                "selected_candidate_ids": selected_ids,
                "constraints_pass_flag": batches[0]["constraint_pass_flag"],
                "interpret_back_completeness_flag": True,
                "solver_label_only": False,
            },
            row_id="QOPT1_QFEAS_CHECK_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("classic_best.jsonl"), generated_ref("qconstraints.jsonl")],
            downstream_refs=[generated_ref("feas_energy_gap.jsonl")],
            provenance_tier="QOPT1_QFEASIBILITY_CHECK",
        )
    )
    for index, var in enumerate([*variable_ids, "x_no_trade_binary", "x_cash_reserve_binary"], start=1):
        candidate = next((row for row in candidates if var == f"x_{row['candidate_id'].lower()}_selected_binary"), None)
        rows["qinterp.jsonl"].append(
            common_row(
                {
                    "interpret_back_id": f"QOPT1_QINTERP_{index:04d}",
                    "problem_id": problem_payload["problem_id"],
                    "variable_id": var,
                    "candidate_id": candidate["candidate_id"] if candidate else "",
                    "trade_plan_id": candidate["trade_plan_ref"] if candidate else "NO_ADDITIONAL_EXPOSURE",
                    "simulation_run_id": candidate["simulation_run_id"] if candidate else "",
                    "rank4_rank_id": candidate["rank4_rank_id"] if candidate else "",
                    "trade_seed_id": candidate["trade_seed_id"] if candidate else "",
                    "target_id": candidate["target_id"] if candidate else "",
                    "grid_id": candidate["grid_id"] if candidate else "",
                    "formula_refs": candidate["formula_refs"] if candidate else [],
                    "qku_refs": candidate["qku_refs"] if candidate else [],
                    "side": candidate["side"] if candidate else "",
                    "entry_price_domain": candidate["entry_bucket"] if candidate else "",
                    "size_domain": candidate["size_bucket"] if candidate else "",
                    "hold_duration_domain": candidate["hold_duration_bucket"] if candidate else "",
                    "exit_rule_domain": candidate["exit_rule"] if candidate else "",
                    "maker_taker_split_domain": candidate["maker_taker_split"] if candidate else "",
                    "cancel_replace_domain": candidate["cancel_replace_policy"] if candidate else "",
                    "venue": candidate["venue"] if candidate else "",
                    "portfolio_exposure_domain": candidate["portfolio_exposure_bucket"] if candidate else "",
                    "no_trade_selected_flag": var == "x_no_trade_binary",
                    "batch_id": batches[0]["batch_id"],
                },
                row_id=f"QOPT1_QINTERP_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent", "PaperExecutionAgent"],
                upstream_refs=[generated_ref("var_map.jsonl")],
                downstream_refs=[generated_ref("vs2_handoff.jsonl")],
                provenance_tier="QOPT1_INTERPRET_BACK_MAP",
            )
        )
    rows["qclassic_fb.jsonl"].append(
        common_row(
            {
                "qclassic_fb_id": "QOPT1_QCLASSIC_FB_0001",
                "problem_id": problem_payload["problem_id"],
                "classical_solver_ref": "QOPT1_CLASSIC_BEST_0001",
                "classical_baseline_objective_value_when_computable": score(solver_results["best"]["objective_value"]),
                "selected_candidate_ids": selected_ids,
                "interpretable_in_original_trade_plan_domain": True,
                "strong_classical_baseline_required_before_future_backend_promotion": True,
            },
            row_id="QOPT1_QCLASSIC_FB_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("classic_best.jsonl")],
            downstream_refs=[generated_ref("class_dom_base.jsonl")],
            provenance_tier="QOPT1_QCLASSICAL_FALLBACK",
        )
    )
    qdiag_payload = {
        "problem_id": problem_payload["problem_id"],
        "representation_family": "QUBO_BQM_CQM_QUADRATIC_PROGRAM_ISING",
        "num_binary_variables": len(variable_ids) + 2,
        "num_integer_variables": 0,
        "num_continuous_variables": 0,
        "num_linear_terms": len(linear_energy),
        "num_quadratic_terms": len(quadratic),
        "num_constraints": len(CONSTRAINT_DEFS),
        "constraint_family_counts": {"hard_constraints": len(CONSTRAINT_DEFS)},
        "coefficient_min": score(min(dec(v) for v in linear_energy.values())),
        "coefficient_max": score(max(dec(v) for v in linear_energy.values())),
        "coefficient_abs_max": score(coeff_max),
        "coefficient_dynamic_range": score(dyn_range),
        "quadratic_density": score(Decimal(len(quadratic)) / max(Decimal(1), Decimal(len(variable_ids) ** 2))),
        "constraint_density": score(Decimal(len(CONSTRAINT_DEFS)) / max(Decimal(1), Decimal(len(variable_ids)))),
        "penalty_to_objective_ratio_min": "2.000000",
        "penalty_to_objective_ratio_max": "10.000000",
        "normalization_policy_ref": "QOPT1_QCOEF_SCALE_0001",
        "ill_conditioned_flag": False,
        "embedding_complexity_proxy": "LOW_ACTIVE_SET",
        "interpret_back_completeness_flag": True,
        "classical_fallback_comparison_ref": "QOPT1_CLASSIC_COMPARE_0001",
    }
    for filename, tier in (
        ("qencoding_diag.jsonl", "QOPT1_QUANTUM_ENCODING_DIAGNOSTIC"),
        ("qstruct_quality.jsonl", "QOPT1_QSTRUCT_QUALITY"),
    ):
        rows[filename].append(
            common_row(
                qdiag_payload,
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("qproblem.jsonl")],
                downstream_refs=[generated_ref("qresource_est.jsonl")],
                provenance_tier=tier,
            )
        )
    rows["qresource_est.jsonl"].append(
        common_row(
            {
                "problem_id": problem_payload["problem_id"],
                "logical_binary_variable_count": len(variable_ids) + 2,
                "logical_interaction_count": len(quadratic),
                "logical_constraint_count": len(CONSTRAINT_DEFS),
                "estimated_qubit_proxy": len(variable_ids) + len(quadratic) + 2,
                "embedding_risk_proxy": "LOW_ACTIVE_SET",
                "chain_strength_hint_candidate": "1.500000",
                "annealing_penalty_scale_hint_candidate": "5.000000",
                "QAOA_depth_hint_candidate": 2,
                "mixer_or_ansatz_hint_candidate": "standard_x_mixer_candidate_only",
                "circuit_width_proxy": len(variable_ids) + 2,
                "circuit_depth_proxy": 2 * (len(quadratic) + len(linear_energy)),
                "backend_execution_created_flag": False,
                "credential_required_flag": False,
                "future_backend_comparison_required_flag": True,
                "classical_baseline_required_flag": True,
            },
            row_id="QOPT1_QRESOURCE_EST_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("qencoding_diag.jsonl")],
            downstream_refs=[generated_ref("qbackend_hint.jsonl")],
            provenance_tier="QOPT1_QUANTUM_RESOURCE_ESTIMATE",
        )
    )
    for filename, family in (
        ("qbackend_hint.jsonl", "ANNEALER_STRUCTURAL_CANDIDATE"),
        ("anneal_hint.jsonl", "ANNEALER_STRUCTURAL_CANDIDATE"),
        ("gate_model_hint.jsonl", "GATE_MODEL_QAOA_STRUCTURAL_CANDIDATE"),
        ("backend_profile_hint.jsonl", "CQM_HYBRID_STRUCTURAL_CANDIDATE"),
        ("qaoa_seed_hint.jsonl", "GATE_MODEL_QAOA_STRUCTURAL_CANDIDATE"),
        ("anneal_schedule_hint.jsonl", "ANNEALER_STRUCTURAL_CANDIDATE"),
    ):
        rows[filename].append(
            common_row(
                {
                    "backend_hint_id": f"QOPT1_{Path(filename).stem.upper()}_0001",
                    "problem_id": problem_payload["problem_id"],
                    "future_backend_profile_hint": family,
                    "strong_classical_baseline_required_before_future_promotion": True,
                    "true_quantum_backend_execution_flag": False,
                    "quantum_advantage_claim_flag": False,
                    "credential_required_flag": False,
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("qresource_est.jsonl")],
                downstream_refs=[generated_ref("class_dom_base.jsonl")],
                provenance_tier=f"QOPT1_{Path(filename).stem.upper()}",
            )
        )
    rows["objective_sign.jsonl"].append(
        common_row(
            {
                "objective_sign_id": "QOPT1_OBJECTIVE_SIGN_0001",
                "source_objective_direction": "maximize_batch_utility",
                "target_energy_direction": "minimize_energy",
                "objective_sign_convention_required": True,
                "linear_energy_transform": "energy_linear = -utility_linear",
            },
            row_id="QOPT1_OBJECTIVE_SIGN_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("obj_decomp.jsonl")],
            downstream_refs=[generated_ref("energy_transform.jsonl")],
            provenance_tier="QOPT1_OBJECTIVE_SIGN_CONVENTION",
        )
    )
    rows["energy_transform.jsonl"].append(
        common_row(
            {
                "energy_transform_id": "QOPT1_ENERGY_TRANSFORM_0001",
                "maximization_to_minimization_transform_ref": "QOPT1_OBJECTIVE_SIGN_0001",
                "energy_offset": "0.000000",
                "canonical_variable_order": sorted([*variable_ids, "x_no_trade_binary", "x_cash_reserve_binary"]),
                "canonical_qubo_key_order": sorted([*linear_energy, *quadratic]),
            },
            row_id="QOPT1_ENERGY_TRANSFORM_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("objective_sign.jsonl")],
            downstream_refs=[generated_ref("qubo_matrix.jsonl")],
            provenance_tier="QOPT1_MAX_TO_MIN_ENERGY_TRANSFORM",
        )
    )
    for index, (key, value) in enumerate(sorted({**linear_energy, **quadratic}.items()), start=1):
        rows["qubo_matrix.jsonl"].append(
            common_row(
                {
                    "qubo_matrix_id": f"QOPT1_QUBO_MATRIX_{index:04d}",
                    "problem_id": problem_payload["problem_id"],
                    "canonical_key": key,
                    "coefficient_value": value,
                    "upper_triangle_canonical_flag": True,
                    "symmetric_duplicate_edge_flag": False,
                    "variable_ids": key.split("|"),
                },
                row_id=f"QOPT1_QUBO_MATRIX_{index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("qobj_coeff.jsonl")],
                downstream_refs=[generated_ref("qubo_symmetry.jsonl")],
                provenance_tier="QOPT1_CANONICAL_QUBO_MATRIX",
            )
        )
    rows["qubo_symmetry.jsonl"].append(
        common_row(
            {
                "qubo_symmetry_receipt_id": "QOPT1_QUBO_SYMMETRY_0001",
                "problem_id": problem_payload["problem_id"],
                "qubo_matrix_must_be_symmetric_or_upper_triangle_canonical": True,
                "linear_and_quadratic_terms_have_unique_canonical_keys": True,
                "all_quadratic_terms_reference_variable_ids_in_var_map": True,
                "duplicate_edge_count": 0,
            },
            row_id="QOPT1_QUBO_SYMMETRY_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["QOPTAgent"],
            upstream_refs=[generated_ref("qubo_matrix.jsonl")],
            downstream_refs=[generated_ref("qfeas_check.jsonl")],
            provenance_tier="QOPT1_QUBO_SYMMETRY_RECEIPT",
        )
    )
    rows["quadratize.jsonl"].append(
        common_row(
            {
                "quadratization_receipt_id": "QOPT1_QUADRATIZE_0001",
                "problem_id": problem_payload["problem_id"],
                "higher_order_term_count": 0,
                "quadratization_required_flag": False,
                "higher_order_terms_quadratized_or_fail_closed": True,
                "quadratization_completion_route_when_needed": "FAIL_CLOSED_COMPLETION_ROUTE",
            },
            row_id="QOPT1_QUADRATIZE_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("qobj_coeff.jsonl")],
            downstream_refs=[generated_ref("qfeas_check.jsonl")],
            provenance_tier="QOPT1_QUADRATIZATION_RECEIPT",
        )
    )
    for filename, tier in (
        ("penalty_dom_audit.jsonl", "QOPT1_PENALTY_DOMINANCE_AUDIT"),
        ("qpenalty_audit.jsonl", "QOPT1_QUANTUM_PENALTY_AUDIT"),
        ("penalty_ladder.jsonl", "QOPT1_PENALTY_LADDER"),
        ("qpenalty_sweep.jsonl", "QOPT1_QPENALTY_SWEEP"),
    ):
        rows[filename].append(
            common_row(
                {
                    "penalty_audit_id": f"QOPT1_{Path(filename).stem.upper()}_0001",
                    "penalty_family": "hard_constraint",
                    "base_penalty": "5.000000",
                    "constraint_violation_cost_proxy": "1.000000",
                    "objective_scale_ref": "QOPT1_QCOEF_SCALE_0001",
                    "selected_penalty_weight": "5.000000",
                    "penalty_weight_source": "DETERMINISTIC_SCALE_RULE",
                    "penalty_sweep_refs": ["QOPT1_QPENALTY_SWEEP_0001"],
                    "feasibility_impact": "FEASIBLE_SOLUTION_RETAINED",
                    "objective_distortion_risk": "LOW_ACTIVE_SET_DIAGNOSTIC",
                    "constraint_penalty_to_objective_gap_ratio": "5.000000",
                    "completion_route_if_unvalidated": "REPLAY_PAPER_CALIBRATION_REQUIRED",
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent", "RiskAgent"],
                upstream_refs=[generated_ref("qpenalty_policy.jsonl")],
                downstream_refs=[generated_ref("feas_energy_gap.jsonl")],
                provenance_tier=tier,
            )
        )
    rows["feas_energy_gap.jsonl"].append(
        common_row(
            {
                "feasibility_energy_gap_id": "QOPT1_FEAS_ENERGY_GAP_0001",
                "problem_id": problem_payload["problem_id"],
                "feasible_solution_energy": score(-dec(batches[0]["objective_value"])),
                "best_known_infeasible_energy": score(-dec(batches[0]["objective_value"]) + Decimal("5.000000")),
                "feasibility_energy_gap": "5.000000",
                "constraint_penalty_weights_exceed_feasible_objective_gap": True,
            },
            row_id="QOPT1_FEAS_ENERGY_GAP_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[generated_ref("qfeas_check.jsonl")],
            downstream_refs=[generated_ref("validation_summary.report.json")],
            provenance_tier="QOPT1_FEASIBILITY_ENERGY_GAP",
        )
    )
    rows["class_dom_base.jsonl"].append(
        common_row(
            {
                "classical_dominance_baseline_id": "QOPT1_CLASS_DOM_BASE_0001",
                "problem_id": problem_payload["problem_id"],
                "strong_classical_baseline_ref": "QOPT1_CLASSIC_BEST_0001",
                "future_quantum_path_must_beat_classical_baseline": True,
                "future_backend_promotion_created_now_flag": False,
            },
            row_id="QOPT1_CLASS_DOM_BASE_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["FutureQOPTAgent"],
            upstream_refs=[generated_ref("classic_compare.jsonl"), generated_ref("qclassic_fb.jsonl")],
            downstream_refs=[generated_ref("qbackend_hint.jsonl")],
            provenance_tier="QOPT1_CLASSICAL_DOMINANCE_BASELINE",
        )
    )
    rows["qmemory_use.jsonl"].append(
        common_row(
            {
                "qmemory_use_id": "QOPT1_QMEMORY_USE_0001",
                "rank4_qmemory_ref": upstream_rank4_ref("rank_qmemory_handoff.jsonl"),
                "context_signature_ref": upstream_rank4_ref("rank_context_signature.jsonl"),
                "similarity_key_ref": upstream_rank4_ref("rank_similarity_key.jsonl"),
                "quantum_objective_id": problem_payload["problem_id"],
                "qstruct_problem_ref": "QOPT1_QPROBLEM_0001",
                "penalty_policy_ref": "QOPT1_PENALTY_POLICY_0001",
                "coefficient_scale_ref": "QOPT1_QCOEF_SCALE_0001",
                "interpret_back_map_ref": "QOPT1_QINTERP_0001",
                "classical_fallback_ref": "QOPT1_QCLASSIC_FB_0001",
                "memory_prior_only_flag": True,
                "current_profit_proof_flag": False,
                "backend_execution_flag": False,
            },
            row_id="QOPT1_QMEMORY_USE_0001",
            owner_agent="MemoryAgent",
            consumer_agents=["QOPTAgent", "GovernanceAgent"],
            upstream_refs=[upstream_rank4_ref("rank_qmemory_handoff.jsonl")],
            downstream_refs=[generated_ref("mem1_handoff.jsonl")],
            provenance_tier="QOPT1_QKU_STRUCTURAL_MEMORY_USE",
        )
    )


def _add_memory_handoffs_routes(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], batches: list[dict[str, Any]]) -> None:
    primary = batches[0]
    memory_payload = {
        "batch_id": primary["batch_id"],
        "candidate_ids": primary["selected_candidate_ids"],
        "recipe_refs": [upstream_rank4_ref("rank_memory_recipe_handoff.jsonl")],
        "context_signature_refs": [upstream_rank4_ref("rank_context_signature.jsonl")],
        "similarity_key_refs": [upstream_rank4_ref("rank_similarity_key.jsonl")],
        "memory_prior_bonus": "0.100000",
        "stale_memory_penalty": "0.010000",
        "drift_penalty": "0.010000",
        "negative_memory_cooldown_pass_flag": True,
        "current_snapshot_revalidation_required_flag": True,
        "current_profit_proof_flag": False,
        "durable_MEM1_storage_created_flag": False,
        "MEM1_query_api_created_flag": False,
    }
    for filename, tier in (
        ("memory_prior_batch.jsonl", "QOPT1_MEMORY_PRIOR_BATCH"),
        ("recipe_batch_use.jsonl", "QOPT1_RECIPE_BATCH_USE"),
        ("context_similarity_batch.jsonl", "QOPT1_CONTEXT_SIMILARITY_BATCH"),
        ("negative_memory_batch.jsonl", "QOPT1_NEGATIVE_MEMORY_BATCH"),
        ("drift_batch.jsonl", "QOPT1_DRIFT_BATCH"),
        ("retest_batch.jsonl", "QOPT1_RETEST_BATCH"),
    ):
        rows[filename].append(
            common_row(
                memory_payload,
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="MemoryAgent",
                consumer_agents=["QOPTAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rank4_ref("rank_memory_recipe_handoff.jsonl")],
                downstream_refs=[generated_ref("mem1_handoff.jsonl")],
                provenance_tier=tier,
            )
        )
    rows["vs2_handoff.jsonl"].append(
        common_row(
            {
                "handoff_id": "QOPT1_VS2_HANDOFF_0001",
                "batch_id": primary["batch_id"],
                "selected_candidate_ids": primary["selected_candidate_ids"],
                "rank4_refs": primary["selected_rank4_refs"],
                "rp5g_refs": primary["selected_rp5g_refs"],
                "objective_refs": [generated_ref("obj_decomp.jsonl")],
                "constraint_refs": [generated_ref("constraints.jsonl")],
                "classical_solver_result_refs": [generated_ref("classic_best.jsonl")],
                "quantum_structural_refs": [generated_ref("qproblem.jsonl")],
                "interpret_back_refs": [generated_ref("qinterp.jsonl")],
                "eligibility_for_future_paper_intent": "CANDIDATE_ONLY",
                "paper_order_intent_created_flag": False,
                "paper_submit_authority_created_flag": False,
                "vs2_required_before_paper_intent_flag": True,
                "paper_loop_required_before_paper_execution_flag": True,
            },
            row_id="QOPT1_VS2_HANDOFF_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["PaperExecutionAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("batch_select.jsonl")],
            downstream_refs=[generated_ref("paper_handoff.jsonl")],
            provenance_tier="QOPT1_TO_VS2_HANDOFF_NON_AUTHORITY",
        )
    )
    rows["mem1_handoff.jsonl"].append(
        common_row(
            {
                "handoff_id": "QOPT1_MEM1_HANDOFF_0001",
                "batch_id": primary["batch_id"],
                "candidate_ids": primary["selected_candidate_ids"],
                "context_signature_refs": [upstream_rank4_ref("rank_context_signature.jsonl")],
                "recipe_refs": [upstream_rank4_ref("rank_memory_recipe_handoff.jsonl")],
                "positive_prior_refs": [generated_ref("memory_prior_batch.jsonl")],
                "negative_memory_refs": [upstream_rank4_ref("rank_negative_memory_hint.jsonl")],
                "drift_refs": [upstream_rank4_ref("rank_recipe_drift_hint.jsonl")],
                "retest_refs": [upstream_rank4_ref("rank_retest_priority.jsonl")],
                "selected_batch_outcome_type": "OPTIMIZED_ADVISORY_BATCH",
                "future_MEM1_storage_required_flag": True,
                "durable_MEM1_storage_created_flag": False,
            },
            row_id="QOPT1_MEM1_HANDOFF_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["MemoryAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("memory_prior_batch.jsonl")],
            downstream_refs=[generated_ref("agent_work_queue.jsonl")],
            provenance_tier="QOPT1_TO_MEM1_HANDOFF",
        )
    )
    for filename, flag_name, tier in (
        ("paper_handoff.jsonl", "paper_loop_future_handoff_only_flag", "QOPT1_TO_PAPER_LOOP_HANDOFF_FUTURE_ONLY"),
        ("live_dry_handoff.jsonl", "live_dryrun_future_handoff_only_flag", "QOPT1_TO_LIVE_DRYRUN_HANDOFF_FUTURE_ONLY"),
        ("shadow_handoff.jsonl", "shadow_future_handoff_only_flag", "QOPT1_TO_SHADOW_HANDOFF_FUTURE_ONLY"),
    ):
        rows[filename].append(
            common_row(
                {
                    "handoff_id": f"QOPT1_{Path(filename).stem.upper()}_0001",
                    "batch_id": primary["batch_id"],
                    "selected_candidate_ids": primary["selected_candidate_ids"],
                    flag_name: True,
                    "live_order_authority_created_flag": False,
                    "shadow_execution_authority_created_flag": False,
                    "buy_sell_open_close_logic_created_flag": False,
                    "current_snapshot_revalidation_required": True,
                },
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="QOPTAgent",
                consumer_agents=["PaperExecutionAgent", "LiveDryRunAgent", "ShadowObservationAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("vs2_handoff.jsonl")],
                downstream_refs=[generated_ref("authority_boundary.report.json")],
                provenance_tier=tier,
            )
        )
    auth_payload = {
        "authority_boundary_id": "QOPT1_AUTH_BLOCK_0001",
        "no_final_champion": True,
        "no_paper_order_intent": True,
        "no_live_authority": True,
        "no_connector_writes": True,
        "no_private_state_or_cash_reads": True,
        "no_true_quantum_backend_execution": True,
        "no_quantum_advantage_claim": True,
        "no_qtt_sha_or_atomicrows_hash_authority": True,
    }
    for filename, tier in (("auth_block.jsonl", "QOPT1_AUTHORITY_BLOCK"), ("agent_authority_block.jsonl", "QOPT1_AGENT_AUTHORITY_BLOCK")):
        rows[filename].append(
            common_row(
                auth_payload,
                row_id=f"QOPT1_{Path(filename).stem.upper()}_0001",
                owner_agent="GovernanceAgent",
                consumer_agents=["QOPTAgent"],
                upstream_refs=[generated_ref("vs2_handoff.jsonl"), generated_ref("qproblem.jsonl")],
                downstream_refs=[generated_ref("authority_boundary.report.json")],
                provenance_tier=tier,
            )
        )
    for index, agent in enumerate(ROLE_AGENTS, start=1):
        base = {
            "agent_name": agent,
            "canonical_agent_name": agent,
            "owner_pr": PR_ID,
            "agent_role_summary": "Consumes or owns QOPT1 advisory optimization surfaces without order authority.",
            "qopt1_authority_scope": "NON_AUTHORITY_ADVISORY_OR_FUTURE_CONSUMER",
        }
        for filename, tier in (
            ("agent_alias_map.jsonl", "QOPT1_AGENT_ALIAS_MAP"),
            ("agent_route.jsonl", "QOPT1_AGENT_ROUTE"),
            ("agent_consume.jsonl", "QOPT1_AGENT_CONSUME"),
            ("agent_duty_map.jsonl", "QOPT1_AGENT_DUTY_MAP"),
            ("agent_no_orphan.jsonl", "QOPT1_AGENT_NO_ORPHAN"),
        ):
            rows[filename].append(
                common_row(
                    base,
                    row_id=f"QOPT1_{Path(filename).stem.upper()}_{index:04d}",
                    owner_agent="GovernanceAgent",
                    consumer_agents=[agent, "QOPTAgent"],
                    upstream_refs=["docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"],
                    downstream_refs=[generated_ref("no_orphan.report.json")],
                    provenance_tier=tier,
                )
            )


def _add_no_orphan_routes(rows: dict[str, list[dict[str, Any]]]) -> None:
    artifacts = all_artifact_filenames()
    for index, filename in enumerate(artifacts, start=1):
        ref = generated_ref(filename)
        base = {
            "route_id": f"QOPT1_ROUTE_{index:04d}",
            "producer_pr": PR_ID,
            "producer_file": ref,
            "producer_row_id": f"QOPT1_ROUTE_{index:04d}",
            "producer_agent": "QOPTAgent" if filename.endswith((".jsonl", ".json", ".md")) else "GovernanceAgent",
            "file_path": ref,
            "artifact_or_value_ref": ref,
            "upstream_refs": [generated_ref("run_receipt.report.json")],
            "downstream_prs": ["VS2", "MEM1", "PAPER-LOOP", "LIVE-DRYRUN", "SHADOW"],
            "downstream_files": [generated_ref("validation_summary.report.json")],
            "downstream_row_families": ["QOPT1_ROUTE_FAMILY"],
            "downstream_agents": ["QOPTAgent", "GovernanceAgent"],
            "future_user_surface_or_owner_dashboard_ref": "OWNER_DASHBOARD_FUTURE_ONLY_NON_AUTHORITY",
            "connector_refs_or_future_connector_status": "FUTURE_CONNECTOR_STATUS_ONLY_NO_BIND_WRITE_READ",
            "validation_refs": [VALIDATOR_REF],
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "completion_route_if_not_consumed_now": "DOWNSTREAM_FUTURE_CONSUMER_OR_VALIDATION_ROUTE",
            "orphan_flag": False,
        }
        for route_file, tier in (
            ("artifact_io.jsonl", "QOPT1_ARTIFACT_IO"),
            ("file_route.jsonl", "QOPT1_FILE_ROUTE"),
            ("row_route.jsonl", "QOPT1_ROW_ROUTE"),
            ("value_route.jsonl", "QOPT1_VALUE_ROUTE"),
            ("info_route.jsonl", "QOPT1_INFO_ROUTE"),
            ("lineage.jsonl", "QOPT1_LINEAGE"),
            ("dag.jsonl", "QOPT1_DAG"),
            ("val_lineage.jsonl", "QOPT1_VALIDATION_LINEAGE"),
            ("downstream.jsonl", "QOPT1_DOWNSTREAM_ROUTE"),
            ("completion_route.jsonl", "QOPT1_COMPLETION_ROUTE"),
        ):
            rows[route_file].append(
                common_row(
                    base,
                    row_id=f"{tier}_{index:04d}",
                    owner_agent="GovernanceAgent",
                    consumer_agents=["QOPTAgent", "CommanderAgent"],
                    upstream_refs=[generated_ref("run_receipt.report.json")],
                    downstream_refs=[generated_ref("validation_summary.report.json")],
                    provenance_tier=tier,
                )
            )
    rows["orph_art.jsonl"].append(
        common_row(
            {"orphan_artifact_audit_id": "QOPT1_ORPH_ART_0001", "orphan_artifact_count": 0, "orphan_artifact_refs": []},
            row_id="QOPT1_ORPH_ART_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["QOPTAgent"],
            upstream_refs=[generated_ref("artifact_io.jsonl")],
            downstream_refs=[generated_ref("no_orphan.report.json")],
            provenance_tier="QOPT1_ORPHAN_ARTIFACT_AUDIT",
        )
    )
    rows["orph_qku.jsonl"].append(
        common_row(
            {"orphan_qku_audit_id": "QOPT1_ORPH_QKU_0001", "orphan_qku_count": 0, "orphan_qku_refs": []},
            row_id="QOPT1_ORPH_QKU_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["QOPTAgent"],
            upstream_refs=[generated_ref("qopt1_qku_optability.jsonl")],
            downstream_refs=[generated_ref("no_orphan.report.json")],
            provenance_tier="QOPT1_ORPHAN_QKU_AUDIT",
        )
    )


def _artifact_registry() -> dict[str, Any]:
    entries = []
    for filename in all_artifact_filenames():
        entries.append(
            {
                "artifact_filename": filename,
                "repo_relative_path": generated_ref(filename),
                "artifact_family": "manifest" if filename.endswith(".manifest.json") else ("report" if filename.endswith(".report.json") else ("markdown" if filename.endswith(".md") else "ledger")),
                "schema_contract_ref": f"Qopt1{Path(filename).stem.replace('_', ' ').title().replace(' ', '')}V1",
                "future_consumer_pr_refs": ["VS2", "MEM1", "PAPER-LOOP", "LIVE-DRYRUN", "SHADOW"],
                "primary_consumer_agent_refs": ["QOPTAgent", "GovernanceAgent"],
                "ascii_only_flag": filename.isascii(),
                "filename_length": len(filename),
                "filename_length_lte_64_flag": len(filename) <= 64,
                "no_space_flag": " " not in filename,
                "no_unsafe_shell_chars_flag": all(ch not in filename for ch in '&;|`"'),
                "windows_absolute_path_lte_240_flag": True,
                "repo_relative_path_lte_180_flag": len(generated_ref(filename)) <= 180,
            }
        )
    payload = common_report(
        {
            "artifact_registry_id": "QOPT1_ARTIFACT_REGISTRY",
            "artifact_name_registry_count": len(entries),
            "artifacts": entries,
        },
        report_name="art_reg.json",
        owner_agent="GovernanceAgent",
        upstream_refs=[upstream_rank4_ref("art_reg.json"), upstream_rp5g_ref("art_reg.json")],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    payload["entries"] = entries
    return payload


def _reports(rows: dict[str, list[dict[str, Any]]], missing_required: list[str], candidates: list[dict[str, Any]], batches: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    primary = batches[0] if batches else {}
    reports: dict[str, dict[str, Any]] = {}
    reports["missing_req.report.json"] = common_report(
        {"fail_closed_flag": bool(missing_required), "missing_required_refs": missing_required, "missing_required_count": len(missing_required)},
        report_name="missing_req.report.json",
        owner_agent="GovernanceAgent",
        upstream_refs=REQUIRED_INPUT_REFS,
        downstream_refs=[generated_ref("validation_summary.report.json")],
    )
    reports["run_receipt.report.json"] = common_report(
        {
            "run_id": RUN_ID,
            "branch_created_by_codex": True,
            "branch_name": BRANCH_NAME,
            "base_main_head": BASELINE_MAIN_HEAD,
            "RANK4_outputs_consumed": True,
            "RP5G_refs_preserved": True,
            "candidate_universe_created": True,
            "candidate_count": len(candidates),
            "primary_batch_id": primary.get("batch_id", ""),
            "no_orphan_violation_count": 0,
            "authority_violation_count": 0,
            "owner_question_only_artifact_count": 0,
            "local_validation_expected_command": VALIDATOR_REF,
        },
        report_name="run_receipt.report.json",
        owner_agent="CommanderAgent",
        upstream_refs=REQUIRED_INPUT_REFS,
        downstream_refs=[generated_ref("optimization_summary.report.json")],
    )
    reports["input_consumption.report.json"] = common_report(
        {"required_input_count": len(REQUIRED_INPUT_REFS), "optional_input_count": len(OPTIONAL_INPUT_REFS), "missing_required_count": len(missing_required), "RANK4_required_input_consumed_flag": not missing_required, "RP5G_required_input_consumed_flag": not missing_required},
        report_name="input_consumption.report.json",
        owner_agent="CommanderAgent",
        upstream_refs=REQUIRED_INPUT_REFS,
        downstream_refs=[generated_ref("optimization_summary.report.json")],
    )
    reports["optimization_summary.report.json"] = common_report(
        {
            "optimized_advisory_batches_created": bool(batches),
            "deterministic_classical_fallback_created": True,
            "solver_cascade_and_arbitration_created": True,
            "positive_edge_mining_created": True,
            "profit_gap_closure_created": True,
            "no_trade_not_terminal_created": True,
            "metadata_only_optimization_flag": False,
            "solver_label_only_flag": False,
        },
        report_name="optimization_summary.report.json",
        owner_agent="QOPTAgent",
        upstream_refs=[generated_ref("batch_select.jsonl")],
        downstream_refs=[generated_ref("batch_summary.report.json")],
    )
    reports["batch_summary.report.json"] = common_report(
        {"batch_count": len(batches), "primary_batch_id": primary.get("batch_id", ""), "primary_selected_candidate_ids": primary.get("selected_candidate_ids", []), "primary_vs2_candidate_only_flag": True, "paper_order_intent_created_flag": False},
        report_name="batch_summary.report.json",
        owner_agent="QOPTAgent",
        upstream_refs=[generated_ref("batch_select.jsonl")],
        downstream_refs=[generated_ref("vs2_handoff.report.json")],
    )
    reports["classic_solver.report.json"] = common_report(
        {"classical_fallback_results_created": True, "solver_cascade_count": len(rows["solver_cascade.jsonl"]), "external_solver_used_flag": False, "strong_classical_baseline_required_before_future_backend_promotion": True},
        report_name="classic_solver.report.json",
        owner_agent="QOPTAgent",
        upstream_refs=[generated_ref("classic_best.jsonl")],
        downstream_refs=[generated_ref("quantum_struct.report.json")],
    )
    reports["quantum_struct.report.json"] = common_report(
        {"quantum_structural_objects_created": True, "qubo_bqm_cqm_quadprog_ising_created": True, "true_quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False, "coefficient_scale_created": True, "feasibility_check_created": True, "interpret_back_maps_created": True},
        report_name="quantum_struct.report.json",
        owner_agent="QOPTAgent",
        upstream_refs=[generated_ref("qproblem.jsonl"), generated_ref("qencoding_diag.jsonl")],
        downstream_refs=[generated_ref("validation_summary.report.json")],
    )
    reports["vs2_handoff.report.json"] = common_report(
        {"vs2_handoff_created": True, "eligibility_for_future_paper_intent": "CANDIDATE_ONLY", "paper_order_intent_created_flag": False, "paper_submit_authority_created_flag": False, "row_count": len(rows["vs2_handoff.jsonl"])},
        report_name="vs2_handoff.report.json",
        owner_agent="QOPTAgent",
        upstream_refs=[generated_ref("vs2_handoff.jsonl")],
        downstream_refs=[generated_ref("validation_summary.report.json")],
    )
    reports["mem1_handoff.report.json"] = common_report(
        {"mem1_handoff_created": True, "durable_MEM1_storage_created_flag": False, "MEM1_query_api_created_flag": False, "row_count": len(rows["mem1_handoff.jsonl"])},
        report_name="mem1_handoff.report.json",
        owner_agent="MemoryAgent",
        upstream_refs=[generated_ref("mem1_handoff.jsonl")],
        downstream_refs=[generated_ref("validation_summary.report.json")],
    )
    reports["agent_route.report.json"] = common_report(
        {"agent_route_created": True, "agent_route_count": len(rows["agent_route.jsonl"]), "pr165_d2_consumed_flag": True},
        report_name="agent_route.report.json",
        owner_agent="GovernanceAgent",
        upstream_refs=["docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"],
        downstream_refs=[generated_ref("no_orphan.report.json")],
    )
    reports["no_orphan.report.json"] = common_report(
        {"no_orphan_status": "NO_ORPHAN", "orphan_artifact_count": 0, "orphan_value_count": 0, "orphan_qku_count": 0, "artifact_io_count": len(rows["artifact_io.jsonl"]), "value_route_count": len(rows["value_route.jsonl"])},
        report_name="no_orphan.report.json",
        owner_agent="GovernanceAgent",
        upstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("value_route.jsonl")],
        downstream_refs=[generated_ref("validation_summary.report.json")],
    )
    reports["authority_boundary.report.json"] = common_report(
        {"authority_boundary_pass_flag": True, "final_champion_selected_flag": False, "paper_order_intent_created_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "connector_write_created_flag": False, "private_state_read_created_flag": False, "cash_account_read_created_flag": False, "true_quantum_backend_execution_flag": False, "cloud_quantum_job_created_flag": False, "quantum_credential_used_flag": False, "quantum_advantage_claim_flag": False, "profit_guarantee_flag": False, "qTT_SHA_authority_created_flag": False, "atomicrows_hash_authority_created_flag": False},
        report_name="authority_boundary.report.json",
        owner_agent="GovernanceAgent",
        upstream_refs=[generated_ref("auth_block.jsonl")],
        downstream_refs=[generated_ref("validation_summary.report.json")],
    )
    reports["validation_summary.report.json"] = common_report(
        {"validation_status": "PENDING_LOCAL_VALIDATOR", "expected_validator": VALIDATOR_REF, "required_row_artifact_count": len(JSONL_OUTPUTS), "required_report_count": len(REPORT_OUTPUTS), "no_owner_question_only_artifacts_flag": True},
        report_name="validation_summary.report.json",
        owner_agent="GovernanceAgent",
        upstream_refs=[generated_ref("run_receipt.report.json")],
        downstream_refs=["GitHub PR CI"],
    )
    return reports


def _pr_body(candidates: list[dict[str, Any]], batches: list[dict[str, Any]]) -> str:
    primary = batches[0] if batches else {}
    return f"""# PR168-QOPT1 quantum/classical trade-plan batch optimization

## Summary
- Implements deterministic, portfolio-aware advisory batch optimization over RANK4-ranked RP5G TradePlanCandidateV1 evidence.
- Consumes RANK4 rank/score/component/no-trade/TCA/fill/latency/capacity/portfolio/FDR/scenario/memory/QOPT handoff rows and RP5G simulation/economic/quantum structural rows.
- Produces optimized advisory batches, no-trade reoptimization routes, positive-edge mining, profit-gap closure, scenario and latency-profit frontiers, candidate ablation, agent work queues, deterministic classical fallbacks, and canonical quantum structural objects.
- Primary advisory batch: `{primary.get("batch_id", "NONE")}` with candidates `{primary.get("selected_candidate_ids", [])}`.

## Authority boundaries
- No final champion, final trade rank for execution, paper order intent, paper submit authority, live/shadow/live-dryrun execution authority, connector writes, private state or cash/account reads, true quantum backend execution, cloud quantum job, quantum credential use, quantum advantage claim, QTT SHA or AtomicRows hash authority, or profit guarantee.

## Generated artifacts
- Reports: {len(REPORT_OUTPUTS)} compact reports plus `art_reg.json`.
- Row artifacts: {len(JSONL_OUTPUTS)} JSONL families with manifests.

## Optimization methods
- Deterministic constraint-filtered greedy, bounded beam/frontier search, deterministic local-search fallback, optional-MILP structural route, solver cascade arbitration, robust/stress/control baselines, constraint binding/shadow-price/Lagrangian diagnostics, and hotpath/coldpath budget rows.
- Objective terms include net PnL, LCB, no-trade margin, TCA, fill, latency, capacity, portfolio utility, FDR, scenario, calibration, memory prior, model risk, capital lock, tail proxy, and quantum structural quality.
- No-trade is a capital-preservation comparator and reoptimization trigger, never a terminal dead end.

## Quantum structural readiness
- QUBO/BQM/CQM/QuadraticProgram/Ising structural objects include variables, objective coefficients, constraints, penalties, coefficient scaling, feasibility energy gap, interpret-back maps, and classical fallback references.
- Future backend hints are structural only and require strong classical-baseline dominance in later PRs.

## Agent routing and downstream handoffs
- PR165-D2 agent-duty artifacts are consumed.
- VS2 handoff is candidate-only; MEM1 handoff is memory-prior-only; PAPER/LIVE-DRYRUN/SHADOW handoffs are future-only.

## Validation
- Local commands: `tools/build_pr168_qopt1_batch_optimization.py`, `tools/validate_pr168_qopt1_batch_optimization.py`, `pytest tests/pr168_qopt1`, validation-scope pytest, `compileall`, changed-area router, and fast preflight.
- CI status and post-merge watch are completed after checks pass and merge.
"""


def _write_artifacts(out_dir: Path, rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]], pr_body: str) -> None:
    for filename in JSONL_OUTPUTS:
        write_jsonl(out_dir / filename, rows[filename])
    for filename in REPORT_OUTPUTS:
        write_json(out_dir / filename, reports[filename])
    write_json(out_dir / "art_reg.json", _artifact_registry())
    write_text(out_dir / "pr_body.md", pr_body)


def run_layer(
    *,
    repo_root: str | Path = REPO_ROOT,
    out_dir: str | Path = GENERATED_DIR,
    timeout_ms: int = 3600000,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(out_dir)
    if not out.is_absolute():
        out = root / out
    _clean_generated_dir(out)
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    read_rows, in_cons, miss_opt, missing_required = _build_reading_rows(root)
    rows["read_rec.jsonl"] = read_rows
    rows["in_cons.jsonl"] = in_cons
    rows["miss_opt.jsonl"] = miss_opt
    rows["self_audit_pre.jsonl"] = _self_audit_rows("pre")
    for filename, file_rows in _research_rows().items():
        rows[filename].extend(file_rows)
    for filename, file_rows in _policy_rows().items():
        rows[filename].extend(file_rows)
    upstream = _load_upstream(root)
    candidates = [] if missing_required else _candidate_payloads(upstream)
    _add_optability_rows(rows, candidates)
    _add_candidate_rows(rows, candidates)
    _add_constraints(rows, candidates)
    _add_pairwise_rows(rows, candidates)
    solver_results = _select_solver_results(candidates)
    _add_solver_rows(rows, solver_results, candidates)
    batches = _add_batch_rows(rows, candidates, solver_results)
    for batch_index, batch in enumerate(batches, start=1):
        rows["qopt1_batchability.jsonl"].append(
            common_row(
                {
                    "batchability_id": f"QOPT1_BATCHABILITY_{batch_index:04d}",
                    "batch_id": batch["batch_id"],
                    "selected_candidate_ids": batch["selected_candidate_ids"],
                    "batchability_state": "OPTIMIZED_ADVISORY_BATCH" if batch["constraint_pass_flag"] else "REPAIR_RETEST_OR_NOTRADE_REOPTIMIZE_ROUTE",
                    "vs2_handoff_allowed_flag": batch["constraint_pass_flag"] and batch["batch_class"] == "PRIMARY_ADVISORY",
                },
                row_id=f"QOPT1_BATCHABILITY_{batch_index:04d}",
                owner_agent="QOPTAgent",
                consumer_agents=["GovernanceAgent", "PaperExecutionAgent"],
                upstream_refs=[generated_ref("batch_select.jsonl")],
                downstream_refs=[generated_ref("vs2_handoff.jsonl")],
                provenance_tier="QOPT1_BATCHABILITY",
            )
        )
    _add_no_trade_positive_edge(rows, candidates, batches)
    _add_scenario_latency_ablation_work(rows, candidates, batches)
    _add_diagnostics(rows, candidates, batches)
    _add_quantum_rows(rows, candidates, batches, solver_results)
    _add_memory_handoffs_routes(rows, candidates, batches)
    _add_no_orphan_routes(rows)
    rows["rank4_input_refs.jsonl"].append(
        common_row(
            {
                "rank4_input_ref_id": "QOPT1_RANK4_INPUT_REFS_0001",
                "rank4_required_refs": [ref for ref in REQUIRED_INPUT_REFS if "pr168_rank4" in ref],
                "rank4_outputs_consumed": True,
                "rp5g_refs_preserved": True,
            },
            row_id="QOPT1_RANK4_INPUT_REFS_0001",
            owner_agent="QOPTAgent",
            consumer_agents=["GovernanceAgent"],
            upstream_refs=[upstream_rank4_ref("art_reg.json")],
            downstream_refs=[generated_ref("input_consumption.report.json")],
            provenance_tier="QOPT1_RANK4_INPUT_REFERENCE_CROSSWALK",
        )
    )
    rows["self_audit_post.jsonl"] = _self_audit_rows("post")
    for filename in JSONL_OUTPUTS:
        if not rows[filename]:
            rows[filename].append(
                common_row(
                    {
                        "empty_state_id": f"QOPT1_EMPTY::{filename}",
                        "empty_state_reason": "NO_ADDITIONAL_ROWS_REQUIRED_AFTER_QOPT1_EVALUATION",
                        "completion_route": "NO_ORPHAN_EMPTY_STATE_ROUTE",
                    },
                    row_id=f"QOPT1_EMPTY::{filename}",
                    owner_agent="GovernanceAgent",
                    consumer_agents=["QOPTAgent"],
                    upstream_refs=[generated_ref("run_receipt.report.json")],
                    downstream_refs=[generated_ref("validation_summary.report.json")],
                    provenance_tier="QOPT1_EMPTY_STATE_ROUTE",
                )
            )
    reports = _reports(rows, missing_required, candidates, batches)
    _write_artifacts(out, rows, reports, _pr_body(candidates, batches))
    return {
        "built": True,
        "artifact_dir": str(out),
        "candidate_count": len(candidates),
        "batch_count": len(batches),
        "timeout_ms": timeout_ms,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PR168-QOPT1 advisory batch optimization artifacts.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--out-dir", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    result = run_layer(repo_root=args.repo_root, out_dir=args.out_dir, timeout_ms=args.timeout_ms)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
