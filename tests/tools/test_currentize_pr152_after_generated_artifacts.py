from __future__ import annotations

from pathlib import Path

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
