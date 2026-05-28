"""PR160 split-record loading facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .input_discovery import build_source_records


def load_records(repo_root: Path | str) -> list[dict[str, Any]]:
    return build_source_records(Path(repo_root).resolve())
