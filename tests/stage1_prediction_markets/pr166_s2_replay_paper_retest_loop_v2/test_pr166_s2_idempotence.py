from __future__ import annotations

import subprocess
import sys

from .helpers import REPO_ROOT


def test_pr166_s2_builder_verify_idempotent():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/build_pr166_s2_replay_paper_retest_loop_v2.py",
            "--verify-idempotent",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PR166_S2_REPLAY_PAPER_RETEST_LOOP_V2_IDEMPOTENT" in completed.stdout
