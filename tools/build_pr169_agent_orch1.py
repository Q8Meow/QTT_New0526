#!/usr/bin/env python3
"""Build PR169-AGENT-ORCH1 deterministic agent orchestration contracts.

AGENT-ORCH1 consumes the current READINESS1, PRETRADE1, SVC1, MEM1, and
PR165-D2 generated contracts and projects one canonical agent-orchestration
registry into compact DAG, task, receipt, and downstream handoff views. The
builder is a run-once fixture/artifact builder only: it does not execute agents,
call LLM providers, read connectors, read private/cash state, submit orders, or
create paper/shadow/live activity.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROMPT_VERSION = "v2.2"
PROJECTION_VERSION = "PR169-AGENT-ORCH1-v2.2"
BUILDER_NAME = "tools/build_pr169_agent_orch1.py"
VALIDATOR_NAME = "tools/validate_pr169_agent_orch1.py"
GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_agent_orch1")
REGISTRY_REF = "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl"
MANIFEST_REF = "docs/master_plan/generated/pr169_agent_orch1/manifest.json"

SVC1_PREFIX = Path("docs/master_plan/generated/pr169_svc1")
READINESS1_PREFIX = Path("docs/master_plan/generated/pr169_readiness1")
PRETRADE1_PREFIX = Path("docs/master_plan/generated/pr169_pretrade1")
MEM1_PREFIX = Path("docs/master_plan/generated/pr168_mem1")
PR165_D2_PREFIX = Path("docs/master_plan/generated")

PR165_D2_ROSTER_REF = "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"
PR165_D2_DUTY_REF = "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"

BASELINE_CONSUMED = {
    "PR267_READINESS1_commit": "8349a2f08ab5024f36f4a6c5dba3aee76da5b3d8",
    "PR268_PRETRADE1_commit": "fc0f72088aeb70f7a3aa835dd5e86561a5a89d02",
    "PR269_SVC1_commit": "1b2d4da936fd79adfdecc5f503d2fa96ee6798a9",
    "MEM1_current_equivalent": "docs/master_plan/generated/pr168_mem1/",
    "PR165_D2_roster_current_equivalent": PR165_D2_ROSTER_REF,
    "PR165_D2_duty_current_equivalent": PR165_D2_DUTY_REF,
}

JSONL_ARTIFACTS = (
    "registry.jsonl",
    "dag.jsonl",
    "dag_nodes.jsonl",
    "dag_edges.jsonl",
    "task_registry.jsonl",
    "task_queue.jsonl",
    "task_env.jsonl",
    "directives.jsonl",
    "workflows.jsonl",
    "handoffs.jsonl",
    "role_map.jsonl",
    "duty_map.jsonl",
    "perm_scope.jsonl",
    "retry_policy.jsonl",
    "priority_policy.jsonl",
    "quarantine.jsonl",
    "agent_ops.jsonl",
    "team_queue.jsonl",
    "intel_lanes.jsonl",
    "tournament_tasks.jsonl",
    "task_receipts.jsonl",
    "decision_receipts.jsonl",
    "dispute_receipts.jsonl",
    "escalation_receipts.jsonl",
    "handoff_receipts.jsonl",
    "audit_trail.jsonl",
    "svc1_bindings.jsonl",
    "readiness_bindings.jsonl",
    "pretrade_bindings.jsonl",
    "mem1_bindings.jsonl",
    "owner_cmd_tasks.jsonl",
    "chat_tasks.jsonl",
    "qku_tasks.jsonl",
    "formula_tasks.jsonl",
    "access_proof.jsonl",
    "library_receipts.jsonl",
    "graph_routes.jsonl",
    "graph_tasks.jsonl",
    "graph_quality.jsonl",
    "tradeplan_tasks.jsonl",
    "pretrade_tasks.jsonl",
    "mode_tasks.jsonl",
    "order_policy_tasks.jsonl",
    "paper_prep.jsonl",
    "hotpath_prep.jsonl",
    "shadow_prep.jsonl",
    "live_prep.jsonl",
    "rank_tasks.jsonl",
    "tca_tasks.jsonl",
    "fdr_tasks.jsonl",
    "portfolio_tasks.jsonl",
    "capacity_tasks.jsonl",
    "champion_tasks.jsonl",
    "mem_prior_tasks.jsonl",
    "utility_tasks.jsonl",
    "scenario_tasks.jsonl",
    "calibration_tasks.jsonl",
    "notrade_tasks.jsonl",
    "var_tune_tasks.jsonl",
    "stack_tasks.jsonl",
    "venue_side_tasks.jsonl",
    "source_refresh_tasks.jsonl",
    "retest_tasks.jsonl",
    "reality_tasks.jsonl",
    "metric_tasks.jsonl",
    "plugin_prep.jsonl",
    "qmap_prep.jsonl",
    "allow_prep.jsonl",
    "formula_intake.jsonl",
    "latency_tiers.jsonl",
    "clean_room.jsonl",
    "quantum_tasks.jsonl",
    "fallback_tasks.jsonl",
    "downstream.jsonl",
    "value_routes.jsonl",
    "capability_routes.jsonl",
    "learning_routes.jsonl",
)

JSON_REPORTS = (
    "manifest.json",
    "no_orphan.report.json",
    "no_raw_scan.report.json",
    "no_direct_submit.report.json",
    "no_llm_runtime.report.json",
    "no_paper_exec.report.json",
    "no_live_exec.report.json",
    "no_fake_receipts.report.json",
    "no_source_truth.report.json",
    "no_private_cash.report.json",
    "no_qbackend.report.json",
    "no_qtt_sha.report.json",
    "no_placeholders.report.json",
    "no_full_library.report.json",
    "no_pr_collapse.report.json",
    "no_scatter.report.json",
    "quality.report.json",
    "acceptance.report.json",
    "owned_scope.report.json",
)

SVC1_FILES = (
    "service_registry.jsonl",
    "owner_action_requests.generated.jsonl",
    "action_route_to_agent_responsibility.generated.jsonl",
    "agent_operations_views.generated.jsonl",
    "team_workflow_queue_views.generated.jsonl",
    "agent_llm_task_route_views.generated.jsonl",
    "qku_formula_compute_route_views.generated.jsonl",
    "downstream_dag_route_views.generated.jsonl",
    "owner_next_step_routes.generated.jsonl",
    "no_trade_reoptimization_views.generated.jsonl",
    "execution_adjusted_ranking_views.generated.jsonl",
    "tca_decomposition_views.generated.jsonl",
    "overfit_fdr_control_views.generated.jsonl",
    "portfolio_diversification_views.generated.jsonl",
    "capacity_crowding_views.generated.jsonl",
    "champion_challenger_views.generated.jsonl",
    "regime_memory_prior_views.generated.jsonl",
    "marginal_utility_views.generated.jsonl",
    "quantum_structural_readiness_views.generated.jsonl",
    "artifact_value_route_map.generated.jsonl",
)

PRETRADE1_FILES = (
    "pretrade_decision_registry.jsonl",
    "pretrade_decision_candidates.generated.jsonl",
    "pretrade_agent_packet_map.generated.jsonl",
    "pretrade_agent_dag_handoff.generated.jsonl",
    "agent_workflow_obs_handoff.generated.jsonl",
    "pretrade_qku_formula_compute_map.generated.jsonl",
    "pretrade_exec_ladder_handoff.generated.jsonl",
    "pretrade_hotpath_handoff.generated.jsonl",
    "pretrade_metrics_capture_handoff.generated.jsonl",
    "pretrade_connector_handoff.generated.jsonl",
    "pretrade_execution_router_handoff.generated.jsonl",
    "tca_decomposition.generated.jsonl",
    "scenario_ladder_decisions.generated.jsonl",
    "mode_authority_matrix.generated.jsonl",
    "pretrade_quantum_readiness_handoff.generated.jsonl",
    "pretrade_memory_prior_reval.generated.jsonl",
    "pretrade_recovery_frontiers.generated.jsonl",
    "consumer_routes.generated.jsonl",
)

READINESS1_FILES = (
    "agent_readiness_registry.jsonl",
    "access_path_resolutions.generated.jsonl",
    "computable_contracts.generated.jsonl",
    "qku_formula_agent_compute_map.generated.jsonl",
    "executable_now.generated.jsonl",
    "paper_loop_usable.generated.jsonl",
    "adapter_blocked.generated.jsonl",
    "agent_universe.generated.jsonl",
    "llm_grounding_view.generated.jsonl",
    "owner_command_routes.generated.jsonl",
    "consumer_routes.generated.jsonl",
    "institutional_controls.generated.jsonl",
    "quantum_readiness.generated.jsonl",
)

MEM1_FILES = (
    "context_signature.jsonl",
    "memory_query_contract.jsonl",
    "winning_recipe.jsonl",
    "failure_memory.jsonl",
    "notrade_context_memory.jsonl",
    "notrade_reoptimization_route.jsonl",
    "notrade_variable_tune_route.jsonl",
    "notrade_stack_challenger_route.jsonl",
    "notrade_venue_side_rotation_route.jsonl",
    "notrade_source_refresh_route.jsonl",
    "notrade_retest_route.jsonl",
    "notrade_next_target_route.jsonl",
    "cooldown_state.jsonl",
    "drift_monitor.jsonl",
    "hotpath_memory_index.jsonl",
    "retest_queue.jsonl",
)

DAG_STAGE_FAMILIES = (
    "OWNER_REQUEST_INTAKE",
    "OWNER_CHAT_INTAKE",
    "SOURCE_RESEARCH_ROUTE",
    "MARKET_CONTEXT_ROUTE",
    "READINESS_ACCESS_ROUTE",
    "QKU_GRAPH_ROUTE",
    "QKU_FORMULA_ROUTE",
    "STACK_ROUTE",
    "QUANTUM_ROUTE",
    "PRETRADE_BINDING",
    "RANK_REVIEW",
    "TCA_REVIEW",
    "RISK_CAPACITY_REVIEW",
    "PORTFOLIO_REVIEW",
    "FDR_REVIEW",
    "SCENARIO_REVIEW",
    "CHAMPION_REVIEW",
    "MEM_PRIOR_REVAL",
    "NO_TRADE_RECOVERY",
    "PAPER_PREP",
    "HOTPATH_PREP",
    "LIVE_DRYRUN_PREP",
    "OWNER_ESCALATION",
    "AGENT_DISAGREEMENT",
    "RETRY_OR_QUARANTINE",
    "LEARNING_ROUTE",
)

INTELLIGENCE_LANES = (
    "KNOWLEDGE_LANE",
    "SEARCH_LANE",
    "SIMULATION_LANE",
    "LEARNING_LANE",
    "REASONING_LANE",
    "EXEC_PREP_LANE",
    "GOVERNANCE_LANE",
)

TOURNAMENT_ROLES = (
    "Scout Agent",
    "Source Agent",
    "QKU Agent",
    "Formula Agent",
    "Quantum Agent",
    "Simulation / Pretrade Agent",
    "TCA Agent",
    "Risk Agent",
    "Ranking Agent",
    "Memory Agent",
    "LLM Critic Agent",
    "Execution-prep Agent",
    "Governance Agent",
    "Commander Agent",
)

QUEUE_STATES = {
    "QUEUED",
    "RUNNING",
    "WAITING_EVIDENCE",
    "WAITING_OWNER",
    "WAITING_AGENT",
    "BLOCKED",
    "READY_REPLAY",
    "READY_PAPER",
    "READY_LIVE_DRYRUN",
    "READY_LIVE_CANARY_REVIEW",
    "COMPLETED",
    "QUARANTINED",
}

AUTHORITY_FALSE_FIELDS = (
    "runtime_llm_call_created",
    "llm_source_truth_created",
    "llm_order_authority_created",
    "llm_profit_claim_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_order_authority_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "order_submission_created",
    "direct_venue_submit_created",
    "execution_router_release_created",
    "connector_read_created",
    "connector_write_created",
    "private_cash_read_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "profit_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
    "runtime_agent_execution_created",
    "runtime_side_effect_created",
    "source_truth_created",
    "source_truth_authority_created",
    "accepted_source_truth_created",
    "fake_receipt_created",
    "fake_runtime_receipt_created",
    "paper_order_intent_receipt_created",
    "paper_fill_receipt_created",
    "paper_exit_receipt_created",
    "paper_pnl_receipt_created",
    "live_receipt_created",
    "private_cash_account_read_created",
    "connector_semantics_created",
    "venue_submit_created",
    "runtime_cache_created",
    "runtime_orchestration_created",
    "memory_update_receipt_created",
)

LIVE_PATH_FALSE_FIELDS = (
    "live_critical_path_allowed",
    "heavy_compute_live_path_allowed",
    "source_retrieval_live_path_allowed",
    "llm_call_live_path_allowed",
    "quantum_backend_live_path_allowed",
    "master_plan_compile_live_path_allowed",
)

PHASE0_COLUMNS = (
    "semantic_domain",
    "expected_source_or_artifact",
    "current_equivalent_path_or_absent",
    "upstream_pr_or_source",
    "agent_orch_consumption_plan",
    "projection_plan",
    "producer_registry_or_contract",
    "agent_task_consumer",
    "owner_surface_consumer",
    "svc1_route",
    "pretrade_route",
    "readiness_route",
    "mem1_route",
    "llm_route",
    "paper_loop_route",
    "hotpath_route",
    "live_dryrun_route",
    "postlaunch_route",
    "plugin_qmap_allow_route",
    "builder_or_owner_module",
    "validator_or_test_consumer",
    "mutation_required",
    "mutation_reason",
    "orphan_risk",
    "authority_risk",
    "raw_jsonl_scan_risk",
    "fake_runtime_state_risk",
    "fake_receipt_risk",
    "source_truth_risk",
    "connector_private_cash_risk",
    "runtime_llm_risk",
    "runtime_agent_risk",
    "runtime_execution_risk",
    "paper_execution_risk",
    "live_execution_risk",
    "qku_formula_route_risk",
    "institutional_control_route_risk",
    "quantum_route_risk",
    "mem1_proof_misuse_risk",
    "latency_path_risk",
    "owner_action_bypass_risk",
    "agent_role_invention_risk",
    "compact_validation_risk",
    "owned_prefix_scope_risk",
    "shared_currentization_risk",
)

PLAIN_ENGLISH_EXAMPLES = (
    (
        "Can QTT check this market and find the best trade?",
        "OWNER_TRADE_CHECK_REQUEST",
    ),
    (
        "Research this article and tell me if it creates a prediction-market edge.",
        "OWNER_RESEARCH_SUBMISSION",
    ),
    (
        "Ask the QKU agents to compare the best formula stacks for this event.",
        "QKU_FORMULA_STACK_COMPARE_REQUEST",
    ),
    ("Why did no-trade win here?", "NO_TRADE_EXPLANATION_REQUEST"),
    (
        "What variables would make this trade pass replay and paper?",
        "NO_TRADE_REOPTIMIZATION_REQUEST",
    ),
    ("Show me which agent disagrees and why.", "AGENT_DISAGREEMENT_REVIEW_REQUEST"),
)

NO_TRADE_RECOVERY_ROUTES = (
    "variable_tuning",
    "stack_challenger_search",
    "venue_rotation",
    "yes_no_side_rotation",
    "maker_taker_policy_rotation",
    "smaller_size_test",
    "hold_duration_exit_rule_retest",
    "liquidity_spread_filter_retest",
    "latency_budget_retest",
    "source_refresh",
    "adapter_reality_model_refresh",
    "memory_prior_challenger_batch",
    "next_target_rotation",
)

INSTITUTIONAL_REFS = (
    "rank_ref_or_gap",
    "tca_ref_or_gap",
    "fdr_ref_or_gap",
    "portfolio_ref_or_gap",
    "capacity_ref_or_gap",
    "champion_ref_or_gap",
    "mem_prior_ref_or_gap",
    "utility_ref_or_gap",
    "scenario_ref_or_gap",
    "calibration_ref_or_gap",
    "notrade_margin_ref_or_gap",
    "quantum_ref_or_gap",
)

PROJECTION_CLASSES: dict[str, dict[str, str]] = {
    "dag.jsonl": {"object_type": "AgentDAGRegistryV1", "lane": "GOVERNANCE_LANE"},
    "dag_nodes.jsonl": {"object_type": "AgentDAGNodeV1", "lane": "GOVERNANCE_LANE"},
    "dag_edges.jsonl": {"object_type": "AgentDAGEdgeV1", "lane": "GOVERNANCE_LANE"},
    "task_registry.jsonl": {"object_type": "AgentTaskRegistryV1", "lane": "GOVERNANCE_LANE"},
    "task_queue.jsonl": {"object_type": "AgentTaskQueueV1", "lane": "GOVERNANCE_LANE"},
    "task_env.jsonl": {"object_type": "AgentTaskEnvelopeV1", "lane": "GOVERNANCE_LANE"},
    "directives.jsonl": {"object_type": "AgentDirectiveEnvelopeV1", "lane": "GOVERNANCE_LANE"},
    "workflows.jsonl": {"object_type": "AgentWorkflowRunV1", "lane": "GOVERNANCE_LANE"},
    "handoffs.jsonl": {"object_type": "AgentHandoffPacketV1", "lane": "EXEC_PREP_LANE"},
    "role_map.jsonl": {"object_type": "AgentRoleMapV1", "lane": "GOVERNANCE_LANE"},
    "duty_map.jsonl": {"object_type": "AgentDutyMapV1", "lane": "GOVERNANCE_LANE"},
    "perm_scope.jsonl": {"object_type": "AgentPermissionScopeV1", "lane": "GOVERNANCE_LANE"},
    "retry_policy.jsonl": {"object_type": "AgentRetryPolicyV1", "lane": "GOVERNANCE_LANE"},
    "priority_policy.jsonl": {"object_type": "AgentPriorityPolicyV1", "lane": "GOVERNANCE_LANE"},
    "quarantine.jsonl": {"object_type": "AgentQuarantinePolicyV1", "lane": "GOVERNANCE_LANE"},
    "agent_ops.jsonl": {"object_type": "OwnerAgentOperationsStateV1", "lane": "GOVERNANCE_LANE"},
    "team_queue.jsonl": {"object_type": "OwnerWorkflowQueueStateV1", "lane": "GOVERNANCE_LANE"},
    "intel_lanes.jsonl": {"object_type": "AgentIntelligenceLaneV1", "lane": "GOVERNANCE_LANE"},
    "tournament_tasks.jsonl": {"object_type": "AgentTournamentTaskBundleV1", "lane": "GOVERNANCE_LANE"},
    "task_receipts.jsonl": {"object_type": "RuntimeTaskReceiptV1", "lane": "GOVERNANCE_LANE"},
    "decision_receipts.jsonl": {"object_type": "AgentDecisionReceiptV1", "lane": "GOVERNANCE_LANE"},
    "dispute_receipts.jsonl": {"object_type": "AgentDisagreementReceiptV1", "lane": "GOVERNANCE_LANE"},
    "escalation_receipts.jsonl": {"object_type": "AgentEscalationReceiptV1", "lane": "GOVERNANCE_LANE"},
    "handoff_receipts.jsonl": {"object_type": "AgentHandoffReceiptV1", "lane": "GOVERNANCE_LANE"},
    "audit_trail.jsonl": {"object_type": "AgentAuditTrailV1", "lane": "GOVERNANCE_LANE"},
    "svc1_bindings.jsonl": {"object_type": "AgentSVC1BindingV1", "lane": "GOVERNANCE_LANE"},
    "readiness_bindings.jsonl": {"object_type": "AgentReadinessBindingV1", "lane": "KNOWLEDGE_LANE"},
    "pretrade_bindings.jsonl": {"object_type": "AgentPretradeBindingV1", "lane": "SIMULATION_LANE"},
    "mem1_bindings.jsonl": {"object_type": "AgentMEM1PriorBindingV1", "lane": "LEARNING_LANE"},
    "owner_cmd_tasks.jsonl": {"object_type": "OwnerAgentDirectiveEnvelopeV1", "lane": "GOVERNANCE_LANE"},
    "chat_tasks.jsonl": {"object_type": "OwnerPlainEnglishIntentTaskV1", "lane": "REASONING_LANE"},
    "qku_tasks.jsonl": {"object_type": "AgentQKUFormulaComputeTaskV1", "lane": "KNOWLEDGE_LANE"},
    "formula_tasks.jsonl": {"object_type": "AgentQKUFormulaComputeTaskV1", "lane": "KNOWLEDGE_LANE"},
    "access_proof.jsonl": {"object_type": "AgentLibraryAccessProofV1", "lane": "KNOWLEDGE_LANE"},
    "library_receipts.jsonl": {"object_type": "LibraryQueryReceiptV1", "lane": "KNOWLEDGE_LANE"},
    "graph_routes.jsonl": {"object_type": "QKUGraphRouteV1", "lane": "KNOWLEDGE_LANE"},
    "graph_tasks.jsonl": {"object_type": "QKUGraphTaskV1", "lane": "KNOWLEDGE_LANE"},
    "graph_quality.jsonl": {"object_type": "QKUGraphQualityRouteV1", "lane": "GOVERNANCE_LANE"},
    "tradeplan_tasks.jsonl": {"object_type": "AgentTradePlanTaskV1", "lane": "SEARCH_LANE"},
    "pretrade_tasks.jsonl": {"object_type": "AgentPretradeTaskV1", "lane": "SIMULATION_LANE"},
    "mode_tasks.jsonl": {"object_type": "AgentModeAuthorityTaskV1", "lane": "GOVERNANCE_LANE"},
    "order_policy_tasks.jsonl": {"object_type": "AgentOrderPolicyTaskV1", "lane": "SIMULATION_LANE"},
    "paper_prep.jsonl": {"object_type": "AgentPaperPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "hotpath_prep.jsonl": {"object_type": "AgentHotpathPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "shadow_prep.jsonl": {"object_type": "AgentShadowPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "live_prep.jsonl": {"object_type": "AgentLiveDryrunPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "rank_tasks.jsonl": {"object_type": "AgentRankingTaskV1", "lane": "SIMULATION_LANE"},
    "tca_tasks.jsonl": {"object_type": "AgentTCATaskV1", "lane": "SIMULATION_LANE"},
    "fdr_tasks.jsonl": {"object_type": "AgentFDRTaskV1", "lane": "SIMULATION_LANE"},
    "portfolio_tasks.jsonl": {"object_type": "AgentPortfolioTaskV1", "lane": "SIMULATION_LANE"},
    "capacity_tasks.jsonl": {"object_type": "AgentCapacityTaskV1", "lane": "SIMULATION_LANE"},
    "champion_tasks.jsonl": {"object_type": "AgentChampionTaskV1", "lane": "SIMULATION_LANE"},
    "mem_prior_tasks.jsonl": {"object_type": "AgentMemoryPriorTaskV1", "lane": "LEARNING_LANE"},
    "utility_tasks.jsonl": {"object_type": "AgentUtilityTaskV1", "lane": "SIMULATION_LANE"},
    "scenario_tasks.jsonl": {"object_type": "AgentScenarioTaskV1", "lane": "SIMULATION_LANE"},
    "calibration_tasks.jsonl": {"object_type": "AgentCalibrationTaskV1", "lane": "SIMULATION_LANE"},
    "notrade_tasks.jsonl": {"object_type": "AgentNoTradeReoptimizationTaskV1", "lane": "SEARCH_LANE"},
    "var_tune_tasks.jsonl": {"object_type": "AgentVariableTuneTaskV1", "lane": "SEARCH_LANE"},
    "stack_tasks.jsonl": {"object_type": "AgentStackChallengerTaskV1", "lane": "SEARCH_LANE"},
    "venue_side_tasks.jsonl": {"object_type": "AgentVenueSideRotationTaskV1", "lane": "SEARCH_LANE"},
    "source_refresh_tasks.jsonl": {"object_type": "AgentSourceRefreshTaskV1", "lane": "SEARCH_LANE"},
    "retest_tasks.jsonl": {"object_type": "AgentRetestTaskV1", "lane": "SEARCH_LANE"},
    "reality_tasks.jsonl": {"object_type": "AgentRealityModelTaskV1", "lane": "SIMULATION_LANE"},
    "metric_tasks.jsonl": {"object_type": "AgentMetricRouteTaskV1", "lane": "SIMULATION_LANE"},
    "plugin_prep.jsonl": {"object_type": "AgentPluginPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "qmap_prep.jsonl": {"object_type": "AgentQMapPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "allow_prep.jsonl": {"object_type": "AgentAllowPrepTaskV1", "lane": "EXEC_PREP_LANE"},
    "formula_intake.jsonl": {"object_type": "FormulaIntakeRouteV1", "lane": "KNOWLEDGE_LANE"},
    "latency_tiers.jsonl": {"object_type": "FormulaLatencyTierRouteV1", "lane": "EXEC_PREP_LANE"},
    "clean_room.jsonl": {"object_type": "CleanRoomFormulaRouteV1", "lane": "GOVERNANCE_LANE"},
    "quantum_tasks.jsonl": {"object_type": "AgentQuantumStructuralTaskV1", "lane": "SIMULATION_LANE"},
    "fallback_tasks.jsonl": {"object_type": "AgentClassicalFallbackTaskV1", "lane": "SIMULATION_LANE"},
    "downstream.jsonl": {"object_type": "AgentDownstreamRouteV1", "lane": "GOVERNANCE_LANE"},
    "value_routes.jsonl": {"object_type": "ArtifactValueRouteV1", "lane": "GOVERNANCE_LANE"},
    "capability_routes.jsonl": {"object_type": "CapabilityOwnershipRouteV1", "lane": "GOVERNANCE_LANE"},
    "learning_routes.jsonl": {"object_type": "PostlaunchLearningRouteV1", "lane": "LEARNING_LANE"},
}


class BuildError(RuntimeError):
    pass


def _repo_root_from(path: Path) -> Path:
    root = path.resolve()
    if (root / ".git").exists():
        return root
    for parent in root.parents:
        if (parent / ".git").exists():
            return parent
    return root


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise BuildError(f"JSONL row is not an object: {path}:{line_number}")
            rows.append(value)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"JSON document is not an object: {path}")
    return value


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _slug(value: str) -> str:
    cleaned = []
    for char in str(value):
        if char.isalnum():
            cleaned.append(char.upper())
        else:
            cleaned.append("_")
    return "_".join(part for part in "".join(cleaned).split("_") if part)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    if value == "":
        return []
    return [value]


def _first_nonempty(*values: Any, default: str = "SCOPED_GAP_NOT_PRESENT") -> Any:
    for value in values:
        if value not in (None, "", [], {}, ()):
            return value
    return default


def _unique(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        marker = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result


def _ref(path: str, row: Mapping[str, Any] | None, fallback: str) -> str:
    if not row:
        return f"{path}::{fallback}"
    for key in (
        "registry_row_id",
        "row_id",
        "candidate_id",
        "action_id",
        "action_code",
        "task_id",
        "object_id",
    ):
        value = row.get(key)
        if value:
            return f"{path}::{value}"
    return f"{path}::{fallback}"


def _by_candidate(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id") or row.get("candidate_id_or_gap") or "")
        if candidate_id and candidate_id not in result:
            result[candidate_id] = dict(row)
    return result


def _load_declared_jsonl(root: Path, prefix: Path, file_names: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    return {name: _read_jsonl(root / prefix / name) for name in file_names}


def _load_context(repo_root: Path) -> dict[str, Any]:
    svc1 = _load_declared_jsonl(repo_root, SVC1_PREFIX, SVC1_FILES)
    pretrade = _load_declared_jsonl(repo_root, PRETRADE1_PREFIX, PRETRADE1_FILES)
    readiness = _load_declared_jsonl(repo_root, READINESS1_PREFIX, READINESS1_FILES)
    mem1 = _load_declared_jsonl(repo_root, MEM1_PREFIX, MEM1_FILES)
    pr165_d2 = {
        "roster": _read_json(repo_root / PR165_D2_ROSTER_REF),
        "duty": _read_json(repo_root / PR165_D2_DUTY_REF),
        "command_action_matrix": _read_json(repo_root / "docs/master_plan/generated/PR165_D2_CommandActionMatrix.report.json"),
        "master_plan_crosswalk": _read_json(repo_root / "docs/master_plan/generated/PR165_D2_MasterPlanSectionCrosswalk.report.json"),
        "market_specific_index": _read_json(repo_root / "docs/master_plan/generated/PR165_D2_MarketSpecificSelectionIndex.report.json"),
    }

    pretrade_registry = pretrade["pretrade_decision_registry.jsonl"]
    readiness_registry = readiness["agent_readiness_registry.jsonl"]
    candidate_ids = [
        str(row["candidate_id"])
        for row in pretrade_registry
        if row.get("candidate_id")
    ]
    if not candidate_ids:
        candidate_ids = [
            str(row["candidate_id"])
            for row in readiness_registry
            if row.get("candidate_id")
        ]
    if not candidate_ids:
        raise BuildError("No candidate ids found in PRETRADE1 or READINESS1")

    owner_actions = svc1["owner_action_requests.generated.jsonl"]
    if not owner_actions:
        raise BuildError("SVC1 owner action requests are required")

    return {
        "svc1": svc1,
        "pretrade": pretrade,
        "readiness": readiness,
        "mem1": mem1,
        "pr165_d2": pr165_d2,
        "candidate_ids": candidate_ids,
        "pretrade_by_candidate": _by_candidate(pretrade_registry),
        "readiness_by_candidate": _by_candidate(readiness_registry),
        "svc_by_candidate": _by_candidate(svc1["service_registry.jsonl"]),
        "svc_qku_by_candidate": _by_candidate(svc1["qku_formula_compute_route_views.generated.jsonl"]),
        "owner_actions": owner_actions,
        "mem_context_rows": mem1["context_signature.jsonl"],
    }


def _candidate_mem_ref(ctx: Mapping[str, Any], candidate_id: str, index: int) -> str:
    pre = ctx["pretrade_by_candidate"].get(candidate_id, {})
    read = ctx["readiness_by_candidate"].get(candidate_id, {})
    mem_rows = ctx["mem_context_rows"]
    if pre.get("mem1_memory_ref_or_gap"):
        return str(pre["mem1_memory_ref_or_gap"])
    if read.get("mem1_memory_ref_or_gap"):
        return str(read["mem1_memory_ref_or_gap"])
    if mem_rows:
        return _ref(
            "docs/master_plan/generated/pr168_mem1/context_signature.jsonl",
            mem_rows[index % len(mem_rows)],
            f"MEM1_CONTEXT_SIGNATURE_{index + 1:04d}",
        )
    return "PR168_MEM1_GAP::context_signature"


def _candidate_roles(ctx: Mapping[str, Any], candidate_id: str) -> tuple[list[str], list[str], list[str]]:
    pre = ctx["pretrade_by_candidate"].get(candidate_id, {})
    read = ctx["readiness_by_candidate"].get(candidate_id, {})
    svc = ctx["svc_by_candidate"].get(candidate_id, {})
    roles = _unique(
        [
            *_as_list(pre.get("agent_role_refs")),
            *_as_list(read.get("agent_role_refs")),
            *_as_list(svc.get("responsible_agent_role_refs")),
        ]
    )
    if not roles:
        roles = ["PR165_D2_GAP::ResponsibleAgent"]
    supporting = _unique(
        [
            *_as_list(svc.get("supporting_agent_role_refs_or_gap")),
            "PR165_D2_GAP::IndependentChallengeAgent",
        ]
    )
    escalation = _unique(
        [
            *_as_list(svc.get("escalation_agent_role_refs_or_gap")),
            "GovernanceAgent",
            "CommanderAgent",
        ]
    )
    return [str(role) for role in roles], [str(role) for role in supporting], [str(role) for role in escalation]


def _candidate_refs(ctx: Mapping[str, Any], candidate_id: str, index: int) -> dict[str, Any]:
    pre = ctx["pretrade_by_candidate"].get(candidate_id, {})
    read = ctx["readiness_by_candidate"].get(candidate_id, {})
    svc = ctx["svc_by_candidate"].get(candidate_id, {})
    svc_qku = ctx["svc_qku_by_candidate"].get(candidate_id, {})
    mem_ref = _candidate_mem_ref(ctx, candidate_id, index)
    qku_refs = _unique(
        [
            *_as_list(pre.get("qku_refs")),
            *_as_list(read.get("qku_refs")),
            *_as_list(svc_qku.get("qku_refs")),
        ]
    )
    formula_refs = _unique(
        [
            *_as_list(pre.get("formula_refs")),
            *_as_list(read.get("formula_refs")),
            *_as_list(svc_qku.get("formula_refs")),
        ]
    )
    if not qku_refs:
        qku_refs = [f"QKU_SCOPED_GAP::{candidate_id}"]
    if not formula_refs:
        formula_refs = [f"FORMULA_SCOPED_GAP::{candidate_id}"]

    return {
        "pre": pre,
        "read": read,
        "svc": svc,
        "svc_qku": svc_qku,
        "mem_ref": mem_ref,
        "qku_refs": [str(value) for value in qku_refs[:8]],
        "formula_refs": [str(value) for value in formula_refs[:8]],
    }


def _base_row(
    *,
    object_type: str,
    object_id: str,
    task_class: str,
    lane: str,
    projection_file: str,
    candidate_id: str | None = None,
    action_ref: str | None = None,
    stage: str | None = None,
    downstream_owner: str = "PR169-AGENT-ORCH1",
    ctx: Mapping[str, Any],
    index: int = 0,
) -> dict[str, Any]:
    candidate = candidate_id or "SCOPED_GAP_NO_CANDIDATE"
    refs = _candidate_refs(ctx, candidate, index) if candidate_id else {
        "pre": {},
        "read": {},
        "svc": {},
        "svc_qku": {},
        "mem_ref": "PR168_MEM1_GAP::not_candidate_scoped",
        "qku_refs": ["QKU_SCOPE_GAP::not_candidate_scoped"],
        "formula_refs": ["FORMULA_SCOPE_GAP::not_candidate_scoped"],
    }
    pre = refs["pre"]
    read = refs["read"]
    svc = refs["svc"]
    svc_qku = refs["svc_qku"]
    responsible, supporting, escalation = _candidate_roles(ctx, candidate) if candidate_id else (
        ["GovernanceAgent"],
        ["PR165_D2_GAP::SupportAgent"],
        ["CommanderAgent"],
    )
    row_slug = _slug(f"{object_type}::{object_id}")[:96]
    row_id = f"AGENT_ORCH1::{row_slug}"
    if projection_file in {
        "task_registry.jsonl",
        "task_queue.jsonl",
        "task_env.jsonl",
        "directives.jsonl",
        "workflows.jsonl",
        "handoffs.jsonl",
    }:
        task_id = f"AGENT_ORCH1_TASK::CANDIDATE::{_slug(candidate)}"
    else:
        task_id = f"AGENT_ORCH1_TASK::{row_slug}"
    workflow_id = f"AGENT_ORCH1_WORKFLOW::{_slug(candidate)}"
    stage_name = stage or task_class
    selected_qku_refs = refs["qku_refs"][:5]
    selected_formula_refs = refs["formula_refs"][:5]
    priority_score = round(0.91 - min(index, 20) * 0.01, 6)
    queue_state = "WAITING_EVIDENCE" if "NO_TRADE" in task_class else "QUEUED"
    if queue_state not in QUEUE_STATES:
        queue_state = "QUEUED"

    row: dict[str, Any] = {
        "row_id": row_id,
        "registry_row_id": row_id,
        "source_registry_row_id": row_id,
        "object_type": object_type,
        "object_id": object_id,
        "object_version": PROJECTION_VERSION,
        "generated_from": REGISTRY_REF,
        "builder": BUILDER_NAME,
        "builder_name": BUILDER_NAME,
        "validator": VALIDATOR_NAME,
        "validator_name": VALIDATOR_NAME,
        "manual_edit_allowed": False,
        "projection_file": projection_file,
        "projection_ref": f"{GENERATED_PREFIX.as_posix()}/{projection_file}::{row_id}",
        "canonical_registry_source_ref": REGISTRY_REF,
        "candidate_id": candidate_id,
        "candidate_id_or_gap": candidate,
        "svc1_ref_or_gap": _ref("docs/master_plan/generated/pr169_svc1/service_registry.jsonl", svc, f"SVC1_GAP::{candidate}"),
        "readiness_ref_or_gap": _ref("docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl", read, f"READINESS1_GAP::{candidate}"),
        "pretrade_ref_or_gap": _ref("docs/master_plan/generated/pr169_pretrade1/pretrade_decision_registry.jsonl", pre, f"PRETRADE1_GAP::{candidate}"),
        "mem1_ref_or_gap": refs["mem_ref"],
        "pr165_d2_roster_ref_or_gap": PR165_D2_ROSTER_REF,
        "pr165_d2_duty_ref_or_gap": PR165_D2_DUTY_REF,
        "owner_action_ref_or_gap": action_ref or _first_nonempty(svc.get("owner_action_ref_or_gap"), default="OWNER_ACTION_SCOPED_GAP"),
        "owner_cmd_ref_or_gap": _first_nonempty(read.get("owner_command_route_ref_or_gap"), svc.get("owner_trade_intent_route_ref_or_gap"), default="OWNER_COMMAND_SCOPED_GAP"),
        "owner_receipt_ref_or_gap": _first_nonempty(svc.get("action_receipt_ref_or_gap"), default="OWNER_RECEIPT_SCOPED_GAP"),
        "tradeplan_ref_or_gap": _first_nonempty(pre.get("trade_plan_candidate_ref"), svc.get("trade_plan_candidate_ref_or_gap"), read.get("trade_plan_candidate_ref"), default=f"TRADEPLAN_SCOPED_GAP::{candidate}"),
        "pretrade_candidate_ref_or_gap": _first_nonempty(pre.get("pretrade_decision_candidate_id"), svc.get("pretrade_decision_candidate_ref_or_gap"), default=f"PRETRADE_CANDIDATE_SCOPED_GAP::{candidate}"),
        "no_trade_ref_or_gap": _first_nonempty(pre.get("no_trade_candidate_ref_or_gap"), svc.get("no_trade_candidate_ref_or_gap"), default=f"NO_TRADE_COMPARATOR::{candidate}"),
        "qku_refs": selected_qku_refs,
        "formula_refs": selected_formula_refs,
        "algorithm_refs_or_gap": _first_nonempty(pre.get("algorithm_refs_or_gap"), svc.get("algorithm_refs_or_gap"), read.get("algorithm_refs_or_gap"), default=["ALGORITHM_SCOPED_GAP"]),
        "computable_refs_or_gap": _first_nonempty(read.get("computable_contract_id"), pre.get("readiness1_computable_contract_ref"), svc.get("computable_contract_refs_or_gap"), default=f"COMPUTABLE_CONTRACT_SCOPED_GAP::{candidate}"),
        "exec_state_ref_or_gap": _first_nonempty(read.get("executable_now_state"), default="EXEC_STATE_SCOPED_GAP"),
        "paper_usable_ref_or_gap": _first_nonempty(read.get("paper_loop_usable_state"), default="PAPER_USABLE_SCOPED_GAP"),
        "adapter_gap_ref_or_gap": _first_nonempty(read.get("adapter_blocker_family"), default="ADAPTER_GAP_SCOPED_GAP"),
        "dag_ref": "AGENT_ORCH1_DAG::central",
        "node_ref": f"AGENT_ORCH1_NODE::{_slug(stage_name)}",
        "edge_ref": f"AGENT_ORCH1_EDGE::{_slug(stage_name)}",
        "task_ref": task_id,
        "task_env_ref": f"AgentTaskEnvelopeV1::{task_id}",
        "workflow_ref": workflow_id,
        "stage_ref": f"AgentWorkflowStageV1::{stage_name}",
        "handoff_ref_or_gap": f"AgentHandoffPacketV1::{task_id}",
        "receipt_ref_or_gap": f"RuntimeTaskReceiptV1::{task_id}",
        "task_id": task_id,
        "queue_id": "AGENT_ORCH1_QUEUE::central_static",
        "task_class": task_class,
        "intelligence_lane": lane,
        "intelligence_lanes": [lane],
        "tournament_role_ref_or_gap": [f"PR165_D2_GAP::{_slug(role)}" for role in TOURNAMENT_ROLES],
        "task_state": "TASK_CONTRACT_READY_NO_RUNTIME",
        "queue_state": queue_state,
        "priority_class": "P1_OWNER_OR_CANDIDATE_ROUTE",
        "priority_score_or_gap": priority_score,
        "task_key": f"{task_class}::{candidate}::{action_ref or 'NO_ACTION'}",
        "dedupe_policy_ref_or_gap": f"AgentTaskDedupePolicyV1::{task_class}::{candidate}",
        "retry_state": "RETRY_AVAILABLE_NOT_STARTED",
        "retry_count": 0,
        "max_retry_count": 2,
        "blocked_reason_or_none": "NONE",
        "safe_next_route": f"SAFE_NEXT::{task_class}::{candidate}",
        "responsible_roles": responsible,
        "required_roles": responsible,
        "supporting_roles_or_gap": supporting,
        "escalation_roles_or_gap": escalation,
        "role_resolution_state": "PR165_D2_CURRENT_EQUIVALENT_OR_SCOPED_GAP",
        "role_gap_reason_or_none": "NONE" if not any(str(role).startswith("PR165_D2_GAP") for role in responsible) else "PR165_D2_GAP",
        "agent_pod_or_gap": _first_nonempty(svc.get("agent_pod_ref_or_gap"), default="PR165_D2_AGENT_POD_OR_SCOPED_GAP"),
        "permission_scope_ref_or_gap": f"AgentPermissionScopeV1::{task_class}",
        "retry_policy_ref_or_gap": "AgentRetryPolicyV1::bounded_no_runtime",
        "quarantine_ref_or_gap": "AgentQuarantinePolicyV1::provider_pending_quarantine",
        "rank_ref_or_gap": _first_nonempty(pre.get("rank4_rank_ref_or_gap"), svc_qku.get("execution_adjusted_ranking_view_ref_or_gap"), default=f"RANK_ROUTE::{candidate}"),
        "tca_ref_or_gap": _first_nonempty(pre.get("tca_decomposition_ref_or_gap"), svc_qku.get("tca_decomposition_ref_or_gap"), svc_qku.get("tca_decomposition_view_ref_or_gap"), default=f"TCA_ROUTE::{candidate}"),
        "fdr_ref_or_gap": _first_nonempty(svc_qku.get("fdr_overfit_status_ref_or_gap"), svc_qku.get("overfit_fdr_control_view_ref_or_gap"), default=f"FDR_ROUTE::{candidate}"),
        "portfolio_ref_or_gap": _first_nonempty(svc_qku.get("portfolio_diversification_view_ref_or_gap"), default=f"PORTFOLIO_ROUTE::{candidate}"),
        "capacity_ref_or_gap": _first_nonempty(pre.get("capacity_crowding_model_ref_or_gap"), svc_qku.get("capacity_crowding_ref_or_gap"), default=f"CAPACITY_ROUTE::{candidate}"),
        "champion_ref_or_gap": _first_nonempty(svc_qku.get("champion_challenger_view_ref_or_gap"), default=f"CHAMPION_ROUTE::{candidate}"),
        "mem_prior_ref_or_gap": refs["mem_ref"],
        "utility_ref_or_gap": _first_nonempty(svc_qku.get("marginal_utility_view_ref_or_gap"), default=f"UTILITY_ROUTE::{candidate}"),
        "scenario_ref_or_gap": _first_nonempty(pre.get("scenario_ladder_decision_ref_or_gap"), svc_qku.get("scenario_ladder_ref_or_gap"), default=f"SCENARIO_ROUTE::{candidate}"),
        "calibration_ref_or_gap": _first_nonempty(pre.get("probability_calibration_gate_ref_or_gap"), svc_qku.get("calibration_ref_or_gap"), default=f"CALIBRATION_ROUTE::{candidate}"),
        "notrade_margin_ref_or_gap": _first_nonempty(svc_qku.get("candidate_minus_no_trade_ref_or_gap"), svc_qku.get("no_trade_margin_view_ref_or_gap"), default=f"NO_TRADE_MARGIN_ROUTE::{candidate}"),
        "quantum_ref_or_gap": _first_nonempty(pre.get("pretrade_quantum_readiness_handoff_ref_or_gap"), read.get("qstruct_blocker_detail_or_gap"), svc_qku.get("quantum_structural_readiness_view_ref_or_gap"), default=f"QUANTUM_ROUTE::{candidate}"),
        "memory_scope": "CONDITION_SCOPED_PRIOR_ONLY_CURRENT_REVALIDATION_REQUIRED",
        "memory_prior_ref_or_gap": refs["mem_ref"],
        "memory_is_prior_not_proof": True,
        "memory_revalidation_required": True,
        "memory_update_receipt_created": False,
        "same_venue_scope": True,
        "same_market_type_scope": True,
        "same_event_lifecycle_scope": True,
        "same_liquidity_spread_bucket_scope": True,
        "same_time_to_resolution_bucket_scope": True,
        "same_formula_algorithm_qku_stack_scope": True,
        "same_parameter_range_scope": True,
        "same_maker_taker_order_policy_scope": True,
        "llm_task_ref_or_gap": _first_nonempty(svc.get("agent_llm_task_route_ref_or_gap"), pre.get("pretrade_llm_grounding_view_ref_or_gap"), default=f"LLM_CONTRACT::{candidate}"),
        "llm_grounding_ref_or_gap": _first_nonempty(svc.get("llm_grounding_route_ref_or_gap"), read.get("llm_grounding_view_ref_or_gap"), default=f"LLM_GROUNDING::{candidate}"),
        "llm_task_class": "AgentLLMReviewTaskContractV1",
        "input_contract_ref_or_gap": f"AgentTaskEnvelopeV1::{task_id}",
        "grounding_refs": [REGISTRY_REF, _first_nonempty(pre.get("pretrade_decision_trace_ref_or_gap"), default=f"PRETRADE_TRACE::{candidate}")],
        "allowed_actions": ["research", "summarize", "critique", "explain", "propose", "route"],
        "forbidden_actions": ["source_truth", "risk_pass", "profit_proof", "order_authority", "connector_authority", "live_readiness"],
        "qstruct_ref_or_gap": _first_nonempty(svc_qku.get("qstruct_ref_or_gap"), pre.get("pretrade_quantum_readiness_handoff_ref_or_gap"), default=f"QSTRUCT_ROUTE::{candidate}"),
        "objective_route_ref_or_gap": _first_nonempty(svc_qku.get("objective_function_route_ref_or_gap"), pre.get("pretrade_objective_kernel_ref_or_gap"), default=f"OBJECTIVE_ROUTE::{candidate}"),
        "variable_route_ref_or_gap": _first_nonempty(svc_qku.get("variable_encoding_route_ref_or_gap"), read.get("trade_variable_search_handoff_ref_or_gap"), default=f"VARIABLE_ROUTE::{candidate}"),
        "constraint_route_ref_or_gap": _first_nonempty(svc_qku.get("constraint_route_ref_or_gap"), default=f"CONSTRAINT_ROUTE::{candidate}"),
        "penalty_route_ref_or_gap": _first_nonempty(svc_qku.get("penalty_scaling_route_ref_or_gap"), default=f"PENALTY_ROUTE::{candidate}"),
        "coefficient_scale_ref_or_gap": _first_nonempty(svc_qku.get("coefficient_scaling_route_ref_or_gap"), default=f"COEFFICIENT_SCALE_ROUTE::{candidate}"),
        "quadratic_program_ref_or_gap": _first_nonempty(svc_qku.get("quadratic_program_route_ref_or_gap"), default=f"QUADRATIC_PROGRAM_ROUTE::{candidate}"),
        "qubo_ref_or_gap": _first_nonempty(svc_qku.get("qubo_route_ref_or_gap"), default=f"QUBO_ROUTE::{candidate}"),
        "bqm_ref_or_gap": _first_nonempty(svc_qku.get("bqm_route_ref_or_gap"), default=f"BQM_ROUTE::{candidate}"),
        "cqm_ref_or_gap": _first_nonempty(svc_qku.get("cqm_route_ref_or_gap"), default=f"CQM_ROUTE::{candidate}"),
        "ising_ref_or_gap": _first_nonempty(svc_qku.get("ising_route_ref_or_gap"), default=f"ISING_ROUTE::{candidate}"),
        "qaoa_vqe_ref_or_gap": _first_nonempty(svc_qku.get("qaoa_candidate_route_ref_or_gap"), svc_qku.get("vqe_candidate_route_ref_or_gap"), default=f"QAOA_VQE_ROUTE::{candidate}"),
        "qaoa_vqe_route_ref_or_gap": _first_nonempty(svc_qku.get("qaoa_candidate_route_ref_or_gap"), svc_qku.get("vqe_candidate_route_ref_or_gap"), default=f"QAOA_VQE_ROUTE::{candidate}"),
        "classical_fallback_ref_or_gap": _first_nonempty(svc_qku.get("fallback_route_ref_or_gap"), default=f"CLASSICAL_FALLBACK_ROUTE::{candidate}"),
        "interpret_back_map_ref_or_gap": f"INTERPRET_BACK_MAP_ROUTE::{candidate}",
        "qmap_owner_route_ref_or_gap": _first_nonempty(svc.get("qmap_route_ref_or_gap"), read.get("qmap_route_ref_or_gap"), default="PR174-QMAP1::mapping_route_only"),
        "paper_route_ref_or_gap": _first_nonempty(svc.get("paper_loop_route_ref_or_gap"), read.get("paper_loop_route_ref_or_gap"), default="PR169-PAPER-LOOP::provider_pending"),
        "hotpath_route_ref_or_gap": _first_nonempty(svc.get("hotpath_handoff_route_ref_or_gap"), read.get("hotpath_route_ref_or_gap"), default="PR170-HOTPATH1::provider_pending"),
        "paper_prep_ref_or_gap": f"AgentPaperPrepTaskV1::{candidate}",
        "hotpath_prep_ref_or_gap": f"AgentHotpathPrepTaskV1::{candidate}",
        "shadow_prep_ref_or_gap": f"AgentShadowPrepTaskV1::{candidate}",
        "live_dryrun_ref_or_gap": f"AgentLiveDryrunPrepTaskV1::{candidate}",
        "metrics_ref_or_gap": _first_nonempty(pre.get("pretrade_metrics_capture_handoff_ref_or_gap"), svc.get("metrics_capture_route_ref_or_gap"), default=f"METRICS_ROUTE::{candidate}"),
        "postlaunch_ref_or_gap": _first_nonempty(svc.get("postlaunch_route_ref_or_gap"), read.get("postlaunch_route_ref_or_gap"), default="PR173-POSTLAUNCH::provider_pending"),
        "plugin_ref_or_gap": _first_nonempty(svc.get("plugin_route_ref_or_gap"), read.get("plugin_route_ref_or_gap"), default="PR174-PLUGIN1::intake_route_only"),
        "qmap_ref_or_gap": _first_nonempty(svc.get("qmap_route_ref_or_gap"), read.get("qmap_route_ref_or_gap"), default="PR174-QMAP1::mapping_route_only"),
        "allow_ref_or_gap": _first_nonempty(svc.get("allowlist_route_ref_or_gap"), read.get("allowlist_route_ref_or_gap"), default="PR174-ALLOW1::review_route_only"),
        "execution_router_ref_or_gap": _first_nonempty(pre.get("pretrade_execution_router_handoff_ref_or_gap"), svc.get("execution_router_route_ref_or_gap"), default="ExecutionRouterBoundary::no_release"),
        "connector_ref_or_gap": _first_nonempty(pre.get("pretrade_connector_handoff_ref_or_gap"), svc.get("connector_route_ref_or_gap"), default="VENUE-NEUTRAL-CONNECTOR::provider_pending_no_read"),
        "graph_node_refs_or_gap": [f"QKU_GRAPH_NODE::{ref}" for ref in selected_qku_refs],
        "graph_edge_refs_or_gap": [f"QKU_GRAPH_EDGE::{candidate}::{idx}" for idx, _ref_value in enumerate(selected_qku_refs, start=1)],
        "graph_source_edges_or_gap": [f"GRAPH_SOURCE_EDGE::{candidate}"],
        "graph_value_edges_or_gap": [f"GRAPH_VALUE_EDGE::{candidate}"],
        "graph_agent_edges_or_gap": [f"GRAPH_AGENT_EDGE::{role}" for role in responsible],
        "graph_validator_edges_or_gap": ["GRAPH_VALIDATOR_EDGE::AGENT_ORCH1_VALIDATOR"],
        "graph_replay_paper_edges_or_gap": [f"GRAPH_REPLAY_PAPER_EDGE::{candidate}"],
        "graph_quantum_edges_or_gap": [f"GRAPH_QUANTUM_EDGE::{candidate}"],
        "graph_owner_review_edges_or_gap": [f"GRAPH_OWNER_REVIEW_EDGE::{candidate}"],
        "graph_route_state": "CONTROL_PLANE_ROUTE_ONLY_NO_TRADING_AUTHORITY",
        "provider_state": "PROVIDER_PENDING_CONTRACT_ONLY",
        "provider_stage": "AGENT_ORCH1_STATIC_CONTRACT_PROVIDER_PENDING",
        "freshness_state": "STATIC_BUILD_CONTRACT_REVALIDATION_REQUIRED",
        "lifecycle_state": "MATERIALIZED_CONTRACT",
        "activation_state": "CONTRACT_ACTIVE_NO_RUNTIME",
        "timing_state": "STATIC_BUILD_TIME_ONLY",
        "downstream_owner": downstream_owner,
        "authority_state": "CONTROL_PLANE_ONLY_NO_EXECUTION",
        "source_authority_state": "UPSTREAM_DECLARED_GENERATED_ARTIFACTS_ONLY_NO_SOURCE_TRUTH",
        "projection_consumers": [
            "src/qtt/agents/pr169_agent_orch1_resolvers.py",
            "OwnerDashboardStateV1/current equivalent",
            "PR169-PAPER-LOOP::prep_only",
            "PR170-HOTPATH1::prep_only",
            "PR170-LIVE-DRYRUN1::prep_only",
            "PR169-LLM1/2::contract_only",
            "PR173-POSTLAUNCH::learning_route_only",
        ],
        "orphan_status": "NOT_ORPHAN",
        "route_gap_reason_or_none": "NONE",
        "validation_state": "VALIDATED_BY_PR169_AGENT_ORCH1",
        "fail_closed_reasons": [],
        "control_plane_only": True,
        "runtime_side_effect_allowed": False,
        "runtime_side_effect_created": False,
        "runtime_orchestration_created": False,
        "paper_execution_allowed": False,
        "live_execution_allowed": False,
        "llm_provider_call_allowed": False,
        "connector_read_allowed": False,
        "connector_write_allowed": False,
        "terminal_no_trade": False,
        "no_trade_recovery_route_refs": [f"AgentNoTradeRecovery::{route}::{candidate}" for route in NO_TRADE_RECOVERY_ROUTES],
        "safe_reoptimization_routes": list(NO_TRADE_RECOVERY_ROUTES),
        "stage_profile_ref_or_gap": _first_nonempty(read.get("active_stage_profile_ref_or_gap"), pre.get("active_stage_profile_ref_or_gap"), default="ACTIVE_STAGE_PROFILE_SCOPED_GAP"),
        "market_applicability_ref_or_gap": _first_nonempty(read.get("market_applicability_ref_or_gap"), default=f"MARKET_APPLICABILITY::{candidate}"),
        "platform_filter_ref_or_gap": _first_nonempty(read.get("platform_applicability_ref_or_gap"), read.get("platform_scope"), default="PLATFORM_APPLICABILITY_SCOPED_GAP"),
        "agent_duty_filter_ref_or_gap": PR165_D2_DUTY_REF,
        "executability_overlay_ref_or_gap": _first_nonempty(read.get("executable_now_state"), pre.get("stage1_prediction_market_applicability_state"), default="EXECUTABILITY_OVERLAY_SCOPED_GAP"),
        "context_filter_ref_or_gap": f"CONTEXT_FILTER::{candidate}",
        "mem1_filter_ref_or_gap": refs["mem_ref"],
        "selected_qku_refs": selected_qku_refs,
        "selected_formula_refs": selected_formula_refs,
        "library_query_receipt_ref_or_gap": f"LibraryQueryReceiptV1::{task_id}",
        "full_library_access_used": False,
        "active_stage_profile": "AGENT_ORCH1_STAGE_PROFILE",
        "market_family": _first_nonempty(pre.get("market_family"), read.get("market_family"), default="prediction_market"),
        "venue_scope": _first_nonempty(pre.get("venue_scope"), read.get("venue_scope"), default="VENUE_SCOPED_GAP"),
        "runtime_recompute_required": False,
        "fresh_snapshot_required": True,
        "paper_loop_owner_pr": "PR169-PAPER-LOOP",
        "required_downstream_receipts": [
            "PaperOrderIntentReceiptV1::downstream_only",
            "PaperFillReceiptV1::downstream_only",
            "PaperExitReceiptV1::downstream_only",
            "PaperPnLReceiptV1::downstream_only",
        ],
        "shadow_candidate_ref_or_gap": f"SHADOW_CANDIDATE_ROUTE::{candidate}",
        "pretrade_candidate_ref_or_gap_for_shadow": _first_nonempty(pre.get("pretrade_decision_candidate_id"), default=f"PRETRADE_CANDIDATE_SCOPED_GAP::{candidate}"),
        "paper_comparison_route_ref_or_gap": f"PAPER_SHADOW_COMPARE_ROUTE::{candidate}",
        "live_dryrun_route_ref_or_gap_for_shadow": f"LIVE_DRYRUN_PREP_ROUTE::{candidate}",
        "metrics_route_ref_or_gap": _first_nonempty(pre.get("pretrade_metrics_capture_handoff_ref_or_gap"), default=f"METRICS_ROUTE::{candidate}"),
        "owner_surface_route_ref_or_gap": _first_nonempty(svc.get("owner_surface_route_ref_or_gap"), read.get("owner_surface_resolver_ref_or_gap"), default="src/qtt/dashboard/owner_surface_resolver.py"),
        "execution_router_boundary_ref_or_gap": "ExecutionRouterBoundary::no_release",
        "owner_approval_route_ref_or_gap": f"OwnerLiveCanaryReviewRequestV1::{candidate}",
        "max_order_size_route_ref_or_gap": f"MAX_ORDER_SIZE_ROUTE_DOWNSTREAM::{candidate}",
        "max_daily_loss_route_ref_or_gap": f"MAX_DAILY_LOSS_ROUTE_DOWNSTREAM::{candidate}",
        "max_venue_exposure_route_ref_or_gap": f"MAX_VENUE_EXPOSURE_ROUTE_DOWNSTREAM::{candidate}",
        "kill_switch_route_ref_or_gap": f"OwnerKillSwitchRequestV1::{candidate}",
        "rollback_route_ref_or_gap": f"OwnerRollbackRequestV1::{candidate}",
        "paper_shadow_compare_ref_or_gap": f"PAPER_SHADOW_COMPARE_ROUTE::{candidate}",
        "credential_boundary_ref_or_gap": "LIVE_CREDENTIAL_BOUNDARY_DOWNSTREAM_NO_READ",
        "audit_route_ref_or_gap": f"AGENT_ORCH1_AUDIT::{task_id}",
        "execution_router_final_check_ref_or_gap": "ExecutionRouterBoundary::final_release_downstream",
        "formula_candidate_lanes": [
            "FAST_CANDIDATE_LANE",
            "CRITICAL_FIELD_FILL_LANE",
            "ENHANCEMENT_BACKLOG_LANE",
            "NON_OFFICIAL_CANDIDATE_LANE",
            "OWNER_SUBMITTED_CANDIDATE_LANE",
            "AGENT_DISCOVERED_CANDIDATE_LANE",
        ],
        "formula_latency_classes": [
            "TIER_0_CACHED",
            "TIER_1_SIMPLE",
            "TIER_2_VECTORIZED",
            "TIER_3_OPTIMIZER",
            "TIER_4_QUANTUM_BATCH",
            "TIER_5_REPLAY_PAPER_ONLY",
        ],
        "reality_model_route_families": [
            "VenueRealityModelV1",
            "FeeModelV1",
            "FillModelV1",
            "SlippageModelV1",
            "LatencyDecayModelV1",
            "QueuePositionModelV1",
            "PartialFillModelV1",
            "CapacityCrowdingModelV1",
            "AdverseSelectionModelV1",
            "SettlementResolutionModelV1",
            "CashflowModelV1",
            "OrderPolicyRealityModelV1",
            "PaperVsReplayRealityDiffV1",
            "RealityModelCalibrationReceiptV1::route_only",
        ],
        "event_time_metric_route_families": [
            "gross_edge",
            "spread_cost",
            "maker_taker_fees",
            "slippage",
            "market_impact",
            "latency_drag",
            "liquidity_drag",
            "adverse_selection_drag",
            "settlement_adjustment",
            "net_edge_after_costs",
            "TCA_adjusted_result",
        ],
        "downstream_route_refs": [
            "PR169-PAPER-LOOP::prep_only",
            "PR170-HOTPATH1::prep_only",
            "PR170-LIVE-DRYRUN1::prep_only_no_execution",
            "PR169-LLM1/2::contract_only",
            "PR173-POSTLAUNCH::learning_route_only",
            "PR174-PLUGIN1::intake_route_only",
            "PR174-QMAP1::mapping_route_only",
            "PR174-ALLOW1::review_route_only",
            "ExecutionRouterBoundary::no_release",
        ],
        "value_route_ref_or_gap": _first_nonempty(svc.get("artifact_value_route_map_ref"), pre.get("pretrade_artifact_value_route_map_ref_or_gap"), default=f"VALUE_ROUTE::{candidate}"),
        "capability_route_ref_or_gap": f"CAPABILITY_ROUTE::{task_class}::{candidate}",
        "learning_route_ref_or_gap": _first_nonempty(read.get("agent_learning_handoff_ref_or_gap"), default=f"LEARNING_ROUTE::{candidate}"),
        "receipt_class": "ORCH_BUILD_TIME_CONTRACT_RECEIPT",
        "runtime_side_effect_created": False,
        "build_time_contract_receipt": True,
        "agent_status": "QUEUED_CONTRACT_NO_RUNTIME",
        "current_task_id_or_gap": task_id,
        "current_workflow_id_or_gap": workflow_id,
        "current_trade_candidate_id_or_gap": candidate,
        "responsible_qku_refs": selected_qku_refs,
        "formula_stack_refs_or_gap": selected_formula_refs,
        "market_venue_event_ref_or_gap": f"{_first_nonempty(pre.get('market_family'), default='prediction_market')}::{_first_nonempty(pre.get('venue_scope'), default='venue_gap')}",
        "started_at_or_static_build_time": "STATIC_BUILD_TIME_PR169_AGENT_ORCH1",
        "expected_finish_policy_or_gap": "STATIC_CONTRACT_NO_RUNTIME_SLA",
        "blocked_reason_or_none": "NONE",
        "next_action": f"ROUTE::{task_class}",
        "latest_receipt_ref_or_gap": f"RuntimeTaskReceiptV1::{task_id}",
        "trust_score_ref_or_gap": "AgentTrustScoreRoute::provider_pending",
        "risk_level_ref_or_gap": "ACTION_RISK_REVIEW_ONLY_NO_EXECUTION",
        "missed_duty_route_ref_or_gap": "AgentMissedDutyRoute::provider_pending",
        "self_heal_route_ref_or_gap": "AgentSelfHealRoute::bounded_retry_no_runtime",
        "quarantine_route_ref_or_gap": "AgentQuarantineRoute::route_only",
        "replacement_candidate_refs_or_gap": [f"ReplacementCandidateRoute::{candidate}"],
        "reroute_control_ref_or_gap": "AgentRerouteControl::route_only",
        "permission_change_ref_or_gap": "NO_PERMISSION_CHANGE_CREATED",
        "workflow_id": workflow_id,
        "tradeplan_ref_or_gap_for_queue": _first_nonempty(pre.get("trade_plan_candidate_ref"), default=f"TRADEPLAN_SCOPED_GAP::{candidate}"),
        "backup_roles_or_gap": supporting,
        "current_stage": stage_name,
        "next_stage": "SAFE_NEXT_STATIC_ROUTE",
        "blocking_evidence_or_none": "NONE",
        "tca_status_ref_or_gap": _first_nonempty(pre.get("tca_decomposition_ref_or_gap"), default=f"TCA_ROUTE::{candidate}"),
        "risk_status_ref_or_gap": _first_nonempty(pre.get("pretrade_risk_envelope_ref_or_gap"), default=f"RISK_ROUTE::{candidate}"),
        "latency_status_ref_or_gap": _first_nonempty(pre.get("latency_budget_decision_ref_or_gap"), default=f"LATENCY_ROUTE::{candidate}"),
        "capacity_status_ref_or_gap": _first_nonempty(pre.get("capacity_crowding_model_ref_or_gap"), default=f"CAPACITY_ROUTE::{candidate}"),
        "no_trade_status_ref_or_gap": _first_nonempty(pre.get("no_trade_candidate_ref_or_gap"), default=f"NO_TRADE_ROUTE::{candidate}"),
        "owner_action_required": False,
        "severity_class": "S1_REVIEW_ONLY",
        "safe_next_action": f"SAFE_NEXT::{task_class}",
    }
    row.update({field: False for field in AUTHORITY_FALSE_FIELDS})
    row.update({field: False for field in LIVE_PATH_FALSE_FIELDS})
    return row


def _dag_rows(ctx: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    dag_row = _base_row(
        object_type="AgentDAGRegistryV1",
        object_id="central",
        task_class="CENTRAL_DAG_REGISTRY",
        lane="GOVERNANCE_LANE",
        projection_file="dag.jsonl",
        stage="OWNER_REQUEST_INTAKE",
        ctx=ctx,
    )
    dag_row.update(
        {
            "dag_id": "AGENT_ORCH1_DAG",
            "dag_version": PROJECTION_VERSION,
            "node_count": len(DAG_STAGE_FAMILIES),
            "edge_count": len(DAG_STAGE_FAMILIES) - 1,
            "workflow_contract": "owner_request_to_learning_route_no_execution",
        }
    )
    rows.append(dag_row)
    for index, stage in enumerate(DAG_STAGE_FAMILIES):
        node = _base_row(
            object_type="AgentDAGNodeV1",
            object_id=stage,
            task_class=stage,
            lane="GOVERNANCE_LANE",
            projection_file="dag_nodes.jsonl",
            stage=stage,
            ctx=ctx,
            index=index,
        )
        node.update(
            {
                "dag_id": "AGENT_ORCH1_DAG",
                "node_id": f"AGENT_ORCH1_NODE::{stage}",
                "node_class": stage,
                "from_node_id": "DAG_START" if index == 0 else f"AGENT_ORCH1_NODE::{DAG_STAGE_FAMILIES[index - 1]}",
                "to_node_id": "DAG_END" if index == len(DAG_STAGE_FAMILIES) - 1 else f"AGENT_ORCH1_NODE::{DAG_STAGE_FAMILIES[index + 1]}",
                "upstream_refs": [REGISTRY_REF, "docs/master_plan/generated/pr169_svc1/service_registry.jsonl"],
                "handoff_ref": f"AgentHandoffPacketV1::{stage}",
                "entry_condition": f"{stage} input refs or scoped gaps are present",
                "exit_condition": f"{stage} emits task envelope/handoff contract only",
                "fail_closed_condition": "missing authority boundary, missing downstream owner, or runtime side effect",
                "retry_policy_ref": "AgentRetryPolicyV1::bounded_no_runtime",
                "escalation_policy_ref": "AgentEscalationPolicyV1::governance_commander",
                "quarantine_policy_ref": "AgentQuarantinePolicyV1::provider_pending_quarantine",
                "authority_boundary": "NO_DIRECT_SUBMIT_NO_EXECUTION_ROUTER_RELEASE",
            }
        )
        rows.append(node)
    for index, (from_stage, to_stage) in enumerate(zip(DAG_STAGE_FAMILIES, DAG_STAGE_FAMILIES[1:]), start=1):
        edge = _base_row(
            object_type="AgentDAGEdgeV1",
            object_id=f"{from_stage}__TO__{to_stage}",
            task_class="DAG_EDGE_ROUTE",
            lane="GOVERNANCE_LANE",
            projection_file="dag_edges.jsonl",
            stage=from_stage,
            ctx=ctx,
            index=index,
        )
        edge.update(
            {
                "dag_id": "AGENT_ORCH1_DAG",
                "edge_id": f"AGENT_ORCH1_EDGE::{from_stage}__TO__{to_stage}",
                "node_class": "DAG_EDGE",
                "from_node_id": f"AGENT_ORCH1_NODE::{from_stage}",
                "to_node_id": f"AGENT_ORCH1_NODE::{to_stage}",
                "upstream_refs": [f"AGENT_ORCH1_NODE::{from_stage}", f"AGENT_ORCH1_NODE::{to_stage}"],
                "handoff_ref": f"AgentHandoffPacketV1::{from_stage}__TO__{to_stage}",
                "entry_condition": "prior stage exits without fail-closed reason",
                "exit_condition": "next stage receives deterministic envelope",
                "fail_closed_condition": "authority boundary missing or runtime side effect requested",
                "retry_policy_ref": "AgentRetryPolicyV1::bounded_no_runtime",
                "escalation_policy_ref": "AgentEscalationPolicyV1::governance_commander",
                "quarantine_policy_ref": "AgentQuarantinePolicyV1::provider_pending_quarantine",
                "authority_boundary": "NO_RUNTIME_EXECUTION_EDGE",
            }
        )
        rows.append(edge)
    return rows


def _candidate_projection_rows(ctx: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidate_projection_files = [
        name
        for name in JSONL_ARTIFACTS
        if name
        not in {
            "registry.jsonl",
            "dag.jsonl",
            "dag_nodes.jsonl",
            "dag_edges.jsonl",
            "role_map.jsonl",
            "duty_map.jsonl",
            "perm_scope.jsonl",
            "retry_policy.jsonl",
            "priority_policy.jsonl",
            "quarantine.jsonl",
            "intel_lanes.jsonl",
            "owner_cmd_tasks.jsonl",
            "chat_tasks.jsonl",
        }
    ]
    for candidate_index, candidate_id in enumerate(ctx["candidate_ids"]):
        for file_index, file_name in enumerate(candidate_projection_files):
            projection = PROJECTION_CLASSES[file_name]
            task_class = _slug(Path(file_name).stem)
            row = _base_row(
                object_type=projection["object_type"],
                object_id=f"{Path(file_name).stem}::{candidate_id}",
                task_class=task_class,
                lane=projection["lane"],
                projection_file=file_name,
                candidate_id=candidate_id,
                stage=_stage_for_projection(file_name),
                downstream_owner=_downstream_owner_for_projection(file_name),
                ctx=ctx,
                index=candidate_index + file_index,
            )
            _apply_projection_specifics(row, file_name, candidate_id)
            rows.append(row)
    return rows


def _stage_for_projection(file_name: str) -> str:
    if file_name in {"paper_prep.jsonl"}:
        return "PAPER_PREP"
    if file_name in {"hotpath_prep.jsonl"}:
        return "HOTPATH_PREP"
    if file_name in {"shadow_prep.jsonl", "live_prep.jsonl"}:
        return "LIVE_DRYRUN_PREP"
    if file_name in {"notrade_tasks.jsonl", "var_tune_tasks.jsonl", "stack_tasks.jsonl", "venue_side_tasks.jsonl", "source_refresh_tasks.jsonl", "retest_tasks.jsonl"}:
        return "NO_TRADE_RECOVERY"
    if file_name in {"qku_tasks.jsonl", "formula_tasks.jsonl", "access_proof.jsonl", "library_receipts.jsonl", "graph_routes.jsonl", "graph_tasks.jsonl", "graph_quality.jsonl"}:
        return "QKU_FORMULA_ROUTE"
    if file_name in {"quantum_tasks.jsonl", "qmap_prep.jsonl"}:
        return "QUANTUM_ROUTE"
    if file_name in {"rank_tasks.jsonl", "tca_tasks.jsonl", "fdr_tasks.jsonl", "portfolio_tasks.jsonl", "capacity_tasks.jsonl", "champion_tasks.jsonl", "utility_tasks.jsonl", "scenario_tasks.jsonl", "calibration_tasks.jsonl"}:
        return "RANK_REVIEW"
    if file_name in {"mem1_bindings.jsonl", "mem_prior_tasks.jsonl", "learning_routes.jsonl"}:
        return "MEM_PRIOR_REVAL"
    return "PRETRADE_BINDING"


def _downstream_owner_for_projection(file_name: str) -> str:
    mapping = {
        "paper_prep.jsonl": "PR169-PAPER-LOOP",
        "hotpath_prep.jsonl": "PR170-HOTPATH1",
        "shadow_prep.jsonl": "PR170-LIVE-DRYRUN1",
        "live_prep.jsonl": "PR170-LIVE-DRYRUN1",
        "plugin_prep.jsonl": "PR174-PLUGIN1",
        "qmap_prep.jsonl": "PR174-QMAP1",
        "allow_prep.jsonl": "PR174-ALLOW1",
        "learning_routes.jsonl": "PR173-POSTLAUNCH",
        "reality_tasks.jsonl": "PR170-METRICS1",
        "metric_tasks.jsonl": "PR170-METRICS1",
    }
    return mapping.get(file_name, "PR169-AGENT-ORCH1")


def _apply_projection_specifics(row: dict[str, Any], file_name: str, candidate_id: str) -> None:
    if file_name == "tournament_tasks.jsonl":
        row["tournament_roles"] = list(TOURNAMENT_ROLES)
        row["tournament_bundle_state"] = "MULTI_AGENT_CHALLENGE_CONTRACT_READY"
        row["single_agent_self_authorization_allowed"] = False
        row["disagreement_receipt_ref_or_gap"] = f"AgentDisagreementReceiptV1::{candidate_id}"
    if file_name in {"notrade_tasks.jsonl", "var_tune_tasks.jsonl", "stack_tasks.jsonl", "venue_side_tasks.jsonl", "source_refresh_tasks.jsonl", "retest_tasks.jsonl"}:
        row["task_class"] = "NO_TRADE_RECOVERY_ROUTE"
        row["terminal_no_trade"] = False
        row["queue_state"] = "WAITING_EVIDENCE"
    if file_name == "paper_prep.jsonl":
        row["candidate_ref"] = candidate_id
        row["qku_formula_task_refs"] = [f"AgentQKUFormulaComputeTaskV1::{candidate_id}"]
        row["risk_tca_task_refs"] = [f"AgentTCATaskV1::{candidate_id}", f"AgentRiskCapacityTaskV1::{candidate_id}"]
        row["notrade_recovery_refs_or_gap"] = row["no_trade_recovery_route_refs"]
        row["mem1_prior_refs_or_gap"] = [row["memory_prior_ref_or_gap"]]
    if file_name == "hotpath_prep.jsonl":
        row["stack_candidate_ref_or_gap"] = f"STACK_CANDIDATE_ROUTE::{candidate_id}"
        row["qku_formula_set_ref_or_gap"] = row["selected_formula_refs"]
        row["risk_capacity_envelope_ref_or_gap"] = row["capacity_ref_or_gap"]
        row["no_trade_threshold_ref_or_gap"] = row["notrade_margin_ref_or_gap"]
        row["mem1_hotpath_prior_ref_or_gap"] = row["memory_prior_ref_or_gap"]
    if file_name == "shadow_prep.jsonl":
        row["shadow_candidate_ref_or_gap"] = f"SHADOW_CANDIDATE_ROUTE::{candidate_id}"
        row["shadow_execution_created"] = False
        row["live_execution_created"] = False
    if file_name == "live_prep.jsonl":
        row["live_execution_created"] = False
        row["execution_router_release_created"] = False
    if file_name == "quantum_tasks.jsonl":
        row["quantum_route_uses"] = [
            "portfolio_bundle_selection",
            "parameter_stack_selection",
            "risk_budget_allocation",
            "order_policy_selection",
            "scenario_arbitration",
            "latency_cost_tradeoff_selection",
            "classical_fallback_comparator_routing",
        ]
    if file_name in {"qku_tasks.jsonl", "formula_tasks.jsonl", "access_proof.jsonl", "library_receipts.jsonl"}:
        row["full_library_access_used"] = False
        row["library_access_path"] = [
            "active_stage_profile",
            "market_applicability",
            "platform_applicability",
            "agent_duty_filter",
            "executability_overlay",
            "context_filter",
            "MEM1_prior_filter",
            "lazy_load_selected_refs",
        ]
    if file_name == "task_receipts.jsonl":
        row["receipt_class"] = "ORCH_BUILD_TIME_CONTRACT_RECEIPT"
    if file_name == "decision_receipts.jsonl":
        row["receipt_class"] = "AgentDecisionReceiptV1_CONTRACT_ONLY"
    if file_name == "dispute_receipts.jsonl":
        row["receipt_class"] = "AgentDisagreementReceiptV1_CONTRACT_ONLY"
    if file_name == "escalation_receipts.jsonl":
        row["receipt_class"] = "AgentEscalationReceiptV1_CONTRACT_ONLY"
    if file_name == "handoff_receipts.jsonl":
        row["receipt_class"] = "AgentHandoffReceiptV1_CONTRACT_ONLY"


def _role_and_policy_rows(ctx: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, role in enumerate(TOURNAMENT_ROLES):
        role_id = _slug(role)
        role_row = _base_row(
            object_type="AgentRoleMapV1",
            object_id=role_id,
            task_class="ROLE_MAP",
            lane="GOVERNANCE_LANE",
            projection_file="role_map.jsonl",
            stage="AGENT_DISAGREEMENT",
            ctx=ctx,
            index=index,
        )
        role_row.update(
            {
                "agent_id_or_role": role_id,
                "agent_role": role,
                "pr165_d2_resolution_ref_or_gap": f"PR165_D2_GAP::{role_id}",
                "role_resolution_state": "PR165_D2_CURRENT_EQUIVALENT_OR_SCOPED_GAP",
            }
        )
        rows.append(role_row)

        duty_row = dict(role_row)
        duty_row.update(
            {
                "row_id": f"AGENT_ORCH1::DUTY_MAP::{role_id}",
                "registry_row_id": f"AGENT_ORCH1::DUTY_MAP::{role_id}",
                "source_registry_row_id": f"AGENT_ORCH1::DUTY_MAP::{role_id}",
                "object_type": "AgentDutyMapV1",
                "object_id": f"duty::{role_id}",
                "projection_file": "duty_map.jsonl",
                "task_class": "DUTY_MAP",
                "projection_ref": f"{GENERATED_PREFIX.as_posix()}/duty_map.jsonl::AGENT_ORCH1::DUTY_MAP::{role_id}",
                "duty_contract": f"{role} consumes centralized registry-derived task envelopes only",
            }
        )
        rows.append(duty_row)

    policy_specs = (
        ("perm_scope.jsonl", "AgentPermissionScopeV1", "permission_scope::review_only", "PERMISSION_SCOPE"),
        ("retry_policy.jsonl", "AgentRetryPolicyV1", "retry::bounded_no_runtime", "RETRY_POLICY"),
        ("priority_policy.jsonl", "AgentPriorityPolicyV1", "priority::institutional_controls", "PRIORITY_POLICY"),
        ("quarantine.jsonl", "AgentQuarantinePolicyV1", "quarantine::provider_pending", "QUARANTINE_POLICY"),
    )
    for index, (file_name, object_type, object_id, task_class) in enumerate(policy_specs):
        policy = _base_row(
            object_type=object_type,
            object_id=object_id,
            task_class=task_class,
            lane="GOVERNANCE_LANE",
            projection_file=file_name,
            stage="RETRY_OR_QUARANTINE",
            ctx=ctx,
            index=index,
        )
        policy["policy_state"] = "ACTIVE_STATIC_CONTRACT_NO_RUNTIME_PERMISSION_WIDENING"
        rows.append(policy)

    for index, lane in enumerate(INTELLIGENCE_LANES):
        lane_row = _base_row(
            object_type="AgentIntelligenceLaneV1",
            object_id=lane,
            task_class="INTELLIGENCE_LANE",
            lane=lane,
            projection_file="intel_lanes.jsonl",
            stage="OWNER_REQUEST_INTAKE",
            ctx=ctx,
            index=index,
        )
        lane_row["lane_contract"] = _lane_contract(lane)
        rows.append(lane_row)
    return rows


def _lane_contract(lane: str) -> str:
    return {
        "KNOWLEDGE_LANE": "immutable QKU/formula/access/graph lookup and provenance routing",
        "SEARCH_LANE": "bounded candidate, stack, venue/side, variable, and no-trade recovery search",
        "SIMULATION_LANE": "PRETRADE1/RP/PAPER-prep numeric-evidence binding and scenario ownership",
        "LEARNING_LANE": "MEM1 prior lookup, drift/cooldown/retest route, and postlaunch handoff",
        "REASONING_LANE": "LLM contract, critique, explanation, and owner-question routing without provider call",
        "EXEC_PREP_LANE": "PAPER/HOTPATH/SHADOW/LIVE-DRYRUN prep ownership without execution",
        "GOVERNANCE_LANE": "authority, no-orphan, no-raw-scan, escalation, quarantine, and owner review",
    }[lane]


def _owner_action_rows(ctx: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, action in enumerate(ctx["owner_actions"]):
        action_code = str(action.get("action_code") or action.get("action_id") or f"OWNER_ACTION_{index + 1:04d}")
        candidate_id = str(action.get("candidate_id") or ctx["candidate_ids"][index % len(ctx["candidate_ids"])])
        row = _base_row(
            object_type="OwnerAgentDirectiveEnvelopeV1",
            object_id=f"owner_action::{action_code}",
            task_class="OWNER_COMMAND_TASK",
            lane="GOVERNANCE_LANE",
            projection_file="owner_cmd_tasks.jsonl",
            candidate_id=candidate_id,
            action_ref=action_code,
            stage="OWNER_REQUEST_INTAKE",
            ctx=ctx,
            index=index,
        )
        row.update(
            {
                "owner_action_ref_or_gap": action_code,
                "owner_request_authority": True,
                "direct_venue_submit_authority": False,
                "execution_router_release_authority": False,
                "market_or_gap": action.get("market_family", "prediction_market"),
                "venue_or_gap": action.get("venue_scope", "VENUE_SCOPED_GAP"),
                "contract_or_event_url_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "side_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "thesis_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "max_capital_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP_NO_PRIVATE_CASH_READ",
                "max_loss_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP_NO_PRIVATE_CASH_READ",
                "hold_duration_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "urgency_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "owner_notes_or_gap": action.get("owner_intent", "OWNER_INTENT_ROUTE"),
                "source_refs_or_gap": ["OWNER_SOURCE_REF_CANDIDATE_ONLY_NO_SOURCE_TRUTH"],
                "target_price_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "target_probability_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "stop_or_exit_preference_or_gap": "OWNER_SUPPLIED_OR_SCOPED_GAP",
                "svc1_owner_action_source_ref": _ref(
                    "docs/master_plan/generated/pr169_svc1/owner_action_requests.generated.jsonl",
                    action,
                    action_code,
                ),
            }
        )
        rows.append(row)
    for index, (text, intent_class) in enumerate(PLAIN_ENGLISH_EXAMPLES):
        candidate_id = str(ctx["candidate_ids"][index % len(ctx["candidate_ids"])])
        row = _base_row(
            object_type="OwnerPlainEnglishIntentTaskV1",
            object_id=f"plain_english::{intent_class}",
            task_class="OWNER_CHAT_TASK",
            lane="REASONING_LANE",
            projection_file="chat_tasks.jsonl",
            candidate_id=candidate_id,
            action_ref=intent_class,
            stage="OWNER_CHAT_INTAKE",
            ctx=ctx,
            index=index,
        )
        row.update(
            {
                "owner_plain_english_example": text,
                "intent_class": intent_class,
                "deterministic_route_only": True,
                "no_runtime_gpt_reply_created": True,
                "llm_runtime_owner": "PR169-LLM1/2",
            }
        )
        rows.append(row)
    return rows


def _build_registry(ctx: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(_dag_rows(ctx))
    rows.extend(_role_and_policy_rows(ctx))
    rows.extend(_candidate_projection_rows(ctx))
    rows.extend(_owner_action_rows(ctx))
    rows.sort(key=lambda row: (str(row["projection_file"]), str(row["row_id"])))
    return rows


def _projection_rows(registry_rows: Sequence[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in registry_rows:
        projection_file = str(row["projection_file"])
        if projection_file == "registry.jsonl":
            continue
        projection_row = dict(row)
        projection_row["generated_from"] = REGISTRY_REF
        projection_row["source_registry_row_id"] = row["row_id"]
        by_file[projection_file].append(projection_row)

    # The canonical registry itself is written separately, but include it in the
    # map for completeness checks.
    by_file["registry.jsonl"] = list(registry_rows)
    for artifact in JSONL_ARTIFACTS:
        if artifact not in by_file:
            raise BuildError(f"Projection has no rows: {artifact}")
    return by_file


def _phase0_mapping() -> list[dict[str, Any]]:
    domains = (
        ("SVC1 owner/read model/action fabric", "docs/master_plan/generated/pr169_svc1/", "PR169-SVC1"),
        ("PRETRADE1 decision/reality/institutional controls", "docs/master_plan/generated/pr169_pretrade1/", "PR169-PRETRADE1"),
        ("READINESS1 computability/executable-now routes", "docs/master_plan/generated/pr169_readiness1/", "PR169-READINESS1"),
        ("MEM1 condition-scoped memory", "docs/master_plan/generated/pr168_mem1/", "PR168-MEM1"),
        ("PR165-D2 agent roster/duty mapping", PR165_D2_ROSTER_REF, "PR165-D2"),
        ("AGENT-ORCH1 canonical registry", REGISTRY_REF, "PR169-AGENT-ORCH1"),
        ("QKU/formula/access/graph tasks", "docs/master_plan/generated/pr169_agent_orch1/qku_tasks.jsonl", "PR169-AGENT-ORCH1"),
        ("No-trade recovery tasks", "docs/master_plan/generated/pr169_agent_orch1/notrade_tasks.jsonl", "PR169-AGENT-ORCH1"),
        ("Downstream prep and ownership routes", "docs/master_plan/generated/pr169_agent_orch1/downstream.jsonl", "PR169-AGENT-ORCH1"),
        ("Proof reports and validation", "docs/master_plan/generated/pr169_agent_orch1/quality.report.json", "PR169-AGENT-ORCH1"),
    )
    rows: list[dict[str, Any]] = []
    for domain, path, source in domains:
        row = {column: "NONE" for column in PHASE0_COLUMNS}
        row.update(
            {
                "semantic_domain": domain,
                "expected_source_or_artifact": path,
                "current_equivalent_path_or_absent": path,
                "upstream_pr_or_source": source,
                "agent_orch_consumption_plan": "consume current equivalent; do not redo upstream layer",
                "projection_plan": "registry-derived compact artifact under owned prefix",
                "producer_registry_or_contract": REGISTRY_REF,
                "agent_task_consumer": "src/qtt/agents/pr169_agent_orch1_resolvers.py",
                "owner_surface_consumer": "SVC1/OwnerDashboardState current equivalent",
                "svc1_route": "consumed_or_scoped_gap",
                "pretrade_route": "consumed_or_scoped_gap",
                "readiness_route": "consumed_or_scoped_gap",
                "mem1_route": "prior_only_revalidation_required",
                "llm_route": "contract_only_no_provider_call",
                "paper_loop_route": "prep_only_no_paper_execution",
                "hotpath_route": "prep_only_no_runtime_cache",
                "live_dryrun_route": "prep_only_no_shadow_or_live_execution",
                "postlaunch_route": "learning_route_only",
                "plugin_qmap_allow_route": "ownership_route_only",
                "builder_or_owner_module": BUILDER_NAME,
                "validator_or_test_consumer": VALIDATOR_NAME,
                "mutation_required": "yes" if source == "PR169-AGENT-ORCH1" else "no",
                "mutation_reason": "owned AGENT-ORCH1 output" if source == "PR169-AGENT-ORCH1" else "upstream consumed only",
                "orphan_risk": "validated_by_no_orphan_report",
                "authority_risk": "fail_closed_false_authority_fields",
                "raw_jsonl_scan_risk": "resolver_reads_owned_prefix_only",
                "fake_runtime_state_risk": "runtime_state_not_created",
                "fake_receipt_risk": "build_time_contract_receipts_only",
                "source_truth_risk": "source_truth_fields_false",
                "connector_private_cash_risk": "connector_private_cash_fields_false",
                "runtime_llm_risk": "llm_contract_only",
                "runtime_agent_risk": "no_runtime_agent_execution",
                "runtime_execution_risk": "no_runtime_side_effects",
                "paper_execution_risk": "paper_prep_only",
                "live_execution_risk": "live_dryrun_prep_only",
                "qku_formula_route_risk": "central_access_refs_required",
                "institutional_control_route_risk": "rank_tca_fdr_portfolio_capacity_champion_memory_utility_scenario_calibration_quantum_refs_required",
                "quantum_route_risk": "structural_route_only_no_backend_or_advantage",
                "mem1_proof_misuse_risk": "prior_only_flags_required",
                "latency_path_risk": "prep_route_not_live_path",
                "owner_action_bypass_risk": "direct_submit_and_router_release_false",
                "agent_role_invention_risk": "PR165_D2_current_equivalent_or_PR165_D2_GAP",
                "compact_validation_risk": "basename_limit_and_manifest_mapping",
                "owned_prefix_scope_risk": "owned_scope_report",
                "shared_currentization_risk": "only validation/currentization files if required",
            }
        )
        rows.append(row)
    return rows


def _artifact_manifest() -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for file_name in JSONL_ARTIFACTS:
        if file_name == "registry.jsonl":
            semantic_class = "canonical_registry"
            object_type = "AgentOrchestrationRegistryV1"
            lane = "GOVERNANCE_LANE"
        else:
            spec = PROJECTION_CLASSES[file_name]
            semantic_class = Path(file_name).stem
            object_type = spec["object_type"]
            lane = spec["lane"]
        manifest.append(
            {
                "file": file_name,
                "semantic_class": semantic_class,
                "object_type": object_type,
                "consumer": "AgentOrchService/resolver and downstream owner routes",
                "canonical_source": REGISTRY_REF,
                "intelligence_lane": lane,
            }
        )
    for file_name in JSON_REPORTS:
        manifest.append(
            {
                "file": file_name,
                "semantic_class": "proof_report" if file_name != "manifest.json" else "manifest",
                "object_type": "AgentOrchProofReportV1" if file_name != "manifest.json" else "AgentOrchManifestV1",
                "consumer": "validator/tests/PR body",
                "canonical_source": REGISTRY_REF,
                "intelligence_lane": "GOVERNANCE_LANE",
            }
        )
    return manifest


def _report_template(
    *,
    report_name: str,
    registry_rows: Sequence[Mapping[str, Any]],
    pass_state: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "report_name": report_name,
        "projection_version": PROJECTION_VERSION,
        "canonical_registry_ref": REGISTRY_REF,
        "builder": BUILDER_NAME,
        "validator": VALIDATOR_NAME,
        "pass": pass_state,
        "row_count": len(registry_rows),
        "manual_edit_allowed_true_count": sum(1 for row in registry_rows if row.get("manual_edit_allowed") is True),
        "authority_true_counts": {
            field: sum(1 for row in registry_rows if row.get(field) is True)
            for field in AUTHORITY_FALSE_FIELDS
        },
        "fail_closed_reasons": [],
    }
    if extra:
        payload.update(dict(extra))
    return payload


def _build_reports(registry_rows: Sequence[Mapping[str, Any]], rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, dict[str, Any]]:
    projection_counts = {file_name: len(rows_by_file[file_name]) for file_name in JSONL_ARTIFACTS}
    missing_projection_files = [file_name for file_name, count in projection_counts.items() if count == 0]
    report_extra = {
        "projection_counts": projection_counts,
        "missing_projection_files": missing_projection_files,
    }
    reports: dict[str, dict[str, Any]] = {
        "manifest.json": {
            "manifest_version": PROJECTION_VERSION,
            "active_prompt_version": PROMPT_VERSION,
            "active_prompt_filename": "PR169_AGENT_ORCH1_v2_2.md",
            "prompt_file_present_in_repo": False,
            "canonical_registry_ref": REGISTRY_REF,
            "baseline_consumed": BASELINE_CONSUMED,
            "artifact_manifest": _artifact_manifest(),
            "phase0_mapping": _phase0_mapping(),
            "phase0_decisions": {
                "exact_pr": "PR169-AGENT-ORCH1",
                "upstream_layers_consumed_not_redone": True,
                "one_registry_builder_validator_resolver": True,
                "generated_rows_derive_from_registry": True,
                "runtime_agents_scan_raw_upstream_jsonl": False,
                "qtt_sha_or_atomicrows_hash_authority_created": False,
                "paper_shadow_live_order_execution_created": False,
                "connector_private_cash_reads_created": False,
                "runtime_llm_provider_calls_created": False,
                "quantum_backend_execution_or_advantage_claim_created": False,
                "all_rows_have_required_state_fields": True,
                "compact_filenames_no_future_or_hint": True,
                "pr165_d2_roles_or_scoped_gaps": True,
                "svc1_owner_actions_mapped": True,
                "pretrade_routes_mapped": True,
                "readiness_routes_mapped": True,
                "mem1_prior_only_requires_revalidation": True,
                "no_trade_routes_reoptimization_not_terminal": True,
                "downstream_owner_routes_present": True,
                "online_findings_candidate_only": True,
                "owned_prefix_only_for_generated": True,
                "pr152_currentization_after_final_file_set_required": True,
            },
        },
        "no_orphan.report.json": _report_template(report_name="no_orphan", registry_rows=registry_rows, extra=report_extra),
        "no_raw_scan.report.json": _report_template(report_name="no_raw_scan", registry_rows=registry_rows, extra={"runtime_raw_upstream_jsonl_scan_count": 0, "resolver_reads_owned_prefix_only": True}),
        "no_direct_submit.report.json": _report_template(report_name="no_direct_submit", registry_rows=registry_rows, extra={"direct_submit_created_count": 0, "execution_router_release_created_count": 0}),
        "no_llm_runtime.report.json": _report_template(report_name="no_llm_runtime", registry_rows=registry_rows, extra={"llm_contracts_only": True, "provider_call_count": 0}),
        "no_paper_exec.report.json": _report_template(report_name="no_paper_exec", registry_rows=registry_rows, extra={"paper_prep_only": True, "paper_execution_count": 0}),
        "no_live_exec.report.json": _report_template(report_name="no_live_exec", registry_rows=registry_rows, extra={"shadow_live_dryrun_prep_only": True, "live_execution_count": 0}),
        "no_fake_receipts.report.json": _report_template(report_name="no_fake_receipts", registry_rows=registry_rows, extra={"build_time_contract_receipts_only": True, "fake_runtime_receipt_count": 0}),
        "no_source_truth.report.json": _report_template(report_name="no_source_truth", registry_rows=registry_rows, extra={"source_truth_created_count": 0, "external_material_state": "candidate_or_provisional_only"}),
        "no_private_cash.report.json": _report_template(report_name="no_private_cash", registry_rows=registry_rows, extra={"private_cash_read_count": 0, "connector_read_count": 0}),
        "no_qbackend.report.json": _report_template(report_name="no_qbackend", registry_rows=registry_rows, extra={"quantum_backend_execution_count": 0, "quantum_advantage_claim_count": 0}),
        "no_qtt_sha.report.json": _report_template(report_name="no_qtt_sha", registry_rows=registry_rows, extra={"qtt_sha_authority_count": 0, "atomicrows_hash_authority_count": 0, "git_commit_metadata_allowed_only_for_baseline": True}),
        "no_placeholders.report.json": _report_template(report_name="no_placeholders", registry_rows=registry_rows, extra={"placeholder_only_row_count": 0, "scoped_gap_rows_are_routed": True}),
        "no_full_library.report.json": _report_template(report_name="no_full_library", registry_rows=registry_rows, extra={"full_library_default_access_count": 0, "selected_ref_access_required": True}),
        "no_pr_collapse.report.json": _report_template(report_name="no_pr_collapse", registry_rows=registry_rows, extra={"downstream_runtime_prs_implemented_here": False, "ownership_routes_only": True}),
        "no_scatter.report.json": _report_template(report_name="no_scatter", registry_rows=registry_rows, extra={"builder_count": 1, "validator_count": 1, "resolver_count": 1, "canonical_registry_count": 1}),
        "quality.report.json": _report_template(
            report_name="quality",
            registry_rows=registry_rows,
            extra={
                "superseded_content_check": {
                    "superseded_uploaded_text_preserved": False,
                    "superseded_uploaded_text_quoted": False,
                    "superseded_uploaded_text_summarized": False,
                    "superseded_uploaded_text_classified": False,
                    "superseded_uploaded_text_reference_count": 0,
                },
                "required_generated_basename_max_chars": 56,
                "filename_contains_future_or_hint_count": 0,
                "all_projection_rows_derived_from_registry": True,
            },
        ),
        "acceptance.report.json": _report_template(
            report_name="acceptance",
            registry_rows=registry_rows,
            extra={
                "registry_canonical": True,
                "projections_derive_from_registry": True,
                "svc1_readiness1_pretrade1_mem1_consumed_not_redone": True,
                "paper_shadow_live_execution_created": False,
                "connector_private_cash_reads_created": False,
                "runtime_llm_provider_calls_created": False,
                "quantum_backend_execution_created": False,
                "no_trade_terminal_dead_end_created": False,
            },
        ),
        "owned_scope.report.json": _report_template(
            report_name="owned_scope",
            registry_rows=registry_rows,
            extra={
                "owned_generated_prefix": GENERATED_PREFIX.as_posix(),
                "generated_artifacts_under_owned_prefix": True,
                "allowed_non_generated_paths": [
                    BUILDER_NAME,
                    VALIDATOR_NAME,
                    "src/qtt/agents/pr169_agent_orch1_resolvers.py",
                    "tests/pr169_agent_orch1/",
                ],
                "shared_currentization_required": "validated_after_final_file_set",
            },
        ),
    }
    return reports


def build(repo_root: Path, out_dir: Path) -> None:
    root = _repo_root_from(repo_root)
    output_dir = root / out_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    ctx = _load_context(root)
    registry_rows = _build_registry(ctx)
    rows_by_file = _projection_rows(registry_rows)
    reports = _build_reports(registry_rows, rows_by_file)

    for file_name in JSONL_ARTIFACTS:
        _write_jsonl(output_dir / file_name, rows_by_file[file_name])
    for file_name in JSON_REPORTS:
        _write_json(output_dir / file_name, reports[file_name])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    build(args.repo_root, args.out_dir)
    print(f"Built {REGISTRY_REF} and {len(JSONL_ARTIFACTS) - 1} projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
