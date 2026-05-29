"""Profit validation state registry projection for PR159S."""

from __future__ import annotations

from typing import Any, Mapping


def build_profit_validation_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "profit_validation_state_id": f"PR159S_PROFIT_STATE__{index:04d}",
            "target_id_or_row_id": target["target_id_or_row_id"],
            "source_provenance_tag": target["source_provenance_tag"],
            "profit_validation_tag": target["profit_validation_tag"],
            "replay_paper_candidate_flag": target["replay_paper_candidate_flag"],
            "replay_paper_result_link": target["replay_paper_result_link"],
            "profit_status_basis": "no replay/paper result artifact linked in PR159S",
            "profit_proven_status_assigned_by_pr159s_flag": False,
            "non_profitable_status_assigned_by_pr159s_flag": False,
        }
        for index, target in enumerate(classified_targets, start=1)
    ]

