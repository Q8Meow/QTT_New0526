"""PR162C canonical QKU execution classification."""

from __future__ import annotations

from typing import Any

from . import constants as c


def execution_classification_records(pr162b_execution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-QKU-EXECUTION-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "source_pr162b_execution_class": record["primary_execution_class"],
            "primary_execution_class": _map_execution_class(record["primary_execution_class"]),
            "primary_market_scope": record["primary_market_scope"],
            "compatible_market_scopes": record["compatible_market_scopes"],
            "excluded_market_scopes": [
                scope for scope in c.MARKET_SCOPES if scope not in record["compatible_market_scopes"]
            ],
            "stage1_prediction_market_activation_status": record[
                "stage1_prediction_market_activation_status"
            ],
            "dormancy_status": record["dormancy_status"],
            "qku_trade_role": record.get("trade_role", "UNKNOWN_ROLE"),
            "formula_refs": record.get("formula_refs") or [],
            "algorithm_refs": record.get("algorithm_refs") or [],
            "objective_refs": record.get("objective_refs") or [],
            "constraint_refs": record.get("constraint_refs") or [],
            "parameter_refs": record.get("parameter_refs") or [],
            "tradable_value_refs": record.get("tradable_value_refs") or [],
            "solver_mapping_refs": record.get("solver_mapping_refs") or [],
            "required_input_fields": record.get("input_field_refs") or [],
            "output_field_definition": record.get("output_field_refs") or [],
            "qtt_agent_consumer_routes": _agent_routes(record),
            "upstream_artifact_refs": _upstream_refs(record),
            "downstream_artifact_refs": list(c.DOWNSTREAM_PR_ROUTES),
            "blocker_code": record.get("blocker_code", c.STATUS_BLOCKED_REQUIRED_FIELDS_MISSING),
            "created_by_pr": c.PR_ID,
        }
        for record in pr162b_execution
    ]


def _map_execution_class(pr162b_class: str) -> str:
    if pr162b_class in {"FORMULA_EXECUTABLE", "ALGORITHM_EXECUTABLE"}:
        return c.EXECUTION_COMPUTABLE
    if pr162b_class in {"PARAMETER_VALUE_MATERIALIZED", "PARAMETER_ONLY"}:
        return c.EXECUTION_PARAMETER_ONLY
    if pr162b_class in {"FEATURE_COMPUTABLE", "FEATURE_ONLY"}:
        return c.EXECUTION_FEATURE_ONLY
    if pr162b_class == "OBJECTIVE_EXECUTABLE":
        return c.EXECUTION_OBJECTIVE_BACKED
    if pr162b_class == "CONSTRAINT_EXECUTABLE":
        return c.EXECUTION_CONSTRAINT_BACKED
    if pr162b_class in {"SOLVER_INPUT_ASSEMBLABLE", "SOLVER_SMOKE_EXECUTABLE", "SOLVER_MAPPING_ONLY"}:
        return c.EXECUTION_SOLVER_BACKED
    return c.EXECUTION_METADATA_ONLY_BLOCKED


def _agent_routes(record: dict[str, Any]) -> list[str]:
    routes = set(record.get("agent_consumer_refs") or [])
    routes.update({"QTT_RESEARCH_AGENT", "QTT_REPLAY_AGENT", "QTT_PAPER_AGENT", "QTT_OWNER_REVIEW_AGENT"})
    if record.get("solver_mapping_refs"):
        routes.update({"QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"})
    if record.get("trade_role") in {"RISK_CONTROL"}:
        routes.add("QTT_RISK_AGENT")
    if record.get("trade_role") in {"CAPITAL_ALLOCATION"}:
        routes.add("QTT_CAPITAL_AGENT")
    if record.get("trade_role") in {"LATENCY_CONTROL"}:
        routes.add("QTT_LATENCY_AGENT")
    if record.get("primary_execution_class") != "METADATA_ONLY_BLOCKED":
        routes.add("QTT_PARAMETER_STACK_AGENT")
    return sorted(route for route in routes if route in c.QTT_AGENT_ROUTES)


def _upstream_refs(record: dict[str, Any]) -> list[str]:
    refs = []
    for key in (
        "upstream_atomicrows_refs",
        "upstream_pr161c_refs",
        "upstream_pr161d_refs",
        "upstream_pr161e_refs",
        "upstream_pr161f_refs",
        "upstream_pr162_refs",
        "upstream_pr162a_refs",
    ):
        refs.extend(ref for ref in record.get(key, []) if ref)
    refs.append("docs/master_plan/generated/PR162B_QKUExecutionClassificationAudit.report.json")
    return sorted(set(refs))
