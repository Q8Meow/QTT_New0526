"""Replay episode construction for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, LoadedSelection, contexts_by_batch


def build_replay_episode_rows(selection: LoadedSelection) -> list[dict[str, Any]]:
    by_batch = contexts_by_batch(selection.contexts)
    rows: list[dict[str, Any]] = []
    for index, batch in enumerate(sorted(selection.batch_rows, key=lambda row: str(row["batch_id"])), start=1):
        batch_id = str(batch["batch_id"])
        members = by_batch.get(batch_id, [])
        ready_count = sum(1 for context in members if context.ready)
        row_id = ordinal_ref("PR166_S_REPLAY_EPISODE", index)
        rows.append(
            {
                "replay_episode_id": row_id,
                "run_id": stable_ref("PR166_S_REPLAY_RUN", batch_id),
                "source_selected_batch_id": batch_id,
                "selected_candidate_ids": [context.candidate_packet_id for context in members],
                "run_mode": "REPLAY",
                "episode_status": "REPLAY_EPISODE_CONSTRUCTED",
                "execution_classification": (
                    "REPLAY_EXECUTED" if ready_count else "REPAIR_REQUIRED_BEFORE_EXECUTION"
                ),
                "event_stream_ref": stable_ref("PR166_S_EVENT_STREAM", batch_id, "REPLAY"),
                "uses_historical_or_fixture_event_stream": True,
                "bounded_fixture_execution_flag": True,
                "no_live_market_state_used": True,
                "no_private_state_used": True,
                "no_live_authority": True,
                "no_profit_evidence": True,
                "no_quantum_backend_execution": True,
                "ready_candidate_count": ready_count,
                "repair_candidate_count": len(members) - ready_count,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_RetestBatchSelectionQueue.report.json",
                    source_row_ref=batch_id,
                    computed_by_module="replay_episode_builder",
                    owning_agent="replay_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="replay episode execution input",
                    downstream_artifact_route="PR166_S_EventStreamRegistry.report.json",
                    replay_paper_scope="REPLAY_ONLY",
                ),
            }
        )
    return rows


def replay_episode_ref_for_context(context: ExecutionContext) -> str:
    return stable_ref("PR166_S_REPLAY_RUN", context.batch_id)
