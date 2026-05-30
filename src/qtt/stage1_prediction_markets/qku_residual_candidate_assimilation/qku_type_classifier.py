"""QKU type classification."""

from __future__ import annotations


def classify_entity_type(entity: dict[str, object]) -> str:
    if entity.get("universe") == "PR154" or entity.get("target_id"):
        return "PR154_TARGET_QKU"
    return "ATOMICROW_QKU"


def classify_residual_type(residual: dict[str, object]) -> str:
    candidate_type = str(residual.get("candidate_type") or "")
    candidate_family = str(residual.get("candidate_family") or "")
    text = f"{candidate_family} {candidate_type}".upper()
    if candidate_type.upper() == "OPTIMIZER_SETTING":
        return "OPTIMIZER_SETTING_QKU"
    if "RANGE" in text:
        return "RANGE_QKU"
    if "CONSTRAINT" in text:
        return "CONSTRAINT_QKU"
    if "FORMULA" in text or "OBJECTIVE" in text:
        return "FORMULA_QKU"
    if "ALGORITHM" in text:
        return "ALGORITHM_QKU"
    if "OPTIMIZER" in text:
        return "OPTIMIZER_SETTING_QKU"
    if "SOURCE" in text:
        return "SOURCE_RECORD_QKU"
    if "RISK" in text:
        return "RISK_QKU"
    if "CAPITAL" in text:
        return "CAPITAL_QKU"
    if "LATENCY" in text:
        return "LATENCY_QKU"
    if "AGENT" in text:
        return "AGENT_BINDING_QKU"
    if "STRATEGY" in text:
        return "STRATEGY_TEMPLATE_QKU"
    if "DEFAULT" in text:
        return "DEFAULT_VALUE_QKU"
    return "PARAMETER_QKU"
