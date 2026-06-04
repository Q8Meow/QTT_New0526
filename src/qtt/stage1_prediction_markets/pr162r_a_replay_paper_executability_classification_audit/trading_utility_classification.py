"""Trading utility class assignment."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def trading_utility_class(record: dict[str, Any]) -> str:
    ctype = candidate_type(record)
    family = " ".join(
        str(record.get(key) or "")
        for key in ("algorithm_family", "formula_category", "formula_family", "parameter_family", "quantum_family", "dataset_family")
    ).lower()
    if ctype == "QUANTUM":
        return "QUANTUM_CLASSICAL_COMPARATOR_INPUT"
    if any(token in family for token in ("qubo", "ising", "bqm", "cqm", "qaoa", "vqe", "annealing", "quantum")):
        return "QUANTUM_OPTIMIZER_INPUT"
    if any(token in family for token in ("calibration", "brier", "log_loss", "probability_clip")):
        return "PROBABILITY_CALIBRATION_FEATURE"
    if any(token in family for token in ("spread", "orderbook", "depth", "candle", "volume", "microstructure", "dataset")):
        return "MARKET_MICROSTRUCTURE_FEATURE"
    if any(token in family for token in ("kelly", "risk", "var", "cvar", "drawdown", "slippage", "latency")):
        return "RISK_SIZING_FEATURE"
    if any(token in family for token in ("portfolio", "variance", "weight", "capital", "sharpe")):
        return "CAPITAL_ALLOCATION_FEATURE"
    if ctype == "PARAMETER":
        return "PARAMETER_STACK_SELECTION_FEATURE"
    return "EXPECTED_VALUE_FEATURE"


def trading_utility_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_id(record),
            "candidate_type": candidate_type(record),
            "trading_utility_class": trading_utility_class(record),
            "profit_evidence_claim_flag": False,
            "live_order_authority": False,
        }
        for record in records
    ]
