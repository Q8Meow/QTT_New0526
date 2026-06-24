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

    rows, index, stats = scanner.scan_files_for_terms(
        ["sample.txt"],
        tmp_path,
        max_wall_seconds=60,
        max_files_scanned=10,
        max_total_line_hits=10,
        progress_interval_seconds=999999,
    )

    assert stats["rg_used_flag"] is False
    assert stats["git_grep_used_flag"] is True
    assert stats["python_fallback_used_flag"] is False
    assert 1 <= len(rows) <= 10
    assert list(index) == ["sample.txt"]
