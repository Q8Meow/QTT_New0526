"""Default materialization engine for primary QKUs."""

from __future__ import annotations

import re
from typing import Any

from .qku_owner_fallback_default_policy import fallback_default_for


def _numeric(value: object) -> float | int | None:
    if value is None or value == "":
        return None
    try:
        number = float(str(value).strip())
    except ValueError:
        match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value))
        if not match:
            return None
        number = float(match.group(0))
    return int(number) if number.is_integer() else number


def materialize_default(qku_type: str, source: dict[str, Any], facet_count: int = 0) -> dict[str, Any]:
    value = _numeric(source.get("value_candidate_if_available") or source.get("default_value") or source.get("value"))
    lower = _numeric(source.get("lower_bound") or source.get("lower_bound_if_available"))
    upper = _numeric(source.get("upper_bound") or source.get("upper_bound_if_available"))
    formula = source.get("formula_candidate_if_available") or source.get("formula_expression")
    range_candidate = source.get("range_candidate_if_available")
    algorithm = source.get("algorithm_family") or source.get("candidate_family")
    payload = fallback_default_for(qku_type)
    fallback_used = True
    fallback_reason = "SOURCE_PRIORITY_LADDER_EXHAUSTED_OWNER_AUTHORIZED_TYPE_DEFAULT_USED"
    fallback_blocking_source_class = "NO_HIGHER_PRIORITY_NUMERIC_OR_LITERAL_VALUE_AVAILABLE"
    source_class_override = None
    state = "MATERIALIZED_CATEGORICAL_DEFAULT"

    if qku_type == "OPTIMIZER_SETTING_QKU":
        payload.update(
            {
                "optimizer_family": str(algorithm or "CLASSICAL_OPTIMIZER"),
                "max_iterations": int(value) if isinstance(value, int) and value > 0 else 100,
                "tolerance": 0.000001,
                "search_lower_bound": 0.0 if lower is None else lower,
                "search_upper_bound": 1.0 if upper is None else upper,
            }
        )
        state = "MATERIALIZED_OPTIMIZER_CONFIG"
        source_class_override = "OPTIMIZER_LIBRARY_DOC_SOURCE"
    elif qku_type == "RANGE_QKU":
        payload.update(
            {
                "range_expression": range_candidate or "owner_authorized_candidate_range",
                "default_value": value if value is not None else payload.get("default_value", 0.5),
                "lower_bound": 0.0 if lower is None else lower,
                "upper_bound": 1.0 if upper is None else upper,
                "unit": source.get("unit_candidate_if_available") or source.get("unit") or payload.get("unit", "dimensionless_candidate"),
                "scale": source.get("scale_candidate_if_available") or source.get("scale") or payload.get("scale", "normalized_candidate_scale"),
            }
        )
        if range_candidate or value is not None or lower is not None or upper is not None:
            fallback_used = False
            fallback_reason = None
            fallback_blocking_source_class = None
        state = "MATERIALIZED_RANGE_DEFAULT"
    elif value is not None:
        payload.update(
            {
                "default_value": value,
                "lower_bound": 0.0 if lower is None else lower,
                "upper_bound": 1.0 if upper is None else upper,
                "unit": source.get("unit_candidate_if_available") or source.get("unit") or "dimensionless_candidate",
                "scale": source.get("scale_candidate_if_available") or source.get("scale") or "normalized_candidate_scale",
            }
        )
        fallback_used = False
        fallback_reason = None
        fallback_blocking_source_class = None
        state = "MATERIALIZED_NUMERIC_DEFAULT"
    elif range_candidate or lower is not None or upper is not None:
        payload.update(
            {
                "range_expression": range_candidate or "owner_authorized_candidate_range",
                "lower_bound": 0.0 if lower is None else lower,
                "upper_bound": 1.0 if upper is None else upper,
                "unit": source.get("unit_candidate_if_available") or source.get("unit") or "dimensionless_candidate",
            }
        )
        fallback_used = False
        fallback_reason = None
        fallback_blocking_source_class = None
        state = "MATERIALIZED_RANGE_DEFAULT"
    elif formula:
        payload.update({"formula_expression": formula})
        fallback_used = False
        fallback_reason = None
        fallback_blocking_source_class = None
        state = "MATERIALIZED_FORMULA_DEFAULT"
    elif qku_type in {"PARAMETER_QKU", "DEFAULT_VALUE_QKU", "RISK_QKU", "CAPITAL_QKU", "LATENCY_QKU"}:
        payload.update(
            {
                "default_value": payload.get("default_value", 0.5),
                "lower_bound": payload.get("lower_bound", 0.0),
                "upper_bound": payload.get("upper_bound", 1.0),
                "unit": source.get("unit_candidate_if_available") or source.get("unit") or payload.get("unit", "dimensionless_candidate"),
                "scale": source.get("scale_candidate_if_available") or source.get("scale") or payload.get("scale", "normalized_candidate_scale"),
            }
        )
        state = "MATERIALIZED_NUMERIC_DEFAULT"
    elif qku_type == "STRATEGY_TEMPLATE_QKU":
        payload.update({"strategy_template": str(source.get("candidate_type") or "STAGE1_STRATEGY_TEMPLATE")})
        state = "MATERIALIZED_STRATEGY_TEMPLATE"
    elif qku_type == "ALGORITHM_QKU":
        payload.update({"algorithm_family": str(algorithm or "CLASSICAL_ALGORITHM"), "max_iterations": 100})
        state = "MATERIALIZED_ALGORITHM_CONFIG"
    elif qku_type in {"ATOMICROW_QKU", "PR154_TARGET_QKU"}:
        payload.update({"entity_field_value_facet_count": facet_count, "entity_materialization_source": "PR161A_ENTITY_AND_FIELD_VALUE_FACETS"})
        fallback_used = False
        state = "MATERIALIZED_FIELD_VALUE_FACET"

    return {
        "state": state,
        "payload": payload,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "fallback_blocking_source_class": fallback_blocking_source_class,
        "source_class_override": source_class_override,
        "confidence": "CANDIDATE_CONFIDENCE_HIGH_FROM_PR161A_PR161B" if not fallback_used else "OWNER_AUTHORIZED_CANDIDATE_DEFAULT_MEDIUM",
    }
