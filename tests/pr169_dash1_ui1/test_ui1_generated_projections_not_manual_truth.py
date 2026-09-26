from tests.pr169_dash1_ui1.conftest import UI, UI_ARTIFACT_FILES, ui_doc


import pytest


@pytest.fixture(scope="module", autouse=True)
def ui1_artifacts():
    """Override only this module's inherited fixture; keep its real body."""
    import inspect
    import stat
    from pathlib import Path
    from tests.pr169_dash1_ui1 import conftest as support
    from tools import validation_reliability as reliability

    source_base = support.BASE
    source_ui = support.UI
    imported_ui = UI
    repository = Path(__file__).resolve().parents[2]
    reliability._local_unlinked_path(repository / source_base)
    origin = (repository / source_base).resolve(strict=True)
    entries = []
    pending = [origin]
    while pending:
        directory = pending.pop()
        reliability._local_unlinked_path(directory)
        for source in sorted(directory.iterdir()):
            reliability._local_unlinked_path(source.parent)
            observed = source.lstat()
            if reliability._stat_is_reparse_point(observed):
                raise ValueError("UI1 copy source is a reparse point")
            if stat.S_ISDIR(observed.st_mode):
                pending.append(source)
            elif not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
                raise ValueError("UI1 copy source is not an ordinary single-link file")
            entries.append(source)
    entries = tuple(sorted(entries))
    paths = tuple(path.relative_to(origin) for path in entries)
    owned, probe = reliability.resolve_validation_run_paths(
        repository,
        explicit_process_root=repository / ".qtt" / "runs",
        projected_relative_paths=tuple(
            "validation-output/" + str(path) for path in paths
        ) + tuple("validation-output/ui/" + name for name in UI_ARTIFACT_FILES),
    )
    fixture_error = None
    try:
        target = owned.validation_output_root
        assert owned.process_root_is_external_to_repo is False
        assert probe.failure_operation is None
        assert not any(target.iterdir())
        for source, relative in zip(entries, paths):
            reliability._local_unlinked_path(source.parent)
            observed = source.lstat()
            destination = target / relative
            if stat.S_ISDIR(observed.st_mode):
                destination.mkdir(parents=True, exist_ok=True)
                continue
            if (not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1
                    or reliability._stat_is_reparse_point(observed)):
                raise ValueError("UI1 copy source is not an ordinary single-link file")
            destination.parent.mkdir(parents=True, exist_ok=True)
            copied = 0
            with reliability._regular_worktree_source(source, observed).open() as reader:
                with destination.open("xb") as writer:
                    while block := reader.read(1048576):
                        if writer.write(block) != len(block):
                            raise OSError("UI1 input copy was incomplete")
                        copied += len(block)
            if copied != observed.st_size:
                raise ValueError("UI1 copy length changed")
            with reliability._regular_worktree_source(source, observed).open() as reader:
                with destination.open("rb") as copied_reader:
                    while True:
                        block = reader.read(1048576)
                        if copied_reader.read(1048576) != block:
                            raise ValueError("UI1 input copy differs from its original bytes")
                        if not block:
                            break
        assert tuple(sorted(path.relative_to(target) for path in target.rglob("*"))) == paths
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(support, "BASE", target)
            patch.setattr(support, "UI", target / "ui")
            patch.setitem(globals(), "UI", target / "ui")
            # This is the original three-statement fixture body, including its
            # real build_ui call and complete validate(BASE) == () assertion.
            original_fixture_body = inspect.unwrap(support.ui1_artifacts)
            assert original_fixture_body() == target
            yield target
        assert support.BASE is source_base and support.UI is source_ui
        assert UI is imported_ui
    except BaseException as error:
        fixture_error = error
        raise
    finally:
        try:
            cleanup_state = reliability.cleanup_validation_run(owned)
        except BaseException as cleanup_error:
            if fixture_error is not None:
                raise BaseExceptionGroup(
                    "UI1 isolated fixture and owned cleanup both failed",
                    [fixture_error, cleanup_error],
                ) from None
            raise
    assert cleanup_state == "PASS_REMOVED_EXACT_RUN_ROOT"
    assert not owned.process_root.exists()


def test_ui1_generated_projections_not_manual_truth(tmp_path, monkeypatch) -> None:
    for name in UI_ARTIFACT_FILES:
        assert (UI / name).exists(), name
        meta = ui_doc(name)["meta"]
        assert meta["generated_from"].startswith("owner_dashboard_surface_registry.jsonl")
        assert meta["manual_edit_allowed"] is False
        assert meta["runtime_truth_authority"] is False
        assert meta["agent_consumable_authority"] is False

    # Exercise both shared writers inside the original collected test.
    import json
    from pathlib import Path
    import pytest
    from tools import build_pr169_dash1_owner_dashboard_ui as builder

    original_open = Path.open
    for writer, payload, expected in (
        (builder._write_json, {"synthetic": 1},
         (json.dumps({"synthetic": 1}, indent=2, sort_keys=True) + "\n").encode("utf-8")),
        (builder._write_text, "A\nB\n", b"A\nB\n"),
    ):
        operand = tmp_path / (writer.__name__ + ".txt")
        for newline in (b"\r\n", b"\r"):
            operand.write_bytes(expected.replace(b"\n", newline))
            writer(operand, payload)
            assert operand.read_bytes() == expected

        # Exact current bytes must not be reopened for truncating writes.
        operand.write_bytes(expected)
        def observe_open(path, mode="r", *args, **kwargs):
            if path == operand and any(flag in mode for flag in "wax+"):
                raise AssertionError("unchanged canonical output was reopened for writing")
            return original_open(path, mode, *args, **kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(Path, "open", observe_open)
            writer(operand, payload)
        assert operand.read_bytes() == expected

        # Retain the original strict UTF-8 error, without changing failed input.
        operand.write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            writer(operand, payload)
        assert operand.read_bytes() == b"\xff"
