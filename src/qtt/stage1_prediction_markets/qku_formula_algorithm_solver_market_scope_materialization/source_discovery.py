"""PR162B upstream artifact discovery and loading."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.compact_records import (
    expand_payload_records as expand_pr161f_payload_records,
)

from . import constants as c
from .json_io import read_json, records_from_payload
from .paths import normalize_repo_relative_ref, resolve_repo_relative


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def ensure_required_inputs(repo_root: Path) -> list[str]:
    missing = [
        ref
        for ref in c.REQUIRED_INPUT_REPORTS
        if not resolve_repo_relative(repo_root, ref).exists()
    ]
    if missing:
        raise FileNotFoundError("missing PR162B required inputs: " + ", ".join(missing))
    return [normalize_repo_relative_ref(repo_root, ref) for ref in c.REQUIRED_INPUT_REPORTS]


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(repo_root / c.GENERATED_DIR / filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest_name = filename.split("_", 1)[0] + "_ReportShardManifest.report.json"
    manifest_path = repo_root / c.GENERATED_DIR / manifest_name
    if not manifest_path.exists() and filename.startswith("PR162A_"):
        manifest_path = repo_root / c.GENERATED_DIR / "PR162A_ReportShardManifest.report.json"
    if not manifest_path.exists() and filename.startswith("PR162_"):
        manifest_path = repo_root / c.GENERATED_DIR / "PR162_ReportShardManifest.report.json"
    manifest_payload = read_json(manifest_path)
    manifest_by_report = {
        record["report_filename"]: record
        for record in records_from_payload(manifest_payload)
    }
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_by_report[filename]["shard_files"]:
        rows.extend(records_from_payload(read_json(resolve_repo_relative(repo_root, shard_ref))))
    return rows


def load_pr161f_records(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    shared_payload = read_json(repo_root / c.GENERATED_DIR / "PR161F_SharedDictionary.report.json")
    shared_dictionary = shared_payload["shared_dictionary"]
    manifest_payload = read_json(repo_root / c.GENERATED_DIR / "PR161F_ReportShardManifest.report.json")
    manifest_by_report = {
        record["report_filename"]: record
        for record in records_from_payload(manifest_payload)
    }
    loaded: dict[str, list[dict[str, Any]]] = {}
    for filename in c.PR161F_REPORTS_REQUIRED:
        payload = read_json(repo_root / c.GENERATED_DIR / filename)
        if not payload.get("sharded_flag"):
            loaded[filename] = expand_pr161f_payload_records(payload, shared_dictionary)
            continue
        rows: list[dict[str, Any]] = []
        for shard_ref in manifest_by_report[filename]["shard_files"]:
            shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
            rows.extend(expand_pr161f_payload_records(shard_payload, shared_dictionary))
        loaded[filename] = rows
    return loaded


def load_upstream_context(repo_root: Path) -> dict[str, Any]:
    qku_records = read_json(
        repo_root / c.GENERATED_DIR / "PR161C_QKUCanonicalRegistry.report.json"
    )["records"]
    pr161d_quality = read_json(
        repo_root / c.GENERATED_DIR / "PR161D_QKUQualityScoreRegistry.report.json"
    )["records"]
    pr162a_mapping = load_report_records(repo_root, "PR162A_MarketScenarioQKUMappingMatrix.report.json")
    pr162a_rerun = load_report_records(repo_root, "PR162A_PR162AdapterRerunReadinessBridge.report.json")
    pr162a_pr163 = read_json(
        repo_root / c.GENERATED_DIR / "PR162A_PR163ReadinessBlockerStatus.report.json"
    )["records"]
    pr161f = load_pr161f_records(repo_root)
    return {
        "qku_records": qku_records,
        "pr161d_quality": pr161d_quality,
        "pr162a_mapping": pr162a_mapping,
        "pr162a_rerun": pr162a_rerun,
        "pr162a_pr163": pr162a_pr163,
        "pr161f": pr161f,
    }


def formula_source_retrieval_target_records() -> list[dict[str, Any]]:
    targets = [
        (
            "prediction_market_formulas",
            ["Kalshi docs", "Polymarket docs", "ForecastEx public docs", "expected-value canonical references"],
            [
                "implied_probability_from_binary_price",
                "fair_price_from_probability",
                "expected_value_binary",
                "fee_adjusted_expected_value",
                "slippage_adjusted_expected_value",
                "latency_adjusted_expected_value",
                "probability_edge",
                "binary_payoff_profit_loss",
                "break_even_probability",
                "no_trade_zone_threshold",
                "prediction_market_position_selection_objective",
            ],
            "OFFICIAL_VENUE_DOC_FIELD_CANDIDATE",
            "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
        ),
        (
            "calibration_formulas",
            ["scikit-learn docs", "canonical ML calibration references"],
            [
                "brier_score_binary",
                "log_loss_binary",
                "calibration_error_candidate",
                "probability_clipping",
                "confidence_penalty",
            ],
            "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE",
            "MARKET_AGNOSTIC_MATH",
        ),
        (
            "position_sizing_formulas",
            ["Kelly criterion sources", "QuantConnect docs", "institutional risk sources"],
            [
                "kelly_fraction",
                "fractional_kelly",
                "capped_kelly",
                "drawdown_capped_kelly",
                "risk_budget_capped_position_size",
                "max_exposure_cap",
                "per_market_cap",
                "per_event_cap",
            ],
            "TEXTBOOK_FORMULA_CANDIDATE",
            "MARKET_AGNOSTIC_RISK",
        ),
        (
            "risk_portfolio_formulas",
            ["PyPortfolioOpt docs", "SciPy optimize docs", "institutional risk references"],
            [
                "mean_return",
                "variance",
                "covariance",
                "correlation",
                "volatility",
                "sharpe_ratio",
                "max_drawdown",
                "VaR_candidate",
                "CVaR_candidate",
                "risk_adjusted_expected_value",
                "mean_variance_objective",
                "portfolio_qp_objective",
            ],
            "OPEN_SOURCE_PACKAGE_FORMULA_CANDIDATE",
            "MARKET_AGNOSTIC_RISK",
        ),
        (
            "technical_feature_formulas",
            ["TA-Lib docs", "pandas docs", "NumPy docs"],
            [
                "SMA",
                "EMA",
                "RSI",
                "MACD",
                "Bollinger Bands",
                "z-score",
                "momentum",
                "realized volatility",
                "VWAP candidate",
                "midpoint",
                "spread",
                "orderbook_imbalance_candidate",
                "liquidity_proxy",
            ],
            "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE",
            "MARKET_AGNOSTIC_FEATURE",
        ),
        (
            "classical_optimizer_formulas",
            ["SciPy optimize docs", "PyPortfolioOpt docs", "cvxpy docs if installed"],
            [
                "linear objective",
                "quadratic objective",
                "bounded optimization contract",
                "equality constraint",
                "inequality constraint",
                "penalty objective",
                "multi-objective weighted sum",
                "constrained_minimize_mapping",
            ],
            "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE",
            "MARKET_AGNOSTIC_OPTIMIZER",
        ),
        (
            "quantum_hybrid_formulas",
            ["D-Wave docs", "Qiskit Optimization docs", "IBM Quantum docs", "PR162 quantum blueprints"],
            [
                "QUBO objective x^T Q x",
                "expanded QUBO terms",
                "Ising energy",
                "BQM formulation",
                "CQM formulation",
                "penalty constraint lambda(Ax-b)^2",
                "QUBO portfolio selection objective",
                "QUBO prediction-market position selection objective",
                "QUBO market-bundle selection objective",
                "QUBO parameter-stack selection objective",
                "QUBO risk-budget objective",
                "QAOA Hamiltonian mapping candidate",
                "VQE objective candidate",
                "annealing BQM/CQM candidate",
                "hybrid classical-quantum comparator objective",
            ],
            "OFFICIAL_LIBRARY_DOC_FORMULA_CANDIDATE",
            "MARKET_AGNOSTIC_OPTIMIZER",
        ),
        (
            "algorithm_families",
            ["repo formulas", "official library docs", "open-source implementations", "research candidates"],
            [
                "binary_edge_signal_algorithm",
                "EV-gated no-trade algorithm",
                "capped Kelly sizing algorithm",
                "risk-budget sizing algorithm",
                "probability clipping algorithm",
                "z-score signal algorithm",
                "portfolio/market-bundle selection algorithm candidate",
                "exact tiny QUBO smoke enumeration algorithm",
                "QUBO solver-input assembly algorithm",
                "Ising solver-input assembly algorithm",
                "replay/paper feature-computation algorithm route",
            ],
            "REPO_EXISTING_FORMULA",
            "NON_MARKET_SPECIFIC",
        ),
        (
            "market_scope_classification_sources",
            ["PR136 market index", "PR161C/D/F QKU graph reports", "Kalshi/Polymarket/ForecastEx docs", "master-plan market-sleeve sections"],
            [
                "QKU market taxonomy",
                "Stage-1 activation status",
                "dormant registry for non-stage-1 market QKUs",
            ],
            "REPO_EXISTING_FORMULA",
            "NON_MARKET_SPECIFIC",
        ),
    ]
    return [
        {
            "retrieval_target_id": f"PR162B-SOURCE-TARGET-{index:03d}",
            "target_family": family,
            "source_targets": source_targets,
            "expected_materialization_targets": materialization_targets,
            "source_class": source_class,
            "primary_market_scope": market_scope,
            "materialization_status": "MATERIALIZED_OR_BLOCKER_EMITTED",
            "ci_requires_network": False,
            "created_by_pr": c.PR_ID,
        }
        for index, (family, source_targets, materialization_targets, source_class, market_scope) in enumerate(targets, start=1)
    ]
