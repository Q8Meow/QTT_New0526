"""External source catalog scouted for PR162D-R1."""

from __future__ import annotations

from .source_quality_scoring import score_source
from .source_tier_classifier import classify_source_tier


_OFFICIAL_SOURCES = (
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/getting_started/historical_data"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/historical/get-historical-cutoff-timestamps.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/historical/get-historical-trades.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/historical/get-historical-markets.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/get-market-candlesticks.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/get-market-orderbook.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/get-multiple-market-orderbooks.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/get-trades.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/get-markets.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/market/get-market.md"),
    ("LANE_A_KALSHI", "OFFICIAL_KALSHI_DOC", "https://docs.kalshi.com/api-reference/events/get-event-candlesticks.md"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/introduction"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/list-markets-keyset-pagination"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/list-markets"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/get-market-by-id"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/events/list-events-keyset-pagination"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/market-data/get-order-book"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/data/get-midpoint-price"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/market-data/get-spread"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/get-prices-history"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/trade/get-trades"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/get-open-interest"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/get-top-holders-for-markets"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/markets/get-market-by-token"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/data/get-market-price"),
    ("LANE_B_POLYMARKET", "OFFICIAL_POLYMARKET_DOC", "https://docs.polymarket.com/api-reference/market-data/get-clob-market-info"),
    ("LANE_C_FORECASTEX", "OFFICIAL_FORECASTEX_DOC", "https://forecastex.com/data"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIKIT_LEARN_DOC", "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIKIT_LEARN_DOC", "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIKIT_LEARN_DOC", "https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIKIT_LEARN_DOC", "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIPY_DOC", "https://docs.scipy.org/doc/scipy/reference/optimize.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIPY_DOC", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIPY_DOC", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_SCIPY_DOC", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.zscore.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_NUMPY_DOC", "https://numpy.org/doc/stable/reference/generated/numpy.cov.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_NUMPY_DOC", "https://numpy.org/doc/stable/reference/generated/numpy.var.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_NUMPY_DOC", "https://numpy.org/doc/stable/reference/generated/numpy.percentile.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_PANDAS_DOC", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_PANDAS_DOC", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_PANDAS_DOC", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html"),
    ("LANE_D_FORMULA_LIBRARY", "OFFICIAL_PANDAS_DOC", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.quantile.html"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/RSI.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/MACD.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/BBANDS.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/EMA.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/SMA.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/ATR.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/ROC.htm"),
    ("LANE_D_TECHNICAL_INDICATORS", "REPUTABLE_LIBRARY_DOC", "https://ta-lib.github.io/ta-doc/indicator/OBV.htm"),
    ("LANE_D_PORTFOLIO_OPTIMIZER", "REPUTABLE_LIBRARY_DOC", "https://pyportfolioopt.readthedocs.io/en/latest/MeanVariance.html"),
    ("LANE_D_PORTFOLIO_OPTIMIZER", "REPUTABLE_LIBRARY_DOC", "https://pyportfolioopt.readthedocs.io/en/latest/RiskModels.html"),
    ("LANE_D_PORTFOLIO_OPTIMIZER", "REPUTABLE_LIBRARY_DOC", "https://pyportfolioopt.readthedocs.io/en/latest/ExpectedReturns.html"),
    ("LANE_E_QUANTUM", "OFFICIAL_DWAVE_DOC", "https://docs.dwavequantum.com/en/latest/concepts/models.html"),
    ("LANE_E_QUANTUM", "OFFICIAL_DWAVE_DOC", "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html"),
    ("LANE_E_QUANTUM", "OFFICIAL_QISKIT_DOC", "https://qiskit-community.github.io/qiskit-optimization/tutorials/06_examples_max_cut_and_tsp.html"),
    ("LANE_E_QUANTUM", "OFFICIAL_QISKIT_DOC", "https://qiskit-community.github.io/qiskit-optimization/tutorials/03_minimum_eigen_optimizer.html"),
    ("LANE_E_QUANTUM", "OFFICIAL_QISKIT_DOC", "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html"),
)

_NON_OFFICIAL_SOURCES = (
    ("LANE_F_RESEARCH", "INSTITUTIONAL_RESEARCH_CANDIDATE", "https://docs.dune.com/data-catalog/curated/prediction-markets/overview/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://www.deltabase.tech/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://www.probalytics.io/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://www.entityml.com/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://www.pmxt.dev/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://tickfoundry.com/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://pred-markets.com/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATA_VENDOR_CANDIDATE", "https://predictiondata.dev/"),
    ("LANE_F_RESEARCH", "NON_OFFICIAL_DATASET_CANDIDATE", "https://www.foresightflow.org/datasets/pmxt-stylized-facts-v1"),
    ("LANE_F_RESEARCH", "RESEARCH_CANDIDATE", "https://arxiv.org/abs/2605.11640"),
    ("LANE_F_RESEARCH", "RESEARCH_CANDIDATE", "https://arxiv.org/abs/2602.19520"),
    ("LANE_F_RESEARCH", "RESEARCH_CANDIDATE", "https://arxiv.org/abs/2604.03888"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Kelly_criterion"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Value_at_risk"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Expected_shortfall"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Sharpe_ratio"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Bollinger_Bands"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Relative_strength_index"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/MACD"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Volume-weighted_average_price"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Drawdown_(economics)"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Slippage_(finance)"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Prediction_market"),
    ("LANE_F_RESEARCH", "PUBLIC_REFERENCE_CANDIDATE", "https://en.wikipedia.org/wiki/Market_scoring_rule"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/Polymarket/py-clob-client"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/Polymarket/clob-client"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/kalshi/kalshi-python"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/dwavesystems/dimod"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/qiskit-community/qiskit-optimization"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/robertmartin8/PyPortfolioOpt"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/TA-Lib/ta-lib"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/scikit-learn/scikit-learn"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/scipy/scipy"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/numpy/numpy"),
    ("LANE_F_RESEARCH", "PUBLIC_CODE_RESEARCH_CANDIDATE", "https://github.com/pandas-dev/pandas"),
)


def external_source_records(qku_pool: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (lane, source_class, locator) in enumerate((*_OFFICIAL_SOURCES, *_NON_OFFICIAL_SOURCES), start=1):
        official = index <= len(_OFFICIAL_SOURCES)
        tier = classify_source_tier(source_class, locator)
        score, authority, confidence = score_source(tier, official)
        qku_ref = qku_pool[(index - 1) % len(qku_pool)] if qku_pool else "PR162D_R1_EXTERNAL_QKU_BACKLOG"
        rows.append(
            {
                "source_id": f"PR162D_R1_SOURCE_{index:03d}",
                "source_lane": lane,
                "source_locator": locator,
                "source_tier": tier,
                "source_class": source_class,
                "source_quality_score": score,
                "authority_class": authority,
                "confidence_class": confidence,
                "official_truth_flag": official,
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": True,
                "not_official_external_fact_flag": not official,
                "candidate_labels": _candidate_labels(official),
                "qku_refs": [qku_ref],
                "formula_refs": [f"PR162D_R1_FORMULA_SOURCE_BINDING_{index:03d}"],
                "field_refs": [f"external_source_field_map_{index:03d}"],
                "agent_route_refs": [
                    "QKU_DATA_ACQUISITION_AGENT",
                    "QKU_FORMULA_COMPUTE_ENGINE",
                    "REPLAY_PAPER_CANDIDATE_ROUTER",
                ],
                "replay_paper_route_refs": [
                    "PR162D_R1_REPLAY_PAPER_CANDIDATE_QUEUE",
                    f"PR162D_R1_SOURCE_REPLAY_ROUTE_{index:03d}",
                ],
                "snapshot_mode": "OFFLINE_SAFE_LOCATOR_AND_FIELD_SUMMARY_ONLY",
                "live_order_authority": False,
            }
        )
    return rows


def _candidate_labels(official: bool) -> list[str]:
    if official:
        return ["OFFICIAL_OR_REPUTABLE_CANDIDATE", "REPLAY_PAPER_DATA_FORMULA_ROUTE"]
    return [
        "RESEARCH_CANDIDATE",
        "PROVISIONAL_CANDIDATE",
        "NON_OFFICIAL_REPLAY_PAPER_CANDIDATE",
        "NOT_OFFICIAL_EXTERNAL_FACT",
    ]
