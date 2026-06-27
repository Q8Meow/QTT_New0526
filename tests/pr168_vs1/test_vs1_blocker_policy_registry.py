from __future__ import annotations

from ._helpers import rows


def test_vs1_blocker_policy_registry_defines_required_codes_without_global_bans():
    blockers = rows("vs1_blocker_policy_registry.jsonl")
    codes = {row["blocker_code"] for row in blockers}

    assert {
        "NO_TRADE_WINS",
        "NO_ELIGIBLE_POSITIVE_NET_CASH_PNL_CANDIDATE_FOUND",
        "REJECT_LCB_NOT_POSITIVE",
        "REJECT_FILL_TOO_LOW",
        "REJECT_TCA_WIPES_EDGE",
        "REJECT_CAPACITY_GATE",
        "REJECT_PORTFOLIO_GATE",
        "REJECT_SCENARIO_LADDER",
        "REJECT_AGENT_ROUTE",
        "REJECT_NO_ORPHAN_PROOF",
        "REJECT_UNKNOWN_NEEDS_REVIEW",
        "REJECT_METADATA_ONLY_BINDING",
        "REJECT_IMPOSSIBLE_PRICE",
        "REJECT_IMPOSSIBLE_FILL",
        "REJECT_GATE_RELAXATION_ATTEMPT",
        "REJECT_HINDSIGHT_BACKSOLVE",
        "REJECT_EXTERNAL_SOURCE_FACT_AUTHORITY",
    }.issubset(codes)
    assert all(row["global_ban_allowed_flag"] is False for row in blockers)
