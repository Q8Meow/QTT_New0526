"""PR137R/PR138/AtomicRows compatibility loader for PR161F."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_loaders import consume_json_report_map


def load_atomicrows_contracts(repo_root: Path) -> dict[str, dict[str, Any] | None]:
    return consume_json_report_map(repo_root, c.ATOMICROWS_CONTRACT_PATHS)

