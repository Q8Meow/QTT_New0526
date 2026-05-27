"""Central constants for PR156 agent binding and universal intake."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR156"
SEMANTIC_TASK_ID = "PR156_AGENT_DEFAULT_BINDING_UNIVERSAL_INTAKE_GATE"
BRANCH = "pr156-agent-default-binding-universal-intake-gate"
REGISTRY_TYPE = "QTT_PR156_AGENT_DEFAULT_BINDING_UNIVERSAL_INTAKE_GATE_REGISTRY"
REPORT_TYPE = "QTT_PR156_AGENT_DEFAULT_BINDING_UNIVERSAL_INTAKE_GATE_REPORT"
SUCCESS_MARKER = "QTT_PR156_AGENT_DEFAULT_BINDING_UNIVERSAL_INTAKE_GATE_OK"
AUTHORITY_CLASS = (
    "AGENT_DEFAULT_BINDING_AND_UNIVERSAL_INTAKE_GATE_NOT_RUNTIME_NOT_LIVE_NOT_"
    "CONNECTOR_NOT_REPLAY_NOT_PAPER_NOT_SCORING_EXECUTION_NOT_OPTIMIZER_EXECUTION_"
    "NOT_QUANTUM_BACKEND_NOT_PROFIT_AUTHORITY"
)
AUTHORITY_CLASS_VALUES = (AUTHORITY_CLASS,)

REGISTRY_PATH = Path(
    "docs/master_plan/generated/"
    "PR156_AgentDefaultBindingUniversalIntakeGate.registry.json"
)
REPORT_PATH = Path(
    "docs/master_plan/generated/"
    "PR156_AgentDefaultBindingUniversalIntakeGate.report.json"
)

PR155_REGISTRY_PATH = Path(
    "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.registry.json"
)
PR155_REPORT_PATH = Path(
    "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.report.json"
)
PR155_REGISTRY_TYPE = "QTT_PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY"
PR155_REPORT_TYPE = "QTT_PR155_AGENT_CONSUMABLE_PARAMETER_DEFAULT_REGISTRY_REPORT"
PR154_REPORT_PATH = Path(
    "docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json"
)
PR154_REPORT_ID = "QTT_PR154_ATOMICROWS_PARAMETER_DEFAULT_VALUE_MATERIALIZATION_GATE_REPORT"

ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
ROADMAP_EXECUTION_STATE_PATH = Path(
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
)
LAUNCH_READINESS_ROADMAP_PATH = Path(
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"
)
LAUNCH_READINESS_POLICY_PATH = Path(
    "src/qtt/stage1_prediction_markets/launch_readiness/"
    "day1_launch_readiness_roadmap_policy.py"
)
PR136_ROUTE_TRIAGE_PATH = Path("docs/master_plan/generated/PR136RouteTriage.report.json")
PR136_SECTION_CROSSWALK_ALIAS_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
PR136_SECTION_CROSSWALK_SUCCESSOR_PATH = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)
PR136_MARKET_INDEX_PATH = Path(
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"
)
PR136_COMMAND_MATRIX_PATH = Path(
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json"
)
PR137R_RECONCILIATION_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
PR138_SEMANTIC_CONTRACT_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
)

REQUIRED_INPUT_ARTIFACT_PATHS = {
    "pr155_registry": PR155_REGISTRY_PATH,
    "pr155_report": PR155_REPORT_PATH,
    "pr154_materialization_report": PR154_REPORT_PATH,
    "pr_identity_roster": ROSTER_PATH,
    "roadmap_execution_state_controller": ROADMAP_EXECUTION_STATE_PATH,
    "day1_launch_readiness_roadmap": LAUNCH_READINESS_ROADMAP_PATH,
    "day1_launch_readiness_policy": LAUNCH_READINESS_POLICY_PATH,
    "pr136_route_triage": PR136_ROUTE_TRIAGE_PATH,
    "pr136_section_crosswalk_alias": PR136_SECTION_CROSSWALK_ALIAS_PATH,
    "pr136_section_crosswalk_successor": PR136_SECTION_CROSSWALK_SUCCESSOR_PATH,
    "pr136_market_specific_launch_readiness_index": PR136_MARKET_INDEX_PATH,
    "pr136_command_action_matrix": PR136_COMMAND_MATRIX_PATH,
    "pr137r_atomicrows_reconciliation": PR137R_RECONCILIATION_PATH,
    "pr138_atomicrows_semantic_contract": PR138_SEMANTIC_CONTRACT_PATH,
}
REQUIRED_INPUT_ALIASES = {
    PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(): (
        PR136_SECTION_CROSSWALK_SUCCESSOR_PATH.as_posix()
    )
}

OPTIONAL_INPUT_ARTIFACT_PATHS = {
    "qtt_agent_role_operating_charter_report": Path(
        "docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json"
    ),
    "qtt_algorithm_formula_family_report": Path(
        "docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json"
    ),
    "qtt_agent_algorithm_binding_report": Path(
        "docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json"
    ),
    "qtt_agent_algorithm_consumer_gate_report": Path(
        "docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json"
    ),
    "atomicrows_parameter_agent_binding_report": Path(
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json"
    ),
    "atomicrows_parameter_agent_binding_consumer_gate_report": Path(
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingConsumerGate.report.json"
    ),
    "atomicrows_parameter_agent_binding_cumulative_gate_report": Path(
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
    ),
    "atomicrows_parameter_agent_binding_command_matrix": Path(
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json"
    ),
    "quantum_applicability_classification_registry": Path(
        "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json"
    ),
    "owner_quantum_priority_policy_registry": Path(
        "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json"
    ),
    "parameter_algorithm_scoring_policy_registry": Path(
        "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json"
    ),
    "parameter_stack_scoring_and_ranking_gate": Path(
        "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json"
    ),
    "quantum_classical_optimizer_arbitration_gate": Path(
        "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json"
    ),
    "candidate_parameter_stack_generation_gate": Path(
        "docs/master_plan/generated/CandidateParameterStackGenerationGate.report.json"
    ),
    "trade_context_parameter_stack_selection_gate": Path(
        "docs/master_plan/generated/TradeContextParameterStackSelectionGate.report.json"
    ),
    "selected_parameter_stack_handoff_packet": Path(
        "docs/master_plan/generated/SelectedParameterStackHandoffPacket.report.json"
    ),
    "replay_paper_candidate_stack_competition_gate": Path(
        "docs/master_plan/generated/ReplayPaperCandidateStackCompetitionGate.report.json"
    ),
    "dual_result_review_for_parameter_stacks": Path(
        "docs/master_plan/generated/DualResultReviewForParameterStacks.report.json"
    ),
    "owner_live_promotion_review_for_parameter_stacks": Path(
        "docs/master_plan/generated/OwnerLivePromotionReviewForParameterStacks.report.json"
    ),
    "atomicrows_parameter_selection_universe_registry": Path(
        "docs/master_plan/generated/AtomicRowsParameterSelectionUniverseRegistry.report.json"
    ),
    "atomicrows_parameter_selection_universe_consumer_gate": Path(
        "docs/master_plan/generated/AtomicRowsParameterSelectionUniverseConsumerGate.report.json"
    ),
    "atomicrows_trade_context_selection_universe_routing_gate": Path(
        "docs/master_plan/generated/AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
    ),
    "future_owner_submitted_research_source_intake_registry": Path(
        "docs/master_plan/generated/AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
    ),
    "future_research_source_to_candidate_family_gate": Path(
        "docs/master_plan/generated/AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
    ),
}
OPTIONAL_INPUT_DISCOVERY_KEYS = tuple(sorted(OPTIONAL_INPUT_ARTIFACT_PATHS))
AGENT_BINDING_OPTIONAL_KEYS = (
    "qtt_agent_role_operating_charter_report",
    "qtt_agent_algorithm_binding_report",
    "qtt_agent_algorithm_consumer_gate_report",
    "atomicrows_parameter_agent_binding_report",
    "atomicrows_parameter_agent_binding_consumer_gate_report",
    "atomicrows_parameter_agent_binding_cumulative_gate_report",
    "atomicrows_parameter_agent_binding_command_matrix",
)
SCORING_OPTIMIZER_STATIC_KEYS = (
    "quantum_applicability_classification_registry",
    "owner_quantum_priority_policy_registry",
    "parameter_algorithm_scoring_policy_registry",
    "parameter_stack_scoring_and_ranking_gate",
    "quantum_classical_optimizer_arbitration_gate",
    "candidate_parameter_stack_generation_gate",
    "trade_context_parameter_stack_selection_gate",
    "selected_parameter_stack_handoff_packet",
    "replay_paper_candidate_stack_competition_gate",
    "dual_result_review_for_parameter_stacks",
    "owner_live_promotion_review_for_parameter_stacks",
)
ATOMICROWS_OPTIONAL_KEYS = (
    "atomicrows_parameter_selection_universe_registry",
    "atomicrows_parameter_selection_universe_consumer_gate",
    "atomicrows_trade_context_selection_universe_routing_gate",
)
FUTURE_CANDIDATE_SOURCE_KEYS = (
    "future_owner_submitted_research_source_intake_registry",
    "future_research_source_to_candidate_family_gate",
    "qtt_algorithm_formula_family_report",
)

EXPECTED_INPUT_PR155_TOTAL_RECORDS = 342
EXPECTED_INPUT_PR155_READY_DEFAULT_COUNT = 230
EXPECTED_INPUT_PR155_BLOCKED_COUNT = 112
EXPECTED_PR154_BLOCKED_COUNT = 112
EXPECTED_ATOMICROWS_UNIVERSE_COUNT = 4183

PR155_READY_DEFAULT_BINDING_LANE = "PR155_READY_DEFAULT_BINDING_LANE"
PR155_READY_DEFAULT_BINDING_PENDING_LANE = "PR155_READY_DEFAULT_BINDING_PENDING_LANE"
PR154_BLOCKED_COMPLETION_INGESTION_LANE = "PR154_BLOCKED_COMPLETION_INGESTION_LANE"
ATOMICROWS_UNIVERSE_COMPLETION_INGESTION_LANE = (
    "ATOMICROWS_UNIVERSE_COMPLETION_INGESTION_LANE"
)
FUTURE_CLASSICAL_FORMULA_TEMPLATE_LANE = "FUTURE_CLASSICAL_FORMULA_TEMPLATE_LANE"
FUTURE_CLASSICAL_ALGORITHM_TEMPLATE_LANE = "FUTURE_CLASSICAL_ALGORITHM_TEMPLATE_LANE"
FUTURE_EDGE_ALPHA_TEMPLATE_LANE = "FUTURE_EDGE_ALPHA_TEMPLATE_LANE"
FUTURE_RISK_CAPITAL_EXECUTION_TEMPLATE_LANE = (
    "FUTURE_RISK_CAPITAL_EXECUTION_TEMPLATE_LANE"
)
FUTURE_QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE_LANE = (
    "FUTURE_QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE_LANE"
)
FUTURE_TRUE_QUANTUM_OPTIMIZER_TEMPLATE_LANE = (
    "FUTURE_TRUE_QUANTUM_OPTIMIZER_TEMPLATE_LANE"
)
FUTURE_HYBRID_CLASSICAL_QUANTUM_TEMPLATE_LANE = (
    "FUTURE_HYBRID_CLASSICAL_QUANTUM_TEMPLATE_LANE"
)
BLOCKED_AMBIGUOUS_INPUT_LANE = "BLOCKED_AMBIGUOUS_INPUT_LANE"
BLOCKED_ORCHESTRATION_PRECHECK_LANE = "BLOCKED_ORCHESTRATION_PRECHECK_LANE"
POPULATION_LANE_VALUES = (
    PR155_READY_DEFAULT_BINDING_LANE,
    PR155_READY_DEFAULT_BINDING_PENDING_LANE,
    PR154_BLOCKED_COMPLETION_INGESTION_LANE,
    ATOMICROWS_UNIVERSE_COMPLETION_INGESTION_LANE,
    FUTURE_CLASSICAL_FORMULA_TEMPLATE_LANE,
    FUTURE_CLASSICAL_ALGORITHM_TEMPLATE_LANE,
    FUTURE_EDGE_ALPHA_TEMPLATE_LANE,
    FUTURE_RISK_CAPITAL_EXECUTION_TEMPLATE_LANE,
    FUTURE_QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE_LANE,
    FUTURE_TRUE_QUANTUM_OPTIMIZER_TEMPLATE_LANE,
    FUTURE_HYBRID_CLASSICAL_QUANTUM_TEMPLATE_LANE,
    BLOCKED_AMBIGUOUS_INPUT_LANE,
    BLOCKED_ORCHESTRATION_PRECHECK_LANE,
)

AGENT_BOUND_NONLIVE_EXPLICIT = "AGENT_BOUND_NONLIVE_EXPLICIT"
ROLE_BOUND_NONLIVE_EXPLICIT = "ROLE_BOUND_NONLIVE_EXPLICIT"
CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT = "CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT"
BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING = (
    "BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING"
)
BINDING_PENDING_PR154_COMPLETION = "BINDING_PENDING_PR154_COMPLETION"
BINDING_PENDING_ATOMICROWS_COMPLETION = "BINDING_PENDING_ATOMICROWS_COMPLETION"
BINDING_PENDING_SOURCE_EVIDENCE = "BINDING_PENDING_SOURCE_EVIDENCE"
BINDING_PENDING_CLASSICAL_QUANTUM_CLASSIFICATION = (
    "BINDING_PENDING_CLASSICAL_QUANTUM_CLASSIFICATION"
)
BINDING_PENDING_REPLAY_PAPER = "BINDING_PENDING_REPLAY_PAPER"
BINDING_BLOCKED_AMBIGUOUS = "BINDING_BLOCKED_AMBIGUOUS"
BINDING_BLOCKED_SCHEMA_INVALID = "BINDING_BLOCKED_SCHEMA_INVALID"
BINDING_BLOCKED_LIVE_AUTHORITY_FORBIDDEN = "BINDING_BLOCKED_LIVE_AUTHORITY_FORBIDDEN"
AGENT_BINDING_STATE_VALUES = (
    AGENT_BOUND_NONLIVE_EXPLICIT,
    ROLE_BOUND_NONLIVE_EXPLICIT,
    CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT,
    BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING,
    BINDING_PENDING_PR154_COMPLETION,
    BINDING_PENDING_ATOMICROWS_COMPLETION,
    BINDING_PENDING_SOURCE_EVIDENCE,
    BINDING_PENDING_CLASSICAL_QUANTUM_CLASSIFICATION,
    BINDING_PENDING_REPLAY_PAPER,
    BINDING_BLOCKED_AMBIGUOUS,
    BINDING_BLOCKED_SCHEMA_INVALID,
    BINDING_BLOCKED_LIVE_AUTHORITY_FORBIDDEN,
)

CLASSICAL_TRADING_FORMULA_TEMPLATE = "CLASSICAL_TRADING_FORMULA_TEMPLATE"
CLASSICAL_STATISTICAL_EDGE_TEMPLATE = "CLASSICAL_STATISTICAL_EDGE_TEMPLATE"
CLASSICAL_MARKET_MICROSTRUCTURE_ALPHA_TEMPLATE = (
    "CLASSICAL_MARKET_MICROSTRUCTURE_ALPHA_TEMPLATE"
)
CLASSICAL_RISK_FORMULA_TEMPLATE = "CLASSICAL_RISK_FORMULA_TEMPLATE"
CLASSICAL_CAPITAL_ALLOCATION_FORMULA_TEMPLATE = (
    "CLASSICAL_CAPITAL_ALLOCATION_FORMULA_TEMPLATE"
)
CLASSICAL_EXECUTION_LATENCY_FORMULA_TEMPLATE = (
    "CLASSICAL_EXECUTION_LATENCY_FORMULA_TEMPLATE"
)
CLASSICAL_OPTIMIZER_METHOD_TEMPLATE = "CLASSICAL_OPTIMIZER_METHOD_TEMPLATE"
QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE = "QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE"
TRUE_QUANTUM_OPTIMIZER_TEMPLATE = "TRUE_QUANTUM_OPTIMIZER_TEMPLATE"
HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE = (
    "HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE"
)
QUBO_COMPATIBLE_TEMPLATE = "QUBO_COMPATIBLE_TEMPLATE"
ISING_COMPATIBLE_TEMPLATE = "ISING_COMPATIBLE_TEMPLATE"
QAOA_COMPATIBLE_TEMPLATE = "QAOA_COMPATIBLE_TEMPLATE"
VQE_COMPATIBLE_TEMPLATE = "VQE_COMPATIBLE_TEMPLATE"
ANNEALING_COMPATIBLE_TEMPLATE = "ANNEALING_COMPATIBLE_TEMPLATE"
QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE = (
    "QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE"
)
UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE = (
    "UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE"
)
UNIVERSAL_INTAKE_TEMPLATE_TYPE_VALUES = (
    CLASSICAL_TRADING_FORMULA_TEMPLATE,
    CLASSICAL_STATISTICAL_EDGE_TEMPLATE,
    CLASSICAL_MARKET_MICROSTRUCTURE_ALPHA_TEMPLATE,
    CLASSICAL_RISK_FORMULA_TEMPLATE,
    CLASSICAL_CAPITAL_ALLOCATION_FORMULA_TEMPLATE,
    CLASSICAL_EXECUTION_LATENCY_FORMULA_TEMPLATE,
    CLASSICAL_OPTIMIZER_METHOD_TEMPLATE,
    QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE,
    TRUE_QUANTUM_OPTIMIZER_TEMPLATE,
    HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE,
    QUBO_COMPATIBLE_TEMPLATE,
    ISING_COMPATIBLE_TEMPLATE,
    QAOA_COMPATIBLE_TEMPLATE,
    VQE_COMPATIBLE_TEMPLATE,
    ANNEALING_COMPATIBLE_TEMPLATE,
    QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE,
    UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE,
)
CLASSICAL_TEMPLATE_TYPES = (
    CLASSICAL_TRADING_FORMULA_TEMPLATE,
    CLASSICAL_STATISTICAL_EDGE_TEMPLATE,
    CLASSICAL_MARKET_MICROSTRUCTURE_ALPHA_TEMPLATE,
    CLASSICAL_RISK_FORMULA_TEMPLATE,
    CLASSICAL_CAPITAL_ALLOCATION_FORMULA_TEMPLATE,
    CLASSICAL_EXECUTION_LATENCY_FORMULA_TEMPLATE,
    CLASSICAL_OPTIMIZER_METHOD_TEMPLATE,
)
QUANTUM_TEMPLATE_TYPES = (
    QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE,
    TRUE_QUANTUM_OPTIMIZER_TEMPLATE,
    QUBO_COMPATIBLE_TEMPLATE,
    ISING_COMPATIBLE_TEMPLATE,
    QAOA_COMPATIBLE_TEMPLATE,
    VQE_COMPATIBLE_TEMPLATE,
    ANNEALING_COMPATIBLE_TEMPLATE,
    QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE,
)
HYBRID_TEMPLATE_TYPES = (HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE,)

TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE = "TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE"
CANDIDATE_INSTANCE_PENDING_RESEARCH_INTAKE = (
    "CANDIDATE_INSTANCE_PENDING_RESEARCH_INTAKE"
)
CANDIDATE_INSTANCE_PENDING_SOURCE_EVIDENCE = (
    "CANDIDATE_INSTANCE_PENDING_SOURCE_EVIDENCE"
)
CANDIDATE_INSTANCE_PENDING_ATOMICROWS_MAPPING = (
    "CANDIDATE_INSTANCE_PENDING_ATOMICROWS_MAPPING"
)
CANDIDATE_INSTANCE_PENDING_CLASSIFICATION = "CANDIDATE_INSTANCE_PENDING_CLASSIFICATION"
CANDIDATE_INSTANCE_BLOCKED = "CANDIDATE_INSTANCE_BLOCKED"
CANDIDATE_INSTANCE_STATE_VALUES = (
    TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE,
    CANDIDATE_INSTANCE_PENDING_RESEARCH_INTAKE,
    CANDIDATE_INSTANCE_PENDING_SOURCE_EVIDENCE,
    CANDIDATE_INSTANCE_PENDING_ATOMICROWS_MAPPING,
    CANDIDATE_INSTANCE_PENDING_CLASSIFICATION,
    CANDIDATE_INSTANCE_BLOCKED,
)

CLASSICAL_ONLY = "CLASSICAL_ONLY"
QUANTUM_APPLICABLE = "QUANTUM_APPLICABLE"
QUANTUM_INSPIRED = "QUANTUM_INSPIRED"
TRUE_QUANTUM = "TRUE_QUANTUM"
HYBRID_CLASSICAL_QUANTUM = "HYBRID_CLASSICAL_QUANTUM"
QUBO_COMPATIBLE = "QUBO_COMPATIBLE"
ISING_COMPATIBLE = "ISING_COMPATIBLE"
QAOA_COMPATIBLE = "QAOA_COMPATIBLE"
VQE_COMPATIBLE = "VQE_COMPATIBLE"
ANNEALING_COMPATIBLE = "ANNEALING_COMPATIBLE"
QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE = (
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE"
)
APPLICABILITY_PENDING_CLASSIFICATION = "APPLICABILITY_PENDING_CLASSIFICATION"
APPLICABILITY_BLOCKED_INSUFFICIENT_EVIDENCE = (
    "APPLICABILITY_BLOCKED_INSUFFICIENT_EVIDENCE"
)
CLASSICAL_QUANTUM_HYBRID_APPLICABILITY_VALUES = (
    CLASSICAL_ONLY,
    QUANTUM_APPLICABLE,
    QUANTUM_INSPIRED,
    TRUE_QUANTUM,
    HYBRID_CLASSICAL_QUANTUM,
    QUBO_COMPATIBLE,
    ISING_COMPATIBLE,
    QAOA_COMPATIBLE,
    VQE_COMPATIBLE,
    ANNEALING_COMPATIBLE,
    QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE,
    APPLICABILITY_PENDING_CLASSIFICATION,
    APPLICABILITY_BLOCKED_INSUFFICIENT_EVIDENCE,
)

OWNER_CLASSICAL_ALLOWED = "OWNER_CLASSICAL_ALLOWED"
OWNER_QUANTUM_ALLOWED = "OWNER_QUANTUM_ALLOWED"
OWNER_HYBRID_COMPARE_ALLOWED = "OWNER_HYBRID_COMPARE_ALLOWED"
OWNER_CLASSICAL_PRIORITY = "OWNER_CLASSICAL_PRIORITY"
OWNER_QUANTUM_PRIORITY = "OWNER_QUANTUM_PRIORITY"
OWNER_HYBRID_COMPARE_PRIORITY = "OWNER_HYBRID_COMPARE_PRIORITY"
OWNER_FORCED_CLASSICAL_INTERNAL_ONLY = "OWNER_FORCED_CLASSICAL_INTERNAL_ONLY"
OWNER_FORCED_QUANTUM_INTERNAL_ONLY = "OWNER_FORCED_QUANTUM_INTERNAL_ONLY"
OWNER_FORCED_HYBRID_COMPARE_INTERNAL_ONLY = (
    "OWNER_FORCED_HYBRID_COMPARE_INTERNAL_ONLY"
)
STRATEGY_PRIORITY_PENDING_OWNER_POLICY = "STRATEGY_PRIORITY_PENDING_OWNER_POLICY"
STRATEGY_PRIORITY_BLOCKED = "STRATEGY_PRIORITY_BLOCKED"
OWNER_STRATEGY_PRIORITY_STATE_VALUES = (
    OWNER_CLASSICAL_ALLOWED,
    OWNER_QUANTUM_ALLOWED,
    OWNER_HYBRID_COMPARE_ALLOWED,
    OWNER_CLASSICAL_PRIORITY,
    OWNER_QUANTUM_PRIORITY,
    OWNER_HYBRID_COMPARE_PRIORITY,
    OWNER_FORCED_CLASSICAL_INTERNAL_ONLY,
    OWNER_FORCED_QUANTUM_INTERNAL_ONLY,
    OWNER_FORCED_HYBRID_COMPARE_INTERNAL_ONLY,
    STRATEGY_PRIORITY_PENDING_OWNER_POLICY,
    STRATEGY_PRIORITY_BLOCKED,
)

SOURCE_EVIDENCE_REFERENCED_ONLY = "SOURCE_EVIDENCE_REFERENCED_ONLY"
SOURCE_EVIDENCE_PENDING_RESEARCH_INTAKE = "SOURCE_EVIDENCE_PENDING_RESEARCH_INTAKE"
SOURCE_EVIDENCE_PENDING_ATOMICROWS_MAPPING = "SOURCE_EVIDENCE_PENDING_ATOMICROWS_MAPPING"
SOURCE_EVIDENCE_PENDING_ACCEPTED_SOURCE_PACKET = (
    "SOURCE_EVIDENCE_PENDING_ACCEPTED_SOURCE_PACKET"
)
SOURCE_EVIDENCE_TEMPLATE_ONLY_NOT_ACCEPTED = (
    "SOURCE_EVIDENCE_TEMPLATE_ONLY_NOT_ACCEPTED"
)
SOURCE_EVIDENCE_BLOCKED_INSUFFICIENT_EVIDENCE = (
    "SOURCE_EVIDENCE_BLOCKED_INSUFFICIENT_EVIDENCE"
)
SOURCE_EVIDENCE_REQUIREMENT_STATE_VALUES = (
    SOURCE_EVIDENCE_REFERENCED_ONLY,
    SOURCE_EVIDENCE_PENDING_RESEARCH_INTAKE,
    SOURCE_EVIDENCE_PENDING_ATOMICROWS_MAPPING,
    SOURCE_EVIDENCE_PENDING_ACCEPTED_SOURCE_PACKET,
    SOURCE_EVIDENCE_TEMPLATE_ONLY_NOT_ACCEPTED,
    SOURCE_EVIDENCE_BLOCKED_INSUFFICIENT_EVIDENCE,
)

ATOMICROWS_COMPATIBLE_EXISTING_PR155_DEFAULT = (
    "ATOMICROWS_COMPATIBLE_EXISTING_PR155_DEFAULT"
)
ATOMICROWS_PENDING_PR154_COMPLETION = "ATOMICROWS_PENDING_PR154_COMPLETION"
ATOMICROWS_PENDING_UNIVERSE_COMPLETION = "ATOMICROWS_PENDING_UNIVERSE_COMPLETION"
ATOMICROWS_UNIVERSE_COUNT_CONFIRMED = "ATOMICROWS_UNIVERSE_COUNT_CONFIRMED"
ATOMICROWS_UNIVERSE_COUNT_UNCONFIRMED = "ATOMICROWS_UNIVERSE_COUNT_UNCONFIRMED"
ATOMICROWS_PENDING_SOURCE_EVIDENCE = "ATOMICROWS_PENDING_SOURCE_EVIDENCE"
ATOMICROWS_PENDING_SEMANTIC_CONTRACT = "ATOMICROWS_PENDING_SEMANTIC_CONTRACT"
ATOMICROWS_PENDING_RECONCILIATION = "ATOMICROWS_PENDING_RECONCILIATION"
ATOMICROWS_FUTURE_CANDIDATE_MAPPING_REQUIRED = (
    "ATOMICROWS_FUTURE_CANDIDATE_MAPPING_REQUIRED"
)
ATOMICROWS_NOT_BUNDLE_AUTHORITY = "ATOMICROWS_NOT_BUNDLE_AUTHORITY"
ATOMICROWS_BLOCKED_AMBIGUOUS = "ATOMICROWS_BLOCKED_AMBIGUOUS"
ATOMICROWS_INGESTION_STATE_VALUES = (
    ATOMICROWS_COMPATIBLE_EXISTING_PR155_DEFAULT,
    ATOMICROWS_PENDING_PR154_COMPLETION,
    ATOMICROWS_PENDING_UNIVERSE_COMPLETION,
    ATOMICROWS_UNIVERSE_COUNT_CONFIRMED,
    ATOMICROWS_UNIVERSE_COUNT_UNCONFIRMED,
    ATOMICROWS_PENDING_SOURCE_EVIDENCE,
    ATOMICROWS_PENDING_SEMANTIC_CONTRACT,
    ATOMICROWS_PENDING_RECONCILIATION,
    ATOMICROWS_FUTURE_CANDIDATE_MAPPING_REQUIRED,
    ATOMICROWS_NOT_BUNDLE_AUTHORITY,
    ATOMICROWS_BLOCKED_AMBIGUOUS,
)

SCORING_RANKING_ELIGIBLE_NONLIVE = "SCORING_RANKING_ELIGIBLE_NONLIVE"
SCORING_RANKING_PENDING_AGENT_BINDING = "SCORING_RANKING_PENDING_AGENT_BINDING"
SCORING_RANKING_PENDING_SOURCE_EVIDENCE = "SCORING_RANKING_PENDING_SOURCE_EVIDENCE"
SCORING_RANKING_PENDING_ATOMICROWS_MAPPING = (
    "SCORING_RANKING_PENDING_ATOMICROWS_MAPPING"
)
SCORING_RANKING_PENDING_CLASSICAL_QUANTUM_CLASSIFICATION = (
    "SCORING_RANKING_PENDING_CLASSICAL_QUANTUM_CLASSIFICATION"
)
SCORING_RANKING_PENDING_REPLAY_PAPER = "SCORING_RANKING_PENDING_REPLAY_PAPER"
SCORING_RANKING_BLOCKED = "SCORING_RANKING_BLOCKED"
SCORING_RANKING_NOT_EXECUTED_IN_PR156 = "SCORING_RANKING_NOT_EXECUTED_IN_PR156"
SCORING_RANKING_READINESS_STATE_VALUES = (
    SCORING_RANKING_ELIGIBLE_NONLIVE,
    SCORING_RANKING_PENDING_AGENT_BINDING,
    SCORING_RANKING_PENDING_SOURCE_EVIDENCE,
    SCORING_RANKING_PENDING_ATOMICROWS_MAPPING,
    SCORING_RANKING_PENDING_CLASSICAL_QUANTUM_CLASSIFICATION,
    SCORING_RANKING_PENDING_REPLAY_PAPER,
    SCORING_RANKING_BLOCKED,
    SCORING_RANKING_NOT_EXECUTED_IN_PR156,
)

OPTIMIZER_NOT_EXECUTED_IN_PR156 = "OPTIMIZER_NOT_EXECUTED_IN_PR156"
CLASSICAL_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER = (
    "CLASSICAL_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER"
)
QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER = (
    "QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER"
)
TRUE_QUANTUM_OPTIMIZER_CANDIDATE_FOR_FUTURE_BACKEND_GATE = (
    "TRUE_QUANTUM_OPTIMIZER_CANDIDATE_FOR_FUTURE_BACKEND_GATE"
)
HYBRID_COMPARE_CANDIDATE_FOR_FUTURE_ARBITRATION = (
    "HYBRID_COMPARE_CANDIDATE_FOR_FUTURE_ARBITRATION"
)
OPTIMIZER_ROUTING_PENDING_CLASSIFICATION = "OPTIMIZER_ROUTING_PENDING_CLASSIFICATION"
OPTIMIZER_ROUTING_BLOCKED = "OPTIMIZER_ROUTING_BLOCKED"
OPTIMIZER_ROUTING_HINT_VALUES = (
    OPTIMIZER_NOT_EXECUTED_IN_PR156,
    CLASSICAL_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER,
    QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER,
    TRUE_QUANTUM_OPTIMIZER_CANDIDATE_FOR_FUTURE_BACKEND_GATE,
    HYBRID_COMPARE_CANDIDATE_FOR_FUTURE_ARBITRATION,
    OPTIMIZER_ROUTING_PENDING_CLASSIFICATION,
    OPTIMIZER_ROUTING_BLOCKED,
)

REPLAY_PAPER_NOT_EXECUTED_IN_PR156 = "REPLAY_PAPER_NOT_EXECUTED_IN_PR156"
REPLAY_PAPER_FUTURE_CANDIDATE = "REPLAY_PAPER_FUTURE_CANDIDATE"
REPLAY_PAPER_PENDING_SOURCE_EVIDENCE = "REPLAY_PAPER_PENDING_SOURCE_EVIDENCE"
REPLAY_PAPER_PENDING_AGENT_BINDING = "REPLAY_PAPER_PENDING_AGENT_BINDING"
REPLAY_PAPER_PENDING_ATOMICROWS_COMPLETION = (
    "REPLAY_PAPER_PENDING_ATOMICROWS_COMPLETION"
)
REPLAY_PAPER_BLOCKED = "REPLAY_PAPER_BLOCKED"
REPLAY_PAPER_ROUTING_HINT_VALUES = (
    REPLAY_PAPER_NOT_EXECUTED_IN_PR156,
    REPLAY_PAPER_FUTURE_CANDIDATE,
    REPLAY_PAPER_PENDING_SOURCE_EVIDENCE,
    REPLAY_PAPER_PENDING_AGENT_BINDING,
    REPLAY_PAPER_PENDING_ATOMICROWS_COMPLETION,
    REPLAY_PAPER_BLOCKED,
)

PR155_DEFAULT_BINDING_RECORD = "PR155_DEFAULT_BINDING_RECORD"
PR154_BLOCKED_INGESTION_RECORD = "PR154_BLOCKED_INGESTION_RECORD"
ATOMICROWS_UNIVERSE_INGESTION_SUMMARY_RECORD = (
    "ATOMICROWS_UNIVERSE_INGESTION_SUMMARY_RECORD"
)
FUTURE_INTAKE_TEMPLATE_RECORD = "FUTURE_INTAKE_TEMPLATE_RECORD"
RECORD_KIND_VALUES = (
    PR155_DEFAULT_BINDING_RECORD,
    PR154_BLOCKED_INGESTION_RECORD,
    ATOMICROWS_UNIVERSE_INGESTION_SUMMARY_RECORD,
    FUTURE_INTAKE_TEMPLATE_RECORD,
)

SOURCE_POPULATION_PR155_READY = "PR155_READY_DEFAULTS"
SOURCE_POPULATION_PR154_BLOCKED = "PR154_PR155_BLOCKED_RECORDS"
SOURCE_POPULATION_ATOMICROWS_UNIVERSE = "ATOMICROWS_UNIVERSE_AGGREGATE"
SOURCE_POPULATION_FUTURE_TEMPLATE_CATALOG = "FUTURE_UNIVERSAL_INTAKE_TEMPLATE_CATALOG"
SOURCE_RECORD_TYPE_PR155_REGISTRY_RECORD = "PR155_AGENT_CONSUMABLE_REGISTRY_RECORD"
SOURCE_RECORD_TYPE_PR154_BLOCKED_RECORD = "PR154_PR155_BLOCKED_RECORD_REFERENCE"
SOURCE_RECORD_TYPE_ATOMICROWS_AGGREGATE = "ATOMICROWS_UNIVERSE_AGGREGATE_REFERENCE"
SOURCE_RECORD_TYPE_TEMPLATE = "PR156_TEMPLATE_CATALOG_RECORD"

COMPLETION_PATH_FIELDS = (
    "missing_fields",
    "required_next_task",
    "required_next_pr_or_phase",
    "responsible_authority",
    "required_input_artifact",
    "exact_unblock_condition",
    "materialization_retry_route",
    "codex_actionable_completion_steps",
)

RECORD_ALWAYS_FALSE_FIELDS = (
    "live_order_ready_flag",
    "runtime_ready_flag",
    "connector_semantic_bound_flag",
    "replay_executed_flag",
    "paper_executed_flag",
    "scoring_executed_as_trade_selection_flag",
    "optimizer_executed_flag",
    "quantum_backend_executed_flag",
    "quantum_execution_evidence_flag",
    "profit_evidence_flag",
)
NON_AUTHORITY_BOUNDARY = {field: False for field in RECORD_ALWAYS_FALSE_FIELDS}
REPORT_ZERO_COUNT_FIELDS = (
    "live_order_ready_count",
    "runtime_ready_count",
    "connector_semantic_bound_count",
    "replay_executed_count",
    "paper_executed_count",
    "scoring_executed_as_trade_selection_count",
    "optimizer_executed_count",
    "quantum_backend_executed_count",
    "quantum_execution_evidence_count",
    "profit_evidence_count",
)
REPORT_FALSE_AUTHORITY_FIELDS = (
    "qtt_sha_authority_created",
    "qtt_generated_sha_created",
    "qtt_freeze_checksum_global_digest_authority_created",
    "atomicrows_bundle_created",
    "atomicrows_bundle_sha_or_hash_authority_created",
)
FIELDS_THAT_MUST_ALWAYS_BE_FALSE = (
    *RECORD_ALWAYS_FALSE_FIELDS,
    *REPORT_FALSE_AUTHORITY_FIELDS,
)
AUTHORITY_BOUNDARY_FALSE_FLAGS = {
    "source_retrieval_created": False,
    "source_acceptance_created": False,
    "connector_binding_created": False,
    "runtime_private_state_receipt_created": False,
    "runtime_cash_receipt_created": False,
    "replay_result_created": False,
    "paper_result_created": False,
    "scoring_ranking_trade_selection_created": False,
    "optimizer_backend_execution_created": False,
    "quantum_advantage_claim_created": False,
    "latency_superiority_evidence_created": False,
    "execution_superiority_evidence_created": False,
    "profit_evidence_created": False,
    **NON_AUTHORITY_BOUNDARY,
}

PR156_READY = "PR156_READY"
PR156_REQUIRED_INPUT_MISSING = "PR156_REQUIRED_INPUT_MISSING"
PR156_REQUIRED_INPUT_INVALID = "PR156_REQUIRED_INPUT_INVALID"
PR156_REQUIRED_INPUT_AMBIGUOUS = "PR156_REQUIRED_INPUT_AMBIGUOUS"
PR156_OPTIONAL_INPUT_INVALID = "PR156_OPTIONAL_INPUT_INVALID"
PR156_ORCHESTRATION_ARTIFACT_MISSING = "PR156_ORCHESTRATION_ARTIFACT_MISSING"
PR156_ORCHESTRATION_ARTIFACT_INVALID = "PR156_ORCHESTRATION_ARTIFACT_INVALID"
PR156_ORCHESTRATION_CROSSWALK_MISSING = "PR156_ORCHESTRATION_CROSSWALK_MISSING"
PR156_PR155_COUNT_MISMATCH = "PR156_PR155_COUNT_MISMATCH"
PR156_PR154_COUNT_MISMATCH = "PR156_PR154_COUNT_MISMATCH"
PR156_RECORD_SCHEMA_INVALID = "PR156_RECORD_SCHEMA_INVALID"
PR156_RECORD_ID_DUPLICATE = "PR156_RECORD_ID_DUPLICATE"
PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE = "PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE"
PR156_BLOCKED_RECORD_CONSUMABLE = "PR156_BLOCKED_RECORD_CONSUMABLE"
PR156_TEMPLATE_RECORD_CONSUMABLE = "PR156_TEMPLATE_RECORD_CONSUMABLE"
PR156_QTT_SHA_AUTHORITY_CREATED = "PR156_QTT_SHA_AUTHORITY_CREATED"
PR156_ATOMICROWS_BUNDLE_AUTHORITY_CREATED = (
    "PR156_ATOMICROWS_BUNDLE_AUTHORITY_CREATED"
)
PR156_FORBIDDEN_ARTIFACT_REFERENCE_CREATED = (
    "PR156_FORBIDDEN_ARTIFACT_REFERENCE_CREATED"
)
PR156_REGISTRY_STALE_OR_NONDETERMINISTIC = (
    "PR156_REGISTRY_STALE_OR_NONDETERMINISTIC"
)
PR156_REPORT_STALE_OR_NONDETERMINISTIC = "PR156_REPORT_STALE_OR_NONDETERMINISTIC"
PR156_CHANGED_PATH_OUT_OF_SCOPE = "PR156_CHANGED_PATH_OUT_OF_SCOPE"
PR156_GIT_STATUS_UNAVAILABLE = "PR156_GIT_STATUS_UNAVAILABLE"
PR156_MASTER_PLAN_MUTATION_DETECTED = "PR156_MASTER_PLAN_MUTATION_DETECTED"
PR156_ATOMICROWS_BUNDLE_MUTATION_DETECTED = "PR156_ATOMICROWS_BUNDLE_MUTATION_DETECTED"
PR156_CENTRALIZED_VOCABULARY_DRIFT = "PR156_CENTRALIZED_VOCABULARY_DRIFT"
PR156_ATOMICROWS_UNIVERSE_SOURCE_MISSING_AGGREGATE_ONLY = (
    "PR156_ATOMICROWS_UNIVERSE_SOURCE_MISSING_AGGREGATE_ONLY"
)
PR156_FUTURE_CANDIDATE_SOURCE_MISSING_TEMPLATE_ONLY = (
    "PR156_FUTURE_CANDIDATE_SOURCE_MISSING_TEMPLATE_ONLY"
)
PR156_EXPLICIT_BINDING_MAP_MISSING = "PR156_EXPLICIT_BINDING_MAP_MISSING"
PR156_PR154_COMPLETION_REQUIRED = "PR156_PR154_COMPLETION_REQUIRED"
PR156_ATOMICROWS_COMPLETION_REQUIRED = "PR156_ATOMICROWS_COMPLETION_REQUIRED"
PR156_TEMPLATE_ONLY_NO_CANDIDATE = "PR156_TEMPLATE_ONLY_NO_CANDIDATE"
PR156_SOURCE_EVIDENCE_REQUIRED_FOR_FUTURE_CANDIDATE = (
    "PR156_SOURCE_EVIDENCE_REQUIRED_FOR_FUTURE_CANDIDATE"
)
BLOCK_CODES = (
    PR156_READY,
    PR156_REQUIRED_INPUT_MISSING,
    PR156_REQUIRED_INPUT_INVALID,
    PR156_REQUIRED_INPUT_AMBIGUOUS,
    PR156_OPTIONAL_INPUT_INVALID,
    PR156_ORCHESTRATION_ARTIFACT_MISSING,
    PR156_ORCHESTRATION_ARTIFACT_INVALID,
    PR156_ORCHESTRATION_CROSSWALK_MISSING,
    PR156_PR155_COUNT_MISMATCH,
    PR156_PR154_COUNT_MISMATCH,
    PR156_RECORD_SCHEMA_INVALID,
    PR156_RECORD_ID_DUPLICATE,
    PR156_FORBIDDEN_AUTHORITY_FLAG_TRUE,
    PR156_BLOCKED_RECORD_CONSUMABLE,
    PR156_TEMPLATE_RECORD_CONSUMABLE,
    PR156_QTT_SHA_AUTHORITY_CREATED,
    PR156_ATOMICROWS_BUNDLE_AUTHORITY_CREATED,
    PR156_FORBIDDEN_ARTIFACT_REFERENCE_CREATED,
    PR156_REGISTRY_STALE_OR_NONDETERMINISTIC,
    PR156_REPORT_STALE_OR_NONDETERMINISTIC,
    PR156_CHANGED_PATH_OUT_OF_SCOPE,
    PR156_GIT_STATUS_UNAVAILABLE,
    PR156_MASTER_PLAN_MUTATION_DETECTED,
    PR156_ATOMICROWS_BUNDLE_MUTATION_DETECTED,
    PR156_CENTRALIZED_VOCABULARY_DRIFT,
    PR156_ATOMICROWS_UNIVERSE_SOURCE_MISSING_AGGREGATE_ONLY,
    PR156_FUTURE_CANDIDATE_SOURCE_MISSING_TEMPLATE_ONLY,
    PR156_EXPLICIT_BINDING_MAP_MISSING,
    PR156_PR154_COMPLETION_REQUIRED,
    PR156_ATOMICROWS_COMPLETION_REQUIRED,
    PR156_TEMPLATE_ONLY_NO_CANDIDATE,
    PR156_SOURCE_EVIDENCE_REQUIRED_FOR_FUTURE_CANDIDATE,
)

REPORT_KEYS = (
    "report_type",
    "pr_id",
    "semantic_task_id",
    "authority_class",
    "input_pr155_total_records",
    "input_pr155_ready_default_count",
    "input_pr155_blocked_count",
    "pr156_binding_record_count",
    "explicit_agent_bound_count",
    "explicit_role_bound_count",
    "explicit_consumer_class_bound_count",
    "binding_pending_count",
    "pr154_blocked_ingestion_lane_count",
    "atomicrows_universe_ingestion_lane_count",
    "atomicrows_universe_confirmed_count",
    "atomicrows_universe_count_state",
    "future_classical_intake_template_count",
    "future_quantum_intake_template_count",
    "future_hybrid_intake_template_count",
    *REPORT_ZERO_COUNT_FIELDS,
    *REPORT_FALSE_AUTHORITY_FIELDS,
    "control_plane_preflight",
    "orchestration_alignment_summary",
    "market_specific_readiness_summary",
    "agent_binding_summary",
    "missing_record_ingestion_summary",
    "atomicrows_ingestion_summary",
    "universal_classical_quantum_intake_summary",
    "scoring_ranking_future_routing_summary",
    "optimizer_replay_paper_future_routing_summary",
    "blocked_completion_path_summary",
    "determinism_metadata_without_runtime_git_volatility",
    "validation_result",
)
REGISTRY_TOP_LEVEL_KEYS = (
    "registry_type",
    "pr_id",
    "semantic_task_id",
    "authority_class",
    "input_artifacts",
    "control_plane_preflight",
    "counts",
    "population_lanes",
    "agent_binding_records",
    "missing_record_ingestion_lanes",
    "atomicrows_universe_ingestion_summary",
    "universal_intake_templates",
    "records",
    "blocked_records",
    "non_authority_boundary",
    "validation_result",
)
RECORD_REQUIRED_FIELDS = (
    "pr156_record_id",
    "record_kind",
    "source_population",
    "source_record_ref",
    "source_record_type",
    "source_artifact_path",
    "source_authority_class",
    "population_lane",
    "agent_binding_state",
    "bound_agent_ids",
    "bound_agent_roles",
    "bound_consumer_classes",
    "binding_basis_artifacts",
    "binding_basis_reason",
    "binding_block_codes",
    "template_type",
    "candidate_instance_state",
    "candidate_origin",
    "candidate_origin_authority_class",
    "candidate_research_intake_state",
    "applicability_class",
    "owner_strategy_priority_state",
    "atomicrows_ingestion_state",
    "scoring_ranking_readiness_state",
    "optimizer_routing_hint",
    "replay_paper_routing_hint",
    "market_scope",
    "platform_scope",
    "route_triage_domain",
    "launch_readiness_domain",
    "section_crosswalk_refs",
    "market_specific_index_refs",
    "command_action_matrix_refs",
    "atomicrows_reconciliation_refs",
    "atomicrows_semantic_contract_refs",
    "pr155_registry_ref",
    "pr154_completion_ref",
    "blocked_completion_path_ref_or_inline",
    "future_completion_pr_hint",
    "future_scoring_ranking_pr_hint",
    "future_optimizer_pr_hint",
    "future_replay_paper_pr_hint",
    *RECORD_ALWAYS_FALSE_FIELDS,
    "non_authority_boundary",
    "created_by_pr",
    "authority_boundary",
)
DETERMINISTIC_SORT_KEYS = {
    "records": "pr156_record_id",
    "blocked_records": "pr156_record_id",
    "input_artifacts": "artifact_path",
}

NO_EXACT_PR136_RECORD_MAPPING = "PR156_MAPPING_UNKNOWN_NO_EXACT_RECORD_LEVEL_PR136_DOMAIN"
NO_EXPLICIT_BINDING_MAP_REASON = (
    "NO_EXPLICIT_AGENT_ROLE_OR_CONSUMER_CLASS_MAP_IN_CONSUMED_ARTIFACTS"
)
EXPLICIT_BINDING_MAP_REASON = "EXPLICIT_BINDING_FROM_CANONICAL_CONSUMED_ARTIFACT"
BLOCKED_PR154_BINDING_REASON = "PR154_COMPLETION_REQUIRED_BEFORE_AGENT_BINDING"
ATOMICROWS_COMPLETION_BINDING_REASON = (
    "ATOMICROWS_UNIVERSE_COMPLETION_REQUIRED_BEFORE_AGENT_BINDING"
)
TEMPLATE_ONLY_BINDING_REASON = "TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE_FOR_BINDING"
FUTURE_COMPLETION_PR_HINT = "FUTURE_COMPLETION_PR_REQUIRED"
FUTURE_SCORING_RANKING_PR_HINT = "FUTURE_SCORING_RANKING_GATE_REQUIRED"
FUTURE_OPTIMIZER_PR_HINT = "FUTURE_OPTIMIZER_ARBITRATION_OR_BACKEND_GATE_REQUIRED"
FUTURE_REPLAY_PAPER_PR_HINT = "FUTURE_REPLAY_PAPER_GATE_REQUIRED"
FUTURE_RESEARCH_INTAKE_PR_HINT = "FUTURE_RESEARCH_INTAKE_AND_SOURCE_EVIDENCE_PR_REQUIRED"

MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
FORBIDDEN_ATOMICROWS_BUNDLE_STEM_PARTS = ("AtomicRows", "bundle")
FORBIDDEN_ATOMICROWS_BUNDLE_DATA_SUFFIX = "jsonl"
FORBIDDEN_ATOMICROWS_BUNDLE_HASH_SUFFIX_PARTS = ("sha", "256")
BRANCH_TOKEN_SENTINEL_ALLOWED_DOMAINMAP = "DomainMap"
BRANCH_TOKEN_SENTINEL_BLOCKED_REF_PREFIX = "refs/heads/"

EXPLICIT_BINDING_RECORD_KEYS = (
    "agent_binding_records",
    "bindings",
    "binding_records",
    "allowed_bindings",
)
EXPLICIT_BINDING_SOURCE_REF_KEYS = (
    "pr155_registry_record_id",
    "registry_record_id",
    "source_record_ref",
    "source_pr155_record_id",
)
EXPLICIT_AGENT_ID_KEYS = ("agent_id", "agent_ids", "bound_agent_ids")
EXPLICIT_ROLE_KEYS = ("agent_role", "agent_roles", "bound_agent_roles")
EXPLICIT_CONSUMER_CLASS_KEYS = (
    "consumer_class",
    "consumer_classes",
    "bound_consumer_classes",
)

CHANGED_PATHS = (
    REGISTRY_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/__init__.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/agent_binding.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/atomicrows_ingestion.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/builder.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/classical_quantum_applicability.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/constants.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/future_routing.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/input_discovery.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/intake_templates.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/io.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/models.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/orchestration_preflight.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/population_router.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/report.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/schema_projection.py",
    "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/validator.py",
    "tools/validate_agent_default_binding_universal_intake_gate.py",
    "tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate/test_agent_default_binding_universal_intake_gate.py",
    "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry/test_agent_consumable_parameter_default_registry.py",
    "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tests/tools/test_ci_branch_context.py",
)
