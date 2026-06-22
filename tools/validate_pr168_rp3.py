#!/usr/bin/env python3
"""CLI wrapper for PR168-RP3 validation."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp3_validator import main


if __name__ == "__main__":
    raise SystemExit(main())
