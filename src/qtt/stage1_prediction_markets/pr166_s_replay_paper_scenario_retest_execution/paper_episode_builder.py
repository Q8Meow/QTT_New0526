"""Paper/simulated-adapter episode construction for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, LoadedSelection, contexts_by_batch


def build_paper_episode_rows(selection: LoadedSelection) -> list[dict[str, Any]]:
    by_batch = contexts_by_batch(selection.contexts)
    rows: list[dict[str, Any]] = []
    for index, batch in enumerate(sorted(selection.batch_rows, key=lambda row: str(row["batch_id"])), start=1):
        batch_id = str(batch["batch_id"])
        members = by_batch.get(batch_id, [])
        ready_count = sum(1 for context in members if context.ready)
        row_id = ordinal_ref("PR166_S_PAPER_EPISODE", index)
        rows.append(
            {
                "paper_episode_id": row_id,
                "run_id": stable_ref("PR166_S_PAPER_RUN", batch_id),
                "source_selected_batch_id": batch_id,
                "selected_candidate_ids": [context.candidate_packet_id for context in members],
                "run_mode": "PAPER",
                "episode_status": "PAPER_EPISODE_CONSTRUCTED",
                "execution_classification": (
                    "PAPER_EXECUTED" if ready_count else "REPAIR_REQUIRED_BEFORE_EXECUTION"
                ),
                "paper_adapter_label": "SIMULATED_ADAPTER_ONLY",
                "paper_state_machine_ref": stable_ref("PR166_S_PAPER_STATE_MACHINE", batch_id),
                "no_real_connector_api_call": True,
                "no_real_account_cash_access": True,
                "no_private_state_used": True,
                "no_live_authority": True,
                "no_profit_evidence": True,
                "ready_candidate_count": ready_count,
                "repair_candidate_count": len(members) - ready_count,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_RetestBatchSelectionQueue.report.json",
                    source_row_ref=batch_id,
                    computed_by_module="paper_episode_builder",
                    owning_agent="paper_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="paper simulated-adapter episode execution input",
                    downstream_artifact_route="PR166_S_OrderIntentRegistry.report.json",
                    replay_paper_scope="PAPER_ONLY",
                ),
            }
        )
    return rows


def paper_episode_ref_for_context(context: ExecutionContext) -> str:
    return stable_ref("PR166_S_PAPER_RUN", context.batch_id)
