#!/usr/bin/env python3
"""Validate PR168-QOPT1 advisory batch optimization artifacts."""

from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.optimization.pr168_qopt1.validator import main


if __name__ == "__main__":
    raise SystemExit(main())
