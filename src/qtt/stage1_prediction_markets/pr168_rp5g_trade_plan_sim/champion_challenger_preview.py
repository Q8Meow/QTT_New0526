"""Champion/challenger preview without final authority."""

from __future__ import annotations


def future_review_eligibility(*, beats_no_trade: bool, lcb_positive: bool, scenario_pass: bool, route_complete: bool) -> dict[str, object]:
    eligible = beats_no_trade and lcb_positive and scenario_pass and route_complete
    return {
        "champion_selection_authority": "NONE_IN_RP5G",
        "final_champion_selected_flag": False,
        "rank4_required_flag": True,
        "qopt1_required_flag": True,
        "vs2_required_before_paper_intent_flag": True,
        "champion_eligible_for_future_review_flag": eligible,
    }

