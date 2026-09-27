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

    # Version3 is a synthetic byte/custody matrix after the complete original
    # native scanner prefix. It grants no owner-repository scanner authority.
    import dataclasses
    import json
    import sys
    from types import MappingProxyType, SimpleNamespace
    from tools import validation_reliability as owner
    from tools import build_pr168_rp5a_legacy_semantic_audit as builder

    v3_root = tmp_path / "v3-repository"
    snapshots = tmp_path / "v3-independent-snapshots"
    v3_root.mkdir()
    snapshots.mkdir()
    data = {"binary.bin": b"\x00\xffA\xfe", "\u00e9.bin": b"\r\nB\x80", "empty.bin": b"",
            "chunked.bin": b"\x00\xff\r\n" * 17_000,
            "tools/run_validation_gates.py": b"# finite current runner\n",
            "tools/validation_scope_registry.py": b"# finite current scope\n"}
    carriers = []
    for number, (name, content) in enumerate(data.items()):
        live = v3_root / name
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_bytes(content)
        saved = snapshots / str(number)
        saved.write_bytes(content)
        descriptor = owner._open_regular_worktree_descriptor(saved)
        try:
            version = owner._scan_same_api_version(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        carriers.append(owner._ScanDiskSnapshotV3(name, saved, version,
            owner._scan_file_identity(live.lstat()), stat.S_IMODE(live.lstat().st_mode), len(content)))
    empty_dir = v3_root / "empty-dir"
    empty_dir.mkdir()
    surfaces = tuple(owner._ScanCandidateSurface(c.path, "FILE", c.mode, c, ()) for c in carriers) + (
        owner._ScanCandidateSurface("empty-dir", "DIRECTORY", stat.S_IMODE(empty_dir.stat().st_mode), b"", ()),
        owner._ScanCandidateSurface("absent.bin", "ABSENT", 0, b"", ()))
    total = sum(len(v) for v in data.values())
    deadline3 = time.monotonic_ns() + 180_000_000_000
    limits3 = owner._ScanRunReadLimits(2_000_000, 10_000, 32, 3)
    allowance = 32 * (total + 1)
    basis_values = {"baseline_ref": "1" * 40, "historical_runner_bytes": b"# historical\n",
        "stdout_bytes_per_call": 100_000, "status_record_limit": 20, "path_byte_limit": 512,
        "source_byte_limit": 100_000, "manifest_node_limit": 10_000,
        "manifest_command_limit": 100, "manifest_argument_limit": 1000}
    basis3 = owner._Rp5aReadBasisV1(**basis_values)
    basis_literal = {**basis_values, "historical_runner_bytes": "2320686973746f726963616c0a"}
    identity3 = owner._ScanLaunchIdentity("v3-fixture", "transport-fixture", 1, 1,
        (sys.executable, "-B", "transport_diagnostic.py"), str(v3_root))

    def literal_control(identity, *, version=3, parent=None, entries=None, count=total):
        # Independent test oracle: ordinary literal JSON data, never a production
        # payload/projection helper repackaged as the expected packet.
        if entries is None:
            cursor = 0
            entries = []
            for row in surfaces:
                extent = []
                if row.kind == "FILE":
                    extent = [cursor, len(data[row.path])]
                    cursor += len(data[row.path])
                entries.append([row.path, row.kind, row.mode, extent, list(row.children)])
        result = {"run_id": identity.run_id, "phase": identity.phase, "command_index": identity.command_index,
            "command_count": identity.command_count, "argv": list(identity.argv), "repo_root": identity.repo_root,
            "candidate_files": entries, "candidate_read_bytes": allowance}
        if version != 1:
            result.update(wire_version=version, rp5a_read_basis=dict(basis_literal), parent_identity=parent)
        if version == 3:
            result["payload_byte_count"] = count
        return result

    def literal_packet(control, raw=b""):
        control_bytes = json.dumps(control, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        return len(control_bytes).to_bytes(4, "big") + control_bytes + raw

    original_raw = b"\x00\xffA\xfe\r\nB\x80" + b"\x00\xff\r\n" * 17_000 + b"# finite current runner\n# finite current scope\n"
    assert len(original_raw) == total
    expected_control = literal_control(identity3)
    expected_packet = literal_packet(expected_control, original_raw)
    assert b'"\\u00e9.bin","FILE"' in expected_packet
    assert b'"empty.bin","FILE",' in expected_packet and b'[8,0],[]]' in expected_packet
    assert b'"parent_identity":null,"payload_byte_count":' in expected_packet
    assert expected_packet[4 + int.from_bytes(expected_packet[:4], "big"):] == original_raw
    assert owner._rp5a_consumer_role_v1(identity3.argv, v3_root) is None

    def sender(identity=identity3, *, rows=None, limits=limits3, capacity=None, checks=None):
        rows = surfaces if rows is None else rows
        scratch3 = tmp_path / ("v3-input-" + str(len(tuple(tmp_path.glob("v3-input-*")))))
        scratch3.mkdir()
        fence3 = owner._ScanCandidateFence(v3_root, rows, limits=limits,
            candidate_read_bytes=allowance, deadline_ns=deadline3, wire_version=3,
            surface_role="sender", snapshot_root=snapshots)
        def check():
            if checks is not None:
                checks.append("full-candidate")
            fence3()
        original_input = owner._ScanLaunchInput(identity, rows, limits=limits, candidate_read_bytes=allowance,
            deadline_ns=deadline3, scratch_root=scratch3, scratch_bytes=3_000_000,
            parent_frame_reread_bytes=20_000_000 if capacity is None else capacity,
            check_candidate=check, rp5a_read_basis=basis3, wire_version=3, snapshot_root=snapshots)
        return original_input, fence3

    # Defaults retain exact v1 and v2 representations, including the one hop.
    legacy_rows = (owner._ScanCandidateSurface("binary.bin", "FILE", carriers[0].mode, b"\x00\xffA\xfe", ()),)
    legacy_entry = [["binary.bin", "FILE", carriers[0].mode, "00ff41fe", []]]
    for version in (1, 2):
        literal = literal_control(identity3, version=version, entries=legacy_entry)
        payload = owner._scan_launch_payload(identity3, legacy_rows, limits=limits3, candidate_read_bytes=allowance,
            rp5a_read_basis=None if version == 1 else basis3)
        emitted = b"".join(owner._scan_launch_parts(payload))
        assert emitted == literal_packet(literal)[4:]
        assert owner._scan_launch_measure(payload, limits=limits3) == len(emitted)
    parent_literal = {name: list(getattr(identity3, name)) if name == "argv" else getattr(identity3, name)
                      for name in ("run_id", "phase", "command_index", "command_count", "argv", "repo_root")}
    nested = dataclasses.replace(identity3, phase="nested-pytest", argv=(sys.executable, "-B", "-c", "fixed_fixture"))
    nested_literal = literal_control(nested, version=2, parent=parent_literal, entries=legacy_entry)
    nested_payload = owner._scan_launch_payload(nested, legacy_rows, limits=limits3, candidate_read_bytes=allowance,
        rp5a_read_basis=basis3, parent_identity=identity3)
    assert b"".join(owner._scan_launch_parts(nested_payload)) == literal_packet(nested_literal)[4:]
    assert owner._scan_launch_measure(nested_payload, limits=limits3) == len(literal_packet(nested_literal)) - 4
    for wrong in (None, 0, False, "3", 4):
        if wrong is None:
            with pytest.raises((ValueError, TypeError)):
                owner._scan_launch_payload(identity3, surfaces, limits=limits3, candidate_read_bytes=allowance,
                    rp5a_read_basis=basis3, snapshot_root=snapshots)
        else:
            with pytest.raises((ValueError, TypeError)):
                owner._scan_launch_payload(identity3, surfaces, limits=limits3, candidate_read_bytes=allowance,
                    rp5a_read_basis=basis3, snapshot_root=snapshots, wire_version=wrong)
    for kwargs in ({"parent_identity": identity3}, {"rp5a_read_basis": None}):
        with pytest.raises((ValueError, TypeError)):
            owner._scan_launch_payload(identity3, surfaces, limits=limits3, candidate_read_bytes=allowance,
                wire_version=3, snapshot_root=snapshots, **({"rp5a_read_basis": basis3} | kwargs))

    decoded_paths = []
    def decode_packet(packet, **options):
        name = tmp_path / ("v3-decode-" + str(len(decoded_paths)))
        decoded_paths.append(name)
        name.write_bytes(packet)
        fd = owner._open_regular_worktree_descriptor(name)
        try:
            return owner._read_scan_launch_fd(fd, limits=limits3, deadline_ns=deadline3,
                **({"expected_identity": identity3, "expected_wire_version": 3,
                    "expected_rp5a_read_basis": basis3, "expected_payload_bytes": total} | options))
        finally:
            os.close(fd)

    # Even a metadata-only packet owns a lease and requires a complete check.
    empty_control = literal_control(identity3, entries=[
        ["empty-dir", "DIRECTORY", surfaces[-2].mode, [], []],
        ["absent.bin", "ABSENT", 0, [], []]], count=0)
    empty_decoded = decode_packet(literal_packet(empty_control), expected_payload_bytes=0)
    empty_fence = owner._ScanCandidateFence(v3_root, empty_decoded[1], limits=limits3,
        candidate_read_bytes=allowance, deadline_ns=deadline3, wire_version=3,
        surface_role="receiver", payload_lease=empty_decoded[5])
    assert empty_decoded[5].initial_consumption_complete is False
    empty_fence()
    assert empty_decoded[5].initial_consumption_complete and empty_decoded[5].payload_bytes == 0
    empty_fence.close_payload_lease()
    assert empty_decoded[5].closed

    # Short progress is real bounded file I/O. The simulated process below is
    # explicitly a no-child lifecycle oracle, never native termination proof.
    requested = []
    written_requests = []
    real_read = owner.os.read
    real_fdopen = owner.os.fdopen
    class ShortStream:
        def __init__(self, stream):
            self.stream = stream
        def __getattr__(self, name):
            return getattr(self.stream, name)
        def write(self, value):
            written_requests.append(len(value))
            return self.stream.write(value[:16381])
        def read(self, count):
            requested.append(count)
            return self.stream.read(min(count, 16381))
    def short_read(fd, count):
        requested.append(count)
        return real_read(fd, min(count, 16381))
    counts = []
    transport, _ = sender(checks=counts)
    initial_allowance = transport.remaining_reread
    with monkeypatch.context() as short:
        short.setattr(owner.os, "read", short_read)
        short.setattr(owner.os, "fdopen", lambda *args, **kwargs: ShortStream(real_fdopen(*args, **kwargs)))
        with transport:
            assert transport.path.read_bytes() == expected_packet
            original_stream = transport._claim(run_id=identity3.run_id, phase=identity3.phase,
                command_index=1, argv=identity3.argv, cwd=v3_root)
            process = SimpleNamespace(pid=1234, returncode=None)
            process.poll = lambda: process.returncode
            transport._attached(process)
            identity, received, returned_allowance, original_basis, delegation, lease = owner._read_scan_launch_fd(
                original_stream.fileno(), limits=limits3, deadline_ns=deadline3, expected_identity=identity3,
                expected_wire_version=3, expected_rp5a_read_basis=basis3, expected_payload_bytes=total)
            assert identity == identity3 and original_basis is basis3 and delegation is None
            assert returned_allowance == allowance and lease.initial_consumption_complete is False
            assert all(type(r.content) is owner._ScanPayloadSpanV3 for r in received if r.kind == "FILE")
            child_fence = owner._ScanCandidateFence(v3_root, received, limits=limits3,
                candidate_read_bytes=allowance, deadline_ns=deadline3, wire_version=3,
                surface_role="receiver", payload_lease=lease)
            child_fence()
            assert lease.initial_consumption_complete and original_stream.tell() == transport.extent
            assert child_fence.remaining == allowance - 2 * total
            for source_name in ("tools/run_validation_gates.py", "tools/validation_scope_registry.py"):
                assert child_fence.read_original_source(source_name, 1000) == (data[source_name], data[source_name])
                assert original_stream.tell() == transport.extent
            for source_name, source_limit in (("binary.bin", 1000), ("tools/run_validation_gates.py", 1)):
                with pytest.raises(ValueError):
                    child_fence.read_original_source(source_name, source_limit)
            child_fence.close_payload_lease()
            assert lease.closed and not lease.held
            with pytest.raises(ValueError):
                child_fence.close_payload_lease()
            process.returncode = 7
            transport._finished(process, 7)
            assert transport.state == "CONSUMED"
    assert transport.state == "CLOSED" and not transport.path.exists()
    assert counts == ["full-candidate"] * 3
    expected_reads = total + 3 * (4 + int.from_bytes(expected_packet[:4], "big") + 2 * total)
    assert initial_allowance - transport.remaining_reread == expected_reads
    assert max(requested) <= 65_536 and max(written_requests) <= 65_536
    assert 65_536 in requested and len(written_requests) > 3

    # Closed control/extent matrix, independently altered literal packets.
    malformed = []
    for key in tuple(expected_control):
        value = dict(expected_control);value.pop(key);malformed.append(value)
    malformed += [{**expected_control, "extra": 0}, {**expected_control, "wire_version": 2},
        {**expected_control, "wire_version": True}, {**expected_control, "wire_version": 4},
        {**expected_control, "payload_byte_count": True}, {**expected_control, "payload_byte_count": total + 1},
        {**expected_control, "candidate_read_bytes": False}, {**expected_control, "candidate_read_bytes": -1},
        {**expected_control, "parent_identity": parent_literal}, {**expected_control, "command_index": True},
        {**expected_control, "command_count": 2}, {**expected_control, "run_id": "foreign"},
        {**expected_control, "repo_root": str(tmp_path)}, {**expected_control, "argv": [sys.executable, "foreign.py"]},
        {**expected_control, "rp5a_read_basis": {**basis_literal, "baseline_ref": "2" * 40}}]
    for extent in ([1, 4], [-1, 4], [0, -1], [False, 4], [0, True], [0, 4.0],
                   ["0", 4], [0, 1 << 63], [(1 << 63) - 1, 1], [0], []):
        entries = [list(r) for r in expected_control["candidate_files"]]
        entries[0] = [*entries[0][:3], extent, []]
        malformed.append({**expected_control, "candidate_files": entries})
    for kind in ("DIRECTORY", "ABSENT"):
        entries = [list(r) for r in expected_control["candidate_files"]]
        entries[0] = [entries[0][0], kind, 0, [0, 4], []]
        malformed.append({**expected_control, "candidate_files": entries})
    # Case-only names are aliases under the existing Windows rule, not a
    # universal lexical-path rule on a case-sensitive platform.
    rejected_names = ("binary.bin", "../escape", "a//b")
    if os.name == "nt":
        rejected_names += ("BINARY.BIN",)
    for name in rejected_names:
        entries = [list(r) for r in expected_control["candidate_files"]]
        entries[1] = [name, *entries[1][1:]]
        malformed.append({**expected_control, "candidate_files": entries})
    entries = [list(r) for r in expected_control["candidate_files"]]
    entries[0], entries[1] = entries[1], entries[0]
    malformed.append({**expected_control, "candidate_files": entries})
    for value in malformed:
        with pytest.raises((ValueError, TypeError)):
            decode_packet(literal_packet(value, original_raw))
    if os.name != "nt":
        entries = [list(row) for row in expected_control["candidate_files"]]
        entries[1] = ["BINARY.BIN", *entries[1][1:]]
        distinct = decode_packet(literal_packet({**expected_control, "candidate_files": entries}, original_raw))
        try:
            assert distinct[1][0].path == "binary.bin" and distinct[1][1].path == "BINARY.BIN"
        finally:
            distinct[5].close()
        assert distinct[5].closed and distinct[5].held and not distinct[5].initial_consumption_complete
    for packet in (expected_packet[:-1], expected_packet + b"X",
                   expected_packet[:5] + b"\xff" + expected_packet[6:]):
        with pytest.raises((ValueError, TypeError, UnicodeError)):
            decode_packet(packet)
    control = literal_packet(expected_control)[4:]
    for modified in (control.replace(b'"wire_version":3', b'"wire_version":3,"wire_version":3'),
                     control.replace(b'"payload_byte_count":', b'"payload_byte_count":NaN,"ignored":'),
                     control.replace(b'"phase":"transport-fixture"', b'"phase": null')):
        with pytest.raises((ValueError, TypeError)):
            decode_packet(len(modified).to_bytes(4, "big") + modified + original_raw)
    for kwargs in ({"expected_payload_bytes": None}, {"expected_payload_bytes": True},
                   {"expected_payload_bytes": total - 1}, {"expected_wire_version": 2, "expected_payload_bytes": None},
                   {"expected_wire_version": 9}, {"expected_parent_identity": identity3},
                   {"expected_rp5a_read_basis": dataclasses.replace(basis3, baseline_ref="2" * 40)}):
        with pytest.raises((ValueError, TypeError)):
            decode_packet(expected_packet, **kwargs)
    for version in (1, 2):
        literal = literal_control(identity3, version=version, entries=[["binary.bin", "FILE", carriers[0].mode, "0", []]])
        with pytest.raises(ValueError):
            decode_packet(literal_packet(literal), expected_wire_version=version, expected_payload_bytes=None,
                          expected_rp5a_read_basis=None if version == 1 else basis3)

    # Metadata arithmetic only: no huge file, payload or synthetic native proof.
    huge = (1 << 32) + 17
    arithmetic = literal_control(identity3, entries=[["huge.bin", "FILE", carriers[0].mode, [0, huge], []]], count=huge)
    arithmetic["candidate_read_bytes"] = 4 * huge
    def immutable(value):
        if type(value) is dict:
            return MappingProxyType({k: immutable(v) for k, v in value.items()})
        if type(value) is list:
            return tuple(immutable(v) for v in value)
        return value
    measured_control = dict(immutable(arithmetic))
    measured_control["rp5a_read_basis"] = MappingProxyType({**basis_values,
        "historical_runner_bytes": owner._ScanHex(b"# historical\n")})
    measured_control = MappingProxyType(measured_control)
    measured = owner._scan_launch_measure(measured_control, limits=limits3)
    assert measured == len(literal_packet(arithmetic)) - 4 and measured < 4096 < huge
    class ArithmeticLengthOnly:
        def __len__(self):
            return huge
    with pytest.raises(ValueError):
        owner._scan_launch_measure(owner._ScanHex(ArithmeticLengthOnly()),
            limits=owner._ScanRunReadLimits(4 * huge, 100, 10, 1))
    assert 2 * huge > 0xFFFFFFFF

    # Sender/receiver typed roles, immutable bases and identity changes.
    for kwargs in ({"wire_version": 1, "surface_role": "sender", "snapshot_root": snapshots},
                   {"wire_version": 2, "surface_role": "legacy", "snapshot_root": snapshots},
                   {"wire_version": 3, "surface_role": "legacy"},
                   {"wire_version": 3, "surface_role": "receiver"}):
        with pytest.raises((TypeError, ValueError)):
            owner._scan_candidate_rows(surfaces, limits=limits3, candidate_read_bytes=allowance, **kwargs)
    with pytest.raises(ValueError):
        dataclasses.replace(carriers[0], snapshot_path=v3_root / "binary.bin",
                            snapshot_version=(*carriers[0].source_identity, 0, 0))
    with pytest.raises(ValueError):
        sender(capacity=expected_reads - 1)
    for defect in ("linked", "reparse", "same-length-mutation", "same-content-replacement"):
        local = tmp_path / ("snapshot-" + defect)
        local.mkdir()
        saved = local / "baseline"
        saved.write_bytes(b"ABCD")
        fd = owner._open_regular_worktree_descriptor(saved)
        try:
            version = owner._scan_same_api_version(os.fstat(fd))
        finally:
            os.close(fd)
        current = v3_root / ("fixture-" + defect)
        current.write_bytes(b"ABCD")
        carrier = owner._ScanDiskSnapshotV3(current.name, saved, version,
            owner._scan_file_identity(current.lstat()), stat.S_IMODE(current.stat().st_mode), 4)
        row = owner._ScanCandidateSurface(current.name, "FILE", carrier.mode, carrier, ())
        if defect == "same-length-mutation":
            saved.write_bytes(b"WXYZ")
            # This row-only negative checks metadata, not payload equality.
            # Force an observed timestamp difference instead of racing the
            # filesystem's timestamp update resolution; do not sleep/retry.
            observed = saved.stat()
            os.utime(saved, ns=(observed.st_atime_ns, version[3] + 2_000_000_000))
            assert saved.stat().st_mtime_ns != version[3]
        elif defect == "same-content-replacement":
            saved.rename(local / "retained-original")
            saved.write_bytes(b"ABCD")
        with monkeypatch.context() as fault:
            if defect in ("linked", "reparse"):
                # Simulated metadata avoids changing privileges or deleting links.
                original_lstat = Path.lstat
                def changed_lstat(path, *args, **kwargs):
                    observed = original_lstat(path, *args, **kwargs)
                    if path != saved:
                        return observed
                    fields = {key: getattr(observed, key) for key in dir(observed) if key.startswith("st_")}
                    fields["st_nlink"] = 2 if defect == "linked" else observed.st_nlink
                    fields["st_file_attributes"] = fields.get("st_file_attributes", 0) | (0x400 if defect == "reparse" else 0)
                    return SimpleNamespace(**fields)
                fault.setattr(Path, "lstat", changed_lstat)
            with pytest.raises((ValueError, OSError)):
                owner._scan_candidate_rows((row,), limits=limits3, candidate_read_bytes=1000,
                    wire_version=3, surface_role="sender", snapshot_root=local)

    # Independently test same-length payload rejection with valid, freshly
    # observed synthetic metadata. Re-observation here is deliberate fixture
    # construction, never rebasing an owner-repository expected snapshot.
    content_root = tmp_path / "snapshot-content-negative"
    content_root.mkdir()
    content_saved = content_root / "baseline"
    content_live = v3_root / "fixture-content-negative"
    content_live.write_bytes(b"ABCD")
    content_saved.write_bytes(b"WXYZ")
    content_fd = owner._open_regular_worktree_descriptor(content_saved)
    try:
        content_version = owner._scan_same_api_version(os.fstat(content_fd))
    finally:
        os.close(content_fd)
    content_carrier = owner._ScanDiskSnapshotV3(content_live.name, content_saved, content_version,
        owner._scan_file_identity(content_live.lstat()), stat.S_IMODE(content_live.stat().st_mode), 4)
    content_row = owner._ScanCandidateSurface(content_live.name, "FILE", content_carrier.mode, content_carrier, ())
    content_fence = owner._ScanCandidateFence(v3_root, (content_row,), limits=limits3,
        candidate_read_bytes=1000, deadline_ns=deadline3, wire_version=3,
        surface_role="sender", snapshot_root=content_root)
    with pytest.raises(ValueError, match="streamed candidate bytes differ from original baseline"):
        content_fence()
    assert content_fence.held and content_fence.remaining == 992

    # Single entry is independent of remaining byte allowance. All process
    # objects in this lifecycle block are no-child oracles, not native proofs.
    def reject_reentry(value):
        before = dict(value.__dict__)
        members = tuple(sorted(value.scratch_root.iterdir()))
        position = None if value.reader is None or value.reader.closed else value.reader.tell()
        with pytest.raises(ValueError, match="launch input entry is single use"):
            value.__enter__()
        assert value.__dict__ == before
        assert tuple(sorted(value.scratch_root.iterdir())) == members
        assert (None if value.reader is None or value.reader.closed else value.reader.tell()) == position

    def lifecycle_input(version, suffix):
        local = tmp_path / ("entry-lifecycle-" + str(version) + "-" + suffix)
        local.mkdir()
        selected_rows = surfaces if version == 3 else legacy_rows
        extras = {"wire_version":3, "snapshot_root":snapshots} if version == 3 else {}
        life_fence = owner._ScanCandidateFence(v3_root, selected_rows, limits=limits3,
            candidate_read_bytes=allowance, deadline_ns=deadline3,
            **({"wire_version":3, "surface_role":"sender", "snapshot_root":snapshots} if version == 3 else {}))
        return owner._ScanLaunchInput(identity3, selected_rows, limits=limits3,
            candidate_read_bytes=allowance, deadline_ns=deadline3, scratch_root=local,
            scratch_bytes=3_000_000, parent_frame_reread_bytes=20_000_000,
            check_candidate=life_fence, rp5a_read_basis=None if version == 1 else basis3, **extras)

    for version in (1, 2, 3):
        life = lifecycle_input(version, "states")
        with life:
            reject_reentry(life)  # READY: do not replace or close the first frame.
            life._claim(run_id=identity3.run_id, phase=identity3.phase, command_index=1,
                argv=identity3.argv, cwd=v3_root)
            reject_reentry(life)  # ISSUED: do not reset the consumed cursor.
            fake_child = SimpleNamespace(pid=4567, returncode=None)
            fake_child.poll = lambda: fake_child.returncode
            life._attached(fake_child)
            reject_reentry(life)  # ATTACHED: no real child is created here.
            parsed = owner._read_scan_launch_fd(life.reader.fileno(), limits=limits3,
                deadline_ns=deadline3, expected_identity=identity3, expected_wire_version=version,
                expected_rp5a_read_basis=None if version == 1 else basis3,
                expected_payload_bytes=total if version == 3 else None)
            if version == 3:
                checked = owner._ScanCandidateFence(v3_root, parsed[1], limits=limits3,
                    candidate_read_bytes=allowance, deadline_ns=deadline3, wire_version=3,
                    surface_role="receiver", payload_lease=parsed[5])
                checked()
                checked.close_payload_lease()
            fake_child.returncode = 0
            life._finished(fake_child, 0)
            reject_reentry(life)  # CONSUMED: surplus allocation grants no reuse.
        reject_reentry(life)      # CLOSED: no new file or descriptor is created.
        assert life.state == "CLOSED" and not life.path.exists()

        failed_entry = lifecycle_input(version, "entry-failure")
        body_fault = OSError("single-use first-entry failure")
        def refuse_initial_check():
            raise body_fault
        with monkeypatch.context() as entry_fault:
            entry_fault.setattr(failed_entry, "_check", refuse_initial_check)
            with pytest.raises(OSError) as failure:
                failed_entry.__enter__()
        assert failure.value is body_fault and failed_entry.state == "HELD" and failed_entry.path is None
        reject_reentry(failed_entry)

        during_entry = lifecycle_input(version, "recursive-entry")
        original_check = during_entry._check
        recursive_checks = []
        def observe_first_check():
            if not recursive_checks:
                recursive_checks.append(during_entry.state)
                reject_reentry(during_entry)
            original_check()
        with monkeypatch.context() as recursive:
            recursive.setattr(during_entry, "_check", observe_first_check)
            with during_entry:
                assert recursive_checks == ["PREPARING"] and during_entry.state == "READY"
        assert during_entry.state == "CLOSED" and not during_entry.path.exists()

        foreign = lifecycle_input(version, "foreign-owner")
        with monkeypatch.context() as foreign_owner:
            foreign_owner.setattr(foreign, "thread_id", foreign.thread_id + 1)
            before = dict(foreign.__dict__)
            with pytest.raises(ValueError, match="foreign launch input owner"):
                foreign.__enter__()
            assert foreign.__dict__ == before and not tuple(foreign.scratch_root.iterdir())
        with foreign:
            assert foreign.state == "READY"
        assert foreign.state == "CLOSED" and not foreign.path.exists()

    # A failed prefix cannot grant credit for the remaining spans.
    decoded = decode_packet(expected_packet)
    lease = decoded[5]
    receiver = owner._ScanCandidateFence(v3_root, decoded[1], limits=limits3, candidate_read_bytes=allowance,
        deadline_ns=deadline3, wire_version=3, surface_role="receiver", payload_lease=lease)
    first_source = v3_root / "binary.bin"
    first_source.write_bytes(b"\x00\xffZ\xfe")
    with pytest.raises(ValueError):
        receiver()
    assert receiver.held and lease.held and not lease.initial_consumption_complete
    assert receiver.remaining == allowance - 8
    receiver.close_payload_lease()
    first_source.write_bytes(b"\x00\xffA\xfe")

    # The earlier intentional current-source mutation requires its separately
    # observed synthetic carrier; it is not rebaselining owner-repository data.
    refreshed = dataclasses.replace(carriers[0], source_identity=owner._scan_file_identity(first_source.lstat()))
    surfaces = (dataclasses.replace(surfaces[0], content=refreshed), *surfaces[1:])

    # Read/close errors retain both original exceptions and close only the
    # process-local duplicate. The no-child oracle owns these fault fixtures.
    decoded = decode_packet(expected_packet)
    lease = decoded[5]
    read_error = OSError("original v3 payload read fault")
    close_error = OSError("original v3 payload close fault")
    receiver = owner._ScanCandidateFence(v3_root, decoded[1], limits=limits3, candidate_read_bytes=allowance,
        deadline_ns=deadline3, wire_version=3, surface_role="receiver", payload_lease=lease)
    real_close = owner.os.close
    with monkeypatch.context() as fault:
        def read_fault(fd, size):
            if fd == lease._fd:
                raise read_error
            return real_read(fd, size)
        def close_fault(fd):
            if fd == lease._fd:
                real_close(fd)
                raise close_error
            return real_close(fd)
        fault.setattr(owner.os, "read", read_fault)
        fault.setattr(owner.os, "close", close_fault)
        errors = []
        try:
            receiver()
        except BaseException as error:
            errors.append(error)
        try:
            receiver.close_payload_lease()
        except BaseException as error:
            errors.append(error)
        with pytest.raises(BaseExceptionGroup) as raised:
            owner._scan_raise_errors(errors)
    assert raised.value.exceptions == (read_error, close_error)
    assert lease.held and lease.initial_consumption_complete is False

    # A live synthetic process object never authorizes deletion. These cases
    # deliberately launch no child; only that oracle permits fixture teardown.
    held, _ = sender()
    held.__enter__()
    held._claim(run_id=identity3.run_id, phase=identity3.phase, command_index=1, argv=identity3.argv, cwd=v3_root)
    unresolved = SimpleNamespace(pid=5678, returncode=None)
    unresolved.poll = lambda: unresolved.returncode
    held._attached(unresolved)
    original_failure = OSError("late receipt/status write fault")
    with pytest.raises(BaseExceptionGroup) as retained:
        held.__exit__(OSError, original_failure, None)
    assert retained.value.exceptions[0] is original_failure
    assert held.state == "HELD" and held.path.exists() and not held.reader.closed
    unresolved.returncode = 9
    with pytest.raises(ValueError):
        held._finished(unresolved, 9)
    assert held.state == "HELD" and held.path.exists()
    with pytest.raises(ValueError):
        held._close()
    assert held.path.exists() and held.reader.closed

    # Real successful and terminal-nonzero children use this same sender and
    # production decoder/fence. No domain builder/validator is called.
    child_script = tmp_path / "fixed-v3-transport-child.py"
    child_script.write_text(
        "import os, sys\nfrom pathlib import Path\n"
        + "sys.path.insert(0, " + repr(str(Path(owner.__file__).resolve().parents[1])) + ")\n"
        + "from tools import validation_reliability as v\n"
        + "root=Path(sys.argv[1]); deadline=int(sys.argv[2]); status=int(sys.argv[3])\n"
        + "identity=v._ScanLaunchIdentity('v3-fixture','transport-fixture',1,1,tuple(sys.orig_argv),str(root))\n"
        + "basis=v._Rp5aReadBasisV1(**" + repr(basis_values) + ")\n"
        + "limits=v._ScanRunReadLimits(2000000,10000,32,3)\n"
        + "parsed=v._read_scan_launch_fd(sys.stdin.fileno(),limits=limits,deadline_ns=deadline,"
          "expected_identity=identity,expected_wire_version=3,expected_rp5a_read_basis=basis,expected_payload_bytes="
        + str(total) + ")\n"
        + "fence=None; errors=[]\n"
        + "try:\n"
        + "    fence=v._ScanCandidateFence(root,parsed[1],limits=limits,candidate_read_bytes=parsed[2],"
          "deadline_ns=deadline,wire_version=3,surface_role='receiver',payload_lease=parsed[5])\n"
        + "    fence()\n"
        + "    assert parsed[5].initial_consumption_complete\n"
        + "    assert os.lseek(sys.stdin.fileno(),0,os.SEEK_CUR)==parsed[5].extent\n"
        + "except BaseException as error: errors.append(error)\n"
        + "try: parsed[5].close()\n"
        + "except BaseException as error: errors.append(error)\n"
        + "v._scan_raise_errors(errors)\n"
        + "print('V3_TRANSPORT_FIXTURE_COMPLETE',flush=True)\n"
        + "raise SystemExit(status)\n", encoding="utf-8", newline="\n")
    for native_status in (0, 7):
        argv3 = (sys.executable, "-B", str(child_script), str(v3_root), str(deadline3), str(native_status))
        direct_identity = dataclasses.replace(identity3, argv=argv3)
        native_input, _ = sender(direct_identity)
        folder = tmp_path / ("v3-native-evidence-" + str(native_status))
        folder.mkdir()
        pending = False
        receipt = None
        errors = []
        try:
            with native_input:
                pending = True
                receipt = owner.supervise_command(argv3, cwd=v3_root, run_id=identity3.run_id,
                    phase=identity3.phase, command_index=1, evidence_root=folder, timeout_seconds=120,
                    environment={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    launch_input=native_input, required_markers=("V3_TRANSPORT_FIXTURE_COMPLETE",),
                    mirror_stdout=False, mirror_stderr=False)
            pending = owner._command_requires_process_retention_v1(receipt)
        except BaseException as error:
            errors.append(error)
        assert pending is False, errors
        owner._scan_raise_errors(errors)
        assert receipt.native_exit_code == native_status
        assert receipt.failure_class == (None if native_status == 0 else "ENGVR_NATIVE_EXIT_NONZERO")
        assert receipt.termination_state == "NOT_REQUIRED" and receipt.stdout_marker_state == "PASS"
        assert native_input.state == "CLOSED" and not native_input.path.exists()


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
