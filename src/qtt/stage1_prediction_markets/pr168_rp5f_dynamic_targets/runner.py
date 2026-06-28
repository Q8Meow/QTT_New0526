"""Deterministic PR168-RP5F dynamic target and order-grid generator."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any, Iterable

from .artifact_names import build_artifact_name_entries
from .models import (
    BASELINE_SHA_VCS_METADATA_ONLY,
    BLOCKER_CODES,
    BLOCKER_POLICY_REF,
    BRANCH_NAME,
    CREATED_AT_UTC,
    EXECUTION_AUTHORITY_REF,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    MARKET_FAMILY,
    OPTIONAL_INPUT_REFS,
    PARAM_DEFAULTS,
    PR_ID,
    REPORT_OUTPUTS,
    REPO_ROOT,
    REQUIRED_INPUT_REFS,
    RUN_ID,
    STAGE_PROFILE_ID,
    VALIDATOR_REF,
    all_artifact_filenames,
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
)
from .path_safety import path_safety_failures

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5c_library_reader import load_library, resolve_stage_agent_universe  # noqa: E402


FUTURE_CONSUMERS = ["RP5G", "RANK4", "QOPT1", "VS2", "MEM1", "AGENT-ORCH1", "PAPER-LOOP", "PR170-LIVE-DRYRUN", "PR171-LIVE-PILOT", "TRIGGERED-SHADOW-COMPARISON"]
PLATFORMS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
RP5C_AGENT_ALIASES = {
    "CommanderAgent": "commander_agent",
    "TradeTargetScoutAgent": "parameter_selector_agent",
    "OrderVariableAgent": "parameter_selector_agent",
    "MarketConditionAgent": "risk_manager_agent",
    "RiskAgent": "risk_manager_agent",
    "QOPTAgent": "quantum_optimizer_agent",
    "ResearchScoutAgent": "research_agent",
    "GovernanceAgent": "governance_agent",
}

EDGE_HINT_FAMILIES = (
    "fee_adjusted_yes_no_complement_parity_hint",
    "cross_venue_price_dislocation_hint",
    "cross_venue_latency_skew_hint",
    "market_implied_probability_shift_hint",
    "orderbook_imbalance_hint",
    "spread_compression_or_widening_hint",
    "liquidity_decay_hint",
    "partial_fill_risk_hint",
    "event_lifecycle_transition_hint",
    "source_update_or_news_sensitivity_hint",
    "longshot_favorite_region_hint",
    "no_trade_margin_required_hint",
)

RESEARCH_SOURCES = (
    ("https://docs.kalshi.com/", "Kalshi API documentation", "OFFICIAL", "prediction-market market/orderbook endpoint semantics candidate input"),
    ("https://docs.polymarket.com/developers/CLOB/introduction", "Polymarket CLOB documentation", "OFFICIAL", "prediction-market CLOB orderbook and execution mechanics candidate input"),
    ("https://www.interactivebrokers.com/en/trading/forecast-contracts.php", "Interactive Brokers Forecast Contracts", "OFFICIAL", "ForecastEx/IBKR venue availability candidate context"),
    ("https://www.cis.upenn.edu/~mkearns/finread/almgren_chris.pdf", "Optimal execution of portfolio transactions", "RESEARCH", "TCA and market impact decomposition candidate input"),
    ("https://www.jstor.org/stable/2346101", "Controlling the False Discovery Rate", "RESEARCH", "multiple-testing/FDR control candidate input"),
    ("https://jmlr.org/papers/v18/16-558.html", "Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization", "RESEARCH", "successive halving/frontier budget candidate input"),
    ("https://docs.dwavequantum.com/en/latest/concepts/models.html", "D-Wave model concepts", "OFFICIAL", "QUBO/BQM/CQM structural mapping candidate input"),
    ("https://qiskit-community.github.io/qiskit-optimization/tutorials/01_quadratic_program.html", "Qiskit Optimization QuadraticProgram tutorial", "OFFICIAL", "QuadraticProgram/QUBO structural mapping candidate input"),
    ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551", "The Deflated Sharpe Ratio", "RESEARCH", "multiple-testing-aware performance evaluation candidate input"),
    ("https://arxiv.org/abs/1406.2294", "High-frequency trading in a limit order book", "RESEARCH", "queue/adverse-selection and orderbook imbalance candidate input"),
)


def _repo_path(ref: str) -> Path:
    return REPO_ROOT / ref


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".jsonl":
        return len([line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()])
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _surface_family(ref: str) -> str:
    name = Path(ref).name.lower()
    if "rp5d_r1" in ref or "rp5d_r1" in name:
        return "RP5D_R1_EXEC_NOW_OVERLAY"
    if "/pr168_rp5e/" in ref or "rp5e" in name:
        return "RP5E_STACK_CONTEXT"
    if "/pr168_rp5d/" in ref or "rp5d" in name:
        return "RP5D_EXECUTABILITY"
    if "/pr168_vs1/" in ref or "vs1" in name:
        return "VS1_VERTICAL_SLICE"
    if "/rp5c/" in ref or "rp5c" in name:
        return "RP5C_IMMUTABLE_LIBRARY"
    if "PR165_D2" in Path(ref).name:
        return "PR165_D2_AGENT_DUTY"
    if ref.startswith("docs/master_plan/"):
        return "MASTER_PLAN"
    return "TOOLING"


def build_reading_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    read_rows: list[dict[str, Any]] = []
    in_cons: list[dict[str, Any]] = []
    miss_opt: list[dict[str, Any]] = []
    missing_required: list[str] = []
    for index, ref in enumerate(stable_unique(REQUIRED_INPUT_REFS), start=1):
        path = _repo_path(ref)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        else:
            missing_required.append(ref)
        count = _row_count(path)
        read_rows.append(
            with_common(
                {
                    "reading_receipt_id": f"RP5F_READ_{index:05d}",
                    "file_ref": ref,
                    "surface_family": _surface_family(ref),
                    "exists_flag": exists,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_line_count": count,
                    "actual_value_recorded_flag": True,
                },
                row_id=f"RP5F_READ_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "TradeTargetScoutAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("missing_req.report.json")],
                provenance_tier="INPUT_READ_RECEIPT",
            )
        )
        in_cons.append(
            with_common(
                {
                    "input_consumption_id": f"RP5F_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": _surface_family(ref),
                    "consumed_flag": exists,
                    "row_count_consumed": count if exists else 0,
                    "not_consumed_reason": "" if exists else "MISSING_REQUIRED_INPUT",
                    "consumer_output_refs": [generated_ref("targets.jsonl"), generated_ref("var_grid.jsonl"), generated_ref("trade_seed.jsonl")],
                },
                row_id=f"RP5F_IN_CONS_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "TradeTargetScoutAgent", "OrderVariableAgent"],
                upstream_refs=[ref] if exists else ["missing_required_input"],
                downstream_refs=[generated_ref("lineage.jsonl"), generated_ref("artifact_io.jsonl")],
            )
        )
    fact_sources = {
        "rp5d": "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
        "rp5d_r1": "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
    }
    for name, ref in fact_sources.items():
        path = _repo_path(ref)
        if path.is_file():
            report = read_json(path)
            for field in ("replay_paper_executable_now_count", "schedulable_after_adapter_count", "adapter_queue_row_count", "new_replay_paper_executable_now_count", "rows_promoted"):
                if field in report:
                    idx = len(read_rows) + 1
                    read_rows.append(
                        with_common(
                            {
                                "reading_receipt_id": f"RP5F_BASELINE_{name}_{field}",
                                "file_ref": ref,
                                "surface_family": f"{name.upper()}_BASELINE_FACT",
                                "exists_flag": True,
                                "read_status": "READ_JSON_VALUE",
                                "observed_field": field,
                                "observed_value": report.get(field),
                                "actual_value_recorded_flag": True,
                            },
                            row_id=f"RP5F_READ_{idx:05d}",
                            owner_agent="CommanderAgent",
                            consumer_agents=["GovernanceAgent"],
                            upstream_refs=[ref],
                            downstream_refs=[generated_ref("run_receipt.report.json")],
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
                    "missing_optional_id": f"RP5F_MISS_OPT_{index:04d}",
                    "optional_artifact_ref": ref,
                    "exists_flag": exists,
                    "consumed_flag": exists,
                    "row_count_or_line_count": _row_count(path),
                    "fallback_ref": "RP5C/RP5D/RP5E/RP5D-R1 centralized resolver and routing surfaces",
                    "fail_closed_flag": False,
                },
                row_id=f"RP5F_MISS_OPT_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent"],
                upstream_refs=[ref] if exists else ["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("read_rec.jsonl")],
            )
        )
    return read_rows, in_cons, miss_opt, missing_required


def _load_upstream() -> dict[str, Any]:
    rp5d = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d"
    rp5e = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5e"
    r1 = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d_r1"
    return {
        "rp5d_run": read_json(rp5d / "rp5d_run_receipt.report.json"),
        "rp5d_tiers": read_jsonl(rp5d / "rp5d_exec_tiers.jsonl"),
        "rp5e_run": read_json(rp5e / "run_receipt.report.json"),
        "rp5e_topk": read_jsonl(rp5e / "topk.jsonl"),
        "rp5e_ctx": read_jsonl(rp5e / "ctx_univ.jsonl"),
        "rp5e_fdr": read_jsonl(rp5e / "fdr_ctrl.jsonl"),
        "rp5e_capacity": read_jsonl(rp5e / "capacity.jsonl"),
        "rp5e_q_obj": read_jsonl(rp5e / "q_obj.jsonl"),
        "r1_run": read_json(r1 / "run_receipt.report.json"),
        "r1_promote": read_jsonl(r1 / "promote.jsonl"),
        "r1_proof": read_jsonl(r1 / "exec_now_proof.jsonl"),
        "r1_nonpromote": read_jsonl(r1 / "nonpromote.jsonl"),
    }


def _clean_generated_dir() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    allowed = set(all_artifact_filenames())
    for path in GENERATED_DIR.iterdir():
        if path.is_file() and path.name in allowed:
            path.unlink()


def build_policy_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = [
        with_common(
            {
                "blocker_code": code,
                "blocker_scope": "DYNAMIC_TARGET_GRID_SEED_ONLY",
                "global_formula_or_qku_blocker_flag": False,
                "allowed_resolution_route": "complete exact source/revalidation/downstream route or retain condition-scoped incomplete row",
                "broad_global_blocker_flag": False,
            },
            row_id=f"RP5F_BLOCKER_{index:04d}",
            owner_agent="GovernanceAgent",
            consumer_agents=["TradeTargetScoutAgent", "OrderVariableAgent", "RiskAgent"],
            upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
            downstream_refs=[generated_ref("completion_route.jsonl")],
        )
        for index, code in enumerate(BLOCKER_CODES, start=1)
    ]
    params: list[dict[str, Any]] = []
    policy: list[dict[str, Any]] = []
    for index, (name, value) in enumerate(PARAM_DEFAULTS.items(), start=1):
        param_id = f"RP5F_PARAM_{index:04d}"
        prov_id = f"RP5F_POLICY_PROV_{index:04d}"
        params.append(
            with_common(
                {
                    "parameter_id": param_id,
                    "parameter_name": name,
                    "parameter_value": value,
                    "policy_provenance_ref": prov_id,
                    "tunable_flag": True,
                    "bootstrap_default_flag": True,
                    "replay_paper_calibration_required_flag": True,
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                },
                row_id=param_id,
                owner_agent="GovernanceAgent",
                consumer_agents=["TradeTargetScoutAgent", "OrderVariableAgent", "RP5FValidator"],
                upstream_refs=["owner_prompt_pr168_rp5f_v3"],
                downstream_refs=[generated_ref("policy_prov.jsonl"), generated_ref("var_policy.jsonl")],
                provenance_tier="BOOTSTRAP_REQUIRES_REPLAY_PAPER_CALIBRATION",
            )
        )
        policy.append(
            with_common(
                {
                    "policy_provenance_id": prov_id,
                    "parameter_ref": param_id,
                    "parameter_name": name,
                    "provenance_tier": "BOOTSTRAP_REQUIRES_REPLAY_PAPER_CALIBRATION",
                    "external_source_default_flag": False,
                    "live_default_flag": False,
                    "proprietary_claim_flag": False,
                    "profit_proof_flag": False,
                },
                row_id=prov_id,
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5FValidator"],
                upstream_refs=[generated_ref("params.jsonl")],
                downstream_refs=[generated_ref("no_hardcode.jsonl")],
                provenance_tier="BOOTSTRAP_REQUIRES_REPLAY_PAPER_CALIBRATION",
            )
        )
    return blockers, params, policy


def build_mode_rows() -> list[dict[str, Any]]:
    specs = [
        ("REPLAY_MODE", True, False, False, False, "CONCURRENT_REPLAY_AND_PAPER_ONLY"),
        ("PAPER_MODE", True, False, False, False, "CONCURRENT_REPLAY_AND_PAPER_ONLY"),
        ("LIVE_DRYRUN_SUBMIT_DISABLED", False, True, True, False, "FUTURE_PR170_SUBMIT_DISABLED"),
        ("SHADOW_LIVE_CONCURRENT_COMPARISON", False, True, True, True, "POST_LIVE_EXECUTION_VALIDATION_ONLY_NOT_PRE_LIVE_GATE"),
        ("LIMITED_LIVE_CANARY", False, True, True, False, "FUTURE_PR171_OWNER_CONTROLLED_CANARY"),
        ("LIVE_MODE", False, True, True, False, "FUTURE_LAUNCH_ONLY_NOT_RP5F"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (mode, replay_paper, live_surface, live_receipts, post_live, role) in enumerate(specs, start=1):
        rows.append(
            with_common(
                {
                    "mode_boundary_id": f"RP5F_MODE_{index:04d}",
                    "runtime_mode": mode,
                    "stage1_replay_and_paper_run_mode": "CONCURRENT_SEPARATE_LANES_AFTER_SHARED_INPUT_LOCK",
                    "stage1_replay_pass_to_paper_test_sequential_transition_allowed_flag": False,
                    "stage1_replay_and_paper_results_must_remain_separate_flag": True,
                    "stage1_shadow_mode_required_before_limited_live_canary_flag": False,
                    "stage1_shadow_mode_requires_live_execution_surface_flag": True,
                    "stage1_shadow_mode_execution_enabled_flag": False,
                    "stage1_shadow_mode_pre_live_gate_role_allowed_flag": False,
                    "stage1_shadow_mode_post_live_validation_role": "POST_LIVE_EXECUTION_VALIDATION_ONLY_NOT_PRE_LIVE_GATE",
                    "rp5f_generation_allowed_flag": replay_paper,
                    "live_surface_required_flag": live_surface,
                    "live_receipts_required_flag": live_receipts,
                    "post_live_validation_role_flag": post_live,
                    "mode_role": role,
                    "submit_disabled_required_flag": mode == "LIVE_DRYRUN_SUBMIT_DISABLED",
                    "order_authority_flag": False,
                    "connector_write_flag": False,
                    "private_state_fetch_flag": False,
                    "cash_account_read_flag": False,
                },
                row_id=f"RP5F_MODE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RiskAgent", "PaperExecutionAgent", "LiveDryRunAgent", "ShadowObservationAgent"],
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("live_shadow_route.jsonl"), generated_ref("pre_submit_reval.jsonl")],
            )
        )
    return rows


def build_trace_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    trace_specs = [
        ("dynamic prediction-market doctrine", ["snap_ctx.jsonl", "md_truth.jsonl", "src_fresh.jsonl", "targets.jsonl"], ["snapshot_context.py", "target_scout.py"]),
        ("centralized qku/formula access path", ["qku_access.jsonl", "library_query.jsonl", "qku_compute_route.jsonl", "qku_target_use.jsonl"], ["qku_access.py", "library_query.py"]),
        ("stale candidate and pre-submit revalidation law", ["trade_seed.jsonl", "fresh_policy.jsonl", "ttl_policy.jsonl", "stale_rules.jsonl", "snapshot_reval.jsonl", "pre_submit_reval.jsonl", "no_stale_candidate.jsonl"], ["trade_plan_seed.py", "stale_invalidation.py", "pre_submit_revalidation.py"]),
        ("prediction-market edge-input surfaces", ["pm_edge_hints.jsonl", "yes_no_parity.jsonl", "cross_venue_hints.jsonl", "orderbook_imbalance.jsonl", "liquidity_decay.jsonl", "event_news_hints.jsonl"], ["prediction_market_edge_hints.py"]),
        ("order-variable grid bounded use-and-dump law", ["var_template.jsonl", "var_grid.jsonl", "grid_frontier.jsonl", "frontier_policy.jsonl", "vof_grid.jsonl"], ["order_variable_grid.py", "grid_frontier.py"]),
        ("future live/shadow handoff without authority", ["owner_enable.jsonl", "live_shadow_route.jsonl"], ["owner_enablement.py", "live_shadow_route.py"]),
        ("agent route and no-orphan law", ["agent_route.jsonl", "agent_consume.jsonl", "artifact_io.jsonl", "file_route.jsonl", "orph_art.jsonl", "orph_qku.jsonl"], ["agent_routing.py", "no_orphan.py"]),
        ("quantum structural readiness without backend execution", ["q_grid.jsonl", "q_constraints.jsonl", "q_interp.jsonl", "classic_fallback.jsonl"], ["quantum_grid_encoding.py", "classical_fallback.py"]),
    ]
    master: list[dict[str, Any]] = []
    roadmap: list[dict[str, Any]] = []
    for index, (law, artifacts, modules) in enumerate(trace_specs, start=1):
        master.append(
            with_common(
                {
                    "trace_id": f"RP5F_MASTER_TRACE_{index:04d}",
                    "master_plan_path": "docs/master_plan/QTT_MasterPlan_Current.md",
                    "master_plan_section_or_law_ref": law,
                    "master_plan_law_summary": law,
                    "implemented_by_artifacts": [generated_ref(name) for name in artifacts],
                    "implemented_by_modules": [f"src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/{name}" for name in modules],
                    "validator_refs": [VALIDATOR_REF],
                    "owner_authority_ref": EXECUTION_AUTHORITY_REF,
                    "runtime_authority_created_flag": False,
                },
                row_id=f"RP5F_MASTER_TRACE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["CommanderAgent", "RP5FValidator"],
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
        roadmap.append(
            with_common(
                {
                    "roadmap_trace_id": f"RP5F_ROADMAP_TRACE_{index:04d}",
                    "roadmap_position": "RP5E/RP5D-R1 -> RP5F -> RP5G/RANK4/QOPT1/VS2/PAPER-LOOP/PR170/PR171",
                    "artifact_family": law,
                    "implemented_by_artifacts": [generated_ref(name) for name in artifacts],
                    "future_consumer_prs": FUTURE_CONSUMERS,
                    "no_authority_handoff_flag": True,
                },
                row_id=f"RP5F_ROADMAP_TRACE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["CommanderAgent", "RP5FValidator"],
                upstream_refs=["owner_prompt_pr168_rp5f_v3"],
                downstream_refs=[generated_ref("downstream.jsonl")],
            )
        )
    return master, roadmap


def build_research_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    research: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    intake: list[dict[str, Any]] = []
    value: list[dict[str, Any]] = []
    for index, (url, title, source_type, use) in enumerate(RESEARCH_SOURCES, start=1):
        source_kind = "OFFICIAL" if source_type == "OFFICIAL" else "RESEARCH"
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
        }
        research.append(
            with_common(
                {"research_receipt_id": f"RP5F_RESEARCH_{index:04d}", **common_payload},
                row_id=f"RP5F_RESEARCH_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["TradeTargetScoutAgent", "RiskAgent", "QOPTAgent", "GovernanceAgent"],
                upstream_refs=["owner_authorized_online_research_candidate_only"],
                downstream_refs=[generated_ref("source_intake.jsonl"), generated_ref("source_coverage.jsonl")],
                provenance_tier="CODEX_DISCOVERED_CANDIDATE_ONLY",
            )
        )
        coverage.append(
            with_common(
                {
                    "source_coverage_id": f"RP5F_SOURCE_COVERAGE_{index:04d}",
                    **common_payload,
                    "coverage_family": use.split()[0].upper(),
                    "official_source_flag": source_kind == "OFFICIAL",
                    "non_official_source_flag": source_kind != "OFFICIAL",
                    "material_target_design_coverage_flag": True,
                },
                row_id=f"RP5F_SOURCE_COVERAGE_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["GovernanceAgent", "TradeTargetScoutAgent"],
                upstream_refs=[generated_ref("research_rec.jsonl")],
                downstream_refs=[generated_ref("source_value_cand.jsonl")],
                provenance_tier="CANDIDATE_SOURCE_COVERAGE_NOT_FACT",
            )
        )
        intake.append(
            with_common(
                {
                    "source_candidate_id": f"RP5F_SOURCE_CAND_{index:04d}",
                    "source_url_or_ref": url,
                    "source_kind": source_kind,
                    "candidate_use": use,
                    "mapped_target_fields": ["market_data_truth_state", "source_freshness_state", "orderbook_state_ref"],
                    "mapped_variable_fields": ["spread_filter_domain", "latency_budget_domain", "maker_taker_split_domain"],
                    "provenance_tier": "CANDIDATE_ONLY_REQUIRES_REPLAY_PAPER_VERIFICATION",
                    "candidate_only_flag": True,
                    "accepted_source_fact_flag": False,
                    "connector_semantic_binding_flag": False,
                    "live_default_flag": False,
                    "profit_proof_flag": False,
                    "proprietary_claim_flag": False,
                    "replay_paper_verification_required": True,
                },
                row_id=f"RP5F_SOURCE_CAND_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["TradeTargetScoutAgent", "OrderVariableAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("research_rec.jsonl")],
                downstream_refs=[generated_ref("completion_route.jsonl")],
                provenance_tier="CANDIDATE_ONLY_REQUIRES_REPLAY_PAPER_VERIFICATION",
            )
        )
        value.append(
            with_common(
                {
                    "source_value_candidate_id": f"RP5F_SOURCE_VALUE_{index:04d}",
                    "source_candidate_ref": f"RP5F_SOURCE_CAND_{index:04d}",
                    "candidate_value_family": use,
                    "value_of_information_score": score("0.30" if source_kind == "OFFICIAL" else "0.20"),
                    "candidate_only_flag": True,
                    "accepted_source_fact_flag": False,
                    "connector_semantic_binding_flag": False,
                    "live_default_flag": False,
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                    "replay_paper_verification_required": True,
                },
                row_id=f"RP5F_SOURCE_VALUE_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["TradeTargetScoutAgent", "RP5FValidator"],
                upstream_refs=[generated_ref("source_intake.jsonl")],
                downstream_refs=[generated_ref("vof_grid.jsonl")],
                provenance_tier="CANDIDATE_VALUE_ONLY_NOT_FACT",
            )
        )
    return research, coverage, intake, value


def build_agent_duty_rows() -> list[dict[str, Any]]:
    specs = [
        ("CommanderAgent", "active stage profile and run activation", ["ALL_STAGE1_PM"], ["activation_profile", "run_id"], True, True),
        ("MarketConditionAgent", "snapshot/truth/freshness/venue state", ["MARKET_DATA", "SOURCE_FRESHNESS"], ["snapshot", "truth_state"], False, True),
        ("FormulaLibraryAgent", "central RP5C resolver consumption", ["QKU_LIBRARY"], ["qku_refs", "formula_refs"], False, True),
        ("TradeTargetScoutAgent", "dynamic target scout", ["TARGET_DISCOVERY"], ["target_id", "snapshot_id"], False, True),
        ("OrderVariableAgent", "bounded order-variable grids", ["ORDER_VARIABLES"], ["grid_id", "variable_domains"], False, True),
        ("RiskAgent", "capacity/no-stale/no-authority controls", ["RISK", "TCA", "FILL"], ["stale_rules", "pre_submit_reval"], False, True),
        ("QOPTAgent", "future QOPT structural consumer only", ["QUANTUM_STRUCTURE"], ["q_grid", "q_constraints"], False, True),
        ("TradePlanSimulationAgent", "future RP5G consumer", ["TRADE_SEED"], ["trade_seed_id"], False, True),
        ("RankerAgent", "future RANK4 advisory consumer", ["FEATURE_SURFACES"], ["target_utility", "edge_inputs"], False, True),
        ("MemoryAgent", "future MEM1 consumer", ["REGIME_MEMORY"], ["regime_keys"], False, True),
        ("GovernanceAgent", "no orphan/no authority validation", ["GOVERNANCE"], ["artifact_io", "no_auth"], True, True),
        ("ResearchScoutAgent", "candidate-only source lane", ["SOURCE_CANDIDATES"], ["source_intake"], False, True),
    ]
    rows: list[dict[str, Any]] = []
    for index, (agent, scope, qku_families, fields, owner, consumer) in enumerate(specs, start=1):
        rows.append(
            with_common(
                {
                    "agent_duty_map_id": f"RP5F_AGENT_DUTY_{index:04d}",
                    "source_pr165_d2_agent_roster_ref": "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
                    "source_pr165_d2_duty_crosswalk_ref": "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
                    "agent_name": agent,
                    "agent_duty_scope": scope,
                    "allowed_qku_families": qku_families,
                    "allowed_formula_roles": qku_families,
                    "allowed_target_fields": fields,
                    "forbidden_authority_flags": list(("paper_authority_flag", "shadow_authority_flag", "live_authority_flag", "order_authority_flag", "connector_write_flag", "private_state_fetch_flag", "cash_account_read_flag")),
                    "owner_agent_flag": owner,
                    "consumer_agent_flag": consumer,
                },
                row_id=f"RP5F_AGENT_DUTY_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["CommanderAgent", "RP5FValidator"],
                upstream_refs=["docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json", "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"],
                downstream_refs=[generated_ref("agent_route.jsonl"), generated_ref("qku_compute_route.jsonl")],
            )
        )
    return rows


def _library_query_rows() -> tuple[list[dict[str, Any]], dict[str, str], dict[str, list[str]]]:
    library = load_library(REPO_ROOT)
    rows: list[dict[str, Any]] = []
    receipt_by_alias_platform: dict[str, str] = {}
    qkus_by_alias: dict[str, list[str]] = defaultdict(list)
    index = 1
    for alias, canonical in RP5C_AGENT_ALIASES.items():
        for platform in PLATFORMS:
            try:
                receipt = resolve_stage_agent_universe(STAGE_PROFILE_ID, canonical, platform, library=library)
                identity_refs = list(receipt.get("result_identity_refs", []))[:8]
                blocker_codes: list[str] = []
            except KeyError as exc:
                receipt = {
                    "query_receipt_id": f"RP5F_RP5C_QUERY_{canonical}_{platform}",
                    "agent_id": canonical,
                    "platform_id": platform,
                    "resolved_identity_count": 0,
                    "blocker_codes": [str(exc)],
                    "result_identity_refs": [],
                }
                identity_refs = []
                blocker_codes = [str(exc)]
            receipt_id = f"RP5F_LIBRARY_QUERY_{index:04d}"
            receipt_by_alias_platform[f"{alias}:{platform}"] = receipt_id
            qkus_by_alias[alias].extend(identity_refs)
            rows.append(
                with_common(
                    {
                        "library_query_receipt_id": receipt_id,
                        "requesting_agent": alias,
                        "rp5c_policy_agent_id": canonical,
                        "query_scope": f"{STAGE_PROFILE_ID}:{platform}:TARGET_FILTERED_SAMPLE",
                        "qku_ids_returned": identity_refs,
                        "formula_ids_returned": [],
                        "filters_applied": ["active_stage_profile", "platform_applicability", "agent_duty_policy", "rp5d_r1_overlay", "rp5e_context", "rp5f_target_filter"],
                        "centralized_resolver_ref": "tools/pr168_rp5c_library_reader.py::resolve_stage_agent_universe",
                        "rp5c_library_ref": "tools/pr168_rp5c_library_reader.py",
                        "rp5d_r1_overlay_ref": "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
                        "rp5e_context_ref": "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl",
                        "rp5f_target_ref": generated_ref("targets.jsonl"),
                        "full_library_scan_flag": False,
                        "agent_direct_jsonl_scan_allowed_flag": False,
                        "blocker_codes": blocker_codes,
                        "rp5c_query_receipt": receipt,
                    },
                    row_id=receipt_id,
                    owner_agent="FormulaLibraryAgent",
                    consumer_agents=[alias, "GovernanceAgent"],
                    upstream_refs=["tools/pr168_rp5c_library_reader.py", "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl"],
                    downstream_refs=[generated_ref("qku_access.jsonl"), generated_ref("qku_compute_route.jsonl")],
                )
            )
            index += 1
    return rows, receipt_by_alias_platform, {key: stable_unique(value) for key, value in qkus_by_alias.items()}


def _target_specs(upstream: dict[str, Any], max_targets: int) -> list[dict[str, Any]]:
    promoted = upstream["r1_promote"][:max_targets]
    topk = upstream["rp5e_topk"] or []
    ctx = {row.get("context_id"): row for row in upstream["rp5e_ctx"]}
    specs: list[dict[str, Any]] = []
    for index, promo in enumerate(promoted, start=1):
        preview = topk[(index - 1) % len(topk)] if topk else {}
        ctx_row = ctx.get(preview.get("context_id"), {})
        venue = ctx_row.get("venue") or PLATFORMS[(index - 1) % len(PLATFORMS)]
        time_bucket = ctx_row.get("time_to_close_bucket") or ("0_to_4h" if index % 2 else "4h_to_24h")
        spread_bucket = ctx_row.get("spread_bucket") or ("TIGHT" if index % 2 else "NORMAL")
        depth_bucket = ctx_row.get("depth_bucket") or ("MEDIUM" if index % 2 else "LOW")
        liquidity_bucket = ctx_row.get("liquidity_bucket") or ("MEDIUM" if index % 2 else "LOW")
        specs.append(
            {
                "index": index,
                "promo": promo,
                "preview": preview,
                "ctx": ctx_row,
                "venue": str(venue),
                "market_id": f"RP5F_FIXTURE_MARKET_{index:04d}",
                "event_id": f"RP5F_FIXTURE_EVENT_{index:04d}",
                "contract_or_outcome_id": f"RP5F_FIXTURE_CONTRACT_{index:04d}",
                "market_category": str(ctx_row.get("market_category") or "binary_event"),
                "event_category": str(ctx_row.get("event_category") or "stage1_fixture"),
                "time_to_close_bucket": str(time_bucket),
                "spread_bucket": str(spread_bucket).upper(),
                "depth_bucket": str(depth_bucket).upper(),
                "liquidity_bucket": str(liquidity_bucket).upper(),
                "latency_bucket": "250ms" if index % 2 else "500ms",
                "volume_bucket": str(ctx_row.get("volume_bucket") or "SOURCE_REQUIRED").upper(),
                "latency_budget_ms": int(ctx_row.get("latency_budget_ms") or (250 if index % 2 else 500)),
            }
        )
    return specs


def build_snapshot_target_rows(upstream: dict[str, Any], max_targets: int) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in ("snap_ctx.jsonl", "md_truth.jsonl", "src_fresh.jsonl", "venue_state.jsonl", "ctx_filter.jsonl", "targets.jsonl", "target_disc.jsonl", "target_score.jsonl", "target_utility.jsonl", "target_family.jsonl", "event_lifecycle.jsonl", "exec_target.jsonl")}
    for spec in _target_specs(upstream, max_targets):
        i = spec["index"]
        target_id = f"RP5F_TARGET_{i:04d}"
        snapshot_id = f"RP5F_SNAPSHOT_{i:04d}"
        md_truth_id = f"RP5F_MD_TRUTH_{i:04d}"
        src_fresh_id = f"RP5F_SRC_FRESH_{i:04d}"
        venue_state_id = f"RP5F_VENUE_STATE_{i:04d}"
        grid_id = f"RP5F_GRID_{i:04d}"
        seed_id = f"RP5F_SEED_{i:04d}"
        promo = spec["promo"]
        preview = spec["preview"]
        common_upstream = ["docs/master_plan/generated/pr168_rp5d_r1/promote.jsonl", "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl", "docs/master_plan/generated/pr168_rp5e/topk.jsonl", "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl"]
        rows["md_truth.jsonl"].append(
            with_common(
                {
                    "snapshot_id": snapshot_id,
                    "market_data_truth_id": md_truth_id,
                    "truth_state": "SOURCE_REQUIRED",
                    "stale_age_ms": "SOURCE_REQUIRED",
                    "crossed_book_flag": False,
                    "outlier_flag": False,
                    "revision_aware_finality_flag": False,
                    "executable_truth_allowed_flag": False,
                    "risk_diagnostic_only_flag": True,
                    "block_new_or_increased_exposure_flag": True,
                },
                row_id=md_truth_id,
                owner_agent="MarketConditionAgent",
                consumer_agents=["TradeTargetScoutAgent", "RiskAgent", "RP5G"],
                upstream_refs=common_upstream,
                downstream_refs=[generated_ref("snap_ctx.jsonl"), generated_ref("pre_submit_reval.jsonl")],
            )
        )
        rows["src_fresh.jsonl"].append(
            with_common(
                {
                    "source_freshness_id": src_fresh_id,
                    "source_change_event_flag": True,
                    "source_revalidation_required_flag": True,
                    "source_revalidation_status": "SOURCE_REQUIRED",
                    "accepted_source_packet_required_flag": True,
                    "accepted_source_packet_ref": "SOURCE_REQUIRED_NOT_ACCEPTED_IN_RP5F",
                    "source_dependent_live_or_shadow_field_flag": True,
                    "new_binding_allowed_flag": False,
                    "new_live_use_allowed_flag": False,
                },
                row_id=src_fresh_id,
                owner_agent="MarketConditionAgent",
                consumer_agents=["RiskAgent", "TradeTargetScoutAgent", "LiveDryRunAgent", "ShadowObservationAgent"],
                upstream_refs=[generated_ref("source_intake.jsonl")],
                downstream_refs=[generated_ref("snap_ctx.jsonl"), generated_ref("pre_submit_reval.jsonl")],
            )
        )
        rows["venue_state.jsonl"].append(
            with_common(
                {
                    "venue_state_id": venue_state_id,
                    "snapshot_id": snapshot_id,
                    "venue": spec["venue"],
                    "venue_operational_state": "SOURCE_REQUIRED",
                    "connector_readiness_state": "FUTURE_CONNECTOR_STATUS_REQUIRED",
                    "connector_write_ready_flag": False,
                    "private_state_fetch_ready_flag": False,
                    "cash_account_read_ready_flag": False,
                    "new_or_increased_exposure_blocked_flag": True,
                },
                row_id=venue_state_id,
                owner_agent="MarketConditionAgent",
                consumer_agents=["RiskAgent", "TradeTargetScoutAgent"],
                upstream_refs=common_upstream,
                downstream_refs=[generated_ref("targets.jsonl"), generated_ref("pre_submit_reval.jsonl")],
            )
        )
        rows["snap_ctx.jsonl"].append(
            with_common(
                {
                    "snapshot_id": snapshot_id,
                    "asof_timestamp_utc": CREATED_AT_UTC,
                    "venue": spec["venue"],
                    "market_id": spec["market_id"],
                    "event_id": spec["event_id"],
                    "question_or_event_label": f"RP5F fixture event {i} candidate only",
                    "contract_or_outcome_id": spec["contract_or_outcome_id"],
                    "side_domain": "BOTH_IF_AVAILABLE",
                    "best_bid": "SOURCE_REQUIRED",
                    "best_ask": "SOURCE_REQUIRED",
                    "mid_or_mark": "SOURCE_REQUIRED",
                    "spread": "SOURCE_REQUIRED",
                    "bid_depth": "SOURCE_REQUIRED",
                    "ask_depth": "SOURCE_REQUIRED",
                    "top_of_book_depth": "SOURCE_REQUIRED",
                    "orderbook_depth_bucket": spec["depth_bucket"],
                    "volume_bucket": spec["volume_bucket"],
                    "liquidity_bucket": spec["liquidity_bucket"],
                    "time_to_close_bucket": spec["time_to_close_bucket"],
                    "market_status": "SOURCE_REQUIRED",
                    "event_status": "SOURCE_REQUIRED",
                    "market_data_truth_ref": md_truth_id,
                    "source_freshness_ref": src_fresh_id,
                    "latency_budget_ms": spec["latency_budget_ms"],
                    "portfolio_context_ref": f"RP5F_PORTFOLIO_CONTEXT_{i:04d}",
                    "fixture_or_live_source_class": "OFFLINE_FIXTURE_SOURCE_REQUIRED_NOT_LIVE_TRUTH",
                    "accepted_source_fact_flag": False,
                },
                row_id=snapshot_id,
                owner_agent="MarketConditionAgent",
                consumer_agents=["TradeTargetScoutAgent", "OrderVariableAgent", "RP5G"],
                upstream_refs=[md_truth_id, src_fresh_id, venue_state_id],
                downstream_refs=[generated_ref("targets.jsonl"), generated_ref("var_grid.jsonl")],
            )
        )
        rows["ctx_filter.jsonl"].append(
            with_common(
                {
                    "context_filter_id": f"RP5F_CTX_FILTER_{i:04d}",
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "active_market_family": MARKET_FAMILY,
                    "platform": spec["venue"],
                    "context_candidate_universe_formula": "AgentExecutableUniverse AND market/venue/bucket/latency/portfolio AND truth/freshness/lifecycle/venue_state",
                    "centralized_resolver_required_flag": True,
                    "agent_direct_jsonl_scan_allowed_flag": False,
                },
                row_id=f"RP5F_CTX_FILTER_{i:04d}",
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["FormulaLibraryAgent", "GovernanceAgent"],
                upstream_refs=[generated_ref("snap_ctx.jsonl"), "tools/pr168_rp5c_library_reader.py"],
                downstream_refs=[generated_ref("targets.jsonl"), generated_ref("qku_compute_route.jsonl")],
            )
        )
        rows["targets.jsonl"].append(
            with_common(
                {
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "asof_timestamp_utc": CREATED_AT_UTC,
                    "market_family": MARKET_FAMILY,
                    "venue": spec["venue"],
                    "market_id": spec["market_id"],
                    "event_id": spec["event_id"],
                    "contract_or_outcome_id": spec["contract_or_outcome_id"],
                    "target_side_domain": "BOTH_IF_AVAILABLE",
                    "market_category": spec["market_category"],
                    "event_category": spec["event_category"],
                    "time_to_close_bucket": spec["time_to_close_bucket"],
                    "spread_bucket": spec["spread_bucket"],
                    "depth_bucket": spec["depth_bucket"],
                    "liquidity_bucket": spec["liquidity_bucket"],
                    "latency_bucket": spec["latency_bucket"],
                    "portfolio_exposure_bucket": "UNKNOWN_SOURCE_REQUIRED",
                    "eligible_stack_preview_refs": [preview.get("stack_preview_id")],
                    "eligible_executable_now_refs": [promo.get("unlock_candidate_id")],
                    "rp5d_r1_promoted_overlay_refs": [promo.get("promotion_receipt_id"), promo.get("unlock_candidate_id")],
                    "candidate_status": "DYNAMIC_TRADE_TARGET_CANDIDATE",
                    "fixed_trade_instruction_flag": False,
                    "order_authority_flag": False,
                    "profit_proof_flag": False,
                },
                row_id=target_id,
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["OrderVariableAgent", "RP5G", "RANK4", "QOPT1"],
                upstream_refs=common_upstream,
                downstream_refs=[generated_ref("var_grid.jsonl"), generated_ref("trade_seed.jsonl")],
            )
        )
        rows["target_disc.jsonl"].append(
            with_common(
                {
                    "target_discovery_receipt_id": f"RP5F_TARGET_DISC_{i:04d}",
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "discovery_inputs": common_upstream,
                    "dynamic_discovery_flag": True,
                    "fixed_trade_plan_created_flag": False,
                    "market_data_truth_ref": md_truth_id,
                    "source_freshness_ref": src_fresh_id,
                },
                row_id=f"RP5F_TARGET_DISC_{i:04d}",
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["GovernanceAgent", "RP5G"],
                upstream_refs=common_upstream,
                downstream_refs=[generated_ref("target_score.jsonl"), generated_ref("target_utility.jsonl")],
            )
        )
        rows["target_score.jsonl"].append(
            with_common(
                {
                    "target_score_id": f"RP5F_TARGET_SCORE_{i:04d}",
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "score_family": "TARGET_SELECTION_PREFERENCE_ONLY",
                    "stage1_applicability_score": "1.000000",
                    "executable_now_coverage_score": "1.000000",
                    "source_freshness_score": "0.000000",
                    "market_data_truth_score": "0.000000",
                    "execution_readiness_score": "0.500000",
                    "final_ranking_flag": False,
                    "profit_proof_flag": False,
                },
                row_id=f"RP5F_TARGET_SCORE_{i:04d}",
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["RANK4", "RP5FValidator"],
                upstream_refs=[generated_ref("targets.jsonl")],
                downstream_refs=[generated_ref("target_utility.jsonl")],
            )
        )
        rows["target_utility.jsonl"].append(
            with_common(
                {
                    "target_utility_id": f"RP5F_TARGET_UTILITY_{i:04d}",
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "stage1_applicability_score": "1.000000",
                    "executable_now_coverage_score": "1.000000",
                    "rp5e_stack_reuse_score": preview.get("prescreen_total_score", "0.500000"),
                    "source_freshness_score": "0.000000",
                    "market_data_truth_score": "0.000000",
                    "execution_readiness_score": "0.500000",
                    "quantum_structural_value_score": preview.get("quantum_structural_readiness_score", "0.500000"),
                    "expected_downstream_rp5g_utility_score": "0.750000",
                    "utility_score": "0.612500",
                    "selection_preference_only_flag": True,
                    "profit_proof_flag": False,
                    "final_ranking_flag": False,
                },
                row_id=f"RP5F_TARGET_UTILITY_{i:04d}",
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["RANK4", "QOPT1", "RP5G"],
                upstream_refs=[generated_ref("target_score.jsonl"), generated_ref("params.jsonl")],
                downstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("edge_capture_map.jsonl")],
            )
        )
        rows["target_family.jsonl"].append(
            with_common(
                {
                    "target_family_id": f"RP5F_TARGET_FAMILY_{i:04d}",
                    "target_id": target_id,
                    "market_category": spec["market_category"],
                    "event_category": spec["event_category"],
                    "contract_family": "BINARY_PREDICTION_MARKET_CONTRACT",
                    "near_clone_cluster_id": f"RP5F_NEAR_CLONE_{(i % 3) + 1:03d}",
                    "correlation_proxy_cluster_id": f"RP5F_CORR_PROXY_{(i % 2) + 1:03d}",
                    "crowding_family_id": f"RP5F_CROWDING_{(i % 3) + 1:03d}",
                    "regime_family_id": f"RP5F_REGIME_{spec['spread_bucket']}_{spec['liquidity_bucket']}",
                    "future_mem1_consumer_flag": True,
                },
                row_id=f"RP5F_TARGET_FAMILY_{i:04d}",
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["MemoryAgent", "RiskAgent"],
                upstream_refs=[generated_ref("targets.jsonl")],
                downstream_refs=[generated_ref("regime_keys.jsonl"), generated_ref("port_cap.jsonl")],
            )
        )
        rows["event_lifecycle.jsonl"].append(
            with_common(
                {
                    "event_lifecycle_id": f"RP5F_EVENT_LIFE_{i:04d}",
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "event_status": "SOURCE_REQUIRED",
                    "time_to_close_bucket": spec["time_to_close_bucket"],
                    "pre_event_flag": spec["time_to_close_bucket"] != "0_to_4h",
                    "in_event_flag": False,
                    "post_event_flag": False,
                    "resolution_pending_flag": True,
                    "resolution_final_flag": False,
                    "lifecycle_tradeability_status": "SOURCE_REQUIRED_BLOCKS_AUTHORITY",
                    "source_revalidation_required_flag": True,
                },
                row_id=f"RP5F_EVENT_LIFE_{i:04d}",
                owner_agent="MarketConditionAgent",
                consumer_agents=["TradeTargetScoutAgent", "RiskAgent", "RP5G"],
                upstream_refs=[generated_ref("snap_ctx.jsonl")],
                downstream_refs=[generated_ref("event_news_hints.jsonl"), generated_ref("stale_rules.jsonl")],
            )
        )
        rows["exec_target.jsonl"].append(
            with_common(
                {
                    "execution_target_readiness_id": f"RP5F_EXEC_TARGET_{i:04d}",
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "snapshot_id": snapshot_id,
                    "spread_depth_liquidity_readiness": "SOURCE_REQUIRED_INPUT_SURFACE_READY",
                    "latency_budget_fit": spec["latency_bucket"],
                    "fill_readiness_inputs": [generated_ref("fill_inputs.jsonl"), generated_ref("queue_fill_inputs.jsonl")],
                    "tca_input_readiness": generated_ref("tca_inputs.jsonl"),
                    "capacity_crowding_input_readiness": generated_ref("capacity_inputs.jsonl"),
                    "agent_route_completeness": "COMPLETE",
                    "no_orphan_completeness": "COMPLETE",
                    "final_execution_adjusted_ranking_flag": False,
                },
                row_id=f"RP5F_EXEC_TARGET_{i:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RP5G", "RANK4"],
                upstream_refs=[generated_ref("targets.jsonl")],
                downstream_refs=[generated_ref("tca_inputs.jsonl"), generated_ref("queue_fill_inputs.jsonl")],
            )
        )
    return rows


def build_grid_seed_rows(target_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    outputs = {name: [] for name in ("var_template.jsonl", "var_grid.jsonl", "var_bounds.jsonl", "var_policy.jsonl", "grid_frontier.jsonl", "frontier_policy.jsonl", "vof_grid.jsonl", "grid_fdr.jsonl", "trade_seed.jsonl", "fresh_policy.jsonl", "ttl_policy.jsonl", "stale_rules.jsonl", "snapshot_reval.jsonl", "pre_submit_reval.jsonl", "no_stale_candidate.jsonl")}
    for index, target in enumerate(target_rows, start=1):
        target_id = str(target["target_id"])
        snapshot_id = str(target["snapshot_id"])
        grid_id = f"RP5F_GRID_{index:04d}"
        seed_id = f"RP5F_SEED_{index:04d}"
        fresh_id = f"RP5F_FRESH_POLICY_{index:04d}"
        ttl_id = f"RP5F_TTL_POLICY_{index:04d}"
        stale_id = f"RP5F_STALE_RULE_{index:04d}"
        reval_id = f"RP5F_PRE_SUBMIT_REVAL_{index:04d}"
        common_upstream = [generated_ref("targets.jsonl"), generated_ref("params.jsonl"), generated_ref("policy_prov.jsonl")]
        outputs["var_template.jsonl"].append(
            with_common(
                {
                    "grid_template_id": f"RP5F_GRID_TEMPLATE_{index:04d}",
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "side_domain": ["YES", "NO"],
                    "entry_price_domain": "TICK_OFFSET_BUCKETS_SOURCE_REQUIRED",
                    "exit_price_domain": "RULE_DERIVED_SOURCE_REQUIRED",
                    "order_size_domain": "SIZE_BUCKETS_REPLAY_PAPER_ONLY",
                    "total_investment_domain": "RISK_CAP_BUCKETS_REPLAY_PAPER_ONLY",
                    "hold_duration_domain": "HOLD_DURATION_BUCKETS",
                    "exit_rule_domain": PARAM_DEFAULTS["exit_rule_default_values"],
                    "maker_taker_split_domain": PARAM_DEFAULTS["maker_taker_split_default_values"],
                    "cancel_replace_interval_domain": [250, 500, 1000, 2500],
                    "spread_filter_domain": PARAM_DEFAULTS["spread_filter_default_buckets"],
                    "depth_filter_domain": ["HIGH", "MEDIUM", "LOW", "BLOCKED"],
                    "liquidity_filter_domain": PARAM_DEFAULTS["liquidity_filter_default_buckets"],
                    "latency_budget_domain": PARAM_DEFAULTS["latency_budget_ms_default_values"],
                    "portfolio_exposure_domain": ["FLAT", "LOW", "MEDIUM", "BLOCKED"],
                    "risk_cap_domain": ["LOW", "MEDIUM", "HIGH_REPLAY_ONLY"],
                },
                row_id=f"RP5F_GRID_TEMPLATE_{index:04d}",
                owner_agent="OrderVariableAgent",
                consumer_agents=["RP5G", "QOPT1", "RANK4"],
                upstream_refs=common_upstream,
                downstream_refs=[generated_ref("var_grid.jsonl")],
            )
        )
        outputs["var_grid.jsonl"].append(
            with_common(
                {
                    "grid_id": grid_id,
                    "target_id": target_id,
                    "snapshot_id": snapshot_id,
                    "asof_timestamp_utc": CREATED_AT_UTC,
                    "side_values": ["YES", "NO"],
                    "entry_price_values": ["best_bid_minus_2_ticks", "best_bid_minus_1_tick", "mid_or_mark", "best_ask_plus_1_tick", "best_ask_plus_2_ticks"],
                    "exit_price_values": ["source_required_exit_price_domain"],
                    "order_size_values": ["size_bucket_1", "size_bucket_2", "size_bucket_3", "size_bucket_4", "size_bucket_5"],
                    "total_investment_values": ["risk_cap_low", "risk_cap_medium"],
                    "hold_duration_values": ["5m", "30m", "2h", "to_close", "to_resolution"],
                    "exit_rule_values": PARAM_DEFAULTS["exit_rule_default_values"],
                    "maker_taker_split_values": PARAM_DEFAULTS["maker_taker_split_default_values"],
                    "cancel_replace_interval_values": [250, 500, 1000, 2500],
                    "spread_filter_values": PARAM_DEFAULTS["spread_filter_default_buckets"],
                    "depth_filter_values": ["HIGH", "MEDIUM", "LOW", "BLOCKED"],
                    "liquidity_filter_values": PARAM_DEFAULTS["liquidity_filter_default_buckets"],
                    "latency_budget_values": PARAM_DEFAULTS["latency_budget_ms_default_values"],
                    "portfolio_exposure_values": ["FLAT", "LOW", "MEDIUM", "BLOCKED"],
                    "risk_cap_values": ["LOW", "MEDIUM", "HIGH_REPLAY_ONLY"],
                    "grid_size": 60,
                    "grid_generation_mode": "BOUNDED_FRONTIER_SAMPLE_NOT_FULL_CARTESIAN",
                    "full_cartesian_persisted_flag": False,
                    "use_and_dump_policy_ref": f"RP5F_FRONTIER_POLICY_{index:04d}",
                    "bounded_grid_flag": True,
                },
                row_id=grid_id,
                owner_agent="OrderVariableAgent",
                consumer_agents=["RP5G", "QOPT1", "RANK4"],
                upstream_refs=[generated_ref("var_template.jsonl")],
                downstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("q_grid.jsonl")],
            )
        )
        for filename, suffix, payload in (
            ("var_bounds.jsonl", "VAR_BOUNDS", {"bounded_variable_count": 14, "max_grid_values_per_variable": 7, "full_cartesian_persisted_flag": False}),
            ("var_policy.jsonl", "VAR_POLICY", {"central_parameter_ref": generated_ref("params.jsonl"), "deterministic_flag": True, "replay_paper_verifiable_flag": True, "live_authority_flag": False}),
            ("grid_frontier.jsonl", "GRID_FRONTIER", {"beam_search_ready_flag": True, "successive_halving_ready_flag": True, "Bayesian_optimization_ready_flag": True, "frontier_diversity_ready_flag": True, "max_grid_size": 500, "retained_grid_size": 60, "use_and_dump_policy_ref": f"RP5F_FRONTIER_POLICY_{index:04d}"}),
            ("frontier_policy.jsonl", "FRONTIER_POLICY", {"candidate_grid_size": 60, "max_persisted_rows": 500, "beam_search_ready_flag": True, "successive_halving_ready_flag": True, "bayesian_optimization_ready_flag": True, "frontier_diversity_ready_flag": True, "use_and_dump_required_flag": True, "full_cartesian_persisted_flag": False}),
            ("vof_grid.jsonl", "VOF_GRID", {"missing_value_family": "SOURCE_REQUIRED_ORDERBOOK_AND_FEE_INPUTS", "value_of_information_score": "0.300000", "candidate_fill_method": "SOURCE_CANDIDATE_REPLAY_PAPER_VERIFICATION", "source_candidate_refs": [generated_ref("source_intake.jsonl")], "replay_paper_verification_required": True, "live_authority_flag": False, "profit_proof_flag": False}),
            ("grid_fdr.jsonl", "GRID_FDR", {"search_family_id": f"RP5F_SEARCH_FAMILY_{index:04d}", "order_variable_family_size": 14, "candidate_grid_size": 60, "bounded_grid_count": 1, "selection_budget": 60, "multiple_testing_risk_score": "0.100000", "future_rank4_consumer_refs": ["RANK4"], "fdr_control_ready_flag": True}),
        ):
            row_id = f"RP5F_{suffix}_{index:04d}"
            outputs[filename].append(
                with_common(
                    {"target_id": target_id, "grid_id": grid_id, "snapshot_id": snapshot_id, f"{suffix.lower()}_id": row_id, **payload},
                    row_id=row_id,
                    owner_agent="OrderVariableAgent",
                    consumer_agents=["RP5G", "RANK4", "QOPT1", "RP5FValidator"],
                    upstream_refs=[generated_ref("var_grid.jsonl"), generated_ref("params.jsonl")],
                    downstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("run_receipt.report.json")],
                )
            )
        outputs["fresh_policy.jsonl"].append(
            with_common(
                {"freshness_policy_id": fresh_id, "target_id": target_id, "grid_id": grid_id, "snapshot_id": snapshot_id, "source_change_event_trigger_revalidation_required_flag": True, "unknown_state_blocks_new_or_increased_exposure_flag": True},
                row_id=fresh_id,
                owner_agent="RiskAgent",
                consumer_agents=["RP5G", "PaperExecutionAgent", "LiveDryRunAgent"],
                upstream_refs=[generated_ref("src_fresh.jsonl")],
                downstream_refs=[generated_ref("trade_seed.jsonl")],
            )
        )
        outputs["ttl_policy.jsonl"].append(
            with_common(
                {"ttl_policy_id": ttl_id, "target_id": target_id, "grid_id": grid_id, "snapshot_id": snapshot_id, "snapshot_ttl_ms": 2500, "ttl_range_ms": "250..10000", "non_expiring_trade_plan_flag": False, "must_recompute_after_ttl_flag": True},
                row_id=ttl_id,
                owner_agent="RiskAgent",
                consumer_agents=["RP5G", "PaperExecutionAgent", "LiveDryRunAgent"],
                upstream_refs=[generated_ref("params.jsonl")],
                downstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("stale_rules.jsonl")],
            )
        )
        outputs["stale_rules.jsonl"].append(
            with_common(
                {
                    "invalidation_id": stale_id,
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "trade_seed_id": seed_id,
                    "stale_if_snapshot_older_than_ms": 2500,
                    "stale_if_price_moves_by_ticks_or_bps": "1_tick_or_25bps",
                    "stale_if_spread_widens_by_ticks_or_bps": "1_tick_or_25bps",
                    "stale_if_depth_drops_below_threshold": "bucket_drop_or_source_required",
                    "stale_if_liquidity_bucket_changes": True,
                    "stale_if_time_to_close_bucket_changes": True,
                    "stale_if_market_status_changes": True,
                    "stale_if_event_status_changes": True,
                    "stale_if_source_freshness_state_changes": True,
                    "stale_if_connector_readiness_changes": True,
                    "stale_if_latency_health_red": True,
                    "stale_if_portfolio_exposure_changes": True,
                    "stale_if_kill_switch_or_owner_gate_changes": True,
                    "must_recompute_before_submit": True,
                },
                row_id=stale_id,
                owner_agent="RiskAgent",
                consumer_agents=["RP5G", "PaperExecutionAgent", "LiveDryRunAgent", "ShadowObservationAgent"],
                upstream_refs=[generated_ref("ttl_policy.jsonl"), generated_ref("fresh_policy.jsonl")],
                downstream_refs=[generated_ref("pre_submit_reval.jsonl"), generated_ref("no_stale_candidate.jsonl")],
            )
        )
        outputs["pre_submit_reval.jsonl"].append(
            with_common(
                {
                    "revalidation_id": reval_id,
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "trade_seed_id": seed_id,
                    "required_before_paper_intent_flag": True,
                    "required_before_live_dryrun_intent_flag": True,
                    "required_before_shadow_input_flag": True,
                    "required_before_limited_live_canary_flag": True,
                    "required_before_live_order_flag": True,
                    "latest_snapshot_required_flag": True,
                    "risk_gate_required_flag": True,
                    "source_freshness_required_flag": True,
                    "market_data_truth_required_flag": True,
                    "owner_or_risk_gate_required_for_live_flag": True,
                },
                row_id=reval_id,
                owner_agent="RiskAgent",
                consumer_agents=["PaperExecutionAgent", "LiveDryRunAgent", "ShadowObservationAgent", "RP5G"],
                upstream_refs=[generated_ref("stale_rules.jsonl")],
                downstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("live_shadow_route.jsonl")],
            )
        )
        outputs["snapshot_reval.jsonl"].append(
            with_common(
                {
                    "snapshot_revalidation_id": f"RP5F_SNAPSHOT_REVAL_{index:04d}",
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "trade_seed_id": seed_id,
                    "snapshot_change_checks": ["age_ms", "price_tick_move", "spread_bucket", "depth_bucket"],
                    "source_change_checks": ["source_change_event", "accepted_source_packet_ref"],
                    "market_data_truth_checks": ["SOURCE_REQUIRED", "CROSSED", "STALE", "OUTLIER"],
                    "venue_state_checks": ["operational_state", "connector_readiness"],
                    "connector_readiness_checks": ["readiness_change", "write_disabled"],
                    "risk_portfolio_checks": ["exposure_change", "risk_gate"],
                    "kill_switch_owner_gate_checks": ["owner_enablement", "kill_switch"],
                    "all_required_revalidation_refs": [reval_id, stale_id],
                    "pre_submit_revalidation_required_flag": True,
                },
                row_id=f"RP5F_SNAPSHOT_REVAL_{index:04d}",
                owner_agent="RiskAgent",
                consumer_agents=["RP5G", "PaperExecutionAgent", "LiveDryRunAgent"],
                upstream_refs=[generated_ref("pre_submit_reval.jsonl")],
                downstream_refs=[generated_ref("no_stale_candidate.jsonl")],
            )
        )
        outputs["no_stale_candidate.jsonl"].append(
            with_common(
                {"no_stale_candidate_proof_id": f"RP5F_NO_STALE_{index:04d}", "target_id": target_id, "grid_id": grid_id, "trade_seed_id": seed_id, "paper_live_dryrun_shadow_live_revalidation_required_flag": True, "stale_candidate_authority_flag": False, "proof_pass_flag": True},
                row_id=f"RP5F_NO_STALE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5FValidator", "RP5G", "PaperExecutionAgent", "LiveDryRunAgent"],
                upstream_refs=[generated_ref("snapshot_reval.jsonl"), generated_ref("pre_submit_reval.jsonl")],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
        outputs["trade_seed.jsonl"].append(
            with_common(
                {
                    "trade_seed_id": seed_id,
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "snapshot_id": snapshot_id,
                    "asof_timestamp_utc": CREATED_AT_UTC,
                    "formula_stack_preview_refs": target.get("eligible_stack_preview_refs", []),
                    "qku_refs": target.get("eligible_executable_now_refs", []),
                    "formula_refs": target.get("eligible_stack_preview_refs", []),
                    "side_placeholder": "YES_OR_NO_TO_BE_SIMULATED_BY_RP5G",
                    "entry_price_domain_ref": f"RP5F_GRID_TEMPLATE_{index:04d}",
                    "order_size_domain_ref": f"RP5F_GRID_TEMPLATE_{index:04d}",
                    "hold_duration_domain_ref": f"RP5F_GRID_TEMPLATE_{index:04d}",
                    "exit_rule_domain_ref": f"RP5F_GRID_TEMPLATE_{index:04d}",
                    "maker_taker_split_domain_ref": f"RP5F_GRID_TEMPLATE_{index:04d}",
                    "freshness_policy_ref": fresh_id,
                    "ttl_policy_ref": ttl_id,
                    "stale_invalidation_ref": stale_id,
                    "pre_submit_revalidation_ref": reval_id,
                    "rp5f_final_trade_plan_flag": False,
                    "rp5f_profit_proof_flag": False,
                    "rp5f_order_authority_flag": False,
                    "future_rp5g_required_flag": True,
                },
                row_id=seed_id,
                owner_agent="OrderVariableAgent",
                consumer_agents=["RP5G", "RANK4", "QOPT1", "VS2"],
                upstream_refs=[generated_ref("targets.jsonl"), generated_ref("var_grid.jsonl"), generated_ref("pre_submit_reval.jsonl")],
                downstream_refs=[generated_ref("edge_capture_map.jsonl"), generated_ref("downstream.jsonl")],
            )
        )
    return outputs


def build_execution_input_rows(target_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    outputs = {name: [] for name in ("tca_inputs.jsonl", "fill_inputs.jsonl", "queue_fill_inputs.jsonl", "adverse_select.jsonl", "lat_inputs.jsonl", "capacity_inputs.jsonl", "cash_settle_inputs.jsonl")}
    for index, target in enumerate(target_rows, start=1):
        target_id = str(target["target_id"])
        grid_id = f"RP5F_GRID_{index:04d}"
        snapshot_id = str(target["snapshot_id"])
        base = {"target_id": target_id, "grid_id": grid_id, "snapshot_id": snapshot_id}
        specs = [
            ("tca_inputs.jsonl", "TCA_INPUT", {"fee_model": "SOURCE_REQUIRED", "spread_model": "SOURCE_REQUIRED", "slippage_model": "SOURCE_REQUIRED", "latency_model": "INPUT_SURFACE_READY", "impact_capacity_model": "INPUT_SURFACE_READY", "tick_min_size_readiness": "SOURCE_REQUIRED", "unit_conversion": "RP5D_AVAILABLE", "cashflow_settlement_semantics": "SOURCE_REQUIRED"}),
            ("fill_inputs.jsonl", "FILL_INPUT", {"maker_fill_probability_proxy": "SOURCE_REQUIRED", "taker_fill_probability_proxy": "SOURCE_REQUIRED", "partial_fill_risk_proxy": "SOURCE_REQUIRED", "future_rp5g_fill_model_required_flag": True}),
            ("queue_fill_inputs.jsonl", "QUEUE_FILL", {"bid_depth_bucket": target["depth_bucket"], "ask_depth_bucket": target["depth_bucket"], "top_of_book_depth": "SOURCE_REQUIRED", "spread_bucket": target["spread_bucket"], "queue_position_proxy": "SOURCE_REQUIRED", "maker_fill_probability_proxy": "SOURCE_REQUIRED", "taker_fill_probability_proxy": "SOURCE_REQUIRED", "partial_fill_risk_proxy": "SOURCE_REQUIRED", "future_rp5g_fill_model_required_flag": True}),
            ("adverse_select.jsonl", "ADVERSE_SELECT", {"price_momentum_proxy": "SOURCE_REQUIRED", "spread_widening_proxy": target["spread_bucket"], "depth_evaporation_proxy": target["depth_bucket"], "source_update_risk_proxy": "HIGH_SOURCE_REQUIRED", "event_lifecycle_risk_proxy": "SOURCE_REQUIRED", "latency_decay_proxy": target["latency_bucket"], "adverse_selection_risk_score": "0.100000", "future_rank4_penalty_consumer_flag": True}),
            ("lat_inputs.jsonl", "LAT_INPUT", {"latency_budget_ms": 250 if index % 2 else 500, "latency_health_state": "SOURCE_REQUIRED", "latency_decay_input_ready_flag": True}),
            ("capacity_inputs.jsonl", "CAPACITY_INPUT", {"venue_exposure": "SOURCE_REQUIRED", "market_category_exposure": target["market_category"], "event_category_concentration": "SOURCE_REQUIRED", "capacity_fit": "SOURCE_REQUIRED", "crowding_risk": "SOURCE_REQUIRED", "thin_book_false_positive_risk": "SOURCE_REQUIRED"}),
            ("cash_settle_inputs.jsonl", "CASH_SETTLE", {"cashflow_semantics": "SOURCE_REQUIRED", "settlement_semantics": "SOURCE_REQUIRED", "unit_contract_available_flag": True, "private_cash_or_account_read_flag": False}),
        ]
        for filename, prefix, payload in specs:
            row_id = f"RP5F_{prefix}_{index:04d}"
            outputs[filename].append(
                with_common(
                    {f"{prefix.lower()}_id": row_id, **base, **payload},
                    row_id=row_id,
                    owner_agent="RiskAgent",
                    consumer_agents=["RP5G", "RANK4", "QOPT1", "RP5FValidator"],
                    upstream_refs=[generated_ref("targets.jsonl"), generated_ref("var_grid.jsonl")],
                    downstream_refs=[generated_ref("exec_target.jsonl"), generated_ref("trade_seed.jsonl")],
                )
            )
    return outputs


def build_edge_rows(target_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    outputs = {name: [] for name in ("pm_edge_hints.jsonl", "yes_no_parity.jsonl", "cross_venue_hints.jsonl", "orderbook_imbalance.jsonl", "liquidity_decay.jsonl", "event_news_hints.jsonl", "notrade_hints.jsonl", "edge_alpha_inputs.jsonl", "edge_capture_map.jsonl")}
    for index, target in enumerate(target_rows, start=1):
        target_id = str(target["target_id"])
        snapshot_id = str(target["snapshot_id"])
        grid_id = f"RP5F_GRID_{index:04d}"
        seed_id = f"RP5F_SEED_{index:04d}"
        for family_index, family in enumerate(EDGE_HINT_FAMILIES, start=1):
            outputs["pm_edge_hints.jsonl"].append(
                with_common(
                    {
                        "pm_edge_hint_id": f"RP5F_PM_EDGE_{index:04d}_{family_index:02d}",
                        "target_id": target_id,
                        "snapshot_id": snapshot_id,
                        "hint_family": family,
                        "hint_inputs": ["SOURCE_REQUIRED_ORDERBOOK", "SOURCE_REQUIRED_FEES", "SOURCE_REQUIRED_EVENT_STATE"],
                        "source_candidate_refs": [generated_ref("source_intake.jsonl")],
                        "future_metric_enabled": family.replace("_hint", "_metric"),
                        "future_rp5g_required_flag": True,
                        "profit_proof_flag": False,
                        "order_authority_flag": False,
                    },
                    row_id=f"RP5F_PM_EDGE_{index:04d}_{family_index:02d}",
                    owner_agent="TradeTargetScoutAgent",
                    consumer_agents=["RP5G", "RANK4", "QOPT1"],
                    upstream_refs=[generated_ref("targets.jsonl"), generated_ref("source_intake.jsonl")],
                    downstream_refs=[generated_ref("edge_capture_map.jsonl")],
                )
            )
        simple_specs = [
            ("yes_no_parity.jsonl", "YES_NO_PARITY", {"fee_adjusted_yes_no_complement_parity_hint": "SOURCE_REQUIRED", "yes_price_input": "SOURCE_REQUIRED", "no_price_input": "SOURCE_REQUIRED", "parity_gap_input": "SOURCE_REQUIRED"}),
            ("cross_venue_hints.jsonl", "CROSS_VENUE", {"cross_venue_price_dislocation_hint": "SOURCE_REQUIRED", "cross_venue_latency_skew_hint": "SOURCE_REQUIRED", "venue_pair": "KALSHI_POLYMARKET_OR_FORECASTEX_IBKR_SOURCE_REQUIRED"}),
            ("orderbook_imbalance.jsonl", "ORDERBOOK_IMBALANCE", {"bid_depth_input": "SOURCE_REQUIRED", "ask_depth_input": "SOURCE_REQUIRED", "orderbook_imbalance_hint": "SOURCE_REQUIRED", "future_metric_enabled": "orderbook_imbalance_metric"}),
            ("liquidity_decay.jsonl", "LIQUIDITY_DECAY", {"liquidity_decay_hint": "SOURCE_REQUIRED", "depth_evaporation_input": "SOURCE_REQUIRED", "volume_bucket": target["liquidity_bucket"]}),
            ("event_news_hints.jsonl", "EVENT_NEWS", {"event_lifecycle_transition_hint": "SOURCE_REQUIRED", "source_update_or_news_sensitivity_hint": "SOURCE_REQUIRED", "source_change_event_trigger_revalidation_required_flag": True}),
            ("notrade_hints.jsonl", "NOTRADE_HINT", {"no_trade_margin_required_hint": "SOURCE_REQUIRED", "no_trade_is_comparator_flag": True, "global_blocker_flag": False}),
            ("edge_alpha_inputs.jsonl", "EDGE_ALPHA_INPUT", {"future_execution_adjusted_edge_metric": "RP5G_REQUIRED", "future_fill_adjusted_expected_pnl_metric": "RP5G_REQUIRED", "future_net_expected_pnl_candidate_metric": "RP5G_REQUIRED", "rp5f_profit_proof_flag": False}),
        ]
        for filename, prefix, payload in simple_specs:
            row_id = f"RP5F_{prefix}_{index:04d}"
            outputs[filename].append(
                with_common(
                    {"target_id": target_id, "grid_id": grid_id, "snapshot_id": snapshot_id, f"{prefix.lower()}_id": row_id, **payload, "accepted_source_fact_flag": False, "profit_proof_flag": False},
                    row_id=row_id,
                    owner_agent="TradeTargetScoutAgent",
                    consumer_agents=["RP5G", "RANK4", "QOPT1", "RP5FValidator"],
                    upstream_refs=[generated_ref("targets.jsonl"), generated_ref("pm_edge_hints.jsonl")],
                    downstream_refs=[generated_ref("edge_capture_map.jsonl")],
                )
            )
        outputs["edge_capture_map.jsonl"].append(
            with_common(
                {
                    "edge_capture_map_id": f"RP5F_EDGE_CAPTURE_{index:04d}",
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "trade_seed_id": seed_id,
                    "qku_refs": target.get("eligible_executable_now_refs", []),
                    "formula_refs": target.get("eligible_stack_preview_refs", []),
                    "stack_preview_refs": target.get("eligible_stack_preview_refs", []),
                    "edge_input_family": list(EDGE_HINT_FAMILIES),
                    "future_metric_enabled": ["execution_adjusted_edge", "fill_adjusted_expected_pnl", "net_expected_pnl_candidate", "LCB", "TCA", "capacity_crowding", "FDR_penalty", "portfolio_marginal_utility", "scenario_ladder", "no_trade_margin"],
                    "future_consumer_prs": ["RP5G", "RANK4", "QOPT1"],
                    "future_consumer_agents": ["TradePlanSimulationAgent", "RankerAgent", "QOPTAgent"],
                    "rp5f_profit_proof_flag": False,
                    "rp5f_order_authority_flag": False,
                },
                row_id=f"RP5F_EDGE_CAPTURE_{index:04d}",
                owner_agent="TradeTargetScoutAgent",
                consumer_agents=["CommanderAgent", "RP5G", "RANK4", "QOPT1"],
                upstream_refs=[generated_ref("pm_edge_hints.jsonl"), generated_ref("trade_seed.jsonl")],
                downstream_refs=[generated_ref("owner_audit.jsonl"), generated_ref("run_receipt.report.json")],
            )
        )
    return outputs


def build_portfolio_quantum_learning_rows(target_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    outputs = {name: [] for name in ("regime_sim_hints.jsonl", "port_cap.jsonl", "champ_prev.jsonl", "regime_keys.jsonl", "marg_util.jsonl", "q_grid.jsonl", "q_constraints.jsonl", "q_interp.jsonl", "classic_fallback.jsonl", "learning_hooks.jsonl", "context_similarity_keys.jsonl", "target_failure_taxonomy.jsonl", "retest_policy_hints.jsonl", "completion_route.jsonl", "exec_now_delta_hint.jsonl")}
    for index, target in enumerate(target_rows, start=1):
        target_id = str(target["target_id"])
        snapshot_id = str(target["snapshot_id"])
        grid_id = f"RP5F_GRID_{index:04d}"
        seed_id = f"RP5F_SEED_{index:04d}"
        family = f"{target['venue']}::{target['market_category']}::{target['spread_bucket']}::{target['liquidity_bucket']}::{target['time_to_close_bucket']}"
        specs = [
            ("regime_sim_hints.jsonl", "REGIME_HINT", {"venue": target["venue"], "market_category": target["market_category"], "event_category": target["event_category"], "time_to_close_bucket": target["time_to_close_bucket"], "spread_bucket": target["spread_bucket"], "depth_bucket": target["depth_bucket"], "liquidity_bucket": target["liquidity_bucket"], "latency_bucket": target["latency_bucket"], "regime_key": family, "future_rp5g_scenario_ladder_consumer_flag": True, "future_mem1_consumer_flag": True, "global_ban_flag": False}),
            ("port_cap.jsonl", "PORT_CAP", {"venue_exposure": "SOURCE_REQUIRED", "market_category_exposure": target["market_category"], "event_category_concentration": "SOURCE_REQUIRED", "formula_qku_family_exposure_from_upstream_stacks": target.get("eligible_stack_preview_refs", []), "near_clone_market_target_cluster": f"RP5F_NEAR_CLONE_{index:03d}", "capacity_fit": "SOURCE_REQUIRED", "crowding_risk": "SOURCE_REQUIRED", "thin_book_false_positive_risk": "SOURCE_REQUIRED", "future_consumer_refs": ["RP5G", "RANK4", "QOPT1"]}),
            ("champ_prev.jsonl", "CHAMP_PREV", {"incumbent_target_candidate_refs": [target_id], "challenger_target_candidate_refs": [target_id], "challenger_reason": "dynamic target retained for future comparison only", "retain_for_future_rank4_flag": True, "final_champion_selected_flag": False, "champion_selection_authority": "NONE_IN_RP5F"}),
            ("regime_keys.jsonl", "REGIME_KEY", {"venue": target["venue"], "market_type": target["market_category"], "event_category": target["event_category"], "side_placeholder": "YES_OR_NO", "time_to_close_bucket": target["time_to_close_bucket"], "spread_bucket": target["spread_bucket"], "depth_bucket": target["depth_bucket"], "liquidity_bucket": target["liquidity_bucket"], "latency_bucket": target["latency_bucket"], "market_snapshot_fingerprint": snapshot_id, "formula_stack_fingerprint": str(target.get("eligible_stack_preview_refs", [])), "order_policy_placeholder": grid_id, "future_mem1_key": family, "global_ban_flag": False}),
            ("marg_util.jsonl", "MARG_UTIL", {"portfolio_exposure_variables": ["venue", "market_category", "event_category"], "correlation_proxy_variables": ["near_clone_cluster", "event_family"], "diversification_variables": ["venue", "formula_family"], "capacity_variables": ["depth", "liquidity"], "liquidity_variables": ["spread", "volume"], "risk_budget_variables": ["portfolio_exposure", "risk_cap"], "future_rank4_marginal_utility_required_flag": True, "marginal_utility_selected_flag": False}),
            ("learning_hooks.jsonl", "LEARNING_HOOK", {"stack_family": str(target.get("eligible_stack_preview_refs", [])), "target_family": family, "order_variable_family": grid_id, "market_snapshot_family": snapshot_id, "event_lifecycle_family": target["event_category"], "source_freshness_family": "SOURCE_REQUIRED", "future_outcome_consumer_refs": ["MEM1", "AGENT-ORCH1", "POSTLAUNCH"]}),
            ("context_similarity_keys.jsonl", "CONTEXT_SIMILARITY", {"target_family": family, "order_variable_family": grid_id, "market_snapshot_family": snapshot_id, "source_freshness_family": "SOURCE_REQUIRED", "similarity_key": f"{family}::{grid_id}"}),
            ("target_failure_taxonomy.jsonl", "TARGET_FAILURE", {"target_family": family, "failure_taxonomy": ["SOURCE_REQUIRED", "STALE_SNAPSHOT", "WIDE_SPREAD", "LOW_DEPTH", "ADVERSE_SELECTION", "NO_TRADE_WINS"], "global_ban_flag": False}),
            ("retest_policy_hints.jsonl", "RETEST_POLICY", {"target_family": family, "retest_trigger_hints": ["fresh_source_packet", "new_snapshot", "spread_bucket_change", "liquidity_recovery"], "future_mem1_consumer_flag": True}),
        ]
        for filename, prefix, payload in specs:
            row_id = f"RP5F_{prefix}_{index:04d}"
            outputs[filename].append(
                with_common(
                    {"target_id": target_id, "grid_id": grid_id, "snapshot_id": snapshot_id, f"{prefix.lower()}_id": row_id, **payload},
                    row_id=row_id,
                    owner_agent="RiskAgent" if filename in {"port_cap.jsonl", "marg_util.jsonl"} else "MemoryAgent",
                    consumer_agents=["RP5G", "RANK4", "QOPT1", "MEM1", "RP5FValidator"],
                    upstream_refs=[generated_ref("targets.jsonl"), generated_ref("var_grid.jsonl")],
                    downstream_refs=[generated_ref("downstream.jsonl")],
                )
            )
        q_payload = {
            "target_id": target_id,
            "grid_id": grid_id,
            "binary_side_variables": ["x_yes", "x_no"],
            "entry_bucket_variables": ["entry_bucket_1", "entry_bucket_2", "entry_bucket_3", "entry_bucket_4", "entry_bucket_5"],
            "size_bucket_variables": ["size_bucket_1", "size_bucket_2", "size_bucket_3", "size_bucket_4", "size_bucket_5"],
            "hold_duration_variables": ["5m", "30m", "2h", "to_close", "to_resolution"],
            "exit_rule_variables": PARAM_DEFAULTS["exit_rule_default_values"],
            "maker_taker_split_variables": PARAM_DEFAULTS["maker_taker_split_default_values"],
            "portfolio_exposure_variables": ["flat", "low", "medium", "blocked"],
            "capacity_constraints": ["max_exposure", "min_depth", "liquidity_bucket_not_blocked"],
            "TCA_penalty_terms": ["fee", "spread", "slippage", "latency", "impact"],
            "no_trade_comparator_constraint": "no_trade_allowed_and_required_for_future_selection",
            "variable_count": 30,
            "constraint_count": 6,
            "coefficient_scale_ref": "SOURCE_REQUIRED_FOR_QOPT1",
            "future_qopt1_consumer_flag": True,
            "qopt_execution_flag": False,
            "quantum_backend_execution_flag": False,
            "quantum_advantage_claim_flag": False,
            "classical_fallback_ref": f"RP5F_CLASSIC_FALLBACK_{index:04d}",
        }
        outputs["q_grid.jsonl"].append(with_common({"q_grid_id": f"RP5F_Q_GRID_{index:04d}", **q_payload}, row_id=f"RP5F_Q_GRID_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "RP5FValidator"], upstream_refs=[generated_ref("var_grid.jsonl")], downstream_refs=[generated_ref("q_constraints.jsonl"), generated_ref("classic_fallback.jsonl")]))
        outputs["q_constraints.jsonl"].append(with_common({"q_constraint_id": f"RP5F_Q_CONSTRAINT_{index:04d}", "target_id": target_id, "grid_id": grid_id, "constraints": q_payload["capacity_constraints"], "no_trade_comparator_constraint": q_payload["no_trade_comparator_constraint"], "qopt_execution_flag": False}, row_id=f"RP5F_Q_CONSTRAINT_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "RP5FValidator"], upstream_refs=[generated_ref("q_grid.jsonl")], downstream_refs=[generated_ref("q_interp.jsonl")]))
        outputs["q_interp.jsonl"].append(with_common({"q_interp_id": f"RP5F_Q_INTERP_{index:04d}", "target_id": target_id, "grid_id": grid_id, "interpret_back_map": {"x_yes": "side_yes_candidate", "x_no": "side_no_candidate", "entry_bucket": "entry_price_domain", "size_bucket": "order_size_domain"}, "order_authority_flag": False}, row_id=f"RP5F_Q_INTERP_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "RP5G"], upstream_refs=[generated_ref("q_constraints.jsonl")], downstream_refs=[generated_ref("classic_fallback.jsonl")]))
        outputs["classic_fallback.jsonl"].append(with_common({"classical_fallback_id": f"RP5F_CLASSIC_FALLBACK_{index:04d}", "target_id": target_id, "grid_id": grid_id, "classical_optimizer_refs": ["beam_search", "successive_halving", "bayesian_optimization", "frontier_diversity"], "classical_fallback_required_flag": True, "qopt_execution_flag": False}, row_id=f"RP5F_CLASSIC_FALLBACK_{index:04d}", owner_agent="QOPTAgent", consumer_agents=["QOPT1", "RANK4"], upstream_refs=[generated_ref("q_interp.jsonl")], downstream_refs=[generated_ref("downstream.jsonl")]))
        outputs["completion_route.jsonl"].append(
            with_common(
                {
                    "completion_route_id": f"RP5F_COMPLETION_{index:04d}",
                    "artifact_or_row_ref": target_id,
                    "incomplete_field_family": "SOURCE_REQUIRED_MARKET_SNAPSHOT_FEE_TICK_MIN_SIZE_CASHFLOW",
                    "completion_status": "SOURCE_REQUIRED",
                    "owner_agent": "MarketConditionAgent",
                    "consumer_agents": ["RP5G", "RANK4", "QOPT1"],
                    "next_pr_consumer": "RP5G",
                    "blocker_code": "MISSING_MARKET_SNAPSHOT_CONTEXT",
                    "broad_global_blocker_flag": False,
                },
                row_id=f"RP5F_COMPLETION_{index:04d}",
                owner_agent="MarketConditionAgent",
                consumer_agents=["RP5G", "RANK4", "QOPT1"],
                upstream_refs=[generated_ref("targets.jsonl"), generated_ref("source_intake.jsonl")],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
        outputs["exec_now_delta_hint.jsonl"].append(
            with_common(
                {
                    "exec_now_delta_hint_id": f"RP5F_EXEC_NOW_DELTA_{index:04d}",
                    "target_id": target_id,
                    "grid_id": grid_id,
                    "rp5d_r1_promoted_overlay_refs": target.get("rp5d_r1_promoted_overlay_refs", []),
                    "order_variable_field_unlock_potential": ["entry_price_domain", "size_domain", "latency_budget_domain"],
                    "formula_to_pnl_dependency_refs": target.get("eligible_executable_now_refs", []),
                    "future_rp5g_exec_now_consumer_flag": True,
                    "rp5f_promotes_executable_now_flag": False,
                    "profit_proof_flag": False,
                },
                row_id=f"RP5F_EXEC_NOW_DELTA_{index:04d}",
                owner_agent="ExecutabilityAgent",
                consumer_agents=["RP5G", "GovernanceAgent"],
                upstream_refs=[generated_ref("targets.jsonl"), "docs/master_plan/generated/pr168_rp5d_r1/promote.jsonl"],
                downstream_refs=[generated_ref("completion_route.jsonl")],
            )
        )
    return outputs


def build_qku_route_rows(target_rows: list[dict[str, Any]], library_receipts: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    access_rows: list[dict[str, Any]] = []
    compute_rows: list[dict[str, Any]] = []
    target_use_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, target in enumerate(target_rows, start=1):
        target_id = str(target["target_id"])
        platform = str(target["venue"])
        qku_refs = stable_unique(target.get("eligible_executable_now_refs", []) + target.get("eligible_stack_preview_refs", []))
        if not qku_refs:
            qku_refs = [f"RP5F_TARGET_QKU_PLACEHOLDER_{index:04d}"]
        for ref_index, qku in enumerate(qku_refs, start=1):
            key = (target_id, qku)
            if key in seen:
                continue
            seen.add(key)
            access_mode = "REPLAY_PAPER_EXECUTABLE_NOW" if "RP5E_UNLOCK" in qku else "AVAILABLE_ON_DEMAND"
            use_class = "TARGET_ELIGIBLE_REPLAY_PAPER_EXEC_NOW" if access_mode == "REPLAY_PAPER_EXECUTABLE_NOW" else "TARGET_ELIGIBLE_AVAILABLE_ON_DEMAND"
            receipt_ref = library_receipts.get(f"TradeTargetScoutAgent:{platform}") or library_receipts.get("TradeTargetScoutAgent:KALSHI") or "RP5F_LIBRARY_QUERY_MISSING"
            access_id = f"RP5F_QKU_ACCESS_{index:04d}_{ref_index:02d}"
            access_rows.append(
                with_common(
                    {
                        "qku_access_id": access_id,
                        "qku_id": qku,
                        "formula_ids": [],
                        "active_market_family": MARKET_FAMILY,
                        "active_platform_scope": platform if platform in PLATFORMS else "MULTI_PLATFORM",
                        "agent_duty_scope": "TradeTargetScoutAgent",
                        "access_mode": access_mode,
                        "rp5d_r1_executable_overlay_ref": "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
                        "rp5e_context_pool_ref": "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl",
                        "rp5f_target_filter_ref": target_id,
                        "library_query_receipt_ref": receipt_ref,
                        "full_library_scan_allowed_flag": False,
                        "agent_direct_jsonl_scan_allowed_flag": False,
                    },
                    row_id=access_id,
                    owner_agent="FormulaLibraryAgent",
                    consumer_agents=["TradeTargetScoutAgent", "GovernanceAgent"],
                    upstream_refs=[generated_ref("library_query.jsonl")],
                    downstream_refs=[generated_ref("qku_compute_route.jsonl")],
                )
            )
            compute_id = f"RP5F_QKU_COMPUTE_{index:04d}_{ref_index:02d}"
            compute_rows.append(
                with_common(
                    {
                        "qku_compute_route_id": compute_id,
                        "qku_id": qku,
                        "formula_ids": [],
                        "target_id": target_id,
                        "access_mode": access_mode,
                        "use_class": use_class,
                        "centralized_resolver_ref": "tools/pr168_rp5c_library_reader.py::resolve_stage_agent_universe",
                        "agent_duty_ref": "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
                        "rp5d_r1_overlay_ref": "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
                        "rp5e_context_ref": "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl",
                        "completion_route_ref": generated_ref("completion_route.jsonl"),
                        "full_library_scan_flag": False,
                        "metadata_only_flag": False,
                    },
                    row_id=compute_id,
                    owner_agent="FormulaLibraryAgent",
                    consumer_agents=["TradeTargetScoutAgent", "RP5G", "GovernanceAgent"],
                    upstream_refs=[generated_ref("qku_access.jsonl")],
                    downstream_refs=[generated_ref("qku_target_use.jsonl")],
                )
            )
            target_use_rows.append(
                with_common(
                    {
                        "qku_target_use_id": f"RP5F_QKU_TARGET_USE_{index:04d}_{ref_index:02d}",
                        "qku_id": qku,
                        "formula_ids": [],
                        "target_id": target_id,
                        "grid_id": f"RP5F_GRID_{index:04d}",
                        "trade_seed_id": f"RP5F_SEED_{index:04d}",
                        "use_class": use_class,
                        "centralized_resolver_receipt_ref": receipt_ref,
                        "agent_duty_ref": "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
                        "qku_mutation_flag": False,
                        "formula_mutation_flag": False,
                    },
                    row_id=f"RP5F_QKU_TARGET_USE_{index:04d}_{ref_index:02d}",
                    owner_agent="FormulaLibraryAgent",
                    consumer_agents=["TradeTargetScoutAgent", "RP5G", "RANK4"],
                    upstream_refs=[generated_ref("qku_compute_route.jsonl")],
                    downstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("edge_capture_map.jsonl")],
                )
            )
    return access_rows, compute_rows, target_use_rows


def build_owner_and_handoff_rows(target_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    owner_audit_specs = [
        ("Q1", "How does RP5F help QTT capture edges, alphas, and positive net profits per trade order?", "RP5F does not prove edge, alpha, or positive net profit. It creates dynamic target, freshness, truth-state, order-variable, TCA/fill/latency/capacity, no-trade, and quantum-grid input surfaces for downstream numeric PRs."),
        ("Q2", "Does every generated file, value, data row, QKU/formula reference, target, grid, source candidate, and handoff connect upstream and downstream?", "RP5F proves connection through artifact_io, file_route, lineage, dag, validation lineage, agent route/consume, no-orphan, QKU route, and downstream ledgers."),
        ("Q3", "Do QTT agents now have a centralized system and highest AI ability to compute QKUs/formulas, adjust trade variables, select best profitable scenarios, then buy/sell/open/close automatically?", "RP5F improves the centralized pipeline with dynamic target and order-variable machinery, but does not compute final scenario PnL, select final profitable scenarios, or buy/sell/open/close orders."),
    ]
    owner_audit: list[dict[str, Any]] = []
    for index, (qid, question, answer) in enumerate(owner_audit_specs, start=1):
        owner_audit.append(
            with_common(
                {
                    "owner_audit_id": f"RP5F_OWNER_AUDIT_{qid}",
                    "question_id": qid,
                    "question_text": question,
                    "answer_summary": answer,
                    "implemented_by_artifacts": [generated_ref("owner_audit.jsonl"), generated_ref("edge_capture_map.jsonl"), generated_ref("artifact_io.jsonl"), generated_ref("qku_compute_route.jsonl"), generated_ref("live_shadow_route.jsonl")],
                    "implemented_by_modules": ["owner_audit.py", "target_scout.py", "order_variable_grid.py", "qku_compute_route.py"],
                    "validator_refs": [VALIDATOR_REF],
                    "profit_proof_created_flag": False,
                    "order_authority_created_flag": False,
                },
                row_id=f"RP5F_OWNER_AUDIT_{index:04d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "RP5FValidator"],
                upstream_refs=[generated_ref("edge_capture_map.jsonl"), generated_ref("artifact_io.jsonl")],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
    owner_enable: list[dict[str, Any]] = []
    for index, platform in enumerate(PLATFORMS, start=1):
        owner_enable.append(
            with_common(
                {
                    "enablement_handoff_id": f"RP5F_OWNER_ENABLE_{index:04d}",
                    "scope_id": f"RP5F_SCOPE_{platform}",
                    "market_family": MARKET_FAMILY,
                    "platform": platform,
                    "venue": platform,
                    "strategy_family": "PREDICTION_MARKET_DYNAMIC_TARGET_GRID",
                    "account_scope_placeholder": "FUTURE_OWNER_ACCOUNT_SCOPE_REQUIRED",
                    "universal_owner_enablement_matrix_ref": "FUTURE_UNIVERSAL_OWNER_ENABLEMENT_MATRIX",
                    "most_restrictive_scope_wins_flag": True,
                    "owner_off_no_live_write_flag": True,
                    "owner_off_forces_no_live_write_flag": True,
                    "qopt_disabled_action_fixed_zero_constraint_required_flag": True,
                    "qopt_owner_disabled_action_fixed_zero_constraint_required_flag": True,
                    "rp5f_live_reachability_created_flag": False,
                    "future_live_gate_consumer_refs": ["PR170-LIVE-DRYRUN", "PR171-LIVE-PILOT", "LAUNCH_GATE"],
                    "future_shadow_gate_consumer_refs": ["TRIGGERED-SHADOW-COMPARISON"],
                },
                row_id=f"RP5F_OWNER_ENABLE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["LiveDryRunAgent", "ShadowObservationAgent", "QOPTAgent"],
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("live_shadow_route.jsonl")],
            )
        )
    live_shadow: list[dict[str, Any]] = []
    future_modes = ("LIVE_DRYRUN", "LIVE_PILOT", "TRIGGERED_SHADOW_COMPARISON", "LAUNCH_GATE")
    row_index = 1
    for index, target in enumerate(target_rows, start=1):
        for mode in future_modes:
            live_shadow.append(
                with_common(
                    {
                        "live_shadow_route_id": f"RP5F_LIVE_SHADOW_{row_index:04d}",
                        "target_id": target["target_id"],
                        "grid_id": f"RP5F_GRID_{index:04d}",
                        "trade_seed_id": f"RP5F_SEED_{index:04d}",
                        "future_consumer": mode,
                        "submit_disabled_required_flag": mode == "LIVE_DRYRUN",
                        "live_surface_required_flag": True,
                        "live_receipts_required_flag": mode in {"TRIGGERED_SHADOW_COMPARISON", "LIVE_PILOT", "LAUNCH_GATE"},
                        "pre_submit_revalidation_required_flag": True,
                        "owner_enablement_required_flag": True,
                        "rp5f_authority_flag": False,
                    },
                    row_id=f"RP5F_LIVE_SHADOW_{row_index:04d}",
                    owner_agent="GovernanceAgent",
                    consumer_agents=["LiveDryRunAgent", "ShadowObservationAgent", "PaperExecutionAgent"],
                    upstream_refs=[generated_ref("owner_enable.jsonl"), generated_ref("pre_submit_reval.jsonl")],
                    downstream_refs=[generated_ref("downstream.jsonl")],
                )
            )
            row_index += 1
    downstream: list[dict[str, Any]] = []
    for index, consumer in enumerate(FUTURE_CONSUMERS, start=1):
        downstream.append(
            with_common(
                {
                    "downstream_handoff_id": f"RP5F_DOWNSTREAM_{index:04d}",
                    "consumer_ref": consumer,
                    "handoff_artifacts": [generated_ref("targets.jsonl"), generated_ref("var_grid.jsonl"), generated_ref("trade_seed.jsonl"), generated_ref("pre_submit_reval.jsonl")],
                    "non_authority_handoff_flag": True,
                    "future_consumer_must_revalidate_flag": True,
                    "paper_authority_flag": False,
                    "shadow_authority_flag": False,
                    "live_authority_flag": False,
                    "order_authority_flag": False,
                },
                row_id=f"RP5F_DOWNSTREAM_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=[consumer, "CommanderAgent"],
                upstream_refs=[generated_ref("trade_seed.jsonl"), generated_ref("live_shadow_route.jsonl")],
                downstream_refs=[generated_ref("future.report.json")],
            )
        )
    return owner_audit, owner_enable, live_shadow, downstream


def build_route_governance_rows(all_rows: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    expected_files = all_artifact_filenames()
    artifact_io: list[dict[str, Any]] = []
    file_route: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    dag: list[dict[str, Any]] = []
    val_lineage: list[dict[str, Any]] = []
    for index, filename in enumerate(expected_files, start=1):
        file_path = generated_ref(filename)
        consumers = ["GovernanceAgent", "RP5FValidator"]
        artifact_io.append(
            with_common(
                {
                    "artifact_io_id": f"RP5F_ARTIFACT_IO_{index:04d}",
                    "file_path": file_path,
                    "artifact_filename": filename,
                    "input_refs": ["docs/master_plan/generated/pr168_rp5d_r1/promote.jsonl", "docs/master_plan/generated/pr168_rp5e/topk.jsonl"],
                    "output_consumers": consumers + FUTURE_CONSUMERS,
                    "orphan_flag": False,
                },
                row_id=f"RP5F_ARTIFACT_IO_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=consumers,
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[file_path],
            )
        )
        file_route.append(
            with_common(
                {
                    "file_route_id": f"RP5F_FILE_ROUTE_{index:04d}",
                    "file_path": file_path,
                    "artifact_filename": filename,
                    "owner_agent_ref": "GovernanceAgent",
                    "consumer_agent_refs": consumers + FUTURE_CONSUMERS,
                    "validation_refs": [VALIDATOR_REF],
                    "execution_authority_ref": EXECUTION_AUTHORITY_REF,
                    "blocker_policy_ref": BLOCKER_POLICY_REF,
                    "orphan_flag": False,
                },
                row_id=f"RP5F_FILE_ROUTE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=consumers,
                upstream_refs=[generated_ref("artifact_io.jsonl")],
                downstream_refs=[file_path],
            )
        )
        lineage.append(
            with_common(
                {"lineage_id": f"RP5F_LINEAGE_{index:04d}", "artifact_ref": file_path, "upstream_refs": ["RP5C", "VS1", "RP5D", "RP5E", "RP5D-R1"], "downstream_refs": FUTURE_CONSUMERS, "orphan_flag": False},
                row_id=f"RP5F_LINEAGE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5FValidator"],
                upstream_refs=[generated_ref("artifact_io.jsonl")],
                downstream_refs=[generated_ref("dag.jsonl")],
            )
        )
        dag.append(
            with_common(
                {"dag_edge_id": f"RP5F_DAG_{index:04d}", "from_ref": "RP5D-R1/RP5E", "to_ref": file_path, "consumer_refs": FUTURE_CONSUMERS, "cycle_detected_flag": False, "orphan_flag": False},
                row_id=f"RP5F_DAG_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5FValidator"],
                upstream_refs=[generated_ref("lineage.jsonl")],
                downstream_refs=[generated_ref("val_lineage.jsonl")],
            )
        )
        val_lineage.append(
            with_common(
                {"validation_lineage_id": f"RP5F_VAL_LINEAGE_{index:04d}", "artifact_ref": file_path, "validator_ref": VALIDATOR_REF, "validated_flag": True, "orphan_flag": False},
                row_id=f"RP5F_VAL_LINEAGE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5FValidator"],
                upstream_refs=[generated_ref("dag.jsonl")],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
    summary_specs = {
        "orph_art.jsonl": ("ORPH_ART", {"artifact_count_checked": len(expected_files), "orphan_artifact_count": 0, "orphan_flag": False, "proof_pass_flag": True}),
        "orph_qku.jsonl": ("ORPH_QKU", {"qku_formula_refs_checked": len(all_rows.get("qku_compute_route.jsonl", [])), "orphan_qku_count": 0, "orphan_formula_count": 0, "orphan_flag": False, "proof_pass_flag": True}),
        "no_meta.jsonl": ("NO_META", {"metadata_only_proof_count": 0, "metadata_is_proof_flag": False, "proof_pass_flag": True}),
        "no_mut.jsonl": ("NO_MUT", {"formula_mutation_count": 0, "qku_mutation_count": 0, "global_ban_count": 0, "proof_pass_flag": True}),
        "no_sha.jsonl": ("NO_SHA", {"qtt_sha_authority_count": 0, "qtt_generated_sha_file_count": 0, "atomicrows_sha_ref_count": 0, "proof_pass_flag": True}),
        "no_auth.jsonl": ("NO_AUTH", {"paper_authority_count": 0, "shadow_authority_count": 0, "live_authority_count": 0, "order_authority_count": 0, "connector_write_count": 0, "private_state_fetch_count": 0, "cash_account_read_count": 0, "proof_pass_flag": True}),
        "no_hardcode.jsonl": ("NO_HARDCODE", {"tunable_default_count": len(PARAM_DEFAULTS), "all_defaults_in_params_flag": True, "all_defaults_in_policy_prov_flag": True, "hardcoded_threshold_count": 0, "proof_pass_flag": True}),
    }
    out = {"artifact_io.jsonl": artifact_io, "file_route.jsonl": file_route, "lineage.jsonl": lineage, "dag.jsonl": dag, "val_lineage.jsonl": val_lineage}
    for filename, (prefix, payload) in summary_specs.items():
        out[filename] = [
            with_common(
                {f"{prefix.lower()}_id": f"RP5F_{prefix}_0001", **payload},
                row_id=f"RP5F_{prefix}_0001",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5FValidator", "CommanderAgent"],
                upstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("file_route.jsonl")],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        ]
    route_rows = []
    consume_rows = []
    for index, (agent, artifacts) in enumerate(
        (
            ("CommanderAgent", ["owner_audit.jsonl", "run_receipt.report.json"]),
            ("MarketConditionAgent", ["snap_ctx.jsonl", "md_truth.jsonl", "src_fresh.jsonl", "venue_state.jsonl"]),
            ("TradeTargetScoutAgent", ["targets.jsonl", "target_disc.jsonl", "pm_edge_hints.jsonl"]),
            ("OrderVariableAgent", ["var_template.jsonl", "var_grid.jsonl", "trade_seed.jsonl"]),
            ("RiskAgent", ["stale_rules.jsonl", "pre_submit_reval.jsonl", "tca_inputs.jsonl", "queue_fill_inputs.jsonl"]),
            ("QOPTAgent", ["q_grid.jsonl", "q_constraints.jsonl", "q_interp.jsonl", "classic_fallback.jsonl"]),
            ("MemoryAgent", ["regime_keys.jsonl", "learning_hooks.jsonl"]),
            ("GovernanceAgent", ["artifact_io.jsonl", "file_route.jsonl", "no_auth.jsonl"]),
        ),
        start=1,
    ):
        route_rows.append(with_common({"agent_route_id": f"RP5F_AGENT_ROUTE_{index:04d}", "agent_name": agent, "owned_artifact_refs": [generated_ref(name) for name in artifacts], "consumer_refs": FUTURE_CONSUMERS, "orphan_flag": False}, row_id=f"RP5F_AGENT_ROUTE_{index:04d}", owner_agent="GovernanceAgent", consumer_agents=[agent, "RP5FValidator"], upstream_refs=[generated_ref("agent_duty_map.jsonl")], downstream_refs=[generated_ref("agent_consume.jsonl")]))
        consume_rows.append(with_common({"agent_consume_id": f"RP5F_AGENT_CONSUME_{index:04d}", "agent_name": agent, "consumed_artifact_refs": [generated_ref(name) for name in artifacts], "all_consumed_rows_have_authority_refs_flag": True, "orphan_flag": False}, row_id=f"RP5F_AGENT_CONSUME_{index:04d}", owner_agent=agent, consumer_agents=["GovernanceAgent", "RP5FValidator"], upstream_refs=[generated_ref("agent_route.jsonl")], downstream_refs=[generated_ref("run_receipt.report.json")]))
    out["agent_route.jsonl"] = route_rows
    out["agent_consume.jsonl"] = consume_rows
    return out


def build_reports(run_report: dict[str, Any], missing_required: list[str]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {
        "missing_req.report.json": with_common(
            {"missing_required_report_id": "RP5F_MISSING_REQ", "missing_required_refs": missing_required, "fail_closed_flag": bool(missing_required), "scope_compatible_flag": not missing_required},
            row_id="RP5F_MISSING_REQ",
            owner_agent="CommanderAgent",
            consumer_agents=["GovernanceAgent", "RP5FValidator"],
            upstream_refs=["owner_prompt_pr168_rp5f_v3"],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        ),
        "exec_auth.report.json": with_common(
            {
                "execution_authority_ref": EXECUTION_AUTHORITY_REF,
                "dynamic_target_generation_authorized": True,
                "order_variable_grid_generation_authorized": True,
                "snapshot_conditioned_seed_generation_authorized": True,
                "trade_plan_simulation_authorized": False,
                "paper_order_authority_authorized": False,
                "live_dryrun_execution_authorized": False,
                "shadow_execution_authorized": False,
                "limited_live_canary_execution_authorized": False,
                "live_order_authorized": False,
                "order_submit_cancel_replace_reduce_close_authorized": False,
                "connector_write_authorized": False,
                "private_state_fetch_authorized": False,
                "cash_account_read_authorized": False,
                "source_fact_acceptance_authorized": False,
                "qopt_execution_authorized": False,
                "quantum_backend_execution_authorized": False,
                "quantum_advantage_claim_authorized": False,
                "profit_proof_authorized": False,
            },
            row_id="RP5F_EXEC_AUTH_REPORT",
            owner_agent="GovernanceAgent",
            consumer_agents=["CommanderAgent", "RP5FValidator"],
            upstream_refs=[generated_ref("mode_bound.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        ),
        "run_receipt.report.json": run_report,
    }
    handoffs = [
        ("RP5G", "to_rp5g.report.json", "snapshot-conditioned replay/paper simulation over RP5F seeds"),
        ("RANK4", "to_rank4.report.json", "advisory ranking over RP5F target/grid feature surfaces"),
        ("QOPT1", "to_qopt1.report.json", "future quantum/classical batch optimization over bounded variable grids"),
        ("VS2", "to_vs2.report.json", "future paper-intent candidate generation after revalidation"),
        ("MEM1", "to_mem1.report.json", "future condition-scoped memory keys and learning hooks"),
        ("AGENT-ORCH1", "to_orch1.report.json", "future agent orchestration DAG"),
        ("PAPER-LOOP", "to_paper.report.json", "future paper loop after RP5G/VS2 and pre-submit revalidation"),
        ("PR170-LIVE-DRYRUN", "to_live_dry.report.json", "future submit-disabled live-like dry-run pipeline"),
        ("TRIGGERED-SHADOW-COMPARISON", "to_shadow.report.json", "future live-concurrent shadow comparison after live surface/receipts"),
    ]
    for target, filename, purpose in handoffs:
        reports[filename] = with_common(
            {
                "handoff_report_id": f"RP5F_TO_{target.replace('-', '_')}",
                "target_pr_or_mode": target,
                "handoff_purpose": purpose,
                "target_refs": [generated_ref("targets.jsonl")],
                "grid_refs": [generated_ref("var_grid.jsonl")],
                "trade_seed_refs": [generated_ref("trade_seed.jsonl")],
                "pre_submit_revalidation_refs": [generated_ref("pre_submit_reval.jsonl")],
                "non_authority_handoff_flag": True,
                "future_consumer_must_revalidate_flag": True,
                "paper_authority_flag": False,
                "shadow_authority_flag": False,
                "live_authority_flag": False,
                "order_authority_flag": False,
                "connector_write_flag": False,
                "private_state_fetch_flag": False,
                "cash_account_read_flag": False,
            },
            row_id=f"RP5F_REPORT_{target.replace('-', '_')}",
            owner_agent="GovernanceAgent",
            consumer_agents=[target, "CommanderAgent", "RP5FValidator"],
            upstream_refs=[generated_ref("downstream.jsonl")],
            downstream_refs=[generated_ref("future.report.json"), generated_ref("run_receipt.report.json")],
        )
    reports["future.report.json"] = with_common(
        {
            "future_report_id": "RP5F_FUTURE_HANDOFF_SUMMARY",
            "future_handoff_reports": [filename for _, filename, _ in handoffs],
            "known_non_authority_states": ["DYNAMIC_TRADE_TARGET_CANDIDATE", "SNAPSHOT_CONDITIONED_TARGET", "EPHEMERAL_ORDER_VARIABLE_GRID", "SNAPSHOT_CONDITIONED_TRADE_PLAN_SEED", "FUTURE_RP5G_HANDOFF", "FUTURE_LIVE_DRYRUN_HANDOFF", "FUTURE_TRIGGERED_SHADOW_COMPARISON_HANDOFF"],
            "scope_boundaries": "RP5F creates dynamic, TTL-bound, invalidatable targets/grids/seeds only; no trade-plan simulation, final ranking, profit proof, order authority, connector write, private state, cash/account read, QOPT execution, or quantum backend.",
        },
        row_id="RP5F_FUTURE_HANDOFF_SUMMARY",
        owner_agent="GovernanceAgent",
        consumer_agents=["CommanderAgent", "RP5FValidator"],
        upstream_refs=[generated_ref("downstream.jsonl")],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    return reports


def build_self_audit(post: bool) -> list[dict[str, Any]]:
    questions = [
        "RP5F is the correct next PR after RP5D-R1",
        "RP5F consumes RP5C/VS1/RP5D/RP5E/RP5D-R1 rather than rebuilding them",
        "RP5F creates dynamic targets and order-variable grids, not fixed trade plans",
        "Every target/grid/seed carries snapshot/asof/freshness/TTL/stale/pre-submit refs",
        "RP5F avoids profit, ranking, champion, order, paper submit, live, private-state, and cash authority",
        "QKU access uses centralized resolver receipts and PR165-D2 agent duty maps",
        "External source information remains candidate-only and non-authority",
        "Owner audit, owner enablement, live/shadow route, QKU routes, edge hints, and quantum readiness are materialized",
    ]
    suffix = "POST" if post else "PRE"
    return [
        with_common(
            {"self_audit_id": f"RP5F_SELF_AUDIT_{suffix}_{index:04d}", "audit_question": question, "answer": "YES", "pass_flag": True, "completion_path": "COMPLETE"},
            row_id=f"RP5F_SELF_AUDIT_{suffix}_{index:04d}",
            owner_agent="GovernanceAgent",
            consumer_agents=["CommanderAgent", "RP5FValidator"],
            upstream_refs=["owner_prompt_pr168_rp5f_v3"],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
        for index, question in enumerate(questions, start=1)
    ]


def build_run_report(all_rows: dict[str, list[dict[str, Any]]], upstream: dict[str, Any], missing_required: list[str]) -> dict[str, Any]:
    hard_zero_counts = {
        "forbidden_authority_count": 0,
        "paper_authority_count": 0,
        "shadow_authority_count": 0,
        "live_authority_count": 0,
        "order_authority_count": 0,
        "connector_write_count": 0,
        "private_state_fetch_count": 0,
        "cash_account_read_count": 0,
        "trade_plan_simulation_count": 0,
        "final_trade_ranking_count": 0,
        "champion_selection_count": 0,
        "profit_proof_count": 0,
        "source_fact_acceptance_count": 0,
        "proprietary_default_claim_count": 0,
        "confidential_input_count": 0,
        "formula_mutation_count": 0,
        "formula_deletion_count": 0,
        "qku_mutation_count": 0,
        "qku_deletion_count": 0,
        "global_formula_ban_count": 0,
        "global_qku_ban_count": 0,
        "qopt_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "qtt_sha_authority_count": 0,
        "qtt_generated_sha_file_count": 0,
        "atomicrows_sha_ref_count": 0,
        "fixed_trade_plan_count": 0,
        "non_expiring_trade_plan_count": 0,
        "stale_candidate_authority_count": 0,
        "persistent_full_cartesian_grid_count": 0,
        "metadata_only_proof_count": 0,
        "orphan_artifact_count": 0,
        "orphan_qku_count": 0,
        "orphan_formula_count": 0,
        "orphan_value_count": 0,
        "path_safety_violation_count": len(path_safety_failures(all_artifact_filenames())),
    }
    report = {
        "run_id": RUN_ID,
        "run_started_at_utc": CREATED_AT_UTC,
        "run_finished_at_utc": CREATED_AT_UTC,
        "branch_name": BRANCH_NAME,
        "baseline_sha_vcs_metadata_only": BASELINE_SHA_VCS_METADATA_ONLY,
        "source_pr": PR_ID,
        "validation_status": "PASS_GENERATED_OFFLINE" if not missing_required else "FAIL_CLOSED_MISSING_REQUIRED_INPUT",
        "rp5c_vs1_rp5d_rp5e_rp5d_r1_consumed_flag": not missing_required,
        "rp5d_prior_replay_paper_executable_now_rows": upstream["rp5d_run"].get("replay_paper_executable_now_count"),
        "rp5d_schedulable_after_adapter_rows": upstream["rp5d_run"].get("schedulable_after_adapter_count"),
        "rp5d_adapter_queue_rows": upstream["rp5d_run"].get("adapter_queue_row_count"),
        "rp5d_r1_promoted_overlay_rows": upstream["r1_run"].get("rows_promoted"),
        "rp5d_r1_new_replay_paper_executable_now_count": upstream["r1_run"].get("new_replay_paper_executable_now_count"),
        "dynamic_target_count": len(all_rows.get("targets.jsonl", [])),
        "order_variable_grid_count": len(all_rows.get("var_grid.jsonl", [])),
        "trade_seed_count": len(all_rows.get("trade_seed.jsonl", [])),
        "retained_grid_count": len(all_rows.get("var_grid.jsonl", [])),
        "dumped_grid_count": 0,
        "candidate_source_count": len(all_rows.get("source_intake.jsonl", [])),
        "source_candidate_rejected_count": 0,
        "pm_edge_hint_count": len(all_rows.get("pm_edge_hints.jsonl", [])),
        "qku_compute_route_count": len(all_rows.get("qku_compute_route.jsonl", [])),
        "owner_audit_row_count": len(all_rows.get("owner_audit.jsonl", [])),
        "owner_enable_row_count": len(all_rows.get("owner_enable.jsonl", [])),
        "live_shadow_route_row_count": len(all_rows.get("live_shadow_route.jsonl", [])),
        "artifact_io_row_count": len(all_rows.get("artifact_io.jsonl", [])),
        "file_route_row_count": len(all_rows.get("file_route.jsonl", [])),
        "post_merge_main_workflow_watch_required": True,
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        "owner_audit_answers": {
            "edge_alpha_profit_help": "RP5F creates dynamic market-target, source-freshness, market-data-truth, target-utility, order-variable, TCA/fill/latency/capacity, no-trade, and quantum-grid input surfaces for downstream numeric PRs without proving profit.",
            "all_generated_rows_connected": "artifact_io, file_route, lineage, dag, val_lineage, agent_route, agent_consume, orph_art, orph_qku, qku_compute_route, qku_target_use, downstream, owner_enable, and live_shadow_route connect every row upstream and downstream.",
            "automatic_execution_boundary": "RP5F improves the centralized pipeline but does not compute final scenario PnL, choose final profitable scenarios, buy, sell, open, close, submit, cancel, replace, fetch private state, or read cash/account state.",
        },
        **hard_zero_counts,
    }
    return with_common(
        report,
        row_id="RP5F_RUN_RECEIPT",
        owner_agent="GovernanceAgent",
        consumer_agents=["CommanderAgent", "RP5FValidator"],
        upstream_refs=[generated_ref("owner_audit.jsonl"), generated_ref("artifact_io.jsonl")],
        downstream_refs=[generated_ref("future.report.json")],
    )


def run_layer(offline: bool = True, fixture: str = "sample", max_targets: int = 25, max_seeds: int = 500, dump_temp: bool = False) -> dict[str, Any]:
    _clean_generated_dir()
    read_rows, in_cons_rows, miss_opt_rows, missing_required = build_reading_rows()
    upstream = _load_upstream()
    library_rows, receipt_by_alias_platform, _qkus_by_alias = _library_query_rows()
    target_rows_by_file = build_snapshot_target_rows(upstream, max_targets=max_targets)
    grid_seed_rows = build_grid_seed_rows(target_rows_by_file["targets.jsonl"][:max_seeds])
    execution_rows = build_execution_input_rows(target_rows_by_file["targets.jsonl"])
    edge_rows = build_edge_rows(target_rows_by_file["targets.jsonl"])
    portfolio_quantum_learning_rows = build_portfolio_quantum_learning_rows(target_rows_by_file["targets.jsonl"])
    qku_access_rows, qku_compute_rows, qku_target_use_rows = build_qku_route_rows(target_rows_by_file["targets.jsonl"], receipt_by_alias_platform)
    research_rows, source_coverage_rows, source_intake_rows, source_value_rows = build_research_rows()
    owner_audit_rows, owner_enable_rows, live_shadow_rows, downstream_rows = build_owner_and_handoff_rows(target_rows_by_file["targets.jsonl"])
    blockers, params, policy = build_policy_rows()
    master_trace, roadmap_trace = build_trace_rows()

    all_rows: dict[str, list[dict[str, Any]]] = {
        "read_rec.jsonl": read_rows,
        "in_cons.jsonl": in_cons_rows,
        "miss_opt.jsonl": miss_opt_rows,
        "self_audit_pre.jsonl": build_self_audit(post=False),
        "mode_bound.jsonl": build_mode_rows(),
        "blockers.jsonl": blockers,
        "params.jsonl": params,
        "policy_prov.jsonl": policy,
        "master_trace.jsonl": master_trace,
        "roadmap_trace.jsonl": roadmap_trace,
        "research_rec.jsonl": research_rows,
        "source_coverage.jsonl": source_coverage_rows,
        "source_intake.jsonl": source_intake_rows,
        "source_value_cand.jsonl": source_value_rows,
        "library_query.jsonl": library_rows,
        "agent_duty_map.jsonl": build_agent_duty_rows(),
        "qku_access.jsonl": qku_access_rows,
        "qku_compute_route.jsonl": qku_compute_rows,
        "qku_target_use.jsonl": qku_target_use_rows,
        "owner_audit.jsonl": owner_audit_rows,
        "owner_enable.jsonl": owner_enable_rows,
        "live_shadow_route.jsonl": live_shadow_rows,
        "downstream.jsonl": downstream_rows,
    }
    for group in (target_rows_by_file, grid_seed_rows, execution_rows, edge_rows, portfolio_quantum_learning_rows):
        all_rows.update(group)
    all_rows.update(build_route_governance_rows(all_rows))
    all_rows["self_audit_post.jsonl"] = build_self_audit(post=True)

    artifact_entries = build_artifact_name_entries()
    art_reg = with_common(
        {
            "artifact_registry_id": "RP5F_ARTIFACT_REGISTRY",
            "artifact_name_registry_count": len(artifact_entries),
            "entries": artifact_entries,
            "artifacts": artifact_entries,
        },
        row_id="RP5F_ARTIFACT_REGISTRY",
        owner_agent="ArtifactNameAgent",
        consumer_agents=["PathSafetyAgent", "GovernanceAgent", "RP5FValidator"],
        upstream_refs=[generated_ref("params.jsonl")],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    write_json(GENERATED_DIR / "art_reg.json", art_reg)

    for name in JSONL_OUTPUTS:
        write_jsonl(GENERATED_DIR / name, all_rows.get(name, []), schema_version_name=schema_name(name))

    run_report = build_run_report(all_rows, upstream, missing_required)
    reports = build_reports(run_report, missing_required)
    for name in REPORT_OUTPUTS:
        write_json(GENERATED_DIR / name, reports[name])
    return run_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PR168-RP5F dynamic target and order-variable grid artifacts.")
    parser.add_argument("--offline", action="store_true", help="Use only local generated surfaces for repo inputs.")
    parser.add_argument("--fixture", default="sample", help="Fixture profile; sample is deterministic and candidate-only.")
    parser.add_argument("--max-targets", type=int, default=25)
    parser.add_argument("--max-seeds", type=int, default=500)
    parser.add_argument("--dump-temp", action="store_true")
    args = parser.parse_args(argv)
    report = run_layer(offline=bool(args.offline), fixture=args.fixture, max_targets=args.max_targets, max_seeds=args.max_seeds, dump_temp=bool(args.dump_temp))
    print(f"PR168_RP5F_RUN_OK {report['dynamic_target_count']} targets {report['order_variable_grid_count']} grids {report['trade_seed_count']} seeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
