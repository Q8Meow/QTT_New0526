"""PR161A entity loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json, records_from_payload


def load_pr161a_atomicrow_entities(repo_root: Path | str) -> list[dict[str, Any]]:
    return records_from_payload(read_json(Path(repo_root) / c.PR161A_REPORT_PATHS["atomicrows_entity"]))


def load_pr161a_pr154_entities(repo_root: Path | str) -> list[dict[str, Any]]:
    return records_from_payload(read_json(Path(repo_root) / c.PR161A_REPORT_PATHS["pr154_entity"]))


def load_pr161a_entities(repo_root: Path | str) -> list[dict[str, Any]]:
    return load_pr161a_atomicrow_entities(repo_root) + load_pr161a_pr154_entities(repo_root)
