"""Paper/simulated-adapter run result registry builder for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract
from .selected_batch_loader import numeric


def build_paper_run_result_rows(
    paper_episode_rows: list[dict[str, Any]],
    attribution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attrs_by_batch: dict[str, list[dict[str, Any]]] = {}
    for attr in attribution_rows:
        attrs_by_batch.setdefault(str(attr["source_selected_batch_id"]), []).append(attr)
    rows: list[dict[str, Any]] = []
    for index, episode in enumerate(paper_episode_rows, start=1):
        batch_id = str(episode["source_selected_batch_id"])
        attrs = attrs_by_batch.get(batch_id, [])
        row_id = f"PR166_S_PAPER_RUN_RESULT::{index:06d}"
        avg_net = _avg(attrs, "net_return_proxy")
        rows.append(
            {
                "paper_run_result_id": row_id,
                "run_id": episode["run_id"],
                "source_selected_batch_id": batch_id,
                "run_mode": "PAPER",
                "paper_adapter_label": "SIMULATED_ADAPTER_ONLY",
                "run_status": "PAPER_EXECUTED" if attrs else "REPAIR_REQUIRED_BEFORE_EXECUTION",
                "tested_candidate_count": len(attrs),
                "positive_net_edge_count": sum(1 for attr in attrs if numeric(attr.get("net_return_proxy"), 0.0) > 0),
                "failed_after_cost_count": sum(1 for attr in attrs if numeric(attr.get("net_return_proxy"), 0.0) <= 0),
                "average_net_edge_after_costs": round(avg_net - (0.001 if attrs else 0.0), 6),
                "input_artifact_refs": episode["upstream_artifact_refs"],
                "model_assumption_refs": ["PR166_S_ExecutionModelAssumptionLedger.report.json"],
                "fee_model_ref": "PR166_S_FeeModelLedger.report.json",
                "slippage_model_ref": "PR166_S_SlippageModelLedger.report.json",
                "latency_model_ref": "PR166_S_LatencyModelLedger.report.json",
                "liquidity_model_ref": "PR166_S_LiquidityModelLedger.report.json",
                "settlement_assumption_ref": "PR166_S_SettlementAssumptionLedger.report.json",
                "no_real_connector_api_call": True,
                "no_private_state_used": True,
                "no_live_authority": True,
                "no_profit_evidence": True,
                "no_quantum_backend_execution": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_PaperEpisodeRegistry.report.json",
                    source_row_ref=episode["paper_episode_id"],
                    computed_by_module="paper_run_engine",
                    owning_agent="paper_agent",
                    consuming_agent="commander_agent",
                    downstream_action_type="paper run result handoff input",
                    downstream_artifact_route="PR166_S_CommanderExecutionHandoff.report.json",
                    replay_paper_scope="PAPER_ONLY",
                ),
            }
        )
    return rows


def _avg(rows: list[dict[str, Any]], field: str) -> float:
    if not rows:
        return 0.0
    return round(sum(numeric(row.get(field), 0.0) for row in rows) / len(rows), 6)
