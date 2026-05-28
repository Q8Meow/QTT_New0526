"""Static scoring/ranking feature-role classification for PR158."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def scoring_feature_role(record: Mapping[str, Any]) -> str:
    tags = set(record.get("secondary_tags") or [])
    family_id = str(record.get("family_id") or "")
    source_requirement = str(record.get("source_requirement_class") or "")
    if source_requirement in {"PUBLIC_EXTERNAL_SOURCE_REQUIRED", "PARAMETER_RANGE_SOURCE_REQUIRED"}:
        return c.ScoringFeatureRole.NOT_SCORING_CONSUMABLE_YET.value
    if "risk_parameter" in tags:
        return c.ScoringFeatureRole.RISK_FILTER.value
    if "capital_parameter" in tags:
        return c.ScoringFeatureRole.CAPITAL_FILTER.value
    if "latency_parameter" in tags:
        return c.ScoringFeatureRole.LATENCY_FILTER.value
    if "execution_parameter" in tags:
        return c.ScoringFeatureRole.EXECUTION_FILTER.value
    if "optimizer_parameter" in tags:
        return c.ScoringFeatureRole.OPTIMIZER_ARBITRATION_FEATURE.value
    if (
        "quantum_inspired_candidate" in tags
        or "true_quantum_candidate" in tags
        or "hybrid_classical_quantum_candidate" in tags
    ):
        return c.ScoringFeatureRole.QUANTUM_PRIORITY_FEATURE.value
    if "replay_paper" in family_id:
        return c.ScoringFeatureRole.REPLAY_PAPER_EVALUATION_FEATURE.value
    if "error_guard_parameter" in tags:
        return c.ScoringFeatureRole.SCORE_CONSTRAINT.value
    if "scoring_ranking" in family_id:
        return c.ScoringFeatureRole.SCORE_WEIGHT.value
    if "statistical_edge" in tags or "microstructure_alpha" in tags or "classical_formula" in tags:
        return c.ScoringFeatureRole.SCORE_INPUT.value
    return c.ScoringFeatureRole.NOT_SCORING_CONSUMABLE_YET.value

