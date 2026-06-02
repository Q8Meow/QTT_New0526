"""Execution classification for all PR162B QKUs."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .qku_agent_activation import activation_status, trade_role_for_qku


def classify_execution(
    qku: dict[str, Any],
    market_record: dict[str, Any],
    formula_binding_refs: dict[str, list[str]],
    algorithm_binding_refs: dict[str, list[str]],
    solver_mapping_refs: dict[str, list[str]],
    pr162a_mapping_by_qku: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    qku_id = qku["qku_id"]
    qku_type = str(qku.get("qku_type") or "")
    has_formula_binding = bool(formula_binding_refs.get(qku_id, []))
    has_algorithm_binding = bool(algorithm_binding_refs.get(qku_id, []))
    has_solver_mapping = bool(solver_mapping_refs.get(qku_id, []))
    input_fields = _input_fields_for_qku(qku, market_record)
    output_fields = _output_fields_for_qku(qku)
    primary_execution_class, secondary = _execution_class_for_qku(
        qku,
        has_formula_binding=has_formula_binding,
        has_algorithm_binding=has_algorithm_binding,
        has_solver_mapping=has_solver_mapping,
    )
    act, dormancy, live_status = activation_status(
        market_record["primary_market_scope"],
        primary_execution_class,
        has_binding=has_formula_binding or has_algorithm_binding or has_solver_mapping or qku_type
        in {"PARAMETER_QKU", "RANGE_QKU", "DEFAULT_VALUE_QKU", "ATOMICROW_QKU", "AGENT_BINDING_QKU"},
        has_input_binding=bool(input_fields),
        market_scope_confidence=market_record["market_scope_confidence"],
    )
    blocker = _blocker_code(primary_execution_class, dormancy, live_status)
    route = pr162a_mapping_by_qku.get(qku_id, {})
    trade_role = trade_role_for_qku(qku, primary_execution_class)
    return {
        "record_id": f"PR162B-EXECUTION-{qku_id}",
        "qku_id": qku_id,
        "qku_family": qku_type,
        "upstream_atomicrows_refs": [
            "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json",
            "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
        ],
        "upstream_pr161c_refs": [
            qku.get("qku_source_artifact_path"),
            "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
        ],
        "upstream_pr161d_refs": ["docs/master_plan/generated/PR161D_QKUQualityScoreRegistry.report.json"],
        "upstream_pr161e_refs": ["docs/master_plan/generated/PR161E_FinalSummary.report.json"],
        "upstream_pr161f_refs": [
            "docs/master_plan/generated/PR161F_ExecutorInputRegistry.report.json",
            route.get("pr161f_executor_input_id"),
        ],
        "upstream_pr162_refs": ["docs/master_plan/generated/PR162_QKUArtifactCoverageBridge.report.json"],
        "upstream_pr162a_refs": [
            "docs/master_plan/generated/PR162A_MarketScenarioQKUMappingMatrix.report.json",
            route.get("record_id"),
        ],
        "primary_execution_class": primary_execution_class,
        "secondary_execution_classes": secondary,
        "primary_market_scope": market_record["primary_market_scope"],
        "compatible_market_scopes": market_record["compatible_market_scopes"],
        "stage1_prediction_market_activation_status": act,
        "dormancy_status": dormancy,
        "trade_role": trade_role,
        "formula_required_flag": qku_type in {"FORMULA_QKU", "RISK_QKU", "CONSTRAINT_QKU"},
        "algorithm_required_flag": qku_type == "ALGORITHM_QKU",
        "objective_required_flag": primary_execution_class in {"OBJECTIVE_EXECUTABLE", "SOLVER_INPUT_ASSEMBLABLE"},
        "constraint_required_flag": qku_type == "CONSTRAINT_QKU",
        "parameter_value_required_flag": qku_type in {"PARAMETER_QKU", "RANGE_QKU", "DEFAULT_VALUE_QKU", "OPTIMIZER_SETTING_QKU"},
        "feature_compute_required_flag": qku_type == "ATOMICROW_QKU",
        "solver_mapping_required_flag": bool(qku.get("qku_quantum_subclass")),
        "source_evidence_required_flag": True,
        "formula_refs": formula_binding_refs.get(qku_id, []),
        "algorithm_refs": algorithm_binding_refs.get(qku_id, []),
        "objective_refs": [],
        "constraint_refs": [],
        "parameter_refs": [],
        "tradable_value_refs": [],
        "input_field_refs": input_fields,
        "output_field_refs": output_fields,
        "solver_mapping_refs": solver_mapping_refs.get(qku_id, []),
        "test_vector_refs": [],
        "agent_consumer_refs": _agent_consumers_for_role(trade_role),
        "replay_paper_route_refs": [
            route.get("pr161f_replay_request_id"),
            route.get("pr161f_paper_request_id"),
            route.get("pr161f_paired_plan_id"),
        ],
        "live_mode_formula_gate_status": live_status,
        "blocker_code": blocker,
        "created_by_pr": c.PR_ID,
    }


def _execution_class_for_qku(
    qku: dict[str, Any],
    *,
    has_formula_binding: bool,
    has_algorithm_binding: bool,
    has_solver_mapping: bool,
) -> tuple[str, list[str]]:
    qku_type = str(qku.get("qku_type") or "")
    subclass = str(qku.get("qku_quantum_subclass") or "")
    if has_solver_mapping and "QUBO" in subclass.upper():
        return "SOLVER_SMOKE_EXECUTABLE", ["SOLVER_INPUT_ASSEMBLABLE", "SOLVER_MAPPING_ONLY"]
    if has_solver_mapping:
        return "SOLVER_INPUT_ASSEMBLABLE", ["SOLVER_MAPPING_ONLY"]
    if qku_type == "FORMULA_QKU" and has_formula_binding:
        return "FORMULA_EXECUTABLE", []
    if qku_type == "ALGORITHM_QKU" and has_algorithm_binding:
        return "ALGORITHM_EXECUTABLE", []
    if qku_type == "CONSTRAINT_QKU" and has_formula_binding:
        return "CONSTRAINT_EXECUTABLE", []
    if qku_type == "RISK_QKU" and has_formula_binding:
        return "OBJECTIVE_EXECUTABLE", ["FORMULA_EXECUTABLE"]
    if qku_type in {"PARAMETER_QKU", "RANGE_QKU", "DEFAULT_VALUE_QKU", "OPTIMIZER_SETTING_QKU"}:
        return "PARAMETER_VALUE_MATERIALIZED", ["PARAMETER_ONLY"]
    if qku_type == "ATOMICROW_QKU":
        return "FEATURE_COMPUTABLE", ["FEATURE_ONLY"]
    if qku_type == "AGENT_BINDING_QKU":
        return "AGENT_ROUTE_ONLY", ["GOVERNANCE_ONLY"]
    if qku_type in {"CAPITAL_QKU", "LATENCY_QKU", "STRATEGY_TEMPLATE_QKU"}:
        return "GOVERNANCE_ONLY", []
    return "METADATA_ONLY_BLOCKED", []


def _input_fields_for_qku(qku: dict[str, Any], market_record: dict[str, Any]) -> list[str]:
    qku_type = str(qku.get("qku_type") or "")
    scope = market_record["primary_market_scope"]
    if scope == "FUTURES" or scope == "UNKNOWN_MARKET_SCOPE":
        return []
    if qku_type == "ATOMICROW_QKU" or scope == "PREDICTION_MARKET_BINARY_EVENT_CONTRACT":
        return list(c.PREDICTION_MARKET_INPUT_FIELDS)
    if scope in c.STAGE1_ALLOWED_MARKET_SCOPES:
        return [
            "yes_price",
            "no_price",
            "yes_bid",
            "yes_ask",
            "volume",
            "liquidity",
            "fee_model_candidate",
        ]
    return []


def _output_fields_for_qku(qku: dict[str, Any]) -> list[str]:
    qku_type = str(qku.get("qku_type") or "")
    return {
        "FORMULA_QKU": ["formula_output_candidate"],
        "ALGORITHM_QKU": ["algorithm_output_candidate"],
        "CONSTRAINT_QKU": ["constraint_status_candidate"],
        "PARAMETER_QKU": ["parameter_value_candidate"],
        "RANGE_QKU": ["parameter_range_candidate"],
        "DEFAULT_VALUE_QKU": ["default_value_candidate"],
        "ATOMICROW_QKU": ["feature_value_candidate"],
        "RISK_QKU": ["risk_control_candidate"],
        "CAPITAL_QKU": ["capital_control_candidate"],
        "LATENCY_QKU": ["latency_control_candidate"],
        "OPTIMIZER_SETTING_QKU": ["optimizer_input_candidate"],
        "AGENT_BINDING_QKU": ["agent_route_candidate"],
        "STRATEGY_TEMPLATE_QKU": ["strategy_template_candidate"],
    }.get(qku_type, ["metadata_classification_candidate"])


def _agent_consumers_for_role(trade_role: str) -> list[str]:
    if trade_role in {"RISK_CONTROL"}:
        return ["QTT_RISK_AGENT", "QTT_PARAMETER_STACK_AGENT"]
    if trade_role in {"CAPITAL_ALLOCATION"}:
        return ["QTT_CAPITAL_AGENT", "QTT_PARAMETER_STACK_AGENT"]
    if trade_role in {"LATENCY_CONTROL"}:
        return ["QTT_LATENCY_AGENT"]
    if trade_role in {"QUANTUM_SOLVER_MAPPING", "QUANTUM_OPTIMIZER_INPUT"}:
        return ["QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"]
    if trade_role in {"OWNER_REVIEW_GOVERNANCE", "SOURCE_EVIDENCE_GOVERNANCE"}:
        return ["QTT_OWNER_REVIEW_AGENT", "QTT_GOVERNANCE_AGENT"]
    return ["QTT_REPLAY_AGENT", "QTT_PAPER_AGENT", "QTT_RESEARCH_AGENT"]


def _blocker_code(primary_execution_class: str, dormancy: str, live_status: str) -> str:
    if dormancy == "NOT_DORMANT_STAGE1_ACTIVE":
        return "PR162B_BLOCKED_NO_REPLAY_PAPER_EVIDENCE"
    if dormancy == "DORMANT_NON_STAGE1_MARKET_SPECIFIC":
        return "PR162B_BLOCKED_NON_STAGE1_MARKET_SCOPE"
    if dormancy == "DORMANT_UNKNOWN_MARKET_SCOPE":
        return "PR162B_BLOCKED_UNKNOWN_MARKET_SCOPE"
    if dormancy == "DORMANT_METADATA_ONLY" or primary_execution_class == "METADATA_ONLY_BLOCKED":
        return "PR162B_BLOCKED_METADATA_ONLY"
    if live_status == "LIVE_BLOCKED_NO_INPUT_BINDING":
        return "PR162B_BLOCKED_NO_INPUT_FIELD_BINDING"
    return "PR162B_BLOCKED_OWNER_REVIEW_REQUIRED"


def execution_classification_records(
    qkus: list[dict[str, Any]],
    market_records: list[dict[str, Any]],
    formula_binding_refs: dict[str, list[str]],
    algorithm_binding_refs: dict[str, list[str]],
    solver_mapping_refs: dict[str, list[str]],
    pr162a_mappings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_market = {record["qku_id"]: record for record in market_records}
    by_mapping = {record["qku_id"]: record for record in pr162a_mappings}
    return [
        classify_execution(
            qku,
            by_market[qku["qku_id"]],
            formula_binding_refs,
            algorithm_binding_refs,
            solver_mapping_refs,
            by_mapping,
        )
        for qku in qkus
    ]
