from __future__ import annotations

from .helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_s2_replay_paper_retest_loop_v2.validator import validate_artifacts


def test_pr166_s2_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures
