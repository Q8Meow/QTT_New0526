#!/usr/bin/env python3
"""Central future-expansion registry seed layer for PR168-RANK."""

from __future__ import annotations

from typing import Any

from tools.pr168_rank_report_writer import authority_flags


REGISTRY_NAMES = [
    "MarketAdapterRegistry",
    "VenueCostModelRegistry",
    "ContractPayoffModelRegistry",
    "FormulaPluginRegistrySeed",
    "AlgorithmPluginRegistrySeed",
    "QuantumObjectiveRegistrySeed",
    "OrderPolicyRegistry",
    "AgentCapabilityRegistry",
    "ConnectorReadinessRegistry",
    "RuntimeAllowlistSeedRegistry",
    "HotPathDecisionSurfaceRegistry",
]

REGISTRY_REPORTS = {
    "MarketAdapterRegistry": "PR168_RANK_MarketAdapterRegistrySeed.report.json",
    "VenueCostModelRegistry": "PR168_RANK_VenueCostModelRegistrySeed.report.json",
    "ContractPayoffModelRegistry": "PR168_RANK_ContractPayoffModelRegistrySeed.report.json",
    "FormulaPluginRegistrySeed": "PR168_RANK_FormulaPluginRegistrySeed.report.json",
    "AlgorithmPluginRegistrySeed": "PR168_RANK_AlgorithmPluginRegistrySeed.report.json",
    "QuantumObjectiveRegistrySeed": "PR168_RANK_QuantumObjectiveRegistrySeed.report.json",
    "OrderPolicyRegistry": "PR168_RANK_OrderPolicyRegistry.report.json",
    "AgentCapabilityRegistry": "PR168_RANK_AgentCapabilityRegistrySeed.report.json",
    "ConnectorReadinessRegistry": "PR168_RANK_ConnectorReadinessRegistrySeed.report.json",
    "RuntimeAllowlistSeedRegistry": "PR168_RANK_RuntimeAllowlistSeedRegistry.report.json",
    "HotPathDecisionSurfaceRegistry": "PR168_RANK_HotPathDecisionSurfaceRegistry.report.json",
}


def build_future_expansion_registries(
    *,
    input_summary: dict[str, Any],
    stack_rows: list[dict[str, Any]],
    tournament_rows: list[dict[str, Any]],
    quantum_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    sample_stack = stack_rows[0] if stack_rows else {}
    sample_tournament = tournament_rows[0] if tournament_rows else {}
    sample_quantum = quantum_rows[0] if quantum_rows else {}
    return {
        "MarketAdapterRegistry": [_base_registry_row("MarketAdapterRegistry", "market_adapter_seed", sample_stack, sample_tournament) | _market_adapter_fields()],
        "VenueCostModelRegistry": [_base_registry_row("VenueCostModelRegistry", "venue_cost_model_seed", sample_stack, sample_tournament) | _venue_cost_fields()],
        "ContractPayoffModelRegistry": [_base_registry_row("ContractPayoffModelRegistry", "contract_payoff_model_seed", sample_stack, sample_tournament) | _payoff_fields()],
        "FormulaPluginRegistrySeed": [_base_registry_row("FormulaPluginRegistrySeed", "formula_plugin_seed", sample_stack, sample_tournament) | _plugin_fields("FORMULA", sample_stack)],
        "AlgorithmPluginRegistrySeed": [_base_registry_row("AlgorithmPluginRegistrySeed", "algorithm_plugin_seed", sample_stack, sample_tournament) | _plugin_fields("ALGORITHM", sample_stack)],
        "QuantumObjectiveRegistrySeed": [_base_registry_row("QuantumObjectiveRegistrySeed", "quantum_objective_seed", sample_stack, sample_tournament) | _quantum_fields(sample_quantum)],
        "OrderPolicyRegistry": _order_policy_rows(sample_stack, sample_tournament),
        "AgentCapabilityRegistry": _agent_capability_rows(),
        "ConnectorReadinessRegistry": [_base_registry_row("ConnectorReadinessRegistry", "connector_readiness_seed", sample_stack, sample_tournament) | _connector_fields()],
        "RuntimeAllowlistSeedRegistry": [_base_registry_row("RuntimeAllowlistSeedRegistry", "runtime_allowlist_seed", sample_stack, sample_tournament) | _runtime_allowlist_fields(input_summary, sample_stack)],
        "HotPathDecisionSurfaceRegistry": [_base_registry_row("HotPathDecisionSurfaceRegistry", "hot_path_surface_seed", sample_stack, sample_tournament) | _hot_path_fields(sample_stack)],
    }


def build_registry_layer_rows(registries: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, registry_rows in sorted(registries.items()):
        rows.append(
            {
                "artifact_id": f"PR168_RANK_REGISTRY_LAYER::{name}",
                "registry_name": name,
                "registry_report_ref": REGISTRY_REPORTS[name],
                "registry_row_count": len(registry_rows),
                "owning_agent": "GovernanceAgent",
                "downstream_consumers": _downstream_consumers_for(name),
                "downstream_pr_refs": _downstream_prs_for(name),
                "no_orphan_status": "CONNECTED_TO_REGISTRY_CONSUMER",
                "authority_boundary_flags": authority_flags(),
                "upstream_numeric_evidence_refs": _flatten_refs(registry_rows, "upstream_numeric_evidence_refs"),
                "upstream_gap_refs": _flatten_refs(registry_rows, "upstream_gap_refs"),
            }
        )
    return rows


def _base_registry_row(
    registry_name: str,
    row_suffix: str,
    stack: dict[str, Any],
    tournament: dict[str, Any],
) -> dict[str, Any]:
    return {
        "registry_row_id": f"PR168_RANK::{registry_name}::{row_suffix}",
        "registry_name": registry_name,
        "registry_class": registry_name,
        "registry_status": "SEED_CONTRACT_ONLY",
        "market_scope": "prediction_market_stage1",
        "venue_scope": "venue_candidate_only_not_bound",
        "mode_scope": ["REPLAY", "PAPER", "SHADOW_CANDIDATE", "LIVE_CANDIDATE_SEED", "FUTURE_LIVE_HOT_PATH_SEED"],
        "qku_refs": stack.get("qku_refs", []),
        "formula_refs": stack.get("formula_refs", []),
        "algorithm_refs": stack.get("algorithm_refs", []),
        "quantum_objective_refs": stack.get("quantum_structural_optimizer_refs_when_applicable", []),
        "order_policy_refs": stack.get("order_policy_refs", []),
        "candidate_stack_refs": [stack.get("candidate_stack_id")] if stack.get("candidate_stack_id") else [],
        "simulated_order_refs": [tournament.get("winning_source_candidate_id")] if tournament.get("winning_source_candidate_id") else [],
        "upstream_numeric_evidence_refs": tournament.get("upstream_numeric_evidence_refs", []),
        "upstream_gap_refs": tournament.get("selection_reason_codes", []),
        "source_evidence_status": "NOT_ACCEPTED_IN_THIS_PR",
        "connector_binding_status": "NOT_BOUND_IN_THIS_PR",
        "private_state_required_flag": False,
        "cash_required_flag": False,
        "order_authority_required_flag": False,
        "live_execution_allowed_flag": False,
        "quantum_backend_required_flag": False,
        "quantum_advantage_claim_flag": False,
        "owning_agent": "GovernanceAgent",
        "supporting_agents": ["RankingAgent", "RiskAgent", "DashboardAgent"],
        "downstream_consumers": _downstream_consumers_for(registry_name),
        "downstream_pr_refs": _downstream_prs_for(registry_name),
        "validator_refs": [f"tools/validate_pr168_rank_{_validator_name(registry_name)}.py"],
        "test_refs": [f"tests/pr168_rank/test_{_validator_name(registry_name)}.py"],
        "no_orphan_status": "CONNECTED_TO_REGISTRY_CONSUMER",
        "authority_boundary_flags": authority_flags(),
        "reason_codes": ["REGISTRY_SEED_CONTRACT_ONLY", "NO_FORBIDDEN_AUTHORITY_CREATED"],
        "manual_edit_allowed_flag": False,
    }


def _market_adapter_fields() -> dict[str, Any]:
    return {
        "market_adapter_id": "MARKET_ADAPTER_SEED::PREDICTION_MARKET_STAGE1",
        "adapter_contract_class": "PREDICTION_MARKET_BINARY_SEED",
        "supported_contract_types": ["BINARY_YES_NO"],
        "supported_sides": ["YES", "NO"],
        "supported_order_policy_refs": ["OrderPolicyRegistry"],
        "payoff_model_registry_ref": "ContractPayoffModelRegistry",
        "venue_cost_model_registry_ref": "VenueCostModelRegistry",
        "source_evidence_required_fields": ["market_id", "side", "execution_price", "fill_probability"],
        "connector_readiness_registry_ref": "ConnectorReadinessRegistry",
        "replay_supported_flag": True,
        "paper_supported_flag": True,
        "shadow_candidate_supported_flag": True,
        "live_candidate_seed_supported_flag": True,
        "adapter_runtime_implemented_in_this_PR": False,
    }


def _venue_cost_fields() -> dict[str, Any]:
    return {
        "venue_cost_model_id": "VENUE_COST_MODEL_SEED::PREDICTION_MARKET_STAGE1",
        "explicit_fee_model_ref": "explicit_fees",
        "spread_crossing_model_ref": "spread_crossing_cost",
        "expected_slippage_model_ref": "expected_slippage",
        "adverse_selection_model_ref": "adverse_selection_cost",
        "latency_decay_model_ref": "latency_decay_cost",
        "book_depth_or_market_impact_model_ref": "market_impact_or_book_depth_cost",
        "failed_fill_or_cancel_cost_model_ref": "failed_fill_or_cancel_cost",
        "settlement_or_resolution_cost_proxy_ref": "settlement_or_resolution_cost_proxy",
        "capital_lock_cost_model_ref": "capital_lock_cost",
        "model_numeric_evidence_refs": ["PR168_RP_TCADecomposition.report.json"],
        "missing_component_gap_refs": [],
    }


def _payoff_fields() -> dict[str, Any]:
    return {
        "payoff_model_id": "PAYOFF_MODEL_SEED::BINARY_YES_NO",
        "contract_type": "BINARY_YES_NO",
        "side_set": ["YES", "NO"],
        "payout_currency_or_unit_status": "UNIT_INTERVAL_PAYOFF_ONLY_NOT_VENUE_BOUND",
        "payoff_win_formula": "p_win * 1.0",
        "payoff_loss_formula": "(1 - p_win) * 0.0",
        "settlement_value_formula_ref": "PR168_RANK_BINARY_PREDICTION_MARKET_PNL",
        "binary_yes_no_supported_flag": True,
        "non_binary_status": "SEED_ONLY_OR_GAP_ROUTED",
        "source_evidence_required_before_connector_binding": True,
        "numeric_smoke_test_refs": ["tests/pr168_rank/test_binary_prediction_market_pnl.py"],
    }


def _plugin_fields(kind: str, stack: dict[str, Any]) -> dict[str, Any]:
    return {
        "plugin_seed_id": f"{kind}_PLUGIN_SEED::PR168_RANK",
        "plugin_kind": kind,
        "formula_or_algorithm_ref": (stack.get("formula_refs") or stack.get("algorithm_refs") or ["GAP_ROUTED"])[0],
        "role_in_candidate_stack": "ranking_component",
        "input_schema_refs": ["PR168_RANK_CandidateStackRoleCompletenessAudit.report.json"],
        "output_schema_refs": ["PR168_RANK_EvidenceBackedRanking.report.json"],
        "numeric_evidence_refs": stack.get("upstream_numeric_evidence_refs", []),
        "test_vector_required_flag": True,
        "replay_queue_candidate_flag": True,
        "paper_queue_candidate_flag": True,
        "shadow_candidate_flag": True,
        "live_candidate_allowed_in_this_PR": False,
        "live_execution_allowed_in_this_PR": False,
        "promotion_state_seed": "REPAIR_REQUIRED",
        "versioning_needed_flag": True,
        "rollback_needed_flag": True,
        "owner_or_agent_intake_consumer_pr": "PR162E",
    }


def _quantum_fields(quantum: dict[str, Any]) -> dict[str, Any]:
    missing = quantum.get("missing_quantum_inputs", []) or ["objective_coefficients_constraints_interpret_back_gap"]
    return {
        "quantum_objective_seed_id": "QUANTUM_OBJECTIVE_SEED::STACK_POLICY_SIZE_RECOVERY",
        "objective_sense": "MAXIMIZE",
        "objective_terms": ["stack_utility", "tca_penalty", "overfit_penalty", "capacity_penalty"],
        "linear_coefficients": {},
        "quadratic_coefficients": {},
        "variable_map": {},
        "variable_domains": {},
        "constraint_map": {},
        "penalty_weight_map": {},
        "mapping_status_QUBO_BQM_Ising_CQM_DQM_QuadraticProgram": "GAP_ROUTED_STRUCTURAL_ONLY",
        "interpret_back_map_ref": "PR168_RANK_QuantumSelectorInterpretBackMap.report.json",
        "classical_fallback_ref": "PR168_RANK_QuantumClassicalComparatorQueue.report.json",
        "classical_comparator_ref": "PR168_RP_StrongestClassicalComparatorMap.report.json",
        "smoke_test_ref": "tests/pr168_rank/test_quantum_objective_registry_seed.py",
        "missing_quantum_component_gap_refs": missing,
        "backend_execution_required_flag": False,
        "quantum_advantage_claim_flag": False,
    }


def _order_policy_rows(stack: dict[str, Any], tournament: dict[str, Any]) -> list[dict[str, Any]]:
    policies = [
        ("NO_TRADE", "NO_TRADE"),
        ("PASSIVE_LIMIT", "PASSIVE_LIMIT"),
        ("BEST_LIMIT", "BEST_LIMIT"),
        ("REPRICE", "REPRICE"),
        ("AGGRESSIVE_CROSS", "AGGRESSIVE_CROSS"),
        ("SPLIT_ORDER", "SPLIT_ORDER"),
        ("CANCEL_EXPIRE", "CANCEL_EXPIRE"),
        ("RETEST", "RETEST"),
        ("REPAIR", "REPAIR"),
    ]
    rows = []
    for policy_name, policy_class in policies:
        rows.append(
            _base_registry_row("OrderPolicyRegistry", policy_name.lower(), stack, tournament)
            | {
                "order_policy_registry_id": f"ORDER_POLICY::{policy_name}",
                "policy_name": policy_name,
                "policy_class": policy_class,
                "allowed_modes": ["REPLAY", "PAPER", "SHADOW_CANDIDATE", "LIVE_CANDIDATE_SEED", "FUTURE_LIVE_HOT_PATH_SEED"],
                "required_numeric_inputs": ["price", "quantity", "fill_probability", "TCA_components", "latency_budget"],
                "expected_output_fields": ["fill_adjusted_expected_pnl", "lcb_edge", "no_trade_margin"],
                "TCA_component_refs": ["VenueCostModelRegistry"],
                "fill_model_refs": ["PR168_RP_FillQueueLatencyResults.report.json"],
                "latency_model_refs": ["PR168_RP_LatencyBudgetResults.report.json"],
                "risk_boundary_flags": authority_flags(),
                "simulated_only_in_this_PR": True,
                "live_execution_allowed_flag": False,
            }
        )
    return rows


def _agent_capability_rows() -> list[dict[str, Any]]:
    agents = [
        "RankingAgent",
        "RiskAgent",
        "ExecutionCostAgent",
        "FillModelAgent",
        "CapacityAgent",
        "CalibrationAgent",
        "QuantumMapperAgent",
        "PortfolioAgent",
        "DashboardAgent",
        "OwnerReviewAgent",
        "ConnectorCandidateAgent",
        "GovernanceAgent",
        "QKUResearchAgent",
        "FormulaExecutionAgent",
        "ReplayPaperReviewAgent",
    ]
    return [
        _base_registry_row("AgentCapabilityRegistry", agent.lower(), {}, {})
        | {
            "agent_capability_id": f"AGENT_CAPABILITY::{agent}",
            "agent_name": agent,
            "capability_class": "PR168_RANK_NONLIVE_DECISION_QUALITY",
            "source_agent_roster_ref": "PR165_D2_AgentRosterDiscoveryAudit.report.json",
            "source_duty_crosswalk_ref": "PR165_D2_AgentDutySourceCrosswalk.report.json",
            "input_report_classes": ["PR168_RP_COMPUTED_EVIDENCE", "PR168_RANK_REGISTRY_SEED"],
            "output_report_classes": ["PR168_RANK_WORK_ORDER", "PR168_RANK_REGISTRY_SEED"],
            "quality_metric_refs": ["PR168_RANK_ScoreComponentLedger.report.json"],
            "failure_route": "PR168_RANK_RepairPriorityQueue.report.json",
            "supported_modes": ["REPLAY", "PAPER", "SHADOW_CANDIDATE", "LIVE_CANDIDATE_SEED"],
            "forbidden_authority_flags": authority_flags(),
            "replacement_or_new_agent_proposal_allowed_flag": False,
        }
        for agent in agents
    ]


def _connector_fields() -> dict[str, Any]:
    return {
        "connector_readiness_id": "CONNECTOR_READINESS_SEED::PREDICTION_MARKET_STAGE1",
        "connector_or_venue_scope": "venue_candidate_only_not_bound",
        "field_or_semantic_needed": "market_id/side/price/quantity/fill/cost semantics",
        "why_needed_for_decision_quality": "future connector binding must preserve computed decision-quality inputs",
        "source_evidence_required_flag": True,
        "source_truth_status": "NOT_ACCEPTED_IN_THIS_PR",
        "connector_binding_status": "NOT_BOUND_IN_THIS_PR",
        "private_state_required_flag": False,
        "cash_required_flag": False,
        "order_authority_required_flag": False,
        "future_consumer_pr": "source_evidence_or_connector_binding_future_pr",
        "responsible_agent": "ConnectorCandidateAgent",
    }


def _runtime_allowlist_fields(input_summary: dict[str, Any], stack: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_allowlist_seed_id": "RUNTIME_ALLOWLIST_SEED::PR168_RANK",
        "formula_refs": stack.get("formula_refs", []),
        "algorithm_refs": stack.get("algorithm_refs", []),
        "candidate_stack_refs": [stack.get("candidate_stack_id")] if stack.get("candidate_stack_id") else [],
        "allowed_future_modes": ["RESEARCH", "REPLAY", "PAPER", "SHADOW_CANDIDATE", "LIVE_CANDIDATE_SEED", "FUTURE_LIVE_HOT_PATH_SEED"],
        "live_execution_allowed_in_this_PR": False,
        "promotion_evidence_refs": input_summary.get("upstream_report_refs", []),
        "missing_receipt_refs": input_summary.get("missing_required_reports", []),
        "rollback_required_flag": True,
        "cacheability_class": "SEED_ONLY_PRECOMPUTED_SURFACE",
        "compute_budget_class": "SLOW_RESEARCH_NOT_HOT_PATH",
        "consumer_pr": "RuntimeFormulaAllowlistHotPathCachePR",
    }


def _hot_path_fields(stack: dict[str, Any]) -> dict[str, Any]:
    return {
        "hot_path_surface_id": "HOT_PATH_SURFACE_SEED::PR168_RANK",
        "candidate_stack_id": stack.get("candidate_stack_id"),
        "surface_ref": "PR168_RANK_OrderDecisionSurfaceLookupSeed.report.json",
        "surface_dimension_refs": ["price_grid", "quantity_grid", "latency_bucket", "regime_bucket"],
        "surface_output_refs": ["no_trade_region", "repair_region", "terminal_region"],
        "cacheability_class": "SEMANTIC_KEY_SEED_ONLY",
        "refresh_class": "RECOMPUTE_BY_RESEARCH_PIPELINE",
        "semantic_cache_key_inputs_without_hash_authority": ["candidate_stack_id", "mode_scope", "regime_bucket"],
        "cache_invalidation_triggers_without_SHA_authority": ["new_PR168_RP_evidence", "policy_threshold_change"],
        "future_hot_path_allowed_flag": "seed_only",
        "full_research_recompute_allowed_on_future_hot_path": False,
        "consumer_pr": "RuntimeFormulaAllowlistHotPathCachePR",
    }


def _downstream_consumers_for(registry_name: str) -> list[str]:
    if "Quantum" in registry_name:
        return ["QuantumMapperAgent", "QuantumComparatorAgent"]
    if "Connector" in registry_name:
        return ["ConnectorCandidateAgent", "GovernanceAgent"]
    if "Runtime" in registry_name or "HotPath" in registry_name:
        return ["FormulaExecutionAgent", "OwnerReviewAgent"]
    return ["RankingAgent", "DashboardAgent", "GovernanceAgent"]


def _downstream_prs_for(registry_name: str) -> list[str]:
    if "Plugin" in registry_name:
        return ["PR162E", "PR162F"]
    if "Quantum" in registry_name:
        return ["PR162E-Q", "PR166-QC-R2"]
    if "Connector" in registry_name or "MarketAdapter" in registry_name or "Venue" in registry_name:
        return ["FutureMarketVenueAdapterExpansionPR"]
    if "Runtime" in registry_name or "HotPath" in registry_name:
        return ["RuntimeFormulaAllowlistHotPathCachePR"]
    return ["OwnerDashboardComputedTruthPR"]


def _validator_name(registry_name: str) -> str:
    mapping = {
        "MarketAdapterRegistry": "market_adapter_registry_seed",
        "VenueCostModelRegistry": "venue_cost_model_registry_seed",
        "ContractPayoffModelRegistry": "contract_payoff_model_registry_seed",
        "FormulaPluginRegistrySeed": "formula_algorithm_plugin_registry_seed",
        "AlgorithmPluginRegistrySeed": "formula_algorithm_plugin_registry_seed",
        "QuantumObjectiveRegistrySeed": "quantum_objective_registry_seed",
        "OrderPolicyRegistry": "order_policy_registry_seed",
        "AgentCapabilityRegistry": "agent_capability_registry_seed",
        "ConnectorReadinessRegistry": "connector_readiness_registry_seed",
        "RuntimeAllowlistSeedRegistry": "runtime_allowlist_seed_registry",
        "HotPathDecisionSurfaceRegistry": "hot_path_decision_surface_registry",
    }
    return mapping[registry_name]


def _flatten_refs(rows: list[dict[str, Any]], key: str) -> list[Any]:
    refs: list[Any] = []
    for row in rows:
        value = row.get(key, [])
        if isinstance(value, list):
            refs.extend(value)
        elif value:
            refs.append(value)
    return sorted(dict.fromkeys(str(ref) for ref in refs if ref not in (None, "")))[:20]
