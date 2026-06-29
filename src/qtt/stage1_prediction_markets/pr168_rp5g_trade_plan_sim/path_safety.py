"""Path safety checks for compact RP5G generated artifacts."""

from __future__ import annotations

from pathlib import PurePosixPath
import re

UNSAFE_CHARS = re.compile(r"[\s<>:\"|?*\x00-\x1f]")


def path_safety_record(filename: str) -> dict[str, object]:
    estimated_repo_relative = f"docs/master_plan/generated/pr168_rp5g/{filename}"
    return {
        "artifact_filename": filename,
        "filename_length": len(filename),
        "repo_relative_path": estimated_repo_relative,
        "repo_relative_path_length": len(estimated_repo_relative),
        "windows_absolute_path_estimate": len(f"C:/Users/Owner/Projects/QTT_New0526/{estimated_repo_relative}"),
        "filename_length_lte_64_flag": len(filename) <= 64,
        "repo_relative_path_lte_180_flag": len(estimated_repo_relative) <= 180,
        "windows_absolute_path_lte_240_flag": len(f"C:/Users/Owner/Projects/QTT_New0526/{estimated_repo_relative}") <= 240,
        "no_space_flag": " " not in filename,
        "no_unsafe_shell_chars_flag": UNSAFE_CHARS.search(filename) is None,
        "ascii_only_flag": filename.isascii(),
        "casefold_key": filename.casefold(),
    }


def path_safety_failures(filenames: tuple[str, ...]) -> list[str]:
    failures: list[str] = []
    seen: dict[str, str] = {}
    for filename in filenames:
        rec = path_safety_record(filename)
        if not rec["filename_length_lte_64_flag"]:
            failures.append(f"FILENAME_TOO_LONG:{filename}")
        if not rec["repo_relative_path_lte_180_flag"]:
            failures.append(f"REPO_PATH_TOO_LONG:{filename}")
        if not rec["windows_absolute_path_lte_240_flag"]:
            failures.append(f"WINDOWS_PATH_TOO_LONG:{filename}")
        if not rec["no_space_flag"] or not rec["no_unsafe_shell_chars_flag"] or not rec["ascii_only_flag"]:
            failures.append(f"UNSAFE_FILENAME:{filename}")
        if PurePosixPath(filename).name != filename:
            failures.append(f"NESTED_FILENAME_NOT_ALLOWED:{filename}")
        key = filename.casefold()
        if key in seen and seen[key] != filename:
            failures.append(f"CASE_COLLISION:{seen[key]}:{filename}")
        seen[key] = filename
    return failures

