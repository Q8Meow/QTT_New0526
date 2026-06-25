#!/usr/bin/env python3
"""CLI wrapper for PR168-RP5B active registry cleanup validation."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5b_validator import run_validation


def main() -> int:
    print(json.dumps(run_validation(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
