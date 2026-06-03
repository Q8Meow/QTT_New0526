"""Formula expression catalog expansion from PR162B into PR162D candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization import (
    formula_registry as pr162b_formula_registry,
)

from . import constants as c
from .deterministic_id import deterministic_id
from .source_quality_policy import authority_for_source, confidence_for_source, source_quality_score


def _tier_for_source_class(source_class: str) -> str:
    if source_class.startswith("OFFICIAL_VENUE"):
        return "TIER_1"
    if source_class.startswith("OFFICIAL_LIBRARY"):
        return "TIER_2"
    if source_class.startswith("TEXTBOOK") or source_class.startswith("INSTITUTIONAL"):
        return "TIER_2"
    if source_class.startswith("OPEN_SOURCE"):
        return "TIER_3"
    if source_class.startswith("RESEARCH"):
        return "TIER_3"
    return "TIER_0"


def expanded_formula_records(repo_root: Path | None = None) -> list[dict[str, Any]]:
    del repo_root
    records: list[dict[str, Any]] = []
    for formula in pr162b_formula_registry.formula_records():
        source_class = str(formula["source_class"])
        source_tier = _tier_for_source_class(source_class)
        official = source_class.startswith("OFFICIAL")
        records.append(
            {
                "candidate_id": deterministic_id("PR162D-FORMULA-CANDIDATE", formula["formula_id"]),
                "stable_deterministic_id_inputs": [formula["formula_id"], formula["formula_name"]],
                "qku_refs": formula.get("qku_refs") or ["PR162D_CANDIDATE_QKU_BACKLOG"],
                "formula_refs": [formula["formula_id"]],
                "algorithm_refs": [],
                "source_refs": [formula["source_locator"]],
                "source_tier": source_tier,
                "source_class": source_class,
                "source_quality_score": source_quality_score(source_tier, official),
                "authority_class": authority_for_source(source_tier, source_class),
                "confidence_class": confidence_for_source(source_tier, source_class),
                "expression": formula["mathematical_expression_latex"],
                "executable_function_reference_or_planned_function_reference": (
                    f"{formula['implementation_module']}.{formula['implementation_function']}"
                ),
                "input_fields": formula["input_fields"],
                "output_fields": formula["output_fields"],
                "units": formula["units"],
                "default_value_candidate": None,
                "range_min_candidate": None,
                "range_max_candidate": None,
                "scale_class": "formula_output_native_scale",
                "normalization_rule": formula.get("normalization_policy"),
                "missing_input_behavior": "candidate_remains_partial_and_routes_to_replay_paper",
                "test_vector_refs": formula["test_vector_refs"],
                "replay_paper_route_refs": ["PR162D_REPLAY_PAPER_CANDIDATE_ROUTER"],
                "agent_route_refs": [
                    "QKU_FORMULA_COMPUTE_ENGINE",
                    "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE",
                    "FEATURE_BUILDER",
                ],
                "official_truth_flag": official,
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": True,
                "metadata_only_flag": False,
                "computable_candidate_flag": True,
                "live_order_authority": False,
                "created_by_pr": c.PR_ID,
            }
        )
    return records
