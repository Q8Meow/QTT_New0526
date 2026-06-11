from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.validator import (
    validate_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_validator_passes_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures[:10]
