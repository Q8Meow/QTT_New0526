"""Portfolio and classical optimizer objective helpers for PR162B."""

from __future__ import annotations


def mean_variance_objective(expected_return: float, variance: float, risk_aversion: float) -> float:
    return float(expected_return) - float(risk_aversion) * float(variance)


def portfolio_qp_objective(
    weights: list[float] | tuple[float, ...],
    returns: list[float] | tuple[float, ...],
    covariance_matrix: list[list[float]] | tuple[tuple[float, ...], ...],
    risk_aversion: float,
) -> float:
    ws = [float(value) for value in weights]
    rs = [float(value) for value in returns]
    if len(ws) != len(rs) or len(covariance_matrix) != len(ws):
        raise ValueError("weights, returns, and covariance matrix dimensions must match")
    linear = sum(weight * ret for weight, ret in zip(ws, rs, strict=True))
    quadratic = 0.0
    for i, row in enumerate(covariance_matrix):
        if len(row) != len(ws):
            raise ValueError("covariance matrix must be square")
        for j, value in enumerate(row):
            quadratic += ws[i] * float(value) * ws[j]
    return linear - float(risk_aversion) * quadratic


def linear_objective(coefficients: list[float], variables: list[float]) -> float:
    if len(coefficients) != len(variables):
        raise ValueError("coefficients and variables must have equal length")
    return sum(float(c) * float(x) for c, x in zip(coefficients, variables, strict=True))


def quadratic_objective(
    variables: list[float],
    q_matrix: list[list[float]],
    linear_coefficients: list[float] | None = None,
) -> float:
    xs = [float(value) for value in variables]
    if len(q_matrix) != len(xs):
        raise ValueError("q_matrix dimension must match variables")
    total = 0.0
    for i, row in enumerate(q_matrix):
        if len(row) != len(xs):
            raise ValueError("q_matrix must be square")
        for j, value in enumerate(row):
            total += xs[i] * float(value) * xs[j]
    if linear_coefficients is not None:
        total += linear_objective(linear_coefficients, xs)
    return total


def equality_constraint(lhs: float, rhs: float, tolerance: float = 0.0) -> bool:
    return abs(float(lhs) - float(rhs)) <= abs(float(tolerance))


def inequality_constraint(lhs: float, upper_bound: float, tolerance: float = 0.0) -> bool:
    return float(lhs) <= float(upper_bound) + abs(float(tolerance))


def penalty_objective(base_objective: float, penalty: float) -> float:
    return float(base_objective) + float(penalty)


def multi_objective_weighted_sum(values: list[float], weights: list[float]) -> float:
    if len(values) != len(weights):
        raise ValueError("values and weights must have equal length")
    return sum(float(value) * float(weight) for value, weight in zip(values, weights, strict=True))
