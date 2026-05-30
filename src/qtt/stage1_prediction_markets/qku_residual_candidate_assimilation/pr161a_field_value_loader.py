"""PR161A field-value facet loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json, records_from_payload


def load_pr161a_field_values(repo_root: Path | str) -> list[dict[str, Any]]:
    return records_from_payload(read_json(Path(repo_root) / c.PR161A_REPORT_PATHS["field_value"]))
