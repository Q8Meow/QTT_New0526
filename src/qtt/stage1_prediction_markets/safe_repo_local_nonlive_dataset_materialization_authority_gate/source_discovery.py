"""PR162A public/source candidate discovery records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def source_candidate_records() -> list[dict[str, Any]]:
    rows = (
        (
            "PR162A-SOURCE-KALSHI-HISTORICAL-TRADES",
            "Kalshi historical trades public endpoint",
            "KALSHI",
            "https://external-api.kalshi.com/trade-api/v2/historical/trades",
            ("OFFICIAL_SOURCE_CANDIDATE", "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE"),
            "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
            "historical/trades",
            "FETCH_PLAN_ONLY",
            "PR162A_BLOCKED_NETWORK_DISABLED_BY_DEFAULT",
        ),
        (
            "PR162A-SOURCE-KALSHI-HISTORICAL-CANDLESTICKS",
            "Kalshi historical market candlesticks public endpoint",
            "KALSHI",
            "https://external-api.kalshi.com/trade-api/v2/historical/markets/{ticker}/candlesticks",
            (
                "OFFICIAL_SOURCE_CANDIDATE",
                "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE",
                "OFFICIAL_PUBLIC_OHLC_EVENT_HISTORY_CANDIDATE",
            ),
            "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
            "historical/markets/candlesticks",
            "BOUNDED_PUBLIC_FETCH_CANDIDATE",
            "NONE",
        ),
        (
            "PR162A-SOURCE-POLYMARKET-PRICES-HISTORY",
            "Polymarket public price history endpoint",
            "POLYMARKET",
            "https://clob.polymarket.com/prices-history",
            (
                "OFFICIAL_SOURCE_CANDIDATE",
                "OFFICIAL_PUBLIC_PRICE_HISTORY_CANDIDATE",
            ),
            "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
            "clob/prices-history",
            "FETCH_PLAN_ONLY",
            "PR162A_BLOCKED_NETWORK_DISABLED_BY_DEFAULT",
        ),
        (
            "PR162A-SOURCE-POLYMARKET-BATCH-PRICES-HISTORY",
            "Polymarket public batch price history endpoint",
            "POLYMARKET",
            "https://clob.polymarket.com/batch-prices-history",
            (
                "OFFICIAL_SOURCE_CANDIDATE",
                "OFFICIAL_PUBLIC_PRICE_HISTORY_CANDIDATE",
            ),
            "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
            "clob/batch-prices-history",
            "FETCH_PLAN_ONLY",
            "PR162A_BLOCKED_NETWORK_DISABLED_BY_DEFAULT",
        ),
        (
            "PR162A-SOURCE-POLYMARKET-GAMMA-MARKETS",
            "Polymarket Gamma market discovery metadata",
            "POLYMARKET",
            "https://gamma-api.polymarket.com/markets",
            ("OFFICIAL_SOURCE_CANDIDATE", "WEB_SOURCE_CANDIDATE"),
            "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
            "gamma/markets",
            "FETCH_PLAN_ONLY",
            "PR162A_BLOCKED_NETWORK_DISABLED_BY_DEFAULT",
        ),
        (
            "PR162A-SOURCE-IBKR-FORECASTEX-SECEF-SEARCH",
            "IBKR ForecastEx event-contract discovery documentation",
            "FORECASTEX_IBKR",
            "https://ibkrcampus.com/campus/ibkr-api-page/event-contracts/",
            (
                "OFFICIAL_SOURCE_CANDIDATE",
                "OFFICIAL_PUBLIC_OHLC_EVENT_HISTORY_CANDIDATE",
                "INSTITUTIONAL_METHOD_CANDIDATE",
            ),
            "AUTHENTICATION_REQUIRED_BLOCKED",
            "iserver/secdef-and-marketdata",
            "BLOCKED_WITH_ACTIONABLE_OWNER_COMMAND",
            "PR162A_BLOCKED_AUTHENTICATION_REQUIRED",
        ),
        (
            "PR162A-SOURCE-QISKIT-OPTIMIZATION-DOCS",
            "IBM Quantum/Qiskit optimization workflow documentation",
            "IBM_QUANTUM_QISKIT",
            "https://qiskit.qotlabs.org/docs/tutorials/solve-higher-order-binary-optimization-problems-with-q-ctrls-optimization-solver",
            (
                "QUANTUM_METHOD_CANDIDATE",
                "QUANTUM_BACKEND_DOC_CANDIDATE",
                "QUANTUM_ALGORITHM_DOC_CANDIDATE",
                "QUANTUM_PARAMETER_RANGE_CANDIDATE",
                "QUANTUM_ENCODING_CANDIDATE",
            ),
            "AUTHENTICATION_REQUIRED_BLOCKED",
            "quantum/optimization-docs",
            "DISCOVERY_ONLY",
            "PR162A_BLOCKED_AUTHENTICATION_REQUIRED",
        ),
        (
            "PR162A-SOURCE-CLASSICAL-HYBRID-BENCHMARKS",
            "Classical and hybrid optimizer benchmark candidate surfaces",
            "RESEARCH_METHODS",
            "RESEARCH_AND_OWNER_REVIEW_QUEUE",
            (
                "RESEARCH_SOURCE_CANDIDATE",
                "CLASSICAL_METHOD_CANDIDATE",
                "HYBRID_METHOD_CANDIDATE",
            ),
            "RESEARCH_USE_CANDIDATE_OK",
            "method-benchmark-candidates",
            "DISCOVERY_ONLY",
            "PR162A_BLOCKED_SOURCE_EVIDENCE_REQUIRED",
        ),
    )
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        (
            record_id,
            source_name,
            platform,
            locator,
            source_classes,
            access_status,
            endpoint_family,
            materialization_mode,
            blocker_code,
        ) = row
        records.append(
            {
                "record_id": record_id,
                "created_by_pr": c.PR_ID,
                "authority_class": c.AUTHORITY_CLASS,
                "source_candidate_index": index,
                "source_name": source_name,
                "source_platform_or_venue": platform,
                "source_locator": locator,
                "source_class": source_classes[0],
                "source_classes": list(source_classes),
                "source_endpoint_family": endpoint_family,
                "source_revalidation_required_flag": True,
                "access_rights_status": access_status,
                "owner_attestation_required_flag": access_status != "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
                "materialization_mode": materialization_mode,
                "candidate_only_flag": True,
                "accepted_as_official_fact_flag": False,
                "creates_connector_semantics": False,
                "private_state_flag": "PRIVATE" in access_status,
                "credential_required_flag": "AUTHENTICATION" in access_status,
                "order_endpoint_dependency_flag": False,
                "live_connector_dependency_flag": False,
                "blocker_code": blocker_code,
                "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
            }
        )
    return records
