from __future__ import annotations

from pathlib import Path

from tools import validate_pr169_val1 as val1


def test_readability_guard_rejects_hidden_bidi_control_character(tmp_path: Path):
    bad_path = tmp_path / "bad.py"
    bad_path.write_text("def ok():\n    return 'x'\u202e\n", encoding="utf-8")

    record = val1.scan_readability_file(tmp_path, Path("bad.py"))

    assert record.hidden_bidi_control_chars == ("U+202E",)
    assert not record.pass_


def test_readability_guard_rejects_many_defs_on_one_line(tmp_path: Path):
    bad_path = tmp_path / "bad.py"
    bad_path.write_text("def one(): pass\ndef two(): pass; def three(): pass\n", encoding="utf-8")

    record = val1.scan_readability_file(tmp_path, Path("bad.py"))

    assert record.many_defs_or_classes_on_one_line
    assert record.semicolon_statement_lines == 1
    assert not record.pass_


def test_readability_guard_accepts_current_critical_files():
    records = val1.readability_records(Path(".").resolve())

    assert records
    assert all(record.pass_ for record in records)
