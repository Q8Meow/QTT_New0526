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
