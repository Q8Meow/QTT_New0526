from __future__ import annotations

import json
from pathlib import Path

from tools.pr168_rp5a_config import REPORT_NAMES, ROW_SHARDS, report_path, shard_path
from tools.pr168_rp5a_validator import run_validation


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_report(name: str) -> dict:
    return json.loads(report_path(name).read_text(encoding="utf-8"))


def load_rows(key: str) -> list[dict]:
    path = shard_path(key)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _original_rp5a_read_context():
    # The selected pytest integration must bind this original session. Test
    # invocation and ambient environment never manufacture accepted capacity.
    from tools.build_pr168_rp5a_legacy_semantic_audit import _require_builder_reads_v1
    return _require_builder_reads_v1()


def assert_rp5a_valid(*, builder_read_context=None) -> None:
    original = _original_rp5a_read_context() if builder_read_context is None else builder_read_context
    assert run_validation(builder_read_context=original)["validation"] == "PR168_RP5A_LEGACY_SEMANTIC_AUDIT_OK"


def file_rows() -> list[dict]:
    return load_rows("legacy_file_semantic_rows")


def delete_rows() -> list[dict]:
    return load_rows("delete_eligibility_rows")
