from __future__ import annotations

from tools.pr168_map3_config import ONLINE_SCOUT_ROWS


def build_online_scout_rows() -> list[dict]:
    return [dict(row) for row in ONLINE_SCOUT_ROWS]
