from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion import constants as c
from src.qtt.stage1_prediction_markets.pr162d_r1_external_formula_data_quantum_acquisition_expansion.validator import validate_artifacts


def test_pr162d_r1_validation_gate_and_branch_context_wiring(summary):
    repo_root = Path(__file__).resolve().parents[3]
    assert summary["active_branch"] == c.EXPECTED_BRANCH
    result = validate_artifacts(repo_root)
    assert result.ok, result.failures
