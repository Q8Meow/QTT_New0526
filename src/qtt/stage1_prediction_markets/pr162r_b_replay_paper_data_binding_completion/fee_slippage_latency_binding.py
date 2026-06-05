"""Fee, slippage, and latency binding registry builders."""

from __future__ import annotations

from typing import Any


FEE_SLIPPAGE_LATENCY_FAMILIES = (
    "FEE_MODEL",
    "SLIPPAGE_MODEL",
    "LATENCY_OBSERVATION_SERIES",
    "STALENESS_AND_FRESHNESS_INPUTS",
    "PAPER_EXECUTION_COST_MODEL",
)


def build_fee_slippage_latency_bindings(dataset_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for binding in dataset_bindings:
        if binding["binding_family"] not in FEE_SLIPPAGE_LATENCY_FAMILIES:
            continue
        rows.append(
            {
                **binding,
                "binding_id": f"PR162R_B_FEE_SLIPPAGE_LATENCY_BINDING::{len(rows) + 1:04d}",
                "dataset_binding_ref": binding["binding_id"],
                "fee_model_ref": "synthetic_fee_slippage_model.fixture.json",
                "slippage_model_ref": "synthetic_fee_slippage_model.fixture.json",
                "latency_observation_ref": "synthetic_latency_observations.fixture.jsonl",
                "latency_classification": [
                    "PRECOMPUTE_REQUIRED",
                    "BENCHMARK_REQUIRED_BEFORE_LIVE",
                    "NOT_LIVE_ELIGIBLE_IN_THIS_PR",
                ],
                "hot_path_rule": "no optimizer, quantum, LLM, source retrieval, or live connector in hot order path",
                "validation_status": "PASS",
            }
        )
    return rows
