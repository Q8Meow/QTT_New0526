"""Research candidate extraction projections."""

from __future__ import annotations

from typing import Any, Mapping


def build_research_candidate_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_record_id": f"PR159S_RESEARCH_CANDIDATE__{index:04d}",
            "target_id_or_row_id": target["target_id_or_row_id"],
            "terminal_completion_state": target["terminal_completion_state"],
            "source_provenance_tag": target["source_provenance_tag"],
            "authority_class": target["authority_class"],
            "source_class": target["source_class"],
            "source_quality_tier": target["source_quality_tier"],
            "profit_validation_tag": target["profit_validation_tag"],
            "claim_type": target["source_claim_type"],
            "candidate_extraction": target["field_value"],
            "replay_paper_candidate_flag": target["replay_paper_candidate_flag"],
            "promotion_limitations": target["promotion_limitations"],
        }
        for index, target in enumerate(classified_targets, start=1)
        if target["replay_paper_candidate_flag"]
    ]

