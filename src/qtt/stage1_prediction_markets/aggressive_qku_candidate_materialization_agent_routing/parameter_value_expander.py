"""Parameter, range, tradable value, and solver-input candidate expansion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization import (
    formula_registry as pr162b_formula_registry,
)

from .deterministic_id import deterministic_id
from .preflight_reader import load_report_records


def expanded_parameter_value_records(repo_root: Path) -> list[dict[str, Any]]:
    base = load_report_records(repo_root, "docs/master_plan/generated/PR162B_QKUParameterValueRegistry.report.json")
    records = []
    for record in base or pr162b_formula_registry.parameter_value_records():
        records.append(
            {
                "candidate_id": deterministic_id("PR162D-PARAMETER-CANDIDATE", record["parameter_id"]),
                "parameter_ref": record["parameter_id"],
                "parameter_name": record["parameter_name"],
                "qku_refs": record.get("qku_refs") or ["PR162D_PARAMETER_QKUS"],
                "formula_refs": record.get("formula_refs") or [],
                "algorithm_refs": record.get("algorithm_refs") or [],
                "source_refs": [record.get("source_locator", "OWNER_PR162D_DIRECTIVE")],
                "source_tier": "TIER_0",
                "source_class": "OWNER_PROVIDED_INTERNAL_CANDIDATE",
                "source_quality_score": 0.92,
                "authority_class": "OWNER_APPROVED_INTERNAL_CANDIDATE_NOT_EXTERNAL_FACT",
                "confidence_class": "LOW_OWNER_DEFAULT_CANDIDATE",
                "expression": f"default candidate {record['parameter_name']} = {record['candidate_value']}",
                "executable_function_reference_or_planned_function_reference": "PR162D_PARAMETER_STACK_AGENT_VALUE_BINDING",
                "input_fields": ["parameter_context"],
                "output_fields": [record["parameter_name"]],
                "units": record["unit"],
                "default_value_candidate": record["candidate_value"],
                "range_min_candidate": record["candidate_range"][0],
                "range_max_candidate": record["candidate_range"][1],
                "scale_class": record["scale"],
                "normalization_rule": "parameter value remains replay/paper candidate until validated",
                "missing_input_behavior": "use candidate default only in replay/paper candidate mode",
                "test_vector_refs": [],
                "replay_paper_route_refs": ["PR162D_REPLAY_PAPER_CANDIDATE_ROUTER"],
                "agent_route_refs": ["PARAMETER_STACK_AGENT", "RISK_MANAGER_CANDIDATE_REVIEW"],
                "official_truth_flag": False,
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": True,
                "metadata_only_flag": False,
                "live_order_authority": False,
            }
        )
    return records


def expanded_range_scale_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "range_scale_id": record["candidate_id"].replace("PARAMETER-CANDIDATE", "PARAMETER-RANGE-SCALE"),
            "parameter_candidate_ref": record["candidate_id"],
            "parameter_name": record["parameter_name"],
            "range_min_candidate": record["range_min_candidate"],
            "range_max_candidate": record["range_max_candidate"],
            "scale_class": record["scale_class"],
            "units": record["units"],
            "live_order_authority": False,
        }
        for record in parameters
    ]


def tradable_value_candidate_records(parameters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "tradable_value_candidate_id": record["candidate_id"].replace("PARAMETER-CANDIDATE", "TRADABLE-VALUE"),
            "parameter_candidate_ref": record["candidate_id"],
            "candidate_value": record["default_value_candidate"],
            "units": record["units"],
            "replay_paper_candidate_flag": True,
            "order_authority_flag": False,
            "live_order_authority": False,
        }
        for record in parameters
    ]


def solver_input_assembly_records(repo_root: Path) -> list[dict[str, Any]]:
    base = load_report_records(repo_root, "docs/master_plan/generated/PR162B_QKUSolverMappingRegistry.report.json")
    output = []
    for record in base[:250]:
        output.append(
            {
                "solver_input_candidate_id": deterministic_id(
                    "PR162D-SOLVER-INPUT", record["solver_mapping_id"]
                ),
                "qku_id": record["qku_id"],
                "solver_mapping_ref": record["solver_mapping_id"],
                "formula_refs": record.get("formula_refs") or [],
                "algorithm_refs": record.get("algorithm_refs") or [],
                "input_representation": record.get("input_representation"),
                "compatible_solver_family": record.get("compatible_solver_family"),
                "candidate_solver_input_ready_flag": True,
                "smoke_execution_allowed_flag": bool(record.get("smoke_execution_allowed_flag")),
                "live_execution_allowed_flag": False,
                "replay_paper_candidate_flag": True,
            }
        )
    return output
