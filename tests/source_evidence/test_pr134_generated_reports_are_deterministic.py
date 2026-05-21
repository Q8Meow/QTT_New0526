import json

from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor.validator import write_artifacts
from .pr134_runtime_resolver_snapshot_support import REPO_ROOT


def _snapshot(root):
    return {
        str(path.relative_to(root)).replace("\\", "/"): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(root.rglob("*.json"))
    }


def test_pr134_generated_reports_are_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_artifacts(repo_root=REPO_ROOT, output_root=first)
    write_artifacts(repo_root=REPO_ROOT, output_root=second)
    assert _snapshot(first) == _snapshot(second)
