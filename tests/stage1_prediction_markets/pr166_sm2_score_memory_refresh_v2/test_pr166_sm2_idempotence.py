from __future__ import annotations

import subprocess
import sys

from .helpers import REPO_ROOT


def test_pr166_sm2_builder_verify_idempotent():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/build_pr166_sm2_score_memory_refresh_v2.py",
            "--verify-idempotent",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PR166_SM2_SCORE_MEMORY_REFRESH_V2_IDEMPOTENT" in completed.stdout
