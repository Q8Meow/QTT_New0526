"""Small data containers for PR142 static evidence loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class StaticEvidence:
    repo_root: Path
    payloads: Mapping[str, Mapping[str, Any]]
    pr141_yaml: Mapping[str, Any]
    pr141_report: Mapping[str, Any]
    alias_resolution: Mapping[str, Any]
    source_evidence_packet_present: bool
