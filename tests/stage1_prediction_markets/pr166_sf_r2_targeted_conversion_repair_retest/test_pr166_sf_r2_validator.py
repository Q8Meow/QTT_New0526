from __future__ import annotations

from .helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest.validator import validate_artifacts


def test_pr166_sf_r2_validator_accepts_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures
