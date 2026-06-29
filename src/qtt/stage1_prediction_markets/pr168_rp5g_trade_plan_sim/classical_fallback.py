"""Classical fallback baseline helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from .models import score


def best_classical_candidate(scores: Mapping[str, Decimal]) -> dict[str, str]:
    if not scores:
        return {"classical_fallback_solver_ref": "DETERMINISTIC_ARGMAX_NO_CANDIDATES", "best_candidate_id": "NO_TRADE", "objective_value": score(0)}
    cid, value = max(scores.items(), key=lambda item: item[1])
    return {"classical_fallback_solver_ref": "DETERMINISTIC_ARGMAX_BASELINE", "best_candidate_id": cid, "objective_value": score(value)}

