from __future__ import annotations

import pytest

from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import constants as c
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import io as pr167_io
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration.io import (
    read_json,
    resolve_repo_relative,
)
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration.report_writer import (
    write_artifacts,
)

from .helpers import REPO_ROOT


def test_pr167_builder_is_bounded_idempotent(monkeypatch):
    monkeypatch.setattr(
        pr167_io,
        "_current_branch",
        lambda _repo_root: "pr168-gfp-global-formula-discovery-real-computation",
    )
    monkeypatch.setattr(
        pr167_io,
        "_ci_branch_context",
        lambda _repo_root: "pr168-gfp-global-formula-discovery-real-computation",
    )
    with pytest.raises(RuntimeError, match="pr168-gfp-global-formula-discovery-real-computation"):
        pr167_io.ensure_branch(REPO_ROOT)

    monkeypatch.setattr(pr167_io, "_current_branch", lambda _repo_root: c.BASE_BRANCH)
    monkeypatch.setattr(pr167_io, "_ci_branch_context", lambda _repo_root: c.BASE_BRANCH)
    first = bounded_snapshot()
    write_artifacts(REPO_ROOT)
    second = bounded_snapshot()
    assert_bounded_idempotence_equal(first, second)


def assert_bounded_idempotence_equal(left, right):
    assert left == right


def bounded_snapshot() -> dict[str, bytes]:
    paths = []
    for filename in c.REPORT_FILENAMES:
        root = REPO_ROOT / c.GENERATED_DIR / filename
        paths.append(root)
        payload = read_json(root)
        for shard in payload.get("shard_files") or []:
            paths.append(resolve_repo_relative(REPO_ROOT, shard))
    for schema in sorted((REPO_ROOT / c.SCHEMA_DIR).glob("*.schema.json")):
        paths.append(schema)
    return {path.relative_to(REPO_ROOT).as_posix(): path.read_bytes() for path in sorted(paths)}
