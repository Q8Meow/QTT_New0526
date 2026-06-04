from __future__ import annotations

from pathlib import Path

import tools.ci_branch_context as branch_context
import tools.run_validation_gates as runner
from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations import paths as p
from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.validators import validate_artifacts


def test_validation_wiring(summary, repo_root):
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert summary["active_branch"] == p.EXPECTED_BRANCH
    assert "validate_pr162d_r2a_real_formulations.py" in command_names
    assert branch_context.is_explicit_downstream_repair_changed_path(
        p.EXPECTED_BRANCH,
        "docs/master_plan/generated/PR162D_R2A_FinalSummary.report.json",
    )
    result = validate_artifacts(repo_root)
    assert result.ok, result.failures
