#!/usr/bin/env python3
"""Validate PR162E negative candidate repair factory reports."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162e_plugin_framework.validator import (  # noqa: E402
    validate_negative_repair_factory,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    validate_negative_repair_factory(Path(args.repo_root))
    print("PR162E_NEGATIVE_REPAIR_FACTORY_VALIDATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
