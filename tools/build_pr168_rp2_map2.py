#!/usr/bin/env python3
"""Build PR168-RP2-MAP2 GFP2R-gated replay/paper artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp2_engine import build_all


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify-online-docs", action="store_true")
    mode.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    summary = build_all(verify_online_docs=bool(args.verify_online_docs))
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
