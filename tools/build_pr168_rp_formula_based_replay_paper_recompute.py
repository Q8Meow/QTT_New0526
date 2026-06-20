#!/usr/bin/env python3
"""Build PR168-RP formula-based replay/paper recomputation reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp_compute_kernel import build_all_reports


def main() -> int:
    summary = build_all_reports(REPO_ROOT)
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
