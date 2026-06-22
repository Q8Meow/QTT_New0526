from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_offline_builder_and_validator_do_not_require_network() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    subprocess.run(
        [sys.executable, "tools/build_pr168_map3.py", "--offline"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, "tools/validate_pr168_map3.py"],
        cwd=repo_root,
        check=True,
    )
