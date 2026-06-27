"""Shared constants and deterministic JSON helpers for PR168-RP5D."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5d"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_rp5d"

PR_ID = "PR168_RP5D"
BRANCH_NAME = "pr168-rp5d-replay-paper-executability-tiers"
BASELINE_SHA_VCS_METADATA_ONLY = "872139b932ee418ea9b0ae6b089be93a6aece01e"
RUN_ID = "PR168_RP5D_DETERMINISTIC_RUN_20260627T000000Z"
CREATED_AT_UTC = "2026-06-27T00:00:00Z"
REPORT_VERSION = "PR168-RP5D-v1.0"
STAGE_PROFILE_ID = "STAGE1_PREDICTION_MARKETS"
MARKET_FAMILY = "PREDICTION_MARKETS"
EXECUTION_AUTHORITY_REF = "RP5D_EXECUTION_AUTHORITY::COMPUTABILITY_TIERING_ONLY"
BLOCKER_POLICY_REF = "RP5D_BLOCKER_POLICY::PR168_RP5D"
WINDOWS_REPO_ROOT_ASSUMPTION = r"C:\Users\Owner\Projects\QTT_New0526\\"

PLATFORM_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")

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
    "docs/master_plan/generated/rp5c/rp5d_executability_handoff.jsonl",
    "tools/pr168_rp5c_library_reader.py",
    "tools/pr168_rp5c_config.py",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "docs/master_plan/generated/PR168_RP5C_ToRP5DExecutabilityHandoff.report.json",
    "docs/master_plan/generated/PR168_RP5C_ToVS1TradingIntelligenceHandoff.report.json",
    "docs/master_plan/generated/PR168_RP5C_MachineConsumableLibraryAccess.report.json",
    "docs/master_plan/generated/PR168_RP5C_NoGlobalBanProof.report.json",
    "docs/master_plan/generated/PR168_RP5C_NoOrphanIdentityProof.report.json",
    "docs/master_plan/generated/PR168_RP5C_NoOrphanGeneratedSurfaceProof.report.json",
)

VS1_REQUIRED_FILES = (
    "docs/master_plan/generated/pr168_vs1/vs1_reading_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_execution_authority_receipt.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_blocker_policy_registry.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_policy_parameter_registry.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_agent_dag_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_agent_artifact_routing_ledger.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_upstream_downstream_artifact_dag.jsonl",
    "docs/master_plan/generated/pr168_vs1/trade_target_fixtures.jsonl",
    "docs/master_plan/generated/pr168_vs1/market_condition_snapshots.jsonl",
    "docs/master_plan/generated/pr168_vs1/stage_agent_universe_query_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/context_formula_selection_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl",
    "docs/master_plan/generated/pr168_vs1/temporary_stack_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/trade_plan_variable_search_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/order_variable_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/tca_breakdown_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/expected_cash_pnl_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/overfit_fdr_control_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/capacity_crowding_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/portfolio_diversification_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/scenario_ladder_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/objective_term_ledger.jsonl",
    "docs/master_plan/generated/pr168_vs1/constraint_penalty_policy_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/trade_plan_quantum_encoding_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/no_trade_comparator_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/trade_plan_candidates.jsonl",
    "docs/master_plan/generated/pr168_vs1/execution_adjusted_ranking_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/champion_challenger_selection_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/quantum_structural_readiness_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/paper_intent_candidate_previews.jsonl",
    "docs/master_plan/generated/pr168_vs1/external_research_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/no_pnl_forcing_proof.jsonl",
    "docs/master_plan/generated/pr168_vs1/no_orphan_qku_formula_proof.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json",
)

PR165_D2_EXPECTED_FILES = (
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

MASTER_PLAN_EXACT_FILES = ("docs/master_plan/QTT_MasterPlan_Current.md",)
MASTER_PLAN_DISCOVERY_PATTERNS = (
    "docs/master_plan/**/roadmap*",
    "docs/master_plan/**/handoff*",
    "docs/master_plan/**/route*triage*",
    "docs/master_plan/**/crosswalk*",
    "docs/master_plan/**/market*specific*index*",
    "docs/master_plan/**/command*action*matrix*",
    "docs/master_plan/generated/**/rp5d*",
    "docs/master_plan/generated/**/vs1*",
    "docs/master_plan/generated/**/rp5c*",
)

JSONL_OUTPUTS = (
    "rp5d_reading_receipts.jsonl",
    "rp5d_crosswalk_discovery_receipts.jsonl",
    "rp5d_blocker_policy_registry.jsonl",
    "rp5d_comp_state_registry.jsonl",
    "rp5d_exec_state_registry.jsonl",
    "rp5d_adapter_family_registry.jsonl",
    "rp5d_policy_params.jsonl",
    "rp5d_input_inventory.jsonl",
    "rp5d_input_consumption.jsonl",
    "rp5d_rp5c_vs1_crosswalk.jsonl",
    "rp5d_universal_coverage.jsonl",
    "rp5d_stage1_coverage.jsonl",
    "rp5d_comp_materialization.jsonl",
    "rp5d_contract_bundles.jsonl",
    "rp5d_exec_tiers.jsonl",
    "rp5d_computable_universe.jsonl",
    "rp5d_input_queue.jsonl",
    "rp5d_formula_pnl_queue.jsonl",
    "rp5d_unit_queue.jsonl",
    "rp5d_market_data_queue.jsonl",
    "rp5d_tca_queue.jsonl",
    "rp5d_fill_liquidity_queue.jsonl",
    "rp5d_latency_queue.jsonl",
    "rp5d_capacity_queue.jsonl",
    "rp5d_portfolio_queue.jsonl",
    "rp5d_scenario_queue.jsonl",
    "rp5d_overfit_fdr_queue.jsonl",
    "rp5d_no_trade_queue.jsonl",
    "rp5d_rank_queue.jsonl",
    "rp5d_champion_queue.jsonl",
    "rp5d_regime_memory_queue.jsonl",
    "rp5d_alpha_queue.jsonl",
    "rp5d_hot_path_queue.jsonl",
    "rp5d_agent_route_queue.jsonl",
    "rp5d_quantum_map_queue.jsonl",
    "rp5d_classical_fb_queue.jsonl",
    "rp5d_qobj_constraint_ledger.jsonl",
    "rp5d_quantum_compat.jsonl",
    "rp5d_optimizer_readiness.jsonl",
    "rp5d_alpha_readiness.jsonl",
    "rp5d_rank_readiness.jsonl",
    "rp5d_tca_readiness.jsonl",
    "rp5d_overfit_fdr_readiness.jsonl",
    "rp5d_portfolio_readiness.jsonl",
    "rp5d_capacity_readiness.jsonl",
    "rp5d_no_trade_readiness.jsonl",
    "rp5d_champion_readiness.jsonl",
    "rp5d_regime_memory_readiness.jsonl",
    "rp5d_marginal_utility_readiness.jsonl",
    "rp5d_hot_path_readiness.jsonl",
    "rp5d_trade_var_readiness.jsonl",
    "rp5d_agent_exec_resolver.jsonl",
    "rp5d_stage_agent_exec_view.jsonl",
    "rp5d_agent_exec_queries.jsonl",
    "rp5d_agent_dag.jsonl",
    "rp5d_agent_routing_ledger.jsonl",
    "rp5d_artifact_dag.jsonl",
    "rp5d_value_lineage.jsonl",
    "rp5d_no_orphan_artifacts.jsonl",
    "rp5d_no_orphan_qku_formula.jsonl",
    "rp5d_no_mutation_proof.jsonl",
    "rp5d_external_candidates.jsonl",
    "rp5d_external_research.jsonl",
    "rp5d_source_coverage.jsonl",
)

JSON_OUTPUTS = ("rp5d_artifact_name_registry.json",)
REPORT_OUTPUTS = (
    "rp5d_execution_authority.report.json",
    "rp5d_to_rp5e_handoff.report.json",
    "rp5d_future_pr_handoff.report.json",
    "rp5d_live_dryrun_handoff.report.json",
    "rp5d_run_receipt.report.json",
)

OLD_LONG_ARTIFACT_NAMES = (
    "rp5d_quantum_objective_constraint_materialization_ledger.jsonl",
    "rp5d_quantum_executability_compatibility_ledger.jsonl",
    "rp5d_execution_adjusted_ranking_readiness_ledger.jsonl",
    "rp5d_portfolio_diversification_readiness_ledger.jsonl",
    "rp5d_regime_conditioned_memory_readiness_ledger.jsonl",
    "rp5d_future_trade_variable_contract_readiness_ledger.jsonl",
    "rp5d_latency_hot_path_readiness_ledger.jsonl",
    "rp5d_alpha_edge_capture_readiness_ledger.jsonl",
    "rp5d_to_rp5f_rp5g_rank4_qopt_mem1_agent_orch_paper_loop_handoff.report.json",
    "rp5d_to_live_dryrun_future_authority_handoff.report.json",
)

COMPACT_NAME_SEMANTICS = {
    "rp5d_qobj_constraint_ledger.jsonl": "RP5D quantum objective and constraint materialization ledger",
    "rp5d_quantum_compat.jsonl": "RP5D quantum executability compatibility ledger",
    "rp5d_rank_readiness.jsonl": "RP5D execution-adjusted ranking readiness ledger",
    "rp5d_portfolio_readiness.jsonl": "RP5D portfolio diversification readiness ledger",
    "rp5d_regime_memory_readiness.jsonl": "RP5D regime-conditioned memory readiness ledger",
    "rp5d_trade_var_readiness.jsonl": "RP5D future trade-variable contract readiness ledger",
    "rp5d_alpha_readiness.jsonl": "RP5D alpha/edge capture readiness ledger",
    "rp5d_hot_path_readiness.jsonl": "RP5D latency hot-path readiness ledger",
    "rp5d_future_pr_handoff.report.json": "RP5D handoff to RP5F/RP5G/RANK4/QOPT/MEM1/AGENT-ORCH/PAPER-LOOP",
    "rp5d_live_dryrun_handoff.report.json": "RP5D future live-dryrun authority handoff without live authority",
}

OLD_TO_COMPACT_NAME = {
    OLD_LONG_ARTIFACT_NAMES[0]: "rp5d_qobj_constraint_ledger.jsonl",
    OLD_LONG_ARTIFACT_NAMES[1]: "rp5d_quantum_compat.jsonl",
    OLD_LONG_ARTIFACT_NAMES[2]: "rp5d_rank_readiness.jsonl",
    OLD_LONG_ARTIFACT_NAMES[3]: "rp5d_portfolio_readiness.jsonl",
    OLD_LONG_ARTIFACT_NAMES[4]: "rp5d_regime_memory_readiness.jsonl",
    OLD_LONG_ARTIFACT_NAMES[5]: "rp5d_trade_var_readiness.jsonl",
    OLD_LONG_ARTIFACT_NAMES[6]: "rp5d_hot_path_readiness.jsonl",
    OLD_LONG_ARTIFACT_NAMES[7]: "rp5d_alpha_readiness.jsonl",
    OLD_LONG_ARTIFACT_NAMES[8]: "rp5d_future_pr_handoff.report.json",
    OLD_LONG_ARTIFACT_NAMES[9]: "rp5d_live_dryrun_handoff.report.json",
}

COMPUTABILITY_STATES = (
    "COMPUTABLE_REPLAY_PAPER_EXECUTABLE_NOW",
    "COMPUTABLE_AFTER_INPUT_BINDING",
    "COMPUTABLE_AFTER_UNIT_ADAPTER",
    "COMPUTABLE_AFTER_FORMULA_TO_PNL_MAP",
    "COMPUTABLE_AFTER_MARKET_DATA_BINDING",
    "COMPUTABLE_AFTER_TCA_BINDING",
    "COMPUTABLE_AFTER_FILL_LIQUIDITY_BINDING",
    "COMPUTABLE_AFTER_LATENCY_BINDING",
    "COMPUTABLE_AFTER_CAPACITY_CROWDING_BINDING",
    "COMPUTABLE_AFTER_PORTFOLIO_CONTEXT_BINDING",
    "COMPUTABLE_AFTER_SCENARIO_LADDER_BINDING",
    "COMPUTABLE_AFTER_OVERFIT_FDR_BINDING",
    "COMPUTABLE_AFTER_NO_TRADE_COMPARATOR_BINDING",
    "COMPUTABLE_AFTER_RANKING_READINESS_BINDING",
    "COMPUTABLE_AFTER_CHAMPION_CHALLENGER_READINESS_BINDING",
    "COMPUTABLE_AFTER_REGIME_MEMORY_BINDING",
    "COMPUTABLE_AFTER_ALPHA_EDGE_READINESS_BINDING",
    "COMPUTABLE_AFTER_LATENCY_HOT_PATH_BINDING",
    "COMPUTABLE_AFTER_QUANTUM_MAPPING_ADAPTER",
    "COMPUTABLE_AFTER_CLASSICAL_FALLBACK_ADAPTER",
    "MATERIALIZATION_REQUIRED_FROM_EXTERNAL_CANDIDATE",
    "PRESERVED_DUPLICATE_LOW_PRIORITY_WITH_CANONICAL_REF",
    "PRESERVED_OUT_OF_STAGE_DORMANT_WITH_FUTURE_STAGE_ROUTE",
    "PRESERVED_UNSAFE_UNMAPPABLE_WITH_EXACT_REASON",
)

EXECUTABILITY_STATES = (
    "REPLAY_PAPER_EXECUTABLE_NOW",
    "REPLAY_PAPER_SCHEDULABLE_AFTER_ADAPTER",
    "NEEDS_ACTIONABLE_MATERIALIZATION",
    "PRESERVED_NOT_STAGE1_ACTIVE",
    "PRESERVED_DUPLICATE_LOW_PRIORITY",
    "PRESERVED_UNSAFE_UNMAPPABLE_NOT_EXECUTED",
)

BLOCKER_CODES = (
    "RP5D_MATERIALIZE_INPUT_CONTRACT",
    "RP5D_MATERIALIZE_UNIT_CONTRACT",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING",
    "RP5D_MATERIALIZE_TCA_BINDING",
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING",
    "RP5D_MATERIALIZE_LATENCY_BINDING",
    "RP5D_MATERIALIZE_CAPACITY_BINDING",
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING",
    "RP5D_MATERIALIZE_SCENARIO_BINDING",
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING",
    "RP5D_MATERIALIZE_NO_TRADE_BINDING",
    "RP5D_MATERIALIZE_RANKING_READINESS",
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS",
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS",
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS",
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS",
    "RP5D_MATERIALIZE_QUANTUM_MAPPING",
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK",
    "RP5D_MATERIALIZE_EXTERNAL_RESEARCH_CANDIDATE",
    "RP5D_PRESERVE_DUPLICATE_LOW_PRIORITY",
    "RP5D_PRESERVE_OUT_OF_STAGE_DORMANT",
    "RP5D_PRESERVE_UNSAFE_UNMAPPABLE_WITH_REASON",
    "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED",
    "RP5D_NO_DOWNSTREAM_CONSUMER_ACTION_REQUIRED",
    "RP5D_EXTERNAL_SOURCE_FACT_AUTHORITY_BLOCKED",
)

ADAPTER_FAMILIES = (
    "INPUT_CONTRACT_ADAPTER",
    "UNIT_CONTRACT_ADAPTER",
    "FORMULA_TO_PNL_ADAPTER",
    "MARKET_DATA_BINDING_ADAPTER",
    "TCA_COST_ADAPTER",
    "FILL_LIQUIDITY_ADAPTER",
    "LATENCY_STALENESS_ADAPTER",
    "CAPACITY_CROWDING_ADAPTER",
    "PORTFOLIO_CONTEXT_ADAPTER",
    "SCENARIO_LADDER_ADAPTER",
    "OVERFIT_FDR_ADAPTER",
    "NO_TRADE_COMPARATOR_ADAPTER",
    "RANKING_READINESS_ADAPTER",
    "CHAMPION_CHALLENGER_READINESS_ADAPTER",
    "REGIME_MEMORY_ADAPTER",
    "ALPHA_EDGE_READINESS_ADAPTER",
    "LATENCY_HOT_PATH_ADAPTER",
    "AGENT_ROUTE_ADAPTER",
    "QUANTUM_MAPPING_ADAPTER",
    "CLASSICAL_FALLBACK_ADAPTER",
    "EXTERNAL_RESEARCH_CANDIDATE_ADAPTER",
)

BLOCKER_TO_ADAPTER = {
    "RP5D_MATERIALIZE_INPUT_CONTRACT": "INPUT_CONTRACT_ADAPTER",
    "RP5D_MATERIALIZE_UNIT_CONTRACT": "UNIT_CONTRACT_ADAPTER",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP": "FORMULA_TO_PNL_ADAPTER",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING": "MARKET_DATA_BINDING_ADAPTER",
    "RP5D_MATERIALIZE_TCA_BINDING": "TCA_COST_ADAPTER",
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING": "FILL_LIQUIDITY_ADAPTER",
    "RP5D_MATERIALIZE_LATENCY_BINDING": "LATENCY_STALENESS_ADAPTER",
    "RP5D_MATERIALIZE_CAPACITY_BINDING": "CAPACITY_CROWDING_ADAPTER",
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING": "PORTFOLIO_CONTEXT_ADAPTER",
    "RP5D_MATERIALIZE_SCENARIO_BINDING": "SCENARIO_LADDER_ADAPTER",
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING": "OVERFIT_FDR_ADAPTER",
    "RP5D_MATERIALIZE_NO_TRADE_BINDING": "NO_TRADE_COMPARATOR_ADAPTER",
    "RP5D_MATERIALIZE_RANKING_READINESS": "RANKING_READINESS_ADAPTER",
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS": "CHAMPION_CHALLENGER_READINESS_ADAPTER",
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS": "REGIME_MEMORY_ADAPTER",
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS": "ALPHA_EDGE_READINESS_ADAPTER",
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS": "LATENCY_HOT_PATH_ADAPTER",
    "RP5D_MATERIALIZE_QUANTUM_MAPPING": "QUANTUM_MAPPING_ADAPTER",
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK": "CLASSICAL_FALLBACK_ADAPTER",
    "RP5D_MATERIALIZE_EXTERNAL_RESEARCH_CANDIDATE": "EXTERNAL_RESEARCH_CANDIDATE_ADAPTER",
    "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED": "AGENT_ROUTE_ADAPTER",
    "RP5D_EXTERNAL_SOURCE_FACT_AUTHORITY_BLOCKED": "EXTERNAL_RESEARCH_CANDIDATE_ADAPTER",
}

BLOCKER_TO_STATE = {
    "RP5D_MATERIALIZE_INPUT_CONTRACT": "COMPUTABLE_AFTER_INPUT_BINDING",
    "RP5D_MATERIALIZE_UNIT_CONTRACT": "COMPUTABLE_AFTER_UNIT_ADAPTER",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP": "COMPUTABLE_AFTER_FORMULA_TO_PNL_MAP",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING": "COMPUTABLE_AFTER_MARKET_DATA_BINDING",
    "RP5D_MATERIALIZE_TCA_BINDING": "COMPUTABLE_AFTER_TCA_BINDING",
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING": "COMPUTABLE_AFTER_FILL_LIQUIDITY_BINDING",
    "RP5D_MATERIALIZE_LATENCY_BINDING": "COMPUTABLE_AFTER_LATENCY_BINDING",
    "RP5D_MATERIALIZE_CAPACITY_BINDING": "COMPUTABLE_AFTER_CAPACITY_CROWDING_BINDING",
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING": "COMPUTABLE_AFTER_PORTFOLIO_CONTEXT_BINDING",
    "RP5D_MATERIALIZE_SCENARIO_BINDING": "COMPUTABLE_AFTER_SCENARIO_LADDER_BINDING",
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING": "COMPUTABLE_AFTER_OVERFIT_FDR_BINDING",
    "RP5D_MATERIALIZE_NO_TRADE_BINDING": "COMPUTABLE_AFTER_NO_TRADE_COMPARATOR_BINDING",
    "RP5D_MATERIALIZE_RANKING_READINESS": "COMPUTABLE_AFTER_RANKING_READINESS_BINDING",
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS": "COMPUTABLE_AFTER_CHAMPION_CHALLENGER_READINESS_BINDING",
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS": "COMPUTABLE_AFTER_REGIME_MEMORY_BINDING",
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS": "COMPUTABLE_AFTER_ALPHA_EDGE_READINESS_BINDING",
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS": "COMPUTABLE_AFTER_LATENCY_HOT_PATH_BINDING",
    "RP5D_MATERIALIZE_QUANTUM_MAPPING": "COMPUTABLE_AFTER_QUANTUM_MAPPING_ADAPTER",
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK": "COMPUTABLE_AFTER_CLASSICAL_FALLBACK_ADAPTER",
    "RP5D_MATERIALIZE_EXTERNAL_RESEARCH_CANDIDATE": "MATERIALIZATION_REQUIRED_FROM_EXTERNAL_CANDIDATE",
    "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED": "COMPUTABLE_AFTER_INPUT_BINDING",
}

QUEUE_FILE_BY_BLOCKER = {
    "RP5D_MATERIALIZE_INPUT_CONTRACT": "rp5d_input_queue.jsonl",
    "RP5D_MATERIALIZE_FORMULA_TO_PNL_MAP": "rp5d_formula_pnl_queue.jsonl",
    "RP5D_MATERIALIZE_UNIT_CONTRACT": "rp5d_unit_queue.jsonl",
    "RP5D_MATERIALIZE_MARKET_DATA_BINDING": "rp5d_market_data_queue.jsonl",
    "RP5D_MATERIALIZE_TCA_BINDING": "rp5d_tca_queue.jsonl",
    "RP5D_MATERIALIZE_FILL_LIQUIDITY_BINDING": "rp5d_fill_liquidity_queue.jsonl",
    "RP5D_MATERIALIZE_LATENCY_BINDING": "rp5d_latency_queue.jsonl",
    "RP5D_MATERIALIZE_CAPACITY_BINDING": "rp5d_capacity_queue.jsonl",
    "RP5D_MATERIALIZE_PORTFOLIO_BINDING": "rp5d_portfolio_queue.jsonl",
    "RP5D_MATERIALIZE_SCENARIO_BINDING": "rp5d_scenario_queue.jsonl",
    "RP5D_MATERIALIZE_OVERFIT_FDR_BINDING": "rp5d_overfit_fdr_queue.jsonl",
    "RP5D_MATERIALIZE_NO_TRADE_BINDING": "rp5d_no_trade_queue.jsonl",
    "RP5D_MATERIALIZE_RANKING_READINESS": "rp5d_rank_queue.jsonl",
    "RP5D_MATERIALIZE_CHAMPION_CHALLENGER_READINESS": "rp5d_champion_queue.jsonl",
    "RP5D_MATERIALIZE_REGIME_MEMORY_READINESS": "rp5d_regime_memory_queue.jsonl",
    "RP5D_MATERIALIZE_ALPHA_EDGE_READINESS": "rp5d_alpha_queue.jsonl",
    "RP5D_MATERIALIZE_LATENCY_HOT_PATH_READINESS": "rp5d_hot_path_queue.jsonl",
    "RP5D_AGENT_ROUTE_UNRESOLVED_ACTION_REQUIRED": "rp5d_agent_route_queue.jsonl",
    "RP5D_MATERIALIZE_QUANTUM_MAPPING": "rp5d_quantum_map_queue.jsonl",
    "RP5D_MATERIALIZE_CLASSICAL_FALLBACK": "rp5d_classical_fb_queue.jsonl",
}

READINESS_FILES = {
    "alpha_edge": "rp5d_alpha_readiness.jsonl",
    "rank": "rp5d_rank_readiness.jsonl",
    "tca": "rp5d_tca_readiness.jsonl",
    "overfit_fdr": "rp5d_overfit_fdr_readiness.jsonl",
    "portfolio": "rp5d_portfolio_readiness.jsonl",
    "capacity": "rp5d_capacity_readiness.jsonl",
    "no_trade": "rp5d_no_trade_readiness.jsonl",
    "champion": "rp5d_champion_readiness.jsonl",
    "regime_memory": "rp5d_regime_memory_readiness.jsonl",
    "marginal_utility": "rp5d_marginal_utility_readiness.jsonl",
    "hot_path": "rp5d_hot_path_readiness.jsonl",
    "trade_var": "rp5d_trade_var_readiness.jsonl",
}

OPTIMIZER_FAMILIES = (
    "greedy_top_k",
    "beam_search",
    "successive_halving",
    "hyperband",
    "TPE",
    "CMA_ES",
    "differential_evolution",
    "dual_annealing",
    "SHGO",
    "genetic_search",
    "NSGA_II",
    "pareto_frontier",
    "bandit_ucb",
    "thompson_sampling",
    "submodular_selection",
    "QUBO",
    "BQM",
    "CQM",
    "DQM",
    "QuadraticProgram",
    "Ising",
    "QAOA_READY",
    "VQE_READY",
)

REQUIRED_AGENTS = (
    "CommanderAgent",
    "FormulaLibraryAgent",
    "VS1EvidenceAgent",
    "AgentDutyResolverAgent",
    "ComputabilityMaterializerAgent",
    "ExecutabilityTierAgent",
    "InputContractAgent",
    "UnitAdapterAgent",
    "FormulaToPnLAgent",
    "MarketDataBindingAgent",
    "ExecutionCostBindingAgent",
    "PortfolioScenarioRiskBindingAgent",
    "AlphaEdgeReadinessAgent",
    "RankingReadinessAgent",
    "LatencyHotPathReadinessAgent",
    "RegimeMemoryReadinessAgent",
    "QuantumCompatibilityAgent",
    "OptimizerReadinessAgent",
    "AgentExecutableUniverseAgent",
    "ArtifactNameAgent",
    "PathSafetyAgent",
    "ValueLineageAgent",
    "ExternalResearchScoutAgent",
    "GovernanceAgent",
)


@dataclass(frozen=True)
class RunConfig:
    offline: bool = True


def rel_ref(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        p = p.relative_to(REPO_ROOT)
    return p.as_posix()


def generated_ref(filename: str) -> str:
    return f"{GENERATED_REF_PREFIX}/{filename}"


def manifest_name(filename: str) -> str:
    path = Path(filename)
    return f"{path.stem}.manifest.json"


def all_artifact_filenames() -> tuple[str, ...]:
    manifests = tuple(manifest_name(name) for name in JSONL_OUTPUTS)
    return tuple(dict.fromkeys((*JSON_OUTPUTS, *REPORT_OUTPUTS, *JSONL_OUTPUTS, *manifests)))


def dec(value: str | int | float | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def ratio_string(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.000000"
    return str((Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def stable_json(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=None if compact else 2, separators=separators) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, schema_version_name: str) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(stable_json(row, compact=True) for row in materialized), encoding="utf-8")
    manifest = with_common(
        {
            "generated_surface_authority_class": "RP5D_GENERATED_COMPUTABILITY_TIERING_ARTIFACT_NOT_SOURCE_TRUTH",
            "manifest_id": f"{path.stem.upper()}_MANIFEST",
            "physical_filename": rel_ref(path),
            "pr_id": PR_ID,
            "report_version": REPORT_VERSION,
            "row_count": len(materialized),
            "row_count_within_bound_flag": True,
            "schema_version_name": schema_version_name,
            "shard_file_path": rel_ref(path),
        },
        producer_agent="GovernanceAgent",
        consumer_agent_refs=["RP5DValidator", "ArtifactNameAgent", "PathSafetyAgent"],
        upstream_artifact_refs=[generated_ref(path.name)],
        downstream_artifact_refs=[generated_ref("rp5d_run_receipt.report.json")],
    )
    write_json(path.with_name(manifest_name(path.name)), manifest)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stable_unique(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            out.extend(stable_unique(value))
            continue
        text = str(value).strip()
        if text:
            out.append(text)
    return sorted(dict.fromkeys(out), key=lambda item: (item.casefold(), item))


def with_common(
    row: dict[str, Any],
    *,
    producer_agent: str,
    consumer_agent_refs: Iterable[str],
    upstream_artifact_refs: Iterable[str],
    downstream_artifact_refs: Iterable[str],
    validation_refs: Iterable[str] = ("tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",),
    blocker_codes: Iterable[str] = (),
) -> dict[str, Any]:
    out = dict(row)
    out.setdefault("run_id", RUN_ID)
    out.setdefault("execution_authority_ref", EXECUTION_AUTHORITY_REF)
    out.setdefault("blocker_policy_ref", BLOCKER_POLICY_REF)
    out.setdefault("producer_agent", producer_agent)
    out.setdefault("consumer_agent_refs", stable_unique(consumer_agent_refs))
    out.setdefault("upstream_artifact_refs", stable_unique(upstream_artifact_refs))
    out.setdefault("downstream_artifact_refs", stable_unique(downstream_artifact_refs))
    out.setdefault("validation_refs", stable_unique(validation_refs))
    if blocker_codes:
        out.setdefault("blocker_codes", stable_unique(blocker_codes))
    return out
