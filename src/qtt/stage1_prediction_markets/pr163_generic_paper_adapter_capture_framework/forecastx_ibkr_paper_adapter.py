"""ForecastEx/IBKR paper adapter capability declarations."""

from __future__ import annotations

from .paper_adapter_interface import capability_row


def build_capability_row(index: int = 3) -> dict:
    return capability_row(
        index,
        "FORECASTEX_IBKR_EVENT_MARKETS",
        [
            "contract_metadata_candidate_slots",
            "market_data_subscription_candidate_slots",
            "order_type_candidate_slots",
            "paper_demonstration_semantics_candidate_only",
            "no_TWS_IBKR_connector_binding",
            "no_private_account_state",
        ],
        [
            "https://www.interactivebrokers.com/en/pricing/commissions-events.php",
        ],
    )
