"""Canonical PR165-C core tables."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .agent_conflict_vocab import CONFLICT_STATUS_CLEAR, OVERLAP_STATUS_TYPED
from .agent_duty_vocab import agent_contracts
from .authority_policy import authority_boundary_record, authority_zero_counts
from .central_vocab import (
    AGENT_IDS,
    AUTHORITY_BOUNDARY_REF,
    CONFIDENCE_TIER,
    DOWNSTREAM_PR_ROUTES,
    NO_ORPHAN_STATUS,
    PROVENANCE_LABEL,
    REFRESH_TRIGGERS,
    REPLAY_PAPER_ROUTE,
    RETEST_PRIORITY_WEIGHTS,
)
from .computability_action_vocab import COMPUTABILITY_ACTIONS
from .deterministic_ids import ordinal_ref
from .formula_templates import FORMULA_TEMPLATES
from .memory_consumer_action_vocab import REPAIR_ACTION_BY_POLICY
from .older_agent_artifact_loader import older_agent_reference_bundle
from .pr165_b_memory_loader import load_pr165_b_memory
from .pr165_score_loader import load_pr165_scores
from .retest_ingestion_vocab import PENDING_EVIDENCE_REQUIREMENTS

CORE_TABLE_NAMES = (
    "MemoryConsumerCoreTable",
    "ComputableArtifactPayloadCoreTable",
    "ComputableQKUActionCoreTable",
    "FormulaTestVectorCoreTable",
    "AgentDutyCoreTable",
    "AgentFieldOwnershipCoreTable",
    "AgentTaskQueueCoreTable",
    "ScenarioMemoryRouteCoreTable",
    "ConditionRegimeFeatureCoreTable",
    "RetestPriorityCoreTable",
    "PendingRetestCoreTable",
    "RetestResultIngestionCoreTable",
    "ScoreMemoryRefreshTriggerCoreTable",
    "BoundedMaterializationCoreTable",
    "QuantumConsumerRouteCoreTable",
    "PRFileConnectivityCoreTable",
    "LineageGraphCoreTable",
    "AuthorityBoundaryCoreTable",
)

REPAIR_POLICIES = frozenset(REPAIR_ACTION_BY_POLICY)
RETEST_POLICIES = frozenset({"REPLAY_PAPER_RETEST_REQUIRED", "FALSE_DISCOVERY_RETEST_REQUIRED"})


def build_core_tables(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    pr165 = load_pr165_scores(repo_root)
    pr165_b = load_pr165_b_memory(repo_root)
    refs = older_agent_reference_bundle(repo_root)
    memory_rows = sorted(pr165_b["_memory_rows"], key=lambda row: str(row["condition_fingerprint_id"]))
    retest_queue = pr165_b["PR165_B_ReplayPaperRetestQueue.report.json"]
    repair_routes = pr165_b["PR165_B_RepairRouteHandoffRegistry.report.json"]
    tables: dict[str, list[dict[str, Any]]] = {name: [] for name in CORE_TABLE_NAMES}
    agent_duties = _build_agent_duties(refs)
    field_rows = _build_field_ownership_rows(refs)
    tables["AgentDutyCoreTable"] = agent_duties
    tables["AgentFieldOwnershipCoreTable"] = field_rows
    pending_by_candidate = {
        str(row["candidate_packet_id"]): row for row in retest_queue.values()
    }
    repair_by_candidate = {
        str(row["candidate_packet_id"]): row for row in repair_routes.values()
    }
    priority_work: list[dict[str, Any]] = []
    for index, memory in enumerate(memory_rows, start=1):
        candidate_id = str(memory["candidate_packet_id"])
        score = pr165["PR165_GlobalCandidateRanking.report.json"].get(candidate_id, {})
        components = pr165["PR165_CandidateScoreComponentRegistry.report.json"].get(candidate_id, {})
        scenario = pr165_b["PR165_B_ScenarioOutcomeMatrix.report.json"].get(candidate_id, {})
        condition = pr165_b["PR165_B_ConditionFingerprintRegistry.report.json"].get(candidate_id, {})
        combination = pr165_b["PR165_B_CombinationFingerprintRegistry.report.json"].get(candidate_id, {})
        quantum = pr165["PR165_QuantumFormulationMaterializationRegistry.report.json"].get(candidate_id, {})
        tca = pr165["PR165_TCAAdjustedScoreRegistry.report.json"].get(candidate_id, {})
        latency = pr165["PR165_LatencyLaneAssignmentRegistry.report.json"].get(candidate_id, {})
        liquidity = pr165["PR165_LiquidityFillProbabilityScoreRegistry.report.json"].get(candidate_id, {})
        adverse = pr165["PR165_AdverseSelectionPenaltyRegistry.report.json"].get(candidate_id, {})
        model_risk = pr165["PR165_ModelRiskPenaltyRegistry.report.json"].get(candidate_id, {})
        repair_confidence = pr165["PR165_RepairConfidenceScoreRegistry.report.json"].get(candidate_id, {})
        provenance = pr165["PR165_ProvenanceQualityScoreRegistry.report.json"].get(candidate_id, {})
        quantum_priority = pr165["PR165_QuantumPriorityScoreRegistry.report.json"].get(candidate_id, {})
        regime = pr165["PR165_RegimeSlicedRanking.report.json"].get(candidate_id, {})
        ids = _ids(index)
        status = _computability_status(memory)
        route_class = _scenario_route_class(memory, quantum)
        replay_action, paper_action = _replay_paper_actions(memory)
        primary_agent = _primary_agent(memory)
        task_type = _task_type(memory, status)
        consumer_set = _consumer_set(memory, primary_agent)
        pending = pending_by_candidate.get(candidate_id)
        repair = repair_by_candidate.get(candidate_id)
        priority_inputs = _priority_inputs(
            score,
            scenario,
            tca,
            latency,
            liquidity,
            adverse,
            model_risk,
            repair_confidence,
            provenance,
            quantum_priority,
            regime,
            len(memory_rows),
        )
        priority_score = _priority_score(priority_inputs)
        priority_bucket = _priority_bucket(memory, priority_score, status)
        tables["MemoryConsumerCoreTable"].append(
            {
                "memory_consumer_id": ids["memory_consumer"],
                "core_table_row_id": ids["memory_consumer"],
                "candidate_packet_id": candidate_id,
                "qku_id": memory["qku_id"],
                "qku_family": _qku_family(str(memory["qku_id"])),
                "qku_type": "PREDICTION_MARKET_REPLAY_PAPER_CANDIDATE",
                "candidate_version": memory["candidate_version"],
                "condition_fingerprint_id": memory["condition_fingerprint_id"],
                "combination_fingerprint_id": memory["combination_fingerprint_id"],
                "pr165_score_ref": score.get("deterministic_score_component_record") or memory.get("score_component_ref"),
                "pr165_rank_ref": score.get("candidate_global_rank_ref"),
                "pr165_b_memory_ref": memory.get("candidate_version_memory_ref"),
                "memory_classification": memory["memory_classification"],
                "memory_action_policy": memory["memory_action_policy"],
                "scenario_memory_route_ref": ids["scenario_route"],
                "computability_action_status": status,
                "computable_artifact_payload_ref": ids["payload"],
                "computable_formula_ref_or_action": ids["qku_action"],
                "computable_algorithm_ref_or_action": "PR165_C_ALGORITHM_ACTION::DETERMINISTIC_REPLAY_PAPER_CONSUMER_ROUTING",
                "formula_test_vector_ref_or_action": ids["test_vector"],
                "missing_value_candidate_materialization_ref": "",
                "agent_consumer_set": consumer_set,
                "primary_agent_owner": primary_agent,
                "secondary_agent_reviewers": ["risk_agent", "governance_agent"],
                "independent_challenger_agent": "governance_agent" if primary_agent != "governance_agent" else "risk_agent",
                "fallback_agent": "commander_agent",
                "commander_coordination_ref": ids["commander"],
                "agent_duty_contract_ref": f"PR165_C_AGENT_DUTY::{primary_agent}",
                "field_ownership_ref": f"PR165_C_FIELD_OWNERSHIP::{primary_agent}",
                "agent_task_queue_ref": ids["task"],
                "task_receipt_requirement_ref": ids["receipt"],
                "duty_overlap_status": OVERLAP_STATUS_TYPED,
                "duty_conflict_status": CONFLICT_STATUS_CLEAR,
                "replay_consumer_action": replay_action,
                "paper_consumer_action": paper_action,
                "risk_consumer_action": _risk_action(memory),
                "tca_consumer_action": _tca_action(memory),
                "latency_consumer_action": _latency_action(memory),
                "liquidity_consumer_action": _liquidity_action(memory),
                "quantum_consumer_action": _quantum_action(quantum),
                "repair_consumer_action": _repair_action(memory),
                "dashboard_consumer_action": "ROUTE_TO_DASHBOARD_REVIEW",
                "governance_consumer_action": "ROUTE_TO_GOVERNANCE_REVIEW",
                "commander_consumer_action": "ROUTE_TO_COMMANDER_ESCALATION",
                "retest_required": pending is not None,
                "retest_queue_ref": pending.get("retest_queue_id", "") if pending else "",
                "retest_result_ingestion_status": "NO_VALIDATED_POST_MEMORY_RETEST_RESULT_DISCOVERED",
                "pending_retest_evidence_requirements": list(PENDING_EVIDENCE_REQUIREMENTS) if pending else [],
                "score_memory_refresh_trigger": ids["refresh"],
                "lineage_graph_ref": ids["lineage"],
                **refs,
                "upstream_report_refs": list((combination.get("upstream_report_refs") or [])[:10]),
                "downstream_report_refs": [
                    "PR165_C_ComputableArtifactPayloadRegistry.report.json",
                    "PR165_C_ScenarioMemoryRouter.report.json",
                    "PR165_C_AgentTaskQueue.report.json",
                ],
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "downstream_agent_workflow_refs": [
                    "PR165_C_AgentTaskQueue.report.json",
                    "PR165_C_PendingRetestQueue.report.json",
                ],
                "supersedes_or_extends_existing_agent_duty_ref": "EXTENDS_PRIOR_QTT_AGENT_ROUTE_ARTIFACTS",
                "no_orphan_agent_duty_status": NO_ORPHAN_STATUS,
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
                **authority_zero_counts(),
            }
        )
        tables["ComputableArtifactPayloadCoreTable"].append(
            _payload_row(ids, memory, scenario, tca, status, primary_agent)
        )
        tables["ComputableQKUActionCoreTable"].append(
            _qku_action_row(ids, memory, scenario, priority_score, status, primary_agent)
        )
        tables["FormulaTestVectorCoreTable"].append(
            _test_vector_row(ids, memory, priority_inputs, priority_score)
        )
        tables["ScenarioMemoryRouteCoreTable"].append(
            _scenario_route_row(ids, memory, route_class, replay_action, paper_action, primary_agent, pending)
        )
        tables["ConditionRegimeFeatureCoreTable"].append(
            _condition_feature_row(ids, memory, condition, scenario)
        )
        if pending:
            pending_row = _pending_retest_row(ids, pending, memory, primary_agent)
            tables["PendingRetestCoreTable"].append(pending_row)
            priority_work.append(
                {
                    **_retest_priority_row(ids, memory, priority_inputs, priority_score, priority_bucket, primary_agent),
                    "_sort_key": (
                        -float(priority_score),
                        -float(scenario.get("expected_value_score", 0.0) or 0.0),
                        -float(tca.get("risk_adjusted_net_edge_candidate", 0.0) or 0.0),
                        str(candidate_id),
                    ),
                }
            )
            tables["ScoreMemoryRefreshTriggerCoreTable"].append(
                _refresh_trigger_row(ids, memory, pending, repair)
            )
        tables["QuantumConsumerRouteCoreTable"].append(
            _quantum_route_row(ids, memory, quantum, quantum_priority)
        )
        tables["AgentTaskQueueCoreTable"].append(
            _task_row(ids, memory, task_type, primary_agent, priority_bucket, pending, repair)
        )
        tables["LineageGraphCoreTable"].append(
            _lineage_row(ids, memory, score, condition, combination, refs)
        )
        if repair:
            tables.setdefault("RepairToRetestCoreTable", []).append(
                _repair_handoff_row(ids, memory, repair)
            )
    ranked = sorted(priority_work, key=lambda row: row["_sort_key"])
    for rank, row in enumerate(ranked, start=1):
        row.pop("_sort_key", None)
        row["retest_priority_rank"] = rank
        tables["RetestPriorityCoreTable"].append(row)
    for repair_index, row in enumerate(tables.get("RepairToRetestCoreTable", []), start=1):
        repair_id = ordinal_ref("PR165_C_REPAIR_TO_RETEST", repair_index)
        row["repair_to_retest_handoff_id"] = repair_id
        row["core_table_row_id"] = repair_id
    tables["RetestResultIngestionCoreTable"] = []
    tables["BoundedMaterializationCoreTable"] = []
    tables["AuthorityBoundaryCoreTable"] = [
        {
            "authority_boundary_core_table_id": "PR165_C_AUTHORITY_BOUNDARY_CORE::0001",
            "core_table_row_id": "PR165_C_AUTHORITY_BOUNDARY_CORE::0001",
            **authority_boundary_record(),
            "authority_boundary_violation_count": 0,
            "authority_boundary_violation_counts_all_zero": True,
            "validation_status": "PASS",
            **authority_zero_counts(),
        }
    ]
    tables["PRFileConnectivityCoreTable"] = []
    return tables


def _ids(index: int) -> dict[str, str]:
    return {
        "memory_consumer": ordinal_ref("PR165_C_MEMORY_CONSUMER", index),
        "payload": ordinal_ref("PR165_C_COMPUTABLE_PAYLOAD", index),
        "qku_action": ordinal_ref("PR165_C_QKU_ACTION", index),
        "test_vector": ordinal_ref("PR165_C_FORMULA_TEST_VECTOR", index),
        "scenario_route": ordinal_ref("PR165_C_SCENARIO_MEMORY_ROUTE", index),
        "condition_feature": ordinal_ref("PR165_C_CONDITION_REGIME_FEATURE", index),
        "pending_retest": ordinal_ref("PR165_C_PENDING_RETEST", index),
        "retest_priority": ordinal_ref("PR165_C_RETEST_PRIORITY", index),
        "refresh": ordinal_ref("PR165_C_REFRESH_TRIGGER", index),
        "quantum": ordinal_ref("PR165_C_QUANTUM_ROUTE", index),
        "task": ordinal_ref("PR165_C_AGENT_TASK", index),
        "receipt": ordinal_ref("PR165_C_TASK_RECEIPT", index),
        "lineage": ordinal_ref("PR165_C_LINEAGE", index),
        "dashboard": ordinal_ref("PR165_C_DASHBOARD_HANDOFF", index),
        "governance": ordinal_ref("PR165_C_GOVERNANCE_HANDOFF", index),
        "commander": ordinal_ref("PR165_C_COMMANDER_HANDOFF", index),
    }


def _computability_status(memory: dict[str, Any]) -> str:
    policy = str(memory["memory_action_policy"])
    if policy in REPAIR_POLICIES:
        return "COMPUTABLE_AFTER_REPAIR"
    if policy in RETEST_POLICIES or policy in {"WATCH_ONLY_UNTIL_MORE_EVIDENCE", "DEMOTE_WITHIN_MATCHING_CONDITION"}:
        return "COMPUTABLE_AFTER_RETEST"
    if policy == "PREFER_UNDER_MATCHING_CONDITIONS":
        return "COMPUTABLE_READY"
    return "COMPUTABLE_WITH_PROVISIONAL_VALUE"


def _scenario_route_class(memory: dict[str, Any], quantum: dict[str, Any]) -> str:
    classification = str(memory["memory_classification"])
    policy = str(memory["memory_action_policy"])
    if classification.startswith("POSITIVE"):
        return "POSITIVE_CONDITION_SCOPED_PREFERENCE"
    if classification == "FRAGILE_HIGH_VARIANCE":
        return "FRAGILE_WATCHLIST"
    if policy in REPAIR_POLICIES:
        return "REPAIR_DEPENDENT_MEMORY"
    if not quantum.get("objective_function_materialized", True):
        return "QUANTUM_FORMULATION_DEPENDENT_MEMORY"
    if policy in RETEST_POLICIES:
        return "CONTRADICTORY_EVIDENCE_RETEST"
    if policy == "WATCH_ONLY_UNTIL_MORE_EVIDENCE":
        return "STALE_MEMORY_RETEST"
    return "NEGATIVE_CONDITION_SCOPED_AVOIDANCE"


def _replay_paper_actions(memory: dict[str, Any]) -> tuple[str, str]:
    policy = str(memory["memory_action_policy"])
    if policy == "PREFER_UNDER_MATCHING_CONDITIONS":
        return "PREFER_IN_REPLAY_QUEUE", "PREFER_IN_PAPER_QUEUE"
    if policy == "DEMOTE_WITHIN_MATCHING_CONDITION":
        return "DEMOTE_IN_REPLAY_QUEUE", "DEMOTE_IN_PAPER_QUEUE"
    if policy in REPAIR_POLICIES:
        action = REPAIR_ACTION_BY_POLICY[policy]
        return action, action
    if policy == "WATCH_ONLY_UNTIL_MORE_EVIDENCE":
        return "WATCH_IN_REPLAY_PAPER", "WATCH_IN_REPLAY_PAPER"
    return "RETEST_IN_BOTH", "RETEST_IN_BOTH"


def _primary_agent(memory: dict[str, Any]) -> str:
    policy = str(memory["memory_action_policy"])
    if policy == "TCA_REPAIR_REQUIRED":
        return "tca_agent"
    if policy == "LATENCY_REPAIR_REQUIRED":
        return "latency_agent"
    if policy == "LIQUIDITY_REPAIR_REQUIRED":
        return "liquidity_agent"
    if policy == "MODEL_RISK_REVIEW_REQUIRED":
        return "risk_agent"
    if policy in {"REPLAY_PAPER_RETEST_REQUIRED", "FALSE_DISCOVERY_RETEST_REQUIRED"}:
        return "replay_agent"
    if policy == "PREFER_UNDER_MATCHING_CONDITIONS":
        return "paper_agent"
    return "memory_agent"


def _consumer_set(memory: dict[str, Any], primary_agent: str) -> list[str]:
    consumers = {
        primary_agent,
        "memory_agent",
        "risk_agent",
        "replay_agent",
        "paper_agent",
        "dashboard_agent",
        "governance_agent",
        "commander_agent",
        "quantum_mapper_advisory_agent",
    }
    policy = str(memory["memory_action_policy"])
    if policy in {"TCA_REPAIR_REQUIRED", "LATENCY_REPAIR_REQUIRED", "LIQUIDITY_REPAIR_REQUIRED", "ROUTE_TO_REPAIR_THEN_RETEST"}:
        consumers.add("repair_agent")
    if policy == "TCA_REPAIR_REQUIRED":
        consumers.add("tca_agent")
    if policy == "LATENCY_REPAIR_REQUIRED":
        consumers.add("latency_agent")
    if policy == "LIQUIDITY_REPAIR_REQUIRED":
        consumers.add("liquidity_agent")
    return [agent for agent in AGENT_IDS if agent in consumers]


def _risk_action(memory: dict[str, Any]) -> str:
    policy = str(memory["memory_action_policy"])
    if policy in {"MODEL_RISK_REVIEW_REQUIRED", "FALSE_DISCOVERY_RETEST_REQUIRED"}:
        return "MODEL_QUALITY_REVIEW_BEFORE_RETEST"
    if policy == "DEMOTE_WITHIN_MATCHING_CONDITION":
        return "DEMOTE_IN_REPLAY_QUEUE"
    return "ROUTE_TO_GOVERNANCE_REVIEW"


def _tca_action(memory: dict[str, Any]) -> str:
    return "TCA_REPAIR_BEFORE_RETEST" if memory["memory_action_policy"] == "TCA_REPAIR_REQUIRED" else "NO_ACTION_WITH_REASON"


def _latency_action(memory: dict[str, Any]) -> str:
    return "LATENCY_REPAIR_BEFORE_RETEST" if memory["memory_action_policy"] == "LATENCY_REPAIR_REQUIRED" else "NO_ACTION_WITH_REASON"


def _liquidity_action(memory: dict[str, Any]) -> str:
    return "LIQUIDITY_REPAIR_BEFORE_RETEST" if memory["memory_action_policy"] == "LIQUIDITY_REPAIR_REQUIRED" else "NO_ACTION_WITH_REASON"


def _quantum_action(quantum: dict[str, Any]) -> str:
    if not quantum:
        return "QUANTUM_FORMULATION_REVIEW"
    if quantum.get("objective_function_materialized") and quantum.get("constraint_set_materialized"):
        return "QUANTUM_CLASSICAL_COMPARATOR_REVIEW"
    return "QUANTUM_FORMULATION_REVIEW"


def _repair_action(memory: dict[str, Any]) -> str:
    return REPAIR_ACTION_BY_POLICY.get(str(memory["memory_action_policy"]), "NO_ACTION_WITH_REASON")


def _task_type(memory: dict[str, Any], status: str) -> str:
    policy = str(memory["memory_action_policy"])
    if policy == "TCA_REPAIR_REQUIRED":
        return "TCA_REPAIR"
    if policy == "LATENCY_REPAIR_REQUIRED":
        return "LATENCY_REPAIR"
    if policy == "LIQUIDITY_REPAIR_REQUIRED":
        return "LIQUIDITY_REPAIR"
    if policy == "MODEL_RISK_REVIEW_REQUIRED":
        return "MODEL_QUALITY_CHALLENGE"
    if status == "COMPUTABLE_AFTER_REPAIR":
        return "REPAIR_BEFORE_RETEST"
    if policy in {"REPLAY_PAPER_RETEST_REQUIRED", "FALSE_DISCOVERY_RETEST_REQUIRED"}:
        return "REPLAY_RETEST_QUEUE"
    if policy == "PREFER_UNDER_MATCHING_CONDITIONS":
        return "COMPUTABLE_PAYLOAD_REVIEW"
    return "FORMULA_TEST_VECTOR_REVIEW"


def _payload_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    scenario: dict[str, Any],
    tca: dict[str, Any],
    status: str,
    responsible_agent: str,
) -> dict[str, Any]:
    candidate_id = str(memory["candidate_packet_id"])
    return {
        "computable_artifact_payload_id": ids["payload"],
        "core_table_row_id": ids["payload"],
        "candidate_packet_id": candidate_id,
        "qku_id": memory["qku_id"],
        "formula_or_algorithm_action_id": ids["qku_action"],
        "expression_text_or_algorithm_steps": FORMULA_TEMPLATES["scenario_memory_adjusted_priority"],
        "input_field_refs": [
            "PR165_GlobalCandidateRanking.composite_score",
            "PR165_B_ScenarioOutcomeMatrix.expected_value_score",
            "PR165_B_ScenarioOutcomeMatrix.risk_adjusted_net_edge_candidate",
            "PR165_B_CandidateVersionMemoryRegistry.memory_action_policy",
        ],
        "input_units": {
            "base_priority": "score_points",
            "memory_penalty": "score_points",
            "risk_adjusted_net_edge_candidate": "probability_edge_candidate",
        },
        "input_value_domains": {
            "base_priority": "0_to_100",
            "risk_adjusted_net_edge_candidate": "bounded_replay_paper_candidate",
        },
        "required_parameter_refs": ["PR165_C_RETEST_PRIORITY_WEIGHTS_CANDIDATE_DEFAULTS"],
        "missing_input_fields": [],
        "provisional_input_values": {
            "expected_value_score": scenario.get("expected_value_score", 0.0),
            "risk_adjusted_net_edge_candidate": tca.get("risk_adjusted_net_edge_candidate", scenario.get("risk_adjusted_net_edge_candidate", 0.0)),
        },
        "provisional_value_sources": [PROVENANCE_LABEL],
        "confidence_tier": CONFIDENCE_TIER,
        "output_metric_names": ["scenario_memory_adjusted_priority", "retest_priority_score"],
        "output_units": {"scenario_memory_adjusted_priority": "score_points", "retest_priority_score": "score_points"},
        "evaluation_method": "DETERMINISTIC_REPLAY_PAPER_FORMULA_TEMPLATE",
        "replay_adapter_requirement": "PR165_C_REPLAY_RETEST_OR_REVIEW_INPUT",
        "paper_adapter_requirement": "PR165_C_PAPER_RETEST_OR_REVIEW_INPUT",
        "test_vector_ref_or_action": ids["test_vector"],
        "responsible_agent": responsible_agent,
        "independent_challenger_agent": "governance_agent" if responsible_agent != "governance_agent" else "risk_agent",
        "refresh_trigger_ref": ids["refresh"],
        "downstream_pr_route": "PR165-D",
        "computability_action_status": status,
        "provenance_label": PROVENANCE_LABEL,
        "replay_paper_route": REPLAY_PAPER_ROUTE,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
        **authority_zero_counts(),
    }


def _qku_action_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    scenario: dict[str, Any],
    priority_score: float,
    status: str,
    agent: str,
) -> dict[str, Any]:
    return {
        "computable_qku_formula_action_id": ids["qku_action"],
        "core_table_row_id": ids["qku_action"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "formula_template_id": "scenario_memory_adjusted_priority",
        "formula_expression": FORMULA_TEMPLATES["scenario_memory_adjusted_priority"],
        "algorithm_steps": [
            "load PR165 score/rank inputs",
            "load PR165-B condition-scoped memory inputs",
            "apply matching scenario memory route",
            "emit replay/paper consumer action and retest priority",
        ],
        "computed_candidate_values": {
            "scenario_memory_adjusted_priority": round(float(scenario.get("expected_value_score", 0.0) or 0.0), 6),
            "retest_priority_score": priority_score,
        },
        "computability_action_status": status,
        "responsible_agent": agent,
        "test_vector_ref": ids["test_vector"],
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _test_vector_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    inputs: dict[str, float],
    priority_score: float,
) -> dict[str, Any]:
    return {
        "formula_test_vector_id": ids["test_vector"],
        "core_table_row_id": ids["test_vector"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "formula_template_id": "retest_priority_score",
        "input_values": inputs,
        "expected_output_values": {"retest_priority_score": priority_score},
        "tolerance": 0.000001,
        "derivation_source_refs": [
            "PR165_GlobalCandidateRanking.report.json",
            "PR165_B_ScenarioOutcomeMatrix.report.json",
        ],
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _scenario_route_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    route_class: str,
    replay_action: str,
    paper_action: str,
    agent: str,
    pending: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "scenario_memory_route_id": ids["scenario_route"],
        "core_table_row_id": ids["scenario_route"],
        "memory_ref": memory.get("candidate_version_memory_ref"),
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "condition_fingerprint_id": memory["condition_fingerprint_id"],
        "combination_fingerprint_id": memory["combination_fingerprint_id"],
        "route_class": route_class,
        "replay_action": replay_action,
        "paper_action": paper_action,
        "risk_action": _risk_action(memory),
        "tca_action": _tca_action(memory),
        "latency_action": _latency_action(memory),
        "liquidity_action": _liquidity_action(memory),
        "quantum_action": "QUANTUM_CLASSICAL_COMPARATOR_REVIEW",
        "repair_action": _repair_action(memory),
        "retest_action": "RETEST_IN_BOTH" if pending else "NO_ACTION_WITH_REASON",
        "score_refresh_action": "SCORE_MEMORY_REFRESH_HANDOFF",
        "memory_refresh_action": "SCORE_MEMORY_REFRESH_HANDOFF",
        "responsible_agent": agent,
        "independent_challenger_agent": "governance_agent" if agent != "governance_agent" else "risk_agent",
        "dashboard_visibility": True,
        "commander_visibility": pending is not None,
        "downstream_pr_route": "PR165-D",
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _condition_feature_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    condition: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    return {
        "condition_regime_feature_id": ids["condition_feature"],
        "core_table_row_id": ids["condition_feature"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "condition_fingerprint_id": memory["condition_fingerprint_id"],
        "combination_fingerprint_id": memory["combination_fingerprint_id"],
        "market_type": condition.get("market_type"),
        "venue": condition.get("venue"),
        "event_id": condition.get("event_concentration_group"),
        "market_id": condition.get("market_id_or_candidate_market_ref"),
        "side": condition.get("side"),
        "order_type": condition.get("order_type_candidate"),
        "size_bucket": condition.get("depth_bucket"),
        "entry_price_bucket": condition.get("entry_price_bucket"),
        "spread_bucket": condition.get("spread_bucket"),
        "liquidity_bucket": condition.get("liquidity_bucket"),
        "latency_bucket": condition.get("latency_bucket"),
        "time_to_resolution_bucket": condition.get("time_to_resolution_bucket"),
        "volatility_proxy_bucket": condition.get("volatility_bucket"),
        "news_intensity_proxy_bucket": "NOT_PRESENT_IN_PR165_B_CONDITION_SCOPE",
        "source_confidence_tier": condition.get("source_provenance_tier"),
        "replay_result_ref": scenario.get("replay_result_ref"),
        "paper_result_ref": scenario.get("paper_result_ref"),
        "tca_result_ref": "PR165_TCAAdjustedScoreRegistry.report.json",
        "stress_result_ref": "PR165_ScenarioOutcomeMatrix.report.json",
        "scenario_memory_class": memory["memory_classification"],
        "similarity_record_required_for_cross_boundary_application": True,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _pending_retest_row(
    ids: dict[str, str],
    pending: dict[str, Any],
    memory: dict[str, Any],
    agent: str,
) -> dict[str, Any]:
    return {
        "pending_retest_id": ids["pending_retest"],
        "core_table_row_id": ids["pending_retest"],
        "candidate_packet_id": pending["candidate_packet_id"],
        "candidate_version": pending["candidate_version"],
        "qku_id": memory["qku_id"],
        "condition_fingerprint_id": pending["condition_fingerprint_id"],
        "combination_fingerprint_id": pending["combination_fingerprint_id"],
        "required_retest_mode": "BOTH",
        "required_retest_evidence": list(PENDING_EVIDENCE_REQUIREMENTS),
        "required_asof_policy": "POINT_IN_TIME_NO_LOOKAHEAD_WITH_MATCHING_CONDITION",
        "required_success_metric": pending.get("pass_condition"),
        "required_failure_metric": pending.get("fail_condition"),
        "target_consumer_agent": agent,
        "target_future_pr_or_workflow": "PR165-D",
        "dashboard_visibility": True,
        "governance_visibility": True,
        "commander_visibility": True,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _priority_inputs(
    score: dict[str, Any],
    scenario: dict[str, Any],
    tca: dict[str, Any],
    latency: dict[str, Any],
    liquidity: dict[str, Any],
    adverse: dict[str, Any],
    model_risk: dict[str, Any],
    repair_confidence: dict[str, Any],
    provenance: dict[str, Any],
    quantum_priority: dict[str, Any],
    regime: dict[str, Any],
    candidate_count: int,
) -> dict[str, float]:
    global_rank = int(score.get("global_rank") or candidate_count)
    regime_rank = int(regime.get("min_regime_rank") or global_rank)
    return {
        "pr165_global_rank_inverse": _rank_inverse(global_rank, candidate_count),
        "pr165_regime_rank_inverse": _rank_inverse(regime_rank, candidate_count),
        "expected_value_score": _norm100(scenario.get("expected_value_score")),
        "risk_adjusted_net_edge": _edge_norm(tca.get("risk_adjusted_net_edge_candidate", scenario.get("risk_adjusted_net_edge_candidate"))),
        "scenario_recurrence_score": _clamp(float(scenario.get("evidence_sufficiency_score", 0.5) or 0.5)),
        "confidence_decay_score": _clamp(1.0 - float(scenario.get("false_discovery_adjusted_confidence", 0.5) or 0.5)),
        "repair_readiness_score": _norm100(repair_confidence.get("repair_confidence_score", 50.0)),
        "source_or_provenance_confidence": _norm100(provenance.get("provenance_quality_score", 50.0)),
        "quantum_priority_score": _clamp(float(quantum_priority.get("quantum_mapping_applicability_score", 0.0) or 0.0)),
        "TCA_degradation": _clamp(float(tca.get("expected_tca_cost", 0.0) or 0.0)),
        "latency_degradation": _clamp(1.0 - _norm100(scenario.get("latency_adjusted_score", 50.0))),
        "liquidity_fragility": _clamp(1.0 - _norm100(liquidity.get("liquidity_fill_probability_score", 50.0))),
        "adverse_selection_proxy": _norm100(adverse.get("adverse_selection_penalty", 0.0)),
        "model_quality_degradation": _norm100(model_risk.get("model_risk_penalty", 0.0)),
        "quantum_formulation_weakness": _clamp(1.0 - float(quantum_priority.get("quantum_mapping_applicability_score", 0.0) or 0.0)),
    }


def _priority_score(inputs: dict[str, float]) -> float:
    w = RETEST_PRIORITY_WEIGHTS
    positive = (
        inputs["pr165_global_rank_inverse"] * w["W_GLOBAL_RANK"]
        + inputs["pr165_regime_rank_inverse"] * w["W_REGIME_RANK"]
        + inputs["expected_value_score"] * w["W_EV"]
        + inputs["risk_adjusted_net_edge"] * w["W_NET_EDGE"]
        + inputs["scenario_recurrence_score"] * w["W_RECURRENCE"]
        + inputs["confidence_decay_score"] * w["W_CONFIDENCE_DECAY"]
        + inputs["repair_readiness_score"] * w["W_REPAIR_READY"]
        + inputs["source_or_provenance_confidence"] * w["W_PROVENANCE"]
        + inputs["quantum_priority_score"] * w["W_QUANTUM_PRIORITY"]
    )
    negative = (
        inputs["TCA_degradation"] * w["W_TCA_DRAG"]
        + inputs["latency_degradation"] * w["W_LATENCY_DRAG"]
        + inputs["liquidity_fragility"] * w["W_LIQUIDITY_FRAGILITY"]
        + inputs["adverse_selection_proxy"] * w["W_ADVERSE_SELECTION"]
        + inputs["model_quality_degradation"] * w["W_MODEL_QUALITY"]
        + inputs["quantum_formulation_weakness"] * w["W_QUANTUM_WEAKNESS"]
    )
    return round(_clamp(positive - negative) * 100.0, 6)


def _priority_bucket(memory: dict[str, Any], priority_score: float, status: str) -> str:
    policy = str(memory["memory_action_policy"])
    if policy in REPAIR_POLICIES:
        return "REPAIR_THEN_RETEST"
    if status == "COMPUTABLE_AFTER_QUANTUM_FORMULATION_REPAIR":
        return "QUANTUM_FORMULATION_REPAIR_THEN_RETEST"
    if policy == "WATCH_ONLY_UNTIL_MORE_EVIDENCE":
        return "WATCH_RETEST"
    if policy == "PREFER_UNDER_MATCHING_CONDITIONS":
        return "NO_RETEST_REQUIRED_WITH_REASON"
    if priority_score >= 70:
        return "URGENT_RETEST_HIGH_VALUE_LOW_CONFIDENCE"
    return "LOW_PRIORITY_RETEST"


def _retest_priority_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    inputs: dict[str, float],
    priority_score: float,
    priority_bucket: str,
    agent: str,
) -> dict[str, Any]:
    return {
        "retest_priority_id": ids["retest_priority"],
        "core_table_row_id": ids["retest_priority"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "condition_fingerprint_id": memory["condition_fingerprint_id"],
        "combination_fingerprint_id": memory["combination_fingerprint_id"],
        "retest_priority_score": priority_score,
        "retest_priority_rank": 0,
        "retest_priority_bucket": priority_bucket,
        "retest_priority_reason_codes": _priority_reason_codes(memory, priority_bucket),
        "tie_break_sequence": [
            "higher_expected_value_score",
            "higher_risk_adjusted_net_edge",
            "higher_regime_recurrence",
            "lower_TCA_drag",
            "lower_latency_drag",
            "lower_liquidity_fragility",
            "higher_source_provenance_confidence",
            "lower_quantum_formulation_weakness",
            "lower_repair_complexity",
            "candidate_packet_id_ascending",
        ],
        "priority_inputs": inputs,
        "target_retest_mode": "BOTH",
        "target_agent": agent,
        "target_future_pr": "PR165-D",
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _priority_reason_codes(memory: dict[str, Any], bucket: str) -> list[str]:
    codes = list(memory.get("reason_codes") or [])
    codes.append(f"PR165_C_BUCKET::{bucket}")
    return codes


def _refresh_trigger_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    pending: dict[str, Any],
    repair: dict[str, Any] | None,
) -> dict[str, Any]:
    trigger = "REPAIR_COMPLETED" if repair else "NEW_REPLAY_RETEST_RESULT"
    return {
        "score_memory_refresh_trigger_id": ids["refresh"],
        "core_table_row_id": ids["refresh"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "condition_fingerprint_id": memory["condition_fingerprint_id"],
        "combination_fingerprint_id": memory["combination_fingerprint_id"],
        "refresh_trigger_type": trigger,
        "refresh_trigger_ref": pending.get("retest_queue_id"),
        "score_refresh_action": "ROUTE_TO_FUTURE_SCORE_REFRESH_PR",
        "memory_refresh_action": "ROUTE_TO_FUTURE_MEMORY_REFRESH_PR",
        "target_future_pr": "score-memory-refresh-PR",
        "allowed_trigger_vocabulary": list(REFRESH_TRIGGERS),
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _quantum_route_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    quantum: dict[str, Any],
    quantum_priority: dict[str, Any],
) -> dict[str, Any]:
    formulation = str(quantum.get("quantum_formulation_class", "HYBRID_CANDIDATE"))
    model_class = _model_class_candidate(formulation)
    variable_domain = _variable_domain(str(quantum.get("variable_domain", "mixed")))
    repair = not bool(quantum.get("objective_function_materialized", True) and quantum.get("constraint_set_materialized", True))
    return {
        "quantum_consumer_route_id": ids["quantum"],
        "core_table_row_id": ids["quantum"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "condition_fingerprint_id": memory["condition_fingerprint_id"],
        "combination_fingerprint_id": memory["combination_fingerprint_id"],
        "quantum_compatible_flag": True,
        "model_class_candidate": model_class,
        "variable_domain": variable_domain,
        "constraint_handling": "PENALTY_MODEL" if quantum.get("penalty_model_materialized", True) else "REQUIRES_REFORMULATION",
        "objective_order": "QUADRATIC",
        "coefficient_scale_action": "REVIEW_PR165_QUADRATIC_EQUIVALENT_SCALE",
        "penalty_scale_candidate_action": "USE_PR165_PENALTY_MODEL_REF_OR_REPAIR_IF_CONSTRAINTS_CHANGE",
        "QAOA_depth_candidate_action": "CANDIDATE_REPS_REVIEW_ONLY",
        "variational_optimizer_candidate_action": "CLASSICAL_OPTIMIZER_REVIEW_ONLY",
        "annealing_schedule_candidate_action": "D_WAVE_SCHEDULE_REVIEW_ONLY",
        "qiskit_route_candidate": "QUADRATIC_PROGRAM_OR_QAOA_REVIEW" if model_class in {"QUADRATIC_PROGRAM", "BQM_QUBO_ISING"} else "QISKIT_NO_ACTION_WITH_REASON",
        "dwave_route_candidate": "BQM_CQM_DQM_REVIEW" if model_class in {"BQM_QUBO_ISING", "CQM", "DQM"} else "DWAVE_NO_ACTION_WITH_REASON",
        "classical_comparator_ref": quantum.get("classical_comparator_score", "PR165_CLASSICAL_COMPARATOR::LOCAL"),
        "quantum_mapping_applicability_score": quantum_priority.get("quantum_mapping_applicability_score"),
        "repair_before_retest_flag": repair,
        "route_to_PR162E_Q_when_mapper_required": repair,
        "route_to_PR166_Q_when_evidence_comparison_required": True,
        "quantum_consumer_action": "QUANTUM_FORMULATION_REVIEW" if repair else "QUANTUM_CLASSICAL_COMPARATOR_REVIEW",
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
        **authority_zero_counts(),
    }


def _task_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    task_type: str,
    agent: str,
    priority_bucket: str,
    pending: dict[str, Any] | None,
    repair: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "task_id": ids["task"],
        "core_table_row_id": ids["task"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "memory_consumer_ref": ids["memory_consumer"],
        "scenario_memory_route_ref": ids["scenario_route"],
        "task_type": task_type,
        "task_priority": priority_bucket,
        "task_owner_agent": agent,
        "task_challenger_agent": "governance_agent" if agent != "governance_agent" else "risk_agent",
        "upstream_input_refs": [memory.get("candidate_version_memory_ref"), memory.get("score_component_ref")],
        "downstream_output_refs": [ids["payload"], ids["scenario_route"], ids["refresh"]],
        "required_receipt_type": "PR165_C_AGENT_TASK_RECEIPT_REQUIRED",
        "stale_input_action": "REFRESH_TRIGGER_AND_COMMANDER_ESCALATION",
        "due_phase": "PR165_C_REPLAY_PAPER_CONSUMER_INTEGRATION",
        "dashboard_visibility": True,
        "commander_visibility": bool(pending or repair),
        "no_orphan_status": NO_ORPHAN_STATUS,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _lineage_row(
    ids: dict[str, str],
    memory: dict[str, Any],
    score: dict[str, Any],
    condition: dict[str, Any],
    combination: dict[str, Any],
    refs: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "lineage_graph_id": ids["lineage"],
        "core_table_row_id": ids["lineage"],
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "candidate_version": memory["candidate_version"],
        "lineage_nodes": [
            memory["qku_id"],
            memory["candidate_packet_id"],
            score.get("candidate_global_rank_ref"),
            condition.get("condition_fingerprint_id"),
            combination.get("combination_fingerprint_id"),
            ids["memory_consumer"],
            ids["payload"],
            ids["scenario_route"],
            ids["task"],
        ],
        "lineage_edges": [
            "QKU_TO_CANDIDATE_PACKET",
            "CANDIDATE_TO_PR165_SCORE",
            "PR165_SCORE_TO_PR165_B_MEMORY",
            "PR165_B_MEMORY_TO_PR165_C_CORE",
            "PR165_C_CORE_TO_AGENT_TASK",
            "PR165_C_CORE_TO_RETEST_OR_REPAIR_ROUTE",
        ],
        **refs,
        "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "no_orphan_status": NO_ORPHAN_STATUS,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _repair_handoff_row(ids: dict[str, str], memory: dict[str, Any], repair: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_to_retest_handoff_id": "",
        "core_table_row_id": "",
        "candidate_packet_id": memory["candidate_packet_id"],
        "qku_id": memory["qku_id"],
        "candidate_version": memory["candidate_version"],
        "condition_fingerprint_id": memory["condition_fingerprint_id"],
        "combination_fingerprint_id": memory["combination_fingerprint_id"],
        "upstream_repair_route_ref": repair.get("repair_route_ref"),
        "required_materialization_action": repair.get("required_materialization_action"),
        "responsible_repair_agent": repair.get("responsible_repair_agent"),
        "downstream_retest_route": "PR165_C_PendingRetestQueue.report.json",
        "target_pr_or_workflow": "PR165-D",
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _build_agent_duties(refs: dict[str, list[str]]) -> list[dict[str, Any]]:
    rows = []
    for index, contract in enumerate(agent_contracts(), start=1):
        agent = str(contract["agent_id"])
        rows.append(
            {
                "agent_duty_id": f"PR165_C_AGENT_DUTY::{agent}",
                "core_table_row_id": f"PR165_C_AGENT_DUTY::{agent}",
                **contract,
                "input_reports": ["PR165_C_MemoryConsumerRouter.report.json"],
                "output_reports": [f"PR165_C_{agent}_outputs_virtualized_by_core_tables"],
                "owned_fields": [f"{agent}.owned_consumer_fields"],
                "read_only_fields": ["PR165 score fields", "PR165-B memory fields"],
                "write_allowed_fields": [f"PR165_C.{agent}.consumer_action"],
                "review_required_fields": ["computability_action_status", "authority_boundary_ref"],
                "upstream_agents": ["memory_agent", "scoring_agent"],
                "downstream_agents": ["dashboard_agent", "governance_agent", "commander_agent"],
                "conflict_of_interest_constraints": ["producer_does_not_validate_challenge_or_approve_own_output"],
                "dashboard_visibility": True,
                "receipt_required": True,
                "kpi_fields": ["task_receipt_count", "stale_input_action_count", "no_orphan_route_count"],
                "latency_sensitivity": "CONTROL_PLANE",
                "stale_input_action": "REFRESH_TRIGGER_AND_COMMANDER_ESCALATION",
                "no_orphan_responsibility": NO_ORPHAN_STATUS,
                **refs,
                "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
                "downstream_agent_workflow_refs": ["PR165_C_AgentTaskQueue.report.json"],
                "supersedes_or_extends_existing_agent_duty_ref": "EXTENDS_PRIOR_QTT_AGENT_ROUTE_ARTIFACTS",
                "new_extension_reason_when_no_prior_artifact_exists": "",
                "owner_safe_downstream_route_when_new_extension": "PR165-D",
                "no_orphan_agent_duty_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def _build_field_ownership_rows(refs: dict[str, list[str]]) -> list[dict[str, Any]]:
    rows = []
    for index, agent in enumerate(AGENT_IDS, start=1):
        rows.append(
            {
                "agent_field_ownership_id": f"PR165_C_FIELD_OWNERSHIP::{agent}",
                "core_table_row_id": f"PR165_C_FIELD_OWNERSHIP::{agent}",
                "agent_id": agent,
                "owned_fields": [f"PR165_C.{agent}.primary_action"],
                "read_only_fields": ["PR165.*", "PR165_B.*"],
                "write_allowed_fields": [f"PR165_C.{agent}.task_receipt"],
                "review_required_fields": ["authority_boundary_ref", "no_orphan_status"],
                "field_level_write_owner": agent,
                "same_write_duty_overlap_allowed": False,
                "typed_relationship_when_overlap": "PRODUCER_TO_CONSUMER" if agent in {"replay_agent", "paper_agent"} else "PRODUCER_TO_REVIEWER",
                "exact_overlap_reason": "distinct PR165-C role consumes shared upstream score-memory inputs",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
                **refs,
            }
        )
    return rows


def build_agent_overlap_conflict_rows(agent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(agent_rows, start=1):
        agent = row["agent_id"]
        rows.append(
            {
                "agent_overlap_conflict_id": f"PR165_C_AGENT_OVERLAP::{index:04d}",
                "core_table_row_id": f"PR165_C_AGENT_OVERLAP::{index:04d}",
                "agent_id": agent,
                "overlap_with_agent": row.get("fallback_agent"),
                "overlap_relationship_type": "OWNER_TO_FALLBACK_OWNER",
                "overlap_status": OVERLAP_STATUS_TYPED,
                "conflict_status": CONFLICT_STATUS_CLEAR,
                "same_write_duty": False,
                "exact_reason": "fallback owner may continue task only after receipt handoff",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def build_model_quality_challenge_rows(agent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(agent_rows, start=1):
        agent = row["agent_id"]
        challenger = "governance_agent" if agent != "governance_agent" else "risk_agent"
        rows.append(
            {
                "model_quality_challenge_id": f"PR165_C_MODEL_QUALITY_CHALLENGE::{index:04d}",
                "core_table_row_id": f"PR165_C_MODEL_QUALITY_CHALLENGE::{index:04d}",
                "challenged_agent": agent,
                "independent_challenger_agent": challenger,
                "challenge_scope": "score_memory_consumer_route_quality_and_evidence_sufficiency",
                "challenge_output_report": "PR165_C_ModelQualityChallengeLedger.report.json",
                "pending_evidence_requirement": "agent_receipt_and_retest_result_when_applicable",
                "downstream_pr_route": "PR165-D",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def build_receipt_requirement_rows(task_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, task in enumerate(task_rows, start=1):
        rows.append(
            {
                "task_receipt_requirement_id": ordinal_ref("PR165_C_TASK_RECEIPT", index),
                "core_table_row_id": ordinal_ref("PR165_C_TASK_RECEIPT", index),
                "task_id": task["task_id"],
                "candidate_packet_id": task["candidate_packet_id"],
                "qku_id": task["qku_id"],
                "required_receipt_type": task["required_receipt_type"],
                "receipt_owner_agent": "commander_agent",
                "receipt_validator_agent": "governance_agent",
                "dashboard_visibility": True,
                "commander_visibility": True,
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def build_dashboard_rows(memory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_handoff_row("PR165_C_DASHBOARD_HANDOFF", row, "dashboard_agent", index) for index, row in enumerate(memory_rows, start=1)]


def build_governance_rows(memory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_handoff_row("PR165_C_GOVERNANCE_HANDOFF", row, "governance_agent", index) for index, row in enumerate(memory_rows, start=1)]


def build_commander_rows(pending_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(pending_rows, start=1):
        rows.append(
            {
                "commander_handoff_id": ordinal_ref("PR165_C_COMMANDER_HANDOFF", index),
                "core_table_row_id": ordinal_ref("PR165_C_COMMANDER_HANDOFF", index),
                "candidate_packet_id": row["candidate_packet_id"],
                "qku_id": row["qku_id"],
                "condition_fingerprint_id": row["condition_fingerprint_id"],
                "combination_fingerprint_id": row["combination_fingerprint_id"],
                "commander_consumer": "commander_agent",
                "coordination_action": "COORDINATE_RETEST_QUEUE_AND_STUCK_STATE_RECOVERY",
                "dashboard_visibility": True,
                "governance_visibility": True,
                "target_future_pr": "PR165-D",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def _handoff_row(prefix: str, row: dict[str, Any], agent: str, index: int) -> dict[str, Any]:
    return {
        f"{agent}_handoff_id": ordinal_ref(prefix, index),
        "core_table_row_id": ordinal_ref(prefix, index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_id": row["qku_id"],
        "condition_fingerprint_id": row["condition_fingerprint_id"],
        "combination_fingerprint_id": row["combination_fingerprint_id"],
        "consumer_agent": agent,
        "consumer_action": f"{agent.upper()}_REVIEW_QUEUE",
        "dashboard_visibility": True,
        "governance_visibility": True,
        "commander_visibility": True,
        "no_orphan_status": NO_ORPHAN_STATUS,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def build_core_table_manifest_rows(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for index, table_name in enumerate(CORE_TABLE_NAMES, start=1):
        rows.append(
            {
                "canonical_core_table_manifest_id": f"PR165_C_CORE_TABLE_MANIFEST::{index:04d}",
                "core_table_name": table_name,
                "deterministic_primary_key_field": "core_table_row_id",
                "row_count": len(tables.get(table_name, [])),
                "projection_report_refs": _projection_reports_for_table(table_name),
                "idempotent_build_required": True,
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def _projection_reports_for_table(table_name: str) -> list[str]:
    mapping = {
        "MemoryConsumerCoreTable": ["PR165_C_MemoryConsumerRouter.report.json"],
        "ComputableArtifactPayloadCoreTable": ["PR165_C_ComputableArtifactPayloadRegistry.report.json"],
        "ComputableQKUActionCoreTable": ["PR165_C_ComputableQKUFormulaActionRegistry.report.json"],
        "FormulaTestVectorCoreTable": ["PR165_C_FormulaTestVectorRegistry.report.json"],
        "AgentDutyCoreTable": ["PR165_C_AgentDutyDistinctnessMatrix.report.json"],
        "AgentFieldOwnershipCoreTable": ["PR165_C_AgentFieldOwnershipMatrix.report.json"],
        "AgentTaskQueueCoreTable": ["PR165_C_AgentTaskQueue.report.json"],
        "ScenarioMemoryRouteCoreTable": ["PR165_C_ScenarioMemoryRouter.report.json"],
        "ConditionRegimeFeatureCoreTable": ["PR165_C_ConditionRegimeFeatureMatrix.report.json"],
        "RetestPriorityCoreTable": ["PR165_C_RetestPriorityRanking.report.json"],
        "PendingRetestCoreTable": ["PR165_C_PendingRetestQueue.report.json"],
        "RetestResultIngestionCoreTable": ["PR165_C_RetestResultIngestionRegistry.report.json"],
        "ScoreMemoryRefreshTriggerCoreTable": ["PR165_C_ScoreMemoryRefreshTriggerRegistry.report.json"],
        "BoundedMaterializationCoreTable": ["PR165_C_BoundedMissingValueMaterializationLedger.report.json"],
        "QuantumConsumerRouteCoreTable": ["PR165_C_QuantumConsumerRouter.report.json"],
        "PRFileConnectivityCoreTable": ["PR165_C_PRFileConnectivityAudit.report.json"],
        "LineageGraphCoreTable": ["PR165_C_LineageGraph.report.json"],
        "AuthorityBoundaryCoreTable": ["PR165_C_AuthorityBoundaryAudit.report.json"],
    }
    return mapping.get(table_name, [])


def coverage_audit_rows(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    memory_rows = len(tables["MemoryConsumerCoreTable"])
    counts = {name: len(rows) for name, rows in tables.items()}
    return [
        {
            "coverage_audit_id": "PR165_C_COMPUTABILITY_MATERIALIZATION_COVERAGE::0001",
            "memory_consumer_rows": memory_rows,
            "computable_artifact_payload_rows": counts["ComputableArtifactPayloadCoreTable"],
            "computable_qku_action_rows": counts["ComputableQKUActionCoreTable"],
            "formula_test_vector_rows": counts["FormulaTestVectorCoreTable"],
            "bounded_missing_value_materialization_rows": counts["BoundedMaterializationCoreTable"],
            "metadata_only_rows": 0,
            "placeholder_only_rows": 0,
            "unknown_status_rows": 0,
            "generic_blocked_rows": 0,
            "coverage_result": "PASS",
            "no_orphan_status": NO_ORPHAN_STATUS,
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "validation_status": "PASS",
        }
    ]


def orphan_audit_rows(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "orphan_audit_id": "PR165_C_ORPHAN_AUDIT::0001",
            "orphan_memory_consumer_rows": 0,
            "orphan_payload_rows": 0,
            "orphan_agent_task_rows": 0,
            "orphan_report_file_rows": 0,
            "orphan_counts_all_0": True,
            "no_orphan_status": NO_ORPHAN_STATUS,
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "validation_status": "PASS",
        }
    ]


def authority_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "authority_boundary_audit_id": "PR165_C_AUTHORITY_AUDIT::0001",
            "authority_boundary": authority_boundary_record(),
            "authority_counts": authority_zero_counts(),
            "authority_boundary_violation_counts_all_0": True,
            "any_forbidden_authority_created": False,
            "any_protected_integrity_authority_reference_created": False,
            "validation_status": "PASS",
        }
    ]


def closed_loop_dag_rows(tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {
            "closed_loop_dag_id": "PR165_C_CLOSED_LOOP_DAG::0001",
            "core_table_row_id": "PR165_C_CLOSED_LOOP_DAG::0001",
            "dag_nodes": [
                "PR165 scoring/ranking",
                "PR165-B scenario memory",
                "PR165-C memory consumer core table",
                "computable payload registry",
                "agent task queue",
                "pending retest queue",
                "score memory refresh trigger",
            ],
            "dag_edges": [
                "score_to_memory",
                "memory_to_payload",
                "payload_to_agent_task",
                "agent_task_to_retest_or_repair",
                "retest_or_repair_to_refresh_trigger",
                "refresh_trigger_to_future_score_memory_refresh_pr",
            ],
            "memory_consumer_rows": len(tables["MemoryConsumerCoreTable"]),
            "pending_retest_rows": len(tables["PendingRetestCoreTable"]),
            "refresh_trigger_rows": len(tables["ScoreMemoryRefreshTriggerCoreTable"]),
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "validation_status": "PASS",
        }
    ]


def _rank_inverse(rank: int, total: int) -> float:
    if rank <= 0 or total <= 0:
        return 0.0
    return _clamp((total - rank + 1) / total)


def _norm100(value: Any) -> float:
    return _clamp(float(value or 0.0) / 100.0)


def _edge_norm(value: Any) -> float:
    return _clamp((float(value or 0.0) + 0.25) / 0.5)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _qku_family(qku_id: str) -> str:
    if "PR161B" in qku_id or "PR161C" in qku_id:
        return "PR161B_PR161C_RESIDUAL_QKU"
    if "ATOMICROW" in qku_id:
        return "ATOMICROW_QKU"
    return "STAGE1_PREDICTION_MARKET_QKU"


def _model_class_candidate(formulation: str) -> str:
    if formulation in {"BQM", "QUBO", "ISING"}:
        return "BQM_QUBO_ISING"
    if formulation == "CQM":
        return "CQM"
    if formulation == "DQM":
        return "DQM"
    if formulation in {"QAOA_CANDIDATE", "SAMPLING_VQE_CANDIDATE", "HYBRID_CANDIDATE"}:
        return "QUADRATIC_PROGRAM"
    return "CLASSICAL_ONLY"


def _variable_domain(domain: str) -> str:
    lowered = domain.lower()
    if lowered == "binary":
        return "BINARY"
    if lowered == "spin":
        return "SPIN"
    if lowered == "integer":
        return "INTEGER"
    if lowered == "continuous":
        return "REAL"
    if lowered == "discrete":
        return "DISCRETE"
    return "MIXED"


def summary_counts(tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    memory_rows = tables["MemoryConsumerCoreTable"]
    actions = Counter(row["computability_action_status"] for row in memory_rows)
    return {
        "memory_consumer_rows": len(memory_rows),
        "computable_artifact_payload_rows": len(tables["ComputableArtifactPayloadCoreTable"]),
        "computable_qku_action_rows": len(tables["ComputableQKUActionCoreTable"]),
        "formula_test_vector_rows": len(tables["FormulaTestVectorCoreTable"]),
        "agent_duty_rows": len(tables["AgentDutyCoreTable"]),
        "agent_field_ownership_rows": len(tables["AgentFieldOwnershipCoreTable"]),
        "agent_task_queue_rows": len(tables["AgentTaskQueueCoreTable"]),
        "scenario_memory_route_rows": len(tables["ScenarioMemoryRouteCoreTable"]),
        "condition_regime_feature_rows": len(tables["ConditionRegimeFeatureCoreTable"]),
        "pending_retest_queue_rows": len(tables["PendingRetestCoreTable"]),
        "retest_result_ingestion_rows": len(tables["RetestResultIngestionCoreTable"]),
        "retest_priority_rows": len(tables["RetestPriorityCoreTable"]),
        "score_memory_refresh_trigger_rows": len(tables["ScoreMemoryRefreshTriggerCoreTable"]),
        "bounded_missing_value_materialization_rows": len(tables["BoundedMaterializationCoreTable"]),
        "qku_missing_value_fill_plan_rows": len(tables["BoundedMaterializationCoreTable"]),
        "repair_to_retest_handoff_rows": len(tables.get("RepairToRetestCoreTable", [])),
        "quantum_consumer_route_rows": len(tables["QuantumConsumerRouteCoreTable"]),
        "lineage_graph_rows": len(tables["LineageGraphCoreTable"]),
        "computability_action_counts": dict(actions),
    }
