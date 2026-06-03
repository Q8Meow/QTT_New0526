"""Algorithm, objective, constraint, and solver expansion from PR162B."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization import (
    algorithm_registry as pr162b_algorithm_registry,
    formula_registry as pr162b_formula_registry,
)

from . import constants as c
from .deterministic_id import deterministic_id


def expanded_algorithm_records(repo_root: Path | None = None) -> list[dict[str, Any]]:
    del repo_root
    records: list[dict[str, Any]] = []
    for algorithm in pr162b_algorithm_registry.algorithm_records():
        records.append(
            {
                "candidate_id": deterministic_id(
                    "PR162D-ALGORITHM-CANDIDATE", algorithm["algorithm_id"]
                ),
                "stable_deterministic_id_inputs": [
                    algorithm["algorithm_id"],
                    algorithm["algorithm_name"],
                ],
                "qku_refs": algorithm.get("qku_refs") or ["PR162D_CANDIDATE_QKU_BACKLOG"],
                "formula_refs": algorithm.get("formula_refs") or [],
                "algorithm_refs": [algorithm["algorithm_id"]],
                "source_refs": ["PR162B_LOCAL_DETERMINISTIC_ALGORITHM_CONTRACT"],
                "source_tier": "TIER_0",
                "source_class": "REPO_LOCAL_OWNER_PROVIDED",
                "source_quality_score": 0.92,
                "authority_class": "REPO_LOCAL_CANDIDATE_NOT_LIVE_TRUTH",
                "confidence_class": "HIGH_OFFICIAL_LOCATOR",
                "expression": "deterministic algorithm candidate: " + algorithm["algorithm_name"],
                "executable_function_reference_or_planned_function_reference": (
                    f"{algorithm['implementation_module']}.{algorithm['implementation_function']}"
                ),
                "input_fields": algorithm["input_fields"],
                "output_fields": algorithm["output_fields"],
                "units": "unitless",
                "default_value_candidate": None,
                "range_min_candidate": None,
                "range_max_candidate": None,
                "scale_class": "algorithm_output_native_scale",
                "normalization_rule": "validate inputs before candidate runtime execution",
                "missing_input_behavior": "candidate_remains_partial_and_routes_to_replay_paper",
                "test_vector_refs": algorithm["test_vector_refs"],
                "replay_paper_route_refs": ["PR162D_REPLAY_PAPER_CANDIDATE_ROUTER"],
                "agent_route_refs": [
                    "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE",
                    "PARAMETER_STACK_AGENT",
                    "REPLAY_PAPER_CANDIDATE_ROUTER",
                ],
                "official_truth_flag": False,
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": True,
                "metadata_only_flag": False,
                "computable_candidate_flag": True,
                "live_order_authority": False,
                "created_by_pr": c.PR_ID,
            }
        )
    return records


def objective_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return pr162b_formula_registry.objective_records(_back_to_pr162b_formulas(formulas))


def constraint_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return pr162b_formula_registry.constraint_records(_back_to_pr162b_formulas(formulas))


def _back_to_pr162b_formulas(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {record["formula_id"]: record for record in pr162b_formula_registry.formula_records()}
    output = []
    for record in records:
        for formula_ref in record.get("formula_refs") or []:
            if formula_ref in by_id:
                output.append(by_id[formula_ref])
    return output
