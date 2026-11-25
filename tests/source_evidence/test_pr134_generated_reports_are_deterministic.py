import json
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir

from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor.validator import write_artifacts
from .pr134_runtime_resolver_snapshot_support import REPO_ROOT


def _snapshot(root):
    return {
        str(path.relative_to(root)).replace("\\", "/"): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(root.rglob("*.json"))
    }


def test_pr134_generated_reports_are_deterministic():
    fixture_parent = Path(gettempdir()).resolve(strict=True)
    assert not fixture_parent.is_relative_to(REPO_ROOT)
    with TemporaryDirectory(prefix="qtt-pr134-", dir=fixture_parent) as fixture_root:
        first = Path(fixture_root) / "first"
        second = Path(fixture_root) / "second"
        write_artifacts(repo_root=REPO_ROOT, output_root=first)
        write_artifacts(repo_root=REPO_ROOT, output_root=second)
        assert _snapshot(first) == _snapshot(second)
