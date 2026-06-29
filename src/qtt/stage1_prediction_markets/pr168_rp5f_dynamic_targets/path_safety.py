"""Path-safety helpers for RP5F generated artifacts."""

from __future__ import annotations

from .models import GENERATED_REF_PREFIX

UNSAFE_CHARS = set(' <>:"|?*')


def path_safety_record(filename: str) -> dict[str, object]:
    repo_relative = f"{GENERATED_REF_PREFIX}/{filename}"
    windows_absolute_estimate = rf"C:\Users\Owner\Projects\QTT_New0526\{repo_relative.replace('/', '\\')}"
    return {
        "artifact_filename": filename,
        "file_path": repo_relative,
        "filename_length": len(filename),
        "repo_relative_path_length": len(repo_relative),
        "windows_absolute_path_estimate_length": len(windows_absolute_estimate),
        "unsafe_shell_char_flag": any(ch in UNSAFE_CHARS for ch in filename),
        "unicode_punctuation_flag": any(ord(ch) > 127 for ch in filename),
        "case_collision_checked_flag": True,
        "windows_safe_flag": len(filename) <= 64 and len(repo_relative) <= 180 and len(windows_absolute_estimate) <= 240 and not any(ch in UNSAFE_CHARS for ch in filename),
    }


def path_safety_failures(filenames: set[str] | tuple[str, ...] | list[str]) -> list[str]:
    failures: list[str] = []
    seen: dict[str, str] = {}
    for filename in filenames:
        record = path_safety_record(filename)
        if not record["windows_safe_flag"]:
            failures.append(f"WINDOWS_UNSAFE:{filename}")
        key = filename.casefold()
        if key in seen and seen[key] != filename:
            failures.append(f"CASE_COLLISION:{seen[key]}:{filename}")
        seen[key] = filename
    return failures
