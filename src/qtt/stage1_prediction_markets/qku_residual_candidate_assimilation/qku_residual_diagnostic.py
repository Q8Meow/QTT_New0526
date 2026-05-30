"""Residual diagnostic classification."""

from __future__ import annotations


def classify_residual_diagnostic(residual: dict[str, object]) -> str:
    text = " ".join(str(value or "") for value in residual.values()).upper()
    if "PRIVATE_KEY=" in text or "API_KEY=" in text or "SECRET_VALUE=" in text or "RAW_SECRET" in text:
        return "UNSAFE_OR_SECRET_REJECTED_QKU"
    if "FUTURE_RUNTIME" in text or "LIVE_FUTURE" in text or "SECRET" in text or "API_KEY" in text:
        return "FUTURE_RUNTIME_ONLY_QKU"
    if "ONLINE_SCOUT" in text:
        return "ONLINE_SCOUT_QKU"
    if "SOURCE_UPGRADE" in text:
        return "SOURCE_UPGRADE_OPTIONAL_QKU"
    coverage_state = str(residual.get("coverage_state") or "").upper()
    if coverage_state == "COVERED_BY_CANONICAL_ALIAS":
        return "DUPLICATE_QKU_ALIAS"
    if coverage_state == "COVERED_BY_PR161A_QUANTUM_PROFILE":
        return "PR161A_ALIAS_REPAIR_QKU"
    if coverage_state.startswith("COVERED_BY_"):
        return "PR161A_FIELD_MATCH_MISSING_INDEX_QKU"
    if str(residual.get("recommended_fill_lane") or "").upper() == "FILL_FROM_EXISTING_PR_ARTIFACT":
        return "PR161A_FIELD_MATCH_MISSING_INDEX_QKU"
    if str(residual.get("recommended_fill_lane") or "").upper() == "FILL_FROM_OPTIMIZER_DEFAULT":
        return "ONLINE_SCOUT_QKU"
    if str(residual.get("candidate_type") or "").upper() == "AGENT_CONSUMPTION_FIELD":
        return "SOURCE_UPGRADE_OPTIONAL_QKU"
    if str(residual.get("candidate_type") or "").upper() == "DOCTRINE_ONLY_REFERENCE":
        return "DOCTRINE_ONLY_QKU"
    return "TRUE_NEW_QKU_REQUIRED"
