from __future__ import annotations

from copy import deepcopy
import io
import inspect
import os
from pathlib import Path
import subprocess
import tempfile

import pytest

from tools import ci_branch_context as context
from tools import validate_idempotence_runtime_containment as validator
from tools import validation_reliability as reliability


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "idempotence_runtime_containment_inventory.json"
)
WORKFLOW_TEXT = (
    REPO_ROOT / ".github" / "workflows" / "qtt_validation.yml"
).read_text(encoding="utf-8")


def _inventory() -> dict[str, object]:
    return deepcopy(validator.load_inventory(INVENTORY_PATH))


def _codes(failures) -> set[str]:
    return {failure.code for failure in failures}


def _validate(
    inventory: dict[str, object],
    *,
    workflow_text: str = WORKFLOW_TEXT,
    changed_paths: tuple[str, ...] = (),
    tracked_paths: tuple[str, ...] = (),
    staged_paths: tuple[str, ...] = (),
    discovered_idempotence=None,
    pytest_membership=None,
    runner_shards=None,
):
    return validator.validate(
        REPO_ROOT,
        inventory=inventory,
        workflow_text=workflow_text,
        changed_paths=changed_paths,
        tracked_paths=tracked_paths,
        staged_paths=staged_paths,
        discovered_idempotence=discovered_idempotence,
        pytest_membership=pytest_membership,
        runner_shards=runner_shards,
    )


def _discovered_with(path: str, **updates):
    discovered = list(validator.discover_idempotence_tests(REPO_ROOT))
    for index, item in enumerate(discovered):
        if item.path == path:
            discovered[index] = validator.DiscoveredIdempotence(
                path=item.path,
                has_verify_idempotent=updates.get(
                    "has_verify_idempotent", item.has_verify_idempotent
                ),
                builder_twice=updates.get("builder_twice", item.builder_twice),
                bounded_contract=updates.get("bounded_contract", item.bounded_contract),
            )
            return tuple(discovered)
    raise AssertionError(f"missing discovered idempotence path: {path}")


def _run_synthetic_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed


def _initialize_synthetic_repo(repo_root: Path) -> None:
    repo_root.mkdir(exist_ok=True)
    _run_synthetic_git(repo_root, "init", "-q")
    _run_synthetic_git(repo_root, "config", "user.name", "QTT Test")
    _run_synthetic_git(
        repo_root,
        "config",
        "user.email",
        "qtt-test@example.invalid",
    )
    _run_synthetic_git(repo_root, "config", "core.autocrlf", "false")


def _assert_repository_stream_classifier_matrix(monkeypatch, tmp_path: Path) -> None:
    lf_json = b'{"value":1}\n'
    crlf_json = b'{"value":1}\r\n'
    pure_cases = (
        (
            "CLEAN",
            "CLEAN",
            "CLEAN",
            "CLEAN_IDENTICAL",
            "WORKTREE_FILTER_EQUIVALENT_CLEAN",
        ),
        (
            "DIRTY",
            "CLEAN",
            "CLEAN",
            "STAT_CACHE_ONLY_CHANGE",
            "GIT_CANONICAL_CONTENT_IDENTICAL",
        ),
        (
            "DIRTY",
            "DIRTY",
            "CLEAN",
            "EOL_REPRESENTATION_ONLY_CHANGE",
            None,
        ),
    )
    for status, unstaged, staged, expected_class, expected_reason in pure_cases:
        record = reliability.classify_byte_surfaces(
            path="filter-equivalent.json",
            baseline_bytes=lf_json,
            index_bytes=lf_json,
            worktree_bytes=crlf_json,
            git_status_state=status,
            git_attribute_text="set",
            git_attribute_eol="lf",
            git_unstaged_diff_state=unstaged,
            git_staged_diff_state=staged,
            authorized=True,
        )
        assert record.change_class == expected_class
        assert record.semantic_scope_member is False
        if expected_reason is not None:
            assert expected_reason in record.reason_codes
        if expected_class == "CLEAN_IDENTICAL":
            assert record.publication_cleanliness_state == "CLEAN"
            assert reliability.text_integrity_failure_codes((record,)) == ()
            assert reliability.semantic_candidate_paths((record,)) == ()
        elif expected_class == "STAT_CACHE_ONLY_CHANGE":
            assert record.publication_cleanliness_state == "DIRTY_MUST_BE_REFRESHED"
            assert reliability.text_integrity_failure_codes((record,)) == (
                "ENGVR_UNRELATED_TEXT_REPRESENTATION_DRIFT",
            )
        else:
            assert record.publication_cleanliness_state == "DIRTY_MUST_BE_RESOLVED"
            assert reliability.text_integrity_failure_codes((record,)) == (
                "ENGVR_UNRELATED_TEXT_REPRESENTATION_DRIFT",
            )

    staged_semantic = reliability.classify_byte_surfaces(
        path="staged-semantic.json",
        baseline_bytes=b'{"value":0}\n',
        index_bytes=lf_json,
        worktree_bytes=crlf_json,
        git_status_state="DIRTY",
        git_attribute_text="set",
        git_attribute_eol="lf",
        git_unstaged_diff_state="CLEAN",
        git_staged_diff_state="DIRTY",
        authorized=True,
    )
    assert staged_semantic.change_class == "SEMANTIC_TEXT_CHANGE"
    assert staged_semantic.semantic_scope_member is True
    assert "WORKTREE_FILTER_EQUIVALENT_CLEAN" not in staged_semantic.reason_codes

    filter_parent = tmp_path / "filter-equivalent-parent"
    filter_parent.mkdir()
    with tempfile.TemporaryDirectory(
        prefix="repository-",
        dir=filter_parent,
    ) as value:
        filter_repo = Path(value)
        _initialize_synthetic_repo(filter_repo)
        attributes_path = filter_repo / ".gitattributes"
        filter_path = filter_repo / "filter.json"
        attributes_path.write_bytes(b"*.json text eol=lf\n")
        filter_path.write_bytes(crlf_json)
        assert filter_path.read_bytes() == crlf_json
        _run_synthetic_git(
            filter_repo,
            "add",
            "--",
            ".gitattributes",
            "filter.json",
        )
        _run_synthetic_git(filter_repo, "commit", "-qm", "filter baseline")

        index_before = _run_synthetic_git(
            filter_repo,
            "show",
            ":filter.json",
        ).stdout
        worktree_before = filter_path.read_bytes()
        staged_before = _run_synthetic_git(
            filter_repo,
            "diff",
            "--cached",
            "--name-only",
            "-z",
            "--",
        ).stdout
        controls_before = _run_synthetic_git(
            filter_repo,
            "ls-files",
            "-v",
            "-z",
            "--",
        ).stdout
        status_before = reliability._git_exact_path_status_state(
            filter_repo,
            "filter.json",
        )
        unstaged_before = reliability._git_exact_path_diff_state(
            filter_repo,
            "filter.json",
            baseline_ref="HEAD",
            staged=False,
        )
        staged_diff_before = reliability._git_exact_path_diff_state(
            filter_repo,
            "filter.json",
            baseline_ref="HEAD",
            staged=True,
        )
        diff_files_before = _run_synthetic_git(
            filter_repo,
            "diff-files",
            "--quiet",
            "--",
            "filter.json",
        ).returncode
        assert index_before == lf_json
        assert worktree_before == crlf_json
        assert status_before == "CLEAN"
        assert unstaged_before == "CLEAN"
        assert staged_diff_before == "CLEAN"
        assert diff_files_before == 0
        assert reliability._git_attributes(filter_repo, "filter.json") == (
            "set",
            "lf",
        )

        exact_diff_calls: list[tuple[str, bool]] = []
        refresh_calls: list[tuple[object, ...]] = []
        original_exact_diff = reliability._git_exact_path_diff_state

        def tracked_exact_diff(root, path, *, baseline_ref, staged):
            exact_diff_calls.append((path, staged))
            return original_exact_diff(
                root,
                path,
                baseline_ref=baseline_ref,
                staged=staged,
            )

        with monkeypatch.context() as filter_patch:
            filter_patch.setattr(
                reliability,
                "_git_exact_path_diff_state",
                tracked_exact_diff,
            )
            filter_patch.setattr(
                reliability,
                "_run_exact_stat_refresh",
                lambda *args, **kwargs: refresh_calls.append((args, kwargs)),
            )
            filter_records = reliability.classify_repository_changes(
                filter_repo,
                authorized_paths=("filter.json",),
                baseline_ref="HEAD",
                include_paths=("filter.json",),
            )
        assert len(filter_records) == 1
        filter_record = filter_records[0]
        assert filter_record.path == "filter.json"
        assert filter_record.change_class == "CLEAN_IDENTICAL"
        assert filter_record.git_status_state == "CLEAN"
        assert filter_record.semantic_scope_member is False
        assert filter_record.publication_cleanliness_state == "CLEAN"
        assert "WORKTREE_FILTER_EQUIVALENT_CLEAN" in filter_record.reason_codes
        assert filter_record.index_profile.terminal_newline_kind == "LF"
        assert filter_record.worktree_profile.terminal_newline_kind == "CRLF"
        assert reliability.semantic_candidate_paths(filter_records) == ()
        assert reliability.text_integrity_failure_codes(filter_records) == ()
        assert exact_diff_calls == [("filter.json", False), ("filter.json", True)]
        assert refresh_calls == []
        assert _run_synthetic_git(filter_repo, "show", ":filter.json").stdout == (
            index_before
        )
        assert filter_path.read_bytes() == worktree_before
        assert _run_synthetic_git(
            filter_repo,
            "diff",
            "--cached",
            "--name-only",
            "-z",
            "--",
        ).stdout == staged_before
        assert _run_synthetic_git(
            filter_repo,
            "ls-files",
            "-v",
            "-z",
            "--",
        ).stdout == controls_before
        assert reliability._git_exact_path_status_state(
            filter_repo,
            "filter.json",
        ) == "CLEAN"
        assert reliability._git_exact_path_diff_state(
            filter_repo,
            "filter.json",
            baseline_ref="HEAD",
            staged=False,
        ) == "CLEAN"
        assert reliability._git_exact_path_diff_state(
            filter_repo,
            "filter.json",
            baseline_ref="HEAD",
            staged=True,
        ) == "CLEAN"

        filter_path.write_bytes(b'{"value":2}\n')
        dirty_diff = subprocess.run(
            ("git", "diff", "--quiet", "--", "filter.json"),
            cwd=filter_repo,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert dirty_diff.returncode == 1
        semantic_chunk_bound = 4
        opened_filter_descriptors = []
        initial_filter_offsets = []
        bounded_read_requests = []
        real_worktree_open = reliability._open_regular_worktree_descriptor
        real_bounded_read = reliability._BoundedContentReader.read

        def tracked_worktree_open(path):
            descriptor = real_worktree_open(path)
            if Path(path) == filter_path:
                opened_filter_descriptors.append(descriptor)
                initial_filter_offsets.append(os.lseek(descriptor, 0, os.SEEK_CUR))
            return descriptor

        def tracked_bounded_read(reader, size=-1):
            bounded_read_requests.append(size)
            return real_bounded_read(reader, size)

        with monkeypatch.context() as reopen_patch:
            reopen_patch.setattr(
                reliability,
                "_open_regular_worktree_descriptor",
                tracked_worktree_open,
            )
            reopen_patch.setattr(
                reliability._BoundedContentReader,
                "read",
                tracked_bounded_read,
            )
            changed_records = reliability.classify_repository_changes(
                filter_repo,
                authorized_paths=("filter.json",),
                baseline_ref="HEAD",
                include_paths=("filter.json",),
                chunk_size=semantic_chunk_bound,
            )
        changed_filter = {record.path: record for record in changed_records}[
            "filter.json"
        ]
        assert changed_filter.change_class == "SEMANTIC_TEXT_CHANGE"
        assert changed_filter.semantic_scope_member is True
        assert "WORKTREE_FILTER_EQUIVALENT_CLEAN" not in changed_filter.reason_codes
        assert "filter.json" in reliability.semantic_candidate_paths(changed_records)
        assert "ENGVR_TEXT_ENCODING_UNCLASSIFIED" not in (
            reliability.text_integrity_failure_codes(changed_records)
        )
        assert changed_filter.baseline_profile.utf8_decode_state == "UTF8_VALID"
        assert changed_filter.index_profile.utf8_decode_state == "UTF8_VALID"
        assert changed_filter.worktree_profile.utf8_decode_state == "UTF8_VALID"
        assert changed_filter.worktree_profile.byte_count == len(b'{"value":2}\n')
        assert changed_filter.worktree_profile.contains_nul is False
        assert changed_filter.worktree_profile.has_mixed_line_endings is False
        assert changed_filter.worktree_profile.bare_cr_count == 0
        assert changed_filter.worktree_profile.terminal_newline_kind == "LF"
        assert len(opened_filter_descriptors) > 1
        assert initial_filter_offsets == [0] * len(opened_filter_descriptors)
        assert bounded_read_requests
        assert max(bounded_read_requests) <= semantic_chunk_bound
        for descriptor in opened_filter_descriptors:
            with pytest.raises(OSError):
                os.fstat(descriptor)
    assert not any(filter_parent.iterdir())

    temporary_parent = tmp_path / "streaming-classifier-parent"
    temporary_parent.mkdir()
    with tempfile.TemporaryDirectory(
        prefix="repository-",
        dir=temporary_parent,
    ) as value:
        repo_root = Path(value)
        _initialize_synthetic_repo(repo_root)
        chunk_size = 4096
        large_path = repo_root / "large.py"
        boundary_path = repo_root / "boundary.py"
        large_baseline = b"controlled line\n" * 30_000
        large_path.write_bytes(large_baseline)
        boundary_path.write_bytes(
            b"x" * (chunk_size - 1) + b"\r\nsecond\r\n"
        )
        _run_synthetic_git(
            repo_root,
            "add",
            "--",
            "large.py",
            "boundary.py",
        )
        _run_synthetic_git(repo_root, "commit", "-qm", "baseline")
        large_path.write_bytes(b"changed line\n" + large_baseline)

        read_requests: list[int] = []
        original_read = reliability._BoundedContentReader.read

        def tracked_read(reader, size=-1):
            read_requests.append(size)
            return original_read(reader, size)

        with monkeypatch.context() as stream_patch:
            stream_patch.setattr(
                reliability._BoundedContentReader,
                "read",
                tracked_read,
            )
            records = reliability.classify_repository_changes(
                repo_root,
                authorized_paths=("large.py", "boundary.py"),
                baseline_ref="HEAD",
                include_paths=("boundary.py",),
                chunk_size=chunk_size,
            )
        by_path = {record.path: record for record in records}
        assert by_path["large.py"].change_class == "SEMANTIC_TEXT_CHANGE"
        assert by_path["large.py"].worktree_profile.byte_count == len(
            b"changed line\n" + large_baseline
        )
        assert by_path["boundary.py"].baseline_profile.crlf_count == 2
        assert by_path["boundary.py"].baseline_profile.bare_cr_count == 0
        assert read_requests
        assert min(read_requests) > 0
        assert max(read_requests) == chunk_size
        classifier_source = inspect.getsource(
            reliability.classify_repository_changes
        )
        assert ".read_bytes(" not in classifier_source
        assert "_git_blob_bytes" not in classifier_source
        exact_diff_source = inspect.getsource(reliability._git_exact_path_diff_state)
        assert "shell=False" in exact_diff_source
        for forbidden_option in (
            "--ignore-cr-at-eol",
            "--ignore-space-at-eol",
            "--ignore-all-space",
        ):
            assert forbidden_option not in exact_diff_source

    assert not any(temporary_parent.iterdir())


def _assert_exact_stat_refresh_matrix(monkeypatch, tmp_path: Path) -> None:
    temporary_parent = tmp_path / "stat-refresh-parent"
    temporary_parent.mkdir()
    with tempfile.TemporaryDirectory(prefix="repository-", dir=temporary_parent) as value:
        repo_root = Path(value)
        _initialize_synthetic_repo(repo_root)
        fixtures = {
            ".gitattributes": b"*.json text eol=lf\n",
            "filter-stat.json": b'{"value":1}\n',
            "same.py": b"same\n",
            "metadata.csv": b"metadata\n",
            "semantic.py": b"old\n",
            "eol.py": b"line\n",
            "control.py": b"control\n",
            "skip.py": b"skip\n",
        }
        for name, content in fixtures.items():
            (repo_root / name).write_bytes(content)
        _run_synthetic_git(repo_root, "add", "--", *fixtures)
        _run_synthetic_git(repo_root, "commit", "-qm", "baseline")
        _run_synthetic_git(
            repo_root,
            "update-index",
            "--assume-unchanged",
            "--",
            "control.py",
        )
        _run_synthetic_git(
            repo_root,
            "update-index",
            "--skip-worktree",
            "--",
            "skip.py",
        )
        same_path = repo_root / "same.py"
        same_stat = same_path.stat()
        os.utime(
            same_path,
            (same_stat.st_atime + 120, same_stat.st_mtime + 120),
        )
        metadata_path = repo_root / "metadata.csv"
        metadata_stat = metadata_path.stat()
        os.utime(
            metadata_path,
            (metadata_stat.st_atime + 120, metadata_stat.st_mtime + 120),
        )
        filter_stat_path = repo_root / "filter-stat.json"
        filter_stat_path.write_bytes(b'{"value":1}\r\n')
        (repo_root / "semantic.py").write_bytes(b"new\n")
        (repo_root / "eol.py").write_bytes(b"line\r\n")
        (repo_root / "untracked.py").write_bytes(b"untracked\n")

        transient_targets = {"filter-stat.json", "metadata.csv", "same.py"}
        transient_status_calls = {path: 0 for path in transient_targets}
        dirty_call_limits = {path: 2 for path in transient_targets}
        real_exact_status = reliability._git_exact_path_status_state

        def transient_exact_status(root, path):
            if path in transient_targets:
                transient_status_calls[path] += 1
                if transient_status_calls[path] <= dirty_call_limits[path]:
                    return "DIRTY"
            return real_exact_status(root, path)

        monkeypatch.setattr(
            reliability,
            "_git_exact_path_status_state",
            transient_exact_status,
        )
        records = reliability.classify_repository_changes(
            repo_root,
            authorized_paths=(
                "filter-stat.json",
                "same.py",
                "semantic.py",
                "eol.py",
            ),
            baseline_ref="HEAD",
            include_paths=tuple(sorted(transient_targets)),
        )
        by_path = {record.path: record for record in records}
        assert by_path["filter-stat.json"].change_class == "STAT_CACHE_ONLY_CHANGE"
        assert "GIT_CANONICAL_CONTENT_IDENTICAL" in by_path[
            "filter-stat.json"
        ].reason_codes
        assert by_path["same.py"].change_class == "STAT_CACHE_ONLY_CHANGE"
        assert by_path["metadata.csv"].change_class == "STAT_CACHE_ONLY_CHANGE"
        assert by_path["metadata.csv"].outside_policy_disposition == (
            "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
        )
        assert by_path["semantic.py"].change_class == "SEMANTIC_TEXT_CHANGE"
        assert by_path["eol.py"].change_class == "EOL_REPRESENTATION_ONLY_CHANGE"
        assert by_path["untracked.py"].change_class == "NEW_CONTROLLED_TEXT_FILE"
        contents_before = {
            path: (repo_root / path).read_bytes()
            for path in (
                "same.py",
                "metadata.csv",
                "filter-stat.json",
                "semantic.py",
                "eol.py",
                "untracked.py",
            )
        }
        staged_before = _run_synthetic_git(
            repo_root,
            "diff",
            "--cached",
            "--name-only",
            "-z",
            "--",
        ).stdout
        controls_before = _run_synthetic_git(
            repo_root,
            "ls-files",
            "-v",
            "-z",
            "--",
        ).stdout

        real_initial_refresh = reliability._run_exact_stat_refresh
        initial_refresh_calls: list[tuple[tuple[str, ...], bool]] = []

        def track_initial_refresh(root, paths, *, stronger):
            initial_refresh_calls.append((tuple(paths), stronger))
            return real_initial_refresh(root, paths, stronger=stronger)

        with monkeypatch.context() as initial_refresh_patch:
            initial_refresh_patch.setattr(
                reliability,
                "_run_exact_stat_refresh",
                track_initial_refresh,
            )
            refreshed = reliability.refresh_exact_stat_cache_paths(repo_root, records)
        assert initial_refresh_calls
        assert initial_refresh_calls[0] == (
            ("filter-stat.json", "metadata.csv", "same.py"),
            False,
        )
        assert all(
            set(paths).issubset(transient_targets)
            for paths, _stronger in initial_refresh_calls
        )
        refreshed_by_path = {record.path: record for record in refreshed}
        assert refreshed_by_path["filter-stat.json"].change_class == "CLEAN_IDENTICAL"
        assert refreshed_by_path["filter-stat.json"].git_status_state == "CLEAN"
        assert "WORKTREE_FILTER_EQUIVALENT_CLEAN" in refreshed_by_path[
            "filter-stat.json"
        ].reason_codes
        assert filter_stat_path.read_bytes() == b'{"value":1}\r\n'
        assert _run_synthetic_git(
            repo_root,
            "show",
            ":filter-stat.json",
        ).stdout == b'{"value":1}\n'
        assert refreshed_by_path["same.py"].change_class == "CLEAN_IDENTICAL"
        assert refreshed_by_path["same.py"].git_status_state == "CLEAN"
        assert refreshed_by_path["metadata.csv"].change_class == "CLEAN_IDENTICAL"
        assert refreshed_by_path["metadata.csv"].git_status_state == "CLEAN"
        assert refreshed_by_path["semantic.py"].change_class == (
            "SEMANTIC_TEXT_CHANGE"
        )
        assert refreshed_by_path["eol.py"].change_class == (
            "EOL_REPRESENTATION_ONLY_CHANGE"
        )
        assert refreshed_by_path["untracked.py"].change_class == (
            "NEW_CONTROLLED_TEXT_FILE"
        )
        assert {
            path: (repo_root / path).read_bytes()
            for path in contents_before
        } == contents_before
        assert _run_synthetic_git(
            repo_root,
            "diff",
            "--cached",
            "--name-only",
            "-z",
            "--",
        ).stdout == staged_before
        assert _run_synthetic_git(
            repo_root,
            "ls-files",
            "-v",
            "-z",
            "--",
        ).stdout == controls_before

        current_stat = same_path.stat()
        os.utime(
            same_path,
            (current_stat.st_atime + 120, current_stat.st_mtime + 120),
        )
        transient_status_calls["same.py"] = 0
        dirty_call_limits["same.py"] = 3
        stronger_records = reliability.classify_repository_changes(
            repo_root,
            authorized_paths=("same.py",),
            baseline_ref="HEAD",
            include_paths=("same.py",),
        )
        assert {record.path: record for record in stronger_records}[
            "same.py"
        ].change_class == "STAT_CACHE_ONLY_CHANGE"
        real_refresh = reliability._run_exact_stat_refresh
        refresh_calls: list[tuple[tuple[str, ...], bool]] = []

        def force_bounded_escalation(root, paths, *, stronger):
            refresh_calls.append((tuple(paths), stronger))
            if not stronger:
                stale = same_path.stat()
                os.utime(
                    same_path,
                    (stale.st_atime + 120, stale.st_mtime + 120),
                )
                return 1
            return real_refresh(root, paths, stronger=True)

        with monkeypatch.context() as refresh_patch:
            refresh_patch.setattr(
                reliability,
                "_run_exact_stat_refresh",
                force_bounded_escalation,
            )
            escalated = reliability.refresh_exact_stat_cache_paths(
                repo_root,
                stronger_records,
            )
        assert refresh_calls == [(("same.py",), False), (("same.py",), True)]
        assert {record.path: record for record in escalated}[
            "same.py"
        ].change_class == "CLEAN_IDENTICAL"
        assert {
            path: (repo_root / path).read_bytes()
            for path in contents_before
        } == contents_before
    assert not any(temporary_parent.iterdir())


def _assert_no_follow_worktree_surface_contract(monkeypatch, tmp_path: Path) -> None:
    temporary_parent = tmp_path / "no-follow-worktree-parent"
    temporary_parent.mkdir()
    with tempfile.TemporaryDirectory(
        prefix="repository-",
        dir=temporary_parent,
    ) as value:
        repo_root = Path(value)
        _initialize_synthetic_repo(repo_root)
        regular_path = repo_root / "a.py"
        race_path = repo_root / "race.py"
        regular_path.write_bytes(b"regular baseline\n")
        race_path.write_bytes(b"race baseline\n")
        _run_synthetic_git(repo_root, "add", "--", "a.py", "race.py")
        _run_synthetic_git(repo_root, "commit", "-qm", "regular baseline")
        external_target = temporary_parent / "external-target.py"
        external_target.write_bytes(b"external target must remain unread\n")
        external_before = external_target.read_bytes()
        regular_path.unlink()
        symlink_supported = True
        try:
            os.symlink(external_target, regular_path)
        except (OSError, NotImplementedError):
            symlink_supported = False

        external_open_count = 0
        real_open_descriptor = reliability._open_regular_worktree_descriptor

        def track_external_open(path):
            nonlocal external_open_count
            if Path(path) == external_target:
                external_open_count += 1
            return real_open_descriptor(path)

        if symlink_supported:
            with monkeypatch.context() as link_patch:
                link_patch.setattr(
                    reliability,
                    "_open_regular_worktree_descriptor",
                    track_external_open,
                )
                linked_records = reliability.classify_repository_changes(
                    repo_root,
                    authorized_paths=("a.py",),
                    baseline_ref="HEAD",
                    include_paths=("a.py",),
                )
            linked_record = {record.path: record for record in linked_records}["a.py"]
            assert linked_record.change_class == "ENCODING_OR_UNCLASSIFIED_CHANGE"
            assert "WORKTREE_FILE_TYPE_CHANGE_OR_LINK" in linked_record.reason_codes
            assert linked_record.semantic_scope_member is False
            assert linked_record.publication_cleanliness_state == "FAIL_DECISION_REQUIRED"
            assert reliability.semantic_candidate_paths((linked_record,)) == ()
            assert reliability.text_integrity_failure_codes((linked_record,)) == (
                "ENGVR_TEXT_ENCODING_UNCLASSIFIED",
            )
            assert linked_record.worktree_profile is None
            assert external_open_count == 0
            assert external_target.read_bytes() == external_before

            tracked_link = repo_root / "tracked-link.py"
            os.symlink("first-target.py", tracked_link)
            _run_synthetic_git(repo_root, "add", "--", "tracked-link.py")
            _run_synthetic_git(repo_root, "commit", "-qm", "tracked symlink")
            baseline_mode, index_mode = reliability._git_exact_path_modes(
                repo_root,
                "HEAD",
                "tracked-link.py",
            )
            assert baseline_mode == index_mode == "120000"
            clean_link = {
                record.path: record
                for record in reliability.classify_repository_changes(
                    repo_root,
                    baseline_ref="HEAD",
                    include_paths=("tracked-link.py",),
                )
            }["tracked-link.py"]
            assert clean_link.change_class == "CLEAN_IDENTICAL"
            assert clean_link.worktree_state == "PRESENT_SYMLINK"
            assert "TRACKED_SYMLINK_PAYLOAD_IDENTICAL" in clean_link.reason_codes
            tracked_link.unlink()
            os.symlink("second-target.py", tracked_link)
            changed_link = {
                record.path: record
                for record in reliability.classify_repository_changes(
                    repo_root,
                    baseline_ref="HEAD",
                    include_paths=("tracked-link.py",),
                )
            }["tracked-link.py"]
            assert changed_link.change_class == "ENCODING_OR_UNCLASSIFIED_CHANGE"
            assert "TRACKED_SYMLINK_PAYLOAD_CHANGE" in changed_link.reason_codes
            assert changed_link.semantic_scope_member is False

            regular_path.unlink()
            regular_path.write_bytes(b"regular baseline\n")
            race_swaps = []

            def swap_before_open(path):
                candidate = Path(path)
                if candidate == race_path and not race_swaps:
                    race_swaps.append(candidate)
                    candidate.unlink()
                    os.symlink(external_target, candidate)
                return real_open_descriptor(candidate)

            with monkeypatch.context() as race_patch:
                race_patch.setattr(
                    reliability,
                    "_open_regular_worktree_descriptor",
                    swap_before_open,
                )
                race_record = {
                    record.path: record
                    for record in reliability.classify_repository_changes(
                        repo_root,
                        authorized_paths=("race.py",),
                        baseline_ref="HEAD",
                        include_paths=("race.py",),
                    )
                }["race.py"]
            assert race_swaps == [race_path]
            assert race_record.change_class == "ENCODING_OR_UNCLASSIFIED_CHANGE"
            assert "WORKTREE_FILE_TYPE_CHANGE_OR_LINK" in race_record.reason_codes
            assert race_record.semantic_scope_member is False
            assert race_record.worktree_profile is None
            assert external_open_count == 0
            assert external_target.read_bytes() == external_before
        else:
            regular_path.write_bytes(b"regular baseline\n")
            assert os.name == "nt"
    external_target.unlink()
    assert not any(temporary_parent.iterdir())


def _assert_runtime_artifact_semantic_scope_contract(
    monkeypatch,
    inventory: dict[str, object],
) -> None:
    router_path = (
        ".tmp/qtt-validation-router/deterministic-validators-a.json"
    )
    timing_path = (
        ".tmp/qtt-validation-timing/deterministic-validators-a.json"
    )
    authorized_path = "tools/validate_idempotence_runtime_containment.py"
    near_name_path = (
        ".tmp/qtt-validation-router-extra/deterministic-validators-a.json"
    )
    wrong_extension_path = (
        ".tmp/qtt-validation-router/deterministic-validators-a.txt"
    )

    runtime_records = tuple(
        reliability.classify_byte_surfaces(
            path=path,
            baseline_bytes=None,
            index_bytes=None,
            worktree_bytes=b'{"value":1}\n',
            path_state="NEW",
            git_status_state="DIRTY",
            authorized=False,
        )
        for path in (router_path, timing_path)
    )
    authorized_record = reliability.classify_byte_surfaces(
        path=authorized_path,
        baseline_bytes=b"old\n",
        index_bytes=b"new\n",
        worktree_bytes=b"new\n",
        git_status_state="DIRTY",
        authorized=True,
    )
    near_name_record = reliability.classify_byte_surfaces(
        path=near_name_path,
        baseline_bytes=None,
        index_bytes=None,
        worktree_bytes=b'{"value":1}\n',
        path_state="NEW",
        git_status_state="DIRTY",
        authorized=False,
    )
    wrong_extension_record = reliability.classify_byte_surfaces(
        path=wrong_extension_path,
        baseline_bytes=None,
        index_bytes=None,
        worktree_bytes=b'{"value":1}\n',
        path_state="NEW",
        git_status_state="DIRTY",
        authorized=False,
    )
    records = (
        *runtime_records,
        authorized_record,
        near_name_record,
        wrong_extension_record,
    )
    generic_paths = reliability.semantic_candidate_paths(records)
    assert router_path in generic_paths
    assert timing_path in generic_paths

    selected_paths = validator._semantic_nonruntime_integrity_paths(
        records,
        inventory,
    )
    assert selected_paths == tuple(
        path
        for path in generic_paths
        if path not in {router_path, timing_path}
    )
    assert router_path not in selected_paths
    assert timing_path not in selected_paths
    assert authorized_path in selected_paths
    assert not validator.is_runtime_artifact_path(near_name_path, inventory)
    assert near_name_path in selected_paths
    assert not validator.is_runtime_artifact_path(wrong_extension_path, inventory)
    assert wrong_extension_path in selected_paths

    invalid_runtime_record = reliability.classify_byte_surfaces(
        path=router_path,
        baseline_bytes=None,
        index_bytes=None,
        worktree_bytes=b'{"value":1}',
        path_state="NEW",
        git_status_state="DIRTY",
        authorized=False,
    )
    assert "ENGVR_EOF_POLICY_FAILURE" in _codes(
        validator._validate_changed_path_integrity((invalid_runtime_record,))
    )

    captured_changed_paths: list[tuple[str, ...]] = []
    real_validate_changed_files = validator._validate_changed_files

    def record_validate_changed_files(
        candidate_inventory,
        changed_paths,
        **kwargs,
    ):
        captured_changed_paths.append(tuple(changed_paths))
        return real_validate_changed_files(
            candidate_inventory,
            changed_paths,
            **kwargs,
        )

    with monkeypatch.context() as integration_patch:
        integration_patch.setattr(
            validator,
            "_changed_path_integrity",
            lambda _root: (*runtime_records, authorized_record),
        )
        integration_patch.setattr(
            validator,
            "_current_branch",
            lambda _root: context.ENGVR_IMPLEMENTATION_BRANCH,
        )
        integration_patch.setattr(
            validator,
            "_validate_changed_files",
            record_validate_changed_files,
        )
        integration_failures = validator.validate(
            REPO_ROOT,
            inventory=inventory,
            workflow_text=WORKFLOW_TEXT,
            changed_paths=None,
            tracked_paths=(),
            staged_paths=(),
        )
    assert integration_failures == ()
    assert captured_changed_paths == [(authorized_path,)]

    explicit_failures = validator.validate(
        REPO_ROOT,
        inventory=inventory,
        workflow_text=WORKFLOW_TEXT,
        changed_paths=(router_path,),
        tracked_paths=(),
        staged_paths=(),
    )
    assert validator.Failure(
        "SEMANTIC_CHANGED_PATH_OUTSIDE_SCOPE",
        (("path", router_path),),
    ) in explicit_failures


def test_current_inventory_passes_and_classifies_runtime_containment(
    monkeypatch,
    tmp_path,
):
    inventory = _inventory()
    failures = _validate(inventory)

    assert failures == ()
    assert {entry["phase"] for entry in inventory["pytest_shards"]} == {
        f"pytest-shard-{index}" for index in range(1, 9)
    }
    assert {entry["family"] for entry in inventory["known_heavy_families"]} >= {
        "PR166-SF-R2",
        "PR166-SM3",
        "PR166-SM2",
        "PR165-D3",
        "PR166-S2",
        "PR165-D2",
        "PR166-SF",
        "PR166-SM",
        "PR162E-Q",
    }
    assert all(
        entry["classification"].startswith("RUNTIME_ARTIFACT_")
        for entry in inventory["runtime_artifact_policy"]
    )
    assert {
        entry["classification"]
        for entry in inventory["checkout_fixture_requirements"]
    } == {"CHECKOUT_FIXTURE_CLASSIFIED_ONLY"}
    assert inventory["manual_nightly_exhaustive_paths"]

    surfaces = (
        (b"a\n", b"a\n", b"a\n", "CLEAN", "CLEAN_IDENTICAL", "a.py", "EXISTING"),
        (b"a\n", b"a\n", b"a\r\n", "DIRTY", "EOL_REPRESENTATION_ONLY_CHANGE", "a.py", "EXISTING"),
        (b"a\n", b"a\n", b"a\r\nb\n", "DIRTY", "MIXED_LINE_ENDING_ERROR", "a.py", "EXISTING"),
        (b"a\n", b"a\n", b"a\rb", "DIRTY", "BARE_CR_ERROR", "a.py", "EXISTING"),
        (b"a\n", b"a", b"a", "DIRTY", "EOF_FINAL_NEWLINE_ONLY_CHANGE", "a.py", "EXISTING"),
        (b"a\n", b"b\n", b"b\n", "DIRTY", "SEMANTIC_TEXT_CHANGE", "a.py", "EXISTING"),
        (b"a\n", b"b \n", b"b \n", "DIRTY", "REAL_WHITESPACE_ERROR", "a.py", "EXISTING"),
        (None, None, b"\x00binary", "DIRTY", "BINARY_CHANGE", "a.bin", "NEW"),
        (b"a\n", b"\xff\n", b"\xff\n", "DIRTY", "ENCODING_OR_UNCLASSIFIED_CHANGE", "a.py", "EXISTING"),
        (None, None, b"new\n", "DIRTY", "NEW_CONTROLLED_TEXT_FILE", "new.py", "NEW"),
        (b"a\n", b"a\n", b"a\n", "DIRTY", "STAT_CACHE_ONLY_CHANGE", "a.py", "EXISTING"),
        (b"a\n", b"b\n", b"b\n", "DIRTY", "OUTSIDE_MANAGED_TEXT_POLICY_CHANGE", "a.csv", "EXISTING"),
        (b"a,b\n", b"a,b\n", b"a,b\n", "DIRTY", "STAT_CACHE_ONLY_CHANGE", "metadata.csv", "EXISTING"),
        (b"a\x00b", b"a\x00b", b"a\x00b", "DIRTY", "STAT_CACHE_ONLY_CHANGE", "metadata.bin", "EXISTING"),
        (b"a\x00b", b"a\x00c", b"a\x00c", "DIRTY", "BINARY_CHANGE", "changed.bin", "EXISTING"),
    )
    classifications = []
    for baseline, index, worktree, status, expected, path, path_state in surfaces:
        record = reliability.classify_byte_surfaces(
            path=path,
            baseline_bytes=baseline,
            index_bytes=index,
            worktree_bytes=worktree,
            path_state=path_state,
            git_status_state=status,
            authorized=path != "a.csv",
        )
        classifications.append(record)
        assert record.change_class == expected
    assert classifications[1].semantic_scope_member is False
    assert classifications[4].semantic_scope_member is False
    assert classifications[10].semantic_scope_member is False
    assert classifications[11].outside_policy_disposition == (
        "OUTSIDE_MANAGED_TEXT_POLICY_REQUIRES_OWNER_DECISION"
    )
    assert classifications[12].outside_policy_disposition == (
        "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
    )
    assert classifications[13].outside_policy_disposition == (
        "OUTSIDE_MANAGED_TEXT_POLICY_UNCHANGED"
    )
    assert reliability.text_integrity_failure_codes((classifications[8],)) == (
        "ENGVR_TEXT_ENCODING_UNCLASSIFIED",
    )

    staged_windows = reliability.classify_byte_surfaces(
        path="windows.py",
        baseline_bytes=b"old\n",
        index_bytes=b"new\n",
        worktree_bytes=b"new\r\n",
        authorized=True,
    )
    assert staged_windows.change_class == "SEMANTIC_TEXT_CHANGE"
    assert staged_windows.index_profile.terminal_newline_kind == "LF"
    assert "WORKTREE_REPRESENTATION_DIFFERS_FROM_INDEX" in staged_windows.reason_codes
    assert reliability.text_integrity_failure_codes((staged_windows,)) == ()

    semantic_without_terminal_lf = reliability.classify_byte_surfaces(
        path="semantic-no-eof.py",
        baseline_bytes=b"old\n",
        index_bytes=b"new",
        worktree_bytes=b"new",
        authorized=True,
    )
    assert semantic_without_terminal_lf.change_class == "SEMANTIC_TEXT_CHANGE"
    assert semantic_without_terminal_lf.semantic_scope_member is True
    assert reliability.text_integrity_failure_codes(
        (semantic_without_terminal_lf,)
    ) == ("ENGVR_EOF_POLICY_FAILURE",)
    new_without_terminal_lf = reliability.classify_byte_surfaces(
        path="new-no-eof.py",
        baseline_bytes=None,
        index_bytes=None,
        worktree_bytes=b"new",
        path_state="NEW",
        authorized=True,
    )
    assert new_without_terminal_lf.change_class == "NEW_CONTROLLED_TEXT_FILE"
    assert new_without_terminal_lf.semantic_scope_member is True
    assert reliability.text_integrity_failure_codes((new_without_terminal_lf,)) == (
        "ENGVR_EOF_POLICY_FAILURE",
    )
    staged_with_unstaged_semantics = reliability.classify_byte_surfaces(
        path="partially-staged.py",
        baseline_bytes=b"old\n",
        index_bytes=b"staged\n",
        worktree_bytes=b"unstaged\n",
        authorized=True,
    )
    assert staged_with_unstaged_semantics.change_class == "SEMANTIC_TEXT_CHANGE"
    assert "ENGVR_PREPUBLICATION_CUSTODY_FAILED" in (
        reliability.text_integrity_failure_codes((staged_with_unstaged_semantics,))
    )
    hard_worktree_surface = reliability.classify_byte_surfaces(
        path="hard-worktree.py",
        baseline_bytes=b"old\n",
        index_bytes=b"staged\n",
        worktree_bytes=b"staged\r\nextra\n",
        authorized=True,
    )
    assert hard_worktree_surface.change_class == "MIXED_LINE_ENDING_ERROR"
    assert "a.bin" not in reliability.semantic_candidate_paths(classifications)

    debt_untouched = reliability.classify_byte_surfaces(
        path="debt.py",
        baseline_bytes=b"old\r\n",
        index_bytes=b"old\r\n",
        worktree_bytes=b"old\r\n",
        git_status_state="CLEAN",
        authorized=True,
    )
    missing_lf_debt_untouched = reliability.classify_byte_surfaces(
        path="missing-lf-debt.py",
        baseline_bytes=b"old",
        index_bytes=b"old",
        worktree_bytes=b"old",
        git_status_state="CLEAN",
        authorized=True,
    )
    dirty_crlf_debt = reliability.classify_byte_surfaces(
        path="dirty-crlf-debt.py",
        baseline_bytes=b"old\r\n",
        index_bytes=b"old\n",
        worktree_bytes=b"old\n",
        git_status_state="DIRTY",
        authorized=True,
    )
    dirty_missing_lf_debt = reliability.classify_byte_surfaces(
        path="dirty-missing-lf-debt.py",
        baseline_bytes=b"old",
        index_bytes=b"old\n",
        worktree_bytes=b"old\n",
        git_status_state="DIRTY",
        authorized=True,
    )
    debt_resolved = reliability.classify_byte_surfaces(
        path="debt.py",
        baseline_bytes=b"old\r\n",
        index_bytes=b"new\n",
        worktree_bytes=b"new\n",
        authorized=True,
    )
    assert debt_untouched.change_class == "LATENT_BASELINE_REPRESENTATION_DEBT"
    assert debt_untouched.representation_debt_resolution_state == "PRESERVE_BYTES"
    assert debt_untouched.publication_cleanliness_state == "CLEAN_PRESERVE_BYTES"
    assert reliability.text_integrity_failure_codes((debt_untouched,)) == ()
    assert reliability.semantic_candidate_paths((debt_untouched,)) == ()
    assert missing_lf_debt_untouched.change_class == (
        "LATENT_BASELINE_REPRESENTATION_DEBT"
    )
    assert missing_lf_debt_untouched.representation_debt_resolution_state == (
        "PRESERVE_BYTES"
    )
    assert missing_lf_debt_untouched.publication_cleanliness_state == (
        "CLEAN_PRESERVE_BYTES"
    )
    assert reliability.text_integrity_failure_codes(
        (missing_lf_debt_untouched,)
    ) == ()
    assert reliability.semantic_candidate_paths((missing_lf_debt_untouched,)) == ()
    for dirty_debt in (dirty_crlf_debt, dirty_missing_lf_debt):
        assert dirty_debt.change_class == "LATENT_BASELINE_REPRESENTATION_DEBT"
        assert dirty_debt.semantic_scope_member is False
        assert dirty_debt.publication_cleanliness_state == "DIRTY_MUST_BE_RESOLVED"
        assert reliability.text_integrity_failure_codes((dirty_debt,)) == (
            "ENGVR_UNRELATED_TEXT_REPRESENTATION_DRIFT",
        )
        assert reliability.semantic_candidate_paths((dirty_debt,)) == ()
    assert debt_resolved.change_class == "SEMANTIC_TEXT_CHANGE"
    assert debt_resolved.representation_debt_resolution_state == (
        "RESOLVED_WITH_INDEPENDENT_SEMANTIC_EDIT"
    )
    for anomalous in (b"a\r\nb\n", b"a\rb", b"\xff", b"a\x00"):
        anomaly = reliability.classify_byte_surfaces(
            path="anomaly.py",
            baseline_bytes=anomalous,
            index_bytes=anomalous,
            worktree_bytes=anomalous,
            git_status_state="CLEAN",
            authorized=True,
        )
        assert anomaly.change_class == "PREEXISTING_BASELINE_TEXT_ANOMALY"

    split_profile = reliability.scan_text_stream(io.BytesIO(b"a\r\nb\r\n"), chunk_size=2)
    assert split_profile.crlf_count == 2
    assert split_profile.standalone_lf_count == 0
    large_payload = (b"controlled line\n" * 200_000)

    class BoundedReadStream(io.BytesIO):
        largest_read = 0

        def read(self, size=-1):
            assert 0 < size <= 4096
            self.largest_read = max(self.largest_read, size)
            return super().read(size)

    large_stream = BoundedReadStream(large_payload)
    large_profile = reliability.scan_text_stream(large_stream, chunk_size=4096)
    assert large_profile.byte_count == len(large_payload)
    assert large_stream.largest_read == 4096
    assert reliability.normalize_text_bytes_for_comparison(b"old\n") != (
        reliability.normalize_text_bytes_for_comparison(b"new \r\n")
    )

    blob_refs = []
    with monkeypatch.context() as baseline_patch:
        baseline_patch.setattr(
            reliability,
            "resolve_verified_baseline",
            lambda _root: "merge-base",
        )
        baseline_patch.setattr(
            reliability,
            "_worktree_index_stat_paths",
            lambda _root: (),
        )
        baseline_patch.setattr(reliability, "_status_paths", lambda _root: ())
        baseline_patch.setattr(
            reliability,
            "_diff_path_states",
            lambda _root, _baseline, **_kwargs: {"proof.py": "EXISTING"},
        )

        def fake_blob(_root, ref, _path):
            blob_refs.append(ref)
            payload = b"base\n" if ref == "merge-base" else b"index\n"
            return reliability._bytes_source(
                payload,
                description=f"{ref}:proof.py",
            )

        baseline_patch.setattr(reliability, "_git_blob_source", fake_blob)
        baseline_patch.setattr(
            reliability,
            "_git_exact_path_modes",
            lambda _root, _baseline, _path: ("100644", "100644"),
        )
        baseline_patch.setattr(
            reliability,
            "_git_attributes",
            lambda _root, _path: ("set", "lf"),
        )
        baseline_patch.setattr(
            reliability,
            "_git_exact_path_status_state",
            lambda _root, _path: "DIRTY",
        )
        baseline_patch.setattr(
            reliability,
            "_git_exact_path_diff_state",
            lambda _root, _path, *, baseline_ref, staged: (
                "DIRTY" if staged else "CLEAN"
            ),
        )
        baseline_proof = reliability.classify_repository_changes(
            tmp_path,
            authorized_paths=("proof.py",),
        )
    assert baseline_proof[0].change_class == "SEMANTIC_TEXT_CHANGE"
    assert blob_refs == ["merge-base", "INDEX"]
    assert (
        reliability.classify_byte_surfaces(
            path="precedence.py",
            baseline_bytes=b"a\n",
            index_bytes=b"a\r\nb\n",
            worktree_bytes=b"a\r\nb\n",
            authorized=True,
        ).change_class
        == "MIXED_LINE_ENDING_ERROR"
    )
    _assert_repository_stream_classifier_matrix(monkeypatch, tmp_path)
    _assert_exact_stat_refresh_matrix(monkeypatch, tmp_path)
    _assert_no_follow_worktree_surface_contract(monkeypatch, tmp_path)
    _assert_runtime_artifact_semantic_scope_contract(monkeypatch, inventory)


def test_missing_idempotence_test_classification_fails():
    inventory = _inventory()
    removed = inventory["idempotence_tests"].pop()

    failures = _validate(inventory)

    assert validator.Failure(
        "UNCLASSIFIED_IDEMPOTENCE_TEST", (("path", removed["path"]),)
    ) in failures


def test_default_ci_verify_idempotent_fails_unless_lightweight_and_budgeted():
    inventory = _inventory()
    path = inventory["idempotence_tests"][0]["path"]
    discovered = _discovered_with(path, has_verify_idempotent=True)
    pytest_membership = {path: inventory["idempotence_tests"][0]["pytest_shard"]}

    failures = _validate(
        inventory,
        discovered_idempotence=discovered,
        pytest_membership=pytest_membership,
    )

    assert "DEFAULT_CI_EXHAUSTIVE_VERIFY_IDEMPOTENT" in _codes(failures)


def test_builder_twice_default_ci_without_bounded_contract_fails():
    inventory = _inventory()
    path = (
        "tests/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/test_pr166_sm_idempotence.py"
    )
    discovered = _discovered_with(path, builder_twice=True, bounded_contract=False)
    pytest_membership = {path: "pytest-shard-4"}

    failures = _validate(
        inventory,
        discovered_idempotence=discovered,
        pytest_membership=pytest_membership,
    )

    assert "BUILDER_TWICE_UNBOUNDED_DEFAULT_CI" in _codes(failures)


def test_missing_shard_8_fails():
    inventory = _inventory()
    inventory["pytest_shards"] = [
        entry
        for entry in inventory["pytest_shards"]
        if entry["phase"] != "pytest-shard-8"
    ]

    failures = _validate(inventory)

    assert validator.Failure("MISSING_PYTEST_SHARD", (("shard", "pytest-shard-8"),)) in failures


def test_failed_or_cancelled_shard_not_aggregated_fails():
    inventory = _inventory()
    workflow_text = WORKFLOW_TEXT.replace("          - phase: pytest-shard-8\n", "")

    failures = _validate(inventory, workflow_text=workflow_text)

    assert "SHARD_NOT_AGGREGATED" in _codes(failures)


def test_non_success_result_guard_removed_fails():
    inventory = _inventory()
    workflow_text = WORKFLOW_TEXT.replace('result != "success"', 'result == "failure"')

    failures = _validate(inventory, workflow_text=workflow_text)

    assert "WORKFLOW_AGGREGATION_NOT_FAIL_CLOSED" in _codes(failures)


def test_tracked_router_runtime_artifact_fails():
    failures = _validate(
        _inventory(),
        tracked_paths=(".tmp/qtt-validation-router/fast-preflight.json",),
    )

    assert "RUNTIME_ARTIFACT_TRACKED" in _codes(failures)


def test_staged_timing_runtime_artifact_fails():
    failures = _validate(
        _inventory(),
        staged_paths=(".tmp/qtt-validation-timing/fast-preflight.json",),
    )

    assert "RUNTIME_ARTIFACT_STAGED" in _codes(failures)


def test_real_source_test_and_generated_files_are_not_runtime_artifacts():
    inventory = _inventory()

    assert not validator.is_runtime_artifact_path("src/qtt/example.py", inventory)
    assert not validator.is_runtime_artifact_path(
        "tests/tools/test_example.py", inventory
    )
    assert not validator.is_runtime_artifact_path(
        "docs/master_plan/generated/PR999_NewReport.report.json", inventory
    )


def test_broad_tmp_runtime_policy_fails():
    inventory = _inventory()
    inventory["runtime_artifact_policy"].append(
        {
            "classification": "RUNTIME_ARTIFACT_IGNORED_IF_UNTRACKED",
            "path_pattern": ".tmp/**",
        }
    )

    failures = _validate(inventory)

    assert "BROAD_TMP_RUNTIME_ARTIFACT_ALLOWLIST" in _codes(failures)


def test_generated_report_payload_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=("docs/master_plan/generated/PR166_Q_New.report.json",),
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_exact_registered_repair_scope_allows_only_current_pr152_report():
    branch = context.ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_BRANCH
    pr152_report = (
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    )

    assert validator._allowed_explicit_roadmap_feature_touch(
        branch,
        pr152_report,
        auto_discovered_changed_paths=True,
    )
    assert validator._validate_changed_files(
        _inventory(),
        (pr152_report,),
        workflow_text=WORKFLOW_TEXT,
        current_branch=branch,
        auto_discovered_changed_paths=True,
    ) == []

    for denied_path in (
        "docs/master_plan/generated/Unrelated.report.json",
        "docs/master_plan/generated/PR208_FinalSummary.report.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/roadmap/generated/Unrelated.report.json",
    ):
        assert not validator._allowed_explicit_roadmap_feature_touch(
            branch,
            denied_path,
            auto_discovered_changed_paths=True,
        )

    for adversarial_branch in (
        branch.upper(),
        f"{branch}-suffix",
        f"{branch}/",
        branch.replace("receipt-closure", "receipts-closure"),
        "repair/st12-unregistered-repair",
    ):
        assert not validator._allowed_explicit_roadmap_feature_touch(
            adversarial_branch,
            pr152_report,
            auto_discovered_changed_paths=True,
        )


def test_master_plan_content_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=("docs/master_plan/QTT_MasterPlan_Current.md",),
    )

    assert "FORBIDDEN_MASTER_PLAN_CHANGE" in _codes(failures)


def test_pr166_q_business_file_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=(
            "src/qtt/stage1_prediction_markets/pr166_q_quantum_next/logic.py",
        ),
    )

    assert "FORBIDDEN_PR166_Q_BUSINESS_CHANGE" in _codes(failures)


def test_pr166_q_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
            "docs/master_plan/generated/pr166_q_shards/"
            "PR166_Q_QuantumStructuralReadiness.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/report_writer.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-q-quantum-classical-hybrid-comparator",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr166_q_github_pr_merge_ref_auto_discovered_changes_are_allowed(
    monkeypatch,
):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/222/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "222/merge")
    monkeypatch.setenv(
        "GITHUB_HEAD_REF",
        "pr166-q-quantum-classical-hybrid-comparator",
    )
    monkeypatch.setattr(
        validator,
        "_changed_paths",
        lambda _repo_root: (
            "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/validator.py",
            "tests/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/"
            "test_pr166_q_validator.py",
        ),
    )
    monkeypatch.setattr(validator, "_tracked_paths", lambda _repo_root: ())
    monkeypatch.setattr(validator, "_staged_paths", lambda _repo_root: ())

    failures = validator.validate(
        REPO_ROOT,
        inventory=_inventory(),
        workflow_text=WORKFLOW_TEXT,
    )

    assert "FORBIDDEN_PR166_Q_BUSINESS_CHANGE" not in _codes(failures)
    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" not in _codes(failures)


def test_pr166_q_branch_scoped_exception_does_not_allow_master_plan():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/QTT_MasterPlan_Current.md",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-q-quantum-classical-hybrid-comparator",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_MASTER_PLAN_CHANGE" in _codes(failures)


def test_pr168_rp5e_shared_receipt_currentization_is_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
            "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
            "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rp5e-stack-gen",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" not in _codes(failures)


def test_pr168_rp5f_pr152_currentization_is_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
            "tools/validate_pr168_rp5f_dynamic_targets.py",
            "tests/pr168_rp5f/test_validation.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rp5f-dynamic-target-order-grid",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" not in _codes(failures)


def test_pr166_qb_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR166_QB_FinalSummary.report.json",
            "docs/master_plan/generated/pr166_qb_shards/"
            "PR166_QB_RaceArb.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_qb_bounded_quantum_benchmark/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr166_qb_bounded_quantum_benchmark/test_pr166_qb_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qb-bounded-nonlive-quantum-optimizer-benchmark",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr166_qb_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_Q_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qb-bounded-nonlive-quantum-optimizer-benchmark",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr166_qc_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR166_QC_FinalSummary.report.json",
            "docs/master_plan/generated/pr166_qc_shards/"
            "PR166_QC_ReplayEvidence.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_qc_quantum_selected_replay_paper_retest/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qc-quantum-selected-replay-paper-retest",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr166_qc_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_QB_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qc-quantum-selected-replay-paper-retest",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr162e_q_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR162E_Q_FinalSummary.report.json",
            "docs/master_plan/generated/pr162e_q_shards/"
            "PR162E_Q_MapEligibility.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr162e_q_quantum_automapper/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr162e_q_quantum_automapper/test_pr162e_q_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-q-quantum-automapper",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr162e_q_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_QC_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-q-quantum-automapper",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr162e_plugin_framework_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR162E_FinalSummary.report.json",
            "docs/master_plan/generated/PR162E_PluginRegistry.report.json",
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr162e_plugin_framework/report_writer.py",
            "src/qtt/plugins/contracts.py",
            "tests/pr162e/test_pr162e_plugin_abi.py",
            "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-plugin-framework",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr162e_plugin_framework_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR167_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-plugin-framework",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr167_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR167_FinalSummary.report.json",
            "docs/master_plan/generated/pr167_shards/"
            "PR167_SimEligibility.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr167_open_trade_simulator_integration/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr167_open_trade_simulator_integration/test_pr167_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr167-open-trade-simulator-integration",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr167_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_QC_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr167-open-trade-simulator-integration",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr168_rank_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR168_RANK_FinalSummary.report.json",
            "docs/master_plan/generated/pr168_rank_shards/"
            "PR168_RANK_EvidenceBackedRanking.part_0001_of_0001.report.json",
            "tools/pr168_rank_compute_kernel.py",
            "tools/validate_pr168_rank_input_consumption.py",
            "tests/pr168_rank/test_input_consumption.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rank-evidence-backed-ranking",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr168_rank_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR168_RP_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rank-evidence-backed-ranking",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr165_d3_business_file_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=(
            "src/qtt/stage1_prediction_markets/"
            "pr165_d3_quantum_aware_scenario_selection_v3/report_writer.py",
        ),
    )

    assert "FORBIDDEN_PR165_D3_BUSINESS_CHANGE" in _codes(failures)


def test_sparse_checkout_profile_addition_is_rejected_when_main_checkout_green():
    failures = _validate(
        _inventory(),
        changed_paths=(".github/sparse-checkout/runtime-profile.txt",),
    )

    assert "SPARSE_CHECKOUT_EXPERIMENT_BLOCKED" in _codes(failures)


def test_removed_inventory_path_fails_unless_removed_with_reason():
    inventory = _inventory()
    inventory["manual_nightly_exhaustive_paths"].append(
        {
            "classification": "MANUAL_NIGHTLY_EXHAUSTIVE_IDEMPOTENCE",
            "path": "tools/build_removed_exhaustive.py",
        }
    )

    failures = _validate(inventory)

    assert "STALE_INVENTORY_ENTRY" in _codes(failures)

    inventory["manual_nightly_exhaustive_paths"][-1][
        "removed_with_reason"
    ] = "synthetic removed path for staleness test"
    failures = _validate(inventory)

    assert "STALE_INVENTORY_ENTRY" not in _codes(failures)


def test_newly_discovered_idempotence_file_missing_from_inventory_fails():
    inventory = _inventory()
    discovered = tuple(validator.discover_idempotence_tests(REPO_ROOT)) + (
        validator.DiscoveredIdempotence(
            path="tests/stage1_prediction_markets/pr999/test_new_idempotence.py",
            has_verify_idempotent=False,
            builder_twice=True,
            bounded_contract=False,
        ),
    )

    failures = _validate(inventory, discovered_idempotence=discovered)

    assert "UNCLASSIFIED_IDEMPOTENCE_TEST" in _codes(failures)


def test_renamed_pytest_shard_not_reflected_in_inventory_fails():
    inventory = _inventory()
    for entry in inventory["pytest_shards"]:
        if entry["phase"] == "pytest-shard-8":
            entry["phase"] = "pytest-shard-eight"

    failures = _validate(inventory)

    assert "MISSING_PYTEST_SHARD" in _codes(failures)


def test_unknown_workflow_job_missing_classification_fails():
    inventory = _inventory()
    workflow_text = WORKFLOW_TEXT + "\n  surprise_job:\n    name: Surprise Job\n"

    failures = _validate(inventory, workflow_text=workflow_text)

    assert validator.Failure(
        "UNCLASSIFIED_WORKFLOW_JOB", (("job", "surprise_job"),)
    ) in failures
