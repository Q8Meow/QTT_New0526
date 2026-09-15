from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from tools import currentize_pr152_after_generated_artifacts as helper


def _prepared_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs/master_plan/atomic_rows").mkdir(parents=True)
    (root / "docs/master_plan/generated").mkdir(parents=True)
    (root / "docs/master_plan/QTT_MasterPlan_Current.md").write_text(
        "master plan\n",
        encoding="utf-8",
    )
    (root / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").write_text(
        "{}\n",
        encoding="utf-8",
    )
    return root


def _report(
    *,
    generated_report_count: int = 1011,
    test_file_count: int = 818,
    validator_tool_count: int = 127,
) -> dict[str, object]:
    return {
        "generated_report_consistency_audit": {
            "generated_report_count": generated_report_count
        },
        "schema_fixture_test_consistency_audit": {
            "test_file_count": test_file_count
        },
        "validator_tool_registry_audit": {
            "validator_tool_count": validator_tool_count
        },
    }


def _unchanged_paths(_root: Path) -> list[str]:
    return []


def _no_untracked_paths(_root: Path) -> list[str]:
    return []


def test_helper_detects_stale_pr152_after_write(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)

    with pytest.raises(helper.CurrentizationError) as exc_info:
        helper.currentize_pr152_after_generated_artifacts(
            root,
            write_report=lambda _root: _report(),
            validate_artifacts=lambda _root, **_kwargs: [
                "PR152_REPORT_STALE_OR_NONDETERMINISTIC"
            ],
            changed_paths=_unchanged_paths,
        )

    assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in exc_info.value.failures


def test_helper_fails_closed_if_untracked_pr_artifacts_exist(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    calls: list[Path] = []

    with pytest.raises(helper.CurrentizationError) as exc_info:
        helper.currentize_pr152_after_generated_artifacts(
            root,
            write_report=lambda report_root: calls.append(report_root) or _report(),
            validate_artifacts=lambda _root, **_kwargs: [],
            changed_paths=_unchanged_paths,
            untracked_paths=lambda _root: [
                "docs/master_plan/generated/PR999_NewReport.report.json",
                (
                    "docs/master_plan/generated/pr999_new_report_shards/"
                    "PR999_NewReport.report.shard_0001.json"
                ),
                "src/qtt/stage1_prediction_markets/new_pr_package/__init__.py",
                "tests/stage1_prediction_markets/new_pr_package/test_new_pr.py",
                "tools/build_pr999_new_report.py",
                "tools/validate_pr999_new_report.py",
            ],
        )

    assert calls == []
    assert any(
        failure.startswith(
            "PR152_CURRENTIZATION_BLOCKED_UNTRACKED_PR_ARTIFACTS"
        )
        for failure in exc_info.value.failures
    )
    assert (
        "PR152_CURRENTIZATION_UNTRACKED_PR_ARTIFACT_PATH: "
        "docs/master_plan/generated/PR999_NewReport.report.json"
    ) in exc_info.value.failures
    assert (
        "PR152_CURRENTIZATION_UNTRACKED_PR_ARTIFACT_PATH: "
        "tools/validate_pr999_new_report.py"
    ) in exc_info.value.failures


def test_helper_allows_intentionally_included_pr_artifacts(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)

    result = helper.currentize_pr152_after_generated_artifacts(
        root,
        write_report=lambda _root: _report(
            generated_report_count=14,
            test_file_count=5,
            validator_tool_count=6,
        ),
        validate_artifacts=lambda _root, **_kwargs: [],
        changed_paths=lambda _root: [
            "docs/master_plan/generated/PR999_NewReport.report.json",
            "src/qtt/stage1_prediction_markets/new_pr_package/__init__.py",
            "tests/stage1_prediction_markets/new_pr_package/test_new_pr.py",
            "tools/build_pr999_new_report.py",
            "tools/validate_pr999_new_report.py",
        ],
        untracked_paths=_no_untracked_paths,
    )

    assert result.generated_report_count == 14
    assert result.test_file_count == 5
    assert result.validator_tool_count == 6


def test_helper_currentizes_through_established_write_path(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    calls: list[Path] = []

    def fake_write(report_root: Path) -> dict[str, object]:
        calls.append(report_root)
        return _report(generated_report_count=12, test_file_count=3, validator_tool_count=4)

    def fake_validate(report_root: Path, **kwargs: object) -> list[str]:
        assert report_root == root.resolve()
        assert kwargs["tracked_report_write_allowed"] is True
        return []

    result = helper.currentize_pr152_after_generated_artifacts(
        root,
        write_report=fake_write,
        validate_artifacts=fake_validate,
        changed_paths=_unchanged_paths,
    )

    assert calls == [root.resolve()]
    assert result.generated_report_count == 12
    assert result.test_file_count == 3
    assert result.validator_tool_count == 4


def test_helper_fails_closed_if_protected_file_changes(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)

    def mutating_write(report_root: Path) -> dict[str, object]:
        (report_root / "docs/master_plan/QTT_MasterPlan_Current.md").write_text(
            "mutated\n",
            encoding="utf-8",
        )
        return _report()

    with pytest.raises(helper.CurrentizationError) as exc_info:
        helper.currentize_pr152_after_generated_artifacts(
            root,
            write_report=mutating_write,
            validate_artifacts=lambda _root, **_kwargs: [],
            changed_paths=_unchanged_paths,
        )

    assert any(
        failure.startswith("PR152_CURRENTIZATION_PROTECTED_FILE_CHANGED")
        for failure in exc_info.value.failures
    )


def test_helper_does_not_mutate_master_plan(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    master_plan = root / "docs/master_plan/QTT_MasterPlan_Current.md"
    before = master_plan.read_bytes()

    helper.currentize_pr152_after_generated_artifacts(
        root,
        write_report=lambda _root: _report(),
        validate_artifacts=lambda _root, **_kwargs: [],
        changed_paths=_unchanged_paths,
    )

    assert master_plan.read_bytes() == before


def test_helper_does_not_mutate_atomicrows_bundle_jsonl(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    bundle = root / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
    before = bundle.read_bytes()

    helper.currentize_pr152_after_generated_artifacts(
        root,
        write_report=lambda _root: _report(),
        validate_artifacts=lambda _root, **_kwargs: [],
        changed_paths=_unchanged_paths,
    )

    assert bundle.read_bytes() == before


def test_helper_fails_if_atomicrows_bundle_sidecar_appears(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    sidecar = (
        root
        / Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").with_suffix(
            "." + "sha" + "256"
        )
    )

    def sidecar_write(_root: Path) -> dict[str, object]:
        sidecar.write_text("forbidden\n", encoding="utf-8")
        return _report()

    with pytest.raises(helper.CurrentizationError) as exc_info:
        helper.currentize_pr152_after_generated_artifacts(
            root,
            write_report=sidecar_write,
            validate_artifacts=lambda _root, **_kwargs: [],
            changed_paths=_unchanged_paths,
        )

    assert any(
        failure.startswith("PR152_CURRENTIZATION_FORBIDDEN_SIDECAR_APPEARED")
        for failure in exc_info.value.failures
    )


def test_helper_does_not_create_atomicrows_bundle_sidecar(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    sidecar = (
        root
        / Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").with_suffix(
            "." + "sha" + "256"
        )
    )

    helper.currentize_pr152_after_generated_artifacts(
        root,
        write_report=lambda _root: _report(),
        validate_artifacts=lambda _root, **_kwargs: [],
        changed_paths=_unchanged_paths,
    )

    assert not sidecar.exists()


def test_helper_fails_if_qtt_integrity_authority_text_appears(tmp_path: Path) -> None:
    root = _prepared_repo(tmp_path)
    note = root / "new_authority_note.txt"
    forbidden = "".join(
        (
            "QTT ",
            "SH",
            "A/",
            "freeze/",
            "check",
            "sum/",
            "global ",
            "di",
            "gest ",
            "authority",
        )
    )
    note.write_text(forbidden, encoding="utf-8")

    with pytest.raises(helper.CurrentizationError) as exc_info:
        helper.currentize_pr152_after_generated_artifacts(
            root,
            write_report=lambda _root: _report(),
            validate_artifacts=lambda _root, **_kwargs: [],
            changed_paths=lambda _root: ["new_authority_note.txt"],
        )

    assert "PR152_CURRENTIZATION_FORBIDDEN_QTT_AUTHORITY_TEXT: new_authority_note.txt" in (
        exc_info.value.failures
    )


def test_helper_fails_if_qtt_integrity_authority_text_is_created(
    tmp_path: Path,
) -> None:
    root = _prepared_repo(tmp_path)
    note = root / "new_authority_note.txt"
    forbidden = "".join(
        (
            "QTT ",
            "SH",
            "A/",
            "freeze/",
            "check",
            "sum/",
            "global ",
            "di",
            "gest ",
            "authority",
        )
    )
    calls = 0

    def changed_paths(_root: Path) -> list[str]:
        nonlocal calls
        calls += 1
        return [] if calls == 1 else ["new_authority_note.txt"]

    def mutating_write(_root: Path) -> dict[str, object]:
        note.write_text(forbidden, encoding="utf-8")
        return _report()

    with pytest.raises(helper.CurrentizationError) as exc_info:
        helper.currentize_pr152_after_generated_artifacts(
            root,
            write_report=mutating_write,
            validate_artifacts=lambda _root, **_kwargs: [],
            changed_paths=changed_paths,
        )

    assert "PR152_CURRENTIZATION_FORBIDDEN_QTT_AUTHORITY_TEXT: new_authority_note.txt" in (
        exc_info.value.failures
    )


def test_helper_cli_fails_closed_without_git_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parent = (tmp_path / "p").resolve()
    root = _prepared_repo(parent)
    hooks = tmp_path / "h"
    hooks.mkdir()
    fixture_environment = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    fixture_environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": "",
        "GIT_OPTIONAL_LOCKS": "0",
    })

    def git(directory: Path, *arguments: str) -> bytes:
        completed = subprocess.run(
            ["git", "-c", "user.name=QTT test fixture",
             "-c", "user.email=qtt-fixture@example.invalid",
             "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false",
             "-c", "core.hooksPath=" + str(hooks),
             "-c", "core.fsmonitor=false", "-c", "protocol.allow=never",
             *arguments],
            cwd=directory, env=fixture_environment, stdin=subprocess.DEVNULL,
            capture_output=True, timeout=60,
        )
        assert completed.returncode == 0, completed.stderr.decode("utf-8")
        return completed.stdout

    (parent / ".gitignore").write_bytes(b"/repo/\n/n/\n/b/\n/w/\n")
    (parent / "parent.txt").write_bytes(b"parent baseline\n")
    git(parent, "init", "--initial-branch=main")
    git(parent, "add", "--", ".gitignore", "parent.txt")
    git(parent, "commit", "-m", "PR152 parent fixture")
    parent_head = git(parent, "rev-parse", "HEAD")
    parent_index = git(parent, "ls-files", "--stage", "-z")
    assert git(parent, "status", "--porcelain=v1", "-z") == b""
    protected = {path: path.read_bytes() for path in (
        root / "docs/master_plan/QTT_MasterPlan_Current.md",
        root / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    )}
    writes: list[Path] = []
    monkeypatch.setattr(helper, "write_report_file", lambda path: writes.append(path) or _report())
    monkeypatch.setattr(helper, "validate_repository_artifacts", lambda _root, **_kwargs: [])

    assert helper.main(["--repo-root", str(root)]) == 1

    output = capsys.readouterr().out
    assert helper.FAILURE_MARKER in output
    assert "PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE" in output
    assert writes == []

    nested = _prepared_repo(parent / "n")
    (nested / "tracked.txt").write_bytes(b"before\n")
    git(nested, "init", "--initial-branch=main")
    git(nested, "add", "--", "tracked.txt",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
    git(nested, "commit", "-m", "PR152 nested fixture")
    nested_protected = {path: path.read_bytes() for path in (
        nested / "docs/master_plan/QTT_MasterPlan_Current.md",
        nested / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    )}
    nested_head = git(nested, "rev-parse", "HEAD")
    assert helper._git_status_changed_paths(nested) == []
    assert helper._git_untracked_paths(nested) == []
    assert helper._added_diff_text_for_path(nested, "tracked.txt") is None
    (nested / "tracked.txt").write_bytes(b"after\n")
    (nested / "new.txt").write_bytes(b"untracked\n")
    (nested / "staged.txt").write_bytes(b"staged\n")
    git(nested, "add", "--", "staged.txt")
    nested_index = git(nested, "ls-files", "--stage", "-z")
    ordinary_child = nested / "child"
    ordinary_child.mkdir()
    bare = parent / "b"
    bare.mkdir()
    git(bare, "init", "--bare", "--initial-branch=main")
    linked = parent / "w"
    git(nested, "worktree", "add", "--detach", str(linked), "HEAD")
    assert (linked / ".git").is_file()

    redirects = {
        "GIT_DIR": str(parent / ".git"), "GIT_WORK_TREE": str(parent),
        "GIT_INDEX_FILE": str(parent / ".git/index"),
        "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.worktree",
        "GIT_CONFIG_VALUE_0": str(parent), "GIT_CONFIG_KEY_1": "core.bare",
        "GIT_CONFIG_VALUE_1": "true", "GIT_CONFIG_PARAMETERS": "'core.bare=true'",
    }
    original_environment = dict(os.environ)
    for inherited in ({}, redirects):
        with pytest.MonkeyPatch.context() as patch:
            for key, value in inherited.items():
                patch.setenv(key, value)
            before_reads = dict(os.environ)
            for rejected in (root, ordinary_child, bare):
                for reader in (helper._git_status_changed_paths, helper._git_untracked_paths):
                    with pytest.raises(
                        helper.CurrentizationError,
                        match="PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE",
                    ):
                        reader(rejected)
            assert helper.main(["--repo-root", str(root)]) == 1
            assert writes == []
            assert helper._git_status_changed_paths(nested) == ["new.txt", "staged.txt", "tracked.txt"]
            assert helper._git_untracked_paths(nested) == ["new.txt"]
            assert helper._added_diff_text_for_path(nested, "tracked.txt") == "after"
            assert helper._git_status_changed_paths(linked) == []
            assert helper._git_untracked_paths(linked) == []
            assert helper._added_diff_text_for_path(linked, "tracked.txt") is None
            assert dict(os.environ) == before_reads
        assert dict(os.environ) == original_environment
    for invalid in (
        parent / "missing", nested / "tracked.txt",
        *(Path(str(root) + character) for character in ("\r", "\n", "\0")),
    ):
        with pytest.raises(helper.CurrentizationError, match="PR152_CURRENTIZATION_GIT_STATUS_UNAVAILABLE"):
            helper._run_repository_git(invalid, ["status", "--porcelain=v1"])
    assert git(parent, "rev-parse", "HEAD") == parent_head
    assert git(parent, "ls-files", "--stage", "-z") == parent_index
    assert git(parent, "status", "--porcelain=v1", "-z") == b""
    assert git(nested, "rev-parse", "HEAD") == nested_head
    assert git(nested, "ls-files", "--stage", "-z") == nested_index
    assert all(path.read_bytes() == expected for path, expected in protected.items())
    assert (parent / "parent.txt").read_bytes() == b"parent baseline\n"
    assert all(path.read_bytes() == expected for path, expected in nested_protected.items())


def test_helper_cli_can_be_called_by_future_pr_finalization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _prepared_repo(tmp_path)
    monkeypatch.setattr(helper, "write_report_file", lambda _root: _report())
    monkeypatch.setattr(helper, "validate_repository_artifacts", lambda _root, **_kwargs: [])
    monkeypatch.setattr(helper, "_git_status_changed_paths", _unchanged_paths)

    assert helper.main(["--repo-root", str(root)]) == 0

    output = capsys.readouterr().out
    assert helper.SUCCESS_MARKER in output
    assert "generated_report_count=1011" in output
    assert "test_file_count=818" in output
    assert "validator_tool_count=127" in output
