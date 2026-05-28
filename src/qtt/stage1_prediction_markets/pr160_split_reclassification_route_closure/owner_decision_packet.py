"""Owner decision packet construction for ambiguous PR160 routes."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build(decisions: list[Mapping[str, Any]]) -> dict[str, Any]:
    questions: list[dict[str, Any]] = []
    for item in decisions:
        if (
            item["final_route_class"]
            != c.ReclassificationFinalRouteClass.OWNER_CLASSIFICATION_DECISION_REQUIRED_WITH_CHOICES.value
        ):
            continue
        questions.append(
            {
                "question_id": f"PR160_OWNER_CHOICE__{item['PR154_target_id']}",
                "PR154_target_id": item["PR154_target_id"],
                "current_ambiguity": "Multiple plausible route classes remain after deterministic evidence review.",
                "candidate_route_choices": [],
                "recommended_choice_or_null": None,
                "recommendation_basis_or_null": None,
                "pros_cons": [],
                "authority_class_for_each_choice": {},
                "source_fact_risk_flag_for_each_choice": {},
                "owner_may_decide_flag": True,
                "owner_decision_cannot_create_external_fact_flag": True,
                "private_doc_attestation_required_flag": False,
                "exact_agent_id_invention_forbidden_flag": True,
                "source_acceptance_forbidden_in_PR160_flag": True,
                "future_route_for_each_choice": {},
                "exact_acceptance_criteria": "Owner chooses only an internal classification route; source facts still require PR159R.",
                "validator_that_will_unblock": c.PR160_VALIDATOR,
            }
        )
    return {
        "packet_type": "PR160_OWNER_RECLASSIFICATION_DECISION_REQUEST",
        "decision_required_count": len(questions),
        "questions": questions,
        "owner_response_file_created_by_PR160_flag": False,
        "owner_approval_created_by_PR160_flag": False,
        "source_acceptance_forbidden_in_PR160_flag": True,
    }
