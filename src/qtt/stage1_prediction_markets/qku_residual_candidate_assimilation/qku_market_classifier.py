"""Market classification for QKU records."""

from __future__ import annotations


def classify_market(text: object, qku_type: str | None = None, source_record: dict[str, object] | None = None) -> dict[str, object]:
    value = str(text or "").upper()
    source = source_record or {}
    source_text = " ".join(str(value or "") for value in source.values()).upper()
    combined = f"{value} {source_text}"
    explicit_market_text = str(source.get("market_type") or source.get("platform") or source.get("platform_scope") or "").upper()
    classification_source = "ARTIFACT_DERIVED"
    reusable_qku_type = qku_type in {
        "PARAMETER_QKU",
        "RANGE_QKU",
        "DEFAULT_VALUE_QKU",
        "FORMULA_QKU",
        "ALGORITHM_QKU",
        "OPTIMIZER_SETTING_QKU",
        "CONSTRAINT_QKU",
        "RISK_QKU",
        "CAPITAL_QKU",
        "LATENCY_QKU",
        "AGENT_BINDING_QKU",
        "STRATEGY_TEMPLATE_QKU",
    }
    if reusable_qku_type and explicit_market_text in {"", "PREDICTION_MARKETS_GENERAL"}:
        primary = "MARKET_AGNOSTIC"
        classification_source = "MASTER_PLAN_DERIVED"
    elif "CRYPTO" in value:
        primary = "CRYPTO_MARKET"
    elif "EQUITY" in value or "STOCK" in value:
        primary = "EQUITY_MARKET"
    elif "FX" in value or "FOREX" in value:
        primary = "FX_MARKET"
    elif "FUTURE" in value:
        primary = "FUTURES_MARKET"
    elif "OPTION" in value:
        primary = "OPTIONS_MARKET"
    elif "COMMOD" in value:
        primary = "COMMODITIES_MARKET"
    elif "KALSHI" in combined or "POLYMARKET" in combined or "FORECASTEX" in combined:
        primary = "PREDICTION_MARKET"
    elif reusable_qku_type:
        primary = "MARKET_AGNOSTIC"
        classification_source = "MASTER_PLAN_DERIVED"
    elif "PREDICTION" in combined:
        primary = "PREDICTION_MARKET"
    else:
        primary = "MARKET_AGNOSTIC"
        classification_source = "OWNER_FALLBACK"
    all_markets = [primary]
    if primary not in {"PREDICTION_MARKET", "MARKET_AGNOSTIC"}:
        all_markets.append("MULTI_MARKET")
    elif primary == "MARKET_AGNOSTIC":
        all_markets.append("PREDICTION_MARKET")
    return {
        "qku_market_primary": primary,
        "qku_market_secondary": "PREDICTION_MARKET" if primary == "MARKET_AGNOSTIC" else "MULTI_MARKET" if primary != "PREDICTION_MARKET" else "MARKET_AGNOSTIC",
        "qku_market_all": all_markets,
        "qku_market_confidence_class": "MARKET_CLASS_HIGH_FROM_ARTIFACT_OR_STAGE1_POLICY",
        "qku_market_basis": "PR161A_PR161B_TEXT_PR136_AND_STAGE1_POLICY",
        "qku_market_classification_source": classification_source,
        "qku_stage1_prediction_market_applicability_flag": True,
        "qku_cross_market_reuse_flag": primary != "PREDICTION_MARKET",
        "qku_future_market_applicability_flag": primary != "PREDICTION_MARKET",
    }
