#!/usr/bin/env python3
"""Build PR162E plugin framework generated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr162e_plugin_framework.report_writer import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = write_artifacts(Path(args.repo_root))
    print(
        "PR162E_BUILD_PASS "
        f"reports={result['report_count']} "
        f"schemas={result['schema_count']} "
        f"plugins={result['plugin_row_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
