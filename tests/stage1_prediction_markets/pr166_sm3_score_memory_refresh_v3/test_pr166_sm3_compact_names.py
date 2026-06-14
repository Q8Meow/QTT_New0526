from __future__ import annotations

from .helpers import REPO_ROOT


def test_pr166_sm3_uses_compact_report_and_schema_names():
    forbidden = list(REPO_ROOT.glob("docs/master_plan/generated/PR166_SM3_*LongName*.report.json"))
    forbidden += list(REPO_ROOT.glob("src/qtt/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3/schemas/p_r166_s_m3_*.json"))
    assert forbidden == []
