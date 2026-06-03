"""Static offline-safe source intake records for PR162D."""

from __future__ import annotations

from .deterministic_id import deterministic_digest, deterministic_id
from .source_quality_policy import (
    authority_for_source,
    confidence_for_source,
    source_quality_score,
)


def source_seed_records() -> list[dict[str, object]]:
    return [
        {
            "source_title": "PR162C repo-local source portfolio",
            "source_locator": "docs/master_plan/generated/PR162C_SourcePortfolioRegistry.report.json",
            "source_tier": "TIER_0",
            "source_class": "REPO_LOCAL_OWNER_PROVIDED",
            "qku_refs": ["PR162D_ALL_PR162C_REQUIREMENT_QKUS"],
            "field_refs": ["PR162C_REQUIRED_FIELD_MISSING_REINTERPRETED_AS_CANDIDATE_TARGET"],
            "formula_refs": [],
            "agent_route_refs": ["PR162D_AGENT_ROUTE_RESOLVER"],
            "source_pack": "OWNER_LOCAL",
        },
        {
            "source_title": "Kalshi public market candlesticks documentation",
            "source_locator": "https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks",
            "source_tier": "TIER_1",
            "source_class": "OFFICIAL_VENUE_PUBLIC_API",
            "qku_refs": ["PR162D_PREDICTION_MARKET_PUBLIC_DATA_QKUS"],
            "field_refs": ["yes_price", "volume", "candlestick", "market_ticker"],
            "formula_refs": ["implied_probability_from_cents", "mid_price", "spread"],
            "agent_route_refs": ["QKU_DATA_ACQUISITION_AGENT", "FEATURE_BUILDER"],
            "source_pack": "KALSHI",
        },
        {
            "source_title": "Polymarket API overview for Gamma, Data, and CLOB APIs",
            "source_locator": "https://docs.polymarket.com/api-reference",
            "source_tier": "TIER_1",
            "source_class": "OFFICIAL_VENUE_PUBLIC_API",
            "qku_refs": ["PR162D_PREDICTION_MARKET_PUBLIC_DATA_QKUS"],
            "field_refs": ["market", "event", "orderbook", "price_history", "token_id"],
            "formula_refs": ["mid_price", "spread", "orderbook_imbalance"],
            "agent_route_refs": ["QKU_DATA_ACQUISITION_AGENT", "FEATURE_BUILDER"],
            "source_pack": "POLYMARKET",
        },
        {
            "source_title": "ForecastEx public data CSV page",
            "source_locator": "https://forecastex.com/data",
            "source_tier": "TIER_1",
            "source_class": "OFFICIAL_VENUE_PUBLIC_CSV",
            "qku_refs": ["PR162D_FORECASTEX_PUBLIC_CSV_QKUS"],
            "field_refs": ["pairs", "prices", "summary", "daily_csv", "intraday_csv"],
            "formula_refs": ["implied_probability_from_price", "volume_momentum"],
            "agent_route_refs": ["QKU_DATA_ACQUISITION_AGENT", "REPLAY_ENGINE_INPUT_PREP"],
            "source_pack": "FORECASTEX_IBKR",
        },
        {
            "source_title": "D-Wave Ocean model documentation for BQM, CQM, QUBO, and Ising",
            "source_locator": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
            "source_tier": "TIER_1",
            "source_class": "OFFICIAL_QUANTUM_PROVIDER_DOC",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "field_refs": ["BQM", "CQM", "QUBO", "Ising", "vartype"],
            "formula_refs": ["QUBO objective x^T Q x", "Ising energy", "BQM energy"],
            "agent_route_refs": ["QUANTUM_ADVISORY_AGENT", "QUANTUM_EXECUTION_HARNESS"],
            "source_pack": "QUANTUM_BACKEND_PROVIDER",
        },
        {
            "source_title": "Qiskit Algorithms QAOA documentation",
            "source_locator": "https://qiskit-community.github.io/qiskit-algorithms/stubs/qiskit_algorithms.QAOA.html",
            "source_tier": "TIER_1",
            "source_class": "OFFICIAL_QUANTUM_PROVIDER_DOC",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "field_refs": ["QAOA", "SamplingVQE", "sampler", "optimizer"],
            "formula_refs": ["QAOA Hamiltonian mapping candidate", "VQE objective candidate"],
            "agent_route_refs": ["QUANTUM_ADVISORY_AGENT", "QUANTUM_CLASSICAL_HYBRID_COMPARATOR"],
            "source_pack": "QUANTUM_BACKEND_PROVIDER",
        },
        {
            "source_title": "scikit-learn log loss and Brier score metric documentation",
            "source_locator": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html",
            "source_tier": "TIER_2",
            "source_class": "OFFICIAL_OPEN_SOURCE_LIBRARY_DOC",
            "qku_refs": ["PR162D_CALIBRATION_QKUS"],
            "field_refs": ["p_pred", "y_true", "epsilon"],
            "formula_refs": ["brier_score_binary", "log_loss_binary", "probability_clipping"],
            "agent_route_refs": ["QKU_FORMULA_COMPUTE_ENGINE", "REPLAY_PAPER_RESULT_ANALYZER_INPUT_PREP"],
            "source_pack": "OPEN_SOURCE_FORMULA_LIBRARY",
        },
        {
            "source_title": "PyPortfolioOpt mean-variance optimization documentation",
            "source_locator": "https://pyportfolioopt.readthedocs.io/en/latest/MeanVariance.html",
            "source_tier": "TIER_2",
            "source_class": "OFFICIAL_OPEN_SOURCE_LIBRARY_DOC",
            "qku_refs": ["PR162D_RISK_PORTFOLIO_QKUS"],
            "field_refs": ["expected_return", "covariance", "risk_aversion", "weights"],
            "formula_refs": ["mean_variance_objective", "portfolio_qp_objective"],
            "agent_route_refs": ["PARAMETER_STACK_AGENT", "RISK_MANAGER_CANDIDATE_REVIEW"],
            "source_pack": "OPEN_SOURCE_FORMULA_LIBRARY",
        },
        {
            "source_title": "Public QUBO formulation tutorial preprint",
            "source_locator": "https://arxiv.org/abs/1811.11538",
            "source_tier": "TIER_3",
            "source_class": "PUBLIC_RESEARCH_FORMULA",
            "qku_refs": ["PR162D_QUANTUM_QKUS"],
            "field_refs": ["QUBO", "binary_variable", "quadratic_terms"],
            "formula_refs": ["market-bundle selection QUBO", "risk-budget QUBO"],
            "agent_route_refs": ["QUANTUM_ADVISORY_AGENT", "REPLAY_PAPER_CANDIDATE_ROUTER"],
            "source_pack": "PUBLIC_RESEARCH",
        },
        {
            "source_title": "PyPortfolioOpt public GitHub repository",
            "source_locator": "https://github.com/PyPortfolio/PyPortfolioOpt",
            "source_tier": "TIER_3",
            "source_class": "PUBLIC_GITHUB_REFERENCE",
            "qku_refs": ["PR162D_RISK_PORTFOLIO_QKUS"],
            "field_refs": ["portfolio_optimization", "risk_model", "efficient_frontier"],
            "formula_refs": ["mean_variance_objective", "correlation-penalized objective"],
            "agent_route_refs": ["PARAMETER_STACK_AGENT", "REPLAY_PAPER_CANDIDATE_ROUTER"],
            "source_pack": "PUBLIC_RESEARCH",
        },
        {
            "source_title": "Public prediction-market API discussion signal",
            "source_locator": "https://www.reddit.com/r/Polymarket/comments/1s17kky/how_to_get_realtime_yesno_prices_from_clob_api/",
            "source_tier": "TIER_4",
            "source_class": "SOCIAL_WEB_RESEARCH_SIGNAL",
            "qku_refs": ["PR162D_PREDICTION_MARKET_PUBLIC_DATA_QKUS"],
            "field_refs": ["websocket_price_update_signal", "token_id_mapping_signal"],
            "formula_refs": ["latency_adjusted_expected_value", "stale_snapshot_candidate"],
            "agent_route_refs": ["REPLAY_PAPER_CANDIDATE_ROUTER", "OWNER_REVIEW_OPTIONAL"],
            "source_pack": "SOCIAL_WEB_INSTITUTIONAL",
        },
        {
            "source_title": "Owner-approved PR162D formula/default expansion directive",
            "source_locator": "OWNER_PR162D_DIRECTIVE",
            "source_tier": "TIER_0",
            "source_class": "OWNER_PROVIDED_INTERNAL_CANDIDATE",
            "qku_refs": ["PR162D_ALL_PR162C_REQUIREMENT_QKUS"],
            "field_refs": ["default_value_candidate", "range_min_candidate", "range_max_candidate"],
            "formula_refs": ["Kelly", "fractional Kelly", "QUBO penalty lambda"],
            "agent_route_refs": ["PARAMETER_STACK_AGENT", "OWNER_REVIEW_OPTIONAL"],
            "source_pack": "OWNER_LOCAL",
        },
    ]


def candidate_source_records() -> list[dict[str, object]]:
    records = []
    for index, seed in enumerate(source_seed_records(), start=1):
        official = str(seed["source_class"]).startswith("OFFICIAL")
        source_tier = str(seed["source_tier"])
        source_class = str(seed["source_class"])
        record = {
            "source_id": deterministic_id("PR162D-SOURCE", seed["source_locator"], size=8),
            "record_id": f"PR162D-SOURCE-INTAKE-{index:04d}",
            "retrieval_status": "SCOUTED_OR_REPO_LOCAL_LOCATOR_CACHED_OFFLINE_SAFE",
            "source_quality_score": source_quality_score(source_tier, official),
            "authority_class": authority_for_source(source_tier, source_class),
            "confidence_class": confidence_for_source(source_tier, source_class),
            "official_truth_flag": official,
            "candidate_or_provisional_flag": True,
            "replay_paper_candidate_flag": True,
            "source_capture_digest_or_locator_digest": deterministic_digest(
                [seed["source_locator"], seed["source_title"]]
            ),
            "live_order_authority": False,
            "accepted_as_live_connector_truth_flag": False,
            "created_by_pr": "PR162D",
            **seed,
        }
        records.append(record)
    return records
