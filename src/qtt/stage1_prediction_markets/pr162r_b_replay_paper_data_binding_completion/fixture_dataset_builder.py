"""Create deterministic non-live PR162R-B fixture datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import write_json, write_jsonl


TRUTH = "SYNTHETIC_TEST_FIXTURE"


def write_fixture_datasets(repo_root: Path) -> list[dict[str, Any]]:
    fixtures: dict[str, Any] = {
        "synthetic_binary_market_orderbook_1s.fixture.jsonl": _orderbook_rows(),
        "synthetic_binary_market_trade_prints.fixture.jsonl": _trade_rows(),
        "synthetic_event_state_timeline.fixture.jsonl": _event_rows(),
        "synthetic_settlement_labels.fixture.jsonl": _settlement_rows(),
        "synthetic_fee_slippage_model.fixture.json": _fee_slippage_model(),
        "synthetic_latency_observations.fixture.jsonl": _latency_rows(),
        "synthetic_paper_market_state.fixture.json": _paper_market_state(),
        "synthetic_paper_portfolio_state.fixture.json": _paper_portfolio_state(),
        "synthetic_paper_open_orders.fixture.json": _paper_open_orders(),
        "synthetic_paper_fill_events.fixture.jsonl": _paper_fill_rows(),
        "synthetic_quantum_objective_inputs.fixture.json": _quantum_objective_inputs(),
        "synthetic_quantum_constraints.fixture.json": _quantum_constraints(),
        "synthetic_classical_comparator_inputs.fixture.json": _classical_comparator_inputs(),
    }
    records: list[dict[str, Any]] = []
    for index, filename in enumerate(p.FIXTURE_FILENAMES, start=1):
        payload = fixtures[filename]
        path = p.fixture_path(repo_root, filename)
        if filename.endswith(".jsonl"):
            write_jsonl(path, payload)
            row_count = len(payload)
        else:
            write_json(path, payload)
            row_count = 1
        records.append(
            {
                "fixture_id": f"PR162R_B_FIXTURE::{index:03d}",
                "fixture_filename": filename,
                "repo_local_path": (p.FIXTURE_DIR / filename).as_posix(),
                "fixture_truth_status": TRUTH,
                "row_count": row_count,
                "deterministic_timestamps": True,
                "live_authority": False,
                "profit_evidence": False,
                "source_acceptance": False,
                "connector_binding": False,
                "validation_status": "PASS",
            }
        )
    return records


def _base_meta() -> dict[str, Any]:
    return {
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "fixture_truth_status": TRUTH,
        "live_authority": False,
        "profit_evidence": False,
        "source_acceptance": False,
        "connector_binding": False,
    }


def _orderbook_rows() -> list[dict[str, Any]]:
    rows = []
    for i in range(6):
        bid = round(0.41 + i * 0.01, 4)
        ask = round(bid + 0.04, 4)
        rows.append(
            {
                **_base_meta(),
                "market_id": "PR162R_B_SYNTH_MARKET_001",
                "event_id": "PR162R_B_SYNTH_EVENT_001",
                "outcome_id": "YES",
                "source_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
                "observation_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
                "best_bid": bid,
                "best_ask": ask,
                "bid_top_size": 100 + i * 10,
                "ask_top_size": 120 + i * 10,
                "bid_depth": 500 + i * 20,
                "ask_depth": 540 + i * 20,
            }
        )
    return rows


def _trade_rows() -> list[dict[str, Any]]:
    return [
        {
            **_base_meta(),
            "market_id": "PR162R_B_SYNTH_MARKET_001",
            "event_id": "PR162R_B_SYNTH_EVENT_001",
            "outcome_id": "YES",
            "trade_id": f"PR162R_B_SYNTH_TRADE_{i:03d}",
            "source_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
            "observation_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
            "side": "BUY" if i % 2 else "SELL",
            "price": round(0.43 + i * 0.01, 4),
            "size": 10 + i,
        }
        for i in range(1, 6)
    ]


def _event_rows() -> list[dict[str, Any]]:
    states = ("CREATED", "OPEN", "PAUSED", "OPEN", "CLOSED", "SETTLED")
    return [
        {
            **_base_meta(),
            "event_id": "PR162R_B_SYNTH_EVENT_001",
            "market_id": "PR162R_B_SYNTH_MARKET_001",
            "source_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
            "event_lifecycle_state": state,
        }
        for i, state in enumerate(states)
    ]


def _settlement_rows() -> list[dict[str, Any]]:
    return [
        {
            **_base_meta(),
            "event_id": "PR162R_B_SYNTH_EVENT_001",
            "market_id": "PR162R_B_SYNTH_MARKET_001",
            "outcome_id": "YES",
            "resolution_timestamp_utc": "2026-01-01T00:00:05Z",
            "settlement_outcome_label": "YES",
            "payout": 1.0,
        }
    ]


def _fee_slippage_model() -> dict[str, Any]:
    return {
        **_base_meta(),
        "model_id": "PR162R_B_SYNTH_FEE_SLIPPAGE_MODEL_001",
        "maker_fee_per_share": 0.001,
        "taker_fee_per_share": 0.002,
        "expected_slippage_per_share": 0.003,
        "latency_bucket_slippage": {"LOW": 0.001, "MEDIUM": 0.003, "HIGH": 0.006},
    }


def _latency_rows() -> list[dict[str, Any]]:
    return [
        {
            **_base_meta(),
            "market_id": "PR162R_B_SYNTH_MARKET_001",
            "source_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
            "observation_timestamp_utc": f"2026-01-01T00:00:0{i}Z",
            "latency_seconds": round(0.02 + i * 0.01, 4),
            "latency_bucket": "LOW" if i < 2 else "MEDIUM" if i < 4 else "HIGH",
        }
        for i in range(6)
    ]


def _paper_market_state() -> dict[str, Any]:
    return {
        **_base_meta(),
        "paper_market_state_id": "PR162R_B_PAPER_MARKET_STATE_001",
        "market_id": "PR162R_B_SYNTH_MARKET_001",
        "event_lifecycle_state": "OPEN",
        "best_bid": 0.46,
        "best_ask": 0.50,
        "bid_depth": 620,
        "ask_depth": 660,
        "observation_timestamp_utc": "2026-01-01T00:00:05Z",
    }


def _paper_portfolio_state() -> dict[str, Any]:
    return {
        **_base_meta(),
        "paper_portfolio_state_id": "PR162R_B_PAPER_PORTFOLIO_001",
        "paper_cash": 10000.0,
        "positions": [{"market_id": "PR162R_B_SYNTH_MARKET_001", "outcome_id": "YES", "quantity": 0}],
        "runtime_cash_receipt": False,
        "private_state": False,
    }


def _paper_open_orders() -> dict[str, Any]:
    return {
        **_base_meta(),
        "paper_open_order_state_id": "PR162R_B_PAPER_OPEN_ORDERS_001",
        "open_orders": [
            {
                "paper_order_id": "PR162R_B_PAPER_ORDER_001",
                "market_id": "PR162R_B_SYNTH_MARKET_001",
                "side": "BUY",
                "limit_price": 0.47,
                "remaining_size": 25,
                "order_authority": False,
            }
        ],
    }


def _paper_fill_rows() -> list[dict[str, Any]]:
    return [
        {
            **_base_meta(),
            "paper_fill_event_id": f"PR162R_B_PAPER_FILL_{i:03d}",
            "paper_order_id": "PR162R_B_PAPER_ORDER_001",
            "market_id": "PR162R_B_SYNTH_MARKET_001",
            "side": "BUY",
            "limit_price": 0.47,
            "fill_price": round(0.465 + i * 0.001, 4),
            "filled_size": 5,
            "missed_size": 0 if i < 3 else 5,
            "partial_fill": i >= 3,
            "stale_quote_rejected": False,
        }
        for i in range(1, 5)
    ]


def _quantum_objective_inputs() -> dict[str, Any]:
    return {
        **_base_meta(),
        "quantum_input_id": "PR162R_B_QUANTUM_OBJECTIVE_001",
        "expected_value_vector": [0.03, 0.04, 0.02],
        "probability_vector": [0.54, 0.61, 0.48],
        "cost_adjusted_price_vector": [0.49, 0.55, 0.44],
        "risk_vector": [0.12, 0.16, 0.10],
        "covariance_matrix": [[0.04, 0.01, 0.0], [0.01, 0.05, 0.01], [0.0, 0.01, 0.03]],
        "correlation_matrix": [[1.0, 0.2, 0.0], [0.2, 1.0, 0.15], [0.0, 0.15, 1.0]],
        "liquidity_depth_vector": [500, 420, 380],
        "settlement_risk_vector": [0.02, 0.03, 0.01],
        "objective_scale": 1.0,
    }


def _quantum_constraints() -> dict[str, Any]:
    return {
        **_base_meta(),
        "quantum_constraint_id": "PR162R_B_QUANTUM_CONSTRAINT_001",
        "capital_budget": 1000.0,
        "position_size_limit": 100.0,
        "drawdown_limit": 0.08,
        "exposure_limit": 0.25,
        "venue_eligibility_vector": [1, 1, 0],
        "latency_window": "BATCH_ONLY",
        "variable_domain_map": {"x0": "BINARY", "x1": "BINARY", "x2": "BINARY"},
        "constraint_matrix_or_terms": [[1, 1, 1], [0.49, 0.55, 0.44]],
        "penalty_weights": {"budget": 3.0, "exposure": 2.0, "liquidity": 1.0},
    }


def _classical_comparator_inputs() -> dict[str, Any]:
    return {
        **_base_meta(),
        "classical_comparator_input_id": "PR162R_B_CLASSICAL_COMPARATOR_001",
        "expected_value": 0.035,
        "transaction_cost_estimate": 0.005,
        "risk_score": 0.14,
        "liquidity_score": 0.82,
        "staleness_seconds": 0.0,
    }
