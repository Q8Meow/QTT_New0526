"""PR161B PR161C assimilation queue loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json, records_from_payload


def load_pr161b_queue(repo_root: Path | str) -> list[dict[str, Any]]:
    return records_from_payload(read_json(Path(repo_root) / c.PR161B_REPORT_PATHS["assimilation_queue"]))
