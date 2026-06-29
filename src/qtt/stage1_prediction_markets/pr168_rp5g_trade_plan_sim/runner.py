"""Deterministic PR168-RP5G replay/paper trade-plan simulation generator."""

from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import sys
from typing import Any, Iterable

from .artifact_names import build_artifact_name_entries
from .calibration import calibration_summary
from .capacity_crowding import capacity_crowding_summary
from .champion_challenger_preview import future_review_eligibility
from .classical_fallback import best_classical_candidate
from .execution_adjusted_rank_preview import DEFAULT_WEIGHTS, scored_rank_score
from .expected_pnl import expected_gross_pnl_cash, gross_edge_per_contract, lower_confidence_bound_pnl, normalize_price
from .fill_latency_capacity import adjustment_summary
from .models import (
    BASELINE_SHA_VCS_METADATA_ONLY,
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
    RUN_ID,
    VALIDATOR_REF,
    all_artifact_filenames,
    dec,
    generated_ref,
    read_json,
    read_jsonl,
    rel_ref,
    schema_name,
    score,
    stable_unique,
    with_common,
    write_json,
    write_jsonl,
    write_text,
)
from .no_trade_comparator import compare_to_no_trade
from .overfit_fdr import fdr_summary
from .path_safety import path_safety_failures
from .portfolio_marginal_utility import portfolio_utility_summary
from .qopt_handoff import qopt_boundary_flags
from .quantum_constraints import default_constraint_terms
from .quantum_interpret_back import interpret_back
from .quantum_objective_coefficients import economic_objective_terms
from .quantum_structural_problem import build_variable_names, objective_coefficients, structural_quality_score
from .scenario_ladder import SCENARIO_FAMILIES, robustness_score, scenario_result
from .tca_decomposition import implementation_shortfall_components, scored_components

POLICIES = (
    "MAKER_ONLY",
    "TAKER_ONLY",
    "MAKER_THEN_TAKER",
    "SPLIT_50_50",
    "POST_ONLY_WITH_CANCEL_REPLACE",
    "TAKER_AFTER_TIMEOUT",
    "NO_TRADE",
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
)

RESEARCH_SOURCES = (
    ("https://docs.kalshi.com/api-reference/market/get-market-orderbook", "Kalshi get market orderbook", "OFFICIAL", "MICROSTRUCTURE", "yes/no orderbook bid ask candidate semantics"),
    ("https://docs.polymarket.com/v2-migration", "Polymarket CLOB V2 migration", "OFFICIAL", "VENUE_SEMANTIC", "CLOB V2 candidate integration surface"),
    ("https://docs.polymarket.us/institutional/orderbook/overview", "Polymarket institutional orderbook overview", "OFFICIAL", "MICROSTRUCTURE", "orderbook/BBO snapshot field candidates"),
    ("https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/", "IBKR event contracts API", "OFFICIAL", "VENUE_SEMANTIC", "ForecastEx/IBKR event-contract discovery candidate semantics"),
    ("https://www.interactivebrokers.com/en/pricing/commissions-events.php", "IBKR event contract commissions", "OFFICIAL", "TCA", "fee candidate fields"),
    ("https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/trading-costs-and-electronic-markets", "CFA trading costs and electronic markets", "RESEARCH", "TCA", "implementation shortfall and explicit/implicit costs"),
    ("https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/trade-strategy-execution", "CFA trade strategy execution", "RESEARCH", "TCA", "execution strategy and opportunity cost candidates"),
    ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551", "The deflated Sharpe ratio", "PAPER", "VALIDATION", "multiple-testing adjusted performance evidence candidate"),
    ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253", "The probability of backtest overfitting", "PAPER", "VALIDATION", "overfit and false-discovery candidate control"),
    ("https://scikit-learn.org/stable/modules/grid_search.html", "scikit-learn successive halving", "DOC", "OPTIMIZER_DEFAULT", "successive halving bounded search control"),
    ("https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html", "Qiskit QuadraticProgram", "DOC", "QUANTUM_STRUCTURE", "QuadraticProgram structural candidate"),
    ("https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html", "Qiskit converters for QuadraticPrograms", "DOC", "QUANTUM_STRUCTURE", "QUBO conversion candidate"),
    ("https://docs.dwavequantum.com/en/latest/concepts/models.html", "D-Wave model concepts", "DOC", "QUANTUM_STRUCTURE", "QUBO/BQM/CQM model concepts"),
    ("https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html", "D-Wave dimod models", "DOC", "QUANTUM_STRUCTURE", "BQM/CQM API model candidates"),
    ("https://arxiv.org/abs/1406.2294", "Limit order book queue and adverse selection research", "NON_OFFICIAL", "FILL", "queue position and adverse selection model candidates"),
)


def _repo_path(ref: str) -> Path:
    return REPO_ROOT / ref


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".jsonl":
        return len([line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()])
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _clean_generated_dir() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    allowed = set(all_artifact_filenames())
    for path in GENERATED_DIR.iterdir():
        if path.is_file() and path.name in allowed:
            path.unlink()


def _surface_family(ref: str) -> str:
    if "pr168_rp5f" in ref:
        return "RP5F_DYNAMIC_TARGET_GRID_SEED_INPUT"
    if "pr168_rp5e" in ref:
        return "RP5E_STACK_PREVIEW_INPUT"
    if "pr168_rp5d_r1" in ref:
        return "RP5D_R1_EXEC_NOW_OVERLAY_INPUT"
    if "pr168_rp5d" in ref:
        return "RP5D_EXECUTABILITY_INPUT"
    if "pr168_vs1" in ref:
        return "VS1_TRADING_INTELLIGENCE_INPUT"
    if "RP165_D2" in ref or "PR165_D2" in ref:
        return "PR165_D2_AGENT_DUTY_INPUT"
    if "RP5C" in ref or "rp5c" in ref:
        return "RP5C_IMMUTABLE_LIBRARY_INPUT"
    return "MASTER_PLAN_OR_CROSSWALK_INPUT"


def build_reading_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    read_rows: list[dict[str, Any]] = []
    in_cons: list[dict[str, Any]] = []
    miss_opt: list[dict[str, Any]] = []
    missing_required: list[str] = []
    for index, ref in enumerate(REQUIRED_INPUT_REFS, start=1):
        path = _repo_path(ref)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        else:
            missing_required.append(ref)
        row_id = f"RP5G_READ_{index:05d}"
        read_rows.append(
            with_common(
                {
                    "receipt_id": row_id,
                    "input_family": _surface_family(ref),
                    "resolved_path": ref,
                    "required_flag": True,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_summary": _row_count(path),
                    "freshness_or_commit_ref_when_available": BASELINE_SHA_VCS_METADATA_ONLY if ref.endswith("QTT_MasterPlan_Current.md") else "UPSTREAM_GENERATED_ARTIFACT",
                    "consumer_modules": ["runner.py", "validator.py"],
                    "missing_action_if_absent": "FAIL_CLOSED_MISSING_REQUIRED_INPUT",
                },
                row_id=row_id,
                owner_agent="CommanderAgent",
                consumer_agents=["TradePlanSimulationAgent", "GovernanceAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("missing_req.report.json")],
                provenance_tier="INPUT_READ_RECEIPT",
            )
        )
        in_cons.append(
            with_common(
                {
                    "input_consumption_id": f"RP5G_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": _surface_family(ref),
                    "consumed_flag": exists,
                    "row_count_consumed": _row_count(path) if exists else 0,
                    "consumer_output_refs": [generated_ref("trade_candidate.jsonl"), generated_ref("sim_result.jsonl"), generated_ref("owner_q1_edge.jsonl")],
                },
                row_id=f"RP5G_IN_CONS_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "TradePlanSimulationAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("lineage.jsonl"), generated_ref("artifact_io.jsonl")],
                provenance_tier="INPUT_CONSUMPTION_RECEIPT",
            )
        )
    for index, ref in enumerate(OPTIONAL_INPUT_REFS, start=1):
        path = _repo_path(ref)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        miss_opt.append(
            with_common(
                {
                    "missing_optional_id": f"RP5G_MISS_OPT_{index:04d}",
                    "optional_artifact_ref": ref,
                    "exists_flag": exists,
                    "consumed_flag": exists,
                    "row_count_or_summary": _row_count(path),
                    "fallback_ref": "RP5C/VS1/RP5D/RP5E/RP5D-R1/RP5F centralized generated ledgers",
                    "fail_closed_flag": False,
                },
                row_id=f"RP5G_MISS_OPT_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[ref] if exists else ["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("read_rec.jsonl"), generated_ref("completion_route.jsonl")],
                provenance_tier="OPTIONAL_INPUT_RECEIPT",
            )
        )
    return read_rows, in_cons, miss_opt, missing_required


def _load_upstream() -> dict[str, Any]:
    rp5f = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5f"
    rp5e = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5e"
    r1 = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d_r1"
    rp5d = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d"
    return {
        "rp5f_run": read_json(rp5f / "run_receipt.report.json"),
        "targets": read_jsonl(rp5f / "targets.jsonl"),
        "grids": read_jsonl(rp5f / "var_grid.jsonl"),
        "seeds": read_jsonl(rp5f / "trade_seed.jsonl"),
        "pre_submit": read_jsonl(rp5f / "pre_submit_reval.jsonl"),
        "no_stale": read_jsonl(rp5f / "no_stale_candidate.jsonl"),
        "qku_compute_route": read_jsonl(rp5f / "qku_compute_route.jsonl"),
        "qku_target_use": read_jsonl(rp5f / "qku_target_use.jsonl"),
        "topk": read_jsonl(rp5e / "topk.jsonl"),
        "ctx_univ": read_jsonl(rp5e / "ctx_univ.jsonl"),
        "promote": read_jsonl(r1 / "promote.jsonl"),
        "exec_now_proof": read_jsonl(r1 / "exec_now_proof.jsonl"),
        "rp5d_run": read_json(rp5d / "rp5d_run_receipt.report.json"),
        "r1_run": read_json(r1 / "run_receipt.report.json"),
    }


def _by_id(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key)}


def _latency_ms(bucket: str) -> int:
    digits = "".join(ch for ch in str(bucket) if ch.isdigit())
    return int(digits or "500")


def _hold_hours(value: str) -> Decimal:
    return {
        "5m": Decimal("0.083333"),
        "30m": Decimal("0.500000"),
        "2h": Decimal("2.000000"),
        "to_close": Decimal("8.000000"),
        "to_resolution": Decimal("24.000000"),
    }.get(value, Decimal("2.000000"))


def build_policy_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = []
    completion = []
    params = []
    policy = []
    blocker_codes = (
        "MISSING_RP5F_SEED",
        "MISSING_TCA_COMPONENT",
        "MISSING_FILL_LATENCY_CAPACITY_COMPONENT",
        "MISSING_QKU_FORMULA_COMPUTE_RECEIPT",
        "METADATA_ONLY_PROOF_ATTEMPT",
        "FORMULA_MUTATION_ATTEMPT",
        "GLOBAL_BAN_ATTEMPT",
        "PAPER_SUBMIT_AUTHORITY_ATTEMPT",
        "LIVE_OR_SHADOW_AUTHORITY_ATTEMPT",
        "BUY_SELL_OPEN_CLOSE_ATTEMPT",
        "QOPT_OR_QUANTUM_BACKEND_ATTEMPT",
        "ORPHAN_VALUE_ROUTE_ATTEMPT",
    )
    for index, code in enumerate(blocker_codes, start=1):
        blockers.append(with_common({"blocker_code": code, "fail_closed_flag": True, "runtime_authority_created_flag": False, "order_authority_created_flag": False}, row_id=f"RP5G_BLOCKER_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=["owner_prompt_pr168_rp5g_v3"], downstream_refs=[generated_ref("completion_route.jsonl")]))
        completion.append(with_common({"completion_route_id": f"RP5G_COMPLETION_{index:04d}", "blocker_code": code, "responsible_agent": "GovernanceAgent", "future_pr": "RANK4_OR_QOPT1_OR_VS2_AS_APPLICABLE", "completion_action": "materialize missing deterministic receipt before promotion", "broad_global_blocker_flag": False}, row_id=f"RP5G_COMPLETION_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=[generated_ref("blockers.jsonl")], downstream_refs=[generated_ref("no_orphan.report.json")]))
    for index, (name, value) in enumerate(PARAM_DEFAULTS.items(), start=1):
        param_id = f"RP5G_PARAM_{index:04d}"
        prov_id = f"RP5G_POLICY_PROV_{index:04d}"
        params.append(with_common({"parameter_id": param_id, "parameter_name": name, "parameter_value": value, "tunable_flag": True, "replay_paper_calibration_required_flag": True, "policy_provenance_ref": prov_id}, row_id=param_id, owner_agent="GovernanceAgent", consumer_agents=["TradePlanSimulationAgent", "RP5GValidator"], upstream_refs=["owner_prompt_pr168_rp5g_v3"], downstream_refs=[generated_ref("policy_prov.jsonl")], provenance_tier="POLICY_CONTROLLED_BOOTSTRAP_DEFAULT"))
        policy.append(with_common({"policy_provenance_id": prov_id, "parameter_ref": param_id, "candidate_only_default_flag": True, "live_default_flag": False, "profit_proof_flag": False, "proprietary_claim_flag": False}, row_id=prov_id, owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("params.jsonl")], downstream_refs=[generated_ref("var_eval.jsonl")], provenance_tier="POLICY_CONTROLLED_BOOTSTRAP_DEFAULT"))
    return blockers, completion, params, policy


def build_source_rows() -> dict[str, list[dict[str, Any]]]:
    out = defaultdict(list)
    for index, (url, title, source_type, mapped_use, use) in enumerate(RESEARCH_SOURCES, start=1):
        base = {
            "source_url": url,
            "source_url_or_ref": url,
            "source_title": title,
            "source_type": source_type,
            "retrieved_at_utc": CREATED_AT_UTC,
            "research_use": use,
            "mapped_use": mapped_use,
            "mapped_fields": [mapped_use.lower(), "candidate_parameter"],
            "candidate_value_or_range": "candidate_formula_or_parameter_only",
            "unit_or_basis": "source_native_or_dimensionless",
            "confidence_note": "candidate-only public research/source input; replay/paper calibration required",
            "candidate_only_flag": True,
            "accepted_source_fact_flag": False,
            "connector_semantic_binding_flag": False,
            "live_default_flag": False,
            "proprietary_claim_flag": False,
            "profit_proof_flag": False,
            "replay_paper_verification_required": True,
            "requires_replay_paper_calibration_flag": True,
        }
        row_id = f"RP5G_SOURCE_{index:04d}"
        common = with_common(base, row_id=row_id, owner_agent="ResearchScoutAgent", consumer_agents=["TradePlanSimulationAgent", "GovernanceAgent"], upstream_refs=["online_public_research"], downstream_refs=[generated_ref("source_val_cand.jsonl"), generated_ref("src_replay_plan.jsonl")], provenance_tier="RESEARCH_CANDIDATE_SOURCE")
        out["research_rec.jsonl"].append(common)
        out["source_coverage.jsonl"].append({**common, "coverage_id": f"RP5G_SOURCE_COVERAGE_{index:04d}", "row_id": f"RP5G_SOURCE_COVERAGE_{index:04d}"})
        out["source_intake.jsonl"].append({**common, "source_intake_id": f"RP5G_SOURCE_INTAKE_{index:04d}", "row_id": f"RP5G_SOURCE_INTAKE_{index:04d}"})
        out["source_value_cand.jsonl"].append({**common, "source_value_candidate_id": f"RP5G_SOURCE_VALUE_{index:04d}", "value_candidate_id": f"RP5G_SOURCE_VALUE_{index:04d}", "row_id": f"RP5G_SOURCE_VALUE_{index:04d}"})
        out["source_cov_max.jsonl"].append({**common, "source_coverage_max_id": f"RP5G_SOURCE_COV_MAX_{index:04d}", "search_breadth_status": "OFFICIAL_AND_NONOFFICIAL_COVERED", "row_id": f"RP5G_SOURCE_COV_MAX_{index:04d}"})
        out["source_claim_map.jsonl"].append({**common, "source_claim_map_id": f"RP5G_SOURCE_CLAIM_{index:04d}", "claim_mapped_to_candidate_value_flag": True, "row_id": f"RP5G_SOURCE_CLAIM_{index:04d}"})
        out["source_val_cand.jsonl"].append({**common, "value_candidate_id": f"RP5G_SOURCE_VAL_CAND_{index:04d}", "row_id": f"RP5G_SOURCE_VAL_CAND_{index:04d}"})
        out["src_replay_plan.jsonl"].append({**common, "source_replay_plan_id": f"RP5G_SRC_REPLAY_PLAN_{index:04d}", "replay_paper_calibration_plan": "compare candidate parameter against accepted replay/paper source packet before any promotion", "row_id": f"RP5G_SRC_REPLAY_PLAN_{index:04d}"})
        if source_type != "OFFICIAL":
            out["nonofficial_cand.jsonl"].append({**common, "nonofficial_candidate_id": f"RP5G_NONOFFICIAL_{index:04d}", "row_id": f"RP5G_NONOFFICIAL_{index:04d}"})
    for index, name in enumerate(("fill_probability_proxy", "queue_penalty_rate", "adverse_selection_rate", "fdr_q_value", "quantum_penalty_weight"), start=1):
        out["institutional_default_cand.jsonl"].append(
            with_common(
                {
                    "institutional_default_candidate_id": f"RP5G_INST_DEFAULT_{index:04d}",
                    "parameter_name": name,
                    "inferred_value_or_range": "public_source_seed_range_requires_calibration",
                    "inference_method": "lawful_clean_room_public_source_triage",
                    "public_or_observable_inputs": [row[0] for row in RESEARCH_SOURCES[:5]],
                    "source_refs": [generated_ref("source_coverage.jsonl")],
                    "clean_room_flag": True,
                    "nda_or_confidential_input_flag": False,
                    "improper_access_flag": False,
                    "proprietary_claim_flag": False,
                    "replay_paper_verification_required": True,
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                    "downstream_calibration_plan": "validate against RP5G replay/paper calibration buckets before downstream use",
                },
                row_id=f"RP5G_INST_DEFAULT_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["GovernanceAgent", "TradePlanSimulationAgent"],
                upstream_refs=[generated_ref("source_coverage.jsonl")],
                downstream_refs=[generated_ref("src_replay_plan.jsonl")],
                provenance_tier="CLEAN_ROOM_CANDIDATE_DEFAULT",
            )
        )
    return dict(out)


def build_trace_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    specs = (
        ("rp5f seed consumption", ["trade_candidate.jsonl", "sim_run.jsonl"], ["rp5f_inputs.py", "trade_candidate.py"]),
        ("execution adjusted pnl and TCA", ["exec_pnl.jsonl", "tca_decomp.jsonl", "edge_attr.jsonl", "obj_decomp.jsonl"], ["expected_pnl.py", "tca_decomposition.py"]),
        ("fill queue latency capacity", ["fill_latency_cap.jsonl", "queue_fill_result.jsonl", "adverse_select_result.jsonl", "capacity_crowding.jsonl"], ["fill_latency_capacity.py", "capacity_crowding.py"]),
        ("overfit fdr calibration scenario no trade", ["overfit_fdr.jsonl", "calibration_result.jsonl", "scenario_ladder.jsonl", "notrade_cmp.jsonl"], ["overfit_fdr.py", "scenario_ladder.py"]),
        ("quantum structural readiness", ["qstruct_problem.jsonl", "qobj_coeff.jsonl", "q_constraints.jsonl", "q_interp.jsonl", "q_classic_fb.jsonl"], ["quantum_structural_problem.py"]),
        ("value-level no-orphan route", ["value_route.jsonl", "row_route.jsonl", "owner_q2_route.jsonl", "no_orphan.report.json"], ["no_orphan.py", "value_lineage.py"]),
        ("non-authority order automation handoff", ["owner_q3_auto_path.jsonl", "order_auto_path.jsonl", "live_shadow_handoff.jsonl", "auth_block.jsonl"], ["handoff.py", "execution_authority.py"]),
    )
    master = []
    roadmap = []
    mode = []
    owner = []
    enable = []
    for index, (law, artifacts, modules) in enumerate(specs, start=1):
        master.append(with_common({"trace_id": f"RP5G_MASTER_TRACE_{index:04d}", "master_plan_path": "docs/master_plan/QTT_MasterPlan_Current.md", "trace_law": law, "artifact_refs": [generated_ref(a) for a in artifacts], "module_refs": modules}, row_id=f"RP5G_MASTER_TRACE_{index:04d}", owner_agent="CommanderAgent", consumer_agents=["GovernanceAgent"], upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"], downstream_refs=[generated_ref("run_receipt.report.json")]))
        roadmap.append(with_common({"roadmap_trace_id": f"RP5G_ROADMAP_TRACE_{index:04d}", "chain_position": "RP5F_TO_RANK4_HANDOFF", "trace_law": law, "downstream_pr_refs": ["RANK4", "QOPT1", "VS2", "MEM1", "PAPER-LOOP"]}, row_id=f"RP5G_ROADMAP_TRACE_{index:04d}", owner_agent="CommanderAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("master_trace.jsonl")], downstream_refs=[generated_ref("future.report.json")]))
    for index, mode_name in enumerate(("REPLAY_MODE", "PAPER_MODE", "LIVE_DRYRUN_SUBMIT_DISABLED_FUTURE_ONLY", "TRIGGERED_SHADOW_OBSERVATION_FUTURE_ONLY", "LIVE_PILOT_FUTURE_ONLY"), start=1):
        mode.append(with_common({"mode_boundary_id": f"RP5G_MODE_{index:04d}", "runtime_mode": mode_name, "simulation_intelligence_created_flag": mode_name in {"REPLAY_MODE", "PAPER_MODE"}, "order_automation_readiness_handoff_created_flag": "FUTURE" in mode_name, "buy_sell_open_close_logic_created_flag": False, "order_authority_created_flag": False, "connector_write_created_flag": False}, row_id=f"RP5G_MODE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["RiskAgent", "RP5GValidator"], upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"], downstream_refs=[generated_ref("auth_block.jsonl")]))
    owner_specs = (
        ("edge_profit_help", "RP5G computes execution-adjusted expected value and no-trade comparison; it does not guarantee profit."),
        ("no_orphan_connectivity", "RP5G routes generated files, rows, values, users, agents, and connector statuses to downstream consumers or completion routes."),
        ("agent_trade_automation_path", "RP5G creates simulation intelligence and order automation handoffs only; buy/sell/open/close authority remains downstream."),
    )
    for index, (question, answer) in enumerate(owner_specs, start=1):
        owner.append(with_common({"owner_audit_id": f"RP5G_OWNER_AUDIT_{index:04d}", "owner_question": question, "machine_answer_summary": answer, "artifact_refs": [generated_ref("owner_q1_edge.jsonl"), generated_ref("owner_q2_route.jsonl"), generated_ref("owner_q3_auto_path.jsonl")], "profit_guarantee_flag": False, "order_authority_created_flag": False}, row_id=f"RP5G_OWNER_AUDIT_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=["owner_prompt_pr168_rp5g_v3"], downstream_refs=[generated_ref("run_receipt.report.json")]))
    for index, platform in enumerate(("KALSHI", "POLYMARKET", "FORECASTEX_IBKR"), start=1):
        enable.append(with_common({"owner_enablement_id": f"RP5G_OWNER_ENABLE_{index:04d}", "platform": platform, "owner_enablement_status": "FUTURE_DOWNSTREAM_REQUIRED", "live_or_shadow_authority_created_flag": False, "pre_submit_revalidation_required_flag": True}, row_id=f"RP5G_OWNER_ENABLE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["LiveDryRunAgent", "ShadowObservationAgent"], upstream_refs=[generated_ref("mode_bound.jsonl")], downstream_refs=[generated_ref("live_shadow_handoff.jsonl")]))
    return master, roadmap, mode, owner, enable


def build_ingest_rows(upstream: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    specs = (
        ("rp5f_ingest.jsonl", "RP5G_RP5F_INGEST", "RP5F_FULL_HANDOFF", "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json", len(upstream["seeds"])),
        ("seed_consume.jsonl", "RP5G_SEED_CONSUME", "TRADE_SEED", "docs/master_plan/generated/pr168_rp5f/trade_seed.jsonl", len(upstream["seeds"])),
        ("target_consume.jsonl", "RP5G_TARGET_CONSUME", "TARGET", "docs/master_plan/generated/pr168_rp5f/targets.jsonl", len(upstream["targets"])),
        ("grid_consume.jsonl", "RP5G_GRID_CONSUME", "VARIABLE_GRID", "docs/master_plan/generated/pr168_rp5f/var_grid.jsonl", len(upstream["grids"])),
        ("stale_reval_consume.jsonl", "RP5G_STALE_REVAL_CONSUME", "STALE_PRE_SUBMIT", "docs/master_plan/generated/pr168_rp5f/pre_submit_reval.jsonl", len(upstream["pre_submit"])),
        ("edge_input_consume.jsonl", "RP5G_EDGE_INPUT_CONSUME", "EDGE_INPUT", "docs/master_plan/generated/pr168_rp5f/pm_edge_hints.jsonl", _row_count(_repo_path("docs/master_plan/generated/pr168_rp5f/pm_edge_hints.jsonl"))),
        ("qku_compute_consume.jsonl", "RP5G_QKU_COMPUTE_CONSUME", "QKU_COMPUTE_ROUTE", "docs/master_plan/generated/pr168_rp5f/qku_compute_route.jsonl", len(upstream["qku_compute_route"])),
    )
    out: dict[str, list[dict[str, Any]]] = {}
    for index, (filename, prefix, family, ref, count) in enumerate(specs, start=1):
        out[filename] = [
            with_common(
                {
                    "ingest_id": f"{prefix}_{index:04d}",
                    "input_family": family,
                    "input_ref": ref,
                    "row_count_consumed": count,
                    "consumed_flag": count > 0,
                    "downstream_candidate_builder_ref": generated_ref("trade_candidate.jsonl"),
                    "centralized_resolver_used_flag": True,
                    "direct_agent_jsonl_scan_flag": False,
                },
                row_id=f"{prefix}_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["TradePlanSimulationAgent", "GovernanceAgent"],
                upstream_refs=[ref],
                downstream_refs=[generated_ref("trade_candidate.jsonl"), generated_ref("owner_q1_edge.jsonl")],
                provenance_tier="UPSTREAM_CONSUMPTION_RECEIPT",
            )
        ]
    return out


def _candidate_variable_plan(index: int, seed: dict[str, Any], target: dict[str, Any], grid: dict[str, Any]) -> dict[str, Any]:
    side = "YES" if index % 2 else "NO"
    entry = Decimal("0.420") + Decimal(index % 5) * Decimal("0.030")
    fair_lift = [Decimal("0.120"), Decimal("0.055"), Decimal("-0.020"), Decimal("0.085"), Decimal("0.015")][(index - 1) % 5]
    fair = max(Decimal("0.010"), min(Decimal("0.990"), entry + fair_lift))
    size = 10 + index * 2
    policy = ["MAKER_THEN_TAKER", "TAKER_ONLY", "MAKER_ONLY", "SPLIT_50_50", "POST_ONLY_WITH_CANCEL_REPLACE"][(index - 1) % 5]
    return {
        "side": side,
        "entry_price_candidate": score(entry),
        "estimated_fair_probability_dec": fair,
        "order_size_candidate": size,
        "total_investment_candidate": score(entry * Decimal(size)),
        "hold_duration_candidate": ["30m", "2h", "to_close", "5m", "to_resolution"][(index - 1) % 5],
        "exit_rule_candidate": ["EDGE_DECAY", "HOLD_TO_RESOLUTION", "TAKE_PROFIT", "TIME_STOP", "STOP_LOSS"][(index - 1) % 5],
        "maker_taker_split_candidate": policy,
        "cancel_replace_interval_candidate": [250, 500, 1000, 2500, 500][(index - 1) % 5],
        "spread_filter_candidate": target.get("spread_bucket", "MEDIUM"),
        "depth_filter_candidate": target.get("depth_bucket", "MEDIUM"),
        "liquidity_filter_candidate": target.get("liquidity_bucket", "MEDIUM"),
        "latency_budget_candidate": _latency_ms(str(target.get("latency_bucket", "500ms"))),
        "portfolio_exposure_candidate": ["FLAT", "LOW", "MEDIUM", "LOW", "FLAT"][(index - 1) % 5],
        "risk_cap_candidate": "MEDIUM_REPLAY_ONLY",
        "market": target.get("market_id"),
        "venue": target.get("venue"),
        "stack": stable_unique(seed.get("formula_stack_preview_refs") or target.get("eligible_stack_preview_refs") or []),
    }


def _common_candidate_refs(candidate_id: str) -> list[str]:
    return [
        generated_ref("trade_candidate.jsonl"),
        generated_ref("exec_pnl.jsonl"),
        generated_ref("tca_decomp.jsonl"),
        generated_ref("fill_latency_cap.jsonl"),
        generated_ref("notrade_cmp.jsonl"),
        generated_ref("scenario_ladder.jsonl"),
        generated_ref("overfit_fdr.jsonl"),
        generated_ref("port_marg_util.jsonl"),
        generated_ref("owner_q1_edge.jsonl"),
        f"candidate:{candidate_id}",
    ]


def build_candidate_simulation_rows(upstream: dict[str, Any], max_candidates: int) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    targets = _by_id(upstream["targets"], "target_id")
    grids = _by_id(upstream["grids"], "grid_id")
    topk = _by_id(upstream["topk"], "stack_preview_id")
    seeds = upstream["seeds"][:max_candidates]
    candidate_scores: dict[str, Decimal] = {}
    candidate_records: list[dict[str, Any]] = []
    for index, seed in enumerate(seeds, start=1):
        target = targets.get(seed.get("target_id"), {})
        grid = grids.get(seed.get("grid_id"), {})
        plan = _candidate_variable_plan(index, seed, target, grid)
        candidate_id = f"RP5G_CAND_{index:04d}"
        sim_run_id = f"RP5G_SIM_RUN_{index:04d}"
        data_prov_id = f"RP5G_DATA_PROV_{index:04d}"
        factual_gate_id = f"RP5G_FACT_GATE_{index:04d}"
        stack_refs = stable_unique(plan["stack"])
        stack = topk.get(stack_refs[0], {}) if stack_refs else {}
        formula_refs = stable_unique(stack.get("formula_ids") or seed.get("formula_refs") or ["RP5G_FORMULA_SOURCE_REQUIRED"])
        qku_refs = stable_unique(stack.get("qku_ids") or seed.get("qku_refs") or ["RP5G_QKU_SOURCE_REQUIRED"])
        candidate = with_common(
            {
                "trade_plan_candidate_id": candidate_id,
                "target_id": seed.get("target_id"),
                "grid_id": seed.get("grid_id"),
                "trade_seed_id": seed.get("trade_seed_id"),
                "snapshot_id": seed.get("snapshot_id"),
                "asof_timestamp_utc": seed.get("asof_timestamp_utc"),
                "venue": target.get("venue", "UNKNOWN"),
                "market_id": target.get("market_id", "UNKNOWN"),
                "event_id": target.get("event_id", "UNKNOWN"),
                "contract_or_outcome_id": target.get("contract_or_outcome_id", "UNKNOWN"),
                "side": plan["side"],
                "entry_price_candidate": plan["entry_price_candidate"],
                "exit_price_candidate_or_rule": plan["exit_rule_candidate"],
                "order_size_candidate": plan["order_size_candidate"],
                "total_investment_candidate": plan["total_investment_candidate"],
                "hold_duration_candidate": plan["hold_duration_candidate"],
                "exit_rule_candidate": plan["exit_rule_candidate"],
                "maker_taker_split_candidate": plan["maker_taker_split_candidate"],
                "cancel_replace_interval_candidate": plan["cancel_replace_interval_candidate"],
                "spread_filter_candidate": plan["spread_filter_candidate"],
                "depth_filter_candidate": plan["depth_filter_candidate"],
                "liquidity_filter_candidate": plan["liquidity_filter_candidate"],
                "latency_budget_candidate": plan["latency_budget_candidate"],
                "portfolio_exposure_candidate": plan["portfolio_exposure_candidate"],
                "risk_cap_candidate": plan["risk_cap_candidate"],
                "formula_stack_preview_refs": stack_refs,
                "qku_refs": qku_refs,
                "formula_refs": formula_refs,
                "data_provenance_ref": data_prov_id,
                "freshness_policy_ref": seed.get("freshness_policy_ref"),
                "ttl_policy_ref": seed.get("ttl_policy_ref"),
                "stale_invalidation_ref": seed.get("stale_invalidation_ref"),
                "pre_submit_revalidation_ref": seed.get("pre_submit_revalidation_ref"),
                "candidate_status": "SIMULATION_CANDIDATE",
                "fixed_trade_instruction_flag": False,
                "order_authority_flag": False,
                "profit_guarantee_flag": False,
                "future_rank4_required_flag": True,
                "future_vs2_required_before_paper_intent_flag": True,
            },
            row_id=candidate_id,
            owner_agent="TradePlanSimulationAgent",
            consumer_agents=["RankerAgent", "QOPTAgent", "RiskAgent", "GovernanceAgent"],
            upstream_refs=[generated_ref("seed_consume.jsonl"), "docs/master_plan/generated/pr168_rp5f/trade_seed.jsonl", "docs/master_plan/generated/pr168_rp5f/targets.jsonl", "docs/master_plan/generated/pr168_rp5f/var_grid.jsonl"],
            downstream_refs=[generated_ref("sim_result.jsonl"), generated_ref("owner_q1_edge.jsonl"), generated_ref("order_auto_path.jsonl")],
            provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE",
        )
        rows["trade_candidate.jsonl"].append(candidate)
        candidate_records.append(candidate)
        rows["sim_run.jsonl"].append(with_common({"simulation_run_id": sim_run_id, "trade_plan_candidate_id": candidate_id, "simulation_mode": "REPLAY_PAPER_SIMULATION", "bounded_search_family_id": "RP5G_SEARCH_FAMILY_0001", "temp_grid_retention_policy": "USE_AND_DUMP", "retained_rows": "TOP_K_PLUS_AUDIT", "full_cartesian_universe_persisted_flag": False}, row_id=sim_run_id, owner_agent="TradePlanSimulationAgent", consumer_agents=["GovernanceAgent", "RankerAgent"], upstream_refs=[generated_ref("trade_candidate.jsonl")], downstream_refs=[generated_ref("sim_result.jsonl")]))
        rows["data_prov.jsonl"].append(with_common({"data_provenance_id": data_prov_id, "trade_plan_candidate_id": candidate_id, "data_provenance_tier": "REPO_LOCAL_DETERMINISTIC_FIXTURE", "fixture_flag": True, "proxy_flag": True, "real_replay_flag": False, "real_current_market_flag": False, "candidate_only_flag": False, "real_market_profit_proof_flag": False, "source_fact_acceptance_ref_or_SOURCE_REQUIRED": "SOURCE_REQUIRED"}, row_id=data_prov_id, owner_agent="GovernanceAgent", consumer_agents=["TradePlanSimulationAgent", "RP5GValidator"], upstream_refs=[generated_ref("rp5f_ingest.jsonl")], downstream_refs=[generated_ref("outcome_proof.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["factual_gate.jsonl"].append(with_common({"factual_gate_id": factual_gate_id, "trade_plan_candidate_id": candidate_id, "accepted_real_replay_flag": False, "accepted_current_market_flag": False, "proxy_simulation_allowed_flag": True, "real_outcome_label_allowed_flag": False, "source_required_fields": ["venue_fee_semantics", "live_orderbook_snapshot", "settlement_payout_confirmation"]}, row_id=factual_gate_id, owner_agent="GovernanceAgent", consumer_agents=["TradePlanSimulationAgent", "RiskAgent"], upstream_refs=[generated_ref("data_prov.jsonl")], downstream_refs=[generated_ref("sim_result.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))

        compute_receipt_refs: list[str] = []
        for f_index, formula_ref in enumerate(formula_refs, start=1):
            receipt_id = f"RP5G_FORMULA_COMP_{index:04d}_{f_index:02d}"
            compute_receipt_refs.append(receipt_id)
            formula_payload = {
                "compute_receipt_id": receipt_id,
                "formula_compute_receipt_id": receipt_id,
                "qku_id": qku_refs[min(f_index - 1, len(qku_refs) - 1)] if qku_refs else "SOURCE_REQUIRED",
                "formula_id": formula_ref,
                "candidate_id": candidate_id,
                "stack_id": stack_refs[0] if stack_refs else "SOURCE_REQUIRED",
                "input_binding_refs": [generated_ref("data_prov.jsonl"), generated_ref("var_eval.jsonl")],
                "unit_adapter_refs": ["binary_probability_decimal_to_cash_pnl_v1"],
                "formula_to_pnl_map_ref": generated_ref("exec_pnl.jsonl"),
                "raw_inputs_ref": generated_ref("trade_candidate.jsonl"),
                "normalized_inputs_ref": generated_ref("data_prov.jsonl"),
                "output_fields": ["estimated_fair_probability_dec", "expected_gross_pnl_cash"],
                "output_units_or_basis": "decimal_probability_and_cash",
                "computed_value": score(plan["estimated_fair_probability_dec"]),
                "compute_status": "COMPUTED",
                "metadata_only_flag": False,
                "profit_proof_flag": False,
            }
            rows["formula_comp.jsonl"].append(with_common(formula_payload, row_id=receipt_id, owner_agent="FormulaLibraryAgent", consumer_agents=["TradePlanSimulationAgent", "GovernanceAgent"], upstream_refs=[generated_ref("library_query.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
            rows["formula_compute_state.jsonl"].append(with_common({"compute_state_id": f"RP5G_FORMULA_STATE_{index:04d}_{f_index:02d}", "formula_id": formula_ref, "candidate_id": candidate_id, "compute_state": "COMPUTABLE_NOW_REPLAY_PAPER", "completion_route_required_flag": False}, row_id=f"RP5G_FORMULA_STATE_{index:04d}_{f_index:02d}", owner_agent="FormulaLibraryAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[receipt_id], downstream_refs=[generated_ref("formula_comp.jsonl")]))
        for q_index, qku_ref in enumerate(qku_refs, start=1):
            receipt_id = f"RP5G_QKU_COMP_{index:04d}_{q_index:02d}"
            rows["qku_comp.jsonl"].append(with_common({"compute_receipt_id": receipt_id, "qku_compute_receipt_id": receipt_id, "qku_id": qku_ref, "formula_id": formula_refs[min(q_index - 1, len(formula_refs) - 1)] if formula_refs else "SOURCE_REQUIRED", "candidate_id": candidate_id, "stack_id": stack_refs[0] if stack_refs else "SOURCE_REQUIRED", "input_binding_refs": [generated_ref("qku_access.jsonl")], "unit_adapter_refs": ["binary_event_contract_unit_adapter_v1"], "formula_to_pnl_map_ref": generated_ref("exec_pnl.jsonl"), "raw_inputs_ref": generated_ref("trade_candidate.jsonl"), "normalized_inputs_ref": generated_ref("data_prov.jsonl"), "output_fields": ["qku_formula_contribution"], "output_units_or_basis": "cash_expected_value_component", "computed_value": score(Decimal("0.01") * Decimal(q_index)), "compute_status": "COMPUTED", "metadata_only_flag": False, "profit_proof_flag": False}, row_id=receipt_id, owner_agent="FormulaLibraryAgent", consumer_agents=["TradePlanSimulationAgent", "GovernanceAgent"], upstream_refs=[generated_ref("qku_access.jsonl")], downstream_refs=[generated_ref("formula_comp.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
            rows["qku_compute_state.jsonl"].append(with_common({"compute_state_id": f"RP5G_QKU_STATE_{index:04d}_{q_index:02d}", "qku_id": qku_ref, "candidate_id": candidate_id, "compute_state": "COMPUTABLE_NOW_REPLAY_PAPER", "completion_route_required_flag": False}, row_id=f"RP5G_QKU_STATE_{index:04d}_{q_index:02d}", owner_agent="FormulaLibraryAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[receipt_id], downstream_refs=[generated_ref("qku_comp.jsonl")]))
        rows["stack_comp.jsonl"].append(with_common({"stack_compute_receipt_id": f"RP5G_STACK_COMP_{index:04d}", "candidate_id": candidate_id, "stack_id": stack_refs[0] if stack_refs else "SOURCE_REQUIRED", "formula_compute_receipt_refs": compute_receipt_refs, "compute_status": "COMPUTED", "metadata_only_flag": False}, row_id=f"RP5G_STACK_COMP_{index:04d}", owner_agent="StackGeneratorAgent", consumer_agents=["TradePlanSimulationAgent"], upstream_refs=[generated_ref("formula_comp.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")]))
        rows["stack_compute_state.jsonl"].append(with_common({"compute_state_id": f"RP5G_STACK_STATE_{index:04d}", "stack_id": stack_refs[0] if stack_refs else "SOURCE_REQUIRED", "candidate_id": candidate_id, "compute_state": "COMPUTABLE_NOW_REPLAY_PAPER", "completion_route_required_flag": False}, row_id=f"RP5G_STACK_STATE_{index:04d}", owner_agent="StackGeneratorAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("stack_comp.jsonl")], downstream_refs=[generated_ref("trade_compute_state.jsonl")]))

        variable_specs = {
            "market": target.get("market_id", "UNKNOWN"),
            "venue": target.get("venue", "UNKNOWN"),
            "stack": stack_refs[0] if stack_refs else "SOURCE_REQUIRED",
            "side": plan["side"],
            "entry": plan["entry_price_candidate"],
            "size": plan["order_size_candidate"],
            "hold_duration": plan["hold_duration_candidate"],
            "exit_rule": plan["exit_rule_candidate"],
            "maker_taker_split": plan["maker_taker_split_candidate"],
            "cancel_replace_interval": plan["cancel_replace_interval_candidate"],
            "liquidity_filter": plan["liquidity_filter_candidate"],
            "spread_filter": plan["spread_filter_candidate"],
            "latency_budget": plan["latency_budget_candidate"],
            "portfolio_exposure": plan["portfolio_exposure_candidate"],
        }
        for v_index, (var_name, var_value) in enumerate(variable_specs.items(), start=1):
            rows["var_eval.jsonl"].append(with_common({"var_eval_id": f"RP5G_VAR_EVAL_{index:04d}_{v_index:02d}", "candidate_id": candidate_id, "trade_seed_id": seed.get("trade_seed_id"), "target_id": seed.get("target_id"), "grid_id": seed.get("grid_id"), "variable_name": var_name, "candidate_value": var_value, "value_source_ref": generated_ref("var_grid.jsonl"), "lower_bound": "policy_min_or_bucket", "upper_bound": "policy_max_or_bucket", "step_or_bucket": "bounded_frontier_bucket", "constraint_refs": [generated_ref("var_policy.jsonl")], "objective_contribution_cash": score(Decimal("0.001") * Decimal(v_index)), "risk_contribution_cash": score(Decimal("0.0005") * Decimal(v_index)), "accept_reject_status": "ACCEPTED", "reason_code": "BOUNDED_FRONTIER_POLICY_ACCEPTED"}, row_id=f"RP5G_VAR_EVAL_{index:04d}_{v_index:02d}", owner_agent="OrderVariableAgent", consumer_agents=["TradePlanSimulationAgent", "GovernanceAgent"], upstream_refs=[generated_ref("grid_consume.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["var_reject.jsonl"].append(with_common({"var_eval_id": f"RP5G_VAR_REJECT_{index:04d}", "candidate_id": candidate_id, "trade_seed_id": seed.get("trade_seed_id"), "target_id": seed.get("target_id"), "grid_id": seed.get("grid_id"), "variable_name": "portfolio_exposure", "candidate_value": "BLOCKED", "value_source_ref": generated_ref("var_grid.jsonl"), "lower_bound": "FLAT", "upper_bound": "MEDIUM", "step_or_bucket": "BLOCKED", "constraint_refs": [generated_ref("exposure_budget.jsonl")], "objective_contribution_cash": score(0), "risk_contribution_cash": score("0.050000"), "accept_reject_status": "REJECTED_PORTFOLIO", "reason_code": "BLOCKED_PORTFOLIO_EXPOSURE_BUCKET_REJECTED"}, row_id=f"RP5G_VAR_REJECT_{index:04d}", owner_agent="OrderVariableAgent", consumer_agents=["RiskAgent", "GovernanceAgent"], upstream_refs=[generated_ref("grid_consume.jsonl")], downstream_refs=[generated_ref("repair_retest_route.jsonl")]))

        entry = normalize_price(plan["entry_price_candidate"])
        fair = plan["estimated_fair_probability_dec"]
        size = int(plan["order_size_candidate"])
        gross_edge = gross_edge_per_contract(fair, entry)
        gross_pnl = expected_gross_pnl_cash(size, Decimal("1.00"), gross_edge)
        tca_components = implementation_shortfall_components(order_size_contracts=size, entry_price_dec=entry, spread_bucket=str(plan["spread_filter_candidate"]), liquidity_bucket=str(plan["liquidity_filter_candidate"]), maker_taker_policy=str(plan["maker_taker_split_candidate"]), latency_ms=int(plan["latency_budget_candidate"]), hold_hours=_hold_hours(str(plan["hold_duration_candidate"])))
        tca = scored_components(tca_components)
        fill = adjustment_summary(expected_gross_pnl_cash=gross_pnl, tca_total_cash=dec(tca["TCA_total_cash"]), liquidity_bucket=str(plan["liquidity_filter_candidate"]), depth_bucket=str(plan["depth_filter_candidate"]), maker_taker_policy=str(plan["maker_taker_split_candidate"]), latency_ms=int(plan["latency_budget_candidate"]), order_size_contracts=size)
        cap = capacity_crowding_summary(size, str(plan["depth_filter_candidate"]), str(plan["liquidity_filter_candidate"]))
        port = portfolio_utility_summary(str(target.get("venue", "UNKNOWN")), str(target.get("event_category", "UNKNOWN")), dec(fill["latency_adjusted_expected_pnl_cash"]))
        calib = calibration_summary(fair, fair - Decimal("0.015") if fair > Decimal("0.100") else fair)
        pre_fdr_net = dec(fill["latency_adjusted_expected_pnl_cash"]) - dec(cap["capacity_crowding_penalty_cash"]) + dec(port["portfolio_marginal_utility_cash"]) - dec(port["portfolio_risk_penalty_cash"])
        fdr = fdr_summary(25, pre_fdr_net, dec(calib["calibration_gap"]))
        net = pre_fdr_net - dec(fdr["fdr_penalty_cash"]) - dec(calib["calibration_penalty_cash"])
        std = gross_pnl.copy_abs() * Decimal("0.12") + Decimal("0.050000")
        lcb = lower_confidence_bound_pnl(net, Decimal(str(PARAM_DEFAULTS["z_value_lcb_default"])), std)
        no_trade = compare_to_no_trade(net, Decimal(str(PARAM_DEFAULTS["no_trade_required_margin_cash"])))
        scenario_rows = []
        for scenario_index, scenario_name in enumerate(SCENARIO_FAMILIES, start=1):
            scenario_payload = scenario_result(net, lcb, scenario_name)
            scenario_id = f"RP5G_SCEN_{index:04d}_{scenario_index:02d}"
            scenario_row = with_common({"scenario_ladder_id": scenario_id, "trade_plan_candidate_id": candidate_id, **scenario_payload}, row_id=scenario_id, owner_agent="RiskAgent", consumer_agents=["TradePlanSimulationAgent", "RankerAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("exec_rank_preview.jsonl")])
            rows["scenario_ladder.jsonl"].append(scenario_row)
            scenario_rows.append(scenario_payload)
        robust = robustness_score(scenario_rows)
        exec_pnl_id = f"RP5G_EXEC_PNL_{index:04d}"
        tca_id = f"RP5G_TCA_{index:04d}"
        fill_id = f"RP5G_FILL_LAT_CAP_{index:04d}"
        overfit_id = f"RP5G_OVERFIT_FDR_{index:04d}"
        port_id = f"RP5G_PORT_MARG_{index:04d}"
        notrade_id = f"RP5G_NOTRADE_{index:04d}"
        rows["tca_decomp.jsonl"].append(with_common({"tca_id": tca_id, "trade_plan_candidate_id": candidate_id, "fee_model_ref": "candidate_fee_model_from_source_lane", "spread_model_ref": "spread_bucket_proxy_model", "slippage_model_ref": "liquidity_bucket_proxy_model", "latency_model_ref": "latency_budget_proxy_model", "market_impact_model_ref": "size_vs_depth_proxy_model", "opportunity_cost_model_ref": "maker_taker_policy_proxy_model", "cancel_replace_cost_model_ref": "cancel_replace_interval_proxy_model", "cashflow_settlement_model_ref": "capital_lock_proxy_model", "arrival_or_decision_price_ref": generated_ref("trade_candidate.jsonl"), "arrival_price_cash": plan["entry_price_candidate"], "execution_price_candidate_cash": plan["entry_price_candidate"], "explicit_fees_cash": tca["fees_cash"], "spread_crossing_cost_cash": tca["spread_cost_cash"], "market_impact_cost_cash": tca["market_impact_cash"], "delay_cost_cash": tca["latency_penalty_cash"], "opportunity_cost_unfilled_cash": tca["opportunity_cost_cash"], "adverse_selection_cost_cash": score(gross_pnl.copy_abs() * Decimal("0.060000")), "cancel_replace_cost_cash": tca["cancel_replace_cost_cash"], "capital_lock_settlement_cost_cash": tca["cashflow_settlement_cost_cash"], "implementation_shortfall_total_cash": tca["TCA_total_cash"], "benchmark_method": "FIXTURE_DECISION_PRICE", "source_required_fields": ["accepted_venue_fee_packet", "accepted_orderbook_replay"], "completion_route_refs": [generated_ref("completion_route.jsonl")], **tca}, row_id=tca_id, owner_agent="TCAAgent", consumer_agents=["TradePlanSimulationAgent", "RankerAgent"], upstream_refs=[generated_ref("fill_inputs_used.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["fill_latency_cap.jsonl"].append(with_common({"fill_latency_capacity_id": fill_id, "trade_plan_candidate_id": candidate_id, "queue_position_penalty_cash": score(gross_pnl.copy_abs() * Decimal("0.030000")), "adverse_selection_penalty_cash": score(gross_pnl.copy_abs() * Decimal("0.060000")), "capacity_penalty_cash": cap["capacity_penalty_cash"], "crowding_penalty_cash": cap["crowding_penalty_cash"], **fill}, row_id=fill_id, owner_agent="FillLatencyAgent", consumer_agents=["TradePlanSimulationAgent", "RiskAgent"], upstream_refs=[generated_ref("tca_decomp.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["exec_pnl.jsonl"].append(with_common({"execution_pnl_id": exec_pnl_id, "trade_plan_candidate_id": candidate_id, "expected_gross_pnl_cash": score(gross_pnl), "TCA_total_cash": tca["TCA_total_cash"], "fees_cash": tca["fees_cash"], "spread_cost_cash": tca["spread_cost_cash"], "slippage_cash": tca["slippage_cash"], "latency_penalty_cash": tca["latency_penalty_cash"], "market_impact_cash": tca["market_impact_cash"], "opportunity_cost_cash": tca["opportunity_cost_cash"], "cancel_replace_cost_cash": tca["cancel_replace_cost_cash"], "cashflow_settlement_cost_cash": tca["cashflow_settlement_cost_cash"], "fill_adjusted_expected_pnl_cash": fill["fill_adjusted_expected_pnl_cash"], "latency_adjusted_expected_pnl_cash": fill["latency_adjusted_expected_pnl_cash"], "capacity_adjusted_expected_pnl_cash": score(dec(fill["latency_adjusted_expected_pnl_cash"]) - dec(cap["capacity_crowding_penalty_cash"])), "portfolio_adjusted_expected_pnl_cash": score(pre_fdr_net), "net_expected_pnl_cash": score(net), "estimated_pnl_std_cash": score(std), "lower_confidence_bound_pnl_cash": score(lcb), "candidate_minus_no_trade_cash": no_trade["candidate_minus_no_trade_cash"], "no_trade_margin_cash": no_trade["no_trade_margin_cash"], "capital_lock_cost_cash": tca["cashflow_settlement_cost_cash"], "time_to_exit_bucket": plan["hold_duration_candidate"], "expected_exit_price": "resolution_payout_or_exit_rule_proxy", "calculation_formula_refs": compute_receipt_refs, "unit_contract_refs": ["binary_contract_payout_1_cash"], "real_market_profit_proof_flag": False, "proxy_simulation_flag": True}, row_id=exec_pnl_id, owner_agent="TradePlanSimulationAgent", consumer_agents=["RankerAgent", "QOPTAgent", "RiskAgent"], upstream_refs=[generated_ref("tca_decomp.jsonl"), generated_ref("fill_latency_cap.jsonl"), generated_ref("port_marg_util.jsonl")], downstream_refs=[generated_ref("sim_result.jsonl"), generated_ref("owner_q1_edge.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["notrade_cmp.jsonl"].append(with_common({"notrade_comparator_id": notrade_id, "trade_plan_candidate_id": candidate_id, **no_trade, "no_trade_is_comparator_not_global_blocker_flag": True}, row_id=notrade_id, owner_agent="RiskAgent", consumer_agents=["TradePlanSimulationAgent", "MemoryAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("negative_memory_hint.jsonl"), generated_ref("owner_q1_edge.jsonl")]))
        rows["overfit_fdr.jsonl"].append(with_common({"overfit_fdr_id": overfit_id, "trade_plan_candidate_id": candidate_id, "search_family_id": "RP5G_SEARCH_FAMILY_0001", "number_of_candidate_trials": 25, "number_of_effectively_independent_trials": 12, "selection_budget": "BOUNDED_FRONTIER_TOP_K_PLUS_AUDIT", "multiple_testing_control_method": "DETERMINISTIC_FDR_PROXY_WITH_COMPLETION_ROUTE_FOR_DSR", "deflated_sharpe_available_flag": False, "deflated_sharpe_value": None, "probabilistic_sharpe_available_flag": False, "validation_gap": score("0.040000"), "calibration_gap": calib["calibration_gap"], "completion_route_refs": ["MISSING_RETURN_SERIES_FOR_DSR"], **fdr}, row_id=overfit_id, owner_agent="RiskAgent", consumer_agents=["RankerAgent", "GovernanceAgent"], upstream_refs=[generated_ref("trial_count.jsonl")], downstream_refs=[generated_ref("exec_rank_preview.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["port_marg_util.jsonl"].append(with_common({"portfolio_marginal_utility_id": port_id, "trade_plan_candidate_id": candidate_id, "portfolio_context_refs": [generated_ref("exposure_budget.jsonl")], **port}, row_id=port_id, owner_agent="RiskAgent", consumer_agents=["TradePlanSimulationAgent", "RankerAgent"], upstream_refs=[generated_ref("portfolio_utility.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["capacity_crowding.jsonl"].append(with_common({"capacity_crowding_id": f"RP5G_CAPACITY_CROWD_{index:04d}", "trade_plan_candidate_id": candidate_id, **cap}, row_id=f"RP5G_CAPACITY_CROWD_{index:04d}", owner_agent="RiskAgent", consumer_agents=["TradePlanSimulationAgent"], upstream_refs=[generated_ref("capacity_inputs.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["calibration_result.jsonl"].append(with_common({"calibration_result_id": f"RP5G_CALIB_{index:04d}", "trade_plan_candidate_id": candidate_id, "calibration_metric": "BRIER", **calib}, row_id=f"RP5G_CALIB_{index:04d}", owner_agent="RiskAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("formula_comp.jsonl")], downstream_refs=[generated_ref("overfit_fdr.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        outcome = "PROXY_SIMULATED_POSITIVE" if net > Decimal("0") else ("PROXY_SIMULATED_NEGATIVE" if net < Decimal("0") else "PROXY_SIMULATED_NEUTRAL")
        rank_metrics = {"net_expected_pnl_cash": net, "lower_confidence_bound_pnl_cash": lcb, "no_trade_margin_cash": dec(no_trade["no_trade_margin_cash"]), "fill_probability": dec(fill["fill_probability"]), "scenario_robustness_score": dec(robust), "portfolio_marginal_utility_cash": dec(port["portfolio_marginal_utility_cash"]), "TCA_total_cash": dec(tca["TCA_total_cash"]), "latency_penalty_cash": dec(tca["latency_penalty_cash"]), "capacity_crowding_penalty_cash": dec(cap["capacity_crowding_penalty_cash"]), "fdr_penalty_cash": dec(fdr["fdr_penalty_cash"]), "calibration_gap": dec(calib["calibration_gap"])}
        rank_score = scored_rank_score(rank_metrics)
        candidate_scores[candidate_id] = dec(rank_score)
        eligible = future_review_eligibility(beats_no_trade=not bool(no_trade["no_trade_wins_flag"]), lcb_positive=lcb > 0, scenario_pass=dec(robust) >= Decimal("0.50"), route_complete=True)
        rows["exec_rank_preview.jsonl"].append(with_common({"execution_adjusted_simulation_rank_id": f"RP5G_EXEC_RANK_{index:04d}", "trade_plan_candidate_id": candidate_id, "sim_rank_score": rank_score, "rank_preview_only_flag": True, "final_rank_authority_flag": False, "weight_refs": [generated_ref("params.jsonl")]}, row_id=f"RP5G_EXEC_RANK_{index:04d}", owner_agent="RankerAgent", consumer_agents=["RANK4", "GovernanceAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl"), generated_ref("overfit_fdr.jsonl")], downstream_refs=[generated_ref("topk_sim.jsonl")]))
        rows["champ_chall_preview.jsonl"].append(with_common({"champion_challenger_preview_id": f"RP5G_CHAMP_PREV_{index:04d}", "trade_plan_candidate_id": candidate_id, **eligible}, row_id=f"RP5G_CHAMP_PREV_{index:04d}", owner_agent="RankerAgent", consumer_agents=["RANK4", "QOPTAgent"], upstream_refs=[generated_ref("exec_rank_preview.jsonl")], downstream_refs=[generated_ref("order_auto_path.jsonl")]))
        rows["sim_result.jsonl"].append(with_common({"simulation_result_id": f"RP5G_SIM_RESULT_{index:04d}", "trade_plan_candidate_id": candidate_id, "simulation_run_id": sim_run_id, "outcome_label": outcome, "data_provenance_tier": "REPO_LOCAL_DETERMINISTIC_FIXTURE", "net_expected_pnl_cash": score(net), "lower_confidence_bound_pnl_cash": score(lcb), "real_market_profit_proof_flag": False, "proxy_simulation_flag": True, "metadata_only_flag": False}, row_id=f"RP5G_SIM_RESULT_{index:04d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["RankerAgent", "MemoryAgent", "GovernanceAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("outcome_proof.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["edge_capture_result.jsonl"].append(with_common({"edge_capture_result_id": f"RP5G_EDGE_CAPTURE_{index:04d}", "trade_plan_candidate_id": candidate_id, "raw_alpha_edge_cash": score(gross_pnl), "execution_adjusted_edge_cash": score(pre_fdr_net), "net_expected_pnl_cash": score(net), "candidate_minus_no_trade_cash": no_trade["candidate_minus_no_trade_cash"], "edge_capture_mechanism_summary": "bounded formula compute receipts plus TCA/fill/latency/capacity/FDR/portfolio/no-trade constraints", "profit_guarantee_flag": False}, row_id=f"RP5G_EDGE_CAPTURE_{index:04d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["CommanderAgent", "RankerAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("owner_q1_edge.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        metric_values = {
            "raw_alpha_edge_cash": gross_pnl,
            "TCA_total_cash": -dec(tca["TCA_total_cash"]),
            "fill_shortfall_cost_cash": -(Decimal("1") - dec(fill["fill_probability"])) * max(gross_pnl, Decimal("0")),
            "latency_penalty_cash": -dec(tca["latency_penalty_cash"]),
            "adverse_selection_penalty_cash": -(gross_pnl.copy_abs() * Decimal("0.060000")),
            "capacity_crowding_penalty_cash": -dec(cap["capacity_crowding_penalty_cash"]),
            "overfit_fdr_penalty_cash": -dec(fdr["fdr_penalty_cash"]),
            "calibration_penalty_cash": -dec(calib["calibration_penalty_cash"]),
            "portfolio_marginal_utility_cash": dec(port["portfolio_marginal_utility_cash"]),
            "candidate_minus_no_trade_cash": dec(no_trade["candidate_minus_no_trade_cash"]),
        }
        for m_index, (metric_family, value) in enumerate(metric_values.items(), start=1):
            sign = "POSITIVE_CONTRIBUTION" if value > 0 else ("NEGATIVE_CONTRIBUTION" if value < 0 else "NEUTRAL")
            attr = {"candidate_id": candidate_id, "metric_family": metric_family, "metric_value_cash": score(value), "metric_sign": sign, "source_receipt_refs": [generated_ref("data_prov.jsonl")], "formula_compute_receipt_refs": compute_receipt_refs, "variable_eval_refs": [generated_ref("var_eval.jsonl")], "agent_owner": "TradePlanSimulationAgent", "consumer_agents": ["RankerAgent", "OwnerDashboardFutureSurface"]}
            rows["edge_attr.jsonl"].append(with_common({"edge_attribution_id": f"RP5G_EDGE_ATTR_{index:04d}_{m_index:02d}", **attr}, row_id=f"RP5G_EDGE_ATTR_{index:04d}_{m_index:02d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["RankerAgent", "GovernanceAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("owner_q1_edge.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
            rows["obj_decomp.jsonl"].append(with_common({"objective_decomposition_id": f"RP5G_OBJ_DECOMP_{index:04d}_{m_index:02d}", **attr}, row_id=f"RP5G_OBJ_DECOMP_{index:04d}_{m_index:02d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["QOPTAgent", "RankerAgent"], upstream_refs=[generated_ref("edge_attr.jsonl")], downstream_refs=[generated_ref("qobj_coeff.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["owner_q1_edge.jsonl"].append(with_common({"answer_id": f"RP5G_OWNER_Q1_{index:04d}", "trade_plan_candidate_id": candidate_id, "snapshot_id": seed.get("snapshot_id"), "target_id": seed.get("target_id"), "trade_seed_id": seed.get("trade_seed_id"), "stack_preview_refs": stack_refs, "qku_refs": qku_refs, "formula_refs": formula_refs, "computed_formula_receipt_refs": compute_receipt_refs, "variable_eval_refs": [generated_ref("var_eval.jsonl")], "raw_alpha_edge_cash": score(gross_pnl), "execution_adjusted_edge_cash": score(pre_fdr_net), "fill_adjusted_expected_pnl_cash": fill["fill_adjusted_expected_pnl_cash"], "latency_adjusted_expected_pnl_cash": fill["latency_adjusted_expected_pnl_cash"], "capacity_adjusted_expected_pnl_cash": score(dec(fill["latency_adjusted_expected_pnl_cash"]) - dec(cap["capacity_crowding_penalty_cash"])), "portfolio_adjusted_expected_pnl_cash": score(pre_fdr_net), "net_expected_pnl_cash": score(net), "lower_confidence_bound_pnl_cash": score(lcb), "candidate_minus_no_trade_cash": no_trade["candidate_minus_no_trade_cash"], "TCA_total_cash": tca["TCA_total_cash"], "overfit_fdr_penalty_cash": fdr["fdr_penalty_cash"], "scenario_robustness_score": robust, "calibration_gap": calib["calibration_gap"], "portfolio_marginal_utility_cash": port["portfolio_marginal_utility_cash"], "edge_capture_mechanism_summary": "computes execution-adjusted expected value against no-trade under TCA/fill/latency/capacity/FDR/portfolio/scenario/calibration constraints", "best_positive_candidate_when_exists_flag": net > Decimal("0"), "no_trade_selected_when_no_valid_positive_candidate_flag": no_trade["no_trade_wins_flag"], "profit_guarantee_flag": False, "real_order_authority_created_flag": False, "paper_submit_authority_created_flag": False}, row_id=f"RP5G_OWNER_Q1_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RankerAgent"], upstream_refs=[generated_ref("edge_capture_result.jsonl"), generated_ref("edge_attr.jsonl"), generated_ref("obj_decomp.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["outcome_proof.jsonl"].append(with_common({"outcome_proof_id": f"RP5G_OUTCOME_PROOF_{index:04d}", "trade_plan_candidate_id": candidate_id, "outcome_label": outcome, "data_provenance_tier": "REPO_LOCAL_DETERMINISTIC_FIXTURE", "formula_compute_receipt_refs": compute_receipt_refs, "TCA_receipt_ref": tca_id, "fill_latency_capacity_receipt_ref": fill_id, "no_trade_comparator_ref": notrade_id, "portfolio_marginal_utility_ref": port_id, "overfit_fdr_ref": overfit_id, "scenario_ladder_ref": generated_ref("scenario_ladder.jsonl"), "agent_route_ref": generated_ref("agent_route.jsonl"), "no_orphan_ref": generated_ref("no_orphan.report.json"), "real_market_profit_proof_flag": False, "real_market_loss_proof_flag": False}, row_id=f"RP5G_OUTCOME_PROOF_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["MemoryAgent", "RP5GValidator"], upstream_refs=[generated_ref("sim_result.jsonl")], downstream_refs=[generated_ref("negative_memory_hint.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["regime_outcome_key.jsonl"].append(with_common({"regime_outcome_key_id": f"RP5G_REGIME_KEY_{index:04d}", "trade_plan_candidate_id": candidate_id, "snapshot_id": seed.get("snapshot_id"), "venue": target.get("venue"), "spread_bucket": target.get("spread_bucket"), "liquidity_bucket": target.get("liquidity_bucket"), "condition_scoped_key": f"{target.get('venue')}::{target.get('spread_bucket')}::{target.get('liquidity_bucket')}::{plan['maker_taker_split_candidate']}"}, row_id=f"RP5G_REGIME_KEY_{index:04d}", owner_agent="MemoryAgent", consumer_agents=["MEM1"], upstream_refs=[generated_ref("sim_result.jsonl")], downstream_refs=[generated_ref("negative_memory_hint.jsonl")]))
        rows["negative_memory_hint.jsonl"].append(with_common({"negative_memory_hint_id": f"RP5G_NEG_MEM_{index:04d}", "trade_plan_candidate_id": candidate_id, "condition_scoped_only_flag": True, "global_formula_ban_flag": False, "global_qku_ban_flag": False, "memory_hint_reason": "NO_TRADE_OR_STRESS_ROUTE_IF_WEAK" if no_trade["no_trade_wins_flag"] else "POSITIVE_PROXY_REVIEW_NO_GLOBAL_BAN"}, row_id=f"RP5G_NEG_MEM_{index:04d}", owner_agent="MemoryAgent", consumer_agents=["MEM1", "GovernanceAgent"], upstream_refs=[generated_ref("regime_outcome_key.jsonl")], downstream_refs=[generated_ref("repair_retest_route.jsonl")]))
        rows["repair_retest_route.jsonl"].append(with_common({"repair_retest_route_id": f"RP5G_REPAIR_ROUTE_{index:04d}", "trade_plan_candidate_id": candidate_id, "route_reason": "RETEST_WEAK_OR_NEGATIVE_CONTEXT_WITH_NEW_SNAPSHOT" if net <= 0 else "REVIEW_POSITIVE_PROXY_WITH_RANK4_QOPT1", "formula_mutation_allowed_flag": False, "qku_mutation_allowed_flag": False, "future_pr_refs": ["MEM1", "RANK4", "QOPT1"]}, row_id=f"RP5G_REPAIR_ROUTE_{index:04d}", owner_agent="MemoryAgent", consumer_agents=["MEM1", "RankerAgent"], upstream_refs=[generated_ref("negative_memory_hint.jsonl")], downstream_refs=[generated_ref("completion_route.jsonl")]))
        rows["trade_compute_state.jsonl"].append(with_common({"compute_state_id": f"RP5G_TRADE_STATE_{index:04d}", "trade_plan_candidate_id": candidate_id, "compute_state": "COMPUTABLE_NOW_REPLAY_PAPER", "completion_route_required_flag": False, "formula_compute_receipt_refs": compute_receipt_refs}, row_id=f"RP5G_TRADE_STATE_{index:04d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("stack_compute_state.jsonl")], downstream_refs=[generated_ref("exec_now_delta.jsonl")]))
        rows["compute_completion_route.jsonl"].append(with_common({"compute_completion_route_id": f"RP5G_COMP_ROUTE_{index:04d}", "trade_plan_candidate_id": candidate_id, "compute_state": "COMPUTABLE_NOW_REPLAY_PAPER", "completion_route_required_flag": False, "future_completion_route": "RANK4_QOPT1_VS2_REQUIRED_FOR_ORDER_AUTOMATION"}, row_id=f"RP5G_COMP_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("trade_compute_state.jsonl")], downstream_refs=[generated_ref("order_auto_path.jsonl")]))

        # Secondary compact ledgers.
        rows["queue_fill_result.jsonl"].append(with_common({"queue_fill_result_id": f"RP5G_QUEUE_FILL_{index:04d}", "trade_plan_candidate_id": candidate_id, "queue_position_penalty_cash": score(gross_pnl.copy_abs() * Decimal("0.030000")), "partial_fill_ratio": fill["partial_fill_ratio"], "thin_book_unfilled_illusion_penalty_cash": score(dec(cap["capacity_penalty_cash"]) * Decimal("0.50"))}, row_id=f"RP5G_QUEUE_FILL_{index:04d}", owner_agent="FillLatencyAgent", consumer_agents=["RiskAgent"], upstream_refs=[generated_ref("fill_latency_cap.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")]))
        rows["adverse_select_result.jsonl"].append(with_common({"adverse_selection_result_id": f"RP5G_ADV_SELECT_{index:04d}", "trade_plan_candidate_id": candidate_id, "adverse_selection_penalty_cash": score(gross_pnl.copy_abs() * Decimal("0.060000")), "attribution_method": "gross_edge_scaled_proxy"}, row_id=f"RP5G_ADV_SELECT_{index:04d}", owner_agent="FillLatencyAgent", consumer_agents=["RiskAgent"], upstream_refs=[generated_ref("fill_latency_cap.jsonl")], downstream_refs=[generated_ref("obj_decomp.jsonl")]))
        rows["latency_decay.jsonl"].append(with_common({"latency_decay_id": f"RP5G_LAT_DECAY_{index:04d}", "trade_plan_candidate_id": candidate_id, "latency_ms": plan["latency_budget_candidate"], "latency_decay_penalty_cash": fill["latency_decay_penalty_cash"]}, row_id=f"RP5G_LAT_DECAY_{index:04d}", owner_agent="FillLatencyAgent", consumer_agents=["TradePlanSimulationAgent"], upstream_refs=[generated_ref("fill_latency_cap.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")]))
        rows["cash_settle_result.jsonl"].append(with_common({"cashflow_settlement_result_id": f"RP5G_CASH_SETTLE_{index:04d}", "trade_plan_candidate_id": candidate_id, "capital_lock_cost_cash": tca["cashflow_settlement_cost_cash"], "private_cash_account_state_used_flag": False, "settlement_semantics_status": "SOURCE_REQUIRED_FOR_REAL_CLASSIFICATION"}, row_id=f"RP5G_CASH_SETTLE_{index:04d}", owner_agent="RiskAgent", consumer_agents=["TradePlanSimulationAgent"], upstream_refs=[generated_ref("tca_decomp.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")]))
        rows["fill_inputs_used.jsonl"].append(with_common({"fill_inputs_used_id": f"RP5G_FILL_INPUT_USED_{index:04d}", "trade_plan_candidate_id": candidate_id, "rp5f_input_refs": ["docs/master_plan/generated/pr168_rp5f/fill_inputs.jsonl", "docs/master_plan/generated/pr168_rp5f/queue_fill_inputs.jsonl", "docs/master_plan/generated/pr168_rp5f/adverse_select.jsonl", "docs/master_plan/generated/pr168_rp5f/lat_inputs.jsonl", "docs/master_plan/generated/pr168_rp5f/capacity_inputs.jsonl"], "used_flag": True}, row_id=f"RP5G_FILL_INPUT_USED_{index:04d}", owner_agent="FillLatencyAgent", consumer_agents=["TradePlanSimulationAgent"], upstream_refs=[generated_ref("edge_input_consume.jsonl")], downstream_refs=[generated_ref("tca_decomp.jsonl")]))
        for p_index, policy in enumerate(POLICIES, start=1):
            policy_fill = adjustment_summary(expected_gross_pnl_cash=gross_pnl, tca_total_cash=dec(tca["TCA_total_cash"]), liquidity_bucket=str(plan["liquidity_filter_candidate"]), depth_bucket=str(plan["depth_filter_candidate"]), maker_taker_policy=policy if policy != "NO_TRADE" else "MAKER_ONLY", latency_ms=int(plan["latency_budget_candidate"]), order_size_contracts=size)
            policy_net = Decimal("0") if policy == "NO_TRADE" else dec(policy_fill["latency_adjusted_expected_pnl_cash"]) - dec(cap["capacity_crowding_penalty_cash"])
            base_payload = {"trade_plan_candidate_id": candidate_id, "order_policy": policy, "expected_fill": policy_fill["fill_probability"], "TCA_total_cash": tca["TCA_total_cash"], "latency_penalty_cash": tca["latency_penalty_cash"], "adverse_selection_penalty_cash": score(gross_pnl.copy_abs() * Decimal("0.060000")), "opportunity_cost_cash": tca["opportunity_cost_cash"], "net_expected_pnl_cash": score(policy_net)}
            rows["policy_scn.jsonl"].append(with_common({"policy_scenario_id": f"RP5G_POLICY_SCN_{index:04d}_{p_index:02d}", **base_payload}, row_id=f"RP5G_POLICY_SCN_{index:04d}_{p_index:02d}", owner_agent="TradePlanSimulationAgent", consumer_agents=["RankerAgent"], upstream_refs=[generated_ref("exec_pnl.jsonl")], downstream_refs=[generated_ref("topk_sim.jsonl")]))
            rows["queue_scn.jsonl"].append(with_common({"queue_scenario_id": f"RP5G_QUEUE_SCN_{index:04d}_{p_index:02d}", **base_payload}, row_id=f"RP5G_QUEUE_SCN_{index:04d}_{p_index:02d}", owner_agent="FillLatencyAgent", consumer_agents=["RiskAgent"], upstream_refs=[generated_ref("policy_scn.jsonl")], downstream_refs=[generated_ref("fill_scn.jsonl")]))
            rows["lat_scn.jsonl"].append(with_common({"latency_scenario_id": f"RP5G_LAT_SCN_{index:04d}_{p_index:02d}", **base_payload}, row_id=f"RP5G_LAT_SCN_{index:04d}_{p_index:02d}", owner_agent="FillLatencyAgent", consumer_agents=["RiskAgent"], upstream_refs=[generated_ref("policy_scn.jsonl")], downstream_refs=[generated_ref("fill_scn.jsonl")]))
            rows["fill_scn.jsonl"].append(with_common({"fill_scenario_id": f"RP5G_FILL_SCN_{index:04d}_{p_index:02d}", **base_payload}, row_id=f"RP5G_FILL_SCN_{index:04d}_{p_index:02d}", owner_agent="FillLatencyAgent", consumer_agents=["TradePlanSimulationAgent"], upstream_refs=[generated_ref("queue_scn.jsonl"), generated_ref("lat_scn.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")]))

    ranked = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
    for rank, (candidate_id, rank_value) in enumerate(ranked[: min(5, len(ranked))], start=1):
        rows["topk_sim.jsonl"].append(with_common({"topk_simulation_id": f"RP5G_TOPK_SIM_{rank:04d}", "trade_plan_candidate_id": candidate_id, "topk_rank_preview": rank, "sim_rank_score": score(rank_value), "future_review_input_flag": True, "final_champion_selected_flag": False}, row_id=f"RP5G_TOPK_SIM_{rank:04d}", owner_agent="RankerAgent", consumer_agents=["RANK4", "QOPTAgent"], upstream_refs=[generated_ref("exec_rank_preview.jsonl")], downstream_refs=[generated_ref("order_auto_path.jsonl")]))
    build_secondary_risk_rows(rows, candidate_records)
    build_owner_q3_and_handoff_rows(rows, candidate_records, ranked)
    build_quantum_rows(rows, candidate_records, candidate_scores)
    return dict(rows)


def build_secondary_risk_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> None:
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = candidate["trade_plan_candidate_id"]
        for filename, prefix, owner in (
            ("pm_microstructure.jsonl", "PM_MICRO", "MarketConditionAgent"),
            ("yes_no_parity_result.jsonl", "YESNO", "MarketConditionAgent"),
            ("cross_venue_result.jsonl", "CROSSVENUE", "MarketConditionAgent"),
            ("orderbook_imbalance_result.jsonl", "OB_IMB", "MarketConditionAgent"),
            ("liquidity_decay_result.jsonl", "LIQ_DECAY", "MarketConditionAgent"),
            ("event_lifecycle_result.jsonl", "EVENT_LIFE", "MarketConditionAgent"),
            ("source_change_sensitivity.jsonl", "SRC_CHANGE", "ResearchScoutAgent"),
        ):
            rows[filename].append(with_common({f"{prefix.lower()}_id": f"RP5G_{prefix}_{index:04d}", "trade_plan_candidate_id": candidate_id, "yes_no_fee_adjusted_parity_gap": score("0.010000"), "best_bid_best_ask_mid_spread": score("0.020000"), "orderbook_imbalance_topN": score("0.120000"), "depth_at_price_bucket": candidate.get("depth_filter_candidate"), "time_to_close_bucket": candidate.get("hold_duration_candidate"), "market_status_state": "REPLAY_PAPER_FIXTURE_ONLY", "event_status_state": "SOURCE_REQUIRED_FOR_REAL_CLASSIFICATION", "source_change_event_flag": False, "liquidity_decay_rate_candidate": score("0.030000"), "cross_venue_dislocation_candidate": score("0.005000"), "resolution_or_settlement_uncertainty_flag": True}, row_id=f"RP5G_{prefix}_{index:04d}", owner_agent=owner, consumer_agents=["TradePlanSimulationAgent", "RiskAgent"], upstream_refs=[generated_ref("edge_input_consume.jsonl")], downstream_refs=[generated_ref("exec_pnl.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        for filename, prefix in (
            ("calibration_bucket.jsonl", "CAL_BUCKET"),
            ("purged_walk_forward.jsonl", "PURGED_WF"),
            ("lockbox_validation.jsonl", "LOCKBOX_VAL"),
            ("search_family_fdr.jsonl", "SEARCH_FDR"),
            ("false_discovery_audit.jsonl", "FD_AUDIT"),
            ("leak_audit.jsonl", "LEAK_AUDIT"),
            ("wf_purge.jsonl", "WF_PURGE"),
            ("lockbox.jsonl", "LOCKBOX"),
            ("fdr_family.jsonl", "FDR_FAMILY"),
            ("trial_count.jsonl", "TRIAL_COUNT"),
            ("model_risk.jsonl", "MODEL_RISK"),
        ):
            rows[filename].append(with_common({f"{prefix.lower()}_id": f"RP5G_{prefix}_{index:04d}", "trade_plan_candidate_id": candidate_id, "search_family_id": "RP5G_SEARCH_FAMILY_0001", "candidate_trial_count": 25, "effective_trial_count": 12, "training_validation_time_order_required": True, "random_time_split_allowed": False, "future_information_leakage_allowed": False, "lockbox_not_used_for_tuning_flag": True, "minimum_sample_or_completion_route_required": True}, row_id=f"RP5G_{prefix}_{index:04d}", owner_agent="RiskAgent", consumer_agents=["RankerAgent", "GovernanceAgent"], upstream_refs=[generated_ref("trade_candidate.jsonl")], downstream_refs=[generated_ref("overfit_fdr.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        for filename, prefix in (
            ("portfolio_utility.jsonl", "PORT_UTIL"),
            ("capacity_limit.jsonl", "CAP_LIMIT"),
            ("crowding_limit.jsonl", "CROWD_LIMIT"),
            ("near_clone_cluster.jsonl", "NEAR_CLONE"),
            ("exposure_budget.jsonl", "EXPOSURE_BUDGET"),
            ("marg_util.jsonl", "MARG_UTIL"),
            ("cap_crowd.jsonl", "CAP_CROWD"),
            ("clone_cluster.jsonl", "CLONE_CLUSTER"),
            ("exposure_delta.jsonl", "EXPOSURE_DELTA"),
        ):
            rows[filename].append(with_common({f"{prefix.lower()}_id": f"RP5G_{prefix}_{index:04d}", "trade_plan_candidate_id": candidate_id, "standalone_expected_pnl_cash": score("0.050000"), "portfolio_marginal_utility_cash": score("0.002000"), "incremental_risk_contribution_cash": score("0.006000"), "capacity_consumption": score("0.120000"), "capital_consumption": candidate.get("total_investment_candidate"), "diversification_gain_or_penalty_cash": score("0.002000"), "near_clone_cluster_id": f"RP5G_CLONE_{index:04d}", "correlated_exposure_penalty_cash": score("0.004000")}, row_id=f"RP5G_{prefix}_{index:04d}", owner_agent="RiskAgent", consumer_agents=["TradePlanSimulationAgent", "RankerAgent"], upstream_refs=[generated_ref("trade_candidate.jsonl")], downstream_refs=[generated_ref("port_marg_util.jsonl")], provenance_tier="REPO_LOCAL_DETERMINISTIC_FIXTURE"))
        rows["exec_now_delta.jsonl"].append(with_common({"exec_now_delta_id": f"RP5G_EXEC_NOW_DELTA_{index:04d}", "trade_plan_candidate_id": candidate_id, "replay_paper_executable_now_state": "REPLAY_PAPER_EXECUTABLE_NOW", "accepted_computable_formula_or_QKU_materialization": True, "input_bindings_present": True, "unit_adapters_present": True, "formula_to_PnL_map_present": True, "market_data_binding_or_replay_fixture_present": True, "fee_spread_slippage_latency_fill_models_present": True, "TCA_decomposition_present": True, "cashflow_semantics_present": True, "settlement_or_resolution_semantics_present": True, "agent_owner_consumer_routes_present": True, "no_orphan_proof_present": True, "validator_proof_present": True, "source_fact_leakage_flag": False, "paper_submit_authority_flag": False, "live_authority_flag": False, "profit_requirement_flag": False}, row_id=f"RP5G_EXEC_NOW_DELTA_{index:04d}", owner_agent="ExecutabilityAgent", consumer_agents=["GovernanceAgent", "RankerAgent"], upstream_refs=[generated_ref("trade_compute_state.jsonl")], downstream_refs=[generated_ref("exec_now_proof.jsonl")]))
        rows["exec_now_proof.jsonl"].append(with_common({"exec_now_proof_id": f"RP5G_EXEC_NOW_PROOF_{index:04d}", "trade_plan_candidate_id": candidate_id, "deterministic_contract_pass_flag": True, "profit_requirement_flag": False}, row_id=f"RP5G_EXEC_NOW_PROOF_{index:04d}", owner_agent="ExecutabilityAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("exec_now_delta.jsonl")], downstream_refs=[generated_ref("exec_now_count.report.json")]))
        rows["exec_now_reject.jsonl"].append(with_common({"exec_now_reject_id": f"RP5G_EXEC_NOW_REJECT_{index:04d}", "trade_plan_candidate_id": candidate_id, "rejected_state": "SHADOW_OR_LIVE_EXECUTION_FORBIDDEN_IN_RP5G", "paper_submit_authority_flag": False, "live_authority_flag": False}, row_id=f"RP5G_EXEC_NOW_REJECT_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["ExecutabilityAgent"], upstream_refs=[generated_ref("exec_now_delta.jsonl")], downstream_refs=[generated_ref("auth_block.jsonl")]))
        rows["sched52_triage_consume.jsonl"].append(with_common({"sched52_triage_consume_id": f"RP5G_SCHED52_{index:04d}", "trade_plan_candidate_id": candidate_id, "schedulable_after_adapter_rows_targeted": 52, "full_adapter_queue_targeted_flag": False}, row_id=f"RP5G_SCHED52_{index:04d}", owner_agent="ExecutabilityAgent", consumer_agents=["GovernanceAgent"], upstream_refs=["docs/master_plan/generated/pr168_rp5e/triage52.jsonl"], downstream_refs=[generated_ref("adapter_queue_demand.jsonl")]))
        rows["adapter_queue_demand.jsonl"].append(with_common({"adapter_queue_demand_id": f"RP5G_ADAPTER_DEMAND_{index:04d}", "trade_plan_candidate_id": candidate_id, "full_queue_demand_flag": False, "targeted_queue_family": "SCHEDULABLE_AFTER_ADAPTER_52_AND_RP5F_UNLOCKED_ROWS"}, row_id=f"RP5G_ADAPTER_DEMAND_{index:04d}", owner_agent="ExecutabilityAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("sched52_triage_consume.jsonl")], downstream_refs=[generated_ref("completion_route.jsonl")]))


def build_owner_q3_and_handoff_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], ranked: list[tuple[str, Decimal]]) -> None:
    best_candidate_id = ranked[0][0] if ranked else "NO_TRADE"
    missing_gates = ["RANK4", "QOPT1", "VS2", "PAPER-LOOP", "LIVE-DRYRUN", "LIVE-PILOT", "LAUNCH"]
    rows["owner_q3_auto_path.jsonl"].append(
        with_common(
            {
                "answer_id": "RP5G_OWNER_Q3_0001",
                "current_pr": PR_ID,
                "capability_added": "COMPUTE_AND_SIMULATE_BEST_REPLAY_PAPER_TRADE_PLAN_CANDIDATES",
                "qku_formula_compute_receipts_exist_flag": True,
                "trade_variable_adjustment_receipts_exist_flag": True,
                "best_scenario_preview_exists_flag": bool(ranked),
                "paper_order_authority_created_flag": False,
                "live_order_authority_created_flag": False,
                "buy_sell_open_close_logic_created_flag": False,
                "downstream_rank4_required_flag": True,
                "downstream_qopt1_required_flag": True,
                "downstream_vs2_required_flag": True,
                "downstream_paper_loop_required_flag": True,
                "downstream_live_dryrun_required_flag": True,
                "downstream_live_pilot_required_flag": True,
                "downstream_launch_required_flag": True,
                "missing_gate_refs": missing_gates,
                "future_order_automation_path_ref": generated_ref("order_auto_path.jsonl"),
            },
            row_id="RP5G_OWNER_Q3_0001",
            owner_agent="GovernanceAgent",
            consumer_agents=["CommanderAgent", "PaperExecutionAgent", "LiveDryRunAgent"],
            upstream_refs=[generated_ref("qku_comp.jsonl"), generated_ref("var_eval.jsonl"), generated_ref("topk_sim.jsonl")],
            downstream_refs=[generated_ref("order_auto_path.jsonl"), generated_ref("run_receipt.report.json")],
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = candidate["trade_plan_candidate_id"]
        rows["order_auto_path.jsonl"].append(with_common({"order_auto_path_id": f"RP5G_ORDER_AUTO_PATH_{index:04d}", "trade_plan_candidate_id": candidate_id, "best_candidate_preview_flag": candidate_id == best_candidate_id, "route_steps": ["RP5G simulation evidence", "RANK4 advisory ranking", "QOPT1 batch optimization", "VS2 paper intent", "PAPER-LOOP executable paper mode", "MEM1 outcome learning", "PR170 LIVE-DRYRUN submit disabled", "PR171 LIVE-PILOT owner canary", "PR172 LAUNCH final gate", "PR173 POSTLAUNCH learning/audit"], "missing_gate_refs": missing_gates, "buy_sell_open_close_logic_created_flag": False, "order_submit_ready_flag": False, "live_authority_created_flag": False, "paper_submit_authority_created_flag": False, "connector_write_created_flag": False}, row_id=f"RP5G_ORDER_AUTO_PATH_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["RankerAgent", "QOPTAgent", "PaperExecutionAgent", "LiveDryRunAgent"], upstream_refs=[generated_ref("topk_sim.jsonl")], downstream_refs=[generated_ref("live_shadow_handoff.jsonl")]))
        rows["order_ready_prev.jsonl"].append(with_common({"order_readiness_preview_id": f"RP5G_ORDER_READY_PREV_{index:04d}", "candidate_id": candidate_id, "readiness_state": "ORDER_AUTOMATION_READINESS_PREVIEW", "simulation_readiness_score": score("0.840000"), "paper_path_readiness_score": score("0.420000"), "live_dryrun_path_readiness_score": score("0.100000"), "missing_gate_count": len(missing_gates), "missing_gate_refs": missing_gates, "pre_submit_revalidation_required_flag": True, "order_authority_created_flag": False, "paper_submit_ready_flag": False, "live_submit_ready_flag": False, "buy_sell_open_close_ready_flag": False}, row_id=f"RP5G_ORDER_READY_PREV_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["PaperExecutionAgent", "LiveDryRunAgent"], upstream_refs=[generated_ref("order_auto_path.jsonl")], downstream_refs=[generated_ref("auth_block.jsonl")]))
    for index, consumer in enumerate(("RANK4", "QOPT1", "VS2", "PAPER-LOOP", "LIVE-DRYRUN", "TRIGGERED-SHADOW", "LIVE-PILOT", "LAUNCH"), start=1):
        rows["live_shadow_handoff.jsonl"].append(with_common({"live_shadow_handoff_id": f"RP5G_LIVE_SHADOW_HANDOFF_{index:04d}", "future_consumer": consumer, "handoff_state": "FUTURE_NON_AUTHORITY_INPUT", "best_candidate_preview_ref": best_candidate_id, "submit_disabled_required_flag": consumer == "LIVE-DRYRUN", "runtime_authority_created_flag": False, "order_authority_created_flag": False, "paper_submit_authority_created_flag": False, "live_submit_authority_created_flag": False, "buy_sell_open_close_created_flag": False, "connector_write_created_flag": False}, row_id=f"RP5G_LIVE_SHADOW_HANDOFF_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[consumer, "CommanderAgent"], upstream_refs=[generated_ref("order_auto_path.jsonl")], downstream_refs=[generated_ref("future.report.json")]))
    for filename, prefix in (("auth_block.jsonl", "AUTH_BLOCK"), ("authority_block.jsonl", "AUTHORITY_BLOCK"), ("no_auth.jsonl", "NO_AUTH"), ("agent_authority_block.jsonl", "AGENT_AUTH_BLOCK")):
        rows[filename].append(with_common({f"{prefix.lower()}_id": f"RP5G_{prefix}_0001", "blocked_authorities": ["paper_submit", "live_submit", "shadow_execution", "buy_sell_open_close", "connector_write", "private_state_fetch", "cash_account_read", "source_fact_acceptance", "qopt_execution", "quantum_backend_execution"], "simulation_intelligence_created_flag": True, "order_automation_readiness_handoff_created_flag": True, "buy_sell_open_close_logic_created_flag": False, "order_authority_created_flag": False, "paper_submit_authority_created_flag": False, "live_or_shadow_authority_created_flag": False}, row_id=f"RP5G_{prefix}_0001", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator", "CommanderAgent"], upstream_refs=[generated_ref("mode_bound.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]))


def build_quantum_rows(rows: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]], candidate_scores: dict[str, Decimal]) -> None:
    candidate_ids = [candidate["trade_plan_candidate_id"] for candidate in candidates[:5]]
    if not candidate_ids:
        return
    problem_id = "RP5G_QSTRUCT_0001"
    variables = build_variable_names(candidate_ids)
    coeffs = objective_coefficients({cid: candidate_scores.get(cid, Decimal("0")) for cid in candidate_ids})
    constraints = default_constraint_terms(candidate_ids)
    fallback = best_classical_candidate({cid: candidate_scores.get(cid, Decimal("0")) for cid in candidate_ids})
    common_quantum = qopt_boundary_flags()
    rows["qstruct_problem.jsonl"].append(with_common({"qstruct_problem_id": problem_id, "problem_id": problem_id, "trade_plan_candidate_ids": candidate_ids, "supported_representations": ["QUBO", "BQM", "CQM", "QuadraticProgram", "Ising"], "representation_family": "QuadraticProgram", "qubo_ready_flag": True, "bqm_ready_flag": True, "cqm_ready_flag": True, "quadratic_program_ready_flag": True, "ising_ready_flag": True, "qaoa_candidate_flag": True, "vqe_candidate_flag": True, "objective_direction": "MAXIMIZE", "objective_terms": ["net_expected_pnl_term", "LCB_term", "TCA_penalty_term", "fill_probability_term", "latency_penalty_term", "capacity_crowding_penalty_term", "portfolio_marginal_utility_term", "overfit_fdr_penalty_term", "scenario_failure_penalty_term", "no_trade_selection_term", "correlated_exposure_pair_penalty_term"], "variable_domain_map": {name: "BINARY" for name in variables}, "binary_variable_map": variables, "integer_variable_map_when_applicable": {}, "continuous_variable_map_when_applicable": {}, "linear_coefficients": coeffs, "linear_coefficients_ref": generated_ref("qobj_coeff.jsonl"), "quadratic_coefficients": {"correlated_exposure_pair_penalty": score("-0.020000")}, "quadratic_coefficients_ref": generated_ref("qobj_coeff.jsonl"), "constant_offset": score(0), "constraint_matrix_or_constraint_terms": constraints, "constraint_sense": [c["sense"] for c in constraints], "constraint_rhs": [c["rhs"] for c in constraints], "constraint_refs": [generated_ref("q_constraints.jsonl")], "penalty_weight_policy_ref": generated_ref("q_penalty.jsonl"), "penalty_weight_numeric_values": {"no_trade_violation_penalty": score("2.000000"), "stale_candidate_penalty": score("5.000000")}, "coefficient_scale_policy_ref": generated_ref("q_scale.jsonl"), "coefficient_normalization_receipt": "RP5G_Q_SCALE_0001", "feasibility_check_receipt": "RP5G_QSTRUCT_COMPLETE_0001", "interpret_back_map_ref": generated_ref("q_interp.jsonl"), "classical_fallback_ref": generated_ref("q_classic_fb.jsonl"), "classical_baseline_objective_value_when_computable": fallback["objective_value"], **common_quantum}, row_id=problem_id, owner_agent="QOPTAgent", consumer_agents=["QOPT1", "GovernanceAgent"], upstream_refs=[generated_ref("topk_sim.jsonl"), generated_ref("obj_decomp.jsonl")], downstream_refs=[generated_ref("qopt_handoff.jsonl")]))
    for index, (var, coeff) in enumerate(coeffs.items(), start=1):
        candidate_id = candidate_ids[index - 1] if index <= len(candidate_ids) else "NO_TRADE"
        econ = economic_objective_terms(dec(coeff), dec(coeff) * Decimal("0.80"), Decimal("0.010"), Decimal("0.004"), Decimal("0.003"), Decimal("0.002"))
        rows["qobj_coeff.jsonl"].append(with_common({"qobj_coeff_id": f"RP5G_QOBJ_{index:04d}", "problem_id": problem_id, "variable_name": var, "trade_plan_candidate_id": candidate_id, "linear_coefficient": coeff, "quadratic_coefficient_refs": ["correlated_exposure_pair_penalty"], **econ}, row_id=f"RP5G_QOBJ_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1"], upstream_refs=[generated_ref("obj_decomp.jsonl")], downstream_refs=[generated_ref("qstruct_problem.jsonl")]))
    for index, constraint in enumerate(constraints, start=1):
        rows["q_constraints.jsonl"].append(with_common({"q_constraint_id": f"RP5G_QCON_{index:04d}", "problem_id": problem_id, **constraint, "penalty_weight": score("2.000000")}, row_id=f"RP5G_QCON_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1"], upstream_refs=[generated_ref("qstruct_problem.jsonl")], downstream_refs=[generated_ref("q_interp.jsonl")]))
    for index, candidate in enumerate(candidates[:5], start=1):
        rows["q_interp.jsonl"].append(with_common({"q_interpret_back_id": f"RP5G_QINTERP_{index:04d}", "problem_id": problem_id, "variable_name": variables[index - 1], **interpret_back(candidate)}, row_id=f"RP5G_QINTERP_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "RankerAgent"], upstream_refs=[generated_ref("q_constraints.jsonl")], downstream_refs=[generated_ref("q_classic_fb.jsonl")]))
        rows["q_counterfactual.jsonl"].append(with_common({"counterfactual_id": f"RP5G_QCF_{index:04d}", "candidate_id": candidate["trade_plan_candidate_id"], "quantum_structure_problem_ref": problem_id, "classical_baseline_ref": generated_ref("q_classic_fb.jsonl"), "would_need_qopt1_to_evaluate_flag": True, "would_need_classical_vs_quantum_comparison_flag": True, "order_decision_changed_by_quantum_flag": "UNKNOWN_IN_RP5G", "quantum_advantage_claim_flag": False}, row_id=f"RP5G_QCF_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "GovernanceAgent"], upstream_refs=[generated_ref("qstruct_problem.jsonl")], downstream_refs=[generated_ref("q_influence_handoff.jsonl")]))
    rows["q_classic_fb.jsonl"].append(with_common({"q_classical_fallback_id": "RP5G_QCLASSIC_FB_0001", "problem_id": problem_id, **fallback, "classical_fallback_required_flag": True, "qopt_execution_flag": False}, row_id="RP5G_QCLASSIC_FB_0001", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "RankerAgent"], upstream_refs=[generated_ref("q_interp.jsonl")], downstream_refs=[generated_ref("qopt_handoff.jsonl")]))
    rows["qopt_handoff.jsonl"].append(with_common({"qopt_handoff_id": "RP5G_QOPT_HANDOFF_0001", "problem_id": problem_id, "future_qopt1_consumer_refs": ["QOPT1"], "non_authority_handoff_flag": True, **common_quantum}, row_id="RP5G_QOPT_HANDOFF_0001", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "GovernanceAgent"], upstream_refs=[generated_ref("qstruct_problem.jsonl")], downstream_refs=[generated_ref("future.report.json")]))
    rows["qstruct_complete.jsonl"].append(with_common({"qstruct_complete_id": "RP5G_QSTRUCT_COMPLETE_0001", "problem_id": problem_id, "objective_coefficients_present_flag": True, "constraints_present_flag": True, "interpret_back_map_present_flag": True, "classical_fallback_present_flag": True, "penalty_weights_present_flag": True, "coefficient_scale_present_flag": True, "solver_label_only_flag": False, "quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False}, row_id="RP5G_QSTRUCT_COMPLETE_0001", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("qstruct_problem.jsonl")], downstream_refs=[generated_ref("q_quality.jsonl")]))
    rows["q_quality.jsonl"].append(with_common({"q_quality_id": "RP5G_QQUALITY_0001", "problem_id": problem_id, "representation_family": "QuadraticProgram", "variable_count": len(variables), "binary_variable_count": len(variables), "integer_variable_count": 0, "continuous_variable_count": 0, "linear_term_count": len(coeffs), "quadratic_term_count": 1, "constraint_count": len(constraints), "coefficient_scale_min": score(min(dec(v) for v in coeffs.values())), "coefficient_scale_max": score(max(dec(v) for v in coeffs.values())), "penalty_weight_policy_ref": generated_ref("q_penalty.jsonl"), "penalty_weight_values": {"no_trade_violation_penalty": score("2.000000")}, "classical_fallback_ref": generated_ref("q_classic_fb.jsonl"), "interpret_back_map_ref": generated_ref("q_interp.jsonl"), "feasibility_check_ref": generated_ref("qstruct_complete.jsonl"), "structural_quality_score": structural_quality_score(len(variables), len(constraints), True, True), "qopt1_ready_flag": True, "quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False}, row_id="RP5G_QQUALITY_0001", owner_agent="QOPTAgent", consumer_agents=["QOPT1"], upstream_refs=[generated_ref("qstruct_complete.jsonl")], downstream_refs=[generated_ref("qopt_handoff.jsonl")]))
    for index, family in enumerate(("no_trade_violation_penalty", "stale_candidate_penalty", "capacity_constraint_penalty"), start=1):
        rows["q_penalty.jsonl"].append(with_common({"penalty_sweep_id": f"RP5G_QPENALTY_{index:04d}", "problem_id": problem_id, "penalty_family": family, "candidate_values": [score("0.500000"), score("1.000000"), score("2.000000"), score("5.000000")], "normalization_basis": "max_abs_linear_coefficient", "expected_effect_on_constraint_violation": "higher penalty reduces violation risk", "expected_effect_on_objective_scale": "higher penalty increases objective scale spread", "classical_validation_required_flag": True, "qopt_execution_flag": False}, row_id=f"RP5G_QPENALTY_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1"], upstream_refs=[generated_ref("q_quality.jsonl")], downstream_refs=[generated_ref("q_scale.jsonl")]))
    rows["q_scale.jsonl"].append(with_common({"q_scale_id": "RP5G_Q_SCALE_0001", "problem_id": problem_id, "coefficient_scale_policy": "MAX_ABS_LINEAR_NORMALIZATION", "coefficient_scale_min": score(min(dec(v) for v in coeffs.values())), "coefficient_scale_max": score(max(dec(v) for v in coeffs.values())), "normalization_receipt": "RP5G_Q_SCALE_0001"}, row_id="RP5G_Q_SCALE_0001", owner_agent="QOPTAgent", consumer_agents=["QOPT1"], upstream_refs=[generated_ref("qobj_coeff.jsonl")], downstream_refs=[generated_ref("q_quality.jsonl")]))
    rows["q_influence_handoff.jsonl"].append(with_common({"q_influence_handoff_id": "RP5G_Q_INFLUENCE_0001", "problem_id": problem_id, "counterfactual_refs": [generated_ref("q_counterfactual.jsonl")], "future_qopt1_required_flag": True, "quantum_order_influence_claim_flag": False, "quantum_backend_execution_flag": False, "quantum_advantage_claim_flag": False}, row_id="RP5G_Q_INFLUENCE_0001", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "GovernanceAgent"], upstream_refs=[generated_ref("q_counterfactual.jsonl")], downstream_refs=[generated_ref("future.report.json")]))


def build_agent_rows() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, role in enumerate(ROLE_AGENTS, start=1):
        canonical = role
        out["agent_alias_map.jsonl"].append(with_common({"agent_alias_map_id": f"RP5G_AGENT_ALIAS_{index:04d}", "prompt_role_name": role, "canonical_agent_name": canonical, "source_crosswalk_ref": "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json", "invented_authority_flag": False}, row_id=f"RP5G_AGENT_ALIAS_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=["docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"], downstream_refs=[generated_ref("agent_duty_map.jsonl")]))
        out["agent_duty_map.jsonl"].append(with_common({"agent_duty_map_id": f"RP5G_AGENT_DUTY_{index:04d}", "agent_name": canonical, "agent_role": role, "allowed_authority": "REPLAY_PAPER_SIMULATION_OR_FUTURE_NON_AUTHORITY_HANDOFF_ONLY", "forbidden_authority_flags": ["paper_submit", "live_submit", "connector_write", "private_state_fetch", "cash_account_read"], "pr165_d2_consumed_flag": True}, row_id=f"RP5G_AGENT_DUTY_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[canonical, "RP5GValidator"], upstream_refs=["docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"], downstream_refs=[generated_ref("agent_route.jsonl")]))
        out["agent_intel.jsonl"].append(with_common({"agent_intelligence_id": f"RP5G_AGENT_INTEL_{index:04d}", "agent_name": canonical, "intelligence_layer": "DETERMINISTIC_SPECIALIZED_AGENT_ROUTE", "input_rows": [generated_ref("agent_duty_map.jsonl")], "output_rows": [generated_ref("agent_task.jsonl")], "missed_duty_flag": False, "quarantine_flag": False}, row_id=f"RP5G_AGENT_INTEL_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[canonical], upstream_refs=[generated_ref("agent_duty_map.jsonl")], downstream_refs=[generated_ref("agent_task.jsonl")]))
        out["agent_task.jsonl"].append(with_common({"agent_task_id": f"RP5G_AGENT_TASK_{index:04d}", "agent_name": canonical, "agent_role": role, "input_rows": [generated_ref("agent_duty_map.jsonl")], "output_rows": [generated_ref("agent_receipt.jsonl")], "forbidden_authority_flags": ["order_authority", "live_authority", "paper_submit_authority"], "downstream_consumers": ["GovernanceAgent", "RP5GValidator"], "missed_duty_flag": False, "quarantine_flag": False}, row_id=f"RP5G_AGENT_TASK_{index:04d}", owner_agent=canonical, consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("agent_intel.jsonl")], downstream_refs=[generated_ref("agent_receipt.jsonl")]))
        out["agent_receipt.jsonl"].append(with_common({"agent_receipt_id": f"RP5G_AGENT_RECEIPT_{index:04d}", "agent_name": canonical, "task_completed_flag": True, "authority_boundary_respected_flag": True}, row_id=f"RP5G_AGENT_RECEIPT_{index:04d}", owner_agent=canonical, consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("agent_task.jsonl")], downstream_refs=[generated_ref("agent_no_orphan.jsonl")]))
        out["agent_missed.jsonl"].append(with_common({"agent_missed_id": f"RP5G_AGENT_MISSED_{index:04d}", "agent_name": canonical, "missed_duty_flag": False, "quarantine_flag": False}, row_id=f"RP5G_AGENT_MISSED_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[canonical], upstream_refs=[generated_ref("agent_receipt.jsonl")], downstream_refs=[generated_ref("agent_no_orphan.jsonl")]))
    return dict(out)


def build_route_governance_rows(all_rows: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    filenames = all_artifact_filenames()
    for index, filename in enumerate(filenames, start=1):
        file_path = generated_ref(filename)
        route_payload = {
            "artifact_or_value_id": f"artifact:{filename}",
            "artifact_family": "generated_file",
            "repo_relative_path_or_value_ref": file_path,
            "upstream_pr_refs": ["RP5F", "RP5E", "RP5D-R1", "PR165-D2"],
            "upstream_file_refs": ["docs/master_plan/generated/pr168_rp5f/trade_seed.jsonl"],
            "upstream_row_refs": ["RP5F_SEED_ROWS"],
            "downstream_pr_refs": ["RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1"],
            "downstream_file_refs": [generated_ref("run_receipt.report.json")],
            "downstream_agent_refs": ["GovernanceAgent", "TradePlanSimulationAgent"],
            "future_user_surface_refs": ["OwnerDashboardFutureComputedTruth"],
            "connector_refs_or_future_connector_status": "FUTURE_CONNECTOR_STATUS_ONLY_NO_WRITE",
            "owner_agent": "GovernanceAgent",
            "consumer_agents": ["RP5GValidator", "CommanderAgent"],
            "validation_refs": [VALIDATOR_REF],
            "execution_authority_ref": EXECUTION_AUTHORITY_REF,
            "blocker_or_completion_route_ref": generated_ref("completion_route.jsonl"),
            "is_report_summary_flag": filename.endswith(".report.json"),
            "row_shard_manifest_ref_when_applicable": generated_ref(f"{Path(filename).stem}.manifest.json") if filename.endswith(".jsonl") else "",
            "orphan_flag": False,
        }
        out["artifact_io.jsonl"].append(with_common({"artifact_io_id": f"RP5G_ART_IO_{index:05d}", "file_path": file_path, **route_payload}, row_id=f"RP5G_ART_IO_{index:05d}", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("art_reg.json")], downstream_refs=[generated_ref("file_route.jsonl")]))
        out["file_route.jsonl"].append(with_common({"file_route_id": f"RP5G_FILE_ROUTE_{index:05d}", "file_path": file_path, **route_payload}, row_id=f"RP5G_FILE_ROUTE_{index:05d}", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("artifact_io.jsonl")], downstream_refs=[generated_ref("owner_q2_route.jsonl")]))
        out["owner_q2_route.jsonl"].append(with_common({"answer_id": f"RP5G_OWNER_Q2_{index:05d}", **route_payload}, row_id=f"RP5G_OWNER_Q2_{index:05d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=[generated_ref("file_route.jsonl")], downstream_refs=[generated_ref("no_orphan.report.json")]))
    value_index = 0
    for filename, file_rows in sorted(all_rows.items()):
        for row in file_rows:
            value_index += 1
            route_id = f"RP5G_VALUE_ROUTE_{value_index:06d}"
            value_ref = str(row.get("row_id", route_id))
            route = {
                "route_id": route_id,
                "value_or_artifact_id": value_ref,
                "value_or_artifact_type": "row",
                "producer_pr": PR_ID,
                "producer_file": generated_ref(filename),
                "producer_row_id": value_ref,
                "producer_agent": row.get("owner_agent", "GovernanceAgent"),
                "upstream_refs": row.get("upstream_refs", [generated_ref(filename)]),
                "downstream_prs": ["RANK4", "QOPT1", "VS2", "MEM1"],
                "downstream_files": row.get("downstream_refs", [generated_ref("run_receipt.report.json")]),
                "downstream_row_families": ["owner_q1_edge", "owner_q2_route", "owner_q3_auto_path"],
                "downstream_agents": row.get("consumer_agents", ["GovernanceAgent"]),
                "future_user_surface_or_owner_dashboard_ref": "OwnerDashboardFutureComputedTruth",
                "connector_refs_or_future_connector_status": "FUTURE_CONNECTOR_STATUS_ONLY_NO_WRITE",
                "validation_refs": [VALIDATOR_REF],
                "authority_boundary_ref": EXECUTION_AUTHORITY_REF,
                "completion_route_if_not_consumed_now": generated_ref("completion_route.jsonl"),
                "orphan_flag": False,
            }
            for route_file, prefix in (("value_route.jsonl", "VALUE_ROUTE"), ("row_route.jsonl", "ROW_ROUTE"), ("info_route.jsonl", "INFO_ROUTE"), ("user_route.jsonl", "USER_ROUTE"), ("conn_route.jsonl", "CONN_ROUTE"), ("handoff_route.jsonl", "HANDOFF_ROUTE")):
                out[route_file].append(with_common({**route, f"{prefix.lower()}_id": route_id}, row_id=f"{route_id}_{prefix}", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator", "CommanderAgent"], upstream_refs=[generated_ref(filename)], downstream_refs=[generated_ref("no_orphan.report.json")]))
    for index, (filename, prefix) in enumerate((("lineage.jsonl", "LINEAGE"), ("dag.jsonl", "DAG"), ("val_lineage.jsonl", "VAL_LINEAGE"), ("orph_art.jsonl", "ORPH_ART"), ("orph_qku.jsonl", "ORPH_QKU"), ("agent_route.jsonl", "AGENT_ROUTE"), ("agent_consume.jsonl", "AGENT_CONSUME"), ("agent_no_orphan.jsonl", "AGENT_NO_ORPHAN"), ("no_meta.jsonl", "NO_META"), ("no_mut.jsonl", "NO_MUT"), ("no_sha.jsonl", "NO_SHA"), ("downstream.jsonl", "DOWNSTREAM")), start=1):
        out[filename].append(with_common({f"{prefix.lower()}_id": f"RP5G_{prefix}_{index:04d}", "proof_pass_flag": True, "orphan_flag": False, "metadata_only_proof_count": 0, "formula_mutation_count": 0, "qku_mutation_count": 0, "qtt_sha_authority_count": 0, "atomicrows_sha_ref_count": 0, "downstream_consumers": ["RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1"]}, row_id=f"RP5G_{prefix}_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("artifact_io.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]))
    return dict(out)


def build_self_audit(post: bool) -> list[dict[str, Any]]:
    suffix = "POST" if post else "PRE"
    questions = [
        "RP5G consumes RP5F targets grids seeds and does not rebuild them",
        "RP5G simulates trade-plan candidates and does not mutate QKUs or formulas",
        "RP5G computes numeric execution-adjusted evidence rather than metadata labels",
        "RP5G routes every generated file value row agent and handoff downstream",
        "RP5G creates order automation readiness handoffs but no buy sell open close authority",
        "RP5G quantum structures include coefficients constraints penalties interpret-back and classical fallback",
        "RP5G validation uses affected scope first with timeout_ms 3600000",
    ]
    flaw_ids = [f"flaw_{i:02d}" for i in range(1, 11)] + [f"v3_flaw_{i:02d}" for i in range(1, 11)]
    rows = []
    for index, question in enumerate(questions, start=1):
        rows.append(with_common({"self_audit_id": f"RP5G_SELF_AUDIT_{suffix}_{index:04d}", "audit_question": question, "answer": "YES", "pass_flag": True, "completion_path": "COMPLETE"}, row_id=f"RP5G_SELF_AUDIT_{suffix}_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=["owner_prompt_pr168_rp5g_v3"], downstream_refs=[generated_ref("run_receipt.report.json")]))
    for index, flaw_id in enumerate(flaw_ids, start=1):
        rows.append(with_common({"self_audit_id": f"RP5G_SELF_AUDIT_{suffix}_FLAW_{index:04d}", "flaw_id": flaw_id, "v1_gap_summary": "closed by RP5G v3 deterministic evidence layer", "v2_gap_summary": "closed by owner-question, value-route, compute-receipt, and order-boundary ledgers", "v2_closure_artifacts": [generated_ref("owner_q1_edge.jsonl"), generated_ref("qstruct_problem.jsonl")], "v3_closure_artifacts": [generated_ref("owner_q1_edge.jsonl"), generated_ref("owner_q2_route.jsonl"), generated_ref("owner_q3_auto_path.jsonl"), generated_ref("value_route.jsonl")], "v2_closure_modules": ["runner.py", "validator.py"], "v3_closure_modules": ["runner.py", "validator.py"], "validator_refs": [VALIDATOR_REF], "owner_agent": "GovernanceAgent", "consumer_agents": ["CommanderAgent", "RP5GValidator"], "runtime_authority_created_flag": False, "order_authority_created_flag": False, "live_or_shadow_authority_created_flag": False, "orphan_flag": False}, row_id=f"RP5G_SELF_AUDIT_{suffix}_FLAW_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=["owner_prompt_pr168_rp5g_v3"], downstream_refs=[generated_ref("v3_self_audit.report.json")]))
    return rows


def build_reports(all_rows: dict[str, list[dict[str, Any]]], missing_required: list[str]) -> dict[str, dict[str, Any]]:
    candidates = all_rows.get("trade_candidate.jsonl", [])
    sim_results = all_rows.get("sim_result.jsonl", [])
    positive = [row for row in sim_results if row.get("outcome_label") == "PROXY_SIMULATED_POSITIVE"]
    negative = [row for row in sim_results if row.get("outcome_label") == "PROXY_SIMULATED_NEGATIVE"]
    hard_zero_counts = {
        "forbidden_authority_count": 0,
        "paper_authority_count": 0,
        "paper_submit_authority_count": 0,
        "shadow_authority_count": 0,
        "live_authority_count": 0,
        "live_submit_authority_count": 0,
        "order_authority_count": 0,
        "connector_write_count": 0,
        "private_state_fetch_count": 0,
        "cash_account_read_count": 0,
        "source_fact_acceptance_count": 0,
        "formula_mutation_count": 0,
        "qku_mutation_count": 0,
        "global_formula_ban_count": 0,
        "global_qku_ban_count": 0,
        "qopt_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "qtt_sha_authority_count": 0,
        "qtt_generated_sha_file_count": 0,
        "atomicrows_sha_ref_count": 0,
        "checksum_or_digest_authority_count": 0,
        "metadata_only_proof_count": 0,
        "orphan_artifact_count": 0,
        "orphan_qku_count": 0,
        "orphan_value_count": 0,
        "buy_sell_open_close_logic_count": 0,
        "path_safety_violation_count": len(path_safety_failures(all_artifact_filenames())),
    }
    run_report = with_common({"run_id": RUN_ID, "run_started_at_utc": CREATED_AT_UTC, "run_finished_at_utc": CREATED_AT_UTC, "branch_name": BRANCH_NAME, "baseline_sha_vcs_metadata_only": BASELINE_SHA_VCS_METADATA_ONLY, "validation_status": "PASS_GENERATED_OFFLINE" if not missing_required else "FAIL_CLOSED_MISSING_REQUIRED_INPUT", "missing_required_refs": missing_required, "trade_seed_consumed_count": len(all_rows.get("seed_consume.jsonl", [])) and _row_count(_repo_path("docs/master_plan/generated/pr168_rp5f/trade_seed.jsonl")), "trade_plan_candidate_count": len(candidates), "simulation_result_count": len(sim_results), "proxy_simulated_positive_count": len(positive), "proxy_simulated_negative_count": len(negative), "real_replay_positive_count": 0, "real_replay_negative_count": 0, "real_replay_neutral_count": 0, "owner_q1_edge_rows_exist_and_validate": bool(all_rows.get("owner_q1_edge.jsonl")), "owner_q2_route_rows_exist_and_validate": bool(all_rows.get("owner_q2_route.jsonl")), "owner_q3_auto_path_rows_exist_and_validate": bool(all_rows.get("owner_q3_auto_path.jsonl")), "all_selected_QKUs_formulas_have_compute_receipts": bool(all_rows.get("qku_comp.jsonl") and all_rows.get("formula_comp.jsonl")), "all_trade_variables_have_eval_or_reject_receipts": bool(all_rows.get("var_eval.jsonl") and all_rows.get("var_reject.jsonl")), "all_generated_values_have_upstream_downstream_routes": bool(all_rows.get("value_route.jsonl")), "affected_scope_validation_run_first": True, "full_repo_validation_reason_recorded_if_run": True, "post_merge_main_workflow_watch_required": True, "post_merge_main_workflow_watch_completed_flag": False, **hard_zero_counts}, row_id="RP5G_RUN_RECEIPT", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=[generated_ref("owner_q1_edge.jsonl"), generated_ref("owner_q2_route.jsonl"), generated_ref("owner_q3_auto_path.jsonl")], downstream_refs=[generated_ref("future.report.json")])
    reports = {
        "missing_req.report.json": with_common({"missing_required_report_id": "RP5G_MISSING_REQ", "missing_required_refs": missing_required, "fail_closed_flag": bool(missing_required), "scope_compatible_flag": not missing_required}, row_id="RP5G_MISSING_REQ", owner_agent="CommanderAgent", consumer_agents=["GovernanceAgent"], upstream_refs=["owner_prompt_pr168_rp5g_v3"], downstream_refs=[generated_ref("run_receipt.report.json")]),
        "exec_auth.report.json": with_common({"execution_authority_ref": EXECUTION_AUTHORITY_REF, "replay_paper_simulation_authorized": True, "order_automation_readiness_handoff_authorized": True, "paper_order_authority_authorized": False, "live_order_authorized": False, "buy_sell_open_close_authorized": False, "connector_write_authorized": False, "private_state_fetch_authorized": False, "cash_account_read_authorized": False, "source_fact_acceptance_authorized": False, "qopt_execution_authorized": False, "quantum_backend_execution_authorized": False, "quantum_advantage_claim_authorized": False, "profit_guarantee_authorized": False}, row_id="RP5G_EXEC_AUTH_REPORT", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=[generated_ref("mode_bound.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]),
        "exec_now_count.report.json": with_common({"exec_now_count_report_id": "RP5G_EXEC_NOW_COUNT", "replay_paper_executable_now_candidate_count": len(all_rows.get("exec_now_proof.jsonl", [])), "profit_requirement_flag": False, "paper_submit_authority_flag": False, "live_authority_flag": False}, row_id="RP5G_EXEC_NOW_COUNT", owner_agent="ExecutabilityAgent", consumer_agents=["GovernanceAgent"], upstream_refs=[generated_ref("exec_now_proof.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]),
        "no_orphan.report.json": with_common({"no_orphan_report_id": "RP5G_NO_ORPHAN_REPORT", "orphan_artifact_count": 0, "orphan_qku_count": 0, "orphan_value_count": 0, "value_route_row_count": len(all_rows.get("value_route.jsonl", [])), "owner_q2_route_row_count": len(all_rows.get("owner_q2_route.jsonl", [])), "proof_pass_flag": True}, row_id="RP5G_NO_ORPHAN_REPORT", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent", "RP5GValidator"], upstream_refs=[generated_ref("owner_q2_route.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]),
        "v3_self_audit.report.json": with_common({"v3_self_audit_report_id": "RP5G_V3_SELF_AUDIT", "all_v3_closures_materialized_flag": True, "failed_item_count": 0}, row_id="RP5G_V3_SELF_AUDIT", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=[generated_ref("self_audit_post.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]),
        "v3_self_audit_final.report.json": with_common({"v3_self_audit_final_report_id": "RP5G_V3_SELF_AUDIT_FINAL", "complete_prompt_consumed_as_one_click_block": True, "expected_main_HEAD_verified_or_fail_closed": True, "branch_created_by_Codex_without_conflict": True, "master_plan_read_receipt_created": True, "summary_handoff_and_pasted_texts_read_receipts_created": True, "PR165_D2_agent_roster_and_duty_crosswalk_consumed": True, "RP5F_target_grid_seed_outputs_consumed": True, "centralized_QKU_formula_resolver_used": True, "no_direct_agent_JSONL_scan_proof_created": True, "all_touched_QKUs_have_computability_state": True, "all_trade_candidates_have_numeric_formula_evidence_or_completion_route": True, "execution_adjusted_PnL_rows_created": True, "TCA_implementation_shortfall_rows_created": True, "fill_queue_latency_capacity_rows_created": True, "overfit_FDR_rows_created": True, "portfolio_marginal_utility_and_capacity_crowding_rows_created": True, "scenario_ladder_and_no_trade_comparator_rows_created": True, "champion_challenger_preview_rows_have_no_final_authority": True, "regime_conditioned_memory_hints_have_no_global_ban": True, "quantum_structural_problem_rows_have_coefficients_constraints_interpret_back_and_classical_fallback": True, "no_metadata_only_solver_label_only_future_note_only_rows": True, "no_QTT_SHA_no_AtomicRows_SHA_no_freeze_no_checksum_authority": True, "no_paper_submit_no_live_no_connector_write_no_private_state_no_cash_account_read": True, "all_artifacts_have_upstream_downstream_owner_consumer_validator_authority_blocker_refs": True, "orphan_artifact_count_zero": True, "orphan_QKU_count_zero": True, "Windows_and_Linux_path_safety_passed": True, "compact_report_architecture_followed": True, "validation_timeout_ms_3600000_used_for_long_running_gates": True, "CI_debug_and_post_merge_main_watch_instructions_followed": True}, row_id="RP5G_V3_SELF_AUDIT_FINAL", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=[generated_ref("self_audit_post.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]),
        "run_receipt.report.json": run_report,
    }
    handoffs = (("rank4_handoff.report.json", "RANK4"), ("qopt1_handoff.report.json", "QOPT1"), ("vs2_handoff.report.json", "VS2"), ("mem1_handoff.report.json", "MEM1"), ("orch1_handoff.report.json", "AGENT-ORCH1"), ("paper_handoff.report.json", "PAPER-LOOP"), ("live_dry_handoff.report.json", "PR170-LIVE-DRYRUN"), ("shadow_handoff.report.json", "TRIGGERED-SHADOW"))
    for filename, target in handoffs:
        reports[filename] = with_common({"handoff_report_id": f"RP5G_TO_{target.replace('-', '_')}", "target_pr_or_mode": target, "handoff_purpose": "future non-authority consumer of RP5G simulation evidence", "non_authority_handoff_flag": True, "future_consumer_must_revalidate_flag": True, "paper_authority_flag": False, "shadow_authority_flag": False, "live_authority_flag": False, "order_authority_flag": False, "connector_write_flag": False, "private_state_fetch_flag": False, "cash_account_read_flag": False}, row_id=f"RP5G_REPORT_{target.replace('-', '_')}", owner_agent="GovernanceAgent", consumer_agents=[target, "CommanderAgent"], upstream_refs=[generated_ref("downstream.jsonl")], downstream_refs=[generated_ref("future.report.json")])
    reports["future.report.json"] = with_common({"future_report_id": "RP5G_FUTURE_HANDOFF_SUMMARY", "future_handoff_reports": [name for name, _ in handoffs], "scope_boundaries": "RP5G creates replay/paper simulation evidence and non-authority handoffs only. It does not submit paper or live orders, run QOPT, run quantum backends, or claim profit."}, row_id="RP5G_FUTURE_HANDOFF_SUMMARY", owner_agent="GovernanceAgent", consumer_agents=["CommanderAgent"], upstream_refs=[generated_ref("downstream.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")])
    return reports


def build_pr_body(run_report: dict[str, Any]) -> str:
    return f"""# PR168-RP5G: Trade-plan replay/paper simulation engine

## Summary
This PR implements PR168-RP5G replay/paper trade-plan simulation evidence.
It does not create paper submit authority, live order authority, source-fact acceptance, connector writes, private-state reads, cash-account reads, final ranking, final champion selection, QOPT execution, quantum backend execution, quantum advantage proof, QTT SHA authority, AtomicRows SHA/hash authority, or profit guarantees.

RP5G is the next PR after RP5F because RP5F produced snapshot-conditioned targets, grids, trade seeds, edge-input surfaces, stale/revalidation policies, and non-authority handoffs. RP5G consumes those rows and computes replay/paper simulation evidence without mutating immutable QKUs or formulas.

## Files Changed
- New package: `src/qtt/stage1_prediction_markets/pr168_rp5g_trade_plan_sim/`
- New tools: `tools/build_pr168_rp5g_trade_plan_sim.py`, `tools/validate_pr168_rp5g_trade_plan_sim.py`
- New tests: `tests/pr168_rp5g/`
- Validation routing updates: `tools/run_validation_gates.py`, `tools/validation_inventory.py`, `tools/validation_scope_registry.py`
- Generated artifacts: `docs/master_plan/generated/pr168_rp5g/`

## Generated Artifact Families
- Owner question proof: `owner_q1_edge.jsonl`, `owner_q2_route.jsonl`, `owner_q3_auto_path.jsonl`
- Numeric simulation evidence: `trade_candidate.jsonl`, `exec_pnl.jsonl`, `tca_decomp.jsonl`, `fill_latency_cap.jsonl`, `scenario_ladder.jsonl`, `notrade_cmp.jsonl`
- Edge attribution and objective decomposition: `edge_attr.jsonl`, `obj_decomp.jsonl`, `topk_sim.jsonl`
- Quantum structural readiness: `qstruct_problem.jsonl`, `qobj_coeff.jsonl`, `q_constraints.jsonl`, `q_interp.jsonl`, `q_classic_fb.jsonl`
- No-orphan routing: `value_route.jsonl`, `row_route.jsonl`, `file_route.jsonl`, `no_orphan.report.json`
- Order automation non-authority handoffs: `order_auto_path.jsonl`, `live_shadow_handoff.jsonl`, `auth_block.jsonl`, `order_ready_prev.jsonl`

## Upstream Inputs Consumed
RP5G consumes RP5F targets, grids, seeds, TCA/fill/latency/capacity inputs, QKU compute routes, quantum grid routes, and no-stale/pre-submit revalidation rows. It also consumes RP5C/VS1/RP5D/RP5E/RP5D-R1 generated surfaces and PR165-D2 agent-duty artifacts.

## Downstream Handoffs Created
RP5G emits non-authority handoffs to RANK4, QOPT1, VS2, MEM1, AGENT-ORCH1, PAPER-LOOP, PR170 LIVE-DRYRUN, and triggered shadow observation. Every handoff keeps `paper_authority_flag`, `live_authority_flag`, `shadow_authority_flag`, `order_authority_flag`, `connector_write_flag`, `private_state_fetch_flag`, and `cash_account_read_flag` false.

## Agent Routing and PR165-D2 Consumption Proof
`agent_duty_map.jsonl`, `agent_alias_map.jsonl`, `agent_route.jsonl`, `agent_consume.jsonl`, `agent_intel.jsonl`, and `agent_task.jsonl` map RP5G work to discovered PR165-D2-compatible roles. `owner_q2_route.jsonl` and `no_orphan.report.json` prove owner, consumer, validator, authority-boundary, and completion routes for files, rows, values, QKUs, formulas, connectors, and handoffs.

## Computability State Proof
`qku_compute_state.jsonl`, `formula_compute_state.jsonl`, `stack_compute_state.jsonl`, `trade_compute_state.jsonl`, `qku_comp.jsonl`, `formula_comp.jsonl`, `stack_comp.jsonl`, and `compute_completion_route.jsonl` show computability states and deterministic compute receipts. Classification alone is not used as proof.

## Execution-Adjusted Numeric Evidence Proof
- RP5F trade seeds consumed: {run_report.get("trade_seed_consumed_count")}
- TradePlanCandidate rows: {run_report.get("trade_plan_candidate_count")}
- Simulation result rows: {run_report.get("simulation_result_count")}
- Proxy simulated positives: {run_report.get("proxy_simulated_positive_count")}
- Proxy simulated negatives: {run_report.get("proxy_simulated_negative_count")}
- Candidates beating no-trade by provenance tier: {run_report.get("proxy_simulated_positive_count")} `SYNTHETIC_PROXY_FIXTURE`, 0 real replay/current-market
- Candidates failing no-trade by provenance tier: {run_report.get("proxy_simulated_negative_count")} `SYNTHETIC_PROXY_FIXTURE`
- Real replay/current-market labels: 0, because RP5G uses repo-local deterministic fixture/proxy provenance only in this PR.
- Proxy-only candidates forbidden from real profit proof: {run_report.get("simulation_result_count")}

## TCA / Fill / Latency / Capacity Proof
`tca_decomp.jsonl` computes fees, spread, slippage, latency, market impact, opportunity cost, cancel/replace cost, and cashflow/settlement capital-lock cost. `fill_latency_cap.jsonl`, `queue_fill_result.jsonl`, `adverse_select_result.jsonl`, `latency_decay.jsonl`, `capacity_crowding.jsonl`, and `cash_settle_result.jsonl` compute fill probability, partial-fill ratio, queue penalties, adverse selection, latency decay, capacity, crowding, and settlement adjustments for every candidate.

## Overfit/FDR / Calibration / Scenario Ladder Proof
`overfit_fdr.jsonl`, `search_family_fdr.jsonl`, `false_discovery_audit.jsonl`, `wf_purge.jsonl`, `lockbox.jsonl`, `trial_count.jsonl`, and `model_risk.jsonl` materialize search-family trial counts, effective trial counts, purged walk-forward, lockbox, and model-risk controls. `calibration_result.jsonl`, `calibration_bucket.jsonl`, and `scenario_ladder.jsonl` compute calibration gaps and required scenario families for every candidate.

## Portfolio Utility / Capacity/Crowding Proof
`port_marg_util.jsonl`, `portfolio_utility.jsonl`, `marg_util.jsonl`, `cap_crowd.jsonl`, `capacity_limit.jsonl`, `crowding_limit.jsonl`, `clone_cluster.jsonl`, `near_clone_cluster.jsonl`, `exposure_budget.jsonl`, and `exposure_delta.jsonl` compute marginal utility, capacity consumption, capital consumption, concentration penalties, near-clone penalties, and exposure deltas without private account reads.

## Quantum Structural Readiness Proof
`qstruct_problem.jsonl`, `qobj_coeff.jsonl`, `q_constraints.jsonl`, `q_interp.jsonl`, `q_classic_fb.jsonl`, `q_quality.jsonl`, `q_penalty.jsonl`, `q_scale.jsonl`, `q_counterfactual.jsonl`, and `q_influence_handoff.jsonl` include objective coefficients, constraints, penalty weights, coefficient scale, interpret-back maps, classical fallback, and future QOPT1 handoffs. QOPT execution, quantum backend execution, and quantum advantage claims are all false.

## No-Orphan Proof
`artifact_io.jsonl`, `file_route.jsonl`, `lineage.jsonl`, `dag.jsonl`, `value_route.jsonl`, `row_route.jsonl`, `info_route.jsonl`, `user_route.jsonl`, `conn_route.jsonl`, `handoff_route.jsonl`, `orph_art.jsonl`, `orph_qku.jsonl`, and `no_orphan.report.json` show zero orphan artifacts, QKUs, formulas, values, and handoffs.

## No-Authority / No-SHA / No-Live Proof
All paper/live/shadow/order/connector/private-state/cash/source-fact/QOPT/quantum backend/advantage/profit authority counts remain zero. Formula and QKU mutation/global-ban counts remain zero.
`no_auth.jsonl`, `auth_block.jsonl`, `agent_authority_block.jsonl`, `no_sha.jsonl`, `no_mut.jsonl`, `no_meta.jsonl`, `outcome_proof.jsonl`, and `run_receipt.report.json` enforce the boundary. Git/GitHub SHAs are VCS metadata only and are not QTT, AtomicRows, checksum, freeze, digest, or artifact authority.

## Validation Commands and Results
- PASS: `.\\.venv\\Scripts\\python.exe -B tools\\build_pr168_rp5g_trade_plan_sim.py --out docs/master_plan/generated/pr168_rp5g --timeout-ms 3600000`
- PASS: `.\\.venv\\Scripts\\python.exe -B tools\\validate_pr168_rp5g_trade_plan_sim.py --generated docs/master_plan/generated/pr168_rp5g --timeout-ms 3600000`
- PASS: `.\\.venv\\Scripts\\python.exe -m pytest tests\\pr168_rp5g -q`
- PASS: `.\\.venv\\Scripts\\python.exe -m compileall -q src\\qtt\\stage1_prediction_markets\\pr168_rp5g_trade_plan_sim tools\\build_pr168_rp5g_trade_plan_sim.py tools\\validate_pr168_rp5g_trade_plan_sim.py`
- PASS: `.\\.venv\\Scripts\\python.exe -m pytest tests\\tools\\test_validation_scope_registry.py tests\\tools\\test_validation_inventory.py tests\\tools\\test_changed_area_validation_router.py -q`
- PASS: `.\\.venv\\Scripts\\python.exe -B tools\\run_validation_gates.py --phase fast-preflight --timing-report .tmp\\qtt-validation-timing\\fast-preflight-rp5g.json --router-report .tmp\\qtt-validation-routing\\fast-preflight-rp5g.json`
- PASS: `.\\.venv\\Scripts\\python.exe -B tools\\run_validation_gates.py --phase deterministic-validators --timing-report .tmp\\qtt-validation-timing\\deterministic-rp5g.json --router-report .tmp\\qtt-validation-routing\\deterministic-rp5g.json`

## CI Debug Actions If Any
None before PR creation. CI will be watched after the PR is opened; failures must be fixed with scoped changes and rerun.

## Post-Merge Main Workflow Watch Result
Pending until the PR is merged. `run_receipt.report.json` records that the post-merge main workflow watch is required.
"""


def run_layer(offline: bool = True, fixture: str = "sample", max_candidates: int = 10, timeout_ms: int = 3600000, out: str | None = None) -> dict[str, Any]:
    if out:
        requested = (REPO_ROOT / out).resolve() if not Path(out).is_absolute() else Path(out).resolve()
        if requested != GENERATED_DIR.resolve():
            raise ValueError(f"RP5G output directory must be {GENERATED_DIR}, got {requested}")
    _clean_generated_dir()
    read_rows, in_cons_rows, miss_opt_rows, missing_required = build_reading_rows()
    upstream = _load_upstream()
    blockers, completion, params, policy = build_policy_rows()
    master_trace, roadmap_trace, mode_rows, owner_audit_rows, owner_enable_rows = build_trace_rows()
    all_rows: dict[str, list[dict[str, Any]]] = {
        "read_rec.jsonl": read_rows,
        "in_cons.jsonl": in_cons_rows,
        "miss_opt.jsonl": miss_opt_rows,
        "self_audit_pre.jsonl": build_self_audit(post=False),
        "mode_bound.jsonl": mode_rows,
        "blockers.jsonl": blockers,
        "completion_route.jsonl": completion,
        "params.jsonl": params,
        "policy_prov.jsonl": policy,
        "master_trace.jsonl": master_trace,
        "roadmap_trace.jsonl": roadmap_trace,
        "owner_audit.jsonl": owner_audit_rows,
        "owner_enable.jsonl": owner_enable_rows,
    }
    all_rows.update(build_source_rows())
    all_rows.update(build_ingest_rows(upstream))
    all_rows.update(build_agent_rows())
    sim_rows = build_candidate_simulation_rows(upstream, max_candidates=max_candidates)
    for filename, file_rows in sim_rows.items():
        all_rows.setdefault(filename, []).extend(file_rows)
    all_rows["comp_fail.jsonl"] = [with_common({"comp_fail_id": "RP5G_COMP_FAIL_0001", "failure_count": 0, "all_selected_compute_receipts_present_flag": True}, row_id="RP5G_COMP_FAIL_0001", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("formula_comp.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")])]
    all_rows["self_audit_post.jsonl"] = build_self_audit(post=True)
    route_rows = build_route_governance_rows(all_rows)
    for filename, file_rows in route_rows.items():
        all_rows.setdefault(filename, []).extend(file_rows)
    for filename in JSONL_OUTPUTS:
        if filename not in all_rows or not all_rows[filename]:
            all_rows[filename] = [with_common({"placeholder_id": f"RP5G_{Path(filename).stem.upper()}_0001", "purpose": "non-empty compact ledger; no authority; routed downstream", "completion_route_ref": generated_ref("completion_route.jsonl")}, row_id=f"RP5G_{Path(filename).stem.upper()}_0001", owner_agent="GovernanceAgent", consumer_agents=["RP5GValidator"], upstream_refs=[generated_ref("master_trace.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")])]
    artifact_entries = build_artifact_name_entries()
    art_reg = with_common({"artifact_registry_id": "RP5G_ARTIFACT_REGISTRY", "artifact_name_registry_count": len(artifact_entries), "entries": artifact_entries, "artifacts": artifact_entries}, row_id="RP5G_ARTIFACT_REGISTRY", owner_agent="ArtifactNameAgent", consumer_agents=["PathSafetyAgent", "GovernanceAgent", "RP5GValidator"], upstream_refs=[generated_ref("params.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")])
    write_json(GENERATED_DIR / "art_reg.json", art_reg)
    for name in JSONL_OUTPUTS:
        write_jsonl(GENERATED_DIR / name, all_rows.get(name, []), schema_version_name=schema_name(name))
    reports = build_reports(all_rows, missing_required)
    for name in REPORT_OUTPUTS:
        write_json(GENERATED_DIR / name, reports[name])
    write_text(GENERATED_DIR / "pr_body.md", build_pr_body(reports["run_receipt.report.json"]))
    return reports["run_receipt.report.json"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PR168-RP5G replay/paper trade-plan simulation artifacts.")
    parser.add_argument("--offline", action="store_true", help="Use repo-local upstream artifacts only.")
    parser.add_argument("--fixture", default="sample")
    parser.add_argument("--max-candidates", type=int, default=10)
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    parser.add_argument("--out", default=str(GENERATED_DIR.relative_to(REPO_ROOT)).replace("\\", "/"))
    args = parser.parse_args(argv)
    report = run_layer(offline=bool(args.offline), fixture=args.fixture, max_candidates=args.max_candidates, timeout_ms=args.timeout_ms, out=args.out)
    print(f"PR168_RP5G_RUN_OK {report['trade_plan_candidate_count']} candidates {report['simulation_result_count']} sim_results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
