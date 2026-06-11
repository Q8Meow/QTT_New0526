"""External design scouting ledger for PR166-S.

Rows are candidate/provisional design references only. They do not create
source-truth, connector, live-order, or quantum-backend authority.
"""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref
from .input_consumption import row_contract


def build_external_design_scout_rows() -> list[dict[str, Any]]:
    seeds = [
        {
            "title": "PredictionMarketBench",
            "source_url": "https://arxiv.org/abs/2602.00133",
            "source_authority_label": "EXTERNAL_RESEARCH_CANDIDATE_PROVISIONAL",
            "design_signal": "deterministic event-driven prediction-market replay with order-book, trade, lifecycle, settlement, maker/taker, fee, and metric streams",
            "pr166_s_use": "event stream, maker/taker fill semantics, binary payoff settlement assumptions",
        },
        {
            "title": "Bridging the Reality Gap in Limit Order Book Simulation",
            "source_url": "https://arxiv.org/abs/2603.24137",
            "source_authority_label": "EXTERNAL_RESEARCH_CANDIDATE_PROVISIONAL",
            "design_signal": "execution realism depends on spread, volume imbalance, latency timing, market impact, and PnL parameter sensitivity",
            "pr166_s_use": "latency, liquidity, market-impact, and slippage sensitivity grid",
        },
        {
            "title": "QuantConnect LEAN reality modeling",
            "source_url": "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts",
            "source_authority_label": "EXTERNAL_DOCUMENTATION_CANDIDATE_PROVISIONAL",
            "design_signal": "separate fill, fee, slippage, settlement, and capacity models for realistic backtests",
            "pr166_s_use": "separated PR166-S core tables for fill, fee, slippage, settlement, and liquidity/capacity",
        },
        {
            "title": "D-Wave Ocean model documentation",
            "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
            "source_authority_label": "EXTERNAL_DOCUMENTATION_CANDIDATE_PROVISIONAL",
            "design_signal": "BQM/QUBO/Ising, CQM, and DQM model classes are distinct advisory formulation lanes",
            "pr166_s_use": "quantum advisory passthrough route labels without backend execution",
        },
        {
            "title": "Qiskit Optimization QuadraticProgram documentation",
            "source_url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/01_quadratic_program.html",
            "source_authority_label": "EXTERNAL_DOCUMENTATION_CANDIDATE_PROVISIONAL",
            "design_signal": "QuadraticProgram provides a modeling route that can be converted to QUBO/Ising for comparator work",
            "pr166_s_use": "PR166-Q advisory passthrough fields for QuadraticProgram and QUBO conversion candidates",
        },
    ]
    rows: list[dict[str, Any]] = []
    for index, seed in enumerate(seeds, start=1):
        row_id = ordinal_ref("PR166_S_EXTERNAL_SCOUT", index)
        rows.append(
            {
                "external_design_scout_id": row_id,
                "candidate_design_reference": seed["title"],
                "source_url": seed["source_url"],
                "source_authority_label": seed["source_authority_label"],
                "useful_external_information_intake": "ALLOWED_WHEN_SAFE_RELEVANT_MAPPABLE_AND_REPLAY_PAPER_USEFUL",
                "non_official_source_rejection_due_only_to_non_official_status": "PROHIBITED",
                "source_truth_conversion_by_PR166_S": False,
                "design_signal": seed["design_signal"],
                "pr166_s_design_use": seed["pr166_s_use"],
                "replay_paper_only": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref=seed["source_url"],
                    source_row_ref=seed["title"],
                    computed_by_module="external_design_scouting",
                    owning_agent="risk_agent",
                    consuming_agent="replay_agent",
                    downstream_action_type="candidate design pattern intake",
                    downstream_artifact_route="PR166_S_ExecutionModelAssumptionLedger.report.json",
                ),
            }
        )
    return rows
