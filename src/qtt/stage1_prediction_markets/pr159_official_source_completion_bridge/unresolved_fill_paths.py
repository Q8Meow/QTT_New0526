"""Human-actionable unresolved fill-path records for PR159."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_unresolved_fill_paths(
    pr154_records: list[Mapping[str, Any]],
    atomicrows_records: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in pr154_records:
        if record["completion_status"] == c.SourceTargetState.ACCEPTED_COMPLETED.value:
            continue
        records.append(
            {
                "target_id_or_row_id": record["target_id"],
                "target_field_id": record["target_field_id"],
                "missing_value_or_range": record["requested_value_name"],
                "source_requirement_class": "PR154_PUBLIC_SOURCE_RETRY_REQUIRED",
                "blocker_class": record["blocker_class"],
                "blocker_reason_code": c.SourceEvidenceState.BLOCKED_TARGET_FIELD_SCOPE_MISMATCH.value,
                "attempted_official_source_queries": [
                    f"{record['platform_scope']} official source for {record['target_field_id']}"
                ],
                "candidate_sources_rejected": [],
                "exact_official_source_needed": "Official page, table, API schema field, SDK field, or rulebook section matching the target field exactly.",
                "exact_steps_to_fill": [
                    "Capture target-field-specific locator and short quote or machine-field path.",
                    "Extract value, range, enum, unit, scale, and basis without inference.",
                    "Run PR159 acceptance validator and record acceptance ledger only if conflict and freshness checks pass.",
                ],
                "exact_acceptance_criteria": "Official confirmed source, exact target-field scope, locator, canonical unit/scale, freshness, and conflict clearance.",
                "validator_that_will_unblock": "tools/validate_pr159_official_source_completion_bridge.py",
                "future_route": record["future_route"],
                "risk_if_unfilled": "Target remains blocked from connector/live use and cannot become a source-backed materialized value.",
                "can_qtt_use_in_scoring_metadata_flag": False,
                "can_qtt_use_in_replay_flag": False,
                "can_qtt_use_in_paper_flag": False,
                "can_qtt_use_in_live_flag": False,
            }
        )
    for record in atomicrows_records:
        records.append(
            {
                "target_id_or_row_id": record["row_id"],
                "target_field_id": record["target_field_id"],
                "missing_value_or_range": record["requested_value_name"],
                "source_requirement_class": record["source_requirement_class"],
                "blocker_class": record["blocker_class"],
                "blocker_reason_code": c.SourceEvidenceState.BLOCKED_AMBIGUOUS.value,
                "attempted_official_source_queries": [
                    f"official source for {record['family_id']} {record['source_requirement_class']}"
                ],
                "candidate_sources_rejected": [],
                "exact_official_source_needed": "Official target-specific range, limit, policy, API constraint, or provider/rulebook specification.",
                "exact_steps_to_fill": [
                    "Create a target-specific source evidence packet for this row.",
                    "Canonicalize the official range/value/unit/scale.",
                    "Regenerate PR159 and then route accepted rows to PR161 materialization.",
                ],
                "exact_acceptance_criteria": "Accepted source packet exists for the row target and passes PR159 validator checks.",
                "validator_that_will_unblock": "tools/validate_pr159_official_source_completion_bridge.py",
                "future_route": record["future_route"],
                "risk_if_unfilled": "Row remains non-consumable for scoring, ranking, selection, replay, paper, and live gates.",
                "can_qtt_use_in_scoring_metadata_flag": False,
                "can_qtt_use_in_replay_flag": False,
                "can_qtt_use_in_paper_flag": False,
                "can_qtt_use_in_live_flag": False,
            }
        )
    return sorted(records, key=lambda item: str(item["target_id_or_row_id"]))
