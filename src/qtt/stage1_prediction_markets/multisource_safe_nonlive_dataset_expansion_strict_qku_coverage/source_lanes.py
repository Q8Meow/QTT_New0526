"""PR162C deterministic source-lane records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def source_portfolio_records() -> list[dict[str, Any]]:
    return [
        _source(
            "PR162C-SOURCE-KALSHI-PUBLIC-CANDLESTICKS",
            "Kalshi public market candlesticks documentation",
            "LANE_A_KALSHI_OFFICIAL_PUBLIC_HISTORICAL_CANDIDATE",
            "OFFICIAL_VENUE_PUBLIC_API",
            "https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks",
            "PUBLIC_DOCUMENTATION_ONLY_OK",
            ["market_ticker", "yes_bid", "yes_ask", "price", "volume", "open_interest"],
        ),
        _source(
            "PR162C-SOURCE-KALSHI-PUBLIC-DOCS",
            "Kalshi public API documentation",
            "LANE_A_KALSHI_OFFICIAL_PUBLIC_HISTORICAL_CANDIDATE",
            "OFFICIAL_VENUE_PUBLIC_API",
            "https://docs.kalshi.com/",
            "PUBLIC_DOCUMENTATION_ONLY_OK",
            ["markets", "trades", "candlesticks", "market_metadata"],
        ),
        _source(
            "PR162C-SOURCE-POLYMARKET-API-DOCS",
            "Polymarket API documentation",
            "LANE_B_POLYMARKET_OFFICIAL_PUBLIC_CANDIDATE",
            "OFFICIAL_VENUE_PUBLIC_API",
            "https://docs.polymarket.com/api-reference",
            "PUBLIC_DOCUMENTATION_ONLY_OK",
            ["gamma_markets", "events", "clob_prices", "prices_history"],
        ),
        _source(
            "PR162C-SOURCE-FORECASTEX-PUBLIC-CSV",
            "ForecastEx public data CSV page",
            "LANE_C_FORECASTEX_IBKR_OFFICIAL_CANDIDATE",
            "OFFICIAL_VENUE_PUBLIC_CSV",
            "https://www.forecastex.com/data/",
            "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
            ["daily_pairs", "daily_prices", "daily_summary", "intraday_event_contract_data"],
        ),
        _source(
            "PR162C-SOURCE-IBKR-FORECASTEX-DOC",
            "IBKR ForecastEx event-contract public documentation candidate",
            "LANE_C_FORECASTEX_IBKR_OFFICIAL_CANDIDATE",
            "OFFICIAL_DOC_ONLY_FETCH_PLAN",
            "https://www.interactivebrokers.com/",
            "PUBLIC_DOCUMENTATION_ONLY_OK",
            ["event_contract_ohlc_documentation_candidate"],
        ),
        _source(
            "PR162C-SOURCE-PREDICTION-MARKET-BENCH",
            "Prediction-market public research dataset candidate",
            "LANE_D_PUBLIC_RESEARCH_THIRD_PARTY_CANDIDATE",
            "PUBLIC_RESEARCH_DATASET_CANDIDATE",
            "https://arxiv.org/abs/2602.00133",
            "THIRD_PARTY_TERMS_REVIEW_REQUIRED",
            ["historical_limit_order_book_candidate", "trades_candidate"],
        ),
        _source(
            "PR162C-SOURCE-POLYMARKET-MICROSTRUCTURE-RESEARCH",
            "Polymarket microstructure research candidate",
            "LANE_D_PUBLIC_RESEARCH_THIRD_PARTY_CANDIDATE",
            "PUBLIC_RESEARCH_DATASET_CANDIDATE",
            "https://arxiv.org/abs/2605.11640",
            "THIRD_PARTY_TERMS_REVIEW_REQUIRED",
            ["microstructure_features_candidate", "quote_attribution_limitations_candidate"],
        ),
        _source(
            "PR162C-SOURCE-DWAVE-MODELS",
            "D-Wave model documentation",
            "LANE_E_OPEN_SOURCE_PACKAGE_INTROSPECTION",
            "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
            "https://docs.dwavequantum.com/en/latest/concepts/models.html",
            "PUBLIC_DOCUMENTATION_ONLY_OK",
            ["BQM", "CQM", "QUBO", "Ising"],
        ),
        _source(
            "PR162C-SOURCE-QISKIT-OPTIMIZATION",
            "Qiskit Optimization documentation",
            "LANE_E_OPEN_SOURCE_PACKAGE_INTROSPECTION",
            "OFFICIAL_LIBRARY_DOC_SOLVER_SOURCE",
            "https://qiskit-community.github.io/qiskit-optimization/",
            "PUBLIC_DOCUMENTATION_ONLY_OK",
            ["QUBO", "Ising", "optimization_problem"],
        ),
    ]


def source_discovery_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "discovery_id": record["source_id"].replace("SOURCE", "DISCOVERY"),
            **record,
            "discovery_mode": "OFFLINE_REGISTERED_LOCATOR_NO_DEFAULT_NETWORK_FETCH",
            "online_materialization_command_required_flag": record["source_lane"]
            in {
                "LANE_A_KALSHI_OFFICIAL_PUBLIC_HISTORICAL_CANDIDATE",
                "LANE_B_POLYMARKET_OFFICIAL_PUBLIC_CANDIDATE",
                "LANE_C_FORECASTEX_IBKR_OFFICIAL_CANDIDATE",
                "LANE_D_PUBLIC_RESEARCH_THIRD_PARTY_CANDIDATE",
            },
            "ci_requires_network": False,
        }
        for record in sources
    ]


def source_records_by_lane(sources: list[dict[str, Any]], lane: str) -> list[dict[str, Any]]:
    return [record for record in sources if record["source_lane"] == lane]


def owner_provided_local_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": "PR162C-OWNER-LOCAL-DATA-SCAN-001",
            "source_lane": "LANE_F_OWNER_PROVIDED_LOCAL_DATA",
            "source_class": "OWNER_PROVIDED_LOCAL_DATASET_CANDIDATE",
            "approved_scan_scope": "repo-local data/stage1_prediction_markets only",
            "owner_provided_file_count": 0,
            "owner_attestation_required": True,
            "access_rights_status": "OWNER_PROVIDED_ATTESTATION_REQUIRED",
            "materialization_status": "OWNER_MATERIALIZATION_COMMAND_REQUIRED",
            "created_by_pr": c.PR_ID,
        }
    ]


def source_access_gate_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "access_gate_id": record["source_id"].replace("SOURCE", "ACCESS-GATE"),
            "source_id": record["source_id"],
            "source_class": record["source_class"],
            "source_lane": record["source_lane"],
            "source_locator": record["source_locator"],
            "access_rights_status": record["access_rights_status"],
            "safe_for_default_ci_flag": True,
            "default_network_fetch_allowed_flag": False,
            "private_state_required_flag": False,
            "order_endpoint_required_flag": False,
            "live_connector_required_flag": False,
            "gate_status": "PASS_CANDIDATE_OR_FETCH_PLAN_ONLY",
            "created_by_pr": c.PR_ID,
        }
        for record in sources
    ]


def owner_materialization_command_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commands = []
    for record in sources:
        if record["source_lane"] == "LANE_E_OPEN_SOURCE_PACKAGE_INTROSPECTION":
            continue
        commands.append(
            {
                "command_id": record["source_id"].replace("SOURCE", "OWNER-COMMAND"),
                "source_name": record["source_title"],
                "source_class": record["source_class"],
                "source_locator": record["source_locator"],
                "expected_format": _expected_format(record),
                "expected_size_class": "BOUNDED_OWNER_SELECTED_SMALL_OR_MEDIUM",
                "access_rights_status": record["access_rights_status"],
                "destination_path": _destination_path(record),
                "validation_command": (
                    "python tools/validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
                ),
                "normalization_command": (
                    "python tools/build_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
                ),
                "owner_attestation_required": record["access_rights_status"]
                not in {"PUBLIC_DOCUMENTATION_ONLY_OK", "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK"},
                "qku_requirement_refs": ["PR162B_PR162CDataRequirementHandoff.report.json"],
                "formula_value_candidate_refs": record["mapped_field_candidates"],
                "replay_paper_candidate_route": "PR162R_ADAPTER_RERUN_AFTER_STRICT_DATASETS",
                "execute_in_default_ci_flag": False,
                "created_by_pr": c.PR_ID,
            }
        )
    return commands


def _source(
    source_id: str,
    title: str,
    lane: str,
    source_class: str,
    locator: str,
    access: str,
    fields: list[str],
) -> dict[str, Any]:
    return {
        "record_id": source_id,
        "source_id": source_id,
        "source_title": title,
        "source_lane": lane,
        "source_class": source_class,
        "source_locator": locator,
        "retrieval_timestamp": None,
        "retrieval_mode": "REGISTERED_LOCATOR_ONLY_NO_DEFAULT_FETCH",
        "access_rights_status": access,
        "source_quality_tier": "REGISTERED_PUBLIC_DOC_OR_LOCATOR_ONLY",
        "candidate_provisional_flag": True,
        "official_truth_flag": source_class.startswith("OFFICIAL_"),
        "not_official_truth_if_non_official": not source_class.startswith("OFFICIAL_"),
        "accepted_as_source_evidence_fact_flag": False,
        "not_live_authority": True,
        "materialized_repo_local_dataset_flag": False,
        "mapped_field_candidates": fields,
        "blocked_endpoint_families": [
            "private_account_state",
            "order_management",
            "fills_private_account",
            "authenticated_live_connector",
        ],
        "authority_class": "OFFICIAL_PUBLIC_SOURCE_CANDIDATE_NOT_ACCEPTED_AS_TRUTH"
        if source_class.startswith("OFFICIAL_")
        else "PUBLIC_RESEARCH_CANDIDATE_NOT_OFFICIAL_TRUTH",
        "created_by_pr": c.PR_ID,
    }


def _expected_format(record: dict[str, Any]) -> str:
    if record["source_class"] == "OFFICIAL_VENUE_PUBLIC_CSV":
        return "csv"
    if record["source_class"] == "PUBLIC_RESEARCH_DATASET_CANDIDATE":
        return "owner_selected_public_dataset_archive_or_jsonl"
    return "json_or_csv"


def _destination_path(record: dict[str, Any]) -> str:
    stem = record["source_id"].lower().replace("pr162c-source-", "").replace("_", "-")
    return f"data/stage1_prediction_markets/nonlive_datasets/pr162c/owner_materialized/{stem}/"
