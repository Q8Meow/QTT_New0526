#!/usr/bin/env python3
"""Validate PR168-VS1 generated artifacts."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr168_vs1_trading_intelligence.validator import main


if __name__ == "__main__":
    raise SystemExit(main())
