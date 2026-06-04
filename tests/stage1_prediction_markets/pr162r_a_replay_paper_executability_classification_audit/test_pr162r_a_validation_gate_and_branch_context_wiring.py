from __future__ import annotations

from pathlib import Path

import tools.ci_branch_context as branch_context
import tools.run_validation_gates as runner
from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit import constants as c
from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.validator import validate_artifacts


def test_pr162r_a_validation_gate_and_branch_context_wiring(summary):
    repo_root = Path(__file__).resolve().parents[3]
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert summary["active_branch"] == c.EXPECTED_BRANCH
    assert "validate_pr162r_a_replay_paper_executability_classification_audit.py" in command_names
    assert branch_context.is_explicit_downstream_repair_changed_path(
        c.EXPECTED_BRANCH,
        "docs/master_plan/generated/PR162R_A_FinalSummary.report.json",
    )
    result = validate_artifacts(repo_root)
    assert result.ok, result.failures
