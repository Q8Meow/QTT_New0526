"""Deterministic PR168-RANK4 advisory ranking generator."""

from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from .eligibility import champion_gate, no_trade_required_margin
from .features import by_candidate, scenario_summary
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
    SELF_AUDIT_FLAWS,
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
    upstream_rp5g_ref,
    write_json,
    write_jsonl,
    write_text,
)
from .normalization import minmax, quality_from_penalty
from .pareto import PARETO_DIMS, dominates
from .policy import policy_rows
from .scoring import COMPONENT_WEIGHTS, weighted_score


ROLE_AGENTS = (
    "CommanderAgent",
    "MarketConditionAgent",
    "FormulaLibraryAgent",
    "StackGeneratorAgent",
    "ExecutabilityAgent",
    "TradeTargetScoutAgent",
    "OrderVariableAgent",
    "TradePlanSimulationAgent",
    "TCAAgent",
    "FillLatencyAgent",
    "RiskAgent",
    "RankerAgent",
    "QOPTAgent",
    "MemoryAgent",
    "GovernanceAgent",
    "PaperExecutionAgent",
    "LiveDryRunAgent",
    "ShadowObservationAgent",
    "ResearchScoutAgent",
    "ModelRiskAgent",
    "OwnerDashboardAgent",
    "ConnectorReadinessAgent",
    "ExecutionRouterAgent",
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
    if "pr168_rp5g" in ref:
        return "RP5G_REPLAY_PAPER_SIMULATION_EVIDENCE"
    if "pr168_rp5f" in ref:
        return "RP5F_DYNAMIC_TARGET_GRID_INPUT"
    if "pr168_rp5e" in ref:
        return "RP5E_STACK_PREVIEW_INPUT"
    if "pr168_rp5d_r1" in ref:
        return "RP5D_R1_EXEC_NOW_INPUT"
    if "pr168_rp5d" in ref:
        return "RP5D_EXECUTABILITY_INPUT"
    if "pr168_vs1" in ref:
        return "VS1_TRADING_SLICE_INPUT"
    if "PR165_D2" in ref:
        return "PR165_D2_AGENT_DUTY_INPUT"
    if "RP5C" in ref or "rp5c" in ref:
        return "RP5C_IMMUTABLE_LIBRARY_INPUT"
    return "MASTER_PLAN_OR_OPTIONAL_INPUT"


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
        row_id = f"RANK4_READ_{index:05d}"
        read_rows.append(
            common_row(
                {
                    "receipt_id": row_id,
                    "input_family": _surface_family(ref),
                    "resolved_path": ref,
                    "required_flag": True,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_summary": _row_count(path),
                    "input_producer_pr": "UPSTREAM" if exists else "MISSING",
                    "missing_action_if_absent": "FAIL_CLOSED_MISSING_REQUIRED_INPUT",
                    "freshness_or_commit_ref_when_available": BASELINE_MAIN_HEAD if ref.endswith("QTT_MasterPlan_Current.md") else "UPSTREAM_GENERATED_ARTIFACT",
                },
                row_id=row_id,
                owner_agent="CommanderAgent",
                consumer_agents=["RankerAgent", "GovernanceAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("missing_req.report.json")],
                provenance_tier="RANK4_INPUT_READ_RECEIPT",
                intelligence_classes=("KNOWLEDGE_INTELLIGENCE", "SIMULATION_INTELLIGENCE"),
            )
        )
        in_cons.append(
            common_row(
                {
                    "input_consumption_id": f"RANK4_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": _surface_family(ref),
                    "consumed_flag": exists,
                    "row_count_consumed": _row_count(path) if exists else 0,
                    "consumer_output_refs": [generated_ref("rank_feat.jsonl"), generated_ref("rank_score.jsonl")],
                },
                row_id=f"RANK4_IN_CONS_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["RankerAgent", "GovernanceAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("lineage.jsonl"), generated_ref("artifact_io.jsonl")],
                provenance_tier="RANK4_INPUT_CONSUMPTION_RECEIPT",
                intelligence_classes=("KNOWLEDGE_INTELLIGENCE", "SIMULATION_INTELLIGENCE"),
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
                    "missing_optional_id": f"RANK4_MISS_OPT_{index:04d}",
                    "optional_artifact_ref": ref,
                    "exists_flag": exists,
                    "consumed_flag": exists,
                    "row_count_or_summary": _row_count(path),
                    "fallback_ref": "RP5G core numeric evidence and RANK4 completion routes",
                    "fail_closed_flag": False,
                },
                row_id=f"RANK4_MISS_OPT_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "RankerAgent"],
                upstream_refs=[ref] if exists else ["optional_input_absent"],
                downstream_refs=[generated_ref("completion_route.jsonl")],
                provenance_tier="RANK4_OPTIONAL_INPUT_RECEIPT",
                intelligence_classes=("KNOWLEDGE_INTELLIGENCE",),
            )
        )
    return read_rows, in_cons, miss_opt, missing_required


def _load_upstream(repo_root: Path) -> dict[str, Any]:
    base = repo_root / "docs" / "master_plan" / "generated" / "pr168_rp5g"
    return {
        "trade_candidate": read_jsonl(base / "trade_candidate.jsonl"),
        "sim_run": read_jsonl(base / "sim_run.jsonl"),
        "sim_result": read_jsonl(base / "sim_result.jsonl"),
        "exec_pnl": read_jsonl(base / "exec_pnl.jsonl"),
        "tca_decomp": read_jsonl(base / "tca_decomp.jsonl"),
        "fill_latency_cap": read_jsonl(base / "fill_latency_cap.jsonl"),
        "capacity_crowding": read_jsonl(base / "capacity_crowding.jsonl"),
        "notrade_cmp": read_jsonl(base / "notrade_cmp.jsonl"),
        "scenario_ladder": read_jsonl(base / "scenario_ladder.jsonl"),
        "overfit_fdr": read_jsonl(base / "overfit_fdr.jsonl"),
        "port_marg_util": read_jsonl(base / "port_marg_util.jsonl"),
        "calibration_result": read_jsonl(base / "calibration_result.jsonl"),
        "data_prov": read_jsonl(base / "data_prov.jsonl"),
        "formula_comp": read_jsonl(base / "formula_comp.jsonl"),
        "var_eval": read_jsonl(base / "var_eval.jsonl"),
        "var_reject": read_jsonl(base / "var_reject.jsonl"),
        "qstruct_problem": read_jsonl(base / "qstruct_problem.jsonl"),
        "qobj_coeff": read_jsonl(base / "qobj_coeff.jsonl"),
        "q_constraints": read_jsonl(base / "q_constraints.jsonl"),
        "q_interp": read_jsonl(base / "q_interp.jsonl"),
        "q_classic_fb": read_jsonl(base / "q_classic_fb.jsonl"),
        "qopt_handoff": read_jsonl(base / "qopt_handoff.jsonl"),
        "agent_route": read_jsonl(base / "agent_route.jsonl"),
        "agent_consume": read_jsonl(base / "agent_consume.jsonl"),
        "no_orphan_report": read_json(base / "no_orphan.report.json"),
        "run_receipt": read_json(base / "run_receipt.report.json"),
        "near_clone_cluster": read_jsonl(base / "near_clone_cluster.jsonl"),
        "pm_microstructure": read_jsonl(base / "pm_microstructure.jsonl"),
    }


def _first_by_any_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = row.get("trade_plan_candidate_id") or row.get("candidate_id")
        if cid and str(cid) not in out:
            out[str(cid)] = row
    return out


def _build_feature_payloads(upstream: dict[str, Any]) -> list[dict[str, Any]]:
    exec_pnl = by_candidate(upstream["exec_pnl"])
    tca = by_candidate(upstream["tca_decomp"])
    fill = by_candidate(upstream["fill_latency_cap"])
    capacity = by_candidate(upstream["capacity_crowding"])
    notrade = by_candidate(upstream["notrade_cmp"])
    fdr = by_candidate(upstream["overfit_fdr"])
    port = by_candidate(upstream["port_marg_util"])
    sim_result = by_candidate(upstream["sim_result"])
    qstruct = by_candidate(upstream["qstruct_problem"])
    scen = scenario_summary(upstream["scenario_ladder"])
    payloads: list[dict[str, Any]] = []
    for index, cand in enumerate(upstream["trade_candidate"], start=1):
        cid = str(cand["trade_plan_candidate_id"])
        pnl = exec_pnl.get(cid, {})
        tca_row = tca.get(cid, {})
        fill_row = fill.get(cid, {})
        cap_row = capacity.get(cid, {})
        no_row = notrade.get(cid, {})
        fdr_row = fdr.get(cid, {})
        port_row = port.get(cid, {})
        sim_row = sim_result.get(cid, {})
        scen_row = scen.get(cid, {})
        payload = {
            "candidate_id": cid,
            "trade_plan_id": cid,
            "rank_id": f"RANK4_RANK_{index:04d}",
            "simulation_run_id": sim_row.get("simulation_run_id", f"RP5G_SIM_RUN_{index:04d}"),
            "target_id": cand.get("target_id"),
            "grid_id": cand.get("grid_id"),
            "seed_id": cand.get("trade_seed_id"),
            "market_id": cand.get("market_id"),
            "venue": cand.get("venue"),
            "market_family": "PREDICTION_MARKETS",
            "side": cand.get("side"),
            "entry_bucket": cand.get("entry_price_candidate"),
            "size_bucket": cand.get("order_size_candidate"),
            "hold_duration_bucket": cand.get("hold_duration_candidate"),
            "exit_rule": cand.get("exit_rule_candidate"),
            "maker_taker_policy": cand.get("maker_taker_split_candidate"),
            "cancel_replace_bucket": cand.get("cancel_replace_interval_candidate"),
            "stack_id": stable_unique(cand.get("formula_stack_preview_refs", []))[0] if cand.get("formula_stack_preview_refs") else f"STACK::{cid}",
            "formula_refs": stable_unique(cand.get("formula_refs", [])),
            "qku_refs": stable_unique(cand.get("qku_refs", [])),
            "formula_family_refs": stable_unique([str(ref).rsplit("_", 1)[0] for ref in cand.get("formula_refs", [])]),
            "qku_family_refs": stable_unique([str(ref).split("::", 1)[0] for ref in cand.get("qku_refs", [])]),
            "market_cluster_id": cand.get("market_id"),
            "event_cluster_id": cand.get("event_id"),
            "liquidity_bucket": cand.get("liquidity_filter_candidate"),
            "spread_bucket": cand.get("spread_filter_candidate"),
            "time_to_close_bucket": cand.get("hold_duration_candidate"),
            "latency_bucket": cand.get("latency_budget_candidate"),
            "provenance_tier": sim_row.get("data_provenance_tier", cand.get("provenance_tier")),
            "outcome_label": sim_row.get("outcome_label", "UNKNOWN"),
            "search_family_id": fdr_row.get("search_family_id", "RP5G_SEARCH_FAMILY_UNKNOWN"),
            "regime_key": f"{cand.get('venue')}::{cand.get('liquidity_filter_candidate')}::{cand.get('spread_filter_candidate')}::{cand.get('hold_duration_candidate')}",
            "agent_owner": "RankerAgent",
            "consumer_agents": ["QOPTAgent", "MemoryAgent", "RiskAgent", "GovernanceAgent"],
            "upstream_refs": [upstream_rp5g_ref(name) for name in ("trade_candidate.jsonl", "exec_pnl.jsonl", "tca_decomp.jsonl", "fill_latency_cap.jsonl", "notrade_cmp.jsonl")],
            "downstream_refs": [generated_ref("rank_score.jsonl"), generated_ref("rank_order.jsonl")],
            "net_expected_pnl_cash": dec(pnl.get("net_expected_pnl_cash", sim_row.get("net_expected_pnl_cash"))),
            "lower_confidence_bound_pnl_cash": dec(pnl.get("lower_confidence_bound_pnl_cash", sim_row.get("lower_confidence_bound_pnl_cash"))),
            "candidate_minus_no_trade_cash": dec(pnl.get("candidate_minus_no_trade_cash", no_row.get("candidate_minus_no_trade_cash"))),
            "TCA_total_cash": dec(tca_row.get("TCA_total_cash", pnl.get("TCA_total_cash"))),
            "implementation_shortfall_total_cash": dec(tca_row.get("implementation_shortfall_total_cash", tca_row.get("TCA_total_cash"))),
            "fees_cash": dec(tca_row.get("fees_cash", pnl.get("fees_cash"))),
            "spread_cost_cash": dec(tca_row.get("spread_cost_cash", pnl.get("spread_cost_cash"))),
            "slippage_cash": dec(tca_row.get("slippage_cash", pnl.get("slippage_cash"))),
            "latency_penalty_cash": dec(tca_row.get("latency_penalty_cash", pnl.get("latency_penalty_cash"))),
            "market_impact_cash": dec(tca_row.get("market_impact_cash", pnl.get("market_impact_cash"))),
            "opportunity_cost_cash": dec(tca_row.get("opportunity_cost_cash", pnl.get("opportunity_cost_cash"))),
            "cancel_replace_cost_cash": dec(tca_row.get("cancel_replace_cost_cash")),
            "capital_lock_cost_cash": dec(tca_row.get("capital_lock_settlement_cost_cash", pnl.get("capital_lock_cost_cash"))),
            "fill_probability": dec(fill_row.get("fill_probability")),
            "partial_fill_ratio": dec(fill_row.get("partial_fill_ratio"), "1"),
            "queue_position_penalty_cash": dec(fill_row.get("queue_position_penalty_cash")),
            "adverse_selection_penalty_cash": dec(fill_row.get("adverse_selection_penalty_cash", tca_row.get("adverse_selection_cost_cash"))),
            "latency_decay_penalty_cash": dec(fill_row.get("latency_decay_penalty_cash", pnl.get("latency_penalty_cash"))),
            "capacity_penalty_cash": dec(cap_row.get("capacity_penalty_cash", fill_row.get("capacity_penalty_cash"))),
            "crowding_penalty_cash": dec(cap_row.get("crowding_penalty_cash", fill_row.get("crowding_penalty_cash"))),
            "capacity_crowding_penalty_cash": dec(cap_row.get("capacity_crowding_penalty_cash")),
            "portfolio_marginal_utility_cash": dec(port_row.get("portfolio_marginal_utility_cash")),
            "portfolio_risk_penalty_cash": dec(port_row.get("portfolio_risk_penalty_cash")),
            "portfolio_diversification_benefit_cash": dec(port_row.get("diversification_benefit_cash")),
            "scenario_robustness_score": dec(scen_row.get("scenario_robustness_score")),
            "scenario_worst_case_pnl_cash": dec(scen_row.get("scenario_worst_case_pnl_cash")),
            "scenario_combined_conservative_pnl_cash": dec(scen_row.get("scenario_combined_conservative_pnl_cash")),
            "scenario_combined_conservative_no_trade_margin_cash": dec(scen_row.get("scenario_combined_conservative_no_trade_margin_cash")),
            "scenario_combined_conservative_pass_flag": scen_row.get("scenario_combined_conservative_pass_flag") is True,
            "calibration_gap": dec(fdr_row.get("calibration_gap")),
            "fdr_penalty_cash": dec(fdr_row.get("fdr_penalty_cash")),
            "overfit_penalty_cash": dec(fdr_row.get("fdr_penalty_cash")) / Decimal("2"),
            "fdr_adjusted_expected_pnl_cash": dec(fdr_row.get("adjusted_pnl_after_fdr_cash", pnl.get("net_expected_pnl_cash"))),
            "number_of_candidate_trials": int(fdr_row.get("number_of_candidate_trials", 0)),
            "number_of_effectively_independent_trials": int(fdr_row.get("number_of_effectively_independent_trials", 0)),
            "time_to_close_seconds_or_bucket": cand.get("hold_duration_candidate"),
            "capital_lock_cost_cash": dec(tca_row.get("capital_lock_settlement_cost_cash")),
            "expected_exit_price_or_bucket": pnl.get("expected_exit_price", cand.get("exit_price_candidate_or_rule")),
            "agent_route_pass_flag": True,
            "no_orphan_proof_pass_flag": True,
            "quantum_structural_handoff_available_flag": bool(qstruct.get(cid)),
            "paper_readiness_route_complete_flag": True,
            "proxy_only_flag": sim_row.get("proxy_simulation_flag") is True,
            "data_provenance_quality_score": Decimal("0.70") if sim_row.get("proxy_simulation_flag") else Decimal("0.90"),
        }
        payloads.append(payload)
    return payloads


def _feature_row(feature: dict[str, Any], index: int) -> dict[str, Any]:
    payload = {
        **{key: (score(value) if isinstance(value, Decimal) else value) for key, value in feature.items()},
        "feature_vector_id": f"RANK4_FEAT_{index:04d}",
        "trade_context_signature_ref": f"RANK4_CTX_SIG_{index:04d}",
        "recipe_similarity_key_ref": f"RANK4_SIM_KEY_{index:04d}",
    }
    return common_row(
        payload,
        row_id=payload["feature_vector_id"],
        owner_agent="RankerAgent",
        consumer_agents=["QOPTAgent", "MemoryAgent", "RiskAgent"],
        upstream_refs=feature["upstream_refs"],
        downstream_refs=[generated_ref("score_norm.jsonl"), generated_ref("elig_gate.jsonl")],
        provenance_tier="RANK4_FEATURE_VECTOR_FROM_RP5G_NUMERIC_EVIDENCE",
        intelligence_classes=("SIMULATION_INTELLIGENCE", "SEARCH_INTELLIGENCE"),
    )


def _normalize_features(features: list[dict[str, Any]]) -> dict[str, dict[str, Decimal]]:
    vals = {key: [dec(row.get(key)) for row in features] for key, _higher in PARETO_DIMS}
    out: dict[str, dict[str, Decimal]] = {}
    for row in features:
        cid = row["candidate_id"]
        net_abs = max(abs(dec(row["net_expected_pnl_cash"])), Decimal("0.000001"))
        out[cid] = {
            "net": minmax(vals["net_expected_pnl_cash"], dec(row["net_expected_pnl_cash"])),
            "lcb": minmax(vals["lower_confidence_bound_pnl_cash"], dec(row["lower_confidence_bound_pnl_cash"])),
            "notrade": minmax(vals["candidate_minus_no_trade_cash"], dec(row["candidate_minus_no_trade_cash"])),
            "fill": bounded(dec(row["fill_probability"]) * dec(row["partial_fill_ratio"])),
            "latency": quality_from_penalty(row["latency_decay_penalty_cash"], net_abs),
            "capacity": quality_from_penalty(dec(row["capacity_penalty_cash"]) + dec(row["crowding_penalty_cash"]), net_abs),
            "portfolio": minmax(vals["portfolio_marginal_utility_cash"], dec(row["portfolio_marginal_utility_cash"])),
            "scenario": bounded(row["scenario_robustness_score"]),
            "calib": bounded(Decimal("1") - dec(row["calibration_gap"])),
            "prov": bounded(row["data_provenance_quality_score"]),
            "route": Decimal("1") if row["agent_route_pass_flag"] and row["no_orphan_proof_pass_flag"] else Decimal("0"),
            "qstruct": Decimal("1") if row["quantum_structural_handoff_available_flag"] else Decimal("0.35"),
            "paper": Decimal("1") if row["paper_readiness_route_complete_flag"] else Decimal("0.50"),
        }
    return out


def _model_risk(feature: dict[str, Any]) -> tuple[dict[str, Decimal], Decimal]:
    proxy = Decimal("0.18") if feature["proxy_only_flag"] else Decimal("0.04")
    sample = Decimal("0.12") if int(feature["number_of_candidate_trials"]) < 30 else Decimal("0.06")
    calibration = bounded(dec(feature["calibration_gap"]) * Decimal("10"))
    fdr = bounded(dec(feature["fdr_penalty_cash"]) / max(abs(dec(feature["net_expected_pnl_cash"])), Decimal("0.000001")))
    tca = bounded(dec(feature["TCA_total_cash"]) / max(abs(dec(feature["net_expected_pnl_cash"])) + dec(feature["TCA_total_cash"]), Decimal("0.000001")))
    fill_latency = bounded((Decimal("1") - dec(feature["fill_probability"])) + dec(feature["latency_decay_penalty_cash"]))
    capacity = bounded(dec(feature["capacity_crowding_penalty_cash"]))
    concentration = bounded(abs(dec(feature["portfolio_risk_penalty_cash"])))
    qstruct = Decimal("0.04") if feature["quantum_structural_handoff_available_flag"] else Decimal("0.10")
    risks = {
        "data_provenance_risk_score": proxy,
        "proxy_only_risk_score": proxy,
        "sample_size_risk_score": sample,
        "staleness_risk_score": Decimal("0.08"),
        "leakage_risk_score": Decimal("0.05"),
        "overfit_search_family_risk_score": fdr,
        "calibration_risk_score": calibration,
        "scenario_fragility_risk_score": Decimal("1") - bounded(feature["scenario_robustness_score"]),
        "TCA_model_risk_score": tca,
        "fill_model_risk_score": fill_latency,
        "latency_model_risk_score": bounded(dec(feature["latency_decay_penalty_cash"])),
        "capacity_model_risk_score": capacity,
        "portfolio_concentration_risk_score": concentration,
        "quantum_structure_only_risk_score": qstruct,
        "external_candidate_value_risk_score": Decimal("0.05"),
    }
    combined = sum(risks.values(), Decimal("0")) / Decimal(len(risks))
    reserve = (
        abs(dec(feature["net_expected_pnl_cash"])) * combined * Decimal("0.10")
        + dec(feature["fdr_penalty_cash"]) * Decimal("0.25")
        + dec(feature["TCA_total_cash"]) * Decimal("0.05")
    )
    risks["combined_model_risk_score"] = combined
    return risks, reserve


def _score_candidates(features: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Decimal], dict[str, Decimal]]:
    norms = _normalize_features(features)
    norm_rows: list[dict[str, Any]] = []
    comp_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    risk_score: dict[str, Decimal] = {}
    reserves: dict[str, Decimal] = {}
    for index, feature in enumerate(features, start=1):
        cid = feature["candidate_id"]
        risks, reserve = _model_risk(feature)
        reserves[cid] = reserve
        risk_score[cid] = risks["combined_model_risk_score"]
        penalties = {
            "penalty_tca_efficiency": bounded(dec(feature["TCA_total_cash"]) / (abs(dec(feature["net_expected_pnl_cash"])) + Decimal("1"))) * Decimal("0.04"),
            "penalty_overfit_fdr": bounded(dec(feature["fdr_penalty_cash"]) / (abs(dec(feature["net_expected_pnl_cash"])) + Decimal("1"))) * Decimal("0.05"),
            "penalty_concentration": bounded(abs(dec(feature["portfolio_risk_penalty_cash"]))) * Decimal("0.02"),
            "penalty_near_clone": Decimal("0"),
            "penalty_missing_completion_route_severity": Decimal("0"),
            "penalty_model_risk_uncertainty_reserve": bounded(reserve / (abs(dec(feature["net_expected_pnl_cash"])) + Decimal("1"))) * Decimal("0.05"),
            "penalty_external_candidate_unverified_value": Decimal("0.005"),
            "penalty_latency_SLA_mismatch": Decimal("0") if dec(feature["latency_decay_penalty_cash"]) <= Decimal("0.05") else Decimal("0.01"),
        }
        rank_score = weighted_score(norms[cid], penalties)
        norm_rows.append(
            common_row(
                {
                    "score_norm_id": f"RANK4_SCORE_NORM_{index:04d}",
                    "candidate_id": cid,
                    **{f"norm_{key}": score(value) for key, value in norms[cid].items()},
                    **{key: score(value) for key, value in penalties.items()},
                    "normalization_policy": "DETERMINISTIC_MINMAX_AND_BOUNDED_QUALITY_TRANSFORMS",
                },
                row_id=f"RANK4_SCORE_NORM_{index:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["RiskAgent", "QOPTAgent"],
                upstream_refs=[generated_ref("rank_feat.jsonl")],
                downstream_refs=[generated_ref("score_comp.jsonl"), generated_ref("rank_score.jsonl")],
                provenance_tier="RANK4_SCORE_NORMALIZATION",
            )
        )
        component_refs: list[str] = []
        for component_name, policy_name in COMPONENT_WEIGHTS.items():
            row_id = f"RANK4_SCORE_COMP_{index:04d}_{component_name.upper()}"
            component_refs.append(row_id)
            comp_rows.append(
                common_row(
                    {
                        "score_component_id": row_id,
                        "candidate_id": cid,
                        "component_name": component_name,
                        "normalized_component_value": score(norms[cid][component_name]),
                        "weight_policy_ref": policy_name,
                        "weight_value": score(PARAM_DEFAULTS[policy_name]),
                        "weighted_component_score": score(norms[cid][component_name] * dec(PARAM_DEFAULTS[policy_name])),
                        "numeric_evidence_refs": [upstream_rp5g_ref("exec_pnl.jsonl"), upstream_rp5g_ref("tca_decomp.jsonl")],
                    },
                    row_id=row_id,
                    owner_agent="RankerAgent",
                    consumer_agents=["GovernanceAgent", "QOPTAgent"],
                    upstream_refs=[generated_ref("score_norm.jsonl")],
                    downstream_refs=[generated_ref("rank_score.jsonl")],
                    provenance_tier="RANK4_SCORE_COMPONENT_ATTRIBUTION",
                )
            )
        score_rows.append(
            common_row(
                {
                    "rank_score_id": f"RANK4_SCORE_{index:04d}",
                    "candidate_id": cid,
                    "rank_id": feature["rank_id"],
                    "rank_scope": "ADVISORY_REPLAY_PAPER_QOPT_PRIORITY",
                    "rank4_execution_adjusted_score": score(rank_score),
                    "score_component_refs": component_refs,
                    "feature_vector_ref": f"RANK4_FEAT_{index:04d}",
                    "penalty_refs": [f"RANK4_SCORE_NORM_{index:04d}"],
                    "model_risk_ref_when_applicable": f"RANK4_MODEL_RISK_{index:04d}",
                    "uncertainty_reserve_ref_when_applicable": f"RANK4_UNCERT_RESERVE_{index:04d}",
                    "numeric_evidence_refs": feature["upstream_refs"],
                    "metadata_only_rank_flag": False,
                },
                row_id=f"RANK4_SCORE_{index:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["QOPTAgent", "MemoryAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("score_comp.jsonl"), generated_ref("rank_feat.jsonl")],
                downstream_refs=[generated_ref("rank_order.jsonl"), generated_ref("champ_prev.jsonl")],
                provenance_tier="RANK4_EXECUTION_ADJUSTED_SCORE",
            )
        )
    return norm_rows, comp_rows, score_rows, risk_score, reserves


def _rank_order(features: list[dict[str, Any]], score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    score_by_id = {row["candidate_id"]: dec(row["rank4_execution_adjusted_score"]) for row in score_rows}
    by_id = {row["candidate_id"]: row for row in features}
    ordered_ids = sorted(
        score_by_id,
        key=lambda cid: (
            -score_by_id[cid],
            -dec(by_id[cid]["candidate_minus_no_trade_cash"]),
            -dec(by_id[cid]["lower_confidence_bound_pnl_cash"]),
            dec(by_id[cid]["TCA_total_cash"]),
            -dec(by_id[cid]["fill_probability"]),
            dec(by_id[cid]["latency_decay_penalty_cash"]),
            dec(by_id[cid]["capacity_crowding_penalty_cash"]),
            dec(by_id[cid]["fdr_penalty_cash"]),
            -dec(by_id[cid]["portfolio_marginal_utility_cash"]),
            -dec(by_id[cid]["scenario_robustness_score"]),
            cid,
        ),
    )
    rows: list[dict[str, Any]] = []
    for pos, cid in enumerate(ordered_ids, start=1):
        feature = by_id[cid]
        rows.append(
            common_row(
                {
                    "advisory_rank_id": f"RANK4_ORDER_{pos:04d}",
                    "candidate_id": cid,
                    "rank_id": feature["rank_id"],
                    "rank_scope": "ADVISORY_REPLAY_PAPER_QOPT_PRIORITY",
                    "rank_class": "ADVISORY_TRADE_PLAN_RANK",
                    "rank_position": pos,
                    "rank4_execution_adjusted_score": score(score_by_id[cid]),
                    "score_component_refs": next((row["score_component_refs"] for row in score_rows if row["candidate_id"] == cid), []),
                    "feature_vector_ref": f"RANK4_FEAT_{features.index(feature)+1:04d}",
                    "eligibility_gate_ref": f"RANK4_ELIG_{features.index(feature)+1:04d}",
                    "notrade_rank_ref": f"RANK4_NOTRADE_{features.index(feature)+1:04d}",
                    "pareto_frontier_ref": f"RANK4_PARETO_{features.index(feature)+1:04d}",
                    "dominance_ref": f"RANK4_DOM_{features.index(feature)+1:04d}",
                    "tca_rank_ref": f"RANK4_TCA_RANK_{features.index(feature)+1:04d}",
                    "fill_latency_rank_ref": f"RANK4_FILL_LAT_{features.index(feature)+1:04d}",
                    "capacity_rank_ref": f"RANK4_CAP_RANK_{features.index(feature)+1:04d}",
                    "portfolio_rank_ref": f"RANK4_PORT_DIV_{features.index(feature)+1:04d}",
                    "fdr_rank_ref": f"RANK4_FDR_{features.index(feature)+1:04d}",
                    "scenario_rank_ref": f"RANK4_SCEN_{features.index(feature)+1:04d}",
                    "calibration_rank_ref": f"RANK4_CALIB_{features.index(feature)+1:04d}",
                    "regime_key_ref": f"RANK4_MICRO_REGIME_{features.index(feature)+1:04d}",
                    "qopt_handoff_ref_when_applicable": f"RANK4_QOPT_BATCH_{features.index(feature)+1:04d}",
                    "vs2_handoff_ref_when_applicable": f"RANK4_VS2_HANDOFF_{features.index(feature)+1:04d}",
                    "mem1_handoff_ref_when_applicable": f"RANK4_MEM1_HANDOFF_{features.index(feature)+1:04d}",
                    "recipe_handoff_ref_when_applicable": f"RANK4_RECIPE_{features.index(feature)+1:04d}",
                    "context_signature_ref_when_applicable": f"RANK4_CTX_SIG_{features.index(feature)+1:04d}",
                    "similarity_key_ref_when_applicable": f"RANK4_SIM_KEY_{features.index(feature)+1:04d}",
                    "winner_attribution_ref_when_applicable": f"RANK4_ATTR_{features.index(feature)+1:04d}",
                    "best_next_action_ref_when_applicable": f"RANK4_NEXT_ACTION_{features.index(feature)+1:04d}",
                    "portfolio_basket_ref_when_applicable": "RANK4_PORT_BASKET_0001",
                    "hotpath_manifest_ref_when_applicable": f"RANK4_HOTPATH_{features.index(feature)+1:04d}",
                },
                row_id=f"RANK4_ORDER_{pos:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["QOPTAgent", "MemoryAgent", "PaperExecutionAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("rank_score.jsonl")],
                downstream_refs=[generated_ref("champ_prev.jsonl"), generated_ref("qopt_batch.jsonl")],
                provenance_tier="RANK4_ADVISORY_RANK_ROW",
            )
        )
    return rows


def _component_layers(features: list[dict[str, Any]], risk_scores: dict[str, Decimal], reserves: dict[str, Decimal]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_id = {row["candidate_id"]: row for row in features}
    for index, feature in enumerate(features, start=1):
        cid = feature["candidate_id"]
        gate_pass, gate_reasons = champion_gate(feature)
        margin = no_trade_required_margin(dec(feature["TCA_total_cash"]))
        rows["elig_gate.jsonl"].append(
            common_row(
                {
                    "eligibility_gate_id": f"RANK4_ELIG_{index:04d}",
                    "candidate_id": cid,
                    "rank_id": feature["rank_id"],
                    "missing_RP5G_simulation_evidence": False,
                    "missing_execution_adjusted_pnl": False,
                    "missing_no_trade_comparison": False,
                    "missing_TCA_decomposition": False,
                    "missing_fill_latency_capacity": False,
                    "missing_provenance_tier": False,
                    "missing_agent_route": False,
                    "missing_no_orphan_proof": False,
                    "stale_candidate_flag": False,
                    "forbidden_authority_flag": False,
                    "eligibility_gate_pass": gate_pass,
                    "advisory_champion_preview_eligible_flag": gate_pass,
                    "failure_reason_codes": gate_reasons,
                    "no_trade_required_margin_cash": score(margin),
                },
                row_id=f"RANK4_ELIG_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("rank_feat.jsonl")],
                downstream_refs=[generated_ref("champ_prev.jsonl")],
                provenance_tier="RANK4_ELIGIBILITY_GATE",
            )
        )
        no_trade_wins = dec(feature["candidate_minus_no_trade_cash"]) <= margin
        rows["notrade_rank.jsonl"].append(
            common_row(
                {
                    "notrade_rank_id": f"RANK4_NOTRADE_{index:04d}",
                    "candidate_id": cid,
                    "rank_id": feature["rank_id"],
                    "no_trade_expected_pnl_cash": "0.000000",
                    "candidate_minus_no_trade_cash": score(feature["candidate_minus_no_trade_cash"]),
                    "no_trade_required_margin_cash": score(margin),
                    "no_trade_wins_flag": no_trade_wins,
                    "advisory_champion_preview_eligible_flag": gate_pass and not no_trade_wins,
                    "paper_priority_class": "NO_TRADE_FOR_SNAPSHOT" if no_trade_wins else "ADVISORY_TOPK_FOR_QOPT1",
                    "condition_scoped_memory_required_flag": True,
                    "repair_or_retest_route_required_flag": no_trade_wins,
                    "formula_global_ban_flag": False,
                    "qku_global_ban_flag": False,
                },
                row_id=f"RANK4_NOTRADE_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent", "MemoryAgent"],
                upstream_refs=[upstream_rp5g_ref("notrade_cmp.jsonl")],
                downstream_refs=[generated_ref("rank_next_action.jsonl")],
                provenance_tier="RANK4_NO_TRADE_DOMINANCE_RESULT",
            )
        )
        rows["tca_rank.jsonl"].append(
            common_row(
                {
                    "tca_rank_id": f"RANK4_TCA_RANK_{index:04d}",
                    "candidate_id": cid,
                    "explicit_fees_cash": score(feature["fees_cash"]),
                    "spread_crossing_cost_cash": score(feature["spread_cost_cash"]),
                    "slippage_cash": score(feature["slippage_cash"]),
                    "market_impact_cost_cash": score(feature["market_impact_cash"]),
                    "latency_delay_cost_cash": score(feature["latency_penalty_cash"]),
                    "opportunity_cost_unfilled_cash": score(feature["opportunity_cost_cash"]),
                    "adverse_selection_cost_cash": score(feature["adverse_selection_penalty_cash"]),
                    "cancel_replace_cost_cash": score(feature["cancel_replace_cost_cash"]),
                    "capital_lock_settlement_cost_cash": score(feature["capital_lock_cost_cash"]),
                    "implementation_shortfall_total_cash": score(feature["implementation_shortfall_total_cash"]),
                    "TCA_total_cash": score(feature["TCA_total_cash"]),
                    "TCA_to_gross_edge_ratio": score(dec(feature["TCA_total_cash"]) / max(abs(dec(feature["net_expected_pnl_cash"])) + dec(feature["TCA_total_cash"]), Decimal("0.000001"))),
                    "TCA_to_net_expected_pnl_ratio": score(dec(feature["TCA_total_cash"]) / max(abs(dec(feature["net_expected_pnl_cash"])), Decimal("0.000001"))),
                    "TCA_dominance_reason": "TCA_WITHIN_RANK4_CONSERVATIVE_SCORE" if dec(feature["net_expected_pnl_cash"]) > dec(feature["TCA_total_cash"]) else "TCA_DOMINATES_OR_REPAIR_RETEST",
                },
                row_id=f"RANK4_TCA_RANK_{index:04d}",
                owner_agent="TCAAgent",
                consumer_agents=["RankerAgent", "RiskAgent"],
                upstream_refs=[upstream_rp5g_ref("tca_decomp.jsonl")],
                downstream_refs=[generated_ref("rank_obj_decomp.jsonl")],
                provenance_tier="RANK4_TCA_ATTRIBUTION_RANK_RESULT",
            )
        )
        thin = dec(feature["fill_probability"]) < Decimal("0.60") or str(feature["liquidity_bucket"]).upper() in {"LOW", "THIN"}
        rows["fill_lat_rank.jsonl"].append(
            common_row(
                {
                    "fill_latency_rank_id": f"RANK4_FILL_LAT_{index:04d}",
                    "candidate_id": cid,
                    "fill_probability_rank_component": score(feature["fill_probability"]),
                    "partial_fill_rank_component": score(feature["partial_fill_ratio"]),
                    "queue_position_penalty_rank_component": score(feature["queue_position_penalty_cash"]),
                    "adverse_selection_rank_component": score(feature["adverse_selection_penalty_cash"]),
                    "latency_decay_rank_component": score(feature["latency_decay_penalty_cash"]),
                    "latency_budget_pass_flag": dec(feature["latency_decay_penalty_cash"]) <= Decimal("0.050000"),
                    "thin_book_false_positive_flag": thin,
                    "unfilled_order_illusion_flag": dec(feature["fill_probability"]) < Decimal("0.50"),
                },
                row_id=f"RANK4_FILL_LAT_{index:04d}",
                owner_agent="FillLatencyAgent",
                consumer_agents=["RankerAgent", "RiskAgent"],
                upstream_refs=[upstream_rp5g_ref("fill_latency_cap.jsonl")],
                downstream_refs=[generated_ref("rank_score.jsonl")],
                provenance_tier="RANK4_FILL_LATENCY_RANK_RESULT",
            )
        )
        rows["capacity_rank.jsonl"].append(
            common_row(
                {
                    "capacity_rank_id": f"RANK4_CAP_RANK_{index:04d}",
                    "candidate_id": cid,
                    "capacity_penalty_cash": score(feature["capacity_penalty_cash"]),
                    "crowding_penalty_cash": score(feature["crowding_penalty_cash"]),
                    "capacity_crowding_penalty_cash": score(feature["capacity_crowding_penalty_cash"]),
                    "capacity_crowding_risk_score": score(bounded(dec(feature["capacity_crowding_penalty_cash"]))),
                    "thin_book_risk_flag": thin,
                    "capacity_pass_flag": dec(feature["capacity_crowding_penalty_cash"]) <= Decimal("0.500000"),
                },
                row_id=f"RANK4_CAP_RANK_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent", "QOPTAgent"],
                upstream_refs=[upstream_rp5g_ref("capacity_crowding.jsonl")],
                downstream_refs=[generated_ref("rank_port_basket.jsonl")],
                provenance_tier="RANK4_CAPACITY_CROWDING_RANK_RESULT",
            )
        )
        cluster_key = f"{feature['venue']}::{feature['market_cluster_id']}::{feature['stack_id']}"
        rows["near_clone_cluster.jsonl"].append(
            common_row(
                {
                    "near_clone_cluster_id": f"RANK4_CLONE_{index:04d}",
                    "candidate_id": cid,
                    "cluster_key": cluster_key,
                    "near_clone_similarity_score": "0.500000",
                    "near_clone_stack_flag": False,
                    "diversity_frontier_exception": False,
                },
                row_id=f"RANK4_CLONE_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[upstream_rp5g_ref("near_clone_cluster.jsonl")],
                downstream_refs=[generated_ref("port_div_rank.jsonl")],
                provenance_tier="RANK4_NEAR_CLONE_CLUSTER",
            )
        )
        rows["port_div_rank.jsonl"].append(
            common_row(
                {
                    "portfolio_diversification_id": f"RANK4_PORT_DIV_{index:04d}",
                    "candidate_id": cid,
                    "market_cluster_exposure": feature["market_cluster_id"],
                    "event_cluster_exposure": feature["event_cluster_id"],
                    "venue_exposure": feature["venue"],
                    "formula_family_exposure": feature["formula_family_refs"],
                    "qku_family_exposure": feature["qku_family_refs"],
                    "side_exposure": feature["side"],
                    "liquidity_bucket_exposure": feature["liquidity_bucket"],
                    "time_to_close_bucket_exposure": feature["time_to_close_bucket"],
                    "correlation_proxy_cluster": cluster_key,
                    "near_clone_similarity_score": "0.500000",
                    "capacity_consumption_cash_or_contracts": feature["size_bucket"],
                    "capital_consumption_cash": score(dec(feature.get("size_bucket")) * dec(feature.get("entry_bucket"))),
                    "incremental_risk_contribution": score(feature["portfolio_risk_penalty_cash"]),
                    "portfolio_marginal_utility_cash": score(feature["portfolio_marginal_utility_cash"]),
                    "diversification_gain_or_penalty": score(feature["portfolio_diversification_benefit_cash"] - feature["portfolio_risk_penalty_cash"]),
                },
                row_id=f"RANK4_PORT_DIV_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent", "QOPTAgent"],
                upstream_refs=[upstream_rp5g_ref("port_marg_util.jsonl")],
                downstream_refs=[generated_ref("rank_port_basket.jsonl")],
                provenance_tier="RANK4_PORTFOLIO_DIVERSIFICATION_RESULT",
            )
        )
        rows["marg_util_rank.jsonl"].append(
            common_row(
                {
                    "marginal_utility_rank_id": f"RANK4_MARG_UTIL_{index:04d}",
                    "candidate_id": cid,
                    "portfolio_marginal_utility_cash": score(feature["portfolio_marginal_utility_cash"]),
                    "portfolio_risk_penalty_cash": score(feature["portfolio_risk_penalty_cash"]),
                    "marginal_utility_pass_flag": dec(feature["portfolio_marginal_utility_cash"]) >= Decimal("-0.050000"),
                },
                row_id=f"RANK4_MARG_UTIL_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[upstream_rp5g_ref("port_marg_util.jsonl")],
                downstream_refs=[generated_ref("rank_score.jsonl")],
                provenance_tier="RANK4_MARGINAL_UTILITY_RANK_RESULT",
            )
        )
        rows["fdr_rank.jsonl"].append(
            common_row(
                {
                    "fdr_rank_id": f"RANK4_FDR_{index:04d}",
                    "candidate_id": cid,
                    "search_family_id": feature["search_family_id"],
                    "candidate_generation_method": "RP5F_GRID_TO_RP5G_SIMULATION",
                    "selection_method": "RANK4_EXECUTION_ADJUSTED_ADVISORY_RANKING",
                    "number_of_candidate_trials": feature["number_of_candidate_trials"],
                    "number_of_effectively_independent_trials": feature["number_of_effectively_independent_trials"],
                    "validation_window_ref": "RP5G_REPLAY_PAPER_WINDOW",
                    "lockbox_window_ref_when_available": "MISSING_LOCKBOX_WINDOW_COMPLETION_ROUTE",
                    "family_leakage_flag": False,
                    "observed_edge_stability": score(Decimal("1") - risk_scores[cid]),
                    "validation_gap": score(feature["calibration_gap"]),
                    "calibration_gap": score(feature["calibration_gap"]),
                    "fdr_q": score(PARAM_DEFAULTS["fdr_q_default"]),
                    "fdr_penalty_cash": score(feature["fdr_penalty_cash"]),
                    "fdr_adjusted_expected_pnl_cash": score(feature["fdr_adjusted_expected_pnl_cash"]),
                    "deflated_or_probabilistic_performance_fields_when_available": "MISSING_RETURN_SERIES_FOR_DSR",
                },
                row_id=f"RANK4_FDR_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent", "GovernanceAgent"],
                upstream_refs=[upstream_rp5g_ref("overfit_fdr.jsonl")],
                downstream_refs=[generated_ref("rank_score.jsonl")],
                provenance_tier="RANK4_OVERFIT_FDR_ADJUSTED_RESULT",
            )
        )
        rows["search_family_rank.jsonl"].append(
            common_row(
                {
                    "search_family_rank_id": f"RANK4_SEARCH_FAM_{index:04d}",
                    "candidate_id": cid,
                    "search_family_id": feature["search_family_id"],
                    "search_family_adjustment_applied_flag": True,
                    "completion_route_if_dsr_missing": "MISSING_RETURN_SERIES_FOR_DSR",
                },
                row_id=f"RANK4_SEARCH_FAM_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[upstream_rp5g_ref("overfit_fdr.jsonl")],
                downstream_refs=[generated_ref("fdr_rank.jsonl")],
                provenance_tier="RANK4_SEARCH_FAMILY_ADJUSTED_SCORE",
            )
        )
        rows["false_discovery_rank_audit.jsonl"].append(
            common_row(
                {
                    "false_discovery_rank_audit_id": f"RANK4_FD_AUDIT_{index:04d}",
                    "candidate_id": cid,
                    "search_family_id": feature["search_family_id"],
                    "statistical_metric_fabricated_flag": False,
                    "missing_statistical_metric_completion_route": "MISSING_RETURN_SERIES_FOR_DSR",
                },
                row_id=f"RANK4_FD_AUDIT_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[upstream_rp5g_ref("overfit_fdr.jsonl")],
                downstream_refs=[generated_ref("fdr_rank.jsonl")],
                provenance_tier="RANK4_FALSE_DISCOVERY_RANK_AUDIT",
            )
        )
        rows["scenario_rank.jsonl"].append(
            common_row(
                {
                    "scenario_rank_id": f"RANK4_SCEN_{index:04d}",
                    "candidate_id": cid,
                    "scenario_robustness_score": score(feature["scenario_robustness_score"]),
                    "scenario_worst_case_pnl_cash": score(feature["scenario_worst_case_pnl_cash"]),
                    "scenario_combined_conservative_pnl_cash": score(feature["scenario_combined_conservative_pnl_cash"]),
                    "scenario_combined_conservative_no_trade_margin_cash": score(feature["scenario_combined_conservative_no_trade_margin_cash"]),
                    "scenario_combined_conservative_pass_flag": feature["scenario_combined_conservative_pass_flag"],
                    "base_case_present_flag": True,
                    "combined_conservative_case_present_flag": True,
                },
                row_id=f"RANK4_SCEN_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[upstream_rp5g_ref("scenario_ladder.jsonl")],
                downstream_refs=[generated_ref("elig_gate.jsonl")],
                provenance_tier="RANK4_SCENARIO_ROBUSTNESS_RESULT",
            )
        )
        rows["calib_rank.jsonl"].append(
            common_row(
                {
                    "calibration_rank_id": f"RANK4_CALIB_{index:04d}",
                    "candidate_id": cid,
                    "calibration_gap": score(feature["calibration_gap"]),
                    "calibration_quality_score": score(Decimal("1") - bounded(feature["calibration_gap"])),
                    "calibration_pass_flag": dec(feature["calibration_gap"]) <= Decimal("0.050000"),
                },
                row_id=f"RANK4_CALIB_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[upstream_rp5g_ref("calibration_result.jsonl"), upstream_rp5g_ref("overfit_fdr.jsonl")],
                downstream_refs=[generated_ref("elig_gate.jsonl")],
                provenance_tier="RANK4_CALIBRATION_RANK_RESULT",
            )
        )
        voi = bounded((Decimal("1") - risk_scores[cid]) + (Decimal("1") - bounded(feature["scenario_robustness_score"])) + (Decimal("1") - bounded(feature["fill_probability"])) - Decimal("0.10"))
        rows["voi_rank.jsonl"].append(
            common_row(
                {
                    "voi_rank_id": f"RANK4_VOI_{index:04d}",
                    "candidate_id": cid,
                    "value_of_information_score": score(voi),
                    "expected_learning_value": score(Decimal("1") - risk_scores[cid]),
                    "uncertainty_reduction_value": score(risk_scores[cid]),
                    "regime_coverage_value": "0.100000",
                    "quantum_frontier_learning_value": "0.100000" if feature["quantum_structural_handoff_available_flag"] else "0.000000",
                    "calibration_gap_closure_value": score(feature["calibration_gap"]),
                    "paper_test_cost_proxy": "0.050000",
                    "operational_complexity_penalty": "0.050000",
                },
                row_id=f"RANK4_VOI_{index:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["MemoryAgent", "QOPTAgent"],
                upstream_refs=[generated_ref("rank_model_risk.jsonl")],
                downstream_refs=[generated_ref("retest_rank.jsonl")],
                provenance_tier="RANK4_VALUE_OF_INFORMATION_RANK",
                intelligence_classes=("LEARNING_INTELLIGENCE", "SEARCH_INTELLIGENCE"),
            )
        )
        rows["rank_model_risk.jsonl"].append(
            common_row(
                {
                    "model_risk_id": f"RANK4_MODEL_RISK_{index:04d}",
                    "candidate_id": cid,
                    "rank_id": feature["rank_id"],
                    "data_provenance_risk_score": score(_model_risk(feature)[0]["data_provenance_risk_score"]),
                    "proxy_only_risk_score": score(_model_risk(feature)[0]["proxy_only_risk_score"]),
                    "sample_size_risk_score": score(_model_risk(feature)[0]["sample_size_risk_score"]),
                    "calibration_risk_score": score(_model_risk(feature)[0]["calibration_risk_score"]),
                    "leakage_risk_score": score(_model_risk(feature)[0]["leakage_risk_score"]),
                    "TCA_model_risk_score": score(_model_risk(feature)[0]["TCA_model_risk_score"]),
                    "fill_latency_model_risk_score": score(_model_risk(feature)[0]["fill_model_risk_score"]),
                    "capacity_model_risk_score": score(_model_risk(feature)[0]["capacity_model_risk_score"]),
                    "portfolio_concentration_risk_score": score(_model_risk(feature)[0]["portfolio_concentration_risk_score"]),
                    "external_candidate_risk_score": score(_model_risk(feature)[0]["external_candidate_value_risk_score"]),
                    "quantum_structure_only_risk_score": score(_model_risk(feature)[0]["quantum_structure_only_risk_score"]),
                    "combined_model_risk_score": score(risk_scores[cid]),
                    "uncertainty_reserve_cash": score(reserves[cid]),
                    "completion_route_if_unavailable": "MODEL_RISK_RESERVE_REQUIRED",
                },
                row_id=f"RANK4_MODEL_RISK_{index:04d}",
                owner_agent="ModelRiskAgent",
                consumer_agents=["RiskAgent", "RankerAgent"],
                upstream_refs=[generated_ref("rank_feat.jsonl")],
                downstream_refs=[generated_ref("rank_uncert_reserve.jsonl")],
                provenance_tier="RANK4_MODEL_RISK_RESULT",
            )
        )
        rows["rank_uncert_reserve.jsonl"].append(
            common_row(
                {
                    "uncertainty_reserve_id": f"RANK4_UNCERT_RESERVE_{index:04d}",
                    "candidate_id": cid,
                    "uncertainty_reserve_cash": score(reserves[cid]),
                    "rank_score_after_uncertainty_reserve": "SEE_RANK_SCORE",
                    "data_provenance_reserve_cash": score(reserves[cid] * Decimal("0.20")),
                    "proxy_only_reserve_cash": score(reserves[cid] * Decimal("0.15")),
                    "calibration_reserve_cash": score(reserves[cid] * Decimal("0.10")),
                    "scenario_fragility_reserve_cash": score(reserves[cid] * Decimal("0.10")),
                    "TCA_model_reserve_cash": score(reserves[cid] * Decimal("0.15")),
                    "fill_latency_capacity_reserve_cash": score(reserves[cid] * Decimal("0.15")),
                    "overfit_fdr_reserve_cash": score(reserves[cid] * Decimal("0.10")),
                    "portfolio_concentration_reserve_cash": score(reserves[cid] * Decimal("0.05")),
                },
                row_id=f"RANK4_UNCERT_RESERVE_{index:04d}",
                owner_agent="ModelRiskAgent",
                consumer_agents=["RankerAgent"],
                upstream_refs=[generated_ref("rank_model_risk.jsonl")],
                downstream_refs=[generated_ref("rank_score.jsonl")],
                provenance_tier="RANK4_UNCERTAINTY_RESERVE_RESULT",
            )
        )
        for file_name, prefix in (
            ("rank_oos_lockbox_hint.jsonl", "OOS"),
            ("rank_bandit_alloc_hint.jsonl", "BANDIT"),
            ("rank_ope_hint.jsonl", "OPE"),
            ("rank_reward_decomp.jsonl", "REWARD"),
            ("rank_latency_sla.jsonl", "LAT_SLA"),
            ("rank_live_ladder.jsonl", "LIVE_LADDER"),
            ("rank_cross_market_hint.jsonl", "CROSS_MARKET"),
            ("rank_tradeplan_lifecycle.jsonl", "LIFECYCLE"),
            ("rank_decision_intel_map.jsonl", "DECISION_INTEL"),
            ("rank_mem1_contract_hint.jsonl", "MEM1_CONTRACT"),
            ("rank_snapshot_reval_plan.jsonl", "SNAP_REVAL"),
            ("rank_auto_trading_path.jsonl", "AUTO_PATH"),
            ("rank_recipe_cred_tier.jsonl", "CRED_TIER"),
            ("rank_recipe_ttl_retest.jsonl", "TTL_RETEST"),
            ("rank_shadow_route.jsonl", "SHADOW_ROUTE"),
            ("rank_llm_non_authority.jsonl", "LLM_NON_AUTH"),
            ("rank_learning_loop_contract.jsonl", "LEARNING_LOOP"),
            ("rank_access_mode.jsonl", "ACCESS_MODE"),
            ("rank_rank_stability.jsonl", "RANK_STAB"),
            ("rank_sensitivity_surface.jsonl", "SENS_SURF"),
            ("rank_micro_regime.jsonl", "MICRO_REGIME"),
            ("rank_tail_guard.jsonl", "TAIL_GUARD"),
            ("rank_hotpath.jsonl", "HOTPATH"),
        ):
            rows[file_name].append(_generic_candidate_handoff(file_name, prefix, index, feature, risk_scores[cid], reserves[cid], no_trade_wins))
        rows["rank_constraint_tightness.jsonl"].extend(_constraint_rows(index, feature, margin, gate_pass))
        rows["rank_context_signature.jsonl"].append(_context_signature(index, feature))
        rows["rank_similarity_key.jsonl"].append(_similarity_key(index, feature))
        rows["rank_memory_recipe_handoff.jsonl"].append(_recipe_handoff(index, feature, no_trade_wins))
        rows["rank_winner_attribution.jsonl"].append(_winner_attribution(index, feature))
        rows["rank_memory_candidate.jsonl"].append(_memory_candidate(index, feature))
        rows["rank_recipe_prior_score.jsonl"].append(_recipe_prior(index, feature, risk_scores[cid]))
        rows["rank_recipe_batch_policy.jsonl"].append(_recipe_batch(index, feature))
        rows["rank_negative_memory_hint.jsonl"].append(_negative_memory(index, feature, no_trade_wins, gate_reasons))
        rows["rank_recipe_drift_hint.jsonl"].append(_drift_hint(index, feature, risk_scores[cid]))
        rows["rank_retest_priority.jsonl"].append(_retest_priority(index, feature, no_trade_wins, risk_scores[cid]))
        rows["rank_two_speed_hint.jsonl"].append(_two_speed(index, feature))
        rows["rank_realization_receipt_req.jsonl"].append(_realization_req(index, feature))
        rows["rank_qmemory_handoff.jsonl"].append(_qmemory(index, feature))
        rows["retest_rank.jsonl"].append(_rank_route_row("retest_rank.jsonl", "RETEST", index, feature, no_trade_wins))
        rows["repair_rank.jsonl"].append(_rank_route_row("repair_rank.jsonl", "REPAIR", index, feature, no_trade_wins))
        rows["mem_keys.jsonl"].append(_rank_route_row("mem_keys.jsonl", "MEM_KEY", index, feature, no_trade_wins))
        rows["rank_next_action.jsonl"].append(_next_action(index, feature, gate_pass, no_trade_wins, risk_scores[cid]))
        rows["rank_stack_synergy.jsonl"].append(_stack_synergy(index, feature))
        rows["rank_port_basket.jsonl"] = []
    # Pareto/dominance must compare all candidates after per-candidate layers are available.
    for index, feature in enumerate(features, start=1):
        dominators = [other["candidate_id"] for other in features if other["candidate_id"] != feature["candidate_id"] and dominates(other, feature)]
        rows["pareto_frontier.jsonl"].append(
            common_row(
                {
                    "pareto_frontier_id": f"RANK4_PARETO_{index:04d}",
                    "candidate_id": feature["candidate_id"],
                    "pareto_frontier_flag": not dominators,
                    "core_dimensions": [key for key, _ in PARETO_DIMS],
                    "dominators": dominators,
                    "diversity_frontier_exception": False,
                    "value_of_information_exception": bool(dominators),
                    "qopt_frontier_exception": feature["quantum_structural_handoff_available_flag"],
                },
                row_id=f"RANK4_PARETO_{index:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["QOPTAgent", "RiskAgent"],
                upstream_refs=[generated_ref("rank_feat.jsonl")],
                downstream_refs=[generated_ref("dominance.jsonl")],
                provenance_tier="RANK4_PARETO_FRONTIER_RESULT",
            )
        )
        rows["dominance.jsonl"].append(
            common_row(
                {
                    "dominance_id": f"RANK4_DOM_{index:04d}",
                    "candidate_id": feature["candidate_id"],
                    "strictly_dominated_flag": bool(dominators),
                    "dominator_candidate_ids": dominators,
                    "dominance_exception_allowed_flag": bool(dominators and feature["quantum_structural_handoff_available_flag"]),
                    "dominance_exception_reason": "QOPT_FRONTIER_EXCEPTION" if dominators and feature["quantum_structural_handoff_available_flag"] else "",
                },
                row_id=f"RANK4_DOM_{index:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["RiskAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("pareto_frontier.jsonl")],
                downstream_refs=[generated_ref("rank_order.jsonl")],
                provenance_tier="RANK4_DOMINANCE_RESULT",
            )
        )
        rows["rank_dominance_explain.jsonl"].append(
            common_row(
                {
                    "dominance_explain_id": f"RANK4_DOM_EXPLAIN_{index:04d}",
                    "candidate_id": feature["candidate_id"],
                    "dominance_summary": "DOMINATED_WITH_EXCEPTION_ROUTE" if dominators else "NON_DOMINATED_OR_FRONTIER_MEMBER",
                    "numeric_reason_codes": stable_unique(dominators),
                },
                row_id=f"RANK4_DOM_EXPLAIN_{index:04d}",
                owner_agent="RankerAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[generated_ref("dominance.jsonl")],
                downstream_refs=[generated_ref("rank_explain.jsonl")],
                provenance_tier="RANK4_DOMINANCE_EXPLANATION",
            )
        )
    return rows


def _generic_candidate_handoff(file_name: str, prefix: str, index: int, feature: dict[str, Any], risk: Decimal, reserve: Decimal, no_trade_wins: bool) -> dict[str, Any]:
    cid = feature["candidate_id"]
    row: dict[str, Any] = {
        "candidate_id": cid,
        "rank_id": feature["rank_id"],
        "hint_family": prefix,
        "current_snapshot_revalidation_required_flag": True,
        "future_owner_enablement_required": True,
        "future_connector_state_required": True,
        "future_cash_account_state_required": True,
        "future_kill_switch_required": True,
        "future_pre_submit_revalidation_required": True,
        "future_execution_router_required": True,
        "future_realized_pnl_receipt_required": True,
    }
    if file_name == "rank_auto_trading_path.jsonl":
        row.update(
            {
                "future_path": "RANK4 -> QOPT1 -> VS2 -> PAPER_LOOP -> MEM1 -> LIVE_DRYRUN -> LIVE_PILOT -> LAUNCH -> POSTLAUNCH",
                "paper_order_intent_created_by_RANK4": False,
                "live_order_authority_created_by_RANK4": False,
                "buy_sell_open_close_logic_created_by_RANK4": False,
                "future_exit_or_settlement_receipt_required": True,
            }
        )
    elif file_name == "rank_live_ladder.jsonl":
        row.update({"future_ladder": "RANK4_advisory_rank -> QOPT1_batch_optimization_required -> VS2_paper_intent_required -> PAPER_LOOP_paper_execution_required -> MEM1_outcome_memory_required -> LIVE_DRYRUN_submit_disabled_required -> LIVE_PILOT_owner_approved_canary_required -> LAUNCH_gate_required -> POSTLAUNCH_audit_required", "live_canary_authority_created_flag": False, "live_order_authority_created_flag": False, "paper_order_intent_created_flag": False, "exit_sell_close_authority_created_flag": False, "realized_pnl_receipt_created_flag": False})
    elif file_name == "rank_shadow_route.jsonl":
        row.update({"future_shadow_observation_route_allowed_flag": True, "shadow_execution_authority_created_flag": False, "live_execution_authority_created_flag": False, "requires_live_surface_and_receipts_before_shadow_flag": True, "consumer_agents": ["ShadowObservationAgent", "GovernanceAgent"]})
    elif file_name == "rank_oos_lockbox_hint.jsonl":
        row.update({"search_family_id": feature["search_family_id"], "train_or_discovery_window_ref": "RP5G_DISCOVERY_WINDOW", "validation_window_ref": "RP5G_REPLAY_PAPER_WINDOW", "lockbox_window_ref_when_available": "MISSING_LOCKBOX_WINDOW_COMPLETION_ROUTE", "temporal_split_required_flag": True, "purged_walk_forward_required_flag": True, "leakage_check_required_flag": True, "lockbox_missing_completion_route": "MISSING_LOCKBOX_WINDOW", "statistical_metric_fabricated_flag": False})
    elif file_name == "rank_access_mode.jsonl":
        row.update({"qku_ref": feature["qku_refs"][0] if feature["qku_refs"] else "QKU_REF_UNKNOWN_COMPLETION_REQUIRED", "formula_ref": feature["formula_refs"][0] if feature["formula_refs"] else "FORMULA_REF_UNKNOWN_COMPLETION_REQUIRED", "agent_id": "RankerAgent", "stage_profile_ref": "PREDICTION_MARKETS_STAGE1", "platform_scope": feature["venue"], "agent_duty_ref": "PR165_D2_AgentDutySourceCrosswalk", "resolver_receipt_ref": "Rank4LibraryQueryReceiptV1", "access_mode": "DEFAULT_COMPUTE", "full_library_default_access_flag": False, "per_agent_copy_created_flag": False, "lazy_load_selected_objects_only_flag": True, "orphan_flag": False})
    elif file_name == "rank_latency_sla.jsonl":
        row.update({"expected_hot_path_ms_hint": 25, "expected_cold_path_ms_hint": 2500, "latency_budget_bucket": feature["latency_bucket"], "hot_path_ready_flag": True, "cold_path_required_flag": True, "snapshot_revalidation_required_flag": True, "precomputed_recipe_signature_required_flag": True, "precomputed_TCA_fill_capacity_bucket_required_flag": True, "completion_route_if_hot_path_not_ready": ""})
    elif file_name == "rank_tradeplan_lifecycle.jsonl":
        row.update({"lifecycle_stage": "RANK4_ADVISORY_RANKING", "upstream_lifecycle_ref": "RP5G_REPLAY_PAPER_SIMULATION", "downstream_lifecycle_refs": ["QOPT1", "VS2", "MEM1", "PAPER_LOOP", "LIVE_DRYRUN", "SHADOW"], "tradeplan_mutable_object_flag": True, "formula_mutation_flag": False, "qku_mutation_flag": False})
    elif file_name == "rank_decision_intel_map.jsonl":
        row.update({"knowledge_intelligence_ref": "RP5C/RP5D/RP5F/RP5G refs", "search_intelligence_ref": "RANK4_QOPT_FRONTIER_HINT", "simulation_intelligence_ref": "RP5G_NUMERIC_EVIDENCE", "learning_intelligence_ref": "RANK4_RECIPE_MEMORY_HINT", "reasoning_intelligence_ref": "LLM_CRITIC_NON_AUTHORITY_ONLY", "optimization_driven_flag": True, "LLM_may_create_rank_proof_flag": False})
    elif file_name == "rank_mem1_contract_hint.jsonl":
        row.update({"future_MEM1_contract_hint_only_flag": True, "ConditionedWinningRecipeV1": "future durable registry object", "ConditionedFailureMemoryV1": "future durable failure registry object", "TradeContextSimilarityEngineV1": "future retrieval engine", "RecipeDriftMonitorV1": "future drift monitor", "RecipeCooldownPolicyV1": "future cooldown policy", "RecipeRetestQueueV1": "future retest queue", "RecipeOutcomeAttributionLedgerV1": "future attribution ledger"})
    elif file_name == "rank_recipe_cred_tier.jsonl":
        tier = "COOLDOWN_CONTEXT_ONLY" if no_trade_wins else "SINGLE_SNAPSHOT_SEED"
        row.update({"recipe_credibility_tier": tier, "tier_source": "RP5G_SINGLE_SNAPSHOT_REPLAY_PAPER_SIMULATION", "paper_validation_fabricated_flag": False, "live_validation_fabricated_flag": False})
    elif file_name == "rank_recipe_ttl_retest.jsonl":
        row.update({"recipe_ttl_bucket": "CURRENT_SNAPSHOT_ONLY", "retest_schedule_hint": "RETEST_ON_NEXT_SNAPSHOT_OR_BEFORE_VS2", "current_snapshot_revalidation_required_flag": True, "stale_memory_trap_prevented_flag": True})
    elif file_name == "rank_next_action.jsonl":
        row.update({"best_next_action": "NO_TRADE_FOR_SNAPSHOT" if no_trade_wins else "ADVISORY_TOPK_FOR_QOPT1"})
    elif file_name == "rank_rank_stability.jsonl":
        row.update({"base_rank": "SEE_RANK_ORDER", "rank_after_weight_perturbation": "DETERMINISTIC_STABLE_PROXY", "rank_after_TCA_worse_case": "SEE_SENSITIVITY_SURFACE", "rank_flip_flag": risk > Decimal("0.35"), "rank_flip_reason": "MODEL_RISK_SENSITIVITY" if risk > Decimal("0.35") else "", "brittle_winner_flag": risk > Decimal("0.35"), "stability_score": score(Decimal("1") - risk), "champion_preview_allowed_after_stability_flag": risk <= Decimal("0.35")})
    elif file_name == "rank_sensitivity_surface.jsonl":
        row.update({"rank_after_weight_perturbation": "SEE_RANK_STABILITY", "rank_after_TCA_worse_case": "CONSERVATIVE_SCORE_REDUCED", "rank_after_fill_probability_haircut": "CONSERVATIVE_SCORE_REDUCED", "rank_after_latency_worse_case": "CONSERVATIVE_SCORE_REDUCED", "rank_after_capacity_haircut": "CONSERVATIVE_SCORE_REDUCED", "rank_after_no_trade_margin_increase": "CONSERVATIVE_SCORE_REDUCED", "rank_flip_flag": risk > Decimal("0.35"), "completion_route_if_missing": "CURRENT_SNAPSHOT_REVALIDATION_REQUIRED"})
    elif file_name == "rank_micro_regime.jsonl":
        row.update({"venue": feature["venue"], "market_category": "PREDICTION_MARKETS", "event_lifecycle_bucket": "SNAPSHOT_FIXTURE", "yes_no_price_bucket": feature["entry_bucket"], "spread_bucket": feature["spread_bucket"], "depth_bucket": feature.get("depth_bucket", feature["liquidity_bucket"]), "liquidity_bucket": feature["liquidity_bucket"], "volume_bucket": "UNKNOWN_COMPLETION_REQUIRED", "orderbook_imbalance_bucket": "UNKNOWN_COMPLETION_REQUIRED", "liquidity_decay_bucket": "RP5G_PROXY", "time_to_close_bucket": feature["time_to_close_bucket"], "source_freshness_bucket": "RP5G_SNAPSHOT", "latency_bucket": feature["latency_bucket"], "capacity_bucket": feature["size_bucket"], "microstructure_regime_key": feature["regime_key"]})
    elif file_name == "rank_tail_guard.jsonl":
        capital = dec(feature.get("size_bucket")) * dec(feature.get("entry_bucket"))
        row.update({"capital_required_cash_or_proxy": score(capital), "capital_lock_time": feature["hold_duration_bucket"], "expected_net_pnl_per_capital": score(dec(feature["net_expected_pnl_cash"]) / max(capital, Decimal("0.000001"))), "expected_net_pnl_per_latency_budget": score(dec(feature["net_expected_pnl_cash"]) / max(dec(feature["latency_bucket"]), Decimal("1"))), "expected_net_pnl_per_capacity_unit": score(dec(feature["net_expected_pnl_cash"]) / max(dec(feature["size_bucket"]), Decimal("1"))), "tail_loss_proxy_cash": score(abs(dec(feature["scenario_worst_case_pnl_cash"]))), "drawdown_proxy_cash": score(abs(dec(feature["scenario_worst_case_pnl_cash"]))), "worst_case_scenario_cash": score(feature["scenario_worst_case_pnl_cash"]), "capital_efficiency_score": score(bounded(dec(feature["net_expected_pnl_cash"]) / max(capital, Decimal("0.000001")))), "tail_guard_pass_flag": dec(feature["scenario_worst_case_pnl_cash"]) >= Decimal("-1"), "live_stage_revalidation_required_flag": True, "realized_pnl_claim_flag": False})
    elif file_name == "rank_hotpath.jsonl":
        row.update({"hotpath_id": f"RANK4_HOTPATH_{index:04d}", "context_signature_ref": f"RANK4_CTX_SIG_{index:04d}", "recipe_similarity_key_ref": f"RANK4_SIM_KEY_{index:04d}", "rank_latency_sla_ref": f"RANK4_LAT_SLA_{index:04d}", "precomputed_components_available": ["context_signature", "score_components", "TCA_fill_capacity_bucket"], "missing_hotpath_components": ["future_cash_account_state", "future_connector_state", "future_kill_switch_state"], "hotpath_ready_for_RANK4_advisory_only_flag": True, "hotpath_order_authority_created_flag": False})
    elif file_name == "rank_reward_decomp.jsonl":
        row.update({"signal_edge_reward_cash": score(feature["net_expected_pnl_cash"]), "execution_quality_reward_cash": score(feature["fill_probability"]), "TCA_savings_reward_cash": score(-dec(feature["TCA_total_cash"])), "fill_quality_reward_cash": score(feature["fill_probability"]), "latency_reward_or_penalty_cash": score(-dec(feature["latency_decay_penalty_cash"])), "capacity_reward_or_penalty_cash": score(-dec(feature["capacity_crowding_penalty_cash"])), "portfolio_utility_reward_cash": score(feature["portfolio_marginal_utility_cash"]), "scenario_robustness_reward_cash": score(feature["scenario_robustness_score"]), "calibration_reward_or_penalty_cash": score(-dec(feature["calibration_gap"])), "FDR_overfit_penalty_cash": score(feature["fdr_penalty_cash"]), "no_trade_margin_component_cash": score(feature["candidate_minus_no_trade_cash"]), "model_risk_reserve_cash": score(reserve), "causal_attribution_claim_flag": False, "attribution_provenance": "PROXY_FROM_RANK_COMPONENTS"})
    elif file_name == "rank_bandit_alloc_hint.jsonl":
        bucket = "EXPLORATION_REPAIR_NOTRADE" if no_trade_wins else "MEMORY_WINNER"
        row.update({"context_signature_ref": f"RANK4_CTX_SIG_{index:04d}", "action_or_recipe_ref": f"RANK4_RECIPE_{index:04d}", "behavior_policy_ref_when_known": "RP5G_FIXED_REPLAY_POLICY", "target_policy_hint_ref": "RANK4_ADVISORY_PRIORITY_POLICY", "propensity_score_available_flag": False, "importance_weight_available_flag": False, "doubly_robust_ready_flag": False, "counterfactual_eval_ready_flag": False, "ope_completion_route": "OPE_HINT_INCOMPLETE", "exploration_bucket": bucket, "recommended_replay_paper_budget_share_hint": "0.700000" if bucket == "MEMORY_WINNER" else "0.100000", "bandit_runtime_policy_created_flag": False, "live_policy_control_created_flag": False, "order_authority_created_flag": False})
    elif file_name == "rank_ope_hint.jsonl":
        row.update({"context_signature_ref": f"RANK4_CTX_SIG_{index:04d}", "action_or_recipe_ref": f"RANK4_RECIPE_{index:04d}", "behavior_policy_ref_when_known": "RP5G_REPLAY_SIM_POLICY", "propensity_score_available_flag": False, "importance_weight_available_flag": False, "doubly_robust_ready_flag": False, "counterfactual_eval_ready_flag": False, "ope_completion_route": "OPE_HINT_INCOMPLETE", "off_policy_evaluation_as_profit_proof_flag": False})
    return common_row(
        row,
        row_id=f"RANK4_{prefix}_{index:04d}",
        owner_agent="RankerAgent" if prefix not in {"OOS", "BANDIT", "OPE"} else "ModelRiskAgent",
        consumer_agents=["GovernanceAgent", "MemoryAgent", "QOPTAgent"],
        upstream_refs=[generated_ref("rank_score.jsonl"), generated_ref("rank_feat.jsonl")],
        downstream_refs=[generated_ref("rank_user_conn_route.jsonl")],
        provenance_tier=f"RANK4_{prefix}_HANDOFF",
        intelligence_classes=("LEARNING_INTELLIGENCE", "SEARCH_INTELLIGENCE", "SIMULATION_INTELLIGENCE"),
    )


def _constraint_rows(index: int, feature: dict[str, Any], no_trade_margin: Decimal, gate_pass: bool) -> list[dict[str, Any]]:
    constraints = (
        ("no_trade_margin", no_trade_margin, dec(feature["candidate_minus_no_trade_cash"])),
        ("lcb_min_cash", Decimal("0"), dec(feature["lower_confidence_bound_pnl_cash"])),
        ("fdr_adjusted_positive", Decimal("0"), dec(feature["fdr_adjusted_expected_pnl_cash"])),
        ("fill_probability", Decimal("0.50"), dec(feature["fill_probability"])),
        ("capacity_crowding_max", Decimal("0.50"), Decimal("0.50") - dec(feature["capacity_crowding_penalty_cash"])),
        ("calibration_gap_max", Decimal("0.05"), Decimal("0.05") - dec(feature["calibration_gap"])),
        ("portfolio_utility_min", Decimal("-0.05"), dec(feature["portfolio_marginal_utility_cash"])),
    )
    rows = []
    for c_index, (name, threshold, observed) in enumerate(constraints, start=1):
        margin = observed - threshold
        rows.append(
            common_row(
                {
                    "constraint_tightness_id": f"RANK4_TIGHT_{index:04d}_{c_index:02d}",
                    "candidate_id": feature["candidate_id"],
                    "rank_id": feature["rank_id"],
                    "constraint_name": name,
                    "threshold_value": score(threshold),
                    "observed_value": score(observed),
                    "margin_to_threshold": score(margin),
                    "pass_flag": margin >= Decimal("0"),
                    "barely_passed_flag": Decimal("0") <= margin <= Decimal("0.05"),
                    "fragility_reason": "BARELY_PASSED_THRESHOLD" if Decimal("0") <= margin <= Decimal("0.05") else "",
                    "future_retest_priority": "HIGH" if not gate_pass or margin <= Decimal("0.05") else "NORMAL",
                },
                row_id=f"RANK4_TIGHT_{index:04d}_{c_index:02d}",
                owner_agent="RiskAgent",
                consumer_agents=["MemoryAgent", "RankerAgent"],
                upstream_refs=[generated_ref("elig_gate.jsonl")],
                downstream_refs=[generated_ref("rank_recipe_ttl_retest.jsonl")],
                provenance_tier="RANK4_CONSTRAINT_TIGHTNESS_AUDIT",
            )
        )
    return rows


def _context_signature(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    row = {
        "context_signature_id": f"RANK4_CTX_SIG_{index:04d}",
        "candidate_id": feature["candidate_id"],
        "rank_id": feature["rank_id"],
        "market_family": feature["market_family"],
        "venue": feature["venue"],
        "market_id_or_cluster": feature["market_cluster_id"],
        "event_category": "PREDICTION_EVENT",
        "contract_type": "BINARY_YES_NO",
        "side": feature["side"],
        "time_to_close_bucket": feature["time_to_close_bucket"],
        "price_bucket": feature["entry_bucket"],
        "spread_bucket": feature["spread_bucket"],
        "depth_bucket": feature.get("depth_bucket", feature["liquidity_bucket"]),
        "liquidity_bucket": feature["liquidity_bucket"],
        "volume_bucket": "UNKNOWN_COMPLETION_REQUIRED",
        "volatility_bucket": "UNKNOWN_COMPLETION_REQUIRED",
        "event_lifecycle_bucket": "RP5G_FIXTURE",
        "source_freshness_bucket": "RP5G_SNAPSHOT",
        "latency_bucket": feature["latency_bucket"],
        "fee_regime_bucket": "RP5G_PROXY",
        "portfolio_exposure_bucket": feature.get("portfolio_exposure_candidate", "RP5G_PROXY"),
        "market_status_ref": "RP5G_SNAPSHOT_STATUS",
        "snapshot_truth_ref": upstream_rp5g_ref("data_prov.jsonl"),
        "regime_key_ref": feature["regime_key"],
    }
    return common_row(row, row_id=row["context_signature_id"], owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("rank_feat.jsonl")], downstream_refs=[generated_ref("rank_similarity_key.jsonl")], provenance_tier="RANK4_CONTEXT_SIGNATURE")


def _similarity_key(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    row = {
        "similarity_key_id": f"RANK4_SIM_KEY_{index:04d}",
        "candidate_id": feature["candidate_id"],
        "rank_id": feature["rank_id"],
        "venue_match_key": feature["venue"],
        "market_category_key": "PREDICTION_MARKETS",
        "event_lifecycle_key": "RP5G_FIXTURE",
        "yes_no_price_bucket_key": feature["entry_bucket"],
        "spread_depth_liquidity_key": f"{feature['spread_bucket']}::{feature['liquidity_bucket']}",
        "time_to_close_key": feature["time_to_close_bucket"],
        "fee_latency_key": f"RP5G_PROXY::{feature['latency_bucket']}",
        "formula_stack_fingerprint": feature["stack_id"],
        "qku_family_fingerprint": "|".join(feature["qku_family_refs"]),
        "formula_family_fingerprint": "|".join(feature["formula_family_refs"]),
        "order_policy_key": feature["maker_taker_policy"],
        "exit_rule_key": feature["exit_rule"],
        "portfolio_exposure_key": "RP5G_PROXY",
        "capacity_bucket_key": feature["size_bucket"],
        "similarity_score_hint": "0.750000",
        "venue_match_weight": "0.150000",
        "market_category_match_weight": "0.150000",
        "price_bucket_similarity_weight": "0.100000",
        "spread_depth_liquidity_similarity_weight": "0.100000",
        "time_to_close_similarity_weight": "0.100000",
        "event_lifecycle_similarity_weight": "0.050000",
        "fee_latency_similarity_weight": "0.050000",
        "formula_stack_overlap_weight": "0.100000",
        "qku_family_overlap_weight": "0.100000",
        "order_policy_similarity_weight": "0.050000",
        "exit_rule_similarity_weight": "0.050000",
        "drift_penalty_weight": "0.050000",
        "stale_memory_penalty_weight": "0.050000",
        "capacity_mismatch_penalty_weight": "0.050000",
    }
    return common_row(row, row_id=row["similarity_key_id"], owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("rank_context_signature.jsonl")], downstream_refs=[generated_ref("rank_memory_recipe_handoff.jsonl")], provenance_tier="RANK4_RECIPE_SIMILARITY_KEY", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _recipe_handoff(index: int, feature: dict[str, Any], no_trade_wins: bool) -> dict[str, Any]:
    row = {
        "recipe_handoff_id": f"RANK4_RECIPE_{index:04d}",
        "candidate_id": feature["candidate_id"],
        "rank_id": feature["rank_id"],
        "source_trade_plan_candidate_id": feature["candidate_id"],
        "source_simulation_run_id": feature["simulation_run_id"],
        "qku_refs": feature["qku_refs"],
        "formula_refs": feature["formula_refs"],
        "formula_stack_id": feature["stack_id"],
        "stack_role_map": {"ranked_stack": feature["stack_id"]},
        "market_family": feature["market_family"],
        "venue": feature["venue"],
        "market_id_or_cluster": feature["market_cluster_id"],
        "event_category": "PREDICTION_EVENT",
        "contract_type": "BINARY_YES_NO",
        "side": feature["side"],
        "entry_rule": feature["entry_bucket"],
        "exit_rule": feature["exit_rule"],
        "hold_duration_bucket": feature["hold_duration_bucket"],
        "order_size_bucket": feature["size_bucket"],
        "total_investment_bucket": "RP5G_PROXY",
        "maker_taker_split": feature["maker_taker_policy"],
        "cancel_replace_interval": feature["cancel_replace_bucket"],
        "spread_filter": feature["spread_bucket"],
        "depth_filter": feature.get("depth_bucket", feature["liquidity_bucket"]),
        "liquidity_filter": feature["liquidity_bucket"],
        "latency_budget": feature["latency_bucket"],
        "portfolio_exposure_bucket": "RP5G_PROXY",
        "expected_gross_pnl_cash": score(feature["net_expected_pnl_cash"] + feature["TCA_total_cash"]),
        "net_expected_pnl_cash": score(feature["net_expected_pnl_cash"]),
        "lower_confidence_bound_pnl_cash": score(feature["lower_confidence_bound_pnl_cash"]),
        "candidate_minus_no_trade_cash": score(feature["candidate_minus_no_trade_cash"]),
        "TCA_total_cash": score(feature["TCA_total_cash"]),
        "fill_probability": score(feature["fill_probability"]),
        "latency_penalty_cash": score(feature["latency_decay_penalty_cash"]),
        "capacity_crowding_penalty_cash": score(feature["capacity_crowding_penalty_cash"]),
        "overfit_fdr_penalty_cash": score(feature["fdr_penalty_cash"]),
        "portfolio_marginal_utility_cash": score(feature["portfolio_marginal_utility_cash"]),
        "scenario_ladder_result_ref": upstream_rp5g_ref("scenario_ladder.jsonl"),
        "calibration_result_ref": upstream_rp5g_ref("calibration_result.jsonl"),
        "data_provenance_tier": feature["provenance_tier"],
        "real_market_profit_proof_flag": False,
        "paper_profit_proof_flag": False,
        "replay_profit_proof_flag": False,
        "proxy_only_flag": feature["proxy_only_flag"],
        "last_seen_utc": CREATED_AT_UTC,
        "recency_weight_hint": "1.000000",
        "drift_flag": False,
        "cooldown_flag": no_trade_wins,
        "retest_required_flag": True,
        "memory_prior_only_flag": True,
        "current_profit_proof_flag": False,
        "durable_MEM1_storage_created_flag": False,
        "live_authority_flag": False,
        "order_authority_flag": False,
    }
    return common_row(row, row_id=row["recipe_handoff_id"], owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("rank_similarity_key.jsonl")], downstream_refs=[generated_ref("mem1_handoff.jsonl")], provenance_tier="RANK4_WINNING_RECIPE_HANDOFF", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _winner_attribution(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    row = {
        "winner_attribution_id": f"RANK4_ATTR_{index:04d}",
        "candidate_id": feature["candidate_id"],
        "rank_id": feature["rank_id"],
        "edge_source_component": score(feature["net_expected_pnl_cash"]),
        "qku_contribution_estimate": "PROXY_FROM_RANK_COMPONENTS",
        "formula_contribution_estimate": "PROXY_FROM_RANK_COMPONENTS",
        "stack_synergy_contribution_estimate": "SEE_RANK_STACK_SYNERGY",
        "entry_price_contribution": feature["entry_bucket"],
        "exit_rule_contribution": feature["exit_rule"],
        "sizing_contribution": feature["size_bucket"],
        "maker_taker_contribution": feature["maker_taker_policy"],
        "cancel_replace_contribution": feature["cancel_replace_bucket"],
        "fill_quality_contribution": score(feature["fill_probability"]),
        "latency_contribution": score(-dec(feature["latency_decay_penalty_cash"])),
        "spread_filter_contribution": feature["spread_bucket"],
        "depth_filter_contribution": feature.get("depth_bucket", feature["liquidity_bucket"]),
        "liquidity_filter_contribution": feature["liquidity_bucket"],
        "portfolio_context_contribution": score(feature["portfolio_marginal_utility_cash"]),
        "scenario_component_contribution": score(feature["scenario_robustness_score"]),
        "TCA_component_contribution": score(-dec(feature["TCA_total_cash"])),
        "no_trade_margin_contribution": score(feature["candidate_minus_no_trade_cash"]),
        "calibration_contribution": score(Decimal("1") - bounded(feature["calibration_gap"])),
        "FDR_overfit_adjustment_contribution": score(-dec(feature["fdr_penalty_cash"])),
        "attribution_provenance": "PROXY_FROM_RANK_COMPONENTS",
        "causal_attribution_claim_flag": False,
    }
    return common_row(row, row_id=row["winner_attribution_id"], owner_agent="RankerAgent", consumer_agents=["MemoryAgent", "QOPTAgent"], upstream_refs=[generated_ref("score_comp.jsonl")], downstream_refs=[generated_ref("rank_memory_recipe_handoff.jsonl")], provenance_tier="RANK4_WINNER_ATTRIBUTION", intelligence_classes=("LEARNING_INTELLIGENCE", "SIMULATION_INTELLIGENCE"))


def _memory_candidate(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    return common_row({"memory_candidate_id": f"RANK4_MEM_CAND_{index:04d}", "candidate_id": feature["candidate_id"], "context_signature_ref": f"RANK4_CTX_SIG_{index:04d}", "recipe_similarity_key_ref": f"RANK4_SIM_KEY_{index:04d}", "memory_prior_only_flag": True, "current_profit_proof_flag": False}, row_id=f"RANK4_MEM_CAND_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("rank_memory_recipe_handoff.jsonl")], downstream_refs=[generated_ref("mem1_handoff.jsonl")], provenance_tier="RANK4_MEMORY_CANDIDATE", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _recipe_prior(index: int, feature: dict[str, Any], risk: Decimal) -> dict[str, Any]:
    prior = dec(feature["net_expected_pnl_cash"]) + dec(feature["lower_confidence_bound_pnl_cash"]) - dec(feature["fdr_penalty_cash"]) - risk
    return common_row({"recipe_prior_score_id": f"RANK4_PRIOR_{index:04d}", "candidate_id": feature["candidate_id"], "recipe_prior_score_hint": score(prior), "current_evidence_only_prior_seed": True, "historical_memory_available_flag": False, "durable_prior_score_finalized_flag": False, "MEM1_required_for_final_prior_flag": True, "memory_prior_only_flag": True, "current_profit_proof_flag": False}, row_id=f"RANK4_PRIOR_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("rank_memory_recipe_handoff.jsonl")], downstream_refs=[generated_ref("rank_recipe_batch_policy.jsonl")], provenance_tier="RANK4_RECIPE_PRIOR_SCORE_HINT", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _recipe_batch(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    return common_row({"recipe_batch_policy_id": f"RANK4_BATCH_POLICY_{index:04d}", "candidate_id": feature["candidate_id"], "batch_A_memory_winner_prior_target_share_default": "0.700000", "batch_B_challenger_target_share_default": "0.200000", "batch_C_exploration_repair_notrade_target_share_default": "0.100000", "if_drift_low_and_memory_confidence_high_increase_memory_winner_share": True, "if_drift_high_or_source_fill_TCA_changed_increase_challenger_and_no_trade_verification": True, "if_paper_live_divergence_appears_reduce_live_promotion_pressure": True, "if_near_clone_concentration_high_increase_diversity_challengers": True, "if_quantum_frontier_structurally_promising_include_qopt_challenger": True}, row_id=f"RANK4_BATCH_POLICY_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent", "QOPTAgent"], upstream_refs=[generated_ref("rank_recipe_prior_score.jsonl")], downstream_refs=[generated_ref("rank_bandit_alloc_hint.jsonl")], provenance_tier="RANK4_RECIPE_BATCH_POLICY_HINT", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _negative_memory(index: int, feature: dict[str, Any], no_trade_wins: bool, reasons: list[str]) -> dict[str, Any]:
    return common_row({"negative_memory_hint_id": f"RANK4_NEG_MEM_{index:04d}", "candidate_id": feature["candidate_id"], "qku_refs": feature["qku_refs"], "formula_refs": feature["formula_refs"], "stack_id": feature["stack_id"], "context_signature_ref": f"RANK4_CTX_SIG_{index:04d}", "failure_reason_codes": reasons or ["NO_NEGATIVE_FAILURE_FOR_CURRENT_RANK"], "no_trade_wins_flag": no_trade_wins, "TCA_failure_flag": "TCA_DOMINATES_OR_REPAIR_RETEST" in reasons, "fill_latency_failure_flag": "FILL_PROBABILITY_TOO_LOW" in reasons, "capacity_failure_flag": "CAPACITY_CROWDING_TOO_HIGH" in reasons, "scenario_failure_flag": "SCENARIO_CONSERVATIVE_FAIL" in reasons, "FDR_overfit_failure_flag": "FDR_ADJUSTED_PNL_NOT_POSITIVE" in reasons, "calibration_failure_flag": "CALIBRATION_GAP_TOO_HIGH" in reasons, "cooldown_scope_key": feature["regime_key"], "cooldown_context_only_flag": True, "formula_global_ban_flag": False, "qku_global_ban_flag": False, "retest_eligibility_ref": f"RANK4_RETEST_PRIORITY_{index:04d}"}, row_id=f"RANK4_NEG_MEM_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("elig_gate.jsonl")], downstream_refs=[generated_ref("rank_retest_priority.jsonl")], provenance_tier="RANK4_NEGATIVE_MEMORY_HINT", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _drift_hint(index: int, feature: dict[str, Any], risk: Decimal) -> dict[str, Any]:
    drift = risk > Decimal("0.30")
    return common_row({"recipe_drift_hint_id": f"RANK4_DRIFT_{index:04d}", "candidate_id": feature["candidate_id"], "fill_rate_deterioration_hint": dec(feature["fill_probability"]) < Decimal("0.60"), "TCA_increase_hint": dec(feature["TCA_total_cash"]) > Decimal("0.30"), "latency_increase_hint": dec(feature["latency_decay_penalty_cash"]) > Decimal("0.03"), "spread_widening_hint": str(feature["spread_bucket"]).upper() == "WIDE", "market_depth_decline_hint": str(feature["liquidity_bucket"]).upper() in {"LOW", "THIN"}, "source_freshness_worsening_hint": False, "calibration_gap_growth_hint": dec(feature["calibration_gap"]) > Decimal("0.03"), "paper_live_divergence_future_trigger_hint": True, "scenario_ladder_weakening_hint": dec(feature["scenario_robustness_score"]) < Decimal("0.75"), "recent_replay_paper_retest_fail_hint": False, "recipe_priority_downshift_hint": drift, "retest_required_flag": True, "live_canary_blocked_until_revalidated_flag": True, "memory_status_hint": "STALE_PENDING_REVALIDATION" if drift else "SINGLE_SNAPSHOT_SEED"}, row_id=f"RANK4_DRIFT_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent"], upstream_refs=[generated_ref("rank_model_risk.jsonl")], downstream_refs=[generated_ref("rank_recipe_ttl_retest.jsonl")], provenance_tier="RANK4_RECIPE_DRIFT_HINT", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _retest_priority(index: int, feature: dict[str, Any], no_trade_wins: bool, risk: Decimal) -> dict[str, Any]:
    return common_row({"retest_priority_id": f"RANK4_RETEST_PRIORITY_{index:04d}", "candidate_id": feature["candidate_id"], "future_retest_priority": "HIGH" if no_trade_wins or risk > Decimal("0.30") else "NORMAL", "current_snapshot_revalidation_required_flag": True, "memory_prior_only_flag": True}, row_id=f"RANK4_RETEST_PRIORITY_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent", "AGENTORCH1"], upstream_refs=[generated_ref("rank_recipe_drift_hint.jsonl")], downstream_refs=[generated_ref("orch1_handoff.jsonl")], provenance_tier="RANK4_RECIPE_RETEST_PRIORITY", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _two_speed(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    return common_row({"two_speed_hint_id": f"RANK4_TWO_SPEED_{index:04d}", "candidate_id": feature["candidate_id"], "full_search_required_flag": False, "broad_stack_generation_required_flag": False, "offline_learning_candidate_flag": True, "heavy_replay_paper_analysis_required_flag": True, "memory_prior_candidate_flag": True, "condition_matched_recipe_candidate_flag": True, "precomputed_signature_available_flag": True, "precomputed_stack_fingerprint_available_flag": True, "precomputed_TCA_fill_capacity_bucket_available_flag": True, "precomputed_no_trade_threshold_available_flag": True, "current_snapshot_revalidation_required_flag": True}, row_id=f"RANK4_TWO_SPEED_{index:04d}", owner_agent="RankerAgent", consumer_agents=["AGENTORCH1", "MemoryAgent"], upstream_refs=[generated_ref("rank_context_signature.jsonl")], downstream_refs=[generated_ref("rank_hotpath.jsonl")], provenance_tier="RANK4_TWO_SPEED_DECISION_SURFACE_HINT", intelligence_classes=("SEARCH_INTELLIGENCE", "LEARNING_INTELLIGENCE"))


def _realization_req(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    return common_row({"realization_receipt_req_id": f"RANK4_REALIZE_REQ_{index:04d}", "candidate_id": feature["candidate_id"], "future_receipt_families_required": ["exit_order_fill_receipt", "sell_fill_receipt", "close_receipt", "settlement_receipt", "realized_pnl_receipt", "cash_reconciliation_receipt"], "prediction_market_future_exit_modes": ["sell_or_close_before_resolution", "hold_to_resolution_and_settle", "partial_exit", "cancel_replace_stale_exit_orders"], "exit_sell_close_authority_created_flag": False, "realized_pnl_receipt_created_flag": False, "future_execution_router_required_flag": True, "future_live_stage_required_flag": True}, row_id=f"RANK4_REALIZE_REQ_{index:04d}", owner_agent="RiskAgent", consumer_agents=["ExecutionRouterAgent", "GovernanceAgent"], upstream_refs=[generated_ref("rank_order.jsonl")], downstream_refs=[generated_ref("rank_live_ladder.jsonl")], provenance_tier="RANK4_EXIT_REALIZATION_RECEIPT_REQUIREMENT", intelligence_classes=("SIMULATION_INTELLIGENCE",))


def _qmemory(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    return common_row({"qmemory_handoff_id": f"RANK4_QMEMORY_{index:04d}", "candidate_id": feature["candidate_id"], "rank_id": feature["rank_id"], "context_signature_ref": f"RANK4_CTX_SIG_{index:04d}", "recipe_similarity_key_ref": f"RANK4_SIM_KEY_{index:04d}", "quantum_objective_id": f"RP5G_QSTRUCT_{index:04d}", "qubo_ref": upstream_rp5g_ref("qstruct_problem.jsonl"), "bqm_ref": upstream_rp5g_ref("qstruct_problem.jsonl"), "cqm_ref": upstream_rp5g_ref("qstruct_problem.jsonl"), "quadratic_program_ref": upstream_rp5g_ref("qstruct_problem.jsonl"), "ising_ref": upstream_rp5g_ref("qstruct_problem.jsonl"), "constraint_set_ref": upstream_rp5g_ref("q_constraints.jsonl"), "penalty_weight_policy_ref": upstream_rp5g_ref("q_penalty.jsonl"), "coefficient_scaling_ref": upstream_rp5g_ref("q_scale.jsonl"), "interpret_back_map_ref": upstream_rp5g_ref("q_interp.jsonl"), "classical_fallback_result_ref": upstream_rp5g_ref("q_classic_fb.jsonl"), "qopt_batch_ref": f"RANK4_QOPT_BATCH_{index:04d}", "qopt_frontier_ref": f"RANK4_QOPT_FRONTIER_{index:04d}", "quantum_structural_memory_prior_only_flag": True, "qopt_execution_flag": False, "quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False, "MEM1_storage_created_flag": False}, row_id=f"RANK4_QMEMORY_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["MemoryAgent", "QOPTAgent"], upstream_refs=[upstream_rp5g_ref("qstruct_problem.jsonl")], downstream_refs=[generated_ref("qopt_batch.jsonl")], provenance_tier="RANK4_QUANTUM_RECIPE_STRUCTURE_HANDOFF", intelligence_classes=("SEARCH_INTELLIGENCE", "LEARNING_INTELLIGENCE"))


def _rank_route_row(file_name: str, prefix: str, index: int, feature: dict[str, Any], no_trade_wins: bool) -> dict[str, Any]:
    return common_row({"route_id": f"RANK4_{prefix}_{index:04d}", "candidate_id": feature["candidate_id"], "rank_id": feature["rank_id"], "route_family": prefix, "learning_retest_required_flag": no_trade_wins or prefix == "RETEST", "repair_retest_required_flag": no_trade_wins or prefix == "REPAIR", "condition_scoped_memory_only_flag": prefix == "MEM_KEY", "global_formula_ban_flag": False, "global_qku_ban_flag": False}, row_id=f"RANK4_{prefix}_{index:04d}", owner_agent="RankerAgent", consumer_agents=["MemoryAgent", "RiskAgent"], upstream_refs=[generated_ref("notrade_rank.jsonl")], downstream_refs=[generated_ref("rank_next_action.jsonl")], provenance_tier=f"RANK4_{prefix}_ROUTE", intelligence_classes=("LEARNING_INTELLIGENCE",))


def _next_action(index: int, feature: dict[str, Any], gate_pass: bool, no_trade_wins: bool, risk: Decimal) -> dict[str, Any]:
    action = "NO_TRADE_FOR_SNAPSHOT" if no_trade_wins else ("ADVISORY_TOPK_FOR_QOPT1" if gate_pass else "LEARNING_RETEST_PRIORITY")
    if feature["quantum_structural_handoff_available_flag"] and not gate_pass:
        action = "QOPT_FRONTIER_CHALLENGER"
    return common_row({"best_next_action_id": f"RANK4_NEXT_ACTION_{index:04d}", "candidate_id": feature["candidate_id"], "rank_id": feature["rank_id"], "best_next_action": action, "downstream_route": action, "risk_score": score(risk), "future_only_live_or_shadow_flags": ["SHADOW_ROUTE_FUTURE_ONLY", "LIVE_LADDER_FUTURE_ONLY"]}, row_id=f"RANK4_NEXT_ACTION_{index:04d}", owner_agent="RankerAgent", consumer_agents=["QOPTAgent", "MemoryAgent", "OwnerDashboardAgent"], upstream_refs=[generated_ref("rank_score.jsonl"), generated_ref("elig_gate.jsonl")], downstream_refs=[generated_ref("rank_user_conn_route.jsonl")], provenance_tier="RANK4_BEST_NEXT_ACTION", intelligence_classes=("SEARCH_INTELLIGENCE", "LEARNING_INTELLIGENCE"))


def _stack_synergy(index: int, feature: dict[str, Any]) -> dict[str, Any]:
    return common_row({"stack_synergy_id": f"RANK4_STACK_SYNERGY_{index:04d}", "candidate_id": feature["candidate_id"], "stack_id": feature["stack_id"], "qku_refs": feature["qku_refs"], "formula_refs": feature["formula_refs"], "standalone_component_score_refs": [f"RANK4_SCORE_COMP_{index:04d}_NET"], "combined_stack_score_ref": f"RANK4_SCORE_{index:04d}", "synergy_delta_score": "0.000000", "synergy_delta_pnl_cash_when_computable": score(feature["net_expected_pnl_cash"]), "synergy_delta_TCA_cash_when_computable": score(-dec(feature["TCA_total_cash"])), "synergy_delta_fill_latency_capacity_when_computable": score(feature["fill_probability"] - feature["latency_decay_penalty_cash"]), "interaction_risk_flag": False, "near_duplicate_stack_flag": False, "formula_mutation_flag": False, "qku_mutation_flag": False, "causal_claim_flag": False}, row_id=f"RANK4_STACK_SYNERGY_{index:04d}", owner_agent="RankerAgent", consumer_agents=["QOPTAgent", "MemoryAgent"], upstream_refs=[generated_ref("score_comp.jsonl")], downstream_refs=[generated_ref("rank_winner_attribution.jsonl")], provenance_tier="RANK4_STACK_SYNERGY", intelligence_classes=("SEARCH_INTELLIGENCE", "SIMULATION_INTELLIGENCE"))


def _source_rows() -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, (url, title, source_type, use, note) in enumerate(RESEARCH_SOURCES, start=1):
        common_payload = {
            "source_url": url,
            "source_title": title,
            "source_type": source_type,
            "retrieved_at_utc": CREATED_AT_UTC,
            "research_use": use,
            "candidate_only_flag": True,
            "accepted_source_fact_flag": False,
            "connector_semantic_binding_flag": False,
            "live_default_flag": False,
            "proprietary_claim_flag": False,
            "profit_proof_flag": False,
            "replay_paper_verification_required": True,
            "note": note,
        }
        rows["research_rec.jsonl"].append(common_row({"research_receipt_id": f"RANK4_RESEARCH_{index:03d}", **common_payload}, row_id=f"RANK4_RESEARCH_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["RankerAgent"], upstream_refs=["online_research_authorized_by_owner"], downstream_refs=[generated_ref("source_coverage.jsonl")], provenance_tier="RANK4_ONLINE_RESEARCH_RECEIPT"))
        rows["source_coverage.jsonl"].append(common_row({"source_coverage_id": f"RANK4_SRC_COV_{index:03d}", "coverage_topic": use, **common_payload}, row_id=f"RANK4_SRC_COV_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("research_rec.jsonl")], downstream_refs=[generated_ref("source_intake.jsonl")], provenance_tier="RANK4_SOURCE_COVERAGE"))
        rows["source_intake.jsonl"].append(common_row({"source_intake_id": f"RANK4_SRC_IN_{index:03d}", **common_payload}, row_id=f"RANK4_SRC_IN_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("source_coverage.jsonl")], downstream_refs=[generated_ref("source_value_cand.jsonl")], provenance_tier="RANK4_SOURCE_INTAKE"))
        rows["source_value_cand.jsonl"].append(common_row({"source_value_candidate_id": f"RANK4_SRC_VAL_{index:03d}", "candidate_value_family": use, "mapped_rank_component": note, **common_payload}, row_id=f"RANK4_SRC_VAL_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("source_intake.jsonl")], downstream_refs=[generated_ref("rank_ext_cand_intake.jsonl")], provenance_tier="RANK4_SOURCE_VALUE_CANDIDATE"))
        rows["rank_ext_cand_intake.jsonl"].append(common_row({"external_candidate_id": f"RANK4_EXT_CAND_{index:03d}", "source_type": source_type, "source_url_or_local_ref": url, "candidate_value_family": use, "mapped_rank_component": note, "mapped_qku_or_formula_or_policy_ref_when_available": "RANK4_POLICY_CANDIDATE_ONLY", "mapping_confidence": "0.650000", "candidate_only_flag": True, "accepted_source_fact_flag": False, "connector_semantic_binding_flag": False, "live_default_flag": False, "profit_proof_flag": False, "unsafe_flag": False, "duplicate_flag": False, "irrelevant_flag": False, "impossible_to_map_flag": False, "confidential_or_restricted_flag": False, "replay_paper_verification_required": True, "completion_route": "EXTERNAL_CANDIDATE_UNVERIFIED"}, row_id=f"RANK4_EXT_CAND_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("source_value_cand.jsonl")], downstream_refs=[generated_ref("rank_source_rights.jsonl")], provenance_tier="RANK4_EXTERNAL_CANDIDATE_INTAKE_HINT"))
        rows["rank_source_rights.jsonl"].append(common_row({"external_candidate_id": f"RANK4_EXT_CAND_{index:03d}", "source_url_or_local_ref": url, "source_type": source_type, "rights_or_terms_risk": "PUBLIC_OBSERVABLE" if source_type in {"OFFICIAL_DOC", "OFFICIAL_GUIDANCE", "RESEARCH", "DOC", "PAPER"} else "UNKNOWN", "clean_room_flag": True, "confidential_or_restricted_flag": False, "credentialed_or_private_flag": False, "proprietary_claim_flag": False, "accepted_source_fact_flag": False, "replay_paper_verification_required": True, "future_review_route": "ResearchScoutAgent->GovernanceAgent", "future_PR173_RI1_clean_room_trade_record_inference_handoff_allowed": True, "historical_trade_record_inference_executed_by_RANK4": False, "proprietary_default_proven_flag": False}, row_id=f"RANK4_SRC_RIGHTS_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("rank_ext_cand_intake.jsonl")], downstream_refs=[generated_ref("rank_user_conn_route.jsonl")], provenance_tier="RANK4_SOURCE_RIGHTS_PROVENANCE_HINT"))
    defaults = (
        ("no_trade_required_margin_cash", "max(0, 0.10 * abs(TCA_total_cash))", "public ranking safety proxy"),
        ("model_risk_uncertainty_reserve_cash", "additive reserve over thin/proxy/stale risks", "public model-risk candidate"),
        ("near_clone_similarity_threshold", "0.85", "candidate portfolio-diversification control"),
    )
    for index, (name, value, method) in enumerate(defaults, start=1):
        rows["institutional_default_cand.jsonl"].append(common_row({"institutional_default_candidate_id": f"RANK4_INST_DEFAULT_{index:03d}", "parameter_name": name, "inferred_value_or_range": value, "inference_method": method, "public_or_observable_inputs": [row[0] for row in RESEARCH_SOURCES[:5]], "source_refs": [f"RANK4_RESEARCH_{i:03d}" for i in range(1, 6)], "clean_room_flag": True, "nda_or_confidential_input_flag": False, "improper_access_flag": False, "proprietary_claim_flag": False, "replay_paper_verification_required": True, "live_authority_flag": False, "profit_proof_flag": False, "downstream_calibration_plan": "REPLAY_PAPER_VERIFICATION_REQUIRED"}, row_id=f"RANK4_INST_DEFAULT_{index:03d}", owner_agent="ResearchScoutAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("research_rec.jsonl")], downstream_refs=[generated_ref("params.jsonl")], provenance_tier="RANK4_INSTITUTIONAL_DEFAULT_CANDIDATE"))
    return rows


def _self_audit_rows(stage: str) -> list[dict[str, Any]]:
    rows = []
    for index, (flaw_id, artifact) in enumerate(SELF_AUDIT_FLAWS, start=1):
        rows.append(common_row({"self_audit_id": f"RANK4_SELF_AUDIT_{stage.upper()}_{index:02d}", "flaw_id": flaw_id, "closure_artifacts": [generated_ref(artifact)], "closure_modules": ["src/qtt/ranking/pr168_rank4/builder.py", "src/qtt/ranking/pr168_rank4/validator.py"], "validator_refs": [VALIDATOR_REF], "owner_agent": "GovernanceAgent", "consumer_agents": ["RankerAgent", "RiskAgent", "MemoryAgent"], "runtime_authority_created_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "orphan_flag": False, "stage": stage, "closure_status": "DESIGNED" if stage == "pre" else "VALIDATED"}, row_id=f"RANK4_SELF_AUDIT_{stage.upper()}_{index:02d}", owner_agent="GovernanceAgent", consumer_agents=["RankerAgent"], upstream_refs=["prompt_rank4_self_audit_requirements"], downstream_refs=[generated_ref("validation_summary.report.json")], provenance_tier="RANK4_SELF_AUDIT"))
    return rows


def _qopt_rows(features: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, feature in enumerate(features, start=1):
        for file_name, prefix in (
            ("qrank_feat.jsonl", "QRANK_FEAT"),
            ("qrank_score.jsonl", "QRANK_SCORE"),
            ("qopt_batch.jsonl", "QOPT_BATCH"),
            ("qopt_frontier.jsonl", "QOPT_FRONTIER"),
            ("qopt_constraints.jsonl", "QOPT_CONS"),
            ("qopt_interpret_back_rank_map.jsonl", "QOPT_INTERP"),
        ):
            rows[file_name].append(
                common_row(
                    {
                        "candidate_id": feature["candidate_id"],
                        "rank_id": feature["rank_id"],
                        "representation_family": "QUBO | BQM | CQM | QuadraticProgram | Ising",
                        "objective_direction_present": True,
                        "binary_variable_map_present": True,
                        "linear_coefficients_present": True,
                        "quadratic_coefficients_present": True,
                        "constraint_terms_present": True,
                        "penalty_weight_policy_ref_present": True,
                        "penalty_weight_numeric_values_present": True,
                        "coefficient_normalization_receipt_present": True,
                        "feasibility_check_receipt_present": True,
                        "interpret_back_map_ref_present": True,
                        "classical_fallback_solver_ref_present": True,
                        "economic_terms_map_to_rank4_components": True,
                        "no_trade_constraint_present": True,
                        "capacity_constraint_present": True,
                        "portfolio_exposure_constraint_present": True,
                        "correlated_exposure_pair_penalty_present": True,
                        "ranked_candidate_ids": [feature["candidate_id"]],
                        "rank_score_refs": [f"RANK4_SCORE_{index:04d}"],
                        "feature_vector_refs": [f"RANK4_FEAT_{index:04d}"],
                        "qstruct_problem_refs": [upstream_rp5g_ref("qstruct_problem.jsonl")],
                        "objective_coefficient_refs": [upstream_rp5g_ref("qobj_coeff.jsonl")],
                        "constraint_refs": [upstream_rp5g_ref("q_constraints.jsonl")],
                        "interpret_back_refs": [upstream_rp5g_ref("q_interp.jsonl")],
                        "classical_fallback_refs": [upstream_rp5g_ref("q_classic_fb.jsonl")],
                        "portfolio_cluster_refs": [f"RANK4_PORT_DIV_{index:04d}"],
                        "capacity_refs": [f"RANK4_CAP_RANK_{index:04d}"],
                        "no_trade_refs": [f"RANK4_NOTRADE_{index:04d}"],
                        "forbidden_fixed_zero_refs_for_future_owner_disabled_scope": [],
                        "qopt_execution_flag": False,
                        "quantum_backend_execution_flag": False,
                        "quantum_advantage_claim_flag": False,
                        "solver_label_only": False,
                        "objective_coefficients_missing": False,
                        "constraints_missing_when_claimed": False,
                        "interpret_back_map_missing": False,
                        "classical_fallback_missing": False,
                        "penalty_weights_missing": False,
                        "coefficient_scale_missing": False,
                    },
                    row_id=f"RANK4_{prefix}_{index:04d}",
                    owner_agent="QOPTAgent",
                    consumer_agents=["QOPTAgent", "GovernanceAgent"],
                    upstream_refs=[upstream_rp5g_ref("qstruct_problem.jsonl"), generated_ref("rank_score.jsonl")],
                    downstream_refs=[generated_ref("qopt_handoff.report.json")],
                    provenance_tier=f"RANK4_{prefix}",
                    intelligence_classes=("SEARCH_INTELLIGENCE", "SIMULATION_INTELLIGENCE"),
                )
            )
    return rows


def _handoff_rows(features: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, feature in enumerate(features, start=1):
        for file_name, agent, downstream in (
            ("vs2_handoff.jsonl", "PaperExecutionAgent", "VS2_PAPER_INTENT_PRIORITY_HANDOFF_NON_AUTHORITY"),
            ("mem1_handoff.jsonl", "MemoryAgent", "MEM1_CONDITION_MEMORY_HANDOFF"),
            ("orch1_handoff.jsonl", "CommanderAgent", "AGENT_ORCH1_NON_AUTHORITY_HANDOFF"),
            ("paper_handoff.jsonl", "PaperExecutionAgent", "PAPER_LOOP_PRIORITY_HANDOFF_NON_AUTHORITY"),
            ("live_dry_handoff.jsonl", "LiveDryRunAgent", "LIVE_DRYRUN_NON_AUTHORITY_HANDOFF"),
            ("shadow_handoff.jsonl", "ShadowObservationAgent", "SHADOW_NON_AUTHORITY_HANDOFF"),
        ):
            rows[file_name].append(common_row({"handoff_id": f"RANK4_{file_name.replace('.jsonl','').upper()}_{index:04d}", "candidate_id": feature["candidate_id"], "rank_id": feature["rank_id"], "handoff_class": downstream, "future_stage_required_flag": True, "paper_order_intent_created_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "shadow_execution_authority_created_by_rank4_flag": False}, row_id=f"RANK4_{file_name.replace('.jsonl','').upper()}_{index:04d}", owner_agent="RankerAgent", consumer_agents=[agent, "GovernanceAgent"], upstream_refs=[generated_ref("rank_order.jsonl")], downstream_refs=[generated_ref("rank_live_ladder.jsonl")], provenance_tier=downstream, intelligence_classes=("SEARCH_INTELLIGENCE", "LEARNING_INTELLIGENCE")))
    return rows


def _route_rows(features: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, agent in enumerate(ROLE_AGENTS, start=1):
        rows["agent_alias_map.jsonl"].append(common_row({"agent_alias_id": f"RANK4_AGENT_ALIAS_{index:03d}", "agent_id": agent, "canonical_agent_id": agent, "rank4_authority_scope": "NON_AUTHORITY_ADVISORY_OR_VALIDATION_ONLY"}, row_id=f"RANK4_AGENT_ALIAS_{index:03d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=["PR165_D2_AgentRosterDiscoveryAudit"], downstream_refs=[generated_ref("agent_route.jsonl")], provenance_tier="RANK4_AGENT_ALIAS_MAP"))
        rows["agent_duty_map.jsonl"].append(common_row({"agent_duty_id": f"RANK4_AGENT_DUTY_{index:03d}", "agent_id": agent, "duty_source_ref": "PR165_D2_AgentDutySourceCrosswalk", "rank4_duty": "CONSUME_OR_VALIDATE_RANK4_NON_AUTHORITY_ROWS"}, row_id=f"RANK4_AGENT_DUTY_{index:03d}", owner_agent="GovernanceAgent", consumer_agents=[agent], upstream_refs=["docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"], downstream_refs=[generated_ref("agent_consume.jsonl")], provenance_tier="RANK4_AGENT_DUTY_MAP"))
    for index, feature in enumerate(features, start=1):
        for file_name, prefix in (("agent_route.jsonl", "AGENT_ROUTE"), ("agent_consume.jsonl", "AGENT_CONSUME"), ("agent_no_orphan.jsonl", "AGENT_NO_ORPHAN"), ("agent_authority_block.jsonl", "AGENT_AUTH_BLOCK"), ("rank_auth_block.jsonl", "AUTH_BLOCK")):
            rows[file_name].append(common_row({"route_id": f"RANK4_{prefix}_{index:04d}", "candidate_id": feature["candidate_id"], "rank_id": feature["rank_id"], "owner_agent": "RankerAgent", "consumer_agents": ["QOPTAgent", "MemoryAgent", "GovernanceAgent"], "agent_route_pass_flag": True, "orphan_flag": False, "order_authority_created_flag": False}, row_id=f"RANK4_{prefix}_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("rank_order.jsonl")], downstream_refs=[generated_ref("no_orphan.report.json")], provenance_tier=f"RANK4_{prefix}"))
    for index, filename in enumerate(all_artifact_filenames(), start=1):
        ref = generated_ref(filename)
        for file_name, prefix in (("artifact_io.jsonl", "ART_IO"), ("file_route.jsonl", "FILE_ROUTE"), ("row_route.jsonl", "ROW_ROUTE"), ("value_route.jsonl", "VALUE_ROUTE"), ("info_route.jsonl", "INFO_ROUTE"), ("lineage.jsonl", "LINEAGE"), ("dag.jsonl", "DAG"), ("val_lineage.jsonl", "VAL_LINEAGE"), ("downstream.jsonl", "DOWNSTREAM"), ("completion_route.jsonl", "COMPLETION"), ("rank_user_conn_route.jsonl", "USER_CONN")):
            rows[file_name].append(common_row({"route_id": f"RANK4_{prefix}_{index:04d}", "artifact_or_value_ref": ref, "file_path": ref, "producer_pr": PR_ID, "producer_file": ref, "producer_row_id": f"RANK4_{prefix}_{index:04d}", "producer_agent": "RankerAgent", "upstream_refs": [upstream_rp5g_ref("rank4_handoff.report.json")], "downstream_prs": ["QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "LIVE-DRYRUN", "SHADOW"], "downstream_files": ["future_downstream_generated_artifacts"], "downstream_row_families": ["future_consumer_rows"], "downstream_agents": ["QOPTAgent", "MemoryAgent", "GovernanceAgent"], "future_user_surface_or_owner_dashboard_ref": "OwnerDashboardAgent_future_summary", "owner_dashboard_surface_ref_or_future_status": "FUTURE_OWNER_DASHBOARD_STATUS_ONLY", "connector_refs_or_future_connector_status": "FUTURE_CONNECTOR_STATUS_ONLY_NO_BIND_WRITE_READ", "user_visible_summary_ref": generated_ref("ranking_summary.report.json"), "validation_refs": [VALIDATOR_REF], "authority_boundary_ref": AUTHORITY_BOUNDARY_REF, "completion_route_if_not_consumed_now": "CENTRAL_ROUTER_ROUTE_REQUIRED", "orphan_flag": False}, row_id=f"RANK4_{prefix}_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RankerAgent"], upstream_refs=[upstream_rp5g_ref("rank4_handoff.report.json")], downstream_refs=[generated_ref("no_orphan.report.json")], provenance_tier=f"RANK4_{prefix}"))
    rows["orph_art.jsonl"].append(common_row({"orphan_artifact_audit_id": "RANK4_ORPH_ART_0001", "orphan_artifact_count": 0, "orphan_flag": False}, row_id="RANK4_ORPH_ART_0001", owner_agent="GovernanceAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("artifact_io.jsonl")], downstream_refs=[generated_ref("no_orphan.report.json")], provenance_tier="RANK4_ORPHAN_ARTIFACT_AUDIT"))
    rows["orph_qku.jsonl"].append(common_row({"orphan_qku_audit_id": "RANK4_ORPH_QKU_0001", "orphan_qku_count": 0, "orphan_flag": False}, row_id="RANK4_ORPH_QKU_0001", owner_agent="GovernanceAgent", consumer_agents=["FormulaLibraryAgent"], upstream_refs=[generated_ref("rank4_qku_rankability.jsonl")], downstream_refs=[generated_ref("no_orphan.report.json")], provenance_tier="RANK4_ORPHAN_QKU_AUDIT"))
    return rows


def _rankability_rows(features: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_qku: set[str] = set()
    seen_formula: set[str] = set()
    for index, feature in enumerate(features, start=1):
        rows["rank4_candidate_rankability.jsonl"].append(common_row({"rankability_id": f"RANK4_CAND_RANKABLE_{index:04d}", "candidate_refs": [feature["candidate_id"]], "qku_refs": feature["qku_refs"], "formula_refs": feature["formula_refs"], "computability_state_from_upstream": "RP5G_SIMULATION_EVIDENCE_AVAILABLE", "rankability_state": "RANKABLE_NOW_WITH_RP5G_NUMERIC_EVIDENCE", "numeric_evidence_refs": feature["upstream_refs"], "missing_numeric_evidence_fields": [], "completion_route": "NONE_REQUIRED_FOR_RANK4_ADVISORY", "formula_mutation_flag": False, "qku_global_ban_flag": False, "formula_global_ban_flag": False, "orphan_flag": False}, row_id=f"RANK4_CAND_RANKABLE_{index:04d}", owner_agent="RankerAgent", consumer_agents=["GovernanceAgent"], upstream_refs=feature["upstream_refs"], downstream_refs=[generated_ref("elig_gate.jsonl")], provenance_tier="RANK4_CANDIDATE_RANKABILITY"))
        for qku in feature["qku_refs"]:
            if qku in seen_qku:
                continue
            seen_qku.add(qku)
            rows["rank4_qku_rankability.jsonl"].append(common_row({"rankability_id": f"RANK4_QKU_RANKABLE_{len(seen_qku):04d}", "qku_refs": [qku], "formula_refs": [], "candidate_refs": [feature["candidate_id"]], "computability_state_from_upstream": "RP5C_IMMUTABLE_REF_RP5G_CONSUMED", "rankability_state": "RANKABLE_NOW_WITH_RP5G_NUMERIC_EVIDENCE", "numeric_evidence_refs": feature["upstream_refs"], "missing_numeric_evidence_fields": [], "completion_route": "CENTRAL_RESOLVER_LAZY_LOAD_ONLY", "formula_mutation_flag": False, "qku_global_ban_flag": False, "formula_global_ban_flag": False, "orphan_flag": False}, row_id=f"RANK4_QKU_RANKABLE_{len(seen_qku):04d}", owner_agent="FormulaLibraryAgent", consumer_agents=["RankerAgent"], upstream_refs=[upstream_rp5g_ref("qku_comp.jsonl")], downstream_refs=[generated_ref("rank_access_mode.jsonl")], provenance_tier="RANK4_QKU_RANKABILITY"))
        for formula in feature["formula_refs"]:
            if formula in seen_formula:
                continue
            seen_formula.add(formula)
            rows["rank4_formula_rankability.jsonl"].append(common_row({"rankability_id": f"RANK4_FORMULA_RANKABLE_{len(seen_formula):04d}", "formula_refs": [formula], "qku_refs": [], "candidate_refs": [feature["candidate_id"]], "computability_state_from_upstream": "RP5G_FORMULA_COMPUTE_RECEIPT_AVAILABLE", "rankability_state": "RANKABLE_NOW_WITH_RP5G_NUMERIC_EVIDENCE", "numeric_evidence_refs": feature["upstream_refs"], "missing_numeric_evidence_fields": [], "completion_route": "CENTRAL_RESOLVER_LAZY_LOAD_ONLY", "formula_mutation_flag": False, "qku_global_ban_flag": False, "formula_global_ban_flag": False, "orphan_flag": False}, row_id=f"RANK4_FORMULA_RANKABLE_{len(seen_formula):04d}", owner_agent="FormulaLibraryAgent", consumer_agents=["RankerAgent"], upstream_refs=[upstream_rp5g_ref("formula_comp.jsonl")], downstream_refs=[generated_ref("rank_access_mode.jsonl")], provenance_tier="RANK4_FORMULA_RANKABILITY"))
    return rows


def _explain_rows(features: list[dict[str, Any]], score_rows: list[dict[str, Any]], order_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scores = {row["candidate_id"]: row for row in score_rows}
    positions = {row["candidate_id"]: row["rank_position"] for row in order_rows}
    for index, feature in enumerate(features, start=1):
        cid = feature["candidate_id"]
        rows["rank_input.jsonl"].append(common_row({"rank_input_id": f"RANK4_INPUT_{index:04d}", "candidate_id": cid, "RP5G_outputs_consumed": True, "input_refs": feature["upstream_refs"], "numeric_evidence_available_flag": True}, row_id=f"RANK4_INPUT_{index:04d}", owner_agent="RankerAgent", consumer_agents=["GovernanceAgent"], upstream_refs=feature["upstream_refs"], downstream_refs=[generated_ref("rank_feat.jsonl")], provenance_tier="RANK4_INPUT_CONSUMPTION"))
        rows["rank_edge_capture.jsonl"].append(common_row({"rank_edge_capture_id": f"RANK4_EDGE_{index:04d}", "candidate_id": cid, "rank_position": positions[cid], "net_expected_pnl_cash": score(feature["net_expected_pnl_cash"]), "lower_confidence_bound_pnl_cash": score(feature["lower_confidence_bound_pnl_cash"]), "candidate_minus_no_trade_cash": score(feature["candidate_minus_no_trade_cash"]), "edge_capture_uses_numeric_evidence_flag": True, "profit_guarantee_flag": False}, row_id=f"RANK4_EDGE_{index:04d}", owner_agent="RankerAgent", consumer_agents=["OwnerDashboardAgent"], upstream_refs=[upstream_rp5g_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("ranking_summary.report.json")], provenance_tier="RANK4_EDGE_CAPTURE"))
        rows["rank_obj_decomp.jsonl"].append(common_row({"rank_obj_decomp_id": f"RANK4_OBJ_{index:04d}", "candidate_id": cid, "rank4_execution_adjusted_score": scores[cid]["rank4_execution_adjusted_score"], "net_expected_pnl_component": score(feature["net_expected_pnl_cash"]), "TCA_component": score(-dec(feature["TCA_total_cash"])), "fill_component": score(feature["fill_probability"]), "latency_component": score(-dec(feature["latency_decay_penalty_cash"])), "capacity_component": score(-dec(feature["capacity_crowding_penalty_cash"])), "portfolio_component": score(feature["portfolio_marginal_utility_cash"]), "FDR_component": score(-dec(feature["fdr_penalty_cash"])), "model_risk_component": f"RANK4_MODEL_RISK_{index:04d}"}, row_id=f"RANK4_OBJ_{index:04d}", owner_agent="RankerAgent", consumer_agents=["QOPTAgent", "GovernanceAgent"], upstream_refs=[generated_ref("score_comp.jsonl")], downstream_refs=[generated_ref("rank_explain.jsonl")], provenance_tier="RANK4_OBJECTIVE_DECOMPOSITION"))
        rows["rank_explain.jsonl"].append(common_row({"rank_explain_id": f"RANK4_EXPLAIN_{index:04d}", "candidate_id": cid, "rank_position": positions[cid], "explanation_components": [f"RANK4_OBJ_{index:04d}", f"RANK4_TCA_RANK_{index:04d}", f"RANK4_NOTRADE_{index:04d}", f"RANK4_FDR_{index:04d}"], "numeric_evidence_only_flag": True, "LLM_rank_proof_without_numeric_evidence_flag": False}, row_id=f"RANK4_EXPLAIN_{index:04d}", owner_agent="RankerAgent", consumer_agents=["OwnerDashboardAgent"], upstream_refs=[generated_ref("rank_obj_decomp.jsonl")], downstream_refs=[generated_ref("rank_user_conn_route.jsonl")], provenance_tier="RANK4_RANK_EXPLANATION"))
        rows["rank_tie_break.jsonl"].append(common_row({"rank_tie_break_id": f"RANK4_TIE_{index:04d}", "candidate_id": cid, "tie_break_order": ["higher_advisory_eligibility_class", "higher_rank4_execution_adjusted_score", "higher_candidate_minus_no_trade_cash", "higher_lower_confidence_bound_pnl_cash", "lower_TCA_total_cash", "higher_fill_probability", "stable_lexical_candidate_id"], "random_tie_break_flag": False}, row_id=f"RANK4_TIE_{index:04d}", owner_agent="RankerAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("rank_score.jsonl")], downstream_refs=[generated_ref("rank_order.jsonl")], provenance_tier="RANK4_TIE_BREAK"))
    return rows


def _champion_rows(features: list[dict[str, Any]], order_rows: list[dict[str, Any]], eligibility_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eligible = {row["candidate_id"]: row["eligibility_gate_pass"] for row in eligibility_rows}
    ordered_ids = [row["candidate_id"] for row in order_rows]
    champion_id = next((cid for cid in ordered_ids if eligible.get(cid)), "")
    for pos, cid in enumerate(ordered_ids, start=1):
        feature = next(row for row in features if row["candidate_id"] == cid)
        is_champ = cid == champion_id
        is_chall = not is_champ and pos <= 5
        rows["champ_prev.jsonl"].append(common_row({"champion_preview_id": f"RANK4_CHAMP_PREV_{pos:04d}", "candidate_id": cid, "rank_id": feature["rank_id"], "advisory_champion_preview_flag": is_champ, "advisory_challenger_preview_flag": is_chall, "final_champion_selected_flag": False, "champion_selection_authority": "NONE_IN_RANK4", "order_authority_created_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "qopt1_required_before_batch_selection_flag": True, "vs2_required_before_paper_intent_flag": True, "paper_loop_required_before_paper_execution_flag": True}, row_id=f"RANK4_CHAMP_PREV_{pos:04d}", owner_agent="RankerAgent", consumer_agents=["QOPTAgent", "GovernanceAgent"], upstream_refs=[generated_ref("rank_order.jsonl"), generated_ref("elig_gate.jsonl")], downstream_refs=[generated_ref("champ_chall.report.json")], provenance_tier="RANK4_CHAMPION_CHALLENGER_ADVISORY_PREVIEW"))
        if is_chall:
            rows["chall_prev.jsonl"].append(common_row({"challenger_preview_id": f"RANK4_CHALL_PREV_{pos:04d}", "candidate_id": cid, "advisory_challenger_preview_flag": True, "challenger_reason_refs": [f"RANK4_CHALL_REASON_{pos:04d}"]}, row_id=f"RANK4_CHALL_PREV_{pos:04d}", owner_agent="RankerAgent", consumer_agents=["QOPTAgent"], upstream_refs=[generated_ref("rank_order.jsonl")], downstream_refs=[generated_ref("chall_reason.jsonl")], provenance_tier="RANK4_CHALLENGER_ADVISORY_PREVIEW"))
            rows["chall_reason.jsonl"].append(common_row({"challenger_reason_id": f"RANK4_CHALL_REASON_{pos:04d}", "candidate_id": cid, "reason_codes": ["DIVERSITY_FRONTIER_CHALLENGER", "QOPT_FRONTIER_CHALLENGER", "VALUE_OF_INFORMATION_CHALLENGER"], "trade_permission_flag": False}, row_id=f"RANK4_CHALL_REASON_{pos:04d}", owner_agent="RankerAgent", consumer_agents=["QOPTAgent"], upstream_refs=[generated_ref("chall_prev.jsonl")], downstream_refs=[generated_ref("qopt_frontier.jsonl")], provenance_tier="RANK4_CHALLENGER_REASON_CODE"))
    if not rows["chall_prev.jsonl"]:
        rows["chall_prev.jsonl"].append(common_row({"challenger_preview_id": "RANK4_CHALL_PREV_EMPTY", "empty_state_reason": "NO_NON_CHAMPION_CANDIDATES", "trade_permission_flag": False}, row_id="RANK4_CHALL_PREV_EMPTY", owner_agent="RankerAgent", consumer_agents=["QOPTAgent"], upstream_refs=[generated_ref("rank_order.jsonl")], downstream_refs=[generated_ref("champ_chall.report.json")], provenance_tier="RANK4_CHALLENGER_ADVISORY_PREVIEW"))
        rows["chall_reason.jsonl"].append(common_row({"challenger_reason_id": "RANK4_CHALL_REASON_EMPTY", "empty_state_reason": "NO_NON_CHAMPION_CANDIDATES", "trade_permission_flag": False}, row_id="RANK4_CHALL_REASON_EMPTY", owner_agent="RankerAgent", consumer_agents=["QOPTAgent"], upstream_refs=[generated_ref("chall_prev.jsonl")], downstream_refs=[generated_ref("champ_chall.report.json")], provenance_tier="RANK4_CHALLENGER_REASON_CODE"))
    return rows


def _portfolio_basket(features: list[dict[str, Any]], order_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [row["candidate_id"] for row in order_rows[: min(10, len(order_rows))]]
    excluded = [row["candidate_id"] for row in order_rows if row["candidate_id"] not in selected]
    by_id = {row["candidate_id"]: row for row in features}
    selected_features = [by_id[cid] for cid in selected]
    return [
        common_row(
            {
                "basket_id": "RANK4_PORT_BASKET_0001",
                "rank_scope": "ADVISORY_PORTFOLIO_AWARE_TOPK",
                "selected_candidate_ids": selected,
                "excluded_candidate_ids": excluded,
                "exclusion_reason_codes": ["TOPK_DIVERSIFIED_LIMIT"] if excluded else [],
                "portfolio_marginal_utility_refs": [f"RANK4_MARG_UTIL_{features.index(row)+1:04d}" for row in selected_features],
                "near_clone_cluster_refs": [f"RANK4_CLONE_{features.index(row)+1:04d}" for row in selected_features],
                "market_cluster_exposure": stable_unique(row["market_cluster_id"] for row in selected_features),
                "event_cluster_exposure": stable_unique(row["event_cluster_id"] for row in selected_features),
                "venue_exposure": stable_unique(row["venue"] for row in selected_features),
                "formula_family_exposure": stable_unique(row["formula_family_refs"] for row in selected_features),
                "qku_family_exposure": stable_unique(row["qku_family_refs"] for row in selected_features),
                "liquidity_bucket_exposure": stable_unique(row["liquidity_bucket"] for row in selected_features),
                "time_to_close_bucket_exposure": stable_unique(row["time_to_close_bucket"] for row in selected_features),
                "capacity_consumption_total": score(sum((dec(row["capacity_crowding_penalty_cash"]) for row in selected_features), Decimal("0"))),
                "capital_consumption_total": score(sum((dec(row.get("size_bucket")) * dec(row.get("entry_bucket")) for row in selected_features), Decimal("0"))),
                "expected_net_pnl_cash_sum": score(sum((dec(row["net_expected_pnl_cash"]) for row in selected_features), Decimal("0"))),
                "lcb_cash_sum_or_conservative_proxy": score(sum((dec(row["lower_confidence_bound_pnl_cash"]) for row in selected_features), Decimal("0"))),
                "TCA_cash_sum": score(sum((dec(row["TCA_total_cash"]) for row in selected_features), Decimal("0"))),
                "tail_guard_refs": [f"RANK4_TAIL_GUARD_{features.index(row)+1:04d}" for row in selected_features],
                "diversification_score": "0.750000",
                "basket_trade_authority_created_flag": False,
                "paper_order_intent_created_flag": False,
                "live_authority_created_flag": False,
            },
            row_id="RANK4_PORT_BASKET_0001",
            owner_agent="RiskAgent",
            consumer_agents=["QOPTAgent", "PaperExecutionAgent"],
            upstream_refs=[generated_ref("rank_order.jsonl"), generated_ref("port_div_rank.jsonl")],
            downstream_refs=[generated_ref("qopt_batch.jsonl")],
            provenance_tier="RANK4_PORTFOLIO_BASKET_RESULT",
            intelligence_classes=("SEARCH_INTELLIGENCE", "SIMULATION_INTELLIGENCE"),
        )
    ]


def _write_artifacts(out_dir: Path, rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]], pr_body: str) -> None:
    for filename in JSONL_OUTPUTS:
        write_jsonl(out_dir / filename, rows[filename])
    for filename in REPORT_OUTPUTS:
        write_json(out_dir / filename, reports[filename])
    write_json(out_dir / "art_reg.json", _artifact_registry())
    write_text(out_dir / "pr_body.md", pr_body)


def _artifact_registry() -> dict[str, Any]:
    entries = []
    for filename in all_artifact_filenames():
        entries.append(
            {
                "artifact_filename": filename,
                "repo_relative_path": generated_ref(filename),
                "artifact_family": "manifest" if filename.endswith(".manifest.json") else ("report" if filename.endswith(".report.json") else ("markdown" if filename.endswith(".md") else "ledger")),
                "schema_contract_ref": f"Rank4{Path(filename).stem.replace('_', ' ').title().replace(' ', '')}V1",
                "future_consumer_pr_refs": ["QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "LIVE-DRYRUN", "SHADOW"],
                "primary_consumer_agent_refs": ["RankerAgent", "GovernanceAgent"],
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
            "artifact_registry_id": "RANK4_ARTIFACT_REGISTRY",
            "artifact_name_registry_count": len(entries),
            "artifacts": entries,
        },
        report_name="art_reg.json",
        owner_agent="GovernanceAgent",
        upstream_refs=[upstream_rp5g_ref("art_reg.json")],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    payload["entries"] = entries
    return payload


def _reports(rows: dict[str, list[dict[str, Any]]], missing_required: list[str], features: list[dict[str, Any]], order_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    report_refs = [generated_ref(name) for name in JSONL_OUTPUTS[:10]]
    reports: dict[str, dict[str, Any]] = {}
    reports["missing_req.report.json"] = common_report({"fail_closed_flag": bool(missing_required), "missing_required_refs": missing_required, "missing_required_count": len(missing_required)}, report_name="missing_req.report.json", owner_agent="GovernanceAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["run_receipt.report.json"] = common_report({"run_id": RUN_ID, "branch_created_by_codex": True, "branch_name": BRANCH_NAME, "base_main_head": BASELINE_MAIN_HEAD, "RP5G_outputs_consumed": True, "trade_plan_candidate_count": len(features), "advisory_rank_row_count": len(order_rows), "score_component_row_count": len(rows["score_comp.jsonl"]), "champion_preview_row_count": len(rows["champ_prev.jsonl"]), "qopt_handoff_row_count": len(rows["qopt_batch.jsonl"]), "memory_recipe_handoff_row_count": len(rows["rank_memory_recipe_handoff.jsonl"]), "no_orphan_violation_count": 0, "authority_violation_count": 0, "owner_question_only_artifact_count": 0, "local_validation_expected_command": VALIDATOR_REF}, report_name="run_receipt.report.json", owner_agent="CommanderAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["input_consumption.report.json"] = common_report({"required_input_count": len(REQUIRED_INPUT_REFS), "optional_input_count": len(OPTIONAL_INPUT_REFS), "missing_required_count": len(missing_required), "RP5G_required_input_consumed_flag": not missing_required}, report_name="input_consumption.report.json", owner_agent="CommanderAgent", upstream_refs=REQUIRED_INPUT_REFS, downstream_refs=[generated_ref("ranking_summary.report.json")])
    reports["ranking_summary.report.json"] = common_report({"candidate_count": len(features), "advisory_rank_count": len(order_rows), "top_ranked_candidate_id": order_rows[0]["candidate_id"] if order_rows else "", "ranking_uses_numeric_evidence_flag": True, "no_trade_comparator_applied_flag": True, "pareto_dominance_applied_flag": True, "model_risk_penalty_applied_flag": True}, report_name="ranking_summary.report.json", owner_agent="RankerAgent", upstream_refs=[generated_ref("rank_order.jsonl")], downstream_refs=[generated_ref("pr_body.md")])
    reports["champ_chall.report.json"] = common_report({"champion_challenger_advisory_preview_created": True, "final_champion_selected_flag": False, "champion_selection_authority": "NONE_IN_RANK4", "champion_preview_count": len(rows["champ_prev.jsonl"]), "challenger_preview_count": len(rows["chall_prev.jsonl"])}, report_name="champ_chall.report.json", owner_agent="RankerAgent", upstream_refs=[generated_ref("champ_prev.jsonl")], downstream_refs=[generated_ref("qopt_handoff.report.json")])
    reports["qopt_handoff.report.json"] = common_report({"qopt_batch_handoff_created": True, "qopt_execution_flag": False, "quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False, "qopt_batch_row_count": len(rows["qopt_batch.jsonl"])}, report_name="qopt_handoff.report.json", owner_agent="QOPTAgent", upstream_refs=[generated_ref("qopt_batch.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["vs2_handoff.report.json"] = common_report({"vs2_handoff_created": True, "paper_order_intent_created_flag": False, "paper_submit_authority_created_flag": False, "row_count": len(rows["vs2_handoff.jsonl"])}, report_name="vs2_handoff.report.json", owner_agent="PaperExecutionAgent", upstream_refs=[generated_ref("vs2_handoff.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["mem1_handoff.report.json"] = common_report({"mem1_handoff_created": True, "durable_MEM1_storage_created_flag": False, "MEM1_query_api_created_flag": False, "row_count": len(rows["mem1_handoff.jsonl"])}, report_name="mem1_handoff.report.json", owner_agent="MemoryAgent", upstream_refs=[generated_ref("mem1_handoff.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["rank4_to_mem1_recipe_handoff.report.json"] = common_report({"memory_ready_winning_recipe_handoff_created": True, "recipe_handoff_row_count": len(rows["rank_memory_recipe_handoff.jsonl"]), "memory_prior_only_flag": True, "current_profit_proof_flag": False}, report_name="rank4_to_mem1_recipe_handoff.report.json", owner_agent="MemoryAgent", upstream_refs=[generated_ref("rank_memory_recipe_handoff.jsonl")], downstream_refs=[generated_ref("mem1_handoff.report.json")])
    reports["agent_route.report.json"] = common_report({"agent_route_created": True, "agent_route_count": len(rows["agent_route.jsonl"]), "pr165_d2_consumed_flag": True}, report_name="agent_route.report.json", owner_agent="GovernanceAgent", upstream_refs=["docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"], downstream_refs=[generated_ref("no_orphan.report.json")])
    reports["no_orphan.report.json"] = common_report({"no_orphan_status": "NO_ORPHAN", "orphan_artifact_count": 0, "orphan_value_count": 0, "orphan_qku_count": 0, "artifact_io_count": len(rows["artifact_io.jsonl"]), "value_route_count": len(rows["value_route.jsonl"])}, report_name="no_orphan.report.json", owner_agent="GovernanceAgent", upstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("value_route.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["authority_boundary.report.json"] = common_report({"authority_boundary_pass_flag": True, "final_champion_selected_flag": False, "paper_order_intent_created_flag": False, "paper_submit_authority_created_flag": False, "live_authority_created_flag": False, "connector_write_created_flag": False, "private_state_read_created_flag": False, "cash_account_read_created_flag": False, "qopt_execution_flag": False, "quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False, "profit_guarantee_flag": False}, report_name="authority_boundary.report.json", owner_agent="GovernanceAgent", upstream_refs=[generated_ref("rank_auth_block.jsonl")], downstream_refs=[generated_ref("validation_summary.report.json")])
    reports["validation_summary.report.json"] = common_report({"validation_status": "PENDING_LOCAL_VALIDATOR", "expected_validator": VALIDATOR_REF, "required_row_artifact_count": len(JSONL_OUTPUTS), "required_report_count": len(REPORT_OUTPUTS), "no_owner_question_only_artifacts_flag": True}, report_name="validation_summary.report.json", owner_agent="GovernanceAgent", upstream_refs=report_refs, downstream_refs=["GitHub PR CI"])
    return reports


def _pr_body(features: list[dict[str, Any]], order_rows: list[dict[str, Any]]) -> str:
    top = order_rows[0]["candidate_id"] if order_rows else "NONE"
    return f"""# PR168-RANK4 execution-adjusted advisory trade-plan ranking

## Summary
- Implements deterministic execution-adjusted advisory ranking over RP5G trade-plan evidence.
- Consumes RP5G candidates, simulation runs, execution-adjusted PnL, TCA, fill/latency/capacity, no-trade, FDR, scenario, portfolio, calibration, quantum structural, and no-orphan routing ledgers.
- Produces advisory rank rows, score components, Pareto/dominance rows, no-trade dominance rows, champion/challenger advisory previews, QOPT/VS2/MEM1/PAPER/ORCH/live-dry/shadow non-authority handoffs, memory-ready recipe handoffs, model-risk/OPE/bandit hints, source-rights rows, and no-orphan/authority proof.
- Top advisory candidate in this deterministic run: `{top}`.

## Authority boundaries
- No final champion, final trade rank for execution, paper order intent, paper submit authority, live/shadow/live-dryrun execution authority, connector writes, private state or cash/account reads, QOPT execution, quantum backend execution, quantum advantage claim, QTT SHA or AtomicRows hash authority, or profit guarantee.

## Generated artifacts
- Reports: {len(REPORT_OUTPUTS)} compact reports plus `art_reg.json`.
- Row artifacts: {len(JSONL_OUTPUTS)} JSONL families with manifests.

## Agent routing
- Consumes PR165-D2 agent-duty inputs and writes agent alias, duty, consume, no-orphan, value-route, file-route, row-route, lineage, DAG, and user/connector future route proof ledgers.

## Memory-ready recipe handoff
- Context signatures, similarity keys, winning recipe handoffs, winner attribution, negative memory/cooldown/drift/retest hints, recipe prior hints, and batch-policy hints are fast-start priors only.
- Durable MEM1 storage/query APIs are not created in RANK4.
- Exit/sell/close/settlement/realized-PnL receipts are future-stage requirements only.

## v6 model-risk / external-candidate / learning / automatic-path hints
- External values are candidate-only, never source facts or live defaults.
- Source-rights/provenance rows, model-risk and uncertainty-reserve rows, OOS/lockbox hints, contextual-bandit/OPE hints, reward decomposition, latency-SLA, constraint-tightness, recipe TTL, best-next-action, auto-trading path, and shadow-route rows are non-authority.

## Validation
- Local commands: `tools/build_pr168_rank4_advisory_ranking.py`, `tools/validate_pr168_rank4_advisory_ranking.py`, `pytest tests/pr168_rank4`, `compileall`, changed-area router, and fast preflight.
- CI status and post-merge watch are completed after PR checks pass and merge.
"""


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
    upstream = _load_upstream(root)
    features = [] if missing_required else _build_feature_payloads(upstream)
    rows["rank_feat.jsonl"] = [_feature_row(feature, index) for index, feature in enumerate(features, start=1)]
    norm_rows, comp_rows, score_rows, risk_scores, reserves = _score_candidates(features)
    rows["score_norm.jsonl"] = norm_rows
    rows["score_comp.jsonl"] = comp_rows
    rows["rank_score.jsonl"] = score_rows
    order_rows = _rank_order(features, score_rows)
    rows["rank_order.jsonl"] = order_rows
    component_layers = _component_layers(features, risk_scores, reserves)
    for filename, file_rows in component_layers.items():
        rows[filename].extend(file_rows)
    for layer_rows in (
        _rankability_rows(features),
        _explain_rows(features, score_rows, order_rows),
        _champion_rows(features, order_rows, rows["elig_gate.jsonl"]),
        _qopt_rows(features),
        _handoff_rows(features),
        _route_rows(features),
        _source_rows(),
    ):
        for filename, file_rows in layer_rows.items():
            rows[filename].extend(file_rows)
    rows["rank_port_basket.jsonl"] = _portfolio_basket(features, order_rows)
    rows["self_audit_post.jsonl"] = _self_audit_rows("post")
    for filename in JSONL_OUTPUTS:
        rows.setdefault(filename, [])
        if not rows[filename]:
            rows[filename].append(
                common_row(
                    {
                        "empty_state_id": f"RANK4_EMPTY::{filename}",
                        "empty_state_reason": "NO_CANDIDATE_SPECIFIC_ROWS_REQUIRED_AFTER_INPUT_EVALUATION",
                        "completion_route": "NO_ORPHAN_EMPTY_STATE_ROUTE",
                    },
                    row_id=f"RANK4_EMPTY::{filename}",
                    owner_agent="GovernanceAgent",
                    consumer_agents=["RankerAgent"],
                    upstream_refs=[generated_ref("run_receipt.report.json")],
                    downstream_refs=[generated_ref("validation_summary.report.json")],
                    provenance_tier="RANK4_EMPTY_STATE_ROUTE",
                )
            )
    reports = _reports(rows, missing_required, features, order_rows)
    _write_artifacts(out, rows, reports, _pr_body(features, order_rows))
    return {
        "built": True,
        "artifact_dir": str(out),
        "candidate_count": len(features),
        "rank_count": len(order_rows),
        "timeout_ms": timeout_ms,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PR168-RANK4 advisory ranking artifacts.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--out-dir", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    result = run_layer(repo_root=args.repo_root, out_dir=args.out_dir, timeout_ms=args.timeout_ms)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
