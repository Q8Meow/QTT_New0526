"""Owner-approved PR161D scoring-policy surface."""

from __future__ import annotations

from . import constants as c


def load_scoring_policy() -> dict[str, object]:
    return {
        "score_range_min": c.SCORE_RANGE_MIN,
        "score_range_max": c.SCORE_RANGE_MAX,
        "score_component_weights": dict(c.SCORE_COMPONENT_WEIGHTS),
        "score_component_weight_sum": round(sum(c.SCORE_COMPONENT_WEIGHTS.values()), 10),
        "owner_approved_internal_candidate_triage_weights_flag": True,
        "not_profit_evidence_flag": True,
        "not_replay_paper_result_flag": True,
        "not_live_trading_authority_flag": True,
    }
