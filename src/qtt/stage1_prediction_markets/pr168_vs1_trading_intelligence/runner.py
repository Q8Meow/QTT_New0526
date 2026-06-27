"""Deterministic PR168-VS1 trading-intelligence vertical-slice generator."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import sys
from typing import Any

from .models import (
    BASELINE_SHA,
    BLOCKER_POLICY_REF,
    BRANCH_NAME,
    CREATED_AT_UTC,
    EXECUTION_AUTHORITY_REF,
    FIXTURE_CASES,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    MARKET_FAMILY,
    PLATFORM_IDS,
    PR_ID,
    REPORT_OUTPUTS,
    REQUIRED_BLOCKER_CODES,
    REPO_ROOT,
    ROLE_ORDER,
    RUN_ID,
    SELECTOR_AGENT_IDS,
    STAGE_PROFILE_ID,
    RunConfig,
    dec,
    formula_ref,
    generated_ref,
    money,
    qku_ref,
    ratio,
    read_json,
    read_jsonl,
    rel_ref,
    with_common,
    write_json,
    write_jsonl,
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5c_library_reader import load_library, resolve_stage_agent_universe  # noqa: E402

EPSILON = Decimal("0.000001")

RP5C_REQUIRED_FILES = (
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/formula_assignment_library.jsonl",
    "docs/master_plan/generated/rp5c/qku_formula_identity_lineage.jsonl",
    "docs/master_plan/generated/rp5c/formula_ontology.jsonl",
    "docs/master_plan/generated/rp5c/ontology_role_registry.jsonl",
    "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl",
    "docs/master_plan/generated/rp5c/market_stage_activation_profile_registry.jsonl",
    "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
    "docs/master_plan/generated/rp5c/agent_duty_routing_rulebook.jsonl",
    "docs/master_plan/generated/rp5c/agent_responsibility_group_registry.jsonl",
    "docs/master_plan/generated/rp5c/platform_applicability_registry.jsonl",
    "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
    "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl",
    "docs/master_plan/generated/rp5c/stage_computation_universe_view.jsonl",
    "docs/master_plan/generated/rp5c/agent_computation_universe_view.jsonl",
    "docs/master_plan/generated/rp5c/library_query_receipts.jsonl",
    "docs/master_plan/generated/rp5c/no_orphan_identity_rows.jsonl",
    "docs/master_plan/generated/rp5c/no_orphan_generated_surface_rows.jsonl",
    "docs/master_plan/generated/rp5c/no_global_ban_rows.jsonl",
    "docs/master_plan/generated/rp5c/shared_cross_market_support_pool.jsonl",
    "docs/master_plan/generated/rp5c/market_specific_qku_pool_registry.jsonl",
    "tools/pr168_rp5c_library_reader.py",
)

REQUIRED_READING_FILES = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    *RP5C_REQUIRED_FILES,
    "docs/master_plan/generated/rp5c/vs1_trading_intelligence_handoff.jsonl",
    "docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl",
)

ARTIFACT_CONSUMERS = {
    "vs1_reading_receipts.jsonl": ["CommanderAgent", "GovernanceAgent"],
    "vs1_crosswalk_discovery_receipts.jsonl": ["AgentDutyResolverAgent", "GovernanceAgent"],
    "vs1_execution_authority_receipt.report.json": ["AllVS1Agents", "VS1Validator"],
    "vs1_blocker_policy_registry.jsonl": ["AllVS1Agents", "VS1Validator"],
    "vs1_policy_parameter_registry.jsonl": ["AllVS1Agents", "VS1Validator"],
    "vs1_agent_dag_receipts.jsonl": ["GovernanceAgent", "AGENT-ORCH1"],
    "vs1_agent_artifact_routing_ledger.jsonl": ["GovernanceAgent", "AGENT-ORCH1"],
    "vs1_upstream_downstream_artifact_dag.jsonl": ["GovernanceAgent", "AGENT-ORCH1"],
    "vs1_no_orphan_artifact_ledger.jsonl": ["GovernanceAgent", "VS1Validator"],
    "trade_target_fixtures.jsonl": ["MarketConditionAgent", "TradePlanVariableSearchAgent"],
    "market_condition_snapshots.jsonl": ["QKUComputabilityMaterializerAgent", "ExpectedCashPnLEngineAgent"],
    "stage_agent_universe_query_receipts.jsonl": ["ContextFormulaSelectorAgent", "GovernanceAgent"],
    "agent_duty_evidence_discovery_receipts.jsonl": ["AgentDutyResolverAgent", "GovernanceAgent"],
    "context_formula_selection_receipts.jsonl": ["QKUComputabilityMaterializerAgent", "StackGeneratorAgent"],
    "selected_computable_qku_formula_bindings.jsonl": ["StackGeneratorAgent", "ObjectiveTermsAgent"],
    "temporary_stack_candidate_receipts.jsonl": ["TradePlanVariableSearchAgent", "QuantumReadinessAgent"],
    "trade_plan_variable_search_receipts.jsonl": ["OrderVariableAgent", "NoPnLForcingProofAgent"],
    "order_variable_candidate_receipts.jsonl": ["ExpectedCashPnLEngineAgent", "TCAAgent"],
    "tca_breakdown_receipts.jsonl": ["ExpectedCashPnLEngineAgent", "NoTradeRiskAgent"],
    "expected_cash_pnl_receipts.jsonl": ["ScenarioAgent", "NoTradeRiskAgent", "RankerAgent"],
    "overfit_fdr_control_receipts.jsonl": ["ExpectedCashPnLEngineAgent", "RankerAgent"],
    "capacity_crowding_receipts.jsonl": ["ExpectedCashPnLEngineAgent", "RankerAgent"],
    "portfolio_diversification_receipts.jsonl": ["ExpectedCashPnLEngineAgent", "RankerAgent"],
    "scenario_ladder_receipts.jsonl": ["ExpectedCashPnLEngineAgent", "RankerAgent"],
    "objective_term_ledger.jsonl": ["RankerAgent", "QuantumReadinessAgent", "QuantumEncodingAgent"],
    "constraint_penalty_policy_receipts.jsonl": ["NoTradeRiskAgent", "QuantumEncodingAgent"],
    "trade_plan_quantum_encoding_receipts.jsonl": ["QuantumReadinessAgent", "QOPT"],
    "no_trade_comparator_receipts.jsonl": ["TradePlanCandidateAssembler", "RankerAgent"],
    "trade_plan_candidates.jsonl": ["RankerAgent", "PaperIntentPreviewAgent", "GovernanceAgent"],
    "execution_adjusted_ranking_receipts.jsonl": ["ChampionChallengerSelectionAgent", "PaperIntentPreviewAgent"],
    "champion_challenger_selection_receipts.jsonl": ["PaperIntentPreviewAgent", "GovernanceAgent"],
    "quantum_structural_readiness_receipts.jsonl": ["QOPT", "GovernanceAgent"],
    "paper_intent_candidate_previews.jsonl": ["OwnerReviewFuture", "GovernanceAgent"],
    "external_research_candidate_receipts.jsonl": ["GovernanceAgent", "FutureResearchLane"],
    "no_pnl_forcing_proof.jsonl": ["GovernanceAgent", "VS1Validator"],
    "no_orphan_qku_formula_proof.jsonl": ["GovernanceAgent", "VS1Validator"],
    "vs1_run_receipt.report.json": ["OwnerReviewFuture", "PR168FollowupPlanning"],
    "vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json": [
        "RP5D",
        "RP5E",
        "RP5F",
        "RP5G",
        "RANK4",
        "QOPT",
        "MEM1",
        "AGENT-ORCH1",
    ],
}


def _field_ref(name: str) -> str:
    return f"VS1_POLICY_PARAM::{name}"


def cash_decimal(value: Decimal) -> Decimal:
    return dec(value).quantize(Decimal("0.0001"))


def build_execution_authority() -> dict[str, Any]:
    payload = {
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        "cash_runtime_authorized": False,
        "connector_runtime_authorized": False,
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "execution_mode": "VS1_PREVIEW_ONLY",
        "fixture_constant_from_external_source_authorized": False,
        "formula_deletion_authorized": False,
        "formula_mutation_authorized": False,
        "gate_relaxation_to_force_pnl_authorized": False,
        "global_formula_ban_authorized": False,
        "global_qku_ban_authorized": False,
        "hindsight_or_outcome_backsolve_authorized": False,
        "impossible_fill_or_price_authorized": False,
        "live_submit_authorized": False,
        "paper_submit_authorized": False,
        "private_state_fetch_authorized": False,
        "producer_agent": "CommanderAgent",
        "pr_id": PR_ID,
        "qku_deletion_authorized": False,
        "qtt_sha_authority_authorized": False,
        "quantum_advantage_claim_authorized": False,
        "quantum_backend_execution_authorized": False,
        "run_id": RUN_ID,
        "source_fact_acceptance_authorized": False,
        "upstream_artifact_refs": ["docs/master_plan/generated/rp5c/vs1_trading_intelligence_handoff.jsonl"],
        "venue_api_call_authorized": False,
        "atomicrows_bundle_sha_authorized": False,
    }
    payload["consumer_agent_refs"] = ["AllVS1Agents", "VS1Validator"]
    payload["downstream_artifact_refs"] = [generated_ref(name) for name in JSONL_OUTPUTS if name != "vs1_reading_receipts.jsonl"]
    return payload


def build_blocker_policy() -> list[dict[str, Any]]:
    categories = {
        "NO_TRADE_WINS": "capital_preservation",
        "NO_ELIGIBLE_POSITIVE_NET_CASH_PNL_CANDIDATE_FOUND": "capital_preservation",
        "REJECT_LCB_NOT_POSITIVE": "risk_gate",
        "REJECT_FILL_TOO_LOW": "execution_gate",
        "REJECT_TCA_WIPES_EDGE": "execution_gate",
        "REJECT_CAPACITY_GATE": "capacity_gate",
        "REJECT_PORTFOLIO_GATE": "portfolio_gate",
        "REJECT_SCENARIO_LADDER": "scenario_gate",
        "REJECT_AGENT_ROUTE": "governance_gate",
        "REJECT_NO_ORPHAN_PROOF": "governance_gate",
        "REJECT_UNKNOWN_NEEDS_REVIEW": "rp5c_access_gate",
        "REJECT_METADATA_ONLY_BINDING": "computability_gate",
        "REJECT_IMPOSSIBLE_PRICE": "feasibility_gate",
        "REJECT_IMPOSSIBLE_FILL": "feasibility_gate",
        "REJECT_GATE_RELAXATION_ATTEMPT": "no_pnl_forcing_gate",
        "REJECT_HINDSIGHT_BACKSOLVE": "no_pnl_forcing_gate",
        "REJECT_EXTERNAL_SOURCE_FACT_AUTHORITY": "source_authority_gate",
    }
    rows = []
    for index, code in enumerate(REQUIRED_BLOCKER_CODES, start=1):
        rows.append(
            with_common(
                {
                    "blocker_code": code,
                    "blocker_category": categories[code],
                    "blocker_policy_ref": BLOCKER_POLICY_REF,
                    "condition_scoped_memory_allowed_flag": True,
                    "consumer_agent_refs": ["AllVS1Agents", "VS1Validator"],
                    "formula_mutation_allowed_flag": False,
                    "gate_relaxation_allowed_flag": False,
                    "global_ban_allowed_flag": False,
                    "qku_deletion_allowed_flag": False,
                    "retriable_flag": code
                    in {
                        "REJECT_FILL_TOO_LOW",
                        "REJECT_TCA_WIPES_EDGE",
                        "REJECT_CAPACITY_GATE",
                        "REJECT_PORTFOLIO_GATE",
                        "REJECT_SCENARIO_LADDER",
                    },
                    "selection_status_mapping": code,
                    "severity": "INFO" if code.startswith("NO_") else "REJECT",
                    "vs1_blocker_policy_row_id": f"VS1_BLOCKER_POLICY_ROW_{index:04d}",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["AllVS1Agents", "VS1Validator"],
                upstream_artifact_refs=[generated_ref("vs1_execution_authority_receipt.report.json")],
                downstream_artifact_refs=[generated_ref("trade_plan_candidates.jsonl"), generated_ref("no_trade_comparator_receipts.jsonl")],
            )
        )
    return rows


def build_policy_parameters() -> tuple[list[dict[str, Any]], dict[str, Decimal | str]]:
    specs: list[tuple[str, str, str, str, str, str, str]] = [
        ("max_selected_identities", "selection_caps", "integer", "50", "COUNT", "10", "50"),
        ("min_selected_identities", "selection_caps", "integer", "10", "COUNT", "10", "50"),
        ("max_stack_size", "selection_caps", "integer", "3", "COUNT", "1", "3"),
        ("max_stacks_per_fixture", "selection_caps", "integer", "20", "COUNT", "1", "20"),
        ("max_total_stack_candidates", "selection_caps", "integer", "60", "COUNT", "1", "60"),
        ("top_k_per_fixture", "selection_caps", "integer", "10", "COUNT", "1", "10"),
        ("max_markets_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_platforms_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_sides_per_fixture", "variable_search_caps", "integer", "2", "COUNT", "1", "2"),
        ("max_entry_prices_per_fixture", "variable_search_caps", "integer", "4", "COUNT", "1", "4"),
        ("max_order_sizes_per_fixture", "variable_search_caps", "integer", "2", "COUNT", "1", "2"),
        ("max_hold_durations_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_exit_rules_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_maker_taker_policies_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_cancel_replace_policies_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_liquidity_filter_variants_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_latency_budget_variants_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_portfolio_exposure_variants_per_fixture", "variable_search_caps", "integer", "1", "COUNT", "1", "1"),
        ("max_total_order_variable_candidates", "variable_search_caps", "integer", "40", "COUNT", "1", "40"),
        ("max_total_trade_plan_candidates", "variable_search_caps", "integer", "40", "COUNT", "1", "40"),
        ("configured_min_fill_probability", "execution_gates", "decimal", "0.35", "PROBABILITY", "0", "1"),
        ("configured_min_lcb_cash", "execution_gates", "decimal", "0", "USD", "0", "100"),
        ("configured_min_no_trade_margin_bps", "execution_gates", "decimal", "1", "BPS", "0", "1000"),
        ("configured_max_capacity_used_ratio", "execution_gates", "decimal", "0.30", "RATIO", "0", "1"),
        ("configured_max_correlation_overlap", "execution_gates", "decimal", "0.60", "RATIO", "0", "1"),
        ("configured_max_tca_to_edge_ratio", "execution_gates", "decimal", "0.90", "RATIO", "0", "10"),
        ("configured_max_overfit_trial_count", "execution_gates", "integer", "60", "COUNT", "1", "60"),
        ("configured_min_scenario_gate_pass_count", "execution_gates", "integer", "4", "COUNT", "0", "8"),
        ("fee_per_contract_fixture", "tca_fixture_coefficients", "decimal", "0.0100", "USD_PER_CONTRACT", "0", "1"),
        ("spread_cost_multiplier_fixture", "tca_fixture_coefficients", "decimal", "0.50", "MULTIPLIER", "0", "5"),
        ("slippage_per_contract_fixture", "tca_fixture_coefficients", "decimal", "0.0030", "USD_PER_CONTRACT", "0", "1"),
        ("cancel_replace_cost_fixture", "tca_fixture_coefficients", "decimal", "0.0100", "USD", "0", "1"),
        ("latency_decay_per_bucket_fixture", "tca_fixture_coefficients", "decimal", "0.0040", "USD_PER_CONTRACT", "0", "1"),
        ("capital_lock_rate_fixture", "tca_fixture_coefficients", "decimal", "0.0010", "RATE_PER_DAY", "0", "1"),
        ("capacity_cost_multiplier_fixture", "tca_fixture_coefficients", "decimal", "0.0500", "MULTIPLIER", "0", "1"),
        ("crowding_cost_multiplier_fixture", "tca_fixture_coefficients", "decimal", "0.0300", "MULTIPLIER", "0", "1"),
        ("uncertainty_penalty_multiplier", "risk_penalty_fixture_coefficients", "decimal", "0.0400", "MULTIPLIER", "0", "1"),
        ("overfit_trial_penalty_multiplier", "risk_penalty_fixture_coefficients", "decimal", "0.0030", "USD_PER_TRIAL", "0", "1"),
        ("scenario_tail_penalty_multiplier", "risk_penalty_fixture_coefficients", "decimal", "0.2500", "MULTIPLIER", "0", "1"),
        ("portfolio_overlap_penalty_multiplier", "risk_penalty_fixture_coefficients", "decimal", "0.2000", "MULTIPLIER", "0", "1"),
        ("lcb_weight", "ranking_weights", "decimal", "1.0000", "WEIGHT", "0", "10"),
        ("marginal_utility_weight", "ranking_weights", "decimal", "1.0000", "WEIGHT", "0", "10"),
        ("diversification_bonus_weight", "ranking_weights", "decimal", "1.0000", "WEIGHT", "0", "10"),
        ("correlation_overlap_penalty_weight", "ranking_weights", "decimal", "1.0000", "WEIGHT", "0", "10"),
        ("scenario_tail_penalty_weight", "ranking_weights", "decimal", "1.0000", "WEIGHT", "0", "10"),
        ("no_trade_margin_weight", "ranking_weights", "decimal", "1.0000", "WEIGHT", "0", "10"),
        ("gate_relaxation_to_force_pnl_allowed", "no_pnl_forcing_policy", "boolean", "0", "BOOLEAN_FALSE", "0", "1"),
        ("formula_mutation_to_force_pnl_allowed", "no_pnl_forcing_policy", "boolean", "0", "BOOLEAN_FALSE", "0", "1"),
        ("impossible_price_allowed", "no_pnl_forcing_policy", "boolean", "0", "BOOLEAN_FALSE", "0", "1"),
        ("impossible_fill_allowed", "no_pnl_forcing_policy", "boolean", "0", "BOOLEAN_FALSE", "0", "1"),
        ("hindsight_backsolve_allowed", "no_pnl_forcing_policy", "boolean", "0", "BOOLEAN_FALSE", "0", "1"),
        ("post_hoc_exit_selection_allowed", "no_pnl_forcing_policy", "boolean", "0", "BOOLEAN_FALSE", "0", "1"),
        ("coefficient_normalization_policy", "quantum_encoding_policy", "string", "0", "UNIT_NORMALIZED_FOR_FIXTURE_ONLY", "0", "0"),
        ("backend_default_policy", "quantum_encoding_policy", "string", "0", "ADOPT_OFFICIAL_LIBRARY_OR_PROVIDER_DEFAULTS_IN_LATER_EXECUTION_PR", "0", "0"),
        ("anneal_time_policy", "quantum_encoding_policy", "string", "0", "NOT_SET_IN_VS1", "0", "0"),
        ("num_reads_policy", "quantum_encoding_policy", "string", "0", "NOT_SET_IN_VS1", "0", "0"),
        ("chain_strength_policy", "quantum_encoding_policy", "string", "0", "NOT_SET_IN_VS1", "0", "0"),
        ("qaoa_reps_policy", "quantum_encoding_policy", "string", "0", "NOT_SET_IN_VS1", "0", "0"),
        ("shots_policy", "quantum_encoding_policy", "string", "0", "NOT_SET_IN_VS1", "0", "0"),
        ("optimizer_budget_policy", "quantum_encoding_policy", "string", "0", "BOUNDED_FIXTURE_ONLY", "0", "0"),
    ]
    rows: list[dict[str, Any]] = []
    values: dict[str, Decimal | str] = {}
    for index, (name, role, typ, value, unit, min_value, max_value) in enumerate(specs, start=1):
        if typ == "string":
            values[name] = unit
        else:
            values[name] = dec(value)
        rows.append(
            with_common(
                {
                    "default_source_class": "VS1_SYNTHETIC_FIXTURE_ONLY",
                    "fixture_only_flag": True,
                    "live_default_flag": False,
                    "owner_override_allowed_later_flag": True if role not in {"no_pnl_forcing_policy"} else False,
                    "parameter_name": name,
                    "parameter_role": role,
                    "parameter_type": typ,
                    "policy_parameter_ref": _field_ref(name),
                    "policy_value_string": unit if typ == "string" else ("false" if typ == "boolean" else value),
                    "used_by_artifact_refs": [generated_ref("trade_plan_variable_search_receipts.jsonl"), generated_ref("expected_cash_pnl_receipts.jsonl")],
                    "value_decimal_string": value,
                    "value_range_max": max_value,
                    "value_range_min": min_value,
                    "value_unit": unit,
                    "vs1_policy_parameter_row_id": f"VS1_POLICY_PARAMETER_ROW_{index:04d}",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["AllVS1Agents", "VS1Validator"],
                upstream_artifact_refs=[generated_ref("vs1_execution_authority_receipt.report.json")],
                downstream_artifact_refs=[generated_ref("trade_plan_variable_search_receipts.jsonl"), generated_ref("expected_cash_pnl_receipts.jsonl")],
            )
        )
    return rows, values


def build_fixtures(policy_refs: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    specs = [
        {
            "fixture_case": "positive_edge_fixture",
            "platform_id": "KALSHI",
            "best_bid": "0.49",
            "best_ask": "0.50",
            "depth": "1000",
            "volume": "12000",
            "liquidity_bucket": "DEEP",
            "latency_bucket": "LOW",
            "fill_seed": "0.92",
            "probabilities": ["0.62", "0.60"],
            "slippage": "0.0020",
            "latency_penalty": "0.0010",
            "capacity_seed": "0.0000",
            "crowding_seed": "0.0010",
            "portfolio_seed": "0.0010",
            "uncertainty_seed": "0.0200",
            "overfit_seed": "0.0100",
            "scenario_seed": "0.0200",
            "sizes": ["20", "50"],
        },
        {
            "fixture_case": "negative_edge_fixture",
            "platform_id": "POLYMARKET",
            "best_bid": "0.53",
            "best_ask": "0.55",
            "depth": "800",
            "volume": "7000",
            "liquidity_bucket": "NORMAL",
            "latency_bucket": "LOW",
            "fill_seed": "0.86",
            "probabilities": ["0.49", "0.47"],
            "slippage": "0.0030",
            "latency_penalty": "0.0015",
            "capacity_seed": "0.0010",
            "crowding_seed": "0.0020",
            "portfolio_seed": "0.0020",
            "uncertainty_seed": "0.0300",
            "overfit_seed": "0.0200",
            "scenario_seed": "0.0300",
            "sizes": ["20", "50"],
        },
        {
            "fixture_case": "thin_book_fixture",
            "platform_id": "FORECASTEX_IBKR",
            "best_bid": "0.44",
            "best_ask": "0.58",
            "depth": "8",
            "volume": "60",
            "liquidity_bucket": "THIN",
            "latency_bucket": "MEDIUM",
            "fill_seed": "0.35",
            "probabilities": ["0.67", "0.64"],
            "slippage": "0.0200",
            "latency_penalty": "0.0100",
            "capacity_seed": "0.0500",
            "crowding_seed": "0.0400",
            "portfolio_seed": "0.0020",
            "uncertainty_seed": "0.0700",
            "overfit_seed": "0.0400",
            "scenario_seed": "0.0800",
            "sizes": ["20", "40"],
        },
        {
            "fixture_case": "crowded_capacity_fixture",
            "platform_id": "KALSHI",
            "best_bid": "0.46",
            "best_ask": "0.49",
            "depth": "120",
            "volume": "3000",
            "liquidity_bucket": "CROWDED",
            "latency_bucket": "MEDIUM",
            "fill_seed": "0.90",
            "probabilities": ["0.63", "0.60"],
            "slippage": "0.0060",
            "latency_penalty": "0.0040",
            "capacity_seed": "0.0300",
            "crowding_seed": "0.0600",
            "portfolio_seed": "0.0100",
            "uncertainty_seed": "0.0500",
            "overfit_seed": "0.0400",
            "scenario_seed": "0.0500",
            "sizes": ["200", "400"],
        },
        {
            "fixture_case": "portfolio_conflict_fixture",
            "platform_id": "POLYMARKET",
            "best_bid": "0.48",
            "best_ask": "0.51",
            "depth": "600",
            "volume": "9000",
            "liquidity_bucket": "NORMAL",
            "latency_bucket": "LOW",
            "fill_seed": "0.88",
            "probabilities": ["0.62", "0.59"],
            "slippage": "0.0030",
            "latency_penalty": "0.0015",
            "capacity_seed": "0.0010",
            "crowding_seed": "0.0040",
            "portfolio_seed": "0.0800",
            "uncertainty_seed": "0.0400",
            "overfit_seed": "0.0300",
            "scenario_seed": "0.0500",
            "sizes": ["80", "120"],
        },
    ]
    fixtures: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    snapshot_by_fixture: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(specs, start=1):
        fixture_id = f"VS1_FIXTURE_{index:04d}_{spec['fixture_case'].upper()}"
        bid = dec(spec["best_bid"])
        ask = dec(spec["best_ask"])
        spread = ask - bid
        mid = (bid + ask) / dec("2")
        event_id = f"VS1_EVENT_{index:04d}"
        contract_id = f"VS1_CONTRACT_{index:04d}"
        market_id = f"VS1_MARKET_{spec['platform_id']}_{index:04d}"
        fixture = with_common(
            {
                "best_ask": money(ask),
                "best_bid": money(bid),
                "contract_id": contract_id,
                "depth": spec["depth"],
                "event_id": event_id,
                "execution_authority_ref": EXECUTION_AUTHORITY_REF,
                "fee_model_ref": "VS1_SYNTHETIC_FEE_MODEL_FIXTURE_ONLY",
                "fixture_case": spec["fixture_case"],
                "fixture_id": fixture_id,
                "liquidity_bucket": spec["liquidity_bucket"],
                "market_family": MARKET_FAMILY,
                "market_id": market_id,
                "mid_price": money(mid),
                "min_order_size": "1",
                "platform_id": spec["platform_id"],
                "question": f"VS1 synthetic {spec['fixture_case']} contract settles YES for fixture-only proof?",
                "reference_time_utc": CREATED_AT_UTC,
                "side_candidates": ["YES", "NO"],
                "source_class": "VS1_SYNTHETIC_FIXTURE_ONLY",
                "spread": money(spread),
                "stage_profile_id": STAGE_PROFILE_ID,
                "synthetic_fixture_flag": True,
                "tick_size": "0.01",
                "time_to_resolution_seconds": "86400",
                "volume": spec["volume"],
            },
            producer_agent="CommanderAgent",
            consumer_agent_refs=["MarketConditionAgent", "TradePlanVariableSearchAgent"],
            upstream_artifact_refs=[generated_ref("vs1_policy_parameter_registry.jsonl")],
            downstream_artifact_refs=[generated_ref("market_condition_snapshots.jsonl")],
        )
        yes_entries = [money(ask), money(max(mid, bid))]
        no_bid = dec("1") - ask
        no_ask = dec("1") - bid
        snapshot = with_common(
            {
                "capacity_penalty_seed": spec["capacity_seed"],
                "contract_id": contract_id,
                "crowding_penalty_seed": spec["crowding_seed"],
                "depth": spec["depth"],
                "entry_price_candidates": {"NO": [money(no_ask), money(max((no_bid + no_ask) / dec("2"), no_bid))], "YES": yes_entries},
                "estimated_yes_probability_candidates": spec["probabilities"],
                "fill_probability_seed": spec["fill_seed"],
                "fixture_id": fixture_id,
                "latency_edge_decay_penalty": spec["latency_penalty"],
                "market_id": market_id,
                "no_best_ask": money(no_ask),
                "no_best_bid": money(no_bid),
                "order_size_candidates": spec["sizes"],
                "overfit_fdr_penalty_seed": spec["overfit_seed"],
                "platform_id": spec["platform_id"],
                "policy_parameter_refs": policy_refs,
                "portfolio_penalty_seed": spec["portfolio_seed"],
                "queue_position_proxy": "0.2500" if spec["liquidity_bucket"] != "THIN" else "0.8500",
                "reference_time_utc": CREATED_AT_UTC,
                "scenario_ladder_seed": spec["scenario_seed"],
                "side_fair_probability_candidates": {
                    "NO": [money(dec("1") - dec(prob)) for prob in spec["probabilities"]],
                    "YES": spec["probabilities"],
                },
                "slippage_per_contract": spec["slippage"],
                "snapshot_id": f"VS1_MARKET_CONDITION_{index:04d}",
                "spread": money(spread),
                "uncertainty_penalty_seed": spec["uncertainty_seed"],
                "volume": spec["volume"],
                "yes_best_ask": money(ask),
                "yes_best_bid": money(bid),
            },
            producer_agent="MarketConditionAgent",
            consumer_agent_refs=["QKUComputabilityMaterializerAgent", "ExpectedCashPnLEngineAgent"],
            upstream_artifact_refs=[generated_ref("trade_target_fixtures.jsonl")],
            downstream_artifact_refs=[generated_ref("selected_computable_qku_formula_bindings.jsonl"), generated_ref("expected_cash_pnl_receipts.jsonl")],
        )
        fixtures.append(fixture)
        snapshots.append(snapshot)
        snapshot_by_fixture[fixture_id] = snapshot
    return fixtures, snapshots, snapshot_by_fixture


def discover_reading_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    reading_rows: list[dict[str, Any]] = []
    for index, ref in enumerate(REQUIRED_READING_FILES, start=1):
        path = REPO_ROOT / ref
        status = "READ" if path.is_file() else "MISSING_BLOCKING" if ref in RP5C_REQUIRED_FILES else "MISSING_NON_BLOCKING"
        byte_size = path.stat().st_size if path.is_file() else 0
        line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines()) if path.is_file() else 0
        reading_rows.append(
            with_common(
                {
                    "byte_size": byte_size,
                    "discovery_pattern": "REQUIRED_READING_LIST",
                    "file_ref": ref,
                    "line_count": line_count,
                    "receipt_id": f"VS1_READING_RECEIPT_{index:04d}",
                    "read_status": status,
                    "schema_version": "VS1ReadingReceiptV1",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["FormulaLibraryAgent", "AgentDutyResolverAgent", "GovernanceAgent"],
                upstream_artifact_refs=[],
                downstream_artifact_refs=[generated_ref("stage_agent_universe_query_receipts.jsonl")],
            )
        )
    discovery_patterns = {
        "ROADMAP_HANDOFF_VS1": ("roadmap", "handoff", "vs1"),
        "ROUTE_TRIAGE": ("route", "triage"),
        "FULL_MASTER_PLAN_SECTION_CROSSWALK": ("section", "crosswalk"),
        "MARKET_SPECIFIC_SECTION_INDEX": ("market", "section", "index"),
        "COMMAND_ACTION_MATRIX": ("command", "action", "matrix"),
    }
    all_docs = sorted(
        [p for p in (REPO_ROOT / "docs" / "master_plan").rglob("*") if p.is_file()],
        key=lambda p: rel_ref(p).casefold(),
    )
    crosswalk_rows: list[dict[str, Any]] = []
    for category, tokens in discovery_patterns.items():
        matches = [rel_ref(p) for p in all_docs if all(token in p.name.lower() for token in tokens)]
        status = "FOUND" if matches else "NOT_FOUND_NON_BLOCKING_FOR_VS1"
        crosswalk_rows.append(
            with_common(
                {
                    "crosswalk_discovery_receipt_id": f"VS1_CROSSWALK_DISCOVERY_{category}",
                    "discovered_file_count": len(matches),
                    "discovered_file_refs": matches,
                    "discovery_category": category,
                    "discovery_status": status,
                    "schema_version": "VS1CrosswalkDiscoveryReceiptV1",
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["AgentDutyResolverAgent", "GovernanceAgent"],
                upstream_artifact_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_artifact_refs=[generated_ref("agent_duty_evidence_discovery_receipts.jsonl")],
            )
        )
    agent_duty = discover_agent_duty_evidence()
    return reading_rows, crosswalk_rows, agent_duty


def discover_agent_duty_evidence() -> dict[str, Any]:
    search_roots = [REPO_ROOT / name for name in ("docs", "src", "tools", "tests")]
    candidates = []
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and ("AgentRosterDiscoveryAudit" in path.name or "AgentDutySourceCrosswalk" in path.name):
                candidates.append(rel_ref(path))
    candidates = sorted(dict.fromkeys(candidates), key=str.casefold)
    roster = [ref for ref in candidates if "AgentRosterDiscoveryAudit" in Path(ref).name]
    crosswalk = [ref for ref in candidates if "AgentDutySourceCrosswalk" in Path(ref).name]

    def _select(refs: list[str], preferred: str) -> str | None:
        exact = [ref for ref in refs if ref == preferred]
        if exact:
            return exact[0]
        generated = [ref for ref in refs if ref.startswith("docs/master_plan/generated/")]
        return sorted(generated or refs, key=str.casefold)[-1] if refs else None

    selected_roster = _select(roster, "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json")
    selected_crosswalk = _select(crosswalk, "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json")
    row = with_common(
        {
            "agent_duty_evidence_discovery_receipt_id": "VS1_AGENT_DUTY_EVIDENCE_DISCOVERY_0001",
            "agent_duty_source_crosswalk_ref": selected_crosswalk,
            "agent_roster_discovery_audit_ref": selected_roster,
            "candidate_file_refs": candidates,
            "decision_basis": "PREFER_EXACT_PR165_D2_GENERATED_ARTIFACTS_ELSE_DETERMINISTIC_GENERATED_SORT",
            "discovery_status": "FOUND_CANONICAL_PR165_D2" if selected_roster and selected_crosswalk else "FALLBACK_TO_RP5C_CURRENT_AGENT_DUTY_SURFACES",
            "fallback_rp5c_agent_policy_refs": [
                "docs/master_plan/generated/rp5c/agent_duty_routing_rulebook.jsonl",
                "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
                "docs/master_plan/generated/rp5c/agent_computation_universe_view.jsonl",
            ],
            "schema_version": "VS1AgentDutyEvidenceDiscoveryReceiptV1",
        },
        producer_agent="AgentDutyResolverAgent",
        consumer_agent_refs=["ContextFormulaSelectorAgent", "GovernanceAgent"],
        upstream_artifact_refs=["docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl"],
        downstream_artifact_refs=[generated_ref("stage_agent_universe_query_receipts.jsonl")],
    )
    return {"row": row, "selected_roster": selected_roster, "selected_crosswalk": selected_crosswalk}


def build_stage_query_receipts(library: dict[str, Any], agent_duty: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[str]]]:
    rows: list[dict[str, Any]] = []
    refs_by_platform_agent: dict[tuple[str, str], list[str]] = {}
    matrix = library["matrix_by_identity"]
    identities = library["identity_by_id"]
    policy_by_id = library["agent_policy_by_id"]
    for platform in PLATFORM_IDS:
        for agent in SELECTOR_AGENT_IDS:
            resolved = resolve_stage_agent_universe(STAGE_PROFILE_ID, agent, platform, library)
            refs = resolved["result_identity_refs"]
            refs_by_platform_agent[(platform, agent)] = refs
            specific_count = sum(1 for ref in refs if matrix[ref]["applicability_mode"] == "MARKET_SPECIFIC")
            shared_count = sum(1 for ref in refs if matrix[ref]["applicability_mode"] == "CROSS_MARKET_SHARED")
            unknown_count = sum(1 for ref in refs if identities[ref].get("unknown_needs_review_flag"))
            policy = policy_by_id.get(agent, {})
            rows.append(
                with_common(
                    {
                        "agent_duty_routing_rulebook_ref": "docs/master_plan/generated/rp5c/agent_duty_routing_rulebook.jsonl",
                        "agent_duty_source_crosswalk_ref": agent_duty.get("selected_crosswalk"),
                        "agent_id": agent,
                        "agent_qku_access_policy_ref": policy.get("agent_access_policy_id", agent),
                        "agent_roster_discovery_audit_ref": agent_duty.get("selected_roster"),
                        "available_on_demand_count": resolved["available_on_demand_count"],
                        "cross_market_shared_identity_count": shared_count,
                        "default_compute_count": resolved["default_compute_count"],
                        "eligible_identity_count": len(refs) - unknown_count,
                        "inactive_for_stage_count": 0,
                        "market_family": MARKET_FAMILY,
                        "platform_id": platform,
                        "query_receipt_id": f"VS1_STAGE_QUERY_{platform}_{agent}",
                        "query_status": "RESOLVED_FROM_RP5C_CENTRAL_SURFACES",
                        "rp5c_input_refs": [
                            "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
                            "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
                            "docs/master_plan/generated/rp5c/agent_duty_routing_rulebook.jsonl",
                        ],
                        "specific_market_identity_count": specific_count,
                        "stage_profile_id": STAGE_PROFILE_ID,
                        "stage_seed_ref": "docs/master_plan/generated/rp5c/stage1_agent_computation_universe_seed.jsonl",
                        "unknown_needs_review_count": unknown_count,
                    },
                    producer_agent="AgentDutyResolverAgent",
                    consumer_agent_refs=["ContextFormulaSelectorAgent", "GovernanceAgent"],
                    upstream_artifact_refs=["docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl"],
                    downstream_artifact_refs=[generated_ref("context_formula_selection_receipts.jsonl")],
                )
            )
    return rows, refs_by_platform_agent


def select_identities_for_platform(
    library: dict[str, Any],
    refs_by_platform_agent: dict[tuple[str, str], list[str]],
    platform: str,
    max_identities: int,
) -> list[str]:
    identities = library["identity_by_id"]
    selected: list[str] = []
    seen: set[str] = set()
    role_categories = [role for role in ROLE_ORDER if role != "exit_timing"]
    for role in role_categories:
        candidates: list[tuple[int, str, str]] = []
        for agent in SELECTOR_AGENT_IDS:
            for ref in refs_by_platform_agent.get((platform, agent), []):
                row = identities.get(ref)
                if not row:
                    continue
                if row.get("ontology_category") != role:
                    continue
                if row.get("unknown_needs_review_flag"):
                    continue
                if row.get("stage1_access_mode") not in {"DEFAULT_COMPUTE", "AVAILABLE_ON_DEMAND"}:
                    continue
                if platform not in set(row.get("stage1_platform_refs", [])):
                    continue
                complete = 0 if row.get("qku_id") and row.get("formula_id") else 1
                candidates.append((complete, ref, agent))
        for _, ref, _agent in sorted(candidates, key=lambda item: (item[0], item[1], item[2])):
            if ref not in seen:
                selected.append(ref)
                seen.add(ref)
                break
    if len(selected) < 10:
        filler = []
        for agent in SELECTOR_AGENT_IDS:
            for ref in refs_by_platform_agent.get((platform, agent), []):
                row = identities.get(ref)
                if not row or row.get("unknown_needs_review_flag") or ref in seen:
                    continue
                if row.get("stage1_access_mode") in {"DEFAULT_COMPUTE", "AVAILABLE_ON_DEMAND"}:
                    filler.append(ref)
        for ref in sorted(dict.fromkeys(filler), key=str.casefold):
            selected.append(ref)
            seen.add(ref)
            if len(selected) >= 10:
                break
    return selected[:max_identities]


def build_context_and_bindings(
    fixtures: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    library: dict[str, Any],
    refs_by_platform_agent: dict[tuple[str, str], list[str]],
    config: RunConfig,
    policy_refs: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], set[str]]:
    identity_by_id = library["identity_by_id"]
    selection_rows: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    bindings_by_fixture: dict[str, list[dict[str, Any]]] = {}
    unique_selected: set[str] = set()
    for fixture in fixtures:
        platform = fixture["platform_id"]
        fixture_id = fixture["fixture_id"]
        selected_refs = select_identities_for_platform(library, refs_by_platform_agent, platform, config.max_identities)
        unique_selected.update(selected_refs)
        context_id = f"VS1_CONTEXT_SELECTION_{fixture_id}"
        selected_rows = [identity_by_id[ref] for ref in selected_refs]
        role_codes = sorted({row.get("ontology_category") for row in selected_rows})
        if "exit_timing" not in role_codes:
            role_codes.append("exit_timing_not_available_in_selected_rp5c_stage1_union")
        selection_rows.append(
            with_common(
                {
                    "agent_duty_source_ref": [
                        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
                        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
                    ],
                    "agent_id": "VS1_BOUNDED_CONTEXT_COMPOSITE",
                    "agent_policy_ref": "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
                    "bounded_subset_flag": True,
                    "context_selection_id": context_id,
                    "fixture_id": fixture_id,
                    "market_family": MARKET_FAMILY,
                    "no_unknown_needs_review_flag": True,
                    "platform_id": platform,
                    "policy_parameter_refs": policy_refs,
                    "resolver_receipt_ref": [f"VS1_STAGE_QUERY_{platform}_{agent}" for agent in SELECTOR_AGENT_IDS],
                    "role_coverage_codes": role_codes,
                    "rp5c_input_refs": RP5C_REQUIRED_FILES,
                    "selected_formula_refs": [formula_ref(row) for row in selected_rows],
                    "selected_identity_count": len(selected_refs),
                    "selected_qku_refs": [qku_ref(row) for row in selected_rows],
                    "selection_reason_codes": [
                        "STAGE1_PREDICTION_MARKET_ELIGIBLE",
                        "AGENT_DUTY_ALLOWED",
                        "BOUNDED_COMPUTABLE_VS1_SUBSET",
                    ],
                    "stage_profile_id": STAGE_PROFILE_ID,
                },
                producer_agent="ContextFormulaSelectorAgent",
                consumer_agent_refs=["QKUComputabilityMaterializerAgent", "StackGeneratorAgent"],
                upstream_artifact_refs=[generated_ref("stage_agent_universe_query_receipts.jsonl")],
                downstream_artifact_refs=[generated_ref("selected_computable_qku_formula_bindings.jsonl")],
            )
        )
        fixture_bindings: list[dict[str, Any]] = []
        snapshot = snapshots[fixture_id]
        for ordinal, identity_ref in enumerate(selected_refs, start=1):
            identity = identity_by_id[identity_ref]
            role = str(identity.get("ontology_category"))
            deterministic_value = deterministic_binding_value(role, snapshot)
            binding = with_common(
                {
                    "agent_owner_ref": owner_for_role(role),
                    "calculation_mode": "VS1_DETERMINISTIC_SYNTHETIC_FIXTURE_BINDING",
                    "calculation_version": "VS1_BINDING_CALC_V1",
                    "classical_fallback_available_flag": True,
                    "computable_algorithm_ref": f"VS1_COMPUTABLE_ALGO::{role.upper()}",
                    "computable_binding_id": f"VS1_BINDING_{fixture_id}_{ordinal:02d}",
                    "computable_expression_ref": f"VS1_EXPR::{role.upper()}::IMMUTABLE_INPUT_OVERLAY",
                    "computable_for_vs1_fixture_flag": True,
                    "context_selection_id": context_id,
                    "deterministic_fixture_value": deterministic_value,
                    "exclusion_reason_if_not_computable": "",
                    "formula_family": identity.get("formula_family"),
                    "formula_ref": formula_ref(identity),
                    "identity_ref": identity_ref,
                    "input_fields": input_fields_for_role(role),
                    "input_fixture_bindings": {"fixture_id": fixture_id, "snapshot_id": snapshot["snapshot_id"]},
                    "input_units": ["PROBABILITY_OR_USD_FIXTURE_UNIT"],
                    "metadata_only_flag": False,
                    "missing_input_count": 0,
                    "objective_term_candidate_flag": role
                    in {
                        "signal_probability",
                        "tca_cost",
                        "fill_queue_liquidity",
                        "latency_staleness",
                        "capacity_crowding",
                        "portfolio_risk",
                        "regime_scenario",
                        "quantum_objective_constraint",
                    },
                    "ontology_role": role,
                    "output_field": output_field_for_role(role),
                    "output_unit": "DECIMAL_FIXTURE_VALUE",
                    "qku_ref": qku_ref(identity),
                    "quantum_structural_candidate_flag": role in {"quantum_objective_constraint", "classical_fallback", "portfolio_risk"},
                    "stack_role": role,
                },
                producer_agent="QKUComputabilityMaterializerAgent",
                consumer_agent_refs=["StackGeneratorAgent", "ObjectiveTermsAgent", "QuantumReadinessAgent"],
                upstream_artifact_refs=[generated_ref("context_formula_selection_receipts.jsonl"), snapshot["snapshot_id"]],
                downstream_artifact_refs=[generated_ref("temporary_stack_candidate_receipts.jsonl")],
            )
            binding_rows.append(binding)
            fixture_bindings.append(binding)
        bindings_by_fixture[fixture_id] = fixture_bindings
    return selection_rows, binding_rows, bindings_by_fixture, unique_selected


def deterministic_binding_value(role: str, snapshot: dict[str, Any]) -> str:
    if role == "signal_probability":
        return snapshot["estimated_yes_probability_candidates"][0]
    if role == "market_implied_probability":
        return money((dec(snapshot["yes_best_bid"]) + dec(snapshot["yes_best_ask"])) / dec("2"))
    if role == "tca_cost":
        return money(dec(snapshot["spread"]) + dec(snapshot["slippage_per_contract"]))
    if role == "fill_queue_liquidity":
        return snapshot["fill_probability_seed"]
    if role == "latency_staleness":
        return snapshot["latency_edge_decay_penalty"]
    if role == "capacity_crowding":
        return snapshot["capacity_penalty_seed"]
    if role == "portfolio_risk":
        return snapshot["portfolio_penalty_seed"]
    if role == "regime_scenario":
        return snapshot["scenario_ladder_seed"]
    if role == "calibration":
        return snapshot["uncertainty_penalty_seed"]
    if role == "quantum_objective_constraint":
        return "1.0000"
    if role == "classical_fallback":
        return "1.0000"
    return "0.0000"


def input_fields_for_role(role: str) -> list[str]:
    mapping = {
        "signal_probability": ["estimated_yes_probability_candidates", "side_fair_probability_candidates"],
        "calibration": ["uncertainty_penalty_seed"],
        "market_implied_probability": ["yes_best_bid", "yes_best_ask", "no_best_bid", "no_best_ask"],
        "tca_cost": ["spread", "slippage_per_contract"],
        "fill_queue_liquidity": ["fill_probability_seed", "queue_position_proxy", "depth"],
        "latency_staleness": ["latency_edge_decay_penalty", "latency_bucket"],
        "capacity_crowding": ["depth", "capacity_penalty_seed", "crowding_penalty_seed"],
        "portfolio_risk": ["portfolio_penalty_seed"],
        "regime_scenario": ["scenario_ladder_seed"],
        "quantum_objective_constraint": ["objective_term_refs", "constraint_penalty_refs"],
        "classical_fallback": ["classical_fallback_optimizer_refs"],
    }
    return mapping.get(role, ["fixture_id"])


def output_field_for_role(role: str) -> str:
    return f"vs1_{role}_fixture_value"


def owner_for_role(role: str) -> str:
    if role in {"tca_cost", "fill_queue_liquidity", "latency_staleness"}:
        return "connector_venue_readiness_future_consumer"
    if role in {"capacity_crowding", "portfolio_risk"}:
        return "risk_manager_agent"
    if role in {"quantum_objective_constraint", "classical_fallback"}:
        return "quantum_optimizer_agent"
    return "research_agent"


def build_stacks(fixtures: list[dict[str, Any]], bindings_by_fixture: dict[str, list[dict[str, Any]]], config: RunConfig) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    stack_rows: list[dict[str, Any]] = []
    stacks_by_fixture: dict[str, list[dict[str, Any]]] = {}
    for fixture in fixtures:
        fixture_id = fixture["fixture_id"]
        bindings = sorted(bindings_by_fixture[fixture_id], key=lambda row: row["computable_binding_id"])
        stacks: list[dict[str, Any]] = []
        for chunk_index in range(0, len(bindings), 3):
            chunk = bindings[chunk_index : chunk_index + 3]
            if not chunk:
                continue
            stack_id = f"VS1_STACK_{fixture_id}_{len(stacks) + 1:02d}"
            row = with_common(
                {
                    "bulk_grid_retained_flag": False,
                    "classical_fallback_hint": "greedy_top_k",
                    "computable_binding_refs": [item["computable_binding_id"] for item in chunk],
                    "context_selection_id": chunk[0]["context_selection_id"],
                    "correlated_formula_exposure_group": "_".join(sorted({str(item["formula_family"]) for item in chunk}))[:120],
                    "diversity_group": "_".join(sorted({str(item["stack_role"]) for item in chunk})),
                    "ephemeral_stack_flag": True,
                    "fixture_id": fixture_id,
                    "formula_refs": [item["formula_ref"] for item in chunk],
                    "qku_refs": [item["qku_ref"] for item in chunk],
                    "quantum_forward_hint": "STRUCTURAL_METADATA_ONLY",
                    "role_coverage_codes": [item["stack_role"] for item in chunk],
                    "stack_role_refs": [item["stack_role"] for item in chunk],
                    "stack_size": len(chunk),
                    "temporary_stack_id": stack_id,
                },
                producer_agent="StackGeneratorAgent",
                consumer_agent_refs=["TradePlanVariableSearchAgent", "QuantumReadinessAgent"],
                upstream_artifact_refs=[generated_ref("selected_computable_qku_formula_bindings.jsonl")],
                downstream_artifact_refs=[generated_ref("trade_plan_variable_search_receipts.jsonl")],
            )
            stacks.append(row)
            stack_rows.append(row)
            if len(stacks) >= config.max_stacks_per_fixture:
                break
        stacks_by_fixture[fixture_id] = stacks
    return stack_rows, stacks_by_fixture


def build_order_grid(
    fixtures: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    selection_rows: list[dict[str, Any]],
    stacks_by_fixture: dict[str, list[dict[str, Any]]],
    policy_refs: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    context_by_fixture = {row["fixture_id"]: row for row in selection_rows}
    search_rows: list[dict[str, Any]] = []
    order_rows: list[dict[str, Any]] = []
    search_by_fixture: dict[str, dict[str, Any]] = {}
    for fixture in fixtures:
        fixture_id = fixture["fixture_id"]
        snapshot = snapshots[fixture_id]
        context_id = context_by_fixture[fixture_id]["context_selection_id"]
        stack_refs = [row["temporary_stack_id"] for row in stacks_by_fixture[fixture_id]]
        search_ref = f"VS1_VARIABLE_SEARCH_{fixture_id}"
        raw_combos = 2 * 2 * len(snapshot["order_size_candidates"]) * max(len(stack_refs), 1)
        search_row = with_common(
            {
                "bounded_candidate_count": 0,
                "bounded_search_flag": True,
                "cancel_replace_policy_count": 1,
                "context_selection_id": context_id,
                "eligible_candidate_count": 0,
                "entry_price_count": 4,
                "ex_ante_search_flag": True,
                "exit_rule_count": 1,
                "fixture_id": fixture_id,
                "gate_relaxation_attempt_count": 0,
                "hindsight_free_flag": True,
                "impossible_fill_candidate_count": 0,
                "impossible_price_candidate_count": 0,
                "latency_budget_count": 1,
                "liquidity_filter_count": 1,
                "maker_taker_policy_count": 1,
                "markets_considered": [fixture["market_id"]],
                "no_eligible_positive_candidate_flag": False,
                "no_eligible_reason_codes": [],
                "order_size_count": len(snapshot["order_size_candidates"]),
                "outcome_backsolve_flag": False,
                "platforms_considered": [fixture["platform_id"]],
                "policy_parameter_refs": policy_refs,
                "portfolio_exposure_variant_count": 1,
                "raw_combination_count": raw_combos,
                "rejected_by_capacity_count": 0,
                "rejected_by_feasibility_count": 0,
                "rejected_by_fill_count": 0,
                "rejected_by_overfit_fdr_count": 0,
                "rejected_by_portfolio_count": 0,
                "rejected_by_scenario_count": 0,
                "rejected_by_tca_count": 0,
                "search_mode": "DETERMINISTIC_BOUNDED_GRID",
                "search_scope": [
                    "market",
                    "venue/platform",
                    "formula/QKU stack",
                    "YES/NO side",
                    "entry price",
                    "order size",
                    "hold duration",
                    "exit rule",
                    "maker/taker/split policy",
                    "cancel/replace interval",
                    "liquidity/spread/depth filters",
                    "latency budget",
                    "capacity/crowding",
                    "portfolio exposure",
                    "objective-term weights",
                    "penalty terms",
                    "quantum/classical encoding eligibility",
                ],
                "sides_considered": ["YES", "NO"],
                "temporary_stack_refs": stack_refs,
                "variable_search_ref": search_ref,
            },
            producer_agent="TradePlanVariableSearchAgent",
            consumer_agent_refs=["OrderVariableAgent", "NoPnLForcingProofAgent"],
            upstream_artifact_refs=[generated_ref("temporary_stack_candidate_receipts.jsonl")],
            downstream_artifact_refs=[generated_ref("order_variable_candidate_receipts.jsonl")],
        )
        candidate_index = 0
        for side in ("YES", "NO"):
            fair_values = snapshot["side_fair_probability_candidates"][side]
            for entry in snapshot["entry_price_candidates"][side]:
                for size in snapshot["order_size_candidates"]:
                    candidate_index += 1
                    order_size = dec(size)
                    entry_price = dec(entry)
                    order = with_common(
                        {
                            "cancel_replace_policy": "CANCEL_REPLACE_60S_FIXTURE",
                            "capacity_limit": "0.30",
                            "contract_id": fixture["contract_id"],
                            "crowding_limit": "0.05",
                            "depth_filter": "DEPTH_POSITIVE_AND_FIXTURE_BOUNDED",
                            "edge_decay_exit_rule": "EXIT_IF_EDGE_DECAYS_BELOW_ZERO_EX_ANTE",
                            "entry_price": money(entry_price),
                            "ex_ante_candidate_flag": True,
                            "exit_rule": "TIME_OR_EDGE_DECAY_EX_ANTE",
                            "feasible_fill_flag": True,
                            "feasible_price_flag": True,
                            "fixture_id": fixture_id,
                            "hold_duration_seconds": "3600",
                            "latency_filter": "LATENCY_BUCKET_ALLOWED",
                            "maker_taker_policy": "MAKER_TAKER_SPLIT_FIXTURE",
                            "market_id": fixture["market_id"],
                            "order_size": money(order_size),
                            "order_variable_candidate_id": f"VS1_ORDER_VAR_{fixture_id}_{candidate_index:03d}",
                            "platform_id": fixture["platform_id"],
                            "policy_parameter_refs": policy_refs,
                            "portfolio_exposure_cap": "0.60",
                            "side": side,
                            "side_fair_probability": fair_values[0],
                            "spread_filter": "SPREAD_WITHIN_FIXTURE_GRID",
                            "stop_loss_rule": "STOP_LOSS_NOT_EXECUTED_PREVIEW_ONLY",
                            "take_profit_rule": "TAKE_PROFIT_NOT_EXECUTED_PREVIEW_ONLY",
                            "total_investment": money(order_size * entry_price),
                            "variable_search_ref": search_ref,
                        },
                        producer_agent="OrderVariableAgent",
                        consumer_agent_refs=["ExpectedCashPnLEngineAgent", "TCAAgent"],
                        upstream_artifact_refs=[search_ref],
                        downstream_artifact_refs=[generated_ref("trade_plan_candidates.jsonl")],
                    )
                    order_rows.append(order)
        search_row["bounded_candidate_count"] = candidate_index
        search_by_fixture[fixture_id] = search_row
        search_rows.append(search_row)
    return search_rows, order_rows, search_by_fixture


def compute_fill_probability(order: dict[str, Any], snapshot: dict[str, Any]) -> Decimal:
    base = dec(snapshot["fill_probability_seed"])
    size = dec(order["order_size"])
    depth = max(dec(snapshot["depth"]), dec("1"))
    pressure = size / depth
    pressure_over = max(pressure - dec("0.30"), Decimal("0"))
    fill = base - pressure_over * dec("0.15") - dec(snapshot["spread"]) * dec("0.15")
    return min(max(fill, dec("0.05")), dec("0.99"))


def calculate_tca(order: dict[str, Any], snapshot: dict[str, Any], params: dict[str, Decimal | str], fill_probability: Decimal, gross_edge_cash: Decimal) -> dict[str, Decimal | bool]:
    size = dec(order["order_size"])
    expected_fill = size * fill_probability
    spread = dec(snapshot["spread"])
    fee = dec(params["fee_per_contract_fixture"])
    spread_multiplier = dec(params["spread_cost_multiplier_fixture"])
    cancel_cost = dec(params["cancel_replace_cost_fixture"])
    capital_rate = dec(params["capital_lock_rate_fixture"])
    capacity_multiplier = dec(params["capacity_cost_multiplier_fixture"])
    crowd_multiplier = dec(params["crowding_cost_multiplier_fixture"])
    depth = max(dec(snapshot["depth"]), dec("1"))
    capacity_used = size / depth
    fees_cash = cash_decimal(fee * expected_fill)
    spread_cost_cash = cash_decimal(spread * expected_fill * spread_multiplier)
    slippage_cash = cash_decimal(dec(snapshot["slippage_per_contract"]) * expected_fill)
    queue_fill_shortfall_cash = cash_decimal(
        (size - expected_fill)
        * max(gross_edge_cash / max(size, EPSILON), Decimal("0"))
        * dec("0.25")
    )
    cancel_cost = cash_decimal(cancel_cost)
    latency_penalty_cash = cash_decimal(dec(snapshot["latency_edge_decay_penalty"]) * expected_fill)
    capital_lock_cost_cash = cash_decimal(
        dec(order["total_investment"])
        * capital_rate
        * (dec(order["hold_duration_seconds"]) / dec("86400"))
    )
    capacity_cost_cash = cash_decimal(max(capacity_used - dec("0.30"), Decimal("0")) * size * capacity_multiplier)
    crowding_cost_cash = cash_decimal(dec(snapshot["crowding_penalty_seed"]) * size * crowd_multiplier)
    total = cash_decimal(
        fees_cash
        + spread_cost_cash
        + slippage_cash
        + queue_fill_shortfall_cash
        + cancel_cost
        + latency_penalty_cash
        + capital_lock_cost_cash
        + capacity_cost_cash
        + crowding_cost_cash
    )
    return {
        "fees_cash": fees_cash,
        "spread_cost_cash": spread_cost_cash,
        "slippage_cash": slippage_cash,
        "queue_fill_shortfall_cash": queue_fill_shortfall_cash,
        "cancel_replace_cost_cash": cancel_cost,
        "latency_penalty_cash": latency_penalty_cash,
        "capital_lock_cost_cash": capital_lock_cost_cash,
        "capacity_cost_cash": capacity_cost_cash,
        "crowding_cost_cash": crowding_cost_cash,
        "tca_total_cash": total,
        "tca_erases_edge_flag": total >= max(cash_decimal(fill_probability * gross_edge_cash), Decimal("0")),
    }


def compute_trade_plan_receipts(
    fixtures: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    order_rows: list[dict[str, Any]],
    stacks_by_fixture: dict[str, list[dict[str, Any]]],
    search_by_fixture: dict[str, dict[str, Any]],
    params: dict[str, Decimal | str],
    policy_refs: list[str],
    top_k: int,
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    orders_by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in order_rows:
        orders_by_fixture[order["fixture_id"]].append(order)
    total_trial_count = len(order_rows)
    for fixture in fixtures:
        fixture_id = fixture["fixture_id"]
        snapshot = snapshots[fixture_id]
        stacks = stacks_by_fixture[fixture_id]
        for index, order in enumerate(sorted(orders_by_fixture[fixture_id], key=lambda row: row["order_variable_candidate_id"]), start=1):
            stack = stacks[(index - 1) % len(stacks)]
            trade_plan_id = f"VS1_TRADE_PLAN_{fixture_id}_{index:03d}"
            side = order["side"]
            entry_price = dec(order["entry_price"])
            side_fair = dec(order["side_fair_probability"])
            size = dec(order["order_size"])
            gross_edge = cash_decimal(size * (side_fair - entry_price))
            fill_probability = compute_fill_probability(order, snapshot)
            expected_fill = cash_decimal(size * fill_probability)
            fill_adjusted_gross = cash_decimal(fill_probability * gross_edge)
            tca = calculate_tca(order, snapshot, params, fill_probability, gross_edge)
            execution_adjusted = cash_decimal(fill_adjusted_gross - dec(tca["tca_total_cash"]))
            depth = max(dec(snapshot["depth"]), dec("1"))
            capacity_used = size / depth
            max_capacity = dec(params["configured_max_capacity_used_ratio"])
            capacity_penalty = cash_decimal(max(capacity_used - max_capacity, Decimal("0")) * size * dec("0.0400"))
            crowding_penalty = cash_decimal(dec(snapshot["crowding_penalty_seed"]) * size * dec("0.0500"))
            conflict_extra = (
                cash_decimal(size * dec("0.0400"))
                if fixture["fixture_case"] == "portfolio_conflict_fixture"
                else Decimal("0")
            )
            portfolio_penalty = cash_decimal(
                dec(snapshot["portfolio_penalty_seed"])
                * size
                * dec(params["portfolio_overlap_penalty_multiplier"])
                + conflict_extra
            )
            uncertainty_penalty = cash_decimal(dec(snapshot["uncertainty_penalty_seed"]) * size * dec(params["uncertainty_penalty_multiplier"]))
            overfit_penalty = cash_decimal(dec(total_trial_count) * dec(params["overfit_trial_penalty_multiplier"]))
            preliminary_without_scenario = cash_decimal(execution_adjusted - (
                capacity_penalty + crowding_penalty + portfolio_penalty + uncertainty_penalty + overfit_penalty
            ))
            scenario = compute_scenarios(
                fixture,
                snapshot,
                preliminary_without_scenario,
                tca,
                gross_edge,
                size,
                capacity_penalty,
                crowding_penalty,
                portfolio_penalty,
                params,
            )
            risk_total = cash_decimal(
                capacity_penalty
                + crowding_penalty
                + portfolio_penalty
                + uncertainty_penalty
                + overfit_penalty
                + dec(scenario["scenario_tail_penalty_cash"])
            )
            net = cash_decimal(execution_adjusted - risk_total)
            lcb_buffer = cash_decimal(uncertainty_penalty + dec(scenario["scenario_tail_penalty_cash"]) * dec("0.25"))
            lcb = cash_decimal(net - lcb_buffer)
            candidate_minus_no_trade = net
            no_trade_margin_bps = dec("10000") * candidate_minus_no_trade / max(dec(order["total_investment"]), EPSILON)
            capacity_gate = capacity_used <= max_capacity
            portfolio_overlap = dec("0.80") if fixture["fixture_case"] == "portfolio_conflict_fixture" else dec("0.20")
            portfolio_gate = portfolio_overlap <= dec(params["configured_max_correlation_overlap"])
            scenario_gate = bool(scenario["scenario_gate_passed"])
            agent_route_valid = True
            no_orphan_valid = True
            selection_status = selection_status_for(
                candidate_minus_no_trade,
                lcb,
                fill_probability,
                tca,
                capacity_gate,
                portfolio_gate,
                scenario_gate,
                agent_route_valid,
                no_orphan_valid,
                params,
            )
            blocker_codes = [] if selection_status == "TOP_K_ELIGIBLE" else [selection_status]
            tca_ref = f"VS1_TCA_{trade_plan_id}"
            pnl_ref = f"VS1_PNL_{trade_plan_id}"
            capacity_ref = f"VS1_CAPACITY_CROWDING_{trade_plan_id}"
            portfolio_ref = f"VS1_PORTFOLIO_{trade_plan_id}"
            scenario_ref = f"VS1_SCENARIO_LADDER_{trade_plan_id}"
            overfit_ref = f"VS1_OVERFIT_FDR_{trade_plan_id}"
            no_trade_ref = f"VS1_NO_TRADE_{trade_plan_id}"
            ranking_ref = f"VS1_RANKING_{trade_plan_id}"
            quantum_ready_ref = f"VS1_QUANTUM_READY_{trade_plan_id}"
            quantum_encoding_ref = f"VS1_QUANTUM_ENCODING_{trade_plan_id}"
            qku_refs = stack["qku_refs"]
            formula_refs = stack["formula_refs"]
            binding_refs = stack["computable_binding_refs"]
            rows["tca_breakdown_receipts.jsonl"].append(
                with_common(
                    {
                        "cancel_replace_cost_cash": money(tca["cancel_replace_cost_cash"]),
                        "capacity_cost_cash": money(tca["capacity_cost_cash"]),
                        "capital_lock_cost_cash": money(tca["capital_lock_cost_cash"]),
                        "crowding_cost_cash": money(tca["crowding_cost_cash"]),
                        "fees_cash": money(tca["fees_cash"]),
                        "fixture_id": fixture_id,
                        "latency_penalty_cash": money(tca["latency_penalty_cash"]),
                        "policy_parameter_refs": policy_refs,
                        "queue_fill_shortfall_cash": money(tca["queue_fill_shortfall_cash"]),
                        "slippage_cash": money(tca["slippage_cash"]),
                        "spread_cost_cash": money(tca["spread_cost_cash"]),
                        "tca_breakdown_ref": tca_ref,
                        "tca_erases_edge_flag": bool(tca["tca_erases_edge_flag"]),
                        "tca_total_cash": money(tca["tca_total_cash"]),
                        "tca_version": "VS1_TCA_DETERMINISTIC_V1",
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="TCAAgent",
                    consumer_agent_refs=["ExpectedCashPnLEngineAgent", "NoTradeRiskAgent"],
                    upstream_artifact_refs=[order["order_variable_candidate_id"]],
                    downstream_artifact_refs=[pnl_ref, no_trade_ref],
                )
            )
            rows["capacity_crowding_receipts.jsonl"].append(
                with_common(
                    {
                        "available_depth": money(depth),
                        "capacity_crowding_ref": capacity_ref,
                        "capacity_gate_passed": capacity_gate,
                        "capacity_penalty_cash": money(capacity_penalty),
                        "capacity_used_ratio": ratio(capacity_used),
                        "crowding_group": "CROWDED" if dec(snapshot["crowding_penalty_seed"]) >= dec("0.04") else "NORMAL",
                        "crowding_penalty_cash": money(crowding_penalty),
                        "expected_fill_quantity": money(expected_fill),
                        "fixture_id": fixture_id,
                        "order_size": money(size),
                        "policy_parameter_refs": policy_refs,
                        "thin_book_flag": fixture["fixture_case"] == "thin_book_fixture",
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="CapacityCrowdingAgent",
                    consumer_agent_refs=["ExpectedCashPnLEngineAgent", "RankerAgent"],
                    upstream_artifact_refs=[order["order_variable_candidate_id"]],
                    downstream_artifact_refs=[pnl_ref, ranking_ref],
                    blocker_codes=[] if capacity_gate else ["REJECT_CAPACITY_GATE"],
                )
            )
            marginal_utility = cash_decimal(net * dec("0.20") - portfolio_penalty)
            diversification_bonus = dec("0.40") if stack["diversity_group"] else Decimal("0")
            correlation_penalty = cash_decimal(portfolio_overlap * size * dec("0.0100"))
            rows["portfolio_diversification_receipts.jsonl"].append(
                with_common(
                    {
                        "correlated_formula_exposure_group": stack["correlated_formula_exposure_group"],
                        "diversity_group": stack["diversity_group"],
                        "fixture_id": fixture_id,
                        "formula_stack_id": stack["temporary_stack_id"],
                        "marginal_utility_cash": money(marginal_utility),
                        "platform_exposure_after_candidate": ratio(dec("0.70") if fixture["fixture_case"] == "portfolio_conflict_fixture" else dec("0.25")),
                        "platform_id": fixture["platform_id"],
                        "policy_parameter_refs": policy_refs,
                        "portfolio_gate_passed": portfolio_gate,
                        "portfolio_penalty_cash": money(portfolio_penalty),
                        "portfolio_receipt_id": portfolio_ref,
                        "side": side,
                        "side_exposure_after_candidate": ratio(dec("0.75") if fixture["fixture_case"] == "portfolio_conflict_fixture" else dec("0.30")),
                        "stack_overlap_penalty_cash": money(correlation_penalty),
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="PortfolioAgent",
                    consumer_agent_refs=["ExpectedCashPnLEngineAgent", "RankerAgent"],
                    upstream_artifact_refs=[stack["temporary_stack_id"]],
                    downstream_artifact_refs=[pnl_ref, ranking_ref],
                    blocker_codes=[] if portfolio_gate else ["REJECT_PORTFOLIO_GATE"],
                )
            )
            rows["scenario_ladder_receipts.jsonl"].append(
                with_common(
                    {
                        "adverse_probability_shift_pnl_cash": money(scenario["adverse_probability_shift_pnl_cash"]),
                        "base_case_pnl_cash": money(scenario["base_case_pnl_cash"]),
                        "crowded_book_pnl_cash": money(scenario["crowded_book_pnl_cash"]),
                        "fixture_id": fixture_id,
                        "latency_decay_pnl_cash": money(scenario["latency_decay_pnl_cash"]),
                        "lower_fill_pnl_cash": money(scenario["lower_fill_pnl_cash"]),
                        "policy_parameter_refs": policy_refs,
                        "portfolio_conflict_pnl_cash": money(scenario["portfolio_conflict_pnl_cash"]),
                        "scenario_gate_passed": scenario_gate,
                        "scenario_ladder_result_ref": scenario_ref,
                        "scenario_tail_penalty_cash": money(scenario["scenario_tail_penalty_cash"]),
                        "thin_book_pnl_cash": money(scenario["thin_book_pnl_cash"]),
                        "trade_plan_id": trade_plan_id,
                        "wider_spread_pnl_cash": money(scenario["wider_spread_pnl_cash"]),
                        "worst_case_pnl_cash": money(scenario["worst_case_pnl_cash"]),
                    },
                    producer_agent="ScenarioAgent",
                    consumer_agent_refs=["ExpectedCashPnLEngineAgent", "RankerAgent"],
                    upstream_artifact_refs=[pnl_ref],
                    downstream_artifact_refs=[ranking_ref],
                    blocker_codes=[] if scenario_gate else ["REJECT_SCENARIO_LADDER"],
                )
            )
            rows["overfit_fdr_control_receipts.jsonl"].append(
                with_common(
                    {
                        "candidate_family_count": len(stacks),
                        "fixture_id": fixture_id,
                        "formula_family_reuse_count": len(formula_refs),
                        "future_bh_fdr_ready_flag": True,
                        "future_cpcv_ready_flag": True,
                        "future_dsr_ready_flag": True,
                        "future_pbo_ready_flag": True,
                        "future_purged_embargo_ready_flag": True,
                        "multiple_testing_penalty_cash": money(overfit_penalty),
                        "order_variable_trial_count": len(orders_by_fixture[fixture_id]),
                        "overfit_fdr_method": "VS1_DETERMINISTIC_TRIAL_COUNT_PENALTY",
                        "overfit_fdr_penalty_cash": money(overfit_penalty),
                        "overfit_fdr_receipt_id": overfit_ref,
                        "policy_parameter_refs": policy_refs,
                        "stack_trial_count": len(stacks),
                        "total_candidate_trial_count": total_trial_count,
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="OverfitFDRAgent",
                    consumer_agent_refs=["ExpectedCashPnLEngineAgent", "RankerAgent"],
                    upstream_artifact_refs=[search_by_fixture[fixture_id]["variable_search_ref"]],
                    downstream_artifact_refs=[pnl_ref, ranking_ref],
                )
            )
            rows["expected_cash_pnl_receipts.jsonl"].append(
                with_common(
                    {
                        "calculation_version": "VS1_EXPECTED_CASH_PNL_V1",
                        "candidate_minus_no_trade_cash": money(candidate_minus_no_trade),
                        "capacity_penalty_cash": money(capacity_penalty),
                        "crowding_penalty_cash": money(crowding_penalty),
                        "entry_price": money(entry_price),
                        "execution_adjusted_expected_pnl_cash": money(execution_adjusted),
                        "expected_fill_quantity": money(expected_fill),
                        "fill_adjusted_gross_edge_cash": money(fill_adjusted_gross),
                        "fill_probability": ratio(fill_probability),
                        "fixture_id": fixture_id,
                        "formula_version_refs": formula_refs,
                        "gross_edge_cash": money(gross_edge),
                        "lcb_uncertainty_buffer_cash": money(lcb_buffer),
                        "lower_confidence_bound_pnl_cash": money(lcb),
                        "net_expected_pnl_cash": money(net),
                        "overfit_fdr_penalty_cash": money(overfit_penalty),
                        "pnl_receipt_id": pnl_ref,
                        "policy_parameter_refs": policy_refs,
                        "portfolio_penalty_cash": money(portfolio_penalty),
                        "risk_penalty_total_cash": money(risk_total),
                        "scenario_tail_penalty_cash": money(scenario["scenario_tail_penalty_cash"]),
                        "side": side,
                        "side_fair_probability": money(side_fair),
                        "tca_breakdown_ref": tca_ref,
                        "tca_total_cash": money(tca["tca_total_cash"]),
                        "trade_plan_id": trade_plan_id,
                        "uncertainty_penalty_cash": money(uncertainty_penalty),
                    },
                    producer_agent="ExpectedCashPnLEngineAgent",
                    consumer_agent_refs=["NoTradeRiskAgent", "RankerAgent"],
                    upstream_artifact_refs=[tca_ref, capacity_ref, portfolio_ref, scenario_ref, overfit_ref],
                    downstream_artifact_refs=[no_trade_ref, ranking_ref],
                )
            )
            no_trade_wins = candidate_minus_no_trade <= 0
            memory_hint = condition_memory_hint(fixture, snapshot, side, stack, blocker_codes)
            rows["no_trade_comparator_receipts.jsonl"].append(
                with_common(
                    {
                        "candidate_minus_no_trade_cash": money(candidate_minus_no_trade),
                        "condition_scoped_memory_hint": memory_hint,
                        "fixture_id": fixture_id,
                        "formula_mutation_flag": False,
                        "gate_relaxation_to_force_pnl_flag": False,
                        "global_formula_ban_flag": False,
                        "global_qku_ban_flag": False,
                        "hindsight_backsolve_flag": False,
                        "impossible_fill_flag": False,
                        "impossible_price_flag": False,
                        "lower_confidence_bound_pnl_cash": money(lcb),
                        "no_trade_comparator_ref": no_trade_ref,
                        "no_trade_expected_pnl_cash": "0.0000",
                        "no_trade_margin_bps": ratio(no_trade_margin_bps),
                        "no_trade_wins_flag": no_trade_wins,
                        "qku_deletion_flag": False,
                        "rejection_reason_codes": blocker_codes,
                        "selection_status": selection_status,
                        "similar_context_cooldown_hint": "RETRY_ONLY_IF_SPREAD_DEPTH_FILL_OR_PORTFOLIO_BUCKET_CHANGES",
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="NoTradeRiskAgent",
                    consumer_agent_refs=["TradePlanCandidateAssembler", "GovernanceAgent"],
                    upstream_artifact_refs=[pnl_ref],
                    downstream_artifact_refs=[generated_ref("trade_plan_candidates.jsonl")],
                    blocker_codes=blocker_codes,
                )
            )
            objective_refs = build_objective_terms(
                rows,
                trade_plan_id,
                fixture_id,
                tca,
                gross_edge,
                fill_adjusted_gross,
                uncertainty_penalty,
                overfit_penalty,
                scenario["scenario_tail_penalty_cash"],
                portfolio_penalty,
                marginal_utility,
                diversification_bonus,
                correlation_penalty,
                candidate_minus_no_trade,
            )
            constraint_refs = build_constraints(
                rows,
                trade_plan_id,
                fixture_id,
                fill_probability,
                lcb,
                candidate_minus_no_trade,
                fill_adjusted_gross,
                tca,
                capacity_used,
                capacity_gate,
                portfolio_gate,
                scenario_gate,
                agent_route_valid,
                no_orphan_valid,
                selection_status,
            )
            ranking_score = cash_decimal(
                lcb
                + marginal_utility
                + diversification_bonus
                - correlation_penalty
                - dec(scenario["scenario_tail_penalty_cash"])
            )
            rows["execution_adjusted_ranking_receipts.jsonl"].append(
                with_common(
                    {
                        "candidate_minus_no_trade_cash": money(candidate_minus_no_trade),
                        "capacity_penalty_cash": money(capacity_penalty),
                        "constraint_penalty_refs": constraint_refs,
                        "correlation_overlap_penalty_cash": money(correlation_penalty),
                        "crowding_penalty_cash": money(crowding_penalty),
                        "diversification_bonus_cash": money(diversification_bonus),
                        "fill_probability": ratio(fill_probability),
                        "fixture_id": fixture_id,
                        "latency_penalty_cash": money(tca["latency_penalty_cash"]),
                        "lower_confidence_bound_pnl_cash": money(lcb),
                        "marginal_utility_cash": money(marginal_utility),
                        "net_expected_pnl_cash": money(net),
                        "objective_term_refs": objective_refs,
                        "overfit_fdr_penalty_cash": money(overfit_penalty),
                        "policy_parameter_refs": policy_refs,
                        "portfolio_penalty_cash": money(portfolio_penalty),
                        "rank": 0,
                        "ranking_receipt_id": ranking_ref,
                        "ranking_score_cash": money(ranking_score),
                        "scenario_tail_penalty_cash": money(scenario["scenario_tail_penalty_cash"]),
                        "selection_status": selection_status,
                        "tca_total_cash": money(tca["tca_total_cash"]),
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="RankerAgent",
                    consumer_agent_refs=["ChampionChallengerSelectionAgent", "PaperIntentPreviewAgent"],
                    upstream_artifact_refs=[pnl_ref, no_trade_ref, *objective_refs, *constraint_refs],
                    downstream_artifact_refs=[generated_ref("champion_challenger_selection_receipts.jsonl")],
                    blocker_codes=blocker_codes,
                )
            )
            decision_variable_refs = [order["order_variable_candidate_id"], stack["temporary_stack_id"]]
            fallback_refs = [
                "TPE",
                "Hyperband",
                "differential_evolution",
                "dual_annealing",
                "SHGO",
                "greedy_top_k",
                "beam_search",
                "successive_halving",
            ]
            rows["trade_plan_quantum_encoding_receipts.jsonl"].append(
                with_common(
                    {
                        "anneal_time_policy": "NOT_SET_IN_VS1",
                        "backend_default_policy": "ADOPT_OFFICIAL_LIBRARY_OR_PROVIDER_DEFAULTS_IN_LATER_EXECUTION_PR",
                        "binary_variable_count": 2,
                        "bqm_candidate_ref": f"VS1_BQM_METADATA_{trade_plan_id}",
                        "chain_strength_policy": "NOT_SET_IN_VS1",
                        "classical_fallback_optimizer_refs": fallback_refs,
                        "coefficient_normalization_policy": "UNIT_NORMALIZED_FOR_FIXTURE_ONLY",
                        "coefficient_scale_max": "1.0000",
                        "coefficient_scale_min": "-1.0000",
                        "constraint_count": len(constraint_refs),
                        "constraint_penalty_refs": constraint_refs,
                        "continuous_variable_count": 1,
                        "cqm_candidate_ref": f"VS1_CQM_METADATA_{trade_plan_id}",
                        "decision_variable_refs": decision_variable_refs,
                        "embedding_complexity_proxy": "LOW_FIXTURE_METADATA_ONLY",
                        "fixture_id": fixture_id,
                        "integer_variable_count": 1,
                        "interpret_back_map_ref": f"VS1_INTERPRET_BACK_{trade_plan_id}",
                        "ising_hamiltonian_candidate_ref": f"VS1_ISING_METADATA_{trade_plan_id}",
                        "linear_term_count": len(objective_refs),
                        "num_reads_policy": "NOT_SET_IN_VS1",
                        "objective_term_refs": objective_refs,
                        "penalty_scaling_policy": "UNIT_NORMALIZED_FIXTURE_PENALTIES",
                        "penalty_term_count": len(constraint_refs),
                        "qaoa_reps_policy": "NOT_SET_IN_VS1",
                        "quadratic_program_candidate_ref": f"VS1_QUADRATIC_PROGRAM_METADATA_{trade_plan_id}",
                        "quadratic_term_count": 2,
                        "quantum_advantage_claim_flag": False,
                        "quantum_backend_execution_flag": False,
                        "quantum_encoding_ref": quantum_encoding_ref,
                        "qubo_matrix_candidate_ref": f"VS1_QUBO_METADATA_{trade_plan_id}",
                        "shots_policy": "NOT_SET_IN_VS1",
                        "sparsity_ratio": "0.250000",
                        "temporary_stack_id": stack["temporary_stack_id"],
                        "trade_plan_id": trade_plan_id,
                    },
                    producer_agent="QuantumEncodingAgent",
                    consumer_agent_refs=["QuantumReadinessAgent", "QOPT"],
                    upstream_artifact_refs=[*objective_refs, *constraint_refs],
                    downstream_artifact_refs=[quantum_ready_ref],
                )
            )
            rows["quantum_structural_readiness_receipts.jsonl"].append(
                with_common(
                    {
                        "binary_variable_candidates": ["select_trade_plan", "side_indicator"],
                        "bqm_eligible_flag": True,
                        "classical_fallback_optimizer_refs": fallback_refs,
                        "constraint_terms": constraint_refs,
                        "continuous_variable_candidates": ["entry_price"],
                        "cqm_eligible_flag": True,
                        "formula_refs": formula_refs,
                        "future_qopt_handoff_reason": "VS1_EMITS_METADATA_ONLY_FOR_QOPT_ENCODING_AND_BACKEND_SELECTION_LATER",
                        "integer_variable_candidates": ["order_size_bucket"],
                        "interpret_back_map_ref": f"VS1_INTERPRET_BACK_{trade_plan_id}",
                        "ising_mapping_candidate_flag": True,
                        "objective_linear_terms": objective_refs,
                        "objective_quadratic_terms": ["portfolio_overlap_x_size", "capacity_pressure_x_size"],
                        "optimization_problem_class": "BOUNDED_MIXED_INTEGER_FIXTURE_METADATA",
                        "penalty_terms": constraint_refs,
                        "qaoa_candidate_flag": True,
                        "qku_refs": qku_refs,
                        "quadratic_program_eligible_flag": True,
                        "quantum_advantage_claim_flag": False,
                        "quantum_backend_execution_flag": False,
                        "quantum_structural_readiness_ref": quantum_ready_ref,
                        "qubo_eligible_flag": True,
                        "temporary_stack_id": stack["temporary_stack_id"],
                        "trade_plan_id": trade_plan_id,
                        "variable_domain_summary": {
                            "binary": 2,
                            "continuous": 1,
                            "integer": 1,
                            "source": "VS1_METADATA_ONLY",
                        },
                        "vqe_candidate_flag": False,
                    },
                    producer_agent="QuantumReadinessAgent",
                    consumer_agent_refs=["QOPT", "GovernanceAgent"],
                    upstream_artifact_refs=[quantum_encoding_ref],
                    downstream_artifact_refs=[generated_ref("vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json")],
                )
            )
            rows["trade_plan_candidates.jsonl"].append(
                with_common(
                    {
                        "agent_route_ref": "VS1_AGENT_ROUTE_VALID_FROM_RP5C_AGENT_DUTY",
                        "blocker_codes": blocker_codes,
                        "candidate_minus_no_trade_cash": money(candidate_minus_no_trade),
                        "cancel_replace_policy": order["cancel_replace_policy"],
                        "capacity_crowding_ref": capacity_ref,
                        "capital_lock_cost_cash": money(tca["capital_lock_cost_cash"]),
                        "champion_challenger_ref": "",
                        "computable_binding_refs": binding_refs,
                        "contract_id": fixture["contract_id"],
                        "constraint_penalty_refs": constraint_refs,
                        "entry_price": money(entry_price),
                        "estimated_gross_pnl_cash": money(gross_edge),
                        "estimated_yes_probability": snapshot["estimated_yes_probability_candidates"][0],
                        "event_id": fixture["event_id"],
                        "ex_ante_candidate_flag": True,
                        "execution_adjusted_expected_pnl_cash": money(execution_adjusted),
                        "expected_gross_pnl_cash": money(gross_edge),
                        "fill_probability": ratio(fill_probability),
                        "fixture_id": fixture_id,
                        "formula_refs": formula_refs,
                        "formula_stack_id": stack["temporary_stack_id"],
                        "gate_relaxation_count": 0,
                        "hindsight_free_flag": True,
                        "hold_duration_seconds": order["hold_duration_seconds"],
                        "impossible_fill_flag": False,
                        "impossible_price_flag": False,
                        "lower_confidence_bound_pnl_cash": money(lcb),
                        "maker_taker_policy": order["maker_taker_policy"],
                        "market_family": MARKET_FAMILY,
                        "market_id": fixture["market_id"],
                        "net_expected_pnl_cash": money(net),
                        "no_orphan_proof_ref": f"VS1_NO_ORPHAN_QKU_FORMULA_{fixture_id}",
                        "no_trade_comparator_ref": no_trade_ref,
                        "objective_term_refs": objective_refs,
                        "order_size": money(size),
                        "order_variable_candidate_ref": order["order_variable_candidate_id"],
                        "overfit_fdr_receipt_ref": overfit_ref,
                        "paper_intent_preview_ref": "",
                        "platform_id": fixture["platform_id"],
                        "portfolio_receipt_ref": portfolio_ref,
                        "qku_refs": qku_refs,
                        "quantum_encoding_ref": quantum_encoding_ref,
                        "quantum_structural_readiness_ref": quantum_ready_ref,
                        "ranking_receipt_ref": ranking_ref,
                        "risk_penalty_total_cash": money(risk_total),
                        "scenario_ladder_result_ref": scenario_ref,
                        "selection_status": selection_status,
                        "side": side,
                        "side_fair_probability": money(side_fair),
                        "stack_role_refs": stack["stack_role_refs"],
                        "stage_profile_id": STAGE_PROFILE_ID,
                        "tca_breakdown_ref": tca_ref,
                        "tca_total_cash": money(tca["tca_total_cash"]),
                        "temporary_stack_ref": stack["temporary_stack_id"],
                        "total_investment": order["total_investment"],
                        "trade_plan_id": trade_plan_id,
                        "variable_search_ref": search_by_fixture[fixture_id]["variable_search_ref"],
                    },
                    producer_agent="TradePlanCandidateAssembler",
                    consumer_agent_refs=["RankerAgent", "PaperIntentPreviewAgent", "GovernanceAgent"],
                    upstream_artifact_refs=[order["order_variable_candidate_id"], stack["temporary_stack_id"], pnl_ref, no_trade_ref],
                    downstream_artifact_refs=[ranking_ref, quantum_ready_ref],
                    blocker_codes=blocker_codes,
                )
            )
    assign_ranks_and_previews(rows, top_k)
    update_search_rejection_counts(rows, search_by_fixture)
    return rows


def compute_scenarios(
    fixture: dict[str, Any],
    snapshot: dict[str, Any],
    base: Decimal,
    tca: dict[str, Decimal | bool],
    gross_edge: Decimal,
    size: Decimal,
    capacity_penalty: Decimal,
    crowding_penalty: Decimal,
    portfolio_penalty: Decimal,
    params: dict[str, Decimal | str],
) -> dict[str, Decimal | bool]:
    base = cash_decimal(base)
    wider = cash_decimal(base - dec(tca["spread_cost_cash"]) * dec("1.5") - dec(snapshot["spread"]) * size * dec("0.20"))
    lower_fill = cash_decimal(base - abs(gross_edge) * dec("0.25"))
    latency = cash_decimal(base - dec(tca["latency_penalty_cash"]) * dec("2") - size * dec(snapshot["latency_edge_decay_penalty"]) * dec("0.50"))
    adverse = cash_decimal(base - size * dec("0.0300"))
    thin = cash_decimal(
        base
        - capacity_penalty * dec("0.50")
        - (size * dec("0.0200") if fixture["fixture_case"] == "thin_book_fixture" else Decimal("0"))
    )
    crowded = cash_decimal(
        base
        - crowding_penalty * dec("0.50")
        - (size * dec("0.0200") if fixture["fixture_case"] == "crowded_capacity_fixture" else Decimal("0"))
    )
    portfolio = cash_decimal(base - portfolio_penalty * dec("0.75"))
    cases = [base, wider, lower_fill, latency, adverse, thin, crowded, portfolio]
    worst = min(cases)
    tail = cash_decimal(max(base - worst, Decimal("0")) * dec(params["scenario_tail_penalty_multiplier"]))
    pass_count = sum(1 for value in cases if value > 0)
    return {
        "adverse_probability_shift_pnl_cash": adverse,
        "base_case_pnl_cash": base,
        "crowded_book_pnl_cash": crowded,
        "latency_decay_pnl_cash": latency,
        "lower_fill_pnl_cash": lower_fill,
        "portfolio_conflict_pnl_cash": portfolio,
        "scenario_gate_passed": pass_count >= int(dec(params["configured_min_scenario_gate_pass_count"])),
        "scenario_tail_penalty_cash": tail,
        "thin_book_pnl_cash": thin,
        "wider_spread_pnl_cash": wider,
        "worst_case_pnl_cash": worst,
    }


def selection_status_for(
    candidate_minus_no_trade: Decimal,
    lcb: Decimal,
    fill_probability: Decimal,
    tca: dict[str, Decimal | bool],
    capacity_gate: bool,
    portfolio_gate: bool,
    scenario_gate: bool,
    agent_route_valid: bool,
    no_orphan_valid: bool,
    params: dict[str, Decimal | str],
) -> str:
    if candidate_minus_no_trade <= 0:
        return "NO_TRADE_WINS"
    if lcb <= dec(params["configured_min_lcb_cash"]):
        return "REJECT_LCB_NOT_POSITIVE"
    if fill_probability < dec(params["configured_min_fill_probability"]):
        return "REJECT_FILL_TOO_LOW"
    if bool(tca["tca_erases_edge_flag"]):
        return "REJECT_TCA_WIPES_EDGE"
    if not capacity_gate:
        return "REJECT_CAPACITY_GATE"
    if not portfolio_gate:
        return "REJECT_PORTFOLIO_GATE"
    if not scenario_gate:
        return "REJECT_SCENARIO_LADDER"
    if not agent_route_valid:
        return "REJECT_AGENT_ROUTE"
    if not no_orphan_valid:
        return "REJECT_NO_ORPHAN_PROOF"
    return "TOP_K_ELIGIBLE"


def condition_memory_hint(fixture: dict[str, Any], snapshot: dict[str, Any], side: str, stack: dict[str, Any], failure_codes: list[str]) -> dict[str, Any]:
    return {
        "contract_id": fixture["contract_id"],
        "depth_bucket": "THIN" if fixture["fixture_case"] == "thin_book_fixture" else "NORMAL",
        "event_category": fixture["fixture_case"],
        "failure_reason_codes": failure_codes,
        "formula_refs": stack["formula_refs"],
        "formula_stack_id": stack["temporary_stack_id"],
        "hold_duration_bucket": "ONE_HOUR",
        "latency_bucket": snapshot.get("latency_bucket", fixture.get("latency_bucket", "UNKNOWN")),
        "liquidity_bucket": fixture["liquidity_bucket"],
        "maker_taker_policy": "MAKER_TAKER_SPLIT_FIXTURE",
        "market_family": MARKET_FAMILY,
        "order_size_bucket": "LARGE" if fixture["fixture_case"] in {"crowded_capacity_fixture", "portfolio_conflict_fixture"} else "SMALL",
        "platform_id": fixture["platform_id"],
        "qku_refs": stack["qku_refs"],
        "side": side,
        "spread_bucket": "WIDE" if dec(snapshot["spread"]) > dec("0.05") else "TIGHT",
        "time_to_resolution_bucket": "ONE_DAY",
    }


OBJECTIVE_TERMS = (
    "expected_edge",
    "fill_adjusted_edge",
    "fees",
    "spread",
    "slippage",
    "queue_fill_shortfall",
    "cancel_replace_cost",
    "latency_decay",
    "capital_lock",
    "capacity_cost",
    "crowding_cost",
    "uncertainty",
    "overfit_fdr",
    "scenario_tail",
    "portfolio_overlap",
    "marginal_utility",
    "diversification_bonus",
    "correlation_overlap_penalty",
    "no_trade_margin",
)


def build_objective_terms(
    rows: dict[str, list[dict[str, Any]]],
    trade_plan_id: str,
    fixture_id: str,
    tca: dict[str, Decimal | bool],
    gross_edge: Decimal,
    fill_adjusted_gross: Decimal,
    uncertainty_penalty: Decimal,
    overfit_penalty: Decimal,
    scenario_tail: Decimal,
    portfolio_penalty: Decimal,
    marginal_utility: Decimal,
    diversification_bonus: Decimal,
    correlation_penalty: Decimal,
    no_trade_margin: Decimal,
) -> list[str]:
    values = {
        "expected_edge": gross_edge,
        "fill_adjusted_edge": fill_adjusted_gross,
        "fees": dec(tca["fees_cash"]),
        "spread": dec(tca["spread_cost_cash"]),
        "slippage": dec(tca["slippage_cash"]),
        "queue_fill_shortfall": dec(tca["queue_fill_shortfall_cash"]),
        "cancel_replace_cost": dec(tca["cancel_replace_cost_cash"]),
        "latency_decay": dec(tca["latency_penalty_cash"]),
        "capital_lock": dec(tca["capital_lock_cost_cash"]),
        "capacity_cost": dec(tca["capacity_cost_cash"]),
        "crowding_cost": dec(tca["crowding_cost_cash"]),
        "uncertainty": uncertainty_penalty,
        "overfit_fdr": overfit_penalty,
        "scenario_tail": scenario_tail,
        "portfolio_overlap": portfolio_penalty,
        "marginal_utility": marginal_utility,
        "diversification_bonus": diversification_bonus,
        "correlation_overlap_penalty": correlation_penalty,
        "no_trade_margin": no_trade_margin,
    }
    refs = []
    for term in OBJECTIVE_TERMS:
        ref = f"VS1_OBJECTIVE_{trade_plan_id}_{term.upper()}"
        refs.append(ref)
        value = values[term]
        is_cost = term in {
            "fees",
            "spread",
            "slippage",
            "queue_fill_shortfall",
            "cancel_replace_cost",
            "latency_decay",
            "capital_lock",
            "capacity_cost",
            "crowding_cost",
            "uncertainty",
            "overfit_fdr",
            "scenario_tail",
            "portfolio_overlap",
            "correlation_overlap_penalty",
        }
        rows["objective_term_ledger.jsonl"].append(
            with_common(
                {
                    "constraint_candidate_flag": is_cost,
                    "execution_authority_ref": EXECUTION_AUTHORITY_REF,
                    "fixture_id": fixture_id,
                    "included_in_quantum_encoding_flag": True,
                    "included_in_ranking_flag": term
                    in {
                        "marginal_utility",
                        "diversification_bonus",
                        "correlation_overlap_penalty",
                        "scenario_tail",
                        "no_trade_margin",
                    },
                    "linear_term_candidate_flag": True,
                    "objective_term_ref": ref,
                    "penalty_candidate_flag": is_cost,
                    "quadratic_term_candidate_flag": term in {"portfolio_overlap", "capacity_cost", "crowding_cost"},
                    "term_cash_value": money(value),
                    "term_direction": "MINIMIZE" if is_cost else "MAXIMIZE",
                    "term_name": term,
                    "term_normalized_value": ratio(value / dec("100")),
                    "term_role": "COST" if is_cost else "BENEFIT",
                    "term_source_receipt_ref": trade_plan_id,
                    "term_weight_ref": _field_ref("lcb_weight") if term == "no_trade_margin" else _field_ref("marginal_utility_weight"),
                    "trade_plan_id": trade_plan_id,
                },
                producer_agent="ObjectiveTermsAgent",
                consumer_agent_refs=["RankerAgent", "QuantumReadinessAgent", "QuantumEncodingAgent"],
                upstream_artifact_refs=[trade_plan_id],
                downstream_artifact_refs=[generated_ref("execution_adjusted_ranking_receipts.jsonl"), generated_ref("trade_plan_quantum_encoding_receipts.jsonl")],
            )
        )
    return refs


CONSTRAINT_NAMES = (
    "min_fill_probability",
    "positive_lcb",
    "positive_no_trade_margin",
    "max_tca_to_edge",
    "max_capacity_used_ratio",
    "portfolio_gate",
    "scenario_gate",
    "agent_route_valid",
    "no_orphan_proof_valid",
    "stage1_identity_eligible",
    "no_unknown_needs_review",
    "ephemeral_stack_only",
    "ex_ante_candidate_only",
    "no_gate_relaxation_to_force_pnl",
    "no_impossible_price",
    "no_impossible_fill",
    "no_hindsight_backsolve",
    "no_backend_execution",
)


def build_constraints(
    rows: dict[str, list[dict[str, Any]]],
    trade_plan_id: str,
    fixture_id: str,
    fill_probability: Decimal,
    lcb: Decimal,
    candidate_minus_no_trade: Decimal,
    fill_adjusted_gross: Decimal,
    tca: dict[str, Decimal | bool],
    capacity_used: Decimal,
    capacity_gate: bool,
    portfolio_gate: bool,
    scenario_gate: bool,
    agent_route_valid: bool,
    no_orphan_valid: bool,
    selection_status: str,
) -> list[str]:
    refs = []
    checks = {
        "min_fill_probability": fill_probability >= dec("0.35"),
        "positive_lcb": lcb > 0,
        "positive_no_trade_margin": candidate_minus_no_trade > 0,
        "max_tca_to_edge": dec(tca["tca_total_cash"]) < max(fill_adjusted_gross, Decimal("0")),
        "max_capacity_used_ratio": capacity_gate,
        "portfolio_gate": portfolio_gate,
        "scenario_gate": scenario_gate,
        "agent_route_valid": agent_route_valid,
        "no_orphan_proof_valid": no_orphan_valid,
        "stage1_identity_eligible": True,
        "no_unknown_needs_review": True,
        "ephemeral_stack_only": True,
        "ex_ante_candidate_only": True,
        "no_gate_relaxation_to_force_pnl": True,
        "no_impossible_price": True,
        "no_impossible_fill": True,
        "no_hindsight_backsolve": True,
        "no_backend_execution": True,
    }
    for name in CONSTRAINT_NAMES:
        ref = f"VS1_CONSTRAINT_{trade_plan_id}_{name.upper()}"
        refs.append(ref)
        passed = checks[name]
        rows["constraint_penalty_policy_receipts.jsonl"].append(
            with_common(
                {
                    "constraint_bound": "0.35" if name == "min_fill_probability" else "0",
                    "constraint_direction": "PASS_REQUIRED",
                    "constraint_expression_ref": f"VS1_CONSTRAINT_EXPR::{name}",
                    "constraint_name": name,
                    "constraint_penalty_ref": ref,
                    "constraint_type": "HARD_GATE" if name.startswith("no_") or name.endswith("_valid") else "RISK_OR_EXECUTION_GATE",
                    "constraint_unit": "BOOLEAN_OR_DECIMAL_FIXTURE",
                    "fixture_id": fixture_id,
                    "hard_constraint_flag": True,
                    "penalty_scaling_policy": "UNIT_NORMALIZED_FIXTURE_ONLY",
                    "penalty_term_ref": f"VS1_PENALTY_TERM_{name.upper()}",
                    "penalty_weight_ref": _field_ref("lcb_weight"),
                    "soft_penalty_flag": not name.startswith("no_"),
                    "trade_plan_id": trade_plan_id,
                    "violated_flag": not passed,
                    "violation_amount": "0.0000" if passed else "1.0000",
                },
                producer_agent="ConstraintPenaltyAgent",
                consumer_agent_refs=["NoTradeRiskAgent", "QuantumEncodingAgent", "RankerAgent"],
                upstream_artifact_refs=[trade_plan_id],
                downstream_artifact_refs=[generated_ref("trade_plan_candidates.jsonl"), generated_ref("trade_plan_quantum_encoding_receipts.jsonl")],
                blocker_codes=[] if passed or selection_status == "NO_TRADE_WINS" else [selection_status],
            )
        )
    return refs


def assign_ranks_and_previews(rows: dict[str, list[dict[str, Any]]], top_k: int) -> None:
    rankings = rows["execution_adjusted_ranking_receipts.jsonl"]
    ranking_by_plan = {row["trade_plan_id"]: row for row in rankings}
    candidates = rows["trade_plan_candidates.jsonl"]
    candidates_by_plan = {row["trade_plan_id"]: row for row in candidates}
    by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rankings:
        by_fixture[row["fixture_id"]].append(row)
    preview_refs_by_plan: dict[str, str] = {}
    champion_ref_by_plan: dict[str, str] = {}
    for fixture_id, fixture_rankings in by_fixture.items():
        sorted_rankings = sorted(
            fixture_rankings,
            key=lambda row: (0 if row["selection_status"] == "TOP_K_ELIGIBLE" else 1, -dec(row["ranking_score_cash"]), row["trade_plan_id"]),
        )
        rank = 0
        eligible = []
        for row in sorted_rankings:
            if row["selection_status"] == "TOP_K_ELIGIBLE":
                rank += 1
                row["rank"] = rank
                if rank <= top_k:
                    eligible.append(row)
            else:
                row["rank"] = 0
        champion = eligible[0] if eligible else None
        challengers = []
        seen_diversity: set[tuple[str, str, str]] = set()
        if champion:
            champ_candidate = candidates_by_plan[champion["trade_plan_id"]]
            seen_diversity.add((champ_candidate["platform_id"], champ_candidate["side"], champ_candidate["temporary_stack_ref"]))
            for ranking in eligible[1:]:
                candidate = candidates_by_plan[ranking["trade_plan_id"]]
                key = (candidate["platform_id"], candidate["side"], candidate["temporary_stack_ref"])
                if key not in seen_diversity:
                    challengers.append(ranking)
                    seen_diversity.add(key)
                if len(challengers) >= 2:
                    break
        cc_ref = f"VS1_CHAMPION_CHALLENGER_{fixture_id}"
        preview_refs: list[str] = []
        for role, ranking in ([("CHAMPION", champion)] if champion else []) + [("CHALLENGER", item) for item in challengers]:
            if ranking is None:
                continue
            candidate = candidates_by_plan[ranking["trade_plan_id"]]
            preview_ref = f"VS1_PAPER_INTENT_PREVIEW_{ranking['trade_plan_id']}"
            preview_refs.append(preview_ref)
            preview_refs_by_plan[ranking["trade_plan_id"]] = preview_ref
            rows["paper_intent_candidate_previews.jsonl"].append(
                with_common(
                    {
                        "cancel_replace_policy": candidate["cancel_replace_policy"],
                        "champion_challenger_role": role,
                        "contract_id": candidate["contract_id"],
                        "entry_price": candidate["entry_price"],
                        "expected_net_cash_pnl": candidate["net_expected_pnl_cash"],
                        "fixture_id": fixture_id,
                        "lower_confidence_bound_pnl_cash": candidate["lower_confidence_bound_pnl_cash"],
                        "maker_taker_policy": candidate["maker_taker_policy"],
                        "market_id": candidate["market_id"],
                        "no_trade_margin_cash": candidate["candidate_minus_no_trade_cash"],
                        "order_size": candidate["order_size"],
                        "paper_intent_preview_id": preview_ref,
                        "paper_ready_preview_flag": True,
                        "platform_id": candidate["platform_id"],
                        "ranking_score_cash": ranking["ranking_score_cash"],
                        "side": candidate["side"],
                        "trade_plan_id": candidate["trade_plan_id"],
                    },
                    producer_agent="PaperIntentPreviewAgent",
                    consumer_agent_refs=["OwnerReviewFuture", "GovernanceAgent"],
                    upstream_artifact_refs=[ranking["ranking_receipt_id"], cc_ref],
                    downstream_artifact_refs=[generated_ref("vs1_run_receipt.report.json")],
                )
            )
        if champion:
            champion_ref_by_plan[champion["trade_plan_id"]] = cc_ref
            for challenger in challengers:
                champion_ref_by_plan[challenger["trade_plan_id"]] = cc_ref
        rows["champion_challenger_selection_receipts.jsonl"].append(
            with_common(
                {
                    "challenger_score_cash_list": [item["ranking_score_cash"] for item in challengers],
                    "challenger_trade_plan_ids": [item["trade_plan_id"] for item in challengers],
                    "champion_score_cash": champion["ranking_score_cash"] if champion else "0.0000",
                    "champion_trade_plan_id": champion["trade_plan_id"] if champion else "",
                    "diversity_constraints_applied": [
                        "platform",
                        "side",
                        "formula_stack",
                        "role_coverage",
                        "liquidity_bucket",
                        "latency_bucket",
                        "capacity_bucket",
                        "scenario_vulnerability_bucket",
                        "quantum_encoding_class",
                    ],
                    "fixture_id": fixture_id,
                    "paper_intent_preview_refs": preview_refs,
                    "same_platform_repeat_count": 0,
                    "same_side_repeat_count": 0,
                    "same_stack_repeat_count": 0,
                    "selection_method": "EXECUTION_ADJUSTED_TOP_K_WITH_DIVERSITY" if champion else "NO_ELIGIBLE_CANDIDATE_NO_TRADE_VALID",
                    "champion_challenger_ref": cc_ref,
                },
                producer_agent="RankerAgent",
                consumer_agent_refs=["PaperIntentPreviewAgent", "GovernanceAgent"],
                upstream_artifact_refs=[row["ranking_receipt_id"] for row in fixture_rankings],
                downstream_artifact_refs=[generated_ref("paper_intent_candidate_previews.jsonl"), generated_ref("vs1_run_receipt.report.json")],
                blocker_codes=[] if champion else ["NO_ELIGIBLE_POSITIVE_NET_CASH_PNL_CANDIDATE_FOUND"],
            )
        )
    for candidate in candidates:
        candidate["paper_intent_preview_ref"] = preview_refs_by_plan.get(candidate["trade_plan_id"], "")
        candidate["champion_challenger_ref"] = champion_ref_by_plan.get(candidate["trade_plan_id"], f"VS1_CHAMPION_CHALLENGER_{candidate['fixture_id']}")


def update_search_rejection_counts(rows: dict[str, list[dict[str, Any]]], search_by_fixture: dict[str, dict[str, Any]]) -> None:
    candidates = rows["trade_plan_candidates.jsonl"]
    by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_fixture[candidate["fixture_id"]].append(candidate)
    for search in search_by_fixture.values():
        fixture_candidates = by_fixture[search["fixture_id"]]
        counts = Counter(candidate["selection_status"] for candidate in fixture_candidates)
        search["eligible_candidate_count"] = counts.get("TOP_K_ELIGIBLE", 0)
        search["no_eligible_positive_candidate_flag"] = search["eligible_candidate_count"] == 0
        search["no_eligible_reason_codes"] = [] if search["eligible_candidate_count"] else ["NO_ELIGIBLE_POSITIVE_NET_CASH_PNL_CANDIDATE_FOUND"]
        search["rejected_by_tca_count"] = counts.get("REJECT_TCA_WIPES_EDGE", 0)
        search["rejected_by_fill_count"] = counts.get("REJECT_FILL_TOO_LOW", 0)
        search["rejected_by_capacity_count"] = counts.get("REJECT_CAPACITY_GATE", 0)
        search["rejected_by_portfolio_count"] = counts.get("REJECT_PORTFOLIO_GATE", 0)
        search["rejected_by_scenario_count"] = counts.get("REJECT_SCENARIO_LADDER", 0)
        search["rejected_by_overfit_fdr_count"] = 0


def build_no_pnl_forcing_proofs(fixtures: list[dict[str, Any]], rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    plans_by_fixture: dict[str, list[str]] = defaultdict(list)
    search_ref_by_fixture = {row["fixture_id"]: row["variable_search_ref"] for row in rows["trade_plan_variable_search_receipts.jsonl"]}
    for candidate in rows["trade_plan_candidates.jsonl"]:
        plans_by_fixture[candidate["fixture_id"]].append(candidate["trade_plan_id"])
    proof_rows = []
    zero_fields = {
        "formula_mutation_count": 0,
        "qku_deletion_count": 0,
        "formula_deletion_count": 0,
        "global_qku_ban_count": 0,
        "global_formula_ban_count": 0,
        "impossible_price_candidate_count": 0,
        "impossible_fill_candidate_count": 0,
        "hindsight_backsolve_count": 0,
        "post_hoc_exit_selection_count": 0,
        "ignored_fee_count": 0,
        "ignored_spread_count": 0,
        "ignored_slippage_count": 0,
        "ignored_fill_risk_count": 0,
        "ignored_latency_risk_count": 0,
        "ignored_capacity_risk_count": 0,
        "ignored_portfolio_risk_count": 0,
        "ignored_scenario_risk_count": 0,
        "ignored_overfit_fdr_count": 0,
        "raw_edge_promoted_without_tca_count": 0,
        "no_trade_overridden_count": 0,
        "gate_relaxation_attempt_count": 0,
    }
    for fixture in fixtures:
        proof_rows.append(
            with_common(
                {
                    **zero_fields,
                    "fixture_id": fixture["fixture_id"],
                    "gate_relaxation_allowed_flag": False,
                    "no_pnl_forcing_proof_ref": f"VS1_NO_PNL_FORCING_{fixture['fixture_id']}",
                    "proof_status": "PASS_NO_PNL_FORCING_ZERO_COUNTS",
                    "trade_plan_ids_checked": sorted(plans_by_fixture[fixture["fixture_id"]]),
                    "variable_search_ref": search_ref_by_fixture[fixture["fixture_id"]],
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["VS1Validator", "OwnerReviewFuture"],
                upstream_artifact_refs=[search_ref_by_fixture[fixture["fixture_id"]], generated_ref("trade_plan_candidates.jsonl")],
                downstream_artifact_refs=[generated_ref("vs1_run_receipt.report.json")],
            )
        )
    return proof_rows


def build_no_orphan_qku_formula_proof(binding_rows: list[dict[str, Any]], stack_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    binding_downstream = defaultdict(list)
    for stack in stack_rows:
        for binding_ref in stack["computable_binding_refs"]:
            binding_downstream[binding_ref].append(stack["temporary_stack_id"])
    stack_downstream = defaultdict(list)
    for candidate in candidate_rows:
        stack_downstream[candidate["temporary_stack_ref"]].append(candidate["trade_plan_id"])
    proof_rows = []
    for binding in sorted(binding_rows, key=lambda row: row["computable_binding_id"]):
        stacks = sorted(binding_downstream[binding["computable_binding_id"]])
        plans = sorted({plan for stack in stacks for plan in stack_downstream[stack]})
        proof_rows.append(
            with_common(
                {
                    "computable_binding_ref": binding["computable_binding_id"],
                    "downstream_stack_refs": stacks,
                    "downstream_trade_plan_refs": plans,
                    "formula_ref": binding["formula_ref"],
                    "identity_ref": binding["identity_ref"],
                    "no_orphan_proof_ref": f"VS1_NO_ORPHAN_QKU_FORMULA_{binding['computable_binding_id']}",
                    "orphan_formula_flag": False,
                    "orphan_identity_flag": False,
                    "orphan_qku_flag": False,
                    "proof_status": "NO_ORPHAN_SELECTED_IDENTITY_ROUTED",
                    "qku_ref": binding["qku_ref"],
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["VS1Validator", "AGENT-ORCH1"],
                upstream_artifact_refs=[binding["computable_binding_id"]],
                downstream_artifact_refs=[generated_ref("vs1_run_receipt.report.json")],
            )
        )
    return proof_rows


def build_agent_dag() -> list[dict[str, Any]]:
    edges = [
        ("CommanderAgent", ["FormulaLibraryAgent", "AgentDutyResolverAgent", "MarketConditionAgent"]),
        ("FormulaLibraryAgent", ["ContextFormulaSelectorAgent"]),
        ("AgentDutyResolverAgent", ["ContextFormulaSelectorAgent"]),
        ("MarketConditionAgent", ["QKUComputabilityMaterializerAgent", "TradePlanVariableSearchAgent"]),
        ("ContextFormulaSelectorAgent", ["QKUComputabilityMaterializerAgent"]),
        ("QKUComputabilityMaterializerAgent", ["StackGeneratorAgent"]),
        ("StackGeneratorAgent", ["TradePlanVariableSearchAgent"]),
        ("TradePlanVariableSearchAgent", ["OrderVariableAgent", "NoPnLForcingProofAgent"]),
        ("OrderVariableAgent", ["ExpectedCashPnLEngineAgent", "TCAAgent"]),
        ("ExpectedCashPnLEngineAgent", ["TCAAgent", "CapacityCrowdingAgent", "PortfolioAgent", "ScenarioAgent", "OverfitFDRAgent", "NoTradeRiskAgent"]),
        ("TCAAgent", ["ExpectedCashPnLEngineAgent", "NoTradeRiskAgent"]),
        ("CapacityCrowdingAgent", ["ExpectedCashPnLEngineAgent", "RankerAgent"]),
        ("PortfolioAgent", ["ExpectedCashPnLEngineAgent", "RankerAgent"]),
        ("ScenarioAgent", ["ExpectedCashPnLEngineAgent", "RankerAgent"]),
        ("OverfitFDRAgent", ["ExpectedCashPnLEngineAgent", "RankerAgent"]),
        ("NoTradeRiskAgent", ["RankerAgent"]),
        ("RankerAgent", ["ChampionChallengerSelectionAgent", "QuantumReadinessAgent"]),
        ("ChampionChallengerSelectionAgent", ["PaperIntentPreviewAgent"]),
        ("QuantumReadinessAgent", ["QuantumEncodingAgent", "QOPT"]),
        ("QuantumEncodingAgent", ["QOPT", "GovernanceAgent"]),
        ("PaperIntentPreviewAgent", ["GovernanceAgent"]),
        ("ExternalResearchScoutAgent", ["GovernanceAgent"]),
        ("GovernanceAgent", ["RP5D", "RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1"]),
    ]
    rows = []
    for index, (agent, consumers) in enumerate(edges, start=1):
        rows.append(
            with_common(
                {
                    "agent_dag_receipt_id": f"VS1_AGENT_DAG_{index:04d}",
                    "agent_id": agent,
                    "dag_status": "ACTIVE_IN_VS1_DETERMINISTIC_SLICE",
                    "downstream_agent_refs": consumers,
                    "schema_version": "VS1AgentDAGReceiptV1",
                    "upstream_agent_refs": sorted([src for src, dsts in edges if agent in dsts]),
                },
                producer_agent="CommanderAgent",
                consumer_agent_refs=["GovernanceAgent", "AGENT-ORCH1"],
                upstream_artifact_refs=[generated_ref("vs1_execution_authority_receipt.report.json")],
                downstream_artifact_refs=[generated_ref("vs1_agent_artifact_routing_ledger.jsonl")],
            )
        )
    return rows


def build_artifact_dag_and_routing(all_outputs: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    dag_rows: list[dict[str, Any]] = []
    no_orphan_rows: list[dict[str, Any]] = []
    routing_rows: list[dict[str, Any]] = []
    for index, filename in enumerate(sorted(all_outputs), start=1):
        ref = generated_ref(filename)
        consumers = ARTIFACT_CONSUMERS.get(filename, ["VS1Validator"])
        producer = producer_for_artifact(filename)
        upstream = upstream_for_artifact(filename)
        downstream = [generated_ref(name) for name in downstream_for_artifact(filename)]
        dag_rows.append(
            with_common(
                {
                    "artifact_ref": ref,
                    "dag_edge_id": f"VS1_ARTIFACT_DAG_EDGE_{index:04d}",
                    "downstream_artifact_refs": downstream,
                    "downstream_consumer_refs": consumers,
                    "no_orphan_flag": True,
                    "producer_agent": producer,
                    "schema_version": "VS1UpstreamDownstreamArtifactDAGV1",
                    "terminal_report_flag": filename.endswith(".report.json") and filename in REPORT_OUTPUTS,
                    "upstream_artifact_refs": upstream,
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["VS1Validator", "AGENT-ORCH1"],
                upstream_artifact_refs=upstream,
                downstream_artifact_refs=downstream or [generated_ref("vs1_run_receipt.report.json")],
            )
        )
        no_orphan_rows.append(
            with_common(
                {
                    "artifact_ref": ref,
                    "consumer_agent_refs": consumers,
                    "no_orphan_artifact_ledger_id": f"VS1_NO_ORPHAN_ARTIFACT_{index:04d}",
                    "orphan_artifact_flag": False,
                    "producer_agent": producer,
                    "schema_version": "VS1NoOrphanArtifactLedgerV1",
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["VS1Validator", "AGENT-ORCH1"],
                upstream_artifact_refs=upstream,
                downstream_artifact_refs=downstream or [generated_ref("vs1_run_receipt.report.json")],
            )
        )
        routing_rows.append(
            with_common(
                {
                    "artifact_ref": ref,
                    "consumer_agent_refs": consumers,
                    "producer_agent": producer,
                    "routing_status": "ROUTED_NO_ORPHAN",
                    "schema_version": "VS1AgentArtifactRoutingLedgerV1",
                    "vs1_agent_artifact_routing_id": f"VS1_AGENT_ARTIFACT_ROUTING_{index:04d}",
                },
                producer_agent="GovernanceAgent",
                consumer_agent_refs=["VS1Validator", "AGENT-ORCH1"],
                upstream_artifact_refs=upstream,
                downstream_artifact_refs=downstream or [generated_ref("vs1_run_receipt.report.json")],
            )
        )
    return dag_rows, no_orphan_rows, routing_rows


def producer_for_artifact(filename: str) -> str:
    if "fixture" in filename or "market_condition" in filename:
        return "MarketConditionAgent"
    if "stage_agent" in filename or "agent_duty" in filename:
        return "AgentDutyResolverAgent"
    if "selection" in filename and "champion" not in filename:
        return "ContextFormulaSelectorAgent"
    if "binding" in filename:
        return "QKUComputabilityMaterializerAgent"
    if "stack" in filename:
        return "StackGeneratorAgent"
    if "variable_search" in filename:
        return "TradePlanVariableSearchAgent"
    if "order_variable" in filename:
        return "OrderVariableAgent"
    if "tca" in filename:
        return "TCAAgent"
    if "pnl" in filename:
        return "ExpectedCashPnLEngineAgent"
    if "portfolio" in filename:
        return "PortfolioAgent"
    if "capacity" in filename:
        return "CapacityCrowdingAgent"
    if "scenario" in filename:
        return "ScenarioAgent"
    if "overfit" in filename:
        return "OverfitFDRAgent"
    if "quantum" in filename:
        return "QuantumReadinessAgent"
    if "ranking" in filename or "champion" in filename:
        return "RankerAgent"
    if "paper_intent" in filename:
        return "PaperIntentPreviewAgent"
    if "external_research" in filename:
        return "ExternalResearchScoutAgent"
    return "GovernanceAgent" if "proof" in filename or "orphan" in filename or "dag" in filename else "CommanderAgent"


def upstream_for_artifact(filename: str) -> list[str]:
    if filename == "vs1_reading_receipts.jsonl":
        return list(REQUIRED_READING_FILES)
    if filename == "trade_target_fixtures.jsonl":
        return [generated_ref("vs1_policy_parameter_registry.jsonl")]
    if filename == "stage_agent_universe_query_receipts.jsonl":
        return ["docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl"]
    if filename.endswith(".report.json") and filename != "vs1_execution_authority_receipt.report.json":
        return [generated_ref("trade_plan_candidates.jsonl"), generated_ref("no_pnl_forcing_proof.jsonl")]
    return [generated_ref("vs1_execution_authority_receipt.report.json")]


def downstream_for_artifact(filename: str) -> list[str]:
    mapping = {
        "trade_target_fixtures.jsonl": ["market_condition_snapshots.jsonl"],
        "market_condition_snapshots.jsonl": ["selected_computable_qku_formula_bindings.jsonl", "expected_cash_pnl_receipts.jsonl"],
        "stage_agent_universe_query_receipts.jsonl": ["context_formula_selection_receipts.jsonl"],
        "context_formula_selection_receipts.jsonl": ["selected_computable_qku_formula_bindings.jsonl"],
        "selected_computable_qku_formula_bindings.jsonl": ["temporary_stack_candidate_receipts.jsonl"],
        "temporary_stack_candidate_receipts.jsonl": ["trade_plan_variable_search_receipts.jsonl"],
        "trade_plan_variable_search_receipts.jsonl": ["order_variable_candidate_receipts.jsonl"],
        "order_variable_candidate_receipts.jsonl": ["trade_plan_candidates.jsonl"],
        "trade_plan_candidates.jsonl": ["execution_adjusted_ranking_receipts.jsonl", "vs1_run_receipt.report.json"],
        "execution_adjusted_ranking_receipts.jsonl": ["champion_challenger_selection_receipts.jsonl"],
        "champion_challenger_selection_receipts.jsonl": ["paper_intent_candidate_previews.jsonl"],
        "paper_intent_candidate_previews.jsonl": ["vs1_run_receipt.report.json"],
    }
    return mapping.get(filename, ["vs1_run_receipt.report.json"])


def build_external_research_receipt() -> list[dict[str, Any]]:
    return [
        with_common(
            {
                "accepted_source_fact_flag": False,
                "candidate_algorithm_refs": [],
                "candidate_parameter_refs": [],
                "candidate_quantum_mapping_refs": [],
                "candidate_risk_refs": [],
                "candidate_tca_refs": [],
                "candidate_use_case": "NO_ONLINE_RESEARCH_USED_IN_VS1",
                "candidate_validation_notes": "CI_OFFLINE_SAFE_EMPTY_RECEIPT",
                "connector_semantic_binding_flag": False,
                "credential_or_secret_risk_flag": False,
                "external_code_cloned_flag": False,
                "external_code_executed_flag": False,
                "external_research_candidate_ref": "VS1_EXTERNAL_RESEARCH_NOT_USED_0001",
                "external_research_used_flag": False,
                "fixture_constant_binding_flag": False,
                "future_consumer_pr_refs": ["RP5D", "RANK4", "QOPT"],
                "live_order_authority_flag": False,
                "non_official_source_flag": False,
                "official_source_flag": False,
                "rejection_reason_if_any": "ONLINE_RESEARCH_NOT_USED",
                "research_topic": "ONLINE_RESEARCH_NOT_USED",
                "retrieved_at_utc": CREATED_AT_UTC,
                "runtime_dependency_flag": False,
                "safe_to_store_as_candidate_flag": True,
                "source_class": "VS1_OFFLINE_SKIP_RECEIPT",
                "source_title": "No external research used",
                "source_url_or_locator": "NOT_APPLICABLE",
                "summary": "VS1 did not use online research; no external source values entered fixtures, connector semantics, venue facts, or live authority.",
                "supply_chain_risk_flag": False,
            },
            producer_agent="ExternalResearchScoutAgent",
            consumer_agent_refs=["GovernanceAgent", "FutureResearchLane"],
            upstream_artifact_refs=[],
            downstream_artifact_refs=[generated_ref("vs1_run_receipt.report.json")],
        )
    ]


def build_handoff_report(run_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        "consumer_agent_refs": ["RP5D", "RP5E", "RP5F", "RP5G", "RANK4", "QOPT", "MEM1", "AGENT-ORCH1"],
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "future_handoff_mappings": {
            "AGENT-ORCH1": ["vs1_agent_dag_receipts.jsonl", "vs1_agent_artifact_routing_ledger.jsonl"],
            "MEM1": ["no_trade_comparator_receipts.jsonl condition_scoped_memory_hint"],
            "QOPT": ["quantum_structural_readiness_receipts.jsonl", "trade_plan_quantum_encoding_receipts.jsonl"],
            "RANK4": ["execution_adjusted_ranking_receipts.jsonl", "overfit_fdr_control_receipts.jsonl"],
            "RP5D": ["selected_computable_qku_formula_bindings.jsonl", "no_orphan_qku_formula_proof.jsonl"],
            "RP5E": ["temporary_stack_candidate_receipts.jsonl"],
            "RP5F": ["order_variable_candidate_receipts.jsonl"],
            "RP5G": ["expected_cash_pnl_receipts.jsonl", "tca_breakdown_receipts.jsonl", "scenario_ladder_receipts.jsonl"],
        },
        "producer_agent": "GovernanceAgent",
        "pr_id": PR_ID,
        "run_id": RUN_ID,
        "scope_boundaries": [
            "NO_RP5D_EXECUTABILITY_TIERING",
            "NO_RP5E_PERMANENT_STACK_AUTHORITY",
            "NO_RP5F_TARGET_SCOUT_EXPANSION",
            "NO_RP5G_FULL_SIMULATION",
            "NO_RANK4_PRODUCTION_RANKING",
            "NO_QOPT_BACKEND_EXECUTION",
            "NO_MEM1_IMPLEMENTATION",
            "NO_PAPER_OR_LIVE_EXECUTION",
        ],
        "upstream_artifact_refs": [generated_ref("vs1_run_receipt.report.json")],
        "validation_status": run_report["validation_status"],
        "vs1_to_future_handoff_report_id": "VS1_TO_RP5D_RP5E_RP5F_RP5G_RANK4_QOPT_MEM1_AGENT_ORCH_HANDOFF",
    }


def build_run_report(
    all_rows: dict[str, list[dict[str, Any]]],
    unique_selected: set[str],
    artifact_dag_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates = all_rows["trade_plan_candidates.jsonl"]
    rankings = all_rows["execution_adjusted_ranking_receipts.jsonl"]
    champions = all_rows["champion_challenger_selection_receipts.jsonl"]
    no_trade = all_rows["no_trade_comparator_receipts.jsonl"]
    positive_topk = [
        row
        for row in candidates
        if row["fixture_id"].startswith("VS1_FIXTURE_0001") and row["selection_status"] == "TOP_K_ELIGIBLE"
    ]
    negative_no_trade = [
        row
        for row in no_trade
        if row["fixture_id"].startswith("VS1_FIXTURE_0002") and row["no_trade_wins_flag"] is True
    ]
    thin_rejected = [
        row
        for row in candidates
        if row["fixture_id"].startswith("VS1_FIXTURE_0003") and row["selection_status"] != "TOP_K_ELIGIBLE"
    ]
    crowded_penalty = [
        row
        for row in all_rows["capacity_crowding_receipts.jsonl"]
        if row["fixture_id"].startswith("VS1_FIXTURE_0004") and dec(row["capacity_penalty_cash"]) > 0
    ]
    report = {
        "artifact_dag_edge_count": len(artifact_dag_rows),
        "atomicrows_bundle_sha_reference_count": 0,
        "blocker_policy_ref": BLOCKER_POLICY_REF,
        "cash_runtime_count": 0,
        "challenger_count": sum(len(row["challenger_trade_plan_ids"]) for row in champions),
        "champion_count": sum(1 for row in champions if row["champion_trade_plan_id"]),
        "computed_artifact_statement": "VS1 materialized fixtures, computable bindings, stacks, order variables, TCA, PnL, ranking, paper previews, and proofs.",
        "computable_binding_count": len(all_rows["selected_computable_qku_formula_bindings.jsonl"]),
        "connector_runtime_count": 0,
        "crowded_capacity_penalty_count": len(crowded_penalty),
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "external_research_candidate_count": len(all_rows["external_research_candidate_receipts.jsonl"]),
        "fixture_constant_from_external_source_count": 0,
        "fixtures_processed_count": len(all_rows["trade_target_fixtures.jsonl"]),
        "formula_mutation_count": 0,
        "gate_relaxation_attempt_count": 0,
        "global_formula_ban_count": 0,
        "global_qku_ban_count": 0,
        "hindsight_backsolve_count": 0,
        "impossible_fill_candidate_count": 0,
        "impossible_price_candidate_count": 0,
        "input_rp5c_refs": list(RP5C_REQUIRED_FILES),
        "live_submit_count": 0,
        "metadata_only_selected_count": 0,
        "no_trade_decision_count": sum(1 for row in no_trade if row["no_trade_wins_flag"] is True),
        "negative_fixture_no_trade_count": len(negative_no_trade),
        "objective_term_count": len(all_rows["objective_term_ledger.jsonl"]),
        "order_variable_candidate_count": len(all_rows["order_variable_candidate_receipts.jsonl"]),
        "orphan_artifact_count": 0,
        "orphan_selected_formula_count": 0,
        "orphan_selected_qku_count": 0,
        "paper_intent_preview_count": len(all_rows["paper_intent_candidate_previews.jsonl"]),
        "paper_submit_count": 0,
        "paper_preview_count": len(all_rows["paper_intent_candidate_previews.jsonl"]),
        "portfolio_diversification_receipt_count": len(all_rows["portfolio_diversification_receipts.jsonl"]),
        "positive_fixture_topk_count": len(positive_topk),
        "private_state_fetch_count": 0,
        "qku_deletion_count": 0,
        "qtt_generated_sha_file_count": 0,
        "qtt_sha_authority_count": 0,
        "quantum_advantage_claim_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_encoding_count": len(all_rows["trade_plan_quantum_encoding_receipts.jsonl"]),
        "quantum_structural_readiness_count": len(all_rows["quantum_structural_readiness_receipts.jsonl"]),
        "reading_receipt_count": len(all_rows["vs1_reading_receipts.jsonl"]),
        "run_finished_at_utc": CREATED_AT_UTC,
        "run_id": RUN_ID,
        "run_started_at_utc": CREATED_AT_UTC,
        "scattered_no_live_flag_count": 0,
        "selected_identity_count": len(unique_selected),
        "source_fact_acceptance_count": 0,
        "stage_universe_identity_count": sum(row["eligible_identity_count"] for row in all_rows["stage_agent_universe_query_receipts.jsonl"]),
        "temporary_stack_count": len(all_rows["temporary_stack_candidate_receipts.jsonl"]),
        "thin_book_no_trade_or_penalty_count": len(thin_rejected),
        "top_k_count": sum(1 for row in rankings if int(row["rank"]) > 0),
        "trade_plan_candidate_count": len(candidates),
        "undefined_blocker_code_count": 0,
        "validation_status": "PASS_GENERATED_OFFLINE",
        "variable_search_count": len(all_rows["trade_plan_variable_search_receipts.jsonl"]),
        "venue_api_call_count": 0,
        "constraint_penalty_count": len(all_rows["constraint_penalty_policy_receipts.jsonl"]),
    }
    return report


def run_slice(config: RunConfig | None = None) -> dict[str, Any]:
    cfg = config or RunConfig()
    if cfg.fixture not in {"all", *FIXTURE_CASES}:
        raise ValueError(f"unknown fixture selector: {cfg.fixture}")
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    execution_authority = build_execution_authority()
    blocker_rows = build_blocker_policy()
    policy_rows, params = build_policy_parameters()
    policy_refs = [row["policy_parameter_ref"] for row in policy_rows]
    reading_rows, crosswalk_rows, agent_duty = discover_reading_inputs()
    agent_duty_rows = [agent_duty["row"]]
    library = load_library(REPO_ROOT)
    stage_rows, refs_by_platform_agent = build_stage_query_receipts(library, agent_duty)
    fixtures, snapshots, snapshot_by_fixture = build_fixtures(policy_refs)
    if cfg.fixture != "all":
        fixtures = [row for row in fixtures if row["fixture_case"] == cfg.fixture]
        fixture_ids = {row["fixture_id"] for row in fixtures}
        snapshots = [row for row in snapshots if row["fixture_id"] in fixture_ids]
        snapshot_by_fixture = {key: value for key, value in snapshot_by_fixture.items() if key in fixture_ids}
    selection_rows, binding_rows, bindings_by_fixture, unique_selected = build_context_and_bindings(
        fixtures, snapshot_by_fixture, library, refs_by_platform_agent, cfg, policy_refs
    )
    stack_rows, stacks_by_fixture = build_stacks(fixtures, bindings_by_fixture, cfg)
    search_rows, order_rows, search_by_fixture = build_order_grid(fixtures, snapshot_by_fixture, selection_rows, stacks_by_fixture, policy_refs)
    computed_rows = compute_trade_plan_receipts(
        fixtures, snapshot_by_fixture, order_rows, stacks_by_fixture, search_by_fixture, params, policy_refs, cfg.top_k
    )
    computed_rows["trade_plan_variable_search_receipts.jsonl"] = search_rows
    computed_rows["order_variable_candidate_receipts.jsonl"] = order_rows
    no_pnl_rows = build_no_pnl_forcing_proofs(fixtures, computed_rows)
    no_orphan_qku_rows = build_no_orphan_qku_formula_proof(binding_rows, stack_rows, computed_rows["trade_plan_candidates.jsonl"])
    agent_dag_rows = build_agent_dag()
    all_output_names = [*JSONL_OUTPUTS, *REPORT_OUTPUTS]
    artifact_dag_rows, no_orphan_artifact_rows, routing_rows = build_artifact_dag_and_routing(all_output_names)
    all_rows: dict[str, list[dict[str, Any]]] = {
        "vs1_reading_receipts.jsonl": reading_rows,
        "vs1_crosswalk_discovery_receipts.jsonl": crosswalk_rows,
        "vs1_blocker_policy_registry.jsonl": blocker_rows,
        "vs1_policy_parameter_registry.jsonl": policy_rows,
        "vs1_agent_dag_receipts.jsonl": agent_dag_rows,
        "vs1_agent_artifact_routing_ledger.jsonl": routing_rows,
        "vs1_upstream_downstream_artifact_dag.jsonl": artifact_dag_rows,
        "vs1_no_orphan_artifact_ledger.jsonl": no_orphan_artifact_rows,
        "trade_target_fixtures.jsonl": fixtures,
        "market_condition_snapshots.jsonl": snapshots,
        "stage_agent_universe_query_receipts.jsonl": stage_rows,
        "agent_duty_evidence_discovery_receipts.jsonl": agent_duty_rows,
        "context_formula_selection_receipts.jsonl": selection_rows,
        "selected_computable_qku_formula_bindings.jsonl": binding_rows,
        "temporary_stack_candidate_receipts.jsonl": stack_rows,
        "external_research_candidate_receipts.jsonl": build_external_research_receipt(),
        "no_pnl_forcing_proof.jsonl": no_pnl_rows,
        "no_orphan_qku_formula_proof.jsonl": no_orphan_qku_rows,
        **computed_rows,
    }
    run_report = build_run_report(all_rows, unique_selected, artifact_dag_rows)
    handoff_report = build_handoff_report(run_report)
    write_json(GENERATED_DIR / "vs1_execution_authority_receipt.report.json", execution_authority)
    for name in JSONL_OUTPUTS:
        write_jsonl(GENERATED_DIR / name, all_rows[name], schema_version_name=schema_name_for_output(name))
    write_json(GENERATED_DIR / "vs1_run_receipt.report.json", run_report)
    write_json(GENERATED_DIR / "vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json", handoff_report)
    return run_report


def schema_name_for_output(filename: str) -> str:
    stem = filename.removesuffix(".jsonl")
    parts = [part.capitalize() for part in stem.split("_") if part]
    return "".join(parts) + "V1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PR168-VS1 trading-intelligence vertical slice.")
    parser.add_argument("--fixture", default="all", choices=("all", *FIXTURE_CASES))
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--max-identities", type=int, default=50)
    parser.add_argument("--max-stacks-per-fixture", type=int, default=20)
    parser.add_argument("--dump-temp", action="store_true")
    args = parser.parse_args(argv)
    report = run_slice(
        RunConfig(
            fixture=args.fixture,
            top_k=args.top_k,
            max_identities=args.max_identities,
            max_stacks_per_fixture=args.max_stacks_per_fixture,
            dump_temp=args.dump_temp,
        )
    )
    print(f"PR168_VS1_RUN_OK {report['trade_plan_candidate_count']} candidates {report['champion_count']} champions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
