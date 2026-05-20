#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.orderbook_event_state_snapshot_builder_validate import main as validate_main


def main(argv: Sequence[str] | None = None) -> int:
    return validate_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
