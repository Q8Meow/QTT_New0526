"""Execution model assumption ledger for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract


def build_execution_model_assumption_rows(
    replay_episode_rows: list[dict[str, Any]],
    paper_episode_rows: list[dict[str, Any]],
    optional_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    optional_refs = [row["optional_replay_paper_input_receipt_id"] for row in optional_rows]
    index = 0
    for mode, episodes in (("REPLAY", replay_episode_rows), ("PAPER", paper_episode_rows)):
        for episode in episodes:
            index += 1
            row_id = ordinal_ref("PR166_S_EXECUTION_ASSUMPTION", index)
            rows.append(
                {
                    "execution_model_assumption_id": row_id,
                    "source_selected_batch_id": episode["source_selected_batch_id"],
                    "run_mode": mode,
                    "assumption_status": "BOUNDED_FIXTURE_EXECUTION_ASSUMPTIONS_RECORDED",
                    "market_data_assumption": "BOUNDED_SYNTHETIC_FIXTURE_FROM_PR165_D_SELECTION_FEATURES",
                    "paper_adapter_assumption": "SIMULATED_ADAPTER_ONLY",
                    "fill_assumption": "DETERMINISTIC_MAKER_TAKER_PARTIAL_NO_FILL_STATE_MACHINE",
                    "cost_assumption": "FEE_SPREAD_SLIPPAGE_LATENCY_LIQUIDITY_IMPACT_SETTLEMENT_COMPONENT_SUM",
                    "settlement_assumption": "CANDIDATE_PROVISIONAL_REPLAY_ONLY_NO_SOURCE_TRUTH_PROMOTION",
                    "optional_input_receipt_refs": optional_refs,
                    "model_assumption_ref": stable_ref("PR166_S_EXECUTION_ASSUMPTION_REF", episode["source_selected_batch_id"], mode),
                    "repair_route_when_too_weak": "EXECUTION_MODEL_WEAK",
                    "no_live_authority": True,
                    "no_source_truth_promotion": True,
                    **row_contract(
                        row_id=row_id,
                        source_artifact_ref="PR166_S_ReplayEpisodeRegistry.report.json" if mode == "REPLAY" else "PR166_S_PaperEpisodeRegistry.report.json",
                        source_row_ref=episode["run_id"],
                        computed_by_module="execution_model_assumptions",
                        owning_agent="execution_simulation_agent",
                        consuming_agent="risk_agent",
                        downstream_action_type="execution model assumption audit input",
                        downstream_artifact_route="PR166_S_ResultConfidenceRegistry.report.json",
                    ),
                }
            )
    return rows
