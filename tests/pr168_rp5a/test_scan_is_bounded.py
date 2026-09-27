import shutil
import subprocess

import pytest

from tools.pr168_rp5a_config import (
    MAX_CONSUMER_REFS_PER_FILE,
    MAX_FILES_SCANNED,
    MAX_IDENTITY_REFS_PER_FILE,
    MAX_LINE_HITS_PER_FILE,
    MAX_MATCHED_FILES,
    MAX_STRUCTURED_JSON_BYTES,
    MAX_TOTAL_LINE_HITS,
    MAX_TOTAL_ROWS_PER_SHARD,
    MAX_WALL_SECONDS,
)
from tools import pr168_rp5a_git_grep_scanner as scanner
from tests.pr168_rp5a._helpers import file_rows, load_report, load_rows


def test_scan_is_bounded() -> None:
    report = load_report("PR168_RP5A_ScanPerformance.report.json")
    consumer_rows = load_rows("consumer_graph_rows")

    assert report["peak_memory_strategy"] in {
        "RG_TEMP_FILE_TWO_PASS_BOUNDED_HITS",
        "GIT_GREP_TEMP_FILE_TWO_PASS_BOUNDED_HITS",
        "PYTHON_FALLBACK_STREAMING_BOUNDED_LINE_SCAN",
    }
    assert report["consumer_graph_scan_mode"] == "BOUNDED_STATUS_ONLY_NO_ALL_PAIRS"
    assert sum(
        bool(report.get(flag))
        for flag in ("rg_used_flag", "git_grep_used_flag", "python_fallback_used_flag")
    ) == 1
    assert report["quick_selftest_flag"] is False
    assert report["scan_budget_status"] in {"SCAN_BUDGET_OK", "SCAN_BUDGET_EXHAUSTED"}
    assert report["max_wall_seconds"] == MAX_WALL_SECONDS
    assert report["max_files_scanned"] == MAX_FILES_SCANNED
    assert report["max_matched_files"] == MAX_MATCHED_FILES
    assert report["max_line_hits_per_file"] == MAX_LINE_HITS_PER_FILE
    assert report["max_total_line_hits"] == MAX_TOTAL_LINE_HITS
    assert report["max_consumer_refs_per_file"] == MAX_CONSUMER_REFS_PER_FILE
    assert report["max_identity_refs_per_file"] == MAX_IDENTITY_REFS_PER_FILE
    assert report["max_structured_json_bytes"] == MAX_STRUCTURED_JSON_BYTES
    assert report["max_total_rows_per_shard"] == MAX_TOTAL_ROWS_PER_SHARD
    assert report["checkpoint_path"] == ".tmp/rp5a_scan_checkpoint.json"
    assert report["checkpoint_committed_flag"] is False
    assert report["matched_files_count"] == len(file_rows())
    assert len(consumer_rows) == len(file_rows())
    assert all(
        row["consumer_strength"] != "DIRECT_PATH_READ"
        or len(row.get("consumer_examples_limited", [])) <= MAX_CONSUMER_REFS_PER_FILE
        for row in consumer_rows
    )


def test_scan_falls_back_when_rg_is_unavailable(monkeypatch, tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("formula repair should be audited only\n", encoding="utf-8")

    monkeypatch.setattr(scanner.shutil, "which", lambda _name: None)

    rows, index, stats = scanner.scan_files_for_terms(
        ["sample.txt"],
        tmp_path,
        max_wall_seconds=60,
        max_files_scanned=10,
        max_total_line_hits=10,
        progress_interval_seconds=999999,
    )

    assert stats["rg_used_flag"] is False
    assert stats["python_fallback_used_flag"] is True
    assert 1 <= len(rows) <= 10
    assert list(index) == ["sample.txt"]
    _exercise_v35_scan_wire_and_limits(monkeypatch, tmp_path)
    _exercise_v35_rp5a_reader_transport_v1(monkeypatch, tmp_path)


def test_scan_uses_git_grep_when_rg_is_unavailable(monkeypatch, tmp_path) -> None:
    git_path = shutil.which("git")
    if git_path is None:
        pytest.skip("git is required for git-grep fallback")
    sample = tmp_path / "sample.txt"
    sample.write_text("formula repair should be audited only\n", encoding="utf-8")
    subprocess.run([git_path, "init"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([git_path, "add", "sample.txt"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def fake_which(name: str) -> str | None:
        if name == "rg":
            return None
        if name == "git":
            return git_path
        return None

    monkeypatch.setattr(scanner.shutil, "which", fake_which)

    # Synthetic fixture grants only this toy repository and these three calls.
    from pathlib import Path
    from tools.validation_reliability import _Rp5aScanProfile, _ScanCandidateFence, _ScanCandidateSurface, _ScanRunReadLimits
    import os
    import stat
    import time

    scratch = tmp_path / "native-scan-scratch"
    scratch.mkdir()
    original = sample.read_bytes()
    deadline = time.monotonic_ns() + 60_000_000_000
    limits = _ScanRunReadLimits(100_000, 1_000, 16, 1)
    fence = _ScanCandidateFence(
        tmp_path, (_ScanCandidateSurface("sample.txt", "FILE", stat.S_IMODE(sample.stat().st_mode), original, ()),),
        limits=limits, candidate_read_bytes=100_000, deadline_ns=deadline)
    executable = str(Path(git_path).resolve())
    profile = _Rp5aScanProfile(
        "synthetic-native-scan", 1, str(tmp_path), str(scratch), ("sample.txt",), 1, len(b"sample.txt\0"),
        (("sample.txt", len(original)),), executable, executable, "git",
        tuple(scanner._scan_child_environment(os.environ).items()), 100_000, 100_000, 4096, 100_000, deadline, 3)
    context = scanner._ScanInvocation(profile, check_candidate=fence)
    assert scanner.scannable_files(tmp_path, scan_context=context) == ["sample.txt"]

    rows, index, stats = scanner.scan_files_for_terms(
        ["sample.txt"],
        tmp_path,
        max_wall_seconds=60,
        max_files_scanned=10,
        max_total_line_hits=10,
        progress_interval_seconds=999999,
        scan_context=context,
    )

    assert stats["rg_used_flag"] is False
    assert stats["git_grep_used_flag"] is True
    assert stats["python_fallback_used_flag"] is False
    assert 1 <= len(rows) <= 10
    assert list(index) == ["sample.txt"]

    assert context.controller.state == "DONE"
    assert context.ledger.invocations == 3
    assert context.ledger.spent_output >= context.ledger.spent_readback > 0
    assert list(scratch.iterdir()) == []


def _exercise_v35_scan_wire_and_limits(monkeypatch, tmp_path):
    import io
    import re
    from tools import pr168_rp5a_json_scanner as structured
    from tools import pr168_rp5a_term_taxonomy as taxonomy
    from tools import build_pr168_rp5a_legacy_semantic_audit as builder

    names = ("a.txt", "b.txt")
    assert scanner._scan_parse_names((b"b.txt\0a.txt\0",), batch=names, exit_code=0) == names
    assert scanner._scan_parse_names((), batch=names, exit_code=1) == ()
    assert scanner._scan_parse_names((), batch=(), exit_code=0, inventory=True) == ()
    for wire, status in ((b"a.txt", 0), (b"a.txt\0a.txt\0", 0), (b"x.txt\0", 0),
                         (b"a.txt\0", 1), (b"", 0), (b"a.txt\0", True), (b"", 2)):
        with pytest.raises(ValueError):
            scanner._scan_parse_names((wire,) if wire else (), batch=names, exit_code=status)
    expected = (("a.txt", 1, b"formula repair"),)
    sizes = {"a.txt": len(b"formula repair\n")}
    for engine, raw in (("git", b"a.txt\x001\x00formula repair\n"), ("rg", b"a.txt\x001:formula repair\n")):
        assert scanner._scan_parse_lines((bytes([value]) for value in raw), batch=("a.txt",), sizes=sizes,
                                         engine=engine, exit_code=0) == expected
        for malformed in (raw[:-1], raw.replace(b"1", b"01", 1), raw + raw,
                          raw.replace(b"a.txt", b"x.txt", 1)):
            with pytest.raises(ValueError):
                scanner._scan_parse_lines((malformed,), batch=("a.txt",), sizes=sizes, engine=engine, exit_code=0)
    for name in ("../x", "/x", "a//b", "a/./b", "a/../b", ".git/index", "a\0b"):
        with pytest.raises(ValueError):
            scanner._scan_path_identity(name)
    for name in ("file:stream", "con.txt", "LPT?", "trailing.", "trailing "):
        with pytest.raises(ValueError):
            scanner._scan_path_identity(name, platform_name="nt")
    assert scanner._scan_path_identity(" leading : name ", platform_name="posix") == " leading : name "
    with pytest.raises(ValueError):
        scanner._scan_admitted_paths(("A.txt", "a.txt"), path_limit=2, byte_limit=20, platform_name="nt")
    with pytest.raises(ValueError):
        scanner._scan_admitted_paths(("?",), path_limit=1, byte_limit=2)

    class NoConversion:
        def __str__(self):
            raise AssertionError("zero allowance converted text")
    assert taxonomy.match_text(NoConversion(), max_matches=0) == []
    corpus = "formula repair / Formula Repair / no trade dominated formula / notrade negative QKU / source truth"
    independent = []
    seen = set()
    for spec in scanner.TERM_TAXONOMY:
        expression = spec.term_text_or_regex if spec.is_regex else re.escape(spec.term_text_or_regex)
        for match in re.finditer(expression, corpus, re.IGNORECASE):
            value = match.group(0)
            key = spec.term_id, value.lower()
            if key not in seen:
                seen.add(key)
                independent.append((spec.term_id, value))
    assert [(row["term_id"], row["matched_text"]) for row in taxonomy.match_text(corpus)] == independent
    for count in range(len(independent) + 1):
        assert [(row["term_id"], row["matched_text"]) for row in taxonomy.match_text(corpus, max_matches=count)] == independent[:count]
    assert scanner._line_may_match("notrade negative QKU") is True
    assert scanner._line_may_match("\u017fource truth") is True

    # Literal Windows names from R5 9.3.20; no filesystem/device operation.
    from types import SimpleNamespace
    from tools import validation_reliability as validation_owner
    with monkeypatch.context() as windows_text_case:
        windows_text_case.setattr(validation_owner, "os", SimpleNamespace(name="nt"))
        for suffix in ("\u00b9", "\u00b2", "\u00b3"):
            for prefix in ("COM", "LPT"):
                for extension in ("", ".txt"):
                    device_name = prefix + suffix + extension
                    with pytest.raises(ValueError):
                        scanner._scan_path_identity(device_name, platform_name="nt")
                    with pytest.raises(ValueError):
                        validation_owner._scan_candidate_path(device_name)
                    assert scanner._scan_path_identity(device_name, platform_name="posix") == device_name
    # U+00E9 is two UTF-8 bytes plus the independently required separator byte.
    with pytest.raises(ValueError, match="UTF-8 allowance exceeded"):
        scanner._scan_admitted_paths(("\u00e9",), path_limit=1, byte_limit=2, platform_name="posix")
    assert scanner._scan_admitted_paths(("\u00e9",), path_limit=1, byte_limit=3,
                                        platform_name="posix") == ("\u00e9",)
    unicode_triggers = ("\u0130", "\u0131", "\u017f", "\u212a")
    assert all(value in scanner._pass_a_fixed_patterns_tuple() for value in unicode_triggers)
    assert "?" not in scanner._pass_a_fixed_patterns_tuple()
    for counterexample in ("champ\u0131on", "L\u0130VE_CAND\u0130DATE", "\u212aKU"):
        assert scanner._line_may_match(counterexample) is True

    class ReadPath:
        def __init__(self, stream):
            self.stream = stream
        def open(self, mode):
            assert mode == "rb"
            return self.stream
    class Short(io.BytesIO):
        def read(self, count=-1):
            return super().read(min(count, 2))
    with monkeypatch.context() as patch:
        patch.setattr(structured, "MAX_STRUCTURED_JSON_BYTES", 6)
        assert structured._read_structured_text(ReadPath(Short(b"abcdef")), errors="strict") == "abcdef"
        with pytest.raises(ValueError):
            structured._read_structured_text(ReadPath(Short(b"abcdefg")), errors="strict")
        for returned in (None, "text", b"01234567"):
            class InvalidRead:
                def read(self, _count):
                    return returned
                def close(self):
                    pass
            with pytest.raises(ValueError):
                structured._read_structured_text(ReadPath(InvalidRead()), errors="strict")
    read_error = OSError("original read")
    close_error = OSError("original close")
    class Broken:
        def read(self, _count):
            raise read_error
        def close(self):
            raise close_error
    with pytest.raises(BaseExceptionGroup) as raised:
        structured._read_structured_text(ReadPath(Broken()), errors="strict")
    assert raised.value.exceptions == (read_error, close_error)

    complete = {"scan_budget_status": "SCAN_BUDGET_OK", "budget_exhausted_flag": False, "budget_exhaustion_reasons": []}
    incomplete = builder._merge_scan_incompleteness(complete, selection_incomplete=True,
        row_field_stats={"row_field_budget_exhausted_flag": True, "skipped_large_structured_file_count": 1})
    assert incomplete["budget_exhaustion_reasons"] == ["MAX_FILES_SCANNED", "ROW_FIELD_MATCH_LIMIT", "STRUCTURED_SIZE_LIMIT"]
    assert complete["budget_exhaustion_reasons"] == [] and complete["budget_exhausted_flag"] is False
    assert incomplete["budget_exhausted_flag"] is True
    for broken in ({**complete, "budget_exhausted_flag": 1}, {**complete, "scan_budget_status": "SCAN_BUDGET_EXHAUSTED"}):
        with pytest.raises(ValueError):
            builder._merge_scan_incompleteness(broken)

def _exercise_v35_rp5a_reader_transport_v1(monkeypatch, tmp_path):
    # All operands below are finite synthetic test data, never owner-repository
    # admission. Expected wire fields and role decisions are independent literals.
    import dataclasses
    import json
    import os
    from pathlib import Path
    import stat
    import sys
    import time
    from types import MappingProxyType
    from tools import validation_reliability as owner
    from tools import build_pr168_rp5a_legacy_semantic_audit as builder
    from tools import run_validation_gates as gates
    from tools import run_pytest_fresh_basetemp as wrapper

    root = tmp_path / "reader-protocol-repo"
    root.mkdir()
    (root / "tools").mkdir()
    historical = b"# finite historical runner source data\n"
    for name in ("run_validation_gates.py", "validation_scope_registry.py"):
        (root / "tools" / name).write_bytes(historical)
    basis_values = dict(baseline_ref="1" * 40, historical_runner_bytes=historical,
        stdout_bytes_per_call=4096, status_record_limit=8, path_byte_limit=128,
        source_byte_limit=4096, manifest_node_limit=1000,
        manifest_command_limit=100, manifest_argument_limit=1000)
    basis = owner._Rp5aReadBasisV1(**basis_values)
    for key in tuple(basis_values)[2:]:
        for invalid in (None, False, True, 0, -1, 1.0, "1"):
            with pytest.raises((TypeError, ValueError)):
                owner._Rp5aReadBasisV1(**{**basis_values, key: invalid})
    for invalid in ("main", "A" * 40, "", None):
        with pytest.raises(ValueError):
            owner._Rp5aReadBasisV1(**{**basis_values, "baseline_ref": invalid})
    for invalid in (bytearray(historical), b"x" * 4097, b""):
        with pytest.raises(ValueError):
            owner._Rp5aReadBasisV1(**{**basis_values, "historical_runner_bytes": invalid})
    with pytest.raises(dataclasses.FrozenInstanceError):
        basis.source_byte_limit = 8192
    limits = owner._ScanRunReadLimits(100000, 10000, 32, 3)
    deadline = time.monotonic_ns() + 120_000_000_000
    direct = owner._ScanLaunchIdentity("synthetic-reader", "outer", 2, 3,
        (sys.executable, "tools/validate_pr168_rp5a_legacy_semantic_audit.py"), str(root))
    rows = tuple(owner._ScanCandidateSurface("tools/" + name, "FILE",
        stat.S_IMODE((root / "tools" / name).stat().st_mode), historical, ())
        for name in ("run_validation_gates.py", "validation_scope_registry.py"))
    old = {"run_id": "synthetic-reader", "phase": "outer", "command_index": 2, "command_count": 3,
           "argv": list(direct.argv), "repo_root": str(root),
           "candidate_files": [[row.path, "FILE", row.mode, historical.hex(), []] for row in rows],
           "candidate_read_bytes": 100000}
    basis_wire = {**basis_values, "historical_runner_bytes": historical.hex()}
    new = {**old, "wire_version": 2, "rp5a_read_basis": basis_wire, "parent_identity": None}
    def encoded(value):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    for wire, version in ((old, 1), (new, 2)):
        payload = owner._scan_launch_payload(direct, rows, limits=limits, candidate_read_bytes=100000,
            **({"rp5a_read_basis": basis} if version == 2 else {}))
        emitted = b"".join(owner._scan_launch_parts(payload))
        assert emitted == encoded(wire)
        assert owner._scan_launch_measure(payload, limits=limits) == len(emitted)
    parent = dataclasses.replace(direct, command_index=3,
        argv=(sys.executable, "tools/run_pytest_fresh_basetemp.py", "tests/pr168_rp5a"))
    nested = owner._ScanLaunchIdentity(direct.run_id, "nested-pytest", 1, 1,
        (sys.executable, "-B", "-c", wrapper._RP5A_PYTEST_BOOTSTRAP_V1), str(root))
    nested_payload = owner._scan_launch_payload(nested, rows, limits=limits,
        candidate_read_bytes=100000, rp5a_read_basis=basis, parent_identity=parent)
    nested_wire = {**new, "phase": "nested-pytest", "command_index": 1, "command_count": 1,
                   "argv": list(nested.argv), "parent_identity": {
                       "run_id": parent.run_id, "phase": parent.phase, "command_index": 3,
                       "command_count": 3, "argv": list(parent.argv), "repo_root": str(root)}}
    assert b"".join(owner._scan_launch_parts(nested_payload)) == encoded(nested_wire)
    assert owner._scan_launch_measure(nested_payload, limits=limits) == len(encoded(nested_wire))
    for payload in (None, MappingProxyType({"nested": owner._scan_launch_payload(
            direct, rows, limits=limits, candidate_read_bytes=100000, rp5a_read_basis=basis)})):
        with pytest.raises((TypeError, ValueError)):
            owner._scan_launch_measure(payload, limits=limits)
        with pytest.raises((TypeError, ValueError)):
            b"".join(owner._scan_launch_parts(payload))
    with pytest.raises(ValueError):
        owner._scan_launch_payload(direct, rows, limits=limits, candidate_read_bytes=100000, parent_identity=parent)

    serial = 0
    def decode(raw, version=2, identity=direct, expected_basis=basis, expected_parent=None, start=0):
        nonlocal serial
        path = tmp_path / ("frame-" + str(serial) + ".bin")
        serial += 1
        path.write_bytes(len(raw).to_bytes(4, "big") + raw)
        with path.open("rb", buffering=0) as stream:
            stream.seek(start)
            return owner._read_scan_launch_fd(stream.fileno(), limits=limits, deadline_ns=deadline,
                expected_identity=identity, expected_wire_version=version,
                expected_rp5a_read_basis=expected_basis, expected_parent_identity=expected_parent)
    assert decode(encoded(old), 1, expected_basis=None) == (direct, rows, 100000)
    assert decode(encoded(new)) == (direct, rows, 100000, basis, None)
    assert decode(encoded(nested_wire), identity=nested, expected_parent=parent) == (nested, rows, 100000, basis, parent)
    malformed = [
        {**new, "extra": 1}, {k: v for k, v in new.items() if k != "parent_identity"},
        {**new, "wire_version": True}, {**new, "wire_version": 3},
        {**new, "command_index": True}, {**new, "candidate_read_bytes": True},
        {**new, "rp5a_read_basis": {**basis_wire, "source_byte_limit": False}},
        {**new, "rp5a_read_basis": {**basis_wire, "historical_runner_bytes": historical.hex().upper()}},
        {**new, "rp5a_read_basis": {**basis_wire, "baseline_ref": "2" * 40}},
        {**new, "rp5a_read_basis": {**basis_wire, "historical_runner_bytes": b"altered".hex()}},
        {**new, "parent_identity": nested_wire["parent_identity"]},
        {**new, "run_id": "foreign"}, {**new, "phase": "foreign"},
        {**new, "argv": [sys.executable, "unrelated.py"]},
        {**new, "repo_root": str(tmp_path)}, {**new, "candidate_files": None},
    ]
    for value in malformed:
        with pytest.raises((TypeError, ValueError)):
            decode(encoded(value))
    for raw in (encoded(new).replace(b'"wire_version":2', b'"wire_version":2,"wire_version":2'),
                encoded(new).replace(b'"candidate_read_bytes":100000', b'"candidate_read_bytes":NaN')):
        with pytest.raises(ValueError):
            decode(raw)
    for kwargs in ({"version": 1, "expected_basis": None}, {"expected_basis": None},
                   {"version": True}, {"start": 1}, {"expected_parent": parent}):
        with pytest.raises((TypeError, ValueError)):
            decode(encoded(new), **kwargs)

    role_vectors = (
        (("tools/build_pr168_rp5a_legacy_semantic_audit.py", "--offline"), "SCANNER"),
        (("tools/build_pr168_rp5a_legacy_semantic_audit.py", "--validation-scope-evidence-only"), "EVIDENCE"),
        (("tools/validate_pr168_rp5a_legacy_semantic_audit.py",), "VALIDATE"),
        (("tools/run_pytest_fresh_basetemp.py", "-vv", "tests/pr168_rp5a"), "PYTEST"),
        (("-m", "pytest", "tests/pr168_rp5a/test_no_validation_scope_removal.py::test_no_validation_scope_removal"), "PYTEST"),
        (("-m", "pytest", "--ignore", "tests/pr168_rp5a", "tests/pr168_rp5b"), None),
        (("-m", "pytest", "-k", "tests/pr168_rp5a", "tests/pr168_rp5b"), None),
        (("unrelated.py", "tools/build_pr168_rp5a_legacy_semantic_audit.py"), None),
        (("-m", "pytest", "tests/pr168_rp5a_extra"), None),
    )
    for tail, expected in role_vectors:
        assert owner._rp5a_consumer_role_v1((sys.executable, *tail), root) == expected
    with pytest.raises(ValueError):
        builder._require_builder_reads_v1()

    # Real finite native Git, including a genuine nonzero result. The original
    # bounded reader performs the native operations and holds on disagreement.
    git = next((str((Path(folder) / ("git.exe" if os.name == "nt" else "git")).resolve())
                for folder in os.get_exec_path()
                if (Path(folder) / ("git.exe" if os.name == "nt" else "git")).is_file()), None)
    assert git is not None
    setup_env = scanner._scan_child_environment(os.environ)
    for command in ([git, "init", "-q", "-b", "main"],
                    [git, "add", "tools"],
                    [git, "-c", "user.name=Synthetic Reader Test", "-c", "user.email=reader-test@invalid",
                     "commit", "-q", "-m", "synthetic historical source"],
                    [git, "-c", "user.name=Synthetic Reader Test", "-c", "user.email=reader-test@invalid",
                     "commit", "-q", "--allow-empty", "-m", "synthetic current source"]):
        completed = subprocess.run(command, cwd=root, env=setup_env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        assert completed.returncode == 0, completed.stderr
    scratch = tmp_path / "bounded-reader-native"
    scratch.mkdir()
    profile = owner._Rp5aScanProfile("synthetic-reader-native", 1, str(root), str(scratch),
        ("tools/run_validation_gates.py", "tools/validation_scope_registry.py"), 2, 256,
        tuple((row.path, len(row.content)) for row in rows), git, git, "git",
        tuple(setup_env.items()), 1_000_000, 100_000, 4096, 2_000_000, deadline, 30)
    # New reader maps cannot retain mutable aliases, and their ledger cannot
    # become a scanner merely because both roles share the same 18-field type.
    mapped_profile = dataclasses.replace(profile, command_index=2)
    mutable_profiles = {2: mapped_profile}
    mutable_bases = {2: basis}
    immutable_launch = owner._ScanLaunch(None, "outer", (), MappingProxyType({}),
        limits, deadline, os.getpid(), 0,
        reader_profiles=MappingProxyType(mutable_profiles),
        reader_bases=MappingProxyType(mutable_bases))
    mutable_profiles.clear()
    mutable_bases.clear()
    assert tuple(immutable_launch.reader_profiles) == (2,)
    assert tuple(immutable_launch.reader_bases) == (2,)
    assert immutable_launch.reader_profiles[2] is mapped_profile
    assert immutable_launch.reader_bases[2] is basis
    for profiles, bases in (
        ({2: profile}, MappingProxyType({2: basis})),
        (MappingProxyType({2: profile}), {2: basis}),
        (MappingProxyType({True: profile}), MappingProxyType({True: basis})),
        (MappingProxyType({2: profile}), MappingProxyType({})),
    ):
        with pytest.raises((TypeError, ValueError)):
            dataclasses.replace(immutable_launch, reader_profiles=profiles, reader_bases=bases)
    reader_ledger = owner._ScanReservationLedger(profile, reader_only=True)
    with pytest.raises(ValueError):
        owner._ScanPhaseController(profile, reader_ledger, check_candidate=lambda: None,
            max_matched_files=1, structured_byte_limit=4096)
    assert reader_ledger.invocations == 0 and reader_ledger.state == "READY"
    for wrong_role in (None, 0, 1, "reader"):
        with pytest.raises(TypeError):
            owner._ScanReservationLedger(profile, reader_only=wrong_role)
    def context(expected_ref=None, expected_source=historical):
        fence = owner._ScanCandidateFence(root, rows, limits=limits,
            candidate_read_bytes=1_000_000, deadline_ns=deadline)
        return builder._Rp5aBuilderReadContext(ledger=owner._ScanReservationLedger(profile),
            **{key: value for key, value in basis_values.items() if key not in ("baseline_ref", "historical_runner_bytes")},
            expected_historical_source=expected_source, current_runner_source=historical,
            expected_current_runner_source=historical, scope_source=historical,
            expected_scope_source=historical, python_executable=sys.executable,
            check_candidate=fence, before_surfaces=MappingProxyType({}), observe_surfaces=fence.observe_surfaces,
            expected_baseline_ref=expected_ref)
    first = context()
    with monkeypatch.context() as bound_root:
        bound_root.setattr(builder, "REPO_ROOT", root)
        with builder._bind_builder_reads_v1(first):
            baseline, _, _ = builder._validation_scope_baseline()
            assert first.resolved_ref == baseline and len(baseline) in (40, 64)
            assert first.acquire(("cat-file", "blob", baseline + ":tools/run_validation_gates.py"),
                lambda chunks: bytes(scanner._scan_wire_bytes(chunks, 4096))) == historical
        matched = context(baseline)
        with builder._rp5a_bound_reader_v1(matched):
            assert builder._validation_scope_baseline()[0] == baseline
        assert matched.ledger.invocations > 0 and matched.ledger.state == "READY"
        mismatched = context("0" * len(baseline))
        with pytest.raises(RuntimeError, match="BASELINE_RESOLVE_FAILED"):
            with builder._bind_builder_reads_v1(mismatched):
                builder._validation_scope_baseline()
        assert mismatched.resolved_ref is None and mismatched.ledger.state == "HELD"
        failed = context()
        failed.resolved_ref = "0" * len(baseline)
        with pytest.raises(Exception):
            failed.acquire(("cat-file", "blob", failed.resolved_ref + ":tools/run_validation_gates.py"),
                lambda chunks: bytes(scanner._scan_wire_bytes(chunks, 4096)))
        assert failed.ledger.state == "HELD"
        cancellation = KeyboardInterrupt("synthetic cancellation")
        exit_error = ValueError("synthetic exit")
        cancelled = context()
        def rejected_exit():
            raise exit_error
        with pytest.raises(BaseExceptionGroup) as grouped:
            with builder._rp5a_bound_reader_v1(cancelled):
                cancelled.check_candidate = rejected_exit
                raise cancellation
        assert grouped.value.exceptions == (cancellation, exit_error)
        assert cancelled.ledger.state == "HELD"
        with pytest.raises(ValueError):
            builder._require_builder_reads_v1()
    # The source guard independently reads fixed original rows; substitutions
    # and missing source selections are rejected before native Git acquisition.
    fence = owner._ScanCandidateFence(root, rows, limits=limits, candidate_read_bytes=100000, deadline_ns=deadline)
    assert fence.read_original_source("tools/run_validation_gates.py", 4096) == (historical, historical)
    with pytest.raises(ValueError):
        fence.read_original_source("tools/other.py", 4096)
    (root / "tools/run_validation_gates.py").write_bytes(b"altered")
    with pytest.raises(ValueError):
        fence.read_original_source("tools/run_validation_gates.py", 4096)
    assert fence.held is True
