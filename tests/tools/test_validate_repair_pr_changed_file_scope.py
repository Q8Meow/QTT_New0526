from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest

from tools import validate_repair_pr_changed_file_scope as validator


def _force_pr166_sm2_repair_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        validator.context,
        "current_branch_context",
        lambda repo_root: validator.context.BranchContext(
            branch=validator.context.PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_BRANCH,
            source="test",
        ),
    )


def _fake_status_git(lines: Sequence[str]):
    def fake_git(
        repo_root: Path,
        args: Sequence[str],
    ) -> tuple[int, str, str]:
        if tuple(args) == ("status", "--porcelain", "--untracked-files=all"):
            return 0, "\n".join(lines), ""
        raise AssertionError(f"unexpected fallback diff query: {tuple(args)!r}")

    return fake_git


def test_changed_files_from_git_prefers_worktree_status(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_git(
        repo_root: Path,
        args: Sequence[str],
    ) -> tuple[int, str, str]:
        calls.append(tuple(args))
        if tuple(args) == ("status", "--porcelain", "--untracked-files=all"):
            return (
                0,
                "\n".join(
                    (
                        " M tools/ci_branch_context.py",
                        "M tests\\tools\\test_validate_repair_pr_changed_file_scope.py",
                        "?? src/qtt/stage1_prediction_markets/bounded_idempotence.py",
                        "R  old_name.py -> tests/tools/test_ci_branch_context.py",
                    )
                ),
                "",
            )
        raise AssertionError(f"unexpected fallback diff query: {tuple(args)!r}")

    monkeypatch.setattr(validator, "_git", fake_git)

    assert validator._changed_files_from_git(Path(".")) == (
        "src/qtt/stage1_prediction_markets/bounded_idempotence.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
        "tools/ci_branch_context.py",
    )
    assert calls == [("status", "--porcelain", "--untracked-files=all")]


def test_changed_files_from_git_falls_back_to_committed_diff(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_git(
        repo_root: Path,
        args: Sequence[str],
    ) -> tuple[int, str, str]:
        calls.append(tuple(args))
        if tuple(args) == ("status", "--porcelain", "--untracked-files=all"):
            return 0, "", ""
        if tuple(args) == ("diff", "--name-only", "HEAD^1", "HEAD"):
            return 0, "tools\\ci_branch_context.py\n", ""
        raise AssertionError(f"unexpected diff query: {tuple(args)!r}")

    monkeypatch.setattr(validator, "_git", fake_git)

    assert validator._changed_files_from_git(Path(".")) == (
        "tools/ci_branch_context.py",
    )
    assert calls == [
        ("status", "--porcelain", "--untracked-files=all"),
        ("diff", "--name-only", "HEAD^1", "HEAD"),
    ]


def test_untracked_validation_router_runtime_artifact_is_ignored(monkeypatch):
    _force_pr166_sm2_repair_branch(monkeypatch)
    monkeypatch.setattr(
        validator,
        "_git",
        _fake_status_git(("?? .tmp\\qtt-validation-router\\fast-preflight.json",)),
    )

    assert validator.validate(Path(".")) == ()


def test_untracked_validation_timing_runtime_artifact_is_ignored(monkeypatch):
    _force_pr166_sm2_repair_branch(monkeypatch)
    monkeypatch.setattr(
        validator,
        "_git",
        _fake_status_git(("?? .tmp\\qtt-validation-timing\\fast-preflight.json",)),
    )

    assert validator.validate(Path(".")) == ()


@pytest.mark.parametrize(
    "path",
    (
        "src/qtt/stage1_prediction_markets/out_of_scope.py",
        "tests/out_of_scope/test_real_file.py",
        "docs/out_of_scope.md",
    ),
)
def test_real_untracked_repo_file_outside_repair_scope_fails(monkeypatch, path):
    _force_pr166_sm2_repair_branch(monkeypatch)
    monkeypatch.setattr(validator, "_git", _fake_status_git((f"?? {path}",)))

    failures = validator.validate(Path("."))

    assert failures == (f"repair branch changed path outside explicit scope: {path}",)


def test_allowed_pr152_currentization_output_still_passes(monkeypatch):
    _force_pr166_sm2_repair_branch(monkeypatch)
    monkeypatch.setattr(
        validator,
        "_git",
        _fake_status_git(
            (
                " M docs\\master_plan\\generated\\"
                "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            )
        ),
    )

    assert validator.validate(Path(".")) == ()


def test_st12_architecture_oracle_prerequisite_repair_scope_is_exact(monkeypatch):
    branch = (
        validator.context.ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH
    )
    allowed = frozenset(
        {
            "tools/independent_validate_qku_computation_control_plane_architecture.py",
            "tools/ci_branch_context.py",
            "tests/tools/test_ci_branch_context.py",
            "tests/tools/test_validate_repair_pr_changed_file_scope.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        }
    )
    assert (
        validator.context.ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_CHANGED_PATHS
        == allowed
    )
    assert all(
        validator.context.changed_path_allowed_for_explicit_repair_branch(
            branch,
            path,
        )
        for path in allowed
    )

    rejected = (
        "src/qtt/stage1_prediction_markets/runtime.py",
        "docs/master_plan/generated/UnrelatedArchitectureOracle.report.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/roadmap/QTT_Roadmap_v10.md",
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_h/test_contract_matrix.py",
        ".github/workflows/qtt_validation.yml",
        "tools/pr168_rp5c_config.py",
        "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
    )
    assert all(
        not validator.context.changed_path_allowed_for_explicit_repair_branch(
            branch,
            path,
        )
        for path in rejected
    )

    monkeypatch.setattr(
        validator.context,
        "current_branch_context",
        lambda repo_root: validator.context.BranchContext(
            branch=branch,
            source="test",
        ),
    )
    monkeypatch.setattr(
        validator,
        "_git",
        _fake_status_git(
            (
                *(f" M {path}" for path in sorted(allowed)),
                "?? .tmp/qtt-validation-router/st12-architecture-oracle.json",
                "?? .pytest_cache/st12-architecture-oracle/cache",
            )
        ),
    )
    assert validator.validate(Path(".")) == ()


def test_exact_mapped_repair_scopes_precede_generic_pr152_allowances():
    context = validator.context
    generic_pr152_paths = context.PR152_CURRENTIZATION_AFTER_FASTFAIL_MERGE_CHANGED_PATHS

    for branch, exact_scope in sorted(
        context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS.items()
    ):
        if not context.is_repair_branch(branch):
            continue
        for path in generic_pr152_paths:
            assert context.is_explicit_downstream_repair_changed_path(
                branch,
                path,
            ) is (path in exact_scope)

    non_repair_owner_branch = "agent/st12a-contract-envelope"
    assert context.is_owner_authorized_validation_branch(non_repair_owner_branch)
    assert not context.is_repair_branch(non_repair_owner_branch)
    assert all(
        context.is_explicit_downstream_repair_changed_path(
            non_repair_owner_branch,
            path,
        )
        for path in generic_pr152_paths
    )


def test_repair_branch_exact_changed_path_scope_still_fails_closed(monkeypatch):
    _force_pr166_sm2_repair_branch(monkeypatch)
    monkeypatch.setattr(
        validator,
        "_git",
        _fake_status_git(
            (
                " M tools/validate_repair_pr_changed_file_scope.py",
                "?? tools/run_validation_gates.py",
            )
        ),
    )

    assert validator.validate(Path(".")) == (
        "repair branch changed path outside explicit scope: tools/run_validation_gates.py",
    )


def test_staged_runtime_artifact_reports_git_hygiene_failure(monkeypatch):
    _force_pr166_sm2_repair_branch(monkeypatch)
    monkeypatch.setattr(
        validator,
        "_git",
        _fake_status_git(("A  .tmp/qtt-validation-router/fast-preflight.json",)),
    )

    assert validator.validate(Path(".")) == (
        "git hygiene failure: transient runtime artifact is tracked or staged: "
        ".tmp/qtt-validation-router/fast-preflight.json",
    )
