#!/usr/bin/env python3
"""Build PR168-RP5D-R1 executable-now unlock overlay artifacts."""

from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr168_rp5d_r1_unlock.runner import main


if __name__ == "__main__":
    raise SystemExit(main())
