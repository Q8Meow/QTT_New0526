"""PR166-SM refreshed net-edge scoring."""

from __future__ import annotations

from . import constants as c
from .normalization import clamp, round6


def refreshed_net_edge_score(components: dict[str, float]) -> float:
    score = 0.0
    for field, weight in c.SCORE_WEIGHTS.items():
        score += weight * float(components[field])
    return round6(clamp(score))
