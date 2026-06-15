from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr166_sm3_score_memory_refresh_v3.validator import validate_artifacts

from .helpers import REPO_ROOT


def test_pr166_sm3_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:10]
