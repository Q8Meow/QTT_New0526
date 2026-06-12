from .conftest import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest.validator import validate_artifacts


def test_pr166_sf_validator_passes():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:25]
