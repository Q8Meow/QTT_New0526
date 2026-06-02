"""PR162C source quality tier helper."""

from __future__ import annotations


def quality_tier_for_materialization(materialized: bool, fetch_plan_only: bool) -> str:
    if materialized:
        return "REPO_LOCAL_CANDIDATE_DATA_PRESENT"
    if fetch_plan_only:
        return "FETCH_PLAN_ONLY_OWNER_COMMAND_REQUIRED"
    return "REGISTERED_PUBLIC_DOC_OR_LOCATOR_ONLY"
