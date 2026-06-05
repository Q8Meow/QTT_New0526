from pathlib import Path

from src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun.validators import (
    validate_artifacts,
)
from tools import run_validation_gates


def test_validation_wiring(repo_root):
    result = validate_artifacts(repo_root)
    assert result.ok, result.failures
    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert command_names.count("validate_pr162r_generic_replay_paper_adapter_rerun.py") == 1
