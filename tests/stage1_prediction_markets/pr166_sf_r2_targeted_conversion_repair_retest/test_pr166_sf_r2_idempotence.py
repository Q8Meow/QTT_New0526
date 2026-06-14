from __future__ import annotations

import subprocess
import sys

from .helpers import REPO_ROOT


def test_pr166_sf_r2_builder_verify_idempotent():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/build_pr166_sf_r2_targeted_conversion_repair_retest.py",
            "--verify-idempotent",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PR166_SF_R2_TARGETED_CONVERSION_REPAIR_RETEST_IDEMPOTENT" in completed.stdout
