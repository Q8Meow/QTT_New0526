from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator.validator import validate_artifacts

from .helpers import REPO_ROOT


def test_pr166_q_validator_passes_generated_artifacts():
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures
