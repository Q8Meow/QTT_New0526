"""PR161A orchestration preflight facade."""

from __future__ import annotations

from pathlib import Path

from .atomicrows_universe_loader import load_atomicrows_universe
from .pr154_universe_loader import load_pr154_universe
from .report_builder import _preflight_receipt


def build_preflight_receipt(root: Path) -> dict[str, object]:
    return _preflight_receipt(root, load_atomicrows_universe(root), load_pr154_universe(root))

