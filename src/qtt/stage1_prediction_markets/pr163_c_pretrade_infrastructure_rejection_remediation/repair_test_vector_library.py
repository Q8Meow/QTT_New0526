"""Executable test vectors for PR163-C formulas."""

from __future__ import annotations

from typing import Any

from .repair_formula_library import apply_formula


TEST_VECTORS: dict[str, dict[str, Any]] = {
    "PR163C_TEST_VECTOR::FEE_COMPONENT": {
        "formula_ref": "PR163C_FORMULA::FEE_COMPONENT",
        "inputs": {"notional": 100.0, "fixed_fee": 0.02, "percentage_fee": 0.01, "fee_cap": 2.0},
        "expected_output": 1.02,
    },
    "PR163C_TEST_VECTOR::EXPECTED_SLIPPAGE_BPS": {
        "formula_ref": "PR163C_FORMULA::EXPECTED_SLIPPAGE_BPS",
        "inputs": {"spread_bps": 20.0, "impact_proxy": 3.0, "adverse_selection_penalty": 2.0},
        "expected_output": 15.0,
    },
    "PR163C_TEST_VECTOR::LATENCY_STALE_DATA_COST": {
        "formula_ref": "PR163C_FORMULA::LATENCY_STALE_DATA_COST",
        "inputs": {"expected_price_move_per_ms": 0.0002, "latency_ms": 50.0, "stale_data_penalty": 0.01},
        "expected_output": 0.02,
    },
    "PR163C_TEST_VECTOR::FILL_PROBABILITY": {
        "formula_ref": "PR163C_FORMULA::FILL_PROBABILITY",
        "inputs": {"order_size_to_depth_ratio": 0.25, "adverse_selection_penalty": 0.04},
        "expected_output": 0.81,
    },
    "PR163C_TEST_VECTOR::EXPECTED_NET_PROFIT_CANDIDATE": {
        "formula_ref": "PR163C_FORMULA::EXPECTED_NET_PROFIT_CANDIDATE",
        "inputs": {
            "gross_edge_candidate": 10.0,
            "exchange_fee_component": 1.0,
            "spread_cross_component": 1.0,
            "slippage_component": 1.0,
            "latency_adverse_selection_component": 1.0,
            "queue_nonfill_opportunity_cost_component": 1.0,
            "cancel_replace_component": 0.25,
            "capital_lock_component": 0.25,
            "settlement_delay_component": 0.25,
            "stale_data_penalty_component": 0.25,
            "operational_error_component": 0.5,
        },
        "expected_output": 3.5,
    },
    "PR163C_TEST_VECTOR::IMPLEMENTATION_SHORTFALL": {
        "formula_ref": "PR163C_FORMULA::IMPLEMENTATION_SHORTFALL",
        "inputs": {"arrival_price_candidate": 0.45, "simulated_execution_price": 0.46, "side_multiplier": 1.0},
        "expected_output": 0.01,
    },
    "PR163C_TEST_VECTOR::TICK_SIZE_QUANTIZE": {
        "formula_ref": "PR163C_FORMULA::TICK_SIZE_QUANTIZE",
        "inputs": {"price": 0.437, "tick_size": 0.01},
        "expected_output": 0.44,
    },
    "PR163C_TEST_VECTOR::VENUE_PRICE_NORMALIZE": {
        "formula_ref": "PR163C_FORMULA::VENUE_PRICE_NORMALIZE",
        "inputs": {"raw_price": 43.0, "price_scale": 0.01},
        "expected_output": 0.43,
    },
}


def test_vector_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for vector_ref in sorted(TEST_VECTORS):
        vector = TEST_VECTORS[vector_ref]
        actual = apply_formula(vector["formula_ref"], vector["inputs"])
        rows.append(
            {
                "test_vector_ref": vector_ref,
                "formula_ref": vector["formula_ref"],
                "inputs": vector["inputs"],
                "expected_output": vector["expected_output"],
                "actual_output": actual,
                "test_vector_passed": actual == vector["expected_output"],
                "validation_status": "PASS" if actual == vector["expected_output"] else "FAIL",
            }
        )
    return rows
