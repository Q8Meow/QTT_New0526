from .conftest import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.validator import (
    validate_artifacts,
)


def test_pr166_sm_generated_artifacts_validate():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:20]
