#!/usr/bin/env python3
"""Build PR168-MEM1 condition-scoped outcome memory artifacts."""

from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.memory.pr168_mem1.builder import main


if __name__ == "__main__":
    raise SystemExit(main())
