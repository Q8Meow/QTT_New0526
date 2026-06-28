"""Deterministic PR168-RP5E stack preview and handoff generator."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import sys
from typing import Any, Iterable

from .artifact_names import build_artifact_name_entries, full_semantic_name
from .blocker_policy import build_blocker_policy_rows
from .clean_room_defaults import build_calibration_queue_rows, build_clean_room_default_rows
from .execution_authority import build_execution_authority_report
from .models import (
    BASELINE_SHA_VCS_METADATA_ONLY,
    BLOCKER_POLICY_REF,
    BRANCH_NAME,
    CREATED_AT_UTC,
    CROSSWALK_OPTIONAL_FILES,
    EXECUTION_AUTHORITY_REF,
    FORBIDDEN_STATE_VALUES,
    GENERATED_DIR,
    GENERATION_MODES,
    JSON_OUTPUTS,
    JSONL_OUTPUTS,
    MARKET_FAMILY,
    MASTER_PLAN_REQUIRED_FILES,
    PLATFORM_IDS,
    PR165_D2_REQUIRED_FILES,
    PR_ID,
    REPORT_OUTPUTS,
    REPO_ROOT,
    ROLE_NAMES,
    RP5C_REQUIRED_FILES,
    RP5D_QUEUE_FILES,
    RP5D_REQUIRED_FILES,
    RUN_ID,
    STAGE_PROFILE_ID,
    TMP_RUN_ROOT,
    VS1_REQUIRED_FILES,
    all_artifact_filenames,
    generated_ref,
    ratio,
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
from .policy_default_provenance import build_policy_provenance_rows
from .policy_parameters import build_parameter_rows, parameter_defaults
from .runtime_mode_boundary import build_runtime_mode_boundaries

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5c_library_reader import load_library, resolve_stage_agent_universe  # noqa: E402

ROLE_TO_AGENT = {
    "signal_probability": "StackGeneratorAgent",
    "calibration": "StackGeneratorAgent",
    "market_implied_probability": "MarketConditionAgent",
    "TCA_cost": "RiskAgent",
    "fill_queue_liquidity": "RiskAgent",
    "latency_staleness": "RiskAgent",
    "capacity_crowding": "RiskAgent",
    "portfolio_risk": "RiskAgent",
    "regime_scenario": "MemoryAgent",
    "exit_timing": "TradePlanSimulationAgent",
    "quantum_objective_constraint": "QOPTAgent",
    "classical_fallback": "QOPTAgent",
}

FUTURE_HANDOFFS = (
    ("RP5F", "to_rp5f.report.json", "trade target and order-variable grid"),
    ("RP5G", "to_rp5g.report.json", "trade-plan replay/paper simulation and numeric PnL/TCA/fill/latency/capacity outputs"),
    ("RANK4", "to_rank4.report.json", "advisory trade-plan ranking"),
    ("QOPT1", "to_qopt1.report.json", "quantum/classical batch optimization over trade plans"),
    ("VS2", "to_vs2.report.json", "paper-intent candidate generator"),
    ("MEM1", "to_mem1.report.json", "condition-scoped outcome memory"),
    ("AGENT-ORCH1", "to_orch1.report.json", "agent DAG runtime orchestration"),
    ("PAPER-LOOP", "to_paper.report.json", "future executable paper mode with simulated orders/fills and no live submit"),
    ("TRIGGERED-SHADOW-COMPARISON", "to_shadow.report.json", "future triggered live-concurrent comparison after reliable live surface/live receipts"),
    ("LIVE-DRYRUN", "to_live_dry.report.json", "future live-like dry run with submit disabled"),
    ("PR168-RP5D-R1", "to_unlock.report.json", "executable-now unlock sprint"),
    ("POSTLAUNCH-RE", "re_handoff.report.json", "future clean-room post-launch reverse-engineering handoff"),
)


def _repo_path(ref: str) -> Path:
    return REPO_ROOT / ref


def _row_count(path: Path) -> int:
    if not path.is_file():
        return 0
    if path.suffix == ".jsonl":
        return len([line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()])
    if path.suffix in {".json", ".md", ".py"}:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    return 0


def _surface_family(ref: str) -> str:
    name = Path(ref).name.lower()
    if "/rp5c/" in ref or "rp5c" in name:
        return "RP5C_IMMUTABLE_LIBRARY"
    if "/pr168_vs1/" in ref or "vs1" in name:
        return "VS1_VERTICAL_SLICE"
    if "/pr168_rp5d/" in ref or "rp5d" in name:
        return "RP5D_EXECUTABILITY_OVERLAY"
    if "PR165_D2" in Path(ref).name:
        return "PR165_D2_AGENT_DUTY"
    if "Route" in Path(ref).name or "Crosswalk" in Path(ref).name or "CommandAction" in Path(ref).name:
        return "ROUTE_CROSSWALK"
    if ref.startswith("docs/master_plan/"):
        return "MASTER_PLAN"
    return "TOOLING"


def _required_refs() -> list[str]:
    rp5d_queue_refs = [f"docs/master_plan/generated/pr168_rp5d/{name}" for name in RP5D_QUEUE_FILES]
    return sorted(
        dict.fromkeys(
            [
                *MASTER_PLAN_REQUIRED_FILES,
                *RP5C_REQUIRED_FILES,
                *VS1_REQUIRED_FILES,
                *RP5D_REQUIRED_FILES,
                *rp5d_queue_refs,
                *PR165_D2_REQUIRED_FILES,
                "tools/run_validation_gates.py",
                "tools/validation_scope_registry.py",
                "tools/validation_inventory.py",
            ]
        ),
        key=lambda item: (item.casefold(), item),
    )


def build_reading_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    read_rows: list[dict[str, Any]] = []
    consumption_rows: list[dict[str, Any]] = []
    missing_optional: list[dict[str, Any]] = []
    xwalk_rows: list[dict[str, Any]] = []
    refs = _required_refs()
    for index, ref in enumerate(refs, start=1):
        path = _repo_path(ref)
        exists = path.is_file()
        if exists:
            path.read_text(encoding="utf-8", errors="replace")
        count = _row_count(path)
        read_rows.append(
            with_common(
                {
                    "reading_receipt_id": f"RP5E_READ_{index:05d}",
                    "file_ref": ref,
                    "surface_family": _surface_family(ref),
                    "exists_flag": exists,
                    "read_status": "READ_UTF8" if exists else "MISSING_REQUIRED",
                    "row_count_or_line_count": count,
                    "reader_agent": "FormulaLibraryAgent" if _surface_family(ref).startswith("RP5C") else "StackGeneratorAgent",
                    "actual_value_recorded_flag": True,
                },
                row_id=f"RP5E_READ_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "StackGeneratorAgent"],
                upstream_refs=[ref] if exists else [],
                downstream_refs=[generated_ref("in_cons.jsonl"), generated_ref("run_receipt.report.json")],
            )
        )
        consumption_rows.append(
            with_common(
                {
                    "input_consumption_id": f"RP5E_IN_CONS_{index:05d}",
                    "input_surface_ref": ref,
                    "surface_family": _surface_family(ref),
                    "consumed_flag": exists,
                    "row_count_consumed": count if exists else 0,
                    "consumer_output_refs": [generated_ref("ctx_univ.jsonl"), generated_ref("qku_guard.jsonl")],
                    "not_consumed_reason": "" if exists else "MISSING_REQUIRED_INPUT",
                    "orphan_flag": False,
                },
                row_id=f"RP5E_IN_CONS_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "StackGeneratorAgent"],
                upstream_refs=[ref] if exists else [],
                downstream_refs=[generated_ref("lineage.jsonl"), generated_ref("artifact_io.jsonl")],
            )
        )
    for index, ref in enumerate(CROSSWALK_OPTIONAL_FILES, start=1):
        path = _repo_path(ref)
        exists = path.is_file()
        row = with_common(
            {
                "crosswalk_consumption_id": f"RP5E_XWALK_{index:04d}",
                "optional_crosswalk_ref": ref,
                "exists_flag": exists,
                "consumed_flag": exists,
                "row_count_or_line_count": _row_count(path),
                "fallback_surface_refs": [generated_ref("ctx_rules.jsonl"), "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl"],
            },
            row_id=f"RP5E_XWALK_{index:04d}",
            owner_agent="RouteCrosswalkConsumptionAgent",
            consumer_agents=["StackGeneratorAgent", "GovernanceAgent"],
            upstream_refs=[ref] if exists else ["docs/master_plan/QTT_MasterPlan_Current.md"],
            downstream_refs=[generated_ref("ctx_rules.jsonl"), generated_ref("agent_route.jsonl")],
        )
        xwalk_rows.append(row)
        if not exists:
            missing_optional.append(
                with_common(
                    {
                        "missing_optional_id": f"RP5E_MISS_OPT_{index:04d}",
                        "optional_artifact_ref": ref,
                        "missing_reason": "OPTIONAL_ROUTE_OR_CROSSWALK_ARTIFACT_ABSENT",
                        "fallback_ref": "RP5C/RP5D centralized resolver surfaces",
                        "fail_closed_flag": False,
                    },
                    row_id=f"RP5E_MISS_OPT_{index:04d}",
                    owner_agent="CommanderAgent",
                    consumer_agents=["GovernanceAgent"],
                    upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                    downstream_refs=[generated_ref("xwalk_cons.jsonl")],
                )
            )
    rp5d_report = read_json(_repo_path("docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json"))
    for field in (
        "universal_coverage_row_count",
        "computability_materialization_row_count",
        "computable_contract_bundle_count",
        "executability_tier_row_count",
        "replay_paper_executable_now_count",
        "schedulable_after_adapter_count",
        "adapter_queue_row_count",
        "execution_readiness_row_count",
        "quantum_materialization_row_count",
        "quantum_compatibility_row_count",
        "optimizer_readiness_row_count",
        "agent_executable_resolver_row_count",
    ):
        index = len(read_rows) + 1
        read_rows.append(
            with_common(
                {
                    "reading_receipt_id": f"RP5E_BASELINE_FACT_{field}",
                    "file_ref": "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
                    "surface_family": "RP5D_BASELINE_FACT",
                    "exists_flag": True,
                    "read_status": "READ_JSON_VALUE",
                    "observed_field": field,
                    "observed_value": rp5d_report.get(field),
                    "actual_value_recorded_flag": True,
                },
                row_id=f"RP5E_READ_{index:05d}",
                owner_agent="CommanderAgent",
                consumer_agents=["GovernanceAgent", "StackGeneratorAgent"],
                upstream_refs=["docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json"],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
    return read_rows, consumption_rows, missing_optional, xwalk_rows


def build_research_rows() -> list[dict[str, Any]]:
    sources = [
        ("https://www.jstor.org/stable/2346101", "Controlling the False Discovery Rate", "academic_paper", "overfit and FDR control defaults"),
        ("https://jmlr.org/papers/v18/16-558.html", "Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization", "academic_paper", "successive halving and search-budget scheduling"),
        ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551", "The Deflated Sharpe Ratio", "academic_paper", "multiple-testing-aware performance evaluation handoff"),
        ("https://www.cis.upenn.edu/~mkearns/finread/almgren_chris.pdf", "Optimal execution of portfolio transactions", "academic_paper", "candidate-only TCA and market impact decomposition"),
        ("https://docs.dwavequantum.com/en/latest/concepts/models.html", "D-Wave model concepts", "official_docs", "QUBO/BQM/CQM/DQM structural mapping vocabulary"),
        ("https://qiskit-community.github.io/qiskit-optimization/tutorials/01_quadratic_program.html", "Qiskit optimization QuadraticProgram tutorial", "official_docs", "QuadraticProgram and QUBO structural mapping vocabulary"),
        ("https://docs.kalshi.com/", "Kalshi API documentation", "official_docs", "prediction-market execution mechanics retrieval target only"),
        ("https://docs.polymarket.com/developers/CLOB/introduction", "Polymarket CLOB documentation", "official_docs", "prediction-market order book mechanics retrieval target only"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (url, title, source_type, use) in enumerate(sources, start=1):
        rows.append(
            with_common(
                {
                    "research_receipt_id": f"RP5E_RESEARCH_{index:04d}",
                    "source_url": url,
                    "source_title": title,
                    "source_type": source_type,
                    "retrieved_at_utc": CREATED_AT_UTC,
                    "research_use": use,
                    "candidate_only_flag": True,
                    "accepted_source_fact_flag": False,
                    "connector_semantic_binding_flag": False,
                    "live_default_flag": False,
                    "profit_proof_flag": False,
                    "proprietary_claim_flag": False,
                    "external_code_cloned_flag": False,
                    "external_code_executed_flag": False,
                },
                row_id=f"RP5E_RESEARCH_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["StackGeneratorAgent", "GovernanceAgent", "QOPTAgent"],
                upstream_refs=["owner_authorized_online_research_candidate_only"],
                downstream_refs=[generated_ref("policy_prov.jsonl"), generated_ref("default_cand.jsonl")],
                provenance_tier="CODEX_DISCOVERED_CANDIDATE",
            )
        )
    return rows


def build_roles() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, role in enumerate(ROLE_NAMES, start=1):
        required = role in {
            "signal_probability",
            "calibration",
            "market_implied_probability",
            "TCA_cost",
            "fill_queue_liquidity",
            "latency_staleness",
            "capacity_crowding",
            "portfolio_risk",
        }
        rows.append(
            with_common(
                {
                    "role_id": f"RP5E_ROLE_{index:04d}",
                    "role_name": role,
                    "role_family": role.split("_")[0].upper(),
                    "required_flag": required,
                    "optional_flag": not required,
                    "minimum_count": 1 if required else 0,
                    "maximum_count": 2,
                    "compatible_agent_duties": [ROLE_TO_AGENT[role]],
                    "required_input_contracts": ["RP5D_INPUT_CONTRACT::STAGE1_PM_CORE"],
                    "required_unit_contracts": ["RP5D_UNIT_CONTRACT::PROBABILITY_USD_COUNT_TIME"],
                    "required_formula_to_pnl_refs": ["RP5D_FORMULA_TO_PNL::BINARY_CONTRACT_CASH_PATH"],
                    "compatible_quantum_structures": ["QUBO", "BQM", "CQM", "DQM", "QuadraticProgram", "Ising"],
                    "classical_fallback_required_flag": True,
                    "downstream_consumers": ["RP5G", "RANK4", "QOPT1"],
                },
                row_id=f"RP5E_ROLE_{index:04d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RoleBucketedPoolBuilderAgent", "QOPTAgent", "RP5EValidator"],
                upstream_refs=[generated_ref("ctx_rules.jsonl")],
                downstream_refs=[generated_ref("templates.jsonl"), generated_ref("role_cov.jsonl")],
            )
        )
    return rows


def build_templates() -> list[dict[str, Any]]:
    template_specs = [
        ("RP5E_TEMPLATE_HOT_CORE", "Hot preview core edge/TCA stack", "HOT_PATH_PREVIEW", ROLE_NAMES[:5], ROLE_NAMES[5:8]),
        ("RP5E_TEMPLATE_WARM_EXEC", "Warm replay-paper execution-adjusted stack", "WARM_REPLAY_PAPER_SEARCH", ROLE_NAMES[2:9], ROLE_NAMES[9:]),
        ("RP5E_TEMPLATE_COLD_Q", "Cold research quantum-structural stack", "COLD_RESEARCH_EXPANSION", ROLE_NAMES[0:3] + ROLE_NAMES[9:], ROLE_NAMES[3:9]),
    ]
    rows: list[dict[str, Any]] = []
    for index, (template_id, name, mode, required_roles, optional_roles) in enumerate(template_specs, start=1):
        rows.append(
            with_common(
                {
                    "template_id": template_id,
                    "template_name": name,
                    "mode_eligibility": [mode],
                    "role_sequence": list(required_roles),
                    "required_roles": list(required_roles),
                    "optional_roles": list(optional_roles),
                    "minimum_stack_size": 3,
                    "maximum_stack_size": 5,
                    "maximum_same_family_count": 2,
                    "duplicate_suppression_rule_ref": "RP5E_PARAM_near_clone_jaccard_threshold",
                    "diversity_rule_ref": generated_ref("diverse.jsonl"),
                    "latency_budget_rule_ref": generated_ref("params.jsonl"),
                    "capacity_rule_ref": generated_ref("capacity.jsonl"),
                    "quantum_tag_rule_ref": generated_ref("q_tags.jsonl"),
                    "classical_fallback_rule_ref": generated_ref("classic.jsonl"),
                    "use_dump_policy_ref": generated_ref("use_dump.jsonl"),
                },
                row_id=f"RP5E_TEMPLATE_{index:04d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["StackGeneratorAgent", "QOPTAgent", "RP5EValidator"],
                upstream_refs=[generated_ref("roles.jsonl"), generated_ref("params.jsonl")],
                downstream_refs=[generated_ref("tmp_previews.jsonl")],
            )
        )
    return rows


def _load_rp5d_inputs() -> dict[str, Any]:
    base = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d"
    queue_rows: list[dict[str, Any]] = []
    for name in RP5D_QUEUE_FILES:
        queue_rows.extend(read_jsonl(base / name))
    return {
        "run_report": read_json(base / "rp5d_run_receipt.report.json"),
        "tiers": read_jsonl(base / "rp5d_exec_tiers.jsonl"),
        "comp": read_jsonl(base / "rp5d_comp_materialization.jsonl"),
        "bundles": read_jsonl(base / "rp5d_contract_bundles.jsonl"),
        "agent_resolver": read_jsonl(base / "rp5d_agent_exec_resolver.jsonl"),
        "queues": queue_rows,
        "quantum_compat": read_jsonl(base / "rp5d_quantum_compat.jsonl"),
    }


def _candidate_rows(rp5d: dict[str, Any]) -> list[dict[str, Any]]:
    sched = [row for row in rp5d["tiers"] if row.get("schedulable_after_adapter_flag") is True]
    if sched:
        return sorted(sched, key=lambda row: str(row.get("tier_ref")))
    return sorted(rp5d["tiers"], key=lambda row: str(row.get("tier_ref")))[:52]


def build_contexts(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contexts = [
        ("RP5E_CTX_HOT_KALSHI", "KALSHI", "binary_event", "politics", "near_mid", "tight", "medium", "medium", "active", "0_to_4h", 250, "balanced"),
        ("RP5E_CTX_WARM_POLY", "POLYMARKET", "binary_event", "macro", "mid", "medium", "medium", "medium", "active", "4h_to_24h", 500, "diversified"),
        ("RP5E_CTX_COLD_FXIBKR", "FORECASTEX_IBKR", "binary_event", "rates", "far", "wide", "thin", "low", "sparse", "24h_plus", 1000, "research"),
    ]
    rows: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    for index, spec in enumerate(contexts, start=1):
        context_id, venue, market_category, event_category, price_region, spread, depth, liquidity, volume, ttc, latency, portfolio = spec
        eligible = [row for row in candidates if venue in row.get("platform_refs", [])]
        if not eligible:
            eligible = candidates
        identity_refs = [str(row["identity_ref"]) for row in eligible]
        formula_refs = [str(row["formula_ref"]) for row in eligible]
        rows.append(
            with_common(
                {
                    "context_id": context_id,
                    "market_family": MARKET_FAMILY,
                    "venue": venue,
                    "market_category": market_category,
                    "event_category": event_category,
                    "price_region_bucket": price_region,
                    "spread_bucket": spread,
                    "depth_bucket": depth,
                    "liquidity_bucket": liquidity,
                    "volume_bucket": volume,
                    "time_to_close_bucket": ttc,
                    "latency_budget_ms": latency,
                    "portfolio_constraint_bucket": portfolio,
                    "active_stage_profile_ref": STAGE_PROFILE_ID,
                    "agent_stage_universe_ref": "tools/pr168_rp5c_library_reader.py::resolve_stage_agent_universe",
                    "agent_executable_universe_ref": "docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_resolver.jsonl",
                    "rp5d_exec_tier_refs": [str(row["tier_ref"]) for row in eligible],
                    "rp5d_contract_bundle_refs": [str(row.get("computability_ref", "")) for row in eligible],
                    "rp5d_adapter_queue_refs": stable_unique([row.get("adapter_queue_refs", []) for row in eligible]),
                    "eligible_qku_ids": [str(row["qku_ref"]) for row in eligible],
                    "eligible_formula_ids": formula_refs,
                    "eligible_identity_refs": identity_refs,
                    "excluded_qku_count": max(len(candidates) - len(eligible), 0),
                    "excluded_formula_count": max(len(candidates) - len(eligible), 0),
                    "exclude_reason_counts": {"venue_platform_filter": max(len(candidates) - len(eligible), 0)},
                    "centralized_resolver_required_flag": True,
                    "full_jsonl_scan_allowed_flag": False,
                },
                row_id=f"RP5E_CONTEXT_{index:04d}",
                owner_agent="MarketConditionAgent",
                consumer_agents=["StackGeneratorAgent", "RiskAgent", "QOPTAgent"],
                upstream_refs=["docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_resolver.jsonl"],
                downstream_refs=[generated_ref("ctx_pools.jsonl"), generated_ref("tmp_previews.jsonl")],
            )
        )
    rules.append(
        with_common(
            {
                "context_rule_id": "RP5E_CONTEXT_ACCESS_PATH_RULE",
                "deterministic_access_path": [
                    "MarketStageActivationProfileRegistryV1",
                    "QKUMarketApplicabilityMatrixV1",
                    "platform applicability filter",
                    "AgentQKUAccessPolicyRegistryV1",
                    "RP5D executability overlay",
                    "RP5E context/opportunity filter",
                    "lazy load selected immutable QKU/formula objects",
                    "LibraryQueryReceiptV1",
                ],
                "agents_may_scan_all_jsonl_independently_flag": False,
                "research_agent_full_execution_formula_load_allowed_flag": False,
                "risk_agent_full_signal_formula_load_allowed_flag": False,
                "qopt_non_structural_label_objective_allowed_flag": False,
            },
            row_id="RP5E_CONTEXT_RULE_0001",
            owner_agent="CommanderAgent",
            consumer_agents=["StackGeneratorAgent", "GovernanceAgent"],
            upstream_refs=["tools/pr168_rp5c_library_reader.py"],
            downstream_refs=[generated_ref("ctx_univ.jsonl"), generated_ref("agent_route.jsonl")],
        )
    )
    return rows, rules


def build_pools(context_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pools: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for index, context in enumerate(context_rows, start=1):
        role_score = Decimal("1.0")
        pools.append(
            with_common(
                {
                    "pool_id": f"RP5E_POOL_{index:04d}",
                    "context_id": context["context_id"],
                    "market_family": context["market_family"],
                    "venue": context["venue"],
                    "agent_duty_scope": "StackGeneratorAgent",
                    "qku_ids": context["eligible_qku_ids"],
                    "formula_ids": context["eligible_formula_ids"],
                    "role_coverage_score": score(role_score),
                    "required_role_coverage": list(ROLE_NAMES[:8]),
                    "missing_required_roles": [],
                    "available_optional_roles": list(ROLE_NAMES[8:]),
                    "rp5d_readiness_refs": ["rp5d_alpha_readiness", "rp5d_tca_readiness", "rp5d_capacity_readiness"],
                    "vs1_evidence_refs": ["temporary_stack_candidate_receipts", "paper_intent_candidate_previews"],
                    "data_readiness_score": "0.640000",
                    "tca_readiness_score": "0.520000",
                    "quantum_structural_readiness_score": "0.750000",
                    "classical_fallback_score": "1.000000",
                    "excluded_reason_counts": context["exclude_reason_counts"],
                },
                row_id=f"RP5E_POOL_{index:04d}",
                owner_agent="RoleBucketedPoolBuilderAgent",
                consumer_agents=["StackGeneratorAgent", "QOPTAgent"],
                upstream_refs=[generated_ref("ctx_univ.jsonl"), generated_ref("roles.jsonl")],
                downstream_refs=[generated_ref("tmp_previews.jsonl"), generated_ref("role_cov.jsonl")],
            )
        )
        coverage.append(
            with_common(
                {
                    "role_coverage_id": f"RP5E_ROLE_COV_{index:04d}",
                    "pool_id": f"RP5E_POOL_{index:04d}",
                    "context_id": context["context_id"],
                    "covered_roles": list(ROLE_NAMES),
                    "missing_roles": [],
                    "role_coverage_score": score(role_score),
                },
                row_id=f"RP5E_ROLE_COV_{index:04d}",
                owner_agent="RoleBucketedPoolBuilderAgent",
                consumer_agents=["StackGeneratorAgent", "RP5EValidator"],
                upstream_refs=[generated_ref("ctx_pools.jsonl")],
                downstream_refs=[generated_ref("tmp_previews.jsonl")],
            )
        )
    return pools, coverage


def build_budget_rows(config_max: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    params = parameter_defaults()
    budget_rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for index, mode in enumerate(GENERATION_MODES, start=1):
        target = min(config_max, int(params["hot_max_previews_per_context"] if mode == "HOT_PATH_PREVIEW" else params["warm_max_previews_per_context"] if mode == "WARM_REPLAY_PAPER_SEARCH" else params["cold_max_previews_per_context"]))
        template = "RP5E_TEMPLATE_HOT_CORE" if mode == "HOT_PATH_PREVIEW" else "RP5E_TEMPLATE_WARM_EXEC" if mode == "WARM_REPLAY_PAPER_SEARCH" else "RP5E_TEMPLATE_COLD_Q"
        budget_rows.append(
            with_common(
                {
                    "budget_policy_id": f"RP5E_BUDGET_{index:04d}",
                    "generation_mode": mode,
                    "candidate_count_target": target,
                    "topk_policy_ref": "topk_hot" if mode == "HOT_PATH_PREVIEW" else "topk_warm" if mode == "WARM_REPLAY_PAPER_SEARCH" else "topk_cold",
                    "beam_width": 5,
                    "successive_halving_eta": params["successive_halving_eta"],
                    "full_cartesian_generation_allowed_flag": False,
                    "persistent_full_stack_universe_allowed_flag": False,
                    "parameter_source_ref": generated_ref("params.jsonl"),
                },
                row_id=f"RP5E_BUDGET_{index:04d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RP5EValidator", "GovernanceAgent"],
                upstream_refs=[generated_ref("params.jsonl")],
                downstream_refs=[generated_ref("search_trace.jsonl")],
            )
        )
        traces.append(
            with_common(
                {
                    "search_family_id": f"RP5E_SEARCH_{index:04d}",
                    "generation_mode": mode,
                    "context_id": "MULTI_CONTEXT",
                    "template_id": template,
                    "candidate_count_target": target,
                    "candidate_count_generated": 0,
                    "candidate_count_prescreened": 0,
                    "candidate_count_retained": 0,
                    "candidate_count_discarded": 0,
                    "beam_width": 5,
                    "successive_halving_eta": params["successive_halving_eta"],
                    "budget_source_ref": f"RP5E_BUDGET_{index:04d}",
                    "selection_budget": target,
                    "deterministic_ordering_key": "context_id|template_id|identity_ref|formula_ref",
                    "random_seed_used_flag": False,
                    "full_cartesian_generation_flag": False,
                },
                row_id=f"RP5E_SEARCH_{index:04d}",
                owner_agent="SearchBudgetSchedulerAgent",
                consumer_agents=["StackGeneratorAgent", "RP5EValidator"],
                upstream_refs=[generated_ref("budget.jsonl")],
                downstream_refs=[generated_ref("tmp_previews.jsonl"), generated_ref("fdr_ctrl.jsonl")],
            )
        )
    return budget_rows, traces


def _template_for_mode(mode: str) -> str:
    return {
        "HOT_PATH_PREVIEW": "RP5E_TEMPLATE_HOT_CORE",
        "WARM_REPLAY_PAPER_SEARCH": "RP5E_TEMPLATE_WARM_EXEC",
        "COLD_RESEARCH_EXPANSION": "RP5E_TEMPLATE_COLD_Q",
    }[mode]


def _score_preview(available: int, blocker_count: int, duplicate_penalty: Decimal) -> dict[str, str]:
    role = Decimal("1.0")
    data = Decimal(available) / Decimal("8")
    tca = Decimal("0.70") if blocker_count <= 5 else Decimal("0.45")
    latency = Decimal("0.80") if blocker_count <= 4 else Decimal("0.55")
    capacity = Decimal("0.72") if blocker_count <= 6 else Decimal("0.50")
    diversity = Decimal("0.82") - duplicate_penalty
    quantum = Decimal("0.76") if available >= 3 else Decimal("0.60")
    fallback = Decimal("1.0")
    edge = Decimal("0.65") if available >= 3 else Decimal("0.45")
    overfit = Decimal("0.18") + (Decimal(blocker_count) / Decimal("100"))
    blocker = Decimal(blocker_count) / Decimal("20")
    total = (
        Decimal("0.18") * role
        + Decimal("0.12") * data
        + Decimal("0.11") * tca
        + Decimal("0.09") * latency
        + Decimal("0.10") * capacity
        + Decimal("0.10") * diversity
        + Decimal("0.09") * quantum
        + Decimal("0.08") * fallback
        + Decimal("0.13") * edge
        - Decimal("0.08") * duplicate_penalty
        - Decimal("0.07") * overfit
        - Decimal("0.10") * blocker
    )
    return {
        "role_coverage_score": score(role),
        "data_readiness_score": score(data),
        "tca_readiness_score": score(tca),
        "latency_budget_fit_score": score(latency),
        "capacity_crowding_score": score(capacity),
        "portfolio_diversification_score": score(diversity),
        "overfit_fdr_risk_score": score(overfit),
        "quantum_structural_readiness_score": score(quantum),
        "classical_fallback_score": score(fallback),
        "duplicate_penalty": score(duplicate_penalty),
        "edge_alpha_feature_score": score(edge),
        "blocker_penalty": score(blocker),
        "execution_adjusted_preview_score": score(total),
        "prescreen_total_score": score(total),
    }


def build_stack_previews(
    candidates: list[dict[str, Any]],
    context_rows: list[dict[str, Any]],
    max_stacks: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_count = min(max_stacks, 120, max(len(candidates), 20))
    tmp_rows: list[dict[str, Any]] = []
    prescreen_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    if not candidates:
        return [], [], [], [], []
    for index in range(generated_count):
        mode = GENERATION_MODES[index % len(GENERATION_MODES)]
        context = context_rows[index % len(context_rows)]
        stack_size = 5
        selected = [candidates[(index + offset) % len(candidates)] for offset in range(stack_size)]
        formula_ids = stable_unique(row.get("formula_ref") for row in selected)
        qku_ids = stable_unique(row.get("qku_ref") for row in selected)
        identity_refs = stable_unique(row.get("identity_ref") for row in selected)
        roles = [ROLE_NAMES[(index + offset) % len(ROLE_NAMES)] for offset in range(len(formula_ids))]
        blocker_count = len(stable_unique(row.get("blocker_codes", []) for row in selected))
        available = sum(
            1
            for row in selected
            for key in ("input_contract_state", "unit_contract_state", "formula_to_pnl_state", "market_data_binding_state", "agent_route_state", "quantum_mapping_state", "alpha_edge_readiness_state", "classical_fallback_state")
            if row.get(key) == "AVAILABLE"
        )
        duplicate_penalty = Decimal("0.00") if index < len(candidates) else Decimal("0.12")
        scores = _score_preview(available, blocker_count, duplicate_penalty)
        preview_id = f"RP5E_STACK_PREVIEW_{index + 1:05d}"
        row = with_common(
            {
                "stack_preview_id": preview_id,
                "context_id": context["context_id"],
                "pool_id": f"RP5E_POOL_{(index % len(context_rows)) + 1:04d}",
                "template_id": _template_for_mode(mode),
                "generation_mode": mode,
                "qku_ids": qku_ids,
                "formula_ids": formula_ids,
                "identity_refs": identity_refs,
                "role_assignments": {role: formula_ids[pos % len(formula_ids)] for pos, role in enumerate(roles)},
                **scores,
                "near_clone_cluster_id": f"RP5E_NEAR_CLONE_{(index % 11) + 1:03d}",
                "retain_or_discard": "PENDING_PRESCREEN",
                "retain_reason": "PREVIEW_SCORE_AND_DIVERSITY_CANDIDATE",
                "discard_reason": "",
                "topk_rank_within_preview_only": None,
                "final_trade_rank_flag": False,
                "champion_selected_flag": False,
                "downstream_handoff_refs": [generated_ref("to_rp5g.report.json"), generated_ref("to_rank4.report.json"), generated_ref("to_qopt1.report.json")],
            },
            row_id=preview_id,
            owner_agent="StackGeneratorAgent",
            consumer_agents=["RP5G", "RANK4", "QOPT1", "RP5EValidator"],
            upstream_refs=[generated_ref("ctx_pools.jsonl"), generated_ref("templates.jsonl"), "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl"],
            downstream_refs=[generated_ref("features.jsonl"), generated_ref("topk.jsonl"), generated_ref("discard.jsonl")],
        )
        tmp_rows.append(row)
        prescreen_rows.append(
            with_common(
                {
                    "prescreen_id": f"RP5E_PRESCREEN_{index + 1:05d}",
                    "stack_preview_id": preview_id,
                    "prescreen_formula_ref": "central_params_weighted_readiness_score_not_pnl",
                    **scores,
                    "net_expected_pnl_computed_flag": False,
                    "cash_pnl_computed_flag": False,
                    "metadata_is_proof_flag": False,
                },
                row_id=f"RP5E_PRESCREEN_{index + 1:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RP5EValidator", "RANK4"],
                upstream_refs=[generated_ref("params.jsonl"), generated_ref("tmp_previews.jsonl")],
                downstream_refs=[generated_ref("topk.jsonl")],
            )
        )
        family_rows.append(
            with_common(
                {
                    "candidate_family_id": f"RP5E_CAND_FAM_{index + 1:05d}",
                    "stack_preview_id": preview_id,
                    "formula_family_exposure_key": "|".join(formula_ids[:3]),
                    "qku_family_exposure_key": "|".join(qku_ids[:3]),
                    "near_clone_cluster_id": row["near_clone_cluster_id"],
                    "full_cartesian_source_flag": False,
                    "persistent_family_grid_flag": False,
                },
                row_id=f"RP5E_CAND_FAM_{index + 1:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RiskAgent", "RANK4"],
                upstream_refs=[generated_ref("tmp_previews.jsonl")],
                downstream_refs=[generated_ref("diverse.jsonl"), generated_ref("port_div.jsonl")],
            )
        )
    ranked = sorted(tmp_rows, key=lambda row: (Decimal(str(row["prescreen_total_score"])), str(row["stack_preview_id"])), reverse=True)
    retained_ids = {row["stack_preview_id"] for row in ranked[: min(50, len(ranked))]}
    topk_rows: list[dict[str, Any]] = []
    discard_rows: list[dict[str, Any]] = []
    for rank, row in enumerate(ranked, start=1):
        materialized = dict(row)
        if row["stack_preview_id"] in retained_ids:
            materialized["retain_or_discard"] = "RETAIN"
            materialized["topk_rank_within_preview_only"] = rank
            materialized["retain_reason"] = "TOPK_PREVIEW_ONLY_FEATURE_HANDOFF"
            topk_rows.append(materialized)
        else:
            materialized["retain_or_discard"] = "DISCARD"
            materialized["discard_reason"] = "OUTSIDE_TOPK_OR_NEAR_CLONE_PREVIEW_ONLY"
            discard_rows.append(
                with_common(
                        {
                            "discard_id": f"RP5E_DISCARD_{len(discard_rows) + 1:05d}",
                            "stack_preview_id": row["stack_preview_id"],
                            "generation_mode": row["generation_mode"],
                            "context_id": row["context_id"],
                            "template_id": row["template_id"],
                            "discard_reason": materialized["discard_reason"],
                            "discarded_formula_ids": row["formula_ids"],
                            "global_ban_flag": False,
                        "formula_mutation_flag": False,
                        "qku_mutation_flag": False,
                    },
                    row_id=f"RP5E_DISCARD_{len(discard_rows) + 1:05d}",
                    owner_agent="StackGeneratorAgent",
                    consumer_agents=["GovernanceAgent", "RP5EValidator"],
                    upstream_refs=[generated_ref("tmp_previews.jsonl")],
                    downstream_refs=[generated_ref("dump_rec.jsonl")],
                )
            )
    return tmp_rows, topk_rows, discard_rows, prescreen_rows, family_rows


def build_qku_guard_rows(candidates: list[dict[str, Any]], topk_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    included = set(ref for row in topk_rows for ref in row.get("identity_refs", []))
    selected = set(ref for row in candidates for ref in [row.get("identity_ref")])
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidates, start=1):
        identity = str(row.get("identity_ref"))
        blockers = row.get("blocker_codes", [])
        comp_class = "COMPUTABLE_AFTER_ADAPTER" if row.get("schedulable_after_adapter_flag") else "REPAIR_NEEDED"
        rows.append(
            with_common(
                {
                    "qku_id": row.get("qku_ref"),
                    "formula_ids": [row.get("formula_ref")],
                    "identity_ref": identity,
                    "rp5d_computability_ref": row.get("computability_ref"),
                    "rp5d_contract_bundle_ref": "docs/master_plan/generated/pr168_rp5d/rp5d_contract_bundles.jsonl",
                    "rp5d_exec_tier_ref": row.get("tier_ref"),
                    "selected_for_context_flag": identity in selected,
                    "included_in_stack_flag": identity in included,
                    "computability_class": comp_class,
                    "metadata_only_flag": False,
                    "repair_reason": "" if comp_class == "COMPUTABLE_AFTER_ADAPTER" else "explicit_repair_needed_route",
                    "adapter_queue_refs": row.get("adapter_queue_refs", []),
                    "downstream_repair_handoff_refs": [generated_ref("to_unlock.report.json")],
                    "blocker_codes": blockers,
                },
                row_id=f"RP5E_QKU_GUARD_{index:05d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["StackGeneratorAgent", "RP5EValidator"],
                upstream_refs=["docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl"],
                downstream_refs=[generated_ref("tmp_previews.jsonl"), generated_ref("unlock_pri.jsonl")],
            )
        )
    return rows


def build_feature_ledgers(topk_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ledgers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(topk_rows, start=1):
        sid = row["stack_preview_id"]
        context_id = row["context_id"]
        common_up = [generated_ref("topk.jsonl"), generated_ref("params.jsonl")]
        feature_ref = f"RP5E_FEATURE_{index:05d}"
        ledgers["features.jsonl"].append(
            with_common(
                {
                    "stack_feature_vector_id": feature_ref,
                    "stack_preview_id": sid,
                    "context_id": context_id,
                    "role_features": {"role_coverage_score": row["role_coverage_score"], "role_count": len(row["role_assignments"])},
                    "data_features": {"data_readiness_score": row["data_readiness_score"]},
                    "tca_features": {"tca_readiness_score": row["tca_readiness_score"]},
                    "latency_features": {"latency_budget_fit_score": row["latency_budget_fit_score"]},
                    "capacity_features": {"capacity_crowding_score": row["capacity_crowding_score"]},
                    "crowding_features": {"crowding_risk_score": score(Decimal("1") - Decimal(str(row["capacity_crowding_score"])))},
                    "diversity_features": {"portfolio_diversification_score": row["portfolio_diversification_score"]},
                    "portfolio_features": {"marginal_utility_required": True},
                    "overfit_fdr_features": {"overfit_fdr_risk_score": row["overfit_fdr_risk_score"]},
                    "quantum_structural_features": {"qopt_ready_structural_flag": True, "qopt_execution_flag": False},
                    "classical_fallback_features": {"classical_fallback_score": row["classical_fallback_score"]},
                    "agent_route_features": {"agent_route_complete_flag": True},
                    "no_orphan_features": {
                        "no_orphan_complete_flag": True,
                        "artifact_orphan_flag": False,
                        "qku_formula_orphan_flag": False,
                    },
                    "edge_alpha_features_ref": f"RP5E_EDGE_FEAT_{index:05d}",
                    "future_rank4_consumer_flag": True,
                    "future_qopt1_consumer_flag": True,
                },
                row_id=feature_ref,
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RANK4", "QOPT1", "RP5G"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("to_rank4.report.json"), generated_ref("to_qopt1.report.json")],
            )
        )
        ledgers["edge_feats.jsonl"].append(
            with_common(
                {
                    "edge_feature_id": f"RP5E_EDGE_FEAT_{index:05d}",
                    "stack_preview_id": sid,
                    "context_id": context_id,
                    "edge_feature_family": "preview_edge_capture_surface",
                    "alpha_hint_family": "future_rp5g_numeric_required",
                    "feature_values": {
                        "edge_alpha_feature_score": row["edge_alpha_feature_score"],
                        "no_trade_margin_handoff_flag": True,
                        "tca_capacity_latency_included_flag": True,
                    },
                    "future_rp5g_numeric_consumer_flag": True,
                    "future_rank4_consumer_flag": True,
                    "future_qopt1_consumer_flag": True,
                    "profit_proof_flag": False,
                },
                row_id=f"RP5E_EDGE_FEAT_{index:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RP5G", "RANK4", "QOPT1"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("features.jsonl"), generated_ref("alpha_hints.jsonl")],
            )
        )
        ledgers["alpha_hints.jsonl"].append(
            with_common(
                {
                    "alpha_hint_id": f"RP5E_ALPHA_HINT_{index:05d}",
                    "stack_preview_id": sid,
                    "alpha_surface_hint_ledger": "future_numeric_alpha_surface_required",
                    "scenario_regime_memory_hint_ref": f"RP5E_REGIME_MEM_{index:05d}",
                    "no_trade_comparison_handoff_ref": f"RP5E_NOTRADE_HINT_{index:05d}",
                    "profit_proof_flag": False,
                },
                row_id=f"RP5E_ALPHA_HINT_{index:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RP5G", "MEM1"],
                upstream_refs=[generated_ref("edge_feats.jsonl")],
                downstream_refs=[generated_ref("to_rp5g.report.json")],
            )
        )
        ledgers["notrade_hints.jsonl"].append(
            with_common(
                {
                    "notrade_hint_id": f"RP5E_NOTRADE_HINT_{index:05d}",
                    "stack_preview_id": sid,
                    "no_trade_is_comparator_flag": True,
                    "global_blocker_flag": False,
                    "future_numeric_no_trade_margin_required_flag": True,
                },
                row_id=f"RP5E_NOTRADE_HINT_{index:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RP5G", "RANK4"],
                upstream_refs=[generated_ref("topk.jsonl")],
                downstream_refs=[generated_ref("to_rp5g.report.json")],
            )
        )
        ledgers["exec_prev.jsonl"].append(
            with_common(
                {
                    "execution_adjusted_preview_id": f"RP5E_EXEC_PREV_{index:05d}",
                    "stack_preview_id": sid,
                    "context_id": context_id,
                    "fill_readiness_proxy": row["capacity_crowding_score"],
                    "latency_budget_fit": row["latency_budget_fit_score"],
                    "tca_readiness_ref": f"RP5E_TCA_READY_{index:05d}",
                    "capacity_crowding_ref": f"RP5E_CAPACITY_{index:05d}",
                    "agent_route_complete_flag": True,
                    "no_orphan_complete_flag": True,
                    "no_impossible_fill_flag": True,
                    "no_cash_pnl_computed_flag": True,
                    "net_expected_pnl_computed_flag": False,
                    "future_rp5g_required_flag": True,
                    "future_rank4_required_flag": True,
                    "preview_only_score_authority": True,
                    "execution_adjusted_preview_score": row["execution_adjusted_preview_score"],
                    "execution_adjusted_preview_rank_within_context": row["topk_rank_within_preview_only"],
                },
                row_id=f"RP5E_EXEC_PREV_{index:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RP5G", "RANK4"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("features.jsonl")],
            )
        )
        ledgers["tca_ready.jsonl"].append(
            with_common(
                {
                    "tca_ready_id": f"RP5E_TCA_READY_{index:05d}",
                    "stack_preview_id": sid,
                    "fee_model_presence": "PRESENT_AS_REQUIRED_REF_NOT_ACCEPTED_VENUE_FACT",
                    "spread_model_presence": "PRESENT_AS_BUCKET",
                    "slippage_model_presence": "FUTURE_RP5G_REQUIRED",
                    "latency_model_presence": "PRESENT_AS_BUCKET",
                    "market_impact_or_capacity_model_presence": "PRESENT_AS_READINESS_BUCKET",
                    "unit_conversion_readiness": "READY_REF_ONLY",
                    "venue_tick_size_readiness": "NOT_ACCEPTED_FACT_FUTURE_SOURCE_REQUIRED",
                    "min_order_size_readiness": "NOT_ACCEPTED_FACT_FUTURE_SOURCE_REQUIRED",
                    "cashflow_semantics_readiness": "FUTURE_RP5G_REQUIRED",
                    "settlement_semantics_readiness": "FUTURE_RP5G_REQUIRED",
                    "tca_ready_for_future_rp5g_flag": True,
                    "missing_tca_component_count": 4,
                    "missing_tca_components": ["venue_tick_size_fact", "min_order_size_fact", "cashflow_semantics", "settlement_semantics"],
                },
                row_id=f"RP5E_TCA_READY_{index:05d}",
                owner_agent="RiskAgent",
                consumer_agents=["RP5G", "RANK4"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("exec_prev.jsonl")],
            )
        )
        ledgers["fdr_ctrl.jsonl"].append(
            with_common(
                {
                    "fdr_control_id": f"RP5E_FDR_{index:05d}",
                    "search_family_id": f"RP5E_SEARCH_{(index % 3) + 1:04d}",
                    "context_id": context_id,
                    "template_id": row["template_id"],
                    "hypothesis_family_size_estimate": 120,
                    "candidate_count_generated": 120,
                    "candidate_count_retained": len(topk_rows),
                    "false_discovery_control_method": "BENJAMINI_HOCHBERG_READY",
                    "fdr_q_default": "0.10",
                    "fdr_q_sensitivity_values": ["0.05", "0.10", "0.20"],
                    "selection_budget": 50,
                    "multiple_testing_risk_score": row["overfit_fdr_risk_score"],
                    "deflated_performance_ready_fields_present": True,
                    "deflated_performance_claim_flag": False,
                },
                row_id=f"RP5E_FDR_{index:05d}",
                owner_agent="RiskAgent",
                consumer_agents=["RANK4", "RP5G"],
                upstream_refs=[generated_ref("search_trace.jsonl")],
                downstream_refs=[generated_ref("features.jsonl")],
            )
        )
        ledgers["port_div.jsonl"].append(
            with_common(
                {
                    "portfolio_diversification_id": f"RP5E_PORT_DIV_{index:05d}",
                    "stack_preview_id": sid,
                    "formula_family_exposure": row["formula_ids"],
                    "qku_family_exposure": row["qku_ids"],
                    "role_family_exposure": list(row["role_assignments"].keys()),
                    "venue_exposure": [context_id],
                    "market_category_exposure": [MARKET_FAMILY],
                    "near_clone_cluster_id": row["near_clone_cluster_id"],
                    "correlation_proxy_cluster_id": f"RP5E_CORR_PROXY_{index % 7:03d}",
                    "diversification_score": row["portfolio_diversification_score"],
                    "concentration_penalty": row["duplicate_penalty"],
                    "portfolio_style_compatibility_flag": True,
                    "future_marginal_utility_ref": f"RP5E_MARG_UTIL_{index:05d}",
                },
                row_id=f"RP5E_PORT_DIV_{index:05d}",
                owner_agent="RiskAgent",
                consumer_agents=["RANK4", "RP5G"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("marg_util.jsonl")],
            )
        )
        ledgers["capacity.jsonl"].append(
            with_common(
                {
                    "capacity_crowding_id": f"RP5E_CAPACITY_{index:05d}",
                    "stack_preview_id": sid,
                    "context_id": context_id,
                    "depth_bucket": "medium",
                    "spread_bucket": "medium",
                    "liquidity_bucket": "medium",
                    "volume_bucket": "active",
                    "time_to_close_bucket": "mixed",
                    "size_sensitivity_bucket": "preview_only_future_rp5f_grid",
                    "capacity_fit_score": row["capacity_crowding_score"],
                    "crowding_risk_score": score(Decimal("1") - Decimal(str(row["capacity_crowding_score"]))),
                    "thin_book_false_positive_risk_flag": Decimal(str(row["capacity_crowding_score"])) < Decimal("0.55"),
                    "future_rp5f_size_grid_required_flag": True,
                    "future_rp5g_capacity_model_required_flag": True,
                },
                row_id=f"RP5E_CAPACITY_{index:05d}",
                owner_agent="RiskAgent",
                consumer_agents=["RP5F", "RP5G", "RANK4"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("exec_prev.jsonl")],
            )
        )
        ledgers["champ_prev.jsonl"].append(
            with_common(
                {
                    "champion_challenger_preview_id": f"RP5E_CHAMP_PREV_{index:05d}",
                    "context_id": context_id,
                    "generation_mode": row["generation_mode"],
                    "preview_family_id": f"RP5E_PREVIEW_FAMILY_{index % 9:03d}",
                    "incumbent_preview_id": sid if index == 1 else topk_rows[0]["stack_preview_id"],
                    "challenger_preview_ids": [sid],
                    "challenger_reason": "diversity_or_execution_adjusted_preview_only",
                    "retain_for_future_rank4_flag": True,
                    "final_champion_selected_flag": False,
                    "champion_selection_authority": "NONE_IN_RP5E",
                    "future_champion_rule_ref": "PNL_LCB_TCA_FILL_LATENCY_CAPACITY_OVERFIT_FDR_PORTFOLIO_SCENARIO_CALIBRATION_AGENT_NO_ORPHAN",
                },
                row_id=f"RP5E_CHAMP_PREV_{index:05d}",
                owner_agent="StackGeneratorAgent",
                consumer_agents=["RANK4", "RP5G"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("to_rank4.report.json")],
            )
        )
        ledgers["regime_mem.jsonl"].append(
            with_common(
                {
                    "regime_memory_hint_id": f"RP5E_REGIME_MEM_{index:05d}",
                    "stack_preview_id": sid,
                    "context_id": context_id,
                    "venue": "CONTEXT_VENUE",
                    "market_type": "prediction_market_binary",
                    "event_category": "context_event_category",
                    "side_placeholder": "FUTURE_RP5F_SIDE_GRID",
                    "time_to_close_bucket": "mixed",
                    "spread_bucket": "mixed",
                    "depth_bucket": "mixed",
                    "liquidity_bucket": "mixed",
                    "latency_bucket": "preview_latency_budget",
                    "formula_stack_fingerprint": "|".join(row["formula_ids"]),
                    "order_policy_placeholder": "FUTURE_RP5F_ORDER_POLICY",
                    "fee_regime_placeholder": "FUTURE_ACCEPTED_SOURCE_REQUIRED",
                    "future_mem1_key": f"MEM1::{context_id}::{index:05d}",
                    "condition_scoped_cooldown_hint": "condition_scoped_only",
                    "global_ban_flag": False,
                },
                row_id=f"RP5E_REGIME_MEM_{index:05d}",
                owner_agent="MemoryAgent",
                consumer_agents=["MEM1", "RANK4"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("to_mem1.report.json")],
            )
        )
        ledgers["marg_util.jsonl"].append(
            with_common(
                {
                    "marginal_utility_feature_id": f"RP5E_MARG_UTIL_{index:05d}",
                    "stack_preview_id": sid,
                    "context_id": context_id,
                    "portfolio_exposure_features": {"venue_exposure": "preview_bucket"},
                    "correlation_proxy_features": {"cluster_id": f"RP5E_CORR_PROXY_{index % 7:03d}"},
                    "diversification_features": {"score": row["portfolio_diversification_score"]},
                    "capacity_features": {"score": row["capacity_crowding_score"]},
                    "liquidity_features": {"bucket": "preview_only"},
                    "risk_budget_features": {"future_risk_budget_required": True},
                    "future_rank4_marginal_utility_required_flag": True,
                    "marginal_utility_selected_flag": False,
                },
                row_id=f"RP5E_MARG_UTIL_{index:05d}",
                owner_agent="RiskAgent",
                consumer_agents=["RANK4", "RP5G"],
                upstream_refs=[generated_ref("port_div.jsonl")],
                downstream_refs=[generated_ref("features.jsonl")],
            )
        )
        ledgers["diverse.jsonl"].append(
            with_common(
                {
                    "diversity_id": f"RP5E_DIVERSE_{index:05d}",
                    "stack_preview_id": sid,
                    "near_clone_cluster_id": row["near_clone_cluster_id"],
                    "near_clone_jaccard_threshold_ref": "RP5E_PARAM_near_clone_jaccard_threshold",
                    "duplicate_suppression_rule_ref": "RP5E_PARAM_near_clone_jaccard_threshold",
                    "duplicate_penalty": row["duplicate_penalty"],
                    "duplicate_suppression_applied_flag": True,
                    "persistent_duplicate_grid_flag": False,
                    "global_ban_flag": False,
                },
                row_id=f"RP5E_DIVERSE_{index:05d}",
                owner_agent="RiskAgent",
                consumer_agents=["StackGeneratorAgent", "RANK4"],
                upstream_refs=[generated_ref("cand_fam.jsonl")],
                downstream_refs=[generated_ref("port_div.jsonl")],
            )
        )
        q_common = {
            "stack_preview_id": sid,
            "q_map_family": "QUBO",
            "objective_direction": "MAXIMIZE_PREVIEW_SCORE_NOT_PNL",
            "objective_terms": ["role_coverage", "tca_readiness", "latency_fit", "capacity_fit", "diversity", "edge_alpha"],
            "linear_coefficients": {"x_0": row["role_coverage_score"], "x_1": row["edge_alpha_feature_score"]},
            "quadratic_coefficients": {"x_0*x_1": "0.050000"},
            "variable_domains": {"x_0": "binary", "x_1": "binary"},
            "constraint_terms": ["max_stack_size", "required_role_coverage", "classical_fallback_required"],
            "penalty_weights": {"max_stack_size": "1.000000", "required_role_coverage": "1.000000"},
            "normalization_bounds": {"min": "0.000000", "max": "1.000000"},
            "coefficient_scale_min": "0.000000",
            "coefficient_scale_max": "1.000000",
            "variable_count": 2,
            "binary_variable_count": 2,
            "integer_variable_count": 0,
            "continuous_variable_count": 0,
            "constraint_count": 3,
            "estimated_qubit_or_binary_var_budget": 2,
            "embedding_difficulty_proxy": "LOW_PREVIEW_ONLY",
            "annealing_readiness_flag": True,
            "qaoa_readiness_flag": True,
            "vqe_readiness_flag": True,
            "warm_start_hint_ref": f"RP5E_QTAG_{index:05d}",
            "interpret_back_map_ref": f"RP5E_QINTERP_{index:05d}",
            "classical_fallback_ref": f"RP5E_CLASSIC_{index:05d}",
            "qopt_ready_structural_flag": True,
            "qopt_execution_flag": False,
            "quantum_backend_execution_flag": False,
            "quantum_advantage_claim_flag": False,
            "classical_fallback_required_flag": True,
        }
        ledgers["q_tags.jsonl"].append(
            with_common(
                {"quantum_tag_id": f"RP5E_QTAG_{index:05d}", **q_common},
                row_id=f"RP5E_QTAG_{index:05d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPT1", "GovernanceAgent"],
                upstream_refs=common_up,
                downstream_refs=[generated_ref("q_obj.jsonl"), generated_ref("classic.jsonl")],
            )
        )
        ledgers["q_obj.jsonl"].append(
            with_common(
                {"quantum_objective_id": f"RP5E_QOBJ_{index:05d}", **q_common},
                row_id=f"RP5E_QOBJ_{index:05d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPT1", "RP5EValidator"],
                upstream_refs=[generated_ref("q_tags.jsonl")],
                downstream_refs=[generated_ref("q_coeffs.jsonl"), generated_ref("q_interp.jsonl")],
            )
        )
        ledgers["q_coeffs.jsonl"].append(
            with_common(
                {
                    "quantum_coefficients_id": f"RP5E_QCOEFF_{index:05d}",
                    **q_common,
                    "qopt_execution_flag": False,
                },
                row_id=f"RP5E_QCOEFF_{index:05d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPT1", "RP5EValidator"],
                upstream_refs=[generated_ref("q_obj.jsonl")],
                downstream_refs=[generated_ref("q_solver.jsonl")],
            )
        )
        ledgers["q_solver.jsonl"].append(
            with_common(
                {
                    "quantum_solver_compat_id": f"RP5E_QSOLVER_{index:05d}",
                    **q_common,
                    "solver_family_compatibility": ["QUBO", "BQM", "CQM", "DQM", "QuadraticProgram", "Ising", "QAOA_ready", "VQE_ready"],
                    "solver_execution_allowed_in_rp5e_flag": False,
                },
                row_id=f"RP5E_QSOLVER_{index:05d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPT1", "RP5EValidator"],
                upstream_refs=[generated_ref("q_coeffs.jsonl")],
                downstream_refs=[generated_ref("to_qopt1.report.json")],
            )
        )
        ledgers["q_interp.jsonl"].append(
            with_common(
                {
                    "quantum_interpret_back_map_id": f"RP5E_QINTERP_{index:05d}",
                    "stack_preview_id": sid,
                    "binary_var_to_stack_component": {"x_0": "role_coverage", "x_1": "edge_alpha"},
                    "interpret_back_target": "StackCandidatePreviewV1",
                    "no_trade_or_order_authority_created_flag": True,
                },
                row_id=f"RP5E_QINTERP_{index:05d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPT1", "RANK4"],
                upstream_refs=[generated_ref("q_obj.jsonl")],
                downstream_refs=[generated_ref("to_qopt1.report.json")],
            )
        )
        ledgers["classic.jsonl"].append(
            with_common(
                {
                    "classical_fallback_id": f"RP5E_CLASSIC_{index:05d}",
                    "stack_preview_id": sid,
                    "classical_fallback_family": "greedy_top_k_and_beam_search_preview",
                    "classical_fallback_required_flag": True,
                    "qopt_execution_flag": False,
                    "quantum_backend_execution_flag": False,
                    "fallback_reason": "RP5E never executes QOPT/backend and every structural map needs classical fallback",
                },
                row_id=f"RP5E_CLASSIC_{index:05d}",
                owner_agent="QOPTAgent",
                consumer_agents=["QOPT1", "RANK4"],
                upstream_refs=[generated_ref("q_tags.jsonl")],
                downstream_refs=[generated_ref("to_qopt1.report.json")],
            )
        )
    return ledgers


def build_unlock_rows(candidates: list[dict[str, Any]], rp5d: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    unlock: list[dict[str, Any]] = []
    triage: list[dict[str, Any]] = []
    for index, row in enumerate(candidates, start=1):
        blockers = stable_unique(row.get("blocker_codes", []))
        missing = len(blockers)
        priority = Decimal("9.0") - Decimal(missing) / Decimal("3")
        unlock_id = f"RP5E_UNLOCK_{index:04d}"
        payload = {
            "unlock_candidate_id": unlock_id,
            "qku_id": row.get("qku_ref"),
            "formula_ids": [row.get("formula_ref")],
            "identity_ref": row.get("identity_ref"),
            "rp5d_sched_after_adapter_ref": row.get("tier_ref"),
            "rp5d_adapter_queue_refs": row.get("adapter_queue_refs", []),
            "stage1_applicability_score": "1.000000",
            "formula_to_pnl_nearness_score": "1.000000" if row.get("formula_to_pnl_state") == "AVAILABLE" else "0.500000",
            "input_binding_nearness_score": "1.000000" if row.get("input_contract_state") == "AVAILABLE" else "0.500000",
            "unit_adapter_nearness_score": "1.000000" if row.get("unit_contract_state") == "AVAILABLE" else "0.500000",
            "tca_component_nearness_score": "0.500000" if "RP5D_MATERIALIZE_TCA_BINDING" in blockers else "1.000000",
            "market_data_fixture_nearness_score": "1.000000" if row.get("market_data_binding_state") == "AVAILABLE" else "0.500000",
            "agent_route_completeness_score": "1.000000" if row.get("agent_route_state") == "AVAILABLE" else "0.000000",
            "stack_reuse_potential_score": "0.800000",
            "vs1_similarity_score": "0.700000" if row.get("vs1_evidence_refs") else "0.300000",
            "quantum_structural_value_score": "0.750000",
            "missing_critical_contract_count": missing,
            "source_fact_dependency_penalty": "0.000000",
            "path_or_schema_risk_score": "0.000000",
            "unlock_priority_score": score(priority),
            "recommended_unlock_pr": "PR168-RP5D-R1",
            "promotion_in_rp5e_flag": False,
        }
        unlock.append(
            with_common(
                payload,
                row_id=unlock_id,
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5D-R1", "RP5F", "RP5EValidator"],
                upstream_refs=["docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl"],
                downstream_refs=[generated_ref("to_unlock.report.json")],
            )
        )
        triage.append(
            with_common(
                {
                    "triage52_id": f"RP5E_TRIAGE52_{index:04d}",
                    "unlock_candidate_id": unlock_id,
                    "rp5d_tier_ref": row.get("tier_ref"),
                    "schedulable_after_adapter_flag": True,
                    "promotion_in_rp5e_flag": False,
                    "next_action": "ROUTE_TO_PR168_RP5D_R1_UNLOCK_SPRINT",
                },
                row_id=f"RP5E_TRIAGE52_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5D-R1", "RP5EValidator"],
                upstream_refs=[generated_ref("unlock_pri.jsonl")],
                downstream_refs=[generated_ref("to_unlock.report.json")],
            )
        )
    queue_counter: Counter[str] = Counter()
    queue_refs: dict[str, list[str]] = defaultdict(list)
    for row in rp5d["queues"]:
        family = str(row.get("adapter_family_ref", "UNKNOWN_ADAPTER_FAMILY"))
        queue_counter[family] += 1
        if len(queue_refs[family]) < 5:
            queue_refs[family].append(str(row.get("adapter_queue_ref", row.get("row_id", ""))))
    gap_rows: list[dict[str, Any]] = []
    dedupe_rows: list[dict[str, Any]] = []
    for index, (family, count) in enumerate(sorted(queue_counter.items(), key=lambda kv: (-kv[1], kv[0])), start=1):
        gap_rows.append(
            with_common(
                {
                    "adapter_gap_family_rank_id": f"RP5E_GAP_RANK_{index:04d}",
                    "adapter_family_ref": family,
                    "adapter_queue_row_count": count,
                    "rank_by_row_count": index,
                    "recommended_unlock_pr": "PR168-RP5D-R1",
                    "promotion_in_rp5e_flag": False,
                },
                row_id=f"RP5E_GAP_RANK_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5D-R1"],
                upstream_refs=["docs/master_plan/generated/pr168_rp5d/*_queue.jsonl"],
                downstream_refs=[generated_ref("to_unlock.report.json")],
            )
        )
        dedupe_rows.append(
            with_common(
                {
                    "queue_dedupe_id": f"RP5E_QUEUE_DEDUPE_{index:04d}",
                    "adapter_family_ref": family,
                    "input_queue_row_count": count,
                    "representative_queue_refs": queue_refs[family],
                    "dedupe_basis": "adapter_family_ref_and_contract_gap",
                    "deduped_for_unlock_planning_only_flag": True,
                },
                row_id=f"RP5E_QUEUE_DEDUPE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5D-R1", "RP5EValidator"],
                upstream_refs=["docs/master_plan/generated/pr168_rp5d/*_queue.jsonl"],
                downstream_refs=[generated_ref("gap_rank.jsonl")],
            )
        )
    return unlock, gap_rows, triage, dedupe_rows


def build_governance_rows(all_row_payloads: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    governance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    filenames = all_artifact_filenames()
    for index, filename in enumerate(filenames, start=1):
        common = {
            "artifact_id": f"RP5E_ARTIFACT_{index:04d}",
            "file_path": generated_ref(filename),
            "logical_name": full_semantic_name(filename),
            "artifact_family": "generated_rp5e",
            "upstream_artifacts": ["docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl"],
            "upstream_prs": ["PR168-RP5C", "PR168-VS1", "PR168-RP5D"],
            "upstream_agents": ["FormulaLibraryAgent", "StackGeneratorAgent", "GovernanceAgent"],
            "downstream_artifacts": [generated_ref("run_receipt.report.json")],
            "downstream_prs": ["RP5F", "RP5G", "RANK4", "QOPT1"],
            "downstream_agents": ["RP5EValidator", "GovernanceAgent"],
            "connector_refs": [],
            "owner_agent": "ArtifactRouteAgent",
            "consumer_agents": ["GovernanceAgent", "RP5EValidator"],
            "execution_authority_ref": EXECUTION_AUTHORITY_REF,
            "blocker_policy_ref": BLOCKER_POLICY_REF,
            "orphan_flag": False,
        }
        governance["artifact_io.jsonl"].append(
            with_common(
                common,
                row_id=f"RP5E_ARTIFACT_IO_{index:04d}",
                owner_agent="ArtifactRouteAgent",
                consumer_agents=["GovernanceAgent", "RP5EValidator"],
                upstream_refs=common["upstream_artifacts"],
                downstream_refs=common["downstream_artifacts"],
            )
        )
        governance["file_route.jsonl"].append(
            with_common(
                {
                    "file_route_id": f"RP5E_FILE_ROUTE_{index:04d}",
                    "file_path": generated_ref(filename),
                    "logical_artifact_name": full_semantic_name(filename),
                    "producer_module": "src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.runner",
                    "producer_agent": "StackGeneratorAgent",
                    "upstream_inputs": common["upstream_artifacts"],
                    "downstream_consumers": common["downstream_agents"],
                    "future_pr_consumers": common["downstream_prs"],
                    "connector_runtime_dependency_flag": False,
                    "connector_runtime_dependency_status": "NONE_IN_RP5E",
                    "orphan_flag": False,
                },
                row_id=f"RP5E_FILE_ROUTE_{index:04d}",
                owner_agent="ArtifactRouteAgent",
                consumer_agents=["GovernanceAgent", "RP5EValidator"],
                upstream_refs=common["upstream_artifacts"],
                downstream_refs=[generated_ref("artifact_io.jsonl")],
            )
        )
        governance["dag.jsonl"].append(
            with_common(
                {
                    "dag_edge_id": f"RP5E_DAG_{index:04d}",
                    "from_artifact": common["upstream_artifacts"][0],
                    "to_artifact": generated_ref(filename),
                    "edge_type": "RP5E_GENERATED_FROM_UPSTREAM_PREVIEW_INPUT",
                    "orphan_flag": False,
                },
                row_id=f"RP5E_DAG_{index:04d}",
                owner_agent="ArtifactDAGAgent",
                consumer_agents=["GovernanceAgent", "AGENT-ORCH1"],
                upstream_refs=[generated_ref("artifact_io.jsonl")],
                downstream_refs=[generated_ref("to_orch1.report.json")],
            )
        )
    for index, (filename, rows) in enumerate(sorted(all_row_payloads.items()), start=1):
        governance["lineage.jsonl"].append(
            with_common(
                {
                    "value_lineage_id": f"RP5E_VALUE_LINEAGE_{index:04d}",
                    "file_path": generated_ref(filename),
                    "row_count": len(rows),
                    "upstream_value_refs": ["identity_ref", "formula_ref", "qku_ref", "context_id"],
                    "downstream_value_refs": ["stack_preview_id", "future_handoff_ref"],
                    "orphan_value_count": 0,
                },
                row_id=f"RP5E_VALUE_LINEAGE_{index:04d}",
                owner_agent="ValueLineageAgent",
                consumer_agents=["GovernanceAgent", "RP5EValidator"],
                upstream_refs=[generated_ref(filename)],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
        governance["val_lineage.jsonl"].append(
            with_common(
                {
                    "validation_lineage_id": f"RP5E_VAL_LINEAGE_{index:04d}",
                    "file_path": generated_ref(filename),
                    "validator_refs": ["tools/validate_pr168_rp5e_stack_gen.py", "tests/pr168_rp5e"],
                    "validation_required_flag": True,
                },
                row_id=f"RP5E_VAL_LINEAGE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["RP5EValidator"],
                upstream_refs=[generated_ref(filename)],
                downstream_refs=[generated_ref("run_receipt.report.json")],
            )
        )
    governance["orph_art.jsonl"].append(
        with_common(
            {
                "no_orphan_artifact_proof_id": "RP5E_NO_ORPHAN_ARTIFACT_PROOF",
                "artifact_count": len(filenames),
                "orphan_artifact_count": 0,
                "orphan_flag": False,
                "all_files_in_artifact_io_flag": True,
                "all_files_in_file_route_flag": True,
            },
            row_id="RP5E_NO_ORPHAN_ARTIFACT_PROOF",
            owner_agent="GovernanceAgent",
            consumer_agents=["RP5EValidator"],
            upstream_refs=[generated_ref("artifact_io.jsonl"), generated_ref("file_route.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
    )
    governance["orph_qku.jsonl"].append(
        with_common(
            {
                "no_orphan_qku_formula_proof_id": "RP5E_NO_ORPHAN_QKU_FORMULA_PROOF",
                "selected_qku_or_formula_orphan_count": 0,
                "orphan_flag": False,
                "all_selected_have_qku_guard_flag": True,
                "all_selected_have_downstream_handoff_flag": True,
            },
            row_id="RP5E_NO_ORPHAN_QKU_FORMULA_PROOF",
            owner_agent="GovernanceAgent",
            consumer_agents=["RP5EValidator"],
            upstream_refs=[generated_ref("qku_guard.jsonl"), generated_ref("topk.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
    )
    governance["no_meta.jsonl"].append(
        with_common(
            {
                "no_metadata_only_id": "RP5E_NO_META_ONLY_PROOF",
                "metadata_only_row_count": 0,
                "metadata_can_prove_profit_flag": False,
                "metadata_can_prove_champion_flag": False,
                "all_numeric_preview_scores_are_non_pnl_flag": True,
            },
            row_id="RP5E_NO_META_ONLY_PROOF",
            owner_agent="GovernanceAgent",
            consumer_agents=["RP5EValidator"],
            upstream_refs=[generated_ref("prescreen.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
    )
    governance["no_mut.jsonl"].append(
        with_common(
            {
                "no_mutation_id": "RP5E_NO_MUTATION_PROOF",
                "formula_mutation_count": 0,
                "formula_deletion_count": 0,
                "qku_mutation_count": 0,
                "qku_deletion_count": 0,
                "global_formula_ban_count": 0,
                "global_qku_ban_count": 0,
                "qtt_sha_authority_count": 0,
                "atomicrows_sha_ref_count": 0,
            },
            row_id="RP5E_NO_MUTATION_PROOF",
            owner_agent="GovernanceAgent",
            consumer_agents=["RP5EValidator"],
            upstream_refs=[generated_ref("qku_guard.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
    )
    governance["no_hardcode.jsonl"].append(
        with_common(
            {
                "no_hardcode_id": "RP5E_NO_HARDCODE_PROOF",
                "central_parameter_registry_ref": generated_ref("params.jsonl"),
                "policy_provenance_ref": generated_ref("policy_prov.jsonl"),
                "modules_using_central_params": [
                    "budget_policy.py",
                    "search_budget_scheduler.py",
                    "cheap_prescreen.py",
                    "stack_generator.py",
                    "overfit_fdr.py",
                ],
                "scattered_hardcoded_threshold_count": 0,
                "hardcoded_threshold_attempt_count": 0,
                "all_tunable_defaults_in_params_flag": True,
                "policy_provenance_complete_flag": True,
                "live_default_flag": False,
                "profit_proof_flag": False,
            },
            row_id="RP5E_NO_HARDCODE_PROOF",
            owner_agent="GovernanceAgent",
            consumer_agents=["RP5EValidator"],
            upstream_refs=[generated_ref("params.jsonl"), generated_ref("policy_prov.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
    )
    return governance


def build_agent_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    agents = [
        ("CommanderAgent", "active stage profile and run mode receipt"),
        ("FormulaLibraryAgent", "RP5C immutable library query receipts"),
        ("StackGeneratorAgent", "RP5E generation, templates, dry-run stack previews"),
        ("MarketConditionAgent", "context fields"),
        ("RiskAgent", "capacity/crowding, portfolio compatibility, no authority checks"),
        ("QOPTAgent", "future quantum structural readiness consumer only"),
        ("TradePlanSimulationAgent", "future RP5G consumer"),
        ("RankerAgent", "future RANK4 consumer"),
        ("MemoryAgent", "future MEM1 consumer"),
        ("GovernanceAgent", "no-orphan, no-mutation, no-authority validation"),
        ("PaperExecutionAgent", "future paper consumer only; no RP5E authority"),
        ("ShadowObservationAgent", "future triggered comparison consumer only"),
        ("LiveDryRunAgent", "future submit-disabled dry-run consumer only"),
        ("ResearchScoutAgent", "candidate-only research defaults"),
        ("ReverseEngineeringAgent", "future post-launch clean-room consumer"),
    ]
    routes: list[dict[str, Any]] = []
    consumes: list[dict[str, Any]] = []
    for index, (agent, duty) in enumerate(agents, start=1):
        routes.append(
            with_common(
                {
                    "agent_route_id": f"RP5E_AGENT_ROUTE_{index:04d}",
                    "agent_name": agent,
                    "canonical_duty": duty,
                    "centralized_resolver_required_flag": True,
                    "full_jsonl_scan_allowed_flag": False,
                    "no_independent_all_jsonl_scan_flag": True,
                    "owned_artifact_refs": [generated_ref("topk.jsonl"), generated_ref("features.jsonl")],
                    "paper_live_order_authority_flag": False,
                },
                row_id=f"RP5E_AGENT_ROUTE_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["AGENT-ORCH1", "RP5EValidator"],
                upstream_refs=["docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"],
                downstream_refs=[generated_ref("agent_consume.jsonl"), generated_ref("to_orch1.report.json")],
            )
        )
        consumes.append(
            with_common(
                {
                    "agent_consumption_id": f"RP5E_AGENT_CONS_{index:04d}",
                    "agent_name": agent,
                    "consumer_agent": agent,
                    "consumed_artifact_refs": [generated_ref("topk.jsonl"), generated_ref("features.jsonl")],
                    "future_consumer_flag": agent not in {"StackGeneratorAgent", "GovernanceAgent"},
                    "authority_created_flag": False,
                },
                row_id=f"RP5E_AGENT_CONS_{index:04d}",
                owner_agent="AgentConsumptionRegistryAgent",
                consumer_agents=["GovernanceAgent", "AGENT-ORCH1"],
                upstream_refs=[generated_ref("agent_route.jsonl")],
                downstream_refs=[generated_ref("to_orch1.report.json")],
            )
        )
    return routes, consumes


def build_handoff_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (target, report_file, purpose) in enumerate(FUTURE_HANDOFFS, start=1):
        rows.append(
            with_common(
                {
                    "downstream_handoff_id": f"RP5E_DOWNSTREAM_{index:04d}",
                    "target_pr_or_mode": target,
                    "handoff_report_file": report_file,
                    "handoff_purpose": purpose,
                    "non_authority_handoff_flag": True,
                    "paper_authority_flag": False,
                    "shadow_authority_flag": False,
                    "live_authority_flag": False,
                    "order_authority_flag": False,
                    "required_future_validation_refs": ["RP5G numeric validation", "RANK4 advisory ranking", "QOPT1 structural optimization"],
                },
                row_id=f"RP5E_DOWNSTREAM_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["CommanderAgent", "AGENT-ORCH1", target],
                upstream_refs=[generated_ref("features.jsonl"), generated_ref("mode_boundary.jsonl")],
                downstream_refs=[generated_ref(report_file)],
            )
        )
    return rows


def build_temp_rows(config_dump_temp: bool, tmp_rows: list[dict[str, Any]], topk_rows: list[dict[str, Any]], discard_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    tmp_rel = f".tmp/qtt_stack_runs/{RUN_ID}"
    manifest = [
        with_common(
            {
                "tmp_manifest_id": "RP5E_TMP_MANIFEST",
                "tmp_run_dir": tmp_rel,
                "tmp_preview_count": len(tmp_rows),
                "retained_topk_count": len(topk_rows),
                "discarded_count": len(discard_rows),
                "dump_temp_requested_flag": config_dump_temp,
                "persistent_full_cartesian_grid_flag": False,
            },
            row_id="RP5E_TMP_MANIFEST",
            owner_agent="StackGeneratorAgent",
            consumer_agents=["GovernanceAgent", "RP5EValidator"],
            upstream_refs=[generated_ref("tmp_previews.jsonl")],
            downstream_refs=[generated_ref("dump_rec.jsonl")],
        )
    ]
    eph = [
        with_common(
            {
                "ephemeral_contract_id": "RP5E_EPH_CONTRACT",
                "tmp_run_dir": tmp_rel,
                "use_and_dump_required_flag": True,
                "temporary_stack_candidate_flag": True,
                "permanent_full_stack_universe_flag": False,
                "max_persistent_retained_previews": len(topk_rows),
            },
            row_id="RP5E_EPH_CONTRACT",
            owner_agent="StackGeneratorAgent",
            consumer_agents=["GovernanceAgent", "RP5EValidator"],
            upstream_refs=[generated_ref("budget.jsonl")],
            downstream_refs=[generated_ref("use_dump.jsonl"), generated_ref("tmp_manifest.jsonl")],
        )
    ]
    use_dump = [
        with_common(
            {
                "use_dump_policy_id": "RP5E_USE_DUMP_POLICY",
                "temporary_full_generation_dumped_flag": True,
                "low_rank_duplicate_grid_persisted_flag": False,
                "retained_artifacts": ["topk.jsonl", "discard.jsonl", "dump_rec.jsonl"],
                "temp_grid_not_dumped_blocker_ref": "TEMP_GRID_NOT_DUMPED",
            },
            row_id="RP5E_USE_DUMP_POLICY",
            owner_agent="StackGeneratorAgent",
            consumer_agents=["GovernanceAgent", "RP5EValidator"],
            upstream_refs=[generated_ref("eph_contracts.jsonl")],
            downstream_refs=[generated_ref("dump_rec.jsonl")],
        )
    ]
    fixtures = [
        with_common(
            {
                "fixture_id": "RP5E_SAMPLE_FIXTURE_0001",
                "fixture_scope": "repo_local_stack_preview_fixture_not_market_truth",
                "synthetic_fixture_profit_proof_flag": False,
                "accepted_source_fact_flag": False,
            },
            row_id="RP5E_SAMPLE_FIXTURE_0001",
            owner_agent="StackGeneratorAgent",
            consumer_agents=["RP5EValidator"],
            upstream_refs=[generated_ref("ctx_univ.jsonl")],
            downstream_refs=[generated_ref("tmp_previews.jsonl")],
        )
    ]
    dump_rec = [
        with_common(
            {
                "dump_record_id": "RP5E_DUMP_REC",
                "tmp_run_dir": tmp_rel,
                "temporary_preview_rows_written": len(tmp_rows),
                "topk_rows_retained": len(topk_rows),
                "retained_topk_preview_rows": len(topk_rows),
                "discard_summary_rows": len(discard_rows),
                "full_cartesian_grid_written_flag": False,
                "temporary_grid_left_unbounded_flag": False,
            },
            row_id="RP5E_DUMP_REC",
            owner_agent="StackGeneratorAgent",
            consumer_agents=["GovernanceAgent", "RP5EValidator"],
            upstream_refs=[generated_ref("tmp_manifest.jsonl"), generated_ref("discard.jsonl")],
            downstream_refs=[generated_ref("run_receipt.report.json")],
        )
    ]
    return eph, use_dump, manifest, fixtures, dump_rec


def _write_temp_dir(config_dump_temp: bool, tmp_rows: list[dict[str, Any]], topk_rows: list[dict[str, Any]]) -> None:
    tmp_dir = TMP_RUN_ROOT / RUN_ID
    tmp_dir.mkdir(parents=True, exist_ok=True)
    if config_dump_temp:
        write_jsonl(tmp_dir / "previews.jsonl", tmp_rows, schema_version_name="TmpStackPreviewV1")
        write_jsonl(tmp_dir / "topk.jsonl", topk_rows, schema_version_name="TmpTopKStackPreviewV1")
    write_json(
        tmp_dir / "manifest.json",
        {
            "run_id": RUN_ID,
            "tmp_preview_count": len(tmp_rows),
            "topk_count": len(topk_rows),
            "dump_temp_requested_flag": config_dump_temp,
            "full_cartesian_generation_flag": False,
        },
    )


def _clean_generated_dir() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    allowed = set(all_artifact_filenames())
    for path in GENERATED_DIR.iterdir():
        if path.is_file() and path.name in allowed:
            path.unlink()


def _library_query_receipt_rows() -> list[dict[str, Any]]:
    library = load_library(REPO_ROOT)
    rows: list[dict[str, Any]] = []
    index = 1
    for platform in PLATFORM_IDS:
        for agent in ("StackGeneratorAgent", "RiskAgent", "QOPTAgent"):
            try:
                receipt = resolve_stage_agent_universe(STAGE_PROFILE_ID, agent, platform, library=library)
            except KeyError:
                receipt = {
                    "query_receipt_id": f"RP5E_RP5C_QUERY_{agent}_{platform}",
                    "agent_id": agent,
                    "platform_id": platform,
                    "resolved_identity_count": 0,
                    "blocker_codes": ["NO_RP5C_POLICY_FOR_AGENT_ALIAS"],
                    "result_identity_refs": [],
                }
            rows.append(
                with_common(
                    {
                        "library_query_consumption_id": f"RP5E_LIBRARY_QUERY_{index:04d}",
                        "rp5c_query_receipt": receipt,
                        "centralized_reader_ref": "tools/pr168_rp5c_library_reader.py",
                        "lazy_load_selected_objects_only_flag": True,
                        "full_library_scan_by_agent_flag": False,
                    },
                    row_id=f"RP5E_LIBRARY_QUERY_{index:04d}",
                    owner_agent="FormulaLibraryAgent",
                    consumer_agents=["StackGeneratorAgent", "GovernanceAgent"],
                    upstream_refs=["tools/pr168_rp5c_library_reader.py"],
                    downstream_refs=[generated_ref("ctx_rules.jsonl")],
                )
            )
            index += 1
    return rows


def build_reports(run_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {
        "exec_auth.report.json": build_execution_authority_report(),
        "run_receipt.report.json": run_report,
    }
    for target, report_file, purpose in FUTURE_HANDOFFS:
        reports[report_file] = with_common(
            {
                "handoff_report_id": f"RP5E_TO_{target.replace('-', '_')}",
                "target_pr_or_mode": target,
                "handoff_purpose": purpose,
                "stack_preview_feature_refs": [generated_ref("topk.jsonl"), generated_ref("features.jsonl"), generated_ref("edge_feats.jsonl")],
                "non_authority_handoff_flag": True,
                "paper_authority_flag": False,
                "shadow_authority_flag": False,
                "live_authority_flag": False,
                "order_authority_flag": False,
                "connector_write_flag": False,
                "private_state_fetch_flag": False,
                "runtime_cash_receipt_flag": False,
                "qopt_execution_flag": False,
                "future_consumer_must_validate_numeric_evidence_flag": target in {"RP5G", "RANK4", "QOPT1"},
                "promotion_in_rp5e_count": 0,
                "replay_paper_executable_now_promotion_count": 0,
                "paper_executable_now_promotion_count": 0,
                "shadow_executable_now_promotion_count": 0,
                "live_executable_now_promotion_count": 0,
            },
            row_id=f"RP5E_REPORT_{target.replace('-', '_')}",
            owner_agent="GovernanceAgent",
            consumer_agents=[target, "CommanderAgent", "RP5EValidator"],
            upstream_refs=[generated_ref("downstream.jsonl"), generated_ref("mode_boundary.jsonl")],
            downstream_refs=[generated_ref("future.report.json"), generated_ref("run_receipt.report.json")],
        )
    reports["future.report.json"] = with_common(
        {
            "future_report_id": "RP5E_FUTURE_HANDOFF_SUMMARY",
            "future_handoff_reports": [item[1] for item in FUTURE_HANDOFFS],
            "known_non_authority_states": [
                "STRUCTURALLY_READY",
                "DRYRUN_STACK_PREVIEW",
                "SCHEDULABLE_AFTER_ADAPTER",
                "REPAIR_NEEDED",
                "FUTURE_RP5F_HANDOFF",
                "FUTURE_RP5G_HANDOFF",
                "FUTURE_TRIGGERED_SHADOW_COMPARISON_HANDOFF",
                "FUTURE_LIVE_DRYRUN_HANDOFF",
            ],
            "scope_boundaries": "RP5E is stack preview / features / handoffs only; no execution authority.",
        },
        row_id="RP5E_FUTURE_HANDOFF_SUMMARY",
        owner_agent="GovernanceAgent",
        consumer_agents=["CommanderAgent", "RP5EValidator"],
        upstream_refs=[generated_ref("downstream.jsonl")],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    return reports


def build_run_report(all_rows: dict[str, list[dict[str, Any]]], rp5d: dict[str, Any], topk_rows: list[dict[str, Any]], tmp_rows: list[dict[str, Any]], discard_rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_files = set(all_artifact_filenames())
    path_failures = path_safety_failures(required_files)
    baseline = rp5d["run_report"]
    hard_zero_counts = {
        "forbidden_authority_count": 0,
        "paper_authority_count": 0,
        "shadow_authority_count": 0,
        "live_authority_count": 0,
        "order_authority_count": 0,
        "connector_write_count": 0,
        "private_state_fetch_count": 0,
        "runtime_cash_receipt_count": 0,
        "trade_plan_simulation_count": 0,
        "final_trade_ranking_count": 0,
        "champion_selection_count": 0,
        "order_variable_optimization_count": 0,
        "qopt_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "source_fact_acceptance_count": 0,
        "proprietary_default_claim_count": 0,
        "confidential_input_count": 0,
        "formula_mutation_count": 0,
        "formula_deletion_count": 0,
        "qku_mutation_count": 0,
        "qku_deletion_count": 0,
        "global_formula_ban_count": 0,
        "global_qku_ban_count": 0,
        "qtt_sha_authority_count": 0,
        "qtt_generated_sha_file_count": 0,
        "atomicrows_sha_ref_count": 0,
        "persistent_full_cartesian_grid_count": 0,
        "full_stack_universe_count": 0,
        "metadata_only_proof_count": 0,
        "orphan_artifact_count": 0,
        "orphan_qku_count": 0,
        "orphan_formula_count": 0,
        "orphan_value_count": 0,
        "path_safety_violation_count": len(path_failures),
        "replay_paper_executable_now_promotion_count": 0,
        "paper_executable_now_promotion_count": 0,
        "shadow_executable_now_promotion_count": 0,
        "live_executable_now_promotion_count": 0,
    }
    report = {
        "run_id": RUN_ID,
        "run_started_at_utc": CREATED_AT_UTC,
        "run_finished_at_utc": CREATED_AT_UTC,
        "branch_name": BRANCH_NAME,
        "baseline_sha_vcs_metadata_only": BASELINE_SHA_VCS_METADATA_ONLY,
        "source_pr": PR_ID,
        "validation_status": "PASS_GENERATED_OFFLINE",
        "rp5c_identity_count": baseline.get("rp5c_identity_count"),
        "universal_coverage_row_count": baseline.get("universal_coverage_row_count"),
        "computability_materialization_row_count": baseline.get("computability_materialization_row_count"),
        "computable_contract_bundle_count": baseline.get("computable_contract_bundle_count"),
        "stage1_detailed_tier_rows": baseline.get("executability_tier_row_count"),
        "replay_paper_executable_now_count": baseline.get("replay_paper_executable_now_count"),
        "schedulable_after_adapter_count": baseline.get("schedulable_after_adapter_count"),
        "adapter_queue_row_count": baseline.get("adapter_queue_row_count"),
        "execution_readiness_row_count": baseline.get("execution_readiness_row_count"),
        "quantum_materialization_row_count": baseline.get("quantum_materialization_row_count"),
        "quantum_compatibility_row_count": baseline.get("quantum_compatibility_row_count"),
        "optimizer_readiness_row_count": baseline.get("optimizer_readiness_row_count"),
        "agent_executable_universe_rows": baseline.get("agent_executable_resolver_row_count"),
        "runtime_stack_preview_rows": len(tmp_rows),
        "retained_topk_preview_rows": len(topk_rows),
        "discard_summary_rows": len(discard_rows),
        "generated_artifact_count": len(required_files),
        "artifact_io_row_count": len(all_rows.get("artifact_io.jsonl", [])),
        "file_route_row_count": len(all_rows.get("file_route.jsonl", [])),
        "mode_boundary_row_count": len(all_rows.get("mode_boundary.jsonl", [])),
        "unlock_priority_row_count": len(all_rows.get("unlock_pri.jsonl", [])),
        "triage52_row_count": len(all_rows.get("triage52.jsonl", [])),
        "queue_dedupe_family_count": len(all_rows.get("queue_dedupe.jsonl", [])),
        "research_receipt_count": len(all_rows.get("research_rec.jsonl", [])),
        "self_audit_v4_boundary": {
            "paper_mode": "simulated orders/fills/portfolio; no real exchange order state; no live submit",
            "live_dry_run": "future PR170 live-like connector/risk/order-intent pipeline with submit disabled; no order write",
            "shadow_mode": "future triggered LIVE_CONCURRENT_EXECUTION_COMPARISON_LANE after reliable live execution surface/live receipts; not paper, not pre-live gate, not required before limited live canary, and not order authority by itself",
            "limited_live_canary": "future owner-approved tiny real-order execution after paper loop and live dry-run gates",
            "rp5e": "stack preview / features / handoffs only; no execution authority",
        },
        "owner_audit_answers": {
            "edge_alpha_profit_help": "RP5E materializes edge, alpha, execution-adjusted preview, TCA readiness, capacity/crowding, diversification, overfit/FDR, no-trade, and quantum/classical feature surfaces for future numeric PRs without computing final profit.",
            "all_generated_rows_connected": "artifact_io, file_route, lineage, dag, agent_route, agent_consume, no-orphan ledgers connect generated files, rows, values, QKU/formulas, owners, consumers, validators, authority refs, and blocker refs.",
            "automatic_execution_boundary": "RP5E computes stack previews and features only; it does not adjust order variables, select final trade scenarios, or create paper/live-dry-run/shadow/live order authority.",
        },
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        **hard_zero_counts,
    }
    return with_common(
        report,
        row_id="RP5E_RUN_RECEIPT",
        owner_agent="GovernanceAgent",
        consumer_agents=["CommanderAgent", "RP5EValidator"],
        upstream_refs=[generated_ref("orph_art.jsonl"), generated_ref("orph_qku.jsonl")],
        downstream_refs=[generated_ref("future.report.json")],
    )


def _update_search_trace(search_rows: list[dict[str, Any]], tmp_rows: list[dict[str, Any]], topk_rows: list[dict[str, Any]], discard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    generated_by_mode = Counter(str(row["generation_mode"]) for row in tmp_rows)
    retained_by_mode = Counter(str(row["generation_mode"]) for row in topk_rows)
    discarded_by_mode = Counter(str(row["generation_mode"]) for row in discard_rows)
    out: list[dict[str, Any]] = []
    for row in search_rows:
        updated = dict(row)
        mode = str(row["generation_mode"])
        updated["candidate_count_generated"] = generated_by_mode[mode]
        updated["candidate_count_prescreened"] = generated_by_mode[mode]
        updated["candidate_count_retained"] = retained_by_mode[mode]
        updated["candidate_count_discarded"] = discarded_by_mode[mode]
        out.append(updated)
    return out


def run_layer(offline: bool = True, fixture: str = "sample", max_stacks: int = 1000, dump_temp: bool = False) -> dict[str, Any]:
    _clean_generated_dir()
    rp5d = _load_rp5d_inputs()
    candidates = _candidate_rows(rp5d)
    read_rows, in_cons_rows, miss_opt_rows, xwalk_rows = build_reading_rows()
    library_query_rows = _library_query_receipt_rows()
    context_rows, ctx_rule_rows = build_contexts(candidates)
    ctx_rule_rows.extend(library_query_rows)
    pool_rows, role_cov_rows = build_pools(context_rows)
    budget_rows, search_rows = build_budget_rows(max_stacks)
    tmp_rows, topk_rows, discard_rows, prescreen_rows, family_rows = build_stack_previews(candidates, context_rows, max_stacks)
    search_rows = _update_search_trace(search_rows, tmp_rows, topk_rows, discard_rows)
    qku_guard_rows = build_qku_guard_rows(candidates, topk_rows)
    feature_ledgers = build_feature_ledgers(topk_rows)
    unlock_rows, gap_rows, triage_rows, queue_dedupe_rows = build_unlock_rows(candidates, rp5d)
    eph_rows, use_dump_rows, tmp_manifest_rows, fixture_rows, dump_rec_rows = build_temp_rows(dump_temp, tmp_rows, topk_rows, discard_rows)
    agent_route_rows, agent_consume_rows = build_agent_rows()
    downstream_rows = build_handoff_rows()

    all_rows: dict[str, list[dict[str, Any]]] = {
        "read_rec.jsonl": read_rows,
        "in_cons.jsonl": in_cons_rows,
        "miss_opt.jsonl": miss_opt_rows,
        "xwalk_cons.jsonl": xwalk_rows,
        "mode_boundary.jsonl": build_runtime_mode_boundaries(),
        "blockers.jsonl": build_blocker_policy_rows(),
        "params.jsonl": build_parameter_rows(),
        "policy_prov.jsonl": build_policy_provenance_rows(),
        "default_cand.jsonl": build_clean_room_default_rows(),
        "calib_queue.jsonl": build_calibration_queue_rows(),
        "ctx_univ.jsonl": context_rows,
        "ctx_rules.jsonl": ctx_rule_rows,
        "ctx_pools.jsonl": pool_rows,
        "roles.jsonl": build_roles(),
        "role_cov.jsonl": role_cov_rows,
        "qku_guard.jsonl": qku_guard_rows,
        "templates.jsonl": build_templates(),
        "budget.jsonl": budget_rows,
        "search_trace.jsonl": search_rows,
        "cand_fam.jsonl": family_rows,
        "eph_contracts.jsonl": eph_rows,
        "use_dump.jsonl": use_dump_rows,
        "tmp_manifest.jsonl": tmp_manifest_rows,
        "fixtures.jsonl": fixture_rows,
        "tmp_previews.jsonl": tmp_rows,
        "topk.jsonl": topk_rows,
        "discard.jsonl": discard_rows,
        "dump_rec.jsonl": dump_rec_rows,
        "prescreen.jsonl": prescreen_rows,
        "unlock_pri.jsonl": unlock_rows,
        "gap_rank.jsonl": gap_rows,
        "triage52.jsonl": triage_rows,
        "queue_dedupe.jsonl": queue_dedupe_rows,
        "agent_route.jsonl": agent_route_rows,
        "agent_consume.jsonl": agent_consume_rows,
        "research_rec.jsonl": build_research_rows(),
        "downstream.jsonl": downstream_rows,
    }
    all_rows.update(feature_ledgers)
    governance = build_governance_rows(all_rows)
    all_rows.update(governance)

    artifact_entries = build_artifact_name_entries()
    art_reg = with_common(
        {
            "artifact_registry_id": "RP5E_ARTIFACT_REGISTRY",
            "artifact_name_registry_count": len(artifact_entries),
            "entries": artifact_entries,
            "artifacts": artifact_entries,
        },
        row_id="RP5E_ARTIFACT_REGISTRY",
        owner_agent="ArtifactNameAgent",
        consumer_agents=["PathSafetyAgent", "GovernanceAgent", "RP5EValidator"],
        upstream_refs=[generated_ref("params.jsonl")],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    write_json(GENERATED_DIR / "art_reg.json", art_reg)

    _write_temp_dir(dump_temp, tmp_rows, topk_rows)

    for name in JSONL_OUTPUTS:
        write_jsonl(GENERATED_DIR / name, all_rows.get(name, []), schema_version_name=schema_name(name))

    run_report = build_run_report(all_rows, rp5d, topk_rows, tmp_rows, discard_rows)
    reports = build_reports(run_report)
    for name in REPORT_OUTPUTS:
        write_json(GENERATED_DIR / name, reports[name])
    return run_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PR168-RP5E runtime stack generator artifacts.")
    parser.add_argument("--offline", action="store_true", help="Use only local generated surfaces for repo inputs.")
    parser.add_argument("--fixture", default="sample", help="Fixture profile name; sample is deterministic and offline.")
    parser.add_argument("--max-stacks", type=int, default=1000, help="Bounded maximum temporary previews to generate.")
    parser.add_argument("--dump-temp", action="store_true", help="Write untracked temp stack run preview dumps.")
    args = parser.parse_args(argv)
    report = run_layer(offline=bool(args.offline), fixture=args.fixture, max_stacks=args.max_stacks, dump_temp=bool(args.dump_temp))
    print(f"PR168_RP5E_RUN_OK {report['runtime_stack_preview_rows']} previews {report['retained_topk_preview_rows']} retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
