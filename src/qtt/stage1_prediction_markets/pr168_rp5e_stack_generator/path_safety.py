"""Windows-safe artifact path validation for PR168-RP5E."""

from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Iterable

from .models import GENERATED_REF_PREFIX, WINDOWS_REPO_ROOT_ASSUMPTION

MAX_GENERATED_FILENAME_CHARS = 64
MAX_REPO_RELATIVE_PATH_CHARS = 180
MAX_WINDOWS_ABSOLUTE_PATH_CHARS = 240
UNSAFE_FILENAME_RE = re.compile(r"[\s<>:\"|?*\x00-\x1f]")
NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")


def repo_relative_path(filename: str) -> str:
    return f"{GENERATED_REF_PREFIX}/{filename}"


def windows_absolute_length(filename: str) -> int:
    return len(WINDOWS_REPO_ROOT_ASSUMPTION + repo_relative_path(filename).replace("/", "\\"))


def filename_is_safe(filename: str) -> bool:
    name = PurePosixPath(filename).name
    return (
        name == filename
        and len(name) <= MAX_GENERATED_FILENAME_CHARS
        and not UNSAFE_FILENAME_RE.search(name)
        and not NON_ASCII_RE.search(name)
    )


def path_safety_record(filename: str) -> dict[str, object]:
    rel = repo_relative_path(filename)
    return {
        "artifact_filename": filename,
        "file_path": rel,
        "repo_relative_path": rel,
        "filename_length": len(filename),
        "repo_relative_path_length": len(rel),
        "windows_absolute_path_length_under_owner_repo": windows_absolute_length(filename),
        "casefold_key": rel.casefold(),
        "safe_filename_flag": filename_is_safe(filename)
        and len(rel) <= MAX_REPO_RELATIVE_PATH_CHARS
        and windows_absolute_length(filename) <= MAX_WINDOWS_ABSOLUTE_PATH_CHARS,
    }


def path_safety_failures(filenames: Iterable[str]) -> list[str]:
    failures: list[str] = []
    seen: dict[str, str] = {}
    for filename in sorted(dict.fromkeys(filenames), key=lambda item: (item.casefold(), item)):
        rec = path_safety_record(filename)
        if rec["filename_length"] > MAX_GENERATED_FILENAME_CHARS:
            failures.append(f"FILENAME_TOO_LONG:{filename}")
        if rec["repo_relative_path_length"] > MAX_REPO_RELATIVE_PATH_CHARS:
            failures.append(f"REPO_RELATIVE_PATH_TOO_LONG:{filename}")
        if rec["windows_absolute_path_length_under_owner_repo"] > MAX_WINDOWS_ABSOLUTE_PATH_CHARS:
            failures.append(f"WINDOWS_ABSOLUTE_PATH_TOO_LONG:{filename}")
        if not rec["safe_filename_flag"]:
            failures.append(f"UNSAFE_FILENAME:{filename}")
        previous = seen.get(str(rec["casefold_key"]))
        if previous is not None and previous != filename:
            failures.append(f"CASE_COLLISION:{previous}:{filename}")
        seen[str(rec["casefold_key"])] = filename
    return failures
