import json
from pathlib import Path

from tools.validate_first_pr_scope import validate_first_pr_scope


def _write_scope_report(path: Path, blocks: list[str]) -> Path:
    path.write_text(
        json.dumps({"first_pr_scope": "schema_only_scaffold", "blocks": blocks}) + "\n",
        encoding="utf-8",
    )
    return path


def test_first_pr_scope_gate_accepts_requested_blocks(tmp_path):
    scope_report = _write_scope_report(
        tmp_path / "FirstPrScopeReport.json",
        ["runtime", "live", "sha"],
    )

    failures = validate_first_pr_scope(
        repo_root=tmp_path,
        scope_report_path=scope_report,
        requested_blocks={"runtime", "live"},
    )

    assert failures == []


def test_first_pr_scope_gate_rejects_missing_requested_block(tmp_path):
    scope_report = _write_scope_report(
        tmp_path / "FirstPrScopeReport.json",
        ["runtime", "live"],
    )

    failures = validate_first_pr_scope(
        repo_root=tmp_path,
        scope_report_path=scope_report,
        requested_blocks={"runtime", "order_execution"},
    )

    assert any("order_execution" in failure for failure in failures)
