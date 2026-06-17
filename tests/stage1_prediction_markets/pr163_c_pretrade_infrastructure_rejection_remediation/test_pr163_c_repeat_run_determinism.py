from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.qtt.stage1_prediction_markets.bounded_idempotence import (
    assert_bounded_idempotence_equal,
    bounded_snapshot,
)
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation import paths as p
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.report_builder import build_payloads_with_shards


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_BRANCH = "pr163-c-pretrade-infrastructure-rejection-remediation"
MAIN_BRANCH = "main"
BRANCH_CONTEXT_ENV = (
    "CI",
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
    "GITHUB_BASE_REF",
)


def _clear_branch_context_env(monkeypatch):
    for env_name in BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def _stub_git_branch(monkeypatch, branch: str) -> None:
    def fake_run(args, cwd, check, capture_output, text):
        assert args == ["git", "branch", "--show-current"]
        assert cwd == REPO_ROOT
        assert check is True
        assert capture_output is True
        assert text is True
        return SimpleNamespace(returncode=0, stdout=branch, stderr="")

    monkeypatch.setattr(p.subprocess, "run", fake_run)


def _set_github_pull_request_env(monkeypatch, head_ref: str) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1000/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "1000/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", head_ref)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")


def _github_main_push_env() -> dict[str, str]:
    return {
        "CI": "true",
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REF_NAME": "main",
    }


def _set_github_main_push_env(monkeypatch) -> None:
    for name, value in _github_main_push_env().items():
        monkeypatch.setenv(name, value)


REQUIRED_EXACT_REPORTS = (
    "PR163_C_FinalSummary.report.json",
    "PR163_C_ReportManifest.report.json",
    "PR163_C_NoLiveProfitSourceConnectorPrivateStateAudit.report.json",
    "PR163_C_NoQTTChecksumFreezeAuthorityAudit.report.json",
    "PR163_C_NoQuantumBackendAdvantageClaimAudit.report.json",
    "PR163_C_NoLLMRuntimeHotPathResultRewriteAudit.report.json",
    "PR163_C_OrphanArtifactAudit.report.json",
)
# The builder's --verify-idempotent CLI remains the manual exhaustive
# byte-for-byte rebuild path. PR/main CI uses this bounded deterministic
# contract over required root reports, manifest coverage, and sampled shards.


def _receipt(message: str) -> None:
    print(f"PR163_C_BOUNDED_IDEMPOTENCE {message}", flush=True)


def _bounded_snapshot(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return bounded_snapshot(
        payloads,
        shard_payloads,
        constants=p,
        required_exact_reports=REQUIRED_EXACT_REPORTS,
        manifest_report_filename="PR163_C_ReportManifest.report.json",
    )


def _branch_error(branch: str) -> str:
    return (
        f"PR163-C build must run on {EXPECTED_BRANCH} or {MAIN_BRANCH}; "
        f"current branch is {branch}"
    )


def test_pr163_c_repeat_run_determinism():
    _receipt("stage=rebuild_once")
    first_payloads, first_shards = build_payloads_with_shards(REPO_ROOT)
    first = _bounded_snapshot(first_payloads, first_shards)

    _receipt("stage=rebuild_twice")
    second_payloads, second_shards = build_payloads_with_shards(REPO_ROOT)
    second = _bounded_snapshot(second_payloads, second_shards)

    assert_bounded_idempotence_equal(first, second)
    _receipt("stage=complete")


def test_pr163_c_local_named_branch_passes_branch_context_check(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, EXPECTED_BRANCH)

    assert p.current_branch(REPO_ROOT) == EXPECTED_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_main_branch_passes_post_merge_branch_context_check(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, MAIN_BRANCH)

    assert p.current_branch(REPO_ROOT) == MAIN_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_ci_main_push_detached_head_passes_branch_context_check(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")
    _set_github_main_push_env(monkeypatch)

    assert p.current_branch(REPO_ROOT) == MAIN_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_ci_detached_head_uses_github_head_ref(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")
    _set_github_pull_request_env(monkeypatch, EXPECTED_BRANCH)

    assert p.current_branch(REPO_ROOT) == EXPECTED_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_wrong_local_branch_still_fails(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "feature/not-pr163-c")

    with pytest.raises(RuntimeError) as excinfo:
        p.ensure_branch(REPO_ROOT)

    assert _branch_error("feature/not-pr163-c") in str(excinfo.value)


def test_pr163_c_wrong_ci_head_branch_still_fails(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")
    _set_github_pull_request_env(monkeypatch, "feature/not-pr163-c")

    with pytest.raises(RuntimeError) as excinfo:
        p.ensure_branch(REPO_ROOT)

    assert _branch_error("feature/not-pr163-c") in str(excinfo.value)


def test_pr163_c_empty_branch_outside_ci_still_fails(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")

    with pytest.raises(RuntimeError) as excinfo:
        p.ensure_branch(REPO_ROOT)

    assert _branch_error("") in str(excinfo.value)
