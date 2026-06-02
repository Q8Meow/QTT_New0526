"""PR162C QTT agent routing records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def executable_qku_agent_route_records(qku_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for record in qku_records:
        output.append(
            {
                "route_id": f"PR162C-QKU-AGENT-ROUTE-{record['qku_id']}",
                "qku_id": record["qku_id"],
                "formula_refs": record["formula_refs"],
                "value_refs": record["parameter_refs"] + record["tradable_value_refs"],
                "dataset_refs": list(c.DATASET_IDS),
                "source_refs": ["PR162C_SourcePortfolioRegistry.report.json"],
                "upstream_pr_artifacts": record["upstream_artifact_refs"],
                "downstream_pr_artifacts": record["downstream_artifact_refs"],
                "allowed_agent_actions": _allowed_actions(record),
                "forbidden_agent_actions": _forbidden_actions(record),
                "replay_paper_route": "PR162R_ADAPTER_RERUN_AFTER_STRICT_DATASETS",
                "owner_review_route": "QTT_OWNER_REVIEW_AGENT",
                "dormant_blocker_route": record["blocker_code"]
                if str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_")
                else None,
                "qtt_agent_consumer_routes": record["qtt_agent_consumer_routes"],
                "created_by_pr": c.PR_ID,
            }
        )
    return output


def dataset_agent_route_records(dataset_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "route_id": f"PR162C-DATASET-AGENT-ROUTE-{record['dataset_id']}",
            "dataset_id": record["dataset_id"],
            "allowed_agent_actions": [
                "read_candidate_metadata",
                "request_owner_materialization",
                "prepare_replay_paper_inputs_after_strict_gate",
            ],
            "forbidden_agent_actions": list(_base_forbidden_actions()),
            "qtt_agent_consumer_routes": [
                "QTT_RESEARCH_AGENT",
                "QTT_SOURCE_EVIDENCE_AGENT",
                "QTT_REPLAY_AGENT",
                "QTT_PAPER_AGENT",
                "QTT_OWNER_REVIEW_AGENT",
            ],
            "created_by_pr": c.PR_ID,
        }
        for record in dataset_records
        if "dataset_id" in record
    ]


def formula_to_agent_route_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for formula in formulas:
        for agent in formula.get("qtt_agent_consumer_route") or ["QTT_RESEARCH_AGENT"]:
            output.append(
                {
                    "route_id": f"PR162C-FORMULA-AGENT-ROUTE-{formula['formula_id']}-{agent}",
                    "formula_ref": formula["formula_id"],
                    "agent_id": agent,
                    "allowed_agent_actions": ["read_candidate_formula", "execute_test_vector_locally"],
                    "forbidden_agent_actions": list(_base_forbidden_actions()),
                    "created_by_pr": c.PR_ID,
                }
            )
    return output


def _allowed_actions(record: dict[str, Any]) -> list[str]:
    actions = ["read_candidate_metadata", "route_owner_materialization_blocker"]
    if record["primary_execution_class"] != "METADATA_ONLY_BLOCKED":
        actions.append("execute_local_formula_test_vectors")
    return actions


def _forbidden_actions(record: dict[str, Any]) -> list[str]:
    actions = list(_base_forbidden_actions())
    if record["primary_execution_class"] == "METADATA_ONLY_BLOCKED":
        actions.append("treat_metadata_only_as_executable")
    if str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_"):
        actions.append("route_dormant_qku_to_execution_router")
    return actions


def _base_forbidden_actions() -> tuple[str, ...]:
    return (
        "create_live_order",
        "fetch_private_account_state",
        "emit_replay_paper_result",
        "emit_profit_evidence",
        "run_quantum_backend_or_simulator",
        "promote_result_backed_ranking",
    )
