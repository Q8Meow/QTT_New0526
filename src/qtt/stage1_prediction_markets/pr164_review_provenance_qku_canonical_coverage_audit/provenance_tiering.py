"""Provenance tiering rows."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_provenance_tier_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "provenance_tier_record_ref": plain_ref("PROVENANCE", index),
            "candidate_id": row["candidate_id"],
            "qku_ids": row["qku_ids"],
            "evidence_id": row["evidence_id"],
            "evidence_tier": row["evidence_tier"],
            "provenance_tier_reason": "PR163-B paired replay/paper candidate evidence is repo-local deterministic candidate evidence, not source acceptance or final result authority.",
            "intended_consumer": "pr165_scoring_agent",
            "validation_status": "PASS",
        }
        for index, row in enumerate(evidence_rows, 1)
    ]
