from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_builder_verify_idempotent():
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py",
            "--verify-idempotent",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PR165_D2_SCORE_REFRESHED_SELECTION_IDEMPOTENT" in result.stdout
