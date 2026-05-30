"""Algorithm, formula, strategy, optimizer, and trading-role classifiers."""

from __future__ import annotations


def classify_algorithm_formula_strategy(record: dict[str, object]) -> dict[str, object]:
    text = " ".join(str(value or "") for value in record.values()).upper()
    algorithm_family = None
    formula_family = None
    strategy_family = None
    optimizer_family = None
    trading_role = "PARAMETER_STACK"
    if "QAOA" in text:
        algorithm_family = "QAOA"
        optimizer_family = "QUANTUM_OPTIMIZER"
    elif "VQE" in text:
        algorithm_family = "VQE"
        optimizer_family = "QUANTUM_OPTIMIZER"
    elif "ANNEAL" in text:
        algorithm_family = "ANNEALING"
        optimizer_family = "QUANTUM_OPTIMIZER"
    elif "OPTIMIZER" in text:
        optimizer_family = "CLASSICAL_OPTIMIZER"
    elif "ALGORITHM" in text:
        algorithm_family = "CLASSICAL_ALGORITHM"
    if "FORMULA" in text or "EXPRESSION" in text:
        formula_family = "CANDIDATE_EXPRESSION_TEMPLATE"
    if "STRATEGY" in text:
        strategy_family = "STAGE1_STRATEGY_TEMPLATE"
        trading_role = "SIGNAL_COMBINATION"
    elif "RISK" in text:
        trading_role = "RISK"
    elif "CAPITAL" in text:
        trading_role = "CAPITAL"
    elif "LATENCY" in text:
        trading_role = "LATENCY"
    elif "AGENT" in text:
        trading_role = "OWNER_REVIEW"
    elif optimizer_family:
        trading_role = "OPTIMIZER"
    return {
        "qku_algorithm_family": algorithm_family,
        "qku_formula_family": formula_family,
        "qku_strategy_family": strategy_family,
        "qku_optimizer_family": optimizer_family,
        "qku_trading_role": trading_role,
        "qku_parameter_role": str(record.get("parameter_role") or record.get("candidate_family") or "candidate_parameter"),
        "qku_signal_feature_role": "FEATURE" if "FEATURE" in text else None,
        "qku_risk_capital_execution_role": trading_role if trading_role in {"RISK", "CAPITAL", "EXECUTION"} else None,
        "qku_latency_role": "LATENCY" if trading_role == "LATENCY" else None,
    }
