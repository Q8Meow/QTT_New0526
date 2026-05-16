#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "agents"
    / "qtt_agent_role_operating_charter_registry.schema.json"
)
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "agents"
    / "QTTAgentRoleOperatingCharterRegistry.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "agents"
    / "synthetic_qtt_agent_role_operating_charter_registry.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAgentRoleOperatingCharterReport.json"
)
MASTER_PLAN = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REGISTRY_TYPE = "QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY"
REGISTRY_VERSION = "v1"
REPORT_TYPE = "QTT_AGENT_ROLE_OPERATING_CHARTER_REPORT"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
ARCHITECTURE_EMPHASIS = "INSTITUTIONAL_AGENT_OPERATING_CHARTER_NOT_PROHIBITION_LIST"
OWNER_OVERRIDE_SATISFACTION_BASIS = (
    "OWNER_GLOBAL_OVERRIDE_SATISFIES_QTT_INTERNAL_WORKFLOW_REQUIREMENTS"
)
STATIC_FORWARD_REFERENCE_ONLY = "STATIC_FORWARD_REFERENCE_ONLY"
FINAL_STATUS = (
    "STATIC_CHARTER_DECLARED_NOT_FINAL_PRODUCTION_READY_OWNER_OVERRIDE_SUPPORTED"
)
SUCCESS_MARKER = "QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY_OK"
FAILURE_MARKER = "QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY_FAILED"
FINAL_INCOMPLETE_MARKER = "QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY_FINAL_INCOMPLETE"

TOP_FIELDS = (
    "registry_type",
    "registry_version",
    "deterministic_output",
    "generated_at_utc",
    "source_of_role_substance",
    "master_plan_followed_as_controlling_doctrine",
    "existing_pr_patterns_used_for_style_only",
    "pr64_is_scope_boundary_not_role_authority",
    "architecture_emphasis",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "chatgpt_authority_over_owner",
    "codex_authority_over_owner",
    "qtt_agent_authority_over_owner",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "quantum_priority_forward_compatible",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "profit_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
    "agent_charters",
)

FIXTURE_EXTRA_FIELDS = (
    "execution",
    "mode",
)

CHARTER_FIELDS = (
    "agent_role",
    "agent_role_id",
    "agent_description",
    "master_plan_doctrine_terms_used",
    "master_plan_role_derivation_summary",
    "master_plan_static_authority_basis",
    "master_plan_runtime_boundary_basis",
    "primary_duties",
    "secondary_duties",
    "owned_surfaces",
    "consumed_artifacts",
    "emitted_artifacts",
    "decision_authority_scope",
    "forbidden_decision_authority",
    "handoff_inputs",
    "handoff_outputs",
    "input_packet_types",
    "output_packet_types",
    "applicable_parameter_family_scopes",
    "applicable_algorithm_family_scopes",
    "authorized_consumer_classes",
    "orchestration_spine_relationship",
    "risk_gate_relationship",
    "execution_router_relationship",
    "receipt_event_log_relationship",
    "coverage_health_monitor_relationship",
    "source_to_connector_to_resolver_relationship",
    "replay_paper_dual_review_relationship",
    "optimizer_arbitration_relationship",
    "dashboard_owner_control_relationship",
    "owner_override_supported",
    "owner_override_satisfaction_basis",
    "owner_approved_scope",
    "may_request_owner_approval",
    "approval_request_behavior",
    "may_approve_for_owner",
    "codex_may_approve_for_owner",
    "chatgpt_may_approve_for_owner",
    "qtt_agent_authority_over_owner",
    "blocks_qtt_when_owner_override_present",
    "classical_scope",
    "quantum_scope",
    "quantum_applicability_scope",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
    "quantum_priority_forward_compatible",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority",
    "quantum_backend_artifact_created",
    "quantum_runtime_authority_created",
    "true_quantum_execution_created",
    "quantum_evidence_claim_created",
    "quantum_scoring_policy_reference",
    "quantum_classical_arbitration_reference",
    "runtime_scope",
    "live_scope",
    "dashboard_scope",
    "source_evidence_scope",
    "connector_scope",
    "atomicrows_scope",
    "fallback_behavior",
    "escalation_behavior",
    "final_qtt_internal_status",
)

ARRAY_FIELDS = {
    "master_plan_doctrine_terms_used",
    "primary_duties",
    "secondary_duties",
    "owned_surfaces",
    "consumed_artifacts",
    "emitted_artifacts",
    "forbidden_decision_authority",
    "handoff_inputs",
    "handoff_outputs",
    "input_packet_types",
    "output_packet_types",
    "applicable_parameter_family_scopes",
    "applicable_algorithm_family_scopes",
    "authorized_consumer_classes",
    "quantum_applicability_scope",
    "quantum_algorithm_family_access",
    "quantum_parameter_family_access",
}

RELATIONSHIP_FIELDS = (
    "orchestration_spine_relationship",
    "risk_gate_relationship",
    "execution_router_relationship",
    "receipt_event_log_relationship",
    "coverage_health_monitor_relationship",
    "source_to_connector_to_resolver_relationship",
    "replay_paper_dual_review_relationship",
    "optimizer_arbitration_relationship",
    "dashboard_owner_control_relationship",
)

ROLE_ORDER = (
    "OWNER",
    "ORCHESTRATOR_AGENT",
    "MASTER_PLAN_AGENT",
    "ATOMICROWS_AGENT",
    "ATOMICROWS_RESEARCH_AGENT",
    "ATOMICROWS_LIFECYCLE_AGENT",
    "SOURCE_EVIDENCE_AGENT",
    "CONNECTOR_AGENT",
    "RUNTIME_RESOLVER_AGENT",
    "REPLAY_AGENT",
    "PAPER_AGENT",
    "DUAL_RESULT_REVIEW_AGENT",
    "OPTIMIZER_AGENT",
    "RISK_AGENT",
    "SIZING_AGENT",
    "EXECUTION_LATENCY_AGENT",
    "ORDER_ROUTER_AGENT",
    "LIVE_CANARY_AGENT",
    "QUANTUM_RESEARCH_AGENT",
    "QUANTUM_BACKEND_AGENT",
    "DASHBOARD_AGENT",
    "GOVERNANCE_AGENT",
    "VALIDATION_AGENT",
    "COMPLIANCE_MARKER_AGENT",
    "OWNER_APPROVAL_REQUEST_AGENT",
)

ROLE_IDS = {
    role: f"QTT_AGENT_ROLE_{index:03d}_{role}"
    for index, role in enumerate(ROLE_ORDER, start=1)
}

TOP_CONST_EXPECTATIONS = {
    "registry_type": REGISTRY_TYPE,
    "registry_version": REGISTRY_VERSION,
    "deterministic_output": True,
    "generated_at_utc": DETERMINISTIC_GENERATED_AT,
    "source_of_role_substance": MASTER_PLAN.as_posix(),
    "master_plan_followed_as_controlling_doctrine": True,
    "existing_pr_patterns_used_for_style_only": True,
    "pr64_is_scope_boundary_not_role_authority": True,
    "architecture_emphasis": ARCHITECTURE_EMPHASIS,
    "owner_global_override_authority": True,
    "owner_override_satisfies_all_qtt_internal_requirements": True,
    "chatgpt_authority_over_owner": False,
    "codex_authority_over_owner": False,
    "qtt_agent_authority_over_owner": False,
    "quantum_forward_design_supported": True,
    "quantum_evidence_claim_created": False,
    "quantum_priority_forward_compatible": True,
    "owner_quantum_priority_supported": True,
    "owner_can_force_quantum_priority": True,
    "runtime_artifact_created": False,
    "live_artifact_created": False,
    "order_artifact_created": False,
    "source_acceptance_artifact_created": False,
    "connector_binding_artifact_created": False,
    "runtime_resolver_snapshot_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "quantum_backend_artifact_created": False,
    "profit_artifact_created": False,
    "bundle_file_present": False,
    "bundle_sha_present": False,
    "uses_pr_number_as_authority": False,
    "final_ready": False,
}

FALSE_CHARTER_FLAGS = (
    "may_approve_for_owner",
    "codex_may_approve_for_owner",
    "chatgpt_may_approve_for_owner",
    "qtt_agent_authority_over_owner",
    "blocks_qtt_when_owner_override_present",
    "quantum_backend_artifact_created",
    "quantum_runtime_authority_created",
    "true_quantum_execution_created",
    "quantum_evidence_claim_created",
)

TRUE_CHARTER_FLAGS = (
    "owner_override_supported",
    "may_request_owner_approval",
    "quantum_priority_forward_compatible",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority",
)

QUANTUM_COMPATIBILITY_CLASSES = (
    "TRUE_QUANTUM",
    "QUANTUM_INSPIRED",
    "HYBRID_CLASSICAL_QUANTUM",
    "QUBO_COMPATIBLE",
    "ISING_COMPATIBLE",
    "QAOA_COMPATIBLE",
    "VQE_COMPATIBLE",
    "ANNEALING_COMPATIBLE",
    "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE",
    "OWNER_QUANTUM_PRIORITY",
    "OWNER_FORCED_QUANTUM",
    "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK",
    "STRONGEST_CLASSICAL_COMPARATOR_REQUIRED",
    "FALLBACK_BUNDLE_REQUIRED",
    "REPLAY_PAPER_EVIDENCE_REQUIRED_BEFORE_ADVANTAGE_CLAIM",
)

QUANTUM_RELEVANT_ROLES = {
    "OWNER",
    "OPTIMIZER_AGENT",
    "QUANTUM_RESEARCH_AGENT",
    "QUANTUM_BACKEND_AGENT",
    "RISK_AGENT",
    "SIZING_AGENT",
    "EXECUTION_LATENCY_AGENT",
    "ORDER_ROUTER_AGENT",
}

OWNER_FORCE_QUANTUM_REQUIRED_ROLES = QUANTUM_RELEVANT_ROLES

PR_NUMBER_PATTERN = re.compile(
    r"\bPR\s*#?\s*\d+\b|(?<![A-Za-z])pr\d+\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RoleSpec:
    description: str
    doctrine_terms: tuple[str, ...]
    derivation: str
    static_basis: str
    runtime_boundary: str
    primary_duties: tuple[str, ...]
    secondary_duties: tuple[str, ...]
    owned_surfaces: tuple[str, ...]
    consumed_artifacts: tuple[str, ...]
    emitted_artifacts: tuple[str, ...]
    decision_scope: str
    forbidden_authority: tuple[str, ...]
    handoff_inputs: tuple[str, ...]
    handoff_outputs: tuple[str, ...]
    input_packets: tuple[str, ...]
    output_packets: tuple[str, ...]
    parameter_scopes: tuple[str, ...]
    algorithm_scopes: tuple[str, ...]
    consumer_classes: tuple[str, ...]
    orchestration: str
    risk: str
    router: str
    receipt: str
    health: str
    source_connector_resolver: str
    replay_paper: str
    optimizer: str
    dashboard: str
    owner_scope: str
    approval_behavior: str
    classical_scope: str
    quantum_scope: str
    runtime_scope: str
    live_scope: str
    dashboard_scope: str
    source_scope: str
    connector_scope: str
    atomicrows_scope: str
    fallback_behavior: str
    escalation_behavior: str


ROLE_SPECS: dict[str, RoleSpec] = {
    "OWNER": RoleSpec(
        description=(
            "Final QTT internal policy authority for approvals, overrides, vetoes, "
            "risk tolerance, launch scope, dashboard control, and quantum priority."
        ),
        doctrine_terms=(
            "owner final policy authority",
            "owner_source_evidence_definitions_packet_external_fact_acceptance_authority",
            "owner quantum priority",
            "QTT orchestration-spine law",
        ),
        derivation=(
            "Mapped to the master-plan owner authority doctrine: the owner controls "
            "internal QTT policy and approvals while external facts and runtime receipts "
            "remain evidence-bound."
        ),
        static_basis=(
            "Static charter records owner policy authority and future receipt surfaces "
            "without creating source, runtime, or live evidence."
        ),
        runtime_boundary=(
            "Owner decisions can satisfy QTT internal workflow requirements but cannot "
            "make external facts, fills, cash, replay, paper, quantum execution, or profit "
            "evidence true by assertion."
        ),
        primary_duties=(
            "Set internal QTT policy, launch scope, risk tolerance, and quantum-priority direction.",
            "Approve, override, veto, pause, disable, or de-scope QTT internal workflows.",
            "Receive escalation packets and issue owner approval or override receipts in later phases.",
        ),
        secondary_duties=(
            "Choose stricter gates when uncertainty, stale evidence, or conflict is present.",
            "Direct dashboard control decisions without granting dashboard trading authority.",
        ),
        owned_surfaces=(
            "OWNER_POLICY",
            "OWNER_APPROVAL",
            "OWNER_OVERRIDE",
            "OWNER_QUANTUM_PRIORITY",
            "OWNER_LAUNCH_SCOPE",
            "OWNER_RISK_TOLERANCE",
        ),
        consumed_artifacts=(
            "OWNER_APPROVAL_REQUEST_PACKET",
            "GOVERNANCE_BOUNDARY_PACKET",
            "RISK_ESCALATION_PACKET",
        ),
        emitted_artifacts=(
            "OWNER_APPROVAL_RECEIPT",
            "OWNER_OVERRIDE_RECEIPT",
            "OWNER_POLICY_CHANGE_RECEIPT",
            "OWNER_QUANTUM_PRIORITY_RECEIPT",
        ),
        decision_scope=(
            "May decide internal QTT policy, approval, override, launch scope, and "
            "quantum-priority settings."
        ),
        forbidden_authority=(
            "Cannot fabricate accepted source facts, runtime receipts, fills, balances, or profit evidence.",
            "Cannot replace source, connector, resolver, replay, paper, risk, cash, or router evidence gates.",
        ),
        handoff_inputs=("OWNER_DECISION_QUEUE", "ESCALATION_PACKET"),
        handoff_outputs=("OWNER_DECISION_RECEIPT", "OWNER_POLICY_ROUTE"),
        input_packets=("OWNER_APPROVAL_REQUEST_PACKET", "OWNER_OVERRIDE_REQUEST_PACKET"),
        output_packets=("OWNER_APPROVAL_RECEIPT", "OWNER_OVERRIDE_RECEIPT"),
        parameter_scopes=("OWNER_POLICY_PARAMETER_SCOPE", "OWNER_QUANTUM_PRIORITY_SCOPE"),
        algorithm_scopes=("OWNER_APPROVED_ALGORITHM_SCOPE", "OWNER_FORCED_QUANTUM_PRIORITY_SCOPE"),
        consumer_classes=("GOVERNANCE", "DASHBOARD_CONTROL", "APPROVAL_ROUTING"),
        orchestration="Owner is the top internal authority consumed by the Decision Orchestrator.",
        risk="Owner sets risk tolerance and can demand stricter gates; Risk Gate still evaluates evidence.",
        router="Owner approval is necessary for live scope but the Execution Router remains final order-submission authority.",
        receipt="Owner approvals and overrides are future receipt events recorded in the event log.",
        health="Coverage and health monitoring must show owner authority without treating it as external fact evidence.",
        source_connector_resolver="Owner may define source policy, but accepted source packets and resolver snapshots require evidence workflows.",
        replay_paper="Owner reviews replay and paper outcomes; owner review does not merge non-live evidence into live proof.",
        optimizer="Owner may force quantum-priority policy, while optimizer arbitration still requires objective, comparator, and evidence.",
        dashboard="Owner controls dashboard decisions; dashboard surfaces requests and status, not autonomous trades.",
        owner_scope="OWNER_APPROVED_INTERNAL_POLICY_SCOPE",
        approval_behavior="Receives approval requests and emits owner decision receipts in later scoped workflows.",
        classical_scope="OWNER_CLASSICAL_POLICY_AND_REVIEW_SCOPE",
        quantum_scope="OWNER_QUANTUM_PRIORITY_AND_OWNER_FORCED_QUANTUM_POLICY_SCOPE",
        runtime_scope="STATIC_OWNER_CHARTER_ONLY_NO_RUNTIME_RECEIPT_CREATED",
        live_scope="OWNER_LIVE_SCOPE_DECISION_SURFACE_ONLY_NO_LIVE_ARTIFACT_CREATED",
        dashboard_scope="OWNER_CONTROL_AND_APPROVAL_SURFACE_FOR_LATER_DASHBOARD_IMPLEMENTATION",
        source_scope="OWNER_SOURCE_POLICY_INPUT_ONLY_NOT_ACCEPTED_FACT_AUTHORITY",
        connector_scope="OWNER_APPROVAL_CONSUMER_OF_CONNECTOR_READINESS_NOT_BINDING_CREATOR",
        atomicrows_scope="OWNER_CAN_DIRECT_PARAMETER_POLICY_WITHOUT_CREATING_BUNDLE_OR_HASH",
        fallback_behavior="When owner policy is absent, stricter gates and explicit approval queues apply.",
        escalation_behavior="Owner receives unresolved governance, risk, launch, and quantum-priority escalations.",
    ),
    "ORCHESTRATOR_AGENT": RoleSpec(
        description=(
            "Coordinates governed QTT agent handoffs through the master-plan orchestration spine."
        ),
        doctrine_terms=(
            "Decision Orchestrator",
            "QTT orchestration-spine law",
            "agent_autonomy_class",
            "execution_router_remains_final_order_submission_authority_flag",
        ),
        derivation=(
            "Mapped to Decision Orchestrator doctrine requiring all market decisions to route "
            "through registered agents, typed artifacts, risk gates, execution routing, and receipts."
        ),
        static_basis="Static charter records workflow ownership and dependency ordering only.",
        runtime_boundary="Does not self-authorize trades or create runtime handoff receipts in this package.",
        primary_duties=(
            "Route decisions across source evidence, connector readiness, resolver readiness, AtomicRows, optimizer, risk, sizing, latency, router, replay, paper, dual review, owner approval, and validation.",
            "Maintain dependency order and fail-closed escalation when required inputs are absent.",
            "Emit orchestration handoff and dependency status packet definitions for later workflows.",
        ),
        secondary_duties=(
            "Coordinate agent retry, reroute, quarantine, and candidate replacement requests under governance.",
            "Expose missing duty and trust-score inputs to validation and health monitoring.",
        ),
        owned_surfaces=("WORKFLOW_ROUTING", "DEPENDENCY_ORDER", "FAIL_CLOSED_ESCALATION"),
        consumed_artifacts=("AGENT_STATUS_PACKET", "DEPENDENCY_STATUS_PACKET", "OWNER_POLICY_PACKET"),
        emitted_artifacts=("ORCHESTRATION_HANDOFF_PACKET", "DEPENDENCY_STATUS_PACKET"),
        decision_scope="May decide internal routing order and escalation path for registered QTT agents.",
        forbidden_authority=(
            "May not approve for owner.",
            "May not send orders, bypass risk, or make source evidence true.",
        ),
        handoff_inputs=("SOURCE_EVIDENCE_STATUS", "CONNECTOR_READINESS_STATUS", "OPTIMIZER_CANDIDATE_STATUS"),
        handoff_outputs=("NEXT_AGENT_HANDOFF", "FAIL_CLOSED_ESCALATION"),
        input_packets=("AGENT_TASK_PACKET", "DEPENDENCY_STATUS_PACKET"),
        output_packets=("ORCHESTRATION_HANDOFF_PACKET", "MISSING_DEPENDENCY_PACKET"),
        parameter_scopes=("ORCHESTRATION_PARAMETER_UNIVERSE", "AGENT_TASK_PRIORITY_PARAMETERS"),
        algorithm_scopes=("DETERMINISTIC_ROUTING_ALGORITHM", "FAIL_CLOSED_DEPENDENCY_SORT"),
        consumer_classes=("ORCHESTRATION", "VALIDATION", "DASHBOARD_STATUS"),
        orchestration="Owns the Decision Orchestrator relationship for all agent-to-agent handoffs.",
        risk="Sends risk-relevant proposed intents to Risk Gate and honors risk blocks.",
        router="Routes only approved intents toward the Execution Router after prerequisite gates.",
        receipt="Defines handoff packet expectations for the future Receipt / Event Log.",
        health="Feeds agent KPI, missed-duty, trust-score, and reroute status to health monitoring.",
        source_connector_resolver="Routes source to connector to resolver only when upstream prerequisites are present.",
        replay_paper="Coordinates replay and paper lanes as separate non-live evidence flows.",
        optimizer="Routes edge hypotheses and AtomicRows inventory toward deterministic optimizer arbitration.",
        dashboard="Feeds owner-visible workflow status and approval needs to dashboard surfaces.",
        owner_scope="OWNER_APPROVED_ORCHESTRATION_SCOPE",
        approval_behavior="Packages workflow blockers for owner approval through the request agent.",
        classical_scope="CLASSICAL_DETERMINISTIC_DEPENDENCY_ROUTING_SCOPE",
        quantum_scope="QUANTUM_AWARE_ROUTING_SCOPE_WITH_NO_BACKEND_EXECUTION",
        runtime_scope="STATIC_ORCHESTRATION_CHARTER_ONLY_NO_RUNTIME_SERVICE_CREATED",
        live_scope="NO_LIVE_AUTHORITY; FUTURE LIVE HANDOFFS REQUIRE ALL GATES",
        dashboard_scope="OWNER_VISIBLE_ORCHESTRATION_STATUS_FOR_LATER_DASHBOARD",
        source_scope="ROUTES_SOURCE_EVIDENCE_STATUS_WITHOUT_ACCEPTING_FACTS",
        connector_scope="ROUTES_CONNECTOR_READINESS_WITHOUT_CREATING_BINDINGS",
        atomicrows_scope="ROUTES_ATOMICROWS_PARAMETER_INVENTORY_WITHOUT_CREATING_BUNDLE",
        fallback_behavior="If dependencies are absent, reroute to validation, governance, or owner approval.",
        escalation_behavior="Escalates stale, conflicted, missing, or unauthorized paths fail-closed.",
    ),
    "MASTER_PLAN_AGENT": RoleSpec(
        description="Maps controlling master-plan doctrine into implementation-facing static contracts.",
        doctrine_terms=("docs/master_plan/QTT_MasterPlan_Current.md", "master plan source of truth", "QTT orchestration-spine law"),
        derivation="Derived from the master plan being the controlling doctrine source for QTT roles and authority.",
        static_basis="Reads and maps doctrine for static implementation artifacts; preserves the master plan unchanged.",
        runtime_boundary="Does not edit the master plan or create runtime behavior in this package.",
        primary_duties=(
            "Read and map master-plan doctrine into role derivation summaries.",
            "Surface doctrine conflicts, section ownership, and static authority bases.",
            "Preserve no-edit master-plan behavior for this static package.",
        ),
        secondary_duties=("Support validation traceability from registry fields to doctrine terms.",),
        owned_surfaces=("DOCTRINE_MAPPING", "ROLE_DERIVATION", "SECTION_OWNER_LOOKUP"),
        consumed_artifacts=("QTT_MASTER_PLAN_CURRENT", "MASTER_PLAN_TERM_SEARCH_RESULTS"),
        emitted_artifacts=("MASTER_PLAN_DERIVATION_SUMMARY", "STATIC_DOCTRINE_MAP"),
        decision_scope="May classify which master-plan terms support each static charter field.",
        forbidden_authority=("May not edit the master plan in this package.", "May not promote prompt text over master-plan doctrine."),
        handoff_inputs=("MASTER_PLAN_TEXT", "TERM_SEARCH_SET"),
        handoff_outputs=("DOCTRINE_DERIVATION_PACKET", "CONFLICT_SURFACE_PACKET"),
        input_packets=("MASTER_PLAN_SCAN_PACKET",),
        output_packets=("ROLE_DERIVATION_PACKET", "STATIC_DOCTRINE_MAP_PACKET"),
        parameter_scopes=("MASTER_PLAN_TRACEABILITY_PARAMETERS",),
        algorithm_scopes=("DETERMINISTIC_TERM_MAPPING", "SECTION_OWNER_LOOKUP"),
        consumer_classes=("VALIDATION", "GOVERNANCE", "ORCHESTRATION"),
        orchestration="Supplies doctrine maps to the orchestrator for governed role routing.",
        risk="Identifies master-plan risk gate doctrine but does not make risk decisions.",
        router="Identifies Execution Router doctrine without creating order-routing authority.",
        receipt="Maps receipt/event-log doctrine for later packet producers.",
        health="Supports health monitor checks proving coded behavior still follows the plan.",
        source_connector_resolver="Maps source, connector, and resolver doctrine without accepting sources or bindings.",
        replay_paper="Maps replay, paper, and dual review doctrine as separate future evidence lanes.",
        optimizer="Maps deterministic scoring, ranking, and quantum/classical arbitration doctrine.",
        dashboard="Maps dashboard owner-control and research-intake boundaries.",
        owner_scope="OWNER_APPROVED_DOCTRINE_MAPPING_SCOPE",
        approval_behavior="Escalates doctrine ambiguity to owner approval request packaging.",
        classical_scope="CLASSICAL_STATIC_DOCTRINE_MAPPING_SCOPE",
        quantum_scope="QUANTUM_DOCTRINE_MAPPING_SCOPE_WITH_NO_EVIDENCE_CLAIM",
        runtime_scope="STATIC_DOCTRINE_AGENT_ONLY_NO_RUNTIME_CREATED",
        live_scope="NO_LIVE_SCOPE_CREATED",
        dashboard_scope="MAY_FEED_STATIC_DOCTRINE_STATUS_TO_LATER_DASHBOARD",
        source_scope="SOURCE_EVIDENCE_DOCTRINE_MAPPING_ONLY",
        connector_scope="CONNECTOR_DOCTRINE_MAPPING_ONLY",
        atomicrows_scope="ATOMICROWS_INVENTORY_DOCTRINE_MAPPING_ONLY",
        fallback_behavior="If doctrine is ambiguous, preserve stricter boundary and escalate.",
        escalation_behavior="Escalates master-plan conflict or missing doctrine to governance and owner request agents.",
    ),
    "ATOMICROWS_AGENT": RoleSpec(
        description="Owns AtomicRows parameter and algorithm inventory surfaces as inventory, not trading authority.",
        doctrine_terms=("atomicrows_bundle_is_parameter_algorithm_inventory_not_trader_flag", "edge_parameter_stack_selection_required_flag", "Parameter Pack Registry"),
        derivation="Mapped to AtomicRows inventory law and parameter pack registry doctrine.",
        static_basis="Records inventory consumer duties without creating bundle or hash artifacts.",
        runtime_boundary="Does not create AtomicRows.bundle.jsonl or AtomicRows.bundle.sha256 here.",
        primary_duties=(
            "Maintain AtomicRows as parameter and algorithm inventory authority.",
            "Expose parameter-family and algorithm-family surfaces to selection and optimizer consumers.",
            "Preserve inventory boundaries so AtomicRows does not become a trader.",
        ),
        secondary_duties=("Coordinate with lifecycle and research agents for readiness and candidate intake.",),
        owned_surfaces=("ATOMICROWS_INVENTORY", "PARAMETER_FAMILY_SURFACE", "ALGORITHM_FAMILY_SURFACE"),
        consumed_artifacts=("PARAMETER_FAMILY_REFERENCE", "ALGORITHM_FAMILY_REFERENCE", "LIFECYCLE_STATUS"),
        emitted_artifacts=("INVENTORY_CONSUMER_PACKET", "PARAMETER_FAMILY_SURFACE_REFERENCE"),
        decision_scope="May classify parameter and algorithm inventory surfaces for future consumers.",
        forbidden_authority=("May not trade or create direct trade paths.", "May not create the AtomicRows bundle or hash in this package."),
        handoff_inputs=("RESEARCH_PARAMETER_CANDIDATE", "LIFECYCLE_STATUS_PACKET"),
        handoff_outputs=("ATOMICROWS_INVENTORY_REFERENCE", "PARAMETER_SELECTION_UNIVERSE_POINTER"),
        input_packets=("PARAMETER_FAMILY_PACKET", "ALGORITHM_FAMILY_PACKET"),
        output_packets=("INVENTORY_CONSUMER_PACKET", "PARAMETER_SURFACE_PACKET"),
        parameter_scopes=("PARAMETER_ALGORITHM_INVENTORY", "SELECTION_UNIVERSE_REFERENCE"),
        algorithm_scopes=("INVENTORY_LOOKUP", "PARAMETER_FAMILY_GROUPING"),
        consumer_classes=("OPTIMIZER", "REPLAY", "PAPER", "RISK", "SIZING", "QUANTUM_RESEARCH"),
        orchestration="Feeds the orchestrator with inventory references for parameter-stack selection.",
        risk="Provides risk with parameter-family identity but does not approve risk.",
        router="No direct router path; router receives only approved intents after all gates.",
        receipt="Future inventory access and lifecycle changes must produce receipts.",
        health="Health monitor validates inventory references and absence of bundle/hash artifacts.",
        source_connector_resolver="Inventory is downstream of source/connector constraints where parameters depend on external semantics.",
        replay_paper="Supplies candidate parameter stacks for future replay and paper lanes.",
        optimizer="Feeds deterministic scoring and ranking with parameter and algorithm inventory.",
        dashboard="May expose inventory status to owner dashboards without trading authority.",
        owner_scope="OWNER_APPROVED_ATOMICROWS_INVENTORY_SCOPE",
        approval_behavior="Escalates missing row ownership or bundle authority questions to owner request routing.",
        classical_scope="CLASSICAL_PARAMETER_INVENTORY_SCOPE",
        quantum_scope="QUANTUM_PARAMETER_FAMILY_INVENTORY_COMPATIBILITY_SCOPE",
        runtime_scope="STATIC_INVENTORY_CHARTER_ONLY_NO_RUNTIME_BUNDLE_CREATED",
        live_scope="NO_LIVE_SCOPE_CREATED_BY_INVENTORY",
        dashboard_scope="OWNER_VISIBLE_PARAMETER_INVENTORY_STATUS_ONLY",
        source_scope="USES_ACCEPTED_SOURCE_DEPENDENCIES_ONLY_WHEN_FUTURE_PARAMETERS_REQUIRE_THEM",
        connector_scope="DOES_NOT_CREATE_CONNECTOR_BINDINGS",
        atomicrows_scope="PRIMARY_ATOMICROWS_INVENTORY_OWNER",
        fallback_behavior="If inventory rows are incomplete, mark selection universe blocked pending lifecycle or owner route.",
        escalation_behavior="Escalates missing ownership, incomplete rows, or forbidden bundle creation attempts.",
    ),
    "ATOMICROWS_RESEARCH_AGENT": RoleSpec(
        description="Converts research inputs into candidate parameter and algorithm family surfaces.",
        doctrine_terms=("owner_submitted_website_authority_class", "external_prediction_market_research_repo_authority_class", "edge_hypothesis_packet_required_before_parameter_stack_selection_flag"),
        derivation="Mapped to research-input doctrine that permits candidate generation without source-fact authority.",
        static_basis="Records research-to-candidate duties only.",
        runtime_boundary="Does not make websites, X posts, news, or repos accepted source facts.",
        primary_duties=(
            "Convert research, owner-submitted materials, and candidate hypotheses into parameter-family candidates.",
            "Route candidate algorithm families toward evidence and AtomicRows review.",
            "Preserve research input as candidate-only until source evidence and replay/paper validation exist.",
        ),
        secondary_duties=("Document candidate assumptions, materiality, and missing evidence needs.",),
        owned_surfaces=("RESEARCH_INTAKE", "CANDIDATE_PARAMETER_FAMILY", "CANDIDATE_ALGORITHM_FAMILY"),
        consumed_artifacts=("OWNER_RESEARCH_INPUT", "EXTERNAL_REPO_RESEARCH_SIGNAL", "EDGE_HYPOTHESIS_PACKET"),
        emitted_artifacts=("CANDIDATE_PARAMETER_FAMILY_PACKET", "CANDIDATE_ALGORITHM_FAMILY_PACKET"),
        decision_scope="May classify research into candidate parameter and algorithm families.",
        forbidden_authority=("May not declare source facts accepted.", "May not create live trading authority from research."),
        handoff_inputs=("RESEARCH_NOTE", "OWNER_SUBMITTED_URL", "EDGE_HYPOTHESIS_PACKET"),
        handoff_outputs=("RESEARCH_CANDIDATE_PACKET", "ATOMICROWS_REVIEW_REQUEST"),
        input_packets=("RESEARCH_INPUT_PACKET", "EDGE_HYPOTHESIS_PACKET"),
        output_packets=("PARAMETER_RESEARCH_PACKET", "ALGORITHM_RESEARCH_PACKET"),
        parameter_scopes=("RESEARCH_CANDIDATE_PARAMETER_SCOPE",),
        algorithm_scopes=("RESEARCH_CANDIDATE_ALGORITHM_SCOPE",),
        consumer_classes=("ATOMICROWS", "SOURCE_EVIDENCE", "OPTIMIZER"),
        orchestration="Receives research intake from orchestrator and hands candidates to AtomicRows and source evidence flows.",
        risk="Risk treats outputs as candidate-only until validated evidence exists.",
        router="No router access; research never produces approved order intents.",
        receipt="Future research intake and candidate handoffs require event records.",
        health="Health monitor can score research-output quality and missed candidate duties.",
        source_connector_resolver="Can request source evidence review but cannot accept facts or create connector semantics.",
        replay_paper="Routes candidate families for future replay/paper testing after prerequisite evidence.",
        optimizer="Feeds candidate surfaces into deterministic optimizer universe construction.",
        dashboard="Dashboard may collect research input and show candidate status to owner.",
        owner_scope="OWNER_APPROVED_RESEARCH_CANDIDATE_SCOPE",
        approval_behavior="Requests owner approval for research scope expansion or high-materiality candidate promotion.",
        classical_scope="CLASSICAL_RESEARCH_CANDIDATE_MAPPING_SCOPE",
        quantum_scope="QUANTUM_RESEARCH_CANDIDATE_SURFACE_SCOPE",
        runtime_scope="STATIC_RESEARCH_CHARTER_ONLY_NO_RUNTIME_INGESTION_SERVICE_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_RESEARCH_INPUT",
        dashboard_scope="RESEARCH_INTAKE_DISPLAY_AND_OWNER_REVIEW_ONLY",
        source_scope="MAY_REQUEST_SOURCE_REVIEW_NOT_ACCEPT_SOURCE_FACTS",
        connector_scope="DOES_NOT_BIND_CONNECTOR_SEMANTICS",
        atomicrows_scope="CANDIDATE_INPUT_TO_ATOMICROWS_REVIEW",
        fallback_behavior="If research lacks evidence, keep candidate quarantined or route to source evidence.",
        escalation_behavior="Escalates materiality conflicts and promotion requests to owner approval routing.",
    ),
    "ATOMICROWS_LIFECYCLE_AGENT": RoleSpec(
        description="Owns AtomicRows lifecycle state, mutation guard, promotion, and readiness gating surfaces.",
        doctrine_terms=("AtomicRows lifecycle registry", "promotion receipt", "owner override satisfaction", "atomicrows_bundle_is_parameter_algorithm_inventory_not_trader_flag"),
        derivation="Mapped to existing AtomicRows lifecycle command, consumer, promotion, and mutation guard contracts.",
        static_basis="Records lifecycle duties without self-promoting runtime or live authority.",
        runtime_boundary="No lifecycle runtime promotion or bundle authority is created here.",
        primary_duties=(
            "Manage lifecycle state, mutation guards, readiness gates, and promotion receipt semantics.",
            "Consume AtomicRows registry state and promotion receipts for readiness decisions.",
            "Emit lifecycle readiness and mutation blocker packets for future phases.",
        ),
        secondary_duties=("Support owner override satisfaction packets for internal lifecycle requirements.",),
        owned_surfaces=("LIFECYCLE_STATE", "MUTATION_GUARD", "PROMOTION_RECEIPT_SEMANTICS"),
        consumed_artifacts=("ATOMICROWS_REGISTRY_STATE", "PROMOTION_RECEIPT", "OWNER_OVERRIDE_RECEIPT"),
        emitted_artifacts=("LIFECYCLE_READINESS_PACKET", "MUTATION_BLOCKER_PACKET", "OWNER_OVERRIDE_SATISFACTION_PACKET"),
        decision_scope="May classify AtomicRows lifecycle readiness and mutation blockers.",
        forbidden_authority=("May not self-promote runtime or live authority.", "May not create bundle/hash artifacts."),
        handoff_inputs=("ATOMICROWS_REGISTRY_STATE", "PROMOTION_REQUEST_PACKET"),
        handoff_outputs=("LIFECYCLE_READINESS_PACKET", "MUTATION_BLOCKER_PACKET"),
        input_packets=("LIFECYCLE_STATUS_PACKET", "PROMOTION_RECEIPT_PACKET"),
        output_packets=("LIFECYCLE_GATE_PACKET", "MUTATION_GUARD_PACKET"),
        parameter_scopes=("LIFECYCLE_GATED_PARAMETER_SCOPE",),
        algorithm_scopes=("LIFECYCLE_PROMOTION_ALGORITHM_SCOPE",),
        consumer_classes=("ATOMICROWS", "VALIDATION", "OPTIMIZER"),
        orchestration="Provides readiness states to orchestrator before parameter-stack selection.",
        risk="Risk consumes lifecycle readiness for stale or incomplete parameter blocks.",
        router="Router cannot receive intents from lifecycle state alone.",
        receipt="Lifecycle promotions and blockers are future receipt/event-log surfaces.",
        health="Health monitor validates lifecycle gates, mutation guards, and readiness counts.",
        source_connector_resolver="Lifecycle marks source-dependent rows blocked until accepted evidence exists.",
        replay_paper="Promotes only eligible candidate rows toward replay/paper lanes.",
        optimizer="Restricts optimizer universe to lifecycle-eligible parameter rows.",
        dashboard="Exposes lifecycle readiness and owner override status for later owner panels.",
        owner_scope="OWNER_APPROVED_LIFECYCLE_SCOPE",
        approval_behavior="Routes blocked promotions and override satisfaction requests to owner approval packaging.",
        classical_scope="CLASSICAL_LIFECYCLE_READINESS_SCOPE",
        quantum_scope="QUANTUM_PARAMETER_LIFECYCLE_COMPATIBILITY_SCOPE",
        runtime_scope="STATIC_LIFECYCLE_CHARTER_ONLY_NO_RUNTIME_PROMOTION_CREATED",
        live_scope="NO_LIVE_PROMOTION_FROM_STATIC_LIFECYCLE_CHARTER",
        dashboard_scope="OWNER_VISIBLE_LIFECYCLE_STATUS_ONLY",
        source_scope="BLOCKS_SOURCE_DEPENDENT_ROWS_UNTIL_ACCEPTED_PACKET_EXISTS",
        connector_scope="DOES_NOT_CREATE_CONNECTOR_BINDINGS",
        atomicrows_scope="PRIMARY_LIFECYCLE_GUARD_FOR_ATOMICROWS",
        fallback_behavior="If lifecycle state is missing or conflicted, block selection and request review.",
        escalation_behavior="Escalates mutation, promotion, and owner override conflicts.",
    ),
    "SOURCE_EVIDENCE_AGENT": RoleSpec(
        description="Owns source-evidence readiness, candidate, acceptance, revalidation, conflict, and materiality surfaces.",
        doctrine_terms=("source_evidence_requirements_suspended_as_freeze_blockers_only_flag", "stage1_source_queue_authority", "source_dependent_live_or_shadow_field_still_requires_accepted_source_packet"),
        derivation="Mapped to master-plan source evidence doctrine separating retrieval readiness from accepted facts.",
        static_basis="Records source-evidence roles without retrieving or accepting sources.",
        runtime_boundary="No source retrieval execution, source acceptance packet, or external fact artifact is created here.",
        primary_duties=(
            "Govern source retrieval readiness, source candidates, accepted packet references, revalidation, conflict, and materiality surfaces.",
            "Separate retrieval targets from accepted facts for downstream connector and resolver consumers.",
            "Emit source readiness, candidate, conflict, and revalidation states in later phases.",
        ),
        secondary_duties=("Consume owner source-evidence definitions and official source target scopes.",),
        owned_surfaces=("SOURCE_READINESS", "SOURCE_CANDIDATE", "SOURCE_ACCEPTANCE_BOUNDARY", "REVALIDATION_STATE"),
        consumed_artifacts=("OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET", "OFFICIAL_SOURCE_TARGET", "SOURCE_REVIEW_INPUT"),
        emitted_artifacts=("SOURCE_READINESS_RECORD", "CANDIDATE_SOURCE_PACKET", "ACCEPTED_SOURCE_PACKET_REFERENCE", "CONFLICT_CLASSIFICATION"),
        decision_scope="May decide source-evidence readiness and conflict classification in future evidence workflows.",
        forbidden_authority=("May not populate connector semantics without accepted packets.", "May not create source acceptance artifacts in this package."),
        handoff_inputs=("SOURCE_TARGET_SCOPE", "OWNER_SOURCE_DEFINITION", "SOURCE_REVIEW_INPUT"),
        handoff_outputs=("SOURCE_READINESS_STATUS", "ACCEPTED_SOURCE_REFERENCE_OR_BLOCK"),
        input_packets=("SOURCE_RETRIEVAL_TARGET_PACKET", "SOURCE_REVIEW_PACKET"),
        output_packets=("SOURCE_READINESS_PACKET", "SOURCE_CONFLICT_PACKET"),
        parameter_scopes=("SOURCE_DEPENDENT_PARAMETER_SCOPE",),
        algorithm_scopes=("SOURCE_REVALIDATION_ALGORITHM_SCOPE", "CONFLICT_CLASSIFICATION_ALGORITHM_SCOPE"),
        consumer_classes=("CONNECTOR", "RUNTIME_RESOLVER", "RISK", "VALIDATION"),
        orchestration="Receives source-evidence tasks from orchestrator before connector and resolver routing.",
        risk="Risk consumes freshness, conflict, materiality, and source acceptance states.",
        router="Router remains blocked when required accepted source packets are absent.",
        receipt="Future source candidate, acceptance, conflict, and revalidation events require receipts.",
        health="Health monitor validates source readiness, revalidation, and conflict coverage.",
        source_connector_resolver="Owns upstream source packet surfaces consumed by Connector and Runtime Resolver agents.",
        replay_paper="Provides source-backed historical semantics for future replay and paper inputs.",
        optimizer="Optimizer may consume source-backed edge context only after evidence prerequisites.",
        dashboard="Dashboard may show source status and owner review queues without accepting facts.",
        owner_scope="OWNER_APPROVED_SOURCE_EVIDENCE_SCOPE",
        approval_behavior="Requests owner approval for source policy ambiguity without converting facts.",
        classical_scope="CLASSICAL_SOURCE_REVALIDATION_AND_CONFLICT_SCOPE",
        quantum_scope="QUANTUM_CANDIDATES_REQUIRE_SOURCE_EVIDENCE_GATE_SCOPE",
        runtime_scope="STATIC_SOURCE_CHARTER_ONLY_NO_RETRIEVAL_RUNTIME_CREATED",
        live_scope="NO_LIVE_OR_SHADOW_SOURCE_DEPENDENT_FIELD_WITHOUT_ACCEPTED_PACKET",
        dashboard_scope="OWNER_VISIBLE_SOURCE_STATUS_AND_REVIEW_QUEUE_ONLY",
        source_scope="PRIMARY_SOURCE_EVIDENCE_OWNER",
        connector_scope="UPSTREAM_EVIDENCE_PROVIDER_FOR_CONNECTOR_BINDINGS",
        atomicrows_scope="MARKS_SOURCE_DEPENDENT_PARAMETER_ROWS_PENDING_EVIDENCE",
        fallback_behavior="If evidence is stale, missing, or conflicted, fail closed and block downstream use.",
        escalation_behavior="Escalates material conflicts, stale packets, and owner source policy questions.",
    ),
    "CONNECTOR_AGENT": RoleSpec(
        description="Owns Connector Registry and semantic binding readiness surfaces.",
        doctrine_terms=("Connector Registry", "runtime_cash_component_field_map_requires_accepted_source_packet_per_component_flag", "source_dependent_live_or_shadow_field_still_requires_accepted_source_packet"),
        derivation="Mapped to connector registry and semantic binding doctrine downstream of accepted source evidence.",
        static_basis="Records connector duties without creating connector binding artifacts.",
        runtime_boundary="Does not fetch private account state or bind connector semantics in this package.",
        primary_duties=(
            "Maintain connector registry readiness for venue/API/account/orderbook/order-entry semantics.",
            "Consume accepted source packets before future semantic binding records.",
            "Emit connector readiness and semantic binding records only when prerequisites exist.",
        ),
        secondary_duties=("Track rate-limit, authentication-state, order-shape, data-state, and failure-mode hooks.",),
        owned_surfaces=("CONNECTOR_REGISTRY", "CONNECTOR_SEMANTIC_BINDING", "CONNECTOR_READINESS"),
        consumed_artifacts=("ACCEPTED_SOURCE_PACKET", "FRESH_REVALIDATION_STATE", "CONFLICT_CLEARANCE", "TARGET_FIELD_SCOPE_MATCH"),
        emitted_artifacts=("CONNECTOR_READINESS_RECORD", "SEMANTIC_BINDING_RECORD"),
        decision_scope="May decide connector readiness and binding eligibility after accepted source prerequisites.",
        forbidden_authority=("May not fetch private account state here.", "May not bind semantics without accepted source packets."),
        handoff_inputs=("ACCEPTED_SOURCE_REFERENCE", "CONNECTOR_TARGET_FIELD_SCOPE"),
        handoff_outputs=("CONNECTOR_READINESS_STATUS", "SEMANTIC_BINDING_REFERENCE"),
        input_packets=("ACCEPTED_SOURCE_PACKET_REFERENCE", "CONNECTOR_TARGET_FIELD_PACKET"),
        output_packets=("CONNECTOR_READINESS_PACKET", "CONNECTOR_SEMANTIC_BINDING_PACKET"),
        parameter_scopes=("CONNECTOR_BOUND_PARAMETER_SCOPE", "VENUE_SEMANTIC_PARAMETER_SCOPE"),
        algorithm_scopes=("CONNECTOR_SEMANTIC_BINDING_ALGORITHM",),
        consumer_classes=("RUNTIME_RESOLVER", "RISK", "ORDER_ROUTER", "VALIDATION"),
        orchestration="Runs after source evidence and before runtime resolver in orchestrated flow.",
        risk="Risk consumes connector readiness and stale/conflict states.",
        router="Execution Router requires connector readiness before venue-specific order instructions.",
        receipt="Future connector binding, downgrade, and failure-mode events require receipts.",
        health="Health monitor validates connector registry, binding readiness, and no private-state fetch in static scope.",
        source_connector_resolver="Owns the connector layer between accepted source evidence and runtime resolver snapshots.",
        replay_paper="Provides connector semantics for future replay and paper configuration.",
        optimizer="Optimizer consumes connector feasibility masks only after binding prerequisites.",
        dashboard="Dashboard may show connector readiness, downgraded state, and owner-visible blocks.",
        owner_scope="OWNER_APPROVED_CONNECTOR_SCOPE",
        approval_behavior="Escalates connector binding gaps and source prerequisites to owner request routing.",
        classical_scope="CLASSICAL_CONNECTOR_SEMANTIC_BINDING_SCOPE",
        quantum_scope="QUANTUM_OUTPUT_SUBORDINATE_TO_CONNECTOR_SEMANTICS_SCOPE",
        runtime_scope="STATIC_CONNECTOR_CHARTER_ONLY_NO_PRIVATE_STATE_FETCH_CREATED",
        live_scope="NO_LIVE_CONNECTOR_REACHABILITY_CREATED",
        dashboard_scope="OWNER_VISIBLE_CONNECTOR_READINESS_STATUS_ONLY",
        source_scope="CONSUMES_ACCEPTED_SOURCE_PACKETS_ONLY",
        connector_scope="PRIMARY_CONNECTOR_REGISTRY_OWNER",
        atomicrows_scope="SUPPLIES_CONNECTOR_FEASIBILITY_TO_PARAMETER_CONSUMERS_IN_LATER_PHASES",
        fallback_behavior="If accepted source prerequisites are absent or stale, connector remains blocked or downgraded.",
        escalation_behavior="Escalates semantic conflicts, stale source packets, and connector readiness blockers.",
    ),
    "RUNTIME_RESOLVER_AGENT": RoleSpec(
        description="Owns runtime resolver snapshot contracts and identity normalization surfaces.",
        doctrine_terms=("runtime resolver snapshot", "source_dependent_live_or_shadow_field_still_requires_accepted_source_packet", "connector semantic binding"),
        derivation="Mapped to runtime resolver snapshot input identity and contract normalization doctrine.",
        static_basis="Records resolver contracts without creating resolver snapshots.",
        runtime_boundary="No runtime resolver snapshot is created in this package.",
        primary_duties=(
            "Define runtime resolver snapshot contracts and input identity requirements.",
            "Normalize contract and market identity after connector and source prerequisites.",
            "Emit resolver snapshots only in later scoped workflows.",
        ),
        secondary_duties=("Prepare handoff surfaces for replay, paper, risk, and optimizer consumers.",),
        owned_surfaces=("RUNTIME_RESOLVER_CONTRACT", "INPUT_IDENTITY", "MARKET_IDENTITY_NORMALIZATION"),
        consumed_artifacts=("CONNECTOR_SEMANTIC_BINDING", "SOURCE_BACKED_IDENTITY_INPUT"),
        emitted_artifacts=("RUNTIME_RESOLVER_SNAPSHOT_REFERENCE", "RESOLVER_HANDOFF_PACKET"),
        decision_scope="May decide resolver input completeness and normalization eligibility in future runtime workflows.",
        forbidden_authority=("May not create runtime snapshots in this package.", "May not resolve identities without source and connector prerequisites."),
        handoff_inputs=("CONNECTOR_SEMANTIC_BINDING_REFERENCE", "SOURCE_BACKED_IDENTITY_PACKET"),
        handoff_outputs=("RESOLVER_SNAPSHOT_STATUS", "REPLAY_PAPER_HANDOFF_REFERENCE"),
        input_packets=("RESOLVER_INPUT_LOCK_PACKET", "CONNECTOR_BINDING_REFERENCE_PACKET"),
        output_packets=("RUNTIME_RESOLVER_SNAPSHOT_PACKET", "RESOLVER_HANDOFF_PACKET"),
        parameter_scopes=("RUNTIME_RESOLVED_PARAMETER_SCOPE",),
        algorithm_scopes=("CONTRACT_NORMALIZATION_ALGORITHM", "MARKET_IDENTITY_NORMALIZATION_ALGORITHM"),
        consumer_classes=("REPLAY", "PAPER", "RISK", "OPTIMIZER"),
        orchestration="Runs after connector readiness and before replay/paper or runtime consumers.",
        risk="Risk consumes resolver completeness and identity uncertainty flags.",
        router="Router cannot act on unresolved identities.",
        receipt="Future resolver snapshot creation and handoff events require receipts.",
        health="Health monitor validates resolver contract coverage and snapshot boundary adherence.",
        source_connector_resolver="Owns the resolver layer after source and connector prerequisites.",
        replay_paper="Provides locked input identity for separate replay and paper lanes.",
        optimizer="Supplies resolved context for deterministic optimizer candidate evaluation.",
        dashboard="Dashboard may show resolver readiness and unresolved identity blockers.",
        owner_scope="OWNER_APPROVED_RUNTIME_RESOLVER_SCOPE",
        approval_behavior="Escalates unresolved identity or source-backed mapping gaps.",
        classical_scope="CLASSICAL_RESOLVER_NORMALIZATION_SCOPE",
        quantum_scope="QUANTUM_CANDIDATES_REQUIRE_RESOLVED_CONTEXT_SCOPE",
        runtime_scope="STATIC_RESOLVER_CHARTER_ONLY_NO_SNAPSHOT_CREATED",
        live_scope="NO_LIVE_RESOLVER_OUTPUT_CREATED",
        dashboard_scope="OWNER_VISIBLE_RESOLVER_STATUS_ONLY",
        source_scope="CONSUMES_SOURCE_BACKED_INPUTS",
        connector_scope="CONSUMES_CONNECTOR_SEMANTIC_BINDINGS",
        atomicrows_scope="SUPPLIES_RESOLVED_CONTEXT_FOR_PARAMETER_STACK_SELECTION",
        fallback_behavior="If identity inputs are incomplete, block downstream replay, paper, risk, and live use.",
        escalation_behavior="Escalates unresolved identity, stale binding, and missing source prerequisites.",
    ),
    "REPLAY_AGENT": RoleSpec(
        description="Owns the non-live replay evidence lane.",
        doctrine_terms=("stage1_replay_and_paper_run_mode", "stage1_replay_and_paper_results_must_remain_separate_flag", "runtime resolver snapshot"),
        derivation="Mapped to concurrent separate replay/paper lane doctrine and resolver handoff contracts.",
        static_basis="Records replay lane duties without executing replay.",
        runtime_boundary="No replay execution or replay result packet is created here.",
        primary_duties=(
            "Run the future non-live replay lane using locked resolver snapshots and candidate parameter stacks.",
            "Keep replay inputs and outputs separate from paper and live workflows.",
            "Emit replay result packets only in later evidence phases.",
        ),
        secondary_duties=("Report replay blockers, data gaps, and parameter-stack compatibility failures.",),
        owned_surfaces=("REPLAY_LANE", "REPLAY_INPUT_LOCK", "REPLAY_RESULT_BOUNDARY"),
        consumed_artifacts=("RUNTIME_RESOLVER_SNAPSHOT", "CANDIDATE_PARAMETER_STACK", "CONNECTOR_SOURCE_BACKED_HISTORICAL_SEMANTICS"),
        emitted_artifacts=("REPLAY_RESULT_PACKET", "REPLAY_BLOCKER_PACKET"),
        decision_scope="May decide replay-lane pass, fail, or blocker states in future non-live evidence workflows.",
        forbidden_authority=("May not create paper or live approval.", "May not claim profit or live readiness from replay alone."),
        handoff_inputs=("RESOLVER_SNAPSHOT_REFERENCE", "PARAMETER_STACK_CANDIDATE"),
        handoff_outputs=("REPLAY_RESULT_REFERENCE", "DUAL_REVIEW_REPLAY_INPUT"),
        input_packets=("REPLAY_RUN_INPUT_PACKET", "PARAMETER_STACK_PACKET"),
        output_packets=("REPLAY_RESULT_PACKET", "REPLAY_BLOCKER_PACKET"),
        parameter_scopes=("REPLAY_PARAMETER_STACK_SCOPE",),
        algorithm_scopes=("REPLAY_EVALUATION_ALGORITHM_SCOPE",),
        consumer_classes=("DUAL_RESULT_REVIEW", "OPTIMIZER", "RISK"),
        orchestration="Receives locked replay tasks from orchestrator and returns results to dual review.",
        risk="Risk may consume replay outcomes but replay cannot approve risk.",
        router="No router path; replay is non-live evidence only.",
        receipt="Future replay start, block, and result events require receipts.",
        health="Health monitor validates replay lane separation and output coverage.",
        source_connector_resolver="Consumes resolver snapshots derived from source and connector prerequisites.",
        replay_paper="Owns replay side of separate replay/paper lanes.",
        optimizer="Feeds replay feedback into deterministic optimizer scoring and candidate competition.",
        dashboard="Dashboard may show replay status and result summaries for owner review.",
        owner_scope="OWNER_APPROVED_REPLAY_SCOPE",
        approval_behavior="Escalates replay blockers or promotion requests to owner approval packaging.",
        classical_scope="CLASSICAL_REPLAY_EVIDENCE_SCOPE",
        quantum_scope="QUANTUM_CANDIDATES_REQUIRE_REPLAY_EVIDENCE_SCOPE",
        runtime_scope="STATIC_REPLAY_CHARTER_ONLY_NO_REPLAY_RUNTIME_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_REPLAY",
        dashboard_scope="OWNER_VISIBLE_REPLAY_STATUS_ONLY",
        source_scope="CONSUMES_SOURCE_BACKED_HISTORICAL_SEMANTICS",
        connector_scope="CONSUMES_CONNECTOR_HISTORICAL_SEMANTICS",
        atomicrows_scope="CONSUMES_REPLAY_ELIGIBLE_PARAMETER_STACKS",
        fallback_behavior="If replay inputs are missing, block result creation and request resolver or source repair.",
        escalation_behavior="Escalates replay/paper divergence, input gaps, and blocker states.",
    ),
    "PAPER_AGENT": RoleSpec(
        description="Owns the non-live paper evidence lane.",
        doctrine_terms=("stage1_pre_live_validation_mode", "CONCURRENT_SEPARATE_LANES_AFTER_SHARED_INPUT_LOCK", "stage1_replay_and_paper_results_must_remain_separate_flag"),
        derivation="Mapped to paper lane doctrine requiring separation from replay and live.",
        static_basis="Records paper lane duties without executing paper mode.",
        runtime_boundary="No paper execution or paper result packet is created here.",
        primary_duties=(
            "Run the future non-live paper lane from shared input locks and candidate stacks.",
            "Keep paper outputs separate from replay and live approval.",
            "Emit paper result packets only in later evidence phases.",
        ),
        secondary_duties=("Report paper blockers, execution configuration gaps, and divergence inputs.",),
        owned_surfaces=("PAPER_LANE", "PAPER_EXECUTION_CONFIG", "PAPER_RESULT_BOUNDARY"),
        consumed_artifacts=("SHARED_INPUT_LOCK", "CANDIDATE_PARAMETER_STACK", "PAPER_EXECUTION_CONFIGURATION"),
        emitted_artifacts=("PAPER_RESULT_PACKET", "PAPER_BLOCKER_PACKET"),
        decision_scope="May decide paper-lane pass, fail, or blocker states in future non-live workflows.",
        forbidden_authority=("May not create replay or live approval.", "May not treat paper outputs as fills or profit evidence."),
        handoff_inputs=("SHARED_INPUT_LOCK_REFERENCE", "PAPER_CONFIGURATION_PACKET"),
        handoff_outputs=("PAPER_RESULT_REFERENCE", "DUAL_REVIEW_PAPER_INPUT"),
        input_packets=("PAPER_RUN_INPUT_PACKET", "PARAMETER_STACK_PACKET"),
        output_packets=("PAPER_RESULT_PACKET", "PAPER_BLOCKER_PACKET"),
        parameter_scopes=("PAPER_PARAMETER_STACK_SCOPE",),
        algorithm_scopes=("PAPER_EVALUATION_ALGORITHM_SCOPE",),
        consumer_classes=("DUAL_RESULT_REVIEW", "OPTIMIZER", "RISK"),
        orchestration="Receives paper tasks from orchestrator and returns separate results to dual review.",
        risk="Risk may consume paper evidence but paper cannot approve risk.",
        router="No router path; paper is non-live evidence only.",
        receipt="Future paper start, block, and result events require receipts.",
        health="Health monitor validates paper lane separation and output coverage.",
        source_connector_resolver="Consumes locked inputs downstream of source, connector, and resolver prerequisites.",
        replay_paper="Owns paper side of separate replay/paper lanes.",
        optimizer="Feeds paper feedback into deterministic optimizer scoring and candidate competition.",
        dashboard="Dashboard may show paper status and summaries for owner review.",
        owner_scope="OWNER_APPROVED_PAPER_SCOPE",
        approval_behavior="Escalates paper blockers or promotion requests to owner approval packaging.",
        classical_scope="CLASSICAL_PAPER_EVIDENCE_SCOPE",
        quantum_scope="QUANTUM_CANDIDATES_REQUIRE_PAPER_EVIDENCE_SCOPE",
        runtime_scope="STATIC_PAPER_CHARTER_ONLY_NO_PAPER_RUNTIME_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_PAPER",
        dashboard_scope="OWNER_VISIBLE_PAPER_STATUS_ONLY",
        source_scope="CONSUMES_SOURCE_BACKED_INPUTS",
        connector_scope="CONSUMES_CONNECTOR_BACKED_CONFIG",
        atomicrows_scope="CONSUMES_PAPER_ELIGIBLE_PARAMETER_STACKS",
        fallback_behavior="If paper inputs are missing, block result creation and request repair.",
        escalation_behavior="Escalates replay/paper divergence, input gaps, and blocker states.",
    ),
    "DUAL_RESULT_REVIEW_AGENT": RoleSpec(
        description="Owns comparison of separate replay and paper evidence outputs.",
        doctrine_terms=("stage1_replay_and_paper_results_must_remain_separate_flag", "dual result review", "owner live promotion review"),
        derivation="Mapped to dual-result review doctrine that compares non-live lanes without auto-promoting live.",
        static_basis="Records dual review duties without comparing real results.",
        runtime_boundary="No dual-result runtime packet is created here.",
        primary_duties=(
            "Compare replay and paper result packets from separate lanes in later phases.",
            "Emit comparison matrices and owner handoff packets without auto-promoting live.",
            "Surface divergence, uncertainty, and evidence gaps for owner and risk review.",
        ),
        secondary_duties=("Preserve replay/paper separation through owner promotion review.",),
        owned_surfaces=("DUAL_RESULT_REVIEW", "REPLAY_PAPER_COMPARISON", "OWNER_HANDOFF_BLOCK"),
        consumed_artifacts=("REPLAY_RESULT_PACKET", "PAPER_RESULT_PACKET"),
        emitted_artifacts=("DUAL_REVIEW_COMPARISON_MATRIX", "OWNER_HANDOFF_PACKET"),
        decision_scope="May decide comparison pass, fail, or divergence states in later non-live review.",
        forbidden_authority=("May not merge replay/paper into live approval.", "May not bypass owner promotion review."),
        handoff_inputs=("REPLAY_RESULT_REFERENCE", "PAPER_RESULT_REFERENCE"),
        handoff_outputs=("DUAL_REVIEW_MATRIX", "OWNER_PROMOTION_REVIEW_HANDOFF"),
        input_packets=("REPLAY_RESULT_PACKET", "PAPER_RESULT_PACKET"),
        output_packets=("DUAL_RESULT_REVIEW_PACKET", "OWNER_HANDOFF_PACKET"),
        parameter_scopes=("DUAL_REVIEW_PARAMETER_STACK_SCOPE",),
        algorithm_scopes=("REPLAY_PAPER_COMPARISON_ALGORITHM",),
        consumer_classes=("OWNER_APPROVAL", "RISK", "OPTIMIZER", "LIVE_CANARY"),
        orchestration="Receives replay and paper outputs after both lanes complete.",
        risk="Risk consumes comparison and divergence flags before approval.",
        router="Router remains blocked until later owner, risk, and live gates pass.",
        receipt="Future dual review matrices and handoffs require event receipts.",
        health="Health monitor validates dual review coverage and separation rules.",
        source_connector_resolver="Reviews outputs whose inputs trace to source, connector, and resolver prerequisites.",
        replay_paper="Owns the comparison bridge between separate replay and paper lanes.",
        optimizer="Feeds comparison outcomes back to optimizer ranking and candidate competition.",
        dashboard="Dashboard may show comparison summaries and owner review queue.",
        owner_scope="OWNER_APPROVED_DUAL_REVIEW_SCOPE",
        approval_behavior="Packages promotion handoffs for owner review without approving for owner.",
        classical_scope="CLASSICAL_DUAL_REVIEW_COMPARISON_SCOPE",
        quantum_scope="QUANTUM_ADVANTAGE_HYPOTHESIS_REQUIRES_DUAL_REVIEW_SCOPE",
        runtime_scope="STATIC_DUAL_REVIEW_CHARTER_ONLY_NO_RUNTIME_PACKET_CREATED",
        live_scope="NO_LIVE_PROMOTION_CREATED_BY_DUAL_REVIEW",
        dashboard_scope="OWNER_VISIBLE_DUAL_REVIEW_SUMMARY_ONLY",
        source_scope="CONSUMES_SOURCE_BACKED_EVIDENCE_LINEAGE",
        connector_scope="CONSUMES_CONNECTOR_BACKED_EVIDENCE_LINEAGE",
        atomicrows_scope="RELATES_RESULTS_TO_PARAMETER_STACKS",
        fallback_behavior="If replay and paper disagree or are incomplete, block promotion and request review.",
        escalation_behavior="Escalates divergence, missing result packets, and promotion ambiguity.",
    ),
    "OPTIMIZER_AGENT": RoleSpec(
        description="Owns deterministic parameter-stack generation, scoring, ranking, competition, and quantum/classical arbitration surfaces.",
        doctrine_terms=("edge_parameter_stack_selection_required_flag", "single_parameter_or_single_algorithm_trade_selection_allowed_flag", "quantum_optimizer_replay_paper_candidate_trigger_allowed_flag", "quantum_output_may_not_override_source_evidence_connector_semantic_runtime_cash_or_owner_approval_gates"),
        derivation="Mapped to deterministic scoring/ranking/arbitration doctrine and quantum optimizer authority boundaries.",
        static_basis="Records optimizer authority surfaces without claiming alpha, profit, or quantum advantage evidence.",
        runtime_boundary="No replay, paper, live, backend, or trade-intent artifact is created here.",
        primary_duties=(
            "Generate deterministic parameter-stack candidates from AtomicRows inventory and edge hypotheses.",
            "Score, rank, and arbitrate candidate stacks using strongest-classical comparators and quantum/classical policy.",
            "Reject random parameter or single-algorithm direct trade selection paths.",
            "Emit ranked stacks, arbitration packets, and replay/paper candidate packs in later phases.",
        ),
        secondary_duties=("Consume replay/paper feedback, risk, sizing, latency, and quantum candidate surfaces.",),
        owned_surfaces=("PARAMETER_STACK_GENERATION", "DETERMINISTIC_SCORING", "DETERMINISTIC_RANKING", "QUANTUM_CLASSICAL_ARBITRATION"),
        consumed_artifacts=("ATOMICROWS_INVENTORY", "EDGE_HYPOTHESIS_PACKET", "TRADE_CONTEXT_PACKET", "REPLAY_PAPER_FEEDBACK", "RISK_CONSTRAINTS"),
        emitted_artifacts=("RANKED_PARAMETER_STACK_PACKET", "OPTIMIZER_SELECTION_PACKET", "ARBITRATION_PACKET", "REPLAY_PAPER_CANDIDATE_PACK"),
        decision_scope="May decide ranked candidate ordering and optimizer selection for later evidence lanes.",
        forbidden_authority=("May not claim alpha, profit, or quantum advantage without evidence.", "May not submit live orders directly."),
        handoff_inputs=("EDGE_HYPOTHESIS_PACKET", "ATOMICROWS_SELECTION_UNIVERSE", "RISK_CONSTRAINT_PACKET"),
        handoff_outputs=("RANKED_PARAMETER_STACKS", "QUANTUM_CLASSICAL_ARBITRATION_PACKET"),
        input_packets=("PARAMETER_STACK_INPUT_PACKET", "QUANTUM_CANDIDATE_PACKET"),
        output_packets=("RANKED_PARAMETER_STACK_PACKET", "ARBITRATION_PACKET"),
        parameter_scopes=("EDGE_PARAMETER_STACK_SCOPE", "QUANTUM_PARAMETER_STACK_SCOPE", "CLASSICAL_COMPARATOR_PARAMETER_SCOPE"),
        algorithm_scopes=("DETERMINISTIC_SCORING", "DETERMINISTIC_RANKING", "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK"),
        consumer_classes=("REPLAY", "PAPER", "RISK", "SIZING", "DASHBOARD"),
        orchestration="Receives edge and inventory inputs through orchestrator and hands candidates to evidence lanes.",
        risk="Risk can block optimizer outputs for stale, conflicted, infeasible, or excessive exposure inputs.",
        router="Optimizer cannot route orders; approved future intents still pass Execution Router.",
        receipt="Future optimizer selections and arbitration results require event receipts.",
        health="Health monitor validates deterministic scoring, no random selection, and arbitration coverage.",
        source_connector_resolver="Optimizer outputs remain subordinate to source evidence, connector semantics, and resolver snapshots.",
        replay_paper="Creates candidate packs for replay/paper evidence before promotion.",
        optimizer="Owns optimizer arbitration surface including strongest-classical comparator and quantum tie-break policy.",
        dashboard="Dashboard may display ranked candidates and owner quantum-priority controls.",
        owner_scope="OWNER_APPROVED_OPTIMIZER_SCOPE",
        approval_behavior="Requests owner approval for quantum priority, live intent enablement, or unresolved arbitration policy.",
        classical_scope="STRONGEST_CLASSICAL_COMPARATOR_AND_DETERMINISTIC_RANKING_SCOPE",
        quantum_scope="TRUE_QUANTUM_QUANTUM_INSPIRED_HYBRID_ARBITRATION_SCOPE_WITH_NO_ADVANTAGE_CLAIM",
        runtime_scope="STATIC_OPTIMIZER_CHARTER_ONLY_NO_RUNTIME_OPTIMIZER_CREATED",
        live_scope="FUTURE_OWNER_ENABLED_TRADE_INTENT_ONLY_AFTER_ALL_GATES_NO_ORDER_AUTHORITY",
        dashboard_scope="OWNER_VISIBLE_OPTIMIZER_RANKING_AND_QUANTUM_PRIORITY_CONTROL",
        source_scope="CANNOT_OVERRIDE_SOURCE_EVIDENCE",
        connector_scope="CANNOT_OVERRIDE_CONNECTOR_SEMANTICS",
        atomicrows_scope="CONSUMES_ATOMICROWS_INVENTORY_FOR_PARAMETER_STACK_SELECTION",
        fallback_behavior="If objective, comparator, fallback bundle, or evidence is missing, block or downgrade candidate.",
        escalation_behavior="Escalates missing comparator, missing fallback, quantum policy ambiguity, and risk blocks.",
    ),
    "RISK_AGENT": RoleSpec(
        description="Owns the Risk Gate for exposure, uncertainty, source freshness, kill conditions, and capital constraints.",
        doctrine_terms=("Risk Gate", "runtime_cash_component_unknown_blocks_new_or_increased_exposure_flag", "risk_manager_may_block_quantum_triggered_trade"),
        derivation="Mapped to Risk Gate doctrine validating sizing, exposure, liquidity, venue state, kill rules, owner permission, and live authority.",
        static_basis="Records risk-gate duties without approving real trades.",
        runtime_boundary="No risk approval receipt or live gate artifact is created here.",
        primary_duties=(
            "Evaluate future proposed trades, parameter stacks, optimizer outputs, source freshness, connector readiness, cash state, exposure, and kill-switch state.",
            "Fail closed on unknown, stale, conflicted, or unauthorized inputs.",
            "Emit risk approvals, blocks, limit packets, and exposure constraints in later phases.",
        ),
        secondary_duties=("Apply owner risk policy and quantum-triggered trade constraints.",),
        owned_surfaces=("RISK_GATE", "EXPOSURE_LIMITS", "KILL_CONDITIONS", "UNCERTAINTY_FLAGS"),
        consumed_artifacts=("PROPOSED_TRADE_INTENT", "RANKED_PARAMETER_STACK_PACKET", "SIZING_SUGGESTION", "SOURCE_FRESHNESS_STATE", "RUNTIME_CASH_STATE"),
        emitted_artifacts=("RISK_APPROVAL_PACKET", "RISK_BLOCK_PACKET", "RISK_LIMIT_PACKET", "KILL_SWITCH_RECOMMENDATION"),
        decision_scope="May approve, block, or constrain future risk-gated intents.",
        forbidden_authority=("May not approve for owner.", "May not fabricate cash, source, connector, replay, or paper evidence."),
        handoff_inputs=("OPTIMIZER_SELECTION_PACKET", "SIZING_SUGGESTION_PACKET", "SOURCE_CONNECTOR_RESOLVER_STATUS"),
        handoff_outputs=("RISK_GATE_DECISION", "EXPOSURE_CONSTRAINT_PACKET"),
        input_packets=("RISK_EVALUATION_PACKET", "KILL_SWITCH_STATE_PACKET"),
        output_packets=("RISK_APPROVAL_PACKET", "RISK_BLOCK_PACKET"),
        parameter_scopes=("RISK_LIMIT_PARAMETER_SCOPE", "QUANTUM_FEASIBILITY_MASK_SCOPE"),
        algorithm_scopes=("RISK_SCORING_ALGORITHM", "FAIL_CLOSED_RISK_CLASSIFIER"),
        consumer_classes=("SIZING", "ORDER_ROUTER", "LIVE_CANARY", "DASHBOARD"),
        orchestration="Receives proposed intents through orchestrator before sizing and router advancement.",
        risk="Primary owner of Risk Gate decisions and fail-closed blocks.",
        router="Router only receives intents that clear risk, owner, source, connector, cash, latency, and kill-switch gates.",
        receipt="Future risk approvals, blocks, and kill-switch recommendations require receipts.",
        health="Health monitor validates risk decisions, stale-input blocks, and exposure constraint coverage.",
        source_connector_resolver="Consumes source freshness, connector readiness, and resolver completeness as risk inputs.",
        replay_paper="Consumes replay/paper and dual review evidence before live eligibility.",
        optimizer="Can block or constrain optimizer and quantum-triggered outputs.",
        dashboard="Dashboard may show risk state, blocks, and owner policy controls.",
        owner_scope="OWNER_APPROVED_RISK_SCOPE",
        approval_behavior="Escalates risk tolerance, stale evidence, and kill-switch conflicts to owner request routing.",
        classical_scope="CLASSICAL_RISK_GATE_AND_EXPOSURE_SCOPE",
        quantum_scope="QUANTUM_CANDIDATE_RISK_AND_FEASIBILITY_MASK_SCOPE",
        runtime_scope="STATIC_RISK_CHARTER_ONLY_NO_RUNTIME_RISK_DECISION_CREATED",
        live_scope="FUTURE_LIVE_RISK_GATE_ONLY_AFTER_ALL_PREREQUISITES",
        dashboard_scope="OWNER_VISIBLE_RISK_GATE_STATUS_ONLY",
        source_scope="FAILS_CLOSED_ON_STALE_OR_CONFLICTED_SOURCE_INPUTS",
        connector_scope="FAILS_CLOSED_ON_MISSING_OR_DOWNGRADED_CONNECTOR_READINESS",
        atomicrows_scope="CONSUMES_PARAMETER_STACK_RISK_ATTRIBUTES",
        fallback_behavior="Unknown, stale, conflicted, or infeasible input blocks new or increased exposure.",
        escalation_behavior="Escalates risk tolerance, exposure, kill-switch, and uncertainty blockers.",
    ),
    "SIZING_AGENT": RoleSpec(
        description="Transforms approved risk and capital constraints into future position sizing recommendations.",
        doctrine_terms=("runtime_cash_component_field_map_requires_accepted_source_packet_per_component_flag", "usable capital gate", "Risk Gate"),
        derivation="Mapped to usable-capital and risk-translation doctrine downstream of source, cash, and risk prerequisites.",
        static_basis="Records sizing duties without fabricating balances or cash receipts.",
        runtime_boundary="No runtime cash receipt or sizing packet is created here.",
        primary_duties=(
            "Transform approved risk and capital constraints into future position sizing recommendations.",
            "Consume runtime cash receipts, volatility, liquidity, confidence, and owner capital policy in later phases.",
            "Emit sizing packets only after evidence and cash prerequisites exist.",
        ),
        secondary_duties=("Apply quantum feasibility masks and capital-allocation constraints when owner quantum priority is active.",),
        owned_surfaces=("POSITION_SIZING", "CAPITAL_ALLOCATION", "USABLE_CAPITAL_TRANSLATION"),
        consumed_artifacts=("RISK_CONSTRAINT_PACKET", "RUNTIME_CASH_RECEIPT", "PARAMETER_STACK_CONFIDENCE", "OWNER_CAPITAL_POLICY"),
        emitted_artifacts=("SIZING_PACKET", "CAPITAL_ALLOCATION_RECOMMENDATION"),
        decision_scope="May recommend future sizing within approved risk and cash constraints.",
        forbidden_authority=("May not fabricate balances or cash receipts.", "May not route orders or approve for owner."),
        handoff_inputs=("RISK_LIMIT_PACKET", "USABLE_CAPITAL_STATE", "VOLATILITY_LIQUIDITY_ASSUMPTIONS"),
        handoff_outputs=("SIZING_RECOMMENDATION_PACKET", "CAPITAL_CONSTRAINT_PACKET"),
        input_packets=("SIZING_INPUT_PACKET", "RUNTIME_CASH_RECEIPT_PACKET"),
        output_packets=("SIZING_PACKET", "CAPITAL_ALLOCATION_PACKET"),
        parameter_scopes=("SIZING_PARAMETER_SCOPE", "CAPITAL_CONSTRAINT_PARAMETER_SCOPE"),
        algorithm_scopes=("POSITION_SIZING_ALGORITHM", "CAPITAL_ALLOCATION_ALGORITHM"),
        consumer_classes=("RISK", "ORDER_ROUTER", "LIVE_CANARY", "DASHBOARD"),
        orchestration="Runs after risk constraints and before latency/router handoffs in the orchestrated flow.",
        risk="Consumes and obeys risk constraints; cannot override Risk Gate blocks.",
        router="Router receives sizing only as part of approved trade intent after all gates.",
        receipt="Future sizing and capital allocation recommendations require receipts.",
        health="Health monitor validates sizing prerequisites and absence of fabricated cash.",
        source_connector_resolver="Sizing depends on source-backed runtime cash semantics and resolved market context.",
        replay_paper="Uses replay/paper confidence only as non-live evidence input.",
        optimizer="Consumes optimizer confidence and quantum feasibility masks after arbitration.",
        dashboard="Dashboard may show sizing recommendations and capital policy controls.",
        owner_scope="OWNER_APPROVED_SIZING_SCOPE",
        approval_behavior="Escalates capital policy, unknown cash, or sizing conflicts to owner request routing.",
        classical_scope="CLASSICAL_POSITION_SIZING_SCOPE",
        quantum_scope="QUANTUM_PORTFOLIO_OPTIMIZATION_FEASIBILITY_SCOPE_WITH_CASH_GATE",
        runtime_scope="STATIC_SIZING_CHARTER_ONLY_NO_CASH_RECEIPT_CREATED",
        live_scope="NO_LIVE_SIZING_AUTHORITY_WITHOUT_RUNTIME_CASH_AND_RISK_GATES",
        dashboard_scope="OWNER_VISIBLE_SIZING_AND_CAPITAL_STATUS_ONLY",
        source_scope="REQUIRES_ACCEPTED_SOURCE_PACKET_FOR_CASH_COMPONENT_MAPS",
        connector_scope="CONSUMES_CONNECTOR_CASH_SEMANTICS_IN_LATER_PHASES",
        atomicrows_scope="CONSUMES_PARAMETER_STACK_CONFIDENCE_AND_SIZING_ROWS",
        fallback_behavior="If usable capital or cash semantics are unknown, block sizing for new or increased exposure.",
        escalation_behavior="Escalates unknown cash, capital conflict, and risk/sizing mismatch.",
    ),
    "EXECUTION_LATENCY_AGENT": RoleSpec(
        description="Owns latency-sensitive architecture, live-path exclusions, and precomputed control-plane snapshot policies.",
        doctrine_terms=("execution latency component model", "quantum_optimizer_live_pretrade_remote_backend_dependency_allowed", "Execution Router"),
        derivation="Mapped to low-latency live-path and quantum backend exclusion doctrine.",
        static_basis="Records latency policy duties without creating live path telemetry.",
        runtime_boundary="No latency runtime service or live observation artifact is created here.",
        primary_duties=(
            "Govern latency-sensitive architecture, live-path weight, and control-plane separation.",
            "Ensure heavy quantum/backend/control-plane work stays outside live pretrade path unless precomputed and approved later.",
            "Emit latency policy packets and live-path exclusion rules in later phases.",
        ),
        secondary_duties=("Consume venue latency maps, orderbook semantics, router constraints, and optimizer path latency.",),
        owned_surfaces=("EXECUTION_LATENCY_POLICY", "LIVE_PATH_EXCLUSION", "PRECOMPUTED_SNAPSHOT_POLICY"),
        consumed_artifacts=("VENUE_LATENCY_MAP", "ORDERBOOK_STATE_SEMANTICS", "EXECUTION_ROUTER_CONSTRAINTS", "OPTIMIZER_PATH_LATENCY"),
        emitted_artifacts=("LATENCY_POLICY_PACKET", "LIVE_PATH_EXCLUSION_RULE", "EXECUTION_QUALITY_CONSTRAINT"),
        decision_scope="May classify latency policy and exclude unapproved live-path dependencies.",
        forbidden_authority=("May not submit orders.", "May not authorize remote quantum backend dependency in live pretrade path."),
        handoff_inputs=("ROUTER_CONSTRAINT_PACKET", "OPTIMIZER_LATENCY_PACKET", "VENUE_LATENCY_PACKET"),
        handoff_outputs=("LATENCY_POLICY_DECISION", "EXECUTION_QUALITY_CONSTRAINT_PACKET"),
        input_packets=("LATENCY_INPUT_PACKET", "EXECUTION_PATH_PACKET"),
        output_packets=("LATENCY_POLICY_PACKET", "LIVE_PATH_EXCLUSION_PACKET"),
        parameter_scopes=("LATENCY_PARAMETER_SCOPE", "EXECUTION_QUALITY_PARAMETER_SCOPE"),
        algorithm_scopes=("LATENCY_CLASSIFICATION_ALGORITHM", "EXECUTION_QUALITY_ALGORITHM"),
        consumer_classes=("RISK", "ORDER_ROUTER", "OPTIMIZER", "LIVE_CANARY"),
        orchestration="Runs as a gate between optimizer/sizing outputs and execution-router eligibility.",
        risk="Risk consumes latency uncertainty and live-path exclusion signals.",
        router="Router receives latency-cleared constraints before future order submission.",
        receipt="Future latency policy decisions and exclusions require receipts.",
        health="Health monitor validates latency gates and live-path dependency exclusions.",
        source_connector_resolver="Consumes source-change snapshots, connector state, and resolver context for latency-sensitive decisions.",
        replay_paper="Can feed execution-quality constraints into replay/paper calibration.",
        optimizer="Constrains optimizer and quantum backend placement relative to live path.",
        dashboard="Dashboard may show latency policy, exclusions, and execution-quality status.",
        owner_scope="OWNER_APPROVED_EXECUTION_LATENCY_SCOPE",
        approval_behavior="Escalates live-path dependency or quantum backend placement questions to owner request routing.",
        classical_scope="CLASSICAL_LATENCY_AND_EXECUTION_QUALITY_SCOPE",
        quantum_scope="QUANTUM_BACKEND_PRECOMPUTED_CONTROL_PLANE_ONLY_SCOPE",
        runtime_scope="STATIC_LATENCY_CHARTER_ONLY_NO_RUNTIME_TELEMETRY_CREATED",
        live_scope="FUTURE_LIVE_PATH_EXCLUSION_GATE_ONLY_AFTER_ALL_GATES",
        dashboard_scope="OWNER_VISIBLE_LATENCY_AND_EXECUTION_QUALITY_STATUS_ONLY",
        source_scope="CONSUMES_SOURCE_CHANGE_SNAPSHOT_STATUS_IN_LATER_PHASES",
        connector_scope="CONSUMES_CONNECTOR_LATENCY_AND_ORDERBOOK_SEMANTICS",
        atomicrows_scope="CONSUMES_LATENCY_RELEVANT_PARAMETER_ROWS",
        fallback_behavior="If latency dependency is unapproved or unknown, exclude from live path and require precompute or review.",
        escalation_behavior="Escalates live-path dependency conflicts and unbounded latency risks.",
    ),
    "ORDER_ROUTER_AGENT": RoleSpec(
        description="Owns the future Execution Router final order-submission authority after all gates.",
        doctrine_terms=("Execution Router", "execution_router_remains_final_order_submission_authority_flag", "quantum_optimizer_direct_live_order_submission_allowed_flag"),
        derivation="Mapped to Execution Router doctrine converting approved intents into venue-specific order instructions only after all gates.",
        static_basis="Records router role without creating order path or order artifacts.",
        runtime_boundary="No order instruction, order receipt, live reachability, or venue call is created here.",
        primary_duties=(
            "Receive only approved future trade intents after owner, risk, source, connector, resolver, cash, latency, kill-switch, and permission gates.",
            "Convert approved intents into venue-specific order instructions in later live-authorized phases.",
            "Remain final order-submission authority in future approved live phases.",
        ),
        secondary_duties=("Reject raw agent desires and quantum outputs that bypass required gates.",),
        owned_surfaces=("EXECUTION_ROUTER", "ORDER_SUBMISSION_AUTHORITY", "VENUE_ORDER_INSTRUCTION"),
        consumed_artifacts=("APPROVED_TRADE_INTENT", "RISK_APPROVAL_PACKET", "SIZING_PACKET", "LATENCY_POLICY_PACKET", "CONNECTOR_READINESS_RECORD"),
        emitted_artifacts=("VENUE_ORDER_INSTRUCTION", "ORDER_RECEIPT"),
        decision_scope="May submit future venue-specific orders only after all gates and owner live authorization.",
        forbidden_authority=("May not create order artifacts in this package.", "May not accept raw agent desires or ungated quantum outputs."),
        handoff_inputs=("APPROVED_TRADE_INTENT_PACKET", "ALL_GATES_GREEN_PACKET"),
        handoff_outputs=("VENUE_ORDER_INSTRUCTION_PACKET", "ORDER_RECEIPT_REFERENCE"),
        input_packets=("APPROVED_TRADE_INTENT_PACKET", "ROUTER_GATE_PACKET"),
        output_packets=("VENUE_ORDER_INSTRUCTION_PACKET", "ORDER_RECEIPT_PACKET"),
        parameter_scopes=("ORDER_ROUTING_PARAMETER_SCOPE", "VENUE_ORDER_SHAPE_PARAMETER_SCOPE"),
        algorithm_scopes=("ORDER_ROUTING_ALGORITHM", "VENUE_ADAPTER_SELECTION_ALGORITHM"),
        consumer_classes=("LIVE_CANARY", "RECEIPT_EVENT_LOG", "DASHBOARD"),
        orchestration="Sits after all prerequisite gates in the orchestrated live path.",
        risk="Consumes and obeys risk approval; risk blocks stop router submission.",
        router="Primary owner of the future final Execution Router role.",
        receipt="Future order instructions, submissions, cancels, fills, and failures require receipts.",
        health="Health monitor validates router prerequisites and absence of static order artifacts.",
        source_connector_resolver="Requires source, connector, resolver, and cash prerequisites before order eligibility.",
        replay_paper="Receives live eligibility only after replay, paper, dual review, and owner promotion gates.",
        optimizer="Consumes only approved optimizer outputs converted into gated trade intents.",
        dashboard="Dashboard may display router readiness and owner live controls without routing authority.",
        owner_scope="OWNER_APPROVED_ORDER_ROUTER_SCOPE",
        approval_behavior="Escalates missing owner live authorization or gate conflicts to owner approval routing.",
        classical_scope="CLASSICAL_ORDER_ROUTING_SCOPE",
        quantum_scope="QUANTUM_OUTPUT_MAY_CREATE_ONLY_GATED_INTENT_NOT_DIRECT_ORDER_SCOPE",
        runtime_scope="STATIC_ROUTER_CHARTER_ONLY_NO_ORDER_RUNTIME_CREATED",
        live_scope="FUTURE_FINAL_ORDER_SUBMISSION_AUTHORITY_AFTER_ALL_GATES",
        dashboard_scope="OWNER_VISIBLE_ROUTER_STATUS_AND_LIVE_SCOPE_CONTROL_ONLY",
        source_scope="REQUIRES_ACCEPTED_SOURCE_EVIDENCE_FOR_SOURCE_DEPENDENT_FIELDS",
        connector_scope="REQUIRES_CONNECTOR_BINDING_AND_READINESS",
        atomicrows_scope="CONSUMES_APPROVED_PARAMETER_STACK_ONLY_AS_PART_OF_GATED_INTENT",
        fallback_behavior="If any gate is missing, stale, conflicted, or blocked, do not route and emit blocker.",
        escalation_behavior="Escalates gate mismatch, missing owner live scope, or connector/order-shape conflicts.",
    ),
    "LIVE_CANARY_AGENT": RoleSpec(
        description="Owns later limited-live canary staging and safety contract after all gates and owner approval.",
        doctrine_terms=("stage1_limited_live_canary_execution_scope", "owner live promotion review", "Execution Router"),
        derivation="Mapped to limited-live canary eligibility doctrine after source, connector, resolver, replay, paper, dual review, risk, and owner gates.",
        static_basis="Records canary readiness duties without creating live canary artifacts.",
        runtime_boundary="No live canary readiness packet, canary execution receipt, or live artifact is created here.",
        primary_duties=(
            "Manage later limited-live canary staging and canary safety contract.",
            "Consume owner live approval, dual review, risk, connector/source/runtime/cash readiness, latency, kill-switch, and router readiness.",
            "Emit limited-live readiness and safety packets only in later live-authorized phases.",
        ),
        secondary_duties=("Coordinate post-trade handoff and canary safety reporting when live canary exists.",),
        owned_surfaces=("LIMITED_LIVE_CANARY", "CANARY_SAFETY_CONTRACT", "POST_TRADE_HANDOFF"),
        consumed_artifacts=("OWNER_LIVE_APPROVAL", "DUAL_RESULT_REVIEW_PACKET", "RISK_APPROVAL_PACKET", "ROUTER_READINESS_PACKET"),
        emitted_artifacts=("CANARY_READINESS_PACKET", "CANARY_EXECUTION_RECEIPT", "POST_TRADE_HANDOFF_PACKET"),
        decision_scope="May classify future canary readiness after all prerequisites and owner approval.",
        forbidden_authority=("May not create live canary artifacts in this package.", "May not bypass owner approval or router authority."),
        handoff_inputs=("OWNER_LIVE_APPROVAL_PACKET", "ALL_GATES_GREEN_PACKET"),
        handoff_outputs=("CANARY_READINESS_STATUS", "CANARY_SAFETY_PACKET"),
        input_packets=("CANARY_ELIGIBILITY_PACKET", "OWNER_LIVE_APPROVAL_PACKET"),
        output_packets=("CANARY_READINESS_PACKET", "CANARY_SAFETY_PACKET"),
        parameter_scopes=("CANARY_PARAMETER_SCOPE", "LIMITED_LIVE_RISK_PARAMETER_SCOPE"),
        algorithm_scopes=("CANARY_SAFETY_ALGORITHM", "LIMITED_LIVE_ELIGIBILITY_ALGORITHM"),
        consumer_classes=("ORDER_ROUTER", "RISK", "DASHBOARD", "GOVERNANCE"),
        orchestration="Runs after owner live approval and all evidence/risk/router gates.",
        risk="Consumes risk approvals and kill-switch state; risk can block canary.",
        router="Canary execution uses Execution Router as final order-submission authority.",
        receipt="Future canary readiness, execution, and post-trade events require receipts.",
        health="Health monitor validates canary prerequisites and safety packet coverage.",
        source_connector_resolver="Requires source, connector, resolver, and cash readiness before canary eligibility.",
        replay_paper="Requires positive replay/paper evidence and dual review before canary.",
        optimizer="Consumes only gated optimizer candidates promoted through owner and risk review.",
        dashboard="Dashboard may show canary readiness and owner live controls.",
        owner_scope="OWNER_APPROVED_LIVE_CANARY_SCOPE",
        approval_behavior="Requests explicit owner live canary approval and escalation for blockers.",
        classical_scope="CLASSICAL_LIMITED_LIVE_CANARY_SCOPE",
        quantum_scope="QUANTUM_ORIGINATED_CANARY_INTENT_REQUIRES_ALL_GATES_SCOPE",
        runtime_scope="STATIC_CANARY_CHARTER_ONLY_NO_CANARY_RUNTIME_CREATED",
        live_scope="FUTURE_LIMITED_LIVE_CANARY_ONLY_AFTER_ALL_GATES_AND_OWNER_APPROVAL",
        dashboard_scope="OWNER_VISIBLE_CANARY_READINESS_AND_CONTROL_STATUS_ONLY",
        source_scope="REQUIRES_ACCEPTED_SOURCE_PACKETS",
        connector_scope="REQUIRES_CONNECTOR_AND_ROUTER_READINESS",
        atomicrows_scope="CONSUMES_PROMOTED_PARAMETER_STACKS_ONLY",
        fallback_behavior="If any canary precondition fails, remain not eligible and route blocker.",
        escalation_behavior="Escalates live-scope, safety, kill-switch, or readiness blockers.",
    ),
    "QUANTUM_RESEARCH_AGENT": RoleSpec(
        description="Owns true quantum, quantum-inspired, and hybrid classical-quantum research candidate surfaces.",
        doctrine_terms=("quantum_candidate_requires_objective_and_comparator", "quantum_candidate_requires_fallback_bundle", "quantum_candidate_parameter_rows_day1_complete", "quantum optimizer"),
        derivation="Mapped to quantum candidate template, objective/comparator, fallback bundle, and evidence-before-advantage doctrine.",
        static_basis="Records quantum research surfaces without claiming validated quantum advantage.",
        runtime_boundary="No true quantum backend execution, provider call, or quantum evidence artifact is created here.",
        primary_duties=(
            "Define true quantum, quantum-inspired, and hybrid candidate template packs.",
            "Map objectives, strongest-classical comparators, fallback bundles, failure modes, and parameter-family requests.",
            "Treat quantum advantage as a hypothesis until replay, paper, live, and owner-approved evidence exists.",
        ),
        secondary_duties=("Support QUBO, Ising, QAOA, VQE, annealing, and portfolio optimization compatibility surfaces.",),
        owned_surfaces=("QUANTUM_RESEARCH", "QUANTUM_CANDIDATE_TEMPLATE", "OBJECTIVE_COMPARATOR_MAPPING", "FALLBACK_BUNDLE_MAPPING"),
        consumed_artifacts=("ATOMICROWS_PARAMETER_FAMILY", "OBJECTIVE_FORMULA", "STRONGEST_CLASSICAL_COMPARATOR", "REPLAY_PAPER_FEEDBACK"),
        emitted_artifacts=("QUANTUM_CANDIDATE_TEMPLATE_PACK", "OBJECTIVE_COMPARATOR_MAPPING_PACKET", "FALLBACK_BUNDLE_PACKET", "KNOWN_FAILURE_MODE_PACKET"),
        decision_scope="May propose quantum candidate templates and compatibility mappings for later evidence lanes.",
        forbidden_authority=("May not claim validated quantum advantage without evidence.", "May not call real quantum backends in this package."),
        handoff_inputs=("PARAMETER_FAMILY_REFERENCE", "OBJECTIVE_FORMULA_PACKET", "CLASSICAL_COMPARATOR_PACKET"),
        handoff_outputs=("QUANTUM_CANDIDATE_TEMPLATE_PACKET", "QUANTUM_PARAMETER_FAMILY_REQUEST"),
        input_packets=("QUANTUM_RESEARCH_INPUT_PACKET", "OBJECTIVE_COMPARATOR_PACKET"),
        output_packets=("QUANTUM_CANDIDATE_TEMPLATE_PACKET", "QUANTUM_FALLBACK_BUNDLE_PACKET"),
        parameter_scopes=("QUANTUM_PARAMETER_FAMILY_SCOPE", "QUBO_PARAMETER_SCOPE", "PORTFOLIO_OPTIMIZATION_PARAMETER_SCOPE"),
        algorithm_scopes=("QUBO", "ISING", "QAOA", "VQE", "ANNEALING", "HYBRID_CLASSICAL_QUANTUM"),
        consumer_classes=("OPTIMIZER", "QUANTUM_BACKEND", "REPLAY", "PAPER", "DASHBOARD"),
        orchestration="Feeds quantum candidate templates to optimizer through orchestrated research routes.",
        risk="Risk receives quantum failure modes, feasibility masks, and evidence limitations.",
        router="No router access; quantum research cannot submit orders.",
        receipt="Future quantum candidate lifecycle events require receipts.",
        health="Health monitor validates objective, comparator, fallback, and no-advantage-claim rules.",
        source_connector_resolver="Quantum outputs cannot override source, connector, resolver, cash, or owner gates.",
        replay_paper="Quantum candidates require replay and paper evidence before advantage claims.",
        optimizer="Feeds optimizer with quantum candidate surfaces and comparator mappings.",
        dashboard="Dashboard may show quantum candidate drilldowns and owner priority controls.",
        owner_scope="OWNER_APPROVED_QUANTUM_RESEARCH_SCOPE",
        approval_behavior="Requests owner approval for quantum priority, backend eligibility, and candidate promotion.",
        classical_scope="STRONGEST_CLASSICAL_COMPARATOR_RESEARCH_SCOPE",
        quantum_scope="TRUE_QUANTUM_QUANTUM_INSPIRED_HYBRID_RESEARCH_SCOPE",
        runtime_scope="STATIC_QUANTUM_RESEARCH_CHARTER_ONLY_NO_BACKEND_RUNTIME_CREATED",
        live_scope="NO_LIVE_TRADE_AUTHORITY_FROM_QUANTUM_RESEARCH",
        dashboard_scope="OWNER_VISIBLE_QUANTUM_RESEARCH_AND_PRIORITY_STATUS_ONLY",
        source_scope="CANNOT_OVERRIDE_SOURCE_EVIDENCE",
        connector_scope="CANNOT_OVERRIDE_CONNECTOR_SEMANTICS",
        atomicrows_scope="REQUESTS_QUANTUM_PARAMETER_FAMILIES_FROM_ATOMICROWS",
        fallback_behavior="If objective, comparator, fallback, or Day-1 parameter rows are missing, block candidate.",
        escalation_behavior="Escalates missing objective/comparator, backend policy, and quantum-priority conflicts.",
    ),
    "QUANTUM_BACKEND_AGENT": RoleSpec(
        description="Owns future quantum backend compatibility and provider execution boundary surfaces.",
        doctrine_terms=("quantum backend compatibility", "quantum_optimizer_live_pretrade_remote_backend_dependency_allowed", "fallback_bundle_id"),
        derivation="Mapped to quantum backend boundary doctrine requiring approved candidate packs, resource envelope, fallback bundle, and owner/backend policy.",
        static_basis="Records backend compatibility surfaces only.",
        runtime_boundary="No QPU/provider call, credential, backend execution, or real quantum artifact is created here.",
        primary_duties=(
            "Define future quantum backend compatibility and provider/backend eligibility records.",
            "Consume approved quantum candidate packs, resource-envelope class, fallback bundle, and owner/backend policy in later phases.",
            "Emit backend compatibility and readiness states only in later scoped workflows.",
        ),
        secondary_duties=("Keep backend work outside live pretrade path unless precomputed and later approved.",),
        owned_surfaces=("QUANTUM_BACKEND_COMPATIBILITY", "PROVIDER_BOUNDARY", "RESOURCE_ENVELOPE"),
        consumed_artifacts=("APPROVED_QUANTUM_CANDIDATE_PACK", "RESOURCE_ENVELOPE_CLASS", "FALLBACK_BUNDLE", "OWNER_BACKEND_POLICY"),
        emitted_artifacts=("BACKEND_COMPATIBILITY_RECORD", "BACKEND_READINESS_STATE"),
        decision_scope="May classify future backend compatibility and resource eligibility.",
        forbidden_authority=("May not execute real quantum backends here.", "May not materialize provider credentials or live backend dependency."),
        handoff_inputs=("QUANTUM_CANDIDATE_TEMPLATE_PACKET", "OWNER_BACKEND_POLICY_PACKET"),
        handoff_outputs=("BACKEND_COMPATIBILITY_STATUS", "BACKEND_READINESS_BLOCK"),
        input_packets=("QUANTUM_BACKEND_ELIGIBILITY_PACKET", "RESOURCE_ENVELOPE_PACKET"),
        output_packets=("BACKEND_COMPATIBILITY_PACKET", "BACKEND_READINESS_PACKET"),
        parameter_scopes=("QUANTUM_BACKEND_PARAMETER_SCOPE", "RESOURCE_ENVELOPE_PARAMETER_SCOPE"),
        algorithm_scopes=("QPU_COMPATIBILITY_CHECK", "SIMULATOR_COMPATIBILITY_CHECK", "HYBRID_BACKEND_SELECTION"),
        consumer_classes=("OPTIMIZER", "QUANTUM_RESEARCH", "EXECUTION_LATENCY", "DASHBOARD"),
        orchestration="Receives approved quantum candidates through orchestrator and returns backend compatibility status.",
        risk="Risk consumes backend uncertainty, fallback, and infeasible candidate states.",
        router="Backend outputs cannot route orders and cannot be live pretrade dependencies without later gates.",
        receipt="Future backend compatibility and execution readiness states require receipts.",
        health="Health monitor validates no provider calls, no credentials, and backend boundary adherence.",
        source_connector_resolver="Backend outputs remain subordinate to source, connector, resolver, cash, and owner gates.",
        replay_paper="Backend compatibility may support replay/paper candidates but does not prove advantage.",
        optimizer="Feeds optimizer with backend feasibility and fallback state.",
        dashboard="Dashboard may show backend eligibility and owner backend policy controls.",
        owner_scope="OWNER_APPROVED_QUANTUM_BACKEND_SCOPE",
        approval_behavior="Requests owner approval for backend policy, provider eligibility, and execution readiness.",
        classical_scope="CLASSICAL_FALLBACK_AND_SIMULATOR_COMPATIBILITY_SCOPE",
        quantum_scope="TRUE_QUANTUM_BACKEND_COMPATIBILITY_SCOPE_WITH_NO_EXECUTION_CREATED",
        runtime_scope="STATIC_BACKEND_CHARTER_ONLY_NO_QPU_OR_PROVIDER_RUNTIME_CREATED",
        live_scope="NO_LIVE_PRETRADE_BACKEND_DEPENDENCY_CREATED",
        dashboard_scope="OWNER_VISIBLE_BACKEND_COMPATIBILITY_STATUS_ONLY",
        source_scope="CANNOT_OVERRIDE_SOURCE_EVIDENCE",
        connector_scope="CANNOT_OVERRIDE_CONNECTOR_OR_RUNTIME_CASH_GATES",
        atomicrows_scope="CONSUMES_QUANTUM_PARAMETER_ROWS_AND_FALLBACK_BUNDLES",
        fallback_behavior="If backend eligibility, resource envelope, or fallback bundle is missing, block backend use.",
        escalation_behavior="Escalates backend policy, provider eligibility, credential, and fallback conflicts.",
    ),
    "DASHBOARD_AGENT": RoleSpec(
        description="Owns owner-visible controls, status panels, approval menus, quantum-priority controls, and research intake displays.",
        doctrine_terms=("dashboard_access_currently_available_flag", "dashboard_runtime_ui_service_required_before_access_flag", "dashboard_and_telegram_owner_interfaces_create_research_intake_not_trading_authority_flag"),
        derivation="Mapped to dashboard/runtime boundary doctrine: owner interfaces create review/control/research-intake requests, not trading authority.",
        static_basis="Records dashboard surfaces without creating a dashboard UI or runtime service.",
        runtime_boundary="No dashboard runtime, Telegram runtime, or trading interface is created here.",
        primary_duties=(
            "Expose owner control, approval, review, role health, validation status, quantum priority, and research intake surfaces in later dashboard work.",
            "Consume validation reports, agent status, owner approval requests, optimizer/quantum summaries, risk states, source states, and live-readiness states.",
            "Emit owner UI/control packets only in later dashboard-scoped workflows.",
        ),
        secondary_duties=("Preserve dashboard and Telegram as research intake/control requests, not trading authority.",),
        owned_surfaces=("OWNER_DASHBOARD_CONTROL", "APPROVAL_MENU", "ROLE_HEALTH_PANEL", "QUANTUM_PRIORITY_CONTROL", "RESEARCH_INTAKE_DISPLAY"),
        consumed_artifacts=("VALIDATION_REPORT", "AGENT_STATUS_PACKET", "OWNER_APPROVAL_REQUEST_PACKET", "OPTIMIZER_SUMMARY", "RISK_STATE_PACKET"),
        emitted_artifacts=("OWNER_UI_CONTROL_PACKET", "DASHBOARD_RESEARCH_INTAKE_PACKET"),
        decision_scope="May organize owner-visible status and control requests in later dashboard work.",
        forbidden_authority=("May not trade or submit orders.", "May not approve for owner or create runtime dashboard access here."),
        handoff_inputs=("AGENT_STATUS_PACKET", "APPROVAL_REQUEST_PACKET", "RESEARCH_INPUT"),
        handoff_outputs=("OWNER_CONTROL_REQUEST", "DASHBOARD_STATUS_PACKET"),
        input_packets=("DASHBOARD_STATUS_INPUT_PACKET", "RESEARCH_INTAKE_PACKET"),
        output_packets=("OWNER_CONTROL_PACKET", "DASHBOARD_STATUS_PACKET"),
        parameter_scopes=("DASHBOARD_DISPLAY_PARAMETER_SCOPE", "OWNER_CONTROL_PARAMETER_SCOPE"),
        algorithm_scopes=("DASHBOARD_STATUS_AGGREGATION", "OWNER_QUEUE_PRIORITIZATION"),
        consumer_classes=("OWNER", "GOVERNANCE", "VALIDATION", "ORCHESTRATION"),
        orchestration="Displays orchestrated agent status and handoff needs for owner review.",
        risk="Shows risk states and blocks without overriding Risk Gate.",
        router="May show router readiness but cannot submit orders.",
        receipt="Future dashboard actions and owner control packets require receipts.",
        health="Displays role health, KPIs, missed duties, and validation status.",
        source_connector_resolver="Displays source, connector, and resolver readiness without creating facts or bindings.",
        replay_paper="Displays replay/paper/dual review status without promotion authority.",
        optimizer="Displays optimizer and quantum candidate summaries plus owner quantum controls.",
        dashboard="Primary owner-visible interface surface for later implementation.",
        owner_scope="OWNER_APPROVED_DASHBOARD_SCOPE",
        approval_behavior="Packages owner UI decisions into approval request and receipt workflows.",
        classical_scope="CLASSICAL_DASHBOARD_STATUS_AGGREGATION_SCOPE",
        quantum_scope="OWNER_QUANTUM_PRIORITY_CONTROL_DISPLAY_SCOPE",
        runtime_scope="STATIC_DASHBOARD_CHARTER_ONLY_NO_UI_RUNTIME_CREATED",
        live_scope="NO_TRADING_AUTHORITY_FROM_DASHBOARD_OR_TELEGRAM",
        dashboard_scope="PRIMARY_DASHBOARD_OWNER_CONTROL_AND_RESEARCH_INTAKE_SCOPE",
        source_scope="DISPLAYS_SOURCE_STATUS_ONLY",
        connector_scope="DISPLAYS_CONNECTOR_STATUS_ONLY",
        atomicrows_scope="DISPLAYS_PARAMETER_INVENTORY_AND_LIFECYCLE_STATUS_ONLY",
        fallback_behavior="If dashboard service is absent, keep controls as static request surfaces.",
        escalation_behavior="Escalates owner UI control ambiguity, approval queue conflicts, and runtime service blockers.",
    ),
    "GOVERNANCE_AGENT": RoleSpec(
        description="Owns governance, authority classification, owner override doctrine, and internal/external fact separation.",
        doctrine_terms=("owner final policy authority", "agent_autonomy_class", "owner_source_evidence_definitions_packet_external_fact_acceptance_authority"),
        derivation="Mapped to governance doctrine separating owner internal policy authority from external facts and runtime evidence.",
        static_basis="Records governance classification without creating live or fact authority.",
        runtime_boundary="No governance runtime packet or external fact evidence is created here.",
        primary_duties=(
            "Enforce authority classification, owner override doctrine, and internal-policy versus external-fact separation.",
            "Route canonical policy decisions, validation reports, compliance markers, role charters, and override receipts.",
            "Prevent internal overrides from being misused as external fact truth.",
        ),
        secondary_duties=("Classify agent autonomy and permission boundaries for bounded tool-using agents.",),
        owned_surfaces=("GOVERNANCE", "AUTHORITY_CLASSIFICATION", "OWNER_OVERRIDE_DOCTRINE", "POLICY_ROUTING"),
        consumed_artifacts=("MASTER_PLAN_DOCTRINE", "OWNER_DECISION", "VALIDATION_REPORT", "COMPLIANCE_MARKER", "ROLE_CHARTER"),
        emitted_artifacts=("GOVERNANCE_PACKET", "AUTHORITY_CLASS_REPORT", "OWNER_POLICY_RECEIPT", "BOUNDARY_AUDIT_REPORT"),
        decision_scope="May classify internal authority and governance boundaries.",
        forbidden_authority=("May not create external fact truth.", "May not approve for owner."),
        handoff_inputs=("ROLE_CHARTER_PACKET", "OWNER_DECISION_RECEIPT", "VALIDATION_REPORT"),
        handoff_outputs=("AUTHORITY_CLASSIFICATION_PACKET", "GOVERNANCE_BOUNDARY_PACKET"),
        input_packets=("GOVERNANCE_INPUT_PACKET", "OWNER_POLICY_PACKET"),
        output_packets=("GOVERNANCE_PACKET", "AUTHORITY_CLASS_REPORT"),
        parameter_scopes=("GOVERNANCE_PARAMETER_SCOPE", "AUTHORITY_CLASS_PARAMETER_SCOPE"),
        algorithm_scopes=("AUTHORITY_CLASSIFICATION_ALGORITHM", "POLICY_ROUTING_ALGORITHM"),
        consumer_classes=("ORCHESTRATION", "VALIDATION", "DASHBOARD", "OWNER_APPROVAL"),
        orchestration="Supplies authority classifications to orchestrator before handoffs proceed.",
        risk="Governance prevents risk overrides from becoming external fact claims.",
        router="Governance enforces owner and gate prerequisites before router eligibility.",
        receipt="Future governance decisions and owner-policy receipts require event records.",
        health="Health monitor validates governance boundaries and role ownership maps.",
        source_connector_resolver="Enforces source/connector/resolver fact boundaries.",
        replay_paper="Enforces evidence boundaries around replay/paper and live promotion.",
        optimizer="Enforces optimizer and quantum authority boundaries.",
        dashboard="Feeds owner-visible governance and authority-class reports.",
        owner_scope="OWNER_APPROVED_GOVERNANCE_SCOPE",
        approval_behavior="Routes governance conflicts and policy changes to owner approval request packaging.",
        classical_scope="CLASSICAL_GOVERNANCE_CLASSIFICATION_SCOPE",
        quantum_scope="QUANTUM_AUTHORITY_BOUNDARY_GOVERNANCE_SCOPE",
        runtime_scope="STATIC_GOVERNANCE_CHARTER_ONLY_NO_RUNTIME_PACKET_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_GOVERNANCE_CLASSIFICATION",
        dashboard_scope="OWNER_VISIBLE_GOVERNANCE_STATUS_ONLY",
        source_scope="SEPARATES_OWNER_POLICY_FROM_ACCEPTED_SOURCE_FACTS",
        connector_scope="PREVENTS_CONNECTOR_BINDING_WITHOUT_EVIDENCE",
        atomicrows_scope="ENFORCES_ATOMICROWS_INVENTORY_NOT_TRADER_BOUNDARY",
        fallback_behavior="If authority class is ambiguous, use stricter boundary and escalate.",
        escalation_behavior="Escalates authority conflicts, owner policy changes, and external-fact boundary risks.",
    ),
    "VALIDATION_AGENT": RoleSpec(
        description="Owns schema validation, deterministic gates, reports, role coverage, and fail-closed behavior.",
        doctrine_terms=("Coverage / Health Monitor", "validation gates", "agent_quality_scorecard_required", "agent_output_trust_score_required"),
        derivation="Mapped to coverage/health monitor and validation gate doctrine proving coded behavior matches the master plan.",
        static_basis="Records validation duties and validates this static package.",
        runtime_boundary="Does not weaken gates or create runtime artifacts.",
        primary_duties=(
            "Validate schemas, registries, fixtures, deterministic reports, role coverage, and fail-closed tests.",
            "Integrate static validators into run_validation_gates without weakening existing gates.",
            "Prove this package follows the master plan and creates no forbidden artifacts.",
        ),
        secondary_duties=("Track role ownership, output trust, missed duties, and deterministic report readiness.",),
        owned_surfaces=("SCHEMA_VALIDATION", "STATIC_GATE_ENFORCEMENT", "DETERMINISTIC_REPORT_VALIDATION", "FAIL_CLOSED_TESTS"),
        consumed_artifacts=("SCHEMA_FILE", "REGISTRY_FILE", "FIXTURE_FILE", "REPORT_FILE", "TEST_OUTPUT"),
        emitted_artifacts=("VALIDATION_REPORT", "BLOCKER_REPORT", "GATE_SUCCESS_MARKER"),
        decision_scope="May pass or fail static validation gates based on deterministic checks.",
        forbidden_authority=("May not approve for owner.", "May not weaken existing gates or create runtime artifacts."),
        handoff_inputs=("VALIDATION_TARGET_SET", "GATE_RESULT_PACKET"),
        handoff_outputs=("VALIDATION_DECISION", "BLOCKER_REPORT"),
        input_packets=("VALIDATION_INPUT_PACKET", "TEST_RESULT_PACKET"),
        output_packets=("VALIDATION_REPORT_PACKET", "GATE_SUCCESS_PACKET"),
        parameter_scopes=("VALIDATION_PARAMETER_SCOPE", "REPORT_COUNT_PARAMETER_SCOPE"),
        algorithm_scopes=("SCHEMA_VALIDATION_ALGORITHM", "FAIL_CLOSED_ASSERTION_ALGORITHM"),
        consumer_classes=("GOVERNANCE", "DASHBOARD", "ORCHESTRATION", "OWNER"),
        orchestration="Provides gate outcomes to orchestrator before workflows advance.",
        risk="Validates risk-gate surfaces but does not decide risk.",
        router="Validates router boundary and absence of order artifacts.",
        receipt="Future validation events and gate results are event-log candidates.",
        health="Primary static owner of coverage/health monitor validation for this package.",
        source_connector_resolver="Validates source, connector, and resolver boundaries and absence of created artifacts.",
        replay_paper="Validates replay/paper/dual review boundaries and absence of executions.",
        optimizer="Validates deterministic scoring/arbitration and quantum no-evidence claims.",
        dashboard="Feeds dashboard validation status in later UI phases.",
        owner_scope="OWNER_APPROVED_VALIDATION_SCOPE",
        approval_behavior="Escalates validation blockers and final-readiness gaps to owner approval request packaging.",
        classical_scope="CLASSICAL_STATIC_VALIDATION_SCOPE",
        quantum_scope="QUANTUM_FORWARD_FIELD_VALIDATION_SCOPE",
        runtime_scope="STATIC_VALIDATION_ONLY_NO_RUNTIME_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_VALIDATION",
        dashboard_scope="OWNER_VISIBLE_VALIDATION_STATUS_ONLY",
        source_scope="VALIDATES_NO_SOURCE_ACCEPTANCE_ARTIFACT_CREATED",
        connector_scope="VALIDATES_NO_CONNECTOR_BINDING_ARTIFACT_CREATED",
        atomicrows_scope="VALIDATES_NO_ATOMICROWS_BUNDLE_OR_HASH_CREATED",
        fallback_behavior="If any invariant fails, fail closed and withhold success marker.",
        escalation_behavior="Escalates schema, report, role coverage, artifact, and gate failures.",
    ),
    "COMPLIANCE_MARKER_AGENT": RoleSpec(
        description="Owns compliance/control-state labels without creating legal conclusions or external facts.",
        doctrine_terms=("governance", "authority classification", "control state classification"),
        derivation="Mapped to compliance marker and control-state classification surfaces under governance boundaries.",
        static_basis="Records marker duties without legal conclusions.",
        runtime_boundary="No legal, external fact, or runtime compliance artifact is created here.",
        primary_duties=(
            "Label compliance and control states from governance, validation, source, risk, live-scope, and owner policy inputs.",
            "Emit compliance marker packets and status labels in later workflows.",
            "Keep markers non-legal and non-fact-creating.",
        ),
        secondary_duties=("Support dashboard and governance review with status labels.",),
        owned_surfaces=("COMPLIANCE_MARKER", "CONTROL_STATE_LABEL", "NON_LEGAL_STATUS_CLASSIFICATION"),
        consumed_artifacts=("GOVERNANCE_PACKET", "VALIDATION_REPORT", "SOURCE_STATE", "RISK_STATE", "OWNER_POLICY"),
        emitted_artifacts=("COMPLIANCE_MARKER_PACKET", "CONTROL_STATE_LABEL"),
        decision_scope="May classify internal control-state labels.",
        forbidden_authority=("May not create legal conclusions.", "May not create external facts or trading authority."),
        handoff_inputs=("GOVERNANCE_BOUNDARY_PACKET", "VALIDATION_STATUS_PACKET"),
        handoff_outputs=("COMPLIANCE_STATUS_LABEL", "CONTROL_STATE_PACKET"),
        input_packets=("COMPLIANCE_INPUT_PACKET", "CONTROL_STATE_INPUT_PACKET"),
        output_packets=("COMPLIANCE_MARKER_PACKET", "CONTROL_STATE_PACKET"),
        parameter_scopes=("COMPLIANCE_MARKER_PARAMETER_SCOPE",),
        algorithm_scopes=("CONTROL_STATE_CLASSIFICATION_ALGORITHM",),
        consumer_classes=("GOVERNANCE", "DASHBOARD", "VALIDATION"),
        orchestration="Provides status labels to orchestrator for governed workflow display.",
        risk="Labels risk control states without overriding Risk Gate.",
        router="Labels router control state without order authority.",
        receipt="Future compliance marker changes require event records when material.",
        health="Health monitor consumes marker status for control coverage.",
        source_connector_resolver="Labels source/connector/resolver control states without creating facts.",
        replay_paper="Labels replay/paper evidence states without live promotion.",
        optimizer="Labels optimizer and quantum control states without evidence claims.",
        dashboard="Feeds owner-visible control-state labels to later dashboard panels.",
        owner_scope="OWNER_APPROVED_COMPLIANCE_MARKER_SCOPE",
        approval_behavior="Escalates ambiguous or material control-state labels to owner request routing.",
        classical_scope="CLASSICAL_CONTROL_STATE_LABELING_SCOPE",
        quantum_scope="QUANTUM_CONTROL_STATE_LABELING_SCOPE_WITH_NO_ADVANTAGE_CLAIM",
        runtime_scope="STATIC_MARKER_CHARTER_ONLY_NO_RUNTIME_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_MARKERS",
        dashboard_scope="OWNER_VISIBLE_CONTROL_STATE_LABELS_ONLY",
        source_scope="LABELS_SOURCE_STATE_ONLY",
        connector_scope="LABELS_CONNECTOR_STATE_ONLY",
        atomicrows_scope="LABELS_ATOMICROWS_CONTROL_STATE_ONLY",
        fallback_behavior="If marker evidence is incomplete, label as blocked, unknown, or review required.",
        escalation_behavior="Escalates material ambiguity and governance boundary conflicts.",
    ),
    "OWNER_APPROVAL_REQUEST_AGENT": RoleSpec(
        description="Packages owner approval and override requests; never approves for owner.",
        doctrine_terms=("owner approval required", "owner override", "dashboard owner control"),
        derivation="Mapped to owner approval and override request packaging required by governed workflows.",
        static_basis="Records request packaging without creating owner decisions.",
        runtime_boundary="No owner approval receipt is created here.",
        primary_duties=(
            "Package owner approval and override requests from unresolved blockers, promotion requests, quantum-priority requests, dashboard requests, risk escalation, and governance escalation.",
            "Emit owner approval request packets and owner decision queue records in later workflows.",
            "Preserve that the agent may request but never approve for owner.",
        ),
        secondary_duties=("Normalize request context, required evidence, and decision options for owner review.",),
        owned_surfaces=("OWNER_APPROVAL_REQUEST", "OWNER_DECISION_QUEUE", "OVERRIDE_REQUEST_PACKAGING"),
        consumed_artifacts=("UNRESOLVED_BLOCKER", "PROMOTION_REQUEST", "QUANTUM_PRIORITY_REQUEST", "RISK_ESCALATION", "GOVERNANCE_ESCALATION"),
        emitted_artifacts=("OWNER_APPROVAL_REQUEST_PACKET", "OWNER_DECISION_QUEUE_RECORD"),
        decision_scope="May decide request completeness and routing priority, not approval outcome.",
        forbidden_authority=("May not approve for owner.", "May not convert requests into live authority."),
        handoff_inputs=("BLOCKER_PACKET", "PROMOTION_REQUEST_PACKET", "QUANTUM_PRIORITY_REQUEST_PACKET"),
        handoff_outputs=("OWNER_APPROVAL_REQUEST_PACKET", "OWNER_DECISION_QUEUE_RECORD"),
        input_packets=("OWNER_APPROVAL_REQUEST_INPUT_PACKET", "ESCALATION_PACKET"),
        output_packets=("OWNER_APPROVAL_REQUEST_PACKET", "OWNER_DECISION_QUEUE_PACKET"),
        parameter_scopes=("OWNER_REQUEST_PARAMETER_SCOPE",),
        algorithm_scopes=("REQUEST_PACKAGING_ALGORITHM", "OWNER_QUEUE_PRIORITIZATION"),
        consumer_classes=("OWNER", "DASHBOARD", "GOVERNANCE", "ORCHESTRATION"),
        orchestration="Receives escalations from orchestrator and returns owner decision queue records.",
        risk="Packages risk escalations for owner review without overriding risk decisions.",
        router="Packages live/router approval requests but cannot authorize routing.",
        receipt="Future approval requests and owner decisions require event records.",
        health="Health monitor validates request packaging and unresolved blocker routing.",
        source_connector_resolver="Packages source, connector, and resolver blockers for owner review when policy is needed.",
        replay_paper="Packages replay/paper promotion requests for owner review.",
        optimizer="Packages optimizer, quantum priority, and arbitration policy requests.",
        dashboard="Feeds owner approval queues to later dashboard surfaces.",
        owner_scope="OWNER_APPROVAL_REQUEST_PACKAGING_SCOPE",
        approval_behavior="Creates request packets and waits for owner decision receipt; never approves.",
        classical_scope="CLASSICAL_OWNER_REQUEST_PACKAGING_SCOPE",
        quantum_scope="QUANTUM_PRIORITY_REQUEST_PACKAGING_SCOPE",
        runtime_scope="STATIC_REQUEST_AGENT_CHARTER_ONLY_NO_APPROVAL_RUNTIME_CREATED",
        live_scope="NO_LIVE_AUTHORITY_FROM_REQUEST_PACKAGING",
        dashboard_scope="OWNER_VISIBLE_APPROVAL_QUEUE_STATUS_ONLY",
        source_scope="PACKAGES_SOURCE_POLICY_REQUESTS_ONLY",
        connector_scope="PACKAGES_CONNECTOR_POLICY_REQUESTS_ONLY",
        atomicrows_scope="PACKAGES_ATOMICROWS_PROMOTION_OR_OVERRIDE_REQUESTS",
        fallback_behavior="If request context is incomplete, return to originating agent for missing evidence.",
        escalation_behavior="Escalates complete approval requests to owner queue and governance visibility.",
    ),
}


def _derived_spec(role: str) -> RoleSpec:
    if role in ROLE_SPECS:
        return ROLE_SPECS[role]
    base = role.replace("_AGENT", "").replace("_", " ").title()
    terms = {
        "GOVERNANCE_AGENT": ("governance",),
    }.get(role, ("QTT orchestration-spine law",))
    return RoleSpec(
        description=f"Owns the {base} charter surface within the governed QTT architecture.",
        doctrine_terms=terms,
        derivation=f"Mapped to master-plan doctrine for {base} duties and handoffs.",
        static_basis="Static charter only; no runtime artifact is created.",
        runtime_boundary="Future runtime behavior requires downstream scoped evidence and gates.",
        primary_duties=(f"Operate the {base} role within governed QTT handoffs.",),
        secondary_duties=(f"Report {base} blockers and readiness to validation and orchestration.",),
        owned_surfaces=(f"{role}_SURFACE",),
        consumed_artifacts=(f"{role}_INPUT_PACKET",),
        emitted_artifacts=(f"{role}_OUTPUT_PACKET",),
        decision_scope=f"May decide {base} readiness within its static role scope.",
        forbidden_authority=("May not approve for owner.", "May not bypass source, risk, owner, or router gates."),
        handoff_inputs=(f"{role}_HANDOFF_INPUT",),
        handoff_outputs=(f"{role}_HANDOFF_OUTPUT",),
        input_packets=(f"{role}_INPUT_PACKET",),
        output_packets=(f"{role}_OUTPUT_PACKET",),
        parameter_scopes=(f"{role}_PARAMETER_SCOPE",),
        algorithm_scopes=(f"{role}_ALGORITHM_SCOPE",),
        consumer_classes=("ORCHESTRATION", "VALIDATION"),
        orchestration=f"Participates in orchestrated {base} handoffs under Decision Orchestrator control.",
        risk=f"Respects Risk Gate decisions for {base} outputs.",
        router=f"Does not route orders; Execution Router remains final authority after all gates.",
        receipt=f"Future {base} decisions require receipt/event-log records.",
        health=f"Coverage and health monitor validates {base} ownership and outputs.",
        source_connector_resolver=f"N/A_STATIC_CHARTER_RELATIONSHIP: {base} does not create source, connector, or resolver artifacts here.",
        replay_paper=f"N/A_STATIC_CHARTER_RELATIONSHIP: {base} does not execute replay or paper here.",
        optimizer=f"N/A_STATIC_CHARTER_RELATIONSHIP: {base} honors deterministic optimizer arbitration when consumed.",
        dashboard=f"Dashboard may show {base} status in later owner UI work.",
        owner_scope=f"OWNER_APPROVED_{role}_SCOPE",
        approval_behavior="Routes approval needs to OWNER_APPROVAL_REQUEST_AGENT.",
        classical_scope=f"CLASSICAL_{role}_SCOPE",
        quantum_scope=f"QUANTUM_FORWARD_AWARE_{role}_SCOPE",
        runtime_scope="STATIC_CHARTER_ONLY_NO_RUNTIME_CREATED",
        live_scope="NO_LIVE_AUTHORITY_CREATED",
        dashboard_scope="OWNER_VISIBLE_STATUS_ONLY",
        source_scope="DOES_NOT_ACCEPT_SOURCE_FACTS",
        connector_scope="DOES_NOT_BIND_CONNECTOR_SEMANTICS",
        atomicrows_scope="DOES_NOT_CREATE_ATOMICROWS_BUNDLE_OR_HASH",
        fallback_behavior="Fail closed and escalate when prerequisites are missing.",
        escalation_behavior="Escalate blockers to orchestration, governance, validation, or owner request routing.",
    )


ROLE_SPECS.update(
    {
        role: _derived_spec(role)
        for role in ROLE_ORDER
        if role not in ROLE_SPECS
    }
)


def _quantum_access(role: str) -> tuple[str, ...]:
    if role in QUANTUM_RELEVANT_ROLES:
        return QUANTUM_COMPATIBILITY_CLASSES
    return (
        "OWNER_QUANTUM_PRIORITY",
        "OWNER_FORCED_QUANTUM",
        "REPLAY_PAPER_EVIDENCE_REQUIRED_BEFORE_ADVANTAGE_CLAIM",
    )


def build_charter(role: str, *, synthetic: bool = False) -> dict[str, Any]:
    spec = ROLE_SPECS[role]
    prefix = "Synthetic valid fixture charter: " if synthetic else ""
    derivation = spec.derivation
    if synthetic:
        derivation = (
            f"Synthetic non-authoritative placeholder for {role}; preserves the "
            f"same master-plan-derived duties without evidence claims."
        )
    return {
        "agent_role": role,
        "agent_role_id": ROLE_IDS[role],
        "agent_description": prefix + spec.description,
        "master_plan_doctrine_terms_used": list(spec.doctrine_terms),
        "master_plan_role_derivation_summary": derivation,
        "master_plan_static_authority_basis": spec.static_basis,
        "master_plan_runtime_boundary_basis": spec.runtime_boundary,
        "primary_duties": list(spec.primary_duties),
        "secondary_duties": list(spec.secondary_duties),
        "owned_surfaces": list(spec.owned_surfaces),
        "consumed_artifacts": list(spec.consumed_artifacts),
        "emitted_artifacts": list(spec.emitted_artifacts),
        "decision_authority_scope": spec.decision_scope,
        "forbidden_decision_authority": list(spec.forbidden_authority),
        "handoff_inputs": list(spec.handoff_inputs),
        "handoff_outputs": list(spec.handoff_outputs),
        "input_packet_types": list(spec.input_packets),
        "output_packet_types": list(spec.output_packets),
        "applicable_parameter_family_scopes": list(spec.parameter_scopes),
        "applicable_algorithm_family_scopes": list(spec.algorithm_scopes),
        "authorized_consumer_classes": list(spec.consumer_classes),
        "orchestration_spine_relationship": spec.orchestration,
        "risk_gate_relationship": spec.risk,
        "execution_router_relationship": spec.router,
        "receipt_event_log_relationship": spec.receipt,
        "coverage_health_monitor_relationship": spec.health,
        "source_to_connector_to_resolver_relationship": spec.source_connector_resolver,
        "replay_paper_dual_review_relationship": spec.replay_paper,
        "optimizer_arbitration_relationship": spec.optimizer,
        "dashboard_owner_control_relationship": spec.dashboard,
        "owner_override_supported": True,
        "owner_override_satisfaction_basis": OWNER_OVERRIDE_SATISFACTION_BASIS,
        "owner_approved_scope": spec.owner_scope,
        "may_request_owner_approval": True,
        "approval_request_behavior": spec.approval_behavior,
        "may_approve_for_owner": False,
        "codex_may_approve_for_owner": False,
        "chatgpt_may_approve_for_owner": False,
        "qtt_agent_authority_over_owner": False,
        "blocks_qtt_when_owner_override_present": False,
        "classical_scope": spec.classical_scope,
        "quantum_scope": spec.quantum_scope,
        "quantum_applicability_scope": list(_quantum_access(role)),
        "quantum_algorithm_family_access": list(_quantum_access(role)),
        "quantum_parameter_family_access": list(_quantum_access(role)),
        "quantum_priority_forward_compatible": True,
        "owner_quantum_priority_supported": True,
        "owner_can_force_quantum_priority": True,
        "quantum_backend_artifact_created": False,
        "quantum_runtime_authority_created": False,
        "true_quantum_execution_created": False,
        "quantum_evidence_claim_created": False,
        "quantum_scoring_policy_reference": STATIC_FORWARD_REFERENCE_ONLY,
        "quantum_classical_arbitration_reference": STATIC_FORWARD_REFERENCE_ONLY,
        "runtime_scope": spec.runtime_scope,
        "live_scope": spec.live_scope,
        "dashboard_scope": spec.dashboard_scope,
        "source_evidence_scope": spec.source_scope,
        "connector_scope": spec.connector_scope,
        "atomicrows_scope": spec.atomicrows_scope,
        "fallback_behavior": spec.fallback_behavior,
        "escalation_behavior": spec.escalation_behavior,
        "final_qtt_internal_status": FINAL_STATUS,
    }


def build_registry(*, synthetic: bool = False) -> dict[str, Any]:
    registry = dict(TOP_CONST_EXPECTATIONS)
    if synthetic:
        registry["execution"] = "DISABLED"
        registry["mode"] = "SOURCE_REQUIRED"
    registry["agent_charters"] = [
        build_charter(role, synthetic=synthetic) for role in ROLE_ORDER
    ]
    return registry


REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "source_of_role_substance",
    "master_plan_followed_as_controlling_doctrine",
    "existing_pr_patterns_used_for_style_only",
    "pr64_is_scope_boundary_not_role_authority",
    "architecture_emphasis",
    "agent_role_count",
    "required_agent_role_count",
    "required_agent_roles_present_count",
    "missing_agent_role_count",
    "agents_with_master_plan_doctrine_terms_count",
    "agents_with_master_plan_derivation_summary_count",
    "agents_with_primary_duties_count",
    "agents_with_owned_surfaces_count",
    "agents_with_consumed_artifacts_count",
    "agents_with_emitted_artifacts_count",
    "agents_with_handoff_inputs_count",
    "agents_with_handoff_outputs_count",
    "agents_with_input_packets_count",
    "agents_with_output_packets_count",
    "agents_with_parameter_family_scope_count",
    "agents_with_algorithm_family_scope_count",
    "agents_with_quantum_scope_count",
    "agents_with_classical_scope_count",
    "agents_with_orchestration_relationship_count",
    "agents_with_risk_gate_relationship_count",
    "agents_with_execution_router_relationship_count",
    "agents_with_receipt_event_log_relationship_count",
    "agents_with_coverage_health_monitor_relationship_count",
    "agents_with_optimizer_arbitration_relationship_count",
    "agents_with_owner_override_supported_count",
    "agents_block_owner_override_count",
    "agents_may_approve_for_owner_count",
    "codex_may_approve_for_owner_count",
    "chatgpt_may_approve_for_owner_count",
    "qtt_agent_authority_over_owner_count",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "quantum_priority_forward_compatible",
    "owner_quantum_priority_supported",
    "owner_can_force_quantum_priority_count",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "profit_artifact_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
    "authority_boundary_all_false",
)


def _non_empty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_non_empty(item) for item in value)
    return value is not None


def build_report(registry: dict[str, Any]) -> dict[str, Any]:
    charters = registry.get("agent_charters")
    agents = charters if isinstance(charters, list) else []
    role_set = {agent.get("agent_role") for agent in agents if isinstance(agent, dict)}
    required_present = sum(1 for role in ROLE_ORDER if role in role_set)

    def count_non_empty(field: str) -> int:
        return sum(1 for agent in agents if isinstance(agent, dict) and _non_empty(agent.get(field)))

    artifact_false_fields = (
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "profit_artifact_created",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
        "quantum_evidence_claim_created",
    )
    report = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_role_substance": MASTER_PLAN.as_posix(),
        "master_plan_followed_as_controlling_doctrine": True,
        "existing_pr_patterns_used_for_style_only": True,
        "pr64_is_scope_boundary_not_role_authority": True,
        "architecture_emphasis": ARCHITECTURE_EMPHASIS,
        "agent_role_count": len(agents),
        "required_agent_role_count": len(ROLE_ORDER),
        "required_agent_roles_present_count": required_present,
        "missing_agent_role_count": len(ROLE_ORDER) - required_present,
        "agents_with_master_plan_doctrine_terms_count": count_non_empty("master_plan_doctrine_terms_used"),
        "agents_with_master_plan_derivation_summary_count": count_non_empty("master_plan_role_derivation_summary"),
        "agents_with_primary_duties_count": count_non_empty("primary_duties"),
        "agents_with_owned_surfaces_count": count_non_empty("owned_surfaces"),
        "agents_with_consumed_artifacts_count": count_non_empty("consumed_artifacts"),
        "agents_with_emitted_artifacts_count": count_non_empty("emitted_artifacts"),
        "agents_with_handoff_inputs_count": count_non_empty("handoff_inputs"),
        "agents_with_handoff_outputs_count": count_non_empty("handoff_outputs"),
        "agents_with_input_packets_count": count_non_empty("input_packet_types"),
        "agents_with_output_packets_count": count_non_empty("output_packet_types"),
        "agents_with_parameter_family_scope_count": count_non_empty("applicable_parameter_family_scopes"),
        "agents_with_algorithm_family_scope_count": count_non_empty("applicable_algorithm_family_scopes"),
        "agents_with_quantum_scope_count": count_non_empty("quantum_scope"),
        "agents_with_classical_scope_count": count_non_empty("classical_scope"),
        "agents_with_orchestration_relationship_count": count_non_empty("orchestration_spine_relationship"),
        "agents_with_risk_gate_relationship_count": count_non_empty("risk_gate_relationship"),
        "agents_with_execution_router_relationship_count": count_non_empty("execution_router_relationship"),
        "agents_with_receipt_event_log_relationship_count": count_non_empty("receipt_event_log_relationship"),
        "agents_with_coverage_health_monitor_relationship_count": count_non_empty("coverage_health_monitor_relationship"),
        "agents_with_optimizer_arbitration_relationship_count": count_non_empty("optimizer_arbitration_relationship"),
        "agents_with_owner_override_supported_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("owner_override_supported") is True
        ),
        "agents_block_owner_override_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("blocks_qtt_when_owner_override_present") is True
        ),
        "agents_may_approve_for_owner_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("may_approve_for_owner") is True
        ),
        "codex_may_approve_for_owner_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("codex_may_approve_for_owner") is True
        ),
        "chatgpt_may_approve_for_owner_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("chatgpt_may_approve_for_owner") is True
        ),
        "qtt_agent_authority_over_owner_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("qtt_agent_authority_over_owner") is True
        ),
        "quantum_forward_design_supported": registry.get("quantum_forward_design_supported") is True,
        "quantum_evidence_claim_created": registry.get("quantum_evidence_claim_created") is True,
        "quantum_priority_forward_compatible": registry.get("quantum_priority_forward_compatible") is True
        and all(isinstance(agent, dict) and agent.get("quantum_priority_forward_compatible") is True for agent in agents),
        "owner_quantum_priority_supported": registry.get("owner_quantum_priority_supported") is True
        and all(isinstance(agent, dict) and agent.get("owner_quantum_priority_supported") is True for agent in agents),
        "owner_can_force_quantum_priority_count": sum(
            1 for agent in agents if isinstance(agent, dict) and agent.get("owner_can_force_quantum_priority") is True
        ),
        "runtime_artifact_created": registry.get("runtime_artifact_created") is True,
        "live_artifact_created": registry.get("live_artifact_created") is True,
        "order_artifact_created": registry.get("order_artifact_created") is True,
        "source_acceptance_artifact_created": registry.get("source_acceptance_artifact_created") is True,
        "connector_binding_artifact_created": registry.get("connector_binding_artifact_created") is True,
        "runtime_resolver_snapshot_created": registry.get("runtime_resolver_snapshot_created") is True,
        "replay_execution_created": registry.get("replay_execution_created") is True,
        "paper_execution_created": registry.get("paper_execution_created") is True,
        "quantum_backend_artifact_created": registry.get("quantum_backend_artifact_created") is True,
        "profit_artifact_created": registry.get("profit_artifact_created") is True,
        "bundle_file_present": CANONICAL_BUNDLE.exists() or registry.get("bundle_file_present") is True,
        "bundle_sha_present": CANONICAL_BUNDLE_SHA.exists() or registry.get("bundle_sha_present") is True,
        "uses_pr_number_as_authority": registry.get("uses_pr_number_as_authority") is True
        or _uses_pr_number_as_authority_values(registry),
        "final_ready": registry.get("final_ready") is True,
        "authority_boundary_all_false": False,
    }
    report["authority_boundary_all_false"] = (
        all(report[field] is False for field in artifact_false_fields)
        and report["agents_block_owner_override_count"] == 0
        and report["agents_may_approve_for_owner_count"] == 0
        and report["codex_may_approve_for_owner_count"] == 0
        and report["chatgpt_may_approve_for_owner_count"] == 0
        and report["qtt_agent_authority_over_owner_count"] == 0
    )
    return report


def build_schema() -> dict[str, Any]:
    string = {"type": "string", "minLength": 1}
    string_array = {"type": "array", "minItems": 1, "items": string}
    charter_properties: dict[str, Any] = {}
    for field in CHARTER_FIELDS:
        if field == "agent_role":
            charter_properties[field] = {"enum": list(ROLE_ORDER)}
        elif field == "agent_role_id":
            charter_properties[field] = {"enum": [ROLE_IDS[role] for role in ROLE_ORDER]}
        elif field in ARRAY_FIELDS:
            charter_properties[field] = string_array
        elif field in TRUE_CHARTER_FLAGS:
            charter_properties[field] = {"const": True}
        elif field in FALSE_CHARTER_FLAGS:
            charter_properties[field] = {"const": False}
        elif field == "owner_override_satisfaction_basis":
            charter_properties[field] = {"const": OWNER_OVERRIDE_SATISFACTION_BASIS}
        elif field in {
            "quantum_scoring_policy_reference",
            "quantum_classical_arbitration_reference",
        }:
            charter_properties[field] = {"const": STATIC_FORWARD_REFERENCE_ONLY}
        elif field == "final_qtt_internal_status":
            charter_properties[field] = {"const": FINAL_STATUS}
        else:
            charter_properties[field] = string

    report_properties: dict[str, Any] = {}
    for field in REPORT_FIELDS:
        if field == "report_type":
            report_properties[field] = {"const": REPORT_TYPE}
        elif field == "deterministic_output":
            report_properties[field] = {"const": True}
        elif field == "generated_at_utc":
            report_properties[field] = {"const": DETERMINISTIC_GENERATED_AT}
        elif field == "source_of_role_substance":
            report_properties[field] = {"const": MASTER_PLAN.as_posix()}
        elif field == "architecture_emphasis":
            report_properties[field] = {"const": ARCHITECTURE_EMPHASIS}
        elif field in {
            "master_plan_followed_as_controlling_doctrine",
            "existing_pr_patterns_used_for_style_only",
            "pr64_is_scope_boundary_not_role_authority",
            "quantum_forward_design_supported",
            "quantum_priority_forward_compatible",
            "owner_quantum_priority_supported",
            "authority_boundary_all_false",
        }:
            report_properties[field] = {"type": "boolean"}
        elif field in {
            "quantum_evidence_claim_created",
            "runtime_artifact_created",
            "live_artifact_created",
            "order_artifact_created",
            "source_acceptance_artifact_created",
            "connector_binding_artifact_created",
            "runtime_resolver_snapshot_created",
            "replay_execution_created",
            "paper_execution_created",
            "quantum_backend_artifact_created",
            "profit_artifact_created",
            "bundle_file_present",
            "bundle_sha_present",
            "uses_pr_number_as_authority",
            "final_ready",
        }:
            report_properties[field] = {"type": "boolean"}
        else:
            report_properties[field] = {"type": "integer"}

    properties: dict[str, Any] = {}
    for field in TOP_FIELDS:
        if field == "agent_charters":
            properties[field] = {
                "type": "array",
                "minItems": len(ROLE_ORDER),
                "maxItems": len(ROLE_ORDER),
                "uniqueItems": True,
                "items": {"$ref": "#/$defs/agent_charter"},
            }
        elif field in TOP_CONST_EXPECTATIONS:
            properties[field] = {"const": TOP_CONST_EXPECTATIONS[field]}
        else:
            properties[field] = string
    properties["execution"] = {"const": "DISABLED"}
    properties["mode"] = {"const": "SOURCE_REQUIRED"}

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://qtt.local/schemas/agents/qtt_agent_role_operating_charter_registry.schema.json",
        "title": "QTT Agent Role Operating Charter Registry",
        "description": (
            "Static deterministic institutional QTT agent operating-charter registry "
            "schema. It defines role duties, handoffs, owner authority, quantum-forward "
            "compatibility, and no-evidence/no-runtime boundaries."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": list(TOP_FIELDS),
        "properties": properties,
        "$defs": {
            "agent_role": {"enum": list(ROLE_ORDER)},
            "agent_role_id": {"enum": [ROLE_IDS[role] for role in ROLE_ORDER]},
            "agent_charter": {
                "type": "object",
                "additionalProperties": False,
                "required": list(CHARTER_FIELDS),
                "properties": charter_properties,
            },
            "agent_role_operating_charter_report": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REPORT_FIELDS),
                "properties": report_properties,
            },
        },
    }


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def serialize_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_json(value), encoding="utf-8")


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is invalid: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError(f"registry must contain an object: {path}")
        return value
    return load_yaml_subset(path)


def _load_registry(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"registry file is missing: {path}"]
    try:
        return load_registry(path), []
    except (json.JSONDecodeError, RegistryParseError, ValueError) as exc:
        return None, [f"registry file is invalid: {path}: {exc}"]


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: Sequence[str],
    label: str,
) -> list[str]:
    expected = set(expected_fields)
    failures: list[str] = []
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _walk_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return values
    return [value]


def _uses_pr_number_as_authority_values(value: Any) -> bool:
    for item in _walk_values(value):
        if isinstance(item, str) and PR_NUMBER_PATTERN.search(item):
            return True
    return False


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(TOP_FIELDS):
        failures.append("schema.required must match top-level registry fields")
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return failures + ["schema.$defs must be an object"]
    role_def = defs.get("agent_role")
    if not isinstance(role_def, dict) or role_def.get("enum") != list(ROLE_ORDER):
        failures.append("schema.$defs.agent_role must contain exact role order")
    role_id_def = defs.get("agent_role_id")
    expected_ids = [ROLE_IDS[role] for role in ROLE_ORDER]
    if not isinstance(role_id_def, dict) or role_id_def.get("enum") != expected_ids:
        failures.append("schema.$defs.agent_role_id must contain exact role ids")
    charter_def = defs.get("agent_charter")
    if not isinstance(charter_def, dict):
        failures.append("schema.$defs.agent_charter must be an object")
    elif charter_def.get("required") != list(CHARTER_FIELDS):
        failures.append("schema.$defs.agent_charter.required must match charter fields")
    report_def = defs.get("agent_role_operating_charter_report")
    if not isinstance(report_def, dict):
        failures.append("schema.$defs.agent_role_operating_charter_report must be an object")
    elif report_def.get("required") != list(REPORT_FIELDS):
        failures.append("schema report required fields must match report fields")
    return failures


def _validate_top_level(
    value: dict[str, Any],
    *,
    label: str,
    schema: dict[str, Any] | None,
) -> list[str]:
    expected_fields = (
        (*TOP_FIELDS, *FIXTURE_EXTRA_FIELDS) if label == "fixture" else TOP_FIELDS
    )
    failures = _require_exact_fields(value, expected_fields, label)
    for field, expected in TOP_CONST_EXPECTATIONS.items():
        if value.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected!r}")
    if label == "fixture":
        if value.get("mode") != "SOURCE_REQUIRED":
            failures.append("fixture.mode must be SOURCE_REQUIRED")
        if value.get("execution") != "DISABLED":
            failures.append("fixture.execution must be DISABLED")
    if schema is not None:
        failures.extend(validate_json_schema_subset(value, schema))
    return failures


def _validate_charter(charter: dict[str, Any], *, index: int, role: str) -> list[str]:
    label = f"agent_charters[{index}]"
    failures = _require_exact_fields(charter, CHARTER_FIELDS, label)
    for field in ARRAY_FIELDS:
        value = charter.get(field)
        if not isinstance(value, list) or not value:
            failures.append(f"{label}.{field} must be a non-empty array")
        elif not all(isinstance(item, str) and item.strip() for item in value):
            failures.append(f"{label}.{field} must contain only non-empty strings")
    for field in CHARTER_FIELDS:
        if field in ARRAY_FIELDS or field in TRUE_CHARTER_FLAGS or field in FALSE_CHARTER_FLAGS:
            continue
        value = charter.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{label}.{field} must be a non-empty string")
    for field in TRUE_CHARTER_FLAGS:
        if charter.get(field) is not True:
            failures.append(f"{label}.{field} must be true")
    for field in FALSE_CHARTER_FLAGS:
        if charter.get(field) is not False:
            failures.append(f"{label}.{field} must be false")
    if charter.get("owner_override_satisfaction_basis") != OWNER_OVERRIDE_SATISFACTION_BASIS:
        failures.append(f"{label}.owner_override_satisfaction_basis is invalid")
    if charter.get("quantum_scoring_policy_reference") != STATIC_FORWARD_REFERENCE_ONLY:
        failures.append(f"{label}.quantum_scoring_policy_reference must be static")
    if charter.get("quantum_classical_arbitration_reference") != STATIC_FORWARD_REFERENCE_ONLY:
        failures.append(f"{label}.quantum_classical_arbitration_reference must be static")
    if charter.get("final_qtt_internal_status") != FINAL_STATUS:
        failures.append(f"{label}.final_qtt_internal_status is invalid")

    affirmative_count = sum(
        len(charter.get(field, []))
        for field in (
            "primary_duties",
            "secondary_duties",
            "owned_surfaces",
            "consumed_artifacts",
            "emitted_artifacts",
            "handoff_inputs",
            "handoff_outputs",
        )
        if isinstance(charter.get(field), list)
    )
    prohibition_count = len(charter.get("forbidden_decision_authority", []))
    if affirmative_count <= prohibition_count:
        failures.append(f"{label} must contain more affirmative role content than prohibitions")
    if len(charter.get("primary_duties", [])) < 1:
        failures.append(f"{label}.primary_duties must contain affirmative duties")

    for field in RELATIONSHIP_FIELDS:
        if not isinstance(charter.get(field), str) or not charter[field].strip():
            failures.append(f"{label}.{field} must describe architecture relationship")

    quantum_fields = (
        "quantum_applicability_scope",
        "quantum_algorithm_family_access",
        "quantum_parameter_family_access",
    )
    if role in QUANTUM_RELEVANT_ROLES:
        for field in quantum_fields:
            values = set(charter.get(field, []))
            missing = sorted(set(QUANTUM_COMPATIBILITY_CLASSES) - values)
            if missing:
                failures.append(f"{label}.{field} missing quantum classes: {', '.join(missing)}")
    if role in OWNER_FORCE_QUANTUM_REQUIRED_ROLES and charter.get("owner_can_force_quantum_priority") is not True:
        failures.append(f"{label}.owner_can_force_quantum_priority must be true for {role}")

    direct_path_text = json.dumps(charter, sort_keys=True).lower()
    if "random parameter selection allowed" in direct_path_text:
        failures.append(f"{label} must not allow random parameter selection")
    if "single-parameter direct trade path allowed" in direct_path_text:
        failures.append(f"{label} must not allow single-parameter direct trade paths")
    return failures


def _validate_charters(value: dict[str, Any], *, label: str) -> list[str]:
    charters = value.get("agent_charters")
    if not isinstance(charters, list):
        return [f"{label}.agent_charters must be a list"]
    failures: list[str] = []
    if len(charters) != len(ROLE_ORDER):
        failures.append(f"{label}.agent_charters must contain exactly {len(ROLE_ORDER)} charters")
    roles: list[str] = []
    ids: list[str] = []
    for index, expected_role in enumerate(ROLE_ORDER):
        if index >= len(charters):
            continue
        charter = charters[index]
        if not isinstance(charter, dict):
            failures.append(f"{label}.agent_charters[{index}] must be an object")
            continue
        role = charter.get("agent_role")
        role_id = charter.get("agent_role_id")
        roles.append(role)
        ids.append(role_id)
        if role != expected_role:
            failures.append(f"{label}.agent_charters[{index}].agent_role must be {expected_role}")
        if role_id != ROLE_IDS[expected_role]:
            failures.append(f"{label}.agent_charters[{index}].agent_role_id must be {ROLE_IDS[expected_role]}")
        failures.extend(_validate_charter(charter, index=index, role=expected_role))
    if len(set(roles)) != len(roles):
        failures.append(f"{label}.agent_charters must have unique agent_role values")
    if len(set(ids)) != len(ids):
        failures.append(f"{label}.agent_charters must have unique agent_role_id values")
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]
    report_schema = defs.get("agent_role_operating_charter_report")
    if not isinstance(report_schema, dict):
        return ["schema report definition is missing"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_counts_25 = (
        "agent_role_count",
        "required_agent_role_count",
        "required_agent_roles_present_count",
        "agents_with_master_plan_doctrine_terms_count",
        "agents_with_master_plan_derivation_summary_count",
        "agents_with_primary_duties_count",
        "agents_with_owned_surfaces_count",
        "agents_with_consumed_artifacts_count",
        "agents_with_emitted_artifacts_count",
        "agents_with_handoff_inputs_count",
        "agents_with_handoff_outputs_count",
        "agents_with_input_packets_count",
        "agents_with_output_packets_count",
        "agents_with_parameter_family_scope_count",
        "agents_with_algorithm_family_scope_count",
        "agents_with_quantum_scope_count",
        "agents_with_classical_scope_count",
        "agents_with_orchestration_relationship_count",
        "agents_with_risk_gate_relationship_count",
        "agents_with_execution_router_relationship_count",
        "agents_with_receipt_event_log_relationship_count",
        "agents_with_coverage_health_monitor_relationship_count",
        "agents_with_optimizer_arbitration_relationship_count",
        "agents_with_owner_override_supported_count",
    )
    for field in expected_counts_25:
        if report.get(field) != len(ROLE_ORDER):
            failures.append(f"report.{field} must be {len(ROLE_ORDER)}")
    zero_fields = (
        "missing_agent_role_count",
        "agents_block_owner_override_count",
        "agents_may_approve_for_owner_count",
        "codex_may_approve_for_owner_count",
        "chatgpt_may_approve_for_owner_count",
        "qtt_agent_authority_over_owner_count",
    )
    for field in zero_fields:
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")
    true_fields = (
        "deterministic_output",
        "master_plan_followed_as_controlling_doctrine",
        "existing_pr_patterns_used_for_style_only",
        "pr64_is_scope_boundary_not_role_authority",
        "quantum_forward_design_supported",
        "quantum_priority_forward_compatible",
        "owner_quantum_priority_supported",
        "authority_boundary_all_false",
    )
    for field in true_fields:
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    false_fields = (
        "quantum_evidence_claim_created",
        "runtime_artifact_created",
        "live_artifact_created",
        "order_artifact_created",
        "source_acceptance_artifact_created",
        "connector_binding_artifact_created",
        "runtime_resolver_snapshot_created",
        "replay_execution_created",
        "paper_execution_created",
        "quantum_backend_artifact_created",
        "profit_artifact_created",
        "bundle_sha_present",
        "uses_pr_number_as_authority",
        "final_ready",
    )
    for field in false_fields:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("owner_can_force_quantum_priority_count", 0) < len(OWNER_FORCE_QUANTUM_REQUIRED_ROLES):
        failures.append("report.owner_can_force_quantum_priority_count must be at least 8")
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must use deterministic sentinel")
    if report.get("source_of_role_substance") != MASTER_PLAN.as_posix():
        failures.append("report.source_of_role_substance must point to master plan")
    if report.get("architecture_emphasis") != ARCHITECTURE_EMPHASIS:
        failures.append("report.architecture_emphasis is invalid")
    if report != json.loads(serialize_json(report)):
        failures.append("report serialization must be deterministic")
    return failures


def _master_plan_has_no_diff(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--", MASTER_PLAN.as_posix()],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return [f"git diff for master plan failed: {completed.stderr.strip()}"]
    if completed.stdout.strip():
        return [f"{MASTER_PLAN.as_posix()} must have no diff"]
    return []


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    registry_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json(root / schema_path)
    registry, registry_failures = _load_registry(root / registry_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(registry_failures)
    failures.extend(fixture_failures)

    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if registry is not None:
        failures.extend(_validate_top_level(registry, label="registry", schema=schema))
        failures.extend(_validate_charters(registry, label="registry"))
    if fixture is not None:
        failures.extend(_validate_top_level(fixture, label="fixture", schema=schema))
        failures.extend(_validate_charters(fixture, label="fixture"))

    failures.extend(
        validate_current_atomicrows_bundle_state(
            root,
            label="QTT agent role operating charter registry",
        )
    )
    failures.extend(_master_plan_has_no_diff(root))

    report = build_report(registry or {})
    second_report = build_report(registry or {})
    if report != second_report:
        failures.append("generated operating charter report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append("final mode incomplete: static charter registry is not production-ready")

    if output_path is not None and not failures:
        write_json(root / output_path, report)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def write_static_artifacts(repo_root: pathlib.Path) -> None:
    root = repo_root.resolve()
    write_json(root / DEFAULT_SCHEMA, build_schema())
    write_json(root / DEFAULT_REGISTRY, build_registry(synthetic=False))
    write_json(root / DEFAULT_FIXTURE, build_registry(synthetic=True))
    report = build_report(build_registry(synthetic=False))
    write_json(root / DEFAULT_REPORT, report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev", "final"], default="dev")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    parser.add_argument("--write-static-artifacts", action="store_true")
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    if args.write_static_artifacts:
        write_static_artifacts(repo_root)

    result = validate(
        mode=args.mode,
        repo_root=repo_root,
        schema_path=pathlib.Path(args.schema),
        registry_path=pathlib.Path(args.registry),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"agents={report.get('agent_role_count', 0)} "
            f"owner_force_quantum={report.get('owner_can_force_quantum_priority_count', 0)} "
            f"final_ready={report.get('final_ready', None)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
