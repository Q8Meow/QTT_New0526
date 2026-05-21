"""Central PR137 launch-readiness dependency-controller constants."""

from __future__ import annotations

from typing import Any


REPO_PR_LABEL = "PR137"
REQUIRED_BRANCH_NAME = "pr137-launch-roadmap-validator-readiness-controller"
TITLE = "Launch-roadmap validator and readiness dependency controller"
AUTHORITY_CLASS = "CANONICAL_POST_PR136_DEPENDENCY_CONTROLLER_NOT_EXECUTION_AUTHORITY"
TARGET_STATE = "STATIC_CONTRACT_READY"
SCOPE_CLASS = "ROADMAP_MAPPING"
GENERATED_AT_UTC = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
GENERATED_BY = (
    "src.qtt.stage1_prediction_markets.launch_readiness."
    "pr137_launch_readiness_dependency_controller"
)

CONTROLLER_VALIDATION_MARKER = "QTT_PR137_LAUNCH_READINESS_DEPENDENCY_CONTROLLER_OK"
GENERATED_INTEGRITY_VALIDATION_MARKER = (
    "QTT_PR137_GENERATED_INTEGRITY_AUTHORITY_BOUNDARY_OK"
)
VALIDATION_MARKERS = (
    CONTROLLER_VALIDATION_MARKER,
    GENERATED_INTEGRITY_VALIDATION_MARKER,
)

CANONICAL_MARKET_SCOPES = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
FORBIDDEN_FORECASTEX_ALIASES = (
    "FORECASTEX",
    "FORECASTX",
    "IBKR_FORECASTX",
    "forecastx",
)

CANONICAL_PR136_SEQUENCE_ENTRY_IDS = (
    "PR137",
    "PR137L",
    "PR138",
    "PR139",
    "PR140",
    "PR141",
    "PR142",
    "PR143K",
    "PR143P",
    "PR143F",
    "PR143",
    "PR144",
    "PR145",
    "PR146",
    "PR147",
    "PR148",
    "PR149",
    "PR150",
    "PR151",
    "PR152",
    "PR153",
    "PR154",
    "PR155",
    "PR156",
    "PR157",
    "PR158",
    "PR159",
    "PR160",
    "PR161",
    "PR162",
    "PR163",
    "PR164",
)

REQUIRED_DEPENDENCY_EDGES = tuple(
    zip(CANONICAL_PR136_SEQUENCE_ENTRY_IDS, CANONICAL_PR136_SEQUENCE_ENTRY_IDS[1:])
)

FUTURE_OWNER_AUTHORIZED_GATES = (
    "PR141",
    "PR142",
    "PR143K",
    "PR143P",
    "PR143F",
    "PR143",
    "PR144",
    "PR145",
    "PR146",
    "PR147",
    "PR148",
    "PR151",
    "PR154",
    "PR156",
    "PR157",
    "PR158",
    "PR159",
    "PR160",
    "PR161",
    "PR164",
)

MISSING_MARKET_PREREQUISITE_CLASSES = (
    "accepted_source_evidence",
    "connector_semantic_binding",
    "credential_private_state_cash_readiness",
    "market_data_live_readiness",
    "order_lifecycle_readiness",
    "replay_paper_evidence",
    "owner_approval",
    "canary_preflight",
    "day1_launch_preflight",
    "risk_readiness",
    "latency_boundary_readiness",
)

AGENT_IDS = (
    "research_source_agent",
    "source_evidence_agent",
    "connector_semantic_agent",
    "credential_private_state_cash_agent",
    "market_data_agent",
    "runtime_resolver_agent",
    "historical_dataset_agent",
    "atomicrows_agent",
    "quantum_optimizer_agent",
    "classical_optimizer_agent",
    "parameter_stack_agent",
    "replay_agent",
    "paper_agent",
    "risk_agent",
    "owner_approval_agent",
    "dashboard_agent",
    "canary_execution_agent",
    "post_trade_reconciliation_agent",
    "launch_runbook_agent",
)

AGENT_FUTURE_DEPENDENCY_PRS = {
    "research_source_agent": ("PR137", "PR143K", "PR143P", "PR143F", "PR143"),
    "source_evidence_agent": ("PR143K", "PR143P", "PR143F", "PR143"),
    "connector_semantic_agent": ("PR143", "PR144"),
    "credential_private_state_cash_agent": ("PR145",),
    "market_data_agent": ("PR137L", "PR143", "PR157", "PR162"),
    "runtime_resolver_agent": ("PR137L", "PR145", "PR146"),
    "historical_dataset_agent": ("PR138", "PR146"),
    "atomicrows_agent": ("PR138", "PR139", "PR140", "PR141", "PR142"),
    "quantum_optimizer_agent": ("PR150", "PR151", "PR152", "PR153"),
    "classical_optimizer_agent": ("PR150", "PR151", "PR152", "PR153"),
    "parameter_stack_agent": ("PR150", "PR152", "PR153"),
    "replay_agent": ("PR146", "PR147", "PR149"),
    "paper_agent": ("PR146", "PR148", "PR149"),
    "risk_agent": ("PR157", "PR158", "PR159", "PR160"),
    "owner_approval_agent": ("PR154", "PR156", "PR164"),
    "dashboard_agent": ("PR155", "PR156"),
    "canary_execution_agent": ("PR157", "PR158", "PR159", "PR160"),
    "post_trade_reconciliation_agent": ("PR159", "PR160"),
    "launch_runbook_agent": ("PR162", "PR163", "PR164"),
}

NO_AUTHORITY_FLAGS = {
    "auto_authorizes_later_pr": False,
    "auto_authorizes_pr137l": False,
    "auto_authorizes_pr138": False,
    "creates_alpha_evidence": False,
    "creates_atomicrows_bundle": False,
    "creates_atomicrows_materialization_authority": False,
    "creates_atomicrows_rows": False,
    "creates_canary_execution": False,
    "creates_connector_binding": False,
    "creates_credential_resolution": False,
    "creates_day1_live_launch": False,
    "creates_execution_superiority_evidence": False,
    "creates_fill_receipt": False,
    "creates_latency_superiority_evidence": False,
    "creates_live_command": False,
    "creates_live_data": False,
    "creates_order_authority": False,
    "creates_order_execution": False,
    "creates_owner_approval_receipt": False,
    "creates_paper_execution": False,
    "creates_paper_result": False,
    "creates_private_state_fetch": False,
    "creates_profit_evidence": False,
    "creates_quantum_advantage_claim": False,
    "creates_quantum_backend_call": False,
    "creates_quantum_execution": False,
    "creates_quantum_optimizer_input": False,
    "creates_quantum_simulator_execution": False,
    "creates_quantum_trading_signal": False,
    "creates_ranking_scoring_arbitration_output": False,
    "creates_replay_execution": False,
    "creates_replay_result": False,
    "creates_runtime_cash_authority": False,
    "creates_source_acceptance": False,
    "creates_source_retrieval": False,
    "creates_trading_signal": False,
}

PR136_SELECTOR_ARTIFACTS = (
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json",
    "docs/master_plan/generated/PR136FuturePRCardRegistry.report.json",
    "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
    "docs/master_plan/generated/PR136ReadinessDomainTaxonomy.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json",
    "docs/master_plan/generated/PR136LatencyControlPlaneVsLivePathMap.report.json",
    "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
    "docs/master_plan/generated/PR136PolicyManifest.report.json",
    "docs/master_plan/generated/PR136ValidationGateIntegration.report.json",
    "docs/master_plan/generated/PR136PathDecision.report.json",
)

ROADMAP_CONTEXT_ARTIFACTS = (
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
    "docs/master_plan/completion/QTTSectionCoverageRegistry.yaml",
    "tools/run_validation_gates.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tools/validate_pr136_day1_launch_readiness_roadmap.py",
    "tools/validate_pr136_roadmap_policy_literal_drift.py",
    "tests/roadmap/test_pr136_day1_launch_readiness_roadmap.py",
)

MANDATORY_READ_ARTIFACTS = PR136_SELECTOR_ARTIFACTS + ROADMAP_CONTEXT_ARTIFACTS

PROTECTED_FILE_PATHS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
)

REPORT_NAMES = (
    "PR137LaunchReadinessDependencyController.report.json",
    "PR137DependencyGateStateMatrix.report.json",
    "PR137MarketReadinessDependencyMatrix.report.json",
    "PR137AgentDependencyController.report.json",
    "PR137QuantumAtomicRowsDependencyBoundary.report.json",
    "PR137GeneratedIntegrityAuthorityBoundary.report.json",
    "PR137ValidationGateIntegration.report.json",
)

SCHEMA_NAMES = (
    "pr137_launch_readiness_dependency_controller.schema.json",
    "pr137_launch_readiness_dependency_node.schema.json",
    "pr137_launch_readiness_dependency_edge.schema.json",
    "pr137_market_dependency_state.schema.json",
    "pr137_generated_integrity_authority_boundary.schema.json",
)

RECEIPT_NAMES = (
    "CODEX_PR137_MANDATORY_READ_RECEIPT.json",
    "CODEX_PR137_ROUTE_TRIAGE_RECEIPT.json",
)

ROADMAP_DOC_PATH = "docs/roadmap/QTT_PR137_Launch_Readiness_Dependency_Controller_v1_0.md"
REPORT_DIR = "docs/master_plan/generated"
SCHEMA_DIR = "schemas/roadmap"
ROADMAP_GENERATED_DIR = "docs/roadmap/generated"

ALLOWED_ARTIFACT_PATHS = (
    "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
    "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
    "tools/validate_pr137_launch_readiness_dependency_controller.py",
    "tools/validate_pr137_generated_integrity_authority_boundary.py",
    "tests/roadmap/test_pr137_launch_readiness_dependency_controller.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "tools/run_validation_gates.py",
    ROADMAP_DOC_PATH,
    *(f"{SCHEMA_DIR}/{name}" for name in SCHEMA_NAMES),
    *(f"{REPORT_DIR}/{name}" for name in REPORT_NAMES),
    *(f"{ROADMAP_GENERATED_DIR}/{name}" for name in RECEIPT_NAMES),
)


def no_authority_flags() -> dict[str, bool]:
    return dict(NO_AUTHORITY_FLAGS)


def report_paths() -> tuple[str, ...]:
    return tuple(f"{REPORT_DIR}/{name}" for name in REPORT_NAMES)


def schema_paths() -> tuple[str, ...]:
    return tuple(f"{SCHEMA_DIR}/{name}" for name in SCHEMA_NAMES)


def receipt_paths() -> tuple[str, ...]:
    return tuple(f"{ROADMAP_GENERATED_DIR}/{name}" for name in RECEIPT_NAMES)


def policy_manifest() -> dict[str, Any]:
    return {
        "allowed_artifact_refs": list(ALLOWED_ARTIFACT_PATHS),
        "authority_class": AUTHORITY_CLASS,
        "branch_name": REQUIRED_BRANCH_NAME,
        "canonical_market_scopes": list(CANONICAL_MARKET_SCOPES),
        "canonical_report_names": list(REPORT_NAMES),
        "canonical_schema_names": list(SCHEMA_NAMES),
        "canonical_sequence_entry_ids": list(CANONICAL_PR136_SEQUENCE_ENTRY_IDS),
        "generated_at_utc": GENERATED_AT_UTC,
        "generated_by": GENERATED_BY,
        "no_authority_flags": no_authority_flags(),
        "pr136_selector_refs": list(PR136_SELECTOR_ARTIFACTS),
        "protected_file_refs": list(PROTECTED_FILE_PATHS),
        "receipt_type": "PR137_POLICY_MANIFEST",
        "repo_pr_number_or_label": REPO_PR_LABEL,
        "report_type": "PR137_POLICY_MANIFEST",
        "report_version": "PR137_POLICY_MANIFEST_V1",
        "required_dependency_edges": [
            {"from_node_id": source, "to_node_id": target}
            for source, target in REQUIRED_DEPENDENCY_EDGES
        ],
        "scope_class": SCOPE_CLASS,
        "target_state": TARGET_STATE,
        "validation_markers": list(VALIDATION_MARKERS),
    }
