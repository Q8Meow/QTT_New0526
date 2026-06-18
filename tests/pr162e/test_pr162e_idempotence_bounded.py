from __future__ import annotations

import hashlib
import subprocess
import sys

from tests.pr162e.helpers import REPO_ROOT


def bounded_snapshot() -> str:
    paths = sorted((REPO_ROOT / "docs/master_plan/generated").glob("PR162E_*.report.json"))
    hasher = hashlib.sha256()
    for path in paths:
        hasher.update(path.as_posix().encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def assert_bounded_idempotence_equal(before: str, after: str) -> None:
    assert after == before


def test_builder_is_bounded_idempotent_for_pr162e_reports():
    before = bounded_snapshot()
    subprocess.run(
        [sys.executable, "tools/build_pr162e_plugin_framework.py", "--repo-root", "."],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    after = bounded_snapshot()
    assert_bounded_idempotence_equal(before, after)
