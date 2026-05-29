"""Master-plan section manifest loading and fallback parsing."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import constants as c


def load_master_plan_sections(root: Path | str) -> tuple[list[dict[str, Any]], int]:
    repo_root = Path(root).resolve()
    manifest_path = repo_root / c.SECTION_MANIFEST_PATH
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_sections = list(payload.get("sections", []))
        line_count = int(payload.get("line_count") or _line_count(repo_root / c.MASTER_PLAN_PATH))
    else:
        raw_sections = _parse_sections(repo_root / c.MASTER_PLAN_PATH)
        line_count = _line_count(repo_root / c.MASTER_PLAN_PATH)
    sections: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_sections, start=1):
        next_line = (
            int(raw_sections[index]["line"]) - 1
            if index < len(raw_sections)
            else line_count
        )
        canonical = raw.get("canonical_id")
        section_id = f"{canonical or 'UNNUMBERED'}__{index:04d}"
        sections.append(
            {
                "section_id": section_id,
                "canonical_id": canonical,
                "section_heading": str(raw.get("title") or ""),
                "section_order_index": index,
                "section_depth": int(raw.get("level") or 0),
                "source_line_start_if_available": int(raw.get("line") or 1),
                "source_line_end_if_available": next_line,
            }
        )
    return sections, line_count


def _parse_sections(path: Path) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    heading_pattern = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = heading_pattern.match(line)
        if not match:
            continue
        title = match.group("title")
        canonical = title.split(" ", 1)[0] if re.match(r"^[0-9A-Z]+(?:\.[0-9A-Z]+)*", title) else None
        sections.append(
            {
                "level": len(match.group("hashes")),
                "title": title,
                "line": line_number,
                "canonical_id": canonical,
            }
        )
    return sections


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())
