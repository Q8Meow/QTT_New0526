from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import pytest

from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import io as pr165_d2_io
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.report_writer import build_payloads_with_shards

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_EXACT_REPORTS = (
    "PR165_D2_FinalSummary.report.json",
    "PR165_D2_ReportManifest.report.json",
    "PR165_D2_RowCountReconciliationLedger.report.json",
    "PR165_D2_AuthorityBoundaryAudit.report.json",
    "PR165_D2_OrphanArtifactAudit.report.json",
    "PR165_D2_StatusEnumDriftAudit.report.json",
)
# The builder's --verify-idempotent CLI remains the manual exhaustive
# byte-for-byte rebuild mode. This PR-CI test is the bounded deterministic
# contract over count-bearing reports, manifest coverage, and sampled shards.


class _BranchResult:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def _clear_branch_env(monkeypatch):
    for env_name in ("GITHUB_ACTIONS", "GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        monkeypatch.delenv(env_name, raising=False)


def _stub_git_branch(monkeypatch, stdout: str) -> None:
    monkeypatch.setattr(
        pr165_d2_io.subprocess,
        "run",
        lambda *args, **kwargs: _BranchResult(stdout),
    )


def _receipt(message: str) -> None:
    print(f"PR165_D2_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=c,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR165_D2_ReportManifest.report.json",
    )


def test_pr165_d2_bounded_idempotence_contract_is_deterministic():
    started = time.perf_counter()
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(REPO_ROOT)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(REPO_ROOT)
    second = _bounded_snapshot(second_payloads, second_shards)
    assert_bounded_idempotence_equal(first, second)

    elapsed = time.perf_counter() - started
    _receipt(f"stage=complete elapsed_seconds={elapsed:.3f}")


def test_builder_verify_idempotent_post_merge_branch_context(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", c.BASE_BRANCH)
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.BASE_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_local_expected_branch(monkeypatch):
    _clear_branch_env(monkeypatch)
    _stub_git_branch(monkeypatch, c.EXPECTED_BRANCH)

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.EXPECTED_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_local_main_post_merge_context(monkeypatch):
    _clear_branch_env(monkeypatch)
    _stub_git_branch(monkeypatch, c.BASE_BRANCH)

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.BASE_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_local_wrong_branch(monkeypatch):
    _clear_branch_env(monkeypatch)
    _stub_git_branch(monkeypatch, "feature/not-pr165-d2")

    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_local_empty_branch_without_github_actions(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == ""
    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_ci_detached_head_ref(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)
    monkeypatch.setenv("GITHUB_REF_NAME", "refs-pull-fallback-not-used")
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.EXPECTED_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_ci_detached_main_ref_name(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", c.BASE_BRANCH)
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.BASE_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_wrong_ci_detached_branch_context(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/not-pr165-d2")
    monkeypatch.setenv("GITHUB_REF_NAME", "release/not-pr165-d2")
    _stub_git_branch(monkeypatch, "")

    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)
