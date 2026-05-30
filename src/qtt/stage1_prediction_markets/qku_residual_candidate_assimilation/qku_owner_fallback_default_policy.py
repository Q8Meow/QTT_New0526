"""Owner-authorized fallback defaults for machine-usable candidate payloads."""

from __future__ import annotations

from . import constants as c


def fallback_default_for(qku_type: str) -> dict[str, object]:
    policy = c.OWNER_FALLBACK_DEFAULT_POLICY
    if qku_type in {"RANGE_QKU", "PARAMETER_QKU", "DEFAULT_VALUE_QKU", "RISK_QKU", "CAPITAL_QKU", "LATENCY_QKU"}:
        return {
            "default_value": policy["neutral_probability"],
            "lower_bound": 0.0,
            "upper_bound": 1.0,
            "unit": policy["default_unit"],
            "scale": policy["default_scale"],
            "candidate_default_class": "OWNER_AUTHORIZED_DEFAULT_CANDIDATE",
        }
    if qku_type == "FORMULA_QKU":
        return {
            "formula_expression": "candidate_expression_template(input_features, candidate_parameters)",
            "candidate_default_class": "OWNER_AUTHORIZED_DEFAULT_CANDIDATE",
        }
    if qku_type in {"ALGORITHM_QKU", "OPTIMIZER_SETTING_QKU"}:
        return {
            "algorithm_family": "CLASSICAL_BASELINE_CANDIDATE",
            "max_iterations": 100,
            "tolerance": 0.000001,
            "candidate_default_class": "OWNER_AUTHORIZED_DEFAULT_CANDIDATE",
        }
    return {
        "categorical_default_state": "AGENT_RETRIEVAL_READY_CANDIDATE",
        "replay_paper_validation": "REPLAY_PAPER_VALIDATION_REQUIRED",
        "candidate_default_class": "OWNER_AUTHORIZED_DEFAULT_CANDIDATE",
    }
