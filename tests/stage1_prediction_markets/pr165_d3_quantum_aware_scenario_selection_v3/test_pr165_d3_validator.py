from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.validator import validate_repo


def test_pr165_d3_validator():
    result = validate_repo(REPO_ROOT)
    assert result["validated_report_count"] == 136
    assert result["authority_zero_counts_validated"] is True
